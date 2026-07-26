"""v23 brief 3 (#133): acuity shift semantics.

shift_acuity_high stops at the drinker's own band edge (stored exactly,
2-decimal) and climbs-and-sustains; shift_acuity_low keeps the hard
ACUITY_FLOOR boundary. Both branches follow the announcement doctrine:
effect ticks never announce no-ops; boundary arrival gets one terminal
line; holding is silent. Shift effects are one-way (the directional
invariant): high never lowers, low never raises."""

from datetime import timedelta

from asgiref.sync import sync_to_async

from django.test import TransactionTestCase
from django.utils import timezone

from apps.shyland.combat_utils import (
    ACUITY_CEILING, ACUITY_FLOOR, acuity_damage_modifier,
)
from apps.shyland.models import (
    Character, EffectComponent, EffectComponentInstance, EffectDefinition,
    EffectInstance,
)

from .test_command_revamp import make_character, make_world
from .test_tick_expiry import run_effects_engine

SETTLES = 'Your focus settles at its keenest.'
FRAYS = 'Your focus frays to nothing.'


def make_shift_effect(prefix, char, ctype, magnitude):
    """One live (far-future expiry) shift component on char."""
    definition = EffectDefinition.objects.create(
        name=f'{prefix} Tonic', slug=f'{prefix}-tonic')
    instance = EffectInstance.objects.create(
        definition=definition, target=char, mk_tier=1, is_active=True)
    component = EffectComponent.objects.create(
        definition=definition, component_type=ctype, order=0,
        magnitude_base=magnitude, magnitude_scaling=0.0,
        duration_base=3600.0, duration_scaling=0.0,
    )
    EffectComponentInstance.objects.create(
        effect_instance=instance, component=component,
        magnitude=magnitude, is_active=True,
        expires_at=timezone.now() + timedelta(seconds=3600),
    )
    return instance


def set_acuity(char, current, baseline=1.0, band_low=0.8, band_high=1.15):
    Character.objects.filter(pk=char.pk).update(
        acuity_current=current, acuity_baseline=baseline,
        acuity_band_low=band_low, acuity_band_high=band_high,
    )


class AcuityShiftHighTests(TransactionTestCase):

    async def _tick(self, cmd, msgs, char, n):
        msgs.clear()
        await cmd.process_effects(n)
        return [t for pk, t, c in msgs if pk == char.pk]

    async def test_band_edge_stop_exact_with_doctrine(self):
        def setup():
            zone, room = make_world('ashA')
            char = make_character('ashA', room)
            set_acuity(char, current=1.0, band_high=1.15)
            make_shift_effect('ashA', char, 'shift_acuity_high', 0.1)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        # Effect components tick on round boundaries (every
        # COMBAT_ROUND_TICKS=3rd tick) — drive boundary ticks only.
        # Boundary 1: climbing — the sharpens line, value-suffixed.
        texts = await self._tick(cmd, msgs, char, 3)
        self.assertEqual(texts, ['Your focus sharpens. (Acuity 1.1)'])

        # Boundary 2: arrival — exactly the terminal line, not the sharpens line.
        texts = await self._tick(cmd, msgs, char, 6)
        self.assertEqual(texts, [SETTLES])

        # Boundaries 3-4: holding — silence.
        texts = await self._tick(cmd, msgs, char, 9)
        self.assertEqual(texts, [])
        texts = await self._tick(cmd, msgs, char, 12)
        self.assertEqual(texts, [])

        def state():
            c = Character.objects.get(pk=char.pk)
            return c.acuity_current, c.acuity_band_high
        current, band_high = await sync_to_async(state)()
        # Stored EXACTLY equal to the 2-decimal band edge, never above.
        self.assertEqual(current, band_high)
        self.assertEqual(current, 1.15)

    async def test_modifier_is_neutral_at_the_stopped_edge(self):
        def setup():
            zone, room = make_world('ashB')
            char = make_character('ashB', room)
            set_acuity(char, current=1.15, band_high=1.15)
            return Character.objects.get(pk=char.pk)
        char = await sync_to_async(setup)()
        # In-band at the top edge: a > band_high is False at equality.
        self.assertEqual(acuity_damage_modifier(char), 1.0)

    async def test_directional_invariant_high_never_lowers(self):
        def setup():
            zone, room = make_world('ashC')
            char = make_character('ashC', room)
            set_acuity(char, current=ACUITY_CEILING, band_high=1.15)
            make_shift_effect('ashC', char, 'shift_acuity_high', 0.1)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        for n in (3, 6):
            texts = await self._tick(cmd, msgs, char, n)
            self.assertEqual(texts, [])
        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).acuity_current)()
        self.assertEqual(current, ACUITY_CEILING)

    async def test_wide_band_stops_at_its_own_edge(self):
        def setup():
            zone, room = make_world('ashD')
            char = make_character('ashD', room)
            # Voidtouched-shaped: band_high 1.30 — stops there, not 1.15.
            set_acuity(char, current=1.0, band_high=1.30)
            make_shift_effect('ashD', char, 'shift_acuity_high', 0.2)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        texts = await self._tick(cmd, msgs, char, 3)
        self.assertEqual(texts, ['Your focus sharpens. (Acuity 1.2)'])
        texts = await self._tick(cmd, msgs, char, 6)
        self.assertEqual(texts, [SETTLES])
        texts = await self._tick(cmd, msgs, char, 9)
        self.assertEqual(texts, [])

        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).acuity_current)()
        self.assertEqual(current, 1.30)


class AcuityShiftLowTests(TransactionTestCase):

    async def _tick(self, cmd, msgs, char, n):
        msgs.clear()
        await cmd.process_effects(n)
        return [t for pk, t, c in msgs if pk == char.pk]

    async def test_floor_arrival_terminal_then_silence(self):
        def setup():
            zone, room = make_world('aslA')
            char = make_character('aslA', room)
            set_acuity(char, current=0.3)
            make_shift_effect('aslA', char, 'shift_acuity_low', 0.1)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        texts = await self._tick(cmd, msgs, char, 3)
        self.assertEqual(texts, ['Your focus wavers. (Acuity 0.2)'])
        texts = await self._tick(cmd, msgs, char, 6)
        self.assertEqual(texts, [FRAYS])
        texts = await self._tick(cmd, msgs, char, 9)
        self.assertEqual(texts, [])

        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).acuity_current)()
        self.assertEqual(current, ACUITY_FLOOR)

    async def test_directional_invariant_low_never_raises(self):
        def setup():
            zone, room = make_world('aslB')
            char = make_character('aslB', room)
            set_acuity(char, current=ACUITY_FLOOR)
            make_shift_effect('aslB', char, 'shift_acuity_low', 0.1)
            return char
        char = await sync_to_async(setup)()
        cmd, msgs = run_effects_engine()

        for n in (3, 6):
            texts = await self._tick(cmd, msgs, char, n)
            self.assertEqual(texts, [])
        current = await sync_to_async(
            lambda: Character.objects.get(pk=char.pk).acuity_current)()
        self.assertEqual(current, ACUITY_FLOOR)
