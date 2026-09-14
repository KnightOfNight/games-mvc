import math
from datetime import timedelta

from django.utils import timezone


def percent_restore_amount(fraction, bar_max, floor):
    """The Draught Law shape (v24.0, #139), generalized per bar (v26.1,
    #70): a percentage restore gives ceil(fraction × bar_max), never less
    than the bar's floor. The fraction is of MAX, never of deficit.
    math.ceil, never bare round() — banker's rounding is the #105
    lesson. One shared home for the arithmetic."""
    return max(floor, math.ceil(fraction * bar_max))


def percent_heal_amount(fraction, vitality_max):
    """The Draught Law (v24.0, #139) for Vitality — a thin delegate to
    percent_restore_amount with the vitality floor; the instant-apply
    branch and the consumers use-path aggregate both call this."""
    from .models import VITALITY_PERCENT_HEAL_FLOOR
    return percent_restore_amount(fraction, vitality_max,
                                  VITALITY_PERCENT_HEAL_FLOOR)


# v26.2 (#331): the six admission-gated lanes — the ticking dot/hot
# family. Shifts, stat effects, and instants are ungated.
GATED_TICKING_TYPES = (
    'dot_vitality', 'hot_vitality',
    'dot_longevity', 'hot_longevity',
    'dot_acuity', 'hot_acuity',
)


class EffectRefused(Exception):
    """v26.2 (#331): an effect application was refused by the admission
    gate (or the same-definition lower-Mk check). Carries the blocking
    active effect's definition name for the caller's warn line."""

    def __init__(self, blocking_name):
        self.blocking_name = blocking_name
        super().__init__(blocking_name)


def apply_effect_definition(definition, target, mk_tier, removed_by_label='consumable'):
    """
    Apply an EffectDefinition to a target Character.
    Returns a list of (clause, annotation) pairs for the instant
    components applied — v23.3 (#149): the effect layer speaks in
    clauses; sentence composition belongs to the caller (see
    compose_standalone_sentence / compose_use_sentence). Timed
    components produce no pairs.

    v26.2 (#331): raises EffectRefused instead of silently returning []
    on a same-definition lower-Mk reapplication, and runs the admission
    gate over the six ticking dot/hot lanes: a gated component is
    admitted only if its magnitude at this mk_tier is strictly greater
    than every active same-type component instance on the target
    (curse-sourced incumbents excluded — a live curse never blocks an
    ordinary effect). Whole-effect atomicity: if ANY gated component is
    refused, the whole application is refused before anything mutates.
    Admission is a join — incumbents in other definitions are never
    deactivated.

    Synchronous — call from within @database_sync_to_async.
    """
    from .models import EffectInstance, EffectComponentInstance

    # Reapplication check
    existing = EffectInstance.objects.filter(
        definition=definition, target=target, is_active=True
    ).first()

    if existing and mk_tier < existing.mk_tier:
        raise EffectRefused(existing.definition.name)

    # v26.2 (#331): the admission gate — checked for every gated
    # component BEFORE any mutation (whole-effect atomicity; the
    # same-definition incumbent is about to be replaced, so its own
    # instances don't gate the replacement).
    for component in definition.components.all():
        if component.component_type not in GATED_TICKING_TYPES:
            continue
        incoming = component.computed_magnitude(mk_tier)
        incumbents = EffectComponentInstance.objects.filter(
            effect_instance__target=target,
            effect_instance__is_active=True,
            is_active=True,
            component__component_type=component.component_type,
        ).exclude(
            effect_instance__definition__is_curse=True,
        ).select_related('effect_instance__definition')
        if existing:
            incumbents = incumbents.exclude(effect_instance=existing)
        for incumbent in incumbents:
            if incumbent.magnitude >= incoming:
                raise EffectRefused(incumbent.effect_instance.definition.name)

    if existing:
        # Same-definition >=-Mk refresh: replace the incumbent.
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

    instance, messages = _create_effect_instance(definition, target, mk_tier)
    return messages


def _create_effect_instance(definition, target, mk_tier):
    """The gate-free creation core: container + component instances +
    instant application. v26.2 (#330): extracted so the curse trap
    (spring_curse) can apply with all gates bypassed. Returns
    (EffectInstance, clause pairs).
    """
    from .models import EffectInstance, EffectComponentInstance

    messages = []

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

        if component.no_expiry:
            # v26.2 (#330): never-expiring component — timed, with a null
            # expires_at the expiry sweep skips; duration fields ignored.
            has_duration_components = True
            ci = EffectComponentInstance(
                effect_instance=instance,
                component=component,
                magnitude=magnitude,
                expires_at=None,
                is_active=True,
            )
            ci.save()
            _apply_persistent_component_on_create(component, target, ci, mk_tier)
        elif component.is_instantaneous():
            pair = _apply_instant_component(component, target, magnitude)
            if pair is not None:
                messages.append(pair)
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
            _apply_persistent_component_on_create(component, target, ci, mk_tier)

    # Close instance immediately if it had no duration components
    if not has_duration_components:
        instance.is_active = False
        instance.removed_by = 'timeout'
        instance.save(update_fields=['is_active', 'removed_by'])

    return instance, messages


def _apply_persistent_component_on_create(component, target, ci, mk_tier):
    """On-apply action for a freshly created timed component instance.
    stat_bonus/stat_penalty apply immediately (pre-v26.2 behavior);
    v26.2 (#330) adds the reversible cut family. damage_cut, armor_cut,
    and floor_hold_vitality need no on-apply action — the first two are
    passive per-round reads, the third ticks."""
    ctype = component.component_type
    if ctype in ('stat_bonus', 'stat_penalty'):
        apply_stat_effect(target, ci, reverse=False)
    elif ctype == 'stat_cut_percent':
        # The fraction lives on the component; the instance stores the
        # NEGATIVE flat delta computed once against the current base
        # stat — exact reversal, no drift (the stat_bonus delta model).
        stat_name = component.target_stat
        attr = f'stat_{stat_name}'
        if stat_name and hasattr(target, attr):
            fraction = ci.magnitude
            delta = int(fraction * getattr(target, attr))
            ci.magnitude = -delta
            ci.save(update_fields=['magnitude'])
            apply_stat_effect(target, ci, reverse=False)
    elif ctype in ('cut_vitality_max', 'cut_longevity_max'):
        # The fraction cuts the bar's max, computed once against the
        # pre-cut max and stored as the flat delta; the rescale family
        # subtracts every active cut inside its formula (bar law — fill
        # fraction invariant), so apply is just store-then-rescale.
        from .combat_utils import rescale_bars_for_gear
        bar_max = (target.vitality_max if ctype == 'cut_vitality_max'
                   else target.longevity_max)
        ci.magnitude = int(ci.magnitude * bar_max)
        ci.save(update_fields=['magnitude'])
        rescale_bars_for_gear(target)
        target.refresh_from_db(fields=[
            'vitality_current', 'vitality_max',
            'longevity_current', 'longevity_max',
        ])


def vitality_hold_value(character):
    """v26.2 (#330): the active floor_hold_vitality hold value for a
    character — max(1, ceil(magnitude2 × vitality_max)), the most
    restrictive (lowest) when several are live — or None with no active
    hold. The heal ceiling: while active, any vitality-increasing write
    clamps to max(current_before_heal, hold_value)."""
    import math
    from .models import EffectComponentInstance
    hold = None
    rows = EffectComponentInstance.objects.filter(
        effect_instance__target=character,
        effect_instance__is_active=True,
        is_active=True,
        component__component_type='floor_hold_vitality',
    ).select_related('component', 'effect_instance')
    for ci in rows:
        mag2 = ci.component.computed_magnitude2(
            ci.effect_instance.mk_tier) or 0.0
        value = max(1, math.ceil(mag2 * character.vitality_max))
        hold = value if hold is None else min(hold, value)
    return hold


def _apply_instant_component(component, target, magnitude):
    """Apply an instantaneous component immediately. Returns a
    (clause, annotation) pair — v23.3 (#149) — or None for component
    types with nothing to say.

    v21 brief 3 (#52): bar restores are single atomic UPDATEs (F() with a
    clamp), never object-arithmetic-then-save — the caller's cached
    character may be stale against the tick engine's per-round damage
    writes, and adding the magnitude to a stale read silently resurrects
    persisted damage. The annotation prints the magnitude; the bars
    render truth because every display path re-fetches after mutation.
    """
    from django.db.models import Case, DecimalField, F, Value, When
    from django.db.models.functions import Cast, Greatest, Least, Round

    from .models import Character, LONGEVITY_PERCENT_RESTORE_FLOOR

    ctype = component.component_type
    row = Character.objects.filter(pk=target.pk)

    if ctype == 'restore_vitality':
        # v26.2 (#330): the floor-hold heal ceiling — below the hold,
        # heals work up to the hold; at or above it, heals are no-ops
        # (clamp to max(current_before_heal, hold)). The consumable is
        # still spent; the annotation keeps its nominal print (the
        # standing at-max clamp shape).
        hold = vitality_hold_value(target)
        ceiling = (F('vitality_max') if hold is None
                   else Least(F('vitality_max'),
                              Greatest(F('vitality_current'), Value(hold))))
        row.update(vitality_current=Least(
            F('vitality_current') + magnitude, ceiling))
        return ("feel your body recover", f"(+{int(magnitude)} Vitality)")

    if ctype == 'restore_vitality_percent':
        # The Draught Law (v24.0, #139): magnitude arrives as the
        # FRACTION of vitality_max (computed_magnitude = 0.15 + 0.05×Mk).
        # vitality_max is safe to read from the caller's character — only
        # equip/level paths move it; the tick engine's per-round writes
        # touch vitality_current, which stays inside the atomic UPDATE.
        # v26.2 (#330): floor-hold heal ceiling, as restore_vitality.
        heal = percent_heal_amount(magnitude, target.vitality_max)
        hold = vitality_hold_value(target)
        ceiling = (F('vitality_max') if hold is None
                   else Least(F('vitality_max'),
                              Greatest(F('vitality_current'), Value(hold))))
        row.update(vitality_current=Least(
            F('vitality_current') + heal, ceiling))
        return ("feel your body recover", f"(+{heal} Vitality)")

    if ctype == 'restore_longevity':
        row.update(longevity_current=Least(
            F('longevity_current') + magnitude, F('longevity_max')))
        return ("feel your stamina return", f"(+{int(magnitude)} Longevity)")

    if ctype == 'restore_longevity_percent':
        # The potion mirror (v26.1, #70): magnitude arrives as the
        # FRACTION of longevity_max (computed_magnitude = 0.15 + 0.05×Mk).
        # longevity_max is safe to read from the caller's character — only
        # equip/level paths move it; the tick engine's regen writes touch
        # longevity_current, which stays inside the atomic UPDATE.
        restore = percent_restore_amount(
            magnitude, target.longevity_max, LONGEVITY_PERCENT_RESTORE_FLOOR)
        row.update(longevity_current=Least(
            F('longevity_current') + restore, F('longevity_max')))
        return ("feel your stamina return", f"(+{restore} Longevity)")

    if ctype == 'restore_acuity':
        # Same formula as before, expressed in SQL: move toward the
        # baseline by up to `magnitude`, never past it, clamped to the
        # 0.1–1.9 scale and rounded to 1 decimal (Cast to numeric —
        # Postgres has no round(double, int)).
        toward_baseline = Case(
            When(acuity_current__lt=F('acuity_baseline'),
                 then=Least(F('acuity_current') + magnitude,
                            F('acuity_baseline'))),
            When(acuity_current__gt=F('acuity_baseline'),
                 then=Greatest(F('acuity_current') - magnitude,
                               F('acuity_baseline'))),
            default=F('acuity_current'),
        )
        row.update(acuity_current=Round(
            Cast(Greatest(Value(0.1), Least(Value(1.9), toward_baseline)),
                 DecimalField(max_digits=8, decimal_places=4)),
            1))
        target.refresh_from_db(fields=['acuity_current'])
        return ("feel your mind steady",
                f"(Acuity {target.acuity_current:.1f})")

    if ctype == 'durability_restore':
        # v24.12 (#134): field repair — patch the owner's most-damaged
        # eligible item, over everything owned (carried + equipped),
        # stable tie-break on pk. Broken (0%) gear is ineligible — the
        # vendor roll owns it — and the kit can never target itself
        # (kits are takes_durability_loss=False). A kit always succeeds:
        # no roll, one atomic clamped UPDATE; the annotation reports the
        # ACTUAL points applied after the clamp. The use-pipeline gate
        # refuses before this runs whenever no target exists — None here
        # is defense, not flow.
        from .item_utils import item_ref
        from .models import ItemInstance
        target_item = (
            ItemInstance.objects.filter(
                owner=target,
                definition__takes_durability_loss=True,
                durability_current__gt=0.0,
                durability_current__lt=100.0,
            )
            .select_related('definition')
            .order_by('durability_current', 'pk')
            .first()
        )
        if target_item is None:
            return None
        before = target_item.durability_current
        ItemInstance.objects.filter(pk=target_item.pk).update(
            durability_current=Least(
                F('durability_current') + magnitude, Value(100.0)))
        applied = int(min(magnitude, 100.0 - before))
        return (f'patch up {item_ref(target_item)}',
                f'(+{applied} durability)')

    return None


def compose_standalone_sentence(pair):
    """v23.3 (#149): the standalone form — the full sentence for callers
    outside `use` (the NPC path): 'You {clause}.' with the annotation
    appended after the period when present."""
    clause, annotation = pair
    sentence = f"You {clause}."
    if annotation:
        sentence += f" {annotation}"
    return sentence


def compose_use_sentence(subject, pairs):
    """v23.3 (#149): the use-sentence form — one sentence, one envelope.
    'You use {subject} and {clause1} and {clause2}. {ann1} {ann2}':
    clauses joined with ' and ' in component order, single period,
    non-empty annotations space-joined after it. An empty pair list is
    the plain transactional sentence (timed-effect consumables)."""
    if not pairs:
        return f"You use {subject}."
    clauses = " and ".join(clause for clause, _ in pairs)
    sentence = f"You use {subject} and {clauses}."
    annotations = " ".join(a for _, a in pairs if a)
    if annotations:
        sentence += f" {annotations}"
    return sentence


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
