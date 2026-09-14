"""v26.2 (#330): the curse engine's lifecycle — the one home for the
trap (spring_curse) and the one shared teardown (end_curse).

A curse is an EffectDefinition with is_curse=True riding an item: the
latent curse is rolled at generation time (item_utils), springs when a
player equips the item, and ends exactly once — expiry, curse-caused
death, or sudo removal — through end_curse, which cleans the item and
stamps the memorial. One curse life per instance: with latent_curse
cleared, no path ever re-springs.

All functions are synchronous — call from within @database_sync_to_async.
"""


def spring_curse(item, character):
    """The trap: apply the item's latent curse to its wearer at the
    ITEM's mk_tier with all gates bypassed — no admission, no
    same-definition check (two items with the same curse each spring
    independently). Sets active_curse and curse_identified in the same
    motion (springing IS the identification). Returns the theater lines:
    apply_text split on newlines, empties dropped."""
    from .effect_utils import _create_effect_instance

    definition = item.latent_curse
    instance, _ = _create_effect_instance(definition, character, item.mk_tier)
    item.active_curse = instance
    item.curse_identified = True
    item.save(update_fields=['active_curse', 'curse_identified'])
    return [line for line in (definition.apply_text or '').splitlines()
            if line.strip()]


def end_curse(item, cause):
    """The one teardown. Deactivates the active curse's component
    instances and instance with removed_by=cause, reverses every
    reversible component (stat cuts by stored delta; bar cuts via the
    bar-law rescale), clears is_cursed and latent_curse, stamps the
    memorial, and leaves curse_identified untouched. Causes: 'timeout'
    (expiry), 'curse-death', 'item-removed' (sudo)."""
    from .combat_utils import rescale_bars_for_gear
    from .effect_utils import apply_stat_effect

    instance = item.active_curse
    if instance is not None:
        target = instance.target
        active_cis = list(instance.component_instances.filter(
            is_active=True).select_related('component'))
        had_bar_cut = False
        for ci in active_cis:
            ctype = ci.component.component_type
            if ctype in ('stat_bonus', 'stat_penalty', 'stat_cut_percent'):
                apply_stat_effect(target, ci, reverse=True)
            elif ctype in ('cut_vitality_max', 'cut_longevity_max'):
                had_bar_cut = True
        instance.component_instances.filter(is_active=True).update(
            is_active=False, removed_by=cause)
        instance.is_active = False
        instance.removed_by = cause
        instance.save(update_fields=['is_active', 'removed_by'])
        if had_bar_cut:
            # The instances are inactive now — the rescale recomputes
            # the maxima without them (bar law, fill fraction invariant).
            rescale_bars_for_gear(target)
            target.refresh_from_db(fields=[
                'vitality_current', 'vitality_max',
                'longevity_current', 'longevity_max',
            ])

    definition = (instance.definition if instance is not None
                  else item.latent_curse)
    item.is_cursed = False
    item.latent_curse = None
    item.active_curse = None
    if definition is not None and definition.memorial_text:
        item.memorial_description = definition.memorial_text
    item.save(update_fields=[
        'is_cursed', 'latent_curse', 'active_curse', 'memorial_description',
    ])
