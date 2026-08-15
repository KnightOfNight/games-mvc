"""v24.29 (#235): the rights-scoped corpse sweep, extracted from
``SkylandConsumer`` so both of its callers can run it.

The sweep used to live on the consumer, awaiting ``self.output(...)`` for
every line. The ``plunder`` setting fires the same sweep from the tick
engine — a different process, with no consumer, and (per the ruling)
sometimes with no connected player at all — so the sweep cannot send
anything itself.

The shape here is transport-agnostic: :func:`sweep_corpses` performs the
mutations and **returns** the lines rather than sending them. The
consumer awaits ``self.output`` over them; the tick engine appends them to
its message accumulator. Neither transport may reach into the other's.

The per-corpse ORM steps are module functions rather than consumer
methods for the same reason — the consumer's ``@database_sync_to_async``
wrappers now delegate here, so there is exactly one implementation of
each and the two call paths cannot drift.
"""

from .currency import display_for_zone
from .item_utils import carry_capacity, compose_item_line, get_display_name
from .models import Character, Corpse, ItemInstance


def get_carry_counts(character):
    """Current unequipped item count and the character's carry capacity."""
    current = ItemInstance.objects.filter(owner=character, is_equipped=False).count()
    equipped = list(
        ItemInstance.objects.filter(owner=character, is_equipped=True)
        .select_related('definition')
    )
    # v24.23 (#215): capacity via the single helper.
    max_carry = carry_capacity(character, equipped)
    return current, max_carry


def get_corpse_contents(corpse):
    return list(corpse.contents.select_related('definition').all())


def loot_item(item, character):
    item.corpse = None
    item.owner = character
    # #80 knowledge by holding: looting is taking — same flip as
    # transfer_to_character, same unidentifiable guard.
    if not item.is_unidentifiable:
        item.is_identified = True
    item.save()
    # Composed AFTER the flip: the looted line names the real item
    # the player now holds (#80) — drop composes before transfer for
    # the mirror-image reason.
    name = get_display_name(item)
    return name


def loot_copper(corpse, character):
    from django.db.models import F
    amount = corpse.copper_drop
    if amount > 0:
        Character.objects.filter(pk=character.pk).update(copper=F('copper') + amount)
        corpse.copper_drop = 0
        corpse.save(update_fields=['copper_drop'])
    return amount


def corpse_empty_and_delete(corpse):
    # Query the table directly: `corpse.contents.exists()` on a corpse
    # loaded with prefetch_related answers from the stale prefetch
    # cache, so an emptied corpse would never delete on the loot that
    # emptied it (found by v20 brief 3 verification).
    if not ItemInstance.objects.filter(corpse=corpse).exists():
        corpse.delete()
        return True
    return False


def corpses_in_room(room):
    """Every corpse in the room, in the sweep's canonical order."""
    return list(
        Corpse.objects.filter(current_room=room)
        .select_related('killed_by', 'npc_definition')
        .prefetch_related('contents__definition')
        .order_by('-created_at')
    )


def lootable_corpses(character, room):
    """v24.29 (#235): the rights predicate, verbatim as bare ``loot``
    applies it — the room's corpses this character killed, in the same
    order. The plunder hook filters with this before deciding whether it
    has anything to do (the silence contract)."""
    return [c for c in corpses_in_room(room) if c.killed_by_id == character.pk]


def plunder_on_combat_end(character_pk):
    """v24.29 (#235): the plunder hook, called wherever ``Combat has
    ended.`` is delivered to a character and nowhere else.

    Returns ``(messages, room_lines, room_id)`` — empty lists and a null
    room id when there is nothing to do.

    **The silence contract:** plunder is silent unless it plunders. With
    the setting off, with no corpses in the room, or with no corpses this
    character has rights to, it emits nothing whatsoever. The typed
    command's refusals (``There is nothing to loot here.`` / ``That is
    not your kill; you may not loot it.``) belong to ``cmd_loot`` and are
    never spoken on plunder's behalf — which is why the filtering happens
    here, before the sweep, and never routes through the command.

    The character is re-read by pk rather than taken as an object so the
    setting is genuinely read *at combat end*: a player who flips
    ``plunder`` mid-fight governs that same fight, whatever the calling
    site had loaded earlier in the round.
    """
    character = (
        Character.objects
        .select_related('current_room__zone')
        .filter(pk=character_pk)
        .first()
    )
    if character is None or not character.plunder_mode:
        return [], [], None
    room = character.current_room
    if room is None:
        return [], [], None
    lootable = lootable_corpses(character, room)
    if not lootable:
        return [], [], None
    messages, room_lines = sweep_corpses(character, room, lootable)
    return messages, room_lines, room.pk


def _disappear_line(corpse):
    name = corpse.display_name
    return (f"{name[0].upper()}{name[1:]} slowly disappears.", 'room')


def sweep_corpses(character, room, lootable):
    """v20 brief 3 amendment 1 (#62), extracted in v24.29 (#235): sweep
    every corpse in ``lootable``. Per-item and coin lines exactly as
    single-corpse looting emits them (each its own message); empty
    corpses make no individual noise — the summary counts them. Stops
    early if the character fills up.

    Synchronous, so each caller wraps it the way it already wraps ORM
    work. Returns ``(messages, room_lines)``:

    - ``messages`` — ordered ``(text, category)`` for the looting
      character, exactly the lines the consumer's ``_loot_sweep`` used to
      await.
    - ``room_lines`` — ordered ``(text, category)`` for the room at
      large: the corpse-disposal announcements, which were always a room
      broadcast rather than a personal line, and stay one. Interleaving
      is preserved: a corpse's disposal line is produced after its own
      loot lines.
    """
    zone_slug = room.zone.slug if room.zone_id else None
    messages = []
    room_lines = []

    current_count, max_carry = get_carry_counts(character)
    swept = 0
    carried_nothing = 0
    capacity_hit = False

    for corpse in lootable:
        swept += 1
        copper = loot_copper(corpse, character)
        if copper > 0:
            copper_str = display_for_zone(copper, zone_slug)
            # v23 B5 amendment 1 (#152): parity with the item-loot lines, which have
            # been reward/loot-color since v22 B2 amendment 1 (#124).
            messages.append(
                (f"You loot {copper_str} from {corpse.display_name}.", 'reward'))
        contents = get_corpse_contents(corpse)
        if copper == 0 and not contents:
            carried_nothing += 1
        for item in contents:
            if current_count >= max_carry:
                messages.append((
                    f"You can't carry any more. ({current_count}/{max_carry} items)",
                    'warn',
                ))
                capacity_hit = True
                break
            line = compose_item_line(item)
            loot_item(item, character)
            # v22 B2 amendment 1 (#124): loot-color per DD §6.
            messages.append((f"You loot {line}.", 'reward'))
            current_count += 1
        if corpse_empty_and_delete(corpse):
            room_lines.append(_disappear_line(corpse))
        if capacity_hit:
            break

    summary = f'Looted {swept} corpse{"s" if swept != 1 else ""}'
    if carried_nothing:
        summary += (f'; {carried_nothing} carried nothing worth taking.')
    else:
        summary += '.'
    messages.append((summary, 'system'))

    return messages, room_lines
