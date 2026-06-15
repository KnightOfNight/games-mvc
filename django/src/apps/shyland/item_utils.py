import random

from .models import ItemInstance

RARITY_SPREAD = {
    'common':    (0.85, 1.00),
    'uncommon':  (0.90, 1.05),
    'rare':      (0.95, 1.10),
    'epic':      (1.00, 1.15),
    'legendary': (1.05, 1.20),
}

RARITY_SECONDARY_SLOTS = {
    'common':    0,
    'uncommon':  1,
    'rare':      2,
    'epic':      3,
    'legendary': None,  # all entries in pool
    'artifact':  None,  # hand-authored; caller should not use this function
}


def _roll_stat(base, factor, mk_tier, rarity):
    midpoint = base + (factor * mk_tier)
    lo, hi = RARITY_SPREAD[rarity]
    return round(random.uniform(midpoint * lo, midpoint * hi))


def generate_item_instance(definition, mk_tier, rarity, owner=None, room=None):
    """
    Generate (but do not save) an ItemInstance from a definition at a given Mk tier and rarity.
    Call .save() on the returned instance to persist it.
    Artifact instances must not be passed through this function — create them manually.
    """
    rolled_primary = [
        {'stat': s['stat'], 'value': _roll_stat(s['base'], s['factor'], mk_tier, rarity)}
        for s in definition.primary_stats
    ]

    pool = definition.secondary_stat_pool
    slots = RARITY_SECONDARY_SLOTS.get(rarity, 0)
    if slots is None:
        sample = list(pool)
    elif slots == 0 or not pool:
        sample = []
    else:
        sample = random.sample(pool, min(slots, len(pool)))

    rolled_secondary = [
        {'stat': s['stat'], 'value': _roll_stat(s['base'], s['factor'], mk_tier, rarity)}
        for s in sample
    ]

    damage_midpoint = None
    damage_spread = None
    if definition.item_type == 'weapon':
        raw_midpoint = definition.scaling_base + (definition.scaling_factor * mk_tier)
        lo, hi = RARITY_SPREAD[rarity]
        damage_midpoint = random.uniform(raw_midpoint * lo, raw_midpoint * hi)
        damage_spread = definition.damage_spread

    return ItemInstance(
        definition=definition,
        owner=owner,
        current_room=room,
        mk_tier=mk_tier,
        rarity=rarity,
        rolled_primary_stats=rolled_primary,
        rolled_secondary_stats=rolled_secondary,
        damage_midpoint=damage_midpoint,
        damage_spread=damage_spread,
        is_soulbound=owner is not None,
        soulbound_to=owner if owner is not None else None,
    )


def get_durability_penalty(item):
    """Return the performance penalty multiplier for an ItemInstance based on current durability."""
    if not item.definition.takes_durability_loss:
        return 0.0
    pct = item.durability_current
    for entry in item.definition.durability_table:
        if entry['min'] <= pct <= entry['max']:
            return entry['penalty']
    return 1.0
