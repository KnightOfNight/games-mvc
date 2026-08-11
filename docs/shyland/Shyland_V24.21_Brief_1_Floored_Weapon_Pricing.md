# Shyland V24.21 Brief 1 — Floored Weapon Pricing

- **Release:** Version 24.21 (point release)
- **Founding ticket:** #201 — Flame Projector / Dart Caster ship at default base_value 1 — pricing unruled
- **Branch:** `version_24_21`
- **Produced by:** Version 24.21 design session, 2026-08-11
- **Milestone:** `Version 24.21` (closes #201)

## Ruling being implemented (recorded on #201, 2026-08-05; release assignment 2026-08-11)

Authored `base_value` for the two floored-proc weapons (operator-confirmed):

- **Flame Projector: 85** — the two-handed ranged peer of the Hunting Bow (80): weaker direct damage but the strongest authored proc floor in the game earns a hair above the bow, staying below the 100 two-handed-melee ceiling (Broadsword / Battle Axe).
- **Dart Caster: 70** — slot-flexible one-hander like the Pulse Pistol (90) but well below its raw output, with the milder poison floor; lands between Iron Mace (65) and Hunting Bow (80).

**Premise correction (recorded on #201):** the pair does not currently sit at the model default `base_value = 1` — the type-wide back-fill (non-consumable/non-bag definitions without authored entries → 25) means they ship today at **25**. The fix is identical either way: two authored dict entries, which also removes them from the back-fill's reach (dict membership excludes a slug from every type-wide `.exclude(slug__in=base_values)` pass).

**Prior pending deploy-time actions:** none outstanding — Version 24.20 closed with an empty tail; nothing carries into this release.

## Design rules — do not deviate

1. Exactly **two entries** added to the `base_values` dict: `'flame-projector': 85` and `'dart-caster': 70`. No other seed change, no runtime code change, no model change.
2. The two ItemDefinitions' seed blocks (slugs, stats, floors, genre, slots) are untouched — this brief changes worth, not identity.
3. Value and sale-price arithmetic is untouched: `get_item_value` / `get_sale_price` in `item_utils.py` already produce the ruled prices from the authored `base_value`. Verify, never modify.
4. Existing item **instances** are not backfilled or touched: `base_value` lives on ItemDefinition, and value reads go through the definition at sale time — the reseed's `.update()` on the two definitions reprices every existing instance automatically. No instance migration, no data script.

## Implementation

**File:** `django/src/apps/shyland/management/commands/seed_world.py`, the `base_values` dict (currently lines 4815–4863).

Insert after the `'repair-kit': 15,` entry (currently line 4844), matching the in-file comment style:

```python
            # v24.21 (#201): the floored-proc pair — authored pricing
            # (ruled 2026-08-05). Listing here also removes them from the
            # type-wide 25 back-fill's reach.
            'flame-projector': 85,
            'dart-caster': 70,
```

The back-fill loop (`ItemDefinition.objects.filter(slug=slug).update(base_value=value)`) applies the numbers on every reseed; no other code change.

## Migrations

**None.** No model changes in this brief. State this in the closeout report.

## Standing requirements

1. **Version constant (first implementation brief of the release — opening act):** bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` from `"24.20"` to `"24.21-DEV"` in **its own commit**, moving the pin-test assertion (`django/src/apps/shyland/tests/test_b2_amendment1.py`, currently line 118: `self.assertEqual(SHYLAND_VERSION, '24.20')` → `'24.21-DEV'`) in the same commit. Then run the version-start `make deploy-dev` from the worktree.
2. **In-session dev deploy:** exactly `make deploy-dev` from the worktree once implementation and verification pass. Production is never deployed from an implementation session.
3. **Operator playtest checklist** targeting the dev stack — below.

## Dev-stack data action (code first, data second)

After the post-implementation `make deploy-dev` (code deployed), run **`make seed`** against the dev stack to apply the two authored values. **Expected deletion count: 0** — the change is two `.update()` entries; no seed-owned replacement table changes. The closeout reports actual against expected.

## Tests

**New regression tests** (new file `django/src/apps/shyland/tests/test_v24_21_brief1.py`, following the seed-data pin pattern of `test_band_lift.py`: `call_command('seed_world', stdout=io.StringIO())` in `setUpTestData`, then assert against the DB):

1. `ItemDefinition.objects.get(slug='flame-projector').base_value == 85`
2. `ItemDefinition.objects.get(slug='dart-caster').base_value == 70`
3. Derived-price pin through the real arithmetic (`get_item_value` / `get_sale_price` on a constructed Mk 1 Common instance of each): Flame Projector value 85, sale 28; Dart Caster value 70, sale 23.

**Existing tests:** no existing test pins the pair's `base_value` (verified at design time — the only `base_value` literals in tests are unrelated fixture helpers). If any test nonetheless fails on the repricing, convert the pinned literal to the ruled value with original intent preserved and report the change as a deviation in the closeout — never silently.

## Verification

All steps must pass before issue close and the architecture-doc step.

1. `grep -n 'flame-projector\|dart-caster' django/src/apps/shyland/management/commands/seed_world.py` shows the two new dict entries alongside the pair's existing definition blocks — and nothing else changed (`git diff` on the file is exactly the two entries plus comment).
2. Full suite green, in-container, path form only:
   `docker exec <django container> python manage.py test apps/shyland/tests`
3. `make deploy-dev`, then `make seed` (the dev-stack data action above), confirming the seed reports **0 deletions**.
4. Post-reseed DB check (dev, via `make shell`): `flame-projector` `base_value` = **85**, `dart-caster` = **70**.
5. Spot-check the derived prices on dev via the shell: a Mk 1 Common instance of each yields value/sale **85/28** and **70/23**; a Mk 2 Common yields **170/56** and **140/46** (`get_item_value` / `get_sale_price`).

## Issue close

Close **#201** once all verification steps pass, with a comment linking the implementing commit. Gated on verification passing.

## Architecture doc — last, gated step

This step is gated on all implementation and verification steps above being complete and passing.

`docs/shyland/Shyland_Architecture_v24.md`, updated **in place**:

- Stamp line: 24.20 → **24.21**. The **commit hash does not move** — this is a seed-data release, not an architectural change (v24.14 precedent).
- No section-content changes expected: the doc describes the base_value back-fill mechanism, not per-item numbers (verify at implementation time; if a passage is found pinning the pair's price, correct it and note it in the closeout).

## Closeout report

`docs/shyland/Shyland_V24.21_Brief_1_Closeout.txt` (stub created at Step 0, completed in place): final commit hash, migration statement ("none"), actual-vs-expected deletion count for the dev reseed (expected 0), any test-hygiene deviations, the operator playtest disposition line (#170), and the block below.

**PENDING DEPLOY-TIME ACTIONS (stays open until the production execution at release deploy):**

- Production seed rerun — `make seed-prod`, bare, in the closeout session's tail on its own operator confirmation (Deployment Law step 6; #187). Expected deletion count: **0**. Code first, data second: runs only after `make deploy-prod` has shipped the release.

## Operator playtest checklist (dev stack)

1. Acquire a **Dart Caster Mk 1 Common** and a **Flame Projector Mk 1 Common** on a test character (loot, or admin gift / the stock-playtest-items path — both weapons must be **unbound**: never equipped, since sell excludes equipped and refuses bound).
2. `sell` the Dart Caster → the sentence reports **23 copper** of payment (rendered by the standard tier formatter, e.g. `2 silvers, 3 coppers`; local zone aliases may rename the denominations).
3. `sell` the Flame Projector → **28 copper** (e.g. `2 silvers, 8 coppers`).
4. Confirm an unchanged peer as a control: selling an unbound **Iron Mace Mk 1 Common** still pays **21 copper** (base 65, unchanged).

## End

This brief touches issue state (#201 closes). End the session per ritual: run the issues report.
