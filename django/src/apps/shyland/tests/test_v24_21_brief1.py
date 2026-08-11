"""v24.21 Brief 1 (#201): floored weapon pricing.

The two floored-proc weapons carry authored base_values — Flame Projector
85, Dart Caster 70 (ruled 2026-08-05) — instead of the type-wide 25
back-fill they previously fell into. Pins the seeded values and the
derived value/sale prices through the real arithmetic.
"""

import io

from django.core.management import call_command
from django.test import TestCase

from apps.shyland.item_utils import get_item_value, get_sale_price
from apps.shyland.models import ItemDefinition, ItemInstance


class FlooredWeaponPricingTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command('seed_world', stdout=io.StringIO())

    def mk1_common(self, slug):
        return ItemInstance(
            definition=ItemDefinition.objects.get(slug=slug),
            mk_tier=1,
            rarity=ItemInstance.COMMON,
        )

    def test_flame_projector_base_value(self):
        self.assertEqual(
            ItemDefinition.objects.get(slug='flame-projector').base_value, 85)

    def test_dart_caster_base_value(self):
        self.assertEqual(
            ItemDefinition.objects.get(slug='dart-caster').base_value, 70)

    def test_flame_projector_derived_prices(self):
        item = self.mk1_common('flame-projector')
        self.assertEqual(get_item_value(item), 85)
        self.assertEqual(get_sale_price(item), 28)

    def test_dart_caster_derived_prices(self):
        item = self.mk1_common('dart-caster')
        self.assertEqual(get_item_value(item), 70)
        self.assertEqual(get_sale_price(item), 23)
