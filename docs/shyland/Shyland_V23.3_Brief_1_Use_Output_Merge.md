# Shyland V23.3 Brief 1 — Use Output Merge

- **Release:** Version 23.3 (point release) · milestone `Version 23.3` (#17) · branch `version_23_3`
- **Issues:** #149 (founding ticket), #151 (dependency of #149)
- **Written and committed by:** the v23.3 design session, 2026-07-28
- **For:** an implementation session on branch `version_23_3` (the operator directs this brief by name)

This is the only implementation brief of Version 23.3 (point-release scope law: one bucket B1, one brief, one founding ticket).

---

## 0. Pre-flight

- **Prior pending deploy-time actions: none.** This is the first brief of Version 23.3; no earlier brief in this release left a PENDING DEPLOY-TIME ACTIONS block, and the prior release (23.2) closed with nothing pending.
- This brief introduces **no data actions of its own** — no seed changes, no data fixups, no `make seed`. If implementation discovers a need for one, that is a deviation: stop and report before proceeding.
- **No model changes and therefore no migration.** If implementation finds a migration necessary, stop and report — that is a scope deviation for a point release ruled as output-composition work.

## 1. Opening act — the version-start ritual (standing requirement)

This is the first implementation brief of the release. As its **opening act, in its own commit**:

1. In `django/src/apps/shyland/version.py`, change `SHYLAND_VERSION = "23.2"` to `SHYLAND_VERSION = "23.3-DEV"`.
2. Move the pin test with it: in `django/src/apps/shyland/tests/test_b2_amendment1.py`, the assertion `self.assertEqual(SHYLAND_VERSION, '23.2')` becomes `self.assertEqual(SHYLAND_VERSION, '23.3-DEV')`.
3. Commit (this commit contains nothing else), push, then run the version-start `make deploy-dev` from the worktree.

The closeout session later stamps `23.3-DEV → 23.3`; this brief never does.

## 2. Design rulings (binding — operator-confirmed 2026-07-28, recorded on #149 and #151)

1. **Merge point and shape (#149):** the effect layer returns its message as a *clause*; `cmd_use` composes one sentence, one envelope: `You use a Healing Draught Mk 1 and feel your body recover. (+25 Vitality)`. Timed-effect consumables (empty apply-time message list, e.g. Focus Tonic) keep the plain `You use a Focus Tonic Mk 1.` line. Multiple instant components join their clauses in order.
2. **Category:** the merged line is `success`; the old separate system-category effect line dies. Exception: a multi-use aggregate that reaches full health sends its single line as `reward` (ruling 5).
3. **Aggregation scope (#151):** up-front computation applies to **instant-restore healing consumables only** — every component of the item's effect is instantaneous and at least one is `restore_vitality`. Everything else keeps the per-item loop (with ruling-1 line composition per item).
4. **Aggregate line composition:** Amendment-5 count form, plural-free: `You use Healing Draught Mk 1 ×3 and feel your body recover. (+75 Vitality)`. Mixed-Mk consumption joins its (definition, Mk) groups with commas in consumption order: `You use Healing Draught Mk 1 ×2, Healing Draught Mk 2 ×1 and feel your body recover. (+85 Vitality)`. A count of 1 keeps the `item_ref` indefinite-article form — never `×1`.
5. **Full-heal fold:** when the aggregate covers the deficit, the single line ends `… You are restored to full health.` and the whole line is `reward`-category — no second message. The shortfall warn `You only had N.` (#132 doctrine) stays a **separate warn line**, firing only when the request exceeded inventory **and** the deficit wasn't covered.
6. **Dying/revival:** unchanged semantics — while dying, `use` consumes exactly one restorative and runs the v19 revival sequence; aggregation applies only to the non-dying path. No over-drinking past revival. (The use+effect line itself merges per ruling 1.)
7. **Amendment 5 reconciliation:** the v22 B2 Amendment 5 per-line ruling is superseded **for `use` only**. **Repair and loot remain per-line.** The #61 full-health refusal (`You are already at full health.`, warn) is retained as the entry gate.

The GDD already records these rulings under `(v23.3, pending implementation)` markers (§9 Partial Fulfillment Doctrine, §9 Success Sentences and Aggregation, §6 Transactional aggregation). **This session never edits GDD source** — the closeout session sweeps the markers.

## 3. Implementation

All code lives in `django/src/apps/shyland/`. Blast radius: `effect_utils.py`, `consumers.py` (`cmd_use` and its helpers), `combat_utils.py` (`apply_npc_effects` — contract-preservation only), tests.

### 3.1 Effect-layer clause contract (`effect_utils.py`)

`_apply_instant_component` currently returns finished sentences (`"You feel your body recover. (+25 Vitality)"`). Change it to return structured clause data — a `(clause, annotation)` pair per component (exact carrier shape is implementation's choice; tuple or small named structure both fine):

| Component | clause | annotation |
|---|---|---|
| `restore_vitality` | `feel your body recover` | `(+{int(magnitude)} Vitality)` |
| `restore_longevity` | `feel your stamina return` | `(+{int(magnitude)} Longevity)` |
| `restore_acuity` | `feel your mind steady` | `(Acuity {acuity_current:.1f})` |
| `durability_restore` | `watch the repair kit fizz to no useful effect` | *(empty)* |

`apply_effect_definition` returns the list of these pairs (still: instant components only produce entries; timed components produce none; the reapplication early-return still returns an empty list). The atomic-update laws in `_apply_instant_component` (#52: single `F()`-with-clamp `UPDATE`, never object-arithmetic-then-save) are untouched.

Sentence composition from clause pairs (shared helper, home of implementation's choosing):

- **Standalone form** (reconstructs today's sentences for the NPC path): `You {clause}. {annotation}` → `You feel your body recover. (+25 Vitality)`.
- **Use-sentence form** (`cmd_use`): `You use {subject} and {clause1} and {clause2}. {annotation1} {annotation2}` — clauses joined with ` and ` in component order, single period, annotations space-joined after it, empty annotations omitted.

### 3.2 NPC path is preserved byte-identical (`combat_utils.apply_npc_effects`)

`apply_npc_effects` consumes `apply_effect_definition`'s return and today extends its message list with the raw sentences. Recompose via the **standalone form** so every string it returns is **byte-identical to current behavior**. A test pins this (see §4). No behavioral change of any kind on the NPC/combat path.

### 3.3 Single-use and per-item loop (`cmd_use`, #149)

For each item applied by the per-item loop (non-aggregatable consumables, and the dying path's single swallow):

- Replace the two sends — `You use {item_ref(item, indefinite=True)}.` (`success`) followed by per-message `system` lines — with **one** send of the use-sentence form, category `success`.
- Empty clause list (timed-effect consumables) → the plain sentence `You use a Focus Tonic Mk 1.`, exactly as today.
- `Nothing happens.` (no effect definition, warn), the #61 full-health refusal, the revival sequence's own lines (`Breath floods back…`, the room re-render, the broadcast), and the per-loop stop-at-full logic for non-aggregatable items are all **unchanged**.

### 3.4 The aggregate path (`cmd_use`, #151)

Insert before the per-item loop. Taken when the character is **not dying** and **every** resolved item's effect qualifies under ruling 3 (all components instantaneous, ≥1 `restore_vitality`). Steps:

1. **Entry gate (#61, unchanged):** fresh character read; if `vitality_current >= vitality_max` → `You are already at full health.` (warn), return.
2. **Deficit:** `deficit = vitality_max − vitality_current` from that fresh read.
3. **Plan consumption without applying:** walk `res.items` in resolution order (the resolver already orders lowest-value-first — do not re-sort), accumulating each item's `restore_vitality` magnitude (`component.computed_magnitude(item.mk_tier)`, summed across restore components if an effect somehow has several), stopping when the accumulated heal ≥ deficit, or the requested quantity is reached, or items run out.
4. **Apply once:** one atomic `UPDATE` for the total (`Least(F('vitality_current') + total, F('vitality_max'))` — the #52 law; exactly one UPDATE regardless of count). Non-vitality instant components of consumed items (none exist in current seed data, but the code must not silently drop them) apply alongside via the same effect machinery, their clauses joining the sentence per ruling 1. `EffectInstance` bookkeeping may run per consumed item as today — only the *player-visible output* and the *vitality write* aggregate.
5. **Delete** the consumed instances.
6. **Compose one line:** subject = `item_ref(item, indefinite=True)` when exactly one item was consumed; otherwise comma-joined `(definition, mk_tier)` groups in consumption order, each `{get_display_name_with_tier(item)} ×{count}` (no article — the existing count-form composition, as at the pickup/drop aggregate sites). Clause per ruling 4, annotation `(+{summed magnitude} Vitality)` (the displayed number is the sum of consumed magnitudes; the DB clamp renders truth on the bars, matching current single-use display law). If the accumulated heal covered the deficit, append ` You are restored to full health.` and send the line as `reward`; otherwise `success`.
7. **Shortfall warn (ruling 5):** if the requested quantity exceeded what inventory held **and** the deficit wasn't covered → second line `You only had {consumed_count}.` (warn). In every other stop case there is no warn.
8. **One status payload**, exactly one, after everything (the existing end-of-command `_status_payload` send).

`effect_restores_vitality` (the existing heal-detection helper) may be generalized or supplemented for the ruling-3 qualification test; keep detection derived from the effect's own components, never a new flag.

### 3.5 Explicitly out of scope

- No resolver, grammar, tab-completion, or state-gating changes. `use` in combat stays allowed; the dispatch guard stands.
- No changes to `repair`, `loot`, buy/sell/drop/pickup composition, or any other command's output.
- No seed data changes; no model changes; no migration.
- No GDD source edits (`make gdd` is not needed — no stamp moves in this brief).

## 4. Tests

Update the existing `use`-path tests that assert the two-line shape, and add coverage in `django/src/apps/shyland/tests/` for at least:

1. Merged single-use line: exact text `You use a Healing Draught Mk 1 and feel your body recover. (+25 Vitality)`, category `success`, one output envelope, no separate `system` effect line.
2. Timed-effect consumable: single plain sentence, unchanged.
3. Aggregate consumption math: deficit-driven stop (consumes ⌈deficit/heal⌉, not N); N-cap; inventory-cap; lowest-value-first order preserved.
4. Aggregate line: count form ×N for one group; comma-joined mixed-Mk groups in consumption order; count of 1 renders the indefinite-article form.
5. Full-heal fold: line ends `You are restored to full health.`, category `reward`, no second message.
6. Shortfall warn: fires when request > inventory and deficit uncovered; does **not** fire when the stop was deficit-driven or the request was met.
7. Exactly one vitality `UPDATE` on the aggregate path (or equivalent single-write assertion) and exactly one status payload.
8. #61 entry gate unchanged (`You are already at full health.`, warn).
9. Dying path: exactly one restorative consumed, revival sequence intact, the swallow's line in merged form.
10. NPC path pin (§3.2): `apply_npc_effects` message strings byte-identical to the pre-change sentences for a representative instant component.

**Test hygiene:** these renderings are stable strings (renderings never pool) — exact-string assertions are correct here. If any existing test pinned the old two-line shape as doctrine, convert it with original intent preserved and record the conversion as a deviation note in the closeout report.

## 5. Verification

Gated on all of §3 and §4 being complete:

1. Full in-container suite — the only working form: `python manage.py test apps/shyland/tests` (directory-path form, via `docker exec` in the django container). Whole suite passes; report the count against the pre-brief baseline (expect: net increase from new tests, zero failures).
2. Verify no migration was created: `git status` shows nothing under `django/src/apps/shyland/migrations/`.
3. Verification must pass **before** the final commit/push of the implementation step.

## 6. Dev deploy (standing requirement)

After implementation and verification pass: `make deploy-dev` from the worktree (never hand-rolled). Production is never touched by this session — the prod deploy happens only in the closeout session's tail (Deployment Law step 6). A deploy bounces all containers of the dev stack (all three games).

## 7. Operator playtest checklist (dev stack)

Ready after §6's `make deploy-dev`; all steps on the dev stack:

1. Below full health, `use healing draught` → **one** green line: `You use a Healing Draught Mk 1 and feel your body recover. (+25 Vitality)`; one timestamp; bars update once.
2. At full health, `use healing draught` → `You are already at full health.` (warn); nothing consumed.
3. With a large deficit and ample draughts, `use 25 healing draught` → **one** line, ×N showing only what the heal needed, ending `You are restored to full health.` in loot-green; no flood, no scroll-away, one status change.
4. With a large deficit and few draughts, `use 25 healing draught` → one aggregate line plus `You only had N.` (warn).
5. If mixed-Mk draughts are on hand: one sentence, comma-joined `×` groups.
6. `use focus tonic` → single plain `You use a Focus Tonic Mk 1.`; tick-engine focus messages behave as before.
7. Enter Dying (let something knock you to zero), then `use healing draught` → revival sequence fires, exactly **one** draught consumed regardless of stack size.
8. `use` mid-combat → merged line interleaves with combat output normally.

## 8. Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing.

Update `docs/shyland/Shyland_Architecture_v23.md` **in place** (point release — never a new file):

- Header blockquote: prepend the v23.3 Brief 1 change summary in the established style; **move the header hash** (architectural point release — code changed) to the brief's final implementation commit; add the `**Version 23.3 (point release)**` block following the 23.1/23.2 pattern, stamped 23.3 with the -DEV-era note that GDD lockstep completes at the point-release closeout.
- **§4.3** (WebSocket consumer): `cmd_use`'s merged sentence, the aggregate path, its category rules.
- **§4.4** (`effect_utils.py`): the clause contract, the two composition forms, the NPC-path preservation.
- **§4.14** (command layer): the partial-fulfillment/aggregation change for `use` (Amendment 5 superseded for `use` only).

## 9. Closeout

Write the closeout report as a `.txt` in `docs/shyland/` (completing the Step-0 stub in place): sections for implementation, verification (with test counts), deviations (or "none"), the final commit hash, and **PENDING DEPLOY-TIME ACTIONS: none** (expected — anything else is a deviation to explain). Close #149 and #151 (gated on verification passing). Commit and push at every step boundary throughout; branch only, never merge. End the session with the `implementation-session-end` ritual — the issues report is its formal end artifact.
