# Shyland V21 Kill-Feasibility Survey

**Issue:** #89 (research spike — kill-feasibility audit of all seeded NPC tiers)
**Date:** 2026-07-16
**Sources of truth:** `combat_utils.py`, `run_tick_engine.py`, `item_utils.py`, `effect_utils.py`, `seed_world.py`, `views.py`, `models.py` at commit `ef3ce6d` (main). Cross-checked against `Shyland_Architecture_v21.md` §4.5 and GDD v20 §3.4; no code-vs-doc formula disagreements were found (two minor doc-drift items are recorded in §3, group G7).

This survey changes nothing: no game code, no data, no deployments. Its findings become issues later via the triage pipeline, after design-chat rulings.

---

## 1. Method

Everything below is derived from the code as it stands. The method section is written to be reproducible from this report alone, and doubles as design input for the Firehose Logging milestone (#33/#37): every quantity computed here by hand is a quantity Firehose should eventually measure live.

### 1.1 Combat formulas as implemented

**To-hit** (`combat_utils.resolve_hit`): contested d20. `total = d20 + attacker_DEX` vs. static `defense = 10 + defender_DEX`. `total ≥ defense` is a success; short by 1–3 is a **graze** (0.5× damage); shorter is a miss. Crit is a separate independent roll on any success: `clamp(0.05 + 0.01 × (attacker_DEX − defender_DEX), 0.05, 0.25)`, 1.5× damage. Writing `Δ = attacker_DEX − defender_DEX`: P(success) = clamp((11 + Δ)/20, 0, 1); the graze window is a flat 3/20 whenever it fits inside the die range. **The d20 can bridge at most 20 points of DEX difference — beyond that, outcomes saturate at always-hit or never-hit.** This saturation is the mechanism behind every cliff found below.

**NPC stats** (`combat_utils.get_npc_stats`, v19 Brief 7 model): `npc_level L = scaling_factor + 10 × (mk_tier − 1)`. Every spawn in `seed_world.py` is `mk_tier=1`, so today L = `scaling_factor` (1–10; the whole seeded world is one Mk 1 band). Then:
- `DEX = round(18 + 2.5 × (L − 1)) + tier_offset`, tier offset 0/3/6 for normal/elite/boss. Python banker's rounding, matching the code (`round(30.5) = 30`, `round(35.5) = 36`).
- `STR = base_str + round(2.5 × (L − 1))` (same for PER/INT; `base_dex` is dead — never read by combat).
- **HP = `base_vitality`, flat** (`run_tick_engine.create_live_instance`). NPC HP does not scale with level or Mk tier (see finding G6).

**Player attack** (`run_tick_engine.execute_actions`): one attack per combat round (round = 3 ticks). On success/graze, damage = `(weapon_roll + STR) × acuity_mod × durability_mod × hit_mult`, where `weapon_roll ~ uniform(midpoint − spread, midpoint + spread)` (expectation = midpoint), truncated to int, min 1. Melee stat bonus is STR (DEX for ranged).

**NPC attack**: damage = `uniform(0.8 × STR, 1.2 × STR) × hit_mult` (expectation = STR per landed hit). **There is no mitigation input of any kind**: armor items, shields, and every rolled item stat are display-only — nothing in `run_tick_engine.py` or `consumers.py` applies `rolled_primary_stats`/`rolled_secondary_stats` to a character's combat stats, and `calculate_damage` for NPC attacks passes `stat_bonus=0, acuity=1, durability=1` with no defender term. Player defense is raw `stat_dex`, full stop.

**Weapon damage** (`item_utils.generate_item_instance`): instance midpoint = `(scaling_base + scaling_factor × mk_tier) × uniform(rarity_lo, rarity_hi)`; Common spread (0.85, 1.00) → expected multiplier 0.925, Uncommon (0.90, 1.05) → 0.975.

**Healing** (`seed_world._seed_effects` + `effect_utils`): Healing Draught restores `20 + 5 × mk_tier` = **25 Vitality at Mk 1**, price **15 copper** (Essa, Sona, Ridda, both Convergence carts). `cmd_use` has **no cooldown and works mid-combat** (it even revives the dying), so healing is supply-limited, not rate-limited — the potion stack is the binding feasibility resource, exactly as #89 ruled.

**No seeded NPC applies effects**: `NpcEffect` is never seeded (the Fracture Wraith poison definition exists but is wired to no NPC), so NPC DPS is pure swing math.

**Aggro**: on room entry every living aggressive NPC in the room engages at once (`get_aggro_npcs_in_room`), so co-spawned counts define the real encounter. Passive NPCs are fought one at a time (attacking one does not draw its neighbors).

### 1.2 Reference players

Canonical attacker = **Blade archetype (STR/DEX primaries)**, the operator's playtest build class. Creation stats: primaries 18, everything else 8 (`views.py`). +5 stat points per level (`STAT_POINTS_PER_LEVEL`), all spent into STR/DEX, split evenly (STR takes the odd point). Vitality = `END×10 + STR×3 + level×5` (`recalculate_bars`); END stays 8. Acuity assumed in-band (neutral 1.0 modifier).

| Level | STR | DEX | HP |
|---|---|---|---|
| 3 | 23 | 23 | 164 |
| 5 (band mid) | 28 | 28 | 189 |
| 6 | 31 | 30 | 203 |
| 8 | 36 | 35 | 228 |
| 9 | 38 | 38 | 239 |
| 10 (band top) | 41 | 40 | 253 |

**Split sensitivity:** every DEX point not bought is −5% hit chance and +5% enemy hit chance inside the d20 window. A build that banks points or spreads them off-primary falls off the boss contest entirely (see §4 — this is the actual #66 mechanism). The blessed 55/40/25% targets implicitly assume DEX keeps pace with the NPC curve (`18 + 2.5/level`); the canonical even split tracks it to within 1 point.

**Weapon:** Broadsword Mk 1 (best seeded band weapon; every Verdant/Ridge boss weapon group can drop it, and the Silk Matron guarantees an Uncommon weapon — so an Uncommon broadsword is realistically attainable from boss #1 onward). Expected instance midpoint: **Common 15.26, Uncommon 16.09**, ±5 spread. Headline columns use Uncommon; Common changes nothing materially (≤ 1 extra potion anywhere). The best *purchasable* weapon is the Iron Sword (75c, Ridda; expected mid ~10.2) — roughly −6 damage per landed swing, which stretches TTKs ~15–20% but flips no verdict.

**Consumables:** Healing Draughts at 25 HP / 15c. Carried stack assumption: **20 draughts (300c)** — the operator's observed practice is a large stack; 20 is the ruled "reasonable supply" for the feasibility bound. Copper context at band: animals/insects drop 0c (carapace/hide sell for 1–2c), villagers 2–24c, Verdant bosses 50–150c, delve bosses 150–1000c — so a full stack is a real mid-band outlay.

### 1.3 Expected-value model

For attacker DEX A vs. defender DEX D: `E[damage multiplier] = P(success) × (1 + 0.5 × P(crit)) + 0.5 × P(graze)`. Player expected damage/round = `(weapon_mid + STR) × E[mult]`; NPC expected damage/round = `STR × E[mult]` (uniform 0.8–1.2 averages to 1.0). TTK = HP / expected damage per round. Int-truncation of per-hit damage (~−0.5/hit) is ignored; it shifts nothing at survey precision.

**Encounters** (boss + gated adds, multi-aggro rooms): all members attack from round 1; the player kills in ascending-HP order (adds first); expected damage taken = Σ over members of (member DPS × time until that member dies). This is deterministic expected-value math — no variance modelling. Variance matters exactly where the verdicts already say CLIFF/INFEASIBLE (long fights compound bad-streak risk), so it only strengthens those verdicts.

**Potions-to-win** = `ceil(max(0, damage_taken − 0.75 × player_HP) / 25)` — the player is willing to spend down to 25% of their own HP pool and heals the rest. **Feasibility bound (ruled in #89): potions-to-win > 20 (the carried stack) = not feasible**, even if the DPS math converges.

**Verdict scale** (applied at the NPC's own level — "at-level" — plus the L5/L10 reference columns):
- **OK** — at-level potions ≤ 5 and hit% within 5 points of the blessed target.
- **HARD** — winnable at-level but leans on the stack (6–12 potions), typically from co-spawn compounding.
- **CLIFF** — at-level cost is 13–20 potions, or the encounter breaches the 20-stack at-level while becoming comfortable within 2–3 levels: a discontinuity relative to adjacent content.
- **INFEASIBLE** — exceeds the 20-potion stack (or has no damage path) **even at band top (L10) with the Uncommon band weapon**.

### 1.4 Coverage and reconciliation

`seed_world.py` seeds **62 NpcDefinitions**: 11 Convergence roster + 1 Primordial Sphere + 29 Verdant Reach + 21 Viridian Ridge. Of these:

- **41 are combat NPCs** (attackable, real authored stats) — the survey population: 24 Verdant (8 surface, 4 villagers, 6 cave insects, 3 bosses, 3 gated minions) + 17 Ridge (6 surface, 2 villagers, 3 elders, 3 bosses, 3 gated minions). All 41 appear in the findings table.
- **17 are non-attackable** (service NPCs, traders, shards, spheres, obelisks, cart vendors): excluded.
- **4 are attackable with placeholder stats** (Aldric, Info Prime, Seris, Veris — `base_vitality=999`, all stats 1): technically killable; recorded as observation G7, not surveyed as combat content.

The architecture doc's v19 Brief 7 narrative says "Z01's 42 combat NPCs"; this survey counts 41 attackable-with-authored-stats definitions in Z01. The off-by-one is doc drift (likely counting a since-reclassified NPC), noted in G7.

---

## 2. Findings table

Columns: contest stats from `get_npc_stats` at Mk 1; Hit% = player hit-or-crit chance; NPC-hit% = NPC hit-or-crit chance against the reference player; TTK in combat rounds (P→N = player kills NPC, N→P = NPC kills an unhealed player); Potions = potions-to-win, solo. All at L5 / L10 reference players with the Uncommon broadsword. "At-lvl hit" = player hit% at player level = NPC level, against the blessed calibration target. Gated minions are shown solo for the row; their real evaluation is inside their boss encounter (§2.1). **This table is authoritative over any prose summary.**

| NPC | Tier | Lvl | DEX | STR | HP | Placement | Hit% L5/L10 | NPC-hit% L5/L10 | TTK P→N L5/L10 | TTK N→P L5/L10 | Potions L5/L10 | At-lvl hit (blessed) | Verdict | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| river-otter | normal | 1 | 18 | 4 | 15 | Vale v08/v17/v21 | 100%/100% | 5%/0% | 0.3/0.2 | 374.3/∞ | 0/0 | 55% (55%) | **OK** |  |
| black-bear | normal | 2 | 20 | 12 | 35 | Vale v06/v12/v21 | 95%/100% | 15%/0% | 0.8/0.5 | 68.9/∞ | 0/0 | 55% (55%) | **OK** |  |
| young-mountain-lion | normal | 2 | 20 | 10 | 28 | Vale v18 | 95%/100% | 15%/0% | 0.6/0.4 | 82.6/∞ | 0/0 | 55% (55%) | **OK** |  |
| wild-boar | elite | 3 | 26 | 17 | 55 | Vale v19 | 65%/100% | 45%/0% | 1.7/0.9 | 20.7/∞ | 0/0 | 40% (40%) | **OK** |  |
| plains-deer | normal | 4 | 26 | 16 | 45 | Flats f02/f04/f15/f16 | 65%/100% | 45%/0% | 1.4/0.7 | 22.0/∞ | 0/0 | 50% (55%) | **OK** |  |
| plains-rabbit | normal | 4 | 26 | 12 | 18 | Flats f07/f10 | 65%/100% | 45%/0% | 0.5/0.3 | 29.4/∞ | 0/0 | 50% (55%) | **OK** |  |
| prairie-dog | normal | 4 | 26 | 12 | 16 | Flats f13 | 65%/100% | 45%/0% | 0.5/0.3 | 29.4/∞ | 0/0 | 50% (55%) | **OK** |  |
| buffalo | elite | 5 | 31 | 26 | 90 | Flats f09/f11/f17 | 40%/100% | 70%/10% | 4.2/1.5 | 9.1/54.8 | 0/0 | 40% (40%) | **OK** |  |
| reedmere-villager | normal | 2 | 20 | 9 | 30 | Reedmere rm1/rm2 | 95%/100% | 15%/0% | 0.7/0.5 | 91.8/∞ | 0/0 | 55% (55%) | **OK** | passive; attackable |
| reedmere-fisher | normal | 2 | 20 | 10 | 30 | Reedmere rm3 | 95%/100% | 15%/0% | 0.7/0.5 | 82.6/∞ | 0/0 | 55% (55%) | **OK** | passive; attackable |
| windhome-villager | normal | 4 | 26 | 17 | 50 | Windhome w1/w2 | 65%/100% | 45%/0% | 1.5/0.8 | 20.7/∞ | 0/0 | 50% (55%) | **OK** | passive; attackable |
| windhome-hunter | normal | 5 | 28 | 20 | 65 | Windhome w2 | 55%/100% | 55%/0% | 2.3/1.0 | 14.8/253.0 | 0/0 | 55% (55%) | **OK** | passive; attackable |
| cave-spider | normal | 2 | 20 | 9 | 25 | Spinner's Hollow c1a/c2a/c2b | 95%/100% | 15%/0% | 0.5/0.4 | 91.8/∞ | 0/0 | 55% (55%) | **OK** | aggro; co-spawns ×2 trivial |
| cave-centipede | normal | 3 | 23 | 14 | 32 | Silken Cleft c2b/c2c | 80%/100% | 30%/0% | 0.8/0.5 | 35.3/∞ | 0/0 | 55% (55%) | **OK** | aggro; mixed pairs trivial |
| cave-beetle | normal | 3 | 23 | 15 | 40 | Silken Cleft c2c | 80%/100% | 30%/0% | 1.0/0.6 | 32.9/∞ | 0/0 | 55% (55%) | **OK** | aggro |
| giant-cave-spider | normal | 4 | 26 | 19 | 55 | Whistling Sink c3a/c3d, Drone Pit c4b/c4d | 65%/100% | 45%/0% | 1.7/0.9 | 18.5/∞ | 0/0 | 50% (55%) | **OK** | aggro |
| giant-cave-centipede | normal | 5 | 28 | 23 | 65 | Whistling Sink c3b/c3e, Drone Pit c4c/c4f | 55%/100% | 55%/0% | 2.3/1.0 | 12.9/220.0 | 0/0 | 55% (55%) | **OK** | aggro |
| giant-cave-beetle | normal | 5 | 28 | 24 | 75 | Whistling Sink c3c/c3e, Drone Pit c4a-c4g | 55%/100% | 55%/0% | 2.7/1.2 | 12.3/210.8 | 0/0 | 55% (55%) | **OK** | aggro |
| silk-matron | boss | 3 | 29 | 17 | 120 | Silken Cleft c2d | 50%/100% | 60%/0% | 4.6/1.9 | 16.0/198.4 | 0/0 | 25% (25%) | **OK** | with 2 brood: 3 pot at L3, 0 at L5 |
| matrons-brood | normal | 2 | 20 | 9 | 25 | c2d x2 (gated) | 95%/100% | 15%/0% | 0.5/0.4 | 91.8/∞ | 0/0 | 55% (55%) | **OK** | gated add, evaluated with boss |
| whistler-below | boss | 6 | 36 | 28 | 260 | Whistling Sink c3f | 15%/75% | 95%/35% | 25.8/5.3 | 6.5/20.8 | 25/0 | 25% (25%) | **CLIFF** | at-level L6: 13 pot solo, 17 with young; fine by L8 full-split build — see §4 |
| whistlers-young | normal | 4 | 26 | 21 | 50 | c3f x2 (gated) | 65%/100% | 45%/0% | 1.5/0.8 | 16.8/∞ | 0/0 | 50% (55%) | **OK** | gated add, evaluated with boss |
| dronemother | boss | 6 | 36 | 30 | 320 | Drone Pit c4h | 15%/75% | 95%/35% | 31.7/6.5 | 6.1/19.4 | 34/0 | 25% (25%) | **CLIFF** | at-level L6: 18 pot solo, 23 with swarm (breaches 20-stack); fine at L8+ |
| dronemothers-swarm | normal | 4 | 26 | 22 | 60 | c4h x2 (gated) | 65%/100% | 45%/0% | 1.8/1.0 | 16.0/∞ | 0/0 | 50% (55%) | **OK** | gated add, evaluated with boss |
| mountain-goat | normal | 6 | 30 | 25 | 70 | Ridge m02/m05/m09/m15/m22/m28/m36 | 45%/100% | 65%/5% | 3.0/1.1 | 10.1/80.2 | 0/0 | 55% (55%) | **OK** |  |
| mountain-squirrel | normal | 6 | 30 | 17 | 20 | Ridge m04/m10/m17/m23/m30/m37 | 45%/100% | 65%/5% | 0.8/0.3 | 14.9/117.9 | 0/0 | 55% (55%) | **OK** |  |
| brown-bear | elite | 7 | 36 | 33 | 130 | Ridge m07/m16/m29 | 15%/75% | 95%/35% | 12.9/2.7 | 5.5/17.7 | 12/0 | 40% (40%) | **OK** | at-level 0 pot |
| mountain-lion | elite | 8 | 39 | 33 | 120 | Ridge m19/m33 | 0%/60% | 100%/50% | 36.3/3.0 | 5.3/13.0 | 47/0 | 35% (40%) | **OK** | at-level 35% hit (−5 rounding drift) |
| prowling-mountain-lion | elite | 9 | 41 | 37 | 150 | Aggro grounds m11 x2 / m38 x3 | 0%/50% | 100%/60% | 136.1/4.5 | 4.7/9.9 | 214/0 | 40% (40%) | **CLIFF** | ×3 room vr-m38: 34 pot at L9, 20 at L10; ×2 vr-m11: 14/7 |
| territorial-brown-bear | elite | 9 | 41 | 41 | 170 | Aggro grounds m24 x2 / m39 x3 | 0%/50% | 100%/60% | 154.2/5.1 | 4.2/8.9 | 271/0 | 40% (40%) | **CLIFF** | ×3 room vr-m39: 45 pot at L9, 27 at L10 (breaches bound at band top) |
| mountain-villager | normal | 7 | 33 | 27 | 95 | Stonestep/Highfold/Lastlight | 30%/90% | 80%/20% | 5.6/1.7 | 7.7/33.5 | 0/0 | 55% (55%) | **OK** | passive; attackable |
| mountain-hunter | normal | 8 | 36 | 31 | 110 | Lastlight ll2 | 15%/75% | 95%/35% | 10.9/2.2 | 5.9/18.8 | 9/0 | 50% (55%) | **OK** | passive; attackable |
| elder-cave-spider | elite | 7 | 36 | 30 | 110 | Undercrag c5a/b/d/g/h, Chitterdeep c6e/g, Hollowcrown c7c/g | 15%/75% | 95%/35% | 10.9/2.2 | 6.1/19.4 | 8/0 | 40% (40%) | **OK** | ×2 rooms: 7 pot at-level L7, 0 at L10 |
| elder-cave-centipede | elite | 8 | 39 | 35 | 130 | Undercrag c5c x2/c5f/c5h, Chitterdeep (7 rooms), Hollowcrown c7e/g/i | 0%/60% | 100%/50% | 39.3/3.3 | 5.0/12.3 | 54/0 | 35% (40%) | **HARD** | NOT a second Whistler; solo at-level 1 pot; ×2 room vr-c5c: 14 pot at L8, 1 at L10 |
| elder-cave-beetle | elite | 9 | 41 | 38 | 150 | Undercrag c5e x2/c5f, Chitterdeep c6c/g/i, Hollowcrown (7 rooms) | 0%/50% | 100%/60% | 136.1/4.5 | 4.6/9.6 | 220/0 | 40% (40%) | **HARD** | solo at-level 0 pot; ×2 rooms: 14 pot at L9, 7 at L10 |
| undercrag-weaver | boss | 9 | 44 | 40 | 500 | Undercrag c5i | 0%/35% | 100%/75% | ∞/20.2 | 4.3/7.4 | ∞/21 | 25% (25%) | **INFEASIBLE** | solo 37 pot at-level L9, 21 at L10; +3 brood: 50/30 — exceeds stack at band top |
| weavers-brood | elite | 6 | 33 | 27 | 90 | c5i x3 (gated) | 30%/90% | 80%/20% | 5.3/1.6 | 7.7/33.5 | 0/0 | 40% (40%) | **OK** | gated add, evaluated with boss |
| chittering-king | boss | 10 | 46 | 46 | 650 | Chitterdeep c6j | 0%/25% | 100%/85% | ∞/34.4 | 3.7/5.7 | ∞/54 | 25% (25%) | **INFEASIBLE** | band top L10: 54 pot solo, 80 with skitterlings |
| kings-skitterlings | elite | 8 | 39 | 35 | 100 | c6j x3 (gated) | 0%/60% | 100%/50% | 30.2/2.5 | 5.0/12.3 | 41/0 | 35% (40%) | **OK** | gated add; solo at-level 0 pot |
| crowned-devourer | boss | 10 | 46 | 49 | 850 | Hollowcrown c7k | 0%/25% | 100%/85% | ∞/44.9 | 3.5/5.3 | ∞/79 | 25% (25%) | **INFEASIBLE** | band top L10: 79 pot solo, 122 with drones |
| devourers-drones | elite | 9 | 41 | 38 | 120 | c7k x3 (gated) | 0%/50% | 100%/60% | 108.9/3.6 | 4.6/9.6 | 175/0 | 40% (40%) | **OK** | gated add; solo at-level 0 pot |

**Verdict counts: 32 OK / 2 HARD / 4 CLIFF / 3 INFEASIBLE** (41 surveyed).

### 2.1 Encounter table (co-spawned groups, evaluated as fought)

Every aggressive room engages as a group. Boss adds are spawn-gated on the living boss (`requires_living_npc`), so the boss fight is always boss + adds. Format: TTK to clear (rounds) / expected damage taken / potions-to-win.

| Encounter | Room | L-mid ref | L-top (L10) ref |
|---|---|---|---|
| Silk Matron + 2 brood | vr-c2d | L3: 11r / 190 / **3** · L5: 6r / 71 / **0** | 3r / 3 / **0** |
| Whistler Below solo | vr-c3f | L6: 17r / 454 / **13** · L8: 8r / 165 / **0** | 5r / 64 / **0** |
| Whistler Below + 2 young | vr-c3f | L6: 19r / 555 / **17** · L8: 10r / 210 / **2** | 7r / 84 / **0** |
| Dronemother solo | vr-c4h | L6: 21r / 598 / **18** · L8: 10r / 217 / **2** | 7r / 85 / **0** |
| Dronemother + 2 swarm | vr-c4h | L6: 23r / 727 / **23** · L8: 13r / 275 / **5** | 8r / 110 / **0** |
| 2× elder cave spider | vr-c5b/d/g, c6e, c7c | L7: 9r / 334 / **7** | 4r / 88 / **0** |
| 2× elder cave centipede | vr-c5c, c6b/d/f/h | L8: 12r / 519 / **14** | 7r / 203 / **1** |
| elder spider + centipede | vr-c5h, c6g | L8: 9r / 356 / **8** | 6r / 143 / **0** |
| 2× elder cave beetle | vr-c5e, c6c, c7b/d/f/h/j | L9: 11r / 523 / **14** | 9r / 353 / **7** |
| elder centipede + beetle | vr-c5f, c6i, c7i | — | 8r / 272 / **4** |
| 2× prowling mountain lion | vr-m11 | L9: 11r / 510 / **14** | 9r / 344 / **7** |
| 3× prowling mountain lion | vr-m38 | L9: 17r / 1019 / **34** | 13r / 688 / **20** |
| 2× territorial brown bear | vr-m24 | L9: 13r / 640 / **19** | 10r / 432 / **10** |
| 3× territorial brown bear | vr-m39 | L9: 19r / 1280 / **45** | 15r / 864 / **27** |
| Undercrag Weaver solo | vr-c5i | L9: 28r / 1085 / **37** | 20r / 694 / **21** |
| Undercrag Weaver + 3 brood | vr-c5i | L9: 33r / 1410 / **50** | 25r / 927 / **30** |
| Chittering King + 3 skitterlings | vr-c6j | — (L10 is at-level) | 42r / 2187 / **80** |
| Crowned Devourer + 3 drones | vr-c7k | — (L10 is at-level) | 56r / 3217 / **122** |

---

## 3. Defect groups

Clusters of the non-OK verdicts and structural observations. These are the shapes of future issues; none are filed here (rulings belong to the design chat).

### G1 — Boss HP escalation crosses the potion bound: the three delve bosses are INFEASIBLE at any attainable level

**Evidence rows:** undercrag-weaver, chittering-king, crowned-devourer (+ their encounter rows).

At the blessed 25% at-level boss hit target, player DPS is pinned at ~0.29 × (weapon_mid + STR) ≈ 16–19/round at L9–10, while the boss hits back at 85–100% for ~0.9 × STR ≈ 34–48/round with zero mitigation. Feasibility therefore decays *linearly in boss HP* at fixed calibration, and the seeded ladder's HP curve (120 → 260 → 320 → 500 → 650 → 850) crosses the 20-potion bound between Dronemother (320) and the Weaver (500):

- **Undercrag Weaver** (500 HP, L9): 37 potions at-level solo; 21 at band top solo; **30 at band top with its 3 brood**.
- **Chittering King** (650 HP, L10 = band top is at-level): 54 solo, **80 with skitterlings**.
- **Crowned Devourer** (850 HP, L10): 79 solo, **122 with drones** — a ~56-round fight absorbing ~3,200 damage.

The Whistler cliff (#66) is the *first symptom* of this group, not an isolated data error: every boss above it on the ladder is strictly worse. A retune limited to #66's six-boss table will fix the numbers it touches but the shape (HP × fixed hit% × unmitigated boss DPS × potion supply) is the underlying defect. Candidate levers, for the design chat: boss HP, the boss DEX offset (drives both directions of the contest), damage mitigation existing at all, potion magnitude/economics, or blessing "raid-style" multi-trip bosses explicitly.

### G2 — Boss escort compounding (the #66 pattern, worse in the delves)

**Evidence rows:** encounter table — every boss row vs. its solo row; matrons-brood/whistlers-young/dronemothers-swarm vs. weavers-brood/kings-skitterlings/devourers-drones.

Verdant bosses take 2 *normal*-tier adds; delve bosses take **3 *elite*-tier adds** (donor stats from the elder trio). The adds multiply opening group DPS by ~1.6–2.7× and add 25–55% to potions-to-win on top of already-failing solo numbers (Weaver 21→30, King 54→80, Devourer 79→122 at band top). The Whistler's young (+2 normals, +4 potions at L6) are the mildest instance of the pattern; the Dronemother's swarm pushes her over the 20-stack at-level (18→23); the delve escorts are strictly compounding an already-infeasible base.

### G3 — The DEX-contest knife-edge: blessed targets assume a max-DEX build (the actual #66 mechanism)

**Evidence:** §4 sensitivity table; whistler-below row; operator report in #66 (L8, STR/DEX 25/25, "hard = I miss a lot").

Because the d20 bridges only 20 points, a boss at `curve + 6` sits 6 points above a player who tracks the curve exactly — and **26+ points above a player whose DEX lags the curve by 10**. Against the Whistler (DEX 36): a DEX-35 canonical L8 hits 50% and wins with 0–2 potions; the operator's actual DEX-25 L8 hits **0%** (grazes only, 15% × half damage) and needs ~97–105 potions — observed as unwinnable, computed as unwinnable. The cliff edge is brutally sharp: DEX ≤ 22 does literally zero damage, 23–25 is graze-only, and every point from 26 to 36 buys +5% hit. The blessed 55/40/25 calibration is only real for players who bank every second point into DEX; the game never tells the player this, and nothing prevents a "reasonable" build (say STR-heavy, or points saved) from walking off the edge. This is a *system* finding about calibration assumptions, separate from G1's HP finding — fixing boss HP alone leaves the knife-edge; fixing the offset alone leaves the HP wall.

### G4 — Band-top ×3 aggro-elite rooms breach the feasibility bound

**Evidence rows:** prowling-mountain-lion, territorial-brown-bear; encounter rows vr-m38, vr-m39 (vs. vr-m11, vr-m24).

The warned-about forbidden grounds spawn 3 aggressive L9 elites that engage simultaneously: vr-m38 costs 34 potions at L9 / 20 at L10 (exactly the stack); vr-m39 costs **45 at L9 / 27 at L10 — beyond the stack even at band top with the best band weapon**. These rooms are deliberately flavored as deadly ("the villagers told you"), so this may be working as intended — but by #89's ruled bound they are not feasible solo at any attainable level, and there is no signal distinguishing "flavor-deadly, come back at Mk 2" from a data error. Needs an explicit design ruling either way; the ×2 versions of the same rooms (14/19 potions at L9, 7/10 at L10) sit just inside feasibility and show how steep the third add is.

### G5 — Elite even-level −5% calibration drift (rounding parity, not data error)

**Evidence rows:** mountain-lion, elder-cave-centipede, kings-skitterlings (35% vs. blessed 40% at-level); plains-deer, plains-rabbit, prairie-dog, windhome-villager, giant-cave-spider, whistlers-young, dronemothers-swarm, mountain-hunter (50% vs. 55%).

At levels where `2.5 × (L−1)` lands on .5 (even levels), banker's rounding in the NPC curve and the floor-share of the player's odd point can misalign by 1 DEX = 5% hit. All deviations found are exactly −5% and only at L4/L8; odd-level NPCs are exact. This is calibration noise inherent to integer stats, worth recording against the arch doc's "blessed targets exact and constant at every level" claim, but it flips no verdict on its own — note that mountain-lion, elder-cave-centipede, and kings-skitterlings (all L8 elites) carry it into their group fights, which is part of why the ×2 elder-centipede room reads HARD.

### G6 — Latent: NPC HP ignores level and Mk tier ("quantities multiply" is unimplemented for vitality)

**Evidence:** `create_live_instance` (run_tick_engine.py) sets `vitality = base_vitality` flat; `get_npc_stats` scales contest stats from `npc_level` but returns `vitality_current` untouched; arch doc §"Contests add, quantities multiply" states pools *may* scale multiplicatively — nothing does.

No live impact today (every spawn is Mk 1), but the moment any Mk 2 spawn is authored, its contest stats will be level-12+ while its HP stays at the Mk 1 authored value — an instant trivialization in the direction opposite to the pre-v20 unkillable-spiders bug. Worth an issue before Mk 2 content exists.

### G7 — Observations (no verdict impact)

- **Armor and all rolled item stats are combat-inert.** Player defense is raw `stat_dex`; NPC damage takes no mitigation input; nothing applies `rolled_primary_stats`/`rolled_secondary_stats` to characters. Five of eight seeded boss-loot groups (armor and accessories) therefore have zero combat effect. The GDD lists item primary stats as a core item property without specifying application; the code never applies them. If they are ever wired up (e.g. +DEX gear), G3's knife-edge geometry changes materially — gear would become the intended way to buy contest points.
- **Attackable placeholder NPCs:** Aldric, Info Prime, Seris, and Veris are attackable with 999 HP / all-1 stats (effective DEX still 18 from the curve, STR 1). A patient level-1 player can slowly kill named Convergence roster NPCs for 10 XP each. Harmless mathematically, odd narratively; `attackable=False` would match the rest of the roster.
- **Arch-doc count drift:** v19 Brief 7 narrative says "Z01's 42 combat NPCs"; the current seed has 41.
- **XP attainability context for the reference players:** cumulative XP to L10 is 28,500 (`level² × 100` per step); at-level kills pay `10 × scaling_factor` (10–100), so the band-top reference represents several hundred kills. Attainable, but the delve bosses are gated behind substantial grind *before* their infeasibility even becomes visible to a player.

---

## 4. #66 refinement — the Whistler Below encounter in full

All numbers Mk 1, Uncommon broadsword (16.09 expected mid), draughts heal 25. Whistler: L6, DEX 36 (curve 30 + boss 6), STR 28, HP 260, expected 28 damage/landed hit, hits the listed player builds at the listed rates. Young (×2, gated): L4, DEX 26, STR 21, HP 50 each.

**Player-side sensitivity vs. Whistler defense (10 + 36 = 46):**

| Player DEX | Hit% | Graze% | Expected player dmg/round (STR/DEX split build) |
|---|---|---|---|
| ≤ 22 | 0% | 0% | **0 — no damage path** |
| 23–25 | 0% | 5–15% | 1.0–3.1 (graze-only) |
| 26 | 5% | 15% | ~4.5 |
| 28 | 15% | 15% | ~7.9 |
| 30 (canonical L6) | 25% | 15% | ~15.6 |
| 35 (canonical L8) | 50% | 15% | ~31.1 |
| 40 (canonical L10) | 75% | 15% | ~48.0 |

**Encounter outcomes:**

| Attacker | Solo: TTK / dmg taken / potions | + 2 young: TTK / dmg taken / potions |
|---|---|---|
| L6 canonical (STR 31 / DEX 30, HP 203) | 17r / 454 / **13** | 19r / 555 / **17** |
| L8 canonical (36/35, HP 228) | 8r / 165 / **0** | 10r / 210 / **2** |
| **L8 operator build (25/25, HP 195)** | 84r / 2551 / **97** | 89r / 2767 / **105** |
| L10 canonical (41/40, HP 253) | 5r / 64 / **0** | 7r / 84 / **0** |

**Reading:** the fight is calibrated to its blessed target at-level (25% hit at L6) but the *cost* of that calibration — 13–17 potions through a 27–45 DPS storm against a 203-HP player — is CLIFF-grade at the level the content implies. Two levels later it collapses to trivial *if and only if* the player bought DEX with every second point; the operator's 25/25 build at L8 is mathematically unwinnable (97+ potions), fully explaining the #66 report. The young add ~100 damage / 4 potions at L6 — real but secondary; the Matron's brood comparison (3 potions total at L3) shows the ladder's difficulty step is dominated by the boss DEX+HP jump, not the escorts. A retune that only trims the Whistler's numbers should also decide what build the 25% target is allowed to assume (G3) and where the ladder's HP curve is allowed to cross the potion bound (G1), or the same cliff reappears one boss later — the survey's delve numbers show it already has.

---

*Survey computation: expected-value model over the code formulas above; script not committed per the brief — §1 carries reproducibility. Verdicts and encounter figures generated 2026-07-16 against `seed_world.py` as of commit `ef3ce6d`.*
