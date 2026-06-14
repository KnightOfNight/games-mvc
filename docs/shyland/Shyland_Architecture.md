# Shyland Architecture

> Authoritative technical reference as of commit 391ae1f.  
> Describes what is built. For design intent see `Shyland_GDD_v3.md`.

---

## 1. Overview

Shyland is a free, browser-based Multi-User Dungeon. The primary interface is text: players connect via WebSocket, type commands, and read descriptive output. A minimal visual chrome (status bar, side panel) supplements the text pane. As of this commit, the game loop is complete: a player can connect, move between rooms, chat, and query who is online. Currency storage and the display utility are implemented. Combat, items, character creation, and all other game systems have not yet been built — see [Section 7](#7-what-is-not-yet-built).

---

## 2. Infrastructure

### 2.1 Docker Compose stack

```
docker-compose.yml defines four containers:

  nginx      nginx:alpine          SSL termination; WebSocket proxy at /ws/
  django     python:3.12-slim      Daphne ASGI server; Django 5 + Channels
  postgres   postgres:16-alpine    Primary database; persistent volume pgdata
  redis      redis:7-alpine        Django Channels layer for WebSocket routing
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

Only `nginx` exposes a host port. `django`, `postgres`, and `redis` are internal to the Docker network. `postgres` has a healthcheck; `django` depends on it being healthy before starting.

### 2.2 Makefile workflow

| Target | What it does |
|--------|-------------|
| `make setup` | First-time: wizard + build + start |
| `make build` | Rebuild Docker image and recreate containers — **required after any Python/template/settings change** (source is baked into the image, not volume-mounted) |
| `make start` / `make stop` / `make restart` | Container lifecycle |
| `make logs` | Follow all container logs |
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

#### Room

```
zone              FK → Zone (CASCADE)
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
4. Accepts the connection.
5. If `current_room_id` is `None`: sends error, returns (connection stays open but idle).
6. Calls `get_current_room()` (full select_related on all exits).
7. Joins `room_{room.id}` channel group.
8. Sends room description + status message to client.

**`disconnect(code)`**
1. Leaves room channel group if joined.
2. Updates `character.last_seen` via `touch_last_seen()`.

#### Command dispatch (`receive_json`)

Client sends: `{"text": "<raw command string>"}`

The text is stripped, split on whitespace into `verb` + optional `args`. Dispatch:

| verb | handler |
|------|---------|
| `north` / `n` / `south` / `s` / `east` / `e` / `west` / `w` / `up` / `u` / `down` / `d` | `cmd_move(verb)` |
| `look` / `l` | `cmd_look()` |
| `say` | `cmd_say(args)` |
| `who` | `cmd_who()` |
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
8. Sends room description for destination.

**`say <text>`** — broadcasts `[say] {name}: {text}` with category `chat` to current room group (all players in room, including the sender, receive it).

**`who`** — queries all `Character` records (not filtered to active connections), returns names list. **Known limitation: shows all characters, not just online players.**

#### Output format

Two message types sent to client:

```json
// Text output — appended to the log pane
{"type": "output", "text": "...", "category": "room|chat|system|error"}

// Status update — updates header bar and room name
{"type": "status", "vitality": N, "acuity": N, "longevity": N, "room_name": "..."}
```

Categories map to CSS classes: `room` (green), `chat` (amber), `combat` (red), `system` (muted purple), `error` (red).

#### DB helper pattern

All ORM operations are in `@database_sync_to_async` methods. The consumer coroutines `await` these methods. Key queries:

| Helper | Key select_related |
|--------|-------------------|
| `get_character(user)` | `current_room__zone`, `recall_room`, `user__profile` |
| `get_current_room()` | `zone`, all six `exit_*` rooms |
| `get_others_in_room(room)` | `user__profile` |
| `get_online_names()` | `user__profile` |

`move_character(destination)` uses `Character.objects.filter(pk=...).update(current_room=destination)` (targeted update, not full save) plus `RoomVisit.objects.get_or_create(...)`.

#### `format_wallet(character)` helper

Not yet called from any command, but available for future use (looting, vendors, `inventory`). Returns `display_for_zone(character.copper, zone_slug)`, using the zone of the character's current room.

### 4.4 Views and URLs

```python
# apps/shyland/urls.py
path('play/', views.game, name='game')       # → shyland/game.html, login_required
path('',      RedirectView → /shyland/play/)

# game_mvc/urls.py also registers:
path('shyland', RedirectView → /shyland/play/)   # handles missing trailing slash
```

The `game` view is a single `@login_required` function view that renders `shyland/game.html` with no context. All game state is delivered via WebSocket after page load.

### 4.5 Admin

| Model | Registered as | Notable config |
|-------|--------------|----------------|
| `Zone` | `ZoneAdmin` | `RoomInline` (tabular, shows name + coords + flag_safe); list_display: name, slug, danger_level, is_pvp_zone, is_scaled |
| `Room` | `RoomAdmin` | `raw_id_fields` for all six exit FKs (prevents loading all rooms in a select); list_filter on zone/flag_safe/flag_pvp |
| `Character` | `CharacterAdmin` | `list_select_related = ('user__profile',)` (avoids N+1 on name property); `readonly_fields = ('wallet_display',)` (human-readable copper via `currency.display()`); `raw_id_fields` for current_room/recall_room |
| `RoomVisit` | `RoomVisitAdmin` | Basic list: character, room, visited_at |

### 4.6 Seed data (`management/commands/seed_world.py`)

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

The command uses `get_or_create` throughout and is safe to run multiple times (idempotent on slug/name keys).

### 4.7 Client template (`templates/shyland/game.html`)

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
  → get_current_room()    [DB: SELECT with select_related all exits]
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

**Items soulbound on pickup.** No player-to-player item trading ever. Items cannot leave the character who picked them up. Super user gifting flow sets soulbind on write. (Items not yet implemented.)

**Room Groups as the broadcast primitive.** Every player in room X is in channel group `room_{X.id}`. Movement = leave old group + join new group. No per-player fan-out needed for room-scoped events.

**Server is the authority; client is a dumb terminal.** Client sends text strings. Server sends JSON output. No game state is trusted from the client.

**`@database_sync_to_async` pattern throughout.** Django ORM is synchronous. Every DB operation in the consumer is wrapped. Never call ORM methods directly in async consumer methods — this raises `SynchronousOnlyOperation` and crashes the connection. Accessing FK descriptor objects (e.g., `room.exit_north`) in async context is also unsafe unless the object was prefetched via `select_related`. `Room.exits()` uses `exit_{direction}_id` (an integer column, always available) to avoid this.

**Three bars: Vitality / Acuity / Longevity.** All three are in the data model from day one. Currently only current values are sent to the client. Acuity is a dynamic spectrum — being too high or too low is bad for different reasons; it is not a simple 0–100 good/bad scale. Each origin has a baseline and an optimal band (`acuity_baseline`, `acuity_band_low`, `acuity_band_high`).

**`make build` required after every code change.** Source is baked into the Docker image at build time. `make restart` picks up no Python or template changes.

**`make makemigrations` auto-syncs migration files.** Django generates migration files inside the container's ephemeral filesystem. The Makefile copies them back to `django/src/apps/*/migrations/` after generation so they survive the next `make build`.

---

## 7. What Is Not Yet Built

Future sessions should check this list before assuming a system exists.

- Tick engine and combat system (including the fixed 1-second tick / 3-tick combat round)
- Item model, loot system, and soulbind logic
- In-game character creation flow (admin creation works)
- `inventory` command
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

**`who` shows all characters, not just online players.** `get_online_names()` queries all `Character` records. A proper presence mechanism (Redis key per active channel name, or a `is_online` flag updated on connect/disconnect) is needed before `who` is accurate.

**Status message omits bar maximums.** `send_room_description()` sends `vitality`, `acuity`, and `longevity` current values but not their maximums (`vitality_max`, `longevity_max`) or Acuity band bounds (`acuity_band_low`, `acuity_band_high`). The client cannot render proportional bars. Add these to the `status` message when the client UI is extended.

**`format_wallet()` is wired but unused.** The helper exists in the consumer and is ready for `inventory`, vendor transactions, and loot commands. It accesses `character.current_room.zone.slug` — ensure `current_room__zone` is in `select_related` when calling it (already is in `get_character()`).

**Side panel is a stub.** `game.html` shows "Session 1 — world coming soon." in the side panel. Future sessions will populate it with minimap, character stats, or party info.
