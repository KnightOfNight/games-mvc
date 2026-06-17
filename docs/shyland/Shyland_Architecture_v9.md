# Shyland Architecture

> Authoritative technical reference as of commit 83de30b (tick engine).  
> Describes what is built. For design intent see `Shyland_GDD_v9.md`.

---

## 1. Overview

Shyland is a free, browser-based Multi-User Dungeon. The primary interface is text: players connect via WebSocket, type commands, and read descriptive output. A minimal visual chrome (status bar, side panel) supplements the text pane. As of this commit, the game loop is complete: a player can connect, move between rooms, chat, query who is online, and fully interact with items. Item interaction commands are implemented: `pickup` / `p`, `drop`, `equip` / `eq`, `unequip` / `uneq`, `use`, and `examine` / `ex`. The soulbind model is in place (items bind on equip, not pickup). The item identification system is in place (items can be mysterious; identification is per-character knowledge; display uses `get_display_name()` / `get_display_description()` throughout). Currency storage and the display utility are implemented. NPC and corpse models are in place. The `loot` command is implemented. The `examine` command covers items, live NPCs, and corpses. The `pickup` command excludes corpse contents. Loot table infrastructure (`LootTable`, `LootTableEntry`) is implemented. The tick engine is implemented as a Django management command (`run_tick_engine`) running as a fifth Docker container (`ticker`). It runs a 1-second loop processing corpse decay, NPC respawn, and EffectInstance expiry. The tick engine communicates with connected players via the Django Channels channel layer using personal player groups (`player_{character_pk}`). Actual NPC AI, combat, and all other game systems have not yet been built — see [Section 7](#7-what-is-not-yet-built).

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
| `/shyland/` | Shyland app (see §4.4) |
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
  acuity_current     IntegerField(default=50)   — dynamic; too high is as bad as too low
  acuity_baseline    IntegerField(default=50)   — origin-specific resting value
  acuity_band_low    IntegerField(default=35)   — lower bound of optimal range
  acuity_band_high   IntegerField(default=65)   — upper bound of optimal range
  longevity_current  IntegerField(default=100)
  longevity_max      IntegerField(default=100)

Currency:
  copper  BigIntegerField(default=0)   — ALL currency stored here; see §4.2

Flags:
  is_hardcore  BooleanField(default=False)  — permadeath
  is_dead      BooleanField(default=False)

Timestamps:
  created_at   DateTimeField(auto_now_add=True)
  last_seen    DateTimeField(auto_now=True)
```

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

A single in-game item. Either owned by a character (`owner` set) or on the ground in a room (`current_room` set). Both cannot be set simultaneously — `save()` raises `ValidationError` if both are non-null.

```
definition           FK → ItemDefinition (CASCADE)
owner                FK → Character (null, SET_NULL), related_name='inventory'
current_room         FK → Room (null, SET_NULL), related_name='items'
                     — mutually exclusive with owner; enforced in save()

# Mk tier and rarity
mk_tier              IntegerField
rarity               CharField(20), choices: common | uncommon | rare | epic | legendary | artifact

# Rolled stats — stored at generation time
rolled_primary_stats    JSONField(default=list)   — [{stat: "str", value: 14}, ...]
rolled_secondary_stats  JSONField(default=list)   — same format

# Weapon damage
damage_midpoint      FloatField(null)
damage_spread        FloatField(null)   — copied from definition; not affected by rarity

# Durability
durability_current   FloatField(default=100.0)   — 0.0–100.0
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
                     — whether this item's true nature is known to its current holder.
                     Builders set False on items they want to be mysterious.
                     Resets to False when the item is dropped (unless is_unidentifiable=True).
is_unidentifiable    BooleanField(default=False)
                     — if True, no in-game mechanism can ever identify this item.
                     Set by super users only on specific instances.
                     Intended for one-of-a-kind mystery Artifacts.

created_at           DateTimeField(auto_now_add=True)
```

`is_soulbound` is set to `True` when a character equips an item — not on pickup. Picking up an item sets `owner` but leaves `is_soulbound = False`. The character may still drop the item at this point. The moment an item is equipped, it becomes permanently soulbound (`is_soulbound = True`, `soulbound_to = character`). Unequipping does not unbind. Admin-gifted items are immediately soulbound via `generate_item_instance(gift=True)`. There is no unsoulbind operation for regular players.

`is_identified` (default `True`) — whether this item's true nature is known to its current holder. Builders set this to `False` on items that should be mysterious. Resets to `False` when the item is dropped (unless `is_unidentifiable = True`). Identification is per-character knowledge, not a property of the object.

`is_unidentifiable` (default `False`) — if `True`, no in-game mechanism can ever identify this item. Set by super users only on specific instances. Intended for one-of-a-kind mystery Artifacts.

#### EffectInstance

An active application of an EffectDefinition on a Character. Used for consumable effects, curse effects, and (future) combat effects.

```
definition     FK → EffectDefinition (CASCADE)
target         FK → Character (CASCADE), related_name='active_effects'
source_item    FK → ItemInstance (null, SET_NULL), related_name='applied_effects'
source_ability CharField(100, blank)   — combat ability slug if from combat

magnitude      FloatField
duration       FloatField(null)        — seconds; null = instantaneous
applied_at     DateTimeField(auto_now_add=True)
expires_at     DateTimeField(null)     — computed: applied_at + duration

is_active      BooleanField(default=True)
removed_by     CharField(50, blank)
               — "timeout" | "warden" | "consumable" | "npc_service" | "repair"
```

#### LootTable

```
name  CharField(200)
slug  SlugField(unique)
```

A named loot table. One `LootTable` is assigned to an `NpcDefinition`; it is rolled when that NPC dies.

#### LootTableEntry

```
loot_table      FK → LootTable (CASCADE), related_name='entries'
item_definition FK → ItemDefinition (CASCADE)
mk_tier_min     IntegerField    — minimum Mk tier for this entry
mk_tier_max     IntegerField    — maximum Mk tier for this entry
drop_chance     FloatField      — 0.0 to 1.0; rolled independently per entry
rarity_weights  JSONField       — {rarity: weight, ...}; keys: common/uncommon/rare/epic/legendary; must sum to 100
```

`clean()` validates that `rarity_weights` values sum to 100.

#### NpcDefinition

Template for an NPC type. One definition per NPC type.

```
name            CharField(200)
slug            SlugField(unique)
description     TextField         — shown when a player examines the NPC
genre_tag       CharField(20), choices: fantasy | cyber | wasteland | gothic | steam | cosmic

is_aggressive   BooleanField(default=False)   — attacks players on sight
is_unique       BooleanField(default=False)   — one instance only; no respawn
wanders         BooleanField(default=False)   — moves between rooms (not yet implemented)

base_vitality   IntegerField
base_str        IntegerField
base_dex        IntegerField
base_end        IntegerField
base_int        IntegerField
base_wis        IntegerField
base_per        IntegerField
scaling_factor  FloatField(default=1.0)       — stat multiplier per Mk tier

loot_table          FK → LootTable (null, SET_NULL)   — rolled on death; null = no item drops
currency_drop_min   IntegerField(default=0)   — minimum copper drop before Mk scaling
currency_drop_max   IntegerField(default=0)   — maximum copper drop before Mk scaling

respawn_minutes IntegerField(default=30)      — ignored if is_unique=True
```

Note: `CORPSE_DECAY_MINUTES = 10` is a module-level constant in `models.py`, not a field on `NpcDefinition`.

#### NpcInstance

A single live (or recently dead) NPC in the world.

```
definition       FK → NpcDefinition (CASCADE), related_name='instances'
current_room     FK → Room (null, SET_NULL), related_name='npcs'
spawn_room       FK → Room (null, SET_NULL), related_name='npc_spawns'
                 — the room this NPC spawns into; used for respawn; set at creation time; never changes
mk_tier          IntegerField(default=1)
vitality_current IntegerField
vitality_max     IntegerField
is_alive         BooleanField(default=True)   — live-NPC discriminator; False = dead/pending respawn
spawned_at       DateTimeField(auto_now_add=True)
respawn_at       DateTimeField(null)           — set on death; null while alive
```

`name` is a Python property returning `self.definition.name`. `is_alive=True` is the discriminator for querying live NPCs in the consumer. On death, the `NpcInstance` row is updated (`is_alive=False`, `respawn_at` set) and a `Corpse` row is created by `create_corpse()` in `item_utils.py`. On respawn, the dead row is deleted and a fresh `NpcInstance` is created in `spawn_room` — rows are never reused.

#### Corpse

Created by `create_corpse()` in `item_utils.py` when an NPC dies. Deleted (not flagged) when fully looted.

```
npc_definition    FK → NpcDefinition (null, SET_NULL)
                  — source NPC definition; SET_NULL so corpse survives definition deletion
npc_name_snapshot CharField(200)    — NPC name captured at death; stable even if definition is deleted
current_room      FK → Room (null, SET_NULL), related_name='corpses'
killed_by         FK → Character (null, SET_NULL), related_name='kills'
created_at        DateTimeField(auto_now_add=True)
decay_at          DateTimeField     — corpse and all contents deleted at this time; sweep deferred to tick engine
copper_drop       BigIntegerField(default=0)
                  — copper set at death by create_corpse(); transferred to killer on first loot; then set to 0
```

`display_name` is a Python property returning `f"the corpse of {self.npc_name_snapshot}"`. `copper_drop` is set once at death and zeroed after the killer loots. Only the killer (`killed_by`) may loot items; currency is visible to all via `examine` but only transferred to the killer. Corpse is deleted when `contents` is empty (checked after each loot operation by `check_corpse_empty_and_delete()`). There is no `is_fully_looted` flag.

#### ItemInstance changes

`ItemInstance` gains a third location field:

```
corpse  FK → Corpse (null, SET_NULL), related_name='contents'
```

`save()` enforces a three-way mutual exclusion: exactly one of `{owner, current_room, corpse}` may be non-null on a saved instance. `ValidationError` is raised if more than one are set. Zero non-null fields is permitted for unsaved instances being constructed before assignment.

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

Platinum has no alias in either zone (too rare to need one at this stage).

### 4.3 WebSocket consumer (`consumers.py`)

`SkylandConsumer(AsyncJsonWebsocketConsumer)` — path `ws/shyland/`.

#### Connection lifecycle

**`connect()`**
1. Rejects unauthenticated connections immediately (no `accept()`).
2. Loads `Character` via `get_character(user)` with `select_related('current_room__zone', 'recall_room', 'user__profile')`.
3. If no character found: accepts, sends error output, closes.
4. Stores `character_pk` as a primitive on `self` — used in disconnect even if connect fails later.
5. Accepts the connection.
6. If `current_room_id` is `None`: sends error, returns (connection stays open but idle).
7. Calls `get_current_room()` (full select_related on all exits).
8. Joins `room_{room.id}` channel group.
9. Joins `player_{character_pk}` personal group (used by tick engine to deliver per-player notifications).
10. Creates an `aioredis` client (`redis://redis:6379`); writes `shyland:online:{character_pk}` with the character's display name and a 90-second TTL.
11. Starts `presence_heartbeat` background task.
12. Sends room description + status message to client.

**`disconnect(code)`**
1. Cancels `presence_heartbeat` task if started.
2. Deletes `shyland:online:{character_pk}` from Redis if the presence key was written.
3. Leaves `player_{character_pk}` personal group if joined.
4. Leaves room channel group if joined.
5. Updates `character.last_seen` via `touch_last_seen()`.

#### Redis presence system

Online presence is tracked via Redis keys with the pattern `shyland:online:{character_pk}`. The value stored is the character's display name (resolved at connect time from `character.name`). This avoids a DB lookup on every `who` call.

- **TTL:** 90 seconds
- **Heartbeat:** `presence_heartbeat()` is a background `asyncio` task that refreshes the TTL via `redis.expire()` every 60 seconds while the connection is live. The 30-second grace window (90s TTL − 60s interval) means an unclean disconnect (process crash, network drop) causes the key to expire within 90 seconds — the player falls off `who` automatically.
- **Connect:** key is written after the room group is joined, immediately before `send_room_description()`.
- **Disconnect:** heartbeat task is cancelled first, then the key is deleted. `character_pk` (an integer) is used rather than `self.character` (an ORM object) because the character object may not be available if disconnect fires before connect completes.
- **Separate client:** a dedicated `aioredis` client is created per connection, distinct from the Django Channels channel layer Redis connection.

#### Command dispatch (`receive_json`)

Client sends: `{"text": "<raw command string>"}`

The text is stripped, split on whitespace into `verb` + optional `args`. Dispatch:

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
| `help` / `?` | `cmd_help()` |
| anything else | unknown command message |

#### Commands

**`look` / `l`** — fetches current room via `get_current_room()`, calls `send_room_description()`.

**Movement** — `cmd_move(direction)`:
1. Fetches current room (with exits select_related).
2. Checks exit field for direction; sends "no exit" message and returns if null.
3. Broadcasts `"{name} has left."` to old room group (excluding the mover via `exclude: self.channel_name`).
4. Leaves old room group.
5. Updates `Character.current_room` in DB; creates `RoomVisit` record if new.
6. Joins new room group.
7. Broadcasts `"{name} has arrived."` to new room group (excluding the mover).
8. Re-fetches destination via `get_current_room()` before calling `send_room_description()`. The exit-FK room object obtained in step 1 does not have its own FK relations (including `area`) pre-loaded; accessing them in async context raises `SynchronousOnlyOperation`. The re-fetch ensures `area` is available.
9. Sends room description for destination.

**`say <text>`** — broadcasts `[say] {name}: {text}` with category `chat` to current room group (all players in room, including the sender, receive it).

**`who`** — queries Redis for all `shyland:online:*` keys, retrieves names via `mget`, and returns a sorted list with a count. Only players with a live connection (or whose TTL has not yet expired after an unclean disconnect) appear. `None` values from `mget` are filtered to handle the race where a key expires between `keys()` and `mget()`. No DB call is made.

**`inventory` / `inv`** — fetches all `ItemInstance` objects owned by the character via `get_inventory()` and renders two sections:

1. **Equipment** — items where `is_equipped=True`, sorted by a fixed slot order: HEAD, NECK, SHOULDERS, CHEST, HANDS, WAIST, LEGS, FEET, RING, MAIN_HAND, OFF_HAND, RANGED, BACK. Each line shows: `[SLOT]  {Rarity} {Name} Mk {tier}` plus a suffix. Empty slots are omitted.

2. **Inventory** — unequipped items, sorted by item_type → mk_tier → rarity rank → name. Consumables of identical definition, Mk tier, and rarity are stacked with an `x{N}` count (presentational only — each is a separate DB row). Header shows current/max carry count: `(current/max items)` where max = `stat_str × 10 + sum of equipped bag carry_bonus values`.

Suffix rules:
- Bags: `+{carry_bonus} carry capacity`
- Items with `takes_durability_loss=True` and `is_broken=True`: `BROKEN`
- Items with `takes_durability_loss=True` and not broken: `{dur}% durability`
- All other items (rings, accessories without durability): no suffix

Curse status is never revealed for items where `curse_identified=False`.

**Item noun syntax (all item commands)** — classic MUD noun syntax is implemented in `parse_item_noun()` in `item_utils.py`:
- `sword` — first item in the relevant list whose display name contains "sword" (case-insensitive)
- `2.sword` — second item whose display name contains "sword"
- `all` — every item (where the command supports it)
- Matching uses `get_display_name(item)`, so unidentified items can be referred to by their mystery name.

**`pickup` / `p`** — pick up a loose item from the room floor.
- Eligible: `ItemInstance` objects where `current_room = character's room` and `owner is null`.
- Supports `all` (picks up all matching items one by one until carry limit is hit).
- Carry limit: `stat_str × 10 + sum of equipped bag carry_bonus`. If at limit: `"You can't carry any more. (N/max items)"`.
- On success: sets `owner = character`, `current_room = None`. Does NOT set `is_soulbound` (items bind on equip, not pickup).
- Broadcasts `"{name} picks up {display_name}."` to room (excluding picker).
- Errors: `"Pick up what?"` (no noun), `"You don't see that here."` (not found), `"There aren't that many of those here."` (index out of range).

**`drop`** — drop a carried, non-soulbound item onto the room floor.
- Eligible for drop: `is_equipped = False` AND `is_soulbound = False`.
- Supports `all` (iterates all carried items; skips ineligible ones with per-item messages).
- Per-item checks: if equipped → `"You'll need to unequip your {name} before dropping it."`; if soulbound → `"Your {name} is bound to you and cannot be dropped."`.
- On success: sets `current_room = character's room`, `owner = None`. Resets `is_identified = False` unless `is_unidentifiable = True`. Display name is captured before the reset so the drop message reflects the name the character knew.
- Broadcasts `"{name} drops {display_name}."` to room.
- Errors: `"Drop what?"` (no noun), `"You aren't carrying that."`, `"You don't have that many of those."`

**`equip` / `eq`** — equip a carried, unequipped item into an equipment slot.
- Does not support `all`.
- Validates: `definition.valid_slots` must not be empty.
- Slot selection: iterates `definition.valid_slots` in order; uses the first unoccupied slot. Two-handed weapons (`is_two_handed = True`) additionally require `OFF_HAND` to be free even if only `MAIN_HAND` is in `valid_slots`.
- Slot-occupied messages:
  - Single slot blocked: `"Your {Slot} slot is occupied by your {item}. Unequip it first."`
  - 2H, both blocked: `"Your Main Hand ({item}) and Off Hand ({item}) slots are both occupied. Unequip them first."`
- On success: sets `is_equipped = True`, `equipped_slot = target_slot`, `is_soulbound = True`, `soulbound_to = character`. **This is when soulbind occurs.**
- Errors: `"Equip what?"`, `"You aren't carrying that."`, `"You don't have that many of those."`, `"That item cannot be equipped."`

**`unequip` / `uneq`** — move an equipped item back to carried inventory.
- Does not support `all`.
- Checks: if `is_cursed = True` → `"Your {name} is cursed and cannot be removed."`.
- Bag check: if the item is a bag, verify that removing its `carry_bonus` would not leave the character over capacity. New limit = `stat_str × 10 + other equipped bags' bonuses`. If `(unequipped_count + 1) > new_limit` → `"You're carrying too many items to remove your {name}."`.
- On success: sets `is_equipped = False`, `equipped_slot = ''`. `is_soulbound` is NOT changed (once bound, always bound).
- Errors: `"Unequip what?"`, `"You don't have that equipped."`, `"You don't have that many of those equipped."`

**`use`** — use a consumable item.
- Eligible: carried, unequipped items where `definition.item_type = 'consumable'`.
- Does not support `all`.
- If `definition.effect is None`: `"Nothing happens."` Item is NOT consumed.
- If `effect_type = 'durability_restore'`: `"You attempt a repair, but the repair system isn't implemented yet."` Item is NOT consumed.
- Otherwise: magnitude = `random.uniform(magnitude_min, magnitude_max)`; duration = `random.uniform(duration_min, duration_max)` if both are non-null, else `None`.
- Immediate effects: `restore_vitality` / `restore_acuity` / `restore_longevity` / `shift_acuity_high` / `shift_acuity_low` apply their stat change immediately with clamping. Duration-only effects (`dot_*`, `stat_bonus`, `stat_penalty`, `curse_generic`) create only an `EffectInstance` — no immediate stat change (tick engine not yet built).
- If duration is non-null: an `EffectInstance` is created before the item is deleted.
- Item is deleted after all effects are applied.
- Sends feedback message (category `system`). Sends a `status` update message after any immediate stat change.
- Errors: `"Use what?"`, `"You aren't carrying that."`, `"You don't have that many of those."`

**`examine` / `ex`** — inspect an item, live NPC, or corpse in detail.
- Search order: (1) carried items, (2) loose room items, (3) live NPCs in room, (4) corpses in room.
- Does not support `all`.
- **Unidentified items** (`is_identified = False`): shows mystery name (or `"an unidentified {item_type}"` fallback), mystery description (or `"You can't determine anything about this item."` fallback), and `"(You cannot determine anything further about this item.)"`. If `is_unidentifiable = True`, adds `"No known method of identification will reveal its true nature."`. No stats, rarity, Mk tier, damage, or durability revealed.
- **Identified items**: shows full stat block — rarity, name, Mk tier; description; item_type and genre_tag; damage range (weapons); durability (items with `takes_durability_loss`); carry bonus (bags); primary and secondary stats (labels from `STAT_LABELS`, with title-case fallback for unlabelled keys); equipped slot; soulbind status; curse notice if `curse_identified = True`; note if not yet bound.
- **Live NPCs**: shows NPC name and description only. No stats, aggro flag, or Mk tier shown.
- **Corpses (killer)**: header `"The corpse of {name}."`, currency (via `display_for_zone()`; `"No currency."` if zero), then full identified item block for each item in `contents`. If no items, `"No items."`.
- **Corpses (non-killer)**: header and currency line shown; item list replaced with flavour denial message.
- Errors: `"Examine what?"`, `"You don't see that here."`, `"There aren't that many of those."`

**`loot [corpse] [item]`** — loot a corpse.
- Bare `loot` with no args: targets the most recently created corpse in the room, loots all items.
- `loot sword`: targets the most recent corpse, loots only items matching "sword".
- `loot 2.corpse sword`: targets the second-most-recent corpse, loots only items matching "sword".
- Permission check: only the killer (`killed_by`) may loot items. Non-killers receive `"That is not your kill; you may not loot it."` No copper transferred.
- Copper is always transferred first (before items), regardless of whether an item noun is provided. Currency transfer is not gated on the kill permission check — wait, it IS — the permission check happens before copper transfer.
- Items are looted one by one, each with a message. Carry limit applies; stops if full.
- Corpse is deleted when all `contents` items and copper have been removed (`check_corpse_empty_and_delete()`). Room broadcast: `"The corpse of {name} slowly disappears."`.
- Errors: `"There is nothing to loot here."`, `"There aren't that many corpses here."`, `"You don't see that here."` (item not in corpse), `"There aren't that many of those."` (item index out of range), `"You can't carry any more. (N/max items)"`.

**Inventory display changes (v2):** All item names use `get_display_name()`. Unidentified items show only their mystery name with no rarity column or Mk tier. A `[bound]` or `[drop]` indicator is appended to every line based on `is_soulbound`.

#### Output format

Two message types sent to client:

```json
// Text output — appended to the log pane
{"type": "output", "text": "...", "category": "room|chat|system|error"}

// Status update — updates header bar and room name
{"type": "status", "vitality": N, "acuity": N, "longevity": N,
 "room_name": "...", "area_name": "..." | null}
```

`area_name` is `null` when the room has no area; the client must handle both cases. `room_name` is always present.

Categories map to CSS classes: `room` (green), `chat` (amber), `combat` (red), `system` (muted purple), `error` (red).

**Room description output format** (`send_room_description`):
- Header line: `[ Area Name — Room Name ]` when the room belongs to an area; `[ Room Name ]` when it does not.
- If `room.area.area_description` is non-empty, it is inserted between the header and the room-specific description, with a blank line separating them. This is the shared atmospheric text written once per area.
- Rooms without an area produce identical output to the pre-Area behaviour.

#### DB helper pattern

All ORM operations are in `@database_sync_to_async` methods. The consumer coroutines `await` these methods. Key queries:

| Helper | Key select_related |
|--------|-------------------|
| `get_character(user)` | `current_room__zone`, `recall_room`, `user__profile` |
| `get_current_room()` | `zone`, `area`, all six `exit_*` rooms |
| `get_others_in_room(room)` | `user__profile` |

`move_character(destination)` uses `Character.objects.filter(pk=...).update(current_room=destination)` (targeted update, not full save) plus `RoomVisit.objects.get_or_create(...)`.

#### `format_wallet(character)` helper

Not yet called from any command, but available for future use (looting, vendors, `inventory`). Returns `display_for_zone(character.copper, zone_slug)`, using the zone of the character's current room.

### 4.4 Item generation and utilities (`item_utils.py`)

`generate_item_instance(definition, mk_tier, rarity, owner=None, room=None, gift=False)` — generates but does not save an `ItemInstance`. The caller decides when to call `.save()`.

**Parameters:**
- `definition` — an `ItemDefinition` instance
- `mk_tier` — integer; the Mk tier to generate at
- `rarity` — one of `common | uncommon | rare | epic | legendary` (never `artifact` — those are hand-authored)
- `owner` — a `Character` instance, or `None` if placing in a room
- `room` — a `Room` instance, or `None` if assigning to a character
- `gift=False` — if `True`, the item is immediately soulbound to `owner` (admin gifting flow). If `False` (default), `is_soulbound` remains `False` even if `owner` is set; the item soulbinds when the character equips it.

**Stat scaling:**

For each stat entry `{stat, base, factor}` in the definition's stat pools:
- `midpoint = base + (factor × mk_tier)`
- A random value is drawn within a rarity-specific spread around midpoint:

| Rarity | Multiplier range |
|--------|-----------------|
| common | 0.85 – 1.00 |
| uncommon | 0.90 – 1.05 |
| rare | 0.95 – 1.10 |
| epic | 1.00 – 1.15 |
| legendary | 1.05 – 1.20 |

- Result is rounded to the nearest integer.

**Secondary stat draw:**

The number of secondary stats drawn from the pool depends on rarity:

| Rarity | Secondary stats |
|--------|----------------|
| common | 0 |
| uncommon | 1 |
| rare | 2 |
| epic | 3 |
| legendary | all entries in pool |

Stats are drawn without replacement via `random.sample`. The same spread multipliers apply.

**Weapon damage:**
- `damage_midpoint = definition.scaling_base + (definition.scaling_factor × mk_tier)`, then rarity spread applied
- `damage_spread` copied directly from definition — not affected by rarity

**Soulbind:** `is_soulbound = True` and `soulbound_to = owner` only when `gift=True`. Otherwise `is_soulbound` remains `False`; soulbind occurs on equip.

**Durability helper:** `get_durability_penalty(item)` walks `item.definition.durability_table` to return the active performance penalty multiplier for an instance.

**Display helpers:**

| Function | Description |
|----------|-------------|
| `get_display_name(item)` | Returns the name to show a player. Identified → `definition.name`. Unidentified → `mystery_name` (or `"an unidentified {item_type}"` fallback). |
| `get_display_description(item)` | Returns the description to show a player. Identified → `definition.description`. Unidentified → `mystery_description` (or default fallback). |

Always use these helpers when displaying item names or descriptions to players. Never access `definition.name` or `definition.description` directly in player-facing output.

**Noun parser:** `parse_item_noun(noun_str, item_list)` — parses classic MUD noun syntax against a list of `ItemInstance` objects. Returns a `(result_code, item_or_None)` tuple: `('all', None)`, `('single', item)`, `('not_found', None)`, or `('bad_index', None)`. Matching is performed against `get_display_name(item)`.

**Corpse noun parser:** `parse_corpse_noun(noun_str, corpse_list)` — parses classic MUD noun syntax against a list of `Corpse` objects. Same `(result_code, corpse_or_None)` tuple pattern as `parse_item_noun` (no `'all'` return). Matching is case-insensitive against `corpse.display_name`.

**Loot table roller:** `generate_loot_from_table(loot_table, mk_tier)` — rolls a `LootTable` at the given Mk tier. For each entry: checks `drop_chance`, clamps `mk_tier` to `[mk_tier_min, mk_tier_max]`, picks rarity from `rarity_weights`. Returns a list of unsaved `ItemInstance` objects. Caller must set `item.corpse` and call `item.save()` on each.

**Corpse factory:** `create_corpse(npc_instance, killer)` — creates and saves a `Corpse` from a dead `NpcInstance`. Rolls copper drop (`currency_drop_min * mk_tier` to `currency_drop_max * mk_tier`). Calls `generate_loot_from_table()` if `loot_table_id` is set, then saves each item with `corpse` assigned. Returns the saved `Corpse`. **This is a synchronous function — it must be called from within a `@database_sync_to_async` wrapper when used from the consumer.**

**Slot utilities:**

| Name | Description |
|------|-------------|
| `SLOT_DISPLAY_NAMES` | Dict mapping slot keys (e.g. `'MAIN_HAND'`) to human-readable strings (e.g. `'Main Hand'`). |
| `format_slot_name(slot_str)` | Returns the human-readable slot name; falls back to `slot_str.title()` for unknown slots. |

**Stat display:**

| Name | Description |
|------|-------------|
| `STAT_LABELS` | Dict mapping core stat keys (`'str'`, `'dex'`, `'end'`, `'int'`, `'wis'`, `'per'`) to display labels (`'Strength'`, etc.). Used in `cmd_examine` for identified item stat blocks. Unknown stat keys fall back to `key.replace('_', ' ').title()`. |

### 4.5 Views and URLs

```python
# apps/shyland/urls.py
path('play/', views.game, name='game')       # → shyland/game.html, login_required
path('',      RedirectView → /shyland/play/)

# game_mvc/urls.py also registers:
path('shyland', RedirectView → /shyland/play/)   # handles missing trailing slash
```

The `game` view is a single `@login_required` function view that renders `shyland/game.html` with no context. All game state is delivered via WebSocket after page load.

### 4.6 Admin

| Model | Registered as | Notable config |
|-------|--------------|----------------|
| `Zone` | `ZoneAdmin` | Two inlines: `AreaInline` (tabular, name + slug, show_change_link) and `RoomInline` (tabular, name + coords + flag_safe); list_display: name, slug, danger_level, is_pvp_zone, is_scaled |
| `Area` | `AreaAdmin` | `RoomInlineForArea` (tabular, name + coords + flag_safe, show_change_link); list_filter on zone; `prepopulated_fields` slug from name |
| `Room` | `RoomAdmin` | `area` in list_display, list_filter, and raw_id_fields; `raw_id_fields` for all six exit FKs (prevents loading all rooms in a select); list_filter on zone/area/flag_safe/flag_pvp |
| `Character` | `CharacterAdmin` | `list_select_related = ('user__profile',)` (avoids N+1 on name property); `readonly_fields = ('wallet_display',)` (human-readable copper via `currency.display()`); `raw_id_fields` for current_room/recall_room |
| `RoomVisit` | `RoomVisitAdmin` | Basic list: character, room, visited_at |
| `EffectDefinition` | `EffectDefinitionAdmin` | list_display: name, effect_type, scales_with_mk; `prepopulated_fields` slug from name |
| `ItemDefinition` | `ItemDefinitionAdmin` | list_display: name, item_type, genre_tag, takes_durability_loss; list_filter on item_type, genre_tag; `prepopulated_fields` slug from name; fieldsets include `mystery_name` and `mystery_description` in an Identification group |
| `ItemInstance` | `ItemInstanceAdmin` | list_display adds `is_identified`, `is_unidentifiable`; list_filter adds `is_unidentifiable`; fieldsets include Identification group with `is_identified` and `is_unidentifiable`; `raw_id_fields` for owner, current_room, soulbound_to, active_curse |
| `EffectInstance` | `EffectInstanceAdmin` | list_display: definition, target, is_active, applied_at, expires_at; list_filter on is_active |

### 4.7 Seed data (`management/commands/seed_world.py`)

`python manage.py seed_world` (via `make shell`) creates:

**Zone: The Convergence**
- slug: `the-convergence`
- danger_level: `sanctuary`
- is_pvp_zone: False, is_scaled: False

**5 rooms (all flag_safe=True):**

```
                    The Northern Arcade (0, 1, 0)
                            ↕
The Western Gate ↔ The Fracture Point ↔ The Eastern Bazaar
  (-1, 0, 0)           (0, 0, 0)              (1, 0, 0)
                            ↕
                    The Southern Docks (0, -1, 0)
```

Exits are bidirectional. No up/down exits exist. **The Fracture Point is the default starting room for new characters** (PK=1 after a fresh seed). Characters are created via Django admin or the shell — no in-game creation flow exists yet.

After creating the rooms and wiring exits, the command also creates:

**Area: The Fracture Point Plaza** (slug `the-fracture-point-plaza`), zone = The Convergence, with a shared `area_description` describing the shimmering residual-Fracture atmosphere of the plaza. All 5 Convergence rooms are assigned to this area via a single `Room.objects.filter(zone=convergence).update(area=convergence_area)` call.

The command uses `get_or_create` throughout and is safe to run multiple times (idempotent on slug/name keys).

**EffectDefinitions seeded:**

| slug | effect_type | magnitude_min | magnitude_max | duration | scales_with_mk | scaling_base | scaling_factor |
|------|-------------|---------------|---------------|----------|----------------|--------------|----------------|
| `vitality-restore` | restore_vitality | 20.0 | 20.0 | instant | True | 10.0 | 5.0 |
| `acuity-shift-high` | shift_acuity_high | 15.0 | 25.0 | 15–30s | False | — | — |
| `durability-restore` | durability_restore | 25.0 | 25.0 | instant | False | — | — |

**ItemDefinitions seeded (11 total):**

| slug | item_type | genre_tag | valid_slots | dur_table |
|------|-----------|-----------|-------------|-----------|
| `iron-sword` | weapon | fantasy | MAIN_HAND | weapon |
| `combat-knife` | weapon | wasteland | MAIN_HAND, OFF_HAND | weapon |
| `pulse-pistol` | weapon (ranged) | cyber | RANGED, MAIN_HAND | ranged |
| `apprentice-staff` | weapon (2H) | fantasy | MAIN_HAND | weapon |
| `leather-vest` | armor | fantasy | CHEST | armor |
| `ballistic-jacket` | armor | wasteland | CHEST | armor |
| `copper-ring` | accessory | fantasy | RING | none |
| `satchel` | bag | fantasy | BACK | none (carry_bonus=20) |
| `healing-draught` | consumable | fantasy | — | — (effect: vitality-restore) |
| `focus-tonic` | consumable | fantasy | — | — (effect: acuity-shift-high) |
| `repair-kit` | consumable | wasteland | — | — (effect: durability-restore) |

### 4.8 Tick Engine (`management/commands/run_tick_engine.py`)

`python manage.py run_tick_engine` — a long-running Django management command that drives all time-based world events. Runs as the `ticker` Docker container.

#### Structure

```python
Command.handle()        → asyncio.run(tick_loop())
tick_loop()             → while True: process_tick(tick_number); asyncio.sleep(1)
process_tick()          → calls all three processors sequentially
```

All ORM calls use `@database_sync_to_async` (from `channels.db`). Channel layer calls are plain `async` awaits.

#### Processors

**`process_corpse_decay()`**
- Queries `Corpse.decay_at <= now`.
- For each expired corpse: captures name and room, deletes the row (Django's `CASCADE` on `ItemInstance.corpse` clears contents automatically), broadcasts the decay message to `room_{room_id}` via the channel layer.
- Logs: `"Corpse decayed: {name} in room {room_id}"`.

**`process_npc_respawn()`**
- Queries `NpcInstance` where `is_alive=False`, `respawn_at <= now`, `definition.is_unique=False`, `spawn_room is not null`.
- For each due respawn: deletes the dead row, creates a new `NpcInstance` in `spawn_room` with full vitality. No room broadcast — the NPC silently appears.
- Logs: `"NPC respawned: {name} (Mk {tier}) in room {room_id}"`.
- NPCs do not move rooms. `spawn_room` is set at creation time and is the respawn destination. `current_room` tracks live position (relevant when wandering NPCs are implemented).

**`process_effect_expiry()`**
- Queries `EffectInstance` where `is_active=True`, `expires_at <= now`, `expires_at is not null`.
- For each expired effect: marks `is_active=False`, `removed_by='timeout'`, looks up an expiry message by `effect_type`, and (if the message is non-null) sends to the player's personal group with a `status` update.
- Logs: `"Effect expired: {slug} on {char_name}"` (only when an expiry message is sent — silent types are not logged).

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

#### Logging policy

- Log meaningful activity only: decayed corpses, respawned NPCs, expired effects.
- Never log empty ticks (ticks where nothing happened).
- Never log a heartbeat.

#### Channel layer helpers

**`broadcast_to_room(room_id, text, category='room')`** — sends to `room_{room_id}` group with `type: room_message`. The consumer's existing `room_message` handler delivers it to all players in the room.

**`send_to_player(character_pk, text, category, status)`** — sends to `player_{character_pk}` group with `type: player_message`. The consumer's `player_message` handler forwards the text output and, if present, the `status` dict as a second JSON message.

### 4.9 Client template (`templates/shyland/game.html`)

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
- Command history: up-arrow walks back through history; down-arrow walks forward; at index -1 shows empty input.
- Mobile (≤600px): `grid-template-columns: 1fr`; side panel hidden by default, toggled via `☰` button (adds/removes `.open` class).

**Accessibility:**
- Output pane: `role="log"`, `aria-live="polite"`, `aria-label="Game output"`, `aria-atomic="false"`
- Combat region: `aria-live="assertive"`, `aria-atomic="true"`, visually hidden via `.sr-only`
- Input: `aria-label="Command input"`
- Side toggle: `aria-label="Toggle side panel"`
- All interactive elements are keyboard-navigable; focus returns to input after send.

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
  → get_current_room()    [DB: SELECT with select_related zone, area, all exits]
  → send_room_description()
      → get_others_in_room()  [DB: SELECT chars in room]
      → send_json {type: output, text: room desc, category: room}
      → send_json {type: status, vitality: N, acuity: N, longevity: N, room_name: ...}
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
→ self.room_group = 'room_{destination.id}'
→ group_add(new_room)
→ group_send(new_room, {type: room_message, text: "X has arrived.", exclude: channel_name})
→ get_current_room()           [DB: re-fetch destination with zone, area, all exits pre-loaded]
→ send_room_description(destination)
    → get_others_in_room(destination)   [DB]
    → send_json {type: output, ...}
    → send_json {type: status, ...}

Other players in old room receive: "X has left."
Other players in new room receive: "X has arrived."
Moving player receives: only the new room description (excluded from both broadcasts).
```

---

## 6. Key Design Decisions

These are settled. Do not revisit without deliberate consideration.

**Single `copper` BigIntegerField for all currency.** Avoids sync bugs between denomination fields. All math goes through `currency.py` functions. Display is purely presentational. `subtract()` raises `ValueError` on insufficient funds — callers must catch and send an error message to the player.

**Character name from `user.profile.gamer_tag`.** No standalone name field on Character (removed in migration `0002_remove_character_name`). Reuses the platform-wide gamer tag system. Changing your tag renames you in Shyland immediately. Always `select_related('user__profile')` before accessing `.name`.

**Items soulbound on equip, not on pickup.** Picking up an item transfers ownership but does not soulbind it — the character can still drop it. The moment an item is equipped into a slot, it becomes permanently soulbound (`is_soulbound = True`, `soulbound_to = character`). Unequipping does not unbind. Soulbound items cannot be dropped but can be sold to vendors (future system). Admin-gifted items are immediately soulbound at the time of gifting via `generate_item_instance(gift=True)`. There is no unsoulbind operation for regular players. Every code path where an item changes hands must enforce this.

**Item identification is per-character knowledge.** Items default to identified (`is_identified = True`). Builders explicitly set `is_identified = False` on items they want to be mysterious. `is_unidentifiable = True` (set by super users on specific instances) marks items that can never be identified by any in-game mechanism. Dropping an item resets `is_identified` to `False` (unless `is_unidentifiable`). All player-facing display uses `get_display_name()` and `get_display_description()` — never `definition.name` or `definition.description` directly. The identification trigger (NPC sage, Warden ability, scroll) is not yet implemented.

**ItemDefinition / ItemInstance split.** One `ItemDefinition` per item type (not per Mk tier). `ItemInstance` stores the generated stats, durability state, and equipped/owner state. This avoids duplicating template data across items. `generate_item_instance()` applies Mk tier and rarity spread at generation time and stores the rolled stats on the instance.

**Shared effect vocabulary.** Consumable effects, curse effects, and (future) combat effects all use `EffectDefinition` + `EffectInstance`. A single model pair covers all applied effects in the game rather than separate tables per effect category.

**Room Groups as the broadcast primitive.** Every player in room X is in channel group `room_{X.id}`. Movement = leave old group + join new group. No per-player fan-out needed for room-scoped events.

**Personal player groups for direct notification.** Each connected player also joins `player_{character_pk}` on connect and leaves it on disconnect. The tick engine sends effect expiry messages and status updates to this group. The consumer handles the `player_message` event type, which forwards the text to the client and optionally sends a `status` update if one is included in the event payload. Group name pattern: `player_{character_pk}`.

**Server is the authority; client is a dumb terminal.** Client sends text strings. Server sends JSON output. No game state is trusted from the client.

**Redis presence for `who`, not a DB flag.** Online players are tracked via `shyland:online:{character_pk}` keys in Redis (90-second TTL, 60-second heartbeat refresh). The value is the character's display name, so `who` needs no DB call — it scans keys and fetches values in two Redis round-trips. A separate `aioredis` client is created per consumer connection, independent of the Channels channel layer. The key prefix `shyland:online:` namespaces presence away from all other Redis data in the shared instance.

**`@database_sync_to_async` pattern throughout.** Django ORM is synchronous. Every DB operation in the consumer is wrapped. Never call ORM methods directly in async consumer methods — this raises `SynchronousOnlyOperation` and crashes the connection. Accessing FK descriptor objects (e.g., `room.exit_north`) in async context is also unsafe unless the object was prefetched via `select_related`. `Room.exits()` uses `exit_{direction}_id` (an integer column, always available) to avoid this.

**Three bars: Vitality / Acuity / Longevity.** All three are in the data model from day one. Currently only current values are sent to the client. Acuity is a dynamic spectrum — being too high or too low is bad for different reasons; it is not a simple 0–100 good/bad scale. Each origin has a baseline and an optimal band (`acuity_baseline`, `acuity_band_low`, `acuity_band_high`).

**`make build` required after every code change.** Source is baked into the Docker image at build time. `make restart` picks up no Python or template changes.

**`make makemigrations` auto-syncs migration files.** Django generates migration files inside the container's ephemeral filesystem. The Makefile copies them back to `django/src/apps/*/migrations/` after generation so they survive the next `make build`.

---

## 7. What Is Not Yet Built

Future sessions should check this list before assuming a system exists.

- Combat system (tick engine is implemented; combat loop is not yet built)
- In-game character creation flow (admin creation works)
- Item identification trigger — NPC sage, Warden ability, and identification scrolls (fields and display logic are in place; trigger mechanism deferred)
- Durability degradation on equip/combat use (model field exists; no tick logic yet)
- `durability_restore` consumable effect (placeholder response implemented; full repair system deferred)
- Duration-based effect ticking — expiry implemented in tick engine; DoT/HoT stat application deferred to combat brief
- Loot system — loot table models and loot command implemented; NPC AI deferred
- NPC aggro, AI behavior, and wandering
- Monitoring container — future work; tracks health of all containers
- `examine` on NPCs — dialogue tree integration (description shown; no dialogue yet)
- Super user in-game item gifting flow
- `brief` toggle (first visit shows full description; repeat visits show `brief_description`)
- Minimap and fog-of-war rendering in the client (`RoomVisit` records exist but are not rendered)
- Party system
- Guild system
- Quest system
- NPC system and dialogue
- Dungeon instancing
- PvP flagging, entry confirmation, and bounty system
- The Wastelands (`is_scaled=True`) level-scaling logic
- Admin in-game teleport commands
- Super user item gifting (in-game flow)
- All chat channels except `say` and `who`: `yell`, `tell`, `party`, `guild`, `zone`, `general`, `emote`
- Zone content beyond The Convergence (5 starter rooms)

---

## 8. Known Issues / Flags for Future Sessions

**Status message omits bar maximums.** `send_room_description()` sends `vitality`, `acuity`, and `longevity` current values but not their maximums (`vitality_max`, `longevity_max`) or Acuity band bounds (`acuity_band_low`, `acuity_band_high`). The client cannot render proportional bars. Add these to the `status` message when the client UI is extended.

**`format_wallet()` is wired but unused.** The helper exists in the consumer and is ready for vendor transactions and loot commands. It accesses `character.current_room.zone.slug` — ensure `current_room__zone` is in `select_related` when calling it (already is in `get_character()`).

**Side panel is a stub.** `game.html` shows "Session 1 — world coming soon." in the side panel. Future sessions will populate it with minimap, character stats, or party info.

**`create_corpse()` is synchronous.** It is a sync function in `item_utils.py` — it must be called from within a `@database_sync_to_async` wrapper in the consumer when combat is implemented.

**DoT and HoT effects expire correctly but do not tick.** `EffectInstance` rows are marked inactive and the player is notified when `expires_at` is reached, but per-tick stat changes are not applied. A `dot_vitality` effect will expire without having dealt any damage. Full DoT/HoT application requires the combat brief.
