---
name: design-session
description: Start a Shyland design session — declare the session type, create or join the release's version branch, set up the worktree, and load verified state (instructions, GDD, latest issues report). Use when the operator opens a design session for a release (major or point).
---

# Shyland Design-Session Startup

This session is a **DESIGN session** (CLAUDE.md Rule 3): it may touch GDD source (`docs/shyland/gdd/`), GitHub issue state, design/planning docs, and briefs (writing AND committing them) — and never game code, migrations, seed data, or deployment. Declare this in your first reply.

Run this checklist **in order**. Report each step's outcome briefly; stop and report on any failure.

## 1. Pre-flight

- Run `python3 scripts/check_docker_host.py` and report the result. For design sessions this is **informational only** — they never touch the daemon — so any non-zero exit is reported to the operator, not blocking. (Implementation sessions keep the hard gate.)
- `git -C <main checkout> status --porcelain` on the main checkout must be clean before creating any branch from it.

## 2. Identify the release

- The operator names the release milestone — always `Version N.M` (milestones are shipping releases only; a major's feature queue is its permanent `VN` label, never a milestone — #175). If they haven't, ask — this is the one blocking question this skill is allowed.
- Branch name derives from the milestone, uniformly `version_N_M` (24.0 → `version_24_0`).
- **First release of a new major (`N.0`)?** This session also does the major's big coherent pass: re-triage the major's `VN`-labeled queue against the theme (off-theme issues lose the label — to a capability label or none), rule the system whole (rulings on issues — version-independent), and rule the queue order. Later releases' design sessions are small: next ticket, its GDD text, its brief.

## 3. Create or join the version branch

- `git fetch origin`, then check `git ls-remote --heads origin <branch>`.
- **Branch absent → this is the FIRST design session for the release:** create it from current `origin/main`, push with `-u`. The design-session version-start ritual is branch creation + push only — the `SHYLAND_VERSION → "N.M-DEV"` bump and the version-start `make deploy-dev` remain the FIRST IMPLEMENTATION brief's opening act (standing requirement; design sessions don't touch code, and production only ever runs main — Deployment Law). Bootstrapping confers no special status: every design session is standalone apart from this setup — there is no "master design session" (operator ruling 2026-07-27).
- **Branch present → join it:** you are a later session for this release; do not rebase or reset it.

## 4. Worktree

- `git worktree add ../games-mvc-<branch> <branch>` (or join the existing worktree directory if one is already checked out for this branch). All session work happens in the worktree, never the main checkout.
- Design worktrees never need `.env`/`ssl/` — do not copy them.

## 5. Load verified state

- Read the highest-numbered `docs/shyland/Shyland_Project_Instructions_vN.md` — it is the process bible for this session.
- Read the latest committed `Shyland_Issues_Report_*.md` (highest timestamp, on this branch or main, whichever is newer) and cross-check the milestone's issue set against it. If session context depends on a prior session's work, verify it from committed reports/documents — never assume.
- Read the GDD index (`docs/shyland/gdd/Shyland_GDD.md`) and the sections relevant to the session's topic.

## 6. Prior-bucket verification (first agenda item, unconditional)

- If any implementation brief for this release has closed since the last design session, verify it NOW from its committed closeout report plus the issues report: end-state invariants, deploy-time actions executed, drift reported as a discrepancy list. This is the release's post-implementation verification home — no closeout sits unverified past this point.
- Sweep the GDD on this branch for "(vNN, pending implementation)" markers whose implementation has landed, and remove them (marker removal is design-session work; implementation sessions never touch GDD source).
- If nothing has closed since the last session, state that explicitly and move on.
- (Complementary, not duplicative: design sessions verify between buckets as work lands; the closeout session re-verifies the complete release at the end. Both run; neither substitutes for the other.)

## 7. Readiness report

Summarize to the operator: branch (created or joined), worktree path, milestone issue set (open/triaged counts), any drift found in step 5, and the session's proposed agenda.

## Standing rules for the session body

- Rulings are recorded on their issues **immediately** — comment, `triaged` label in the same motion, milestone per ruling. GitHub follows the conversation in real time.
- GDD-first: section edits land as rulings settle; the operator reviews mechanics/balance edits in-conversation before commit; creative content flows under the creative-content policy. Intra-branch "(vNN, pending implementation)" markers where code hasn't landed yet.
- Briefs are born committed: write the brief file into `docs/shyland/` on this branch and commit it. Never deliver a brief by paste.
- Issue callouts, MapFrag diagrams for any layout work, geography audit for authored directional text, `--assignee "@me"` on every filing.
- Commit and push at every meaningful boundary — the operator follows the branch in near-real time.
- End the session with the `design-session-end` skill. Do not close without it.
