"""v25.8 brief 1 (#294/#290/#296/#299/#300): bot memory and record
search — the AgentMemory store and its four-verb door vocabulary, the
rooms directory query and the move origin receipt, the events/event
MC-record search, and the game-rendered report action delivered through
the shared player compositions.

Socket tests drive the real MCEgressConsumer over the
test_mc_agent_door fixtures (faked stream/presence client, recording
channel layer)."""

import json
from datetime import timedelta

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.test import TransactionTestCase
from django.utils import timezone
from unittest import mock

from apps.shyland import mc_door
from apps.shyland.item_utils import (
    carry_capacity, equipment_doll_lines, inventory_table_lines,
)
from apps.shyland.models import AgentMemory, ItemInstance, MCEvent, Room
from apps.shyland.tests.test_mc_agent_door import (
    DoorTestBase, FakeDoorClient, RecordingLayer, make_equippable, request,
)
from apps.shyland.tests.test_mc_kill_switch import engage_switch
from apps.shyland.tests.test_new_commands import grant_admin
from apps.shyland.tests.test_room_visits import make_character


async def query(comm, q, params, frame_id='1'):
    return await request(comm, {'type': 'query', 'id': frame_id, 'q': q,
                                'params': params})


async def action(comm, act, params, frame_id='1'):
    return await request(comm, {'type': 'action', 'id': frame_id,
                                'act': act, 'params': params})


# ----------------------------------------------------------------------
# Memory (#294)
# ----------------------------------------------------------------------

class MemoryRoundTripTests(DoorTestBase):

    async def test_waypoint_round_trip(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('mem_wp')
        async with self.door(agent) as comm:
            taught = await action(comm, 'remember', {
                'kind': 'waypoint', 'name': 'battle',
                'data': {'room_id': room_b.pk},
                'taught_by': char.name,
            })
            self.assertTrue(taught['ok'])
            self.assertEqual(taught['data']['result'], 'created')
            memory_id = taught['data']['id']

            listing = await query(comm, 'memories', {})
            self.assertTrue(listing['ok'])
            self.assertEqual(listing['data']['count'], 1)
            row = listing['data']['memories'][0]
            self.assertEqual(row['id'], memory_id)
            self.assertEqual(row['kind'], 'waypoint')
            self.assertEqual(row['name'], 'battle')
            # Live summary: the current zone/room path (no area here).
            self.assertEqual(row['summary'],
                             f'{zone.name}: {room_b.name}')

            detail = await query(comm, 'memory', {'id': memory_id})
            self.assertTrue(detail['ok'])
            self.assertEqual(detail['data']['data'], {'room_id': room_b.pk})
            # taught_by resolved to the teaching character's user.
            self.assertEqual(detail['data']['taught_by'],
                             char.user.username)

            gone = await action(comm, 'forget', {'id': memory_id})
            self.assertTrue(gone['ok'])
            self.assertEqual(gone['data']['forgotten'],
                             {'id': memory_id, 'kind': 'waypoint',
                              'name': 'battle'})
            self.assertEqual(
                await sync_to_async(AgentMemory.objects.count)(), 0)

    async def test_bundle_round_trip_with_labeled_detail(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('mem_bn')
        sword = await sync_to_async(make_equippable)(
            'mem_bn', 'Test Sword', 'weapon', ['MAIN_HAND'])
        lines = [[sword.slug, 1, 'common', 2]]
        async with self.door(agent) as comm:
            taught = await action(comm, 'remember', {
                'kind': 'bundle', 'name': 'starter kit',
                'data': {'lines': lines},
            })
            self.assertTrue(taught['ok'])
            memory_id = taught['data']['id']

            listing = await query(comm, 'memories', {'kind': 'bundle'})
            self.assertEqual(listing['data']['memories'][0]['summary'],
                             '1 lines')

            detail = await query(comm, 'memory', {'id': memory_id})
            # Stored positional, rendered legible.
            self.assertEqual(detail['data']['data']['lines'], [
                {'slug': sword.slug, 'mk_tier': 1, 'rarity': 'common',
                 'quantity': 2},
            ])
            # Absent taught_by is null — audit, not authorization.
            self.assertIsNone(detail['data']['taught_by'])

    async def test_upsert_case_insensitive_created_then_replaced(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('mem_up')
        async with self.door(agent) as comm:
            first = await action(comm, 'remember', {
                'kind': 'waypoint', 'name': 'Battle',
                'data': {'room_id': room_a.pk}})
            self.assertEqual(first['data']['result'], 'created')
            second = await action(comm, 'remember', {
                'kind': 'waypoint', 'name': 'BATTLE',
                'data': {'room_id': room_b.pk}})
            self.assertEqual(second['data']['result'], 'replaced')
            self.assertEqual(second['data']['id'], first['data']['id'])
        row = await sync_to_async(AgentMemory.objects.get)()
        # The replace takes the new casing and the new payload.
        self.assertEqual(row.name, 'BATTLE')
        self.assertEqual(row.data, {'room_id': room_b.pk})

    async def test_memory_and_forget_not_found(self):
        agent, *_ = await sync_to_async(self._fixture)('mem_nf')
        async with self.door(agent) as comm:
            detail = await query(comm, 'memory', {'id': 999999})
            self.assertFalse(detail['ok'])
            self.assertEqual(detail['error'], 'not-found')
            gone = await action(comm, 'forget', {'id': 999999})
            self.assertFalse(gone['ok'])
            self.assertEqual(gone['error'], 'not-found')


class MemoryTeachValidationTests(DoorTestBase):

    async def test_waypoint_nonexistent_room_refused(self):
        agent, *_ = await sync_to_async(self._fixture)('mem_vr')
        async with self.door(agent) as comm:
            result = await action(comm, 'remember', {
                'kind': 'waypoint', 'name': 'nowhere',
                'data': {'room_id': 999999}})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'not-found')

    async def test_bundle_bad_slug_rarity_artifact_refused(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('mem_vb')
        sword = await sync_to_async(make_equippable)(
            'mem_vb', 'Vb Sword', 'weapon', ['MAIN_HAND'])
        async with self.door(agent) as comm:
            bad_slug = await action(comm, 'remember', {
                'kind': 'bundle', 'name': 'k1',
                'data': {'lines': [['no-such-slug', 1, 'common', 1]]}})
            self.assertFalse(bad_slug['ok'])
            self.assertEqual(bad_slug['error'], 'not-found')

            bad_rarity = await action(comm, 'remember', {
                'kind': 'bundle', 'name': 'k2',
                'data': {'lines': [[sword.slug, 1, 'shiny', 1]]}})
            self.assertFalse(bad_rarity['ok'])
            self.assertEqual(bad_rarity['error'], 'bad-params')

            artifact = await action(comm, 'remember', {
                'kind': 'bundle', 'name': 'k3',
                'data': {'lines': [[sword.slug, 1, 'artifact', 1]]}})
            self.assertFalse(artifact['ok'])
            self.assertEqual(artifact['error'], 'bad-params')
            self.assertIn('artifact', artifact['detail'])
        self.assertEqual(
            await sync_to_async(AgentMemory.objects.count)(), 0)

    async def test_unknown_kind_and_long_name_refused(self):
        agent, zone, room_a, *_ = await sync_to_async(
            self._fixture)('mem_vk')
        async with self.door(agent) as comm:
            result = await action(comm, 'remember', {
                'kind': 'grudge', 'name': 'x',
                'data': {'room_id': room_a.pk}})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            result = await action(comm, 'remember', {
                'kind': 'waypoint', 'name': 'x' * 61,
                'data': {'room_id': room_a.pk}})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')


class MemoryCapTests(DoorTestBase):
    """The three cap refusals — distinct legible errors, never silent
    truncation."""

    async def test_row_cap_memory_full(self):
        agent, zone, room_a, *_ = await sync_to_async(
            self._fixture)('mem_cr')
        async with self.door(agent) as comm:
            with mock.patch.object(mc_door, 'MEMORY_MAX_ROWS_PER_AGENT', 1):
                first = await action(comm, 'remember', {
                    'kind': 'waypoint', 'name': 'one',
                    'data': {'room_id': room_a.pk}})
                self.assertTrue(first['ok'])
                second = await action(comm, 'remember', {
                    'kind': 'waypoint', 'name': 'two',
                    'data': {'room_id': room_a.pk}})
                self.assertFalse(second['ok'])
                self.assertEqual(second['error'], 'memory-full')
                # Replacing an existing name never trips the row cap.
                replace = await action(comm, 'remember', {
                    'kind': 'waypoint', 'name': 'ONE',
                    'data': {'room_id': room_a.pk}})
                self.assertTrue(replace['ok'])
                self.assertEqual(replace['data']['result'], 'replaced')

    async def test_payload_cap_payload_too_large(self):
        agent, zone, room_a, *_ = await sync_to_async(
            self._fixture)('mem_cp')
        async with self.door(agent) as comm:
            with mock.patch.object(mc_door, 'MEMORY_MAX_PAYLOAD_BYTES', 4):
                result = await action(comm, 'remember', {
                    'kind': 'waypoint', 'name': 'big',
                    'data': {'room_id': room_a.pk}})
                self.assertFalse(result['ok'])
                self.assertEqual(result['error'], 'payload-too-large')

    async def test_bundle_line_cap_too_many_lines(self):
        agent, *_ = await sync_to_async(self._fixture)('mem_cl')
        sword = await sync_to_async(make_equippable)(
            'mem_cl', 'Cl Sword', 'weapon', ['MAIN_HAND'])
        lines = [[sword.slug, 1, 'common', 1]] * 51
        async with self.door(agent) as comm:
            result = await action(comm, 'remember', {
                'kind': 'bundle', 'name': 'big kit',
                'data': {'lines': lines}})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'too-many-lines')


class MemoryListingTests(DoorTestBase):

    async def test_windowing_and_newest_first(self):
        agent, zone, room_a, *_ = await sync_to_async(
            self._fixture)('mem_lw')
        async with self.door(agent) as comm:
            for name in ('old', 'mid', 'new'):
                result = await action(comm, 'remember', {
                    'kind': 'waypoint', 'name': name,
                    'data': {'room_id': room_a.pk}})
                self.assertTrue(result['ok'])
            now = timezone.now()
            for name, age_days in (('old', 10), ('mid', 5), ('new', 0)):
                await sync_to_async(
                    AgentMemory.objects.filter(name=name).update)(
                        created_at=now - timedelta(days=age_days))

            listing = await query(comm, 'memories', {})
            self.assertEqual(
                [r['name'] for r in listing['data']['memories']],
                ['new', 'mid', 'old'])

            windowed = await query(comm, 'memories', {
                'since': (now - timedelta(days=7)).isoformat(),
                'until': (now - timedelta(days=1)).isoformat()})
            self.assertEqual(
                [r['name'] for r in windowed['data']['memories']],
                ['mid'])
            self.assertEqual(windowed['data']['count'], 1)

    async def test_dangling_room_summary(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('mem_dg')
        async with self.door(agent) as comm:
            taught = await action(comm, 'remember', {
                'kind': 'waypoint', 'name': 'doomed',
                'data': {'room_id': room_b.pk}})
            self.assertTrue(taught['ok'])
            await sync_to_async(
                Room.objects.filter(pk=room_b.pk).delete)()
            listing = await query(comm, 'memories', {})
            self.assertEqual(listing['data']['memories'][0]['summary'],
                             '(room no longer exists)')

    async def test_store_scoped_to_requesting_agent(self):
        agent, zone, room_a, *_ = await sync_to_async(
            self._fixture)('mem_sc')
        other = await sync_to_async(User.objects.create_user)(
            username='mem_sc_other', password='x')
        row = await sync_to_async(AgentMemory.objects.create)(
            agent=other, kind='waypoint', name='theirs',
            data={'room_id': room_a.pk})
        async with self.door(agent) as comm:
            listing = await query(comm, 'memories', {})
            self.assertEqual(listing['data']['count'], 0)
            detail = await query(comm, 'memory', {'id': row.pk})
            self.assertEqual(detail['error'], 'not-found')
            gone = await action(comm, 'forget', {'id': row.pk})
            self.assertEqual(gone['error'], 'not-found')


# ----------------------------------------------------------------------
# Rooms (#290) + the move origin receipt
# ----------------------------------------------------------------------

class RoomsQueryTests(DoorTestBase):

    async def test_substring_zone_filter_shape_and_cap(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('rooms_q')
        result = None
        async with self.door(agent) as comm:
            result = await query(comm, 'rooms', {'name': 'rooms_q'})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data']['count'], 2)
            # Ordered by zone name then room name; the _room_dict shape.
            self.assertEqual(result['data']['rooms'][0], {
                'id': room_a.pk, 'name': room_a.name,
                'area': None, 'zone': zone.name,
            })

            miss = await query(comm, 'rooms', {'name': 'rooms_q',
                                               'zone': 'no such zone'})
            self.assertEqual(miss['data']['count'], 0)
            hit = await query(comm, 'rooms', {'name': ' B',
                                              'zone': zone.name.lower()})
            self.assertEqual([r['id'] for r in hit['data']['rooms']],
                             [room_b.pk])

            with mock.patch.object(mc_door, 'LIST_CAP', 1):
                capped = await query(comm, 'rooms', {'name': 'rooms_q'})
                self.assertEqual(capped['data']['count'], 1)

            missing_name = await query(comm, 'rooms', {})
            self.assertFalse(missing_name['ok'])
            self.assertEqual(missing_name['error'], 'bad-params')

    async def test_move_receipt_carries_origin(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('rooms_mv')
        async with self.door(agent) as comm:
            result = await action(comm, 'move', {
                'name': char.name, 'to_room_id': room_b.pk})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data']['room']['id'], room_b.pk)
            self.assertEqual(result['data']['from_room'], {
                'id': room_a.pk, 'name': room_a.name,
                'area': None, 'zone': zone.name,
            })


# ----------------------------------------------------------------------
# Record search (#300)
# ----------------------------------------------------------------------

def make_event(stream_id, age_hours=0, kind='combat_hit', actor_id=None,
               actor_name='', room_id=None, data=None):
    return MCEvent.objects.create(
        stream_id=stream_id, ts=timezone.now() - timedelta(hours=age_hours),
        kind=kind, actor_id=actor_id, actor_name=actor_name,
        room_id=room_id, data=data if data is not None else {'n': stream_id},
    )


class EventSearchTests(DoorTestBase):

    async def test_default_window_is_24h_and_newest_first(self):
        agent, *_ = await sync_to_async(self._fixture)('ev_w')
        await sync_to_async(make_event)('ev-w-old', age_hours=30)
        await sync_to_async(make_event)('ev-w-mid', age_hours=12)
        await sync_to_async(make_event)('ev-w-new', age_hours=1)
        async with self.door(agent) as comm:
            result = await query(comm, 'events', {})
            self.assertTrue(result['ok'])
            self.assertEqual(
                [e['stream_id'] for e in result['data']['events']],
                ['ev-w-new', 'ev-w-mid'])
            widened = await query(comm, 'events', {
                'since': (timezone.now()
                          - timedelta(hours=48)).isoformat()})
            self.assertEqual(widened['data']['count'], 3)

    async def test_text_over_seven_days_refused(self):
        agent, *_ = await sync_to_async(self._fixture)('ev_7')
        async with self.door(agent) as comm:
            result = await query(comm, 'events', {
                'text': 'sword',
                'since': (timezone.now() - timedelta(days=8)).isoformat()})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            self.assertIn('7 days', result['detail'])
            # The same span without text is fine.
            result = await query(comm, 'events', {
                'since': (timezone.now() - timedelta(days=8)).isoformat()})
            self.assertTrue(result['ok'])

    async def test_filters_cap_and_gist(self):
        agent, *_ = await sync_to_async(self._fixture)('ev_f')
        await sync_to_async(make_event)(
            'ev-f-1', age_hours=3, kind='agent_action', actor_id=7,
            actor_name='sudo', room_id=42,
            data={'act': 'gift', 'params': {'slug': 'iron-mace'}})
        await sync_to_async(make_event)(
            'ev-f-2', age_hours=2, kind='combat_hit', actor_id=8,
            actor_name='Player One', room_id=42)
        await sync_to_async(make_event)(
            'ev-f-3', age_hours=1, kind='combat_hit', actor_id=8,
            actor_name='Player One', room_id=43,
            data={'text': 'x' * 300})
        async with self.door(agent) as comm:
            by_kind = await query(comm, 'events', {'kind': 'agent_action'})
            self.assertEqual([e['stream_id']
                              for e in by_kind['data']['events']],
                             ['ev-f-1'])
            by_actor_id = await query(comm, 'events', {'actor': 8})
            self.assertEqual(by_actor_id['data']['count'], 2)
            by_actor_name = await query(comm, 'events', {'actor': 'SUDO'})
            self.assertEqual([e['stream_id']
                              for e in by_actor_name['data']['events']],
                             ['ev-f-1'])
            by_room = await query(comm, 'events', {'room_id': 42})
            self.assertEqual(by_room['data']['count'], 2)
            by_text = await query(comm, 'events', {'text': 'iron-mace'})
            self.assertEqual([e['stream_id']
                              for e in by_text['data']['events']],
                             ['ev-f-1'])
            # Gist truncates the serialized payload to 120 chars.
            row = (await query(comm, 'events',
                               {'room_id': 43}))['data']['events'][0]
            self.assertEqual(len(row['gist']), 120)
            with mock.patch.object(mc_door, 'LIST_CAP', 2):
                capped = await query(comm, 'events', {})
                self.assertEqual(capped['data']['count'], 2)
                # ':' appears in every serialized payload — the cap
                # bounds the text walk too.
                capped_text = await query(comm, 'events', {'text': ':'})
                self.assertEqual(capped_text['data']['count'], 2)

    async def test_event_by_stream_id_and_not_found(self):
        agent, *_ = await sync_to_async(self._fixture)('ev_one')
        event = await sync_to_async(make_event)(
            'ev-one-1', age_hours=1, actor_id=9, actor_name='Someone',
            room_id=5, data={'k': 'v'})
        async with self.door(agent) as comm:
            result = await query(comm, 'event', {'stream_id': 'ev-one-1'})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'], {
                'stream_id': 'ev-one-1',
                'ts': event.ts.isoformat(),
                'kind': 'combat_hit',
                'actor_id': 9,
                'actor_name': 'Someone',
                'room_id': 5,
                'audience': [],
                'data': {'k': 'v'},
            })
            miss = await query(comm, 'event', {'stream_id': 'nope'})
            self.assertFalse(miss['ok'])
            self.assertEqual(miss['error'], 'not-found')


# ----------------------------------------------------------------------
# Rendered report (#296)
# ----------------------------------------------------------------------

class ReportTests(DoorTestBase):

    def _report_fixture(self, prefix):
        agent, zone, room_a, room_b, char = self._fixture(prefix)
        admin = make_character(f'{prefix}_adm', room_a)
        grant_admin(admin)
        sword_def = make_equippable(prefix, f'{prefix} Sword', 'weapon',
                                    ['MAIN_HAND'])
        potion_def = make_equippable(prefix, f'{prefix} Potion',
                                     'consumable', [])
        equipped = ItemInstance.objects.create(
            definition=sword_def, owner=char, mk_tier=1, rarity='common',
            is_equipped=True, equipped_slot='MAIN_HAND',
            is_soulbound=True, soulbound_to=char)
        carried = ItemInstance.objects.create(
            definition=potion_def, owner=char, mk_tier=1, rarity='common')
        return agent, char, admin, equipped, carried

    async def test_non_admin_recipient_refused(self):
        (agent, char, admin, equipped,
         carried) = await sync_to_async(self._report_fixture)('rep_na')
        async with self.door(agent) as comm:
            result = await action(comm, 'report', {
                'to': char.name, 'character': char.name,
                'kind': 'inventory'})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'not-admin')

    async def test_unknown_kind_refused(self):
        (agent, char, admin, equipped,
         carried) = await sync_to_async(self._report_fixture)('rep_uk')
        async with self.door(agent) as comm:
            result = await action(comm, 'report', {
                'to': admin.name, 'character': char.name,
                'kind': 'wallet'})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')

    async def test_offline_recipient_delivered_false(self):
        (agent, char, admin, equipped,
         carried) = await sync_to_async(self._report_fixture)('rep_off')
        fake, layer = FakeDoorClient(), RecordingLayer()
        async with self.door(agent, fake, layer) as comm:
            result = await action(comm, 'report', {
                'to': admin.name, 'character': char.name,
                'kind': 'inventory'})
            self.assertTrue(result['ok'])
            self.assertFalse(result['data']['delivered'])
            self.assertEqual(result['data']['item_count'], 2)
        self.assertEqual(layer.sent, [])

    async def test_delivery_leader_then_sections_privately(self):
        (agent, char, admin, equipped,
         carried) = await sync_to_async(self._report_fixture)('rep_ok')
        fake, layer = FakeDoorClient(), RecordingLayer()
        fake.set_online(admin)
        async with self.door(agent, fake, layer) as comm:
            result = await action(comm, 'report', {
                'to': admin.name, 'character': char.name,
                'kind': 'inventory'})
            self.assertTrue(result['ok'])
            self.assertTrue(result['data']['delivered'])
            self.assertEqual(result['data']['item_count'], 2)

        # Privately to the recipient's pane only — never a room group.
        self.assertEqual({group for group, _ in layer.sent},
                         {f'player_{admin.pk}'})
        events = [event for _, event in layer.sent]
        self.assertEqual(len(events), 3)
        # 1. The door-composed leader, sudo-voiced, count from live data.
        self.assertEqual(events[0]['text'],
                         f'sudo: {char.name} (2 items total)')
        self.assertEqual(events[0]['category'], 'sudo')
        # 2-3. Equipped then carried, byte-identical to the player
        # compositions, in the player report category.
        expected_doll, expected_inv = await sync_to_async(
            self._expected_sections)(char)
        self.assertEqual(events[1]['category'], 'report')
        self.assertEqual(events[1]['lines'], expected_doll)
        self.assertEqual(events[2]['category'], 'report')
        self.assertEqual(events[2]['lines'], expected_inv)

    @staticmethod
    def _expected_sections(char):
        items = list(ItemInstance.objects.filter(owner=char)
                     .select_related('definition'))
        equipped = [i for i in items if i.is_equipped]
        unequipped = [i for i in items if not i.is_equipped]
        return (
            equipment_doll_lines(equipped),
            inventory_table_lines(unequipped, len(unequipped),
                                  carry_capacity(char, equipped)),
        )


# ----------------------------------------------------------------------
# Kill-switch coverage — one new query, one new action
# ----------------------------------------------------------------------

class NewKindsKillSwitchTests(DoorTestBase):

    async def test_killed_switch_severs_memories_query(self):
        agent, *_ = await sync_to_async(self._fixture)('ks_q8')
        async with self.door(agent) as comm:
            await sync_to_async(engage_switch)()
            await comm.send_json_to(
                {'type': 'query', 'id': '1', 'q': 'memories', 'params': {}})
            message = await comm.receive_output(timeout=10)
            self.assertEqual(message['type'], 'websocket.close')
            self.assertEqual(message['code'], 4503)

    async def test_killed_switch_severs_remember_action(self):
        agent, zone, room_a, *_ = await sync_to_async(
            self._fixture)('ks_a8')
        async with self.door(agent) as comm:
            await sync_to_async(engage_switch)()
            await comm.send_json_to(
                {'type': 'action', 'id': '1', 'act': 'remember',
                 'params': {'kind': 'waypoint', 'name': 'x',
                            'data': {'room_id': room_a.pk}}})
            message = await comm.receive_output(timeout=10)
            self.assertEqual(message['type'], 'websocket.close')
            self.assertEqual(message['code'], 4503)
        self.assertEqual(
            await sync_to_async(AgentMemory.objects.count)(), 0)
