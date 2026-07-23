# Shyland Issues Report

- Generated: 20260723T142533Z
- Repo: KnightOfNight/games-mvc
- Open issues: 38
- Closed issues: 95
- Dependency data: available

## Open Issues — Summary Table

| # | Title | Author | Labels | Milestone | Updated |
|---|---|---|---|---|---|
| 4 | Build Zone: Ashenveil Cathedral (Z02) | KnightOfNight |  | Z02 - Ashenveil Cathedral | 2026-07-12 |
| 5 | Build Zone: The Neon Sprawl (Z03) | KnightOfNight |  | Z03 - The Neon Sprawl | 2026-07-12 |
| 6 | Build Zone: The Blasted Flats (Z04) | KnightOfNight |  | Z04 - The Blasted Flats | 2026-07-12 |
| 7 | Build Zone: The Iron Deeps (Z06) | KnightOfNight |  | Z06 - The Iron Deeps | 2026-07-12 |
| 8 | Build Zone: The Pale Shore (Z07) | KnightOfNight |  | Z07 - The Pale Shore | 2026-07-12 |
| 9 | Build Zone: The Wastelands (Z08) | KnightOfNight |  | Z08 - The Wastelands | 2026-07-12 |
| 10 | Transactional email via Postmark (password resets) | KnightOfNight |  | Authentication | 2026-07-22 |
| 11 | Account onboarding via unusable password + reset link (no temp passwords) | KnightOfNight |  | Authentication | 2026-07-22 |
| 12 | Two-factor authentication via TOTP (django-otp) | KnightOfNight |  | Authentication | 2026-07-22 |
| 18 | Animal Hides Don't Stack in Inventory | KnightOfNight | bug | Version 23 | 2026-07-22 |
| 25 | Bosses do not heal when the player disengages | KnightOfNight | bug | Version 23 | 2026-07-22 |
| 26 | Boss and elite kills pay flat XP — no tier multiplier | KnightOfNight |  | Version 24 | 2026-07-22 |
| 30 | Travel network: should checkpoints (shards) also be travel senders? | KnightOfNight |  | Version 24 | 2026-07-22 |
| 33 | Shyland: persist detailed combat logs for balance analysis | KnightOfNight |  | Firehose Logging | 2026-07-12 |
| 37 | Universal event logging (firehose): every command, every output, every event | KnightOfNight |  | Firehose Logging | 2026-07-12 |
| 38 | Obelisk attunement: player-set home spawn at checkpoint shards | KnightOfNight |  | Version 24 | 2026-07-22 |
| 40 | Free repair messages repeat too often (Morra example) — research spike into other duplication cases | KnightOfNight |  | Version 23 | 2026-07-23 |
| 41 | Lock battle-zone access until a new player has visited all of The Convergence | KnightOfNight |  | Version 24 | 2026-07-22 |
| 47 | Right pane: player effects display (sent and received) | KnightOfNight |  | Version 24 | 2026-07-22 |
| 70 | Feature: Longevity has no drain — the slow-burn design needs its first consuming mechanic | KnightOfNight |  | Version 24 | 2026-07-22 |
| 80 | Design: item identification visibility — knowledge by holding | KnightOfNight |  | Version 24 | 2026-07-22 |
| 95 | the ring needs an area | KnightOfNight | stub | Version 24 | 2026-07-22 |
| 104 | NPC HP must scale with level/Mk tier before any Mk 2 spawn is authored | KnightOfNight |  | Version 24 | 2026-07-22 |
| 105 | Elite even-level −5% hit calibration drift (rounding parity) | KnightOfNight |  | Version 24 | 2026-07-22 |
| 117 | shyland: stub tests.py shadows tests/ package — breaks whole-app test discovery | KnightOfNight | bug, triaged | Version 23 | 2026-07-23 |
| 119 | do not change border colors | KnightOfNight | bug | Version 23 | 2026-07-22 |
| 125 | player macro/alias system | KnightOfNight |  | Version 24 | 2026-07-22 |
| 126 | pluralization subsystem — natural-English plurals for aggregate output | KnightOfNight |  | Version 24 | 2026-07-22 |
| 127 | Ranged proc damage ("between X and Y") — new weapon kind, midpoint-and-spread family | KnightOfNight |  | Version 24 | 2026-07-22 |
| 129 | Authored per-item armor base — guaranteed minimum coverage under rolled resist | KnightOfNight |  | Version 24 | 2026-07-22 |
| 130 | Secondary-stat curves vs Mk band growth — audit before Mk 2 content | KnightOfNight |  | Version 24 | 2026-07-22 |
| 133 | Focus Tonic overshoots the acuity band system and announces no-op ticks at the 1.9 clamp | KnightOfNight | bug | Version 23 | 2026-07-22 |
| 134 | Repair kit not wired up yet | KnightOfNight |  | Version 24 | 2026-07-22 |
| 137 | Corpse decay orphans unlooted contents — ItemInstance rows leak with no location | KnightOfNight | bug, triaged | Version 23 | 2026-07-23 |
| 138 | Bound zero-value items have no disposal path — starter kit junk is stuck in inventory forever | KnightOfNight | bug, triaged | Version 23 | 2026-07-23 |
| 139 | Healing consumables can't track vitality growth — the draught tier needs an evolution pass | KnightOfNight |  | Version 24 | 2026-07-22 |
| 141 | text cleanup | KnightOfNight | triaged | Version 23 | 2026-07-23 |
| 142 | Finish the acuity design: in-combat drift is unruled | KnightOfNight |  | Version 24 | 2026-07-23 |

## Open Issues — Full Detail

## Issue #4: Build Zone: Ashenveil Cathedral (Z02)

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Z02 - Ashenveil Cathedral
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-12
- Blocked by: none
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
- Labels: none
- Milestone: Z03 - The Neon Sprawl
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-12
- Blocked by: none
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
- Labels: none
- Milestone: Z04 - The Blasted Flats
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-12
- Blocked by: none
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
- Labels: none
- Milestone: Z06 - The Iron Deeps
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-12
- Blocked by: none
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
- Labels: none
- Milestone: Z07 - The Pale Shore
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-12
- Blocked by: none
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
- Labels: none
- Milestone: Z08 - The Wastelands
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-12
- Blocked by: none
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
- Labels: none
- Milestone: Authentication
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-22
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
- Labels: none
- Milestone: Authentication
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-22
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
- Labels: none
- Milestone: Authentication
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-22
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

## Issue #18: Animal Hides Don't Stack in Inventory

- State: open
- Author: KnightOfNight
- Labels: bug
- Milestone: Version 23
- Assignees: none
- Created: 2026-07-11 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/18

### Body

Healing Draughts stack in inventory. Animal Hides should too.

Look at all stackable-or-not issues.

Insect Carapace

### Comments (2)

**KnightOfNight** — 2026-07-12:
Interacts with #22 (command grammar): stackability changes what plural references like "sell all hides" resolve to. Design the two against each other.

**KnightOfNight** — 2026-07-13:
V20 planning ruling: deferred — not in Version 20.

The coupling with #22 flagged in the earlier comment is resolved by ruling #22's grammar stacking-agnostic ('all X' resolves over matching item instances regardless of display representation). This issue is therefore purely a display/inventory-representation change with no command-grammar implications, and can land in any later version without touching #22's design.

## Issue #25: Bosses do not heal when the player disengages

- State: open
- Author: KnightOfNight
- Labels: bug
- Milestone: Version 23
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/25

### Body

Verified empirically during the v19 Silk Matron playtest: damage dealt to a boss persists indefinitely after the player flees. A player can chip a boss down, flee, regenerate to full, and return repeatedly — the boss never recovers. This makes chip-and-run the strictly optimal (and trivializing) strategy against every boss.

Expected behavior: bosses heal when the player disengages (flee/leave). Implementation details — full reset vs. regeneration rate, what counts as disengagement, whether this applies to non-boss NPCs too — need discussion and planning before implementation.

Note: the first Matron kill was a straight fight with no fleeing; this was discovered through a deliberate second-visit experiment.


### Comments (0)

None.

## Issue #26: Boss and elite kills pay flat XP — no tier multiplier

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/26

### Body

XP awards derive from NPC level only. In the v19 Matron fight: Silk Matron (level-3 boss, 120 vitality, minion adds) paid 30 XP — identical to a level-3 cave beetle. Her brood paid 20, same as any level-2 normal. Risk/reward is flat across the normal/elite/boss tiers even though difficulty now scales sharply by tier (Brief 7's contest offsets).

Proposal direction: a tier-based XP multiplier. **How much more bosses and elites should pay needs discussion and planning — the amount is explicitly NOT decided in this issue.**


### Comments (0)

None.

## Issue #30: Travel network: should checkpoints (shards) also be travel senders?

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-22
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


### Comments (2)

**KnightOfNight** — 2026-07-12:
Companion issue filed as promised: #38 (obelisk attunement / player-set home spawn).

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19). Deferred: the B4 travel/attunement bucket is dropped from Version 22. This item belongs to a future version dedicated to zones and travel — revisit at that version's planning, alongside #41 and #95 which carry the same disposition. Version 22 retains only the travel destination-listing order (ascending distance, shard/sphere labels), captured in the B2 spec DD. For v22, home ships pointing at its default destination (The Convergence).


## Issue #33: Shyland: persist detailed combat logs for balance analysis

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Firehose Logging
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-12
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
- Labels: none
- Milestone: Firehose Logging
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-12
- Blocked by: #32
- Blocks: #112
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
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-22
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


### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19). Deferred: the B4 travel/attunement bucket is dropped from Version 22. This item belongs to a future version dedicated to zones and travel — revisit at that version's planning, alongside #41 and #95 which carry the same disposition. Version 22 retains only the travel destination-listing order (ascending distance, shard/sphere labels), captured in the B2 spec DD. For v22, home ships pointing at its default destination (The Convergence).


## Issue #40: Free repair messages repeat too often (Morra example) — research spike into other duplication cases

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 23
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-23
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/40

### Body

## Summary

Free-repair flavor messages repeat too often — the same line fires on every free repair from a given NPC, which reads as noise once a player has seen it more than once or twice.

## Example

Morra, on a free repair:

> Morra turns the piece over once, snorts softly, and fixes it for nothing. "Come back when you've got something worth charging for."

This is the only free-repair line for Morra, so every free repair from her produces this exact text.

## Research spike

Before fixing this NPC-by-NPC, audit the scope of the problem:

- Which other NPCs offer free repairs, and how many flavor-message variants does each have (likely also just one each)?
- Do paid repairs have the same single-message-per-NPC problem, or do they already have variety?
- Are there other non-repair NPC interactions with the same single-line-repeated-verbatim pattern worth folding into the same fix (dedupe the audit, not just the repair case)?

## Out of scope (for the spike)

- Writing the additional message variants themselves — that's a follow-up once the audit above defines the scope


### Comments (1)

**KnightOfNight** — 2026-07-23:
## V23 research spike — duplication audit (facts only; no variants written, no code changed)

### Summary table

| Site | NPC(s) | Variants | Data-only or code-change |
|---|---|---|---|
| Free ("pity") repair line | Morra, Pella, Ferwick, Repairbot Prime | **1 each** | Code (constant dict, no selection machinery) |
| Free repair fallback | Maro the Mender, Tavik the Mender, Old Brammel | **1 shared template** | Code |
| Paid repair — success | all repairers | 1 bulk + 1 single template | Code |
| Paid repair — failure | all repairers | 1 bulk + 1 single template | Code |
| Paid repair — can't afford | all repairers | 1 bulk + 1 single template | Code |
| Vendor buy transaction | all vendors | 1 (×1) + 1 (×N) — vendor never speaks | Code |
| Vendor sell transaction | all vendors | 1 (×1) + 1 (×N); one voiced refusal line | Code |
| Vendor list header / sold-out | all vendors | 1 each | Code |
| Kibitz (second vendor reacts) | gazebo vendor pairs | **3**, `random.choice` | Code-constant edit (machinery exists) |
| Keyword dialogue (say-triggered) | 10 Convergence NPCs | **1–3 per entry**, random + no-consecutive-repeat | **Pure data** (seed rows) |
| First-contact greetings | same 10 NPCs | 1 each — but fires once ever per character | Pure data (pool machinery exists) |
| Departure reactions | Aldric, Info Prime, Morra, Pella, Ferwick, Repairbot Prime | **1 each** (repeats per walk-out) | Pure data |
| Multi-speaker connectives | any dialogue NPC | 3 + 3, `random.choice` | Pure data |
| Obelisk travel messages | system | 10 / 6 / 6, `random.choice` | Pure data |
| Aggro engagement ("snarls and moves to attack!") | every aggressive NPC | **1**, hardcoded at 3 sites | Code |
| NPC `death_message` | 9 bosses | **1 scalar field per NPC** | Code + schema (migration) |
| Unarmed combat flavor | players & NPCs | pooled, `random.choice` | Pure data |
| Ambient/idle barks | — | **system does not exist** | n/a |
| Verdant Reach service NPCs' dialogue | Maro, Tavik, Old Brammel, Essa, Sona, Ridda | **0 entries** — never greet, never answer | Pure data to add |

All paths below are under `django/src/apps/shyland/`.

### 1. Free-repair audit — issue confirmed

Seven NPCs repair (`is_repairer=True`): Morra, Pella, Ferwick, Repairbot Prime (`seed_world.py:1394` `CONVERGENCE_SERVICE_NPCS`, wired at `:1550`), plus Maro the Mender (`seed_world.py:6140`), Tavik the Mender (`:6152`), and Old Brammel (`:6535`; the trio is also asserted at `:2780`).

**Morra has exactly one free-repair line — confirmed** — and so does every other pity-repair NPC. The four Convergence lines are a dict of single strings, `consumers.py:64-84` (`PITY_REPAIR_LINES`); the three Verdant menders all share one fallback sentence, `consumers.py:82-84`:

```python
PITY_REPAIR_FALLBACK = (
    '{name} looks your battered gear over, takes pity, and repairs it for nothing.'
)
```

The composition site proves there is no variant machinery — `consumers.py:87-91` is a straight dict lookup, no `random.choice`:

```python
def _pity_repair_line(repairer):
    template = PITY_REPAIR_LINES.get(repairer.definition.slug)
    if template:
        return template
    return PITY_REPAIR_FALLBACK.replace('{name}', ...)
```

Emitted at `consumers.py:2037` (bulk) and `:2085` (single). The text lives entirely in Python constants — not DB-backed, so adding variety is a code change (list + `random.choice`), but no migration.

### 2. Paid-repair audit — one template per outcome, shared by all repairers

`do_repair_attempt` (`consumers.py:3763-3788`) returns only an outcome; all text is hardcoded f-strings in `cmd_repair` (`consumers.py:1994-2096`). Outcomes have variants; NPCs do not — each outcome is one template with the NPC name interpolated (bulk success doesn't even name the repairer):

- success: `:2039-2043` (bulk, `'{name} is restored to full condition. (cost)'`), `:2087-2090` (single)
- failure: `:2047-2051` (bulk), `:2092-2096` (single, `"...works on your {name}, but the mending didn't take."`)
- can't afford: `:2026-2030` (bulk), `:2078-2082` (single)

Code change to add variety.

### 3. Wider sweep

**Vendor transactions — no NPC flavor exists at all.** Buy success: `consumers.py:1907-1916` (`'You buy X for Y.'` — the vendor never speaks). Sell: `:1940`, `:1973-1981`; the one voiced line is the hardcoded refusal `"That's not worth anything to me."` (`:1936`). List header `:1837`, sold-out `:1809`. All single templates → code change. The **one existing vendor-flavor mechanism is kibitz** (second vendor in the room reacts after a completed trade): pool of 3 with `random.choice`, `consumers.py:58-62` + `maybe_kibitz` `:2874-2886`. Machinery exists; the pool is a Python constant, so new lines are a code-constant edit, no migration.

**Keyword dialogue (there is no `talk` command — dialogue triggers off `say` keyword matching) — the one properly variant-ready system.** Storage is row-per-variant: `DialogueEntry` (`models.py:1054-1076`) with child pool `DialogueResponse.text` (`models.py:1082-1086`). Selection is random twice: entry pick `consumers.py:3856`, response pick with a no-consecutive-repeat guard `run_tick_engine.py:1405-1418`. **Adding variants is pure seed data, zero code, zero migrations.** Current counts (`seed_world.py:1637-2076`):

| NPC | keyword entries (responses each) | greeting | departed |
|---|---|---|---|
| Aldric | help 3, obelisk 2 | 1 | 1 |
| Info Prime | help 2, network **1** | 1 | 1 |
| Morra | repair 3, wares 3, help 2 | 1 | 1 |
| Pella | help 3, wares 3, bag 2 | 1 | 1 |
| Ferwick | help 3, wares 3, bag 2 | 1 | 1 |
| Repairbot Prime | repair 3, help **1** | 1 | 1 |
| Seris | obelisk 3, help 2 | 1 | — |
| Veris | obelisk 3, help 2 | 1 | — |
| VND-9 | wares **1**, thanks **1** | 1 | — |
| Mother Tansy | wares **1**, thanks **1** | 1 | — |

Bolded **1**s repeat verbatim today (e.g. Info Prime `network`, `seed_world.py:1697-1705`). Greetings are single-authored but gated to fire **once ever per character** (`DialogueGreetingRecord`, `consumers.py:3892-3895`, unique-together `models.py:1145`) — not a repetition problem in practice. Departure reactions (1 each for the six NPCs that have them) do repeat on every walk-out; the read site already has random-with-exclusion machinery (`run_tick_engine.py:1432-1442`), so more lines are pure data.

**Dialogue coverage gap found while auditing:** the six Verdant Reach service NPCs — Maro the Mender, Tavik the Mender, Old Brammel, Essa the Trader, Sona the Trader, Ridda the Trader — have **no dialogue entries at all** (`_seed_npc_dialogue` is called for exactly the 10 Convergence-era slugs, `seed_world.py:1637-2049`). They never greet and never answer. Pure data to add; engine ready.

**Ambient/idle barks: the system does not exist.** No timer-driven NPC bark surface anywhere; `NpcDefinition.wanders` is marked not yet implemented (`models.py:719`). The tick engine's only NPC message surfaces are dialogue delivery, departure reactions, death messages, and respawn-aggro engagement.

**Other repeated-verbatim sites found:**
- **Aggro engagement line** — one authored string, three sites: `consumers.py:634-638` (walk-in), `:2222` (flee-into-aggro), `run_tick_engine.py:932-935` (respawn engagement). Every aggressive NPC "snarls and moves to attack!" identically. Code change.
- **`death_message`** — a single scalar `TextField` on `NpcDefinition` (`models.py:767`), broadcast verbatim at `run_tick_engine.py:543-544`; authored for 9 bosses (`seed_world.py:6213-6234`, `:6590-6610`). Variants would need a schema change (child table or list field) plus a selection at the read site — the only category here needing a migration.
- Already variant-ready pools, for contrast: obelisk travel messages (`TravelMessage`, `models.py:978-986`; 10/6/6 seeded `seed_world.py:2136-2171`; `random.choice` `consumers.py:3414-3419`) and unarmed combat flavor (`UnarmedMessagePool`, `models.py:163-181`; `combat_utils.py:424`). Both pure data.

### 4. Mechanism bottom line (for scoping the follow-up)

- **Pure data (seed rows, zero code):** keyword dialogue responses, greetings, departure reactions, connectives, travel messages, unarmed pools — plus filling the Verdant six's empty dialogue.
- **Code-constant edits (no DB):** kibitz pool (machinery exists); pity-repair lines (machinery absent — dict of single strings).
- **Code changes (hardcoded single f-strings, no selection machinery):** paid-repair outcome lines, vendor buy/sell/list/sold-out lines, the aggro "snarls" line (3 sites).
- **Code + migration:** `death_message` (scalar field).


## Issue #41: Lock battle-zone access until a new player has visited all of The Convergence

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-22
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


### Comments (1)

**KnightOfNight** — 2026-07-18:
Deferred (2026-07-17): revisit in the next major version that releases new zones.


## Issue #47: Right pane: player effects display (sent and received)

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-13 | Updated: 2026-07-22
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


### Comments (0)

None.

## Issue #70: Feature: Longevity has no drain — the slow-burn design needs its first consuming mechanic

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-15 | Updated: 2026-07-22
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


### Comments (0)

None.

## Issue #80: Design: item identification visibility — knowledge by holding

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-16 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/80

### Body

Found in v20 Brief 5 playtesting: dropping an item flips is_identified False (deliberate v18 behavior, per the model help text) but the identification system it fed was never built — a one-way trapdoor: any dropped item is mystery-named forever, for everyone, including its original owner on re-pickup. The database record is fully intact; the boolean is purely a presentation gate.

RULED DESIGN DIRECTION (2026-07-15, for a future version — deliberately unmilestoned):
- Knowledge is a property of HOLDING; single boolean, no per-character tracking.
- A ground item shows its mystery name in the room listing and to all observers.
- `examine` is close inspection: it reveals the item's REAL details without requiring pickup.
- Picking the item up flips is_identified True — permanent unlock of normal display.
- Drop continues to re-veil (flips False) — the item becomes a stranger the moment it leaves hands.
- The future identification SERVICE (NPC/skill, per the GDD) then concerns curses and deeper properties, not basic nature. is_unidentifiable interplay preserved.
- Ride-along cleanup for that fix: examine's unidentified branch currently prints two redundant cannot-determine lines; also durability displays truthfully on unidentified items (arguably leaks real data through the veil) — resolve both in the same design pass.

No code changes in v20; filed for a future version's triage.

### Comments (0)

None.

## Issue #95: the ring needs an area

- State: open
- Author: KnightOfNight
- Labels: stub
- Milestone: Version 24
- Assignees: none
- Created: 2026-07-17 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/95

### Body



### Comments (1)

**KnightOfNight** — 2026-07-18:
Deferred (2026-07-17): revisit in the next major version that releases new zones.


## Issue #104: NPC HP must scale with level/Mk tier before any Mk 2 spawn is authored

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-17 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/104

### Body

Survey finding G6 (#89): create_live_instance sets NPC vitality = base_vitality, flat; get_npc_stats scales contest stats from npc_level but never HP. No live impact today (every spawn is Mk 1), but the first Mk 2 spawn authored will carry level-12+ contest stats with Mk 1 HP — an instant trivialization, the inverse of the pre-v20 unkillable-spiders bug.

Operator ruling (2026-07-17): unmilestoned; MUST be resolved before any Mk 2 content exists. Blocks Mk 2 spawn authoring. Related: the v22 combat wiring issue #100 will touch the same damage pipeline.


### Comments (0)

None.

## Issue #105: Elite even-level −5% hit calibration drift (rounding parity)

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-17 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/105

### Body

Survey finding G5 (#89): at even levels, banker's rounding in the NPC DEX curve and the floor-share of the player's odd stat point misalign by 1 DEX = 5% hit. All observed deviations are exactly −5%, at L4/L8 only. Calibration noise inherent to integer stats; flips no verdict alone, but compounds in multi-elite rooms. Recorded for a future calibration pass; the arch doc's "blessed targets exact at every level" claim is overstated by this amount.


### Comments (0)

None.

## Issue #117: shyland: stub tests.py shadows tests/ package — breaks whole-app test discovery

- State: open
- Author: KnightOfNight
- Labels: bug, triaged
- Milestone: Version 23
- Assignees: KnightOfNight
- Created: 2026-07-18 | Updated: 2026-07-23
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/117

### Body

**Found while implementing v21.1 Brief 1 (#116), filed under the brief's Discovery Rule — no fix applied, no milestone, no bucket label.**

**Defect:** `django/src/apps/shyland/` contains both a `tests.py` (the untouched `startapp` stub: `from django.test import TestCase` / `# Create your tests here.`) and a `tests/` package (the real suite: `test_area.py`, `test_combat_state.py`, `test_command_grammar.py`, `test_currency.py`, `test_dispatch_guard.py`, `test_output_messaging.py`, `test_room_visits.py`, `test_session_takeover.py`, `test_ui_layout.py`).

**Observed behavior:** whole-app test discovery fails:

```
$ python manage.py test apps.shyland -t /app
ImportError: 'tests' module incorrectly imported from '/app/apps/shyland/tests'. Expected '/app/apps/shyland'. Is this module globally installed?
```

(raised from `unittest/loader.py` `_find_test_path` during discovery, Python 3.12, in-container.)

**Mechanism:** with both a `tests` package and a `tests.py` module in the same parent, the package wins at import time, but unittest's file-based discovery walks the directory, sees `tests.py`, imports `apps.shyland.tests` (getting the package), compares the module's `__file__` location against the path it expected for `tests.py`, and raises the "incorrectly imported" guard.

**Impact:** `manage.py test apps.shyland` (and by extension bare `manage.py test` full-project discovery, which walks the same path) cannot run. The suite is only runnable by targeting the package explicitly: `manage.py test apps.shyland.tests -t /app` (132 tests, all passing as of this filing).

**Suspected origin:** `tests.py` is the `startapp` scaffold remnant, never removed when the `tests/` package was introduced. Likely fix (for whoever picks this up): delete `django/src/apps/shyland/tests.py`.


### Comments (0)

None.

## Issue #119: do not change border colors

- State: open
- Author: KnightOfNight
- Labels: bug
- Milestone: Version 23
- Assignees: none
- Created: 2026-07-19 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/119

### Body

Do not change the color of the border below the player pane while in combat.  It turns red.  It should not.

Border colors should not change except as styled by the zone/area/room.

### Comments (0)

None.

## Issue #125: player macro/alias system

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: none
- Created: 2026-07-20 | Updated: 2026-07-22
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

### Comments (0)

None.

## Issue #126: pluralization subsystem — natural-English plurals for aggregate output

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-20 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/126

### Body

Ruled 2026-07-20 (V22 B2 Amendment 5): aggregate transactional output ships with the count form ('Healing Draught Mk 1 ×100') as a deliberately plural-free first iteration. The upgrade is a shared pluralization subsystem callable from any output site: forward pluralization rules (inverting the resolver's _plural_variants de-pluralizer), an authored plural-name override field on ItemDefinition for irregulars, and multi-word head-noun handling ('Boots of the Marsh'). When it ships, the ×N aggregates upgrade to natural English ('You buy 100 Healing Draughts Mk 1 …'). Future version; scope deliberately excluded from v22.


### Comments (0)

None.

## Issue #127: Ranged proc damage ("between X and Y") — new weapon kind, midpoint-and-spread family

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-21 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/127

### Body

Deferred out of v22 B5 by operator ruling. v22 wires "up to N" procs (damage
= 1 to N off the power stat). A proc floor — "between 10 and 20 flame
damage" — is a second number per proc: generation changes, stat-table
changes (GDD §5), display composition, rolled-stat structure. That is a new
weapon kind and should copy the weapons midpoint-and-spread pattern when a
future itemization version picks it up. Ruling recorded on #68.



### Comments (0)

None.

## Issue #129: Authored per-item armor base — guaranteed minimum coverage under rolled resist

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-21 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/129

### Body

Future armor-set design seeded during B5's knob session: a real armor field
on ItemDefinition would let a set guarantee minimum coverage (authored base)
while rolled physical_resist provides bonus above it. Option C's derived
slot-weight table (v22) retires gracefully into this — TAV sums authored
bases instead of computed slot × Mk. Same family as the itemization
deepening in #127. Unmilestoned; a future feature version's question.


### Comments (0)

None.

## Issue #130: Secondary-stat curves vs Mk band growth — audit before Mk 2 content

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-21 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/130

### Body

Surfaced during B5's wiring rulings: secondary-stat midpoints grow as
base + factor × mk_tier (typically +0.2/band) while NPC numbers roughly
double per band — flat-value effects (lifesteal, proc factors, +N stat
bonuses) that matter at Mk 1 shrink toward irrelevance by Mk 3 if curves
stay as seeded. Wiring (v22 B5) is curve-agnostic; curves are pure seed
data under the code-is-definitive rule, so this is a retune, not a rework.
Audit and retune when Mk 2 content is designed — same era as #104, which
blocks all Mk 2 content.


### Comments (0)

None.

## Issue #133: Focus Tonic overshoots the acuity band system and announces no-op ticks at the 1.9 clamp

- State: open
- Author: KnightOfNight
- Labels: bug
- Milestone: Version 23
- Assignees: KnightOfNight
- Created: 2026-07-22 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/133

### Body

UNTRIAGED — filed with everything known so far; deeper triage to follow in
a future design pass. Two facets of one problem, observed in play
2026-07-22 and confirmed against code.

OBSERVED (operator playtest, production):

    You buy the Focus Tonic Mk 1 for 1 silver, 5 coppers.
    You use a Focus Tonic Mk 1.
    Your focus sharpens. (Acuity 1.1)
    Your focus sharpens. (Acuity 1.2)
    Your focus sharpens. (Acuity 1.4)
    Your focus sharpens. (Acuity 1.5)
    Your focus sharpens. (Acuity 1.6)
    Your focus sharpens. (Acuity 1.8)
    Your focus sharpens. (Acuity 1.9)
    Your focus sharpens. (Acuity 1.9)   <- no change
    Your focus sharpens. (Acuity 1.9)   <- no change
    Your focus sharpens. (Acuity 1.9)   <- no change

CODE FACTS (as of branch state ~ac01d37; cite-checked):

- Effect: EffectDefinition 'focus-tonic', single component
  shift_acuity_high with magnitude_base 0.1, magnitude_scaling 0.05,
  duration_base 30.0, duration_scaling 5.0
  (management/commands/seed_world.py, "--- Focus Tonic ---" block).
  At Mk 1: +0.15 per effect tick for ~35s — an attempted total shift of
  roughly +1.6.
- Application: run_tick_engine.py, shift_acuity_high branch —
  acuity_current = round(max(0.1, min(1.9, current + magnitude)), 1).
  1.9 is a hardcoded ceiling; the rounding explains the displayed skips
  (1.2 -> 1.4, 1.6 -> 1.8).
- The "Your focus sharpens. (Acuity N)" line fires on EVERY effect tick,
  including ticks where the clamp makes the change a no-op — the
  repeated identical 1.9 lines above.

FACET 1 — BALANCE/DESIGN (the substantive bug): under the v19
band-relative acuity redesign, every Origin's optimal band tops out at
1.15 except Voidtouched at 1.30 (GDD Origins table). A 15-copper
consumable that drives acuity to the 1.9 ceiling launches every Origin
far PAST its band into over-band (hyper-focus penalty) territory — the
opposite of what "Focus Tonic" advertises. The magnitude/duration tuning
reads as pre-v19 (authored when acuity was a simple more-is-better
meter) and was never re-tuned for the band system. A band-aware tonic
would nudge acuity toward/into band, not to the ceiling.

FACET 2 — DISPLAY: announcing no-op ticks at the clamp is the
no-change-message anti-pattern. Honest behavior at the ceiling is
silence or a one-time terminal line (e.g. "Your focus can sharpen no
further."). Related but separately tracked: these effect lines speak in
the muted 'system' voice — already recorded in the untouched-sends list
of the B5 Amendment 3 closeout as future ruling material.

Also noted for the eventual triage: shift_acuity_low (Fracture Wraith
territory) shares the same clamp-and-announce structure and should be
examined alongside whatever ruling fixes facet 2.

Design questions for the future pass: intended tonic magnitude/duration
under band rules; whether shifts should taper or stop at band edges;
per-Origin behavior (Voidtouched's wide band); the terminal-line wording;
whether the 1.9/0.1 hard clamps themselves are design or legacy.


### Comments (0)

None.

## Issue #134: Repair kit not wired up yet

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: none
- Created: 2026-07-22 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/134

### Body



### Comments (0)

None.

## Issue #137: Corpse decay orphans unlooted contents — ItemInstance rows leak with no location

- State: open
- Author: KnightOfNight
- Labels: bug, triaged
- Milestone: Version 23
- Assignees: KnightOfNight
- Created: 2026-07-22 | Updated: 2026-07-23
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/137

### Body

Corpse decay leaks the corpse's unlooted contents as permanently orphaned `ItemInstance` rows — items with `owner`, `current_room`, and `corpse` all NULL, invisible to every game query and accumulating forever. Found by the operator poking around the database manually; confirmed against production 2026-07-22.

**Production numbers (read-only check, 2026-07-22):** 87 of 211 total `ItemInstance` rows are orphaned. All 87 are the animal/insect material drops — 77 Insect Carapace, 10 Animal Hide. None equipped, none soulbound. `created_at` spans 2026-07-10 through 2026-07-22 — the leak is ongoing, not a one-time event.

**Mechanism:**

1. An animal/insect dies; its loot roll places a hide/carapace into the corpse.
2. Nobody loots it — these are low-value vendor trash, so players routinely walk away. (Villager gear/copper gets looted; that's why the orphans are exclusively materials.)
3. After `CORPSE_DECAY_MINUTES` the decay sweep fires: `delete_corpse` (`run_tick_engine.py:742`) does `Corpse.objects.filter(pk=pk).delete()` — the corpse row is deleted without touching its contents.
4. `ItemInstance.corpse` is `on_delete=SET_NULL` (`models.py:571`), so each contained item survives with its corpse pointer nulled — leaving it in no location at all.

The model's own location invariant (`ItemInstance.save()` raises unless exactly one of owner/current_room/corpse is set) never fires: `on_delete=SET_NULL` acts at the database level and doesn't call `save()`. Zero locations also passes the check as written — it only rejects *more than one*.

**What's clean:** the consumer's looted-empty path (`check_corpse_empty_and_delete`, `consumers.py:3619`) only deletes corpses that are already empty — no leak there. The leak is solely the decay sweep meeting unlooted contents.

**Player-facing impact:** none directly — the orphans are unreachable by inventory, ground, and corpse queries. The cost is unbounded table growth at the rate players kill-and-don't-loot, plus a standing violation of the one-location invariant that any future item-wide query (audits, economy metrics, migration backfills) will trip over.

**Fix shape (design ruling needed):**
- Delete contents in the decay path (explicitly, before/with the corpse delete), or change `ItemInstance.corpse` to `on_delete=CASCADE` — decayed loot is gone either way; the question is whether any future design ever wants corpse contents to outlive the corpse (e.g. drop-to-ground on decay instead of vanishing).
- Either way, a one-time purge of the existing 87 orphans (the filter is exact: all three location fields NULL).


### Comments (1)

**KnightOfNight** — 2026-07-23:
Design-chat ruling 2026-07-23 — all four parts confirmed by the operator. This comment is the authoritative design direction for the fix; the implementation brief will cite it.

1. Vanish on decay. Corpse contents do not outlive the corpse. Decayed loot is gone — no spill-to-ground. (Spill-to-ground remains available as a deliberate future feature; nothing in this fix forecloses it, since a spill would relocate items before corpse deletion.)
2. CASCADE. `ItemInstance.corpse` changes from `on_delete=SET_NULL` to `on_delete=CASCADE` (migration required). This makes the leak structurally impossible from any corpse-deletion path, not just the decay sweep. Rationale: corpse contents are by definition unowned, unequipped, unbound loot — unconditional destruction on corpse delete is always correct.
3. Tighten the location invariant to exactly-one. `ItemInstance.save()` currently rejects only more than one of owner/current_room/corpse being set; zero locations passes silently, which is what let this leak stay invisible. The check becomes exactly one. Implementation caveat (part of the fix, not optional): before tightening, verify that no legitimate transient zero-location state exists in any creation, transfer, loot, or drop flow — if one is found, STOP and report back to the design chat rather than working around it. The one-time purge (part 4) removes all currently-violating rows before the tightened check can encounter them.
4. Purge with post-run verification. One-time cleanup of existing orphans via a management command (pattern: `fix_zero_secondary_stats`). Filter is exact: `owner`, `current_room`, and `corpse` all NULL. The count is re-checked at run time, not assumed to be the 87 observed on 2026-07-22 — the leak is ongoing. The command must verify its own result: after the delete, it re-runs the orphan query and asserts a count of zero, reporting both the deleted count and the post-run count. The database must be provably clean at completion. This is a deploy-time data action: the implementing brief's closeout carries it in a PENDING DEPLOY-TIME ACTIONS block, and it stays an open verification item until its production execution — including the zero-count confirmation — is reported.

Sequencing note for the implementer: purge orphans → CASCADE migration → invariant tightening land together in one brief; the decay-path behavior itself needs no code change beyond the migration (the existing `Corpse.objects.filter(pk=pk).delete()` becomes correct under CASCADE).


## Issue #138: Bound zero-value items have no disposal path — starter kit junk is stuck in inventory forever

- State: open
- Author: KnightOfNight
- Labels: bug, triaged
- Milestone: Version 23
- Assignees: KnightOfNight
- Created: 2026-07-22 | Updated: 2026-07-23
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/138

### Body

A soulbound zero-value item has no disposal path — two individually correct rules collide, and every player who equips the free starter kit ends up carrying its outgrown pieces forever. Found by the operator in live play (a bound starter-kit item that could be neither sold nor dropped).

**The collision:**

- **Drop refuses bound items.** `cmd_drop` filters candidates to unbound only (`consumers.py:1166`) — soulbind's no-trading rule.
- **Sell refuses worthless items.** The vendor sell path answers `base_value=0` items with "That's not worth anything to me." (`consumers.py:1936`) — the v19 exploit-proofing on the free starter kit.
- Selling is the *designed* disposal path for bound items ("compensated disposal" — GDD §6.12: soulbound CAN be sold, instance deleted). The worthless-sell refusal closes that path for exactly the items whose whole design is `base_value=0`.

**Result:** any starter-kit piece that has ever been equipped (bound on equip, and equipping it is the point of the kit) is permanently stuck in the player's inventory — undropppable, unsellable, counting against the carry limit forever. Since the free kit is the onboarding path, essentially every character accumulates this junk as they outgrow the kit.

**Design question for the ruling:** which rule bends —

1. Vendors *accept* worthless bound items for 0 copper (disposal without compensation; the exploit-proofing holds, since selling for 0 pays nothing), or
2. Zero-value bound items become droppable/destroyable (a narrow soulbind exception), or
3. A dedicated discard/destroy verb for bound items generally, or
4. **Make the free stuff non-binding** (operator's suggestion): exempt `base_value=0` items from soulbind-on-equip entirely. Kit pieces stay Unbound for life — droppable the normal way, and the worthless-sell refusal stays untouched. No-trading pillar unthreatened: the only transfer channel is drop/pickup, and anything another player could gain is already free at Morra's shelf. Would need a one-time data fix un-binding existing bound kit pieces, since the trap has already sprung on live characters.

Options 1 and 4 are the smallest surfaces; 4 also reads best in fiction (free things carry no claim).


### Comments (1)

**KnightOfNight** — 2026-07-23:
Design-chat ruling 2026-07-23 — settled in full by the operator. This comment is the authoritative design direction for the fix; the implementation brief will cite it. Option 1 from the issue body, refined:

1. Vendors accept worthless items — uniformly. The `base_value=0` sell refusal ("That's not worth anything to me.") is removed. Vendors accept zero-value items, bound or unbound, for 0 copper; the instance is deleted per normal compensated disposal. The exploit-proofing holds by arithmetic: selling for 0 pays nothing. The binding system is untouched — no soulbind changes, no migration, no data fix (existing stuck kit pieces become disposable the moment this ships).
2. Exception: vendors never buy Artifact-rarity items, at any value. Artifact is the top rarity tier (one-of-a-kind, hand-authored); this refusal protects every artifact from disposal-by-accident — including the previously-existing hazard of a valued artifact being compensated-disposed for ⅓ price and deleted forever. Ruled intentional consequence: a bound artifact has no disposal path at all. A one-of-a-kind gift is yours, forever. If a buggy artifact ever needs removing, that is an admin action, not a game mechanic.
3. Voice and flavor:
   * Zero-value acceptance is a success — normal voice. The vendor's snarky remark replaces the payment sentence on transactions that net 0 ("taking out your trash" flavor); it draws from a proper variant pool, not a single line — per the #40 spike findings, the sell path currently has no NPC flavor at all, so this is the first vendor line site born variant-ready rather than joining the one-line-forever club.
   * On mixed bulk sells (paying items + worthless riders in one `sell all`): the normal payment sentence covers the paid total, and the snark appends as a trailing remark ("...oh, and I'll take that crap too" energy). Sanctioned fallback if the v22 aggregation plumbing makes the trailing form disproportionate: snark on all-worthless transactions only, mixed transactions silent about the riders — the implementing brief reports which form shipped.
   * The Artifact refusal is world-declined — warn voice (three-layer doctrine). Flavor direction: the refusal is about pricelessness, not worthlessness ("I couldn't put a price on that" energy). Variant pool here too.
4. Doctrine amendment (GDD §6.12 at version closeout): compensated disposal — "soulbound CAN be sold" — gains its one exception: except Artifact rarity, which no vendor will buy. Zero-value acceptance is recorded alongside: worthless items are accepted for nothing; the refusal that closed #138's trap is gone.

Not adopted, recorded for the archive: option 4 (exempting `base_value=0` from soulbind) was examined and rejected as the more intrusive change — it touched the binding system, required a data fix with deploy-time verification, opened a gift-path edge, and created a ground-litter problem (no ground-item decay sweep exists). Option 1 dissolves all four concerns. A seed-enforced `base_value ≥ 1` invariant for artifacts was likewise superseded by the vendor refusal, which protects artifacts at any authored value.


## Issue #139: Healing consumables can't track vitality growth — the draught tier needs an evolution pass

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-22 | Updated: 2026-07-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/139

### Body

The game's entire healing-consumable roster is one item, and its scaling curve structurally cannot track the bar it heals. Not a bug — the numbers work exactly as authored — this is evolution: the consumable tier was designed for the L1–3 opening and the game has outgrown it. Reviewed against seed and production data 2026-07-22.

**Current state (seed and live agree):**

- **The Healing Draught is the only vitality-restoring consumable in the game.** Instantaneous `restore_vitality`, magnitude `20 + 5×Mk` → **25 HP at Mk 1**. No heal-over-time item, no higher-tier variant. (The only other consumables are the Focus Tonic and the stub Repair Kit, #134.)
- **Vendors stock Mk 1 only, everywhere:** Essa (Fordwatch), Sona (Stairhead), Ridda (Cragfoot), VND-9, Mother Tansy — all Mk 1 @ 15cp, unlimited. All 341 live instances are Mk 1.
- **Sold counters show where the demand is:** Ridda at the delve staging point has sold 1,328; Sona 475; Essa 261; Mother Tansy 126; VND-9 1.

**The problem, quantified:** a L12 character with `vitality_max=718` gets 3.5% of their bar per draught — ~29 draughts for a full heal. Copper is irrelevant (15cp against a five-figure wallet); the real cost is action economy — one combat round per drink never converges against boss damage. At the L1–3 levels the draught was authored for, 25 HP was ~a fifth of the bar; the item didn't get worse, the player outgrew it.

**Why "stock Mk 2 draughts" isn't the fix:** magnitude scaling is linear and shallow (+5/Mk → Mk 10 heals 70) while `vitality_max` grows on `END×10 + STR×3 + level×5` into the many hundreds. The healing curve and the health curve diverge no matter how high the Mk ladder goes. The design pass needs to rule the shape — retuned `magnitude_base`/`magnitude_scaling`, percentage-of-max healing, a proper potion tier ladder, HoT variants, or some combination — and then the vendor stocking follows.

**Goes with (design together, no hard blockers):**

- #130 — secondary-stat curves vs Mk band growth: the same authored-curve-vs-player-growth disease; this draught is the starkest single example of it.
- #104 — NPC HP must scale before Mk 2 spawns: the other half of the same ledger. Healing throughput, NPC HP, and stat curves want ruling in one Mk 2 readiness pass — potion budgets are meaningless if only one side moves.
- See also #133 (v23): the Focus Tonic's clamp bug — the sibling consumable misbehaving at the top of its range; different failure, same subsystem.

**Context:** the v21 boss potion budgets (≤8/encounter, zone-final ≤12) were computed against this 25-HP draught at intended kill levels L3–L10; v22's gear wiring (#100) has since moved player power. Healing is the last leg of that balance triangle still at v18-era numbers.


### Comments (0)

None.

## Issue #141: text cleanup

- State: open
- Author: KnightOfNight
- Labels: triaged
- Milestone: Version 23
- Assignees: none
- Created: 2026-07-23 | Updated: 2026-07-23
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/141

### Body

*** You have reached level 13! Your Vitality is now 739 and your Longevity is now 568. You have 5 unspent stat points. Type 'spend' to allocate them.


should be two messages...


You have reached level 13! Your Vitality is now 739 and your Longevity is now 568.
You have X unspent stat points. Type 'spend' to allocate them.

where X is the number unspent including any from before the leveling.

the current color appears correct, but make sure it's loot-color



---

remove "  Type 'spend [<quantity>] <stat>' to allocate. (e.g. 'spend 2 str')" from stats output



### Comments (1)

**KnightOfNight** — 2026-07-23:
Code facts to scope this (research only, nothing changed):

**Level-up message — single site.** `run_tick_engine.py:546-562`, inside the kill branch of `process_combat`'s round execution: one message per level gained, category `reward`. Current text verbatim:

```python
f"*** You have reached level {character.level}! "
f"Your Vitality is now {new_vit_max} and your Longevity is now {new_lon_max}. "
f"You have {pts} unspent stat point{'s' if pts != 1 else ''}. "
f"Type 'spend' to allocate them.",
'reward', None
```

- **X already includes pre-level points.** `pts = character.unspent_stat_points` is read *after* `character.unspent_stat_points += STAT_POINTS_PER_LEVEL` (`run_tick_engine.py:548,556`), so the printed number is the accumulated total including any unspent from before the level. The split doesn't need an arithmetic change — just carry the same value into message two.
- **Color is already loot-color.** `reward` maps to `.msg-reward { color: var(--loot-color); }` (`game.html:152`), `--loot-color: #4caf7d` (`game.html:22`; `--success-color` is the alias at `:26`). The split messages only need to keep category `reward` on both.
- **Multi-level rounds exist.** The `while character.xp >= xp_for_next_level(...)` loop can fire more than once in a single combat round on a big XP gain — the split makes that 2 messages per level instead of 1. That's consistent with the bulk-messaging rule (one event = one envelope = one stamp); each of the two messages gets its own ts/seq.
- **Wording SETTLED (operator ruling 2026-07-23):** the `*** ` prefix is intentionally dropped — both split lines render without it, exactly as written in the issue body. Line two keeps the current short form `Type 'spend' to allocate them.` (not the stats pane's fuller `spend [<quantity>] <stat>` syntax). No open questions on this issue.

**Stats-output hint removal — single site.** `consumers.py:2300-2303`: the line is conditional (only rendered when `unspent_stat_points > 0`) inside the `stats` report:

```python
if character.unspent_stat_points > 0:
    lines.append(
        {'v': "  Type 'spend [<quantity>] <stat>' to allocate. (e.g. 'spend 2 str')"},
    )
```

Trivial deletion; the `Unspent stat points: N` line above it (`consumers.py:2298`) is untouched. Discoverability of the syntax survives via the help table row (`'spend [<quantity>] <stat>'`, `consumers.py:1016`) and `SPEND_USAGE` (`consumers.py:2310`).

**Test impact: none.** No test asserts on either string (grepped `tests/` for "reached level" and "to allocate"). A new test pinning the two-message form would be the only test work.


## Issue #142: Finish the acuity design: in-combat drift is unruled

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: Version 24
- Assignees: KnightOfNight
- Created: 2026-07-23 | Updated: 2026-07-23
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


### Comments (1)

**KnightOfNight** — 2026-07-23:
Split from #27, whose research-spike findings comment contains the full code-level analysis (tick phases, exclusion sites, v19-vs-current confirmation). #27 is closed as premise-corrected; this issue carries the surviving design question.


## Closed Issues — Summary Table

| # | Title | Author | Labels | Closed |
|---|---|---|---|---|
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
