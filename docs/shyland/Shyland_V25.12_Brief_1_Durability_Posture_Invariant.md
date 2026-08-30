# Shyland V25.12 — Brief 1: The Durability-Posture Invariant

- **Release:** Version 25.12 (point release) · **Branch:** `version_25_12`
- **Founding ticket:** #311 (empty `durability_table` with `takes_durability_loss=True` — pristine items render yellow and fight fully penalized)
- **Dependencies:** #312 (admin cannot re-save ItemDefinitions with legitimately-empty JSON lists) and #314 (door `durability_current` edit accepts fractional values) — blocked-by recorded on #311 for both; all three close with this brief, gated on verification
- **Produced by:** the V25.12 design session, 2026-08-30. The operator confirmed the five-point fix shape in-conversation and ruled #314's integral rule into the release; rulings are recorded on #311, #312, and #314 (2026-08-30 comments/body).
- **GDD:** §6.5 gained "The durability-posture invariant" and "Hand-authored artifacts do not wear" at commit `151a562`, carrying the "(v25.12, pending implementation)" marker. Implementation sessions never touch GDD source; the marker is swept later by a design/closeout session.

This brief is self-contained: implement from this document and the repo only.

---

## 1. The problem

Every bot-created artifact definition inherits the model defaults `takes_durability_loss=True` + `durability_table=[]` — the broken pair. The penalty lookup's no-band-matched fallback (1.0) then treats a pristine item as fully degraded: the Details durability cell paints say-voice (yellow) and combat applies the full penalty (#311). The manual repair path was itself blocked: the Django admin cannot re-save any ItemDefinition whose JSON list fields are legitimately empty, because they lack `blank=True` (#312). The dev instance of the observed item (`Ludicrous Speed`) was already mitigated by the operator via the container shell (`takes_durability_loss=False`, table stays `[]`). A third face of the same coherence gap (#314, found during this design pass): the door's `durability_current` instance edit accepts fractional values that no seed band covers, silently drawing the same 1.0 fallback penalty.

## 2. Technical claims — verified at writing time (#252)

All claims below were verified against `version_25_12` @ `151a562` on 2026-08-30 by the design session (file reads, not recall):

- `django/src/apps/shyland/models.py` — `takes_durability_loss = models.BooleanField(default=True)` (line 512); `durability_table` (513), `primary_stats` (522), `secondary_stat_pool` (523), `valid_slots` (509) are all `models.JSONField(default=list)` with **no** `blank=True`; `ItemInstance.rolled_primary_stats` (621) and `rolled_secondary_stats` (622) likewise. `DialogueEntry.keywords` (1193) already carries `default=list, blank=True` — the in-repo idiom this brief extends. `LootTableEntry.rarity_weights` (754, `default=dict`) is deliberately **left required** (never legitimately empty — must sum to 100). `DEATH_DURABILITY_LOSS = 10.0` (line 12). **`ItemDefinition` currently defines no `clean()` and no `Meta`** — both are new additions, not edits.
- `django/src/apps/shyland/item_utils.py` — `get_durability_penalty` (line 333): returns `0.0` when `takes_durability_loss` is False; walks `definition.durability_table` for `entry['min'] <= pct <= entry['max']`; **returns `1.0` when no band matches** — with an empty table the fallback always fires. `details_cell` (line 522) derives the durability voice from it (`is_broken` → error, penalty > 0 → say, else value). `item_utils` imports from `models` (line 4) — so the shared validator must live in `models.py` to avoid an import cycle.
- `django/src/apps/shyland/mc_door.py` — `_create_artifact` (line 656) sets **neither** durability field in `ItemDefinition.objects.create(...)`, so every bot-created artifact definition gets the broken default pair. `_validate_artifact_spec` (line 518): the `allowed` key set contains no durability keys (and stays that way — artifacts don't wear). `INSTANCE_EDIT_KEYS` (985) and `ARTIFACT_DEFINITION_EDIT_KEYS` (989) contain no durability-definition keys; `_edit_item` (1143) refuses the whole request on any unknown key (line 1164) and gates definition-side keys to artifacts (`not-artifact`, 1156). The `mystery_name`/`mystery_description` coupling — validated at creation (623–633) and on **post-edit state** (1126–1139) — is the structural precedent this brief's coupling validation mirrors.
- `django/src/apps/shyland/management/commands/seed_world.py` — `WEAPON_DUR`/`RANGED_DUR`/`ARMOR_DUR` (lines 34–56) are five-band tables covering **every integer 0–100 with touching boundaries** (75 sits in both `[75,100]` and `[50,75]`; the reader resolves first-match). The pairing is universal and count-verified: **34** `takes_durability_loss': True` sites, each immediately paired with a named table; **21** `False` sites, each paired with `'durability_table': []` (e.g. the accessory ladder, lines 312–313) — 55 of 55 accounted for.
- Wear/repair arithmetic is integral on every game path: the only decrement is `DEATH_DURABILITY_LOSS` (`combat_utils.py:569`), repair kits restore `15 + 10 × Mk`, vendor repair sets `100.0` (`consumers.py:4513`), instances generate at `durability_current` default `100.0` (`models.py:627`). Fractional values are only reachable via the door's `durability_current` instance edit (`_edit_instance_fields`, the branch at ~1027): it accepts any non-bool number with `0 <= value <= 100`, stores `float(value)`, and maintains `is_broken = (durability_current == 0)` — so `0.5` matches no seed band, silently draws the 1.0 fallback penalty, renders `0%` (display rounds) yet is not broken. That is #314, ruled into this release.
- `Makefile` — `migrate` and `makemigrations` **docker-exec into the running container** (no rebuild); `makemigrations` then copies each app's container-side migrations directory back to the local filesystem. Source is baked into the image at build time — hence Step 3's explicit `make build` ordering below.
- Version constant: `django/src/apps/shyland/version.py:8` reads `SHYLAND_VERSION = "25.11"`; the pin test is `tests/test_b2_amendment1.py:118` (`assertEqual(SHYLAND_VERSION, '25.11')`).
- Latest migration: `0054_agentmemory.py`. `ItemDefinition` is admin-registered (`admin.py:165`).

## 3. Design rules — do not deviate

1. **Artifacts don't wear.** The door's artifact builder authors `takes_durability_loss=False, durability_table=[]` explicitly on every definition it creates. The artifact spec vocabulary gains **no** durability keys.
2. **The durability-posture invariant** (GDD §6.5): `takes_durability_loss=True` requires a durability table that **covers every integer 0–100**; `False` requires `[]`. Nothing between the two postures saves, anywhere.
3. **Coverage, not non-overlap.** Bands may touch or overlap (the seed's do); first-match-wins at read time is existing behavior — **do not change the reader**. Validation entry rules: each entry is a dict with exactly the keys `min`, `max`, `penalty`; `min`/`max` numbers with `0 ≤ min ≤ max ≤ 100`; `penalty` a number with `0.0 ≤ penalty ≤ 1.0`; booleans are not numbers.
4. **Three enforcement layers, one validator.** Model `clean()` (admin form), door-side validation on the new edit keys, DB `CheckConstraint` on the cheap core. All three route through one shared pure function.
5. **`get_durability_penalty`'s 1.0 fallback stays exactly as it is.** With the invariant enforced the state is unreachable; softening it would mask future misconfiguration.
6. **Durability is integral (#314, operator-ruled 2026-08-30).** The door's `durability_current` edit accepts only integral values: an `int`, or a float whose value is integral (`value.is_integer()` — JSON clients may deliver `42.0`); booleans remain refused; fractional values draw `bad-params` naming the rule. Stored value normalized to the integral float; range check and the `is_broken` invariant unchanged.
7. Whole-request edit semantics, artifact-only definition edits, and every other door behavior stay byte-identical outside the enumerated changes.

## 4. Implementation steps

Commit and push at every step boundary (branch only — never merge to main).

### Step 1 — Version start (standing requirement, opening act)

In its **own commit**: bump `version.py:8` to `SHYLAND_VERSION = "25.12-DEV"` and move the pin test (`tests/test_b2_amendment1.py:118`) to `'25.12-DEV'`. Then run `make deploy-dev` from the worktree (the version-start deploy).

### Step 2 — Models (`models.py`)

a. **The shared validator**, module-level in `models.py` (placement avoids the `item_utils` import cycle — verified above):

```python
def durability_posture_violations(takes_durability_loss, durability_table):
    """The v25.12 durability-posture invariant (#311, GDD 6.5).
    Returns a list of human-readable violation strings; empty = coherent."""
```

Pure function, no ORM. Rules exactly as §3.2/§3.3 above: `False` ⇒ table must be `[]`; `True` ⇒ table non-empty, every entry structurally valid, and every integer 0–100 inside at least one band. Violation strings name the rule broken (the legible-refusal house style).

b. **`blank=True`** added to exactly six fields, no other option changes: `ItemDefinition.valid_slots`, `.durability_table`, `.primary_stats`, `.secondary_stat_pool`; `ItemInstance.rolled_primary_stats`, `.rolled_secondary_stats`.

c. **`ItemDefinition.clean()`** (new method): call the validator; if violations, `raise ValidationError({'durability_table': violations})` — keyed to the field so the admin form renders the errors in place.

d. **`ItemDefinition.Meta`** (new class): `constraints = [models.CheckConstraint(condition=~models.Q(takes_durability_loss=True, durability_table=[]), name='durability_posture_coherent')]`. (`condition=` is the Django ≥5.1 kwarg name — the image installs the newest 5.x per `requirements.txt`'s `Django>=5.0,<6.0`; the old `check=` kwarg is deprecated. The repo has no prior CheckConstraint; the two existing `UniqueConstraint`s in `models.py` are the Meta-constraints precedent.)

### Step 3 — Migrations (order is load-bearing)

a. **First, the authored data migration** `0055_normalize_durability_posture.py` (a new authored file with `dependencies = [('shyland', '0054_agentmemory')]` — authoring a data migration is not the forbidden hand-editing of *generated* files). Forward, two normalizations, one UTC-stamped (trailing-Z) line each reporting its count; reverse: no-op (`migrations.RunPython.noop`):
   - **Definitions:** count then `ItemDefinition.objects.filter(takes_durability_loss=True, durability_table=[]).update(takes_durability_loss=False)`.
   - **Instances (#314 completing move):** any `ItemInstance` whose `durability_current` is non-integral is normalized to `float(int(round(value)))` — the display's own convention (`int(round(...))`) — with `is_broken` re-derived (`durability_current == 0`) in the same save.

   **Expected counts: 0 and 0 on dev** (the operator's shell mitigation already flipped the one affected definition; no fractional instance edit is known to have occurred); prod counts unknown-but-small — actuals reported in the closeout.

b. **`make build`** — load-bearing, not optional: `makemigrations`/`migrate` exec into the **running** container, whose source is baked at build time. Without this build the container carries neither the Step-2 model changes nor 0055; in-container generation would then number the new migration 0055 itself and the sync-back would land a colliding second 0055 locally.

c. **Then** `make makemigrations APP=shyland` → generates `0056` (the six `blank=True` option changes + `AddConstraint`; it will auto-depend on 0055 as latest). Never hand-edit 0056. Commit both migration files.

d. `make migrate` (dev). If the AddConstraint fails, that is a normalize-ordering defect — stop and investigate; never fake, reorder, or squash.

### Step 4 — The door (`mc_door.py`)

a. `_create_artifact`: add `takes_durability_loss=False, durability_table=[]` to the `ItemDefinition.objects.create(...)` kwargs (line 673 block).

b. `ARTIFACT_DEFINITION_EDIT_KEYS` (989): add `'takes_durability_loss'` and `'durability_table'`.

c. `_edit_definition_fields` (1039): handle the two keys — `takes_durability_loss` must be a boolean, `durability_table` must be a list (each a `bad-params` `DoorError` naming the rule if not); apply, then judge the coupling **on post-edit state** via `durability_posture_violations(defn.takes_durability_loss, defn.durability_table)`, mirroring the mystery-coupling structure at 1126–1139; any violation ⇒ `bad-params` carrying the violation text. Whole-request atomicity and the artifact-only gate come free from `_edit_item`'s existing structure — do not duplicate them.

d. **#314** — `_edit_instance_fields`, the `durability_current` branch (~1027): after the existing type/range check, require the value be integral (`int`, or float with `value.is_integer()`); fractional ⇒ `bad-params` naming the integral rule. Store the integral float as now; the `is_broken` derivation is unchanged.

### Step 5 — Tests (`tests/test_v25_12_brief1.py`, new file)

- **Validator:** `True`+`[]` fails; a gappy table (e.g. bands `[0,40]`+`[60,100]`) fails naming the gap; malformed entries fail (missing key, extra key, `min > max`, out-of-range values, boolean-as-number, non-dict entry); penalty out of `[0,1]` fails; **`WEAPON_DUR` passes verbatim** (touching boundaries legal); `False`+non-empty fails; `False`+`[]` passes.
- **`clean()`:** `full_clean()` on definitions in each illegal posture raises with the error keyed to `durability_table`; both legal postures pass.
- **Constraint:** `ItemDefinition.objects.create(...)` with `True`+`[]` raises `IntegrityError` (inside `transaction.atomic` in the test).
- **Door creation:** a definition created through `_create_artifact` reads `takes_durability_loss=False`, `durability_table=[]`.
- **Door edit (definition):** `True` + full seed-shaped table accepted; `True`+`[]` refused `bad-params`; `True`+gappy refused; `False`+non-empty refused; a mixed request containing one bad durability key still refuses the whole request (whole-request semantics intact).
- **Door edit (instance, #314):** `durability_current` of `42` accepted; `42.0` accepted (integral float); `55.5` refused `bad-params` naming the integral rule; `0` accepted and sets `is_broken`; the existing bool/range refusals unchanged.
- **Admin re-save (#312):** the admin model form for a seeded-shape non-wearing definition (empty table + empty stat lists + empty `valid_slots` where applicable) validates with no changes; an `ItemInstance` with empty rolled lists passes `full_clean()`.
- **No existing test is modified or weakened.**

### Step 6 — Full verification, then deploy

Run the full in-container suite — the only working form: `python manage.py test apps/shyland/tests` via `docker exec` in the django container. All green, then `make deploy-dev`, then the data checks in §5.

## 5. Verification (all steps must pass before #311/#312/#314 close)

| # | Check | Expected |
|---|---|---|
| 1 | Full in-container suite (path form) | all pass (existing suite + this brief's additions; zero modified tests) |
| 2 | Dev DB: `ItemDefinition.objects.filter(takes_durability_loss=True, durability_table=[]).count()` | `0` |
| 3 | Dev DB shell sweep: `durability_posture_violations(d.takes_durability_loss, d.durability_table)` over **all** definitions | zero violations, every row |
| 4 | Migrate output carries 0055's two UTC-stamped normalize lines (definitions, instances) | counts `0` and `0` on dev |
| 5 | Constraint live: shell `create(True, [])` inside an atomic block | `IntegrityError`, rolled back |
| 6 | Door path: artifact created via the door reads `False` + `[]` | exact |
| 7 | Dev DB: count of `ItemInstance` rows with non-integral `durability_current` | `0` |

The table is authoritative over any prose disagreement. Close #311, #312, and #314 only when all seven pass.

## 6. Operator playtest checklist (dev stack, after Step 6's `make deploy-dev`)

Steps 3–4 and 6 additionally require the **dev bot restarted on this release's code** (from the 25.12 worktree via `botctl`) — without it they cannot run and the disposition should say so.

1. Django admin → Item definitions → open a seeded non-wearing definition (any consumable, e.g. a Healing Draught) → **Save with no changes** → saves clean (previously blocked by three false "required" errors — the #312 fix).
2. Same form: set `takes_durability_loss` on, leave the table empty → Save → form error **on the durability_table field** naming the coverage rule; revert without saving.
3. Ask sudo to create a small test artifact → `inv`/`examine`: **no durability percentage** in the Details cell (rarity + binding only); the item fights unpenalized.
4. Ask sudo to edit that artifact: enable wear with a full five-band table → accepted; then enable wear with an empty table → refused, and the refusal names the rule.
5. `Ludicrous Speed` (the #311 item, already flipped non-wearing by the shell mitigation): confirm its inventory line shows **no durability cell and no yellow**.
6. (#314; bot required, target a carried **wearing** item, e.g. a weapon) Ask sudo to set its durability to `55.5` → refused, refusal names the integral rule; to `55` → accepted, item reads 55%.

## 7. PENDING DEPLOY-TIME ACTIONS

**None.** The normalize (0055) and schema (0056) migrations ride `make deploy-prod`'s migrate step in the closeout tail — **named executor: `make deploy-prod`**. 0055's two printed counts on prod appear in the deploy output; the closeout session records actual-vs-expected. Seed data is unchanged by this brief; no seed rerun.

## 8. Architecture doc update (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. `docs/shyland/Shyland_Architecture_v25.md`, updated in place:

- **Header:** stamp → 25.12; **the hash moves** (architectural change: model constraint + door vocabulary).
- **§4.1 (models):** the six `blank=True` fields, `durability_posture_violations`, `clean()`, the `durability_posture_coherent` constraint, migrations 0055/0056.
- **§4.22 (agent door):** creation-path posture (artifacts don't wear); the two new `ARTIFACT_DEFINITION_EDIT_KEYS` and their coupling validation; the `durability_current` integral rule (#314).
- **§4.7 (admin):** the empty-JSON-list re-save gap closed.
- **§8 (known issues):** adjust if the #311/#312/#314 behavior is listed there (check at update time).

## 9. Closeout report

Completed in place in the Step-0 stub (`.txt` in `docs/shyland/`): final commit hash, deviations (if any), 0055's actual-vs-expected dev counts (both normalize lines), and the operator playtest disposition verbatim-style (#170). This brief is the release's **first** implementation brief — Step 1 owns the `-DEV` bump; the closeout session stamps `25.12`.
