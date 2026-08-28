"""v25.9 brief 1 (#302): structural receipts — the door half. The
``move`` action's third destination form (``waypoint``: lookup-and-act
atomic in the door, agent-scoped through the memory verbs' addressing
law) and the ``answer`` action's machinery-only ``receipts`` param
(door-composed ``sudo did:`` lines, receipts-only delivery).

Socket tests drive the real MCEgressConsumer over the
test_mc_agent_door fixtures (faked stream/presence client, recording
channel layer). The bot-side ledger/composer half is exercised by the
brief's deterministic driver check — ``agents/`` is outside the Django
image (the 25.8 precedent)."""

from asgiref.sync import sync_to_async

from apps.shyland.models import AgentMemory, Room
from apps.shyland.tests.test_mc_agent_door import (
    DoorTestBase, FakeDoorClient, RecordingLayer, request,
)
from apps.shyland.tests.test_mc_egress import make_agent
from apps.shyland.tests.test_new_commands import grant_admin

EXACTLY_ONE = ("Exactly one of 'to_name', 'to_room_id', or 'waypoint' "
               "is required.")


async def move(comm, params, frame_id='m1'):
    return await request(comm, {'type': 'action', 'id': frame_id,
                                'act': 'move', 'params': params})


async def answer(comm, params, frame_id='a1'):
    return await request(comm, {'type': 'action', 'id': frame_id,
                                'act': 'answer', 'params': params})


def teach_waypoint(agent, name, room):
    return AgentMemory.objects.create(
        agent=agent, kind=AgentMemory.KIND_WAYPOINT, name=name,
        data={'room_id': room.pk})


# ----------------------------------------------------------------------
# move: the waypoint destination form (§2)
# ----------------------------------------------------------------------

class MoveWaypointTests(DoorTestBase):

    async def test_waypoint_happy_path_offline(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('wp_ok')
        layer = RecordingLayer()
        async with self.door(agent, FakeDoorClient(), layer) as comm:
            # Teach through the door itself — the verbs compose.
            taught = await request(comm, {
                'type': 'action', 'id': 't1', 'act': 'remember',
                'params': {'kind': 'waypoint', 'name': 'battle',
                           'data': {'room_id': room_b.pk}}})
            self.assertTrue(taught['ok'])
            result = await move(comm, {'name': char.name,
                                       'waypoint': 'battle'})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data']['room']['id'], room_b.pk)
            self.assertEqual(result['data']['from_room']['id'], room_a.pk)
            self.assertEqual(result['data']['waypoint'], 'battle')
        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, room_b.pk)
        # Offline move: DB update + visit only, no broadcasts.
        self.assertEqual(layer.sent, [])

    async def test_waypoint_case_insensitive_returns_stored_casing(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('wp_ci')
        await sync_to_async(teach_waypoint)(agent, 'The Heart', room_b)
        async with self.door(agent) as comm:
            result = await move(comm, {'name': char.name,
                                       'waypoint': 'the heart'})
            self.assertTrue(result['ok'])
            # The row's cased name, not the caller's.
            self.assertEqual(result['data']['waypoint'], 'The Heart')

    async def test_exactly_one_of_three(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('wp_x1')
        await sync_to_async(teach_waypoint)(agent, 'spot', room_b)
        async with self.door(agent) as comm:
            for params in (
                {'name': char.name},
                {'name': char.name, 'to_name': char.name,
                 'to_room_id': room_b.pk},
                {'name': char.name, 'to_name': char.name,
                 'waypoint': 'spot'},
                {'name': char.name, 'to_room_id': room_b.pk,
                 'waypoint': 'spot'},
            ):
                result = await move(comm, params)
                self.assertFalse(result['ok'])
                self.assertEqual(result['error'], 'bad-params')
                self.assertEqual(result['detail'], EXACTLY_ONE)

    async def test_unknown_waypoint_not_found_names_it(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('wp_nf')
        async with self.door(agent) as comm:
            result = await move(comm, {'name': char.name,
                                       'waypoint': 'atlantis'})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'not-found')
            self.assertIn('atlantis', result['detail'])

    async def test_deleted_room_not_found_names_waypoint_and_room(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('wp_del')
        doomed_pk = room_b.pk
        await sync_to_async(teach_waypoint)(agent, 'doomed', room_b)
        await sync_to_async(Room.objects.filter(pk=doomed_pk).delete)()
        async with self.door(agent) as comm:
            result = await move(comm, {'name': char.name,
                                       'waypoint': 'doomed'})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'not-found')
            # The legible-refusal law: both the waypoint and the
            # vanished room id are named.
            self.assertIn('doomed', result['detail'])
            self.assertIn(str(doomed_pk), result['detail'])
        await sync_to_async(char.refresh_from_db)()
        self.assertEqual(char.current_room_id, room_a.pk)

    async def test_cross_agent_isolation(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('wp_iso')
        other = await sync_to_async(make_agent)('wp_iso_b')
        await sync_to_async(teach_waypoint)(other, 'theirs', room_b)
        async with self.door(agent) as comm:
            result = await move(comm, {'name': char.name,
                                       'waypoint': 'theirs'})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'not-found')

    async def test_to_room_id_result_shape_untouched(self):
        # The two prior forms are byte-identical to v25.8 behavior —
        # the broader pins live in DoorMoveTests (untouched); here the
        # result-shape guarantee: no 'waypoint' key unless the waypoint
        # form was used.
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('wp_sh')
        async with self.door(agent) as comm:
            result = await move(comm, {'name': char.name,
                                       'to_room_id': room_b.pk})
            self.assertTrue(result['ok'])
            self.assertNotIn('waypoint', result['data'])
            self.assertEqual(
                set(result['data']), {'room', 'from_room'})


# ----------------------------------------------------------------------
# answer: machinery-only receipts (§3)
# ----------------------------------------------------------------------

class AnswerReceiptsValidationTests(DoorTestBase):

    async def test_receipts_bounds_refused(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('rc_val')
        await sync_to_async(grant_admin)(char)
        async with self.door(agent) as comm:
            for receipts in (
                'gave a thing',            # non-list
                [],                        # empty list
                ['r'] * 21,                # > 20 entries
                ['ok', 7],                 # non-string entry
                ['ok', ''],                # empty string entry
                ['x' * 201],               # > 200 chars
            ):
                result = await answer(comm, {'to': char.name,
                                             'receipts': receipts})
                self.assertFalse(result['ok'])
                self.assertEqual(result['error'], 'bad-params')

    async def test_neither_text_nor_receipts_refused(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('rc_none')
        await sync_to_async(grant_admin)(char)
        async with self.door(agent) as comm:
            result = await answer(comm, {'to': char.name})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            # text-only behavior is unchanged (the v25.5 DoorAnswerTests
            # pin it); the boundary case here: text rules still hold
            # when receipts ride along.
            too_long = await answer(comm, {'to': char.name,
                                           'text': 'x' * 2001,
                                           'receipts': ['did a thing']})
            self.assertFalse(too_long['ok'])
            self.assertEqual(too_long['error'], 'bad-params')


class AnswerReceiptsDeliveryTests(DoorTestBase):

    async def test_text_then_receipts_in_order_all_sudo(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('rc_ok')
        await sync_to_async(grant_admin)(char)
        fake, layer = FakeDoorClient(), RecordingLayer()
        fake.set_online(char)
        async with self.door(agent, fake, layer) as comm:
            result = await answer(comm, {
                'to': char.name, 'text': 'done',
                'receipts': ['moved X from A to B',
                             "remembered waypoint 'battle' (created, id 3)"]})
            self.assertTrue(result['ok'])
            # Result shape unchanged.
            self.assertEqual(result['data'], {'delivered': True})
        self.assertEqual({group for group, _ in layer.sent},
                         {f'player_{char.pk}'})
        texts = [event['text'] for _, event in layer.sent]
        self.assertEqual(texts, [
            'sudo: done',
            'sudo did: moved X from A to B',
            "sudo did: remembered waypoint 'battle' (created, id 3)",
        ])
        for _, event in layer.sent:
            self.assertEqual(event['category'], 'sudo')

    async def test_receipts_only_no_sudo_line(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('rc_only')
        await sync_to_async(grant_admin)(char)
        fake, layer = FakeDoorClient(), RecordingLayer()
        fake.set_online(char)
        async with self.door(agent, fake, layer) as comm:
            result = await answer(comm, {'to': char.name,
                                         'receipts': ['stripped Someone']})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'], {'delivered': True})
        texts = [event['text'] for _, event in layer.sent]
        self.assertEqual(texts, ['sudo did: stripped Someone'])

    async def test_non_admin_refused_offline_silent(self):
        agent, zone, room_a, room_b, char = await sync_to_async(
            self._fixture)('rc_gate')
        layer = RecordingLayer()
        async with self.door(agent, FakeDoorClient(), layer) as comm:
            refused = await answer(comm, {'to': char.name,
                                          'receipts': ['did a thing']})
            self.assertFalse(refused['ok'])
            self.assertEqual(refused['error'], 'not-admin')
            await sync_to_async(grant_admin)(char)
            offline = await answer(comm, {'to': char.name,
                                          'receipts': ['did a thing']})
            self.assertTrue(offline['ok'])
            self.assertEqual(offline['data'], {'delivered': False})
        self.assertEqual(layer.sent, [])
