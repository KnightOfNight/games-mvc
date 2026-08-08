# Shyland Issues Report

- Generated: 20260808T013050Z
- Repo: KnightOfNight/games-mvc
- Open issues: 38
- Closed issues: 144
- Dependency data: available

## Open Issues — Summary Table

| # | Title | Author | Labels | Milestone | Updated |
|---|---|---|---|---|---|
| 4 | Build Zone: Ashenveil Cathedral (Z02) | KnightOfNight | Z02 |  | 2026-07-30 |
| 5 | Build Zone: The Neon Sprawl (Z03) | KnightOfNight | Z03 |  | 2026-07-30 |
| 6 | Build Zone: The Blasted Flats (Z04) | KnightOfNight | Z04 |  | 2026-07-30 |
| 7 | Build Zone: The Iron Deeps (Z06) | KnightOfNight | Z06 |  | 2026-07-30 |
| 8 | Build Zone: The Pale Shore (Z07) | KnightOfNight | Z07 |  | 2026-07-30 |
| 9 | Build Zone: The Wastelands (Z08) | KnightOfNight | Z08 |  | 2026-07-30 |
| 10 | Transactional email via Postmark (password resets) | KnightOfNight | authentication |  | 2026-07-30 |
| 11 | Account onboarding via unusable password + reset link (no temp passwords) | KnightOfNight | authentication |  | 2026-07-30 |
| 12 | Two-factor authentication via TOTP (django-otp) | KnightOfNight | authentication |  | 2026-07-30 |
| 26 | Boss and elite kills pay flat XP — no tier multiplier | KnightOfNight | triaged, V24, game-balance | Version 24.15 | 2026-08-08 |
| 30 | Travel network: should checkpoints (shards) also be travel senders? | KnightOfNight | V24, travel |  | 2026-07-30 |
| 33 | Shyland: persist detailed combat logs for balance analysis | KnightOfNight | firehose-logging |  | 2026-07-30 |
| 37 | Universal event logging (firehose): every command, every output, every event | KnightOfNight | firehose-logging |  | 2026-07-30 |
| 38 | Obelisk attunement: player-set home spawn at checkpoint shards | KnightOfNight | V24, travel |  | 2026-07-30 |
| 41 | Lock battle-zone access until a new player has visited all of The Convergence | KnightOfNight | V24, travel |  | 2026-07-30 |
| 47 | Right pane: player effects display (sent and received) | KnightOfNight |  |  | 2026-07-30 |
| 70 | Feature: Longevity has no drain — the slow-burn design needs its first consuming mechanic | KnightOfNight |  |  | 2026-07-30 |
| 95 | the ring needs an area | KnightOfNight | stub, V24, travel |  | 2026-07-31 |
| 105 | Elite even-level −5% hit calibration drift (rounding parity) | KnightOfNight | V24, game-balance |  | 2026-07-30 |
| 125 | player macro/alias system | KnightOfNight |  |  | 2026-07-30 |
| 126 | pluralization subsystem — natural-English plurals for aggregate output | KnightOfNight |  |  | 2026-07-30 |
| 142 | Finish the acuity design: in-combat drift is unruled | KnightOfNight | V24, game-balance |  | 2026-07-30 |
| 145 | hot_acuity / dot_acuity announce no-op effect ticks (doctrine from #133) | KnightOfNight |  |  | 2026-07-24 |
| 148 | Loot-take sentence embeds the listing composition — flag block and double space don't match other item output | KnightOfNight | output |  | 2026-07-25 |
| 161 | Use shortfall warn lacks context — name the item and the now-empty inventory | KnightOfNight | output |  | 2026-07-29 |
| 163 | Map: more information — starting with percentage of the current zone explored | KnightOfNight |  |  | 2026-07-29 |
| 174 | Admin command: uptime (container uptimes, disk free, reclaimable space) | KnightOfNight |  |  | 2026-07-30 |
| 179 | New-zone design rules (collecting issue) | KnightOfNight |  |  | 2026-07-30 |
| 182 | Map changes/fixes (collecting issue) | KnightOfNight |  |  | 2026-08-01 |
| 188 | Process proposal: merged design+implementation session per point release, with automated playtesting (future Instructions v32) | KnightOfNight | deployments |  | 2026-08-02 |
| 191 | Firehose consumer: command-pattern watcher — mine player behavior for the next heal/loot-shaped improvements | KnightOfNight | firehose-logging |  | 2026-08-02 |
| 201 | Flame Projector / Dart Caster ship at default base_value 1 — pricing unruled | KnightOfNight | triaged, V24 |  | 2026-08-05 |
| 203 | Design: examine's 'Note: … you may drop it' line — weird on ground items, redundant with the flag block, key/value inconsistent | KnightOfNight | V24 |  | 2026-08-05 |
| 205 | Production deploy target gains a dangling-only image prune — stop the ~500MB/release root-volume growth | KnightOfNight | triaged, deployments |  | 2026-08-07 |
| 206 | 'repair' command has no path to a carried Repair Kit — field repair is 'use' only, vendor repair needs an NPC | KnightOfNight |  |  | 2026-08-07 |
| 208 | 'inv' still shows equipment and wallet — trim to inventory only ('equip' and 'wallet' own those views now) | KnightOfNight | output, V24 |  | 2026-08-07 |
| 209 | Research spike: player info on stat points — discoverability, what each stat controls, spend preview/simulator, and respec | KnightOfNight |  |  | 2026-08-07 |
| 211 | Silver accessory tier: Mk 2 jewelry needs the tier-material ladder extended (silver definitions + Mk-mismatch ruling) | KnightOfNight | V24 |  | 2026-08-08 |

## Open Issues — Full Detail

## Issue #4: Build Zone: Ashenveil Cathedral (Z02)

- State: open
- Author: KnightOfNight
- Labels: Z02
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-30
- Blocked by: #179
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/4

### Body

Build out Z02 — Ashenveil Cathedral, a dark gothic horror zone for Intermediate-level characters.

Zone described in docs/shyland/Shyland_GDD_v18.md, Section 2.2 (Zone Architecture). Wire the sealed gate on the Infinity City ring street (~2:00 position) once the zone is built.

This is one of the remaining battle zones tracked for post-Verdant-Reach content expansion.

### Comments (0)

None.

## Issue #5: Build Zone: The Neon Sprawl (Z03)

- State: open
- Author: KnightOfNight
- Labels: Z03
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-30
- Blocked by: #179
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/5

### Body

Build out Z03 — The Neon Sprawl, a cyberpunk megacity zone for Intermediate-level characters.

Zone described in docs/shyland/Shyland_GDD_v18.md, Section 2.2 (Zone Architecture). Wire the sealed gate on the Infinity City ring street once the zone is built.

This is one of the remaining battle zones tracked for post-Verdant-Reach content expansion.

### Comments (0)

None.

## Issue #6: Build Zone: The Blasted Flats (Z04)

- State: open
- Author: KnightOfNight
- Labels: Z04
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-30
- Blocked by: #179
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/6

### Body

Build out Z04 — The Blasted Flats, a post-apocalyptic wasteland zone for Advanced-level characters.

Zone described in docs/shyland/Shyland_GDD_v18.md, Section 2.2 (Zone Architecture). Wire the sealed gate on the Infinity City ring street once the zone is built.

This is one of the remaining battle zones tracked for post-Verdant-Reach content expansion.

### Comments (0)

None.

## Issue #7: Build Zone: The Iron Deeps (Z06)

- State: open
- Author: KnightOfNight
- Labels: Z06
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-30
- Blocked by: #179
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/7

### Body

Build out Z06 — The Iron Deeps, a steampunk underground zone for Advanced-level characters.

Zone described in docs/shyland/Shyland_GDD_v18.md, Section 2.2 (Zone Architecture). Wire the sealed gate on the Infinity City ring street once the zone is built.

This is one of the remaining battle zones tracked for post-Verdant-Reach content expansion.

### Comments (0)

None.

## Issue #8: Build Zone: The Pale Shore (Z07)

- State: open
- Author: KnightOfNight
- Labels: Z07
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-30
- Blocked by: #179
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/8

### Body

Build out Z07 — The Pale Shore, a cosmic horror / lovecraftian ocean zone for Endgame-level characters.

Zone described in docs/shyland/Shyland_GDD_v18.md, Section 2.2 (Zone Architecture). Wire the sealed gate on the Infinity City ring street once the zone is built.

This is one of the remaining battle zones tracked for post-Verdant-Reach content expansion.

### Comments (0)

None.

## Issue #9: Build Zone: The Wastelands (Z08)

- State: open
- Author: KnightOfNight
- Labels: Z08
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-30
- Blocked by: #179
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/9

### Body

Build out Z08 — The Wastelands, an infinite scaling zone that stays level-appropriate for any character, serving as the game's permanent endgame safety valve.

Zone described in docs/shyland/Shyland_GDD_v18.md, Sections 2.2 (Zone Architecture) and 2.7 (The Wastelands — Infinite Scaling Zone). Wire the sealed gate on the Infinity City ring street once the zone is built.

This is one of the remaining battle zones tracked for post-Verdant-Reach content expansion.

### Comments (0)

None.

## Issue #10: Transactional email via Postmark (password resets)

- State: open
- Author: KnightOfNight
- Labels: authentication
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-30
- Blocked by: none
- Blocks: #11
- URL: https://github.com/KnightOfNight/games-mvc/issues/10

### Body

## Summary

Add transactional email capability to the platform using Postmark, with password reset as the first use case.

## Background

Postmark has been selected as the transactional email provider:

- Transactional-only infrastructure (strong deliverability reputation)
- Message Streams separate transactional traffic
- 45-day activity log retention
- 100 emails/month free tier (sufficient for current scale)
- Strong Python/Django tooling

## Scope

- Postmark account setup, sender signature / domain verification for magrathea.com
- Django email backend configuration (Postmark)
- Wire Django's built-in password reset flow (views, tokens, templates) to send via Postmark
- Email templates for password reset (plain text at minimum; HTML optional)
- Configuration via environment variables in the Docker Compose stack — no secrets in the repo

## Notes

- This is shared surface area: email configuration lives at project-settings level and affects all three apps (Shyland, Shydle, Shyship). Design pass must define scope boundaries before implementation.
- Design work has not started. This issue tracks the feature; a formal design pass and brief will precede implementation.

## Out of scope

- SMS / Twilio (deferred — US A2P 10DLC registration friction)
- 2FA enrollment emails (2FA is TOTP-based and does not require email)
- Marketing or bulk email of any kind


### Comments (0)

None.

## Issue #11: Account onboarding via unusable password + reset link (no temp passwords)

- State: open
- Author: KnightOfNight
- Labels: authentication
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-30
- Blocked by: #10
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/11

### Body

## Summary

When accounts are created administratively, never issue a temporary password. Instead, create the account with Django's `set_unusable_password()` and send the user a password-setup link via the password reset machinery. The user's first action is setting their own password.

**Depends on #10** — this flow requires transactional email (Postmark) to be live before it can function.

## Background

Two patterns were evaluated for forcing a password change on first login:

1. Middleware + boolean flag redirecting to a change-password view
2. Unusable password + reset link (this issue)

Pattern 2 was preferred: it reuses Django's existing token generation, views, and templates; requires no custom middleware; and no temporary password ever exists to be intercepted or leaked.

## Scope

- Admin account-creation path calls `user.set_unusable_password()` on creation
- Setup email sent via the password reset flow (`PasswordResetTokenGenerator`)
- Token lifetime appropriate for onboarding (design pass to decide; Django default may be too short for an invite-style link)
- Login page handling for accounts with unusable passwords (design pass to decide messaging)
- Setup email template — distinct wording from the routine "reset your password" email

## Notes

- Shared surface area: touches the `profiles` app and project-level auth configuration, affecting all three apps. Design pass must define scope boundaries before implementation.
- Design work has not started. This issue tracks the feature; a formal design pass and brief will precede implementation.

## Out of scope

- 2FA (tracked separately)
- Self-service account registration changes


### Comments (0)

None.

## Issue #12: Two-factor authentication via TOTP (django-otp)

- State: open
- Author: KnightOfNight
- Labels: authentication
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/12

### Body

## Summary

Add optional two-factor authentication to user accounts using TOTP (time-based one-time passwords) per RFC 6238, compatible with any standard authenticator app (Google Authenticator, Authy, 1Password, Aegis, etc.).

## Background

TOTP via authenticator apps has been selected as the 2FA mechanism:

- RFC 6238 is an open standard — any TOTP app is interchangeable, no vendor lock-in
- No per-message cost and no delivery infrastructure required (unlike SMS or email codes)
- SMS 2FA was evaluated and deferred (Twilio / US A2P 10DLC registration friction)

Library candidates: `django-otp` (lower-level building blocks) or `django-two-factor-auth` (batteries-included flow built on django-otp). Final selection is a design-pass decision.

## Scope

- TOTP device enrollment: secret generation, QR code display, confirmation code to complete setup
- **Accessible enrollment is required**: the QR code must have a text fallback of the secret (manual entry) so screen-reader users can enroll — QR-only enrollment is not acceptable
- Login flow: password step followed by TOTP code step for enrolled accounts
- Backup / recovery codes: generated at enrollment, single-use, regenerable; needed so a lost device does not permanently lock the account
- Disenrollment (turning 2FA off) with appropriate re-authentication
- 2FA is opt-in per account, not mandatory

## Notes

- Shared surface area: authentication lives at the `profiles` app / project-settings level and affects all three apps (Shyland, Shydle, Shyship). Design pass must define scope boundaries before implementation.
- No dependency on transactional email — TOTP enrollment and login are fully offline-capable; backup codes cover the account-recovery case.
- Design work has not started. This issue tracks the feature; a formal design pass and brief will precede implementation.

## Out of scope

- SMS-based 2FA (deferred)
- Email-based one-time codes
- WebAuthn / passkeys (not evaluated; could be a future issue)
- Mandatory 2FA enforcement


### Comments (0)

None.

## Issue #26: Boss and elite kills pay flat XP — no tier multiplier

- State: open
- Author: KnightOfNight
- Labels: triaged, V24, game-balance
- Milestone: Version 24.15
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-08-08
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/26

### Body

XP awards derive from NPC level only. In the v19 Matron fight: Silk Matron (level-3 boss, 120 vitality, minion adds) paid 30 XP — identical to a level-3 cave beetle. Her brood paid 20, same as any level-2 normal. Risk/reward is flat across the normal/elite/boss tiers even though difficulty now scales sharply by tier (Brief 7's contest offsets).

Proposal direction: a tier-based XP multiplier. **How much more bosses and elites should pay needs discussion and planning — the amount is explicitly NOT decided in this issue.**


### Comments (3)

**KnightOfNight** — 2026-07-30:
Design ruling (2026-07-30, V24.0 design session): series phase order ruled — this issue is in **Phase 3 (Mk 2 balance)**, third of four (healing economy → itemization structure → Mk 2 balance → travel & world) — the numbers are computed once, against settled healing and settled items, fresh for V25 zone authoring. Each phase spans one or more point releases; release-by-release order is ruled per design session. Full series plan recorded on #139 (Version 24.0 founding ticket).


**KnightOfNight** — 2026-08-08:
Design ruling (2026-08-08, V24.15 design session): **#26 is the founding ticket of Version 24.15** (milestone assigned; Phase 3, Mk 2 balance). The tier XP multiplier is ruled — operator-confirmed numbers:

## The ladder (all five tiers ruled now, design-ahead for V25 authoring)

| combat_tier | XP multiplier |
|---|---|
| normal | ×1 |
| elite | ×2 |
| champion | ×4 |
| boss | ×8 |
| world_boss | ×16 |

**The doubling ladder: every rung doubles.** Champion and world_boss are ruled now even though unseeded — V25 zone authoring gets its numbers for free.

## Rationale (grounded in the #180 fight-cost survey)

Measured at-level cost ratios vs normal: elite 1.8× time / 3.6× draught cost; boss-as-fought ~5–6.5× time / 13.3× cost, plus 29–90% no-drink lethality at the top. The ladder sits deliberately **above time parity** (each tier is a modest ~1.1–1.4× XP-per-time premium — rewarded, not mandatory) and **below draught-cost parity** (boss loot already carries the economy leg; XP does not double-pay what loot pays). The v19 Matron example: level-3 boss 30 → 240 XP against a 900-XP level gate.

## Implementation shape (pinned)

- `combat_utils.py`: new authored int dict `NPC_TIER_XP_MULT = {'normal': 1, 'elite': 2, 'champion': 4, 'boss': 8, 'world_boss': 16}`, alongside the `NPC_TIER_OFFSET` precedent; missing-key default 1.
- `xp_for_kill`: base becomes `int(mk_tier * 10 * scaling_factor) * tier_mult`; the v18 outleveled decay then multiplies as today — **tier multiplier before band decay**, floor semantics unchanged (multiplier floor 10%, absolute min 1).
- Adds/minions pay their own tier (a boss's normal-tier adds stay ×1).
- Zero migrations, zero seed changes, zero model changes. Expected seed deletions: n/a (no seed run).
- Storage ruling: doctrine-constant dict keyed on the tier choices, not per-NPC config — the data-into-models decision does not force a model field here (operator-confirmed).

GDD text (§3 kill XP, §5 tier paragraph) lands on `version_24_15` with the pending-implementation marker; brief follows on the branch. Cold-start-ready — `triaged` applied in the same motion.


**KnightOfNight** — 2026-08-08:
Brief committed (2026-08-08, V24.15 design session): `Shyland_V24.15_Brief_1_Tier_XP_Multiplier.md` on `version_24_15` at 4d85210. Actionable when the operator directs an implementation session to it by name on this branch (CLAUDE.md Rule 4).

Carries the version-start ritual (24.15-DEV bump + `make deploy-dev`) as its opening act, then the ruled ladder: `NPC_TIER_XP_MULT` (×1/2/4/8/16) into `xp_for_kill`'s base before the outleveled decay; escorts pay their own tier. Runtime code only — no models, no migration, no seed, no data actions; no PENDING DEPLOY-TIME ACTIONS. Sentinel table pins the Matron 30 → 240; playtest rig is the standing dev Mk 2 Hollowcrown encounter (Devourer +1600, drone +360). Arch doc stamps 24.15 with the hash moving (runtime change). GDD doctrine landed at 308964b (§3 kill-XP ladder, §2 decay composition, §5.9 reward counterpart) with `(v24.15, pending implementation)` markers.


## Issue #30: Travel network: should checkpoints (shards) also be travel senders?

- State: open
- Author: KnightOfNight
- Labels: V24, travel
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/30

### Body

As built (v18 ruling), `travel` can only be initiated from the two obelisk-source nodes; checkpoint shards are destinations only (`node_type` enforces the asymmetry). Play experience: reaching a frontier checkpoint and wanting to shop means walking back or being stuck — the network feels one-way at exactly the moments it's most wanted. Discussed and deferred in the v19 design pass.

Options recorded from the discussion (decision needs design planning; explicitly NOT decided here):

1. **Full mesh** — every node sends and receives; maximum convenience, but obelisks lose their specialness and return-trip world traversal mostly disappears.
2. **Shards relay to obelisks only** — checkpoints can send, but only to the two great obelisks; obelisks send anywhere. Fixes the stranded-at-the-frontier pain while preserving hub hierarchy; diegetically clean (a shard is a fragment of an obelisk, with a fragment of its power).
3. **Status quo** — keep the asymmetry as designed friction.

A companion issue on attunement / player-set home spawn was drafted alongside this one — the two interlock (both make shards more meaningful) but are separable in implementation. Cross-link it here once it is filed.


### Comments (3)

**KnightOfNight** — 2026-07-12:
Companion issue filed as promised: #38 (obelisk attunement / player-set home spawn).

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19). Deferred: the B4 travel/attunement bucket is dropped from Version 22. This item belongs to a future version dedicated to zones and travel — revisit at that version's planning, alongside #41 and #95 which carry the same disposition. Version 22 retains only the travel destination-listing order (ascending distance, shard/sphere labels), captured in the B2 spec DD. For v22, home ships pointing at its default destination (The Convergence).


**KnightOfNight** — 2026-07-30:
Design ruling (2026-07-30, V24.0 design session): series phase order ruled — this issue is in **Phase 4 (travel & world)**, last of four (healing economy → itemization structure → Mk 2 balance → travel & world) — independent of the math phases; needed by V25 ship time, not V25 design time. Each phase spans one or more point releases; release-by-release order is ruled per design session. Full series plan recorded on #139 (Version 24.0 founding ticket).


## Issue #33: Shyland: persist detailed combat logs for balance analysis

- State: open
- Author: KnightOfNight
- Labels: firehose-logging
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/33

### Body

## Summary

We currently have no durable, structured record of individual combat encounters. Balance issues (like the unkillable-spiders bug found and fixed in earlier commits) get caught by observation/playtesting rather than by data. As the player base and play time grow, we want to be able to run math over historical combat data to find outliers (unkillable/unbeatable mobs, over/under-tuned stats, degenerate strategies, etc.) instead of relying solely on manual discovery.

## Request

Log every combat encounter with enough detail to reconstruct and analyze it after the fact, e.g.:

- Combatant identities (character vs. NPC definition/instance, including relevant stats/tier at time of fight — Vitality, Acuity, Longevity, combat tier, etc.)
- Per-round or per-action detail: contest rolls, damage dealt/taken, hit/miss/crit, status effects applied
- Outcome (win/loss/flee/death) and duration (rounds and/or wall-clock time)
- Enough context to group and aggregate later — e.g. NPC definition, zone/room, character archetype/origin

This is a tooling/observability feature, not a bug — the goal is to give the design process real data to tune balance with, rather than changing any current combat mechanics.

## Notes for implementation

- New logging is additive — should not alter existing combat math or outcomes.
- Combat math currently lives in `combat_utils.py` / `models.py`; log capture should hook in there without becoming load-bearing for gameplay itself (i.e., failure to log should never break or block a fight).
- Needs a data model design (new model(s) + migration) and a decision on retention/volume, since this will be one of the highest-write-volume tables in the game if it captures per-round detail at scale.
- Should be queryable/exportable enough to "run math on the logs" — consider what aggregate queries or admin/reporting tooling would actually be needed to catch tuning problems like the spider issue.

### Comments (1)

**KnightOfNight** — 2026-07-12:
Moved to the Firehose Logging milestone. This issue is the mechanics-instrumentation half (tick-engine rolls and per-round detail that never surface as player-visible messages); #37 is the umbrella and covers the envelope-tap half. See #32 for the v20 envelope both build on.

## Issue #37: Universal event logging (firehose): every command, every output, every event

- State: open
- Author: KnightOfNight
- Labels: firehose-logging
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-30
- Blocked by: #32
- Blocks: #112, #191
- URL: https://github.com/KnightOfNight/games-mvc/issues/37

### Body

## Summary

Log everything: every command any player sends, every line the server emits (personal output, room broadcasts, NPC dialogue, chat, system messages), with enough structure to query for game-balance analysis, anomaly detection, and eventual AI-assisted observation of the game world.

## Relationship to other issues

- **Blocked by #32 (v20 message envelope).** The envelope — one choke point stamping every player-visible message with a server UTC timestamp and sequence number — is the tap point this issue's log sink attaches to. Without it, instrumentation means hunting emit sites across the whole consumer.
- **#33 (persist detailed combat logs)** is the mechanics-instrumentation component of this milestone: dice rolls, contest values, and per-round detail happen inside the tick engine before any message is composed, and many rolls never produce player-visible output at all. The envelope tap cannot see them; #33 instruments them at the resolution points. The two issues together are the full firehose.

## Scope

- Log sink at the envelope choke point: every enveloped message recorded with timestamp, sequence number, character, room, category, and text
- Command ingress logging: every command received in `receive_json`, accepted or rejected
- Retention and volume policy (design decision — this will be a high-write-volume store)
- Query/analysis access: enough tooling to actually "run math on the logs"

## Required GDD ruling

GDD §7.1 says "all channels are logged server-side for moderation" while §10.5 says chat messages are "never persisted." Reality currently matches §10.5 (nothing is logged). This issue requires a formal reversal of the §10.5 chat-persistence ruling, including an explicit privacy/retention stance on player speech in logs. That ruling happens in the design chat before any implementation brief.

## Notes

- Logging is additive and must never be load-bearing: a logging failure must never break or block gameplay.
- Player-facing timestamps in the output window ship earlier, in v20, via #32.


### Comments (0)

None.

## Issue #38: Obelisk attunement: player-set home spawn at checkpoint shards

- State: open
- Author: KnightOfNight
- Labels: V24, travel
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/38

### Body

## Summary

Let a player attune to a checkpoint shard (and the great obelisks), making it their personal respawn / recall home point. Companion to #30 (checkpoint shards as travel senders) — the two interlock (both make shards more meaningful destinations) but are separable in implementation.

## Background

Drafted alongside #30 during the v19 design pass and never filed; #30's body asks for the cross-link once this exists. Today respawn is fixed (The Convergence) and `recall` is unimplemented (a known v19 carry-over gap) — this issue and the recall gap should be designed against each other.

## Needs discussion and planning (nothing decided here)

- What attunement means mechanically: automatic on first visit, or an explicit `attune` command at the node?
- One home at a time, or a small set?
- Which node types are attunable: shards only, or obelisk sources too?
- Interaction with #30: if shards become senders, does attunement gate that, or are they independent powers?
- Death respawn vs. voluntary recall: same destination or separately settable?

## Out of scope

- The travel-sender question itself (#30)


### Comments (2)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19). Deferred: the B4 travel/attunement bucket is dropped from Version 22. This item belongs to a future version dedicated to zones and travel — revisit at that version's planning, alongside #41 and #95 which carry the same disposition. Version 22 retains only the travel destination-listing order (ascending distance, shard/sphere labels), captured in the B2 spec DD. For v22, home ships pointing at its default destination (The Convergence).


**KnightOfNight** — 2026-07-30:
Design ruling (2026-07-30, V24.0 design session): series phase order ruled — this issue is in **Phase 4 (travel & world)**, last of four (healing economy → itemization structure → Mk 2 balance → travel & world) — independent of the math phases; needed by V25 ship time, not V25 design time. Each phase spans one or more point releases; release-by-release order is ruled per design session. Full series plan recorded on #139 (Version 24.0 founding ticket).


## Issue #41: Lock battle-zone access until a new player has visited all of The Convergence

- State: open
- Author: KnightOfNight
- Labels: V24, travel
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/41

### Body

## Summary

New feature: lock access to battle zones (starting with the Verdant Reach, via the Green Gate) until a new character has visited every room in The Convergence.

## Goal

Guarantee new players discover all of the newbie gear seeded in The Convergence before they can leave it for a zone where things can hurt them. Today a player can walk straight through the Green Gate without ever seeing the rest of the starter zone.

## Needs discussion and planning (nothing decided here)

- Enforcement point: block the gate exit itself (Green Gate, R02, `exit_north` into the Tree Arch per #34) versus blocking all battle-zone entrances generically as new ones are added
- Completion check: does "visited all of the Convergence" mean every room in the zone, or a curated subset (e.g. excluding rooms that aren't gear-relevant)? Uses the existing `RoomVisit` model — no new tracking model
- Player-facing messaging: what tells the player they're not yet allowed through, and what (if anything) nudges them toward the unvisited rooms
- One-time gate: once a character satisfies the requirement, does it stay unlocked permanently, or could a state regression re-lock it (it shouldn't)
- Interaction with future zones: is this Convergence-specific, or a general pattern other starter/gated zones should reuse

## Out of scope

- Redesigning The Convergence's room layout or gear placement — this issue only gates the exit, it doesn't change what's inside


### Comments (2)

**KnightOfNight** — 2026-07-18:
Deferred (2026-07-17): revisit in the next major version that releases new zones.


**KnightOfNight** — 2026-07-30:
Design ruling (2026-07-30, V24.0 design session): series phase order ruled — this issue is in **Phase 4 (travel & world)**, last of four (healing economy → itemization structure → Mk 2 balance → travel & world) — independent of the math phases; needed by V25 ship time, not V25 design time. Each phase spans one or more point releases; release-by-release order is ruled per design session. Full series plan recorded on #139 (Version 24.0 founding ticket).


## Issue #47: Right pane: player effects display (sent and received)

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-13 | Updated: 2026-07-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/47

### Body

## Summary

Display of player effects (sent and received) in the right pane. Originally part of #2's scope ("Player effects sent and received."); DEFERRED out of Version 20 during the v20 layout design pass (2026-07-13) — no milestone.

## Why deferred

Requires an effect-state data feed the game barely exercises yet (the EffectDefinition/EffectInstance vocabulary is built but lightly used). The v20 right pane ships with stats (top), fight info (middle), and the map (bottom); effects display slots into a later version once effects see real play.

## Notes for the eventual design pass

- Natural home: the right pane's middle region alongside (or within) the fight-info scroller.
- Will need a structured effect-state message (active effects with magnitude/duration remaining), likely riding the same delivery pattern as the v20 fight message.

## Related

- #2 — right pane design (origin of this scope)


### Comments (1)

**KnightOfNight** — 2026-07-30:
Design ruling (2026-07-30, V24.0 design session, major re-triage): deferred out of the Version 24 (new-zone-prep) major — V24 label removed. Off-theme for new-zone prep; remains open, unlabeled for grouping, and ships as an ordinary point release whenever chosen (v30 release model).


## Issue #70: Feature: Longevity has no drain — the slow-burn design needs its first consuming mechanic

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-15 | Updated: 2026-07-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/70

### Body

## Summary

Verified by code audit during v20 Brief 4 playtesting (2026-07-15): every site touching longevity_current only raises or resets it — level-up recalculation, death-respawn refill, a restore_longevity effect component (unused by any seeded consumable), and passive regen. NOTHING drains it. The bar has been load-bearing scaffolding since the three-bars rule put it in the data model on day one.

## The design IOU

GDD intent: Longevity is the slow burn — stamina duration, DoT/HoT windows, sustained-effect budgets, the bar that makes a LONG dungeon run hard and recovers slowly. Those systems (DoTs in play, stamina-consuming sustained actions, exhaustion) have not shipped, so the bar reads 274/274 forever.

## Design question for a future features version

What is the FIRST thing that spends Longevity? Candidates already latent in the design/fiction:
- Flee exertion — the "You are still recovering from your last flee attempt" fiction is begging for a cost.
- Sustained/stance actions when they arrive (Archetype abilities are unbuilt).
- DoT durations drawing on the target's Longevity per the effect-system design.

Companion consideration: once a drain exists, the restore_longevity effect component gets its first consumable, and the (pending) stats-pane Longevity bar stops looking broken-at-full.

## Disposition

Deliberately UNMILESTONED (ruled 2026-07-15) — a features-version candidate (even-numbered release per the cadence rule), to be weighed at v22+ planning.


### Comments (1)

**KnightOfNight** — 2026-07-30:
Design ruling (2026-07-30, V24.0 design session, major re-triage): deferred out of the Version 24 (new-zone-prep) major — V24 label removed. Off-theme for new-zone prep; remains open, unlabeled for grouping, and ships as an ordinary point release whenever chosen (v30 release model).


## Issue #95: the ring needs an area

- State: open
- Author: KnightOfNight
- Labels: stub, V24, travel
- Milestone: none
- Assignees: none
- Created: 2026-07-17 | Updated: 2026-07-31
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/95

### Body



### Comments (3)

**KnightOfNight** — 2026-07-18:
Deferred (2026-07-17): revisit in the next major version that releases new zones.


**KnightOfNight** — 2026-07-30:
Design ruling (2026-07-30, V24.0 design session): series phase order ruled — this issue is in **Phase 4 (travel & world)**, last of four (healing economy → itemization structure → Mk 2 balance → travel & world) — independent of the math phases; needed by V25 ship time, not V25 design time. Each phase spans one or more point releases; release-by-release order is ruled per design session. Full series plan recorded on #139 (Version 24.0 founding ticket).


**KnightOfNight** — 2026-07-31:
Operator note (2026-07-30, V24.0 design session — late-catch record): the ring area is part of travel and lore, nothing too special; no surprises expected. Stub to be fattened when Phase 4 (travel & world) reaches it.

## Issue #105: Elite even-level −5% hit calibration drift (rounding parity)

- State: open
- Author: KnightOfNight
- Labels: V24, game-balance
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-17 | Updated: 2026-07-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/105

### Body

Survey finding G5 (#89): at even levels, banker's rounding in the NPC DEX curve and the floor-share of the player's odd stat point misalign by 1 DEX = 5% hit. All observed deviations are exactly −5%, at L4/L8 only. Calibration noise inherent to integer stats; flips no verdict alone, but compounds in multi-elite rooms. Recorded for a future calibration pass; the arch doc's "blessed targets exact at every level" claim is overstated by this amount.


### Comments (1)

**KnightOfNight** — 2026-07-30:
Design ruling (2026-07-30, V24.0 design session): series phase order ruled — this issue is in **Phase 3 (Mk 2 balance)**, third of four (healing economy → itemization structure → Mk 2 balance → travel & world) — the numbers are computed once, against settled healing and settled items, fresh for V25 zone authoring. Each phase spans one or more point releases; release-by-release order is ruled per design session. Full series plan recorded on #139 (Version 24.0 founding ticket).


## Issue #125: player macro/alias system

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: none
- Created: 2026-07-20 | Updated: 2026-07-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/125

### Body

research spike


example commands to help frame the functionality...


**example**
`
alias heal "use 10 healing draughts"
`
player can then type 'heal'



**example**
`
unalias heal
`
removes the macro

### Comments (3)

**KnightOfNight** — 2026-07-29:
Cross-reference (2026-07-29): the recurring 'heal' use case that keeps motivating this alias system has been spun out as a built-in command — #166 (Healing Economy milestone). The macro/alias system remains the general-purpose solution; #166 is the staple shortcut that shouldn't wait for it.

**KnightOfNight** — 2026-07-29:
if we implement a 'heal' command, that's a good example of how 'alias heal <some command>' should then fail.

**KnightOfNight** — 2026-07-30:
Design ruling (2026-07-30, V24.0 design session, major re-triage): deferred out of the Version 24 (new-zone-prep) major — V24 label removed. Off-theme for new-zone prep; remains open, unlabeled for grouping, and ships as an ordinary point release whenever chosen (v30 release model).


## Issue #126: pluralization subsystem — natural-English plurals for aggregate output

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-20 | Updated: 2026-07-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/126

### Body

Ruled 2026-07-20 (V22 B2 Amendment 5): aggregate transactional output ships with the count form ('Healing Draught Mk 1 ×100') as a deliberately plural-free first iteration. The upgrade is a shared pluralization subsystem callable from any output site: forward pluralization rules (inverting the resolver's _plural_variants de-pluralizer), an authored plural-name override field on ItemDefinition for irregulars, and multi-word head-noun handling ('Boots of the Marsh'). When it ships, the ×N aggregates upgrade to natural English ('You buy 100 Healing Draughts Mk 1 …'). Future version; scope deliberately excluded from v22.


### Comments (1)

**KnightOfNight** — 2026-07-30:
Design ruling (2026-07-30, V24.0 design session, major re-triage): deferred out of the Version 24 (new-zone-prep) major — V24 label removed. Off-theme for new-zone prep; remains open, unlabeled for grouping, and ships as an ordinary point release whenever chosen (v30 release model).


## Issue #142: Finish the acuity design: in-combat drift is unruled

- State: open
- Author: KnightOfNight
- Labels: V24, game-balance
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-23 | Updated: 2026-07-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/142

### Body

**Origin:** split out of #27 per design-chat ruling 2026-07-23. The research spike on #27 (see its findings comment) corrected that issue's premise — the observed "regen" lines were consumable heals — but surfaced this: **Acuity drift has no in-combat exclusion.** Phase 2 of the tick engine pulls every character's acuity toward their Origin baseline on every tick, in combat or out, while the Phase 4 Vitality/Longevity regen pass explicitly excludes in-combat characters. Nobody ever ruled what combat should do to the mind's pull toward baseline — the asymmetry exists because the question was never asked. This is unfinished design, not a bug, hence a feature-version item.

**Everything we know about acuity so far:**

*Doctrine (GDD §Three Bars):* Acuity is the mind's dynamic state — explicitly not a sanity meter. Each Origin has a baseline and an optimal band; the system has been band-relative and deviation-based since v19. Too LOW: spells fizzle, aim drifts, awareness collapses. Too HIGH: hyper-focus — single-target bonus, but flanking enemies go undetected. (Doctrine; verify current combat-wiring status against the architecture doc before designing.)

*Origin values (decimal scale; GDD authoritative):*

| Origin | Baseline | Band Low | Band High |
|---|---|---|---|
| Highborn | 1.0 | 0.85 | 1.15 |
| Feral | 0.95 | 0.80 | 1.10 |
| Streetborn | 1.0 | 0.85 | 1.15 |
| Irradiated | 0.90 | 0.75 | 1.05 |
| Undying | 0.80 | 0.65 | 1.00 |
| Machinekind | 1.05 | 0.90 | 1.20 |
| Voidtouched | 0.70 | 0.40 | 1.30 |

*Code facts (from the #27 spike, verified against current main):* drift runs in tick Phase 2 with no combat-membership check; Vitality/Longevity regen runs in Phase 4 with an explicit in-combat exclusion (`run_tick_engine.py:1267` at time of spike) and has been silent since its v14 introduction. The two recovery systems are structurally asymmetric today.

*UI:* the stats pane renders the Acuity band gauge (v20; repainted v22 — success-color fills, solid band, say-color 16×4 tick).

*Consumables:* Focus Tonic and `shift_acuity_low` shift acuity via instant/tick effect components. **#133 (Version 23)** covers the tonic's defects against the current band rules — it drives to the 1.9 clamp past every Origin's band and announces no-op ticks; its magnitude/duration/taper/terminal-line/clamp questions are open there. Sequencing note: #133 will re-tune the tonic against *current* drift behavior; whatever this issue rules about in-combat drift may reshape tonic assumptions again. The two rulings should be made aware of each other.

*Related systems:* the Warden archetype is designed as the healer / acuity manager. The combat-economy pile (#25 heal-on-disengage, #26 and kin) concerns what recovers during and around combat — this issue is the acuity-shaped member of that family.

**The design question for Version 24:** what does combat do to acuity drift? Sketch of the option space (none ruled): (a) pause drift in combat entirely — symmetric with the other two bars; (b) keep drift running as-is — maintaining an off-baseline state mid-fight requires active upkeep, which gives the Warden a job and makes high-acuity states a spend; (c) combat-specific drift — rate or direction changes under stress, possibly per-Origin. Interactions to resolve: band-based combat effects wiring, tonic timing/duration post-#133, Voidtouched's deliberately wide band, and whatever the combat-economy rulings decide about recovery during engagement.


### Comments (3)

**KnightOfNight** — 2026-07-23:
Split from #27, whose research-spike findings comment contains the full code-level analysis (tick phases, exclusion sites, v19-vs-current confirmation). #27 is closed as premise-corrected; this issue carries the surviving design question.


**KnightOfNight** — 2026-07-30:
Design ruling (2026-07-30, V24.0 design session, major re-triage): confirmed in the Version 24 (new-zone-prep) major plan — V24 label stays. Series order and release assignment to be ruled separately.


**KnightOfNight** — 2026-07-30:
Design ruling (2026-07-30, V24.0 design session): series phase order ruled — this issue is in **Phase 3 (Mk 2 balance)**, third of four (healing economy → itemization structure → Mk 2 balance → travel & world) — the numbers are computed once, against settled healing and settled items, fresh for V25 zone authoring. Each phase spans one or more point releases; release-by-release order is ruled per design session. Full series plan recorded on #139 (Version 24.0 founding ticket).


## Issue #145: hot_acuity / dot_acuity announce no-op effect ticks (doctrine from #133)

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-24 | Updated: 2026-07-24
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/145

### Body

**Doctrine source:** #133 ruling 3 (operator-confirmed 2026-07-23), promoted to standing doctrine and implemented on both `shift_acuity_*` branches by V23 B3: *effect ticks never announce no-ops; boundary arrival gets one terminal line; holding is silent.*

Two effect branches in `run_tick_engine.py`'s `process_effects` still violate it (deliberately untouched by B3 — constants substitution only):

- **`hot_acuity`** (~line 1102): at baseline, `diff` is 0 so `step` computes to 0 — the branch still saves and announces `Your mind clears from {name}. (Acuity N)` **every tick**, a no-op announcement loop identical in shape to the one #133 fixed on the shift branches.
- **`dot_acuity`** (~line 1065) and the flat-floor resource DoTs (`dot_vitality`/`dot_longevity` at their floors) share the clamp-and-announce structure: once the value pins at its floor, ticks keep announcing an unchanging number.

Fix shape (at fix time): apply the same change-only + one-time-terminal-line pattern the shift branches now use. Per standing creative policy, the terminal-line wording for each branch is **authored at fix time** — not specified here.


### Comments (0)

None.

## Issue #148: Loot-take sentence embeds the listing composition — flag block and double space don't match other item output

- State: open
- Author: KnightOfNight
- Labels: output
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-25 | Updated: 2026-07-25
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/148

### Body

Observed (v23, post-B5):

```
You loot Insect Carapace Mk 1  [Common, Unbound].
```

This does not match the game's other transactional item sentences. The DD §6 family (buy/sell/drop/pickup/use) composes item references through `item_utils.item_ref` — definite article, name-with-tier, **no flag block** — e.g. `You sell the Insect Carapace Mk 1 for 1 copper.` The loot-take line instead embeds the *listing* composition (`compose_item_line` shape: name-with-tier + double-spaced `[Rarity, Bound|Unbound]` flag block) inside a sentence, which is where the stray double space and the bracketed flags come from.

Site: `consumers.py`, the loot-take output (`You loot {line}.`, category `reward`).

Operator direction (2026-07-25): change the loot-take sentence to match the other item output in the game.


### Comments (0)

None.

## Issue #161: Use shortfall warn lacks context — name the item and the now-empty inventory

- State: open
- Author: KnightOfNight
- Labels: output
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-29 | Updated: 2026-07-29
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/161

### Body

**Finding (v23.3 Brief 1 dev playtest, 2026-07-29):** the use shortfall warn `You only had 1.` is easy to miss and lacks context — it names neither the item nor the consequence.

**Proposed wording (operator):** `You only had X <items> available to use; you now have no <items> left in your inventory.`

**Notes for the ruling session:**
- This is the #132 shortfall-visibility doctrine family: `use` and `drop` share `You only had N.`; `pickup` says `There were only N here.`, `buy` says `They only had N.`, `sell` has its ruled success-voice exception. Ruling scope question: use only, or the family?
- On `use` the second clause is always literally true — the warn fires only after every matching item was consumed (v23.3 aggregate path: request > inventory AND deficit uncovered; per-item path: all resolved items used), so inventory of that item is zero whenever it prints.
- Sites: `consumers.cmd_use` per-item loop and `_use_aggregate` (v23.3 B1).

Could ride as a v23.3 amendment if ruled in-release; otherwise queues normally.


### Comments (0)

None.

## Issue #163: Map: more information — starting with percentage of the current zone explored

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-29 | Updated: 2026-07-29
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/163

### Body

Update the map with more information, starting with: **percentage of the current zone explored**.

"Starting with" is deliberate — this is the first element of a broader map-information pass; the design session that picks this up should consider what else belongs (the operator will have opinions by then).

Context for the first element:

- The data already exists: fog-of-war is `RoomVisit` (recorded at arrival in every path), so zone-explored % is `count(RoomVisit for character in zone) / count(rooms in zone)` — no new models expected.
- The map build is a bounded five-query constant (v20/v22 Maps V2); adding a percentage should stay within that spirit — one cheap aggregate, not per-room work.
- Presentation needs a ruling: the map SVG is `aria-hidden`, so the percentage must also live as accessible text (not only drawn inside the SVG) per the screen-reader non-negotiable.


### Comments (2)

**KnightOfNight** — 2026-07-29:
Operator follow-up (2026-07-29): the map text does NOT have to be screen-reader-accessible — it can live inside the aria-hidden SVG. Accessibility is served instead by a NEW COMMAND that reports the same kind of information in the standard command/output fashion (screen-reader-native by design, like every command). Scope of #163 therefore includes both halves: the SVG display element(s) and the companion command; the design session names the command and rules its output format.

**KnightOfNight** — 2026-07-29:
Operator follow-up 2 (2026-07-29): the companion command's verb will be `map` — verb settled, nouns entirely open (no ideas yet). The design session rules the noun grammar (e.g. what `map` bare reports vs. noun-scoped forms) within the v22 command-grammar conventions (§9.1 chart, three-layer response doctrine, tab-completion pools).

## Issue #174: Admin command: uptime (container uptimes, disk free, reclaimable space)

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-30 | Updated: 2026-07-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/174

### Body

New admin command `uptime`.

It should report:

- the uptime of all containers (nginx, django, postgres, redis, ticker)
- free disk space
- reclaimable space (e.g. pruneable docker images)


### Comments (1)

**KnightOfNight** — 2026-07-30:
Design ruling (2026-07-30, V24.0 design session, major re-triage): reviewed and ruled NOT part of the Version 24 (new-zone-prep) major — no V24 label. Remains unlabeled for grouping; ships as an ordinary point release whenever chosen (v30 release model).

## Issue #179: New-zone design rules (collecting issue)

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-30 | Updated: 2026-07-30
- Blocked by: none
- Blocks: #4, #5, #6, #7, #8, #9
- URL: https://github.com/KnightOfNight/games-mvc/issues/179

### Body

Collecting issue for new-zone design rules. Rules accumulate here (body + comments) until a design session rules them and ships them as GDD text — realistically the Zone Design Standards passage in V25.0's coherent pass, landing with the release that first builds a zone under them. This issue closes when that ships.

Rules are **construction standards for new zones** — shipped zones are documented as-is, not retroactively in violation (precedent: the v18 identification trapdoor note). Whether an existing zone gets remediated to a standard is its own someday-ticket.

---

## Rule 1 — Zone topology must branch (operator, 2026-07-30)

Stated by counterexample: **The Verdant Reach is a straight line, not at all maze-shaped.** New zones don't get to be. Branching, loops, decision points — topology that rewards the map instead of merely scrolling it. The map machinery (MapFrags, fog-of-war, boundary flags) was built for geometry Z01 never gave it.


### Comments (0)

None.

## Issue #182: Map changes/fixes (collecting issue)

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-31 | Updated: 2026-08-01
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/182

### Body

Collecting issue for map changes and fixes — the map counterpart to #179 (new-zone design rules). Ideas, fixes, and follow-on map-information elements accumulate here (residents list + comments) until design sessions carve them into shippable slices.

Mechanics, per the scope law: this umbrella never ships as a release itself. Each shippable slice is (or becomes) its own ticket — one founding ticket, one brief, one release — and gets added to the residents list below. The umbrella closes when the operator judges the map pass complete (or the issue no longer useful).

Standing context: Maps V2 (v20/v22) is the shipped foundation — per-zone map-space coordinates, MapFrags, fog-of-war via RoomVisit, bounded five-query build, aria-hidden 300×300 SVG. Operator rulings already recorded on #163: map display elements may live inside the aria-hidden SVG; accessibility is served by a companion command (verb settled: `map`, nouns open).

## Residents

- [ ] #163 — percentage of current zone explored + the `map` companion command (first shippable slice)


### Comments (1)

**KnightOfNight** — 2026-08-01:
**New entry (operator, 2026-08-01): indicate "the way out."**

When you're down in a cave — or off in any map branch — it's easy to get lost: there are no breadcrumbs when you change MapFrags. Each MapFrag transition (up/down, boundary seams) starts a fresh drawing on the far side, and nothing on the new frag indicates the route back the way you came.

The ask: some indication of the way out. Form is a design-session ruling — candidates include marking the room/exit that returns toward the previous frag, a persistent entry-point marker on the current frag, or a `map`-command answer (which would also carry the screen-reader path) — remembering direction and state are always carried by words, never color alone.


## Issue #188: Process proposal: merged design+implementation session per point release, with automated playtesting (future Instructions v32)

- State: open
- Author: KnightOfNight
- Labels: deployments
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-02 | Updated: 2026-08-02
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/188

### Body

**Status: proposal only — operator-directed filing so the idea isn't lost. NOT ruled, NOT to be applied until the operator directs it explicitly.**

## Operator's proposal (2026-08-01)

Under the release model, every point release is one brief — so design and implementation could be **one session**, removing a session change. With automatic playtesting added, the flow becomes: design → operator says **"go"** → implementation → automated playtest → less babysitting. Some playtesting remains manual. **Closeout stays a separate session** (it deploys to production).

Context: five point releases shipped in ~3 days under the current shape (24.0–24.4). The bottleneck is operator touchpoints, not work.

## Analysis (ops session, same conversation)

The design/implementation firewall protects four things; each survives the merge with a re-homing:

1. **Brief self-containedness** (today tested by a cold implementation session) → hard phase gate: brief written, committed, pushed **before** the go; implementation implements the brief, not the conversation. The next release's design phase keeps verifying from committed reports (independent audit).
2. **Operator design checkpoint** (today implicit in the session change) → the explicit **"go" gate**, same trust pattern as the closeout tail's one-time go-ahead.
3. **Firewall discipline mid-build** (today: stop and amend via design session) → operator is in the room; ambiguity → ruling → recorded on the issue immediately → continue. The firewall becomes sequential — a phase wall, not a session wall.
4. **Verification independence** (the one real loss — design→code→test in one context is self-grading) → playtest checklist authored in the design phase before code exists; the automated pass runs in a **fresh-context subagent** driving the dev stack cold from the brief's checklist (Rule 4's objectively-verifiable-steps allowance is the seed). Perceptual/multi-account testing stays manual; the disposition gate stays, gaining an automated-results line.

Boundaries to keep: **closeout separate** (prod deploy + independent audit of the merged session's artifacts); **big coherent passes stay pure design sessions** — the merged form fits point releases whose design is mostly pre-ruled (under design-ahead, that's most of them).

Touchpoint math: ~5 per release today → ~3 merged (open+rulings, "go", manual playtest + disposition + end).

## Shape when applied (Instructions v32)

- Session-quantities rule: design and implementation may run as one session with the go-gate between phases.
- CLAUDE.md Rule 3 table: merged type's edit surface (GDD source in the design phase, code in the implementation phase — never simultaneously).
- One folded end ritual (design-session-end duties absorbed into implementation-session-end).
- Brief template: playtest checklist split into automated (subagent-run against dev) and manual (operator) parts; closeout report disposition carries both.


### Comments (0)

None.

## Issue #191: Firehose consumer: command-pattern watcher — mine player behavior for the next heal/loot-shaped improvements

- State: open
- Author: KnightOfNight
- Labels: firehose-logging
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-02 | Updated: 2026-08-02
- Blocked by: #37
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/191

### Body

Once the firehose (#37) is running, one of the **first agents to listen to it** should watch for **command patterns** — mining how players actually play for the next `heal`- and `loot`-shaped improvements.

## Motivation (operator, 2026-08-02)

`heal` was a simple addition on the surface and a huge gameplay improvement; bare-`loot`-as-sweep is the same shape. Both were visible in advance as *patterns*: players repeatedly typing `use healing draught` is a missing `heal` verb; players looting corpse after corpse is a missing default sweep. A faster process makes the game better faster — this agent finds where to point it.

## What the agent watches for (sketch, design session rules the real spec)

- **Repeated command sequences** — the same multi-step chain typed over and over is a candidate single verb (the `heal` signature).
- **Repetition of one command with varying targets** in quick succession — a candidate `all`/default form (the `loot` signature).
- **Refusal and error frequency** — which CLI errors and world-declined warns players hit most (each one is friction; some are missing affordances).
- **Unknown-command attempts** — what players *try* to type is a direct vocabulary wishlist.
- Output: a periodic digest the operator reads — candidates ranked by frequency, each one a potential thin issue.

Blocked by #37 (the firehose itself). Related: #33 (combat-log persistence for balance analysis) is a sibling consumer of the same stream.


### Comments (0)

None.

## Issue #201: Flame Projector / Dart Caster ship at default base_value 1 — pricing unruled

- State: open
- Author: KnightOfNight
- Labels: triaged, V24
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-02 | Updated: 2026-08-05
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/201

### Body

Mid-build discovery from V24.10 Brief 1 (#127) implementation.

The brief's seed table for Flame Projector and Dart Caster authors no `base_value`, and the rulings on #127 / GDD §6.4 are silent on pricing — so both definitions ship at the model default (`base_value = 1`): value ≈ 1 copper × mk × rarity multiplier, sale price ~0–10 copper. Their weapon peers author 35–100 (`base_values` back-fill dict in `seed_world.py`).

Needs a design ruling: authored `base_value` for the two floored-proc weapons (and a `base_values` dict entry each). No code change beyond the two numbers once ruled.


### Comments (1)

**KnightOfNight** — 2026-08-05:
Design ruling (2026-08-05, V24.11 design session): pricing ruled — operator-confirmed authored `base_value`s:

- **Flame Projector: 85** — the two-handed ranged peer of the Hunting Bow (80): weaker direct damage (Mk 1 midpoint 7 vs 10) but the strongest authored proc floor in the game (flame 8 + 4/Mk) earns a hair above the bow, staying below the 100 two-handed-melee ceiling (Broadsword/Battle Axe).
- **Dart Caster: 70** — slot-flexible one-hander like the Pulse Pistol (90) but well below its raw output (Mk 1 midpoint 5.8 vs 8.5), with the milder poison floor (5 + 3/Mk); lands between Iron Mace (65) and Hunting Bow (80).

Implementation shape (unchanged from the issue): one `base_values` dict entry each in `seed_world.py` — no other code change.

**Premise correction for the record:** the pair does not sit at the model default `base_value = 1` — the type-wide back-fill (`seed_world.py` ~line 4855: non-consumable/non-bag definitions without authored entries → 25) means they currently ship at **25**. The fix is identical either way: two authored dict entries, which also removes them from the back-fill's reach.

Release mechanics: ships as its own tiny release under the scope law (it cannot ride V24.11 — different problem than #80). Applying the numbers requires a seed rerun, so its release's brief carries a PENDING DEPLOY-TIME ACTIONS block (production seed at the closeout tail via `make seed-prod`); the back-fill is an `.update()` — expected deletions: 0. Release assignment and queue slot remain a design-session call (the ruled Phase 2 queue #80 → #134 continues first).

With numbers ruled and the implementation shape pinned, this issue is cold-start-ready — `triaged` applied in the same motion.


## Issue #203: Design: examine's 'Note: … you may drop it' line — weird on ground items, redundant with the flag block, key/value inconsistent

- State: open
- Author: KnightOfNight
- Labels: V24
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-05 | Updated: 2026-08-05
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/203

### Body

## Current behavior

`examine` on any identified-rendered item that is neither equipped nor soulbound appends a fixed line (`_format_identified_item_lines`, `consumers.py` ~1789):

```
  Note:       This item is not yet bound — you may drop it.
```

Its counterpart for soulbound items is:

```
  Bound:      This item is bound to you.
```

## Problems (operator, 2026-08-05, during the V24.11 Brief 1 implementation session)

1. **Weird on ground items.** Since v24.11 (#80, knowledge by holding), examining an item on the ground renders the full identified detail block — and a ground item you don't hold telling you "you may drop it" reads wrong.
2. **Redundant for every item.** The trailing flag block already carries `[Bound]`/`[Unbound]` on the headline of the same examine render (and everywhere else an item line composes). The prose line restates it.
3. **Key/value inconsistency.** The label `Note:` doesn't name the property it reports — its sibling rows use property keys (`Bound:`, `Curse:`, `Equipped:`, `Durability:`), so the same fact renders under two different key styles depending on state.

## Direction

Operator's initial lean: just remove the line — but this needs a design session ruling (the `Bound:` prose line's fate and any key/value normalization are part of the same question). Not ruled; filed thin for triage into the V24 queue.


### Comments (0)

None.

## Issue #205: Production deploy target gains a dangling-only image prune — stop the ~500MB/release root-volume growth

- State: open
- Author: KnightOfNight
- Labels: triaged, deployments
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-07 | Updated: 2026-08-07
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/205

### Body

## Ruling (operator, 2026-08-06, recorded live — filed on direction; NOT yet applied)

`make deploy-prod` gains a **dangling-only image prune** as its post-build sweep: each deploy removes its predecessors' orphaned image pairs. **Routine pruning is dangling-only, never `-a`.**

## Diagnosis (live census on prod, 2026-08-06)

- Root volume was back to 43% (from ~20% after the 2026-07-29 manual cleanup); `docker system df`: 30 images, 4 active, **4.35GB reclaimable (84%)**.
- Composition: 13 pairs of untagged `<none>` images — one django (464MB) + nginx (61.8MB) pair per release deploy, ages 4–8 days. The release stream's exhaust: every `make build` re-tags `:latest` and orphans the previous pair. At current cadence root grows ~500MB/release without intervention.
- The history has no value: not rollback artifacts (prod runs main; rollback = rebuild from source), not addressable (untagged), not cache (a superseded image's unique layers are exactly the changed layers — never cache hits again; the reusable layers are shared with `:latest` and are not reclaimable).

## Why dangling-only doesn't slow the next build

The 2026-07-29 slowdown came from the full `-a` prune: it removed the tagged base images (`python:3.12-slim` re-pull) and forced a cold rebuild. Dangling-only preserves the `:latest` layer chains and service images — the next build's cache hits are identical before and after. The only layer that rebuilds is the one that was going to rebuild anyway (source COPY; pip only when requirements.txt changes).

## Implementation shape (applied on operator direction, ops session)

In the `deploy-prod` recipe, after the build/migrate steps and before the resting-posture restore:

```
DOCKER_HOST=$(PROD_DOCKER_HOST) docker image prune -f
```

(`-f` skips the confirmation prompt; dangling-only is the no-flag default.) Optional same-motion extension, needs its own nod: the same line (bare, local daemon) in `deploy-dev` — Emma's dev daemon accumulates the same exhaust at a higher rate.

One-time catch-up: a manual dangling-only prune on prod reclaims the current ~4.3GB immediately; thereafter the deploy step keeps root flat.


### Comments (1)

**KnightOfNight** — 2026-08-07:
**Dev-side finding (2026-08-06) — corrects this issue's optional deploy-dev rider.**

Emma's dev daemon has the same growth disease in a different organ: Rancher Desktop builds with BuildKit, so the exhaust accumulates as **builder cache**, not dangling images (census: images clean at ~0 reclaimable, but build cache at 41GB / 898 entries / 98% reclaimable, filling the Lima VM's virtual disk to 43%). Prod's daemon uses the classic builder, which is why its exhaust shows up as dangling image pairs instead.

So the sweep is per-daemon, matched to mechanism:

- **Prod / deploy target:** `docker image prune -f` (dangling-only) — as ruled in the body.
- **Dev / deploy-dev:** `docker builder prune -f --keep-storage 5GB` — LRU eviction down to a cap; the most recent build's layers are by definition kept, so the next build is not slower. This replaces the body's "same line in deploy-dev" phrasing.

One-time dev catch-up executed 2026-08-06 (operator-directed, ops session): 35.04GB reclaimed, cache now 5.9GB, VM disk 43% → 7%. The prod catch-up and both recipe changes remain pending an "apply" direction.


## Issue #206: 'repair' command has no path to a carried Repair Kit — field repair is 'use' only, vendor repair needs an NPC

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-07 | Updated: 2026-08-07
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/206

### Body

Observed during the V24.12 Brief 1 playtest (repair-kit wiring, #134), filed thin at the moment of discovery.

**Observed behavior:** the `repair` command has no path to a carried Repair Kit. `repair <item>` / `repair all` require a repairer NPC in the room — with no repairer present the command refuses (`There is no one here who can repair.`), even when the player is carrying Repair Kits. Field repair works only through `use repair kit`.

**This is currently by design:** #134 ruled the kit as the field-repair *consumable* on the `use` pipeline (automatic most-damaged-first targeting, no roll), while `repair` remains vendor repair (the paid, rolled, NPC-hosted mechanic). The two are deliberately separate mechanics.

**Operator note:** may change this later — e.g. `repair` might fall back to (or offer) a carried kit when no repairer is present, or accept a kit-targeted form. No ruling yet; this issue records the observation and the possible future direction.


### Comments (0)

None.

## Issue #208: 'inv' still shows equipment and wallet — trim to inventory only ('equip' and 'wallet' own those views now)

- State: open
- Author: KnightOfNight
- Labels: output, V24
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-07 | Updated: 2026-08-07
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/208

### Body

## Current behavior

`inv` / `inventory` output is a three-part composite (shape established by #90): the equipment paper-doll, the inventory table, and the wallet line (`cmd_inventory`, `consumers.py`).

## Requested change

Trim `inv` to the inventory table only — drop the equipment paper-doll section and the wallet line. Both now have dedicated commands that own those views:

- Bare `equip` shows the equipment paper-doll (#195, shipped V24)
- `wallet` shows money

`inv` showing all three is a holdover from before those commands existed; the composite duplicates them.

## Implementation notes

- The equipped-items query must stay even though the paper-doll section goes: carry capacity is computed from effective STR (base + gear, #100) plus bag `carry_bonus` from equipped bags, and the `Inventory (N/M)` header still needs it.
- Help text needs the matching edit: `inventory (inv)` currently reads "Show your equipment, inventory, and wallet."
- GDD §9's `inv` entry describes the composite output — the GDD text change ships with the release that ships this (per the design-ahead rule), not before.

## Lineage

- #90 — established the composite Equipment/Inventory/Wallet output (B1 era, pre-dates the dedicated commands)
- #195 — bare `equip` paper-doll (the equipment view's new home)
- #76 — inv filters (adjacent, closed)


### Comments (1)

**KnightOfNight** — 2026-08-07:
Operator direction (2026-08-07, outside a design session): V24 membership confirmed — to be triaged and assigned to a specific point release in a design session, with the stated intent that it ships before the new-zone releases (i.e., within the V24 stream, ahead of V25.0/Z02–Z03).


## Issue #209: Research spike: player info on stat points — discoverability, what each stat controls, spend preview/simulator, and respec

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-07 | Updated: 2026-08-07
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/209

### Body

## Research spike — player-facing stat-point information

Players will ask (the operator is asking now):

- **How do I spend my stat points?** `spend [<quantity>] <stat>` exists, but how does a player discover it and know they have points to spend?
- **What happens when I give X points to stat Y?** What does each stat actually control? Today the consequences of an allocation are invisible before (and largely after) committing.
- **Maybe: an in-game stat-point simulator** — preview the effect of a prospective allocation before committing the expenditure.
- **Re-spending stats (respec)** — a very old topic, never tracked as an issue. Needs to be thought through alongside the above: any answer to "what does each stat do" raises "I allocated wrong, now what?"

## Spike deliverables

1. Survey the current information surfaces: `help`, `stats` output (which shows the unspent-points line), the spend flow itself, and what the GDD says about each stat.
2. Enumerate from code what each spendable stat actually controls (combat contest math, carry capacity, bars, regen, flee, etc.) — the authoritative ground truth an info surface would present.
3. Propose the info surface(s): help text, a `stats`-adjacent detail view, spend-time preview, and/or a full simulator — with rough scope for each option.
4. Frame the respec question for a design ruling: whether to allow it, cost/limits, and interaction with anything that keys off stats (e.g. the #109 bar-refill ruling).

Output is a findings/options writeup for a design session to rule on — no implementation in the spike.

## Adjacent prior work

- #131 — block stat spend during combat (closed)
- #109 — design ruling: mid-combat stat spend refills bars to new max (closed; superseded in part by #131)
- #91 — 'stats' output changes (closed)
- #142 — acuity in-combat drift design (open) — stat semantics still moving; the spike's stat-effects inventory should note what's unsettled


### Comments (3)

**KnightOfNight** — 2026-08-07:
Operator design thought (2026-08-07) — a middle option between static info and a standalone simulator: build the preview into the spend flow itself.

```
> spend 5 str
Your character will change in the following ways: (example: vitality goes up xyz points)
Confirm you want to spend these points?
```

Cost to weigh: this introduces conversational state — the consumer would have to listen for an answer and know the pending context. **No confirmation flow exists anywhere in the consumer today**; this would be the first pending-command state machine (what clears it — timeout, any other command, combat start, disconnect?). The spike should scope this pattern explicitly, since a confirm primitive, once built, is reusable (e.g. bulk-sell guards).

GDD ground truth on respec, for the spike's frame:

- **§12 Future Systems** lists **Stat Respec Mechanic** verbatim: "Allow players to rebalance already-spent stat points using in-game currency. Needs a dedicated design session." So the old topic is on the books, parked, with currency-cost as the sketched direction.
- **§3 Character System** separately says *skill* respec "is possible but costly (in-game currency and a cooldown period)", and §6 lists "skill respecs" among currency sinks — a distinct system (skills, not stat points), but establishes the pay-to-undo precedent the stat-respec ruling will want to stay consistent with.
- Also relevant: the bar law (§4.4) governs spend today — bar grows, fill fraction holds, never refills (#109 dead). Any respec design inherits that question in reverse (what happens to bars when points come *out* of a bar-feeding stat).


**KnightOfNight** — 2026-08-07:
Operator design thought (2026-08-07), option to add to the spike's menu: put the information directly in the `stats` output — next to each stat row, a short note of what it grants ("gives you vitality, gives you this, gives you that").

Zero conversational state, always visible at the moment a player is looking at their stats and deciding where points go. Composition note for the spike: the stat rows already carry a base + gear parenthetical (§9 character-sheet standard), so this is a second annotation per row — table column vs. trailing text is a layout question to settle alongside the row-width budget.

Running option menu so far, roughly in ascending effort: (1) stats-row annotations, (2) help/reference text, (3) spend-time preview + confirm (first pending-command state machine), (4) standalone simulator. Not mutually exclusive — (1) may be the floor that ships regardless of what else is ruled in.


**KnightOfNight** — 2026-08-07:
Operator sequencing confirmation (2026-08-07): **not part of V24.** Targeted to come soon after the first new zone release(s) — i.e., after V25.0 ships Z02/Z03. Membership label and point-release assignment to be settled by the design session that picks it up.


## Issue #211: Silver accessory tier: Mk 2 jewelry needs the tier-material ladder extended (silver definitions + Mk-mismatch ruling)

- State: open
- Author: KnightOfNight
- Labels: V24
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-08 | Updated: 2026-08-08
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/211

### Body

## Observation (V24.14 playtest, dev, 2026-08-07)

During the V24.14 Brief 1 (#130 gear stat band lift) playtest, three Mk 2 accessories were admin-gifted as instances of the **copper** definitions (`copper-ring-of-strength`, `copper-ring-of-dexterity`, `copper-amulet-of-endurance` at `mk_tier=2`). Operator finding: **nothing distinguishes them from their Mk 1 counterparts when examined except the stat values.** Tier-material names suppress the Mk suffix, so the name carries no tier signal — and the name says copper, which means Mk 1.

## The doctrine (GDD §6, tier-material naming rule)

> Items whose names carry a **tier material** — the copper → silver → gold → platinum ladder that tracks the currency table — do not display a Mark suffix, because the material already says the tier … Today the tier-material rule covers accessories only; later zones extend the ladder upward with the nobler metals as Mk tiers rise.

So the ladder's next rung is **silver**, and the doctrine already anticipates this: the material name IS the tier display. A "Copper Ring of Strength" at `mk_tier=2` is a name that lies. The seeded world never produces one (copper accessories drop only in Z01 at Mk 1) — the admin gift manufactured an off-doctrine instance.

## The gap

1. **The silver accessory definitions do not exist.** Mk 2 zones (Z02/Z03 — Version 25) need the ladder's second rung: `Silver Ring of <stat>` ×6 and `Silver Amulet of <stat>` ×6 as their own ItemDefinitions (`suppress_mk_suffix=True`, `mk_tier=2` at drop), mirroring the v18 copper set. Under the #130 band-lift doctrine their stat entries author Mk 1 midpoint + class lift like everything else (the Mk-2-native midpoints are a design call).
2. **Ruling wanted — the Mk-mismatch guard:** should tier-material definitions refuse instance generation (or at least warn) at a mismatched `mk_tier`? Nothing enforces name/tier agreement today; `generate_item_instance` and admin paths will happily mint a Mk 5 copper ring. Options range from a hard guard in generation to convention-only (seed discipline + admin care).

## Current state

- 12 copper accessory definitions (v18 kit), Z01 drop tables, Mk 1.
- Dev-only workaround for the in-flight playtest: three Silver clone definitions created directly on the dev DB (off-seed, operator-directed) and Harley Stone's three Mk 2 instances re-pointed to them. Dev state only — the seed does not author them; production untouched.

Filed from the V24.14 implementation session. Labeled V24 per operator direction — triage may move it (likely lands in V25/zone-build scope).


### Comments (0)

None.

## Closed Issues — Summary Table

| # | Title | Author | Labels | Closed |
|---|---|---|---|---|
| 130 | Secondary-stat curves vs Mk band growth — audit before Mk 2 content | KnightOfNight | triaged, V24, game-balance | 2026-08-08 |
| 104 | NPC HP must scale with level/Mk tier before any Mk 2 spawn is authored | KnightOfNight | triaged, V24, game-balance | 2026-08-07 |
| 134 | Repair kit not wired up yet | KnightOfNight | triaged, V24, itemization | 2026-08-07 |
| 80 | Design: item identification visibility — knowledge by holding | KnightOfNight | triaged, V24, itemization | 2026-08-05 |
| 127 | Ranged proc damage ("between X and Y") — new weapon kind, midpoint-and-spread family | KnightOfNight | triaged, V24, itemization | 2026-08-02 |
| 129 | Authored per-item armor base — guaranteed minimum coverage under rolled resist | KnightOfNight | triaged, V24, itemization | 2026-08-02 |
| 197 | Listing Slot cell hides either-hand flexibility — dual-slot weapons should read 'Main hand/Off hand' | KnightOfNight | triaged, V24 | 2026-08-02 |
| 194 | Weapon handed-ness is invisible to the player — two-handed never surfaced in item display; equip expectations form wrong (V24.6 playtest) | KnightOfNight | triaged, output, V24, itemization | 2026-08-02 |
| 176 | Equipment paper-doll renders consumed hand slots as free (two-handed weapons) | KnightOfNight | triaged, output, V24, itemization | 2026-08-02 |
| 195 | Bare 'equip' should show current equipment — shared composition with 'inv' paper-doll | KnightOfNight | triaged, V24, itemization | 2026-08-02 |
| 193 | GDD erratum: §5.4 claims unarmed base_damage = 0 — shipped code rolls uniform(1, 3) | KnightOfNight | errata | 2026-08-02 |
| 178 | Ranged slot semantics unruled — stat-swap flag only; equip asymmetry with two-handers; Pulse Pistol has no acquisition path | KnightOfNight | triaged, V24, itemization | 2026-08-02 |
| 177 | Combat ignores weapon slots — only one equipped weapon ever attacks; dual-wield contributes nothing | KnightOfNight | triaged, V24, game-balance, itemization | 2026-08-02 |
| 189 | Bare 'loot' behaves like 'loot all' — target becomes optional, defaulting to the sweep | KnightOfNight | triaged, V24 | 2026-08-02 |
| 166 | Top-level heal command — 'use infinity healing draughts' semantics | KnightOfNight | triaged, V24, healing-economy | 2026-08-02 |
| 187 | Closeout tails need a sanctioned production-seed path: make seed-prod (Instructions v31) | KnightOfNight | triaged, deployments | 2026-08-02 |
| 165 | Out-of-combat vitality regen is too slow and doesn't scale | KnightOfNight | triaged, V24, healing-economy | 2026-08-01 |
| 181 | Loot-table enrichment: healing draughts (and other items) as NPC drops | KnightOfNight | triaged, V24, healing-economy | 2026-08-01 |
| 164 | Healing economics: draught dependence outruns player income — sell values and money drops can't fund the staple | KnightOfNight | triaged, V24, healing-economy | 2026-08-01 |
| 180 | Post-gear-wiring fight-cost survey: measured HP loss, duration, and draughts-per-fight across NPC tiers | KnightOfNight | triaged, V24, healing-economy, game-balance | 2026-08-01 |
| 139 | Healing consumables can't track vitality growth — the draught tier needs an evolution pass | KnightOfNight | triaged, V24, healing-economy | 2026-08-01 |
| 175 | Process: major-version membership becomes labels; milestones are shipping releases only (Instructions v30) | KnightOfNight | triaged | 2026-07-30 |
| 173 | The release model: a constant stream of point releases — Instructions v29, closeout marker self-check, retirements | KnightOfNight | triaged | 2026-07-30 |
| 172 | GDD erratum: main §9 carries stale v23.3 pending-implementation markers (#149/#151) — cherry-pick 53e887f from the retiring version_24 branch | KnightOfNight | errata | 2026-07-30 |
| 170 | Playtest-disposition gate: implementation-session-end requires explicit operator disposition; closeout reads it from committed reports — Instructions v28 | KnightOfNight | triaged | 2026-07-29 |
| 162 | Redo home timings: cooldown 15m to 5m, countdown 15s to 10s | KnightOfNight | B1, triaged | 2026-07-29 |
| 168 | GDD §6/§9 say use-heal consumption is lowest-value first; shipped v23.3 behavior is oldest-first | KnightOfNight | errata | 2026-07-29 |
| 169 | Codify GDD errata as ops work on main — Instructions v27 + Rule 3 scope line | KnightOfNight | triaged | 2026-07-29 |
| 151 | Multi-use healing floods the pane — compute the heal once, consume what's needed, send one message | KnightOfNight | B1, triaged, output | 2026-07-29 |
| 149 | Using a consumable prints two lines — merge the use sentence and the effect message into one | KnightOfNight | B1, triaged, output | 2026-07-29 |
| 160 | End rituals for all session types — positive confirmation at every level, closeout fails hard early on unended sessions, Instructions v26 | KnightOfNight | triaged | 2026-07-28 |
| 155 | shyland_issues_report.py crashes on Python 3.9 — require 3.14+ via env line and explicit version guard | KnightOfNight | bug, B1, triaged | 2026-07-28 |
| 158 | Iteration 2: the closeout session — type, stamp whitelist, tail deploy, merge terms, instructions v25, -DEV CI gate | KnightOfNight | triaged, deployments | 2026-07-28 |
| 156 | Codify the standing release flow — prod runs main only, main never carries -DEV; must land before v23.1 closeout | KnightOfNight | triaged, deployments | 2026-07-26 |
| 150 | Protect players from 'sell all'-ing their potions — bulk sell needs a consumable guard | KnightOfNight | B1, emergent, triaged | 2026-07-26 |
| 152 | V23 output-color pass: narration/system to value-color, direction-split miss colors, copper-loot line to reward | KnightOfNight | B5, triaged, output | 2026-07-25 |
| 147 | First-contact greetings render as speech — the NPC's name is printed twice | KnightOfNight | bug, B4, triaged | 2026-07-25 |
| 40 | Free repair messages repeat too often (Morra example) — research spike into other duplication cases | KnightOfNight | B4, triaged | 2026-07-25 |
| 144 | Six service NPCs have zero dialogue entries — they have never greeted anyone | KnightOfNight | bug, B4, triaged | 2026-07-25 |
| 146 | Remove dead ItemInstance.is_artifact field — a trap for hand-authored artifacts | KnightOfNight | bug, B4, triaged | 2026-07-25 |
| 138 | Bound zero-value items have no disposal path — starter kit junk is stuck in inventory forever | KnightOfNight | bug, B4, triaged | 2026-07-25 |
| 141 | text cleanup | KnightOfNight | B3, triaged | 2026-07-24 |
| 119 | do not change border colors | KnightOfNight | bug, B3, triaged | 2026-07-24 |
| 133 | Focus Tonic overshoots the acuity band system and announces no-op ticks at the 1.9 clamp | KnightOfNight | bug, B3, triaged | 2026-07-24 |
| 25 | Bosses do not heal when the player disengages | KnightOfNight | bug, B1, triaged | 2026-07-24 |
| 143 | Flee is mathematically impossible — the contest computes NPC PER with pre-v21 scaling_factor semantics | KnightOfNight | bug, B1, triaged | 2026-07-24 |
| 137 | Corpse decay orphans unlooted contents — ItemInstance rows leak with no location | KnightOfNight | bug, B2, triaged | 2026-07-24 |
| 18 | Animal Hides Don't Stack in Inventory | KnightOfNight | bug, B2, triaged | 2026-07-24 |
| 117 | shyland: stub tests.py shadows tests/ package — breaks whole-app test discovery | KnightOfNight | bug, B2, triaged | 2026-07-24 |
| 27 | Research: passive regen ticks landing after combat engagement | KnightOfNight |  | 2026-07-23 |
| 140 | GDD split: per-section source files with a generated monolith | KnightOfNight |  | 2026-07-22 |
| 135 | Tick engine crashes (SynchronousOnlyOperation) on every full timed-effect expiry — unwrapped ORM call in the async expiry-message path | KnightOfNight | bug | 2026-07-22 |
| 132 | Shortfall and no-effect reports render in the muted system voice | KnightOfNight |  | 2026-07-22 |
| 131 | Block stat spend during combat | KnightOfNight |  | 2026-07-21 |
| 110 | apply_stat_effect races the engine's effect-expiry reversal (cached-object RMW on stat fields) | KnightOfNight | B5 | 2026-07-21 |
| 109 | Design ruling: mid-combat stat spend refills bars to new max (bankable free heal) | KnightOfNight | B5 | 2026-07-21 |
| 100 | Wire equipped item stats into combat (armor mitigation, stat bonuses) | KnightOfNight | B5 | 2026-07-21 |
| 128 | B5 knob survey — armor/proc tuning dataset from code and production DB | KnightOfNight |  | 2026-07-21 |
| 112 | new command: sudo | KnightOfNight | B3 | 2026-07-20 |
| 88 | new command: last | KnightOfNight | stub, B3 | 2026-07-20 |
| 113 | new command: cancel | KnightOfNight | B3 | 2026-07-20 |
| 57 | new command: home [now] | KnightOfNight | B3 | 2026-07-20 |
| 120 | add version number of running game to 'help' output using key/value display type 1 | KnightOfNight | B2 | 2026-07-20 |
| 124 | color fixes | KnightOfNight | B2 | 2026-07-20 |
| 123 | Item listing fixes | KnightOfNight | B2 | 2026-07-20 |
| 122 | invariant: players and NPCs may never share a name | KnightOfNight | B2 | 2026-07-19 |
| 121 | client renders error category as amber, ignoring --error | KnightOfNight | bug, B2 | 2026-07-19 |
| 98 | command 'who' needs color output | KnightOfNight | stub, B2 | 2026-07-19 |
| 96 | examine doesn't autocomplete on NPC name | KnightOfNight | stub, B2 | 2026-07-19 |
| 75 | repair all should retry, not need multiple manual tries | KnightOfNight | B2 | 2026-07-19 |
| 67 | tab completion doesn't work for 'equip' | KnightOfNight | B2 | 2026-07-19 |
| 65 | 'use 3 heal' responds with 'You can't use everything at once.' | KnightOfNight | B2 | 2026-07-19 |
| 61 | refuse to use a healing draught if player vitality is full | KnightOfNight | B2 | 2026-07-19 |
| 59 | some commands not logged in timestamped output | KnightOfNight | bug, B2 | 2026-07-19 |
| 58 | vendor for-sale list changes | KnightOfNight | B2 | 2026-07-19 |
| 54 | consider how to simplify combat language and make it more human | KnightOfNight | B2 | 2026-07-19 |
| 29 | Block looting (and related inventory commands) during combat | KnightOfNight | B2 | 2026-07-19 |
| 111 | command revamp | KnightOfNight | B2 | 2026-07-19 |
| 93 | command behavior inconsistencies when no arguments passed | KnightOfNight | B2 | 2026-07-19 |
| 76 | inv should take filters like buy or sell | KnightOfNight | stub, B2 | 2026-07-19 |
| 115 | Map pane: restore breathing room lost to v21 zone-colored borders | KnightOfNight | bug, B1 | 2026-07-19 |
| 82 | map changes | KnightOfNight | B1 | 2026-07-19 |
| 116 | No single-session enforcement — two simultaneous logins on one character desync and race | KnightOfNight | bug, B1, emergent | 2026-07-18 |
| 17 | New NPC Spawn Doesn't Agro Immediately | KnightOfNight | bug, B2 | 2026-07-17 |
| 64 | Unify NPC ordering: targeting order, N.noun index, and ordinal labels disagree | KnightOfNight | bug, B2 | 2026-07-17 |
| 52 | In-combat heals apply on stale character state, resurrecting persisted damage (lost-update race) | KnightOfNight | bug, B2 | 2026-07-17 |
| 107 | Tick engine runs ~5s/tick — combat rounds land at ~15.5s vs ~3-4s design (per-row DB calls in every per-tick sweep) | KnightOfNight | bug, emergent | 2026-07-17 |
| 103 | Make placeholder roster NPCs unattackable (Aldric, Info Prime, Seris, Veris) | KnightOfNight | B3 | 2026-07-17 |
| 102 | Rule the ×3 aggro-elite rooms deadly-by-design: signpost them, ×2 rooms are the solo ceiling | KnightOfNight | B3 | 2026-07-17 |
| 101 | Retune the Z01 boss ladder: HP curve and boss DEX offset, balanced for even-split builds | KnightOfNight | B3 | 2026-07-17 |
| 68 | broadsword has a lifesteal value of zero | KnightOfNight | bug, B3 | 2026-07-17 |
| 66 | Balance: the Whistler Below is a difficulty cliff — contest scale doubles at boss #2 | KnightOfNight | B3 | 2026-07-17 |
| 89 | Survey: kill-feasibility audit of all seeded NPC tiers (contest scale and HP vs. attainable player capability) | KnightOfNight | B3 | 2026-07-17 |
| 97 | Reduce the room separator height from 5px to 3px | KnightOfNight | B1 | 2026-07-17 |
| 92 | 'wallet' output changes | KnightOfNight | B1 | 2026-07-16 |
| 91 | 'stats' output changes | KnightOfNight | B1 | 2026-07-16 |
| 90 | 'inv' and output changes | KnightOfNight | B1 | 2026-07-16 |
| 86 | Colorize area and room description prose to match the location bar | KnightOfNight | B1 | 2026-07-16 |
| 85 | make the pane borders match the HR in style and color | KnightOfNight | B1 | 2026-07-16 |
| 84 | player help fixes | KnightOfNight | bug, B1 | 2026-07-16 |
| 81 | we need to adjust what a player sees for room description when entering an agro room | KnightOfNight | B1 | 2026-07-16 |
| 60 | change flag "Droppable" to "Unbound" | KnightOfNight | B1 | 2026-07-16 |
| 55 | "who's here" list doesn't need "is here" at the end of every line | KnightOfNight | bug, B1 | 2026-07-16 |
| 53 | map gates are gray (ed out) even if they have been passed by the player | KnightOfNight | bug | 2026-07-16 |
| 83 | command 'brief' not listed in player help | KnightOfNight | bug | 2026-07-16 |
| 79 | NPC grammar: indefinite article on first presentation; occupant lines capitalized | KnightOfNight | bug | 2026-07-16 |
| 78 | Add a zone-colored separator between the room block and event lines | KnightOfNight |  | 2026-07-16 |
| 77 | Remove the bracketed room header from the output pane | KnightOfNight |  | 2026-07-16 |
| 28 | Corpse decay and empty-loot messaging is noisy and misleading | KnightOfNight |  | 2026-07-15 |
| 24 | NPC display grammar: article stacking in combat messages | KnightOfNight |  | 2026-07-15 |
| 15 | Show Commands in Output Window for Context | KnightOfNight |  | 2026-07-15 |
| 39 | Output colorization: section header labels ('Exits:', 'Who's here?', 'What's here?') should share one color | KnightOfNight |  | 2026-07-15 |
| 14 | Look-Command Output Sections | KnightOfNight |  | 2026-07-15 |
| 13 | Combat Messages Colors | KnightOfNight |  | 2026-07-15 |
| 74 | Bulk repair joins all lines into one message; split per-repair per the #63 ruling | KnightOfNight | bug | 2026-07-15 |
| 51 | right pane has horizontal and vertical scrollbars | KnightOfNight | bug | 2026-07-15 |
| 73 | Browser window scrollbar present at every size; app should fit the viewport exactly | KnightOfNight | bug | 2026-07-15 |
| 72 | Player stats render as plain text; make V/L bars and A a band gauge like the fight panel | KnightOfNight |  | 2026-07-15 |
| 71 | Right-pane stats header says SHYLAND instead of the character name | KnightOfNight | bug | 2026-07-15 |
| 31 | Shyland: richer live connection status indicator (beyond static "Connected to Shyland") | KnightOfNight |  | 2026-07-15 |
| 2 | Right Pane Design | KnightOfNight |  | 2026-07-15 |
| 1 | Location Bar Updates - Complete Breadcrumb Trail by Name | KnightOfNight |  | 2026-07-15 |
| 63 | Bulk sell batches all sale lines into one message; split per-sale like loot | KnightOfNight | bug | 2026-07-15 |
| 62 | loot all should sweep every corpse in the room, not one corpse | KnightOfNight |  | 2026-07-15 |
| 48 | Move rarity out of item display names into the status flag block | KnightOfNight |  | 2026-07-15 |
| 45 | New command: timestamps on\|off (player preference for output timestamp display) | KnightOfNight |  | 2026-07-15 |
| 23 | Leaving a room by cardinal direction command does not end combat like 'flee' does. | KnightOfNight | bug | 2026-07-15 |
| 20 | Command 'loot all' throws hidden unhandled exception and disconnects player websocket | KnightOfNight | bug | 2026-07-15 |
| 19 | Automatic command completion | KnightOfNight |  | 2026-07-15 |
| 21 | New command: sell all | KnightOfNight |  | 2026-07-15 |
| 3 | New Command: loot all | KnightOfNight |  | 2026-07-15 |
| 22 | Command nouns and verbs: allow better item references, allow plural references | KnightOfNight |  | 2026-07-15 |
| 56 | Timestamps display on renderings and state reports; should mark events only | KnightOfNight | bug | 2026-07-15 |
| 32 | Shyland: output messages need timestamps and guaranteed ordering | KnightOfNight |  | 2026-07-14 |
| 50 | map only displays one circle with gray lines when you enter a new room with agro | KnightOfNight | bug | 2026-07-14 |
| 49 | Checkpoint shard wording: remaining sphere->shard fixes (Stairhead, Cragfoot, shard entity, villager lines) | KnightOfNight | bug | 2026-07-14 |
| 36 | Map system client: right-pane map rendering (node-and-line, fog-of-war) | KnightOfNight |  | 2026-07-14 |
| 35 | Map system backend: MapFrag derivation, exit boundary flags, map data payload | KnightOfNight |  | 2026-07-14 |
| 46 | Fordwatch (vr-v07) brief description: "sphere" should be "shard" | KnightOfNight | bug | 2026-07-14 |
| 44 | Z01 geometry fixes: Stonestep/Highfold relabels, surface z-flattening, boundary-flag seeding list | KnightOfNight |  | 2026-07-14 |
| 43 | Z05 ring re-lay: realize the chamfer (6 rooms, 3 relabels, spoke re-lay, 2 ring vendors) | KnightOfNight |  | 2026-07-14 |
| 16 | Change Description and Output to be Different Panes | KnightOfNight |  | 2026-07-13 |
| 42 | Audit: intra-MapFrag spatial consistency of The Convergence and Z01 room graphs | KnightOfNight |  | 2026-07-13 |
| 34 | Aldric's help response gives wrong direction to the Verdant Reach gate | KnightOfNight | bug | 2026-07-12 |
