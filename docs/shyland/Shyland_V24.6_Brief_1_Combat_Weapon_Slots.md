# Shyland V24.6 Brief 1 — Combat Weapon Slots: The Composite Strike

- **Release:** Version 24.6 (milestone `Version 24.6`)
- **Branch:** `version_24_6`
- **Founding ticket:** #177 (combat ignores weapon slots — dual-wield contributes nothing)
- **Dependency (settled by this same brief):** #178 (Ranged-slot semantics)
- **Design authority:** operator-confirmed rulings recorded on #177 and #178 (2026-08-02, V24.6 design session); GDD text landed in commit 323cc50 (§5.4 step 2, §3.6 Ranged-slot paragraph, §6.4 composite sentence — all carrying `(v24.6, pending implementation)` markers, which this brief does NOT touch; marker removal is design/closeout work)
- **This is the FIRST implementation brief of the release** — it carries the version-start opening act.

This brief is self-contained. Everything needed is in this document, the repo, and the two issues' ruling comments. No design decisions remain; deviations from the rules below require stopping and reporting, not improvising.

---

## 1. What ships

Combat currently selects the attacking weapon as `equipped_weapons[0]` (`run_tick_engine.py` player-attack path): only one equipped weapon ever supplies base damage and the stat bonus, chosen by queryset ordering. This brief replaces that with the **composite strike**: every equipped, non-broken weapon contributes to one strike per round.

**The model (operator-confirmed; GDD §5.4 as amended):**

1. **One hit roll per round, unchanged** (`resolve_hit`). A miss remains one miss line.
2. **Primary weapon** = the occupant of the highest-priority weapon slot, priority **`MAIN_HAND` → `RANGED` → `OFF_HAND`**. A bow-only or off-hand-only loadout fights at full strength.
3. **Weapon term** = Σ over equipped, non-broken weapons `w` of `factor_w × (damage_roll_w + stat_w) × dur_w`, where:
   - `damage_roll_w` = uniform within `w`'s `damage_midpoint ± damage_spread` (per weapon, as the single-weapon path does today);
   - `stat_w` = `w`'s own governing effective stat — effective STR if `w.definition.is_ranged` is False, effective DEX if True;
   - `dur_w` = `1.0 − get_durability_penalty(w)` (per weapon);
   - `factor_w` = **1.0 for the primary**, else the slot factor: **`OFF_HAND` 0.5, `RANGED` 0.5**.
4. **Acuity modifier and the graze/crit multiplier apply once, to the composite** — exactly as they apply to the single weapon today (including the focus-target-only rule for the above-band bonus and the minimum-1 floor).
5. **Procs, lifesteal, and gear crit-chance are UNTOUCHED** — `roll_gear_bonus_damage` already iterates all equipped items at full strength; no slot factor is applied to any of it.
6. **Unarmed path untouched** — no equipped, non-broken weapon means the existing unarmed branch runs byte-identically (base `uniform(1, 3)`, STR bonus, durability 1.0, unarmed message pools).
7. **Output stays one sentence** — the existing hit-line composition (`You hit X for N damage.` / crit variant / gear parenthetical) is unchanged in shape; only the number grows. NPC-side combat is untouched.

**Ranged-slot semantics (#178, no code change required):** the Ranged slot means "at the ready." The current equip resolver's behavior — a two-hander claims both hands from any slot it occupies; the RANGED slot itself is never claimed by hand logic; a one-handed ranged weapon equips into RANGED alongside anything — is **confirmed correct as built**. This brief must NOT change the equip resolver. The ranged weapon's participation in every round's composite strike is what makes the ruling real.

## 2. Design rules — do not deviate

- One hit roll per round; one output line per player attack; no per-weapon breakdown in output.
- Broken weapons (`is_broken` or 0% durability) contribute nothing (the existing exclusion already filters `is_broken`; keep its semantics).
- The slot factors and priority order are **named module-level constants in `combat_utils.py`** (the tunable-constants convention: `TO_HIT_DEFENSE_BASE` et al.), e.g. `PRIMARY_WEAPON_SLOT_PRIORITY = ('MAIN_HAND', 'RANGED', 'OFF_HAND')` and `SECONDARY_WEAPON_SLOT_FACTOR = {'OFF_HAND': 0.5, 'RANGED': 0.5}`. Phase 3 (Mk 2 balance) retunes the values; the code must make that a constants edit.
- If a weapon somehow occupies a slot not in either constant (defensive case), treat its factor as the secondary default 0.5 — never crash the tick engine over a slot name.
- No model changes, **no migrations**, no seed-data changes, no client changes.
- All ORM access from async context stays behind the existing `@database_sync_to_async` / prefetch patterns — the attack path already has `equipped_all` in memory; do not add per-round queries.

## 3. Implementation steps

**Step 1 — version-start opening act (standing requirement, first brief of the release):**
1. In `django/src/apps/shyland/version.py`: `SHYLAND_VERSION = "24.5"` → `"24.6-DEV"`.
2. Move the pin test with it in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py` line ~118, `assertEqual(SHYLAND_VERSION, '24.5')` → `'24.6-DEV'`.
3. Commit (own commit), push, then run `make deploy-dev` from the worktree (version-start deploy).

**Step 2 — composite-strike helper (`django/src/apps/shyland/combat_utils.py`):**
- Add the two constants above.
- Add a helper (suggested name `composite_weapon_term(weapons, eff_str, eff_dex)`) that: selects the primary by slot priority (first occupied slot in `PRIMARY_WEAPON_SLOT_PRIORITY` order; among the passed weapons, each occupies `item.equipped_slot`), computes the per-weapon terms per §1.3 above, and returns the summed term (float). Rolling stays in this helper so tests can patch randomness the same way existing damage tests do.

**Step 3 — tick-engine integration (`django/src/apps/shyland/management/commands/run_tick_engine.py`, player-attack path ~lines 444–476):**
- Keep the existing `equipped_weapons` filter (weapon type, not broken).
- Replace the `weapon_item = equipped_weapons[0]` selection and the single-weapon `base_damage`/`stat_bonus`/`dur_mod` computation: when `equipped_weapons` is non-empty, compute the weapon term via the Step 2 helper and feed it through the existing `calculate_damage` call as `base_damage` with `stat_bonus=0` and `durability_mod=1.0` (stat and durability are now inside the per-weapon terms; acuity/hit-multiplier/floor logic is thereby reused unchanged).
- The armed/unarmed branch condition (`if weapon_item:` at both the damage site and the flavor-text site) becomes "any equipped, non-broken weapon" — armed flavor with one or more weapons, unarmed pool only with zero.
- The unarmed `else` branch stays byte-identical.

**Step 4 — tests (`django/src/apps/shyland/tests/`, new file `test_v24_6_brief1.py`):**
Minimum coverage, all with patched randomness where rolls are involved:
1. Primary selection: MAIN_HAND occupant is primary over RANGED and OFF_HAND; RANGED over OFF_HAND; sole off-hand weapon is primary at factor 1.0.
2. Composite math: main-hand + off-hand + ranged loadout produces `1.0×main + 0.5×off + 0.5×ranged` (each term `(roll + own stat) × own durability`); ranged weapon's term uses DEX, melee terms use STR.
3. Per-weapon durability: a damaged off-hand weapon reduces only its own term.
4. Broken weapons contribute nothing; a broken primary means the next slot in priority is primary.
5. Two-hander + ranged (`Battle Axe` + `Pulse Pistol` shape): both contribute; axe is primary.
6. Unarmed path unchanged when zero weapons equipped.
7. Unknown-slot defensive default does not crash and uses factor 0.5.

**Test hygiene:** any existing test pinning single-weapon damage output must convert with original intent preserved as explicit assertions — reported as a deviation in the closeout, never changed silently.

**Step 5 — verification (gate for everything after it):**
- Full suite in-container, the only working form: `python manage.py test apps/shyland/tests` via `docker exec` in the django container. All tests pass, including the new file.

**Step 6 — close the issues (gated on Step 5 passing):** close #177 and #178 with closing comments referencing this brief and the final implementation commit.

**Step 7 — architecture doc (LAST, gated).** This step is gated on all implementation and verification steps above being complete and passing. Update `docs/shyland/Shyland_Architecture_v24.md` **in place**:
- §4.5 (Combat utilities): document the composite-strike helper, the two constants, and the reuse of `calculate_damage` (weapon term as `base_damage`).
- §4.9 (Tick Engine): rewrite the player-attack weapon-selection description — `equipped_weapons[0]` is retired; primary-by-slot-priority + secondary factors.
- Header: stamp to **24.6**; the hash **moves** to this release's implementation commit (this is an architectural change).

**Step 8 — dev deploy + closeout report:**
- `make deploy-dev` from the worktree.
- Complete the closeout-report stub in place (`.txt` in `docs/shyland/`): final commit hash, deviations, test counts, and the **operator playtest disposition** line (required before the session can end).
- **PENDING DEPLOY-TIME ACTIONS: none.** This brief has no seed reruns, no data actions, no migrations — state that explicitly in the closeout report.

## 4. Operator playtest checklist (dev stack, after Step 8's deploy)

The Pulse Pistol has no world acquisition path (#178 — deliberate; zone content). Obtain test weapons via the admin/sudo route or the `stock-playtest-items` skill before starting.

1. Equip Iron Mace (Main hand) only; fight a Convergence-adjacent Z01 NPC; note typical hit numbers.
2. Add Combat Knife (Off hand): hit numbers rise noticeably (~half a knife's contribution); output remains one line per hit, no new message shapes.
3. Add Pulse Pistol (Ranged): numbers rise again — the triple loadout visibly compounds ("knife, mace, pistol hits hard").
4. Swap to Battle Axe (two hands) + Pulse Pistol: equip succeeds (both hands consumed + pistol at the ready), and the pistol adds on top of axe hits.
5. Equip Hunting Bow alone: full-strength attacks (bow is primary from RANGED), damage stat is DEX-driven.
6. Unequip everything: unarmed combat reads exactly as before.
7. Miss a few times (low-level character vs. higher NPC if needed): one miss line, unchanged.
8. Confirm crits still land and read as before, gear proc parentheticals still appear.

## 5. Out of scope

- #176 (paper-doll consumed-hands display) — separate ticket, not in this milestone.
- Equip-resolver changes of any kind (#178 confirms current behavior).
- Slot-factor tuning beyond the 0.5 first-pass values (Phase 3).
- GDD source edits, including the three `(v24.6, pending implementation)` markers (design/closeout work).
- Pulse Pistol acquisition path (zone content, V25 era).
