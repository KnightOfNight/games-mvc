# Shyland Project Instructions v15.3

These instructions apply to every chat session in this project. Read them before responding to any message.

---

## What This Project Is

Shyland is a free, web-based Multi-User Dungeon (MUD) — a modern version of classic text-based telnet MUDs. It runs in the browser, is screen reader compatible, has no monetization of any kind, and is built on a Django/Channels/PostgreSQL stack.

The setting is a genre-collision world where dimensional rifts have pulled fragments of different realities together. A cyberpunk street samurai can appear in a woodland adventure zone. The anachronism is intentional and central to the game's identity.

---

## The Repo

**https://github.com/KnightOfNight/games-mvc**

This is the source of truth for all code and architecture. When asked about implementation details, fetch and read the repo before answering. Key locations:

- `django/src/apps/shyland/` — the Shyland Django app (models, consumers, currency, admin, templates)
- `docs/shyland/` — architecture and design documentation living in the repo
- `CLAUDE.md` — repo-wide orientation document (read this first in any Claude Code session)
- `Makefile` — all build and management commands

---

## Documents in This Project

The following files are uploaded to this project and should be read when relevant:

- **Shyland_GDD_vN.md** — the full Game Design Document. This is the authoritative source for game design decisions. When design questions arise, check here first.
- **Shyland_Architecture_vN.md** — the authoritative technical reference describing what is actually built. When implementation questions arise, check here first.

The versions of the documents are always in sync.

Multiple versions of the documents may be found in project files; the current
version is always the highest-numbered one.

The architecture document includes, in its header, the git commit hash of the
architectural changes, if any were made, in a version change. In this case
claude code will drive increment of the major version number stamp on the file
and remove the old one from git.

If there is a new version of the game that does not require architectural
changes, then there is no change to the git commit in the architecture
document, but its version stamp is still incremented along with that of the
GDD.

---

## How This Project Works

This Claude project is used for two things:

1. **Game design conversations** — brainstorming, designing systems, making decisions, and updating the GDD
2. **Preparing Claude Code briefs** — structured markdown documents that are downloaded and pasted into Claude Code sessions to implement specific features

Claude Code sessions run separately in the terminal. They are the implementation environment. This chat is the design environment.

---

## Workflow — Closing Out a Brief

Each Claude Code brief follows a complete lifecycle. This applies to every brief, not just item-related ones.

**1. Design happens here (this chat)**
Decisions are made, the GDD is the reference. Output is a Claude Code brief delivered as a downloadable markdown file. Always produce the brief as a file — never paste it inline in the chat.

**2. Claude Code implements the brief**
Claude Code runs in the terminal against the repo. It implements the brief, runs verification, and — only after all implementation and verification steps pass — updates the architecture document (`docs/shyland/architecture.md`) in the repo. The architecture doc update is always the last step and is gated on everything else being complete and tested.

**3. Close out here (this chat)**
After Claude Code is done and the repo is pushed:
- Upload the updated architecture doc to this project (replacing the previous version)
- Update the GDD here to reflect the finalized design
- Both the GDD and the architecture doc increment to their next version number
- Remove the old versions from the project

**The GDD is updated here. The architecture doc is updated by Claude Code.**

These are not interchangeable. The GDD describes design intent and decisions. The architecture doc describes what is actually built. Neither should be updated by the wrong party.

---

## Brief Writing Rules

When preparing a Claude Code brief:

- Briefs are self-contained — Claude Code reads only the brief, not this chat history
- Always deliver the brief as a downloadable markdown file, never inline in chat
- Include exact model field names, types, and defaults
- Include exact file paths relative to the repo root
- Include all design rules that must not be deviated from
- Include a migration step explicitly whenever a model changes
- Include a verification section with specific testable steps
- The architecture doc update section goes last, after verification, with an explicit gate: "This step is gated on all implementation and verification steps above being complete and passing"
- Specify exactly which sections of the architecture doc need updating and what they should say — Claude Code should not be making documentation decisions, only recording what was built

---

## Document Versioning Convention

**GDD:** Version number increments when design decisions change (v1 → v2 → v3). The current version is always the highest-numbered one in project files. When a new version is produced here, upload it to the project and remove the old one.

**Architecture doc:** Version is tracked by git commit hash in the document header. Claude Code updates the header to the new commit hash as part of every brief closeout. When a new version is uploaded to this project, remove the old one.

**Claude Code briefs:** Named to reflect their contents (e.g. `Shyland_Brief_Who_Presence.md`, `Shyland_Brief_Items.md`). Briefs are one-time documents — used once in a Claude Code session and not kept current afterward. They do not need to be retained in this project after the work is complete and closed out.

---

## Key Design Decisions — Never Re-Litigate These

These are settled. Do not suggest alternatives unless the human explicitly opens the topic.

| Decision | Detail |
|---|---|
| **Free forever** | No monetization, no premium currency, no real-money transactions of any kind. Ever. |
| **Items soulbound on pickup** | No player-to-player item trading. Items cannot leave the character who picked them up. Super users can gift items; gifts become immediately soulbound to the recipient. |
| **Currency freely transferable** | Players can give each other currency. |
| **No off-body storage** | No banks, no stash, no mule accounts. Players carry what they carry. |
| **No hard level cap** | Infinite progression. Soft cap at content frontier. The Wastelands zone always scales to player level. |
| **Mk item system** | Items named "Sword Mk 3" — one base item definition per weapon/armor type, scaled by Mark tier (Mk 1 = levels 1–10, Mk 2 = 11–20, etc., extending infinitely). Instances are generated at drop time with Mk tier and rarity applied. |
| **No housing** | Deferred to future version. |
| **No mounts** | Deferred to future version. |
| **No seasonal content** | Ever. World freshness comes from regular content updates only. |
| **English only** | v1 is English only. |
| **Single visual theme** | No colorblind or high-contrast mode in v1. |
| **Fixed combat ticks** | 3-second rounds, 1-second engine tick. No per-player adjustment. |
| **PvE default, PvP opt-in** | PvP only in rooms/zones explicitly flagged for it. Entering requires player confirmation. |
| **Screen reader compatible** | Non-negotiable from day one. ARIA live regions on output pane. All functionality accessible via keyboard. |
| **Web only** | Responsive down to phone screen. No native app in v1. |
| **No auction house** | Ever. Items are soulbound; there is nothing to trade. |
| **Artifact items are unique** | The Artifact rarity tier is reserved for one-of-a-kind hand-authored items that exist nowhere else in the game. They do not follow standard item generation rules. |
| **One character per account** | A player has exactly one Shyland character tied to their account. No character slots, no alts. |
| **No portraits** | Character creation is Origin, Archetype, and Name only. No visual avatar system — considered and explicitly cut, not deferred. |
| **Character name defaults to gamer tag** | Name pre-fills from the player's `user.profile` gamer tag at creation. Override is allowed, with live uniqueness checking as the player types and a profanity filter (well-maintained public library only, never a custom wordlist) that runs solely on overridden names. |

---

## The Three Bars

Characters have three resource bars — not two, not one. All three are in the data model from day one.

- **Vitality** — the body right now. Low = slower, hits softer, takes more damage. Zero = Dying state.
- **Acuity** — the mind's dynamic state. Not a sanity meter. Each Origin has a baseline and an optimal band. Too LOW = spells fizzle, aim drifts, situational awareness collapses. Too HIGH = hyper-focus, single-target bonus but flanking enemies undetected. Players can deliberately manipulate it.
- **Longevity** — the slow burn. Controls stamina duration, DoT/HoT durations, sustained effect windows. Recovers slowly. The hardest bar to manage over a long dungeon run.

---

## The Tech Stack

- **Backend:** Django 5 (Python)
- **Real-time:** Django Channels + Daphne (ASGI) + WebSockets
- **Database:** PostgreSQL 16
- **Cache/channel layer:** Redis 7
- **Deployment:** Docker Compose (nginx → Daphne → Django/Redis/Postgres)
- **Client:** Vanilla JS, responsive HTML/CSS, no framework dependency
- **Auth:** Django built-in auth; character name comes from `user.profile` (shared gamer tag system)

All game logic runs server-side. The client is a dumb terminal. It sends text commands and renders JSON output. Never trust anything from the client for game state.

---

## Currency System

All currency stored as a single `BigIntegerField` named `copper` on the Character model. Display and conversion are handled by `apps/shyland/currency.py`. Never store silver, gold, or platinum as separate fields.

Tier values follow an escalating-multiplier pattern:

| Tier | Name | Value in Copper |
|---|---|---|
| 1 | Copper | 1 |
| 2 | Silver | 10 |
| 3 | Gold | 1,000 |
| 4 | Platinum | 1,000,000 |
| 5+ | Future | Continues the pattern |

Local zone currency (e.g. "Soul Tokens" in Ashenveil Cathedral) is a display alias only — same math, different names, converts to copper on pickup.

---

## Item System

Items use a definition/instance split:

- **ItemDefinition** — the template. One per item type. Created by builders. Never changes at runtime.
- **ItemInstance** — a specific physical copy. Generated at drop time with Mk tier, rarity, and rolled stats applied.

### Rarity and secondary stats

| Rarity | Secondary stat slots |
|---|---|
| Common | 0 |
| Uncommon | 1 |
| Rare | 2 |
| Epic | 3 |
| Legendary | All in pool |
| Artifact | Hand-authored — not generated by standard machinery |

### Stat scaling

Midpoint = `scaling_base + (scaling_factor × mk_tier)`. Rarity determines the spread around the midpoint. Each ItemDefinition is self-contained with its own scaling parameters.

### Weapon damage

Stored as midpoint + spread. Spread is a weapon identity property (not affected by rarity). Rarity shifts the midpoint only.

### Durability

| Durability % | Performance penalty |
|---|---|
| 75–100% | None |
| 50–75% | 25% |
| 25–50% | 35% |
| 1–25% | 50% |
| 0% | Non-functional |

`takes_durability_loss` flag on ItemDefinition. Items without this flag never degrade. Repair success chance scales with current durability; at 0% repair is possible but very difficult.

### Effect system

A shared EffectDefinition and EffectInstance vocabulary used by consumables, curses, and combat effects. Effects have configurable magnitude and duration set at application time. The same effect type can be applied with different magnitude and duration depending on source context (combat vs. cursed item).

### Cursed items

Curse is hidden until equipped or identified (via NPC service or player skill). Cannot be unequipped until the curse is removed (Warden ability, NPC service, consumable, or timeout). Curse effects draw from the shared effect vocabulary.

### Bags

Bags occupy equipment slots and add a carry bonus to the character's total carry capacity. Cannot be unequipped if doing so would put the character over carry limit. Inventory is a flat pool — no manual slot management by the player.

---

## World Hierarchy

```
Zone → Area → Room
```

- **Zone** — genre-distinct region (fantasy, cyberpunk, gothic, etc.)
- **Area** — named grouping of rooms sharing a common atmosphere. Optional — not every room needs one. Area description is written once and shown in every room that belongs to it.
- **Room** — atomic unit. Has its own description, exits, flags, and contents.

Room header format: `[ Area Name — Room Name ]` when the room has an area, `[ Room Name ]` when it doesn't.

---

## Commands Currently Implemented

`look` / `l`, `north` / `n`, `south` / `s`, `east` / `e`, `west` / `w`, `up` / `u`, `down` / `d`, `say <text>`, `who`, `help` / `?`

When suggesting new commands, check Section 9 of the GDD for the full planned command list before proposing something that may already be designed.

---

## Zones Reference

| ID | Name | Genre | Danger |
|---|---|---|---|
| Z01 | The Verdant Reach | Fantasy wilderness | Beginner |
| Z02 | Ashenveil Cathedral | Dark gothic horror | Intermediate |
| Z03 | The Neon Sprawl | Cyberpunk megacity | Intermediate |
| Z04 | The Blasted Flats | Post-apocalyptic | Advanced |
| Z05 | The Convergence | All genres — central hub | Sanctuary |
| Z06 | The Iron Deeps | Steampunk underground | Advanced |
| Z07 | The Pale Shore | Cosmic horror | Endgame |
| Z08 | The Wastelands | Post-apocalyptic, infinite scaling | All levels |

The Convergence is the starting room, social hub, and default recall destination. PvP disabled. The Wastelands always scales to player level — it is the permanent endgame safety valve.

---

## Origins Reference

Acuity values use the same decimal scale as the GDD (`Origin.acuity_baseline`, `acuity_band_low`, `acuity_band_high`) — not a 0–100 scale. This table must always match the GDD; the GDD is authoritative if the two ever diverge.

| Origin | Flavor | Acuity Baseline | Band Low | Band High |
|---|---|---|---|---|
| Highborn | Fantasy noble | 1.0 | 0.85 | 1.15 |
| Feral | Wilderness/tribal | 0.95 | 0.80 | 1.10 |
| Streetborn | Cyberpunk | 1.0 | 0.85 | 1.15 |
| Irradiated | Post-apocalyptic | 0.90 | 0.75 | 1.05 |
| Undying | Gothic/undead | 0.80 | 0.65 | 1.00 |
| Machinekind | Steampunk construct | 1.05 | 0.90 | 1.20 |
| Voidtouched | Cosmic horror | 0.70 | 0.40 | 1.30 |

---

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
