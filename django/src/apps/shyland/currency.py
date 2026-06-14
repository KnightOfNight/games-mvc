"""
Shyland currency system.

All currency is stored as a single integer in copper (the base unit).
Tiers follow an escalating-multiplier pattern:

  Tier 1: Copper    — base unit (value: 1)
  Tier 2: Silver    — 1 silver  = 10 copper       (multiplier: ×10)
  Tier 3: Gold      — 1 gold    = 100 silver       (multiplier: ×100)
  Tier 4: Platinum  — 1 plat    = 1,000 gold       (multiplier: ×1,000)
  Tier 5: (future)              = 10,000 platinum  (multiplier: ×10,000)

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
        display(1_543)                           -> "1 gold, 54 silvers, 3 coppers"
        display(10)                              -> "1 silver"
        display(0)                               -> "0 copper"
        display(1_543, {"copper": "Token", ...}) -> "1 Death Crown, 54 Grave Marks, 3 Tokens"
    """
    if total_copper == 0:
        zero_name = (currency_display or {}).get("copper", "copper")
        return f"0 {zero_name}"

    breakdown = from_copper(total_copper)
    parts = []
    for name, _ in TIERS:
        if name in breakdown:
            display_name = (currency_display or {}).get(name, name)
            amount = breakdown[name]
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


# ---------------------------------------------------------------------------
# Zone local currency display aliases
# ---------------------------------------------------------------------------

# Key: zone slug (matches Zone.slug in the database).
# Value: dict mapping engine tier names to local display names.
# Zones not listed here use standard names.
ZONE_CURRENCY_DISPLAY = {
    "ashenveil-cathedral": {
        "copper": "Soul Token",
        "silver": "Grave Mark",
        "gold":   "Death Crown",
    },
    "the-neon-sprawl": {
        "copper": "Credit",
        "silver": "Kilocredit",
        "gold":   "Megacredit",
    },
}


def display_for_zone(total_copper, zone_slug):
    """
    Display currency using zone-appropriate local names if defined,
    otherwise fall back to standard names.
    """
    currency_display = ZONE_CURRENCY_DISPLAY.get(zone_slug)
    return display(total_copper, currency_display)
