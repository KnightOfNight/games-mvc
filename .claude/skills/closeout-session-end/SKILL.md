---
name: closeout-session-end
description: End a Shyland closeout session — confirm every step of the closeout ritual completed (stamps, PR, merge, tail, memory, report) and nothing is left dangling. Deliberately overlaps the ritual's own closing step; kept for consistency so every session type ends with a positive confirmation. Use when the operator says the closeout session is done.
---

# Shyland Closeout-Session End Ritual

This skill is the operator's positive confirmation that the closeout session — and with it, the release — is done. It deliberately overlaps the `version-closeout` runner's closing step (operator ruling 2026-07-27: redundant is fine, consistency wins). It verifies; it never performs ritual steps — an incomplete step goes back to the runner.

## 1. Ritual completeness check

Against the `version-closeout` runner's checklist, confirm each step reached a terminal state: entry gates passed → version bookkeeping committed (stamps, changelog, markers, `make gdd`) → dev proof green → version PR **merged** (method recorded: squash or merge-commit, per the always-ask ruling) → tail completed (prod deployed on the one-time go-ahead, or explicitly left as "ready for operator deploy") → milestone closed → instructions refreshed if rules changed.

## 2. Git end-state

Version worktree: clean, pushed. Main checkout: synced to the merge, `SHYLAND_VERSION` reads the release stamp, no `-DEV` anywhere on main.

## 3. Memory + closing report

Project memory updated with the release's closed state; the closing report was delivered (stamps, hashes, PR number, merge method, test count, deploy status). If either is missing, produce it now.

## 4. Final word

One line to the operator: release N.M closed end-to-end; branch retained; worktree awaiting between-releases cleanup; next suggested session.
