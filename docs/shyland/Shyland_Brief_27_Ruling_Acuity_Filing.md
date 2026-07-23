# Shyland Brief: Issue #27 Ruling + Acuity Design Filing

**Type:** Ops / housekeeping brief — runs on `main`, no worktree, no code changes of any kind.
**Issues touched:** #27 (comment + close), one NEW issue (create, milestone, comment). No label changes anywhere. No dependency links (`--blocked-by` etc.) — cross-references are comments only, per operator ruling.

---

## Pre-flight

1. Working tree is clean and you are on `main`. If either is false, STOP and report.
2. No deployment surface is touched by this brief. Do not build, deploy, or run any management command against any database.

## Step 0 — Self-commit

Save this brief's full text verbatim to `docs/shyland/Shyland_Brief_27_Ruling_Acuity_Filing.md` (skip the write if an identical file already exists). Commit on `main` and **push immediately**.

---

## Step 1 — Ensure milestone "Version 24" exists

Check whether a milestone named exactly `Version 24` exists. If not, create it (no due date, no description required). Report in the closeout whether it was found or created.

## Step 2 — File the new acuity design issue

Create a new issue with the title:

**Finish the acuity design: in-combat drift is unruled**

Milestone: `Version 24`. No labels. Body exactly as follows (fix nothing, add nothing):

---

**Origin:** split out of #27 per design-chat ruling 2026-07-23. The research spike on #27 (see its findings comment) corrected that issue's premise — the observed "regen" lines were consumable heals — but surfaced this: **Acuity drift has no in-combat exclusion.** Phase 2 of the tick engine pulls every character's acuity toward their Origin baseline on every tick, in combat or out, while the Phase 4 Vitality/Longevity regen pass explicitly excludes in-combat characters. Nobody ever ruled what combat should do to the mind's pull toward baseline — the asymmetry exists because the question was never asked. This is unfinished design, not a bug, hence a feature-version item.

**Everything we know about acuity so far:**

*Doctrine (GDD §Three Bars):* Acuity is the mind's dynamic state — explicitly not a sanity meter. Each Origin has a baseline and an optimal band; the system has been band-relative and deviation-based since v19. Too LOW: spells fizzle, aim drifts, awareness collapses. Too HIGH: hyper-focus — single-target bonus, but flanking enemies go undetected. (Doctrine; verify current combat-wiring status against the architecture doc before designing.)

*Origin values (decimal scale; GDD authoritative):*

| Origin | Baseline | Band Low | Band High |
|---|---|---|---|
| Highborn | 1.0 | 0.85 | 1.15 |
| Feral | 0.95 | 0.80 | 1.10 |
| Streetborn | 1.0 | 0.85 | 1.15 |
| Irradiated | 0.90 | 0.75 | 1.05 |
| Undying | 0.80 | 0.65 | 1.00 |
| Machinekind | 1.05 | 0.90 | 1.20 |
| Voidtouched | 0.70 | 0.40 | 1.30 |

*Code facts (from the #27 spike, verified against current main):* drift runs in tick Phase 2 with no combat-membership check; Vitality/Longevity regen runs in Phase 4 with an explicit in-combat exclusion (`run_tick_engine.py:1267` at time of spike) and has been silent since its v14 introduction. The two recovery systems are structurally asymmetric today.

*UI:* the stats pane renders the Acuity band gauge (v20; repainted v22 — success-color fills, solid band, say-color 16×4 tick).

*Consumables:* Focus Tonic and `shift_acuity_low` shift acuity via instant/tick effect components. **#133 (Version 23)** covers the tonic's defects against the current band rules — it drives to the 1.9 clamp past every Origin's band and announces no-op ticks; its magnitude/duration/taper/terminal-line/clamp questions are open there. Sequencing note: #133 will re-tune the tonic against *current* drift behavior; whatever this issue rules about in-combat drift may reshape tonic assumptions again. The two rulings should be made aware of each other.

*Related systems:* the Warden archetype is designed as the healer / acuity manager. The combat-economy pile (#25 heal-on-disengage, #26 and kin) concerns what recovers during and around combat — this issue is the acuity-shaped member of that family.

**The design question for Version 24:** what does combat do to acuity drift? Sketch of the option space (none ruled): (a) pause drift in combat entirely — symmetric with the other two bars; (b) keep drift running as-is — maintaining an off-baseline state mid-fight requires active upkeep, which gives the Warden a job and makes high-acuity states a spend; (c) combat-specific drift — rate or direction changes under stress, possibly per-Origin. Interactions to resolve: band-based combat effects wiring, tonic timing/duration post-#133, Voidtouched's deliberately wide band, and whatever the combat-economy rulings decide about recovery during engagement.

---

Capture the new issue's number at runtime from the `gh issue create` output. Call it **#N** below.

## Step 3 — Close #27 with the ruling comment

Add the following comment to #27, then close the issue (close as completed / not-planned per your tooling default — the comment carries the ruling):

> **Design-chat ruling 2026-07-23: closed, not a bug — premise corrected.** The spike findings above establish that the observed lines were Healing Draught consumable heals landing in the legitimate ~3s window between engagement and first blows, not passive regen. Regen has been silent and combat-excluded since v14; no missing check, no ordering race. Nothing to fix. The spike's genuine discovery — Acuity drift has no in-combat exclusion — is unfinished design rather than a defect and moves to **#N** (Version 24).

Substitute the real number for #N.

## Step 4 — Back-link comment on the new issue

Add this comment to #N:

> Split from #27, whose research-spike findings comment contains the full code-level analysis (tick phases, exclusion sites, v19-vs-current confirmation). #27 is closed as premise-corrected; this issue carries the surviving design question.

---

## Closeout

1. Commit a closeout report as `docs/shyland/Shyland_Brief_27_Ruling_Acuity_Filing_Closeout.txt` on `main`: milestone found-or-created, the new issue number, confirmation of the exact comment/close sequence, confirmation of zero label changes and zero dependency links, final commit hash.
2. Push.
3. **Run the issues report.**
