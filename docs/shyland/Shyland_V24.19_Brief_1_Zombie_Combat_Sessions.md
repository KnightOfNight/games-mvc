# Shyland V24.19 — Brief 1: Zombie Combat Session Reaping (#218)

- **Release:** Version 24.19 (milestone `Version 24.19`, GitHub milestone #39)
- **Founding ticket:** #218 — Zombie combat sessions: all NPCs dead but session stays active — loot blocked 'in combat'; stale sweep can't reap
- **Branch:** `version_24_19` (cut from main @ 4937b0c, the V24.18 merge)
- **Authored by:** V24.19 design session, 2026-08-10 (ruling recorded on #218 the same day, operator-confirmed)
- **Scope class:** runtime code only — **no model changes, no migration, no seed data, no data actions, deletions 0.** The architecture doc hash **MOVES** (architectural runtime change to the tick engine's session lifecycle).

## Pre-flight

- This is the **first implementation brief of Version 24.19** — it carries the version-start ritual (Step 1).
- **Prior pending deploy-time actions: none.** V24.18 closed with an empty tail (deploy-prod only, the fourth consecutive); no PENDING DEPLOY-TIME ACTIONS block is open anywhere in V24. This brief creates none.

## The bug (context — full forensics on #218)

`CombatSession.npcs` is M2M: one `NpcInstance` can belong to multiple players' sessions. The engine's kill path (`run_tick_engine.py`, the `npc.vitality_current <= 0` block at ~534–596) removes the dead NPC from the **killer's session only** and closes only that session. Every other session holding that NPC keeps the dead row attached, can never fire its own last-kill deactivation, and its members are stuck behind the in-combat gate (loot refused) for minutes. The stale sweep cannot reap the zombie because `update_session_tick` (~259) refreshes `last_tick_at` unconditionally before any liveness check. Root cause confirmed by deliberate live reproduction on prod, 2026-08-08 (sessions 1500 and 1509; bug fires regardless of `first_attacker`).

## The ruling (design rules — binding, no deviation)

Recorded on #218 (2026-08-10, operator-confirmed). **No GDD change ships with this release** — GDD §5 already describes intended behavior; this is a mechanical defect. **#220 (multiplayer combat model) is explicitly out of scope:** no aggro, attribution, or session-sharing semantics change — this brief is orphan-session hygiene only.

1. **Kill path goes M2M-wide (the semantic fix).** When an NPC dies, it is removed from **every** active session holding it, not just the killer's. Each *other* affected session left with zero living NPCs closes on the standard end pattern within the same engine round: `is_active=False`, `focus_npc=None`, `release_session_npcs()`, its members receive **"Combat has ended."** (category `reward`, the existing line verbatim), a fight-clear payload, and a fresh status. The killer's own session keeps its existing flow untouched.
2. **Other-session focus is never silently dangling.** If the dead NPC was another still-active session's focus (that session retains other living NPCs), focus reassigns to that session's next living NPC with the standard announcement ("You turn your attacks on {name}.") — GDD §5: focus changes are never silent.
3. **Loop-head self-heal, placed *before* `update_session_tick`.** Any active session the engine picks up with zero living NPCs (dead rows attached or no rows at all) closes immediately with the same messaging, instead of ticking. Because the check precedes the tick update, a zombie never refreshes its own `last_tick_at` — the stale sweep is restored as a backstop by construction. Stuck window for any leak path, present or future, caps at one engine tick.
4. **The disengagement-restore rule is preserved untouched.** `release_session_npcs()` already filters `is_alive=True` and skips NPCs shared with another active session (GDD §5 Disengagement, v23 #25). Dead NPCs are never restored; a living shared NPC another player is still fighting never snaps to full. No changes to `release_session_npcs`.
5. **Path audit: confirmed single site.** Exactly one place in game code kills an NPC (~line 535); the only other `is_alive=False` reference is the respawn reaper (~line 803). No further audit work.

## Step 1 — Version constant (opening act)

In its **own commit**: bump `SHYLAND_VERSION` from `"24.18"` to `"24.19-DEV"` and move the pin-test assertion in the same commit. Then run the version-start `make deploy-dev` from the worktree.

## Step 2 — Implementation

**File:** `django/src/apps/shyland/management/commands/run_tick_engine.py` (both parts). No other game-code files change.

### Part A — kill path M2M-wide removal

In the kill block (inside `execute_actions`, after `npc.save(update_fields=['is_alive', 'respawn_at'])` at ~538): after the existing killer's-session handling, process the other sessions:

- Query the dead NPC's other active sessions: `npc.combat_sessions.filter(is_active=True).exclude(pk=session.pk)`.
- For each such session: remove the NPC row (`other.npcs.remove(npc)`), then evaluate:
  - **No living NPCs remain** (`other.npcs.filter(is_alive=True).exists()` is False): close it — `is_active=False`, `focus_npc=None`, save, `release_session_npcs(other)`. Queue for each of its member characters: `("Combat has ended.", 'reward')` via the round's pk-addressed `messages` list, a fresh status via `statuses`, and send that session's fight-clear payload after the round (the `messages`/`statuses` flush at ~704–712 is pk-addressed, not session-bound — other-session members are deliverable there; `build_fight_payloads` on an inactive session already returns the clearing payload).
  - **Living NPCs remain** and the dead NPC was that session's `focus_npc`: reassign focus to the session's next living NPC (canonical `(spawned_at, pk)` order), save, and queue the standard announcement `("You turn your attacks on {display}.", 'combat')` to its members. The display name composes ordinal-aware against **that session's** remaining live NPCs (`npc_display_name`).
- No room broadcast changes: the existing "X has slain Y!" room message already informs bystanders of the death.

### Part B — loop-head self-heal

In the active-sessions loop (~268), **before** `update_session_tick(session)`: re-read the session's current DB state (one `@database_sync_to_async` helper returning current `is_active` plus living-NPC existence — **do not trust the prefetched cache**, which is stale for any session Part A closed earlier in this same tick's loop).

- If the session is no longer active in the DB: `continue` silently (already closed and messaged this tick).
- If active with zero living NPCs: close it on the standard pattern — `is_active=False`, `focus_npc=None`, save, `release_session_npcs()`, "Combat has ended." (`reward`) to each member, fight-clear payload, fresh status — then `continue`. **`update_session_tick` must not run for this session** (no `last_tick_at` refresh — this ordering is what restores the stale sweep).
- Log line: `Combat session {pk} closed (self-heal: no living NPCs)` at info level, mirroring the stale-close log.

The existing stale sweep (`get_stale_sessions`/`close_session`, ~97–169) is untouched — it remains the outer net.

## Step 3 — Tests

**New file:** `django/src/apps/shyland/tests/test_zombie_sessions.py`, engine-harness style (instantiate `Command`, stub `broadcast_to_room` / `send_to_player` / `_online_character_pks`, drive the relevant `process_*` coroutines with `asyncio.run` — the established pattern in `tests/test_combat_state.py`; reuse the existing world/character/NPC factory helpers).

Required pins:

1. **Cross-session kill closes the bystander (the headline fix):** characters A and B each in their own active session, both sessions holding the same single NPC; A's queued attack kills it. Same round: both sessions `is_active=False`, the NPC row removed from both, B received "Combat has ended." (`reward`), and B is no longer in combat (`combat_sessions.filter(is_active=True)` empty — the loot gate's predicate).
2. **Cross-session focus reassignment:** B's session holds the shared NPC (as B's focus) plus a second living NPC of its own; A kills the shared NPC. B's session stays active, its `focus_npc` moves to the surviving NPC, B received the focus announcement, and B's session was *not* closed.
3. **Loop-head self-heal, dead row attached:** a manufactured zombie (active session, one dead NPC row attached — the live forensic signature) is closed on the next engine pass; member receives "Combat has ended."; and the session's `last_tick_at` is **unchanged** (the no-refresh assertion — this pins the stale-sweep restoration).
4. **Loop-head self-heal, zero rows:** an active session with no NPC rows at all closes identically.
5. **Dead NPCs never restored:** after both close paths, the dead NPC's `is_alive` remains False and `vitality_current` remains 0 (pins ruling 4 / the `release_session_npcs` living-only filter).
6. **Living shared NPC never snaps to full (regression):** a living NPC in two active sessions keeps its current (damaged) vitality when one session closes while the other stays active (the v23 #25 multiplayer guard, pinned against this brief's new close paths).

**Expected conversions: zero.** No existing test was found at design time that pins the leaked-session behavior. If any existing test fails under the new close paths, that is a **deviation — record it in the closeout report**, do not silently re-oracle.

## Step 4 — Verification

Full suite in-container, the only working form:

```
docker exec <django container> python manage.py test apps/shyland/tests
```

All tests pass (was 566/566 at V24.18 close; expect that plus the new file's additions). Verification gates Steps 5–7.

## Step 5 — Dev deploy

`make deploy-dev` from the worktree once implementation and verification pass.

## Step 6 — Operator playtest checklist (dev stack)

The natural playtest is the exact live reproduction from #218, now expected to pass. Requires **two accounts** (human interaction — operator's own steps):

1. Player A and player B both engage the **same NPC**, each from their own session (either engagement order — the bug was confirmed independent of `first_attacker`).
2. A lands the kill. **B immediately sees "Combat has ended."** (reward color), B's fight pane clears, and B is out of combat within a second — no stuck window.
3. B can `loot` immediately (the original failing surface).
4. Variant: B fights the shared NPC **plus** a second NPC of B's own. A kills the shared NPC. B stays in combat, sees the focus shift to the remaining NPC, and the fight continues normally.
5. Sanity: an ordinary solo kill still ends combat cleanly with loot working (the unchanged killer's-session path).

## Step 7 — Architecture doc (LAST, gated)

This step is gated on all implementation and verification steps above being complete and passing.

`docs/shyland/Shyland_Architecture_v24.md`, updated **in place**:

- **Header:** stamp 24.18 → 24.19; the "as of commit" hash **MOVES** to this brief's implementation commit; prepend the v24.19 brief-1 summary to the header's change-summary chain in the established style.
- **§4.9 (Tick Engine):** amend the combat-session lifecycle description to record: kill-path NPC removal is M2M-wide with other-session closure/focus-reassignment; the loop-head self-heal (zero-living-NPC sessions close before ticking, `last_tick_at` never refreshed for them — the stale sweep's restoration); and the fresh-DB-state read at the loop head.
- Sweep the doc (`grep -n 'last_tick_at\|stale'`) for any statement implying the tick refresh is unconditional or that the kill path touches only one session; update only where factually stale.

## Closeout

- Closeout report as `.txt` in `docs/shyland/` (stub created at Step 0 per the session ritual, completed in place): final commit hash, deviations (expected: none), deletions 0/0, **no PENDING DEPLOY-TIME ACTIONS block** (nothing pending), and the **operator playtest disposition** verbatim.
- Commit and push at every step boundary — branch only, never merge.
- `SHYLAND_VERSION` remains `24.19-DEV` at session end; the closeout session stamps `24.19`.
