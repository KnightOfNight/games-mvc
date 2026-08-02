# Shyland V24.4 — Brief 1: The `heal` Command

- **Release:** Version 24.4 (point release; milestone `Version 24.4`)
- **Branch:** `version_24_4`
- **Founding ticket:** #166 — Top-level heal command, "use infinity healing draughts" semantics (`triaged`, ruled 2026-07-30 in the V24.0 design session, operator-confirmed; GDD text landed on this branch in commit `083c043`)
- **Authored by:** V24.4 design session, 2026-08-01
- **Prior pending deploy-time actions:** none outstanding — V24.3 closed with no data actions; V24.2's production seed executed and its pending block closed.

This brief is self-contained: everything the implementation session needs is in this file, the repo, and the issue tracker. GDD §9.1 and §6.12 (as committed at `083c043`, carrying `(v24.4, pending implementation)` markers) are the design of record; **if this brief and the GDD ever disagree, stop and report — do not choose.**

---

## 1. The design (binding rules)

`heal` is a **bare verb** — "use as many healing draughts as needed." One computed transaction on the existing v23.3 aggregate machinery (#151). No new mechanics, no new power: an aggregate `use N healing draughts` in combat is already legal; `heal` only removes the arithmetic from the player.

1. **Grammar:** no arguments; all arguments ignored (GDD §9.1 chart, footnote 2). No noun pool. Tab completion completes the verb only.
2. **Semantics:** compute the vitality deficit once (fresh read); consume the **minimum** count of qualifying draughts that covers it, or all remaining if short; one merged count-form line via the #151 aggregate path; one status payload. Mixed-Mk consumption uses the standing sentence form (comma-joined `(definition, Mk)` ×N groups; a count of 1 keeps the indefinite article).
3. **Selection:** oldest-first regardless of Mk (#168, applied verbatim — `use`'s existing `'oldest'` resolution policy, never re-sorted); each consumed item's heal computed from **its own Mk** under the Draught Law (`percent_heal_amount`, GDD §6.9).
4. **Qualifying pool** (the mechanical meaning of "healing draught family"): carried consumables passing the existing per-item `use_items_aggregatable` test — every effect component instantaneous, at least one `restore_vitality` / `restore_vitality_percent`. **Never a name match.**
5. **State gating:** allowed in combat, identical to `use` (no `COMBAT_BLOCKED` entry). Allowed while dying: behaves exactly as `use` — **exactly one** restorative, the v19 revival sequence, never over-drunk.
6. **Reuse, not duplication:** the #61 at-full refusal, the #151 aggregate path (`_use_aggregate` / `_apply_aggregate_heal`), the #168 ordering, and the dying/revival path are the implementations. `cmd_heal` is a thin front door; it composes no sentences of its own.
7. **Reserved built-in:** no code change for #125 (unshipped), but the GDD records `heal` as a verb the future alias system may never shadow. Nothing to implement; do not build alias machinery.

### Output cases — this table is authoritative

| # | State | Result | Category |
|---|---|---|---|
| 1 | At full vitality (not dying), with or without draughts | `You are already at full health.` — the standing #61 refusal, byte-identical, sourced from the existing gate (shared, not copied) | warn |
| 2 | Not full, zero qualifying draughts carried | `You have no healing draughts.` (authored for this brief) | warn |
| 3 | Not full, supply covers the deficit | One merged count-form sentence with the full-heal fold ` You are restored to full health.` — exactly `_use_aggregate`'s covered branch | reward |
| 4 | Not full, supply exhausted short of full | The merged count-form sentence (success), then the standing shortfall warn `You only had N.` on its own line (#132) | success + warn |
| 5 | Dying, ≥1 qualifying draught | Exactly one consumed; the existing revival sequence verbatim (merged use sentence, `Breath floods back into your lungs. You are alive — barely.`, room re-render, room broadcast) | as shipped |
| 6 | Dying, zero qualifying draughts | `You have no healing draughts.` | warn |

Gate order: **case 1 beats case 2** — at full vitality the at-full refusal fires even with an empty inventory (heal's purpose is already fulfilled; inventory is irrelevant). Cases 3/4 end with exactly one status payload, as `_use_aggregate` already does.

Wording note: case 4 deliberately **reuses** the standing `You only had N.` family string — the richer family-wide shortfall wording is #161's open question and is **not** absorbed here.

---

## 2. Implementation steps

### Step 1 — Version constant (opening act, its own commit)

`django/src/apps/shyland/version.py`: `SHYLAND_VERSION = "24.3"` → `"24.4-DEV"`. The pin test moves in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py` (`assertEqual(SHYLAND_VERSION, '24.3')` → `'24.4-DEV'`). Then the version-start deploy: `make deploy-dev` from the worktree.

### Step 2 — Registration (`django/src/apps/shyland/consumers.py`)

- `COMMAND_TABLE`: add `'heal': ('cmd_heal', False)` (bare verb — args ignored, footnote 2). No alias.
- `DYING_ALLOWED`: add `'heal'`.
- **No** entry in `COMBAT_BLOCKED`, `PROMPT_VERBS`, or `GRAMMAR_VERBS`. The connect-time verb list and verb tab-completion derive from `COMMAND_TABLE` — verify `heal` appears with no further wiring.

### Step 3 — `cmd_heal`

Behavior per §1 and the output table. Shape (mechanics latitude within these bounds):

- Fetch carried consumables the way `cmd_use` does (`get_carried_consumables`), filter to the qualifying pool (§1.4) preserving the oldest-first order the resolution machinery already yields — do not re-sort.
- **Dying:** take the oldest qualifying item and run it through the existing per-item use/revival path (extract a helper from `cmd_use` if needed rather than copying the sequence). The aggregate path stays dying-forbidden as today.
- **Not dying:** apply the gate order (at-full first — reuse the #61 gate as a shared check, byte-identical wording; then empty-pool warn), then delegate to `_use_aggregate` with a resolution-shaped request over the **entire** qualifying pool, uncapped, with `requested` set so the standing shortfall warn fires when the deficit goes uncovered. `_use_aggregate` supplies the deficit math, consumption, sentence, full-heal fold, shortfall warn, and the single status payload unchanged.

### Step 4 — Help

`HELP_SECTIONS`, Action commands, between `flee` and `home`: `('heal', 'heal', 'Drink healing draughts until your vitality is full.')`.

### Step 5 — Migrations / seed / models

**None.** No model changes, no migration, no seed data changes. There is **no PENDING DEPLOY-TIME ACTIONS block for this brief** — nothing runs at prod-deploy time beyond the deploy itself. State this in the closeout report.

### Step 6 — Tests

New suite `django/src/apps/shyland/tests/test_v244_heal.py` covering, at minimum:

1. Registration: `heal` in `COMMAND_TABLE` mapping to `cmd_heal`; in `DYING_ALLOWED`; absent from `COMBAT_BLOCKED`, `PROMPT_VERBS`, `GRAMMAR_VERBS`.
2. Output table case 1 — at full, with draughts and with none (both get the at-full refusal, warn).
3. Case 2 — damaged, no qualifying draughts → `You have no healing draughts.` (warn).
4. Case 3 — exact-cover: deficit covered by the minimum count, surplus draughts untouched, one reward line with the full-heal fold, one status payload. (Example: `vitality_max` 100, current 55, three Mk 1 draughts at 25 each → exactly 2 consumed, 1 remains.)
5. Case 4 — shortfall: deficit exceeds total supply → all consumed, success line, then `You only had N.` warn.
6. Oldest-first mixed-Mk: older Mk 1 consumed before newer Mk 2; per-item heal from each item's own Mk; comma-joined merged sentence.
7. In combat: `heal` proceeds (no refusal) and heals normally.
8. Dying: exactly one draught consumed, revival fires, remaining draughts untouched.
9. Arguments ignored: `heal 5 draughts` behaves exactly as bare `heal`.
10. Help: the heal row renders for a regular player; verb completion includes `heal`.

Sweep existing tests that enumerate the verb inventory, help rows, or gating sets (grep the test tree for such assertions) and update them; any literal-pin → pool conversion is reported as a deviation in the closeout, never changed silently.

**Invocation (the only working form, in-container):** `python manage.py test apps/shyland/tests` via `docker exec` in the django container.

### Step 7 — Dev deploy

Once implementation and the full suite pass: `make deploy-dev` from the worktree. (Production is never deployed from an implementation session — Deployment Law.)

### Step 8 — Architecture doc (LAST, gated)

This step is gated on all implementation and verification steps above being complete and passing. `docs/shyland/Shyland_Architecture_v24.md`, updated in place:

- Header banner: new **Version 24.4 (point release)** block — Brief 1, the `heal` command (#166); **the header hash moves** (architectural point release — consumer code changed) to the brief's final implementation commit; stamp 24.4.
- The line-3 authoritative-reference summary gains the v24.4 brief-1 clause, matching the established pattern.
- §4.3 (WebSocket consumer): new subsection **"The `heal` command (v24.4 brief 1, #166)"** — registration, the qualifying pool, gate order, delegation to `_use_aggregate`, dying single-consume, and the output table's six cases.

No other sections change. GDD source is not touched (design-session property; `make gdd` only if a directed mechanical operation requires it — this brief directs none).

### Step 9 — Closeout report

`docs/shyland/Shyland_V24.4_Brief_1_Closeout.txt` (completed in place from the Step-0 stub): steps, deviations, test counts, final commit hash, the no-pending-actions statement (Step 5), and the **operator playtest disposition** line (verbatim-style, per #170).

---

## 3. Verification (specific, testable)

1. Full suite green in-container: `python manage.py test apps/shyland/tests` — zero failures/errors; report the test count against the pre-brief count (must strictly increase).
2. Every row of the §1 output table demonstrated by a test in `test_v244_heal.py` (map row → test name in the closeout).
3. `grep -n 'heal' django/src/apps/shyland/consumers.py` shows the four registration points (COMMAND_TABLE, DYING_ALLOWED absence-checks aside, HELP_SECTIONS, cmd_heal) and no duplicated refusal/sentence strings introduced.
4. Pin test asserts `24.4-DEV`.
5. `make deploy-dev` completed; dev stack serves the branch build.

---

## 4. Operator playtest checklist (dev stack)

1. At full health: `heal` → yellow "You are already at full health."
2. Take damage (below max by a few draughts' worth), carry ≥3 Mk 1 draughts: `heal` → one reward-color merged line ending "You are restored to full health.", bar full, minimum draughts consumed (check `inv` count), one status update.
3. Damage exceeding total supply: `heal` → merged success line, then yellow "You only had N."; bar not full.
4. Drop/sell all draughts, take damage: `heal` → yellow "You have no healing draughts."
5. In combat: `heal` works mid-fight (no refusal), combat continues.
6. Get to Dying (vitality 0) carrying draughts: `heal` → exactly one draught consumed, revival sequence plays.
7. If a Mk 2 draught is available (admin gift / `stock-playtest-items`): acquire Mk 1 first, then Mk 2, damage deep, `heal` → oldest-first order, comma-joined mixed-Mk sentence. *(Optional if no Mk 2 draught is obtainable on dev.)*
8. `help` → heal row under Action commands ("Drink healing draughts until your vitality is full."); tab completes `heal`; `heal extra words` behaves as bare `heal`.
