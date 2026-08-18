# Shyland V25.1 — Brief 1: The MC Sink

**Release:** Version 25.1 (milestone) · **Branch:** `version_25_1` · **Written and committed by the V25.1 design session, 2026-08-18.**
**Founding ticket:** #37 (universal event logging — the MC sink). **Dependency:** #271 (presence Redis endpoint hardcoded — blocker, ruled 2026-08-18), same milestone.
**Authority:** operator rulings recorded on #37 (comments dated 2026-08-16 through 2026-08-18) and GDD §10.11 (Total Capture + the v25.1 mechanism/event-record/retention paragraphs, landed this session at `fc6d83c` and `c82d33e`). The tracker and GDD win over this brief on any divergence.

This is the **first and only implementation brief of the release** (scope law). It ships the MC sink: the creation-level taps in both processes, the Redis Stream hot tier, the Postgres persister, the durable-record model, read-only admin access, and the #271 endpoint fix. "The firehose works" when this brief is done.

---

## 1. Design rules — binding, do not deviate

1. **Total capture with the ruled chrome boundary.** Every game event is captured: every command (accepted or rejected), every outbound event of every client type (output, room-render, report, status, fight, map, redirect, quit, superseded), presence transitions. Excluded as **protocol chrome** (ruled 2026-08-18, GDD §10.11): the `ping`/`pong` keepalive, the connect-time `verbs` list, and the `complete` **response**. The `complete` **request** IS captured (player intent). Nothing else is excluded, conditionally or otherwise.
2. **Creation-level, one record per event.** Records are emitted where the event is born — never at the delivery choke point (`send_json` keeps its envelope-stamp role untouched). One `group_send` = one record; one ticker `send_to_player` call = one record even though delivery unpacks it into up to three client messages (text, status, fight).
3. **Audience is a field**, resolved at fan-out time: the list of character pks the event was addressed to, honoring exclude semantics. Personal events: `[character_pk]`. Room broadcasts: connected characters in the room minus excludes.
4. **Fire-and-forget by construction.** The emit helper's entire body is guarded; a sink failure (Redis down, serialization error, anything) drops the record and never raises into game code. No game path may ever block or break on MC.
5. **The choke-point discipline:** every creation site calls the emit helper; nothing may bypass it. In the consumer, `channel_layer.group_send` may appear **only** inside the new tapped wrapper (§5.4); in the ticker, only inside the two existing tapped helpers. Verification greps enforce this (§8).
6. **No FKs into live tables.** `actor_id` and `room_id` are loose integers plus a denormalized `actor_name` — never ForeignKeys (reseeds delete rows; the record survives).
7. **Append-only truth.** The admin surface is read-only: add, change, and delete all disabled. Nothing edits history.
8. **Never log secrets.** The single-session `token` (uuid nonce) is stripped from the superseded event's record. No credential, secret key, or session token ever enters a record.
9. **Unattributable pre-entry traffic is not captured** (no-character connect path, unauthenticated close): there is no actor to attribute. The deleted-while-connected redirect (a known `character_pk`) IS captured.
10. **Bare-local is out for MC work** (ruled): `local.py` uses `InMemoryChannelLayer` and no Redis. The containerized dev stack is the dev target for this brief and all MC briefs.

## 2. Verified state — technical claims, all confirmed against the code 2026-08-18

Every claim below was read from the file at brief-writing time (#252). Line numbers are as of branch tip `c82d33e`.

| Claim | Where |
|---|---|
| `SHYLAND_VERSION = "25.0"`; pin test asserts `'25.0'` | `django/src/apps/shyland/version.py:8`; `tests/test_b2_amendment1.py:118` |
| `redis>=5.0` is a direct dependency | `django/requirements.txt:9` |
| `REDIS_HOST` env read exists inline (default `'redis'`) in the channel layer and defender URL; **no settings constant yet** | `game_mvc/settings/base.py:82` and `:124` |
| Consumer already imports the async client: `import redis.asyncio as aioredis` | `consumers.py:11` |
| Presence client hardcodes its endpoint: `aioredis.from_url("redis://redis:6379")` | `consumers.py:458` (the #271 site) |
| Presence keys: `shyland:online:{pk}` with 90s expiry + heartbeat | `consumers.py:478-483` |
| Delivery choke point `send_json` (envelope stamp only, warns on missing `ts`) | `consumers.py:395-414` |
| Ingress: `receive_json` — `ping` branch `:544`, `complete` branch `:553`, echo `:565`, dying gate `:574`, dispatch guard `:584` | `consumers.py:540-596` |
| Connect path: character load `:426`, no-character redirect `:432`, group adds `:453,:456`, superseded group_send `:465`, presence write `:478`, verbs send `:499` | `consumers.py:420-512` |
| Disconnect: guarded teardown, `character_pk` may be absent | `consumers.py:514-534` |
| Personal-output helpers: `send_output:3455`, `output:3491` (duplicate twins), `send_report_lines:3553` | `consumers.py` |
| Status sends: 7 sites, all the form `await self.send_json(await self._status_payload(…))` | `consumers.py:1666,1752,2960,3004,3028,3652,4675` |
| Other direct creation sends: deleted-character redirect `:591`, no-exit warn `:665`, quit event `:1266`, room-render `:3633`, complete response `:3713` (chrome), map `:3824`, fight `:4663,:4667` | `consumers.py` |
| Delivery handlers (never tapped): `room_message:3335`, `player_message:3358` — their `send_json` calls at `:3356,:3373,:3382,:3391,:3393,:3397` are delivery, not creation | `consumers.py` |
| Consumer `group_send` sites (10): superseded `:465` (player group); room group `:684` (depart), `:700` (arrive), `:922` (say), `:1302` (pickup), `:1365` (drop), `:2115,:2199` (loot), `:3460` (`broadcast_to_room_exclude` helper), `:3484` (kibitz) | `consumers.py` |
| Ticker is async: `asyncio.run(self.tick_loop())` | `run_tick_engine.py:65` |
| Ticker outbound funnels through exactly two helpers — `send_to_player:1714` (player group; text + optional status/fight/event), `broadcast_to_room:1739` (room group; `exclude_pk`/`exclude_pks`) — the only two `group_send` sites in the file | `run_tick_engine.py` |
| Ticker online-filter precedent: `_online_character_pks` | `run_tick_engine.py:981` |
| Compose: `ticker` service = `image: shyland-django`, `command: python manage.py run_tick_engine`, env block, `depends_on` postgres healthy + redis started, `restart: unless-stopped` — the block `mc-persister` mirrors | `docker-compose.yml:58-73` |
| No read-only admin precedent exists (no `has_add_permission` overrides) — this brief introduces the pattern | `apps/shyland/admin.py` |
| `JSONField` convention in models | `models.py:474` et al. |
| Test suite baseline: **687 tests**, in-container path form only | V25.0 Brief 1 closeout |

## 3. Step 0 — verify-and-signal (standing)

Confirm this brief exists verbatim at the branch tip. Create `docs/shyland/Shyland_V25.1_Brief_1_Closeout.txt` as a stub (one-line session-start record: date, brief name, branch), commit, **push immediately**. Commit and push at every step boundary hereafter; branch only, never merge.

## 4. Step 1 — version start (standing, first brief of the release)

1. `SHYLAND_VERSION` → `"25.1-DEV"` in `version.py`; pin test at `test_b2_amendment1.py:118` → `'25.1-DEV'` in the **same commit**, its own commit.
2. `make deploy-dev` from the worktree (the version-start deploy).

## 5. Implementation

### 5.1 Settings (`game_mvc/settings/base.py` — shared surface, operator-authorized 2026-08-18 in-session)

- Add named constants: `REDIS_HOST = env('REDIS_HOST', default='redis')` and `MC_STREAM_MAXLEN = env.int('MC_STREAM_MAXLEN', default=100000)`.
- Re-point the two existing inline `env('REDIS_HOST', …)` reads (`:82` channel layer, `:124` defender URL) at the constant. Identical values everywhere today — zero behavior change.

### 5.2 The #271 fix

`consumers.py:458` → build the presence URL from the constant: `aioredis.from_url(f"redis://{settings.REDIS_HOST}:6379")`. Nothing else about presence changes.

### 5.3 `apps/shyland/mc.py` — the emit helper (new module)

Standalone; game code imports `mc`, never the reverse. Contents:

- `MC_STREAM_KEY = 'mc:events'`. Lazy module-level async client (`redis.asyncio.Redis`) built from `settings.REDIS_HOST`, port 6379, db 0 (shared with the channel layer and presence keys — key namespaces don't collide).
- `async def mc_emit(kind, *, actor_id=None, actor_name='', room_id=None, audience=(), data=None)` — the single creation choke point. Builds the flat record — `kind`, `actor_id` (str, `''` when none), `actor_name`, `room_id` (str, `''` when none), `audience` (JSON array of ints), `data` (JSON object) — and `XADD`s with `maxlen=settings.MC_STREAM_MAXLEN, approximate=True`. **The entire body sits in `try/except Exception`**: on failure, drop the record and emit at most one `logger.warning` per 60 seconds (module-level throttle timestamp) so a dead Redis never floods the logs. No return value is ever used by callers.
- `async def resolve_room_audience(room_id, exclude_pks=())` — pks of characters whose `current_room_id` is `room_id` (ORM via `database_sync_to_async`), filtered to those with a live presence key (`MGET` on `shyland:online:{pk}`), minus `exclude_pks`. Returns a sorted list. Same fire-and-forget posture when called from inside the emit path — a resolver failure yields `[]`, never an exception. (Precedent for both mechanics: `consumers.py` presence filtering and `run_tick_engine.py:981`.)

### 5.4 Consumer taps (`consumers.py`)

**Ingress (`receive_json`):**
- `ping`/`pong` branch: untouched — chrome, no record.
- `complete` branch: emit `kind='cmd'`, `data={'complete': <text>}`, audience omitted (`[]`).
- Command text: immediately after the verb/args parse (`:567-569`) and **before** the dying gate, emit `kind='cmd'`, `data={'raw': raw, 'verb': verb, 'args': args}`, `actor` = this character, `room_id` = current room. **No outcome field**: rejections (unknown command, gate refusals, CLI errors) are themselves captured as the immediately following `out` records — outcome is stream-adjacent by construction, and the tap stays a single unconditional call.

**Presence:** at the end of the successful connect path (after the group adds and presence write), emit `kind='connect'` (`audience=[pk]`, `data={}`). In `disconnect`, when `character_pk` exists, emit `kind='disconnect'` with `data={'code': code}`. The no-character and unauthenticated paths emit nothing (rule 9).

**Personal out:** tap inside the three helpers — `send_output`, `output`, `send_report_lines` — emitting `kind='out'` with `audience=[character_pk]` and `data` = the client payload minus `ts`/`seq` (e.g. `{'type':'output','text':…,'category':…}` or the report-lines form). Guard: if the connection has no `character_pk` yet (pre-entry `output` call at `:429`), skip the emit (rule 9).

**Direct creation sends** — tap each with an adjacent `mc_emit` (`kind='out'`, `audience=[character_pk]`, `data` = payload minus `ts`):
- deleted-character redirect `:591` (actor = the known `character_pk`)
- no-exit warn `:665` (includes `hint_exits` in data — it's part of the payload)
- quit event `:1266`
- the 7 status sends: introduce `async def send_status(self, char, room)` that composes `_status_payload`, sends, and emits (`data={'type':'status'}` plus the payload's non-chrome fields — capture the payload as-is minus `ts`); refactor the 7 sites to call it.
- room-render `:3633` (inside `send_room_description` — one emit for the render payload)
- map `:3824` (`send_map` — the full map payload is the data; low frequency, capture whole)
- fight `:4663,:4667`
- **Not tapped (chrome):** verbs `:499`, pong `:547`, complete response `:3713`. **Not tapped (delivery):** every send inside `room_message`/`player_message`.

**Broadcasts — the wrapper (discipline rule 5):** add `async def mc_group_send(self, group, event)` which (a) derives the audience — `player_{pk}` group → `[pk]`; `room_{id}` group → `await mc.resolve_room_audience(id, exclude_pks=…)` honoring the event's exclude semantics (`exclude` == own channel → exclude own pk; `exclude_pk`; `exclude_pks`) — (b) emits `kind='out'` with `data` = the event dict minus `ts` **and minus `token`** (rule 8), and (c) performs the `channel_layer.group_send`. Mechanically convert all 10 sites (`:465,:684,:700,:922,:1302,:1365,:2115,:2199,:3460,:3484`) to call it with their payload dicts **unchanged**. After this step, `channel_layer.group_send` appears in `consumers.py` only inside `mc_group_send`.

### 5.5 Ticker taps (`run_tick_engine.py`)

Tap inside the two existing helpers, nothing else changes:
- `send_to_player`: one emit per call — `kind='out'`, `actor_name='ticker'` (the process identity, always; finer attribution lives in `data`), `audience=[character_pk]`, `data` = `{text, category, status, fight, event}` with `None` values omitted and `ts` stripped.
- `broadcast_to_room`: `kind='out'`, `audience = await mc.resolve_room_audience(room_id, exclude_pks=…)` from `exclude_pk`/`exclude_pks`, `data={text, category}`.

The ticker's `group_send` calls remain exactly where they are — inside these tapped helpers.

### 5.6 The durable record (`models.py` + migration)

```python
class MCEvent(models.Model):
    """The MC durable record (#37). Append-only; no FKs into live tables
    by design (GDD §10.11) — reseeds delete rows, the record survives."""
    stream_id = models.CharField(max_length=32, unique=True)
    ts = models.DateTimeField(db_index=True)
    kind = models.CharField(max_length=16)
    actor_id = models.BigIntegerField(null=True, blank=True)
    actor_name = models.CharField(max_length=64, blank=True, default='')
    room_id = models.BigIntegerField(null=True, blank=True)
    audience = models.JSONField(default=list, blank=True)
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['kind', 'ts']),
            models.Index(fields=['actor_id', 'ts']),
            models.Index(fields=['room_id', 'ts']),
        ]
```

`ts` derives from the stream id's millisecond prefix (timezone-aware UTC). Migration: `make makemigrations APP=shyland && make migrate`; commit the migration file.

### 5.7 The persister (`management/commands/run_mc_persister.py`)

Sync loop, sync `redis.Redis` client from `settings.REDIS_HOST` (a management command doing ORM writes — no async needed):

1. Ensure the group: `XGROUP CREATE mc:events persister 0 MKSTREAM`, swallowing `BUSYGROUP`.
2. Loop: periodically `XAUTOCLAIM` pending entries idle > 60s (crash recovery); `XREADGROUP GROUP persister worker-1 COUNT 500 BLOCK 5000` on `>`.
3. Batch → `MCEvent` rows → `bulk_create(ignore_conflicts=True)` (the unique `stream_id` makes replay idempotent) → `XACK` the batch. **Ack only after a successful write**; on DB failure, back off and retry without acking.
4. A malformed entry never crashes the loop: store what parses (raw fields into `data`), log one warning, ack, continue.
5. Graceful shutdown on SIGTERM (finish the in-flight batch, exit 0). Startup line and a periodic drained-count line to stdout, matching the ticker's logging style.

### 5.8 Compose service (`docker-compose.yml` — shared surface, operator-authorized 2026-08-18 in-session)

Add `mc-persister`: mirror the `ticker` block verbatim (`image: shyland-django`, same env block, same `depends_on`, `restart: unless-stopped`) with `command: python manage.py run_mc_persister`.

### 5.9 Read-only admin (`admin.py`)

Register `MCEvent`: `list_display = ('ts', 'kind', 'actor_name', 'room_id', 'short_data')` (a truncated text column), `list_filter = ('kind',)`, `search_fields = ('actor_name', 'data')`, `date_hierarchy = 'ts'`, and `has_add_permission`/`has_change_permission`/`has_delete_permission` all returning `False` (rule 7 — this introduces the repo's read-only-admin pattern).

### 5.10 CLAUDE.md + doc lines (the ruled Redis role change, rides this release)

- CLAUDE.md Redis bullet: "Used exclusively as the Django Channels channel layer. Not a general-purpose cache." → "**Redis:** the Django Channels channel layer, the Shyland presence keys, and the MC event stream (hot tier — Streams, bounded window). Not a general-purpose cache."
- CLAUDE.md infrastructure table: add the `mc-persister` row (same image as `django`, "MC durable-record persister (`run_mc_persister` management command)").
- These are the operator-ruled doc updates recorded on #37 (2026-08-16); they land in this brief's final doc commit alongside the architecture doc (§9).

## 6. Tests (new: `tests/test_mc_sink.py`, `tests/test_mc_persister.py`)

Mock-based — **no new test dependencies**. Cover at minimum:
- `mc_emit` produces the correct flat XADD fields (kind/actor/room/audience/data JSON) with `maxlen` and `approximate=True`.
- Fire-and-forget: a client that raises on `xadd` → no exception propagates; warning throttle honored (second failure within 60s logs nothing).
- Chrome boundary: `ping`, the `verbs` payload, and the `complete` response produce no emit; a `complete` request produces a `cmd` record.
- The superseded record contains no `token` key (rule 8).
- `resolve_room_audience`: presence-filtered, exclude-honoring, failure → `[]`.
- Persister: entry → row field mapping; `ts` derivation from the stream id; duplicate `stream_id` replay is a no-op (`ignore_conflicts`); malformed entry is stored-raw + acked, loop survives.
- The moved pin test (`'25.1-DEV'`).

Suite invocation (the only working form): `python manage.py test apps/shyland/tests` via `docker exec` in the django container. Baseline 687 — expect 687 + new, all passing.

## 7. Deploy (standing)

`make deploy-dev` from the worktree once implementation and §8 verification pass. No production action of any kind in this session (Deployment Law).

## 8. Verification — all must pass before issue closes or the arch doc step

1. Full in-container suite passes (§6 count arithmetic: baseline 687 + this brief's new tests, zero failures).
2. Discipline greps (exact expectations):
   - `grep -n 'channel_layer.group_send' django/src/apps/shyland/consumers.py` → hits only inside `mc_group_send`.
   - `grep -n 'group_send' django/src/apps/shyland/management/commands/run_tick_engine.py` → hits only inside `send_to_player` / `broadcast_to_room` (plus the one docstring mention at `:1705`).
   - `grep -n 'redis://' django/src/apps/shyland/consumers.py` → no hardcoded endpoint remains (#271 proof; the settings-built f-string is the only form).
3. `make deploy-dev`, then live on the dev stack: connect, `look`, `say hello`, move once, `quit`. Then:
   - `docker exec game-mvc-redis redis-cli XLEN mc:events` > 0; `XRANGE mc:events - + COUNT 5` shows well-formed records (kind/actor/audience/data).
   - `MCEvent.objects.count()` (via `make shell`) grows to match; a `say` row's `audience` lists the connected characters in the room; the `cmd` row for `say` precedes the say broadcast's `out` row in stream order. (The echo `out` row legitimately precedes the `cmd` row — echo fires at `:565`, before the verb/args parse where the cmd tap sits; this is correct, not a defect.)
   - No `pong`/`verbs` records exist: `MCEvent.objects.filter(data__type='pong').count() == 0` and none with a `verbs` payload.
   - Resilience: `docker stop <mc-persister>` → play → `XLEN` grows while the row count holds; `docker start` → backlog drains, no gap (row count catches up to XLEN's tail).
4. Admin: MC event list renders, filters work, no add/change/delete affordances.

## 9. Architecture doc — last, gated

**This step is gated on all implementation and verification steps above being complete and passing.** Update `Shyland_Architecture_v25.md` in place:
- Header: append the Version 25.1 entry; stamp → 25.1; **the "as of commit" hash MOVES** (this is an architectural change).
- The delivery-choke-point section (the envelope text at ~:1375 rewritten in V25.0): extend with the shipped creation-level MC tap description.
- New MC sink section: the emit helper and discipline, the four kinds + chrome boundary, audience resolution, the stream (key, MAXLEN, db 0), the persister (group, batch, idempotency), `MCEvent`, the read-only admin, the #271 settings constant.
- The Redis role line(s): channel layer + presence + MC hot tier (matching §5.10's CLAUDE.md language).
- Container/stack inventory: add `mc-persister`.

## 10. Operator playtest checklist (dev stack)

1. Play a few minutes: connect, `look`, move through 2–3 rooms, `say` something with a second character present if convenient, buy or sell one item, `attack` something, `quit`.
2. Django admin → MC events: records exist for each thing you did; kinds read `cmd`/`out`/`connect`/`disconnect`; your `say` shows the room's occupants in `audience`; there are no add/edit/delete buttons.
3. Type `sudo anything` — the `cmd` record with its arguments is visible in admin (ingress capture, the #262 food).
4. Confirm no `pong` records exist (filter/search the list).
5. Resilience (two docker commands on the dev host): `docker stop` the mc-persister container, play for a minute, confirm the admin count froze; `docker start` it, confirm the backlog drains in.

## 11. Closeout

- Complete the closeout report in place (`Shyland_V25.1_Brief_1_Closeout.txt`): technical pre-flight result, commits, deviations, verification outcomes (including the §8 grep results and the resilience check), final commit hash, **and the operator playtest disposition** (#170).
- **Issue closes, gated on §8 passing:** #37 (comment naming this brief and the final hash) and #271 (comment naming the settings-constant commit). Both sit in milestone Version 25.1.
- **PENDING DEPLOY-TIME ACTIONS: none.** The production deploy at the closeout tail (`make deploy-prod`) builds the new image, runs the migration, and brings up `mc-persister` as ordinary compose reconciliation. No data actions, no seed changes. (The prod stream starts empty and fills from live play; the persister creates its group on first run.)
- Volume note for the record: status-sync events dominate row growth; the closeout reports the observed dev row rate so the durable tier's "unbounded pending an operational trigger" posture (GDD §10.11) has a first data point.

## 12. Out of scope — do not touch

- Combat internals instrumentation (#33 — next release), egress/agents (#267/#266/#262/#265), the command-pattern watcher (#191).
- Any GDD source edit (`make gdd` only if a brief-directed mechanical need arises — none is expected).
- Any change to game behavior, output text, or command semantics. This brief is additive capture only; the only behavior-adjacent edits are the mechanical broadcast-wrapper conversion (payloads unchanged) and the #271 URL construction (value unchanged).
- Redis volumes/AOF (ruled: volumeless; Postgres is durability), Redis Stack modules (ruled out), delivery-level taps (ruled out for 25.1).
