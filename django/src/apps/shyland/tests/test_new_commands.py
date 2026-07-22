"""v22 brief 3 (B3): home (#57), cancel (#113), last (#88), sudo (#112).

Stealth gating byte-identity and live revocation; the delayed-action
registry; home's countdown, interruptions, completion-only cooldown; and
last's three time forms and ordering."""

import asyncio
from datetime import timedelta

from asgiref.sync import sync_to_async
from django.contrib.auth.models import Group
from django.test import TransactionTestCase
from django.utils import timezone

from apps.shyland.consumers import SkylandConsumer
from apps.shyland.models import (
    Character, CombatSession, NpcDefinition, NpcInstance, Room, RoomVisit,
    TravelNode, Zone,
)
from apps.shyland.tests.test_command_revamp import (
    make_character, make_stub_consumer, make_world, outputs,
)

UNKNOWN_LINE = "Unknown command. Type 'help' for a list of commands."


class FakeRedis:
    def __init__(self, online_pks=()):
        self.online_pks = list(online_pks)

    async def keys(self, pattern):
        return [f'shyland:online:{pk}'.encode() for pk in self.online_pks]

    async def mget(self, *keys):
        return [b'{}' for _ in keys]


def make_home_world(prefix):
    """A heart room (with the Convergence obelisk node) and a far room."""
    zone, far_room = make_world(prefix)
    heart = Room.objects.create(
        zone=zone, name=f'{prefix} Heart', description='Long.',
        brief_description='Brief.', coord_x=5, coord_y=5,
    )
    TravelNode.objects.create(
        room=heart, travel_name='The Convergence', node_type='obelisk',
        listing_description='At the center of everything stands the Obelisk.',
    )
    char = make_character(prefix, far_room)
    return char, far_room, heart


def quiet_home_consumer(char, sent):
    """Stub consumer with instant cadence and render/map no-ops (the
    render path needs Redis; relocation state is what's under test)."""
    consumer = make_stub_consumer(char, sent)
    consumer.HOME_CADENCE = (0, 0, 0)

    async def noop(*args, **kwargs):
        return None
    consumer.send_room_description = noop
    consumer.send_map = noop
    return consumer


def grant_admin(char):
    # get_or_create mirrors the idempotent 0034 data migration —
    # TransactionTestCase truncation wipes RunPython data between tests.
    group, _ = Group.objects.get_or_create(name='admins.shyland')
    char.user.groups.add(group)


class StealthGatingTests(TransactionTestCase):

    async def test_non_member_responses_byte_identical_to_unknown(self):
        zone, room = await sync_to_async(make_world)('sgA')
        char = await sync_to_async(make_character)('sgA', room)

        async def response_for(text):
            sent = []
            consumer = make_stub_consumer(char, sent)
            await consumer.receive_json({'text': text})
            return [m for m in outputs(sent) if m['category'] != 'echo']

        gibberish = await response_for('frobnicate')
        for attempt in ('sudo hello', 'last'):
            got = await response_for(attempt)
            self.assertEqual(len(got), 1, attempt)
            self.assertEqual(got[0]['text'], gibberish[0]['text'])
            self.assertEqual(got[0]['category'], gibberish[0]['category'])
            self.assertEqual(got[0]['text'], UNKNOWN_LINE)

    async def test_member_passes_and_revocation_is_live(self):
        zone, room = await sync_to_async(make_world)('sgB')
        char = await sync_to_async(make_character)('sgB', room)
        await sync_to_async(grant_admin)(char)

        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer._dispatch('sudo', 'hello watcher')
        # Member sudo: the game never responds.
        self.assertEqual(outputs(sent), [])

        def revoke():
            char.user.groups.clear()
        await sync_to_async(revoke)()

        sent2 = []
        consumer2 = make_stub_consumer(char, sent2)
        await consumer2._dispatch('sudo', 'hello again')
        msgs = outputs(sent2)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], UNKNOWN_LINE)

    async def test_help_admin_rows_member_only(self):
        zone, room = await sync_to_async(make_world)('sgC')
        char = await sync_to_async(make_character)('sgC', room)

        async def help_text(c):
            sent = []
            consumer = make_stub_consumer(c, sent)
            await consumer.cmd_help()
            report = next(m for m in sent if m.get('category') == 'report')
            out = []
            for entry in report['lines']:
                if 'segs' in entry:
                    out.append(''.join(seg['t'] for seg in entry['segs']))
                else:
                    out.append((entry.get('k', '') or '') + (entry.get('v', '') or ''))
            return '\n'.join(out)

        text = await help_text(char)
        self.assertNotIn('sudo', text)
        self.assertNotIn('Show characters and when they were last seen.', text)
        self.assertIn('Return home after a short delay.', text)
        self.assertIn('Stop an in-progress command.', text)

        await sync_to_async(grant_admin)(char)
        text = await help_text(char)
        self.assertIn('Speak to the watcher.', text)
        self.assertIn('Show characters and when they were last seen.', text)


class CancelTests(TransactionTestCase):

    async def test_bare_cancel_with_nothing_running(self):
        zone, room = await sync_to_async(make_world)('cnA')
        char = await sync_to_async(make_character)('cnA', room)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_cancel('')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['text'], "You don't have anything to cancel.")
        self.assertEqual(msgs[0]['category'], 'warn')

    async def test_cancel_home_bare_and_named_and_in_combat(self):
        char, far_room, heart = await sync_to_async(make_home_world)('cnB')

        # In combat: cancel still works (the escape hatch is never locked).
        def combat():
            definition = NpcDefinition.objects.create(
                name='cnB snarler', slug='cnb-snarler', description='x',
                genre_tag='fantasy', base_vitality=10, base_str=1,
                base_dex=1, base_end=1, base_int=1, base_wis=1, base_per=1,
            )
            npc = NpcInstance.objects.create(
                definition=definition, current_room=far_room,
                spawn_room=far_room, vitality_current=10, vitality_max=10,
            )
            session = CombatSession.objects.create(
                room=far_room, last_tick_at=timezone.now())
            session.characters.add(char)
            session.npcs.add(npc)
        await sync_to_async(combat)()

        sent = []
        consumer = quiet_home_consumer(char, sent)

        async def never_finish():
            await asyncio.sleep(3600)
        task = asyncio.ensure_future(never_finish())
        consumer.delayed_actions['home'] = task

        await consumer.receive_json({'text': 'cancel home'})
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn('You stop heading home.', texts)
        self.assertNotIn('home', consumer.delayed_actions)
        await asyncio.sleep(0)
        self.assertTrue(task.cancelled() or task.done())


class HomeTests(TransactionTestCase):

    async def test_refusals(self):
        char, far_room, heart = await sync_to_async(make_home_world)('hmA')

        # At the Heart.
        def move_to_heart():
            Character.objects.filter(pk=char.pk).update(current_room=heart)
            char.current_room = heart
            char.current_room_id = heart.pk
        await sync_to_async(move_to_heart)()
        sent = []
        consumer = quiet_home_consumer(char, sent)
        await consumer.cmd_home()
        self.assertEqual(outputs(sent)[0]['text'], 'You are already home.')
        self.assertEqual(outputs(sent)[0]['category'], 'warn')

        # Already counting down.
        def move_back():
            Character.objects.filter(pk=char.pk).update(current_room=far_room)
            char.current_room = far_room
            char.current_room_id = far_room.pk
        await sync_to_async(move_back)()
        sent2 = []
        consumer2 = quiet_home_consumer(char, sent2)

        async def never_finish():
            await asyncio.sleep(3600)
        task = asyncio.ensure_future(never_finish())
        consumer2.delayed_actions['home'] = task
        await consumer2.cmd_home()
        self.assertEqual(outputs(sent2)[0]['text'], 'You are already heading home.')
        task.cancel()

    async def test_cooldown_math_minutes_and_seconds(self):
        char, far_room, heart = await sync_to_async(make_home_world)('hmB')

        def set_cooldown(seconds_ago, cooldown):
            Character.objects.filter(pk=char.pk).update(
                home_last_completed=timezone.now() - timedelta(seconds=seconds_ago),
                home_cooldown_seconds=cooldown,
            )
        # 900s cooldown, 300s elapsed -> 10m remaining.
        await sync_to_async(set_cooldown)(300, 900)
        sent = []
        consumer = quiet_home_consumer(char, sent)
        await consumer.cmd_home()
        msg = outputs(sent)[0]
        self.assertEqual(msg['category'], 'warn')
        self.assertIn('(10m cooldown rem.)', msg['text'])

        # 900s cooldown, 855s elapsed -> 45s remaining.
        await sync_to_async(set_cooldown)(855, 900)
        sent2 = []
        consumer2 = quiet_home_consumer(char, sent2)
        await consumer2.cmd_home()
        self.assertIn('s cooldown rem.)', outputs(sent2)[0]['text'])
        self.assertNotIn('m cooldown', outputs(sent2)[0]['text'])

        # Override honored: cooldown 0 -> immediate reuse (countdown starts).
        await sync_to_async(set_cooldown)(1, 0)
        sent3 = []
        consumer3 = quiet_home_consumer(char, sent3)
        await consumer3.cmd_home()
        self.assertIn('home', consumer3.delayed_actions)
        await consumer3.delayed_actions['home']

    async def test_completion_relocates_and_sets_cooldown(self):
        char, far_room, heart = await sync_to_async(make_home_world)('hmC')
        sent = []
        consumer = quiet_home_consumer(char, sent)
        await consumer.cmd_home()
        self.assertIn('home', consumer.delayed_actions)
        await consumer.delayed_actions['home']

        texts = [m['text'] for m in outputs(sent)]
        self.assertEqual(texts[0], consumer.HOME_START_LINE)
        self.assertIn(consumer.HOME_ARRIVAL_LINE, texts)

        def state():
            fresh = Character.objects.get(pk=char.pk)
            visited = RoomVisit.objects.filter(
                character=char, room=heart).exists()
            return fresh.current_room_id, fresh.home_last_completed, visited
        room_id, completed, visited = await sync_to_async(state)()
        self.assertEqual(room_id, heart.pk)
        self.assertIsNotNone(completed)
        self.assertTrue(visited)
        # Witness lines went to the room groups.
        witness_texts = [e['text'] for _, e in consumer.channel_layer.events
                         if e.get('type') == 'room_message']
        self.assertTrue(any('fades into a fog' in t for t in witness_texts))
        self.assertTrue(any('steps out of it' in t for t in witness_texts))

    async def test_movement_auto_cancels_and_move_proceeds(self):
        char, far_room, heart = await sync_to_async(make_home_world)('hmD')

        def link_rooms():
            east = Room.objects.create(
                zone=far_room.zone, name='hmD East', description='Long.',
                brief_description='Brief.', coord_x=1, coord_y=0,
            )
            far_room.exit_east = east
            far_room.save(update_fields=['exit_east'])
            return east
        east = await sync_to_async(link_rooms)()

        sent = []
        consumer = quiet_home_consumer(char, sent)
        await consumer.cmd_home()
        self.assertIn('home', consumer.delayed_actions)

        await consumer._dispatch('east', '')
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn(consumer.HOME_MOVE_CANCEL_LINE, texts)
        self.assertNotIn('home', consumer.delayed_actions)

        def state():
            fresh = Character.objects.get(pk=char.pk)
            return fresh.current_room_id, fresh.home_last_completed
        room_id, completed = await sync_to_async(state)()
        self.assertEqual(room_id, east.pk)      # the move proceeded
        self.assertIsNone(completed)            # no cooldown consumed

    async def test_combat_entry_interrupts_violently_no_cooldown(self):
        char, far_room, heart = await sync_to_async(make_home_world)('hmE')

        def engage():
            definition = NpcDefinition.objects.create(
                name='hmE snarler', slug='hme-snarler', description='x',
                genre_tag='fantasy', base_vitality=10, base_str=1,
                base_dex=1, base_end=1, base_int=1, base_wis=1, base_per=1,
            )
            npc = NpcInstance.objects.create(
                definition=definition, current_room=far_room,
                spawn_room=far_room, vitality_current=10, vitality_max=10,
            )
            session = CombatSession.objects.create(
                room=far_room, last_tick_at=timezone.now())
            session.characters.add(char)
            session.npcs.add(npc)
        # Engine-side combat entry mid-countdown: caught at a beat's
        # checkpoint — the violent line, no relocation, no cooldown.
        sent = []
        consumer = quiet_home_consumer(char, sent)
        await consumer.cmd_home()
        await sync_to_async(engage)()
        await consumer.delayed_actions['home']

        texts = [m['text'] for m in outputs(sent)]
        self.assertIn(consumer.HOME_VIOLENT_LINE, texts)
        self.assertNotIn(consumer.HOME_ARRIVAL_LINE, texts)

        def state():
            fresh = Character.objects.get(pk=char.pk)
            return fresh.current_room_id, fresh.home_last_completed
        room_id, completed = await sync_to_async(state)()
        self.assertEqual(room_id, far_room.pk)
        self.assertIsNone(completed)

    async def test_disconnect_kills_countdown_silently(self):
        char, far_room, heart = await sync_to_async(make_home_world)('hmF')
        sent = []
        consumer = quiet_home_consumer(char, sent)
        consumer.HOME_CADENCE = (3600, 0, 0)
        await consumer.cmd_home()
        task = consumer.delayed_actions['home']
        before = len(outputs(sent))

        # The disconnect path: every delayed task dies silently.
        for t in list(consumer.delayed_actions.values()):
            t.cancel()
        consumer.delayed_actions.clear()
        await asyncio.sleep(0)

        self.assertEqual(len(outputs(sent)), before)   # no new line

        def state():
            fresh = Character.objects.get(pk=char.pk)
            return fresh.current_room_id, fresh.home_last_completed
        room_id, completed = await sync_to_async(state)()
        self.assertEqual(room_id, far_room.pk)
        self.assertIsNone(completed)


class LastTests(TransactionTestCase):

    async def test_forms_ordering_and_composite(self):
        zone, room = await sync_to_async(make_world)('lsA')

        def setup():
            admin = make_character('lsA', room)
            grant_admin(admin)
            now = timezone.now()
            online = make_character('lsA2', room)
            Character.objects.filter(pk=online.pk).update(
                last_connect=now - timedelta(minutes=5))
            offline_new = make_character('lsA3', room)
            Character.objects.filter(pk=offline_new.pk).update(
                last_connect=now - timedelta(hours=1))
            offline_old = make_character('lsA4', room)
            Character.objects.filter(pk=offline_old.pk).update(
                last_connect=now - timedelta(days=2))
            never = make_character('lsA5', room)
            return admin, online
        admin, online = await sync_to_async(setup)()

        sent = []
        consumer = make_stub_consumer(admin, sent)
        consumer.redis = FakeRedis(online_pks=[online.pk])
        await consumer.cmd_last()

        report = next(m for m in sent if m.get('category') == 'report')
        texts = []
        for entry in report['lines']:
            if 'segs' in entry:
                texts.append(''.join(seg['t'] for seg in entry['segs']))
            else:
                texts.append((entry.get('k', '') or '') + (entry.get('v', '') or ''))

        self.assertEqual(texts[0], 'Last seen...')
        self.assertIn('Character', texts[1])
        self.assertIn('Status', texts[1])
        self.assertIn('Last seen', texts[1])

        rows = texts[2:]
        online_row = next(t for t in rows if 'lsA2 Char' in t)
        self.assertIn('Online', online_row)
        self.assertIn('since ', online_row)
        self.assertIn('Level 1 lsA2 Origin lsA2 Archetype', online_row)

        never_row = next(t for t in rows if 'lsA5 Char' in t)
        self.assertIn('never', never_row)
        self.assertIn('Offline', never_row)

        # Ordering: online first, then offline by recency, never last.
        def idx(fragment):
            return next(i for i, t in enumerate(rows) if fragment in t)
        self.assertLess(idx('lsA2 Char'), idx('lsA3 Char'))
        self.assertLess(idx('lsA3 Char'), idx('lsA4 Char'))
        self.assertLess(idx('lsA4 Char'), idx('lsA5 Char'))
