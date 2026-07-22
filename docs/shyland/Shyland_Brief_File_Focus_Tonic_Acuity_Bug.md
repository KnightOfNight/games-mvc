Shyland Brief — File Focus Tonic Acuity Bug
Type: ops/housekeeping brief (zero code changes; does not count against any cap) Branch: the current Version 22 worktree branch (`version_22`) — this brief runs in the v22 CC session; commits land on that branch as all v22 work has Scope: file exactly one issue, verbatim, then the issues report. Nothing else. Migrations: NONE. Pending deploy-time actions: NONE (the standing pre-flight check should confirm none remain outstanding — expected state: the B5 data actions ran 2026-07-21).
This brief files a single untriaged bug capturing everything currently known about the Focus Tonic's behavior under the v19+ acuity band system. It is deliberately NOT milestoned — deeper triage comes later. Do not diagnose further, do not label beyond `bug`, do not milestone, do not change any code or data.
Standing rules

* Work in the Version 22 worktree on its branch. Commit and push the branch at every step boundary — branch only, NEVER merge to main on your own initiative.
* Never remove, prune, or clean up any transient document.
* If any repo fact contradicts this brief, stop and record the contradiction in the closeout rather than improvising.

Pre-flight

1. Confirm you are in the Version 22 worktree, tree clean, branch synced with its remote.
2. Deploy-time actions check (standing rule): confirm no prior pending deploy-time data actions remain unexecuted.
3. `gh auth status` shows repo access.

Step 0 — Self-commit this brief
Save verbatim to `docs/shyland/Shyland_Brief_File_Focus_Tonic_Acuity_Bug.md` (skip if an identical file exists). Commit on the worktree branch and push the branch immediately.
Step 1 — File the issue
Create exactly one issue. Capture its number from the `gh issue create` output for the closeout.

* Title: `Focus Tonic overshoots the acuity band system and announces no-op ticks at the 1.9 clamp`
* Labels: `bug`
* Milestone: none
* Body (verbatim):


```
UNTRIAGED — filed with everything known so far; deeper triage to follow in
a future design pass. Two facets of one problem, observed in play
2026-07-22 and confirmed against code.

OBSERVED (operator playtest, production):

    You buy the Focus Tonic Mk 1 for 1 silver, 5 coppers.
    You use a Focus Tonic Mk 1.
    Your focus sharpens. (Acuity 1.1)
    Your focus sharpens. (Acuity 1.2)
    Your focus sharpens. (Acuity 1.4)
    Your focus sharpens. (Acuity 1.5)
    Your focus sharpens. (Acuity 1.6)
    Your focus sharpens. (Acuity 1.8)
    Your focus sharpens. (Acuity 1.9)
    Your focus sharpens. (Acuity 1.9)   <- no change
    Your focus sharpens. (Acuity 1.9)   <- no change
    Your focus sharpens. (Acuity 1.9)   <- no change

CODE FACTS (as of branch state ~ac01d37; cite-checked):

- Effect: EffectDefinition 'focus-tonic', single component
  shift_acuity_high with magnitude_base 0.1, magnitude_scaling 0.05,
  duration_base 30.0, duration_scaling 5.0
  (management/commands/seed_world.py, "--- Focus Tonic ---" block).
  At Mk 1: +0.15 per effect tick for ~35s — an attempted total shift of
  roughly +1.6.
- Application: run_tick_engine.py, shift_acuity_high branch —
  acuity_current = round(max(0.1, min(1.9, current + magnitude)), 1).
  1.9 is a hardcoded ceiling; the rounding explains the displayed skips
  (1.2 -> 1.4, 1.6 -> 1.8).
- The "Your focus sharpens. (Acuity N)" line fires on EVERY effect tick,
  including ticks where the clamp makes the change a no-op — the
  repeated identical 1.9 lines above.

FACET 1 — BALANCE/DESIGN (the substantive bug): under the v19
band-relative acuity redesign, every Origin's optimal band tops out at
1.15 except Voidtouched at 1.30 (GDD Origins table). A 15-copper
consumable that drives acuity to the 1.9 ceiling launches every Origin
far PAST its band into over-band (hyper-focus penalty) territory — the
opposite of what "Focus Tonic" advertises. The magnitude/duration tuning
reads as pre-v19 (authored when acuity was a simple more-is-better
meter) and was never re-tuned for the band system. A band-aware tonic
would nudge acuity toward/into band, not to the ceiling.

FACET 2 — DISPLAY: announcing no-op ticks at the clamp is the
no-change-message anti-pattern. Honest behavior at the ceiling is
silence or a one-time terminal line (e.g. "Your focus can sharpen no
further."). Related but separately tracked: these effect lines speak in
the muted 'system' voice — already recorded in the untouched-sends list
of the B5 Amendment 3 closeout as future ruling material.

Also noted for the eventual triage: shift_acuity_low (Fracture Wraith
territory) shares the same clamp-and-announce structure and should be
examined alongside whatever ruling fixes facet 2.

Design questions for the future pass: intended tonic magnitude/duration
under band rules; whether shifts should taper or stop at band edges;
per-Origin behavior (Voidtouched's wide band); the terminal-line wording;
whether the 1.9/0.1 hard clamps themselves are design or legacy.

```

Verification gate
Verify via `gh issue view`: title, body content-identical, label exactly `bug`, no milestone. Any deviation: STOP, run the issues report, closeout explaining. Do not retry creatively.
Step 2 — Closeout
Write `docs/shyland/Shyland_Brief_File_Focus_Tonic_Acuity_Bug_closeout.txt`: the new issue number, gate result, and the final commit hash. Commit and push.
Step 3 — Final instruction
run the issues report
