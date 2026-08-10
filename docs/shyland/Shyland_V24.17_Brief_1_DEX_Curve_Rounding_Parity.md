# Shyland V24.17 — Brief 1: NPC DEX Curve Rounding Parity (#105)

- **Release:** Version 24.17 (milestone `Version 24.17`) — V24 major, Phase 3 (Mk 2 balance)
- **Founding ticket:** #105 — "Elite even-level −5% hit calibration drift (rounding parity)" (ruling recorded on the issue 2026-08-10)
- **Branch:** `version_24_17` (cut from main at 38b5570, the V24.16 release tip)
- **Shape:** runtime code only — no models, no migration, no seed data, no data actions, **deletions 0**. Architecture-doc hash **MOVES** (architectural point release: contest-math change).
- **Prior pending deploy-time actions:** none — V24.16 closed with zero pending actions; nothing carries into this release.

This brief is self-contained. Everything the implementation session needs is in this file and the repo.

---

## 1. Problem

`get_npc_stats` (in `django/src/apps/shyland/combat_utils.py`) derives NPC DEX — the difficulty dial for all opposed rolls — from the player-matching curve:

```python
curve = round(NPC_CONTEST_BASE + NPC_CONTEST_STEP * (L - 1))   # 18 + 2.5/level
```

Python's built-in `round()` is banker's rounding (round-half-to-even). The calibration's reference player accrues the **floor-share** of 2.5 DEX per level (5 stat points per level split across two primaries), i.e. attainable primary = `18 + floor(2.5 × (level − 1))`. The two disagree exactly where banker's rounds the `.5` levels **up**:

| Within-band level | Curve value | Banker's | Player floor-share | Drift |
|---|---|---|---|---|
| L2 | 20.5 | 20 | 20 | aligned |
| L4 | 25.5 | **26** | 25 | **−5% hit** |
| L6 | 30.5 | 30 | 30 | aligned |
| L8 | 35.5 | **36** | 35 | **−5% hit** |
| L10 | 40.5 | 40 | 40 | aligned |

(Odd levels land on integers — always aligned.) 1 DEX = one d20 pip = 5% hit. Mk-band lifts add `10 × 2.5 = 25` per band — an integer — so the pattern repeats identically in every band. This is survey finding G5 (#89); the architecture doc's "blessed targets exact and constant at every level" claim is overstated by exactly this amount at L4/L8.

## 2. The ruling (design rules — do not deviate)

1. **Floor the growth term:** the curve becomes `NPC_CONTEST_BASE + floor(NPC_CONTEST_STEP × (L − 1))` — floor applied to the growth term, mirroring the player's own floor-share accrual. NPC DEX then equals the reference build's attainable at-level primary at **every** level of **every** band; blessed at-level hit targets (55% normal / 45% elite / 45% boss) are exact everywhere.
2. **DEX curve only.** The `growth = round(NPC_CONTEST_STEP * (L - 1))` line for STR/PER/INT is **untouched** — its banker's-rounding ±1 artifacts were explicitly ratified by v19 Brief 7 Amendment 1 (damage-side noise, no hit% effect). Do not "fix" it.
3. `npc_max_vitality`'s HALF-UP rounding (#104) and its comment are **untouched**.
4. Constants `NPC_CONTEST_BASE = 18`, `NPC_CONTEST_STEP = 2.5`, `NPC_TIER_OFFSET = {'normal': 0, 'elite': 2, 'boss': 2}` are **untouched**.
5. **Sentinel:** elite L4 (scaling_factor 4.0, Mk 1) DEX 28 → **27**; elite L8 38 → **37**. Aligned levels are byte-identical pre/post (normal L2 = 20, L6 = 30, L10 = 40, all odd levels).

## 3. Implementation

### Step 1 — Version constant (opening act, own commit)

First implementation brief of the release: in `django/src/apps/shyland/version.py`, bump `SHYLAND_VERSION` from `"24.16"` to `"24.17-DEV"`. The pin test moves in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py` (the `assertEqual(SHYLAND_VERSION, '24.16')` assertion, currently line 118) changes to `'24.17-DEV'`. Commit, then run the version-start `make deploy-dev` from the worktree.

### Step 2 — The curve fix

In `django/src/apps/shyland/combat_utils.py`, inside `get_npc_stats` (currently line 383):

```python
# before
curve = round(NPC_CONTEST_BASE + NPC_CONTEST_STEP * (L - 1))
# after
curve = NPC_CONTEST_BASE + math.floor(NPC_CONTEST_STEP * (L - 1))
```

`math` is already imported (line 1). Update the `get_npc_stats` docstring to state that the floor on the growth term mirrors the reference player's floor-share DEX accrual, making the blessed targets exact at every level (v24.17, #105). No other line in the function changes.

### Step 3 — Tests

New file `django/src/apps/shyland/tests/test_dex_parity.py` (construct `NpcDefinition`/`NpcInstance` following the existing pattern in `tests/test_npc_hp_scaling.py`). Pins, all as exact equality assertions:

1. **The curve law:** for every `mk_tier` in (1, 2, 3) × `scaling_factor` in 1–10 × `combat_tier` in ('normal', 'elite', 'boss'): `get_npc_stats(...)['dex'] == 18 + math.floor(2.5 * (L - 1)) + NPC_TIER_OFFSET[tier]`, where `L = scaling_factor + 10 * (mk_tier - 1)`.
2. **Player parity:** for level Λ in 1–30, a normal-tier NPC at effective level Λ has DEX exactly equal to the reference player's attainable primary `18 + math.floor(2.5 * (Λ - 1))`.
3. **Blessed targets exact:** for every level 1–30 and tier: with player DEX = the attainable primary, the to-hit threshold `TO_HIT_DEFENSE_BASE (10) + npc_dex − player_dex` yields hit chance exactly 55% (normal) / 45% (elite) / 45% (boss) — i.e. threshold 10 / 12 / 12, success faces `21 − threshold` of 20.
4. **Sentinels:** elite scaling_factor 4.0 Mk 1 → DEX **27**; elite scaling_factor 8.0 Mk 1 → DEX **37**.
5. **Surgical-fix pins (unchanged values):** normal Mk 1 at scaling_factor 2.0 → 20, 6.0 → 30, 10.0 → 40 (the levels banker's already got right).

No existing test pins the DEX curve numerically (grep-verified at design time: no `NPC_CONTEST` references and no `['dex']` curve assertions in `tests/` beyond gear-bonus math) — expect **zero test conversions**. If one surfaces anyway, convert it with intent preserved and record a deviation in the closeout.

### Step 4 — Full suite

In-container, the only working form:

```
docker exec <django container> python manage.py test apps/shyland/tests
```

Suite was 553/553 at the V24.16 stamp; expect 553 + (new tests in `test_dex_parity.py`), all passing. Invariant: count grows by exactly the new file's tests.

### Step 5 — Dev deploy

`make deploy-dev` from the worktree once implementation and verification pass. Dev-side data actions: none.

## 4. Verification

1. New test file passes; full suite passes at the expected count.
2. Shell spot-check (dev container, Django shell): an elite NPC instance at scaling_factor 4.0, Mk 1 reports `get_npc_stats(...)['dex'] == 27`; at Mk 2 (effective L14, curve 18 + floor(32.5) = 50) reports `52`.
3. Grep-check: `combat_utils.py` contains exactly one `math.floor` in `get_npc_stats` and the `growth` line still reads `round(`.

## 5. Architecture doc (LAST, gated)

This step is gated on all implementation and verification steps above being complete and passing. `docs/shyland/Shyland_Architecture_v24.md`, updated in place:

- Header stamp → **24.17**; the header hash **MOVES** to the release's code commit (architectural point release — contest-math change); the header blockquote gains the v24.17 brief-1 note in the established running style.
- **§4.5 Combat utilities:** the NPC contest-stats paragraph — the DEX derivation changes from `round(curve)` to `curve = 18 + floor(2.5 × (L − 1))`; the "blessed at-level hit targets exact and constant across every level and Mk tier" sentence now holds without the #105 caveat; note the floor mirrors the reference player's floor-share accrual and that STR/PER/INT growth deliberately keeps its Amendment-1 `round()`.

## 6. Playtest checklist (dev stack)

The change's surface is statistical (a 5% hit-rate shift at two levels per band); there is no crisp hand-playtest. Offered for completeness:

- [ ] At a level-4-equivalent character on dev, engage an at-level elite and observe hit rate over an extended exchange (~45% expected, was ~40%).

**"No playtests for this brief" is an acceptable disposition** — the operator's call, recorded verbatim in the closeout report.

## 7. Closeout report requirements

`docs/shyland/` `.txt` per standing process: final commit hash, operator playtest disposition, deviations (expected: none), deletions actual vs expected (**0/0**), pending deploy-time actions (**none**), suite count. Issue #105 is closed by the implementation session, gated on verification passing.
