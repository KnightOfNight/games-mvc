"""V24.25 Brief 1 (#41, #95, GDD §2.12): zone entry locks and keys.

Locks are world data (Zone.entry_requires_zone, seed-authored); keys are
player data (ZoneCompletion, permanent, never revoked). Coverage: the
model, key minting at the record_room_visit choke point, the
transition-generic gate on walking and travel, the pooled refusal and
completion speech, the muted travel listing, and the seed authoring
(the brief's 6d table)."""

import io

from asgiref.sync import sync_to_async
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase

from apps.shyland.consumers import (
    ZONE_COMPLETE_LINES, ZONE_LOCK_REFUSAL_LINES,
    ZONE_LOCK_REFUSAL_LINES_NO_AREA,
)
from apps.shyland.models import (
    Area, Room, RoomVisit, TravelNode, Zone, ZoneCompletion,
)
from apps.shyland.tests.test_command_revamp import (
    make_character, make_stub_consumer, outputs,
)


def make_zone(prefix, name=None):
    return Zone.objects.create(
        name=name or f'{prefix} Zone', slug=f'{prefix}-zone',
        genre_tone='Test', danger_level='beginner',
        description='A test zone.',
    )


def make_room(zone, name, x, y, area=None):
    return Room.objects.create(
        zone=zone, name=name, area=area,
        description=f'The long form of {name}.',
        brief_description=f'{name}, briefly.',
        coord_x=x, coord_y=y,
    )


def link_north(south_room, north_room):
    south_room.exit_north = north_room
    south_room.save(update_fields=['exit_north'])
    north_room.exit_south = south_room
    north_room.save(update_fields=['exit_south'])


def visit(character, *rooms):
    for room in rooms:
        RoomVisit.objects.create(character=character, room=room)


def warn_texts(sent):
    return [m['text'] for m in outputs(sent) if m['category'] == 'warn']


def reward_texts(sent):
    return [m['text'] for m in outputs(sent) if m['category'] == 'reward']


class ZoneLockModelTests(TestCase):
    """Brief step 7.1: the model surface."""

    def test_completion_uniqueness(self):
        zone = make_zone('zlmu')
        room = make_room(zone, 'zlmu Room', 0, 0)
        char = make_character('zlmu', room)
        ZoneCompletion.objects.create(character=char, zone=zone)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ZoneCompletion.objects.create(character=char, zone=zone)
        self.assertEqual(
            ZoneCompletion.objects.filter(character=char, zone=zone).count(),
            1,
        )

    def test_entry_requires_zone_present_and_nullable(self):
        hub = make_zone('zlmh')
        gated = make_zone('zlmg')
        self.assertIsNone(gated.entry_requires_zone)
        gated.entry_requires_zone = hub
        gated.save(update_fields=['entry_requires_zone'])
        gated.refresh_from_db()
        self.assertEqual(gated.entry_requires_zone_id, hub.pk)


class KeyMintingTests(TransactionTestCase):
    """Brief step 7.2: minting at the record_room_visit choke point."""

    def _world(self, prefix):
        zone = make_zone(prefix)
        room_a = make_room(zone, f'{prefix} A', 0, 0)
        room_b = make_room(zone, f'{prefix} B', 0, 1)
        link_north(room_a, room_b)
        char = make_character(prefix, room_a)
        visit(char, room_a)
        return zone, room_a, room_b, char

    async def test_last_room_mints_exactly_one_key_and_announces(self):
        zone, room_a, room_b, char = await sync_to_async(self._world)('mint')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_move('north')

        count = await sync_to_async(
            ZoneCompletion.objects.filter(character=char, zone=zone).count)()
        self.assertEqual(count, 1)
        rewards = reward_texts(sent)
        self.assertEqual(len(rewards), 1)
        expected_pool = [line.format(zone=zone.name)
                         for line in ZONE_COMPLETE_LINES]
        self.assertIn(rewards[0], expected_pool)

    async def test_rearrival_mints_nothing_and_announces_nothing(self):
        zone, room_a, room_b, char = await sync_to_async(self._world)('remint')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_move('north')
        del sent[:]
        await consumer.cmd_move('south')
        await consumer.cmd_move('north')

        count = await sync_to_async(
            ZoneCompletion.objects.filter(character=char, zone=zone).count)()
        self.assertEqual(count, 1)
        self.assertEqual(reward_texts(sent), [])

    async def test_precreated_completion_suppresses_announcement(self):
        zone, room_a, room_b, char = await sync_to_async(self._world)('gfmint')
        # The grandfather path: the key already exists before the final
        # room is walked.
        await sync_to_async(ZoneCompletion.objects.create)(
            character=char, zone=zone)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_move('north')

        count = await sync_to_async(
            ZoneCompletion.objects.filter(character=char, zone=zone).count)()
        self.assertEqual(count, 1)
        self.assertEqual(reward_texts(sent), [])
        room_b_visited = await sync_to_async(
            RoomVisit.objects.filter(character=char, room=room_b).exists)()
        self.assertTrue(room_b_visited)


class WalkingGateTests(TransactionTestCase):
    """Brief step 7.3: the gate on cmd_move."""

    def _world(self, prefix):
        """Hub with an unvisited two-room Area (most unseen) and an
        unvisited one-room Area; a gated zone north of the start room."""
        hub = make_zone(f'{prefix}h', name=f'{prefix} Hub')
        far = Area.objects.create(
            zone=hub, name=f'{prefix} Far Side', slug=f'{prefix}-far-side')
        near = Area.objects.create(
            zone=hub, name=f'{prefix} Near Side', slug=f'{prefix}-near-side')
        start = make_room(hub, f'{prefix} Start', 0, 0)
        make_room(hub, f'{prefix} Far 1', 1, 0, area=far)
        make_room(hub, f'{prefix} Far 2', 2, 0, area=far)
        make_room(hub, f'{prefix} Near 1', -1, 0, area=near)
        gated = make_zone(f'{prefix}g', name=f'{prefix} Gated')
        gated.entry_requires_zone = hub
        gated.save(update_fields=['entry_requires_zone'])
        inside = make_room(gated, f'{prefix} Inside', 0, 1)
        link_north(start, inside)
        char = make_character(prefix, start)
        visit(char, start)
        return hub, far, start, inside, char

    async def test_keyless_move_is_refused_with_the_fullest_area(self):
        hub, far, start, inside, char = await sync_to_async(self._world)('wg')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_move('north')

        warns = warn_texts(sent)
        self.assertEqual(len(warns), 1)
        expected_pool = [
            line.format(zone=hub.name, area=far.name)
            for line in ZONE_LOCK_REFUSAL_LINES
        ]
        self.assertIn(warns[0], expected_pool)

        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, start.pk)
        inside_visited = await sync_to_async(
            RoomVisit.objects.filter(character=char, room=inside).exists)()
        self.assertFalse(inside_visited)

    async def test_move_with_the_key_proceeds(self):
        hub, far, start, inside, char = await sync_to_async(self._world)('wk')
        await sync_to_async(ZoneCompletion.objects.create)(
            character=char, zone=hub)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_move('north')

        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, inside.pk)
        self.assertEqual(warn_texts(sent), [])


class TravelGateTests(TransactionTestCase):
    """Brief step 7.4: the same pair through cmd_travel."""

    def _world(self, prefix):
        hub = make_zone(f'{prefix}h', name=f'{prefix} Hub')
        back = Area.objects.create(
            zone=hub, name=f'{prefix} Back Half', slug=f'{prefix}-back-half')
        start = make_room(hub, f'{prefix} Start', 0, 0)
        make_room(hub, f'{prefix} Back 1', 1, 0, area=back)
        gated = make_zone(f'{prefix}g', name=f'{prefix} Gated')
        gated.entry_requires_zone = hub
        gated.save(update_fields=['entry_requires_zone'])
        inside = make_room(gated, f'{prefix} Inside', 0, 0)
        TravelNode.objects.create(
            room=start, travel_name=f'{prefix} Hubstone',
            node_type='obelisk', listing_description='The hub obelisk.')
        TravelNode.objects.create(
            room=inside, travel_name=f'{prefix} Lockhaven',
            node_type='obelisk', listing_description='The gated obelisk.')
        char = make_character(prefix, start)
        # Revealed-but-locked: the destination was seen (its node is
        # revealed) while the hub is not yet complete.
        visit(char, start, inside)
        return hub, back, start, inside, char

    async def test_keyless_travel_is_refused(self):
        hub, back, start, inside, char = await sync_to_async(self._world)('tg')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_travel('tg lockhaven')

        warns = warn_texts(sent)
        self.assertEqual(len(warns), 1)
        expected_pool = [
            line.format(zone=hub.name, area=back.name)
            for line in ZONE_LOCK_REFUSAL_LINES
        ]
        self.assertIn(warns[0], expected_pool)
        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, start.pk)

    async def test_travel_with_the_key_proceeds(self):
        hub, back, start, inside, char = await sync_to_async(self._world)('tk')
        await sync_to_async(ZoneCompletion.objects.create)(
            character=char, zone=hub)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_travel('tk lockhaven')

        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, inside.pk)
        self.assertEqual(warn_texts(sent), [])


class NoAreaFallbackTests(TransactionTestCase):
    """Brief step 7.5: when no unvisited room of the required zone has an
    Area, the fallback pool speaks."""

    async def test_no_area_fallback_pool(self):
        def setup():
            hub = make_zone('nah', name='nah Hub')
            start = make_room(hub, 'nah Start', 0, 0)
            make_room(hub, 'nah Bare', 1, 0)  # unvisited, area-free
            gated = make_zone('nag', name='nah Gated')
            gated.entry_requires_zone = hub
            gated.save(update_fields=['entry_requires_zone'])
            inside = make_room(gated, 'nah Inside', 0, 1)
            link_north(start, inside)
            char = make_character('nah', start)
            visit(char, start)
            return hub, char
        hub, char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_move('north')

        warns = warn_texts(sent)
        self.assertEqual(len(warns), 1)
        expected_pool = [line.format(zone=hub.name)
                         for line in ZONE_LOCK_REFUSAL_LINES_NO_AREA]
        self.assertIn(warns[0], expected_pool)


class TravelListingTests(TransactionTestCase):
    """Brief step 7.6: muted rows for locked zones, zone-colored heading,
    unlocked zones unchanged, tab completion intact."""

    def _world(self, prefix):
        hub = make_zone(f'{prefix}h', name=f'{prefix} Hub')
        hub.theme_color = '#B387E8'
        hub.save(update_fields=['theme_color'])
        start = make_room(hub, f'{prefix} Start', 0, 0)
        make_room(hub, f'{prefix} Unseen', 1, 0)

        locked = make_zone(f'{prefix}l', name=f'{prefix} Locked')
        locked.theme_color = '#7DC95E'
        locked.entry_requires_zone = hub
        locked.save(update_fields=['theme_color', 'entry_requires_zone'])
        locked_room = make_room(locked, f'{prefix} Locked Stop', 0, 0)

        open_zone = make_zone(f'{prefix}o', name=f'{prefix} Open')
        open_room = make_room(open_zone, f'{prefix} Open Stop', 0, 0)

        TravelNode.objects.create(
            room=start, travel_name=f'{prefix} Hubstone',
            node_type='obelisk', listing_description='The hub obelisk.')
        TravelNode.objects.create(
            room=locked_room, travel_name=f'{prefix} Lockhaven',
            node_type='obelisk', listing_description='A gated stop.')
        TravelNode.objects.create(
            room=open_room, travel_name=f'{prefix} Freeport',
            node_type='obelisk', listing_description='An open stop.')

        char = make_character(prefix, start)
        visit(char, start, locked_room, open_room)
        return hub, locked, open_zone, char

    def _report_lines(self, sent):
        reports = [m for m in sent if m.get('category') == 'report'
                   and 'lines' in m]
        self.assertEqual(len(reports), 1)
        return reports[0]['lines']

    def _seg_for(self, lines, text):
        for line in lines:
            for seg in line.get('segs', []):
                if text in seg.get('t', ''):
                    return seg
        self.fail(f'No seg containing {text!r} in the listing')

    async def test_locked_rows_muted_heading_zone_colored(self):
        hub, locked, open_zone, char = await sync_to_async(self._world)('tl')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_travel('')
        lines = self._report_lines(sent)

        heading = self._seg_for(lines, locked.name)
        self.assertEqual(heading.get('x'), locked.theme_color)
        self.assertNotIn('c', heading)

        locked_cell = self._seg_for(lines, 'Lockhaven')
        self.assertEqual(locked_cell.get('c'), 'muted')
        locked_desc = self._seg_for(lines, 'A gated stop.')
        self.assertEqual(locked_desc.get('c'), 'muted')

        open_cell = self._seg_for(lines, 'Freeport')
        self.assertEqual(open_cell.get('c'), 'value')

    async def test_locked_destination_still_tab_completes(self):
        hub, locked, open_zone, char = await sync_to_async(self._world)('tc')
        sent = []
        consumer = make_stub_consumer(char, sent)
        options = await consumer._complete_travel('')
        self.assertIn('tc lockhaven', options)


class SeedTests(TransactionTestCase):
    """Brief step 7.7: seed run twice (idempotence), then the 6d table,
    both theme colors, and the lock authoring."""

    # The 6d table is authoritative.
    EXPECTED_MEMBERSHIPS = {
        'the-everround': 40,
        'morras-smithy': 2,
        'wisteria-walk': 4,
        'bamboo-run': 4,
        'basalt-way': 5,
        'fern-boards': 4,
    }

    def test_seed_twice_then_the_6d_table(self):
        call_command('seed_world', stdout=io.StringIO())
        call_command('seed_world', stdout=io.StringIO())

        everround = Area.objects.get(slug='the-everround')
        self.assertEqual(everround.name, 'The Everround')
        self.assertEqual(everround.theme_color, '#C9AE7A')
        smithy = Area.objects.get(slug='morras-smithy')
        self.assertEqual(smithy.name, "Morra's Smithy")
        self.assertEqual(smithy.theme_color, '#C0855C')

        for slug, expected in self.EXPECTED_MEMBERSHIPS.items():
            self.assertEqual(
                Room.objects.filter(
                    zone__slug='the-convergence', area__slug=slug).count(),
                expected, f'area {slug}',
            )
        area_free = Room.objects.filter(
            zone__slug='the-convergence', area__isnull=True)
        self.assertEqual(area_free.count(), 1)
        self.assertEqual(area_free.get().name, 'Heart of the Convergence')
        self.assertEqual(
            Room.objects.filter(zone__slug='the-convergence').count(), 60)

        self.assertEqual(
            Zone.objects.get(slug='the-verdant-reach')
            .entry_requires_zone.slug,
            'the-convergence',
        )
        self.assertEqual(
            Zone.objects.exclude(slug='the-verdant-reach')
            .filter(entry_requires_zone__isnull=False).count(),
            0,
        )


class PoolLawTests(TestCase):
    """Pooled speech law: every pool in this brief has >= 3 lines."""

    def test_pool_sizes(self):
        self.assertGreaterEqual(len(ZONE_LOCK_REFUSAL_LINES), 3)
        self.assertGreaterEqual(len(ZONE_LOCK_REFUSAL_LINES_NO_AREA), 3)
        self.assertGreaterEqual(len(ZONE_COMPLETE_LINES), 3)
