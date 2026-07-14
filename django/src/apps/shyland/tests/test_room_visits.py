"""v20 brief 1 amendment 2 (#50): room visits are recorded at arrival time
in every arrival path, decoupled from room-description rendering. An aggro
ambush that skips the room description must not skip the visit."""

from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase

from apps.shyland.consumers import SkylandConsumer
from apps.shyland.models import (
    Archetype, Character, CombatSession, NpcDefinition, NpcInstance,
    Origin, Room, RoomVisit, Zone,
)


def make_world(prefix):
    """Two-room zone: A --north--> B, grid-adjacent per map geometry."""
    zone = Zone.objects.create(
        name=f'{prefix} Zone',
        slug=f'{prefix}-zone',
        genre_tone='Test',
        danger_level='beginner',
        description='A test zone.',
    )
    room_a = Room.objects.create(
        zone=zone, name=f'{prefix} A',
        description='The long form of room A.',
        brief_description='Room A, briefly.',
        coord_x=0, coord_y=0,
    )
    room_b = Room.objects.create(
        zone=zone, name=f'{prefix} B',
        description='The long form of room B.',
        brief_description='Room B, briefly.',
        coord_x=0, coord_y=1,
    )
    room_a.exit_north = room_b
    room_a.save(update_fields=['exit_north'])
    room_b.exit_south = room_a
    room_b.save(update_fields=['exit_south'])
    return zone, room_a, room_b


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


def make_aggro_npc(prefix, room):
    definition = NpcDefinition.objects.create(
        name=f'{prefix} Snarler', slug=f'{prefix}-snarler',
        description='A test aggressor.', genre_tag='fantasy',
        is_aggressive=True,
        base_vitality=10, base_str=1, base_dex=1, base_end=1,
        base_int=1, base_wis=1, base_per=1,
    )
    return NpcInstance.objects.create(
        definition=definition, current_room=room, spawn_room=room,
        vitality_current=10, vitality_max=10,
    )


# The raw sync functions behind the database_sync_to_async wrappers, so
# plain TestCase (transactional) tests can call them on this thread.
_record_room_visit = SkylandConsumer.__dict__['record_room_visit'].func
_resolve_room_rendering = SkylandConsumer.__dict__['_resolve_room_rendering'].func


class RoomVisitHelperTests(TestCase):
    """Unit coverage for the arrival-time recording helper and the now
    read-only rendering resolver."""

    def setUp(self):
        self.zone, self.room_a, self.room_b = make_world('Unit')
        self.character = make_character('Unit', self.room_a)
        self.consumer = SkylandConsumer()

    def record(self, room):
        return _record_room_visit(self.consumer, self.character, room)

    def resolve(self, room, force_long=False, first_visit=None):
        return _resolve_room_rendering(
            self.consumer, self.character, room, force_long, first_visit,
        )

    def test_record_reports_first_visit_and_is_idempotent(self):
        self.assertTrue(self.record(self.room_b))
        self.assertFalse(self.record(self.room_b))
        self.assertEqual(
            RoomVisit.objects.filter(
                character=self.character, room=self.room_b,
            ).count(),
            1,
        )

    def test_resolve_never_creates_visits(self):
        # Unvisited room renders long (first-entry rule) but the lookup
        # must not record the visit — that is the arrival paths' job.
        self.assertTrue(self.resolve(self.room_b))
        self.assertFalse(
            RoomVisit.objects.filter(
                character=self.character, room=self.room_b,
            ).exists()
        )

    def test_revisit_honors_brief_mode(self):
        self.record(self.room_b)
        self.character.brief_mode = True
        self.assertFalse(self.resolve(self.room_b))
        self.character.brief_mode = False
        self.assertTrue(self.resolve(self.room_b))

    def test_force_long_always_wins(self):
        self.record(self.room_b)
        self.character.brief_mode = True
        self.assertTrue(self.resolve(self.room_b, force_long=True))

    def test_explicit_first_visit_overrides_lookup(self):
        # Arrival paths pass the recording result; the resolver must trust
        # it rather than re-query (the visit row already exists by then).
        self.record(self.room_b)
        self.character.brief_mode = True
        self.assertTrue(self.resolve(self.room_b, first_visit=True))
        # first_visit=False with brief_mode on renders brief even with no row.
        self.assertFalse(self.resolve(self.room_a, first_visit=False))


class ArrivalRecordingTests(TransactionTestCase):
    """End-to-end over the consumer: the #50 regression case. Requires the
    in-container environment (Redis reachable for presence/channel layer)."""

    async def _drain_until_map(self, communicator):
        """Consume output until the map payload — the last message every
        movement path sends — collecting room-description texts seen."""
        room_texts = []
        while True:
            msg = await communicator.receive_json_from(timeout=10)
            if msg.get('type') == 'map':
                return room_texts
            if msg.get('type') == 'output' and msg.get('category') == 'room' \
                    and msg.get('exits') is not None:
                room_texts.append(msg['text'])

    async def _connect(self, character):
        communicator = WebsocketCommunicator(
            SkylandConsumer.as_asgi(), '/ws/shyland/',
        )
        communicator.scope['user'] = character.user
        connected, _ = await communicator.connect()
        assert connected
        await self._drain_until_map(communicator)
        return communicator

    async def test_aggro_entry_records_visit(self):
        zone, room_a, room_b = await sync_to_async(make_world)('Aggro')
        character = await sync_to_async(make_character)('Aggro', room_a)
        await sync_to_async(make_aggro_npc)('Aggro', room_b)

        communicator = await self._connect(character)
        try:
            await communicator.send_json_to({'text': 'north'})
            await self._drain_until_map(communicator)

            visit_exists = await sync_to_async(
                RoomVisit.objects.filter(
                    character=character, room=room_b,
                ).exists
            )()
            self.assertTrue(
                visit_exists,
                'Aggro entry must record a RoomVisit despite skipping the '
                'room description (#50).',
            )
            in_combat = await sync_to_async(
                CombatSession.objects.filter(
                    is_active=True, characters=character,
                ).exists
            )()
            self.assertTrue(in_combat, 'Aggro engagement itself must be intact.')
        finally:
            await communicator.disconnect()

    async def test_peaceful_entry_first_long_then_brief(self):
        zone, room_a, room_b = await sync_to_async(make_world)('Peace')
        character = await sync_to_async(make_character)('Peace', room_a)

        communicator = await self._connect(character)
        try:
            # First entry: long form, exactly one room description.
            await communicator.send_json_to({'text': 'north'})
            texts = await self._drain_until_map(communicator)
            self.assertEqual(len(texts), 1)
            self.assertIn('The long form of room B.', texts[0])

            visit_exists = await sync_to_async(
                RoomVisit.objects.filter(
                    character=character, room=room_b,
                ).exists
            )()
            self.assertTrue(visit_exists)

            # Revisit: brief_mode (default True) renders the brief form.
            await communicator.send_json_to({'text': 'south'})
            await self._drain_until_map(communicator)
            await communicator.send_json_to({'text': 'north'})
            texts = await self._drain_until_map(communicator)
            self.assertEqual(len(texts), 1)
            self.assertIn('Room B, briefly.', texts[0])

            # look: always long, and still no duplicate visit rows.
            await communicator.send_json_to({'text': 'look'})
            msg = await communicator.receive_json_from(timeout=10)
            while not (msg.get('type') == 'output'
                       and msg.get('category') == 'room'
                       and msg.get('exits') is not None):
                msg = await communicator.receive_json_from(timeout=10)
            self.assertIn('The long form of room B.', msg['text'])

            visit_count = await sync_to_async(
                RoomVisit.objects.filter(
                    character=character, room=room_b,
                ).count
            )()
            self.assertEqual(visit_count, 1)
        finally:
            await communicator.disconnect()

    async def test_respawn_records_visit_at_recall_room(self):
        zone, room_a, room_b = await sync_to_async(make_world)('Respawn')
        character = await sync_to_async(make_character)('Respawn', room_a)
        await sync_to_async(
            Character.objects.filter(pk=character.pk).update
        )(recall_room=room_b)

        communicator = await self._connect(character)
        try:
            # Simulate the tick engine's execute_death relocation, then its
            # respawn event to the player group.
            await sync_to_async(
                Character.objects.filter(pk=character.pk).update
            )(current_room=room_b)
            await get_channel_layer().group_send(f'player_{character.pk}', {
                'type': 'player_message',
                'event': 'respawn',
                'text': 'You have died and awakened.',
                'category': 'system',
            })
            texts = await self._drain_until_map(communicator)

            visit_exists = await sync_to_async(
                RoomVisit.objects.filter(
                    character=character, room=room_b,
                ).exists
            )()
            self.assertTrue(
                visit_exists,
                'Respawn arrival at the recall room must record a RoomVisit.',
            )
            # First-ever arrival there: the long form must render.
            self.assertEqual(len(texts), 1)
            self.assertIn('The long form of room B.', texts[0])
        finally:
            await communicator.disconnect()
