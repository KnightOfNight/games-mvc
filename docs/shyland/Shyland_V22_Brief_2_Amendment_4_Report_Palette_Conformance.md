Shyland V22 Brief 2 — Amendment 4 — Report Color & Palette Conformance
Amends: `Shyland_V22_Brief_2_Command_Revamp.md` · Version: 22 · Bucket: B2 Issues: none founded — executes design rulings (2026-07-20) recorded below. No filings, no closures. Branch: the v22 worktree branch. Never merge.
This amendment is self-contained. Out of scope: any color change beyond Step 2 — in particular `--text` (`#c8c8d4`) keeps its remaining readers (body default, input field) untouched; the exhaustive test reports such colors, it does not change them.
Pre-flight

1. Verify `DOCKER_HOST` before any deployment-touching action.
2. v22 worktree branch, clean tree aside from committed work.

Step 0 — Self-commit this amendment
Save verbatim to `docs/shyland/Shyland_V22_Brief_2_Amendment_4_Report_Palette_Conformance.md` (skip if identical exists), commit, push immediately. Commit and push at every step boundary. Never merge.
Step 1 — The rulings this amendment executes
Ruled 2026-07-20:

1. The report color dies. `.msg-report`'s `#B8B4A6` (an unnamed, undocumented dimmer parchment carried by the entire report category — examine prose, unsegmented information output) is killed; report text renders value-color. One content voice.
2. Chart-as-license principle: the color chart is not a description of the colors in use — it is the license to use them. A color literal not on the chart (or on the explicitly documented chrome list below) is a defect by definition. This amendment builds the enforcement.

Step 2 — CSS
File: `django/src/apps/shyland/templates/shyland/game.html`.

1. `.msg-report` → `color: var(--value-color);` — `#B8B4A6` must not survive anywhere in the file.

Step 3 — Exhaustive palette conformance test
Add to the suite (`apps.shyland.tests`), superseding-and-absorbing the piecemeal dead-hex scans from Amendments 1–3 (keep those tests or fold them in; do not lose their assertions):

1. The test renders/reads the game template source and extracts every color literal: `#RGB`/`#RRGGBB` hex (case-insensitive) and `rgb(...)`/`rgba(...)` forms.
2. It asserts set equality against an explicit `ALLOWED_COLORS` constant defined in the test module — not merely subset: an allowed color disappearing fails the test the same as a new color appearing. Every future palette change is therefore a deliberate two-place edit (CSS + allowlist) traceable in one diff.
3. `ALLOWED_COLORS` is initialized to exactly the literals present after Step 2, organized with comments in two groups:
   * Chart colors — each annotated with its chart name(s) (key/value/muted/error-agro-crit-out-Artifact-combat-accent/say-Epic/warn/loot-success/hit-out/hit-in/crit-in/Common/Uncommon/Rare/combat-bg …).
   * Chrome — structural colors not yet on the chart (background, surface, border grays, `--text`'s `#c8c8d4`, connection-dot colors, and whatever else the extraction finds), each annotated `chrome — pending chart ruling`.
4. Normalization: compare case-insensitively; treat `#RGB` and `#RRGGBB` forms of the same color as one.
5. The closeout must list the complete Chrome group verbatim — that list is the design chat's queue for future ruling, and the operator decides each color's fate in later sessions. Do not change any chrome color in this amendment.

Step 4 — Operator playtest checklist
Ready after deploy: examine something and see its prose at full value-color brightness beside a room render; an inv/stats report likewise; nothing else visibly changes.
Step 5 — Architecture doc (gated last)
Gated on Steps 2–3 complete and passing. Update `docs/shyland/Shyland_Architecture_v22.md` in place: the report category's color, and a short paragraph documenting the palette conformance test and the chart-as-license rule (the display section's new standing law).
Closeout
`docs/shyland/Shyland_V22_Brief_2_Amendment_4_Closeout_Report.txt`: per-step results, the full ALLOWED_COLORS list as shipped (both groups, chrome verbatim), test totals, deviations, final commit hash. Commit and push. Do not remove or prune any documents. No issues to close.
Finally: run the issues report.
