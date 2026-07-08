import random

from .models import ItemInstance

SLOT_DISPLAY_NAMES = {
    'MAIN_HAND':  'Main Hand',
    'OFF_HAND':   'Off Hand',
    'RANGED':     'Ranged',
    'HEAD':       'Head',
    'NECK':       'Neck',
    'SHOULDERS':  'Shoulders',
    'CHEST':      'Chest',
    'HANDS':      'Hands',
    'WAIST':      'Waist',
    'LEGS':       'Legs',
    'FEET':       'Feet',
    'RING':       'Ring',
    'BACK':       'Back',
}

STAT_LABELS = {
    'str': 'Strength',
    'dex': 'Dexterity',
    'end': 'Endurance',
    'int': 'Intelligence',
    'wis': 'Wisdom',
    'per': 'Perception',
}

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

RARITY_VALUE_MULTIPLIERS = {
    'common': 1, 'uncommon': 2, 'rare': 4,
    'epic': 8, 'legendary': 16, 'artifact': 32,
}


def get_item_value(item):
    """Full worth in copper: base_value × mk_tier × rarity multiplier."""
    mult = RARITY_VALUE_MULTIPLIERS.get(item.rarity, 1)
    return item.definition.base_value * item.mk_tier * mult


def get_sale_price(item):
    """What a vendor pays: one third of value, minimum 1 copper."""
    return max(1, get_item_value(item) // 3)


def get_repair_cost(item):
    """Cost per repair attempt: value × missing durability × 50%, min 1."""
    missing = 1.0 - (item.durability_current / 100.0)
    return max(1, int(get_item_value(item) * missing * 0.5))


def get_repair_success_chance(item):
    """20% at zero durability, ~95% near full."""
    return 0.20 + ((item.durability_current / 100.0) * 0.75)


def _roll_stat(base, factor, mk_tier, rarity):
    midpoint = base + (factor * mk_tier)
    lo, hi = RARITY_SPREAD[rarity]
    return round(random.uniform(midpoint * lo, midpoint * hi))


def generate_item_instance(definition, mk_tier, rarity, owner=None, room=None, gift=False):
    """
    Generate (but do not save) an ItemInstance from a definition at a given Mk tier and rarity.
    Call .save() on the returned instance to persist it.
    Artifact instances must not be passed through this function — create them manually.
    Pass gift=True when an admin is deliberately giving an item — soulbinds immediately.
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

    is_soulbound = bool(owner and gift)
    soulbound_to = owner if (owner and gift) else None

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
        is_soulbound=is_soulbound,
        soulbound_to=soulbound_to,
    )


def format_slot_name(slot_str):
    return SLOT_DISPLAY_NAMES.get(slot_str.upper(), slot_str.title())


def get_display_name(item):
    """
    Return the name to show a player for this item instance.
    Identified items show the real definition name; unidentified show mystery name or fallback.
    """
    if item.is_identified:
        return item.definition.name
    mystery = item.definition.mystery_name.strip()
    if mystery:
        return mystery
    return f"an unidentified {item.definition.item_type}"


def get_display_name_with_tier(item):
    """
    Display name plus Mk tier suffix, honoring suppress_mk_suffix.
    Unidentified items never show a tier.
    """
    name = get_display_name(item)
    if not item.is_identified:
        return name
    if item.definition.suppress_mk_suffix:
        return name
    return f"{name} Mk {item.mk_tier}"


def get_display_description(item):
    """
    Return the description to show a player for this item instance.
    Identified items show the real description; unidentified show mystery description or fallback.
    """
    if item.is_identified:
        return item.definition.description
    mystery = item.definition.mystery_description.strip()
    if mystery:
        return mystery
    return "You can't determine anything about this item."


def parse_item_noun(noun_str, item_list):
    """
    Parse a classic MUD item noun against a list of ItemInstance objects.

    Returns:
        ('all', None)              if noun_str == 'all'
        ('single', ItemInstance)   if a match is found
        ('not_found', None)        if no match
        ('bad_index', None)        if N.keyword has N out of range

    Matching is against get_display_name(item) so mystery names work.
    """
    noun_str = noun_str.strip().lower()

    if noun_str == 'all':
        return ('all', None)

    index = 1
    keyword = noun_str
    if '.' in noun_str:
        parts = noun_str.split('.', 1)
        if parts[0].isdigit():
            index = int(parts[0])
            keyword = parts[1]

    matches = [
        item for item in item_list
        if keyword in get_display_name(item).lower()
    ]

    if not matches:
        return ('not_found', None)
    if index > len(matches):
        return ('bad_index', None)

    return ('single', matches[index - 1])


def get_durability_penalty(item):
    """Return the performance penalty multiplier for an ItemInstance based on current durability."""
    if not item.definition.takes_durability_loss:
        return 0.0
    pct = item.durability_current
    for entry in item.definition.durability_table:
        if entry['min'] <= pct <= entry['max']:
            return entry['penalty']
    return 1.0


def generate_loot_from_table(loot_table, mk_tier):
    """
    Roll a LootTable at the given mk_tier.
    Returns a list of unsaved ItemInstance objects (caller must set corpse and call .save()).

    Ungrouped entries (guaranteed_group blank) each make an independent
    drop_chance roll. Entries sharing a guaranteed_group label yield exactly
    one drop per group per roll, chosen with drop_chance as relative weight.
    """
    entries = loot_table.entries.select_related('item_definition').all()

    ungrouped = []
    groups = {}
    for entry in entries:
        if entry.guaranteed_group:
            groups.setdefault(entry.guaranteed_group, []).append(entry)
        else:
            ungrouped.append(entry)

    dropped = [e for e in ungrouped if random.random() <= e.drop_chance]
    for group_entries in groups.values():
        weights = [e.drop_chance for e in group_entries]
        dropped.append(random.choices(group_entries, weights=weights, k=1)[0])

    results = []
    for entry in dropped:
        tier = max(entry.mk_tier_min, min(mk_tier, entry.mk_tier_max))

        rarities = list(entry.rarity_weights.keys())
        weights  = list(entry.rarity_weights.values())
        rarity   = random.choices(rarities, weights=weights, k=1)[0]

        instance = generate_item_instance(
            definition=entry.item_definition,
            mk_tier=tier,
            rarity=rarity,
        )
        results.append(instance)

    return results


def create_corpse(npc_instance, killer):
    """
    Create a Corpse for a dead NpcInstance.
    Rolls loot table and copper drop. Saves corpse and all loot items.
    Returns the saved Corpse.
    Must be called from within a @database_sync_to_async wrapper when used from the consumer.
    """
    import random as _random
    from datetime import timedelta
    from django.utils import timezone
    from .models import Corpse, CORPSE_DECAY_MINUTES

    definition = npc_instance.definition
    mk_tier    = npc_instance.mk_tier

    copper = 0
    if definition.currency_drop_max > 0:
        copper = _random.randint(
            definition.currency_drop_min * mk_tier,
            definition.currency_drop_max * mk_tier,
        )

    corpse = Corpse.objects.create(
        npc_definition=definition,
        npc_name_snapshot=definition.name,
        current_room=npc_instance.current_room,
        killed_by=killer,
        decay_at=timezone.now() + timedelta(minutes=CORPSE_DECAY_MINUTES),
        copper_drop=copper,
    )

    if definition.loot_table_id:
        items = generate_loot_from_table(definition.loot_table, mk_tier)
        for item in items:
            item.corpse = corpse
            item.save()

    return corpse


def parse_corpse_noun(noun_str, corpse_list):
    """
    Parse MUD noun syntax against a list of Corpse objects.
    Matching is case-insensitive against corpse.display_name.

    Returns:
      ('single', corpse)   — matched one corpse
      ('not_found', None)  — no match
      ('bad_index', None)  — N.keyword where N exceeds matches
    """
    if not noun_str:
        return ('not_found', None)

    noun_str = noun_str.strip().lower()

    index = 1
    keyword = noun_str
    if '.' in noun_str:
        parts = noun_str.split('.', 1)
        try:
            index = int(parts[0])
            keyword = parts[1]
        except ValueError:
            pass

    matches = [c for c in corpse_list if keyword in c.display_name.lower()]

    if not matches:
        return ('not_found', None)
    if index > len(matches):
        return ('bad_index', None)
    return ('single', matches[index - 1])
