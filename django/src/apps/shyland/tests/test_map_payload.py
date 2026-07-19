"""v22 brief 1 (#82, #115): Maps V2 payload. Frontier entries are masked by
construction (exactly x, y, discovered — fog-of-war enforced in the wire
format), exit statuses are tri-state by destination RoomVisit, agro is
configuration not instance state, and the build holds a bounded, constant
query count (post-#107 discipline)."""

from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase

from apps.shyland.consumers import SkylandConsumer
from apps.shyland.models import (
    Archetype, Character, NpcDefinition, NpcInstance, Origin, Room,
    RoomSpawn, RoomVisit, TravelNode, Zone,
)


def make_map_world(prefix):
    """Purpose-built Maps V2 fixture zone.

    Grid (z=0 unless noted):

        (0,2)  deep        unvisited, depth 2 — must never appear
        (0,1)  node_front  unvisited frontier, has a TravelNode
        (0,0)  center      current room (no RoomVisit row), TravelNode,
                           up->upper (z=1, visited), down->lower (z=-1,
                           unvisited), south->gate_dest boundary-flagged
        (-1,0) west        visited, passive spawn only
        (1,0)  east        visited, aggressive spawn (dead instance),
                           east->xzone cross-zone
        (0,-1) gate_dest   intra-zone boundary destination
        (2,0)  xzone       other-zone destination
    """
    zone = Zone.objects.create(
        name=f'{prefix} Zone', slug=f'{prefix}-zone', genre_tone='Test',
        danger_level='beginner', description='A test zone.',
    )
    other_zone = Zone.objects.create(
        name=f'{prefix} Other Zone', slug=f'{prefix}-other-zone',
        genre_tone='Test', danger_level='beginner', description='Another.',
    )

    def room(z, key, x, y, cz=0):
        return Room.objects.create(
            zone=z, name=f'{prefix} {key}',
            description=f'The long form of {key}.',
            brief_description=f'{key}, briefly.',
            coord_x=x, coord_y=y, coord_z=cz,
        )

    rooms = {
        'center': room(zone, 'center', 0, 0),
        'east': room(zone, 'east', 1, 0),
        'west': room(zone, 'west', -1, 0),
        'node_front': room(zone, 'node-front', 0, 1),
        'deep': room(zone, 'deep', 0, 2),
        'gate_dest': room(zone, 'gate-dest', 0, -1),
        'upper': room(zone, 'upper', 0, 0, 1),
        'lower': room(zone, 'lower', 0, 0, -1),
        'xzone': room(other_zone, 'xzone', 2, 0),
    }

    def link(a, direction, b, reverse, boundary=False):
        setattr(rooms[a], f'exit_{direction}', rooms[b])
        setattr(rooms[b], f'exit_{reverse}', rooms[a])
        if boundary:
            setattr(rooms[a], f'exit_{direction}_boundary', True)
            setattr(rooms[b], f'exit_{reverse}_boundary', True)

    link('center', 'east', 'east', 'west')
    link('center', 'west', 'west', 'east')
    link('center', 'north', 'node_front', 'south')
    link('node_front', 'north', 'deep', 'south')
    link('center', 'south', 'gate_dest', 'north', boundary=True)
    link('center', 'up', 'upper', 'down')
    link('center', 'down', 'lower', 'up')
    link('east', 'east', 'xzone', 'west')
    for r in rooms.values():
        r.save()

    TravelNode.objects.create(
        room=rooms['center'], travel_name=f'{prefix} Center',
        node_type='obelisk',
    )
    TravelNode.objects.create(
        room=rooms['node_front'], travel_name=f'{prefix} Node Front',
        node_type='checkpoint',
    )

    aggressive = NpcDefinition.objects.create(
        name=f'{prefix} Snarler', slug=f'{prefix}-snarler',
        description='A test aggressor.', genre_tag='fantasy',
        is_aggressive=True,
        base_vitality=10, base_str=1, base_dex=1, base_end=1,
        base_int=1, base_wis=1, base_per=1,
    )
    passive = NpcDefinition.objects.create(
        name=f'{prefix} Grazer', slug=f'{prefix}-grazer',
        description='A test grazer.', genre_tag='fantasy',
        is_aggressive=False,
        base_vitality=10, base_str=1, base_dex=1, base_end=1,
        base_int=1, base_wis=1, base_per=1,
    )
    RoomSpawn.objects.create(room=rooms['east'], npc_definition=aggressive)
    RoomSpawn.objects.create(room=rooms['west'], npc_definition=passive)
    # Agro is configuration, not instance state: the only instance of the
    # aggressive definition is dead, and the room must still flag.
    NpcInstance.objects.create(
        definition=aggressive, current_room=rooms['east'],
        spawn_room=rooms['east'], vitality_current=0, vitality_max=10,
        is_alive=False,
    )
    return zone, rooms


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


# The raw sync function behind the database_sync_to_async wrapper, so plain
# TestCase tests can call it on this thread.
_build_map_payload = SkylandConsumer.__dict__['build_map_payload'].func


class MapPayloadTests(TestCase):
    """Unit coverage for build_map_payload against the fixture zone."""

    def setUp(self):
        self.zone, self.rooms = make_map_world('Map')
        self.character = make_character('Map', self.rooms['center'])
        # Visited: east, west, upper. NOT center (defense-in-depth case),
        # node_front, deep, gate_dest, lower, or xzone.
        for key in ('east', 'west', 'upper'):
            RoomVisit.objects.create(
                character=self.character, room=self.rooms[key],
            )

    def build(self):
        consumer = SkylandConsumer()
        consumer.character = self.character
        consumer.character_pk = self.character.pk
        return _build_map_payload(consumer)

    def entries_by_coord(self, payload):
        return {(r['x'], r['y']): r for r in payload['rooms']}

    def test_top_level_schema(self):
        payload = self.build()
        self.assertEqual(payload['type'], 'map')
        self.assertEqual(payload['zone'], self.zone.slug)
        self.assertEqual(payload['current'], {'x': 0, 'y': 0})

    def test_frontier_masking(self):
        payload = self.build()
        frontier = [r for r in payload['rooms'] if not r['discovered']]
        self.assertTrue(frontier)
        for entry in frontier:
            self.assertEqual(set(entry), {'x', 'y', 'discovered'})

    def test_frontier_extent(self):
        # node_front is the only unvisited fragment room adjacent to a
        # discovered one; deep (depth 2) must never appear.
        payload = self.build()
        by_coord = self.entries_by_coord(payload)
        self.assertIn((0, 1), by_coord)
        self.assertFalse(by_coord[(0, 1)]['discovered'])
        self.assertNotIn((0, 2), by_coord)
        frontier = [r for r in payload['rooms'] if not r['discovered']]
        self.assertEqual(len(frontier), 1)

    def test_frontier_travel_node_masked(self):
        # node_front has a TravelNode; masking beats specialness.
        payload = self.build()
        entry = self.entries_by_coord(payload)[(0, 1)]
        self.assertNotIn('travel_node', entry)

    def test_agro_is_configuration_not_state(self):
        # east's only aggressive instance is dead; the room still flags.
        payload = self.build()
        by_coord = self.entries_by_coord(payload)
        self.assertIs(by_coord[(1, 0)]['agro'], True)
        self.assertIs(by_coord[(-1, 0)]['agro'], False)

    def test_exit_statuses(self):
        payload = self.build()
        by_coord = self.entries_by_coord(payload)
        self.assertEqual(by_coord[(0, 0)]['exits'], {
            'east': 'known',        # east visited
            'west': 'known',        # west visited
            'north': 'unknown',     # node_front unvisited
            'south': 'gate-unknown',  # boundary-flagged, dest unvisited
        })
        self.assertEqual(by_coord[(1, 0)]['exits'], {
            'west': 'known',
            'east': 'gate-unknown',  # cross-zone, dest unvisited
        })

    def test_gate_statuses_track_destination_visits(self):
        RoomVisit.objects.create(
            character=self.character, room=self.rooms['gate_dest'],
        )
        RoomVisit.objects.create(
            character=self.character, room=self.rooms['xzone'],
        )
        payload = self.build()
        by_coord = self.entries_by_coord(payload)
        self.assertEqual(by_coord[(0, 0)]['exits']['south'], 'gate-known')
        self.assertEqual(by_coord[(1, 0)]['exits']['east'], 'gate-known')

    def test_up_down_tristate(self):
        payload = self.build()
        by_coord = self.entries_by_coord(payload)
        center = by_coord[(0, 0)]
        self.assertEqual(center['up'], 'known')      # upper visited
        self.assertEqual(center['down'], 'unknown')  # lower unvisited
        east = by_coord[(1, 0)]
        self.assertNotIn('up', east)                 # no exit: key absent
        self.assertNotIn('down', east)

    def test_here_on_exactly_the_current_room(self):
        # center has no RoomVisit row and must still be included, with here.
        self.assertFalse(
            RoomVisit.objects.filter(
                character=self.character, room=self.rooms['center'],
            ).exists()
        )
        payload = self.build()
        here = [r for r in payload['rooms'] if r.get('here')]
        self.assertEqual(len(here), 1)
        self.assertEqual((here[0]['x'], here[0]['y']), (0, 0))
        self.assertIs(here[0]['discovered'], True)
        self.assertIs(here[0]['travel_node'], True)

    def test_query_ceiling(self):
        # The performance regression guard: the build is five constant
        # queries (current room, zone rooms, visit union, aggro ids,
        # travel-node ids) — never per-room.
        with self.assertNumQueries(5):
            self.build()

    def test_gate_destinations_never_in_rooms_array(self):
        RoomVisit.objects.create(
            character=self.character, room=self.rooms['gate_dest'],
        )
        RoomVisit.objects.create(
            character=self.character, room=self.rooms['xzone'],
        )
        payload = self.build()
        by_coord = self.entries_by_coord(payload)
        self.assertNotIn((0, -1), by_coord)  # intra-zone boundary dest
        self.assertNotIn((2, 0), by_coord)   # cross-zone dest


class MapDeliveryTests(TransactionTestCase):
    """End-to-end over the consumer: the new-schema map message arrives on
    connect and on move. Requires the in-container environment (Redis
    reachable for presence/channel layer)."""

    async def _next_map(self, communicator):
        while True:
            msg = await communicator.receive_json_from(timeout=10)
            if msg.get('type') == 'map':
                return msg

    async def test_map_arrives_on_connect_and_move(self):
        zone, rooms = await sync_to_async(make_map_world)('Deliver')
        character = await sync_to_async(make_character)(
            'Deliver', rooms['center'],
        )

        communicator = WebsocketCommunicator(
            SkylandConsumer.as_asgi(), '/ws/shyland/',
        )
        communicator.scope['user'] = character.user
        connected, _ = await communicator.connect()
        assert connected
        try:
            msg = await self._next_map(communicator)
            self.assertEqual(msg['zone'], zone.slug)
            self.assertEqual(msg['current'], {'x': 0, 'y': 0})
            for entry in msg['rooms']:
                self.assertIn('discovered', entry)
                if not entry['discovered']:
                    self.assertEqual(set(entry), {'x', 'y', 'discovered'})
            here = [r for r in msg['rooms'] if r.get('here')]
            self.assertEqual(len(here), 1)

            await communicator.send_json_to({'text': 'north'})
            msg = await self._next_map(communicator)
            self.assertEqual(msg['current'], {'x': 0, 'y': 1})
            here = [r for r in msg['rooms'] if r.get('here')]
            self.assertEqual(len(here), 1)
            self.assertEqual((here[0]['x'], here[0]['y']), (0, 1))
            # The former frontier node is now discovered and shows its
            # specialness.
            self.assertIs(here[0]['travel_node'], True)
        finally:
            await communicator.disconnect()
