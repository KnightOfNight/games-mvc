# Shyland MapFrag Audit — Z05 (The Convergence) and Z01 (The Verdant Reach)

**Issue:** #42 (Version 20 triage) &nbsp;|&nbsp; **Generated:** 2026-07-13T14:26:48Z &nbsp;|&nbsp; **Source analyzed:** `django/src/apps/shyland/management/commands/seed_world.py` at commit `65a1b26161dfdaee3b105719d6c825174055b729`

## 1. Provenance & Method

Static analysis of the seed source only — the room table (`self._room(...)` /
`self._vr_room(...)` call sites) and the edge literals (`PATH_EDGES`, `RING_WALK` expanded via
`_ring_edges()`, `VR_EDGES_ONE_WAY` expanded via `vr_edges()`) were extracted by AST parse; the
module was never imported and no database was touched. Checks follow the settled map data model
from the issue #35 superseding rulings: coordinates are per-zone positional truth (z is not
elevation), exits are connectivity truth, every unflagged intra-zone cardinal exit must land
grid-adjacent at the same z, up/down and cross-zone exits carry no geometric requirement, and a
MapFrag is the derived connected component over unflagged intra-zone cardinal exits.

**Status of proposals.** Everything in sections 7, 9, 10, and 11 is **PROPOSED, PENDING DESIGN
RULINGS**. This audit decides nothing; findings return to the design chat.

## 2. Totals & Checksums

| Checksum | Expected | Found | Result |
|---|---|---|---|
| Z05 rooms | 54 | 54 | PASS |
| Z01 rooms | 150 | 150 | PASS |
| Unique directed edges after expansion & dedup | ~414 | 414 | PASS |
| — cardinal | ~386 | 386 | PASS |
| — up/down | ~28 | 28 | PASS |
| Duplicate (x, y, z) cells within a zone | 0 | 0 | PASS |
| Exit-slot conflicts (same src+direction wired twice) | 0 | 0 | PASS |
| Edge keys with no matching room | 0 | 0 | PASS |
| Cross-zone cardinal exit pairs | 1 | 1 | PASS |

Every room key referenced by an edge exists in the room table, every room participates in at
least one edge, and no exit slot is wired twice. Determinism: two independent runs of the
analysis produced byte-identical output.

## 3. Check 1 — Geometry Agreement

Every intra-zone directed cardinal edge was checked against `coords(dst) == coords(src) +
delta(direction)`. The two cross-zone gate edges (section 5) are excluded. **54
directed-edge violations** were found: 24 z-drift and 30 x,y-mismatch. Each
bad exit pair appears twice (once per direction).

### 3a. z-drift (x,y correct, z differs) — 24 directed edges

All z-drift is in Z01, on the ancient stair (`vr-s*`, z climbing 0→4) and the Viridian Ridge
spine (`vr-m*`, z climbing 4→12): terrain-as-elevation authoring. Under the settled model z is
not elevation, so these all flatten out in the re-author plan (section 10).

| Zone | Src | Dir | Dst | Src coords | Dst coords | Expected dst |
|---|---|---|---|---|---|---|
| Z01 | vr-c01 | north | vr-m01 | (0, 31, 4) | (0, 32, 5) | (0, 32, 4) |
| Z01 | vr-m01 | south | vr-c01 | (0, 32, 5) | (0, 31, 4) | (0, 31, 5) |
| Z01 | vr-m04 | north | vr-m05 | (0, 35, 5) | (0, 36, 6) | (0, 36, 5) |
| Z01 | vr-m05 | south | vr-m04 | (0, 36, 6) | (0, 35, 5) | (0, 35, 6) |
| Z01 | vr-m08 | north | vr-m14 | (0, 39, 6) | (0, 40, 7) | (0, 40, 6) |
| Z01 | vr-m14 | south | vr-m08 | (0, 40, 7) | (0, 39, 6) | (0, 39, 7) |
| Z01 | vr-m18 | north | vr-m19 | (0, 44, 7) | (0, 45, 8) | (0, 45, 7) |
| Z01 | vr-m19 | south | vr-m18 | (0, 45, 8) | (0, 44, 7) | (0, 44, 8) |
| Z01 | vr-m21 | north | vr-m27 | (0, 47, 8) | (0, 48, 9) | (0, 48, 8) |
| Z01 | vr-m27 | south | vr-m21 | (0, 48, 9) | (0, 47, 8) | (0, 47, 9) |
| Z01 | vr-m29 | north | vr-m30 | (0, 50, 9) | (0, 51, 10) | (0, 51, 9) |
| Z01 | vr-m30 | south | vr-m29 | (0, 51, 10) | (0, 50, 9) | (0, 50, 10) |
| Z01 | vr-m33 | north | vr-m34 | (0, 54, 10) | (0, 55, 11) | (0, 55, 10) |
| Z01 | vr-m34 | south | vr-m33 | (0, 55, 11) | (0, 54, 10) | (0, 54, 11) |
| Z01 | vr-m35 | north | vr-m41 | (0, 56, 11) | (0, 57, 12) | (0, 57, 11) |
| Z01 | vr-m41 | south | vr-m35 | (0, 57, 12) | (0, 56, 11) | (0, 56, 12) |
| Z01 | vr-s1 | south | vr-v16 | (0, 15, 1) | (0, 14, 0) | (0, 14, 1) |
| Z01 | vr-s2 | north | vr-s3 | (0, 16, 1) | (0, 17, 2) | (0, 17, 1) |
| Z01 | vr-s3 | north | vr-s4 | (0, 17, 2) | (0, 18, 3) | (0, 18, 2) |
| Z01 | vr-s3 | south | vr-s2 | (0, 17, 2) | (0, 16, 1) | (0, 16, 2) |
| Z01 | vr-s4 | north | vr-s5 | (0, 18, 3) | (0, 19, 4) | (0, 19, 3) |
| Z01 | vr-s4 | south | vr-s3 | (0, 18, 3) | (0, 17, 2) | (0, 17, 3) |
| Z01 | vr-s5 | south | vr-s4 | (0, 19, 4) | (0, 18, 3) | (0, 18, 4) |
| Z01 | vr-v16 | north | vr-s1 | (0, 14, 0) | (0, 15, 1) | (0, 15, 0) |

### 3b. x,y mismatch — 30 directed edges

| Zone | Src | Dir | Dst | Src coords | Dst coords | Expected dst |
|---|---|---|---|---|---|---|
| Z01 | vr-hf2 | west | vr-m24 | (1, 45, 7) | (-1, 45, 7) | (0, 45, 7) |
| Z01 | vr-m07 | east | vr-m12 | (0, 38, 6) | (2, 38, 6) | (1, 38, 6) |
| Z01 | vr-m11 | south | vr-st2 | (1, 40, 6) | (1, 38, 6) | (1, 39, 6) |
| Z01 | vr-m12 | west | vr-m07 | (2, 38, 6) | (0, 38, 6) | (1, 38, 6) |
| Z01 | vr-m24 | east | vr-hf2 | (-1, 45, 7) | (1, 45, 7) | (0, 45, 7) |
| Z01 | vr-st2 | north | vr-m11 | (1, 38, 6) | (1, 40, 6) | (1, 39, 6) |
| Z05 | br3 | east | r10 | (3, 0, 0) | (5, 0, 0) | (4, 0, 0) |
| Z05 | bw5 | south | r18 | (1, -4, 0) | (-1, -5, 0) | (1, -5, 0) |
| Z05 | fb1 | west | fb2 | (-1, 0, 0) | (-2, 1, 0) | (-2, 0, 0) |
| Z05 | fb2 | east | fb1 | (-2, 1, 0) | (-1, 0, 0) | (-1, 1, 0) |
| Z05 | fb4 | west | r24 | (-4, 1, 0) | (-5, 0, 0) | (-5, 1, 0) |
| Z05 | r01 | south | ww4 | (0, 5, 0) | (-1, 4, 0) | (0, 4, 0) |
| Z05 | r06 | north | r33 | (5, 4, 0) | (4, 4, 0) | (5, 5, 0) |
| Z05 | r10 | west | br3 | (5, 0, 0) | (3, 0, 0) | (4, 0, 0) |
| Z05 | r13 | east | r34 | (4, -4, 0) | (5, -3, 0) | (5, -4, 0) |
| Z05 | r15 | west | r16 | (2, -4, 0) | (1, -5, 0) | (1, -4, 0) |
| Z05 | r16 | east | r15 | (1, -5, 0) | (2, -4, 0) | (2, -5, 0) |
| Z05 | r18 | north | bw5 | (-1, -5, 0) | (1, -4, 0) | (-1, -4, 0) |
| Z05 | r20 | west | r35 | (-3, -5, 0) | (-4, -4, 0) | (-4, -5, 0) |
| Z05 | r21 | south | r35 | (-5, -3, 0) | (-4, -4, 0) | (-5, -4, 0) |
| Z05 | r24 | east | fb4 | (-5, 0, 0) | (-4, 1, 0) | (-4, 0, 0) |
| Z05 | r31 | east | r32 | (-2, 4, 0) | (-1, 5, 0) | (-1, 4, 0) |
| Z05 | r32 | west | r31 | (-1, 5, 0) | (-2, 4, 0) | (-2, 5, 0) |
| Z05 | r33 | south | r06 | (4, 4, 0) | (5, 4, 0) | (4, 3, 0) |
| Z05 | r34 | west | r13 | (5, -3, 0) | (4, -4, 0) | (4, -3, 0) |
| Z05 | r35 | east | r20 | (-4, -4, 0) | (-3, -5, 0) | (-3, -4, 0) |
| Z05 | r35 | north | r21 | (-4, -4, 0) | (-5, -3, 0) | (-4, -3, 0) |
| Z05 | ww1 | west | ww2 | (0, 1, 0) | (-1, 2, 0) | (-1, 1, 0) |
| Z05 | ww2 | east | ww1 | (-1, 2, 0) | (0, 1, 0) | (0, 2, 0) |
| Z05 | ww4 | north | r01 | (-1, 4, 0) | (0, 5, 0) | (-1, 5, 0) |

Two distinct patterns:

- **Z05 (24 edges).** The Convergence was authored as a
  *picture*: a chamfered ring with diagonal corner steps and diagonal jogs on the park paths
  (Wisteria Walk, Fern Boards). Cardinal exits cannot express a diagonal, so wiring and stored
  coordinates disagree at every corner and jog. Root cause analysis is in section 8.
- **Z01 (6 edges).** These six edges are exactly the three
  authored *dodges* of the three forced cell collisions found in section 8: `vr-m12`, `vr-m11`,
  and `vr-m24` were each parked one cell away from where their exits say they are, to avoid
  overlapping `vr-st2`/`vr-m13`/`vr-m19`. Coordinate edits alone cannot fix these — they are on
  the wiring-decision list (section 11).

## 4. Check 2 — Cell Uniqueness

**PASS — no violations.** Within each zone, every room occupies a unique (x, y, z) cell: 54
unique cells in Z05, 150 in Z01. (Coordinate overlap *between* the two zones exists and is
legal — coordinate space is per-zone — and is not reported as a violation.)

Note the flip side: as-built uniqueness was achieved partly by the geometry-breaking dodges
documented in section 3b. The *derived* (exit-faithful) layout does collide — see section 8.

## 5. Check 3 — Cross-Zone Cardinal Exit Inventory

Informational only: cross-zone cardinal exits are MapFrag boundaries automatically, need no
flag, and are exempt from geometric checks. Exactly one pair exists — the expected Tree Arch
gate.

| Src | Dir | Dst | Src zone | Dst zone | Rooms |
|---|---|---|---|---|---|
| r02 | north | vr-v01 | Z05 | Z01 | The Green Gate → The Tree Arch |
| vr-v01 | south | r02 | Z01 | Z05 | The Tree Arch → The Green Gate |

## 6. Check 4 — Up/Down Edge Inventory

14 up/down exit pairs (28 directed edges), all in Z01, all inside or at
the mouths of the seven caves. No geometric requirement applies; each pair always breaks a
fragment. Listed in the seed's canonical direction.

| Src | Dir | Dst | Src room | Dst room |
|---|---|---|---|---|
| vr-c3a | up | vr-f12 | The Fallen Light | The Sink Mouth |
| vr-c4a | up | vr-f14 | The Drop | The Drone Mouth |
| vr-c4e | down | vr-c4f | The Droneway | The Larder Shaft |
| vr-c5a | down | vr-c5b | The Crag Gate | The First Descent |
| vr-c5c | up | vr-c5d | The Under Gallery | The Web Chimney |
| vr-c5e | down | vr-c5f | The Cold Ladder | The Black Span |
| vr-c5f | down | vr-c5g | The Black Span | The Silk Well |
| vr-c6a | down | vr-c6b | The Chitter Gate | The Falling Gallery |
| vr-c6b | down | vr-c6c | The Falling Gallery | The Thousand Steps |
| vr-c6e | down | vr-c6f | The Chitter Hall | The Egg Vault |
| vr-c6h | up | vr-c6i | The Rising Dark | The King's Approach |
| vr-c7b | up | vr-c7c | The Hollow Stair | The Veined Gallery |
| vr-c7e | up | vr-c7f | The Upper Dark | The Wingway |
| vr-c7h | up | vr-c7i | The Deep Turn | The Last Dark |

## 7. Check 5 — Cave-Entrance Determination

For each of the seven Z01 caves: how the entrance is wired, which cave rooms are currently
merged into the surface MapFrag via cardinal exits, the **proposed** boundary-flag placement,
and the **proposed** relocation anchor (full coordinates in section 10). All proposals PENDING
DESIGN RULINGS.

| Cave | Rooms | Entrance wiring | Merged into surface today | Proposed boundary | Proposed relocation |
|---|---|---|---|---|---|
| Spinner's Hollow (`vr-c1*`) | 1 | `vr-v20` east → `vr-c1a` (cardinal) | `vr-c1a` | Flag `vr-v20` east → `vr-c1a` (both directions of the pair) | anchor `vr-c1a` at (2, 11, -1) |
| The Silken Cleft (`vr-c2*`) | 4 | `vr-v22` east → `vr-c2a` (cardinal) | `vr-c2a`, `vr-c2b`, `vr-c2c`, `vr-c2d` | Flag `vr-v22` east → `vr-c2a` (both directions of the pair) | anchor `vr-c2a` at (2, 13, -1) |
| The Whistling Sink (`vr-c3*`) | 6 | `vr-f12` down → `vr-c3a` (up/down) | — | None needed — first transition is already up/down | anchor `vr-c3a` at (1, 25, -1) |
| The Drone Pit (`vr-c4*`) | 8 | `vr-f14` down → `vr-c4a` (up/down) | — | None needed — first transition is already up/down | anchor `vr-c4a` at (3, 27, -1) |
| The Undercrag (`vr-c5*`) | 9 | `vr-m13` east → `vr-c5a` (cardinal) | `vr-c5a` | Flag `vr-m13` east → `vr-c5a` (both directions of the pair) | anchor `vr-c5a` at (2, 39, -1) |
| Chitterdeep (`vr-c6*`) | 10 | `vr-m25` east → `vr-c6a` (cardinal) | `vr-c6a` | Flag `vr-m25` east → `vr-c6a` (both directions of the pair) | anchor `vr-c6a` at (2, 47, -1) |
| Hollowcrown (`vr-c7*`) | 11 | `vr-m40` east → `vr-c7a` (cardinal) | `vr-c7a`, `vr-c7b` | Flag `vr-m40` east → `vr-c7a` (both directions of the pair) | anchor `vr-c7a` at (2, 55, 1) |

**Where surface ends and cave begins (proposed).** The ridge approaches to the Undercrag,
Chitterdeep, and Hollowcrown each run through a named antechamber pair on the surface —
`vr-m08`→`vr-m13` (The Crag Mouth), `vr-m21`→`vr-m25` (The Chittering Mouth), and
`vr-m34`→`vr-m40` (The Crown Mouth). **Proposal:** the mouth rooms (`vr-m13`, `vr-m25`,
`vr-m40`) remain *surface* — they are ridge terrain with cave-facing names — and the cave
begins at `vr-c5a`/`vr-c6a`/`vr-c7a`, with the boundary flag on the mouth→cave exit as tabled
above. The same reading applies to the vale caves: `vr-v20` (The Webbed Gully) and `vr-v22`
(The Cleft Mouth) stay surface; Spinner's Hollow and the Silken Cleft begin at
`vr-c1a`/`vr-c2a`. The alternative — pulling the mouth rooms into their caves by flagging one
exit earlier (e.g. `vr-m08` east → `vr-m13`) — is a design-chat call; nothing in the geometry
forces either choice.

**Hollowcrown merges two rooms today** (`vr-c7a`, `vr-c7b`) because its entrance chain is
cardinal for two steps before the first `up`; the other cardinal-entered caves merge only their
first chamber (Silken Cleft, with no interior up/down at all, merges all four rooms).
The Whistling Sink and the Drone Pit are entered by `down` and merge nothing.

## 8. Check 6 — Embeddability Results

Each **intended** fragment (intra-zone cardinal edges, minus the five proposed boundary pairs
of section 9) was re-derived by BFS from its anchor using exit deltas alone, ignoring stored
coordinates. Anchors: `heart` at (0,0,0) for Z05, `vr-v01` at (0,0,0) for Z01's surface, and
each cave fragment's alphabetically-first room. Where derivation is consistent and
collision-free, the derived positions are the proposed re-authored coordinates (section 10).

### 8a. The ring street cannot close as wired

Summing the direction deltas around `RING_WALK` (35 steps: 9 east,
9 south, 9 west, 8 north) gives
**(0, -1)** — one `north` step short of zero. A walk whose deltas do not sum to
(0, 0) cannot return to its starting cell, so **no coordinate assignment whatsoever can make
the ring street geometrically consistent**. This single defect is the root cause of every Z05
contradiction and collision below: BFS enters the ring at four junctions (`r01`, `r10`, `r18`,
`r24` via the park paths), and the missing step surfaces as disagreement wherever two arcs
meet, with a local pile-up at `r28`/`r29` (The Waste Gate corner).

### 8b. Per-fragment results

| Anchor | Fragment | Rooms | Embeddability |
|---|---|---|---|
| `heart` | Z05 — The Convergence (entire zone) | 54 | **wiring-decision list** — 8 contradictions, 1 cell collision |
| `vr-v01` | Z01 — surface (vale, stair, flats, ridge, villages) | 101 | **wiring-decision list** — 0 contradictions, 3 cell collisions |
| `vr-c1a` | Z01 — Spinner's Hollow interior | 1 | **consistent** — derived coords proposed |
| `vr-c2a` | Z01 — The Silken Cleft interior | 4 | **consistent** — derived coords proposed |
| `vr-c3a` | Z01 — The Whistling Sink interior | 6 | **consistent** — derived coords proposed |
| `vr-c4a` | Z01 — The Drone Pit interior | 7 | **consistent** — derived coords proposed |
| `vr-c4f` | Z01 — The Drone Pit interior | 1 | **consistent** — derived coords proposed |
| `vr-c5a` | Z01 — The Undercrag interior | 1 | **consistent** — derived coords proposed |
| `vr-c5b` | Z01 — The Undercrag interior | 3 | **consistent** — derived coords proposed |
| `vr-c5d` | Z01 — The Undercrag interior | 1 | **consistent** — derived coords proposed |
| `vr-c5f` | Z01 — The Undercrag interior | 3 | **consistent** — derived coords proposed |
| `vr-c5g` | Z01 — The Undercrag interior | 1 | **consistent** — derived coords proposed |
| `vr-c6a` | Z01 — Chitterdeep interior | 1 | **consistent** — derived coords proposed |
| `vr-c6b` | Z01 — Chitterdeep interior | 1 | **consistent** — derived coords proposed |
| `vr-c6c` | Z01 — Chitterdeep interior | 5 | **consistent** — derived coords proposed |
| `vr-c6f` | Z01 — Chitterdeep interior | 1 | **consistent** — derived coords proposed |
| `vr-c6i` | Z01 — Chitterdeep interior | 2 | **consistent** — derived coords proposed |
| `vr-c7a` | Z01 — Hollowcrown interior | 2 | **consistent** — derived coords proposed |
| `vr-c7c` | Z01 — Hollowcrown interior | 3 | **consistent** — derived coords proposed |
| `vr-c7f` | Z01 — Hollowcrown interior | 3 | **consistent** — derived coords proposed |
| `vr-c7i` | Z01 — Hollowcrown interior | 3 | **consistent** — derived coords proposed |

### 8c. Z05 contradictions (8) and collisions (1)

A contradiction means the room was first reached at one position and a second route derives a
different position (the listed edge is where BFS noticed, not where the "error" lives — the
defect is the non-closing walk as a whole).

| Edge where detected | Position already derived | Position via this edge |
|---|---|---|
| `r05` south `r33` | (4, 5, 0) | (3, 3, 0) |
| `r14` west `r15` | (4, -5, 0) | (1, -3, 0) |
| `r15` east `r14` | (2, -3, 0) | (5, -5, 0) |
| `r21` south `r35` | (-2, -5, 0) | (-5, -4, 0) |
| `r28` east `r29` | (-5, 4, 0) | (-4, 4, 0) |
| `r29` west `r28` | (-5, 4, 0) | (-6, 4, 0) |
| `r33` north `r05` | (3, 4, 0) | (4, 6, 0) |
| `r35` north `r21` | (-5, -3, 0) | (-2, -4, 0) |

| Derived cell | Colliding rooms | Room names |
|---|---|---|
| (-5, 4, 0) | `r28`, `r29` | The Waste Gate, Northern Ring — The Return |

### 8d. Z01 surface collisions (3) — 0 contradictions

The Z01 surface embeds with **zero contradictions**: every loop closes. But three derived cells
are forced to hold two rooms each — the Stonestep and Highfold village loops rejoin the ridge
spine one column too close, and the Crag Shelf/Undercrag approach threads the same column.
These are exactly the cells the as-built coordinates dodge (section 3b).

| Derived cell | Colliding rooms | Room names |
|---|---|---|
| (0, 45, 0) | `vr-m19`, `vr-m24` | The High Traverse, Bear's Hollow |
| (1, 38, 0) | `vr-m12`, `vr-st2` | The Crag Shelf, Stonestep Hearths |
| (1, 39, 0) | `vr-m11`, `vr-m13` | The Lion's Backyard, The Crag Mouth |

All 19 cave interior fragments embed cleanly. Single-room fragments are legal and expected:
`vr-c1a` (Spinner's Hollow, cardinal-entered), `vr-c5a` (Undercrag first chamber), `vr-c6a`
(Chitterdeep first chamber), and the up/down-only rooms `vr-c4f`, `vr-c5d`, `vr-c5g`,
`vr-c6b`, `vr-c6f`.

## 9. Consolidated Boundary-Flag Seeding List (PROPOSED)

Every exit proposed to carry the per-exit boundary flag once issue #35 builds it. A flag on an
exit applies to both directions of the pair; rows list the canonical surface → cave direction.
The Tree Arch gate (section 5) is cross-zone and needs no flag. The Whistling Sink and Drone
Pit mouths are up/down and need no flag.

| Src | Dir | Dst | Rooms | Cave |
|---|---|---|---|---|
| `vr-v20` | east | `vr-c1a` | The Webbed Gully → Spinner's Hollow | Spinner's Hollow |
| `vr-v22` | east | `vr-c2a` | The Cleft Mouth → The Entry Cleft | The Silken Cleft |
| `vr-m13` | east | `vr-c5a` | The Crag Mouth → The Crag Gate | The Undercrag |
| `vr-m25` | east | `vr-c6a` | The Chittering Mouth → The Chitter Gate | Chitterdeep |
| `vr-m40` | east | `vr-c7a` | The Crown Mouth → The Crown Gate | Hollowcrown |

5 flagged exit pairs total. (A possible sixth — flagging one Convergence ring exit to
resolve the non-closing walk — is listed as an *option* under wiring decision W1, not proposed
here.)

## 10. Proposed Coordinate Re-Author Plan

**PROPOSED, PENDING DESIGN RULINGS — nothing here is decided.** This section contains only the
fixes achievable by coordinate edits alone (given the section 9 boundary flags). Everything
coordinate edits cannot fix is in section 11.

### 10a. Z01 surface — flatten to the single plane z = 0

The surface fragment's derived embedding is loop-consistent, so its derived coordinates are
adopted wholesale: **every surface room keeps its as-built x,y** (the derivation reproduces
them exactly) **except the three dodge rooms**, and **all z values flatten to 0** (the stair
and ridge climb becomes flavor, not coordinates — z is not elevation). Of 101
surface rooms: 25 unchanged,
70 z-flattened and/or x,y-corrected, 6 withheld pending wiring decisions
W2/W3 (their derived cells collide; both claimants are shown at the derived cell).

| Room | Name | As-built (x, y, z) | Proposed (x, y, z) | Status |
|---|---|---|---|---|
| `vr-c01` | Cragfoot | (0, 31, 4) | (0, 31, 0) | changed |
| `vr-f01` | Stairhead | (0, 20, 4) | (0, 20, 0) | changed |
| `vr-f02` | The Grass Sea | (0, 21, 4) | (0, 21, 0) | changed |
| `vr-f03` | The Wind Rows | (0, 22, 4) | (0, 22, 0) | changed |
| `vr-f04` | The Tall Grass Crossing | (0, 23, 4) | (0, 23, 0) | changed |
| `vr-f05` | Windhome Approach | (0, 24, 4) | (0, 24, 0) | changed |
| `vr-f06` | The Whistling Rise | (0, 25, 4) | (0, 25, 0) | changed |
| `vr-f07` | The Dust Trail | (0, 26, 4) | (0, 26, 0) | changed |
| `vr-f08` | The Low Swale | (0, 27, 4) | (0, 27, 0) | changed |
| `vr-f09` | The Herd Path | (0, 28, 4) | (0, 28, 0) | changed |
| `vr-f10` | The Rabbit Warrens | (-1, 22, 4) | (-1, 22, 0) | changed |
| `vr-f11` | The Grazing Grounds | (1, 23, 4) | (1, 23, 0) | changed |
| `vr-f12` | The Sink Mouth | (1, 25, 4) | (1, 25, 0) | changed |
| `vr-f13` | Prairie Dog Town | (-1, 26, 4) | (-1, 26, 0) | changed |
| `vr-f14` | The Drone Mouth | (1, 27, 4) | (1, 27, 0) | changed |
| `vr-f15` | The Deer Run | (-1, 28, 4) | (-1, 28, 0) | changed |
| `vr-f16` | The Open Sky | (0, 29, 4) | (0, 29, 0) | changed |
| `vr-f17` | The Buffalo Wallow | (1, 29, 4) | (1, 29, 0) | changed |
| `vr-f18` | The Boulder Field | (0, 30, 4) | (0, 30, 0) | changed |
| `vr-hf1` | Highfold Terrace | (1, 44, 7) | (1, 44, 0) | changed |
| `vr-hf2` | Highfold Hearths | (1, 45, 7) | (1, 45, 0) | changed |
| `vr-ll1` | Lastlight Terrace | (1, 52, 10) | (1, 52, 0) | changed |
| `vr-ll2` | Lastlight Hearths | (1, 53, 10) | (1, 53, 0) | changed |
| `vr-m01` | The First Switchback | (0, 32, 5) | (0, 32, 0) | changed |
| `vr-m02` | The Goat Trail | (0, 33, 5) | (0, 33, 0) | changed |
| `vr-m03` | The Shale Turn | (0, 34, 5) | (0, 34, 0) | changed |
| `vr-m04` | The Pine Shelf | (0, 35, 5) | (0, 35, 0) | changed |
| `vr-m05` | The Second Switchback | (0, 36, 6) | (0, 36, 0) | changed |
| `vr-m06` | Stonestep Approach | (0, 37, 6) | (0, 37, 0) | changed |
| `vr-m07` | The Long Traverse | (0, 38, 6) | (0, 38, 0) | changed |
| `vr-m08` | The Crag Shoulder | (0, 39, 6) | (0, 39, 0) | changed |
| `vr-m09` | The Goat Ledges | (1, 33, 5) | (1, 33, 0) | changed |
| `vr-m10` | The Squirrel Pines | (-1, 35, 5) | (-1, 35, 0) | changed |
| `vr-m11` | The Lion's Backyard | (1, 40, 6) | (1, 39, 0) | PENDING (W2/W3) |
| `vr-m12` | The Crag Shelf | (2, 38, 6) | (1, 38, 0) | PENDING (W2/W3) |
| `vr-m13` | The Crag Mouth | (1, 39, 6) | (1, 39, 0) | PENDING (W2/W3) |
| `vr-m14` | The Wind Gap | (0, 40, 7) | (0, 40, 0) | changed |
| `vr-m15` | The Third Switchback | (0, 41, 7) | (0, 41, 0) | changed |
| `vr-m16` | The Grey Ridge | (0, 42, 7) | (0, 42, 0) | changed |
| `vr-m17` | The Windbreak | (0, 43, 7) | (0, 43, 0) | changed |
| `vr-m18` | Highfold Approach | (0, 44, 7) | (0, 44, 0) | changed |
| `vr-m19` | The High Traverse | (0, 45, 8) | (0, 45, 0) | PENDING (W2/W3) |
| `vr-m20` | The Fourth Switchback | (0, 46, 8) | (0, 46, 0) | changed |
| `vr-m21` | The Chitter Shoulder | (0, 47, 8) | (0, 47, 0) | changed |
| `vr-m22` | The Goat Walk | (1, 41, 7) | (1, 41, 0) | changed |
| `vr-m23` | The Windbreak Pines | (-1, 43, 7) | (-1, 43, 0) | changed |
| `vr-m24` | Bear's Hollow | (-1, 45, 7) | (0, 45, 0) | PENDING (W2/W3) |
| `vr-m25` | The Chittering Mouth | (1, 47, 8) | (1, 47, 0) | changed |
| `vr-m26` | The Grey Vista | (-1, 46, 8) | (-1, 46, 0) | changed |
| `vr-m27` | The Thin Air | (0, 48, 9) | (0, 48, 0) | changed |
| `vr-m28` | The Fifth Switchback | (0, 49, 9) | (0, 49, 0) | changed |
| `vr-m29` | The Stone Teeth | (0, 50, 9) | (0, 50, 0) | changed |
| `vr-m30` | The Stunted Rise | (0, 51, 10) | (0, 51, 0) | changed |
| `vr-m31` | Lastlight Approach | (0, 52, 10) | (0, 52, 0) | changed |
| `vr-m32` | The Knife Edge | (0, 53, 10) | (0, 53, 0) | changed |
| `vr-m33` | The Sixth Switchback | (0, 54, 10) | (0, 54, 0) | changed |
| `vr-m34` | The Crown Shoulder | (0, 55, 11) | (0, 55, 0) | changed |
| `vr-m35` | The Green Ascent | (0, 56, 11) | (0, 56, 0) | changed |
| `vr-m36` | The High Fold Ledge | (1, 49, 9) | (1, 49, 0) | changed |
| `vr-m37` | The Stunted Pines | (-1, 51, 10) | (-1, 51, 0) | changed |
| `vr-m38` | Lion's Watch | (-1, 53, 10) | (-1, 53, 0) | changed |
| `vr-m39` | Bear's Throne | (1, 54, 10) | (1, 54, 0) | changed |
| `vr-m40` | The Crown Mouth | (1, 55, 11) | (1, 55, 0) | changed |
| `vr-m41` | The Last Stair | (0, 57, 12) | (0, 57, 0) | changed |
| `vr-m42` | The Cloud Rail | (1, 56, 11) | (1, 56, 0) | changed |
| `vr-m43` | The Silent Col | (-1, 48, 9) | (-1, 48, 0) | changed |
| `vr-rm1` | Reedmere Shore | (-1, 9, 0) | (-1, 9, 0) | unchanged |
| `vr-rm2` | Reedmere Huts | (-1, 10, 0) | (-1, 10, 0) | unchanged |
| `vr-rm3` | Reedmere Jetty | (-2, 9, 0) | (-2, 9, 0) | unchanged |
| `vr-s1` | The First Steps | (0, 15, 1) | (0, 15, 0) | changed |
| `vr-s2` | The Low Vista | (0, 16, 1) | (0, 16, 0) | changed |
| `vr-s3` | The Long Climb | (0, 17, 2) | (0, 17, 0) | changed |
| `vr-s4` | The High Vista | (0, 18, 3) | (0, 18, 0) | changed |
| `vr-s5` | The Rim | (0, 19, 4) | (0, 19, 0) | changed |
| `vr-st1` | Stonestep Terrace | (1, 37, 6) | (1, 37, 0) | changed |
| `vr-st2` | Stonestep Hearths | (1, 38, 6) | (1, 38, 0) | PENDING (W2/W3) |
| `vr-v01` | The Tree Arch | (0, 0, 0) | (0, 0, 0) | unchanged |
| `vr-v02` | The Green Path | (0, 1, 0) | (0, 1, 0) | unchanged |
| `vr-v03` | The Narrowing Way | (0, 2, 0) | (0, 2, 0) | unchanged |
| `vr-v04` | The Rocky Descent | (0, 3, 0) | (0, 3, 0) | unchanged |
| `vr-v05` | The Riverbank | (0, 4, 0) | (0, 4, 0) | unchanged |
| `vr-v06` | Bear Hollow | (1, 3, 0) | (1, 3, 0) | unchanged |
| `vr-v07` | Fordwatch | (0, 5, 0) | (0, 5, 0) | unchanged |
| `vr-v08` | The Valley Floor | (0, 6, 0) | (0, 6, 0) | unchanged |
| `vr-v09` | The Fern Meadow | (0, 7, 0) | (0, 7, 0) | unchanged |
| `vr-v10` | The Cliffside Path | (0, 8, 0) | (0, 8, 0) | unchanged |
| `vr-v11` | Reedmere Approach | (0, 9, 0) | (0, 9, 0) | unchanged |
| `vr-v12` | The Old Orchard | (0, 10, 0) | (0, 10, 0) | unchanged |
| `vr-v13` | The Bramble Cut | (0, 11, 0) | (0, 11, 0) | unchanged |
| `vr-v14` | The Riverfork | (0, 12, 0) | (0, 12, 0) | unchanged |
| `vr-v15` | The Cleft Wall | (0, 13, 0) | (0, 13, 0) | unchanged |
| `vr-v16` | The Vanished Road | (0, 14, 0) | (0, 14, 0) | unchanged |
| `vr-v17` | Otter Bend | (-1, 7, 0) | (-1, 7, 0) | unchanged |
| `vr-v18` | The Talon Ledge | (1, 8, 0) | (1, 8, 0) | unchanged |
| `vr-v19` | Boar Wallow | (1, 10, 0) | (1, 10, 0) | unchanged |
| `vr-v20` | The Webbed Gully | (1, 11, 0) | (1, 11, 0) | unchanged |
| `vr-v21` | The Shallows | (-1, 12, 0) | (-1, 12, 0) | unchanged |
| `vr-v22` | The Cleft Mouth | (1, 13, 0) | (1, 13, 0) | unchanged |
| `vr-vc1` | The Verdant Crown | (0, 58, 12) | (0, 58, 0) | changed |
| `vr-w1` | Windhome Circle | (-1, 24, 4) | (-1, 24, 0) | changed |
| `vr-w2` | Windhome Tents | (-1, 25, 4) | (-1, 25, 0) | changed |

### 10b. Cave relocations

Cave interiors all embed cleanly; each fragment keeps its derived internal layout and is
anchored as follows: the first chamber sits one cell beyond its mouth (cardinal mouths) or
directly beneath its entrance (up/down mouths) at z = −1; deeper/higher sub-fragments step one
z-level per up/down transition at the same x,y. Hollowcrown ascends, so it occupies z = +1…+4.
The Drone Pit anchor is shifted two columns east of its entrance so its plane doesn't overlap
the Whistling Sink's (both are z = −1 off the flats). The full proposed assignment below is
verified collision-free against the flattened surface and every other cave.

| Room | Name | Cave | As-built (x, y, z) | Proposed (x, y, z) |
|---|---|---|---|---|
| `vr-c1a` | Spinner's Hollow | Spinner's Hollow | (2, 11, 0) | (2, 11, -1) |
| `vr-c2a` | The Entry Cleft | The Silken Cleft | (2, 13, 0) | (2, 13, -1) |
| `vr-c2b` | The Silk Gallery | The Silken Cleft | (2, 14, 0) | (2, 14, -1) |
| `vr-c2c` | The Choke | The Silken Cleft | (2, 15, 0) | (2, 15, -1) |
| `vr-c2d` | The Matron's Larder | The Silken Cleft | (2, 16, 0) | (2, 16, -1) |
| `vr-c3a` | The Fallen Light | The Whistling Sink | (1, 25, 3) | (1, 25, -1) |
| `vr-c3b` | The Whistle Throat | The Whistling Sink | (1, 26, 3) | (1, 26, -1) |
| `vr-c3c` | The Wind Gallery | The Whistling Sink | (1, 27, 3) | (1, 27, -1) |
| `vr-c3d` | The Bone Niche | The Whistling Sink | (2, 27, 3) | (2, 27, -1) |
| `vr-c3e` | The Deep Hum | The Whistling Sink | (1, 28, 3) | (1, 28, -1) |
| `vr-c3f` | The Whistler's Hollow | The Whistling Sink | (1, 29, 3) | (1, 29, -1) |
| `vr-c4a` | The Drop | The Drone Pit | (3, 27, 3) | (3, 27, -1) |
| `vr-c4b` | The Buzzing Dark | The Drone Pit | (3, 28, 3) | (3, 28, -1) |
| `vr-c4c` | The Honeycomb Walls | The Drone Pit | (3, 29, 3) | (3, 29, -1) |
| `vr-c4d` | The Husk Pile | The Drone Pit | (4, 29, 3) | (4, 29, -1) |
| `vr-c4e` | The Droneway | The Drone Pit | (3, 30, 3) | (3, 30, -1) |
| `vr-c4f` | The Larder Shaft | The Drone Pit | (3, 30, 2) | (3, 30, -2) |
| `vr-c4g` | The Low Chamber | The Drone Pit | (3, 31, 3) | (3, 31, -1) |
| `vr-c4h` | The Dronemother's Vault | The Drone Pit | (3, 32, 3) | (3, 32, -1) |
| `vr-c5a` | The Crag Gate | The Undercrag | (2, 39, 6) | (2, 39, -1) |
| `vr-c5b` | The First Descent | The Undercrag | (2, 39, 5) | (2, 39, -2) |
| `vr-c5c` | The Under Gallery | The Undercrag | (2, 40, 5) | (2, 40, -2) |
| `vr-c5d` | The Web Chimney | The Undercrag | (2, 40, 6) | (2, 40, -1) |
| `vr-c5e` | The Cold Ladder | The Undercrag | (2, 41, 5) | (2, 41, -2) |
| `vr-c5f` | The Black Span | The Undercrag | (2, 41, 4) | (2, 41, -3) |
| `vr-c5g` | The Silk Well | The Undercrag | (2, 41, 3) | (2, 41, -4) |
| `vr-c5h` | The Deep Landing | The Undercrag | (2, 42, 4) | (2, 42, -3) |
| `vr-c5i` | The Weaver's Vault | The Undercrag | (2, 43, 4) | (2, 43, -3) |
| `vr-c6a` | The Chitter Gate | Chitterdeep | (2, 47, 8) | (2, 47, -1) |
| `vr-c6b` | The Falling Gallery | Chitterdeep | (2, 47, 7) | (2, 47, -2) |
| `vr-c6c` | The Thousand Steps | Chitterdeep | (2, 47, 6) | (2, 47, -3) |
| `vr-c6d` | The Molt Chamber | Chitterdeep | (3, 47, 6) | (3, 47, -3) |
| `vr-c6e` | The Chitter Hall | Chitterdeep | (2, 48, 6) | (2, 48, -3) |
| `vr-c6f` | The Egg Vault | Chitterdeep | (2, 48, 5) | (2, 48, -4) |
| `vr-c6g` | The Long Crawl | Chitterdeep | (2, 49, 6) | (2, 49, -3) |
| `vr-c6h` | The Rising Dark | Chitterdeep | (2, 50, 6) | (2, 50, -3) |
| `vr-c6i` | The King's Approach | Chitterdeep | (2, 50, 7) | (2, 50, -2) |
| `vr-c6j` | The Chittering Throne | Chitterdeep | (2, 51, 7) | (2, 51, -2) |
| `vr-c7a` | The Crown Gate | Hollowcrown | (2, 55, 11) | (2, 55, 1) |
| `vr-c7b` | The Hollow Stair | Hollowcrown | (2, 56, 11) | (2, 56, 1) |
| `vr-c7c` | The Veined Gallery | Hollowcrown | (2, 56, 12) | (2, 56, 2) |
| `vr-c7d` | The Glittering Seam | Hollowcrown | (3, 56, 12) | (3, 56, 2) |
| `vr-c7e` | The Upper Dark | Hollowcrown | (2, 57, 12) | (2, 57, 2) |
| `vr-c7f` | The Wingway | Hollowcrown | (2, 57, 13) | (2, 57, 3) |
| `vr-c7g` | The Fallen Shaft | Hollowcrown | (3, 57, 13) | (3, 57, 3) |
| `vr-c7h` | The Deep Turn | Hollowcrown | (2, 58, 13) | (2, 58, 3) |
| `vr-c7i` | The Last Dark | Hollowcrown | (2, 58, 14) | (2, 58, 4) |
| `vr-c7j` | The Devourer's Approach | Hollowcrown | (2, 59, 14) | (2, 59, 4) |
| `vr-c7k` | The Devourer's Hoard | Hollowcrown | (2, 60, 14) | (2, 60, 4) |

### 10c. Z05 — the Convergence park interior

The heart, the four park paths, and their jogs re-author cleanly from `heart` at (0,0,0) — the
derived positions straighten the Wisteria Walk and Fern Boards diagonals into pure cardinal
chains. **The 35 ring rooms and the two smithy rooms are excluded**: the ring cannot embed
until wiring decision W1 is ruled, and the smithy hangs off ring room `r01`, so its final cells
follow the ring's. The park-path junction cells below (`br3`, `bw5`, `fb4`, `ww4` endpoints)
fix where the ring rooms `r10`/`r18`/`r24`/`r01` must land once W1 is resolved.

| Room | Name | As-built (x, y, z) | Proposed (x, y, z) | Status |
|---|---|---|---|---|
| `heart` | Heart of the Convergence | (0, 0, 0) | (0, 0, 0) | unchanged |
| `ww1` | First Steps on the Wisteria Walk | (0, 1, 0) | (0, 1, 0) | unchanged |
| `ww2` | Along the Wisteria Walk | (-1, 2, 0) | (-1, 1, 0) | changed |
| `ww3` | Deeper on the Wisteria Walk | (-1, 3, 0) | (-1, 2, 0) | changed |
| `ww4` | Northern Edge of the Wisteria Walk | (-1, 4, 0) | (-1, 3, 0) | changed |
| `br1` | Onto the Bamboo Run | (1, 0, 0) | (1, 0, 0) | unchanged |
| `br2` | Along the Bamboo Run | (2, 0, 0) | (2, 0, 0) | unchanged |
| `br3` | End of the Bamboo Run | (3, 0, 0) | (3, 0, 0) | unchanged |
| `bw1` | Onto the Basalt Way | (0, -1, 0) | (0, -1, 0) | unchanged |
| `bw2` | Along the Basalt Way | (1, -1, 0) | (1, -1, 0) | unchanged |
| `bw3` | Deeper on the Basalt Way | (1, -2, 0) | (1, -2, 0) | unchanged |
| `bw4` | Near the Southern Edge of the Basalt Way | (1, -3, 0) | (1, -3, 0) | unchanged |
| `bw5` | Southern Edge of the Basalt Way | (1, -4, 0) | (1, -4, 0) | unchanged |
| `fb1` | Onto the Fern Boards | (-1, 0, 0) | (-1, 0, 0) | unchanged |
| `fb2` | Along the Fern Boards | (-2, 1, 0) | (-2, 0, 0) | changed |
| `fb3` | Deeper on the Fern Boards | (-3, 1, 0) | (-3, 0, 0) | changed |
| `fb4` | End of the Fern Boards | (-4, 1, 0) | (-4, 0, 0) | changed |

## 11. Wiring-Decision List

Items coordinate edits **cannot** fix. Each returns to the design chat with options; **no
recommendation is selected here**. Any option that rewires an exit triggers the project's
geography-audit rule: NPC dialogue compass-direction re-checks for every affected room.

### W1 — The Convergence ring street does not close (35 steps, delta sum (0, -1))

Affects all 35 ring rooms, the smithy pair, and the four park-path junctions; manifests as the
8 contradictions and the `r28`/`r29` collision in section 8c.

- **Option A — add a 36th ring room.** Insert one room into the west leg's `north` run (between
  `r35` and `r28`, exact spot free), making the walk 9 east / 9 south / 9 west / 9 north. The
  ring closes as a true 10×10 circuit; every ring room then re-authors by derivation. Adds a
  room (name, description, area) and rewires two exit pairs → NPC dialogue re-checks.
- **Option B — flag one ring exit as a MapFrag boundary.** Pick one seam (e.g.
  `r32` east → `r01`, "Closing the Loop") and flag it under the #35 mechanism. Connectivity is
  untouched; the ring becomes a 35-room *arc* geometrically and the map renders it with a
  fragment break. No room changes, no NPC re-checks; costs a visible seam on the city map.
- **Option C — redirect one walk step.** Change one step's direction (e.g. absorb the extra
  `south` by making one south-leg step `west`), reshaping the ring to a closable 35-step
  circuit that is no longer rectangular. No new rooms, but the reshape moves many stored
  coordinates and rewires at least one exit pair → NPC dialogue re-checks.

### W2 — Stonestep village loop / Crag approach: derived cells (1, 38, 0) and (1, 39, 0) each hold two rooms

`vr-st2` (Stonestep Hearths) collides with `vr-m12` (The Crag Shelf); `vr-m11` (The Lion's
Backyard) collides with `vr-m13` (The Crag Mouth). The village loop `vr-m06 → vr-st1 → vr-st2 →
vr-m11` and the eastern offshoots `vr-m07 → vr-m12`, `vr-m08 → vr-m13` all thread column x = 1
at y = 38–39. As-built coordinates dodge by parking `vr-m12` at x = 2 and `vr-m11` at y = 40,
breaking geometry (section 3b).

- **Option A — push the village one column east.** Rewire `vr-st1`'s chain so `vr-st2` and
  `vr-m11` derive at x = 2 (e.g. `vr-st1` east → new/turned step, then north). Requires exit
  rewiring (and possibly one new room) → NPC dialogue re-checks.
- **Option B — flag the village as its own fragment.** Flag `vr-m06` east → `vr-st1` (or
  `vr-st2` north → `vr-m11`) as a boundary; the village embeds independently and keeps its
  as-built dodge cells. No rewiring, no NPC re-checks; the village renders as its own MapFrag.
- **Option C — retarget the offshoots.** Move `vr-m12` and `vr-m13` off column x = 1 by
  changing their approach directions (e.g. `vr-m07` west instead of east). Rewires two exit
  pairs → NPC dialogue re-checks; changes the ridge's east-facing shape.

### W3 — Highfold village loop: derived cell (0, 45, 0) holds two rooms

`vr-m24` (Bear's Hollow) collides with `vr-m19` (The High Traverse): the loop `vr-m18 → vr-hf1
→ vr-hf2 → (west) → vr-m24` lands its last room back on the spine column. As-built dodge parks
`vr-m24` at x = −1.

- **Option A — hang Bear's Hollow north of the loop.** Rewire `vr-hf2` north → `vr-m24`
  (instead of west); `vr-m24` derives at (1, 46, 0), collision-free. One exit pair rewired →
  NPC dialogue re-checks.
- **Option B — flag the loop's return edge.** Flag `vr-hf2` west → `vr-m24` as a boundary;
  `vr-m24` becomes a one-room fragment (an aggro pocket) and keeps its dodge cell (−1, 45, 0).
  No rewiring, no NPC re-checks.
- **Option C — flag the village entrance.** Flag `vr-m18` east → `vr-hf1`; the whole Highfold
  loop (3 rooms + `vr-m24`) embeds as its own fragment at its dodge coordinates. No rewiring,
  no NPC re-checks; Highfold renders as its own MapFrag.

## 12. MapFrag Inventory

Fragments = connected components over unflagged intra-zone cardinal exits. Rooms with only
up/down exits are single-room fragments.

### 12a. As-built today (no flags exist): 16 fragments, 204 rooms

| Fragment | Anchor | Rooms |
|---|---|---|
| Z01 — surface | `vr-c01` | 110 |
| Z05 — The Convergence | `br1` | 54 |
| Z01 — The Drone Pit (`vr-c4a` …) | `vr-c4a` | 7 |
| Z01 — The Whistling Sink (`vr-c3a` …) | `vr-c3a` | 6 |
| Z01 — Chitterdeep (`vr-c6c` …) | `vr-c6c` | 5 |
| Z01 — The Undercrag (`vr-c5b` …) | `vr-c5b` | 3 |
| Z01 — The Undercrag (`vr-c5f` …) | `vr-c5f` | 3 |
| Z01 — Hollowcrown (`vr-c7c` …) | `vr-c7c` | 3 |
| Z01 — Hollowcrown (`vr-c7f` …) | `vr-c7f` | 3 |
| Z01 — Hollowcrown (`vr-c7i` …) | `vr-c7i` | 3 |
| Z01 — Chitterdeep (`vr-c6i` …) | `vr-c6i` | 2 |
| Z01 — The Drone Pit (`vr-c4f` …) | `vr-c4f` | 1 |
| Z01 — The Undercrag (`vr-c5d` …) | `vr-c5d` | 1 |
| Z01 — The Undercrag (`vr-c5g` …) | `vr-c5g` | 1 |
| Z01 — Chitterdeep (`vr-c6b` …) | `vr-c6b` | 1 |
| Z01 — Chitterdeep (`vr-c6f` …) | `vr-c6f` | 1 |

### 12b. Projected after the proposed plan: 21 fragments, 204 rooms

Projection applies the five proposed boundary flags of section 9 only. **Unresolved
wiring-decision items are excluded from the projection**: W1 does not change Z05's fragment
count under options A/C but would split it 35 + 19 under option B; W2/W3 likewise leave the
Z01 surface fragment intact under their rewiring options but would split off village fragments
(3, 4, or 1 rooms) under their flag options.

| Fragment | Anchor | Rooms |
|---|---|---|
| Z01 — surface | `vr-v01` | 101 |
| Z05 — The Convergence | `heart` | 54 |
| Z01 — The Drone Pit (`vr-c4a` …) | `vr-c4a` | 7 |
| Z01 — The Whistling Sink (`vr-c3a` …) | `vr-c3a` | 6 |
| Z01 — Chitterdeep (`vr-c6c` …) | `vr-c6c` | 5 |
| Z01 — The Silken Cleft (`vr-c2a` …) | `vr-c2a` | 4 |
| Z01 — The Undercrag (`vr-c5b` …) | `vr-c5b` | 3 |
| Z01 — The Undercrag (`vr-c5f` …) | `vr-c5f` | 3 |
| Z01 — Hollowcrown (`vr-c7c` …) | `vr-c7c` | 3 |
| Z01 — Hollowcrown (`vr-c7f` …) | `vr-c7f` | 3 |
| Z01 — Hollowcrown (`vr-c7i` …) | `vr-c7i` | 3 |
| Z01 — Chitterdeep (`vr-c6i` …) | `vr-c6i` | 2 |
| Z01 — Hollowcrown (`vr-c7a` …) | `vr-c7a` | 2 |
| Z01 — Spinner's Hollow (`vr-c1a` …) | `vr-c1a` | 1 |
| Z01 — The Drone Pit (`vr-c4f` …) | `vr-c4f` | 1 |
| Z01 — The Undercrag (`vr-c5a` …) | `vr-c5a` | 1 |
| Z01 — The Undercrag (`vr-c5d` …) | `vr-c5d` | 1 |
| Z01 — The Undercrag (`vr-c5g` …) | `vr-c5g` | 1 |
| Z01 — Chitterdeep (`vr-c6a` …) | `vr-c6a` | 1 |
| Z01 — Chitterdeep (`vr-c6b` …) | `vr-c6b` | 1 |
| Z01 — Chitterdeep (`vr-c6f` …) | `vr-c6f` | 1 |

---

*End of audit. All proposals PENDING DESIGN RULINGS (issue #42 → design chat → Version 20 fix
issues → the map brief).*
