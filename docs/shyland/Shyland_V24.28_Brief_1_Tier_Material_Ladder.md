# Shyland V24.28 — Brief 1: The Tier-Material Ladder

**Release:** Version 24.28 (point release, V24 new-zone-prep major)
**Branch:** `version_24_28`
**Founding ticket:** #211 — *Silver accessory tier: Mk 2 jewelry needs the tier-material ladder extended (silver definitions + Mk-mismatch ruling)*
**Dependency:** #245 — *Tier-material ladder: rule its full extent (eight rungs, copper → sphaerium) and its unbounded terminal rung* (`#211 blocked by #245`)
**Milestone:** `Version 24.28`
**Design rulings:** recorded on #211 (initial ruling plus two amendments, 2026-08-14) and #245. This brief is self-contained — read it and the repo, nothing else.

---

## 1. What this release ships

Three things, one coherent change:

1. **Eighty-four new accessory ItemDefinitions** — the tier-material ladder's seven unshipped rungs (silver, gold, platinum, rhodium, iridium, osmium, sphaerium), each mirroring the v18 copper set exactly. The ladder totals **96 definitions** when done.
2. **Two new `ItemDefinition` fields**, `tier_material_mk_min` and `tier_material_mk_max`, binding a definition to its rung's tier range (migration `0048`).
3. **A hard Mk-mismatch guard in `generate_item_instance`** — a tier-material definition can no longer be instantiated outside its rung's range.

Every rung above silver is **prep work**: Z02 through Z08 do not exist yet, so all eighty-four definitions ship with **zero drop-table and zero vendor entries**. Seeding the ladder complete now means no future zone build has to stop and author jewelry before it can drop any — which is exactly what the V24 new-zone-prep major is for. The marginal cost is near zero because every rung is copper's curve under a different name.

**Out of scope — do not touch:** loot tables, vendor entries, combat math, valuation code, display/composition code, the command layer, the map, any shared surface (`apps/profiles/`, project settings, root URLs, `requirements.txt`, `docker-compose*.yml`, nginx, `Makefile`, base templates). No other game app.

---

## 2. Standing requirements

### 2.1 Version constant — opening act, its own commit

This is the **first implementation brief of the release**. Before any other work:

- `django/src/apps/shyland/version.py` — `SHYLAND_VERSION = "24.27"` → `SHYLAND_VERSION = "24.28-DEV"`
- `django/src/apps/shyland/tests/test_b2_amendment1.py:118` — the pin assertion `self.assertEqual(SHYLAND_VERSION, '24.27')` → `'24.28-DEV'`, moved **in the same commit**
- Commit these two changes alone, then run the version-start `make deploy-dev` from the worktree.

The closeout session bumps `24.28-DEV` → `24.28`. Do not do that here.

### 2.2 Dev deploy

Once implementation and verification pass, run **exactly `make deploy-dev`** from the worktree. Never hand-roll build + migrate. Never `make deploy-prod` — production deploys happen only in the closeout session's tail.

### 2.3 Test invocation

The only working form, run via `docker exec` in the django container:

```
python manage.py test apps/shyland/tests
```

The label form `apps.shyland` crashes on the `apps` namespace package; bare `manage.py test` discovers zero tests.

---

## 3. The model change

**File:** `django/src/apps/shyland/models.py`, class `ItemDefinition`, immediately after the existing `suppress_mk_suffix` field (currently at line 511).

```python
tier_material_mk_min = models.PositiveSmallIntegerField(
    null=True,
    blank=True,
    help_text='Lowest Mk tier this definition may be generated at. When set, '
              'this definition is a rung on the tier-material ladder '
              '(copper=1, silver=2, gold=3, platinum=4, rhodium=5, '
              'iridium=6, osmium=7, sphaerium=8). Null means the definition '
              'is not on the ladder.',
)
tier_material_mk_max = models.PositiveSmallIntegerField(
    null=True,
    blank=True,
    help_text='Highest Mk tier this definition may be generated at. Null with '
              'a set minimum means the rung is unbounded above — the '
              'sphaerium shape, covering every tier from its minimum upward. '
              'Meaningless unless tier_material_mk_min is set.',
)
```

**Also update the existing `suppress_mk_suffix` help text** — it currently claims the flag is "Used for tier-material items," which stopped being the whole truth when the v19 freebie kit adopted it, and is now actively wrong at the top of the ladder. Replace its help text with:

```python
help_text='If True, display names never show the "Mk N" suffix. '
          'Most tier-material items use this because the material already '
          'conveys the tier, but it is a display flag only and NOT ladder '
          'membership — see tier_material_mk_min. The freebie kit suppresses '
          'without being on the ladder; sphaerium is on the ladder and does '
          'not suppress, because its rung spans infinitely.',
```

**Migration:** run `make makemigrations APP=shyland` (never bare `makemigrations` — the enhanced target syncs generated files back to the local filesystem). Expected output: **`0048`**, two `AddField` operations plus an `AlterField` for the help-text change. Never hand-edit the migration; always commit it.

Existing rows take `NULL` for both — correct by construction, since only the seed authors ladder membership.

**Admin:** `django/src/apps/shyland/admin.py:172` currently groups `suppress_mk_suffix` under the `'Identification'` fieldset. Add both new fields to that same tuple, immediately after `suppress_mk_suffix`. No other admin change.

---

## 4. The guard

**File:** `django/src/apps/shyland/item_utils.py`, function `generate_item_instance` (currently line 95).

Insert the check as the **first statement in the function body**, before any rolling:

```python
lo = definition.tier_material_mk_min
if lo is not None:
    hi = definition.tier_material_mk_max
    if mk_tier < lo or (hi is not None and mk_tier > hi):
        bound = f'Mk {lo}' if hi == lo else f'Mk {lo}+' if hi is None else f'Mk {lo}-{hi}'
        raise ValueError(
            f'{definition.slug} is a tier-material definition bound to '
            f'{bound}; refusing to generate at Mk {mk_tier}. (#211)'
        )
```

Extend the function's docstring with one sentence recording the rule: a definition carrying `tier_material_mk_min` may only be generated inside its rung's range, because the material name *is* the tier display and any tier outside the range produces a name that lies.

**Why here and nowhere else.** Both live generation paths funnel through this function — `item_utils.py:322` (the loot-drop roll) and `consumers.py:4430` (`do_buy`, the vendor path) — so one guard binds them both, plus every shell and admin path that uses the helper.

**Known, deliberate residual gap — state it in the closeout, do not close it.** Constructing an `ItemInstance` directly through the ORM bypasses the guard. Do **not** add a `save()`-time or `clean()`-time check: a save-time guard would make any pre-existing mismatched instance unsavable, turning a naming defect into an unrepairable row (the scope law: leave no landmines). Generation is the choke point that matters; the V24.14 incident came in through generation.

---

## 5. The ladder's definitions

**File:** `django/src/apps/shyland/management/commands/seed_world.py`, the `accessories` list (currently opens at line 4665). Insert the eighty-four new entries **after the twelve copper entries and before the v19 freebie-kit entries** (`tarnished-band`, currently line 4887), grouped by material in ladder order, with a comment marking them as the v24.28 ladder build (#211, #245).

Eighty-four hand-written dicts is a lot of near-identical text. Generating them in the seed from a compact table — a materials table crossed with the stat table in §5.3 — is **permitted and preferred**, provided the resulting rows are byte-identical in effect to the copper set's authorship and every description is authored per §5.5 rather than templated. Do not restructure the copper entries to fit; leave them as they are.

### 5.1 The eight rungs — this table is authoritative

| Rung | Material | Slug prefix | `tier_material_mk_min` | `tier_material_mk_max` | `suppress_mk_suffix` | Status |
|---|---|---|---|---|---|---|
| 1 | Copper | `copper-` | 1 | 1 | `True` | shipped v18 — gains the range fields only |
| 2 | Silver | `silver-` | 2 | 2 | `True` | new |
| 3 | Gold | `gold-` | 3 | 3 | `True` | new |
| 4 | Platinum | `platinum-` | 4 | 4 | `True` | new |
| 5 | Rhodium | `rhodium-` | 5 | 5 | `True` | new |
| 6 | Iridium | `iridium-` | 6 | 6 | `True` | new |
| 7 | Osmium | `osmium-` | 7 | 7 | `True` | new |
| 8 | **Sphaerium** | `sphaerium-` | **8** | **`None`** | **`False`** | new — unbounded above |

**Sphaerium is the one rung that does not suppress the Mk suffix.** Its range has no ceiling, so the material alone cannot say the tier — a Mk 8 and a Mk 47 piece would render identically, which is the exact defect this release exists to remove. A sphaerium piece therefore reads `Sphaerium Ring of Strength Mk 15`. Do not "fix" this to match the other rungs; it is the ruling (#245).

### 5.2 Fields — identical for all eighty-four

| Field | Value |
|---|---|
| `item_type` | `'accessory'` |
| `genre_tag` | `'fantasy'` |
| `suppress_mk_suffix` | per §5.1 — `True` for rungs 1–7, **`False` for sphaerium** |
| `tier_material_mk_min` / `tier_material_mk_max` | per §5.1 |
| `scaling_base` | `2.0` |
| `scaling_factor` | `0.8` |
| `takes_durability_loss` | `False` |
| `durability_table` | `[]` |

`scaling_base` / `scaling_factor` are inert for accessories (only `item_type == 'weapon'` reads them in `generate_item_instance`) — they are authored anyway, mirroring the copper set exactly.

### 5.3 Stat authorship — the ruling's core

Every definition on the ladder carries **byte-identical stat authorship to its copper counterpart**, at every rung:

- `primary_stats`: `[{'stat': <stat>, 'base': 0.7, 'factor': 2.1}]` — Mk 1 midpoint 2.8, authored as the #130 full lift `(0.25, 0.75) × m1`
- `secondary_stat_pool`: two entries, each `{'stat': <stat>, 'base': 0.175, 'factor': 0.525}` — m1 = 0.7, same lift

Because `_roll_stat` computes `midpoint = base + factor × mk_tier`, this identical authorship yields 2.8 at Mk 1 (copper), 4.9 at Mk 2 (silver), 15.4 at Mk 7 (osmium), 17.5 at Mk 8 (sphaerium's floor) and 32.2 at Mk 15. Tier progression is already paid for by the engine, at every tier the ladder can name. **Do not invent per-rung midpoints** — that was considered and rejected on #211.

Rings take `valid_slots: ['RING']`; amulets take `valid_slots: ['NECK']`. The stat structure is identical between the ring and the amulet of the same stat, at every rung. **This table is authoritative:**

| Stat | Ring slug suffix | Amulet slug suffix | Primary | Secondary pool |
|---|---|---|---|---|
| Strength | `ring-of-strength` | `amulet-of-strength` | `str` | `dex`, `end` |
| Dexterity | `ring-of-dexterity` | `amulet-of-dexterity` | `dex` | `str`, `per` |
| Endurance | `ring-of-endurance` | `amulet-of-endurance` | `end` | `str`, `wis` |
| Intelligence | `ring-of-intelligence` | `amulet-of-intelligence` | `int` | `wis`, `dex` |
| Wisdom | `ring-of-wisdom` | `amulet-of-wisdom` | `wis` | `int`, `end` |
| Perception | `ring-of-perception` | `amulet-of-perception` | `per` | `dex`, `int` |

Full slug = material prefix + suffix, e.g. `sphaerium-amulet-of-wisdom`. Names follow `<Material> Ring of <Stat>` and `<Material> Amulet of <Stat>`, matching the copper set's capitalization exactly.

### 5.4 `base_value` — 30 at every rung

`base_value` is applied by the back-fill pass, not the definition dict. At `seed_world.py:4990-4993` the existing loop reads:

```python
for stat in ('strength', 'dexterity', 'endurance',
             'intelligence', 'wisdom', 'perception'):
    base_values[f'copper-ring-of-{stat}'] = 30
    base_values[f'copper-amulet-of-{stat}'] = 30
```

Extend it to an outer loop over all eight materials, leaving the value at **30** for every rung. Valuation multiplies by `mk_tier`, so a sphaerium piece at Mk 15 is worth 450 against copper's 30 at Mk 1 — the standard per-tier scaling every item type gets, and it keeps working at every tier above the ladder's named floor. **Do not price the rungs against the currency ladder** — considered and rejected on #211.

### 5.5 Descriptions — authored, not templated

Descriptions are authored at implementation time under the standing creative-content policy — not specified here, not reviewed line by line. The standard, which is not optional:

- **Each material gets its own physical opener per form** — fourteen new sentences in total (seven materials × ring/amulet), each carried consistently across all six stats of that form. The copper set's shape is the model: `'A plain copper band, faintly warm. …'` for rings, `'A copper pendant on a leather cord, faintly warm. …'` for amulets. Let the openers climb the ladder — copper is warm and plain; osmium should not be, and sphaerium should read as something that is not quite metal at all.
- **Each material authors its own stat clauses.** They may echo the copper set's shape (one clause, concrete, physical) but must not be verbatim copies of it. Escalating imagery as the rungs rise is encouraged, not mandated.
- **Sphaerium may allude to the spheres** — it is named for them, and the Primordial Sphere at the Heart is established world fiction. It may not name a zone that does not exist, invent sphere lore beyond what GDD §2 already establishes, or imply a mechanic the item does not have.
- No proper nouns otherwise, no lore names, no references to zones that do not exist.

### 5.6 Copper set gains its range

Add `'tier_material_mk_min': 1,` and `'tier_material_mk_max': 1,` to each of the **twelve copper accessory dicts**, immediately after their existing `'suppress_mk_suffix': True,` line.

**Do not add the keys to the freebie kit** (`tarnished-band`, `cloudy-glass-pendant`) — they keep `suppress_mk_suffix: True` and stay off the ladder at `NULL`. Un-overloading that flag is a deliberate part of this release, and sphaerium is why it matters.

**Do not add the keys to any non-accessory definition** in the `items` list — they rely on the migration's `NULL` default.

### 5.7 Seed verification additions

The seed's built-in verification pass gains five assertions, in the style of the existing checks:

1. Exactly **96** ItemDefinitions have a non-null `tier_material_mk_min` — **12 at each value 1 through 8**.
2. **Range shape:** for rungs 1–7, `tier_material_mk_max == tier_material_mk_min`; for rung 8 (sphaerium), `tier_material_mk_max is None`. Exactly one rung is unbounded.
3. **Suffix shape:** every definition on rungs 1–7 has `suppress_mk_suffix=True`; every sphaerium definition has `suppress_mk_suffix=False`.
4. For every rung, the twelve definitions' `primary_stats` and `secondary_stat_pool` are equal to the copper set's corresponding entries (the one-curve invariant, asserted at seed time as well as in tests).
5. **Drop and vendor entries respect the range:** every `LootTableEntry` whose `item_definition` is on the ladder has `mk_tier_min` and `mk_tier_max` inside that definition's range (for a bounded rung this means both equal the rung; for sphaerium it means both are ≥ 8), and every `VendorEntry` on a ladder definition has `mk_tier` inside the range. Vacuous for rungs 2–8 today — zero entries — and must hold for copper.

Assertion 5 exists because the drop path clamps to `entry.mk_tier_min`/`mk_tier_max` and the vendor path passes `entry.mk_tier` straight into `generate_item_instance` — a mis-authored entry would now raise at drop or purchase time rather than merely producing a wrong name. **If any assertion fails on the current seed, stop and report it — do not silently retune loot or vendor data.**

### 5.8 Expected reconciliation counts

`ItemDefinition` is seed-owned and swept by `_sweep_all`. Expected `make seed` reconciliation report for this release:

| Outcome | Expected count |
|---|---|
| ItemDefinition **created** | **84** (seven rungs × twelve) |
| ItemDefinition **updated** | **12** (the copper set gaining its range fields) |
| ItemDefinition **deleted** | **0** |

Report actual against expected in the closeout. **A nonzero deletion count means something off-seed is in the database — stop and report it rather than proceeding.** (Context, not an action item: the three off-seed silver clone definitions created directly on the dev DB during the V24.14 playtest are already gone — a prior reseed swept them, and `ItemInstance.definition` is `on_delete=CASCADE`, so the three Mk 2 instances went with them. Nothing is owed here. Note that those clones used `silver-` slugs; if any survive, the reconciliation will report them as *updated* rather than *created*, which is itself the signal to stop and report.)

---

## 6. Tests

New file `django/src/apps/shyland/tests/test_v24_28_brief1.py`:

1. **Schema pin** — both range fields exist on `ItemDefinition`, are nullable, and default to `None` on a definition created without them.
2. **Guard raises** — a definition with range 1–1 passed to `generate_item_instance` at `mk_tier=2` raises `ValueError`; the message names the slug, the bound, and the offending tier.
3. **Guard passes** — the same definition at `mk_tier=1` generates normally.
4. **Guard is inert off-ladder** — a definition with a null minimum generates at Mk 1, 2 and 5 without raising.
5. **Guard across the bounded rungs** — parameterized over rungs 1–7: each rung's definition generates at its own tier and raises at every other tier in 1–8.
6. **The unbounded rung** — a sphaerium definition raises at Mk 7 and below, and generates successfully at Mk 8, Mk 15 and Mk 200. This is the ruling's infinity property; pin it explicitly.
7. **Ladder completeness** — 96 definitions carry a minimum, twelve at each value 1–8; every expected slug from §5.1 × §5.3 exists.
8. **Range and suffix shape** — rungs 1–7 have `max == min` and `suppress_mk_suffix=True`; sphaerium has `max is None` and `suppress_mk_suffix=False`.
9. **One-curve equality** — for every rung and every stat, the ring's `primary_stats` and `secondary_stat_pool` equal the copper ring's, and likewise for amulets. This is the ruling's central invariant; pin it directly.
10. **Tier progression** — the primary midpoint (`base + factor × mk_tier`) computes to 2.8 at copper's Mk 1, 4.9 at silver's Mk 2, 15.4 at osmium's Mk 7, and 32.2 for a sphaerium instance at Mk 15.
11. **Display** — instances on rungs 1–7 render with **no** Mk suffix through `get_display_name_with_tier` in `item_utils.py`; a sphaerium instance at Mk 15 renders **`Sphaerium Ring of Strength Mk 15`**.
12. **Suppression is not membership** — `tarnished-band` and `cloudy-glass-pendant` have `suppress_mk_suffix=True` and a null minimum; sphaerium has a non-null minimum and `suppress_mk_suffix=False`. The two facts are independent in both directions.
13. **No drop or vendor exposure yet** — no `LootTableEntry` or `VendorEntry` references any ladder definition above rung 1.

Tests 7–13 read seeded data; follow whatever seeding pattern the existing suite uses for seed-dependent assertions.

**Existing suite:** 638 tests at the 24.27 stamp. Report the new total. If any existing test breaks, fix the cause, not the assertion — and if a literal-pinning test legitimately has to become a pool/shape assertion, preserve the original intent as an explicit assertion and record it as a deviation in the closeout.

---

## 7. Verification

Run in order; all must pass before the architecture-doc step and before closing #211 and #245.

1. `make makemigrations APP=shyland` produced exactly `0048`; the file is committed and unedited by hand.
2. `make deploy-dev` from the worktree completes (build + migrate).
3. `make seed` against the dev stack; the reconciliation report matches §5.8 **exactly** — 84 created, 12 updated, 0 deleted.
4. The seed's verification pass, including the five new assertions in §5.7, reports clean.
5. In-container suite green: `python manage.py test apps/shyland/tests` — report the total.
6. **Ladder query** — in `make shell`, confirm `ItemDefinition.objects.filter(tier_material_mk_min__isnull=False).count() == 96`, twelve at each minimum 1 through 8, and exactly twelve with a null maximum.
7. **Guard smoke** — in `make shell`: `copper-ring-of-strength` at `mk_tier=2` raises `ValueError`; `sphaerium-ring-of-strength` at `mk_tier=7` raises; the same at `mk_tier=47` returns an instance whose display name ends `Mk 47` and whose rolled `str` sits near 99.4 before rarity spread.
8. **Read-only mismatch survey (dev)** — count existing `ItemInstance` rows on a ladder definition whose `mk_tier` falls outside that definition's range. **Expected: 0.** This is a *report*, not a cleanup: if any rows exist, record the count and their slugs in the closeout and stop for a design ruling — do not delete or rewrite instance data.
9. No file outside `django/src/apps/shyland/` and `docs/shyland/` was modified (shared-surface check).

---

## 8. PENDING DEPLOY-TIME ACTIONS

**The production seed rerun.** The eighty-four new definitions and the copper set's range fields reach production only when the seed runs there.

- **Action:** `make seed-prod` — the sanctioned path (#187), invoked **bare**, on its own operator confirmation, in the closeout session's tail deploy window.
- **Order:** code first, data second — the deploy (`make deploy-prod`) runs the migration; the seed follows.
- **Expected production reconciliation:** ItemDefinition **84 created, 12 updated, 0 deleted** — identical to dev.
- **Expected production mismatch survey (verification step 8 repeated against prod):** **0 rows.** Copper accessories have only ever dropped in Z01 at Mk 1, and no character has been admin-gifted a mismatched instance on production.

This block stays open until that production execution. Every subsequent brief or amendment in this release must carry a pre-flight line reporting whether it has executed.

---

## 9. Architecture document

**This step is gated on all implementation and verification steps above being complete and passing.**

`docs/shyland/Shyland_Architecture_v24.md` — updated **in place** (point-release document rule; no new file, filename keeps the major-version name).

- **Header:** stamp → 24.28; **the commit hash moves** — this is an architectural change (new model fields, new generation guard).
- Add the `Version 24.28 (point release)` block at the top of the version blocks, in the established style.
- **§4.1 Models** — `tier_material_mk_min` / `tier_material_mk_max` documented including the unbounded-rung shape, and the `suppress_mk_suffix` entry corrected to describe it as a display flag independent of ladder membership in both directions.
- **§4.6 Item generation and utilities (`item_utils.py`)** — the range guard in `generate_item_instance`, including the deliberate residual gap (direct ORM construction is not guarded, and why).
- **§4.8 Seed data** — the eight-rung ladder, its 96 definitions, the copper set's range assignment, the `base_value` loop extension, and the five new verification assertions.

No other section changes. Do not touch GDD source — §6's ladder passage already landed with this release's design session (GDD-first); its `(v24.28, pending implementation)` markers are swept by the closeout session, not by this one.

---

## 10. Issue closure

Close **#211** (founding) and **#245** (dependency) once verification §7 passes in full. They are the release's only issues.

---

## 11. Operator playtest checklist — dev stack

Ready after `make deploy-dev`. All steps against the **dev** stack; production hosts no mid-version builds.

1. **Version reads 24.28-DEV.** Connect and run the command showing the version line (the stats/info sheet) — confirm `Version: 24.28-DEV`.
2. **The ladder exists and is inert.** In the Django admin, confirm all ninety-six ladder definitions are present across the eight materials, and that nothing above copper appears in any loot table or vendor list (it should not — Z02 through Z08 do not exist yet).
3. **Silver reads right in play.** Admin-gift yourself a `Silver Ring of Strength` **at Mk 2** and examine it. Confirm: the name reads `Silver Ring of Strength` with **no `Mk 2` suffix**, the flag block renders normally (`[Rarity, Bound|Unbound]`), and the strength value sits around **4.9** before rarity spread — visibly above what a copper ring gives.
4. **The last finite rung.** Admin-gift an `Osmium Amulet of Wisdom` **at Mk 7**. Confirm no Mk suffix, and a wisdom value around **15.4** before spread. This is also the read-through on the authored descriptions — the openers should feel like a ladder, not seven coats of the same paint.
5. **Sphaerium carries its number.** Admin-gift a `Sphaerium Ring of Strength` **at Mk 15**, then another **at Mk 200**. Confirm both succeed, both render **with** the Mk suffix (`Sphaerium Ring of Strength Mk 15`), and the strength values scale accordingly (~32.2 at Mk 15). This is the rung that has to work at any tier forever — try an absurd one on purpose.
6. **The lie is refused.** Attempt to admin-gift a **`Copper Ring of Strength` at Mk 2**, a **`Gold Ring of Strength` at Mk 2**, and a **`Sphaerium Ring of Strength` at Mk 7**. Confirm all three fail with the Mk-mismatch error rather than minting the item. Then gift a `Gold Ring of Strength` at **Mk 3** and confirm it works normally.
7. **Nothing else moved.** Play a short Z01 loop — kill something, take the loot, buy and sell at a vendor, equip and unequip an accessory. Confirm loot drops, purchases, and prices behave exactly as before; the copper accessories in particular should be unchanged in every respect.
8. **Freebie kit untouched.** Confirm the starter `Tarnished Band` and `Cloudy Glass Pendant` still render with **no** Mk suffix and are still equippable — they keep suppression without joining the ladder.

---

## 12. Closeout report

Commit as `docs/shyland/Shyland_V24.28_Brief_1_Closeout.txt`, opened as a stub at Step 0 and completed in place. Must include: the final commit hash, actual-vs-expected seed reconciliation counts (§5.8), the suite total, the dev mismatch survey result (§7.8), any deviations, the still-open **PENDING DEPLOY-TIME ACTIONS** block (§8), and the **operator playtest disposition** verbatim-style — *"Operator reports playtest successful"*, *"No playtests for this brief"*, or *"Operator deferring playtest"*.
