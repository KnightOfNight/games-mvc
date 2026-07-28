# Shyland V23.2 Brief 1 — Issues-Report Python Version Guard (#155)

- **Produced by:** the Version 23.2 design session, 2026-07-27 (branch `version_23_2`)
- **Milestone:** Version 23.2 (point release — scope law: one bucket B1, one implementation brief, one founding ticket)
- **Founding ticket:** #155 (`bug`, `B1`, `triaged` — ruling in the issue body, confirmed final by design-session comment 2026-07-27)
- **GDD:** **no GDD changes for this release** (operator-ruled 2026-07-27) — the change is repo tooling, not game design. No pending-implementation markers exist on this branch. Do not touch GDD source.
- **Pre-flight (deploy-time actions ledger):** no prior pending deploy-time actions are outstanding — v23.1 closed clean (PR #157 merged and deployed to production 2026-07-26).
- **Release character:** no game-code changes beyond the version stamp, but the release runs the **full standing rhythm** — version bump, dev deploy, playtest, closeout — by operator direction (v23.2 is the end-to-end process test under Instructions v25).

## Problem

`scripts/shyland_issues_report.py` crashes when run with the macOS system Python (3.9.6 at `/usr/bin/python3`). The script uses PEP 604 union annotations at exactly three sites — line 73 (`tuple[list[int], list[int]] | None`), line 103 (`str | None`), line 130 (`list[int] | None`) — which are evaluated at function-definition time and raise `TypeError: unsupported operand type(s) for |` on anything below 3.10. There is no `from __future__ import annotations`. The shebang is `#!/usr/bin/env python3`, which resolves to the 3.9 system interpreter, so a bare invocation gets a traceback instead of a report. The docstring's usage line (`Usage: python3 scripts/shyland_issues_report.py`, line 10) reproduces the failing invocation.

## The ruling (law — do not deviate)

Operator-confirmed 2026-07-27 on #155:

1. **The floor is Python 3.14+** — deliberately stricter than the 3.10 syntax minimum. 3.14 is the interpreter the script is run and tested on; guard for the supported environment, not the syntax floor.
2. **Two layers:** a shebang pointing at `python3.14`, plus an explicit runtime version guard.
3. **Guard placement:** top of module, immediately after the import block — before any annotated `def` — written in syntax that runs on old interpreters, so the friendly message always fires before the annotation `TypeError` can.
4. **Guard behavior:** exits nonzero with a message naming both the required version and the interpreter actually used.
5. **Docstring usage line updated** to the working invocation.

## Implementation

All paths repo-relative. The only files touched are `scripts/shyland_issues_report.py`, `django/src/apps/shyland/version.py`, and the pin test — nothing else.

1. **Version constant (opening act, own commit).** This is the release's only implementation brief: bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` from `"23.1"` to `"23.2-DEV"`, and in the **same commit** move the pin-test assertion in `django/src/apps/shyland/tests/test_b2_amendment1.py` (line 118, `self.assertEqual(SHYLAND_VERSION, '23.1')` → `'23.2-DEV'`). Then run the version-start `make deploy-dev` from the worktree. (The closeout ritual later stamps `"23.2"`.)
2. **Shebang + executable bit.** `scripts/shyland_issues_report.py` line 1: `#!/usr/bin/env python3` → `#!/usr/bin/env python3.14`. The file is currently **not executable** (`-rw-r--r--`), so the shebang has never been reachable by direct execution — set the executable bit as part of this change (`chmod +x` and commit the mode change; confirm `git diff` shows the `100644 → 100755` mode line).
3. **Version guard.** Insert after the import block (after `from pathlib import Path`) and before the `ISSUE_FIELDS` assignment — i.e. before the first `def` — exactly:

   ```python
   if sys.version_info < (3, 14):
       sys.exit(
           "FATAL: this script requires Python 3.14+; it was run with "
           f"Python {sys.version_info.major}.{sys.version_info.minor} "
           f"({sys.executable}). Try: python3.14 scripts/shyland_issues_report.py"
       )
   ```

   Every construct here (f-strings, `sys.version_info` tuple comparison, `sys.exit` with a string) parses and runs on Python 3.6+ — the guard wins the race against the annotation `TypeError` on any interpreter that could plausibly be invoked.
4. **Docstring.** Line 10: `Usage: python3 scripts/shyland_issues_report.py` → `Usage: python3.14 scripts/shyland_issues_report.py` (or direct execution via the shebang). Add `Python 3.14+` to the `Requires:` line.
5. **No model changes → no migration.** State in the closeout that no migration was created.
6. **No seed or data changes → PENDING DEPLOY-TIME ACTIONS: none.**

## Tests

No new Django tests — the changed script lives outside the Django app and has no test harness; its behavior is proven by the verification steps below. The pin test moves with the version bump (step 1). The full suite must pass unchanged: **v23.1 baseline 370 tests; expect exactly 370** (no additions, no removals). In-container invocation, the only working form:

```
python manage.py test apps/shyland/tests
```

(run via `docker exec` in the django container).

## Verification (all must pass before closing #155)

1. **Old interpreter gets the friendly guard:** `/usr/bin/python3 scripts/shyland_issues_report.py` → exits nonzero, output contains `requires Python 3.14+` and the interpreter path, and **no traceback / no `TypeError`**.
2. **Bare `python3` (the original failing invocation):** `python3 scripts/shyland_issues_report.py` — same result as step 1 wherever `python3` resolves below 3.14.
3. **Direct execution proves the shebang and the new executable bit:** `scripts/shyland_issues_report.py` (run from the repo root in the worktree) → a report generates normally in `docs/shyland/`. This creates one real timestamped report — commit it as a normal report artifact; reports are never deleted.
4. **Full Django suite green** (370/370) in the dev stack after the version-start `make deploy-dev`.

Close #155 only after all verification steps pass.

## Architecture doc (deliberate no-op — ruled)

**No architecture-doc changes in this brief.** Nothing architectural changed — the fix is repo tooling outside the game. The 23.2 stamp line moves at closeout as version bookkeeping (doc-only point release: stamp increments, **hash does not move**). This deviation from the usual last-gated-step is deliberate and ruled by the design session; record it in the closeout report.

## Deploy

- **Dev only.** `make deploy-dev` from the worktree — once as the version-start ritual (step 1) and again only if later commits change files under `django/src/` (this brief's remaining changes don't; a second deploy is not required).
- **Production is never deployed from this session.** The prod deploy happens only in the closeout session's tail on the operator's one-time go-ahead (Deployment Law, Instructions v25). This brief ends "ready for closeout."
- No deploy-time data actions.

## Ready after deploy — operator playtest checklist (dev stack)

1. Log into Shyland on the dev stack, run `help` — confirm the output shows `Version: 23.2-DEV`.
2. On your Mac, from the repo: `python3 scripts/shyland_issues_report.py` — confirm the friendly FATAL message naming Python 3.14+ and the interpreter used, with no traceback.
3. `scripts/shyland_issues_report.py` (direct) — confirm a report generates.

## Closeout

Standing process applies (Step 0 verify-and-signal: confirm this brief verbatim at the branch tip, commit and push the closeout-report stub `Shyland_V23.2_Brief_1_Closeout_Report.txt` as the work-started signal; commit and push at every step boundary; branch `version_23_2` only, never merge). The closeout report records: no migration created, no deploy-time actions pending, actual-vs-expected test count (370/370), the architecture-doc no-op deviation, and the final commit hash.

End by: **run the issues report.**
