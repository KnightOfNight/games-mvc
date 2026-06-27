# Shyland Architecture

> Authoritative technical reference as of commit f4d212e (v14: passive out-of-combat regeneration).
> Describes what is built. For design intent see the current GDD.

---

## 1. Overview

Shyland is a free, browser-based Multi-User Dungeon. The primary interface is text: players connect via WebSocket, type commands, and read descriptive output. A minimal visual chrome (status bar, side panel) supplements the text pane. As of this commit, v14 adds passive out-of-combat Vitality and Longevity regeneration to the tick engine. Regen is silent — no message is sent to the player; the status bar update is the only signal. See [Section 7](#7-what-is-not-yet-built) for unbuilt systems.

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

Ordering: `['name']`. Owns the three Acuity parameters previously held in the `_ACUITY_DEFAULTS` dict. `_ACUITY_DEFAULTS` and `get_acuity_defaults()` have been removed from `models.py`.

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

#### `Zone`, `Area`, `Room`, `RoomVisit`

*(unchanged from v13a)*

`Room.brief_description` is `CharField(500, blank=False)` — non-null, non-blank. Required on all rooms. No fallback path exists.

#### `Character`

`origin` and `archetype` are now ForeignKey fields (PROTECT), not CharFields. Both are non-nullable.

```
origin     ForeignKey(Origin, PROTECT, related_name='characters')
archetype  ForeignKey(Archetype, PROTECT, related_name='characters')
```

All other fields unchanged from v13a. Acuity defaults are now read from `character.origin.acuity_baseline`, `character.origin.acuity_band_low`, `character.origin.acuity_band_high`.

**Flags block:**

```
is_hardcore  BooleanField(default=False)
is_dead      BooleanField(default=False)
is_dying     BooleanField(default=False)
dying_since  DateTimeField(null, blank)
brief_mode   BooleanField(default=False)   — if True, always show brief room description
```

#### `EffectDefinition`, `EffectComponent`, `ItemDefinition`, `ItemInstance`

*(unchanged from v13a)*

#### `EffectInstance`, `EffectComponentInstance`

*(unchanged from v13a)*

#### `LootTable`, `LootTableEntry`

*(unchanged from v13a)*

#### `NpcDefinition`

Added one field:

```
unarmed_message_pool  ForeignKey(UnarmedMessagePool, SET_NULL, null, blank, related_name='npc_definitions')
```

All other `NpcDefinition` fields unchanged.

#### `NpcEffect`, `NpcInstance`, `Corpse`, `CombatSession`, `CombatAction`

*(unchanged from v13a)*

### 4.2 Currency system (`currency.py`)

*(unchanged from v12)*

### 4.3 WebSocket consumer (`consumers.py`)

#### Command dispatch table

| Command | Handler |
|---------|---------|
| direction aliases | `cmd_move(verb)` |
| `look` / `l` | `cmd_look()` |
| `say` | `cmd_say(args)` |
| `who` | `cmd_who()` |
| `inventory` / `inv` | `cmd_inventory()` |
| `pickup` / `p` | `cmd_pickup(args)` |
| `drop` | `cmd_drop(args)` |
| `equip` / `eq` | `cmd_equip(args)` |
| `unequip` / `uneq` | `cmd_unequip(args)` |
| `use` | `cmd_use(args)` |
| `examine` / `ex` | `cmd_examine(args)` |
| `loot` | `cmd_loot(args)` |
| `kill` / `attack` / `k` | `cmd_attack(args)` |
| `flee` | `cmd_flee()` |
| `brief` | `cmd_brief(args)` |
| `spend` | `cmd_spend(args)` |
| `stats` | `cmd_stats()` |
| `help` / `?` | `cmd_help()` |

#### `cmd_brief(args)`

Accepts `on` or `off`; explicit value always required. Sets `Character.brief_mode` via `.update()` (avoids a fetch round-trip) and updates `self.character.brief_mode` in memory. Sends confirmation as category `system`. Bare `brief` (no argument or unrecognised argument) sends `"Usage: brief on | brief off"` as category `error`.

#### `send_room_description(room, entering=False, force_long=False)`

Assembles and sends room output. Description selection logic:

- If `force_long=True` (used by `look`): always use `room.description`; record visit with `RoomVisit.get_or_create`.
- Otherwise: call `_check_and_record_visit(character, room)`, which does `get_or_create` in one DB hit and returns `True` if brief should be shown:
  - Returns `True` if `character.brief_mode` is `True`
  - Returns `True` if the visit already existed (repeat visit)
  - Returns `False` if the visit was just created (first visit)
- Select `room.brief_description` or `room.description` based on the result.

`look` always uses `room.description` (bypasses `should_show_brief` entirely) and still calls `get_or_create` to record the visit.

`RoomVisit` is recorded in `send_room_description`, not in `move_character`. The `move_character` helper only updates the character's `current_room`.

#### `cmd_use(args)`

1. Find item in carried consumables by display name match.
2. Load `item.definition.effect`. If `None`, send `"Nothing happens."` and return.
3. Call `do_apply_effect(effect_def, char, item.mk_tier)` — `@database_sync_to_async` around `apply_effect_definition()`.
4. Consume item (`item.delete()`).
5. Send each returned message to the player as category `'system'`.
6. Send expanded status update (see Section 4.9 for payload shape).

#### Character fetch helpers

All character fetch helpers include `current_room__zone` in their `select_related` chain, ensuring `format_wallet()` can access `character.current_room.zone.slug` without a synchronous query.

`get_character_fresh()` and `get_character()` both include `archetype__unarmed_message_pool` in their `select_related` chain so that unarmed message resolution in combat can access the pool without a synchronous query.

`get_character_fresh()` also includes `current_room__area` so that `cmd_spend`'s status payload can populate `area_name`.

### 4.4 `effect_utils.py`

*(unchanged from v12)*

### 4.5 Combat utilities (`combat_utils.py`)

#### `get_unarmed_message(attacker_pool, target_name) → str`

Selects a random `UnarmedMessage` from `attacker_pool`. Falls back to the `default` pool if `attacker_pool` is `None` or has no messages. If no messages are found at all, returns `"You strike {target_name}."`. Substitutes `{target}` with `target_name` using Python `.format()`. Caller is responsible for prefetching `pool.messages` before calling — this function is synchronous and must be called from within a `@database_sync_to_async` wrapper in async context, or directly in the synchronous tick engine.

#### Unarmed attack message injection

When the tick engine processes a combat round:

- **Player → NPC:** if the player has no non-broken weapon equipped (`ItemInstance.is_equipped=True, definition__item_type='weapon', is_broken=False`), `get_unarmed_message` is called with `character.archetype.unarmed_message_pool` (may be `None`) and the NPC's display name as `target_name`. The returned flavor (with trailing period stripped) replaces the "You hit / You land a critical hit on" prefix. Damage calculation is unchanged.
- **NPC → player:** `get_unarmed_message` is called with `npc.definition.unarmed_message_pool` (may be `None`) and the character's name as `target_name`. The flavor replaces the "The {npc} hits / lands a critical hit" prefix.

All other functions unchanged from v13a.

### 4.6 Item generation and utilities (`item_utils.py`)

*(unchanged from v12)*

### 4.7 Admin

| Model | Admin class | Notes |
|-------|-------------|-------|
| `UnarmedMessagePool` | `UnarmedMessagePoolAdmin` | Inline: `UnarmedMessageInline` (tabular, fields: template, order) |
| `Origin` | `OriginAdmin` | list_display: name, slug, acuity_baseline, acuity_band_low, acuity_band_high |
| `Archetype` | `ArchetypeAdmin` | list_display: name, slug, primary_stat_1, primary_stat_2, unarmed_message_pool; raw_id_fields: unarmed_message_pool |

`CharacterAdmin` updated: `origin` and `archetype` moved to `raw_id_fields` (they are now FKs). `list_filter` on `origin` removed (FK filters require select; archetype retained).

`NpcDefinitionAdmin` updated: `unarmed_message_pool` added to `raw_id_fields`.

All other admin registrations unchanged from v13a.

### 4.8 Seed data (`management/commands/seed_world.py`)

Idempotent. Room creation uses `update_or_create` (not `get_or_create`) to ensure `brief_description` is written on existing records after migration. All five Convergence rooms have non-empty `brief_description` values.

**Seeded `UnarmedMessagePool`:**

| slug | name | messages |
|------|------|---------|
| `default` | Default | 10 (delete-and-recreate on each seed run) |

Default pool messages (templates with `{target}` placeholder): "You punch {target}.", "You kick {target}.", "You shove {target} hard.", "You swing at {target}.", "You lunge at {target}.", "You jab {target}.", "You strike {target}.", "You slam into {target}.", "You drive your shoulder into {target}.", "You throw a wild hit at {target}."

**Seeded `Origin` rows (7):**

| slug | name | acuity_baseline | acuity_band_low | acuity_band_high |
|------|------|-----------------|-----------------|------------------|
| `highborn` | Highborn | 1.0 | 0.85 | 1.15 |
| `feral` | Feral | 0.95 | 0.80 | 1.10 |
| `streetborn` | Streetborn | 1.0 | 0.85 | 1.15 |
| `irradiated` | Irradiated | 0.90 | 0.75 | 1.05 |
| `undying` | Undying | 0.80 | 0.65 | 1.00 |
| `machinekind` | Machinekind | 1.05 | 0.90 | 1.20 |
| `voidtouched` | Voidtouched | 0.70 | 0.40 | 1.30 |

**Seeded `Archetype` rows (7):**

| slug | name | primary_stat_1 | primary_stat_2 | unarmed_message_pool |
|------|------|----------------|----------------|----------------------|
| `blade` | Blade | str | dex | null |
| `bulwark` | Bulwark | str | end | null |
| `shade` | Shade | dex | int | null |
| `conduit` | Conduit | int | wis | null |
| `warden` | Warden | wis | end | null |
| `gunner` | Gunner | dex | per | null |
| `machinist` | Machinist | int | dex | null |

All archetypes fall back to the default pool.

**Seeded `EffectDefinition` entries:**

*(unchanged from v13a)*

### 4.9 Tick Engine (`management/commands/run_tick_engine.py`)

#### Structure

*(unchanged from v12)*

#### `process_combat(tick_number)`

Characters are loaded in `load_participants` with `select_related('user__profile', 'current_room__area', 'archetype__unarmed_message_pool')` and `prefetch_related('archetype__unarmed_message_pool__messages')` so that unarmed message resolution and `_build_status` work without extra queries.

NPCs are loaded with `select_related('definition', 'definition__unarmed_message_pool')` and `prefetch_related('definition__effects__effect_definition', 'definition__unarmed_message_pool__messages')`.

Death handling (`execute_death`) unchanged from v13a.

#### `process_effects(tick_number)`

`get_ticking_component_instances` includes `effect_instance__target__current_room__area` in its `select_related` chain so that `_build_status` works correctly for effect-tick status updates.

Phases 1–3 unchanged from v12.

**Phase 4 — Passive bar regeneration (every tick)**

Queries all `Character` rows where `is_dying=False` and at least one bar is below max. Excludes any character with an active `CombatSession`. For each eligible character:

- `vitality_heal = ceil((vitality_max - vitality_current) / VITALITY_REGEN_SECS)` if below max, else 0
- `longevity_heal = ceil((longevity_max - longevity_current) / LONGEVITY_REGEN_SECS)` if below max, else 0

Applies heals, caps at max, saves only changed fields, then sends a `_build_status()` payload to the character's personal group. No message text is sent — the status update is the only signal. All Origins including Machinekind receive passive regen (nanomachine narrative).

#### `_build_status(character) → dict`

```python
{
    'type': 'status',
    'vitality': character.vitality_current,
    'vitality_max': character.vitality_max,
    'acuity': round(character.acuity_current, 2),
    'acuity_baseline': round(character.acuity_baseline, 2),
    'acuity_band_low': round(character.acuity_band_low, 2),
    'acuity_band_high': round(character.acuity_band_high, 2),
    'longevity': character.longevity_current,
    'longevity_max': character.longevity_max,
    'room_name': character.current_room.name if character.current_room else '',
    'area_name': character.current_room.area.name if character.current_room and character.current_room.area_id else None,
}
```

`area_id` (the integer FK column) is checked before accessing `area.name` — avoids an extra query when area is not pre-fetched.

All status payloads in the consumer (`send_room_description`, `cmd_use`, `cmd_spend`) send the same expanded shape.

---

## 5. Data Flow Diagrams

### Effect application via `cmd_use`

*(unchanged from v12)*

### Component expiry (Phase 3)

*(unchanged from v12)*

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

**`_ACUITY_DEFAULTS` dict and `get_acuity_defaults()` removed.** Acuity defaults are now read from `character.origin.acuity_baseline / .acuity_band_low / .acuity_band_high`.

**Unarmed combat is explicit, not a fallback.** No weapon equipped means no weapon damage component — the formula is unchanged. Flavor messaging comes from the attacker's `UnarmedMessagePool`, falling back to the default pool.

**`UnarmedMessage.template` uses Python `.format(target=name)`.** This is the established pattern for all configurable message templates going forward.

**Passive regen is silent and gate-only.** No combat session + not dying = regen fires. No delay, no Origin exceptions, no player notification. Formula: `ceil((max - current) / ticks_to_full)`. Minimum effective heal of 1 per tick prevents stall. Both bars covered; Longevity recovers 30× slower than Vitality.

---

## 7. What Is Not Yet Built

Future sessions should check this list before assuming a system exists.

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
