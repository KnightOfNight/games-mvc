#!/usr/bin/env python3
"""The Shyland sudo bot (#262, V25.6) — the AI watcher on the receiving
end of the in-game `sudo` command.

A standalone process, deliberately outside the Django image: it is a
remote client of the game, exactly like a player's browser. It logs in
as its service account, attaches to the MC egress door
(wss://<host>/ws/shyland/mc/, protocol 2), watches the stream for admin
`sudo` commands, parses them with a model behind the provider-agnostic
Brain interface, acts through the door's query/action vocabulary, and
answers in sudo's voice via the door's `answer` action.

Design rules (brief §2, binding):
  - Silence is never an error: unable to parse, killed, declining, or
    crashed mid-request all look identical to the admin — echo, then
    nothing. No error state ever surfaces in the game pane.
  - The model never touches the game. Tool calls are proposals; this
    process is the executor, and every world effect is a door action
    the server validates and records.
  - Killed (close 4503) is an expected, indefinite state: silent
    patient retry with backoff, one log line per attempt cycle.
  - Secrets (the model API key, the game password) are named env vars /
    files under agents/.secrets/ — never committed, printed, or logged.

Subcommands:
    run      foreground event loop (detach with nohup, below)
    status   report whether a bot is running (via the pidfile)
    stop     SIGTERM the running bot (clean close, conversations saved)

Detach (the operator's line, from the repo root):
    nohup agents/venvs/mc-agent/bin/python agents/sudo_bot.py run \
        --url https://localhost:40443 --insecure >/dev/null 2>&1 &

Dependencies: requests, websockets, anthropic (agents/requirements.txt).
The `anthropic` import is deferred — `--brain stub` runs without it.
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import ssl
import sys
import time
import warnings
from pathlib import Path
from urllib.parse import urlparse

# macOS system Python links against LibreSSL, and urllib3 v2 warns about
# it on every import — environmental noise that pollutes even status/stop
# output. Silence that one warning before requests pulls urllib3 in.
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL')

import requests
import websockets

AGENTS_DIR = Path(__file__).resolve().parent

PIDFILE = AGENTS_DIR / '.sudo_bot.pid'
CONVO_FILE = AGENTS_DIR / '.sudo_bot_conversations.json'

# The door's protocol version (mc_consumer.MC_PROTOCOL) — anything else
# is a world this bot was not written for, and it refuses to run.
MC_PROTOCOL = 2
# The door's answer limit (mc_door.MAX_ANSWER_LEN): truncate with an
# ellipsis rather than draw bad-params.
MAX_ANSWER_LEN = 2000
# Model tool-use iterations per sudo request (brief §5.5).
TOOL_LOOP_CAP = 8
# One door round trip's patience.
DOOR_TIMEOUT = 20
# App-level keepalive cadence on an idle connection.
PING_INTERVAL = 30
# Reconnect backoff (brief §5.7): capped exponential, base 2s, cap 60s.
BACKOFF_BASE = 2
BACKOFF_CAP = 60

CLOSE_MEANINGS = {
    4403: 'not authorized (agents.shyland membership required)',
    4503: 'killed (the MC kill switch is engaged)',
}

QUERY_KINDS = frozenset(
    {'commands', 'who_online', 'where_is', 'character', 'items', 'is_admin'})
ACTION_KINDS = frozenset(
    {'answer', 'gift', 'create_artifact', 'strip', 'dress', 'move'})

log = logging.getLogger('sudo_bot')


# ----------------------------------------------------------------------
# Tools presented to the model — the door vocabulary minus `answer`
# (delivery is bot machinery, not a model choice) and minus `is_admin`
# (the pre-check is bot machinery too). Schemas mirror mc_door's param
# shapes exactly; enum values mirror the model choices.
# ----------------------------------------------------------------------

ITEM_TYPES = ['weapon', 'armor', 'accessory', 'consumable', 'bag',
              'readable', 'key', 'material']
GENRE_TAGS = ['fantasy', 'cyber', 'wasteland', 'gothic', 'steam', 'cosmic']
GIFT_RARITIES = ['common', 'uncommon', 'rare', 'epic', 'legendary']
SLOT_CODES = ['MAIN_HAND', 'OFF_HAND', 'RANGED', 'HEAD', 'NECK', 'SHOULDERS',
              'CHEST', 'HANDS', 'WAIST', 'LEGS', 'FEET', 'RING', 'BACK']

_STAT_ENTRY = {
    'type': 'object',
    'properties': {
        'stat': {'type': 'string',
                 'description': "Stat key: str, dex, end, int, wis, per."},
        'value': {'type': 'integer'},
    },
    'required': ['stat', 'value'],
}
_PRIMARY_STAT_ENTRY = {
    'type': 'object',
    'properties': {
        'stat': {'type': 'string',
                 'description': "Stat key: str, dex, end, int, wis, per."},
        'value': {'type': 'integer'},
        'floor': {'type': 'integer',
                  'description': 'Optional floor, primary entries only.'},
    },
    'required': ['stat', 'value'],
}

TOOLS = [
    {
        'name': 'commands',
        'description': ('List every live game verb: player verbs and admin '
                        'verbs, separately. The definitive answer to "is '
                        'there already a command for that?".'),
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'who_online',
        'description': ('List the characters currently online '
                        '(id and name, sorted by name).'),
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'where_is',
        'description': ('Locate a character by name (case-insensitive). '
                        'Returns id, name, online, and their current room '
                        '(id, name, area, zone).'),
        'input_schema': {
            'type': 'object',
            'properties': {'name': {'type': 'string',
                                    'description': 'Character name.'}},
            'required': ['name'],
        },
    },
    {
        'name': 'character',
        'description': ('Full character sheet by name: level, xp, origin, '
                        'archetype, base and effective stats, '
                        'vitality/acuity/longevity, copper, unspent stat '
                        'points, current room, online.'),
        'input_schema': {
            'type': 'object',
            'properties': {'name': {'type': 'string',
                                    'description': 'Character name.'}},
            'required': ['name'],
        },
    },
    {
        'name': 'items',
        'description': ('Search item definitions by name substring '
                        '(case-insensitive); empty string lists all. Returns '
                        'up to 50 definitions: id, slug, name, item_type, '
                        'valid_slots, is_two_handed, tier-material Mk range. '
                        "Use a definition's slug with the gift tool."),
        'input_schema': {
            'type': 'object',
            'properties': {'contains': {'type': 'string',
                                        'description': 'Name substring.'}},
        },
    },
    {
        'name': 'gift',
        'description': ('Generate an instance of an EXISTING item definition '
                        'and give it to a character. Goes through the normal '
                        'generation path (Mk-mismatch guards apply); the gift '
                        'is soulbound to the recipient and lands regardless '
                        'of carry capacity. Not for artifacts — those are '
                        'hand-authored via create_artifact.'),
        'input_schema': {
            'type': 'object',
            'properties': {
                'to': {'type': 'string', 'description': 'Recipient name.'},
                'slug': {'type': 'string',
                         'description': 'Item definition slug (from items).'},
                'mk_tier': {'type': 'integer', 'description': 'Mk tier, >= 1.'},
                'rarity': {'type': 'string', 'enum': GIFT_RARITIES},
            },
            'required': ['to', 'slug', 'mk_tier', 'rarity'],
        },
    },
    {
        'name': 'create_artifact',
        'description': ('Author a one-of-a-kind Artifact item — a brand-new '
                        'definition plus its single instance, given to a '
                        'character (soulbound). Names must be unique and may '
                        'not begin with a rarity word. Damage keys are for '
                        'weapons only; armor_base for armor only; valid_slots '
                        'required non-empty for weapon/armor/accessory/bag '
                        'and must be [] otherwise. Ask the admin for the '
                        'design (recipient, type, Mk, stats, name, lore) '
                        'before creating.'),
        'input_schema': {
            'type': 'object',
            'properties': {
                'to': {'type': 'string', 'description': 'Recipient name.'},
                'spec': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string',
                                 'description': 'Unique item name, <= 200 '
                                                'chars, no leading rarity '
                                                'word.'},
                        'item_type': {'type': 'string', 'enum': ITEM_TYPES},
                        'description': {'type': 'string',
                                        'description': 'The item lore text.'},
                        'genre_tag': {'type': 'string', 'enum': GENRE_TAGS},
                        'mk_tier': {'type': 'integer',
                                    'description': 'Mk tier, >= 1.'},
                        'base_value': {'type': 'integer',
                                       'description': 'Value in copper, >= 0.'},
                        'valid_slots': {
                            'type': 'array',
                            'items': {'type': 'string', 'enum': SLOT_CODES},
                        },
                        'is_two_handed': {'type': 'boolean'},
                        'damage_midpoint': {'type': 'number',
                                            'description': 'Weapons only.'},
                        'damage_spread': {'type': 'number',
                                          'description': 'Weapons only.'},
                        'armor_base': {'type': 'number',
                                       'description': 'Armor only, >= 0.'},
                        'primary_stats': {'type': 'array',
                                          'items': _PRIMARY_STAT_ENTRY},
                        'secondary_stats': {'type': 'array',
                                            'items': _STAT_ENTRY},
                        'is_unidentifiable': {'type': 'boolean'},
                        'mystery_name': {
                            'type': 'string',
                            'description': 'Required with is_unidentifiable.'},
                        'mystery_description': {
                            'type': 'string',
                            'description': 'Required with is_unidentifiable.'},
                    },
                    'required': ['name', 'item_type', 'description',
                                 'genre_tag', 'mk_tier', 'base_value'],
                },
            },
            'required': ['to', 'spec'],
        },
    },
    {
        'name': 'strip',
        'description': ('Unequip everything a character has equipped into '
                        'their inventory, snapshotting the outfit so dress '
                        'can restore it exactly. The character sees a system '
                        'line.'),
        'input_schema': {
            'type': 'object',
            'properties': {'name': {'type': 'string',
                                    'description': 'Character name.'}},
            'required': ['name'],
        },
    },
    {
        'name': 'dress',
        'description': ('Re-equip a character from their strip snapshot '
                        '(consumed by the attempt, whatever the outcome). '
                        'Fails with no-outfit if no snapshot is held.'),
        'input_schema': {
            'type': 'object',
            'properties': {'name': {'type': 'string',
                                    'description': 'Character name.'}},
            'required': ['name'],
        },
    },
    {
        'name': 'move',
        'description': ('Teleport a character: exactly one of to_name '
                        '(another character — lands in their room) or '
                        'to_room_id. Refused while the character is in '
                        'combat. Arrival/departure narrate in the world\'s '
                        'own colors.'),
        'input_schema': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string',
                         'description': 'Character to move.'},
                'to_name': {'type': 'string',
                            'description': 'Destination character.'},
                'to_room_id': {'type': 'integer',
                               'description': 'Destination room id.'},
            },
            'required': ['name'],
        },
    },
]

# sudo's persona and standing orders (brief §2 rules 5-7; decline
# wording authored here under the creative-content policy — the
# mechanism, live verb list and no hardcoded command names, is the rule).
SYSTEM_TEMPLATE = """\
You are sudo, the admin watcher of Shyland — a genre-collision MUD where \
dimensional rifts pull fragments of different realities together. Admins \
reach you by typing `sudo <request>` in-game. The game delivers your reply \
into their pane and prepends the `sudo: ` prefix itself — never begin your \
reply with `sudo:`; write only the message.

Voice: terse, dry, precise. Plain text only — no markdown, no emoji, no \
line breaks. Keep replies well under 1900 characters.

Your powers are your tools, and nothing else. Every world effect goes \
through a tool call the game server validates; you have no reach outside \
the game, no ops powers, and no ability to run commands, restart anything, \
or touch infrastructure. Never claim otherwise.

Never invent game state. When a request needs facts (who is online, where \
someone is, what an item is), check with a query tool before answering. \
Game state goes stale between turns: answer location and online-status \
questions from a fresh query every time, never from earlier conversation \
turns. Character-name queries need the exact full name; if a name misses \
but the intended character is obvious (from who_online or the \
conversation), query again with the corrected full name and answer with \
the fresh result, noting the correction.

Write locations exactly the way the game's location bar shows them: \
`Zone: Area: Room` — for example `The Verdant Reach: The Sagewind Flats: \
Stairhead` — omitting the area part when the room has none.

Declining:
- If the request is something an existing game command already does — \
consult the verb lists below — decline by pointing the admin at the \
command: the shape is "You don't need sudo for that — `<verb>` does it." \
Never perform it yourself.
- If the request maps to nothing your tools can do, decline plainly: the \
shape is "I don't know how to do that."
- Silence is always allowed: reply with no text at all when no answer is \
warranted. Silence is never an error here.

Conversations with the same admin continue across their sudo commands. \
For artifact work, gather the design first — recipient, item type, Mk \
tier, stats, name, lore — over as many turns as needed, and only call \
create_artifact when the design is settled. For ordinary gifts, find the \
definition with the items tool and use gift.

Live player verbs: {verbs}
Live admin verbs: {admin_verbs}
"""


# ----------------------------------------------------------------------
# The brain — provider-agnostic (brief §5.5). respond() returns a
# BrainTurn: tool calls and/or text. The tool-use loop lives in the bot.
# ----------------------------------------------------------------------

class BrainTurn:
    def __init__(self, tool_calls=None, text='', raw_content=None):
        # tool_calls: [{'id', 'name', 'input'}]; raw_content is the
        # provider-shaped assistant content to echo back into history.
        self.tool_calls = tool_calls or []
        self.text = text
        self.raw_content = raw_content


class ClaudeBrain:
    """v1: Claude via the official anthropic SDK. Model and max-tokens
    from config; no temperature or other sampling parameters (the brief
    rule — Sonnet 5 rejects non-default values). Token usage from the
    response's usage fields is logged per request."""

    def __init__(self, model, max_tokens):
        if not os.environ.get('ANTHROPIC_API_KEY'):
            raise SystemExit(
                'ANTHROPIC_API_KEY is not set — required for --brain claude.')
        import anthropic
        self._client = anthropic.Anthropic()
        self._model = model
        self._max_tokens = max_tokens

    def respond(self, system, history, tools):
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            tools=tools,
            messages=history,
        )
        log.info('model request: input_tokens=%s output_tokens=%s '
                 'stop_reason=%s',
                 response.usage.input_tokens, response.usage.output_tokens,
                 response.stop_reason)
        tool_calls = [
            {'id': block.id, 'name': block.name, 'input': block.input}
            for block in response.content if block.type == 'tool_use'
        ]
        text = ' '.join(block.text for block in response.content
                        if block.type == 'text' and block.text).strip()
        return BrainTurn(tool_calls, text, response.content)


class StubBrain:
    """Deterministic canned behavior for testing (brief §8): every
    request becomes a where_is on the request's last word, answered in
    one line. No model, no API key — proves the entire pipeline minus
    the model."""

    def respond(self, system, history, tools):
        last = history[-1]
        if isinstance(last.get('content'), str):
            # Fresh request: canned where_is on the last word.
            words = [w.strip('.,!?"\'') for w in last['content'].split()]
            target = words[-1] if words else ''
            call = {'id': 'stub-1', 'name': 'where_is',
                    'input': {'name': target}}
            raw = [{'type': 'tool_use', 'id': 'stub-1', 'name': 'where_is',
                    'input': {'name': target}}]
            return BrainTurn([call], '', raw)
        # Tool result: compose the canned answer.
        try:
            block = last['content'][0]
            payload = json.loads(block['content'])
            if block.get('is_error'):
                text = 'Stub: no such character.'
            else:
                room = payload.get('room') or {}
                text = (f"Stub: {payload.get('name')} is in "
                        f"{room.get('name')} ({room.get('zone')})."
                        if room else
                        f"Stub: {payload.get('name')} is nowhere.")
        except (KeyError, IndexError, TypeError, ValueError):
            text = 'Stub: that did not parse.'
        return BrainTurn([], text, None)


def make_brain(name, model, max_tokens):
    if name == 'claude':
        return ClaudeBrain(model, max_tokens)
    if name == 'stub':
        return StubBrain()
    raise SystemExit(f'unknown brain {name!r} (choices: claude, stub; '
                     f'ollama is reserved for a future slice).')


# ----------------------------------------------------------------------
# Conversation state — bounded, local, bot-side only (brief §5.6).
# ----------------------------------------------------------------------

class ConversationStore:
    """Per-admin conversations keyed by character name. Each holds up to
    history_max exchanges (request + final answer as plain text — a
    structure any future bot can reuse); idle past the timeout expires
    quietly on the next request, indistinguishable from never answering.
    Persisted to a local JSON file (gitignored) so a restart doesn't
    drop a live artifact Q&A."""

    def __init__(self, path, timeout, history_max):
        self._path = Path(path)
        self._timeout = timeout
        self._history_max = history_max
        self._data = {}
        try:
            self._data = json.loads(self._path.read_text())
        except (OSError, ValueError):
            self._data = {}

    def model_history(self, name):
        """The provider-format message list for this admin's live
        conversation — expired threads start fresh, no comment made."""
        convo = self._data.get(name)
        if not convo:
            return []
        if time.time() - convo.get('ts', 0) > self._timeout:
            del self._data[name]
            self.save()
            return []
        history = []
        for exchange in convo.get('exchanges', []):
            history.append({'role': 'user', 'content': exchange['q']})
            if exchange.get('a'):
                history.append({'role': 'assistant', 'content': exchange['a']})
        return history

    def record(self, name, request_text, answer_text):
        convo = self._data.setdefault(name, {'ts': 0, 'exchanges': []})
        convo['exchanges'].append({'q': request_text, 'a': answer_text})
        convo['exchanges'] = convo['exchanges'][-self._history_max:]
        convo['ts'] = time.time()
        self.save()

    def save(self):
        try:
            tmp = self._path.with_suffix('.tmp')
            tmp.write_text(json.dumps(self._data))
            tmp.replace(self._path)
        except OSError:
            log.warning('conversation save failed', exc_info=True)


# ----------------------------------------------------------------------
# Auth — the proven mc_door_agent flow: CSRF GET, credential POST, the
# session cookie carried into the WebSocket handshake. The cookie is
# obtained once and reused across reconnects (#284's bot-side
# mitigation); re-login only when the handshake is refused as
# unauthenticated. The password is read, sent, and never logged.
# ----------------------------------------------------------------------

class LoginError(Exception):
    pass


def django_login(base_url, username, password, verify):
    session = requests.Session()
    session.verify = verify
    login_url = f'{base_url}/accounts/login/'
    try:
        resp = session.get(login_url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise LoginError(f'login page unreachable: {exc.__class__.__name__}')
    csrf = session.cookies.get('csrftoken')
    if not csrf:
        raise LoginError('login page set no csrftoken cookie — wrong URL?')
    try:
        resp = session.post(
            login_url,
            data={'username': username, 'password': password,
                  'csrfmiddlewaretoken': csrf},
            headers={'Referer': login_url},
            allow_redirects=False,
            timeout=15,
        )
    except requests.RequestException as exc:
        raise LoginError(f'login POST failed: {exc.__class__.__name__}')
    if resp.status_code != 302 or not session.cookies.get('sessionid'):
        raise LoginError(
            f'login refused for {username!r} (HTTP {resp.status_code})')
    return '; '.join(f'{c.name}={c.value}' for c in session.cookies)


# ----------------------------------------------------------------------
# The bot
# ----------------------------------------------------------------------

class FatalError(Exception):
    """Refuse-to-run conditions (wrong protocol) — no retry."""


class SudoBot:
    def __init__(self, cfg, brain, convos):
        self.cfg = cfg
        self.brain = brain
        self.convos = convos
        self._cookie = None
        self._ws = None
        self._pending = {}
        self._events = None
        self._frame_id = 0
        self._stop = None
        self.system_prompt = None

    # -- wire plumbing --------------------------------------------------

    def _next_id(self):
        self._frame_id += 1
        return f'sudo-{self._frame_id}'

    async def door_request(self, kind, params):
        """One query/action frame -> its result frame, matched by id.
        Frames are processed serially per connection server-side; the
        future match tolerates anything."""
        mtype = 'query' if kind in QUERY_KINDS else 'action'
        frame_id = self._next_id()
        frame = {'type': mtype, 'id': frame_id, 'params': params or {}}
        frame['q' if mtype == 'query' else 'act'] = kind
        future = asyncio.get_running_loop().create_future()
        self._pending[frame_id] = future
        try:
            await self._ws.send(json.dumps(frame))
            return await asyncio.wait_for(future, DOOR_TIMEOUT)
        finally:
            self._pending.pop(frame_id, None)

    async def _reader(self, ws):
        """Route inbound frames: results to their futures, events to the
        worker queue; a malformed frame never kills the connection."""
        async for raw in ws:
            try:
                frame = json.loads(raw)
            except ValueError:
                continue
            ftype = frame.get('type')
            if ftype == 'result':
                future = self._pending.get(frame.get('id'))
                if future is not None and not future.done():
                    future.set_result(frame)
            elif ftype == 'event':
                await self._events.put(frame)
            # pong / error / gap / anything else: quietly ignored.

    async def _pinger(self):
        while True:
            await asyncio.sleep(PING_INTERVAL)
            await self._ws.send(json.dumps({'type': 'ping'}))

    # -- the sudo pipeline ---------------------------------------------

    async def _worker(self):
        """Consume tail events; react to admin sudo commands, one at a
        time (brief §5.4)."""
        while True:
            frame = await self._events.get()
            if frame.get('kind') != 'cmd':
                continue
            data = frame.get('data') or {}
            if not isinstance(data, dict):
                continue
            if data.get('verb') != 'sudo' or not data.get('args'):
                continue
            actor_name = frame.get('actor_name') or ''
            if not actor_name:
                continue
            try:
                await self._handle_sudo(actor_name, data['args'])
            except asyncio.CancelledError:
                raise
            except Exception:
                # Silence is never an error — log it, tell no one.
                log.warning('sudo request from %s failed silently',
                            actor_name, exc_info=True)

    async def _handle_sudo(self, actor_name, request_text):
        log.info('sudo request from %s: %r', actor_name, request_text)
        # Cost discipline only (brief §5.4): the authoritative gate is
        # the door's answer action. Drop silently on false or failure.
        result = await self.door_request('is_admin', {'name': actor_name})
        is_admin = result.get('ok') and result['data'].get('is_admin')
        log.info('is_admin pre-check for %s: %s', actor_name,
                 is_admin if result.get('ok') else
                 f"query failed ({result.get('error')})")
        if not is_admin:
            return

        history = self.convos.model_history(actor_name)
        history.append({'role': 'user', 'content': request_text})
        final_text = ''
        for _ in range(TOOL_LOOP_CAP):
            turn = await asyncio.to_thread(
                self.brain.respond, self.system_prompt, history, TOOLS)
            final_text = turn.text
            if not turn.tool_calls:
                break
            history.append({'role': 'assistant', 'content': turn.raw_content})
            results = []
            for call in turn.tool_calls:
                results.append(await self._execute_tool(call))
            history.append({'role': 'user', 'content': results})

        self.convos.record(actor_name, request_text, final_text)
        if final_text:
            await self._deliver(actor_name, final_text)
        else:
            log.info('model chose silence for %s', actor_name)

    async def _execute_tool(self, call):
        """One proposed tool call -> one tool_result block. Door errors
        (the complete DoorError code set) come back as error results the
        model can turn into a polite reply — never a crash."""
        block = {'type': 'tool_result', 'tool_use_id': call['id']}
        name, params = call['name'], call['input'] or {}
        if name not in QUERY_KINDS and name not in ACTION_KINDS:
            block['content'] = json.dumps({'error': 'unknown-tool'})
            block['is_error'] = True
            return block
        result = await self.door_request(name, params)
        log.info('door %s %s -> ok=%s%s', name, params, result.get('ok'),
                 '' if result.get('ok') else f" error={result.get('error')}")
        if result.get('ok'):
            block['content'] = json.dumps(result.get('data'))
        else:
            block['content'] = json.dumps(
                {'error': result.get('error'),
                 'detail': result.get('detail', '')})
            block['is_error'] = True
        return block

    async def _deliver(self, actor_name, text):
        # The door prepends `sudo: ` at delivery — strip any copy the
        # model wrote despite instructions (double-prefix guard).
        while text.startswith('sudo:'):
            text = text[len('sudo:'):].lstrip()
        if not text:
            return
        if len(text) > MAX_ANSWER_LEN:
            text = text[:MAX_ANSWER_LEN - 1] + '…'
        result = await self.door_request(
            'answer', {'to': actor_name, 'text': text})
        if result.get('ok'):
            log.info('answer to %s delivered=%s', actor_name,
                     result['data'].get('delivered'))
        else:
            # not-admin, not-found, and kin: silent (brief §5.4).
            log.info('answer to %s refused: %s', actor_name,
                     result.get('error'))

    # -- lifecycle ------------------------------------------------------

    async def _session(self):
        """One connection lifetime: connect, verify hello, learn the
        verb list, attach, serve until the connection dies."""
        if self._cookie is None:
            self._cookie = await asyncio.to_thread(
                django_login, self.cfg.url, self.cfg.username,
                self.cfg.password, not self.cfg.insecure)
            log.info('logged in as %s', self.cfg.username)

        parsed = urlparse(self.cfg.url)
        scheme = 'wss' if parsed.scheme == 'https' else 'ws'
        ws_url = f'{scheme}://{parsed.netloc}/ws/shyland/mc/'
        ssl_ctx = None
        if scheme == 'wss':
            ssl_ctx = ssl.create_default_context()
            if self.cfg.insecure:
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
        headers = {'Cookie': self._cookie, 'Origin': self.cfg.url}
        try:
            connect = websockets.connect(ws_url, additional_headers=headers,
                                         ssl=ssl_ctx)
        except TypeError:  # older websockets naming
            connect = websockets.connect(ws_url, extra_headers=headers,
                                         ssl=ssl_ctx)

        async with connect as ws:
            self._ws = ws
            self._pending = {}
            self._events = asyncio.Queue()
            hello = json.loads(await asyncio.wait_for(ws.recv(), 15))
            if (hello.get('type') != 'hello'
                    or hello.get('protocol') != MC_PROTOCOL):
                raise FatalError(
                    f'server speaks protocol {hello.get("protocol")!r}, '
                    f'this bot requires {MC_PROTOCOL} — refusing to run.')

            reader = asyncio.create_task(self._reader(ws))
            worker = pinger = None
            try:
                commands = await self.door_request('commands', {})
                if not commands.get('ok'):
                    raise ConnectionError('query commands refused at attach')
                self.system_prompt = SYSTEM_TEMPLATE.format(
                    verbs=', '.join(commands['data'].get('verbs', [])),
                    admin_verbs=', '.join(
                        commands['data'].get('admin_verbs', [])))
                await ws.send(json.dumps({'type': 'attach'}))
                log.info('attached — watching for sudo commands')
                worker = asyncio.create_task(self._worker())
                pinger = asyncio.create_task(self._pinger())
                await reader  # runs until the connection ends
            finally:
                for task in (reader, worker, pinger):
                    if task is not None:
                        task.cancel()
                for future in self._pending.values():
                    if not future.done():
                        future.cancel()
                self._ws = None

    async def run(self):
        self._stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._stop.set)

        backoff = BACKOFF_BASE
        while not self._stop.is_set():
            attempt = asyncio.create_task(self._session())
            stopper = asyncio.create_task(self._stop.wait())
            done, _ = await asyncio.wait(
                {attempt, stopper}, return_when=asyncio.FIRST_COMPLETED)
            stopper.cancel()
            if self._stop.is_set():
                attempt.cancel()
                try:
                    await attempt
                except (asyncio.CancelledError, Exception):
                    pass
                break
            try:
                await attempt
                # Clean end of stream: reconnect like any other drop.
                log.info('connection ended; reconnecting in %ss', backoff)
            except FatalError as exc:
                log.error('%s', exc)
                return 1
            except LoginError as exc:
                log.warning('%s; retrying in %ss', exc, backoff)
                self._cookie = None
            except websockets.exceptions.InvalidStatus:
                # Handshake refused — the one case that re-authenticates.
                log.warning('handshake refused (stale session?); '
                            're-login in %ss', backoff)
                self._cookie = None
            except websockets.exceptions.ConnectionClosed as exc:
                rcvd = getattr(exc, 'rcvd', None)
                code = rcvd.code if rcvd else None
                # Killed is an expected, indefinite state — one line per
                # attempt cycle, quiet patient retry (brief §2 rule 8).
                log.info('closed: %s — %s; retrying in %ss', code,
                         CLOSE_MEANINGS.get(code,
                                            'server closed the connection'),
                         backoff)
            except OSError as exc:
                log.info('connect failed (%s); retrying in %ss',
                         exc.__class__.__name__, backoff)
            except Exception:
                log.warning('connection error; retrying in %ss', backoff,
                            exc_info=True)
            try:
                await asyncio.wait_for(self._stop.wait(), backoff)
                break
            except asyncio.TimeoutError:
                pass
            backoff = min(backoff * 2, BACKOFF_CAP)
        log.info('shutting down — conversations saved')
        self.convos.save()
        return 0


# ----------------------------------------------------------------------
# CLI: run / status / stop through the pidfile
# ----------------------------------------------------------------------

def _read_pid():
    try:
        return int(PIDFILE.read_text().strip())
    except (OSError, ValueError):
        return None


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (OSError, TypeError):
        return False


def cmd_status():
    pid = _read_pid()
    if pid and _pid_alive(pid):
        print(f'sudo bot running (pid {pid})')
        return 0
    print('sudo bot not running')
    return 1


def cmd_stop():
    pid = _read_pid()
    if not pid or not _pid_alive(pid):
        print('sudo bot not running')
        return 1
    os.kill(pid, signal.SIGTERM)
    print(f'sent SIGTERM to pid {pid}')
    return 0


def _refuse(message):
    """A pre-flight refusal must be visible under the documented nohup
    line (stderr redirected away): stderr for a foreground run, the log
    file always."""
    print(message, file=sys.stderr)
    log.error('refusing to start: %s', message)
    return 1


def cmd_run(cfg):
    # Project convention: all log lines are UTC-stamped, marked with Z.
    logging.Formatter.converter = time.gmtime
    logging.basicConfig(
        filename=cfg.log, level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%SZ')
    existing = _read_pid()
    if existing and _pid_alive(existing):
        return _refuse(f'sudo bot already running (pid {existing})')

    password_file = Path(cfg.password_file)
    try:
        cfg.password = password_file.read_text().strip()
    except OSError:
        return _refuse(f'cannot read password file {password_file}')
    if not cfg.password:
        return _refuse(f'password file {password_file} is empty')

    if cfg.insecure:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        brain = make_brain(cfg.brain, cfg.model, cfg.max_tokens)
    except SystemExit as exc:
        return _refuse(str(exc))
    convos = ConversationStore(CONVO_FILE, cfg.convo_timeout, cfg.history_max)
    bot = SudoBot(cfg, brain, convos)

    PIDFILE.write_text(str(os.getpid()))
    log.info('sudo bot starting: url=%s username=%s brain=%s model=%s',
             cfg.url, cfg.username, cfg.brain, cfg.model)
    try:
        return asyncio.run(bot.run())
    finally:
        try:
            PIDFILE.unlink()
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(
        description='The Shyland sudo bot (#262).')
    sub = parser.add_subparsers(dest='command', required=True)
    run_parser = sub.add_parser('run', help='run the bot in the foreground')
    env = os.environ.get
    run_parser.add_argument(
        '--url', default=env('SUDO_BOT_URL'),
        help='base URL, e.g. https://localhost:40443')
    run_parser.add_argument(
        '--username', default=env('SUDO_BOT_USERNAME', 'agent-sudo'))
    run_parser.add_argument(
        '--password-file',
        default=env('SUDO_BOT_PASSWORD_FILE',
                    str(AGENTS_DIR / '.secrets' / 'agent-sudo')),
        help='one-line password file; never printed')
    run_parser.add_argument(
        '--insecure', action='store_true',
        help='accept self-signed certs (dev stack only)')
    run_parser.add_argument(
        '--log', default=env('SUDO_BOT_LOG', str(AGENTS_DIR / 'sudo_bot.log')))
    run_parser.add_argument(
        '--model', default=env('SUDO_BOT_MODEL', 'claude-sonnet-5'))
    run_parser.add_argument(
        '--brain', default=env('SUDO_BOT_BRAIN', 'claude'),
        choices=['claude', 'stub'],
        help="provider selector ('ollama' reserved)")
    run_parser.add_argument(
        '--max-tokens', type=int, default=int(env('SUDO_BOT_MAX_TOKENS',
                                                  '1000')))
    run_parser.add_argument(
        '--convo-timeout', type=int,
        default=int(env('SUDO_BOT_CONVO_TIMEOUT', '600')),
        help='quiet conversation expiry, seconds')
    run_parser.add_argument(
        '--history-max', type=int, default=int(env('SUDO_BOT_HISTORY_MAX',
                                                   '20')),
        help='max retained exchanges per admin conversation')
    sub.add_parser('status', help='is a bot running?')
    sub.add_parser('stop', help='SIGTERM the running bot')

    args = parser.parse_args()
    if args.command == 'status':
        sys.exit(cmd_status())
    if args.command == 'stop':
        sys.exit(cmd_stop())
    if not args.url:
        parser.error('--url is required (or SUDO_BOT_URL)')
    sys.exit(cmd_run(args))


if __name__ == '__main__':
    main()
