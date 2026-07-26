Shyland V23 Brief 3 — Effects & Display
Type: implementation brief (bucket B3 of Version 23) Branch: the Version 23 worktree branch (`version_23`) — all work, commits, and pushes on that branch Issues: #133 (Focus Tonic overshoots the band system; no-op tick announcements), #119 (combat must not change pane border colors), #141 (level-up message split; stats hint removal) — all three close with this brief, gated on verification. This brief also FILES one new thin issue (Step 4) that it does not fix. Migrations: NONE (no model changes anywhere in this brief) Seed changes: NONE (#133 ruling 4: seeded magnitudes and durations stay untouched) Pending deploy-time actions: this brief creates NONE. It ends with an operator-authorized in-session production deploy (Step 7) so the operator can playtest.
All three issues carry operator-confirmed design rulings recorded on the issues themselves (comments dated 2026-07-23; #141's body plus its comment together are the ruling, with wording explicitly SETTLED). Those rulings are reproduced in this brief verbatim where they are law. If any repo fact contradicts this brief, stop and record the contradiction in the closeout rather than improvising.
Standing rules

* Work in the Version 23 worktree on branch `version_23`. Commit and push at every step boundary — branch only, NEVER merge to main on your own initiative.
* Never remove, prune, or clean up any transient document.
* Scope lock: exactly #133, #119, #141 as ruled, plus the one thin filing in Step 4. No retuning of tonic magnitudes, durations, or prices (#133 ruling 4). No changes to `dot_acuity` / `hot_acuity` announcement behavior (that is the Step 4 filing's territory — constants substitution in those branches is mechanical and in scope; behavior changes are not). No other pane-state styling work (#119 scope note: the parked "pane-not-reddening" observation stays parked). Anything else discovered beyond scope: file a thin issue (`--assignee @me` per standing convention), cite it in the closeout, do not fix it here.
* If any step's verification fails, stop at that step, commit what exists, and write the closeout explaining — do not proceed to issue closes, the deploy, or the architecture doc.

Pre-flight

1. Version 23 worktree, branch `version_23`, tree clean, branch synced with origin. Branch HEAD is, or descends from, `6f9021c` (the verified post-B2 tip). If not, STOP and report.
2. Deploy-time actions check (standing rule): the version's only prior pending deploy-time action — B2's `purge_orphaned_items` production run — is CONFIRMED DONE (executed 2026-07-24: 87 found / 87 deleted / 0 remaining; post-deploy sweep 0/0/0; #137 field-complete). Report this line in the closeout. No Version 23 deploy-time actions are pending as of this brief's start.
3. `SHYLAND_VERSION` is already `23.0-DEV` (bumped by B2, the version's first implementation brief). This brief does NOT touch `version.py`. Verify the constant reads `23.0-DEV` and report; if it doesn't, STOP.
4. `gh auth status` shows repo access.
5. `DOCKER_HOST` is set and verified (standing rule) — this brief ends with a production deploy (Step 7).
6. Standard test command for this brief (established by B2/#117): `python manage.py test apps.shyland -t /app`, in-container, whole-app discovery. Confirm it runs green before any change (306 tests at B2 closeout; record the count found).

Step 0 — Self-commit this brief
Save this brief's full text verbatim to `docs/shyland/Shyland_V23_Brief_3_Effects_And_Display.md` (skip the write if an identical file already exists). Commit on the branch and push immediately.
Step 1 — #133: acuity engine constants, the band-edge stop, and honest effect-tick announcements
The ruling on #133 (operator-confirmed 2026-07-23) is the authoritative design direction. Its six parts, verbatim:

1. Band-edge stop. `shift_acuity_high` never moves acuity past the drinker's own `acuity_band_high`. The per-tick application clamps to `min(band_high, current + magnitude)` instead of the 1.9 ceiling. Per-Origin behavior is automatic (Voidtouched climbs to 1.30, Undying tops at 1.00). Fiction: the tonic sharpens you to your mind's own limit; it can't push you past yourself. The 1.75× exploit dies; over-band becomes unreachable by any wired mechanic until future systems (panic spikes, hostile effects) claim it deliberately.
2. Reaching the edge holds, not ends. The effect runs its full duration; on ticks after band_high is reached, the value sits at band_high silently, with drift still paused by the active shift. The tonic is climb-and-sustain — honestly priced utility.
3. Announcements: change-only, plus a one-time terminal line. Effect ticks announce only when they change the value. Arrival at band_high fires exactly one terminal line — authored: "Your focus settles at its keenest." — then silence through the hold. Promoted to standing doctrine: effect ticks never announce no-ops; boundary arrival gets one terminal line; holding is silent.
4. Seeded magnitudes stay. magnitude 0.1 + 0.05×Mk per tick, duration 30 + 5×Mk — untouched. The band stop does the balancing; higher Mk climbs faster and holds longer. No price change.
5. The 0.1/1.9 clamps are ruled engine absolutes and kept — the meter's physical range, promoted from inline magic numbers to named constants (used by the tick engine's shift branches and `combat_utils.py:244` alike). Tonics can no longer reach the ceiling; the rails remain for everything else.
6. `shift_acuity_low` gets the announcement pattern only, not a band-edge stop. A hostile effect dragging acuity below band into fizzle territory is that attack's entire point; its boundary stays the 0.1 hard floor, with change-only ticks and a one-time floor terminal line. Its only consumer today is the placeholder Fracture Wraith kit — machinery-correctness, dormant until a zone ships it live.

Load-bearing fact from the ruling (no code change needed, verify it still holds): Phase 2 acuity drift is suspended while any shift effect is active — the has-shift exclusion in `run_tick_engine.py` (`acuity_shift_types` filter, ~line 1136). This is what makes "reaching the edge holds": the boundary-stopped tonic naturally holds its peak because drift never fights it. Do not touch this code; cite its line in the closeout as verified-present.
Rounding law (from the ruling, binding): the round-to-0.1 display behavior stays for climbing ticks; the final climbing tick lands exactly on `band_high` — band values are 2-decimal in the model. Clamp first, then round for display only; the stored value must equal `band_high` exactly so the in-band check (`acuity_damage_modifier`) and the stats-pane band gauge agree. `a > band_high` is False at equality → modifier 1.0, in-band. This exactness is a required test assertion.
1a — The engine constants (mechanical; zero behavior change)
In `django/src/apps/shyland/combat_utils.py`, with the other module constants at the top of the file:

```python
ACUITY_FLOOR = 0.1     # the acuity meter's physical range — engine
ACUITY_CEILING = 1.9   # absolutes, ruled #133 (v23); rails for everything

```

Replace every inline `0.1` / `1.9` acuity clamp literal with these constants at ALL SIX sites:

1. `combat_utils.py` ~line 244 (`acuity_damage_modifier`): `a = min(ACUITY_CEILING, max(ACUITY_FLOOR, character.acuity_current))`
2. `run_tick_engine.py` `dot_acuity` branch (~line 1054–55)
3. `run_tick_engine.py` `hot_acuity` branch (~line 1093–94)
4. `run_tick_engine.py` `shift_acuity_high` branch (~line 1106–07) — rewritten in 1b, uses the constants
5. `run_tick_engine.py` `shift_acuity_low` branch (~line 1118–19) — rewritten in 1c, uses the constants
6. `run_tick_engine.py` Phase 2 drift clamp (~line 1167)

`run_tick_engine.py` imports the constants from `combat_utils` (extend its existing import). After this sub-step, `grep -rn "min(1.9" django/src/apps/shyland/` and `grep -rn "max(0.1" django/src/apps/shyland/` return zero hits outside the constant definitions themselves — a verification requirement.
Sites 2, 3, and 6 get the constants ONLY — their behavior (including announcement behavior) is untouched by this brief (Step 4 files the follow-up).
1b — `shift_acuity_high`: band-edge stop + change-only announcements + terminal line
Replace the branch body (`run_tick_engine.py`, `elif ctype == 'shift_acuity_high':`) with this exact logic:

```python
old = character.acuity_current
band_high = character.acuity_band_high
if old >= band_high:
    new = old                      # never lowers, never exceeds — silent no-op
else:
    candidate = old + magnitude
    if candidate >= band_high:
        new = band_high            # stored EXACTLY (2-decimal); no 0.1 rounding
    else:
        new = round(max(ACUITY_FLOOR, candidate), 1)   # existing climb behavior

```

Then, by case:

* `new == old` (no change): do nothing at all. No save, no message, no status send. The tick is silent.
* `old < band_high and new == band_high` (the arrival tick): save `acuity_current`, build status, send exactly one line — text verbatim, no acuity suffix: `Your focus settles at its keenest.` — category `system`, with the status sync (the gauge carries the value). This line REPLACES the sharpens line on this tick; it fires at most once per climb because every later tick is a silent no-op.
* Otherwise (changed, not yet arrived): save, build status, send the existing line unchanged: `Your focus sharpens. (Acuity {new:.1f})`, category `system`, with status.

The `old >= band_high` guard implements the directional invariant (operator ruling 2026-07-24, this session): shift effects are one-way. `shift_acuity_high` moves acuity rightward only — it never lowers it; `shift_acuity_low` moves it leftward only — it never raises it. A drinker already at or above band_high gets a silent no-op, never a pull-down (`min(band_high, ...)` alone would drag an above-band value down, violating the invariant).
1c — `shift_acuity_low`: announcement pattern only (floor stays `ACUITY_FLOOR`)
Replace the branch body (`elif ctype == 'shift_acuity_low':`) with the same pattern against the hard floor — no band-edge stop (ruling 6):

```python
old = character.acuity_current
new = round(max(ACUITY_FLOOR, min(ACUITY_CEILING, old - magnitude)), 1)

```

* `new == old`: silent — no save, no message, no status.
* `old > ACUITY_FLOOR and new == ACUITY_FLOOR` (the floor-arrival tick): save, status, one terminal line — authored (creative content, standing policy): `Your focus frays to nothing.` — category `system`, with status. Fires at most once per drag; later ticks at the floor are silent no-ops.
* Otherwise: save, status, existing line unchanged: `Your focus wavers. (Acuity {new:.1f})`, category `system`, with status.

(0.1 is exact at one decimal, so the floor value survives the round unchanged — no special-casing needed. The directional invariant holds here by construction: the branch only ever subtracts, so `shift_acuity_low` can never raise acuity.)
1d — Tests
New tests placed with the suite as found (a new `tests/test_acuity_shifts.py` is acceptable; cite placement in the closeout):

* Band-edge stop, exact: a character with a 2-decimal `acuity_band_high` (e.g. 1.15) under repeated `shift_acuity_high` ticks climbs and stops; assert the stored `acuity_current` equals `acuity_band_high` exactly and never exceeds it.
* Gauge/modifier agreement: at the stopped value, `acuity_damage_modifier` returns exactly `1.0` (in-band at the top edge).
* Terminal line once: the arrival tick emits exactly `Your focus settles at its keenest.` (and not the sharpens line); every subsequent tick of the same effect emits nothing.
* Change-only: climbing ticks emit the sharpens line with the value; no-change ticks emit nothing (no message, no status).
* Directional invariant: a character starting above `band_high` (set via queryset `.update()` to bypass any validation, e.g. 1.9) under `shift_acuity_high` ticks keeps the value unchanged and receives no messages (the high shift never lowers); a character at `ACUITY_FLOOR` under `shift_acuity_low` ticks keeps the value unchanged (the low shift never raises — silent no-ops at the floor).
* Per-Origin automatic: a wide-band character (Voidtouched-shaped, band_high 1.30) stops at 1.30, not 1.15.
* `shift_acuity_low` floor: repeated ticks drag to exactly `ACUITY_FLOOR`, one `Your focus frays to nothing.` terminal line at arrival, silence after; change ticks emit the wavers line.
* Constants regression: `dot_acuity`, `hot_acuity`, and Phase 2 drift behavior is byte-for-byte unchanged (existing tests must stay green; if none cover these branches, that fact goes in the closeout — do not write new behavior tests for branches this brief doesn't change).

Step 1 verification: full suite green via `python manage.py test apps.shyland -t /app`, including the new tests. The two greps in 1a return zero non-definition hits.
Commit and push.
Step 2 — #119: combat stops recoloring the stats-pane border
The ruling on #119 (operator-diagnosed and settled 2026-07-23) is the authoritative design direction. Diagnosis from the ruling: the red border is `templates/shyland/game.html` line ~210 — the `border-bottom-color: var(--combat-accent)` declaration in the `#side-stats.in-combat` rule is a collision of two rulings: v20 brief 4 (#2) turned the whole stats subsection combat-red including its border, then v21 brief 1 (#85) established pane borders as zone-theme territory (`--zone-border`) — and the v20 border override survived unnoticed.
The fix, exactly: delete the `border-bottom-color: var(--combat-accent);` declaration from that rule. The rule becomes:

```css
#side-stats.in-combat { background: var(--combat-bg); }

```

Nothing else changes. The adjacent `#side-stats.in-combat #stats-name { color: var(--error); }` (line ~211) is untouched — the stats section still visibly enters its combat state through background and name color; only the border stops participating. `--combat-accent` itself remains defined and in use (the connection indicator, line ~318) — do not remove the variable.
Doctrine (promoted from this issue, ruled): pane borders belong to zone/area theming exclusively; combat state — and any other transient state — expresses through backgrounds and text, never through borders. This lands in the architecture doc in Step 8.
Scope note (from the ruling): the parked "pane-not-reddening" observation from the v22 closeout reports stays parked — this fix is the border only.
Step 2 verification: the chart-as-license set-equality test (and the full suite) stays green — deleting a usage changes no palette membership.
Commit and push.
Step 3 — #141: level-up message split + stats hint removal
The ruling on #141 (issue body + operator wording ruling 2026-07-23, SETTLED — no open questions) is the authoritative design direction.
3a — The level-up split
Single site: `run_tick_engine.py` ~lines 546–562, the level-up block inside the kill branch of `process_combat`. The current single `messages.append` becomes two appends — two messages, each with its own ts/seq envelope (consistent with the bulk-messaging rule), both keeping category `reward` (loot-color, per the ruling's color confirmation):

```python
messages.append((character.pk,
    f"You have reached level {character.level}! "
    f"Your Vitality is now {new_vit_max} and your Longevity is now {new_lon_max}.",
    'reward', None
))
messages.append((character.pk,
    f"You have {pts} unspent stat point{'s' if pts != 1 else ''}. "
    f"Type 'spend' to allocate them.",
    'reward', None
))

```

Binding details from the ruling:

* The `*** `prefix is intentionally dropped — both lines render without it, exactly as written in the issue body.
* Line two keeps the short form `Type 'spend' to allocate them.` — NOT the stats pane's fuller `spend [<quantity>] <stat>` syntax.
* `pts` is read after the `+= STAT_POINTS_PER_LEVEL` increment, so it already includes pre-level unspent points — no arithmetic change; carry the same value into message two.
* Multi-level rounds (the `while` loop) now produce two messages per level instead of one. That is correct and ruled-consistent.

3b — The stats hint removal
Single site: `consumers.py` ~lines 2313–2317, inside the `stats` report — delete the conditional hint block in its entirety:

```python
if character.unspent_stat_points > 0:
    lines.append(
        {'v': "  Type 'spend [<quantity>] <stat>' to allocate. (e.g. 'spend 2 str')"},
    )

```

The `Unspent stat points: N` line above it is untouched. Syntax discoverability survives via the help table row and `SPEND_USAGE` — verified in the ruling; change neither.
3c — Tests
The ruling's grep found no existing test asserting on either string. Add one test pinning the two-message form: a level-up emits exactly two `reward`-category messages, neither starting with `***`, the second containing the accumulated unspent count; and one test (or an extension of an existing stats-report test) asserting the hint line is absent from `stats` output while the `Unspent stat points:` line is present when points > 0.
Step 3 verification: full suite green via `python manage.py test apps.shyland -t /app`.
Commit and push.
Step 4 — File the doctrine follow-up issue (thin; NOT fixed in this brief)
Step 1's ruling 3 promoted a standing doctrine: effect ticks never announce no-ops; boundary arrival gets one terminal line; holding is silent. Two effect branches this brief deliberately does not touch still violate it:

* `hot_acuity` (~line 1090): at baseline, `step` computes to 0 and the branch announces `Your mind clears from {name}. (Acuity N)` every tick — a no-op announcement loop identical in shape to the one #133 fixed.
* `dot_acuity` (~line 1053) and the flat-floor resource DoTs share the clamp-and-announce structure at their floors.

File ONE thin issue via `gh issue create --assignee "@me"`, title along the lines of `hot_acuity / dot_acuity announce no-op effect ticks (doctrine from #133)`, body: the observed shape (the two sites above with approximate lines), a citation of #133's ruling 3 doctrine, and the note that the terminal-line wording for each branch is authored at fix time per standing creative policy. No milestone, no bucket label. Capture the issue number for the closeout. Do not fix it here — this is a filing, not a combined file-and-fix; no code in this brief depends on it.
Commit and push (if the filing produced no repo change, note that and continue).
Step 5 — Full verification

1. Full suite green: `python manage.py test apps.shyland -t /app` (whole-app discovery). Record the test count in the closeout (306 at B2 closeout, plus this brief's additions).
2. `makemigrations --check` clean (this brief must generate NO migrations — a produced migration is a STOP-and-report defect).
3. Clamp-literal greps from 1a return zero non-definition hits.
4. Invariant arithmetic: zero model changes, zero migrations, zero seed changes; exactly one CSS declaration deleted; exactly one message split into two; exactly one hint block deleted; exactly one new issue filed; exactly two new terminal-line strings introduced (`Your focus settles at its keenest.` / `Your focus frays to nothing.`).

Step 6 — Close the issues (gated on Step 5 passing)
Close each with a short comment citing its ruling:

* #133: closed — band-edge stop with exact-band_high storage, climb-and-sustain hold, change-only announcements with one-time terminal lines on both shift branches, engine clamps promoted to `ACUITY_FLOOR`/`ACUITY_CEILING`; seeded magnitudes untouched per ruling 4. Cite the Step 4 follow-up issue number for the remaining doctrine sites.
* #119: closed — `border-bottom-color` deleted from `#side-stats.in-combat`; borders are zone-theme territory per the promoted doctrine; combat state expresses through background and text only.
* #141: closed — level-up split into two `reward` messages without the `***` prefix, short spend hint on line two, accumulated count carried; stats-output hint block removed, count line intact.

Commit and push.
Step 7 — Production deploy (operator-authorized, in-session)
Standing implementation-brief requirement. With the operator's authorization in-session:

1. Verify `DOCKER_HOST` (pre-flight already did; re-confirm before touching production).
2. `make deploy && make migrate` (the migrate is a no-op for this brief — it ships no migrations — but the standard deploy invocation runs both).
3. This brief has no deploy-time data actions — no migrations, no seed reruns, no fixup commands. Record that explicitly in the closeout: the PENDING DEPLOY-TIME ACTIONS block reads `NONE — this brief created no deploy-time actions; B2's prior action is confirmed done (pre-flight item 2)`.

If the operator does not authorize the deploy in-session, record that, list nothing as pending (there are no data actions — the deploy itself simply waits on the operator), and continue to Step 8.
Ready after deploy — operator playtest checklist

* Focus Tonic (the headline): buy and use a Focus Tonic Mk 1. It climbs in visible steps, then prints `Your focus settles at its keenest.` exactly once at your band top — then silence while it holds. Acuity never reads 1.9 again (unless you started there), the stats-pane band gauge sits in-band at the peak, and the hold lasts the full ~35s before drift resumes.
* No damage steroid: in combat at the tonic peak, your damage against the focus target is band-neutral (no 1.75× spike).
* Border law: enter combat. The stats pane background shifts to combat and your name turns red — but the border below the pane stays zone-colored. Leave combat; nothing about borders changed at any point.
* Level up: gain a level in combat. Two separate green (loot-color) lines: the level/bars line, then the unspent-points line — no `***` prefix on either. If you had unspent points before the level, the count includes them.
* Stats output: with unspent points, `stats` shows `Unspent stat points: N` but no longer shows the `Type 'spend [<quantity>] <stat>' ...` hint line. `help` still documents the spend syntax; a bad `spend` still prints usage.

Step 8 — Architecture document (GATED, last)
This step is gated on all implementation and verification steps above being complete and passing.
File handling: `docs/shyland/Shyland_Architecture_v23.md` exists on the branch (created by B2). Update it in place — do not create a new file, do not bump the version stamp. The header hash moves (this brief's changes are architectural: engine constants, shift semantics, announcement doctrine) and the header narrative gains this brief's entry.
Section changes:

* Section 1 (Overview) intro: append the v23 continuation sentence in the established narrative style: v23 Brief 3 (B3 Effects & Display, #133/#119/#141) — acuity shift effects stop at the drinker's own band edge with change-only announcements and one-time terminal lines, the engine's 0.1/1.9 acuity rails promoted to named constants, combat state withdrawn from pane borders, and the level-up message split honestly in two.
* Section 4.5 (Combat utilities): document `ACUITY_FLOOR` / `ACUITY_CEILING` alongside the other constants — the acuity meter's physical range, ruled engine absolutes (#133), consumed by `acuity_damage_modifier` and every tick-engine acuity clamp; no inline 0.1/1.9 acuity literals remain.
* Section 4.9 (Tick Engine): the effect-application description documents the new `shift_acuity_high` semantics (band-edge stop at the character's own `acuity_band_high`, stored exactly; climb-and-sustain with drift paused by the has-shift exclusion) and `shift_acuity_low` (hard floor at `ACUITY_FLOOR`, no band stop — ruled); the directional invariant (shift effects are one-way: high never lowers, low never raises); plus the announcement doctrine now in force for both shift branches: effect ticks never announce no-ops; boundary arrival gets one terminal line; holding is silent — with the two authored terminal lines and a pointer to the Step 4 issue for the branches not yet migrated to the doctrine. The level-up messaging description documents the two-message form (both `reward`, no `***` prefix, accumulated count on line two).
* Section 4.15 (UI layout) — where the combat state of `#side-stats` is documented: the combat state is background + name color only; the border declaration is gone. Record the doctrine: pane borders belong to zone/area theming exclusively; transient state (combat included) expresses through backgrounds and text, never borders (#119, reconciling v20 brief 4 with v21 brief 1's zone-border ruling).
* Section 6 (Key Design Decisions): add rows (or entries, matching the section's local form) for the borders doctrine (#119) and the effect-tick announcement doctrine (#133 ruling 3); note the 0.1/1.9 rails as ruled engine absolutes.

Commit and push.
Step 9 — Closeout
Write `docs/shyland/Shyland_V23_Brief_3_Closeout_Report.txt` containing:

* What shipped per issue and the fix shapes; the test count (suite green via whole-app discovery) and new-test placement.
* The pre-flight deploy-time actions line (B2's purge confirmed done) and the `SHYLAND_VERSION` check result.
* The verified-present citation for the Phase 2 has-shift drift exclusion (line number at implementation time).
* The Step 4 filed issue number.
* The PENDING DEPLOY-TIME ACTIONS block: `NONE` (with the B2-confirmed-done note), per Step 7.
* Whether the Step 7 deploy executed in-session (and the `make deploy && make migrate` result) or awaits the operator.
* Confirmation the architecture doc was updated in place (no new file, no stamp bump, hash moved).
* Any deviations or discrepancies (including whitespace-only Step 0 drift, report-and-accept per standing practice).
* The final commit hash.

Commit and push. Do not remove or prune any documents.
Step 10 — Final instruction
run the issues report
