# Shyland V24.15 Brief 1 — Tier XP Multiplier

**Release:** Version 24.15 (milestone) · **Founding ticket:** #26 (no dependencies) · **Branch:** `version_24_15`
**Phase:** 3 (Mk 2 balance) of the V24 series plan (#139)
**Design authority:** the ruling recorded on #26 (2026-08-08, V24.15 design session) and GDD §3 "Kill XP" (the `(v24.15, pending implementation)` marker), with cross-references in §2 (full-set hunt) and §5.9. This brief is self-contained — implement from this document and the repo only.

## 1. Summary

Kill XP currently derives from NPC level only: `xp_for_kill` pays `int(mk_tier × 10 × scaling_factor)`, then the v18 outleveled decay. A level-3 boss pays the same 30 XP as a level-3 beetle while costing ~5–6.5× the time and ~13× the draughts (#180 survey). This brief adds the ruled combat-tier XP multiplier — **the doubling ladder**:

| `combat_tier` | XP multiplier |
|---|---|
| `normal` | ×1 |
| `elite` | ×2 |
| `champion` | ×4 |
| `boss` | ×8 |
| `world_boss` | ×16 |

Runtime code only — one dict and one function edit in `combat_utils.py`, new tests, arch doc. **No model changes, no migration, no seed changes, no data actions.**

## 2. Standing pre-flight

- **Prior pending deploy-time actions: none outstanding.** V24.14's production seed executed at its closeout tail (`make seed-prod`, deletions 0/0, prod verified at 24.14). This release inherits nothing.
- This brief creates **no** PENDING DEPLOY-TIME ACTIONS. Seed deletions: n/a (no seed run).

## 3. Step 0 — verify-and-signal

Confirm this brief exists verbatim at the branch tip (whitespace-only drift is report-and-accept). Create the closeout report stub `docs/shyland/Shyland_V24.15_Brief_1_Closeout.txt` opening with a one-line session-start record (date, brief name, branch). Commit and **push immediately** — the work-has-started signal.

## 4. Step 1 — version constant (opening act)

First implementation brief of the release: bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` (line 8) from `"24.14"` to `"24.15-DEV"` in **its own commit**, moving the pin test in the same commit (`tests/test_b2_amendment1.py` line 118: `assertEqual(SHYLAND_VERSION, '24.14')` → `'24.15-DEV'`). Then run the version-start `make deploy-dev` from the worktree.

## 5. Step 2 — implementation

All changes in `django/src/apps/shyland/combat_utils.py`.

**5.1** Add the authored ladder next to `NPC_TIER_OFFSET` (~line 41):

```python
NPC_TIER_XP_MULT = {'normal': 1, 'elite': 2, 'champion': 4, 'boss': 8, 'world_boss': 16}
```

**5.2** In `xp_for_kill`, multiply the base by the tier multiplier **before** the outleveled decay:

```python
tier_mult = NPC_TIER_XP_MULT.get(npc_instance.definition.combat_tier, 1)
base = int(npc_instance.mk_tier * 10 * npc_instance.definition.scaling_factor) * tier_mult
```

Everything downstream — `band_top`, `levels_over`, the −20%/level multiplier with its 10% floor, the round-at-9th-decimal correction, `max(1, …)` — is **unchanged**. Update the docstring to record the ladder and the composition order.

**Design rules (deviations from these are report-and-stop, not judgment calls):**

- The ladder values are exactly ×1 / ×2 / ×4 / ×8 / ×16, integers, keyed on the five `COMBAT_TIER_CHOICES` values.
- The multiplier applies to the base, **before** the outleveled decay — the decay multiplies the tier-multiplied base.
- Escorts and adds pay their own tier — no special-casing, no shared-encounter logic.
- Missing/unknown tier defaults to ×1 via `.get(…, 1)`.
- No model field, no migration, no seed change, no new queries (the call site already has `npc.definition` loaded).
- The kill message format is untouched — `(+{xp} XP)` in `run_tick_engine.py` picks up the new number automatically.

## 6. Step 3 — tests

New module `django/src/apps/shyland/tests/test_tier_xp.py`. Construction may follow existing suite patterns (ORM rows or stubs); the assertions below are the contract. **When prose and table disagree, the table is authoritative.**

1. **Ladder shape:** `NPC_TIER_XP_MULT` equals the §1 table exactly; every `NpcDefinition.COMBAT_TIER_CHOICES` key is present (a future sixth tier fails loudly instead of silently paying ×1); in choices order each rung is 2× the previous.
2. **Sentinels and composition** (`xp_for_kill`):

| `combat_tier` | `mk_tier` | `scaling_factor` | char level | expected XP | proves |
|---|---|---|---|---|---|
| normal | 1 | 3.0 | 3 | 30 | ×1 unchanged |
| elite | 1 | 3.0 | 3 | 60 | ×2 |
| champion | 1 | 3.0 | 3 | 120 | ×4 |
| boss | 1 | 3.0 | 3 | **240** | the Matron sentinel (was 30) |
| world_boss | 1 | 3.0 | 3 | 480 | ×16 |
| boss | 1 | 3.0 | 13 | 96 | decay after tier: 240 × 0.4 |
| boss | 1 | 3.0 | 30 | 24 | 10% floor of tier-multiplied base |
| normal | 1 | 0.5 | 30 | 1 | absolute min 1 preserved |

3. **Unknown tier:** a definition with an off-choices `combat_tier` string pays ×1.

## 7. Step 4 — migration

**None.** No model changes. Do not run `makemigrations`.

## 8. Step 5 — verification (gates for issue close and the doc step)

1. Full in-container suite, path form (via `docker exec` in the django container): `python manage.py test apps/shyland/tests` — all pass (543 at branch cut, plus this brief's new tests).
2. `make shell` spot-checks against the dev DB:
   - `NpcDefinition.objects.get(slug='crowned-devourer')` is `combat_tier='boss'`, `scaling_factor=10.0`; `silk-matron` is boss, 3.0.
   - Every distinct `NpcDefinition.combat_tier` value in the DB is a key of `NPC_TIER_XP_MULT` (the `.get` default never fires for seeded content).
3. `git diff` against the Step 1 commit touches only: `combat_utils.py`, `tests/test_tier_xp.py`, the closeout report, and (at Step 8) the architecture doc.

## 9. Step 6 — dev deploy

`make deploy-dev` from the worktree once implementation and verification pass. (Source is baked at build time — no code change is live without it.)

## 10. Step 7 — operator playtest checklist (dev stack)

The standing dev Hollowcrown encounter (Mk 2, respawn 1 minute) is the natural rig; expected values below assume the level-20 test character (in band for Mk 2: band top 20, no decay).

1. Kill the **Crowned Devourer** (Mk 2): the slain line reads **(+1600 XP)** — was 200 (base `int(2 × 10 × 10.0)` = 200, ×8).
2. Kill one **Devourer's drone** (Mk 2, elite, sf 9.0): **(+360 XP)** — was 180 (×2, its own tier — not the boss's ×8).
3. Kill any deeply outleveled Z01 Mk 1 normal: XP unchanged from pre-brief values (×1 tier; the outleveled floor already governs).
4. `stats` — the XP total reflects the awards.

## 11. Step 8 — architecture doc (gated, last)

**This step is gated on all implementation and verification steps above being complete and passing.**

`docs/shyland/Shyland_Architecture_v24.md`, updated in place (point-release rule):

- Header blockquote: new **Version 24.15 (point release)** entry — tier XP multiplier (#26), the ladder, composition before decay, runtime-code-only. **The "as of commit" hash MOVES** to this brief's Step 2 implementation commit (architectural change — runtime code), replacing f001a79.
- §4.5 Combat utilities: the `xp_for_kill` paragraph (~line 703) gains the `NPC_TIER_XP_MULT` ladder, the before-decay composition, the escorts-pay-their-own-tier rule, and the worked Matron sentinel (30 → 240).
- No other sections change. GDD source is not touched (the §3/§2/§5.9 text is already on the branch; marker removal is design/closeout work).

## 12. Closeout

Complete the stub in place: summary, per-step commit hashes, verification results (actual test count), deviations (none expected; record any, never silently), the explicit line "PENDING DEPLOY-TIME ACTIONS: none — no seed or data actions in this release", the final commit hash, and the operator playtest disposition (#170 wording). Close #26 gated on §8 passing. Commit and push at every step boundary; branch only, never merge. End with the `implementation-session-end` ritual (playtest disposition first; issues report unconditional).
