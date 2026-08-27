"""v25.5 (#281): the agent door — the machinery behind the MC egress
consumer's query and action vocabularies (GDD §10.11).

The trust boundary does not move: agents reach the game only through
``MCEgressConsumer`` (Django session auth, live ``agents.shyland``
membership), which is the sole importer of this module. Import
direction (brief §7.4): this module may import from ``consumers``,
``item_utils``, ``models``, ``mc`` and their kin; nothing imports
``mc_door`` except ``mc_consumer``.

Everything on the record: every player-visible line the door causes
goes through ``audited_send`` — emit the ``out`` record (audience =
the target pks), then the group send; no bare ``group_send`` anywhere
in door code. Effect narration tells the truth (``An admin ...``) in
the world's standard colors (#261); bots talk in their talking color
(category ``sudo``) only.
"""

import json
import logging
from datetime import timedelta, timezone as dt_timezone

from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify

from . import mc
from .combat_utils import effective_stats, rescale_bars_for_gear
from .consumers import DIRECTIONS, SkylandConsumer, parse_presence_name
from .envelope import envelope_ts
from .item_utils import (
    SLOT_DISPLAY_NAMES, equip_candidates, generate_item_instance, item_ref,
)
from .models import (
    AgentMemory, Character, CombatSession, EffectInstance, ItemDefinition,
    ItemInstance, MCEvent, Room, record_room_visit_sync,
)

logger = logging.getLogger('shyland.mc')

MAX_ANSWER_LEN = 2000
ITEMS_CAP = 50
# v25.8 (#290/#300): rooms/events list results — the §3 preamble cap.
LIST_CAP = 50
# v25.8 (#294): the memory caps, all refused legibly — never truncated.
MEMORY_MAX_PAYLOAD_BYTES = 4096      # serialized JSON, checked at teach
MEMORY_MAX_ROWS_PER_AGENT = 262144   # = 1 GiB / 4 KiB (operator-ruled)
MEMORY_MAX_NAME_LEN = 60
MEMORY_MAX_BUNDLE_LINES = 50
MEMORY_LIST_CAP = 50
STAT_KEYS = ('str', 'dex', 'end', 'int', 'wis', 'per')
# The v20 #22 authoring law, enforced at runtime for hand-authored
# artifact names (seed_world enforces the same law for seeded names).
RARITY_WORDS = ('common', 'uncommon', 'rare', 'epic', 'legendary', 'artifact')
EQUIPPABLE_TYPES = {'weapon', 'armor', 'accessory', 'bag'}


class DoorError(Exception):
    """A refused frame: ``code`` is the wire error code, ``detail`` the
    human sentence for the result frame."""

    def __init__(self, code, detail=''):
        super().__init__(code)
        self.code = code
        self.detail = detail


# ----------------------------------------------------------------------
# Shared plumbing
# ----------------------------------------------------------------------

def _require_str(params, key, *, max_len=None):
    value = params.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DoorError('bad-params', f"'{key}' must be a non-empty string.")
    value = value.strip()
    if max_len is not None and len(value) > max_len:
        raise DoorError('bad-params',
                        f"'{key}' must be at most {max_len} characters.")
    return value


def _require_int(value, key, *, minimum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        raise DoorError('bad-params', f"'{key}' must be an integer.")
    if minimum is not None and value < minimum:
        raise DoorError('bad-params', f"'{key}' must be >= {minimum}.")
    return value


def _parse_when(params, key):
    """v25.8 (#294/#300): optional ISO-8601 window bound. Naive stamps
    are read as UTC (the project's log law); absent is None."""
    value = params.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise DoorError('bad-params',
                        f"'{key}' must be an ISO-8601 timestamp string.")
    parsed = parse_datetime(value)
    if parsed is None:
        raise DoorError('bad-params',
                        f"'{key}' must be an ISO-8601 timestamp.")
    if timezone.is_naive(parsed):
        parsed = parsed.replace(tzinfo=dt_timezone.utc)
    return parsed


@database_sync_to_async
def _character_by_name(name):
    return (Character.objects
            .select_related('current_room__zone', 'current_room__area',
                            'origin', 'archetype', 'user')
            .filter(name__iexact=name).first())


async def _resolve_character(params, key='name'):
    """All character-name params resolve case-insensitively; no match
    is ``not-found`` (§4)."""
    name = _require_str(params, key)
    char = await _character_by_name(name)
    if char is None:
        raise DoorError('not-found', f'No character named {name!r}.')
    return char


async def _presence_online(pk):
    """Live presence — the ``shyland:online:{pk}`` key. Quiet False on
    any failure: offline delivery is the norm, never an error (§4.2)."""
    try:
        return bool(await mc._get_client().exists(f'shyland:online:{pk}'))
    except Exception:
        return False


def _room_dict(room):
    """The §4.1 room shape: area is a name or null, zone a name."""
    if room is None:
        return None
    return {
        'id': room.id,
        'name': room.name,
        'area': room.area.name if room.area_id else None,
        'zone': room.zone.name,
    }


async def audited_send(group, event, *, agent_name, room_id=None):
    """§6: the door's delivery choke point, mirroring the consumer's
    ``mc_group_send`` discipline — emit the ``out`` record (audience =
    the target pks, resolved at fan-out time honoring the event's
    exclude semantics), then perform the send with the payload
    unchanged. No bare ``group_send`` anywhere in door code."""
    audience = []
    try:
        if group.startswith('player_'):
            audience = [int(group[len('player_'):])]
        elif group.startswith('room_'):
            rid = int(group[len('room_'):])
            exclude_pks = []
            if event.get('exclude_pk') is not None:
                exclude_pks.append(event['exclude_pk'])
            if event.get('exclude_pks'):
                exclude_pks.extend(event['exclude_pks'])
            audience = await mc.resolve_room_audience(
                rid, exclude_pks=exclude_pks)
    except Exception:
        audience = []
    await mc.mc_emit(
        'out', actor_id=None, actor_name=agent_name,
        room_id=room_id, audience=audience,
        data={k: v for k, v in event.items() if k not in ('ts', 'token')},
    )
    await get_channel_layer().group_send(group, event)


async def _send_player_line(pk, text, category, *, agent_name, event=None):
    """One audited personal line; ``event`` rides along for consumer
    branches (``moved``, ``refresh_status``)."""
    payload = {
        'type': 'player_message',
        'text': text,
        'category': category,
        'ts': envelope_ts(),
    }
    if event is not None:
        payload['event'] = event
    await audited_send(f'player_{pk}', payload, agent_name=agent_name)


# ----------------------------------------------------------------------
# Query kinds (§4.1)
# ----------------------------------------------------------------------

async def q_commands(params, agent_name):
    """Derived exactly as connect does it: ``set(DIRECTIONS) |
    set(COMMAND_TABLE)``, with ``ADMIN_VERBS`` listed separately —
    agents see the full vocabulary; the split lets a bot model stealth
    (what a non-member's connect-time list omits)."""
    full = set(DIRECTIONS) | set(SkylandConsumer.COMMAND_TABLE)
    admin = set(SkylandConsumer.ADMIN_VERBS)
    return {'verbs': sorted(full - admin), 'admin_verbs': sorted(admin)}


async def q_who_online(params, agent_name):
    client = mc._get_client()
    keys = await client.keys('shyland:online:*')
    characters = []
    if keys:
        values = await client.mget(*keys)
        for key, raw in zip(keys, values):
            if not raw:
                continue
            key_text = key.decode() if isinstance(key, bytes) else key
            try:
                pk = int(key_text.rsplit(':', 1)[1])
            except (ValueError, IndexError):
                continue
            characters.append({'id': pk, 'name': parse_presence_name(raw)})
    characters.sort(key=lambda c: c['name'])
    return {'characters': characters}


async def q_where_is(params, agent_name):
    char = await _resolve_character(params)
    return {
        'id': char.pk,
        'name': char.name,
        'online': await _presence_online(char.pk),
        'room': _room_dict(char.current_room),
    }


@database_sync_to_async
def _character_payload(char):
    eff = effective_stats(char)
    return {
        'id': char.pk,
        'name': char.name,
        'level': char.level,
        'xp': char.xp,
        'origin': char.origin.name,
        'archetype': char.archetype.name,
        'stats_base': {k: getattr(char, f'stat_{k}') for k in STAT_KEYS},
        'stats_effective': {k: eff[k] for k in STAT_KEYS},
        'vitality': [char.vitality_current, char.vitality_max],
        'acuity': round(char.acuity_current, 2),
        'longevity': [char.longevity_current, char.longevity_max],
        'copper': char.copper,
        'unspent_stat_points': char.unspent_stat_points,
        'room': _room_dict(char.current_room),
    }


async def q_character(params, agent_name):
    char = await _resolve_character(params)
    data = await _character_payload(char)
    data['online'] = await _presence_online(char.pk)
    return data


@database_sync_to_async
def _items_payload(contains):
    qs = ItemDefinition.objects.all()
    if contains:
        qs = qs.filter(name__icontains=contains)
    rows = list(qs.order_by('name')[:ITEMS_CAP + 1])
    truncated = len(rows) > ITEMS_CAP
    return {
        'definitions': [
            {
                'id': d.id,
                'slug': d.slug,
                'name': d.name,
                'item_type': d.item_type,
                'valid_slots': d.valid_slots,
                'is_two_handed': d.is_two_handed,
                'tier_material_mk_min': d.tier_material_mk_min,
                'tier_material_mk_max': d.tier_material_mk_max,
            }
            for d in rows[:ITEMS_CAP]
        ],
        'truncated': truncated,
    }


async def q_items(params, agent_name):
    contains = params.get('contains', '')
    if contains is None:
        contains = ''
    if not isinstance(contains, str):
        raise DoorError('bad-params', "'contains' must be a string.")
    return await _items_payload(contains)


@database_sync_to_async
def _is_admin(char):
    """Live ``admins.shyland`` membership (#273) — never cached."""
    return char.user.groups.filter(name='admins.shyland').exists()


async def q_is_admin(params, agent_name):
    char = await _resolve_character(params)
    return {'is_admin': await _is_admin(char)}


def _item_row(item):
    """v25.7 (#293): the inventory-roster row — the shared field set the
    ``inventory`` query lists and the ``item`` query extends. Names come
    from the definition: admin reads show true state (the no-leak rule
    governs world speech, which queries never touch)."""
    d = item.definition
    return {
        'id': item.pk,
        'slug': d.slug,
        'name': d.name,
        'item_type': d.item_type,
        'mk_tier': item.mk_tier,
        'rarity': item.rarity,
        'durability_current': item.durability_current,
        'is_broken': item.is_broken,
        'is_soulbound': item.is_soulbound,
        'is_equipped': item.is_equipped,
        'equipped_slot': item.equipped_slot,
    }


@database_sync_to_async
def _inventory_payload(char):
    items = list(char.inventory.select_related('definition').order_by('pk'))
    return {
        'character_id': char.pk,
        'character_name': char.name,
        'count': len(items),
        'items': [_item_row(i) for i in items],
    }


async def q_inventory(params, agent_name):
    """v25.7 (#293): the owner-wide state report — uncapped, every
    instance the character owns, equipped included (deliberately unlike
    the player ``inventory`` command's protective pools). ``ITEMS_CAP``
    remains a catalog (``items``) concern."""
    char = await _resolve_character(params)
    return await _inventory_payload(char)


@database_sync_to_async
def _item_payload(item_id):
    item = (ItemInstance.objects
            .select_related('definition', 'owner',
                            'current_room__zone', 'current_room__area')
            .filter(pk=item_id).first())
    if item is None:
        raise DoorError('not-found', f'No item instance with id {item_id}.')
    row = _item_row(item)
    row.update({
        'rolled_primary_stats': item.rolled_primary_stats,
        'rolled_secondary_stats': item.rolled_secondary_stats,
        'damage_midpoint': item.damage_midpoint,
        'damage_spread': item.damage_spread,
        'is_cursed': item.is_cursed,
        'curse_identified': item.curse_identified,
        'is_identified': item.is_identified,
        'is_unidentifiable': item.is_unidentifiable,
        'owner': ({'id': item.owner_id, 'name': item.owner.name}
                  if item.owner_id else None),
        'room': _room_dict(item.current_room),
    })
    return row


async def q_item(params, agent_name):
    """v25.7 (#293/#289): one instance at full fidelity, true state —
    curse and identification flags exactly as stored."""
    item_id = _require_int(params.get('item_id'), 'item_id')
    return await _item_payload(item_id)


# ----------------------------------------------------------------------
# Action kinds (§4.2)
# ----------------------------------------------------------------------

async def a_answer(params, agent_name):
    """#273: the delivery gate — the target's live ``admins.shyland``
    membership is authoritative regardless of what the bot concluded.
    Offline is ``ok: true, delivered: false``, never an error —
    silence is the norm."""
    char = await _resolve_character(params, key='to')
    text = params.get('text')
    if not isinstance(text, str) or not text or len(text) > MAX_ANSWER_LEN:
        raise DoorError(
            'bad-params',
            f"'text' must be a string of 1-{MAX_ANSWER_LEN} characters.")
    if not await _is_admin(char):
        raise DoorError(
            'not-admin',
            f'{char.name} is not an admin; answers deliver only to '
            f'admins.shyland members.')
    delivered = await _presence_online(char.pk)
    if delivered:
        # Words carry identity; the sudo color reinforces (§5.1).
        await _send_player_line(char.pk, f'sudo: {text}', 'sudo',
                                agent_name=agent_name)
    return {'delivered': delivered}


@database_sync_to_async
def _gift_item(char, slug, mk_tier, rarity):
    definition = ItemDefinition.objects.filter(slug=slug).first()
    if definition is None:
        raise DoorError('not-found', f'No item definition with slug {slug!r}.')
    try:
        item = generate_item_instance(definition, mk_tier, rarity,
                                      owner=char, gift=True)
    except ValueError as exc:
        # The Mk-mismatch guard (#211) surfaces with its own message.
        raise DoorError('invalid-item', str(exc))
    item.save()
    return item, f'An admin has given you {item_ref(item)}.'


async def a_gift(params, agent_name):
    """Capacity is deliberately not checked — an admin gift lands
    regardless of carry state (recorded design point, §4.2)."""
    char = await _resolve_character(params, key='to')
    slug = _require_str(params, 'slug')
    mk_tier = _require_int(params.get('mk_tier'), 'mk_tier', minimum=1)
    rarity = params.get('rarity')
    if not isinstance(rarity, str):
        raise DoorError('bad-params', "'rarity' must be a string.")
    if rarity == ItemInstance.ARTIFACT:
        raise DoorError('artifact-requires-create',
                        'Artifacts are hand-authored — use create_artifact.')
    if rarity not in {code for code, _ in ItemInstance.RARITY_CHOICES}:
        raise DoorError('bad-params', f'Unknown rarity {rarity!r}.')
    item, line = await _gift_item(char, slug, mk_tier, rarity)
    if await _presence_online(char.pk):
        await _send_player_line(char.pk, line, 'reward',
                                agent_name=agent_name)
    return {'item_id': item.pk}


def _validate_stat_entries(entries, key, *, allow_floor):
    """Exactly the rolled-entry shape generation produces (§5.4):
    ``{"stat": str, "value": int}`` plus an optional ``"floor"`` int on
    primary entries only."""
    if entries is None:
        return []
    if not isinstance(entries, list):
        raise DoorError('bad-params', f"'{key}' must be a list.")
    allowed = {'stat', 'value', 'floor'} if allow_floor else {'stat', 'value'}
    cleaned = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) - allowed:
            raise DoorError(
                'bad-params',
                f"Each '{key}' entry must be an object with 'stat' and "
                f"'value'{' (and optional floor)' if allow_floor else ''}.")
        stat = entry.get('stat')
        if not isinstance(stat, str) or not stat:
            raise DoorError('bad-params',
                            f"'{key}' entry 'stat' must be a non-empty string.")
        value = _require_int(entry.get('value'), f'{key}.value')
        clean = {'stat': stat, 'value': value}
        if 'floor' in entry:
            clean['floor'] = _require_int(entry.get('floor'), f'{key}.floor')
        cleaned.append(clean)
    return cleaned


def _validate_artifact_spec(spec):
    """The §5.4 table, table-authoritative. Returns the normalized spec;
    every violation is ``bad-params`` except name collisions, which the
    builder reports as ``name-taken``."""
    if not isinstance(spec, dict):
        raise DoorError('bad-params', "'spec' must be an object.")
    allowed = {
        'name', 'item_type', 'description', 'genre_tag', 'mk_tier',
        'base_value', 'valid_slots', 'is_two_handed', 'damage_midpoint',
        'damage_spread', 'armor_base', 'primary_stats', 'secondary_stats',
        'is_unidentifiable', 'mystery_name', 'mystery_description',
    }
    unknown = set(spec) - allowed
    if unknown:
        raise DoorError('bad-params',
                        f'Unknown spec keys: {sorted(unknown)}.')

    name = spec.get('name')
    if not isinstance(name, str) or not name.strip():
        raise DoorError('bad-params', "'name' must be a non-empty string.")
    name = name.strip()
    if len(name) > 200:
        raise DoorError('bad-params', "'name' must be at most 200 characters.")
    if name.split()[0].lower() in RARITY_WORDS:
        raise DoorError(
            'bad-params',
            'Artifact names may not begin with a rarity word — rarity '
            'words are a closed grammar vocabulary (the #22 authoring law).')

    item_type = spec.get('item_type')
    if item_type not in {code for code, _ in ItemDefinition.ITEM_TYPE_CHOICES}:
        raise DoorError('bad-params', f'Unknown item_type {item_type!r}.')

    description = spec.get('description')
    if not isinstance(description, str) or not description.strip():
        raise DoorError('bad-params',
                        "'description' must be non-empty text.")

    genre_tag = spec.get('genre_tag')
    if genre_tag not in {code for code, _ in ItemDefinition.GENRE_TAG_CHOICES}:
        raise DoorError('bad-params', f'Unknown genre_tag {genre_tag!r}.')

    mk_tier = _require_int(spec.get('mk_tier'), 'mk_tier', minimum=1)
    base_value = _require_int(spec.get('base_value'), 'base_value', minimum=0)

    valid_slots = spec.get('valid_slots', [])
    if not isinstance(valid_slots, list) or any(
            slot not in SLOT_DISPLAY_NAMES for slot in valid_slots):
        raise DoorError('bad-params',
                        "'valid_slots' must be a list of slot codes.")
    if item_type in EQUIPPABLE_TYPES:
        if not valid_slots:
            raise DoorError(
                'bad-params',
                f"'valid_slots' is required non-empty for {item_type}.")
    elif valid_slots:
        raise DoorError('bad-params',
                        f"'valid_slots' must be [] for {item_type}.")

    is_two_handed = spec.get('is_two_handed', False)
    if not isinstance(is_two_handed, bool):
        raise DoorError('bad-params', "'is_two_handed' must be a boolean.")

    damage_midpoint = spec.get('damage_midpoint')
    damage_spread = spec.get('damage_spread')
    if item_type == ItemDefinition.WEAPON:
        for key, value in (('damage_midpoint', damage_midpoint),
                           ('damage_spread', damage_spread)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise DoorError('bad-params',
                                f"'{key}' (a number) is required for weapons.")
        damage_midpoint = float(damage_midpoint)
        damage_spread = float(damage_spread)
    elif damage_midpoint is not None or damage_spread is not None:
        raise DoorError('bad-params',
                        'Damage keys apply to weapons only.')

    armor_base = spec.get('armor_base')
    if item_type == ItemDefinition.ARMOR:
        if armor_base is None:
            armor_base = 0.0
        elif (isinstance(armor_base, bool)
                or not isinstance(armor_base, (int, float))
                or armor_base < 0):
            raise DoorError('bad-params', "'armor_base' must be a float >= 0.")
        armor_base = float(armor_base)
    elif armor_base is not None:
        raise DoorError('bad-params', "'armor_base' applies to armor only.")
    else:
        armor_base = 0.0

    primary_stats = _validate_stat_entries(
        spec.get('primary_stats'), 'primary_stats', allow_floor=True)
    secondary_stats = _validate_stat_entries(
        spec.get('secondary_stats'), 'secondary_stats', allow_floor=False)

    is_unidentifiable = spec.get('is_unidentifiable', False)
    if not isinstance(is_unidentifiable, bool):
        raise DoorError('bad-params', "'is_unidentifiable' must be a boolean.")
    mystery_name = spec.get('mystery_name', '')
    mystery_description = spec.get('mystery_description', '')
    for key, value in (('mystery_name', mystery_name),
                       ('mystery_description', mystery_description)):
        if not isinstance(value, str):
            raise DoorError('bad-params', f"'{key}' must be a string.")
    if is_unidentifiable and not (mystery_name.strip()
                                  and mystery_description.strip()):
        raise DoorError(
            'bad-params',
            "'mystery_name' and 'mystery_description' are required "
            "together with 'is_unidentifiable': true.")
    if (mystery_name or mystery_description) and not is_unidentifiable:
        raise DoorError(
            'bad-params',
            "'mystery_name'/'mystery_description' are required together "
            "with 'is_unidentifiable': true.")

    return {
        'name': name,
        'item_type': item_type,
        'description': description,
        'genre_tag': genre_tag,
        'mk_tier': mk_tier,
        'base_value': base_value,
        'valid_slots': valid_slots,
        'is_two_handed': is_two_handed,
        'damage_midpoint': damage_midpoint,
        'damage_spread': damage_spread,
        'armor_base': armor_base,
        'primary_stats': primary_stats,
        'secondary_stats': secondary_stats,
        'is_unidentifiable': is_unidentifiable,
        'mystery_name': mystery_name,
        'mystery_description': mystery_description,
    }


@database_sync_to_async
def _create_artifact(char, spec):
    """The §5.4 builder — never through ``generate_item_instance``
    (forbidden for artifacts). ``scaling_base``/``scaling_factor`` are
    required floats on the definition, meaningless for hand-authored
    stats — authored 0.0 by design. Artifacts are one-of-a-kind: any
    name or slug collision is ``name-taken``."""
    name = spec['name']
    if ItemDefinition.objects.filter(name__iexact=name).exists():
        raise DoorError('name-taken',
                        f'An item definition named {name!r} already exists.')
    slug = slugify(name)
    if not slug:
        raise DoorError('bad-params', "'name' yields an empty slug.")
    if ItemDefinition.objects.filter(slug=slug).exists():
        raise DoorError('name-taken', f'Slug {slug!r} already exists.')
    try:
        with transaction.atomic():
            definition = ItemDefinition.objects.create(
                name=name,
                slug=slug,
                item_type=spec['item_type'],
                genre_tag=spec['genre_tag'],
                description=spec['description'],
                base_value=spec['base_value'],
                scaling_base=0.0,
                scaling_factor=0.0,
                valid_slots=spec['valid_slots'],
                is_two_handed=spec['is_two_handed'],
                armor_base=spec['armor_base'],
                suppress_mk_suffix=False,
                mystery_name=spec['mystery_name'],
                mystery_description=spec['mystery_description'],
            )
            item = ItemInstance(
                definition=definition,
                owner=char,
                mk_tier=spec['mk_tier'],
                rarity=ItemInstance.ARTIFACT,
                rolled_primary_stats=spec['primary_stats'],
                rolled_secondary_stats=spec['secondary_stats'],
                damage_midpoint=spec['damage_midpoint'],
                damage_spread=spec['damage_spread'],
                is_soulbound=True,
                soulbound_to=char,
                is_identified=not spec['is_unidentifiable'],
                is_unidentifiable=spec['is_unidentifiable'],
            )
            item.save()
    except IntegrityError:
        raise DoorError('name-taken',
                        f'An item definition named {name!r} already exists.')
    return definition, item, f'An admin has given you {item_ref(item)}.'


async def a_create_artifact(params, agent_name):
    char = await _resolve_character(params, key='to')
    spec = _validate_artifact_spec(params.get('spec'))
    definition, item, line = await _create_artifact(char, spec)
    if await _presence_online(char.pk):
        await _send_player_line(char.pk, line, 'reward',
                                agent_name=agent_name)
    return {'definition_id': definition.pk, 'item_id': item.pk}


@database_sync_to_async
def _strip(char):
    equipped = list(char.inventory.filter(is_equipped=True))
    if not equipped:
        raise DoorError('nothing-equipped',
                        f'{char.name} has nothing equipped.')
    # The snapshot lands before any unequip — a crash mid-loop must
    # never lose the outfit.
    snapshot = [{'instance_id': item.pk, 'slot': item.equipped_slot}
                for item in equipped]
    Character.objects.filter(pk=char.pk).update(outfit_snapshot=snapshot)
    for item in equipped:
        # Deliberately bypassing _unequip_blocked_reason: this is an
        # admin tool, and the operator accepts the resulting #275
        # over-capacity state knowingly (ruled 2026-08-22).
        item.is_equipped = False
        item.equipped_slot = ''
        item.save()
    rescale_bars_for_gear(char)
    return len(equipped)


async def a_strip(params, agent_name):
    char = await _resolve_character(params)
    stripped = await _strip(char)
    if await _presence_online(char.pk):
        await _send_player_line(
            char.pk,
            'An admin has unequipped your gear; it is in your inventory.',
            'system', agent_name=agent_name, event='refresh_status')
    return {'stripped': stripped}


@database_sync_to_async
def _dress(char):
    snapshot = Character.objects.values_list(
        'outfit_snapshot', flat=True).get(pk=char.pk)
    if not snapshot:
        if snapshot is not None:
            # An empty-list snapshot is consumed like any other attempt.
            Character.objects.filter(pk=char.pk).update(outfit_snapshot=None)
        raise DoorError('no-outfit', f'{char.name} holds no outfit snapshot.')
    restored = 0
    missing = []
    try:
        for entry in snapshot:
            instance_id = entry.get('instance_id') if isinstance(entry, dict) else None
            slot = entry.get('slot', '') if isinstance(entry, dict) else ''
            item = (ItemInstance.objects.filter(pk=instance_id).first()
                    if instance_id is not None else None)
            if item is None or item.owner_id != char.pk or item.is_equipped:
                missing.append(instance_id)
                continue
            # Byte-consistent with equip_item: equip re-soulbinds.
            item.is_equipped = True
            item.equipped_slot = slot or ''
            item.is_soulbound = True
            item.soulbound_to = char
            item.save()
            restored += 1
        rescale_bars_for_gear(char)
    finally:
        # The snapshot is always consumed by a dress attempt, whatever
        # the outcome.
        Character.objects.filter(pk=char.pk).update(outfit_snapshot=None)
    return restored, missing


async def a_dress(params, agent_name):
    char = await _resolve_character(params)
    restored, missing = await _dress(char)
    if await _presence_online(char.pk):
        await _send_player_line(
            char.pk, 'An admin has re-equipped your gear.',
            'system', agent_name=agent_name, event='refresh_status')
    return {'restored': restored, 'missing': missing}


@database_sync_to_async
def _in_combat(char):
    return CombatSession.objects.filter(
        is_active=True, characters=char).exists()


@database_sync_to_async
def _room_by_id(room_id):
    return (Room.objects.select_related('zone', 'area')
            .filter(pk=room_id).first())


@database_sync_to_async
def _move_character(char, destination, record_visit):
    Character.objects.filter(pk=char.pk).update(current_room=destination)
    char.current_room = destination
    char.current_room_id = destination.pk
    if record_visit:
        record_room_visit_sync(char, destination)


async def a_move(params, agent_name):
    """Online targets get the full arrival treatment through their own
    consumer (the ``moved`` branch — modeled on respawn — re-seats
    groups and records the visit, so a first visit announces zone
    completion exactly like a walked arrival). Offline targets get the
    DB update + visit only, no broadcasts."""
    char = await _resolve_character(params)
    has_name = 'to_name' in params
    has_id = 'to_room_id' in params
    if has_name == has_id:
        raise DoorError(
            'bad-params',
            "Exactly one of 'to_name' or 'to_room_id' is required.")
    if await _in_combat(char):
        # No landmines in the combat model: a combat session's room
        # binding must never watch its character teleport away.
        raise DoorError('in-combat',
                        f'{char.name} is in an active combat session.')
    if has_name:
        other = await _resolve_character(params, key='to_name')
        destination = other.current_room
        if destination is None:
            raise DoorError('not-found', f'{other.name} is in no room.')
    else:
        room_id = _require_int(params.get('to_room_id'), 'to_room_id')
        destination = await _room_by_id(room_id)
        if destination is None:
            raise DoorError('not-found', f'No room with id {room_id}.')
    origin_room_id = char.current_room_id
    # v25.8 (#290): the receipt's origin — captured before the move,
    # already select_related through _character_by_name.
    origin_room = char.current_room
    online = await _presence_online(char.pk)
    await _move_character(char, destination, record_visit=not online)
    if online:
        # The cmd_move sentence shapes, pk-excluded (the door has no
        # channel name; room_message honors exclude_pk at delivery).
        if origin_room_id is not None and origin_room_id != destination.id:
            await audited_send(
                f'room_{origin_room_id}',
                {'type': 'room_message', 'text': f'{char.name} has left.',
                 'category': 'system', 'exclude_pk': char.pk,
                 'ts': envelope_ts()},
                agent_name=agent_name, room_id=origin_room_id)
        if origin_room_id != destination.id:
            await audited_send(
                f'room_{destination.id}',
                {'type': 'room_message', 'text': f'{char.name} has arrived.',
                 'category': 'system', 'exclude_pk': char.pk,
                 'ts': envelope_ts()},
                agent_name=agent_name, room_id=destination.id)
        # Operator-authored, verbatim (§5.3).
        await _send_player_line(
            char.pk, 'An admin moved you to a new room.', 'system',
            agent_name=agent_name, event='moved')
    return {'room': _room_dict(destination),
            'from_room': _room_dict(origin_room)}


# ----------------------------------------------------------------------
# Granular item control (v25.7 — #287/#288/#289/#293)
# ----------------------------------------------------------------------

def _owned_item(char, item_id):
    """The shared write-path addressing law (§4 of the v25.7 brief):
    the instance must exist and be owned by the named character — a
    stale id is a refusal, never a guess. Sync; call inside the
    handler's atomic block."""
    item = (ItemInstance.objects
            .select_related('definition', 'owner')
            .filter(pk=item_id).first())
    if item is None:
        raise DoorError('not-found', f'No item instance with id {item_id}.')
    if item.owner_id != char.pk:
        if item.owner_id is None:
            raise DoorError(
                'not-owner',
                f'Item {item_id} is owned by no character '
                f'(room floor or corpse).')
        raise DoorError(
            'not-owner',
            f'Item {item_id} is owned by {item.owner.name}, '
            f'not {char.name}.')
    return item


@database_sync_to_async
def _remove_item(char, item_id):
    """#287: destruction, never transfer — the ``_strip`` posture (no
    combat gate, no protective guards). An artifact removal deletes the
    definition too (the CASCADE takes the instance), freeing the unique
    name for re-authoring. The curse ends with the item (operator-ruled):
    the death-teardown pattern applied to one effect."""
    with transaction.atomic():
        item = _owned_item(char, item_id)
        ref = item_ref(item)
        if item.active_curse_id is not None:
            item.active_curse.component_instances.filter(
                is_active=True).update(
                    is_active=False, removed_by='item-removed')
            EffectInstance.objects.filter(pk=item.active_curse_id).update(
                is_active=False, removed_by='item-removed')
        was_equipped = item.is_equipped
        if item.rarity == ItemInstance.ARTIFACT:
            item.definition.delete()
            definition_removed = True
        else:
            item.delete()
            definition_removed = False
        if was_equipped:
            # The bar law binds every max-changing mutation.
            rescale_bars_for_gear(char)
    return ref, was_equipped, definition_removed


async def a_remove_item(params, agent_name):
    char = await _resolve_character(params)
    item_id = _require_int(params.get('item_id'), 'item_id')
    ref, was_equipped, definition_removed = await _remove_item(char, item_id)
    if await _presence_online(char.pk):
        await _send_player_line(
            char.pk, f'An admin has taken {ref} from you.', 'system',
            agent_name=agent_name,
            event='refresh_status' if was_equipped else None)
    return {'item_id': item_id, 'definition_removed': definition_removed}


# The #289 raw-set whitelists: the admin's values land exactly; nothing
# re-rolls or re-derives. ``item_type`` is deliberately not editable.
INSTANCE_EDIT_KEYS = frozenset({
    'mk_tier', 'rarity', 'rolled_primary_stats', 'rolled_secondary_stats',
    'damage_midpoint', 'damage_spread', 'durability_current',
})
ARTIFACT_DEFINITION_EDIT_KEYS = frozenset({
    'name', 'description', 'base_value', 'valid_slots', 'is_two_handed',
    'armor_base', 'mystery_name', 'mystery_description', 'genre_tag',
})


def _edit_instance_fields(item, changes):
    if 'mk_tier' in changes:
        item.mk_tier = _require_int(changes['mk_tier'], 'mk_tier', minimum=1)
    if 'rarity' in changes:
        rarity = changes['rarity']
        if rarity not in {code for code, _ in ItemInstance.RARITY_CHOICES}:
            raise DoorError('bad-params', f'Unknown rarity {rarity!r}.')
        item.rarity = rarity
    if 'rolled_primary_stats' in changes:
        item.rolled_primary_stats = _validate_stat_entries(
            changes['rolled_primary_stats'], 'rolled_primary_stats',
            allow_floor=True)
    if 'rolled_secondary_stats' in changes:
        item.rolled_secondary_stats = _validate_stat_entries(
            changes['rolled_secondary_stats'], 'rolled_secondary_stats',
            allow_floor=False)
    for key in ('damage_midpoint', 'damage_spread'):
        if key in changes:
            value = changes[key]
            if value is not None:
                if (isinstance(value, bool)
                        or not isinstance(value, (int, float)) or value < 0):
                    raise DoorError(
                        'bad-params',
                        f"'{key}' must be a number >= 0, or null.")
                value = float(value)
            setattr(item, key, value)
    if (item.damage_midpoint is None) != (item.damage_spread is None):
        raise DoorError(
            'bad-params',
            "'damage_midpoint' and 'damage_spread' must be both set or "
            'both null after the edit.')
    if 'durability_current' in changes:
        value = changes['durability_current']
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not 0 <= value <= 100):
            raise DoorError(
                'bad-params',
                "'durability_current' must be a number between 0 and 100.")
        item.durability_current = float(value)
        # The invariant the durability system maintains everywhere.
        item.is_broken = (item.durability_current == 0)


def _edit_definition_fields(item, defn, changes):
    """Artifact-only definition edits, validated by the same rules
    ``_validate_artifact_spec`` applies at creation. A rename re-runs
    the unique-name law excluding the definition itself."""
    if 'name' in changes:
        name = changes['name']
        if not isinstance(name, str) or not name.strip():
            raise DoorError('bad-params', "'name' must be a non-empty string.")
        name = name.strip()
        if len(name) > 200:
            raise DoorError('bad-params',
                            "'name' must be at most 200 characters.")
        if name.split()[0].lower() in RARITY_WORDS:
            raise DoorError(
                'bad-params',
                'Artifact names may not begin with a rarity word — rarity '
                'words are a closed grammar vocabulary (the #22 authoring '
                'law).')
        if (ItemDefinition.objects.exclude(pk=defn.pk)
                .filter(name__iexact=name).exists()):
            raise DoorError(
                'name-taken',
                f'An item definition named {name!r} already exists.')
        slug = slugify(name)
        if not slug:
            raise DoorError('bad-params', "'name' yields an empty slug.")
        if (ItemDefinition.objects.exclude(pk=defn.pk)
                .filter(slug=slug).exists()):
            raise DoorError('name-taken', f'Slug {slug!r} already exists.')
        defn.name = name
        defn.slug = slug
    if 'description' in changes:
        description = changes['description']
        if not isinstance(description, str) or not description.strip():
            raise DoorError('bad-params', "'description' must be non-empty text.")
        defn.description = description
    if 'base_value' in changes:
        defn.base_value = _require_int(
            changes['base_value'], 'base_value', minimum=0)
    if 'valid_slots' in changes:
        valid_slots = changes['valid_slots']
        if not isinstance(valid_slots, list) or any(
                slot not in SLOT_DISPLAY_NAMES for slot in valid_slots):
            raise DoorError('bad-params',
                            "'valid_slots' must be a list of slot codes.")
        if defn.item_type in EQUIPPABLE_TYPES:
            if not valid_slots:
                raise DoorError(
                    'bad-params',
                    f"'valid_slots' is required non-empty for "
                    f'{defn.item_type}.')
        elif valid_slots:
            raise DoorError('bad-params',
                            f"'valid_slots' must be [] for {defn.item_type}.")
        defn.valid_slots = valid_slots
    if 'is_two_handed' in changes:
        if not isinstance(changes['is_two_handed'], bool):
            raise DoorError('bad-params', "'is_two_handed' must be a boolean.")
        defn.is_two_handed = changes['is_two_handed']
    if 'armor_base' in changes:
        armor_base = changes['armor_base']
        if defn.item_type == ItemDefinition.ARMOR:
            if armor_base is None:
                armor_base = 0.0
            elif (isinstance(armor_base, bool)
                    or not isinstance(armor_base, (int, float))
                    or armor_base < 0):
                raise DoorError('bad-params',
                                "'armor_base' must be a float >= 0.")
            defn.armor_base = float(armor_base)
        elif armor_base is not None:
            raise DoorError('bad-params',
                            "'armor_base' applies to armor only.")
        else:
            defn.armor_base = 0.0
    if 'genre_tag' in changes:
        genre_tag = changes['genre_tag']
        if genre_tag not in {code for code, _
                             in ItemDefinition.GENRE_TAG_CHOICES}:
            raise DoorError('bad-params', f'Unknown genre_tag {genre_tag!r}.')
        defn.genre_tag = genre_tag
    if 'mystery_name' in changes or 'mystery_description' in changes:
        for key in ('mystery_name', 'mystery_description'):
            if key in changes:
                if not isinstance(changes[key], str):
                    raise DoorError('bad-params', f"'{key}' must be a string.")
                setattr(defn, key, changes[key])
        # The creation coupling, judged on the post-edit state.
        has_both = (defn.mystery_name.strip()
                    and defn.mystery_description.strip())
        has_any = (defn.mystery_name or defn.mystery_description)
        if item.is_unidentifiable and not has_both:
            raise DoorError(
                'bad-params',
                "'mystery_name' and 'mystery_description' must both be "
                'non-empty while the instance is unidentifiable.')
        if has_any and not item.is_unidentifiable:
            raise DoorError(
                'bad-params',
                "'mystery_name'/'mystery_description' apply only to an "
                'unidentifiable instance.')


@database_sync_to_async
def _edit_item(char, item_id, changes):
    """#289: whole-request semantics — any key outside the applicable
    whitelists refuses everything (the atomic block guarantees no
    partial application)."""
    with transaction.atomic():
        item = _owned_item(char, item_id)
        defn = item.definition
        artifact_rarity = item.rarity == ItemInstance.ARTIFACT
        definition_changed = False
        for key in changes:
            if key in INSTANCE_EDIT_KEYS:
                continue
            if key in ARTIFACT_DEFINITION_EDIT_KEYS:
                if not artifact_rarity:
                    raise DoorError(
                        'not-artifact',
                        f"'{key}' edits the definition — {defn.name!r} is "
                        f'a shared template; definition-side edits apply '
                        f'to artifacts only.')
                definition_changed = True
                continue
            raise DoorError('bad-params', f'Unknown edit key {key!r}.')
        _edit_instance_fields(item, changes)
        if definition_changed:
            _edit_definition_fields(item, defn, changes)
            defn.save()
        item.save()
        was_equipped = item.is_equipped
        if was_equipped:
            rescale_bars_for_gear(char)
        # Composed after the edit, so a rename shows the new name.
        ref = item_ref(item)
    return ref, was_equipped, definition_changed


async def a_edit_item(params, agent_name):
    char = await _resolve_character(params)
    item_id = _require_int(params.get('item_id'), 'item_id')
    changes = params.get('changes')
    if not isinstance(changes, dict) or not changes:
        raise DoorError('bad-params', "'changes' must be a non-empty object.")
    ref, was_equipped, definition_changed = await _edit_item(
        char, item_id, changes)
    if await _presence_online(char.pk):
        await _send_player_line(
            char.pk, f'An admin has altered {ref}.', 'system',
            agent_name=agent_name,
            event='refresh_status' if was_equipped else None)
    return {'item_id': item_id, 'changed': sorted(changes),
            'definition_changed': definition_changed}


@database_sync_to_async
def _equip_item_admin(char, item_id, slot):
    """#288: targeted equip through the player's own slot-resolution
    algorithm (``equip_candidates``). Structural rules always hold
    (valid slots, capacity, two-hander geometry); protective guards
    yield (the ``_strip`` precedent: cursed comes off, capacity
    ignored). ``outfit_snapshot`` is never read, written, or consumed."""
    with transaction.atomic():
        item = _owned_item(char, item_id)
        if item.is_equipped:
            raise DoorError('already-equipped',
                            f'{item_ref(item)} is already equipped.')
        defn = item.definition
        if slot is not None and slot not in defn.valid_slots:
            valid = ', '.join(defn.valid_slots) or '(none — not equippable)'
            raise DoorError('bad-slot',
                            f'Valid slots for {defn.name}: {valid}.')
        equipped_items = list(
            char.inventory.filter(is_equipped=True)
            .select_related('definition'))
        candidates = equip_candidates(defn, equipped_items)
        if slot is not None:
            candidates = [(s, d) for s, d in candidates if s == slot]
        if not candidates:
            raise DoorError('bad-slot', f'{defn.name} is not equippable.')
        free = next(((s, d) for s, d in candidates if not d), None)
        if free is not None:
            target_slot, displaced = free
        else:
            min_size = min(len(d) for _, d in candidates)
            minimal = [(s, d) for s, d in candidates if len(d) == min_size]
            # Candidates displacing the same set are one option; distinct
            # sets are the admin's choice — refuse, structured enough for
            # the bot to ask or retry with an explicit slot.
            distinct = {}
            for s, d in minimal:
                distinct.setdefault(frozenset(i.pk for i in d), (s, d))
            if len(distinct) > 1:
                options = '; '.join(
                    f'{s}: ' + ' + '.join(
                        f'{item_ref(i)} (id {i.pk})' for i in d)
                    for s, d in distinct.values())
                raise DoorError(
                    'ambiguous',
                    f'Equipping would displace one of: {options}. Name a '
                    f'slot or unequip the chosen item first.')
            target_slot, displaced = next(iter(distinct.values()))
        for equipped in displaced:
            # Flags only — protective guards bypassed admin-style.
            equipped.is_equipped = False
            equipped.equipped_slot = ''
            equipped.save()
        # Byte-consistent with equip_item/_dress: equip re-soulbinds.
        item.is_equipped = True
        item.equipped_slot = target_slot
        item.is_soulbound = True
        item.soulbound_to = char
        item.save()
        rescale_bars_for_gear(char)
        ref = item_ref(item)
    return ref, target_slot, [i.pk for i in displaced]


async def a_equip_item(params, agent_name):
    char = await _resolve_character(params)
    item_id = _require_int(params.get('item_id'), 'item_id')
    slot = params.get('slot')
    if slot is not None:
        if not isinstance(slot, str) or not slot.strip():
            raise DoorError('bad-params',
                            "'slot' must be a non-empty string.")
        slot = slot.strip()
    ref, target_slot, displaced = await _equip_item_admin(char, item_id, slot)
    if await _presence_online(char.pk):
        await _send_player_line(
            char.pk, f'An admin has equipped {ref} on you.', 'system',
            agent_name=agent_name, event='refresh_status')
    return {'item_id': item_id, 'slot': target_slot, 'displaced': displaced}


@database_sync_to_async
def _unequip_item_admin(char, item_id):
    """#288: targeted unequip — no protective guards (cursed comes off;
    over-capacity accepted, the #275 acceptance). Curse *effects*
    untouched — unequip is not removal. ``outfit_snapshot`` untouched."""
    with transaction.atomic():
        item = _owned_item(char, item_id)
        if not item.is_equipped:
            raise DoorError('not-equipped',
                            f'{item_ref(item)} is not equipped.')
        item.is_equipped = False
        item.equipped_slot = ''
        item.save()
        rescale_bars_for_gear(char)
        ref = item_ref(item)
    return ref


async def a_unequip_item(params, agent_name):
    char = await _resolve_character(params)
    item_id = _require_int(params.get('item_id'), 'item_id')
    ref = await _unequip_item_admin(char, item_id)
    if await _presence_online(char.pk):
        await _send_player_line(
            char.pk,
            f'An admin has unequipped {ref}; it is in your inventory.',
            'system', agent_name=agent_name, event='refresh_status')
    return {'item_id': item_id}


# ----------------------------------------------------------------------
# Agent memory (v25.8 — #294)
# ----------------------------------------------------------------------

MEMORY_KINDS = {code for code, _ in AgentMemory.KIND_CHOICES}


def _agent_user(agent_name):
    """The requesting bot's own User row — every memory verb scopes to
    it; one bot never reads or forgets another's store. Sync; call
    inside the handler's database context."""
    return User.objects.get(username=agent_name)


def _validate_memory_data(kind, data):
    """Kind-aware validation at teach time — kinds own their payload
    shapes (§3.1). Returns the normalized stored form. Sync (existence
    checks hit the DB)."""
    if kind == AgentMemory.KIND_WAYPOINT:
        if not isinstance(data, dict) or set(data) != {'room_id'}:
            raise DoorError(
                'bad-params',
                "waypoint 'data' must be exactly {'room_id': <int>}.")
        room_id = _require_int(data.get('room_id'), 'room_id')
        if not Room.objects.filter(pk=room_id).exists():
            raise DoorError('not-found', f'No room with id {room_id}.')
        # The room PK and nothing else — no path snapshot, nothing
        # duplicative that can go stale (operator-ruled).
        return {'room_id': room_id}
    if not isinstance(data, dict) or set(data) != {'lines'}:
        raise DoorError(
            'bad-params',
            "bundle 'data' must be exactly "
            "{'lines': [[slug, mk_tier, rarity, quantity], ...]}.")
    lines = data['lines']
    if not isinstance(lines, list) or not lines:
        raise DoorError('bad-params', "'lines' must be a non-empty list.")
    if len(lines) > MEMORY_MAX_BUNDLE_LINES:
        raise DoorError(
            'too-many-lines',
            f'Bundles hold at most {MEMORY_MAX_BUNDLE_LINES} lines.')
    rarities = {code for code, _ in ItemInstance.RARITY_CHOICES}
    cleaned = []
    for i, line in enumerate(lines):
        if not isinstance(line, list) or len(line) != 4:
            raise DoorError(
                'bad-params',
                f'Line {i}: each bundle line is '
                f'[slug, mk_tier, rarity, quantity].')
        slug, mk_tier, rarity, quantity = line
        if (not isinstance(slug, str)
                or not ItemDefinition.objects.filter(slug=slug).exists()):
            raise DoorError('not-found',
                            f'Line {i}: no item definition with slug '
                            f'{slug!r}.')
        mk_tier = _require_int(mk_tier, f'line {i} mk_tier', minimum=1)
        quantity = _require_int(quantity, f'line {i} quantity', minimum=1)
        if not isinstance(rarity, str):
            raise DoorError('bad-params',
                            f"Line {i}: 'rarity' must be a string.")
        if rarity == ItemInstance.ARTIFACT:
            # The same law a_gift applies — bundles replay gift, and
            # gift refuses artifacts.
            raise DoorError(
                'bad-params',
                f'Line {i}: artifact rarity is refused — bundles replay '
                f'gift, and gift refuses artifacts.')
        if rarity not in rarities:
            raise DoorError('bad-params',
                            f'Line {i}: unknown rarity {rarity!r}.')
        cleaned.append([slug, mk_tier, rarity, quantity])
    return {'lines': cleaned}


@database_sync_to_async
def _remember(agent_name, kind, name, data, taught_by_name):
    agent = _agent_user(agent_name)
    data = _validate_memory_data(kind, data)
    raw = json.dumps(data).encode()
    if len(raw) > MEMORY_MAX_PAYLOAD_BYTES:
        raise DoorError(
            'payload-too-large',
            f'Serialized data is {len(raw)} bytes; the cap is '
            f'{MEMORY_MAX_PAYLOAD_BYTES}.')
    taught_by = None
    if taught_by_name:
        # Audit, not authorization: unresolvable or absent is null.
        teacher = (Character.objects.select_related('user')
                   .filter(name__iexact=taught_by_name).first())
        if teacher is not None:
            taught_by = teacher.user
    with transaction.atomic():
        row = (AgentMemory.objects
               .filter(agent=agent, kind=kind, name__iexact=name).first())
        if row is not None:
            # The upsert law: replace takes the new casing too.
            row.name = name
            row.data = data
            row.taught_by = taught_by
            row.save(update_fields=['name', 'data', 'taught_by',
                                    'updated_at'])
            return row.pk, 'replaced'
        if (AgentMemory.objects.filter(agent=agent).count()
                >= MEMORY_MAX_ROWS_PER_AGENT):
            raise DoorError(
                'memory-full',
                f'The store holds {MEMORY_MAX_ROWS_PER_AGENT} rows '
                f'already — forget something first.')
        row = AgentMemory.objects.create(
            agent=agent, kind=kind, name=name, data=data,
            taught_by=taught_by)
        return row.pk, 'created'


async def a_remember(params, agent_name):
    """#294: teach — upsert by (agent, kind, name) case-insensitive.
    Cap violations are distinct legible errors, never silent
    truncation."""
    kind = _require_str(params, 'kind')
    if kind not in MEMORY_KINDS:
        raise DoorError(
            'bad-params',
            f'Unknown memory kind {kind!r} — declared kinds: '
            f'{", ".join(sorted(MEMORY_KINDS))}.')
    name = _require_str(params, 'name', max_len=MEMORY_MAX_NAME_LEN)
    taught_by = params.get('taught_by')
    if taught_by is not None and not isinstance(taught_by, str):
        raise DoorError('bad-params', "'taught_by' must be a string.")
    pk, result = await _remember(agent_name, kind, name,
                                 params.get('data'), taught_by)
    return {'id': pk, 'result': result}


@database_sync_to_async
def _forget(agent_name, memory_id):
    agent = _agent_user(agent_name)
    row = AgentMemory.objects.filter(agent=agent, pk=memory_id).first()
    if row is None:
        raise DoorError('not-found', f'No memory with id {memory_id}.')
    info = {'id': row.pk, 'kind': row.kind, 'name': row.name}
    row.delete()
    return info


async def a_forget(params, agent_name):
    """#294: by PK only, never by name — read-before-delete, the door's
    mutation discipline."""
    memory_id = _require_int(params.get('id'), 'id')
    return {'forgotten': await _forget(agent_name, memory_id)}


def _memory_summary(row, rooms):
    """The list-row summary, rendered live: waypoint resolves its room
    now (never a stored snapshot); bundle counts its lines."""
    if row.kind == AgentMemory.KIND_WAYPOINT:
        room = rooms.get(row.data.get('room_id'))
        if room is None:
            return '(room no longer exists)'
        if room.area_id:
            return f'{room.zone.name}: {room.area.name}: {room.name}'
        return f'{room.zone.name}: {room.name}'
    return f"{len(row.data.get('lines', []))} lines"


@database_sync_to_async
def _memories_payload(agent_name, kind, contains, since, until):
    agent = _agent_user(agent_name)
    qs = AgentMemory.objects.filter(agent=agent)
    if kind is not None:
        qs = qs.filter(kind=kind)
    if contains:
        qs = qs.filter(name__icontains=contains)
    if since is not None:
        qs = qs.filter(created_at__gte=since)
    if until is not None:
        qs = qs.filter(created_at__lte=until)
    rows = list(qs.order_by('-created_at')[:MEMORY_LIST_CAP])
    room_ids = [r.data.get('room_id') for r in rows
                if r.kind == AgentMemory.KIND_WAYPOINT]
    rooms = (Room.objects.select_related('zone', 'area')
             .in_bulk([rid for rid in room_ids if isinstance(rid, int)]))
    return {
        'memories': [
            {'id': r.pk, 'kind': r.kind, 'name': r.name,
             'summary': _memory_summary(r, rooms)}
            for r in rows
        ],
        'count': len(rows),
    }


async def q_memories(params, agent_name):
    """#294: the store listing — newest-first, capped, summaries
    rendered live (one joined room query for every waypoint row)."""
    kind = params.get('kind')
    if kind is not None and kind not in MEMORY_KINDS:
        raise DoorError('bad-params', f'Unknown memory kind {kind!r}.')
    contains = params.get('name', '')
    if contains is None:
        contains = ''
    if not isinstance(contains, str):
        raise DoorError('bad-params', "'name' must be a string.")
    since = _parse_when(params, 'since')
    until = _parse_when(params, 'until')
    return await _memories_payload(agent_name, kind, contains, since, until)


@database_sync_to_async
def _memory_payload(agent_name, memory_id):
    agent = _agent_user(agent_name)
    row = (AgentMemory.objects.select_related('taught_by')
           .filter(agent=agent, pk=memory_id).first())
    if row is None:
        raise DoorError('not-found', f'No memory with id {memory_id}.')
    data = row.data
    if row.kind == AgentMemory.KIND_BUNDLE:
        # The stored form is positional; the rendered detail is legible.
        data = {'lines': [
            {'slug': l[0], 'mk_tier': l[1], 'rarity': l[2],
             'quantity': l[3]}
            for l in row.data.get('lines', [])
            if isinstance(l, list) and len(l) == 4
        ]}
    return {
        'id': row.pk,
        'kind': row.kind,
        'name': row.name,
        'data': data,
        'taught_by': row.taught_by.username if row.taught_by_id else None,
        'created_at': row.created_at.isoformat(),
        'updated_at': row.updated_at.isoformat(),
    }


async def q_memory(params, agent_name):
    memory_id = _require_int(params.get('id'), 'id')
    return await _memory_payload(agent_name, memory_id)


# ----------------------------------------------------------------------
# Rooms (v25.8 — #290)
# ----------------------------------------------------------------------

@database_sync_to_async
def _rooms_payload(contains, zone_contains):
    qs = (Room.objects.select_related('zone', 'area')
          .filter(name__icontains=contains))
    if zone_contains:
        qs = qs.filter(zone__name__icontains=zone_contains)
    rows = list(qs.order_by('zone__name', 'name')[:LIST_CAP])
    return {'rooms': [_room_dict(r) for r in rows], 'count': len(rows)}


async def q_rooms(params, agent_name):
    """#290: the room directory — case-insensitive substring against
    the room name, optional zone narrowing. Duplicate names across
    zones are simply multiple rows."""
    contains = _require_str(params, 'name')
    zone = params.get('zone')
    if zone is not None and not isinstance(zone, str):
        raise DoorError('bad-params', "'zone' must be a string.")
    return await _rooms_payload(contains, (zone or '').strip())


# ----------------------------------------------------------------------
# Dispatch (§4) — the consumer resolves kinds through these tables.
# ----------------------------------------------------------------------

QUERY_HANDLERS = {
    'commands': q_commands,
    'who_online': q_who_online,
    'where_is': q_where_is,
    'character': q_character,
    'items': q_items,
    'is_admin': q_is_admin,
    'inventory': q_inventory,
    'item': q_item,
    'memories': q_memories,
    'memory': q_memory,
    'rooms': q_rooms,
}

ACTION_HANDLERS = {
    'answer': a_answer,
    'gift': a_gift,
    'create_artifact': a_create_artifact,
    'strip': a_strip,
    'dress': a_dress,
    'move': a_move,
    'remove_item': a_remove_item,
    'edit_item': a_edit_item,
    'equip_item': a_equip_item,
    'unequip_item': a_unequip_item,
    'remember': a_remember,
    'forget': a_forget,
}
