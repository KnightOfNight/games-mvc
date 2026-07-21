import math
import random

TO_HIT_DEFENSE_BASE = 10   # static defense = base + defender DEX
GRAZE_WINDOW = 3           # miss the defense by 1..GRAZE_WINDOW -> graze
CRIT_BASE = 0.05           # critical chance floor on any successful hit
CRIT_PER_DEX_ADVANTAGE = 0.01
CRIT_CAP = 0.25

# v22 B5 (#100): the Option C armor table — slot weight × Mk tier over worn
# armor pieces, summed with rolled physical_resist, is the character's TAV.
# Derived weights, not authored per-item bases; this table retires gracefully
# if authored armor fields ever ship (#129). Only these eight slots carry
# armor per the knob survey. Full set = 13 per Mk tier.
ARMOR_SLOT_WEIGHTS = {
    'CHEST': 3, 'HEAD': 2, 'LEGS': 2, 'OFF_HAND': 2,
    'SHOULDERS': 1, 'HANDS': 1, 'WAIST': 1, 'FEET': 1,
}
ARMOR_MITIGATION_K = 48    # mitigation fraction = TAV / (TAV + K)

# v22 B5 (#68/#100): proc factors — the rolled value V does double duty:
# chance = V × PROC_CHANCE_PER_POINT (capped), size = randint(1, ceil(V)).
PROC_CHANCE_PER_POINT = 0.05
PROC_CHANCE_CAP = 0.50
PROC_FACTOR_STATS = ('bleed_factor', 'stun_factor', 'poison_factor')

PRIMARY_STAT_KEYS = ('str', 'dex', 'end', 'int', 'wis', 'per')

# v19 brief 7: NPC contest stats scale additively on the same curve players
# climb (contests add; quantities like vitality multiply).
NPC_CONTEST_BASE = 18        # matches a level-1 player's primary stat
NPC_CONTEST_STEP = 2.5       # per level, matches player primary-stat growth
NPC_TIER_OFFSET = {'normal': 0, 'elite': 2, 'boss': 2}   # blessed: 55% / 45% / 45% at-level hit
MK_LEVEL_SPAN = 10           # each Mk tier spans 10 levels (matches the item system's bands)

ORDINALS = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth']


def _capitalize_first(text):
    return text[0].upper() + text[1:] if text else text


def npc_display(npc, capitalize=False, introduction=False):
    """v20 brief 5 (#24): THE composer for every player-visible NPC
    reference. Accepts an NpcInstance or an NpcDefinition. plural_phrase
    verbatim when set; else article + name; else the bare name (proper
    nouns). capitalize=True uppercases only the first character, for
    sentence-initial use. Message templates never prepend their own
    articles — they call this.

    Amendment 1 (#79): introduction=True is the first-presentation
    context — room occupant lines and aggro-engagement lines, exactly
    those two families. It uses indefinite_article ("A black bear is
    here."); a blank indefinite_article (proper nouns, bosses, unique
    landmarks) falls back to the definite/bare composition, so "The
    Silk Matron snarls and moves to attack!" is unchanged."""
    definition = getattr(npc, 'definition', npc)
    if definition.plural_phrase:
        text = definition.plural_phrase
    elif introduction and definition.indefinite_article:
        text = f"{definition.indefinite_article} {definition.name}"
    elif definition.article:
        text = f"{definition.article} {definition.name}"
    else:
        text = definition.name
    return _capitalize_first(text) if capitalize else text


def npc_display_name(npc, npcs_in_room, capitalize=False):
    """npc_display plus ordinal disambiguation: 'the black bear' when
    unique in the room, 'the second black bear' when multiple NPCs share
    the definition name. Positional: index within the same-name NPCs in
    room parse order. Not a stable per-instance number — it shifts as
    same-name NPCs die. Proper nouns and plural_phrase names never take
    an ordinal (the phrase is inherently non-specific)."""
    definition = npc.definition
    if definition.plural_phrase or not definition.article:
        return npc_display(npc, capitalize)
    name = definition.name
    same_name = [n for n in npcs_in_room if n.definition.name == name]
    if len(same_name) <= 1:
        return npc_display(npc, capitalize)
    index = next((i for i, n in enumerate(same_name) if n.pk == npc.pk), None)
    if index is None or index >= len(ORDINALS):
        return npc_display(npc, capitalize)
    text = f"{definition.article} {ORDINALS[index]} {name}"
    return _capitalize_first(text) if capitalize else text


def _iter_rolled_entries(item):
    for entry in (item.rolled_primary_stats or []) + (item.rolled_secondary_stats or []):
        stat = entry.get('stat')
        value = entry.get('value')
        if stat is not None and value is not None:
            yield stat, value


def gear_stat_bonus(character, equipped_items=None):
    """v22 B5 (#100): the gear-only six-stat bonus dict. Sums matching
    rolled entries (primary + secondary) across all equipped items, rounded
    to nearest int per stat. Computed per use — no caching fields. Pass
    equipped_items (any iterable of ItemInstances) to avoid a query in
    sync-display or per-round contexts; an unsaved character has no gear."""
    if equipped_items is None:
        if character.pk is None:
            equipped_items = []
        else:
            equipped_items = list(character.inventory.filter(is_equipped=True))
    totals = {key: 0.0 for key in PRIMARY_STAT_KEYS}
    for item in equipped_items:
        for stat, value in _iter_rolled_entries(item):
            if stat in totals:
                totals[stat] += value
    return {key: int(round(total)) for key, total in totals.items()}


def effective_stats(character, equipped_items=None):
    """v22 B5 (#100): base stat fields + equipped-gear bonuses — the values
    every gameplay read uses (contests, damage bonuses, carry capacity,
    initiative, bar maxima). +N on gear means +N here. Display splits base
    from bonus via gear_stat_bonus instead."""
    gear = gear_stat_bonus(character, equipped_items)
    return {
        key: getattr(character, f'stat_{key}') + gear[key]
        for key in PRIMARY_STAT_KEYS
    }


def summed_gear_stat(equipped_items, stat_name):
    """Sum of one rolled stat across equipped items (crit_chance for the
    to-hit bonus, lifesteal for the on-hit heal). Broken items still count —
    only TAV has a ruled non-functional band."""
    return sum(
        value
        for item in equipped_items
        for stat, value in _iter_rolled_entries(item)
        if stat == stat_name
    )


def total_armor_value(character, equipped_items=None):
    """v22 B5 (#100): TAV = Σ(slot weight × mk_tier over worn armor pieces
    in the Option C table) + Σ(rolled physical_resist over ALL equipped
    items, any type). Broken / zero-durability items contribute nothing
    (the non-functional band)."""
    if equipped_items is None:
        equipped_items = list(
            character.inventory.filter(is_equipped=True).select_related('definition'))
    tav = 0.0
    for item in equipped_items:
        if item.is_broken or item.durability_current == 0:
            continue
        if (item.definition.item_type == 'armor'
                and item.equipped_slot in ARMOR_SLOT_WEIGHTS):
            tav += ARMOR_SLOT_WEIGHTS[item.equipped_slot] * item.mk_tier
        for stat, value in _iter_rolled_entries(item):
            if stat == 'physical_resist':
                tav += value
    return int(round(tav))


def apply_armor_mitigation(damage, tav):
    """v22 B5 (#100): deterministic per-hit mitigation on NPC→player damage,
    applied AFTER calculate_damage produces the hit's final value. Fraction
    TAV/(TAV+K); when TAV > 0 the reduction is at least 1 (applied once to
    the total), and at least 1 damage always lands beneath it."""
    if tav <= 0:
        return damage
    reduction = max(1, round(damage * tav / (tav + ARMOR_MITIGATION_K)))
    return max(1, damage - reduction)


def roll_gear_bonus_damage(equipped_items):
    """v22 B5 (#68/#100): the gear-bonus damage pool for one landed player
    hit (hit or critical — never graze/miss). Each equipped item rolls each
    of its proc-factor stats independently: chance = V × PROC_CHANCE_PER_POINT
    capped at PROC_CHANCE_CAP; success adds randint(1, ceil(V)). Flat
    electric_damage_bonus values join the pool on every landed hit. The
    caller renders a nonzero pool as the hit line's parenthetical."""
    pool = 0.0
    for item in equipped_items:
        for stat, value in _iter_rolled_entries(item):
            if stat in PROC_FACTOR_STATS:
                if value > 0 and random.random() < min(
                        PROC_CHANCE_CAP, value * PROC_CHANCE_PER_POINT):
                    pool += random.randint(1, math.ceil(value))
            elif stat == 'electric_damage_bonus':
                pool += value
    return int(round(pool))


def bar_rescale_updates(gear_end=0, gear_str=0, gear_wis=0,
                        end_delta=0, str_delta=0, wis_delta=0):
    """v22 B5 (#110): the bar law. Returns the field→expression dict for
    ONE atomic .update() that recomputes both maxima from effective stats
    and rescales both currents to preserve fill fraction — current ×
    new_max ÷ old_max, rounded to nearest, floored at 1 while alive (a
    dying 0 stays 0). All stat-field references are F() expressions (DB
    truth at update time), so a concurrent stat write — effect expiry,
    another consumer — is never lost; only the gear sums and the spend
    delta arrive as Python constants, because they belong to the mutation
    itself. Callers: equip, unequip, spend. Level-up keeps its own path."""
    from django.db.models import (
        Case, DecimalField, ExpressionWrapper, F, FloatField, IntegerField,
        Value, When,
    )
    from django.db.models.functions import Cast, Greatest, Round

    new_vit = ExpressionWrapper(
        (F('stat_end') + (end_delta + gear_end)) * 10
        + (F('stat_str') + (str_delta + gear_str)) * 3
        + F('level') * 5,
        output_field=IntegerField())
    new_lon = ExpressionWrapper(
        (F('stat_end') + (end_delta + gear_end)) * 8
        + (F('stat_wis') + (wis_delta + gear_wis)) * 5
        + F('level') * 5,
        output_field=IntegerField())

    def rescaled(current_field, max_field, new_max):
        ratio = ExpressionWrapper(
            Cast(F(current_field) * new_max, FloatField()) / Cast(F(max_field), FloatField()),
            output_field=FloatField())
        scaled = Round(Cast(ratio, DecimalField(max_digits=14, decimal_places=4)))
        return Case(
            When(**{f'{current_field}__lte': 0}, then=Value(0)),
            default=Greatest(Value(1), scaled),
            output_field=IntegerField(),
        )

    return {
        'vitality_current': rescaled('vitality_current', 'vitality_max', new_vit),
        'vitality_max': new_vit,
        'longevity_current': rescaled('longevity_current', 'longevity_max', new_lon),
        'longevity_max': new_lon,
    }


def acuity_damage_modifier(character):
    """Band-relative, deviation-based Acuity modifier (v19 ruling).
    Inside the Origin band: neutral. Above band_high: bonus by the distance
    beyond it (applied to focus target only, enforced by calculate_damage).
    Below band_low: penalty by the distance beyond it (always applies)."""
    a = min(1.9, max(0.1, character.acuity_current))
    if a > character.acuity_band_high:
        return 1.0 + (a - character.acuity_band_high)
    if a < character.acuity_band_low:
        return 1.0 - (character.acuity_band_low - a)
    return 1.0


def roll_initiative(stat_dex, stat_per):
    """d10 + DEX + PER."""
    return stat_dex + stat_per + random.randint(1, 10)


def resolve_hit(attacker_dex, target_dodge, crit_bonus=0.0):
    """Return 'miss', 'graze', 'hit', or 'critical'.

    Contested to-hit: d20 + attacker DEX vs static defense
    (TO_HIT_DEFENSE_BASE + defender DEX). Critical is a separate
    independent roll on any successful hit, floored at CRIT_BASE and
    capped at CRIT_CAP. v22 B5 (#100): crit_bonus is the gear
    contribution — summed rolled crit_chance × 0.01, player attacks only —
    added inside the same capped computation.
    """
    total = random.randint(1, 20) + attacker_dex
    defense = TO_HIT_DEFENSE_BASE + target_dodge
    if total >= defense:
        crit_chance = min(CRIT_CAP, max(CRIT_BASE,
            CRIT_BASE + CRIT_PER_DEX_ADVANTAGE * (attacker_dex - target_dodge)
            + crit_bonus))
        return 'critical' if random.random() < crit_chance else 'hit'
    if defense - total <= GRAZE_WINDOW:
        return 'graze'
    return 'miss'


def calculate_damage(base_damage, stat_bonus, acuity_mod, durability_mod, hit_result, is_focus_target=True):
    """
    Returns final damage as a float (minimum 1).

    Acuity bonus (>1.0) applies only when is_focus_target=True.
    Acuity penalty (<1.0) always applies.
    """
    effective_acuity = acuity_mod if (acuity_mod < 1.0 or is_focus_target) else 1.0
    raw = (base_damage + stat_bonus) * effective_acuity * durability_mod
    hit_multipliers = {'graze': 0.5, 'hit': 1.0, 'critical': 1.5}
    final = raw * hit_multipliers.get(hit_result, 1.0)
    return max(1.0, final)


def npc_level(npc_instance):
    """The NPC's effective level. scaling_factor encodes the NPC's
    within-band level (1-10); Mk tier lifts it by whole bands."""
    return npc_instance.definition.scaling_factor + MK_LEVEL_SPAN * (npc_instance.mk_tier - 1)


def get_npc_stats(npc_instance):
    """Return effective NPC stats. DEX (the difficulty dial for contests)
    grows purely off the curve+tier-offset so hit chances hit the blessed
    targets (55% normal / 45% elite / 45% boss) at every level and Mk tier.
    v21 B3 (#101): boss and elite share the +2 dodge tier — boss identity
    lives in HP, damage, and escorts, not the miss rate.
    STR/PER/INT keep their authored species bases and grow additively on the
    same per-level slope players climb, so species identity survives while
    damage stays proportionate. base_dex is no longer read here."""
    d = npc_instance.definition
    L = npc_level(npc_instance)
    curve = round(NPC_CONTEST_BASE + NPC_CONTEST_STEP * (L - 1))
    offset = NPC_TIER_OFFSET.get(d.combat_tier, 0)
    growth = round(NPC_CONTEST_STEP * (L - 1))
    return {
        'dex':      curve + offset,
        'str':      d.base_str + growth,
        'per':      d.base_per + growth,
        'int':      d.base_int + growth,
        'vitality': npc_instance.vitality_current,
    }


def get_npc_health_description(vitality_current, vitality_max):
    """Return a descriptive phrase for NPC health state (no raw numbers)."""
    if vitality_max <= 0:
        return "appears to be in perfect health"
    pct = vitality_current / vitality_max
    if pct >= 0.9:
        return "appears to be in perfect health"
    elif pct >= 0.75:
        return "has a few minor wounds"
    elif pct >= 0.50:
        return "looks moderately wounded"
    elif pct >= 0.25:
        return "looks badly wounded"
    elif pct > 0:
        return "is near death"
    else:
        return "is dead"


def apply_death_penalties(character):
    """
    Apply death penalties to a character. Synchronous — call from within @database_sync_to_async.
    Returns a list of broken item names.
    """
    from .models import ItemInstance, DEATH_DURABILITY_LOSS, XP_PENALTY_MIN_LEVEL
    broken_items = []

    equipped_items = ItemInstance.objects.filter(
        owner=character, is_equipped=True
    ).select_related('definition')

    for item in equipped_items:
        if not item.definition.takes_durability_loss:
            continue
        item.durability_current = max(0.0, item.durability_current - DEATH_DURABILITY_LOSS)
        if item.durability_current == 0.0 and not item.is_broken:
            item.is_broken = True
            broken_items.append(item.definition.name)
        item.save(update_fields=['durability_current', 'is_broken'])

    if character.level >= XP_PENALTY_MIN_LEVEL:
        xp_loss = max(0, int(character.xp * 0.10))
        character.xp = max(0, character.xp - xp_loss)
        character.save(update_fields=['xp'])

    return broken_items


def apply_npc_effects(npc_instance, target_character):
    """
    Roll each NpcEffect for the given NPC and apply those that fire.
    Returns a list of effect names to append to the attack line.
    Synchronous — call from within @database_sync_to_async.
    """
    from .models import NpcEffect
    from .effect_utils import apply_effect_definition

    messages = []
    effects = NpcEffect.objects.filter(
        npc_definition=npc_instance.definition
    ).select_related('effect_definition')

    for npc_effect in effects:
        if random.random() > npc_effect.effect_chance:
            continue
        msgs = apply_effect_definition(
            definition=npc_effect.effect_definition,
            target=target_character,
            mk_tier=npc_instance.mk_tier,
            removed_by_label='npc_service',
        )
        messages.extend(msgs)
        messages.append(npc_effect.effect_definition.name)

    return messages


def get_unarmed_message(attacker_pool, target_name, attacker_name=None, fallback_slug='default'):
    """
    Select a random unarmed attack message from the given pool.
    Falls back to the pool named by fallback_slug if attacker_pool is None or
    has no messages ('default' for player attacks, 'npc-default' for NPC attacks).
    Substitution is literal str.replace, not .format: '{target}' -> target_name,
    '{attacker}' -> attacker_name when provided. Stray braces in prose are harmless.
    Caller is responsible for prefetching pool.messages before calling.
    v20 brief 5 (#24): attacker_name must arrive composed (npc_display /
    npc_display_name, capitalized for sentence-initial use) — no template
    or fallback prepends an article.
    """
    import random
    messages = list(attacker_pool.messages.all()) if attacker_pool else []
    if not messages:
        from apps.shyland.models import UnarmedMessagePool
        try:
            fallback_pool = UnarmedMessagePool.objects.prefetch_related('messages').get(slug=fallback_slug)
            messages = list(fallback_pool.messages.all())
        except UnarmedMessagePool.DoesNotExist:
            messages = []
    if not messages:
        if attacker_name:
            return f"{attacker_name} strikes {target_name}."
        return f"You strike {target_name}."
    template = random.choice(messages).template
    text = template.replace('{target}', target_name)
    if attacker_name:
        text = text.replace('{attacker}', attacker_name)
    return text


def xp_for_kill(npc_instance, character):
    """
    XP for killing an NPC. Full value while the character is within the
    NPC's Mk level band (band top = mk_tier * 10). Beyond the band top,
    -20% per level over, floored at 10% of base — and never less than 1.
    Outleveled content always pays something.
    """
    base = int(npc_instance.mk_tier * 10 * npc_instance.definition.scaling_factor)
    band_top = npc_instance.mk_tier * 10
    levels_over = max(0, character.level - band_top)
    multiplier = max(0.10, 1.0 - (0.20 * levels_over))
    # round(…, 9) corrects binary-float error (0.20 * 3 → 0.6000…01) so the
    # truncation below matches the decimal formula: 10 XP at −60% is 4, not 3.
    return max(1, int(round(base * multiplier, 9)))


def xp_for_next_level(level):
    """XP required to reach (level + 1). Formula: level² × 100."""
    return level * level * 100


def recalculate_bars(character, equipped_items=None):
    """
    Recalculate vitality_max and longevity_max from stats + level.
    Sets current bars to new maximums (full bars on level-up).
    Returns (new_vitality_max, new_longevity_max).

    v22 B5 (#100): the formula inputs are EFFECTIVE stats (base + equipped
    gear) — equipping END gear raises vitality_max. Callers: level-up (the
    full-refill semantics here are level-up's own, explicitly preserved)
    and character creation (no gear yet). Equip/unequip/spend do NOT write
    through this — they use the atomic bar_rescale_updates path (#110).
    """
    eff = effective_stats(character, equipped_items)
    new_vitality_max  = (eff['end'] * 10) + (eff['str'] * 3) + (character.level * 5)
    new_longevity_max = (eff['end'] * 8)  + (eff['wis'] * 5) + (character.level * 5)

    character.vitality_max      = new_vitality_max
    character.vitality_current  = new_vitality_max
    character.longevity_max     = new_longevity_max
    character.longevity_current = new_longevity_max

    return new_vitality_max, new_longevity_max
