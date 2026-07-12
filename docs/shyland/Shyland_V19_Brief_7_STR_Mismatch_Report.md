# Shyland V19 Brief 7 — STR Table Conformance Report

**Status: implementation applied to the working tree, NOT committed.** Per the
brief's own instruction ("if any implementation result disagrees with this
table, the table wins and the disagreement is a stop-and-flag"), this brief
is paused pending design-chat review of the discrepancy below. No commit, no
architecture doc update, has been made.

## What was implemented

All of Brief 7 as written: `combat_utils.py` (`npc_level`, rewritten
`get_npc_stats`, `NPC_CONTEST_BASE`/`NPC_CONTEST_STEP`/`NPC_TIER_OFFSET`/
`MK_LEVEL_SPAN`, `acuity_damage_modifier`), the `run_tick_engine.py` call-site
change, the boss `scaling_factor` data migration (`0023_boss_scaling_factor_corrections.py`),
and the matching `seed_world.py` tuple sync. The formula used is exactly the
brief's pseudocode:

```python
def npc_level(npc_instance):
    return npc_instance.definition.scaling_factor + MK_LEVEL_SPAN * (npc_instance.mk_tier - 1)

def get_npc_stats(npc_instance):
    d = npc_instance.definition
    L = npc_level(npc_instance)
    curve = round(NPC_CONTEST_BASE + NPC_CONTEST_STEP * (L - 1))
    offset = NPC_TIER_OFFSET.get(d.combat_tier, 0)
    growth = round(NPC_CONTEST_STEP * (L - 1))
    return {'dex': curve + offset, 'str': d.base_str + growth, ...}
```

## Verification results

- **DEX / defense / blessed hit%: 41/41 rows match the brief's table exactly.**
  100k-roll simulations confirm 55% (normal) / 40% (elite) / 25% (boss)
  at-level hit rates within tolerance, at mk 1 and at a synthetic mk 2
  instance, and the reverse (NPC-attacks-player) rates of 55/70/85%.
- **Acuity (`acuity_damage_modifier`): all unit checks pass exactly** —
  every Origin at baseline returns neutral 1.0 (including Feral 0.95, the
  float-bug regression case), Feral 1.25 → 1.15, Voidtouched 0.30 → 0.90,
  Voidtouched 1.9 → 1.60, and `calculate_damage` focus-gating (bonus only on
  focus target, penalty always) is confirmed both ways.
- **STR: 27/41 rows match; 14/41 are off by exactly ±1.**

## The STR discrepancy

The brief's formula gives one `growth` value per level
(`round(NPC_CONTEST_STEP * (L - 1))`) — every NPC at the same level gets the
same STR growth added to its authored `base_str`. The table's own numbers
don't hold to that: at identical levels, different NPCs imply different
growth.

All 14 mismatches occur exactly at the five levels where
`2.5 × (L-1)` lands precisely on a `.5` boundary — L = 2, 4, 6, 8, 10 (2.5,
7.5, 12.5, 17.5, 22.5). At every odd level (1, 3, 5, 7, 9), where the product
is a clean integer, **all rows match perfectly, 0 exceptions.** So this is a
rounding-tie artifact — but not one resolvable by picking a different
rounding rule, because the table splits in both directions, sometimes within
the same level:

| Level | .5 boundary | Rows matching formula (round-half-even) | Rows wanting +1 | Rows wanting −1 |
|---|---|---|---|---|
| L2 | 2.5 → 2 | black-bear, young-mountain-lion, reedmere-fisher | reedmere-villager, maro-the-mender, essa-the-trader, cave-spider | — |
| L4 | 7.5 → 8 | plains-deer, plains-rabbit, prairie-dog | — | windhome-villager, tavik-the-mender, sona-the-trader, giant-cave-spider |
| L6 | 12.5 → 12 | whistler-below, dronemother | mountain-goat, mountain-squirrel | — |
| L8 | 17.5 → 18 | *(no matching rows at L8)* | — | mountain-lion, mountain-hunter, elder-cave-centipede |
| L10 | 22.5 → 22 | chittering-king | crowned-devourer | — |

Round-half-up would fix L2/L6/L10 but break L4/L8 (which already match
round-half-even and would go one *too high*). Round-half-down (floor)
matches L4/L8's mismatches but breaks the L2/L6/L10 rows that currently
match. No single tie-breaking rule reproduces the table — the STR column
appears to have been computed by hand per-NPC in the design chat rather than
from the stated closed-form formula, and picked up ±1 slips at the boundary
levels.

## Full data (all 41 table rows)

`table_growth` = table's `New STR` − authored `base_str`. `formula_growth` =
`round(2.5 × (L−1))`, the brief's literal formula. `diff` = table − formula.

| NPC | L | base_str | table STR | table_growth | formula_growth | diff |
|---|---|---|---|---|---|---|
| river-otter | 1 | 4 | 4 | 0 | 0 | 0 |
| black-bear | 2 | 10 | 12 | 2 | 2 | 0 |
| young-mountain-lion | 2 | 8 | 10 | 2 | 2 | 0 |
| wild-boar | 3 | 12 | 17 | 5 | 5 | 0 |
| plains-deer | 4 | 8 | 16 | 8 | 8 | 0 |
| plains-rabbit | 4 | 4 | 12 | 8 | 8 | 0 |
| prairie-dog | 4 | 4 | 12 | 8 | 8 | 0 |
| buffalo | 5 | 16 | 26 | 10 | 10 | 0 |
| reedmere-villager | 2 | 7 | 10 | 3 | 2 | **+1** |
| reedmere-fisher | 2 | 8 | 10 | 2 | 2 | 0 |
| windhome-villager | 4 | 9 | 16 | 7 | 8 | **−1** |
| windhome-hunter | 5 | 10 | 20 | 10 | 10 | 0 |
| maro-the-mender | 2 | 7 | 10 | 3 | 2 | **+1** |
| essa-the-trader | 2 | 7 | 10 | 3 | 2 | **+1** |
| tavik-the-mender | 4 | 9 | 16 | 7 | 8 | **−1** |
| sona-the-trader | 4 | 9 | 16 | 7 | 8 | **−1** |
| cave-spider | 2 | 7 | 10 | 3 | 2 | **+1** |
| cave-centipede | 3 | 9 | 14 | 5 | 5 | 0 |
| cave-beetle | 3 | 10 | 15 | 5 | 5 | 0 |
| giant-cave-spider | 4 | 11 | 18 | 7 | 8 | **−1** |
| giant-cave-centipede | 5 | 13 | 23 | 10 | 10 | 0 |
| giant-cave-beetle | 5 | 14 | 24 | 10 | 10 | 0 |
| silk-matron | 3 | 12 | 17 | 5 | 5 | 0 |
| whistler-below | 6 | 16 | 28 | 12 | 12 | 0 |
| dronemother | 6 | 18 | 30 | 12 | 12 | 0 |
| mountain-goat | 6 | 13 | 26 | 13 | 12 | **+1** |
| mountain-squirrel | 6 | 5 | 18 | 13 | 12 | **+1** |
| brown-bear | 7 | 18 | 33 | 15 | 15 | 0 |
| mountain-lion | 8 | 15 | 32 | 17 | 18 | **−1** |
| prowling-mountain-lion | 9 | 17 | 37 | 20 | 20 | 0 |
| territorial-brown-bear | 9 | 21 | 41 | 20 | 20 | 0 |
| mountain-villager | 7 | 12 | 27 | 15 | 15 | 0 |
| mountain-hunter | 8 | 13 | 30 | 17 | 18 | **−1** |
| old-brammel | 7 | 12 | 27 | 15 | 15 | 0 |
| ridda-the-trader | 7 | 12 | 27 | 15 | 15 | 0 |
| elder-cave-spider | 7 | 15 | 30 | 15 | 15 | 0 |
| elder-cave-centipede | 8 | 17 | 34 | 17 | 18 | **−1** |
| elder-cave-beetle | 9 | 18 | 38 | 20 | 20 | 0 |
| undercrag-weaver | 9 | 20 | 40 | 20 | 20 | 0 |
| chittering-king | 10 | 24 | 46 | 22 | 22 | 0 |
| crowned-devourer | 10 | 27 | 50 | 23 | 22 | **+1** |

## For the design chat to decide

1. **Accept the ±1 STR slack.** STR is explicitly not the difficulty dial in
   this brief (DEX alone sets hit%); it's flavor/species-muscle that "grows
   at the player-curve slope so damage stays proportionate." A ±1 STR
   difference on a handful of NPCs changes damage output by a fraction of a
   point. Ratify the code formula (`round(NPC_CONTEST_STEP * (L-1))`,
   round-half-even) as authoritative and close the loop — no table
   correction needed.
2. **Correct the table.** Provide amended `New STR` values (or an amended
   growth rule) for the 14 flagged rows so the table and formula agree
   exactly, and re-issue as an amendment to this brief.

Everything else in the brief (DEX/hit%, Acuity, boss `scaling_factor`
corrections, minion inventory) is verified and ready; only this STR question
is blocking close-out.
