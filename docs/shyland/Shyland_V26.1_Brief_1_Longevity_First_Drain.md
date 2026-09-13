# Shyland V26.1 Brief 1 — Longevity First Drain

- **Release:** Version 26.1 (milestone `Version 26.1`; founding and sole ticket **#70**)
- **Branch:** `version_26_1` (work in its worktree; this is the release's FIRST implementation brief)
- **Design provenance:** rulings on #70 — the 2026-09-11 V26.0-session ruling set as amended by the 2026-09-13 V26.1-session comments (regen blessing + regime rule, flee gate mechanics, the potion superseded to the draught mirror, carts confirmed, stop-at-full derived). The GDD §4 rewrite and §9 additions landed GDD-first at commit `83908e1` on this branch.
- **Self-contained:** implement from this brief and the repo only. Where this brief and the GDD text differ in wording, the GDD is the design source and this brief is the build spec; where a data table below and prose disagree, **the table is authoritative**.

## What ships

Longevity's first consuming mechanic and its support structure, per the three-tanks doctrine (fuel gates, never scales):

1. **Flee exertion:** a contested flee attempt costs 25% of `longevity_max`; below the cost the attempt is refused, free.
2. **Regen retune with regime rule:** `LONGEVITY_REGEN_SECS` 3600 → 900; interval form below the constant, vitality-style per-tick form at or above it.
3. **The Stamina Potion:** Longevity's restorative consumable, an exact Healing Draught mirror (percent-of-max, Mk-scaled, 15 cp), via a new `restore_longevity_percent` component type. Stop-at-full mirrors the draught's rule.
4. **Display reorder:** the stats pane renders Vitality, Longevity, Acuity.

## Design rules — do not deviate

- **Cost:** `ceil(longevity_max / 4)`, charged on every **contested** flee attempt — success, failure, and nowhere-to-run alike (all three are post-contest outcomes; the attempt is the purchase).
- **Gate:** `longevity_current >= cost` fires; strictly under refuses. At exactly the cost the flee fires and lands the character at 0.
- **Refusal is free:** no Longevity deducted, no flee cooldown recorded (`record_flee_attempt` must NOT be called on the refusal path).
- **Exempt paths (no cost, no gate):** flee outside combat (existing `You are not in combat.` no-op — byte-unchanged) and the empty-session disengage (the `flee_empty` path — no living opposition, no contest).
- **Refusal line (authored):** `You are too spent to flee!` — warn category (the world declining), sibling in form to `You are too close to death to flee!`.
- **Regen:** rate is `longevity_max / 900` points per second, form chosen by regime: `longevity_max < 900` → interval form (one point every `ceil(900 / longevity_max)` ticks, as shipped); `longevity_max >= 900` → per-tick form (`ceil(longevity_max / 900)` points per tick, exactly Vitality's shape).
- **The potion is a draught mirror, exactly:** percent-of-max restore `0.15 + 0.05×Mk` of `longevity_max`, floor 25 points, `math.ceil` never `round()` (the #105 lesson), Common, `base_value` 15, Mk-scaled by the standard generation path. **The Mk-1 shortfall against flee is deliberate** (20% < 25%) — do not "fix" it.
- **Potion supply:** authored `VendorEntry` rows for Essa, Sona, Ridda (Z01) at 15 cp; the Convergence carts (VND-9, Mother Tansy) pick it up **automatically** via the #43 every-consumable query — no cart code changes. **No loot-table entries.**
- **Stop-at-full:** using the potion at full Longevity refuses (warn, item not consumed): `You are already at full stamina.` Authored line; mirrors the draught's full-health rule.
- **No other bar, stat, effect, or command changes.** Acuity is untouched everywhere. `heal` remains vitality-draught-only. The `dot_longevity`/`hot_longevity` tick branches are untouched.
- All bar mutations are atomic F()-expression updates (#52 style) — never read-modify-write on a cached object.

## Verified technical claims (#252)

Every structural claim below was verified against the code at writing time (2026-09-13, branch `version_26_1` @ `83908e1`); file:line references are to that tree.

- `django/src/apps/shyland/version.py:8` — `SHYLAND_VERSION = "26.0"`; pin test at `tests/test_b2_amendment1.py:122` asserts `'26.0'`.
- `django/src/apps/shyland/models.py:15-17` — `VITALITY_REGEN_SECS = 120`, `LONGEVITY_REGEN_SECS = 3600`, `VITALITY_PERCENT_HEAL_FLOOR = 25`. `COMPONENT_TYPE_CHOICES` at models.py:389 (contains `restore_longevity` flat, no percent form). `Character.longevity_current/max` are `IntegerField(default=100)` (models.py:273-274). `EffectComponent.is_instantaneous()` (models.py:437) is duration-based — a new duration-0 type is instant with no change.
- `django/src/apps/shyland/consumers.py:2673` — `cmd_flee` order: no-session no-op (2677) → dying check (2681) → cooldown check (2685) → empty-session `flee_empty` disengage (2690-2699) → contest (from 2703, `avg_per = flee_contest_npc_side(npcs)`). `record_flee_attempt` is called at exactly two sites, both post-contest (2731 nowhere-to-run, 2801 contest failure); the success path's room change refreshes status (the 3932 room-change contract), the failure and nowhere-to-run paths send no status refresh today.
- `django/src/apps/shyland/effect_utils.py:7` — `percent_heal_amount(fraction, vitality_max)` = `max(VITALITY_PERCENT_HEAL_FLOOR, ceil(fraction × vitality_max))`; its two callers are the instant-apply branch (effect_utils.py:127) and the consumers use-path aggregate (consumers.py:1749). `_apply_instant_component` branches: `restore_vitality_percent` at :121, flat `restore_longevity` at :132 with clause `("feel your stamina return", "(+N Longevity)")`.
- `django/src/apps/shyland/consumers.py:4366` — the use path calls `apply_effect_definition(effect_def, character, mk_tier, removed_by_label='consumable')`: the potion's Mk scaling rides for free.
- `django/src/apps/shyland/consumers.py:1544-1553` — the per-item use loop's stop-at-full gate: `effect_restores_vitality` (defined :3622, types `restore_vitality`/`restore_vitality_percent`/`hot_vitality`) → at full vitality warn `You are already at full health.`, break before apply/consume. The vitality-deficit aggregate path and `heal` qualification (`_item_aggregatable`, :1633) are vitality-restore-only **by design** — the potion does not qualify and takes the general per-item path (the Focus Tonic precedent).
- `django/src/apps/shyland/management/commands/run_tick_engine.py:1848-1901` — Phase 4 regen: vitality per-tick ceil at :1883; longevity interval form at :1895 (`interval = ceil(LONGEVITY_REGEN_SECS / longevity_max)`, fires on `tick_number % interval == 0`).
- `django/src/apps/shyland/management/commands/seed_world.py` — Healing Draught mirror template: `EffectDefinition` + component at :4144-4157 (`restore_vitality_percent`, magnitude 0.15/0.05, duration 0/0), `ItemDefinition` dict entry at :4656-4673 (`base_value` 15, scaling 0/0). Vendors: `_seed_verdant_vendors` :7618 (Essa 4 wares, Sona 4), `_seed_ridge_vendors` :7963 (Ridda 5; Ridda spawns in `vr-c01` — Z01, :7869). Cart auto-stock loop :5482-5503 (every `item_type=CONSUMABLE` definition, price from `CART_CONSUMABLE_PRICES` :2554 else default 15). `base_values` back-fill dict :5334+ (forced on every reseed). Seed verification pins vendor counts at :3872-3878: Essa 4, Sona 4, Ridda 5.
- `django/src/apps/shyland/templates/shyland/game.html:413-416` — the `#bars` block renders rows V, A, L; JS binds by element id (`bar-v`, `bar-a`, `bar-l`) so a markup reorder changes nothing functional. The `stats` command (consumers.py:2861-2864) **already renders Vitality, Longevity, Acuity** — no server change for ordering.
- `docs/shyland/Shyland_Architecture_v26.md` — current header hash `bdb83f3`, stamp 26.0; relevant sections: §4.1 Models, §4.3 consumers, §4.4 effect_utils, §4.8 seed, §4.9 tick engine, §4.15 UI layout.
- Migration head is `0057` (v25.16); this brief's model change produces `0058`.

**One verified deviation from the 2026-09-11 ruling's letter, ruled 2026-09-13:** that ruling named the potion "`restore_longevity`'s first customer," but the flat `restore_longevity` type cannot express a percent-of-max restore. The percent family member `restore_longevity_percent` is the customer; the flat type is untouched.

## Implementation steps

Commit and push at every step boundary (branch only — never merge to main).

### Step 1 — Version constant (opening act, own commit)

`SHYLAND_VERSION` `"26.0"` → `"26.1-DEV"` in `django/src/apps/shyland/version.py`; the pin test assertion in `tests/test_b2_amendment1.py:122` moves to `'26.1-DEV'` in the same commit. Then run the version-start `make deploy-dev` from the worktree.

### Step 2 — Constants and model (`models.py`)

1. `LONGEVITY_REGEN_SECS = 3600` → `900` (comment stays accurate: seconds to regen full Longevity from zero out of combat).
2. Add beside `VITALITY_PERCENT_HEAL_FLOOR`:
   `LONGEVITY_PERCENT_RESTORE_FLOOR = 25  # the potion mirror of the Draught Law floor (#70)`
3. Add to `COMPONENT_TYPE_CHOICES`, immediately after the `restore_longevity` entry:
   `('restore_longevity_percent', 'Restore Longevity (percent of max)'),`
4. **Migration:** `make makemigrations APP=shyland` (expect one `0058_alter_effectcomponent_component_type`-shaped migration — choices only, no schema change) then `make migrate`. Commit the migration file.

### Step 3 — Effect layer (`effect_utils.py`)

1. Add a generalized helper; `percent_heal_amount` becomes a thin delegate so its two existing callers are byte-compatible:

```python
def percent_restore_amount(fraction, bar_max, floor):
    """The Draught Law shape (#139), generalized per bar (#70): restores
    ceil(fraction × bar_max), never less than the bar's floor. The
    fraction is of MAX, never of deficit. math.ceil, never bare round()."""
    return max(floor, math.ceil(fraction * bar_max))


def percent_heal_amount(fraction, vitality_max):
    from .models import VITALITY_PERCENT_HEAL_FLOOR
    return percent_restore_amount(fraction, vitality_max,
                                  VITALITY_PERCENT_HEAL_FLOOR)
```

(Preserve `percent_heal_amount`'s existing docstring content on whichever of the two functions reads best; the signature and behavior must not change.)

2. In `_apply_instant_component`, add a branch immediately after the flat `restore_longevity` branch (mirror the `restore_vitality_percent` branch at :121, including its stale-read comment adapted — `longevity_max` is safe to read from the caller's character for the same reason `vitality_max` is):

```python
    if ctype == 'restore_longevity_percent':
        restore = percent_restore_amount(
            magnitude, target.longevity_max, LONGEVITY_PERCENT_RESTORE_FLOOR)
        row.update(longevity_current=Least(
            F('longevity_current') + restore, F('longevity_max')))
        return ("feel your stamina return", f"(+{restore} Longevity)")
```

(Import `LONGEVITY_PERCENT_RESTORE_FLOOR` the same way the vitality floor is imported. The clause is identical to the flat branch's — same speech, actual amount in the annotation.)

### Step 4 — Stop-at-full mirror (`consumers.py`)

1. Add beside `effect_restores_vitality` (:3622), same shape and docstring style:

```python
    @database_sync_to_async
    def effect_restores_longevity(self, effect_def):
        """#70: the potion's stop-at-full rule — derived from the effect's
        own components, never a separate flag (the #61 helper's law)."""
        return effect_def.components.filter(
            component_type__in=('restore_longevity',
                                'restore_longevity_percent', 'hot_longevity'),
        ).exists()
```

2. In the per-item use loop, directly after the vitality stop-at-full block (:1544-1553), add the longevity gate with the same structure, conditioned on: the effect restores longevity **and does not restore vitality**. When that holds and not `was_dying`, fresh-read the character; at `longevity_current >= longevity_max` warn `You are already at full stamina.` (only when `used == 0`, mirroring the vitality block), set the stopped flag, `break` before apply and consume. (Effects restoring **both** bars — none seeded today — deliberately keep the existing vitality-gate semantics untouched; a dual-restore gating rule is a future design question, not this brief's.)

### Step 5 — Flee fuel gate (`cmd_flee`, consumers.py)

Insert after the empty-session block (:2690-2699) and before the contest (`avg_per = ...`, :2703):

1. `cost = math.ceil(character.longevity_max / 4)`
2. If `character.longevity_current < cost`: `await self.send_output("You are too spent to flee!", 'warn')` and `return`. **No deduction, no `record_flee_attempt`, no status refresh** (nothing changed).
3. Otherwise deduct once, atomically, before the contest, via a new `@database_sync_to_async` helper: `Character.objects.filter(pk=character.pk).update(longevity_current=Greatest(F('longevity_current') - cost, 0))` (`Greatest` is belt-and-suspenders under the gate; import from `django.db.models.functions`). Also set `character.longevity_current = max(0, character.longevity_current - cost)` on the local object so every downstream read in this handler sees the spent value.
4. **Status refresh on the non-success outcomes:** the success path's room change already refreshes status (the room-change contract); add `await self.send_status_refresh()` to the contest-failure path (after the :2801 `record_flee_attempt`) and the nowhere-to-run path (after the :2731 `record_flee_attempt`), so the player's pane shows the spent fuel.

Do not touch the dying check, the cooldown check, the no-session no-op, the empty-session path, the contest math, or the MC `combat_flee` event payloads.

### Step 6 — Regen regime (`run_tick_engine.py`, Phase 4)

Replace the longevity arm (:1889-1901) with the regime form; the vitality arm is untouched:

```python
            if character.longevity_current < character.longevity_max:
                if character.longevity_max >= LONGEVITY_REGEN_SECS:
                    # Per-tick form (v26.1, #70): at or above the constant,
                    # Vitality's shape — ceil(max / CONSTANT) points per tick.
                    heal = math.ceil(
                        character.longevity_max / LONGEVITY_REGEN_SECS)
                    character.longevity_current = min(
                        character.longevity_current + heal,
                        character.longevity_max)
                    changed_fields.append('longevity_current')
                else:
                    # Interval form: below the constant the per-tick ceil
                    # would always be 1 (the ceil trap). One point every
                    # ceil(CONSTANT / max) ticks; an engine restart resetting
                    # tick_number at worst delays one point by up to one
                    # interval — accepted, no persistent state.
                    interval = math.ceil(
                        LONGEVITY_REGEN_SECS / character.longevity_max)
                    if tick_number % interval == 0:
                        character.longevity_current = min(
                            character.longevity_current + 1,
                            character.longevity_max)
                        changed_fields.append('longevity_current')
```

### Step 7 — Seed (`seed_world.py`)

All additions; **expected deletion count: 0**.

| Object | Content |
|---|---|
| `EffectDefinition` | slug `stamina-potion`, name `Stamina Potion`, description `Restores Longevity immediately.` |
| `EffectComponent` | definition ↑, order 0, `component_type='restore_longevity_percent'`, `magnitude_base=0.15`, `magnitude_scaling=0.05`, `duration_base=0.0`, `duration_scaling=0.0` |
| `ItemDefinition` | slug `stamina-potion`, name `Stamina Potion`, `item_type` consumable, `genre_tag` fantasy, `valid_slots=[]`, `base_value=15`, scaling 0/0, `takes_durability_loss=False`, `durability_table=[]`, `primary_stats=[]`, `secondary_stat_pool=[]`, `effect=effects['stamina-potion']`, description `Thick as tar and stubborn going down. Puts the road back under your feet.` |
| `VendorEntry` ×3 | `('stamina-potion', 15)` appended to Essa's, Sona's, and Ridda's wares lists |

Supporting edits, mirroring the draught's precedents exactly:

1. Seed the effect in the effects section (beside the Healing Draught block, :4144), register it in the `effects` dict, and place the `ItemDefinition` dict entry in the Consumables run (beside `healing-draught`, :4656).
2. `base_values` back-fill dict: add `'stamina-potion': 15` (the forced-on-reseed authored value).
3. `CART_CONSUMABLE_PRICES`: add `'stamina-potion': 15` (explicit even though it equals the default — the repair-kit precedent guards against a future default change).
4. **Seed verification counts (:3872-3878):** Essa `4` → `5`, Sona `4` → `5`, Ridda `5` → `6`; update the check's label string to match.
5. **No loot-table entries anywhere.** The Convergence carts pick the potion up automatically from the every-consumable query — verify in dev output, change no cart code.
6. Expected new rows per reseed against a pre-brief database: 1 `EffectDefinition`, 1 `EffectComponent`, 1 `ItemDefinition`, **5** `VendorEntry` (Essa, Sona, Ridda authored + VND-9, Mother Tansy automatic).

### Step 8 — Display reorder (`game.html`)

In the `#bars` block (:413-416), move the L row above the A row so the order is V, L, A. Markup move only — ids, classes, and JS untouched. (The `stats` command already renders V/L/A; no server change.)

### Step 9 — Tests (`tests/test_v26_1_brief1.py`, new file)

Cover, at minimum:

1. **Flee cost:** contested success and contested failure each deduct exactly `ceil(longevity_max / 4)`.
2. **Refusal:** below the cost — warn line exact, `longevity_current` unchanged, `last_flee_attempt_at` unchanged (no cooldown).
3. **Boundary:** at exactly the cost the flee proceeds and lands at 0.
4. **Exemptions:** empty-session flee deducts nothing; out-of-combat flee response byte-unchanged.
5. **Regen regime:** interval form below 900 (fires only on interval ticks, +1); per-tick form at `longevity_max >= 900` (+`ceil(max/900)` every tick); both clamp at max.
6. **`percent_restore_amount`:** ceil behavior and the 25-point floor; `percent_heal_amount` delegation unchanged for vitality (spot-check one existing value).
7. **`restore_longevity_percent` apply:** Mk 1 restores `max(25, ceil(0.20 × longevity_max))` clamped at max (at the default 100-point bar the floor governs: 25); annotation carries the actual amount.
8. **Stop-at-full:** potion at full Longevity refuses with the exact line and consumes nothing; at a deficit it applies and consumes.
9. **Seed:** after `seed_world`, the potion's definition/effect/component wiring is exact (type, magnitudes, value 15) and all five vendors list it at 15.

Zero existing tests change beyond the Step 1 pin move. Full-suite invariant for the closeout report: previous suite count 967, all prior tests still passing, plus this file's additions.

### Step 10 — Full suite + dev deploy

1. In-container suite — the only working form: `python manage.py test apps/shyland/tests` (directory-path form, via `docker exec` in the django container). All green.
2. `make deploy-dev` from the worktree.
3. `make seed` from the worktree (dev posture — targets the dev stack). Record actual row deltas against the Step 7 expectations (deletions must be 0); the seed's own verification pass (including the updated vendor counts) must report clean.

## PENDING DEPLOY-TIME ACTIONS

| Action | Executor | Expected effect |
|---|---|---|
| Production seed rerun (delivers the Stamina Potion: effect, item, 3 authored + 2 automatic vendor entries; expected deletions **0**) | `make seed-prod` — closeout tail's deploy window only, bare invocation, on its own operator confirmation | +1 `EffectDefinition`, +1 `EffectComponent`, +1 `ItemDefinition`, +5 `VendorEntry`; seed verification (incl. 5/5/6 vendor counts) passes on prod |

This block stays open until the production execution at release deploy. (No `verify_*` command ships with this brief; the count invariants live in the seed's own verification pass, which `make seed-prod` runs.)

## Operator playtest checklist (dev stack, after Step 10)

Steps are run/expect/decision. "Stop and report" means stop the playtest and report to the session; otherwise continue to the next step.

1. **Run:** log in on dev, open the game client. **Expect** (precondition: Step 8 deployed): the stats pane bars read top-to-bottom **V, L, A**. **If not:** stop and report. Else continue.
2. **Run:** `stats`. **Expect:** the bar lines read Vitality, Longevity, Acuity in that order (this was already the order; it must not have regressed). **If not:** stop and report. Else continue.
3. **Run:** `flee`, outside combat. **Expect:** `You are not in combat.` and Longevity unchanged. **If not:** stop and report. Else continue.
4. **Run:** note Longevity current/max, engage any Z01 NPC (`attack <npc>`), then `flee`. **Expect** (precondition: Longevity ≥ 25% of max at the moment of the flee): either the escape or `You tried to flee but your enemies are too strong.` — and in both cases the Longevity number drops by exactly ⌈max/4⌉ on the pane. **If no deduction, or a deduction on a different amount:** stop and report. Else continue.
5. **Run:** repeat step 4's engage-and-flee (waiting out the flee cooldown as needed) until Longevity current sits **below** 25% of max, then `flee` once more in combat. **Expect:** `You are too spent to flee!`, Longevity unchanged by that refused attempt, and the fight still on. **If the flee fires or Longevity moves:** stop and report. Else continue (end the fight by winning or dying — either is fine for the test).
6. **Run:** out of combat, note Longevity **and max**, wait 60 seconds without acting, compare. **Expect** (precondition: Longevity below max): with interval = ⌈900 ÷ max⌉ seconds, roughly 60 ÷ interval points regained (±1 for tick alignment — e.g. a 274 bar regains ~15, a 100 bar ~6–7). **If zero regen or well outside that:** stop and report. Else continue.
7. **Run:** visit Essa, Sona, or Ridda (Z01), `list`. **Expect:** `Stamina Potion` listed at 15 copper. **If absent or mispriced:** stop and report. Else continue.
8. **Run:** `buy stamina potion`, then travel to the Convergence ring street and `list` at Mother Tansy or VND-9. **Expect:** the potion also listed there at 15 copper (the automatic cart stock). **If absent:** stop and report. Else continue.
9. **Run:** with Longevity below max (flee once if needed), `use stamina potion`. **Expect:** a success sentence with the clause `feel your stamina return (+N Longevity)` where N = max(25, ⌈0.20 × max⌉) at Mk 1 — at a 100-point bar the 25-point floor governs — the pane's Longevity rising by N (clamped at max), and the potion consumed from inventory. **If the amount is wrong or the item survives:** stop and report. Else continue.
10. **Run:** at **full** Longevity, `use stamina potion` (buy one first if needed). **Expect:** `You are already at full stamina.` (warn) and the potion still in inventory. **If it consumes or applies:** stop and report. Else continue.
11. **Run:** damage yourself below full Vitality (any fight), then `heal`. **Expect:** the draught flow byte-identical to 26.0 — draughts consumed, vitality restored; the potion is never consumed by `heal`. **If `heal` touches the potion:** stop and report. Else the playtest is complete — report success.

## Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing.

Update `docs/shyland/Shyland_Architecture_v26.md` **in place**: stamp to **26.1**; the header hash **moves** to this release's final implementation commit (architectural change: new component type + migration, flee gate, regen regime). Sections to update:

- **Header block:** the standard release paragraph (Version 26.1, branch, #70, what shipped, suite delta, hash rationale).
- **§4.1 Models:** `LONGEVITY_REGEN_SECS` 900, `LONGEVITY_PERCENT_RESTORE_FLOOR`, the new component type + migration `0058`.
- **§4.3 consumers:** the flee fuel gate (position, cost, free refusal, exemptions, status refreshes) and the longevity stop-at-full gate.
- **§4.4 effect_utils:** `percent_restore_amount` generalization and the `restore_longevity_percent` branch.
- **§4.8 seed:** the Stamina Potion (definition/effect/vendors/back-fills) and the updated vendor-count verification.
- **§4.9 tick engine:** the Phase 4 regen regime rule.
- **§4.15 UI layout:** the V/L/A bar order.
- **§7 What Is Not Yet Built / §8 Known Issues:** correct any now-stale "nothing drains Longevity" claims.

## Closeout

Closeout report as `.txt` in `docs/shyland/` (completed in place from the Step-0 stub), including: final commit hash, actual seed row deltas vs Step 7 expectations, the suite count, any deviations (the test-hygiene and ruling-letter notes above are pre-declared), the PENDING DEPLOY-TIME ACTIONS block, and the **operator playtest disposition** verbatim-style (successful / no playtests / deferring — the closeout session reads this line as a gate). Then end with the `implementation-session-end` ritual (which runs the issues report).
