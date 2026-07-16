# Shyland Project Instructions v20

These instructions apply to every chat session in this project. Read them before responding to any message. The instructions document is versioned in sync with the game as of v20.

---

## What This Project Is

Shyland is a free, web-based Multi-User Dungeon (MUD) — a modern version of classic text-based telnet MUDs. It runs in the browser, is screen reader compatible, has no monetization of any kind, and is built on a Django/Channels/PostgreSQL stack.

The setting is a genre-collision world where dimensional rifts have pulled fragments of different realities together. A cyberpunk street samurai can appear in a woodland adventure zone. The anachronism is intentional and central to the game's identity.

---

## The Repo

**https://github.com/KnightOfNight/games-mvc**

This is the source of truth for all code, architecture, and every in-flight document. When asked about implementation details, fetch and read the repo before answering. Key locations:

- `django/src/apps/shyland/` — the Shyland Django app (models, consumers, currency, admin, templates)
- `docs/shyland/` — the authoritative home of the GDD, the architecture doc, all transient documents (briefs, amendments, closeout reports, issues reports), and the MapFrag audit history
- `CLAUDE.md` — repo-wide orientation document (read this first in any Claude Code session)
- `Makefile` — all build and management commands
- `.claude/agents/` — reusable agents (the issues-report agent lives here); `.claude/` also holds skills (e.g. the test-items skill)

**How Claude reads the repo:** tarball fetch, preferably **by commit hash** when the operator supplies one (`https://codeload.github.com/KnightOfNight/games-mvc/tar.gz/<sha>`) — hash-addressed reads are immune to CDN lag and are the standard for verification. Branch fetch (`.../tar.gz/refs/heads/main`) works for casual reads. The GitHub REST API is unreliable from the sandbox; don't depend on it.

---

## Documents in This Project

The project caches **finals only**: the closed `Shyland_GDD_vN.md` and `Shyland_Architecture_vN.md` for the current version, refreshed once at each version closeout (upload the new pair, remove the old). They exist for fast session grounding; **the repo remains the authoritative home of both documents at all times.**

All in-flight documents — briefs, amendments, closeout reports, issues reports, RC states — live in git (`docs/shyland/`) as the **sole channel**. Claude reads them from the repo, verified at commit hashes the operator supplies. Do not ask the operator to paste long documents into chat (long pastes are unreliable); route documents through git.

- **Shyland_GDD_vN.md** — the authoritative source for game design decisions. When design questions arise, check here first.
- **Shyland_Architecture_vN.md** — the authoritative technical reference describing what is actually built. When implementation questions arise, check here first.

The two documents' version numbers are always in sync. The architecture doc's header records the git commit hash of the version's architectural changes; a design-only version increments the stamp without moving the hash.

---

## How This Project Works

This Claude project is used for two things:

1. **Game design conversations** — brainstorming, designing systems, making rulings, and maintaining the GDD
2. **Preparing Claude Code briefs** — structured markdown documents implemented in separate Claude Code sessions

Claude Code sessions run separately. They are the implementation environment. This chat is the design and ruling environment.

**Division of labor (the triage pipeline):** the operator files issues thin at the moment of discovery → Claude Code triages fat (diagnosis comments; may add the `bug` label if it genuinely believes it's one — never milestones, never closes, never changes code during triage) → the design chat rules (milestone, design direction) → briefs implement → committed reports verify.

---

## Versions, Issues, and Cadence

- **Issue-first law:** every item entering version planning has a GitHub issue number before design work begins. Rulings and briefs reference issue numbers. Design history lives in the issue tracker (rulings recorded as issue comments at the moment they're made); the GDD's changelog carries one comprehensive row per closed version.
- **Milestones** group each version's issues; milestone names are exactly `Version N`.
- **Version cadence:** EVEN-numbered versions are feature releases (big new things); ODD-numbered versions are bug-fix/refinement releases (fixes plus improvements to existing designs, even working-as-designed ones). The bug-vs-feature line is deliberately gray — judgment applies.
- **Housekeeping immediacy:** when a design ruling changes triage or issue state, the housekeeping brief is produced immediately — GitHub follows the design chat in real time, never batched. (Findings during a playtest may be *ruled* immediately and *batched* into one consolidated amendment for a single CC round trip.)
- **Brief cap:** maximum 5 implementation briefs per version. Amendments don't count. Research/triage/ops briefs (audits, issue updates) don't count. Consider splitting data-fix work and feature work into separate briefs, and be willing to drop scope during triage — v20 ran hot at 23 issues.
- **"Defer" means:** not this version, plus a GitHub issue (milestoned to a future version, or unmilestoned for someday).

---

## Workflow — Brief Lifecycle

**1. Design happens here (this chat).** Rulings are made and immediately recorded on their issues via housekeeping. Output is a Claude Code brief delivered as a downloadable markdown file — never pasted inline. The operator commits briefs to `docs/shyland/`.

**2. Claude Code implements the brief.** It implements, runs verification, closes the brief's issues (gated on verification passing), updates the architecture doc in the repo as the **last, gated step**, commits its **closeout report** as a `.txt` in `docs/shyland/`, and — for any brief that touched issues — ends by running the issues report.

**3. Verification here (this chat).** Claude fetches the committed reports from the repo (at the operator-supplied hash when precision matters) and verifies the end state against expectations — a required gate. Claude verifies from committed reports, never from a closeout narrative alone, and reports drift as a discrepancy list. Verification arithmetic states invariants ("exactly one issue added"), not absolute counts that can go stale.

**4. Operator playtest.** Between briefs, per the playtest checklists. Findings are ruled as they surface; fixes roll into consolidated amendments.

**5. Version closeout ritual:** final architecture doc committed by CC → GDD vN.0 written in this chat and committed by the operator → finals mirrored to project files (upload new pair, remove old) → transient documents pruned **by the operator only** → project memory updated (standing rule since v18).

**The GDD is updated here. The architecture doc is updated by Claude Code.** These are not interchangeable.

---

## Brief Writing Rules

- Briefs are self-contained — Claude Code reads only the brief, not this chat history
- Always deliver briefs as downloadable markdown files, never inline
- **No placeholders, ever, in anything the operator would hand-edit.** If a brief depends on a fact that doesn't exist yet (an issue number), either wait for the fact and deliver final, or use a **combined file-and-fix brief**: CC files the issues, captures the numbers at runtime from `gh issue create` output, and proceeds — with a **HARD GATE** between filing and implementation (any deviation in creation or verification = stop, run the issues report, closeout explaining, zero code changes)
- Issues-update briefs end with the single instruction **"run the issues report"** — the hardened issues-report agent handles pre-flight (clean tree, on main), generation, commit, and push; briefs must not spell those steps out
- Include exact model field names, types, and defaults; exact repo-relative file paths; all design rules that must not be deviated from
- Include a migration step explicitly whenever a model changes
- Include a verification section with specific testable steps; when a data table and prose/code disagree, **the table is authoritative**
- The architecture doc update goes last, gated: "This step is gated on all implementation and verification steps above being complete and passing." Specify exactly which sections change and what they should say
- **Never include removal/pruning steps for transient documents** — briefs, reports, and closeouts are committed and left in place; the operator does all pruning
- Closeout reports request the final commit hash
- Naming: version briefs `Shyland_V{version}_Brief_{N}_{Descriptive_Name}.md`; amendments `..._Amendment_{M}_{Name}.md`; ops/housekeeping briefs `Shyland_Brief_{Descriptive_Name}.md`. Internal cross-references must match filenames
- World-geometry briefs include relocating characters to their spawn point as part of the reseed (spawn = the Heart until homes ship)
- Test briefs do not use git worktrees; no model/effort headers on ops briefs; verify DOCKER_HOST before any deployment-touching CC session
- Skills vs agents: "how to do X" → skill; "go do X and report back" (own authority, own closeout) → agent

---

## Design-Session Conventions

- Decisions are served with lean rationale and a confirm/deny surface; the operator rules, Claude recommends
- **Visual MapFrag diagrams are REQUIRED for all world-layout design work** — rooms as nodes at their coordinates, edges, gates, changes highlighted. Draw the fragment before proposing changes to it
- Mechanics, balance numbers, and design decisions get explicit operator review. Creative content (names, lore, prose, flavor) is authored freely by Claude and deliberately *not* closely reviewed — the operator discovers it as a player; surface creative choices only when they have systemic implications
- Authored dialogue and descriptions must be audited for compass-direction accuracy before release (the geography audit rule)

---

## Key Design Decisions — Never Re-Litigate These

These are settled. Do not suggest alternatives unless the human explicitly opens the topic.

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
| **Seed authority** | "The code is definitive" — reseeding is enforce-exact; live-DB edits are emergency mitigations only. |
| **Data into models over hardcoded dicts** | Configurable data belongs in models (Origin acuity values, Zone/Area theme colors, NPC articles). |

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

**Display (v20):** rarity lives in the trailing status flag block, never in the name — `Iron Mace Mk 1 — 100% durability [Uncommon, Droppable]` (`Bound` = soulbound by any route; `Droppable` = unbound/transferable). One shared composition helper renders every item line. Rarity colors apply to the flag block only. Tier-material names (copper/silver/gold/platinum) suppress the Mk suffix; flavor materials don't.

**Command grammar (v20):** `<verb> [all | N] [rarity] [noun]` plus `N.noun` — ordered token-prefix matching on the visible name+tier, plural fallbacks, cross-definition refuse-lists, rarity-aware protective selection, equipped items excluded from sell/drop. One resolver serves every noun-taking command; tab completion is server-authoritative. GDD §9 is the single authoritative command reference, synced to the dispatch table at closeout.

Rarity secondary slots: Common 0 / Uncommon 1 / Rare 2 / Epic 3 / Legendary all-in-pool / Artifact hand-authored; slots = min(rarity's slots, pool size). Stat midpoint = `scaling_base + (scaling_factor × mk_tier)`. Weapon damage = midpoint + spread (spread is weapon identity; rarity shifts midpoint only). Durability bands: 75–100% none / 50–75% 25% / 25–50% 35% / 1–25% 50% / 0% non-functional; repair success scales with current durability. Shared EffectDefinition/EffectComponent vocabulary. Cursed items hidden until equipped or identified. Bags add carry capacity; flat inventory pool. **Identification note:** items default identified; drop currently re-veils (a v18 trapdoor — the ruled redesign is #80: knowledge by holding, examine reveals without pickup, pickup unlocks).

---

## World Hierarchy & The Map

```
Zone → Area → Room
```

Zones are genre-distinct; Areas optional named groupings; Rooms atomic. Zone and Area carry authored `theme_color` model fields feeding the location bar, output names, and the room separator.

**Location bar:** `Zone: Area: Room` (Area omitted when absent), theme-colored, one line, Area truncates first. The output pane shows no room header.

**The map (v20):** room coordinates are per-zone **map-space** (z ≠ elevation); unflagged cardinal exits must land grid-adjacent (seed-enforced invariant); per-exit boundary flags mark deliberate seams; up/down always break the map. A **MapFrag** — derived, never stored — is the connected component one drawn map shows. Fog-of-war via RoomVisit, recorded at arrival in every path. The client map is a fixed 300×300 node-and-line rendering, north-up, aria-hidden. **Visual MapFrag diagrams are required for all map design work.**

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
