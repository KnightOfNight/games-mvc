# Shyland V24.29 — Brief 1: The `plunder` Setting and the Verification Harness

**Release:** Version 24.29 · **Branch:** `version_24_29` · **Milestone:** `Version 24.29`
**Founding issue:** #235 (plunder) — closed by this brief
**Related ticket:** #250 (`_set_echo_mode` writes the wrong cached attribute) — closed by this brief; ruled in by the operator as emergent
**Riding issue:** #249 Part 2 (the read-only verification harness) — **NOT closed by this brief**; it stays open for its Part 3
**Session type:** implementation. Design is settled; this brief invents nothing.

---

## 1. What this brief ships

Two things, deliberately bundled by the #249 ruling ("no dedicated release for a base class; it piggybacks"):

1. **`plunder [on|off]`** — a new settings command, default off, that runs the rights-scoped corpse sweep automatically at the moment combat ends. Founding ticket #235.
2. **The forced-rollback verification harness plus `verify_ladder`** — the in-container half of `make verify-prod` (#249 Part 2). The Makefile target and its guard hook already shipped on main (Part 1, `28db69e`) and are live but inert; this brief gives them their first command to run.
3. **The #250 one-line fix** — `_set_echo_mode` assigns the wrong cached attribute. Found by this release's design session while specifying `plunder`'s setter, and ruled into this brief by the operator as emergent: it sits in the exact family §4 extends and is the template a developer would copy.

**Out of scope, explicitly.** Typed `loot` behavior does not change in any observable way. No new loot capability, no new faucet, no rights-model change, no change to corpse decay. No other pre-existing setter is touched. No GDD source edits — §5 and §9 text landed with this release's design session (GDD-first) and its `(v24.29, pending implementation)` markers are the closeout session's to sweep, not yours.

---

## 2. Step 0 — verify and signal

1. Confirm this brief exists verbatim at the branch tip. Whitespace-only drift is report-and-accept.
2. Create `docs/shyland/Shyland_V24.29_Brief_1_Closeout.txt` as a **stub** — one line recording date, brief name, branch. Commit it and **push immediately**. That push is the work-has-started signal.
3. The stub is completed in place at the end (§13).

**Pre-flight line on prior deploy-time actions:** V24.28's PENDING DEPLOY-TIME ACTIONS block is **closed** — `make seed-prod` executed in the V24.28 closeout tail on 2026-08-15 (prod reconciliation 84/12/0, matching dev exactly). Its one unexecuted item, the prod-side mismatch survey, was handed to the operator with no sanctioned path and is precisely what this brief's `verify_ladder` finally makes runnable. Nothing else is pending.

---

## 3. Opening act — the version constant

**This is the first implementation brief of the release, so this is its opening act, in its own commit, before anything else.**

- `django/src/apps/shyland/version.py` — `SHYLAND_VERSION = "24.28"` → `SHYLAND_VERSION = "24.29-DEV"`.
- `django/src/apps/shyland/tests/test_b2_amendment1.py:118` — the pin assertion `self.assertEqual(SHYLAND_VERSION, '24.28')` → `'24.29-DEV'`. It moves in the same commit.
- Then run `make deploy-dev` from the worktree (the version-start deploy).

The closeout session bumps it to `24.29`. Do not touch it again.

---

## 4. The `plunder` setting

### 4.1 The model field

`django/src/apps/shyland/models.py`, on `Character`, alongside `brief_mode` / `show_timestamps` / `echo_mode`:

```python
plunder_mode = models.BooleanField(default=False)
```

Exact name, exact type, exact default. Place it adjacent to the other three so the settings family stays together, with a short comment naming v24.29 and #235 in the house style.

### 4.2 The migration

`make makemigrations APP=shyland` — must produce exactly **`0049`**, one `AddField`. Commit it unedited by hand. If the generated number is not 0049, stop and report: something else has landed on the branch.

### 4.3 The command handler

`django/src/apps/shyland/consumers.py`, in the settings block next to `cmd_brief` / `cmd_echo`:

```python
async def cmd_plunder(self, args):
    value = await self._cmd_setting(
        args, 'plunder', 'plunder', 'is',
        lambda c: c.plunder_mode, self._set_plunder_mode,
    )
    if value is not None:
        self.character.plunder_mode = value
```

The shared `_cmd_setting` helper already delivers the whole settings standard — bare form reports, six accepted words set, invalid input answers `Usage: plunder [on|off]` in error-color, confirmations in `system`. Do not reimplement any of it.

**The subject/verb pair is `('plunder', 'is')`**, producing `plunder is off.` (bare) and `plunder is now on.` (set). The other three settings name a *thing* ("brief room display", "command echo", "output timestamps"); plunder's subject is the setting's own name because there is no separate noun for it — the command names the behavior directly.

### 4.4 The setter

Alongside `_set_brief_mode` and friends, written out here in full so there is no pattern-matching involved:

```python
@database_sync_to_async
def _set_plunder_mode(self, value):
    Character.objects.filter(pk=self.character_pk).update(plunder_mode=value)
    self.character.plunder_mode = value
```

Note that the setter writes the DB row **and** the cached attribute, and `cmd_plunder` (§4.3) also assigns the cached attribute after the setter returns. That belt-and-braces duplication matches `cmd_brief`'s shape and is deliberate; leave both.

### 4.5 The #250 fix — `_set_echo_mode`

Immediately above the new setter, `_set_echo_mode` assigns the wrong cached attribute:

```python
@database_sync_to_async
def _set_echo_mode(self, value):
    Character.objects.filter(pk=self.character_pk).update(echo_mode=value)
    self.character.show_timestamps = value      # <-- wrong field
```

The DB write is correct; the in-memory line names `show_timestamps` where it means `echo_mode`, so every `echo on` / `echo off` silently corrupts the cached `show_timestamps`. It is latent today — the connect-time `verbs` payload (`:498`) reads that attribute before any command can dirty it, and `_status_payload` (`:3450`) reads a fresh DB fetch — but it is a wrong-attribute assignment in the family this brief extends.

**Fix: delete the stray line entirely.** Do not "correct" it to `self.character.echo_mode = value` — `cmd_echo` already does exactly that after the setter returns, so the line is redundant as well as wrong, and deleting it makes `_set_echo_mode` match `_set_brief_mode` and `_set_show_timestamps`, which write only the DB row.

Keep this in **its own commit**, referencing #250, so an unrelated one-line fix is not buried inside the plunder work.

### 4.6 The five registration sites

A settings command is registered in five places. All five, or the command is half-alive:

| # | Location | Change |
|---|---|---|
| 1 | `consumers.py` `COMMAND_TABLE` (~:285) | `'plunder': ('cmd_plunder', True),` — takes args, alongside `'echo'` |
| 2 | `consumers.py` `DYING_ALLOWED` (~:339) | add `'plunder'` to the `'brief', 'echo', 'timestamps'` line |
| 3 | `consumers.py` `HELP_SECTIONS` Settings block (~:1205) | `('plunder', 'plunder [on|off]', 'Automatically loot your kills when combat ends. Default: off.')` — alphabetical, between `echo` and `timestamps` |
| 4 | `consumers.py` tab completion (~:3683) | `if head in ('brief', 'echo', 'plunder', 'timestamps'):` |
| 5 | GDD §9.1 chart | **already done** by the design session — do not edit GDD source |

**Not** added to `COMBAT_BLOCKED`: all settings are allowed in combat by the state-gating matrix, and plunder is no exception. Flipping it mid-fight governs that same fight, because the setting is read at combat end.

The connect-time `verbs` payload derives from `COMMAND_TABLE` automatically — no separate edit.

---

## 5. Extracting the sweep

**This is the load-bearing structural change. Read it before writing any code.**

The sweep lives at `consumers.py::_loot_sweep` as a method on `SkylandConsumer`: it awaits `self.output(...)` and consumer-bound `@database_sync_to_async` helpers (`get_carry_counts`, `get_corpse_contents`, `do_loot_item`, `check_corpse_empty_and_delete`, and `_loot_corpse_copper`'s `do_loot_copper`). The plunder trigger fires in **`run_tick_engine.py`** — a different process, with no consumer, and per §6.4 sometimes with no connected player at all. The consumer method cannot be called from there.

**Required shape:** extract the sweep into a transport-agnostic helper that performs the mutations and **returns** the messages rather than sending them.

- **Home:** a new module `django/src/apps/shyland/loot_utils.py`, in the style of the existing `item_utils.py` / `combat_utils.py` / `effect_utils.py`.
- **Signature:** a synchronous function taking `(character, room, lootable_corpses)` and returning an **ordered list of `(text, category)` tuples** — exactly the lines the current `_loot_sweep` emits, in exactly the current order. Synchronous, so both callers wrap it as they already wrap ORM work.
- **Behavior preserved byte-for-byte:** per-corpse coin line (`reward`), per-item loot lines (`reward`) composed through `compose_item_line`, the carry-capacity refusal (`warn`) with its `(N/M items)` count and the early stop it causes, the empty-corpse disposal call, and the closing summary (`system`) including the `; N carried nothing worth taking.` clause and its singular/plural handling.
- **Both callers use it.** `_loot_sweep` becomes a thin wrapper: call the helper (wrapped for async), then `await self.output(text, category)` for each returned tuple, in order. The tick engine appends the same tuples to its message accumulator (§6.2).

**Do not change the rights predicate, the corpse ordering, the message text, the categories, or the order of operations.** This is a move, not a redesign. If preserving behavior exactly requires the helper to take an extra collaborator (e.g. the zone slug for `display_for_zone`), pass it in — do not reach for consumer state from inside the helper.

**The regression bar:** every existing test touching `loot`, `loot all`, and the sweep must pass unchanged, without being edited. If an existing test needs editing to accommodate the extraction, the extraction is wrong — stop and report it as a deviation rather than adjusting the test.

---

## 6. The plunder trigger

### 6.1 The rule

**Plunder fires wherever `Combat has ended.` is delivered to a character, and nowhere else.** That line is emitted from exactly three sites in `run_tick_engine.py`, all firing on the same condition — no living NPCs remain in the session:

| Site | Line (approx.) | Case |
|---|---|---|
| A | ~311 | Loop-head self-heal close — session holding no living NPCs (#218's path) |
| B | ~663 | An M2M sibling session emptied by someone else's kill |
| C | ~685 | The killer's own session emptied by its last kill |

All three get the plunder hook. This anchoring is the whole trigger rule; do not invent a separate condition.

**It excludes flee and death for free, and that is by design:** flee's end path is in `consumers.py` and emits no `Combat has ended.` line, and a dying character is removed from its session before the session can close. Do not add explicit flee or death guards — the anchor already handles them, and an extra guard is a second source of truth. **Verify** both exclusions by test (§9), don't code around them.

### 6.2 What the hook does, per character

For each character receiving `Combat has ended.`:

1. Read the character's `plunder_mode`. If false, do nothing further.
2. Find lootable corpses in that character's current room: the room's corpses filtered to `corpse.killed_by_id == character.pk` — **the same predicate bare `loot` uses**, not a variant.
3. If the list is empty, **emit nothing at all** and stop. This is the silence contract (§6.3).
4. Otherwise call the §5 helper and append its returned tuples to the engine's message accumulator for that character, **after** the `Combat has ended.` line and after any level-up lines already queued for that character.

The engine's accumulator is already `(char_pk, text, category, status)`; the helper returns `(text, category)`, so each becomes `(char_pk, text, category, None)`. Status refreshes are already queued by the surrounding close paths — do not add another.

Ordering is not cosmetic: the transition is announced, *then* its consequence.

### 6.3 The silence contract — ruled, and testable

**Plunder is silent unless it plunders.** With no corpses in the room, or no corpses this character has rights to, plunder emits **nothing whatsoever**.

The typed command's refusals — `There is nothing to loot here.` and `That is not your kill; you may not loot it.` — belong to `cmd_loot` and must never be spoken on plunder's behalf. Structurally this means the hook filters *before* calling the helper (step 2/3 above) and never routes through `cmd_loot`.

### 6.4 Disconnected players

Plunder does not require a connected player. Quit is allowed in combat and combat continues after quit, so a fight that ends for a logged-out character plunders on their behalf: the mutations land, and `send_to_player`'s `group_send` reaches an empty group — a no-op, not an error. **Do not add a connected-player check.** The loot is theirs by the same rights predicate either way.

### 6.5 Positive-case output identity

When plunder does sweep, its output is the sweep's output verbatim — same per-item lines, same coin lines, same summary line, same carry-capacity refusal when the player fills up mid-sweep. A plunder must be indistinguishable from a `loot` the player typed. This falls out of §5 if the extraction is done correctly; it is called out here because it is a ruled requirement, not an implementation convenience.

---

## 7. The verification harness (#249 Part 2)

### 7.1 The base class

**New file:** `django/src/apps/shyland/verification.py` — a module, not a command. `management/commands/` holds commands only.

**Deliberately Shyland-scoped, not platform-shared.** A shared home would be shared surface under CLAUDE.md Rule 2 and would require its own stop-and-flag; Shyland is the only consumer today. If a second game ever needs it, moving it is that session's decision. Do not place it outside `django/src/apps/shyland/`.

**Contract:**

- A `BaseCommand` subclass — suggested name `VerificationCommand` — that subclasses implement by providing the verification body rather than overriding `handle()`.
- The body executes inside `transaction.atomic()` with a **forced rollback**, so any write a verification command performs — accidental or otherwise — is discarded rather than committed. This is the runtime backstop behind the `verify_*` name gate the Part 1 Makefile already enforces.
- **Exit code is the outcome signal: 0 = clean, nonzero = findings or error.** A failure must be loud through `make verify` / `make verify-prod`, not buried in stdout. Use the standard Django mechanism for a nonzero exit.
- **Findings are reported, never repaired.** No verification command may mutate state, even to "fix" what it finds. The rollback enforces this at runtime; the rule is also a review rule.
- Human-readable output goes to stdout in the house style.

### 7.2 `verify_ladder`

**New file:** `django/src/apps/shyland/management/commands/verify_ladder.py`, subclassing §7.1.

Spec, verbatim from **V24.28 Brief 1 §7 step 8** — the survey that went to production unverified and spawned #248:

> Count existing `ItemInstance` rows on a ladder definition whose `mk_tier` falls outside that definition's range. **Expected: 0.**

Precisely:

- **Ladder membership:** `ItemInstance` rows whose `definition.tier_material_mk_min` is non-null. (Null minimum = not on the ladder; the freebie kit suppresses its Mk suffix without joining the ladder, and must not be counted.)
- **Mismatch:** `mk_tier` below `definition.tier_material_mk_min`, **or** above `definition.tier_material_mk_max` where that maximum is non-null. Sphaerium's null maximum is unbounded and can never mismatch upward — a null max must not be treated as zero or as a mismatch.
- **Output:** on a clean run, a single line reporting zero mismatches out of the ladder-row total, exit 0. On findings, the mismatch count plus the offending definition slugs (and their `mk_tier` values), exit nonzero.
- **Never mutates.** This is a report. If rows exist, they are recorded and a design ruling is sought — nothing is deleted or rewritten.

Field names, confirmed against the models: `ItemInstance.definition` (FK), `ItemInstance.mk_tier`, `ItemDefinition.tier_material_mk_min`, `ItemDefinition.tier_material_mk_max`.

### 7.3 Dev testing path

`make verify VERIFY=verify_ladder` against the dev stack. This is the Part 1 dev path and the reason it exists.

---

## 8. Architecture note on the three parts

Plunder, the harness, and the #250 fix share this brief but share no code. Keep them in **separate commits** so the history reads honestly and each can be reasoned about — and reverted — alone.

---

## 9. Tests

New file: `django/src/apps/shyland/tests/test_v24_29_brief1.py`. Every item below is a required assertion.

**The setting**

1. `plunder_mode` defaults to `False` on a newly created character.
2. Bare `plunder` reports `plunder is off.` (category `system`); after `plunder on`, bare reports `plunder is on.`
3. `plunder on` answers `plunder is now on.` and persists to the DB; all six accepted words work in both cases and mixed case.
4. `plunder banana` answers `Usage: plunder [on|off]` in category `error` and changes nothing.
5. `plunder` is allowed in combat and while dying (it is a setting), and appears in the help Settings section and in the connect-time verb list.

**The trigger**

6. **Fires at combat end with plunder on:** a character with `plunder_mode=True` who lands the last kill receives the sweep's output after `Combat has ended.`, and the corpse's items are in inventory and its copper on the character.
7. **Does not fire with plunder off:** identical scenario, `plunder_mode=False` — `Combat has ended.` arrives, no loot lines, the corpse still holds its contents.
8. **No mid-fight plunder:** a kill with other NPCs still alive produces no loot lines and leaves the fresh corpse untouched — including for a character with plunder on.
9. **Flee does not plunder:** a successful flee from a fight with a rights-held corpse in the room produces no loot lines.
10. **Death does not plunder:** a character who goes dying produces no loot lines.
11. **Rights are respected:** with two characters and two corpses, a combat-end plunder takes only the corpses the plundering character killed; the other character's corpse is untouched.

**The silence contract**

12. **Nothing to sweep, nothing said:** combat ends with plunder on and no rights-held corpse in the room (e.g. the corpse was already looted) — the character receives `Combat has ended.` and **no other message**. Assert on the absence of both refusal strings specifically, and on the absence of the summary line.

**Output identity**

13. The plunder message sequence for a given corpse is **identical** to the sequence typed `loot` produces for the same corpse — same texts, same categories, same order. Build it as a direct comparison, not two hand-written expectations.
14. Carry capacity: a plunder that fills the character mid-sweep emits the `You can't carry any more. (N/M items)` warn and stops, exactly as the typed sweep does.

**Disconnected**

15. A combat-end plunder for a character with no connected consumer completes its mutations without raising.

**The harness**

16. A verification command whose body attempts a write leaves the database unchanged after the command completes — the forced rollback works.
17. `verify_ladder` on a clean database reports zero mismatches and exits 0.
18. `verify_ladder` with a deliberately mismatched `ItemInstance` (constructed directly via the ORM, bypassing the generation guard) reports the count and the offending slug and exits nonzero — **and leaves the mismatched row in place**, proving it reports rather than repairs.
19. A ladder definition with a null `tier_material_mk_max` (sphaerium) at a very high `mk_tier` is **not** counted as a mismatch.
20. A non-ladder definition (null `tier_material_mk_min`, e.g. the freebie kit) at any `mk_tier` is **not** counted.

**#250**

21. After `echo off` and `echo on`, the consumer's cached `self.character.show_timestamps` still matches the database value — the echo setter no longer touches it. Assert on the cached attribute specifically; a test that only reads a fresh fetch would pass against the bug and prove nothing.
22. `echo` itself still behaves: bare reports, six words set, the value persists, and the status payload carries the new `echo_mode`.

**Regression**

23. The full existing suite passes with no test file edited except the version pin (§3). If any pre-existing test requires modification, stop and report it as a deviation.

---

## 10. Verification

Run in order. All must pass before the architecture-doc step and before closing #235.

1. `make makemigrations APP=shyland` produced exactly `0049`, a single `AddField`, committed unedited.
2. `make deploy-dev` from the worktree completes (build + migrate).
3. In-container suite green: `python manage.py test apps/shyland/tests` — report the total. (Path form only; the label form crashes on the `apps` namespace package.)
4. **`make verify VERIFY=verify_ladder`** against the dev stack: exits 0, reports **0 mismatches**. Record the ladder-row total it reports.
5. **The dev-path gates still behave:** `make verify` with no `VERIFY` gives the usage error; `make verify VERIFY=seed_world` is refused by the `verify_*` name gate. Both nonzero, posture untouched.
6. **Output identity, live:** in `make shell` or by playing on dev, confirm a plunder and a typed `loot` of an equivalent corpse produce the same lines.
7. `git grep` confirms no file outside `django/src/apps/shyland/` and `docs/shyland/` was modified (shared-surface check). **The Makefile is not touched by this brief** — the verify targets already shipped in Part 1.
8. GDD source is untouched by this session — `git diff` against the branch point shows no changes under `docs/shyland/gdd/`.

---

## 11. PENDING DEPLOY-TIME ACTIONS

**The production ladder verification.** The first live exercise of `make verify-prod`, and the settlement of V24.28's handed-off survey.

- **Action:** `make verify-prod VERIFY=verify_ladder`
- **Executor:** the closeout session, on its own explicit operator confirmation in the closeout tail — **bare, single-command invocation**. (Executor checkpoint, Instructions v33: this step names a sanctioned posture-setting target, so it is runnable. It is the target #249 Part 1 shipped for exactly this.)
- **Order:** after `make deploy-prod`. The command is baked into the image, so it must be deployed before it can run.
- **Expected result: 0 mismatches, exit 0** — the number V24.28 Brief 1 §8 predicted and had no way to confirm.
- **If it reports findings:** record the count and slugs in the closing report and **stop for a design ruling**. Do not delete or rewrite instance data. The command cannot mutate, so a finding is information, never damage.

No seed run and no data mutation is required by this release. This block stays open until that production execution.

---

## 12. Architecture document

**This step is gated on all implementation and verification steps above being complete and passing.**

`docs/shyland/Shyland_Architecture_v24.md` — updated **in place** (point-release rule; no new file, filename keeps the major-version name).

- **Header:** stamp → 24.29; **the commit hash moves** — this is an architectural change (new model field, a new shared module, a new command family).
- Add the `Version 24.29 (point release)` block at the top of the version blocks, in the established style.
- **§4.1 Models** — `Character.plunder_mode`.
- **The consumers/commands section** — `plunder` as the fourth settings command and its five registration sites; the #250 correction to `_set_echo_mode` (one line, noted for the record — the setters now uniformly write only the DB row, with the cached attribute maintained by the command); the `_loot_sweep` extraction into `loot_utils.py`, stating explicitly that the helper returns messages rather than sending them and why (the tick engine has no consumer, and per the ruling no connected player is required).
- **The tick-engine section** — the plunder hook at the three `Combat has ended.` sites, the anchor rule, and the flee/death exclusions falling out of it rather than being coded.
- **A new subsection for the verification family** — `verification.py`'s forced-rollback contract, the exit-code convention, the report-never-repair rule, `verify_ladder`, and the `make verify` / `make verify-prod` relationship (#249 Parts 1 and 2).

Do not touch GDD source.

---

## 13. Issue closure

- **Close #235** once verification §10 passes in full.
- **Close #250** once §9.21–22 pass. It and #235 are the milestone's two issues; both must be closed for the closeout's `milestone closed N/N` gate.
- **Do NOT close #249.** It stays open for Part 3 (retiring the v33 interim rule), which is an ops session's work after this release ships. Add a comment recording what Part 2 shipped, with the commit hash — do not change its state or milestone.

---

## 14. Operator playtest checklist — dev stack

Ready after `make deploy-dev`. All steps against **dev**; production hosts no mid-version builds.

1. **Version reads 24.29-DEV.** Connect and check the version line at the bottom of `help`.
2. **The setting behaves.** `plunder` reports `plunder is off.` `plunder on` answers `plunder is now on.` `plunder` reports on. `plunder banana` gives the red usage line. Reconnect and confirm it is still on — it persists.
3. **Help reads right.** `help` shows `plunder` in the Settings section between `echo` and `timestamps`, with its default stated.
4. **Tab completion.** Type `plunder ` and tab — the six boolean words offer.
5. **The happy path.** With plunder **on**, kill a single NPC that drops loot and coin. Confirm: `Combat has ended.` arrives first, then the loot lines and the coin line and the `Looted 1 corpse.` summary — and that the items are in your inventory. It should read exactly as if you had typed `loot`.
6. **The comparison.** Turn plunder **off**, kill another of the same NPC, and type `loot`. The lines should be indistinguishable from step 5's.
7. **Multi-kill fight.** With plunder on, engage a room with two or more NPCs. Confirm **nothing** is looted as each one dies — the sweep happens once, at the end, taking all the corpses together.
8. **Silence.** With plunder on, kill something, type `loot` yourself immediately, and then let the next combat end (or kill something whose corpse you have already emptied). Confirm no stray `There is nothing to loot here.` or `That is not your kill` lines ever appear on their own.
9. **Flee.** With plunder on, start a fight, kill one of two NPCs, then `flee`. Confirm nothing is looted.
10. **Aggro respawn.** In an aggro-respawn room (The Choke), with plunder on, fight until a respawn re-engages you immediately at combat end. Confirm that when the fight *does* finally end, the older corpses are swept too — the missed sweep self-corrects rather than being lost.
11. **Full inventory.** With plunder on and a nearly full inventory, kill something with several drops. Confirm the `You can't carry any more.` warn appears and nothing is silently eaten.
12. **Off is off.** With plunder **off**, kill something and confirm nothing is looted automatically and the corpse still holds its contents.
13. **Echo and timestamps still independent (#250).** Turn `echo off`, then check `timestamps` — it must still report its own true value, and timestamps must still render on stamped lines. Repeat with `echo on`. (The #250 defect was latent, so this is a confirmation that the fix changed nothing player-visible, not a reproduction of a symptom.)
14. **Nothing else moved.** Play a short Z01 loop — buy, sell, equip, unequip, travel, heal. Confirm nothing about looting or combat feels different from before.

> Any step that gifts an item must **gift via the shell helper** — `generate_item_instance(definition, mk_tier, rarity, owner=character)` — never the Django admin add form, which bypasses generation guards by design (#246). No step here requires a gift.

---

## 15. Closeout report

Commit as `docs/shyland/Shyland_V24.29_Brief_1_Closeout.txt`, opened as a stub at Step 0 (§2) and completed in place. Must include:

- The final commit hash.
- The suite total.
- The `make verify VERIFY=verify_ladder` result on dev (mismatch count and ladder-row total).
- The dev-path gate results (§10.5).
- Any deviations — in particular, any pre-existing test that had to be edited (§5, §9.21), which is a stop-and-report condition, not a silent fix.
- The still-open **PENDING DEPLOY-TIME ACTIONS** block (§11) verbatim, with its named executor.
- The **operator playtest disposition**, verbatim-style: *"Operator reports playtest successful"*, *"No playtests for this brief"*, or *"Operator deferring playtest"*.
