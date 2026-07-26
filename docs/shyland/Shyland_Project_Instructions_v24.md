# Shyland Project Instructions v24

**Status: ACTIVE — approved by the operator 2026-07-26. Supersedes Shyland_Project_Instructions_v23.md.**

These instructions govern every Claude Code session doing Shyland work, of every type. Read them at the start of any Shyland session. The document is versioned in sync with the game's current major version; refreshing it (when process rules changed during the version) is part of the version closeout ritual. This v24 edition is the workflow-consolidation rewrite (2026-07-26, per `Shyland_Workflow_Consolidation_Plan.md`): the claude.ai design chat is retired, and design, implementation, and ops all run as typed Claude Code sessions. It governs all sessions from its approval onward, including any v23.x point release. **Amended in place 2026-07-26 (#156): the Deployment Law section added — production runs main only, playtests run on dev, the -DEV gate at closeout — with the implementation-brief deploy requirements rewritten to match.**

---

## What This Project Is

Shyland is a free, web-based Multi-User Dungeon (MUD) — a modern version of classic text-based telnet MUDs. It runs in the browser, is screen reader compatible, has no monetization of any kind, and is built on a Django/Channels/PostgreSQL stack.

The setting is a genre-collision world where dimensional rifts have pulled fragments of different realities together. A cyberpunk street samurai can appear in a woodland adventure zone. The anachronism is intentional and central to the game's identity.

---

## The Repo

**https://github.com/KnightOfNight/games-mvc**

The source of truth for all code, all documents, and all process state. Key locations:

- `django/src/apps/shyland/` — the Shyland Django app (models, consumers, currency, admin, templates)
- `docs/shyland/` — the authoritative home of the GDD, the architecture doc, all transient documents (briefs, amendments, closeout reports, issues reports), and the MapFrag audit history
- `docs/shyland/gdd/` — the GDD **source**: one file per top-level section plus the stamped index `Shyland_GDD.md` (see Documents below)
- `CLAUDE.md` — repo-wide orientation document (read first in any session)
- `Makefile` — all build and management commands
- `.claude/agents/` — reusable agents (the issues-report agent lives here); `.claude/` also holds skills

Sessions read the repo directly. Verification reads committed files at the branch tip (or at a specific hash when precision matters) — never a chat narrative alone. Long chat pastes are dead as a document channel: documents route through git, always.

---

## Documents

- **The GDD** — the authoritative source for game design decisions; check here first when design questions arise. Its **source** is `docs/shyland/gdd/`: one file per top-level section (unversioned filenames; section numbering preserved verbatim so every §-reference stays valid) plus the index `Shyland_GDD.md`, which carries the version stamp of record, the lockstep note, and the build-order table. The monolithic **`Shyland_GDD_vN.md`** is a **generated build artifact** — `make gdd` prepends a 4-line banner and concatenates the sections in order (output filename driven by the Makefile's `GDD_MAJOR` variable). **The section files win if the two ever disagree**; the monolith is never hand-edited.
- **Shyland_Architecture_vN.md** — the authoritative technical reference describing what is actually built; check here first when implementation questions arise. The architecture doc remains **monolithic** — the split applies to the GDD only.

The two documents' version numbers are always in sync — including point-release stamps (N.M). The GDD's stamp of record lives in the index; a stamp change touches the index, `_00_header.md`, and the changelog (`_01_version_history.md`), followed by a `make gdd` rebuild. A **point release never creates new document files**: both documents are updated **in place**, their stamps move to N.M, and only affected sections are touched. The monolith's filename keeps the major-version `vN` name (`GDD_MAJOR` bumps only at major closeouts, with the old monolith `git rm`'d at the rename).

The architecture doc's header records the git commit hash of the version's architectural changes; a design-only version (or doc-only point-release change) increments the stamp without moving the hash. An architectural point release moves the hash.

**Main is the state of record, not necessarily what's running.** Main's GDD always describes the released game; unshipped design exists only on version branches. (Deployment follows the same law: the **dev stack** runs branch builds during development and hosts all playtests; **production runs main only** — see Deployment Law.) Within a version branch, GDD sections describing rulings whose implementation hasn't landed yet may carry a "(vNN, pending implementation)" marker as an intra-branch courtesy between buckets. **Marker removal is design-session work** — implementation sessions never edit GDD source, markers included: the next design session sweeps markers whose implementation has landed (a startup agenda item), and the GDD close at version closeout removes any stragglers.

---

## Session Types — How Work Is Organized

Every Shyland session has an operator-declared type. The type bounds what the session may touch (also codified in CLAUDE.md Rule 3):

| Session type | Runs on | May touch | Never touches |
|---|---|---|---|
| **Design** | Version-branch worktree | GDD source, GitHub issue state, design/planning docs, briefs (writes and commits them) | Game code, migrations, seed data, deployment |
| **Implementation** | Version-branch worktree (operator supplies the branch name) | Game code, tests, seed data, migrations, architecture doc (final gated step), dev-stack deploys (`make deploy-dev`) | GDD source (reads, never writes; `make gdd` / brief-directed mechanical ops only); production deploys — `make deploy-prod` is operator-run, from main, post-merge (Deployment Law) |
| **Ops/housekeeping** | `main` | Issue-state clerical work, issues reports, process docs | Game code, GDD source |

**Design sessions are the design-and-ruling environment** — brainstorming, system design, rulings, GDD maintenance, brief writing. **Implementation sessions are the build environment.** The firewall is absolute: implementation never invents design; design never touches code.

**Multiple design sessions per major version:** roughly **one design session per bucket**, planned that way from the start. Nothing carries between sessions except the issue tracker, the committed documents, and Claude Code's persistent memory — a session that needs context reads issues and repo docs, never another session's transcript. Each session verifies its own work from committed reports before handing off.

**Division of labor (the triage pipeline):** the operator files issues thin at the moment of discovery → triage fattens them (diagnosis comments; may add the `bug` label when genuinely confirmed — never milestones, never closes, never changes code during triage) → design sessions rule (milestone, design direction, `triaged` label in the same motion) → briefs implement → committed reports verify.

---

## Branch Discipline — Main Is Protected

No doc or code changes land on main except via PR — the sole exceptions are ops/housekeeping work and absolute emergencies the operator declares.

**The version-branch lifecycle (a release is a release — major or point, same lifecycle):**

1. **The first design session for a release creates the branch** — named for the milestone (`version_24`, `version_23_1`), cut from current main — and runs the version-start rituals on it.
2. **Every later design session for that release joins the same branch** — new worktree, same branch. One branch per release, however many sessions it takes.
3. **Implementation sessions demand a branch name as their first act**, start a worktree on it, and find everything already there: committed briefs, updated GDD, prior buckets' code.
4. **Everything for the release accumulates on the branch** — briefs, GDD edits, code, tests, arch doc, closeout reports, design-session issues reports — and merges to main as **one version PR at closeout**, reviewed and merged by the operator.
5. The point-release **scope law** (below) constrains what goes on a point-release branch, not how the branch works. Any in-flight branch **merges main forward** after another release lands (never a rebase — Deployment Law).

Notes: issue state is not git — rulings, labels, and filings hit GitHub live from any session regardless of branch. Issues reports fork by session type: design sessions commit theirs to the version branch, ops sessions to main; timestamped filenames never collide at merge. Worktree env files are automated: the committed `post-checkout` git hook (activated per clone via `make hooks`) copies `.env.dev`, `.env.prod`, and `ssl/` from the main checkout into every new worktree and initializes `.env` in **dev posture** (`.env.dev`). Design-session worktrees never use them (they never build or deploy); implementation worktrees get them ready-made — and still sanity-check `DOMAIN` before any deploy.

---

## Deployment Law — Dev and Prod (operator-ruled 2026-07-26, #156)

Two invariants, absolute:

1. **Production runs `main` — nothing else, ever.** `make deploy-prod` is run by the operator, from the **main checkout**, only **after** the version PR has merged. Never from a worktree; never with unmerged code; never invoked by a Claude session under any circumstances (the permission layer is a backstop, not the decision point).
2. **`main` never contains a `-DEV` suffix in `SHYLAND_VERSION` — on any commit, at any time.** `-DEV` exists only on version branches, between the version-start bump and the closeout stamp. A version PR whose tip still reads `N.M-DEV` is not mergeable; the closeout stamp step is the gate that makes it so.

The flow every release follows (major `N.0` or point `N.M` alike):

1. **Version start** (first implementation brief, opening act): bump `SHYLAND_VERSION` to `N.M-DEV` in its own commit (the pin test moves with it), then `make deploy-dev` from the worktree.
2. **Every brief deploys to dev**: `make deploy-dev` from the worktree once implementation and verification pass. The dev stack is where the release lives during development.
3. **All operator playtests run on the dev stack.** Brief playtest checklists target dev; production hosts no mid-version builds.
4. **Closeout stamps on the branch**: `N.M-DEV → N.M` before the PR opens, alongside the doc stamps. The **-DEV gate**: no version PR opens while `version.py` reads `-DEV`.
5. **The version PR merges to main** (operator-reviewed).
6. **The operator deploys production from main**: `make deploy-prod` from the main checkout. Deploy-time data actions (seed reruns, `make seed`, fixups) execute against production **here**, in the operator's post-merge deploy window — PENDING DEPLOY-TIME ACTIONS blocks stay open until this point.

**Main moves mid-release → merge forward, never rebase.** When main advances while a release is in flight (ops work, another release landing), bring it into the version branch with an ordinary `git merge main` from the worktree. Published branches are never rebased or force-pushed. In particular, process-doc changes on main (instructions, skills) must be merged into the branch **before** the next session that depends on them runs there — worktree sessions read process docs from their own checkout.

---

## Versions, Issues, and Cadence

- **Issue-first law:** every item entering version planning has a GitHub issue number before design work begins. Rulings and briefs reference issue numbers. Design history lives in the issue tracker (rulings recorded as issue comments at the moment they're made, by the design session itself); the GDD's changelog carries one comprehensive row per closed version.
- **Milestones** group each version's issues. Names are exactly `Version N` / `Version N.M`.
- **Version cadence:** EVEN-numbered major versions are feature releases; ODD-numbered are bug-fix/refinement releases (including improvements to working-as-designed behavior). The bug-vs-feature line is deliberately gray — judgment applies.
- **Ruling immediacy:** when a ruling changes triage or issue state, the design session records it on the issue immediately — GitHub follows the design conversation in real time, never batched. (Playtest findings may be *ruled* immediately and *batched* into one consolidated amendment for a single implementation round trip.)
- **Brief cap:** maximum 5 implementation briefs per major version. Amendments don't count. Research/triage/ops work doesn't count. Consider splitting data-fix and feature work into separate briefs, and be willing to drop scope during triage — v20 ran hot at 23 issues.
- **Brief numbers map to buckets, not execution order.** Brief N implements bucket BN; the run order is an operator ruling made independently (v23 executed 2, 1, 3, 4, 5). Nothing may assume it is first — see the architecture-doc rule below.
- **A bucket may split across briefs by mechanism** — code half then data half (v23 B4/B5 pattern); costs a brief slot and is usually worth it.
- **"Defer" means:** not this version, plus a GitHub issue (milestoned to a future version, or unmilestoned for someday).

### Point Releases (Version N.M)

- **Entry bar:** urgent / critical / i-want-it-now only. Bug or feature — odd/even parity applies only to major versions.
- **Numbering:** M is a **minor version number, not a decimal** — 21.5 < 21.15, ordering numeric on M.
- **Scope law:** exactly **one bucket (B1)**, **one implementation brief**, **one founding ticket**. Additional tickets only as dependencies (`gh --blocked-by`) describing the same problem, never widening it. Mid-build discoveries file thin into the normal pipeline; a second breaking issue means a second point release.
- **Timing:** may plan and ship while a major version is in flight, and may land ahead of it; in-flight branches merge main forward after it lands (never a rebase).
- **Sessions:** its own design session, its own branch — same lifecycle as any release.
- **Documents:** no new files — GDD and architecture doc updated in place. The GDD gets its own changelog row.
- **Closeout:** the lightweight variant (Workflow step 5a).

---

## Workflow — The Release Lifecycle

**1. Design sessions rule and author.** Rulings are recorded on their issues in the same conversation, immediately. GDD section files are updated **as rulings settle, before implementation** — GDD-first; the operator reviews mechanics/balance edits in-session (creative content flows under the creative-content policy). Briefs are written AND committed to the version branch by the design session. Every design session ends with the end ritual: issues report generated, committed to the version branch, pushed; end-state verified against the tracker before the session closes.

**2. Implementation sessions build.** The operator supplies the branch name and directs a brief by name. **Step 0 (verify-and-signal):** confirm the directed brief exists verbatim at the branch tip (it was committed by its design session; whitespace-only drift is report-and-accept), then create the brief's closeout report as a **stub** — the `.txt` file opening with a one-line session-start record (date, brief name, branch) — commit it, and **push immediately**: that push is the work-has-started signal, a defined artifact rather than whatever work commit happens first. The stub is completed in place at closeout. Thereafter it commits and pushes at every step boundary — branch only, never merging on its own initiative. It implements, runs verification, closes the brief's issues (gated on verification passing), updates the architecture doc as the **last, gated step**, commits its **closeout report** as a `.txt` in `docs/shyland/`, and — for any brief that touched issues — ends by running the issues report.

**3. Verification from committed reports.** Post-implementation verification belongs to the **next design session for the release, as its first agenda item** (the design-session skill enforces this — the commissioning session is closed by the time implementation runs). It fetches the committed reports from the repo and verifies the end state against expectations — a required gate. Verify from committed reports, never a closeout narrative alone; report drift as a discrepancy list. Verification arithmetic states invariants ("exactly one issue added"), not absolute counts that go stale.

**4. Operator playtest.** Between briefs, per the playtest checklists, **against the dev stack** (production hosts no mid-version builds — Deployment Law). Findings are ruled as they surface; fixes roll into consolidated amendments.

**5. Version closeout ritual (major versions):** final architecture doc committed by the implementation session → `SHYLAND_VERSION` bumped to the release stamp (`N.0`) alongside the doc stamps → GDD vN.0 closed by a design session as **per-section updates** (changed section files, changelog row, stamp bumps in index + `_00_header.md`) → `GDD_MAJOR` bumped in the Makefile, old monolith `git rm`'d, `make gdd` run → **-DEV gate verified** (`version.py` at the branch tip carries no `-DEV`) → **the version PR opened for operator review and merge** → project instructions refreshed if process rules changed during the version → **after the merge, the operator deploys production from the main checkout (`make deploy-prod`), executing any pending deploy-time data actions in that window** → transient documents pruned **by the operator only** → Claude Code project memory updated (the standing closeout habit, retargeted from the retired chat's memory).

**5a. Point-release closeout (lightweight):** verification from committed reports → GDD changelog row and stamp bump to N.M, affected sections updated in place, `make gdd` rebuild (`GDD_MAJOR` unchanged) → `SHYLAND_VERSION` bumped `N.M-DEV → N.M` (pin test in the same commit) → **-DEV gate verified** → version PR opened for operator review and merge → after the merge, the operator deploys production from the main checkout (`make deploy-prod`) → memory updated. Pruning is the operator's, as always.

**The GDD is authored by design sessions. The architecture doc is authored by implementation sessions.** These are not interchangeable. Implementation and ops sessions never author or edit GDD source; their only permitted GDD operation is `make gdd` (or another mechanical operation explicitly directed by a brief).

---

## Brief Writing Rules

- Briefs are self-contained — the implementation session reads only the brief (and the repo), never a design conversation
- Briefs are **born committed**: the design session writes the brief file into `docs/shyland/` on the version branch and commits it (standalone ops briefs are the exception: an ops session commits them to `main`). Pasted briefs are never actionable (CLAUDE.md Rule 4) — actionability = committed + operator-directed by name
- **Push cadence (every implementation brief):** commit and push at every step boundary — WIP-sized intermediate commits desired; **branch only, NEVER merge to main on the session's own initiative** (merging is the operator's action; operator-directed merges via the scoped `gh pr merge` allowance are standing capability, not a discrepancy)
- **Deploy-time data-action rule:** for production, "deploy time" means the operator's **post-merge `make deploy-prod` window** (Deployment Law step 6) — sessions run data actions against the **dev stack** in-session as their briefs require, but the production execution always waits for that window. Any brief with such actions (seed reruns, data fixup commands, `make seed` itself) must (a) list them in a dedicated **PENDING DEPLOY-TIME ACTIONS** block in its closeout, and (b) every subsequent brief/amendment in the same version carries a pre-flight line reporting whether prior pending actions executed on dev, until confirmed done; the block itself stays open until the production execution at release deploy. Verification treats unexecuted deploy-time actions as open items — never silently passed. **`make seed` is one of these**
- **Code first, data second:** when a brief ships both a behavior change and dependent seed data, the code deploys **before** the data action runs
- **Seed-owned replacements delete rows — say how many.** State the **expected deletion count as a number**; the closeout reports actual against expected
- **Test hygiene when a fixed string becomes a pool:** literal-pinning tests convert to pool-membership assertions with original intent preserved as explicit assertions, reported as a deviation in the closeout — never changed silently
- **No placeholders, ever, in anything the operator would hand-edit.** If a brief depends on a not-yet-existing fact (an issue number), wait for the fact — or use a **combined file-and-fix brief**: the session files the issues, captures numbers at runtime from `gh issue create` output, and proceeds, with a **HARD GATE** between filing and implementation (any deviation = stop, run the issues report, closeout explaining, zero code changes)
- Issue-touching work ends with the single instruction **"run the issues report"** — the hardened issues-report agent handles generation, commit, and push **on the current session's branch** (design → version branch; ops → main); briefs must not spell those steps out. (The agent definition's on-main pre-flight is updated to branch-awareness as part of the consolidation build-out.)
- Include exact model field names, types, defaults; exact repo-relative paths; all design rules that must not be deviated from
- Include a migration step explicitly whenever a model changes
- Include a verification section with specific testable steps; when a data table and prose disagree, **the table is authoritative**
- The architecture doc update goes last, gated: "This step is gated on all implementation and verification steps above being complete and passing." Specify exactly which sections change
- **Architecture doc file handling — create-or-update, always:** every implementation brief of a major version carries the same conditional step: **create** `Shyland_Architecture_vN.md` if absent (`git rm` the old, written header-first then one section at a time), **update in place** if present. Creation duty follows **first-to-execute, not brief number**. A point-release brief never creates a new file — in-place update, stamp to N.M, hash moves only for architectural changes
- **Standing implementation-brief requirements — never omit:**
  1. **Version constant.** The *first* implementation brief of a release bumps `SHYLAND_VERSION` to `"N.0-DEV"` (`"N.M-DEV"` for a point release) **as its opening act** — its own commit, pin test moved with it, followed by the version-start `make deploy-dev`; the closeout bumps to the release stamp. Later briefs state they leave it alone.
  2. **An in-session dev deploy — exactly `make deploy-dev`**, run from the worktree once implementation and verification pass (build + migrate against the local dev stack; never hand-roll the sequence). **Production is never deployed from an implementation session** — `make deploy-prod` is the operator's, from the main checkout, only after the version PR merges (Deployment Law). Dev-side data actions (e.g. `make seed`) run in-session against the dev stack; the production execution stays in the PENDING DEPLOY-TIME ACTIONS block for the operator's post-merge window.
  3. **An operator playtest checklist targeting the dev stack**, itemized — ready after the brief's `make deploy-dev`.
- **Never include removal/pruning steps for transient documents** — committed and left in place; the operator does all pruning
- **Operator stashes are apply-only** — `git stash apply` permitted only with line-for-line diff verification against the brief and experiment markers replaced by permanent issue-referenced comments; **never `drop`, never `pop`**
- **Binary documentation assets are never chased** — if a generated asset needs regenerating and no renderer is present, report it **stale in the closeout** and stop
- Closeout reports include the final commit hash
- Naming: major-version briefs `Shyland_V{version}_Brief_{N}_{Descriptive_Name}.md`; point-release briefs `Shyland_V{N}.{M}_Brief_1_{Descriptive_Name}.md`; amendments `..._Amendment_{M}_{Name}.md`; standalone ops docs `Shyland_Brief_{Descriptive_Name}.md`. Internal cross-references must match filenames
- World-geometry briefs include relocating characters to their spawn point as part of the reseed (spawn = the Heart until homes ship)
- Verify `DOCKER_HOST` before any deployment-touching session
- Skills vs agents: "how to do X" → skill; "go do X and report back" (own authority, own closeout) → agent

---

## Design-Session Conventions

- **Startup checklist (every design session):** declare the type → determine the branch (first session for the release? create `version_N` from main and run version-start rituals; otherwise join the existing branch) → create the worktree → verify clean state → fetch the latest committed issues report → load these instructions. Design sessions start from verified state.
- **End ritual (every design session):** issues report committed to the version branch and pushed; end-state verified against the tracker before closing.
- Decisions are served with lean rationale and a confirm/deny surface; the operator rules, Claude recommends
- **GDD-first authoring:** section edits land as rulings settle; the operator reviews mechanics/balance edits in the conversation before commit. Creative content (names, lore, prose, flavor) is authored freely and deliberately *not* closely reviewed — the operator discovers it as a player; surface creative choices only when they have systemic implications
- **Visual MapFrag diagrams are REQUIRED for all world-layout design work** — rooms as nodes at their coordinates, edges, gates, changes highlighted. Draw the fragment before proposing changes
- Authored dialogue and descriptions must be audited for compass-direction accuracy before release (the geography audit rule)
- **Issue callouts:** whenever Claude believes something warrants a GitHub issue, it says so in a clearly visible **"Issue callout:"** and files it (with operator assent in-session). Every filed issue gets `--assignee "@me"` — the `KnightOfNight/@me` form is **not valid `gh` syntax**; never use it
- **The `triaged` label means cold-start-ready:** applied only when an issue carries complete diagnosis plus ruling sufficient for a brand-new session to pick it up with no other context; applied by the ruling session in the same motion as the ruling, never on personal judgment. It is RARE — even operator-directed filings with stated direction may deliberately stay untriaged
- **Access failure = blocker:** when repo state can't be read or is ambiguous, flag it explicitly and ask — never present an unverified assumption as fact
- **5-implementation-brief cap** and the bucket/bucket-split rules above bind design sessions during planning

---

## Key Design Decisions — Never Re-Litigate These

These are settled. Do not suggest alternatives unless the operator explicitly opens the topic.

| Decision | Detail |
|---|---|
| **Free forever** | No monetization, no premium currency, no real-money transactions of any kind. Ever. |
| **Items soulbound on equip** | No player-to-player item trading. Picking up transfers ownership but does not bind; the moment an item is equipped it becomes permanently soulbound. Super users can gift items; gifts become immediately soulbound to the recipient. |
| **Currency freely transferable** | Players can give each other currency. |
| **No off-body storage** | No banks, no stash, no mule accounts. Players carry what they carry. |
| **No hard level cap** | Infinite progression. Soft cap at content frontier. The Wastelands zone always scales to player level. |
| **Mk item system** | One base item definition per type, scaled by Mark tier (Mk 1 = levels 1–10, Mk 2 = 11–20, …). Instances generated at drop time with Mk tier and rarity applied. |
| **No housing** | Deferred to future version. |
| **No mounts** | Deferred to future version. |
| **No seasonal content** | Ever. World freshness comes from regular content updates only. |
| **English only** | v1 is English only. |
| **Single visual theme** | No colorblind or high-contrast mode in v1 — which is why direction and state are always carried by words, never color alone. |
| **Fixed combat ticks** | 3-second rounds, 1-second engine tick. No per-player adjustment. |
| **PvE default, PvP opt-in** | PvP only in rooms/zones explicitly flagged for it. Entering requires player confirmation. |
| **Screen reader compatible** | Non-negotiable from day one. ARIA live regions on the output pane. All functionality keyboard-accessible. |
| **Web only** | Responsive down to phone screen. No native app in v1. |
| **No auction house** | Ever. Items are soulbound; there is nothing to trade. |
| **Artifact items are unique** | One-of-a-kind hand-authored items outside standard generation. |
| **One character per account** | Exactly one Shyland character per account. No slots, no alts. |
| **No portraits** | Character creation is Origin, Archetype, and Name only — cut, not deferred. |
| **Character name defaults to gamer tag** | Pre-fills from `user.profile` gamer tag (username fallback, truncated to 20). Override allowed with live case-insensitive uniqueness checking (DB constraint) and a public-library profanity filter; only a kept, set gamer tag is exempt. `Character.name` is independent of later gamer-tag changes and renders **verbatim casing** everywhere. |
| **Exits are transitions, not doors** | The world changes around the player. MapFrags start a new drawing on the far side; the exit itself always works. |
| **Unified output pane, clears per room** | One pane carries everything; it resets on each room entry (ruled deliberate). Place identity lives in the location bar; a zone-colored separator frames each room render. No bracketed in-pane room header. |
| **Timestamps mark events, not renderings** | Every message carries `ts`/`seq`; only event categories display the prefix. Setting changes are events; reports and renderings are not. |
| **Directional combat arrows** | Designed, reviewed, ABANDONED in v20 — not deferred, not tracked. |
| **The bar law** | Fill fraction is invariant under every max-changing mutation (equip, unequip, spend) via one atomic rescale; nothing refills. Level-up keeps its full refill. |
| **Quit allowed in combat** | Combat continues after quit — the player can die logged out. Tab-closing and quitting are identical in cost. `flee` remains the only exit *from* combat. |
| **Chart-as-license** | The color chart is the license to use a color, not a description; off-chart literals are defects, enforced by set-equality test. |
| **Scope law (gear wiring)** | Wire only what combat reads; build nothing for absent systems; leave no landmines for them either. Inert stats stay visible (zeros never hidden). |
| **Seed authority** | "The code is definitive" — reseeding is enforce-exact; live-DB edits are emergency mitigations only. |
| **Data into models over hardcoded dicts** | Configurable data belongs in models (Origin acuity values, Zone/Area theme colors, NPC articles). |
| **Speech gets pooled; renderings stay stable** | Any line the world *says* more than once has a pool of at least three; reports, captions, and summaries are renderings and never vary. Speech is attributed (`Name: text`, say-color); narration is not (verbatim, ambient voice, no connective). |
| **The color doctrine** | Gold is speech. Green is what went your way — their misses, every kind of loot. Yellow is your whiff and the world declining. The reds are damage, by direction. Value-color is the world: content, narration, ambient. Muted is true chrome only. Borders are zone-theme territory; transient state speaks through backgrounds and text, never the frame. |
| **Disengagement costs the damage** | A combat session ending without a death restores its NPCs to full. Chip-and-run is dead by ruling; a boss is one sustained engagement or nothing. |

---

## The Three Bars

Characters have three resource bars — not two, not one. All three are in the data model from day one.

- **Vitality** — the body right now. Low = slower, hits softer, takes more damage. Zero = Dying state.
- **Acuity** — the mind's dynamic state. Not a sanity meter. Each Origin has a baseline and an optimal band (rendered as the stats-pane band gauge). Too LOW = spells fizzle, aim drifts, awareness collapses. Too HIGH = hyper-focus, single-target bonus but flanking enemies undetected. Band-relative and deviation-based since v19.
- **Longevity** — the slow burn. Controls stamina duration, DoT/HoT durations, sustained effect windows. Recovers slowly. **Note: nothing drains it yet** — its first consuming mechanic is filed as #70, a features-version question.

---

## The Tech Stack

- **Backend:** Django 5 (Python) · **Real-time:** Django Channels + Daphne (ASGI) + WebSockets
- **Database:** PostgreSQL 16 · **Cache/channel layer:** Redis 7
- **Deployment:** Docker Compose (nginx → Daphne → Django/Redis/Postgres) on a single EC2 instance; production at `games.magrathea.com`; deploys bounce all three games in the repo
- **Client:** Vanilla JS, responsive HTML/CSS, no framework dependency
- **Auth:** Django built-in auth with the shared `user.profile` gamer tag system

All game logic runs server-side. The client is a dumb terminal: it renders server-sent semantic categories and payloads (map, fight, state sync) and is never trusted for game state. Every outbound message passes one delivery choke point carrying the `ts`/`seq` envelope — the future firehose tap.

---

## Currency System

All currency stored as a single `BigIntegerField` named `copper` on the Character model. Display and conversion via `apps/shyland/currency.py`. Never store silver, gold, or platinum as separate fields.

| Tier | Name | Value in Copper |
|---|---|---|
| 1 | Copper | 1 |
| 2 | Silver | 10 |
| 3 | Gold | 1,000 |
| 4 | Platinum | 1,000,000 |
| 5+ | Future | Continues the pattern |

Local zone currency is a display alias only. Every player-facing amount goes through the tier formatter.

---

## Item System

Definition/instance split: **ItemDefinition** (the template, never changes at runtime) and **ItemInstance** (a physical copy generated at drop time with Mk tier, rarity, and rolled stats).

**Display (v20/v22):** rarity lives in the trailing status flag block, never in the name — `Iron Mace Mk 1 — 100% durability [Uncommon, Unbound]` (`Bound` = soulbound by any route; `Unbound` = transferable). One shared composition helper renders every item line. Rarity colors apply to the flag block only; rarity words are rarity-colored wherever item names render in information output. Tier-material names (copper/silver/gold/platinum) suppress the Mk suffix; flavor materials don't. **Gear is combat-live (v22, #100):** effective stats (base + equipped gear) on every gameplay read; Option C armor (slot weight × Mk + rolled physical_resist = TAV, curve TAV/(TAV+48), NPC→player only); proc factors (`bleed/stun/poison_factor`) roll per item per landed hit; the bar law — fill fraction invariant under every max-changing mutation, nothing refills.

**Command grammar (v20/v22):** `<verb> [all | N] [rarity] [noun]` plus `N.noun` — ordered token-prefix matching on the visible name+tier, plural fallbacks, cross-definition refuse-lists, rarity-aware protective selection, equipped items excluded from sell/drop. One resolver serves every noun-taking command; tab completion is server-authoritative and completes exactly each pool. **The v22 command chart (GDD §9.1) is law** — four types, stable-numbered footnotes, the three-layer response doctrine (CLI error red / world-declined warn / world-answered), the central state-gating matrix (quit allowed in combat; combat continues after quit), resolution pools with the player/NPC name invariant, the settings standard (brief off / echo on / timestamps on), and the `admins.shyland` stealth gating for `sudo`/`last`. GDD §9 is the single authoritative command reference, synced to the dispatch table at closeout.

**Stacking (v23, #18):** consumable, material, readable, and key stack; weapon, armor, accessory, and bag never do. The grouping key is definition + Mk tier + rarity + **soulbound state** — a display fold only; the inventory stays a flat pool of instances. **Zero-value disposal (v23, #138):** vendors accept worthless items for exactly 0 copper (the bound starter kit's only exit); Artifacts are refused generically under the **no-leak rule** — refusal speech never names or implies rarity, tier, or true name.

Rarity secondary slots: Common 0 / Uncommon 1 / Rare 2 / Epic 3 / Legendary all-in-pool / Artifact hand-authored; slots = min(rarity's slots, pool size). Stat midpoint = `scaling_base + (scaling_factor × mk_tier)`. Weapon damage = midpoint + spread (spread is weapon identity; rarity shifts midpoint only). Durability bands: 75–100% none / 50–75% 25% / 25–50% 35% / 1–25% 50% / 0% non-functional; repair success scales with current durability. Shared EffectDefinition/EffectComponent vocabulary. Cursed items hidden until equipped or identified. Bags add carry capacity; flat inventory pool. **Identification note:** items default identified; drop currently re-veils (a v18 trapdoor — the ruled redesign is #80: knowledge by holding, examine reveals without pickup, pickup unlocks).

---

## World Hierarchy & The Map

```
Zone → Area → Room
```

Zones are genre-distinct; Areas optional named groupings; Rooms atomic. Zone and Area carry authored `theme_color` model fields feeding the location bar, output names, and the room separator.

**Location bar:** `Zone: Area: Room` (Area omitted when absent), theme-colored, one line, Area truncates first. The output pane shows no room header.

**The map (v20/v22 Maps V2):** room coordinates are per-zone **map-space** (z ≠ elevation); unflagged cardinal exits must land grid-adjacent (seed-enforced invariant); per-exit boundary flags mark deliberate seams; up/down always break the map. A **MapFrag** — derived, never stored — is the connected component one drawn map shows. Fog-of-war via RoomVisit, recorded at arrival in every path. The client map is a fixed 300×300 SVG, north-up, aria-hidden — a 7×7 window in a pinned 16px margin on the four-color vocabulary (key-color here-dot, value known, muted unknown, agro strokes); octagons for travel nodes (never agro, seed-enforced); frontier rooms as half-diameter muted dots **masked by construction** to `{x, y, discovered: false}` in the payload; the build is a bounded five-query constant. **Visual MapFrag diagrams are required for all map design work.**

---

## Zones Reference

| ID | Name | Genre | Danger |
|---|---|---|---|
| Z01 | The Verdant Reach | Fantasy wilderness | Beginner (LIVE — 150 rooms, complete) |
| Z02 | Ashenveil Cathedral | Dark gothic horror | Intermediate |
| Z03 | The Neon Sprawl | Cyberpunk megacity | Intermediate |
| Z04 | The Blasted Flats | Post-apocalyptic | Advanced |
| Z05 | The Convergence | All genres — central hub | Sanctuary (LIVE — 60 rooms, ring closed in v20) |
| Z06 | The Iron Deeps | Steampunk underground | Advanced |
| Z07 | The Pale Shore | Cosmic horror | Endgame |
| Z08 | The Wastelands | Post-apocalyptic, infinite scaling | All levels |

The Convergence is the starting room, social hub, and default recall destination. PvP disabled. Next zone build (Z02 or Z03) belongs to a future EVEN version per the cadence.

---

## Origins Reference

Acuity values use the GDD's decimal scale (`Origin` model fields). This table must always match the GDD; the GDD is authoritative if they diverge.

| Origin | Flavor | Acuity Baseline | Band Low | Band High |
|---|---|---|---|---|
| Highborn | Fantasy noble | 1.0 | 0.85 | 1.15 |
| Feral | Wilderness/tribal | 0.95 | 0.80 | 1.10 |
| Streetborn | Cyberpunk | 1.0 | 0.85 | 1.15 |
| Irradiated | Post-apocalyptic | 0.90 | 0.75 | 1.05 |
| Undying | Gothic/undead | 0.80 | 0.65 | 1.00 |
| Machinekind | Steampunk construct | 1.05 | 0.90 | 1.20 |
| Voidtouched | Cosmic horror | 0.70 | 0.40 | 1.30 |

## Archetypes Reference

| Archetype | Role | Primary Stats |
|---|---|---|
| Blade | Melee DPS | STR, DEX |
| Bulwark | Tank | STR, END |
| Shade | Stealth / burst | DEX, INT |
| Conduit | Magic/tech ranged DPS | INT, WIS |
| Warden | Healer / Acuity manager | WIS, END |
| Gunner | Ranged DPS | DEX, PER |
| Machinist | Pet / construct / turret | INT, DEX |
