# Shyland V24.30 — Brief 1: Uniform Config Setters

- **Release:** Version 24.30 (point release) — milestone `Version 24.30`
- **Branch:** `version_24_30`
- **Founding ticket:** #251 — *All config command setters should write both the cached attribute and the DB row* (operator-ruled 2026-08-15; ruling comment on the issue records the full audit)
- **Related:** #250 (the `_set_echo_mode` wrong-field line, fixed in v24.29 by deletion — this brief adds the *correct* line back, in the setter; the issue's comment explains why that is not a reversal). #243 (config set paths never fresh-fetch and so miss the deleted-while-connected guard — **deliberately out of scope here**; that ruling stays with #243).
- **Written by:** the V24.30 design session, 2026-08-15.

---

## 1. Problem and ruling

The four settings commands (`brief`, `echo`, `plunder`, `timestamps`) share one helper (`_cmd_setting`) but their `@database_sync_to_async` setters are non-uniform: three write only the DB row, leaving the cached `self.character` attribute to be maintained by the calling `cmd_*` — the cache is right only by the caller's cooperation. Any direct call to a setter leaves `self.character` stale.

**Ruling (operator, 2026-08-15, on #251): all config command setters write both the cached attribute and the database row. `_set_plunder_mode` is the shape.** Consequence ruled by the design session (recorded on #251): the setter becomes the **single writer** of the cache — the now-redundant caller-side cache assignments are removed, because leaving them would preserve the caller-maintains-the-cache pattern this ruling kills.

**Zero player-visible behavior change. No model change, no migration. No GDD change** — the v22 settings standard (six words, bare-reports, `Usage:` line) is untouched.

## 2. Technical claims — verified per the v36 technical-coherence rule

Every claim below was **confirmed against the code at writing time** (branch `version_24_30` at commit `1e159e3`, cut from main after the V24.29 closeout). File: `django/src/apps/shyland/consumers.py`. Line numbers are indicative at that commit, not load-bearing.

1. **The setters (lines 4082–4097):**
   ```python
   @database_sync_to_async
   def _set_brief_mode(self, value):
       Character.objects.filter(pk=self.character_pk).update(brief_mode=value)

   @database_sync_to_async
   def _set_show_timestamps(self, value):
       Character.objects.filter(pk=self.character_pk).update(show_timestamps=value)

   @database_sync_to_async
   def _set_echo_mode(self, value):
       Character.objects.filter(pk=self.character_pk).update(echo_mode=value)

   @database_sync_to_async
   def _set_plunder_mode(self, value):
       Character.objects.filter(pk=self.character_pk).update(plunder_mode=value)
       self.character.plunder_mode = value
   ```
2. **The caller-side cache assignments:** `cmd_brief` line 2994 (`self.character.brief_mode = value`), `cmd_echo` line 3004 (`self.character.echo_mode = value`), `cmd_plunder` line 3018 (`self.character.plunder_mode = value` — redundant *today*, since its setter already writes the cache). Each runs under `if value is not None:` after the `_cmd_setting` call.
3. **`cmd_timestamps` has no caller-side assignment.** Its set path (line 3030) bypasses `_cmd_setting` (status payload must precede the confirmation line so the confirmation renders under the new preference) and calls `await self._set_show_timestamps(value)` directly — the cached attribute is never assigned; it is correct today only because the subsequent `get_character_fresh()` (line 3031) replaces `self.character` wholesale (line 4481: `self.character = char`). This is the third instance of the fragility; the setter owning the cache closes it by construction.
4. **No live staleness bug exists at this commit:** every gameplay read of the four settings is fresh — `send_room_description` fresh-fetches (line 3569) before `_resolve_room_rendering` reads `brief_mode` (line 4143); `_status_payload` reads the `char` its callers freshly fetch (lines 3454–3455); plunder is re-read by pk in `loot_utils.get_plunder` at combat end (loot_utils.py lines 116–122, deliberately, per its docstring); the connect-time payload (consumers.py lines 501–502) reads the object fetched at connect (line 425). The fix removes a *latent* class of bug, exactly as #251 states.
5. **The existing test shape:** `tests/test_v24_29_brief1.py` — `test_all_six_words_in_mixed_case` asserts both the fresh DB row (line 125) and the consumer's cached attribute (line 130) after each `plunder` flip. This is the assertion shape §5 extends to the whole family.
6. **The architecture doc documents the current split** and must change: `docs/shyland/Shyland_Architecture_v24.md`, the **"Setter hygiene (v24.29 brief 1, #250)"** passage (line 1378), ends: *"`_set_brief_mode`, `_set_show_timestamps` and `_set_echo_mode` now uniformly write only the DB row, with the cached attribute maintained by the command. `_set_plunder_mode` is the one deliberate exception…"* — after this brief that text is false and is rewritten (§8).
7. **Version constant:** `django/src/apps/shyland/version.py` line 8 (`SHYLAND_VERSION = "24.29"`); pin test `tests/test_b2_amendment1.py` line 118 (`self.assertEqual(SHYLAND_VERSION, '24.29')`).

Self-consistency: this brief was given one end-to-end read before commit; §2's claims, §4's steps, and §8's arch-doc scope agree.

## 3. Step 1 — version start (opening act, standing requirement)

1. In its **own commit**: `SHYLAND_VERSION = "24.30-DEV"` in `django/src/apps/shyland/version.py`, and the pin test in `tests/test_b2_amendment1.py` moved to `'24.30-DEV'` in the same commit.
2. `make deploy-dev` from the worktree (the version-start deploy).

## 4. Step 2 — implementation

All edits in `django/src/apps/shyland/consumers.py`:

1. **Bring the three setters to the plunder shape** — append the cache write to each:
   - `_set_brief_mode`: add `self.character.brief_mode = value`
   - `_set_show_timestamps`: add `self.character.show_timestamps = value`
   - `_set_echo_mode`: add `self.character.echo_mode = value`
   Each assignment goes **after** the `.update(...)` line, inside the setter, mirroring `_set_plunder_mode` exactly.
2. **Remove the three caller-side cache assignments** (§2 claim 2): the `self.character.brief_mode = value` line in `cmd_brief`, the `self.character.echo_mode = value` line in `cmd_echo`, the `self.character.plunder_mode = value` line in `cmd_plunder`. Where the removal empties an `if value is not None:` block entirely (`cmd_brief`, `cmd_plunder`), remove the now-empty conditional too. `cmd_echo` **keeps** its `if value is not None:` block — the fresh fetch + status payload inside it (lines 3005–3006) remain; only the assignment line goes.
3. **`cmd_timestamps` is not edited.** Its direct setter call now maintains the cache via the setter itself; its status-before-confirmation ordering is deliberate and stays.
4. **Do not** add fresh-fetch/deleted-guard logic to any set path — that is #243's ruling, not this brief's.

**Migration step: none.** No model changes. (Stated explicitly per the brief rules.)

## 5. Step 3 — tests

New file `django/src/apps/shyland/tests/test_v24_30_brief1.py`:

1. **Setter-owns-both, all four:** for each of the four setters, call the setter directly (not through the command) on a connected consumer and assert **both** the fresh DB row and `consumer.character.<field>` reflect the new value — the issue's exact complaint ("any direct call to a setter leaves `self.character` stale") becomes the pinned regression.
2. **Command-level cache coherence, all four:** flip each setting via its command (`brief on`, `echo off`, `plunder on`, `timestamps off`) and assert DB row and cached attribute agree afterward. For `timestamps` this pins §2 claim 3's path.
3. **No behavior drift:** bare `brief` / `echo` / `plunder` / `timestamps` still report the current-setting sentence; an invalid word still answers the `Usage:` line and changes nothing (assertion shape as in `test_v24_29_brief1.py`'s `test_invalid_input_answers_usage_and_changes_nothing`).

The existing suites (`test_v24_29_brief1.py`, `test_command_revamp.py`) must pass **unedited** — they are the regression bar; if any of their assertions fail, that is a deviation to stop and report, not a test to edit.

## 6. Verification

1. Full suite, in-container, the only working form:
   `python manage.py test apps/shyland/tests` (via `docker exec` in the django container). All tests pass; suite count grows only by this brief's new tests.
2. `grep -n 'self.character.brief_mode = value\|self.character.echo_mode = value\|self.character.plunder_mode = value\|self.character.show_timestamps = value' django/src/apps/shyland/consumers.py` — every hit sits inside a `_set_*` setter; **zero** hits inside any `cmd_*`.
3. `make deploy-dev` from the worktree once 1–2 pass.

## 7. Operator playtest checklist (dev stack)

Ready after this brief's `make deploy-dev`. All steps on dev, any character:

1. `brief` (bare) → current-setting sentence. `brief on` → `brief room display is now on.` Re-enter a visited room → brief description renders. `brief off` → long form returns.
2. `echo off` → confirmation, then typed commands stop echoing in the pane. `echo on` → echo returns. Bare `echo` reports correctly both times.
3. `timestamps off` → the confirmation line itself renders **without** a timestamp prefix (status-first ordering intact). `timestamps on` → prefix returns on event lines.
4. `plunder on`, kill one NPC with a corpse you have rights to → the automatic sweep still fires at combat end. `plunder off` → it doesn't.
5. Refresh the browser (reconnect) after setting all four away from defaults → all four survive the reconnect (bare-report each).

**No PENDING DEPLOY-TIME ACTIONS.** No migration, no seed, no data actions — nothing for the closeout tail beyond the ordinary `make deploy-prod`.

## 8. Architecture doc — last, gated

This step is gated on all implementation and verification steps above being complete and passing.

`docs/shyland/Shyland_Architecture_v24.md`, updated **in place**:

- Stamp line → **24.30**; the header's "as of commit" hash **moves** (this is a code change) to this brief's final implementation commit, with a one-line summary of the change appended in the header's established style.
- The **"Setter hygiene"** passage (§2 claim 6): rewrite to the new truth — all four `_set_*` setters write the DB row **and** the cached attribute (`_set_plunder_mode`'s v24.29 shape generalized by #251); the commands no longer maintain the cache; `cmd_timestamps`' direct-call path is covered by construction. Keep the #250 history (deletion-not-correction) intact and add #251 as its completion.
- The v24.29 release box-out is history — **not** edited.

## 9. Closeout report

`docs/shyland/Shyland_V24.30_Brief_1_Closeout.txt` (stub created and pushed at Step 0 per the standing ritual, completed in place): final commit hash, suite count, verification results including §6.2's grep, any deviations, and the **operator playtest disposition** line (#170) — one of "Operator reports playtest successful" / "No playtests for this brief" / "Operator deferring playtest".
