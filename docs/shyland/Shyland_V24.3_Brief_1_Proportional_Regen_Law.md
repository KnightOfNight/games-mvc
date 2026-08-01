# Shyland V24.3 — Brief 1: The Proportional Regen Law

- **Release:** Version 24.3 (milestone `Version 24.3`; branch `version_24_3`)
- **Founding ticket:** #165 (out-of-combat vitality regen is too slow and doesn't scale) — the sole issue of this release
- **Produced by:** V24.3 design session, 2026-08-01
- **Session type to apply it:** Implementation, on branch `version_24_3`
- **GDD:** §4.1 / §4.3 Recovery text already landed on this branch (commit `f5cb16a`) with "(v24.3, pending implementation)" markers — read it; never edit it (marker removal is design/closeout work)

---

## 1. Context

Out-of-combat regen is deficit-proportional today: `ceil(deficit / CONSTANT)` per tick. For Vitality that is exponential decay with a 1 HP/s tail — ~100 s at a 100-max bar but ~5.6 minutes at the L12/718 reference, the last ~120 HP always crawling at 1 HP/s. For Longevity the same formula degenerates: because `longevity_max` (~274) is far below its 3600 constant, the ceil is always 1 — a flat 1 point/second, refilling from zero in ~4.6 minutes and silently falsifying the GDD's "at most one hour" claim.

The ruled fix (#165, operator-confirmed 2026-07-30, amendment same session): **regen is proportional to maximum.** Full refill from zero takes the constant's number of seconds at every level, forever. Vitality: exactly 120 s. Longevity: about one hour.

## 2. Binding design rulings — do not deviate

1. **The law:** out-of-combat regen rate = `bar_max / CONSTANT` points per second. `VITALITY_REGEN_SECS = 120`, `LONGEVITY_REGEN_SECS = 3600`. Neither constant changes; both constants' comments in `models.py` become true.
2. **Vitality uses the per-tick form:** `heal = ceil(vitality_max / VITALITY_REGEN_SECS)` per tick, clamped at max (the existing `min()`).
3. **Longevity uses the interval form:** one point every `ceil(LONGEVITY_REGEN_SECS / longevity_max)` seconds (~14 s at a 274 bar → ~64 min from zero). The vitality form cannot express the law here — `ceil(274 / 3600)` is always 1 (the ceil trap). Key the interval off the engine's existing `tick_number` (regen fires on ticks where `tick_number % interval == 0`); an engine restart resetting `tick_number` at worst delays one point by up to one interval — accepted, no persistent state, **no model changes**.
4. **Unchanged and binding:** the in-combat exclusion, the dying-state exclusion, regen silence (no output message ever; the status-pane push on changed fields is the only signal), tick-loop async-safety conventions (Section 4.9's rule: sync helpers cross into the async loop only via `database_sync_to_async` or on verifiably prefetched data).
5. **Out of scope:** acuity drift (#142, Phase 3), any Longevity drain (#70, deferred out of V24), heal command (#166 — its own release), seed data, models, migrations.
6. Known boundary, not scope: if `longevity_max` ever exceeds `LONGEVITY_REGEN_SECS`, the interval form saturates at 1 point/tick (slower than the law). Bars are nowhere near that; if play ever approaches it, file a new issue — do not pre-build for it.

## 3. Implementation

### Step 1 — Version constant (opening act, own commit)

First implementation brief of the release: bump `SHYLAND_VERSION` from `"24.2"` to `"24.3-DEV"` in `django/src/apps/shyland/version.py` (line 8), and move the pin-test assertion in `django/src/apps/shyland/tests/test_b2_amendment1.py` (line 118, `assertEqual(SHYLAND_VERSION, '24.2')`) to `'24.3-DEV'` **in the same commit**. Then run the version-start `make deploy-dev` from the worktree.

### Step 2 — Phase 4 rewrite

File: `django/src/apps/shyland/management/commands/run_tick_engine.py`, Phase 4 ("Passive bar regeneration", currently ~lines 1313–1366, at the tail of `process_effects(self, tick_number)` — `tick_number` is already in scope).

- **Vitality branch** (~1344–1351): replace
  `heal = math.ceil((character.vitality_max - character.vitality_current) / VITALITY_REGEN_SECS)`
  with
  `heal = math.ceil(character.vitality_max / VITALITY_REGEN_SECS)`.
  The existing `min(current + heal, max)` clamp stays.
- **Longevity branch** (~1353–1360): replace the deficit formula with the interval form:
  `interval = math.ceil(LONGEVITY_REGEN_SECS / character.longevity_max)`; heal exactly **1** point only when `tick_number % interval == 0`, else nothing this tick. Clamp at max (a 1-point heal below max never exceeds it, but keep the `min()` shape for uniformity). Guard division: `longevity_max` is always ≥ 1 in practice; do not add speculative handling beyond what the expression needs.
- Candidate selection (`get_regen_candidates`), the combat/dying exclusions, `save_regen`, and the changed-fields status push are all unchanged. On a tick where only the longevity branch runs and it is not an interval tick, no field changes → no save, no status push (existing behavior of the `changed_fields` gate — preserve it).

### Step 3 — Migration

**None.** No model changes in this brief. (Stated per the standing rule; if you find yourself writing one, stop — the brief is wrong or the work has drifted.)

### Step 4 — Tests

New file `django/src/apps/shyland/tests/test_v243_regen.py`, driving the Phase 4 path directly in async context (follow the `tests/test_tick_expiry.py` pattern for exercising `process_effects` with an explicit `tick_number`). Required cases:

1. **Vitality rate:** a character with `vitality_max = 718` and a large deficit heals exactly `ceil(718/120) = 6` per tick.
2. **Vitality clamp:** at `max − 1`, one tick heals exactly 1 (clamped, never overshoots).
3. **Vitality law end-to-end:** from zero, the number of ticks to full is `ceil(718 / 6) = 120` — the 120 s promise within one tick.
4. **Longevity interval:** with `longevity_max = 274` (interval `ceil(3600/274) = 14`), a tick where `tick_number % 14 == 0` heals exactly 1; the adjacent tick heals 0.
5. **Longevity law:** from zero at a 274 bar, full recovery spans `274 × 14 = 3836` ticks (~64 min) — assert the arithmetic via the interval, not a 3836-iteration loop.
6. **Exclusions unchanged:** a character in an active combat session regens neither bar; a character with `is_dying=True` regens neither bar.
7. **Silence:** regen produces no output message — only a status push, and only on ticks where a field changed.

In-container invocation (the only working form): `python manage.py test apps/shyland/tests` via `docker exec` in the django container. The full suite must pass, not only the new file.

## 4. Verification

- Full in-container test suite green (path form above).
- Manual arithmetic spot-check in `make shell`: set a character's `vitality_current` low, confirm per-tick recovery at `ceil(vitality_max/120)` by observing two ticks' values; set `longevity_current = longevity_max - 5`, confirm one point lands roughly every `ceil(3600/longevity_max)` seconds and the bar tops out clamped.
- Confirm no new queries per tick beyond the existing Phase 4 shape (the change is arithmetic, not data access).

## 5. Dev deploy

`make deploy-dev` from the worktree once implementation and verification pass (in addition to Step 1's version-start deploy). Production is never deployed from an implementation session.

**PENDING DEPLOY-TIME ACTIONS: none.** No seed changes, no data actions, nothing for the closeout tail's window. (No prior briefs exist in this release, so there are no carried-forward pending actions either.)

## 6. Operator playtest checklist (dev stack)

1. Fight something in the Verdant Reach, take real damage, disengage, and stand still out of combat: the vitality bar visibly climbs every tick and a deep deficit fully refills in ~2 minutes — no 1-HP/s tail crawl at the end.
2. Confirm the output pane stays silent for the whole refill (bars move in the stats pane only).
3. Confirm regen halts while in combat and while dying (take a fight to Dying if you're willing — the bar must not move until respawn's own refill).
4. Longevity (shell-assisted — nothing in play drains it): after a `make shell` nudge of `longevity_current` downward, watch the stats pane recover ~1 point per ~14 s. If you'd rather skip this half, the automated tests cover it — say so in the disposition.

## 7. Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. Update `docs/shyland/Shyland_Architecture_v24.md` **in place**:

- **§4.9 (Tick Engine):** add a passive-regen paragraph — Phase 4's proportional-to-max law, both forms (vitality per-tick ceil, longevity `tick_number`-modulo interval with the ceil-trap rationale), the unchanged exclusions and silence, the restart-resets-`tick_number` acceptance.
- **Header blockquote:** stamp line to Version 24.3 / Brief 1 applied on `version_24_3`, hash moved to this brief's final implementation commit — this is an architectural change (tick-engine behavior), so the hash moves. Follow the 24.2 header's form.
- The constants block copy (§4.1 area, `VITALITY_REGEN_SECS`/`LONGEVITY_REGEN_SECS`) keeps its values; its comments are now accurate — no edit needed unless the doc quotes the old formula elsewhere (check and update any such quote).

## 8. Closeout report

`docs/shyland/` `.txt` per standing process: stub pushed at Step 0 (session start), completed in place at session end — final commit hash, deviations (including any test-hygiene conversions, none expected), the PENDING DEPLOY-TIME ACTIONS block (none), and the **operator playtest disposition** line (one of the three ruled forms — the closeout session reads it as a gate). Issue #165 closes gated on verification passing. End with the `implementation-session-end` ritual; issue-touching work ends with "run the issues report".
