Shyland V22 Brief 2 — Amendment 3 — Pane Recolors & Travel Listing
Amends: `Shyland_V22_Brief_2_Command_Revamp.md` · Version: 22 · Bucket: B2 Issues: none founded — this amendment executes design rulings (2026-07-20) recorded below; the design chat is the source. No filings, no closures. Branch: the v22 worktree branch. Never merge.
This amendment is self-contained. Out of scope, explicitly: the pane-not-reddening observation and #119 (parked — touch nothing about `#side-stats.in-combat` background/border behavior beyond the single variable re-point in Step 3), and any change to travel's sort order, pools, or mechanics (display only).
Pre-flight

1. Verify `DOCKER_HOST` before any deployment-touching action.
2. v22 worktree branch, clean tree aside from committed work.

Step 0 — Self-commit this amendment
Save verbatim to `docs/shyland/Shyland_V22_Brief_2_Amendment_3_Panes_Travel_Listing.md` (skip if identical exists), commit, push immediately. Commit and push at every step boundary. Never merge.
Step 1 — The rulings this amendment executes
All ruled 2026-07-20 in the B2 design chat:

1. Fight panel recolor: targeting arrow, enemy health-bar border, and fill → error-color; enemy name and the x/y count → value-color.
2. Player pane recolor: the character name renders value-color normally (retiring its `--text` fossil read); the V/A/L bar labels and all bar numbers (including the A decimal) render value-color; the in-combat name red re-points from `--combat-accent` to `var(--error)` for naming hygiene (same pixels).
3. Acuity tick geometry: the tick grows to 16px tall × 4px wide (extends 4px above and below the 8px track), still say-color.
4. Travel listing rebuild: the bare `travel` listing becomes per-zone display blocks — zones sorted by hardness to the player (danger order per GDD §Zones: Sanctuary before Beginner before Intermediate …); each block headed by a Kind 1 line `Zone: <zone name>` with `Zone:` in key-color and the zone name in the zone's theme color (the licensed exception to Kind 1's value-color); under each heading a Kind 3 table (muted column headers, value-color rows) with columns Type / Destination / Description; Type reads `Sphere` (obelisk) or `Shard` (checkpoint), capitalized; all zone tables share identical column x-geometry; within-zone row order keeps the ruled interim sort (ascending map-space distance; the alphabetical cross-zone fallback is unchanged and now invisible inside per-zone blocks). Descriptions are harvested, not authored fresh — see Step 4.

Step 2 — Fight panel CSS
File: `django/src/apps/shyland/templates/shyland/game.html`.

1. `.fight-focus` → `color: var(--error);` (weight unchanged)
2. `.fight-bar` → `border: 1px solid var(--error);` (track background unchanged)
3. `.fight-fill` → `background: var(--error);`
4. `.fight-name` → `color: var(--value-color);`
5. `.fight-nums` → `color: var(--value-color);` (size unchanged)

`--combat-accent` and `--text` survive with their remaining readers untouched.
Step 3 — Player pane CSS
Same file.

1. `#stats-name` → `color: var(--value-color);`
2. `#side-stats.in-combat #stats-name` → `color: var(--error);`
3. `.bar-label` → `color: var(--value-color);`
4. `.bar-num` → `color: var(--value-color);`
5. `.gauge-tick` → `top: -4px; bottom: -4px; width: 4px; margin-left: -2px;` (color stays `var(--say-color)`)

Step 4 — Travel listing rebuild
File: `django/src/apps/shyland/consumers.py`, the bare-`travel` listing branch of `cmd_travel`.

1. Grouping and order: group revealed destinations by their room's zone. Order zones by hardness: use the GDD danger ladder — The Convergence (Sanctuary) first, then The Verdant Reach (Beginner), then any future zones by their danger tier. Implement as an explicit zone-slug ordering list with a comment citing the GDD zone table (a `danger_rank` model field is NOT in scope; the list is the interim authority and lives in one place).
2. Rendering: replace the current prose lines with the structured display: the opening line `The Obelisk offers passage to...` (key-color, ellipsis — structure follows); then per zone: the Kind-1 heading `Zone: <zone name>` (key-color key; zone name in the zone's `theme_color`); the Kind-3 table with muted headers Type / Destination / Description and value-color rows; identical column positions across all zone tables (size columns to the widest content across the whole listing, not per table). Use the established k/v-and-table display machinery from the B2 information-output work — do not invent a parallel renderer.
3. Type column: `Sphere` for node_type obelisk, `Shard` for checkpoint — capitalized exactly.
4. Description harvest: each node's Description is the authored one-line stone sentence from the world's own prose. For the seeded network, harvest these exact lines from the seed (CC verifies each against `seed_world.py` and uses them verbatim):
   * The Convergence — `At the center of everything stands the Obelisk.`
   * The Verdant Crown — the sphere one-liner from the Crown's room prose (locate in the seed; the Crown's room vr-vc1 opening sphere/obelisk sentence)
   * Fordwatch — `A green shard drifts above the crossing where the fog gives way.`
   * Stairhead — `A green shard rides the wind above a trodden waystation.`
   * Cragfoot — `A green shard warms itself by a fire at the mountains' feet.` Storage: add `TravelNode.listing_description` (`TextField`, blank default) via migration, seeded with the harvested lines (seed is authoritative; enforce-exact on reseed). This makes the harvest a one-time authoring capture and future nodes carry the standing convention: every new stone gets its one-liner at authoring time. If the Verdant Crown's room prose lacks a suitable single opening sentence, STOP and flag in the closeout rather than authoring fresh — zero deviations on harvested prose.
5. The traveling, non-listing path of `cmd_travel` is untouched.

Step 5 — Migration
One migration: `TravelNode.listing_description` as above. Run `makemigrations` + `migrate`; the seed populates values; reseed is enforce-exact for this field.
Step 6 — Tests
Extend the suite (`apps.shyland.tests`):

1. Source-conformance scan extension: `.fight-fill`/`.fight-focus`/`.fight-bar` read `var(--error)`; `.fight-name`/`.fight-nums`/`#stats-name`/`.bar-label`/`.bar-num` read `var(--value-color)`; gauge-tick geometry 16×4; no reader of `--text` remains among the fight/stats selectors changed here.
2. Travel listing: from a Z01 obelisk with full visits, the payload/text contains both zone headings in order (Convergence before Verdant Reach), the three columns, capitalized `Sphere`/`Shard`, and each seeded `listing_description` verbatim.
3. Migration applied; seed-verify green including the new field's enforce-exact.
4. Full suite green; report counts.

Step 7 — Operator playtest checklist
Ready after deploy: fight panel in a multi-enemy fight (red arrow/bars, parchment names and counts); stats pane at rest (parchment name, labels, numbers) and in combat (name in the unified red); the fat gold tick; `travel` at the Heart (one zone block) and at the Verdant Crown (both blocks, hardness order, aligned columns, the stones' own sentences in the Description column).
Step 8 — Architecture doc (gated last)
Gated on Steps 2–6 complete and passing. Update `docs/shyland/Shyland_Architecture_v22.md` in place: the fight/stats pane color reads (all chart names), tick geometry, the travel listing's structured renderer, the `listing_description` field and its authoring convention, and the zone hardness-order list's location.
Closeout
`docs/shyland/Shyland_V22_Brief_2_Amendment_3_Closeout_Report.txt`: per-step results, the harvested Crown sentence (verbatim, for the design record), test totals, deviations, final commit hash. Commit and push. Do not remove or prune any documents. No issues to close.
Finally: run the issues report.
