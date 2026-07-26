# Version 23 — Closeout Packet (for the design chat)

Prepared 2026-07-25 at branch `version_23` tip `f5406bb`.

## Status

**Milestone:** 15/15 issues closed, nothing open. Five implementation briefs plus one amendment, all applied, deployed, playtested, and closed:

| Brief | Issues closed | Highlights |
|---|---|---|
| B2 Data Integrity | #137, #117, #18 | corpse CASCADE + exactly-one location invariant; `purge_orphaned_items` FIELD-COMPLETE on production (87/87/0, post-deploy sweep 0/0/0); whole-app test discovery restored; wear-free stacking with soulbound in the key |
| B1 Flee & Disengagement | #143, #25 | flee contest NPC side on effective PER (both sides effective now); session-end-without-death NPC reset with the last-active-session multiplayer guard; chip-and-run dead on every tier |
| B3 Effects & Display | #133, #119, #141 | acuity band-edge stop with exact band_high storage; ACUITY_FLOOR/CEILING rails; effect-tick announcement doctrine (+ #145 filed for the unmigrated branches); borders doctrine; two-line level-up; stats hint removed |
| B4 Voice Machinery (part 1/2) | #138, #146 | `npc_voice.py` pool module + pick(); the NO-LEAK rule on vendor speech; worthless-sell opens (zero floor in get_sale_price, artifacts refused generically); dead `is_artifact` removed (migration 0037) |
| B5 Voice Content (part 2/2) | #40, #144, #147 | corpus lifted to module-level NPC_DIALOGUE — 16 voices, 73 entries, 3-response pool floor; six silent checkpoint services voiced; speech-vs-narration render rule (greetings/departures narrate unprefixed, no connective); dialogue seeds last (fresh-DB trap fixed, scratch-DB-proven) |
| B5 Amendment 1 | #152 | the output-color pass: direction-split miss categories (out=warn, in=success), system/room narration at value-color, copper loot at reward |

**Branch/production state:**
- Tests: 291 at v22 close → **354/354** now.
- Migrations this version: `0035` (corpse CASCADE), `0036` (scaling_factor help text), `0037` (is_artifact removal) — all applied to production.
- Deploy-time data actions: ALL executed and verified in session (the #137 purge field-complete; B5's `make seed` idempotent-verified).
- `SHYLAND_VERSION = "23.0-DEV"`; production runs the branch tip image.
- All operator playtests complete, zero defects found across the version.

## GDD items queued during the version (awaiting closeout authoring)

1. **#119 — the borders doctrine**: pane borders are zone/area theming exclusively; transient state (combat included) expresses through backgrounds and text, never borders. Ruled for GDD at version closeout.
2. **#138 — GDD §6.12 amendment**: soulbound-CAN-be-sold gains its one exception — vendors never buy Artifact rarity at any value (bound artifact = no disposal path, intentional).
3. **#133 — the effect-tick announcement doctrine** (ticks never announce no-ops; boundary arrival gets one terminal line; holding is silent), if the GDD carries it.
4. **#152 — the color doctrine** (gold is speech, green is what went your way, yellow is your whiff, the reds are damage, value-color is the world, muted is true chrome only), if GDD-worthy.
5. **Open question:** was the v22 B2 Command Spec DD (`Shyland_V22_B2_Command_Spec_DD.md`) absorbed into the GDD at v22's closeout, or does it still bind as a separate document? If unabsorbed, v23's closeout is the opportunity.

## Post-v23 queue (not closeout blockers)

- **#150** — the sell-all potion guard: ruled for the **point release immediately after v23 ships**; candidate directions seeded on the issue.
- **#148, #149, #151** — `output`-labeled items (loot-line composition, single-line use, multi-use heal aggregation; #151 blocked-by #149).
- **#145** — hot_acuity/dot_acuity no-op tick announcements (doctrine follow-up from #133).
- **#142** — acuity in-combat drift (already milestoned Version 24).

## What the closeout brief needs to direct (the mechanical ritual, for reference)

1. `SHYLAND_VERSION` → `"23.0"` **with the test pin in `test_b2_amendment1` moved in the same commit** and the suite run (the pin now moves with the version rituals).
2. GDD: version stamps in the index, `_00_header.md`, and the changelog; new Version History row; `make gdd` rebuild (mechanical ops only — content arrives authored by the design chat / committed by the operator per standing practice).
3. Architecture doc header: "Version 23 — Closed. In lockstep with GDD v23.0" (hash stays at the last architectural commit per convention); Known-Issues entries kept/removed per the chat's rulings.
4. Final issues report; milestone "Version 23" closed.
5. PR from `version_23` → main, squash-merged on the operator's word; local main synced; final production build from main.

## Request to the design chat: a new color-chart PNG

`Shyland_Color_Chart.svg` (the design chat's artifact) was updated by B5 Amendment 1 — the caption baseline moved to "v23 B5 Amendment 1 (#152)" and four "Used for" strings changed (value-color gains narration + ambient; muted loses misses; warn-color gains your misses; loot/success-color gains their misses). **`Shyland_Color_Chart.png` is now stale and needs re-export from the updated SVG** — the implementation environment has no SVG renderer, so the chart's owner (the design chat) should produce the new PNG; the operator will commit it. The current SVG is on branch `version_23` at `docs/shyland/Shyland_Color_Chart.svg`.

## Loose ends

- None otherwise — stash pruned, stack empty, all playtests complete, no pending deploy-time actions.
