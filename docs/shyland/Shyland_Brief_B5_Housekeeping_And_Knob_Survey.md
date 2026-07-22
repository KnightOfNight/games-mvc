Shyland Brief — B5 Housekeeping and Knob Survey
Type: ops/research brief (zero code changes; does not count against the v22 brief cap) Branch: the current Version 22 worktree branch — this brief runs in the v22 worktree used for all v22 development, mines that branch's code and the production database, and commits to that branch as all v22 work has Version context: Version 22, bucket B5 (gear combat wiring, #100)
This brief does three things, in strict order: (1) records the confirmed B5 ruling set on its issues, (2) files two new issues, (3) surveys the code and production database to produce the machine-readable dataset the armor knob-tuning session will run against. No game code, seed data, or documents other than those named below are touched. Nothing is ever deleted or pruned.
Standing rules

* Work in the Version 22 worktree, on its branch. Commit and push the branch at every step boundary — branch only, NEVER merge to main; merging is the operator's action. WIP-sized commits are fine.
* Read-only against production data. Every database interaction in this brief is a query. If any step appears to require a write to game tables, STOP — that is a defect in this brief. (The only writes are: this brief file, the two `gh issue create` calls, issue comments, the survey JSON, and the closeout `.txt`.)
* Never remove, prune, or clean up any transient document. The operator does all pruning.
* If any repo fact contradicts this brief, stop and record the contradiction in the closeout rather than improvising.

Pre-flight

1. Confirm you are in the Version 22 worktree, the working tree is clean, and the branch is up to date with its remote tracking branch.
2. Verify `DOCKER_HOST` is set and points at the production host; confirm by listing running containers and identifying the Postgres and Django containers for the games stack. The production database is reachable only via `DOCKER_HOST`. If `DOCKER_HOST` is unset or the containers are not visible, STOP and report — do not proceed to Step 3's database queries with a local or partial database.
3. Confirm `gh` is authenticated (`gh auth status`) and can see `KnightOfNight/games-mvc` issues.

Step 0 — Self-commit this brief
Save this brief's full text verbatim to `docs/shyland/Shyland_Brief_B5_Housekeeping_And_Knob_Survey.md` (skip the write if an identical file already exists). Commit on the worktree branch and push the branch immediately — the push is the operator's signal that work has started.
Step 1 — Housekeeping: record the B5 rulings on their issues
Post the following comments. Each comment body is given in full; post them verbatim. These rulings were made in the B5 design sessions and are confirmed by the operator — do not re-litigate, editorialize, or annotate them.
1a. Comment on issue #100 (gear combat wiring)

```
B5 design rulings — confirmed by the operator (recorded from the B5 design sessions):

1. SCOPE LAW (governs the whole bucket): fix what exists so it works the way a
   reasonable player assumes it does; build nothing for absent future systems;
   leave no landmines for them either. Wire only what combat already reads.
   Nothing is invented for INT/WIS/PER's future systems — their gear bonuses
   add to the stat like any other (+N rule below); systems that read those
   stats read the boosted value; no new consumers are created.

2. +N MEANS +N: a stat bonus on any equipped item adds flatly to the stat via
   one effective-stat function (base + gear), read everywhere the stat is read
   — hit, damage, carry, derived values, all of it.

3. STATS DISPLAY: the stats sheet shows the paid-for base with gear's
   contribution in parentheses — `STR: 25 (+3)`. Parenthetical present only
   when nonzero.

4. BAR LAW: fill fraction is invariant under ALL max-changing mutations —
   equip, unequip, and stat spend alike. The bar grows or shrinks; the
   percentage holds; nothing refills. Implementation notes captured with the
   ruling: the proportional rescale (current × new_max ÷ old_max) must be one
   atomic single-F()-expression update in the v21 #52 style — this is exactly
   where #110's stat-field race gets fixed; rounding is to nearest with a
   floor of 1 while alive, so no rescale ever kills by arithmetic.

5. ARMOR — OPTION C (derived base + resist on top, no schema change):
   Total Armor Value (TAV) = Σ(slot weight × Mk tier, over worn armor pieces)
   + Σ(rolled physical_resist). Even Common armor works; rarity means
   "better at armoring," never "allowed to armor." The slot-weight table
   lives in code (same species as SLOT_ORDER) and retires gracefully if real
   per-item armor fields ever ship. Damage taken is reduced by a percentage
   tied to TAV, with floors in both directions (armor never does nothing;
   no hit is ever reduced to nothing).

   STILL OPEN (the bucket's last conversation): the knob numbers — slot
   weights, the mitigation curve constant, and the floors — plus the
   power-target/budget re-bless question. A knob survey (see the research
   issue filed alongside this comment) grounds that session in real data.

Proc semantics rulings are recorded on #68; the #109 reversal on #109; the
race-fix location on #110.

```

1b. Comment on issue #68 (proc stats)

```
B5 ruling — proc semantics (the half deferred out of v21), confirmed by the
operator:

WIRED, minimal honest version. On each landed hit, each equipped proc item
rolls its chance separately (per-item rolls are cheap; combat's budget won't
notice). On success, the item contributes bonus damage with "up to N"
semantics — damage = 1 to N off the power stat. Successes from multiple items
SUM into a single bonus. No damage types, no elemental mechanics, no flavor
field — damage type is not modeled at all in v22.

DISPLAY: no separate proc announcement. The proc bonus folds into the hit
line using the same parenthetical grammar the stats sheet adopted:
`You hit the giant cave spider for 14 (+7) damage.` No proc fired → no
parenthetical; the quiet hit line stays byte-identical to today. Crits
compose naturally: `for a critical 14 (+7) damage!` — base crit math and the
proc bonus keep separate books.

DEFERRED: min–max ranged procs ("between 10 and 20 damage") — a floor is a
second number per proc, which is a generation + stat-table + display +
rolled-stat structure change. Ruled a new weapon kind in the
midpoint-and-spread family; filed thin and unmilestoned (see the deferral
issue filed alongside this comment).

```

1c. Comment on issue #109 (mid-combat spend-refill)

```
B5 ruling — #109 closed by unification, confirmed by the operator. This
REVERSES the standing triage ruling:

The "bankable free heal" is dead. Spending a stat point mid-combat does not
refill the bars. Spend obeys the same bar law as equip/unequip: fill
fraction is invariant under every max-changing mutation — spending into END
gives a bigger bar at the same percentage, no heal. One law, no special
cases, exploit-proof by construction.

What survives on purpose: spend remains legal in combat per the state matrix
— still a legitimate mid-fight move, now an honest one (bank STR for damage,
bank END for the bigger pool going forward — not for a heal).

What dies with the reversal: the B2-shipped loot-color refill display line
must be REMOVED by the B5 implementation brief — there is no refill moment to
announce. Spend's success line stays the standard sentence plus the new
value.

Operator-confirmed disposition: this issue stays OPEN under Version 22 / B5
until the B5 implementation ships the removal; it closes with the
implementation brief, not with this housekeeping.

```

1d. Comment on issue #110 (apply_stat_effect stat-field race)

```
B5 ruling — fix location confirmed by the operator: #110's race is fixed
inside the B5 effective-stat / equip-mutation work. The bar-law rescale
(current × new_max ÷ old_max) is implemented as one atomic
single-F()-expression update in the v21 #52 style; equip-time stat
application is the racing path and gets the same discipline. Rounding to
nearest, floor 1 while alive. Rides bucket B5 with #100.

```

1e. Milestone consistency check (idempotent)
Check #110's milestone. If it does not currently carry milestone `Version 22`, set it (`gh issue edit 110 --milestone "Version 22"`); if it already does, no action. Record which case applied in the closeout.
Commit any working-tree changes (there should be none from this step) and push.
Step 2 — File two issues
Capture both issue numbers at runtime from the `gh issue create` output.
2a. Range-floor proc deferral (thin, unmilestoned)

* Title: `Ranged proc damage ("between X and Y") — new weapon kind, midpoint-and-spread family`
* Labels: none required (do not add `bug`)
* Milestone: none
* Body:


```
Deferred out of v22 B5 by operator ruling. v22 wires "up to N" procs (damage
= 1 to N off the power stat). A proc floor — "between 10 and 20 flame
damage" — is a second number per proc: generation changes, stat-table
changes (GDD §5), display composition, rolled-stat structure. That is a new
weapon kind and should copy the weapons midpoint-and-spread pattern when a
future itemization version picks it up. Ruling recorded on #68.

```

2b. Founding research issue for the knob survey (milestoned)

* Title: `B5 knob survey — armor/proc tuning dataset from code and production DB`
* Labels: none required
* Milestone: `Version 22`
* Body:


```
Founding issue for the B5 knob-survey research brief
(docs/shyland/Shyland_Brief_B5_Housekeeping_And_Knob_Survey.md). Zero code
changes. Produces docs/shyland/Shyland_V22_B5_Knob_Survey.json — the
machine-readable dataset (equip slots, armor definitions and rolled-stat
distributions, combat NPC numbers, player-side constants, every figure
source-cited) that grounds the armor knob-tuning session (slot weights,
mitigation curve, floors) and the Q4 budget re-bless. Prior knob numbers
were derived during a sandbox outage from conversation data; this survey
replaces them with code-cited fact.

```

Comment on this new issue after the survey commits (Step 3), noting the survey file path and the commit hash that introduced it. Then close it — closure is gated on the survey JSON being committed and pushed.
⛔ HARD GATE
Before proceeding past this point: verify both issues exist exactly as specified (title, body, labels, milestone) via `gh issue view`. Any deviation in creation or verification — wrong milestone, failed create, duplicate detection, anything — means: STOP, run the issues report, write the closeout explaining what happened, make zero further changes. Do not proceed to Step 3 on a deviated state.
Commit and push (the brief file may be the only tracked change so far; that is fine).
Step 3 — The knob survey
Goal: one committed JSON file the design chat can parse and trust: `docs/shyland/Shyland_V22_B5_Knob_Survey.json`.
Sources: the code as checked out in the Version 22 worktree (cite repo-relative file paths) and the production database via `DOCKER_HOST` (cite the exact ORM query or SQL used). Every figure in the JSON carries a `source` — a file path for code-derived facts, a query string for DB-derived facts. Prefer `manage.py shell` inside the production Django container for ORM queries.
Known reference points (verify, do not trust blindly — if the code disagrees with any of these, the code wins and the discrepancy goes in the closeout):

* Equip slots: `SLOT_ORDER` and `SLOT_CAPACITY` in `django/src/apps/shyland/consumers.py` (13 slot names; `RING` capacity 2 → 14 slots).
* Item models: `ItemDefinition` (`item_type`, `valid_slots`, `scaling_base`, `scaling_factor`, `secondary_stat_pool` — entries shaped `{'stat': ..., 'base': ..., 'factor': ...}`, `suppress_mk_suffix`) and `ItemInstance` (`mk_tier`, `rarity`, `rolled_primary_stats`, `rolled_secondary_stats`, `is_equipped`, `equipped_slot`, `durability_current`, `owner`) in `django/src/apps/shyland/models.py`.
* NPC models: `NpcDefinition` (`combat_tier`, `base_vitality`, `base_str`/`base_dex`/`base_end`/`base_int`/`base_wis`/`base_per`, `scaling_factor`, `is_aggressive`, `attackable`, `is_unique`) and `NpcInstance` (`mk_tier`, `vitality_max`) in the same file.
* Combat math: `django/src/apps/shyland/combat_utils.py` — `resolve_hit` (d20 + DEX vs `TO_HIT_DEFENSE_BASE` + defender DEX; crit floored `CRIT_BASE`, capped `CRIT_CAP`, slope `CRIT_PER_DEX_ADVANTAGE`; `GRAZE_WINDOW`), `calculate_damage` (graze ×0.5 / hit ×1.0 / critical ×1.5, minimum 1), `npc_level` (`scaling_factor + MK_LEVEL_SPAN × (mk_tier − 1)`), `get_npc_stats` (`NPC_CONTEST_BASE`, `NPC_CONTEST_STEP`, `NPC_TIER_OFFSET`), `recalculate_bars` (`vitality_max = stat_end × 10 + stat_str × 3 + level × 5`).

JSON structure (top-level keys; within each, exact shape is CC's judgment so long as every figure is cited and the content below is present):

1. `meta` — generation timestamp, the worktree branch name and HEAD commit hash the code facts were read at, a note identifying the production DB as the data source.
2. `equip_slots` — the slot list, capacities, and total slot count; plus, per slot, which `item_type`s can occupy it as derived from the union of `valid_slots` across all `ItemDefinition`s (this settles which slots actually carry armor — the proposed 8-slot weight table must be checked against reality, not assumed).
3. `armor_definitions` — every `ItemDefinition` with `item_type='armor'`: slug, name, `valid_slots`, `scaling_base`/`scaling_factor`, full `secondary_stat_pool` (flagging `physical_resist` presence and its curve), `suppress_mk_suffix`.
4. `secondary_stat_census` — across ALL item definitions (every `item_type`): the full vocabulary of `secondary_stat_pool` stats with, per stat, the count of definitions carrying it by item_type and the set of distinct base/factor curves. (Expected vocabulary from a prior read: `str dex end int wis per physical_resist magic_resist radiation_resist crit_chance bleed_chance stun_chance poison_chance lifesteal spell_damage_bonus electric_damage_bonus mana_regen` — verify and correct.)
5. `rolled_distributions` — across live `ItemInstance` rows in production, grouped by rarity and item_type: instance counts, and per stat appearing in `rolled_primary_stats`/`rolled_secondary_stats`, the min/mean/max rolled value; separately for equipped instances. This gives the real `physical_resist` and stat-bonus mass the armor formula will actually multiply.
6. `combat_npcs` — every `NpcDefinition` with `attackable=True` that participates in combat: slug, name, `combat_tier`, `base_vitality`, base stats, `scaling_factor`, and per live-instance Mk tier present in production: effective level (`npc_level`), effective stats (`get_npc_stats`), `vitality_max`, and expected damage per landed hit and per round against a reference defender — computed exactly the way the tick engine computes NPC damage (cite the code path; use the v21-blessed hit rates 55%/45%/45% by tier in the per-round expectation, #89-survey style). If the NPC damage path reads any constant or pool not listed above, capture and cite it.
7. `player_constants` — `TO_HIT_DEFENSE_BASE`, `CRIT_BASE`, `CRIT_CAP`, `CRIT_PER_DEX_ADVANTAGE`, `GRAZE_WINDOW`, hit multipliers, `NPC_CONTEST_BASE`, `NPC_CONTEST_STEP`, `NPC_TIER_OFFSET`, `MK_LEVEL_SPAN`, the `vitality_max` formula, the acuity damage-modifier bounds, and the healing-consumable table: every consumable `ItemDefinition` that heals (slug, name, heal amount via its effect definition/components, `base_value`), cited to seed/effect code or DB.

Commit the JSON and push. Then post the completion comment on the research issue (Step 2b) and close it.
Step 4 — Closeout
Write a closeout report as a `.txt` in `docs/shyland/` (name it `Shyland_Brief_B5_Housekeeping_And_Knob_Survey_closeout.txt`). It must include: what was posted (the four comments), the #110 milestone case that applied (1e), the two new issue numbers, any discrepancies between this brief's reference points and the code, any DB anomalies encountered, and the final commit hash. Commit and push.
Step 5 — Final instruction
run the issues report
