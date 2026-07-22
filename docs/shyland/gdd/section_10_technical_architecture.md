## 10. Technical Architecture

### 10.1 Stack

|Layer                        |Technology                                                        |
|-----------------------------|------------------------------------------------------------------|
|**Backend framework**        |Django 5 (Python)                                                 |
|**Real-time transport**      |Django Channels + Daphne (ASGI) + WebSockets                      |
|**Database**                 |PostgreSQL 16                                                     |
|**In-memory / session state**|Redis 7 (Channels layer + presence tracking)                      |
|**Client**                   |Browser-based — vanilla HTML/CSS/JS, no framework                 |
|**Auth**                     |Django built-in auth with the shared gamer-tag profile system; Shyland characters have their own `name` field, initialized from the gamer tag at creation and independent of it thereafter|
|**Deployment**               |Docker Compose: nginx → Daphne → Django/Redis/Postgres            |

All game logic runs server-side. The client is a dumb terminal — it sends text commands and renders JSON output. No game state is trusted from the client.

### 10.2 Client Architecture (v20)

Web-only. Responsive down to phone screen size. No native app. **The app fits the viewport exactly — the page never scrolls;** only designated panes scroll internally.

```
┌───────────────────────────────────────────────┬──────────────────┐
│ LOCATION BAR  Zone: Area: Room (theme colors) │ CHARACTER NAME   │
├───────────────────────────────────────────────┤ V ▓▓▓▓▓░░ 226/345│
│                                               │ A ──[band]─┃─ 1.0│
│   OUTPUT PANE — one unified scrolling pane    │ L ▓▓▓▓▓▓▓ 274/274│
│   (clears on each room entry, by ruling;      ├──────────────────┤
│    room render, then zone-colored separator,  │ FIGHT INFO       │
│    then events)                               │ (scrolls; enemy  │
│                                               │  hp bars, focus »)│
│                                               ├──────────────────┤
├───────────────────────────────────────────────┤                  │
│ > COMMAND BAR            ●42ms        [SEND]  │  MAP  300 × 300  │
└───────────────────────────────────────────────┴──────────────────┘
        left 2/3 flexes on resize          right pane fixed 300px
```

**Location bar:** `Zone: Area: Room` (Area omitted when absent); zone and area names in their model-authored `theme_color`s, room near-white, separators chrome; one line; overflow truncates Area first, then Room, never Zone. Colors are server-delivered — one source of truth shared with output.

**Right pane (fixed 300px):** the stats section — headed by the **character name, verbatim casing, in value-color** — with Vitality and Longevity as ratio bars (fills in success-color — the loot-message green, verbatim, full strength; numerals and labels value-color) and **Acuity as a band gauge** (fixed 0.0–2.0 track, the Origin's optimal band as a **solid success-color block** — the translucency era ended in v22 — and a say-color gold position tick, 16×4px, extending above and below the track): the first surface that teaches the three-bars design, now speaking the chart's own colors. The whole section turns **combat-red** (from the state-sync combat boolean; the name re-points to error-color). Below it, the **fight panel**: one row per session enemy — name and `hp/hp_max` in value-color, hp bar and the focus marker `»` in error-color — fed by a `fight` message each combat tick, empty outside combat, scrolling on overflow. The **map** (Section 2.5) sits fixed at the bottom.

**Command bar:** input line with the send button inside and the **connection indicator** at its right — a dot plus latency (client pings every 10s, server echoes; green healthy, amber degraded, red pulsing on reconnect, gray dead; accessible label, never announced).

**The output envelope:** every outbound WebSocket message carries `ts` (epoch ms UTC, stamped at creation) and `seq` (per-connection monotonic, stamped at one audited delivery choke point — the designated future firehose tap; nothing may bypass it). **`seq` order is authoritative for rendering;** `ts` may lawfully be non-monotonic against it. **Display rule — timestamps mark events, not renderings:** combat, chat, presence, commerce, XP, errors, system/ambient, setting-change confirmations, and command echoes display the dim `[HH:MM:SS.ss]` local-time prefix (aria-hidden; governed by the `timestamps` preference); room renders and state reports (inventory, stats, vendor lists, examine, help) do not.

**The output palette (v22 — the named chart):** client-side styling driven by server-sent semantic categories (the server never sends hex for message text). The complete named vocabulary, every name a CSS variable and citable design language:

| Name | Value | Voice |
|---|---|---|
| key-color | `#7FB3D5` | labels; section headers; the map here-dot |
| value-color | `#E8E4D8` | content; success prose; report text; the known |
| muted-color | `#6b6b80` | column guides, command echo, system/ambient, combat misses, the unknown |
| error-color / agro-color | `#E24B4A` | CLI errors; hostile map rooms (two names, deliberately separable, currently one value) |
| warn-color | `#E8D44D` | the world declined — resolution and mechanical failures |
| say-color | `#f0c060` | speech, player and NPC; the Epic rarity gold (deliberate reuse); the acuity tick |
| loot-color / success-color | `#4caf7d` | gains: reward lines, pickups, heal-to-full, "Combat has ended."; the V/L bar fills and the acuity band |
| combat family | hit-out `#C4453F` · crit-out `#E24B4A` bold · hit-in `#E0724A` · crit-in `#F08A50` bold | direction axis: red = dealing, orange = taking; crits brighter + bold; misses muted. Crit-in ships wired, dormant until NPC crits occur mechanically |
| rarity scale | Common `#9C9A90` · Uncommon `#5FA8D3` · Rare `#B387E8` · Epic `#f0c060` · Legendary `#E0724A` · Artifact `#E24B4A` | the item flag block, and rarity words wherever item names render in information output |

**Chart-as-license (v22 — standing law):** the color chart is not a description of the colors in use — it is the *license* to use them. A color literal not on the chart (or the documented chrome list) is a defect by definition, enforced by a set-equality palette conformance test: a new color appearing fails, and a licensed color disappearing fails, so every palette change is a deliberate two-place edit traceable in one diff. The v22 sweep killed the hard-coded error amber (#121), the dimmer report parchment (one content voice — report text is value-color), and the old translucent band — and named every survivor.

Structural section headers share key-color — *every* header, present and future. Room-content lines in value-color; room description prose value-color and area prose in the Area's `theme_color` (the two prose levels visually distinct). **Structured reports (v21/v22):** `report` messages carry server-tagged lines — keys key-color, values value-color, plus segment-tagged spans naming a palette voice for the Kind-3 tables (muted headers, band-colored durability, rarity-colored words) — adopted by `inv`, `stats`, `wallet`, `help`, and the travel listing. Who's-here / What's-here entries are bare noun phrases. Speech is `Name: message` in say-color, both species, no prefix. Rarity colorizes the item flag block and rarity words; the binding flag reads `Bound | Unbound`. Directional combat arrows were designed and **abandoned**. **(v21) Zone-colored chrome:** all five pane borders render 5px in the current Zone's `theme_color` at ~0.75 alpha, re-tinting on zone change (`#CCCCCC` pre-first-render fallback); the combat-red takeover keeps precedence on the stats/fight border during a fight; the room separator runs slimmer at 3px so the frame outweighs the punctuation.

**Accessibility:** Semantic HTML throughout. ARIA live regions on the output pane; timestamps, the map, the bars/gauge, and the separator are decorative to the reader — the numerals and text carry every fact. All functionality keyboard-accessible. Screen reader compatible from day one.

**Phone layout:** location bar → compact stats strip (fight info beneath it only during combat) → output (flex) → command bar pinned; the map below the output, reachable by scroll. Typing and reading stay primary.

**Single visual theme** — no colorblind mode or high-contrast mode in v1 (which is why direction and state are always carried by words, never color alone).
### 10.3 Online Presence

Online player presence is tracked via Redis keys:

- **Key pattern:** `shyland:online:{character_pk}`
- **Value:** character display name (resolved at connect time)
- **TTL:** 90 seconds, refreshed by a 60-second heartbeat while connected
- **On connect:** key written after joining the room channel group
- **On disconnect:** heartbeat cancelled, key deleted
- **Unclean disconnect:** key expires naturally within 90 seconds

The `who` command queries Redis directly — no DB call. This means only players with active connections (or whose TTL has not yet expired) appear in `who`.

### 10.4 Server / Tick Architecture

The game server runs a **tick engine** implemented as a Django management command (`run_tick_engine`) running as a fifth Docker container (`ticker`). It loops every 1 second and calls four processors in order:

1. **`process_combat()`** — resolves combat rounds for all active `CombatSession` rows; handles dying-state expiry and stale-session cleanup
1. **`process_corpse_decay()`** — deletes corpses whose `decay_at` has passed
1. **`process_npc_respawn()`** — `RoomSpawn`-driven. Each tick: (a) loads all active `RoomSpawn` rows; (b) for each spawn, deletes dead `NpcInstance` rows for that definition/room/mk_tier where `respawn_at__lte=now`; (c) counts remaining live and dead instances; (d) computes `to_create = min(spawn.count - live_count, (spawn.count × 2) - (live_count + dead_count))`; (e) creates that many new live `NpcInstance` rows. Dead instances persist until their `respawn_at` passes — this is what controls the respawn delay. The cap at `count × 2` total instances prevents unbounded dead-instance accumulation. **(v21, #107 — emergency fix)** The sweep is batched to per-zone queries rather than per-row round-trips: the pre-existing per-row pattern (~750–800 queries/tick, ~4.2s of processing per 1s tick) had stretched combat rounds to ~15.5s against the 3s design and invalidated all balance feel-testing; the batch restored live rounds to ~3.8s, behavior contract unchanged (timers, boss gating, spawn counts). Aggressive respawns engage present players inside this same path (§5.9). **Per-tick query discipline (standing, #107):** new per-tick work must justify its query count; further batching candidates are tracked on #107.
1. **`process_effects()`** — four phases per tick: (1) component ticking at round boundaries (`tick_number % COMBAT_ROUND_TICKS == 0`) — queries active `EffectComponentInstance` rows of ticking types (DoT, HoT, Acuity shift) and applies their effect to the target character's bars; (2) passive Acuity drift every tick — moves characters' `acuity_current` toward their Origin baseline by `ACUITY_DRIFT_RATE` (0.01) when no active shift component instance exists, snapping to baseline when within the drift step; (3) component expiry every tick — deactivates `EffectComponentInstance` rows whose `expires_at` has passed, reverses stat deltas for `stat_bonus`/`stat_penalty` components via `apply_stat_effect(reverse=True)`, sends one expiry message per parent `EffectInstance` if all components expire together or one per component if staggered, then closes the parent `EffectInstance` when all its components are inactive; (4) passive bar regeneration every tick — for all characters not in an active `CombatSession` and not `is_dying`, heals Vitality by `ceil((vitality_max - vitality_current) / VITALITY_REGEN_SECS)` and Longevity by `ceil((longevity_max - longevity_current) / LONGEVITY_REGEN_SECS)`, skipping bars already at max; sends a silent status update to the player's personal group when any bar changes; all Origins including Machinekind receive Phase 4 regen

Each processor runs every tick regardless of whether it has work to do. Only `process_combat()` performs additional internal gating — a combat round only resolves when `tick_counter % COMBAT_ROUND_TICKS == 0` on the session.

**Tick-loop async-safety rule (v22, #135 — standing):** synchronous helpers cross into the async tick loop **only** via `database_sync_to_async` or verifiably prefetched data — never as bare calls that execute ORM queries. The founding case: the full-expiry branch of `process_effects` called the expiry-message helper bare, and its fresh query raised `SynchronousOnlyOperation` and killed the entire engine on every full timed-effect expiry — a 100%-reproducible engine-killer, fixed surgically and field-proven against production as v22's final brief.

**Status payload:** The status message sent to clients on every relevant event includes: `vitality`, `vitality_max`, `acuity`, `acuity_baseline`, `acuity_band_low`, `acuity_band_high`, `longevity`, `longevity_max`, `room_name`, `area_name`. All consumer and tick engine status sends use this same expanded shape.

**Global tick rate:** 1 second. Combat round = 3 ticks (`COMBAT_ROUND_TICKS = 3`). Fixed — not adjustable per player or per NPC.

NPC AI runs server-side. No game state is trusted from the client.

### 10.5 Persistence Model

#### Written to DB on change (event-driven):

- Character stats, all three bars (Vitality/Acuity/Longevity current values), inventory, position. **(v21, #52 — standing invariant)** Consumer-side bar mutations are atomic database operations (`F('<bar>_current') + magnitude` clamped with `Least` to the max), never read-modify-write on the cached character object; the cached character is refreshed before any display that follows a mutation. The tick engine is the only other bar writer. Row-locking was considered and rejected (tick-engine contention). The #52 audit documented every bar-write call site; the sibling stat-field race is tracked as #110.
- Quest state
- Faction reputation
- Guild data
- Item soulbind records
- EffectInstance creation and deactivation

#### Written to DB on interval (every 60 seconds):

- Character XP
- Currency amounts
- Item durability values

#### In-memory only (Redis):

- Online presence keys (`shyland:online:*`) — self-healing on reconnect; TTL 90s
- Django Channels channel layer (WebSocket group routing)

**Redis is not used for combat state, effect state, or any game data where loss would affect player experience or require recovery logic.** All combat state (`CombatSession`, `CombatAction`) lives in PostgreSQL.

#### Never persisted:

- Chat messages (ephemeral; stored only if reported for moderation)
- Combat log

### 10.6 World State & Instancing

Shared persistent world — all players inhabit the same rooms. No instancing for standard content.

**Dungeons:** Semi-instanced. One party per dungeon copy. Additional parties queue or enter a parallel copy. Dungeon state resets on a timer (default: 6 hours).

**Guild halls:** Fully instanced per guild.

**The Wastelands:** Shared world but all content is dynamically scaled — no instancing required. Scaling is computed server-side at spawn time based on the highest-level player in the triggering party.

### 10.7 Admin / Super User Infrastructure

Super user tools are **v1 critical infrastructure** — not an afterthought.

**In-game admin (v22):** the Django auth Group **`admins.shyland`** is the in-game admin grant — membership checked live per command attempt (revocation is instant), gating the stealth commands `sudo` and `last` (Section 9.1). Grants are made through Django admin; the Group ships empty. Per-player mechanical overrides (e.g. `home_cooldown_seconds`) are likewise Django-admin edits.

Required v1 admin capabilities:

- Teleport to any room by ID or name
- Spawn any NPC or item in current room
- Observe any room invisibly
- Adjust any character's stats, bars, currency, or position
- Gift items to players (items become immediately soulbound on gift; gifted Artifact items are hand-authored)
- Mute, kick, ban players
- Force-reset dungeon instances
- Access moderation queue

### 10.8 Security

- All game logic runs server-side; client is a dumb terminal
- Rate limiting on all WebSocket messages
- Command injection sanitized at input layer
- Item soulbind status, currency amounts, stat values, and durability values never trusted from client
- Anti-cheat: server validates all position changes, damage values, inventory states
- Item gifting requires super user authentication — cannot be spoofed by regular players
- Curse status never sent to client for unidentified items

### 10.9 Moderation

- `report <player> <reason>` sends flagged log to moderation queue
- Staff can appear invisible, observe rooms, mute/kick/ban
- Automated detection: spam, impossible stat values, movement anomalies

-----

### 10.10 Standing Engineering Tenets (v19+)

Adopted as version-level law, recorded here and in the architecture doc's design principles:

- **The code is definitive.** Reseeding restores the exact coded world configuration: every seed-owned table is enforced to authored values on every run, operator-added extras are deleted (cascades reported loudly), and a second consecutive run must report zero changes. Live-database edits are emergency mitigations at most — real changes go through the issue → design → brief → deploy workflow.
- **Status payloads are always built from fresh DB reads, and every engine-side mutation of player-visible state pushes an update to the client.** The complement of "the server is the authority": the server must also *speak*.
- **Contests add, quantities multiply.** Stats fed into opposed rolls grow additively on the player curve; pools and payouts may scale multiplicatively.
- **Criticals are an independent roll on successful hits** — never a band of the to-hit roll.
- **Dying interrupts combat in both directions**; revival restores exactly what the potion heals.
- **Presence is ownership-tokened**: connect takes the key unconditionally; heartbeat and delete are guarded Lua operations; the heartbeat self-heals a lost key.
- **The only legitimate exit from combat is `flee`** — quitting is allowed (v22) but ends nothing: combat continues after quit, and abandoning the connection abandons the character to the fight. Tab-closing and quitting are identical in cost.
- **NPC-level protection is independent of room safety**: `attackable=False` refuses everywhere; safe rooms remain their own layer.
- **(v21) Consumers never read-modify-write bar or stat fields** — mutations are atomic database operations, refreshed before display.
- **(v21) Per-tick and per-operation query discipline** — new recurring work must justify its query count; the map payload's bounded-five-query build is the pattern.
- **(v22) Fill fraction is invariant under every max-changing mutation** — the bar law (Section 4.4), one atomic rescale, no special cases.
- **(v22) Sync helpers cross into the tick loop only via `database_sync_to_async` or verifiably prefetched data** — the async-safety rule (Section 10.4).
- **(v22) The color chart is the license** — a color literal off the chart is a defect, enforced by set-equality test (Section 10.2).
- **(v22) Consequence must be seen** — anything the player needs to act on speaks in a visible voice, never the muted ambient one; masking is done by construction on the server, never delegated to the client (the map's frontier rule is the pattern).

-----

