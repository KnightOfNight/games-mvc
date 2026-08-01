# Shyland V24.1 Brief 1 — Post-Gear-Wiring Fight-Cost Survey (#180)

**Release:** Version 24.1 (milestone `Version 24.1`; branch `version_24_1`)
**Founding ticket:** #180 (operator-confirmed 2026-07-31, V24.1 design session)
**Type:** implementation-session **research brief** — committed dataset + report document, **zero game-behavior changes**
**Produced by:** V24.1 design session, 2026-07-31

---

## 0. Pre-flight

- **Prior pending deploy-time actions: none.** V24.0 Brief 1's PENDING DEPLOY-TIME ACTION (production `make seed`, draught EffectComponent conversion) was executed in the V24.0 closeout tail (2026-07-31; actuals matched: 0 deletions, 1 updated row, draught row verified percent-law). The block is closed. Nothing carries into this release.
- Confirm this brief exists verbatim at the `version_24_1` branch tip (Step 0 of the implementation-session ritual; whitespace-only drift is report-and-accept).
- Standard Step 0: create `docs/shyland/Shyland_V24.1_Brief_1_Closeout_Report.txt` as a stub (one-line session-start record: date, brief name, branch), commit, **push immediately** — the work-has-started signal.

## 1. Context and goal

#164's income numbers must derive from **measured** fight costs. The last feasibility dataset (#89, v21, report `docs/shyland/Shyland_V21_Kill_Feasibility_Survey.md`) predates two things that moved the numbers:

1. **The v22 gear wiring (#100):** effective stats include equipped gear; Option C armor mitigation (TAV = slot weight × Mk + rolled `physical_resist`, curve `TAV/(TAV+48)`, NPC→player only); per-landed-hit weapon procs (`bleed/stun/poison_factor`, lifesteal). #89's math assumed all item stats combat-inert — true then, false now.
2. **The V24.0 Draught Law (#139):** a Healing Draught now restores `ceil((0.15 + 0.05 × Mk) × vitality_max)`, minimum 25 HP (Mk 1 = 20% of max — five drinks zero-to-full at every level). #89's potion counts assumed the old flat 25 HP heal.

This survey measures fight costs under the current shipped-on-branch code and publishes the dataset the following consumers read:

1. **#164 income targets (primary — #164 is blocked by #180):** the provisional k = 2 income law's per-tier numbers derive from these measurements, ruled in a subsequent design session.
2. **Phase 3 baselines:** #104 (NPC HP scaling) and #130 (secondary-stat curve audit).
3. **The v21 boss potion budgets** (≤8/encounter, zone-final ≤12), re-derived in drinks-per-encounter under the Draught Law.

**The survey is the deliverable. It contains no rulings** — findings feed the next design session (the #89 precedent: "the survey *is* the deliverable; rulings on findings happen afterward"). Any defect discovered in game code along the way is **filed thin as an issue**, never fixed in this brief.

## 2. Opening act — version start (standing requirement, first brief of the release)

1. Bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` (line 8) from `"24.0"` to `"24.1-DEV"`, and move the pin test with it in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py` (line 118) asserts the new literal `'24.1-DEV'`. Own commit, nothing else in it.
2. Run the version-start `make deploy-dev` from the worktree.

After this commit, **no further changes under `django/src/` are permitted in this brief.** No migrations. No seed changes. No model changes.

## 3. The survey harness

- **Location:** `scripts/shyland_fight_cost_survey.py` (committed; the `scripts/shyland_issues_report.py` precedent — Shyland tooling outside the app tree).
- **It must drive the shipped combat code, not re-implement it.** The harness runs **inside the django container** (e.g. `docker cp` the script in, then execute with the container's Python against `manage.py shell`/Django setup — exact invocation is the implementation session's choice, recorded in the report) and calls the real functions: `combat_utils` (hit resolution, stats, damage), `item_utils` (instance generation/expected stats), `effect_utils` (the Draught Law helper `percent_heal_amount()`), and the tick-engine attack logic. Where tick-engine code is inseparable from live consumers/DB rows, the harness may replicate its *call sequence* (not its formulas) and must cite the replicated lines in the report's method section.
- **No persistent DB writes.** Any ORM objects the harness needs are constructed in memory or inside a transaction that is rolled back. The dev database is byte-identical before and after a run (verify: row counts on shyland tables unchanged).
- **Reproducible:** fixed RNG seed, recorded in the report and the dataset header. Monte Carlo with **N = 10,000 trials per (encounter × player level × loadout scenario)**.

## 4. Survey specification

### 4.1 Population

- **All attackable combat NPC definitions with authored stats** in the seeded world, reconciled against `seed_world.py` exactly as #89 §1.4 did (#89 counted 41: 24 Verdant Reach + 17 Viridian Ridge; 17 non-attackable and 4 placeholder-stat roster NPCs excluded). Report the reconciliation at the current branch tip; any count drift from #89 is reported, not silently absorbed.
- **Encounters:** every NPC solo, **plus** every boss + gated-adds group, **plus** every multi-aggro co-spawn room (the signposted ×2/×3 rooms) — same encounter model as #89: all aggro members engage from round 1; the player kills in ascending-HP order.

### 4.2 Reference player

- **Blade archetype, even-split build** (#89 §1.2 verbatim): creation primaries STR/DEX 18, others 8; +5 points/level split evenly into STR/DEX, STR takes the odd point; END stays 8; `vitality_max` from the shipped formula with **effective** stats (gear included); Acuity in-band (1.0); durability 100%.
- **Levels sampled per encounter:** **at-level** (player level = NPC/encounter level — the blessed calibration point) plus the **L5 and L10 reference columns** (#89 comparability).

### 4.3 Loadout scenarios

- **Headline — "current-era standard gear":** Uncommon **Broadsword Mk 1** at expected instance stats (the #89 headline weapon, realistically attainable from boss #1 onward) **plus a full Mk 1 armor loadout** derived from seed data at execution time: for each armor slot, the best **realistically attainable** piece (vendor-stocked anywhere, or drop chance ≥ 0.10 in the Mk 1 band), **Common rarity, expected rolled stats** (distribution mean). The chosen per-slot loadout is recorded as a table in the report's method section. Exactly one weapon equipped (combat reads `equipped_weapons[0]` only — #177; do not model a second weapon).
- **Sensitivity A — bare:** same build, no armor, Uncommon Broadsword. This isolates what the gear wiring changed and is the direct comparison row against #89's numbers.
- **Sensitivity B — Common weapon:** headline armor, Common Broadsword (#89 carried the same sensitivity).
- All implemented per-landed-hit weapon effects (proc factors, lifesteal) are modeled exactly as the tick engine applies them — lifesteal reduces net HP loss and must be included, not idealized away.

### 4.4 Measured quantities (per encounter × level × scenario)

| Quantity | Definition |
|---|---|
| HP loss per fight | Net vitality lost, fight start to last NPC death, no mid-fight drinking: **mean, std, p10, p90**, as absolute HP **and** as fraction of `vitality_max` |
| Fight duration | Combat rounds (3 s each): mean, std |
| Death-unhealed probability | P(HP loss ≥ player pool) across trials |
| Implied draughts-per-fight (economy form) | mean HP loss ÷ Mk 1 draught heal (`ceil(0.20 × vitality_max)`, min 25) — **decimal, not ceiled** (amortized across fights; this × 15 cp is the fight's expected draught cost, the direct input to #164's k = 2 law) |
| Potions-to-win (feasibility form) | `ceil(max(0, HP loss − 0.75 × player pool) ÷ Mk 1 draught heal)` — #89's rule under the new law, for verdict comparability |
| Verdict | #89's scale verbatim (OK / HARD / CLIFF / INFEASIBLE, 20-draught stack bound) recomputed under current code + Draught Law |

### 4.5 Analyses in the report

1. **Per-tier aggregation** — the table #164 consumes: expected HP-loss fraction, expected draughts-per-fight, and expected draught cost in copper per fight, aggregated by tier (normal / elite / boss / multi-aggro rooms) at at-level play. **This table is the survey's headline output.**
2. **#89 flip list** — every encounter whose verdict changed vs the #89 table, each attributed (armor mitigation vs Draught Law vs both; the bare-scenario column is the attribution instrument). An empty list is itself a reported result.
3. **Boss budget re-derivation** — the three Verdant bosses and three delve bosses in drinks-per-encounter under the Draught Law, against the v21 bounds (≤8, zone-final ≤12).
4. **Harness validation** — before headline runs: the bare scenario at 3+ matchups #89 tabulated (e.g. buffalo at L5, brown-bear at L10, whistler-below at L6) must reproduce #89's expected-value TTK and hit% within Monte Carlo tolerance; the validation table appears in the method section. A mismatch beyond tolerance stops the survey until explained (code changed since v21 → document which change; harness bug → fix harness).

## 5. Deliverables (all committed to `version_24_1`, `docs/shyland/` unless noted)

1. `Shyland_V24.1_Fight_Cost_Survey.md` — the report: method (reproducible standalone, #89 §1 style, including harness invocation, RNG seed, loadout table, validation table), findings tables, the three analyses. **Data tables are authoritative over prose.**
2. `Shyland_V24.1_Fight_Cost_Survey_Dataset.csv` — machine-readable: one row per (encounter × player level × scenario) carrying every measured quantity; header comment records git commit, RNG seed, N.
3. `scripts/shyland_fight_cost_survey.py` — the harness.
4. Completed `Shyland_V24.1_Brief_1_Closeout_Report.txt` (in place, from the Step 0 stub), including final commit hash and the operator playtest disposition.

## 6. Verification (gate for closing #180)

1. `git diff` against the opening-act commit shows **zero changes under `django/src/`**.
2. Full in-container test suite passes: `python manage.py test apps/shyland/tests` (directory-path form via `docker exec`) — expected 402/402 (401 pre-existing + the moved pin test; report the actual count).
3. Dev DB row counts on all shyland tables identical before and after a full harness run.
4. Dataset row-count invariant: rows = encounters × 3 levels (at-level, L5, L10; deduplicated where at-level ∈ {5, 10}) × 3 scenarios — state the arithmetic in the closeout with actual counts.
5. Draught Law spot checks in harness output: heal at `vitality_max` 718 → 144; heal at `vitality_max` 100 → 25 (floor) — matching the #139 test values.
6. Harness validation table (§4.5.4) present and within tolerance.
7. Every #89 encounter appears in the findings; the reconciliation section accounts for every `NpcDefinition` at the tip.
8. #180 closed with a completion comment (gated on 1–7 passing), pointing at the report and dataset paths.

## 7. Standing requirements

- **Version constant:** bumped to `24.1-DEV` as the opening act (§2). The closeout session stamps `24.1`.
- **Dev deploy:** the version-start `make deploy-dev` (§2) is this brief's in-session dev deploy — no later `django/src/` change exists to redeploy. State this in the closeout.
- **Operator playtest checklist:** this brief has **no playtestable surface** (no game-behavior change; the dev stack after §2 differs from 24.0 only by the version string — the checklist is: `help` output shows `24.1-DEV`). Expected disposition: **"No playtests for this brief"** — the operator states the disposition in-conversation; the session records it verbatim-style in the closeout report (#170).
- **PENDING DEPLOY-TIME ACTIONS: none.** This brief creates no production-side data actions. The closeout report carries the block explicitly as "None."
- **Architecture doc:** **untouched by this brief** (design ruling, this session: a research brief records nothing architectural; the 24.1 stamp move is closeout bookkeeping, hash does not move). State this in the closeout.
- **GDD:** no GDD text ships with 24.1 (the survey changes no design). Implementation sessions never touch GDD source regardless.
- Commit and push at every step boundary; branch only; never merge to main.

## 8. Design rules binding this brief

- The survey changes nothing: no game code (beyond §2's version bump), no data, no deployments beyond `make deploy-dev`, no rulings.
- Findings that look like bugs are **filed thin** via the normal pipeline (`--assignee "@me"`), referenced in the report, and left unfixed.
- The #89 verdict scale, encounter model, reference build, and 20-draught feasibility bound are reused **unchanged** — comparability across surveys is the point. Anything the implementation session believes must deviate is a deviation recorded in the closeout, not a silent improvement.
