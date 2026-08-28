# Shyland V25.10 — Brief 1: Truthful Delivery and the Filing Bot

**Release:** Version 25.10 (point release) · **Milestone:** `Version 25.10` (#62) · **Branch:** `version_25_10`
**Founding ticket:** #301 (sudo files GitHub issues from in-game). **Riding the release:** #304 (per-(bot, target) singleton), #305 (persist receipts with the stored answer), #306 (deterministic delivery — the report family grows).
**Written by:** V25.10 design session, 2026-08-28. All rulings recorded on the issues the same day; GDD §10.11 passage committed at 203f3ff (`(v25.10, #301/#304/#305/#306, pending implementation)`).

This is the **first implementation brief of the release**: it opens with the version-constant bump and version-start `make deploy-dev`.

**Character of the release:** code-only. **No model change, no migration, no seed data, no client change.** Game-side: two files (`mc_consumer.py`, `mc_door.py`) plus tests. Bot-side: `agents/sudo_bot.py` and `agents/botctl.py`. One new operator-provisioned secret (a GitHub token on the bot host — never on the game box).

---

## §1 Technical claims verified at writing time (#252)

Every structural claim below was verified against the code on branch `version_25_10` @ 203f3ff by the design session on 2026-08-28. Line numbers are as-of that commit.

1. `MCEgressConsumer.connect` (mc_consumer.py:111–135) gates in order: unauthenticated → bare `close()`; non-member of `agents.shyland` → accept-then-`close(code=4403)`; kill switch → accept-then-`close(code=4503)`; then sets `self._agent = user.username`, accepts, sends the `hello` frame. **No per-agent attach registry exists anywhere in the consumer.** `disconnect` (137–142) cancels the stream task and logs detach — the only teardown hook.
2. The `django` container runs a **single Daphne process** (`django/Dockerfile:23` — `CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", ...]`; no worker fan-out anywhere in `docker-compose.yml`). Daphne's WebSocket ping defaults are in effect (no `--ping-interval`/`--ping-timeout` flags): interval 20s, timeout 30s.
3. `REPORT_KINDS = ('inventory',)` (mc_door.py:1680). `a_report` (1701–1735) resolves `to`, validates `kind` against `REPORT_KINDS` (`bad-params` naming the kinds), resolves `character`, admin-gates `to` (`not-admin`), then delivers: a `_send_player_line(to.pk, f'sudo: ...', 'sudo', ...)` leader plus two `audited_send` frames `{'type': 'player_message', 'category': 'report', 'lines': ...}`. Offline ⇒ `{'delivered': False, ...}`, never an error.
4. `_memories_payload` (mc_door.py:1470–1493): agent-scoped (`_agent_user(agent_name)`), optional kind/name-icontains/since/until filters, `-created_at` order, cap `MEMORY_LIST_CAP` (50), waypoint summaries resolved live via one `in_bulk` joined room query; `_memory_summary` (1456–1466) renders `Zone: Area: Room` (area omitted when absent) or `(room no longer exists)` for a dangling waypoint, `N lines` for a bundle. `_memory_payload` (1513–1536) returns the full row with bundle lines rendered legible and `taught_by`/`created_at`/`updated_at`. `MEMORY_KINDS` derives from `AgentMemory.KIND_CHOICES` (waypoint, bundle).
5. `QUERY_HANDLERS`/`ACTION_HANDLERS` (mc_door.py:1742–1772) are the dispatch tables; the consumer resolves kinds through them (mc_consumer.py:208–209).
6. Bot-side (`agents/sudo_bot.py`): `pidfile(target)`/`convo_file(target)` (64–69) derive from `AGENTS_DIR = Path(__file__).resolve().parent` (59) — per-checkout by construction. `CLOSE_MEANINGS` (91–94) holds 4403 and 4503 only. `--log` default is `AGENTS_DIR / 'sudo_bot.log'` (1624); `--password-file` default is `AGENTS_DIR / '.secrets' / 'agent-sudo'` (1616–1618). `cmd_run` writes the pidfile (1587) and unlinks it in `finally` (1593–1597). `import requests` at line 56; `requests` is in `agents/requirements.txt`.
7. `_handle_sudo` (1266–1310): per-turn `ReceiptLedger` + `ActionLog`; **`self.convos.record(actor_name, request_turn, final_text)` at line 1301 runs BEFORE `receipts = actions.receipts()` at 1302** — the stored answer today carries no receipts; delivery happens when `final_text or receipts` (1307).
8. `ConversationStore` (1078–1126): `_data` keyed by admin character name; each exchange `{'q': request, 'a': answer}` plain text; `model_history` replays `q`/`a` as user/assistant text turns and expires idle threads; `record(name, request_text, answer_text)`; atomic save via `.tmp` + `replace`.
9. `_execute_tool` (1312–1354): the single choke point — names outside `QUERY_KINDS`/`ACTION_KINDS` draw `{'error': 'unknown-tool'}`; `CHECKED_ARGS` ledger gate; door round trip; `ledger.harvest` on success; `actions.add(name, params, data)` for every successful action except `answer` (1346–1347). Its signature is `(self, call, ledger, actions)` — it does **not** receive `actor_name`; the call site is line 1297.
10. `_compose_receipt` (880–925) composes per-name receipt strings; its `report` branch (920–924) reads `params.get('character')` unconditionally. `ActionLog.receipts()` truncates to `MAX_RECEIPT_LEN` (200) and caps at `MAX_RECEIPTS` (20).
11. The `report` tool schema in `TOOLS` (643–664): `kind` enum `['inventory']`, required `['to', 'character', 'kind']`.
12. `botctl.py`: `BotPaths` (66–77) derives `module`, `log`, `key_file`, `pid_file`, `convo_file` — log/pid/convo all under `AGENTS_DIR`, per-checkout; `cmd_start` (134–165) injects `ANTHROPIC_API_KEY` from `key_file` into the **child environment only** and opens the log for append before `Popen(..., start_new_session=True)`.
13. `SHYLAND_VERSION = "25.9"` (`django/src/apps/shyland/version.py:8`); the pin test asserts the literal at `tests/test_b2_amendment1.py:118`.
14. Suite baseline: 877 tests green in-container at the 25.9 close.
15. `sudo_bot.py` `run()` (1443–1501) logs `ConnectionClosed` with `CLOSE_MEANINGS.get(code, 'server closed the connection')` and retries on capped backoff (2s → 60s) — a 4409-refused bot retries patiently by existing behavior, with or without the meanings entry.

The brief was given one end-to-end read for self-consistency before commit.

---

## §2 Design rules binding this brief (do not deviate)

1. **One agent account = one attached connection** (#304, operator-ruled): hard reject, **never takeover**. Close code **4409**. The claim registry is **in-process** (module-level in `mc_consumer.py`) — deliberately not Redis: a crash must destroy the registry together with the connections it guards, making a stale lock structurally impossible.
2. **Gate order in `connect` is fixed:** auth → membership (4403) → kill switch (4503) → singleton (4409). A killed door reports killed, not conflict; a non-member sees 4403 either way (the leak law).
3. **Machinery composes, the game renders, model prose is commentary** (#306, standing doctrine, GDD §10.11). The new report kinds are door-composed from live data. Nothing about them is model-formatted.
4. **The store remembers what the game confirmed, not what the model said** (#305): the persisted answer carries the turn's receipt lines; the exchange shape `{'q', 'a'}` and the provider-neutral plain-text form are unchanged.
5. **Filing is bot-side** (#301): the GitHub token lives on the bot host under `agents/.secrets/` (named, never printed, never committed, never argv — the `ANTHROPIC_API_KEY` custody pattern, #268 law). The game box holds no GitHub credentials; **the door grows no new vocabulary for filing.**
6. **The confirm gate:** sudo reads the complete draft back (title and body, verbatim) and files **only on an explicit yes**. The gate is behavioral (prompt + tool description) by design this release; the filing's *honesty* is structural — the receipt carries the number and URL from the API response, never model text.
7. **Filed issues are thin:** title + body only, assignee applied by machinery, **no labels** — triage fattens them (doctrine).
8. All log lines UTC-stamped with trailing Z (already the standing formatter — do not regress).
9. Never print or log a credential value anywhere, in any step, including verification output.

---

## §3 Step 0 — verify and signal

Standard Step 0: confirm this brief exists verbatim at the `version_25_10` tip (whitespace-only drift is report-and-accept); create `docs/shyland/Shyland_V25.10_Brief_1_Closeout.txt` as a stub opening with a one-line session-start record (date, brief name, branch); commit; **push immediately**. Complete the stub in place at closeout. Commit and push at every step boundary thereafter; branch only, never merge.

---

## §4 Step 1 — version start (opening act)

1. In its own commit: `django/src/apps/shyland/version.py` → `SHYLAND_VERSION = "25.10-DEV"`, and the pin assertion at `tests/test_b2_amendment1.py:118` → `'25.10-DEV'` (same commit, standing law).
2. `make deploy-dev` from the worktree (the version-start deploy).

---

## §5 Step 2 — game-side: the door singleton (#304)

**File: `django/src/apps/shyland/mc_consumer.py`**

1. Add a module-level registry: `ATTACHED = {}` — agent username → `channel_name`. Module docstring gains a v25.10 note (one agent account = one attached connection; in-process by design — the registry must die with the process that owns the connections).
2. In `connect`, **after** the kill-switch gate and before the current accept/hello block:
   - If `ATTACHED.get(user.username)` is set: `accept()`, send `{'type': 'error', 'error': 'already-attached', 'detail': 'Another connection for <username> is already attached.'}`, `close(code=4409)`, log `'shyland mc: egress attach refused — already attached (agent=%s)'`, and return **without** setting `self._agent` and without claiming.
   - Otherwise claim before accepting: `ATTACHED[user.username] = self.channel_name`, then proceed exactly as today (`self._agent = ...`, accept, hello, attach log line).
3. In `disconnect`, guarded release (the guarded-presence-delete discipline): if `self._agent` is set and `ATTACHED.get(self._agent) == self.channel_name`, delete the entry. A rejected duplicate (which never claimed and never set `_agent`) must not disturb the holder's claim.
4. No other behavior changes: tail/query/action handling, kill-switch semantics, and the 4403/4503 paths are byte-identical.

**File: `agents/sudo_bot.py`** — `CLOSE_MEANINGS` gains `4409: 'refused: another connection for this account is already attached'`. No behavior change: the existing backoff loop (§1 claim 15) is the correct response — the bot waits patiently for the holder to die, then attaches.

**Freed-slot guarantee (verified, recorded on #304):** clean stop or `kill -9` of the holder closes its socket at the OS level → Channels fires `disconnect` immediately → slot freed. A truly half-dead peer is reaped by Daphne's default WS ping (20s/30s) within ~50s. A Django restart destroys registry and connections together.

**Tests** (in the new `tests/test_v25_10_brief1.py`, using the existing egress communicator patterns from `test_mc_egress.py` / `test_mc_agent_door.py`):

| # | Scenario | Expected |
|---|---|---|
| 1 | Second connection, same agent account, first still attached | accepted, `error: already-attached` frame, closed 4409 |
| 2 | First disconnects, then a new connection for the account | admitted normally (hello frame) |
| 3 | Two different agent accounts concurrently | both admitted |
| 4 | After a rejected duplicate, a third attempt while the holder lives | still 4409 (the rejected attempt's teardown did not free the holder's claim) |
| 5 | Kill switch engaged + duplicate account | 4503 (precedence: killed before conflict) |
| 6 | Non-member duplicate | 4403 (membership before singleton) |

---

## §6 Step 3 — game-side: the report family grows (#306)

**File: `django/src/apps/shyland/mc_door.py`**

1. `REPORT_KINDS = ('inventory', 'waypoints', 'memories', 'memory')`.
2. `a_report` becomes kind-dispatched. Common to every kind: `to` resolved and admin-gated exactly as today; unknown kind ⇒ the existing `bad-params` naming all kinds; offline recipient ⇒ `ok: true, delivered: false`, nothing sent. Per kind:
   - **`inventory`** — byte-identical to today (requires `character`; leader + doll/inv sections; result `{'delivered', 'item_count'}`). Existing tests must pass with zero edits.
   - **`waypoints`** — no `character` param. Rows: the **calling agent's** waypoint memories, `-created_at`, capped `MEMORY_LIST_CAP` (50), with the store's true total counted before the slice. Leader (via `_send_player_line`, category `sudo`, exactly the inventory-report pattern): `sudo: {total} waypoints` — append ` (newest {len(rows)} shown)` when total > rows shown; when total is 0 the leader alone is the report. Lines (one `player_message`, category `report`, `lines` list): `#{id} {name} — {path}` per row, path rendered live per the `_memory_summary` semantics (`Zone: Area: Room`, area omitted when absent; `(room no longer exists)` when dangling). Result `{'delivered', 'count': total}`.
   - **`memories`** — identical shape to `waypoints` but over all kinds; line form `#{id} {kind} {name} — {summary}` (waypoint summary = live path; bundle summary = `{N} lines`). Leader `sudo: {total} memories` (same truncation suffix rule). Result `{'delivered', 'count': total}`.
   - **`memory`** — requires integer `id` (`_require_int`); the **calling agent's** row or `not-found` (the `q_memory` message form). Leader: `sudo: {kind} '{name}' (id {id})`. Lines: for a waypoint, `where: {path}` (live; `(room no longer exists)` when dangling); for a bundle, one line per stored line `{quantity}× {slug} Mk {mk_tier} {rarity}`; then `taught by {username}` (or `taught by (unknown)` when null) and `created {created_at} / updated {updated_at}` (ISO-8601, the `_memory_payload` values). Result `{'delivered', 'id'}`.
3. Composition is door-side in new sync helpers alongside `_memories_payload`/`_memory_payload` (reusing their query shapes — agent scoping via `_agent_user(agent_name)`, the `in_bulk` live room resolution, the bundle positional-lines decode). **This table is authoritative over any prose above it.**

**File: `agents/sudo_bot.py`**

4. The `report` tool schema (§1 claim 11): `kind` enum grows to the four kinds; `character` moves out of `required` (schema-required: `['to', 'kind']`; description states `character` is required for `inventory` and `id` for `memory` — the door validates authoritatively); add integer `id` property. Description gains: memory/waypoint listings and memory detail are reports too — prefer them whenever an admin asks to *see* what the bot knows.
5. `_compose_receipt`'s `report` branch becomes kind-aware: `report ({kind}) to {to}: {status}`, with ` on {character}` inserted only when `character` was passed — the current form must not render `on None` for the new kinds.
6. System prompt: extend the existing "prefer the report action" standing order (§1 — SYSTEM_TEMPLATE lines 770–772): when an admin asks what waypoints or memories exist, or for one memory's detail, use `report` (kinds `waypoints`/`memories`/`memory`) — the game renders the listing itself, deterministically; use the `memories`/`memory` *queries* only when the data feeds the bot's own next step rather than the admin's eyes.

**Tests** (same new file):

| # | Scenario | Expected |
|---|---|---|
| 7 | `report` unknown kind | `bad-params` naming all four kinds |
| 8 | `waypoints`, empty store | delivered, leader `sudo: 0 waypoints`, no lines frame |
| 9 | `waypoints`, rows incl. one dangling room | `#{id} {name} — {path}` lines; dangling row shows `(room no longer exists)` |
| 10 | `memories`, mixed kinds | kind-tagged lines, both summary forms |
| 11 | `memory` by id — waypoint and bundle | detail line-sets exactly as specified in the table |
| 12 | `memory`, unknown id | `not-found` |
| 13 | `memory`/`waypoints` agent-scoping | agent B's report never shows agent A's rows |
| 14 | `to` not an admin | `not-admin`; offline admin ⇒ `delivered: false`, nothing sent |
| 15 | `inventory` regression | pre-existing report tests pass with zero edits |

---

## §7 Step 4 — bot-side: the central runtime directory (#304)

**Both files.** Define once per file: `RUNTIME_DIR = Path.home() / '.shyland'`.

1. `agents/sudo_bot.py`: `pidfile(target)` → `RUNTIME_DIR / f'.sudo_bot.{target}.pid'`; `convo_file(target)` → `RUNTIME_DIR / f'.sudo_bot_conversations.{target}.json'`; the `--log` default → `RUNTIME_DIR / 'sudo_bot.log'`. `cmd_run` creates the directory (`RUNTIME_DIR.mkdir(parents=True, exist_ok=True)`) before the pidfile write. Module docstring's path map updated.
2. `agents/botctl.py`: `BotPaths.log` → `RUNTIME_DIR / f'{name}_bot.{target}.log'`; `pid_file`/`convo_file` → the RUNTIME_DIR forms above (generalized on `{name}`: `.{name}_bot.{target}.pid`, `.{name}_bot_conversations.{target}.json`). `module` and `key_file` **stay checkout-scoped** — code belongs to the checkout it ships in; secrets stay under `agents/.secrets/`. `cmd_start` creates `RUNTIME_DIR` before opening the log. Header docstring's path map updated (the "one map for humans" comment, §1 claim 12).
3. **No state migration.** Old per-checkout pid/log/convo files are abandoned in place (conversations expire in 600s; pidfiles are transient; logs are history). The operator prunes; the brief must not delete anything.
4. **Transition note (record in the closeout):** a bot already running was started by old code and owns an old-location pidfile — the new botctl cannot see it. Before starting a new-code bot on a target, stop any running bot for that target **from the checkout that started it**. If missed, the door's 4409 is the backstop: the new bot logs `already attached` and retries instead of double-acting — the 25.9 incident shape, now failing safe.

---

## §8 Step 5 — bot-side: the store remembers what the game confirmed (#305)

**File: `agents/sudo_bot.py`**, `_handle_sudo` (§1 claim 7):

1. Reorder: compute `receipts = actions.receipts()` **before** the record call.
2. The stored answer folds the receipt lines in as plain text: `stored = final_text` plus, for each receipt, a line `[did: {receipt}]` — receipt lines joined by `\n`, appended after the text with a `\n` separator (text absent ⇒ the `[did: …]` lines alone; neither text nor receipts ⇒ record the empty answer exactly as today). `record()`'s signature and the exchange shape `{'q', 'a'}` are unchanged.
3. System prompt gains one sentence in the receipts-not-intentions paragraph: earlier turns' answers in this conversation carry `[did: …]` lines for every action the game actually confirmed — **a past answer claiming an action without a `[did: …]` line performed nothing**, and is never a license to skip a tool call now. (The v25.9 deviation-8 standing order stays in force beneath it — defense-in-depth.)
4. `ConversationStore`'s docstring notes the stored answer carries game-confirmed receipt lines (v25.10, #305).

---

## §9 Step 6 — bot-side: sudo files the tickets (#301)

**File: `agents/botctl.py`**

1. `BotPaths` gains `github_token_file = AGENTS_DIR / '.secrets' / f'github-token.{name}'`. `cmd_start`: if the file exists and is non-empty, inject its stripped contents as `GITHUB_TOKEN` into the **child environment only** (the `ANTHROPIC_API_KEY` pattern — never argv, never echoed, never logged). An absent token file is not an error — the bot refuses filing legibly at call time instead. Docstring path map updated.

**File: `agents/sudo_bot.py`**

2. Constants: `GITHUB_REPO = 'KnightOfNight/games-mvc'`, `GITHUB_API = 'https://api.github.com'`, `GITHUB_ASSIGNEE = 'KnightOfNight'`, `GITHUB_TIMEOUT = 15`. `cmd_run` reads `os.environ.get('GITHUB_TOKEN', '')` into the config (never logged; the startup log line must not mention the token's value or presence beyond `filing=enabled|disabled`).
3. New tool in `TOOLS` — `file_issue`; input schema `{title: string, body: string}`, both required. Description (the confirm gate lives here and in the prompt): gather the title and body conversationally over as many turns as needed; read the **complete draft back verbatim** (title and full body); call this tool **only after the admin explicitly confirms** the read-back draft — never on inference, never "while you're at it"; machinery applies the assignee and a provenance footer; the game renders the filing receipt with the real issue number.
4. Execution: a `BOT_ACTIONS = frozenset({'file_issue'})` set; `_execute_tool` gains a branch **before** the door round trip: names in `BOT_ACTIONS` run locally and never become door frames. Thread `actor_name` through: `_execute_tool(self, call, ledger, actions, actor_name)` and the call site at line 1297 updated. The handler `_file_issue(actor_name, params)`:
   - Missing or empty `title` or `body` (non-string included) ⇒ error tool_result `{'error': 'bad-params', 'detail': ...}` naming the field — the model recovers in its loop by finishing the draft.
   - No token configured ⇒ error tool_result `{'error': 'not-configured', 'detail': 'no GitHub token on this bot host; filing is disabled'}` — the model tells the admin plainly.
   - Compose the body: the drafted body + `\n\n---\n_Filed via sudo (in-game) by {actor_name}, {UTC ISO-8601 timestamp}Z._`
   - `await asyncio.to_thread(requests.post, f'{GITHUB_API}/repos/{GITHUB_REPO}/issues', ...)` with json `{'title', 'body', 'assignees': [GITHUB_ASSIGNEE]}`, headers `{'Authorization': 'Bearer <token>', 'Accept': 'application/vnd.github+json'}`, `timeout=GITHUB_TIMEOUT`.
   - HTTP 201 ⇒ success data `{'number', 'url' (html_url), 'title'}`; anything else ⇒ error tool_result `{'error': 'github', 'detail': 'HTTP {status}'}` (response body **not** echoed into the detail — it can be large; log a bounded excerpt instead). Log lines for attempt and outcome (no token, no secrets).
5. Receipts: `_compose_receipt` gains a `file_issue` branch — `filed issue #{number}: {url}` — and `_execute_tool`'s success path calls `actions.add` for `BOT_ACTIONS` successes as it does for door actions (§1 claim 9). **No ledger harvest** for filing — issue numbers belong to no door id-space, deliberately. The receipt rides the turn's `answer` delivery (landing on the MC record via the door's `agent_action` record for `answer`, as all receipts do) and persists with the stored answer (#305).
6. System prompt: a new ticket-filing paragraph — admins can ask sudo to file a GitHub issue about anything noticed in the game; gather Q&A style like artifact work (a clear title; a body saying what/where/when — thin is correct, the operator's own filings are thin by doctrine; don't pad, don't speculate); read the complete draft back and file only on an explicit yes; after filing, the receipt with the issue number renders automatically — never restate a number from memory; if filing is disabled, say so plainly.

---

## §10 Verification

**Game-side (all must pass before any issue closes):**

1. `make build`, then the in-container suite — the only working form: `python manage.py test apps/shyland/tests` via `docker exec` in the django container. **All green; total strictly greater than 877** (the 15 new tests of §5/§6 at minimum); no pre-existing test edited except as this brief specifies (none are).
2. `make deploy-dev` once implementation and tests pass.

**Bot-side proof (deterministic, on dev, no model required where possible):**

3. **Singleton drill:** start the dev bot from the worktree (`agents/botctl.py dev start`); attempt a second attach as `agent-sudo` (e.g. `agents/mc_door_agent.py` with the agent-sudo credentials) — expect the `already-attached` error frame and close 4409; confirm the bot's own log shows nothing (its connection was untouched) and `~/.shyland/.sudo_bot.dev.pid` exists. Stop the bot; re-run the second client — admitted.
4. **Central directory:** after the drill, confirm pid/log/convo files exist under `~/.shyland/` and none were created under the worktree's `agents/`.
5. **Store receipts:** drive one action turn (the scripted/stub-brain driver pattern of prior releases), then read the dev conversation JSON and confirm the recorded answer carries the `[did: …]` line(s).
6. **Filing refusal path:** with no `GITHUB_TOKEN` in the bot's environment, drive a `file_issue` tool call (stub driver) — expect the `not-configured` error result and a legible model-side decline. **Verification never files a real issue** — the live filing is the playtest's, operator-driven, exactly once.
7. **Report rendering:** drive `report` kind `waypoints` and `memories` against a seeded store and confirm the pane lines land exactly as §6's table specifies (the driver's captured `player_message` frames).

**Issue closing (gated on 1–7):** close #301, #304, #305, #306 with comments naming this brief and the verifying commit.

---

## §11 Operator playtest checklist (dev stack)

*Prerequisite (operator, bot host): create `agents/.secrets/github-token.sudo` — a GitHub token able to create issues on `KnightOfNight/games-mvc` (fine-grained PAT, Issues read/write, this repo only). Named here; its value is never typed into the game, the session, or any log.*

*Transition step first: stop any running dev bot **from the checkout that started it** (its old botctl still sees its old pidfile). Then start the dev bot from this worktree.*

1. **Singleton, for real:** with the worktree dev bot running, try starting a dev bot from the main checkout (old code). Expect: it connects and is refused at the door; the pane never double-answers a `sudo` command; the old-code bot logs a close (code 4409, message generic under old code) and retries quietly. Stop it. — *the 25.9 incident, replayed against the fix.*
2. **Deterministic listings:** teach a waypoint or two if the store is empty, then: `sudo what waypoints do you know` → a `sudo:` leader plus one `#id name — Zone: Area: Room` line per waypoint, identical format every time you ask; `sudo show me memory <id>` → the detail block; `sudo what do you remember` → the mixed listing. Ask twice; the format must not drift.
3. **Receipts in the thread:** `sudo give <character> a <something>` (the bot's own gift path — items generated server-side), see the `sudo did:` line; then ask `sudo what did you do for me earlier` — the answer should reflect the confirmed action (its history now carries the `[did: …]` line).
4. **Poison immunity:** restart the dev bot (worktree botctl), then re-ask about or re-teach the same names from step 2/3 — no "already done" refusals from replayed prose; a re-teach calls `remember` and receipts it.
5. **File a real ticket:** `sudo file a ticket about <a real or throwaway finding>` — answer its questions, hear the full draft read back, say yes. Expect the `sudo did: filed issue #N: <url>` receipt; open the issue on GitHub and confirm title, body, the provenance footer naming your character, assignee KnightOfNight, and **no labels**. (The issue is real — keep or close it as you see fit.) Also try: decline a draft ("no, drop it") — nothing files; and note filing refuses legibly if the token file is absent.
6. **Kill switch sanity:** `mc kill` severs the bot as always (4503 precedence intact); `mc restore` and it reattaches unaided.

---

## §12 Architecture doc (LAST, gated)

This step is gated on all implementation and verification steps above being complete and passing.

`docs/shyland/Shyland_Architecture_v25.md`, updated in place (point-release rule): stamp to **25.10**; **the header hash moves** (architectural changes: a new consumer-level invariant, new door report kinds, a new bot capability, the bot runtime relocation). A new Version 25.10 paragraph in the header block (the established per-release form), and section updates:

- **§4.20 (the MC egress)** — the attach singleton: the `ATTACHED` registry, gate order, 4409, guarded release, the in-process rationale and freed-slot guarantee.
- **§4.22 (the agent door)** — `REPORT_KINDS` × 4 and the per-kind composition/result shapes; title line gains the v25.10 reference.
- **§4.23 (the sudo bot)** — `file_issue` (BOT_ACTIONS, the local execution branch, token custody, receipt), the store's `[did: …]` persistence, `RUNTIME_DIR`, the 4409 close meaning, prompt additions.
- **§4.24 (botctl)** — RUNTIME_DIR paths, the github-token injection, what stays checkout-scoped.

---

## §13 Closeout

- Complete the Step 0 stub in place: deviations, the transition note (§7.4), suite count, final commit hash, and the **operator playtest disposition** (verbatim-style, #170).
- **PENDING DEPLOY-TIME ACTIONS: none.** No migration (no model change), no seed, no prod-side data action. Two operator-side notes for the record, neither a deploy-time block: (a) prod bot restart after the eventual prod deploy is the operator's standing action — the restarted bot must be started with post-25.10 code so its state files land in `~/.shyland/`; (b) prod filing needs `agents/.secrets/github-token.sudo` on the bot host (executor: **explicitly the operator**), any time before first use.
- End with the `implementation-session-end` ritual (playtest disposition first, issues report last, as always).
