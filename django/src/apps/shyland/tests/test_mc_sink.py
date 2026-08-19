"""v25.1 (#37): the MC sink — emit helper, chrome boundary, audience
resolution, and the never-log-secrets rule (GDD §10.11).

Unit tests mock the stream client; the capture tests run the real
consumer path end-to-end (in-container environment required — Redis
reachable for presence/channel layer), with ``mc.mc_emit`` replaced by
a recorder so nothing pollutes the live stream."""

import asyncio
import json

import redis.asyncio as aioredis
from unittest import mock

from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.conf import settings
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TransactionTestCase

from apps.shyland import mc
from apps.shyland.consumers import SkylandConsumer
from apps.shyland.models import Archetype, Character, Origin, Room, Zone


def make_world(prefix):
    zone = Zone.objects.create(
        name=f'{prefix} Zone', slug=f'{prefix}-zone',
        genre_tone='Test', danger_level='beginner',
        description='A test zone.',
    )
    room = Room.objects.create(
        zone=zone, name=f'{prefix} Room',
        description='The long form of the room.',
        brief_description='The room, briefly.',
        coord_x=0, coord_y=0,
    )
    return zone, room


def make_character(prefix, room):
    user = User.objects.create_user(username=f'{prefix}_user', password='x')
    origin = Origin.objects.create(
        name=f'{prefix} Origin', slug=f'{prefix}-origin',
        acuity_baseline=1.0, acuity_band_low=0.8, acuity_band_high=1.2,
    )
    archetype = Archetype.objects.create(
        name=f'{prefix} Archetype', slug=f'{prefix}-archetype',
        primary_stat_1='str', primary_stat_2='dex',
    )
    return Character.objects.create(
        user=user, name=f'{prefix} Char',
        origin=origin, archetype=archetype,
        current_room=room,
    )


class FakeStreamClient:
    def __init__(self):
        self.calls = []

    async def xadd(self, key, record, maxlen=None, approximate=None):
        self.calls.append((key, record, maxlen, approximate))


class ExplodingClient:
    async def xadd(self, *args, **kwargs):
        raise RuntimeError('redis down')

    async def mget(self, *keys):
        raise RuntimeError('redis down')


class EmitRecorder:
    def __init__(self):
        self.calls = []

    async def __call__(self, kind, *, actor_id=None, actor_name='',
                       room_id=None, audience=(), data=None):
        self.calls.append({
            'kind': kind, 'actor_id': actor_id, 'actor_name': actor_name,
            'room_id': room_id, 'audience': list(audience),
            'data': data or {},
        })

    def kinds(self):
        return [c['kind'] for c in self.calls]

    def with_data_type(self, type_name):
        return [c for c in self.calls
                if c['data'].get('type') == type_name]


class McEmitTests(SimpleTestCase):
    """The flat XADD record, MAXLEN bounding, and fire-and-forget."""

    def setUp(self):
        mc._last_warn = None

    def tearDown(self):
        mc._last_warn = None

    def test_emit_produces_flat_xadd_record(self):
        fake = FakeStreamClient()
        with mock.patch.object(mc, '_get_client', lambda: fake):
            asyncio.run(mc.mc_emit(
                'cmd', actor_id=7, actor_name='Tess', room_id=3,
                audience=[9, 7],
                data={'raw': 'say hi', 'verb': 'say', 'args': 'hi'}))
        key, record, maxlen, approximate = fake.calls[0]
        self.assertEqual(key, 'mc:events')
        self.assertEqual(record['kind'], 'cmd')
        self.assertEqual(record['actor_id'], '7')
        self.assertEqual(record['actor_name'], 'Tess')
        self.assertEqual(record['room_id'], '3')
        self.assertEqual(json.loads(record['audience']), [9, 7])
        self.assertEqual(json.loads(record['data']),
                         {'raw': 'say hi', 'verb': 'say', 'args': 'hi'})
        self.assertEqual(maxlen, settings.MC_STREAM_MAXLEN)
        self.assertTrue(approximate)

    def test_emit_none_ids_become_empty_strings(self):
        fake = FakeStreamClient()
        with mock.patch.object(mc, '_get_client', lambda: fake):
            asyncio.run(mc.mc_emit('out'))
        _key, record, _maxlen, _approximate = fake.calls[0]
        self.assertEqual(record['actor_id'], '')
        self.assertEqual(record['room_id'], '')
        self.assertEqual(json.loads(record['audience']), [])
        self.assertEqual(json.loads(record['data']), {})

    def test_fire_and_forget_never_raises(self):
        exploding = ExplodingClient()
        with mock.patch.object(mc, '_get_client', lambda: exploding):
            with self.assertLogs('apps.shyland.mc', level='WARNING') as logs:
                asyncio.run(mc.mc_emit('out'))
        self.assertEqual(len(logs.output), 1)

    def test_warning_throttle_second_failure_logs_nothing(self):
        exploding = ExplodingClient()
        with mock.patch.object(mc, '_get_client', lambda: exploding):
            asyncio.run(mc.mc_emit('out'))
            with mock.patch.object(mc.logger, 'warning') as warn:
                asyncio.run(mc.mc_emit('out'))
                warn.assert_not_called()


class ResolveRoomAudienceTests(TransactionTestCase):
    """Presence-filtered, exclude-honoring, failure yields []. Requires
    the in-container environment (real Redis presence keys)."""

    async def _set_presence(self, pks):
        r = aioredis.from_url(f'redis://{settings.REDIS_HOST}:6379')
        try:
            for pk in pks:
                await r.set(f'shyland:online:{pk}', '{"t":"test"}', ex=30)
        finally:
            await r.aclose()

    async def _clear_presence(self, pks):
        r = aioredis.from_url(f'redis://{settings.REDIS_HOST}:6379')
        try:
            for pk in pks:
                await r.delete(f'shyland:online:{pk}')
        finally:
            await r.aclose()

    async def test_presence_filter_and_excludes(self):
        zone, room = await sync_to_async(make_world)('Aud')
        online_a = await sync_to_async(make_character)('AudA', room)
        online_b = await sync_to_async(make_character)('AudB', room)
        offline = await sync_to_async(make_character)('AudC', room)
        await self._set_presence([online_a.pk, online_b.pk])
        try:
            self.assertEqual(
                await mc.resolve_room_audience(room.pk),
                sorted([online_a.pk, online_b.pk]))
            self.assertEqual(
                await mc.resolve_room_audience(
                    room.pk, exclude_pks=[online_a.pk]),
                [online_b.pk])
            self.assertNotIn(
                offline.pk, await mc.resolve_room_audience(room.pk))
        finally:
            await self._clear_presence([online_a.pk, online_b.pk])

    async def test_failure_yields_empty_list(self):
        zone, room = await sync_to_async(make_world)('AudFail')
        await sync_to_async(make_character)('AudFail', room)
        mc._last_warn = None
        exploding = ExplodingClient()
        with mock.patch.object(mc, '_get_client', lambda: exploding):
            self.assertEqual(await mc.resolve_room_audience(room.pk), [])


class McCaptureEndToEndTests(TransactionTestCase):
    """The chrome boundary and capture shape over the real consumer.
    ``mc.mc_emit`` is a recorder for the duration — no stream writes."""

    async def _connect(self, character):
        communicator = WebsocketCommunicator(
            SkylandConsumer.as_asgi(), '/ws/shyland/',
        )
        communicator.scope['user'] = character.user
        connected, _ = await communicator.connect()
        assert connected
        while True:
            msg = await communicator.receive_json_from(timeout=10)
            if msg.get('type') == 'map':
                return communicator

    async def test_chrome_boundary_and_capture(self):
        zone, room = await sync_to_async(make_world)('Chrome')
        character = await sync_to_async(make_character)('Chrome', room)
        recorder = EmitRecorder()
        with mock.patch.object(mc, 'mc_emit', recorder):
            comm = await self._connect(character)
            try:
                # The connect path: a connect record exists; the verbs
                # payload (chrome) produced no record.
                self.assertIn('connect', recorder.kinds())
                self.assertEqual(recorder.with_data_type('verbs'), [])
                connect_call = [c for c in recorder.calls
                                if c['kind'] == 'connect'][0]
                self.assertEqual(connect_call['audience'], [character.pk])

                # ping: chrome — no record at all.
                before = len(recorder.calls)
                await comm.send_json_to({'type': 'ping', 'nonce': 5})
                pong = await comm.receive_json_from(timeout=10)
                self.assertEqual(pong.get('type'), 'pong')
                self.assertEqual(len(recorder.calls), before)
                self.assertEqual(recorder.with_data_type('pong'), [])

                # complete: the request IS captured (cmd), the response
                # is chrome.
                before = len(recorder.calls)
                await comm.send_json_to({'type': 'complete', 'text': 'lo'})
                response = await comm.receive_json_from(timeout=10)
                self.assertEqual(response.get('type'), 'complete')
                new = recorder.calls[before:]
                self.assertEqual([c['kind'] for c in new], ['cmd'])
                self.assertEqual(new[0]['data'], {'complete': 'lo'})
                self.assertEqual(recorder.with_data_type('complete'), [])

                # A command: cmd record precedes its out records; the
                # say broadcast's audience lists the room's connected
                # characters (this one).
                before = len(recorder.calls)
                await comm.send_json_to({'text': 'say hello'})
                await comm.receive_json_from(timeout=10)  # echo
                await comm.receive_json_from(timeout=10)  # say line
                new = recorder.calls[before:]
                cmd_calls = [c for c in new if c['kind'] == 'cmd']
                self.assertEqual(len(cmd_calls), 1)
                self.assertEqual(cmd_calls[0]['data'],
                                 {'raw': 'say hello', 'verb': 'say',
                                  'args': 'hello'})
                say_broadcasts = [
                    c for c in new
                    if c['data'].get('category') == 'say']
                self.assertEqual(len(say_broadcasts), 1)
                self.assertIn(character.pk, say_broadcasts[0]['audience'])
            finally:
                await comm.disconnect()
            # The disconnect record arrived once the socket closed.
            self.assertIn('disconnect', recorder.kinds())

    async def test_superseded_record_carries_no_token(self):
        zone, room = await sync_to_async(make_world)('Token')
        character = await sync_to_async(make_character)('Token', room)
        recorder = EmitRecorder()
        with mock.patch.object(mc, 'mc_emit', recorder):
            comm_a = await self._connect(character)
            comm_b = await self._connect(character)
            try:
                superseded = [c for c in recorder.calls
                              if c['data'].get('event') == 'superseded']
                self.assertTrue(superseded)
                for call in superseded:
                    self.assertNotIn('token', call['data'])
                    self.assertNotIn('ts', call['data'])
                    self.assertEqual(call['audience'], [character.pk])
            finally:
                await comm_b.disconnect()
                await comm_a.disconnect()
