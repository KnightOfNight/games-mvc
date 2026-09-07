# Shyland V25.17 — Brief 1: Legible Bot Failure Reporting

- **Release:** Version 25.17 (point release) — milestone `Version 25.17`
- **Branch:** `version_25_17`
- **Founding ticket:** #326 (sole milestone member — scope law: one founding ticket, one brief)
- **Authored:** 2026-09-07, V25.17 design session
- **Session type to apply this brief:** implementation session on `version_25_17`

## 1. What this release does

Found during the V25.16 Brief 1 playtest: the Anthropic API refused the sudo bot's model calls with a billing error (`400 invalid_request_error: credit balance is too low`). The bot handled it as designed — caught per request, logged `sudo request from <name> failed silently` with the traceback, stayed attached — but the requesting admin got nothing in the pane. From the player side this is indistinguishable from the bot being down; the operator diagnosed it only from the host-side log.

**Operator ruling (2026-09-07, recorded on #326):** no more silent failure from the bot unless it is not running at all. When the bot is up and an admin's request **terminally fails** — model API error, billing, auth, whatever — the admin gets **exactly one legible in-pane line**, delivered through the door's shipped `answer` action in sudo's voice (error-color talking color, per #262), naming the failure **class** and never the raw API detail (which stays in the host-side log). Two classes, ruled coarse deliberately: **transient** (worth trying again) and **persistent** (billing, auth — retrying won't help; the operator's attention is required). A transient error that succeeds on retry stays quiet — the answer arriving is the report. The silence doctrine survives intact for reconnect/kill-switch states and model-chosen silence (#308's exemption untouched); and the report attempt itself never escalates — if delivery fails too (a dead door connection is the usual cause), the bot logs and stays quiet, which is the not-running case the rule exempts.

GDD text landed with the design session (§10 "A failed request is never silent" paragraph — commit 29c3b45, marker to be swept at closeout). Implementation never touches GDD source.

## 2. Technical premises — verified at writing time

Per the technical-coherence rule (#252), every claim below was **confirmed by file-read against `version_25_17` @ 29c3b45** (code identical to the 25.16 merge tip a48f639 — the branch's only commit is the GDD edit) during the authoring session. The implementation session's pre-flight re-diffs these against the code before writing anything; a load-bearing mismatch is a HARD STOP.

1. **The silent-failure choke point** — `agents/sudo_bot.py`, `SudoBot._worker` (1453–1475): consumes tail events, filters to `cmd` frames with `verb == 'sudo'` and non-empty args and a non-empty `actor_name`, then wraps `await self._handle_sudo(actor_name, data['args'])` in `except asyncio.CancelledError: raise` / `except Exception:` — the latter logging `log.warning('sudo request from %s failed silently', actor_name, exc_info=True)` (1474) and telling no one. **Every terminal per-request failure funnels here**; there is no other catch between `_handle_sudo`'s body and the worker loop.
2. **The model call** — `_handle_sudo` calls `await asyncio.to_thread(self.brain.respond, self.system_prompt, history, TOOLS)` (1507–1508) inside its tool loop. `ClaudeBrain.respond` (1219–1237) calls `self._client.messages.create(...)` with no exception handling of its own — SDK exceptions propagate straight to premise 1's catch-all.
3. **The SDK's retry/exception surface** (verified against the installed `anthropic` 1.0.0 in `agents/venvs/mc-agent`): `anthropic.Anthropic()` defaults to `max_retries=2`; `_should_retry` retries 408/409/429/5xx (and connection errors) only — **400/401/403 raise immediately**. HTTP-status failures raise `APIStatusError` subclasses carrying **`.status_code`**; `APIConnectionError` (post-retry connection failure) has **no** `status_code` attribute. So by the time an exception reaches premise 1, the SDK's own transient retries are already spent — every arriving exception is terminal for this request.
4. **`ClaudeBrain.__init__` (1210–1217) checks only that `ANTHROPIC_API_KEY` is *set*, never that it is valid** — a bot started with a bad key attaches cleanly and fails on the first model call (the playtest lever, §6).
5. **The deferred-import rule** — the `anthropic` import lives inside `ClaudeBrain.__init__` (1214); `--brain stub` runs without the package (module docstring, 41–42). The classification therefore must not import `anthropic` at module level (design rule §3).
6. **Delivery** — `_deliver(actor_name, text, receipts=None)` (1795–1817): strips model-written `sudo:` prefixes, truncates at `MAX_ANSWER_LEN` (2000, constant at 87), sends door `action answer` with `{'to': actor_name, 'text': ...}` via `door_request`, logs delivered/refused, **and does not raise on a door refusal** (ok=False is logged, 1814–1817) — but `door_request` itself (1413–1427) can raise (`asyncio.wait_for(future, DOOR_TIMEOUT)` → `TimeoutError`, or a websocket send error on a dead connection), so a failure-report call into `_deliver` must be exception-wrapped (design rule §3).
7. **The `answer` gate is server-side and authoritative** — the `is_admin` pre-check in `_handle_sudo` (1479–1487) is cost discipline only (its own comment); the door's `answer` action enforces admins-only delivery (#273). Attempting a failure report is therefore always safe: a non-admin target is refused server-side. Today, when the pre-check **query itself fails** (`result.get('ok')` false), the code treats it as not-admin and returns silently (1482–1487) — a failed request the machinery knows about, in scope per the ruling (§4.3).
8. **The dev bot's runtime surface** — `agents/botctl.py`: CLI is `botctl.py <target> <command>` with `target ∈ {dev, prod}`, `command ∈ {start, stop, restart, status, tail}`, `--bot` default `sudo` (243–262). The child environment is `dict(os.environ)` plus `ANTHROPIC_API_KEY` read from `agents/.secrets/anthropic-api-key.<name>` (81, 157–159) — so an env var exported in the invoking shell (e.g. `ANTHROPIC_BASE_URL`) reaches the bot process, and the key file's contents are the key the bot uses. The anthropic SDK reads `ANTHROPIC_BASE_URL` from the environment when set (client construction, premise 3's SDK).
9. **Change-surface precedent (v25.11, #308)** — a pure bot-side release: change surface `agents/sudo_bot.py` only (host-side; nothing in the Docker image beyond the version stamp); **no new in-suite tests — the suite cannot see `agents/`**; behavior proven by the scripted-brain driver pattern over the real dev door (precedent v25.9/v25.10); **no header-hash move** (25.11's changelog entry carries no hash-move sentence; the hash names architectural — game-side — change only).
10. **Suite baseline:** 954 in-container tests green at the 25.16 closeout. This brief expects the count to stay 954 with zero existing-test changes.
11. **The conversation store records nothing on a failed request** — `self.convos.record(...)` runs at the end of `_handle_sudo` (1594); an exception before that point persists no exchange. This brief leaves that behavior unchanged (design rule §3).

## 3. Design rules — do not deviate

- **The two pane lines are fixed strings** (the door prepends `sudo: `; error-color voice is the shipped #262 rendering — no game-side change):
  - Transient: `Your request failed — a temporary problem reaching the model. Try again.`
  - Persistent: `Your request failed — the model service refused; this needs the operator's attention.`
- **Classification is duck-typed and provider-agnostic:** class keys on `getattr(exc, 'status_code', None)` — a status of **400, 401, or 403 ⇒ persistent; anything else, including no status at all ⇒ transient**. No `anthropic` import anywhere at module level (premise 5); no exception-type dispatch. This survives the future Ollama brain unchanged.
- **One line per failed request, to the requesting admin only.** Never broadcast, never repeated, never queued for later.
- **The report path never raises.** The classify-and-report step wraps its delivery attempt; on any exception it logs and stays quiet (the exempted bot-effectively-down case). `asyncio.CancelledError` handling in `_worker` stays first and re-raises, byte-identical.
- **Raw detail never reaches the pane.** The exception class/status/traceback stay in the log (existing `exc_info=True` behavior); the pane gets the fixed class line only. No secrets, account, or billing detail in any delivered text.
- **Silence stays sanctioned where it is ruled:** model-chosen silence (no text, no receipts), the not-admin drop, abandoned-conversation expiry, and reconnect/kill-switch states are all untouched. Only the premise-1 catch-all (and the premise-7 pre-check query failure) gain a voice.
- **No new door vocabulary, no game-side code change, no consumer change, no migration, no seed change.** The Docker image changes only by the version stamp (4.1).
- **The conversation store stays out of it** (premise 11): a failed request persists no exchange; the failure line is delivery-only.

## 4. Implementation steps

Commit and push at every step boundary (branch only — never merge). Step 0 (closeout-report stub push) is owned by the `implementation-session` start ritual.

### 4.1 Version start (opening act — first brief of the release)

Bump `SHYLAND_VERSION` to `"25.17-DEV"` (`django/src/apps/shyland/version.py:8`) in its own commit, moving the pin-test assertion (in `tests/test_b2_amendment1.py`) in the same commit. Then run the version-start `make deploy-dev` from the worktree.

### 4.2 Classification + the fixed lines

In `agents/sudo_bot.py`, near the other module constants: the two line constants (`FAILURE_LINE_TRANSIENT`, `FAILURE_LINE_PERSISTENT`, exact strings from §3), `PERSISTENT_STATUS_CODES = frozenset({400, 401, 403})`, and a module-level pure function `classify_failure(exc)` returning `'persistent'` when `getattr(exc, 'status_code', None)` is in the set, else `'transient'`. Pure and import-free so it is trivially provable from the venv (§5).

### 4.3 The report path

- **`_worker`:** in the `except Exception:` branch, replace the `failed silently` log line with one that names the class (e.g. `sudo request from %s failed (%s) — reporting to the admin`, still `exc_info=True`, UTC-Z stamps unchanged), then `await self._report_failure(actor_name, exc)`.
- **New method `_report_failure(self, actor_name, exc)`:** picks the line by `classify_failure(exc)` and calls `await self._deliver(actor_name, line)` inside its own `try/except Exception`: on any exception, one log line (report delivery failed — staying quiet) and return. Nothing propagates.
- **The pre-check query failure (premise 7):** in `_handle_sudo`, when the `is_admin` result has `ok` false (as opposed to a genuine `is_admin: false`), raise a new module-level `class RequestFailed(Exception)` instead of returning silently — routing it through the same choke point (no status code ⇒ transient; the door's `answer` gate still protects delivery if admin-ness is genuinely in doubt). A genuine non-admin (`ok` true, `is_admin` false) still returns silently, byte-identical.

### 4.4 Scripted proof over the dev door (the v25.9/v25.10/v25.11 driver pattern)

A throwaway raising-brain driver (not committed; the 25.11 precedent): run the bot against the dev stack with a brain whose `respond` raises (a) a stub exception carrying `status_code = 401` and (b) a plain `RuntimeError`, issuing one in-game `sudo` request per case, and confirm in-pane: the persistent line for (a), the transient line for (b), one line each, `sudo: `-prefixed in sudo's voice. Confirm the log carries the classed warning with traceback both times. (The chaos-monkey runs in §6 then prove the same end-to-end with the real `ClaudeBrain`.)

### 4.5 Dev deploy + issue close

`make deploy-dev` from the worktree (the stamp is the only image change; the bot code change takes effect on the dev bot restart in §6). Close #326 gated on §5 passing, with a closing comment naming the release and the shipped shape.

### 4.6 Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. `docs/shyland/Shyland_Architecture_v25.md`, updated in place per the point-release document rule:

- New changelog entry (`> **Version 25.17 (point release) — Brief 1 applied on branch `version_25_17`: ...**`) after the header, before the 25.16 entry — covering the ruling, the two classes and fixed lines, the duck-typed classification, the `RequestFailed` routing of pre-check query failures, the never-raises report path, and the change-surface sentence (bot-side only; nothing in the Docker image beyond the version stamp; no new in-suite tests — the suite cannot see `agents/`; suite steady at 954).
- **§4.23 (the sudo bot):** append the release to the section title line, and amend the silence prose — the "Reconnect and the kill switch" paragraph's closing sentence ("silence is never an error, in every failure mode") gains the carve-out: reconnect/kill-switch states stay silent; a terminally failed live request now speaks one classed line.
- **Stamp moves to 25.17; the header hash does NOT move** (no architectural change — the 25.11 precedent, premise 9).

### 4.7 Closeout report

Complete the Step-0 stub in place: final commit hash, deviations (expected: none), §5 results, actual-vs-expected on everything numbered, and the operator playtest disposition line (#170).

## 5. Verification

1. **Classification proof (pure):** from `agents/venvs/mc-agent/bin/python`, drive `classify_failure` with stub objects — `status_code` 400/401/403 ⇒ `'persistent'`; 429, 500, `None`-status, and an attribute-free exception ⇒ `'transient'`. (Import `sudo_bot` directly; no game, no key needed — the module imports without `anthropic` by premise 5.)
2. **The §4.4 scripted-driver run passes** (both classes delivered in-pane, one line each, log carries the classed warning).
3. **No-regression:** with the stub brain (`--brain stub`), a normal request round-trips exactly as before (the report path is unreachable on success).
4. **In-container suite green, count 954, zero existing-test changes** (`python manage.py test apps/shyland/tests`, directory-path form via `docker exec`).
5. **Module import hygiene:** `grep -n 'import anthropic' agents/sudo_bot.py` still matches only inside `ClaudeBrain.__init__` — the deferred-import rule (premise 5) preserved; nothing this brief adds imports `anthropic` anywhere.

## 6. Operator playtest checklist (dev stack — chaos monkey by configuration, no code hacks)

After 4.5, restart the dev bot on the brief's code (`agents/botctl.py dev restart` from this worktree). Then:

1. **Baseline:** as an admin in-game, one normal `sudo` request → normal answer (no failure line, nothing new).
2. **Persistent class — the intentionally bad API key (operator-proposed lever):** stop the dev bot; replace the contents of `agents/.secrets/anthropic-api-key.sudo` with an obviously invalid string (operator's hands — never echo the real key); start the dev bot (it attaches cleanly — premise 4). Issue a `sudo` request → expect exactly one line: `sudo: Your request failed — the model service refused; this needs the operator's attention.` in sudo's error-color voice. Confirm the host-side log has the classed warning + traceback. Restore the real key file (operator's hands).
3. **Transient class — unreachable model endpoint:** with the real key restored, `ANTHROPIC_BASE_URL=http://127.0.0.1:1 ./agents/botctl.py dev restart` (the env var rides the child environment — premise 8; connection refused fails fast). Issue a `sudo` request → expect exactly one line: `sudo: Your request failed — a temporary problem reaching the model. Try again.` Confirm the log. Restart the bot normally (no env var) and confirm a normal request succeeds again.
4. **Silence still sanctioned:** with the healthy bot, issue a request the bot declines to answer (or let a thread expire) → no failure line appears.

## 7. PENDING DEPLOY-TIME ACTIONS

None. The bot is host-side; production takes the change when the operator restarts the **prod** bot on post-25.17 `main` code (a standing operator action, not a deploy-window step — same as every bot release since 25.10). No prod data actions, no seed, no verify command.

## 8. Explicitly out of scope

- Any change to the door's `answer` gate or per-agent scopes (#282 — deferred to Sirius' design session).
- Retry machinery beyond the SDK's built-in retries (no bot-side retry loop ships; the SDK's spent-retries surface is the terminality signal — premise 3).
- Finer failure taxonomy, model-error text passthrough, or pane detail of any kind (ruled out on #326).
- Conversation-store changes (premise 11), reconnect/kill-switch behavior, and the #308 bounce machinery — all byte-identical.
- The Django admin, game-side code, and every other bot (`mc_door_agent.py`, `mc_test_agent.py`) — untouched.
