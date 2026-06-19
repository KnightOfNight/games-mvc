# Shyland Architecture

> Authoritative technical reference as of commit d0ce3c4 (v11: effects ticking, level-up, stat spending).  
> Describes what is built. For design intent see `Shyland_GDD_v3.md`.

---

## 1. Overview

Shyland is a free, browser-based Multi-User Dungeon. The primary interface is text: players connect via WebSocket, type commands, and read descriptive output. A minimal visual chrome (status bar, side panel) supplements the text pane. As of this commit, v11 adds three systems on top of combat v1: (1) **effects tick over time** — DoT and Acuity-shift effects apply damage/shift each combat round; stat_bonus/stat_penalty effects apply their delta on creation and reverse it on expiry; passive Acuity drift returns characters to their origin baseline when no shift effect is active; (2) **level-up is real** — XP thresholds (`level² × 100`) trigger level-up, bars recalculate and fill, and 5 stat points are awarded per level; (3) **stat spending** — `spend <stat> <amount>` allocates unspent stat points; `stats` shows the full stat block with XP progress. The full combat game loop (kill/flee, tick-driven rounds, dying state, NPC aggro) was completed in combat v1. The pre-combat loop (movement, chat, `who`, item interaction, soulbind, identification, currency) is also complete. The tick engine drives corpse decay, NPC respawn, effect lifecycle, and combat rounds. Actual NPC AI (wandering, dialogue) and many other game systems have not yet been built — see [Section 7](#7-what-is-not-yet-built).

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
| `make build` | Rebuild Docker image and recreate containers — **required after any Python/template/settings change** (source is baked into the image, not volume-mounted) |
| `make start` / `make stop` / `make restart` | Container lifecycle |
| `make logs` | Follow all container logs |
| `make tick-logs` | Follow ticker container logs only |
| `make migrate` | Run `python manage.py migrate` inside the container |
| `make makemigrations [APP=name]` | Generate migrations **and automatically sync the generated files back to the local filesystem** (the container has an ephemeral filesystem; without the sync the files are lost on the next build) |
| `make shell` | Django shell inside the container |
| `make createsuperuser` | Create a Django admin superuser |
| `make new-app NAME=x` | Scaffold a new game app in `apps/` |

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

`AuthMiddlewareStack` populates `scope['user']` with the authenticated Django `User` before the consumer receives the connection. All consumers can rely on `self.scope['user']` being set.

### 3.2 `routing.py` — WebSocket URL registry

```python
path('ws/shyship/<uuid:game_id>/', ShyshipConsumer.as_asgi()),
path('ws/shyland/',               SkylandConsumer.as_asgi()),
```

Shyship uses a per-game UUID in the URL (many concurrent game sessions). Shyland uses a single path — player position is tracked server-side on `Character.current_room`, and the consumer swaps channel groups on movement.

### 3.3 `urls.py` — HTTP endpoints

| Path | Handler |
|------|---------|
| `/` | `HomeView` (game lobby) |
| `/admin/` | Django admin |
| `/accounts/` | `django.contrib.auth.urls` (login, logout, password) |
| `/api/auth/` | DRF browsable API auth |
| `/shydle` | Shydle app |
| `/shyship/` | Shyship app |
| `/shyland/` | Shyland app (see §4.6) |
| `/shyland` (no slash) | 302 → `/shyland/play/` |

### 3.4 Settings

| File | Used when | Notable differences |
|------|-----------|---------------------|
| `base.py` | Always imported | PostgreSQL, Redis channel layer, all INSTALLED_APPS |
| `production.py` | Default (container env) | `DEBUG=False`, `SECURE_SSL_REDIRECT=True`, `SECURE_PROXY_SSL_HEADER` set (nginx sets `X-Forwarded-Proto: https`) |
| `local.py` | Set `DJANGO_SETTINGS_MODULE=game_mvc.settings.local` | `DEBUG=True`, `ALLOWED_HOSTS=['*']`, **InMemoryChannelLayer** (no Redis needed for local dev without the full stack) |

### 3.5 Platform profile system (`apps.profiles`)

`apps.profiles` is a platform-wide app (not game-specific) that extends `auth.User` with a `UserProfile` model. It stores a single `gamer_tag` field (max 20 chars, unique, nullable). A `post_save` signal auto-creates a `UserProfile` for each new `User`.

Shyland uses this for `Character.name` — see §4.1. Any consumer or query that needs the character's display name must include `select_related('user__profile')` to avoid a synchronous DB hit in async context.

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
ACUITY_DRIFT_RATE     = 0.01  # Acuity movement per tick toward baseline (passive drift)
STAT_POINTS_PER_LEVEL = 5     # unspent stat points awarded per level-up
```

`ACUITY_DRIFT_RATE` and `STAT_POINTS_PER_LEVEL` are imported by the tick engine and consumer. All callers should import these constants rather than hardcoding numeric literals.

#### `_ACUITY_DEFAULTS` and `get_acuity_defaults(origin)`

```python
_ACUITY_DEFAULTS = {
    'highborn':    (1.0,  0.85, 1.15),
    'feral':       (0.95, 0.80, 1.10),
    'streetborn':  (1.0,  0.85, 1.15),
    'irradiated':  (0.90, 0.75, 1.05),
    'undying':     (0.80, 0.65, 1.00),
    'machinekind': (1.05, 0.90, 1.20),
    'voidtouched': (0.70, 0.40, 1.30),
}

def get_acuity_defaults(origin):
    return _ACUITY_DEFAULTS.get(origin, (1.0, 0.8, 1.2))
```

Returns `(baseline, band_low, band_high)`. Used by migrations and any shell reset. Falls back to `(1.0, 0.8, 1.2)` for unknown origins.

#### Zone

```
name         CharField(100)
slug         SlugField(unique)              — used in routing and ZONE_CURRENCY_DISPLAY keys
genre_tone   CharField(100)                 — e.g. "Classic fantasy wilderness"
danger_level CharField, choices:
               beginner | intermediate | advanced | sanctuary | all_levels
is_pvp_zone  BooleanField(default=False)
is_scaled    BooleanField(default=False)    — True for The Wastelands (scales to player level)
description  TextField
```

#### Area

```
zone              FK → Zone (CASCADE), related_name='areas'
name              CharField(200)
slug              SlugField(200, unique)
area_description  TextField(blank=True)
                  — shared atmospheric prose for all rooms in this area.
                  Shown above the room-specific description when non-empty.
```

`Meta: ordering = ['zone', 'name']`  
`__str__`: `"Zone name / Area name"`

Areas are **optional** — not every room belongs to one.

#### Room

```
zone              FK → Zone (CASCADE)
area              FK → Area (nullable, SET_NULL), related_name='rooms'
name              CharField(200)
description       TextField
brief_description CharField(500)
coord_x/y/z       IntegerField(default=0)

Exit FKs (all nullable, SET_NULL, self-referential):
  exit_north, exit_south, exit_east, exit_west, exit_up, exit_down

Room flags (all BooleanField, default=False):
  flag_safe, flag_pvp, flag_dark, flag_indoors, flag_water,
  flag_no_recall, flag_radiation, flag_holy, flag_magic_dead, flag_scaled
```

`exits()` method returns a dict of `{direction: True}` using `exit_{direction}_id` (integer FK column) to avoid synchronous ORM lookups in async context.

#### Character

```
user         OneToOneField → auth.User (CASCADE), related_name='shyland_character'
origin       CharField, choices:
               highborn | feral | streetborn | irradiated | undying | machinekind | voidtouched
archetype    CharField, choices:
               blade | bulwark | shade | conduit | warden | gunner | machinist
level        IntegerField(default=1)
xp           IntegerField(default=0)
unspent_stat_points  IntegerField(default=0)   — accumulated from level-ups; spent via `spend`
current_room FK → Room (nullable, SET_NULL), related_name='characters'
recall_room  FK → Room (nullable, SET_NULL), related_name='recall_characters'

Primary stats (all IntegerField, default=10):
  stat_str, stat_dex, stat_end, stat_int, stat_wis, stat_per

Three bars:
  vitality_current   IntegerField(default=100)
  vitality_max       IntegerField(default=100)
  acuity_current     FloatField(default=1.0)
  acuity_baseline    FloatField(default=1.0)
  acuity_band_low    FloatField(default=0.8)
  acuity_band_high   FloatField(default=1.2)
  longevity_current  IntegerField(default=100)
  longevity_max      IntegerField(default=100)

Currency:
  copper  BigIntegerField(default=0)

Flags:
  is_hardcore  BooleanField(default=False)
  is_dead      BooleanField(default=False)
  is_dying     BooleanField(default=False)
  dying_since  DateTimeField(null=True)

Timestamps:
  created_at   DateTimeField(auto_now_add=True)
  last_seen    DateTimeField(auto_now=True)
```

**`name`** is a Python property (not a DB column): resolves `gamer_tag` → `user.username`. Always fetch with `select_related('user__profile')`.

**Acuity** is stored as a `FloatField` in [0.1, 1.9]. The stored value IS the damage modifier. 1.0 = neutral.

**Dying state:** When `vitality_current` reaches 0 the tick engine sets `is_dying=True`. All commands except `use` are blocked. After `DYING_DURATION_SECS` the tick engine fires `execute_death`.

#### RoomVisit

```
character   FK → Character (CASCADE)
room        FK → Room (CASCADE)
visited_at  DateTimeField(auto_now_add=True)
unique_together: (character, room)
```

#### EffectDefinition

```
name           CharField(200)
slug           SlugField(unique)
effect_type    CharField(30), choices:
                 restore_vitality | restore_acuity | restore_longevity |
                 dot_vitality | dot_acuity | dot_longevity |
                 shift_acuity_high | shift_acuity_low |
                 stat_bonus | stat_penalty | durability_restore | curse_generic
target_stat    CharField(blank, choices: str|dex|end|int|wis|per)
               — which primary stat the effect modifies; only meaningful for
                 stat_bonus and stat_penalty effect types
magnitude_min  FloatField
magnitude_max  FloatField
duration_min   FloatField(null)
duration_max   FloatField(null)
scales_with_mk BooleanField(default=False)
scaling_base   FloatField(null)
scaling_factor FloatField(null)
description    TextField(blank)
```

#### ItemDefinition

*(unchanged from v10 — see v10 doc for full field listing)*

#### ItemInstance

*(unchanged from v10 — see v10 doc for full field listing)*

#### EffectInstance

```
definition     FK → EffectDefinition (CASCADE)
target         FK → Character (CASCADE), related_name='active_effects'
source_item    FK → ItemInstance (null, SET_NULL), related_name='applied_effects'
source_ability CharField(100, blank)
magnitude      FloatField
duration       FloatField(null)
applied_at     DateTimeField(auto_now_add=True)
expires_at     DateTimeField(null)
is_active      BooleanField(default=True)
removed_by     CharField(50, blank)
               — "timeout" | "warden" | "consumable" | "npc_service" | "repair" | "death"
```

`removed_by='death'` bulk-clears all active effects when a character dies.

#### LootTable / LootTableEntry / NpcDefinition / NpcEffect / NpcInstance / Corpse / CombatSession / CombatAction

*(unchanged from v10 — see v10 doc for full field listings)*

### 4.2 Currency system (`currency.py`)

*(unchanged from v10 — single `copper` BigIntegerField; all math through `currency.py`; `subtract()` raises `ValueError` on insufficient funds)*

### 4.3 WebSocket consumer (`consumers.py`)

`SkylandConsumer(AsyncJsonWebsocketConsumer)` — path `ws/shyland/`.

#### Connection lifecycle, Redis presence, command dispatch

Unchanged from v10 except for two additions to the dispatch table and `cmd_help`.

#### Command dispatch (`receive_json`) — additions

| verb | handler |
|------|---------|
| `stats` | `cmd_stats()` |
| `spend` | `cmd_spend(args)` |

All other verbs unchanged from v10.

#### New commands

**`stats`** — calls `get_character_fresh()` then `_send_stats(character)`. Displays full stat block: STR / DEX / END / INT / WIS / PER values; vitality and longevity with current/max; acuity current / baseline / band low–high; XP current and XP needed for next level (via `xp_for_next_level`); unspent stat points. If points > 0, appends a hint: `"Use: spend <stat> <amount>"`.

**`spend <stat> <amount>`** — `cmd_spend(args)`:
1. Parses `args` into stat name (str/dex/end/int/wis/per) and integer amount.
2. Validates: stat name must be in the allowed set; amount must be a positive integer; `character.unspent_stat_points >= amount`.
3. Inner `@database_sync_to_async apply_spend(char, stat, pts)`:
   - Increments `char.stat_<name>` by `pts`.
   - Decrements `char.unspent_stat_points` by `pts`.
   - If stat is `end`, `str`, or `wis`: calls `recalculate_bars(char)` and includes bar fields in `update_fields`.
   - Saves all changed fields via `update_fields`.
4. Sends confirmation output and a status update.

**`_send_stats(character)`** — shared helper used by `cmd_stats` and optionally after `cmd_spend`.

#### `player_message` handler (fix)

`if event.get('text'):` — skips events with empty or missing text (prevents sending empty output lines).  
`if event.get('status') is not None:` — skips events where status is `None` (prevents sending JSON `null` over WebSocket).

#### Output format

Unchanged from v10:
```json
{"type": "output", "text": "...", "category": "room|chat|combat|system|error"}
{"type": "status", "vitality": N, "acuity": N, "longevity": N, "room_name": "...", "area_name": "..." | null}
```

### 4.4 Combat utilities (`combat_utils.py`)

Pure Python functions — synchronous; must be called from within a `@database_sync_to_async` wrapper in async context.

| Function | Signature | Purpose |
|----------|-----------|---------|
| `apply_stat_effect(character, effect_instance, reverse=False)` | `→ (str, int) \| (None, None)` | Reads `effect_instance.definition.target_stat`; adds magnitude to the named `stat_<name>` field (`reverse=True` subtracts instead). Saves via `update_fields`. Returns `(stat_name, new_value)` or `(None, None)` if `target_stat` is blank. **Must be defined before `apply_npc_effects` in the file** — `apply_npc_effects` calls it. |
| `xp_for_next_level(level)` | `→ int` | `level * level * 100` — XP needed to reach the next level from `level` |
| `recalculate_bars(character)` | `→ (int, int)` | `vitality_max = (END×10)+(STR×3)+(level×5)`, `longevity_max = (END×8)+(WIS×5)+(level×5)`; sets current bars to new maximums; saves `update_fields=['vitality_max','vitality_current','longevity_max','longevity_current']`. Returns `(new_vitality_max, new_longevity_max)`. |
| `get_acuity_modifier(character)` | `→ float` | Clamps `character.acuity_current` to [0.1, 1.9], rounds to 1dp |
| `roll_initiative(stat_dex, stat_per)` | `→ int` | `d10 + DEX + PER` |
| `resolve_hit(attacker_dex, target_dodge)` | `→ 'miss' \| 'graze' \| 'hit' \| 'critical'` | d100 + attacker_dex vs target_dodge |
| `calculate_damage(base_damage, stat_bonus, acuity_mod, durability_mod, hit_result, is_focus_target=True)` | `→ float (min 1.0)` | Applies acuity, durability, and hit multiplier |
| `get_npc_stats(npc_instance)` | `→ dict` | Scaled stat dict using `scaling_factor * mk_tier` |
| `get_npc_health_description(vitality_current, vitality_max)` | `→ str` | 5-threshold health phrase |
| `apply_death_penalties(character)` | `→ list[str]` | Durability loss on equipped items; XP loss at level ≥ `XP_PENALTY_MIN_LEVEL` |
| `apply_npc_effects(npc_instance, target_character)` | `→ list[str]` | Rolls each `NpcEffect`; creates `EffectInstance` for those that fire; for `stat_bonus`/`stat_penalty` types, immediately calls `apply_stat_effect(target_character, instance, reverse=False)`; returns list of effect names |
| `xp_for_kill(npc_instance, character)` | `→ int` | `int(mk_tier * 10 * definition.scaling_factor)` |

### 4.5 Item generation and utilities (`item_utils.py`)

*(unchanged from v10)*

### 4.6 Views and URLs

*(unchanged from v10)*

### 4.7 Admin

| Model | Registered as | Notable config |
|-------|--------------|----------------|
| `Zone` | `ZoneAdmin` | Two inlines: `AreaInline`, `RoomInline`; list_display: name, slug, danger_level, is_pvp_zone, is_scaled |
| `Area` | `AreaAdmin` | `RoomInlineForArea`; list_filter on zone; prepopulated slug |
| `Room` | `RoomAdmin` | `area` in list_display/list_filter/raw_id_fields; raw_id_fields for all six exit FKs |
| `Character` | `CharacterAdmin` | `list_display` includes `unspent_stat_points` after `level`; fieldsets include a **Progression** section with `level`, `xp`, `unspent_stat_points`; `list_select_related = ('user__profile',)` |
| `RoomVisit` | `RoomVisitAdmin` | Basic list: character, room, visited_at |
| `EffectDefinition` | `EffectDefinitionAdmin` | `list_display`: name, slug, effect_type, **target_stat**, scales_with_mk; fieldsets include `target_stat` directly below `effect_type`; `search_fields = ['name', 'slug']` (required for NpcEffectInline autocomplete) |
| `ItemDefinition` | `ItemDefinitionAdmin` | list_display: name, item_type, genre_tag, takes_durability_loss |
| `ItemInstance` | `ItemInstanceAdmin` | Identification fieldset; raw_id_fields for owner, current_room, soulbound_to, active_curse |
| `EffectInstance` | `EffectInstanceAdmin` | list_display: definition, target, is_active, applied_at, expires_at |
| `NpcDefinition` | `NpcDefinitionAdmin` | `NpcEffectInline` with autocomplete_fields |
| `NpcEffect` | `NpcEffectAdmin` | list_display: npc_definition, effect_definition, effect_chance |
| `CombatSession` | `CombatSessionAdmin` | list_display: pk, room, is_active, started_at, first_attacker |
| `CombatAction` | `CombatActionAdmin` | list_display: pk, combat_session, action_type, is_processed, queued_at |

### 4.8 Seed data (`management/commands/seed_world.py`)

*(unchanged from v10 — idempotent; The Convergence zone; 5 rooms; 3 EffectDefinitions; 11 ItemDefinitions; 2 NpcDefinitions; 1 NpcEffect; 2 NpcInstances)*

### 4.9 Tick Engine (`management/commands/run_tick_engine.py`)

`python manage.py run_tick_engine` — long-running management command; runs as the `ticker` Docker container.

#### Structure

```python
Command.handle()   → asyncio.run(tick_loop())
tick_loop()        → while True: process_tick(tick_number); asyncio.sleep(1)
process_tick()     → process_combat(tick_number) FIRST,
                     then process_corpse_decay(),
                     then process_npc_respawn(),
                     then process_effects(tick_number)
```

All ORM calls use `@database_sync_to_async`. Channel layer calls are plain `async` awaits.

#### `process_combat(tick_number)`

Three phases (unchanged from v10):

1. **Stale session cleanup** — closes `CombatSession` rows with `last_tick_at < now - STALE_SESSION_SECS`.
2. **Dying state expiry** — fires `execute_death` for characters where `dying_since <= now - DYING_DURATION_SECS`. Death clears all active `EffectInstance` rows (`removed_by='death'`), applies penalties, teleports to `recall_room`, resets bars.
3. **Active session round processing** — on `tick_counter % COMBAT_ROUND_TICKS == 0`: resolves player and NPC actions, applies damage, handles NPC death and XP award.

**Level-up (new in v11) — inside `execute_actions` after XP award:**

```python
while character.xp >= xp_for_next_level(character.level):
    character.level += 1
    character.unspent_stat_points += STAT_POINTS_PER_LEVEL
    new_vit_max, new_lon_max = recalculate_bars(character)
    character.save(update_fields=[
        'level', 'unspent_stat_points',
        'vitality_max', 'vitality_current',
        'longevity_max', 'longevity_current',
    ])
    # sends level-up message + status to player personal group
```

Multiple levels in one kill are each announced separately. Bars fill to the new maximum on level-up.

#### `process_corpse_decay()` / `process_npc_respawn()`

*(unchanged from v10)*

#### `process_effects(tick_number)` — replaces `process_effect_expiry()`

Three phases per tick:

**Phase 1 — Effect ticking (round boundaries only: `tick_number % COMBAT_ROUND_TICKS == 0`)**

Processes these `effect_type` values for all active `EffectInstance` rows:

| effect_type | Action |
|-------------|--------|
| `dot_vitality` | Reduces `vitality_current` by `magnitude`. If ≤ 0: sets `is_dying=True`, `dying_since=now`, sends dying warning. Sends hit message + status. |
| `dot_acuity` | Shifts `acuity_current` by `-magnitude`. Clamps to [0.1, 1.9]. Sends message + status. |
| `dot_longevity` | Reduces `longevity_current` by `magnitude`. Clamps to 0. Sends message + status. |
| `shift_acuity_high` | Adds `magnitude` to `acuity_current`. Clamps to [0.1, 1.9]. Sends message + status. |
| `shift_acuity_low` | Subtracts `magnitude` from `acuity_current`. Clamps to [0.1, 1.9]. Sends message + status. |

**Phase 2 — Passive Acuity drift (every tick)**

Finds characters where `acuity_current != acuity_baseline` and no active `shift_acuity_high` or `shift_acuity_low` effect exists. Moves `acuity_current` toward `acuity_baseline` by `ACUITY_DRIFT_RATE` (0.01). If `abs(diff) <= ACUITY_DRIFT_RATE`, snaps directly to baseline. Silent — no message sent to player.

**Phase 3 — Effect expiry (every tick)**

Finds `EffectInstance` where `is_active=True` and `expires_at <= now`. For each:
- If `effect_type` is `stat_bonus` or `stat_penalty`: calls `apply_stat_effect(char, effect, reverse=True)` to undo the stat delta before marking inactive.
- Sets `is_active=False`, `removed_by='timeout'`.
- Sends expiry message to player's personal group (silent for restore and curse types).

#### Expiry messages (Phase 3)

| `effect_type` | Expiry message |
|---|---|
| `restore_vitality` / `restore_acuity` / `restore_longevity` | *(instantaneous — never have `expires_at`; skip)* |
| `shift_acuity_high` | `"Your heightened focus fades. Your mind settles."` |
| `shift_acuity_low` | `"The fog lifts from your mind. Your thoughts sharpen."` |
| `dot_vitality` | `"The pain subsides."` |
| `dot_acuity` | `"The mental static clears."` |
| `dot_longevity` | `"The draining sensation fades."` |
| `stat_bonus` | `"The {effect_name} fades. Your body returns to normal."` |
| `stat_penalty` | `"The {effect_name} lifts."` |
| `curse_generic` | *(handled by curse removal — skip silently)* |
| *(unrecognised)* | `"An effect has worn off."` |

#### Channel layer helpers

**`broadcast_to_room(room_id, text, category='room')`** — sends to `room_{room_id}` group.

**`send_to_player(character_pk, text, category, status)`** — sends to `player_{character_pk}` group. When `status` is non-null, the consumer's `player_message` handler forwards it as a second JSON message to the client.

#### Logging policy

Log meaningful activity only: decayed corpses, respawned NPCs, expired effects, combat deaths, stale session closures, level-ups. Never log empty ticks or heartbeats.

### 4.10 Client template (`templates/shyland/game.html`)

*(unchanged from v10 — vanilla JS, CSS grid layout, color scheme)*

---

## 5. Data Flow Diagrams

### Player connects

*(unchanged from v10)*

### Player moves ("north")

*(unchanged from v10)*

### Combat tick (every COMBAT_ROUND_TICKS seconds)

*(unchanged from v10)*

### Effect tick (every COMBAT_ROUND_TICKS seconds, Phase 1 of process_effects)

```
Tick engine process_effects(tick_number)
→ if tick_number % COMBAT_ROUND_TICKS == 0:
    → get_active_dot_and_shift_effects()   [DB: EffectInstance where is_active=True, effect_type in dot/shift types]
    → for each effect:
        → load character                   [DB]
        → apply damage/shift to bar field  [DB: save update_fields]
        → if vitality <= 0: set is_dying   [DB]
        → send_to_player() message + status
→ passive drift: chars with acuity != baseline, no active shift
    → update acuity_current toward baseline [DB]
→ expiry: EffectInstance where expires_at <= now
    → if stat_bonus/stat_penalty: apply_stat_effect(reverse=True) [DB]
    → mark is_active=False                 [DB]
    → send_to_player() expiry message
```

---

## 6. Key Design Decisions

These are settled. Do not revisit without deliberate consideration.

**Single `copper` BigIntegerField for all currency.** Avoids sync bugs between denomination fields. All math goes through `currency.py`. `subtract()` raises `ValueError` on insufficient funds.

**Character name from `user.profile.gamer_tag`.** No standalone name field on Character. Always `select_related('user__profile')` before accessing `.name`.

**Items soulbound on equip, not on pickup.** The moment an item is equipped it becomes permanently soulbound. Admin-gifted items are immediately soulbound via `generate_item_instance(gift=True)`.

**Item identification is per-character knowledge.** Dropping resets `is_identified` to `False`. All player-facing display uses `get_display_name()` / `get_display_description()` — never `definition.name` directly.

**`ItemDefinition` / `ItemInstance` split.** One definition per item type; instances store rolled stats and state.

**Shared effect vocabulary.** Consumable, curse, and combat effects all use `EffectDefinition` + `EffectInstance`.

**Room Groups as the broadcast primitive.** Every player in room X is in channel group `room_{X.id}`. Movement = leave old group + join new group.

**Personal player groups for direct notification.** Each connected player joins `player_{character_pk}` on connect. The tick engine sends combat messages, effect notices, level-up announcements, and death messages to this group.

**Server is the authority; client is a dumb terminal.** Client sends text strings. Server sends JSON output. No game state is trusted from the client.

**Redis presence for `who` and room description filtering.** Online players tracked via `shyland:online:{character_pk}` keys (90s TTL, 60s heartbeat). `who` needs no DB call.

**`@database_sync_to_async` pattern throughout.** Never call ORM methods directly in async context. `Room.exits()` uses `exit_{direction}_id` (integer column) to avoid FK descriptor access.

**Acuity as a float damage modifier (0.1–1.9).** 1.0 = neutral, >1.0 = bonus, <1.0 = penalty. Per-origin defaults in `_ACUITY_DEFAULTS`. Do not hardcode clamp values — use `get_acuity_modifier()`.

**Tick-driven combat with queued actions.** `CombatSession` owns session metadata; `CombatAction` owns per-round actions. The tick engine resolves all actions; the consumer only creates the session and queues the initial action.

**Dying state as a 30-second grace window.** Characters enter `is_dying=True` at 0 vitality. All commands except `use` are blocked. After `DYING_DURATION_SECS` the tick engine fires death and respawns at `recall_room`.

**Flee with cooldown and directional preference.** DEX + d20 vs average NPC PER. Success prefers reverse of `self.last_direction`. Failed attempt sets cooldown of `FLEE_COOLDOWN_TICKS × COMBAT_ROUND_TICKS` seconds.

**XP threshold formula: `level² × 100`.** `xp_for_next_level(level)` in `combat_utils.py`. Level 1→2 costs 100 XP; level 10→11 costs 10,000 XP. The while-loop in `execute_actions` handles multiple level-ups from a single kill.

**Stat points on level-up.** `STAT_POINTS_PER_LEVEL = 5` unspent points per level. Persisted indefinitely on `Character.unspent_stat_points`. Spent via `spend <stat> <amount>`. Never expire.

**Bar recalculation on stat change.** `vitality_max = (END×10)+(STR×3)+(level×5)`. `longevity_max = (END×8)+(WIS×5)+(level×5)`. `recalculate_bars()` also sets current bars to the new maximum (level-up fully restores). Called on level-up and whenever END, STR, or WIS is spent.

**Effect ticking and passive Acuity drift.** DoT and shift effects tick on round boundaries (`tick_number % COMBAT_ROUND_TICKS == 0`). `stat_bonus`/`stat_penalty` effects apply their delta immediately on creation (in both `apply_npc_effects` and `create_effect_instance`) and reverse it on expiry via `apply_stat_effect(reverse=True)`. Passive Acuity drift (`ACUITY_DRIFT_RATE = 0.01` per tick) runs every tick when no shift effect is active.

**`make build` required after every code change.** Source is baked into the Docker image at build time.

**`make makemigrations` auto-syncs migration files.** Django generates files inside the container's ephemeral filesystem; the Makefile copies them back. Always rebuild after editing a migration file, then run `make migrate`.

---

## 7. What Is Not Yet Built

Future sessions should check this list before assuming a system exists.

- In-game character creation flow (admin creation works)
- Item identification trigger — NPC sage, Warden ability, identification scrolls (fields and display logic are in place; trigger mechanism deferred)
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
- XP death penalty floor logic — level < `XP_PENALTY_MIN_LEVEL` (10) currently has no XP penalty; intended floor is level 10
- Revival mechanic — another player using a revival item on a dying character (dying timer exists; no revival command)
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

**Status message omits bar maximums.** `send_room_description()` sends `vitality`, `acuity`, and `longevity` current values but not their maximums or Acuity band bounds. Add `vitality_max`, `longevity_max`, `acuity_band_low`, `acuity_band_high` to the `status` message when the client UI is extended.

**`format_wallet()` is wired but unused.** Accesses `character.current_room.zone.slug` — ensure `current_room__zone` is in `select_related` when calling it (already is in `get_character()`).

**Side panel is a stub.** `game.html` shows "Session 1 — world coming soon." in the side panel.

**`create_corpse()` is synchronous.** Always call it from within a `@database_sync_to_async` wrapper. This is already done in the tick engine's `execute_actions`.

**No room description sent after entering combat.** When a player moves into a room with aggressive NPCs, the room description is not sent — combat announce messages replace it. A `look` after the initial combat messages will show the room.

**Combat status updates lack `room_name`.** The status dict sent by the tick engine during combat has `room_name: ''` because the NPC attack path doesn't load the room name. The client will blank out the room-name display during combat.
