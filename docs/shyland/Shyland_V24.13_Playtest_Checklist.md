# Shyland V24.13 — Playtest Checklist (Brief 1: NPC HP Mk Scaling, #104)

Run against the **dev stack** after Brief 1's `make deploy-dev`. This is the human layer — CC's own verification (541/541 suite, live spot-check) has already passed.

**The honest framing:** this change has no visible Mk 2 surface yet — no Mk 2 content is authored until the V25 era. Every claim you can playtest is an *invariance* claim: **Mk 1 combat must feel exactly as it did on 24.12.** Anything that feels different is a finding. (If you judge this surface too thin to bother, "No playtests for this brief" is a reasonable disposition — your call, recorded per #170.)

**Before you start:** `help` should report `Version: 24.13-DEV`.

---

## Check 1 — Normal fight, unchanged

Target: a **cave beetle** — The Choke, in the Verdant Reach cave system (base 40 HP, unchanged).

- [ ] Fight and kill one. Fight length and feel identical to before — same number of rounds you'd expect, no spongier, no squishier.

## Check 2 — Health-description transitions, unchanged

Target: an **elder cave beetle** (elite, 110 HP — The Cold Ladder, The Black Span, The Thousand Steps, or The Long Crawl) or the **Silk Matron** (boss, 150 HP — The Matron's Larder), whichever you'd rather fight.

- [ ] Fight far enough to read the health ladder walk down through its bands: *perfect health* → *a few minor wounds* (below 90%) → *moderately wounded* (below 75%) → *badly wounded* (below 50%) → *near death* (below 25%).
- [ ] The transitions land where they always did — the bands read off current/max percentage, and Mk 1 max is untouched, so nothing here should move.

## Regression feel

- [ ] Nothing else about combat plays differently — healing draughts restore what they should, loot drops normally, respawns repopulate as usual.

---

When done, give the session your disposition per #170: **"Operator reports playtest successful"**, **"No playtests for this brief"**, or **"Operator deferring playtest"** — it goes verbatim into the closeout report and the closeout session reads it as a gate.
