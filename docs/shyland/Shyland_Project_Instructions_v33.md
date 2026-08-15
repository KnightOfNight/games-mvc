# Shyland Project Instructions v33

**Status: ACTIVE — approved by the operator 2026-08-15. Supersedes Shyland_Project_Instructions_v32.md.**

These instructions govern every Claude Code session doing Shyland work, of every type. Read them at the start of any Shyland session. **The document's version is an independent counter, decoupled from the game version (operator ruling 2026-07-27):** every refresh that changes process rules produces the next-numbered edition, whenever that happens; the highest-numbered edition is always the active one. This decoupling applies to the instructions doc only — the GDD and architecture doc remain in game-version lockstep. This v33 edition is the prod-verification ruling pass (#248): every PENDING DEPLOY-TIME ACTIONS step must name an executor at design time; permanent data-shape invariants ride seed verification; read-only prod inspection steps are handed to the operator until the sanctioned `make verify-prod` target ships (#249). It also codifies two queued rulings: the architecture-doc ops-lane extension of the errata rule (#242) and the errata-filing pre-authorization. (v32 the gift-language pass; v31 the seed-prod pass; v30 the label model; v29 the release model; v28 the playtest-disposition gate; v27 the GDD-errata rule; v26 the end rituals; v25 the closeout session type.)

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

**Main is the state of record, not necessarily what's running.** Main's GDD always describes the released game; unshipped design exists only on version branches. (Deployment follows the same law: the **dev stack** runs branch builds during development and hosts all playtests; **production runs main only** — see Deployment Law.) Within a version branch, GDD sections describing rulings whose implementation hasn't landed yet may carry a "(vNN, pending implementation)" marker as an intra-branch courtesy. **Marker removal is design-session work mid-release, closeout work at the end** — implementation sessions never edit GDD source, markers included: the next design session sweeps markers whose implementation has landed (a startup agenda item), and the closeout session sweeps its own release's remaining markers as version bookkeeping (parenthetical deletion only, verified against the landed implementation — operator-ruled 2026-07-27).

**GDD errata (operator-ruled 2026-07-29, #169):** when the GDD is wrong about **shipped** behavior — the game is right, the docs are out of date — the correction is **ops work on main**: one operator-directed ops session per erratum issue. The session corrects the affected section files to match shipped behavior, runs `make gdd`, commits directly to main (ops is main's exception lane — no PR), closes the issue, and runs the issues report. **No version, no stamp move, no changelog row** — the stamp still truthfully names the shipped game, now described accurately; git history is the provenance. **The gate is the erratum test:** describing what shipped = erratum (ops may do it); describing anything not shipped, or any question requiring a design ruling, = design content (version branch only, never main) — the moment a ruling is needed, the ops session stops and says so. This is deliberately not a new session type and not a conditional on design sessions. **The lane extends to the architecture doc (operator-ruled 2026-08-13, recorded on #242):** arch-doc factual corrections passing the **technical-writer test** — no new technical content, no design change, the header hash untouched — are ops-lane under the same contract (correct on main, no stamp move, git history is the provenance).

---

## Session Types — How Work Is Organized

Every Shyland session has an operator-declared type. The type bounds what the session may touch (also codified in CLAUDE.md Rule 3):

| Session type | Runs on | May touch | Never touches |
|---|---|---|---|
| **Design** | Version-branch worktree | GDD source, GitHub issue state, design/planning docs, briefs (writes and commits them) | Game code, migrations, seed data, deployment |
| **Implementation** | Version-branch worktree (operator supplies the branch name) | Game code, tests, seed data, migrations, architecture doc (final gated step), dev-stack deploys (`make deploy-dev`) | GDD source (reads, never writes; `make gdd` / brief-directed mechanical ops only); production deploys — `make deploy-prod` is operator-run, from main, post-merge (Deployment Law) |
| **Ops/housekeeping** | `main` | Issue-state clerical work, issues reports, process docs, operator-directed GDD errata (docs wrong about shipped behavior — see GDD Errata under Documents) | Game code, GDD design content, deploys of any kind |
| **Closeout** | Version-branch worktree; the main checkout for the post-merge tail | Version bookkeeping only: doc stamps (GDD changelog row/header/index, arch-doc stamp line), the release's landed "(pending implementation)" markers, the **stamp whitelist** (`SHYLAND_VERSION` line + its pin-test assertion), `make gdd`, the version PR, the operator-permitted merge, and the tail's one-time-go-ahead prod deploy | Game code beyond the whitelist, game design content, seed data, migrations |

**Session quantities per release (operator-ruled 2026-07-27):** one or more **design** sessions — the first bootstraps (creates the branch, begins triage) but holds no special status; every design session is standalone apart from that bootstrap. One or more **implementation** sessions — no bootstrap; they work directly on the branch. **Exactly one closeout session.** Mechanical constraint, not process: one branch = one worktree = at most one session active in it at a time. **Implementations run serially — doctrine, not accident (operator-ruled 2026-07-29, #170):** briefs often build on each other, and the dev stack is a shared singleton — only one brief's build owns it at a time. (The deferring disposition, below, is the escape hatch when the operator wants a session ended before playtesting.)

**Session end rituals (operator-ruled 2026-07-27, #160):** every session type has an end skill — `design-session-end`, `implementation-session-end`, `ops-session-end`, `closeout-session-end` — and **every session ends with its end ritual**; the operator's invocation is the positive confirmation of completion at every level (the closeout one deliberately overlaps the ritual's own closing step; consistency wins). Design and implementation end rituals terminate by committing an **issues report — the formal end artifact — unconditionally**, whether or not issues were touched; implementation end rituals additionally gate on the **operator playtest disposition** (#170) before anything else. **A closeout session fails hard, early, if any design or implementation session for its release has not formally ended:** an incomplete closeout-report stub, unpushed work, or content commits after the branch's last issues report each mean an unended session, and the closeout stops until the owning session type runs its end ritual. Start skills (`design-session`, `implementation-session`, `version-closeout`) are model-facing checklists — the operator typically opens sessions in natural language (session pickers lazy-load commands until after the first prompt) and the session self-invokes the right skill; ops sessions need no start ritual.

**Design sessions are the design-and-ruling environment** — brainstorming, system design, rulings, GDD maintenance, brief writing. **Implementation sessions are the build environment.** The firewall is absolute: implementation never invents design; design never touches code. **Closeout sessions touch neither** — their entire edit surface is the enumerated bookkeeping in the table above; the stamp whitelist exists because the version constant is a stamp that happens to live in a `.py` file, and it extends no further.

**Multiple design sessions per major version:** the first does the big coherent pass (system rulings, queue order); each release's design session is small (its ticket, its GDD text, its brief). Nothing carries between sessions except the issue tracker, the committed documents, and Claude Code's persistent memory — a session that needs context reads issues and repo docs, never another session's transcript. Each session verifies its own work from committed reports before handing off.

**Division of labor (the triage pipeline):** the operator files issues thin at the moment of discovery → triage fattens them (diagnosis comments; may add the `bug` label when genuinely confirmed — never milestones or version/grouping labels, never closes, never changes code during triage) → design sessions rule (major/grouping labels and release milestone, design direction, `triaged` label in the same motion) → briefs implement → committed reports verify.

---

## Branch Discipline — Main Is Protected

No doc or code changes land on main except via PR — the sole exceptions are ops/housekeeping work and absolute emergencies the operator declares.

**The version-branch lifecycle (a release is a release — major or point, same lifecycle):**

1. **The first design session for a release creates the branch** — named for the milestone, uniformly `version_N_M` (`version_24_0`, `version_23_1`), cut from current main — and runs the version-start rituals on it.
2. **Every later design session for that release joins the same branch** — new worktree, same branch. One branch per release, however many sessions it takes.
3. **Implementation sessions demand a branch name as their first act**, start a worktree on it, and find everything already there: committed briefs, updated GDD, prior code.
4. **Everything for the release accumulates on the branch** — briefs, GDD edits, code, tests, arch doc, closeout reports, design-session issues reports — and merges to main as **one version PR at closeout**, reviewed and merged by the operator.
5. The point-release **scope law** (below) constrains what goes on a point-release branch, not how the branch works. Any in-flight branch **merges main forward** after another release lands (never a rebase — Deployment Law).

Notes: issue state is not git — rulings, labels, and filings hit GitHub live from any session regardless of branch. Issues reports fork by session type: design sessions commit theirs to the version branch, ops sessions to main; timestamped filenames never collide at merge. Worktree env files are automated: the committed `post-checkout` git hook (activated per clone via `make hooks`) copies `.env.dev`, `.env.prod`, and `ssl/` from the main checkout into every new worktree and initializes `.env` in **dev posture** (`.env.dev`). Design-session worktrees never use them (they never build or deploy); implementation worktrees get them ready-made — and still sanity-check `DOMAIN` before any deploy.

---

## Deployment Law — Dev and Prod (operator-ruled 2026-07-26, #156)

Two invariants, absolute:

1. **Production runs `main` — nothing else, ever.** `make deploy-prod` runs from the **main checkout**, only **after** the version PR has merged. Never from a worktree; never with unmerged code; and never invoked by a Claude session **except** in the closeout session's tail on the operator's one-time, in-conversation go-ahead — one exact occurrence, no future permission implied (the permission layer is a backstop, not the decision point).
2. **`main` never contains a `-DEV` suffix in `SHYLAND_VERSION` — on any commit, at any time.** `-DEV` exists only on version branches, between the version-start bump and the closeout stamp. A version PR whose tip still reads `N.M-DEV` is not mergeable; the closeout stamp step is the gate that makes it so.

The flow every release follows (major `N.0` or point `N.M` alike):

1. **Version start** (first implementation brief, opening act): bump `SHYLAND_VERSION` to `N.M-DEV` in its own commit (the pin test moves with it), then `make deploy-dev` from the worktree.
2. **Every brief deploys to dev**: `make deploy-dev` from the worktree once implementation and verification pass. The dev stack is where the release lives during development.
3. **All operator playtests run on the dev stack.** Brief playtest checklists target dev; production hosts no mid-version builds.
4. **Closeout stamps on the branch**: `N.M-DEV → N.M` before the PR opens, alongside the doc stamps. The **-DEV gate**: no version PR opens while `version.py` reads `-DEV`.
5. **The version PR merges to main** (operator-reviewed).
6. **Production deploys in the closeout session's tail — nowhere else.** Gates: the complete closeout ritual is done including the operator's merge, and the dev stack is running the stamped release build (no `-DEV`). The session moves to the **main checkout** (a directory change — the main checkout always sits on `main`), syncs, verifies the merged tip, and reports ready. On the operator's **one-time go-ahead**, the session runs `make deploy-prod` (the fully automated target). **That go-ahead authorizes exactly that one deploy — it implies no future permission, ever.** Absent a go-ahead, the session ends with "ready for operator deploy" and the operator runs the command personally. Deploy-time data actions (seed reruns, fixups) execute against production in this same window — PENDING DEPLOY-TIME ACTIONS blocks stay open until this point. **The sanctioned path for the production seed is `make seed-prod` (#187)**: self-contained posture handling in the deploy target's exact contract (pins its own `DOCKER_HOST`, refuses an ambient one, flips posture, seeds, restores resting posture; partial failure leaves prod posture for a human), invoked **bare only** on its own operator confirmation — sessions never hand-flip posture to run data actions, and `make seed` from resting posture targets dev, never production. No other session type — ops/housekeeping included — may ever invoke or host the prod deploy. **Read-only production inspection currently has no sanctioned session path** (#248): until `make verify-prod` ships (#249), a brief's prod-side verification step names the **operator** as executor and the closeout reports it handed off, not done; permanent invariants ride the seed's verification pass instead (see the executor checkpoint under Brief Writing Rules).

**Main moves mid-release → merge forward, never rebase.** When main advances while a release is in flight (ops work, another release landing), bring it into the version branch with an ordinary `git merge main` from the worktree. Published branches are never rebased or force-pushed. In particular, process-doc changes on main (instructions, skills) must be merged into the branch **before** the next session that depends on them runs there — worktree sessions read process docs from their own checkout.

---

## Versions, Issues, and Cadence

- **Issue-first law:** every item entering version planning has a GitHub issue number before design work begins. Rulings and briefs reference issue numbers. Design history lives in the issue tracker (rulings recorded as issue comments at the moment they're made, by the design session itself); the GDD's changelog carries one comprehensive row per closed version.
### The Release Model (operator-ruled 2026-07-29, #173)

**"We're just always shipping out a constant stream of point releases one after the other, sometimes incrementing the major number too."** (operator, verbatim — this sentence is the model.)

- **There is one kind of release.** Every release is a point release running the identical lifecycle: design session → committed brief → implementation → playtest disposition → closeout session → operator merge → tail deploy. Nothing else ships anything.
- **A bump in the major number indicates a significant change in the game** — one or more new features with a name (Version 24 = new-zone-prep; Version 25 = new zones). It rides an otherwise-ordinary release as `N.0`, whose closeout additionally runs the **major-opening mechanics**: `GDD_MAJOR` bump, monolith rename to `Shyland_GDD_vN.md`, old monolith `git rm`'d. (These moved here from the retired end-of-version ritual — main's GDD carries the major's name from the major's first day.)
- **A change in the minor number is related to the current design: a bug fix or continued development under the current major** — the major's feature parts, amendments, bug fixes (which never wait for anything), small features to existing functions, and prep work for the next major. **Litmus: maps were a major version; adding percentage-seen to maps is a point release.**
- **There is no cadence.** Majors happen whenever something big is in the works. The even/odd feature/fix alternation is retired (2026-07-29).
- **There is no end-of-major ritual.** Every release closes itself completely; a major ends by implication when the next major's `N.0` ships. The major's queue is drained when no open issue carries its label unshipped (deliberate stragglers are relabeled to the next major or a capability label) — the shipping release's changelog row notes it, and that's the whole event.
- **Numbering:** M is a **minor version number, not a decimal** — 21.5 < 21.15, ordering numeric on M.
- **Labels and milestones (operator-ruled 2026-07-30, #175 — crisp gates, small permanent namespace):** the two GitHub axes carry the two kinds of fact. **Permanent membership = label; shipping release = milestone.**
  - **Major membership is a permanent label** — `V24`, `V25`, … — applied when an item is triaged into the major, never removed; the label is the major's plan of record and the queue the release stream drains, and the whole era stays queryable forever (`--label VN --state all`). **No major-level milestone exists.**
  - **Milestones are shipping releases only:** each release gets its `Version N.M` milestone — born with its design session, holding the founding ticket plus dependencies only, closed at closeout (the entry gate's "milestone closed N/N" query). Names are exactly `Version N.M`.
  - **Every other permanent grouping is a label too** — capabilities (`healing-economy`, `authentication`, `firehose-logging`) and content groups (zone builds `Z02`–`Z08`). An issue may carry a major label, grouping labels, and its shipping release's milestone simultaneously — full history survives shipping.
  - **Queue order is not encoded in the tracker** — neither labels nor milestones order issues. Order lives where it always effectively lived: design-session rulings ("next founding ticket"), recorded on issues.
  - The first design session of a new major re-triages the major's labeled queue against the theme (off-theme issues lose the label — moving to a capability label or none — and ship as ordinary point releases whenever chosen).
- **Scope law (every release):** **one founding ticket, one implementation brief.** Additional tickets only as dependencies (`gh --blocked-by`) describing the same problem, never widening it. Work too big for one brief becomes two releases. Mid-build discoveries file thin into the normal pipeline.
- **Design runs ahead of the release stream:** system-wide design happens whole — rulings recorded on issues (the tracker is version-independent) and queue order ruled — while GDD text lands only with the release that ships it. A major's first design session typically does the big coherent pass; later design sessions are small: next ticket, its GDD text, its brief.
- **Branch names are uniformly `version_N_M`** (24.0 → `version_24_0`); in-flight branches merge main forward after another release lands (never a rebase).
- **Ruling immediacy:** when a ruling changes triage or issue state, the design session records it on the issue immediately — GitHub follows the design conversation in real time, never batched. (Playtest findings may be *ruled* immediately and *batched* into one consolidated amendment for a single implementation round trip.)
- **"Defer" means:** not now, plus a GitHub issue (carrying a future major's label, a capability label, or no label for someday).
- **Retired (2026-07-29, #173):** the even/odd cadence; the `B1`–`B5` bucket labels (dormant on GitHub, never deleted — closed-issue history preserved); the 5-brief-per-major cap (the per-release scope law is the discipline mechanism).
- **Retired (2026-07-30, #175):** all grouping milestones — the `Version N` major queue plus capability and zone milestones (emptied into their labels and closed, never deleted).

---

## Workflow — The Release Lifecycle

**1. Design sessions rule and author.** Rulings are recorded on their issues in the same conversation, immediately. GDD section files are updated **as rulings settle, before implementation** — GDD-first; the operator reviews mechanics/balance edits in-session (creative content flows under the creative-content policy). Briefs are written AND committed to the version branch by the design session. Every design session ends with the end ritual: issues report generated, committed to the version branch, pushed; end-state verified against the tracker before the session closes.

**2. Implementation sessions build.** The operator supplies the branch name and directs a brief by name. **Step 0 (verify-and-signal):** confirm the directed brief exists verbatim at the branch tip (it was committed by its design session; whitespace-only drift is report-and-accept), then create the brief's closeout report as a **stub** — the `.txt` file opening with a one-line session-start record (date, brief name, branch) — commit it, and **push immediately**: that push is the work-has-started signal, a defined artifact rather than whatever work commit happens first. The stub is completed in place at closeout. Thereafter it commits and pushes at every step boundary — branch only, never merging on its own initiative. It implements, runs verification, closes the brief's issues (gated on verification passing), updates the architecture doc as the **last, gated step**, commits its **closeout report** as a `.txt` in `docs/shyland/`, and ends with the `implementation-session-end` ritual — which **first requires an explicit operator playtest disposition** (recorded in the closeout report; see step 4) and always runs the issues report (the formal end artifact), whether or not issues were touched.

**3. Verification from committed reports.** Post-implementation verification belongs to the **next design session for the release, as its first agenda item** (the design-session skill enforces this — the commissioning session is closed by the time implementation runs). It fetches the committed reports from the repo and verifies the end state against expectations — a required gate. Verify from committed reports, never a closeout narrative alone; report drift as a discrepancy list. Verification arithmetic states invariants ("exactly one issue added"), not absolute counts that go stale.

**4. Operator playtest.** Between briefs, per the playtest checklists, **against the dev stack** (production hosts no mid-version builds — Deployment Law). **An implementation session cannot end without an explicit operator playtest disposition (#170), recorded verbatim-style in its closeout report:** *"Operator reports playtest successful"* (terminal), *"No playtests for this brief"* (terminal — some briefs have no playtestable surface), or *"Operator deferring playtest"* (the session may end now, but the disposition is OPEN — the closeout entry gate treats it as a blocker and demands fresh operator attestation before proceeding; deferred never silently becomes done). Findings during playtest: a bug against the brief's own spec means the brief isn't done — fix in the still-open session, redeploy dev, re-playtest; design-level findings are filed and ruled as always, with fixes rolling into consolidated amendments.

**5. The closeout session (exactly one per release, major or point — the `version-closeout` skill is the runner):** operator-declared type; the session runs the gated ritual **in the version worktree**, every gate verified in order:

- **Session-end gate — fail hard, early, before anything else:** every design and implementation session for the release has formally ended (their end rituals). Checks on the branch as-is: clean and fully pushed; every brief's closeout report complete (a stub = an unended implementation session); the most recent non-merge commit is a committed issues report (the end rituals' terminal artifact). Any failure stops the closeout until the owning session ends properly — never patch the branch to make the gate pass.
- **Forward-merge first:** `git merge main` into the branch so the session reads current process docs and the PR carries no surprises.
- **Entry verification** — implementation is *done*, verified never assumed: every milestone issue closed, every brief's closeout report committed, **every brief's playtest disposition read from its committed closeout report** — "successful" and "no playtests" are terminal; **"deferring" is a blocker: the ritual stops until the operator freshly attests the deferred playtest in-conversation** (the late attestation is recorded in the closing report) — no dev-side deploy-time actions unexecuted. GDD content is complete before closeout by the GDD-first law — a design gap found here (an unruled change, an unswept mid-release marker outside this release) blocks the ritual and goes back to a design session.
- **Version bookkeeping:** GDD changelog row (on its own physical line) + stamp bumps (index + `_00_header.md`); this release's landed "(pending implementation)" markers swept (parenthetical deletion only, verified against the shipped code — zero prose changes), **ending with the sweep self-check: grep the GDD source for any remaining marker naming this release — nonzero means the sweep is not done (#173; the v23.3 closeout missed two and only the next design sessions' startup sweeps caught it)**; architecture doc stamp (hash moves only for architectural changes); the **stamp whitelist** — `SHYLAND_VERSION` → release stamp with its pin-test assertion moved in the same commit. `N.0` releases additionally (the major-opening mechanics): `GDD_MAJOR` bumped, monolith renamed, old monolith `git rm`'d. `make gdd` rebuild always.
- **Final proof on dev:** rebuild the dev stack from the stamped source and run the full in-container suite — dev now runs exactly the build prod will get, with no `-DEV` anywhere.
- **-DEV gate** (the constant line carries no `-DEV`) → push → **the version PR**.
- **The merge:** on a fresh, single-use, in-conversation operator permission — the ask always presents **squash vs merge-commit** as an explicit choice. Branches are never deleted.
- **The tail:** the session moves to the **main checkout**, syncs, verifies the merged tip — then Deployment Law step 6: prod deploy on the operator's one-time go-ahead (or "ready for operator deploy" if none is given), including any pending production-side data actions.
- **Close:** project instructions refreshed (next `vN`) if process rules changed; transient documents pruned **by the operator only**; Claude Code project memory updated; closing report; the session ends with `closeout-session-end` — the positive confirmation, like every session type.

**The GDD is authored by design sessions. The architecture doc is authored by implementation sessions.** These are not interchangeable. Implementation sessions never author or edit GDD source; their only permitted GDD operation is `make gdd` (or another mechanical operation explicitly directed by a brief). Ops sessions likewise — with the single exception of **operator-directed GDD errata** (the GDD Errata rule under Documents): corrections to shipped behavior, zero design decisions.

---

## Brief Writing Rules

- Briefs are self-contained — the implementation session reads only the brief (and the repo), never a design conversation
- Briefs are **born committed**: the design session writes the brief file into `docs/shyland/` on the version branch and commits it (standalone ops briefs are the exception: an ops session commits them to `main`). Pasted briefs are never actionable (CLAUDE.md Rule 4) — actionability = committed + operator-directed by name
- **Push cadence (every implementation brief):** commit and push at every step boundary — WIP-sized intermediate commits desired; **branch only, NEVER merge to main on the session's own initiative** (merging is the operator's action; operator-directed merges via the scoped `gh pr merge` allowance are standing capability, not a discrepancy)
- **Deploy-time data-action rule:** for production, "deploy time" means the **closeout tail's deploy window** (Deployment Law step 6) — sessions run data actions against the **dev stack** in-session as their briefs require, but the production execution always waits for that window. Any brief with such actions (seed reruns, data fixup commands, `make seed` itself) must (a) list them in a dedicated **PENDING DEPLOY-TIME ACTIONS** block in its closeout, and (b) every subsequent brief/amendment in the same version carries a pre-flight line reporting whether prior pending actions executed on dev, until confirmed done; the block itself stays open until the production execution at release deploy. Verification treats unexecuted deploy-time actions as open items — never silently passed. **`make seed` is one of these**
- **Executor checkpoint (#248, operator-ruled 2026-08-15): no step enters a PENDING DEPLOY-TIME ACTIONS block without a named executor** — a sanctioned posture-setting target (`make deploy-prod`, `make seed-prod`, and `make verify-prod` when it ships, #249), the seed's own verification pass, or **explicitly the operator**. A brief may not write a prod-side step no session can run. Classification rule: a **permanent data-shape invariant** ("nothing sits outside its rung") belongs in **seed verification** — it rides `make seed-prod`, executes on production for free, and re-running forever is a feature; one-time surveys do not go in the forever-pass. **Interim, until #249 ships:** a read-only prod inspection step is addressed **to the operator** as its named executor, and the closeout reports it **handed off, not done** — never unverified-by-surprise, never assumed clean
- **Code first, data second:** when a brief ships both a behavior change and dependent seed data, the code deploys **before** the data action runs
- **Seed-owned replacements delete rows — say how many.** State the **expected deletion count as a number**; the closeout reports actual against expected
- **Test hygiene when a fixed string becomes a pool:** literal-pinning tests convert to pool-membership assertions with original intent preserved as explicit assertions, reported as a deviation in the closeout — never changed silently
- **No placeholders, ever, in anything the operator would hand-edit.** If a brief depends on a not-yet-existing fact (an issue number), wait for the fact — or use a **combined file-and-fix brief**: the session files the issues, captures numbers at runtime from `gh issue create` output, and proceeds, with a **HARD GATE** between filing and implementation (any deviation = stop, run the issues report, closeout explaining, zero code changes)
- Issue-touching work ends with the single instruction **"run the issues report"** — the hardened issues-report agent handles generation, commit, and push **on the current session's branch** (design → version branch; ops → main); briefs must not spell those steps out. (The agent definition's on-main pre-flight is updated to branch-awareness as part of the consolidation build-out.)
- Include exact model field names, types, defaults; exact repo-relative paths; all design rules that must not be deviated from
- Include a migration step explicitly whenever a model changes
- Include a verification section with specific testable steps; when a data table and prose disagree, **the table is authoritative**
- **In-container test invocation — the only working form:** `python manage.py test apps/shyland/tests` (directory-path form, run via `docker exec` in the django container). The label form `apps.shyland` crashes on the `apps` namespace package (`TypeError` in unittest's loader) and bare `manage.py test` discovers zero tests. Briefs and verification sections use the path form.
- The architecture doc update goes last, gated: "This step is gated on all implementation and verification steps above being complete and passing." Specify exactly which sections change
- **Architecture doc file handling:** the `N.0` release's brief **creates** `Shyland_Architecture_vN.md` (`git rm` the old, written header-first then one section at a time); every other release's brief **updates in place** — stamp to N.M, hash moves only for architectural changes
- **Standing implementation-brief requirements — never omit:**
  1. **Version constant.** The *first* implementation brief of a release bumps `SHYLAND_VERSION` to `"N.0-DEV"` (`"N.M-DEV"` for a point release) **as its opening act** — its own commit, pin test moved with it, followed by the version-start `make deploy-dev`; the closeout bumps to the release stamp. Later briefs state they leave it alone.
  2. **An in-session dev deploy — exactly `make deploy-dev`**, run from the worktree once implementation and verification pass (build + migrate against the local dev stack; never hand-roll the sequence). **Production is never deployed from an implementation session** — the prod deploy happens only in the closeout session's tail (Deployment Law step 6). Dev-side data actions (e.g. `make seed`) run in-session against the dev stack; the production execution stays in the PENDING DEPLOY-TIME ACTIONS block for the closeout tail's deploy window.
  3. **An operator playtest checklist targeting the dev stack**, itemized — ready after the brief's `make deploy-dev`.
- **Gift language (#246, operator-ruled 2026-08-15): never write "admin-gift" in a brief or playtest checklist.** Wherever a step grants an item and any step depends on generation-path behavior (Mk-mismatch guards, rarity slot logic, anything inside `generate_item_instance`), the checklist says **"gift via the shell helper"** — `generate_item_instance(definition, mk_tier, rarity, owner=character)`, the same path the `stock-playtest-items` skill mandates. The Django admin add form is direct ORM construction and bypasses generation guards **by design** (the documented residual gap); a checklist that routes the operator through it to test a guard produces a false failure report against working behavior. A step that deliberately exercises the admin-form bypass must say so explicitly.
- **Never include removal/pruning steps for transient documents** — committed and left in place; the operator does all pruning
- **Operator stashes are apply-only** — `git stash apply` permitted only with line-for-line diff verification against the brief and experiment markers replaced by permanent issue-referenced comments; **never `drop`, never `pop`**
- **Binary documentation assets are never chased** — if a generated asset needs regenerating and no renderer is present, report it **stale in the closeout** and stop
- Closeout reports include the final commit hash **and the operator playtest disposition** (#170: "Operator reports playtest successful" / "No playtests for this brief" / "Operator deferring playtest" — or similar; the closeout session reads this line as a gate)
- Naming: every release's brief is `Shyland_V{N}.{M}_Brief_1_{Descriptive_Name}.md`; amendments `..._Amendment_{M}_{Name}.md`; standalone ops docs `Shyland_Brief_{Descriptive_Name}.md`. Internal cross-references must match filenames
- World-geometry briefs include relocating characters to their spawn point as part of the reseed (spawn = the Heart until homes ship)
- Verify `DOCKER_HOST` before any deployment-touching session
- Skills vs agents: "how to do X" → skill; "go do X and report back" (own authority, own closeout) → agent

---

## Design-Session Conventions

- **Startup checklist (every design session):** declare the type → determine the branch (first session for the release? create `version_N_M` from main and run version-start rituals; otherwise join the existing branch) → create the worktree → verify clean state → fetch the latest committed issues report → load these instructions. Design sessions start from verified state.
- **End ritual (every design session):** issues report committed to the version branch and pushed; end-state verified against the tracker before closing.
- Decisions are served with lean rationale and a confirm/deny surface; the operator rules, Claude recommends
- **GDD-first authoring:** section edits land as rulings settle; the operator reviews mechanics/balance edits in the conversation before commit. Creative content (names, lore, prose, flavor) is authored freely and deliberately *not* closely reviewed — the operator discovers it as a player; surface creative choices only when they have systemic implications
- **Visual MapFrag diagrams are REQUIRED for all world-layout design work** — rooms as nodes at their coordinates, edges, gates, changes highlighted. Draw the fragment before proposing changes
- Authored dialogue and descriptions must be audited for compass-direction accuracy before release (the geography audit rule)
- **Issue callouts:** whenever Claude believes something warrants a GitHub issue, it says so in a clearly visible **"Issue callout:"** and files it (with operator assent in-session — **except errata, whose filing is pre-authorized (operator-ruled 2026-08-13): never ask assent, file with the `errata` label and call out the number automatically**; this applies in every session type). Every filed issue gets `--assignee "@me"` — the `KnightOfNight/@me` form is **not valid `gh` syntax**; never use it
- **The `triaged` label means cold-start-ready:** applied only when an issue carries complete diagnosis plus ruling sufficient for a brand-new session to pick it up with no other context; applied by the ruling session in the same motion as the ruling, never on personal judgment. It is RARE — even operator-directed filings with stated direction may deliberately stay untriaged
- **Access failure = blocker:** when repo state can't be read or is ambiguous, flag it explicitly and ask — never present an unverified assumption as fact
- The **per-release scope law** (one founding ticket, one brief) and the **major's labeled queue** (`VN`) bind design sessions during planning; a major's first design session re-triages the labeled queue against the theme and rules its order

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

The Convergence is the starting room, social hub, and default recall destination. PvP disabled. The next zone build (Z02 or Z03) belongs to a future major version (Version 25 = new zones).

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
