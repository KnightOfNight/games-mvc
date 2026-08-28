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
from apps.shyland.tests.test_mc_egress import make_agent
from apps.shyland.tests.test_mc_kill_switch import engage_switch


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
