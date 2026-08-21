"""v25.4 brief 1 (#266/#277): the MC kill switch — flip semantics, the
egress gates (connect refuse, replay sever, live sever, fail closed),
the mc admin command with fn-18 stealth, surface wiring, and the
persister/egress block-constant pins (GDD §10.11, §9.1 fn 22).

Socket tests reuse test_mc_egress.py's communicator and fake-client
shapes; command tests reuse test_command_revamp.py's stub consumer."""

from unittest import mock

from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, TransactionTestCase

from apps.shyland import mc_consumer
from apps.shyland.consumers import SkylandConsumer
from apps.shyland.management.commands import run_mc_persister
from apps.shyland.mc_consumer import MC_PROTOCOL, MCEgressConsumer
from apps.shyland.models import MCKillSwitch
from apps.shyland.tests.test_command_revamp import (
    make_character, make_stub_consumer, make_world, outputs,
)
from apps.shyland.tests.test_mc_egress import (
    EgressCommunicator, FakeEgressClient, entry, make_agent,
)
from apps.shyland.tests.test_new_commands import UNKNOWN_LINE, grant_admin

USAGE_LINE = 'Usage: mc <status|kill|restore>'


def engage_switch():
    """Set the row directly — no emit; flip semantics are under test
    elsewhere, and these callers only need the state."""
    MCKillSwitch.objects.update_or_create(pk=1, defaults={'killed': True})


class FlipSemanticsTests(TestCase):
    """§1 rules: absent row = alive; every actual flip emits exactly one
    mc_kill record; a no-change flip emits nothing."""

    def test_default_state_alive_no_row(self):
        self.assertFalse(MCKillSwitch.objects.exists())
        self.assertFalse(MCKillSwitch.is_killed())

    def test_flip_engages_emits_once_and_stamps(self):
        with mock.patch('apps.shyland.mc.mc_emit_sync') as emit:
            changed = MCKillSwitch.flip(True, by='op', surface='shell')
        self.assertTrue(changed)
        row = MCKillSwitch.objects.get(pk=1)
        self.assertTrue(row.killed)
        self.assertIsNotNone(row.flipped_at)
        self.assertEqual(row.flipped_by, 'op')
        self.assertEqual(emit.call_count, 1)
        args, kwargs = emit.call_args
        self.assertEqual(args, ('mc_kill',))
        self.assertEqual(kwargs['actor_name'], 'op')
        self.assertEqual(kwargs['data'],
                         {'killed': True, 'surface': 'shell'})
        self.assertTrue(MCKillSwitch.is_killed())

    def test_no_change_flip_emits_nothing(self):
        with mock.patch('apps.shyland.mc.mc_emit_sync') as emit:
            MCKillSwitch.flip(True, by='op', surface='shell')
            changed = MCKillSwitch.flip(True, by='op2', surface='command')
        self.assertFalse(changed)
        self.assertEqual(emit.call_count, 1)
        # The no-change attempt left the stamps alone.
        self.assertEqual(MCKillSwitch.objects.get(pk=1).flipped_by, 'op')

    def test_restore_emits_again(self):
        with mock.patch('apps.shyland.mc.mc_emit_sync') as emit:
            MCKillSwitch.flip(True, by='op', surface='shell')
            changed = MCKillSwitch.flip(False, by='op', surface='shell')
        self.assertTrue(changed)
        self.assertFalse(MCKillSwitch.is_killed())
        self.assertEqual(emit.call_count, 2)
        self.assertEqual(emit.call_args[1]['data'],
                         {'killed': False, 'surface': 'shell'})

    def test_migration_applied_table_exists(self):
        # §9.8: an explicit touch proves 0052 ran in the test DB build.
        self.assertEqual(MCKillSwitch.objects.count(), 0)


class EgressConnectGateTests(TransactionTestCase):
    """§5.2: killed = refused 4503; membership is checked first, so the
    switch leaks nothing to non-members; any read failure = killed."""

    async def _connect_outcome(self, user):
        comm = WebsocketCommunicator(
            MCEgressConsumer.as_asgi(), '/ws/shyland/mc/')
        comm.scope['user'] = user
        connected, _ = await comm.connect()
        self.assertTrue(connected)
        message = await comm.receive_output(timeout=10)
        await comm.disconnect()
        return message

    async def test_member_engaged_switch_closed_4503(self):
        user = await sync_to_async(make_agent)('ks_gate')
        await sync_to_async(engage_switch)()
        message = await self._connect_outcome(user)
        self.assertEqual(message['type'], 'websocket.close')
        self.assertEqual(message['code'], 4503)

    async def test_member_alive_switch_gets_hello(self):
        user = await sync_to_async(make_agent)('ks_alive')
        async with EgressCommunicator(user, FakeEgressClient()) as comm:
            hello = await comm.receive_json_from(timeout=10)
            self.assertEqual(hello, {'type': 'hello',
                                     'protocol': MC_PROTOCOL})

    async def test_non_member_engaged_switch_still_4403(self):
        user = await sync_to_async(User.objects.create_user)(
            username='ks_nonmember', password='x')
        await sync_to_async(engage_switch)()
        message = await self._connect_outcome(user)
        self.assertEqual(message['type'], 'websocket.close')
        self.assertEqual(message['code'], 4403)

    async def test_read_failure_fails_closed_4503(self):
        user = await sync_to_async(make_agent)('ks_fail')
        with mock.patch.object(MCKillSwitch, 'is_killed',
                               side_effect=Exception('db down')):
            message = await self._connect_outcome(user)
        self.assertEqual(message['type'], 'websocket.close')
        self.assertEqual(message['code'], 4503)


class EgressSeverTests(TransactionTestCase):
    """§5.3/§5.4: an attached connection is severed on the next stream
    wake; a kill during replay severs per batch."""

    async def test_live_sever_on_next_wake(self):
        user = await sync_to_async(make_agent)('ks_live')
        fake = FakeEgressClient(window=[entry('5-1')])
        async with EgressCommunicator(user, fake) as comm:
            await comm.receive_json_from(timeout=10)  # hello
            await comm.send_json_to({'type': 'attach'})
            await sync_to_async(engage_switch)()
            # Wake the loop if it was already blocked in XREAD. The
            # sever may land before or after the fed entry delivers
            # (the engage races the loop's first top-of-iteration
            # check) — the guarantee is the close, within one wake.
            fake.feed(entry('6-1'))
            while True:
                message = await comm.receive_output(timeout=10)
                if message['type'] == 'websocket.close':
                    break
            self.assertEqual(message['code'], 4503)

    async def test_replay_sever_before_any_batch(self):
        user = await sync_to_async(make_agent)('ks_replay')
        fake = FakeEgressClient(window=[entry('5-1'), entry('6-1')])
        async with EgressCommunicator(user, fake) as comm:
            await comm.receive_json_from(timeout=10)  # hello
            await sync_to_async(engage_switch)()
            await comm.send_json_to({'type': 'attach', 'after': '5-1'})
            message = await comm.receive_output(timeout=10)
            self.assertEqual(message['type'], 'websocket.close')
            self.assertEqual(message['code'], 4503)


class CmdMcStealthTests(TransactionTestCase):
    """§6: for non-members mc does not exist — the fn-18 machinery,
    byte-identical to the unknown-command response."""

    async def test_non_member_mc_byte_identical_to_unknown(self):
        zone, room = await sync_to_async(make_world)('ksA')
        char = await sync_to_async(make_character)('ksA', room)

        async def response_for(text):
            sent = []
            consumer = make_stub_consumer(char, sent)
            await consumer.receive_json({'text': text})
            return [m for m in outputs(sent) if m['category'] != 'echo']

        gibberish = await response_for('frobnicate')
        for attempt in ('mc status', 'mc kill', 'mc'):
            got = await response_for(attempt)
            self.assertEqual(len(got), 1, attempt)
            self.assertEqual(got[0]['text'], gibberish[0]['text'])
            self.assertEqual(got[0]['category'], gibberish[0]['category'])
            self.assertEqual(got[0]['text'], UNKNOWN_LINE)


class CmdMcTests(TransactionTestCase):
    """§6: the member surface — usage line, status rendering, flip
    voices, no-change warns, prefix matching."""

    async def _admin_consumer(self, prefix, sent):
        zone, room = await sync_to_async(make_world)(prefix)
        char = await sync_to_async(make_character)(prefix, room)
        await sync_to_async(grant_admin)(char)
        return make_stub_consumer(char, sent)

    async def test_bare_and_bogus_draw_usage_error(self):
        sent = []
        consumer = await self._admin_consumer('ksB', sent)
        await consumer._dispatch('mc', '')
        await consumer._dispatch('mc', 'bogus')
        msgs = outputs(sent)
        self.assertEqual([m['text'] for m in msgs],
                         [USAGE_LINE, USAGE_LINE])
        self.assertTrue(all(m['category'] == 'error' for m in msgs))

    async def test_status_both_states(self):
        sent = []
        consumer = await self._admin_consumer('ksC', sent)
        await consumer._dispatch('mc', 'status')
        await sync_to_async(engage_switch)()
        await consumer._dispatch('mc', 'status')
        reports = [m for m in sent if m.get('category') == 'report']
        self.assertEqual(len(reports), 2)
        self.assertEqual(reports[0]['lines'], [
            {'k': 'MC kill switch:',
             'v': ' not engaged — AI actors may act.'}])
        self.assertEqual(reports[1]['lines'], [
            {'k': 'MC kill switch:',
             'v': ' engaged — all AI actors are silenced.'}])

    async def test_kill_restore_flip_voices_and_emits(self):
        sent = []
        consumer = await self._admin_consumer('ksD', sent)
        with mock.patch('apps.shyland.mc.mc_emit_sync') as emit:
            await consumer._dispatch('mc', 'kill')
            await consumer._dispatch('mc', 'kill')
            await consumer._dispatch('mc', 'restore')
            await consumer._dispatch('mc', 'restore')
        msgs = outputs(sent)
        self.assertEqual([(m['text'], m['category']) for m in msgs], [
            ('MC kill switch engaged. All AI actors are silenced.',
             'success'),
            ('The kill switch is already engaged.', 'warn'),
            ('MC kill switch released. AI actors may act again.',
             'success'),
            ('The kill switch is not engaged.', 'warn'),
        ])
        # Two actual flips, two emits — the no-change attempts are
        # silent on the stream.
        self.assertEqual(emit.call_count, 2)
        surfaces = [c[1]['data']['surface'] for c in emit.call_args_list]
        self.assertEqual(surfaces, ['command', 'command'])
        actor = consumer.character
        self.assertEqual(emit.call_args_list[0][1]['actor_name'],
                         actor.name)
        self.assertEqual(emit.call_args_list[0][1]['actor_id'], actor.pk)

    async def test_prefix_matching_mc_k(self):
        sent = []
        consumer = await self._admin_consumer('ksE', sent)
        with mock.patch('apps.shyland.mc.mc_emit_sync'):
            await consumer._dispatch('mc', 'k')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['text'],
                         'MC kill switch engaged. All AI actors are silenced.')
        self.assertTrue(await sync_to_async(MCKillSwitch.is_killed)())


class SurfaceWiringTests(TransactionTestCase):
    """§6 touch points: tables, help stealth, completion gating."""

    def test_tables_carry_mc(self):
        self.assertIn('mc', SkylandConsumer.COMMAND_TABLE)
        self.assertEqual(SkylandConsumer.COMMAND_TABLE['mc'],
                         ('cmd_mc', True))
        self.assertIn('mc', SkylandConsumer.ADMIN_VERBS)
        self.assertIn('mc', SkylandConsumer.DYING_ALLOWED)
        self.assertNotIn('mc', SkylandConsumer.COMBAT_BLOCKED)

    async def test_help_row_member_only(self):
        zone, room = await sync_to_async(make_world)('ksF')
        char = await sync_to_async(make_character)('ksF', room)

        async def help_text(c):
            sent = []
            consumer = make_stub_consumer(c, sent)
            await consumer.cmd_help()
            report = next(m for m in sent if m.get('category') == 'report')
            out = []
            for line in report['lines']:
                if 'segs' in line:
                    out.append(''.join(seg['t'] for seg in line['segs']))
                else:
                    out.append((line.get('k', '') or '')
                               + (line.get('v', '') or ''))
            return '\n'.join(out)

        text = await help_text(char)
        self.assertNotIn('The MC kill switch.', text)
        await sync_to_async(grant_admin)(char)
        text = await help_text(char)
        self.assertIn('The MC kill switch.', text)
        self.assertIn('mc <status|kill|restore>', text)

    async def _complete(self, char, line):
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.handle_complete(line)
        return next(m for m in sent if m.get('type') == 'complete')['options']

    async def test_completion_member_only(self):
        zone, room = await sync_to_async(make_world)('ksG')
        char = await sync_to_async(make_character)('ksG', room)
        self.assertEqual(await self._complete(char, 'mc '), [])
        await sync_to_async(grant_admin)(char)
        self.assertEqual(await self._complete(char, 'mc '),
                         ['kill', 'restore', 'status'])
        self.assertEqual(await self._complete(char, 'mc k'), ['kill'])


class BlockConstantPinTests(SimpleTestCase):
    """#277: every blocking stream read must sit comfortably inside the
    client's socket_timeout — redis-py >= 8 defaults it to 5s, and a
    server-side BLOCK equal to the client read cap is a coin-flip race
    every idle cycle. Both constants pin at 2000ms, asserted < 5000."""

    def test_persister_block_ms(self):
        self.assertEqual(run_mc_persister.BLOCK_MS, 2000)
        self.assertLess(run_mc_persister.BLOCK_MS, 5000)

    def test_egress_live_block_ms(self):
        self.assertEqual(mc_consumer.LIVE_BLOCK_MS, 2000)
        self.assertLess(mc_consumer.LIVE_BLOCK_MS, 5000)
