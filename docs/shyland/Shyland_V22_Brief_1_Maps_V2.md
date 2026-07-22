# Shyland V22 Brief 1 — Maps V2
**Version:** 22 (major, feature release) · **Bucket:** B1 · **Brief:** 1 of the version
**Issues:** #82 (map changes — the founding B1 ticket), #115 (map pane breathing room). #53 was closed at triage as absorbed into #82; its content (gates grayed even when passed) is satisfied by the gate discovery-coloring in this brief and is named in the #82 comment below.
**Branch:** implement on the version's worktree branch (already created by the operator). Never merge to main; merging is the operator's action.
This brief is self-contained. Do not consult chat history. Where a data table and prose disagree, the table is authoritative.
---
## Pre-flight
1. Verify `DOCKER_HOST` before any deployment-touching action.
2. Confirm you are on the v22 worktree branch with a clean tree.
## Step 0 — Self-commit this brief (required first step)
Save this brief's full text verbatim to `docs/shyland/Shyland_V22_Brief_1_Maps_V2.md` (skip the write if an identical file already exists), commit it on the working branch, and **push immediately** — the push is the operator's signal that work has started.
**Standing rule for this brief:** commit and push at every step boundary below. WIP-sized intermediate commits are desired. Branch only — never merge.
---
## Step 1 — Issue housekeeping (before any implementation)
Post the following as comments via `gh`:
**On #82** — a design-history comment recording the ruled visual language (2026-07-18 design session), including these supersessions of the issue's original text:
- One glyph for travel nodes: shard and sphere rooms both render as the **octagon** — the issue's "different shape for shard" vs "different shape for sphere" is deliberately collapsed; the distinction lives in the travel listing.
- Undiscovered rooms render as **solid muted dots at half diameter**, superseding the issue's "simple gray circle" (which implied a full-size hollow circle).
- The **"UD" composite badge is retired**; U and D are independent corner badges with independent discovery coloring.
- **#53 is satisfied by this design**: gates now color by destination discovery (value-color once passed, muted-color before), which is exactly the defect #53 filed.
- Then the full ruling table (copy the Design Specification section of this brief, or link to this brief's committed path).
**On #115** — the margin ruling: 16px margin on all sides, pinned (not derived from glyph size), implemented as a centered 268×268 drawable area inside the unchanged 300×300 SVG; pane geometry and CSS untouched.
Do **not** close either issue now. Both close at closeout, gated on verification passing.
---
## Step 2 — Design Specification (authoritative)
### Named colors
| Name | Value | Meaning on the map |
|---|---|---|
| key-color | `#7FB3D5` | The one key fact: the here-dot |
| value-color | `#E8E4D8` | Known: discovered rooms, known edges/stubs, discovered-destination gates and badges |
| muted-color | `#6b6b80` | Unknown: frontier dots and their lines, unknown-destination gates and badges |
| agro-color | `#cc4444` | Stroke of a **visited** room with any aggressive spawn configured. Same value as error-color by design; the two names are deliberately separable in the future. Add `--agro-color: #cc4444;` as a CSS variable; do not reuse `--error` in map code. |
Rule of grammar: **stroke color carries room state** (value / agro); **solid fills mean points** (here-dot, frontier dot); value-vs-muted carries known-vs-unknown everywhere.
### Geometry constants
| Constant | Value |
|---|---|
| SVG size | 300×300 (unchanged), inside `#map-wrap` (unchanged CSS) |
| Margin | **16px all sides, pinned** — drawable area 268×268, centered |
| Window | **7×7 cells (radius 3)**, current room centered; CELL = 268/7 ≈ 38.29px |
| Unified stroke | **2px** for room circles, all edges, all stubs, gate lines and triangles |
| Room glyph | hollow circle, **r=10**, fill `--surface`, stroke value-color (or agro-color) |
| Here-marker | solid key-color dot, **r=6**, centered, drawn atop the room glyph; no ring, no fill change |
| Travel-node glyph | **octagon, circumradius 12, stroke 4px** value-color, vertices at 22.5°+45k° (flat sides face the cardinals), fill `--surface`. One glyph for shard and sphere rooms. **Never agro** (see invariant, Step 5). |
| Gate glyph | 8px connector line from the room glyph's **outer stroke edge**, perpendicular into the base midpoint of a **solid equilateral triangle, side 10px**, apex pointing outward. Color: value-color if the destination room is visited, muted-color if not — line and triangle together. |
| Undiscovered (frontier) room | **solid muted-color circle, r=5**, no stroke. Its connecting line from the discovered room is muted-color. |
| U/D badges | **14px bold** `Courier New, monospace` text. **U at the upper-right corner, D at the lower-right corner**, text center at **(+17, −17) and (+17, +17)** from the glyph center (the 17px offset is uniform for all glyph shapes). Color per badge: value-color if the destination room (above/below) is visited, muted-color if not. Independent per direction. |
**Attachment law (general):** anything that attaches to a glyph attaches at the **outer edge of its stroke**, never the geometric radius — circles at 10 + 1 = 11px; the octagon's flat side at its apothem 12·cos 22.5° ≈ 11.09 + 2 = 13.09px. This prevents cross-color stroke overlap.
### Rendering rules
- Edges draw first, glyphs on top, here-dot and badges last.
- Edge between two drawn rooms: full line center-to-center. Known destination → value-color; unvisited destination (frontier link) → muted-color.
- Open exit whose **visited** destination is outside the window: solid **value** half-cell stub (screen-space artifact — "known path continues off-screen").
- Exit to an **unvisited** destination outside the window: solid **muted** half-cell stub.
- The old dashed-stub and boundary-tick vocabulary is **retired entirely**: no dashes, no perpendicular ticks, anywhere.
- Frontier rooms draw **no exits of their own** — only lines *from* discovered rooms reach them (terminus rule).
- Full re-render on every `map` message (unchanged behavior).
- The map remains `aria-hidden="true"` (unchanged accessibility stance).
---
## Step 3 — Payload rewrite (server)
File: `django/src/apps/shyland/consumers.py` — rewrite `build_map_payload` (and keep `send_map` delivery events unchanged: connect, move including aggro-ambush branch, flee, travel, respawn; `look` still sends no map).
### Schema
```json
{"type": "map", "zone": "<zone slug>", "current": {"x": 0, "y": 0},
 "rooms": [
   {"x": 0, "y": 0, "discovered": true, "here": true,
    "travel_node": true, "agro": false,
    "exits": {"north": "known", "east": "unknown", "south": "gate-unknown"},
    "up": "known", "down": "unknown"},
   {"x": 0, "y": 1, "discovered": false}
 ]}
```
### Field semantics (authoritative)
| Field | On discovered rooms | On frontier rooms |
|---|---|---|
| `x`, `y` | always | always |
| `discovered` | `true` | `false` |
| `here` | `true` on the current room only; omit elsewhere | never |
| `travel_node` | `true` iff a `TravelNode` exists for the room; omit when false is acceptable, but if emitted must be boolean | **never present** |
| `agro` | `true` iff any `RoomSpawn` in the room references an `NpcDefinition` with `is_aggressive=True` — **configuration, not instance state** (a dead or unspawned instance still flags) | **never present** |
| `exits` | per cardinal exit present: `"known"` / `"unknown"` (destination visited or not), `"gate-known"` / `"gate-unknown"` (boundary-flagged **or** cross-zone exit, destination visited or not). Directions with no exit omitted. | **never present** |
| `up`, `down` | `"known"` / `"unknown"` by destination `RoomVisit`; omit the key when the exit doesn't exist | **never present** |
**Masking by construction:** a frontier entry contains **exactly** `x`, `y`, `discovered: false` — nothing else, ever. This is the fog-of-war philosophy enforced in the wire format: an undiscovered room discloses existence only. The server must not rely on the client to hide anything.
### Room set
- Discovered set: the MapFrag (connected component over unflagged, intra-zone cardinal exits from the current room — unchanged definition) intersected with the character's `RoomVisit` set. The current room is always included (defense-in-depth, unchanged).
- Frontier set: fragment rooms **not** visited that are cardinally adjacent (via an unflagged, intra-zone exit) to a room in the discovered set.
- Nothing deeper than the frontier ever enters the payload.
- Gate destinations never enter the `rooms` array; they are looked up only for their visit bit.
### Query discipline (performance — binding)
Payload builds fire **per player, per room change, plus connect**. This is the post-#107 rule: per-operation query discipline; the map must never introduce N+1 patterns. The build must use a **bounded, constant number of queries**, target ≤ 5:
1. Zone rooms with exit ids (the existing fragment-BFS source data).
2. One `RoomVisit` query for this character over the **union** of zone room ids **and all gate destination ids** (cross-zone gate destinations live outside the zone — the union makes one query cover fragment membership, U/D destinations, and gate destinations alike).
3. Aggro room ids: `RoomSpawn` filtered on `room__zone` and `npc_definition__is_aggressive=True`, `values_list('room_id')`.
4. Travel-node room ids for the zone.
**No queries inside the BFS loop. No per-room queries of any kind.** Lock this with the `assertNumQueries` test in Step 6.
---
## Step 4 — Renderer rewrite (client)
File: `django/src/apps/shyland/templates/shyland/game.html`.
- Rewrite `renderMap` to the Step 2 specification and the new payload schema. New constants: `MAP_SIZE=300`, `MARGIN=16`, `INNER=268`, `MAP_RADIUS=3`, `CELL=INNER/7`.
- Coordinate mapping: `px(x) = MARGIN + INNER/2 + (x−cx0)·CELL`, `py(y) = MARGIN + INNER/2 − (y−cy0)·CELL` (north up, unchanged).
- Octagon path: 8 vertices at circumradius 12, angles 22.5°+45k°, so flat sides face the cardinals.
- Gate assembly: start point at the room glyph's outer stroke edge along the exit direction (circle 11px, octagon 13.09px); 8px line; triangle base midpoint at line end; apex a further side·√3/2 ≈ 8.66px out; solid fill = stroke color.
- Badges: `<text>` at (+17,−17)/(+17,+17), `text-anchor="middle"`, 14px bold, per-direction color from the tri-state payload fields.
- CSS: **remove** the old `.map-open`, `.map-stub`, `.map-tick`, `.map-room`, `.map-room.here`, `.map-here-ring`, `.map-badge`, `.map-badge.here` rules. Add `--agro-color: #cc4444;` to the palette variables. New map styling may be inline SVG attributes or new classes referencing `var(--key-color)`, `var(--value-color)`, `var(--muted)`, `var(--agro-color)` — implementer's choice, but no hard-coded map colors that bypass the variables.
- `#map-wrap` CSS is untouched (#115 is solved inside the renderer via the margin inset, not padding).
---
## Step 5 — Seed-verify invariant
File: `django/src/apps/shyland/management/commands/seed_world.py`, in `_verify`.
Add a permanent check: **no travel-node room has an aggressive spawn configured** — i.e., no `RoomSpawn` whose `room` has a `TravelNode` references an `NpcDefinition` with `is_aggressive=True`. Check message: `travel-node rooms have no aggressive spawns (octagons never agro)`. This is law: an octagon is a special room that will never have agro.
---
## Step 6 — Tests
New file: `django/src/apps/shyland/tests/test_map_payload.py`. Note #117: the suite must be run as `python manage.py test apps.shyland.tests -t /app` (the stub `tests.py` breaks whole-app discovery; do not fix #117 in this brief).
Test `build_map_payload` directly against fixture data (small purpose-built zone in test setup: a few rooms, one boundary pair, one cross-zone exit, one travel node, one aggressive and one passive spawn, an up/down pair), plus one WebsocketCommunicator integration test asserting a `map` message with the new schema arrives on connect and on move. Required assertions, minimum:
1. **Frontier masking:** every `discovered: false` entry has exactly the key set `{x, y, discovered}`.
2. Frontier entries appear for unvisited fragment rooms adjacent to visited ones, and **only** those (nothing at depth 2).
3. An unvisited travel-node room adjacent to a visited room appears as a frontier entry with no `travel_node` key (masking beats specialness).
4. `agro` is `true` for a room whose aggressive spawn's instance is currently dead or unspawned (configuration, not state), and `false`/absent for rooms with only passive spawns.
5. Exit statuses: `known` and `unknown` track destination `RoomVisit`; a boundary-flagged exit and a cross-zone exit both produce `gate-known`/`gate-unknown` by destination visit.
6. `up`/`down` tri-state: `"known"`, `"unknown"`, and key-absent all covered.
7. `here: true` appears on exactly the current room; the current room is included even without a `RoomVisit` row.
8. **Query ceiling:** `assertNumQueries` around one payload build, at the constant count the implementation achieves (≤ 5). This test is the performance regression guard.
9. Gate destination rooms never appear in the `rooms` array.
Run the full suite (`apps.shyland.tests`) — all existing tests must still pass.
---
## Step 7 — Operator playtest checklist (client-side, manual)
The renderer cannot be auto-verified; closeout notes must state these are ready for operator playtest:
- Heart of the Convergence: octagon + here-dot; margin visible on all sides against the zone border.
- The Green Gate before and after entering the Verdant Reach: muted vs value triangle.
- A partially explored area: frontier dots at half size, solid, muted lines, no exits shown from them.
- The Sink/Drone Mouths: value D vs muted D at 17px offset.
- The Undercrag middle chamber: agro strokes + here-dot + both badge colors composing.
- Lion's Watch / Bear's Throne: agro-color strokes on real ×3 grounds.
---
## Step 8 — Architecture document (gated last step)
**This step is gated on all implementation and verification steps above being complete and passing.**
Brief 1 of a major version creates the new versioned file: `git rm docs/shyland/Shyland_Architecture_v21.md`, create `docs/shyland/Shyland_Architecture_v22.md`. Write **header first** (version 22.0; the header's commit hash records this brief's architectural changes), then copy content **one section at a time** from the v21 document — never one giant operation — with these changes:
- **Section 1 intro:** append one sentence: v22 opens with Brief 1 (Maps V2), the map vocabulary and payload redesign (#82, #115; #53 absorbed).
- **Section 4.12** — full rewrite to this brief's Steps 2–5: the named four-color vocabulary, the 7×7/16px-margin geometry, every glyph with exact numbers, the attachment law, the new payload schema and field-semantics table, masking-by-construction, the frontier/terminus rules, the query-discipline ceiling, and the octagon-never-agro seed invariant. Keep the MapFrag definition, delivery events, and accessibility stance (unchanged). Remove the old exit-status vocabulary and old renderer description.
- All other sections copy unchanged.
---
## Closeout
Write the closeout report to `docs/shyland/Shyland_V22_Brief_1_Maps_V2_Closeout_Report.txt`: what shipped, test results (counts), any deviations (deviations in issue creation or verification = stop per the standard rules), the operator-playtest-pending note, and the **final commit hash**. Close #82 and #115 (gated on verification passing), commit and push everything on the branch.
Do not remove or prune any documents.
Finally: run the issues report.
