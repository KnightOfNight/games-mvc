"""v25.10 brief 1 (#301/#304/#305/#306): truthful delivery and the
filing bot — game-side coverage.

§5: the egress attach singleton (one agent account = one attached
connection; hard reject, close 4409; in-process ``ATTACHED`` registry
with guarded release). §6: the report family grows — kinds
``waypoints``/``memories``/``memory`` join ``inventory``, door-composed
from live store data.

Socket tests drive the real MCEgressConsumer over the established
egress/door fixtures (test_mc_egress.py / test_mc_agent_door.py)."""

from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TransactionTestCase

from apps.shyland import mc_consumer
from apps.shyland.mc_consumer import MC_PROTOCOL, MCEgressConsumer
from apps.shyland.models import AgentMemory
from apps.shyland.tests.test_mc_agent_door import (
    DoorTestBase, FakeDoorClient, RecordingLayer, make_equippable, request,
)
from apps.shyland.tests.test_mc_egress import make_agent
from apps.shyland.tests.test_mc_kill_switch import engage_switch
from apps.shyland.tests.test_new_commands import grant_admin
from apps.shyland.tests.test_room_visits import make_character


async def report(comm, params, frame_id='1'):
    return await request(comm, {'type': 'action', 'id': frame_id,
                                'act': 'report', 'params': params})


async def bare_connect(user):
    """One raw communicator, connected — no hello assertion (the
    outcome under test differs per scenario). Caller disconnects."""
    comm = WebsocketCommunicator(
        MCEgressConsumer.as_asgi(), '/ws/shyland/mc/')
    comm.scope['user'] = user
    connected, _ = await comm.connect()
    assert connected
    return comm


async def expect_hello(comm):
    hello = await comm.receive_json_from(timeout=10)
    assert hello == {'type': 'hello', 'protocol': MC_PROTOCOL}


async def expect_close(comm, code):
    message = await comm.receive_output(timeout=10)
    assert message['type'] == 'websocket.close', message
    assert message['code'] == code, message


class AttachSingletonTests(TransactionTestCase):
    """§5 (#304): one agent account = one attached connection."""

    def setUp(self):
        # The module-level registry survives across tests in-process by
        # design; tests start from a clean slate.
        mc_consumer.ATTACHED.clear()
        self.addCleanup(mc_consumer.ATTACHED.clear)

    async def test_duplicate_account_refused_4409(self):
        agent = await sync_to_async(make_agent)('single_dup')
        holder = await bare_connect(agent)
        await expect_hello(holder)
        dup = await bare_connect(agent)
        error = await dup.receive_json_from(timeout=10)
        self.assertEqual(error, {
            'type': 'error', 'error': 'already-attached',
            'detail': (f'Another connection for {agent.username} '
                       f'is already attached.')})
        await expect_close(dup, 4409)
        await dup.disconnect()
        await holder.disconnect()

    async def test_slot_freed_on_disconnect_then_admitted(self):
        agent = await sync_to_async(make_agent)('single_free')
        holder = await bare_connect(agent)
        await expect_hello(holder)
        await holder.disconnect()
        again = await bare_connect(agent)
        await expect_hello(again)
        await again.disconnect()

    async def test_two_different_accounts_both_admitted(self):
        agent_a = await sync_to_async(make_agent)('single_a')
        agent_b = await sync_to_async(make_agent)('single_b')
        comm_a = await bare_connect(agent_a)
        await expect_hello(comm_a)
        comm_b = await bare_connect(agent_b)
        await expect_hello(comm_b)
        await comm_b.disconnect()
        await comm_a.disconnect()

    async def test_rejected_duplicate_does_not_free_holder_claim(self):
        agent = await sync_to_async(make_agent)('single_guard')
        holder = await bare_connect(agent)
        await expect_hello(holder)
        dup = await bare_connect(agent)
        await dup.receive_json_from(timeout=10)  # error frame
        await expect_close(dup, 4409)
        await dup.disconnect()
        # The rejected attempt's teardown must not disturb the claim:
        # a third attempt while the holder lives is still refused.
        third = await bare_connect(agent)
        error = await third.receive_json_from(timeout=10)
        self.assertEqual(error['error'], 'already-attached')
        await expect_close(third, 4409)
        await third.disconnect()
        await holder.disconnect()

    async def test_killed_switch_precedes_conflict_4503(self):
        agent = await sync_to_async(make_agent)('single_kill')
        holder = await bare_connect(agent)
        await expect_hello(holder)
        await sync_to_async(engage_switch)()
        # A killed door reports killed, not conflict.
        dup = await bare_connect(agent)
        await expect_close(dup, 4503)
        await dup.disconnect()
        await holder.disconnect()

    async def test_membership_precedes_singleton_4403(self):
        user = await sync_to_async(User.objects.create_user)(
            username='single_nonmember', password='x')
        # Artificially seed the registry with this username: no real
        # non-member can ever claim, but the gate order (membership
        # before singleton — the leak law) must hold regardless.
        mc_consumer.ATTACHED[user.username] = 'occupied!fake'
        comm = await bare_connect(user)
        await expect_close(comm, 4403)
        await comm.disconnect()
        # 4403 never releases a claim it never held.
        self.assertEqual(mc_consumer.ATTACHED[user.username],
                         'occupied!fake')


# ----------------------------------------------------------------------
# §6 (#306): the report family grows
# ----------------------------------------------------------------------

class ReportFamilyTests(DoorTestBase):

    def _report_fixture(self, prefix):
        agent, zone, room_a, room_b, char = self._fixture(prefix)
        admin = make_character(f'{prefix}_adm', room_a)
        grant_admin(admin)
        return agent, zone, room_a, room_b, char, admin

    def _teach(self, agent, kind, name, data, taught_by=None):
        return AgentMemory.objects.create(
            agent=agent, kind=kind, name=name, data=data,
            taught_by=taught_by)

    async def test_unknown_kind_names_all_four(self):
        (agent, zone, room_a, room_b, char,
         admin) = await sync_to_async(self._report_fixture)('repf_uk')
        async with self.door(agent) as comm:
            result = await report(comm, {'to': admin.name,
                                         'kind': 'wallet'})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'bad-params')
            for kind in ('inventory', 'waypoints', 'memories', 'memory'):
                self.assertIn(kind, result['detail'])

    async def test_waypoints_empty_store_leader_alone(self):
        (agent, zone, room_a, room_b, char,
         admin) = await sync_to_async(self._report_fixture)('repf_e')
        fake, layer = FakeDoorClient(), RecordingLayer()
        fake.set_online(admin)
        async with self.door(agent, fake, layer) as comm:
            result = await report(comm, {'to': admin.name,
                                         'kind': 'waypoints'})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'],
                             {'delivered': True, 'count': 0})
        # The leader alone is the report — no lines frame.
        events = [event for _, event in layer.sent]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['text'], 'sudo: 0 waypoints')
        self.assertEqual(events[0]['category'], 'sudo')

    async def test_waypoints_rows_with_dangling_room(self):
        (agent, zone, room_a, room_b, char,
         admin) = await sync_to_async(self._report_fixture)('repf_wp')
        older = await sync_to_async(self._teach)(
            agent, AgentMemory.KIND_WAYPOINT, 'battle',
            {'room_id': room_b.pk})
        dangling = await sync_to_async(self._teach)(
            agent, AgentMemory.KIND_WAYPOINT, 'lost',
            {'room_id': 999999})
        fake, layer = FakeDoorClient(), RecordingLayer()
        fake.set_online(admin)
        async with self.door(agent, fake, layer) as comm:
            result = await report(comm, {'to': admin.name,
                                         'kind': 'waypoints'})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'],
                             {'delivered': True, 'count': 2})
        events = [event for _, event in layer.sent]
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]['text'], 'sudo: 2 waypoints')
        self.assertEqual(events[1]['category'], 'report')
        # Newest first; live path; dangling row tells the truth. Rows
        # ride the client report-lines contract as value-voice dicts.
        self.assertEqual(events[1]['lines'], [
            {'v': f'#{dangling.pk} lost — (room no longer exists)'},
            {'v': f'#{older.pk} battle — {zone.name}: {room_b.name}'},
        ])

    async def test_memories_mixed_kinds_both_summary_forms(self):
        (agent, zone, room_a, room_b, char,
         admin) = await sync_to_async(self._report_fixture)('repf_mx')
        sword = await sync_to_async(make_equippable)(
            'repf_mx', 'Mixed Sword', 'weapon', ['MAIN_HAND'])
        waypoint = await sync_to_async(self._teach)(
            agent, AgentMemory.KIND_WAYPOINT, 'battle',
            {'room_id': room_b.pk})
        bundle = await sync_to_async(self._teach)(
            agent, AgentMemory.KIND_BUNDLE, 'kit',
            {'lines': [[sword.slug, 1, 'common', 2]]})
        fake, layer = FakeDoorClient(), RecordingLayer()
        fake.set_online(admin)
        async with self.door(agent, fake, layer) as comm:
            result = await report(comm, {'to': admin.name,
                                         'kind': 'memories'})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'],
                             {'delivered': True, 'count': 2})
        events = [event for _, event in layer.sent]
        self.assertEqual(events[0]['text'], 'sudo: 2 memories')
        self.assertEqual(events[1]['lines'], [
            {'v': f'#{bundle.pk} bundle kit — 1 lines'},
            {'v': f'#{waypoint.pk} waypoint battle — '
                  f'{zone.name}: {room_b.name}'},
        ])

    async def test_memory_detail_waypoint_and_bundle(self):
        (agent, zone, room_a, room_b, char,
         admin) = await sync_to_async(self._report_fixture)('repf_d')
        sword = await sync_to_async(make_equippable)(
            'repf_d', 'Detail Sword', 'weapon', ['MAIN_HAND'])
        waypoint = await sync_to_async(self._teach)(
            agent, AgentMemory.KIND_WAYPOINT, 'battle',
            {'room_id': room_b.pk}, taught_by=char.user)
        bundle = await sync_to_async(self._teach)(
            agent, AgentMemory.KIND_BUNDLE, 'kit',
            {'lines': [[sword.slug, 1, 'common', 2]]})
        fake, layer = FakeDoorClient(), RecordingLayer()
        fake.set_online(admin)
        async with self.door(agent, fake, layer) as comm:
            result = await report(comm, {'to': admin.name,
                                         'kind': 'memory',
                                         'id': waypoint.pk})
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'],
                             {'delivered': True, 'id': waypoint.pk})
            result = await report(comm, {'to': admin.name,
                                         'kind': 'memory',
                                         'id': bundle.pk}, frame_id='2')
            self.assertTrue(result['ok'])
            self.assertEqual(result['data'],
                             {'delivered': True, 'id': bundle.pk})
        events = [event for _, event in layer.sent]
        self.assertEqual(len(events), 4)
        self.assertEqual(events[0]['text'],
                         f"sudo: waypoint 'battle' (id {waypoint.pk})")
        self.assertEqual(events[0]['category'], 'sudo')
        self.assertEqual(events[1]['lines'], [
            {'v': f'where: {zone.name}: {room_b.name}'},
            {'v': f'taught by {char.user.username}'},
            {'v': f'created {waypoint.created_at.isoformat()} / '
                  f'updated {waypoint.updated_at.isoformat()}'},
        ])
        self.assertEqual(events[2]['text'],
                         f"sudo: bundle 'kit' (id {bundle.pk})")
        self.assertEqual(events[3]['lines'], [
            {'v': f'2× {sword.slug} Mk 1 common'},
            {'v': 'taught by (unknown)'},
            {'v': f'created {bundle.created_at.isoformat()} / '
                  f'updated {bundle.updated_at.isoformat()}'},
        ])

    async def test_memory_unknown_id_not_found(self):
        (agent, zone, room_a, room_b, char,
         admin) = await sync_to_async(self._report_fixture)('repf_nf')
        async with self.door(agent) as comm:
            result = await report(comm, {'to': admin.name,
                                         'kind': 'memory', 'id': 999999})
            self.assertFalse(result['ok'])
            self.assertEqual(result['error'], 'not-found')

    async def test_agent_scoping_never_leaks_other_store(self):
        (agent_a, zone, room_a, room_b, char,
         admin) = await sync_to_async(self._report_fixture)('repf_sa')
        agent_b = await sync_to_async(make_agent)('repf_sb')
        row = await sync_to_async(self._teach)(
            agent_a, AgentMemory.KIND_WAYPOINT, 'battle',
            {'room_id': room_b.pk})
        fake, layer = FakeDoorClient(), RecordingLayer()
        fake.set_online(admin)
        async with self.door(agent_b, fake, layer) as comm:
            listing = await report(comm, {'to': admin.name,
                                          'kind': 'waypoints'})
            self.assertEqual(listing['data'],
                             {'delivered': True, 'count': 0})
            detail = await report(comm, {'to': admin.name,
                                         'kind': 'memory',
                                         'id': row.pk}, frame_id='2')
            self.assertFalse(detail['ok'])
            self.assertEqual(detail['error'], 'not-found')

    async def test_non_admin_refused_and_offline_sends_nothing(self):
        (agent, zone, room_a, room_b, char,
         admin) = await sync_to_async(self._report_fixture)('repf_na')
        fake, layer = FakeDoorClient(), RecordingLayer()
        async with self.door(agent, fake, layer) as comm:
            refused = await report(comm, {'to': char.name,
                                          'kind': 'waypoints'})
            self.assertFalse(refused['ok'])
            self.assertEqual(refused['error'], 'not-admin')
            # Offline admin: ok true, delivered false, nothing sent.
            offline = await report(comm, {'to': admin.name,
                                          'kind': 'memories'},
                                   frame_id='2')
            self.assertTrue(offline['ok'])
            self.assertEqual(offline['data'],
                             {'delivered': False, 'count': 0})
        self.assertEqual(layer.sent, [])
