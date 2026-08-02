# Shyland V24.10 — Brief 1: The Proc Floor (#127)

**Founding ticket:** #127 — Ranged proc damage ("between X and Y") — new weapon kind, midpoint-and-spread family
**Milestone:** Version 24.10 · **Branch:** `version_24_10`
**Design authority:** the rulings recorded on #127 (2026-08-02, V24.10 design session — composition (a)–(d), scope (e)–(h), display (i)–(j)) and GDD §6.4 "The proc floor" / §5.4 step 4 / §5.5 (committed 239159a). This brief is self-contained; where prose and a table disagree, **the table is authoritative**.

**Pre-flight note (prior pending actions):** V24.9's pending deploy-time action (production `make seed-prod`) was executed in its closeout tail and verified — there are **no** outstanding pending actions entering this brief.

---

## 1. Version constant — opening act

First commit of the brief, before any other change: `SHYLAND_VERSION` → `"24.10-DEV"`, with the pin-test assertion moved in the same commit. Then run the version-start `make deploy-dev` from the worktree.

## 2. Design rules (binding — no deviation)

1. **The floor is authored, deterministic, rarity-blind.** A definition stat entry may carry the optional pair `floor_base`, `floor_factor`. At drop, floor `X = floor_base + (floor_factor × mk_tier)` — no rarity multiplier, no roll.
2. **The ceiling is the existing rolled factor V, unchanged machinery.** Same `_roll_stat` path, same rarity spread. `Y = X + ⌈V⌉`.
3. **Combat, on proc success: damage = uniform random integer in [X, Y].** Proc **chance is untouched**: `V × 0.05`, capped at 50%.
4. **Unfloored procs keep the shipped `random 1..⌈V⌉` path, byte-identical.** "No floor" is the absence of the keys — never X=0 or X=1 routed through the new formula. Zero behavior or display change for any existing item.
5. **`flame_factor` joins the proc family** as its fourth member — identical wiring to bleed/stun/poison (flavor name only; no status effects, no damage types).
6. **Floors are authorable only on primary-stat proc entries.** A floor pair on a secondary-pool entry, or on a non-proc-family stat, is a **seed defect** — enforced by a seed-time invariant check (§5 below).
7. **Drop-time snapshot:** the instance stores both rolled V and computed X. Held items never change retroactively; only newly generated instances carry floors.
8. **Display, examine:** floored entries render the standard stat line **plus** the promise parenthetical — `Flame Factor: 4.2 (between 12 and 17 damage)` where the range is X and X+⌈V⌉. Unfloored entries render **no** parenthetical, byte-identical to today. No `STAT_LABELS` addition (title-case fallback yields "Flame Factor").
9. **Display, combat:** the hit line changes not at all — floored payouts join the existing single gear-bonus parenthetical (quiet-line law). No new output lines.

## 3. Implementation

All paths repo-relative under `django/src/apps/shyland/`.

### 3.1 Model — no schema change, no migration

`ItemDefinition.primary_stats` / `secondary_stat_pool` and `ItemInstance.rolled_primary_stats` / `rolled_secondary_stats` are `JSONField`s (models.py:455–456, 531–532). The floor pair is two new optional keys on a definition stat-spec entry; the snapshot is one new optional key on an instance entry:

- Definition entry (floored): `{'stat': 'flame_factor', 'base': 2.0, 'factor': 1.0, 'floor_base': 8.0, 'floor_factor': 4.0}`
- Instance entry (floored): `{'stat': 'flame_factor', 'value': <rolled V>, 'floor': <int X>}`

**No model class changes. No migration.** State this in the closeout.

### 3.2 Generation — `item_utils.py`

In `generate_item_instance` (line 94): when a primary stat entry carries `floor_base`/`floor_factor`, compute `X = floor_base + (floor_factor × mk_tier)`, coerce to `int`, and write it as `floor` on the instance's rolled entry alongside `value`. `_roll_stat` is untouched. Secondary-pool entries never receive floors (the seed invariant guarantees none exist; generation must not silently honor one — ignore floor keys on secondary entries).

### 3.3 Combat — `combat_utils.py`

- `PROC_FACTOR_STATS` (line 21) gains `'flame_factor'`: `('bleed_factor', 'stun_factor', 'poison_factor', 'flame_factor')`.
- At the proc roll site (~line 183): entries whose rolled dict carries `floor` pay `random.randint(X, X + ceil(V))` on success; entries without `floor` keep the existing `random.randint(1, ceil(V))` expression **untouched** — two paths, selected by key presence. Chance computation unchanged for both.

### 3.4 Examine display — `consumers.py`

In the item-detail stat rendering (~lines 1752–1763): entries carrying `floor` append ` (between {X} and {X + ⌈V⌉} damage)` to the stat line. Applies wherever those entry dicts render stat lines (primary and secondary loops both — secondaries will never match, by invariant, but the rendering helper should not care which list it's in). All other lines byte-identical.

### 3.5 Seed — `management/commands/seed_world.py`

**Additive only. Expected deletion count: 0.** Two new weapon definitions appended to the weapons block, joining the standard weapon drop pools exactly as the existing eight do (no loot-table or vendor changes).

| Field | **Flame Projector** (`flame-projector`) | **Dart Caster** (`dart-caster`) |
|---|---|---|
| `item_type` | `weapon` | `weapon` |
| `genre_tag` | `wasteland` | `fantasy` |
| `valid_slots` | `['RANGED']` | `['RANGED', 'MAIN_HAND']` |
| `is_two_handed` | `True` | `False` |
| `scaling_base` / `scaling_factor` | 5.0 / 2.0 | 4.0 / 1.8 |
| `damage_spread` | 3.0 | 2.0 |
| `is_ranged` | `True` | `True` |
| `takes_durability_loss` | `True` | `True` |
| `durability_table` | `RANGED_DUR` | `RANGED_DUR` |
| Primary 1 | `{'stat': 'per', 'base': 2.0, 'factor': 0.8}` | `{'stat': 'dex', 'base': 2.0, 'factor': 0.8}` |
| Primary 2 | `{'stat': 'flame_factor', 'base': 2.0, 'factor': 1.0, 'floor_base': 8.0, 'floor_factor': 4.0}` | `{'stat': 'poison_factor', 'base': 2.0, 'factor': 1.0, 'floor_base': 5.0, 'floor_factor': 3.0}` |
| Secondary pool | `per` 1.0/0.4 · `crit_chance` 0.5/0.2 | `dex` 1.0/0.4 · `crit_chance` 0.8/0.3 |

Descriptions: author freely in-session (creative-content policy) — wasteland improvised flamethrower flavor; fantasy hunter's blowpipe flavor. Balance rationale on record (#127): the hot V curve (2.0/1.0 vs the 0.5/0.2 family guideline) is deliberate — ~13–18% Mk 1 proc chance for weapons whose identity is the proc; the guideline governs rider procs, and seed already deviates per-definition (Battle Axe 0.8/0.3, Iron Sword 0.3/0.1).

**Seed invariant (new):** after definitions are ensured, assert no `secondary_stat_pool` entry anywhere carries `floor_base` or `floor_factor`, and no `primary_stats` floor pair sits on a stat outside `PROC_FACTOR_STATS`. Violation aborts the seed with a named error, in the style of the grid-adjacency and octagon-never-agro checks.

## 4. Tests — `tests/`

In-container invocation, path form only: `python manage.py test apps/shyland/tests` via `docker exec` in the django container.

1. **Floor math:** generated floored instance snapshots `floor == floor_base + floor_factor × mk_tier` (int), rarity-independent — same X across all five rarities at fixed Mk; `value` still varies with rarity spread.
2. **Combat range:** floored proc success pays within [X, X+⌈V⌉] inclusive (seeded RNG or repeated-draw bounds assertion); unfloored proc still pays within [1, ⌈V⌉]. Chance formula unchanged (unit-level: the chance expression reads V only).
3. **Byte-identity:** an unfloored weapon's examine output and hit-line rendering are unchanged against current expectations (existing tests keep passing untouched — any literal-pinning test that trips converts per the pool-hygiene rule with intent preserved and a closeout deviation note).
4. **Examine parenthetical:** floored instance's stat line ends `(between X and Y damage)` with the snapshot numbers; secondary lines never carry it.
5. **Seed:** definitions count grows by exactly 2 (invariant arithmetic, not absolute count); both new definitions carry their floored primary per the table; the seed invariant check passes — and a deliberately corrupted in-memory spec (floor on a secondary) is rejected (unit-test the checker function directly).
6. **`PROC_FACTOR_STATS`** contains exactly the four names.

## 5. Execution order

1. Version constant commit + `make deploy-dev` (§1).
2. Code (§3.1–3.4) + tests (§4) — commit and push at every step boundary.
3. Seed changes (§3.5) with invariant check.
4. Full suite green in-container.
5. `make build && make restart` cycle as needed during work (source is baked into the image).
6. **Deploy + data action, code first, data second:** `make deploy-dev`, then `make seed` against the dev stack. Re-verify §4.5's DB assertions after the seed. Reconciliation report must show **0 deletions** (expected 0).
7. Close #127 — gated on all verification above passing.
8. Architecture doc — **last, gated step**: gated on all implementation and verification steps above being complete and passing. Update `docs/shyland/Shyland_Architecture_v24.md` **in place**: stamp → 24.10, **hash moves** (this is an architectural change). Sections: item generation (floor snapshot), combat/proc mechanics (floored payout path, four-member `PROC_FACTOR_STATS`), examine display (promise parenthetical), seed invariants (primary-only floors). Then `make gdd` is NOT run by this session (no GDD source was touched; GDD text landed in design).
9. Closeout report `docs/shyland/Shyland_V24.10_Brief_1_Closeout.txt` completed in place (stub created at Step 0 per the implementation-session ritual), including: final commit hash, actual-vs-expected deletion count (0/0), the no-migration statement, any test-hygiene deviations, the PENDING DEPLOY-TIME ACTIONS block below, and the operator playtest disposition.

## 6. PENDING DEPLOY-TIME ACTIONS (for the closeout tail)

- **Production seed** (`make seed-prod`, bare, on its own operator confirmation, in the closeout tail's deploy window): materializes Flame Projector and Dart Caster definitions in production. **Expected deletion count: 0.** Dev-side execution of the same action happens in-session at §5.6; this block stays open until the production execution at release deploy.

## 7. Operator playtest checklist (dev stack)

After §5.6, on the dev stack:

1. Generate/loot a **Flame Projector** and a **Dart Caster** (admin gift or drops); `examine` each: floored stat line reads `Flame Factor: <V> (between X and Y damage)` / `Poison Factor: <V> (between X and Y damage)`; X = 12/8 at Mk 1 respectively; both weapons show two primary stat lines plus rolled secondaries per rarity.
2. Examine at two different rarities of the same weapon (same Mk): **X identical**, V (and Y) differ — rarity buys ceiling, never floor.
3. Equip and fight: hit lines show only the familiar single parenthetical — no new line types; over a fight, bonus spikes ≥ X appear (the floor paying out).
4. Examine an existing proc weapon (Iron Sword / Battle Axe): stat lines **unchanged**, no parenthetical.
5. Sell/drop/stack behavior on the new weapons: ordinary weapon behavior (never stacks, standard flags).

---

*Written and committed by the V24.10 design session, 2026-08-02. Implementation session: verify this brief at the branch tip (Step 0), then execute in order.*
