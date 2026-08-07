"""v24.12 Brief 1 — repair-kit wiring (#134).

The durability_restore application (most-damaged-first, always-succeeds,
15 + 10×Mk clamped at 100, actual-points annotation), the component-keyed
use-pipeline gate (dying → combat → eligibility, refusals consume
nothing), the fulfilled-purpose stop, per-line sequence output, the
per-item path (never aggregatable), and the seeded shape (base_value 15,
one instantaneous component, no loot tables).

Brief §5 test list → class map:
   1 → SeedShapeTests               2 → MostDamagedFirstTests
   3 → ClampTests                   4 → MkScalingTests
   5 → TieBreakTests                6 → BrokenSkippedTests
   7 → BrokenOnlyRefusalTests       8 → ZeroNeedRefusalTests
   9 → CombatRefusalTests          10 → DyingRefusalTests
  11 → FulfilledStopTests          12 → ShortfallTests
  13 → PerLineOutputTests          14 → NotAggregatableTests
  15 → EquippedEligibilityTests    16 → the full suite run itself
"""

import io

from asgiref.sync import sync_to_async

from django.core.management import call_command
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.shyland.item_utils import get_sale_price
from apps.shyland.models import (
    CombatSession, EffectComponent, EffectDefinition, ItemDefinition,
    ItemInstance, LootTableEntry, NpcDefinition, NpcInstance,
)

from .test_command_revamp import (
    make_character, make_item_def, make_owned_item, make_stub_consumer,
    make_world, outputs,
)
from .test_use_output_merge import make_heal_effect


COMBAT_LINE = "There's no patching anything up in the middle of a fight!"
DYING_LINE = "Patchwork won't save you now — you need healing."
ZERO_NEED_LINE = 'Nothing you own needs patching.'
BROKEN_ONLY_LINE = ("What's broken is beyond a field patch — "
                    'you need a real repairer.')
FULFILLED_LINE = 'Everything you own is in good repair.'


class FakeRedis:
    async def keys(self, *args):
        return []

    async def mget(self, *args):
        return []


def make_repair_effect(prefix):
    effect = EffectDefinition.objects.create(
        name=f'{prefix} Repair Kit', slug=f'{prefix}-repair-kit')
    EffectComponent.objects.create(
        definition=effect, component_type='durability_restore',
        magnitude_base=15.0, magnitude_scaling=10.0,
        duration_base=0.0, duration_scaling=0.0,
    )
    return effect


def setup_kits(prefix, count=1, mk_tier=1):
    zone, room = make_world(prefix)
    char = make_character(prefix, room)
    effect = make_repair_effect(prefix)
    kit_def = make_item_def(prefix, 'Repair Kit', 'consumable',
                            base_value=15, effect=effect)
    for _ in range(count):
        ItemInstance.objects.create(
            definition=kit_def, owner=char, mk_tier=mk_tier,
            rarity='common', durability_current=100.0, is_identified=True)
    return char, kit_def


def make_gear(prefix, char, name, durability, equipped=False):
    gear_def = make_item_def(prefix, name, 'weapon', takes_durability=True)
    return ItemInstance.objects.create(
        definition=gear_def, owner=char, mk_tier=1, rarity='common',
        durability_current=durability, is_identified=True,
        is_equipped=equipped)


def kits_left(kit_def):
    return ItemInstance.objects.filter(definition=kit_def).count()


def durability(item):
    return ItemInstance.objects.get(pk=item.pk).durability_current


class SeedShapeTests(TestCase):
    """Brief §5 case 1 + §6 spot-checks: the seeded repair-kit shape."""

    @classmethod
    def setUpTestData(cls):
        call_command('seed_world', stdout=io.StringIO())

    def test_item_definition_base_value_and_effect(self):
        kit = ItemDefinition.objects.get(slug='repair-kit')
        self.assertEqual(kit.base_value, 15)
        self.assertIsNotNone(kit.effect)
        self.assertEqual(kit.effect.slug, 'repair-kit')
        self.assertFalse(kit.takes_durability_loss)

    def test_effect_has_exactly_one_instantaneous_component(self):
        effect = EffectDefinition.objects.get(slug='repair-kit')
        components = list(effect.components.all())
        self.assertEqual(len(components), 1)
        component = components[0]
        self.assertEqual(component.component_type, 'durability_restore')
        self.assertEqual(component.magnitude_base, 15.0)
        self.assertEqual(component.magnitude_scaling, 10.0)
        self.assertTrue(component.is_instantaneous())
        # The restore table: 15 + 10×Mk.
        self.assertEqual(component.computed_magnitude(1), 25.0)
        self.assertEqual(component.computed_magnitude(2), 35.0)

    def test_sale_price_is_the_standard_third(self):
        kit = ItemDefinition.objects.get(slug='repair-kit')
        zone, room = make_world('rkS')
        instance = ItemInstance.objects.create(
            definition=kit, current_room=room, mk_tier=1, rarity='common',
            durability_current=100.0, is_identified=True)
        self.assertEqual(get_sale_price(instance), 5)

    def test_kit_joins_no_loot_table(self):
        self.assertFalse(
            LootTableEntry.objects.filter(
                item_definition__slug='repair-kit').exists())


class MostDamagedFirstTests(TransactionTestCase):
    """Brief §5 case 2: automatic targeting, most-damaged-first."""

    async def test_most_damaged_item_is_patched(self):
        def setup():
            char, kit_def = setup_kits('rkA')
            worse = make_gear('rkA1', char, 'Iron Mace', 40.0)
            better = make_gear('rkA2', char, 'Iron Sword', 70.0)
            return char, kit_def, worse, better
        char, kit_def, worse, better = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('repair kit')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Repair Kit Mk 1 and patch up the Iron Mace Mk 1. '
            '(+25 durability)')
        self.assertEqual(msgs[0]['category'], 'success')
        self.assertEqual(await sync_to_async(durability)(worse), 65.0)
        self.assertEqual(await sync_to_async(durability)(better), 70.0)
        self.assertEqual(await sync_to_async(kits_left)(kit_def), 0)


class ClampTests(TransactionTestCase):
    """Brief §5 case 3: clamp at 100; the annotation reports the ACTUAL
    points applied after the clamp."""

    async def test_clamp_and_actual_points_annotation(self):
        def setup():
            char, kit_def = setup_kits('rkB')
            gear = make_gear('rkB1', char, 'Iron Mace', 90.0)
            return char, kit_def, gear
        char, kit_def, gear = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('repair kit')
        msgs = outputs(sent)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Repair Kit Mk 1 and patch up the Iron Mace Mk 1. '
            '(+10 durability)')
        self.assertEqual(await sync_to_async(durability)(gear), 100.0)
        self.assertEqual(await sync_to_async(kits_left)(kit_def), 0)


class MkScalingTests(TransactionTestCase):
    """Brief §5 case 4: a Mk 2 kit restores 35."""

    async def test_mk2_kit_restores_35(self):
        def setup():
            char, kit_def = setup_kits('rkC', mk_tier=2)
            gear = make_gear('rkC1', char, 'Iron Mace', 40.0)
            return char, kit_def, gear
        char, kit_def, gear = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('repair kit')
        msgs = outputs(sent)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Repair Kit Mk 2 and patch up the Iron Mace Mk 1. '
            '(+35 durability)')
        self.assertEqual(await sync_to_async(durability)(gear), 75.0)


class TieBreakTests(TransactionTestCase):
    """Brief §5 case 5: equal durability — the stable pk tie-break."""

    async def test_equal_durability_patches_lower_pk(self):
        def setup():
            char, kit_def = setup_kits('rkD')
            first = make_gear('rkD1', char, 'Iron Mace', 50.0)
            second = make_gear('rkD2', char, 'Iron Sword', 50.0)
            return char, first, second
        char, first, second = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('repair kit')
        self.assertEqual(await sync_to_async(durability)(first), 75.0)
        self.assertEqual(await sync_to_async(durability)(second), 50.0)


class BrokenSkippedTests(TransactionTestCase):
    """Brief §5 case 6: broken (0%) gear is an ineligible target — the
    kit patches around it."""

    async def test_broken_item_is_skipped(self):
        def setup():
            char, kit_def = setup_kits('rkE')
            broken = make_gear('rkE1', char, 'Iron Mace', 0.0)
            damaged = make_gear('rkE2', char, 'Iron Sword', 50.0)
            return char, broken, damaged
        char, broken, damaged = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('repair kit')
        msgs = outputs(sent)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Repair Kit Mk 1 and patch up the Iron Sword Mk 1. '
            '(+25 durability)')
        self.assertEqual(await sync_to_async(durability)(broken), 0.0)
        self.assertEqual(await sync_to_async(durability)(damaged), 75.0)


class BrokenOnlyRefusalTests(TransactionTestCase):
    """Brief §5 case 7: when the only damage owned is broken gear, the
    kit refuses — and is not consumed."""

    async def test_broken_only_refuses_without_consuming(self):
        def setup():
            char, kit_def = setup_kits('rkF')
            make_gear('rkF1', char, 'Iron Mace', 0.0)
            return char, kit_def
        char, kit_def = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('repair kit')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], BROKEN_ONLY_LINE)
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertEqual(await sync_to_async(kits_left)(kit_def), 1)


class ZeroNeedRefusalTests(TransactionTestCase):
    """Brief §5 case 8: nothing damaged — the zero-need refusal, kit
    not consumed."""

    async def test_zero_need_refuses_without_consuming(self):
        def setup():
            char, kit_def = setup_kits('rkG')
            make_gear('rkG1', char, 'Iron Mace', 100.0)
            return char, kit_def
        char, kit_def = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('repair kit')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], ZERO_NEED_LINE)
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertEqual(await sync_to_async(kits_left)(kit_def), 1)


def make_combat(char, room, prefix):
    definition = NpcDefinition.objects.create(
        name=f'{prefix} snarler', slug=f'{prefix}-snarler',
        description='x', genre_tag='fantasy', is_aggressive=True,
        base_vitality=10, base_str=1, base_dex=1, base_end=1,
        base_int=1, base_wis=1, base_per=1,
    )
    npc = NpcInstance.objects.create(
        definition=definition, current_room=room, spawn_room=room,
        vitality_current=10, vitality_max=10,
    )
    session = CombatSession.objects.create(
        room=room, last_tick_at=timezone.now(),
    )
    session.characters.add(char)
    session.npcs.add(npc)
    return session


class CombatRefusalTests(TransactionTestCase):
    """Brief §5 case 9: the kit refuses in combat without consuming;
    a Healing Draught still uses fine in the same scenario."""

    def _setup(self):
        char, kit_def = setup_kits('rkH')
        make_gear('rkH1', char, 'Iron Mace', 40.0)
        from apps.shyland.models import Character
        Character.objects.filter(pk=char.pk).update(
            vitality_current=55, vitality_max=100)
        heal = make_heal_effect('rkH', magnitude=25.0)
        draught_def = make_item_def('rkH', 'Healing Draught',
                                    'consumable', effect=heal)
        make_owned_item(draught_def, char)
        make_combat(char, char.current_room, 'rkH')
        return char, kit_def, draught_def

    async def test_combat_refuses_kit_but_passes_draught(self):
        char, kit_def, draught_def = await sync_to_async(self._setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('repair kit')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], COMBAT_LINE)
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertEqual(await sync_to_async(kits_left)(kit_def), 1)

        # The draught is untouched by the gate — component-keyed, never
        # item-wide: it drinks fine in the identical combat state.
        sent2 = []
        consumer2 = make_stub_consumer(char, sent2)
        await consumer2.cmd_use('healing draught')
        msgs2 = outputs(sent2)
        self.assertIn('feel your body recover', msgs2[0]['text'])

        def draughts():
            return ItemInstance.objects.filter(
                definition=draught_def).count()
        self.assertEqual(await sync_to_async(draughts)(), 0)


class DyingRefusalTests(TransactionTestCase):
    """Brief §5 case 10: the kit refuses while dying (dying wins over
    combat when both hold) without consuming; a draught while dying
    still runs the revival sequence."""

    def _setup(self, prefix, in_combat=False):
        from apps.shyland.models import Character
        char, kit_def = setup_kits(prefix)
        make_gear(f'{prefix}1', char, 'Iron Mace', 40.0)
        Character.objects.filter(pk=char.pk).update(
            vitality_current=0, vitality_max=100, is_dying=True)
        char.is_dying = True
        heal = make_heal_effect(prefix, magnitude=25.0)
        draught_def = make_item_def(prefix, 'Healing Draught',
                                    'consumable', effect=heal)
        make_owned_item(draught_def, char)
        if in_combat:
            make_combat(char, char.current_room, prefix)
        return char, kit_def, draught_def

    async def test_dying_refuses_kit_without_consuming(self):
        char, kit_def, _ = await sync_to_async(self._setup)('rkI')
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('repair kit')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['text'], DYING_LINE)
        self.assertEqual(msgs[0]['category'], 'warn')
        self.assertEqual(await sync_to_async(kits_left)(kit_def), 1)

    async def test_dying_wins_over_combat(self):
        char, kit_def, _ = await sync_to_async(self._setup)(
            'rkJ', in_combat=True)
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('repair kit')
        msgs = outputs(sent)
        self.assertEqual(msgs[0]['text'], DYING_LINE)
        self.assertEqual(await sync_to_async(kits_left)(kit_def), 1)

    async def test_draught_while_dying_still_revives(self):
        char, kit_def, draught_def = await sync_to_async(self._setup)('rkK')
        sent = []
        consumer = make_stub_consumer(char, sent)
        consumer.redis = FakeRedis()
        await consumer.cmd_use('healing draught')
        texts = [m['text'] for m in outputs(sent)]
        self.assertIn(
            'Breath floods back into your lungs. You are alive — barely.',
            texts)
        self.assertEqual(await sync_to_async(kits_left)(kit_def), 1)


class FulfilledStopTests(TransactionTestCase):
    """Brief §5 case 11: the fulfilled-purpose stop — one kit does the
    job, the sequence stops whole, no only-had-N warn."""

    async def test_sequence_stops_when_nothing_damaged_remains(self):
        def setup():
            char, kit_def = setup_kits('rkL', count=3)
            gear = make_gear('rkL1', char, 'Iron Mace', 80.0)
            return char, kit_def, gear
        char, kit_def, gear = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('3 repair kit')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 2)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Repair Kit Mk 1 and patch up the Iron Mace Mk 1. '
            '(+20 durability)')
        self.assertEqual(msgs[0]['category'], 'success')
        self.assertEqual(msgs[1]['text'], FULFILLED_LINE)
        self.assertEqual(msgs[1]['category'], 'reward')
        self.assertNotIn('You only had', ''.join(m['text'] for m in msgs))
        self.assertEqual(await sync_to_async(durability)(gear), 100.0)
        self.assertEqual(await sync_to_async(kits_left)(kit_def), 2)


class ShortfallTests(TransactionTestCase):
    """Brief §5 case 12: the standing shortfall warn fires when the
    request exceeded inventory and the sequence wasn't fulfilled."""

    async def test_shortfall_consumes_all_and_warns(self):
        def setup():
            char, kit_def = setup_kits('rkM', count=2)
            make_gear('rkM1', char, 'Iron Mace', 10.0)
            make_gear('rkM2', char, 'Iron Sword', 20.0)
            return char, kit_def
        char, kit_def = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('5 repair kit')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 3)
        self.assertIn('patch up', msgs[0]['text'])
        self.assertIn('patch up', msgs[1]['text'])
        self.assertEqual(msgs[2]['text'], 'You only had 2.')
        self.assertEqual(msgs[2]['category'], 'warn')
        self.assertEqual(await sync_to_async(kits_left)(kit_def), 0)


class PerLineOutputTests(TransactionTestCase):
    """Brief §5 case 13: per-item sentences, never count-form
    aggregation — each mend names its own item, re-targeted
    most-damaged-first after each kit."""

    async def test_two_kits_two_items_two_sentences(self):
        def setup():
            char, kit_def = setup_kits('rkN', count=2)
            first = make_gear('rkN1', char, 'Iron Mace', 60.0)
            second = make_gear('rkN2', char, 'Iron Sword', 70.0)
            return char, first, second
        char, first, second = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('2 repair kit')
        msgs = outputs(sent)
        self.assertEqual(len(msgs), 2)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Repair Kit Mk 1 and patch up the Iron Mace Mk 1. '
            '(+25 durability)')
        self.assertEqual(
            msgs[1]['text'],
            'You use a Repair Kit Mk 1 and patch up the Iron Sword Mk 1. '
            '(+25 durability)')
        self.assertNotIn('×', msgs[0]['text'] + msgs[1]['text'])
        self.assertEqual(await sync_to_async(durability)(first), 85.0)
        self.assertEqual(await sync_to_async(durability)(second), 95.0)


class NotAggregatableTests(TransactionTestCase):
    """Brief §5 case 14: kits never take the aggregate path — the
    per-item test fails them (no vitality-restore component)."""

    async def test_use_items_aggregatable_is_false_for_kits(self):
        def setup():
            char, kit_def = setup_kits('rkO')
            kit = ItemInstance.objects.select_related(
                'definition__effect').get(definition=kit_def)
            return char, kit
        char, kit = await sync_to_async(setup)()
        consumer = make_stub_consumer(char, [])
        self.assertFalse(await consumer.use_items_aggregatable([kit]))


class EquippedEligibilityTests(TransactionTestCase):
    """Brief §5 case 15: a damaged equipped item is a valid target —
    the kit's scope is everything owned."""

    async def test_equipped_damaged_item_is_patched(self):
        def setup():
            char, kit_def = setup_kits('rkP')
            gear = make_gear('rkP1', char, 'Iron Mace', 40.0,
                             equipped=True)
            return char, gear
        char, gear = await sync_to_async(setup)()
        sent = []
        consumer = make_stub_consumer(char, sent)
        await consumer.cmd_use('repair kit')
        msgs = outputs(sent)
        self.assertEqual(
            msgs[0]['text'],
            'You use a Repair Kit Mk 1 and patch up the Iron Mace Mk 1. '
            '(+25 durability)')
        self.assertEqual(await sync_to_async(durability)(gear), 65.0)
