# Shyland V24.22 Brief 1 — Acuity Two-Decimal Display

**Release:** Version 24.22 (milestone `Version 24.22`)
**Branch:** `version_24_22`
**Founding ticket:** #225 — Acuity displays truncate to one decimal — 1.15 renders as 1.1
**Design ruling:** recorded on #225, 2026-08-11 (V24.22 design session)
**GDD:** §4.2, "Acuity display precision — two decimals, end to end (v24.22, pending implementation) (#225)" — committed on this branch

---

## The ruling (design rules — do not deviate)

**The whole meter goes two-decimal, end to end.** Every acuity numeral the game renders shows **fixed two decimals, trailing zeros kept** (`1.00`, never `1.0`):

- server-side format is `:.2f`, client-side is `toFixed(2)` — uniform, every surface;
- this supersedes #133's "round-to-0.1 display" behavior for mid-climb values — no surface anywhere renders acuity at one decimal after this brief;
- **display-only:** stored values remain unrounded floats; the modifier derivation stays rounding-free (v19 rule); the status payload's existing `round(..., 2)` calls in `_build_status` are already correct and are not touched;
- no new precision appears anywhere else — three-or-more-decimal renders are out of scope and wrong.

---

## Step 0 — Verify-and-signal (standing)

Confirm this brief exists verbatim at the `version_24_22` tip (whitespace-only drift is report-and-accept). Create the closeout report stub `docs/shyland/Shyland_V24.22_Brief_1_Closeout.txt` opening with a one-line session-start record (date, brief name, branch), commit, **push immediately**.

## Step 1 — Version constant (standing requirement 1; opening act)

This is the **first implementation brief of Version 24.22**: bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` from `"24.21"` to `"24.22-DEV"` **in its own commit**, moving the pin test with it in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py` line ~118, `assertEqual(SHYLAND_VERSION, '24.21')` → `'24.22-DEV'`. Then run the version-start `make deploy-dev` from the worktree.

## Step 2 — Implementation

Seven format sites, three files. Exact repo-relative paths; current → new:

1. **`django/src/apps/shyland/templates/shyland/game.html`** (~line 657, stats-pane render):
   - `msg.acuity.toFixed(1)` → `msg.acuity.toFixed(2)`
   - Update the adjacent comment ("One decimal, matching the `stats` command's Acuity rendering.") to say two decimals — the comment's claim must stay true.
2. **`django/src/apps/shyland/consumers.py`** (~lines 2726–2727, `stats` command render, one line, two conversions):
   - `{character.acuity_current:.1f}` → `{character.acuity_current:.2f}`
   - `{character.acuity_baseline:.1f}` → `{character.acuity_baseline:.2f}`
3. **`django/src/apps/shyland/management/commands/run_tick_engine.py`** — four message-suffix sites, all `{character.acuity_current:.1f}` → `{character.acuity_current:.2f}`:
   - ~line 1181 (`dot_acuity` suffix)
   - ~line 1220 (`hot_acuity` suffix)
   - ~line 1257 (`Your focus sharpens. (Acuity …)`)
   - ~line 1282 (`Your focus wavers. (Acuity …)`)

No other file changes. **No model changes — no migration step.** No seed data.

## Step 3 — Tests

Three existing literal assertions in `django/src/apps/shyland/tests/test_acuity_shifts.py` pin one-decimal tick suffixes and must update to the new correct literals (literal-for-literal expected-output updates — the pooling rule does not apply; the strings remain fixed renderings):

- line ~79: `'Your focus sharpens. (Acuity 1.1)'` → `'Your focus sharpens. (Acuity 1.10)'`
- line ~138: `'Your focus sharpens. (Acuity 1.2)'` → `'Your focus sharpens. (Acuity 1.20)'`
- line ~167: `'Your focus wavers. (Acuity 0.2)'` → `'Your focus wavers. (Acuity 0.20)'`

Add one new test (in `test_acuity_shifts.py` or a small new `test_v24_22_brief1.py`, implementer's choice) asserting the trailing-zero contract at a band-edge settle: a character whose acuity sits exactly on a two-decimal band edge (e.g. 1.15) renders the tick suffix as `(Acuity 1.15)` — the founding complaint, asserted forever.

## Step 4 — Verification

All steps below must pass before issue closure:

1. `grep -n 'acuity' django/src/apps/shyland/consumers.py django/src/apps/shyland/management/commands/run_tick_engine.py | grep '\.1f'` → **zero hits**.
2. `grep -n 'toFixed(1)' django/src/apps/shyland/templates/shyland/game.html` → **zero hits** (acuity was its only user; if another reader exists, stop and report — do not change it).
3. Full in-container suite passes — the only working invocation form: `python manage.py test apps/shyland/tests` (directory-path form, via `docker exec` in the django container).
4. `make build` before any in-container testing of the changed source (source is baked into the image).

Close #225 gated on all of the above passing.

## Step 5 — Dev deploy (standing requirement 2)

`make deploy-dev` from the worktree once implementation and verification pass. No pending deploy-time data actions — this brief has no PENDING DEPLOY-TIME ACTIONS block, and there are no unexecuted prior-brief actions in this version (this is the release's first brief).

## Step 6 — Operator playtest checklist (standing requirement 3; dev stack)

1. Log in and look at the stats pane: the Acuity numeral shows two decimals with trailing zeros (a character at baseline 1.0 reads `1.00`).
2. Run `stats`: both the Acuity current value and `(baseline …)` show two decimals.
3. Drink a Focus Tonic and let it settle at the band edge: the terminal line and stats pane both read the exact two-decimal edge (e.g. `1.15` for Highborn/Streetborn) — the founding #225 complaint, now correct.
4. Observe a sharpens/wavers tick mid-climb: suffix shows two decimals (e.g. `(Acuity 1.10)`).
5. Confirm Vitality/Longevity numerals are unchanged (integers — this brief touches nothing but acuity).

## Step 7 — Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. Update `docs/shyland/Shyland_Architecture_v24.md` **in place**:

- Header stamp line: add the v24.22 brief 1 change (acuity display precision two-decimal end to end, #225 — `game.html` stats-pane render, `consumers.py` stats command, `run_tick_engine.py` four suffixes; display-only, no models/migrations/seed) and move the **hash** to this brief's final code commit (runtime code changes — the hash moves; it has sat at `4f30bdf` through the seed-only/doc-only 24.20–24.21).
- Stats-pane content paragraph (~line 1284): `numeral alongside (one decimal, matching `stats`)` → two decimals, matching `stats`.
- No other sections change.

## Closeout

Complete the closeout report stub in place: final commit hash, deviations (expected: none beyond the three test-literal updates, which are specified above, not deviations — record anything unexpected), verification results, and the **operator playtest disposition** (exact form: "Operator reports playtest successful" / "No playtests for this brief" / "Operator deferring playtest"). End with the `implementation-session-end` ritual — playtest disposition first, then run the issues report.
