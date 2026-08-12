# Shyland V24.23 — Brief 1: Percentage Bags

**Release:** Version 24.23 (milestone `Version 24.23`, branch `version_24_23`)
**Founding ticket:** #215 — Bags don't do enough: flat `carry_bonus` is noise against the STR-scaling capacity base
**Ruling of record:** the design ruling comment on #215 (2026-08-11, V24.23 design session). GDD §6.10 (with §6.11 and §3 references) carries the design text under a `(v24.23, pending implementation)` marker.
**Session type:** Implementation. This brief is the release's only brief and its **first** implementation brief.

---

## 1. Design summary (binding — do not deviate)

The equipped-bag contribution to carry capacity changes from a flat additive number to a **percentage of the STR-derived base**:

```
capacity = floor( effective_STR × 10 × (100 + Σ bag_pct) / 100 )
```

- `effective_STR` is the existing effective-stat read (base + gear) — unchanged (#100).
- Each equipped bag contributes `carry_pct_base + carry_pct_per_mk × mk_tier` percentage points, where `mk_tier` is the **instance's** Mk tier. Deterministic — no rarity roll; bags continue to have no rolled stats.
- Percentages from multiple equipped bags **sum into one multiplier, never compound**: two 20% bags → ×1.40, not ×1.44. (Only BACK exists today; the rule is pinned for the future hip slot.)
- Integer math: compute as `effective_str * 10 * (100 + total_pct) // 100` (floor).
- **Unchanged mechanics:** the cannot-unequip-a-bag-over-limit guard, BACK slot, bags never stack, the flat-pool inventory, the no-off-body-storage law.

### Authored values (seed — the table is authoritative)

| Definition (slug) | `carry_pct_base` | `carry_pct_per_mk` | Mk 1 | Mk 2 |
|---|---|---|---|---|
| `satchel` | 10 | 5 | 15% | 20% |
| `patchwork-satchel` | 5 | 3 | 8% | 11% |

Reference check (from #215's body): a level-17 character with effective STR 47 (base 470) and a Mk 2 Satchel gets `470 × 120 // 100 = 564` — +94 versus +20 today.

---

## 2. Standing requirements (v31 Instructions — never omit)

1. **Version constant — opening act.** This is the release's first implementation brief: bump `SHYLAND_VERSION` to `"24.23-DEV"` in `django/src/apps/shyland/version.py` as its own commit, moving the pin-test assertion in the same commit, then run the version-start `make deploy-dev` from the worktree.
2. **In-session dev deploy** — exactly `make deploy-dev`, run again from the worktree once implementation and verification pass (never hand-rolled).
3. **Operator playtest checklist** targeting the dev stack — Section 7 below, ready after the final `make deploy-dev`.

---

## 3. Model change (migration required)

File: `django/src/apps/shyland/models.py`, `ItemDefinition` (the `carry_bonus` field is at the `('Carry', ...)` admin fieldset / line ~453).

- **Rename** `carry_bonus` → `carry_pct_base` (`IntegerField`, `default=0`). Django's `makemigrations` should detect a rename — confirm the migration is a `RenameField`, not drop-and-add (no data worth preserving either way, but the rename keeps history clean).
- **Add** `carry_pct_per_mk` (`IntegerField`, `default=0`).
- Run `make makemigrations APP=shyland && make migrate` (the enhanced target syncs the migration file to the local filesystem). Commit the migration file.
- Update `admin.py`'s `('Carry', {'fields': ('carry_bonus',)})` fieldset to `('carry_pct_base', 'carry_pct_per_mk')`.

## 4. Capacity computation — one helper, all sites

Today four sites independently sum `carry_bonus` over equipped bags: `consumers.py` lines ~975, ~1414, ~3963 (`get_carry_capacity`), and ~4103. Centralize:

- Add one module-level helper (suggested home: `item_utils.py`) with signature shape `carry_capacity(character, equipped_items) -> int` implementing the Section 1 formula, plus a small `bag_pct(definition, mk_tier) -> int` used by displays. All four consumer sites call the helper; no site keeps a private copy of the formula. (`effective_stats` currently lives where the consumers already import it — keep the dependency direction clean; if importing into `item_utils` creates a cycle, the helper lives beside `effective_stats` instead. Placement is the implementer's call; **singleness is not**.)
- The unequip guard site(s) must use the same helper — the guard's question is "capacity without this bag," which the helper answers by being called with the reduced equipped list.

## 5. Displays

- `item_utils.py` line ~219: the bag info suffix `— +{defn.carry_bonus} carry capacity` becomes the percentage form for the **instance's** Mk: `— +{pct}% carry capacity` (e.g. `— +20% carry capacity`). The composition site has the instance in hand; use its `mk_tier`.
- `consumers.py` line ~1801 (examine detail block): `Carry bonus: +{defn.carry_bonus}` becomes `Carry bonus: +{pct}%` computed the same way.
- Inventory header carry count (`Inventory (12/250)`) needs no format change — the number simply comes from the helper.
- Unidentified items continue to show **no** carry contribution anywhere (GDD §6.7/§6.10 no-leak discipline) — verify no new site leaks it.

## 6. Seed (`management/commands/seed_world.py`)

- `satchel` (~line 4155): remove `'carry_bonus': 20`, add `'carry_pct_base': 10, 'carry_pct_per_mk': 5`.
- `patchwork-satchel` (~line 4435): remove `'carry_bonus': 10`, add `'carry_pct_base': 5, 'carry_pct_per_mk': 3`.
- Definitions reconcile in place keyed by slug (`_reconcile`). **Expected deletion count: 0 rows.** The closeout report states actual against expected.
- Run `make seed` against the **dev stack** in-session after `make deploy-dev` (code first, data second).

## 7. Tests

- New tests (new file `tests/test_v24_23_brief1.py`): formula floor behavior; Mk scaling (same definition, Mk 1 vs Mk 2 instance); multi-bag summing (construct two equipped bags even though only BACK ships — the helper takes an equipped list, so this is testable without a second slot); the reference case from Section 1 (STR 47 + Mk 2 Satchel = 564); unequip guard still refuses when removing the bag would overflow.
- **Test hygiene:** existing carry assertions in `tests/test_v24_16_brief1.py`, `tests/test_v24_11_brief1.py`, and `tests/test_gear_combat.py` pin the flat-bonus math and will need conversion to the percentage formula **with original intent preserved as explicit assertions** — every such conversion is reported as a deviation-class note in the closeout, never changed silently.
- Full suite must pass in-container. **Invocation (the only working form):** `python manage.py test apps/shyland/tests` via `docker exec` in the django container.

## 8. Verification (all steps must pass before issue close)

1. Migration applies cleanly on the dev stack (`make deploy-dev` runs migrate).
2. After dev reseed: both bag definitions carry the Section 1 authored values (shell check: `ItemDefinition.objects.filter(item_type='bag').values('slug', 'carry_pct_base', 'carry_pct_per_mk')`), and the reseed deleted 0 rows.
3. Shell check of the reference case or nearest live equivalent: a character's capacity equals the helper formula recomputed by hand; equipping/unequipping a bag moves capacity by the percentage, not a flat 10/20.
4. `inv` header, bag info suffix, and `examine` on a bag all show the percentage form; an unidentified bag shows none of it.
5. Unequip guard: with inventory filled above the bagless limit, `unequip` on the bag refuses.
6. Full in-container test suite passes (path-form invocation, Section 7).
7. Close #215 — gated on 1–6 passing.

## 9. Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. Update `docs/shyland/Shyland_Architecture_v24.md` **in place**: stamp → 24.23; this release is **architectural** (model field change + capacity formula), so the header hash **moves** to this release's implementation commit. Sections to touch: the item/inventory model reference (ItemDefinition fields) and the carry-capacity formula wherever stated. No other sections.

## 10. Closeout report

`docs/shyland/Shyland_V24.23_Brief_1_Closeout.txt` (stub created at Step 0 per the session ritual, completed in place): final commit hash; actual-vs-expected seed deletions (expected 0); test-conversion deviations (Section 7); **PENDING DEPLOY-TIME ACTIONS** block: production reseed (`make seed-prod`) in the closeout tail's deploy window — code deploys before the data action; and the **operator playtest disposition** line (required before session end: "Operator reports playtest successful" / "No playtests for this brief" / "Operator deferring playtest").

## 11. Operator playtest checklist (dev stack)

After the final `make deploy-dev` + dev reseed:

1. `inv` with a bag equipped — header capacity reflects the percentage (a Mk 2 Satchel reads +20% over your bagless number, not +20 flat).
2. `examine` the equipped bag — detail row shows `+20%`; the inventory line's suffix shows `— +20% carry capacity`.
3. `unequip satchel`, re-check capacity; `equip satchel`, re-check — the delta is exactly the percentage of your current bagless capacity.
4. Spend a level-up point on STR (or equip/remove a STR item) with the bag on — capacity moves with the base *and* the bag's share moves proportionally.
5. Fill inventory above the bagless limit, then try to unequip the bag — refusal, unchanged wording.

Issue-touching work ends with: **run the issues report.**
