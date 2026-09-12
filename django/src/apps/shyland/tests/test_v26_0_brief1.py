"""v26.0 brief 1 (#145): effect tick hygiene — the #133 announcement
doctrine applied uniformly to the dot/hot family.

Change-only ticks: new == old does nothing at all (no save, no status
build, no announcement). Change ticks announce the ACTUAL applied delta,
never the nominal magnitude where they differ. Boundary arrival gets one
stateless terminal line instead of the ordinary line (dot_longevity at
0, dot_acuity at ACUITY_FLOOR, hot_vitality/hot_longevity at their maxes,
hot_acuity at baseline); holding at the boundary is silent by
construction. dot_vitality is pinned unchanged (its floor is the Dying
event, terminal by nature), and the shift branches — the pattern's
origin — are smoke-pinned untouched.

Test characters sit in an active CombatSession: Phase 2 drift and
Phase 4 regen both exclude in-combat characters, so the ticking
component under test is the only thing moving the bars.
"""

from unittest import mock

from asgiref.sync import sync_to_async

from django.test import TransactionTestCase

from apps.shyland.combat_utils import ACUITY_FLOOR
from apps.shyland.models import Character, CombatSession, EffectInstance

from .test_command_revamp import make_character, make_world
from .test_tick_expiry import run_effects_engine
from .test_acuity_shifts import make_shift_effect as make_tick_effect, set_acuity

TORN = 'Your focus is torn to nothing.'
SETTLES_CENTER = 'Your mind settles back to its center.'


def set_bars(char, **kwargs):
    Character.objects.filter(pk=char.pk).update(**kwargs)


def enter_combat(char, room):
    session = CombatSession.objects.create(room=room, is_active=True)
    session.characters.add(char)
    return session


class TickHygieneBase(TransactionTestCase):

    async def _tick(self, cmd, msgs, char, n):
        msgs.clear()
        await cmd.process_effects(n)
        return [(t, c) for pk, t, c in msgs if pk == char.pk]

    async def _silent_tick_no_saves(self, cmd, msgs, char, n):
        """Drive one boundary tick asserting zero messages AND zero
        Character saves (the no-change path skips the save entirely)."""
        with mock.patch.object(Character, 'save') as save_spy:
            rows = await self._tick(cmd, msgs, char, n)
        self.assertEqual(rows, [])
        self.assertEqual(save_spy.call_count, 0)


class DotLongevityTests(TickHygieneBase):

    async def test_actual_delta_partial_terminal_then_silence(self):
        def setup():
            zone, room = make_world('ethA')
            char = make_character('ethA', room)
            set_bars(char, longevity_current=25, longevity_max=100)
            enter_combat(char, room)
            make_tick_effect('ethA', char, 'dot_longevity', 10)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        # Change ticks: the actual delta, combat category.
        rows = await self._tick(cmd, msgs, char, 3)
        self.assertEqual(rows, [
            ('Your stamina drains from ethA Tonic. (-10 Longevity)', 'combat')])
        rows = await self._tick(cmd, msgs, char, 6)
        self.assertEqual(rows, [
            ('Your stamina drains from ethA Tonic. (-10 Longevity)', 'combat')])

        # Arrival at 0 is a PARTIAL application (5 left, magnitude 10):
        # one terminal line carrying the actual delta, not the nominal.
        rows = await self._tick(cmd, msgs, char, 9)
        self.assertEqual(rows, [
            ('Your stamina is bled dry. (-5 Longevity)', 'combat')])

        # Holding at the floor: zero messages, zero saves.
        await self._silent_tick_no_saves(cmd, msgs, char, 12)

        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).longevity_current)()
        self.assertEqual(current, 0)


class DotAcuityTests(TickHygieneBase):

    async def test_change_terminal_at_floor_then_silence(self):
        def setup():
            zone, room = make_world('ethB')
            char = make_character('ethB', room)
            set_acuity(char, current=0.4)
            enter_combat(char, room)
            make_tick_effect('ethB', char, 'dot_acuity', 0.1)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        rows = await self._tick(cmd, msgs, char, 3)
        self.assertEqual(rows, [
            ('Your focus is disrupted by ethB Tonic. (Acuity 0.30)', 'combat')])
        rows = await self._tick(cmd, msgs, char, 6)
        self.assertEqual(rows, [
            ('Your focus is disrupted by ethB Tonic. (Acuity 0.20)', 'combat')])

        # Arrival at ACUITY_FLOOR: the bare terminal line, once.
        rows = await self._tick(cmd, msgs, char, 9)
        self.assertEqual(rows, [(TORN, 'combat')])

        # Holding at the floor: silence, no saves.
        await self._silent_tick_no_saves(cmd, msgs, char, 12)

        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).acuity_current)()
        self.assertEqual(current, ACUITY_FLOOR)


class HotVitalityTests(TickHygieneBase):

    async def test_recovery_partial_terminal_then_silence(self):
        def setup():
            zone, room = make_world('ethC')
            char = make_character('ethC', room)
            set_bars(char, vitality_current=80, vitality_max=100)
            enter_combat(char, room)
            make_tick_effect('ethC', char, 'hot_vitality', 15)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        # Change tick: actual recovery, system category.
        rows = await self._tick(cmd, msgs, char, 3)
        self.assertEqual(rows, [
            ('You recover 15 Vitality from ethC Tonic.', 'system')])

        # Arrival at the cap is a PARTIAL top-up (+5, not the nominal 15):
        # one terminal line carrying the actual delta.
        rows = await self._tick(cmd, msgs, char, 6)
        self.assertEqual(rows, [
            ('Your body is whole once more. (+5 Vitality)', 'system')])

        # Holding at full: silence, no saves.
        await self._silent_tick_no_saves(cmd, msgs, char, 9)

        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).vitality_current)()
        self.assertEqual(current, 100)

    async def test_already_full_bar_is_silent_from_the_first_tick(self):
        def setup():
            zone, room = make_world('ethD')
            char = make_character('ethD', room)
            set_bars(char, vitality_current=100, vitality_max=100)
            enter_combat(char, room)
            make_tick_effect('ethD', char, 'hot_vitality', 15)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        # Pre-brief behavior: a false 'You recover…' line every round.
        for n in (3, 6, 9):
            await self._silent_tick_no_saves(cmd, msgs, char, n)


class HotLongevityTests(TickHygieneBase):

    async def test_recovery_partial_terminal_then_silence(self):
        def setup():
            zone, room = make_world('ethE')
            char = make_character('ethE', room)
            set_bars(char, longevity_current=90, longevity_max=100)
            enter_combat(char, room)
            make_tick_effect('ethE', char, 'hot_longevity', 6)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        rows = await self._tick(cmd, msgs, char, 3)
        self.assertEqual(rows, [
            ('You recover 6 Longevity from ethE Tonic.', 'system')])

        # Partial arrival (+4): terminal line with the actual delta.
        rows = await self._tick(cmd, msgs, char, 6)
        self.assertEqual(rows, [
            ('Your stamina returns in full. (+4 Longevity)', 'system')])

        await self._silent_tick_no_saves(cmd, msgs, char, 9)

        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).longevity_current)()
        self.assertEqual(current, 100)


class HotAcuityTests(TickHygieneBase):

    async def test_walk_to_baseline_terminal_then_silence(self):
        def setup():
            zone, room = make_world('ethF')
            char = make_character('ethF', room)
            set_acuity(char, current=0.8, baseline=1.0)
            enter_combat(char, room)
            make_tick_effect('ethF', char, 'hot_acuity', 0.1)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        rows = await self._tick(cmd, msgs, char, 3)
        self.assertEqual(rows, [
            ('Your mind clears from ethF Tonic. (Acuity 0.90)', 'system')])

        # Arrival at baseline: the bare terminal line, once.
        rows = await self._tick(cmd, msgs, char, 6)
        self.assertEqual(rows, [(SETTLES_CENTER, 'system')])

        # Holding at baseline: silence AND no save (pre-brief this branch
        # saved every tick at baseline).
        await self._silent_tick_no_saves(cmd, msgs, char, 9)

        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).acuity_current)()
        self.assertEqual(current, 1.0)

    async def test_at_baseline_from_the_start_is_silent_and_saveless(self):
        def setup():
            zone, room = make_world('ethG')
            char = make_character('ethG', room)
            set_acuity(char, current=1.0, baseline=1.0)
            enter_combat(char, room)
            make_tick_effect('ethG', char, 'hot_acuity', 0.1)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        for n in (3, 6, 9):
            await self._silent_tick_no_saves(cmd, msgs, char, n)


class DotVitalityPinTests(TickHygieneBase):
    """#145 conformance pin: the dot_vitality branch is UNCHANGED by this
    brief — its floor is the Dying event, terminal by nature."""

    async def test_non_fatal_tick_line_byte_identical(self):
        def setup():
            zone, room = make_world('ethH')
            char = make_character('ethH', room)
            set_bars(char, vitality_current=50, vitality_max=100)
            enter_combat(char, room)
            make_tick_effect('ethH', char, 'dot_vitality', 10)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        rows = await self._tick(cmd, msgs, char, 3)
        self.assertEqual(rows, [
            ('You take 10 damage from ethH Tonic.', 'combat')])

        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).vitality_current)()
        self.assertEqual(current, 40)

    async def test_fatal_tick_still_routes_to_the_dying_event_path(self):
        def setup():
            zone, room = make_world('ethI')
            char = make_character('ethI', room)
            set_bars(char, vitality_current=5, vitality_max=100)
            enter_combat(char, room)
            instance = make_tick_effect('ethI', char, 'dot_vitality', 10)
            return char, instance
        char, instance = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        rows = await self._tick(cmd, msgs, char, 3)
        self.assertIn(
            ('You have been dealt a fatal blow. Your life force is ebbing '
             'away — you have only moments to act.', 'error'),
            rows)

        def state():
            c = Character.objects.get(pk=char.pk)
            ei = EffectInstance.objects.get(pk=instance.pk)
            return c.is_dying, c.vitality_current, ei.is_active, ei.removed_by
        is_dying, vitality, ei_active, removed_by = await sync_to_async(state)()
        self.assertTrue(is_dying)
        self.assertEqual(vitality, 0)
        self.assertFalse(ei_active)
        self.assertEqual(removed_by, 'dying')


class ShiftBranchRegressionTests(TickHygieneBase):
    """One smoke assertion each: the shift branches — the doctrine's
    origin pattern — are untouched by this brief."""

    async def test_shift_high_still_announces_the_sharpens_line(self):
        def setup():
            zone, room = make_world('ethJ')
            char = make_character('ethJ', room)
            set_acuity(char, current=1.0, band_high=1.15)
            make_tick_effect('ethJ', char, 'shift_acuity_high', 0.1)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        rows = await self._tick(cmd, msgs, char, 3)
        self.assertEqual(rows, [('Your focus sharpens. (Acuity 1.10)', 'system')])

    async def test_shift_low_still_announces_the_wavers_line(self):
        def setup():
            zone, room = make_world('ethK')
            char = make_character('ethK', room)
            set_acuity(char, current=0.3)
            make_tick_effect('ethK', char, 'shift_acuity_low', 0.1)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        rows = await self._tick(cmd, msgs, char, 3)
        self.assertEqual(rows, [('Your focus wavers. (Acuity 0.20)', 'system')])
