# Shyland V24.12 — Brief 1: Repair Kit Wiring (#134)

- **Release:** Version 24.12 (milestone `Version 24.12`) — singleton wiring release; the last Phase 2 (itemization structure) item of the V24 plan
- **Branch:** `version_24_12` (worktree; this brief is committed at its tip)
- **Founding ticket:** #134 — "Repair kit not wired up yet" (complete ruling + addendum recorded on the issue, 2026-08-06)
- **Design authority:** GDD §6.5 "Field Repair — the Repair Kit (v24.12, pending implementation)", §9 state-gating matrix + aggregation paragraph (same marker), commit `822addc`. The GDD section files win over anything in this brief if they disagree — stop and report the discrepancy rather than choosing.
- **Scope law:** one founding ticket, one brief. #201's ruled base_value changes (Flame Projector / Dart Caster) are **not** in scope — do not touch them.
- **Pending-actions pre-flight:** this is the first brief of Version 24.12; no prior deploy-time actions exist in this version.

## What this brief does

The seeded `Repair Kit` consumable (`repair-kit`) carries `effect: None`; `use repair kit` prints the generic `Nothing happens.` warn. The `durability_restore` EffectComponent type has existed since migration `0004` with zero uses, and its clause handler in `effect_utils.py` is a dead fizz placeholder. This brief wires the kit into the existing repair machinery as the field-repair consumable, exactly per the #134 rulings. Vendor repair (`repair` / `repair all`) is untouched.

## Design rules — never deviate

1. **Target selection is automatic: most-damaged-first** over everything the character owns (carried + equipped), stable tie-break on pk. Broken (0%) items are **ineligible targets and are skipped**.
2. **A kit always succeeds and is consumed.** No roll — the roll stays vendor repair's mechanic.
3. **Restore = 15 + 10 × Mk durability points** (Mk 1 = +25, Mk 2 = +35), clamped at 100. The annotation reports the **actual** points applied after the clamp.
4. **Broken gear refuses the kit.** When the only damaged items owned are broken, `use` refuses (warn) — and the kit is **not** consumed.
5. **Refused in combat and while dying** — nothing but healing while dying. The gate keys on the **effect component, never the item name**; each state has its own authored warn line; no kit is consumed on any refusal.
6. **Economy:** `base_value` 15 (the draught standard — cart buy 15 cp stands via the existing `CART_CONSUMABLE_PRICES` entry; sale 5 cp follows from the standard third). **Cart-only supply: add the kit to no loot table.**
7. **Sequences are per-item** (repair-family output stays per-line), re-targeting most-damaged-first after each kit; zero need refuses without consuming; the sequence **stops the moment nothing damaged remains** (fulfilled-purpose doctrine) with the standard only-had-N reporting.
8. All refusals are warn-layer; the mend sentence is the standard merged use sentence (success-color), one envelope.

## Part 1 — Version constant (opening act)

First commit of the implementation session, on its own:

- `django/src/apps/shyland/version.py`: `SHYLAND_VERSION = "24.11"` → `"24.12-DEV"`
- The pin test moves in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py` line asserting `self.assertEqual(SHYLAND_VERSION, '24.11')` → `'24.12-DEV'`

Then the version-start dev deploy: `make deploy-dev` from the worktree.

## Part 2 — Code

### 2.1 The durability-restore application (`django/src/apps/shyland/effect_utils.py`)

Replace the fizz placeholder in `_apply_instant_component` (`if ctype == 'durability_restore':` — currently returns `("watch the repair kit fizz to no useful effect", "")`) with the real application:

- Select the target: the character's most-damaged eligible item —
  `ItemInstance.objects.filter(owner=target, definition__takes_durability_loss=True, durability_current__gt=0.0, durability_current__lt=100.0).select_related('definition').order_by('durability_current', 'pk').first()`
  (this is the existing `get_damaged_items` query from `consumers.py` plus the `__gt=0.0` broken-exclusion; the kit can never target itself — kits are `takes_durability_loss=False`).
- If no eligible item exists, return `None` (nothing to say) — but note the gate in Part 2.2 refuses **before** application/consumption in every such case, so this branch firing with no target would indicate a gating bug; returning `None` is defense, not flow.
- Read `durability_current` (pre-read), then apply one atomic UPDATE in the house style: `durability_current = Least(F('durability_current') + magnitude, Value(100.0))`.
- Return the pair: clause `patch up the {name}` with the item's definite-form visible name rendered exactly as repair's own mend lines render it; annotation `(+N durability)` where `N = int(min(magnitude, 100.0 - before))`.

`magnitude` arrives as `computed_magnitude(mk_tier)` from the existing pipeline — no changes to `apply_effect_definition` itself.

### 2.2 The use-pipeline gate (`django/src/apps/shyland/consumers.py`)

Add a mechanical helper in the family of `_item_aggregatable` / `effect_restores_vitality` — e.g. `effect_restores_durability(effect_def)`: true when any component's `component_type == 'durability_restore'`. **Derived from components, never a name match.**

In `_use_per_item`, for each item whose effect passes that test, gate **before** `do_apply_effect` and **before** `consume_item` (order below is normative; a refusal consumes nothing and ends the command):

1. **Dying** (`was_dying`): refuse — authored warn line (dying wins over combat when both hold).
2. **In combat**: refuse — authored warn line.
3. **Eligibility check** (fresh query, the Part 2.1 filter):
   - No eligible items and `used == 0`: if damaged-but-broken items exist (`durability_current == 0` under the same owner/`takes_durability_loss` filter), refuse with the broken-only line; otherwise refuse with the zero-need line. Warn either way; kit not consumed.
   - No eligible items and `used >= 1`: the **fulfilled stop** — print the fulfilled line (reward color, mirroring heal's full-health fold precedent as its own line here) and stop the sequence. No only-had-N warn in this case.
4. Otherwise: apply, consume, print the merged per-line mend sentence (success) — existing machinery.

After the loop, the standing shortfall rule fires unchanged (`You only had N.` when the request exceeded inventory and the sequence wasn't fulfilled-stopped), and the standard status update sends when `used >= 1`.

The aggregate path needs **no change**: `_item_aggregatable` already returns false for the kit (no vitality-restore component), so kits always take the per-item path. Assert this in tests rather than re-deriving it.

Resolution, tab completion, stacking, and the `use` grammar are untouched.

### 2.3 Authored lines (creative content — ship as written)

| Situation | Layer/color | Line |
|---|---|---|
| Mend (per kit) | success, merged use sentence | `You use a Repair Kit Mk 1 and patch up the Iron Mace Mk 1. (+25 durability)` |
| Fulfilled stop (`used >= 1`) | reward | `Everything you own is in good repair.` |
| Zero need (`used == 0`, nothing damaged) | warn | `Nothing you own needs patching.` |
| Broken-only (`used == 0`, all damage is broken gear) | warn | `What's broken is beyond a field patch — you need a real repairer.` |
| In combat | warn | `There's no patching anything up in the middle of a fight!` |
| While dying | warn | `Patchwork won't save you now — you need healing.` |

The mend sentence composes through the standard clause machinery (Part 2.1 returns the pieces); the table's first row shows the assembled result, not a literal to hard-code.

## Part 3 — Seed data (`django/src/apps/shyland/management/commands/seed_world.py`)

1. **`_seed_effects`** gains the Repair Kit effect, in the established `_reconcile` shape:
   - `EffectDefinition` slug `'repair-kit'`, name `'Repair Kit'`, description `'Restores durability to the owner\'s most damaged item.'`
   - One `EffectComponent` (`definition`=it, `order`: 0): `component_type='durability_restore'`, `target_stat=''`, `magnitude_base=15.0`, `magnitude_scaling=10.0`, `duration_base=0.0`, `duration_scaling=0.0` (instantaneous).
   - Register it in the `self._effects` dict as `'repair-kit'`.
2. **The `repair-kit` ItemDefinition entry** in `_seed_items` gains two keys: `'base_value': 15` (with a brief comment in the draught's style noting the seed owns the value — the draught standard, #134) and `'effect': effects['repair-kit']` (replacing `'effect': None`).
3. **No loot-table changes.** The kit joins no table; `CART_CONSUMABLE_PRICES` already carries `'repair-kit': 15` — leave it.

**Expected row deletions from this seed change: 0** (reconcile-in-place only). The closeout reports actual against expected.

## Part 4 — Migration

**No model changes; no migration.** `durability_restore` is already in `COMPONENT_TYPE_CHOICES`; all new rows are data through the seed.

## Part 5 — Tests (`django/src/apps/shyland/tests/`)

New test module (e.g. `test_v2412_repair_kit.py`) covering, at minimum:

1. Seed shape: `repair-kit` ItemDefinition has `base_value=15` and an effect with exactly one component — `durability_restore`, `magnitude_base=15.0`, `magnitude_scaling=10.0`, instantaneous.
2. Most-damaged-first: two damaged owned items (40.0 and 70.0) → the 40.0 item is patched to 65.0; the kit is consumed; the other item unchanged.
3. Clamp + actual-points annotation: item at 90.0 → 100.0, sentence annotation reads `(+10 durability)`.
4. Mk scaling: a Mk 2 kit restores 35.
5. Tie-break: equal durability → lower pk patched.
6. Broken skipped: items at 0.0 and 50.0 → the 50.0 item is patched; the 0% item untouched.
7. Broken-only refusal: only a 0% damaged item owned → broken-only warn line, kit **not** consumed.
8. Zero-need refusal: nothing damaged → zero-need warn line, kit **not** consumed.
9. Combat refusal: in combat, `use repair kit` → combat warn line, kit **not** consumed; a Healing Draught still uses fine in combat in the same scenario.
10. Dying refusal: while dying → dying warn line, kit **not** consumed; a draught while dying still runs the revival sequence.
11. Fulfilled stop: one item at 80.0, `use 3 repair kit` with 3 carried → exactly 1 kit consumed, item at 100.0, fulfilled reward line, **no** only-had-N warn.
12. Shortfall: heavy damage across items, `use 5 repair kit` with 2 carried → 2 consumed, two per-line mend sentences, `You only had 2.` warn.
13. Per-line output: 2 kits over 2 damaged items → two separate mend sentences (no count-form aggregation), each naming its item.
14. Not aggregatable: `use_items_aggregatable` is false for kits (per-item path taken).
15. Equipped eligibility: a damaged **equipped** item is a valid target.
16. The full existing suite passes unchanged.

**In-container invocation (the only working form):** `python manage.py test apps/shyland/tests` via `docker exec` in the django container.

## Part 6 — Verification

Run after implementation; all must pass before issue close or deploy:

1. Full suite green in-container (path form above).
2. Django shell spot-check on dev: the `repair-kit` definition's `base_value == 15`, `effect.components.count() == 1`, component type/magnitudes per the table below.
3. `get_sale_price` on a common Mk 1 kit instance returns 5.
4. Grep check: `'repair-kit'` appears in no loot-table seed entries.

| Fact | Value (authoritative) |
|---|---|
| Restore, Mk 1 | 25 points |
| Restore, Mk 2 | 35 points |
| Restore formula | 15 + 10 × Mk, clamp at 100, actual applied reported |
| `base_value` | 15 cp |
| Cart buy price | 15 cp (existing entry, unchanged) |
| Sale price (common Mk 1) | 5 cp |
| Expected seed deletions | 0 |
| Migration | none |

## Part 7 — Dev deploy and dev data action (code first, data second)

Once implementation and verification pass:

1. `make deploy-dev` from the worktree (build + migrate).
2. Then the data action against the dev stack: `make seed` (the reconcile applies the effect wiring and `base_value`). Report actual deletions (expected 0).

## Part 8 — Operator playtest checklist (dev stack)

1. Buy a Repair Kit at a ring street cart (15 cp); sell one back (5 cp).
2. Wear some gear down in combat, then `use repair kit` — the most-damaged item is patched, one merged sentence with the `(+N durability)` annotation, per-line.
3. `use repair kit` with nothing damaged — the zero-need refusal; kit still in inventory.
4. In combat, `use repair kit` — the combat refusal; kit not consumed.
5. `use 3 repair kit` against light damage — mends print per-line, the sequence stops at whole with `Everything you own is in good repair.`, leftover kits intact.
6. Let an item hit 0% (or set one via admin) — the kit refuses/skips it; the vendor repairer still takes the very-difficult roll on it.
7. Confirm draught behavior is unchanged: `heal`, `use N healing draught`, in-combat and dying use.

## Part 9 — Architecture doc (final, gated step)

This step is gated on all implementation and verification steps above being complete and passing.

`docs/shyland/Shyland_Architecture_v24.md`, updated **in place** — stamp to **24.12**, and the header hash **moves** (architectural point release — code changed):

- §4.4 (`effect_utils.py`): `durability_restore` goes live — target selection, atomic update, clause/annotation; the fizz placeholder's retirement.
- §4.3 (the merged-use-sentence subsection family): the per-item durability gate — component-keyed, dying-then-combat order, eligibility/fulfilled-stop/refusal flow, per-line output.
- §4.8 (seed data): the repair-kit effect + `base_value` reconcile entries.
- §4.14 (command layer / gates): the durability-restore exception to `use` in the combat and dying states.

## Part 10 — Closeout report

`docs/shyland/Shyland_V24.12_Brief_1_Repair_Kit_Wiring_Closeout.txt` — created as the Step 0 stub, completed in place at session end. Must include: final commit hash; deviations (or "none"); test count before/after; actual seed deletions vs expected 0 on dev; the operator playtest disposition line (verbatim-style per #170); and this block, which stays open until the closeout tail's deploy window:

```
PENDING DEPLOY-TIME ACTIONS (production, closeout tail only):
- Production seed rerun (the sanctioned path: `make seed-prod`, bare, on its own
  operator confirmation) — applies the repair-kit effect wiring + base_value 15.
  Expected deletions: 0. Code deploys before this runs (code first, data second).
```

Issues to close (gated on verification passing): **#134**.
