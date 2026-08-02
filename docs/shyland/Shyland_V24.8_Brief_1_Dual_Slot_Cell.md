# Shyland V24.8 — Brief 1: Dual-Slot Cell

**Release:** Version 24.8 (milestone `Version 24.8`) · **Branch:** `version_24_8` · **Founding ticket:** #197 (no dependencies)

**Design authority:** #197 ruling comment (2026-08-02, V24.8 design session) + GDD §6.11 (this branch — carries the `(v24.8, pending implementation — #197)` marker this brief implements). Where this brief and the GDD disagree, the GDD wins.

---

## 1. What ships

The listing-table Slot cell stops hiding either-hand flexibility. An item valid in more than one equip slot names **all** its slots — sentence-case labels joined with `/` in authored `valid_slots` order:

```
Main hand/Off hand
```

Seed's only current dual-slot case is the **Combat Knife** (`valid_slots: ['MAIN_HAND', 'OFF_HAND']`), which today lists as just `Main hand` in the `inv` inventory table and vendor `list`.

**Ruled composition (from the #197 ruling — do not deviate):**

1. All valid slots render, joined with `/`, each through the existing sentence-case label mapping (`item_utils.format_slot_name`); order is authored `valid_slots` order.
2. The two-handed word appends **once, after the full joined label**: a hypothetical dual-slot two-hander reads `Main hand/Off hand (two-handed)`. (Defensive ruling — no such item exists in seed; no seed changes in this brief.)
3. Single-slot items render exactly as today (`Main hand`, `Ranged (two-handed)`, …); slotless items keep the muted `-`.
4. Scope is the shared `_slot_cell` helper only — `inv`'s inventory table and vendor `list` inherit together. The Equipment paper-doll, examine's `Equipped:` row, and all equip/combat mechanics are untouched.

Display composition only. **Zero mechanics changes. Runtime code only — `consumers.py`. No models, no migrations, no seed data.**

## 2. Version constant — opening act (first brief of the release)

Before any other change, in its own commit:

- `django/src/apps/shyland/version.py`: `SHYLAND_VERSION = "24.7"` → `"24.8-DEV"`.
- The pin test moves in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py` line ~118, `self.assertEqual(SHYLAND_VERSION, '24.7')` → `'24.8-DEV'`.
- Then the version-start `make deploy-dev` from the worktree.

## 3. Implementation

`django/src/apps/shyland/consumers.py`, `_slot_cell` (~line 903). Current body renders `format_slot_name(defn.valid_slots[0])`. Change to compose the joined label from every entry of `defn.valid_slots`, preserving order, then apply the existing two-handed suffix rule to the joined label:

```python
label = '/'.join(format_slot_name(s) for s in defn.valid_slots)
if defn.item_type == 'weapon' and defn.is_two_handed:
    return f'{label} (two-handed)'
return label
```

Update the helper's docstring to record the v24.8 (#197) rule alongside the v22 (#123) and v24.7 (#194) history. The slotless branch (`return [('-', 'muted')]`) is untouched. No other call sites change — both callers (`cmd_inventory`'s inventory table, the vendor-list row builder) inherit.

## 4. Verification

New test file `django/src/apps/shyland/tests/test_v24_8_brief1.py`, covering:

1. **Dual-slot in `inv`:** a character holding a Combat Knife (unequipped) sees `Main hand/Off hand` in the inventory table's Slot cell.
2. **Dual-slot in vendor `list`:** a vendor entry whose definition carries `['MAIN_HAND', 'OFF_HAND']` lists `Main hand/Off hand`.
3. **Single-slot unchanged:** a one-hander lists `Main hand`; a RANGED two-hander lists `Ranged (two-handed)` (byte-identical to v24.7 behavior).
4. **Slotless unchanged:** a material/consumable renders the muted `-` cell.
5. **Dual-slot two-hander (synthetic):** a test-constructed definition with `valid_slots ['MAIN_HAND', 'OFF_HAND']`, `item_type='weapon'`, `is_two_handed=True` composes `Main hand/Off hand (two-handed)`. Construct in-test; **do not add it to seed**.
6. **Version pin:** `24.8-DEV` asserted (lives in `test_b2_amendment1.py`, moved by §2).

Full suite must pass — in-container, the only working form:

```
docker exec game-mvc-django python manage.py test apps/shyland/tests
```

Test hygiene (standing rule): if any existing test literal-pins a Combat Knife Slot cell as `Main hand`, convert it to the ruled composition with original intent preserved as explicit assertions and report the conversion as a deviation in the closeout. None is known at brief-writing time.

## 5. Deploy

`make deploy-dev` from the worktree once implementation and verification pass. No migrations expected (none permitted — no model changes). No PENDING DEPLOY-TIME ACTIONS — no seed changes, no data actions.

## 6. Operator playtest checklist (dev stack)

1. With a Combat Knife in inventory (vendor-buy one if needed): `inv` → Slot cell reads `Main hand/Off hand`.
2. At a vendor selling the Combat Knife: `list` → Slot cell reads `Main hand/Off hand`.
3. Spot-check a one-hander (`Main hand`), a bow (`Ranged (two-handed)`), and a material (muted `-`) in `inv` — unchanged.
4. `examine combat knife` and the paper-doll (`inv` top section / bare `equip`) — unchanged (real slot names only; no joined labels there).
5. Equip the Combat Knife to each hand in turn — equip behavior itself unchanged.

## 7. Architecture doc — last, gated

This step is gated on all implementation and verification steps above being complete and passing.

`docs/shyland/Shyland_Architecture_v24.md`, updated **in place**:

- §4.3 (equipment display / listing composition): the `_slot_cell` sentence updates to the ruled composition (all slots joined with `/`; two-handed word after the full label).
- Header: stamp → **24.8**, hash → this brief's implementation commit (architectural point release — display composition changed; the v24.7 precedent).
- A **Version 24.8** block in the header's version history paragraph, following the v24.7 pattern.

## 8. Closeout

Closeout report `docs/shyland/Shyland_V24.8_Brief_1_Closeout.txt` (stub created and pushed as Step 0 per the standing ritual; completed in place). Must include the final commit hash and the operator playtest disposition line. Close #197 gated on verification passing. End with the `implementation-session-end` ritual.
