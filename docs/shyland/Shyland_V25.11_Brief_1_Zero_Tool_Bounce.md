# Shyland V25.11 — Brief 1: The Zero-Tool Bounce

- **Release:** Version 25.11 (point release, V25 monitoring-and-command major)
- **Founding ticket:** #308 (sole milestone member; approach ruled on the issue 2026-08-30)
- **Branch:** `version_25_11`
- **Authored:** 2026-08-30, V25.11 design session. Every structural claim in §2 was verified against the code at writing time (#252); sources are cited per claim.

---

## §1 Context

V25.10 closed the **marked** fabrication: a would-be final answer carrying a `[did:]` mark with no receipt behind it bounces back into the tool loop, and any surviving model-written `[did:]` line is stripped before delivery and storage. Its own playtest then showed the **unmarked** sibling (observed twice, 2026-08-29): on a see-request (`sudo what do you remember`) the model intermittently answers with delivery-claim prose — *"Sent — full memory list delivered to your pane."* — on a turn with **zero tool calls**. Nothing delivers, and plain prose on a zero-tool turn has no machine-detectable signature. An immediate retry always works.

**The ruling (#308, operator-confirmed 2026-08-30): the zero-tool-turn bounce, single-shot.** When a nonempty would-be final answer arrives and no tool call has run at any point this turn, machinery bounces it once with a corrective message; the redo's answer is then delivered without a second bounce (the existing `[did:]` gates still apply on top). Signature-free — it closes the whole unmarked class, not the observed instances — and machinery stays dumb: no natural-language classification of requests moves bot-side. The accepted cost, ruled explicitly: every genuinely conversational turn (drafting Q&A, confirm-gate exchanges) draws exactly one extra model round trip. GDD §10.11 carries the doctrine paragraph ("The unmarked lie draws one redo"), marked pending implementation.

---

## §2 Verified current state (all confirmed against the `version_25_11` tip, a0223d7)

1. `agents/sudo_bot.py` constants: `TOOL_LOOP_CAP = 8` (line 93); `MAX_ANSWER_LEN = 2000` (line 87). *(Confirmed in the file.)*
2. **The tool loop** (`_handle_sudo`, lines 1379–1413): `for _ in range(TOOL_LOOP_CAP):` → `turn = await asyncio.to_thread(self.brain.respond, self.system_prompt, history, TOOLS)` → `final_text = turn.text` → `if not turn.tool_calls:` runs the **receiptless-`[did:]` redo gate** — when `'[did:' in final_text and not actions.receipts()`, it logs `rejected receiptless [did:] answer for %s — redo`, appends the assistant text plus a `[game]`-voice corrective user message to `history`, and `continue`s — else `break`. The tool-ful path appends `turn.raw_content` as the assistant turn, executes each call through `_execute_tool`, and appends the results list as one user turn. *(Confirmed in the file.)*
3. **Post-loop** (lines 1415–1445): `receipts = actions.receipts()`; the strip guard removes model-written `[did:]` lines from `final_text`; the stored answer folds genuine receipt lines in; `self.convos.record(...)`; delivery happens iff `final_text or receipts`, else the log records `model chose silence` — silence is sanctioned behavior. *(Confirmed in the file.)*
4. `BrainTurn` (lines 1075–1081): `.tool_calls` (list of `{'id','name','input'}`, default empty), `.text`, `.raw_content`. *(Confirmed in the file.)*
5. `StubBrain` (lines 1120–1151): a fresh request draws one canned `where_is` tool call; the canned final answer arrives on the *following* iteration, after that tool call executed. **Its zero-tool answer therefore always follows an executed tool call this turn — the new gate never fires on the stub's canned flow.** *(Confirmed in the file.)*
6. `SHYLAND_VERSION = "25.10"` at `django/src/apps/shyland/version.py:8`; the pin assertion at `django/src/apps/shyland/tests/test_b2_amendment1.py:118`. *(Confirmed in both files.)*
7. Suite baseline: **891 tests** green in-container at the 25.10 close. *(Source: `Shyland_Architecture_v25.md` Version 25.10 block, "Suite 877 → 891".)*
8. **The change surface is `agents/sudo_bot.py` only.** The bot is host-side plain Python run from the checkout via `agents/botctl.py` (runtime state in `~/.shyland/`); it is not baked into the Docker image. Game-side code, door vocabulary, models, client: untouched. `make deploy-dev` matters to this release only for the version stamp. *(Confirmed: architecture doc §4.23/§4.24.)*
9. No prior-version PENDING DEPLOY-TIME ACTIONS carry into 25.11 (the 25.10 closeout left only post-deploy operator standing actions, outside the pending-block mechanism).

---

## §3 Design rules — do not deviate

1. **Single-shot:** at most one zero-tool bounce per sudo request (one turn). After the one redo, the next answer is delivered regardless — subject only to the existing gates.
2. **Nonempty answers only.** A silent zero-tool turn (no text, no tool calls) is never bounced — model silence stays sanctioned exactly as today (§2.3).
3. **The condition is turn-scoped:** the bounce fires only when *no tool call has been executed at any point in the entire turn so far*. A turn where any tool call executed — success **or** error result — never bounces; an answer after a lookup is legitimate whether or not actions ran.
4. **Gate order:** the existing receiptless-`[did:]` gate is evaluated first and is unchanged (including its loop-capped, multi-fire behavior). The zero-tool gate applies only to answers that pass it. (A zero-tool answer carrying a `[did:]` mark necessarily has no receipts — the existing gate owns it.)
5. **Everything else is byte-identical:** the strip guard, receipt folding, store shape (`{'q','a'}`), delivery/silence rules, `_deliver`, `_execute_tool`, and `StubBrain` behavior (§2.5 — no stub edits needed or permitted).
6. The bounce consumes one `TOOL_LOOP_CAP` iteration; cap exhaustion falls through to the strip guard and delivery path exactly as today.

---

## §4 Implementation

1. **Version constant, opening act (own commit, standing law):** `django/src/apps/shyland/version.py:8` → `SHYLAND_VERSION = "25.11-DEV"`; the pin assertion at `tests/test_b2_amendment1.py:118` → `'25.11-DEV'` in the same commit. Then the version-start `make deploy-dev` from the worktree.
2. **The gate**, in `_handle_sudo` (`agents/sudo_bot.py`):
   - Two per-request locals initialized beside `ledger`/`actions` (names indicative, implementer's choice): `ran_tool = False`, `bounced = False`.
   - Set `ran_tool = True` on the tool-execution branch (i.e. whenever `turn.tool_calls` is non-empty and the calls are executed), regardless of result success (§3.3).
   - In the `if not turn.tool_calls:` branch, **after** the existing `[did:]` gate and before `break`:
     ```python
     if final_text and not ran_tool and not bounced:
         bounced = True
         log.info('zero-tool answer for %s — one corrective redo',
                  actor_name)
         history.append({'role': 'assistant', 'content': final_text})
         history.append({
             'role': 'user',
             'content': ('[game] Your answer made no tool call this '
                         'turn. If the request asks you to see or do '
                         'something, do it now with a tool call — '
                         'machinery reports only what it confirms. If '
                         'this was just conversation, answer as you '
                         'were.')})
         continue
     ```
     The corrective text above is the ruled wording — `[game]` register, mirroring the shipped gate at lines 1397–1404.
   - Code comment cites the release and ticket in the neighbors' style (`v25.11 (#308): ...`), stating the single-shot rule and that silence is deliberately exempt.
3. No other file changes (game-side or bot-side) beyond §5's pin edit and §7's architecture doc step.

---

## §5 Tests

**No new in-suite tests — a deliberate, recorded exception.** The django in-container suite cannot see `agents/` (host-side, outside the image); bot-loop machinery is proven by the scripted-brain driver pattern, precedent v25.9 and v25.10 (their closeout reports in `docs/shyland/` document the pattern). The suite's only edit is the pin literal (§4.1); expected total stays **891**, all green.

---

## §6 Verification

1. **Suite:** `make build`, then in-container — the only working form — `python manage.py test apps/shyland/tests` via `docker exec` in the django container. All green, total **891**, no pre-existing test edited except the pin literal.
2. **Scripted-brain driver over the real dev door** (the v25.9/v25.10 pattern: a `SudoBot` instance with a scripted brain, attached as **`agent-smith`** — the standing test agent, avoiding the dev sudo bot's 4409 singleton; the v25.10 closeout's driver notes apply, including the throwaway dev-credential precedent). Four cases, each asserted from the bot log, the model-history the driver can observe, and the captured pane/store where named:
   - **a. Unmarked fabrication:** first `respond` returns zero-tool prose (`Sent — delivered to your pane.`). Assert: the new log line fires (`zero-tool answer ... — one corrective redo`), the corrective `[game]` message enters history, and a second `respond` occurs. Scripted second turn performs a real query/action then answers. Assert: delivered, exactly one bounce.
   - **b. Conversational:** both `respond` calls return zero-tool plain prose (no claims). Assert: exactly one bounce; the second answer is delivered as-is; no second bounce.
   - **c. Marked regression:** first `respond` returns a zero-tool answer containing a `[did: ...]` line. Assert: the **existing** gate's log line (`rejected receiptless [did:] answer`) fires, not the new one.
   - **d. Tool-ful pass-through:** a `respond` with one query call, then a zero-tool prose answer. Assert: no bounce of either kind; delivered.
3. **`make deploy-dev`** once 1–2 pass (standing requirement; carries the version stamp).
4. **Restart the dev bot on worktree code** (`agents/botctl.py`, dev target) so the playtest exercises the gate with the real brain; confirm the startup log line.

---

## §7 Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. `docs/shyland/Shyland_Architecture_v25.md`, updated in place per the point-release rule:

- Header stamp 25.10 → 25.11; a new `Version 25.11` block in the header's version list; **the hash moves** (architectural change: a new bot-machinery gate layer).
- §4.23 (the sudo bot): heading line gains `v25.11 brief 1, #308`; body gains the zero-tool bounce — condition, single-shot rule, gate order, silence exemption, the corrective's `[game]` register, loop-cap interaction.

---

## §8 Closeout

- Complete the Step 0 stub in place: deviations (§5's no-new-tests exception restated), suite count, final commit hash, and the **operator playtest disposition** (verbatim-style, #170).
- Close **#308**, gated on §6 passing.
- **Post-deploy operator standing action (record in the closeout; not a PENDING block — no session executor exists):** after 25.11 merges and prod deploys, the operator restarts the **prod** bot from the main checkout — the running prod bot predates the gate.
- End with the `implementation-session-end` ritual (playtest disposition first; run the issues report).

---

## §9 Operator playtest checklist (dev stack, after §6.4)

1. The original probe: `sudo what do you remember`, repeated ~5×. Every response either renders a real report into the pane or answers honestly — **no delivery-claim prose without a rendered report**. The bot log may show `zero-tool answer ... — one corrective redo` on intercepted turns; at most one per request.
2. A conversational exchange (e.g. ticket-draft Q&A, stopping short of the confirm): answers arrive normally; a modest added latency on some turns is the ruled cost, not a defect.
3. One do-request (e.g. a bundle gift or a move): acts, narrates, and receipts exactly as before.
4. The confirm-gate filing flow end-to-end once, if desired: draft → read-back → yes → real receipt with the true issue number.
