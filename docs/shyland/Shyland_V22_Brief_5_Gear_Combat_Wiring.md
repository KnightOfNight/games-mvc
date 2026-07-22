Shyland V22 Brief 5 — Gear Combat Wiring
Type: implementation brief (counts against the v22 cap; the fourth implementation brief of the version) Branch: the current Version 22 worktree branch (`version_22`) — all work, commits, and pushes on that branch Bucket: B5 · Issues: #100 (primary), #109, #110 — all close with this brief, gated on verification. #68's B5 ruling half is implemented here (#68 itself is already closed; do not reopen it). Migrations: NONE. Nothing in this brief touches schema. The stat rename (Step 5a) edits JSON contents and seed data only. If any step appears to require a model change, STOP — that is a defect in this brief.
This brief makes equipped gear real in combat: stat bonuses apply, armor mitigates, procs fire, the bars obey one law, and the stats sheet confesses all of it. The complete ruling record is embedded in Step 1's housekeeping comment; it is authoritative for every implementation step. Data tables are authoritative over prose if they disagree.
Standing rules

* Work in the Version 22 worktree on its branch. Commit and push the branch at every step boundary — branch only, NEVER merge to main on your own initiative; merging is the operator's action after review and playtest. WIP-sized commits are desired.
* Never remove, prune, or clean up any transient document. The operator does all pruning.
* The test suite must run as `apps.shyland.tests` (the stub `tests.py` shadows the package — known issue #117, unfixed, out of scope here; do not fix it, work around it).
* If any repo fact contradicts this brief, stop and record the contradiction in the closeout rather than improvising.

Pre-flight

1. Confirm you are in the Version 22 worktree, tree clean, branch synced with its remote.
2. Verify `DOCKER_HOST` is set and points at the production host before any deployment-touching action.
3. Confirm `gh auth status` shows repo access.

Step 0 — Self-commit this brief
Save this brief verbatim to `docs/shyland/Shyland_V22_Brief_5_Gear_Combat_Wiring.md` (skip if an identical file exists). Commit on the branch and push immediately.
Step 1 — Housekeeping, then HARD GATE
1a. Post this comment on #100, verbatim:

```
B5 knob and wiring rulings — all confirmed by the operator (completing the
ruling record; the design-record comment above holds the framework):

SLOT WEIGHTS (the Option C authored table; only these eight slots carry
armor, per the knob survey): CHEST 3, HEAD 2, LEGS 2, OFF_HAND 2 (shields),
SHOULDERS 1, HANDS 1, WAIST 1, FEET 1. Full set = 13 per Mk tier.

MITIGATION CURVE: mitigation fraction = TAV / (TAV + K), K = 48.
TAV = Σ(slot weight × mk_tier over worn armor pieces)
    + Σ(rolled physical_resist over ALL equipped items).

FLOORS: (1) when TAV > 0, each incoming hit's reduction is at least 1 —
applied ONCE to the total, never per item; (2) the existing minimum-1 final
damage clamp (max(1.0, final) in calculate_damage) is preserved beneath it.
No roll is involved in mitigation; it is deterministic per hit.

PROC FACTOR RENAME (ruled: the *_chance names lie under the new semantics —
the value is a factor driving both frequency and size): the stats
bleed_chance, stun_chance, poison_chance are renamed bleed_factor,
stun_factor, poison_factor in the seed data and on all live rolled
instances. Three flavor-distinct names are kept (not collapsed to one) so
weapon variety survives on examine. crit_chance keeps its name — under its
ruled wiring it genuinely is a chance contribution. lifesteal keeps its
name — under its ruled wiring it genuinely steals life.

SECONDARY-STAT WIRING MAP (the ruled abstraction mapped onto the real
17-stat vocabulary; scope law governs — wire what combat reads, invent
nothing for absent systems):
- str/dex/end/int/wis/per: +N means +N via the effective-stat function.
- physical_resist: consumed by TAV (above). Not a proc.
- crit_chance: +V percentage points (summed rolled values × 0.01) added to
  the existing crit computation in resolve_hit, still capped at CRIT_CAP.
  Wired to the mechanic it names; not a proc.
- bleed_factor / stun_factor / poison_factor: PROC FACTORS. The rolled
  value V does double duty. Per landed player hit, each equipped item rolls
  each of its proc-factor stats independently: chance = V ×
  PROC_CHANCE_PER_POINT (0.05), capped at PROC_CHANCE_CAP (0.50). On
  success: bonus damage = random integer 1..ceil(V) ("up to N", N = the
  rolled value). The names are flavor only — no DoT, no stun, no status
  effects; damage types are not modeled in v22.
- lifesteal: on each landed player hit, heals the attacker by the summed
  rolled values (flat), clamped to vitality_max, via the atomic bar update.
  Always-on, no roll. Not part of the damage parenthetical; no extra output
  line in v22 beyond the bar moving.
- electric_damage_bonus: always-on flat +V to the gear-bonus damage pool on
  every landed hit (rides the proc parenthetical as gear damage).
- spell_damage_bonus, mana_regen, magic_resist, radiation_resist: INERT by
  scope law — their consuming systems (spells, mana, non-physical damage)
  do not exist. They remain visible on items per zeros-never-hidden; they
  are wired to nothing and added to nothing (magic/radiation resist do NOT
  join TAV).

SCALING NOTE (ruled): secondary-stat curves grow shallowly per Mk band
(midpoint = base + factor × mk_tier) relative to NPC band growth. This is
itemization tuning, not wiring — the wiring is curve-agnostic and curves
are seed data. Filed thin and unmilestoned for the Mk 2 era, alongside
#104's territory (see the filings below).

DISPLAY: all gear bonus damage on a hit (proc successes + electric) sums
into one parenthetical on the hit line — "You hit the giant cave spider for
14 (+7) damage." No gear bonus → no parenthetical, line byte-identical to
today. Crits compose: "for a critical 14 (+7) damage!"

BUDGET GUARD: the v21 Z01 boss budgets are re-blessed by survey-lite
recomputation for an armored 25/25 reference build in full Common Mk 1
armor; if any of the six bosses drops to a zero-potion expected fight, the
implementation STOPS before the architecture step and reports for an
operator ruling on K. K is never adjusted unilaterally.

```

1b. File two issues (both thin, unmilestoned, no labels). Capture both numbers from `gh issue create` output.
Issue 1:

* Title: `Authored per-item armor base — guaranteed minimum coverage under rolled resist`
* Body:


```
Future armor-set design seeded during B5's knob session: a real armor field
on ItemDefinition would let a set guarantee minimum coverage (authored base)
while rolled physical_resist provides bonus above it. Option C's derived
slot-weight table (v22) retires gracefully into this — TAV sums authored
bases instead of computed slot × Mk. Same family as the itemization
deepening in #127. Unmilestoned; a future feature version's question.

```

Issue 2:

* Title: `Secondary-stat curves vs Mk band growth — audit before Mk 2 content`
* Body:


```
Surfaced during B5's wiring rulings: secondary-stat midpoints grow as
base + factor × mk_tier (typically +0.2/band) while NPC numbers roughly
double per band — flat-value effects (lifesteal, proc factors, +N stat
bonuses) that matter at Mk 1 shrink toward irrelevance by Mk 3 if curves
stay as seeded. Wiring (v22 B5) is curve-agnostic; curves are pure seed
data under the code-is-definitive rule, so this is a retune, not a rework.
Audit and retune when Mk 2 content is designed — same era as #104, which
blocks all Mk 2 content.

```

⛔ HARD GATE
Verify via `gh issue view`: the #100 comment posted intact; both new issues exist with titles and bodies as specified, no milestones, no labels. Any deviation: STOP, run the issues report, closeout explaining, zero code changes.
Commit and push.
Step 2 — The effective-stat function
File: `django/src/apps/shyland/combat_utils.py`
Add `effective_stats(character)` returning a dict `{'str','dex','end','int','wis','per'}` where each value = the character's base field (`stat_str` … `stat_per`) + the sum of matching entries across all equipped items' `rolled_primary_stats` and `rolled_secondary_stats` (entry shape: `{'stat': <name>, 'value': <number>}`; sum `value` where `stat` matches; round the gear sum to nearest int per stat). Query: the character's `inventory` filtered `is_equipped=True`. One function, computed per use — no caching fields, no schema.
Also add `gear_stat_bonus(character)` (the gear-only dict, same computation without the base) — Step 6's display needs the split.
Wire it everywhere the six stats are read for gameplay. Run an exhaustive sweep for reads of `stat_str|stat_dex|stat_end|stat_int|stat_wis|stat_per` across `apps/shyland/` (consumers, combat_utils, tick engine, item/effect utils). Classify every site in the closeout: gameplay reads (combat contests, damage stat bonuses, carry capacity, initiative, `recalculate_bars`, XP/level-up inputs if any) switch to `effective_stats`; non-gameplay reads (character creation, admin, the base-vs-bonus display itself, spend's mutation of the base field) keep the base. `recalculate_bars` reads effective END/STR — equipping END gear raises `vitality_max` — which is exactly why Step 4's bar law must land in the same commit or earlier. Known formula to preserve with effective inputs: `vitality_max = END×10 + STR×3 + level×5` (and longevity's analogue as coded).
Tests: effective stats equal base with nothing equipped; a +3 STR item moves exactly the gameplay reads; unequipping restores base.
Step 3 — Armor mitigation
File: `django/src/apps/shyland/combat_utils.py`

1. `ARMOR_SLOT_WEIGHTS = {'CHEST': 3, 'HEAD': 2, 'LEGS': 2, 'OFF_HAND': 2, 'SHOULDERS': 1, 'HANDS': 1, 'WAIST': 1, 'FEET': 1}` — module constant beside the other combat constants, with a comment naming it the Option C table (retires if authored armor fields ever ship).
2. `ARMOR_MITIGATION_K = 48`.
3. `total_armor_value(character)`: Σ(`ARMOR_SLOT_WEIGHTS[equipped_slot] × mk_tier`) over equipped items with `definition.item_type == 'armor'` whose `equipped_slot` is in the table, plus Σ of `physical_resist` entries in `rolled_secondary_stats`/`rolled_primary_stats` across ALL equipped items (any item_type). Items with `durability_current == 0` / `is_broken` contribute nothing (non-functional band).
4. `apply_armor_mitigation(damage, tav)`: if `tav <= 0` return damage unchanged; `reduction = max(1, round(damage × tav / (tav + ARMOR_MITIGATION_K)))`; return `damage - reduction`, then clamp the result to ≥ 1. Applied to NPC→player damage AFTER `calculate_damage` produces the hit's final value.

Wire into the NPC→player damage path only (players mitigate; NPCs do not gain armor). Locate the tick-engine/consumer site where NPC damage is applied to the character and insert mitigation there — cite the exact site in the closeout.
Tests: naked = unchanged; full Common Mk 1 set (TAV 13) reduces a 28-damage hit to 22 (13/61 = 21.3% → reduction 6); TAV 1 vs a 4-damage hit still saves 1 (floor); a 1-damage hit vs any TAV still deals 1; broken chestpiece drops out of TAV.
Step 4 — The bar law and #110's fix
Fill fraction is invariant under every max-changing mutation: equip, unequip, spend. Implement one shared rescale path used by all three:

* On any change to `vitality_max`/`longevity_max`, current values rescale as `current × new_max ÷ old_max`, rounded to nearest, floored at 1 while the character is alive. Full bars stay exactly full (rescale of max = new max, no drift).
* The mutation must be one atomic database update in the v21 #52 style — a single `.update()` with F-expressions computing the rescaled currents and new maxima together; the consumer never reads-modifies-writes bar or stat fields on a cached object. This is where #110's race dies: equip/unequip-time stat application and the spend path go through this atomic update, not through `setattr` + `save()` on stale objects. Refactor `cmd_spend`'s `apply_spend` and `recalculate_bars`'s callers accordingly (`recalculate_bars` may remain as the max-formula calculator, but the write becomes the atomic update).
* Level-up bar behavior is out of scope — whatever level-up does today, it keeps doing. Only equip/unequip/spend adopt the law in this brief.

Tests: equip END gear at 40% fill → still 40% of the larger bar (rounding to nearest); unequip at full → still full; spend END mid-combat → bigger bar, same fraction, no refill; concurrent effect-expiry + equip cannot lose an update (regression shaped on #110's report).
Step 5 — Procs and the secondary wiring map
5a. The rename (ruled; data only, zero schema)

1. Seed: in `django/src/apps/shyland/management/commands/seed_world.py`, rename every secondary-pool stat key `bleed_chance` → `bleed_factor`, `stun_chance` → `stun_factor`, `poison_chance` → `poison_factor`. No curve values change. (`crit_chance` and `lifesteal` are untouched — their names remain honest under their ruled wirings.)
2. Live-instance fixup: new management command `rename_proc_stats` in the exact `fix_zero_secondary_stats` mold — idempotent; walks every `ItemInstance`'s `rolled_primary_stats` and `rolled_secondary_stats`, renames the three keys in place, reports counts, changes no values. Write it and test it against a local database. Running it against production is a deploy-time, operator-directed action — this brief does not execute it against production.
3. All code written in this brief uses the new names exclusively.

5b. The wiring
Constants (`combat_utils.py`): `PROC_CHANCE_PER_POINT = 0.05`, `PROC_CHANCE_CAP = 0.50`, `PROC_FACTOR_STATS = ('bleed_factor', 'stun_factor', 'poison_factor')`.
On each landed player hit (hit or critical, not graze/miss), after base damage is computed:

1. For each equipped item, for each entry in its rolled stats whose `stat` is in `PROC_FACTOR_STATS` with value V: roll independently against `min(PROC_CHANCE_CAP, V × PROC_CHANCE_PER_POINT)`; on success add `random.randint(1, ceil(V))` to the gear-bonus pool.
2. Add flat `electric_damage_bonus` values (all equipped items) to the pool every landed hit.
3. `crit_chance` rolled values: sum × 0.01 added inside `resolve_hit`'s crit computation, still capped at `CRIT_CAP` (pass the gear crit bonus in; keep the existing signature workable — cite the chosen approach in the closeout).
4. `lifesteal`: after damage lands, heal the attacker by the summed rolled lifesteal values, clamped to `vitality_max`, via an atomic F()-update (consumer-never-RMWs invariant). No output line beyond the bar moving.
5. `spell_damage_bonus`, `mana_regen`, `magic_resist`, `radiation_resist`: wired to nothing. Do not add consumers.

Display: the gear-bonus pool (proc successes + electric), when > 0, renders in the hit line as the parenthetical: `You hit the giant cave spider for 14 (+7) damage.` — base damage first, parenthetical is gear's part, total dealt = base + bonus. Zero pool → today's line byte-identical. Crit composition: `for a critical 14 (+7) damage!` The parenthetical inherits the hit line's existing color; no new palette entries.
Tests: no proc stats → no parenthetical, line unchanged; forced-success proc adds 1..ceil(V) and prints the parenthetical; multiple proc items roll independently and sum; lifesteal heals and clamps; the rename command is idempotent and value-preserving; NPC damage to players never gains procs (player-side only in v22 — NPCs have no equipment).
Step 6 — Stats display
`stats` (and any other surface rendering the six stats) shows base with the gear parenthetical from `gear_stat_bonus`: `STR: 25 (+3)` — parenthetical only when the gear sum is nonzero. Kind 1 key/value rows per the standing display standards; the parenthetical takes value-color with the existing key/value vocabulary (no new colors). Bars elsewhere unchanged.
Tests: no gear → no parentheticals; +3 STR equipped → `(+3)`; unequip → parenthetical gone.
Step 7 — #109's removal
In `cmd_spend` (consumers.py ~line 2240): the bar handling now flows through Step 4's law (bigger bar, same fraction). Remove any refill-moment display line shipped by v22 B2 (the loot-color refill announcement) — the success output is exactly the transactional sentence plus the new value per DD §6. If no such line exists in the current code, record that finding in the closeout and change nothing there.
Test: mid-combat spend into END: fraction preserved, no refill, no refill line in output.
Step 8 — Verification and the budget guard

1. Full suite green, run as `apps.shyland.tests`.
2. All new tests from Steps 2–7 green.
3. Survey-lite re-bless: using the seeded numbers (cite code, #89-survey style), recompute the six Z01 boss fights for the 25/25 reference build wearing full Common Mk 1 armor (TAV 13, 21% mitigation): expected rounds unchanged (player damage is untouched by armor), expected potions from mitigated incoming damage at the blessed hit rates. Record per-boss potion expectations in the closeout. If any boss drops to a zero-potion expected fight, STOP before Step 9 and report — K is an operator ruling. The final boss must still demand potions.

Step 9 — Architecture doc (GATED, last)
This step is gated on all implementation and verification steps above being complete and passing. Update `docs/shyland/Shyland_Architecture_v22.md` in place (no new file, no version bump; the header's commit hash moves — this is an architectural change): the combat section gains effective stats (function, read-site policy), armor mitigation (Option C, the slot-weight table, TAV, the curve and floors), the bar law (fill-fraction invariance, the atomic rescale, #110's fix), proc semantics (the rename, the wiring map, constants, the parenthetical), and the stats-display split; the #109 reversal is noted where spend is documented; the `rename_proc_stats` deploy-time step is noted wherever deploy/reseed steps are documented.
Step 10 — Closeout
Close #100, #109, #110 (gated on Step 8 passing). Write `docs/shyland/Shyland_V22_Brief_5_Closeout_Report.txt`: the read-site classification sweep, the mitigation insertion site, the crit-bonus approach, the #109-line finding, per-boss re-bless numbers, both new issue numbers from 1b, confirmation that `rename_proc_stats` was NOT run against production, any discrepancies, and the final commit hash. Commit and push.
Step 11 — Final instruction
run the issues report
