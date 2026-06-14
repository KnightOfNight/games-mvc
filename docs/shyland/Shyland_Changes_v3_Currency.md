# Shyland — Claude Code Change Brief v3
**Currency System — apply these changes to the existing codebase**

---

## What This Brief Covers

The currency system has been fully designed. This brief contains only the changes needed — nothing else has changed from the Session 1 kickoff brief.

---

## 1. Update the Character Model

The `Character` model currently has placeholder currency fields (`shards`, `marks`, `crowns`). Replace them with a single `bigint` field.

**Remove these fields:**
```python
shards = models.IntegerField(default=0)
marks = models.IntegerField(default=0)
crowns = models.IntegerField(default=0)
```

**Add this field:**
```python
copper = models.BigIntegerField(default=0)
# Stores ALL currency as a single integer in the base unit (copper).
# Display conversion is handled by the currency utility — never store
# silver/gold/platinum as separate fields.
```

Run `make makemigrations APP=shyland && make migrate` after this change.

---

## 2. Create the Currency Utility Module

Create a new file: `django/src/apps/shyland/currency.py`

This module handles all conversion and display logic. The engine always works in copper internally.

```python
"""
Shyland currency system.

All currency is stored as a single integer in copper (the base unit).
Tiers follow an escalating-multiplier pattern:

  Tier 1: Copper    — base unit (value: 1)
  Tier 2: Silver    — 1 silver  = 10 copper       (multiplier: ×10)
  Tier 3: Gold      — 1 gold    = 100 silver       (multiplier: ×100)
  Tier 4: Platinum  — 1 plat    = 1,000 gold       (multiplier: ×1,000)
  Tier 5: (future)              = 10,000 platinum  (multiplier: ×10,000)

The multiplier between tiers is itself multiplied by 10 at each step.

Value in copper:
  1 copper   = 1
  1 silver   = 10
  1 gold     = 1,000
  1 platinum = 1,000,000
"""

# Tier definitions: (engine_name, value_in_copper)
# Listed highest to lowest for display decomposition.
TIERS = [
    ("platinum", 1_000_000),
    ("gold",     1_000),
    ("silver",   10),
    ("copper",   1),
]

# Future tiers append here:
# ("tier5", 10_000_000_000),


def to_copper(platinum=0, gold=0, silver=0, copper=0):
    """Convert any combination of denominations to total copper."""
    return (
        platinum * 1_000_000 +
        gold     * 1_000 +
        silver   * 10 +
        copper   * 1
    )


def from_copper(total_copper):
    """
    Decompose a copper total into the minimum set of denominations.
    Returns a dict with only non-zero tiers.

    Example:
        from_copper(1_543) -> {"gold": 1, "silver": 54, "copper": 3}
        from_copper(10)    -> {"silver": 1}
        from_copper(7)     -> {"copper": 7}
    """
    if total_copper < 0:
        raise ValueError("Currency cannot be negative.")

    result = {}
    remainder = total_copper
    for name, value in TIERS:
        if remainder >= value:
            result[name] = remainder // value
            remainder %= value
    return result


def display(total_copper, currency_display=None):
    """
    Return a human-readable string for a copper total.

    currency_display: optional dict mapping engine tier names to local aliases.
    Example: {"copper": "Soul Token", "silver": "Grave Mark", "gold": "Death Crown"}

    Examples:
        display(1_543)                          -> "1 gold, 54 silver, 3 copper"
        display(10)                             -> "1 silver"
        display(0)                              -> "0 copper"
        display(1_543, {"copper": "Token", ...}) -> "1 Death Crown, 54 Grave Mark, 3 Token"
    """
    if total_copper == 0:
        zero_name = (currency_display or {}).get("copper", "copper")
        return f"0 {zero_name}"

    breakdown = from_copper(total_copper)
    parts = []
    for name, value in TIERS:
        if name in breakdown:
            display_name = (currency_display or {}).get(name, name)
            amount = breakdown[name]
            # Naive pluralisation — extend if local names need custom plural forms
            if amount != 1 and not display_name.endswith("s"):
                display_name = display_name + "s"
            parts.append(f"{amount} {display_name}")
    return ", ".join(parts)


def add(total_copper, amount_copper):
    """Add currency. Returns new total. Amount must be non-negative."""
    if amount_copper < 0:
        raise ValueError("Use subtract() to remove currency.")
    return total_copper + amount_copper


def subtract(total_copper, amount_copper):
    """
    Subtract currency. Returns new total.
    Raises ValueError if the result would be negative (insufficient funds).
    """
    if amount_copper < 0:
        raise ValueError("Amount must be non-negative.")
    if amount_copper > total_copper:
        raise ValueError("Insufficient funds.")
    return total_copper - amount_copper


def can_afford(total_copper, cost_copper):
    """Return True if total_copper >= cost_copper."""
    return total_copper >= cost_copper
```

---

## 3. Local Currency Display Configs

Create a small registry of zone-specific currency display aliases.

Add this to `currency.py` beneath the utility functions:

```python
# Zone local currency display aliases.
# Key: zone slug (matches Zone.slug in the database).
# Value: dict mapping engine tier names to local display names.
# Zones not listed here use standard names.
ZONE_CURRENCY_DISPLAY = {
    "ashenveil-cathedral": {
        "copper": "Soul Token",
        "silver": "Grave Mark",
        "gold":   "Death Crown",
        # platinum intentionally omitted — too rare to need an alias here
    },
    "the-neon-sprawl": {
        "copper": "Credit",
        "silver": "Kilocredit",
        "gold":   "Megacredit",
    },
    # Add more zones here as they are built.
}


def display_for_zone(total_copper, zone_slug):
    """
    Display currency using zone-appropriate local names if defined,
    otherwise fall back to standard names.
    """
    currency_display = ZONE_CURRENCY_DISPLAY.get(zone_slug)
    return display(total_copper, currency_display)
```

---

## 4. Wire Currency Into the Consumer

In `django/src/apps/shyland/consumers.py`, add a helper that formats the player's wallet for display:

```python
from apps.shyland.currency import display_for_zone

def format_wallet(character):
    """Return a display string for the character's current currency."""
    zone_slug = character.current_room.zone.slug if character.current_room else None
    return display_for_zone(character.copper, zone_slug)
```

Use `format_wallet(character)` wherever currency needs to be shown to the player — looting, vendor transactions, the `inventory` command, etc.

---

## 5. Write Tests

Create `django/src/apps/shyland/tests/test_currency.py`:

```python
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
```

Run with: `make shell` then `python manage.py test apps.shyland.tests.test_currency`

---

## 6. Admin Display

In `django/src/apps/shyland/admin.py`, add a read-only display field on the Character admin so staff see a human-readable wallet alongside the raw `copper` integer:

```python
from apps.shyland.currency import display as currency_display

class CharacterAdmin(admin.ModelAdmin):
    readonly_fields = ("wallet_display",)

    def wallet_display(self, obj):
        return currency_display(obj.copper)
    wallet_display.short_description = "Wallet"
```

---

## Summary of Files Changed / Created

| File | Action |
|---|---|
| `apps/shyland/models.py` | Remove `shards`, `marks`, `crowns`. Add `copper` BigIntegerField. |
| `apps/shyland/currency.py` | **New file.** Full currency utility module. |
| `apps/shyland/consumers.py` | Add `format_wallet()` helper. Import `display_for_zone`. |
| `apps/shyland/admin.py` | Add `wallet_display` readonly field to CharacterAdmin. |
| `apps/shyland/tests/test_currency.py` | **New file.** Full test suite for currency module. |
| Migration | Run `make makemigrations APP=shyland && make migrate` |

---

## Design Rules — Do Not Deviate From These

- **Never store silver, gold, or platinum as separate fields.** One `copper` BigIntegerField only.
- **Never do currency math in the consumer or views.** All math goes through `currency.py` functions.
- **Never let copper go negative.** `subtract()` raises `ValueError` on insufficient funds — catch it and send the player an error message.
- **Local currency is display-only.** It converts to copper on pickup. The wallet always stores copper.
- **The multiplier pattern is fixed:** copper=1, silver=10, gold=1,000, platinum=1,000,000. Do not change these values.

---

*Change Brief v3 — Currency System*
*Applies on top of Session 1 (Kickoff Brief v1)*
