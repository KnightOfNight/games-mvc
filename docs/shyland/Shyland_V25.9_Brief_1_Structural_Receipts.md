# Shyland V25.9 Brief 1 — Structural Receipts

**Release:** Version 25.9 (milestone 61) · **Founding ticket:** #302 (sole milestone member)
**Branch:** `version_25_9` · **Written:** 2026-08-28, V25.9 design session
**GDD:** §10.11 "Structural receipts (v25.9, #302, pending implementation)" — committed e302f81

## 0. The rule this release ships

**The sudo bot never invents a value it should have read from the database.** Every id it acts on and every action it claims must trace to a tool receipt from the current turn — enforced by machinery, never asked of the model. Three layers (operator-ruled 2026-08-28, recorded on #302):

1. **Door-side:** `move` gains a `waypoint` destination — lookup-and-act atomic in the door; the bot never handles a room id for a taught place.
2. **Bot-side:** a typed receipts ledger at the tool-execution choke point — an id-typed argument no current-turn tool result produced (in the matching id-space) is refused before it reaches the door.
3. **Delivery-side:** `answer` gains machinery-only action receipts, rendered by the game as their own lines in a form model prose cannot produce.

Plus: id-typed tool-schema descriptions carry the "from `<tool>`, this turn" contract explicitly. The v25.8 prompt standing orders remain in force — defense-in-depth, no longer the only line.

**Technical coherence (#252):** every structural claim in this brief was verified against the code on `version_25_9` (tip e302f81) at writing time. Each section cites its verification. Recall was not used as a source.

## 1. Opening act — version constant (standing requirement 1)

First implementation brief of the release: bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` from `"25.8"` (confirmed at `version.py:8`) to `"25.9-DEV"` **in its own commit**, moving the pin-test assertion in the same commit. Then run the version-start `make deploy-dev` from the worktree. Push.

## 2. Door-side: `move` gains a `waypoint` destination form

**Site:** `a_move` in `django/src/apps/shyland/mc_door.py` (confirmed at mc_door.py:779–835).

**Verified current shape:** `a_move` requires exactly one of `to_name` / `to_room_id` via `has_name == has_id` XOR check (mc_door.py:786–791); refuses `in-combat`; resolves `to_room_id` through `_room_by_id` with `not-found` on a miss; captures `origin_room` before the move; returns `{'room': _room_dict(destination), 'from_room': _room_dict(origin_room)}`.

**Change:** a third mutually exclusive destination key, `waypoint` (string, the memory name):

- The exactly-one check extends to all three keys; the `bad-params` message becomes: `"Exactly one of 'to_name', 'to_room_id', or 'waypoint' is required."`
- Resolution: the calling agent's own store, the memory verbs' addressing law — `AgentMemory` filtered on `agent=_agent_user(agent_name)`, `kind=AgentMemory.KIND_WAYPOINT`, `name__iexact=<waypoint>` (the same scoping `_remember`/`_forget` use, confirmed at mc_door.py:1319–1321 and 1363–1364; `_agent_user` confirmed at mc_door.py:1235–1240). No memory of that name → `DoorError('not-found', ...)` naming the waypoint.
- The stored payload is exactly `{'room_id': <int>}` (kind-aware validation confirmed at mc_door.py:1246–1256). Resolve the room via the existing `_room_by_id`; a deleted room → `not-found` with a message naming both the waypoint and the vanished room id (the legible-refusal law of the 25.8 memory design).
- Everything downstream is unchanged: combat refusal, origin capture, online/offline handling, arrival narration, MC records. The result gains `'waypoint': <stored name>` (the row's cased name) when the waypoint form was used; the `room`/`from_room` shape is untouched.
- `to_name` and `to_room_id` behavior is byte-identical to today.

No dispatch change: `ACTION_HANDLERS['move']` already routes (confirmed at mc_door.py:1687).

## 3. Door-side: `answer` gains machinery-only receipts

**Site:** `a_answer` in `mc_door.py` (confirmed at mc_door.py:390–411).

**Verified current shape:** resolves `to`; requires `text` a string of 1–`MAX_ANSWER_LEN` (2000, confirmed at mc_door.py:47); `not-admin` gate via `_is_admin`; online target gets one `_send_player_line(char.pk, f'sudo: {text}', 'sudo', ...)`; returns `{'delivered': delivered}`.

**Changed contract (the table is authoritative):**

| Param | Rule |
|---|---|
| `to` | unchanged — required, admin gate unchanged |
| `text` | now optional **when `receipts` is present and non-empty**; when present, the existing 1–2000 string rule holds; when `receipts` is absent, `text` is required exactly as today |
| `receipts` | optional; a list of 1–20 non-empty strings, each ≤ 200 chars; any violation → `bad-params` naming the rule broken |

At least one of `text` / `receipts` must be present, else `bad-params`.

**Delivery (online target):** first the `sudo: {text}` line exactly as today (skipped when no text), then **one line per receipt**, in list order, each via `_send_player_line(char.pk, f'sudo did: {receipt}', 'sudo', agent_name=agent_name)`. The `sudo did: ` prefix is door-composed — model text can never occupy line-start position (its prose lives inside the single `sudo: ` line, and the bot strips any leading `sudo:` the model writes — confirmed in `_deliver`, sudo_bot.py:1075–1083). Category `'sudo'` exists since v25.5; **no client change**. Offline: `delivered: false`, nothing sent, never an error — unchanged posture. Result shape unchanged.

Every receipt line rides `_send_player_line` → `audited_send`, so receipts appear in the MC record like all door output (confirmed at mc_door.py:183–194).

## 4. Bot-side: the typed receipts ledger

**Site:** `agents/sudo_bot.py`. Verified current shape: `_handle_sudo` runs the tool loop (`TOOL_LOOP_CAP` = 8, sudo_bot.py:78) calling `_execute_tool(call)` per proposed call (sudo_bot.py:1035–1045); `_execute_tool` is the single choke point — unknown-tool refusal, `door_request`, success → `content = json.dumps(result['data'])`, failure → error block (sudo_bot.py:1053–1073); `_deliver` posts the `answer` action (sudo_bot.py:1075–1092). `QUERY_KINDS`/`ACTION_KINDS` frozensets confirmed at sudo_bot.py:92–98, mirroring the door's handler tables (mc_door.py:1665–1695).

### 4.1 The ledger

A per-request `ReceiptLedger` created at the top of `_handle_sudo` and passed through the loop (one sudo request = one turn = one ledger; matches the standing orders' "current turn"). Four id-spaces: **room** (int), **item** (int, instance ids), **memory** (int), **stream** (str).

**Checked arguments** — before the door is called, each listed argument must be present in the matching space or the call is refused (the table is authoritative):

| Tool call | Argument | Space |
|---|---|---|
| `move` | `to_room_id` | room |
| `item` | `item_id` | item |
| `remove_item` | `item_id` | item |
| `edit_item` | `item_id` | item |
| `equip_item` | `item_id` | item |
| `unequip_item` | `item_id` | item |
| `memory` | `id` | memory |
| `forget` | `id` | memory |
| `event` | `stream_id` | stream |

A refusal never reaches the door: `_execute_tool` returns an error tool_result (`is_error: True`) with content `{'error': 'unreceipted-id', 'detail': "'<arg>' <value> is not from a lookup this turn — look it up first."}` and logs it. The model recovers inside the loop by looking the value up. `move` with `waypoint` or `to_name` has no checked argument — nothing to invent.

**Harvest** — on every **successful** result (never from error results), ids are harvested from these verified result fields (the table is authoritative; field names confirmed against the door's return statements at the cited lines):

| Tool | Harvested → space | Verified at |
|---|---|---|
| `where_is` | `room.id` → room | mc_door.py:232–237, `_room_dict` 142–151 |
| `character` | `room.id` → room | mc_door.py:243–258 |
| `rooms` | `rooms[].id` → room | mc_door.py:1478 |
| `move` | `room.id`, `from_room.id` → room | mc_door.py:834–835 |
| `memory` (kind waypoint) | `data.room_id` → room | mc_door.py:1451–1459 (waypoint `data` is the stored `{'room_id': ...}`) |
| `events` | `events[].room_id` → room; `events[].stream_id` → stream | `_event_row`, mc_door.py:1502–1509 |
| `event` | `room_id` → room; `stream_id` → stream | mc_door.py:1582–1591 |
| `inventory` | `items[].id` → item | mc_door.py:337–341, `_item_row` 319–323 |
| `item` | `id` → item | `_item_row` shape, mc_door.py:376 |
| `gift` | `item_id` → item | mc_door.py:447 |
| `create_artifact` | `item_id` → item | mc_door.py:677 (`definition_id` is not harvested — no tool argument takes definition ids) |
| `remove_item` / `edit_item` / `equip_item` / `unequip_item` | `item_id` echo → item | mc_door.py:903, 1115–1116, 1196, 1225 |
| `memories` | `memories[].id` → memory | mc_door.py:1409–1415 |
| `memory` | `id` → memory | mc_door.py:1451 |
| `remember` | `id` → memory | mc_door.py:1358 |
| `forget` | `forgotten.id` → memory | mc_door.py:1376, 1367 |

Harvest is a per-tool map (tool name → list of (path, space)), not a generic integer sweep — **the typing is the point**: v25.8's playtest failure passed a receipted integer (a memory's own id) into the wrong id-space, and an untyped ledger would have licensed it. Missing keys during harvest are skipped silently (a result field the door stops sending must not crash the bot).

### 4.2 The action log and receipt composition

Alongside the ledger, `_handle_sudo` keeps a per-request action log: every **successful** `ACTION_KINDS` call except `answer` appends one composed receipt string. Composition is bot machinery from the call's params and the door's result — never model text. Formats (the table is authoritative; `<path>` = `Zone: Area: Room` from a `_room_dict`, area omitted when null, `nowhere` for a null room; every referenced field verified above or at the cited line):

| Action | Receipt format |
|---|---|
| `gift` | `gave <slug> Mk <mk_tier> <rarity> to <to> (item <result.item_id>)`; **identical (slug, mk_tier, rarity, to) gifts in one turn aggregate to a single receipt** `gave <slug> Mk <mk_tier> <rarity> ×<N> to <to>` (ids omitted when aggregated — per-instance ids live in the MC record; the ×N count form is the shipped v22 aggregate style). Without this, a bundle replay (up to 50 gift calls, the 25.8 design) would flood or overflow the receipt bound |
| `create_artifact` | `created artifact '<spec.name>' for <to> (item <result.item_id>)` |
| `strip` | `stripped <name>` |
| `dress` | `dressed <name>` |
| `move` | `moved <name> from <from_room path> to <room path>`, plus ` (waypoint '<result.waypoint>')` when the waypoint form was used |
| `remove_item` | `removed item <item_id> from <name>`, plus ` (artifact definition deleted)` when `result.definition_removed` (mc_door.py:903) |
| `edit_item` | `edited item <item_id> on <name>: <result.changed joined by ', '>` (mc_door.py:1115–1116) |
| `equip_item` | `equipped item <item_id> on <name> (slot <result.slot>)` (mc_door.py:1196) |
| `unequip_item` | `unequipped item <item_id> on <name>` |
| `remember` | `remembered <kind> '<name>' (<result.result>, id <result.id>)` (mc_door.py:1358) |
| `forget` | `forgot <forgotten.kind> '<forgotten.name>' (id <forgotten.id>)` (mc_door.py:1367) |
| `report` | `report on <character> to <to>: delivered` / `: not delivered (offline)` per `result.delivered` (mc_door.py:1658) |

Receipts are truncated bot-side to the door's 200-char bound (ellipsis) and capped at 20, oldest kept, any overflow dropped with a log line. With gift aggregation in place, >20 distinct receipts in an 8-iteration turn is pathological, not a legitimate flow.

### 4.3 Delivery changes

`_deliver` gains the receipts: the answer call sends `{'to': ..., 'text': ..., 'receipts': [...]}` with `receipts` included only when non-empty. **Delivery now happens when there is text OR receipts**: a turn whose model went silent but whose actions succeeded delivers receipts-only (empty/absent `text`) — the admin always sees what was actually done; model prose is commentary, receipts are the record. The existing leading-`sudo:` strip and `MAX_ANSWER_LEN` truncation of `text` are unchanged. A turn with neither text nor receipts stays silent exactly as today.

### 4.4 Schema and prompt updates (ruling 4)

- `TOOLS`: the `move` schema (confirmed at sudo_bot.py:296–315) gains `waypoint` (string, "Waypoint memory name — the door resolves it from your own store; for taught places, always prefer this over to_room_id.") and its description states exactly-one-of-three.
- Every checked argument's description (per §4.1's first table) gains the explicit contract, e.g. `to_room_id`: "Must come from a tool result in this turn (rooms, where_is, or a waypoint memory); calls with unreceipted ids are refused."
- `SYSTEM_TEMPLATE` (confirmed at sudo_bot.py:634–729): the move paragraph's waypoint clause updates — waypoint moves pass the `waypoint` name to `move` directly, never resolve the room id themselves; the to_room_id standing order stays for rooms-search destinations. One added sentence: the game renders `sudo did:` receipt lines for every action automatically — never enumerate your own receipts; summarize outcomes plainly. All other standing orders stand verbatim (defense-in-depth).

No change to `botctl.py`. No change to `agents/mc_door_agent.py` — its action params are free-form JSON passthrough and `move`/`answer` are already in its `ACTION_KINDS` catalog (confirmed at mc_door_agent.py:17, 75–76).

## 5. What this release does NOT touch

- **No model changes, no migration, no seed change.** (State in the closeout: migrate is a no-op.)
- **No client (`app.js`/template) changes** — category `'sudo'` and plain text lines render today.
- **No kill-switch changes** — it covers the whole door already; the new param and destination form ride existing choke points.
- **No new door kinds** — `move` and `answer` change shape; the handler tables gain nothing.
- **No player-facing command changes** — GDD §9 untouched.

## 6. Tests (`django/src/apps/shyland/tests/test_v25_9_brief1.py`)

Door-side, following the 25.8 file's patterns (suite currently 865; it must grow by exactly this file's count):

1. `move` waypoint happy path — teach a waypoint (via `a_remember` or direct `AgentMemory.objects.create`), move an offline character by waypoint name; assert destination, `from_room`, and `waypoint` keys in the result.
2. Waypoint resolution is case-insensitive and returns the stored casing in the result.
3. Exactly-one-of-three: zero destinations, and each two-of-three pairing → `bad-params` with the new message.
4. Unknown waypoint name → `not-found` naming the waypoint.
5. Waypoint whose room was deleted → `not-found` naming waypoint and room id.
6. Cross-agent isolation: agent B's waypoint is invisible to agent A's `move` (→ `not-found`).
7. `to_name` and `to_room_id` paths byte-identical to current behavior (existing coverage may already pin this; if an existing test pins the old two-of XOR `bad-params` message, update the pinned string and report it as a test-hygiene deviation in the closeout).
8. `answer` receipts validation: non-list, empty list, >20 entries, non-string entry, empty string, >200 chars → `bad-params` each.
9. `answer` with `text` + `receipts` to an online admin: one `sudo: ` line then `sudo did: ` lines in order, all category `'sudo'`.
10. `answer` receipts-only (no `text`): delivers the receipt lines, no `sudo: ` line.
11. `answer` with neither `text` nor `receipts` → `bad-params`; `text`-only behavior unchanged (existing tests must pass untouched).
12. Receipts to a non-admin → `not-admin`; offline admin → `delivered: false`, nothing sent.

Bot-side ledger/composer logic is exercised by the deterministic driver check (§7) — `agents/` is outside the Django image and its logic is not importable in-container (the 25.8 precedent).

## 7. Verification (all must pass before commit of the closeout; the table/list is authoritative)

1. Full suite in-container, path form: `python manage.py test apps/shyland/tests` — green, grown from 865 by exactly the new file's tests.
2. `make deploy-dev` from the worktree after implementation and tests pass.
3. **Deterministic driver check against the live dev stack** (stub brain via `SUDO_BOT_BRAIN` — zero model calls; the 25.8 harness precedent), scripted scenarios asserted from the bot log and door results:
   a. A scripted `move` with an un-receipted `to_room_id` → refused bot-side (`unreceipted-id`), door never called.
   b. The same `to_room_id` after a `rooms` lookup in the same turn → executes.
   c. A scripted `forget` passing a room id from a `rooms` result (wrong space) → refused — the typed-ledger proof.
   d. Waypoint move end-to-end: teach → `move {name, waypoint}` → single hop, result carries `waypoint`.
   e. An action turn delivers `sudo did:` receipt lines into a live admin pane (text + receipts, and receipts-only with a silent stub turn).
4. Restart the dev bot via `agents/botctl.py` with the new code (dev target) after `make deploy-dev`.

## 8. Issues

Close **#302** with a closing comment naming this brief and the final implementation commit — **gated on §7 passing**. No other issue closes with this release.

## 9. Architecture doc (LAST, gated)

This step is gated on all implementation and verification steps above being complete and passing. `docs/shyland/Shyland_Architecture_v25.md`, updated in place, stamp → 25.9; **the hash moves** (architectural change — door vocabulary and bot machinery):

- §4.22 (the agent door): `move`'s three destination forms and agent-scoped waypoint resolution; `answer`'s receipts param, bounds, and the `sudo did:` rendering.
- §4.23 (the sudo bot): the typed receipts ledger (spaces, checked args, harvest), the action log and receipt composer, receipts-only delivery, the schema/prompt tightening.

## 10. Operator playtest checklist (dev stack, after §7)

1. Teach a fresh waypoint, then ask sudo to move a character there. Verify: one hop only (no wrong-room detour), the answer carries a `sudo did: moved ... (waypoint '...')` receipt line.
2. Repeat the same move request after walking the character elsewhere — verify sudo re-moves (fresh location decision) rather than declining, and the receipt shows the new origin.
3. Re-run the 25.8 failure shape: teach three waypoints in quick succession. Verify every "saved" claim is accompanied by a `remembered ...` receipt line — and that any turn without a receipt makes no save claim.
4. Ask for a gift and an item removal; verify each lands with a matching `sudo did:` line and the bot's prose agrees with the receipts.
5. Ask sudo something that needs the record (`events`) and a memory detail — verify normal operation (ledger transparent when the model behaves).
6. Skim the dev bot log for `unreceipted-id` refusals during the session — each one is the machinery catching an invention; note any for the closeout.

## 11. PENDING DEPLOY-TIME ACTIONS

None expected: code-only release, migrate no-op, no seed change. (The prod bot restart after the eventual prod deploy remains the operator's standing action, `--target prod` via botctl — not a brief step.)

## 12. Standing constraints

- Commit and push at every step boundary; branch only, never merge to main.
- Step 0 per the instructions: verify this brief verbatim at the branch tip, create and push the closeout-report stub before any work.
- Closeout report as `.txt` in `docs/shyland/`, final commit hash + operator playtest disposition included.
- No GDD source edits (the §10.11 marker is swept by a later design session or the closeout, never by implementation).
- Heredoc ban, quoting rules, and all repo standing rules apply.
