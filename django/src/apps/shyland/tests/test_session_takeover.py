"""v21.1 (#116): single-session enforcement — the newest WebSocket
connection for a character takes over; the older connection prints a
farewell and closes. No room broadcast; the new connection sees nothing."""

import asyncio
import json

import redis.asyncio as aioredis
from channels.testing import WebsocketCommunicator
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.test import TransactionTestCase

from apps.shyland.consumers import SkylandConsumer
from apps.shyland.models import Archetype, Character, Origin, Room, Zone

FAREWELL = ("The world's attention shifts — your story is being told "
            "through another window now. This one falls quiet.")


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
        current_room=room, recall_room=room,
    )


class SessionTakeoverTests(TransactionTestCase):
    """End-to-end over the consumer. Requires the in-container environment
    (Redis reachable for presence/channel layer)."""

    async def _drain_until_map(self, communicator):
        """Consume output until the map payload — the last message the
        connect path sends — collecting every message seen."""
        seen = []
        while True:
            msg = await communicator.receive_json_from(timeout=10)
            seen.append(msg)
            if msg.get('type') == 'map':
                return seen

    async def _drain_until_room_render(self, communicator):
        """Consume output until a room description — what a bare 'look'
        ends with (look sends no map payload) — collecting every message
        seen."""
        seen = []
        while True:
            msg = await communicator.receive_json_from(timeout=10)
            seen.append(msg)
            if msg.get('type') == 'output' \
                    and msg.get('category') == 'room-render':
                return seen

    async def _connect(self, character):
        communicator = WebsocketCommunicator(
            SkylandConsumer.as_asgi(), '/ws/shyland/',
        )
        communicator.scope['user'] = character.user
        connected, _ = await communicator.connect()
        assert connected
        seen = await self._drain_until_map(communicator)
        return communicator, seen

    async def _presence_token(self, character_pk):
        r = aioredis.from_url('redis://redis:6379')
        try:
            raw = await r.get(f'shyland:online:{character_pk}')
            return None if raw is None else json.loads(raw)['token']
        finally:
            await r.aclose()

    async def test_second_connection_supersedes_first(self):
        zone, room = await sync_to_async(make_world)('Takeover')
        character = await sync_to_async(make_character)('Takeover', room)

        comm_a, _ = await self._connect(character)
        token_a = await self._presence_token(character.pk)
        self.assertIsNotNone(token_a)

        comm_b, seen_b = await self._connect(character)
        token_b = await self._presence_token(character.pk)
        self.assertIsNotNone(token_b)
        self.assertNotEqual(token_a, token_b)

        try:
            # A receives, in order: the farewell (category system), the
            # client-facing superseded event, then a server-side close.
            msg = await comm_a.receive_json_from(timeout=10)
            self.assertEqual(msg.get('type'), 'output')
            self.assertEqual(msg.get('category'), 'system')
            self.assertIn(FAREWELL, msg.get('text', ''))

            msg = await comm_a.receive_json_from(timeout=10)
            self.assertEqual(msg.get('event'), 'superseded')

            raw = await comm_a.receive_output(timeout=10)
            self.assertEqual(raw['type'], 'websocket.close')

            # Wait for A's disconnect path (guarded presence delete) to
            # settle, then B's presence value must still be in place.
            await asyncio.sleep(0.2)
            self.assertEqual(await self._presence_token(character.pk),
                             token_b)

            # B saw neither the farewell nor a superseded event during
            # its connect drain...
            for msg in seen_b:
                self.assertNotEqual(msg.get('event'), 'superseded')
                self.assertNotIn(FAREWELL, msg.get('text') or '')

            # ...and remains connected and functional: look round-trips.
            await comm_b.send_json_to({'text': 'look'})
            looked = await self._drain_until_room_render(comm_b)
            for msg in looked:
                self.assertNotEqual(msg.get('event'), 'superseded')
                self.assertNotIn(FAREWELL, msg.get('text') or '')
            self.assertTrue(any(
                msg.get('type') == 'output'
                and msg.get('category') == 'room-render'
                for msg in looked
            ))
        finally:
            await comm_b.disconnect()
            await comm_a.disconnect()

    async def test_single_connection_ignores_own_broadcast(self):
        zone, room = await sync_to_async(make_world)('Solo')
        character = await sync_to_async(make_character)('Solo', room)

        comm, seen = await self._connect(character)
        try:
            # The connect-time drain contains no farewell and no
            # superseded event — the consumer ignored its own broadcast
            # (token match).
            for msg in seen:
                self.assertNotEqual(msg.get('event'), 'superseded')
                self.assertNotIn(FAREWELL, msg.get('text') or '')

            # Normal play round-trips.
            await comm.send_json_to({'text': 'look'})
            looked = await self._drain_until_room_render(comm)
            self.assertTrue(any(
                msg.get('type') == 'output'
                and msg.get('category') == 'room-render'
                for msg in looked
            ))
        finally:
            await comm.disconnect()
