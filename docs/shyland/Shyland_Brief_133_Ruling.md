Shyland Brief: Issue #133 Ruling Recorded + Triaged
Type: Ops / housekeeping brief — runs on `main`, no worktree, no code changes of any kind. Issues touched: #133 (comment + add `triaged` label). No other state changes: no closes, no milestone changes, no assignee changes, no dependency links, no other labels modified.
Pre-flight

1. Working tree is clean and you are on `main`. If either is false, STOP and report.
2. Confirm the label `triaged` exists. If not, STOP and report.
3. No deployment surface is touched by this brief.

Step 0 — Self-commit
Save this brief's full text verbatim to `docs/shyland/Shyland_Brief_133_Ruling.md` (skip if an identical file exists). Commit on `main` and push immediately.
Step 1 — Post the ruling comment on #133
Add the following comment to #133, verbatim:
Design-chat ruling 2026-07-23 — settled in full by the operator. This comment is the authoritative design direction for the fix; the implementation brief will cite it.
Correction to this issue's facet-1 framing, from code: over-band is not penalty territory. `acuity_damage_modifier` (`combat_utils.py:239-248`, the v19 wiring) grants `1.0 + (a − band_high)` outgoing damage against the focus target when above band; the hyper-focus drawback (flanking undetected) is GDD doctrine but was never wired (scope law — only what combat reads). At the 1.9 clamp, a Highborn (band_high 1.15) gets 1.75× focus-target damage for ~35 seconds for 15 copper. The tonic is not stranding drinkers in a penalty zone; it is a grossly underpriced damage steroid. Facet 1 stands, pointed the other direction. Also load-bearing: Phase 2 acuity drift is suspended while any shift effect is active (the has-shift exclusion in `run_tick_engine.py`), so a boundary-stopped tonic naturally holds its peak.
The six-part ruling:

1. Band-edge stop. `shift_acuity_high` never moves acuity past the drinker's own `acuity_band_high`. The per-tick application clamps to `min(band_high, current + magnitude)` instead of the 1.9 ceiling. Per-Origin behavior is automatic (Voidtouched climbs to 1.30, Undying tops at 1.00). Fiction: the tonic sharpens you to your mind's own limit; it can't push you past yourself. The 1.75× exploit dies; over-band becomes unreachable by any wired mechanic until future systems (panic spikes, hostile effects) claim it deliberately.
2. Reaching the edge holds, not ends. The effect runs its full duration; on ticks after band_high is reached, the value sits at band_high silently, with drift still paused by the active shift. The tonic is climb-and-sustain — honestly priced utility.
3. Announcements: change-only, plus a one-time terminal line. Effect ticks announce only when they change the value. Arrival at band_high fires exactly one terminal line — authored: "Your focus settles at its keenest." — then silence through the hold. Promoted to standing doctrine: effect ticks never announce no-ops; boundary arrival gets one terminal line; holding is silent. (The muted-'system'-voice question for these lines remains separately tracked as recorded in the B5 Amendment 3 closeout — not scope here.)
4. Seeded magnitudes stay. magnitude 0.1 + 0.05×Mk per tick, duration 30 + 5×Mk — untouched. The band stop does the balancing; higher Mk climbs faster and holds longer. No price change.
5. The 0.1/1.9 clamps are ruled engine absolutes and kept — the meter's physical range, promoted from inline magic numbers to named constants (used by the tick engine's shift branches and `combat_utils.py:244` alike). Tonics can no longer reach the ceiling; the rails remain for everything else.
6. `shift_acuity_low` gets the announcement pattern only, not a band-edge stop. A hostile effect dragging acuity below band into fizzle territory is that attack's entire point; its boundary stays the 0.1 hard floor, with change-only ticks and a one-time floor terminal line (authored at implementation, same doctrine). Its only consumer today is the placeholder Fracture Wraith kit — machinery-correctness, dormant until a zone ships it live.

Rounding note for the implementer: the round-to-0.1 display behavior stays; with the band stop, the final climbing tick lands exactly on band_high (band values are 2-decimal in the model — clamp first, then round for display only; the stored value must equal band_high exactly so the in-band check and gauge agree).
Step 2 — Add the `triaged` label to #133
Per the standing definition — complete diagnosis plus ruling on-issue. Leave `bug` and all other state untouched.
Closeout

1. Commit a closeout report as `docs/shyland/Shyland_Brief_133_Ruling_Closeout.txt` on `main`: confirmation the comment was posted verbatim, confirmation of the label addition, confirmation of zero other state changes, final commit hash.
2. Push.
3. Run the issues report.
