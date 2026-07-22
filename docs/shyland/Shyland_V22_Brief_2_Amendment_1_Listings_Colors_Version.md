Shyland V22 Brief 2 — Amendment 1 — Listings, Colors, Version
Amends: `Shyland_V22_Brief_2_Command_Revamp.md` · Version: 22 · Bucket: B2 Issues (close at closeout, gated on verification): #123, #124, #120 Normative spec: the B2 DD (`docs/shyland/Shyland_V22_B2_Command_Spec_DD.md`) as amended by the rulings below; where they touch the same ground, this amendment wins. Branch: the v22 worktree branch. Never merge.
This amendment is self-contained.
Pre-flight

1. Verify `DOCKER_HOST` before any deployment-touching action.
2. v22 worktree branch, clean tree aside from committed B2 work.

Step 0 — Self-commit this amendment
Save verbatim to `docs/shyland/Shyland_V22_Brief_2_Amendment_1_Listings_Colors_Version.md` (skip if identical exists), commit, push immediately. Commit and push at every step boundary. Never merge.
Step 1 — Vocabulary law (applies throughout)
The item binding words are Bound and Unbound. "Droppable" and "Undroppable" are dead vocabulary. Sweep all player-facing output, help text, and completion strings; replace any survivor with the correct word (an unbound item's flag reads `Unbound`). The closeout states how many survivors were found (zero is a fine answer if B2 already conformed).
Step 2 — #123: item listing fixes
File: the information renderers in `django/src/apps/shyland/consumers.py` (per B2 Step 9).

1. Vendor list table: remove the Quantity column entirely. The Details column shows rarity only — no durability, no binding flag. Columns: Slot / Name / Details / Price.
2. Slot column populated: on both the vendor list and the player Inventory table, the Slot cell shows the item's equip slot in the ruled sentence-case label form (Main hand, Off hand, etc.) when the item is slotted; muted `-` when slotless. (The Equipment paper-doll is unaffected — its Slot column was always populated.)

Step 3 — #124: color fixes
Files: `django/src/apps/shyland/templates/shyland/game.html` (variables/classes), `consumers.py` and `run_tick_engine.py` (categories).

1. success-color: alias for loot-color — add `--success-color: #4caf7d;` alongside `--loot-color` (same value; both names valid; success-color is the general name for good-outcome lines, loot-color remains the natural name in loot contexts).
2. "Combat has ended." renders success-color (re-tag its category from its current voice to the reward/success class).
3. Loot lines: the `You loot <item> [rarity, binding].` lines currently render value-color — conform them to loot-color per DD §6. Other loot-family messages are already correct; touch only the miscolored form.
4. Remove the four dead variables: `--bar-v`, `--bar-a`, `--bar-l`, `--combat` (#e06060). Nothing reads them; delete the declarations.
5. Name the combat colors as CSS variables and point the classes at them: `--hit-out-color: #C4453F;` `--crit-out-color: #E24B4A;` `--hit-in-color: #E0724A;` `--crit-in-color: #F08A50;` (`.msg-combat*` classes read the variables; no rendered change).
6. error-color becomes `#E24B4A` — the same red as crit-out and Artifact (deliberate reuse). Update `--error` to `#E24B4A`. agro-color stays `#cc4444`: the error/agro dual-naming was designed for exactly this divergence — add `--agro-color: #cc4444;` as its own variable if B1 shipped it as a shared read of `--error`, and ensure the map reads `--agro-color`. The two names now carry two values.
7. Epic rarity becomes `#f0c060` — the same gold as say-color (deliberate reuse). Update `.rar-epic`.

Step 4 — #120: version in help

1. Add the constant: `django/src/apps/shyland/version.py` containing `SHYLAND_VERSION = "22.0-DEV"` (single source of truth; imported where needed).
2. Help output gains a final Kind 1 line: `Version: 22.0-DEV` (key-color `Version:`, value-color value), always the last thing in help, separated from the content above by a blank line — regardless of future help growth.
3. Process note for the closeout (no action beyond recording it): the version-closeout ritual gains a step — bump `SHYLAND_VERSION` to the release stamp (`22.0`) alongside the GDD and architecture stamps; point releases bump it on main (`21.2`, etc.). The constant tells the truth about the code it ships with.

Step 5 — Tests
Extend the suite (`apps.shyland.tests`):

1. Vendor list: no Quantity column; Details is rarity-only; Slot populated for a slotted item, `-` for slotless.
2. Inventory table: Slot populated for a slotted unequipped item.
3. Help: the final line is the Version Kind-1 line, preceded by a blank line; value equals `SHYLAND_VERSION`.
4. Categories: "Combat has ended." emits the success/reward class; the `You loot …` line emits the loot class.
5. Vocabulary: no player-facing output or help string contains "Droppable" or "Undroppable".
6. Full suite green; report counts.

Step 6 — Architecture doc (gated last)
Gated on Steps 1–5 complete and passing. Update `docs/shyland/Shyland_Architecture_v22.md` in place: the palette table (combat color names, success-color alias, error `#E24B4A`, agro `#cc4444` divergence, Epic `#f0c060`, dead variables removed), the listing column changes, the version constant and its ritual.
Closeout
`docs/shyland/Shyland_V22_Brief_2_Amendment_1_Closeout_Report.txt`: per-step results, Droppable-survivor count, test totals, deviations, final commit hash. Close #123, #124, #120 — gated on verification. Commit and push. Do not remove or prune any documents.
Finally: run the issues report.
