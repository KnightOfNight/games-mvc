"""v24.0 Brief 1 — The Draught Law (#139).

A Healing Draught restores a percentage of the drinker's vitality_max,
never a flat amount: heal = ceil((0.15 + 0.05 × Mk) × vitality_max),
minimum VITALITY_PERCENT_HEAL_FLOOR (25). The percentage is of MAX,
never of deficit; math.ceil, never bare round() (the #105 lesson).
Covers the law's arithmetic, the single-use path at large and small
bars, Mk scaling, the unchanged #61 refusal, the #151 aggregate's
consume-only-what's-needed with the law's magnitudes, and the clamp
at max.
"""

from asgiref.sync import sync_to_async

from django.test import TestCase, TransactionTestCase

from apps.shyland.effect_utils import percent_heal_amount
from apps.shyland.models import (
    Character, EffectComponent, EffectDefinition, ItemInstance,
    VITALITY_PERCENT_HEAL_FLOOR,
)

from .test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_world, outputs,
)


def make_percent_heal_effect(prefix, base=0.15, scaling=0.05):
    heal = EffectDefinition.objects.create(
        name=f'{prefix} PctHeal', slug=f'{prefix}-pct-heal')
    EffectComponent.objects.create(
        definition=heal, component_type='restore_vitality_percent',
        magnitude_base=base, magnitude_scaling=scaling,
        duration_base=0.0, duration_scaling=0.0,
    )
    return heal


def setup_percent_draughts(prefix, count=3, vitality=(10, 100)):
    """The law-standard draught: 0.15 base, 0.05 scaling (Mk 1 = 20%)."""
    zone, room = make_world(prefix)
    char = make_character(prefix, room)
    current, maximum = vitality
    Character.objects.filter(pk=char.pk).update(
        vitality_current=current, vitality_max=maximum)
    char.vitality_current, char.vitality_max = current, maximum
    heal = make_percent_heal_effect(prefix)
    draught_def = make_item_def(prefix, 'Healing Draught', 'consumable',
                                effect=heal)
    for _ in range(count):
        make_owned_item(draught_def, char)
    return char, draught_def


def remaining(char):
    return ItemInstance.objects.filter(owner=char).count()


def vitality_now(char):
    return Character.objects.get(pk=char.pk).vitality_current


class LawArithmeticTests(TestCase):
    """The shared helper is the law: ceil of fraction × max, floored."""

    def test_percentage_case_large_bar(self):
        # ceil(0.20 × 718) = ceil(143.6) = 144.
        self.assertEqual(percent_heal_amount(0.20, 718), 144)

    def test_floor_case_small_bar(self):
        # 0.20 × 100 = 20 — the floor lifts it to 25, never 20.
        self.assertEqual(percent_heal_amount(0.20, 100), 25)

    def test_mk_scaling_same_max(self):
        # Mk 2 = 25% of the same bar: ceil(0.25 × 718) = ceil(179.5) = 180.
        self.assertEqual(percent_heal_amount(0.25, 718), 180)

    def test_floor_disengages_past_125(self):
        # At Mk 1 the floor disengages once vitality_max exceeds 125:
        # exactly 125 → 25 (floor and percentage agree); 126 → ceil rules.
        self.assertEqual(percent_heal_amount(0.20, 125), 25)
        self.assertEqual(percent_heal_amount(0.20, 126), 26)

    def test_ceil_never_bankers_rounding(self):
        # ceil(0.20 × 502) = ceil(100.4) = 101 — round() would say 100.
        self.assertEqual(percent_heal_amount(0.20, 502), 101)

    def test_floor_constant_is_25(self):
        self.assertEqual(VITALITY_PERCENT_HEAL_FLOOR, 25)


class PercentSingleUseTests(TransactionTestCase):
    """The single-use path heals by the law and says so."""

    async def test_large_bar_mk1_heals_144(self):
        char, _ = await sync_to_async(setup_percent_draughts)(
            'dlA', count=1, vitality=(100, 718))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('healing draught')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Healing Draught Mk 1 and feel your body recover. '
            '(+144 Vitality)')
        self.assertEqual(msgs[0]['category'], 'success')
        self.assertEqual(await sync_to_async(vitality_now)(char), 244)

    async def test_small_bar_floor_heals_25_not_20(self):
        char, _ = await sync_to_async(setup_percent_draughts)(
            'dlB', count=1, vitality=(10, 100))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('healing draught')
        msgs = outputs(sent)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Healing Draught Mk 1 and feel your body recover. '
            '(+25 Vitality)')
        self.assertEqual(await sync_to_async(vitality_now)(char), 35)

    async def test_mk2_heals_25_percent(self):
        # Same max, Mk 2 → 25%: ceil(0.25 × 718) = 180.
        def setup():
            char, draught_def = setup_percent_draughts(
                'dlC', count=0, vitality=(100, 718))
            ItemInstance.objects.create(
                definition=draught_def, owner=char, mk_tier=2,
                rarity='common', durability_current=100.0,
                is_identified=True)
            return char
        char = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('healing draught')
        msgs = outputs(sent)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Healing Draught Mk 2 and feel your body recover. '
            '(+180 Vitality)')
        self.assertEqual(await sync_to_async(vitality_now)(char), 280)


class RefusalUnchangedTests(TransactionTestCase):
    """The #61 world-declined refusal is untouched by the law."""

    async def test_full_vitality_refusal_unchanged(self):
        char, _ = await sync_to_async(setup_percent_draughts)(
            'dlD', count=3, vitality=(718, 718))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('healing draught')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['text'], 'You are already at full health.')
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertEqual(await sync_to_async(remaining)(char), 3)


class PercentAggregateTests(TransactionTestCase):
    """The #151 aggregate under the law's magnitudes: consume only
    what's needed, one merged message, clamp at max."""

    async def test_consume_only_whats_needed(self):
        # Deficit 200 at 144/heal (max 718, Mk 1): two draughts cover
        # it — 3 asked, 2 consumed, one merged ×2 line.
        char, _ = await sync_to_async(setup_percent_draughts)(
            'dlE', count=3, vitality=(518, 718))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('3 healing draughts')
        self.assertEqual(await sync_to_async(remaining)(char), 1)
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0]['text'],
            'You use Healing Draught Mk 1 ×2 and feel your body recover. '
            '(+288 Vitality) You are restored to full health.')
        self.assertEqual(msgs[0]['category'], 'reward')

    async def test_clamp_at_max(self):
        # Deficit 50, heal 144 — vitality clamps at max, full-heal fold.
        char, _ = await sync_to_async(setup_percent_draughts)(
            'dlF', count=1, vitality=(668, 718))
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('healing draught')
        self.assertEqual(await sync_to_async(vitality_now)(char), 718)
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertTrue(
            msgs[0]['text'].endswith('You are restored to full health.'))
        self.assertEqual(msgs[0]['category'], 'reward')
