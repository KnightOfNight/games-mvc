# Shyland Workflow Consolidation Plan

**Status:** DRAFT v2 — for operator review. Nothing in this document takes effect until approved.
**Date:** 2026-07-26 (v2 same day; v1 revised per operator fixes: paste retirement, branch discipline, automation items accepted)
**What this is:** the plan for retiring the claude.ai design chat and running the entire Shyland workflow — design and implementation — in Claude Code.

---

## 0. The one-paragraph version

Design conversations become Claude Code sessions. Everything the design chat did — planning versions, triaging tickets, making rulings, writing lore, producing briefs — happens in a **design session** instead, with direct access to the repo and the issue tracker. Each release lives on one **version branch**: the first design session for the release creates it, later design sessions join it, implementation sessions worktree onto it, and the whole version lands on main as one reviewed PR. Main is protected — only ops/housekeeping sessions run there. The discipline that made v19–v23 work is kept whole; what disappears is the transport between two systems.

---

## 1. Session types (the core of the change)

One system, three **session types**, distinguished by what they may touch and where they run:

| Session type | Runs on | May touch | Never touches |
|---|---|---|---|
| **Design session** | Version-branch worktree | `docs/shyland/gdd/` (GDD source), GitHub issues (file, comment, label, milestone, close), design/planning docs, briefs (writes AND commits them) | Game code, migrations, seed data, deployment |
| **Implementation session** | Version-branch worktree | Game code, tests, seed data, migrations, architecture doc (last gated step), deploys (operator-authorized) | GDD source (reads it, never writes it) |
| **Ops/housekeeping session** | `main` | Issues, transient docs (reports, standing process docs) | Game code, GDD source |

The firewall that matters — *implementation never invents design* — survives as a rule about session scope. Every session declares its type at the start.

**You're agreeing to:** design work in Claude Code sessions that may directly edit GDD source and issue state; implementation sessions scoped exactly as today; ops sessions as the only thing that commits to main directly.

---

## 2. Branch discipline (main is protected)

**The rule:** no doc or code changes land on main except via PR — the sole exceptions are ops/housekeeping sessions (issue-state clerical work, issues reports, process docs) and absolute emergencies. This extends the proven `version_22`/`version_23` implementation pattern to cover design too.

**The version-branch lifecycle:**

1. **The first design session for a release creates the branch** (`version_24`, from current main) and does the version-start rituals on it.
2. **Every later design session for that release joins the same branch** — new worktree, same branch. One branch per version, however many sessions it takes.
3. **Implementation sessions demand a branch name as their first act**, start a worktree on it, and find everything already there: the committed briefs, the updated GDD, the prior buckets' code. No handoff artifacts beyond the branch itself.
4. **Everything for the version accumulates on the branch** — briefs, GDD section edits, rulings' paper trail, code, tests, arch doc, closeout reports — and merges to main as **one version PR at closeout**, reviewed and merged by you (the v23 PR #153 pattern).
5. **Point releases** get their own short branch anchored to their founding ticket, as today (`version_21_1` pattern); in-flight version branches rebase after a point release lands, as today.

Consequences worth naming:

- **Main's GDD always describes the shipped game.** Unshipped design exists only on the version branch, so nobody reading main can be misled by not-yet-built rulings. (The "(vNN, pending implementation)" tag from plan v1 survives only as an *intra-branch* courtesy marker between buckets — main never needs it.)
- **Issues reports fork by session type:** design sessions commit theirs to the version branch; ops sessions commit theirs to main. Timestamped filenames mean the streams never collide at merge.
- **Issue state is not git.** Rulings, labels, and filings from a design session hit GitHub live regardless of branch — the branch carries the *documents*, the tracker carries the *state*. This is the same split v23 ran.
- Design-session worktrees never need `.env`/`ssl/` (they never build or deploy) — that copy step stays implementation-only.
- Optional enforcement, your call: a GitHub branch-protection rule on main requiring PRs, with you as the only bypass. The discipline works without it; the setting makes it unbreakable.

**You're agreeing to:** the protected-main rule, the five-step branch lifecycle, and (separately, optional) the branch-protection setting.

---

## 3. CLAUDE.md changes

Two rules rewritten; the rest stand untouched (app isolation, shared-surface stop-and-flag, pre-flight — all unchanged).

- **Rule 3 (design changes come only from the design chat)** becomes **"design changes come only from design sessions."** The clause "GDD source files are never authored or edited by Claude Code" becomes "…never authored or edited by *implementation or ops* sessions; design sessions author them with the operator in the conversation." `make gdd` stays the only GDD operation outside a design session.
- **Rule 4 (briefs are only applied when pasted)** — **pasting is retired entirely.** A brief is actionable only when (a) it has been discussed, planned, and triaged in a design session, (b) it is committed to the version branch, and (c) the operator directs a session to apply it by name ("apply Brief 2 on version_24"). Briefs found in the repo are never self-selected or auto-applied; the operator always pulls the trigger. Long chat pastes die as a document channel completely — git was already the sole channel for everything else, and now briefs join it.

**You're agreeing to:** these two rewrites, with replacement text drafted for your review as the first act after plan approval — CLAUDE.md doesn't change until you've read the actual words.

---

## 4. The document flow inverts (GDD-first)

**Today:** design chat rules → CC implements → architecture doc updates → GDD catches up at version closeout.

**After:** the design session updates the affected GDD section files **as rulings settle, before implementation** — on the version branch, so the GDD there describes the intended release ahead of its code. The implementation session then makes the architecture doc follow the code, as its last gated step, exactly as today. Version closeout gets lighter: the GDD is already current when the version PR opens, so closeout is stamps, the changelog row, and the `make gdd` rebuild.

Safety points: you approve GDD edits in-session (mechanics and balance get explicit review; creative content stays under the don't-spoil-the-novel policy — both unchanged), and main's GDD is structurally incapable of describing unshipped design (§2).

**You're agreeing to:** design sessions committing GDD section edits to the version branch with your in-session review of mechanics/balance, and the lighter closeout.

---

## 5. What replaces the ruling-transport briefs

Housekeeping immediacy is preserved and gets faster: when a ruling settles in a design session, the same session records it on the issue, applies `triaged`, files any split-out issues, and ends with the issues report — same conversation, nothing for you to carry. The "Ruling Recorded" ops-brief class ceases to exist.

Briefs survive where they earn their keep: **implementation briefs** (the contract between design intent and code, with Step 0, hard gates, deploys, closeouts — unchanged, except they're now born committed per §3) and genuinely standalone ops work. The 5-implementation-brief cap, amendments, bucket labels, and playtest checklists: all unchanged.

**You're agreeing to:** rulings landing on issues directly from design sessions, with the issues report as the same verification gate.

---

## 6. Rituals: what dies, what retargets, what stays

| Ritual step | Fate |
|---|---|
| Mirror finals (GDD/arch doc) to project files | **Dies.** The mirror served the chat being retired. |
| "Project memory updated" at closeout | **Retargets** to Claude Code's memory files — same habit, new home, no entry cap. |
| Design-side verification from committed issues reports | **Stays**, performed by the design session itself (fetch committed report, diff against expected end-state, report drift). |
| Design session ends with issues report, committed and pushed | **New standing rule** (operator-accepted) — to the version branch. |
| Pruning transient docs | **Stays yours.** Nothing changes. |
| Merges (incl. the version PR), deploy authorization, playtests | **Stay yours.** Nothing changes. |
| One design session per bucket | **Stays.** |
| Version-start SHYLAND_VERSION bump, Step 0 self-commit, push cadence, deploy-time data-action rule | **Stay**, verbatim. Version-start rituals now run on the fresh version branch. |

**You're agreeing to:** the two retirements and the one addition; everything else is explicitly frozen.

---

## 7. Automation (all three proposals accepted)

Automated by construction (formerly your manual sync labor): brief commits, GDD commits, ruling recording, all claude.ai upkeep.

Accepted by the operator, to be built as checklists/skills after plan approval:

1. **Design-session startup checklist** — declares the session type; determines the branch (*first session for the release? create `version_N` from main and run version-start rituals. Otherwise? join the existing branch*); creates the worktree; verifies clean state; fetches the current issues report; loads the instructions doc. Design sessions start from verified state the way implementation sessions always have.
2. **Design-session end ritual** — issues report generated, committed to the version branch, pushed; end-state verified against the tracker before the session closes.
3. **Version-closeout checklist runner** — walks the closeout ritual steps in order and refuses to skip gates.

Deliberately never automated: merges, deploys, pruning, playtest sign-off, scope rulings, anything touching production data. Control points, not chores.

**You're agreeing to:** building 1–3 as part of the migration (they'll arrive as reviewable skill/checklist definitions, not silent behavior).

---

## 8. The process bible

`Shyland_Project_Instructions_v23.md` gets a v24 rewrite reflecting all of the above: session types replace the chat/CC split, branch discipline gets its own section, the project-files section is deleted, the closeout ritual loses its mirror step, and the design-session conventions absorb the seven rules inherited from the retired chat's memory. One document, versioned in the repo, governing all three session types. Recommendation stands: rewrite it **immediately after plan approval**, so v24 planning runs under written rules rather than remembered ones.

**You're agreeing to:** the instructions rewrite, and its timing (recommended: before v24 planning).

---

## 9. Migration checklist

1. ~~Dump and triage the design chat's memory~~ — **done 2026-07-26**, unique residue ported.
2. ~~Confirm project files/instructions hold nothing repo-absent~~ — **done** (operator confirmed).
3. Operator approves this plan (line-item vetoes welcome).
4. I draft the CLAUDE.md Rule 3/4 replacement text for your review; you approve; I commit (via PR or as ops-on-main — your call, it's a process doc).
5. I draft `Shyland_Project_Instructions_v24.md` for your review; you approve; I commit.
6. I build the three checklist/skill definitions (§7) for your review.
7. Optional: you enable branch protection on main (§2).
8. You say goodbye to the claude.ai project and archive/delete it at your leisure — nothing depends on it from step 4 onward.
9. **Version 24 planning runs as the first design session** — it creates `version_24` and proves the model on the zone-build feature version.

**Not part of this plan:** the deployment-structure change (one dev stack, `make prod` disabled). It stays its own gated effort; consolidation just means you teach one system instead of two when you're ready.

---

## 10. What you are NOT agreeing to

No game code changes, no process loosening, no reduction in your review points, no autonomous merges or deploys, no self-selected work. The change is *where design conversations happen, which branch carries a version, and who does the clerical transport* — not who decides anything. Every decision that is yours today is yours after.
