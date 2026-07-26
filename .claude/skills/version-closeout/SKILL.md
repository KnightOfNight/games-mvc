---
name: version-closeout
description: Run the Shyland version-closeout ritual (major N.0 or point release N.M) as a gated checklist — every step verified in order, no gate skipped. Use when the operator directs the closeout of a release.
---

# Shyland Version-Closeout Runner

Determine the variant from the milestone: **major** (`Version N`) runs the full ritual; **point** (`Version N.M`) runs the lightweight variant. Authority: the Workflow section of the highest-numbered `Shyland_Project_Instructions_vN.md` — read it before starting; if it and this skill disagree, the instructions doc wins and the disagreement is reported.

Rules of the runner: execute steps **in order**; each step's gate must be verified PASSED before the next begins; a failed gate stops the ritual with a report — never skip, never reorder, never "come back to it." Steps marked **[operator]** are performed by the operator — verify their completion, never perform them. If a step belongs to a session type this session is not (e.g. GDD edits outside a design session), stop and tell the operator which session type it needs.

## Major-version ritual (Version N → N.0)

1. **Entry gate:** every issue in the milestone is closed; all implementation briefs' closeout reports exist on the version branch; no PENDING DEPLOY-TIME ACTIONS block remains unexecuted (check every closeout report in the version). Verify from committed files and the tracker, not memory.
2. **Architecture doc final:** `Shyland_Architecture_vN.md` exists for this version, stamped, header hash correct (architectural-changes commit). Verify committed.
3. **Version constant:** `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` bumped from `"N.0-DEV"` to `"N.0"`, committed on the version branch.
4. **GDD close (design-session work):** per-section updates for everything the version changed; changelog row in `_01_version_history.md`; stamp bumps in the index and `_00_header.md`; any "(vNN, pending implementation)" markers for this version removed.
5. **GDD build:** `GDD_MAJOR` bumped in the Makefile; old monolith `git rm`'d; `make gdd` run; new `Shyland_GDD_vN.md` committed. Verify the build-minus-banner matches the sections (the standing byte-identical check).
6. **Version PR:** opened from the version branch to main, carrying the whole release. **[operator]** reviews and merges.
7. **Instructions refresh:** if process rules changed during the version, produce the next `Shyland_Project_Instructions_vN.md` refresh (per the doc's own versioning convention) for operator review; if none changed, state "no process changes this version" explicitly.
8. **Post-merge:** local main synced; **[operator]** prunes transient documents at their leisure (never prompt for it, never do it).
9. **Memory update:** Claude Code project memory updated with the version's closed state (the standing closeout habit).
10. **Closing report:** one summary — stamps, hashes, PR number, test count, anything left open.

## Point-release ritual (Version N.M)

1. **Entry gate:** founding ticket (and its dependency tickets) closed; the single implementation brief's closeout report committed; no unexecuted deploy-time actions.
2. **Documents in place:** GDD changelog row + stamp bump to N.M (index + `_00_header.md`), affected section files updated in place; architecture doc stamped N.M in place (hash moved only if architectural). `make gdd` rebuild (`GDD_MAJOR` unchanged — the monolith filename never moves at a point release).
3. **Version constant:** `SHYLAND_VERSION` bumped to `"N.M"`.
4. **Version PR:** opened to main; **[operator]** reviews and merges.
5. **Memory update**, then the closing report. Pruning is the operator's.
