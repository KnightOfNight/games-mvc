import random


def get_acuity_modifier(character):
    """Return acuity_current clamped to [0.1, 1.9], rounded to 1dp."""
    return round(max(0.1, min(1.9, character.acuity_current)), 1)


def roll_initiative(stat_dex, stat_per):
    """d10 + DEX + PER."""
    return stat_dex + stat_per + random.randint(1, 10)


def resolve_hit(attacker_dex, target_dodge):
    """Return 'miss', 'graze', 'hit', or 'critical'."""
    roll = random.randint(1, 100) + attacker_dex
    if roll < target_dodge:
        return 'miss'
    elif roll < target_dodge + 10:
        return 'graze'
    elif roll < target_dodge + 30:
        return 'hit'
    else:
        return 'critical'


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
    from datetime import timedelta
    from django.utils import timezone
    from .models import NpcEffect, EffectInstance

    messages = []
    effects = NpcEffect.objects.filter(
        npc_definition=npc_instance.definition
    ).select_related('effect_definition')

    for npc_effect in effects:
        if random.random() > npc_effect.effect_chance:
            continue
        ed = npc_effect.effect_definition
        magnitude = random.uniform(ed.magnitude_min, ed.magnitude_max)
        duration = None
        expires_at = None
        if ed.duration_min is not None and ed.duration_max is not None:
            duration = random.uniform(ed.duration_min, ed.duration_max)
            expires_at = timezone.now() + timedelta(seconds=duration)

        EffectInstance.objects.create(
            definition=ed,
            target=target_character,
            magnitude=magnitude,
            duration=duration,
            expires_at=expires_at,
            is_active=True,
        )
        messages.append(ed.name)

    return messages


def xp_for_kill(npc_instance, character):
    """Return XP awarded for killing an NPC."""
    return int(npc_instance.mk_tier * 10 * npc_instance.definition.scaling_factor)
