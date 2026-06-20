from datetime import timedelta

from django.utils import timezone


def apply_effect_definition(definition, target, mk_tier, removed_by_label='consumable'):
    """
    Apply an EffectDefinition to a target Character.
    Returns a list of human-readable messages to send to the player.
    Synchronous — call from within @database_sync_to_async.
    """
    from .models import EffectInstance, EffectComponentInstance

    messages = []

    # Reapplication check
    existing = EffectInstance.objects.filter(
        definition=definition, target=target, is_active=True
    ).first()

    if existing:
        if mk_tier >= existing.mk_tier:
            # Undo any active stat_bonus/stat_penalty component instances
            active_cis = list(existing.component_instances.filter(is_active=True).select_related('component'))
            for ci in active_cis:
                if ci.component.component_type in ('stat_bonus', 'stat_penalty'):
                    apply_stat_effect(target, ci, reverse=True)
            existing.component_instances.filter(is_active=True).update(
                is_active=False, removed_by='reapplication'
            )
            existing.is_active = False
            existing.removed_by = 'reapplication'
            existing.save(update_fields=['is_active', 'removed_by'])
        else:
            return []

    # Create container
    instance = EffectInstance(
        definition=definition,
        target=target,
        mk_tier=mk_tier,
        is_active=True,
    )
    instance.save()

    has_duration_components = False

    for component in definition.components.all():
        magnitude = component.computed_magnitude(mk_tier)
        duration  = component.computed_duration(mk_tier)

        if component.is_instantaneous():
            msg = _apply_instant_component(component, target, magnitude)
            if msg:
                messages.append(msg)
        else:
            has_duration_components = True
            expires_at = timezone.now() + timedelta(seconds=duration)
            ci = EffectComponentInstance(
                effect_instance=instance,
                component=component,
                magnitude=magnitude,
                expires_at=expires_at,
                is_active=True,
            )
            ci.save()
            if component.component_type in ('stat_bonus', 'stat_penalty'):
                apply_stat_effect(target, ci, reverse=False)

    # Close instance immediately if it had no duration components
    if not has_duration_components:
        instance.is_active = False
        instance.removed_by = 'timeout'
        instance.save(update_fields=['is_active', 'removed_by'])

    return messages


def _apply_instant_component(component, target, magnitude):
    """Apply an instantaneous component immediately. Returns a message string."""
    ctype = component.component_type

    if ctype == 'restore_vitality':
        target.vitality_current = min(
            target.vitality_current + magnitude, target.vitality_max
        )
        target.save(update_fields=['vitality_current'])
        return f"You feel your body recover. (+{int(magnitude)} Vitality)"

    if ctype == 'restore_longevity':
        target.longevity_current = min(
            target.longevity_current + magnitude, target.longevity_max
        )
        target.save(update_fields=['longevity_current'])
        return f"Your stamina is restored. (+{int(magnitude)} Longevity)"

    if ctype == 'restore_acuity':
        diff = target.acuity_baseline - target.acuity_current
        step = min(abs(diff), magnitude) * (1 if diff >= 0 else -1)
        target.acuity_current = round(
            max(0.1, min(1.9, target.acuity_current + step)), 1
        )
        target.save(update_fields=['acuity_current'])
        return f"Your mind steadies. (Acuity {target.acuity_current:.1f})"

    if ctype == 'durability_restore':
        return "The repair kit fizzes but does nothing useful yet."

    return ""


def apply_stat_effect(target, component_instance, reverse=False):
    """
    Apply or reverse a stat_bonus / stat_penalty component instance.
    Returns (stat_name, new_value) or (None, None) if target_stat is blank.
    Synchronous — call from within @database_sync_to_async.
    """
    stat_name = component_instance.component.target_stat
    if not stat_name:
        return None, None

    attr = f'stat_{stat_name}'
    if not hasattr(target, attr):
        return None, None

    delta = component_instance.magnitude
    if reverse:
        delta = -delta

    current = getattr(target, attr)
    new_value = max(1, int(current + delta))
    setattr(target, attr, new_value)
    target.save(update_fields=[attr])

    return stat_name, new_value


def _expiry_message_for_effect(effect_instance):
    """One message for the whole effect when all components expire together."""
    definition_name = effect_instance.definition.name
    first_component = effect_instance.definition.components.order_by('order').first()
    if first_component is None:
        return f"The {definition_name} wears off."

    primary_type = first_component.component_type

    if primary_type in ('dot_vitality', 'dot_longevity', 'dot_acuity'):
        return f"The {definition_name} wears off."
    if primary_type in ('hot_vitality', 'hot_longevity', 'hot_acuity'):
        return f"The {definition_name} wears off."
    if primary_type == 'shift_acuity_high':
        return "Your heightened focus fades. Your mind settles."
    if primary_type == 'shift_acuity_low':
        return "The fog lifts from your mind. Your thoughts sharpen."
    if primary_type == 'stat_bonus':
        return f"The {definition_name} fades. Your body returns to normal."
    if primary_type == 'stat_penalty':
        return f"The {definition_name} lifts."
    if primary_type == 'curse_generic':
        return ""
    return f"The {definition_name} wears off."


def _expiry_message_for_component(component_instance, definition_name):
    """Per-component expiry message when components expire individually."""
    ctype = component_instance.component.component_type

    if ctype == 'dot_vitality':
        return f"The poison from {definition_name} subsides."
    if ctype == 'dot_longevity':
        return f"The draining from {definition_name} fades."
    if ctype == 'dot_acuity':
        return f"The mental static from {definition_name} clears."
    if ctype == 'hot_vitality':
        return f"The healing from {definition_name} fades."
    if ctype == 'hot_longevity':
        return f"The endurance boost from {definition_name} fades."
    if ctype == 'hot_acuity':
        return f"The clarity from {definition_name} fades."
    if ctype == 'shift_acuity_high':
        return "Your heightened focus fades. Your mind settles."
    if ctype == 'shift_acuity_low':
        return "The fog lifts from your mind. Your thoughts sharpen."
    if ctype == 'stat_bonus':
        return f"The stat boost from {definition_name} fades."
    if ctype == 'stat_penalty':
        return f"The penalty from {definition_name} lifts."
    if ctype == 'curse_generic':
        return ""
    return f"An effect from {definition_name} wears off."
