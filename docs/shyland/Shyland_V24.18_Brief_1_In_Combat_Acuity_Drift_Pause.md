# Shyland V24.18 — Brief 1: In-Combat Acuity Drift Pause (#142)

- **Release:** Version 24.18 (milestone `Version 24.18`, GitHub milestone #38)
- **Founding ticket:** #142 — Finish the acuity design: in-combat drift is unruled
- **Branch:** `version_24_18` (cut from main @ 90734e7, the V24.17 merge)
- **Authored by:** V24.18 design session, 2026-08-10 (ruling recorded on #142 the same day)
- **Scope class:** runtime code only — **no model changes, no migration, no seed data, no data actions, deletions 0.** The architecture doc hash **MOVES** (architectural runtime change).

## Pre-flight

- This is the **first implementation brief of Version 24.18** — it carries the version-start ritual (Step 1).
- **Prior pending deploy-time actions: none.** V24.17 closed with an empty tail (deploy-prod only); no PENDING DEPLOY-TIME ACTIONS block is open anywhere in V24. This brief creates none.

## The ruling (design rules — binding, no deviation)

Recorded on #142 (2026-08-10) and in GDD §4.2 (committed 7f34c61, marker `(v24.18, pending implementation)`):

1. **Passive acuity drift pauses during combat.** Tick Phase 2 (passive acuity drift, inside `process_effects`) excludes any character with an active combat session — symmetric with Phase 4's Vitality/Longevity regen exclusion. "Nothing passively recovers in combat" now holds for all three bars.
2. **Predicate identity.** Phase 2 uses the **same combat-membership predicate** Phase 4 uses: active `CombatSession` membership (`combat_sessions` reverse relation, `is_active=True`). Do **not** introduce a second definition of "in combat" — if #218 later changes membership semantics, both phases must move together by construction.
3. **Shift interaction unchanged.** Shift-active (#133 — "a running shift owns the value") and in-combat are **independent** pause conditions. The existing `acuity_shift_types` exclusion stands verbatim; a character with a running shift is paused regardless of combat state.
4. **Post-combat resume is ordinary.** When the character's last active session ends, drift resumes at `ACUITY_DRIFT_RATE` per tick — no burst correction, no refill, no catch-up.
5. **Nothing else changes.** Drift rate (0.01), the snap-within-rate rule, the 2-decimal rounding, the `ACUITY_FLOOR`/`ACUITY_CEILING` clamp, and drift silence (no output message) are all untouched.

## Step 1 — Version constant (opening act)

In its **own commit**: bump `SHYLAND_VERSION` from `"24.17"` to `"24.18-DEV"` and move the pin-test assertion in the same commit. Then run the version-start `make deploy-dev` from the worktree.

## Step 2 — Implementation

**File:** `django/src/apps/shyland/management/commands/run_tick_engine.py`, `process_effects`, Phase 2 (`---- Phase 2: Passive Acuity drift (every tick) ----`, currently ~line 1195).

In `get_characters_needing_drift`, add the in-combat exclusion to the candidate queryset:

```python
candidates = list(Character.objects.exclude(
    acuity_current=F('acuity_baseline')
).exclude(
    combat_sessions__is_active=True
))
```

The `.exclude(combat_sessions__is_active=True)` clause removes every character having **any** active combat session — exactly Phase 4's membership predicate (`combat_sessions.filter(is_active=True).exists()`, regen candidates ~line 1333) expressed at queryset level. Add a short comment noting the predicate is shared with Phase 4 regen by ruling (#142). The downstream per-character drift loop, the `acuity_shift_types` exclusion, and `save_acuity` are untouched.

## Step 3 — Tests

**New file:** `django/src/apps/shyland/tests/test_acuity_drift_pause.py`, engine-harness style (instantiate `Command`, stub `broadcast_to_room` / `send_to_player` / `_online_character_pks`, drive `asyncio.run(cmd.process_effects(tick_number))` — the established pattern in `tests/test_v243_regen.py` and `test_combat_state.py`'s `RespawnAggroTests._command`; reuse the existing world/character factory helpers).

Required pins:

1. **Drift law (regression):** out of combat, acuity below baseline moves up by exactly 0.01 on one `process_effects` call; above baseline moves down by 0.01.
2. **Snap rule (regression):** out of combat, |baseline − current| ≤ 0.01 lands exactly on baseline.
3. **In-combat pause (the change):** a character in an active `CombatSession`, acuity off baseline, is byte-unchanged after `process_effects`.
4. **Resume:** same character after the session is deactivated (`is_active=False`) drifts by exactly 0.01 on the next call — ordinary rate, no catch-up.
5. **Shift independence (regression + independence):** an active `shift_acuity_high` component pauses drift out of combat (the #133 exclusion, pinned); and with both shift and combat active, still no drift.

**Expected conversions: zero.** No existing test asserts drift for an in-combat character (verified at design time — the only drift-adjacent tests are `test_v243_regen.py`'s Phase 4 pins and an incidental comment in `test_combat_state.py`). If any existing test fails because of the new exclusion, that is a **deviation — record it in the closeout report**, do not silently re-oracle.

## Step 4 — Verification

Full suite in-container, the only working form:

```
docker exec <django container> python manage.py test apps/shyland/tests
```

All tests pass (was 559/559 at V24.17 close; expect that plus the new file's additions). Verification gates Steps 5–7.

## Step 5 — Dev deploy

`make deploy-dev` from the worktree once implementation and verification pass.

## Step 6 — Operator playtest checklist (dev stack)

The pause is fully pinned by the engine-harness tests; the playtest is a visual confirmation and its surface is thin (reaching an off-baseline state mid-combat on current seeded content requires a tonic expiring mid-fight). Checklist:

1. Out of combat, drink a Focus Tonic — the band gauge climbs to the top of your band and holds (shift owns the value).
2. Engage a durable NPC and stay in combat past the tonic's expiry.
3. After expiry, while still in combat: the gauge **holds** — no downward creep toward baseline between rounds.
4. End the fight. Out of combat, the gauge drifts back toward baseline at the ordinary rate (~0.01/s; a band-top deviation settles in well under a minute).

The **"No playtests for this brief"** disposition is explicitly offered as an acceptable terminal disposition if the operator prefers to rely on the test pins (V24.17 precedent).

## Step 7 — Architecture doc (LAST, gated)

This step is gated on all implementation and verification steps above being complete and passing.

`docs/shyland/Shyland_Architecture_v24.md`, updated **in place**:

- **Header:** stamp 24.17 → 24.18; the "as of commit" hash **MOVES** to this brief's implementation commit; prepend the v24.18 brief-1 summary to the header's change-summary chain in the established style.
- **§4.9 (Tick Engine):** amend the Phase 2 drift description — currently the #133 paragraph records only the has-shift pause — to record the in-combat exclusion, the shared-predicate doctrine (Phase 2 and Phase 4 use one definition of "in combat"), and the independence of the two pause conditions.
- Sweep the doc (`grep -n 'drift'`) for any other statement implying drift runs unconditionally; update only where factually stale.

## Closeout

- Closeout report as `.txt` in `docs/shyland/` (stub created at Step 0 per the session ritual, completed in place): final commit hash, deviations (expected: none), deletions 0/0, **no PENDING DEPLOY-TIME ACTIONS block** (nothing pending), and the **operator playtest disposition** verbatim.
- Commit and push at every step boundary — branch only, never merge.
- `SHYLAND_VERSION` remains `24.18-DEV` at session end; the closeout session stamps `24.18`.
