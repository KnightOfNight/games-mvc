"""V24.23 Brief 1 (#215): Percentage Bags.

The equipped-bag carry contribution becomes a percentage of the
STR-derived base:

    capacity = floor( effective_STR × 10 × (100 + Σ bag_pct) / 100 )

where each equipped bag contributes carry_pct_base + carry_pct_per_mk ×
the instance's Mk tier. Percentages from multiple equipped bags sum into
one multiplier, never compound. One helper (item_utils.carry_capacity)
answers every site, the unequip guard included.
"""

from asgiref.sync import sync_to_async

from django.test import SimpleTestCase, TransactionTestCase

from apps.shyland.item_utils import bag_pct, carry_capacity
from apps.shyland.models import Character, ItemDefinition, ItemInstance

from .test_command_revamp import make_character, make_stub_consumer, make_world


def mem_bag_def(pk, pct_base, pct_per_mk):
    return ItemDefinition(
        pk=pk, name=f'Test Bag {pk}', slug=f'v2423-bag-{pk}',
        item_type='bag', genre_tag='fantasy', valid_slots=['BACK'],
        scaling_base=0.0, scaling_factor=0.0,
        carry_pct_base=pct_base, carry_pct_per_mk=pct_per_mk,
    )


def mem_bag(pk, defn, mk_tier):
    item = ItemInstance(
        pk=pk, mk_tier=mk_tier, rarity='common', durability_current=100.0,
        is_equipped=True, equipped_slot='BACK', is_identified=True,
    )
    item.definition = defn
    return item


class FormulaTests(SimpleTestCase):
    """The Section 1 formula: floor, Mk scaling, summing, reference case."""

    def test_bagless_capacity_is_the_plain_str_base(self):
        char = Character(stat_str=10)
        self.assertEqual(carry_capacity(char, []), 100)

    def test_floor_behavior(self):
        # STR 11 → base 110; one 3% bag → 110 × 103 / 100 = 113.3 → 113.
        char = Character(stat_str=11)
        bag = mem_bag(1, mem_bag_def(1, 3, 0), mk_tier=1)
        self.assertEqual(carry_capacity(char, [bag]), 113)

    def test_mk_scaling_same_definition(self):
        # Satchel authored values: base 10, per-Mk 5 → 15% at Mk 1,
        # 20% at Mk 2 — the instance's Mk tier drives the ladder.
        defn = mem_bag_def(2, 10, 5)
        self.assertEqual(bag_pct(defn, 1), 15)
        self.assertEqual(bag_pct(defn, 2), 20)
        char = Character(stat_str=10)
        self.assertEqual(carry_capacity(char, [mem_bag(2, defn, 1)]), 115)
        self.assertEqual(carry_capacity(char, [mem_bag(3, defn, 2)]), 120)

    def test_multi_bag_percentages_sum_never_compound(self):
        # Two 20% bags → ×1.40 (sum), never ×1.44 (compound). Only BACK
        # ships today; the helper takes an equipped list, so the rule is
        # pinned here for the future hip slot.
        char = Character(stat_str=10)
        defn = mem_bag_def(4, 20, 0)
        bags = [mem_bag(4, defn, 1), mem_bag(5, defn, 1)]
        self.assertEqual(carry_capacity(char, bags), 140)

    def test_reference_case_str47_mk2_satchel(self):
        # The #215 reference: effective STR 47 (base 470) + Mk 2 Satchel
        # (20%) → 470 × 120 // 100 = 564 — +94 versus +20 under the old
        # flat bonus.
        char = Character(stat_str=47)
        satchel = mem_bag(6, mem_bag_def(6, 10, 5), mk_tier=2)
        self.assertEqual(carry_capacity(char, [satchel]), 564)

    def test_non_bag_items_contribute_no_percentage(self):
        char = Character(stat_str=10)
        armor_def = ItemDefinition(
            pk=7, name='Test Plate', slug='v2423-plate', item_type='armor',
            genre_tag='fantasy', valid_slots=['CHEST'],
            scaling_base=0.0, scaling_factor=0.0,
            carry_pct_base=50, carry_pct_per_mk=50,
        )
        plate = mem_bag(7, armor_def, mk_tier=1)
        self.assertEqual(carry_capacity(char, [plate]), 100)


class UnequipGuardTests(TransactionTestCase):
    """The guard's question — capacity without this bag — flows through
    the same helper, called with the reduced equipped list."""

    def _char_with_bag(self, prefix):
        zone, room = make_world(prefix)
        char = make_character(prefix, room)
        defn = ItemDefinition.objects.create(
            name='Guard Satchel', slug=f'{prefix}-guard-satchel',
            item_type='bag', genre_tag='fantasy', valid_slots=['BACK'],
            scaling_base=0.0, scaling_factor=0.0,
            carry_pct_base=10, carry_pct_per_mk=5,
        )
        bag = ItemInstance.objects.create(
            definition=defn, owner=char, mk_tier=1, rarity='common',
            durability_current=100.0, is_identified=True,
            is_equipped=True, equipped_slot='BACK',
        )
        return char, bag

    async def test_guard_refuses_when_removal_would_overflow(self):
        char, bag = await sync_to_async(self._char_with_bag)('pg1')
        consumer = make_stub_consumer(char, [])
        # STR 10 → bagless limit 100. Carrying 100 unequipped items,
        # removing the bag would put 101 over 100 → refuse.
        blocked = consumer._unequip_blocked_reason(bag, [bag], 100)
        self.assertIsNotNone(blocked)
        self.assertIn('too many items', blocked)

    async def test_guard_allows_when_room_remains(self):
        char, bag = await sync_to_async(self._char_with_bag)('pg2')
        consumer = make_stub_consumer(char, [])
        # 99 carried + the bag coming off = 100 ≤ the bagless limit 100.
        blocked = consumer._unequip_blocked_reason(bag, [bag], 99)
        self.assertIsNone(blocked)
