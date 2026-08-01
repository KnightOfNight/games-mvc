# Shyland V24.2 — Brief 1: Healing-Economy Income Table (Loot-in-Kind)

**Release:** Version 24.2 (point release; V24 new-zone-prep major, Phase 1 — healing economy)
**Branch:** `version_24_2`
**Founding ticket:** #164 (healing economics — income can't fund the staple)
**Dependency shipped by this brief:** #181 (loot-table enrichment — draughts and materials as NPC drops)
**Design authority:** GDD §6.15 (this release, on this branch) and the operator-confirmed rulings on #164 (2026-08-01, six points) and #181 (2026-08-01, per-table design). Where this brief's tables and its prose disagree, **the tables are authoritative**.
**Written:** 2026-08-01, V24.2 design session.

---

## 1. Context (read-only)

The #180 fight-cost survey (V24.1) plus a faucet audit established: bosses and villagers already satisfy the Income Law (k = 2 — expected income ≈ 2 × expected draught cost per kill, solo); the whole structural deficit is the aggressive grind population, paying ~0.7 cp/kill against solo draught costs of ~7.2 cp (normal) / ~26.2 cp (elite). The ruled fix is **loot-in-kind**: per-tier loot tables that pay grind kills in healing draughts and materials — no new copper faucets (beasts and insects don't carry coins; zone lore, operator-ruled).

This is a **data-only brief**: seed content and seed self-checks in `django/src/apps/shyland/management/commands/seed_world.py`, plus the version constant. **No model changes. No migrations. No runtime code changes.** The loot roll path (`item_utils.generate_loot_from_table` → `generate_item_instance`) is definition-generic and already handles consumables and materials; do not modify it.

**Pre-flight (prior pending deploy-time actions):** none outstanding — V24.0's production `make seed` executed in the V24.0 closeout tail; V24.1 was a research release with zero deploy-time actions (per its committed closeout report).

## 2. Version constant (opening act — own commit)

First implementation brief of the release: bump `SHYLAND_VERSION` to `"24.2-DEV"` in `django/src/apps/shyland/version.py`, moving the pin-test assertion in the same commit, then run the version-start `make deploy-dev` from the worktree.

## 3. Item definition changes (seed)

All in `seed_world.py`. The seed is authoritative ("the code is definitive") — reseeding is enforce-exact.

### 3a. Rebase the two common materials (two sites each)

| Slug | `base_value` old → new | Sites |
|---|---|---|
| `animal-hide` | 6 → **12** | authored item dict (`'base_value': 6`) **and** the v18-brief-4 `base_values` back-fill dict (`'animal-hide': 6`) |
| `insect-carapace` | 8 → **12** | authored item dict **and** `base_values` dict |

Sale price becomes 4 cp each (value ÷ 3). Descriptions unchanged.

### 3b. Make the seed own the draught's value

`healing-draught`'s authored item dict currently carries **no** `base_value` key — the live DB value (12) is historical and unowned by the seed. Add `'base_value': 15` to the `healing-draught` item dict (and `'healing-draught': 15` to the `base_values` back-fill dict, so reseeds force it). This implements #164 ruling point 2's arithmetic exactly: a draught is worth 15 cp (the Essa/Sona/Ridda vendor price standard), sale 5 cp. Vendor `VendorEntry` prices (already 15) are untouched. `focus-tonic` and `repair-kit` are out of scope — leave them alone.

### 3c. Two new elite material definitions

Append to the materials block (mirror the hide/carapace dict shape exactly — `item_type='material'`, `genre_tag='fantasy'`, no slots, no stats, no durability), and add both to the `base_values` back-fill dict at 36:

| Slug | Name | `base_value` | Description (authored creative content — use verbatim) |
|---|---|---|---|
| `pristine-animal-pelt` | Pristine Animal Pelt | 36 | `A flawless pelt from a beast in its prime — thick, unscarred, heavy in the hand. Traders pay well.` |
| `hardened-insect-chitin` | Hardened Insect Chitin | 36 | `A slab of chitin dense enough to turn a knife. Traders and tinkerers alike pay for these.` |

Sale price 12 cp each.

## 4. Loot table changes (seed)

### 4a. Four new tables (in `_seed_verdant_loot_tables`)

All entries: `mk_tier_min=1, mk_tier_max=1`, `guaranteed_group=''` (independent rolls), `rarity_weights={'common': 100}`.

| Table slug | Table name | Entries (item slug, drop_chance) |
|---|---|---|
| `combat-animal-drops` | Combat Animal Drops | (`healing-draught`, 0.35), (`animal-hide`, 0.5) |
| `combat-insect-drops` | Combat Insect Drops | (`healing-draught`, 0.35), (`insect-carapace`, 0.5) |
| `elite-animal-drops` | Elite Animal Drops | (`healing-draught`, 1.0), (`pristine-animal-pelt`, 1.0), (`animal-hide`, 0.5) |
| `elite-insect-drops` | Elite Insect Drops | (`healing-draught`, 1.0), (`hardened-insect-chitin`, 1.0), (`insect-carapace`, 0.5) |

### 4b. `animal-drops` — UNCHANGED, membership shrinks to the seven trivial passives

The table itself (one entry: `animal-hide` at 0.35) is untouched. After the re-pointing in 4d, its **only** users are: `river-otter`, `black-bear`, `young-mountain-lion`, `plains-deer`, `plains-rabbit`, `prairie-dog`, `mountain-squirrel`. This is the ruled carve-out — no 1-minute-respawn rabbit-farm draught faucet.

### 4c. `insect-drops` — deleted

After 4d, zero NPC definitions reference it. Remove its seed block and add an explicit deletion to the seed (delete `LootTable` slug `insect-drops`; its single entry goes by CASCADE). **Expected deletion count: 2 rows** (1 `LootTable` + 1 `LootTableEntry`). No other deletions are expected anywhere in this brief.

### 4d. NPC re-pointing (22 `NpcDefinition` rows change `loot_table`)

Exact enumeration — this list is authoritative:

| New table | NPC slugs | Count |
|---|---|---|
| `combat-animal-drops` | `mountain-goat` | 1 |
| `combat-insect-drops` | `cave-spider`, `cave-centipede`, `cave-beetle`, `giant-cave-spider`, `giant-cave-centipede`, `giant-cave-beetle`, `matrons-brood`, `whistlers-young`, `dronemothers-swarm` | 9 |
| `elite-animal-drops` | `wild-boar`, `buffalo`, `brown-bear`, `mountain-lion`, `prowling-mountain-lion`, `territorial-brown-bear` | 6 |
| `elite-insect-drops` | `elder-cave-spider`, `elder-cave-centipede`, `elder-cave-beetle`, `weavers-brood`, `kings-skitterlings`, `devourers-drones` | 6 |

Note: `mountain-goat` is passive but is **not** in the seven-passive carve-out (the ruling's list is exact); it takes the enriched normal animal table. The delve adds are elite-tier and take the elite table, per the ruling ("all 12 elites, including the delve adds").

**Untouched by rule:** all villager gear tables (`reedmere-gear`, `windhome-gear`, `ridge-gear`, `ridge-hunter-gear`), all six boss tables (including their existing `insect-carapace` 0.5 side entries), all copper drop ranges everywhere (#164 ruling point 3: boss and villager copper numbers are unchanged).

## 5. Seed self-check updates

In the verification pass:

- `table_entry_counts`: remove `'insect-drops': 1`; add `'combat-animal-drops': 2`, `'combat-insect-drops': 2`, `'elite-animal-drops': 3`, `'elite-insect-drops': 3`. Update the check label `'12 Verdant loot tables with expected entry counts'` → `'15 Verdant loot tables with expected entry counts'`.
- New check — carve-out membership: exactly the seven slugs of 4b (and no others) have `loot_table__slug='animal-drops'`.
- New check — re-pointing counts: `NpcDefinition` counts per new table equal 1 / 9 / 6 / 6 per the 4d table.
- New check — `insect-drops` gone: no `LootTable` with that slug exists and no `NpcDefinition` references it.
- New check — values: `animal-hide` and `insect-carapace` base_value 12; `pristine-animal-pelt` and `hardened-insect-chitin` exist, `item_type='material'`, base_value 36; `healing-draught` base_value 15.

## 6. Verification (all must pass before any issue closes)

1. Full in-container suite: `python manage.py test apps/shyland/tests` via `docker exec` in the django container (path form — the only working invocation). All tests pass.
2. `make seed` on the dev stack: all self-checks pass, including the five new/updated ones in §5. Report actual deletions vs the expected 2 rows.
3. Functional loot roll (Django shell, statistical): roll `generate_loot_from_table` ≥ 1,000 times against each new table; assert (a) elite tables yield exactly one draught and exactly one elite material on every roll, plus a common material at ~0.5; (b) combat tables yield draughts at ~0.35 and the common material at ~0.5 (binomial tolerance ±5 points); (c) `animal-drops` never yields a draught.
4. Economy spot-check (authoritative expectations): expected income per kill at Mk 1 — combat normal ≈ 7.25 cp (0.35 × 15 + 0.5 × 4), elite ≈ 29 cp (15 + 12 + 0.5 × 4), trivial passive ≈ 1.4 cp (0.35 × 4). Compute from the seeded rows, not from this brief's constants.
5. Sale prices via `get_sale_price`: hide 4, carapace 4, pelt 12, chitin 12, draught 5.

## 7. Dev deploy and data action (code first, data second)

Once §§3–6 implementation and tests pass: `make deploy-dev` from the worktree, **then** `make seed` against the dev stack (the deploy bakes the new seed into the image before the data action runs). Record actual seed deletions/creations in the closeout report against: 2 rows deleted; 4 `LootTable` + 10 `LootTableEntry` + 2 `ItemDefinition` created; 22 `NpcDefinition` and 3 `ItemDefinition` value rows updated.

## 8. Operator playtest checklist (dev stack)

1. Kill several cave spiders (combat normal): draughts appear on roughly a third of corpses; carapaces on about half.
2. Kill an elite (e.g. an elder cave spider): corpse always holds a draught and a Hardened Insect Chitin.
3. Kill an elite animal (e.g. the territorial brown bear): always a draught and a Pristine Animal Pelt.
4. Kill a plains rabbit: hide sometimes, never a draught.
5. Sell one of each material: hide/carapace pay 4 cp, pelt/chitin pay 12 cp; sell a draught: 5 cp.
6. Buy a draught: still 15 cp. Boss and villager kills: copper and gear drops unchanged.
7. Play a grind session in the caves: draughts roughly keep pace with consumption; wallet trends up on materials.

## 9. PENDING DEPLOY-TIME ACTIONS (production — closeout tail only)

- `make seed` on production after the V24.2 release deploys (Deployment Law step 6 window). Expected deletions: **2 rows** (the `insect-drops` table + its entry). Dev-side execution status to be recorded here by the implementation session. This block stays open until the production execution; any subsequent V24.2 brief/amendment pre-flights whether the dev-side action ran.

## 10. Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. Update `docs/shyland/Shyland_Architecture_v24.md` **in place**: add the Version 24.2 header block entry (point release, `version_24_2`, this brief's content summary — per-tier loot-in-kind tables, material rebase, seed-owned draught value); stamp 24.2. **The header hash moves** (code under `django/src/` changed — seed logic and self-checks), citing this brief's final implementation commit.

## 11. Issue closes (gated on §6 passing)

Close #164 and #181 with implementation comments (what shipped, where, the verification headline). Then the closeout report (including the operator playtest disposition line per #170) and the `implementation-session-end` ritual.

## Standing constraints (never deviate)

- No changes outside `django/src/apps/shyland/management/commands/seed_world.py`, `version.py` + its pin test, and the architecture doc step.
- No model changes, no migrations, no runtime code changes, no vendor stock/price changes, no copper changes.
- Commit and push at every step boundary; branch only; never merge to main.
- Transient documents are committed and left in place; the operator does all pruning.
