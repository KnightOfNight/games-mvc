# Shyland V25.3 Brief 1 — MC Egress

**Release:** Version 25.3 (milestone `Version 25.3`) · **Founding ticket:** #267 · **Branch:** `version_25_3`
**Written and committed by the V25.3 design session, 2026-08-20.** Rulings of record: #267 comments dated 2026-08-20 (R1–R6), plus the binding inputs already on the issue (soft RAM ceiling 2026-08-16; volumeless Redis 2026-08-18). GDD text: §10.11 egress passage, committed caa5925, marked `(v25.3, pending implementation)`.

**What ships:** the MC egress — a read-only WebSocket endpoint through which remote agents attach to the MC event stream: session auth, `agents.shyland` group gate, hello/attach protocol, hot-window replay with explicit gap semantics, then live tailing. Transport only — no actor, no actuation, no kill switch (that's 25.4/#266).

---

## 1. Technical claims — verified at writing time (#252)

Every claim below was verified against the branch tip (caa5925) during the design session; nothing here is from recall.

1. **The sink** (`django/src/apps/shyland/mc.py`, 110 lines): `MC_STREAM_KEY = 'mc:events'` (:21); lazy module-level async client `_get_client()` (:39–45) built from `settings.REDIS_HOST` port 6379 db 0, rebound if the running event loop changes; `mc_emit(kind, *, actor_id=None, actor_name='', room_id=None, audience=(), data=None)` (:56) XADDs field dict `{kind, actor_id, actor_name, room_id, audience(json), data(json)}` with `maxlen=settings.MC_STREAM_MAXLEN, approximate=True` (:74–77), fire-and-forget try/except with throttled `_warn`.
2. **Settings** (`game_mvc/settings/base.py`): `REDIS_HOST = env('REDIS_HOST', default='redis')` (:77); `MC_STREAM_MAXLEN = env.int('MC_STREAM_MAXLEN', default=250000)` (:81). No `.env`* file overrides `MC_STREAM_MAXLEN` (verified in the 25.2 closeout §7.3; re-verify in §7).
3. **The persister** (`management/commands/run_mc_persister.py`): sync loop, consumer group `persister`, acks after commit, XAUTOCLAIM recovery, idempotent on unique `stream_id`. **Untouched by this brief** — consumer groups remain its mechanism alone (R5).
4. **`MCEvent`** (`models.py:1240–1257`): `stream_id` unique CharField(32), `ts` indexed, `kind` CharField(16), `actor_id`/`room_id` BigIntegerField null, `actor_name` CharField(64), `audience`/`data` JSONField; indexes on (kind, ts), (actor_id, ts), (room_id, ts). **Untouched by this brief.**
5. **Auth stack** (`game_mvc/asgi.py`): websocket protocol runs `AuthMiddlewareStack(URLRouter(websocket_urlpatterns))` — `scope['user']` is the authenticated session user for every consumer.
6. **Routing** (`game_mvc/routing.py`): exactly two entries today — `ws/shyship/<uuid:game_id>/` and `ws/shyland/` (`SkylandConsumer`). This brief adds one line (operator-approved shared-surface touch, 2026-08-20, recorded on #267).
7. **nginx** (`nginx/conf/default.conf.template:14–22`): one `location /ws/` block proxies with Upgrade headers — `ws/shyland/mc/` is covered by prefix; **no nginx change**.
8. **The admin-gate precedent** (`consumers.py:3279–3283`): `check_shyland_admin` — `@database_sync_to_async`, live `user.groups.filter(name='admins.shyland').exists()`, no session caching. The agent gate copies this shape against `agents.shyland`.
9. **The group-creation precedent** (`migrations/0034_create_shyland_admin_group.py`): data migration, `Group.objects.get_or_create(name='admins.shyland')` forward, filtered delete backward. Newest migration is `0050_mcevent.py` → this brief's is **0051**.
10. **Test surface**: `tests/test_mc_sink.py` patches `mc._get_client` at 5 sites (:105, :124, :134, :141, :192) and drives the real consumer via `channels.testing.WebsocketCommunicator` with `communicator.scope['user'] = character.user` (:201–205); `test_map_payload.py:285` and `test_room_visits.py` use the same communicator pattern. **`_get_client` is NOT renamed** (see §2, rule 8) — zero existing patch sites move (the V25.2 D1 lesson, avoided by construction).
11. **Dependencies** (`django/requirements.txt`): `channels>=4.0`, `channels-redis>=4.2`, `redis>=5.0`. No `websockets` client library — none needed; tests use WebsocketCommunicator, playtest uses the browser.
12. **Volume numbers** (25.1/25.2 closeouts): ~0.6 records/sec non-combat baseline, ~1.03/sec in combat — the 250k window is days deep; replay batching at 500 matches the persister's `BATCH_COUNT`.

## 2. Design rules — never deviate

1. **Read-only endpoint (R4).** No inbound frame may cause any game action, ORM write, or stream write. Inbound vocabulary is exactly: `attach`, `ping`. Anything else (including a second `attach`) draws `{"type": "error", "error": "read-only"}` and is otherwise ignored; the connection stays open.
2. **Access = `agents.shyland` membership, checked live at connect (R1/R2).** Unauthenticated → reject the handshake (plain `close()` before accept, the player-consumer pattern — a custom close code cannot be delivered pre-accept in Channels). Authenticated non-member → accept, then close with code **4403** (accept-then-close so the code reaches the client). Members get the full stream — no scoped subscriptions, no category filters.
3. **The gate is the group, not a character.** Agent service accounts have no `Character` and must never be routed to the creator — the MC consumer never queries `Character` for its own connection.
4. **Gaps are announced, never silent (R5).** Resume from an id older than the window's oldest entry (trim and Redis restart are the same symptom) sends one `gap` frame, then replays from oldest. Deep replay is never served on this socket.
5. **Agents own their cursors (R5).** No consumer groups, no server-side per-agent state. Server reads are stateless `XRANGE`/`XREAD`.
6. **Backpressure never reaches the game.** The sink (`mc_emit`) is untouched; egress reads never block or slow emission. A slow agent is Daphne/nginx's problem.
7. **Capture boundary:** MC egress connections are **not** captured as stream events (they are not in-world events; `connect`/`disconnect` kinds are player presence). Attach/detach get `shyland.mc` logger lines carrying the agent username — fleet observability belongs to #268's arc.
8. **`mc._get_client` is reused, not renamed.** `mc_consumer.py` calls it as a module attribute (`mc._get_client()`), so existing and new `mock.patch.object(mc, '_get_client', ...)` test patches govern egress reads too. The private-name reuse is deliberate and this rule is its record.
9. **No model changes.** `MCEvent`, `mc_emit`, the persister, and every game path are untouched. Migration 0051 is a data migration only.
10. **Provisioning is operational, not seeded.** No agent service account is created by code, seed, or migration — the operator creates accounts at need (playtest checklist shows the motion). The group itself is migration-created (idempotent `get_or_create`, the 0034 pattern).

## 3. The wire protocol (the contract)

Endpoint: **`wss://<host>/ws/shyland/mc/`**. All frames JSON objects with a `type` field.

**Server → client:**

| Frame | Shape | When |
|---|---|---|
| `hello` | `{"type": "hello", "protocol": 1}` | Immediately on accept. Protocol version is per-connection, from the module constant `MC_PROTOCOL = 1`. |
| `event` | `{"type": "event", "id": "<stream-id>", "kind": str, "actor_id": int\|null, "actor_name": str, "room_id": int\|null, "audience": [int,...], "data": {...}}` | One per stream entry, replay and live alike, in stream order. Fields decoded from the stream record: empty-string `actor_id`/`room_id` → `null`, else int; `audience`/`data` json-decoded. A field that fails to parse is passed through as its raw string — a malformed entry never kills the connection. |
| `gap` | `{"type": "gap", "requested": "<id>", "oldest": "<id>"\|null}` | Once, before replay, when the attach cursor predates the window (`oldest` null = window empty). |
| `pong` | `{"type": "pong"}` (plus `"nonce"` echoed verbatim if the ping carried one) | Reply to `ping`. |
| `error` | `{"type": "error", "error": "read-only"}` | Any inbound frame outside the vocabulary, or an `attach` after the first. |

**Client → server:**

| Frame | Shape | Meaning |
|---|---|---|
| `attach` | `{"type": "attach"}` | Go live from now (`$`). |
| `attach` | `{"type": "attach", "after": "<stream-id>"}` | Replay everything after `<stream-id>` from the hot window, then go live. Exclusive of the id itself. |
| `ping` | `{"type": "ping"}` (optional `"nonce"`) | Liveness; answered with `pong`. |

**Connection lifecycle:** auth + live group check (rejection semantics per §2 rule 2) → accept → `hello` → server waits for the client's `attach` (no timeout beyond nginx's; nothing streams until attach) → (`gap` if applicable) → replay in batches of 500 via `XRANGE` (exclusive start `(<id>`) → live tail via `XREAD BLOCK 5000` from the last-sent id, as an asyncio task cancelled on disconnect. Stream-id comparison for gap detection parses both dash-separated parts numerically — never string comparison.

## 4. Version start — the opening act (standing requirement)

This is the **first implementation brief of Version 25.3**:

1. In its own commit: `SHYLAND_VERSION = "25.3-DEV"` (`django/src/apps/shyland/version.py:8`, currently `"25.2"`), with the pin test moved in the same commit — the pin is `tests/test_b2_amendment1.py:118`, `self.assertEqual(SHYLAND_VERSION, '25.2')` → `'25.3-DEV'` (verified at writing time; there is no separate pin-test file).
2. Then the version-start `make deploy-dev` from the worktree.

## 5. Implementation

All paths relative to `django/src/`.

**5.1 Migration 0051 — the `agents.shyland` group.** `apps/shyland/migrations/0051_create_shyland_agents_group.py`, exactly the 0034 shape: forward `Group.objects.get_or_create(name='agents.shyland')`, backward `Group.objects.filter(name='agents.shyland').delete()`, `dependencies = [('shyland', '0050_mcevent')]`. Data migrations are **authored**, not generated — 0034 is the in-repo precedent, and the never-hand-edit rule applies to generated schema migrations; author this file directly on 0034's structure.

**5.2 The MC consumer — new module `apps/shyland/mc_consumer.py`.** Class `MCEgressConsumer(AsyncJsonWebsocketConsumer)`. Module constants: `MC_PROTOCOL = 1`, `REPLAY_BATCH = 500`, `LIVE_BLOCK_MS = 5000`. Imports `apps.shyland.mc as mc` and uses `mc.MC_STREAM_KEY` and `mc._get_client()` (rule 8). Implements §3 exactly:

- `connect()`: `scope['user']` unauthenticated → `close()` without accept (handshake rejection, the player-consumer pattern at `consumers.py:499–501`). Live group check (a `@database_sync_to_async` method on the `check_shyland_admin` shape, name `check_shyland_agent`, group `agents.shyland`) fails → `accept()` then `close(code=4403)` — accept-then-close so the code reaches the client (the player consumer's no-character path uses the same accept-signal-close shape, `consumers.py:504–511`). Pass → accept, send `hello`, log attach (`shyland.mc` logger, agent username).
- `receive_json()`: dispatch on `type` per §3. First `attach` starts the stream task; `ping` → `pong`; everything else → the `error` frame.
- Replay: oldest = first entry of `XRANGE mc:events - + COUNT 1`; gap decision by numeric id comparison; batches of `REPLAY_BATCH` with exclusive start; each entry decoded and sent as an `event` frame.
- Live: `asyncio.create_task` looping `XREAD BLOCK LIVE_BLOCK_MS` from the last-sent id; task stored on the consumer and cancelled in `disconnect()` (log detach).
- Decoding: one module-level `entry_to_frame(stream_id, fields)` helper (bytes→str, int-or-null, json-or-raw per §3) — unit-testable without a socket.

**5.3 Routing — the approved shared-surface line.** In `game_mvc/routing.py`: `path('ws/shyland/mc/', MCEgressConsumer.as_asgi()),` after the existing shyland entry, with the import. Nothing else in the file changes.

**5.4 No other file changes.** `mc.py`, `consumers.py`, the persister, models, settings, nginx, compose: untouched.

## 6. Tests

New file `apps/shyland/tests/test_mc_egress.py`, existing-suite patterns (WebsocketCommunicator with `scope['user']`; `mock.patch.object(mc, '_get_client', ...)` fakes on the `test_mc_sink.py` shape, extended with the XRANGE/XREAD surface):

1. **Gate:** unauthenticated (AnonymousUser scope) → handshake rejected (`connected` is False); authenticated non-member → accepted then closed with 4403; `agents.shyland` member (User with no Character) accepted, receives `hello` with `protocol` 1.
2. **Read-only:** unknown frame → `error` read-only, connection stays open (a subsequent `ping` still answers); second `attach` → `error`. (The no-game-writes property is structural — §7.2's greps enforce it; no test fakes it.)
3. **Attach live:** bare attach → no replay, then a faked live entry arrives as a correct `event` frame (field decoding: null actor, audience list, data dict).
4. **Resume:** attach after id X with fake window containing X+ entries → exactly the after-X entries replay in order, then live picks up from the last.
5. **Gap:** attach after an id older than the fake window's oldest → one `gap` frame (requested + oldest), then replay from oldest. Empty-window variant: `gap` with `oldest: null`, then live.
6. **Decode robustness:** `entry_to_frame` unit tests — malformed json `data` passes through raw; empty actor_id → null; nonce echo on ping.
7. **Migration:** `agents.shyland` group exists after migrate (query in any TestCase — the test DB runs all migrations).

Suite arithmetic states the invariant: previous total (731) + this file's count = new total, all green.

## 7. Verification (all must pass before the closeout commits)

1. Full in-container suite, the only working form: `python manage.py test apps/shyland/tests` via `docker exec` — green, arithmetic per §6.
2. Grep discipline (single-quoted patterns): `grep -n 'mc_emit' apps/shyland/mc_consumer.py` → **zero hits** (egress never emits); `grep -rn 'agents.shyland' apps/shyland/` → exactly migration 0051, the consumer's gate check, and tests; `grep -n 'Character' apps/shyland/mc_consumer.py` → zero hits (rule 3).
3. `game_mvc/routing.py` diff is exactly one import + one path line.
4. In-container `settings.MC_STREAM_MAXLEN == 250000` still holds and no `.env`* override appeared (claim 2 re-check).
5. Live dev-stack check (after §8's deploy, the 25.1/25.2 throwaway pattern): an in-container script creates a throwaway agent user in `agents.shyland`, drives `MCEgressConsumer` via `WebsocketCommunicator` **against the container's real Redis** (no `_get_client` fake — this is the genuine stream, fed by the live stack's emissions), and asserts: hello → attach → live `event` frames arrive while a scripted actor generates activity; resume-by-id returns the intervening records in order; a non-member draws 4403. Clean up the throwaway user; MCEvent rows are append-only and remain. (The nginx/WSS path is proven by the operator playtest, §10 — the two checks together cover the full route.)

## 8. Deploy (standing requirement)

`make deploy-dev` from the worktree once implementation and §7 pass (in addition to the version-start deploy of §4). No data actions. **No PENDING DEPLOY-TIME ACTIONS** — no seed, no migration beyond 0051 (which `make deploy-prod`'s migrate step applies at the closeout tail as an ordinary migration; executor already named by the deploy target itself), no prod-side steps.

## 9. Architecture doc — last, gated

This step is gated on all implementation and verification steps above being complete and passing. `docs/shyland/Shyland_Architecture_v25.md`, updated in place:

- Stamp → **25.3**; header hash **moves** to the final implementation commit (architectural change — new consumer, new route, new group).
- New **§4.20 The MC egress (`mc_consumer.py`)** after §4.19: the endpoint, the gate, the protocol table (§3's content in arch-doc voice), the no-consumer-groups/agents-own-cursors design, the capture boundary (rule 7), and the reused `_get_client` note.
- The header's change-summary blockquote row in the established per-release voice.

## 10. Operator playtest checklist (dev stack)

After §8's deploy. Needs two browser contexts (one normal, one private/incognito).

1. Create the agent account (operator chooses the password; never echo it): `make shell` → `from django.contrib.auth.models import User, Group; u = User.objects.create_user('agent-smoke', password='<choose>'); u.groups.add(Group.objects.get(name='agents.shyland'))`.
2. In the **incognito** window: log in at the dev site as `agent-smoke`. In the devtools console: `ws = new WebSocket('wss://<dev-host>:40443/ws/shyland/mc/'); ws.onmessage = e => console.log(e.data); ws.onclose = e => console.log('closed', e.code);` — expect the `hello` frame with `protocol: 1`.
3. Send `ws.send(JSON.stringify({type: 'attach'}))` — then, in the **normal** window, log in as your player and move/say something. Expect `event` frames streaming in the console: your `cmd`, `out`, presence records, with ids, kinds, and decoded `data`.
4. Note any event's `id`; close and reopen the socket (rerun step 2's console line); `ws.send(JSON.stringify({type: 'attach', after: '<that id>'}))` — expect the records since that id to replay, then live flow to continue.
5. `ws.send(JSON.stringify({type: 'attach', after: '0-1'}))` on a fresh connection — expect a `gap` frame naming the window's oldest id, then replay.
6. Send `ws.send(JSON.stringify({type: 'say', text: 'hi'}))` — expect `{"type":"error","error":"read-only"}` and nothing in the game.
7. In the **normal** window (your player account, not in `agents.shyland`), console-open the same WebSocket — expect close with code **4403**.
8. Optional cleanup: delete `agent-smoke` in `make shell` (operator's call; the account is dev-stack data).

## 11. Closeout requirements

Standard form: commit list with the final implementation hash marked; deviations (none silent); §7 outcomes; migration statement (0051, data-only); **PENDING DEPLOY-TIME ACTIONS: none** (state it); **#267 closed, gated on §7 passing**, with a comment naming this brief and the final hash; the operator playtest disposition (#170) verbatim-style. End with the `implementation-session-end` ritual.
