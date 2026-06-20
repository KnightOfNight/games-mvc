# Shyland Architecture

> Authoritative technical reference as of commit 0ba36ef (v12: effect system redesign).
> Describes what is built. For design intent see the current GDD.

---

## 1. Overview

Shyland is a free, browser-based Multi-User Dungeon. The primary interface is text: players connect via WebSocket, type commands, and read descriptive output. A minimal visual chrome (status bar, side panel) supplements the text pane. As of this commit, v12 redesigns the effect system: `EffectDefinition` becomes a pure container/label; all behavior lives in child `EffectComponent` rows. A new `effect_utils.py` module centralizes all effect application logic. `EffectInstance` is now also a container with child `EffectComponentInstance` rows that store per-component magnitude, expiry time, and lifecycle state. Mk tier scaling is linear: `magnitude = magnitude_base + (magnitude_scaling × mk_tier)`. Reapplication at the same or higher Mk tier resets the effect; lower Mk tier is silently ignored. A new `make db-reset` target drops all volumes, rebuilds, migrates, and reseeds. v11 introduced effects ticking, level-up, and stat spending. The full combat game loop (kill/flee, tick-driven rounds, dying state, NPC aggro) was completed in combat v1. See [Section 7](#7-what-is-not-yet-built) for unbuilt systems.

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

#### `Zone`, `Area`, `Room`, `Character`, `RoomVisit`

*(unchanged from v11 — see v11 doc for full field listings)*

#### `EffectDefinition`

Pure container/label. All behavior lives in `EffectComponent` children.

```
name        CharField(200)
slug        SlugField(unique)
description TextField(blank)
```

#### `EffectComponent`

Defines one behavioral unit within an `EffectDefinition`.

```
definition        FK → EffectDefinition (CASCADE), related_name='components'
component_type    CharField(30), choices:
                    restore_vitality | restore_acuity | restore_longevity |
                    dot_vitality | dot_acuity | dot_longevity |
                    hot_vitality | hot_acuity | hot_longevity |
                    shift_acuity_high | shift_acuity_low |
                    stat_bonus | stat_penalty |
                    curse_generic | durability_restore
target_stat       CharField(10, blank), choices: str|dex|end|int|wis|per
                  — only meaningful for stat_bonus and stat_penalty
magnitude_base    FloatField
magnitude_scaling FloatField(default=0.0)
duration_base     FloatField(default=0.0)   — seconds; 0 = instantaneous
duration_scaling  FloatField(default=0.0)
order             IntegerField(default=0)
```

`Meta: ordering = ['order']`

**Methods:**
- `is_instantaneous()` → `duration_base == 0.0 and duration_scaling == 0.0`
- `computed_magnitude(mk_tier)` → `magnitude_base + (magnitude_scaling × mk_tier)`
- `computed_duration(mk_tier)` → `duration_base + (duration_scaling × mk_tier)`

#### `ItemDefinition`, `ItemInstance`

*(unchanged from v11)*

#### `EffectInstance`

Container linking an `EffectDefinition` application to a target `Character`.

```
definition FK → EffectDefinition (CASCADE), related_name='instances'
target     FK → Character (CASCADE), related_name='active_effects'
mk_tier    IntegerField(default=1)   — source Mk tier at application time
is_active  BooleanField(default=True)
applied_at DateTimeField(auto_now_add=True)
removed_by CharField(50, blank)
```

**`removed_by` vocabulary:** `"timeout"` | `"warden"` | `"consumable"` | `"npc_service"` | `"repair"` | `"death"` | `"reapplication"`

An `EffectInstance` with only instantaneous components is immediately closed (`is_active=False, removed_by='timeout'`) after application.

#### `EffectComponentInstance`

Per-component runtime state stored at application time.

```
effect_instance FK → EffectInstance (CASCADE), related_name='component_instances'
component       FK → EffectComponent (CASCADE)
magnitude       FloatField   — computed at application time; tick engine reads this
expires_at      DateTimeField(null)   — null if instantaneous; no row created for instantaneous components
is_active       BooleanField(default=True)
removed_by      CharField(50, blank)
```

#### `LootTable`, `LootTableEntry`, `NpcDefinition`, `NpcEffect`, `NpcInstance`, `Corpse`, `CombatSession`, `CombatAction`

*(unchanged from v11)*

### 4.2 Currency system (`currency.py`)

*(unchanged from v11)*

### 4.3 WebSocket consumer (`consumers.py`)

#### `cmd_use(args)`

1. Find item in carried consumables by display name match.
2. Load `item.definition.effect`. If `None`, send `"Nothing happens."` and return.
3. Call `do_apply_effect(effect_def, char, item.mk_tier)` — `@database_sync_to_async` around `apply_effect_definition()`.
4. Consume item (`item.delete()`).
5. Send each returned message to the player as category `'system'`.
6. Send status update.

All other commands unchanged from v11.

### 4.4 `effect_utils.py`

New module centralizing all effect application logic. Synchronous — all functions must be called from within `@database_sync_to_async`.

#### `apply_effect_definition(definition, target, mk_tier, removed_by_label='consumable') → list[str]`

Single entry point for applying any effect to any character.

1. **Reapplication check:** If active `EffectInstance` exists for this definition+target:
   - `mk_tier >= existing.mk_tier`: undo stat deltas, deactivate old CIs (`removed_by='reapplication'`), deactivate parent, proceed.
   - `mk_tier < existing.mk_tier`: return `[]`.
2. Create `EffectInstance` container.
3. For each `EffectComponent` (ordered by `order`):
   - If instantaneous: call `_apply_instant_component()`, no `EffectComponentInstance` row.
   - Else: create `EffectComponentInstance(expires_at=now+duration, magnitude=computed_magnitude)`. If `stat_bonus`/`stat_penalty`: call `apply_stat_effect()` immediately.
4. If no duration components: close instance immediately.
5. Return messages.

#### `_apply_instant_component(component, target, magnitude) → str`

| component_type | Action | Message |
|---|---|---|
| `restore_vitality` | Clamp-add to vitality_current | `"You feel your body recover. (+N Vitality)"` |
| `restore_longevity` | Clamp-add to longevity_current | `"Your stamina is restored. (+N Longevity)"` |
| `restore_acuity` | Nudge toward baseline, clamp [0.1, 1.9] | `"Your mind steadies. (Acuity N.N)"` |
| `durability_restore` | Placeholder | `"The repair kit fizzes but does nothing useful yet."` |
| *(other)* | No-op | `""` |

#### `apply_stat_effect(target, component_instance, reverse=False) → tuple[str, int] | tuple[None, None]`

Reads `component_instance.component.target_stat`. Adds `component_instance.magnitude` to `target.stat_{name}` (or subtracts if `reverse=True`, floored at 1). Saves via `update_fields`. Returns `(stat_name, new_value)` or `(None, None)`.

Replaces the old `apply_stat_effect()` that was in `combat_utils.py`. Signature changed — takes `EffectComponentInstance` not `EffectInstance`.

#### `_expiry_message_for_effect(effect_instance) → str`

Used when all components of a parent expire simultaneously. Looks at first component (by `order`) to determine primary type.

#### `_expiry_message_for_component(component_instance, definition_name) → str`

Used when components expire individually (staggered durations).

### 4.5 Combat utilities (`combat_utils.py`)

`apply_stat_effect()` removed — now in `effect_utils.py`.

`apply_npc_effects(npc_instance, target_character) → list[str]` now delegates to `apply_effect_definition()` for each `NpcEffect` that rolls successfully. Returns all effect messages plus effect definition names.

All other functions unchanged from v11.

### 4.6 Item generation and utilities (`item_utils.py`)

*(unchanged from v11)*

### 4.7 Admin

| Model | Registered as | Notable config |
|-------|--------------|----------------|
| `EffectDefinition` | `EffectDefinitionAdmin` | `EffectComponentInline` (tabular, extra=1); list_display: name, slug; search_fields: name, slug |
| `EffectComponent` | `EffectComponentAdmin` | list_display: definition, component_type, target_stat, magnitudes, durations, order; list_filter: component_type |
| `EffectInstance` | `EffectInstanceAdmin` | `EffectComponentInstanceInline` (read-only, can_delete=False); list_display: definition, target, mk_tier, is_active, applied_at |
| `EffectComponentInstance` | `EffectComponentInstanceAdmin` | All fields readonly; list_display: effect_instance, component, magnitude, expires_at, is_active, removed_by |
| All other models | unchanged from v11 | |

### 4.8 Seed data (`management/commands/seed_world.py`)

Idempotent (`get_or_create` on slug). After each `EffectDefinition` upsert, existing `EffectComponent` rows are deleted and recreated fresh.

**Seeded `EffectDefinition` entries:**

| Slug | Name | Component type | magnitude_base | magnitude_scaling | duration_base | duration_scaling |
|------|------|----------------|----------------|-------------------|---------------|------------------|
| `healing-draught` | Healing Draught | `restore_vitality` | 20.0 | 5.0 | 0.0 (instant) | 0.0 |
| `focus-tonic` | Focus Tonic | `shift_acuity_high` | 0.1 | 0.05 | 30.0 | 5.0 |
| `fracture-wraith-poison` | Fracture Wraith Poison | `dot_vitality` | 3.0 | 2.0 | 15.0 | 3.0 |

`durability_restore` is still deferred. Repair Kit `ItemDefinition` has `effect=None`.

`NpcEffect` linking Fracture Wraith → `fracture-wraith-poison` seeded with `effect_chance=0.30`.

### 4.9 Tick Engine (`management/commands/run_tick_engine.py`)

#### Structure

*(unchanged from v11)*

#### `process_combat(tick_number)`

*(unchanged from v11)*. Death handling (`execute_death`) also deactivates `EffectComponentInstance` rows (`removed_by='death'`) before closing parent `EffectInstance` rows.

#### `process_effects(tick_number)`

**Phase 1 — Component ticking (round boundaries only)**

Queries `EffectComponentInstance` where `is_active=True` and `component_type in TICKING_TYPES`:

```python
TICKING_TYPES = {
    'dot_vitality', 'dot_acuity', 'dot_longevity',
    'hot_vitality', 'hot_acuity', 'hot_longevity',
    'shift_acuity_high', 'shift_acuity_low',
}
```

| component_type | Action |
|---|---|
| `dot_vitality` | Reduce `vitality_current` by `magnitude`. If ≤ 0: set dying. Send damage message + status. |
| `dot_longevity` | Reduce `longevity_current` by `magnitude`, floor 0. Send drain message + status. |
| `dot_acuity` | Shift `acuity_current` by `-magnitude`, clamp [0.1, 1.9]. Send focus message + status. |
| `hot_vitality` | Add `magnitude` to `vitality_current`, cap at max. Send recovery message + status. |
| `hot_longevity` | Add `magnitude` to `longevity_current`, cap at max. Send recovery message + status. |
| `hot_acuity` | Nudge toward `acuity_baseline` by `magnitude`. Send clarity message + status. |
| `shift_acuity_high` | Add `magnitude` to `acuity_current`, clamp. Send sharpening message + status. |
| `shift_acuity_low` | Subtract `magnitude` from `acuity_current`, clamp. Send wavering message + status. |

**Phase 2 — Passive Acuity drift (every tick)**

Characters where `acuity_current != acuity_baseline` and no active `EffectComponentInstance` with `component_type in {'shift_acuity_high', 'shift_acuity_low'}`. Move toward baseline by `ACUITY_DRIFT_RATE`. Snap if within drift step. Silent.

**Phase 3 — Component expiry (every tick)**

Query `EffectComponentInstance` where `is_active=True` and `expires_at <= now`. Group by parent `EffectInstance` pk.

For each group: check if all active CIs on parent are expiring now. For each CI: if `stat_bonus`/`stat_penalty`, call `apply_stat_effect(reverse=True)`; deactivate CI. If not all expiring together: send per-component message. If all expiring together: send one parent-level message. If no CIs remain active on parent: close parent.

#### `_build_status(character) → dict`

```python
{'type': 'status', 'vitality': ..., 'acuity': ..., 'longevity': ..., 'room_name': '', 'area_name': None}
```

---

## 5. Data Flow Diagrams

### Effect application via `cmd_use`

```
Player: "use healing draught"
→ SkylandConsumer.cmd_use(args)
→ get_carried_consumables()                                [DB]
→ do_apply_effect(effect_def, char, mk_tier)              [DB: @database_sync_to_async]
    → apply_effect_definition(definition, target, mk_tier)
        → reapplication check                              [DB: EffectInstance filter]
        → EffectInstance.save()                            [DB]
        → for each EffectComponent:
            → if instantaneous: _apply_instant_component() + Character.save()
            → else: EffectComponentInstance.save()
→ consume_item(item)                                       [DB: item.delete()]
→ output messages; send status
```

### Component expiry (Phase 3)

```
→ EffectComponentInstance.filter(is_active=True, expires_at__lte=now)
→ group by parent EffectInstance
→ for each group:
    → if stat_bonus/stat_penalty: apply_stat_effect(reverse=True)
    → expire each CI
    → send expiry messages (per-effect if all expire together, else per-component)
    → if no active CIs remain: close parent EffectInstance
```

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
- `brief` toggle (first visit shows full description; repeat visits show `brief_description`)
- Minimap and fog-of-war rendering in client (`RoomVisit` records exist but are not rendered)
- Admin in-game teleport commands
- All chat channels except `say` and `who`: `yell`, `tell`, `party`, `guild`, `zone`, `general`, `emote`
- Zone content beyond The Convergence (5 starter rooms)
- Monitoring container — tracks health of all containers

---

## 8. Known Issues / Flags for Future Sessions

**Status message omits bar maximums.** `send_room_description()` sends `vitality`, `acuity`, and `longevity` current values but not their maximums or Acuity band bounds.

**`format_wallet()` is wired but unused.** Accesses `character.current_room.zone.slug` — ensure `current_room__zone` is in `select_related`.

**Side panel is a stub.** `game.html` shows "Session 1 — world coming soon." in the side panel.

**`create_corpse()` is synchronous.** Always call it from within a `@database_sync_to_async` wrapper.

**No room description sent after entering combat.** When a player moves into a room with aggressive NPCs, the room description is not sent.

**Combat status updates lack `room_name`.** The status dict sent by the tick engine during combat has `room_name: ''`.
