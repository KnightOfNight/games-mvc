"""v25.3 (#267): the MC egress — the read-only WebSocket endpoint
through which remote agents attach to the MC event stream (GDD §10.11).

Transport only: no inbound frame may cause any game action, ORM write,
or stream write — the inbound vocabulary is exactly ``attach`` and
``ping``. Access is live ``agents.shyland`` membership at connect; the
gate is the group, not a character — this consumer never queries
Character. Agents own their cursors: server reads are stateless
XRANGE/XREAD, no consumer groups (those remain the persister's
mechanism alone), no server-side per-agent state. Gaps are announced,
never silent. Egress connections are not captured as stream events —
attach/detach get ``shyland.mc`` logger lines only.
"""

import asyncio
import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.shyland import mc

logger = logging.getLogger('shyland.mc')

MC_PROTOCOL = 1
REPLAY_BATCH = 500
LIVE_BLOCK_MS = 5000


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
            self._stream_task = asyncio.create_task(
                self._stream(content.get('after')))
            return
        # Everything else — a second attach included — draws the error
        # frame and is otherwise ignored; the connection stays open.
        await self.send_json({'type': 'error', 'error': 'read-only'})

    # ------------------------------------------------------------------
    # The stream task: (gap) → replay → live tail.

    async def _stream(self, after):
        try:
            client = mc._get_client()
            if after is None:
                last_id = '$'
            else:
                last_id = await self._replay(client, str(after))
            await self._live(client, last_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Never silent-dead: log and close so the agent reconnects.
            logger.warning('shyland mc: egress stream failed (agent=%s)',
                           self._agent, exc_info=True)
            await self.close()

    async def _replay(self, client, after):
        """Hot-window replay per §10.11: gap frame when the cursor
        predates the window, then batches from the right start. Returns
        the id the live tail reads from."""
        oldest = await client.xrange(mc.MC_STREAM_KEY, min='-', max='+',
                                     count=1)
        if not oldest:
            await self.send_json({'type': 'gap', 'requested': after,
                                  'oldest': None})
            return '$'
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
            result = await client.xread({mc.MC_STREAM_KEY: last_id},
                                        count=REPLAY_BATCH,
                                        block=LIVE_BLOCK_MS)
            if not result:
                continue
            for _stream, entries in result:
                if entries:
                    last_id = await self._send_entries(entries)
