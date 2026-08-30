"""V24.28 Brief 1 (#211, #245): the tier-material ladder.

Eight rungs, copper through sphaerium, twelve accessories each. On this
ladder the material name IS the tier display, so generation is range-bound:
a definition carrying tier_material_mk_min may only be instantiated inside
its rung. Sphaerium is the terminal rung and the only unbounded one — its
range has no ceiling, which is exactly why it is the one rung that keeps
its Mk suffix.

The central invariant is one curve for the whole ladder: every rung carries
stat authorship identical to its copper counterpart, and the engine's
midpoint = base + factor x mk_tier does all the tier progression.
"""

import io

from django.core.management import call_command
from django.test import TestCase

from apps.shyland.item_utils import (
    generate_item_instance, get_display_name_with_tier,
)
from apps.shyland.models import (
    ItemDefinition, ItemInstance, LootTableEntry, VendorEntry,
)

MATERIALS = [
    ('copper', 1, 1, True),
    ('silver', 2, 2, True),
    ('gold', 3, 3, True),
    ('platinum', 4, 4, True),
    ('rhodium', 5, 5, True),
    ('iridium', 6, 6, True),
    ('osmium', 7, 7, True),
    ('sphaerium', 8, None, False),
]

STATS = ('strength', 'dexterity', 'endurance',
         'intelligence', 'wisdom', 'perception')

FORMS = ('ring', 'amulet')


class LadderSchemaTests(TestCase):
    """§6.1: the range fields exist, are nullable, and default to None."""

    def test_range_fields_exist_and_are_nullable(self):
        for name in ('tier_material_mk_min', 'tier_material_mk_max'):
            field = ItemDefinition._meta.get_field(name)
            self.assertTrue(field.null, f'{name} must be nullable')
            self.assertTrue(field.blank, f'{name} must be blank-able')

    def test_a_definition_created_without_them_defaults_to_none(self):
        definition = ItemDefinition.objects.create(
            slug='schema-pin-widget', name='Schema Pin Widget',
            item_type='accessory', genre_tag='fantasy',
            description='A widget that exists only to pin the schema.',
            scaling_base=2.0, scaling_factor=0.8,
            # v25.12 (#311): explicit all-worn band — preserves the
            # retired empty-table fallback these fixtures ran under.
            durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
        )
        definition.refresh_from_db()
        self.assertIsNone(definition.tier_material_mk_min)
        self.assertIsNone(definition.tier_material_mk_max)


class GuardTests(TestCase):
    """§6.2-6.6: the Mk-mismatch guard in generate_item_instance."""

    def make_definition(self, slug, mk_min, mk_max):
        return ItemDefinition.objects.create(
            slug=slug, name=slug.replace('-', ' ').title(),
            item_type='accessory', genre_tag='fantasy',
            description='A guard fixture.',
            scaling_base=2.0, scaling_factor=0.8,
            valid_slots=['RING'],
            primary_stats=[{'stat': 'str', 'base': 0.7, 'factor': 2.1}],
            secondary_stat_pool=[],
            tier_material_mk_min=mk_min, tier_material_mk_max=mk_max,
            durability_table=[{'min': 0, 'max': 100, 'penalty': 1.0}],
        )

    def generate(self, definition, mk_tier):
        return generate_item_instance(
            definition, mk_tier, ItemInstance.COMMON)

    def test_guard_raises_outside_the_rung(self):
        definition = self.make_definition('guard-bound-1-1', 1, 1)
        with self.assertRaises(ValueError) as ctx:
            self.generate(definition, 2)
        message = str(ctx.exception)
        self.assertIn('guard-bound-1-1', message)   # names the slug
        self.assertIn('Mk 1', message)              # names the bound
        self.assertIn('at Mk 2', message)           # names the offending tier

    def test_guard_passes_inside_the_rung(self):
        definition = self.make_definition('guard-pass-1-1', 1, 1)
        instance = self.generate(definition, 1)
        self.assertEqual(instance.mk_tier, 1)

    def test_guard_is_inert_off_the_ladder(self):
        definition = self.make_definition('guard-off-ladder', None, None)
        for mk_tier in (1, 2, 5):
            instance = self.generate(definition, mk_tier)
            self.assertEqual(instance.mk_tier, mk_tier)

    def test_guard_across_the_bounded_rungs(self):
        """§6.5: each bounded rung generates at its own tier and refuses
        every other tier in 1-8."""
        for rung in range(1, 8):
            definition = self.make_definition(f'guard-rung-{rung}', rung, rung)
            instance = self.generate(definition, rung)
            self.assertEqual(instance.mk_tier, rung)
            for other in range(1, 9):
                if other == rung:
                    continue
                with self.assertRaises(ValueError, msg=f'rung {rung} at Mk {other}'):
                    self.generate(definition, other)

    def test_the_unbounded_rung(self):
        """§6.6: sphaerium's shape — refuses below Mk 8, generates at every
        tier above it, forever. This is the ruling's infinity property."""
        definition = self.make_definition('guard-unbounded', 8, None)
        for below in range(1, 8):
            with self.assertRaises(ValueError, msg=f'unbounded rung at Mk {below}'):
                self.generate(definition, below)
        for at_or_above in (8, 15, 200):
            instance = self.generate(definition, at_or_above)
            self.assertEqual(instance.mk_tier, at_or_above)

    def test_unbounded_bound_renders_as_an_open_range(self):
        definition = self.make_definition('guard-unbounded-msg', 8, None)
        with self.assertRaises(ValueError) as ctx:
            self.generate(definition, 7)
        self.assertIn('Mk 8+', str(ctx.exception))


class SeededLadderTests(TestCase):
    """§6.7-6.13: the seeded ladder itself."""

    @classmethod
    def setUpTestData(cls):
        call_command('seed_world', stdout=io.StringIO())

    def ladder(self):
        return ItemDefinition.objects.filter(tier_material_mk_min__isnull=False)

    def test_ladder_completeness(self):
        """§6.7: 96 definitions, twelve at each minimum 1-8, and every
        expected slug present."""
        self.assertEqual(self.ladder().count(), 96)
        for material, mk_min, _mk_max, _suppress in MATERIALS:
            self.assertEqual(
                self.ladder().filter(tier_material_mk_min=mk_min).count(), 12,
                f'{material} rung should hold twelve definitions')
            for form in FORMS:
                for stat in STATS:
                    slug = f'{material}-{form}-of-{stat}'
                    self.assertTrue(
                        ItemDefinition.objects.filter(slug=slug).exists(),
                        f'missing ladder definition {slug}')

    def test_range_and_suffix_shape(self):
        """§6.8: rungs 1-7 are single tiers that suppress; sphaerium is
        unbounded and does not."""
        for material, mk_min, mk_max, suppress in MATERIALS:
            rung = self.ladder().filter(tier_material_mk_min=mk_min)
            for definition in rung:
                self.assertEqual(definition.tier_material_mk_max, mk_max,
                                 f'{definition.slug} range shape')
                self.assertIs(definition.suppress_mk_suffix, suppress,
                              f'{definition.slug} suffix shape')
        unbounded = self.ladder().filter(tier_material_mk_max__isnull=True)
        self.assertEqual(unbounded.count(), 12)
        for definition in unbounded:
            self.assertTrue(definition.slug.startswith('sphaerium-'))

    def test_one_curve_equality(self):
        """§6.9: every rung's stat authorship equals copper's, for every
        stat and both forms. The ruling's central invariant."""
        for form in FORMS:
            for stat in STATS:
                copper = ItemDefinition.objects.get(
                    slug=f'copper-{form}-of-{stat}')
                for material, _lo, _hi, _suppress in MATERIALS:
                    definition = ItemDefinition.objects.get(
                        slug=f'{material}-{form}-of-{stat}')
                    self.assertEqual(
                        definition.primary_stats, copper.primary_stats,
                        f'{definition.slug} primary_stats differ from copper')
                    self.assertEqual(
                        definition.secondary_stat_pool,
                        copper.secondary_stat_pool,
                        f'{definition.slug} secondary pool differs from copper')

    def test_tier_progression(self):
        """§6.10: the engine's midpoint does the climbing — 2.8 at copper's
        Mk 1, 4.9 at silver's Mk 2, 15.4 at osmium's Mk 7, 32.2 for a
        sphaerium piece at Mk 15."""
        expected = [
            ('copper-ring-of-strength', 1, 2.8),
            ('silver-ring-of-strength', 2, 4.9),
            ('osmium-ring-of-strength', 7, 15.4),
            ('sphaerium-ring-of-strength', 15, 32.2),
        ]
        for slug, mk_tier, midpoint in expected:
            entry = ItemDefinition.objects.get(slug=slug).primary_stats[0]
            self.assertAlmostEqual(
                entry['base'] + entry['factor'] * mk_tier, midpoint, places=6,
                msg=f'{slug} at Mk {mk_tier}')

    def test_display_suppression_across_the_ladder(self):
        """§6.11: rungs 1-7 render with no Mk suffix; sphaerium carries its
        number, because its rung alone cannot say the tier by name."""
        for material, mk_min, _mk_max, suppress in MATERIALS:
            if not suppress:
                continue
            definition = ItemDefinition.objects.get(
                slug=f'{material}-ring-of-strength')
            instance = generate_item_instance(
                definition, mk_min, ItemInstance.COMMON)
            self.assertEqual(
                get_display_name_with_tier(instance),
                f'{material.title()} Ring of Strength')

        sphaerium = ItemDefinition.objects.get(slug='sphaerium-ring-of-strength')
        instance = generate_item_instance(sphaerium, 15, ItemInstance.COMMON)
        self.assertEqual(get_display_name_with_tier(instance),
                         'Sphaerium Ring of Strength Mk 15')

    def test_suppression_is_not_membership(self):
        """§6.12: the two facts are independent in both directions."""
        for slug in ('tarnished-band', 'cloudy-glass-pendant'):
            freebie = ItemDefinition.objects.get(slug=slug)
            self.assertTrue(freebie.suppress_mk_suffix,
                            f'{slug} suppresses the suffix')
            self.assertIsNone(freebie.tier_material_mk_min,
                              f'{slug} is off the ladder')
        sphaerium = ItemDefinition.objects.get(slug='sphaerium-amulet-of-wisdom')
        self.assertEqual(sphaerium.tier_material_mk_min, 8)
        self.assertFalse(sphaerium.suppress_mk_suffix)

    def test_no_drop_or_vendor_exposure_above_copper(self):
        """§6.13: the seven new rungs are prep work — Z02-Z08 do not exist
        yet, so nothing above copper drops or is stocked anywhere."""
        above_copper = self.ladder().filter(tier_material_mk_min__gt=1)
        self.assertEqual(above_copper.count(), 84)
        self.assertFalse(
            LootTableEntry.objects.filter(
                item_definition__in=above_copper).exists(),
            'no ladder definition above copper may appear in a loot table')
        self.assertFalse(
            VendorEntry.objects.filter(
                item_definition__in=above_copper).exists(),
            'no ladder definition above copper may be stocked by a vendor')
