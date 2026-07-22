Shyland V22 Brief 5 — Amendment 3 — Shortfall Visibility
Type: amendment to `Shyland_V22_Brief_5_Gear_Combat_Wiring.md` (does not count against the cap); combined file-and-fix — files one issue and implements against it, with a HARD GATE between Branch: the current Version 22 worktree branch (`version_22`) — all work, commits, and pushes on that branch Issues: files one new issue (number captured at runtime); no comments on other issues Migrations: NONE. Pending deploy-time actions: NONE — and per the deploy-time rule, pre-flight confirms the parent brief's two data actions (`seed_world`, `rename_proc_stats`) have executed against production (they have — verified 2026-07-21; definitions 0 old-keyed / 9 new-keyed).
Operator ruling from play: five messages that carry consequence render in the muted system voice and go unseen. All five recategorize `'system'` → `'warn'`. This is a category change only — zero wording changes, zero logic changes.
Standing rules

* Work in the Version 22 worktree on its branch. Commit and push at every step boundary — branch only, NEVER merge to main on your own initiative.
* Never remove, prune, or clean up any transient document.
* Test suite runs as `apps.shyland.tests` (#117 workaround, unchanged).
* If any repo fact contradicts this amendment, stop and record the contradiction in the closeout rather than improvising.

Pre-flight

1. Version 22 worktree, tree clean, branch synced.
2. Deploy-time actions check (standing rule): confirm no prior pending data actions remain unexecuted — expected state: the parent brief's two actions already ran against production.
3. `gh auth status` shows repo access.

Step 0 — Self-commit this amendment
Save verbatim to `docs/shyland/Shyland_V22_Brief_5_Amendment_3_Shortfall_Visibility.md` (skip if identical file exists). Commit and push immediately.
Step 1 — File the founding issue
Create one issue. Capture its number from `gh issue create` output — referenced in Step 2 and closed in Step 5.

* Title: `Shortfall and no-effect reports render in the muted system voice`
* Labels: none
* Milestone: `Version 22`
* Body:


```
Operator ruling from play (surfaced healing with 'use N' and missing the
shortfall note): five consequence-bearing messages ship in the 'system'
category, which renders in the muted color, and go unseen. All five
recategorize to 'warn' — wording untouched:

1. "You only had {N}." — use partial fulfillment (the founding case:
   player believes they healed more than they did)
2. "You only had {N}." — drop partial fulfillment
3. "There were only {N} here." — get/loot partial fulfillment
4. "They only had {N}." — buy partial fulfillment (vendor stocked less
   than ordered)
5. "Nothing happens." — use on an effect-less item (functionally a
   refusal; in muted the player may think the command never registered)

Explicitly UNCHANGED, ruled correct as-is: the sell shortfall ("You only
had {N} — the vendor was happy to take them.", already 'success'); the
logout farewell (ambient, muted correct); combat misses (muted by v21
display ruling). Implemented by B5 Amendment 3.

```

⛔ HARD GATE
Verify via `gh issue view`: the issue exists exactly as specified (title, body, milestone `Version 22`, no labels). Any deviation: STOP, run the issues report, closeout explaining, zero code changes.
Commit and push.
Step 2 — Housekeeping comment
On the new issue, post:

```
Ruling record complete in the issue body. Implementation: B5 Amendment 3 —
five category changes 'system' -> 'warn', wording and logic untouched,
tests updated to assert the new category. Closes with the amendment.

```

Step 3 — The five recategorizations
File: `django/src/apps/shyland/consumers.py`. Locate each by its exact message text and verb context (line numbers have shifted across amendments — match on text, not position). In each, change the category argument `'system'` → `'warn'`. No other character of any line changes.

1. `f'You only had {used}.'` — in the use command's partial-fulfillment path.
2. `f'You only had {len(res.items)}.'` — in the drop command's partial-fulfillment path.
3. `f'There were only {len(taken)} here.'` — in the get/loot partial-fulfillment path.
4. `f'They only had {qty}.'` — in the buy partial-fulfillment path.
5. `'Nothing happens.'` — in the use command's no-effect branch.

Do not touch: the sell shortfall (`'You only had {sold} — the vendor was happy to take them.'`, category `'success'`); the logout farewell; combat-miss categories; any other `'system'` send. If the sweep finds additional `'system'` sends beyond the six known (the five above plus the farewell), list them in the closeout untouched — they are future ruling material, not this amendment's scope.
Tests: for each of the five, assert the message fires with category `'warn'` and its wording byte-identical to before. Update any existing tests that assert the old `'system'` category on these lines (the B2/DD §7 shortfall tests are the likely holders — cite which tests changed in the closeout). Add a guard test that the sell shortfall remains `'success'`.
Step 4 — Verification
Full suite green (`apps.shyland.tests`), including the updated and new tests.
Step 5 — Close the founding issue
Close the Step 1 issue (gated on Step 4 passing) with a closing comment noting implementation landed in this amendment.
Step 6 — Architecture doc (GATED, last)
Gated on all steps above complete and passing. Update `docs/shyland/Shyland_Architecture_v22.md` in place (no new file, no version bump; the header hash moves): wherever the output categories / palette voices are documented, note that partial-fulfillment shortfall reports and the no-effect line speak in the warn voice (consequence must be seen), with the sell shortfall's success voice and the ambient system voice (farewell, misses) documented as the deliberate exceptions.
Step 7 — Closeout
Write `docs/shyland/Shyland_V22_Brief_5_Amendment_3_Closeout_Report.txt`: the founding issue number, the five sites as found (file/verb context), which existing tests changed, any additional `'system'` sends discovered and left untouched, any discrepancies, and the final commit hash. Commit and push.
Step 8 — Final instruction
run the issues report
