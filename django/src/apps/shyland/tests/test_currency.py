from django.test import TestCase
from apps.shyland.currency import (
    to_copper, from_copper, display, add, subtract, can_afford
)


class CurrencyConversionTests(TestCase):

    def test_to_copper_single_tier(self):
        self.assertEqual(to_copper(copper=7), 7)
        self.assertEqual(to_copper(silver=1), 10)
        self.assertEqual(to_copper(gold=1), 1_000)
        self.assertEqual(to_copper(platinum=1), 1_000_000)

    def test_to_copper_mixed(self):
        self.assertEqual(to_copper(gold=1, silver=54, copper=3), 1_543)

    def test_from_copper_exact_tier(self):
        self.assertEqual(from_copper(10), {"silver": 1})
        self.assertEqual(from_copper(1_000), {"gold": 1})
        self.assertEqual(from_copper(1_000_000), {"platinum": 1})

    def test_from_copper_mixed(self):
        self.assertEqual(from_copper(1_543), {"gold": 1, "silver": 54, "copper": 3})

    def test_from_copper_zero(self):
        self.assertEqual(from_copper(0), {})

    def test_display_standard(self):
        self.assertEqual(display(0), "0 copper")
        self.assertEqual(display(7), "7 coppers")
        self.assertEqual(display(10), "1 silver")
        self.assertEqual(display(1_543), "1 gold, 54 silvers, 3 coppers")
        self.assertEqual(display(1_000_000), "1 platinum")

    def test_display_local_currency(self):
        aliases = {"copper": "Soul Token", "silver": "Grave Mark", "gold": "Death Crown"}
        self.assertEqual(display(1_543, aliases), "1 Death Crown, 54 Grave Marks, 3 Soul Tokens")

    def test_add(self):
        self.assertEqual(add(100, 50), 150)

    def test_subtract_success(self):
        self.assertEqual(subtract(100, 50), 50)

    def test_subtract_exact(self):
        self.assertEqual(subtract(100, 100), 0)

    def test_subtract_insufficient(self):
        with self.assertRaises(ValueError):
            subtract(50, 100)

    def test_can_afford(self):
        self.assertTrue(can_afford(100, 100))
        self.assertTrue(can_afford(100, 50))
        self.assertFalse(can_afford(50, 100))

    def test_negative_add_raises(self):
        with self.assertRaises(ValueError):
            add(100, -1)

    def test_negative_subtract_raises(self):
        with self.assertRaises(ValueError):
            subtract(100, -1)

    def test_negative_from_copper_raises(self):
        with self.assertRaises(ValueError):
            from_copper(-1)
