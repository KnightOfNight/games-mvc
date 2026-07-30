---
name: version-closeout
description: Run a Shyland closeout session (major N.0 or point release N.M) — the fourth session type, exactly one per release. Gated checklist from the session-end gate and entry verification through the operator-permitted merge and the tail's one-time-go-ahead prod deploy. Use when the operator directs the closeout of a release.
---

# Shyland Closeout-Session Runner

This session is a **CLOSEOUT session** (Instructions, Session Types): exactly one per release, operator-declared. It touches **no game code and no game design content** — its entire edit surface is version bookkeeping: doc stamps, the changelog row, this release's landed "(pending implementation)" markers, and the **stamp whitelist** (`SHYLAND_VERSION` line + its pin-test assertion — a stamp that happens to live in a `.py` file, extending no further). Declare this in your first reply.

Authority: the Workflow section of the highest-numbered `Shyland_Project_Instructions_vN.md` — read it before starting; if it and this skill disagree, the instructions doc wins and the disagreement is reported. **Every release runs this same ritual** (release milestones are always `Version N.M`; a bare `Version N` milestone is a feature queue, never a release). An **`N.0` release** — a major's first — additionally runs the major-opening mechanics in step 5.

Rules of the runner: execute steps **in order**; each gate verified PASSED before the next begins; a failed gate stops the ritual with a report — never skip, never reorder, never "come back to it." Steps marked **[operator]** are the operator's — verify, never perform. A blocking design gap (unruled change, unswept marker from a *different* release) goes back to a design session — never resolve it here.

## The ritual

1. **Pre-flight + worktree.** `python3 scripts/check_docker_host.py` (hard gate on non-zero). Work in the release's version worktree. Verify clean tree, synced with origin.
2. **Session-end gate — FAIL HARD, EARLY.** Every design and implementation session for this release must have formally ended (their end skills' rituals; operator ruling 2026-07-27). Checks, on the branch as-is:
   - Clean tree, fully pushed (already verified in step 1 — a dirty or unpushed branch is an unended session).
   - Every brief's closeout report is **complete** — a stub-only report is an unended implementation session.
   - The branch's most recent non-merge commit is a **committed issues report** (the end rituals' terminal artifact). Content commits after the last issues report mean an unended session.
   Any failure → STOP and report which session type must run its end ritual first. Never patch the branch to make this gate pass.
3. **Forward-merge main.** If main has advanced since the branch was cut: `git merge main` (ordinary merge — never rebase, never force-push), push. This session must read current process docs from its own checkout.
4. **Entry verification — implementation is DONE, verified never assumed:** every milestone issue closed; every brief's closeout report committed on the branch; **every brief's playtest disposition read from its committed closeout report (#170)** — "Operator reports playtest successful" and "No playtests for this brief" are terminal; **"Operator deferring playtest" is a BLOCKER: stop and ask the operator to attest the deferred playtest now, in-conversation, and record the late attestation in the closing report** — no dev-side deploy-time actions unexecuted; architecture doc stamped for this release. Verify from committed files and the tracker, not memory.
5. **Version bookkeeping (the only edits this session makes):**
   - GDD: changelog row in `_01_version_history.md` **on its own physical line** (the v23.1 closeout once appended onto the prior row's line — check the table renders); stamp bumps in the index + `_00_header.md`; this release's landed "(vN.M, pending implementation)" markers swept — parenthetical deletion only, each verified against the shipped code, zero prose changes.
   - **Sweep self-check (#173 — the v23.3 closeout missed two markers):** after sweeping, grep the GDD source for any remaining marker naming THIS release (e.g. `grep -rn 'vN.M' docs/shyland/gdd/ | grep 'pending implementation'`, single-quoted). Nonzero hits = the sweep is not done; sweep them and re-check. Do not proceed past this bullet with hits remaining.
   - Architecture doc: stamp to the release value (hash moves only for architectural changes).
   - **Stamp whitelist:** `SHYLAND_VERSION` → release stamp, pin-test assertion moved, same commit.
   - *`N.0` releases only — the major-opening mechanics:* `GDD_MAJOR` bumped in the Makefile, monolith renamed to the new major, old monolith `git rm`'d.
   - `make gdd` rebuild, always.
6. **Final proof on dev:** `make build` from the worktree, then the full in-container suite — `docker exec <django-container> python manage.py test apps/shyland/tests` (path form; the label form crashes on the `apps` namespace package). Dev now runs exactly the build production will get, with no DEV suffix anywhere. Suite must be green.
7. **Gate + PR:** the DEV-suffix gate — grep the `SHYLAND_VERSION` **constant line only** (a whole-file grep false-positives on docstring wording); it must carry no `-DEV`. CI enforces the same on the PR. Commit, push, open the version PR to main carrying the whole release.
8. **The merge [operator-permitted]:** ask the operator ONE fresh in-conversation question — merge now, and **squash or merge-commit** (always an explicit choice, never assumed; both have version-PR precedent). The permission is single-use for this PR. Merge on their answer. Branches are never deleted.
9. **The tail (moves to the main checkout):** `cd` to the main checkout (a directory change — it always sits on `main`), `git pull --ff-only`, verify the tip is the merge result and the constant reads the release stamp. Report **ready for production deploy**, listing any pending production-side data actions and the standing reminder that the deploy bounces all three games.
   - **[operator] The go-ahead:** on the operator's **one-time go-ahead** — fresh, in-conversation, covering exactly this one deploy — run `make deploy-prod` from the main checkout, then execute any pending production-side data actions in the same window and record results. Absent a go-ahead, end here as "ready for operator deploy" — the operator runs it personally. No other session type ever invokes or hosts the prod deploy.
10. **Close:** instructions refresh if process rules changed this release (next `vN` — the doc's version is an independent counter); transient-document pruning is **[operator]** only, never prompt for it; update Claude Code project memory (the standing closeout habit); closing report — stamps, hashes, PR number, merge method, test count, deploy status, anything left open. Then end the session with the `closeout-session-end` skill — the operator's positive confirmation. Do not close without it.
