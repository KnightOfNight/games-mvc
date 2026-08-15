# Shyland Standalone Ops Brief — The `verify-prod` Target (Part 1 of #249)

**Lane:** standalone ops brief, main. **Authority:** #248 ruling (operator, 2026-08-15) + the Part 1/2/3 execution shape recorded on #249. **Precedent:** the #187 `seed-prod` process pass (e47bf78).

**Scope law for this brief:** everything *outside the container* — Makefile, guard hook, docs. **Zero game code.** The in-container half (the forced-rollback harness and the first `verify_*` command) is Part 2, riding an ordinary point release; the target ships **awaiting its first shipped verification command**. Part 3 (retire the v33 interim rule, close #249) happens only after Part 2 ships.

---

## 1. Makefile — the `verify` / `verify-prod` pair

Mirror the `seed` / `seed-prod` split exactly: a guarded current-target action, and a posture-setting production wrapper in the Deployment section.

**1a. `verify` (Django-management section, next to `seed`):**

- Guarded by `crosscheck-env` (from resting posture it targets **dev** — this is the "tested on dev" path every Part 2 brief uses).
- Requires `VERIFY=<name>`; refuses a missing value with a usage message.
- **Name gate:** the value must match `verify_*` — the read-only verification command family ruled on #248/#249. Anything else is refused. This naming convention is the contract until the Part 2 harness adds the runtime rollback backstop.
- Runs `docker compose exec django python manage.py $(VERIFY)`.

**1b. `verify-prod` (Deployment section, after the production seed target):**

The sibling contract, verbatim from the other two posture-setting targets:

- Refuses an ambient `DOCKER_HOST` (stale state gets investigated, not inherited).
- Requires `.env.prod` and `.env.dev` present and non-empty.
- Validates `VERIFY` (present + `verify_*`) **before** flipping posture — never leaves resting posture on a bad invocation.
- `cp .env.prod .env` → pinned-`DOCKER_HOST` pre-flight (`scripts/check_docker_host.py`) → pinned-`DOCKER_HOST` `$(MAKE) verify VERIFY=$(VERIFY)` → `cp .env.dev .env`.
- Partial failure deliberately leaves prod posture for a human — report, never repair.
- One command per invocation; a brief listing three checks means three operator-confirmed invocations.

**1c. Incidental consistency fixes (in scope, discovered writing this brief):**

- `.PHONY` is missing the production seed target; add it along with `verify` and `verify-prod`.
- The help text's Deployment section is missing the production seed target; add it along with `verify-prod`, and add `verify` under Django.

## 2. Guard hook + permissions (`.claude/settings.json`)

Third guard entry in the PreToolUse family, matching its siblings' shape with an argument-aware bare form:

- Any Bash command containing `verify-prod`: if the trimmed command matches exactly `make verify-prod VERIFY=verify_<word>` → **ask** (operator confirmation, #249); anything else → **deny** (embedded in a larger command — hard-blocked).
- `permissions.ask`: add the `make verify-prod VERIFY=*` form.
- `autoMode.soft_deny`: add the read-only-verification line mirroring the seed target's (exact single-command invocation only, operator confirmation in the current conversation).

Hooks hot-load mid-session: apply this file **last**, after the Makefile is verified, then prove the deny path with a harmless embedded invocation (expected: hard block).

## 3. Docs

- **CLAUDE.md** (shared surface — this brief is the operator authorization):
  - Deploy commands block: add `verify-prod` (operator-authorized only; read-only production verification in the same posture contract; awaiting its first shipped `verify_*` command, #249).
  - Both guard enumerations (Session Pre-Flight and the Make-commands guard note): add `verify` to the `crosscheck-env` list.
- **version-closeout skill**, tail step: after the production-seed sentence, add — prod-side read-only verification steps run via bare `make verify-prod VERIFY=verify_<name>`, one per operator confirmation, once Part 2 has shipped the command; until then such steps are handed to the operator (v33 interim).
- **Instructions:** no edit — v33 already codifies the interim and points at #249. Part 3 owns the retire.

## 4. Verification (all runnable in-session, ops-safe, dev-only)

1. `make verify` with no `VERIFY` → usage error, nonzero exit, posture untouched.
2. `make verify VERIFY=bogus` → name-gate refusal, nonzero exit.
3. `make verify VERIFY=verify_smoke` → passes both gates, reaches the dev container, and fails with Django's *Unknown command* — the correct, documented "awaiting first shipped command" state. Read-only against dev throughout.
4. `verify-prod` static review only — **never invoked in this session** (nothing to run; bare-only; operator confirmation). Confirm by inspection: gate order (VERIFY checks before posture flip), pinned pre-flight, restore line.
5. After the settings.json edit: prove the new hook's deny path with a harmless embedded use of the target's name (expected: hard block). The ask path is proven organically on first real use.

## 5. Not in this brief

- No `verify_*` management command, no rollback harness, no tests — Part 2, in-container, rides a release.
- No Instructions edit, no #249 closure — Part 3.
- No transient-document pruning; operator prunes.

**Close:** commit the applied changes to main (ops lane), record the applied state + verification results as a comment on #249 (which stays open for Parts 2–3), run the issues report.
