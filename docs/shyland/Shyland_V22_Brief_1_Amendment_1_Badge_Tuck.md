# Shyland V22 Brief 1 — Amendment 1 — Badge Tuck

**Amends:** `Shyland_V22_Brief_1_Maps_V2.md` (Steps 2 and 4) · **Version:** 22 · **Bucket:** B1
**Issues:** #82 (this amendment refines the U/D badge geometry ruled in the base brief; no new issues)
**Branch:** the same v22 worktree branch as the base brief. Never merge to main; merging is the operator's action.

This amendment is self-contained for the change it makes, but assumes the base brief has been (or is being) implemented. If Step 4 of the base brief is already complete, apply this as a revision to `renderMap`; if not yet complete, implement Step 4 with these values directly and skip the old ones.

---

## Pre-flight

1. Verify `DOCKER_HOST` before any deployment-touching action.
2. Confirm you are on the v22 worktree branch with a clean tree (aside from in-flight base-brief work already committed).

## Step 0 — Self-commit this amendment (required first step)

Save this amendment's full text verbatim to `docs/shyland/Shyland_V22_Brief_1_Amendment_1_Badge_Tuck.md` (skip the write if an identical file exists), commit it on the working branch, and **push immediately**.

**Standing rule:** commit and push at every step boundary below. Branch only — never merge.

---

## Step 1 — The ruling this amendment implements

The base brief placed U/D badges at a uniform 17px offset; a subsequent design session (2026-07-18/19) found two defects and ruled the fix:

1. At 17px the letters read as disconnected from their rooms, and
2. Two vertically adjacent rooms with opposing badges (top room's D over bottom room's U) collide in the inter-room corridor.

**Superseding ruling — the tuck rule:** each badge is placed **as close to its glyph as possible without touching**, centered on the 45° diagonal away from the glyph center (U upper-right, D lower-right, unchanged). "Without touching" means the letter's ink clears the glyph's **outer stroke edge** by ~0.5px (the attachment law's spirit applied to text).

Concrete constants, derived from the measured rendered ink of 14px bold `Courier New` (`U`/`D` ink is ≈6.8px wide, spanning −4.2..+5.0px vertically around the placement point):

| Glyph | Badge offset (was 17) |
|---|---|
| Circle (r=10, 2px stroke, outer edge 11px) | **12.25** |
| Octagon (circumradius 12, 4px stroke, diagonal flat-face outer edge ≈13.09px) | **13.75** |

Badge placement formula (unchanged form, new constants): text center at `(x + OFF, y − OFF)` for U and `(x + OFF, y + OFF)` for D, rendered as `<text>` with `text-anchor="middle"` at `y ± OFF + 5` baseline adjustment, 14px bold `Courier New, monospace`.

**Record the rule with the constants** (in code comments and the architecture doc): the offsets are derived from this font's measured ink under the closest-without-touching rule; if the rendering font's metrics ever change, the rule explains how to re-derive them.

**Consequence — constraint withdrawn:** the tight tuck clears every opposing-badge adjacency case (circle–circle ≈4.6px air, mixed ≈3.1px, octagon–octagon ≈1.6px). No authored-content constraint on vertically adjacent U/D rooms is needed; if the base brief's #82 comment mentioned one (it did not, per the base brief text), do not add one.

All other badge semantics are unchanged: independent per-direction marks, value-color when the destination room is visited, muted-color when not, no badges on frontier rooms.

---

## Step 2 — Implementation

File: `django/src/apps/shyland/templates/shyland/game.html`.

- In `renderMap`, replace the uniform badge offset constant with per-glyph constants: `BADGE_OFF_ROOM = 12.25`, `BADGE_OFF_NODE = 13.75`, selected by whether the room is a travel node.
- No payload changes. No server changes. No CSS changes beyond what the base brief already specifies.

## Step 3 — Issue housekeeping

Append a comment to **#82** via `gh`: the badge-tuck ruling (2026-07-19) — closest-without-touching on the 45° diagonal, circle 12.25 / octagon 13.75 from measured ink, superseding the uniform 17; opposing-badge collisions dissolved by the tuck, no adjacency constraint required.

## Step 4 — Verification

The badge geometry is client-side and not unit-testable; verification is by the operator playtest checklist. Amend the base brief's Step 7 checklist (in the closeout notes, not by editing the committed base brief) with:

- The Sink/Drone Mouths: D badges visibly nestled into their rooms' lower-right niches, clearly attached to their rooms.
- The Undercrag middle chamber: U badges tucked, composing with agro strokes and the here-dot.
- Any vertically adjacent opposing U/D pair encountered: two distinct letters with visible dark separation between them.

Run the full test suite (`python manage.py test apps.shyland.tests -t /app`) to confirm no regressions from the constant change.

## Step 5 — Architecture doc

**Gated on Steps 2–4 being complete and passing.** Update `docs/shyland/Shyland_Architecture_v22.md` **in place** (no version bump): in §4.12's badge specification, replace the 17px uniform offset with the tuck rule and the per-glyph constants (12.25 / 13.75), including the derived-from-measured-ink note and the withdrawn-constraint consequence.

---

## Closeout

Write the closeout report to `docs/shyland/Shyland_V22_Brief_1_Amendment_1_Closeout_Report.txt`: what changed, test results, playtest-pending note, and the **final commit hash**. Commit and push on the branch.

Do not remove or prune any documents.

Finally: run the issues report.
