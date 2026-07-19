import asyncio
import json
import logging
import random
import re
import uuid
from collections import deque
from datetime import timedelta

import redis.asyncio as aioredis
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.urls import reverse
from django.utils import timezone

from . import currency
from .combat_utils import npc_display, npc_display_name
from .command_grammar import (
    RARITY_RANK, complete as grammar_complete, entry_display_name, resolve,
)
from .envelope import envelope_ts
from .currency import display_for_zone
from .item_utils import (
    compose_item_line, format_slot_name, generate_item_instance,
    get_display_name, get_display_name_with_tier, get_display_description,
    get_durability_penalty, get_item_flags, get_item_suffix, get_item_value,
    get_repair_cost, get_repair_success_chance, get_sale_price, item_ref,
    parse_corpse_noun, STAT_LABELS,
)
from .models import (
    Character, CombatSession, DialogueEntry, DialogueGreetingRecord,
    ItemInstance, NpcInstance, PendingDialogueResponse, Room, RoomSpawn,
    RoomVisit, TravelMessage, TravelNode, VendorEntry,
    COMBAT_ROUND_TICKS, DIALOGUE_FIRST_DELAY_TICKS, DIALOGUE_STAGGER_TICKS,
    FLEE_COOLDOWN_TICKS,
)

# v22 brief 2 (DD §9): the re-authored anatomical order, head to feet —
# the Equipment paper-doll renders every slot in this order (RING twice,
# per SLOT_CAPACITY).
SLOT_ORDER = [
    'HEAD', 'NECK', 'SHOULDERS', 'BACK', 'CHEST',
    'MAIN_HAND', 'OFF_HAND', 'RANGED', 'HANDS', 'RING',
    'WAIST', 'LEGS', 'FEET',
]
SLOT_RANK = {s: i for i, s in enumerate(SLOT_ORDER)}

# RING is the only slot a character has two of.
SLOT_CAPACITY = {'RING': 2}

# v19 brief 10: kibitz lines (gazebo double-vendor transactions) and
# pity-repair lines (repairs whose computed value is 0). Not part of the
# brief 9 dialogue engine — plain authored pools, keyed and consumed here.
KIBITZ_LINES = [
    '{other} watches the exchange and nods approvingly.',
    '{other} pretends not to supervise, and supervises.',
    '{other} rearranges the shelf, satisfied.',
]

PITY_REPAIR_LINES = {
    'morra': (
        'Morra turns the piece over once, snorts softly, and fixes it for '
        'nothing. "Come back when you\'ve got something worth charging for."'
    ),
    'pella': (
        "Pella tuts over the wear like it's a personal affront and mends it "
        'free. "There. Don\'t thank me, just eat something."'
    ),
    'ferwick': (
        'Ferwick waves off payment before you can reach for your purse. '
        '"The city gave it to you; the city can keep it standing."'
    ),
    'repairbot-prime': (
        'Repairbot Prime completes the work in silence. "COST: NEGLIGIBLE. '
        'WAIVED. MAINTAIN YOUR EQUIPMENT."'
    ),
}
PITY_REPAIR_FALLBACK = (
    '{name} looks your battered gear over, takes pity, and repairs it for nothing.'
)


def _pity_repair_line(repairer):
    template = PITY_REPAIR_LINES.get(repairer.definition.slug)
    if template:
        return template
    return PITY_REPAIR_FALLBACK.replace('{name}', npc_display(repairer, capitalize=True))


logger = logging.getLogger('shyland.envelope')
cmd_logger = logging.getLogger('shyland.commands')

DIRECTIONS = {
    'north': 'exit_north', 'n': 'exit_north',
    'south': 'exit_south', 's': 'exit_south',
    'east': 'exit_east',  'e': 'exit_east',
    'west': 'exit_west',  'w': 'exit_west',
    'up': 'exit_up',      'u': 'exit_up',
    'down': 'exit_down',  'd': 'exit_down',
}

DIRECTION_CANONICAL = {
    'north': 'north', 'n': 'north',
    'south': 'south', 's': 'south',
    'east': 'east',   'e': 'east',
    'west': 'west',   'w': 'west',
    'up': 'up',       'u': 'up',
    'down': 'down',   'd': 'down',
}

REVERSE_DIRECTIONS = {
    'north': 'south', 'south': 'north',
    'east': 'west',   'west': 'east',
    'up': 'down',     'down': 'up',
}

# v20 brief 1 (#35): the four directions that can join a MapFrag. Up/down
# exits always break fragments; non-cardinal movement never joins them.
MAP_CARDINALS = ('north', 'south', 'east', 'west')

_NO_EXIT_DEFAULTS = {
    'north': "There is no exit in that direction.",
    'south': "There is no exit in that direction.",
    'east':  "There is no exit in that direction.",
    'west':  "There is no exit in that direction.",
    'up':    "There is nothing above you.",
    'down':  "You'd have to dig to go that way.",
}


def _join_owned_names(items, conj):
    names = [f'your {get_display_name(i)}' for i in items]
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f'{names[0]} {conj} {names[1]}'
    return ', '.join(names[:-1]) + f', {conj} {names[-1]}'


_DIALOGUE_WORD_RE = re.compile(r"[a-zA-Z']+")


def _tokenize_said_words(text):
    """Lowercase, punctuation-stripped word set for NPC keyword matching."""
    return {w.lower() for w in _DIALOGUE_WORD_RE.findall(text)}


def parse_presence_name(raw: bytes) -> str:
    """Extract the character name from a presence value.
    Tolerates legacy values that are a bare name string."""
    text = raw.decode()
    try:
        return json.loads(text)["name"]
    except (ValueError, KeyError, TypeError):
        return text


# Guarded heartbeat: self-heals a missing key, refreshes TTL only if this
# session still owns the key, and never clobbers a different session's value.
PRESENCE_HEARTBEAT_LUA = """
local v = redis.call('GET', KEYS[1])
if v == false then
  redis.call('SET', KEYS[1], ARGV[1], 'EX', 90)
  return 1
elseif v == ARGV[1] then
  redis.call('EXPIRE', KEYS[1], 90)
  return 1
else
  return 0
end
"""

# Guarded delete: only removes the key if it still holds this session's value.
PRESENCE_DELETE_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
else
  return 0
end
"""


class SkylandConsumer(AsyncJsonWebsocketConsumer):

    # v20 brief 3 (#22/#19/#20): THE dispatch table — the source of truth
    # for implemented commands (see CLAUDE.md). verb → (handler name,
    # takes args). Movement verbs live in DIRECTIONS and dispatch to
    # cmd_move. The connect-time verb list (#19) is derived from this
    # table plus DIRECTIONS.
    COMMAND_TABLE = {
        'look': ('cmd_look', False), 'l': ('cmd_look', False),
        'say': ('cmd_say', True),
        'who': ('cmd_who', False),
        'inventory': ('cmd_inventory', False), 'inv': ('cmd_inventory', False),
        'wallet': ('cmd_wallet', False),
        'pickup': ('cmd_pickup', True), 'p': ('cmd_pickup', True),
        'drop': ('cmd_drop', True),
        'equip': ('cmd_equip', True), 'eq': ('cmd_equip', True),
        'unequip': ('cmd_unequip', True), 'uneq': ('cmd_unequip', True),
        'use': ('cmd_use', True),
        'examine': ('cmd_examine', True), 'ex': ('cmd_examine', True),
        'loot': ('cmd_loot', True),
        'list': ('cmd_list', False),
        'buy': ('cmd_buy', True),
        'sell': ('cmd_sell', True),
        'repair': ('cmd_repair', True),
        'kill': ('cmd_attack', True), 'attack': ('cmd_attack', True),
        'k': ('cmd_attack', True),
        'flee': ('cmd_flee', False),
        'travel': ('cmd_travel', True),
        'brief': ('cmd_brief', True),
        'echo': ('cmd_echo', True),
        'timestamps': ('cmd_timestamps', True),
        'spend': ('cmd_spend', True),
        'stats': ('cmd_stats', False),
        'quit': ('cmd_quit', False),
        'help': ('cmd_help', False), '?': ('cmd_help', False),
    }

    # ------------------------------------------------------------------
    # v22 brief 2 (DD §5): the state-gating matrix, applied centrally in
    # the dispatch path. Refusals are warn-color (world declined).
    # ------------------------------------------------------------------

    # In combat: commerce, inventory manipulation, gear, travel, and
    # movement refuse; everything else (attack/flee/use/spend/examine/
    # say/quit, all information, all settings) proceeds. Movement verbs
    # gate through DIRECTIONS in _dispatch.
    COMBAT_BLOCKED = {
        'travel': "You can't just walk away from a fight — flee!",
        'buy': "There's no trading in the middle of a fight!",
        'sell': "There's no trading in the middle of a fight!",
        'repair': "There's no mending anything in the middle of a fight!",
        'drop': "Your hands are too busy with the fight!",
        'pickup': "Your hands are too busy with the fight!",
        'p': "Your hands are too busy with the fight!",
        'loot': "Your hands are too busy with the fight!",
        'equip': "There's no time to fiddle with your gear mid-fight!",
        'eq': "There's no time to fiddle with your gear mid-fight!",
        'unequip': "There's no time to fiddle with your gear mid-fight!",
        'uneq': "There's no time to fiddle with your gear mid-fight!",
    }
    COMBAT_MOVE_REFUSAL = "You can't just walk away from a fight — flee!"

    # While dying: use (self-rescue), say, quit, all information, and all
    # settings proceed; everything else refuses (warn).
    DYING_ALLOWED = {
        'use', 'say', 'quit',
        'help', '?', 'inventory', 'inv', 'list', 'look', 'l',
        'stats', 'wallet', 'who',
        'brief', 'echo', 'timestamps',
    }

    # v22 brief 2 (DD §1 fn 10): verbs with a required target and their
    # canonical prompt verb — bare invocation gets the standard prompt
    # "What do you want to <verb>?" (CLI error).
    PROMPT_VERBS = {
        'attack': 'attack', 'kill': 'attack', 'k': 'attack',
        'buy': 'buy',
        'drop': 'drop',
        'equip': 'equip', 'eq': 'equip',
        'examine': 'examine', 'ex': 'examine',
        'loot': 'loot',
        'pickup': 'pickup', 'p': 'pickup',
        'repair': 'repair',
        'say': 'say',
        'sell': 'sell',
        'spend': 'spend',
        'unequip': 'unequip', 'uneq': 'unequip',
        'use': 'use',
    }

    # v20 brief 3 (#19/#22): alias → canonical grammar verb, for the
    # commands whose arguments resolve through command_grammar. Also the
    # set of verbs that offer argument completion.
    GRAMMAR_VERBS = {
        'use': 'use', 'sell': 'sell', 'buy': 'buy',
        'pickup': 'pickup', 'p': 'pickup',
        'drop': 'drop',
        'equip': 'equip', 'eq': 'equip',
        'unequip': 'unequip', 'uneq': 'unequip',
        'examine': 'examine', 'ex': 'examine',
        'loot': 'loot', 'repair': 'repair',
        'attack': 'attack', 'kill': 'attack', 'k': 'attack',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # v20 brief 2 (#32): per-connection seq counter. One consumer
        # instance per connection, so this resets to 0 on every reconnect
        # and the first message of a connection carries seq 1.
        self._seq = 0

    # ------------------------------------------------------------------
    # Delivery choke point (v20 brief 2, #32)
    # ------------------------------------------------------------------

    async def send_json(self, content, close=False):
        """The single delivery choke point: every outbound message to the
        client passes through here — there is no other legal send path.
        Assigns the per-connection monotonic ``seq`` (authoritative for
        client render order) and guarantees ``ts`` is present. ``ts`` is
        supposed to be stamped at each creation site; stamping it here is
        a fallback and logs a warning so unstamped creation sites get
        found and fixed. This is the designated tap point for the
        Firehose Logging milestone (#37/#33)."""
        self._seq += 1
        content['seq'] = self._seq
        if 'ts' not in content:
            logger.warning(
                "shyland envelope: message type %r reached delivery without "
                "ts; stamped at the choke point — fix its creation site",
                content.get('type', content.get('event')),
            )
            content['ts'] = envelope_ts()
        await super().send_json(content, close=close)

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return

        self.character = await self.get_character(user)
        if self.character is None:
            await self.accept()
            await self.output('No character found. Create one to play.', 'error')
            # Structured signal so the client can route to the creator instead
            # of sitting on a dead socket.
            await self.send_json({'type': 'redirect', 'url': reverse('shyland:create_character'),
                                  'ts': envelope_ts()})
            await self.close()
            return

        self.character_pk = self.character.pk
        self.last_direction = None
        self._character_is_dying = self.character.is_dying
        await self.accept()

        if self.character.current_room_id is None:
            await self.output('You are not in any room. Contact an admin.', 'error')
            return

        room = await self.get_current_room()
        # Arrival-equivalent (#50): covers a fresh character's spawn room
        # (creation sets current_room without a visit) and heals any
        # pre-fix room the character is standing in.
        first_visit = await self.record_room_visit(self.character, room)
        self.room_group = f'room_{room.id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)

        self.player_group = f'player_{self.character_pk}'
        await self.channel_layer.group_add(self.player_group, self.channel_name)

        self.redis = aioredis.from_url("redis://redis:6379")
        self.session_token = uuid.uuid4().hex
        # v21.1 (#116): single-session enforcement. Any older consumer in
        # this character's personal group sees a token mismatch, prints a
        # farewell, and closes; this consumer ignores its own broadcast.
        # Fired before the presence write — either interleaving with the
        # old session's guarded presence delete is safe (see arch doc 4.3).
        await self.channel_layer.group_send(
            self.player_group,
            {
                'type': 'player_message',
                'event': 'superseded',
                'token': self.session_token,
                'ts': envelope_ts(),
            }
        )
        self.presence_value = json.dumps({
            "name": self.character.name,
            "token": self.session_token,
        })
        await self.redis.set(
            f"shyland:online:{self.character_pk}",
            self.presence_value,
            ex=90,
        )
        self.heartbeat_task = asyncio.ensure_future(self.presence_heartbeat())

        # v20 brief 3 (#19): the verb+alias list from the dispatch table,
        # for client-side verb-position tab completion. Carries the
        # show_timestamps preference (#45) too, so the very first stamped
        # lines already honor it — the status payload keeps it in sync
        # from then on.
        await self.send_json({
            'type': 'verbs',
            'verbs': sorted(set(DIRECTIONS) | set(self.COMMAND_TABLE)),
            'show_timestamps': self.character.show_timestamps,
            'echo_mode': self.character.echo_mode,
            'ts': envelope_ts(),
        })

        await self.send_room_description(room, first_visit=first_visit)
        # v20 brief 1 (#35): full map state on connect, following the v19
        # client-state sync full-state pattern.
        await self.send_map()

    async def disconnect(self, code):
        if hasattr(self, 'heartbeat_task'):
            self.heartbeat_task.cancel()
        if hasattr(self, 'character_pk') and hasattr(self, 'redis'):
            await self.redis.eval(
                PRESENCE_DELETE_LUA,
                1,
                f"shyland:online:{self.character_pk}",
                self.presence_value,
            )
        if hasattr(self, 'player_group'):
            await self.channel_layer.group_discard(self.player_group, self.channel_name)
        if hasattr(self, 'room_group'):
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
        if getattr(self, 'character', None) is not None:
            await self.touch_last_seen(self.character)

    # ------------------------------------------------------------------
    # Receive / dispatch
    # ------------------------------------------------------------------

    async def receive_json(self, content):
        # v20 brief 4 (#31): connection-indicator ping. Echo the nonce back
        # and nothing else — no client data is trusted or stored, and a
        # malformed nonce is dropped rather than reflected.
        if content.get('type') == 'ping':
            nonce = content.get('nonce')
            if isinstance(nonce, int) and not isinstance(nonce, bool):
                await self.send_json({'type': 'pong', 'nonce': nonce,
                                      'ts': envelope_ts()})
            return

        # v20 brief 3 (#19): tab-completion requests are their own message
        # type, never treated as command text.
        if content.get('type') == 'complete':
            await self.handle_complete(content.get('text', ''))
            return

        raw = content.get('text', '').strip()
        if not raw:
            return

        # v20 brief 5 (#15): command echo — every submitted command, valid
        # or not, echoes into this player's transcript before its result
        # (including the dying-gate refusal below). Never re-broadcast to
        # anyone else; a stamped, displayed-prefix category like output.
        await self.send_output(f'> {raw}', 'echo')

        parts = raw.split(None, 1)
        verb = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''

        # v22 brief 2 (DD §5): the dying gate — use (self-rescue), say,
        # quit, information, and settings proceed; everything else is a
        # state-gate refusal (warn).
        if self._character_is_dying and verb not in self.DYING_ALLOWED:
            await self.send_output(
                "You are dying! Use a revival item or wait for another player to revive you.",
                'warn',
            )
            return

        # v20 brief 3 (#20): the dispatch guard. A crashing handler must
        # never kill the connection — log the full traceback server-side,
        # tell the player one error line, and stay alive.
        try:
            await self._dispatch(verb, args)
        except Exception:
            cmd_logger.exception('shyland command handler crashed: %r', raw)
            await self.send_output('Something went wrong with that command.', 'error')

    async def _dispatch(self, verb, args):
        # v22 brief 2 (DD §5): the combat gate, applied centrally — one
        # lookup, one query, warn-color refusals in voice.
        if verb in DIRECTIONS or verb in self.COMBAT_BLOCKED:
            session = await self.get_active_combat_session(self.character)
            if session:
                refusal = (self.COMBAT_MOVE_REFUSAL if verb in DIRECTIONS
                           else self.COMBAT_BLOCKED[verb])
                await self.send_output(refusal, 'warn')
                return
        if verb in DIRECTIONS:
            await self.cmd_move(verb)
            return
        entry = self.COMMAND_TABLE.get(verb)
        if entry is None:
            await self.output("Unknown command. Type 'help' for a list of commands.", 'error')
            return
        # v22 brief 2 (DD §1 fn 10): the standard bare-invocation prompt
        # for every command with a required target (CLI error).
        if verb in self.PROMPT_VERBS and entry[1] and not args.strip():
            await self.send_output(
                f'What do you want to {self.PROMPT_VERBS[verb]}?', 'error',
            )
            return
        handler = getattr(self, entry[0])
        if entry[1]:
            await handler(args)
        else:
            await handler()

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def cmd_look(self):
        room = await self.get_current_room()
        await self.send_room_description(room, entering=True, force_long=True)

    async def cmd_move(self, direction):
        # v20 brief 3 (#23): active combat blocks directional movement —
        # since v22 brief 2 the refusal fires centrally in _dispatch.
        exit_field = DIRECTIONS[direction]
        room = await self.get_current_room()
        destination = getattr(room, exit_field)

        if destination is None:
            exits = room.exits()
            canonical = DIRECTION_CANONICAL[direction]
            custom_msg = getattr(room, f'no_exit_{canonical}_msg', '')
            msg = custom_msg if custom_msg else _NO_EXIT_DEFAULTS[canonical]
            # v22 brief 2 (DD §3): the world declined — warn, not error.
            await self.send_json({
                'type': 'output',
                'category': 'warn',
                'text': msg,
                'hint_exits': ', '.join(exits.keys()) if exits else 'none',
                'ts': envelope_ts(),
            })
            return

        char_name = self.character.name

        await self.channel_layer.group_send(self.room_group, {
            'type': 'room_message',
            'text': f'{char_name} has left.',
            'category': 'system',
            'exclude': self.channel_name,
            'ts': envelope_ts(),
        })
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

        await self.move_character(destination)
        first_visit = await self.record_room_visit(self.character, destination)
        self.last_direction = DIRECTION_CANONICAL[direction]
        self.room_group = f'room_{destination.id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)

        await self.channel_layer.group_send(self.room_group, {
            'type': 'room_message',
            'text': f'{char_name} has arrived.',
            'category': 'system',
            'exclude': self.channel_name,
            'ts': envelope_ts(),
        })

        # Re-fetch with full select_related (destination from exit FK lacks area pre-fetch)
        destination = await self.get_current_room()

        # v21 brief 1 (#81): an aggro room renders like any other entry —
        # full room render first (its who's-here section introduces the
        # attackers), then definite-article engagement lines (the render
        # already introduced the NPCs), then combat state last so the
        # combat-red status is the final status the client receives.
        await self.send_room_description(destination, entering=True,
                                         first_visit=first_visit)
        aggro_npcs = await self.get_aggro_npcs_in_room(destination)
        if aggro_npcs:
            for npc in aggro_npcs:
                # v21 brief 3 (#64): ordinal-aware while duplicates share
                # the visible name — singles render exactly as before.
                await self.send_output(
                    f"{npc_display_name(npc, aggro_npcs, capitalize=True)} "
                    "snarls and moves to attack!",
                    'combat',
                )
            session = await self.start_combat(aggro_npcs, first_attacker='npc')
            # v20 brief 4 (#2): engagement — fight feed + combat-red state.
            await self.send_fight(session)
            await self.send_status_refresh()
        await self.send_map()

    async def cmd_travel(self, args):
        # v20 brief 3 (#23): travel is movement too — the combat block
        # fires centrally in _dispatch since v22 brief 2.
        room = await self.get_current_room()
        node = await self.get_travel_node(room)

        if node is None:
            await self.output(
                'There is no obelisk here. Travel is a gift of the obelisks — '
                'you must stand before one.', 'warn',
            )
            return
        if node.node_type != 'obelisk':
            await self.output(
                'The obelisks project their protection here, but only an obelisk '
                'itself can send you onward.', 'warn',
            )
            return

        destinations = await self.get_revealed_destinations(node)

        if not args:
            if not destinations:
                await self.output(
                    'The Obelisk is silent. It has nothing to show you yet — '
                    'the network reveals itself only to those who walk it.', 'report',
                )
                return
            # v22 brief 2 (Step 11, DD ruling): destinations sort
            # ascending by straight-line map-space distance from the
            # player (same-zone; other-zone entries follow, by name), and
            # every entry is labeled shard (checkpoint) or sphere
            # (obelisk).
            def _distance_key(dest):
                dest_room = dest.room
                if dest_room.zone_id != room.zone_id:
                    return (1, 0.0, dest.travel_name.lower())
                dist = ((dest_room.coord_x - room.coord_x) ** 2
                        + (dest_room.coord_y - room.coord_y) ** 2
                        + (dest_room.coord_z - room.coord_z) ** 2) ** 0.5
                return (0, dist, dest.travel_name.lower())

            lines = ['The Obelisk offers passage to:']
            for dest in sorted(destinations, key=_distance_key):
                label = 'sphere' if dest.node_type == 'obelisk' else 'shard'
                lines.append(f'  {dest.travel_name} ({label})')
            await self.output('\n'.join(lines), 'report')
            return

        query = args.strip().lower()
        matches = [d for d in destinations if self._travel_name_matches(d.travel_name, query)]

        if not matches:
            await self.output(
                'The Obelisk knows no such place — or you have not yet stood there. '
                'Type "travel" to see where it can send you.', 'warn',
            )
            return
        if len(matches) > 1:
            names = ', '.join(d.travel_name for d in matches)
            await self.output(
                f'The Obelisk offers more than one such passage: {names}. '
                'Be more specific.', 'warn',
            )
            return

        destination = matches[0].room
        char_name = self.character.name

        departure = await self.get_random_travel_message('departure')
        if departure:
            await self.broadcast_to_room_exclude(departure.replace('{name}', char_name), 'room')

        await self.channel_layer.group_discard(self.room_group, self.channel_name)
        await self.move_character(destination)
        first_visit = await self.record_room_visit(self.character, destination)
        self.last_direction = None
        self.room_group = f'room_{destination.id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)

        traveler = await self.get_random_travel_message('traveler')
        if traveler:
            await self.output(traveler, 'room')

        # Re-fetch with full select_related, same as normal movement.
        destination = await self.get_current_room()
        await self.send_room_description(destination, entering=True,
                                         first_visit=first_visit)
        await self.send_map()

        arrival = await self.get_random_travel_message('arrival')
        if arrival:
            await self.broadcast_to_room_exclude(arrival.replace('{name}', char_name), 'room')

    @staticmethod
    def _travel_name_matches(travel_name, query):
        """Case-insensitive prefix match, tolerating a leading 'The ' on the node name."""
        name = travel_name.lower()
        if name.startswith(query):
            return True
        return name.startswith('the ') and name[4:].startswith(query)

    async def cmd_say(self, text):
        # v22 brief 2 (DD §13): the '[say] ' prefix is dead — speech is
        # 'Name: message' in say-color, players and NPCs alike. The
        # speaker keeps receiving their own broadcast (double vision is
        # intentional; echo-off is the remedy). Bare say prompts via the
        # central fn-10 gate in _dispatch.
        await self.channel_layer.group_send(self.room_group, {
            'type': 'room_message',
            'text': f'{self.character.name}: {text}',
            'category': 'say',
            'ts': envelope_ts(),
        })
        await self.schedule_npc_dialogue_responses(text)

    async def cmd_who(self):
        # v22 brief 2 (DD §9, #98): one line — key-color label with the
        # embedded count, value-color names.
        keys = await self.redis.keys("shyland:online:*")
        names = await self.redis.mget(*keys) if keys else []
        online = sorted(parse_presence_name(n) for n in names if n)
        count = len(online)
        await self.send_report_lines([
            {'k': f'Players online ({count}):', 'v': f' {", ".join(online)}'},
        ])

    async def presence_heartbeat(self):
        while True:
            await asyncio.sleep(60)
            await self.redis.eval(
                PRESENCE_HEARTBEAT_LUA,
                1,
                f"shyland:online:{self.character_pk}",
                self.presence_value,
            )

    # ------------------------------------------------------------------
    # v22 brief 2 (DD §9): Kind-3 table rendering — muted column headers,
    # value-color rows, per-cell voice segments (durability bands, rarity
    # words). Widths derive from rendered text; the font is monospace.
    # ------------------------------------------------------------------

    @staticmethod
    def _table_lines(headers, rows, indent='  ', gap='   '):
        """Seg-form report lines for a table. A cell is a plain string
        (value voice) or a list of (text, voice) tuples."""
        def cell_text(cell):
            if isinstance(cell, str):
                return cell
            return ''.join(t for t, _ in cell)

        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(cell_text(cell)))

        header_text = indent + gap.join(
            h.ljust(widths[i]) for i, h in enumerate(headers)
        ).rstrip()
        lines = [{'segs': [{'t': header_text, 'c': 'muted'}]}]
        for row in rows:
            segs = [{'t': indent, 'c': 'value'}]
            for i, cell in enumerate(row):
                if isinstance(cell, str):
                    segs.append({'t': cell, 'c': 'value'})
                else:
                    segs.extend({'t': t, 'c': c} for t, c in cell)
                if i < len(row) - 1:
                    pad = widths[i] - len(cell_text(cell))
                    segs.append({'t': ' ' * pad + gap, 'c': 'value'})
            lines.append({'segs': segs})
        return lines

    @staticmethod
    def _details_cell(item):
        """DD §9: Details = durability + flags, no brackets —
        '90%, Uncommon, Bound'. The durability voice derives from the
        mechanical durability band (never its own thresholds): no
        penalty → value, penalty bands → say, broken → error. Rarity
        words are always rarity-colored in information output."""
        segs = []
        if item.definition.takes_durability_loss:
            if item.is_broken:
                voice = 'error'
            elif get_durability_penalty(item) > 0:
                voice = 'say'
            else:
                voice = 'value'
            segs.append((f'{int(round(item.durability_current))}%', voice))
        if item.is_identified:
            if segs:
                segs.append((', ', 'value'))
            segs.append((item.rarity.capitalize(), f'rar-{item.rarity}'))
        if segs:
            segs.append((', ', 'value'))
        segs.append(('Bound' if item.is_soulbound else 'Unbound', 'flag-chrome'))
        return segs

    def _wallet_line(self, char):
        """DD §9: THE wallet line — one renderer shared by `wallet` and
        inv's Wallet section, byte-identical output."""
        return {'k': 'Wallet:', 'v': f' {self.format_wallet(char)}'}

    async def cmd_inventory(self):
        items = await self.get_inventory()
        char = self.character

        equipped = [i for i in items if i.is_equipped]
        unequipped = [i for i in items if not i.is_equipped]

        bag_bonus = sum(
            i.definition.carry_bonus for i in equipped if i.definition.item_type == 'bag'
        )
        max_carry = char.stat_str * 10 + bag_bonus
        current_carry = len(unequipped)

        # v22 brief 2 (DD §9): Equipment paper-doll — every slot always
        # shown, anatomical order, sentence-case labels, muted '-' for
        # empties. Header punctuation law: ellipsis = structure below.
        lines = [{'k': 'Equipment...'}]
        by_slot = {}
        for item in equipped:
            by_slot.setdefault(item.equipped_slot, []).append(item)
        doll_rows = []
        for slot in SLOT_ORDER:
            occupants = by_slot.get(slot, [])
            for i in range(SLOT_CAPACITY.get(slot, 1)):
                label = format_slot_name(slot)
                if i < len(occupants):
                    item = occupants[i]
                    doll_rows.append([
                        label,
                        get_display_name_with_tier(item),
                        self._details_cell(item),
                    ])
                else:
                    doll_rows.append([
                        label, [('-', 'muted')], [('-', 'muted')],
                    ])
        lines += self._table_lines(['Slot', 'Name', 'Details'], doll_rows)

        # Inventory table: Quantity after Name, Slot empty unless slotted
        # (unequipped items never are), flat alphabetical by name.
        lines.append({})
        lines.append({'k': f'Inventory ({current_carry}/{max_carry})...'})
        unequipped_sorted = sorted(
            unequipped, key=lambda i: get_display_name_with_tier(i).lower(),
        )
        inv_rows = []
        idx = 0
        while idx < len(unequipped_sorted):
            item = unequipped_sorted[idx]
            count = 1
            if item.definition.item_type == 'consumable':
                j = idx + 1
                while j < len(unequipped_sorted):
                    other = unequipped_sorted[j]
                    if (other.definition_id == item.definition_id
                            and other.mk_tier == item.mk_tier
                            and other.rarity == item.rarity):
                        count += 1
                        j += 1
                    else:
                        break
                idx = j
            else:
                idx += 1
            inv_rows.append([
                '',
                get_display_name_with_tier(item),
                str(count),
                self._details_cell(item),
            ])
        lines += self._table_lines(
            ['Slot', 'Name', 'Quantity', 'Details'], inv_rows,
        )

        wallet_char = await self.get_character_fresh()
        lines.append({})
        lines.append(self._wallet_line(wallet_char))

        # v20 brief 2 amendment 1 (#56): state reports carry 'report'
        # (unstamped on the client) — inventory, wallet, help, who, stats,
        # vendor list, examine, travel listing, brief query.
        await self.send_report_lines(lines)

    async def cmd_wallet(self):
        # v21 brief 1 (#92) + v22 brief 2 (DD §9): the shared wallet-line
        # renderer — byte-identical to inv's Wallet section.
        char = await self.get_character_fresh()
        await self.send_report_lines([self._wallet_line(char)])

    # v21 brief 1 (#84): the help text. The movement line is static —
    # help documents the command set, not the current room. Commands
    # taking item arguments reference <item selection>; the grammar is
    # explained once in the Item selection section. Bracketed
    # alternatives use spaces around the pipe everywhere. Amendment 1:
    # the render sorts alphabetically by leading command word — table
    # order doesn't matter.
    HELP_COMMANDS = [
        ('look / l', 'describe this room'),
        ('say <text>', 'speak to players here; NPCs may listen too'),
        ('who', 'list players online'),
        ('inventory / inv', 'show carried items and equipment'),
        ('wallet', 'show your copper'),
        ('pickup (p) <item selection>', 'pick up an item from the room'),
        ('drop <item selection>', 'drop a carried item (unbound items only)'),
        ('equip (eq) <item selection>', 'equip a carried item'),
        ('unequip (uneq) <item selection>', 'unequip an equipped item'),
        ('use <item selection>', 'use a consumable'),
        ('examine (ex) <item selection>', 'inspect an item, NPC, or corpse in detail'),
        ('loot [corpse] [<item selection> | all]',
         "loot a corpse; bare 'loot' or 'loot all' takes everything from your most recent kill"),
        ('travel [destination]', 'fast-travel via the Obelisk Network (from an obelisk)'),
        ('list', 'see what a vendor here has for sale'),
        ('buy <item selection>', 'buy an item from a vendor here'),
        ('sell <item selection>', 'sell an unequipped item to a vendor here'),
        ('repair [<item selection> | all]', 'pay a mender here to repair damaged gear'),
        ('kill / attack (k) [npc]',
         'attack an NPC; bare attack strikes back at whatever hit you first'),
        ('flee', 'attempt to escape from combat'),
        ('stats', 'show your character stats and XP'),
        ('spend <stat> <amount>', 'spend stat points (e.g. spend dex 2)'),
        ('brief on | off', 'short room descriptions for rooms you have seen'),
        ('timestamps on | off', 'show or hide message timestamps'),
        ('quit', 'leave the game and return to the games lobby'),
        ('help / ?', 'show this list'),
    ]

    async def cmd_help(self):
        # Amendment 1 (#84): structured key/value form — section headers
        # (Movement:, Commands:, Item selection:) in key-color, every
        # other line value-colored; commands alphabetical.
        width = max(len(cmd) for cmd, _ in self.HELP_COMMANDS) + 2
        lines = [
            {'k': 'Movement:',
             'v': ' north (n), south (s), east (e), west (w), up (u), down (d)'},
            {},
            {'k': 'Commands:'},
        ]
        lines += [
            {'v': f'  {cmd:<{width}}— {desc}'}
            for cmd, desc in sorted(self.HELP_COMMANDS,
                                    key=lambda entry: entry[0].split()[0])
        ]
        lines += [
            {},
            {'k': 'Item selection:'},
            {'v': "  Commands marked <item selection> accept: a name or prefix ('axe', 'battle axe'),"},
            {'v': "  an index ('2.axe' — the second match), a quantity ('3 axes'), 'all' ('all axes'),"},
            {'v': "  and a rarity filter ('sell uncommon axe', 'sell all common')."},
            {},
            {'v': 'Tab completes commands and item names.'},
        ]
        await self.send_report_lines(lines)

    async def cmd_quit(self):
        # v22 brief 2 (DD §5): quit is allowed in combat and while dying —
        # combat continues after quit (CombatSession is DB state; the
        # player can die logged out). Tab-closing and quitting are
        # identical in cost.
        await self.output('The world folds itself away behind you. Come back soon.', 'system')
        await self.send_json({'event': 'quit', 'ts': envelope_ts()})
        # Normal close; the disconnect path owns presence delete, group
        # discards, and heartbeat cancellation.
        await self.close()

    async def cmd_pickup(self, args):
        char = self.character
        room = await self.get_current_room()
        room_items = await self.get_room_items(room)

        res = resolve('pickup', args, room_items)
        if not res.ok:
            await self.output(res.message, self._refusal_category(res))
            return

        # v22 brief 2 (DD §7): any pickup at capacity fails outright.
        current_count, max_capacity = await self.get_carry_capacity(char)
        if current_count >= max_capacity:
            await self.output(
                f"You can't carry any more. ({current_count}/{max_capacity} items)",
                'warn',
            )
            return

        taken = 0
        for item in res.items:
            if current_count >= max_capacity:
                # Partial sweep: oldest-first has been taken; report warmly.
                await self.output(
                    f"You can't carry the rest. ({current_count}/{max_capacity} items)",
                    'warn',
                )
                break

            display_name = get_display_name(item)
            await self.transfer_to_character(item, char)
            current_count += 1
            taken += 1

            # DD §6: pickup lines are gains — loot-color (reward).
            await self.output(f'You pick up {item_ref(item)}.', 'reward')
            await self.channel_layer.group_send(self.room_group, {
                'type': 'room_message',
                'text': f'{char.name} picks up {display_name}.',
                'category': 'room',
                'exclude': self.channel_name,
                'ts': envelope_ts(),
            })
        if res.requested and taken == len(res.items):
            await self.output(f'There were only {taken} here.', 'system')

    async def cmd_drop(self, args):
        char = self.character
        room = await self.get_current_room()
        carried_items = await self.get_carried_items(char)
        # v22 brief 2 (DD §8 fn 16): bound items are excluded from drop's
        # candidate pool entirely.
        unbound = [i for i in carried_items if not i.is_soulbound]

        res = resolve('drop', args, unbound)
        if not res.ok:
            if res.error == 'not_found':
                # A match that exists only among bound items is a
                # mechanical refusal, not a resolution miss (DD §3).
                bound_res = resolve('drop', args, carried_items)
                if bound_res.ok:
                    await self.output(
                        f'Your {get_display_name(bound_res.items[0])} is bound '
                        'to you and cannot be dropped.', 'warn',
                    )
                    return
            await self.output(res.message, self._refusal_category(res))
            return

        # Equipped items never resolve for drop (policy).
        for item in res.items:
            display_name = get_display_name(item)
            await self.transfer_to_room(item, room)

            await self.output(f'You drop {item_ref(item)}.', 'success')
            await self.channel_layer.group_send(self.room_group, {
                'type': 'room_message',
                'text': f'{char.name} drops {display_name}.',
                'category': 'room',
                'exclude': self.channel_name,
                'ts': envelope_ts(),
            })
        if res.requested:
            await self.output(f'You only had {len(res.items)}.', 'system')

    async def cmd_equip(self, args):
        char = self.character
        unequipped_items = await self.get_carried_unequipped_items(char)
        # Candidate scope (#22): carried equippables only.
        equippables = [i for i in unequipped_items if i.definition.valid_slots]

        res = resolve('equip', args, equippables)
        if not res.ok:
            await self.output(res.message, self._refusal_category(res))
            return

        item = res.items[0]
        defn = item.definition

        equipped_items = await self.get_equipped_items(char)

        # One candidate per way the item could go on: (slot, items displaced).
        # A two-handed item claims both hands from any slot it occupies; a
        # one-handed item going into a hand conflicts with any equipped
        # two-handed item, wherever that item sits (including RANGED).
        candidates = []
        for slot in defn.valid_slots:
            occupants = [i for i in equipped_items if i.equipped_slot == slot]
            capacity = SLOT_CAPACITY.get(slot, 1)

            if defn.is_two_handed:
                extras = [
                    i for i in equipped_items
                    if i.equipped_slot in ('MAIN_HAND', 'OFF_HAND')
                    or i.definition.is_two_handed
                ]
            elif slot in ('MAIN_HAND', 'OFF_HAND'):
                extras = [i for i in equipped_items if i.definition.is_two_handed]
            else:
                extras = []

            base_sets = [[]] if len(occupants) < capacity else [[o] for o in occupants]
            for base in base_sets:
                displaced, seen = [], set()
                for equipped in base + extras:
                    if equipped.pk not in seen:
                        seen.add(equipped.pk)
                        displaced.append(equipped)
                candidates.append((slot, displaced))

        # A slot the item can occupy without displacing anything wins outright.
        free = next(((slot, d) for slot, d in candidates if not d), None)
        if free is not None:
            target_slot = free[0]
            await self.equip_item(item, target_slot, char)
            # v22 brief 2 (DD §6): the transactional sentence — no slot
            # mention; the paper-doll carries slot placement now.
            await self.output(f'You equip {item_ref(item)}.', 'success')
            return

        min_size = min(len(d) for _, d in candidates)
        minimal = [(slot, d) for slot, d in candidates if len(d) == min_size]

        if min_size >= 2:
            _, displaced = minimal[0]
            await self.output(
                f"You'd have to unequip {_join_owned_names(displaced, 'and')} first.",
                'warn',
            )
            return

        # Exactly one item must come off. If different candidate slots would
        # displace different items, the choice is the player's — refuse.
        distinct, seen = [], set()
        for _, d in minimal:
            if d[0].pk not in seen:
                seen.add(d[0].pk)
                distinct.append(d[0])

        if len(distinct) > 1:
            if all(slot == 'RING' for slot, _ in minimal):
                msg = (
                    f"Both ring slots are full — "
                    f"unequip {_join_owned_names(distinct, 'or')} first."
                )
            else:
                msg = f"You'd have to unequip {_join_owned_names(distinct, 'or')} first."
            await self.output(msg, 'warn')
            return

        # Unambiguous one-for-one exchange: auto-swap, if the displaced item
        # can legally come off. Never perform a partial swap.
        displaced_item = distinct[0]
        target_slot = minimal[0][0]

        unequipped_count = 0
        if displaced_item.definition.item_type == 'bag':
            unequipped_count = await self.count_unequipped_items(char)
        blocked = self._unequip_blocked_reason(displaced_item, equipped_items, unequipped_count)
        if blocked:
            await self.output(blocked, 'warn')
            return

        await self.unequip_item(displaced_item)
        await self.equip_item(item, target_slot, char)
        # v22 brief 2 (DD §6): the swap-aware sentence.
        await self.output(
            f'You equip {item_ref(item)}, replacing {item_ref(displaced_item)}.',
            'success',
        )

    async def cmd_unequip(self, args):
        char = self.character
        equipped_items = await self.get_equipped_items(char)

        res = resolve('unequip', args, equipped_items)
        if not res.ok:
            await self.output(res.message, self._refusal_category(res))
            return

        item = res.items[0]

        unequipped_count = 0
        if item.definition.item_type == 'bag':
            unequipped_count = await self.count_unequipped_items(char)
        blocked = self._unequip_blocked_reason(item, equipped_items, unequipped_count)
        if blocked:
            await self.output(blocked, 'warn')
            return

        await self.unequip_item(item)
        await self.output(f'You unequip {item_ref(item)}.', 'success')

    def _unequip_blocked_reason(self, item, equipped_items, unequipped_count):
        """Return the refusal message if the item cannot legally be unequipped, else None."""
        if item.is_cursed:
            return f"Your {get_display_name(item)} is cursed and cannot be removed."
        if item.definition.item_type == 'bag':
            other_bag_bonus = sum(
                i.definition.carry_bonus for i in equipped_items
                if i.definition.item_type == 'bag' and i.pk != item.pk
            )
            new_limit = self.character.stat_str * 10 + other_bag_bonus
            if (unequipped_count + 1) > new_limit:
                return f"You're carrying too many items to remove your {get_display_name(item)}."
        return None

    async def cmd_use(self, args):
        # v22 brief 2 (DD §1 fn 11, #65): 'use [<quantity>] <item>' with a
        # numeric-only quantity — sequences apply one item at a time and
        # stop when purpose is fulfilled (DD §7, #61 generalized).
        char = self.character
        was_dying = self._character_is_dying
        consumables = await self.get_carried_consumables(char)

        res = resolve('use', args, consumables)
        if not res.ok:
            await self.output(res.message, self._refusal_category(res))
            return

        used = 0
        stopped_at_full = False
        for item in res.items:
            effect_def = item.definition.effect

            if effect_def is None:
                await self.output('Nothing happens.', 'system')
                break

            is_heal = await self.effect_restores_vitality(effect_def)
            if is_heal and not was_dying:
                gate_char = await self.get_character_fresh()
                if gate_char.vitality_current >= gate_char.vitality_max:
                    # DD §7 / #61: any heal attempted at full fails; a
                    # sequence that just reached full already said so.
                    if used == 0:
                        await self.output('You are already at full health.', 'warn')
                    stopped_at_full = True
                    break

            msgs = await self.do_apply_effect(effect_def, char, item.mk_tier)
            await self.consume_item(item)
            used += 1

            # DD §6: the transactional sentence, then the effect line.
            await self.output(f'You use {item_ref(item, indefinite=True)}.', 'success')
            for msg in msgs:
                await self.output(msg, 'system')

            room = await self.get_current_room()
            char_fresh = await self.get_character_fresh()

            if was_dying and char_fresh.vitality_current > 0:
                await self.revive_character(char_fresh)
                self._character_is_dying = False
                await self.output(
                    "Breath floods back into your lungs. You are alive — barely.", 'system',
                )
                await self.send_room_description(room, entering=False)
                await self.broadcast_to_room_exclude(
                    f"{char_fresh.name} staggers back to their feet!", 'combat',
                )
                return

            if is_heal and char_fresh.vitality_current >= char_fresh.vitality_max:
                # DD §7: purpose fulfilled — the loot-color line, stop.
                await self.output('You have been restored to full health.', 'reward')
                stopped_at_full = True
                break

        if used:
            if res.requested and not stopped_at_full and used == len(res.items):
                await self.output(f'You only had {used}.', 'system')
            room = await self.get_current_room()
            char_fresh = await self.get_character_fresh()
            await self.send_json(await self._status_payload(char_fresh, room))

    def _format_identified_item_lines(self, item):
        defn = item.definition
        lines = []
        # v20 brief 3 (#48): composed headline; rarity lives in the
        # trailing flag block now.
        lines.append(compose_item_line(item))
        lines.append(f'  {defn.description}')
        lines.append('')
        lines.append(f'  Type:       {defn.item_type.title()}')
        lines.append(f'  Genre:      {defn.genre_tag.title()}')

        if (defn.item_type == 'weapon'
                and item.damage_midpoint is not None
                and item.damage_spread is not None):
            dmg_lo = int(item.damage_midpoint - item.damage_spread)
            dmg_hi = int(item.damage_midpoint + item.damage_spread)
            lines.append(f'  Damage:     {dmg_lo} – {dmg_hi}')

        if defn.takes_durability_loss:
            dur_str = f'  Durability: {int(item.durability_current)}%'
            if item.is_broken:
                dur_str += ' (BROKEN)'
            lines.append(dur_str)

        if defn.item_type == 'bag':
            lines.append(f'  Carry bonus: +{defn.carry_bonus}')

        if item.rolled_primary_stats:
            lines.append('')
            for entry in item.rolled_primary_stats:
                label = STAT_LABELS.get(entry['stat'], entry['stat'].replace('_', ' ').title())
                lines.append(f'  {label}: {entry["value"]}')

        if item.rolled_secondary_stats:
            if not item.rolled_primary_stats:
                lines.append('')
            for entry in item.rolled_secondary_stats:
                label = STAT_LABELS.get(entry['stat'], entry['stat'].replace('_', ' ').title())
                lines.append(f'  {label}: {entry["value"]}')

        if item.is_equipped:
            lines.append(f'  Equipped:   {format_slot_name(item.equipped_slot)}')

        if item.is_soulbound:
            lines.append('  Bound:      This item is bound to you.')

        if item.is_cursed and item.curse_identified:
            lines.append('  Curse:      This item carries a curse.')

        if not item.is_equipped and not item.is_soulbound:
            lines.append('  Note:       This item is not yet bound — you may drop it.')

        return lines

    async def cmd_examine(self, args):
        # v22 brief 2 (DD §8, #96): examine's pool is the union —
        # inventory + equipped + room floor + NPCs + corpses + players +
        # vendor stock — resolved nearest-first (self before room before
        # vendor) where segments overlap.
        char = self.character
        room = await self.get_current_room()
        carried_items = await self.get_carried_items(char)
        room_items = await self.get_room_items(room)
        combined = carried_items + room_items

        res = resolve('examine', args, combined)

        if not res.ok and res.error not in ('not_found',):
            await self.output(res.message, self._refusal_category(res))
            return

        if res.ok:
            item = res.items[0]
            lines = []
            if not item.is_identified:
                lines.append(compose_item_line(item))
                lines.append('')
                lines.append(f'  {get_display_description(item)}')
                lines.append('')
                lines.append('  (You cannot determine anything further about this item.)')
                if item.is_unidentifiable:
                    lines.append('  No known method of identification will reveal its true nature.')
            else:
                lines = self._format_identified_item_lines(item)
            await self.output('\n'.join(lines), 'report')
            return

        # Search live NPCs
        npcs = await self.get_npcs_in_room(room)
        noun_lower = args.strip().lower()
        npc_match = next(
            (n for n in npcs if noun_lower in npc_display(n).lower()), None,
        )

        if npc_match is not None:
            lines = [npc_display(npc_match, capitalize=True), '',
                     f'  {npc_match.definition.description}']
            await self.output('\n'.join(lines), 'report')
            return

        # Search corpses
        corpses = await self.get_corpses_in_room(room)
        code, corpse = parse_corpse_noun(args, corpses)

        if code == 'bad_index':
            await self.output("There aren't that many of those.", 'warn')
            return

        if code == 'single':
            from .currency import display_for_zone
            zone_slug = room.zone.slug if room.zone_id else None
            lines = [f'The corpse of {corpse.npc_name_snapshot}.']

            if corpse.copper_drop > 0:
                lines.append(f'  Currency:  {display_for_zone(corpse.copper_drop, zone_slug)}')
            else:
                lines.append('  Currency:  No currency.')

            if char.pk == corpse.killed_by_id:
                contents = await self.get_corpse_contents(corpse)
                if contents:
                    lines.append('')
                    for item in contents:
                        lines.append('')
                        lines.extend(self._format_identified_item_lines(item))
                else:
                    lines.append('  No items.')
            else:
                lines.append(
                    '  The body lies here, its belongings just out of reach. Whatever it was\n'
                    "  carrying is none of your business — you didn't make this kill."
                )

            await self.output('\n'.join(lines), 'report')
            return

        # Search players here (DD §8: players are in examine's union).
        players = await self.get_characters_in_room(room)
        player_match = next(
            (p for p in players if p.name.lower().startswith(noun_lower)), None,
        )
        if player_match is not None:
            await self.output(
                f'{player_match.name} - Level {player_match.level} '
                f'{player_match.origin.name} {player_match.archetype.name}',
                'report',
            )
            return

        # Search vendor stock last (self before room before vendor).
        vendor = await self.get_vendor_in_room(room)
        if vendor is not None:
            entries = await self.get_vendor_entries(vendor)
            stock = [e for e in entries if not self._entry_exhausted(e)]
            # VendorEntry candidates resolve through the entry-kind ('buy')
            # policy; only the match is used here.
            entry_res = resolve('buy', args, stock)
            if entry_res.ok:
                entry = entry_res.items[0]
                defn = entry.item_definition
                await self.output('\n'.join([
                    entry_display_name(entry),
                    '',
                    f'  {defn.description}',
                    '',
                    f'  Type:       {defn.item_type.title()}',
                    f'  Genre:      {defn.genre_tag.title()}',
                ]), 'report')
                return

        await self.output("You don't see that here.", 'warn')

    async def cmd_loot(self, args):
        # v22 brief 2 (DD §1): 'loot all | <NPC>' — a room sweep, or one
        # corpse named by its NPC. The v20 item-noun forms are retired
        # with the chart; bare loot prompts via the central fn-10 gate.
        room = await self.get_current_room()
        character = await self.get_character(self.scope['user'])
        corpses = await self.get_corpses_in_room(room)

        if not corpses:
            await self.output("There is nothing to loot here.", "warn")
            return

        if args.strip().lower() == 'all':
            lootable = [c for c in corpses if c.killed_by_id == character.pk]
            if not lootable:
                await self.output("That is not your kill; you may not loot it.", "warn")
                return
            await self._loot_sweep(character, room, lootable)
            return

        code, matched = parse_corpse_noun(args.strip(), corpses)
        if code == 'single':
            await self._loot_single_corpse(character, room, matched, None)
            return
        if code == 'bad_index':
            await self.output("There aren't that many corpses here.", "warn")
            return
        await self.output("You don't see that corpse here.", "warn")

    async def _loot_corpse_copper(self, character, room, corpse):
        """Loot a corpse's coin drop, emitting the coin line if any.
        Returns the amount taken."""
        from .currency import display_for_zone
        amount = await self.do_loot_copper(corpse, character)
        if amount > 0:
            zone_slug = room.zone.slug if room.zone_id else None
            copper_str = display_for_zone(amount, zone_slug)
            await self.output(f"You loot {copper_str} from {corpse.display_name}.", "success")
        return amount

    @staticmethod
    def _corpse_npc_ref(corpse, capitalize=False):
        """Composed reference for the NPC a corpse belonged to. Falls back
        to the name snapshot (itself composed at death) if the definition
        has since been deleted."""
        if corpse.npc_definition_id:
            return npc_display(corpse.npc_definition, capitalize)
        text = corpse.npc_name_snapshot
        return f'{text[0].upper()}{text[1:]}' if (capitalize and text) else text

    async def _maybe_dispose_corpse(self, corpse):
        deleted = await self.check_corpse_empty_and_delete(corpse)
        if deleted:
            name = corpse.display_name
            await self.channel_layer.group_send(self.room_group, {
                'type': 'room_message',
                'text': f"{name[0].upper()}{name[1:]} slowly disappears.",
                'category': 'room',
                'ts': envelope_ts(),
            })

    async def _loot_single_corpse(self, character, room, target_corpse, item_noun=None):
        """Loot one targeted corpse in full — 'loot <NPC>' (v22 brief 2:
        the chart's corpse-by-name form; item nouns are retired)."""
        if target_corpse.killed_by_id != character.pk:
            await self.output("That is not your kill; you may not loot it.", "warn")
            return

        copper_taken = await self._loot_corpse_copper(character, room, target_corpse)

        contents = await self.get_corpse_contents(target_corpse)

        if not contents:
            # v20 brief 5 (#28): an empty corpse answers honestly. A corpse
            # that never had loot to give (no loot table, no coin capacity —
            # normal-tier NPCs drop nothing by design) "carried nothing
            # worth taking"; one this player emptied keeps a distinct,
            # accurate line. A loot that just took the coin drop needs no
            # complaint at all.
            if copper_taken == 0:
                defn = target_corpse.npc_definition
                never_had_loot = (
                    defn is not None
                    and defn.loot_table_id is None
                    and defn.currency_drop_max == 0
                )
                if never_had_loot:
                    await self.output(
                        f"{self._corpse_npc_ref(target_corpse, capitalize=True)} "
                        "carried nothing worth taking.", "system",
                    )
                else:
                    await self.output(
                        "You've already taken everything from "
                        f"{self._corpse_npc_ref(target_corpse)}.", "system",
                    )
            await self._maybe_dispose_corpse(target_corpse)
            return

        current_count, max_carry = await self.get_carry_counts(character)

        for item in contents:
            if current_count >= max_carry:
                await self.output(
                    f"You can't carry any more. ({current_count}/{max_carry} items)",
                    "warn"
                )
                break
            line = compose_item_line(item)
            await self.do_loot_item(item, character)
            await self.output(f"You loot {line}.", "success")
            current_count += 1

        await self._maybe_dispose_corpse(target_corpse)

    async def _loot_sweep(self, character, room, lootable):
        """v20 brief 3 amendment 1 (#62): 'loot all' sweeps every corpse
        in the room the character may loot. Per-item and coin lines
        exactly as single-corpse looting emits them (each its own
        message); empty corpses make no individual noise — the summary
        counts them. Stops early if the character fills up."""
        current_count, max_carry = await self.get_carry_counts(character)
        swept = 0
        carried_nothing = 0
        capacity_hit = False

        for corpse in lootable:
            swept += 1
            copper = await self._loot_corpse_copper(character, room, corpse)
            contents = await self.get_corpse_contents(corpse)
            if copper == 0 and not contents:
                carried_nothing += 1
            for item in contents:
                if current_count >= max_carry:
                    await self.output(
                        f"You can't carry any more. ({current_count}/{max_carry} items)",
                        "warn"
                    )
                    capacity_hit = True
                    break
                line = compose_item_line(item)
                await self.do_loot_item(item, character)
                await self.output(f"You loot {line}.", "success")
                current_count += 1
            await self._maybe_dispose_corpse(corpse)
            if capacity_hit:
                break

        summary = f'Looted {swept} corpse{"s" if swept != 1 else ""}'
        if carried_nothing:
            summary += (f'; {carried_nothing} carried nothing worth taking.')
        else:
            summary += '.'
        await self.output(summary, 'system')

    # ------------------------------------------------------------------
    # Commerce commands
    # ------------------------------------------------------------------

    @staticmethod
    def _entry_exhausted(entry):
        return entry.stock_limit is not None and entry.sold_count >= entry.stock_limit

    async def cmd_list(self):
        room = await self.get_current_room()
        vendor = await self.get_vendor_in_room(room)
        if vendor is None:
            await self.output('There is no one here to trade with.', 'warn')
            return

        entries = await self.get_vendor_entries(vendor)
        listable = [e for e in entries if not self._entry_exhausted(e)]
        if not listable:
            await self.output(
                f'{npc_display(vendor, capitalize=True)} has nothing left for sale.',
                'report',
            )
            return

        char = await self.get_character_fresh()

        # v22 brief 2 (DD §9, #58): the standard table + Price — two
        # groups, free first (Price reads muted 'free'), alphabetical
        # within groups; vendor stock mints Common at full durability.
        def entry_row(entry):
            defn = entry.item_definition
            details = []
            if defn.takes_durability_loss:
                details.append(('100%', 'value'))
                details.append((', ', 'value'))
            details.append(('Common', 'rar-common'))
            if entry.price == 0:
                price_cell = [('free', 'muted')]
            else:
                price_cell = self.format_amount(char, entry.price)
            quantity = ('' if entry.stock_limit is None
                        else str(entry.stock_limit - entry.sold_count))
            return ['', entry_display_name(entry), quantity, details, price_cell]

        free = sorted((e for e in listable if e.price == 0),
                      key=lambda e: entry_display_name(e).lower())
        priced = sorted((e for e in listable if e.price > 0),
                        key=lambda e: entry_display_name(e).lower())
        rows = [entry_row(e) for e in free + priced]

        lines = [{'k': f'{npc_display(vendor, capitalize=True)} offers...'}]
        lines += self._table_lines(
            ['Slot', 'Name', 'Quantity', 'Details', 'Price'], rows,
        )
        await self.send_report_lines(lines)

    async def cmd_buy(self, args):
        room = await self.get_current_room()
        vendor = await self.get_vendor_in_room(room)
        if vendor is None:
            await self.output('There is no one here to trade with.', 'warn')
            return

        entries = await self.get_vendor_entries(vendor)
        res = resolve('buy', args, entries)
        if not res.ok:
            await self.output(res.message, self._refusal_category(res))
            return

        entry = res.items[0]
        qty = res.quantity
        requested = 0
        if self._entry_exhausted(entry):
            await self.output('Sold out.', 'warn')
            return
        if entry.stock_limit is not None:
            left = entry.stock_limit - entry.sold_count
            if left < qty:
                # v22 brief 2 (DD §7, by analogy): do the possible part —
                # buy what's there and report warmly.
                requested = qty
                qty = left

        # v20 brief 3 (#22): funds and carry capacity checked up front for
        # the whole quantity — the purchase itself stays all-or-nothing.
        char = await self.get_character_fresh()
        total = entry.price * qty
        if total > char.copper:
            await self.output(
                f"You can't afford that — it costs {self.format_amount(char, total)}.",
                'warn',
            )
            return

        current_count, max_capacity = await self.get_carry_capacity(char)
        if current_count + qty > max_capacity:
            if qty == 1:
                msg = f"You can't carry any more. ({current_count}/{max_capacity} items)"
            else:
                msg = f"You can't carry {qty} more. ({current_count}/{max_capacity} items)"
            await self.output(msg, 'warn')
            return

        result = await self.do_buy(entry, char, qty)
        if result == 'poor':
            await self.output(
                f"You can't afford that — it costs {self.format_amount(char, total)}.",
                'warn',
            )
            return
        if result == 'sold_out':
            await self.output('Sold out.', 'warn')
            return
        # v22 brief 2 (DD §6): one line per item as it lands.
        for instance in result:
            await self.output(
                f'You buy {item_ref(instance)} for '
                f'{self.format_amount(char, entry.price)}.', 'success',
            )
        if requested:
            await self.output(f'They only had {qty}.', 'system')
        await self.maybe_kibitz(room, vendor)

    async def cmd_sell(self, args):
        room = await self.get_current_room()
        vendor = await self.get_vendor_in_room(room)
        if vendor is None:
            await self.output('There is no one here to trade with.', 'warn')
            return

        char = self.character
        carried = await self.get_carried_items(char)
        res = resolve('sell', args, carried)
        if not res.ok:
            await self.output(res.message, self._refusal_category(res))
            return

        if res.mode in ('single', 'index'):
            item = res.items[0]
            if get_item_value(item) == 0:
                await self.output("That's not worth anything to me.", 'warn')
                return
            display = item_ref(item)
            price = await self.do_sell(item, char)
            await self.output(f'You sell {display} for {self.format_amount(char, price)}.', 'success')
            await self.maybe_kibitz(room, vendor)
            return

        # v20 brief 3 (#21) + amendment 1 (#63): 'sell all <noun>' /
        # 'sell N <noun>' / 'sell all <rarity>'. Bulk operations narrate
        # as streams of events: each sale is its own message (own ts/seq
        # through the choke point), the total is its own message, and the
        # zero-value skip summary is its own message — never one joined
        # batch under a single stamp.
        sold = 0
        total = 0
        skipped = 0
        for item in res.items:
            if get_item_value(item) == 0:
                skipped += 1
                continue
            display = item_ref(item)
            price = await self.do_sell(item, char)
            sold += 1
            total += price
            await self.output(f'You sell {display} for {self.format_amount(char, price)}.', 'success')
        if sold:
            # v22 brief 2 (DD §6/§7): the shortfall report, verbatim.
            if res.requested:
                await self.output(
                    f'You only had {sold} — the vendor was happy to take them.',
                    'success',
                )
            await self.output(
                f'Sold {sold} item{"s" if sold != 1 else ""} '
                f'for {self.format_amount(char, total)}.', 'success',
            )
            if skipped:
                await self.output(
                    f'({skipped} worthless item'
                    f'{"s" if skipped != 1 else ""} skipped.)', 'system',
                )
            await self.maybe_kibitz(room, vendor)
        else:
            await self.output(
                f'Nothing sold — {skipped} worthless item'
                f'{"s" if skipped != 1 else ""} skipped.', 'warn',
            )

    async def cmd_repair(self, args):
        char = await self.get_character_fresh()
        room = await self.get_current_room()
        repairer = await self.get_repairer_in_room(room)
        if repairer is None:
            await self.output('There is no one here who can repair.', 'warn')
            return

        arg = args.strip().lower() if args else ''
        damaged = await self.get_damaged_items(char)

        if arg == 'all':
            if not damaged:
                await self.output('You have nothing to repair.', 'warn')
                return
            # v20 brief 4 amendment 1 (#74): the #63 bulk-operation rule —
            # each repair attempt is its own message through the choke
            # point (own ts/seq), and the summary is its own message.
            # v22 brief 2 (DD §7, #75): bounded retries — the sweep loops
            # over what's still damaged until everything is repaired,
            # funds run out, or 5 passes; each mend line prints as it
            # lands.
            repaired = failed = spent = 0
            out_of_funds = False
            for _ in range(5):
                if not damaged or out_of_funds:
                    break
                still_damaged = []
                for item in damaged:
                    name = get_display_name_with_tier(item)
                    outcome, cost = await self.do_repair_attempt(item, char)
                    if outcome == 'poor':
                        await self.output(
                            f"You can't afford to repair {name} "
                            f"({self.format_amount(char, cost)}) — you stop there.",
                            'warn',
                        )
                        out_of_funds = True
                        break
                    spent += cost
                    if outcome == 'success':
                        repaired += 1
                        if get_item_value(item) == 0:
                            await self.output(_pity_repair_line(repairer), 'success')
                        else:
                            await self.output(
                                f'{name} is restored to full condition. '
                                f'({self.format_amount(char, cost)})',
                                'success',
                            )
                    else:
                        failed += 1
                        still_damaged.append(item)
                        await self.output(
                            f"The mending on {name} didn't take. "
                            f"({self.format_amount(char, cost)})",
                            'warn',
                        )
                damaged = still_damaged
            await self.output(
                f'Repaired {repaired} item{"s" if repaired != 1 else ""}, '
                f'{failed} attempt{"s" if failed != 1 else ""} failed, '
                f'{self.format_amount(char, spent)} spent.',
                'system',
            )
            return

        # v22 brief 2 (DD §1): 'repair all | <item>' — a target is required;
        # bare repair prompts via the central fn-10 gate.
        # Repair scope (#22): carried + equipped — everything owned.
        items = await self.get_carried_items(char)
        res = resolve('repair', args, items)
        if not res.ok:
            await self.output(res.message, self._refusal_category(res))
            return
        item = res.items[0]
        if (not item.definition.takes_durability_loss
                or item.durability_current >= 100.0):
            await self.output("That doesn't need repair.", 'warn')
            return

        name = get_display_name_with_tier(item)
        outcome, cost = await self.do_repair_attempt(item, char)
        if outcome == 'poor':
            await self.output(
                f"Repairing your {name} costs {self.format_amount(char, cost)} — "
                "you can't afford it.",
                'warn',
            )
        elif outcome == 'success':
            if get_item_value(item) == 0:
                await self.output(_pity_repair_line(repairer), 'success')
            else:
                await self.output(
                    f'{npc_display(repairer, capitalize=True)} restores your {name} '
                    f'to full condition. ({self.format_amount(char, cost)})', 'success',
                )
        else:
            await self.output(
                f"{npc_display(repairer, capitalize=True)} works on your {name}, "
                f"but the mending didn't take. ({self.format_amount(char, cost)})",
                'warn',
            )

    # ------------------------------------------------------------------
    # Combat commands
    # ------------------------------------------------------------------

    async def cmd_attack(self, args):
        character = await self.get_character_fresh()
        room = await self.get_current_room()
        npcs_in_room = await self.get_live_npcs_in_room(room)

        # v22 brief 2 (DD §1): a target is required — the targetless
        # auto-attack fossil is removed (aggro NPCs self-engage since
        # v21 #17); bare attack prompts via the central fn-10 gate.
        res = resolve('attack', args, npcs_in_room)
        if not res.ok:
            await self.send_output(res.message, self._refusal_category(res))
            return
        npc = res.items[0]

        if not npc.definition.attackable:
            await self.send_output(f"{npc_display(npc, capitalize=True)} cannot be attacked.", 'warn')
            return

        display = npc_display_name(npc, npcs_in_room)

        session = await self.get_active_combat_session(character)
        in_session = session is not None and await self.npc_in_session(session, npc)

        if in_session:
            if session.focus_npc_id == npc.pk:
                await self.send_output(f"You're already fighting {display}.", 'combat')
                return
            await self.set_session_focus(session, npc)
            await self.send_output(f"You change your attacks to focus on {display}.", 'combat')
            # v20 brief 4 (#2): move the fight pane's focus marker now
            # rather than waiting for the next tick's fight message.
            await self.send_fight(session)
            return

        await self.send_output(f"You move to attack {display}!", 'combat')
        await self.broadcast_to_room_exclude(
            f"{character.name} moves to attack {npc_display(npc)}!", 'combat'
        )
        session = await self.start_combat([npc], first_attacker='character', focus_npc=npc)
        # v20 brief 4 (#2): engagement — fight feed + combat-red state.
        await self.send_fight(session)
        await self.send_status_refresh()

    async def cmd_flee(self):
        character = await self.get_character_fresh()

        session = await self.get_active_combat_session(character)
        if not session:
            await self.send_output("You are not in combat.", 'warn')
            return

        if character.is_dying:
            await self.send_output("You are too close to death to flee!", 'warn')
            return

        on_cooldown = await self.check_flee_cooldown(character, session)
        if on_cooldown:
            await self.send_output("You are still recovering from your last flee attempt.", 'warn')
            return

        npcs = await self.get_session_npcs(session)
        if not npcs:
            await self.end_combat_session(session)
            # v20 brief 4 (#2): combat ended for the player — clear the
            # fight pane and the combat-red state.
            await self.send_fight(None)
            await self.send_status_refresh()
            return

        avg_per = sum(
            npc.definition.base_per * npc.definition.scaling_factor * npc.mk_tier
            for npc in npcs
        ) / len(npcs)

        success = (character.stat_dex + random.randint(1, 20)) > avg_per

        if success:
            result = await self.get_flee_destination(character)
            if result is None:
                await self.send_output("There is nowhere to run!", 'warn')
                await self.record_flee_attempt(character, session)
                return

            destination, flee_dir = result
            await self.send_output("You have successfully fled from your enemies.", 'combat')
            await self.broadcast_to_room_exclude(
                f"{character.name} fled the room leaving the enemies looking confused.", 'combat'
            )
            await self.end_combat_session(session)
            # v20 brief 4 (#2): flee ends combat for the player — clear the
            # fight pane; a fresh engagement below re-fills it if the flee
            # destination has aggro.
            await self.send_fight(None)
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
            await self.move_character(destination)
            first_visit = await self.record_room_visit(self.character, destination)
            self.last_direction = flee_dir
            self.room_group = f"room_{destination.id}"
            await self.channel_layer.group_add(self.room_group, self.channel_name)

            # v21 brief 1 (#81): flee-into-aggro renders the destination
            # like any other entry — full render first (who's-here
            # introduces the attackers), then definite-article engagement
            # lines, then combat state last.
            destination_full = await self.get_current_room()
            await self.send_room_description(destination_full, entering=True,
                                             first_visit=first_visit)
            aggro_npcs = await self.get_aggro_npcs_in_room(destination)
            if aggro_npcs:
                for npc in aggro_npcs:
                    # v21 brief 3 (#64): ordinal-aware while duplicates
                    # share the visible name.
                    await self.send_output(
                        f"{npc_display_name(npc, aggro_npcs, capitalize=True)} "
                        "snarls and moves to attack!",
                        'combat',
                    )
                new_session = await self.start_combat(aggro_npcs, first_attacker='npc')
                await self.send_fight(new_session)
                await self.send_status_refresh()
            await self.send_map()
        else:
            # v22 brief 2 (DD §3): a failed flee is the world declining.
            await self.send_output("You tried to flee but your enemies are too strong.", 'warn')
            await self.broadcast_to_room_exclude(
                f"{character.name} tried to flee combat but could not slip away.", 'combat'
            )
            await self.record_flee_attempt(character, session)

    # ------------------------------------------------------------------
    # Stat commands
    # ------------------------------------------------------------------

    async def cmd_stats(self):
        character = await self.get_character_fresh()
        await self._send_stats(character)

    async def _send_stats(self, character):
        # v21 brief 1 (#91): key/value form — 'Character Stats:' header
        # in key-color, everything under it in value-color (stat labels
        # included; a subkey-color was explicitly deferred). The Player
        # line is Origin + Archetype, e.g. 'Level 10 Feral Blade'.
        from .combat_utils import xp_for_next_level
        lines = [
            {'k': 'Character Stats:'},
            {'v': f'  Player: {character.name} - Level {character.level} '
                  f'{character.origin.name} {character.archetype.name}'},
            {},
            {'v': f'  Strength     (STR): {character.stat_str}'},
            {'v': f'  Dexterity    (DEX): {character.stat_dex}'},
            {'v': f'  Endurance    (END): {character.stat_end}'},
            {'v': f'  Intelligence (INT): {character.stat_int}'},
            {'v': f'  Wisdom       (WIS): {character.stat_wis}'},
            {'v': f'  Perception   (PER): {character.stat_per}'},
            {},
            {'v': f'  Vitality:   {character.vitality_current} / {character.vitality_max}'},
            {'v': f'  Longevity:  {character.longevity_current} / {character.longevity_max}'},
            {'v': f'  Acuity:     {character.acuity_current:.1f} '
                  f'(baseline {character.acuity_baseline:.1f})'},
            {},
            {'v': f'  XP: {character.xp} / {xp_for_next_level(character.level)} (next level)'},
            # v22 brief 2 (DD §9): blank line before Unspent stat points.
            {},
            {'v': f'  Unspent stat points: {character.unspent_stat_points}'},
        ]
        if character.unspent_stat_points > 0:
            lines.append(
                {'v': "  Type 'spend [<quantity>] <stat>' to allocate. (e.g. 'spend 2 str')"},
            )
        await self.send_report_lines(lines)

    # v22 brief 2 (DD §1): 'spend [<quantity>] <stat>' — the argument
    # order flips (footnotes 7 14); 'all' = every unspent point; a bare
    # numeric prompts per footnote 15; the old '<stat> <amount>' order
    # dies. Bare spend prompts via the central fn-10 gate.
    SPEND_USAGE = ('Usage: spend [<quantity> | all] <stat>  '
                   '(stats: str dex end int wis per)')

    async def cmd_spend(self, args):
        VALID_STATS = {
            'str': 'Strength',
            'dex': 'Dexterity',
            'end': 'Endurance',
            'int': 'Intelligence',
            'wis': 'Wisdom',
            'per': 'Perception',
        }

        character = await self.get_character_fresh()

        parts = args.lower().split()

        # Optional leading quantity: a number or 'all'.
        quantity = 1
        spend_all = False
        if parts and (parts[0] == 'all' or parts[0].isdigit()):
            if parts[0] == 'all':
                spend_all = True
            else:
                quantity = int(parts[0])
            parts = parts[1:]

        if not parts:
            # Footnote 15: a bare numeric names its missing target.
            if not spend_all and quantity != 1:
                await self.send_output(
                    f'spend {quantity} points on which stat?', 'error',
                )
            else:
                await self.send_output(self.SPEND_USAGE, 'error')
            return

        if len(parts) != 1 or parts[0] not in VALID_STATS:
            await self.send_output(self.SPEND_USAGE, 'error')
            return
        stat_name = parts[0]

        if not spend_all and quantity <= 0:
            await self.send_output(self.SPEND_USAGE, 'error')
            return

        if character.unspent_stat_points <= 0:
            await self.send_output("You have no unspent stat points.", 'warn')
            return

        amount = character.unspent_stat_points if spend_all else quantity
        if amount > character.unspent_stat_points:
            pts = character.unspent_stat_points
            await self.send_output(
                f"You only have {pts} unspent stat point{'s' if pts != 1 else ''}.", 'warn'
            )
            return

        @database_sync_to_async
        def apply_spend(char, stat, pts):
            from .combat_utils import recalculate_bars
            attr = f'stat_{stat}'
            current = getattr(char, attr)
            setattr(char, attr, current + pts)
            char.unspent_stat_points -= pts
            if stat in ('end', 'str', 'wis'):
                recalculate_bars(char)
                char.save(update_fields=[
                    attr, 'unspent_stat_points',
                    'vitality_max', 'vitality_current',
                    'longevity_max', 'longevity_current',
                ])
            else:
                char.save(update_fields=[attr, 'unspent_stat_points'])
            return getattr(char, attr)

        new_value = await apply_spend(character, stat_name, amount)
        remaining = character.unspent_stat_points

        # v22 brief 2 (DD §6): the transactional sentence + the new value.
        await self.send_output(
            f'You spend {amount} point{"s" if amount != 1 else ""} '
            f'on {VALID_STATS[stat_name]}.', 'success',
        )
        await self.send_output(
            f"{VALID_STATS[stat_name]} is now {new_value}. "
            f"{'No' if remaining == 0 else remaining} stat point{'s' if remaining != 1 else ''} remaining.",
            'success'
        )

        room = character.current_room
        await self.send_json(await self._status_payload(character, room))

    # v22 brief 2 (DD §10): the settings standard. Six accepted words,
    # case-insensitive; bare = the current-setting sentence (the set
    # message minus 'now'); set = the 'now' sentence — stateless,
    # idempotent, plain prose. Invalid input is a CLI error showing the
    # canonical pair (synonyms silently accepted). Fully firehosed:
    # stamped like every other event.
    SETTING_WORDS = {
        'on': True, 'yes': True, 'true': True,
        'off': False, 'no': False, 'false': False,
    }

    async def _cmd_setting(self, args, cmd_name, subject, verb_is, getter, setter):
        arg = args.strip().lower() if args else ''
        if not arg:
            character = await self.get_character_fresh()
            state = 'on' if getter(character) else 'off'
            await self.send_output(f'{subject} {verb_is} {state}.', category='system')
            return None
        if arg not in self.SETTING_WORDS:
            await self.send_output(f'Usage: {cmd_name} [on|off]', category='error')
            return None
        value = self.SETTING_WORDS[arg]
        await setter(value)
        state = 'on' if value else 'off'
        await self.send_output(f'{subject} {verb_is} now {state}.', category='system')
        return value

    async def cmd_brief(self, args):
        value = await self._cmd_setting(
            args, 'brief', 'brief room display', 'is',
            lambda c: c.brief_mode, self._set_brief_mode,
        )
        if value is not None:
            self.character.brief_mode = value

    async def cmd_echo(self, args):
        # The client applies the change from the status payload; the
        # preference is pane-only and never touches the firehose.
        value = await self._cmd_setting(
            args, 'echo', 'command echo', 'is',
            lambda c: c.echo_mode, self._set_echo_mode,
        )
        if value is not None:
            self.character.echo_mode = value
            char = await self.get_character_fresh()
            await self.send_json(await self._status_payload(char, char.current_room))

    async def cmd_timestamps(self, args):
        """v20 brief 3 (#45): the preference persists on the Character and
        reaches the client through the state-sync payload; envelope ts/seq
        fields are always present regardless. v22 brief 2 (DD §10): bare
        reports the current setting; six boolean words accepted."""
        arg = args.strip().lower() if args else ''
        if arg and arg in self.SETTING_WORDS:
            # Status first so the confirmation line already renders under
            # the new preference.
            value = self.SETTING_WORDS[arg]
            await self._set_show_timestamps(value)
            char = await self.get_character_fresh()
            await self.send_json(await self._status_payload(char, char.current_room))
            state = 'on' if value else 'off'
            await self.send_output(f'output timestamps are now {state}.', category='system')
            return
        await self._cmd_setting(
            args, 'timestamps', 'output timestamps', 'are',
            lambda c: c.show_timestamps, self._set_show_timestamps,
        )

    # ------------------------------------------------------------------
    # Channel layer event handlers
    # ------------------------------------------------------------------

    async def room_message(self, event):
        if event.get('exclude') == self.channel_name:
            return
        exclude_pk = event.get('exclude_pk')
        if exclude_pk is not None and exclude_pk == self.character_pk:
            return
        # v20 brief 5 (#28): multi-recipient suppression (corpse decay is
        # dropped, not deferred, for players in active combat).
        exclude_pks = event.get('exclude_pks')
        if exclude_pks and self.character_pk in exclude_pks:
            return
        # v20 brief 2 (#32): ts travels with the event from its creation
        # site (broadcaster); the choke point warns if it's missing rather
        # than this handler silently restamping.
        payload = {
            'type': 'output',
            'text': event['text'],
            'category': event.get('category', 'system'),
        }
        if 'ts' in event:
            payload['ts'] = event['ts']
        await self.send_json(payload)

    async def player_message(self, event):
        """Handle messages sent directly to this player (e.g. effect ticks from tick engine)."""
        event_type = event.get('event')
        ts = event.get('ts')
        # v21.1 (#116): single-session enforcement. Not a command — no
        # command gates apply; fires even while dying or in combat (the
        # in-combat refusal belongs to quit only). No room broadcast.
        if event_type == 'superseded':
            if event.get('token') == self.session_token:
                return
            await self.output(
                "The world's attention shifts — your story is being told "
                "through another window now. This one falls quiet.",
                'system',
            )
            await self.send_json({'event': 'superseded', 'ts': envelope_ts()})
            # Normal close; the disconnect path owns the guarded presence
            # delete, group discards, heartbeat cancellation, last_seen.
            await self.close()
            return
        if event_type == 'clear':
            payload = {'type': 'clear'}
            if ts is not None:
                payload['ts'] = ts
            await self.send_json(payload)
        if event.get('text'):
            payload = {
                'type': 'output',
                'text': event['text'],
                'category': event.get('category', 'system'),
            }
            if ts is not None:
                payload['ts'] = ts
            await self.send_json(payload)
        if event.get('status') is not None:
            await self.send_json(event['status'])
        # v20 brief 4 (#2): fight-info messages from the tick engine are
        # delivered as their own client message, like status payloads.
        if event.get('fight') is not None:
            await self.send_json(event['fight'])

        if event_type == 'dying':
            self._character_is_dying = True
        elif event_type == 'respawn':
            char = await self.get_character_fresh()
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
            self.room_group = f'room_{char.current_room_id}'
            await self.channel_layer.group_add(self.room_group, self.channel_name)
            self.last_direction = None
            room = await self.get_current_room()
            first_visit = await self.record_room_visit(char, room)
            await self.send_room_description(room, entering=True,
                                             first_visit=first_visit)
            await self.send_map()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def _status_payload(self, char, room):
        """The client-state sync payload. v20 brief 3 (#45): carries the
        show_timestamps preference so it applies immediately, on
        reconnect, and across devices. v20 brief 4: carries the location
        names+colors for the location bar (#1) and the combat-membership
        boolean for the stats section's combat-red state (#2) — runs in a
        DB thread for the combat-session lookup."""
        zone = room.zone if room else None
        area = room.area if room and room.area_id else None
        return {
            'type': 'status',
            # v20 brief 4 amendment 1 (#71): the stats-pane header renders
            # this verbatim — byte-for-byte, never client-derived.
            'character_name': char.name,
            'vitality': char.vitality_current,
            'vitality_max': char.vitality_max,
            'acuity': round(char.acuity_current, 2),
            'acuity_baseline': round(char.acuity_baseline, 2),
            'acuity_band_low': round(char.acuity_band_low, 2),
            'acuity_band_high': round(char.acuity_band_high, 2),
            'longevity': char.longevity_current,
            'longevity_max': char.longevity_max,
            'room_name': room.name if room else '',
            'zone_name': zone.name if zone else '',
            'zone_color': zone.theme_color if zone else '#CCCCCC',
            'area_name': area.name if area else None,
            'area_color': area.theme_color if area else None,
            'in_combat': CombatSession.objects.filter(
                is_active=True, characters=char,
            ).exists(),
            'show_timestamps': char.show_timestamps,
            'echo_mode': char.echo_mode,
            'ts': envelope_ts(),
        }

    async def send_output(self, text, category='system'):
        await self.send_json({'type': 'output', 'text': text, 'category': category,
                              'ts': envelope_ts()})

    async def broadcast_to_room_exclude(self, text, category='room'):
        await self.channel_layer.group_send(self.room_group, {
            'type': 'room_message',
            'text': text,
            'category': category,
            'exclude': self.channel_name,
            'ts': envelope_ts(),
        })

    def format_wallet(self, character):
        zone_slug = character.current_room.zone.slug if character.current_room_id else None
        return display_for_zone(character.copper, zone_slug)

    def format_amount(self, character, amount):
        zone_slug = character.current_room.zone.slug if character.current_room_id else None
        return display_for_zone(amount, zone_slug)

    async def maybe_kibitz(self, room, vendor):
        """v19 brief 10: after a completed buy/sell, the room's other living
        vendor (the gazebo's spouse) gets one flavor line, if present."""
        other = await self.get_other_vendor_in_room(room, vendor.pk)
        if other is None:
            return
        line = random.choice(KIBITZ_LINES).replace('{other}', npc_display(other, capitalize=True))
        await self.channel_layer.group_send(self.room_group, {
            'type': 'room_message',
            'text': line,
            'category': 'room',
            'ts': envelope_ts(),
        })

    async def output(self, text, category='system'):
        await self.send_json({'type': 'output', 'text': text, 'category': category,
                              'ts': envelope_ts()})

    @staticmethod
    def _refusal_category(res):
        """v22 brief 2 (DD §3): map a resolver refusal to its response
        layer. Shapes the grammar itself refused (bad syntax, quantifier
        misuse, missing-target numerics) are CLI errors; everything else
        — pool misses, bad indexes, ambiguity, the sell-all block — is
        the world declining (warn)."""
        if res.error in ('usage', 'no_multi', 'bare_numeric'):
            return 'error'
        return 'warn'

    @database_sync_to_async
    def effect_restores_vitality(self, effect_def):
        """v22 brief 2 (DD §7): heal detection for the stop-at-full rule —
        derived from the effect's own components, never a separate flag."""
        return effect_def.components.filter(
            component_type__in=('restore_vitality', 'hot_vitality'),
        ).exists()

    async def send_report_lines(self, lines):
        """v21 brief 1 (#90/#91/#92): the structured key/value report
        form. Each entry is one output line: 'k' renders in key-color,
        'v' in value-color (concatenated k-then-v when both present);
        an empty dict is a blank line. Value text still passes the
        client's flag-block colorizer, so item flag blocks keep their
        rarity/chrome colors inside value-colored lines."""
        await self.send_json({'type': 'output', 'category': 'report',
                              'lines': lines, 'ts': envelope_ts()})

    async def send_room_description(self, room, entering=False, force_long=False,
                                    first_visit=None):
        char = await self.get_character_fresh()
        exits = room.exits()
        exit_str = ', '.join(exits.keys()) if exits else 'none'
        others_db = await self.get_others_in_room(room)
        # Filter to only characters who are actively connected (have a Redis presence key)
        online_names = set()
        if others_db:
            keys = await self.redis.keys("shyland:online:*")
            if keys:
                values = await self.redis.mget(*keys)
                online_names = {parse_presence_name(v) for v in values if v}
        others = [name for name in others_db if name in online_names]
        npcs = await self.get_npcs_in_room(room)
        corpses = await self.get_corpses_in_room(room)

        show_long = await self._resolve_room_rendering(char, room, force_long, first_visit)
        if show_long:
            description_text = room.description
        else:
            description_text = room.brief_description

        # v20 brief 5 (#14) + amendment 1 (#77): the ruled section order —
        # prose first (no bracket header; place identity lives in the
        # location bar alone), Exits, Who's here?, What's here? — as ONE
        # structured message. Sections with no content are omitted
        # entirely. Occupant lines are introductions (#79): indefinite
        # article, sentence-capitalized. v21 brief 1 (#55): the lines are
        # bare noun phrases — no "is here"/"lies here" suffixes.
        living_npcs = [npc for npc in npcs if not npc.definition.is_fixture]
        fixture_npcs = [npc for npc in npcs if npc.definition.is_fixture]

        who_lines = [
            npc_display(npc, capitalize=True, introduction=True)
            for npc in living_npcs
        ]

        # What's here? is THE things/items section: fixtures, corpses, and
        # the ground items (one composed line per distinct item, identical
        # lines collapsed to xN). The brief-3 "On the ground:" section is
        # absorbed here.
        what_lines = [
            npc_display(npc, capitalize=True, introduction=True)
            for npc in fixture_npcs
        ]
        what_lines += [
            f'{corpse.display_name[0].upper()}{corpse.display_name[1:]}'
            for corpse in corpses
        ]
        room_items = await self.get_room_items(room)
        grouped = {}
        for item in room_items:
            key = compose_item_line(item)
            if key in grouped:
                grouped[key][1] += 1
            else:
                grouped[key] = [item, 1]
        what_lines += [compose_item_line(item, count) for item, count in grouped.values()]

        # v20 brief 2 amendment 1 (#56): the whole room block is a
        # rendering, not an event — 'room-render', unstamped on the client.
        # Brief 5 amendment 1 (#78): zone_color rides the render so the
        # client's closing separator always has the CURRENT zone's color
        # (the status payload that also carries it arrives after this
        # message, so it can't be the source on a cross-zone move).
        # v21 brief 1 (#86): area and room prose travel as separate
        # fields (area_color riding along) so the client can color each
        # to match its location-bar segment; brief mode carries no area
        # prose, matching the old concatenation's behavior.
        await self.send_json({
            'type': 'output',
            'category': 'room-render',
            'enter': entering,
            'zone_color': room.zone.theme_color if room.zone_id else '#CCCCCC',
            'area_text': room.area.area_description
                         if (show_long and room.area and room.area.area_description)
                         else None,
            'area_color': room.area.theme_color
                          if (room.area_id and room.area.theme_color)
                          else None,
            'room_text': description_text,
            'players': ', '.join(others) if others else None,
            'exits': exit_str,
            'who': who_lines,
            'what': what_lines,
            'ts': envelope_ts(),
        })

        await self.send_json(await self._status_payload(char, room))

        if entering and npcs:
            await self.schedule_npc_greetings(room, npcs)

    # ------------------------------------------------------------------
    # Tab completion (v20 brief 3, #19)
    # ------------------------------------------------------------------

    async def handle_complete(self, line):
        """Answer a client completion request. Candidates come from the
        same per-verb providers the resolver uses — one source of truth;
        nothing from the client is trusted beyond the text to complete.
        Verbs without noun arguments (and the verb position itself, which
        the client completes locally) get an empty option list.

        v22 brief 2 (DD §8, #67/#96): completion covers exactly each
        command's pool, per position, literals included — the six boolean
        words for settings, stat names and 'all' for spend, destination
        names for travel, corpse NPC names and 'all' for loot."""
        options = []
        try:
            text = line or ''
            parts = text.split(None, 1)
            at_argument = bool(parts) and (len(parts) > 1 or text != text.rstrip())
            if at_argument:
                head = parts[0].lower()
                arg_text = parts[1] if len(parts) > 1 else ''
                if arg_text and text.endswith(' ') and not arg_text.endswith(' '):
                    arg_text += ' '
                verb = self.GRAMMAR_VERBS.get(head)
                if head in ('brief', 'echo', 'timestamps'):
                    options = self._complete_words(
                        arg_text, sorted(self.SETTING_WORDS), first_only=True)
                elif head == 'spend':
                    options = self._complete_spend(arg_text)
                elif head == 'travel':
                    options = await self._complete_travel(arg_text)
                elif head == 'loot':
                    options = await self._complete_loot(arg_text)
                elif verb is not None:
                    candidates = await self._completion_candidates(verb)
                    options = grammar_complete(verb, arg_text, candidates)
                    if verb == 'examine':
                        # Players are in examine's union too (DD §8).
                        room = await self.get_current_room()
                        players = await self.get_characters_in_room(room)
                        partial = ('' if arg_text.endswith(' ') or not arg_text
                                   else arg_text.lower().split()[-1])
                        extra = {
                            t for p in players for t in p.name.lower().split()
                            if t.startswith(partial)
                        }
                        options = sorted(set(options) | extra)[:50]
        except Exception:
            cmd_logger.exception('shyland completion failed: %r', line)
            options = []
        await self.send_json({'type': 'complete', 'text': line,
                              'options': options, 'ts': envelope_ts()})

    @staticmethod
    def _complete_words(arg_text, words, first_only=False):
        """Prefix-complete the trailing token against a literal word list."""
        if arg_text.endswith(' ') or not arg_text:
            prev, partial = arg_text.lower().split(), ''
        else:
            tokens = arg_text.lower().split()
            prev, partial = tokens[:-1], tokens[-1]
        if first_only and prev:
            return []
        return sorted(w for w in words if w.startswith(partial))

    def _complete_spend(self, arg_text):
        """spend [<quantity>|all] <stat> — position one offers 'all' and
        the stats; after a quantity, the stats."""
        stats = ['str', 'dex', 'end', 'int', 'wis', 'per']
        if arg_text.endswith(' ') or not arg_text:
            prev, partial = arg_text.lower().split(), ''
        else:
            tokens = arg_text.lower().split()
            prev, partial = tokens[:-1], tokens[-1]
        if not prev:
            words = stats + ['all']
        elif len(prev) == 1 and (prev[0] == 'all' or prev[0].isdigit()):
            words = stats
        else:
            return []
        return sorted(w for w in words if w.startswith(partial))

    async def _complete_travel(self, arg_text):
        room = await self.get_current_room()
        node = await self.get_travel_node(room)
        if node is None or node.node_type != 'obelisk':
            return []
        destinations = await self.get_revealed_destinations(node)
        names = [d.travel_name.lower() for d in destinations]
        partial = arg_text.lower().lstrip()
        return sorted({n for n in names if n.startswith(partial)})[:50]

    async def _complete_loot(self, arg_text):
        room = await self.get_current_room()
        corpses = await self.get_corpses_in_room(room)
        words = {'all'}
        for corpse in corpses:
            words.update(corpse.display_name.lower().split())
        if arg_text.endswith(' ') or not arg_text:
            partial = ''
        else:
            partial = arg_text.lower().split()[-1]
        return sorted(w for w in words if w.startswith(partial))[:50]

    async def _completion_candidates(self, verb):
        """Part A4 candidate scoping, verb by verb — shared between the
        resolver call sites and completion."""
        char = self.character
        if verb == 'use':
            return await self.get_carried_consumables(char)
        if verb in ('sell', 'repair'):
            return await self.get_carried_items(char)
        if verb == 'drop':
            # v22 brief 2 (DD §8 fn 16): drop's pool excludes bound items.
            items = await self.get_carried_items(char)
            return [i for i in items if not i.is_soulbound]
        if verb == 'equip':
            items = await self.get_carried_unequipped_items(char)
            return [i for i in items if i.definition.valid_slots]
        if verb == 'unequip':
            return await self.get_equipped_items(char)
        if verb == 'pickup':
            room = await self.get_current_room()
            return await self.get_room_items(room)
        if verb == 'examine':
            # v22 brief 2 (DD §8, #96): the union — inventory + equipped +
            # floor + NPCs here + vendor stock (players merge in the
            # caller; corpses complete through their NPC names via the
            # NPC segment).
            room = await self.get_current_room()
            carried = await self.get_carried_items(char)
            pool = carried + await self.get_room_items(room)
            pool += await self.get_npcs_in_room(room)
            vendor = await self.get_vendor_in_room(room)
            if vendor is not None:
                entries = await self.get_vendor_entries(vendor)
                pool += [e for e in entries if not self._entry_exhausted(e)]
            return pool
        if verb == 'buy':
            room = await self.get_current_room()
            vendor = await self.get_vendor_in_room(room)
            if vendor is None:
                return []
            entries = await self.get_vendor_entries(vendor)
            return [e for e in entries if not self._entry_exhausted(e)]
        if verb == 'attack':
            room = await self.get_current_room()
            return await self.get_live_npcs_in_room(room)
        return []

    # ------------------------------------------------------------------
    # Map (v20 brief 1, #35)
    # ------------------------------------------------------------------

    async def send_map(self):
        """Send the full map state for the character's current MapFrag.
        Called on connect and on every room change (move, flee, travel,
        respawn) — the client discards and fully re-renders each time."""
        await self.send_json(await self.build_map_payload())

    @database_sync_to_async
    def build_map_payload(self):
        """v22 brief 1 (#82, #115): Maps V2 payload. Derive the character's
        MapFrag fresh — BFS from the current room over unflagged, intra-zone
        cardinal exits (unchanged definition) — then split it into the
        discovered set (fragment ∩ RoomVisit, plus the current room) and the
        frontier set (unvisited fragment rooms cardinally adjacent to a
        discovered room). Frontier entries are masked by construction: they
        carry exactly x, y, discovered — the server never relies on the
        client to hide anything. Gate destinations never enter the rooms
        array; they are looked up only for their visit bit.

        Query discipline (post-#107, binding): a bounded, constant number of
        queries — current room, zone rooms, one RoomVisit query over the
        union of zone room ids and all out-of-zone destination ids, aggro
        room ids, travel-node room ids. Five total; no queries inside the
        BFS loop, no per-room queries. Locked by assertNumQueries in
        tests/test_map_payload.py."""
        current = Room.objects.select_related('zone').get(
            pk=self.character.current_room_id,
        )
        zone_rooms = {
            room.pk: room
            for room in Room.objects.filter(zone_id=current.zone_id)
        }

        def cardinal_exit(room, direction):
            """(destination pk or None, is_gate) for one cardinal exit.
            Cross-zone exits are gates automatically; a boundary flag on
            either side of an intra-zone pair makes it a gate."""
            dst_id = getattr(room, f'exit_{direction}_id')
            if dst_id is None:
                return None, False
            dst = zone_rooms.get(dst_id)
            if dst is None:
                return dst_id, True
            if (getattr(room, f'exit_{direction}_boundary')
                    or getattr(dst, f'exit_{REVERSE_DIRECTIONS[direction]}_boundary')):
                return dst_id, True
            return dst_id, False

        fragment = {current.pk}
        queue = deque([current.pk])
        while queue:
            room = zone_rooms[queue.popleft()]
            for direction in MAP_CARDINALS:
                dst_id, is_gate = cardinal_exit(room, direction)
                if dst_id is None or is_gate or dst_id in fragment:
                    continue
                fragment.add(dst_id)
                queue.append(dst_id)

        # One visit query covers fragment membership, U/D destinations, and
        # gate destinations alike: the union of the zone's room ids and every
        # exit destination that lives outside the zone (cross-zone gates,
        # cross-zone up/down).
        outside_ids = set()
        for room in zone_rooms.values():
            for direction in ('north', 'south', 'east', 'west', 'up', 'down'):
                dst_id = getattr(room, f'exit_{direction}_id')
                if dst_id is not None and dst_id not in zone_rooms:
                    outside_ids.add(dst_id)
        visited = set(
            RoomVisit.objects.filter(
                character_id=self.character_pk,
                room_id__in=zone_rooms.keys() | outside_ids,
            ).values_list('room_id', flat=True)
        )
        # The room underfoot is always known. Since #50 every arrival path
        # records its RoomVisit, so this is defense-in-depth for moves that
        # bypass the consumer (e.g. an admin editing current_room).
        visited.add(current.pk)
        discovered = (fragment & visited) | {current.pk}

        # Frontier: unvisited fragment rooms one unflagged intra-zone
        # cardinal step from a discovered room. Nothing deeper than the
        # frontier ever enters the payload.
        frontier = set()
        for pk in discovered:
            room = zone_rooms[pk]
            for direction in MAP_CARDINALS:
                dst_id, is_gate = cardinal_exit(room, direction)
                if dst_id is not None and not is_gate and dst_id not in visited:
                    frontier.add(dst_id)

        # Aggro is configuration, not instance state: a dead or unspawned
        # instance still flags its room.
        agro_ids = set(
            RoomSpawn.objects.filter(
                room__zone_id=current.zone_id,
                npc_definition__is_aggressive=True,
            ).values_list('room_id', flat=True)
        )
        travel_ids = set(
            TravelNode.objects.filter(
                room__zone_id=current.zone_id,
            ).values_list('room_id', flat=True)
        )

        rooms_payload = []
        for pk in sorted(discovered | frontier):
            room = zone_rooms[pk]
            if pk not in discovered:
                rooms_payload.append({
                    'x': room.coord_x, 'y': room.coord_y, 'discovered': False,
                })
                continue
            entry = {
                'x': room.coord_x, 'y': room.coord_y, 'discovered': True,
            }
            if pk == current.pk:
                entry['here'] = True
            if pk in travel_ids:
                entry['travel_node'] = True
            entry['agro'] = pk in agro_ids
            exits = {}
            for direction in MAP_CARDINALS:
                dst_id, is_gate = cardinal_exit(room, direction)
                if dst_id is None:
                    continue
                status = 'known' if dst_id in visited else 'unknown'
                exits[direction] = f'gate-{status}' if is_gate else status
            entry['exits'] = exits
            for direction in ('up', 'down'):
                dst_id = getattr(room, f'exit_{direction}_id')
                if dst_id is not None:
                    entry[direction] = 'known' if dst_id in visited else 'unknown'
            rooms_payload.append(entry)

        return {
            'type': 'map',
            'zone': current.zone.slug,
            'current': {'x': current.coord_x, 'y': current.coord_y},
            'rooms': rooms_payload,
            'ts': envelope_ts(),
        }

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def get_character(self, user):
        try:
            char = (
                Character.objects
                .select_related(
                    'current_room__zone', 'recall_room',
                    'archetype__unarmed_message_pool',
                )
                .get(user=user)
            )
            return char
        except Character.DoesNotExist:
            return None

    @database_sync_to_async
    def get_current_room(self):
        return (
            Room.objects
            .select_related('zone', 'area',
                            'exit_north', 'exit_south',
                            'exit_east', 'exit_west',
                            'exit_up', 'exit_down')
            .get(pk=self.character.current_room_id)
        )

    @database_sync_to_async
    def move_character(self, destination):
        Character.objects.filter(pk=self.character.pk).update(current_room=destination)
        self.character.current_room = destination
        self.character.current_room_id = destination.pk

    @database_sync_to_async
    def record_room_visit(self, character, room):
        """Record the fog-of-war visit for an arrival, returning whether it
        was the first. v20 brief 1 amendment 2 (#50): visits land at arrival
        time in every arrival path, independent of room-description
        rendering — an aggro ambush that skips the description must not skip
        the visit."""
        _, created = RoomVisit.objects.get_or_create(character=character, room=room)
        return created

    @database_sync_to_async
    def touch_last_seen(self, character):
        Character.objects.filter(pk=character.pk).update(last_seen=timezone.now())

    @database_sync_to_async
    def _set_brief_mode(self, value):
        Character.objects.filter(pk=self.character_pk).update(brief_mode=value)

    @database_sync_to_async
    def _set_show_timestamps(self, value):
        Character.objects.filter(pk=self.character_pk).update(show_timestamps=value)

    @database_sync_to_async
    def _set_echo_mode(self, value):
        Character.objects.filter(pk=self.character_pk).update(echo_mode=value)
        self.character.show_timestamps = value

    @database_sync_to_async
    def get_travel_node(self, room):
        return TravelNode.objects.filter(room=room).first()

    @database_sync_to_async
    def get_revealed_destinations(self, current_node):
        return list(
            TravelNode.objects
            .filter(room__visits__character_id=self.character_pk)
            .exclude(pk=current_node.pk)
            .select_related('room')
            .order_by('travel_name')
        )

    @database_sync_to_async
    def get_random_travel_message(self, category):
        texts = list(
            TravelMessage.objects.filter(category=category)
            .values_list('text', flat=True)
        )
        return random.choice(texts) if texts else None

    @database_sync_to_async
    def _resolve_room_rendering(self, character, room, force_long, first_visit=None):
        """Return True if the long description (+ area description) should
        render, False for brief-only. Per v19 brief 8 Part 2b: first entry
        and `look` always show the long form; revisits obey brief_mode.
        Read-only with respect to visits (#50): arrival paths record the
        visit and pass first_visit in; non-arrival renders (look, revive)
        look it up without creating it."""
        if first_visit is None:
            first_visit = not RoomVisit.objects.filter(
                character=character, room=room,
            ).exists()
        if force_long or first_visit:
            return True
        return not character.brief_mode

    @database_sync_to_async
    def get_inventory(self):
        return list(
            ItemInstance.objects.filter(owner=self.character)
            .select_related('definition')
            .order_by('is_equipped', 'definition__item_type', 'mk_tier', 'rarity', 'definition__name')
        )

    @database_sync_to_async
    def get_others_in_room(self, room):
        chars = list(
            Character.objects
            .filter(current_room=room)
            .exclude(pk=self.character.pk)
        )
        return [c.name for c in chars]

    @database_sync_to_async
    def get_characters_in_room(self, room):
        """v22 brief 2 (DD §8): player rows for examine's union pool."""
        return list(
            Character.objects
            .filter(current_room=room)
            .exclude(pk=self.character.pk)
            .select_related('origin', 'archetype')
        )

    @database_sync_to_async
    def get_room_items(self, room):
        return list(
            ItemInstance.objects.filter(current_room=room, owner__isnull=True, corpse__isnull=True)
            .select_related('definition')
        )

    @database_sync_to_async
    def get_carried_items(self, character):
        return list(
            ItemInstance.objects.filter(owner=character)
            .select_related('definition')
        )

    @database_sync_to_async
    def get_carried_unequipped_items(self, character):
        return list(
            ItemInstance.objects.filter(owner=character, is_equipped=False)
            .select_related('definition')
        )

    @database_sync_to_async
    def get_equipped_items(self, character):
        return list(
            ItemInstance.objects.filter(owner=character, is_equipped=True)
            .select_related('definition')
        )

    @database_sync_to_async
    def get_carried_consumables(self, character):
        return list(
            ItemInstance.objects.filter(
                owner=character,
                is_equipped=False,
                definition__item_type='consumable',
            )
            .select_related('definition', 'definition__effect')
        )

    @database_sync_to_async
    def get_carry_capacity(self, character):
        from django.db.models import Sum
        items = ItemInstance.objects.filter(owner=character)
        current_count = items.count()
        bag_bonus = items.filter(
            is_equipped=True,
            definition__item_type='bag',
        ).aggregate(total=Sum('definition__carry_bonus'))['total'] or 0
        max_capacity = character.stat_str * 10 + bag_bonus
        return (current_count, max_capacity)

    @database_sync_to_async
    def count_unequipped_items(self, character):
        return ItemInstance.objects.filter(owner=character, is_equipped=False).count()

    @database_sync_to_async
    def transfer_to_character(self, item, character):
        item.owner = character
        item.current_room = None
        item.save()

    @database_sync_to_async
    def transfer_to_room(self, item, room):
        item.current_room = room
        item.owner = None
        if not item.is_unidentifiable:
            item.is_identified = False
        item.save()

    @database_sync_to_async
    def equip_item(self, item, slot, character):
        item.is_equipped = True
        item.equipped_slot = slot
        item.is_soulbound = True
        item.soulbound_to = character
        item.save()

    @database_sync_to_async
    def unequip_item(self, item):
        item.is_equipped = False
        item.equipped_slot = ''
        item.save()

    @database_sync_to_async
    def apply_character_stat_change(self, character):
        character.save()

    @database_sync_to_async
    def do_apply_effect(self, effect_def, character, mk_tier):
        from .effect_utils import apply_effect_definition
        return apply_effect_definition(effect_def, character, mk_tier, removed_by_label='consumable')

    @database_sync_to_async
    def consume_item(self, item):
        item.delete()

    @database_sync_to_async
    def get_npcs_in_room(self, room):
        from .models import NpcInstance
        return list(
            NpcInstance.objects.filter(current_room=room, is_alive=True)
            .select_related('definition')
        )

    @database_sync_to_async
    def get_corpses_in_room(self, room):
        from .models import Corpse
        return list(
            Corpse.objects.filter(current_room=room)
            .select_related('killed_by', 'npc_definition')
            .prefetch_related('contents__definition')
            .order_by('-created_at')
        )

    @database_sync_to_async
    def get_corpse_contents(self, corpse):
        return list(corpse.contents.select_related('definition').all())

    @database_sync_to_async
    def do_loot_item(self, item, character):
        name = get_display_name(item)
        item.corpse = None
        item.owner = character
        item.save()
        return name

    @database_sync_to_async
    def do_loot_copper(self, corpse, character):
        from django.db.models import F
        amount = corpse.copper_drop
        if amount > 0:
            Character.objects.filter(pk=character.pk).update(copper=F('copper') + amount)
            corpse.copper_drop = 0
            corpse.save(update_fields=['copper_drop'])
        return amount

    @database_sync_to_async
    def check_corpse_empty_and_delete(self, corpse):
        # Query the table directly: `corpse.contents.exists()` on a corpse
        # loaded with prefetch_related answers from the stale prefetch
        # cache, so an emptied corpse would never delete on the loot that
        # emptied it (found by v20 brief 3 verification).
        if not ItemInstance.objects.filter(corpse=corpse).exists():
            corpse.delete()
            return True
        return False

    @database_sync_to_async
    def get_carry_counts(self, character):
        current = ItemInstance.objects.filter(owner=character, is_equipped=False).count()
        equipped_bags = list(
            ItemInstance.objects.filter(
                owner=character, is_equipped=True, definition__item_type='bag'
            ).select_related('definition')
        )
        bag_bonus = sum(b.definition.carry_bonus for b in equipped_bags)
        max_carry = character.stat_str * 10 + bag_bonus
        return current, max_carry

    # ------------------------------------------------------------------
    # Commerce DB helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def get_vendor_in_room(self, room):
        """First living NPC in the room whose definition has an active VendorEntry."""
        return (
            NpcInstance.objects.filter(
                current_room=room,
                is_alive=True,
                definition__vendor_entries__is_active=True,
            )
            .select_related('definition')
            .order_by('pk')
            .distinct()
            .first()
        )

    @database_sync_to_async
    def get_other_vendor_in_room(self, room, exclude_instance_pk):
        """Another living vendor in the room besides the one serving the
        transaction — v19 brief 10 kibitz (the gazebo's non-serving spouse)."""
        return (
            NpcInstance.objects.filter(
                current_room=room,
                is_alive=True,
                definition__vendor_entries__is_active=True,
            )
            .exclude(pk=exclude_instance_pk)
            .select_related('definition')
            .order_by('pk')
            .distinct()
            .first()
        )

    @database_sync_to_async
    def get_repairer_in_room(self, room):
        return (
            NpcInstance.objects.filter(
                current_room=room,
                is_alive=True,
                definition__is_repairer=True,
            )
            .select_related('definition')
            .order_by('pk')
            .first()
        )

    @database_sync_to_async
    def get_vendor_entries(self, vendor):
        """Active entries for a vendor, exhausted ones included (buy reports Sold out)."""
        return list(
            VendorEntry.objects.filter(
                npc_definition_id=vendor.definition_id, is_active=True,
            )
            .select_related('item_definition')
            .order_by('item_definition__name', 'mk_tier')
        )

    @database_sync_to_async
    def do_buy(self, entry, character, qty=1):
        """Atomically charge, count the sale, and create the purchased
        item(s). v20 brief 3 (#22): the whole quantity succeeds or fails
        as one transaction — never a partial purchase. Returns the list
        of created items, or 'poor' / 'sold_out'."""
        from django.db import transaction
        with transaction.atomic():
            fresh = VendorEntry.objects.select_related('item_definition').select_for_update().get(pk=entry.pk)
            if (fresh.stock_limit is not None
                    and fresh.stock_limit - fresh.sold_count < qty):
                return 'sold_out'
            char = Character.objects.select_for_update().get(pk=character.pk)
            try:
                char.copper = currency.subtract(char.copper, fresh.price * qty)
            except ValueError:
                return 'poor'
            char.save(update_fields=['copper'])
            fresh.sold_count += qty
            fresh.save(update_fields=['sold_count'])
            items = []
            for _ in range(qty):
                item = generate_item_instance(
                    definition=fresh.item_definition,
                    mk_tier=fresh.mk_tier,
                    rarity='common',
                    owner=char,
                )
                item.save()
                items.append(item)
        self.character.copper = char.copper
        return items

    @database_sync_to_async
    def do_sell(self, item, character):
        """Credit the sale price and delete the sold instance — compensated disposal."""
        from django.db import transaction
        price = get_sale_price(item)
        with transaction.atomic():
            char = Character.objects.select_for_update().get(pk=character.pk)
            char.copper = currency.add(char.copper, price)
            char.save(update_fields=['copper'])
            item.delete()
        self.character.copper = char.copper
        return price

    @database_sync_to_async
    def get_damaged_items(self, character):
        """Eligible repair targets, most-damaged first (stable tie-break on pk)."""
        return list(
            ItemInstance.objects.filter(
                owner=character,
                definition__takes_durability_loss=True,
                durability_current__lt=100.0,
            )
            .select_related('definition')
            .order_by('durability_current', 'pk')
        )

    @database_sync_to_async
    def do_repair_attempt(self, item, character):
        """One paid repair attempt. Returns (outcome, cost); outcome is
        'poor' (refused, nothing charged), 'success', or 'fail' (copper spent,
        item unchanged)."""
        from django.db import transaction
        # v19 brief 10: get_repair_cost floors to a minimum of 1 copper, but
        # a genuinely worthless item (base_value 0 — the newbie kit) repairs
        # for real zero, not a token copper, so the pity framing is honest.
        cost = 0 if get_item_value(item) == 0 else get_repair_cost(item)
        with transaction.atomic():
            char = Character.objects.select_for_update().get(pk=character.pk)
            try:
                char.copper = currency.subtract(char.copper, cost)
            except ValueError:
                return ('poor', cost)
            char.save(update_fields=['copper'])
            if random.random() < get_repair_success_chance(item):
                item.durability_current = 100.0
                item.is_broken = False
                item.save(update_fields=['durability_current', 'is_broken'])
                outcome = 'success'
            else:
                outcome = 'fail'
        self.character.copper = char.copper
        return (outcome, cost)

    # ------------------------------------------------------------------
    # Combat DB helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def get_character_fresh(self):
        # v21 brief 1 (#91): origin joins the select_related set — the
        # stats Player line renders origin.name + archetype.name.
        char = Character.objects.select_related(
            'current_room__zone', 'current_room__area', 'recall_room',
            'origin', 'archetype__unarmed_message_pool',
        ).get(pk=self.character_pk)
        self.character = char
        self._character_is_dying = char.is_dying
        return char

    @database_sync_to_async
    def revive_character(self, character):
        character.is_dying = False
        character.dying_since = None
        character.save(update_fields=['is_dying', 'dying_since'])

    @database_sync_to_async
    def get_aggro_npcs_in_room(self, room):
        return list(NpcInstance.objects.filter(
            current_room=room,
            is_alive=True,
            definition__is_aggressive=True,
            definition__attackable=True,
        ).order_by('spawned_at', 'pk')
         .select_related('definition').prefetch_related('definition__effects__effect_definition'))

    @database_sync_to_async
    def get_live_npcs_in_room(self, room):
        # v21 brief 3 (#64): (spawned_at, pk) is THE canonical NPC order —
        # the Who's-here listing, the resolver's default pick, the N.noun
        # index, and message ordinals all derive from it. Every room/session
        # NPC queryset must carry this order_by.
        return list(NpcInstance.objects.filter(
            current_room=room,
            is_alive=True,
        ).order_by('spawned_at', 'pk')
         .select_related('definition').prefetch_related('definition__effects__effect_definition'))

    @database_sync_to_async
    def schedule_npc_dialogue_responses(self, text):
        """v19 brief 9: NPCs listen to room say. Entry-first draw per eligible
        NPC, then a shuffled, tick-staggered delivery queue."""
        words = _tokenize_said_words(text)
        if not words:
            return

        room = Room.objects.get(pk=self.character.current_room_id)
        npcs = list(
            NpcInstance.objects.filter(current_room=room, is_alive=True)
            .select_related('definition')
            .prefetch_related('definition__dialogue_entries')
        )

        eligible = []
        for npc in npcs:
            matched_entries = [
                e for e in npc.definition.dialogue_entries.all()
                if e.entry_type == DialogueEntry.ENTRY_KEYWORD and words.intersection(e.keywords or [])
            ]
            if matched_entries:
                eligible.append((npc, random.choice(matched_entries)))

        if not eligible:
            return

        random.shuffle(eligible)
        now = timezone.now()
        utterance_id = uuid.uuid4()
        last_index = len(eligible) - 1
        for position, (npc, entry) in enumerate(eligible):
            PendingDialogueResponse.objects.create(
                utterance_id=utterance_id,
                npc_instance=npc,
                entry=entry,
                character=self.character,
                room=room,
                position=position,
                is_final=(position == last_index),
                fire_at=now + timedelta(
                    seconds=DIALOGUE_FIRST_DELAY_TICKS + position * DIALOGUE_STAGGER_TICKS,
                ),
            )

    @database_sync_to_async
    def schedule_npc_greetings(self, room, npcs):
        """v19 brief 9: first-contact greetings, queued through the same
        pending-response machinery so simultaneous greeters stagger too."""
        character = self.character
        greeters = []
        for npc in npcs:
            greeting_entries = [
                e for e in npc.definition.dialogue_entries.all()
                if e.entry_type == DialogueEntry.ENTRY_GREETING
            ]
            if not greeting_entries:
                continue
            if DialogueGreetingRecord.objects.filter(
                character=character, npc_definition_id=npc.definition_id,
            ).exists():
                continue
            greeters.append((npc, random.choice(greeting_entries)))

        if not greeters:
            return

        random.shuffle(greeters)
        now = timezone.now()
        utterance_id = uuid.uuid4()
        last_index = len(greeters) - 1
        new_records = []
        for position, (npc, entry) in enumerate(greeters):
            PendingDialogueResponse.objects.create(
                utterance_id=utterance_id,
                npc_instance=npc,
                entry=entry,
                character=character,
                room=room,
                position=position,
                is_final=(position == last_index),
                fire_at=now + timedelta(
                    seconds=DIALOGUE_FIRST_DELAY_TICKS + position * DIALOGUE_STAGGER_TICKS,
                ),
            )
            new_records.append(DialogueGreetingRecord(character=character, npc_definition_id=npc.definition_id))
        DialogueGreetingRecord.objects.bulk_create(new_records)

    @database_sync_to_async
    def start_combat(self, npcs, first_attacker='character', focus_npc=None):
        existing = CombatSession.objects.filter(
            is_active=True,
            characters=self.character,
        ).first()
        if existing:
            session = existing
        else:
            session = CombatSession.objects.create(
                room_id=self.character.current_room_id,
                first_attacker=first_attacker,
            )
            session.characters.add(self.character)
        for npc in npcs:
            session.npcs.add(npc)
        if focus_npc is not None:
            session.focus_npc = focus_npc
        session.save()
        return session

    @database_sync_to_async
    def get_active_combat_session(self, character):
        return CombatSession.objects.filter(is_active=True, characters=character).first()

    @database_sync_to_async
    def set_session_focus(self, session, npc):
        session.focus_npc = npc
        session.save(update_fields=['focus_npc'])

    # ------------------------------------------------------------------
    # Fight-info feed (v20 brief 4, #2)
    # ------------------------------------------------------------------

    @database_sync_to_async
    def _fight_enemies(self, session):
        """Enemy rows for the fight message: every living NPC in the
        session, with the focus flag resolved the same way the tick engine
        resolves it (session focus if alive and present, else the first)."""
        npcs = list(session.npcs.select_related('definition')
                    .filter(is_alive=True).order_by('spawned_at', 'pk'))
        focus_pk = session.focus_npc_id
        if focus_pk is None or all(n.pk != focus_pk for n in npcs):
            focus_pk = npcs[0].pk if npcs else None
        return [
            {
                'name': npc_display_name(npc, npcs),
                'hp': npc.vitality_current,
                'hp_max': npc.vitality_max,
                'focused': npc.pk == focus_pk,
            }
            for npc in npcs
        ]

    async def send_fight(self, session):
        """Send the fight-info message for this player's session; None
        means combat has ended for the player and clears the pane."""
        if session is None:
            await self.send_json({'type': 'fight', 'active': False,
                                  'enemies': [], 'ts': envelope_ts()})
            return
        enemies = await self._fight_enemies(session)
        await self.send_json({'type': 'fight', 'active': True,
                              'enemies': enemies, 'ts': envelope_ts()})

    async def send_status_refresh(self):
        """Re-send the state-sync payload (combat-red state, location bar)
        after a combat-membership transition."""
        char = await self.get_character_fresh()
        room = await self.get_current_room()
        await self.send_json(await self._status_payload(char, room))

    @database_sync_to_async
    def npc_in_session(self, session, npc):
        return session.npcs.filter(pk=npc.pk).exists()

    @database_sync_to_async
    def get_session_npcs(self, session):
        return list(session.npcs.select_related('definition').all())

    @database_sync_to_async
    def end_combat_session(self, session):
        session.is_active = False
        session.save(update_fields=['is_active'])
        session.npcs.clear()

    @database_sync_to_async
    def get_flee_destination(self, character):
        room = Room.objects.select_related(
            'exit_north', 'exit_south', 'exit_east', 'exit_west', 'exit_up', 'exit_down'
        ).get(pk=character.current_room_id)
        exits = room.exits()

        reverse = REVERSE_DIRECTIONS.get(self.last_direction)
        if reverse and reverse in exits:
            destination = getattr(room, f'exit_{reverse}')
            if destination is not None:
                return destination, reverse

        available = list(exits.keys())
        if available:
            direction = random.choice(available)
            destination = getattr(room, f'exit_{direction}')
            if destination is not None:
                return destination, direction

        return None

    @database_sync_to_async
    def check_flee_cooldown(self, character, session):
        from django.utils import timezone
        from datetime import timedelta
        if session.last_flee_attempt_at is None:
            return False
        if session.last_flee_character_id != character.pk:
            return False
        cooldown_secs = FLEE_COOLDOWN_TICKS * COMBAT_ROUND_TICKS
        cutoff = timezone.now() - timedelta(seconds=cooldown_secs)
        return session.last_flee_attempt_at > cutoff

    @database_sync_to_async
    def record_flee_attempt(self, character, session):
        from django.utils import timezone
        session.last_flee_attempt_at = timezone.now()
        session.last_flee_character = character
        session.save(update_fields=['last_flee_attempt_at', 'last_flee_character'])

