# Shyland V20 Brief 1 — Amendment 2: Record Room Visits on Arrival, Not on Description

Implements GitHub issue **#50**. Amendment to the applied v20 Brief 1; does not count against the brief cap. Self-contained. **Never remove or prune any transient document** — the operator prunes.

## The bug (diagnosed and screenshot-confirmed)

`RoomVisit` is created inside `_resolve_room_rendering` (`consumers.py` ~line 1983), reached only via `send_room_description`. `cmd_move`'s aggro branch deliberately skips the room description (ambush design) and starts combat instead — so **rooms entered under aggro never record a visit**. The map's current-room special case masks it while standing there; on leaving, the room vanishes from fog-of-war. Holes appear in the map wherever first entry was an aggro entry (most of the Whistling Sink), lines vanish because lines draw only between two drawn rooms, and revisits read as first visits. Latent since v19 Brief 8 coupled visit recording to rendering; the map made it visible. Side effect of the same coupling: aggro first entries also never received the v19 guaranteed first-entry long description.

## The fix — decouple

### 1. Record visits at arrival time, unconditionally

In every code path where a character arrives in a room, record the visit immediately after `move_character` (or its equivalent) and before any aggro check or description logic, capturing whether it was new:

- `cmd_move` (both branches — aggro and peaceful)
- `cmd_travel` (arrival at the destination node's room)
- respawn/death arrival at the recall room
- any other arrival path found in the audit below

Implementation: a small `@database_sync_to_async` helper, e.g. `record_room_visit(character, room) -> bool` returning `created`, using the existing `get_or_create`. Call it once per arrival; pass the result forward where needed.

**Audit step (required):** grep for every site that changes `current_room` or delivers a character into a room (move, travel, respawn, superuser teleport/administrative moves if any exist) and confirm each records the visit. List every arrival path and its disposition in the closeout.

### 2. Make `_resolve_room_rendering` read-only with respect to visits

It no longer calls `get_or_create`. Signature/behavior: it receives the `first_visit` boolean from the caller (the arrival-time recording) when the caller just arrived, or looks the visit up read-only for non-arrival renders (`look`). Preserved behavior, exactly: first entry and `look` always show the long form; revisits obey `brief_mode`. Peaceful first entries must render the long description exactly as today.

### 3. Aggro-path behavior otherwise unchanged

Aggro entries still skip the room description and go straight to the snarl + combat (design intact). The only change is the visit landing. (Whether post-combat should auto-describe the room is explicitly out of scope — a design question for some later version, not this amendment.)

## No data repair

Missing visits from playtesting self-heal: the next entry into each affected room records it. No backfill script, no migration, no model changes.

## Verification (all must pass before the doc touch)

1. Enter a never-visited room that triggers aggro; while fighting, the map shows the room (current-room case). Leave. The map still shows it, and re-entering renders as a *revisit* (brief-mode honored, no first-entry long form).
2. Walk a chain of aggro rooms in the Whistling Sink: the map draws a connected chain behind you with no holes — the Wind Gallery control case from the screenshots now renders connected on first pass.
3. Peaceful first entry still shows the long description; peaceful revisit honors `brief_mode`; `look` always long. (The v19 rule intact.)
4. `travel` records a visit at the destination; death/respawn records a visit at the recall room.
5. Regression: no duplicate visit rows (get_or_create semantics), no double descriptions, no change to aggro engagement messaging or combat behavior.
6. Badge spot-check (screenshot follow-up from image 1): in "The Fallen Light" (exits west, down), the current-room badge on the map reads **D**, not U — verify the U/D badge letters are driven by the room's actual up/down exits. If a swap is found, fix it in this amendment and report it; if the screenshot was a misread, report that.

Close **#50** with a closing comment referencing this amendment, gated on the checks above.

## Architecture doc touch (LAST, gated)

In `docs/shyland/Shyland_Architecture_v20.md`, update the fog-of-war/RoomVisit description: visits are recorded at arrival time in all arrival paths (move/travel/respawn), independent of room-description rendering; `_resolve_room_rendering` consumes visit state read-only. Note the #50 fix in the Brief 1 amendment trail alongside #49. No version bump, no file removals.

## Closeout report

Commit hash, the arrival-path audit list, all verification results including the badge finding, and #50 closed.
