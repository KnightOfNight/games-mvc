# Shyland V24.1 Fight-Cost Survey

**Issue:** #180 (V24.1 founding ticket — post-gear-wiring fight-cost survey)
**Date:** 2026-07-31
**Sources of truth:** `combat_utils.py`, `run_tick_engine.py`, `item_utils.py`, `effect_utils.py`, `consumers.py`, `seed_world.py` (via the seeded dev database), `models.py` at commit `ead50f5` (`version_24_1`).
**Harness:** `scripts/shyland_fight_cost_survey.py` (committed alongside this report). **RNG seed 180, N = 10,000 Monte Carlo trials per (encounter × player level × loadout scenario).**
**Dataset:** `Shyland_V24.1_Fight_Cost_Survey_Dataset.csv` (555 rows; header comment carries commit, seed, N).

This survey changes nothing: no game code, no data, no rulings. Its findings feed the next design session — primarily the #164 income-law derivation (#164 is blocked by #180), the Phase 3 baselines (#104, #130), and the boss potion-budget re-derivation. **Data tables are authoritative over prose.**

---

## 1. Method

### 1.1 What moved the numbers since #89

The #89 survey (v21, `Shyland_V21_Kill_Feasibility_Survey.md`, commit `ef3ce6d`) predates **three** changes that move fight costs, not the two the brief anticipated:

1. **The v21 B3 retune (#101)** — *landed after #89, in the same release, in direct response to it.* The NPC tier dodge offsets went from 0/+3/+6 (normal/elite/boss) to **0/+2/+2** ("boss identity lives in HP, damage, and escorts, not the miss rate"), moving the blessed at-level hit targets from 55/40/25 to **55/45/45**; boss HP was re-authored downward (Whistler 260→240, Dronemother 320→260, Weaver 500→200, King 650→220, Devourer 850→280); and the delve boss escorts went from **3 elite adds to 2**. #89's printed table is pre-retune; this is the dominant mover of every boss verdict below and is documented per the validation gate's "code changed since v21 → document which change."
2. **The v22 gear wiring (#100)** — effective stats include equipped gear (rolled STR on the weapon now adds damage; rolled END on armor now adds `vitality_max`); Option C armor mitigation (TAV = slot weight × Mk + rolled `physical_resist`, fraction TAV/(TAV+48), NPC→player only); per-landed-hit procs (`bleed/stun/poison_factor`), gear `crit_chance`, and lifesteal. #89's math assumed all item stats combat-inert.
3. **The V24.0 Draught Law (#139)** — a Healing Draught restores `ceil((0.15 + 0.05 × Mk) × vitality_max)`, minimum 25 (Mk 1 = 20% of max). #89 assumed the old flat 25 HP heal.

Two further population drifts from #89, reported not absorbed (§1.5): the four attackable placeholder-stat NPCs are now non-attackable, and the delve escorts are ×2.

### 1.2 The harness

`scripts/shyland_fight_cost_survey.py` runs inside the django container against the seeded dev database:

```
docker cp scripts/shyland_fight_cost_survey.py game-mvc-django:/tmp/
docker exec -w /app game-mvc-django python /tmp/shyland_fight_cost_survey.py \
    --out /tmp/survey_out --commit <git-hash>
docker cp game-mvc-django:/tmp/survey_out ./survey_out
```

It **drives the shipped combat code**: `resolve_hit`, `calculate_damage`, `apply_armor_mitigation`, `effective_stats`, `total_armor_value`, `summed_gear_stat`, `roll_gear_bonus_damage`, `get_npc_stats`, `acuity_damage_modifier`, `roll_initiative`, `recalculate_bars`, `get_durability_penalty`, and `percent_heal_amount` are all the real imported functions. The tick engine's per-round logic is inseparable from live consumers/DB rows, so the harness replicates its **call sequence** (never its formulas); the replicated lines at the tip are cited in the harness docstring (`run_tick_engine.py` 331–342, 359–383, 410–421, 438–439, 444–502, 608–610, 614–643; `consumers.py` 624, 1231–1236, 2384, 2399 for first-attacker, two-handed-displacement, and focus-change semantics).

**No persistent DB writes:** every ORM object the simulator touches (Character, ItemInstance, NpcInstance) is constructed in memory and never saved; the database is only read. Shyland table row counts were captured before and after the official run and were **identical** (32 tables, no drift).

**Reproducibility:** single global `random.seed(180)`; the shipped functions draw from the same `random` module. Two consecutive full runs produced byte-identical aggregates.

Faithful optimizations, hoisted not reformulated: NPC contest stats are computed by one real `get_npc_stats()` call per member (deterministic per definition + Mk tier); the equipped-set derivations are precomputed per loadout variant (gear cannot change mid-fight; an Uncommon weapon has exactly four secondary-slot variants).

### 1.3 Reference player and loadouts

**Reference player** (#89 §1.2 verbatim): Blade, creation primaries STR/DEX 18, others 8; +5 points/level split evenly into STR/DEX, STR takes the odd point; END stays 8; Acuity in-band (modifier 1.0); durability 100%. `vitality_max` from the shipped formula (`recalculate_bars`) with **effective** stats — gear included, which is why the geared pools below dwarf #89's (L5 headline pool 404 vs #89's bare 189).

**Expected instance stats:** deterministic item values are set to the exact distribution mean of what `generate_item_instance` stores — `damage_midpoint` = raw midpoint × mean rarity spread (Uncommon 16.0875, matching #89's 16.09), and each rolled integer stat at its exact `E[round(uniform(mid·lo, mid·hi))]`. The Uncommon weapon's single secondary slot (pool: `dex`, `crit_chance`, `bleed_factor`, `lifesteal`) is **sampled uniformly per trial** — the Monte Carlo marginalization of "expected instance stats" over the slot choice. At Mk 1 the pool's expected rolled values are `dex` 1.33 and exactly 1 for the other three.

**Scenarios:**

| Scenario | Weapon | Armor |
|---|---|---|
| **headline** ("current-era standard gear") | Uncommon Broadsword Mk 1, expected stats (mid 16.0875 ± 5, +5 rolled STR, sampled secondary) | Full attainable Mk 1 Common loadout below |
| **bare** (sensitivity A — #89 comparison row) | same Uncommon Broadsword | none |
| **common-weapon** (sensitivity B) | Common Broadsword Mk 1 (mid 15.2625 ± 5, +4.90 rolled STR, no secondary — Common rolls zero secondaries) | headline armor |

Exactly one weapon is equipped throughout (combat reads `equipped_weapons[0]` only — #177; no second weapon modeled).

**Headline armor loadout** — per Option-C slot, the best realistically attainable Mk 1 piece (vendor-stocked anywhere, or effective per-kill drop chance ≥ 0.10 in the Mk 1 band; grouped loot entries use their weight share of the group), Common rarity, expected rolled stats. TAV per slot is identical across candidates (slot weight × Mk; Common rolls no secondary `physical_resist`), so "best" resolves on expected primary-stat value — END on every seeded piece, the stat that feeds `vitality_max`:

| Slot (weight) | Piece | E[rolled END] | Attainable via |
|---|---|---|---|
| CHEST (3) | leather-vest | 3.83 | Sona 60cp; windhome-gear 0.12; whistler/king-loot 0.125 |
| HEAD (2) | leather-cap | 2.49 | Ridda 40cp; windhome-gear 0.10; whistler/king-loot 0.125 |
| LEGS (2) | leather-leggings | 3.83 | Sona 55cp; windhome-gear 0.10; whistler/king-loot 0.125 |
| OFF_HAND (2) | — | — | **excluded: the Broadsword is two-handed and displaces both hands** (`consumers.py:1231-1236`) |
| SHOULDERS (1) | leather-shoulders | 2.49 | ridge-gear / ridge-hunter-gear 0.10; whistler/king-loot 0.125 |
| HANDS (1) | leather-gloves | 2.49 | Essa 35cp; reedmere-gear 0.10; whistler/king-loot 0.125 |
| WAIST (1) | leather-belt | 2.49 | reedmere-gear 0.10; whistler/king-loot 0.125 |
| FEET (1) | leather-boots | 2.49 | Essa 35cp; reedmere-gear 0.10; whistler/king-loot 0.125 |

Loadout totals: **TAV 11** (mitigation 11/59 ≈ 18.6% per hit), **+20 effective END** (≈ +200 `vitality_max`), **+5 effective STR** from the weapon. The full seven-piece set is purchasable/farmable well inside the Mk 1 band (≈ 225 cp of vendor pieces plus three common ≥10% drops).

### 1.4 Encounter model and measured quantities

**Encounter model (#89, reused unchanged):** all aggro members engage from round 1 (`first_attacker='npc'`; a passive solo target gives the player the first round); the player kills in **ascending-HP order** (adds first), retargeting instantly (a focus change is a free action); passive NPCs are fought one at a time. Boss fights are always boss + gated adds (spawn-gated on the living boss).

Per trial the harness simulates full rounds exactly as the engine executes them: round-1 order by `first_attacker`, later rounds by the initiative contest (player's effective DEX+PER+d10 vs the mean of per-NPC rolls, player first on ties); a mid-round kill removes the NPC before its queued action resolves.

**Measured quantities** (per encounter × level × scenario; each from the same 10,000 trials):

- **HP loss per fight** — net vitality lost, fight start to last NPC death, no mid-fight drinking; lifesteal heals are netted in. Mean, std, p10, p90, absolute and as fraction of `vitality_max`.
- **Fight duration** — combat rounds (3 s each): mean, std.
- **Death-unhealed probability** — P(running HP loss reaches ≥ the pool at any point in the fight). The running maximum is used because the player dies the moment cumulative unhealed loss reaches the pool, even if later lifesteal would pull the final net loss back under it.
- **Implied draughts-per-fight (economy form)** — mean HP loss ÷ Mk 1 draught heal (`percent_heal_amount(0.20, vitality_max)` = ceil(0.20 × vmax), min 25) — decimal, not ceiled. This × 15 cp is the fight's expected draught cost, the direct input to #164's k = 2 law.
- **Potions-to-win (feasibility form)** — `ceil(max(0, mean HP loss − 0.75 × pool) ÷ heal)` — #89's rule under the new law. A flat-25 variant (`potions_to_win_flat25`) is carried in the dataset as the Draught Law attribution instrument.
- **Verdict** — #89's scale verbatim (OK ≤ 5 / HARD 6–12 / CLIFF 13–20 or at-level-breach-but-comfortable-by-band-top / INFEASIBLE breaches the 20-draught stack even at L10 with the Uncommon band weapon), recomputed under current code + Draught Law. Two scale notes, both matching #89's own practice: at-level hit% drift from the blessed target is recorded (G5 style, §3.4) but never demotes a verdict (#89's mountain-lion carried −5% and stayed OK); and the blessed targets are the code's current 55/45/45 (#101) — the 55/40/25 targets #89 quoted no longer exist.

**Model limitations (documented, matching #89's own):** the no-drinking HP-loss counterfactual lets the trajectory run past zero to measure total cost; XP/level-up during a fight is not modeled; mid-fight **gated-add respawn** (respawn timers are 1–10 min at the tip) is outside the encounter model — no at-level fight's mean duration approaches the 20-round/1-minute floor (max at-level mean: 14.9 rounds), but the off-level L5 reference columns against delve bosses reach 100+ round grinds where real fights would see adds respawn, so those L5 cells **understate** true cost. Player attacks continue while "dying" would have triggered in reality — consistent with the counterfactual.

**Levels sampled:** at-level (player level = encounter level; for groups, the boss's/highest member's level) plus the L5 and L10 reference columns, deduplicated where at-level ∈ {5, 10}.

### 1.5 Coverage and reconciliation

`seed_world.py` (read via the seeded dev DB) holds **62 NpcDefinitions** at the tip:

- **41 attackable combat NPCs with authored stats** — the survey population, identical in membership to #89's 41 (24 Verdant Reach + 17 Viridian Ridge). All 41 appear in the findings.
- **21 non-attackable.** #89 counted 17 non-attackable + 4 attackable-with-placeholder-stats (Aldric, Info Prime, Seris, Veris); those four are now `attackable=False` — #89's G7 observation was adopted. Zero attackable placeholder-stat NPCs remain.
- **Escort drift:** every delve boss now takes **2 gated adds, not #89's 3** (Weaver +2 brood, King +2 skitterlings, Devourer +2 drones; part of the #101 retune). The Verdant bosses keep +2.

**Encounters: 65** — 41 solo, 6 boss + gated-adds groups, 18 distinct multi-aggro co-spawn room compositions (deduplicated across 40+ rooms; the dataset's `rooms` column lists every room per composition, including the signposted ×3 rooms Lion's Watch and Bear's Throne).

### 1.6 Harness validation (ran before the headline runs)

Bare scenario under #89's model assumptions (stat-less Uncommon broadsword at expected midpoint, no armor, no procs). Six matchups: three normal-tier — untouched by #101, so #89's printed numbers must reproduce **directly** — plus the brief's three named elite/boss matchups carrying the retune. `EV` is #89 §1.3's expected-value model evaluated under current code constants; `MC` is this harness.

| Matchup | #89 printed hit/TTK | #89 stats (DEX/STR/HP) | Current stats | EV hit/TTK | MC hit/TTK |
|---|---|---|---|---|---|
| black-bear @ L5 (normal) | 95% / 0.8 | 20/12/35 | 20/12/35 | 95.0% / 0.77 | 94.98% / 0.78 |
| giant-cave-beetle @ L5 (normal) | 55% / 2.7 | 28/24/75 | 28/24/75 | 55.0% / 2.66 | 55.11% / 2.69 |
| mountain-goat @ L10 (normal) | 100% / 1.1 | 30/25/70 | 30/25/70 | 100% / 1.14 | 100% / 1.15 |
| buffalo @ L5 (elite) | 40% / 4.2 | 31/26/90 | **30**/26/90 | 45.0% / 3.81 | 45.08% / 3.85 |
| brown-bear @ L10 (elite) | 75% / 2.7 | 36/33/130 | **35**/33/130 | 80.0% / 2.49 | 79.73% / 2.52 |
| whistler-below @ L6 (boss) | 25% / 16.7¹ | 36/28/260 | **32**/28/**240** | 45.0% / 9.50 | 44.80% / 9.66 |

¹ #89's at-level TTK derived from its own §4 figures (260 HP ÷ 15.6 expected damage/round); the §2 row's TTK column is L5/L10.

**Verdict: PASS.** MC vs EV agrees within tolerance everywhere (hit% within 0.25 pt; TTK within 2%, tolerance ±1 pt / ±5%; the consistent ≈ +1% TTK is the engine's per-hit int-truncation, which the EV model ignores by #89's own convention). The three normal-tier matchups reproduce #89 exactly (hit% to the point; TTK within its 1-decimal rounding). Every elite/boss mismatch is exactly the documented **#101 retune**: elite offset +3→+2 = +5 pts hit; boss offset +6→+2 = +20 pts on the Whistler, plus its 260→240 HP re-author. No unexplained residue; the survey proceeded.

---

## 2. Findings

All tables from the official run (commit `ead50f5`, seed 180, N = 10,000). **These tables are authoritative over prose.** Loss = net HP lost (mean ± std, and as % of pool); Heal = Mk 1 draught heal at that pool; Draughts = economy form (decimal); Cost = draughts × 15 cp; Pot = potions-to-win (headline / bare); P(death) = death-unhealed probability; Hit% = landed (hit or crit) fraction of player attacks.

### 2.1 Solo NPCs at-level (headline gear, with bare comparison)

| NPC | Tier | Lvl | Pool | Heal | Loss mean±std (frac) | p10/p90 | Rounds | P(death) | Draughts | Cost cp | Pot | Pot(bare) | Hit% | Verdict | #89 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| river-otter | normal | 1 | 354 | 71 | 0.8±1.8 (0.2%) | 0/3 | 1.4 | 0.000 | 0.01 | 0.2 | 0 | 0 | 56% | **OK** | OK |
| black-bear | normal | 2 | 368 | 74 | 5.2±8.4 (1.4%) | 0/18 | 1.7 | 0.000 | 0.07 | 1.0 | 0 | 0 | 56% | **OK** | OK |
| cave-spider | normal | 2 | 368 | 74 | 6.6±5.8 (1.8%) | 0/14 | 1.7 | 0.000 | 0.09 | 1.3 | 0 | 0 | 56% | **OK** | OK |
| matrons-brood | normal | 2 | 368 | 74 | 6.7±5.9 (1.8%) | 0/14 | 1.7 | 0.000 | 0.09 | 1.4 | 0 | 0 | 56% | **OK** | OK |
| reedmere-fisher | normal | 2 | 368 | 74 | 4.7±7.3 (1.3%) | 0/16 | 1.7 | 0.000 | 0.06 | 1.0 | 0 | 0 | 56% | **OK** | OK |
| reedmere-villager | normal | 2 | 368 | 74 | 3.9±6.1 (1.0%) | 0/13 | 1.7 | 0.000 | 0.05 | 0.8 | 0 | 0 | 56% | **OK** | OK |
| young-mountain-lion | normal | 2 | 368 | 74 | 4.8±7.4 (1.3%) | 0/16 | 1.7 | 0.000 | 0.06 | 1.0 | 0 | 0 | 56% | **OK** | OK |
| cave-beetle | normal | 3 | 379 | 76 | 12.3±10.4 (3.2%) | 0/25 | 1.8 | 0.000 | 0.16 | 2.4 | 0 | 0 | 56% | **OK** | OK |
| cave-centipede | normal | 3 | 379 | 76 | 11.0±9.4 (2.9%) | 0/23 | 1.7 | 0.000 | 0.14 | 2.2 | 0 | 0 | 57% | **OK** | OK |
| silk-matron | boss | 3 | 379 | 76 | 69.3±28.6 (18.3%) | 37/108 | 7.1 | 0.000 | 0.91 | 13.7 | 0 | 0 | 46% | **OK** | OK |
| wild-boar | elite | 3 | 379 | 76 | 30.9±19.4 (8.1%) | 11/57 | 3.3 | 0.000 | 0.41 | 6.1 | 0 | 0 | 46% | **OK** | OK |
| dronemothers-swarm | normal | 4 | 393 | 79 | 35.7±20.8 (9.1%) | 14/62 | 3.0 | 0.000 | 0.45 | 6.8 | 0 | 0 | 52% | **OK** | OK |
| giant-cave-spider | normal | 4 | 393 | 79 | 30.6±18.2 (7.8%) | 12/55 | 3.0 | 0.000 | 0.39 | 5.8 | 0 | 0 | 51% | **OK** | OK |
| plains-deer | normal | 4 | 393 | 79 | 15.6±16.6 (4.0%) | 0/38 | 2.2 | 0.000 | 0.20 | 3.0 | 0 | 0 | 51% | **OK** | OK |
| plains-rabbit | normal | 4 | 393 | 79 | 5.4±9.1 (1.4%) | 0/20 | 1.5 | 0.000 | 0.07 | 1.0 | 0 | 0 | 51% | **OK** | OK |
| prairie-dog | normal | 4 | 393 | 79 | 5.3±9.0 (1.3%) | 0/19 | 1.5 | 0.000 | 0.07 | 1.0 | 0 | 0 | 52% | **OK** | OK |
| whistlers-young | normal | 4 | 393 | 79 | 31.3±20.3 (8.0%) | 8/58 | 2.8 | 0.000 | 0.40 | 5.9 | 0 | 0 | 51% | **OK** | OK |
| windhome-villager | normal | 4 | 393 | 79 | 23.8±17.8 (6.1%) | 0/47 | 2.8 | 0.000 | 0.30 | 4.5 | 0 | 0 | 51% | **OK** | OK |
| buffalo | elite | 5 | 404 | 81 | 60.5±33.8 (15.0%) | 22/106 | 4.0 | 0.000 | 0.75 | 11.2 | 0 | 0 | 46% | **OK** | OK |
| giant-cave-beetle | normal | 5 | 404 | 81 | 37.6±22.9 (9.3%) | 11/67 | 3.2 | 0.000 | 0.46 | 7.0 | 0 | 0 | 56% | **OK** | OK |
| giant-cave-centipede | normal | 5 | 404 | 81 | 32.1±19.8 (7.9%) | 9/58 | 2.8 | 0.000 | 0.40 | 5.9 | 0 | 0 | 56% | **OK** | OK |
| windhome-hunter | normal | 5 | 404 | 81 | 27.5±17.3 (6.8%) | 7/49 | 2.8 | 0.000 | 0.34 | 5.1 | 0 | 0 | 56% | **OK** | OK |
| dronemother | boss | 6 | 418 | 84 | 176.4±61.0 (42.2%) | 104/258 | 10.1 | 0.001 | 2.10 | 31.5 | 0 | 2 | 46% | **OK** | CLIFF |
| mountain-goat | normal | 6 | 418 | 84 | 34.4±21.7 (8.2%) | 8/62 | 2.8 | 0.000 | 0.41 | 6.1 | 0 | 0 | 56% | **OK** | OK |
| mountain-squirrel | normal | 6 | 418 | 84 | 6.0±11.3 (1.4%) | 0/25 | 1.4 | 0.000 | 0.07 | 1.1 | 0 | 0 | 56% | **OK** | OK |
| weavers-brood | elite | 6 | 418 | 84 | 48.2±28.1 (11.5%) | 18/85 | 3.3 | 0.000 | 0.57 | 8.6 | 0 | 0 | 46% | **OK** | OK |
| whistler-below | boss | 6 | 418 | 84 | 155.3±56.2 (37.2%) | 89/229 | 9.5 | 0.001 | 1.85 | 27.7 | 0 | 1 | 46% | **OK** | CLIFF |
| brown-bear | elite | 7 | 429 | 86 | 101.8±48.7 (23.7%) | 49/165 | 5.2 | 0.000 | 1.18 | 17.7 | 0 | 0 | 46% | **OK** | OK |
| elder-cave-spider | elite | 7 | 429 | 86 | 69.7±38.8 (16.2%) | 26/121 | 4.0 | 0.000 | 0.81 | 12.2 | 0 | 0 | 46% | **OK** | OK |
| mountain-villager | normal | 7 | 429 | 86 | 44.8±26.2 (10.4%) | 17/79 | 3.3 | 0.000 | 0.52 | 7.8 | 0 | 0 | 56% | **OK** | OK |
| elder-cave-centipede | elite | 8 | 443 | 89 | 96.7±54.0 (21.8%) | 39/167 | 4.4 | 0.000 | 1.09 | 16.3 | 0 | 0 | 41% | **OK** | HARD |
| kings-skitterlings | elite | 8 | 443 | 89 | 54.3±33.9 (12.3%) | 19/98 | 3.3 | 0.000 | 0.61 | 9.1 | 0 | 0 | 42% | **OK** | OK |
| mountain-hunter | normal | 8 | 443 | 89 | 64.0±35.9 (14.4%) | 24/111 | 3.8 | 0.000 | 0.72 | 10.8 | 0 | 0 | 51% | **OK** | OK |
| mountain-lion | elite | 8 | 443 | 89 | 113.6±54.9 (25.6%) | 53/187 | 5.5 | 0.000 | 1.28 | 19.1 | 0 | 0 | 41% | **OK** | OK |
| undercrag-weaver | boss | 8 | 443 | 89 | 163.1±65.4 (36.8%) | 88/249 | 8.1 | 0.001 | 1.83 | 27.5 | 0 | 1 | 41% | **OK** | INFEASIBLE |
| chittering-king | boss | 9 | 454 | 91 | 134.7±53.1 (29.7%) | 73/205 | 7.7 | 0.000 | 1.48 | 22.2 | 0 | 0 | 46% | **OK** | INFEASIBLE |
| devourers-drones | elite | 9 | 454 | 91 | 54.0±31.2 (11.9%) | 20/94 | 3.3 | 0.000 | 0.59 | 8.9 | 0 | 0 | 46% | **OK** | OK |
| elder-cave-beetle | elite | 9 | 454 | 91 | 89.8±50.0 (19.8%) | 33/156 | 4.0 | 0.000 | 0.99 | 14.8 | 0 | 0 | 46% | **OK** | HARD |
| prowling-mountain-lion | elite | 9 | 454 | 91 | 85.8±48.1 (18.9%) | 31/150 | 4.0 | 0.000 | 0.94 | 14.1 | 0 | 0 | 46% | **OK** | CLIFF |
| territorial-brown-bear | elite | 9 | 454 | 91 | 114.1±57.4 (25.1%) | 49/191 | 4.7 | 0.000 | 1.25 | 18.8 | 0 | 0 | 46% | **OK** | CLIFF |
| crowned-devourer | boss | 10 | 468 | 94 | 183.0±66.1 (39.1%) | 106/270 | 9.2 | 0.001 | 1.95 | 29.2 | 0 | 1 | 46% | **OK** | INFEASIBLE |

**Verdict counts (solo, headline): 41 OK / 0 HARD / 0 CLIFF / 0 INFEASIBLE** (vs #89's 32/2/4/3).

### 2.2 Group encounters at-level (as fought)

| Encounter | Room(s) | Lvl | Pool | Loss mean (frac) | Rounds | P(death) | Draughts | Cost cp | Pot | Pot(bare) | P(death, bare) | Verdict | Verdict(bare) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Silk Matron + 2 brood | The Matron's Larder | 3 | 379 | 107.9 (28.5%) | 9.8 | 0.000 | 1.42 | 21.3 | 0 | 0 | 0.138 | **OK** | OK |
| Whistler Below + 2 young | The Whistler's Hollow | 6 | 418 | 235.2 (56.3%) | 12.4 | 0.011 | 2.80 | 42.0 | 0 | 3 | 0.813 | **OK** | OK |
| Dronemother + 2 swarm | The Dronemother's Vault | 6 | 418 | 297.4 (71.1%) | 14.3 | 0.063 | 3.54 | 53.1 | 0 | 5 | 0.963 | **OK** | OK |
| Undercrag Weaver + 2 brood | The Weaver's Vault | 8 | 443 | 319.5 (72.1%) | 12.7 | 0.080 | 3.59 | 53.8 | 0 | 5 | 0.949 | **OK** | OK |
| Chittering King + 2 skitterlings | The Chittering Throne | 9 | 454 | 309.9 (68.3%) | 12.4 | 0.075 | 3.41 | 51.1 | 0 | 4 | 0.878 | **OK** | OK |
| Crowned Devourer + 2 drones | The Devourer's Hoard | 10 | 468 | 415.7 (88.8%) | 14.9 | 0.286 | 4.42 | 66.3 | 1 | 6 | 0.987 | **OK** | HARD |
| 2× cave-spider | The Entry Cleft | 2 | 368 | 19.6 (5.3%) | 3.4 | 0.000 | 0.27 | 4.0 | 0 | 0 | 0.000 | **OK** | OK |
| cave-centipede + cave-spider | The Silk Gallery | 3 | 379 | 23.7 (6.3%) | 3.1 | 0.000 | 0.31 | 4.7 | 0 | 0 | 0.000 | **OK** | OK |
| cave-beetle + cave-centipede | The Choke | 3 | 379 | 35.5 (9.4%) | 3.5 | 0.000 | 0.47 | 7.0 | 0 | 0 | 0.001 | **OK** | OK |
| 2× giant-cave-spider | The Bone Niche, The Husk Pile | 4 | 393 | 92.4 (23.5%) | 6.1 | 0.000 | 1.17 | 17.6 | 0 | 0 | 0.062 | **OK** | OK |
| 2× giant-cave-beetle | The Drop, The Droneway, The Low Chamber | 5 | 404 | 112.0 (27.7%) | 6.3 | 0.000 | 1.38 | 20.7 | 0 | 0 | 0.124 | **OK** | OK |
| giant-cave-beetle + giant-cave-centipede | The Deep Hum, The Larder Shaft | 5 | 404 | 102.9 (25.5%) | 6.0 | 0.000 | 1.27 | 19.1 | 0 | 0 | 0.076 | **OK** | OK |
| giant-cave-beetle + giant-cave-spider | The Buzzing Dark | 5 | 404 | 84.9 (21.0%) | 5.6 | 0.000 | 1.05 | 15.7 | 0 | 0 | 0.022 | **OK** | OK |
| 2× giant-cave-centipede | The Whistle Throat, The Honeycomb Walls | 5 | 404 | 95.8 (23.7%) | 5.6 | 0.000 | 1.18 | 17.7 | 0 | 0 | 0.051 | **OK** | OK |
| 2× elder-cave-spider | The First Descent, The Web Chimney, The Silk Well, The Chitter Hall, The Veined Gallery | 7 | 429 | 209.4 (48.8%) | 7.9 | 0.017 | 2.43 | 36.5 | 0 | 2 | 0.561 | **OK** | OK |
| 2× elder-cave-centipede | The Under Gallery, The Falling Gallery, The Molt Chamber, The Egg Vault, The Rising Dark, The Upper Dark | 8 | 443 | 289.9 (65.4%) | 8.7 | 0.100 | 3.26 | 48.9 | 0 | 4 | 0.796 | **OK** | OK |
| elder-cave-centipede + elder-cave-spider | The Deep Landing, The Fallen Shaft | 8 | 443 | 219.6 (49.6%) | 7.7 | 0.013 | 2.47 | 37.0 | 0 | 2 | 0.566 | **OK** | OK |
| 2× elder-cave-beetle | The Cold Ladder, The Thousand Steps, The Hollow Stair, The Glittering Seam, The Wingway, The Deep Turn, The Devourer's Approach | 9 | 454 | 266.6 (58.7%) | 8.0 | 0.053 | 2.93 | 43.9 | 0 | 3 | 0.700 | **OK** | OK |
| elder-cave-beetle + elder-cave-centipede | The Black Span, The King's Approach, The Last Dark | 9 | 454 | 220.2 (48.5%) | 7.3 | 0.013 | 2.42 | 36.3 | 0 | 2 | 0.522 | **OK** | OK |
| elder-cave-beetle + elder-cave-spider | The Long Crawl | 9 | 454 | 177.7 (39.2%) | 6.6 | 0.001 | 1.95 | 29.3 | 0 | 1 | 0.293 | **OK** | OK |
| 2× prowling-mountain-lion | The Lion's Backyard | 9 | 454 | 259.9 (57.2%) | 8.0 | 0.047 | 2.86 | 42.8 | 0 | 3 | 0.673 | **OK** | OK |
| **3× prowling-mountain-lion** | Lion's Watch | 9 | 454 | 521.0 (114.8%) | 12.0 | **0.623** | 5.73 | 85.9 | 2 | 9 | 0.996 | **OK** | HARD |
| 2× territorial-brown-bear | Bear's Hollow | 9 | 454 | 343.9 (75.7%) | 9.5 | 0.175 | 3.78 | 56.7 | 1 | 5 | 0.888 | **OK** | OK |
| **3× territorial-brown-bear** | Bear's Throne | 9 | 454 | 687.4 (151.4%) | 14.2 | **0.902** | 7.55 | 113.3 | 4 | 13 | 1.000 | **OK** | CLIFF |

### 2.3 L5/L10 reference columns (headline; solo NPCs)

For #89 comparability. `inf` marks configurations with no damage path (d20 saturation). At L5 against the Crowned Devourer the damage path exists only in the ~25% of trials whose weapon secondary is DEX (unwinnable fraction 0.75); its L5 row aggregates resolved trials only and is a 100+ round grind — see the respawn caveat in §1.4.

| NPC | Loss L5 | Draughts L5 | Pot L5 | Hit% L5 | Loss L10 | Draughts L10 | Pot L10 | Hit% L10 |
|---|---|---|---|---|---|---|---|---|
| river-otter | 0.0 | 0.00 | 0 | 100% | 0.0 | 0.00 | 0 | 100% |
| black-bear | 0.1 | 0.00 | 0 | 96% | 0.0 | 0.00 | 0 | 100% |
| cave-spider | 1.4 | 0.02 | 0 | 96% | 0.0 | 0.00 | 0 | 100% |
| matrons-brood | 1.4 | 0.02 | 0 | 96% | 0.0 | 0.00 | 0 | 100% |
| reedmere-fisher | 0.1 | 0.00 | 0 | 96% | 0.0 | 0.00 | 0 | 100% |
| reedmere-villager | 0.1 | 0.00 | 0 | 96% | 0.0 | 0.00 | 0 | 100% |
| young-mountain-lion | 0.1 | 0.00 | 0 | 96% | 0.0 | 0.00 | 0 | 100% |
| cave-beetle | 4.6 | 0.06 | 0 | 82% | 0.0 | 0.00 | 0 | 100% |
| cave-centipede | 4.3 | 0.05 | 0 | 81% | 0.0 | 0.00 | 0 | 100% |
| silk-matron | 26.9 | 0.33 | 0 | 71% | 0.0 | 0.00 | 0 | 100% |
| wild-boar | 10.5 | 0.13 | 0 | 71% | 0.0 | 0.00 | 0 | 100% |
| dronemothers-swarm | 21.4 | 0.26 | 0 | 66% | 0.0 | 0.00 | 0 | 100% |
| giant-cave-spider | 18.7 | 0.23 | 0 | 66% | 0.0 | 0.00 | 0 | 100% |
| plains-deer | 6.2 | 0.08 | 0 | 66% | 0.0 | 0.00 | 0 | 100% |
| plains-rabbit | 2.2 | 0.03 | 0 | 66% | 0.0 | 0.00 | 0 | 100% |
| prairie-dog | 2.1 | 0.03 | 0 | 65% | 0.0 | 0.00 | 0 | 100% |
| whistlers-young | 17.2 | 0.21 | 0 | 67% | 0.0 | 0.00 | 0 | 100% |
| windhome-villager | 11.6 | 0.14 | 0 | 66% | 0.0 | 0.00 | 0 | 100% |
| buffalo | 60.5 | 0.75 | 0 | 46% | 2.9 | 0.03 | 0 | 100% |
| giant-cave-beetle | 37.6 | 0.46 | 0 | 56% | 1.0 | 0.01 | 0 | 100% |
| giant-cave-centipede | 32.1 | 0.40 | 0 | 56% | 0.9 | 0.01 | 0 | 100% |
| windhome-hunter | 27.5 | 0.34 | 0 | 56% | 0.8 | 0.01 | 0 | 100% |
| dronemother | 261.2 | 3.22 | 0 | 36% | 22.7 | 0.24 | 0 | 96% |
| mountain-goat | 49.7 | 0.61 | 0 | 47% | 3.2 | 0.03 | 0 | 100% |
| mountain-squirrel | 9.9 | 0.12 | 0 | 46% | 0.0 | 0.00 | 0 | 100% |
| weavers-brood | 66.4 | 0.82 | 0 | 37% | 7.1 | 0.08 | 0 | 96% |
| whistler-below | 227.8 | 2.81 | 0 | 36% | 19.2 | 0.20 | 0 | 96% |
| brown-bear | 286.0 | 3.53 | 0 | 21% | 28.7 | 0.31 | 0 | 81% |
| elder-cave-spider | 192.5 | 2.38 | 0 | 21% | 19.7 | 0.21 | 0 | 81% |
| mountain-villager | 115.2 | 1.42 | 0 | 31% | 11.3 | 0.12 | 0 | 91% |
| elder-cave-centipede | 560.0 | 6.91 | 4 | 6% | 41.3 | 0.44 | 0 | 66% |
| kings-skitterlings | 265.6 | 3.28 | 0 | 6% | 18.6 | 0.20 | 0 | 66% |
| mountain-hunter | 285.0 | 3.52 | 0 | 16% | 26.1 | 0.28 | 0 | 76% |
| mountain-lion | 588.7 | 7.27 | 4 | 6% | 41.3 | 0.44 | 0 | 66% |
| undercrag-weaver | 918.6 | 11.34 | 8 | 6% | 65.5 | 0.70 | 0 | 66% |
| chittering-king | 2325.6 | 28.71 | 25 | 0% | 93.9 | 1.00 | 0 | 56% |
| devourers-drones | 696.3 | 8.60 | 5 | 0% | 38.9 | 0.41 | 0 | 56% |
| elder-cave-beetle | 1508.6 | 18.63 | 15 | 0% | 63.7 | 0.68 | 0 | 56% |
| prowling-mountain-lion | 1474.3 | 18.20 | 15 | 0% | 62.1 | 0.66 | 0 | 56% |
| territorial-brown-bear | 1778.3 | 21.95 | 19 | 0% | 71.8 | 0.76 | 0 | 56% |
| crowned-devourer | 7154.0 | 88.32 | 85 | 0% | 183.0 | 1.95 | 0 | 46% |

---

## 3. Analyses

### 3.1 Per-tier aggregation — the table #164 consumes (HEADLINE OUTPUT)

At-level play, headline ("current-era standard gear") scenario, unweighted mean over the encounters in each set. Boss figures are given both solo (the 6 boss rows of §2.1) and as fought (boss + gated adds, §2.2); **the as-fought row is the real per-fight cost** — a boss is never fought without its adds.

| Tier | Encounters | E[HP-loss fraction] | E[draughts per fight] | E[draught cost, cp per fight] |
|---|---|---|---|---|
| Normal (solo) | 23 | 4.8% | 0.241 | **3.61** |
| Elite (solo) | 12 | 17.5% | 0.872 | **13.09** |
| Boss (solo reference) | 6 | 33.9% | 1.687 | 25.30 |
| **Boss encounter (as fought)** | 6 | 64.2% | 3.196 | **47.94** |
| Multi-aggro room | 18 | 47.3% | 2.360 | **35.39** |

Context for the #164 derivation: current at-band copper drops are animals/insects 0 cp (1–2 cp sellable parts), villagers 2–24 cp, Verdant bosses 50–150 cp, delve bosses 150–1000 cp (unchanged since #89 §1.2). Under the k = 2 provisional law these expected draught costs are the "fight cost" leg; note they scale with `vitality_max` (the Draught Law heal is 20% of pool, so cost-per-fight is stable across levels within a tier — the fractions column is the level-invariant form).

### 3.2 #89 flip list — every changed verdict, attributed

Attribution instrument: the chain **#89 → bare/flat-25 → bare → headline** isolates the three movers in order. Bare/flat-25 (current code, no armor, old 25-HP heal) isolates the **#101 retune + weapon-stat wiring**; bare adds the **Draught Law**; headline adds **armor + END gear**. Nine solo verdicts flipped — all improvements, no regressions; the other 32 solo verdicts are unchanged (OK → OK).

| NPC (solo, at-level) | #89 | flat-25 pot | bare pot | headline pot | Now | Dominant mover |
|---|---|---|---|---|---|---|
| whistler-below | CLIFF (13) | 2 | 1 | 0 | **OK** | #101 retune (hit 25→45%, HP −20) |
| dronemother | CLIFF (18) | 3 | 2 | 0 | **OK** | #101 retune (HP 320→260) |
| undercrag-weaver | INFEASIBLE (37) | 1 | 1 | 0 | **OK** | #101 retune (HP 500→200, DEX 44→40) |
| chittering-king | INFEASIBLE (54) | 0 | 0 | 0 | **OK** | #101 retune (HP 650→220, DEX 46→42) |
| crowned-devourer | INFEASIBLE (79) | 2 | 1 | 0 | **OK** | #101 retune (HP 850→280, DEX 46→42) |
| prowling-mountain-lion | CLIFF (214¹) | 0 | 0 | 0 | **OK** | #101 retune (elite offset; solo was never the problem) |
| territorial-brown-bear | CLIFF (271¹) | 0 | 0 | 0 | **OK** | #101 retune |
| elder-cave-centipede | HARD (54¹) | 0 | 0 | 0 | **OK** | #101 retune |
| elder-cave-beetle | HARD (220¹) | 0 | 0 | 0 | **OK** | #101 retune |

¹ #89's Potions column for these rows is the L5 reference, not at-level; their at-level costs were 0–1 and the #89 verdicts keyed off the ×2/×3 room encounters.

Group-encounter flips against #89's encounter table (same chain):

| Encounter | #89 potions | flat-25 | bare | headline | Now (headline/bare) |
|---|---|---|---|---|---|
| Whistler + young | 17 (L6) | 6 | 3 | 0 | OK / OK |
| Dronemother + swarm | 23 (L6) | 9 | 5 | 0 | OK / OK |
| Weaver + brood | 50 (L9, ×3 adds) | 9 | 5 | 0 | OK / OK |
| King + skitterlings | 80 (L10, ×3 adds) | 8 | 4 | 0 | OK / OK |
| Devourer + drones | 122 (L10, ×3 adds) | 13 | 6 | 1 | OK / HARD |
| 3× prowling lion (Lion's Watch) | 34 (L9) | 19 | 9 | 2 | OK / HARD |
| 3× territorial bear (Bear's Throne) | 45 (L9) | 27 | 13 | 4 | OK / CLIFF |

Reading: **the #101 retune did the heavy lifting** (it was designed to — it answered #89's G1/G3), collapsing three orders of INFEASIBLE into single digits. The **Draught Law roughly halves** remaining potion counts (heals scale to ~20% of a real pool instead of flat 25). The **gear wiring finishes the job**: +200 pool from END armor, 18.6% mitigation, +5 STR — turning the last HARD/CLIFF rooms into OK. Only the deliberately signposted ×3 rooms and the zone-final Devourer encounter retain teeth without gear. #89's G1 ("feasibility decays linearly in boss HP") and G4 (×3 rooms breach the stack) are **resolved** in the current code; its G2 escort-compounding shape survives in miniature (adds still roughly double boss fight cost — compare §2.1 boss rows to §2.2).

### 3.3 Boss potion budgets under the Draught Law

The v21 bounds: ≤ 8 drinks per boss encounter, ≤ 12 for the zone-final. At-level, headline gear, as fought (boss + adds). Economy form = mean loss ÷ heal (decimal, amortized); feasibility form = #89's spend-down rule; flat-25 = the same fight under the retired flat heal, for scale.

| Boss encounter | Lvl | Drinks (economy) | Potions-to-win | Potions (flat-25) | P(death unhealed) | Bound | Margin |
|---|---|---|---|---|---|---|---|
| Silk Matron + 2 brood | 3 | 1.42 | 0 | 0 | 0.000 | ≤ 8 | comfortable |
| Whistler Below + 2 young | 6 | 2.80 | 0 | 0 | 0.011 | ≤ 8 | comfortable |
| Dronemother + 2 swarm | 6 | 3.54 | 0 | 0 | 0.063 | ≤ 8 | comfortable |
| Undercrag Weaver + 2 brood | 8 | 3.59 | 0 | 0 | 0.080 | ≤ 8 | comfortable |
| Chittering King + 2 skitterlings | 9 | 3.41 | 0 | 0 | 0.075 | ≤ 8 | comfortable |
| Crowned Devourer + 2 drones | 10 | 4.42 | 1 | 3 | 0.286 | ≤ 12 | comfortable |

**Every boss sits inside its v21 bound with large margin** — the whole ladder runs 1.4–4.4 expected drinks per encounter (21–66 cp at 15 cp/draught). The ladder's difficulty progression is intact and monotone in drinks; it is simply priced in draughts a Mk 1 player can actually carry.

### 3.4 Observations (no verdicts changed by these; no rulings made)

- **"OK" now means "affordable," not "safe."** Death-unhealed probability tells the real story the potion counts hide: at-level with full standard gear and **no drinking**, Bear's Throne kills you 90% of the time (mean loss 151% of pool), Lion's Watch 62%, the Devourer encounter 29%. These fights are won by drinking mid-fight (4–8 draughts, 60–113 cp), exactly as the potion economy intends. Bare, the same rooms are 99–100% lethal — gear is now load-bearing for the top of the Mk 1 band, which is the #100 design intent realized. Whether ~62–90% no-drink lethality on the signposted forbidden grounds is the intended sharpness is a design question for the #164/#104 sessions, not a defect.
- **G5's even-level rounding drift persists, in the retuned geometry**: at L4/L8 the at-level hit% runs ≈ 4–5 points under the blessed target (e.g. plains-rabbit 50.6%, mountain-lion 41.2%, undercrag-weaver 41.2% vs 45), exactly the parity artifact #89 recorded; odd levels are exact (±0.5 MC noise). The headline gear's occasional +1 DEX secondary nudges normal-tier hit% ≈ +1 point above blessed (56%).
- **The Draught Law's floor is invisible at reference builds**: every surveyed pool (354–468 headline, 218–268 bare) yields percent heals of 44–94 HP, far above the 25 floor. The floor only binds below 125 `vitality_max` — sub-L1 territory for this build.
- **Gear dominance ordering** (from the scenario deltas): END-driven pool growth > armor mitigation > weapon rolled STR > procs/lifesteal (the last are real but small at Mk 1 — expected proc values of 1 and 5% trigger rates).
- **Common vs Uncommon weapon** (sensitivity B): ≈ +5–9% loss and +0.5–1 rounds across the board; flips nothing. Consistent with #89's finding that weapon rarity moves TTK, not verdicts.
- **No new code defects were found.** Nothing observed in harness construction or output contradicted the shipped code's documented behavior; no issues were filed. Known-tracked matters touched by this survey: NPC HP ignores level/Mk (#89 G6 — the #104 Phase 3 baseline), and the L5-vs-delve-boss reference cells understate cost by excluding mid-fight add respawn (§1.4 limitation).

---

*Survey computed by `scripts/shyland_fight_cost_survey.py` at commit `ead50f5` (RNG seed 180, N = 10,000); dataset in `Shyland_V24.1_Fight_Cost_Survey_Dataset.csv`. The survey is the deliverable; rulings on these findings belong to the next design session (#164, #104, #130).*
