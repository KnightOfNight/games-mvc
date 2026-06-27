# Shyland Architecture

> Authoritative technical reference as of commit 1f7496d (v13a: status bar maximums, combat room_name, brief toggle).
> Describes what is built. For design intent see the current GDD.

---

## 1. Overview

Shyland is a free, browser-based Multi-User Dungeon. The primary interface is text: players connect via WebSocket, type commands, and read descriptive output. A minimal visual chrome (status bar, side panel) supplements the text pane. As of this commit, v13a delivers three bug fixes and one new feature: status payloads now include bar maximums (`vitality_max`, `longevity_max`, Acuity band bounds); combat status updates populate `room_name` from the character's current room; `format_wallet()` is defended with a correct `select_related` chain; and a `brief` command lets players toggle between always-short and first-visit-long room descriptions. See [Section 7](#7-what-is-not-yet-built) for unbuilt systems.

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
```

#### `Zone`, `Area`, `Room`, `RoomVisit`

*(unchanged from v12)*

`Room.brief_description` is `CharField(500, blank=False)` — non-null, non-blank. Required on all rooms. No fallback path exists.

#### `Character`

Core stats, bars, currency, and flags fields. All from v12 plus one new flag:

**Flags block:**

```
is_hardcore  BooleanField(default=False)
is_dead      BooleanField(default=False)
is_dying     BooleanField(default=False)
dying_since  DateTimeField(null, blank)
brief_mode   BooleanField(default=False)   — if True, always show brief room description
```

#### `EffectDefinition`, `EffectComponent`, `ItemDefinition`, `ItemInstance`

*(unchanged from v12)*

#### `EffectInstance`, `EffectComponentInstance`

*(unchanged from v12)*

#### `LootTable`, `LootTableEntry`, `NpcDefinition`, `NpcEffect`, `NpcInstance`, `Corpse`, `CombatSession`, `CombatAction`

*(unchanged from v12)*

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

`get_character_fresh()` also includes `current_room__area` so that `cmd_spend`'s status payload can populate `area_name`.

### 4.4 `effect_utils.py`

*(unchanged from v12)*

### 4.5 Combat utilities (`combat_utils.py`)

*(unchanged from v12)*

### 4.6 Item generation and utilities (`item_utils.py`)

*(unchanged from v12)*

### 4.7 Admin

*(unchanged from v12)*

### 4.8 Seed data (`management/commands/seed_world.py`)

Idempotent. Room creation uses `update_or_create` (not `get_or_create`) to ensure `brief_description` is written on existing records after migration. All five Convergence rooms have non-empty `brief_description` values.

**Seeded `EffectDefinition` entries:**

*(unchanged from v12)*

### 4.9 Tick Engine (`management/commands/run_tick_engine.py`)

#### Structure

*(unchanged from v12)*

#### `process_combat(tick_number)`

Characters are loaded in `load_participants` with `select_related('user__profile', 'current_room__area')` so that `_build_status` can populate `room_name` and `area_name` without extra queries.

Death handling (`execute_death`) unchanged from v12.

#### `process_effects(tick_number)`

`get_ticking_component_instances` includes `effect_instance__target__current_room__area` in its `select_related` chain so that `_build_status` works correctly for effect-tick status updates.

All other phases unchanged from v12.

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

---

## 7. What Is Not Yet Built

Future sessions should check this list before assuming a system exists.

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
