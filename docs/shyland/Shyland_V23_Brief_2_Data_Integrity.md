# Shyland V23 Brief 2 — Data Integrity
**Type:** implementation brief (bucket B2 of Version 23)
**Branch:** the Version 23 worktree branch — all work, commits, and pushes on that branch
**Issues:** #137 (corpse decay orphans), #117 (stub tests.py breaks discovery), #18 (materials don't stack) — all three close with this brief, gated on verification
**Migrations:** ONE (`ItemInstance.corpse` `on_delete` change — AlterField, generated via `makemigrations`)
**Pending deploy-time actions:** this brief CREATES one (the orphan purge — see Step 7's PENDING DEPLOY-TIME ACTIONS block)
All three issues carry operator-confirmed design rulings recorded on the issues themselves (comments dated 2026-07-23 on #137 and #18; #117's body is its own ruling). Those rulings are reproduced in this brief verbatim where they are law. If any repo fact contradicts this brief, stop and record the contradiction in the closeout rather than improvising.
---
## Standing rules
- Work in the Version 23 worktree on its branch. Commit and push at every step boundary — branch only, **NEVER merge to main on your own initiative**.
- Never remove, prune, or clean up any transient document.
- Scope lock: exactly #137, #117, #18 as ruled. No redesign of loot, corpse decay timing, corpse messaging, inventory layout, command grammar, or sell/use behavior. Anything discovered beyond scope: file a thin issue (assigned `--assignee @me` per standing convention), cite it in the closeout, do not fix it here.
- If any step's verification fails, stop at that step, commit what exists, and write the closeout explaining — do not proceed to issue closes or the architecture doc.
## Pre-flight
1. Version 23 worktree, tree clean, branch synced with origin.
2. Confirm the branch HEAD is, or descends from, commit `4d3016d` (the operator's Version 23 branch-start commit). If not, STOP and report.
3. Deploy-time actions check (standing rule): report whether any prior Version 23 pending deploy-time actions exist. (At branch start none are known; this brief creates the version's first.)
4. `gh auth status` shows repo access.
5. This brief touches no deployment surface. The purge command it ships is executed by the operator at deploy time, not by this session.
## Step 0 — Self-commit this brief
Save this brief's full text verbatim to `docs/shyland/Shyland_V23_Brief_2_Data_Integrity.md` (skip the write if an identical file already exists). Commit on the branch and **push immediately**.
---
## Step 1 — #117: delete the stub `tests.py`
**The defect (from the issue, confirmed against the branch):** `django/src/apps/shyland/` contains both the untouched `startapp` stub `tests.py` (`from django.test import TestCase` / `# Create your tests here.`) and the real `tests/` package. unittest's file-based discovery sees `tests.py`, imports `apps.shyland.tests` (getting the package), and raises the "incorrectly imported" guard — so `manage.py test apps.shyland` cannot run and the suite has been invoked as `apps.shyland.tests` as a workaround ever since.
**The fix:** `git rm django/src/apps/shyland/tests.py`. Nothing else — the `tests/` package is untouched.
**Step 1 verification (required before proceeding):** whole-app discovery now works — `python manage.py test apps.shyland -t /app` (in-container, per established practice) discovers and runs the full suite green. **From this point on, this invocation is the brief's standard test command** — every later verification step uses whole-app discovery, which continuously re-proves this fix.
Commit and push.
---
## Step 2 — #137: corpse-content CASCADE, exactly-one invariant, self-verifying purge
**The ruling on #137 (operator-confirmed 2026-07-23) is the authoritative design direction. Its four parts, verbatim:**
> 1. **Vanish on decay.** Corpse contents do not outlive the corpse. Decayed loot is gone — no spill-to-ground. (Spill-to-ground remains available as a deliberate future feature; nothing in this fix forecloses it, since a spill would relocate items before corpse deletion.)
> 2. **CASCADE.** `ItemInstance.corpse` changes from `on_delete=SET_NULL` to `on_delete=CASCADE` (migration required). This makes the leak structurally impossible from any corpse-deletion path, not just the decay sweep. Rationale: corpse contents are by definition unowned, unequipped, unbound loot — unconditional destruction on corpse delete is always correct.
> 3. **Tighten the location invariant to exactly-one.** `ItemInstance.save()` currently rejects only more than one of owner/current_room/corpse being set; zero locations passes silently, which is what let this leak stay invisible. The check becomes exactly one. Implementation caveat (part of the fix, not optional): before tightening, verify that no legitimate transient zero-location state exists in any creation, transfer, loot, or drop flow — if one is found, STOP and report back to the design chat rather than working around it. The one-time purge (part 4) removes all currently-violating rows before the tightened check can encounter them.
> 4. **Purge with post-run verification.** One-time cleanup of existing orphans via a management command (pattern: `fix_zero_secondary_stats`). Filter is exact: `owner`, `current_room`, and `corpse` all NULL. The count is re-checked at run time, not assumed to be the 87 observed on 2026-07-22 — the leak is ongoing. The command must verify its own result: after the delete, it re-runs the orphan query and asserts a count of zero, reporting both the deleted count and the post-run count. The database must be provably clean at completion. This is a deploy-time data action: the implementing brief's closeout carries it in a PENDING DEPLOY-TIME ACTIONS block, and it stays an open verification item until its production execution — including the zero-count confirmation — is reported.
**Sequencing note from the ruling:** purge orphans → CASCADE migration → invariant tightening land together in this one brief; the decay-path behavior itself needs no code change beyond the migration (the existing `Corpse.objects.filter(pk=pk).delete()` in `delete_corpse`, `management/commands/run_tick_engine.py` ~line 742, becomes correct under CASCADE — Django's collector cascades the contents on ORM delete).
### 2a — The audit gate (do this FIRST, before any code change in this step)
Per part 3's caveat: audit **every** `ItemInstance` creation, transfer, loot, drop, buy, sell, gift, and equip/unequip flow (consumer, tick engine, item_utils, seed, admin) for any legitimate transient state where an instance is saved with zero of `owner` / `current_room` / `corpse` set.
- ⛔ **If any legitimate zero-location save exists in a game flow: STOP.** Commit the audit findings in the closeout, touch no invariant code, and report back to the design chat. Zero workarounds.
- If existing **tests** (not game flows) construct zero-location instances out of convenience, that is test hygiene, not a flow violation — fix those tests to set exactly one location and cite each fix in the closeout.
Record the audit's flow list and result in the closeout either way.
### 2b — The purge command
New file: `django/src/apps/shyland/management/commands/purge_orphaned_items.py`, in the mold of `fix_zero_secondary_stats.py` (BaseCommand, styled stdout reporting).
Behavior, exactly:
1. Query: `ItemInstance.objects.filter(owner__isnull=True, current_room__isnull=True, corpse__isnull=True)` — the ruled filter, exact.
2. Report the count found (do not assume 87 — the leak is ongoing).
3. Delete via the queryset (`.delete()` — never per-instance `save()`).
4. Re-run the same query. Report the post-run count. If it is not zero, exit with a `CommandError` — the command must prove the database clean at completion.
5. Idempotent: a second run finds zero and reports zero deleted, zero remaining.
### 2c — The migration
In `django/src/apps/shyland/models.py` (~line 571): `ItemInstance.corpse` `on_delete=models.SET_NULL` → `on_delete=models.CASCADE`. All other field attributes unchanged (`null=True, blank=True, related_name='contents'`). Generate the migration via `makemigrations` (AlterField); cite the generated migration number in the closeout.
### 2d — The invariant
In `ItemInstance.save()` (~line 578): the check changes from `if non_null > 1` to **exactly one** — `if non_null != 1: raise ValidationError(...)`. Update the message so it truthfully covers both directions (zero locations and multiple locations both name the count found; keep the "must be in exactly one location: owner, current_room, or corpse" wording, which is already correct).
Note: the CASCADE acts at the Django-collector level and never calls `save()`, so the migration and the tightened invariant do not interact; and the production orphans are never `save()`d by anything, so the tightened check shipping ahead of the production purge run is safe.
### 2e — Tests
New tests placed with the suite as found (a new `tests/test_data_integrity.py` is acceptable; cite placement in the closeout):
- **CASCADE:** create a corpse containing items; delete the corpse via the ORM (the same `Corpse.objects.filter(pk=pk).delete()` shape the tick engine uses); assert the contained `ItemInstance` rows are gone.
- **Invariant:** saving an instance with zero locations raises; with two locations raises; with exactly one (each of the three, individually) saves cleanly.
- **Purge:** construct orphan rows via a queryset `.update()` (bypassing `save()`, mirroring how production orphans exist); run `purge_orphaned_items` via `call_command`; assert the orphans are deleted, the output reports both counts, and a second run is a clean no-op. Assert non-orphan items (owned, on ground, in a corpse) are untouched.
**Step 2 verification:** full suite green via `python manage.py test apps.shyland -t /app`, including the new tests. `makemigrations --check` reports no missing migrations.
Commit and push.
---
## Step 3 — #18: material (and readable/key) stacking in inventory
**The ruling on #18 (operator-confirmed 2026-07-23) is the authoritative design direction.** Diagnosis from the ruling: inventory stacking exists and works — the grouping condition in `cmd_inventory` (`django/src/apps/shyland/consumers.py`, ~line 953 region) applies only to `item_type == 'consumable'`; materials fall through to one-row-per-instance. Command grammar, sell, and use are already stacking-agnostic per the ruled #22 resolution — **this is purely an inventory-display change. No grammar changes, no model changes, no migration.**
**The general stackability table (authoritative — the table wins over any prose or code that disagrees):**
| Stacks | Never stacks |
|---|---|
| consumable (already does) | weapon |
| material (the fix) | armor |
| readable | accessory |
| key | bag |
The rule behind the table: wear-free interchangeable types stack; per-instance-identity types (durability, rolled stats) never stack.
**The grouping key (ruled):** extends from (definition, mk_tier, rarity) to **(definition, mk_tier, rarity, soulbound state)** — preventing a bound copy (e.g. super-user gifted) merging with unbound copies. This deliberately also tightens the existing consumable stacking (a pre-existing hole the ruling closes); a bound and an unbound stack of the same consumable now render as two rows, which is correct.
### Implementation
In `cmd_inventory`:
1. Introduce a named constant for the stackable set — `STACKABLE_ITEM_TYPES = {'consumable', 'material', 'readable', 'key'}` (place it with the consumer's other display constants; use the `ItemDefinition` type constants if imports are clean, string literals otherwise — match local style). The grouping gate changes from `item.definition.item_type == 'consumable'` to membership in this set.
2. The grouping key becomes `(definition_id, mk_tier, rarity, is_soulbound)` — `is_soulbound` is the existing `BooleanField` on `ItemInstance` (models.py ~line 530).
3. **Adjacency guarantee:** the current grouping walks adjacent rows after a sort by display name only, so same-key items could interleave with different-key ties. Extend the sort key to `(display name lowercased, definition_id, mk_tier, rarity, is_soulbound)` — alphabetical-by-name remains the primary visible order; the trailing components exist only to make same-group rows adjacent.
4. A grouped row renders exactly as the existing consumable grouped row does today (representative = first instance of the group; Quantity = group count; Slot/Details cells unchanged in form). No other display change of any kind.
### Tests
Extend the suite where inventory display is already tested (or add to `tests/test_data_integrity.py`; cite placement):
- Multiple same-definition/mk/rarity/unbound **materials** render as one row with the correct Quantity.
- A **bound** copy does not merge with unbound copies of the same definition/mk/rarity (two rows).
- **Consumables** still stack (regression), and the bound/unbound split applies to them too.
- **Weapons** (or any right-column type) never stack even when definition/mk/rarity/bound state all match.
- `readable` and `key` stack (synthetic test definitions are fine if the seed lacks convenient ones).
**Step 3 verification:** full suite green via `python manage.py test apps.shyland -t /app`.
Commit and push.
---
## Step 4 — Full verification
1. Full suite green: `python manage.py test apps.shyland -t /app` (whole-app discovery — this is also #117's standing proof). Record the test count in the closeout.
2. `makemigrations --check` clean.
3. Invariant arithmetic: exactly one migration added by this brief; exactly one management command added; exactly one file deleted (`tests.py`); zero model fields added or removed (one field's `on_delete` changed).
---
## Step 5 — Close the issues (gated on Step 4 passing)
Close each with a short comment citing its ruling:
- **#117:** closed — stub deleted; whole-app discovery (`manage.py test apps.shyland`) is the standard invocation again. Note that prior briefs' "run as `apps.shyland.tests`" standing rule is retired as of this brief.
- **#18:** closed — stackable set extended to {consumable, material, readable, key} per the ruled table; grouping key now includes soulbound state. Display-only.
- **#137:** closed — CASCADE migration, exactly-one invariant, and `purge_orphaned_items` shipped per the four-part ruling. **The closing comment must state explicitly:** the production purge run is a PENDING DEPLOY-TIME ACTION — this issue's fix is not field-complete until the operator runs `purge_orphaned_items` on production after deploy and reports the deleted count and the zero-count confirmation.
Commit and push.
---
## Step 6 — Architecture document (GATED, last)
**This step is gated on all implementation and verification steps above being complete and passing.**
**File handling — check the repo state at this step and take exactly one path:**
- **If `docs/shyland/Shyland_Architecture_v23.md` does not exist** (no other Version 23 implementation brief has landed the doc yet): this brief creates it per the major-version convention. `git rm docs/shyland/Shyland_Architecture_v22.md`, create `docs/shyland/Shyland_Architecture_v23.md`. Write the **header first** (version 23.0, in progress; the header's commit hash records this brief's architectural changes; the header's brief narrative opens with this brief's entry in the established style), then copy content **one section at a time** from the v22 document — never one giant operation — applying the section changes below.
- **If it already exists:** update it **in place**, no version bump; the header hash moves (this brief's changes are architectural: a model change and a new command) and the header narrative gains this brief's entry.
**Section changes (either path):**
- **Section 1 (Overview) intro:** append the v23 opener/continuation sentence in the established narrative style: v23 Brief 2 (B2 Data Integrity, #137/#117/#18) — corpse contents CASCADE with the exactly-one location invariant and the one-time `purge_orphaned_items` command, the stub `tests.py` deleted restoring whole-app test discovery, and inventory stacking extended to all wear-free types with soulbound state in the grouping key.
- **Section 4.1 (Models):** `ItemInstance.corpse` documents `on_delete=CASCADE` (contents die with the corpse — #137) and the `save()` invariant documents **exactly one** of owner/current_room/corpse (zero and multiple both rejected).
- **Section 4.3 (Consumer):** the `cmd_inventory` description documents the stackable-types set {consumable, material, readable, key}, the never-stacks set {weapon, armor, accessory, bag}, the rule behind them (wear-free interchangeable stacks; per-instance-identity never), and the grouping key (definition, mk_tier, rarity, soulbound state) with the extended sort guaranteeing adjacency (#18).
- **Section 4.6 (item generation and utilities), where `fix_zero_secondary_stats` and `rename_proc_stats` are documented:** add `purge_orphaned_items` in the same style — one-time, self-verifying (post-run zero-count assertion, CommandError otherwise), idempotent, stays in the repo — with the deploy note: run once on production after this version deploys (#137).
- **Section 4.9 (Tick Engine):** the corpse-decay description notes that `delete_corpse`'s ORM delete now cascades the corpse's contents — decayed loot vanishes with the corpse, no orphans (#137).
- **Section 8 (Known Issues / Flags):** **remove** the "`tests.py` and `tests/` coexist" entry (resolved by this brief).
Commit and push.
---
## Step 7 — Closeout
Write `docs/shyland/Shyland_V23_Brief_2_Closeout_Report.txt` containing:
- What shipped per issue, the fix shapes, and the test count (suite green via whole-app discovery).
- The Step 2a audit: the flows examined and the finding (no legitimate zero-location state, or the STOP that halted the brief), plus any test-hygiene fixes made.
- The generated migration number; new-test placement.
- A dedicated **PENDING DEPLOY-TIME ACTIONS** block (standing rule), verbatim shape:
  ```
  PENDING DEPLOY-TIME ACTIONS
  - Run `python manage.py purge_orphaned_items` on production after this
    version deploys. The command reports the deleted count and asserts a
    post-run orphan count of zero. #137 is not field-complete until this
    execution — including the zero-count confirmation — is reported.
    Every subsequent Version 23 brief/amendment pre-flights whether this
    has executed, until confirmed done.
  ```
- Which architecture-doc path Step 6 took (created v23 vs updated in place).
- Any deviations or discrepancies.
- The **final commit hash**.
Commit and push. Do not remove or prune any documents.
## Step 8 — Final instruction
run the issues report
