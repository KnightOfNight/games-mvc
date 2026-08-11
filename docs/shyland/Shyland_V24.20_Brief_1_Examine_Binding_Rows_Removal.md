# Shyland V24.20 Brief 1 — Examine Binding Rows Removal

- **Release:** Version 24.20 (point release)
- **Founding ticket:** #203 — Design: examine's 'Note: … you may drop it' line — weird on ground items, redundant with the flag block, key/value inconsistent
- **Branch:** `version_24_20`
- **Produced by:** Version 24.20 design session, 2026-08-10
- **Milestone:** `Version 24.20` (closes #203)

## Ruling being implemented (recorded on #203, 2026-08-10)

Both binding prose rows are **deleted** from examine's identified detail block:

- `  Note:       This item is not yet bound — you may drop it.` (rendered when neither equipped nor soulbound)
- `  Bound:      This item is bound to you.` (rendered when soulbound)

Bound state is carried **solely by the headline's trailing flag block** (`[Rarity, Bound|Unbound]`), which heads the same detail block, consistent with the binding-in-the-flag-block doctrine (GDD §6.11). The `Equipped:` and `Curse:` rows are **explicitly untouched** — each carries a fact the flag block does not (equip slot; identified curse state). GDD §6.8 ("Examine Is Close Inspection") carries the ruled text with a `(v24.20, pending implementation — #203)` marker; implementation sessions never edit GDD source — the marker is swept later by a design or closeout session.

## Design rules — do not deviate

1. Delete exactly the two rows above. No replacement row, no rewording, no key/value normalization — the fact leaves the block body entirely.
2. Every other row of the detail block is byte-identical to before: headline (`compose_item_line`), description, `Type:`/`Genre:`/`Damage:`/`Hands:`/`Armor:`/`Durability:`/`Carry bonus:` rows, blank-line placement, stat lines, `Equipped:`, `Curse:`.
3. The change is output composition only. No model change, no resolver change, no state change, no message-category change.
4. The flag block itself is untouched — this brief does not modify `compose_item_line` or any other item-line composition site.

## Implementation

**File:** `django/src/apps/shyland/consumers.py`, method `_format_identified_item_lines` (~lines 1814–1826).

Current tail of the method:

```python
        if item.is_equipped:
            lines.append(f'  Equipped:   {format_slot_name(item.equipped_slot)}')

        if item.is_soulbound:
            lines.append('  Bound:      This item is bound to you.')

        if item.is_cursed and item.curse_identified:
            lines.append('  Curse:      This item carries a curse.')

        if not item.is_equipped and not item.is_soulbound:
            lines.append('  Note:       This item is not yet bound — you may drop it.')

        return lines
```

Delete the `if item.is_soulbound:` block and the `if not item.is_equipped and not item.is_soulbound:` block (two lines each). Resulting tail:

```python
        if item.is_equipped:
            lines.append(f'  Equipped:   {format_slot_name(item.equipped_slot)}')

        if item.is_cursed and item.curse_identified:
            lines.append('  Curse:      This item carries a curse.')

        return lines
```

## Migrations

**None.** No model changes in this brief. State this in the closeout report.

## Standing requirements

1. **Version constant (first implementation brief of the release — opening act):** bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` from `"24.19"` to `"24.20-DEV"` in **its own commit**, moving the pin-test assertion (`django/src/apps/shyland/tests/test_b2_amendment1.py`, currently line 118: `self.assertEqual(SHYLAND_VERSION, '24.19')` → `'24.20-DEV'`) in the same commit. Then run the version-start `make deploy-dev` from the worktree.
2. **In-session dev deploy:** exactly `make deploy-dev` from the worktree once implementation and verification pass. Production is never deployed from an implementation session.
3. **Operator playtest checklist** targeting the dev stack — below.

## Tests

**New regression tests** (new file `django/src/apps/shyland/tests/test_v24_20_brief1.py`, following the existing per-brief test-file pattern), exercising `_format_identified_item_lines` directly as the prior brief tests do:

1. An **unbound, unequipped** item: no rendered line contains `Note:` and no line contains `not yet bound`; the headline (first line) still ends with an `Unbound` flag block.
2. A **soulbound, unequipped** item: no line contains `This item is bound to you.`; the headline flag block reads `Bound`.
3. A **soulbound, equipped** item: the `Equipped:` row is present; no binding prose row.
4. A **curse-identified cursed** item: the `Curse:      This item carries a curse.` row is present, unchanged.

**Existing tests:** no existing test asserts either deleted string (verified at design time — the only `bound to you` test hit is drop's refusal warn `…bound to you and cannot be dropped`, a different string and site, untouched). If any existing test nonetheless fails on the block's shape (e.g. a full-list or length assertion), adjust it minimally to the ruled composition with original intent preserved, and report the change as a deviation in the closeout — never silently.

## Verification

All steps must pass before issue close and the architecture-doc step.

1. Full suite green, in-container, path form only:
   `docker exec <django container> python manage.py test apps/shyland/tests`
2. The four new regression tests pass.
3. `grep -n 'not yet bound\|bound to you\.' django/src/apps/shyland/consumers.py` returns **no hit inside `_format_identified_item_lines`** (drop's refusal warn elsewhere in the file is expected and untouched).
4. `make deploy-dev`, then on the dev stack: `examine` an unbound carried item, a ground item, and a soulbound equipped item — no binding prose row in any render; flag block, `Equipped:`, and durability/stat rows intact.

## Issue close

Close **#203** once all verification steps pass, with a comment linking the implementing commit. Gated on verification passing.

## Architecture doc — last, gated step

This step is gated on all implementation and verification steps above being complete and passing.

`docs/shyland/Shyland_Architecture_v24.md`, updated **in place**:

- Stamp line: 24.19 → **24.20**. The **commit hash does not move** — this is an output-composition change, not an architectural one.
- No section-content changes expected: the doc does not enumerate the detail block's tail rows (verified at design time — no hit for either deleted string). If a passage is nonetheless found describing them, correct it to the ruled composition and note it in the closeout.

## Closeout report

`docs/shyland/Shyland_V24.20_Brief_1_Closeout.txt` (stub created at Step 0, completed in place): final commit hash, migration statement ("none"), any test-hygiene deviations, **PENDING DEPLOY-TIME ACTIONS: none** (no seed or data actions in this brief), and the operator playtest disposition line (#170).

## Operator playtest checklist (dev stack)

1. `examine` a carried **unbound** item → detail block shows no `Note:` row; headline flag block reads `[…, Unbound]`.
2. `drop` that item, then `examine` it on the ground → full detail block (knowledge-by-holding reveal), no `Note:` row, no "you may drop it" anywhere.
3. `examine` an **equipped** (therefore soulbound) item → no `Bound:` prose row; `Equipped:` row present; headline flag block reads `[…, Bound]`.
4. Confirm one unaffected composition: `inv` Details column still reads `…, Bound|Unbound`.

## End

This brief touches issue state (#203 closes). End the session per ritual: run the issues report.
