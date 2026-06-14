# Shyland — Claude Code Kickoff Brief
**Paste this entire document as the first message in a Claude Code session.**

---

## What We Are Building

Shyland is a free, web-based Multi-User Dungeon (MUD). Think classic telnet MUDs modernized: text is the primary interface, with supplementary visual elements (minimap, portraits, status bars). It runs in the browser, responsive down to phone size.

The setting is a genre-collision world called Shyland where dimensional rifts have pulled fragments of different realities together. A cyberpunk street samurai can appear in a woodland adventure zone. The anachronism is intentional and central to the game's identity.

This is a passion project. There is no monetization, no premium currency, no real-money transactions of any kind. It is free to play, full stop.

---

## The Existing Stack

The infrastructure is already built. The repo is at:
**https://github.com/KnightOfNight/games-mvc**

It is a Docker-based platform for hosting Django games. The four containers are:

| Container | Image | Purpose |
|---|---|---|
| `nginx` | nginx:alpine | SSL termination, WebSocket proxy at `/ws/` |
| `django` | python:3.12-slim + Daphne | ASGI server running Django 5 + Channels |
| `postgres` | postgres:16-alpine | Primary database, persistent volume |
| `redis` | redis:7-alpine | Django Channels layer for WebSocket routing |

**Key packages already installed:**
- `Django` — web framework
- `channels` + `channels-redis` + `daphne` — WebSocket/ASGI support (official Django projects)
- `djangorestframework` — REST API support
- `psycopg2-binary` — PostgreSQL driver
- `redis` — Python Redis client
- `django-environ` — reads `.env` into Django settings
- `whitenoise` — static file serving

**Key files:**
- `docker-compose.yml` — defines all four containers
- `django/src/game_mvc/asgi.py` — ASGI router, wires HTTP → Django and `/ws/` → Channels with `AuthMiddlewareStack`
- `django/src/game_mvc/routing.py` — central registry for WebSocket URL patterns
- `django/src/game_mvc/urls.py` — HTTP URL config (admin, auth, API auth already wired)
- `django/src/game_mvc/settings/base.py` — reads all config from env; PostgreSQL + Redis channel layer configured
- `django/src/game_mvc/settings/production.py` — DEBUG=False, locked ALLOWED_HOSTS, secure cookies
- `django/src/game_mvc/settings/local.py` — DEBUG=True, InMemoryChannelLayer for local dev without Redis
- `django/src/templates/base.html` — minimal base template with `{% block content %}`
- `Makefile` — `make new-app NAME=<name>`, `make migrate`, `make shell`, `make logs`, etc.

**WebSocket connections already have the authenticated Django user available** via `AuthMiddlewareStack` in `asgi.py`. Django's auth system (login/logout/password) is already wired.

**`make new-app NAME=shyland`** is the first command to run. It scaffolds the Shyland Django app at `django/src/apps/shyland/`.

---

## Session 1 Goals

Build the minimum viable game loop: a player can log in, connect via WebSocket, enter a room, see its description, and move between rooms. Nothing more.

### Step 1 — Scaffold the app
```bash
make new-app NAME=shyland
```

Then wire it up:
- Add `'apps.shyland'` to `INSTALLED_APPS` in `django/src/game_mvc/settings/base.py`
- Add URL include to `django/src/game_mvc/urls.py`
- Add WebSocket path to `django/src/game_mvc/routing.py`

### Step 2 — Build the core data models

File: `django/src/apps/shyland/models.py`

Build these models in order. Run `make makemigrations APP=shyland && make migrate` after.

**Zone**
```
- id (auto PK)
- name (str, max 100)
- slug (str, unique, used in routing and admin)
- genre_tone (str, max 100) — e.g. "Classic fantasy wilderness"
- danger_level (str, choices: beginner / intermediate / advanced / sanctuary / all_levels)
- is_pvp_zone (bool, default False)
- is_scaled (bool, default False) — True for The Wastelands
- description (text)
```

**Room**
```
- id (auto PK)
- zone (FK → Zone)
- name (str, max 200) — short name shown in header
- description (text) — long description, shown on look / first visit
- brief_description (str, max 500) — one-liner shown on repeat visits
- coord_x, coord_y, coord_z (int, default 0) — position within zone grid for minimap
- exit_north, exit_south, exit_east, exit_west (nullable FK → Room self)
- exit_up, exit_down (nullable FK → Room self)
- flag_safe (bool, default False)
- flag_pvp (bool, default False)
- flag_dark (bool, default False)
- flag_indoors (bool, default False)
- flag_water (bool, default False)
- flag_no_recall (bool, default False)
- flag_radiation (bool, default False)
- flag_holy (bool, default False)
- flag_magic_dead (bool, default False)
- flag_scaled (bool, default False) — for Wastelands rooms
```

**Character**
```
- id (auto PK)
- user (OneToOne FK → Django User)
- name (str, max 50, unique)
- origin (str, choices: highborn / feral / streetborn / irradiated / undying / machinekind / voidtouched)
- archetype (str, choices: blade / bulwark / shade / conduit / warden / gunner / machinist)
- level (int, default 1)
- xp (int, default 0)
- current_room (FK → Room, nullable, on_delete SET_NULL)
- recall_room (FK → Room, nullable, on_delete SET_NULL, related_name recall_room)

# Primary stats
- stat_str (int, default 10)
- stat_dex (int, default 10)
- stat_end (int, default 10)
- stat_int (int, default 10)
- stat_wis (int, default 10)
- stat_per (int, default 10)

# The Three Bars — current and max
- vitality_current (int, default 100)
- vitality_max (int, default 100)
- acuity_current (int, default 50)   # dynamic — not a 0–100 good/bad scale
- acuity_baseline (int, default 50)  # set by Origin at character creation
- acuity_band_low (int, default 35)  # lower bound of optimal band
- acuity_band_high (int, default 65) # upper bound of optimal band
- longevity_current (int, default 100)
- longevity_max (int, default 100)

# Currency
- shards (int, default 0)
- marks (int, default 0)
- crowns (int, default 0)

# Flags
- is_hardcore (bool, default False) — permadeath mode
- is_dead (bool, default False)
- created_at (datetime, auto)
- last_seen (datetime, auto)
```

**RoomVisit** (fog of war tracking)
```
- character (FK → Character)
- room (FK → Room)
- visited_at (datetime, auto)
- unique_together: (character, room)
```

### Step 3 — Seed data

Create a management command `django/src/apps/shyland/management/commands/seed_world.py` that creates:

- The Convergence zone (sanctuary, safe, the starting hub)
- 5 rooms in The Convergence in a simple cross layout:
  - Center: "The Fracture Point" (the main hub room, flag_safe=True)
  - North: "The Northern Arcade"
  - South: "The Southern Docks"
  - East: "The Eastern Bazaar"
  - West: "The Western Gate"
- Wire all exits correctly (center↔north, center↔south, etc.)

All new characters should start in "The Fracture Point".

### Step 4 — The WebSocket Consumer

File: `django/src/apps/shyland/consumers.py`

Build a `SkylandConsumer(AsyncJsonWebsocketConsumer)` that:

1. On `connect`: authenticate user, load or reject if no character, add to room's Channel Group (`room_{room_id}`), send the room description
2. On `disconnect`: remove from room Group, update `character.last_seen`
3. On `receive`: parse the text command, dispatch to a handler
4. Command handlers for this session:
   - `look` — send room name, description, exit list, list of other players present
   - `north`, `south`, `east`, `west`, `up`, `down` (and single-letter abbreviations) — move to adjacent room if exit exists; update character's `current_room`; remove from old room Group, add to new room Group; send new room description; notify old room "X has left." and new room "X has arrived."
   - `say <text>` — broadcast to current room Group: `[say] CharName: text`
   - `who` — send list of all online players (query characters with active WebSocket sessions)
   - unknown command — send `"Unknown command. Type 'look' to see your surroundings."`

**Room Group naming:** `room_{room_id}` — all consumers in the same room join this group.

**Message format to client** (JSON):
```json
{
  "type": "output",
  "text": "The text to display",
  "category": "room" | "combat" | "chat" | "system" | "error"
}
```

The category drives ARIA live region urgency on the client:
- `combat` → `aria-live="assertive"`
- everything else → `aria-live="polite"`

### Step 5 — The Client

File: `django/src/apps/shyland/templates/shyland/game.html`

A single HTML page that extends `base.html`. Build it with vanilla JS — no framework dependency for this session.

Layout (responsive, CSS grid):
```
┌─────────────────────────────────────────────────┐
│  [Room Name]          [V:100 A:50 L:100]        │
├──────────────────────────────┬──────────────────┤
│                              │                  │
│   OUTPUT PANE                │   SIDE PANEL     │
│   aria-live="polite"         │   (stub for now) │
│   (scrolling text log)       │                  │
│                              │                  │
├──────────────────────────────┴──────────────────┤
│  > INPUT LINE                        [SEND]      │
└─────────────────────────────────────────────────┘
```

JS requirements:
- Open WebSocket to `wss://<host>/ws/shyland/`
- On message: append text to output pane, auto-scroll to bottom
- Combat messages use `aria-live="assertive"` on a separate visually-hidden div
- Input: send on Enter key or SEND button click
- Command history: up/down arrow cycles through previous commands
- On phone: side panel hidden by default, accessible via a tab/toggle

**Accessibility requirements (non-negotiable):**
- Output pane has `aria-live="polite"` and `aria-label="Game output"`
- Input has `aria-label="Command input"`
- All interactive elements keyboard-navigable
- Focus management: after sending a command, focus returns to input

### Step 6 — Wire everything together

- Add a view in `django/src/apps/shyland/views.py` that renders `game.html` (login required)
- Add URL in `django/src/apps/shyland/urls.py`: `path('play/', views.game, name='game')`
- Add WebSocket URL in `routing.py`: `path('ws/shyland/', consumers.SkylandConsumer.as_asgi())`
- Add login redirect in settings so unauthenticated users go to `/accounts/login/`

### Step 7 — Run and verify

```bash
make build && make restart
make migrate
make shell
# In shell: from apps.shyland.management.commands.seed_world import Command; Command().handle()
```

Visit `https://localhost:40443/play/` in two browser tabs logged in as different users. Verify:
- Both see The Fracture Point description on connect
- Moving north in tab 1 shows the new room; tab 2 sees "X has left."
- `say hello` in one tab appears in both tabs if in same room
- `who` lists online players

---

## Architecture Principles — Enforce These From Day One

**Server is the authority.** The client is a dumb terminal. It sends text commands and renders text output. It never sends game state — only player intent.

**All game logic in Python.** No game decisions in JavaScript. JS handles rendering and input only.

**Room Groups are the broadcast primitive.** Everyone in Room X is in Channel Group `room_{room_id}`. Use `channel_layer.group_send()` for all room-scoped messages.

**Never trust the client for:** item quantities, currency amounts, stat values, position, soulbind status. All validated server-side on every operation.

**Soulbind is forever.** Every item that exists will eventually have a `bound_to` FK. When set, it cannot be cleared by any player action — only super user gift flow sets it on gift.

**Three bars, not one.** Characters have Vitality (body), Acuity (mind — dynamic, no perfect value), and Longevity (slow burn). All three must be in the data model from day one even if only Vitality is active in v1 gameplay.

**Acuity is not a sanity meter.** It is a dynamic spectrum. Being too high is as bad as being too low. Each Origin has a baseline and an optimal band. Do not model it as "0 = bad, 100 = good."

**Screen reader support is not optional.** ARIA live regions on the output pane must be in the first working client. This is a text game — screen reader support is nearly free and must not be retrofitted later.

---

## Key Design Decisions — Do Not Re-Litigate These

| Decision | Detail |
|---|---|
| Items soulbound on pickup | No player-to-player item trading ever. Items cannot leave the character who picked them up. |
| Currency freely transferable | Players can give each other Shards/Marks/Crowns. |
| Super user gifting | Staff can gift items; items become soulbound to recipient immediately. |
| No off-body storage | No banks, no stash, no mule accounts. Carry what you carry. STR governs carry weight. |
| No hard level cap | Progression is infinite. Soft cap at content frontier. The Wastelands zone always scales to player level. |
| Mk item system | Items named "Sword Mk 3" — one base item type, scaled by Mark tier (Mk 1 = levels 1–10, Mk 2 = 11–20, etc., Mk 11+ = Wastelands/beyond). |
| No housing | Deferred to future version. |
| No mounts | Deferred to future version. Super user teleport covers testing. |
| No seasonal content | Ever. World stays fresh through content updates only. |
| No monetization | Ever. Free to play, full stop. |
| English only | v1 is English only. |
| Single visual theme | No colorblind or high-contrast mode in v1. |
| Fixed combat ticks | No per-player tick rate adjustment. Same speed for everyone. |
| PvE default, PvP opt-in | PvP only in rooms/zones flagged `flag_pvp=True`. Entering requires confirmation. |
| Logout persistence | Character stays in world for 60 seconds after logout (killable in PvP zones), then fades. |

---

## The Three Bars — Quick Reference

**Vitality** — the body right now
- Low → move slower, hit softer, take more damage
- Zero → Dying state (30s ally revive window) → Dead

**Acuity** — the mind's dynamic state (not a sanity meter)
- Each Origin has a `baseline` and an optimal `band_low`/`band_high`
- Too LOW: spells fizzle, aim drifts, situational awareness drops, combat log degrades
- Too HIGH: hyper-focus, single-target bonus but flanking enemies undetected
- Shifts due to: eldritch damage, zone effects, stress, consumables, Warden abilities
- Drifts back toward `acuity_baseline` over time when no forces act on it
- Players can deliberately manipulate it (focus potions, etc.) — with tradeoffs

**Longevity** — the slow burn
- Controls stamina duration, DoT/HoT durations, sustained effect windows
- Recovers slowly. Mismanaging it over a long dungeon run is a real problem.
- Your own DoTs last longer at high Longevity. Enemy DoTs on you expire faster at high Longevity.

---

## Zones Reference (v1)

| ID | Name | Genre | Danger | Notes |
|---|---|---|---|---|
| Z01 | The Verdant Reach | Fantasy wilderness | Beginner | Starting zone content |
| Z02 | Ashenveil Cathedral | Dark gothic horror | Intermediate | |
| Z03 | The Neon Sprawl | Cyberpunk megacity | Intermediate | |
| Z04 | The Blasted Flats | Post-apocalyptic | Advanced | |
| Z05 | The Convergence | All genres | Sanctuary | Starting room. Hub. PvP disabled. |
| Z06 | The Iron Deeps | Steampunk underground | Advanced | |
| Z07 | The Pale Shore | Cosmic horror | Endgame | Acuity-disrupting zone |
| Z08 | The Wastelands | Post-apocalyptic | All levels | `is_scaled=True`. Always level-appropriate. |

---

## Archetypes Reference

| Archetype | Role | Primary Stats |
|---|---|---|
| Blade | Melee DPS | STR, DEX |
| Bulwark | Tank | STR, END |
| Shade | Stealth / burst | DEX, INT |
| Conduit | Magic/tech ranged DPS | INT, WIS |
| Warden | Healer / Acuity manager | WIS, END |
| Gunner | Ranged DPS | DEX, PER |
| Machinist | Pet / construct / turret | INT, DEX |

---

## Origins Reference

| Origin | Flavor | Key Trait | Acuity Baseline |
|---|---|---|---|
| Highborn | Fantasy noble | +10% quest XP | Mid (50) |
| Feral | Wilderness/tribal | +15% move, foraging | Mid-low (45) |
| Streetborn | Cyberpunk | Hacking -10% energy | Mid (50) |
| Irradiated | Post-apocalyptic | Rad resistance | Mid-low (42) |
| Undying | Gothic/undead | Reduced death penalty | Low (35) |
| Machinekind | Steampunk construct | No poison/no magic heal | Mid-high (55) |
| Voidtouched | Cosmic horror | Eldritch bonus; wide Acuity band | Low (30), wide band |

---

## Full GDD Location

The full Game Design Document (v2.0) is at:
`Shyland_GDD_v2.md` (in the same directory as this kickoff brief)

It covers: World Model, Character System, Three Bars system, Combat, Economy, Social, Quests, Technical Architecture, Admin Tools, and Future Systems in full detail.

---

## What Comes After Session 1

Session 2 will add:
- Character creation flow (origin + archetype + name + portrait selection)
- The `brief` toggle (first visit shows long description, repeat visits show brief)
- Fog of war — minimap rendering based on `RoomVisit` records
- The `inventory` command stub

Session 3 will begin the combat engine — the tick loop, auto-attack, hit resolution.

But first: get a player moving between rooms.

---

*Kickoff Brief v1.0 — Shyland*
*Generated from GDD v2.0 and games-mvc stack review.*
