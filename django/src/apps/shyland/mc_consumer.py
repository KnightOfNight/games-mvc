"""v25.3 (#267): the MC egress — the WebSocket endpoint through which
remote agents attach to the MC event stream (GDD §10.11).

v25.5 (#281): the agent door — the endpoint grows from a read-only
tail into three vocabularies on one authenticated connection:
``tail`` (``attach``/``ping``, byte-identical to v25.3), ``query``,
and ``action``. The v25.3 read-only law is hereby superseded for the
connection and narrows to the tail: the tail itself still causes no
game action, but ``query``/``action`` frames (dispatched through
``mc_door``) read and mutate the world — every processed frame on the
record as an ``agent_query``/``agent_action`` stream event, every
player-visible effect line an ``out`` record at creation. Frames are
processed serially per connection (Channels delivers ``receive_json``
sequentially) — that serialization is the day-one rate discipline,
recorded deliberately (#261/#268 own per-agent scopes and limits).

Access is live ``agents.shyland`` membership at connect; the gate is
the group, not a character. The kill switch covers the whole door:
every query/action frame checks it fresh before processing (fail
closed); killed ⇒ close 4503, same as the tail sever. Agents own
their cursors: server reads are stateless XRANGE/XREAD, no consumer
groups (those remain the persister's mechanism alone), no server-side
per-agent state. Gaps are announced, never silent. Egress
*connections* are still not captured as stream events —
attach/detach/tail get ``shyland.mc`` logger lines only; queries and
actions are game-facing activity and are on the record.
"""

import asyncio
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.shyland import mc, mc_door

logger = logging.getLogger('shyland.mc')

MC_PROTOCOL = 2
# The §4 frame contract: client ids echo back verbatim, capped.
MAX_FRAME_ID_LEN = 64
REPLAY_BATCH = 500
# Must sit comfortably inside the reused client's socket_timeout
# (redis-py >= 8 defaults it to 5s): an XREAD whose server-side BLOCK
# equals the client-side read cap is a coin-flip race every idle cycle,
# and the loser tears down the connection. 2s block, 5s cap, no race.
LIVE_BLOCK_MS = 2000


def _text(value):
    return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value


def _id_parts(stream_id):
    """Numeric (ms, seq) of a dash-separated stream id — gap comparison
    is numeric on both parts, never a string compare."""
    ms, _, seq = str(stream_id).partition('-')
    return (int(ms), int(seq or 0))


def entry_to_frame(stream_id, fields):
    """Decode one raw stream entry into an ``event`` frame.

    bytes→str throughout; empty-string ``actor_id``/``room_id`` → None,
    else int; ``audience``/``data`` json-decoded. A field that fails to
    parse passes through as its raw string — a malformed entry never
    kills the connection.
    """
    decoded = {_text(k): _text(v) for k, v in fields.items()}
    frame = {'type': 'event', 'id': _text(stream_id),
             'kind': decoded.get('kind', '')}
    for key in ('actor_id', 'room_id'):
        raw = decoded.get(key, '')
        if raw == '':
            frame[key] = None
        else:
            try:
                frame[key] = int(raw)
            except (TypeError, ValueError):
                frame[key] = raw
    frame['actor_name'] = decoded.get('actor_name', '')
    for key in ('audience', 'data'):
        raw = decoded.get(key)
        try:
            frame[key] = json.loads(raw)
        except (TypeError, ValueError):
            frame[key] = raw
    return frame


@database_sync_to_async
def _switch_killed():
    from apps.shyland.models import MCKillSwitch
    return MCKillSwitch.is_killed()


async def switch_killed():
    """v25.4 (#266): the kill-switch read, fresh every call. Fail
    closed: any failure to read = killed. (Not the character table —
    the consumer's no-character-table law is untouched.)"""
    try:
        return await _switch_killed()
    except Exception:
        return True


class MCEgressConsumer(AsyncJsonWebsocketConsumer):
    """The §10.11 egress endpoint at ``ws/shyland/mc/``."""

    async def connect(self):
        self._stream_task = None
        self._attached = False
        self._agent = None
        user = self.scope['user']
        if not user.is_authenticated:
            # Handshake rejection — a close code cannot be delivered
            # pre-accept in Channels (the player-consumer pattern).
            await self.close()
            return
        if not await self.check_shyland_agent():
            # Accept-then-close so the code reaches the client.
            await self.accept()
            await self.close(code=4403)
            return
        # v25.4 (#266): the kill switch — checked after membership, so a
        # non-member sees 4403 either way (the switch leaks nothing).
        if await switch_killed():
            await self.accept()
            await self.close(code=4503)
            return
        self._agent = user.username
        await self.accept()
        await self.send_json({'type': 'hello', 'protocol': MC_PROTOCOL})
        logger.info('shyland mc: egress attach (agent=%s)', self._agent)

    async def disconnect(self, code):
        task = getattr(self, '_stream_task', None)
        if task is not None:
            task.cancel()
        if getattr(self, '_agent', None) is not None:
            logger.info('shyland mc: egress detach (agent=%s)', self._agent)

    @database_sync_to_async
    def check_shyland_agent(self):
        """#267 R1/R2: live membership check at connect, the
        check_shyland_admin shape — no session caching."""
        user = self.scope['user']
        return user.groups.filter(name='agents.shyland').exists()

    async def receive_json(self, content, **kwargs):
        mtype = content.get('type') if isinstance(content, dict) else None
        if mtype == 'ping':
            pong = {'type': 'pong'}
            if 'nonce' in content:
                pong['nonce'] = content['nonce']
            await self.send_json(pong)
            return
        if mtype == 'attach' and not self._attached:
            self._attached = True
            after = content.get('after')
            try:
                client = mc._get_client()
                # The bare attach's "now" is snapshotted here, inside
                # attach handling, not in the task: once the attach
                # frame is processed (observable via a ping/pong fence),
                # every later emission is guaranteed delivered.
                live_from = (await self._tail_id(client)
                             if after is None else None)
            except Exception:
                logger.warning(
                    'shyland mc: egress attach failed (agent=%s)',
                    self._agent, exc_info=True)
                await self.close()
                return
            self._stream_task = asyncio.create_task(
                self._stream(client, after, live_from))
            return
        if mtype in ('query', 'action'):
            # v25.5 (#281): kill switch first, fresh, per frame — the
            # switch covers the whole door, fail closed (v25.4 law).
            if await switch_killed():
                await self.close(code=4503)
                return
            await self._handle_request(mtype, content)
            return
        # Everything else — a second attach included — draws the error
        # frame and is otherwise ignored; the connection stays open.
        # (v25.5: the string was 'read-only' in protocol 1; the ruled
        # supersession renames it now that the door answers frames.)
        await self.send_json({'type': 'error', 'error': 'unknown-frame'})

    async def _handle_request(self, mtype, content):
        """One §4 request frame → one result frame → one MC record.

        Missing/non-string ``id`` ⇒ ``bad-frame`` with ``id: null``;
        unknown kinds ⇒ ``unknown-query``/``unknown-action``; malformed
        params ⇒ ``bad-params`` (handlers raise DoorError); anything
        unexpected ⇒ ``internal`` — the frame is refused, the
        connection survives. The record is emitted after processing,
        fire-and-forget, with the §6 envelope discipline (actor_name =
        the agent's username, everything else empty)."""
        kind_key = 'q' if mtype == 'query' else 'act'
        kind = content.get(kind_key)
        params = content.get('params')
        if params is None:
            params = {}
        handlers = (mc_door.QUERY_HANDLERS if mtype == 'query'
                    else mc_door.ACTION_HANDLERS)
        frame_id = content.get('id')
        ok, data, error, detail = False, None, None, ''
        if (not isinstance(frame_id, str)
                or len(frame_id) > MAX_FRAME_ID_LEN):
            frame_id = None
            error = 'bad-frame'
            detail = (f"'id' must be a string of at most "
                      f'{MAX_FRAME_ID_LEN} characters.')
        elif not isinstance(kind, str) or kind not in handlers:
            error = ('unknown-query' if mtype == 'query'
                     else 'unknown-action')
            detail = f'Unknown {kind_key!s} {kind!r}.'
        elif not isinstance(params, dict):
            error = 'bad-params'
            detail = "'params' must be an object."
        else:
            try:
                data = await handlers[kind](params, self._agent)
                ok = True
            except mc_door.DoorError as exc:
                error, detail = exc.code, exc.detail
            except Exception:
                logger.warning(
                    'shyland mc: %s handler failed (agent=%s, kind=%s)',
                    mtype, self._agent, kind, exc_info=True)
                error = 'internal'
                detail = ('The door hit an unexpected error; the frame '
                          'was refused.')
        result = {'type': 'result', 'id': frame_id, 'ok': ok}
        if ok:
            result['data'] = data
        else:
            result['error'] = error
            if detail:
                result['detail'] = detail
        await self.send_json(result)
        record = {kind_key: kind, 'params': params, 'ok': ok}
        if not ok:
            record['error'] = error
        elif mtype == 'action':
            record['result'] = data
        await mc.mc_emit(
            'agent_query' if mtype == 'query' else 'agent_action',
            actor_name=self._agent, data=record)

    # ------------------------------------------------------------------
    # The stream task: (gap) → replay → live tail.

    async def _stream(self, client, after, live_from):
        try:
            if after is None:
                last_id = live_from
            else:
                last_id = await self._replay(client, str(after))
                if last_id is None:
                    # Severed mid-replay (kill switch) — already closed.
                    return
            await self._live(client, last_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Never silent-dead: log and close so the agent reconnects.
            logger.warning('shyland mc: egress stream failed (agent=%s)',
                           self._agent, exc_info=True)
            await self.close()

    async def _tail_id(self, client):
        """The stream's current tail id — the concrete meaning of "live
        from now". The live tail always reads from a concrete id, never
        ``$``: entries landing between an XREAD returning and the next
        call would be silently dropped under ``$``.
        """
        tail = await client.xrevrange(mc.MC_STREAM_KEY, max='+', min='-',
                                      count=1)
        return _text(tail[0][0]) if tail else '0-0'

    async def _replay(self, client, after):
        """Hot-window replay per §10.11: gap frame when the cursor
        predates the window, then batches from the right start. Returns
        the id the live tail reads from."""
        oldest = await client.xrange(mc.MC_STREAM_KEY, min='-', max='+',
                                     count=1)
        if not oldest:
            await self.send_json({'type': 'gap', 'requested': after,
                                  'oldest': None})
            return '0-0'
        oldest_id = _text(oldest[0][0])
        if _id_parts(after) < _id_parts(oldest_id):
            await self.send_json({'type': 'gap', 'requested': after,
                                  'oldest': oldest_id})
            # Replay from oldest — inclusive; the requested id is gone.
            first = await self._send_entries(oldest)
            cursor = first
        else:
            cursor = after
        last_id = cursor
        while True:
            # v25.4 (#266): a kill during a long catch-up severs per
            # batch — replay never outlives the switch. None tells
            # _stream the connection is already closed.
            if await switch_killed():
                await self.close(code=4503)
                return None
            batch = await client.xrange(mc.MC_STREAM_KEY, min=f'({cursor}',
                                        max='+', count=REPLAY_BATCH)
            if not batch:
                break
            last_id = await self._send_entries(batch)
            cursor = last_id
            if len(batch) < REPLAY_BATCH:
                break
        return last_id

    async def _send_entries(self, entries):
        last_id = None
        for stream_id, fields in entries:
            last_id = _text(stream_id)
            await self.send_json(entry_to_frame(last_id, fields))
        return last_id

    async def _live(self, client, last_id):
        while True:
            # v25.4 (#266): the live sever — the loop wakes at least
            # every LIVE_BLOCK_MS, so a hung or rogue agent is cut
            # within ~2s without its cooperation. Fail closed.
            if await switch_killed():
                await self.close(code=4503)
                return
            result = await client.xread({mc.MC_STREAM_KEY: last_id},
                                        count=REPLAY_BATCH,
                                        block=LIVE_BLOCK_MS)
            if not result:
                continue
            for _stream, entries in result:
                if entries:
                    last_id = await self._send_entries(entries)
