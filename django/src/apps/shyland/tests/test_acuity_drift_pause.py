"""v24.18 Brief 1 (#142): passive acuity drift pauses during combat.

Tick Phase 2 excludes any character with an active CombatSession — the
same combat-membership predicate Phase 4 regen uses, by ruling: nothing
passively recovers in combat, for all three bars. Shift-active (#133)
and in-combat are independent pause conditions; post-combat resume is
ordinary (ACUITY_DRIFT_RATE per tick, no catch-up). These tests drive
process_effects directly (the test_v243_regen engine-harness style) and
pin the drift law, the snap rule, the pause, the resume, and shift
independence.

Non-boundary ticks (tick_number not a round boundary) are used
throughout so Phase 1 shift processing never moves the value — only
Phase 2 drift is in play.
"""

from asgiref.sync import sync_to_async

from django.test import TransactionTestCase

from apps.shyland.models import Character, CombatSession

from .test_acuity_shifts import make_shift_effect, set_acuity
from .test_command_revamp import make_character, make_world


def run_drift_engine():
    """Engine harness with stubbed delivery and presence."""
    from apps.shyland.management.commands.run_tick_engine import Command
    cmd = Command()
    sent = []

    async def record_send(character_pk, text, category, status,
                          event=None, fight=None):
        sent.append((character_pk, text, category, status))

    async def record_broadcast(room_id, text, category='room',
                               exclude_pk=None, exclude_pks=None):
        pass

    async def no_online(pks):
        return set()
    cmd.send_to_player = record_send
    cmd.broadcast_to_room = record_broadcast
    cmd._online_character_pks = no_online
    return cmd, sent


def get_acuity(char):
    return Character.objects.get(pk=char.pk).acuity_current


class DriftLawTests(TransactionTestCase):

    async def test_below_baseline_drifts_up_by_rate(self):
        def setup():
            zone, room = make_world('adpA')
            char = make_character('adpA', room)
            set_acuity(char, current=0.90, baseline=1.0)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_drift_engine()
        await cmd.process_effects(1)

        self.assertEqual(await sync_to_async(get_acuity)(char), 0.91)

    async def test_above_baseline_drifts_down_by_rate(self):
        def setup():
            zone, room = make_world('adpB')
            char = make_character('adpB', room)
            set_acuity(char, current=1.10, baseline=1.0)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_drift_engine()
        await cmd.process_effects(1)

        self.assertEqual(await sync_to_async(get_acuity)(char), 1.09)

    async def test_snap_within_rate_lands_exactly_on_baseline(self):
        def setup():
            zone, room = make_world('adpC')
            char = make_character('adpC', room)
            set_acuity(char, current=0.995, baseline=1.0)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_drift_engine()
        await cmd.process_effects(1)

        self.assertEqual(await sync_to_async(get_acuity)(char), 1.0)


class DriftPauseTests(TransactionTestCase):

    async def test_active_combat_pauses_drift(self):
        def setup():
            zone, room = make_world('adpD')
            char = make_character('adpD', room)
            set_acuity(char, current=0.90, baseline=1.0)
            session = CombatSession.objects.create(room=room, is_active=True)
            session.characters.add(char)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_drift_engine()
        await cmd.process_effects(1)

        self.assertEqual(await sync_to_async(get_acuity)(char), 0.90)

    async def test_resume_after_combat_is_ordinary_rate(self):
        def setup():
            zone, room = make_world('adpE')
            char = make_character('adpE', room)
            set_acuity(char, current=0.90, baseline=1.0)
            session = CombatSession.objects.create(room=room, is_active=True)
            session.characters.add(char)
            return char, session
        char, session = await sync_to_async(setup)()

        cmd, sent = run_drift_engine()
        await cmd.process_effects(1)
        self.assertEqual(await sync_to_async(get_acuity)(char), 0.90)

        def end_combat():
            session.is_active = False
            session.save(update_fields=['is_active'])
        await sync_to_async(end_combat)()

        # One tick after the session ends: exactly one rate step —
        # no burst correction, no catch-up.
        await cmd.process_effects(2)
        self.assertEqual(await sync_to_async(get_acuity)(char), 0.91)


class ShiftIndependenceTests(TransactionTestCase):

    async def test_active_shift_pauses_drift_out_of_combat(self):
        def setup():
            zone, room = make_world('adpF')
            char = make_character('adpF', room)
            set_acuity(char, current=0.90, baseline=1.0)
            make_shift_effect('adpF', char, 'shift_acuity_high', 0.1)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_drift_engine()
        await cmd.process_effects(1)

        # The #133 exclusion, pinned: a running shift owns the value.
        self.assertEqual(await sync_to_async(get_acuity)(char), 0.90)

    async def test_shift_and_combat_together_still_no_drift(self):
        def setup():
            zone, room = make_world('adpG')
            char = make_character('adpG', room)
            set_acuity(char, current=0.90, baseline=1.0)
            make_shift_effect('adpG', char, 'shift_acuity_high', 0.1)
            session = CombatSession.objects.create(room=room, is_active=True)
            session.characters.add(char)
            return char
        char = await sync_to_async(setup)()

        cmd, sent = run_drift_engine()
        await cmd.process_effects(1)

        self.assertEqual(await sync_to_async(get_acuity)(char), 0.90)
