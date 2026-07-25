# Shyland V23 Brief 5 — Amendment 1: Output Color Pass
**Version:** 23 · **Bucket:** B5 · **Issue:** #152 (closes)
**Branch:** `version_23` (existing — do not create a new one)
**Parent brief:** `Shyland_V23_Brief_5_Voice_Content_And_Coverage.md` (closed out at implementation commit `d20b88c`; branch state read at `d24d206`)
**Model/effort:** Sonnet or Opus, normal effort. Small, exact, three files plus docs.
Playtest of Brief 5 found that the #147 render rule landed dialogue narration at category `room` — which the client paints muted — so a witness watching a full NPC exchange saw everything except the say lines fade into dim gray. The operator ran a color experiment live and ruled it in. **This amendment is that experiment, made permanent.**
**Scope is CLOSED** to the three changes in §3–§5. Playtest also produced #148, #149, #150, and #151; all four are unmilestoned and explicitly **out of scope here** — no "while we're in there."
---
## 1. Pre-flight
Report each; any failure = stop.
1. `DOCKER_HOST` set and the daemon reachable.
2. On `version_23`, tree clean, synced with origin. Record the tip hash.
3. `SHYLAND_VERSION` reads `23.0-DEV` — **not touched by this amendment.**
4. Pending deploy-time actions from prior V23 briefs: expected **none** (Brief 5 ran `make seed` in session and verified it). Report status.
5. Baseline suite: `python manage.py test apps.shyland -t /app` — expected **347 OK** at Brief 5's close. Record the actual number.
6. `python manage.py makemigrations --check` → no changes. **This amendment has no model changes and no migration.**
7. Report whether stash `428bc16c` (`v23-color-experiment-2026-07-25`) is present in the repo's stash list, and whether the working tree matches it.
---
## 2. Step 0 and the stash
**Step 0 (first action):** save this amendment's full text verbatim to `docs/shyland/Shyland_V23_Brief_5_Amendment_1_Output_Color_Pass.md` (skip if a byte-identical file exists), commit on `version_23`, and **push immediately**. Commit and push at every step boundary after. Branch only — never merge to main on your own initiative.
**The stash.** The operator's live experiment is stashed at `428bc16c`. **This document is the specification, not the stash.** You may `git stash apply` it as a starting point **if and only if** it applies cleanly and you then verify the resulting diff matches §3–§5 exactly, line for line, with every `EXPERIMENT` comment marker stripped and replaced by the permanent issue-referenced comments specified below. If it does not apply cleanly, or the diff diverges in any way, discard the applied changes and implement from this document instead — and say which path you took in the closeout.
**Never `git stash drop`, `git stash pop`, or otherwise mutate the stash stack.** The stash is the operator's; he prunes his own. `apply` only.
---
## 3. Client palette (`django/src/apps/shyland/templates/shyland/game.html`)
Three edits inside the ruled palette block. No hex literals change anywhere — every value is an existing CSS variable — so the chart-as-license set-equality test (`tests/test_b2_amendment4.py`) is untouched by construction. Confirm that in verification.
**3.1 — Split the miss rule.** Replace:
```css
  .msg-combat-miss     { color: var(--muted); }  /* miss, either direction */
```
with:
```css
  /* v23 B5 amendment 1 (#152): misses split by direction — your whiff is
     a warning, their whiff is good news. The legacy rule is retained with
     zero senders; the client's combat family is prefix-matched
     (indexOf('combat') === 0), so both new categories inherit assertive
     announcement and stamping with no client-JS change. */
  .msg-combat-miss     { color: var(--muted); }  /* legacy — zero senders */
  .msg-combat-miss-out { color: var(--warn-color); }    /* your miss */
  .msg-combat-miss-in  { color: var(--success-color); } /* their miss on you */
```
**3.2 — Ambient and narration lift off muted.** Replace:
```css
  .msg-system  { color: var(--muted); }          /* system / ambient */
  .msg-room    { color: var(--muted); }          /* ambient room events */
```
with:
```css
  /* v23 B5 amendment 1 (#152): ambient and narration read as content, not
     chrome. #147 put dialogue narration (greetings, departures,
     connectives) on category room, where muted made it nearly invisible
     mid-exchange. --muted keeps its other users: echo, seg-muted, map
     unknowns, placeholders, the legacy miss rule. */
  .msg-system  { color: var(--value-color); }    /* system / ambient */
  .msg-room    { color: var(--value-color); }    /* ambient room events, narration */
```
**3.3 — `.msg-echo` stays `var(--muted)`.** No edit; stated so the diff is unambiguous.
Nothing else in the palette block moves. Do not touch `.msg-room-render`, `.room-content`, `.msg-success`, or any `seg-*` rule.
---
## 4. Miss categories (`django/src/apps/shyland/management/commands/run_tick_engine.py`)
Two sends, both currently category `combat-miss`. At the branch state read for this amendment they sit at lines 460 and 623; locate them by their text, not by line number.
**4.1 — The player's miss** (character-attacks-NPC branch):
```python
messages.append((character.pk, f"You miss {display}.", 'combat-miss', None))
```
becomes
```python
# v23 B5 amendment 1 (#152): your whiff is a warning, not chrome.
messages.append((character.pk, f"You miss {display}.", 'combat-miss-out', None))
```
**4.2 — The NPC's miss** (NPC-attacks-character branch):
```python
messages.append((character.pk, f"{attacker_ref} misses you.", 'combat-miss', None))
```
becomes
```python
# v23 B5 amendment 1 (#152): their whiff is good news.
messages.append((character.pk, f"{attacker_ref} misses you.", 'combat-miss-in', None))
```
Message text is unchanged in both cases. No other category on either path moves.
---
## 5. The copper-loot line (`django/src/apps/shyland/consumers.py`)
One send, currently category `success` — around line 1663; locate by text:
```python
await self.output(f"You loot {copper_str} from {corpse.display_name}.", "success")
```
becomes
```python
# v23 B5 amendment 1 (#152): parity with the item-loot lines, which have
# been reward/loot-color since v22 B2 amendment 1 (#124).
await self.output(f"You loot {copper_str} from {corpse.display_name}.", "reward")
```
The two item-loot sends (`You loot {line}.`, category `reward`) are already correct — do not touch them.
---
## 6. Tests
New file `tests/test_output_color_pass.py`, `SimpleTestCase` (no DB — every assertion reads template text or Python source). Docstring: `v23 B5 amendment 1 (#152): the output-color pass — the miss split, ambient/narration off muted, and copper loot at reward.`
Read `game.html` once via `pathlib` (the pattern `tests/test_b2_amendment4.py` already uses) and the app's Python sources excluding `tests/` and `migrations/`.
1. **The four CSS rules** — `.msg-combat-miss-out` maps to `var(--warn-color)`; `.msg-combat-miss-in` to `var(--success-color)`; `.msg-system` and `.msg-room` both to `var(--value-color)`. Assert on the rule text, tolerant of whitespace.
2. **The legacy rule survives** — `.msg-combat-miss` is still declared, still `var(--muted)`.
3. **Zero legacy senders** — no non-test Python source contains the standalone category literal `'combat-miss'` (match on quote-delimited exact string so `combat-miss-out` does not false-positive).
4. **Both new senders exist** — `'combat-miss-out'` and `'combat-miss-in'` each appear exactly once across the non-test sources, both in `run_tick_engine.py`.
5. **Copper loot pays reward** — the `You loot ` + `from ` send in `consumers.py` carries `"reward"`; assert the `"success"` literal is gone from that statement.
6. **Combat-family styling coverage** — every `combat-…` category literal appearing in the non-test sources has a matching `.msg-…` rule in `game.html`. A category can never ship unstyled.
7. **No new hex** — the set of color literals in `game.html` is unchanged by this amendment; assert that `tests/test_b2_amendment4.py`'s `ALLOWED_COLORS` still passes set equality by importing and reusing that module's own helper rather than duplicating its logic (if it exposes none, simply assert the two new rules contain `var(`, not `#`).
Do not modify existing tests. Verified at authoring time: no existing test pins `combat-miss`, `.msg-system`, or `.msg-room`. If one turns out to, report it as a deviation with the original intent preserved as an explicit assertion (the Brief 4/5 hygiene pattern).
---
## 7. Verification
Record verbatim output.
7.1 `grep -n "msg-combat-miss\|msg-system\|msg-room " apps/shyland/templates/shyland/game.html` → the legacy rule plus the two new ones; system and room both on value-color.
7.2 `grep -rn "'combat-miss'" apps/shyland/ --include=*.py` → **no output**.
7.3 `grep -rn "combat-miss-out\|combat-miss-in" apps/shyland/ --include=*.py | grep -v tests/` → exactly two hits, both in `run_tick_engine.py`.
7.4 `grep -n "You loot" apps/shyland/consumers.py` → three sites; the copper one now `"reward"`, the two item ones unchanged.
7.5 `python manage.py makemigrations --check` → no changes.
7.6 Full suite → all green. Record the total (expected: 347 baseline + the new tests).
7.7 `python manage.py test apps.shyland.tests.test_b2_amendment4 -t /app` → green, called out separately as the chart-as-license proof.
---
## 8. Documentation
### 8.1 Architecture doc — `docs/shyland/Shyland_Architecture_v23.md`
Update **in place**; no version stamp change. Move the header hash to this amendment's final implementation commit and extend the "Version 23.0 — IN PROGRESS" line with Brief 5 Amendment 1 (#152: the output-color pass).
**§4.16** (output palette / category table) is the substantive edit: the miss category splits into `combat-miss-out` (warn-color) and `combat-miss-in` (success-color) with the legacy `combat-miss` retained at zero senders; `system` and `room` move from muted to value-color, with the reason recorded — #147 put dialogue narration on the `room` category and muted made it unreadable mid-exchange; the copper-loot line moves `success` → `reward` for parity with item loot (#124). State the resulting doctrine plainly, because it is what the operator ruled from play: **gold is speech, green is what went your way (their misses, all loot), yellow is your whiff, the reds are damage, value-color is the world, and muted is true chrome only.** Note that stamping class is unaffected — the v20 B2 stamped/unstamped table does not move; these categories changed color and name, not whether they are events.
### 8.2 Color chart — `docs/shyland/Shyland_Color_Chart.svg`
The chart is organized by color, so this pass edits four "Used for" strings and the baseline caption. Exact replacements (all stay within the widest existing cell, 101 characters):
| Row | Old text | New text |
|---|---|---|
| caption | `baseline: v22 B2 + Amendments 1-5 (arch 892c034) - synced to the palette conformance test ALLOWED_COLORS - sorted by hue` | `baseline: v23 B5 Amendment 1 (#152) - synced to the palette conformance test ALLOWED_COLORS - sorted by hue` |
| `#E8E4D8` value-color | `content; report prose; fight names/counts; pane name, labels, numbers; --loc-room` | `content; report prose; narration + ambient; fight names/counts; pane, labels; --loc-room` |
| `#6b6b80` muted-color | `guides, echo, the unknown, misses, empty cells; --conn-gray` | `guides, echo, the unknown, empty cells; --conn-gray` |
| `#E8D44D` warn-color | `the world declined: resolution + mechanical failures` | `the world declined: resolution + mechanical failures; your misses` |
| `#4caf7d` loot-color / success-color | `gains &amp; good outcomes; V and L bar fills; acuity band; --conn-green` | `gains &amp; good outcomes; their misses; V and L bar fills; acuity band; --conn-green` |
`Shyland_Color_Chart.png` is a rendered twin. Re-export it **only if** a renderer is already available in the container (`rsvg-convert`, `inkscape`, or `cairosvg`). **Do not install tooling to chase it** — if none is present, leave the PNG untouched and report it as stale in the closeout so the operator can re-export.
---
## 9. Issue close — gated
Gated on §7 passing. Close **#152** with a comment recording: the three changes as shipped, the final implementation commit hash, whether the stash applied cleanly or the spec was implemented fresh, the test count, that no hex literals changed and the chart-as-license test stayed green, and the chart/arch-doc updates (noting PNG staleness if applicable).
---
## 10. Deploy — operator-authorized, in-session
Invocation, exactly: **`make build && make migrate`** (never `make prod`, never `make deploy`).
Production already runs these bits from the operator's live experiment, so the player-visible delta is nil; the build re-syncs the deployed image with git. `migrate` will report nothing to apply.
**PENDING DEPLOY-TIME ACTIONS: none.** No migration, no data command, no seed change — the corpus is untouched by this amendment.
Post-deploy sanity: `SHYLAND_VERSION` reads `23.0-DEV`, tick engine running, `/shyland/` returns 200.
---
## 11. Ready after deploy — operator playtest
1. Take a swing and miss — your miss line reads yellow.
2. Let something miss you — its miss line reads green.
3. Kill something and loot the corpse — the copper line and the item lines are the same loot-green.
4. Stand in a checkpoint room while an NPC greets someone, or walk out mid-exchange — narration and connectives read as content, not gray.
5. Presence lines (someone arrives, someone leaves) and effect ticks read as content too.
6. `> command` echo is still muted, and the map's unknown rooms are still muted.
---
## 12. Closeout
Write `docs/shyland/Shyland_V23_Brief_5_Amendment_1_Closeout_Report.txt` in the established format: pre-flight results including the stash status, which path you took on the stash, what shipped, **no migration** stated explicitly, test results before/after, §7 output verbatim, the doc and chart edits (PNG status), the deploy, **PENDING DEPLOY-TIME ACTIONS: none**, deviations, and the commit list with the final implementation commit called out.
Then, as the final instruction: **run the issues report.**
