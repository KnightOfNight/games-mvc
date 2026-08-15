---
name: implementation-session
description: Start a Shyland implementation session — declare the type, demand the branch name, join the worktree, hard pre-flight, verify the directed brief at the branch tip, run Step 0 (the closeout-report stub push). Use when the operator opens an implementation session for a release.
---

# Shyland Implementation-Session Startup

This session is an **IMPLEMENTATION session** (CLAUDE.md Rule 3): it may touch game code, tests, seed data, migrations, the architecture doc (final gated step), and dev-stack deploys (`make deploy-dev`) — and never GDD source (`make gdd` or brief-directed mechanical ops only) and never production deploys (closeout-tail only, Deployment Law). Declare this in your first reply.

Run this checklist **in order**. Report each step's outcome briefly; stop and report on any failure.

## 1. Branch name — the first act

The operator supplies the version branch name (`version_N` / `version_N_M`). If they haven't, ask — this is the one blocking question this skill is allowed. No branch name, no work.

## 2. Pre-flight (hard gate)

`python3 scripts/check_docker_host.py` — any non-zero exit is a **hard blocker**: stop, report, do no work on the brief. The printed target must be **local dev**.

## 3. Worktree

- Join the branch's existing worktree (`../games-mvc-<branch>`), or `git worktree add ../games-mvc-<branch> <branch>` if none exists. All work happens in the worktree, never the main checkout.
- Verify: clean tree, synced with origin. Env files arrive via the post-checkout hook (dev posture); sanity-check `DOMAIN` before any deploy.

## 4. Load verified state

- Read the highest-numbered `docs/shyland/Shyland_Project_Instructions_vN.md` — the process bible.
- The operator directs a brief **by name** (Rule 4). Confirm it exists **verbatim at the branch tip** (whitespace-only drift is report-and-accept). No directed brief = reference-only session; ask what the operator wants.
- Diff the brief's process assumptions against the standing rituals in the instructions; flag discrepancies before starting.
- **Technical pre-flight (#252):** diff the brief's load-bearing technical claims about existing code (function shapes, tuple members, call-site behavior, field names) against the code itself, before writing anything. **A mismatch on a load-bearing claim is a HARD STOP back to the operator** — never implement a false premise as written, never silently improvise around it.

## 5. Step 0 — verify-and-signal

Create the brief's closeout report as a **stub** (`.txt`, opening with a one-line session-start record: date, brief name, branch), commit, **push immediately** — the work-has-started signal. The stub is completed in place at session end.

## 6. Standing rules for the session body

- **Version-start duty (first brief of the release only):** bump `SHYLAND_VERSION` to `N.M-DEV` as its own opening commit (pin test moves with it), then `make deploy-dev`.
- Commit and push at **every step boundary** — branch only, never merge to main on your own initiative.
- Full suite via the path form: `python manage.py test apps/shyland/tests` (in-container). Deviations recorded in the closeout report, never silent.
- Architecture doc last, gated on all implementation and verification passing.
- End the session with the `implementation-session-end` skill. Do not close without it.
