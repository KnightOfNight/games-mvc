# Shyland Architecture

> Authoritative technical reference as of commit b2d0914 (v18 brief 2: the Obelisk Network — `TravelNode`/`TravelMessage` models, `ZoneGate` removed, the `travel` command, the Primordial Sphere, and the network's first node at the Heart of the Convergence).
> Describes what is built. For design intent see the current GDD.
>
> **v18 is implemented across multiple briefs. Subsequent v18 briefs update this file in place; the version stamp does not increment again until v19.**

---

## 1. Overview

Shyland is a free, browser-based Multi-User Dungeon. The primary interface is text: players connect via WebSocket, type commands, and read descriptive output. A minimal visual chrome (status bar, side panel) supplements the text pane. As of this commit, v16 adds the in-game character creator: a player with no `Character` who visits `/shyland/play/` is redirected to a creation form where they choose an Origin, an Archetype, and a Name, then spawn into The Convergence. Supporting changes: `Character.name` is now a real database field (previously a read-only property over the gamer tag), `Origin` and `Archetype` gained attire flavor-text fields and real seeded descriptions, and the `better-profanity` dependency was added for name filtering. v17 adds the Infinity City world seed — a data-only change (no models, no migrations) that replaces the 5-room placeholder starter zone in `seed_world.py` with the full first-version map of The Convergence: 4 park-path areas (Wisteria Walk, Bamboo Run, Basalt Way, Fern Boards), 54 rooms (obelisk hub, four park paths, a 35-room ring street, and Morra's Smithy), and 9 non-combat NPC definitions placed via `RoomSpawn`. v18 (in progress across multiple briefs) begins The Verdant Reach series. Brief 1 ships the Mk 1 item kit: 23 fantasy `ItemDefinition` seed rows (22 net-new plus the legacy Copper Ring absorbed as Copper Ring of Wisdom) covering a leather armor set, a wooden shield, four weapons, and twelve copper accessories; a `suppress_mk_suffix` display field on `ItemDefinition` (migration `0018`); a central `get_display_name_with_tier()` helper in `item_utils.py`; and a rewritten `equip` command implementing a general exchange rule (one-for-one auto-swap, refusals on multi-item or ambiguous displacement). Brief 1 contains no zone content — Verdant Reach rooms, NPCs, and drop tables come in later v18 briefs. Brief 2 ships the Obelisk Network, Shyland's fast-travel system (GDD 2.11): the superseded `ZoneGate` model is removed and replaced by `TravelNode` (one node per room, obelisk or checkpoint type) and `TravelMessage` (three seeded flavor pools), the `travel` command is implemented in the consumer (list + go forms, revelation derived from `RoomVisit`), the Primordial Sphere NPC is placed at the Heart of the Convergence, and the Heart is registered as the network's first node ("The Convergence", obelisk). Brief 2 also contains no Verdant Reach content. See [Section 7](#7-what-is-not-yet-built) for unbuilt systems.

---

## 2. Infrastructure

*(unchanged from v15)*

### 2.1 Docker Compose stack

```
docker-compose.yml defines five containers:

  nginx      nginx:alpine          SSL termination; WebSocket proxy at /ws/
  django     python:3.12-slim      Daphne ASGI server; Django 5 + Channels
  postgres   postgres:16-alpine    Primary database; persistent volume pgdata
  redis      redis:7-alpine        Django Channels layer for WebSocket routing
  ticker     shyland-django image  Tick engine; run_tick_engine management command
```

**Network flow:**

```
Browser
  ↓ HTTPS / WSS  (port HOST_PORT, default 40443)
nginx
  ↓ HTTP proxy_pass http://django:8000
  ↓ Sets X-Forwarded-Proto: https on all requests
  ↓ WebSocket Upgrade headers forwarded for /ws/ paths
Daphne (Django ASGI)
  ├── HTTP requests → Django WSGI stack
  └── WebSocket /ws/* → Django Channels consumers
        ├── reads from / writes to Redis (channel layer)
        └── reads from / writes to PostgreSQL (ORM)
```

Only `nginx` exposes a host port. `django`, `postgres`, `redis`, and `ticker` are internal to the Docker network. `postgres` has a healthcheck; `django` and `ticker` both depend on it being healthy before starting. `ticker` uses the same `shyland-django` image as `django` — no separate build step.

### 2.2 Makefile workflow

| Target | What it does |
|--------|-------------|
| `make setup` | First-time: wizard + build + start |
| `make build` | Rebuild Docker image and recreate containers — **required after any Python/template/settings change** |
| `make start` / `make stop` / `make restart` | Container lifecycle |
| `make logs` | Follow all container logs |
| `make tick-logs` | Follow ticker container logs only |
| `make migrate` | Run `python manage.py migrate` inside the container |
| `make makemigrations [APP=name]` | Generate migrations and auto-sync generated files back to local filesystem |
| `make shell` | Django shell inside the container |
| `make createsuperuser` | Create a Django admin superuser |
| `make new-app NAME=x` | Scaffold a new game app in `apps/` |
| `make reset` | Drop all Docker volumes, rebuild, start, migrate, and run `seed_world` — full data wipe |

> **Critical workflow note:** After editing any file under `django/src/`, run `make build` before testing. `make restart` alone recreates containers from the existing image and picks up no changes.

---

## 3. Django Project Structure

The Django project lives in `django/src/game_mvc/`.

### 3.1 `asgi.py`

Entry point for all traffic. Sets `DJANGO_SETTINGS_MODULE` to `game_mvc.settings.production` by default.

```python
application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

`AuthMiddlewareStack` populates `scope['user']` with the authenticated Django `User` before the consumer receives the connection.

### 3.2 `routing.py` — WebSocket URL registry

```python
path('ws/shyship/<uuid:game_id>/', ShyshipConsumer.as_asgi()),
path('ws/shyland/',               SkylandConsumer.as_asgi()),
```

### 3.3 `urls.py` — HTTP endpoints

| Path | Handler |
|------|---------|
| `/` | `HomeView` (game lobby) |
| `/admin/` | Django admin |
| `/accounts/` | `django.contrib.auth.urls` (login, logout, password) |
| `/api/auth/` | DRF browsable API auth |
| `/shydle` | Shydle app |
| `/shyship/` | Shyship app |
| `/shyland/` | Shyland app |

App-level routes inside the Shyland include are documented in [Section 4.10](#410-http-routes-urlspy).

### 3.4 Settings

| File | Used when | Notable differences |
|------|-----------|---------------------|
| `base.py` | Always imported | PostgreSQL, Redis channel layer, all INSTALLED_APPS |
| `production.py` | Default (container env) | `DEBUG=False`, `SECURE_PROXY_SSL_HEADER` set |
| `local.py` | Set `DJANGO_SETTINGS_MODULE=game_mvc.settings.local` | `DEBUG=True`, `ALLOWED_HOSTS=['*']`, `InMemoryChannelLayer` |

### 3.5 Platform profile system (`apps.profiles`)

`apps.profiles` extends `auth.User` with a `UserProfile` model (`gamer_tag` CharField, max 20, unique, nullable). A `post_save` signal auto-creates a `UserProfile` for each new `User`. As of v16, Shyland no longer derives `Character.name` from the gamer tag at read time — the gamer tag (falling back to `user.username`) is only the *default value* offered in the character creator's Name field. Once a `Character` exists, its `name` field is authoritative and independent of the profile.

---

## 4. The Shyland App (`apps/shyland/`)

### 4.1 Models (`models.py`)

#### Module-level constants

*(unchanged from v15)*

```python
COMBAT_ROUND_TICKS    = 3     # ticks between combat rounds
DYING_DURATION_SECS   = 30    # seconds in dying state before death fires
FLEE_COOLDOWN_TICKS   = 3     # rounds before another flee attempt is allowed
STALE_SESSION_SECS    = 30    # close a CombatSession with no tick activity
XP_PENALTY_MIN_LEVEL  = 10    # level threshold for XP death penalty
DEATH_DURABILITY_LOSS = 10.0  # durability % lost per equipped item on death
CORPSE_DECAY_MINUTES  = 10    # minutes until a corpse is deleted by the tick engine
ACUITY_DRIFT_RATE     = 0.01  # Acuity movement per tick toward baseline
STAT_POINTS_PER_LEVEL = 5     # unspent stat points awarded per level-up
VITALITY_REGEN_SECS   = 120   # seconds to regen full Vitality from zero out of combat
LONGEVITY_REGEN_SECS  = 3600  # seconds to regen full Longevity from zero out of combat
```

#### `UnarmedMessagePool`, `UnarmedMessage`

*(unchanged from v15)*

#### `Origin`

One new field added in v16:

```
name             CharField(100)
slug             SlugField(unique)
description      TextField(blank)
acuity_baseline  FloatField
acuity_band_low  FloatField
acuity_band_high FloatField
attire_material  CharField(200, blank=True, default='')   ← new in v16
```

Ordering: `['name']`. `attire_material` holds the Origin's material/palette phrase for the starting-attire flavor text (see Section 4.11). `description` is now seeded with real content (see Section 4.8).

#### `Archetype`

One new field added in v16:

```
name                 CharField(100)
slug                 SlugField(unique)
description          TextField(blank)
primary_stat_1       CharField(3, choices=STAT_CHOICES)
primary_stat_2       CharField(3, choices=STAT_CHOICES)
attire_silhouette    CharField(200, blank=True, default='')   ← new in v16
unarmed_message_pool ForeignKey(UnarmedMessagePool, SET_NULL, null, blank, related_name='archetypes')
```

Ordering: `['name']`. `STAT_CHOICES` covers all six stats: str, dex, end, int, wis, per. `attire_silhouette` holds the Archetype's garment-silhouette phrase for the starting-attire flavor text (see Section 4.11). `description` is now seeded with real content (see Section 4.8).

#### `Zone`, `Area`, `Room`, `RoomVisit`

*(unchanged from v15)*

#### `Character`

Changed in v16: `name` is now a real, required database field, placed immediately after `user`:

```
user  OneToOneField(User, CASCADE, related_name='shyland_character')
name  CharField(20)                                                    ← new in v16
```

Uniqueness is **case-insensitive and enforced at the database level** via a functional constraint in `Character.Meta`:

```python
constraints = [
    models.UniqueConstraint(
        Lower('name'),
        name='shyland_character_name_ci_unique',
        violation_error_message='That name is already taken.',
    ),
]
```

Django validates this constraint in `full_clean()`, so the admin and any `ModelForm` path get a friendly "That name is already taken." error rather than an `IntegrityError`. `Character.clean()` also strips surrounding whitespace from `name`, so padded names cannot be stored through any `full_clean()`-based write path.

The previous read-only `@property def name` — which returned `user.profile.gamer_tag` falling back to `user.username` — has been **removed entirely**. `Character.name` is set once at creation (defaulting to the gamer tag in the creator form, but freely overridable) and is thereafter independent of the profile. The max length of 20 matches `UserProfile.gamer_tag`'s constraint. The `ObjectDoesNotExist` import that supported the property was also removed.

Migration `0017` adds the field in the standard safe three-step form so it applies cleanly on databases that already contain `Character` rows (this codebase runs as multiple installations): `AddField` nullable → `RunPython` backfill (gamer tag falling back to username, truncated to 20, deduplicated case-insensitively with numeric suffixes) → `AlterField` to non-null + `AddConstraint`. On this deployment the table was empty, so the backfill was a no-op; the populated-table path was exercised by planting rows on the 0016 schema and migrating forward.

#### `ItemDefinition`

One new field added in v18 (brief 1), alongside the existing display-related fields (`mystery_name`, `mystery_description`):

```python
suppress_mk_suffix = models.BooleanField(
    default=False,
    help_text='If True, display names never show the "Mk N" suffix. '
              'Used for tier-material items (copper/silver/gold/platinum) '
              'whose material name already conveys the tier.',
)
```

This is **display-only**: `mk_tier`, scaling, and rarity machinery are untouched — a Copper Ring of Strength still has a real `mk_tier` and scales normally; the player just never sees "Mk N" appended to a tier-material name. Flavor materials (iron, wood, leather) do *not* suppress — an Iron Sword still displays "Iron Sword Mk 1". The suffix suppression is honored by `get_display_name_with_tier()` in `item_utils.py` (see Section 4.6). Migration `0018` adds the field (single `AddField` with a default — safe on populated databases).

#### `TravelNode`, `TravelMessage` (new in v18 brief 2) — and `ZoneGate` removed

**`ZoneGate` no longer exists.** The model (introduced v15, authoring-only, never wired to a command; no gate data was ever seeded) was superseded by the Obelisk Network and deleted in brief 2 — model, admin registration, and all references. Migration `0019_travelmessage_travelnode_delete_zonegate` drops the table and creates the two new models below. Do not hunt for `ZoneGate` in current code; it survives only in migration history (`0016` created it, `0019` deletes it).

**`TravelNode`** — the node registry for the Obelisk Network (GDD 2.11). Fields:

| Field | Type | Notes |
|-------|------|-------|
| `room` | `OneToOneField(Room, related_name='travel_node')` | One node per room, enforced by the one-to-one |
| `travel_name` | `CharField(max_length=60, unique=True)` | Unique, typeable destination name shown in travel lists (e.g. "The Convergence") |
| `node_type` | `CharField(max_length=12, choices=...)` | `'obelisk'` (travel source **and** destination) or `'checkpoint'` (destination only) |

There is no per-character revelation table: a character's available destinations are derived entirely from `RoomVisit` — any node whose room appears in their visit records is revealed, permanently. The network is global (no zone scoping) and travel is free (no cost, no cooldown). Node rooms are safe by seeding convention (GDD 2.11); the travel logic performs no combat checks.

**`TravelMessage`** — global flavor-text pools for travel events. Fields: `category` (`'traveler'` — shown to the traveling player; `'departure'` — shown to players in the origin room; `'arrival'` — shown to players in the destination room) and `text`. Witness messages (departure/arrival) may include the literal placeholder `{name}`, replaced with the traveling character's name via `str.replace` (not `.format`, so stray braces in prose are harmless); traveler messages take no placeholders. One message is selected uniformly at random from the appropriate pool per event — travel text is never hardcoded. Pools are global, not per-zone.

#### All other models

`EffectDefinition`, `EffectComponent`, `ItemInstance`, `EffectInstance`, `EffectComponentInstance`, `LootTable`, `LootTableEntry`, `NpcDefinition`, `NpcEffect`, `NpcInstance`, `Corpse`, `RoomSpawn`, `VendorEntry`, `CombatSession`, `CombatAction` — *(unchanged from v15)*.

### 4.2 Currency system (`currency.py`)

*(unchanged from v15)*

### 4.3 WebSocket consumer (`consumers.py`)

Changed in v18: brief 1 rewrote the `equip` command and centralized name-plus-tier display formatting; brief 2 added the `travel` command. All other command handling *(unchanged from v16)*.

#### The `travel` command (v18 brief 2)

`cmd_travel(args)`, dispatched on the verb `travel`, with two forms. Both forms start with the same source checks against the current room's `TravelNode`:

- **No node in this room** → error: `There is no obelisk here. Travel is a gift of the obelisks — you must stand before one.`
- **Checkpoint node** → error: `The obelisks project their protection here, but only an obelisk itself can send you onward.` Checkpoints are destinations only; only an obelisk-type node can initiate travel.

The character's revealed destinations are computed as all `TravelNode` rows whose room has a `RoomVisit` for this character (helper `get_revealed_destinations`), excluding the node the character is standing at, ordered alphabetically by `travel_name`. No zone filtering — the network is global.

**`travel` (no argument) — list.** Empty set → `The Obelisk is silent. It has nothing to show you yet — the network reveals itself only to those who walk it.` Otherwise a header line `The Obelisk offers passage to:` followed by one plain line per destination — the `travel_name`, with obelisk-type nodes suffixed ` (obelisk)` and checkpoints unsuffixed (screen-reader-friendly, matching existing list output style).

**`travel <destination>` — go.** The argument is matched against the revealed set by case-insensitive prefix match on `travel_name`, additionally ignoring a leading `The ` on the node name (`_travel_name_matches` static helper — `travel verdant` and `travel the verdant crown` both match "The Verdant Crown"). No match → `The Obelisk knows no such place — or you have not yet stood there. Type "travel" to see where it can send you.` Multiple matches → the matching names are listed and the player is asked to be more specific; nothing changes. On a unique match, the travel sequence runs:

1. A random `departure` message (with `{name}` substituted) is broadcast to the origin room, excluding the traveler.
2. The character moves using the same machinery as normal movement: `group_discard` the old room group, the existing `move_character()` helper, `group_add` the new room group (`self.last_direction` is reset to `None` — travel has no direction for flee to reverse).
3. A random `traveler` message is sent to the traveler, followed by the full standard room output (`send_room_description(entering=True)` — identical to normal movement, including `RoomVisit` bookkeeping on arrival; no special-casing).
4. A random `arrival` message (with `{name}` substituted) is broadcast to the destination room, excluding the traveler.

Travel is free: no currency cost, no cooldown, and no combat check (node rooms are safe by design — safety is a seeding concern, not travel logic). The obelisk speaks no words: no NPC dialogue is involved; all travel text comes from the `TravelMessage` pools, selected randomly per event. Supporting DB helpers: `get_travel_node(room)`, `get_revealed_destinations(current_node)`, `get_random_travel_message(category)`.

#### The equip exchange rule (`cmd_equip`)

The old behavior — refuse whenever a target slot is occupied or a two-handed conflict exists — is replaced by a general exchange rule. For each slot in the item's `valid_slots` (in order), `cmd_equip` computes a **displacement set**: every currently equipped item that must come off for the new item to legally occupy that slot.

- The current occupant(s) of the slot, if it is at capacity. Slot capacity comes from the module-level `SLOT_CAPACITY = {'RING': 2}` — RING is the only slot a character has two of; every other slot holds one item. A slot below capacity contributes an empty base set; a slot at capacity contributes one candidate per occupant (displacing that occupant).
- If the new item is two-handed: every equipped item in MAIN_HAND or OFF_HAND, plus every equipped item whose definition is two-handed **regardless of its slot** — a two-handed item claims the character's hands from wherever it sits, including a two-handed bow equipped in RANGED.
- If the new item is one-handed and the candidate slot is MAIN_HAND or OFF_HAND: additionally, any equipped item whose definition is two-handed (its hands-claim conflicts even from RANGED).

Outcome selection, in `valid_slots` order:

1. **Any candidate with an empty displacement set** → equip there. Output: `You equip <item> in your <slot>.`
2. Otherwise, take the minimal displacement sets across candidates:
   - **Minimum size ≥ 2** → refuse, naming every item in the set: `You'd have to unequip your Iron Sword and your Wooden Shield first.` Nothing is unequipped.
   - **Minimum size 1, all minimal sets contain the same item** → **auto-swap**: unequip the displaced item, equip the new one, and send a single exchange message: `You unequip your Broadsword and equip your Wooden Shield in your Off Hand.` (Display names via `get_display_name()`.)
   - **Minimum size 1, but different candidate slots displace different items** (ambiguous — a third ring while both RING slots are full; a MAIN_HAND/OFF_HAND item while both hands hold different items) → refuse, naming the candidates: `Both ring slots are full — unequip your Copper Ring of Strength or your Copper Ring of Wisdom first.` (Non-ring ambiguity uses `You'd have to unequip your X or your Y first.`) Nothing is unequipped.

**Auto-swap defers to the existing unequip constraints.** Before swapping, the displaced item is checked with the same rules `cmd_unequip` applies — cursed items cannot be removed; a bag cannot come off if doing so would violate the carry limit. These checks live in the shared helper `_unequip_blocked_reason()`, used by both `cmd_unequip` and the auto-swap path, so the refusal messages are identical and a partial swap can never occur. The swap itself reuses the existing `unequip_item()`/`equip_item()` helpers, so soulbinding and slot bookkeeping behave exactly as a manual unequip-then-equip would.

A module-level `_join_owned_names(items, conj)` helper formats the `your X and/or your Y` lists in refusal and exchange messages.

#### Display formatting

`consumers.py` no longer formats Mk suffixes inline. Every name-plus-tier display (inventory equipment block, inventory item lines, examine header) goes through `get_display_name_with_tier()` from `item_utils.py` (see Section 4.6). Rarity labels are unchanged and still appear exactly where they did before, prepended by the call sites.

Carried over from v16 unchanged: character-less connections get a structured redirect; `disconnect()` guards against `self.character is None`; profile joins removed.

### 4.4 `effect_utils.py`

*(unchanged from v15)*

### 4.5 Combat utilities (`combat_utils.py`)

*(unchanged from v15)*

`recalculate_bars(character)` gained a second call site in v16: the character creator calls it on the unsaved `Character` to compute starting bars from the level-1 stats before the first save (see Section 4.11).

### 4.6 Item generation and utilities (`item_utils.py`)

One new helper added in v18 (brief 1), directly below `get_display_name()`:

```python
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
```

This is the **single source of truth for name-plus-tier formatting**. No inline `Mk {item.mk_tier}` formatting of player-facing item names remains in `consumers.py`. (Model `__str__` methods and tick-engine log lines are admin/debug representations, not display names, and intentionally do not use it.) Everything else in `item_utils.py` *(unchanged from v15)*.

### 4.7 Admin

| Model | Admin class | Notable changes in v16 |
|-------|-------------|------------------------|
| `Character` | `CharacterAdmin` | `name` added to the first fieldset (`user, name, origin, archetype, current_room, recall_room`) — required now that it is a real, non-nullable field |
| `Origin` | `OriginAdmin` | `attire_material` added to `list_display` |
| `Archetype` | `ArchetypeAdmin` | `attire_silhouette` added to `list_display` |

Neither `OriginAdmin` nor `ArchetypeAdmin` declares `fieldsets`, so the new attire fields appear in their add/change forms automatically. All other admin registrations unchanged from v15, except: one v18 (brief 1) change — `ItemDefinitionAdmin` *does* declare `fieldsets`, so `suppress_mk_suffix` was added to its Identification fieldset (alongside `mystery_name` / `mystery_description`); and v18 (brief 2) changes — `ZoneGateAdmin` was removed with its model, and `TravelNodeAdmin` (list display: `travel_name`, `room`, `node_type` — nodes are builder-authorable data) and `TravelMessageAdmin` (list display: `category`, `text`) were registered.

### 4.8 Seed data (`management/commands/seed_world.py`)

Changed in v18 (brief 2): three new idempotent seed steps, run from `handle()` after `_seed_convergence_npcs`:

- **`_seed_primordial_sphere`** — the tenth Convergence NPC: **the Primordial Sphere** (`the-primordial-sphere`), the white sphere suspended in the Obelisk at the Heart of the Convergence, now examinable. The first of its kind — origin of the pattern every zone-end obelisk sphere will follow. Non-aggressive, unique, never wanders, `combat_tier='normal'`, no loot table, no currency drop. Unlike the other Convergence NPCs (whose placeholder stats use `base_vitality=999`), the brief pins its stats at 1 across the board (`base_vitality` and all six base stats = 1, `scaling_factor=1.0`). Follows the standard NPC convention: `update_or_create` by slug with content in `defaults` and balance in `create_defaults`, placed via a `RoomSpawn` (count 1) in the Heart. The Heart is a safe room, so the Sphere can never be attacked in practice.
- **`_seed_travel_nodes`** — registers the network's first node: `TravelNode(room=<Heart of the Convergence>, travel_name='The Convergence', node_type='obelisk')` via `get_or_create` on the room. The room is looked up by the seed's own room key (coordinate identity `(0,0,0)`), never by display-name matching.
- **`_seed_travel_messages`** — seeds the three global message pools with exactly 22 entries: **10 traveler, 6 departure-witness, 6 arrival-witness**. Idempotent via `get_or_create` on `(category, text)`.

The built-in verification pass was extended accordingly: 10 NPC definitions / 10 RoomSpawns (was 9/9), exactly one Sphere spawn at the Heart, exactly one `TravelNode` (The Convergence obelisk at the Heart), and the 10/6/6 message counts.

Changed in v18 (brief 1): `_seed_items` was expanded with the Mk 1 item kit for The Verdant Reach. Three mechanisms:

- **Legacy absorption.** Before any item is processed, the legacy generic `copper-ring` definition is renamed in place (`.filter(slug='copper-ring').update(...)`) to `copper-ring-of-wisdom` / "Copper Ring of Wisdom". The old dictionary was removed from the seed list, so the generic ring can never be recreated and the rename is safe to re-run on both fresh and existing databases.
- **Gear** (weapons, armor, shield) stays on `get_or_create(slug=...)` — created once, never overwritten, so admin-tuned balance survives re-seeding.
- **The 12 copper accessories** use `update_or_create(slug=...)` uniformly, so the absorbed legacy ring is normalized to its authored shape on existing databases and re-seeding stays idempotent.

**Full post-brief ItemDefinition inventory (33 rows):**

| Group | Definitions |
|-------|-------------|
| Leather armor set (6 new + adopted vest) | Leather Cap (HEAD), Leather Shoulders (SHOULDERS), Leather Gloves (HANDS), Leather Belt (WAIST), Leather Leggings (LEGS), Leather Boots (FEET); the pre-existing Leather Vest (CHEST) is adopted into the set unchanged |
| Shield (new) | Wooden Shield (armor-typed, OFF_HAND, one-handed) |
| Weapons (4 new) | Iron Mace (MAIN_HAND, 1H), Broadsword (MAIN_HAND, 2H), Battle Axe (MAIN_HAND, 2H), Hunting Bow (RANGED, **2H** — all bows are two-handed for now) |
| Copper accessories (11 new + 1 absorbed) | Copper Ring of Strength / Dexterity / Endurance / Intelligence / Wisdom / Perception (RING) and Copper Amulet of the same six stats (NECK). Copper Ring of Wisdom is the absorbed legacy `copper-ring`. All twelve: `suppress_mk_suffix=True`, scaling 2.0/0.8, no durability, primary = suffix stat at base 2.0 / factor 0.8, secondary pool = the two adjacent stats at 0.5/0.2 (str→dex+end, dex→str+per, end→str+wis, int→wis+dex, wis→int+end, per→dex+int) |
| Pre-existing, unchanged | Iron Sword, Combat Knife, Pulse Pistol, Apprentice Staff, Leather Vest, Ballistic Jacket, Satchel, Healing Draught, Focus Tonic, Repair Kit |

Net effect on an existing v17 database: 22 new rows plus the in-place rename (11 → 33). On a fresh database the full seed creates all 33 directly. No proper nouns in any new item name; no new technology weapons (the Pulse Pistol is untouched and receives no new associations). This brief seeds **no zone content** — no rooms, NPCs, or drop tables.

Changed in v17: the world-seed portion of the command was rewritten for the Infinity City map. `handle()` first deletes the placeholder content (the five Fracture Point plaza rooms by name, the `goblin-scout`/`training-dummy`/`fracture-wraith` NPC definitions, and the `the-fracture-point-plaza` area — the old `_seed_npcs` method that created them is gone), then builds The Convergence: the zone, 4 areas, 54 rooms keyed on `(zone, coord_x, coord_y, coord_z)` via `update_or_create`, exits wired in a second pass (every room's six exit FKs are assigned explicitly, absent ones to `NULL`, so re-runs fully normalize), 9 unique non-combat NPC definitions placed via `RoomSpawn`, and character relocation (characters with no `current_room`, or one outside The Convergence, move to Heart of the Convergence at (0,0,0); null `recall_room` is set the same way). The command ends with a built-in verification pass (room/area/NPC/spawn counts, ring-loop and path-connectivity walks, flags) that raises `CommandError` on any failure. The command is idempotent. One deliberate deviation from the v17 content brief: the brief assigned ring room R16 the same coordinates as the Basalt Way's last room; R16 sits at (1,−5,0) instead. NPC stats and drop/respawn numbers follow the balance-data convention below (create-only); NPC name, description, genre tag, and behavior flags are refreshed on every run.

Changed in v16: `_seed_origins` and `_seed_archetypes` now use **`update_or_create`** instead of `get_or_create`, keyed on `slug`. Re-running the seed command therefore applies content changes to already-existing rows instead of silently skipping them (their stdout lines now report `"created"`/`"updated"` accordingly). This mattered for v16 because all seven Origins and seven Archetypes already existed from prior seeding.

**Balance data is create-only.** The `defaults` dict (applied on every run) carries only content fields — `name`, `description`, and the attire phrase — while balance values (`Origin.acuity_baseline`/`acuity_band_low`/`acuity_band_high`, `Archetype.primary_stat_1`/`primary_stat_2`) go in `create_defaults` (Django 5's create-only bucket). Re-running `seed_world` on a live database refreshes descriptions but never reverts admin-tuned balance numbers. (The v18 copper accessories deliberately deviate: they are full `update_or_create` rows per the brief, so re-seeding normalizes them — including the absorbed legacy ring.)

Both methods seed real content:

- **Origins** — each of the seven (`highborn`, `feral`, `streetborn`, `irradiated`, `undying`, `machinekind`, `voidtouched`) has a non-empty `description` (flavor text tying the Origin's genre to its Acuity profile) and a non-empty `attire_material` phrase (e.g. Voidtouched: `'shifting, void-dark cloth that seems to drink the light'`). The `acuity_baseline` / `acuity_band_low` / `acuity_band_high` values are unchanged from v15.
- **Archetypes** — each of the seven (`blade`, `bulwark`, `shade`, `conduit`, `warden`, `gunner`, `machinist`) has a non-empty `description` (role summary referencing its two primary stats) and a non-empty `attire_silhouette` phrase (e.g. Machinist: `'a utility vest lined with tool loops'`). The `primary_stat_1` / `primary_stat_2` values are unchanged from v15.

All other seed methods (`_seed_unarmed_pools`, `_seed_effects`, zone/room/area creation) *(unchanged from v17)*.

### 4.9 Tick Engine (`management/commands/run_tick_engine.py`)

*(unchanged from v15)*

### 4.10 HTTP routes (`urls.py`)

The app-level URL configuration (`apps/shyland/urls.py`, namespace `shyland`) as of v16:

| Path | View | URL name |
|------|------|----------|
| `/shyland/play/` | `GameView` | `shyland:game` |
| `/shyland/create/` | `CharacterCreateView` | `shyland:create_character` |
| `/shyland/create/check-name/` | `CheckNameView` | `shyland:check_name` |
| `/shyland/` | `RedirectView` → `/shyland/play/` (non-permanent) | — |

All views are gated by `ShylandAccessMixin` (login required + `players.shyland` group or superuser).

### 4.11 Character Creation Flow (`views.py`, `forms.py`, `templates/shyland/character_create.html`)

New in v16. One character per account was already enforced at the schema level (`Character.user` is a `OneToOneField`); the creation flow now also enforces it at the view layer.

**Gating (`GameView.get`)** — if the authenticated user has no `Character`, `/shyland/play/` redirects to `shyland:create_character` instead of rendering the game terminal. A player without a character can do nothing in Shyland except use the creator or follow its "Back to front page" link to the site root (`{% url 'home' %}`).

**`CharacterCreateView`** (`GET`/`POST` at `/shyland/create/`) — both handlers first check for an existing `Character` and redirect to `shyland:game` if one exists (visiting the creator with a character never shows the form). The form has exactly three fields: Origin, Archetype, Name. No portrait selection exists, by design.

**Default name** — `_default_character_name(user)` returns `user.profile.gamer_tag or user.username`, matching the fallback order of the removed `Character.name` property, **truncated to 20 characters** so a long username can never pre-fill a value that fails validation.

**`CharacterCreationForm`** (`forms.py`) — `origin`/`archetype` are `ModelChoiceField`s with no empty label; `name` is a max-20 CharField. `clean_name` is the single source of truth for name validation, used by both the AJAX check and the final POST:

1. strip; reject blank
2. reject > 20 characters
3. reject if `Character.objects.filter(name__iexact=name).exists()` (advisory pre-check for the friendly error; the DB constraint is the authoritative gate)
4. **only if the submitted name differs from the user's set gamer tag** (`vetted_name`, passed in by the views): reject if `better_profanity.profanity.contains_profanity(name)`. The exemption covers only the gamer tag — the `username` fallback default has no upstream vetting and is always profanity-checked.

**`CheckNameView`** (`GET /shyland/create/check-name/?name=...`) — real-time availability endpoint. Instantiates `CharacterCreationForm` with only the name populated, runs validation, and returns `{"available": bool, "error": str|null}` from the name field's errors alone. The client-side check is advisory; the POST re-validates authoritatively.

**Creation (`CharacterCreateView.post`)** — on a valid form:

- **Spawn point** — `Room.objects.filter(zone__slug='the-convergence', coord_x=0, coord_y=0, coord_z=0).first()`. The lookup is by zone slug + coordinates, **never by room name** — the coordinate convention is stable across content rebuilds (as of v17 the room seeded there is "Heart of the Convergence"; before the Infinity City seed it was the placeholder "The Fracture Point"). If no room matches, the view fails loudly with a non-field form error ("Spawn point is not configured. Contact an admin.") rather than picking a different room. Both `current_room` and `recall_room` are set to the spawn room.
- **Starting stats** — flat baseline of 8 on all six stats, with the Archetype's `primary_stat_1` and `primary_stat_2` raised to 18. No Origin-based stat modifiers.
- **Acuity** — `acuity_current`, `acuity_baseline`, `acuity_band_low`, `acuity_band_high` are copied from the chosen Origin (overriding the model defaults of 1.0/1.0/0.8/1.2).
- **Bars** — `recalculate_bars(character)` is called on the unsaved instance so `vitality_max/current` and `longevity_max/current` are computed from the level-1 stats above, not left at the model's raw 100/100 defaults.
- **Race safety** — `character.save()` runs inside `transaction.atomic()` with `IntegrityError` handling: concurrent same-name submits (both passing the form's advisory `exists()` check) re-render the form with "That name is already taken.", and a double-submit that trips the `user` OneToOne constraint redirects to the game. No creation path can 500 on a constraint violation.
- On save, the player is redirected to `shyland:game` and drops into the terminal at the spawn room.

**Starting attire** — generated flavor text only: the Archetype's `attire_silhouette` phrase combined with the Origin's `attire_material` phrase (e.g. Warden + Undying → "simple, unadorned vestments" of "black lace and grave-worn cloth"). No `ItemDefinition`/`ItemInstance` is created and no equipment slot is occupied. The phrases live on the two model fields; no code path renders the combined text yet (see Section 7).

**Template** (`character_create.html`) — extends the shared `base.html`, continuing the dark monospace terminal aesthetic of `game.html`. Native `<select>`/`<label>` elements (accessible without custom ARIA work), the chosen Origin's and Archetype's `description` shown beneath each select via a small vanilla-JS show-on-select, and a debounced (~400 ms) `fetch` to `shyland:check_name` that writes availability feedback into an inline `aria-live` status area under the Name field. Responses are sequence-guarded: stale in-flight checks are invalidated both by newer input and by clearing the field. `{% csrf_token %}` is the first element inside the form. All fields remain editable until submit.

**No-character WebSocket handling** — the consumer's character-less connect path sends `{"type": "redirect", "url": "/shyland/create/"}` before closing, and `game.html` navigates on that message type, so the HTTP gate and the WS gate route to the same place (see Section 4.3).

**Dependency** — `better-profanity>=0.7` added to `django/requirements.txt` (image rebuild required).

---

## 5. Data Flow Diagrams

*(unchanged from v15)*

---

## 6. Key Design Decisions

These are settled. Do not revisit without deliberate consideration.

**`EffectDefinition` is a pure container.** All behavior lives in `EffectComponent` children. Allows multi-component effects.

**Mk tier scaling: `magnitude = magnitude_base + (magnitude_scaling × mk_tier)`; `duration = duration_base + (duration_scaling × mk_tier)`.** Deterministic — no random ranges.

**Instantaneous components: `duration_base=0`, `duration_scaling=0`.** No `EffectComponentInstance` row created. Parent `EffectInstance` closed immediately after application.

**Reapplication: same or higher Mk tier resets; lower Mk tier ignored silently.** Prevents downgrading active effects.

**Expiry messages: one per parent if all components expire together; one per component if staggered.** Balances feedback against message spam.

**`make reset` target** (renamed from `db-reset`). Drops all volumes, rebuilds, starts with `--wait`, migrates, reseeds. Used for breaking model changes.

**Single `copper` BigIntegerField for all currency.** All math through `currency.py`.

**`Character.name` is a real field, not derived from `user.profile.gamer_tag` at read time.** ⚠️ This **explicitly reverses** the decision recorded in v14/v15 ("Character name from `user.profile.gamer_tag`. Always `select_related('user__profile')`."). As of v16, the gamer tag is only the default offered in the character creator; once created, `Character.name` is authoritative (max 20 chars) and independent of the profile. The `user__profile` joins that served the old property have been removed, and CLAUDE.md's profile-name rule was amended with the Shyland exception in the same change.

**Name uniqueness is case-insensitive and lives in the database.** `UniqueConstraint(Lower('name'))` on `Character` is the authoritative gate for every write path (creator, admin, shell); the form's `name__iexact` `exists()` check is only an advisory pre-check for friendlier real-time feedback, and the creation view catches `IntegrityError` from the race the pre-check cannot close. Never rely on a form-level uniqueness check alone.

**One character per account.** Enforced at the schema level by `Character.user` being a `OneToOneField` (true since v14); as of v16 the creation flow also enforces it at the view layer — both the creator's GET and POST redirect to the game if a character already exists, rather than relying on the DB constraint to fail loudly.

**Spawn-point lookups use zone slug + coordinates, never room name.** The creator finds the spawn room via `zone__slug='the-convergence', coord_x=0, coord_y=0, coord_z=0`. Room names are content, subject to rebuild; coordinates are convention. Future briefs should reuse this pattern instead of name-based room lookups. If the lookup fails, fail loudly — never silently substitute a different room.

**Tier materials suppress the Mk display suffix (v18).** Items named with a tier material (copper — later silver/gold/platinum) never display "Mk N"; the material name conveys the tier. Display-only via `ItemDefinition.suppress_mk_suffix` and `get_display_name_with_tier()` — `mk_tier`, scaling, and rarity machinery are unchanged. Flavor materials (iron, wood, leather) do not suppress.

**The equip exchange rule (v18).** Equipping counts the equipped items that must come off: zero → equip into a free valid slot; exactly one, unambiguously → auto-swap in a single command with an exchange message (never silent); two or more, or one but ambiguous → refuse, naming the items. A two-handed item claims both hands regardless of which slot it sits in (a two-handed bow in RANGED conflicts with MAIN_HAND/OFF_HAND and with other two-handed items); all bows are two-handed for now. Auto-swap defers to the existing unequip constraints (curses, bag carry limit) — no partial swaps.

**Items soulbound on equip.** Permanently soulbound the moment an item is equipped.

**Item identification is per-character knowledge.** Dropping resets `is_identified=False`.

**Room Groups as the broadcast primitive.** Every player in room X is in channel group `room_{X.id}`.

**Personal player groups for direct notification.** Each connected player joins `player_{character_pk}` on connect.

**Server is the authority; client is a dumb terminal.**

**Redis presence for `who` and room description filtering.** `shyland:online:{character_pk}` keys (90s TTL, 60s heartbeat).

**`@database_sync_to_async` pattern throughout.** Never call ORM methods in async context.

**Acuity as a float damage modifier (0.1–1.9).** 1.0 = neutral.

**Tick-driven combat with queued actions.** `CombatSession` owns session metadata; `CombatAction` owns per-round actions.

**Dying state as a 30-second grace window.** All commands except `use` blocked.

**Flee with cooldown and directional preference.** DEX + d20 vs average NPC PER.

**XP threshold formula: `level² × 100`.** `xp_for_next_level(level)` in `combat_utils.py`.

**Stat points on level-up.** `STAT_POINTS_PER_LEVEL = 5`. Never expire.

**Bar recalculation on stat change.** `vitality_max = (END×10)+(STR×3)+(level×5)`. `longevity_max = (END×8)+(WIS×5)+(level×5)`.

**`make build` required after every code change.** Source is baked into the Docker image at build time.

**`make makemigrations` auto-syncs migration files.** The Makefile copies generated files back from the container.

**Boolean commands always require an explicit value.** `brief on` / `brief off`, not bare `brief`. This rule applies to all future boolean-setting commands.

**`brief_description` is required on all rooms.** Non-null, non-blank. No fallback path.

**`look` always shows the long description.** Bypasses `brief_mode` entirely.

**`Origin` and `Archetype` are full models.** Both were promoted from CharField choices in v13b. `Origin` owns the Acuity baseline and band bounds (copied onto the `Character` at creation). `Archetype` owns primary stats and the unarmed message pool FK.

**Unarmed combat is explicit, not a fallback.** No weapon equipped means no weapon damage component — the formula is unchanged. Flavor messaging comes from the attacker's `UnarmedMessagePool`, falling back to the default pool.

**`UnarmedMessage.template` uses Python `.format(target=name)`.** This is the established pattern for all configurable message templates going forward.

**Passive regen is silent and gate-only.** No combat session + not dying = regen fires. No delay, no Origin exceptions, no player notification. Formula: `ceil((max - current) / ticks_to_full)`. Minimum effective heal of 1 per tick prevents stall. Both bars covered; Longevity recovers 30× slower than Vitality.

**`RoomSpawn` is the source of truth for NPC population.** The tick engine populates rooms from `RoomSpawn` config, not from dead `NpcInstance` state. Dead instances persist until `respawn_at` passes; `clear_expired_dead` deletes them at that point, allowing the fill logic to create replacements. Total instances (live + dead) per spawn slot are capped at `count × 2` to prevent unbounded accumulation.

**`VendorEntry` price is always explicit copper.** No auto-calculation formula. Every row requires a price value.

**The Obelisk Network replaces `ZoneGate` (v18 brief 2).** Fast travel is node-based, not edge-based: `TravelNode` rows mark rooms as obelisks (source + destination) or checkpoints (destination only), and any revealed node is reachable from any obelisk — the network is global, with no zone scoping and no per-gate rows. Revelation is per-character, permanent, and derived entirely from `RoomVisit` (no new per-character table; no sharing between characters). Travel is free — no currency, no resource, no cooldown. The obelisk speaks no words: all travel text comes from the randomly-selected `TravelMessage` pools. Safe rooms are a seeding concern, not travel logic — the command performs no combat checks.

**Per-direction blocked exit messages are optional on `Room`.** Fields `no_exit_{direction}_msg` default to `''`. When non-empty, the custom message overrides the hardcoded default in `_NO_EXIT_DEFAULTS` in `consumers.py`. Direction aliases are resolved to canonical before the field lookup.

**Profanity filtering skips only a kept gamer tag, via `better-profanity`.** A name exactly equal to the user's set gamer tag skips the profanity check (the tag is treated as vetted upstream); everything else — overrides *and* the `username` fallback default, which has no upstream vetting — is checked with the `better-profanity` library, never a hand-rolled wordlist. Uniqueness is always checked, default or not, both in real time (AJAX) and authoritatively at the DB constraint on submit.

---

## 7. What Is Not Yet Built

Future sessions should check this list before assuming a system exists.

- Buy/sell commands (`VendorEntry` model exists; no commands yet)
- Obelisk Network nodes beyond The Convergence (the machinery and `travel` command are fully built in brief 2; only one node is registered, so no destination is reachable yet — Verdant Reach nodes arrive with the zone's world seed)
- Per-combat-tier behavior differences (`combat_tier` field exists; no differentiated AI yet)
- Custom blocked exit messages for the `flee` path (flee uses a different room-exit lookup; `no_exit_*_msg` fields only apply to `cmd_move`)
- Per-archetype unarmed message pools (all archetypes currently fall back to the default pool)
- Per-NPC unarmed message pools (all NPCs currently fall back to the default pool)
- Rendering of starting-attire flavor text (`Origin.attire_material` / `Archetype.attire_silhouette` are seeded; no command or view composes/displays the combined phrase yet)
- Item identification trigger — NPC sage, Warden ability, identification scrolls
- Durability degradation on combat use (model field and death-penalty logic exist; per-hit degradation deferred)
- `durability_restore` consumable effect (placeholder response implemented; full repair system deferred)
- Skill point system — distinct from stat points; abilities/talents unlocked by spending skill points (not yet designed)
- NPC AI — wandering, dialogue, patrol (is_aggressive aggro on room entry is implemented)
- Party system (M2M relationship on `CombatSession` is in place; multi-character combat not yet wired)
- Guild system
- Quest system
- Dungeon instancing
- PvP flagging, entry confirmation, and bounty system
- The Wastelands (`is_scaled=True`) level-scaling logic
- XP death penalty floor logic — level < `XP_PENALTY_MIN_LEVEL` (10) currently has no XP penalty
- Revival mechanic — another player using a revival item on a dying character
- `examine` dialogue integration — NPC examine shows description only; no dialogue tree
- Super user in-game item gifting flow
- Minimap and fog-of-war rendering in client (`RoomVisit` records exist but are not rendered)
- Admin in-game teleport commands
- All chat channels except `say` and `who`: `yell`, `tell`, `party`, `guild`, `zone`, `general`, `emote`
- Zone content beyond The Convergence — The Verdant Reach and all other zones are not yet built (v18 brief 1 ships only the Verdant Reach item kit: definitions exist, but no Verdant Reach rooms, NPCs, or drop tables)
- Monitoring container — tracks health of all containers

---

## 8. Known Issues / Flags for Future Sessions

**Side panel is a stub.** `game.html` shows "Session 1 — world coming soon." in the side panel.

**`create_corpse()` is synchronous.** Always call it from within a `@database_sync_to_async` wrapper.

**No room description sent after entering combat.** When a player moves into a room with aggressive NPCs, the room description is not sent.

**`tests.py` and `tests/` coexist in `apps/shyland/`.** The stale default `tests.py` stub shadows nothing at runtime, but `manage.py test apps.shyland` crashes during unittest discovery because of the module/package name collision. Run the test modules explicitly (`manage.py test apps.shyland.tests.test_currency apps.shyland.tests.test_area`) until the stub is removed. Pre-existing; not introduced by v18.
