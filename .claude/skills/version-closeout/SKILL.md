---
name: version-closeout
description: Run the Shyland version-closeout ritual (major N.0 or point release N.M) as a gated checklist — every step verified in order, no gate skipped. Use when the operator directs the closeout of a release.
---

# Shyland Version-Closeout Runner

Determine the variant from the milestone: **major** (`Version N`) runs the full ritual; **point** (`Version N.M`) runs the lightweight variant. Authority: the Workflow section of the highest-numbered `Shyland_Project_Instructions_vN.md` — read it before starting; if it and this skill disagree, the instructions doc wins and the disagreement is reported.

Rules of the runner: execute steps **in order**; each step's gate must be verified PASSED before the next begins; a failed gate stops the ritual with a report — never skip, never reorder, never "come back to it." Steps marked **[operator]** are performed by the operator — verify their completion, never perform them. If a step belongs to a session type this session is not (e.g. GDD edits outside a design session), stop and tell the operator which session type it needs.

## Major-version ritual (Version N → N.0)

1. **Entry gate:** every issue in the milestone is closed; all implementation briefs' closeout reports exist on the version branch; every brief's operator playtest is confirmed complete **on the dev stack**; no PENDING DEPLOY-TIME ACTIONS block remains unexecuted on dev (production-side actions belong to the operator's post-merge deploy window — step 8 — and do not block entry). Verify from committed files and the tracker, not memory.
2. **Architecture doc final:** `Shyland_Architecture_vN.md` exists for this version, stamped, header hash correct (architectural-changes commit). Verify committed.
3. **Version constant:** `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` bumped from `"N.0-DEV"` to `"N.0"` (pin test moved in the same commit), committed on the version branch.
4. **GDD close (design-session work):** per-section updates for everything the version changed; changelog row in `_01_version_history.md`; stamp bumps in the index and `_00_header.md`; any "(vNN, pending implementation)" markers for this version removed.
5. **GDD build:** `GDD_MAJOR` bumped in the Makefile; old monolith `git rm`'d; `make gdd` run; new `Shyland_GDD_vN.md` committed. Verify the build-minus-banner matches the sections (the standing byte-identical check).
6. **Version PR:** two gates first — **the -DEV gate:** `version.py` at the branch tip must carry no `-DEV` (main never contains a `-DEV` suffix, on any commit; a PR that would put one there must not open); and **merge-forward:** if main has advanced since the branch was cut, `git merge main` into the branch now (an ordinary merge — never rebase, never force-push). Then the PR: opened from the version branch to main, carrying the whole release. **[operator]** reviews and merges.
7. **Instructions refresh:** if process rules changed during the version, produce the next `Shyland_Project_Instructions_vN.md` refresh (per the doc's own versioning convention) for operator review; if none changed, state "no process changes this version" explicitly.
8. **Post-merge:** local main synced; **[operator]** deploys production from the **main checkout** — `make deploy-prod` (production runs main only; never from a worktree, never invoked by a Claude session), executing any pending production-side deploy-time data actions in that window; **[operator]** prunes transient documents at their leisure (never prompt for it, never do it).
9. **Memory update:** Claude Code project memory updated with the version's closed state (the standing closeout habit).
10. **Closing report:** one summary — stamps, hashes, PR number, test count, anything left open.

## Point-release ritual (Version N.M)

1. **Entry gate:** founding ticket (and its dependency tickets) closed; the single implementation brief's closeout report committed; operator playtest confirmed complete **on the dev stack**; no deploy-time actions unexecuted on dev (production-side actions belong to the operator's post-merge deploy window).
2. **Documents in place:** GDD changelog row + stamp bump to N.M (index + `_00_header.md`), affected section files updated in place; architecture doc stamped N.M in place (hash moved only if architectural). `make gdd` rebuild (`GDD_MAJOR` unchanged — the monolith filename never moves at a point release).
3. **Version constant:** `SHYLAND_VERSION` bumped `"N.M-DEV"` → `"N.M"` (pin test moved in the same commit).
4. **Version PR:** gates first — **the -DEV gate** (`version.py` at the branch tip carries no `-DEV`) and **merge-forward** (if main has advanced, `git merge main` into the branch — never rebase). Then the PR opened to main; **[operator]** reviews and merges, then deploys production from the **main checkout** — `make deploy-prod` — executing any pending production-side data actions in that window.
5. **Memory update**, then the closing report. Pruning is the operator's.
