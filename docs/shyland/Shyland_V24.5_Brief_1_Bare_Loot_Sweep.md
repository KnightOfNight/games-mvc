# Shyland V24.5 — Brief 1: Bare `loot` Behaves Like `loot all`

- **Release:** Version 24.5 (milestone `Version 24.5`)
- **Branch:** `version_24_5`
- **Founding issue:** #189 (the release's only ticket — scope law)
- **Authored:** 2026-08-01, V24.5 design session
- **Ruling of record:** #189 body (operator, 2026-08-01, recorded live) — *"Bare `loot` behaves exactly like `loot all` — verbatim, in every case. The target becomes optional, defaulting to the room sweep."*

This brief is self-contained. The implementation session reads only this brief and the repo.

---

## 1. Context

Today bare `loot` never reaches the handler: `loot` sits in the `PROMPT_VERBS` table, so the central footnote-10 gate in `_dispatch` answers `What do you want to loot?` as a CLI error. The ruling removes `loot` from the required-target set: bare `loot` becomes the exact equivalent of `loot all` — the kill-gated room sweep — with every downstream behavior inherited unchanged.

**This makes `loot` the first verb whose bare form performs the `all` sweep. It is deliberately NOT a precedent for `sell`** — #150 ruled bare bulk-sell stays refused; loot is kill-gated and value-safe, sell is destructive of inventory. Do not generalize this change to any other verb.

The GDD §9.1 changes (chart row `3 \| 5 · 20`, new footnote 20, Corpses-and-Loot prose) are already committed on this branch by the design session, marked "(v24.5, #189, pending implementation)". Implementation does not touch GDD source (the marker sweep is design/closeout work).

## 2. Standing requirement — version constant (opening act)

This is the **first implementation brief of Version 24.5**:

1. **Own commit, before anything else:** bump `SHYLAND_VERSION` from `"24.4"` to `"24.5-DEV"` in `django/src/apps/shyland/version.py` (line 8), and move the pin-test assertion in `django/src/apps/shyland/tests/test_b2_amendment1.py` (line 118: `self.assertEqual(SHYLAND_VERSION, '24.4')` → `'24.5-DEV'`) **in the same commit**.
2. Then run the version-start `make deploy-dev` from the worktree.

## 3. Implementation

All changes are in `django/src/apps/shyland/consumers.py`. **Runtime code only — no models, no migrations, no seed data, no new dependencies.**

1. **Remove `loot` from `PROMPT_VERBS`** (~line 276: the `'loot': 'loot',` entry). Bare `loot` then reaches `cmd_loot` via the normal dispatch path. Do not touch any other entry; do not touch `GRAMMAR_VERBS` (loot stays — argument completion is unchanged) or `COMBAT_BLOCKED` (loot stays refused in combat with its authored line `Your hands are too busy with the fight!`, ~line 246 — bare `loot` in combat now hits that refusal, exactly as `loot all` does today).
2. **In `cmd_loot`** (~line 1834): treat empty args as the sweep — e.g. the sweep branch triggers when `args.strip().lower() in ('', 'all')`. Everything downstream is inherited verbatim and must not change: the no-corpse warn `There is nothing to loot here.` (already emitted before argument parsing), the `killed_by_id` kill gate, `That is not your kill; you may not loot it.`, copper transfer on first loot, per-line sweep output plus summary, the corpse-noun and `N.<NPC>` single-corpse forms, `The <npc> carried nothing worth taking.`
3. **Help line** (~line 1008): `('loot', 'loot all | <NPC>', 'Loot a corpse, or every corpse here.')` → `('loot', 'loot [all] | <NPC>', 'Loot every corpse here, or one named corpse.')` (matches the GDD §9.1 row; description unchanged in spirit per the ruling).

**Design rules — no deviation:**

- Bare `loot` ≡ `loot all` **verbatim, in every case** — identical output, identical gating, identical refusals. No new sentences, no new categories.
- The bare form is the room sweep, never a single-corpse guess (the v18 most-recent-corpse convenience stays retired).
- Tab completion pools are unchanged: loot still completes `all` and corpse names. Verify no completion code keys off `PROMPT_VERBS` membership for pool construction; if any does, the pool must remain exactly as before — report how in the closeout.
- No other verb leaves `PROMPT_VERBS`. Footnote 10's rule is untouched for every other command.

## 4. Migration step

None — no model changes. Stated explicitly per the brief rules.

## 5. Tests

New test file `django/src/apps/shyland/tests/test_v245_bare_loot.py` (mirror the structure of `test_v244_heal.py`, which covers the same kind of dispatch-table change):

1. **Table assertion:** `'loot'` is **not** in `SkylandConsumer.PROMPT_VERBS` (mirror of `test_v244_heal.py:62`), and `'loot'` **is** still in `GRAMMAR_VERBS` and `COMBAT_BLOCKED`.
2. **Bare ≡ all, sweep path:** with corpses killed by the character present, bare `loot` produces exactly the output `loot all` produces (loot lines + summary; run both against identical fixtures and compare).
3. **Bare ≡ all, kill-gate refusal:** with only another character's corpse in the room, bare `loot` answers `That is not your kill; you may not loot it.` (warn).
4. **Bare ≡ all, empty room:** no corpses → `There is nothing to loot here.` (warn).
5. **Unchanged forms:** `loot <NPC>` and `loot all` still work (regression guard riding the same fixtures).

**Test-hygiene conversion clause:** at brief-writing time, **no existing test asserts the literal `What do you want to loot?`** (verified by repo-wide grep). If the implementation session finds one anyway, convert it to the new behavior with original intent preserved as explicit assertions and report the conversion as a deviation in the closeout — never change it silently.

## 6. Verification

1. Full in-container suite — the only working form: `python manage.py test apps/shyland/tests` (directory-path form, via `docker exec` in the django container). **All tests pass.**
2. Spot-check via the test client or a dev-stack session: bare `loot` on a fresh kill sweeps; `What do you want to loot?` is no longer reachable for loot by any input.

## 7. Deploy — dev stack

After implementation and verification pass: `make deploy-dev` from the worktree. **No production actions of any kind. No PENDING DEPLOY-TIME ACTIONS — this brief has no data actions, no seed changes.**

## 8. Operator playtest checklist (dev stack)

1. Kill an NPC; type bare `loot` → the room sweep runs (loot lines, summary), identical to `loot all`.
2. Kill two NPCs; bare `loot` sweeps both corpses.
3. In a room containing only a corpse you did not kill: bare `loot` → "That is not your kill; you may not loot it."
4. In a corpse-free room: bare `loot` → "There is nothing to loot here."
5. `loot all` and `loot <NPC>` (and `2.<NPC>` with duplicate corpses) behave exactly as before.
6. During combat: `loot` → "Your hands are too busy with the fight!" (unchanged).
7. `help` shows `loot [all] | <NPC> — Loot every corpse here, or one named corpse.`
8. Tab completion after `loot ` still offers `all` and corpse names.

## 9. Architecture doc (last, gated step)

**This step is gated on all implementation and verification steps above being complete and passing.** Update `docs/shyland/Shyland_Architecture_v24.md` **in place**:

- Header stamp line: version to **24.5-DEV** is never written to the arch doc — the doc stamps **24.5**, and the hash annotation moves (this is an architectural behavior change: the dispatch table's required-target set changes). Append the v24.5 brief-1 summary to the "as of commit" annotation per the standing pattern (line 3).
- §4.14 (Command layer): update the `PROMPT_VERBS` membership and the loot grammar text — loot's target is optional, bare = the `all` sweep, first and only such verb, explicitly no precedent for sell (#150).
- Doc-wide grep for any other claim that bare `loot` prompts (`What do you want to loot`, "bare loot") and correct each hit.

## 10. Closeout

- Closeout report `docs/shyland/Shyland_V24.5_Brief_1_Closeout.txt` — created as a **stub at Step 0** (one-line session-start record: date, brief name, branch; committed and pushed immediately as the work-has-started signal), completed **in place** at session end.
- The completed report includes: what shipped, deviations (or "none"), test results (count passing), the final commit hash, and the **operator playtest disposition** (one of: "Operator reports playtest successful" / "No playtests for this brief" / "Operator deferring playtest" — this brief HAS a playtestable surface, so "No playtests" does not apply).
- Close #189 gated on verification passing.
- End with the `implementation-session-end` ritual (playtest disposition first, issues report as the formal end artifact).
