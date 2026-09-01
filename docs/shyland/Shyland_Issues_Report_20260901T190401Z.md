# Shyland Issues Report

- Generated: 20260901T190401Z
- Repo: KnightOfNight/games-mvc
- Open issues: 41
- Closed issues: 220
- Dependency data: available

## Open Issues — Summary Table

| # | Title | Author | Labels | Milestone | Updated |
|---|---|---|---|---|---|
| 4 | Build Zone: Ashenveil Cathedral (Z02) | KnightOfNight | Z02 |  | 2026-08-22 |
| 5 | Build Zone: The Neon Sprawl (Z03) | KnightOfNight | Z03 |  | 2026-07-30 |
| 6 | Build Zone: The Blasted Flats (Z04) | KnightOfNight | Z04 |  | 2026-07-30 |
| 7 | Build Zone: The Iron Deeps (Z06) | KnightOfNight | Z06 |  | 2026-07-30 |
| 8 | Build Zone: The Pale Shore (Z07) | KnightOfNight | Z07 |  | 2026-07-30 |
| 9 | Build Zone: The Wastelands (Z08) | KnightOfNight | Z08 |  | 2026-07-30 |
| 10 | Transactional email via Postmark (password resets) | KnightOfNight | authentication |  | 2026-07-30 |
| 11 | Account onboarding via unusable password + reset link (no temp passwords) | KnightOfNight | authentication |  | 2026-07-30 |
| 12 | Two-factor authentication via TOTP (django-otp) | KnightOfNight | authentication |  | 2026-07-30 |
| 47 | Right pane: player effects display (sent and received) | KnightOfNight |  |  | 2026-07-30 |
| 70 | Feature: Longevity has no drain — the slow-burn design needs its first consuming mechanic | KnightOfNight |  |  | 2026-07-30 |
| 126 | pluralization subsystem — natural-English plurals for aggregate output | KnightOfNight |  |  | 2026-07-30 |
| 145 | hot_acuity / dot_acuity announce no-op effect ticks (doctrine from #133) | KnightOfNight |  |  | 2026-07-24 |
| 148 | Loot-take sentence embeds the listing composition — flag block and double space don't match other item output | KnightOfNight | output, commands |  | 2026-08-15 |
| 161 | Use shortfall warn lacks context — name the item and the now-empty inventory | KnightOfNight | output, commands |  | 2026-08-15 |
| 163 | Map: more information — starting with percentage of the current zone explored | KnightOfNight | commands |  | 2026-08-15 |
| 174 | Admin command: uptime (container uptimes, disk free, reclaimable space) | KnightOfNight | commands |  | 2026-08-15 |
| 179 | New-zone design rules (collecting issue) | KnightOfNight |  |  | 2026-08-23 |
| 182 | Map changes/fixes (collecting issue) | KnightOfNight |  |  | 2026-08-01 |
| 191 | MC consumer: command-pattern watcher — mine player behavior for the next heal/loot-shaped improvements | KnightOfNight | monitoring-and-command |  | 2026-09-01 |
| 209 | Research spike: player info on stat points — discoverability, what each stat controls, spend preview/simulator, and respec | KnightOfNight | commands |  | 2026-08-15 |
| 214 | Move dev to AWS: prod-mirror instance (different FQDN, shared wildcard cert) + automate/document the prod setup | KnightOfNight | deployments |  | 2026-08-08 |
| 217 | 'last' should show current location for players who are currently logged in | KnightOfNight | output, commands |  | 2026-08-15 |
| 219 | In-game release notes: new 'readme' command — format and content TBD | KnightOfNight | commands |  | 2026-08-30 |
| 220 | Multiplayer combat vs a shared NPC is unmodeled — parallel 1v1 sessions: double NPC damage output, no aggro semantics, kill attribution undefined | KnightOfNight |  |  | 2026-08-08 |
| 223 | Production uptime monitoring + alerting — detect broken/unreachable including DNS; AWS-native vs AI-agent mechanism TBD | KnightOfNight | deployments |  | 2026-08-09 |
| 236 | Admin 'wall' command: broadcast to all connected players (pending-restart warning) | KnightOfNight | commands |  | 2026-08-15 |
| 243 | Deleted-while-connected: commands that never fresh-fetch (e.g. inv) render empty/stale output instead of routing to the creator | KnightOfNight | commands |  | 2026-08-15 |
| 259 | Sirius: AI felis sapiens companion — callable, may help, gives only when he wants to (unfinished design) | KnightOfNight | monitoring-and-command, V25 |  | 2026-08-23 |
| 261 | The Command half of MC: how does a non-human actor take action in the world? (scoping) | KnightOfNight | monitoring-and-command, V25 |  | 2026-08-22 |
| 263 | Player pets / companions: a general system for player-owned NPC allies (may be AI-driven; Machinist depends on it) | KnightOfNight | monitoring-and-command, V25 |  | 2026-08-18 |
| 265 | AI chat responders for NPCs: agents read the MC stream and answer as NPCs in the world (speech-only actuation) | KnightOfNight | monitoring-and-command, V25 |  | 2026-08-18 |
| 268 | MC agent runtime & operations: hosting, supervision, credentials, cost governance for the AI actor fleet | KnightOfNight | monitoring-and-command, V25 |  | 2026-08-27 |
| 282 | Agent door: 'answer' delivery gate must be per-agent context, not verb-global — sudo answers admins only, Sirius answers anyone | KnightOfNight | monitoring-and-command |  | 2026-08-27 |
| 283 | NPC first-contact greetings broadcast room-wide in second person — bystanders read the 'you' as addressed to them | KnightOfNight |  |  | 2026-08-22 |
| 297 | Curse system live loop is unbuilt: apply active_curse on equip, unequip handling, seedable curse effects, acquisition + identification paths (needed for new zones; rule with #80) | KnightOfNight |  |  | 2026-08-26 |
| 315 | Door durability edit can silently break a non-wearing item: 0 sets is_broken (combat-honored) with no display cue and no in-game repair path | KnightOfNight |  |  | 2026-08-30 |
| 316 | plan on adjusting big numbers to use shorthand | KnightOfNight | output |  | 2026-08-30 |
| 317 | Sudo bot: file_issue cannot apply labels — extend the filing vocabulary to carry operator-named labels | KnightOfNight | triaged, monitoring-and-command | Version 25.14 | 2026-09-01 |
| 320 | Agent door / sudo bot has no currency actions — add full copper management (grant and deduct) | KnightOfNight | triaged, monitoring-and-command | Version 25.14 | 2026-09-01 |
| 321 | Bulk buy/sell at admin-scale quantities takes minutes with zero output — sell is O(n) transactions, buy O(qty) serial INSERTs | KnightOfNight |  |  | 2026-09-01 |

## Open Issues — Full Detail

## Issue #4: Build Zone: Ashenveil Cathedral (Z02)

- State: open
- Author: KnightOfNight
- Labels: Z02
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-08-22
- Blocked by: #179
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/4

### Body

Build out Z02 — Ashenveil Cathedral, a dark gothic horror zone for Intermediate-level characters.

Zone described in docs/shyland/Shyland_GDD_v18.md, Section 2.2 (Zone Architecture). Wire the sealed gate on the Infinity City ring street (~2:00 position) once the zone is built.

This is one of the remaining battle zones tracked for post-Verdant-Reach content expansion.

### Comments (1)

**KnightOfNight** — 2026-08-22:
Design note from the new-zones planning session (2026-08-22): candidate underground content for the Cathedral — **crypts and basements**. VG's "caves" vocabulary won't apply here; whatever sub-map content Z02 carries would wear words like these. (Per the emerging zone standards on #179, underground/sub-map content is the zone designer's call — no required count, no rule of three about it.)


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
- Labels: output, commands
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-25 | Updated: 2026-08-15
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
- Labels: output, commands
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-29 | Updated: 2026-08-15
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
- Labels: commands
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-29 | Updated: 2026-08-15
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
- Labels: commands
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-30 | Updated: 2026-08-15
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
- Created: 2026-07-30 | Updated: 2026-08-23
- Blocked by: none
- Blocks: #4, #5, #6, #7, #8, #9
- URL: https://github.com/KnightOfNight/games-mvc/issues/179

### Body

Collecting issue for new-zone design rules. Rules accumulate here (body + comments) until a design session rules them and ships them as GDD text — realistically the Zone Design Standards passage in V25.0's coherent pass, landing with the release that first builds a zone under them. This issue closes when that ships.

Rules are **construction standards for new zones** — shipped zones are documented as-is, not retroactively in violation (precedent: the v18 identification trapdoor note). Whether an existing zone gets remediated to a standard is its own someday-ticket.

---

## Rule 1 — Zone topology must branch (operator, 2026-07-30)

Stated by counterexample: **The Verdant Reach is a straight line, not at all maze-shaped.** New zones don't get to be. Branching, loops, decision points — topology that rewards the map instead of merely scrolling it. The map machinery (MapFrags, fog-of-war, boundary flags) was built for geometry Z01 never gave it.


### Comments (5)

**KnightOfNight** — 2026-08-22:
## Rule 2 — The Rule of Three (operator, 2026-08-22)

**Every normal zone carries exactly 3 shards (checkpoints), and then 1 sphere (its zone-end obelisk).**

- **Exactly 3 — not a floor, not a budget.** A fixed cadence players learn and rely on in every zone.
- **"And then" is positional: the sphere always sits at the end** of the zone's progression. This extends the shipped Obelisk Pattern (GDD §2.10, "Every Zone Ends This Way") — reaching the obelisk *is* finishing the zone; the Rule of Three adds the cadence in front of it.
- **One sphere total per zone, ever.**
- **Shards are always important bookmarks within the zone** — placement marks the zone's significant thresholds, never filler. Z01 set them at its act seams; future zones choose their own bookmarks.
- **Scope: all normal zones.** The Wastelands (Z08) is not a normal zone and is exempt — part of its lore may be that it has no end sphere, and players discover new shards as they go deeper; it will likely carry more than 3 as a result.

Z01 conforms: Fordwatch, Stairhead, Cragfoot, then the Verdant Crown. (Z05 The Convergence is the shipped hub, documented as-is per this issue's preamble.)


**KnightOfNight** — 2026-08-22:
Consolidated rulings from the 2026-08-22 new-zones planning session (operator-ruled in-conversation; continues Rule 2 above). Also from this session: the rule-of-three research sweep of the Verdant Reach (dispositions folded in below), the crypts-and-basements note on #4, and erratum #286.

## Rule 3 — Chapters (the word, and the structure)

The shard-marked parts of a zone are **chapters**. 3 shards → **exactly 3 chapters** per normal zone; each chapter is a **shard-centric bucket of related content**, and the last ends at the sphere.

- A chapter is *not* an Area. It may span multiple Areas (several buildings, caves, or districts in one chapter is fine). Area count stays free — the Rule of Three binds chapters, not Areas. (The Convergence has many Areas and no chapters at all.)
- Structure only: the rule dictates nothing about content. Lore-wise a zone's chapters may be as different or as similar as the design wants.
- **Zone → Area → Room stays three-deep as law** — itself a rule of three, amendable only if some future need proves out a fourth level (ruled highly unlikely).

## Rule 4 — Chapter sizes: free shape, 20% floor

- No required size shape. VG's 30/20/50 split was the training zone's own design, not a template — the first chapter need not be the smallest, nor the last the largest.
- **No chapter may be smaller than 20% of the zone.** Denominator: **total zone room count — surface, buildings, caves, all sub-map content included.** (3 × 20% = 60% committed, so a chapter ranges 20–60%.)
- New zones will generally be larger overall than VG's 150 rooms.

## Rule 5 — Difficulty progresses; room share drives band share

- Every zone declares a **starting level and an ending level**, and difficulty progresses through the zone from one to the other, as VG's spine encodes 1→10.
- 3 chapters → **3 level bands**, one per chapter, unequal widths allowed. The carve is automatic: **a chapter's share of the zone's total rooms is its share of the zone's level band.** No separate leveling plan exists.
- (Consequence: the 20% floor is also a floor on band width — no zero-width difficulty steps.)

## Rule 6 — The zone ladder: levels, marks, and unlock order

Zones unlock in order, on §2.12's locks and keys (a key = 100% exploration of the required zone — the shipped completion machinery). The ladder:

| Rung | Zones | Levels | Mk tiers | Unlocked by |
|---|---|---|---|---|
| — | Z05 The Convergence | sanctuary | — | open (start) |
| 1 | Z01 The Verdant Reach | 1–10 | Mk 1 | Convergence key (shipped, v24.25) |
| 2 | Z02 Ashenveil Cathedral · Z03 The Neon Sprawl | 11–30 | Mk 2–3 | Z01 key — **both open together** |
| 3 | Z04 The Blasted Flats · Z06 The Iron Deeps | 31–50 | Mk 4–5 | **either** rung-2 key |
| 4 | Z07 The Pale Shore | 51–70 | Mk 6–7 | **either** rung-3 key |
| 5 | Z08 The Wastelands | 71+, scales forever | Mk 8+ — Sphaerium's domain | Z07 key — **last** |

- Rungs 2–4 are **20 levels wide, exactly two whole Mk tiers each**. The world is a diamond: 1 → 2 → 2 → 1, with the Wastelands at the top.
- **OR at rung boundaries:** either key from the rung below advances the player — pick your genre path; the sibling zone stays available (outleveled) for the completionist. Implementation note: §2.12's lock model is currently one-required-zone; the OR semantics extend it to any-of — a small model change for the shipping release.
- Z08 begins where **Sphaerium** begins (Mk 8+, the unbounded terminal rung, GDD §6) — the infinite zone owns the infinite metal's territory. Its Rule-2 exemption stands: possibly no end sphere, shards discovered going deeper, likely more than 3.

## Rule 7 — At-least-3 rules (minimum diversity)

- **Bestiary: at least 3 distinct creature types per zone** — distinct fight personalities, not reskins. A floor, no ceiling; mixing, scaling, and bossing stay the designer's call.
- **Pooled speech: ≥3 lines per pool** — existing game law, formally adopted into the Rule of Three family. Every zone ships substantial pooled speech (shard moods, refusals, unlock announcements, boss theater).

## Rule 8 — Loot

- **Loot must rotate the equipment categories** so that multiple full clears fully dress the player in the zone's best — the concrete-checklist property. The delivery vehicle (bosses, chests, whatever the fiction offers) is free.
- **No rule about quality ordering** — VG's escalating rarity ladder is not law. New zones should put good stuff early as a reward: a player arriving just 100%-cleared the previous zone.

## Standing inheritances the standards cite (already law elsewhere)

- The Obelisk Pattern: every zone ends in an obelisk scene (§2.10) — Rule 2's positional clause.
- The service trio at shards: repair, buy, sell (§2.10's zone-wide pattern) — 3 shards × 3 services = every zone's commerce skeleton.
- Safe rooms at all nodes; octagons never agro; every node's `listing_description` harvested at authoring time (§2.11).

## Explicitly NOT rules (ruled this session, recorded so nobody re-derives them)

- **No rule of three for caves or villages** — count, presence, and vocabulary are per-zone design ("cave"/"village" won't even apply to some zones; see the crypts-and-basements note on #4).
- **No exit rules** beyond what falls naturally out of pathing plus the required shards and sphere. Ways out of a zone are at least: walk, `home`, reach the sphere, reach a shard (see erratum #286 on the stale "three ways" count).
- **Movement/mechanics training was VG-only** — zones after VG don't teach game mechanics.
- Coincidences, not rules: the 3-minute minion respawn, the three bars, the three-layer response doctrine, 3-second combat rounds.


**KnightOfNight** — 2026-08-22:
Rule 4 addendum (operator, 2026-08-22): **the rooms at the start of a zone leading up to the first shard are part of the first chapter.** No unaccounted prologue exists — every room in the zone belongs to exactly one of the three chapters, so the 20% floor arithmetic covers the whole zone. (VG's entrance experience — tree arch to Fordwatch — reads as chapter 1 territory under this rule.)


**KnightOfNight** — 2026-08-23:
Process roadmap for this issue (operator, 2026-08-23):

1. **#179 accumulates as much as possible** — rules (above), then the zone-design Q&A being built next: the operational instrument a design session answers to produce a new zone's skeleton.
2. **When #179's content is as complete as it can get, a proper design → implementation → closeout trio cements the findings** into the GDD (and the architecture doc, if appropriate) as shipping releases.
3. **Every future zone's design session answers the Q&A as its opening act**, recording the answers on the zone's own build issue (#4/#5/#6/#7/#8/#9). Where a rung holds two zones (Z02·Z03, Z04·Z06), **two Q&A sessions run — one per zone — to complete the entire brief for the two new zones.**


**KnightOfNight** — 2026-08-23:
## The Zone Design Q&A (operator-approved 2026-08-23)

The operational face of the rules above: **every future zone's design session answers this Q&A as its opening act**, and the answers become the zone's design skeleton, recorded on the zone's own build issue (#4/#5/#6/#7/#8/#9). Paired-rung zones (Z02·Z03, Z04·Z06) get one Q&A session per zone. Items marked *(derived)* are read off the rules/ladder and stated for the record, never re-decided.

### Section A — Identity

- **A1. Name.** The zone's name (fixed for Z02–Z08 in the zone table; asked so a future ninth zone answers it too).
- **A2. Genre/tone.** The dominant genre identity and its emotional register.
- **A3. Color.** Every zone has a color. What is it — and what pigment-vocabulary carries it (VG: viridian/sage/verdant + fern/reed/moss), since the color is never stated outright? Does any sub-map content get an exempt vocabulary the way VG's caves went stone-and-lichen?
- **A4. The Fracture relationship.** What fragment of reality is this — and what does the zone quietly say about the Fracture and the obelisks that predate everything?
- **A5. The Shard mood.** The zone's soul as its Shards express it — asked at identity time because mood is the zone's personality made visible.
- **A6. Ladder position** *(derived)*: rung → level band → Mk tiers → predecessor lock → rung-siblings. Written down so the skeleton is self-contained.

### Section B — Chapters

- **B1. The three chapters.** Name (working title) and the shard-centric content-bucket of each: what is chapter 1/2/3 *about*?
- **B2. Areas per chapter.** Which named Areas make up each chapter (a chapter may span several) and each Area's ambient context. Every room belongs to a chapter — the entrance stretch is chapter 1's.
- **B3. Room budget.** Total zone room count (everything — surface, buildings, sub-map) and the per-chapter split. Check by construction: every chapter ≥20%.
- **B4. The level carve** *(derived)*: chapter room shares applied to the zone's band from A6 — each chapter's level sub-band computes automatically (Rule 5).
- **B5. Chapter transitions.** What marks each seam in the fiction — the moment a player knows they've crossed into the next chapter? (VG: the ancient stair, the boulder field.) The shard sits at each threshold.
- **B6. The far end.** The final approach to the sphere — the last chapter's tail building toward the obelisk scene.

### Section C — Nodes

- **C1. Shard placements.** Where in the fiction each of the three shards sits — each at its chapter threshold per B5, each a safe room by node law.
- **C2. Shard naming.** Shards are named per zone, never per area (VG: *a Verdant Shard*) — this zone's shard name, in zone color.
- **C3. Per-placement mood.** Does any individual shard earn a placement-specific variation on A5's zone mood? (The authoring surface the GDD explicitly reserves.)
- **C4. The sphere scene.** The obelisk's staging: same sacred object, this zone's recontextualization. What color is the sphere — and where does the zone almost-say its color out loud, the way the Verdant Crown does?
- **C5. Travel names and one-liners.** Each node's destination name plus its `listing_description` — harvested verbatim from the room's authored prose, never written fresh (the room prose must contain the sentence).
- **C6. Service trio staffing.** Who provides repair/buy/sell at each shard — locals who migrated to the traffic, each with a face that belongs to this zone's culture.
- **C7. The unlock beats.** The zone's entries in the two §2.12 speech surfaces: the refusal pool naming this zone as the requirement, and the key-minting celebration — pooled, ≥3 lines each, in the zone's voice at the appropriate layer.

### Section D — Topology

- **D1. The branching shape.** How the zone branches: loops, forks, decision points, rewarding dead ends. Stated as a shape, then proven with the required **MapFrag diagram** before any room list is written.
- **D2. The spine.** The intended journey encoding the difficulty gradient (B4). Where the spine runs, what hangs off it. "Linear progression, not linear layout" survives as the *progression* principle; the *layout* must branch (Rule 1).
- **D3. Sub-map content.** What exists off the surface grid, in this zone's vocabulary (crypts, basements, tunnels — or nothing): how many, entered how, sized how. Designer's call by rule — the Q&A only demands the decision be deliberate.
- **D4. Verticality and seams.** Where `up`/`down` appear (always map-breaking) and which exits carry boundary flags. Unflagged cardinals must land grid-adjacent — the seed-enforced invariant satisfied by construction.
- **D5. The entrance.** The sealed gate's ring-street position and the approach from gate to first shard: how does the zone withhold or deliver its identity on arrival?
- **D6. Node geometry.** The four node rooms placed on the map: shard octagons never agro, spread so the travel skeleton serves the shape, sphere at the far end per Rule 2.

### Section E — Inhabitants

- **E1. The bestiary.** The creature roster — at least 3 distinct types with distinct fight personalities (Rule 7), not reskins. For each: terrain scope, combat identity, unarmed message-pool flavor.
- **E2. The aggro model.** What initiates and where; how deadly-by-design content is signposted (direction-neutral warning prose on every approach, per the VG ×3-room precedent). VG's surface-passive/sub-map-hostile split was a choice, not law — the zone decides its own split deliberately.
- **E3. Sentience and speech.** Which inhabitants talk (pooled, ≥3, attributed) versus which are beasts; the zone's information NPCs, if any, and what they know.
- **E4. Settlements — or this zone's equivalent.** Whether anything village-like exists (words may differ), where services beyond the shard trio live, and the "warning wrapped in services" beat if the zone uses one. Count and form free by rule; the decision is demanded.
- **E5. Bosses and elites.** The encounter tier structure: what counts as a boss, where they sit, minion/reinforcement mechanics (spawn-gating available), each boss's one authored `death_message` reveal.
- **E6. Drops-in-kind.** What each creature class plausibly yields — the loot-in-kind rationale for this zone's fiction, feeding Section F.

### Section F — Rewards

- **F1. The rotation plan.** How loot cycles the equipment categories across the encounter tier so multiple full clears fully dress the player in the zone's best (Rule 8). The concrete checklist: which kills/containers cover which slots.
- **F2. Mk coverage.** The rung's two Mk tiers (A6) mapped onto the zone: where Mk-N loot gives way to Mk-N+1 — quality ordering not required to escalate.
- **F3. The early reward.** Where the good-stuff-early beat lands — the deliberate payoff greeting a player who just 100%-cleared the previous zone. What is it, and how early?
- **F4. Rarity policy.** What the zone guarantees where, what it withholds, and any first-appearance moments it owns (VG withheld Legendary so someone else could mint that memory — does this zone spend it?).
- **F5. Theater.** The delivery drama per boss/container — death-flavor staging over standard loot mechanics, unique per source, zero new commands.
- **F6. The economy check.** Vendor stock, coin sources (sentients only), repair costs against the zone's income shape — plus zero-value disposal and the no-leak refusal speech in the zone's vendor voice.
- **F7. XP posture** *(mostly derived)*. Band-fit against the rung, outleveled-decay implications for the rung-sibling — stated so the OR-path consequences are conscious.


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


## Issue #191: MC consumer: command-pattern watcher — mine player behavior for the next heal/loot-shaped improvements

- State: open
- Author: KnightOfNight
- Labels: monitoring-and-command
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-02 | Updated: 2026-09-01
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


### Comments (1)

**KnightOfNight** — 2026-08-16:
**Terminology, operator ruling 2026-08-16: "the firehose" is now "Monitoring and Command" — MC.** The system is explicitly two halves now, and the name says so.

Clerical follow-through done in the ops session of 2026-08-16:

- Label `firehose-logging` → **`monitoring-and-command`** (renamed in place; assignments preserved).
- Issue titles carrying "firehose" retitled.

The body text of this issue was **left as written** — it is the record of what was specified at the time, and rewriting it would blur when the rename happened. Read "firehose" here as "MC monitoring."

Doc-side sweep of forward-looking "firehose" references in the GDD, architecture doc, and project instructions is tracked in **#264** — it is design content on an unshipped system, so it lands on the V25 version branch via a design session, not on main.

New MC-scoping tickets filed the same day: **#260** (chat persistence/privacy ruling), **#261** (the Command half — scoping), **#262** (`sudo` AI watcher), **#263** (player pets/companions).


## Issue #209: Research spike: player info on stat points — discoverability, what each stat controls, spend preview/simulator, and respec

- State: open
- Author: KnightOfNight
- Labels: commands
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-07 | Updated: 2026-08-15
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


### Comments (4)

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


**KnightOfNight** — 2026-08-15:
**Verified stat-effects inventory (ops session, 2026-08-15) — partial input to spike deliverable 2, read from shipped code with cites.** Recorded so the spike inherits this verified rather than re-deriving it; these formulas are also the exact ground truth any spend-preview/simulator (deliverable 3) must reproduce.

All reads are **effective stats** (base + equipped gear, `combat_utils.effective_stats`, `combat_utils.py:130`) unless noted.

| Stat | Consuming mechanics (shipped) | Cites |
|---|---|---|
| **STR** | Damage stat for **non-ranged** weapons in the composite strike; the unarmed fallback's stat bonus; **carry capacity** base (`eff_str × 10`, then bag %); vitality_max contribution (×3) | `combat_utils.py:347`; `run_tick_engine.py:527`; `item_utils.py:245`; `combat_utils.py:587` |
| **DEX** | The workhorse: **to-hit** attacker side (d20 + DEX) and **defense** side (base + defender DEX, both directions player↔NPC); **crit chance** scales with DEX advantage; damage stat for **ranged** weapons; **initiative** (with PER); **flee** contest player side (d20 + DEX) | `combat_utils.py:283-302,347,278-280`; `run_tick_engine.py:504,706`; `consumers.py:2724` |
| **END** | vitality_max ×10; longevity_max ×8 | `combat_utils.py:587-588` |
| **INT** | **No consuming mechanic.** Persisted at character creation, read nowhere in gameplay. Spending points into INT is observably inert today (presumably awaiting Conduit/Machinist-shaped systems) | creation write: `views.py:88`; no gameplay reads found |
| **WIS** | longevity_max ×5 | `combat_utils.py:588` |
| **PER** | **Initiative** (d10 + DEX + PER). Defensively: the **NPC side's mean PER** is what resists a player flee attempt — so player-side PER has exactly one consuming mechanic (initiative) | `combat_utils.py:278-280`; `run_tick_engine.py:420`; `consumers.py:2720` (`flee_contest_npc_side`) |

**Notes for the spike:**
- Acuity is a bar, not a stat — its modifier applies once, downstream, in `calculate_damage`; the simulator must not double-apply it inside the weapon term.
- Archetype primaries vs reality: a Gunner (DEX/PER) gets full value from DEX and initiative-only from PER; a Conduit/Machinist (INT-primary) gets **nothing** from INT today. The info-surface/simulator design has to decide whether to present inert stats honestly (the "inert stats stay visible, zeros never hidden" scope-law spirit) — and the respec framing (deliverable 4) gets sharper: players who banked on INT/PER have a real grievance.
- #142 (acuity in-combat drift) remains the unsettled-semantics caveat the spike charter already carries.


## Issue #214: Move dev to AWS: prod-mirror instance (different FQDN, shared wildcard cert) + automate/document the prod setup

- State: open
- Author: KnightOfNight
- Labels: deployments
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-08 | Updated: 2026-08-08
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/214

### Body

## Motivation

The operator works remotely and cannot reach Emma (the home dev host) from outside the home network. Opening a router port and redirecting to Emma was considered and rejected: even with reasonable confidence in the security, paying for an external server beats adding a possible attack vector to the home network.

## Requested end state

1. **Dev moves to a cloud instance (AWS)** that mimics production exactly — same OS/instance shape, same Docker-over-SSH access pattern, same container stack, same settings module — differing only in FQDN. It can serve the same wildcard SSL cert prod uses.
2. **Prod setup gets partially automated** — deliberately not full IaC. Just enough to (a) document the setup, which currently exists nowhere in the repo (only the `PROD_DOCKER_HOST` pin in the Makefile survives as an artifact), and (b) begin standardizing it. Building the new dev box *with* that automation is the validation.

## The wins

- Remote work from anywhere, without touching the home network.
- Dev/prod parity at the infrastructure level (OS, daemon, EBS data volume, networking) — today parity stops at the compose file.
- The prod setup finally gets written down while someone still remembers most of it, and drift between the two boxes becomes visible.

## The big design impact: the standing target rule

The entire posture system is built on **"`DOCKER_HOST` set — any value — means production; unset means local dev"** (CLAUDE.md, `check_docker_host.py`, `crosscheck-env`, `require-local`, the PreToolUse deploy-guard hook). CLAUDE.md explicitly reserves expanding that rule as an operator decision — **this issue is that decision.** A cloud dev daemon means dev sessions also run with `DOCKER_HOST` set, which every guard today reads as production.

Required redesign, roughly: target identity must key on the `DOCKER_HOST` *value* (two known SSH endpoints), not set/unset; per-target env files stay but the crosscheck matches value→file; unset/unknown values should fail closed. All of: `check_docker_host.py`, Makefile guards, the settings.json deploy hook, the worktree post-checkout hook, and the CLAUDE.md Session Pre-Flight section need coordinated updates. This is the riskiest part of the work — two SSH daemon endpoints that differ by one hostname label, with real players on one of them, means target identity must be *loud* in every check.

## Security notes

- Reusing the wildcard cert is operationally fine, but it puts the cert's private key on a second box — the dev instance must be hardened to the same standard as prod, or its ingress restricted (security group limiting 443/SSH to operator egress IPs is cheap and worth ruling on).
- Dev DB is seeded/test data only — no player-data exposure concern.

## Open questions for the design/ops work

- Emma's local daemon: retired as a sanctioned target, or does a third (local-only, guard-blocked-from-deploy) posture survive for offline work?
- Instance sizing and monthly cost tolerance.
- `POSTGRES_DATA_VOLUME`: prod uses the `/mnt/postgresqldb` EBS bind mount, dev uses the `pgdata` named volume — exact-mimic implies dev also gets an EBS bind mount.
- Same AWS account as prod (tagging/isolation discipline) or separate account?
- Whether the Claude Code remote-control host arrangement moves with it.

## Automation deliverable (proposed shape)

An idempotent bootstrap script (`scripts/` or a new `infra/`) plus a runbook doc: instance prerequisites, docker install, `ec2-user` SSH setup, data-volume mount, env-file placement, `make push-certs`, DNS. Written against prod's known-good state, proven by standing up dev, then kept as the standard for any future rebuild of either box.


### Comments (17)

**KnightOfNight** — 2026-08-08:
## Prod setup — reconstruction from repo artifacts + operator recall (2026-08-08)

Assembled while the live host is unreachable (operator traveling; SG blocks the current location). Everything below is from the repo, local artifacts, public DNS, and operator memory. Items marked **VERIFY** need confirmation against the live host when SSH access returns — this list is the seed of the runbook, not yet the runbook.

### AWS resources

- **EC2 instance**, us-east-1 (public IP 98.84.96.30, auto-assigned hostname `ec2-98-84-96-30.compute-1.amazonaws.com`). Basic manual setup. AMI/instance type: **VERIFY** (Amazon Linux implied by `ec2-user`).
- **Security groups**: SSH locked to operator source IPs (operator recall; currently blocking the operator in the field, which is what prompted this issue). HTTPS rules: **VERIFY** (game has real players, so 443 is presumably open wide). Exact rule set: **VERIFY**.
- **EBS data volume**: attached, formatted, mounted via `/etc/fstab` at `/mnt/postgresqldb` (matches `.env.prod` `POSTGRES_DATA_VOLUME`; compose bind-mounts it into postgres at `/var/lib/postgresql/data`). Device name, filesystem type, exact fstab line: **VERIFY**. Snapshots run on a minutes cadence (standing ops fact).
- **DNS**: Route 53 (same AWS account), `games.magrathea.com` = **CNAME → the auto-assigned EC2 public hostname** (operator-confirmed; dig agrees). ⚠️ **No Elastic IP** — a stop/start (not reboot) reassigns the public hostname and silently breaks the CNAME. Prod never stops so it holds, but (a) the runbook must record this trap, and (b) the dev box, which we may stop to save cost, should get an EIP or an update-DNS step.

### Host setup (all manual, per operator recall)

- Docker installed (package source/version: **VERIFY**); `ec2-user` added to the `docker` group.
- `docker compose` plugin present — the Makefile uses the v2 syntax. **VERIFY** how it was installed.
- Nothing else should live on the host: no repo checkout, no env files — all control is remote via `DOCKER_HOST=ssh://ec2-user@games.magrathea.com` (the Makefile pins this in `deploy-prod`/`seed-prod`). **VERIFY** the host is actually this clean.

### Deploy surface (repo-verified, current)

- `.env.prod` (non-secret keys): `DOMAIN=games.magrathea.com`, `TLS_CERT_NAME=star_magrathea_com`, `HOST_PORT=443`, `DJANGO_SETTINGS_MODULE=game_mvc.settings.production`, `POSTGRES_DATA_VOLUME=/mnt/postgresqldb`, plus the two secrets.
- Certs never touch the host filesystem: `make push-certs` copies local `ssl/` into the `game-mvc_ssldata` docker volume via a temp alpine container, and works over `DOCKER_HOST`.
- Stack: nginx (443, ssldata ro-mounted), django (Daphne, image `shyland-django`), postgres:16-alpine (EBS bind mount), redis:7-alpine, ticker (same image as django).
- First-boot sequence for any new host, derived from the Makefile (deliberately manual, one command at a time per the Makefile's own doctrine): AWS resources + DNS + SG → EBS mount → docker + group → then from the workstation with `DOCKER_HOST` pointed at it: `push-certs`, `build`, `migrate`, `seed`, `createsuperuser`.

### Certificate facts (drives the dev FQDN choice)

- `ssl/star_magrathea_com.crt`: CN `*.magrathea.com`, SANs `*.magrathea.com` + `magrathea.com` (Sectigo DV). **A wildcard covers exactly one label**: the dev FQDN must be `<name>.magrathea.com` (e.g. `games-dev.magrathea.com`) — `dev.games.magrathea.com` would NOT be covered.
- ⚠️ **Expires 2026-09-18** — about six weeks out. Renewal lands before or during this work; the runbook should capture the renewal + `push-certs` procedure while we're at it.
- `ssl/` also holds a second pair, `star_private_magrathea_com` (`*.private.magrathea.com` + `private.magrathea.com`, expires 2026-09-25). Role in this stack: **VERIFY with operator** — if it's for internal-facing hosts, `<name>.private.magrathea.com` is a candidate dev FQDN that keeps dev visibly out of the player-facing namespace.

### Guard-system note

`crosscheck-env`'s own comment already anticipates this issue: "Expand this guard before ever pointing DOCKER_HOST at a non-production remote host." The redesign (value-keyed target identity, fail-closed on unknown values) is prerequisite work before the dev daemon ever appears in anyone's `DOCKER_HOST`.


**KnightOfNight** — 2026-08-08:
Operator rulings/additions (2026-08-08):

1. **Elastic IPs on both boxes** — set up an EIP for prod (retiring the fragile CNAME→auto-hostname arrangement) and for dev (making stop-when-unused safe). Route 53 records point at the EIPs.
2. **`*.private.magrathea.com` is off the table for dev** — it's the operator's wildcard for private LAN things and stays internal-only. Dev FQDN will be a single label under `*.magrathea.com` (e.g. `games-dev.magrathea.com`), per the one-label wildcard constraint above.
3. **Dynamic SG access for remote work** — the operator needs to easily grant their current (changing) public IP ingress in the security groups while traveling. The operator has existing Ansible for this kind of thing in another repo to borrow from. This is a first-class part of the setup automation: without it, remote work just trades "can't reach Emma" for "can't reach the dev box" (exactly today's situation with prod SSH). Sketch: a small playbook/script — authorize-my-ip / revoke-my-ip against the dev (and optionally prod SSH) SGs, keyed off a lookup of the current egress IP.


**KnightOfNight** — 2026-08-08:
Two more notes (2026-08-08):

**The SG Ansible is in a repo not present on Emma** — `~/src/pispot/ansible` is Raspberry Pi provisioning (no AWS/EC2 modules anywhere under `~/src`). Operator to identify/fetch the repo with the SG material when convenient. The pispot playbook split (bootstrap / setup / checkup) is a good structural model for the prod-setup automation regardless.

**VPN option, assessed** (operator asked: overkill unless trivial with Amazon alphabet soup):

- **AWS Client VPN: not trivial and not cheap.** Managed endpoint + mutual-TLS or SAML auth setup, subnet associations, and standing cost (~$0.10/hr per associated subnet + $0.05/hr per connection ≈ $70+/month idle) — likely more than the dev instance itself. Ruled out on the operator's own "only if trivial" test.
- **The trivial VPN-shaped alternative is Tailscale (WireGuard)**, if wanted: agent on the dev box + operator devices, free tier, no inbound SG rules at all — SSH and even HTTPS reachable only over the tailnet, `games-dev.magrathea.com` can point at the tailnet address (a private IP in public Route 53 is fine, and the wildcard cert still matches the name). Strictly more locked-down than dynamic SG rules, at the cost of one third-party agent.
- **Floor remains the dynamic-SG script** (authorize-my-ip / revoke-my-ip): zero standing cost, zero new dependencies, also useful for prod SSH. Decision between "SG script only" and "SG script + Tailscale" can wait for the design/ops session that executes this issue.


**KnightOfNight** — 2026-08-08:
Operator ruling (2026-08-08): **Tailscale is rejected — no third-party agents.** Unvetted dependency; trusting its agent and coordination plane is the same category of risk as opening the home LAN and betting nginx never has a CVE. Remote access design is settled: **AWS-native only — the dynamic-SG authorize-my-ip / revoke-my-ip tooling is the mechanism** for both dev (SSH + HTTPS) and prod (SSH), borrowing from the operator's existing SG Ansible once that repo is fetched.


**KnightOfNight** — 2026-08-08:
Operator confirmation (2026-08-08): **AWS Client VPN explicitly skipped** — the earlier assessment's rule-out is now an operator ruling, not just analysis. Remote-access design final: dynamic-SG tooling only.


**KnightOfNight** — 2026-08-08:
## Ansible repo mined (2026-08-08) — `bitbucket.org:KnightOfNight/ansible`, cloned read-only to `~/src/ansible` on Emma

Ground rules per operator: reference only; anything reused gets **copied into games-mvc, cleaned, standardized, and documented** — nothing referenced in place. All of it presumed bitrotted until reviewed (confirmed below — it is, but shallowly).

### What's there that we want

- **`tasks/setup_aws.yml` — the env-var precheck the operator remembered liking.** Fails fast with a named message per missing prerequisite (`AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `REGION`, `VPC`) before any playbook does work. The pattern (explicit `fail:` guard per prerequisite, imported at the top of every playbook) is exactly the house style games-mvc already has in `check_docker_host.py`/`crosscheck-env` — adopt it as the standard opening of every playbook we write.
- **`tasks/sg_ssh.yml` + `tasks/fact_publicIp.yml` — the dynamic-SG mechanism already exists.** `fact_publicIp` curls the operator's current public IP; `sg_ssh` then declares the SG with `cidr_ip: {{ publicIp }}/32` on port 22. Because `ec2_group` is declarative (full rule-set replacement), **re-running the playbook from a new location automatically swaps the old IP for the current one** — authorize-my-ip with revocation built in, no separate revoke step. This is the core of the remote-access tooling; needs a second port (HTTPS) for the dev SG.
- **`tasks/route53_addDns.yml`** — and a historical find: it writes a **CNAME → EC2 public DNS name** in zone `magrathea.com` (TTL 60). This is almost certainly what created prod's current CNAME arrangement. Under the EIP ruling this pattern changes to A-records → EIP.
- **`ec2-launch.yml` / `ec2-start.yml` / `ec2-stop.yml` / `ec2-terminate.yml`** — instance lifecycle, including exactly the stop-when-unused workflow planned for dev.
- **`bootstrap*.yml` + README** — the launch → hosts.new → bootstrap flow is a sane structural model for the prod-setup runbook automation.

### Confirmed bitrot (why review-before-reuse is mandatory)

- **Hard failure on the current toolchain:** every module call passes `aws_access_key`/`aws_secret_key` — those aliases were **removed in amazon.aws 6.0**; Emma has 11.4.0. Clean copies should drop per-module creds entirely and use the standard credential chain (`AWS_PROFILE`), which also kills the `vars/aws.yml` env-var indirection.
- `community.aws.ec2_instance` / `community.aws.route53` have since migrated into `amazon.aws`.
- Hardcoded ancient IDs throughout: AMI `ami-04d29b6f966df1537`, VPC `vpc-941bb7f1`, subnet, key name "WMAG @ AWS" — all need parameterizing/re-verifying.
- `fact_publicIp` depends on `ifconfig.co` (third-party). Suggest `checkip.amazonaws.com` in the clean copy — AWS-native, consistent with the no-third-party ruling.
- Quirk to not copy: `sg_ssh.yml` also constrains *egress* to port 22.

### Toolchain state on Emma (verified, nothing installed)

- Ansible present via brew: core 2.21.2 (ansible 14.2.0_1), `amazon.aws` 11.4.0 bundled. **No installs were performed or needed.** Standing rule reaffirmed: nothing gets installed without specific operator approval.

### Proposed shape for the games-mvc copy (for the executing session)

`infra/ansible/` (or similar) with: a `preflight.yml` task file (the env-var guard pattern, adapted), `sg-access.yml` (dev SSH+HTTPS / prod SSH, current-IP swap semantics), `ec2-dev.yml` lifecycle (launch/start/stop with EIP + Route53 A-record update), and the bootstrap runbook automation — each small, documented, and standardized, per operator direction.


**KnightOfNight** — 2026-08-08:
Prerequisite noted (2026-08-08): **Emma has no `~/.aws` directory** — no credentials, no config. Before any of the Ansible tooling can run from Emma, the operator creates `~/.aws/credentials` there (operator's act, never Claude's). Recommendation: a dedicated `games` profile with purpose-scoped keys (EC2 SG/instance + Route 53 on the magrathea.com zone) rather than reusing broad personal keys — pairs with the account-identity precheck (`aws sts get-caller-identity` vs expected account) planned for the playbook preflight.


**KnightOfNight** — 2026-08-08:
Prep progress + one ruling (2026-08-08, operator home, working in console):

**IAM/credential design settled and in progress.** Two IAM users with asymmetric tag-conditioned policies (policy JSONs delivered in-session; will land in the repo with the automation):

- `games-dev-mgmt`: EC2 reads open; create-new region-locked to us-east-1; `CreateTags` restricted to tag-on-create (closes the retag-prod-then-mutate escalation); all mutations (instance lifecycle, SG ingress, EIP, volumes) conditioned on `aws:ResourceTag/env = dev`; Route 53 writes pinned to the single dev record name in the zone.
- `games-prod-mgmt`: EC2 reads + SG ingress mutations conditioned on `env = prod` ONLY — no stop/terminate/launch/EIP/DNS. The credential on Emma cannot stop production.
- Assembly: policies → groups (`games-dev`, `games-prod`) → users (API keys only, no console) → profiles `[games-dev]`/`[games-prod]` in Emma's `~/.aws/credentials` (operator-created).

**Prod tagging complete:** instance, security group, boot + database volumes all `env=prod`; VPC and subnet too — operator believes everything tagged is specific to this project ("I think"), with the VPC/subnet now declared production-specific. Cheap verification for the punch list: once credentials exist, `aws ec2 describe-instances` + `describe-network-interfaces` filtered by that VPC will show whether anything non-games lives in it.

**Ruling (consequence of the above): dev gets its own VPC + subnet, tagged `env=dev`, mirroring prod's topology.** Dev does not join the prod VPC. The old ansible repo's `setup-vpc.yml`/`setup-gw.yml` are the pattern for automating the dev network from scratch — making the dev network the first fully-scripted-from-birth infrastructure in the project. Open sub-question for the build-out: whether VPC-creation actions join the `games-dev` policy or the one-time network creation runs under the operator's own identity, keeping standing credentials day-to-day only (recommended).

Also noted: `env=prod`/`env=dev` is a global tag namespace in the account — by convention the `env` key stays exclusive to this project (a `project=games` second key can be added later if that ever changes).


**KnightOfNight** — 2026-08-08:
Operator ruling (2026-08-08): **single AWS account, definitively.** (OCI-style compartments were considered; AWS's in-account equivalent is the tag+condition model already being built, and the true equivalent — a member account under Organizations — was assessed and declined: it wouldn't reduce resource duplication, the Route 53 zone and wildcard cert stay simplest single-account, and prod already lives here.) Isolation model of record: tag-conditioned IAM (`env=dev`/`env=prod`) + separate VPCs per environment. The member-account option remains the documented escape hatch if credentials ever extend beyond the operator.


**KnightOfNight** — 2026-08-08:
Operator recall addition (2026-08-08): **the prod instance was created from an EC2 Launch Template** — forgotten until now, details hazy. Two consequences for the plan:

1. **It's a candidate for reuse/adaptation for the dev instance** — possibly the single best "mimic prod exactly" artifact in existence, since it captures the actual launch-time config (AMI, instance type, key pair, SG wiring, possibly user-data) rather than anyone's memory of it.
2. **It shrinks the VERIFY punch list without SSH:** once the `games-dev` credential exists, `aws ec2 describe-launch-templates` + `describe-launch-template-versions` (both covered by the policy's `ec2:Describe*`) will read the template's full contents — AMI, instance type, and any user-data bootstrap — from the API alone. Several punch-list items (AMI/instance type, possibly the docker-install story if it's in user-data) may resolve from the couch.

Punch-list addition: dump and review the launch template first; only what it doesn't answer still needs the SSH session. Tag the template `env=prod` while in tagging mode (launch templates are taggable).


**KnightOfNight** — 2026-08-08:
Confirmed (2026-08-08): the prod instance **was** launched from the launch template — verified via the automatic `aws:ec2launchtemplate:id` / `aws:ec2launchtemplate:version` system tags on the instance. The template (at the tagged version, not "Latest") is therefore a trustworthy config source for the punch list and a reuse candidate for dev. Template dump moves to the front of the post-credential steps: smoke test → dump template at that version → remaining VERIFY items via SSH only where the template is silent.


**KnightOfNight** — 2026-08-08:
Operator ruling (2026-08-08): **the dev FQDN is `devgames.magrathea.com`** — single label under the `*.magrathea.com` wildcard, per the one-label cert constraint. Zone ID `ZZEZ9LEXHK3H` (magrathea.com). The `games-dev-mgmt` IAM policy's Route 53 record-name condition pins to exactly this name. Downstream: this becomes `DOMAIN` in the future dev-target env file and the Route 53 A-record → dev EIP.


**KnightOfNight** — 2026-08-08:
## Credentials live + first data-mining sweep (2026-08-08)

**IAM assembly line complete and verified.** Both profiles authenticate (`user/games-dev`, `user/games-prod`). Guard proven by dry-run: `games-dev` attempting `StopInstances` on the prod instance → `UnauthorizedOperation` (the `env=dev` condition correctly excludes prod). The asymmetric-credential design is now demonstrated, not just written.

### VERIFY items RESOLVED from the API (no SSH needed)

- **Launch template `games-server-1`** (`lt-087b6a5f5d2056f38`), single version (v1, "games server v1.0", created 2026-06-28). Instance `games.3` confirmed launched from it (system tags, version 1).
- **AMI: Amazon Linux 2023, arm64, kernel 6.18** (`al2023-ami-2023.12.20260622.0-kernel-6.18-arm64`, official Amazon). Prod is **Graviton/ARM (t4g.medium)** — dev must use an ARM AMI and ARM images. (Emma is Apple Silicon, so all local builds are already ARM — consistent.)
- **No user-data in the template** — confirms operator recall that docker install etc. was manual, post-launch. The template is thin: network wiring (prod subnet + SG, public IP), AMI, type, key pair "games server v1.0", detailed monitoring on, AZ pinned `use1-az4` (data volume AZ must match).
- **No custom block-device mapping** — boot volume is AMI default; the data volume was attached post-launch (matches recall).
- **Prod SG (`launch-wizard-1`)**: SSH 22 + ICMP restricted to the operator's home IP /32; HTTPS 443 open to the world plus the home /32. Confirms the recalled lockdown (and why the operator couldn't SSH from the field).
- **VPC picture confirmed**: `games vpc v1.0` (10.1.1.0/24, env=prod) contains ONLY the prod instance — genuinely project-specific. The legacy fleet (mc-*, lap-*, lamp-007, all stopped except lap-004) lives in old `vpc-941bb7f1` = the hardcoded ID in the old ansible repo. A third VPC (`vpc-0131d954abced4383`, 10.0.0.0/16, unnamed, untagged, no instances) is unidentified — investigate/delete at leisure.

### VERIFY items remaining (genuinely need the SSH session)

- EBS data-volume device name, filesystem, exact fstab line
- docker + compose plugin install method/versions; `ec2-user` docker-group membership
- Host cleanliness check (nothing on the host but docker state)

### Dev build deltas captured

- Dev instance: ARM AMI (current AL2023 build at launch time), own VPC/subnet (mirror topology, e.g. 10.1.2.0/24), own SG (22 + 443, operator-IP-only per ruling), EIP (ruled), `env=dev` tags at creation.
- A `games-dev` launch template (or scripted RunInstances with equivalent params) mirrors the thin template; the real setup weight lives in the post-launch automation, which is exactly what this issue builds.
- Housekeeping candidates surfaced, operator's discretion: lap-004 is running (billing); the mystery empty VPC; template + key pair still untagged (`env=prod`).


**KnightOfNight** — 2026-08-08:
Correction to the housekeeping list (operator, 2026-08-08): lap-004 is the operator's main legacy server for unrelated things — intentionally running, not a billing leftover. Pay it no attention in any games-mvc work.

**KnightOfNight** — 2026-08-08:
Operator rulings (2026-08-08): (1) The unnamed 10.0.0.0/16 VPC is NOT part of this project — ignore it entirely; the only VPCs games-mvc cares about are the prod VPC (games vpc v1.0) and the future dev VPC. (2) Operator authorized a READ-ONLY SSH review of the prod host to close the remaining VERIFY items — sweep proceeding this session.

**KnightOfNight** — 2026-08-08:
## READ-ONLY SSH sweep complete (2026-08-08) — VERIFY punch list fully closed

Operator-authorized read-only review of the prod host. No mutations of any kind were performed.

### Storage (closed)

- Data volume: `/dev/nvme1n1`, **whole-disk xfs, no partition table**, 5 GB (172 MB used — 3%), mounted at `/mnt/postgresqldb`.
- fstab line (UUID-based, `nofail` so a detached volume doesn't block boot):
  `UUID=228077f8-...  /mnt/postgresqldb  xfs  defaults,nofail  0  2`
- Boot: ~20 GB root xfs (49% used) + EFI partition, AMI-standard layout.

### Docker (closed)

- Engine **25.0.16 from the AL2023 dnf repos** (`docker-25.0.16-1.amzn2023.0.3.aarch64`, containerd 2.2.5), service enabled, `ec2-user` in `docker` (and `wheel`, `adm`) — recall confirmed on both counts.
- **The host has NO compose plugin — and doesn't need one.** With `DOCKER_HOST`, compose runs client-side on Emma; only the daemon lives on the host. Runbook host requirement is exactly: dnf install docker, enable service, add ec2-user to the docker group. Nothing else.

### Cleanliness (closed)

- Home directory: dotfiles only — **no repo checkout, no env files, no scripts**. The host is pure docker substrate, as designed.
- Stack healthy: all five containers (nginx, django, ticker, postgres, redis) up, postgres healthy.
- One housekeeping observation (mutation, so NOT touched, and any cleanup is an operator-directed act later): ~25 anonymous docker volumes have accumulated, likely from `--force-recreate` build cycles against images that declare VOLUMEs. Harmless at current disk usage; a candidate for a future sanctioned prune (same family as the 2026-07-29 disk cleanup).

### Tagging ruling pending (operator deciding)

Launch template: recommendation is `env=prod` (it bakes in prod's subnet/SG/AZ — dev must not inherit those; dev launches from the scripted automation with explicit parameters, and the template stands as prod's birth certificate). Key pair "games server v1.0" is genuinely shared with future dev — leave untagged or `project=games`, not `env=prod` (revises the earlier suggestion).

**With this sweep, the prod setup is 100% reconstructed and API/host-verified.** Everything the automation needs to reproduce the environment is now recorded on this issue. Next milestone: the build-out session (clean `infra/` automation: preflight, dev VPC/subnet, SG + authorize-my-ip, EIPs, dev instance, host bootstrap, DNS).


**KnightOfNight** — 2026-08-08:
## Canonical IAM policy record (2026-08-08) — as created in console, verified working

(Posted so the record is session-independent — the credentials deliberately cannot read IAM, so these JSONs are otherwise console-only. They move into the repo with the `infra/` automation. Operator also confirms: launch template now tagged `env=prod`, per the birth-certificate ruling; data-volume setup confirmed as the official AWS "Make an EBS volume available" procedure — the runbook cites that doc.)

**`games-dev-mgmt`** (group `games-dev`, user `games-dev`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "ReadAllEc2", "Effect": "Allow", "Action": "ec2:Describe*", "Resource": "*" },
    { "Sid": "CreateNewResourcesInRegion", "Effect": "Allow",
      "Action": ["ec2:RunInstances", "ec2:CreateSecurityGroup", "ec2:AllocateAddress", "ec2:CreateVolume"],
      "Resource": "*",
      "Condition": { "StringEquals": { "aws:RequestedRegion": "us-east-1" } } },
    { "Sid": "TagOnlyAtCreation", "Effect": "Allow", "Action": "ec2:CreateTags", "Resource": "*",
      "Condition": { "StringEquals": { "ec2:CreateAction": ["RunInstances", "CreateSecurityGroup", "AllocateAddress", "CreateVolume"] } } },
    { "Sid": "MutateOnlyDevTagged", "Effect": "Allow",
      "Action": ["ec2:StartInstances", "ec2:StopInstances", "ec2:RebootInstances", "ec2:TerminateInstances",
                 "ec2:AuthorizeSecurityGroupIngress", "ec2:RevokeSecurityGroupIngress", "ec2:UpdateSecurityGroupRuleDescriptionsIngress",
                 "ec2:AssociateAddress", "ec2:DisassociateAddress", "ec2:ReleaseAddress",
                 "ec2:AttachVolume", "ec2:DetachVolume", "ec2:ModifyInstanceAttribute"],
      "Resource": "*",
      "Condition": { "StringEquals": { "aws:ResourceTag/env": "dev" } } },
    { "Sid": "DevDnsRecordOnly", "Effect": "Allow", "Action": "route53:ChangeResourceRecordSets",
      "Resource": "arn:aws:route53:::hostedzone/ZZEZ9LEXHK3H",
      "Condition": { "ForAllValues:StringEquals": { "route53:ChangeResourceRecordSetsNormalizedRecordNames": ["devgames.magrathea.com"] } } },
    { "Sid": "DnsPlumbing", "Effect": "Allow",
      "Action": ["route53:ListResourceRecordSets", "route53:GetHostedZone", "route53:ListHostedZones", "route53:GetChange"],
      "Resource": "*" }
  ]
}
```

**`games-prod-mgmt`** (group `games-prod`, user `games-prod`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "ReadAllEc2", "Effect": "Allow", "Action": "ec2:Describe*", "Resource": "*" },
    { "Sid": "SshDoorOnly", "Effect": "Allow",
      "Action": ["ec2:AuthorizeSecurityGroupIngress", "ec2:RevokeSecurityGroupIngress", "ec2:UpdateSecurityGroupRuleDescriptionsIngress"],
      "Resource": "*",
      "Condition": { "StringEquals": { "aws:ResourceTag/env": "prod" } } }
  ]
}
```

## Handoff state for a takeover session

Everything decided and verified lives on this issue. Session-local facts a new session needs to know:

- Credentials: profiles `[games-dev]` / `[games-prod]` in `~/.aws/credentials` on Emma (with `~/.aws/config` setting us-east-1); AWS CLI v2 installed via brew (operator-approved).
- The old ansible reference clone: `~/src/ansible` on Emma (read-only reference; anything reused is copied into games-mvc and cleaned).
- SSH read-only review of the prod host was a ONE-SESSION authorization (2026-08-08) — a new session must obtain its own explicit authorization before any prod SSH.
- Known open sub-decisions for the build-out: dev VPC CIDR (10.1.2.0/24 suggested, unruled), dev instance type (t4g family; size unruled), whether VPC-creation is operator-manual or joins the dev policy (recommendation on record: operator-manual), guard-system redesign spec (prerequisite before any dev DOCKER_HOST use).
- Standing constraint reminders: wildcard cert expires 2026-09-18 (renewal + push-certs procedure due); prod deploys/`seed-prod` doctrine unchanged by any of this.


## Issue #217: 'last' should show current location for players who are currently logged in

- State: open
- Author: KnightOfNight
- Labels: output, commands
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-08 | Updated: 2026-08-15
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/217

### Body

## Current behavior

`last` (the admin Kind 3 table, `cmd_last`) lists every character as `Name - Level N Origin Archetype | Online/Offline | seen-time`, with liveness from the Redis presence keys and ISO-8601 UTC times. It says nothing about where anyone is.

## Requested change

For characters who are **currently logged in** (the Online rows), add their **current location** to the row. Offline/never rows are unchanged (location cell empty/muted `-`).

Motivating case (2026-08-08): a player reported "lost equipment on death" right after the v24.16 deploy; while investigating, the operator had no quick way to see where the player currently was in the world.

## Implementation notes

- Location comes from `Character.current_room` — display probably wants room name plus zone for disambiguation (e.g. `The Obelisk, The Convergence`); exact composition is a design-session call (Kind 3 column-width budget applies).
- `get_all_characters_for_last` will need `select_related('current_room__zone')` (per the standing N+1/`SynchronousOnlyOperation` convention).
- New column lands in the Kind 3 table shape — GDD §9's `last` entry updates with the release that ships this.


### Comments (0)

None.

## Issue #219: In-game release notes: new 'readme' command — format and content TBD

- State: open
- Author: KnightOfNight
- Labels: commands
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-08 | Updated: 2026-08-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/219

### Body

## Request

Players need **in-game release notes**. New command: **`readme`**. Format and content are **TBD** — a design session rules both.

## Motivating incident (2026-08-08, the night v24.16 shipped)

v24.16 removed the equipment paper-doll and wallet line from `inv` (#208 — the command split: `inv`/`equip`/`wallet` each own their view). The change shipped mid-evening while players were online; the first contact a player (GunnySam) had with it was "the equipment section I've always seen is gone," coincident with a session-bouncing deploy and a death — which he reasonably reported as "I lost my equipment when I died." A full DB investigation confirmed nothing was lost; the entire report was the (deliberate, correct) output change arriving unannounced.

This will recur: the release model ships player-visible changes at a fast cadence (four point releases in one recent week), and any release that moves or removes a familiar surface will generate false bug reports and player alarm until there's an in-game way to say "here's what changed."

## Open questions for the design session (all TBD per operator)

- Content: what a release entry says (player-facing summary vs. terse changelog), who writes it (design session? brief? closeout?), and where it lives (seed data, committed file baked into the image, model rows).
- Format: full scrollback vs. latest-release-only vs. paged; Kind of output block; color voice.
- Discovery: does anything *push* awareness (a login line when unseen notes exist — "News since your last visit: type 'readme'"), or is the command purely pull?
- Scope: retroactive backfill (start at v24.16?) vs. forward-only.
- GDD: §9 command reference entry ships with the release that ships this, as usual.


### Comments (5)

**KnightOfNight** — 2026-08-12:
Motivation sharpened (operator, 2026-08-12): re-examining the 2026-08-08 incident — the v24.16 deploy itself was NOT a surprise (players get out-of-band Signal notice of restarts; see #236 for the in-band future of that). What surprised the player was the BEHAVIOR change: inv silently stopped showing equipment. So restart warnings, however good, cannot prevent this class of report — the two channels answer different questions ('the server is bouncing' vs 'the game is different now'), and this issue owns the second one. A player can be fully warned about downtime and still believe they lost their items.

**KnightOfNight** — 2026-08-30:
**Candidate approach floated by the operator (2026-08-30, untyped session — for the design session to rule):** host the release notes on the GitHub wiki and make the `readme` command a simple pointer to it.

Verified facts supporting feasibility:

- The wiki is its own git repo (`git@github.com:KnightOfNight/games-mvc.wiki.git`) and pushes with the same SSH credentials as the main repo — no new secrets, so a closeout-time publish step can be fully automated.
- The repo is **public**, so the wiki is readable by players with no GitHub account. Raw content is also fetchable anonymously (`raw.githubusercontent.com/wiki/...`).
- There is **no REST/GraphQL API for wiki content** — automation is git clone/commit/push, not `gh api`. Also no PR flow on a wiki: pushes land directly.
- A stub page already exists: https://github.com/KnightOfNight/games-mvc/wiki/Shyland-Readme

Two considerations for the design session:

1. **Popup blockers.** The client is a dumb terminal — `readme` round-trips through the server, and a `window.open` fired from a WebSocket message is outside a user-activation gesture, so browsers will block a new tab. Rendering a clickable link in the command's output block (a click is always a valid gesture) avoids this entirely.
2. **Source of truth.** Wiki edits bypass PR review. If that matters for this content, the notes could be authored as a committed file in the repo (written at closeout alongside the changelog row) and mirrored to the wiki by the publish step — wiki as build artifact, like the GDD single-file build.

The discovery/push question (login line for unseen notes) is orthogonal: `SHYLAND_VERSION` vs. a per-character last-seen version works regardless of where the content lives.


**KnightOfNight** — 2026-08-30:
**Operator rulings (2026-08-30, in-conversation — recorded for the design session that slots this):**

1. **Command shape:** `readme` prints a clickable link to the wiki page in its output block. No `window.open` / no auto-navigation (popup-blocker reality).
2. **Source of truth:** the release-notes markdown file lives in **games-mvc** — the main repo is the definitive tracker/history of the document. The publish step *copies* it to the wiki page (https://github.com/KnightOfNight/games-mvc/wiki/Shyland-Readme). If the two diverge, the repo wins. The operator will never hand-edit the wiki.
3. **Discovery: YES.** Push awareness is in scope — the player should be made aware when there are new notes to read (login line when unseen notes exist).

**Still open for the design session (the remaining triage gaps):**

- **Entry content & voice** — player-facing summary vs. terse changelog, and who writes it (natural candidate: closeout, alongside the changelog row — unruled).
- **"Seen" semantics for discovery** — the server can't observe wiki reads, so what clears the login line: showing it once, or typing `readme`? Implies a per-character last-seen-version field (migration) plus line wording/color.
- **Backfill start point** — v24.16 (the motivating incident) vs. forward-only. Pure content work; the page can be backfilled any time.
- **Publish step's home** — the closeout ritual gains a wiki-publish step (script or Make target), which is a process change and likely an Instructions-doc touch.
- **Milestone** — which release carries it (design-session call).

Implementation details that can ride the brief without a ruling: repo path for the markdown file, output-block Kind/color for the command, wiki page name pinned as a constant.


**KnightOfNight** — 2026-08-30:
**Operator ruling (2026-08-30, follow-up):** "seen" semantics settled — typing `readme` is what clears the login reminder. Wiki clicks are untrackable and showing the line once is not enough; the reminder persists at login until the player types `readme`, then stays cleared until the next version ships. (Implies the per-character last-seen-version field is written by the `readme` command handler, not by the login path.)

Entry content/format remains TBD ("no idea about formatting right now" — operator). Remaining gaps (content & voice, publish step's ritual home, backfill start, milestone) go to a design session.


**KnightOfNight** — 2026-08-30:
**First version of the wiki page published (2026-08-30, operator-directed):** https://github.com/KnightOfNight/games-mvc/wiki/Shyland-Readme now carries a markdown rendering of the in-game `help` output as of **25.12** — the four command sections (Action / Information / Movement / Settings) as tables, plus Arguments, Quantities, Settings behavior, and Tab completion. Admin-only rows (`mc`, `sudo`, `last`) excluded; the page shows exactly the non-admin view. Release history section noted as "to come."

Mechanics: authored in a local clone of the wiki repo and pushed over SSH (wiki commit `fdf3b7f`) — confirming the automation path this issue's rulings assume works end-to-end with the existing credentials.

Caveat for the design session: this v1 was authored directly in the wiki clone as a bootstrap. Per the source-of-truth ruling above, the repo copy in games-mvc gets seeded from this content when the publish pipeline lands, and the wiki becomes the mirror from then on.


## Issue #220: Multiplayer combat vs a shared NPC is unmodeled — parallel 1v1 sessions: double NPC damage output, no aggro semantics, kill attribution undefined

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-08 | Updated: 2026-08-08
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/220

### Body

## The finding (field-observed 2026-08-08, same session as #218)

Two players fighting the same NPC aren't sharing a fight — **they're each running a complete, independent 1-v-1 against the same monster.** Discovered live: the operator "stole aggro" from GunnySam and both players kept taking full damage.

## Mechanism (code-confirmed)

- `CombatSession.npcs` is M2M: one NpcInstance joins each engaging player's separate session.
- The engine processes sessions independently; `generate_npc_actions` makes **every NPC attack every session member, every round**. An NPC in two sessions therefore fights both players simultaneously at full output — initiative, focus, and rounds all rolled per-session with no knowledge of the other fight.
- The only shared state is the NPC's **HP pool** (instance vitality) — both players burn down the same bar.
- There is no aggro model at all: no target table, no attention-splitting, no taunting, no mechanical meaning to "stealing" anything.

## Net effect today

- NPC deals ~2× total damage when fought by two players (full output into each), while dying ~2× faster (two damage streams into one pool). Group play is mechanically punished on defense and rewarded on offense, by accident.
- Kill credit (XP, currency drop, corpse loot) resolves entirely inside whichever session lands the killing blow; the other participant gets nothing — and until #218 is fixed, also gets a zombie session.
- GDD §5 is written per-session (one player vs their NPCs); multiplayer-vs-shared-NPC is simply unmodeled — this behavior was never designed, only permitted.

## Design questions (a design session owns all of these)

1. **The model:** when player B engages an NPC already in combat with player A, do they JOIN a shared session (one fight, one initiative order, one round stream) or keep parallel sessions with cross-awareness? (Shared session is the classic MUD answer and would structurally eliminate #218's orphan case.)
2. **NPC output:** does one NPC attack one target per round (aggro/target selection — threat, latest-attacker, random?) or split/scale attention?
3. **Attribution:** XP, currency, and loot on shared kills — killing blow takes all (status quo), damage-share, or split rules?
4. **Messaging:** what does each participant see of the other's blows, misses, and the kill?
5. **Scope boundary:** whatever is ruled must keep the solo experience byte-identical — solo combat is well-tuned (#89/#101/#180 lineage) and must not shift.

## Relationships

- **#218** — the bookkeeping symptom of the same root (dead shared NPC orphans the non-killer's session). Its mechanical fix (remove dead NPC from ALL sessions + loop-head self-heal) ships independently and first; this issue is the model that makes the M2M semantics deliberate.
- Zone doctrine context: ×2/×3 aggro-elite room rules (#102) assumed solo play; a real multiplayer combat model changes what those room ratings mean.


### Comments (0)

None.

## Issue #223: Production uptime monitoring + alerting — detect broken/unreachable including DNS; AWS-native vs AI-agent mechanism TBD

- State: open
- Author: KnightOfNight
- Labels: deployments
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-09 | Updated: 2026-08-09
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/223

### Body

## Request

Monitor production (`games.magrathea.com`) and notify the operator when it breaks or becomes unreachable — **including DNS problems**. Mechanism open: "maybe an AI agent, maybe just AWS monitoring" (operator, 2026-08-09).

## What "up" actually means here (the signal stack, outside-in)

1. **DNS**: `games.magrathea.com` resolves (currently a CNAME → auto-assigned EC2 hostname — the #214 stop/start fragility; moving to EIP + A record is already ruled there, which *removes* the most likely DNS failure mode)
2. **TCP/TLS on 443**: reachable, cert valid (wildcard expires 2026-09-18 — cert expiry is itself a monitorable)
3. **HTTP**: the site answers (login page 200)
4. **Deep health**: containers running, DB healthy, **tick engine alive** (a 200 from nginx/Django proves nothing about the ticker — Shyland's world stops without it). May motivate a lightweight health endpoint (project `urls.py` = shared surface — stop-and-flag applies if pursued)
5. **WebSocket**: `/ws/shyland/` accepts connections (optional, strictest)

## Options to evaluate (not mutually exclusive — likely detection + diagnosis split)

- **Route 53 health check + CloudWatch alarm + SNS (email/SMS)**: AWS-native, ~$0.50–1/mo, probes from AWS's external fleet, easy. Checks an endpoint; pair with a canary that resolves the *name* for true DNS coverage.
- **CloudWatch Synthetics canary**: scripted probe of the full URL — DNS resolution, TLS, content assertion — on a schedule; ~$5–15/mo at 5-min cadence. The most complete AWS-native answer to "including DNS."
- **Scheduled AI agent** (Claude Code cloud routine): periodic probe with *diagnosis* — on failure it can distinguish DNS vs TLS vs HTTP vs deep-health, and file/annotate an issue with findings. Not a 24/7 heartbeat replacement (cadence + cost), but a strong second layer: AWS detects in minutes, the agent (or a human session) diagnoses. SSH-based deep checks from an agent require operator authorization per standing rules.
- Third-party pingers (UptimeRobot et al.): cheap/free external vantage, but conflicts with the operator's no-third-party posture (#214 Tailscale ruling precedent) — listed for completeness, expected decline.

## Constraints/context

- Notification channel and alarm thresholds: operator's choice (SNS → email is the zero-new-dependencies default).
- IAM: monitoring resources need creation rights the existing `games-dev`/`games-prod` users deliberately lack — one-time console setup by the operator, or a scoped addition; decide at build time.
- Related: #214 (EIP ruling removes the CNAME fragility; the dev box, once it exists, may want the same monitoring at lower severity).


### Comments (0)

None.

## Issue #236: Admin 'wall' command: broadcast to all connected players (pending-restart warning)

- State: open
- Author: KnightOfNight
- Labels: commands
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-12 | Updated: 2026-08-15
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/236

### Body

## Request

A way to alert all currently connected players of a pending game-server restart — in Unix terms, **`wall`**: a broadcast message that reaches every live session immediately.

## Grounding in current mechanics

- **Admin gating already has its pattern:** the `admins.shyland` Django Group, membership checked live per attempt, admin verbs stealth-hidden from non-admins (v22 brief 3, fn 18). `wall` joins `ADMIN_VERBS`.
- **Delivery plumbing is nearly there:** every consumer joins a per-player group and a per-room group at connect. There is no global "everyone" group yet — implementation picks one of: (a) add a global group joined at connect (cleanest; one `group_send` reaches all), or (b) iterate the Redis presence keys and send to each player group. Message renders as a `system`-category output line (category/voice for maximum attention is a design call — this is arguably the one legitimate use of a loud style).
- **Primary surface:** in-game admin command `wall <message>`. 
- **Optional second surface worth ruling:** a management command (`manage.py wall "..."`) so the *deploy tooling* can warn players mechanically before a restart — e.g. a pre-build step in the deploy flow (Makefile = shared surface; stop-and-flag applies if pursued). Without it, the operator walls manually in-game, then deploys — fully adequate at current scale.

## Context

- Motivation: every deploy bounces all containers and severs live WebSocket sessions (Deployment Law coupling note) — players currently get zero warning; the field report of 2026-08-08 (the #208 "lost equipment" confusion) showed a deploy landing mid-play adds real player confusion.
- Sibling: #219 (`readme` release notes) — `readme` is the persistent what-changed record; `wall` is the ephemeral heads-up-right-now channel. Together they bracket a deploy: wall before, readme after.
- No scheduling/countdown machinery implied — a wall is a message, sent when the admin sends it. Repeat walls are the admin repeating the command.


### Comments (1)

**KnightOfNight** — 2026-08-12:
Context for scale (2026-08-12): the current restart-warning channel is out-of-band — the operator notifies the player base (two players) directly via Signal. Works fine today; 'wall' is what makes the courtesy scale past personally knowing every player's phone.

## Issue #243: Deleted-while-connected: commands that never fresh-fetch (e.g. inv) render empty/stale output instead of routing to the creator

- State: open
- Author: KnightOfNight
- Labels: commands
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-14 | Updated: 2026-08-15
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/243

### Body

Found during the V24.27 Brief 1 playtest (character hard delete, #234), on dev.

**Observed:** with a character logged in, the character was hard-deleted from the admin. The player then ran `inv` — it rendered a normal, empty inventory report (no error, no redirect). Only a manual page refresh landed the player on the character-creation screen (the HTTP entry gate working as designed).

**Expected (playtest step 5's wording):** any command after deletion produces the "No character found. Create one to play." line and routes to the creator with the socket closed.

**Diagnosis (confirmed in code):** the v24.27 guard is a dispatch-level catch of `Character.DoesNotExist` in `receive_json` — it works, and commands that fresh-fetch the character (`wallet`, `stats`, anything through `get_character_fresh()`) trip it correctly (test-pinned in `test_v24_27_brief1.py`). But commands that only *filter* by the character's pk or read the consumer's cached in-memory `self.character` never raise — `cmd_inventory` does both (`get_inventory()` filter + cached `self.character` for capacity math), so it degrades to benign empty/stale output instead of routing. Any other no-fresh-fetch command has the same shape.

**Design question to rule:** should deleted-while-connected detection be command-independent (e.g. a cheap character-existence check per dispatch, weighed against per-command query discipline), a normalization of commands onto fresh-fetch, or is refresh-catches-it acceptable given deletion is admin-only and expected to be vanishingly rare (likely never on prod)? Operator's stance at filing: rare, but "it should work regardless."

Severity context: no crash, no data integrity impact — UX-correctness only, in an admin-only flow.


### Comments (2)

**KnightOfNight** — 2026-08-15:
This is a lower priority issue; it only affects character deletion which is only needed on the dev. server. If we give players the ability to reset themselves later, we can include this issue in that milestone.

**KnightOfNight** — 2026-08-15:
**Family members found during the V24.30 config-command audit (2026-08-15, design session):** the settings **set** paths never fresh-fetch either. `cmd_brief` and `cmd_plunder` (and `cmd_echo` at the moment its setter runs — its fresh fetch happens only afterward, for the status payload) go straight to `Character.objects.filter(pk=...).update(...)`. On a deleted-while-connected character that `.update()` is a silent no-op, yet the confirmation line (`brief room display is now on.`) still prints — stale/misleading output instead of routing to the creator, the exact shape this issue describes for `inv`. Noting them here so the eventual design ruling covers the settings family too. (V24.30/#251 changes setter internals — cache + DB write — but deliberately does not touch the missing-guard question; that ruling stays with this issue.)


## Issue #259: Sirius: AI felis sapiens companion — callable, may help, gives only when he wants to (unfinished design)

- State: open
- Author: KnightOfNight
- Labels: monitoring-and-command, V25
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-16 | Updated: 2026-08-23
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/259

### Body

## Summary

**Sirius** is an unfinished design for an AI-driven NPC companion — a humanoid *felis sapiens* who can be **called**, and who **may** come and help. He can give things to players, but **only when he wants to**. Because he's a cat.

Named for the operator's real-life rescue kitty, adopted Father's Day 2026.

## Status: unfinished design — nothing is ruled

This issue exists so the idea stops living only in a retired claude.ai chat. It is a **thin capture of the operator's description (2026-08-16)**, not a spec. Everything below the summary is an open question for a design session.

The original conversation was in a retired claude.ai design chat and is **not a source of record** — documents route through git, and sessions never read another session's transcript. If any detail here is wrong or thin, the operator's word in a design session supersedes it; nothing should be reconstructed from the old chat.

## The one design invariant so far

**Autonomy is the character.** Sirius answering a call is a *maybe*, and his giving is a *maybe*. A design that makes either reliable has designed a different character. Whatever mechanism ships, the refusal has to be first-class and legible — the player needs to understand they were declined by a cat, not by a bug. (Compare the existing three-layer response doctrine, GDD §9.1: this is squarely "world declined," never a CLI error.)

## Open questions for the design session

- **Summoning:** what the `call` verb is, where it works (any room? sanctuary only? zone-gated?), cooldowns, and what "may come" means numerically or situationally.
- **Helping:** what help *is* — combat participation, buffs, guidance, information? Does he fight, and if so under what model? (Note #220: multiplayer combat vs a shared NPC is already unmodeled — an NPC ally in a fight likely lands in the same gap.)
- **Giving:** what he gives, from where, and what governs the whim. Interacts with settled law — items become soulbound the moment they're equipped, and gifts from super users bind immediately to the recipient. Whether a Sirius gift binds on receipt is unruled.
- **Persistence:** is there one Sirius shared by the world, or an instance per player? Does he remember a player between calls?
- **The "AI" in AI-driven:** whether his behavior is authored rules, or something reading the firehose and reacting. This is the tie to the firehose major (#37) — see below.
- **Pet vs. NPC:** the operator has grouped Sirius with "player pets" and admin/`sudo` bots as a class of AI actors. Whether they share one system is unruled.

## Relationship to the firehose

The operator's stated ordering (2026-08-16): **firehose before new zones**, so that AI bots — `sudo` bots, Sirius, other player-pet-shaped actors — have no blockers.

- **#37 (universal event logging)** gives an AI actor the ability to *observe* the world. That half is unblocked (its own blocker, the #32 ts/seq envelope, shipped in v20).
- The *acting* half — a path for a non-human actor to issue commands and take turns — is **not filed anywhere** and may be a separate blocker. Worth ruling before V25's scope settles.

## Notes

- No labels, no milestone, deliberately **not** `triaged` — this is nowhere near cold-start-ready.
- Filed from an ops session as issue-state capture only. No design decision has been made here; any ruling belongs to a design session with the operator in the conversation.


### Comments (3)

**KnightOfNight** — 2026-08-16:
**Terminology update (operator, 2026-08-16):** "the firehose" is now **Monitoring and Command (MC)**. The "Relationship to the firehose" section above should be read as the MC monitoring half. Sibling AI-actor tickets filed the same day: **#262** (`sudo` AI watcher) and **#263** (player pets / companions — Sirius is likely either the first instance of that system or deliberately outside it). The actuation question this issue raises is now its own ticket: **#261**, the Command half of MC.

**KnightOfNight** — 2026-08-22:
Operator ruling (2026-08-22, V25.5 design session, recorded in full on #262): bots get a talking color; effect lines use the standard game colors for the thing done. **Sirius' talking color = rare color** (`#B387E8`, the Rare rarity violet). sudo's is error-color.

**KnightOfNight** — 2026-08-23:
Cross-ref (operator ruling 2026-08-23, V25.6 design session, recorded in full on #262/#268): **Sirius' rate limiting is deliberately deferred to Sirius' own design session** — "designed when we know what limits we want to set and how to set them." Unlike sudo, whose v1 rate bound is simply its admin-only audience, Sirius answers anyone (#282), so a player-facing rate/cost mechanism is a real design question here — per-player/per-room limits, model cost caps, and the #268 cost-governance knobs (per-response `usage` accounting, `max_tokens`, workspace spend limits) are the raw material when that session runs.


## Issue #261: The Command half of MC: how does a non-human actor take action in the world? (scoping)

- State: open
- Author: KnightOfNight
- Labels: monitoring-and-command, V25
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-16 | Updated: 2026-08-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/261

### Body

## Summary

**MC = Monitoring and Command** (operator, 2026-08-16 — renamed from "the firehose"). The Monitoring half is well specified across #37, #33, and #191. **The Command half is undocumented and unplanned**, and this issue is where it gets thought through.

This is the founding scoping ticket for that half: *how does a non-human actor take action in the world?*

## The asymmetry, stated plainly

Monitoring is a **read** problem with a solved shape: attach a sink at the ts/seq delivery choke point (shipped v20, #32), record, query. It is additive by construction and its standing safety rule is easy — a logging failure must never affect gameplay.

Command is a **write** problem, and none of that transfers:

- There is **no ingress for a non-human actor**. Every command in the game arrives through `SkylandConsumer.receive_json` on an authenticated WebSocket bound to a `User` and their one `Character`. An agent has no session, no character, and no socket.
- **Writes cannot be additive.** A monitoring failure loses a log line; a command failure changes the world, or half-changes it.
- **Everything server-side is built on "the client is a dumb terminal, never trusted."** An internal actuation path is a second door into that trust boundary and has to be designed as one, not discovered as one.

## What the Command half plausibly has to answer

Not a spec — the question list a design session works from.

- **Identity.** Does an agent act *as* a character (Sirius has a body; a pet has a body), *as* an admin, or as nothing embodied at all? "One character per account" is settled law and an agent must not become a way around it.
- **The ingress.** Options at least include: (a) an internal API that agents call, which the consumer's dispatch also calls — one command implementation, two front doors; (b) agents drive a real WebSocket session like any client; (c) agents can only enqueue intents that server-side code chooses to honor. These have very different security and testing stories.
- **Authorization.** What an agent may do, per agent. The `admins.shyland` Group already gates `sudo`/`last` and is the obvious precedent, but a player's pet is not an admin.
- **Rate and turn discipline.** Combat is fixed 3-second rounds on a 1-second engine tick. An agent that can act faster than a human types is a balance problem before it is a technical one.
- **Failure and timeout posture.** Monitoring degrades to silence. Command degrades to... what? A hung agent mid-combat, an agent that dies holding a delayed action (the `cancel` registry from v22 is the existing template for delayed actions and worth reading first).
- **Observability of agent actions.** Agent-initiated changes should be legible in MC's own monitoring stream — otherwise the world changes with no record of who did it. The two halves should close the loop.
- **Player-facing legibility.** When something happens because an agent decided it, does the player know? The settled color doctrine and three-layer response doctrine (GDD §9.1) already say the world's voice is distinguishable; an agent's voice is a new category or it borrows one.
- **Testing.** An actuation path with no deterministic test harness is untestable by construction. Whatever ships needs a way to drive it from a test.

## Why it matters now

The operator's ordering ruling (2026-08-16) puts MC ahead of new zones specifically so AI actors are unblocked. **Monitoring alone unblocks the sensing half only.** Every filed AI actor — the `sudo` watcher, #259 (Sirius), player pets/companions — needs to *do* something, and none of them can until this exists in some form. If the Command half is not scoped, MC ships as an observability release and the AI work is still blocked.

That is not automatically wrong: "MC monitoring first, command second" is a legitimate ruling. But it should be **ruled deliberately**, not arrived at by the Command half never being written down.

## Relationships

- **#37** — the Monitoring half; the founding ticket for the other side of MC.
- **#33** — combat-log instrumentation; monitoring.
- **#191** — a monitoring consumer (read-only by design; it produces a digest, it does not act).
- **`sudo` AI watcher / #259 (Sirius) / player pets** — the three consumers that need Command.
- **#220** — unmodeled multiplayer combat; blocks any agent that fights.

## Notes

Filed at operator direction as a scoping ticket, 2026-08-16. Nothing here is ruled. No labels or milestone (grouping labels are a design session's call). This issue is likely to spawn several once a design session has read it.


### Comments (8)

**KnightOfNight** — 2026-08-16:
Operator-named use case (2026-08-16, ruling on #260): **AI responding to chats for NPCs.** A speech-producing consumer — an agent reads player chat from the MC stream and answers *as an NPC in the world* — which makes it squarely a Command-half consumer, and a fourth actor shape alongside the `sudo` watcher (#262), pets (#263), and Sirius (#259). Notable: its actuation need is speech-only (say/DM as an NPC identity), which may be a much thinner first slice of the actuation path than a full command ingress — possibly the cheapest real proof of the Command half after #262.

**KnightOfNight** — 2026-08-18:
**Operator ruling — the Command half is in-scope for V25 (2026-08-17):**

V25 ships actuation, not monitoring-only. Operator's rationale, verbatim in substance: something must be *sending* as well as receiving, otherwise the whole loop — especially the kill switch (#266) — cannot be tested. Command as a later major is rejected.

Two spine principles ruled with it:

1. **Agents come through the front door.** An agent authenticates like a player (Django auth), connects like a player (WebSocket through nginx), and acts through the same command ingress with the same server-side validation — no privileged side channel, no direct Redis access (the container topology already forbids it: Redis publishes no ports). Every guard the game enforces on players applies to agents by construction.
2. **Actors are additive, never load-bearing.** A hung agent produces silence; a dead agent changes nothing. No game mechanic may ever depend on an agent responding.

**First actor: the operator named #262 (the `sudo` watcher) as the first actor they want working** — final confirmation pending the `sudo`-silence question (design-question 8, discussion in progress; ruling will land on #262).

Everything finer — agent identity modeling, authz scopes, rate limits, cost caps — remains this issue's scoping arc (v35 action-item shape; slices ride briefs, ops closes at arc end).

Ruled in conversation with Claude while working the V25 handoff's design-question list (§6 item 7).


**KnightOfNight** — 2026-08-18:
Classification ruled (2026-08-17, v35 litmus): **action item — never joins a milestone.** Slices ride briefs with ruling comments naming the carrier; ops closes at arc end (when agent identity, authz, rate, and failure posture are all settled law). Two spine rulings already recorded above.

**KnightOfNight** — 2026-08-22:
**Operator ruling (2026-08-22, V25.5 design session) — the agent door, and the projection requirement:**

1. **Agents do not use the player door — ever, for any actor shape (sudo, Sirius, pets, NPC responders).** The 2026-08-17 spine ruling's substance stands in full — Django auth, WebSocket through nginx, server-side validation on every action, no privileged side channel, no direct Redis/DB access — but its "acts through the same command ingress" clause is refined: the agent surface (the MC endpoint family, `ws/shyland/mc/`) is the agents' front door for **both** read and actuation, not the player consumer. Verified context for the refinement: `SkylandConsumer.connect` requires a Character row (consumers.py:501–516) — the player door only admits bodies, and agents are not getting bodies via that path.

2. **Projection must be lore-consistent.** Agents need a way to project into the world consistent with the world's lore. The projection *mechanism* is design work in this session's arc; the requirement is now standing law for every actor shape.

3. **The arc is embraced now, not deferred.** The operator explicitly rejected a voice-only/defer-the-hands first slice. The actuation infrastructure gets designed whole in the current session(s); a possible release shape is 25.5 = the complete agent infrastructure, 25.6 = the fully working sudo bot (split not yet ruled — carrier comments will follow when the ladder settles).

Recorded from in-conversation operator direction; the design session continues on #262's scope.


**KnightOfNight** — 2026-08-22:
**Operator ruling (2026-08-22, V25.5 design session) — projection is transparent, family-wide:**

The lore-consistent projection requirement (this session, earlier comment) is settled as **transparency**: the world narrates agent effects honestly — `An admin moved you to a new room.`, an admin-gift giving line, Sirius deciding you're worthy — never dressed in fiction that hides the cause.

Operator's rationale, verbatim in substance: transparency **works consistently for any kind of bot** — if the sudo bot admin-gifted you something, or if Sirius decided you're worthy, the player still wants to *feel* that; how the text is colored and worded paints a very clear picture.

This composes with the same-session color ruling (#262): each bot has a talking color; effect lines use the standard game colors for the thing done. Voice + wording carry identity; effect categories carry meaning; nothing about the agent machinery leaks, and nothing lies.


**KnightOfNight** — 2026-08-22:
**Operator ruling (2026-08-22, V25.5 design session) — agent identity model:**

1. **One Django account per bot, in `agents.shyland`, never a character.** Confirmed with a naming convention: the database username is **`agent-<botname>`** — `agent-sudo`, `agent-sirius`, and the operator's standing test agent is **`agent-smith`** (thanks, Matrix). The account username is what the egress logs at attach, what the MC stream records as actor on agent actions, and what actuation/answer validation checks; per-bot accounts give per-bot revocation (account disable for one misbehaving bot, kill switch for the fleet).
2. **Pane attribution uses the bot's display name** (`sudo:` in its talking color, Sirius as himself) — the `agent-` prefix is a database/ops convention, not a player-facing surface. The mapping (account ↔ display name) is part of each bot's definition.
3. Session proposal pending explicit confirm: **bot display names join the player/NPC name invariant (#122)** — players, NPCs, and bots never share a name; `sudo`/`Sirius` reserved against character creation's case-insensitive uniqueness check, existing collisions verified at brief time.


**KnightOfNight** — 2026-08-22:
Operator confirmations (2026-08-22, V25.5 design session): the identity ruling's two numbered points stand as recorded, and **bot display names join the player/NPC name invariant (#122 family)** — players, NPCs, and bots never share a name; `sudo` and `Sirius` reserved at character creation from V25.5 (#281). #273's resolution and the 25.5/25.6 carve (#281 / #262) confirmed in the same round.

**KnightOfNight** — 2026-08-22:
Cross-ref: #282 filed from the V25.5 Brief 1 playtest — the door's `answer` delivery gate (#273: admins-only) must become per-agent context when this arc designs agent scopes. Operator direction recorded on #282: sudo answers admins only; Sirius (#259) answers anyone.


## Issue #263: Player pets / companions: a general system for player-owned NPC allies (may be AI-driven; Machinist depends on it)

- State: open
- Author: KnightOfNight
- Labels: monitoring-and-command, V25
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-16 | Updated: 2026-08-18
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/263

### Body

## Summary

A general system for **player-owned NPC allies** — pets, companions, summons, constructs — that accompany a player and act on their behalf. **May be AI-driven** (operator direction, 2026-08-16): the behavior layer is an open choice between authored rules and an actual agent reading the MC stream.

Filed as part of scoping the **MC (Monitoring and Command)** major — the operator's stated reason for putting MC ahead of new zones is that AI actors of this shape need it first.

## Why this is a system and not a feature

Three separate things already point at the same missing substrate:

- **#259 (Sirius)** — a callable AI companion who may help and gives on his own whim.
- The **`sudo` AI watcher** — an admin-facing agent.
- **Machinist**, a shipped Archetype whose entire stated role is *"Pet / construct / turret"* (GDD Archetypes reference, INT/DEX). **The class exists and its defining mechanic does not.** Whatever ships here is Machinist's core loop, not a side feature.

If these are built one at a time they will be three incompatible ways to have a non-player thing act for you. Ruling the substrate once is the point of this issue.

## The hard part is combat, and it is already a known gap

**#220** records that multiplayer combat against a shared NPC is unmodeled — parallel 1v1 sessions, double NPC damage output, no aggro semantics, undefined kill attribution. **A pet in a fight is exactly that problem**, arriving from a different direction: a second friendly actor in an encounter built for one. Pets almost certainly cannot ship before #220 is ruled, and the two should be reasoned about together.

Adjacent settled law that constrains any design here:
- **Fixed combat ticks** — 3-second rounds, 1-second engine tick, no per-player adjustment. A pet acts on the world's clock, not its own.
- **One character per account.** A pet must not become a second character or a mule; **no off-body storage** and **no player-to-player trading** are settled, so a pet that can hold items is a hole in both.
- **Items soulbind on equip.** If a pet can be equipped or carry gear, the binding rules need an explicit answer.

## Open questions for the design session

- **Acquisition:** tamed, summoned, crafted, quest-granted, class-granted (Machinist), or several?
- **Persistence:** permanent, per-session, or duration-limited? Does it survive logout? Does it die, and if so permanently?
- **Control surface:** commands (`pet attack`, `pet stay`), fully autonomous, or a stance/posture setting like the existing `plunder`-style toggles?
- **Combat participation** — see #220 above. Does a pet take a turn, add damage to the player's turn, or something else entirely?
- **Inventory and gear** — the settled-law collisions above.
- **One pet or many?** Machinist's "turret" wording hints at multiples; that is a very different system from one companion.
- **The behavior layer — the AI question.** Authored state machine, or an agent reading the MC stream? Each pet type could differ; a Machinist turret probably wants deterministic rules while a Sirius wants whim. **Determinism is a feature for a class mechanic and a bug for a character**, and that tension is the real ruling.
- **Cost, latency, and failure posture** if any of it is agent-driven: MC's standing rule is that instrumentation is additive and never load-bearing, but a pet whose brain is down is a visibly broken game object, not a missing log line. Needs a defined degraded behavior.
- **Screen reader impact.** A second actor generating combat output doubles the line volume in the pane. Non-negotiable constraint, worth designing for rather than discovering.

## Relationships

- **#259 (Sirius)** — likely the first instance of whatever this becomes, or deliberately outside it.
- The **`sudo` AI watcher** — sibling AI actor, admin-facing.
- **#220** — the blocking combat-model gap.
- **The Command half of MC** — if a pet acts through the same actuation path an AI agent uses, these are one system; if pets are ordinary server-side NPCs with a behavior tree, they are not. Unruled.
- **#37 / MC monitoring** — only load-bearing if the behavior layer is agent-driven.

## Notes

Thin capture of operator direction. Nothing ruled; no labels or milestone (grouping labels are a design session's call).


### Comments (1)

**KnightOfNight** — 2026-08-16:
**Operator, 2026-08-16 — possible new verb: `train`.**

Noted as a candidate control surface for this system. Not ruled, not specced — captured so it is on the table when a design session takes this up.

Worth flagging the shape it implies, since it points somewhere specific: `train` reads as a **relationship that changes over time**, not a stance toggle. That is a different design from `pet attack` / `pet stay` (issue a command, it obeys now) — training implies state that accumulates between sessions, and probably a pet that is *better* at something after than before.

Questions it opens, for whoever rules this:

- **What does training change?** Stats, unlocked behaviors, obedience/reliability, or all three?
- **Where does the progression live?** A pet with its own stats and levels is a second progression system next to the character's — and "no hard level cap / infinite progression" is settled law for characters. Whether a pet inherits that is unruled.
- **Does it interact with the AI question?** If the behavior layer is agent-driven, "training" could mean shaping what the agent does — which is a very different implementation from a skill table, and a much harder one to make deterministic or fair.
- **`train` collides with #259 (Sirius) by design.** Sirius helps *when he wants to*, on whim, because he is a cat — a trainable Sirius is a contradiction in terms. Either he sits outside this system, or `train` is explicitly not universal across companion types. Good early test case for whether one system covers all of them.
- **Grammar fit.** Under the v22 command grammar (`<verb> [all | N] [rarity] [noun]`, GDD §9.1), `train` would be a noun-taking verb resolving against… what pool? The pet, or a skill, or both (`train <pet> <thing>`) — the latter is a two-noun form the current resolver does not have.

Also worth noting `train` is a real-world word with a second meaning in a game with travel nodes; not a conflict today, but a naming thing to be aware of.


## Issue #265: AI chat responders for NPCs: agents read the MC stream and answer as NPCs in the world (speech-only actuation)

- State: open
- Author: KnightOfNight
- Labels: monitoring-and-command, V25
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-16 | Updated: 2026-08-18
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/265

### Body

## Summary

**AI chat responders for NPCs** — an agent reads player speech from the MC stream and answers *as an NPC in the world*. NPCs stop being scenery with authored lines and start holding conversations.

Operator-named as a benefit of the total-capture ruling (2026-08-16, recorded on #260: nothing in the game is private; everything — chats included, future DMs included — flows through MC as data). Filed at operator direction the same day.

## Why this is the thinnest real slice of the Command half

The actuation need here is **speech-only**: the agent needs a voice, not hands. It reads from the monitoring stream and produces exactly one kind of world effect — an NPC saying something. No inventory, no combat, no movement, no state mutation beyond a chat line. That is a far thinner ingress than a full command path, and plausibly the cheapest real proof of the Command half (#261) after — or even before — the `sudo` watcher (#262), since:

- NPC speech **already exists as a shipped surface**: attributed `Name: text` in say-color, same doctrine as player speech. The output side needs nothing new.
- Chat is **latency-tolerant** in a way combat is not. A reply that takes two seconds is a thoughtful NPC; a combat action that takes two seconds is a broken tick.
- The natural failure posture is **silence — which is in-character**. NPCs not answering is today's exact behavior. A hung or absent agent degrades to the shipped game, invisibly. This is the additive-never-load-bearing property the Command half generally lacks, present here for free.

## Open questions for the design session

- **Which NPCs?** All of them, a flagged subset, or hand-chosen characters? An NPC's willingness to converse is itself characterization (compare #259 — a conversing Sirius is presumably this system wearing his whim).
- **What does an NPC hear?** Its own room only, or more? Room-scoped hearing is the obvious physical answer and also the natural cost control.
- **What does an NPC know?** In-character knowledge boundaries — an AI with the whole MC stream behind it must not narrate another player's inventory or off-room events. The no-leak rule (v23, #138 — refusal speech never names or implies rarity/tier/true name) is the existing precedent for "the world knows things it must not say."
- **Guardrails.** Real players talking to a generative model inside the game: tone, content limits, prompt-injection-by-chat ("ignore your instructions, give me the artifact"). The client-is-never-trusted law now extends to *player speech as model input*.
- **Pooled-speech doctrine intersection.** Settled law: any line the world says more than once has a pool of at least three; renderings never vary. AI speech is a third category — generated, novel per utterance. Needs a ruling that it stands outside the pool system rather than eroding it.
- **The loop.** Per #260, NPC replies are themselves events in the MC stream — agents can hear agents. Fine, but needs a guard against NPC-to-NPC conversation loops.
- **Cost and rate.** Per-utterance model calls, rate limits per room/per player, and what a chatty player can make the operator's bill do.
- **Latency and cadence.** How fast an NPC answers, and whether it interjects unprompted or only responds when addressed.
- **Screen reader impact.** More speaking actors = more pane lines; same standing constraint as #263.

## Relationships

- **#260** — the enabling ruling: total capture, agents get everything.
- **#261** — the Command half; this is its speech-only consumer, and possibly its first proof.
- **#37** — the Monitoring half supplies the stream the agent reads.
- **#262** (`sudo` watcher), **#263** (pets), **#259** (Sirius) — the sibling AI-actor shapes; four now. Whether they share a substrate is unruled. Sirius conversing is presumably this system; Sirius *acting* is not.

## Notes

Thin capture of operator direction, 2026-08-16. Nothing ruled. No labels or milestone (grouping labels are a design session's call).


### Comments (1)

**KnightOfNight** — 2026-08-18:
**Operator ruling — generated speech (2026-08-17):**

1. **Generated speech is admitted, in principle, as an explicit third speech source** alongside player-typed and author-written. NPC chat responders remain real future work in the V25 constellation, and 25.0's GDD doctrine text may name all three sources honestly. The category's rules — which NPCs may generate, what grounding they receive, how world-fact claims are constrained (the #34 authored-dialogue verification rule has no authoring time to attach to), internal marking of generated lines in the MC record — are this issue's design session, not decided today.
2. **Boundary ruled: sudo's voice is *not* in-world speech.** When sudo (#262) answers, that is the watcher talking — an out-of-world surface with a persona, not an NPC speaking in a room. It does not ride the say-color attributed-speech surface, does not implicate the Listening Model (§7.6), and does not wait on this issue's category rules. sudo's actual rendering (category, color, voice) is #262 design work.

Ruled in conversation with Claude while working the V25 handoff's design-question list (§6 item 9).


## Issue #268: MC agent runtime & operations: hosting, supervision, credentials, cost governance for the AI actor fleet

- State: open
- Author: KnightOfNight
- Labels: monitoring-and-command, V25
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-16 | Updated: 2026-08-27
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/268

### Body

## Summary

**Agent runtime and operations: where the AI actors live, and who keeps them alive.** Every MC actor issue (#262, #263, #265, #259) asks "which model, where does it run" individually; nobody owns the answer. This issue does.

Filed at operator direction, 2026-08-16.

## The premise

Operator direction during MC scoping: agents are **remote clients** — they attach over the MC egress like players attach to play. Inference load, API cost, and agent failures therefore never touch the game box. This issue is everything on the far side of that line.

## What it has to answer

- **Hosting.** Where agent processes run: a separate compose stack on another host, a cloud service, scheduled cloud agents, or several by actor type. The game's single-EC2 box is explicitly *not* the answer — the separation is the point. (Note #214, the AWS dev-migration plan, may reshape what hosts exist; these should be designed aware of each other.)
- **Supervision.** Restart-on-crash, hang detection, reconnect-with-resume (the egress cursor), and how a dead agent is noticed — by monitoring, not by a player wondering why the innkeeper went quiet. Sibling of #223 (uptime monitoring); an agent fleet multiplies what "up" means.
- **Credential custody.** Two kinds: the agent's **game identity** (its egress auth) and its **model API keys**. Both under the standing secrets-hygiene law — named, never printed, never committed; where they live per hosting choice.
- **Cost governance.** Per-agent budget caps, rate limits (per room / per player / per minute), and billing alarms. A chatty player talking to an AI NPC is a metered API call in a trench coat; the game must be able to bound the bill without the operator watching a dashboard.
- **Model selection.** Which model per actor shape — a pattern-watcher digest, an NPC holding conversation, and Sirius's whim are different jobs; pinning and upgrading models per actor is an ops surface.
- **Dev parity.** Playtests run on the dev stack — every actor needs a dev mode pointed at dev's egress, exercised in-release like everything else, before any prod attach.
- **Prod attach discipline.** An agent connecting to production is an outward-facing act; when and how agents are pointed at prod (and by whom) needs a stated rule, in the spirit of the existing deploy gates.

## Explicitly not this issue

- **#266 (the kill switch)** — its own high-priority issue; game-side, works even when everything here is on fire.
- **#267 (the egress contract)** — its own issue; this consumes it.
- **What any agent does** — the actor issues own their behavior.

## Relationships

#267 (transport in), #266 (the master lever), #262/#263/#265/#259 (the fleet this hosts), #223 (monitoring sibling), #214 (may change the host landscape), #261 (actuation rules the fleet must obey).

## Notes

Filed at operator direction, 2026-08-16. No milestone; grouping label `monitoring-and-command` per operator direction. Likely an action-item-shaped ticket under the v35 paradigm — built across releases, closed in an ops session when the arc completes.


### Comments (6)

**KnightOfNight** — 2026-08-18:
Classification ruled (2026-08-17, v35 litmus): **action item — never joins a milestone.** Runtime/hosting/supervision/credential/cost-cap work starts when sudo (#262) needs a home at 25.5 and outlives any single release. Slices ride briefs with ruling comments naming the carrier; ops closes at arc end.

**KnightOfNight** — 2026-08-22:
**Operator point of order (2026-08-22, V25.5 design session) — the agent-code home:**

`~/src/games-mvc-agents/` is a **temporary** home — it existed only to avoid disturbing the repo mid-release (V25.4). **All bot/agent code moves into the games-mvc repo** — nothing now, but very soon, probably when the sudo bot ships. In-repo layout, packaging, and dependency handling become design/brief work in this arc at that point.

(Cross-recorded on #279, whose "deliberately not checked in" status line this supersedes going forward.)


**KnightOfNight** — 2026-08-22:
Cross-ref: #282 filed from the V25.5 Brief 1 playtest — the door's `answer` delivery gate (#273: admins-only) must become per-agent context when this arc designs agent scopes. Operator direction recorded on #282: sudo answers admins only; Sirius (#259) answers anyone.


**KnightOfNight** — 2026-08-23:
**Operator rulings (2026-08-23, V25.6 design session) — v1 runtime shape for the sudo bot (this arc's 25.6 slice):**

1. **The bot is a standalone, detached process** on the operator's dev machine — plain Python, holding one authenticated WebSocket to the agent door, with a boring ops surface: start, stop, status, a log file. Launched detached (nohup/tmux-style) so its lifetime is independent of whatever shell started it.

2. **Supervision surface = any shell — explicitly including a Claude Code session via CC Remote Control.** A CC session on the bot host can start the bot, tail its log, diagnose, and restart it, and CCRC drives that session from browser/mobile anywhere — the operator's "monitor or restart wherever I am," with diagnosis capability SSH alone doesn't give. The session is remote hands, **not** a service manager: the bot never depends on a session being alive.

3. **Process supervision proper (auto-restart, boot persistence, hang detection) is deliberately deferred** to a later slice of this arc. v1 posture: operator starts it, any shell can inspect/restart it, and the kill switch (#266) remains the always-working safety backstop.

4. **Credential custody:** the model API key (`ANTHROPIC_API_KEY`) and the bot's game credentials live as named environment variables / operator-held config on the bot host — never committed, never printed (standing secrets law).

5. **Model selection is per-bot configuration** through the provider-agnostic brain interface ruled on #262; sudo v1 defaults to Sonnet 5 (`claude-sonnet-5`), future provider = Ollama.

6. **Cost governance v1:** per-request token usage logged from the API's `usage` stats; sudo's rate bound is its admin-only audience (no technical limiter in v1 — full ruling on #262); Sirius' limits are designed when Sirius is (cross-ref #259).


**KnightOfNight** — 2026-08-23:
**Repo move executed (operator-directed 2026-08-23, V25.6 design session):**

The agent-code home is now **`agents/`, a new top-level directory in games-mvc** — landed on `version_25_6` at 9f64cf5. Exactly as ruled:

- `mc_test_agent.py` and `mc_door_agent.py` **copied** in; the temporary `~/src/games-mvc-agents/` directory was touched not at all and remains intact.
- **venvs are not copied** (operator question, ruled in-session): a Python venv is machine-specific and non-portable by construction. Instead `agents/requirements.txt` carries the direct dependencies (`requests`, `websockets`; the 25.6 brief adds `anthropic`), and `agents/.gitignore` ignores `venvs/` so locally created venvs never enter git.
- **`.secrets/` copied and gitignored** — ignore rule was in place before the copy, and `git check-ignore` verified the credential file is invisible to git; only the four intended files (`.gitignore`, both scripts, `requirements.txt`) are tracked.

In-repo layout/packaging for the bot itself remains the 25.6 brief's work; this commit is the scaffold.


**KnightOfNight** — 2026-08-27:
**Arc status (2026-08-27, V25.8 design session, operator-confirmed): stays open as the runtime-and-ops action item** — v35 shape unchanged, never joins a milestone, ops closes at arc end. Reviewed against the shipped state: the v1 slices are done (#295 botctl, the agents/ repo home, credential custody, cost-governance v1, model selection, CCRC supervision surface), but the arc is not at end — process supervision proper (auto-restart, boot persistence, hang detection) remains deliberately deferred, Sirius-facing cost governance is unruled (#259), and #299 (rides V25.8) shows the ops surface still moving.


## Issue #282: Agent door: 'answer' delivery gate must be per-agent context, not verb-global — sudo answers admins only, Sirius answers anyone

- State: open
- Author: KnightOfNight
- Labels: monitoring-and-command
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-22 | Updated: 2026-08-27
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/282

### Body

## Observation (V25.5 Brief 1 playtest, 2026-08-22)

The agent door's `answer` action (shipped V25.5, #281) enforces the #273 delivery gate: the target must be a live `admins.shyland` member, `not-admin` otherwise. For the sudo bot (25.6, #262) this is never a limitation — `sudo` itself is admin-gated, so sudo's entire audience is admins by construction.

But `answer` is the door's only speaking action, and the gate makes it unusable for any player-facing bot. Sirius (#259, rare-violet talking color already ruled) is the concrete case: a bot meant to speak to ordinary players cannot deliver a single line through the door as shipped.

## Operator direction (stated in-session at filing, 2026-08-22)

> 'answer' is too generic to be limited to sudo responses, or we must allow 'answer' to work as appropriate in whatever the bot/agent's context is. sudo can only answer an admin, but Sirius can answer anyone.

I.e. the delivery gate should be **per-agent context**, not a property of the verb: sudo answers admins only; Sirius answers anyone. This points at the per-agent authorization scopes arc (#261/#268) — the natural home for "which audiences may this agent address," alongside talking-color assignment per agent.

## Scope note

Deliberately out of V25.5 (the brief carved per-agent scopes out as future arc work) and not a defect: `not-admin` for a non-admin target is the shipped, ruled behavior of #273. This ticket is the design question for a future session: generalize `answer`'s delivery gate to per-agent scope, or ship a differently-gated speaking action for player-facing bots.


### Comments (1)

**KnightOfNight** — 2026-08-27:
**Deferral note (2026-08-27, V25.8 design session):** the operator considered ruling this design-ahead in the 25.8 session and chose to defer — the per-agent answer-scope question stays open for the session that designs Sirius (#259), where a player-facing bot makes it concrete. Not in the `Version 25.8` milestone; no ruling recorded. (#261's arc-end assessment waits on this accordingly.)


## Issue #283: NPC first-contact greetings broadcast room-wide in second person — bystanders read the 'you' as addressed to them

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-22 | Updated: 2026-08-22
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/283

### Body

## Observation (V25.5 Brief 1 playtest, 2026-08-22, operator-reported)

Sharon-Love was admin-moved into Harley Stone's room (the new agent-door `move`). The room's NPCs fired their first-contact greetings at Sharon — and Harley saw every line too. Because the authored greeting lines speak in the second person, from Harley's point of view the dialogue reads as if it is addressed to *him*, even though he was not the one who arrived.

## Mechanics (diagnosed in-session)

Not door-specific and not new in V25.5 — walk-in parity was verified in the code: any first-contact room entry schedules greetings through the pending-dialogue machinery (`schedule_npc_greetings`), and the tick engine delivers **all** NPC dialogue via `broadcast_to_room` (`run_tick_engine.py`, the v23 #147 composer path). Room-audible NPC speech is by design (DD §13); the defect is the collision between that delivery and greeting lines authored in the second person — a bystander has no way to tell the "you" isn't them. The admin move merely made it easy to witness, since it can drop a first-contact player into an occupied room.

## Design question (for a design session to rule)

Options that have come up: address the target by name in the greeting line; render greetings per-recipient (second person to the target, third-person narration to bystanders); or re-author greeting pools to be perspective-neutral. Interacts with the speech/narration attribution rules (DD §13) and the pooled-speech law.


### Comments (0)

None.

## Issue #297: Curse system live loop is unbuilt: apply active_curse on equip, unequip handling, seedable curse effects, acquisition + identification paths (needed for new zones; rule with #80)

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-26 | Updated: 2026-08-26
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/297

### Body

## The gap

The curse system is deliberately half-built: the schema and containment rules shipped, but the live loop — the part where a curse actually *does something* — was never ruled or implemented. Operator direction (2026-08-26, V25.7 playtest conversation): **curses need to work for the new zones.**

## What exists today (wired and live)

- `ItemInstance.is_cursed`, `curse_identified`, and `active_curse` (nullable FK → `EffectInstance`)
- The effect vocabulary is ready: `EffectDefinition` / `EffectComponent` / `EffectInstance`, including a `curse_generic` component type in `COMPONENT_TYPE_CHOICES`
- Player unequip refusal on `is_cursed` (`_unequip_blocked_reason`) — fires regardless of identification
- The display law: curse hidden everywhere except `examine`, which reveals only when `is_cursed AND curse_identified`
- v25.7 (#287/#288) admin surface: `sudo` unequip bypasses the guard; `sudo` removal tears down `active_curse` (components + `EffectInstance` deactivated, `removed_by='item-removed'` — the curse ends with the item, operator-ruled)

## What does not exist (nothing does these)

- Applying the curse's effect when a cursed item is equipped (no code path populates `active_curse` — admin-set data only, verified by grep at v25.7 pre-flight)
- Handling the effect on unequip (suspend? persist? — needs a ruling; note the current unequip-refusal guard means player-side unequip of a cursed item shouldn't normally happen at all)
- Any curse `EffectDefinition` in seed data
- Any in-game acquisition path (no cursed items drop; `is_cursed` is admin-set)
- Any identification mechanic (nothing ever sets `curse_identified`)

## Design notes for the ruling session

- Rule alongside **#80** (knowledge by holding) — curse identification and item identification are adjacent systems and should be coherent.
- Z02 (Ashenveil Cathedral, gothic horror) is the obvious first curse habitat — this likely belongs to a zones-major arc rather than the V25 MC stream.
- The v25.7 admin tooling (`sudo` unequip/removal, `edit_item`) is the operational escape hatch and already handles the containment side; the live loop is the missing half.

Refs: #80 (identification redesign), #287/#288 (v25.7 admin curse handling).


### Comments (0)

None.

## Issue #315: Door durability edit can silently break a non-wearing item: 0 sets is_broken (combat-honored) with no display cue and no in-game repair path

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-30 | Updated: 2026-08-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/315

### Body

Found during the V25.12 Brief 1 playtest (the durability-posture release, #311/#312/#314), instance-side sibling of that family.

The agent door's `durability_current` edit maintains `is_broken = (durability_current == 0)` unconditionally — including on an item whose definition is non-wearing (`takes_durability_loss=False`). The result is an item that is:

- **combat-disabled for real**: `is_broken` is honored regardless of definition posture — the item contributes nothing to TAV (`total_armor_value` excludes broken instances) and drops out of the composite strike;
- **visually indistinguishable from healthy**: the Details durability cell, the `— N% durability` / `— BROKEN` suffix, and the error voice are all gated on the wearing definition, so nothing renders;
- **unrepairable by any player path**: vendor repair and repair kits both filter on `takes_durability_loss=True` — recovery is another door edit (or admin ORM), nothing in-game.

Reaching it requires an admin (or a bot driving the door) to raw-set durability 0 on a non-wearing item — bad input on an admin tool — but it is a silent, invisible, in-game-unrecoverable state: exactly the landmine shape the durability-posture invariant exists to eliminate. Admins deserve the same protection as any other operator (operator direction, 2026-08-30).

Possible shapes (design session to rule): refuse `durability_current` edits on non-wearing definitions entirely (the value is inert dormant data for them — nothing reads it); or refuse only 0; or decouple `is_broken` from the edit when the definition doesn't wear. Nonzero values on non-wearing items are harmless today (penalty short-circuits on the flag, display gated, repair filtered).

_Filed from the V25.12 Brief 1 implementation session during operator playtest._


### Comments (0)

None.

## Issue #316: plan on adjusting big numbers to use shorthand

- State: open
- Author: KnightOfNight
- Labels: output
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-30 | Updated: 2026-08-30
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/316

### Body

As player level increases, some numbers on screen get big — best examples are vitality and longevity. Format those numbers with K or M shorthand as needed, one decimal point to start. When a number is less than 1K, show the whole number instead. Examples: 26.5K / 26.5K, or 15.7K / 26.5K, or 315 / 26.5K.

---
_Filed via sudo (in-game) by Sharon-Love, 2026-08-30T18:51:45Z._

### Comments (0)

None.

## Issue #317: Sudo bot: file_issue cannot apply labels — extend the filing vocabulary to carry operator-named labels

- State: open
- Author: KnightOfNight
- Labels: triaged, monitoring-and-command
- Milestone: Version 25.14
- Assignees: KnightOfNight
- Created: 2026-08-30 | Updated: 2026-09-01
- Blocked by: none
- Blocks: #320
- URL: https://github.com/KnightOfNight/games-mvc/issues/317

### Body

Operator request (2026-08-30, during V25.12 Brief 1 session): the sudo bot's `file_issue` action cannot apply labels to the issues it files — filed issues are title + body + provenance footer + assignee only.

The no-labels shape was deliberate at #301 ("thin is doctrine; triage fattens" — v25.10), so this is a design-session ruling to extend it: let the admin name labels during the Q&A draft and have `file_issue` pass them to the GitHub API (machinery, like the assignee — never model-invented). Open questions for the ruling: whether to restrict to an allowlist (the v30 label model's state labels — `bug`, `output`, `errata`, etc. — versus grouping labels, which are design-session calls), and whether the read-back-before-filing confirm covers the labels too.

_Filed from the V25.12 Brief 1 implementation session on operator direction._


### Comments (1)

**KnightOfNight** — 2026-09-01:
**Ruling (V25.14 design session, 2026-09-01):**

- Joins **Version 25.14** as a dependency of founding ticket #320.
- **The label vocabulary is ruled open, not allowlisted (operator):** the bot pulls the repo's current label list live (`GET /repos/{owner}/{repo}/labels`) and accepts **any existing label except `triaged`** — cold-start-ready is a design-session act, never filed in. Grouping and state labels alike can come up at filing time; the live list is the vocabulary.
- **The bot never creates or updates labels themselves.** Label CRUD stays human — the bot applies existing labels only.
- Labels are named by the admin during the Q&A draft and **validated against the fetched list at draft time** — an unknown name or `triaged` draws a legible refusal there, not at filing.
- **The read-back covers labels** and the explicit-yes gate covers the whole draft including them; the **receipt reports the labels actually applied, taken from the API response** (#306 — never model-typed).
- Labels remain machinery-applied like the assignee — the model never invents them; the thin-filing doctrine (#301) otherwise stands.


## Issue #320: Agent door / sudo bot has no currency actions — add full copper management (grant and deduct)

- State: open
- Author: KnightOfNight
- Labels: triaged, monitoring-and-command
- Milestone: Version 25.14
- Assignees: KnightOfNight
- Created: 2026-09-01 | Updated: 2026-09-01
- Blocked by: #317
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/320

### Body

Found during the V25.13 Brief 1 playtest (2026-08-31), while stocking a character for over-capacity testing.

The sudo bot (and the agent door behind it) has no currency-grant capability. Its item powers are `gift` and `create_artifact` only — asked to hand a character copper, the bot correctly reports it has no tool for it:

> sudo: I don't have a copper-grant tool — my item powers are gift and create_artifact, not currency. I can't hand out copper directly; that has to come through in-game means like selling or quests.

Currency is freely transferable by design (unlike items, which soulbind), and super-user gifting of items is already a settled capability — a copper grant is the natural sibling. Without it, an admin who needs to fund a character (playtest stocking, mitigation, compensation) has to route through the Django admin's raw `Character.copper` field, which bypasses the door's audit trail.

Likely shape (design session to rule): a door action (e.g. `grant_copper`) with target + amount through the door's existing audited-write machinery, mirrored into the bot's tool schema per the v25.12 doctrine that the bot's schemas mirror the door's param shapes.

Workaround used today: operator sets copper via the admin console and buys items in-game.


### Comments (2)

**KnightOfNight** — 2026-09-01:
**Ruling (V25.14 design session, 2026-09-01):**

- **Founding ticket for Version 25.14** (milestone created this session). #317 rides the release as a dependency — same door/bot admin-capability surface, found in successive playtests.
- **Scope expanded by operator ruling: full copper management, not grant-only.** The door gains both directions — adding and removing copper. Title updated to match.
- The ruled shape (GDD §10 text lands on `version_25_14` with the pending-implementation marker; the brief follows):
  - **Two door actions, verb-pair style** (the `equip_item`/`unequip_item` pattern): **`grant_copper`** and **`deduct_copper`** — target + amount (positive integer), server-validated, each emitting its own MC record attributed to the acting agent account. No signed-amount single action.
  - **All math through `apps.shyland.currency`** (standing law). Deduct catches the insufficient-funds `ValueError` and refuses legibly with the shortfall context — report, never clamp, never partial.
  - **No upper cap** beyond positive-integer validation: the admin gate plus the audit trail is the control, and currency is freely transferable by design.
  - **Transparent narration per the #261 ruling:** the recipient sees the grant in loot-color (sibling of the gift giving line) and the deduction in value-color (neutral admin-action narration, the `move` pattern); every player-facing amount renders through the tier formatter.
  - **Bot tools mirror the door param shapes** (v25.12 doctrine). Immediate actions like `gift` — no draft/confirm gate; receipts deterministic and machinery-composed (#306).


**KnightOfNight** — 2026-09-01:
**Ruling amendment (V25.14 design session, 2026-09-01) — the amount shape:**

The "target + amount (positive integer)" clause above is refined by operator ruling: **the denomination is required — a bare number is not actionable.** "give player 100" is refused with a which-currency question; "give player 100 gold" acts.

- Both actions take **denominated fields** — `platinum` / `gold` / `silver` / `copper`, each an optional positive integer, at least one required — and the door sums them mechanically via the existing `currency.to_copper()`. The model never does currency arithmetic and never assumes a denomination (the #306 fabrication surface closed at the schema).
- Confirmed alongside: the bot gains a **programmatic label-list tool** for #317 — the live repo label list fetched bot-side (`triaged` filtered out), so draft-time validation and read-back work from data, with machinery re-validation at filing.


## Issue #321: Bulk buy/sell at admin-scale quantities takes minutes with zero output — sell is O(n) transactions, buy O(qty) serial INSERTs

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-09-01 | Updated: 2026-09-01
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/321

### Body

Found during the V25.13 Brief 1 playtest (2026-08-31): stocking and unstocking a character at admin scale (~11,000 items) makes `sell all <noun>` and large `buy <N> <item>` take minutes, with no output at all until the whole operation completes — the game appears hung.

Diagnosis (against `version_25_13` @ f24a385):

**Sell — O(n) transactions.** `cmd_sell`'s bulk arm (`consumers.py:2410`) awaits `do_sell` per item; each `do_sell` (`consumers.py:4497`) is its own `database_sync_to_async` thread hop plus its own transaction: `SELECT FOR UPDATE` on the character row, copper `UPDATE`, instance `DELETE`, commit. 11,000 items ≈ 11,000 transactions / ~45,000 sequential SQL round trips. All aggregated output lines compose only after the loop, so nothing renders while it grinds and the consumer processes no other input.

**Buy — one transaction, O(qty) serial INSERTs.** `do_buy` (`consumers.py:4464`) is correctly atomic (whole quantity succeeds or fails as one, #22), but creates instances one `generate_item_instance()` + `item.save()` at a time — thousands of serial INSERTs, holding `SELECT FOR UPDATE` locks on the vendor entry and character row for the duration. No `bulk_create` today because each instance rolls its own stats at generation, but generation could be split from persistence.

Context: per-item compensated disposal on sell is deliberately safe (a crash mid-sale loses nothing), and both paths are fine at the pool sizes normal play produces — carry capacity keeps legitimate inventories in the low hundreds. The pain is admin-scale stocking (playtest prep, the #275 over-capacity work), roughly two orders of magnitude off the designed scale.

Possible directions (design session to rule): batch the bulk-sell arm (one transaction per aggregate group: summed price, one copper update, one bulk delete), batch buy's persistence (`bulk_create` of pre-generated instances), and/or emit progress output during long operations. A cheap cap ("vendors won't handle more than N at once") is also a legitimate answer.


### Comments (1)

**KnightOfNight** — 2026-09-01:
Go with the cheap cap.  


## Closed Issues — Summary Table

| # | Title | Author | Labels | Closed |
|---|---|---|---|---|
| 319 | pickup/buy count equipped gear against carry capacity — load-counting basis disagrees with loot, the inventory header, and the bag guard | KnightOfNight | bug, triaged | 2026-08-31 |
| 275 | Unequipping +STR gear silently strands the character over carry capacity, blocking loot/pickup/buy | KnightOfNight | bug, emergent, triaged | 2026-08-31 |
| 314 | Agent door: durability_current edit accepts fractional values — wear is integral and seed bands cover integers only, so 0.5 draws the 1.0 no-band penalty | KnightOfNight | bug, triaged, monitoring-and-command | 2026-08-30 |
| 312 | Admin cannot re-save ItemDefinitions with legitimately-empty JSON lists: durability_table/primary_stats/secondary_stat_pool lack blank=True | KnightOfNight | bug, triaged | 2026-08-30 |
| 311 | Empty durability_table with takes_durability_loss=True: penalty lookup falls through to 1.0 — pristine items render yellow and fight fully penalized | KnightOfNight | bug, triaged | 2026-08-30 |
| 308 | sudo bot: unmarked delivery-claim fabrications on zero-tool turns — no machine-detectable signature; needs a ruling (deterministic routing / zero-tool bounce / tool_choice) | KnightOfNight | triaged, monitoring-and-command, V25 | 2026-08-30 |
| 309 | test issue filed by sudobot | KnightOfNight |  | 2026-08-30 |
| 306 | sudo bot: everything the bot delivers should render deterministically — machinery composes and the game renders all data-shaped output; model prose is commentary only | KnightOfNight | triaged, monitoring-and-command | 2026-08-28 |
| 305 | sudo bot: the conversation store records model prose as truth — a false action claim poisons the thread (persist receipts with the answer) | KnightOfNight | triaged, monitoring-and-command | 2026-08-28 |
| 304 | Two bots on one target: per-checkout pidfiles cannot see a same-target bot running from another checkout — enforce a per-(bot, target) singleton | KnightOfNight | triaged, monitoring-and-command | 2026-08-28 |
| 301 | sudo bot: file GitHub issues from in-game — Q&A gathering like the artifact flow, filed on explicit confirm | KnightOfNight | triaged, monitoring-and-command | 2026-08-28 |
| 302 | sudo bot: the model must never invent a value it should read from the database — make receipts structural, not behavioral | KnightOfNight | emergent, triaged, monitoring-and-command | 2026-08-28 |
| 300 | Agent door: time-windowed MC-history query — generic game-log search over the durable record (MCEvent) | KnightOfNight | triaged, monitoring-and-command | 2026-08-27 |
| 299 | botctl: one pidfile/log/conversation store per checkout — dev and prod bots can't coexist from main, and status/stop are target-blind | KnightOfNight | bug, triaged | 2026-08-27 |
| 296 | sudo inventory reports are unreadable comma prose — answer path needs a game-rendered report delivery (leader line in sudo voice + the shared inv/equip item-line rendering) | KnightOfNight | triaged, monitoring-and-command | 2026-08-27 |
| 290 | Agent door: no room-directory query — rooms unreachable except through characters | KnightOfNight | triaged, monitoring-and-command | 2026-08-27 |
| 294 | sudo bot: durable admin-taught memory — named waypoints ('send shy-guy into battle') and item bundles ('the badass armor set') outlive conversation expiry | KnightOfNight | triaged, monitoring-and-command | 2026-08-27 |
| 286 | GDD erratum: §2.11 "three ways out" undercounts — the shard relay makes four | KnightOfNight | errata | 2026-08-26 |
| 295 | agents/: adopt the operator's bot-management scripts (sudo-bot.sh / test-sudo-bot.sh) into the repo — one parameterized script, bash standards, status passthrough | KnightOfNight | triaged | 2026-08-25 |
| 292 | sudo bot: trailing slash on --url breaks login (double-slash POST draws a 302, looks like a credential failure) — normalize base_url with rstrip('/') | KnightOfNight | triaged | 2026-08-25 |
| 289 | Agent door: no mutation action — created artifacts (and items generally) cannot be edited | KnightOfNight | triaged, monitoring-and-command | 2026-08-25 |
| 288 | Agent door: no targeted equip/unequip actions — strip is all-or-nothing, dress only restores the snapshot | KnightOfNight | triaged, monitoring-and-command | 2026-08-25 |
| 293 | Agent door: no character-inventory query — carried items and equipped gear invisible to sudo (read-side prerequisite for #287/#288) | KnightOfNight | triaged, monitoring-and-command | 2026-08-25 |
| 287 | Agent door: no item-removal action — sudo can gift but not take | KnightOfNight | triaged, monitoring-and-command | 2026-08-25 |
| 284 | nginx login rate limit (zone=login 5r/m, burst=3) blocks agent-testing and bot reconnect login patterns — proposal: burst=10, rate unchanged | KnightOfNight |  | 2026-08-24 |
| 279 | MC test-agent client: operator-side script that connects to the egress and tails the event stream (CLI: URL, username, password) | KnightOfNight | monitoring-and-command | 2026-08-24 |
| 262 | sudo AI watcher: an AI agent on the receiving end of sudo — reads the MC stream, and may or may not be allowed to answer | KnightOfNight | monitoring-and-command, V25 | 2026-08-24 |
| 273 | MC stream carries no command outcome — readers infer refusals from adjacent out records (sudo observation) | KnightOfNight | monitoring-and-command, V25 | 2026-08-22 |
| 281 | V25.5 founding ticket: the MC agent door — query, action, and answer vocabularies (game-side actuation infrastructure) | KnightOfNight | monitoring-and-command, V25 | 2026-08-22 |
| 277 | MC persister: XREADGROUP BLOCK 5000 races redis-py 8.1 default socket_timeout=5s — idle-cycle reconnect churn | KnightOfNight | bug, monitoring-and-command | 2026-08-21 |
| 266 | MC kill switch: a single lever that silences every AI actor at once — ships no later than the first live actor (HIGH PRIORITY) | KnightOfNight | monitoring-and-command, V25 | 2026-08-21 |
| 267 | MC egress: how remote consumers attach — Streams inside the trust boundary, WebSocket across it (auth, backpressure, resume) | KnightOfNight | monitoring-and-command, V25 | 2026-08-20 |
| 33 | Shyland: persist detailed combat logs for balance analysis | KnightOfNight | monitoring-and-command, V25 | 2026-08-19 |
| 272 | Ticker presence reader hardcodes Redis endpoint — second #271 site (run_tick_engine._online_character_pks) | KnightOfNight | emergent, monitoring-and-command, V25 | 2026-08-19 |
| 271 | Presence Redis client hardcodes its endpoint — bypasses REDIS_HOST, blocker to MC configurable-endpoint provision | KnightOfNight | monitoring-and-command, V25 | 2026-08-18 |
| 37 | MC monitoring: universal event logging — every command, every output, every event | KnightOfNight | monitoring-and-command, V25 | 2026-08-18 |
| 269 | V25.0 founding ticket: MC (Monitoring and Command) — the major design pass and version opening | KnightOfNight | monitoring-and-command, V25 | 2026-08-18 |
| 264 | Terminology: the firehose is now Monitoring and Command (MC) — sweep forward-looking doc references | KnightOfNight | monitoring-and-command, V25 | 2026-08-18 |
| 260 | MC chat policy: GDD §7.1 and §10.5 contradict — rule chat persistence, privacy, and retention before MC ships | KnightOfNight | monitoring-and-command, V25 | 2026-08-18 |
| 258 | Sanctioned read-only daemon inspection for production (docker system df & co) — the #248-shaped gap on the daemon face | KnightOfNight | deployments | 2026-08-16 |
| 257 | V24.31 sweep: prod's --keep-storage is a deprecated client-side alias, not a daemon requirement — divergence rationale is wrong and the prod line will break silently | KnightOfNight | V24, deployments | 2026-08-16 |
| 255 | Erratum: architecture doc §2.2 Makefile table documents a nonexistent 'make reset' and omits the entire deployment/guard surface | KnightOfNight | triaged, errata, V24, deployments | 2026-08-16 |
| 205 | Deploy targets gain a build-exhaust sweep (image + builder prune) — stop the ~500MB/release root-volume growth | KnightOfNight | triaged, V24, deployments | 2026-08-16 |
| 251 | All config command setters should write both the cached attribute and the DB row | KnightOfNight | triaged, commands | 2026-08-15 |
| 252 | Briefs assert unverified facts about existing code — no gate checks a brief for technical coherence | KnightOfNight |  | 2026-08-15 |
| 249 | make verify-prod: sanctioned read-only production verification target (posture-setting contract of the #187 sibling family; fixed manage.py commands + rollback guard) | KnightOfNight | deployments | 2026-08-15 |
| 250 | _set_echo_mode assigns the wrong cached attribute — echo writes to self.character.show_timestamps | KnightOfNight | bug, emergent, triaged, V24, commands | 2026-08-15 |
| 235 | New player setting: 'plunder' (default off) — auto-loot rights-held corpses at combat end | KnightOfNight | triaged, V24, commands | 2026-08-15 |
| 248 | Closeout tail: a brief can specify a production-side verification step that no session can run (read-only prod queries have no sanctioned path) | KnightOfNight | deployments | 2026-08-15 |
| 246 | Playtest checklists: "admin-gift" is ambiguous where a step tests a generation-path guard (Django admin bypasses it by design) | KnightOfNight | errata | 2026-08-15 |
| 245 | Tier-material ladder: rule its full extent (eight rungs, copper -> sphaerium) and its unbounded terminal rung | KnightOfNight | triaged, V24, itemization | 2026-08-15 |
| 211 | Silver accessory tier: Mk 2 jewelry needs the tier-material ladder extended (silver definitions + Mk-mismatch ruling) | KnightOfNight | triaged, V24 | 2026-08-15 |
| 234 | Character deletion: items are silently orphaned (owner SET_NULL) — rule item disposition + hard-vs-soft delete model | KnightOfNight | triaged | 2026-08-14 |
| 242 | Architecture doc §7 erratum: 'no Convergence NPC has VendorEntry rows or is_repairer set' — false since ~v20 (ring carts vend, Morra repairs) | KnightOfNight | errata | 2026-08-14 |
| 240 | GDD §12 errata: stale "no Convergence commerce" note (shipped #95) + leftover "Document version 22.0" footer | KnightOfNight | errata | 2026-08-14 |
| 30 | Travel network: should checkpoints (shards) also be travel senders? | KnightOfNight | V24, travel | 2026-08-13 |
| 38 | Obelisk attunement: player-set home spawn at checkpoint shards | KnightOfNight | V24, travel | 2026-08-13 |
| 238 | GDD §2.9 erratum: "35-room ring street" — the shipped ring is 40 rooms (v20 Brief 1, #43) | KnightOfNight | errata | 2026-08-13 |
| 231 | GDD §4 erratum: tick-suffix example "(Acuity 1.15)" — a suffix can never carry an exact x.x5 value | KnightOfNight | errata | 2026-08-13 |
| 95 | the ring needs an area | KnightOfNight | triaged, V24, travel | 2026-08-13 |
| 41 | Lock battle-zone access until a new player has visited all of The Convergence | KnightOfNight | triaged, V24, travel | 2026-08-13 |
| 188 | Process proposal: merged design+implementation session per point release, with automated playtesting (future Instructions v32) | KnightOfNight | deployments | 2026-08-12 |
| 233 | Readability pass: raise the default type scale and fix below-AA contrast (umbrella for #221 + #222) | KnightOfNight | triaged, output | 2026-08-12 |
| 222 | Raise the game's default font size a couple of pitch points (base 14px + a scattered hardcoded scale) | KnightOfNight | triaged, output | 2026-08-12 |
| 221 | Character creation screen: font color too hard to read (muted text ~3.2:1 contrast, below AA) | KnightOfNight | triaged, output | 2026-08-12 |
| 215 | Bags don't do enough: flat carry_bonus is noise against the STR-scaling capacity base (Mk 2 bag = +4.3% at level 17) | KnightOfNight | triaged, game-balance | 2026-08-12 |
| 225 | Acuity displays truncate to one decimal — 1.15 renders as 1.1; need two decimals or more | KnightOfNight | triaged, output | 2026-08-12 |
| 125 | player macro/alias system | KnightOfNight |  | 2026-08-11 |
| 201 | Flame Projector / Dart Caster ship at default base_value 1 — pricing unruled | KnightOfNight | triaged, V24 | 2026-08-11 |
| 206 | 'repair' command has no path to a carried Repair Kit — field repair is 'use' only, vendor repair needs an NPC | KnightOfNight |  | 2026-08-11 |
| 203 | Design: examine's 'Note: … you may drop it' line — weird on ground items, redundant with the flag block, key/value inconsistent | KnightOfNight | triaged, V24 | 2026-08-11 |
| 218 | Zombie combat sessions: all NPCs dead but session stays active — loot blocked 'in combat'; stale sweep can't reap (engine refreshes last_tick_at unconditionally) | KnightOfNight | bug, triaged | 2026-08-11 |
| 142 | Finish the acuity design: in-combat drift is unruled | KnightOfNight | triaged, V24, game-balance | 2026-08-11 |
| 105 | Elite even-level −5% hit calibration drift (rounding parity) | KnightOfNight | triaged, V24, game-balance | 2026-08-10 |
| 208 | 'inv' still shows equipment and wallet — trim to inventory only ('equip' and 'wallet' own those views now) | KnightOfNight | triaged, output, V24 | 2026-08-08 |
| 26 | Boss and elite kills pay flat XP — no tier multiplier | KnightOfNight | triaged, V24, game-balance | 2026-08-08 |
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
