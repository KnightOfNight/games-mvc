## 2. World Model

### 2.1 The Lore of the Fracture

Imagine a Venn diagram of universes. Each universe is its own reality — fantasy, cyberpunk, gothic horror, post-apocalyptic, steampunk, cosmic. At some point in the deep past, these realities collided. Not violently destroyed — *overlapped*. Where any two universes touch, there is tension, bleed-through, anachronism. A fantasy forest where neon signs flicker between the trees. A cyberpunk alley where a knight in plate armor wanders, confused.

But where *all* of them meet — the dead center of the Venn diagram — something unexpected happened. The forces cancelled each other out. The chaos balanced into stillness. A neutral zone emerged, not belonging to any single universe, touched by all of them.

That is **The Convergence**.

Nobody fully understands it. Scholars debate what caused the collision. Some zones have adapted to their neighbors; others remain hostile to anything foreign. This tension is a primary driver of narrative and conflict.

**How players arrive:** Death in a home universe — an honorable death, a death that found peace — is what brings a character to the Convergence. They did not choose to come. The Convergence is not a second chance handed out freely; it is where the worthy end up when their story in one world closes. They wake at the Obelisk, whole, in a place they have never been, with everything still ahead of them.

### 2.2 Zone Architecture

The world is divided into **Zones**, each with a dominant genre identity. Within each zone are **Areas**, which contain individual **Rooms**.

```
World
└── Zone (e.g., "The Neon Sprawl" — cyberpunk city)
    └── Area (e.g., "The Underbelly Markets")
        └── Room (e.g., "Black Market Stall #7")
```

#### Zone Types (v1 set)

|Zone ID|Name               |Genre Tone                                      |Danger Level|
|-------|-------------------|------------------------------------------------|------------|
|Z01    |The Verdant Reach  |Classic fantasy wilderness                      |Beginner    |
|Z02    |Ashenveil Cathedral|Dark gothic horror                              |Intermediate|
|Z03    |The Neon Sprawl    |Cyberpunk megacity                              |Intermediate|
|Z04    |The Blasted Flats  |Post-apocalyptic wasteland                      |Advanced    |
|Z05    |The Convergence    |All genres collide — the world's central hub    |Sanctuary   |
|Z06    |The Iron Deeps     |Steampunk underground                           |Advanced    |
|Z07    |The Pale Shore     |Cosmic horror / lovecraftian ocean              |Endgame     |
|Z08    |The Wastelands     |Infinite scaling zone — always level-appropriate|All levels  |

**The Convergence (Z05)** is the game's social hub — a permanent sanctuary zone where PvP is disabled, vendors of all types exist, and players from all backgrounds congregate. It is the point where all universes overlap and stillness holds. It is also the default logout and recall destination. The starting area within The Convergence is **Infinity City** — see Section 2.9.

**The Wastelands (Z08)** is a special infinite scaling zone — see Section 2.7.

### 2.3 Areas

An **Area** is a named grouping of rooms within a zone that share a common ambient context. Areas are the middle layer of the world hierarchy — they sit between Zone and Room, giving world builders a tool to express shared atmosphere without repeating it in every room description.

```
Zone → Area → Room
```

Areas are **optional** — a room does not have to belong to an area. Standalone rooms (a remote wilderness clearing, a unique landmark) exist without one. But any multi-room location with a coherent identity — a marketplace, a dungeon wing, a ship, a temple — should be modelled as an Area.

#### What an Area Contains

- **Name** — the location name players see as part of their room header (e.g., "The Eastern Bazaar")
- **Area description** — shared ambient prose that applies to all rooms in the area. Describes the general atmosphere: sounds, smells, lighting, the feel of the place. Written once, displayed in every room that belongs to the area.

#### How Areas Appear to Players

When a player enters a room that belongs to an area, their output has two layers:

1. **Area description** (if present) — the shared ambient text, shown above the room-specific description, rendered in the Area's `theme_color` **(v21)** — the same color as the Area segment of the location bar
1. **Room description** — the specific detail of this individual space, rendered in value-color **(v21)** — the same near-white as the location bar's room segment

(The bracketed `[ Area Name — Room Name ]` header was removed in v20 — place identity lives in the location bar. The v21 per-level prose colors make the two paragraphs visually distinct where they previously read as one undifferentiated block; the server delivers them as separate payload fields.)

**Example — The Eastern Bazaar:**

```
The Eastern Bazaar hums with commerce. Vendors call out from their stalls,
the smell of spices mingles with hot metal and sawdust, and the clatter of
coins fills the air. Torches line the perimeter, casting warm light across
a dozen competing storefronts.

A scarred dwarf stands behind a worn wooden counter, eyeing you appraisingly.
Racks of swords, axes, and shields cover every wall. A grinding wheel spins
slowly in the corner.

Exits: north, out.
```

For a room without an area, the header is just `[ Room Name ]` and no area text is shown — identical to previous behavior.

#### Builder Guidelines

- The **area description** describes the environment — what it feels, sounds, and smells like. It does not describe specific objects or characters that only exist in one room.
- Each **room description** describes what is specific and unique to that room — the vendor, the furniture, the view, the hazard.
- Keep area descriptions atmospheric and timeless. Room descriptions can reference specific NPCs and items.
- An area with no `area_description` still serves a purpose — it groups rooms for admin filtering, minimap clustering, and potential future uses — but players will not see any extra text.

#### Minimap Integration

Rooms belonging to the same area are visually clustered on the minimap. The area name appears as a label on the minimap when the player is inside it. This helps players understand the spatial relationship between rooms that share a common location.

### 2.4 Rooms

Each room is the atomic unit of the world. Rooms contain:

- **Short name** — displayed in the **location bar** as the room segment of the `Zone: Area: Room` breadcrumb. **(v20)** The bracketed in-pane room header (`[ Area — Room ]`) is removed: the output pane clears on every room entry (ruled deliberate), so the render begins directly with the description prose and place identity lives in the location bar alone. A **zone-colored separator bar** (solid, **3px (v21)**, rounded, `Zone.theme_color` at ~0.75 opacity, one text line of vertical presence, aria-hidden) closes each room render, framing *where you are* against *what happens next*
- **Long description** — the room-specific prose a player reads on entering (first visit) or using the `look` command
- **Brief description** — required on every room; non-null, non-blank — no fallback path exists. **Rendering semantics (v19):** the first entry to a room always shows the full text (area description if any + long description) in both modes; revisits with `brief_mode` on show the brief description only (no area text); revisits with `brief_mode` off show the full text; `look` always shows the full text. The area description renders exactly when the long description does — never with the brief line. `brief_mode` defaults to **on** for new characters
- **Area** — optional parent area providing shared ambient context (see 2.3)
- **Exit list** — directional links to adjacent rooms (N, S, E, W, U, D, and custom named exits)
- **Blocked exit messages** — six optional per-direction fields (`no_exit_north_msg`, `no_exit_south_msg`, `no_exit_east_msg`, `no_exit_west_msg`, `no_exit_up_msg`, `no_exit_down_msg`). When a player attempts to move in a direction with no exit, the room's custom message for that direction is sent if set; otherwise the hardcoded default is used. Defaults: cardinals → `"There is no exit in that direction."`; up → `"There is nothing above you."`; down → `"You'd have to dig to go that way."` All six fields are optional; a room with none set uses all defaults.
- **Flags** — booleans that modify room behavior (see below)
- **Contents** — current list of players, NPCs, and items present

#### Room Flags

|Flag        |Effect                                                             |
|------------|-------------------------------------------------------------------|
|`SAFE`      |No combat allowed, NPCs won't aggro                                |
|`PVP`       |PvP is enabled in this room                                        |
|`DARK`      |Players need a light source to see descriptions                    |
|`INDOORS`   |Weather effects don't apply                                        |
|`WATER`     |Swimming/drowning rules apply                                      |
|`NO_RECALL` |Players cannot use recall/teleport abilities                       |
|`RADIATION` |Periodic radiation damage (wasteland zones)                        |
|`HOLY`      |Undead and demonic entities take passive damage                    |
|`MAGIC_DEAD`|Spell and tech abilities disabled                                  |
|`SCALED`    |Room and its contents scale to entering player's level (Wastelands)|

### 2.5 The Map System — Coordinates, MapFrags, and the Client Map (v20)

**Coordinates are the map's positional source of truth; exits remain the connectivity source of truth.** Every room carries `coord_x / coord_y / coord_z` in a **per-zone** coordinate space — pure *map-space*, not physical space: **z is not elevation**, it is a drawing plane. One room per (zone, x, y, z) cell, no exceptions.

**The core invariant:** every *unflagged* cardinal exit (N/S/E/W) between same-zone rooms lands grid-adjacent at the same z (north = (0,+1,0), etc.). The seed's verification enforces this — plus cell uniqueness and flag symmetry — on every reseed, so the world cannot drift out of drawability.

**Boundary flags:** four per-room booleans (`exit_{n/s/e/w}_boundary`, cardinals only) mark exits that are deliberate map seams — a flagged exit has no geometric requirement and severs the map there. Cross-zone cardinal exits are boundaries automatically. Up/down exits have no geometric requirement and always break the map. Any non-cardinal movement verb, present or future, is map-neutral by definition. In Z01, exactly five cave mouths carry the flag (the valley caves and the three Ridge delve approaches).

**MapFrags:** a MapFrag is a *derived, never stored* connected component of rooms linked by unflagged intra-zone cardinal exits. It is what one drawn map shows. The Z01 surface is one 101-room fragment; each cave interior is its own; a room with no cardinal exits is a legal single-room fragment. Exits between fragments still work exactly as ever — **exits are transitions**; the map simply starts a new drawing on the far side.

**Fog of war:** per-character and permanent, via `RoomVisit` — recorded **at arrival** in every path (move, travel, flee, respawn, connect), independent of description rendering. Unvisited rooms are never drawn.

**The payload (v22 — Maps V2, #82):** server-computed on connect and on every room change. Two kinds of entry, and nothing else:

- **Discovered rooms** — the visited members of the current MapFrag (the current room always included) — carry coordinates, `here` on the current room only, `travel_node` (a `TravelNode` exists for the room), `agro` (**configuration, not instance state**: true iff any `RoomSpawn` in the room references an aggressive definition — a dead or unspawned instance still flags), per-cardinal exit status (`known`/`unknown` by destination `RoomVisit`; `gate-known`/`gate-unknown` for boundary-flagged or cross-zone exits), and `up`/`down` tri-state by destination visit.
- **Frontier rooms** — unvisited fragment rooms one unflagged intra-zone cardinal step from a discovered room — carry **exactly `{x, y, discovered: false}` and nothing else, ever**. This is **masking by construction**: an undiscovered room discloses existence only, enforced in the wire format — the server never relies on the client to hide anything. Nothing deeper than the frontier enters the payload; gate destinations never enter the room set at all (they are looked up only for their visit bit).

The build is a **bounded, constant number of queries** (five; guarded by an `assertNumQueries` regression test) — the standing #107 per-tick/per-operation query discipline applied to the map. The client is dumb: it renders exactly what it is sent.

**The client map (v22 — Maps V2):** a fixed **300×300px square at the bottom of the right pane**, north up, a **7×7-cell window** centered on the current room, drawn inside a **pinned 16px margin** (268×268 drawable area — #115's breathing room, solved inside the renderer, not the pane CSS). The visual language runs on the named four-color vocabulary, with one rule of grammar — **stroke color carries room state; solid fills mean points; value-vs-muted carries known-vs-unknown everywhere**:

- **Rooms** — hollow circles (r=10, 2px stroke) in value-color; **agro-color stroke** when the room has aggressive spawns configured. The **here-dot** is a solid key-color dot (r=6) atop the current room's glyph — the map's one key fact.
- **Travel nodes** — the **octagon** (circumradius 12, 4px stroke, flat sides to the cardinals): one glyph for shard and sphere rooms alike — the distinction lives in the travel listing. **Octagons never agro**: no travel-node room may carry an aggressive spawn, a permanent seed-verify invariant.
- **Gates** — an 8px connector from the glyph's outer stroke edge into a solid outward-pointing triangle; value-color if the destination has been visited, muted if not (#53's defect, closed by design — a passed gate is no longer gray).
- **Frontier rooms** — **solid muted dots at half diameter (r=5)** with muted link lines, and **no exits of their own** (the terminus rule): the map admits they exist and says nothing more.
- **Stubs** — solid half-cell lines for exits whose destination lies outside the window: value for a known path continuing off-screen, muted for an unknown one. The old dashed-stub and boundary-tick vocabulary is retired entirely.
- **U/D badges** — independent 14px bold letter badges at the upper-right (U) and lower-right (D) corners, each colored by its own destination's visit state, **tucked** as close to the glyph as possible without touching (per-glyph offsets 12.25 circle / 13.75 octagon, derived from the measured ink of the badge font — the derivation rule lives in the code for future re-derivation).

The attachment law (anything attaching to a glyph attaches at the outer edge of its stroke, never the geometric radius) prevents cross-color overlap. `aria-hidden` — the map adds no information not already present in text, and the text remains the accessible source of truth.

**Design-tool rule:** visual MapFrag diagrams (the same node-and-line rendering) are **required** for all world-layout design work — the map the game draws is the map the designers draw first.
### 2.6 Travel & Navigation

Players move using directional commands: `north`, `south`, `east`, `west`, `up`, `down` (and abbreviations: `n`, `s`, `e`, `w`, `u`, `d`). Named exits use the exit name directly (e.g., `enter portal`).

**Movement costs no action economy in normal exploration.** Combat changes this (see Section 5).

Special travel options:

- **`home` (v22)** — the hearth command: a 15-second delayed return to the Heart of the Convergence, from anywhere, narrated as fog-motif atmosphere; broken by movement, combat, or `cancel`; 15-minute completion-only cooldown. The Heart is the only destination until attunement (#38) ships. Full design in Section 2.11.
- **Recall scroll** — teleports player to their bound recall point (default: The Convergence)
- **The Obelisk Network** — the game's fast-travel system: obelisk rooms are travel sources; checkpoints and obelisks are destinations, revealed per-character by visiting them. Free, global, and command-driven (`travel`). Full design in Section 2.11.
- **Zone gates** — the sealed genre-zone gates on the Convergence ring are authored prose (opened per zone as its content ships — the Verdant gate opened in v18). The `ZoneGate` model was superseded and deleted in v18 (Brief 2, migration 0019); the Obelisk Network above is the game's fast-travel system.

Mounts are deferred to a future version.

### 2.7 The Wastelands — Infinite Scaling Zone

The Wastelands is a post-apocalyptic expanse that serves as the game's permanent endgame safety valve. It has no fixed difficulty — the zone scales to match any entering character's level.

**Scaling rules:**

- Enemy stats, HP, and damage scale to the entering player's level
- Loot scales to match — a level 200 character finds level 200 loot (using the Mk system — see Section 6.3)
- In a party, the zone scales to the highest level member
- XP rewards scale appropriately — The Wastelands always provides meaningful XP regardless of player level

**Design purpose:**
When no higher-level content has yet been published, The Wastelands ensures players always have somewhere challenging to go. It is not a substitute for purpose-built high-level zones but bridges the gap between content updates.

### 2.8 Logout Persistence

When a player logs out, their character remains in the world at their exact location for 60 seconds (allowing them to be targeted in PvP zones — a deliberate risk of logging out in dangerous areas), then fades from the world. On next login, they appear at the exact room where they logged out.

There is no safe logout room. Players are responsible for where they choose to go offline.

### 2.9 Infinity City — The Starting Area

**Infinity City** is the starting area of The Convergence zone. It is not a planned city. It grew organically at the point where all dimensional paths converge — the way a city always grows at a crossroads or the mouth of a river, except this crossroads has infinite paths and the travelers arriving on them come from every universe that exists.

The city is old. Nobody planned it. It accumulated. Travelers, refugees, merchants, and wanderers from every universe drifted toward the one place that felt stable, and over generations it became a city that belongs to no world and therefore belongs to everyone.

**Architecture and nature coexist.** The city grew around its trees, not through them. Buildings have roots running beneath their foundations. Vines climb the storefronts. The trees do not stop at the street. This was not a design decision — it is what happened when the city grew up alongside Convergence Park, and the city never saw a reason to change it.

#### Heart of the Convergence — (0, 0, 0)

The starting room and default recall destination. At its center stands **the Obelisk** — a dark, smooth monolith with as many facets as there are universes, each face ground to a perfect plane that catches light differently. At the Obelisk's heart, suspended inside the stone, is a small sphere that glows white. Steadily. Without flickering. It simply is.

The Obelisk serves as an information point for new players. It speaks in as few words as possible, always the best ones.

#### Convergence Park

A rectangular park (9 rooms wide, 7 rooms tall on the coordinate grid) surrounding the Obelisk. The park is tended but not controlled — nature was here first and the city has respected that. Not all park rooms are navigable paths. Four paths wind outward from the Obelisk to the ring street:

| Path | Direction | Material | Rooms |
|---|---|---|---|
| Wisteria Walk | North | Pale grey stone + wisteria trellises | 4 |
| Bamboo Run | East | Crushed amber gravel + bamboo stands | 3 |
| Basalt Way | South | Dark basalt slabs + flowering moss | 5 |
| Fern Boards | West | Dark timber boardwalk + ferns | 4 |

Each path has a continuous sensory identity maintained through all its rooms. Non-path park rooms are not navigable; rooms adjacent to lawn areas have custom `no_exit_*_msg` text directing players to stay on the paths.

#### The Ring Street

A 35-room ring street surrounds the park, approximating a circle in the square-room coordinate system. The ring connects to each path at its cardinal intersection. Walking the ring clockwise from north, players encounter:

- **Seven sealed zone gates** — one per future battle zone, placed clockwise from north in zone build order (Verdant Reach at ~1:00, Ashenveil at ~2:00, continuing through The Wastelands at ~11:00). Each sealed gate has atmospheric `no_exit_*_msg` flavor text hinting at the zone beyond. When a zone is built, its gate is opened by wiring the exit.
- **Four information NPC intersections** — at the north, east, south, and west path/ring junctions, each with a unique NPC and structure
- **Four vendor locations** — each paired with the information NPC across the ring street

The ring street is lined with trees throughout. Sparse content between gates includes closed storefronts, stalls under construction, undeveloped lots, and atmospheric details hinting at the zone beyond each gate.

#### Information NPCs

| NPC | Location | Structure | Personality |
|---|---|---|---|
| The Obelisk | Heart of the Convergence (0,0,0) | The Obelisk itself | Disinterested — operates at a level where everything else is beneath it; speaks as few words as possible, always the best ones |
| Aldric | North ring/path intersection | Ancient hollowed tree, "INFORMATION" carved in old bark | Grumpy but not mean; has been here 40+ years and has opinions about it |
| Info Prime | East ring/path intersection | Vertical metal docking tube, green button to summon | Nearly flat tone; 412 years old; occasionally and unexpectedly poignant |
| Pella | South ring/path intersection | Brightly colored gazebo with climbing vines | Bubbly but not annoying; old; already decided she likes you |
| Seris | West ring/path intersection | Exotic shifting crystal structure | Friendly, doesn't always proffer help; feels like more than looking; cosmic genre |

#### Vendor NPCs

| NPC | Location | Structure | Function | Personality |
|---|---|---|---|---|
| Morra | Across ring from Aldric (north) | Proper smithy building — 2 rooms (exterior + interior) | Blacksmith — repairs and sells weapons/armor | Grumpy because she always works on Mk 1 garbage; reverential toward high-Mk items in good condition; genuinely offended by high-Mk items in poor condition |
| Repairbot Prime | Across ring from Info Prime (east) | Vertical metal docking tube, Version 2 chassis | General repair | ~300 years old; same design lineage as Info Prime; precise; unexpectedly mentions things it has never said aloud before |
| Ferwick | Across ring from Pella (south) | Open-air stall | Magical repairs | Old, cheerful, slightly scattered; first attempt sometimes fails; always succeeds on second attempt; never charges for the retry; finds it funny |
| Veris | Across ring from Seris (west) | Exotic shifting crystal structure — exact twin of Seris's | Crystal vendor | Same personality as Seris — quiet, perceptive, unhurried — but different words; twins in nature, not in script |

**Exits are transitions, not doors.** This is a core world-building principle established with Infinity City. Players do not open doors between rooms — they feel the world change around them. Zone gates in particular should feel like the zone begins, not like a door was opened.

### 2.10 The Verdant Reach — Zone Z01

**The Verdant Reach** is the game's first battle zone: a beginner-level classic-fantasy wilderness spanning **levels 1–10** — the full Mk 1 band. Players graduate to the intermediate zones (Ashenveil Cathedral, The Neon Sprawl) right as Mk 2 gear begins to matter. The zone is entered through the sealed gate at ~1:00 on the Infinity City ring street — a natural tree arch where the forest simply begins. Opening the zone means wiring that exit.

Every zone has a color. The Verdant Reach's color is **green**. The color is never stated outright in names or content — it is carried in pigment-words (viridian, sage, verdant) and living-green imagery (fern, reed, moss), and told in the sum of all the zone's names rather than any single one. Caves carry no green at all — their vocabulary is stone, silk, moss, and lichen.

#### Design Principles

- **Linear progression, not linear layout.** The zone is a maze with one true path — the spine — running from the tree arch to the summit, encoding the level 1→10 difficulty gradient. Side branches, dead ends, and pockets of exploration hang off the spine. "Linear" describes the intended player journey, not a corridor of rooms.
- **The zone is a movement tutorial disguised as wilderness.** Act 1 (the valley) teaches horizontal exploration and safe cave-diving through valley-wall cave entrances. Act 2 (the plains) introduces literal `down` travel via sinkhole caves. Act 3 (the mountains) demands full three-dimensional navigation — the big delves use `up` and `down` internally. A player who finishes the Reach has learned the game's complete movement vocabulary without a single tutorial prompt.
- **The surface is passive; the caves are hostile.** Outdoors, every creature is attackable but none initiate (yellow). All aggro content lives in the seven caves — with one deliberate exception: in some mountain offshoot rooms, some lions and bears aggro. The spine stays safe; Act 3's side branches carry real danger. **(v21, #102)** The ×3 aggro-elite rooms (the prowling grounds and the torn meadows) are **deadly-by-design** — beyond the solo feasibility bound even at band top, deliberately: signposted "don't" content, with authored direction-neutral warning prose appended to every approach room so the danger is unambiguous *before* entry. The ×2 rooms are the ceiling of intended solo content. No stat changes soften the ×3 rooms; the warnings are the design.
- **Terrain-typed inhabitants.** Every creature belongs to its terrain and never appears outside it. No mountain men in the valley; no goats on the plains. Spawn placement is terrain-scoped.
- **Greenery and paths are decoration, not geography.** Forest, trees, glades, ferns, and paths are room-level flavor vocabulary woven through every surface area's prose. They are never Areas. Caves use their own decorative vocabulary: moss, lichen, damp stone.

#### Structure

**150 rooms total. 101 surface, 49 underground.** Ten Areas: three surface Areas in spine order, plus seven cave Areas.

| Area | Act | Surface Rooms | Levels | Caves |
|---|---|---|---|---|
| **Fernwater Vale** | 1 — Valley | ~30 | 1–3 | Spinner's Hollow, The Silken Cleft |
| **The Sagewind Flats** | 2 — Plains | ~20 | 4–5 | The Whistling Sink, The Drone Pit |
| **The Viridian Ridge** | 3 — Mountains | ~51 | 6–10 | The Undercrag, Chitterdeep, Hollowcrown |

The surface split is 30/20/50 by design: a gentle, roomy opening act; a short, brisk transitional middle; and half the zone devoted to the long climb through the mountains. Room share tracks level share — the split *is* the leveling plan.

#### The Seven Caves

Cave room counts follow a logarithmic curve — `rooms(n) = round(1 + 5·ln(n))` — growing fast early and flattening late:

| # | Name | Act | Rooms | Entrance Style | Boss |
|---|---|---|---|---|---|
| 1 | Spinner's Hollow | Vale | 1 | Horizontal valley-wall entrance | None — a single spider; the pure introduction to entering an aggro room |
| 2 | The Silken Cleft | Vale | 4 | Horizontal valley-wall entrance | Yes |
| 3 | The Whistling Sink | Flats | 6 | Sinkhole — teaches `down` | Yes |
| 4 | The Drone Pit | Flats | 8 | Sinkhole | Yes |
| 5 | The Undercrag | Ridge | 9 | Mountain delve — uses `up` and `down` internally | Yes |
| 6 | Chitterdeep | Ridge | 10 | Mountain delve | Yes |
| 7 | Hollowcrown | Ridge | 11 | Mountain delve — the hollow inside the crown of the summit mountain | Yes |

**Cave inhabitants:** spiders, giant centipedes, and giant beetles. The beetles fly — their attack message pool carries aerial flavor (swooping down, dropping from the ceiling darkness). Cave 1 contains only a spider. Caves 2–7 mix all three types and end in a boss: a big, hard version of one of the three, attended by minions, guarding the cave's loot (see Boss Loot below). The three insect types have distinct fight personalities — the spider's speed, the centipede's skittering panic, the beetle's armored dive-bombing — and are the game's first use of per-NPC unarmed message pools.

#### The Entrance Experience

Five rooms of pure atmosphere bring the player in:

1. **The tree arch** — the threshold itself, hinting at a short path beyond
2. **–4. The descending path** — starting green, turning rocky as it drops toward the sound of water
5. **The river** — running along the valley floor; the true boundary of the zone's opening

One offshoot room hangs off the path with a few bears — the player's first optional kill, safely off the spine. **Crossing the river, the fog lifts and the whole valley spreads out before the player.** The zone withholds its identity for five rooms, then delivers it all at once — the fog is the mechanism behind "you don't realize you're in a valley at first." Checkpoint **Fordwatch** sits just across the river: arrival, reveal, and waystation in one beat.

#### Act Transitions

Each seam between acts teaches differently, and each is marked by a checkpoint:

- **Vale → Flats: the ancient stair.** The valley path reaches an apparent dead end — then the player spots very old steps carved into the rock. **Five rooms of climbing** from valley floor to the plains above, with vista rooms along the way that mix beauty with a worried glance at how much climbing remains. Looking back down the valley, the player sees what was once an easier path, long since eroded away by the river — the world is older than the player, and the hard way is the only way left. Checkpoint **Stairhead** waits at the top. The stair is the valley's single exit — a deliberate maze-spine chokepoint.
- **Flats → Ridge: the boulder field.** The plains end in a room of grassy field littered with boulders marking the mountains' feet. **One single transition room**, then the player is in the mountains proper, where checkpoint **Cragfoot** sits at the base. By Act 3 the player no longer needs a gentle hand.

#### The Mountain Climb and the Summit

The Viridian Ridge's ~51 surface rooms wind upward as a switchback mountain path, delve mouths and offshoots hanging off the bends. Each mountain village anchors a mini-cluster: village (safety, services, a warning) → the cave it precedes (the sanctioned danger) → an aggro offshoot (the unsanctioned one). The signature pattern: an aggro lion room one step past a village — the place the villagers warned you about. The warning lives in the village's flavor text; ignoring it is a choice; the lions are the consequence.

**The maze ends at The Verdant Crown** — the top of the mountain, but no snowy peak. It is tall, lush, and impossibly green, a garden where no garden should survive. In the middle stands an obelisk with a sphere — not white like the Heart of the Convergence's, but **green**, the Reach's color. The name is the one place the zone says its color almost out loud, echoing The Verdant Reach itself — reaching it feels like arriving at the zone's namesake.

#### The Obelisk Pattern — Every Zone Ends This Way

The Verdant Crown establishes a world grammar that every future zone follows: **every zone ends in an obelisk scene.** Same structure, different color and different staging — one zone's obelisk might sit in a catacomb ringed by zombies. The player learns that reaching the obelisk *is* finishing the zone, and each zone's version recontextualizes the same sacred object. Like the eroded valley path, the obelisks quietly deepen the lore: they predate everything. The Fracture's fingerprints.

Each zone-end obelisk includes an **obelisk NPC that can send the player back to any other obelisk or checkpoint.** Retroactively, **the Obelisk at the Heart of the Convergence gains the same workings** — the white sphere becomes the network's origin node. The fast-travel design is settled in full — network shape, revelation, the `travel` command, cost, safety, Shards, and messaging. See Section 2.11, The Obelisk Network.

#### Checkpoints

Three checkpoints, each sitting at an act threshold so that reaching the next act and unlocking the next waystation are the same event:

| Checkpoint | Location |
|---|---|
| **Fordwatch** | Just across the river, at the fog-lift reveal |
| **Stairhead** | Top of the ancient stair, entering the Sagewind Flats |
| **Cragfoot** | Base of the Viridian Ridge |

Checkpoints are waystations in the full sense: destination-only nodes on the Obelisk Network (Section 2.11), and — as a **zone-wide pattern for all future zones** — the home of the zone's service NPCs (repair, buy, sell). Every zone gets consistent repair/vendor access, and checkpoint rooms are where it lives. Checkpoints let a returning player skip ahead to later content rather than re-walking outleveled territory.

#### Bestiary

All surface creatures are passive (yellow) except the flagged mountain-offshoot aggressors. Villagers are human NPCs going about their lives — attackable, optionally killable for money and gear.

| Act | Animals | Humanoids |
|---|---|---|
| Fernwater Vale | Bears (feeding at the river), mountain lions (scaling the cliffs), river otters (playing near the villages), wild boars (the valley's toughest passive fight) | Peaceful fishing villagers (Reedmere) |
| The Sagewind Flats | Deer, buffalo, rabbits, prairie dogs | Native plains peoples living in hide tents (Windhome) — written as a fully realized culture with their own names, work, and daily life; no stereotypes |
| The Viridian Ridge | Bears, mountain lions (some aggro in offshoot rooms), mountain goats, mountain squirrels | Mountain villagers (Stonestep, Highfold, Lastlight) |
| Caves | Spiders, giant centipedes, giant beetles (flying) | — |

#### Villages

Villages are **1–3 rooms each** — starting at one, growing to a max of three where the settlement earns it. At least three villages in the Viridian Ridge alone; more than that across the zone. **A village always precedes a cave in the mountains** — players can repair, sell, and gear up before diving. Minimum settlement roster:

| Village | Act | Role |
|---|---|---|
| **Reedmere** | Vale | Fishing village — reeds, still water; the player's first settlement |
| **Windhome** | Flats | The plains peoples' home — theirs by name, a place of belonging |
| **Stonestep** | Ridge | Before The Undercrag |
| **Highfold** | Ridge | Before Chitterdeep — a fold is where goats are kept |
| **Lastlight** | Ridge | Before Hollowcrown — the final hearth before the top |

#### Loot & Drops

- **Animals drop no items** — a bear carrying a sword makes no sense. Animals give XP plus a dice-roll chance at a generic **Animal Hide**; cave insects the same with **Insect Carapace**. One ItemDefinition each for now — pure vendor-sellables. Crafting uses for hides and carapaces come much later (see Section 12).
- **Villagers drop money and gear** — Common trash, the zone's baseline loot source.
- **Pre-boss rarity is deliberately unimpressive.** Everything before a boss is Mk 1 with at most a few points in a single stat — Common with occasional Uncommon. Nothing fancier ever rolls from trash.
- **Boss drop category rotation:** weapon → armor → accessory, looping boss by boss through the zone. ("Accessory" is the real item-type word — see Section 3.6; "trinket" is a conversational alias only and never appears in code or data.) Cave 2 = weapon, Cave 3 = armor, Cave 4 = accessory; the mountain caves repeat the cycle at higher rarity: Cave 5 = weapon, Cave 6 = armor, Cave 7 = accessory. Accessories fill the NECK and RING (×2) slots. Loot mechanism (settled at brief time): guaranteed-group entries on loot tables — each labeled group yields exactly one weighted pick per kill, so a boss always drops exactly one item from its rotation category, with rarity floors expressed through the existing rarity weights; ungrouped entries still roll independently for bonus drops. A player who clears all six bosses touches every equipment category twice — once in cheap versions, once in the good stuff. The "full set of the zone's best" is therefore a concrete checklist: seven armor slots, the weapon slots, one neck, two rings.
- **Boss rarity ladder:** Caves 2–4 guarantee **Uncommon** (visibly better than anything looted off a villager, but modest). Caves 5–6 guarantee **Rare**. Cave 7 guarantees **Epic**. **Legendary never drops in the Reach** — the first one a player ever sees should mean something.
- **The full-set hunt:** a player who clears the mountains, with some replays, should walk out wearing a complete set of the zone's best. Missing pieces are farmable on replay, at reduced XP since the player has outleveled the content. The rule (settled in v18): full XP while within the NPC's Mk level band (band top = Mk tier × 10); −20% per character level beyond the band top; floored at 10% of base and never less than 1 XP. Outleveled content always pays something — helping a friend or farming a missing Epic never feels like nothing.
- **The narrative chest.** Boss loot delivery is pure theater over standard mechanics: the boss guards a chest that splits open when it dies, or the spider drops the prized possessions it was holding, or the kill cuts a net suspending a chest from the ceiling — all death-flavor text, unique per boss. Mechanically almost nothing new exists: the loot lands where loot always lands and the player loots the corpse normally. Delivery mechanism (settled at brief time): a `death_message` text field on the NPC definition, blank by default, broadcast once to the room at the moment of death — one authored reveal per boss, the same staged beat every kill, by design. Zero new commands, maximum theater.

#### Respawn

The Reach runs MUD-traditional: **one shared world, no instancing.** A boss killed by one player is dead for every player until it respawns. Players can race, camp, or cooperate. Timers (mapped to `NpcDefinition.respawn_minutes`):

| Tier | Respawn |
|---|---|
| Bosses | 10 minutes |
| Boss minions | 3 minutes — only while their boss lives |
| All other animals & insects | 1 minute |
| Villagers | 5 minutes |

The world refills almost immediately for general hunting; wiped villages stay eerily quiet for a noticeable while; a 10-minute boss timer makes the full-set hunt a rhythm — dive, loot, resupply at the village, dive again — rather than a camp-fest.

**Minion respawn is gated on the boss** (engine mechanic: a spawn can require a living NPC of a given definition in its room). While the boss lives, minions respawn every 3 minutes — mid-fight reinforcements are deliberate pressure: the adds are effectively infinite, so the winning play is to burn the boss down, not clear the room first. One minute proved too fast for a team to kill the boss between waves; three gives a real window. The moment the boss dies, reinforcements stop — survivors linger, but the player mops up and loots in peace. When the boss respawns at 10 minutes, the encounter resets as a unit and the 3-minute cycle restarts. Adds stopped coming? The boss must be mortal after all.

#### The Mk 1 Item Kit — Leather (Design Complete)

The zone's loot depends on a full-slot roster of Mk 1 ItemDefinitions. The kit's identity is **leather** — humble, fantasy-native, and it quietly rhymes with the zone (hides are what the Reach's animals are made of). Naming is a **plain uniform set with no proper nouns**; the Mark system carries progression. 23 definitions authored (22 net-new rows — the twelfth accessory is the absorbed legacy Copper Ring) plus housekeeping. This kit is authored via its own focused brief, separate from the world seed.

**Armor — the Leather set (6 new + 1 adopted).** Every piece is END-anchored (armor's job is survival) with one slot-flavored twist in its secondary pool. Scaling ~4–5 + 2.0/Mk, chest and legs highest, cap and belt lowest; all take durability loss.

| Piece | Slot | Secondary flavor |
|---|---|---|
| Leather Cap | HEAD | PER (awareness) |
| Leather Shoulders | SHOULDERS | STR |
| Leather Vest *(adopted, exists in seed)* | CHEST | STR, DEX, physical_resist |
| Leather Gloves | HANDS | DEX, crit_chance |
| Leather Belt | WAIST | STR, END |
| Leather Leggings | LEGS | END-weighted |
| Leather Boots | FEET | DEX (movement-flavored) |

**Shield (1).** Wooden Shield — armor-typed, OFF_HAND, END 3+1.0 primary, secondary pool weighted toward physical_resist with STR and magic_resist. Takes durability loss. The Bulwark's identity piece.

**Weapons (4 new).** No technology weapons in Z01 — no pistols, no guns, no lasers, nothing lightsaber-shaped. The existing Pulse Pistol is excluded from all Z01 drop tables. Two-handers run ~40–50% above one-handers in damage budget to pay for the empty off-hand. Spread is weapon identity: tight = consistent, wide = swingy. The Broadsword and Battle Axe share a power budget with opposite personalities — the sword is steady, the axe gambles.

| Weapon | Hands | Midpoint | Spread | Primary | Secondary pool flavor |
|---|---|---|---|---|---|
| Iron Mace *(new)* | 1H | 8 + 3.0/Mk | 3 | STR 3+1.0 | END, stun_chance, physical_resist |
| Broadsword *(new)* | 2H | 12 + 4.5/Mk | 5 | STR 4+1.2 | DEX, crit_chance, bleed_chance, lifesteal |
| Battle Axe *(new)* | 2H | 11 + 4.5/Mk | 8 | STR 4+1.2 | crit_chance (heavy), bleed_chance, END |
| Hunting Bow *(new)* | 2H ranged | 7 + 3.0/Mk | 4 | DEX 2+0.8, PER 2+0.8 | crit_chance, PER, bleed_chance |
| Iron Sword *(exists)* | 1H | 8 + 3.0/Mk | 4 | STR | — |
| Combat Knife *(exists)* | 1H | 5 + 2.0/Mk | 2 | DEX | — |
| Apprentice Staff *(exists, two-handed)* | 2H | 7 + 2.5/Mk | 5 | INT | — |

With this roster every Archetype finds something in the zone's loot: Blade (sword/knife), Bulwark (mace + shield), Shade (knife), Conduit (staff), Warden (staff/mace), Gunner (bow), Machinist (knife/staff until pet machinery exists).

**Accessories (12).** Copper accessories only in Zone 1. Each stat variant is its own ItemDefinition: **Copper Ring of `<stat>` ×6 and Copper Amulet of `<stat>` ×6** (STR, DEX, END, INT, WIS, PER). Each has its suffix stat as sole primary (2 + 0.8/Mk, matching the existing Copper Ring's budget), a secondary pool of the two stats adjacent in that stat's Archetype pairings, and no durability loss. The pieces drop randomly; rarity carries the benefit variance (number of secondary stats and stat points). The existing generic `copper-ring` definition is absorbed as Copper Ring of Wisdom.

**Handedness and the equip exchange rule (verified against the repo).** `ItemDefinition.is_two_handed` already exists in the model, the Apprentice Staff is already flagged two-handed, and basic two-handed refusal already exists in the equip logic. v18 replaces the refuse-always policy with the **general one-for-one auto-swap rule** (Section 3.6): one unambiguous displacement auto-swaps with a message; two or more, or an ambiguous one (the ring exception), refuses. All bows are two-handed for now. Two code gaps found in review (off-hand equips while a two-hander is wielded, and a second two-hander alongside a two-handed bow in RANGED) are subsumed by the exchange-rule rewrite in the kit brief (`consumers.py`, no migration).

#### Implementation Status — Complete (v18.0)

The zone is fully implemented and live. Design flowed through an approved intermediate design document — `Shyland_Verdant_Reach_Layout.md` (the DD), mapping all 150 rooms, the NPC roster and balance, bosses, loot, vendors, and travel nodes, where the XP pacing check passed (~475 average kills for 1→10 under the approved `scaling_factor = level` rule) — and shipped across the six v18 briefs. Per-boss drop pools shipped as guaranteed-group loot tables drawn from the Mk 1 kit. No open items remain for this zone.

### 2.11 The Obelisk Network — Checkpoints & Fast Travel

The obelisks are the game's fast-travel system. There are no waystones, no portals, no ticket vendors — only the obelisks, their checkpoints, and the `travel` command. This section is the authoritative design for the network; Section 2.10 documents the Verdant Reach's specific nodes.

#### Network Shape

- **Obelisks are sources and destinations.** To travel, a player must be standing in an obelisk room. Every zone-end obelisk is a network node, as is the Obelisk at the Heart of the Convergence.
- **Checkpoints are destinations only.** A player can arrive at a checkpoint but never depart from one. From a checkpoint, you walk — the zone content stays meaningful.
- **The network is global, never zone-scoped.** From any obelisk, a player can travel to any checkpoint or obelisk they have revealed — no zone boundaries, no special-casing the Convergence. Cross-battle-zone travel is allowed by design (a high-level player warping to a beginner-zone checkpoint to help a friend is a feature, not an exploit). One flat rule — *destination revealed? travel permitted* — keeps the implementation simple: a single per-character set of revealed nodes and one membership check.

The Convergence Obelisk is not mechanically special — it is simply the first node every character reveals, at minute zero. Special in lore, ordinary in code.

#### Revelation

A node becomes an available destination the moment the player sees its room. **Revelation is per-character and permanent** — once revealed, a node never un-reveals, and revealed nodes are never shared between players (your friend still has to reach you the first time).

The Heart of the Convergence reveals at first login — every character is born there — but the network starts empty of anywhere to *go*. The destination list grows as the player explores. A brand-new player standing at the Obelisk with zero destinations is a natural lore beat: the Obelisk has nothing to show them yet.

A player deep in a zone therefore has exactly three ways out: walk, recall scroll (to the Convergence), or push forward to the summit obelisk. (Note, recorded at Brief 2 closeout: the recall command is designed but not yet implemented — §9.2 — so until it ships, deep-zone players have two ways out. Accepted for The Verdant Reach's launch.) Conquering a zone's obelisk is what turns that zone from a place you trek through into a place you command.

#### The `travel` Command

Travel is a simple command — no dialogue system required:

- `travel` — lists the player's revealed destinations. Only meaningful in an obelisk room; elsewhere it explains that travel requires an obelisk.
- `travel <destination>` — travels there, if the destination is revealed and the player stands at an obelisk.

**The listing (v22):** the bare `travel` listing renders as **per-zone display blocks** — the key-color opener `The Obelisk offers passage to...`, then per zone a `Zone: <name>` heading (the zone name in the zone's own theme color — the licensed exception to value-color) over a `Type / Destination / Description` table with identical column geometry across every block. Zones sort by **hardness to the player** (the danger ladder from the zone table: Sanctuary before Beginner before Intermediate, and so on); within a zone, destinations sort ascending by straight-line map-space distance from the player (the interim sort — the real travel redesign belongs to a future zones-and-travel version). Type reads `Sphere` (obelisk) or `Shard` (checkpoint). **The Description is the stone's own sentence:** each node carries a one-line `listing_description` harvested verbatim from its room's authored prose (never authored fresh for the listing) — the standing convention is that every new node gets its one-liner at authoring time, seed-owned and enforce-exact.

Destination names are unique across the entire network and typeable (Fordwatch, Stairhead, Cragfoot — every future zone's node names must keep that promise). Multi-word destinations accept case-insensitive prefix matching, consistent with MUD command feel.

**Travel is free, forever. It is a gift from the obelisks, but it has to be earned through revelation.** The cost is not copper — it is the journey the player already made. Discovery is the price. No fee, no resource cost, no cooldown.

#### Safety — Obelisk Presence

**All checkpoint and obelisk rooms are safe rooms (`flag_safe=True`), in every zone, because of the obelisks themselves.** Safety is not a game rule bolted on — it is obelisk presence and influence. At checkpoints, which have no obelisk of their own, the obelisks project their spirit there. Consequences:

- Combat can never occur where travel occurs, so `travel` needs no combat gate — the question is structurally impossible.
- Arriving players always materialize inside the obelisks' protection.
- A zone-end obelisk room (e.g. The Verdant Crown) is a bubble of sanctuary inside hostile territory: nothing hostile grows in the obelisk's garden.

#### Shards

Every checkpoint holds a **Shard** — a small sphere like the one suspended in the zone's obelisk, but unattached and free: floating, buzzing around, looking at things. A Shard is a piece of the obelisk projected into the world, and it is the source of the checkpoint's safe-room protection made visible.

- **Shards are named per zone, never per area.** In Z01, every checkpoint has *a Verdant Shard*. Zone color, zone name.
- **Shards have moods, expressed purely in text.** Room prose and `examine` describe temperament. The Reach's Shards are all pretty happy — bobbing, curious. A future graveyard checkpoint's Shard might hover quietly in a corner. Mood is an authoring surface per zone (and per placement where it earns it), and a storytelling channel: players learn to read a zone's soul from how its Shards behave.
- **Shards are indestructible presences.** `attackable=False` (refused everywhere, independent of room safety) and listed under "Who's here?" — a *who*, like the spheres, by field-confirmed v19 ruling. Examine-only for now. They watch.
- **The Shard is the only checkpoint-specific thing the obelisk put there.** No stone markers, no waystones, no built structures — the obelisk's medium is magic, not masonry. Everything else in a checkpoint room is the natural evolution of the local zone.

The recurring signature players learn across every zone: see a Shard, you're safe, services are near, and you can arrive here from any obelisk.

#### Checkpoint Commerce

The service NPCs at checkpoints (repair, buy, sell — the zone-wide pattern from Section 2.10) are **locals who migrated to the checkpoint because they recognized how much traffic it gets and want to make money there.** A Reedmere fisherman with a repair bench at Fordwatch; a mountain trader at Cragfoot. The obelisk provides safety and arrival; commerce follows foot traffic, exactly as it would in a real world. Zones keep their cultural identity, and the network keeps its magic unlittered. The locals don't understand the network — they just know travelers keep appearing near the floating sphere, and travelers have money.

#### Travel Messaging

The obelisk speaks no words during travel — consistent with its character, it simply acts. All travel text is randomly selected from pools so the experience never goes stale:

- **The traveler** sees the screen go funny with a message drawn from a pool themed around transportation, transformation, teleportation, crossing boundaries, crossing universes.
- **Witnesses in the departure room** see a random third-person message about someone going.
- **Witnesses in the arrival room** see a random third-person message about someone arriving.

The game already has message-pool machinery of this shape (`UnarmedMessagePool`); whether travel messages reuse it or get their own model is a brief-time implementation decision, not a design one.

#### Implementation Mapping (settled, carried in the Obelisk Network brief)

- **`ZoneGate` is superseded and removed.** Pairwise gate edges are the wrong shape for a node-membership network; the model is deleted with a migration. The network gets purpose-built storage: a `TravelNode` registry (room + unique travel name + obelisk/checkpoint type).
- **Revelation is derived from `RoomVisit`** — no new per-character table. A character's destinations are exactly the nodes whose rooms they have visited; permanence comes free.
- **Travel messages get a dedicated `TravelMessage` model** (traveler / departure-witness / arrival-witness categories, random selection per event, global pools for now).
- **Shards are NPC definitions** — non-aggressive, no loot, examine-only; safe rooms make them unkillable in practice. Verdant Shard content ships with the zone's world seed, not the network brief.
- **The Heart of the Convergence gains a Sphere NPC — the Primordial Sphere** — for examine parity with every zone-end sphere to come. The Convergence sphere doesn't predate the pattern — **it started it**, and its name says so. Each zone-end sphere is named for its zone (the Verdant Reach's is the Verdant Sphere). The Obelisk itself remains room prose; the network registers the Heart as its first node (travel name: "The Convergence").

#### Home — the Hearth Command (v22)

`home` is the way back when there is no obelisk near: a **15-second delayed return to the Heart of the Convergence**, usable anywhere, in home's own fog-motif voice — a cousin of obelisk travel's machinery pattern, never its words.

- **The countdown is atmosphere, never a UI.** Authored prose lines at the start, middle, and late beats of the wait (`You close your eyes and reach for home. The edges of the world begin to soften.` → drawn from mid and late pools → `The fog parts, and the Heart takes you in. You are home.`). No timer display, no meta-instructions about canceling — the wait warns implicitly, in fiction.
- **Anything breaks it.** The player's own movement or travel auto-cancels the countdown (its line prints, then the move proceeds normally); combat entry of any kind — the player's own attack, aggro engagement, any incoming attack — interrupts it in a distinct violent voice (`The fog is ripped away. The world comes back hard — you are not going anywhere.`); `cancel` stops it voluntarily (`You stop heading home.`). Disconnect mid-countdown kills it silently — intent state dies with the intender.
- **Cooldown: 15 minutes, completion-only.** Interrupted or canceled countdowns never start the clock; it starts when the traveler lands at the Heart. Per-player overridable via admin. The refusal is wry in-fiction prose ending in a terse machine-honest parenthetical with the remaining time: `You can't go home yet, you were just there. Give it a few minutes. (10m cooldown rem.)` — funny in the prose, exact in the parens.
- **Ceremony like travel:** departure is witnessed by the origin room at the vanish (`{name} fades into a fog only they can see, and is gone.`), arrival is witnessed at the Heart (`A fog gathers from nowhere, and {name} steps out of it.`).
- **The Heart is the only destination** until obelisk attunement (#38) ships — home ships pointing at its default and gains player-set destinations with that future zones-and-travel version. Refused in combat and while dying; refused (kindly) when already at the Heart — homing from home would burn the cooldown for nothing.

Under the hood, home is the first resident of the **delayed-action registry** — a connection-bound task pattern that is the standing template for all future delayed actions and `cancel`'s candidate pool (Section 9.1).

-----

