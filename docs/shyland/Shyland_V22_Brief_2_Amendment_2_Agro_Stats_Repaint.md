Shyland V22 Brief 2 — Amendment 2 — Agro Unification & Stats Pane Repaint
Amends: `Shyland_V22_Brief_2_Command_Revamp.md` (and Amendment 1's palette work) · Version: 22 · Bucket: B2 Issues: none founded — this amendment executes two design rulings (2026-07-20) recorded below; the design chat is the source. No issue filings, no closures. Branch: the v22 worktree branch. Never merge.
This amendment is self-contained. Out of scope, explicitly: the pane-not-reddening observation and #119 (both parked by the operator — touch nothing about `#side-stats.in-combat` or border coloring).
Pre-flight

1. Verify `DOCKER_HOST` before any deployment-touching action.
2. v22 worktree branch, clean tree aside from committed work.

Step 0 — Self-commit this amendment
Save verbatim to `docs/shyland/Shyland_V22_Brief_2_Amendment_2_Agro_Stats_Repaint.md` (skip if identical exists), commit, push immediately. Commit and push at every step boundary. Never merge.
Step 1 — The rulings this amendment executes

1. Agro unification (ruled 2026-07-20): agro-color follows error-color to `#E24B4A`. The error/agro dual naming survives (two names remain separable in the future); today they carry one value again. The map's hostile-room strokes brighten to the unified red.
2. Stats pane repaint (ruled 2026-07-20): the V fill, L fill, and the acuity gauge's Origin band all render in success-color `#4caf7d`, full strength, no alpha, no modification — the bar green is the loot-message green, verbatim. The acuity tick renders in say-color `#f0c060`. The band's translucency era ends: it becomes a solid success-color block on the gauge track. Reference render approved by the operator in the design chat (solid bars + solid band + gold tick, color-matched against a loot line).

Step 2 — Implementation
File: `django/src/apps/shyland/templates/shyland/game.html`.

1. `--agro-color` → `#E24B4A`. Nothing else about the map's reads changes.
2. `.statbar-fill.v` → `background: var(--success-color);`
3. `.statbar-fill.l` → `background: var(--success-color);`
4. `.gauge-band` → `background: var(--success-color);` (the `rgba(64, 181, 140, .3)` value dies; no opacity anywhere on the band)
5. `.gauge-tick` → `background: var(--say-color);`
6. The hexes `#8FCF9F`, `#D8B45A`, `#40B58C`, and the rgba band value must not survive anywhere in the file after this step.

No server changes. No migrations. No reseed.
Step 3 — Tests
The changes are pure CSS; unit coverage is limited by design. Add one source-conformance test to the suite (`apps.shyland.tests`), in the pattern of Amendment 1's vocabulary scan: assert the rendered template source contains none of `#8FCF9F`, `#D8B45A`, `#40B58C`, `rgba(64, 181, 140`, and that `--agro-color: #E24B4A` is present. Run the full suite; report counts.
Step 4 — Operator playtest checklist
State in the closeout, ready after deploy: the map's agro rooms in the brighter red (Lion's Watch / Bear's Throne, the Undercrag); the stats pane's three green elements color-matching a fresh loot line by eye; the gold tick visible against the solid band across the band's range.
Step 5 — Architecture doc (gated last)
Gated on Steps 2–3 complete and passing. Update `docs/shyland/Shyland_Architecture_v22.md` in place: the palette table's agro entry (unified `#E24B4A`, dual naming retained), and the stats-pane rendering description (success-color fills and band, say-color tick, translucency removed).
Closeout
`docs/shyland/Shyland_V22_Brief_2_Amendment_2_Closeout_Report.txt`: per-step results, dead-hex scan outcome, test totals, deviations, final commit hash. Commit and push. Do not remove or prune any documents. No issues to close.
Finally: run the issues report.
