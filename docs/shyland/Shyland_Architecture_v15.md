# Shyland Architecture

> Authoritative technical reference as of commit TBD (v15: world-building schema).
> Describes what is built. For design intent see the current GDD.

---

## 1. Overview

Shyland is a free, browser-based Multi-User Dungeon. The primary interface is text: players connect via WebSocket, type commands, and read descriptive output. A minimal visual chrome (status bar, side panel) supplements the text pane. As of this commit, v15 adds five world-building schema changes: `NpcDefinition.combat_tier`, `RoomSpawn`, `VendorEntry`, `ZoneGate`, and per-direction blocked exit messages on `Room`. The tick engine's `process_npc_respawn()` now uses `RoomSpawn` as its source of truth for NPC population. No new player-facing commands are added. See [Section 7](#7-what-is-not-yet-built) for unbuilt systems.

---

## 2. Infrastructure

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
| `make db-reset` | Drop all Docker volumes, rebuild, start, migrate, and run `seed_world` — full data wipe |

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

### 3.4 Settings

| File | Used when | Notable differences |
|------|-----------|---------------------|
| `base.py` | Always imported | PostgreSQL, Redis channel layer, all INSTALLED_APPS |
| `production.py` | Default (container env) | `DEBUG=False`, `SECURE_PROXY_SSL_HEADER` set |
| `local.py` | Set `DJANGO_SETTINGS_MODULE=game_mvc.settings.local` | `DEBUG=True`, `ALLOWED_HOSTS=['*']`, `InMemoryChannelLayer` |

### 3.5 Platform profile system (`apps.profiles`)

`apps.profiles` extends `auth.User` with a `UserProfile` model (`gamer_tag` CharField, max 20, unique, nullable). A `post_save` signal auto-creates a `UserProfile` for each new `User`. Shyland uses this for `Character.name`. Always `select_related('user__profile')`.

---

## 4. The Shyland App (`apps/shyland/`)

### 4.1 Models (`models.py`)

#### Module-level constants

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

#### `UnarmedMessagePool`

```
name   CharField(100)
slug   SlugField(unique)
```

Ordering: `['name']`.

#### `UnarmedMessage`

```
pool      ForeignKey(UnarmedMessagePool, CASCADE, related_name='messages')
template  TextField  — Python format string; use {target} for target name
order     IntegerField(default=0)
```

Ordering: `['order']`. Runtime selection is always random from the pool; `order` is for admin display only. `template` is rendered at runtime via `chosen.template.format(target=target_name)`.

#### `Origin`

```
name             CharField(100)
slug             SlugField(unique)
description      TextField(blank)
acuity_baseline  FloatField
acuity_band_low  FloatField
acuity_band_high FloatField
```

Ordering: `['name']`. Owns the three Acuity parameters previously held in the `_ACUITY_DEFAULTS` dict.

#### `Archetype`

```
name                 CharField(100)
slug                 SlugField(unique)
description          TextField(blank)
primary_stat_1       CharField(3, choices=STAT_CHOICES)
primary_stat_2       CharField(3, choices=STAT_CHOICES)
unarmed_message_pool ForeignKey(UnarmedMessagePool, SET_NULL, null, blank, related_name='archetypes')
```

Ordering: `['name']`. `STAT_CHOICES` covers all six stats: str, dex, end, int, wis, per.

#### `Zone`, `Area`

*(unchanged from v14)*

#### `Room`

*(unchanged from v14 except the six new blocked-exit message fields)*

`Room.brief_description` is `CharField(500, blank=False)` — non-null, non-blank. Required on all rooms.

Six new optional `CharField(255, blank=True, default='')` fields placed after the exit FK fields and before the flags block:

```
no_exit_north_msg  CharField(255, blank=True, default='')
no_exit_south_msg  CharField(255, blank=True, default='')
no_exit_east_msg   CharField(255, blank=True, default='')
no_exit_west_msg   CharField(255, blank=True, default='')
no_exit_up_msg     CharField(255, blank=True, default='')
no_exit_down_msg   CharField(255, blank=True, default='')
```

All six are optional. No field is required. When non-empty, the value overrides the hardcoded default in `_NO_EXIT_DEFAULTS` in `consumers.py`. See Section 4.3.

#### `RoomVisit`

*(unchanged from v14)*

#### `Character`

*(unchanged from v14)*

#### `EffectDefinition`, `EffectComponent`, `ItemDefinition`, `ItemInstance`

*(unchanged from v14)*

#### `EffectInstance`, `EffectComponentInstance`

*(unchanged from v14)*

#### `LootTable`, `LootTableEntry`

*(unchanged from v14)*

#### `NpcDefinition`

One new field added:

```
combat_tier  CharField(20, choices=COMBAT_TIER_CHOICES, default='normal')
```

`COMBAT_TIER_CHOICES` is defined as a class attribute on `NpcDefinition`:

| value | display |
|-------|---------|
| `normal` | Normal |
| `elite` | Elite |
| `champion` | Champion |
| `boss` | Boss |
| `world_boss` | World Boss |

All existing NPCs default to `normal`. The field exists for display and future AI/balance logic; no differentiated behavior is implemented in v15.

All other `NpcDefinition` fields unchanged from v14.

#### `NpcEffect`, `NpcInstance`, `Corpse`

*(unchanged from v14)*

#### `RoomSpawn`

New model. Configuration record declaring that a room should contain a certain number of live instances of a given NPC definition at a given Mk tier. The tick engine uses this as the source of truth for NPC population.

```
room            ForeignKey(Room, CASCADE, related_name='spawns')
npc_definition  ForeignKey(NpcDefinition, CASCADE, related_name='room_spawns')
mk_tier         IntegerField(default=1)
count           IntegerField(default=1)   — desired live instance count
is_active       BooleanField(default=True)
```

`unique_together = ('room', 'npc_definition', 'mk_tier')`. Ordering: `['room', 'npc_definition', 'mk_tier']`.

Cap rule: total instances (live + dead) per spawn slot may not exceed `count × 2`. This prevents unbounded dead-instance accumulation while still allowing respawn timers to run their course.

Inactive (`is_active=False`) spawns are ignored by the tick engine entirely.

#### `VendorEntry`

New model. Declares that an NPC sells a particular item at a particular Mk tier for a specific copper price. An `NpcDefinition` with one or more `VendorEntry` rows is a vendor — no flag is needed on `NpcDefinition` itself. Buy/sell commands are not yet implemented.

```
npc_definition  ForeignKey(NpcDefinition, CASCADE, related_name='vendor_entries')
item_definition ForeignKey(ItemDefinition, CASCADE, related_name='vendor_entries')
mk_tier         IntegerField(default=1)
price           BigIntegerField          — price in copper; always required
stock_limit     IntegerField(null, blank) — null = unlimited stock
is_active       BooleanField(default=True)
```

`unique_together = ('npc_definition', 'item_definition', 'mk_tier')`. Ordering: `['npc_definition', 'item_definition', 'mk_tier']`.

#### `ZoneGate`

New model. Fast-travel configuration linking two rooms. No travel command is implemented in v15; this model exists for authoring gate configurations before the command is built.

```
name              CharField(100)
source_room       ForeignKey(Room, CASCADE, related_name='gates_from')
destination_room  ForeignKey(Room, CASCADE, related_name='gates_to')
description       TextField(blank)
is_bidirectional  BooleanField(default=True)
requires_discovery BooleanField(default=True)
is_active         BooleanField(default=True)
```

Ordering: `['name']`.

When `is_bidirectional=True`, a single row represents travel in both directions; the travel command will check both `source_room` and `destination_room`.

When `requires_discovery=True`, a character must have a `RoomVisit` record for the gate's source room before they can use the gate from elsewhere. No additional fields are needed — `RoomVisit` already tracks this.

#### `CombatSession`, `CombatAction`

*(unchanged from v14)*

### 4.2 Currency system (`currency.py`)

*(unchanged from v14)*

### 4.3 WebSocket consumer (`consumers.py`)

#### Module-level constants

In addition to `DIRECTIONS`, `DIRECTION_CANONICAL`, and `REVERSE_DIRECTIONS`, a new constant is defined:

```python
_NO_EXIT_DEFAULTS = {
    'north': "There is no exit in that direction.",
    'south': "There is no exit in that direction.",
    'east':  "There is no exit in that direction.",
    'west':  "There is no exit in that direction.",
    'up':    "There is nothing above you.",
    'down':  "You'd have to dig to go that way.",
}
```

#### Command dispatch table

*(unchanged from v14)*

#### `cmd_move(direction)` — no-exit block

When `destination is None`, the updated block resolves the raw direction verb (which may be an alias) to its canonical form via `DIRECTION_CANONICAL[direction]`, checks `room.no_exit_{canonical}_msg`, and falls back to `_NO_EXIT_DEFAULTS[canonical]` if the field is empty.

```python
if destination is None:
    exits = room.exits()
    canonical = DIRECTION_CANONICAL[direction]
    custom_msg = getattr(room, f'no_exit_{canonical}_msg', '')
    msg = custom_msg if custom_msg else _NO_EXIT_DEFAULTS[canonical]
    await self.send_json({
        'type': 'output',
        'category': 'error',
        'text': msg,
        'hint_exits': ', '.join(exits.keys()) if exits else 'none',
    })
    return
```

The `hint_exits` key on the payload is preserved. Alias resolution via `DIRECTION_CANONICAL` is required because `cmd_move` receives the raw verb from the dispatch table (`'n'`, `'s'`, etc.) and the `no_exit_*_msg` fields are named after canonical directions.

All other `cmd_move` behavior unchanged.

#### All other commands

*(unchanged from v14)*

### 4.4 `effect_utils.py`

*(unchanged from v14)*

### 4.5 Combat utilities (`combat_utils.py`)

*(unchanged from v14)*

### 4.6 Item generation and utilities (`item_utils.py`)

*(unchanged from v14)*

### 4.7 Admin

| Model | Admin class | Notable changes in v15 |
|-------|-------------|------------------------|
| `Room` | `RoomAdmin` | Added explicit `fieldsets`; collapsible "Blocked Exit Messages" fieldset containing the six `no_exit_*_msg` fields |
| `NpcDefinition` | `NpcDefinitionAdmin` | `combat_tier` added to `list_display` |
| `RoomSpawn` | `RoomSpawnAdmin` | New registration |
| `VendorEntry` | `VendorEntryAdmin` | New registration |
| `ZoneGate` | `ZoneGateAdmin` | New registration |

All other admin registrations unchanged from v14.

#### `RoomAdmin` fieldsets

```
(None)                  — zone, area, name, description, brief_description
Coordinates             — coord_x, coord_y, coord_z
Exits                   — exit_north, exit_south, exit_east, exit_west, exit_up, exit_down
Blocked Exit Messages   — (collapse) no_exit_north_msg, no_exit_south_msg, no_exit_east_msg,
                          no_exit_west_msg, no_exit_up_msg, no_exit_down_msg
Flags                   — flag_safe, flag_pvp, flag_dark, flag_indoors, flag_water,
                          flag_no_recall, flag_radiation, flag_holy, flag_magic_dead, flag_scaled
```

#### `RoomSpawnAdmin`

```python
list_display        = ('npc_definition', 'mk_tier', 'count', 'room', 'is_active')
list_filter         = ('is_active', 'npc_definition')
raw_id_fields       = ('room', 'npc_definition')
list_select_related = ('room', 'npc_definition')
```

#### `VendorEntryAdmin`

```python
list_display        = ('npc_definition', 'item_definition', 'mk_tier', 'price', 'stock_limit', 'is_active')
list_filter         = ('is_active', 'npc_definition')
raw_id_fields       = ('npc_definition', 'item_definition')
list_select_related = ('npc_definition', 'item_definition')
```

#### `ZoneGateAdmin`

```python
list_display        = ('name', 'source_room', 'destination_room', 'is_bidirectional', 'requires_discovery', 'is_active')
list_filter         = ('is_active', 'is_bidirectional', 'requires_discovery')
raw_id_fields       = ('source_room', 'destination_room')
list_select_related = ('source_room', 'destination_room')
```

### 4.8 Seed data (`management/commands/seed_world.py`)

*(unchanged from v14 except the three new `RoomSpawn` rows)*

Three `RoomSpawn` rows are seeded at the end of `_seed_npcs()`:

| room | npc_definition | mk_tier | count |
|------|---------------|---------|-------|
| The Fracture Point | a goblin scout | 1 | 1 |
| The Fracture Point | Training Dummy | 1 | 1 |
| The Eastern Bazaar | Fracture Wraith | 1 | 1 |

All three use `get_or_create` (idempotent). The existing `NpcInstance` creations remain as the initial live population; `RoomSpawn` rows allow the tick engine to maintain that population going forward.

### 4.9 Tick Engine (`management/commands/run_tick_engine.py`)

#### Structure

*(unchanged from v14)*

#### `process_combat(tick_number)`

*(unchanged from v14)*

#### `process_effects(tick_number)`

*(unchanged from v14)*

#### `process_npc_respawn()`

Replaced in v15. Now driven by `RoomSpawn` configuration rather than dead `NpcInstance` state.

**Algorithm per tick:**

1. Load all active `RoomSpawn` rows (`is_active=True`) via `get_active_spawns()`.
2. For each spawn:
   a. Call `clear_expired_dead(spawn, now)` — deletes dead `NpcInstance` rows for this definition/room/mk_tier where `respawn_at__lte=now`.
   b. Call `count_instances(spawn)` — returns `(live_count, dead_count)`.
   c. Compute `to_create = min(spawn.count - live_count, (spawn.count * 2) - (live_count + dead_count))`.
   d. If `to_create <= 0`, skip.
   e. For each instance to create: call `create_live_instance(spawn)` and log.

**Helper methods** (all decorated with `@database_sync_to_async`):

`get_active_spawns()` — returns `list(RoomSpawn.objects.filter(is_active=True).select_related('npc_definition', 'room'))`.

`clear_expired_dead(spawn, now)` — `NpcInstance.objects.filter(definition=spawn.npc_definition, spawn_room=spawn.room, mk_tier=spawn.mk_tier, is_alive=False, respawn_at__lte=now).delete()`.

`count_instances(spawn)` — queries `NpcInstance.objects.filter(definition=spawn.npc_definition, spawn_room=spawn.room, mk_tier=spawn.mk_tier)`; returns `(live_count, dead_count)` as a tuple.

`create_live_instance(spawn)` — `NpcInstance.objects.create(definition=spawn.npc_definition, current_room=spawn.room, spawn_room=spawn.room, mk_tier=spawn.mk_tier, vitality_current=spawn.npc_definition.base_vitality, vitality_max=spawn.npc_definition.base_vitality, is_alive=True)`. Does not set `respawn_at`.

**Removed helpers:** `get_due_respawns` and `respawn_npc` have been removed entirely.

#### `_build_status(character) → dict`

*(unchanged from v14)*

---

## 5. Data Flow Diagrams

### Effect application via `cmd_use`

*(unchanged from v14)*

### Component expiry (Phase 3)

*(unchanged from v14)*

---

## 6. Key Design Decisions

These are settled. Do not revisit without deliberate consideration.

**`EffectDefinition` is a pure container.** All behavior lives in `EffectComponent` children. Allows multi-component effects.

**Mk tier scaling: `magnitude = magnitude_base + (magnitude_scaling × mk_tier)`; `duration = duration_base + (duration_scaling × mk_tier)`.** Deterministic — no random ranges.

**Instantaneous components: `duration_base=0`, `duration_scaling=0`.** No `EffectComponentInstance` row created. Parent `EffectInstance` closed immediately after application.

**Reapplication: same or higher Mk tier resets; lower Mk tier ignored silently.** Prevents downgrading active effects.

**Expiry messages: one per parent if all components expire together; one per component if staggered.** Balances feedback against message spam.

**`make db-reset` target.** Drops all volumes, rebuilds, starts, waits 5 seconds, migrates, reseeds. Used for breaking model changes.

**Single `copper` BigIntegerField for all currency.** All math through `currency.py`.

**Character name from `user.profile.gamer_tag`.** Always `select_related('user__profile')`.

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

**`Origin` and `Archetype` are full models.** Both were promoted from CharField choices in v13b. `Origin` owns the Acuity baseline and band bounds. `Archetype` owns primary stats and the unarmed message pool FK.

**Unarmed combat is explicit, not a fallback.** No weapon equipped means no weapon damage component — the formula is unchanged. Flavor messaging comes from the attacker's `UnarmedMessagePool`, falling back to the default pool.

**`UnarmedMessage.template` uses Python `.format(target=name)`.** This is the established pattern for all configurable message templates going forward.

**Passive regen is silent and gate-only.** No combat session + not dying = regen fires. No delay, no Origin exceptions, no player notification. Formula: `ceil((max - current) / ticks_to_full)`. Minimum effective heal of 1 per tick prevents stall. Both bars covered; Longevity recovers 30× slower than Vitality.

**`RoomSpawn` is the source of truth for NPC population.** The tick engine populates rooms from `RoomSpawn` config, not from dead `NpcInstance` state. Dead instances persist until `respawn_at` passes; `clear_expired_dead` deletes them at that point, allowing the fill logic to create replacements. Total instances (live + dead) per spawn slot are capped at `count × 2` to prevent unbounded accumulation.

**`VendorEntry` price is always explicit copper.** No auto-calculation formula. Every row requires a price value.

**`ZoneGate.is_bidirectional` controls travel direction.** When True, a single row covers travel in both directions; the travel command (not yet implemented) checks both `source_room` and `destination_room`. Discovery gating uses the existing `RoomVisit` model — no additional fields needed.

**Per-direction blocked exit messages are optional on `Room`.** Fields `no_exit_{direction}_msg` default to `''`. When non-empty, the custom message overrides the hardcoded default in `_NO_EXIT_DEFAULTS` in `consumers.py`. Direction aliases are resolved to canonical before the field lookup.

---

## 7. What Is Not Yet Built

Future sessions should check this list before assuming a system exists.

- Buy/sell commands (`VendorEntry` model exists; no commands yet)
- Zone gate travel command (`ZoneGate` model exists; no command yet)
- Per-combat-tier behavior differences (`combat_tier` field exists; no differentiated AI yet)
- Custom blocked exit messages for the `flee` path (flee uses a different room-exit lookup; `no_exit_*_msg` fields only apply to `cmd_move`)
- Per-archetype unarmed message pools (all archetypes currently fall back to the default pool)
- Per-NPC unarmed message pools (all NPCs currently fall back to the default pool)
- Origin and Archetype description fields are seeded blank (content deferred to character creation version)
- In-game character creation flow (admin creation works)
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
- Zone content beyond The Convergence (5 starter rooms)
- Monitoring container — tracks health of all containers

---

## 8. Known Issues / Flags for Future Sessions

**Side panel is a stub.** `game.html` shows "Session 1 — world coming soon." in the side panel.

**`create_corpse()` is synchronous.** Always call it from within a `@database_sync_to_async` wrapper.

**No room description sent after entering combat.** When a player moves into a room with aggressive NPCs, the room description is not sent.
