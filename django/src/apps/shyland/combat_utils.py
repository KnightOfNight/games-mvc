import random

TO_HIT_DEFENSE_BASE = 10   # static defense = base + defender DEX
GRAZE_WINDOW = 3           # miss the defense by 1..GRAZE_WINDOW -> graze
CRIT_BASE = 0.05           # critical chance floor on any successful hit
CRIT_PER_DEX_ADVANTAGE = 0.01
CRIT_CAP = 0.25


def get_acuity_modifier(character):
    """Return acuity_current clamped to [0.1, 1.9], rounded to 1dp."""
    return round(max(0.1, min(1.9, character.acuity_current)), 1)


def roll_initiative(stat_dex, stat_per):
    """d10 + DEX + PER."""
    return stat_dex + stat_per + random.randint(1, 10)


def resolve_hit(attacker_dex, target_dodge):
    """Return 'miss', 'graze', 'hit', or 'critical'.

    Contested to-hit: d20 + attacker DEX vs static defense
    (TO_HIT_DEFENSE_BASE + defender DEX). Critical is a separate
    independent roll on any successful hit, floored at CRIT_BASE and
    capped at CRIT_CAP.
    """
    total = random.randint(1, 20) + attacker_dex
    defense = TO_HIT_DEFENSE_BASE + target_dodge
    if total >= defense:
        crit_chance = min(CRIT_CAP, max(CRIT_BASE,
            CRIT_BASE + CRIT_PER_DEX_ADVANTAGE * (attacker_dex - target_dodge)))
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


def get_npc_stats(npc_instance):
    """Return effective NPC stats scaled by Mk tier."""
    d = npc_instance.definition
    factor = d.scaling_factor * npc_instance.mk_tier
    return {
        'dex':      int(d.base_dex * factor),
        'str':      int(d.base_str * factor),
        'per':      int(d.base_per * factor),
        'int':      int(d.base_int * factor),
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
            return f"The {attacker_name} strikes {target_name}."
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


def recalculate_bars(character):
    """
    Recalculate vitality_max and longevity_max from stats + level.
    Sets current bars to new maximums (full bars on level-up).
    Returns (new_vitality_max, new_longevity_max).
    """
    new_vitality_max  = (character.stat_end * 10) + (character.stat_str * 3) + (character.level * 5)
    new_longevity_max = (character.stat_end * 8)  + (character.stat_wis * 5) + (character.level * 5)

    character.vitality_max      = new_vitality_max
    character.vitality_current  = new_vitality_max
    character.longevity_max     = new_longevity_max
    character.longevity_current = new_longevity_max

    return new_vitality_max, new_longevity_max
