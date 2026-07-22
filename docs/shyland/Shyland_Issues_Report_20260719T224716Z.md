# Shyland Issues Report

- Generated: 20260719T224716Z
- Repo: KnightOfNight/games-mvc
- Open issues: 48
- Closed issues: 66
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
| 10 | Transactional email via Postmark (password resets) | KnightOfNight |  |  | 2026-07-12 |
| 11 | Account onboarding via unusable password + reset link (no temp passwords) | KnightOfNight |  |  | 2026-07-12 |
| 12 | Two-factor authentication via TOTP (django-otp) | KnightOfNight |  |  | 2026-07-12 |
| 18 | Animal Hides Don't Stack in Inventory | KnightOfNight | bug |  | 2026-07-13 |
| 25 | Bosses do not heal when the player disengages | KnightOfNight | bug |  | 2026-07-12 |
| 26 | Boss and elite kills pay flat XP — no tier multiplier | KnightOfNight |  |  | 2026-07-12 |
| 27 | Research: passive regen ticks landing after combat engagement | KnightOfNight |  |  | 2026-07-12 |
| 29 | Block looting (and related inventory commands) during combat | KnightOfNight | B2 | Version 22 | 2026-07-19 |
| 30 | Travel network: should checkpoints (shards) also be travel senders? | KnightOfNight | B4 | Version 22 | 2026-07-18 |
| 33 | Shyland: persist detailed combat logs for balance analysis | KnightOfNight |  | Firehose Logging | 2026-07-12 |
| 37 | Universal event logging (firehose): every command, every output, every event | KnightOfNight |  | Firehose Logging | 2026-07-12 |
| 38 | Obelisk attunement: player-set home spawn at checkpoint shards | KnightOfNight | B4 | Version 22 | 2026-07-18 |
| 40 | Free repair messages repeat too often (Morra example) — research spike into other duplication cases | KnightOfNight |  |  | 2026-07-12 |
| 41 | Lock battle-zone access until a new player has visited all of The Convergence | KnightOfNight |  |  | 2026-07-18 |
| 47 | Right pane: player effects display (sent and received) | KnightOfNight |  |  | 2026-07-13 |
| 54 | consider how to simplify combat language and make it more human | KnightOfNight | B2 | Version 22 | 2026-07-19 |
| 57 | new command: home [now] | KnightOfNight | B3 | Version 22 | 2026-07-19 |
| 58 | vendor for-sale list changes | KnightOfNight | B2 | Version 22 | 2026-07-19 |
| 59 | some commands not logged in timestamped output | KnightOfNight | bug, B2 | Version 22 | 2026-07-19 |
| 61 | refuse to use a healing draught if player vitality is full | KnightOfNight | B2 | Version 22 | 2026-07-19 |
| 65 | 'use 3 heal' responds with 'You can't use everything at once.' | KnightOfNight | B2 | Version 22 | 2026-07-19 |
| 67 | tab completion doesn't work for 'equip' | KnightOfNight | B2 | Version 22 | 2026-07-19 |
| 70 | Feature: Longevity has no drain — the slow-burn design needs its first consuming mechanic | KnightOfNight |  |  | 2026-07-15 |
| 75 | repair all should retry, not need multiple manual tries | KnightOfNight | B2 | Version 22 | 2026-07-19 |
| 80 | Design: item identification visibility — knowledge by holding | KnightOfNight |  |  | 2026-07-16 |
| 88 | new command: last | KnightOfNight | stub, B3 | Version 22 | 2026-07-19 |
| 95 | the ring needs an area | KnightOfNight | stub |  | 2026-07-18 |
| 96 | examine doesn't autocomplete on NPC name | KnightOfNight | stub, B2 | Version 22 | 2026-07-19 |
| 98 | command 'who' needs color output | KnightOfNight | stub, B2 | Version 22 | 2026-07-19 |
| 100 | Wire equipped item stats into combat (armor mitigation, stat bonuses) | KnightOfNight | B5 | Version 22 | 2026-07-18 |
| 104 | NPC HP must scale with level/Mk tier before any Mk 2 spawn is authored | KnightOfNight |  |  | 2026-07-17 |
| 105 | Elite even-level −5% hit calibration drift (rounding parity) | KnightOfNight |  |  | 2026-07-17 |
| 109 | Design ruling: mid-combat stat spend refills bars to new max (bankable free heal) | KnightOfNight | B5 | Version 22 | 2026-07-19 |
| 110 | apply_stat_effect races the engine's effect-expiry reversal (cached-object RMW on stat fields) | KnightOfNight | B5 | Version 22 | 2026-07-18 |
| 111 | command revamp | KnightOfNight | B2 | Version 22 | 2026-07-19 |
| 112 | new command: sudo | KnightOfNight | B3 | Version 22 | 2026-07-19 |
| 113 | new command: cancel | KnightOfNight | B3 | Version 22 | 2026-07-19 |
| 117 | shyland: stub tests.py shadows tests/ package — breaks whole-app test discovery | KnightOfNight | bug |  | 2026-07-18 |
| 119 | do not change border colors | KnightOfNight |  |  | 2026-07-19 |
| 120 | add version number of running game to 'help' output using key/value display type 1 | KnightOfNight |  |  | 2026-07-19 |
| 121 | client renders error category as amber, ignoring --error | KnightOfNight | bug, B2 | Version 22 | 2026-07-19 |
| 122 | invariant: players and NPCs may never share a name | KnightOfNight | B2 | Version 22 | 2026-07-19 |

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
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-12
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
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-12
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
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-12
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
- Milestone: none
- Assignees: none
- Created: 2026-07-11 | Updated: 2026-07-13
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
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-12
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
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-12
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/26

### Body

XP awards derive from NPC level only. In the v19 Matron fight: Silk Matron (level-3 boss, 120 vitality, minion adds) paid 30 XP — identical to a level-3 cave beetle. Her brood paid 20, same as any level-2 normal. Risk/reward is flat across the normal/elite/boss tiers even though difficulty now scales sharply by tier (Brief 7's contest offsets).

Proposal direction: a tier-based XP multiplier. **How much more bosses and elites should pay needs discussion and planning — the amount is explicitly NOT decided in this issue.**


### Comments (0)

None.

## Issue #27: Research: passive regen ticks landing after combat engagement

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-12
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/27

### Body

Research spike. In a v19 combat log, two passive regen ticks ("You feel your body recover. (+25 Vitality)") landed *after* NPCs had engaged the player (post-aggro "moves to attack!" lines, pre-first-blows). Determine whether the tick engine's regen pass is intended to exclude in-combat characters, and whether it actually checks combat-session membership (vs. a timing race between the aggro engagement and the regen pass within the same tick).

Outcome decides classification: if regen is meant to be out-of-combat only, this is a bug (add the `bug` label then); if in-combat regen is intended, document it as design and close.


### Comments (0)

None.

## Issue #29: Block looting (and related inventory commands) during combat

- State: open
- Author: KnightOfNight
- Labels: B2
- Milestone: Version 22
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-19
- Blocked by: none
- Blocks: #111
- URL: https://github.com/KnightOfNight/games-mvc/issues/29

### Body

Currently `loot` works mid-combat: a player can secure spoils from earlier kills while a fight is still undecided, and mid-fight looting also sidesteps the risk that death (or corpse decay) costs you the unclaimed loot. Discussed and deferred in the v19 design pass.

Ruled direction (starting point, not final): `loot` refuses during combat with an in-fiction message, matching the pattern `quit` will use. Needs discussion and planning before implementation:

- Which sibling commands join it for one consistent combat-blocked list — `pickup` has the identical exploit; `equip`/`unequip` mid-fight (armor-swapping per enemy) is arguably a bigger one. `use` stays allowed by design (potions in combat are the point).
- Corpse-decay interaction: if loot must wait for combat's end, long multi-NPC fights must not outlive the first corpse's despawn timer — verify the timer comfortably exceeds long fights, or freeze decay while the killer's session is active.
- Classic-MUD alternative recorded for the discussion: allow looting but at an action cost (looting consumes your combat round). Requires an action economy that doesn't exist yet; noted as future flavor, not the recommended path.


### Comments (3)

**KnightOfNight** — 2026-07-12:
#23 (cardinal movement doesn't end combat) belongs on this issue's combat-blocked command list — its proposed solution is an entry here. Rule them together.

**KnightOfNight** — 2026-07-13:
V20 planning ruling: deferred — not in Version 20. This is a gameplay-rules change, and v20 scope is UI/UX fixes and improvements only.

#23 has been pulled out of this issue's combined design pass and ships in v20 as a bug fix. The remaining combat-blocked command list (loot, pickup, equip/unequip) stays here for a future version's design pass.

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

Ruled via the state-gating matrix: loot (with drop, pickup, equip, unequip, commerce, repair, home, travel, movement) is refused in combat, warn-color. Full matrix in DD §5.


## Issue #30: Travel network: should checkpoints (shards) also be travel senders?

- State: open
- Author: KnightOfNight
- Labels: B4
- Milestone: Version 22
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-18
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


### Comments (1)

**KnightOfNight** — 2026-07-12:
Companion issue filed as promised: #38 (obelisk attunement / player-set home spawn).

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
- Labels: B4
- Milestone: Version 22
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-18
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


### Comments (0)

None.

## Issue #40: Free repair messages repeat too often (Morra example) — research spike into other duplication cases

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-12
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


### Comments (0)

None.

## Issue #41: Lock battle-zone access until a new player has visited all of The Convergence

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-18
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
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-13 | Updated: 2026-07-13
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

## Issue #54: consider how to simplify combat language and make it more human

- State: open
- Author: KnightOfNight
- Labels: B2
- Milestone: Version 22
- Assignees: none
- Created: 2026-07-14 | Updated: 2026-07-19
- Blocked by: none
- Blocks: #111
- URL: https://github.com/KnightOfNight/games-mvc/issues/54

### Body

Example: when fighting multiple monsters, instead of "You hit the first giant cave spider for 19 damage. The first giant cave spider is dead.", what about "You hit a giant cave spider for 19 damage. One of giant cave spiders is dead."

The engine only needs to track quantity of monsters and pluralization.

### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

The shipped combat transcript is ratified as the language spec — the v21 work (#64 ordinals, authored attack variety, wound ladder) answered this ticket's complaint. Remaining deltas are color only: crit-in #F08A50 bold added; miss re-colored to muted-color. Implementation rides the B2 output brief.


## Issue #57: new command: home [now]

- State: open
- Author: KnightOfNight
- Labels: B3
- Milestone: Version 22
- Assignees: none
- Created: 2026-07-14 | Updated: 2026-07-19
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/57

### Body

sends the player home in 15 seconds.  player can type cancel to stop the request.

### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

The chart rules `home` takes no arguments (footnote 2). The "home now" instant variant is DEAD — superseded; home is always the delayed action with cancel as the escape. State matrix: refused in combat and while dying. Remaining design (delay mechanics, arrival) belongs to the B3 pass.


## Issue #58: vendor for-sale list changes

- State: open
- Author: KnightOfNight
- Labels: B2
- Milestone: Version 22
- Assignees: none
- Created: 2026-07-15 | Updated: 2026-07-19
- Blocked by: none
- Blocks: #111
- URL: https://github.com/KnightOfNight/games-mvc/issues/58

### Body

display rarity
display free items separately
sort groups of items (free, not-free, other groups later) by name


### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

Fully ruled: list renders as the standard table (Slot/Name/Quantity/Details/Price), rarity words rarity-colored in Details, two groups free-first (Price shows muted "free"), alphabetical within groups. DD §9.


## Issue #59: some commands not logged in timestamped output

- State: open
- Author: KnightOfNight
- Labels: bug, B2
- Milestone: Version 22
- Assignees: none
- Created: 2026-07-15 | Updated: 2026-07-19
- Blocked by: none
- Blocks: #111
- URL: https://github.com/KnightOfNight/games-mvc/issues/59

### Body

buy
sell

it might be all commands right now


### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

Answered by doctrine: every command is timestamped and firehosed as an event; the settings standards fix the specific inconsistencies. Implementation rides the revamp.


## Issue #61: refuse to use a healing draught if player vitality is full

- State: open
- Author: KnightOfNight
- Labels: B2
- Milestone: Version 22
- Assignees: none
- Created: 2026-07-15 | Updated: 2026-07-19
- Blocked by: none
- Blocks: #111
- URL: https://github.com/KnightOfNight/games-mvc/issues/61

### Body



### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

Ruled and generalized: any heal attempted at full vitality fails (warn-color); multi-use sequences stop at full with the loot-color line "You have been restored to full health."; use while dying is allowed (self-rescue is deliberate design). DD §7.


## Issue #65: 'use 3 heal' responds with 'You can't use everything at once.'

- State: open
- Author: KnightOfNight
- Labels: B2
- Milestone: Version 22
- Assignees: none
- Created: 2026-07-15 | Updated: 2026-07-19
- Blocked by: none
- Blocks: #111
- URL: https://github.com/KnightOfNight/games-mvc/issues/65

### Body



### Comments (2)

**KnightOfNight** — 2026-07-15:
V21 triage ruling (2026-07-15): deferred to Version 21 per the version cadence rule (verb-noun handling refinement). Design note for the v21 pass — the message is answering a question the player didn't ask: 'You can't use everything at once' is the 'use all' rejection firing for 'use 3', meaning the quantifier rejection path doesn't distinguish all from N. Two questions to rule: (1) should 'use N' simply WORK (sequential consumption is legitimate QoL; instant effects apply fine back-to-back); (2) if any quantifier stays rejected for use, the refusal must name what was actually asked.


**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

The chart rules `use [<quantity>] <item>` (numeric only) — `use 3 healing draught` is legal; the current refusal dies. Sequence semantics per DD §7.


## Issue #67: tab completion doesn't work for 'equip'

- State: open
- Author: KnightOfNight
- Labels: B2
- Milestone: Version 22
- Assignees: none
- Created: 2026-07-15 | Updated: 2026-07-19
- Blocked by: none
- Blocks: #111
- URL: https://github.com/KnightOfNight/games-mvc/issues/67

### Body



### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

Covered by the completion rule: tab completes exactly each command's pool, per position — equip completes inventory item names. DD §8.


## Issue #70: Feature: Longevity has no drain — the slow-burn design needs its first consuming mechanic

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-15 | Updated: 2026-07-15
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

## Issue #75: repair all should retry, not need multiple manual tries

- State: open
- Author: KnightOfNight
- Labels: B2
- Milestone: Version 22
- Assignees: none
- Created: 2026-07-15 | Updated: 2026-07-19
- Blocked by: none
- Blocks: #111
- URL: https://github.com/KnightOfNight/games-mvc/issues/75

### Body

[16:49:20.74] > repair all
[16:49:20.88] Leather Gloves Mk 1 is restored to full condition. (1 copper)
[16:49:20.91] Battle Axe Mk 1 is restored to full condition. (9 coppers)
[16:49:20.93] The mending on Leather Vest Mk 1 didn't take. (2 coppers)
[16:49:20.95] Leather Cap Mk 1 is restored to full condition. (1 copper)
[16:49:20.97] Leather Boots Mk 1 is restored to full condition. (1 copper)
[16:49:20.99] Leather Leggings Mk 1 is restored to full condition. (2 coppers)
[16:49:21.02] Leather Belt Mk 1 is restored to full condition. (1 copper)
[16:49:21.02] Repaired 6 items, 1 attempt failed, 1 silver, 7 coppers spent.
[16:49:26.76] > repair all
[16:49:26.89] Leather Vest Mk 1 is restored to full condition. (2 coppers)
[16:49:26.89] Repaired 1 item, 0 attempts failed, 2 coppers spent.

### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

Ruled: `repair all` loops until everything is repaired, funds run out, or 5 attempts; each mend line prints as it lands. DD §7.


## Issue #80: Design: item identification visibility — knowledge by holding

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-16 | Updated: 2026-07-16
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

## Issue #88: new command: last

- State: open
- Author: KnightOfNight
- Labels: stub, B3
- Milestone: Version 22
- Assignees: none
- Created: 2026-07-16 | Updated: 2026-07-19
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/88

### Body

last - reports on the history of connected users

only available to admins

will ship along with 'sudo'


### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

Reclassified **information** (not action). No arguments. Admin-gated with stealth (footnote 18; Django Group, live check). Output: Kind 3 table — Character / Status / Time Last Seen; Character as the composite status-page line; Status Online/Offline for now; most recent first. DD §9, §12.


## Issue #95: the ring needs an area

- State: open
- Author: KnightOfNight
- Labels: stub
- Milestone: none
- Assignees: none
- Created: 2026-07-17 | Updated: 2026-07-18
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/95

### Body



### Comments (1)

**KnightOfNight** — 2026-07-18:
Deferred (2026-07-17): revisit in the next major version that releases new zones.


## Issue #96: examine doesn't autocomplete on NPC name

- State: open
- Author: KnightOfNight
- Labels: stub, B2
- Milestone: Version 22
- Assignees: none
- Created: 2026-07-17 | Updated: 2026-07-19
- Blocked by: none
- Blocks: #111
- URL: https://github.com/KnightOfNight/games-mvc/issues/96

### Body



### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

Covered by the completion rule: examine completes its full pool union — including NPCs here. DD §8.


## Issue #98: command 'who' needs color output

- State: open
- Author: KnightOfNight
- Labels: stub, B2
- Milestone: Version 22
- Assignees: none
- Created: 2026-07-17 | Updated: 2026-07-19
- Blocked by: none
- Blocks: #111
- URL: https://github.com/KnightOfNight/games-mvc/issues/98

### Body



### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

Ruled: who becomes one line — `Players online (3): name, name, name` — key-color label, value-color names. DD §9.


## Issue #100: Wire equipped item stats into combat (armor mitigation, stat bonuses)

- State: open
- Author: KnightOfNight
- Labels: B5
- Milestone: Version 22
- Assignees: KnightOfNight
- Created: 2026-07-17 | Updated: 2026-07-18
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/100

### Body

Survey finding G7 (#89, docs/shyland/Shyland_V21_Kill_Feasibility_Survey.md): no rolled item stat is ever applied to combat. Player defense is raw stat_dex; NPC damage takes no mitigation input; nothing applies rolled_primary_stats/rolled_secondary_stats to a character's combat stats. Five of eight seeded boss-loot groups (armor, accessories) are combat-inert.

Operator ruling (2026-07-17): wiring equipment into combat is a Version 22 feature with its own design pass — how stat bonuses apply, whether armor mitigates, and how gear interacts with the d20 contest window (survey G3: gear that grants DEX is the natural lever for buying contest points).

Scope includes ruling the proc-stat semantics deferred from #68 (lifesteal and kin currently roll on an inert system).


### Comments (0)

None.

## Issue #104: NPC HP must scale with level/Mk tier before any Mk 2 spawn is authored

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-17 | Updated: 2026-07-17
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
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-17 | Updated: 2026-07-17
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/105

### Body

Survey finding G5 (#89): at even levels, banker's rounding in the NPC DEX curve and the floor-share of the player's odd stat point misalign by 1 DEX = 5% hit. All observed deviations are exactly −5%, at L4/L8 only. Calibration noise inherent to integer stats; flips no verdict alone, but compounds in multi-elite rooms. Recorded for a future calibration pass; the arch doc's "blessed targets exact at every level" claim is overstated by this amount.


### Comments (0)

None.

## Issue #109: Design ruling: mid-combat stat spend refills bars to new max (bankable free heal)

- State: open
- Author: KnightOfNight
- Labels: B5
- Milestone: Version 22
- Assignees: KnightOfNight
- Created: 2026-07-17 | Updated: 2026-07-19
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/109

### Body

Surfaced by the V21 Brief 3 audit sweep (#52's mandated audit; closeout `docs/shyland/Shyland_V21_Brief_3_Closeout_Report.txt`, call site 4).

`cmd_spend` → `combat_utils.recalculate_bars` performs an absolute set: spending a point in END/STR/WIS recomputes bar maxima and refills both bars to the new max. This is the documented level-up-refill family, not a race — but unlike level-ups, stat points are **bankable on demand**: a player who saves points carries free full heals into any fight (take damage, `spend 1 end`, bars full). Repeatable until points run out.

Operator disposition (2026-07-17): design ruling required, not a v21 stopper — the behavior predates v21, is self-limiting, and belongs to the same "what refills when" design space as future content. Milestoned Version 22 for the ruling; possible outcomes include spend-refill only out of combat, refill deltas instead of full set, or keeping it as a deliberate mechanic.


### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

Confirmed in the state matrix: spend allowed in combat; the bar refill stands as the bankable free heal, priced-in design; the refill line renders loot-color. DD §5, §6.


## Issue #110: apply_stat_effect races the engine's effect-expiry reversal (cached-object RMW on stat fields)

- State: open
- Author: KnightOfNight
- Labels: B5
- Milestone: Version 22
- Assignees: KnightOfNight
- Created: 2026-07-17 | Updated: 2026-07-18
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/110

### Body

Surfaced by the V21 Brief 3 audit sweep (#52's mandated audit; closeout `docs/shyland/Shyland_V21_Brief_3_Closeout_Report.txt`, call site 6 — noted out-of-mandate there, filed here).

`effect_utils.apply_stat_effect` performs a cached-object read-modify-write on `stat_*` fields; the tick engine's effect-expiry reversal writes the same fields. This is the #52 lost-update disease on non-bar fields: an expiry landing between the consumer's read and write is silently overwritten (or a fresh buff erased by an expiry computed from stale values). Latent today (stat effects are rare and short), but structurally identical to the bug #52 fixed.

Operator disposition (2026-07-17): unmilestoned. Should ride whichever version next touches the effect system — most plausibly #100's v22 gear/combat wiring, which lives in the same code. The fix pattern is established: atomic F() arithmetic per #52's Option A, or effect application moved into the engine's own write path. Reference: the consumer-never-RMWs invariant recorded in Architecture v21 covers bar fields; this issue is the case for extending it to every engine-shared field.


### Comments (0)

None.

## Issue #111: command revamp

- State: open
- Author: KnightOfNight
- Labels: B2
- Milestone: Version 22
- Assignees: KnightOfNight
- Created: 2026-07-17 | Updated: 2026-07-19
- Blocked by: #29, #54, #58, #59, #61, #65, #67, #75, #76, #93, #96, #98
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/111

### Body

A large design session: review every single command and its output, and standardize everything.

Scope of the standardization pass:

- **Look and feel** — output formatting, colorization, key/value report form adoption, message phrasing and tone, across every command.
- **Code routing** — one consistent path through the dispatch and output machinery for every command's output.
- **Timestamps** — envelope category assignments (stamped events vs. unstamped reports) made consistent everywhere.
- **Argument behavior** — bare-form query semantics, bad-argument responses, filters, and completion made uniform.

Every command gets reviewed one by one against the standard; nothing is grandfathered.

The dependency-linked issues attached to this one are folded into the session. Some of them may be superseded or made redundant by the revamp's rulings — they are kept open and linked for tracking either way.


### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

The complete command specification exists — chart, footnotes, palette, three-layer response doctrine (error/warn/success), firehose+echo doctrine, state-gating matrix, partial-fulfillment doctrine, resolution pools with the player/NPC name invariant, success sentence standards, information-output kinds, settings standards, chart-derived help, admin gating, combat voice ratification. The DD is the conformance spec the revamp implements. Notable rulings: spend argument order flips to `spend <quantity> <stat>`; bare `sell all` blocked; drop excludes bound items and loses "all"; buy loses "all"; targetless attack removed (aggro auto-engagement made it a fossil); N.noun survives input-only; vendor stock joins examine's pool; `.msg-error` amber defect found (all error call sites re-tag under the doctrine); new commands echo (settings) and the four B3 arrivals are charted.


## Issue #112: new command: sudo

- State: open
- Author: KnightOfNight
- Labels: B3
- Milestone: Version 22
- Assignees: KnightOfNight
- Created: 2026-07-18 | Updated: 2026-07-19
- Blocked by: #37
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/112

### Body

`sudo` — a new command backed by a new Django permission for this game.

- A new permission grants a player super-user privileges in the game.
- A player holding the permission can type `sudo <anything>`.
- The game itself does not respond to `sudo` at all. An AI monitoring the firehose (#37) responds.
- The AI monitor comes later — this issue depends on the firehose.

Already referenced by #88 (`last` will ship alongside `sudo`).


### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

Chart: footnote 9 (any arguments accepted) + footnote 18 (admin stealth gating — Django Group, live per-attempt check; non-members get unknown-command; hidden from help and completion). The game never responds to sudo by design; arguments pass to the firehose for the watcher. DD §12.


## Issue #113: new command: cancel

- State: open
- Author: KnightOfNight
- Labels: B3
- Milestone: Version 22
- Assignees: KnightOfNight
- Created: 2026-07-18 | Updated: 2026-07-19
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/113

### Body

`cancel` — cancels an effect in progress.

Example: `home` (#57) starts a 15-second delayed teleport; typing `cancel` during the wait stops it. (`home now` skips the wait entirely, so there is nothing to cancel.)

`cancel` is the general verb for stopping any in-progress delayed effect, with `home` as its first customer.


### Comments (1)

**KnightOfNight** — 2026-07-19:
Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.

Chart: `cancel [<command>]` (footnote 12) — optional argument matching a running command; today's pool has at most one member. Allowed in ALL states including combat and dying (the escape hatch is never locked). Success line named per action: "You stop heading home."


## Issue #117: shyland: stub tests.py shadows tests/ package — breaks whole-app test discovery

- State: open
- Author: KnightOfNight
- Labels: bug
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-18 | Updated: 2026-07-18
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
- Labels: none
- Milestone: none
- Assignees: none
- Created: 2026-07-19 | Updated: 2026-07-19
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/119

### Body

Do not change the color of the border below the player pane while in combat.  It turns red.  It should not.

Border colors should not change except as styled by the zone/area/room.

### Comments (0)

None.

## Issue #120: add version number of running game to 'help' output using key/value display type 1

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: none
- Created: 2026-07-19 | Updated: 2026-07-19
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/120

### Body



### Comments (0)

None.

## Issue #121: client renders error category as amber, ignoring --error

- State: open
- Author: KnightOfNight
- Labels: bug, B2
- Milestone: Version 22
- Assignees: KnightOfNight
- Created: 2026-07-19 | Updated: 2026-07-19
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/121

### Body

`.msg-error` is hard-coded `#C08A3E` (commented "amber") and does not use `--error: #cc4444`. Every error line in the game renders amber. The fix is not a recolor: under the three-layer doctrine (DD §3, docs/shyland/Shyland_V22_B2_Command_Spec_DD.md), every error-emitting call site must be re-tagged as CLI error (error-color) or world-declined (warn-color #E8D44D). Found during the 2026-07-19 design session playtest.


### Comments (0)

None.

## Issue #122: invariant: players and NPCs may never share a name

- State: open
- Author: KnightOfNight
- Labels: B2
- Milestone: Version 22
- Assignees: KnightOfNight
- Created: 2026-07-19 | Updated: 2026-07-19
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/122

### Body

Ruled 2026-07-19 (DD §8): a player character and an NPC may never share a name, ever. Two enforcement edges: (1) character creation rejects any name matching an NPC definition name, case-insensitive, alongside the existing uniqueness and profanity checks; (2) seed-verify gains a check that no NPC definition name collides with any existing character name. Motivated by attack/examine ambiguity resolution — cross-segment ambiguity dies by fiat.


### Comments (0)

None.

## Closed Issues — Summary Table

| # | Title | Author | Labels | Closed |
|---|---|---|---|---|
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
