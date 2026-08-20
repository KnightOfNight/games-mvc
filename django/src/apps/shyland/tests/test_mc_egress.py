"""v25.3 brief 1 (#267): the MC egress — gate, read-only vocabulary,
attach/replay/gap semantics, decode robustness, and the agents.shyland
group migration (GDD §10.11).

Socket tests drive the real consumer via WebsocketCommunicator with the
stream client faked at ``mc._get_client`` (the test_mc_sink.py shape,
extended with the XRANGE/XREAD surface). No test touches the live
stream; the genuine-Redis pass is the brief's §7.5 live dev-stack check.
"""

import asyncio

from unittest import mock

from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser, Group, User
from django.test import SimpleTestCase, TestCase, TransactionTestCase

from apps.shyland import mc
from apps.shyland.mc_consumer import (
    MC_PROTOCOL, MCEgressConsumer, entry_to_frame,
)


def make_agent(prefix):
    user = User.objects.create_user(username=f'{prefix}_agent', password='x')
    group, _ = Group.objects.get_or_create(name='agents.shyland')
    user.groups.add(group)
    return user


def entry(stream_id, **overrides):
    """One fake raw stream entry — bytes throughout, the wire shape."""
    fields = {
        b'kind': b'out',
        b'actor_id': b'',
        b'actor_name': b'',
        b'room_id': b'',
        b'audience': b'[]',
        b'data': b'{}',
    }
    for key, value in overrides.items():
        fields[key.encode()] = value
    return (stream_id.encode(), fields)


class FakeEgressClient:
    """XRANGE/XREAD over a fixed in-memory window, plus a feed for live
    entries. XREAD blocks until fed (or pends forever), like BLOCK."""

    def __init__(self, window=()):
        self.window = list(window)
        self.live = asyncio.Queue()
        self.xread_calls = []

    def _parts(self, stream_id):
        ms, _, seq = stream_id.partition('-')
        return (int(ms), int(seq or 0))

    async def xrange(self, key, min='-', max='+', count=None):
        entries = self.window
        if min not in ('-', '+'):
            exclusive = min.startswith('(')
            start = self._parts(min[1:] if exclusive else min)
            entries = [
                e for e in entries
                if self._parts(e[0].decode()) > start
                or (not exclusive and self._parts(e[0].decode()) == start)
            ]
        if count is not None:
            entries = entries[:count]
        return entries

    async def xrevrange(self, key, max='+', min='-', count=None):
        entries = list(reversed(self.window))
        if count is not None:
            entries = entries[:count]
        return entries

    async def xread(self, streams, count=None, block=None):
        self.xread_calls.append(dict(streams))
        item = await self.live.get()
        if item is None:
            return []
        return [(b'mc:events', [item])]

    def feed(self, item):
        self.live.put_nowait(item)


class EgressCommunicator:
    """Context helper: the consumer over a faked stream client."""

    def __init__(self, user, fake):
        self.user = user
        self.fake = fake

    async def __aenter__(self):
        self.patch = mock.patch.object(mc, '_get_client', lambda: self.fake)
        self.patch.start()
        self.comm = WebsocketCommunicator(
            MCEgressConsumer.as_asgi(), '/ws/shyland/mc/')
        self.comm.scope['user'] = self.user
        connected, _ = await self.comm.connect()
        assert connected
        return self.comm

    async def __aexit__(self, *exc):
        await self.comm.disconnect()
        self.patch.stop()


class EgressGateTests(TransactionTestCase):
    """§2 rule 2: the three connect outcomes."""

    async def test_unauthenticated_handshake_rejected(self):
        comm = WebsocketCommunicator(
            MCEgressConsumer.as_asgi(), '/ws/shyland/mc/')
        comm.scope['user'] = AnonymousUser()
        connected, _ = await comm.connect()
        self.assertFalse(connected)
        await comm.disconnect()

    async def test_authenticated_non_member_closed_4403(self):
        user = await sync_to_async(User.objects.create_user)(
            username='egress_nonmember', password='x')
        comm = WebsocketCommunicator(
            MCEgressConsumer.as_asgi(), '/ws/shyland/mc/')
        comm.scope['user'] = user
        connected, _ = await comm.connect()
        self.assertTrue(connected)
        message = await comm.receive_output(timeout=10)
        self.assertEqual(message['type'], 'websocket.close')
        self.assertEqual(message['code'], 4403)
        await comm.disconnect()

    async def test_member_without_character_gets_hello(self):
        user = await sync_to_async(make_agent)('hello')
        async with EgressCommunicator(user, FakeEgressClient()) as comm:
            hello = await comm.receive_json_from(timeout=10)
            self.assertEqual(hello, {'type': 'hello',
                                     'protocol': MC_PROTOCOL})


class EgressReadOnlyTests(TransactionTestCase):
    """§2 rule 1: the vocabulary is attach and ping; nothing else does
    anything, and the connection survives it."""

    async def test_unknown_frame_draws_error_and_connection_survives(self):
        user = await sync_to_async(make_agent)('readonly')
        async with EgressCommunicator(user, FakeEgressClient()) as comm:
            await comm.receive_json_from(timeout=10)  # hello
            await comm.send_json_to({'type': 'say', 'text': 'hi'})
            error = await comm.receive_json_from(timeout=10)
            self.assertEqual(error, {'type': 'error', 'error': 'read-only'})
            await comm.send_json_to({'type': 'ping', 'nonce': 7})
            pong = await comm.receive_json_from(timeout=10)
            self.assertEqual(pong, {'type': 'pong', 'nonce': 7})

    async def test_second_attach_draws_error(self):
        user = await sync_to_async(make_agent)('reattach')
        async with EgressCommunicator(user, FakeEgressClient()) as comm:
            await comm.receive_json_from(timeout=10)  # hello
            await comm.send_json_to({'type': 'attach'})
            await comm.send_json_to({'type': 'attach'})
            error = await comm.receive_json_from(timeout=10)
            self.assertEqual(error, {'type': 'error', 'error': 'read-only'})


class EgressAttachTests(TransactionTestCase):
    """§3 lifecycle: bare attach goes live; attach-after replays the
    window then goes live; gaps are announced, never silent."""

    async def test_bare_attach_no_replay_then_live_event(self):
        user = await sync_to_async(make_agent)('live')
        fake = FakeEgressClient(window=[entry('5-1'), entry('6-1')])
        async with EgressCommunicator(user, fake) as comm:
            await comm.receive_json_from(timeout=10)  # hello
            await comm.send_json_to({'type': 'attach'})
            fake.feed(entry(
                '7-1', kind=b'cmd', actor_id=b'', actor_name=b'Tess',
                audience=b'[3, 9]', data=b'{"verb": "say"}'))
            event = await comm.receive_json_from(timeout=10)
            self.assertEqual(event, {
                'type': 'event', 'id': '7-1', 'kind': 'cmd',
                'actor_id': None, 'actor_name': 'Tess', 'room_id': None,
                'audience': [3, 9], 'data': {'verb': 'say'},
            })
            # No replay happened: the live tail starts at the window's
            # tail id (the concrete "now" — never $, the reissue race).
            self.assertEqual(fake.xread_calls[0], {'mc:events': '6-1'})

    async def test_resume_replays_after_id_in_order_then_live(self):
        user = await sync_to_async(make_agent)('resume')
        window = [entry('5-1'), entry('5-2'), entry('6-1'), entry('7-1')]
        fake = FakeEgressClient(window=window)
        async with EgressCommunicator(user, fake) as comm:
            await comm.receive_json_from(timeout=10)  # hello
            await comm.send_json_to({'type': 'attach', 'after': '5-2'})
            replayed = [await comm.receive_json_from(timeout=10)
                        for _ in range(2)]
            self.assertEqual([f['id'] for f in replayed], ['6-1', '7-1'])
            self.assertTrue(all(f['type'] == 'event' for f in replayed))
            fake.feed(entry('8-1', kind=b'connect'))
            live = await comm.receive_json_from(timeout=10)
            self.assertEqual(live['id'], '8-1')
            # The live tail picked up from the last replayed id.
            self.assertEqual(fake.xread_calls[0], {'mc:events': '7-1'})

    async def test_gap_announced_then_replay_from_oldest(self):
        user = await sync_to_async(make_agent)('gap')
        window = [entry('20-1'), entry('21-1')]
        fake = FakeEgressClient(window=window)
        async with EgressCommunicator(user, fake) as comm:
            await comm.receive_json_from(timeout=10)  # hello
            await comm.send_json_to({'type': 'attach', 'after': '3-5'})
            gap = await comm.receive_json_from(timeout=10)
            self.assertEqual(gap, {'type': 'gap', 'requested': '3-5',
                                   'oldest': '20-1'})
            replayed = [await comm.receive_json_from(timeout=10)
                        for _ in range(2)]
            self.assertEqual([f['id'] for f in replayed], ['20-1', '21-1'])

    async def test_gap_on_empty_window_oldest_null_then_live(self):
        user = await sync_to_async(make_agent)('gapempty')
        fake = FakeEgressClient(window=[])
        async with EgressCommunicator(user, fake) as comm:
            await comm.receive_json_from(timeout=10)  # hello
            await comm.send_json_to({'type': 'attach', 'after': '3-5'})
            gap = await comm.receive_json_from(timeout=10)
            self.assertEqual(gap, {'type': 'gap', 'requested': '3-5',
                                   'oldest': None})
            fake.feed(entry('30-1'))
            live = await comm.receive_json_from(timeout=10)
            self.assertEqual(live['id'], '30-1')


class EntryToFrameTests(SimpleTestCase):
    """§3 decode robustness — unit-level, no socket."""

    def test_full_decode(self):
        frame = entry_to_frame(b'12-3', {
            b'kind': b'out', b'actor_id': b'7', b'actor_name': b'Tess',
            b'room_id': b'3', b'audience': b'[9, 7]',
            b'data': b'{"category": "say"}',
        })
        self.assertEqual(frame, {
            'type': 'event', 'id': '12-3', 'kind': 'out', 'actor_id': 7,
            'actor_name': 'Tess', 'room_id': 3, 'audience': [9, 7],
            'data': {'category': 'say'},
        })

    def test_empty_ids_become_null(self):
        frame = entry_to_frame('1-1', {'actor_id': '', 'room_id': ''})
        self.assertIsNone(frame['actor_id'])
        self.assertIsNone(frame['room_id'])

    def test_malformed_json_passes_through_raw(self):
        frame = entry_to_frame('1-1', {'data': '{broken', 'audience': 'x'})
        self.assertEqual(frame['data'], '{broken')
        self.assertEqual(frame['audience'], 'x')


class AgentsGroupMigrationTests(TestCase):
    """§5.1: migration 0051 created the group (the test DB runs all
    migrations; TestCase ordering runs this before any
    TransactionTestCase flush can clear migration-seeded rows)."""

    def test_agents_group_exists(self):
        self.assertTrue(
            Group.objects.filter(name='agents.shyland').exists())
