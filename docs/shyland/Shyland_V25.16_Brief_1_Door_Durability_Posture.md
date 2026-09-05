# Shyland V25.16 — Brief 1: Instance-Side Durability Posture at the Door

- **Release:** Version 25.16 (point release) — milestone `Version 25.16`
- **Branch:** `version_25_16`
- **Founding ticket:** #315 (sole milestone member — scope law: one founding ticket, one brief)
- **Authored:** 2026-09-05, V25.16 design session
- **Session type to apply this brief:** implementation session on `version_25_16`

## 1. What this release does

The agent door's `durability_current` edit maintains `is_broken = (value == 0)` unconditionally — including on an item whose definition is non-wearing (`takes_durability_loss=False`). A raw-set 0 on such an item produces the exact state the v25.12 durability-posture invariant exists to forbid: combat-disabled for real (broken instances contribute nothing to TAV and drop out of the composite strike), visually indistinguishable from healthy (every display cue is gated on the wearing definition), and unrecoverable by any in-game path (both repair paths filter on `takes_durability_loss=True`). The instance-side sibling of #311/#314, found in the V25.12 playtest.

**Operator ruling (2026-09-05, recorded on #315 — shape A):** the door **refuses `durability_current` edits on non-wearing definitions entirely** — the value is inert dormant data there; exact-or-refused, the `deduct_copper` posture, under `edit_item`'s standing whole-request semantics. **Flip-path sub-ruling (same conversation):** a wearing → non-wearing posture flip on an artifact definition **resets its instance to healthy** — `durability_current` 100, `is_broken` cleared — in the same atomic edit; authoring the non-wearing posture includes the instance. Wearing definitions keep the full edit unchanged.

GDD text landed with the design session (§6.5 instance-side invariant paragraph, §10.11 v25.16 passage — commit e6164a4, markers to be swept at closeout). Implementation never touches GDD source.

## 2. Technical premises — verified at writing time

Per the technical-coherence rule (#252), every claim below was **confirmed by file-read against `version_25_16` @ e6164a4** (code identical to the 25.15 merge tip 5bfa51e — the branch's only commits are docs) during the authoring session. The implementation session's pre-flight re-diffs these against the code before writing anything; a load-bearing mismatch is a HARD STOP.

1. **`_edit_instance_fields(item, changes)`** — `django/src/apps/shyland/mc_door.py:1081`–1130. The `durability_current` block (1113–1130): bool rejection + 0–100 range check, the #314 integral rule (`value.is_integer()` for floats), then `item.durability_current = float(value)` and — line 1130 — the unconditional `item.is_broken = (item.durability_current == 0)`. **`takes_durability_loss` is consulted nowhere in the function.**
2. **The whitelists** — `INSTANCE_EDIT_KEYS` (mc_door.py:1070–1073) includes `durability_current`; `ARTIFACT_DEFINITION_EDIT_KEYS` (1074–1078) includes `takes_durability_loss` and `durability_table`.
3. **`_edit_definition_fields(item, defn, changes)`** — mc_door.py:1133+. Its posture block (1234–1252) type-checks and applies both keys, then judges **post-edit state** through `durability_posture_violations(defn.takes_durability_loss, defn.durability_table)` (imported from `models` at mc_door.py:42), any violation ⇒ `DoorError('bad-params', ...)`. **The block never touches the instance** — no reconciliation on a posture flip.
4. **`_edit_item`** — mc_door.py:1255–1288: one `transaction.atomic()`; `_owned_item`; the whole-request whitelist scan (unknown key ⇒ `bad-params`, definition key on a non-artifact ⇒ `not-artifact`); **`_edit_instance_fields` runs before `_edit_definition_fields`** (1278–1280); `defn.save()` only when a definition key was present; `item.save()` always runs (1282); `rescale_bars_for_gear(char)` when the item is equipped; `ref` composed after the edit. `a_edit_item` (1291–1305) narrates `An admin has altered {ref}.` (category `system`, `refresh_status` when equipped) to an online holder; result `{'item_id', 'changed', 'definition_changed'}`.
5. **Instance fields** — `models.py:709`–710: `durability_current = models.FloatField(default=100.0)`, `is_broken = models.BooleanField(default=False)`.
6. **Artifacts are born non-wearing and healthy** — `_create_artifact` authors `takes_durability_loss=False, durability_table=[]` (mc_door.py:768–769); instance defaults are 100.0/False (premise 5). The reverse flip (non-wearing → wearing) therefore inherits healthy state by construction once this brief closes the damage paths.
7. **The reads really are gated** (the #315 diagnosis, re-confirmed): `total_armor_value` skips an item when `item.is_broken or item.durability_current == 0` (`combat_utils.py:154`–166 — **note the second disjunct: the raw 0 combat-disables even without the flag**, which is why step 4.4's normalization resets the value, not just the flag); the penalty/display paths gate on `defn.takes_durability_loss` before consulting durability (`item_utils.py:297`–298, 531–532; `consumers.py:1873`, 2580); both repair pools filter `definition__takes_durability_loss=True` (`consumers.py:3645` vendor repair, 4544 repair kits).
8. **Migration head is `0056`** (`0056_alter_itemdefinition_durability_table_and_more.py`); `0055_normalize_durability_posture.py` is the authored-data-migration precedent this brief's 4.4 follows (forward normalization with one UTC-Z-stamped count line, reverse noop).
9. **Bot-side schemas** — `agents/sudo_bot.py`: the `edit_item` tool's `durability_current` description reads "0-100, whole numbers only (fractional is refused); 0 marks the item broken." (509–513) and `takes_durability_loss`'s reads "Artifact definitions only; true requires a durability_table covering 0-100 (send both keys in one edit)." (543–548). Both are true today and become incomplete under this brief — the v25.12 playtest-found-gap lesson: the checklist drives sudo, so the schema mirror ships in the same brief.
10. **Test precedent** — `tests/test_v25_12_brief1.py` `DoorPostureTests`: the `_edit` helper (173–177) and `test_definition_edit_postures` (191–232), whose p1/p5 legs flip an artifact wearing and back. **p5 asserts `result['ok']` only — no instance-durability assertions — so it survives the flip reset unchanged.** Zero existing-test changes are expected from this brief; any needed change is a deviation, recorded in the closeout.
11. **Suite baseline:** 946 in-container tests green at the 25.15 closeout.

## 3. Design rules — do not deviate

- **Shape A is total:** every `durability_current` value — 0, 50, 100, all of them — refuses on a non-wearing definition. Not just 0.
- **The refusal is `DoorError('bad-params', ...)`**, message naming the rule and the state (the definition doesn't take durability loss; durability is not editable on it) and pointing at the two-request path for artifacts (flip the posture wearing first if a wearing, damaged artifact is the intent).
- **Judged on pre-edit posture.** `_edit_instance_fields` runs before the definition edit (premise 4) and stays there: a combined request on a non-wearing artifact that both flips wearing and sets durability **refuses** (pre-edit posture is non-wearing) — two requests, flip first. The reverse combination — wearing artifact, durability set + flip to non-wearing in one request — is accepted and **the flip reset wins** (it runs after the instance edit). Both semantics are deliberate, documented here, and test-pinned (4.6).
- **The flip reset is idempotent and posture-keyed:** it fires whenever a definition edit touched a posture key (`takes_durability_loss` / `durability_table`) and the **post-edit** posture is non-wearing — unconditional assignment of `durability_current = 100.0`, `is_broken = False`. Re-asserting non-wearing on an already-non-wearing definition also resets (harmless on a healthy instance; heals a stranded one).
- **No new narration, no new MC record shape, no new door vocabulary.** The refusal and the reset ride `edit_item`'s existing machinery (`An admin has altered {ref}.`, existing attribution) untouched.
- **Wearing-path behavior is byte-identical:** range check, integral rule, `is_broken` coupling — all exactly as shipped for wearing definitions.
- **No DB constraint attempt.** The instance-side invariant crosses tables (instance → definition); a `CheckConstraint` cannot express it. Enforcement is door-side plus the 4.4 normalization; the Django admin form's direct-ORM path remains the documented deliberate bypass (v25.7 residual-gap doctrine) — out of scope.
- **No seed change, no client change, no schema migration** — 4.4 is data-only; the model tables are untouched.

## 4. Implementation steps

Commit and push at every step boundary (branch only — never merge). Step 0 (closeout-report stub push) is owned by the `implementation-session` start ritual.

### 4.1 Version start (opening act — first brief of the release)

Bump `SHYLAND_VERSION` to `"25.16-DEV"` in its own commit, moving the pin-test assertion in the same commit. Then run the version-start `make deploy-dev` from the worktree.

### 4.2 Door: the shape-A refusal

In `_edit_instance_fields`'s `durability_current` block (mc_door.py:1113), before the existing value checks: when `item.definition.takes_durability_loss` is `False`, raise `DoorError('bad-params', ...)` per the design rules. (`item.definition` is loaded — `_owned_item` feeds the handler inside the atomic block; if the current query lacks `select_related('definition')`, the one extra definition fetch inside the transaction is acceptable and not worth restructuring.) The rest of the block — and line 1130's coupling, now reachable only under a wearing definition — stays byte-identical.

### 4.3 Door: the flip reset

In `_edit_definition_fields`'s posture block (mc_door.py:1234–1252), after `durability_posture_violations` passes: if the post-edit `defn.takes_durability_loss` is `False`, set `item.durability_current = 100.0` and `item.is_broken = False`. Persistence rides `_edit_item`'s existing `item.save()` (premise 4 — it always runs); an equipped target's bar rescale and `refresh_status` ride the existing `was_equipped` path.

### 4.4 Data migration: normalize stranded instances

Authored data migration **`0057_normalize_nonwearing_instances`** on the 0055 pattern: forward pass sets `durability_current = 100.0`, `is_broken = False` on every `ItemInstance` whose definition has `takes_durability_loss=False` and whose state differs — one UTC-Z-stamped count line ("normalized N non-wearing instances"); reverse noop. Without this, any already-stranded row (the #315 playtest is how one gets made) becomes permanently unfixable the moment 4.2 lands — for an ordinary item, definition edits refuse `not-artifact`, so the door would have no recovery path at all. **Expected dev count: 0 or 1** (the playtest item, if never repaired); actual reported in the closeout. Prod count lands in the closeout tail's deploy output (the 0055 precedent). Migration authored by hand (data migrations are authored; the never-hand-edit rule governs generated ones), committed like any migration.

### 4.5 Bot-side schema mirror

`agents/sudo_bot.py`, `edit_item` tool schema — the v25.12 lesson (a checklist that drives sudo against a rule the schema contradicts produces false failures):

- `durability_current` description (509–513) gains: wearing items only — refused when the definition doesn't take durability loss.
- `takes_durability_loss` description (543–548) gains: flipping to false resets the instance to healthy (durability 100, not broken).

No other bot change; no new tools; `_execute_tool` untouched.

### 4.6 Tests — `tests/test_v25_16_brief1.py`

New in-container tests (invocation: `python manage.py test apps/shyland/tests` via `docker exec` — the directory-path form, the only working form). Build on the `DoorTestBase`/`_edit` pattern of `test_v25_12_brief1.py`:

1. **Shape-A refusal, ordinary item:** non-wearing definition, instance owned — `durability_current: 0` refuses `bad-params`; so do `50` and `100` (shape A is total). Instance state unchanged after each (100.0/False).
2. **Whole-request atomicity:** `{'mk_tier': 3, 'durability_current': 0}` on the same item — whole request refuses; `mk_tier` unchanged.
3. **Wearing-path pin:** wearing definition — `durability_current: 40` accepted (40.0/False); `0` accepted and sets `is_broken=True`; a fractional value still refuses (the #314 rule intact).
4. **Flip reset, damaged:** artifact flipped wearing (posture pair + full table), instance edited to 40 — flip back to non-wearing accepted; instance reads 100.0/False.
5. **Flip reset, broken:** same shape with the instance at 0/`is_broken=True` before the flip — after: 100.0/False.
6. **Combined request, reset wins:** wearing artifact — one request `{'durability_current': 50, 'takes_durability_loss': False, 'durability_table': []}` accepted; instance ends 100.0/False.
7. **Combined request, pre-edit posture judges:** non-wearing artifact — one request `{'takes_durability_loss': True, 'durability_table': <full table>, 'durability_current': 50}` refuses `bad-params` (the two-request path is the documented shape); definition still non-wearing after (atomicity).
8. **Idempotent re-assert:** non-wearing artifact, instance hand-stranded via ORM (0/True — simulating pre-25.16 damage) — a definition edit re-asserting `{'takes_durability_loss': False, 'durability_table': []}` heals it to 100.0/False.
9. Full suite green: 946 + the new tests, zero existing tests changed (any needed change is a deviation, recorded in the closeout).

### 4.7 Dev deploy + issue close

`make deploy-dev` from the worktree once implementation and all verification pass (the deploy's migrate runs 0057 on dev — capture the count line). Restart the dev sudo bot **from this worktree's copy** of the fleet tooling (`agents/botctl.py dev restart` — self-locating: the copy you run is the checkout it manages) so the 4.5 schema mirror is live for the playtest. Then close **#315** (gated on verification passing), with a closing comment naming this brief and the release.

### 4.8 Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. `Shyland_Architecture_v25.md`, updated in place per the point-release rule:

- Stamp → **25.16**; **the header hash moves** (architectural change: door edit semantics + a data migration).
- Header version-note block: one new `> **Version 25.16 (point release)…**` entry in the established pattern.
- **§4.22** (the agent door): the v25.7 `edit_item` passage's `durability_current` clause (~line 1694: "maintaining `is_broken == (durability == 0)`") gains the posture gate — wearing definitions only, refused otherwise; the durability-posture paragraph (~line 1708) gains the instance-side extension: shape-A refusal, the flip reset, the pre-edit/post-edit combined-request semantics, and `0057`'s normalization.
- **§4.23** (the sudo bot): one sentence on the two schema-description updates (4.5).
- §4.22's title line gains the release reference in the established accretion style ("; the instance-side posture — v25.16 brief 1, #315").

### 4.9 Closeout report

`docs/shyland/Shyland_V25.16_Brief_1_Closeout.txt`, completed in place from the Step 0 stub: final commit hash, deviations, actual vs expected test counts, the 0057 dev count (actual vs the 0-or-1 expectation), and the **operator playtest disposition** line (the closeout session reads it as a gate).

## 5. Verification

1. Suite green in-container (path form), 946 + new, no existing test modified.
2. On dev, post-migrate: a shell query for stranded rows — `ItemInstance.objects.filter(definition__takes_durability_loss=False).exclude(durability_current=100.0, is_broken=False).count()` — returns **0**.
3. On dev, via the door test driver or shell: the shape-A refusal fires on a real non-wearing instance; a wearing item's durability edit still lands.
4. The 0057 migration's count line is present in the deploy-dev migrate output and recorded.

## 6. Operator playtest checklist (dev stack, after 4.7 — including the dev bot restart)

1. Ask sudo to set durability to 0 on a non-wearing item you own (a ring/accessory, or a fresh artifact — they're born non-wearing). Expect a polite relayed refusal naming the posture rule; the item's Details and combat behavior unchanged.
2. Ask sudo to flip an artifact to wearing (it must send the posture pair), set its durability to 40, confirm the `— 40% durability` suffix renders — then flip it back to non-wearing. Expect the suffix gone and, via sudo's `item` read, durability 100 / not broken.
3. Regression feel-pass: set a wearing item (starter kit gear wears) to 50 — suffix updates; to 0 — `— BROKEN` renders; repair it back via the normal vendor path.
4. Anything odd: file thin, normal pipeline.

## 7. PENDING DEPLOY-TIME ACTIONS

**No manual actions.** The `0057` data migration rides the closeout tail's standard `make deploy-prod` migrate step (**executor: `make deploy-prod`**); its prod normalization count lands in that deploy's output (expected: 0 — the stranded shape has only ever been produced on dev, but the count line reports the truth either way). Standing operator note, not a new action: the 4.5 schema mirror reaches production sudo only when the **operator** restarts the prod bot with post-25.16 code — the already-carried prod-bot-restart standing action absorbs this; door-side enforcement is live from the deploy regardless. (Any container restart bounces all three games — standard closeout-tail fact; in-session deploys bounce the dev stack only.)

## 8. Explicitly out of scope

- The Django admin instance form (`durability_current`/`is_broken` raw fields) — the documented deliberate direct-ORM bypass; a checklist step deliberately exercising it must say so (standing rule).
- Any DB-level instance-side constraint (cross-table — inexpressible as a `CheckConstraint`).
- Wearing artifacts as a design question (GDD §6.5: "a wearing artifact would be a future ruling of its own" — the door's mechanical flip capability is unchanged by this brief and implies no ruling).
- In-game repair paths for non-wearing items (there is deliberately nothing to repair once this brief lands).
- GDD changes: landed by the design session (e6164a4); the markers are closeout's to sweep.
