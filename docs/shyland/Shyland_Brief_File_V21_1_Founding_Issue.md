# Shyland Brief — File the Version 21.1 Founding Issue

This is an ops/housekeeping brief. It files exactly one GitHub issue, adds two comments to it, and runs the issues report. It makes **zero code changes**. It runs on **main** (no worktree).

## Context

Version 21.1 is the project's first **point release** — a surgical release outside the major-version cadence, governed by the point-release rules in `docs/shyland/Shyland_Project_Instructions_v21.md`. Its milestone (`Version 21.1`) already exists. This brief creates the point release's **founding ticket**. A separate design chat session will produce the implementation brief; this brief only puts the issue in place.

The issue arrives **already ruled** by the design chat. Do not triage direction, do not propose alternatives, do not milestone anything else, and do not change any code. The only investigation permitted is the read-only confirmation in Step 3.

## Pre-flight

1. Working tree clean, on branch `main`.
2. Confirm the milestone exists by exact name: `gh api repos/{owner}/{repo}/milestones --jq '.[].title'` must include `Version 21.1`. If it does not, **stop** — report to the operator, do nothing further.
3. Confirm labels `bug`, `emergent`, and `B1` exist: `gh label list`. If any is missing, **stop** — report to the operator, do nothing further. Never create labels.

## Step 1 — Create the issue

Create exactly one issue with `gh issue create`, capturing the issue number from the command output at runtime.

- **Milestone:** `Version 21.1`
- **Labels:** `bug`, `emergent`, `B1`
- **Title:** `No single-session enforcement — two simultaneous logins on one character desync and race`
- **Body** (verbatim):

```
Nothing in the connect path prevents two WebSocket connections for the same character. Each connection independently joins the room and personal channel groups, writes the presence key, and serves commands. Discovered when the operator prepared to log in from a second device while a first session was active.

**Failure modes with two live sessions:**

1. **Channel-group desync (primary).** `self.room_group` is per-connection consumer state, updated only when *that* connection processes a move. Session A moves the character; session B's consumer stays subscribed to the old room's broadcast group — it keeps rendering the old room and map, receives the old room's broadcasts, and its commands act in a mix of the real room (fresh-fetch paths) and the ghost room (cached `self.character` paths). Same failure class as the v19 respawn desync ("client stayed subscribed to the death room"), but no cross-notify event exists for a move made by the character's *other* connection.

2. **Per-connection flag drift.** `_character_is_dying` and `last_direction` live on the consumer instance. Engine events on the `player_{pk}` group reach both connections, but consumer-originated state changes do not cross-notify.

3. **Interleaved command races.** Commands are serialized within one consumer but interleave freely across two. Vitality/bar mutations are safe (#52's F()/Least invariant), but wallet mutations in buy/sell, equip-slot displacement, and combat-action queuing were all written assuming one actor per character — double-spend, duplicate CombatActions in a round, and slot-capacity violations are all plausible.

**What already works:** the Redis presence layer alone is concurrent-safe by design — the v19 per-connection ownership token makes the `who` key newest-wins (a stale session can never delete a newer session's key). That is the only place concurrent sessions were ever considered; it protects exactly one key.

**Urgency:** real human players are now being onboarded. Logging in from a second device is an innocent, expected action, and today it produces silent state corruption and races.
```

## Step 2 — Record the design ruling as a comment

Add one comment to the issue just created (verbatim):

```
**Design ruling (design chat, 2026-07-18):** newest connection wins; the oldest is kicked — the classic MUD "reconnect seizes your link" behavior, philosophically consistent with the presence layer's newest-wins token design.

Ruled direction (mechanism sketch, final design in the Version 21.1 design chat):

- On connect, after joining the `player_{pk}` group and writing the presence key, the new connection sends a `superseded` event to the `player_{pk}` group carrying its own per-connection presence token.
- Every consumer's `player_message` handler checks the event's token against its own; a consumer whose token does not match prints a farewell (e.g. "Your session has been taken over from another location.") and closes through the **normal disconnect path** — the guarded presence delete, group discards, and heartbeat cancellation all behave correctly for free (the old session's guarded delete is a no-op against the new session's key).
- **Combat carries over untouched, by design.** `CombatSession` is DB state keyed to the character, and the tick engine delivers combat output to the `player_{pk}` group, not to a socket. The new connection joins that group on connect; the next round's output lands on the new screen. No handover logic exists or is needed.
- No new models anticipated; the change is expected to live in the consumer's connect path and `player_message` handler.

Scope per the point-release rules: this is the founding ticket for Version 21.1 — one bucket (B1), one implementation brief. Anything discovered while building files thin into the normal pipeline.
```

## Step 3 — Read-only triage confirmation

The design chat asserted the no-guard reading from Architecture v21, not from code. Confirm it against the source:

1. Read `django/src/apps/shyland/consumers.py` — specifically `connect()` and the `player_message` handler.
2. Confirm: (a) no existing mechanism refuses, closes, or supersedes a second connection for the same character; (b) the per-connection presence token from the v19 rework exists and is available at connect time (this is the token the ruling reuses).
3. Add one short diagnosis comment to the issue stating what you confirmed, quoting the relevant line numbers/function names. If the code **contradicts** the ruling's assumptions in any way — a guard already exists, the token is not available where the ruling assumes, anything — say so explicitly in the comment and flag it in your closeout. **Change no code either way.**

## Verification

- Exactly **one** issue was created by this brief — no more, no fewer.
- The issue carries milestone `Version 21.1` and exactly the labels `bug`, `emergent`, `B1`.
- The issue has exactly two comments from this brief: the design ruling and the triage confirmation.
- Working tree is still clean: `git status` shows no modified, added, or deleted files (this brief makes zero code changes).

## Closeout

Report the issue number captured at runtime, the result of the Step 3 confirmation (including any contradiction found), and then:

run the issues report
