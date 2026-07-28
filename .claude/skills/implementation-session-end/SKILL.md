---
name: implementation-session-end
description: End a Shyland implementation session — verify the brief is complete with deviations recorded, the closeout report finished in place, issues closed as gated, everything pushed, and run the issues report (the formal end artifact). Use when the operator says the implementation session is done (or before closing one).
---

# Shyland Implementation-Session End Ritual

Run **in order**. The session is not over until every step passes. The operator's invocation of this skill is their positive confirmation that the session should end; the ritual proves the branch agrees.

## 1. Work sweep

The directed brief's implementation AND verification sections are fully complete, and its issues are closed (closing is gated on verification passing). Any deviation from the brief is recorded in the closeout report — never silent.

## 2. Closeout report completed in place

The Step 0 stub is fully replaced with the finished report (including the final commit hash), committed and pushed. **A stub left incomplete marks this session as unended and will hard-block the closeout session.**

## 3. Everything pushed

`git status --porcelain` clean; `git log origin/<branch>..<branch>` empty. Dev-stack state reported (last `make deploy-dev`, suite count).

## 4. Issues report — always

Invoke the issues-report agent on the version branch — **unconditionally**, whether or not issues were touched. Its committed report is the **formal end artifact**: the closeout session's early gate checks that the branch's latest content commit is an issues report. Do not spell out the agent's steps.

## 5. Closing summary

Report to the operator: brief applied (name + branch), issues closed, test count, deviations, dev-deploy status, the operator playtest checklist handoff, and what's next (another bucket's implementation session, or "ready for closeout"). Update project memory if durable state changed (the standing habit).
