"""v24.10 Brief 1 (#127): the proc floor.

Floored proc composition — an authored, deterministic, rarity-blind floor
X = floor_base + floor_factor × mk_tier, snapshotted onto the instance at
drop time, paying randint(X, X + ⌈V⌉) on proc success while unfloored
procs keep the shipped randint(1, ⌈V⌉) path byte-identical. flame_factor
joins the proc family as its fourth member; examine renders the promise
parenthetical on floored entries only; the seed authors Flame Projector
and Dart Caster and enforces the primary-only-floor invariant.
"""

import io
import random as real_random

from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from apps.shyland.combat_utils import PROC_FACTOR_STATS, roll_gear_bonus_damage
from apps.shyland.consumers import SkylandConsumer
from apps.shyland.item_utils import generate_item_instance
from apps.shyland.management.commands.seed_world import floor_invariant_violations
from apps.shyland.models import ItemDefinition

from .test_command_revamp import make_character, make_stub_consumer, make_world
from .test_gear_combat import MemItem

RARITIES = ('common', 'uncommon', 'rare', 'epic', 'legendary')


def make_floored_def(**overrides):
    fields = dict(
        name='Test Flamer', slug='test-flamer', item_type='weapon',
        genre_tag='wasteland', valid_slots=['RANGED'], is_two_handed=True,
        scaling_base=5.0, scaling_factor=2.0, damage_spread=3.0,
        is_ranged=True,
        primary_stats=[
            {'stat': 'per', 'base': 2.0, 'factor': 0.8},
            {'stat': 'flame_factor', 'base': 2.0, 'factor': 1.0,
             'floor_base': 8.0, 'floor_factor': 4.0},
        ],
        secondary_stat_pool=[],
    )
    fields.update(overrides)
    return ItemDefinition.objects.create(**fields)


# ----------------------------------------------------------------------
# §4.1 — floor math at generation
# ----------------------------------------------------------------------

class FloorSnapshotTests(TestCase):

    def test_floor_is_deterministic_int_and_rarity_blind(self):
        defn = make_floored_def()
        for mk in (1, 2, 5):
            floors = []
            for rarity in RARITIES:
                inst = generate_item_instance(defn, mk, rarity)
                entry = next(e for e in inst.rolled_primary_stats
                             if e['stat'] == 'flame_factor')
                self.assertIn('floor', entry)
                self.assertIsInstance(entry['floor'], int)
                floors.append(entry['floor'])
            # X = 8 + 4 × mk, identical across all five rarities.
            self.assertEqual(floors, [8 + 4 * mk] * len(RARITIES))

    def test_value_still_varies_with_rarity_spread(self):
        defn = make_floored_def()
        values = {}
        with mock.patch('apps.shyland.item_utils.random') as rng:
            rng.uniform.side_effect = lambda a, b: b   # top of each spread
            for rarity in ('common', 'legendary'):
                inst = generate_item_instance(defn, 4, rarity)
                entry = next(e for e in inst.rolled_primary_stats
                             if e['stat'] == 'flame_factor')
                values[rarity] = entry['value']
                self.assertEqual(entry['floor'], 8 + 4 * 4)   # X unmoved
        self.assertNotEqual(values['common'], values['legendary'])

    def test_unfloored_primary_entries_carry_no_floor_key(self):
        defn = make_floored_def()
        inst = generate_item_instance(defn, 1, 'common')
        per = next(e for e in inst.rolled_primary_stats if e['stat'] == 'per')
        self.assertNotIn('floor', per)

    def test_generation_ignores_floor_keys_on_secondary_entries(self):
        # The seed invariant guarantees none exist; generation must not
        # silently honor a defect that slips past it.
        defn = make_floored_def(
            slug='test-flamer-corrupt',
            secondary_stat_pool=[
                {'stat': 'crit_chance', 'base': 0.5, 'factor': 0.2,
                 'floor_base': 3.0, 'floor_factor': 1.0}])
        inst = generate_item_instance(defn, 1, 'legendary')   # all-in-pool
        self.assertTrue(inst.rolled_secondary_stats)
        for entry in inst.rolled_secondary_stats:
            self.assertNotIn('floor', entry)


# ----------------------------------------------------------------------
# §4.2 / §4.6 — the floored payout path and the four-member family
# ----------------------------------------------------------------------

class FlooredProcRollTests(SimpleTestCase):

    def test_floored_success_pays_between_x_and_x_plus_ceil_v(self):
        items = [MemItem(primary=[
            {'stat': 'flame_factor', 'value': 4.2, 'floor': 12}])]
        with mock.patch('apps.shyland.combat_utils.random') as rng:
            rng.random.return_value = 0.0
            rng.randint.return_value = 15
            self.assertEqual(roll_gear_bonus_damage(items), 15)
            rng.randint.assert_called_once_with(12, 17)   # X, X + ceil(4.2)

    def test_unfloored_success_keeps_the_shipped_expression(self):
        items = [MemItem(secondary=[{'stat': 'bleed_factor', 'value': 3}])]
        with mock.patch('apps.shyland.combat_utils.random') as rng:
            rng.random.return_value = 0.0
            rng.randint.return_value = 2
            self.assertEqual(roll_gear_bonus_damage(items), 2)
            rng.randint.assert_called_once_with(1, 3)

    def test_real_draws_stay_inside_the_promise_inclusive(self):
        # Repeated-draw bounds check on the real RNG: V=2.0, X=5 → every
        # payout lands in [5, 7], both ends reachable.
        items = [MemItem(primary=[
            {'stat': 'flame_factor', 'value': 2.0, 'floor': 5}])]
        state = real_random.getstate()
        try:
            real_random.seed(1127)
            draws = [roll_gear_bonus_damage(items) for _ in range(2000)]
        finally:
            real_random.setstate(state)
        payouts = [d for d in draws if d]
        self.assertTrue(payouts)
        self.assertEqual(min(payouts), 5)
        self.assertEqual(max(payouts), 7)

    def test_chance_reads_v_only_floor_never_changes_it(self):
        # V=20 pins the 0.50 cap with or without a floor — the floor is
        # invisible to the chance gate.
        floored = [MemItem(primary=[
            {'stat': 'flame_factor', 'value': 20, 'floor': 12}])]
        with mock.patch('apps.shyland.combat_utils.random') as rng:
            rng.randint.return_value = 1
            rng.random.return_value = 0.49
            self.assertEqual(roll_gear_bonus_damage(floored), 1)
            rng.random.return_value = 0.51
            self.assertEqual(roll_gear_bonus_damage(floored), 0)

    def test_flame_factor_is_a_proc_family_member(self):
        items = [MemItem(secondary=[{'stat': 'flame_factor', 'value': 3}])]
        with mock.patch('apps.shyland.combat_utils.random') as rng:
            rng.random.return_value = 0.0
            rng.randint.return_value = 2
            self.assertEqual(roll_gear_bonus_damage(items), 2)
            rng.randint.assert_called_once_with(1, 3)

    def test_proc_family_is_exactly_the_four(self):
        self.assertEqual(PROC_FACTOR_STATS, (
            'bleed_factor', 'stun_factor', 'poison_factor', 'flame_factor'))


# ----------------------------------------------------------------------
# §4.3 / §4.4 — examine: the promise parenthetical, byte-identity
# ----------------------------------------------------------------------

class PromiseParentheticalTests(TestCase):

    def test_floored_stat_line_matches_the_ruled_example(self):
        line = SkylandConsumer._item_stat_line(
            {'stat': 'flame_factor', 'value': 4.2, 'floor': 12})
        self.assertEqual(line, '  Flame Factor: 4.2 (between 12 and 17 damage)')

    def test_unfloored_stat_lines_byte_identical(self):
        self.assertEqual(
            SkylandConsumer._item_stat_line(
                {'stat': 'bleed_factor', 'value': 3}),
            '  Bleed Factor: 3')
        self.assertEqual(
            SkylandConsumer._item_stat_line({'stat': 'per', 'value': 2}),
            '  Perception: 2')

    def test_examine_parenthetical_only_on_the_floored_entry(self):
        zone, room = make_world('pf')
        char = make_character('pf', room)
        defn = make_floored_def(slug='pf-flamer')
        inst = generate_item_instance(defn, 1, 'common', owner=char)
        inst.rolled_primary_stats = [
            {'stat': 'per', 'value': 3},
            {'stat': 'flame_factor', 'value': 4.2, 'floor': 12},
        ]
        inst.rolled_secondary_stats = [{'stat': 'crit_chance', 'value': 1}]
        inst.save()
        consumer = make_stub_consumer(char, [])
        lines = consumer._format_identified_item_lines(inst)
        self.assertIn('  Flame Factor: 4.2 (between 12 and 17 damage)', lines)
        self.assertIn('  Perception: 3', lines)
        self.assertIn('  Crit Chance: 1', lines)
        self.assertEqual(len([l for l in lines if 'between' in l]), 1)


# ----------------------------------------------------------------------
# §4.5 — the seed: the two authored weapons and the invariant checker
# ----------------------------------------------------------------------

class FloorInvariantCheckerTests(SimpleTestCase):

    def test_clean_specs_pass(self):
        self.assertEqual(floor_invariant_violations([
            ('flame-projector',
             [{'stat': 'flame_factor', 'base': 2.0, 'factor': 1.0,
               'floor_base': 8.0, 'floor_factor': 4.0}],
             [{'stat': 'crit_chance', 'base': 0.5, 'factor': 0.2}]),
            ('iron-sword',
             [{'stat': 'str', 'base': 3.0, 'factor': 1.0}],
             [{'stat': 'bleed_factor', 'base': 0.3, 'factor': 0.1}]),
        ]), [])

    def test_floor_on_a_secondary_entry_is_rejected(self):
        violations = floor_invariant_violations([
            ('bad-item', [],
             [{'stat': 'poison_factor', 'base': 0.5, 'factor': 0.2,
               'floor_base': 3.0, 'floor_factor': 1.0}]),
        ])
        self.assertEqual(len(violations), 1)
        self.assertIn('bad-item', violations[0])
        self.assertIn('secondary', violations[0])

    def test_floor_on_a_non_proc_primary_stat_is_rejected(self):
        violations = floor_invariant_violations([
            ('bad-item-2',
             [{'stat': 'str', 'base': 3.0, 'factor': 1.0,
               'floor_base': 2.0, 'floor_factor': 1.0}],
             []),
        ])
        self.assertEqual(len(violations), 1)
        self.assertIn('non-proc', violations[0])


class SeedFlooredWeaponsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # A passing run is itself the invariant proof: a floor violation
        # anywhere fails the seed's verification by name.
        call_command('seed_world', stdout=io.StringIO())

    def test_flame_projector_authors_the_ruled_table(self):
        fp = ItemDefinition.objects.get(slug='flame-projector')
        self.assertEqual(fp.item_type, 'weapon')
        self.assertEqual(fp.genre_tag, 'wasteland')
        self.assertEqual(fp.valid_slots, ['RANGED'])
        self.assertTrue(fp.is_two_handed)
        self.assertTrue(fp.is_ranged)
        self.assertTrue(fp.takes_durability_loss)
        self.assertEqual(
            (fp.scaling_base, fp.scaling_factor, fp.damage_spread),
            (5.0, 2.0, 3.0))
        self.assertEqual(fp.primary_stats, [
            {'stat': 'per', 'base': 2.0, 'factor': 0.8},
            {'stat': 'flame_factor', 'base': 2.0, 'factor': 1.0,
             'floor_base': 8.0, 'floor_factor': 4.0},
        ])
        self.assertEqual(fp.secondary_stat_pool, [
            {'stat': 'per', 'base': 1.0, 'factor': 0.4},
            {'stat': 'crit_chance', 'base': 0.5, 'factor': 0.2},
        ])

    def test_dart_caster_authors_the_ruled_table(self):
        dc = ItemDefinition.objects.get(slug='dart-caster')
        self.assertEqual(dc.item_type, 'weapon')
        self.assertEqual(dc.genre_tag, 'fantasy')
        self.assertEqual(dc.valid_slots, ['RANGED', 'MAIN_HAND'])
        self.assertFalse(dc.is_two_handed)
        self.assertTrue(dc.is_ranged)
        self.assertTrue(dc.takes_durability_loss)
        self.assertEqual(
            (dc.scaling_base, dc.scaling_factor, dc.damage_spread),
            (4.0, 1.8, 2.0))
        self.assertEqual(dc.primary_stats, [
            {'stat': 'dex', 'base': 2.0, 'factor': 0.8},
            {'stat': 'poison_factor', 'base': 2.0, 'factor': 1.0,
             'floor_base': 5.0, 'floor_factor': 3.0},
        ])
        self.assertEqual(dc.secondary_stat_pool, [
            {'stat': 'dex', 'base': 1.0, 'factor': 0.4},
            {'stat': 'crit_chance', 'base': 0.8, 'factor': 0.3},
        ])

    def test_floored_definitions_are_exactly_the_two(self):
        # The growth invariant, stated stably: the set of definitions
        # carrying any floor key is exactly the brief's two additions.
        floored = sorted(
            d.slug for d in ItemDefinition.objects.all()
            if any('floor_base' in e or 'floor_factor' in e
                   for e in (d.primary_stats or [])
                   + (d.secondary_stat_pool or [])))
        self.assertEqual(floored, ['dart-caster', 'flame-projector'])

    def test_reseed_adds_and_deletes_nothing(self):
        before = ItemDefinition.objects.count()
        slugs = set(ItemDefinition.objects.values_list('slug', flat=True))
        call_command('seed_world', stdout=io.StringIO())
        self.assertEqual(ItemDefinition.objects.count(), before)
        self.assertEqual(
            set(ItemDefinition.objects.values_list('slug', flat=True)), slugs)
