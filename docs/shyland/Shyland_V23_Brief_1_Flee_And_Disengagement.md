Shyland V23 Brief 1 — Flee & Disengagement
Type: implementation brief (bucket B1 of Version 23) Branch: the Version 23 worktree branch — all work, commits, and pushes on that branch Issues: #143 (flee mathematically impossible — pre-v21 `scaling_factor` semantics in the contest) and #25 (NPCs never heal on disengagement) — both close with this brief, gated on verification Ordering law (from both rulings): the flee fix (#143) lands FIRST, then the disengagement reset (#25). Fixing flee re-arms the chip-and-run exploit; the reset must ship in the same brief, in that order, so #25's disengagement path is testable. Migrations: ONE expected (`NpcDefinition.scaling_factor` help-text correction — confirm via `makemigrations`; Django generates AlterField for help-text changes) Pending deploy-time actions: this brief creates NONE (code-only; the deploy in Step 5 has no data actions)
Both issues carry operator-confirmed design rulings recorded on the issues themselves (#143's body is its own ruling, dated 2026-07-23; #25's ruling is the comment dated 2026-07-23). Those rulings are reproduced in this brief verbatim where they are law. If any repo fact contradicts this brief, stop and record the contradiction in the closeout rather than improvising.
Standing rules

* Work in the Version 23 worktree on its branch. Commit and push at every step boundary — branch only, NEVER merge to main on your own initiative.
* Never remove, prune, or clean up any transient document.
* All tick-engine DB operations stay wrapped with `database_sync_to_async` (standing async-safety rule). The new helper in this brief is a sync function called only from inside existing wrapped functions.
* Scope lock: exactly #143 and #25 as ruled. No flee-balance tuning — the ruled, eyes-open consequence that a low-DEX character (e.g. a STR/END Bulwark at DEX ~10) sits near 0% against bosses is ACCEPTED; do not compensate for it. No out-of-combat NPC regeneration system. No changes to the flee d20, cooldown, destination selection, or any flee/combat messaging. No boss/elite/normal distinctions anywhere in the reset. Anything discovered beyond scope: file a thin issue (assigned `--assignee @me` per standing convention), cite it in the closeout, do not fix it here.
* If any step's verification fails, stop at that step, commit what exists, and write the closeout explaining — do not proceed to issue closes or the architecture doc.

Pre-flight

1. Version 23 worktree, tree clean, branch synced with origin.
2. Prior pending deploy-time actions (standing rule): report B2's `purge_orphaned_items` production run as CONFIRMED DONE (executed 2026-07-24: 87 found / 87 deleted / 0 remaining, post-deploy sweep 0/0/0; #137 field-complete). No open deploy-time actions exist entering this brief. State this line in the closeout.
3. `django/src/apps/shyland/version.py` reads `SHYLAND_VERSION = "23.0-DEV"` (set by B2; this brief is not the version's first and does not touch it). If it reads anything else, STOP and report.
4. `DOCKER_HOST` is set and verified (required for Step 5's production deploy).
5. `gh auth status` shows repo access.

Step 0 — Self-commit this brief
Save this brief's full text verbatim to `docs/shyland/Shyland_V23_Brief_1_Flee_And_Disengagement.md` (skip the write if an identical file already exists). Commit on the branch and push immediately.
Step 1 — #143: fix the flee contest's NPC side
The defect (from the issue, confirmed against the branch): `cmd_flee` in `django/src/apps/shyland/consumers.py` (the contest sits at ~lines 2190–2197 on the current branch) computes the NPC side as:

```python
avg_per = sum(
    npc.definition.base_per * npc.definition.scaling_factor * npc.mk_tier
    for npc in npcs
) / len(npcs)

```

This multiplicative reading is pre-v21. Since the v21 balance retune (#101), `scaling_factor` is the NPC's within-band level (1–10) and `combat_utils.py` is the authority: `npc_level()` (~line 293) and `get_npc_stats()` (~line 299), where `per = base_per + round(2.5 × (L−1))`. The player side of this same contest already reads effective DEX (v22 B5, #100); the NPC side was never migrated. The broken formula contests a phantom stat 2–7× the NPC's real PER.
The ruled fix (from #143, verbatim in substance): the NPC side of the flee contest reads `get_npc_stats(npc)['per']` — the same effective-stats function every other combat read uses. Session average over that value replaces the inline formula. No other flee mechanics change: d20, cooldown, destination selection, and all messaging stay exactly as they are.
1a — The helper
In `django/src/apps/shyland/combat_utils.py`, add (near `get_npc_stats`):

```python
def flee_contest_npc_side(npcs):
    """v23 B1 (#143): the NPC side of the flee contest — the session
    mean of effective PER from get_npc_stats(), the same effective-stats
    read every other combat contest uses. Replaces a pre-v21 inline
    formula that multiplied base_per by scaling_factor (which since the
    v21 retune, #101, encodes within-band level, not a multiplier)."""
    return sum(get_npc_stats(npc)['per'] for npc in npcs) / len(npcs)

```

Callers guarantee `npcs` is non-empty (`cmd_flee` handles the empty session before the contest).
1b — The call site
In `consumers.py` `cmd_flee`, replace the inline `avg_per` computation with:

```python
# v23 B1 (#143): the NPC side reads the same effective stats as every
# other combat contest — session mean of get_npc_stats()['per'].
avg_per = flee_contest_npc_side(npcs)

```

Add `flee_contest_npc_side` to the existing `from .combat_utils import (...)` block at the top of `consumers.py` (~line 17). The success line (`success = (eff['dex'] + random.randint(1, 20)) > avg_per`) and everything around it is untouched.
Async note: `get_session_npcs` already returns instances with `select_related('definition')`, and `get_npc_stats` reads only loaded definition fields plus `vitality_current` — the helper performs no DB I/O at call time, so calling it in the async body is safe. Do not add a wrapper.
1c — The help-text correction
In `django/src/apps/shyland/models.py` (~line 753), the stale help text that produced this bug:

```python
scaling_factor  = models.FloatField(default=1.0, help_text="Stat multiplier per Mk tier.")

```

becomes:

```python
scaling_factor  = models.FloatField(default=1.0, help_text="Within-band level (1-10); Mk tier lifts the effective level by whole bands. See combat_utils.npc_level().")

```

Run `makemigrations`; if a migration is generated (expected — AlterField on help_text), commit it and cite its number in the closeout.
1d — The test
New test file `django/src/apps/shyland/tests/test_flee_disengagement.py` (this brief's single test home; Step 2 adds to it). Pin semantics, not snapshot numbers (the ruling's words):

* Build a mixed set of NPC instances (different `base_per`, `scaling_factor`, `mk_tier`, mixed combat tiers) and assert `flee_contest_npc_side(npcs)` equals `sum(get_npc_stats(n)['per'] for n in npcs) / len(npcs)` computed independently in the test.
* One arithmetic anchor from the issue's authoritative table (tables-over-prose, standing rule): an L6 normal at Mk 1 with `base_per=10`, `scaling_factor=6.0` has effective PER 22 (`10 + round(2.5 × 5)`; Python banker's rounding gives `round(12.5) == 12`). Assert `get_npc_stats(...)['per'] == 22` for that construction.

Step 1 verification (required before proceeding):

* Full suite green via `python manage.py test apps.shyland -t /app` (in-container, whole-app discovery — the standard established by v23 B2), including the new tests. Report the test count (306 at B2 close; it must only grow).
* `grep` confirms no remaining occurrence of the pattern `base_per * npc.definition.scaling_factor` (or any `base_per` × `scaling_factor` product) anywhere in `consumers.py`.
* `makemigrations --check` reports no missing migrations.

Commit and push.
Step 2 — #25: NPC reset on session-end-without-death
The ruling on #25 (operator-confirmed 2026-07-23) is the authoritative design direction. Its rule and five components, verbatim:
The rule: when a combat session ends without an NPC dying, and that NPC is participating in no other player's active combat session, the NPC resets to full vitality with its active effect instances cleared (bleeds, poisons, and any other lingering effects on it). This applies to all NPCs uniformly — no boss/elite/normal distinction.

1. Full reset, not regeneration. Keep it simple: no out-of-combat NPC regen system, no partial-recovery curve. The fight either kills the NPC or never happened, health-wise.
2. All NPCs, not just bosses. One rule, no tier check.
3. The trigger is session-end-without-death — this covers every disengagement path uniformly: successful flee, player death, and any future path that ends a session, with no per-path logic.
4. The multiplayer guard: reset fires only when the NPC exits its last active combat session. If another player is still fighting it (shared NPC instance across sessions), its vitality is live state and must not snap to full. The implementation must check remaining session membership before resetting.
5. Effects cleared with the reset.

Data-model reality note (design-chat finding 2026-07-24, recorded so you don't go hunting): NPCs cannot currently carry lingering effect instances — `EffectInstance.target` is a Character-only FK, and player procs (v22 B5 proc factors) resolve as instant bonus damage via `roll_gear_bonus_damage`, never as persistent state on the NPC. Ruling component 5 is therefore satisfied by construction today; the reset helper documents the invariant so any future NPC-targeted effect system clears its state at this single choke point. Do NOT build an NPC-effects model here — that would be out of scope.
2a — The helper (the single choke point)
In `django/src/apps/shyland/combat_utils.py`:

```python
def release_session_npcs(session):
    """v23 B1 (#25): session-end-without-death NPC reset.

    Called at EVERY session-end site, after the session has been marked
    inactive and saved. For each living NPC still in the session: if the
    NPC participates in no other active combat session (the multiplayer
    guard — a shared NpcInstance another player is still fighting is
    live state and must not snap to full), reset it to full vitality.
    All NPCs uniformly — no tier check. Full reset, not regeneration.

    INVARIANT: any NPC-targeted lingering-effect state must be cleared
    here as part of the reset. As of v23 no such state exists
    (EffectInstance targets Characters only; player procs are instant
    bonus damage) — a future NPC-effects system extends this function,
    nowhere else.

    Clears the session's NPC membership last.
    """
    npcs = list(session.npcs.filter(is_alive=True))
    for npc in npcs:
        if npc.combat_sessions.filter(is_active=True).exclude(pk=session.pk).exists():
            continue
        if npc.vitality_current != npc.vitality_max:
            npc.vitality_current = npc.vitality_max
            npc.save(update_fields=['vitality_current'])
    session.npcs.clear()

```

Notes that are law:

* The guard query excludes the ending session by pk AND filters `is_active=True`, so correctness does not depend on whether the caller's `is_active=False` save has landed — but callers still mark-and-save first (belt and suspenders, and it keeps the fight-feed consistent).
* `is_alive=True` filter: dead NPCs are never touched (they respawn at full via the respawn sweep; resetting a corpse-state instance would be wrong).
* Per-NPC `exists()` queries are acceptable here — sessions hold a handful of NPCs and session-end is not a per-tick hot path (per-tick query discipline is not violated).
* Sync function, DB-touching: it must only ever be called from inside `database_sync_to_async`-wrapped functions. Every call site below already is one.

2b — The four call sites (no per-path logic — every site routes through the helper)

1. `consumers.py` → `end_combat_session` (~line 4017). Currently:

```python
@database_sync_to_async
def end_combat_session(self, session):
    session.is_active = False
    session.save(update_fields=['is_active'])
    session.npcs.clear()

```

The `session.npcs.clear()` line becomes `release_session_npcs(session)` (add the import). This covers the successful-flee path and the flee-with-empty-session path (the helper is a no-op on an empty set).
2. Tick engine → `close_session` (stale-session cleanup, `management/commands/run_tick_engine.py` ~line 105). After `session.save(update_fields=['is_active'])`, add `release_session_npcs(session)` before building the status pairs. Deliberate behavior alignment (flag in the closeout, it is intended): this path previously left NPC membership rows in place on the inactive session; it now clears them like every other end path.
3. Tick engine → `execute_death` (~lines 199–203). Currently:

```python
for session in character.combat_sessions.filter(is_active=True):
    session.characters.remove(character)
    if session.characters.count() == 0:
        session.is_active = False
        session.save(update_fields=['is_active'])
        session.npcs.clear()

```

`session.npcs.clear()` becomes `release_session_npcs(session)`. This covers the player-death disengagement path.
4. Tick engine → the all-NPCs-dead session end (~lines 569–572, the `if not live_npcs:` branch). After the `session.save(update_fields=['is_active', 'focus_npc'])`, add `release_session_npcs(session)`. At this point every killed NPC has already been removed from the session and dead stragglers are filtered by `is_alive=True`, so the reset loop is a no-op — the call is here for uniformity (component 3: no per-path logic) and membership hygiene.

Add `release_session_npcs` to the tick engine's `from apps.shyland.combat_utils import (...)` block (~lines 75–79).
2c — Tests
In `tests/test_flee_disengagement.py`:

* Reset on last-session exit: NPC instance at half vitality in one session; mark the session inactive, run `release_session_npcs`; assert vitality equals max and the session's NPC membership is empty.
* Multiplayer guard: one NPC instance shared by two active sessions (one character each); end session A (mark inactive + helper); assert the NPC's vitality is UNCHANGED and only session A's membership cleared. Then end session B the same way; assert vitality now equals max.
* Dead NPCs untouched: an `is_alive=False` NPC at vitality 0 in an ending session stays at 0 and is not saved to full.
* Full-health no-op: an NPC already at max is not degraded and the helper completes cleanly.

Step 2 verification: full suite green via `python manage.py test apps.shyland -t /app`, including all new tests. `makemigrations --check` clean.
Commit and push.
Step 3 — Close the issues
Gated on Steps 1–2 verification passing in full.

* Close #143 with a comment summarizing: contest NPC side now `flee_contest_npc_side()` (session mean of `get_npc_stats()['per']`), help text corrected, migration number if generated, semantics test in place.
* Close #25 with a comment summarizing: `release_session_npcs()` choke point, four call sites, multiplayer guard, the data-model reality note (effects clause satisfied by construction; invariant documented for future NPC-effects work).

Commit and push anything the closes touched.
Step 4 — Architecture doc update (LAST code-adjacent step, gated)
This step is gated on all implementation and verification steps above being complete and passing.
`docs/shyland/Shyland_Architecture_v23.md` EXISTS on the branch (created by B2). This brief updates it in place — no new file, no version bump. This is an architectural change, so the header's commit hash moves to this brief's architectural commit. Update one section at a time, never one giant operation:

1. Combat system / flee: the flee contest's NPC side is the session mean of `get_npc_stats()['per']` via `combat_utils.flee_contest_npc_side()` — both sides of the contest now read effective stats (player: effective DEX since v22 B5; NPC: v23 B1). Note the corrected `scaling_factor` help text and that `combat_utils.npc_level()` is the semantic authority.
2. Combat sessions / NPC lifecycle: the session-end-without-death reset rule — `release_session_npcs()` as the single choke point, its four call sites (consumer `end_combat_session`, tick stale close, tick `execute_death`, tick all-NPCs-dead end), the multiplayer guard (reset only on last-active-session exit), full-reset-not-regeneration, all NPCs uniformly. Record the invariant: NPC-targeted lingering-effect state, when it exists, is cleared in this function and nowhere else (none exists as of v23 — EffectInstance is Character-targeted; procs are instant damage). Record the stale-close membership alignment.

Commit and push.
Step 5 — Production deploy and operator playtest handoff
Operator-authorized in-session production deploy (standing requirement): with `DOCKER_HOST` verified (pre-flight item 4), run `make prod`. This brief carries no deploy-time data actions — the deploy is code-only. If the deploy is not authorized in-session, record a PENDING DEPLOY-TIME ACTIONS block containing only the deploy itself and stop after the closeout.
Ready after deploy — operator playtest checklist

1. Flee works at all. Engage an L4–L6 normal NPC in the Verdant Reach with Shy-Guy (DEX 25); `flee`. Per the ruled arithmetic this should succeed essentially every attempt (table: 100% at those levels). The years of 0-for-everything are over or this brief failed.
2. Flee odds scale. Try an L8 elite (expect roughly 3-in-4 attempts to succeed) and an L10 boss (expect roughly half). Cooldown message between attempts should be unchanged.
3. Chip-and-run is dead (boss). Chip a boss visibly down, flee, regenerate, return: the boss is at FULL health (health description reads perfect health).
4. Chip-and-run is dead (normal). Same test on a normal NPC — one rule, no tier distinction.
5. Death path resets too. Let a fight kill Shy-Guy; after recall, return to the room: the NPC is at full health.
6. Multiplayer guard. With Sharon-Love and Shy-Guy both fighting the SAME NPC instance (attack the same spawn from the same room), have one flee: the remaining fighter's fight pane shows the NPC's health unchanged (no snap to full mid-fight). When the second player also disengages, the NPC resets.
7. Nothing else moved. Flee destination behavior (reverse-of-entry preferred), flee-into-aggro re-engagement, cooldown timing, and all flee messaging read exactly as before.

Step 6 — Closeout
Commit the closeout report as `docs/shyland/Shyland_V23_Brief_1_Closeout_Report.txt`, covering: pre-flight results (including the B2 deploy-time-action confirmed-done line), per-step verification results, the migration number (or the finding that none was generated), the test count delta, the stale-close alignment note, deploy execution (or the pending block if unauthorized), and the final commit hash.
Then, because this brief touched issues: run the issues report.
