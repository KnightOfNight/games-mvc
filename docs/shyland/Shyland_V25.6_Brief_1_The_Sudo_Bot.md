# Shyland V25.6 — Brief 1: The Sudo Bot

**Release:** Version 25.6 (milestone: #262 founding · #279, #284 dependencies)
**Branch:** `version_25_6` (worktree; operator supplies the name at session start)
**Written:** 2026-08-23, V25.6 design session. Committed to the version branch per Rule 4.
**Technical coherence (#252):** every structural claim in this brief about existing code was verified against the code at writing time, in this design session, on this branch (tip 3bee92f at verification time). The Verified-Claims Ledger (§12) records each claim and its source location. Recall was not used as a source.

## 1. What this brief builds

The first live MC actor: **the sudo bot** — the AI watcher on the receiving end of `sudo` (#262). The game side is already complete: the agent door (v25.5, #281) ships the tail/query/action vocabularies, the `answer` delivery gate, the outfit snapshot, the kill switch (v25.4, #266), and the reserved bot names. This brief builds the **bot side**: a standalone Python process in the repo's `agents/` directory that tails the MC stream for admin `sudo` commands, parses them with a Claude model behind a provider-agnostic brain interface, acts through the door, and answers in sudo's voice. Plus two riders: the #284 nginx login-burst tune (shared surface, operator-acknowledged) and closing out #279's formalization.

**Game-side code changes in this release are deliberately tiny:** the version constant, one nginx template line, and one gitignore line. The bot is not part of the Django image and never will be — it is a remote client, exactly like a player's browser.

## 2. Design rules — do not deviate

All ruled on #262/#261/#268/#259 (2026-08-17 → 2026-08-23); this section is the binding summary.

1. **sudo ships whole** — voice AND fulfillment. No voice-only fallback scope cut.
2. **Silence is never an error.** Bot not running, unable to parse, killed, or declining → the admin sees exactly the v22 game: echo, then nothing. No error states ever surface in the pane from the bot's side.
3. **The model never touches the game.** AI is used for human-language parsing and composition only. Every world effect is a door action the bot sends and the server validates; every one is on the MC record. The model's tool calls are proposals; the bot is the executor.
4. **Provider-agnostic brain.** v1 = Claude via the official `anthropic` SDK; the interface must allow an Ollama-hosted model to swap in by configuration later. Model ID is configuration, **default `claude-sonnet-5`**, never hardcoded outside config.
5. **Scope tiers:** knowledge (game-state questions) and item/movement powers (gift, artifact create+gift, strip, dress, move) are in; **ops powers are excluded by design** — the bot must have no capability outside the door vocabulary.
6. **Decline model — no per-command conditionals.** The bot fetches the live verb list through `query commands` at attach. A request that maps to an existing command (admin or player) → decline in the "you don't need sudo for that" shape. A request the bot can't map to a door capability → the general "I don't know how to do that" shape. Wording of both is authored at implementation time (creative-content policy); the *mechanism* (live list, no hardcoded command names) is the rule.
7. **Conversation state lives in the bot** — bounded, local file, never in the game's DB/Redis/client. Abandoned multi-turn exchanges (e.g. an artifact Q&A) **time out quietly**; an expired conversation is indistinguishable from the bot never answering. Structure should be reusable by future bots.
8. **Kill-switch integration (standing actor invariant, GDD §10.11):** the bot's actuation is checked game-side — the door refuses/severs with close code 4503 when killed. The bot's degraded behavior is **silent patient retry**: on any disconnect it reconnects with backoff and keeps retrying quietly on repeated 4503 (killed is an expected, indefinite state, not an error). No pane output, no crash, no log spam beyond one line per attempt cycle.
9. **Rate/cost posture v1:** the admin-only audience is the bound; no technical rate limiter. The bot logs each model request's token usage (from the API response's `usage` fields). A per-request `max_tokens` cap applies (config, default below).
10. **Login once, reuse the session cookie across WebSocket reconnects** (#284's bot-side mitigation) — never re-authenticate per reconnect attempt unless the cookie is actually rejected.
11. **Secrets law:** the model API key and the `agent-sudo` game password are named env vars / files under `agents/.secrets/` — never committed (already gitignored), never printed, never logged.

## 3. Step 0 (standing)

Verify this brief exists verbatim at the branch tip; create the closeout-report stub (`.txt`, one-line session-start record), commit, **push immediately**. Complete the stub in place at closeout.

## 4. Step 1 — version constant (opening act)

First implementation brief of the release: bump `SHYLAND_VERSION` from `"25.5"` to `"25.6-DEV"` in its own commit, moving the pin test in the same commit, then run the version-start `make deploy-dev` from the worktree.

- Constant: `django/src/apps/shyland/version.py` line 8 — `SHYLAND_VERSION = "25.5"` *(confirmed against the file)*.
- Pin test: `django/src/apps/shyland/tests/test_b2_amendment1.py` line 118 — `self.assertEqual(SHYLAND_VERSION, '25.5')` *(confirmed)*.

## 5. Step 2 — the bot: `agents/sudo_bot.py`

One new file, plain Python 3, standard library plus `requests`, `websockets`, and `anthropic`. Single-file v1 is deliberate (matches the harness style already in `agents/`); a package split is future work if a second bot demands it.

### 5.1 Configuration surface

CLI arguments with environment fallbacks; all defaults exactly as stated:

| Knob | Default | Notes |
|---|---|---|
| `--url` | (required) | Base URL, e.g. `https://localhost:40443` |
| `--username` | `agent-sudo` | The bot's service account |
| `--password-file` | `agents/.secrets/agent-sudo` | One-line password file; never printed |
| `--insecure` | off | Accept self-signed certs (dev stack only) |
| `--log` | `agents/sudo_bot.log` | Append; gitignored (existing `*.log` rule) |
| `--model` | `claude-sonnet-5` | Passed to the brain; env `SUDO_BOT_MODEL` |
| `--brain` | `claude` | Provider selector (`claude` \| `stub`; `ollama` reserved) |
| `--max-tokens` | `1000` | Per model request |
| `--convo-timeout` | `600` (seconds) | Quiet conversation expiry |
| `--history-max` | `20` | Max retained exchanges per admin conversation |
| API key | env `ANTHROPIC_API_KEY` | Required for `--brain claude`; name only, never echoed |

Subcommands: `run` (foreground; the operator detaches with `nohup ... &` — document the exact line in the module docstring), `status`, `stop`. `status`/`stop` work through a pidfile `agents/.sudo_bot.pid`; **add `*.pid` to `agents/.gitignore`**.

### 5.2 Auth + connect *(all confirmed against `agents/mc_door_agent.py` and `mc_consumer.py`)*

Reuse the proven flow from `agents/mc_door_agent.py`: GET `/accounts/login/` for the CSRF token, POST credentials, carry the session cookie into the WebSocket handshake to `wss://<host>/ws/shyland/mc/`. On connect the server sends `{"type": "hello", "protocol": 2}` (`MC_PROTOCOL = 2`, `mc_consumer.py:40`); the bot must verify `protocol == 2` and refuse to run otherwise. Close codes: **4403** not authorized, **4503** killed. Per rule 2.10, the session cookie is obtained once and reused across reconnects; re-login only when the handshake is refused as unauthenticated.

### 5.3 The wire protocol the bot speaks *(confirmed against `mc_consumer.py`)*

- **Attach:** send `{"type": "attach"}` (bare — live-from-now; the bot never needs replay). Event frames arrive as `{"type": "event", "id", "kind", "actor_id", "actor_name", "room_id", "audience", "data"}`.
- **Requests:** `{"type": "query", "id": "<unique str ≤64>", "q": "<kind>", "params": {...}}` and `{"type": "action", "id": ..., "act": "<kind>", "params": {...}}` → one `{"type": "result", "id", "ok", "data" | "error" (+ "detail")}` each. Frames are processed serially per connection — the bot may simply await each result in order.
- **Keepalive:** `{"type": "ping"}` → `{"type": "pong"}` (optional `nonce` echoed).
- Error codes the bot must tolerate gracefully (map to a polite reply or silence, never a crash): `bad-frame`, `unknown-query`, `unknown-action`, `bad-params`, `not-found`, `not-admin`, `invalid-item`, `artifact-requires-create`, `name-taken`, `nothing-equipped`, `no-outfit`, `in-combat`, `internal` *(the complete `DoorError` code set, confirmed against `mc_door.py`)*.

### 5.4 Trigger: spotting a sudo command on the stream *(confirmed against `consumers.py:675–686`)*

A submitted command emits one `cmd` record: `data = {"raw": <full line>, "verb": <first token lowercased>, "args": <remainder or "">}`, with `actor_id` = character pk and `actor_name` = character name (`_mc_actor`, `consumers.py:438–441`). The bot reacts to event frames where `kind == "cmd"` and `data.verb == "sudo"` and `data.args` is non-empty; `data.args` is the request text; `actor_name` is the requesting admin's character name. (`cmd_sudo` itself remains a silent no-op game-side, `consumers.py:3302` — unchanged by this brief.)

Before invoking the model, the bot pre-checks `query is_admin {"name": <actor_name>}` and drops the request silently on `false` — a cost discipline only; the authoritative gate remains the door's `answer` action (`not-admin`), which the bot must also handle silently. (Game-side, `sudo` is already admin-gated, so this is defense in depth, not the security boundary.)

### 5.5 The brain interface

```python
class Brain:                                    # provider-agnostic
    def respond(self, system, history, tools) -> BrainTurn   # tool calls and/or text
```

Implementations: `ClaudeBrain` (v1, the `anthropic` SDK; model/max-tokens from config; **do not set temperature or other sampling parameters** — Sonnet 5 rejects non-default values; log `usage.input_tokens`/`usage.output_tokens` per request) and `StubBrain` (deterministic canned behavior for testing — §8). The tool-use loop lives in the **bot**, not the brain: brain returns tool calls → bot executes them as door frames → feeds results back → repeats (cap: 8 tool iterations per sudo request) → final text, if any, is delivered via `action answer {"to": <actor_name>, "text": ...}`. Answer text must respect the door's 2000-char limit (`MAX_ANSWER_LEN`, `mc_door.py:38`) — truncate with an ellipsis rather than draw `bad-params`.

**Tools presented to the model** = the door vocabulary minus `answer` (delivery is bot machinery, not a model choice): queries `commands`, `who_online`, `where_is`, `character`, `items`; actions `gift`, `create_artifact`, `strip`, `dress`, `move`. Tool schemas mirror the door's param shapes exactly *(confirmed against `mc_door.py` — `QUERY_HANDLERS`/`ACTION_HANDLERS` and each handler's params, including `create_artifact`'s full spec table: name/item_type/description/genre_tag/mk_tier/base_value/valid_slots/is_two_handed/damage keys for weapons only/armor_base for armor only/primary+secondary stat entries/unidentifiable+mystery pair)*. The system prompt carries: sudo's persona and the design rules above (decline shapes, silence option, in-game-only scope), plus the live verb list fetched via `query commands` at attach (`verbs` + `admin_verbs`, confirmed shape).

### 5.6 Conversations

Keyed by admin `actor_name`. Each holds up to `--history-max` exchanges; on every new sudo request, expire the conversation if idle past `--convo-timeout` (fresh start, no comment about the expiry). Persist to a local JSON file under `agents/` (gitignored — add its name to `agents/.gitignore` alongside the pid entry) so a bot restart doesn't drop a live artifact Q&A mid-design. Multi-turn Q&A needs no special machinery: the model's answer asks the next question; the next `sudo` from that admin continues the same conversation.

### 5.7 Lifecycle

`run`: login → connect → verify hello → `query commands` → attach → event loop, with periodic pings on idle. On any disconnect: reconnect with capped exponential backoff (base 2s, cap 60s), reusing the cookie. On 4503 specifically: same loop, one log line per attempt — killed is an expected indefinite state (rule 2.8). SIGTERM: clean close, persist conversations, remove pidfile.

## 6. Step 3 — dependencies

Add `anthropic` to `agents/requirements.txt` (the file's own comment already anticipates this). Operator-side venv install (`venvs/mc-agent` or a fresh venv per the file's instructions) is directed by this brief — the implementation session states the exact command in-session and the operator runs or approves it; nothing installs into the repo or the Django image.

## 7. Step 4 — #284: nginx login burst (shared surface — operator-acknowledged 2026-08-23)

In `nginx/conf/default.conf.template`, the `location /accounts/login/` block *(confirmed: currently `limit_req zone=login burst=3 nodelay;`)*: change `burst=3` → `burst=10`. Rate stays 5r/m (`rate-limit.conf` untouched); django-defender untouched. **Shared surface:** nginx fronts all three games; the change reaches dev with this brief's `make deploy-dev` and production with the ordinary 25.6 closeout deploy — no separate deploy-time action.

## 8. Step 5 — dev-side provisioning + verification

**Dev provisioning (in-session, dev stack only):** create the `agent-sudo` Django user via `make shell` (set a password the operator supplies into `agents/.secrets/agent-sudo`; never echo it), add it to the `agents.shyland` group. No `Character` — bots are never characters. (`RESERVED_BOT_NAMES` already reserves `sudo`/`sirius` at creation — `models.py:242`, shipped v25.5; no change here.)

**Verification (all must pass before any issue closes or `git push` of the completion commit):**

1. Full in-container suite green: `python manage.py test apps/shyland/tests` (directory-path form via `docker exec`, the only working invocation). Invariant: no test count regression from the branch's baseline; the pin test passes at `25.6-DEV`.
2. `git check-ignore agents/.secrets/agent-sudo` succeeds; `git status` shows no secrets, no pidfile, no log, no conversation file.
3. **Stub-brain end-to-end against the dev stack** (deterministic, no model, no API key): run `sudo_bot.py run --brain stub`; from an admin character in the browser or via the play client, issue a `sudo` request the stub maps to a canned `where_is` + answer. Confirm: the bot's log shows the cmd record spotted, `is_admin` pre-check, door round trip, and `answer` delivered `{"delivered": true}`; the admin's pane shows the `sudo: ...` line in sudo-color. This proves the entire pipeline minus the model.
4. Kill-switch drill with the stub: `mc kill` in-game → bot log shows 4503 and quiet retry; `mc restore` → bot reattaches unaided; a fresh sudo request round-trips.

## 9. In-session dev deploy + operator playtest checklist (dev stack)

Run `make deploy-dev` once implementation and verification pass (this also carries the nginx burst change to dev). Then, with the bot running under `--brain claude` (real model):

1. `sudo where is <player>` → an answer in sudo's voice/color, correct room.
2. `sudo who is online` → correct roster.
3. `sudo give <player> a <existing item>, mk 1, uncommon` → recipient sees the loot-color giving line; sudo confirms; item in inventory.
4. `sudo let's talk about a new artifact, a sword` → multi-turn Q&A (recipient, stats, Mk, name, lore) → artifact created and gifted; recipient line lands; `examine` shows the authored artifact.
5. `sudo strip <name>` then `sudo dress <name>` → gear off to inventory with the system line, then restored exactly.
6. `sudo move <playerA> to <playerB>` → arrival/departure narration in the world's colors; `An admin moved you to a new room.` to the moved player.
7. `sudo mc kill` (or another existing admin command) → the "you don't need sudo for that" decline shape.
8. `sudo wall hello everyone` → the "I don't know how to do that" decline shape (`wall` is #236, unshipped — nothing hardcoded about it).
9. `mc kill` → sudo goes silent mid-conversation (no errors anywhere); `mc restore` → sudo recovers without a bot restart.
10. Artifact Q&A abandoned past the timeout → next `sudo` starts fresh, no mention of the old thread.
11. (Optional, the #268 posture check) From a Claude Code session on the bot host: `status`, tail the log, `stop`, restart — bot health fully manageable without SSH.

## 10. Issues, architecture doc, closeout

- **Close #262, #279, #284** — gated on §8 verification passing and the playtest disposition. (#279 closes on confirming the in-repo scripts run against dev; #284 on the nginx change verified on dev.)
- **Architecture doc (last, gated):** this step is gated on all implementation and verification steps above being complete and passing. Update `Shyland_Architecture_v25.md` in place: stamp → 25.6; **the hash moves** (a new top-level component is architectural). Sections: the MC/agent-door section gains the bot-side counterpart (the `agents/` home, the bot process shape, brain interface, conversation store, reconnect/kill behavior); the deployment/nginx section notes the login burst change.
- **Closeout report** (`.txt`, completed in place): final commit hash; deviations; the **operator playtest disposition** verbatim-style; and this block:

  **PENDING DEPLOY-TIME ACTIONS**
  - Production `agent-sudo` account provisioning (create user, set password, join `agents.shyland`) — **executor: the operator**, in the closeout tail's deploy window (the release's prod attach window). No seed, no migration; a human act by design.
  - (The nginx burst change needs no separate action — it rides the ordinary prod deploy bounce.)

## 11. Out of scope (deliberate)

Per-agent `answer` scopes (#282 — future arc), Sirius (#259), NPC responders (#265), pets (#263), process supervision/auto-restart (#268 later slice), Ollama implementation (interface only), any game-side command changes (the dispatch table is untouched), #283's greeting perspective fix.

## 12. Verified-Claims Ledger (#252)

| Claim | Verified at |
|---|---|
| `SHYLAND_VERSION = "25.5"` | `django/src/apps/shyland/version.py:8` |
| Pin test asserts `'25.5'` | `django/src/apps/shyland/tests/test_b2_amendment1.py:118` |
| `MC_PROTOCOL = 2`; hello/attach/ping/query/action/result/event/gap frame shapes; serial per-connection processing; 4403/4503; kill-switch per-frame check | `django/src/apps/shyland/mc_consumer.py` (whole file read) |
| Query kinds `commands, who_online, where_is, character, items, is_admin`; action kinds `answer, gift, create_artifact, strip, dress, move`; all param shapes; `MAX_ANSWER_LEN = 2000`; full `DoorError` code set; artifact spec table; capacity deliberately unchecked on gift; strip bypasses the unequip guard by ruling | `django/src/apps/shyland/mc_door.py` (whole file read) |
| `cmd` record `data={'raw','verb','args'}`; `actor_name` = character name (`_mc_actor`); `cmd_sudo` silent no-op | `django/src/apps/shyland/consumers.py:665–686, 438–441, 3302` |
| Login flow (CSRF GET → POST → cookie into WSS handshake) | `agents/mc_door_agent.py` module docstring + `#279` spec |
| nginx login block currently `burst=3` | `nginx/conf/default.conf.template:28` |
| `RESERVED_BOT_NAMES = frozenset({'sudo', 'sirius'})` | `django/src/apps/shyland/models.py:242` |
| `agents/requirements.txt` anticipates `anthropic`; `agents/.gitignore` covers `.secrets/`, `venvs/`, `*.log` | `agents/` (authored this session, 9f64cf5) |

*Self-consistency: this brief was read end-to-end after writing; the config table (§5.1) is authoritative where prose and table could disagree.*
