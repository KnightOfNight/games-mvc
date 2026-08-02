# Shyland V24.9 Brief 1 — Authored Armor Base

- **Release:** Version 24.9 (milestone `Version 24.9`)
- **Branch:** `version_24_9`
- **Founding issue:** #129 — Authored per-item armor base — guaranteed minimum coverage under rolled resist
- **Design session:** 2026-08-02 (ruling recorded on #129; pair doctrine cross-recorded on #127)
- **Session type to apply this brief:** Implementation, on a worktree of `version_24_9`

This brief is self-contained. Implement from this document and the repo only.

---

## 1. Design summary and rules that must not be deviated from

The pair doctrine (#127/#129, ruled 2026-08-02): **an item stat of consequence is an authored guarantee plus a roll above it.** This release ships the defense side: each `ItemDefinition` authors its own base armor; rolled `physical_resist` remains bonus strictly on top.

Binding rules:

1. **Structure, not balance.** TAV must be numerically identical before and after this release for every possible loadout of currently seeded items. K = 48 is blessed and untouched. No seeded value changes beyond the mechanical slot-weight → `armor_base` mapping in §4 below.
2. **No slot gate.** TAV sums `armor_base × mk_tier` over ALL equipped, non-broken items — no `item_type` check, no slot check. Only armor items carry nonzero values today; the code must not care.
3. **Rarity-blind base.** Rarity continues to act only through secondary slots; `armor_base` never varies by rarity.
4. **Unchanged by construction:** mitigation curve `TAV/(TAV+K)`; NPC→player-only mitigation; both floors (reduction ≥ 1 when TAV > 0; ≥ 1 damage always lands); broken piece contributes nothing; `int(round(tav))`; the `stats` Armor row and `examine` confession display shapes.
5. **The `ARMOR_SLOT_WEIGHTS` table is deleted**, not kept in parallel. After this brief, the only armor authority is the field.

## 2. Version constant — opening act (standing requirement 1)

First implementation brief of the release: bump `SHYLAND_VERSION` from `24.8` to `"24.9-DEV"` in its own commit, moving the pin test's assertion in the same commit, then run the version-start `make deploy-dev` from the worktree.

## 3. Model + migration

File: `django/src/apps/shyland/models.py`, class `ItemDefinition`.

Add:

```python
armor_base = models.FloatField(
    default=0.0,
    help_text='Authored base armor per Mk tier (#129): TAV adds armor_base '
              'x mk_tier for every equipped, non-broken instance. 0 = '
              'authors no protection. Rarity-blind; rolled physical_resist '
              'is bonus on top.',
)
```

Migration step (required — model change): `make makemigrations APP=shyland && make migrate`. Commit the migration file.

## 4. Seed data — 18 armor definitions, in place

File: `django/src/apps/shyland/management/commands/seed_world.py`, `_seed_items`.

Add `'armor_base': <value>` to each armor definition dict, values below (each item's retired slot weight — **the table is authoritative over any prose**):

| Slug | Slot | `armor_base` |
|---|---|---|
| `leather-vest` | CHEST | 3.0 |
| `ballistic-jacket` | CHEST | 3.0 |
| `leather-cap` | HEAD | 2.0 |
| `leather-shoulders` | SHOULDERS | 1.0 |
| `leather-gloves` | HANDS | 1.0 |
| `leather-belt` | WAIST | 1.0 |
| `leather-leggings` | LEGS | 2.0 |
| `leather-boots` | FEET | 1.0 |
| `wooden-shield` | OFF_HAND | 2.0 |
| `patched-cap` | HEAD | 2.0 |
| `threadbare-vest` | CHEST | 3.0 |
| `mended-leggings` | LEGS | 2.0 |
| `scuffed-boots` | FEET | 1.0 |
| `frayed-gloves` | HANDS | 1.0 |
| `moth-eaten-shoulder-wrap` | SHOULDERS | 1.0 |
| `rope-belt` | WAIST | 1.0 |
| `oak-round-shield` | OFF_HAND | 2.0 |
| `quilted-jerkin` | CHEST | 3.0 |

No other definition gains the key (every non-armor definition keeps the model default 0.0). Definitions flow through the existing `_reconcile` enforce-exact path — this is an in-place definition update. **Expected deletion count: 0.**

## 5. Code rewire

### 5a. `django/src/apps/shyland/combat_utils.py`

- Delete the `ARMOR_SLOT_WEIGHTS` dict and its Option C comment block (lines ~10–18). Replace the comment with a v24.9 (#129) note stating the authored-base doctrine. `ARMOR_MITIGATION_K = 48` stays exactly as is.
- In `calculate_tav`, replace the slot-gated branch:

```python
if (item.definition.item_type == 'armor'
        and item.equipped_slot in ARMOR_SLOT_WEIGHTS):
    tav += ARMOR_SLOT_WEIGHTS[item.equipped_slot] * item.mk_tier
```

with the ungated field read:

```python
tav += item.definition.armor_base * item.mk_tier
```

(still inside the existing non-broken guard; the broken `continue` above it is untouched). The rolled `physical_resist` summation and the final `int(round(tav))` are untouched. Update the docstring's Option C reference to the authored field.

### 5b. `django/src/apps/shyland/consumers.py` — `examine` confession

- Remove `ARMOR_SLOT_WEIGHTS` from the `combat_utils` import (line ~19).
- Replace the slot-weight confession block (lines ~1729–1749): the gate becomes `defn.armor_base > 0` (not `item_type == 'armor'` — rule 2). The multi-slot differing-weights branch is deleted outright — the authored value is per-item and slot-independent, so the display is always the single form.
- Composition (shapes unchanged from the current single-weight form):
  - `Armor: {base} per Mk` where `{base}` renders integral values without a decimal (`3`, not `3.0`) — use `f'{defn.armor_base:g}'`.
  - Equipped and functional: append `(worn: {n})` with `n = defn.armor_base * item.mk_tier`, same `:g` formatting.
  - Equipped and broken/0%-durability: append `(worn: 0 — broken)` — verbatim current wording.

### 5c. Confirm no other read sites

`grep -rn 'ARMOR_SLOT_WEIGHTS' django/src/` must return zero hits after the rewire (tests included, per §6). The `stats` Armor row reads `calculate_tav` and needs no change — verify, don't modify.

## 6. Tests

File: `django/src/apps/shyland/tests/test_gear_combat.py` (and siblings that reference the table).

- **Conversion (test hygiene rule — literal pins on a deleted table):** the assertions `sum(ARMOR_SLOT_WEIGHTS.values()) == 13` and `ARMOR_SLOT_WEIGHTS['CHEST'] == 3` convert to seed-data assertions preserving the original intent: the 18 seeded armor definitions carry exactly the §4 table's `armor_base` values (assert each slug → value), one full set (one item per armor slot, Common Mk 1) still totals TAV 13 base, and chest pieces author 3.0. Report the conversion as a deviation-class note in the closeout (ruled conversion, not silent).
- **New tests:**
  - No slot gate: an equipped non-armor item with a nonzero `armor_base` contributes `armor_base × mk_tier` to TAV.
  - Default contributes nothing: `armor_base = 0` items add 0 base (TAV unchanged when equipped, physical_resist rolls aside).
  - Mk scaling: an Mk 2 instance of a 3.0-base definition contributes 6.
  - Broken: a 0%-durability piece contributes 0 base (existing broken tests keep passing).
  - Examine confession: `Armor: 3 per Mk` renders from the field; `(worn: …)` and `(worn: 0 — broken)` branches; a `armor_base = 0` item shows no Armor line.
- Any other test touching `ARMOR_SLOT_WEIGHTS` converts on the same intent-preserving basis.

## 7. Verification (gate for issue close and the architecture doc step)

1. Full in-container suite passes: `python manage.py test apps/shyland/tests` (directory-path form, via `docker exec` in the django container) — the only working invocation.
2. `grep -rn 'ARMOR_SLOT_WEIGHTS' django/src/` → zero hits.
3. Equivalence invariants (assert, not eyeball): full Common Mk 1 armor set → base TAV 13, `stats` row reads `Armor: 13 (blocks 21%)` (with no physical_resist rolls); naked → `Armor: 0`.
4. After the dev reseed (§8): all 18 armor `ItemDefinition` rows carry exactly the §4 values; every other definition reads `armor_base = 0.0`; ItemDefinition row count unchanged by the reseed (deletion count 0 against expected 0).

## 8. Deploy + data action (standing requirement 2)

Once implementation and verification pass: `make deploy-dev` from the worktree (code first), then `make seed` against the dev stack (data second). Re-run verification item 4 after the seed.

## PENDING DEPLOY-TIME ACTIONS

- **Production seed** (`make seed-prod`, bare, on its own operator confirmation) in the Version 24.9 closeout tail's deploy window, **after** `make deploy-prod` — code first, data second. Populates `armor_base` on the 18 production armor definitions per §4. Expected deletion count: 0. This block stays open until that execution; any subsequent brief/amendment in this version carries a pre-flight line reporting whether the dev-side action ran.

## 9. Operator playtest checklist (dev stack) — standing requirement 3

Ready after §8's `make deploy-dev` + `make seed`:

1. `stats` with a full Common Mk 1 armor set equipped: Armor row reads `Armor: 13 (blocks 21%)` (higher if pieces carry physical_resist rolls) — identical to pre-release.
2. `examine` an equipped Leather Vest: `Armor: 3 per Mk` with `(worn: 3)`; unequipped: no `(worn: …)` suffix.
3. `examine` a non-armor item (weapon, ring): no Armor line.
4. Break a piece (or admin-set durability 0): examine shows `(worn: 0 — broken)`; `stats` Armor drops by that piece's contribution.
5. Fight a familiar Mk 1 NPC armored: incoming damage indistinguishable from pre-release (structure, not balance).
6. Unequip everything: `Armor: 0`.

## 10. Architecture doc — final, gated step

This step is gated on all implementation and verification steps above being complete and passing.

`docs/shyland/Shyland_Architecture_v24.md`, updated in place: stamp → 24.9; the hash **moves** (architectural change — schema field plus TAV rewire) to this brief's implementation commit. Sections that change: the armor/TAV passages (Option C's derived table → authored `armor_base` doctrine, the §4/§5 equivalents of GDD §3.6) and the ItemDefinition schema listing. Add the Version 24.9 block to the header's version history per the v24.8 pattern.

## 11. Closeout

Closeout report: `docs/shyland/Shyland_V24.9_Brief_1_Closeout.txt` (Step 0 stub first, completed in place at session end). Include: actual-vs-expected deletion count (0), the §6 test conversion note, final commit hash, and the operator playtest disposition line. Close #129 (gated on the suite passing) with an implementation comment. End with "run the issues report".
