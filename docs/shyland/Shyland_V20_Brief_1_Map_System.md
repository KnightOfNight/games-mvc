# Shyland V20 Brief 1 — Map System

Implements GitHub issues **#43** (Z05 ring re-lay), **#44** (Z01 geometry fixes), **#46** (Fordwatch text fix), **#35** (map backend), and **#36** (map client), in that order. This brief is self-contained; do not consult chat history. Audit reference for background only: `docs/shyland/Shyland_MapFrag_Audit_Z05_Z01.md`.

Close each issue with `gh issue close <N>` only at the point marked for it, gated as stated. **Never remove or prune any transient document from the repo** (reports, briefs) — the operator does all pruning.

---

## 0. The settled map data model (context — binding design rules)

- `Room.coord_x / coord_y / coord_z` are the map's **positional source of truth**. Pure map-space; **z is not elevation**. Exits remain the connectivity source of truth.
- Coordinate space is **per-zone**; one room per (zone, x, y, z) cell, no exceptions.
- **Core invariant:** every unflagged cardinal exit (N/S/E/W) between same-zone rooms lands grid-adjacent at the same z. Deltas: north (0,+1,0), south (0,−1,0), east (+1,0,0), west (−1,0,0).
- A per-exit **boundary flag** (built in Part C) overrides: a flagged exit is a MapFrag boundary regardless of geometry and has no geometric requirement.
- **Cross-zone cardinal exits are boundaries automatically**; exempt from geometric checks; no flag needed.
- **Up/down exits have no geometric requirement** and always break fragments. Non-cardinal movement never joins fragments.
- A **MapFrag** is derived, never stored: a connected component over unflagged, intra-zone cardinal exits. Rooms with no cardinal exits are single-room fragments.
- Fog-of-war: per-character via the existing `RoomVisit` model. No new tracking model.
- All game logic server-side; the client renders what it is sent and is never trusted.

---

## Part A — Z05 ring re-lay (#43)

All world changes in Parts A and B are made in `django/src/apps/shyland/management/commands/seed_world.py` (seed authority: the code is definitive; reseeding is enforce-exact).

### A1. Six new rooms

Add to the Convergence seeding, using the `_room` pattern of neighboring ring rooms. Each new room's Area assignment **matches its adjacent ring rooms' — including the likely case that ring rooms have no Area at all** (Z05's only Areas are the four park paths; Area is optional and the room header format already handles area-less rooms). `br4` matches the Bamboo Run path's Area. `brief_description` is required non-null non-blank on every Room.

| Key | (x, y) | Name | brief_description |
|---|---|---|---|
| r36 | (5, −4) | The Coppersmith's Turn | The ring street bends west at a chamfered corner. |
| r37 | (2, −5) | Lantern Corner | The street turns beneath a crooked lantern post. |
| r38 | (−4, −5) | The Long Shadow | The street angles north where the wall throws shade. |
| r39 | (−5, −4) | Quiet Corner | A hushed bend where the street turns north. |
| r40 | (−2, 5) | The Painted Bend | The street curves east past a wall of murals. |

Full descriptions (author exactly; these are final creative content):

- **r36 — The Coppersmith's Turn.** *The ring street bends here, its flagstones worn bright at the turn where ten thousand boots have cut the corner. A verdigris statue of a smith — no one remembers from which world — raises a hammer that will never fall. South and west, the street runs on; the wall above glitters with rivets from at least three realities.*
- **r37 — Lantern Corner.** *A single crooked lantern post marks the turn, its flame burning a color that has no proper name. Someone has bolted a second lamp — sleek, humming, unmistakably from the Sprawl — to the same post, and the two lights argue gently over the cobbles. The street bends west toward the Iron Gate and north back along the wall.*
- **r38 — The Long Shadow.** *The city wall leans close here, and its shadow lies across the street at every hour, in defiance of any sun. Chalk marks from generations of travelers scale the lower stones: names, dates, and arrows pointing to places that may no longer exist. The street turns, running north along the wall and east toward the Iron Gate.*
- **r39 — Quiet Corner.** *For no reason anyone can explain, sound falls soft at this bend of the ring street. Merchants lower their voices; even cart wheels seem to apologize. A small stone bench sits against the wall, worn smooth, facing nothing in particular. The street runs north toward the Pale Gate and east into the long shadow of the wall.*
- **r40 — The Painted Bend.** *The wall at this corner is a riot of murals — layered, overlapping, painted by hands from every world the rifts have swallowed. A knight rides a neon serpent; a rocket lifts off from a wheat field; someone has painted the Heart itself, glowing, at the center of it all. The street curves east toward the gates and south along the western wall.*
- **br4 — (4, 0) — End of the Bamboo Run** (Bamboo Run path Area). brief_description: *The bamboo path opens onto the ring street.* Full: *The bamboo thins here, the green hush of the run giving way to the noise and light of the ring street just east. The last stalks are carved with initials and small blessings in a dozen scripts — travelers marking the end of the quiet part of their walk.*

### A2. Ring and spoke rewiring

Update `RING_WALK` (and any dependent wiring) so the ring reads, in walk order, with the new rooms inserted and the one direction corrected:

- Insert `r36` between `r34` and `r13`: `r34 --south--> r36 --west--> r13` (replaces `r34 --west--> r13`).
- Insert `r37` between `r15` and `r16`: `r15 --south--> r37 --west--> r16` (replaces `r15 --west--> r16`).
- Insert `r38` between `r20` and `r35`: `r20 --west--> r38 --north--> r35` (replaces `r20 --west--> r35`).
- Insert `r39` between `r35` and `r21`: `r35 --west--> r39 --north--> r21` (replaces `r35 --north--> r21`).
- Insert `r40` between `r31` and `r32`: `r31 --north--> r40 --east--> r32` (replaces `r31 --east--> r32`).
- Relabel `r33 --south--> r06` to `r33 --east--> r06` (reverse becomes west).
- Insert `br4` in `PATH_EDGES`: `br3 --east--> br4 --east--> r10` (replaces `br3 --east--> r10`).
- Relabel `ww1 --west--> ww2` to `ww1 --north--> ww2` (reverse becomes south).
- Relabel `bw1 --east--> bw2` to `bw1 --west--> bw2` (reverse becomes east).

All reverse pairs are handled by the existing expansion machinery — verify it still applies.

### A3. Spoke coordinate re-lay (coordinate-only)

ww1 (0,1), ww2 (0,2), ww3 (0,3), ww4 (0,4); bw2 (−1,−1), bw3 (−1,−2), bw4 (−1,−3), bw5 (−1,−4); fb1 (−1,0), fb2 (−2,0), fb3 (−3,0), fb4 (−4,0); br1 (1,0), br2 (2,0), br3 (3,0). **No other Z05 room's coordinates change** — every ring room, the Heart, bw1, and the smithy keep their exact current values. Note: the seeder reconciles rooms by (zone, coords) — moving a room's coordinates must update the same seeded room (match by key/name), not create a duplicate; adjust the reconcile path if needed so room identity follows the room key, and verify no orphan rooms remain after reseed.

### A4. Two ring street-cart vendors

Vendor NPCs in **r36** and **r40** (opposite sides of the ring). Configure exactly like the existing Convergence vendor NPCs (e.g. Essa the Trader): non-attackable fixture, same commerce wiring (priced stock, buy/sell rules, authored `base_value`), and dialogue entries following the same listening-system pattern as the v19 Convergence roster.

**Stock rule for both carts (phrase it this way in code/data so it self-updates): every ItemDefinition of the consumable item type that exists at seed time**, at standard authored prices. At minimum this includes Healing Draughts.

- **r36 — VND-9, "the Draught Cart"** (cyberpunk vending automaton). Description: *A chrome-and-brass vending automaton squats beside the coppersmith statue, its serving hatch polished by use. A menu screen cycles through potions in four languages, two of which no longer exist. Stenciled on its flank: VND-9 — HOT DRAUGHTS — COLD LOGIC.* Dialogue (listening lines, matching existing vendor keyword patterns — greeting/browse/thanks): greeting: *"WELCOME, TRAVELER. HYDRATION IS SURVIVAL. SURVIVAL IS CUSTOMER RETENTION."* browse/wares: *"CURRENT INVENTORY: RESTORATIVES. ALL SALES FINAL. ALL CUSTOMERS VALUED."* thanks/farewell: *"TRANSACTION COMPLETE. DO NOT DIE. RETURN SOON."*
- **r40 — Mother Tansy's cart** (fantasy herbalist). Description: *A hand-painted wooden cart leans against the mural wall, hung with drying herbs and stoppered bottles that glow faintly in the shade. Mother Tansy, small and sun-browned, watches the street with the patience of someone who has sold remedies on six worlds and found the customers identical on all of them.* Dialogue: greeting: *"Come closer, love — everyone limps past this corner eventually."* browse/wares: *"Draughts for what ails you. And something ails everyone who walks this ring twice."* thanks/farewell: *"Off you go. Try to need me less next time."*

### A5. Geography audit (gated step — required before Part A closes)

Re-check all authored NPC dialogue and room descriptions for compass/positional accuracy against: the three relabeled transitions (Wisteria Walk and Basalt Way path room descriptions no longer bend; the r33/r06 corner turns east), and the six new rooms' neighbors (their descriptions must not contradict the new corners — e.g. any text implying the street continues straight where a corner room now sits). List every line checked and every line changed in the closeout report. Known-safe during design: "the gate north of the Heart" (the Green Gate does not move).

**Close #43** after A1–A5 are implemented, reseeded enforce-exact, and the Part F verification checks for Z05 pass.

## Part B — Z01 geometry fixes (#44)

### B1. Two relabels

- `vr-m06 --east--> vr-st1` becomes `--west-->` (reverse becomes east). Stonestep re-derives at: vr-st1 (−1,37), vr-st2 (−1,38), vr-m11 (−1,39).
- `vr-hf2 --west--> vr-m24` becomes `--north-->` (reverse becomes south). vr-m24 re-derives at (1,46).

### B2. Surface z-flattening (coordinate-only)

Every room in the Z01 surface fragment gets `coord_z = 0`, x,y preserved (they already agree with the exit graph), except the five rooms in B1 which take the cells listed there. Membership of "the surface fragment": every `vr-` room **except** the cave rooms (`vr-c1a` … `vr-c7i`). Cave rooms are untouched entirely — coordinates and wiring. Same reconcile-by-key caution as A3.

### B3. Boundary-flag seeding (executes after Part C's migration, in this same brief)

Set the boundary flag on both directions of exactly these five exit pairs:

| # | Pair |
|---|---|
| F1 | vr-v20 ↔ vr-c1a (east/west) |
| F2 | vr-v22 ↔ vr-c2a (east/west) |
| F3 | vr-m13 ↔ vr-c5a (east/west) |
| F4 | vr-m25 ↔ vr-c6a (east/west) |
| F5 | vr-m40 ↔ vr-c7a (east/west) |

No other exit anywhere gets the flag. The Tree Arch gate needs nothing (automatic cross-zone boundary).

### B4. Geography audit (gated)

Re-check NPC dialogue for: which side of the spine Stonestep is on (now west), and Highfold's warned-about aggro-offshoot direction (Bear's Hollow now north of the village). Report every line checked/changed.

### B5 — Fordwatch text fix (#46)

In `vr-v07` "Fordwatch": the brief description becomes exactly *"A green shard drifts above the crossing where the fog gives way."* (was "sphere"). In the full description, the sentence "A small sphere of soft green light drifts and bobs above the crossing" becomes *"A small shard of soft green light drifts and bobs above the crossing"* — the object is a Verdant Shard, and "sphere" wrongly echoes the Primordial Sphere, an unrelated obelisk object. No other wording changes.

**Close #44 and #46** after B1–B5 (B3 lands with Part C) and the Part F Z01 checks pass.

## Part C — Map backend (#35)

### C1. Model change: boundary flags

`Room` currently carries per-direction exit FKs (`exit_north`, `exit_south`, `exit_east`, `exit_west`, `exit_up`, `exit_down` — verify exact names in `models.py` and match the established pattern). Add four booleans, cardinals only (up/down always break and need no flag):

- `exit_north_boundary = models.BooleanField(default=False)`
- `exit_south_boundary = models.BooleanField(default=False)`
- `exit_east_boundary = models.BooleanField(default=False)`
- `exit_west_boundary = models.BooleanField(default=False)`

**Migration required.** Semantics: an undirected edge is a boundary if either side is flagged; seeding always sets both sides (B3), and the verify step enforces flag symmetry.

### C2. Extended seed verification (permanent invariant enforcement)

Extend the seeder's `_verify` to enforce, on every reseed, failing loudly on violation:

1. Geometry agreement: every unflagged intra-zone cardinal exit lands grid-adjacent at the same z.
2. Cell uniqueness per (zone, x, y, z).
3. Flag symmetry: a flagged exit's reverse is also flagged.
4. Flagged exits exist only on the five B3 pairs (for this seed).

### C3. MapFrag computation and payload

Server-side, computed fresh on demand (zones are ≤ ~160 rooms; no caching in v1):

- Fragment membership: BFS from the character's current room over **unflagged, intra-zone cardinal exits** (existence only — positions come from stored coords).
- Payload rooms: the intersection of the fragment with the character's `RoomVisit` set, plus the current room.
- Message, server-generated, sent on connect (with the v19 client-state sync full-state pattern) and on every room change (move, flee, travel, respawn):

```json
{"type": "map", "zone": "<zone id>", "current": {"x": 0, "y": 0},
 "rooms": [
   {"x": 0, "y": 0, "here": true,
    "exits": {"north": "open", "east": "unexplored", "west": "boundary"},
    "up": false, "down": true}
 ]}
```

Exit status per cardinal direction present on the room: `"open"` = leads to a visited room inside the fragment; `"unexplored"` = exit exists, destination unvisited; `"boundary"` = flagged or cross-zone. Directions with no exit are omitted. `up`/`down` are presence booleans. No room names or keys in the payload (v1 sends geometry only). Coordinates are the per-zone stored values; the client centers on `current`.

**Close #35** after C1–C3 (including B3 seeding) and the Part F backend checks pass.

## Part D — Map client (#36)

- Right-pane geometry (ruled final in the v20 layout pre-decision — this is the map's permanent home, not interim): the right pane is **fixed-width (300 px content width) running top to bottom**; the map is a **fixed 300×300 px square at the BOTTOM of the right pane**. Existing player stats stay at the top of the pane; the space between stats and map is left as-is for now (a later v20 brief fills it with fight information). Baseline layout is 1000 px total (left regions 700 + right pane 300); when the browser window widens, **the right pane keeps its fixed width and only the left regions grow**. Responsive down to phone width per the existing responsive rules (on narrow layouts the map may stack below; it must not break the terminal).
- Vanilla JS, rendering into the map area (SVG generation is fine; no framework, no external libraries).
- **North is up. Fixed window centered on the current room, no zoom**: render a 9×9 cell window (radius 4); rooms outside it are not drawn; cell size fixed at one-ninth of the 300 px square (~33 px).
- Rooms are circles; `"open"` exits between two drawn rooms are solid lines; `"unexplored"` exits are short dashed stubs (half a cell); `"boundary"` exits are short dashed stubs with a small perpendicular tick at the end. The current room gets a distinct highlight ring. Rooms with `up`/`down` show a small U/D letter badge (brighter on the current room).
- Redraw on every `map` message. Discard and fully re-render (no incremental diffing in v1).
- The map container carries `aria-hidden="true"`. Room descriptions and exits in the output remain the accessible source of truth; the map adds no information not already present in text.

**Close #36** after Part F client checks pass.

## Part E — Ordering and commits

Recommended commit sequence: (1) Part C1 migration + C2 verify skeleton; (2) Parts A + B world changes + B3 flags, reseed enforce-exact, C2 passing; (3) C3 payload; (4) Part D client. Amendments flow as needed; never remove transient docs.

## Part F — Verification (all must pass before the architecture doc step)

1. Reseed enforce-exact completes; extended `_verify` (C2) passes all four checks.
2. Z05: BFS from `heart` over cardinal exits places **60 rooms, 0 contradictions, 0 cell collisions**; the ring is 40 rooms/40 edges with delta sum (0,0).
3. Z01: every intra-zone cardinal exit is grid-adjacent at the same z except exactly the five flagged pairs; cell uniqueness holds zone-wide; fragment inventory: surface fragment of 101 rooms; caves split per the audit's projected inventory (single-room fragments are legal). Fordwatch (`vr-v07`) shows the corrected "shard" wording in both its brief and full descriptions after reseed.
4. Both carts: `buy` a Healing Draught succeeds at r36 and r40; stock lists every consumable-type ItemDefinition; vendors are non-attackable fixtures; dialogue responds per the listening system.
5. Payload: on connect and on movement the client receives a `map` message matching the schema; a brand-new character in the Heart receives exactly one room with `here: true` and four `unexplored` stubs; crossing the Tree Arch switches `zone` and the room set; entering the Silken Cleft via the flagged mouth switches fragments; `travel` recenters within the same (surface) fragment.
6. Client: renders per Part D on desktop and phone widths; screen reader ignores the map region; the output pane's text behavior is unchanged.
7. Geography audit reports for A5 and B4 are complete and included in the closeout.

## Part G — Architecture doc update (LAST — gated on all implementation and verification above being complete and passing)

Create `docs/shyland/Shyland_Architecture_v20.md` per the multi-brief convention: written header-first, then one section at a time, never one giant operation. **Do not remove `Shyland_Architecture_v19.md`** — the operator prunes. Header records the commit hash of this brief's architectural changes. Content: copy v19 forward and update: the Room model section (coordinate semantics: per-zone map-space, z not elevation; the four boundary-flag fields; the geometry invariant and extended `_verify`), a new Map System section (MapFrag definition, payload schema, delivery events, client rendering summary, aria-hidden stance), the world-data section (Z05 ring now 40 rooms incl. the six new rooms and two cart vendors; Z01 flattening and the five flagged mouths), and the consumer/message-type inventory (the new `map` message). Subsequent v20 briefs update this file in place with no version bump.

## Closeout report

Report: commit hashes per Part E step, all Part F results with numbers, both geography-audit line lists, and confirmation that #43, #44, #46, #35, #36 are closed with closing comments referencing this brief.
