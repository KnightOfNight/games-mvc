# Shyland Architecture

> Authoritative technical reference as of commit 22c4ace (combat v1).  
> Describes what is built. For design intent see `Shyland_GDD_v3.md`.

---

## 1. Overview

Shyland is a free, browser-based Multi-User Dungeon. The primary interface is text: players connect via WebSocket, type commands, and read descriptive output. A minimal visual chrome (status bar, side panel) supplements the text pane. As of this commit, combat v1 is complete: players can engage NPCs with `kill`/`attack`, fight through tick-driven combat rounds, flee to adjacent rooms, and die with penalties before respawning at their recall room. Aggressive NPCs attack players on room entry. The full pre-combat game loop is also complete: movement, chat, `who`, item interaction (`pickup`, `drop`, `equip`, `unequip`, `use`, `examine`, `loot`), soulbind, item identification, and the full currency system. The tick engine drives corpse decay, NPC respawn, effect expiry, and now combat rounds. The `send_room_description` function filters the players-here list against Redis presence keys so offline characters do not appear in room descriptions. Actual NPC AI (wandering, dialogue) and many other game systems have not yet been built — see [Section 7](#7-what-is-not-yet-built).

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
```

`CORPSE_DECAY_MINUTES` is at module level; `COMBAT_ROUND_TICKS` and friends are imported by the tick engine and consumer. All callers should import these constants rather than hardcoding numeric literals.

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
                  An area with no area_description still groups rooms for
                  admin filtering and minimap clustering.
```

`Meta: ordering = ['zone', 'name']`  
`__str__`: `"Zone name / Area name"`

Areas are **optional** — not every room belongs to one. Standalone rooms work exactly as before. Any multi-room location with a coherent identity (marketplace, dungeon wing, ship) should be modelled as an Area.

#### Room

```
zone              FK → Zone (CASCADE)
area              FK → Area (nullable, SET_NULL), related_name='rooms'
                  — optional; rooms without an area behave identically to pre-Area behaviour
name              CharField(200)
description       TextField              — shown on first visit / look
brief_description CharField(500)        — shown on repeat visits (not yet implemented)
coord_x/y/z       IntegerField(default=0)  — position within zone grid for minimap

Exit FKs (all nullable, SET_NULL, self-referential):
  exit_north, exit_south, exit_east, exit_west, exit_up, exit_down

Room flags (all BooleanField, default=False):
  flag_safe       — no combat, no PvP
  flag_pvp        — PvP enabled in this room
  flag_dark       — reduced visibility
  flag_indoors    — affects weather/sky mechanics
  flag_water      — aquatic movement rules
  flag_no_recall  — recall spell blocked
  flag_radiation  — radiation damage tick
  flag_holy       — holy/undead interactions
  flag_magic_dead — magic suppressed
  flag_scaled     — Wastelands per-room scaling marker
```

`exits()` method — returns a dict of `{direction: True}` for each non-null exit, using `exit_{direction}_id` (the integer FK column) to avoid triggering a synchronous ORM lookup in async context. Only direction keys are used; the Room objects themselves are never accessed through this method.

#### Character

```
user         OneToOneField → auth.User (CASCADE), related_name='shyland_character'
origin       CharField, choices:
               highborn | feral | streetborn | irradiated | undying | machinekind | voidtouched
archetype    CharField, choices:
               blade | bulwark | shade | conduit | warden | gunner | machinist
level        IntegerField(default=1)
xp           IntegerField(default=0)
current_room FK → Room (nullable, SET_NULL), related_name='characters'
recall_room  FK → Room (nullable, SET_NULL), related_name='recall_characters'

Primary stats (all IntegerField, default=10):
  stat_str, stat_dex, stat_end, stat_int, stat_wis, stat_per

Three bars:
  vitality_current   IntegerField(default=100)
  vitality_max       IntegerField(default=100)
  acuity_current     FloatField(default=1.0)    — damage modifier; 1.0 = neutral
  acuity_baseline    FloatField(default=1.0)    — origin-specific resting value
  acuity_band_low    FloatField(default=0.8)    — lower bound of optimal range
  acuity_band_high   FloatField(default=1.2)    — upper bound of optimal range
  longevity_current  IntegerField(default=100)
  longevity_max      IntegerField(default=100)

Currency:
  copper  BigIntegerField(default=0)   — ALL currency stored here; see §4.2

Flags:
  is_hardcore  BooleanField(default=False)  — permadeath
  is_dead      BooleanField(default=False)
  is_dying     BooleanField(default=False)  — True while in dying state (0 vitality)
  dying_since  DateTimeField(null=True)     — set when is_dying becomes True

Timestamps:
  created_at   DateTimeField(auto_now_add=True)
  last_seen    DateTimeField(auto_now=True)
```

**Acuity scale:** Acuity is now stored as a `FloatField` in the range 0.1–1.9. The stored value IS the damage modifier passed to `calculate_damage()` in `combat_utils.py`. 1.0 is neutral. Being too high or too low degrades combat performance in different ways. Per-origin defaults are applied at character creation and reset on death. The old 0-100 integer scale was retired in migration `0008` / `0009`.

**`name` is a Python property, not a database column** (removed in migration `0002_remove_character_name`):

```python
@property
def name(self):
    try:
        tag = self.user.profile.gamer_tag
        if tag:
            return tag
    except ObjectDoesNotExist:
        pass
    return self.user.username
```

Resolution order: `gamer_tag` (if set and non-null) → `user.username`. Changing a player's gamer tag renames them in Shyland immediately. Always fetch characters with `select_related('user__profile')` before accessing `.name`.

**Dying state:** When a character's `vitality_current` reaches 0, the tick engine sets `is_dying = True` and `dying_since = now`. All commands except `use` are blocked while dying. After `DYING_DURATION_SECS` (30s), `execute_death` fires: penalties are applied, the character is teleported to `recall_room` with full bars, and `is_dying` is cleared. A connected player sees the death message via their personal player group.

#### RoomVisit

```
character   FK → Character (CASCADE)
room        FK → Room (CASCADE)
visited_at  DateTimeField(auto_now_add=True)
unique_together: (character, room)
```

Fog-of-war tracking. A row is created on first entry to each room via `get_or_create` in `move_character()`. The minimap renderer (not yet built) will query this table.

#### EffectDefinition

Template for a game effect (buff, debuff, DoT, curse, etc.). The same definition is shared by all instances of that effect.

```
name           CharField(200)
slug           SlugField(unique)
effect_type    CharField(30), choices:
                 restore_vitality | restore_acuity | restore_longevity |
                 dot_vitality | dot_acuity | dot_longevity |
                 shift_acuity_high | shift_acuity_low |
                 stat_bonus | stat_penalty | durability_restore | curse_generic
magnitude_min  FloatField
magnitude_max  FloatField
duration_min   FloatField(null)   — seconds; null = instantaneous
duration_max   FloatField(null)
scales_with_mk BooleanField(default=False)
scaling_base   FloatField(null)
scaling_factor FloatField(null)
description    TextField(blank)   — builder notes
```

#### ItemDefinition

Template for an item type. One definition per item type (not per Mk tier). Instances are generated at drop time with Mk tier and rarity applied.

```
name                 CharField(200)
slug                 SlugField(unique)
item_type            CharField(20), choices: weapon | armor | accessory | consumable | bag | readable | key
genre_tag            CharField(20), choices: fantasy | cyber | wasteland | gothic | steam | cosmic
description          TextField         — flavor text shown to player

# Scaling
scaling_base         FloatField
scaling_factor       FloatField

# Weapon-specific
damage_spread        FloatField(null)
is_ranged            BooleanField(default=False)

# Equipment
valid_slots          JSONField(default=list)   — list of slot strings e.g. ["MAIN_HAND", "OFF_HAND"]
is_two_handed        BooleanField(default=False)

# Durability
takes_durability_loss    BooleanField(default=True)
durability_table         JSONField(default=list)
                         — [{min: N, max: N, penalty: N}, ...] threshold table

# Carry capacity (bags)
carry_bonus          IntegerField(default=0)

# Stats
primary_stats        JSONField(default=list)   — [{stat: "str", base: 5.0, factor: 1.2}, ...]
secondary_stat_pool  JSONField(default=list)   — same format; instances draw from this pool at generation

# Effect (consumables and cursed items)
effect               FK → EffectDefinition (null, SET_NULL)
is_cursed_template   BooleanField(default=False)

# Identification (mystery items)
mystery_name         CharField(200, blank)
                     — name shown before identification; e.g. "an unknown sword"
                     Falls back to "an unidentified <item_type>" if blank.
mystery_description  TextField(blank)
                     — description shown on examine before identification.
                     Falls back to "You can't determine anything about this item." if blank.
```

#### ItemInstance

A single in-game item. Either owned by a character (`owner` set), on the ground in a room (`current_room` set), or in a corpse (`corpse` set). Only one of the three may be non-null on a saved instance — `save()` raises `ValidationError` otherwise.

```
definition           FK → ItemDefinition (CASCADE)
owner                FK → Character (null, SET_NULL), related_name='inventory'
current_room         FK → Room (null, SET_NULL), related_name='items'
corpse               FK → Corpse (null, SET_NULL), related_name='contents'
                     — three-way mutual exclusion; enforced in save()

# Mk tier and rarity
mk_tier              IntegerField
rarity               CharField(20), choices: common | uncommon | rare | epic | legendary | artifact

# Rolled stats — stored at generation time
rolled_primary_stats    JSONField(default=list)
rolled_secondary_stats  JSONField(default=list)

# Weapon damage
damage_midpoint      FloatField(null)
damage_spread        FloatField(null)

# Durability
durability_current   FloatField(default=100.0)
is_broken            BooleanField(default=False)

# Soulbind
is_soulbound         BooleanField(default=False)
soulbound_to         FK → Character (null, SET_NULL), related_name='soulbound_items'

# Equipment state
is_equipped          BooleanField(default=False)
equipped_slot        CharField(20, blank)

# Curse state
is_cursed            BooleanField(default=False)
curse_identified     BooleanField(default=False)
active_curse         FK → EffectInstance (null, SET_NULL), related_name='cursed_item'

is_artifact          BooleanField(default=False)

# Identification
is_identified        BooleanField(default=True)
is_unidentifiable    BooleanField(default=False)

created_at           DateTimeField(auto_now_add=True)
```

`is_soulbound` is set to `True` when a character equips an item — not on pickup. Admin-gifted items are immediately soulbound via `generate_item_instance(gift=True)`. There is no unsoulbind operation for regular players.

#### EffectInstance

An active application of an EffectDefinition on a Character.

```
definition     FK → EffectDefinition (CASCADE)
target         FK → Character (CASCADE), related_name='active_effects'
source_item    FK → ItemInstance (null, SET_NULL), related_name='applied_effects'
source_ability CharField(100, blank)

magnitude      FloatField
duration       FloatField(null)        — seconds; null = instantaneous
applied_at     DateTimeField(auto_now_add=True)
expires_at     DateTimeField(null)

is_active      BooleanField(default=True)
removed_by     CharField(50, blank)
               — "timeout" | "warden" | "consumable" | "npc_service" | "repair" | "death"
```

`removed_by='death'` is set by `execute_death` in the tick engine to bulk-clear all active effects when a character dies.

#### LootTable / LootTableEntry

```
LootTable:
  name  CharField(200)
  slug  SlugField(unique)

LootTableEntry:
  loot_table      FK → LootTable (CASCADE), related_name='entries'
  item_definition FK → ItemDefinition (CASCADE)
  mk_tier_min     IntegerField
  mk_tier_max     IntegerField
  drop_chance     FloatField      — 0.0 to 1.0
  rarity_weights  JSONField       — {rarity: weight, ...}; must sum to 100
```

#### NpcDefinition

Template for an NPC type.

```
name            CharField(200)
slug            SlugField(unique)
description     TextField
genre_tag       CharField(20), choices: fantasy | cyber | wasteland | gothic | steam | cosmic

is_aggressive   BooleanField(default=False)   — attacks players on room entry
is_unique       BooleanField(default=False)
wanders         BooleanField(default=False)

base_vitality   IntegerField
base_str        IntegerField
base_dex        IntegerField
base_end        IntegerField
base_int        IntegerField
base_wis        IntegerField
base_per        IntegerField
scaling_factor  FloatField(default=1.0)       — stat multiplier per Mk tier

loot_table          FK → LootTable (null, SET_NULL)
currency_drop_min   IntegerField(default=0)
currency_drop_max   IntegerField(default=0)

respawn_minutes IntegerField(default=30)
```

#### NpcEffect

Links an `EffectDefinition` to an `NpcDefinition` with a probability. When an NPC hits a character, `apply_npc_effects()` in `combat_utils.py` rolls each `NpcEffect` entry.

```
npc_definition    FK → NpcDefinition (CASCADE), related_name='effects'
effect_definition FK → EffectDefinition (CASCADE)
effect_chance     FloatField(default=1.0)   — 0.0–1.0; probability per attack
```

`Meta: ordering = ['npc_definition', 'effect_definition']`

#### NpcInstance

A single live (or recently dead) NPC in the world.

```
definition       FK → NpcDefinition (CASCADE), related_name='instances'
current_room     FK → Room (null, SET_NULL), related_name='npcs'
spawn_room       FK → Room (null, SET_NULL), related_name='npc_spawns'
                 — never changes; used as respawn destination
mk_tier          IntegerField(default=1)
vitality_current IntegerField
vitality_max     IntegerField
is_alive         BooleanField(default=True)
spawned_at       DateTimeField(auto_now_add=True)
respawn_at       DateTimeField(null)
```

`name` property returns `self.definition.name`. On death: `is_alive=False`, `respawn_at` set, a `Corpse` row created by `create_corpse()`. On respawn: dead row deleted, new `NpcInstance` created in `spawn_room`. Rows are never reused.

#### Corpse

```
npc_definition    FK → NpcDefinition (null, SET_NULL)
npc_name_snapshot CharField(200)
current_room      FK → Room (null, SET_NULL), related_name='corpses'
killed_by         FK → Character (null, SET_NULL), related_name='kills'
created_at        DateTimeField(auto_now_add=True)
decay_at          DateTimeField
copper_drop       BigIntegerField(default=0)
```

`display_name` property returns `f"the corpse of {self.npc_name_snapshot}"`. Deleted (not flagged) when fully looted or when `decay_at` is reached.

#### CombatSession

Tracks an active fight between one character and one or more NPCs.

```
characters           M2M → Character, related_name='combat_sessions'
npcs                 M2M → NpcInstance, related_name='combat_sessions'
room                 FK → Room (SET_NULL, null), related_name='combat_sessions'
started_at           DateTimeField(auto_now_add=True)
last_tick_at         DateTimeField(null)    — updated each tick; used for stale detection
tick_counter         IntegerField(default=0)
is_active            BooleanField(default=True)
first_attacker       CharField(max_length=20, default='character')
                     — 'character' or 'npc'; determines who acts first in round 1
last_flee_attempt_at DateTimeField(null)
last_flee_character  FK → Character (SET_NULL, null, related_name='+')
                     — tracks flee cooldown per character
```

`Meta: ordering = ['-started_at']`

V1 caps at one character per session. The M2M is in place for future group combat.

#### CombatAction

A queued action within a `CombatSession`. Created by the consumer (player actions) or the tick engine (NPC actions) each round.

```
combat_session   FK → CombatSession (CASCADE), related_name='actions'
character        FK → Character (CASCADE, null), related_name='combat_actions'
npc              FK → NpcInstance (CASCADE, null), related_name='combat_actions'
action_type      CharField, choices: attack | use | flee (default: attack)
target_character FK → Character (SET_NULL, null), related_name='targeted_by_actions'
target_npc       FK → NpcInstance (SET_NULL, null), related_name='targeted_by_actions'
item             FK → ItemInstance (SET_NULL, null), related_name='combat_actions'
queued_at        DateTimeField(auto_now_add=True)
is_processed     BooleanField(default=False)
```

`Meta: ordering = ['queued_at']`

Exactly one of `character` / `npc` is set (the actor). Exactly one of `target_character` / `target_npc` is set (the target). `item` is only set for `use` actions.

### 4.2 Currency system (`currency.py`)

All currency is stored as a single `BigIntegerField` named `copper` on `Character`. Display is purely presentational.

**Tier table:**

| Tier | Engine name | Value in copper | Multiplier from previous |
|------|-------------|-----------------|--------------------------|
| 1 | copper | 1 | — |
| 2 | silver | 10 | ×10 |
| 3 | gold | 1,000 | ×100 |
| 4 | platinum | 1,000,000 | ×1,000 |
| 5 | (future) | 10,000,000,000 | ×10,000 |

**Public API:**

| Function | Purpose |
|----------|---------|
| `to_copper(platinum, gold, silver, copper)` | Convert denomination mix → copper total |
| `from_copper(total)` | Decompose copper total → `{tier: amount}` dict (non-zero tiers only) |
| `display(total, currency_display=None)` | Human-readable string; naïve pluralisation |
| `add(total, amount)` | Add currency; raises `ValueError` if `amount < 0` |
| `subtract(total, amount)` | Subtract; raises `ValueError` on insufficient funds or negative amount |
| `can_afford(total, cost)` | Boolean; does not mutate |
| `display_for_zone(total, zone_slug)` | Looks up zone alias in `ZONE_CURRENCY_DISPLAY`, falls back to standard names |

**Zone currency aliases (`ZONE_CURRENCY_DISPLAY`):**

| Zone slug | copper | silver | gold |
|-----------|--------|--------|------|
| `ashenveil-cathedral` | Soul Token | Grave Mark | Death Crown |
| `the-neon-sprawl` | Credit | Kilocredit | Megacredit |

### 4.3 WebSocket consumer (`consumers.py`)

`SkylandConsumer(AsyncJsonWebsocketConsumer)` — path `ws/shyland/`.

#### Module-level constants

```python
DIRECTION_CANONICAL = {
    'north': 'north', 'n': 'north', 'south': 'south', 's': 'south',
    'east': 'east',   'e': 'east',  'west': 'west',   'w': 'west',
    'up': 'up',       'u': 'up',    'down': 'down',   'd': 'down',
}

REVERSE_DIRECTIONS = {
    'north': 'south', 'south': 'north',
    'east': 'west',   'west': 'east',
    'up': 'down',     'down': 'up',
}
```

`DIRECTION_CANONICAL` maps all direction aliases to their canonical form. `REVERSE_DIRECTIONS` is used by `get_flee_destination` to prefer the direction the player came from when fleeing.

#### Connection lifecycle

**`connect()`**
1. Rejects unauthenticated connections immediately (no `accept()`).
2. Loads `Character` via `get_character(user)` with `select_related('current_room__zone', 'recall_room', 'user__profile')`.
3. If no character found: accepts, sends error output, closes.
4. Stores `character_pk` as a primitive on `self` — used in disconnect even if connect fails later.
5. Sets `self.last_direction = None` (tracks last movement direction for flee logic).
6. Sets `self._character_is_dying = self.character.is_dying` (used by the dying-state command guard).
7. Accepts the connection.
8. If `current_room_id` is `None`: sends error, returns (connection stays open but idle).
9. Calls `get_current_room()` (full select_related on all exits).
10. Joins `room_{room.id}` channel group.
11. Joins `player_{character_pk}` personal group (used by tick engine to deliver per-player notifications).
12. Creates an `aioredis` client (`redis://redis:6379`); writes `shyland:online:{character_pk}` with the character's display name and a 90-second TTL.
13. Starts `presence_heartbeat` background task.
14. Sends room description + status message to client.

**`disconnect(code)`**
1. Cancels `presence_heartbeat` task if started.
2. Deletes `shyland:online:{character_pk}` from Redis if the presence key was written.
3. Leaves `player_{character_pk}` personal group if joined.
4. Leaves room channel group if joined.
5. Updates `character.last_seen` via `touch_last_seen()`.

#### Redis presence system

Online presence is tracked via Redis keys with the pattern `shyland:online:{character_pk}`. The value stored is the character's display name (resolved at connect time from `character.name`). This avoids a DB lookup on every `who` call.

- **TTL:** 90 seconds
- **Heartbeat:** `presence_heartbeat()` is a background `asyncio` task that refreshes the TTL via `redis.expire()` every 60 seconds while the connection is live.
- **Connect:** key is written after the room group is joined, immediately before `send_room_description()`.
- **Disconnect:** heartbeat task is cancelled first, then the key is deleted.
- **Room description filter:** `send_room_description()` queries `get_others_in_room(room)` (DB, returns all character names whose `current_room` matches), then cross-references against all live `shyland:online:*` Redis keys. Only names present in Redis are included in the `players` field sent to the client. This prevents offline characters (whose `current_room` still points to a room in the DB) from appearing in room descriptions. The Redis scan is a two-step `keys()` + `mget()`.

#### Command dispatch (`receive_json`)

Client sends: `{"text": "<raw command string>"}`

The text is stripped, split on whitespace into `verb` + optional `args`. **Dying state guard:** if `self._character_is_dying` is True and the verb is not `use`, the consumer sends an error message and returns immediately without dispatching. Dispatch:

| verb | handler |
|------|---------|
| `north` / `n` / `south` / `s` / `east` / `e` / `west` / `w` / `up` / `u` / `down` / `d` | `cmd_move(verb)` |
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
| `help` / `?` | `cmd_help()` |
| anything else | unknown command message |

#### Commands

**`look` / `l`** — fetches current room via `get_current_room()`, calls `send_room_description()`.

**Movement** — `cmd_move(direction)`:
1. Fetches current room (with exits select_related).
2. Checks exit field for direction; sends "no exit" message and returns if null.
3. Broadcasts `"{name} has left."` to old room group (excluding the mover).
4. Leaves old room group.
5. Updates `Character.current_room` in DB; creates `RoomVisit` record if new. Sets `self.last_direction = DIRECTION_CANONICAL[direction]`.
6. Joins new room group.
7. Broadcasts `"{name} has arrived."` to new room group (excluding the mover).
8. Re-fetches destination via `get_current_room()` with full select_related.
9. **Aggro check:** calls `get_aggro_npcs_in_room(destination)` (NPCs with `is_aggressive=True` and `is_alive=True`). If any are found, sends a combat announce message for each and calls `start_combat(aggro_npcs, first_attacker='npc')`. If no aggro NPCs, calls `send_room_description(destination)`.

**`say <text>`** — broadcasts `[say] {name}: {text}` with category `chat` to current room group.

**`who`** — queries Redis for all `shyland:online:*` keys, retrieves names via `mget`, returns a sorted list with a count. No DB call.

**`kill` / `attack` / `k <noun>`** — `cmd_attack(args)`:
1. Requires args; sends `"Attack what?"` if empty.
2. Re-fetches character via `get_character_fresh()` (ensures `is_dying` is current).
3. Fetches live NPCs in room via `get_live_npcs_in_room(room)`.
4. Matches `args` against NPC names via `parse_npc_noun(args, npcs)`.
5. If not found: `"You don't see that here."`.
6. Sends `"You attack the {name}!"` to player; broadcasts `"{char} attacks the {name}!"` to room (excluding attacker).
7. Calls `start_combat([npc], first_attacker='character')` to create or join a `CombatSession`.

**`flee`** — `cmd_flee()`:
1. Re-fetches character via `get_character_fresh()`.
2. If no active `CombatSession`: `"You are not in combat."`.
3. If `is_dying`: `"You are too close to death to flee!"`.
4. Checks flee cooldown via `check_flee_cooldown(character, session)` — cooldown = `FLEE_COOLDOWN_TICKS × COMBAT_ROUND_TICKS` seconds. If on cooldown: error.
5. Rolls success: `(character.stat_dex + d20) > average_npc_per` of session NPCs.
6. **Success:** gets flee destination via `get_flee_destination(character)` — prefers the reverse of `self.last_direction`; falls back to a random exit; returns `None` if no exits exist. If no destination: `"There is nowhere to run!"` + records flee attempt. Otherwise: sends success message, broadcasts to room, ends session, moves to destination room, sets `self.last_direction`, checks for aggro NPCs in destination.
7. **Failure:** sends failure message, broadcasts to room, records flee attempt (sets cooldown).

**`use`** — use a consumable item. Acuity clamp uses the float scale [0.1, 1.9]. This is the only command not blocked by the dying-state guard (allows revival items).

All other commands (`inventory`, `pickup`, `drop`, `equip`, `unequip`, `examine`, `loot`) are unchanged from v9 — see v9 doc for details.

#### Output format

Two message types sent to client:

```json
// Text output — appended to the log pane
{"type": "output", "text": "...", "category": "room|chat|combat|system|error"}

// Status update — updates header bar and room name
{"type": "status", "vitality": N, "acuity": N, "longevity": N,
 "room_name": "...", "area_name": "..." | null}
```

`area_name` is `null` when the room has no area. `room_name` is always present. The `combat` category was added for combat messages; maps to red CSS class.

**Room description output format** (`send_room_description`):
- Header line: `[ Area Name — Room Name ]` when the room belongs to an area; `[ Room Name ]` when it does not.
- If `room.area.area_description` is non-empty, it is inserted between the header and the room-specific description.
- Players-here: filtered to online characters only (Redis presence check).
- NPCs: each live NPC in room is listed as `"{name} is here."` (category `room`).
- Corpses: each corpse is listed as `"The corpse of {name} lies here."` (category `room`).

#### DB helper pattern

All ORM operations are in `@database_sync_to_async` methods. Key queries:

| Helper | Key select_related |
|--------|-------------------|
| `get_character(user)` | `current_room__zone`, `recall_room`, `user__profile` |
| `get_current_room()` | `zone`, `area`, all six `exit_*` rooms |
| `get_others_in_room(room)` | `user__profile` |
| `get_character_fresh()` | `current_room__zone`, `recall_room`, `user__profile` — also updates `self.character` and `self._character_is_dying` |
| `get_aggro_npcs_in_room(room)` | `definition`, prefetch `definition__effects__effect_definition` |
| `get_live_npcs_in_room(room)` | `definition`, prefetch `definition__effects__effect_definition` |

**Combat DB helpers (all `@database_sync_to_async`):**

| Helper | Purpose |
|--------|---------|
| `start_combat(npcs, first_attacker)` | Creates or joins a `CombatSession`; adds NPCs to it |
| `get_active_combat_session(character)` | Returns first active session for character, or `None` |
| `get_session_npcs(session)` | Returns list of live NPCs in session |
| `end_combat_session(session)` | Sets `is_active=False`, clears NPCs |
| `get_flee_destination(character)` | Returns `(Room, direction_str)` or `None` |
| `check_flee_cooldown(character, session)` | Returns True if flee is on cooldown |
| `record_flee_attempt(character, session)` | Updates `last_flee_attempt_at` and `last_flee_character` |
| `parse_npc_noun(noun_str, npcs)` | Classic `[N.]keyword` noun resolution against NPC list |

### 4.4 Combat utilities (`combat_utils.py`)

Pure Python functions — no Django ORM calls, no async. All functions are synchronous and must be called from within a `@database_sync_to_async` wrapper when used in async context.

| Function | Signature | Purpose |
|----------|-----------|---------|
| `get_acuity_modifier(character)` | `→ float` | Clamps `character.acuity_current` to [0.1, 1.9], rounds to 1dp |
| `roll_initiative(stat_dex, stat_per)` | `→ int` | `d10 + DEX + PER` |
| `resolve_hit(attacker_dex, target_dodge)` | `→ 'miss' \| 'graze' \| 'hit' \| 'critical'` | Rolls d100 + attacker_dex vs target_dodge with fixed thresholds |
| `calculate_damage(base_damage, stat_bonus, acuity_mod, durability_mod, hit_result, is_focus_target=True)` | `→ float (min 1.0)` | Applies acuity, durability, and hit multiplier. Acuity bonus (>1.0) only applies when `is_focus_target=True`; penalty (<1.0) always applies. |
| `get_npc_stats(npc_instance)` | `→ dict` | Returns scaled stat dict: `{dex, str, per, int, vitality}` using `definition.scaling_factor * mk_tier` |
| `get_npc_health_description(vitality_current, vitality_max)` | `→ str` | Descriptive health phrase (no raw numbers); 5 thresholds from "in perfect health" to "near death" |
| `apply_death_penalties(character)` | `→ list[str]` | Deducts `DEATH_DURABILITY_LOSS` from each equipped item with `takes_durability_loss=True`; applies XP loss at `XP_PENALTY_MIN_LEVEL`+; returns list of newly-broken item names |
| `apply_npc_effects(npc_instance, target_character)` | `→ list[str]` | Rolls each `NpcEffect` entry; creates `EffectInstance` for those that fire; returns list of effect names for appending to the hit message |
| `xp_for_kill(npc_instance, character)` | `→ int` | `int(mk_tier * 10 * definition.scaling_factor)` |

**`resolve_hit` thresholds:**

| Result | Condition |
|--------|-----------|
| `miss` | `roll < target_dodge` |
| `graze` | `target_dodge ≤ roll < target_dodge + 10` |
| `hit` | `target_dodge + 10 ≤ roll < target_dodge + 30` |
| `critical` | `roll ≥ target_dodge + 30` |

**`calculate_damage` hit multipliers:**

| Hit result | Multiplier |
|------------|------------|
| `graze` | 0.5 |
| `hit` | 1.0 |
| `critical` | 1.5 |
| `miss` | — (handled before damage calc; never reaches this function) |

### 4.5 Item generation and utilities (`item_utils.py`)

`generate_item_instance(definition, mk_tier, rarity, owner=None, room=None, gift=False)` — generates but does not save an `ItemInstance`. The caller decides when to call `.save()`.

**Stat scaling** — for each entry in `primary_stats` / `secondary_stat_pool`:
- `midpoint = base + (factor × mk_tier)`
- Random multiplier drawn from rarity-specific range around 1.0:

| Rarity | Multiplier range |
|--------|-----------------|
| common | 0.85 – 1.00 |
| uncommon | 0.90 – 1.05 |
| rare | 0.95 – 1.10 |
| epic | 1.00 – 1.15 |
| legendary | 1.05 – 1.20 |

**Secondary stat draw by rarity:**

| Rarity | Secondary stats |
|--------|----------------|
| common | 0 |
| uncommon | 1 |
| rare | 2 |
| epic | 3 |
| legendary | all entries in pool |

**Display helpers:**

| Function | Description |
|----------|-------------|
| `get_display_name(item)` | Identified → `definition.name`; unidentified → `mystery_name` (or fallback) |
| `get_display_description(item)` | Identified → `definition.description`; unidentified → `mystery_description` (or fallback) |

**Noun parsers:**

| Function | Returns |
|----------|---------|
| `parse_item_noun(noun_str, item_list)` | `('all', None)` / `('single', item)` / `('not_found', None)` / `('bad_index', None)` |
| `parse_corpse_noun(noun_str, corpse_list)` | Same tuple pattern, no `'all'` return |

**Loot / corpse utilities:**

| Function | Purpose |
|----------|---------|
| `generate_loot_from_table(loot_table, mk_tier)` | Rolls a `LootTable`; returns list of unsaved `ItemInstance` objects |
| `create_corpse(npc_instance, killer)` | Creates and saves a `Corpse`; rolls copper drop and loot table; assigns items to corpse. **Synchronous — must be called from within a `@database_sync_to_async` wrapper.** |
| `get_durability_penalty(item)` | Walks `definition.durability_table` to return active performance penalty multiplier |

**Slot / stat display:**

| Name | Description |
|------|-------------|
| `SLOT_DISPLAY_NAMES` | Dict mapping slot keys to human-readable strings |
| `format_slot_name(slot_str)` | Returns readable slot name; falls back to `slot_str.title()` |
| `STAT_LABELS` | Dict mapping `str/dex/end/int/wis/per` to display labels |

### 4.6 Views and URLs

```python
# apps/shyland/urls.py
path('play/', views.game, name='game')       # → shyland/game.html, login_required
path('',      RedirectView → /shyland/play/)

# game_mvc/urls.py also registers:
path('shyland', RedirectView → /shyland/play/)   # handles missing trailing slash
```

The `game` view is a single `@login_required` function view that renders `shyland/game.html` with no context. All game state is delivered via WebSocket after page load.

### 4.7 Admin

| Model | Registered as | Notable config |
|-------|--------------|----------------|
| `Zone` | `ZoneAdmin` | Two inlines: `AreaInline` (tabular, name + slug, show_change_link) and `RoomInline` (tabular, name + coords + flag_safe); list_display: name, slug, danger_level, is_pvp_zone, is_scaled |
| `Area` | `AreaAdmin` | `RoomInlineForArea` (tabular, name + coords + flag_safe, show_change_link); list_filter on zone; `prepopulated_fields` slug from name |
| `Room` | `RoomAdmin` | `area` in list_display, list_filter, and raw_id_fields; `raw_id_fields` for all six exit FKs; list_filter on zone/area/flag_safe/flag_pvp |
| `Character` | `CharacterAdmin` | `list_select_related = ('user__profile',)`; `readonly_fields = ('wallet_display',)`; `raw_id_fields` for current_room/recall_room |
| `RoomVisit` | `RoomVisitAdmin` | Basic list: character, room, visited_at |
| `EffectDefinition` | `EffectDefinitionAdmin` | list_display: name, effect_type, scales_with_mk; `prepopulated_fields` slug from name; **`search_fields = ['name', 'slug']`** (required for `NpcEffectInline` autocomplete) |
| `ItemDefinition` | `ItemDefinitionAdmin` | list_display: name, item_type, genre_tag, takes_durability_loss; list_filter on item_type, genre_tag; fieldsets include Identification group |
| `ItemInstance` | `ItemInstanceAdmin` | list_display adds `is_identified`, `is_unidentifiable`; fieldsets include Identification group; `raw_id_fields` for owner, current_room, soulbound_to, active_curse |
| `EffectInstance` | `EffectInstanceAdmin` | list_display: definition, target, is_active, applied_at, expires_at; list_filter on is_active |
| `NpcDefinition` | `NpcDefinitionAdmin` | **`NpcEffectInline`** (TabularInline with `autocomplete_fields=['effect_definition']`) |
| `NpcEffect` | `NpcEffectAdmin` | list_display: npc_definition, effect_definition, effect_chance |
| `CombatSession` | `CombatSessionAdmin` | list_display: pk, room, is_active, started_at, first_attacker; list_filter on is_active |
| `CombatAction` | `CombatActionAdmin` | list_display: pk, combat_session, action_type, is_processed, queued_at; list_filter on action_type, is_processed |

### 4.8 Seed data (`management/commands/seed_world.py`)

`python manage.py seed_world` (via `make shell`) is idempotent (uses `get_or_create` throughout).

**Zone: The Convergence** — slug `the-convergence`, danger_level `sanctuary`

**5 rooms (all flag_safe=True), Area: The Fracture Point Plaza:**

```
                    The Northern Arcade (0, 1, 0)
                            ↕
The Western Gate ↔ The Fracture Point ↔ The Eastern Bazaar
  (-1, 0, 0)           (0, 0, 0)              (1, 0, 0)
                            ↕
                    The Southern Docks (0, -1, 0)
```

All 5 rooms are assigned to the area `the-fracture-point-plaza`. **The Fracture Point is the default starting room.**

**EffectDefinitions seeded:**

| slug | effect_type | magnitude_min | magnitude_max | duration | scales_with_mk |
|------|-------------|---------------|---------------|----------|----------------|
| `vitality-restore` | restore_vitality | 20.0 | 20.0 | instant | True |
| `acuity-shift-high` | shift_acuity_high | **0.3** | **0.5** | 15–30s | False |
| `durability-restore` | durability_restore | 25.0 | 25.0 | instant | False |

Note: `acuity-shift-high` magnitude was updated from 15.0/25.0 (old integer scale) to 0.3/0.5 (float scale) to match the new acuity range. The seed command updates pre-existing rows with old values in place.

**ItemDefinitions seeded (11 total):**

| slug | item_type | genre_tag | valid_slots |
|------|-----------|-----------|-------------|
| `iron-sword` | weapon | fantasy | MAIN_HAND |
| `combat-knife` | weapon | wasteland | MAIN_HAND, OFF_HAND |
| `pulse-pistol` | weapon (ranged) | cyber | RANGED, MAIN_HAND |
| `apprentice-staff` | weapon (2H) | fantasy | MAIN_HAND |
| `leather-vest` | armor | fantasy | CHEST |
| `ballistic-jacket` | armor | wasteland | CHEST |
| `copper-ring` | accessory | fantasy | RING |
| `satchel` | bag | fantasy | BACK (carry_bonus=20) |
| `healing-draught` | consumable | fantasy | — (effect: vitality-restore) |
| `focus-tonic` | consumable | fantasy | — (effect: acuity-shift-high) |
| `repair-kit` | consumable | wasteland | — (effect: durability-restore) |

**NpcDefinitions seeded (new in combat v1):**

| slug | is_aggressive | base_vitality | base_str | base_dex | respawn_minutes | location |
|------|---------------|---------------|----------|----------|-----------------|----------|
| `training-dummy` | False | 20 | 1 | 1 | 1 | The Fracture Point |
| `fracture-wraith` | **True** | 15 | 4 | 6 | 5 | The Eastern Bazaar |

**NpcEffect seeded:**
- Fracture Wraith → Acuity Shift High, `effect_chance=0.30`

**NpcInstances seeded (get_or_create keyed on definition + spawn_room):**
- Training Dummy in The Fracture Point
- Fracture Wraith in The Eastern Bazaar

### 4.9 Tick Engine (`management/commands/run_tick_engine.py`)

`python manage.py run_tick_engine` — a long-running Django management command. Runs as the `ticker` Docker container.

#### Structure

```python
Command.handle()        → asyncio.run(tick_loop())
tick_loop()             → while True: process_tick(tick_number); asyncio.sleep(1)
process_tick()          → process_combat(tick_number) FIRST, then corpse_decay, npc_respawn, effect_expiry
```

All ORM calls use `@database_sync_to_async`. Channel layer calls are plain `async` awaits.

#### Processors (in call order)

**`process_combat(tick_number)`** — new in combat v1. The first processor called each tick. Contains all combat logic as nested `@database_sync_to_async` inner functions (using the `_dsa` alias imported locally within the method).

Three phases:

1. **Stale session cleanup:** finds `CombatSession` rows where `is_active=True` and `last_tick_at < now - STALE_SESSION_SECS`. Closes each stale session (`is_active=False`). Stale sessions arise when all players disconnect mid-combat.

2. **Dying state expiry:** finds `Character` rows where `is_dying=True` and `dying_since <= now - DYING_DURATION_SECS`. For each expired character, calls `execute_death`:
   - Calls `apply_death_penalties(character)` — durability loss on equipped items; XP loss at level ≥ 10.
   - Moves character to `recall_room` with full `vitality_current`, `acuity_current` reset to `acuity_baseline`, and full `longevity_current`.
   - Clears `is_dying`, `dying_since`, `is_dead`.
   - Bulk-sets all active `EffectInstance` rows to `is_active=False, removed_by='death'`.
   - Deletes unprocessed `CombatAction` rows for the character.
   - Removes the character from all active `CombatSession` rows; closes any session that now has zero characters.
   - Sends death message and status update to the player's personal group.

3. **Active session round processing:** finds all `is_active=True` sessions, increments each session's `tick_counter` and updates `last_tick_at`. On ticks where `tick_counter % COMBAT_ROUND_TICKS != 0`, no further action. On a round boundary:
   - Loads session participants (characters + NPCs with `select_related`/`prefetch_related`).
   - If no characters or no NPCs: closes the session.
   - Loads unprocessed player `CombatAction` rows (in `queued_at` order); generates one NPC attack action per NPC.
   - If no player actions exist: auto-creates an attack action targeting the first NPC.
   - **Initiative / ordering:** round 1 honours `first_attacker` field (`'character'` first or `'npc'` first). Subsequent rounds roll `roll_initiative()` for character and average NPC; higher initiative goes first.
   - Calls `execute_actions()` — synchronous inner function wrapped in `_dsa`:
     - **Character attacks NPC:** resolves hit via `resolve_hit()`; picks equipped unbroken weapon (falls back to unarmed 1–3 base damage); calls `calculate_damage()` with `is_focus_target=(npc.pk == focus_npc_pk)` (v1: focus is always the first NPC in session). On NPC death: sets `is_alive=False`, sets `respawn_at`, calls `create_corpse()`, awards XP, removes NPC from session.
     - **NPC attacks character:** resolves hit; calculates damage from NPC STR stats; calls `apply_npc_effects()` to roll and create effect instances. On character reaching 0 vitality: sets `is_dying=True`, `dying_since=now`, sends dying warning message.
   - After `execute_actions`: sends all combat messages to player personal groups and room broadcasts.

**`process_corpse_decay()`** — queries `Corpse.decay_at <= now`. For each: deletes row (CASCADE clears contents), broadcasts decay message to room group.

**`process_npc_respawn()`** — queries `NpcInstance` where `is_alive=False`, `respawn_at <= now`, `definition.is_unique=False`, `spawn_room is not null`. For each: deletes dead row, creates fresh `NpcInstance` in `spawn_room`.

**`process_effect_expiry()`** — queries `EffectInstance` where `is_active=True`, `expires_at <= now`. For each: marks inactive, looks up expiry message by `effect_type`, sends to player personal group with status update.

#### Expiry messages by effect type

| `effect_type` | Expiry message |
|---|---|
| `restore_vitality` | *(instantaneous — skip silently)* |
| `restore_acuity` | *(instantaneous — skip silently)* |
| `restore_longevity` | *(instantaneous — skip silently)* |
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

**`broadcast_to_room(room_id, text, category='room')`** — sends to `room_{room_id}` group with `type: room_message`.

**`send_to_player(character_pk, text, category, status)`** — sends to `player_{character_pk}` group with `type: player_message`. When `status` is non-null, the consumer's `player_message` handler sends it as a second JSON message to the client. The `status` dict must include `'type': 'status'` for the handler to forward it correctly.

#### Logging policy

- Log meaningful activity only: decayed corpses, respawned NPCs, expired effects, combat deaths, stale session closures.
- Never log empty ticks.
- Never log a heartbeat.

### 4.10 Client template (`templates/shyland/game.html`)

Extends `base.html`. Pure vanilla JS — no framework.

**Layout (CSS grid, 100vh):**

```
┌────────────────────────────────────────────────┐  44px
│ [room name]              [V:100 A:50 L:100] [☰]│  header
├────────────────────────────────────┬───────────┤
│                                    │           │
│  output pane                       │  side     │  1fr
│  aria-live="polite"                │  panel    │
│  role="log"                        │  220px    │
│                                    │           │
├────────────────────────────────────┴───────────┤  42px
│ >  [command input field]           [SEND]      │  input row
└────────────────────────────────────────────────┘
```

**JavaScript behaviour:**
- Opens WebSocket at `wss://<host>/ws/shyland/` (or `ws://` if HTTP).
- On `message`: parses JSON; `output` type appends a `<div class="msg-{category}">` to `#output` and scrolls to bottom; `status` type updates `#room-name`, `#bar-v`, `#bar-a`, `#bar-l`.
- Combat messages additionally announce to `#combat-live` (`aria-live="assertive"`) via `requestAnimationFrame` reset-then-set pattern.
- `send()`: trims input, pushes to history (max 100), sends `{"text": value}`, clears input, refocuses.
- Command history: up/down arrows walk through history.
- Mobile (≤600px): side panel hidden by default, toggled via `☰` button.

**Color scheme (CSS vars):**

| Variable | Value | Meaning |
|----------|-------|---------|
| `--bg` | `#0d0d0f` | Page background |
| `--surface` | `#16161a` | Header/input/side panel |
| `--room` | `#a8d8a8` | Room descriptions |
| `--chat` | `#f0c060` | Say messages |
| `--combat` | `#e06060` | Combat output |
| `--system` | `#8888aa` | System messages |
| `--error` | `#cc4444` | Error messages |
| `--accent` | `#7b68ee` | Prompt symbol, SEND button, Acuity bar |

---

## 5. Data Flow Diagrams

### Player connects

```
Browser → nginx (SSL/WSS) → Daphne (ASGI)
  → AuthMiddlewareStack  (populates scope['user'])
  → SkylandConsumer.connect()
  → get_character()       [DB: SELECT with select_related user__profile, current_room__zone]
  → group_add('room_{id}')
  → group_add('player_{pk}')
  → redis.set('shyland:online:{pk}', name, ex=90)
  → get_current_room()    [DB: SELECT with select_related zone, area, all exits]
  → send_room_description()
      → get_others_in_room()  [DB: SELECT chars in room, exclude self]
      → redis.keys / mget     [filter to online only]
      → send_json {type: output, ...}
      → send_json {type: status, ...}
```

### Player moves ("north")

```
Client sends {"text": "north"}
→ receive_json()
→ cmd_move("north")
→ get_current_room()          [DB]
→ check exit_north_id → not None → destination room object
→ group_send(old_room, {type: room_message, text: "X has left.", exclude: channel_name})
→ group_discard(old_room)
→ move_character(destination) [DB: UPDATE character SET current_room; RoomVisit.get_or_create]
→ self.last_direction = 'north'
→ self.room_group = 'room_{destination.id}'
→ group_add(new_room)
→ group_send(new_room, {type: room_message, text: "X has arrived.", exclude: channel_name})
→ get_current_room()          [DB: re-fetch destination with zone, area, all exits pre-loaded]
→ get_aggro_npcs_in_room()    [DB]
  if aggro: start_combat()    [DB: create CombatSession, add NPC]
  else: send_room_description(destination)
```

### Combat tick (every COMBAT_ROUND_TICKS seconds)

```
Tick engine process_combat(tick_number)
→ get_active_sessions()       [DB]
→ update_session_tick()       [DB: tick_counter++, last_tick_at=now]
→ if tick_counter % 3 != 0: skip
→ load_participants()         [DB: chars + npcs with prefetch]
→ load_player_actions()       [DB: unprocessed CombatAction rows]
→ generate_npc_actions()      [DB: create CombatAction for each NPC]
→ roll initiative / order actions
→ execute_actions()           [DB: hit rolls, damage, saves, corpse creation, XP]
→ send_to_player() for each message / status
→ broadcast_to_room() for room-visible events
```

---

## 6. Key Design Decisions

These are settled. Do not revisit without deliberate consideration.

**Single `copper` BigIntegerField for all currency.** Avoids sync bugs between denomination fields. All math goes through `currency.py` functions. `subtract()` raises `ValueError` on insufficient funds.

**Character name from `user.profile.gamer_tag`.** No standalone name field on Character. Reuses the platform-wide gamer tag system. Always `select_related('user__profile')` before accessing `.name`.

**Items soulbound on equip, not on pickup.** Picking up transfers ownership but does not soulbind. The moment an item is equipped, it becomes permanently soulbound. Admin-gifted items are immediately soulbound via `generate_item_instance(gift=True)`.

**Item identification is per-character knowledge.** Items default to identified. Builders set `is_identified=False` explicitly. Dropping resets `is_identified` to `False` (unless `is_unidentifiable`). All player-facing display uses `get_display_name()` / `get_display_description()` — never `definition.name` directly.

**`ItemDefinition` / `ItemInstance` split.** One definition per item type; instances store rolled stats and state. `generate_item_instance()` applies Mk tier and rarity spread at generation time.

**Shared effect vocabulary.** Consumable, curse, and combat effects all use `EffectDefinition` + `EffectInstance`.

**Room Groups as the broadcast primitive.** Every player in room X is in channel group `room_{X.id}`. Movement = leave old group + join new group.

**Personal player groups for direct notification.** Each connected player joins `player_{character_pk}` on connect. The tick engine sends combat messages, effect expiry notices, and death messages to this group.

**Server is the authority; client is a dumb terminal.** Client sends text strings. Server sends JSON output. No game state is trusted from the client.

**Redis presence for `who` and room description filtering.** Online players are tracked via `shyland:online:{character_pk}` keys (90-second TTL, 60-second heartbeat refresh). The value is the character's display name. `who` needs no DB call. `send_room_description` cross-references `get_others_in_room()` (DB) against Redis presence keys to exclude offline characters from the players-here list. A character whose `current_room` still points to a room in the DB (normal for offline characters) will not appear unless they also have a live Redis key.

**`@database_sync_to_async` pattern throughout.** Never call ORM methods directly in async consumer or tick engine methods. Accessing FK descriptor objects in async context is also unsafe unless prefetched via `select_related`. `Room.exits()` uses `exit_{direction}_id` (integer column) to avoid this.

**Acuity as a float damage modifier (0.1–1.9).** Acuity is stored as a `FloatField` where the value IS the damage modifier: 1.0 = neutral, >1.0 = bonus, <1.0 = penalty. Per-origin defaults are defined in `_ACUITY_DEFAULTS` and `get_acuity_defaults()`. The old 0-100 integer scale was retired in migrations 0008/0009. Do not hardcode acuity clamp values — use the `[0.1, 1.9]` constants or `get_acuity_modifier()` in `combat_utils.py`.

**Tick-driven combat with queued actions.** Combat state lives in `CombatSession` (session-level metadata) and `CombatAction` (per-round actions). The tick engine owns all resolution; the consumer only creates the session and queues the initial action. Each combat round fires every `COMBAT_ROUND_TICKS` (3) ticks. Player actions are queued in DB; NPC actions are generated each round by the tick engine. If no player action is queued when a round fires, the tick engine creates an auto-attack.

**Dying state as a 30-second grace window.** Characters don't die instantly — they enter `is_dying=True` when vitality reaches 0. All commands except `use` are blocked. After `DYING_DURATION_SECS` (30s), the tick engine fires death penalties and respawns at `recall_room`. Future: another player could revive a dying character before the timer expires.

**Flee with cooldown and directional preference.** `flee` attempts a DEX + d20 vs average NPC PER roll. On success, destination prefers the reverse of `self.last_direction` (the way the player came in), then falls back to a random exit. A failed flee attempt sets a cooldown of `FLEE_COOLDOWN_TICKS × COMBAT_ROUND_TICKS` seconds. Cooldown is tracked per character per session in `CombatSession.last_flee_attempt_at` / `last_flee_character`.

**`make build` required after every code change.** Source is baked into the Docker image at build time. `make restart` picks up no Python or template changes.

**`make makemigrations` auto-syncs migration files.** Django generates migration files inside the container's ephemeral filesystem. The Makefile copies them back to `django/src/apps/*/migrations/` after generation. Edits made to a local migration file (e.g. adding `RunPython`) are NOT in the container until the next `make build`. Always rebuild after editing a migration file, then run `make migrate`.

---

## 7. What Is Not Yet Built

Future sessions should check this list before assuming a system exists.

- In-game character creation flow (admin creation works)
- Item identification trigger — NPC sage, Warden ability, identification scrolls (fields and display logic are in place; trigger mechanism deferred)
- Durability degradation on combat use (model field and death-penalty logic exist; per-hit degradation deferred)
- `durability_restore` consumable effect (placeholder response implemented; full repair system deferred)
- Duration-based effect ticking — DoT/HoT stat application per tick (expiry is implemented; per-tick damage/healing deferred)
- NPC AI — wandering, dialogue, patrol (is_aggressive aggro on room entry is implemented)
- Party system (M2M relationship on `CombatSession` is in place; multi-character combat not yet wired)
- Guild system
- Quest system
- Dungeon instancing
- PvP flagging, entry confirmation, and bounty system
- The Wastelands (`is_scaled=True`) level-scaling logic
- Level-up system and XP thresholds (XP accrual and death penalty exist; no level-up trigger)
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

**Status message omits bar maximums.** `send_room_description()` sends `vitality`, `acuity`, and `longevity` current values but not their maximums or Acuity band bounds. The client cannot render proportional bars. Add `vitality_max`, `longevity_max`, `acuity_band_low`, `acuity_band_high` to the `status` message when the client UI is extended.

**`format_wallet()` is wired but unused.** The helper is ready for vendor transactions; it accesses `character.current_room.zone.slug` — ensure `current_room__zone` is in `select_related` when calling it (already is in `get_character()`).

**Side panel is a stub.** `game.html` shows "Session 1 — world coming soon." in the side panel.

**`create_corpse()` is synchronous.** It is a sync function in `item_utils.py` — always call it from within a `@database_sync_to_async` wrapper. This is already done in the tick engine's `execute_actions`.

**DoT and HoT effects expire correctly but do not tick.** `EffectInstance` rows are marked inactive at `expires_at`, but per-tick stat changes are not applied. A `dot_vitality` effect will expire without dealing any damage.

**No room description sent after entering combat.** When a player moves into a room with aggressive NPCs, the room description is not sent — combat announce messages replace it. A `look` after the initial combat messages will show the room. Consider sending the room description first, then the combat announces.

**Combat status updates lack `room_name`.** The status dict sent by the tick engine during combat has `room_name: ''` (empty string) because the NPC attack path doesn't load the room name. The client will blank out the room-name display during combat. Fix by including the actual room name in the NPC-attack status payload.

**Acuity clamp in `use` / `cmd_use`.** The `use` command clamps acuity shift effects to the float scale [0.1, 1.9] — this was corrected from the old integer scale [0, 100]. Verify any future effect code also uses this range.
