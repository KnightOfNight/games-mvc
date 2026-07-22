Shyland V22 Brief 6 — Tick Expiry Crash Fix
Type: implementation brief (the fifth and final implementation brief of the v22 cap) Branch: the current Version 22 worktree branch (`version_22`) — all work, commits, and pushes on that branch Issues: #135 — pulled into Version 22 by operator ruling; closes with this brief, gated on verification Migrations: NONE. Pending deploy-time actions: NONE (pre-flight confirms none outstanding).
Operator ruling: #135 rides Version 22 — main must not gain a known, 100%-reproducible engine-killer at the merge. The defect (per the issue's cite-checked triage): the full-expiry branch of `process_effects` calls the synchronous helper `_expiry_message_for_effect(parent)` directly in the async tick loop; the helper runs a fresh ORM query (`effect_instance.definition.components.order_by('order').first()`), raising `SynchronousOnlyOperation` and killing the whole tick process on every full expiry of a timed effect. The scope is exactly that defect and its identical siblings — nothing else.
Standing rules

* Work in the Version 22 worktree on its branch. Commit and push at every step boundary — branch only, NEVER merge to main on your own initiative.
* Never remove, prune, or clean up any transient document.
* Test suite runs as `apps.shyland.tests` (#117 workaround, unchanged).
* Scope lock: no redesign of expiry messaging, no wording changes, no category changes, no touches to effect magnitudes or the acuity clamps (#133 stays untriaged), no refactor of `process_effects` beyond the async-safety fix.
* If any repo fact contradicts this brief, stop and record the contradiction in the closeout rather than improvising.

Pre-flight

1. Version 22 worktree, tree clean, branch synced.
2. Deploy-time actions check (standing rule): confirm none outstanding.
3. `gh auth status` shows repo access.
4. `DOCKER_HOST` set (production container verification in Step 5 needs it).

Step 0 — Self-commit this brief
Save verbatim to `docs/shyland/Shyland_V22_Brief_6_Tick_Expiry_Crash_Fix.md` (skip if identical file exists). Commit and push immediately.
Step 1 — Housekeeping, then gate

1. Move #135 to milestone `Version 22` (`gh issue edit 135 --milestone "Version 22"`).
2. Post this comment on #135, verbatim:


```
Operator ruling: pulled into Version 22 — the merge must not hand main a
known 100%-reproducible engine-killer while real players are onboarded;
the fix is surgical and takes the version's final implementation-brief
slot (V22 Brief 6). The V23 milestone assignment is superseded. Scope is
the async-safety defect and identical siblings in the tick loop only —
the expiry-message design, effect tunings, and #133's questions are all
untouched.

```

⛔ GATE
Verify via `gh issue view 135`: milestone `Version 22`, comment posted intact. Any deviation: STOP, run the issues report, closeout explaining, zero code changes.
Commit and push.
Step 2 — The fix
File: `django/src/apps/shyland/management/commands/run_tick_engine.py`, `process_effects`, the full-expiry (`all_expiring_now`) branch (~line 1230 at branch state f17039c).
The invariant, which must not be deviated from: no synchronous ORM executes on the async tick path, and the full-expiry player message is actually delivered. Implement it as one of exactly the two shapes the triage named — choose whichever is cleaner in the code as found, and cite the choice in the closeout:

* (a) Wrap at the call site: `msg = await database_sync_to_async(_expiry_message_for_effect)(parent)` — the helper stays documented-sync and is invoked correctly; or
* (b) Prefetch: extend the loading of `parent` (the same loader whose `select_related` already makes the per-component sibling path safe) so `definition.components` is prefetched, making the helper's query-free path hold — only valid if the helper is then verifiably query-free on prefetched data (the triage notes `.order_by('order').first()` defeats prefetch as written, so (b) requires the helper to consume the prefetched cache, e.g. sorting in Python — if that exceeds a trivial change, use (a)).

When in doubt: (a). It is the minimal, unambiguous fix.
Sibling sweep (bounded): within `run_tick_engine.py`'s async paths only, find any other direct call into a documented-synchronous helper that unconditionally executes ORM queries (the same crash class). Fix identical instances the same way; list anything looser than identical in the closeout untouched — report, don't fix.
Step 3 — Regression tests
New tests (placed with the tick-engine tests as found): a timed effect running to full natural expiry (all components expiring on the same tick) completes the tick without exception, delivers the expiry message, closes the parent effect, and leaves no partial state for the next tick's sweep; and the per-component sibling path still behaves as before. If the existing test harness cannot drive the async tick loop, build the minimal async test in the established `WebsocketCommunicator`/async-test style already in the suite — cite the approach in the closeout.
Step 4 — Verification
Full suite green (`apps.shyland.tests`) including the new tests.
Step 5 — Production reproduction check (the field proof)
After the suite passes and a production build (operator-authorized in session): reproduce #135's own recipe — apply a short timed effect, let it fully expire, and confirm via `docker logs` and the container restart count that the ticker does not die and the expiry message reaches the player. Record the before/after in the closeout. (This is the one step that touches production; it changes no data beyond normal gameplay effects.)
Step 6 — Close #135
Close #135 (gated on Steps 4–5 passing) with a closing comment noting the fix shape chosen and the field reproduction result.
Step 7 — Architecture doc (GATED, last)
Gated on all steps above complete and passing. Update `docs/shyland/Shyland_Architecture_v22.md` in place (no new file, no version bump; the header hash moves): the tick-engine section documents the expiry path's async-safety rule — synchronous helpers cross into the tick loop only via `database_sync_to_async` or verifiably prefetched data — with #135 as the founding case.
Step 8 — Closeout
Write `docs/shyland/Shyland_V22_Brief_6_Closeout_Report.txt`: the fix shape chosen and why, the sibling-sweep findings (fixed vs reported), the test approach, the production reproduction before/after, any discrepancies, and the final commit hash. Commit and push.
Step 9 — Final instruction
run the issues report
