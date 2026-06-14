# Shyland — Claude Code Brief: Create Architecture Document
**Session goal: write `docs/shyland/Shyland_Architecture.md` based on the actual codebase**

---

## Your Task

Read the existing Shyland source code and produce `docs/shyland/Shyland_Architecture.md`.

This document is the authoritative technical reference for Shyland. It describes what is actually built — not what was planned. Future Claude Code sessions will read it to orient themselves before touching code. Write it as if briefing a competent Django developer who has never seen this project.

---

## Files to Read First

Before writing anything, read all of these:

```
django/src/apps/shyland/models.py
django/src/apps/shyland/consumers.py
django/src/apps/shyland/currency.py
django/src/apps/shyland/admin.py
django/src/apps/shyland/views.py
django/src/apps/shyland/urls.py
django/src/apps/shyland/templates/shyland/game.html
django/src/apps/shyland/management/commands/seed_world.py
django/src/apps/shyland/migrations/0001_initial.py
django/src/apps/shyland/migrations/0002_remove_character_name.py
django/src/game_mvc/routing.py
django/src/game_mvc/settings/base.py
django/src/game_mvc/asgi.py
docker-compose.yml
```

Also read `docs/shyland/Shyland_GDD_v3.md` for design context, but the architecture doc must reflect the code as it exists, not the GDD aspirationally.

---

## Document Structure to Produce

Write `docs/shyland/Shyland_Architecture.md` with the following sections. Fill each section from what you actually read in the code — do not invent or speculate.

---

### 1. Overview

One paragraph: what Shyland is, what it does right now (as of this commit), and what the next major systems to be built are.

---

### 2. Infrastructure

Describe the Docker Compose stack as it actually runs. Cover all four containers, their images, how they communicate, what ports are exposed, and how the nginx → daphne → redis/postgres flow works. Include the actual architecture diagram from the README (it is accurate).

Note the `make` workflow — key targets a developer needs to know: `setup`, `build`, `start`, `stop`, `restart`, `logs`, `migrate`, `makemigrations`, `shell`, `createsuperuser`, `new-app`.

Note the `makemigrations` enhancement: it now auto-syncs generated migration files back to the local filesystem from the container.

---

### 3. Django Project Structure

Describe `django/src/game_mvc/` — the project package. Cover:
- `asgi.py` — how HTTP and WebSocket traffic is routed, the role of `AuthMiddlewareStack`
- `routing.py` — the WebSocket URL registry, what is currently registered
- `urls.py` — what HTTP endpoints exist
- `settings/` — the three settings files and when each is used
- The shared `User` + `profile` pattern (the `user__profile` select_related appears throughout consumers.py — note that character name comes from `user.profile` rather than a standalone field on Character; this was migration `0002_remove_character_name.py`)

---

### 4. The Shyland App (`apps/shyland/`)

#### 4.1 Models

Document every model with its fields, relationships, and any notable methods. Ground this in `models.py` as read. Include:

- **Zone** — fields, what `is_scaled` means (Wastelands), what `danger_level` choices are
- **Room** — all fields including all `flag_*` booleans and all `exit_*` self-FKs; note the `exits()` method called in consumers.py
- **Character** — all fields; critically note that `name` is NOT a field (removed in migration 0002 — comes from `user.profile`); all three bar fields (vitality, acuity, longevity — current and max); `copper` BigIntegerField; origin/archetype choices
- **RoomVisit** — fog of war tracking, unique_together constraint

#### 4.2 Currency System (`currency.py`)

Document the escalating-multiplier tier system precisely:

```
Copper  = 1
Silver  = 10       (×10 from copper)
Gold    = 1,000    (×100 from silver)
Platinum = 1,000,000 (×1,000 from gold)
```

All currency stored as a single `BigIntegerField` named `copper` on Character. Document the public API: `to_copper()`, `from_copper()`, `display()`, `add()`, `subtract()`, `can_afford()`, `display_for_zone()`. Document `ZONE_CURRENCY_DISPLAY` and which zones have aliases so far.

#### 4.3 WebSocket Consumer (`consumers.py`)

Document `SkylandConsumer(AsyncJsonWebsocketConsumer)` in detail:

**Connection lifecycle:**
- `connect()` — auth check, character load, room group join, initial room description sent
- `disconnect()` — group leave, `last_seen` updated

**Command dispatch (`receive_json`):**
- Input format: `{"text": "<raw command string>"}`
- Parsed as `verb [args]`
- Dispatch table: directions → `cmd_move`, `look`/`l` → `cmd_look`, `say` → `cmd_say`, `who` → `cmd_who`, else → unknown command message

**Commands implemented:**
- `look` / `l` — sends room description to caller
- `north`/`n`, `south`/`s`, `east`/`e`, `west`/`w`, `up`/`u`, `down`/`d` — move to adjacent room
- `say <text>` — broadcast to room group
- `who` — list all Character records (note: this is all characters, not just online ones — flag for future improvement)

**Room Groups:** Named `room_{room_id}`. All consumers in the same room join the same group. Movement = leave old group, join new group. Room-scoped broadcasts use `channel_layer.group_send()` with `type: room_message`.

**Exclude pattern:** Move messages pass `exclude: self.channel_name` so the moving player doesn't see their own departure/arrival messages.

**Output format to client:**
```json
{"type": "output", "text": "...", "category": "room|chat|system|error"}
{"type": "status", "vitality": N, "acuity": N, "longevity": N, "room_name": "..."}
```

**DB helper pattern:** All ORM calls are wrapped in `@database_sync_to_async` methods. The consumer itself is fully async. Key queries use `select_related` to avoid N+1 problems.

#### 4.4 Views and URLs

Document what HTTP routes exist, what the game view renders, and any login requirements.

#### 4.5 Admin

Document the registered models and any notable customisations (wallet display, RoomInline on Zone, raw_id_fields on exits).

#### 4.6 Seed Data (`management/commands/seed_world.py`)

Document what `make shell` + `python manage.py seed_world` creates: which zones, which rooms, how the exits are wired, and which room is the default starting room for new characters.

#### 4.7 Templates

Document `game.html` — the layout, what panels exist, how the WebSocket is opened, what JS handles, what ARIA attributes are present, how the status bar is updated, command history behaviour.

---

### 5. Data Flow Diagrams

Write two short ASCII flow diagrams:

**Player connects:**
```
Browser → nginx (SSL) → Daphne (ASGI) → AuthMiddlewareStack
→ SkylandConsumer.connect()
→ get_character() [DB]
→ group_add(room_{id})
→ send_room_description() → client receives {type: output} + {type: status}
```

**Player moves (e.g. "north"):**
```
Client sends {"text": "north"}
→ receive_json() → cmd_move("north")
→ get_current_room() [DB]
→ group_send(old_room, "X has left.") [excludes mover]
→ group_discard(old_room)
→ move_character(destination) [DB: update + RoomVisit.get_or_create]
→ group_add(new_room)
→ group_send(new_room, "X has arrived.") [excludes mover]
→ send_room_description(destination)
```

---

### 6. Key Design Decisions (with rationale)

Document these as settled decisions that should not be revisited without good reason:

- **Single `copper` BigIntegerField for all currency** — avoids sync bugs between tiers; display is purely presentational via `currency.py`
- **Items soulbound on pickup** — no player-to-player item trading; super user gifting sets soulbind on write
- **Character name from `user.profile`** — reuses existing gamer tag system; removed standalone `name` field in migration 0002
- **Room Groups as the broadcast primitive** — every player in a room is in `room_{id}`; move = group swap; no per-player fan-out needed
- **All game logic server-side** — client is a dumb terminal; sends text commands, receives JSON output
- **`@database_sync_to_async` pattern** — ORM is synchronous; all DB calls in consumer are wrapped; keeps consumer fully async
- **Three bars: Vitality / Acuity / Longevity** — all three are in the data model from day one even if only Vitality is active in gameplay currently; Acuity is a dynamic spectrum, not a sanity meter; high is as bad as low for different reasons
- **Fixed combat tick rate** — 1 second global engine tick, 3 ticks per combat round; no per-player adjustment

---

### 7. What Is Not Yet Built

Be explicit about what the GDD describes that does not yet exist in code. Future sessions should check this list before assuming something is implemented:

- Tick engine / combat system
- Item model and loot system
- Character creation flow (in-game; admin creation works)
- Inventory command
- Minimap / fog-of-war rendering in the client
- Party system
- Guild system
- Quest system
- NPC system
- Dungeon instancing
- PvP flagging and bounty system
- The Wastelands scaling logic
- The Robotic Helper NPC
- Faction / reputation system
- Admin teleport commands (in-game; Django admin works)
- Super user item gifting (in-game)
- `yell`, `tell`, `party`, `guild`, `zone`, `general`, `emote` chat channels (only `say` and `who` implemented)
- `who` currently returns all Character records, not just online players

---

### 8. Known Issues / Flags for Future Sessions

Note any issues observed while reading the code that are worth flagging but not fixing in this session:

- `get_online_names()` in consumers.py queries all Character records, not just those with active WebSocket connections. This is a placeholder — a proper online tracking mechanism (Redis presence, or a connected flag) is needed before `who` is accurate at scale.
- `send_room_description()` sends a `status` message with bar values, but Vitality/Acuity/Longevity maximums are not sent — the client cannot render a proportional bar without knowing the max. Consider adding `vitality_max`, `acuity_band_low`, `acuity_band_high`, `longevity_max` to the status message.
- Character name is derived from `user.profile` — document clearly in code comments what the expected profile model looks like, so future sessions know what to `select_related`.

---

## Output

Write the document to `docs/shyland/Shyland_Architecture.md`.

It should read as a clear, precise technical reference — not a tutorial. Use present tense throughout ("The consumer joins the room group on connect", not "The consumer will join"). Use code blocks for any code examples or field lists. Keep prose tight.

When done, confirm what was written and flag anything in the code you could not fully interpret from the files available.

---

*Architecture brief — Shyland v0.1*
*Based on commit 391ae1f — "first iteration of Shyland MUD"*
