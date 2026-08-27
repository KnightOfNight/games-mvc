# Shyland V25.8 — Brief 1: Bot Memory and Record Search

**Release:** Version 25.8 (point release, milestone `Version 25.8`)
**Branch:** `version_25_8` (cut from main 5c7f21d; GDD design text landed at 8841518)
**Founding ticket:** #294 — with #290, #296, #299, #300 as milestone dependencies
**Design session:** 2026-08-27; all rulings recorded on the issues
**GDD:** §10.11 v25.8 paragraph + §10.5 event-driven line (committed 8841518, marked "(v25.8, pending implementation)" — marker removal is NOT this session's work)

The sudo bot's first week of real use asked for permanence and reach. This brief ships: the generic game-side taught-memory store with its four-verb door vocabulary (#294), the `rooms` directory query + `move` origin receipt (#290), the game-rendered `report` action (#296), time-windowed MC-record search (#300), and (bot, target)-scoped bot-side state files (#299).

---

## 0. Technical pre-flight — verified claims (#252 receipts)

Every structural claim below was verified against the code at branch commit 8841518 at brief-writing time. The implementation session's pre-flight re-diffs the load-bearing ones; a mismatch is a HARD STOP.

| Claim | Where verified |
|---|---|
| `QUERY_HANDLERS` / `ACTION_HANDLERS` dispatch tables | `mc_door.py:1195` / `mc_door.py:1206` |
| Dispatch resolves through those tables; kill switch checked before dispatch; every query/action emits its MC record via `mc.mc_emit` — **new table entries inherit kill-switch gating and record emission with zero extra work** (the 25.7 receipt, still true) | `mc_consumer.py:182, 208–209, 251` |
| `a_answer`: `_resolve_character(params, key='to')`, `MAX_ANSWER_LEN = 2000` (`mc_door.py:40`), `not-admin` gate via `_is_admin`, delivery via `_send_player_line(char.pk, f'sudo: {text}', 'sudo', agent_name=agent_name)`, offline ⇒ `ok: true, delivered: false` | `mc_door.py:357–378` |
| `a_move` returns `{'room': _room_dict(destination)}` and already computes `origin_room_id` in its body | `mc_door.py:746–798` |
| `_room_dict` shape: `{id, name, area (name or null), zone (name)}` | `mc_door.py:109–120` |
| `compose_item_line(item, count=1)` — the shared item-line composition | `item_utils.py:316` |
| Equipment paper-doll composition (bare `equip`'s shared rendering) | `consumers.py:~1170` (slot-order comment at `:56`), `cmd_equip` at `:1509` |
| `MCEvent`: `stream_id` (unique), `ts` (indexed), `kind`, `actor_id`, `actor_name`, `room_id`, `audience`, `data`; composite indexes `(kind, ts)`, `(actor_id, ts)`, `(room_id, ts)`; append-only, FK-free | `models.py:1275–1296` |
| Case-insensitive unique-constraint precedent: `UniqueConstraint(Lower('name'), …)` (Character) | `models.py:323–324` |
| `SHYLAND_VERSION = "25.7"`; pin test asserts `'25.7'` | `version.py:8`; `tests/test_b2_amendment1.py:118` |
| Latest migration is `0053_character_outfit_snapshot.py` — this brief's migration will be 0054 | `migrations/` listing |
| Bot tools: `TOOLS` list of `{name, description, input_schema}` dicts | `agents/sudo_bot.py:131` |
| Bot state constants: `PIDFILE = AGENTS_DIR / '.sudo_bot.pid'`, `CONVO_FILE = AGENTS_DIR / '.sudo_bot_conversations.json'`; used at `:1034` (status read), `:1106` (ConversationStore), `:1109/:1116` (write/unlink) | `agents/sudo_bot.py:61–62` |
| `botctl.py`: `BotPaths` keys log by bot name only; `cmd_stop(paths)` / `cmd_status(paths)` never receive the target | `agents/botctl.py:60–67, 218–230` |
| `agents/.gitignore` already wildcards `*.log` and `*.pid` — **suffixed pid/log forms are already ignored**; only the literal `.sudo_bot_conversations.json` needs widening (corrects #299's "may need widening" sketch, which guessed at pid/log too) | `agents/.gitignore` |
| Existing door test module: `tests/test_mc_agent_door.py` (72 tests) | test directory listing |
| Architecture doc: `Shyland_Architecture_v25.md`, hash line `bf9c6a4 (v25.7 …)` | doc header |

## 1. Standing requirements (never omit)

1. **Version constant — opening act.** Bump `SHYLAND_VERSION` to `"25.8-DEV"` (`version.py:8`) in its own commit, moving the pin test assertion (`tests/test_b2_amendment1.py:118`) in the same commit. Then run the version-start `make deploy-dev` from the worktree.
2. **In-session dev deploy:** exactly `make deploy-dev` from the worktree once implementation and verification pass. Production is never deployed from an implementation session.
3. **Operator playtest checklist** (§8) targets the dev stack, ready after the final `make deploy-dev`.
4. Push cadence: commit and push at every step boundary; branch only, never merge.
5. Step 0 (verify-and-signal): confirm this brief verbatim at the branch tip, create the closeout-report stub `.txt`, commit, push immediately.

## 2. The model — `AgentMemory` (#294)

Add to `django/src/apps/shyland/models.py`:

```python
class AgentMemory(models.Model):
    """Generic per-bot durable storage (#294, v25.8). One row per taught
    fact. Kinds own their payload shapes; the door validates per kind at
    teach time. Shared namespace per (agent, kind) across all admins."""
    KIND_WAYPOINT = 'waypoint'
    KIND_BUNDLE = 'bundle'
    KIND_CHOICES = [(KIND_WAYPOINT, 'Waypoint'), (KIND_BUNDLE, 'Bundle')]

    agent = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='agent_memories')
    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    name = models.CharField(max_length=60)
    data = models.JSONField(default=dict, blank=True)
    taught_by = models.ForeignKey(User, null=True, blank=True,
                                  on_delete=models.SET_NULL,
                                  related_name='taught_agent_memories')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                'agent', 'kind', Lower('name'),
                name='agentmemory_unique_agent_kind_name_ci'),
        ]
        indexes = [models.Index(fields=['agent', 'created_at'])]
```

Notes, binding: direct `User` FK, the house style (`models.py:1` imports it; the Character FK at `:246` is the precedent) — agent accounts are Users, never a Character FK; `taught_by` is `SET_NULL` audit, not ownership; the case-insensitive constraint follows the Character-name precedent (`models.py:323`). Module-level cap constants live beside the door handlers (§3.1), not on the model.

**Migration step:** `make makemigrations APP=shyland && make migrate` → expect `0054_agentmemory.py` (name may vary; commit whatever Django generates — never hand-edit).

## 3. Door vocabulary (`mc_door.py`)

All new handlers join the two dispatch tables; kill-switch gating and MC record emission are inherited by construction (verified above). Every list result is newest-first where time-ordered and capped at 50. Error kinds reuse the door's existing `DoorError` vocabulary (`bad-params`, `not-found`, `not-admin`) plus new legible kinds noted below.

### 3.1 Memory (#294) — queries `memories`, `memory`; actions `remember`, `forget`

Cap constants (module-level, beside `MAX_ANSWER_LEN`):

```python
MEMORY_MAX_PAYLOAD_BYTES = 4096      # serialized JSON, checked at teach
MEMORY_MAX_ROWS_PER_AGENT = 262144   # = 1 GiB / 4 KiB (operator-ruled)
MEMORY_MAX_NAME_LEN = 60
MEMORY_MAX_BUNDLE_LINES = 50
MEMORY_LIST_CAP = 50
```

- **`memories`** (query). Params: optional `kind`, optional `name` (case-insensitive substring), optional `since` / `until` (ISO-8601; both optional — an unwindowed call lists newest-first). Returns `{'memories': [...], 'count': N}` — rows newest-first by `created_at`, capped `MEMORY_LIST_CAP`, each `{id, kind, name, summary}` where `summary` is rendered live: waypoint → the current `Zone: Area: Room` path via one joined query (`'(room no longer exists)'` when dangling); bundle → `'<N> lines'`.
- **`memory`** (query). Params: `id` (int, required). Full row: `{id, kind, name, data, taught_by, created_at, updated_at}` — bundle `data` rendered with labeled fields (the stored form is positional; the rendered detail is legible). `not-found` on a bad id.
- **`remember`** (action). Params: `kind` (must be a declared kind), `name` (≤ 60 chars after strip), `data`. **Kind-aware validation at teach time:** waypoint `data` must be exactly `{'room_id': <int>}` and the room must exist; bundle `data` must be `{'lines': [[slug, mk_tier, rarity, quantity], ...]}` with 1–50 lines, every slug resolving to a real `ItemDefinition`, every mk_tier/rarity/quantity valid under the same checks `a_gift` applies (artifact rarity refused — bundles replay `gift`, and `gift` refuses artifacts; verified `mc_door.py:405–408`). Serialized `data` ≤ 4096 bytes; agent row count < 262,144. **Upsert by (agent, kind, name) case-insensitive:** result `{'id': N, 'result': 'created' | 'replaced'}`. Cap violations are distinct legible errors (`memory-full`, `payload-too-large`, `too-many-lines` — never silent truncation). Attribution: `remember` takes an optional `taught_by` string param — the teaching admin's character name, which the bot passes from its conversation context; the door resolves it to the character's User (unresolvable or absent ⇒ null — audit, not authorization).
- **`forget`** (action). Params: `id` (int, required) — **by PK only, never by name** (read-before-delete; the door's mutation discipline). Result `{'forgotten': {id, kind, name}}`; `not-found` on a bad id.

**Waypoints store the room PK and nothing else** — no path snapshot, nothing duplicative that can go stale (operator-ruled). **Bundle replay is not a door feature:** the bot replays a bundle as N ordinary `gift` calls — fresh generation each time, operator-ruled — the door ships no `replay` verb.

### 3.2 Rooms (#290) — query `rooms`; `move` result gains origin

- **`rooms`** (query). Params: `name` (required, case-insensitive substring against `Room.name`), optional `zone` (case-insensitive substring against `Zone.name`). Returns `{'rooms': [_room_dict rows...], 'count': N}` capped 50, ordered by zone name then room name. Duplicate names across zones are simply multiple rows.
- **`a_move`**: the result becomes `{'room': _room_dict(destination), 'from_room': _room_dict(origin) or None}`. The handler already holds `origin_room_id`; fetch the origin Room (or capture `char.current_room` before the move — implementer's choice) and pass it through `_room_dict`. No other behavior changes.

### 3.3 Record search (#300) — queries `events`, `event`

- **`events`** (query). Params, all optional except as noted: `kind` (exact), `actor` (int id, or string name matched case-insensitively against `actor_name`), `room_id` (int), `text` (case-insensitive substring against the JSON-serialized `data` payload), `since` / `until` (ISO-8601). Defaults: `until` = now, `since` = `until` − 24 hours. **When `text` is present, the (since, until) span must be ≤ 7 days** — `bad-params` with a legible message otherwise ("text search runs in windows of up to 7 days — narrow the window and walk backwards"). Query: filter `ts` range + indexed fields first (the composite indexes are the point), newest-first, then apply `text` inside that bounded scan, cap 50. Returns `{'events': [...], 'count': N}` — rows `{stream_id, ts, kind, actor_name, room_id, gist}` where `gist` is the serialized `data` truncated to 120 chars.
- **`event`** (query). Params: `stream_id` (string, required). The full record: `{stream_id, ts, kind, actor_id, actor_name, room_id, audience, data}`. `not-found` on a miss.

### 3.4 Rendered report (#296) — action `report`

Params: `to` (the requesting admin — same resolution and **identical admin gate** as `a_answer`: `_resolve_character(params, key='to')` + `_is_admin` ⇒ `not-admin`), `character` (the target whose state is reported), `kind` (must be `'inventory'` — the only v1 kind; unknown kinds `bad-params`). Offline recipient ⇒ `ok: true, delivered: false`, never an error (the `a_answer` posture).

Delivery, in order, **privately to the recipient's pane only** (via `_send_player_line`, never a room broadcast):

1. **Leader, door-composed:** `sudo: <Character Name> (<N> items total)` in the `sudo` category — N counted from live data (total owned instances). The model never writes this line.
2. **Equipped section** then **carried section**, rendered through the *same shared composition the player commands use* — the bare-`equip` paper-doll composition (every slot, slot order, `consumers.py:~1170`) and the inventory listing composition over `compose_item_line` (`item_utils.py:316`) — each line delivered in the same category/color the player-facing reports use. If those compositions live as consumer methods, extract the shared parts to `item_utils` the way `equip_candidates` was extracted in 25.7 — **byte-identical player-facing output, verified by the existing tests** (the 25.7 `cmd_equip` extraction forced zero test edits; that is the bar).

Result: `{'delivered': bool, 'item_count': N}`. **`a_answer` is untouched** — its cap and voice rules stand.

## 4. Bot side (`agents/`)

### 4.1 Eight new tools (`sudo_bot.py` `TOOLS`)

`memories`, `memory`, `remember`, `forget`, `rooms`, `events`, `event`, `report` — same `{name, description, input_schema}` dict shape as the existing entries, descriptions written for the model (e.g. `remember`: "Store a durable named fact. Kinds: waypoint {room_id}, bundle {lines: [[slug, mk_tier, rarity, quantity], ...]}. Overwrites an existing name and says so."). The system prompt gains a short paragraph: taught facts go in durable memory (not conversation), `forget` requires looking the memory up first (the id), "what happened" questions use `events`/`event` with time windows walking backwards from now, and inventory questions for admins should prefer the `report` action over hand-written rosters.

### 4.2 Target-scoped state (#299)

- `sudo_bot.py`: `PIDFILE` and `CONVO_FILE` derive from the target — `.sudo_bot.<target>.pid`, `.sudo_bot_conversations.<target>.json`. The `run` subcommand gains a required `--target {dev,prod}` (or positional matching botctl's convention — implementer's choice, botctl is the only caller); `status`/`stop` paths resolve the same way.
- `botctl.py`: `BotPaths` takes `(name, target)` and derives `self.log = AGENTS_DIR / f'{name}_bot.{target}.log'` plus the pid/convo paths; `cmd_stop(args.target, paths)` and `cmd_status(args.target, paths)` receive and use the target (`botctl.py:222–228` currently drop it). `dev stop` must be incapable of touching the prod bot's pidfile by construction.
- `agents/.gitignore`: widen the literal `.sudo_bot_conversations.json` to `.sudo_bot_conversations*.json`. (`*.pid` / `*.log` already cover the suffixed forms — verified.)
- Migration of existing state files is NOT required — the operator restarts bots after deploy (standing action); stale unsuffixed files may be left in place, ignored.

## 5. Tests

New tests join `tests/test_mc_agent_door.py` (or a sibling module if size warrants; path-form discovery covers either). Required coverage, minimum:

- `remember`/`memory`/`memories`/`forget` round-trip per kind; case-insensitive upsert (created → replaced); the three cap refusals (rows, payload bytes, bundle lines); waypoint teach with nonexistent room refused; bundle teach with bad slug/rarity/artifact refused; forget by id + not-found; `memories` windowing and newest-first order; dangling-room summary rendering.
- `rooms`: substring match, zone filter, cap, `_room_dict` shape.
- `events`/`event`: window defaults (24h), text-without-window-cap refusal (> 7-day span + `text` ⇒ `bad-params`), filter combinations, newest-first, cap, gist truncation, `event` by `stream_id` + not-found.
- `report`: admin gate (`not-admin`), offline recipient `delivered: false`, leader-line composition (name + count from live data), section order (equipped then carried), unknown kind refused — and the player-facing `inv`/`equip` outputs byte-identical before/after any extraction (existing tests are the guard; zero edits expected there).
- Kill-switch coverage: one representative new query and one new action refused when killed (pattern from `test_mc_kill_switch.py`).
- Pin test moved to `'25.8-DEV'` in the opening-act commit, then to nothing further (closeout stamps).

**In-container invocation (the only working form):** `python manage.py test apps/shyland/tests` via `docker exec` in the django container.

## 6. Verification (all must pass before issue-closing)

1. Full suite green in-container (path form above). Suite count grows from 840; record the new total in the closeout.
2. Migration `0054` applied on dev (`make migrate` output or `showmigrations`).
3. Driver check via `agents/mc_door_agent.py` (extend it with the new kinds as needed — it is the deterministic driver, no model in the loop): teach a waypoint, list, detail, move a test character to it (verify `from_room` in the receipt), teach a 2-line bundle, forget both by id; `rooms` search; `events` window query returning the just-emitted records (the actions' own MC records prove emission end-to-end); `report` delivered to an online admin session showing leader + paper-doll + inventory lines in the pane.
4. Two-target coexistence (#299), **without ever starting a prod-pointed bot — implementation sessions never touch production**: with the dev bot running, `botctl.py prod status` reports not-running while `dev status` reports running (target-scoped resolution proven); `botctl.py prod stop` is a no-op that leaves the dev bot untouched; the dev bot's state files carry the `dev` suffix. File independence and target-scoped stop/status are the claims under test; real prod coexistence is the operator's post-release standing usage.
5. Where a table and prose disagree in this brief, the table is authoritative.

## 7. Deploy + issue closing

`make deploy-dev` from the worktree after verification passes. Close #294, #290, #296, #299, #300 (gated on verification passing), each with a closing comment naming this brief and the commit.

## 8. Operator playtest checklist (dev stack)

1. Teach sudo a waypoint conversationally ("remember this spot as battle" while pointing at a character's location), wait out or force conversation expiry (default 600s, or restart the bot), then `sudo send <char> into battle` — the waypoint survives where conversation memory would have blanked.
2. Teach a small bundle ("remember these two items as the starter kit" style), replay it on a character — items arrive freshly generated (gift via the door; NOT the Django admin form).
3. `sudo move <char> to <room name>` for an authored room name — works via `rooms` resolution; ask sudo to send them back — works via the `move` receipt's origin.
4. Ask sudo "what did I give <char> in the last few days?" — answered from `events` search, not conversation memory.
5. `sudo show me <char>'s inventory` — the pane shows the sudo-voiced leader line plus the same equipment/inventory rendering the `equip`/`inv` commands produce, colors and flag blocks included.
6. From one checkout: with the dev bot running, `botctl.py dev status` / `prod status` report independently and `prod stop` cannot touch the dev bot (optionally, at the operator's own discretion and on their own machine, with the real prod bot alongside — the operator's standing usage, not a session action).

## 9. Architecture doc — last, gated

This step is gated on all implementation and verification steps above being complete and passing. Update `Shyland_Architecture_v25.md` **in place**: stamp to 25.8, **hash moves** (this is an architectural release) to the release's final implementation commit; update the MC/agent-door sections with the new model (`AgentMemory`), the eight vocabulary additions, the report delivery path, the `events` search, and the (bot, target)-scoped agents runtime. No GDD source edits of any kind (the v25.8 markers are the next design/closeout session's sweep).

## 10. Closeout report

`docs/shyland/` `.txt`, completed in place from the Step 0 stub: final commit hash, suite count, deviations (including any test-hygiene conversions), the **operator playtest disposition** (verbatim-style, #170), and:

**PENDING DEPLOY-TIME ACTIONS: none expected.** Migration 0054 rides `make deploy-prod` automatically; no seed change, no production-side data action. (Prod bot restart after deploy remains the operator's standing action.) If implementation discovers otherwise, the block gains the named-executor entries per the executor checkpoint (#248).
