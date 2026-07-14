# Shyland V20 Brief 4 — UI Layout

Implements GitHub issues **#2** (right pane / layout skeleton), **#1** (location bar), **#31** (connection indicator). Self-contained; do not consult chat history. Applies fourth, after Briefs 1–3. The map component and its 300×300 home already exist (Brief 1); all new messages route through the standard consumer send path, so they carry the envelope's `ts`/`seq` automatically (Brief 2).

**Never remove or prune any transient document from the repo** — the operator does all pruning.

---

## 0. Ruled design (binding)

Desktop skeleton, baseline 1000 px; on window widening the right pane keeps fixed width and only the left regions grow:

- **Left 2/3 (700 px baseline), stacked:** LOCATION BAR (top, one line of text high) → OUTPUT PANE (one unified scrolling pane for ALL output: zone/area/room text, who's/what's here, commands and results — there is no separate description pane) → COMMAND BAR (bottom; the send button lives INSIDE the command bar; the connection indicator lives at its right end).
- **Right pane (fixed 300 px content width, full height):** player stats (top; the whole subsection turns red during combat) → current-fight information (middle; scrolling) → the map (bottom; the existing fixed 300×300 component from the Map brief — **do not modify the map component**; re-home only if its container placement needs adjusting to sit at the pane bottom).
- Phone stacking (narrow breakpoint): location bar → compact stats strip (fight info directly under it, only while combat is active) → output (flex) → command bar pinned last; the map renders below the output, reachable by scroll. The terminal (output + command bar) is primary on phones.
- The output pane's ARIA live region behavior is preserved exactly through the restructure. All functionality remains keyboard-accessible.

## Part A — Model change: theme colors (migration required)

Per the data-into-models principle, add to `models.py`:

- `Zone.theme_color = models.CharField(max_length=7, default='#CCCCCC')` — hex like `#7DC95E`
- `Area.theme_color = models.CharField(max_length=7, default='#CCCCCC')`

Seed the authored values (enforce-exact, in `seed_world.py`):

| Zone | theme_color |
|---|---|
| The Convergence (Z05) | `#B387E8` |
| The Verdant Reach (Z01) | `#7DC95E` |

| Area | theme_color |
|---|---|
| Wisteria Walk | `#C9A0DC` |
| Bamboo Run | `#A8C77A` |
| Basalt Way | `#9A9A9A` |
| Fern Boards | `#7FA86B` |
| Fernwater Vale | `#8FCF9F` |
| The Sagewind Flats | `#B4C79A` |
| The Silken Cleft | `#D8D4C8` |
| The Whistling Sink | `#9FC4D8` |
| The Drone Pit | `#D8B45A` |
| The Viridian Ridge | `#40B58C` |
| The Undercrag | `#8FA3B8` |
| Chitterdeep | `#C09A6B` |
| Hollowcrown | `#C4D96B` |

(If Areas exist in the seed that are not listed here, seed them `#CCCCCC` and list them in the closeout report.) Any zone/area created by other v20 briefs inherits the default until authored.

## Part B — Layout restructure (HTML/CSS, vanilla)

Rebuild the play template/CSS to the ruled skeleton. Baseline 1000 px total; left column `flex: 1` (min sensible width), right pane fixed 300 px content width top-to-bottom. Send button moves inside the command bar. Verify: no separate description region remains anywhere; everything textual flows through the one output pane; the existing output categories, scrollback, and live-region semantics are untouched. Phone breakpoint per §0.

## Part C — Location bar (#1)

- Format: `Zone: Area: Room` — Area omitted (with its colon) when the room has no Area.
- Colors are **server-delivered**: the location update the client already receives is extended to carry `zone_name`, `zone_color`, `area_name`, `area_color`, `room_name` (colors straight from the new model fields; nothing computed client-side). Room name renders in fixed near-white `#E8E4D8`; the colon separators render in a neutral chrome gray (`#8A887F`).
- Overflow (one line, ruled): the Area segment truncates first with an ellipsis, then Room; Zone never truncates. CSS text-overflow within per-segment spans.

## Part D — Combat-red stats state (#2)

- The client-state sync payload gains a combat-membership boolean (add only if not already present; server-derived from combat-session membership, updated on engagement and on combat end/flee/death).
- The stats section toggles class `in-combat` from that boolean. Combat-red family base values (the v20 output palette derives its shades from this family later): background tint `#3A1212`, accent/border `#E24B4A`. Stat text colors unchanged.

## Part E — Fight-info feed and rendering (#2)

New server-generated message to the involved player:

```json
{"type": "fight", "active": true,
 "enemies": [{"name": "cave spider", "hp": 12, "hp_max": 20, "focused": true}]}
```

- Sent on combat engagement, on every combat tick while the player is in combat, and once with `"active": false, "enemies": []` when combat ends for the player (victory, flee, death, disengagement).
- `enemies` lists every NPC in the player's combat session; `focused` marks the player's current attack-focus target (the v19 focus mechanism); names use current display names as combat messages render them today (the NPC display-grammar fix arrives in a different v20 brief and needs no coordination here).
- Middle-region rendering: one row per enemy — name, a horizontal hp bar (fill proportional to hp/hp_max, using the combat-red accent), `hp/hp_max` numerals, and a focus marker (`»`) on the focused row. Region scrolls on overflow; completely empty when `active` is false or no fight message has arrived.
- Server-side only; nothing trusted from the client.

## Part F — Connection indicator (#31)

- Protocol: client sends `{"type": "ping", "nonce": <int>}` every 10 seconds over the existing WebSocket; server replies `{"type": "pong", "nonce": <same>}` (echo only — no client data trusted or stored). RTT computed client-side from the nonce round-trip.
- Placement: right end of the command bar, before the send button — a status dot plus latency readout ("42ms").
- States: **green** healthy (fresh pong, RTT < 250 ms); **amber** degraded (RTT ≥ 250 ms or one missed pong); **red, pulsing** while the client is attempting reconnection; **gray** disconnected/closed. On reconnect the indicator returns to green on the first pong.
- Accessibility: the indicator carries an accessible label ("Connected, 42 ms" / "Reconnecting" / "Disconnected") that updates, but is NOT in an announcing live region — no screen-reader spam. The static "Connected to Shyland" line behavior in the output is unchanged.

## Part G — Verification (all must pass before the architecture doc step)

1. Migration applies; reseed enforce-exact seeds all theme colors per Part A tables; any unlisted Area reported.
2. Desktop layout at 1000 px matches §0; widening the window grows only the left regions; the map remains a 300×300 square at the pane bottom, rendering exactly as before this brief (regression check).
3. Location bar: correct format with and without an Area; server-delivered colors match the seeded values in both zones and several areas; truncation order Area → Room, Zone never, verified with an artificially long name.
4. Combat-red: stats section turns red on engagement and clears on victory, flee, and death; boolean present in state sync payloads.
5. Fight feed: engaging one and multiple NPCs shows correct rows; hp bars track damage per tick; switching attack focus moves the `»` marker; the region clears on victory, flee, and death; a second character in the room does not receive the first character's fight messages.
6. Indicator: green with live latency in normal play; amber on simulated latency/missed pong; red pulsing when the server is stopped mid-session; gray when closed; recovers to green after reconnect; accessible label updates without screen-reader announcements.
7. Phone-width pass: stacking order per §0; typing and reading unimpeded; map reachable by scroll; ARIA live region intact.
8. No gameplay changes anywhere; all existing commands and output behave identically.

Close **#1**, **#2**, and **#31** (each with a closing comment referencing this brief), gated on all checks above passing.

## Part H — Architecture doc update (LAST — gated on all implementation and verification above being complete and passing)

Update `docs/shyland/Shyland_Architecture_v20.md` **in place, no version bump**: the client layout section (the ruled skeleton, fixed right pane, phone stacking), the Zone/Area model fields and seeded palette, the extended location payload, the state-sync combat boolean, the new `fight` and `ping`/`pong` message types in the message reference, and the connection-indicator behavior. Do not remove any file.

## Closeout report

Commit hashes, all Part G results, any Areas seeded with the default color, and confirmation that #1, #2, #31 are closed.
