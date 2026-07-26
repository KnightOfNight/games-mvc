# Shyland Workflow Consolidation Plan

**Status:** DRAFT — for operator review. Nothing in this document takes effect until approved.
**Date:** 2026-07-26
**What this is:** the plan for retiring the claude.ai design chat and running the entire Shyland workflow — design and implementation — in Claude Code.

---

## 0. The one-paragraph version

Design conversations become Claude Code sessions. Everything you did in the design chat — planning versions, triaging tickets, making rulings, writing lore, producing briefs — happens in a **design session** instead, with direct access to the repo and the issue tracker. The discipline that made v19–v23 work is kept whole; what disappears is the transport between two systems: no more hand-carrying rulings as ops briefs, no more mirroring finals to project files, no more syncing anything to claude.ai. The GDD becomes a living document that design sessions update *first*, with the architecture doc following behind implementation, as you specified.

---

## 1. Session types (the core of the change)

Today there are two systems. After this change there is one system with three **session types**, distinguished by what they are allowed to touch:

| Session type | May touch | Never touches |
|---|---|---|
| **Design session** | `docs/shyland/gdd/` (GDD source), GitHub issues (file, comment, label, milestone, close), design/planning docs in `docs/shyland/`, briefs (writes them) | Game code, migrations, seed data, deployment |
| **Implementation session** | Game code, tests, seed data, migrations, the architecture doc (last gated step), deploys (operator-authorized) | GDD source (reads it, never writes it) |
| **Ops/housekeeping session** | Issues, transient docs — same as today | Game code, GDD source |

The firewall you actually care about — *implementation never invents design* — survives as a rule about session scope instead of a rule about which app the conversation happens in. Every session declares its type at the start (you say "design session" or paste a brief, same as today's habits).

**You're agreeing to:** design work happening in Claude Code sessions that may directly edit GDD source files and issue state, while implementation sessions remain exactly as scoped today.

---

## 2. CLAUDE.md changes

Two rules need rewriting; the rest stand untouched (app isolation, shared-surface stop-and-flag, pre-flight — all unchanged).

- **Rule 3 (Shyland design changes come only from the design chat)** becomes **"Shyland design changes come only from design sessions."** The design chat's monopoly transfers to the design-session type. The clause "the GDD source files are never authored or edited by Claude Code" becomes "…never authored or edited by *implementation or ops* sessions; design sessions author them with the operator in the conversation." `make gdd` stays the only GDD operation available outside a design session.
- **Rule 4 (briefs are only applied when pasted)** relaxes slightly: a brief becomes actionable when the operator either pastes it **or directs a session to apply a named brief file** ("apply Brief 2") — because under one system, the design session commits the brief to `docs/shyland/` itself, and re-pasting a file that's already in the repo is ceremony without safety. The core protection stays: briefs found in the repo are never self-selected or auto-applied; the operator always pulls the trigger, by name.

**You're agreeing to:** these two rewrites, drafted for your review as the first act after plan approval — CLAUDE.md doesn't change until you've read the actual replacement text.

---

## 3. The document flow inverts (GDD-first)

**Today:** design chat rules → CC implements → architecture doc updates → GDD catches up at version closeout, committed by you.

**After:** the design session updates the affected GDD section files **as rulings settle, before implementation** — the GDD describes the intended game ahead of the code. The implementation session then makes the architecture doc follow the code, as its last gated step, exactly as today. Version closeout gets lighter: the GDD is already current, so closeout is just stamps, the changelog row, and the `make gdd` rebuild.

Two details that make this safe:

- **You approve GDD edits in-session.** Design sessions show you what changed (mechanics and balance get explicit review; creative content stays under the don't-spoil-the-novel policy — both rules unchanged).
- **The GDD may briefly describe unshipped design.** That's the point of inversion, but it needs one honesty marker: sections describing not-yet-implemented rulings carry a small "(vNN, pending implementation)" tag that the implementing brief's closeout removes. The GDD never silently claims unbuilt things exist.

**You're agreeing to:** design sessions committing GDD section edits (with you reviewing mechanics/balance in-session), the pending-implementation tag convention, and the lighter closeout.

---

## 4. What replaces the ruling-transport briefs

Housekeeping immediacy is preserved and gets *faster*: when a ruling settles in a design session, the same session records it on the issue, applies `triaged`, files any split-out issues, and runs the issues report — in the same conversation, minutes later, with nothing for you to carry. The entire class of "Ruling Recorded" ops briefs (seven of them in the last week alone) ceases to exist.

Briefs survive where they earn their keep: **implementation briefs** (the contract between design intent and code work, with Step 0, hard gates, deploys, closeouts — all unchanged) and genuinely standalone ops work. The 5-implementation-brief cap, amendments, bucket labels, playtest checklists: all unchanged.

**You're agreeing to:** rulings landing on issues directly from design sessions, with the issues report as the same verification gate it is today.

---

## 5. Rituals: what dies, what retargets, what stays

| Ritual step | Fate |
|---|---|
| Mirror finals (GDD/arch doc) to project files | **Dies.** Git has been the sole channel since v20; the mirror was for the chat being retired. |
| "Project memory updated" at closeout | **Retargets** to Claude Code's memory files — same habit, new home, no 30-entry cap. |
| Design-side verification from committed issues reports | **Stays**, now performed by the design session itself (fetch the committed report, diff against expected end-state, report drift). |
| Pruning transient docs | **Stays yours.** Nothing changes. |
| Merges, deploy authorization, playtests | **Stay yours.** Nothing changes. |
| One design conversation per bucket | **Stays**, as one design *session* per bucket. |
| Version-start SHYLAND_VERSION bump, Step 0 self-commit, push cadence, deploy-time data-action rule | **Stay**, verbatim. |

**You're agreeing to:** the two retirements in rows one and two; everything else is explicitly frozen.

---

## 6. Automation inventory

What consolidation automates by construction (these were your manual sync labor):

1. Committing briefs to the repo (design session does its own Step 0).
2. Committing GDD updates (design session, with your in-session approval).
3. Recording rulings on issues (design session, same conversation).
4. All claude.ai mirroring and memory upkeep (gone entirely).

What could be automated next, **proposed, not assumed** — each needs your yes separately:

5. A `design-session` startup checklist (skill or agent) that pre-flights: clean tree, current issues report fetched, instructions doc loaded — so design sessions start from verified state the way implementation sessions do.
6. Auto-running the issues report at design-session end whenever issue state changed (today I ask; it could be standing).
7. A version-closeout checklist runner that walks the ritual steps in order and refuses to skip gates.

What is deliberately **not** automated, ever: merges, deploys, pruning, playtest sign-off, scope rulings, and anything touching production data. Those are control points, not chores.

**You're agreeing to:** items 1–4 (inherent to the change). Items 5–7 are a menu — pick any, none, or defer.

---

## 7. The process bible

`Shyland_Project_Instructions_v23.md` — which the memory-dump triage proved is already the real constitution — gets a v24 refresh reflecting all of the above: session types replace the chat/CC split, the "Documents in This Project" (project-files) section is deleted, the closeout ritual loses its mirror step, and the design-session conventions section absorbs the seven inherited rules from the retired chat's memory. One document, versioned in the repo, governing both session types. It refreshes at the v24 closeout per the existing instructions-refresh ritual — or immediately after plan approval if you prefer the constitution to lead rather than trail. My recommendation: immediately, so v24 planning runs under written rules, not remembered ones.

**You're agreeing to:** the instructions rewrite, and choosing its timing (my recommendation: before v24 planning).

---

## 8. Migration checklist

1. ~~Dump and triage the design chat's memory~~ — **done 2026-07-26**, unique residue ported.
2. ~~Confirm project files/instructions hold nothing repo-absent~~ — **done** (operator confirmed).
3. Operator approves this plan (with any line-item vetoes).
4. I draft the CLAUDE.md Rule 3/4 replacement text for your review; you approve; I commit.
5. I draft `Shyland_Project_Instructions_v24.md` for your review; you approve; I commit (timing per §7).
6. You say goodbye to the claude.ai project and archive/delete it at your leisure — nothing depends on it from step 4 onward.
7. **Version 24 planning runs as the first design session**, one bucket-planning session at a time, proving the model on the zone-build feature version.

**Not part of this plan:** the deployment-structure change (one dev stack, `make prod` disabled). It stays its own gated effort with its own session and go-ahead; consolidation just means that when you're ready, you teach one system instead of two.

---

## 9. What you are NOT agreeing to

For the avoidance of 2 a.m. doubt: no game code changes, no process loosening, no reduction in your review points, no autonomous merges or deploys, no self-selected work. The change is *where design conversations happen and who does the clerical transport* — not who decides anything. Every decision that is yours today is yours after.
