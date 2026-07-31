# Shyland V24.0 — Brief 1: The Draught Law

**Founding ticket:** #139 (Healing consumables can't track vitality growth — the draught tier needs an evolution pass) — ruled and `triaged` 2026-07-30; the full ruling is the comment thread on #139.
**Branch:** `version_24_0` · **Release:** Version 24.0, first release of the Version 24 (new-zone-prep) major.
**This is the FIRST implementation brief of the release** — the version-start ritual is its opening act (Step 1).

This brief is self-contained. Read it and the repo; no design conversation is needed.

---

## The ruled design (deviate from nothing here)

**The Draught Law:** a Healing Draught restores a percentage of the drinker's `vitality_max`, never a flat amount:

> **heal = ceil( (0.15 + 0.05 × Mk) × vitality_max ), minimum 25 HP** — then clamped at `vitality_max` as ever.

- Mk 1 = 20% — five drinks from zero to full at every level. The percentage is of **max, never of deficit**.
- **The Mk axis buys rounds, not raw HP.** Price scaling (`base_value × mk_tier`) is untouched; per-copper efficiency deliberately does not improve with tier. `base_value` stays 15.
- **The 25 HP floor** keeps every character at least as well off as the old `20 + 5×Mk`; it disengages once `vitality_max` exceeds 125 at Mk 1.
- **Rounding is `math.ceil`** — never Python's bare `round()` (banker's rounding; the #105 lesson).
- **Behavior explicitly unchanged:** the full-vitality refusal (#61), the single-message aggregate with consume-only-what's-needed (#151), oldest-first consumption (#168), vendor stock and prices, the Focus Tonic and every other effect. No HoT variant, no new items, no vendor changes.
- The old `restore_vitality` component type **remains in the vocabulary** (additive-only law); only the draught's seed component converts.

GDD authority: §6.9 "Percentage Healing — the Draught Law (v24.0, pending implementation)" — committed on this branch at `dd10a9f`. The marker is swept at closeout, never by this session.

---

## Step 1 — Version start (opening act, own commit)

1. Bump `SHYLAND_VERSION` to `"24.0-DEV"` (its pin-test assertion moves in the same commit).
2. Commit, push, then run `make deploy-dev` from this worktree (the version-start deploy).

## Step 2 — Model: the new component type

In `django/src/apps/shyland/models.py`, add to `COMPONENT_TYPE_CHOICES` (near line 327, beside `restore_vitality`):

```python
('restore_vitality_percent', 'Restore Vitality (percent of max)'),
```

**Migration required** (choices change): `make makemigrations APP=shyland && make migrate`. Commit the migration file. Expected: one migration, DB no-op (`AlterField` on `component_type` choices only).

## Step 3 — The law's constant and handler

- Add a named constant beside the regen constants in `models.py`: `VITALITY_PERCENT_HEAL_FLOOR = 25`.
- `django/src/apps/shyland/effect_utils.py` (~line 103, the `ctype == 'restore_vitality'` branch): add the sibling branch for `restore_vitality_percent` — `computed_magnitude(mk_tier)` yields the **fraction** (`magnitude_base + magnitude_scaling × mk_tier`, i.e. `0.15 + 0.05 × Mk`); heal = `max(VITALITY_PERCENT_HEAL_FLOOR, math.ceil(fraction * character.vitality_max))`, clamped at max exactly as the flat branch clamps.

## Step 4 — The use-path sites (the #151 aggregate machinery)

In `django/src/apps/shyland/consumers.py`, every site that keys on `component_type == 'restore_vitality'` must recognize the percent type as a healing component with the law's magnitude:

- ~1445–1456: the aggregate-eligibility detection (`any(c.component_type == 'restore_vitality' ...)`)
- ~1511–1548: the deficit/count math and per-item magnitude derivation — per-item heal computed by the law from **that item's Mk** and the **drinker's** `vitality_max`; mixed-Mk oldest-first accumulation logic is otherwise unchanged
- ~3168: the `component_type__in=('restore_vitality', 'hot_vitality')` tuple — add `'restore_vitality_percent'`

One shared helper for the law's arithmetic is preferred over three inline copies — `effect_utils` is its natural home; consumers import it.

## Step 5 — Seed data

In `seed_world.py` `_seed_effects()`, the Healing Draught component (the `_reconcile(EffectComponent, {'definition': healing_draught, 'order': 0}, ...)` block) becomes:

```python
'component_type': 'restore_vitality_percent',
'magnitude_base': 0.15,
'magnitude_scaling': 0.05,
```

(duration fields stay 0.0.) This is a reconcile-in-place update: **expected deletions 0; expected updated rows: exactly 1** (the draught's order-0 component).

## Step 6 — Tests

- Update any test pinning the old flat heal (25 HP at Mk 1 etc.) to the law's arithmetic — expected-value updates, reported in the closeout as a deviation only if a test's *intent* had to change.
- New law tests (in `apps/shyland/tests/`): percentage case at a large bar (e.g. max 718, Mk 1 → heal 144); floor case at a small bar (max 100, Mk 1 → heal 25, not 20); Mk scaling (same max, Mk 2 → 25%); full-vitality refusal unchanged; aggregate consume-only-what's-needed with the law's magnitudes; clamp at max.
- **In-container invocation (the only working form):** `python manage.py test apps/shyland/tests` via `docker exec` in the django container.

## Step 7 — Verification

All tests pass; then against the dev DB (after Step 8's deploy and seed):

1. The draught's EffectComponent row reads `restore_vitality_percent / 0.15 / 0.05`.
2. Shell check: a character at `vitality_max=718`, vitality damaged, drinking one Mk 1 draught heals exactly `ceil(0.20 × 718) = 144`.
3. A fresh-scale character (`vitality_max ≤ 125`) heals exactly 25 (floor engaged).
4. `use 3 healing draughts` at a deficit needing 2 consumes 2, one merged message (#151 shape unchanged).
5. Full-vitality drink attempt → the #61 world-declined refusal, unchanged wording.

## Step 8 — Deploy and data action (dev)

`make deploy-dev` from this worktree, then `make seed` against the dev stack (the component change requires the seed rerun to reach the DB). Code first, data second — this ordering is mandatory.

## PENDING DEPLOY-TIME ACTIONS (production — closeout tail only)

- **`make seed` on production** after the release deploys (Deployment Law step 6 window): converts the live draught EffectComponent to the percent law. Expected deletions 0; expected updated rows 1. Until then, this block stays open, and every subsequent V24.0 brief/amendment pre-flights whether the dev-side action ran.

## Step 9 — Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. This is the `N.0` release's brief, so per the Instructions' file-handling rule it **creates `Shyland_Architecture_v24.md`**: `git rm` the old `Shyland_Architecture_v23.md`, write the new doc header-first then one section at a time, carrying all v23 content forward unchanged **except**: the hash line moves (this brief is an architectural change), and the affected sections document the `restore_vitality_percent` component type and its law (formula, floor constant, ceil rule), the shared law helper's location, and the touched use-path sites. The release stamp itself (`24.0`) is the closeout session's; this doc carries the in-development lineage per header conventions.

## Step 10 — Operator playtest checklist (dev stack)

1. On a damaged high-level character: `use healing draught` → observe a ~20%-of-bar heal in one merged message with the `(+N Vitality)` parenthetical.
2. `heal`-style aggregate: `use 5 healing draughts` at a small deficit → only the needed count consumed.
3. On a fresh/low-level character: drink → +25 (floor).
4. At full vitality: drink refused, world-declined voice.
5. `help` shows version `24.0-DEV`.

---

**Closeout report:** standard `.txt` in `docs/shyland/`, final commit hash, deviations, the PENDING DEPLOY-TIME ACTIONS block, and the operator playtest disposition line (#170). Issue #139 closes gated on verification passing. End with the single instruction: **run the issues report.**
