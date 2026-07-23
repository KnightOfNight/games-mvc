# Shyland Brief: File Flee-Contest Bug (Fat, Ruled, Triaged)
**Type:** Ops / housekeeping brief — runs on `main`, no worktree, no code changes of any kind.
**Issues touched:** one NEW issue (create, milestone, labels, assignee). No other issue is modified. No dependency links — the #25 relationship is body text only.
---
## Pre-flight
1. Working tree is clean and you are on `main`. If either is false, STOP and report.
2. Confirm labels `bug` and `triaged` both exist. If either is missing, STOP and report.
3. No deployment surface is touched by this brief.
## Step 0 — Self-commit
Save this brief's full text verbatim to `docs/shyland/Shyland_Brief_File_Flee_Contest_Bug.md` (skip the write if an identical file already exists). Commit on `main` and **push immediately**.
## Step 1 — File the issue
Create a new issue with the title:
**Flee is mathematically impossible — the contest computes NPC PER with pre-v21 scaling_factor semantics**
Milestone: `Version 23`. Labels: `bug`, `triaged`. Assignee: the operator (`--assignee "@me"`, standing convention). Body exactly as follows:
---
**Symptom (operator, live play):** no successful flee in many hours of playtesting across many attempts. Confirmed by code analysis 2026-07-23 (design chat): for a DEX 25 character, flee is arithmetically impossible against any NPC above the weakest trash. This is not variance.
**Diagnosis — a semantic collision on `scaling_factor`:**
The flee contest (`consumers.py:2172-2182`) computes the NPC side as:
```python
avg_per = sum(
    npc.definition.base_per * npc.definition.scaling_factor * npc.mk_tier
    for npc in npcs
) / len(npcs)
...
success = (eff['dex'] + random.randint(1, 20)) > avg_per
```
This **multiplicative** reading matches the stale model help text (`models.py:750`: "Stat multiplier per Mk tier") — but the v21 balance retune (#101) redefined `scaling_factor` as the NPC's **within-band level** (1–10), with `combat_utils.py` as the authority: `npc_level()` (`combat_utils.py:293-296`) and `get_npc_stats()` (`combat_utils.py:299-318`), where effective stats grow **additively** — `per = base_per + round(2.5 × (L−1))`. The flee formula was never migrated to the new semantics. Note the v22 B5 pass (#100) modernized the *player* side of this exact contest to effective DEX and left the NPC side untouched — half the line lives in v22, half in v18.
**The arithmetic:**
| vs. (at Mk 1) | broken avg_per | true eff PER | DEX 25 odds (broken) | DEX 25 odds (fixed) |
|---|---|---|---|---|
| L4 normal (base_per 9, sf 4.0) | 36 | 17 | 45% | 100% |
| L6 normal (base_per 10, sf 6.0) | 60 | 22 | 0% | 100% |
| L8 elite (base_per 12, sf 8.0) | 96 | 30 | 0% | 75% |
| L10 boss (base_per 14, sf 10.0) | 140 | 36 | 0% | 45% |
The broken formula contests a phantom stat 2–7× the NPC's real PER; anything with `sf ≥ 5` is unreachable at any d20 roll for a DEX 25 character.
**Ruled fix direction (design-chat ruling 2026-07-23):**
1. The NPC side of the flee contest reads `get_npc_stats(npc)['per']` from `combat_utils` — the same effective-stats function every other combat read uses, and the symmetric partner to the player side's effective DEX. Session average over that value replaces the inline formula. No other flee mechanics change: d20, cooldown, destination selection, and all messaging stay as they are.
2. The stale `scaling_factor` help text on `NpcDefinition` (`models.py:750`) is corrected to the v21 semantics ("within-band level (1–10); Mk tier lifts by whole bands") as part of the same fix, so the trap that produced this bug is disarmed at the source. Help-text-only model change — confirm at implementation whether a migration is generated and include it if so.
3. Verification: a test pinning that the flee contest's NPC side equals the session mean of `get_npc_stats()['per']` — semantics, not snapshot numbers.
**Ruled eyes-open consequence:** DEX is the escape stat. Post-fix, a low-DEX character (e.g. a STR/END Bulwark at DEX ~10) sits near 0% against bosses — the tank can't run from the big ones. Accepted as coherent for now; any deeper flee-balance tuning is a separate future question, not scope here.
**Coupling — same-version requirement:** the chip-and-run boss exploit (#25) is currently unreachable *because* flee is broken; fixing flee re-arms it. This fix and #25's fix ship in the same version (both Version 23). #25's ruling is pending in the design chat.
---
Capture the new issue's number at runtime from the `gh issue create` output for the closeout report.
## Closeout
1. Commit a closeout report as `docs/shyland/Shyland_Brief_File_Flee_Contest_Bug_Closeout.txt` on `main`: the new issue number, confirmation of milestone/labels/assignee, confirmation that no other issue was touched, final commit hash.
2. Push.
3. **Run the issues report.**
