# Shyland V26.0 Brief 1 — Effect Tick Hygiene

- **Release:** Version 26.0 (milestone) — the V26 game-mechanics major opener
- **Founding ticket:** #145 (sole milestone member)
- **Branch:** `version_26_0`
- **Authored:** 2026-09-11, V26.0 design session (this brief is committed by that session; ruling of record is the 2026-09-11 comment on #145)
- **Release type:** code-only — no migration, no seed data, no GDD change, no client change

## 1. Summary

Apply the #133 announcement doctrine — *effect ticks never announce no-ops; boundary arrival gets one terminal line; holding is silent* — uniformly to the dot/hot effect family in the tick engine. The shift branches have followed the doctrine since v23 B3; five of the six dot/hot branches still violate it. This release makes the whole family conform, before the curse engine (#330, release 26.2) builds ticking curse effects on top of these branches.

**Technical coherence note (#252):** every structural claim below about `run_tick_engine.py` was verified against the code by the authoring design session on 2026-09-11 (direct read of the Phase-1 component-ticking block, lines ~1440–1648 at branch tip `5d0c0f3`). Line numbers are anchors, not law — match on the `ctype` dispatch, which is unambiguous.

## 2. Version constant — opening act (standing requirement 1)

This is the first implementation brief of the release. **Opening act, own commit:** bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` from `"25.17"` to `"26.0-DEV"`, moving the pin test in the same commit — `django/src/apps/shyland/tests/test_b2_amendment1.py`, the assertion `self.assertEqual(SHYLAND_VERSION, '25.17')` (line ~122; confirmed against the file at writing time) becomes `'26.0-DEV'`. Then run the version-start `make deploy-dev` from the worktree.

## 3. The defects (all confirmed against the code at writing time)

All six branches live in `run_tick_engine.py`, Phase 1 component ticking (`TICKING_TYPES` dispatch inside the round-boundary block). Current state:

| Branch | Current behavior | Verdict |
|---|---|---|
| `dot_vitality` | Non-fatal tick always applies full magnitude and announces real damage; reaching 0 routes to the Dying event path (clear + dying lines + room broadcast) | **Already conformant — DO NOT CHANGE.** Its floor is the Dying event, terminal by nature. Pin with a test only. |
| `dot_longevity` | `max(0, current − magnitude)` then unconditional save + announce `Your stamina drains from {name}. (-{magnitude} Longevity)` (category `combat`) — keeps announcing at a pinned 0, and announces nominal magnitude even when the applied delta was partial | Fix |
| `dot_acuity` | clamp to `ACUITY_FLOOR` then unconditional save + announce `Your focus is disrupted by {name}. (Acuity {value})` (category `combat`) — keeps announcing at a pinned floor | Fix |
| `hot_vitality` | `min(current + magnitude, max)` then unconditional save + announce `You recover {magnitude} Vitality from {name}.` (category `system`) — keeps announcing at a full bar, nominal magnitude on partial top-up | Fix |
| `hot_longevity` | same shape as `hot_vitality`, `Longevity` wording (category `system`) | Fix |
| `hot_acuity` | computes `step` toward `acuity_baseline` (0 at baseline) then **unconditionally** saves and announces `Your mind clears from {name}. (Acuity {value})` (category `system`) — a no-op announcement loop every tick at baseline | Fix |

## 4. The fix — the shift-branch pattern, verbatim in spirit

Mirror the pattern `shift_acuity_high` / `shift_acuity_low` already use (confirmed at writing time: compute `new`; **only `if new != old`** save + announce; the announcement is the terminal line when `new` equals the boundary, else the ordinary change line; `new == old` does nothing at all — no save, no announcement):

For each of the five fixed branches:

1. Compute `old`, compute `new` (existing clamp math unchanged — this brief changes announcements and saves, never magnitudes, floors, or ceilings).
2. **`new == old` → skip entirely.** No save, no status build, no announcement. (This also removes `hot_acuity`'s pointless every-tick save at baseline.)
3. **`new != old` → save and announce the ACTUAL applied delta**, never the nominal magnitude where they differ (`dot_longevity` partial at the floor, `hot_vitality`/`hot_longevity` partial at the cap; `dot_acuity`/`hot_acuity` announce the resulting value as today, which is already actual).
4. **Boundary arrival gets the terminal line instead of the ordinary line** on the tick that reaches it: `dot_longevity` at 0, `dot_acuity` at `ACUITY_FLOOR`, `hot_vitality` at `vitality_max`, `hot_longevity` at `longevity_max`, `hot_acuity` at `acuity_baseline`. Subsequent holding ticks are `new == old` and therefore silent by construction — the terminal line fires exactly once per arrival, statelessly, exactly as the shift branches do it.

**Terminal-line wording (five lines) is authored at fix time** per the standing creative policy recorded on #145 — the shift branches' lines (`Your focus settles at its keenest.` / `Your focus frays to nothing.`) are the register to match. Message categories stay per-branch as they are today (`combat` for the dots, `system` for the hots).

**Do not touch:** the `dot_vitality` branch, both shift branches, Phase 2 drift, the regen pass, effect expiry handling, and `effect_utils.py` (its `restore_*` instant paths are not ticks).

## 5. Design rules binding this brief

- The #133 doctrine as ruled on #145 (2026-09-11): change-only ticks, one terminal line at boundary arrival, holding is silent — all six branches, five changed, one pinned.
- Announce actual deltas, never nominal magnitudes where they differ.
- No magnitude/clamp/floor math changes of any kind.
- No model changes → **no migration** (0057 remains head; `make migrate` is a no-op).
- No GDD change (the doctrine is already GDD law from #133; ruled: no new text for this release).

## 6. Tests

New file `django/src/apps/shyland/tests/test_v26_0_brief1.py` (naming per the `test_v25_16_brief1.py` precedent). Required coverage, per branch:

1. `dot_longevity`: ticking above floor announces the actual delta; the arrival tick at 0 announces the terminal line (once); the next tick at 0 produces **zero messages and zero saves**; partial application (current < magnitude) announces the partial delta, not the nominal.
2. `dot_acuity`: same trio — change tick / terminal at `ACUITY_FLOOR` / silent hold.
3. `hot_vitality`: change tick announces actual recovery; terminal at `vitality_max` once; silent hold at full; partial top-up announces the partial delta.
4. `hot_longevity`: same trio as `hot_vitality`.
5. `hot_acuity`: movement toward baseline announces; arrival at baseline gets the terminal line once; at-baseline ticks are silent **and do not save**.
6. `dot_vitality` conformance pin: non-fatal tick announces damage exactly as before this brief (byte-identical line), fatal tick still routes to the Dying event path — the branch is unchanged.
7. Shift branches regression: one smoke assertion each that their existing behavior is untouched.

The existing suite passes **unedited** (954 tests at 25.17; the only permitted edit is the pin-test stamp move of §2). In-container invocation, the only working form: `python manage.py test apps/shyland/tests` via `docker exec` in the django container.

## 7. Verification

1. Full in-container suite green: 954 + the new tests, zero pre-existing tests edited (§2's pin move excepted).
2. Grep proof: no unconditional `save(update_fields=` remains in the five fixed branches' no-change paths (each is inside an `if new != old` guard or equivalent).
3. Manual tick-engine spot-check on dev (post-deploy, may fold into the playtest): a `hot_vitality` effect on a full bar produces no output across ≥3 round boundaries.

Issue #145 closes only when all verification steps pass (standing gate).

## 8. Deploy

`make deploy-dev` from the worktree once implementation and verification pass (build + migrate against the local dev stack; migrate is a no-op this release). Production is never deployed from an implementation session — the prod deploy is the closeout tail's (Deployment Law step 6).

**PENDING DEPLOY-TIME ACTIONS: none.** Code-only release; nothing for the closeout tail beyond the ordinary `make deploy-prod`.

## 9. Operator playtest checklist (dev stack)

Ready after §8's `make deploy-dev`. Effects are applied via the Django shell (`make shell`) since no consumable applies ticking effects at range today; the implementation session includes in its closeout report a short, copy-pasteable shell recipe for each numbered step below (creating an active `EffectInstance` + component of the named type on the test character), plus the teardown that removes them.

1. **Silent full-bar HoT:** with the character's Vitality full, apply a `hot_vitality` effect. Watch ≥3 combat rounds: **no output at all.** (Pre-brief behavior: a false `You recover…` line every round.)
2. **HoT recovery + terminal:** damage the character (e.g. one fight), then re-apply the HoT out of combat and wait — ticks announce actual recovery each round, then exactly **one** terminal line at full, then silence while the effect remains active.
3. **`dot_longevity` floor:** apply with a magnitude that empties the bar in a few ticks — draining announcements with actual deltas, one terminal line at 0, then silence.
4. **`hot_acuity` at baseline:** with Acuity at baseline, apply — **silence.** Push Acuity off-baseline (an acuity consumable or shell write), watch it walk back with per-tick lines, one terminal line at baseline, silence after.
5. **`dot_vitality` unchanged:** apply a small one; damage lines read exactly as they always have.

## 10. Architecture document — last, gated step

This step is gated on all implementation and verification steps above being complete and passing.

This is the `N.0` release: **create `docs/shyland/Shyland_Architecture_v26.md`** from the v25 content (`git rm docs/shyland/Shyland_Architecture_v25.md` at the rename), written header-first then one section at a time per the standing rule. Content changes beyond the carry-forward: stamp **26.0**, header hash moved to this release's implementation commit (runtime behavior change), and the tick-engine/effects-processing section updated to state the uniform dot/hot announcement doctrine (change-only, actual deltas, stateless one-time terminal lines, the `dot_vitality` Dying-event exception) with #145/#133 provenance.

## 11. Closeout

Closeout report as `.txt` in `docs/shyland/` (completed in place from the Step-0 stub), including the final commit hash and the operator playtest disposition line (#170). Commit and push at every step boundary; branch only.
