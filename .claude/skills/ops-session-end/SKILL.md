---
name: ops-session-end
description: End a Shyland ops/housekeeping session — verify all work is committed and pushed on main, issue state matches what was directed, and run the issues report on main (the formal end artifact). Use when the operator says the ops session is done (or before closing one).
---

# Shyland Ops-Session End Ritual

Run **in order**. The session is not over until every step passes. The operator's invocation is their positive confirmation that the session should end.

## 1. Work sweep

Every change this session made is accounted for: process docs committed, issue-state changes (comments, labels, milestones, closures) match what the operator directed — record any straggler NOW and report it as a late catch.

## 2. Everything pushed

On `main`: `git status --porcelain` clean; `git log origin/main..main` empty.

## 3. Issues report — always

Invoke the issues-report agent on `main` — **unconditionally**. Do not spell out its steps; do not substitute manual queries.

## 4. Verify end-state from the committed report

Check the session's expected invariants against the report (issues filed/closed/labeled this session), stated as invariants, not stale counts. Drift → discrepancy list, resolve or escalate before closing.

## 5. Closing summary

Report: what changed (commits, issues), anything left open, suggested next session. Update project memory if durable state changed (the standing habit).
