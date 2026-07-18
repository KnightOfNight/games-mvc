Shyland_V21.1_Brief_1_Session_Takeover.md
Point release Version 21.1 — Brief 1 of 1. Founding ticket: #116.
This brief implements single-session enforcement for Shyland characters: the newest WebSocket connection for a character takes over; any older connection prints a farewell and closes. It touches `django/src/apps/shyland/consumers.py`, the game client template, and (as the final gated step) the architecture doc — nothing else. No model changes; no migration.
This is a point release under the point-release rules in `docs/shyland/Shyland_Project_Instructions_v21.md`: one brief, one founding ticket, scope never grows. Read the Discovery Rule below before starting.
Pre-flight

1. Run `python3 scripts/check_docker_host.py` and gate on its exit code per CLAUDE.md.
2. Working tree clean on the session's working branch.

Step 0 — Commit this brief
Save the full text of this brief, verbatim, to `docs/shyland/Shyland_V21.1_Brief_1_Session_Takeover.md`. If an identical file already exists, skip the write. Commit it (message: `Add brief: Shyland_V21.1_Brief_1_Session_Takeover.md`) on the session's working branch, then push the branch to origin immediately — before proceeding to anything else. The operator watches progress on GitHub; this first push is how they see the brief has been received and started.
Push cadence (standing for this entire brief)
Commit and push the working branch to origin at every step boundary — after Step 0, after Step 1's issue comment (nothing to push there, but any subsequent file change pushes), after the server implementation (Step 2), after the client implementation (Step 3), after verification artifacts (Step 4, if any test files were added), and after the architecture doc update (Step 6). Push the branch only — never merge to main; merging is the operator's action. Intermediate commits may be small and work-in-progress; that is desired, not a problem. The operator follows the branch on GitHub in near-real time.
Discovery Rule (standing for this entire brief)
If, at any point while implementing, you find a bug or defect other than the one this brief fixes — pre-existing, adjacent, anything — do not fix it and do not widen this brief's changes. Instead: file a new GitHub issue for it immediately with `gh issue create`, writing the most complete body you can from what you observed (file, function, line numbers, reproduction reasoning, suspected mechanism). You may apply the `bug` label if you genuinely believe it is one. Apply no milestone and no bucket label. Then continue this brief. List every issue you filed this way in your closeout.
Step 1 — Record the design rulings on #116
Add one comment to issue #116 (verbatim):

```
**Design rulings for the implementation brief (design chat, 2026-07-18):**

1. **Broadcast point:** the supersede event fires in `connect()` immediately after the `player_{pk}` group join and `session_token` mint, before the presence write. Ordering with the old session's guarded presence delete is safe in either interleaving: if the old session's delete runs before the new presence write, it deletes the old value and the new unconditional SET follows; if after, the guarded compare no-ops against the new value.
2. **Old client behavior:** farewell renders, socket closes server-side, client suppresses the reconnect placeholder — but stays on the page with the farewell visible. No navigation. Refresh-to-retake remains a legitimate action.
3. **No room broadcast:** witnesses see nothing. The character never left the room; only the link moved.
4. **Farewell wording** is authored creative content (design-chat authored, not operator-reviewed), category `system`.
5. **Discoveries:** any other bug found while implementing is filed as its own detailed issue by CC at the moment of discovery — no milestone, no fix, no scope growth. (Operator ruling, superseding the default thin-filing for this brief.)

```

Step 2 — Server implementation (`django/src/apps/shyland/consumers.py`)
2a. Fire the supersede broadcast in `connect()`
Immediately after the existing `self.session_token = uuid.uuid4().hex` mint (line ~301, which itself follows the `player_{pk}` group join), and before the presence write, send a group message to the character's personal group:

```python
await self.channel_layer.group_send(
    self.player_group,
    {
        'type': 'player_message',
        'event': 'superseded',
        'token': self.session_token,
        'ts': envelope_ts(),
    }
)

```

Use the consumer's existing attribute name for the personal group (`self.player_group` or whatever `connect()` actually joins — match the code, do not invent a name). The payload carries no `text`, `category`, or `status` fields. `ts` is stamped at creation per the envelope rules (Section 4.13 of the architecture doc); import of `envelope_ts` already exists in this module.
2b. Handle `event == 'superseded'` in `player_message`
Add a branch to the `player_message` handler (line ~1988), checked before the existing `text`/`category`/`status` delivery and the `dying`/`respawn` event handling:

* If `event == 'superseded'`:
   * If `content['token'] == self.session_token` → this is the connection that fired it. Return immediately; deliver nothing.
   * Otherwise this consumer has been superseded:
      1. Send the farewell via the normal output path, category `system` (exact text below).
      2. Send `{'type': 'output', 'event': 'superseded', 'ts': envelope_ts()}` through `send_json` — the client-facing event, following the `{'event': 'quit'}` pattern from `cmd_quit` (a `text`-less event message; match the quit event's exact message shape as it exists in the code, changing only the event name).
      3. `await self.close()` — the normal server-side close. Everything after is the existing `disconnect()` path, none of it duplicated here: guarded presence delete (a no-op or harmless delete against the new session's key, per ruling 1), group discards, heartbeat cancellation, `last_seen` touch.

Farewell text (verbatim, authored):

```
The world's attention shifts — your story is being told through another window now. This one falls quiet.

```

Rules that must hold:

* The superseded close is not a command and passes through no command gates: it fires even if the character is dying, and even if the character is in combat. The in-combat refusal belongs to `quit` only — a takeover mid-fight is the entire point (combat is DB state; output follows the `player_{pk}` group; the new connection inherits the fight with zero handover logic).
* No room broadcast of any kind (ruling 3).
* No new models, no migration, no changes to the tick engine, presence Lua scripts, or `disconnect()`.

Step 3 — Client implementation (game client template)
In the game client template (the file `cmd_quit`'s `event == 'quit'` handling lives in — locate it; the architecture doc calls it `game.html`):

* Handle `event == 'superseded'`: set a flag (e.g. `superseded = true`, parallel to the existing `quitting` flag).
* In the socket close handler, when the flag is set: suppress the "Connection closed. Refresh to reconnect." placeholder — and do nothing else. No navigation, no redirect, no reload. The farewell line, already rendered through the normal output path (and announced by the polite ARIA live region like any other output), stays visible as the last thing on screen.
* A close without the superseded or quit event behaves exactly as before.

Step 4 — Verification (gate for everything after it)

1. `make build && make restart` completes cleanly.
2. Two-connection check. Using a Channels `WebsocketCommunicator`-based test (if the app has an existing test harness, put it there; if not, a standalone test module under the shyland app is acceptable) or an equivalent scripted check against the running stack:
   * Connect session A for a character; connect session B for the same character.
   * Assert A receives, in order: an output message containing the farewell text (category `system`), then a message with `event == 'superseded'`, then the socket closes.
   * Assert B receives neither the farewell nor a client-facing superseded event, and remains connected and functional (e.g. a `look` round-trips).
   * Assert the Redis presence key for the character holds B's token value after the dust settles.
3. Single-session check (regression of normal flow): a single fresh connection connects and plays normally — the supersede broadcast it fires is ignored by its own consumer (token match).
4. Code check: grep confirms no room-group broadcast was added anywhere in the new code paths.

Steps requiring human interaction — two real browsers, iPad takeover, mid-combat takeover with a second account — are the operator's, performed after deploy. Never simulate or declare them complete.
Step 5 — Close #116
Gated on Step 4 passing. Close issue #116 with a closing comment summarizing what shipped and referencing the verification results.
Step 6 — Architecture doc update (last, gated)
This step is gated on all implementation and verification steps above being complete and passing.
Update `docs/shyland/Shyland_Architecture_v21.md` IN PLACE. Do not create a new file. Do not `git rm` anything. Per the point-release document rules:

* Header: version stamp moves to 21.1. The architectural-changes commit hash moves to the commit containing this brief's code changes (this is an architectural change).
* Section 4.3 (WebSocket consumer): add a subsection "Single-session enforcement (v21.1, #116)" describing: the supersede broadcast in `connect()` (placement relative to the token mint and presence write, and why either interleaving with the old session's guarded delete is safe), the `player_message` `superseded` event branch (token comparison, farewell, client event, normal close), the not-a-command rule (fires through dying and combat), the no-room-broadcast rule, and combat carryover (DB-state session, personal-group output, no handover logic). Update the `player_message` handler's documented event list (`dying`/`respawn`) to include `superseded`.
* Section 4.3 presence subsection: add one sentence noting the v19 per-connection token now also drives session takeover, with a pointer to the new subsection.
* Client section covering `game.html` close handling: note the `superseded` flag alongside the `quitting` flag and its suppress-only (no navigation) behavior.
* Touch only those sections.

Closeout
Commit and push everything on the session's working branch — branch only; do not merge to main (the operator merges after review and playtest). The closeout report (committed as a `.txt` in `docs/shyland/` per standing practice) must include: the final commit hash, the verification results, any Discovery Rule issues filed (numbers and one-line summaries), and confirmation that the architecture doc stamp reads 21.1 with the hash moved.
Then: run the issues report
