Shyland V22 Brief 5 — Amendment 2 — Spend Block and Display Trims
Type: amendment to `Shyland_V22_Brief_5_Gear_Combat_Wiring.md` (does not count against the cap); combined file-and-fix — it files one issue and implements against it, with a HARD GATE between Branch: the current Version 22 worktree branch (`version_22`) — all work, commits, and pushes on that branch Issues: files one new issue (number captured at runtime); posts ruling comments on #100 and #109 (both closed — comment, do NOT reopen) Migrations: NONE.
Three operator rulings from post-ship play: mid-combat stat spend is now blocked (superseding the last surviving half of #109's state-matrix ruling); the `stats` report gets a blank line before the Armor row; and Amendment 1's incoming hit parenthetical is removed entirely — it was scaffolding to watch armor work, and the permanent surfaces (the Armor row, the examine line) carry visibility from here. Data tables are authoritative over prose if they disagree.
Standing rules

* Work in the Version 22 worktree on its branch. Commit and push at every step boundary — branch only, NEVER merge to main on your own initiative.
* Never remove, prune, or clean up any transient document.
* Test suite runs as `apps.shyland.tests` (#117 workaround, unchanged).
* If any repo fact contradicts this amendment, stop and record the contradiction in the closeout rather than improvising.

Pre-flight

1. Version 22 worktree, tree clean, branch synced. Both the parent brief and Amendment 1 must already be applied on the branch (this amendment edits Amendment 1's incoming-line code and rewrites tests in `tests/test_b5_amendment1.py`). If they are not present, STOP.
2. `gh auth status` shows repo access.

Step 0 — Self-commit this amendment
Save verbatim to `docs/shyland/Shyland_V22_Brief_5_Amendment_2_Spend_Block_And_Display_Trims.md` (skip if identical file exists). Commit and push immediately.
Step 1 — File the founding issue
Create one issue. Capture its number from `gh issue create` output — it is referenced in Step 2's comments and closed in Step 7.

* Title: `Block stat spend during combat`
* Labels: none
* Milestone: `Version 22`
* Body:


```
Operator ruling from post-B5 play: spending stat points during combat is
now blocked. This supersedes the last surviving half of #109's state-matrix
ruling ("spend remains legal in combat") — with the bankable free heal
already dead (bar law: bigger bar, same fill fraction), in-combat spend
retained no upside worth its surface area, and the operator has ruled it
out of the combat state matrix entirely. Refusal uses the generic line
"You can't do that while in combat." (warn category) — ruled acceptable as
the first generic in-combat refusal; existing refusals are per-command
authored lines. Implemented by B5 Amendment 2.

```

⛔ HARD GATE
Verify via `gh issue view`: the issue exists exactly as specified (title, body, milestone `Version 22`, no labels). Any deviation: STOP, run the issues report, closeout explaining, zero code changes.
Commit and push.
Step 2 — Housekeeping comments
2a. On the new issue from Step 1, post:

```
Ruling record complete in the issue body. Implementation: B5 Amendment 2 —
combat gate at the top of the spend command before any mutation, using the
standard get_active_combat_session check; refusal line "You can't do that
while in combat." sent as warn. Closes with the amendment.

```

2b. On #109 (closed — do not reopen), post, replacing `<N>` with the Step 1 issue number:

```
Superseded further by operator ruling (B5 Amendment 2, #<N>): mid-combat
stat spend is now BLOCKED entirely. The state-matrix half of the B5 ruling
("spend remains legal in combat") no longer stands. #109 is now fully
superseded: no refill (B5) and no in-combat spend (#<N>).

```

2c. On #100 (closed — do not reopen), post:

```
B5 Amendment 2 display rulings, confirmed by the operator:

1. STATS SPACING: a blank line is inserted before the Armor row in the
   stats report — the row reads as its own group beneath the six stats.

2. INCOMING PARENTHETICAL REMOVED (supersedes Amendment 1 ruling 3): the
   incoming hit line drops the (-N) parenthetical entirely and returns to
   its pre-Amendment-1 form — the leading number is the damage taken (post-
   mitigation, the bar delta), nothing else. The parenthetical was
   scaffolding to verify armor in play; the "(-6)" grammar read ambiguously
   ("25 minus 6 pending" vs "25 landed, 6 blocked") and every wordier
   alternative was ruled too wordy. Armor visibility now lives permanently
   in the stats Armor row and the examine contribution line. The
   one-vocabulary rule survives on the OUTGOING side only (+N = gear's
   added damage); the byte-identical quiet-line law now covers incoming
   lines unconditionally. Mitigation math is untouched.

```

Commit and push (the amendment file may be the only tracked change; fine).
Step 3 — Block spend in combat
In the spend command path (consumers.py; the post-B5 refactored spend — locate the command handler, not this amendment's guess at a line number): at the very top, before any validation output or mutation, check `get_active_combat_session(self.character)`; if a session exists, send exactly `You can't do that while in combat.` with the `warn` category and return. The dying gate (if spend has one) keeps its existing precedence — cite the ordering chosen in the closeout.
Tests: in combat, spend refuses with exactly that line and mutates nothing (stat unchanged, unspent points unchanged, bars unchanged); out of combat, spend behaves exactly as before (fraction-preserving per the bar law); the refusal line's category is `warn`.
Step 4 — Stats spacing
In the `stats` report composition, insert one blank line between the six stat rows and the Armor row (Amendment 1 placed the row directly after them; it now sits as its own group). No other spacing changes.
Test: the rendered stats report contains exactly one blank line between the PER row and the Armor row; no trailing blank after Armor beyond what exists today.
Step 5 — Remove the incoming parenthetical
In the NPC-attack rendering path (Amendment 1 Step 4's composition point): remove the `(-N)` parenthetical entirely. The line returns to its pre-Amendment-1 form — leading number = post-mitigation, post-clamp damage (the bar delta) — across plain, crit, and graze renderings. `apply_armor_mitigation` and all mitigation math are untouched; `raw_damage`/`blocked` bookkeeping may be deleted if nothing else consumes it (cite what was removed in the closeout).
Rewrite the Amendment 1 tests in `tests/test_b5_amendment1.py` that asserted the parenthetical (armored composition, crit, graze, TAV-1 floor `(-1)`): they now assert the inverse — armored incoming lines contain NO `(-` parenthetical and the leading number still equals the bar delta (mitigation still applied). Keep the byte-identical unarmored assertions; armored and unarmored lines now share the same form.
Step 6 — Verification
Full suite green (`apps.shyland.tests`) including all rewritten and new tests. No re-bless — mitigation math untouched.
Step 7 — Close the founding issue
Close the Step 1 issue (gated on Step 6 passing), with a closing comment noting implementation landed in this amendment.
Step 8 — Architecture doc (GATED, last)
Gated on all steps above complete and passing. Update `docs/shyland/Shyland_Architecture_v22.md` in place (no new file, no version bump; the header hash moves): the spend documentation gains the in-combat block and the generic refusal line (noting it as the first generic in-combat refusal alongside the per-command authored lines); the stats-report paragraph notes the blank-line grouping of the Armor row; §4.9's one-vocabulary rule narrows to outgoing-only, and the incoming hit line is documented in its parenthetical-free form with the unconditional quiet-line law.
Step 9 — Closeout
Write `docs/shyland/Shyland_V22_Brief_5_Amendment_2_Closeout_Report.txt`: the founding issue number, the spend-gate ordering chosen vs the dying gate, what raw/blocked bookkeeping was removed, the test rewrites, any discrepancies, and the final commit hash. Commit and push.
Step 10 — Final instruction
run the issues report
