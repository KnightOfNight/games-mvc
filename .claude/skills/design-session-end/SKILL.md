---
name: design-session-end
description: End a Shyland design session — confirm rulings and documents are recorded and committed, run the issues report on the version branch, push, and verify end-state against the tracker. Use when the operator says the design session is done (or before closing one).
---

# Shyland Design-Session End Ritual

Run **in order**. The session is not over until every step passes.

## 1. Ruling sweep

Review the session for every ruling made in conversation. Each must already be recorded on its issue (comment posted, `triaged` applied where ruled, milestone set per ruling). Record any straggler NOW and report it as a late catch — a ruling that lives only in the transcript is a process failure.

## 2. Document sweep

Every document authored this session — GDD section edits, briefs, planning docs — is committed and pushed to the version branch. `git status --porcelain` in the worktree must be clean; `git log origin/<branch>..<branch>` must be empty (everything pushed).

## 3. Issues report

Invoke the issues-report agent (it verifies a clean tree, generates the report, and commits + pushes it on the **current branch** — the version branch for a design session). Do not spell out its steps; do not substitute manual gh queries.

## 4. Verify end-state from the committed report

Read the report file the agent committed. Check the session's expected invariants against it — issues filed this session present, labels/milestones as ruled, closes as ruled. State invariants ("exactly two issues gained `triaged`"), not stale absolute counts. Any drift → report as a discrepancy list and resolve or escalate before closing.

## 5. Closing summary

Report to the operator: rulings recorded (issue numbers), documents committed (paths), briefs ready for implementation (**by name + branch** — the exact string an implementation session needs), open questions carried forward, and the suggested next session.

Then update Claude Code project memory if this session changed durable project state (version shape, standing rules, conventions) — the standing closeout habit.
