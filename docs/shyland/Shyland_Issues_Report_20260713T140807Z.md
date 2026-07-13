# Shyland Issues Report

- Generated: 20260713T140807Z
- Repo: KnightOfNight/games-mvc
- Open issues: 41
- Closed issues: 1
- Dependency data: available

## Open Issues — Summary Table

| # | Title | Labels | Milestone | Updated |
|---|---|---|---|---|
| 1 | Location Bar Updates - Complete Breadcrumb Trail by Name |  | Version 20 | 2026-07-12 |
| 2 | Right Pane Design |  | Version 20 | 2026-07-12 |
| 3 | New Command: loot all |  | Version 20 | 2026-07-12 |
| 4 | Build Zone: Ashenveil Cathedral (Z02) |  | Z02 - Ashenveil Cathedral | 2026-07-12 |
| 5 | Build Zone: The Neon Sprawl (Z03) |  | Z03 - The Neon Sprawl | 2026-07-12 |
| 6 | Build Zone: The Blasted Flats (Z04) |  | Z04 - The Blasted Flats | 2026-07-12 |
| 7 | Build Zone: The Iron Deeps (Z06) |  | Z06 - The Iron Deeps | 2026-07-12 |
| 8 | Build Zone: The Pale Shore (Z07) |  | Z07 - The Pale Shore | 2026-07-12 |
| 9 | Build Zone: The Wastelands (Z08) |  | Z08 - The Wastelands | 2026-07-12 |
| 10 | Transactional email via Postmark (password resets) |  |  | 2026-07-12 |
| 11 | Account onboarding via unusable password + reset link (no temp passwords) |  |  | 2026-07-12 |
| 12 | Two-factor authentication via TOTP (django-otp) |  |  | 2026-07-12 |
| 13 | Combat Messages Colors |  | Version 20 | 2026-07-12 |
| 14 | Look-Command Output Sections |  | Version 20 | 2026-07-12 |
| 15 | Show Commands in Output Window for Context |  | Version 20 | 2026-07-12 |
| 16 | Change Description and Output to be Different Panes |  | Version 20 | 2026-07-12 |
| 17 | New NPC Spawn Doesn't Agro Immediately | bug |  | 2026-07-11 |
| 18 | Animal Hides Don't Stack in Inventory | bug |  | 2026-07-13 |
| 19 | Automatic command completion |  | Version 20 | 2026-07-13 |
| 20 | Command 'loot all' throws hidden unhandled exception and disconnects player websocket | bug | Version 20 | 2026-07-12 |
| 21 | New command: sell all |  | Version 20 | 2026-07-13 |
| 22 | Command nouns and verbs: allow better item references, allow plural references |  | Version 20 | 2026-07-13 |
| 23 | Leaving a room by cardinal direction command does not end combat like 'flee' does. | bug | Version 20 | 2026-07-13 |
| 24 | NPC display grammar: article stacking in combat messages |  | Version 20 | 2026-07-13 |
| 25 | Bosses do not heal when the player disengages | bug |  | 2026-07-12 |
| 26 | Boss and elite kills pay flat XP — no tier multiplier |  |  | 2026-07-12 |
| 27 | Research: passive regen ticks landing after combat engagement |  |  | 2026-07-12 |
| 28 | Corpse decay and empty-loot messaging is noisy and misleading |  | Version 20 | 2026-07-13 |
| 29 | Block looting (and related inventory commands) during combat |  |  | 2026-07-13 |
| 30 | Travel network: should checkpoints (shards) also be travel senders? |  |  | 2026-07-12 |
| 31 | Shyland: richer live connection status indicator (beyond static "Connected to Shyland") |  | Version 20 | 2026-07-13 |
| 32 | Shyland: output messages need timestamps and guaranteed ordering |  | Version 20 | 2026-07-12 |
| 33 | Shyland: persist detailed combat logs for balance analysis |  | Firehose Logging | 2026-07-12 |
| 35 | Map system backend: MapFrag derivation, exit boundary flags, map data payload |  | Version 20 | 2026-07-13 |
| 36 | Map system client: right-pane map rendering (node-and-line, fog-of-war) |  | Version 20 | 2026-07-13 |
| 37 | Universal event logging (firehose): every command, every output, every event |  | Firehose Logging | 2026-07-12 |
| 38 | Obelisk attunement: player-set home spawn at checkpoint shards |  |  | 2026-07-12 |
| 39 | Output colorization: section header labels ('Exits:', 'Who's here?', 'What's here?') should share one color |  | Version 20 | 2026-07-12 |
| 40 | Free repair messages repeat too often (Morra example) — research spike into other duplication cases |  |  | 2026-07-12 |
| 41 | Lock battle-zone access until a new player has visited all of The Convergence |  |  | 2026-07-12 |
| 42 | Audit: intra-MapFrag spatial consistency of The Convergence and Z01 room graphs |  | Version 20 | 2026-07-13 |

## Open Issues — Full Detail

## Issue #1: Location Bar Updates - Complete Breadcrumb Trail by Name

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-12
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/1

### Body

The location bar should always show Zone: (Area:) Room.  Values are colon separated.

Area is optional and may not always appear.

Zone name should be colored in the Zone's theme color.

Area color should be apropos to the area itself. Gray mountains, blue with ocean, that kind of thing. 

Room should be white.

"White" does not necessarily mean #FFFFFF.

Color will be a much wider palate than just red, green, blue.  We'll be able to use many different shades across #000000 to #FFFFFF. We must be cautious, not to make anything too dark against the background.

Any zone, area, or room information in the main output window will be colored the same as the breadcrumbs.


### Comments (0)

None.

## Issue #2: Right Pane Design

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-12
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/2

### Body

Map. 

Enemy stats. 

Player effects sent and received. 

### Comments (1)

**KnightOfNight** — 2026-07-12:
Map system issues filed: backend #35, client #36. The client issue widens the right pane for a square map area — the right-pane layout design here must account for it.

## Issue #3: New Command: loot all

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-12
- Blocked by: #22
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/3

### Body

Expectation: all available loot will be picked up by the player; each looted item will be listed. Usual messaging if there is nothing at all to loot.

### Comments (1)

**KnightOfNight** — 2026-07-12:
Blocked by #22: the "all" grammar is defined there, once, for the whole command family. Also see #20 — typing this not-yet-implemented command currently kills the websocket; the dispatch guard there must land regardless of when this command does.

## Issue #4: Build Zone: Ashenveil Cathedral (Z02)

- State: open
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

## Issue #13: Combat Messages Colors

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: none
- Created: 2026-07-11 | Updated: 2026-07-12
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/13

### Body

Combat Messages should be different colors.

There should be different shades of red for different levels of hit.

A miss should be gray.

Consider adding arrows showing the direction of the attack. A hit from an NPC you can start the line of text with an arrow pointing left. A hit from a player can end with a arrow pointing right.

### Comments (0)

None.

## Issue #14: Look-Command Output Sections

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-12
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/14

### Body

Who's here?

What's here?

Those sections will appear newline separated after the room information.

Exits: north, south.

Who's here?

Maro the Mender is here.
Essa the Trader is here.

What's here?

a Verdant Shard is here.

### Comments (1)

**KnightOfNight** — 2026-07-12:
Color requirement filed as #39: the "Who's here?" and "What's here?" labels defined here should match the color of "Exits:". This issue defines the section structure; #39 rules the color consistency across those labels.

## Issue #15: Show Commands in Output Window for Context

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: none
- Created: 2026-07-11 | Updated: 2026-07-12
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/15

### Body

"You don't see that here." by itself loses context.

Print player commands in the output window.

### Comments (0)

None.

## Issue #16: Change Description and Output to be Different Panes

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: none
- Created: 2026-07-11 | Updated: 2026-07-12
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/16

### Body

The scrolling output pane should be a separate area than the pane that holds room description, who's here, what's here, etc.


### Comments (0)

None.

## Issue #17: New NPC Spawn Doesn't Agro Immediately

- State: open
- Labels: bug
- Milestone: none
- Assignees: none
- Created: 2026-07-11 | Updated: 2026-07-11
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/17

### Body

Player standing in a room with two agro spiders.

Kills both.

One spider respawns but is listed as green in 'look'.

Leave room, return to room, spider is listed as red and agro's.

### Comments (1)

**KnightOfNight** — 2026-07-11:
Additional labels may apply.

## Issue #18: Animal Hides Don't Stack in Inventory

- State: open
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

## Issue #19: Automatic command completion

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: none
- Created: 2026-07-11 | Updated: 2026-07-13
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/19

### Body

Typing ise healing draught is too hard. I can't type use draught. I can type use healing. I'd like to be able to type use space H tab.

I think other commands could benefit from this.

### Comments (0)

None.

## Issue #20: Command 'loot all' throws hidden unhandled exception and disconnects player websocket

- State: open
- Labels: bug
- Milestone: Version 20
- Assignees: none
- Created: 2026-07-12 | Updated: 2026-07-12
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/20

### Body

## Summary

Typing `loot all` (a command that does not exist yet — see #3) causes a hidden unhandled exception server-side and disconnects the player's websocket. The player sees no error output; the connection simply drops.

## Two bugs in one

1. **The trigger:** something in command parsing or `cmd_loot`'s argument handling raises on the argument `all` instead of producing a normal "you can't do that" message.
2. **The structural bug (the important one):** an unhandled exception inside a command handler kills the entire websocket connection. No single command handler bug should ever be able to disconnect a player. Command dispatch (`receive_json`) needs a catch-all guard: log the traceback server-side, send the player a generic error line (category `error`), keep the connection alive.

Fixing #3 (implementing `loot all`) would hide the symptom without fixing bug 2. The dispatch guard must land regardless.

## Repro

1. Stand in a room with (or without) a corpse.
2. Type `loot all`.
3. Websocket disconnects; client shows connection lost; no error message is delivered.


### Comments (1)

**KnightOfNight** — 2026-07-12:
Live repro not attempted in this session (dev stack unavailable). Traceback to be captured at implementation time — the fix (dispatch-level guard) does not depend on the specific exception.

## Issue #21: New command: sell all

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: none
- Created: 2026-07-12 | Updated: 2026-07-13
- Blocked by: #22
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/21

### Body

Expectation: with no arguments, will respond with usual messaging asking what the player wants to sell. With arguments the player will sell all copies of an item they are carrying.

Example: sell all animal hide


### Comments (1)

**KnightOfNight** — 2026-07-12:
Blocked by #22: the all/plural/quantity grammar is defined there, once, for the whole command family (see also #3).

## Issue #22: Command nouns and verbs: allow better item references, allow plural references

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: none
- Created: 2026-07-12 | Updated: 2026-07-13
- Blocked by: none
- Blocks: #3, #21
- URL: https://github.com/KnightOfNight/games-mvc/issues/22

### Body

Example commands that do not work...

sell hide

sell carapace

buy draught

Expected commands that should work...

sell hide
sell all hides
sell carapace
sell all carapaces

buy draught
buy 10 draughts
buy 25 healing draughts

Check all commands for the normal naming ambiquities.

### Comments (2)

**KnightOfNight** — 2026-07-12:
Consolidation: this issue is the foundation of the command-grammar family. #3 (loot all) and #21 (sell all) are now blocked by it — both need the all/plural/quantity grammar defined once, here, rather than implemented per-command. #18 (stacking) interacts: whether hides stack changes what "sell all hides" means, so the two designs should be checked against each other. One design pass should cover this whole family.

**KnightOfNight** — 2026-07-13:
V20 planning ruling: this issue ships in Version 20 (milestone added).

Grammar semantics ruled stacking-agnostic: 'all <noun>' and quantity references resolve over the set of matching item instances in the character's inventory, regardless of whether those instances are displayed as a stack. 'sell all hides' means every hide instance carried, whether inventory shows 'Animal Hide (x7)' or seven separate lines.

Consequence: this design has NO dependency on #18 (stacking). #18 is deferred and becomes a pure display/inventory-representation change whenever it lands — it must not alter what 'all' resolves to.

## Issue #23: Leaving a room by cardinal direction command does not end combat like 'flee' does.

- State: open
- Labels: bug
- Milestone: Version 20
- Assignees: none
- Created: 2026-07-12 | Updated: 2026-07-13
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/23

### Body

Possible solution: leaving by one of the directional commands is blocked during combat.

### Comments (2)

**KnightOfNight** — 2026-07-12:
Same design pass as #29: "block directional movement during combat" is one entry in #29's combat-blocked command list. Rule them together.

**KnightOfNight** — 2026-07-13:
V20 planning ruling: this is a bug and ships in Version 20 (milestone added).

Decoupled from #29: the earlier comment proposed ruling them together, but #29 is deferred as a gameplay change while this issue is a defect to fix now. The specific fix approach (block directional movement during combat vs. treat it as flee) is settled during the v20 commands design pass, not here.

## Issue #24: NPC display grammar: article stacking in combat messages

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-13
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/24

### Body

Combat messages prepend "the" to NPC names that already contain articles or phrases, producing lines like:

> You land a critical hit on the one of the Matron's brood for 64 damage.
> You hit the the Silk Matron for 22 damage.
> A the Silk Matron snarls and moves to attack!

Root cause: `NpcDefinition.name` values include their own articles/phrasing ("the Silk Matron", "one of the Matron's brood") while message templates independently prepend articles ("the {name}", "A {name}").

Likely structural fix (for later design discussion, not decided here): author NPC names article-free and add a display-name helper or explicit article/phrase fields, rather than patching 40+ name strings against every template. Needs discussion and planning before implementation.

Found during v19 playtest (first boss kill session).


### Comments (1)

**KnightOfNight** — 2026-07-13:
V20 planning ruling: ships in Version 20 (milestone added).

Rides with the output & messaging work (#13, #14, #39): combat message templates are opened once in v20 for colorization, and the article fix lands in the same pass rather than reopening the templates next version. The structural fix direction in the body stands (article-free authored names plus display-name/article support, not per-template patching). Note for planning: this is the one migration-carrying item in the output & messaging group — exact field shape on NpcDefinition is a design-brief decision, and it includes a data pass over the existing NPC names.

## Issue #25: Bosses do not heal when the player disengages

- State: open
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

## Issue #28: Corpse decay and empty-loot messaging is noisy and misleading

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-13
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/28

### Body

Two related texture problems from v19 play:

1. Corpse decay announces itself for every corpse, including mid-combat ("The corpse of cave centipede slowly disappears." interleaved with active fight lines), adding noise at the worst moment.
2. Lootless kills (normal-tier NPCs, which by design drop nothing) answer `loot` with "The corpse of X is already empty." / "There is nothing to loot here." — to a new player this reads as *I missed the loot* rather than *normals don't drop*.

Needs discussion and planning: quieter decay (suppress during the looter's active combat? decay silently?), and empty-corpse messaging that doesn't imply missed treasure. Interacts with the planned combat-message colorization work (#13), so they may want to ride together.


### Comments (1)

**KnightOfNight** — 2026-07-13:
V20 planning ruling: ships in Version 20 (milestone added).

Rides with the output & messaging work (#13, #14, #39), per the interaction with #13 already flagged in the body. Scope boundary for the design pass: corpse decay timing and loot mechanics are unchanged — this issue governs only when and how the decay and empty-loot messages are emitted (suppression during the looter's active combat, and empty-corpse wording that does not imply missed treasure).

## Issue #29: Block looting (and related inventory commands) during combat

- State: open
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-13
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/29

### Body

Currently `loot` works mid-combat: a player can secure spoils from earlier kills while a fight is still undecided, and mid-fight looting also sidesteps the risk that death (or corpse decay) costs you the unclaimed loot. Discussed and deferred in the v19 design pass.

Ruled direction (starting point, not final): `loot` refuses during combat with an in-fiction message, matching the pattern `quit` will use. Needs discussion and planning before implementation:

- Which sibling commands join it for one consistent combat-blocked list — `pickup` has the identical exploit; `equip`/`unequip` mid-fight (armor-swapping per enemy) is arguably a bigger one. `use` stays allowed by design (potions in combat are the point).
- Corpse-decay interaction: if loot must wait for combat's end, long multi-NPC fights must not outlive the first corpse's despawn timer — verify the timer comfortably exceeds long fights, or freeze decay while the killer's session is active.
- Classic-MUD alternative recorded for the discussion: allow looting but at an action cost (looting consumes your combat round). Requires an action economy that doesn't exist yet; noted as future flavor, not the recommended path.


### Comments (2)

**KnightOfNight** — 2026-07-12:
#23 (cardinal movement doesn't end combat) belongs on this issue's combat-blocked command list — its proposed solution is an entry here. Rule them together.

**KnightOfNight** — 2026-07-13:
V20 planning ruling: deferred — not in Version 20. This is a gameplay-rules change, and v20 scope is UI/UX fixes and improvements only.

#23 has been pulled out of this issue's combined design pass and ships in v20 as a bug fix. The remaining combat-blocked command list (loot, pickup, equip/unequip) stays here for a future version's design pass.

## Issue #30: Travel network: should checkpoints (shards) also be travel senders?

- State: open
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-12
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

## Issue #31: Shyland: richer live connection status indicator (beyond static "Connected to Shyland")

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-13
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/31

### Body

## Summary

Right now the Shyland web client just shows a static "Connected to Shyland" message once the WebSocket connects. There's no ongoing indication that the connection is alive and healthy — it looks identical whether the session has been stable for 2 seconds or 2 hours, and it wouldn't visibly change if the connection were degrading.

## Request

Add a real-time-feeling connection status indicator to the play UI, for example:

- A blinking/pulsing "connected" light (green = healthy, could shift color/state on reconnect attempts or lag)
- Live network/latency info (e.g. round-trip ping time to the server)
- Some visible heartbeat so a stable connection *looks* stable, rather than a message that's printed once and never updates

This is a UX/polish feature, not a bug — the connection itself works fine, this is about giving players confidence/feedback that it's still working.

## Notes for implementation

- Likely needs a lightweight ping/pong exchange over the existing `wss://<host>/ws/shyland/` connection (`SkylandConsumer`) to measure latency, plus client-side JS to animate the indicator.

### Comments (0)

None.

## Issue #32: Shyland: output messages need timestamps and guaranteed ordering

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-12
- Blocked by: none
- Blocks: #37
- URL: https://github.com/KnightOfNight/games-mvc/issues/32

### Body

## Summary

Output messages sent to the Shyland client (`{"type": "output", "text": "...", "category": "room|chat|system|error"}`) currently have no timestamp, and there's no guarantee they render in the order they were generated server-side. Under normal play this isn't noticeable, but with concurrent events (room broadcasts, chat, combat ticks, etc.) messages can potentially arrive or be displayed out of sequence, and players have no way to tell when something happened.

## Request

- Add a timestamp to outgoing `output` messages (server-generated, not client-trusted) so the client can display when each line occurred.
- Ensure output messages are delivered/rendered in the order they were produced, even when they originate from different sources (room broadcast via `group_send`, direct send, tick engine, etc.).

This is a UX/reliability feature, not a bug report — flagging a gap rather than a specific broken repro.

## Notes for implementation

- Timestamp should be generated server-side in `consumers.py` / wherever `output` messages are constructed, not trusted from the client.
- Ordering guarantees may need to account for messages arriving from multiple channel-layer group sends and the ticker (`run_tick_engine`) landing at the same client at once — consider whether a sequence number is also needed alongside the timestamp.

### Comments (1)

**KnightOfNight** — 2026-07-12:
Ruled: this ships in Version 20. Beyond the player-facing timestamp feature, this issue is the structural foundation for firehose logging — routing every player-visible message through one envelope (server UTC timestamp + monotonic sequence number) creates the single tap point the firehose issue attaches its sink to. See the Firehose Logging milestone.

## Issue #33: Shyland: persist detailed combat logs for balance analysis

- State: open
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

## Issue #35: Map system backend: MapFrag derivation, exit boundary flags, map data payload

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-13
- Blocked by: #42
- Blocks: #36
- URL: https://github.com/KnightOfNight/games-mvc/issues/35

### Body

## Summary

Server-side foundation for the v20 in-client map: derive map structure from the existing room/exit graph and deliver a per-character map payload to the client. Companion to the client rendering issue (see cross-links).

## Ruled design decisions (firm — from the v20 pre-planning session)

- **MapFrag** is the unit of map display: a connected component of rooms computed over **unflagged cardinal exits (N/S/E/W) only**. MapFrags are **derived at runtime, never stored**.
- **No coordinates are added to `Room` for map purposes.** Map layout is derived by walking the cardinal exit graph (north always up). All GDD §2.5 content about coordinate grids / stored room coordinates is deprecated by this ruling (the "(0,0,0) Heart of the Convergence" reference may survive as Obelisk mythology lore).
- **NSEW exits are spatially consistent by default** — walking north then south returns you — unless a **per-exit boundary flag** overrides. The boundary flag is a new authored property on exits; flagged exits do not join rooms into the same MapFrag.
- **Up/down always break into a new MapFrag.** No vertical layering in v1.
- **Non-cardinal movement verbs (enter, travel, etc.) never join MapFrags.**
- **Zone boundaries only break a MapFrag if the boundary flag is set** — a zone border alone does not split the map.
- **Fog-of-war comes from the existing `RoomVisit` model**: the payload includes only rooms the character has visited. Per-character revelation, no new tracking model.

## Scope

- Model change: per-exit boundary flag (exact field shape is a design-brief decision — exits are currently direction fields on `Room`). Migration required.
- MapFrag computation: given a character's current room, compute its MapFrag and the visited subset, with relative positions derived from cardinal traversal.
- Map payload: shape and delivery (on move / on look / on demand) to be settled in the design brief; server-generated, nothing trusted from the client.
- Seeding: audit for exits that need the boundary flag once it exists.

## Not in scope

- Client rendering (companion issue)
- Zoom, vertical layers, minimap variants — explicitly deferred past v1


### Comments (1)

**KnightOfNight** — 2026-07-13:
SUPERSEDING RULINGS (v20 design session, 2026-07-13). The 'Ruled design decisions' in this issue's body are revised as follows. Where this comment and the body conflict, this comment wins. The implementation brief will restate the full model and is authoritative once written.

THE SETTLED MAP DATA MODEL:

1. Room.coord_x/coord_y/coord_z exist today, authored for all rooms, and are the map's POSITIONAL source of truth. They are map-space only — z is NOT elevation and never will be. Exits remain the connectivity source of truth.

2. Coordinate space is PER-ZONE. Each zone has its own origin and grid. One room per (zone, x, y, z) cell, no exceptions.

3. Core invariant: every UNFLAGGED cardinal exit (N/S/E/W) between rooms in the same zone must land grid-adjacent at the same z (north = y+1, etc.). A violation is a data defect.

4. The per-exit boundary boolean is KEPT (new authored property, model change + migration as scoped in the body). A flagged exit is a MapFrag boundary regardless of geometry — flagged exits have NO geometric requirement and may even be grid-adjacent (severed neighbors are legal).

5. Cross-zone cardinal exits are boundaries AUTOMATICALLY (per-zone spaces are not comparable). They need no flag and are exempt from geometric checks. The Tree Arch gate requires nothing.

6. Up/down exits have no geometric requirement of any kind and always break fragments. Non-cardinal movement verbs never join fragments.

7. MapFrag remains DERIVED, never stored: connected components over unflagged, intra-zone cardinal exits. Map positions come straight from stored coords (fog-of-war filtered by RoomVisit) — the BFS position-derivation machinery in the body is superseded and will not be built.

8. Partial revision of the earlier GDD ruling: GDD §2.5 is deprecated as an elevation-aware coordinate/minimap spec, but the coordinate grid itself is reinstated in revised form as pure map-space. The GDD capture at v20 closeout will reflect this.

CONSEQUENCE FOR SCOPE: 'Seeding: audit for exits that need the boundary flag' expands — the audit (#42, revised by its own comment) will also produce a coordinate re-author plan (Z01 surface z-flattening, Convergence ring re-layout, valley-cave fragment relocation). Those findings become issues and are fixed inside the map implementation brief.


## Issue #36: Map system client: right-pane map rendering (node-and-line, fog-of-war)

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-13
- Blocked by: #35
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/36

### Body

## Summary

Client-side rendering of the v20 map in the right pane, consuming the MapFrag payload from the backend issue (see cross-links).

## Ruled design decisions (firm — from the v20 pre-planning session)

- **Node-and-line graph**: rooms are circles, exits are lines. Not tiles, not ASCII.
- **North is always up.** No rotation.
- **Fixed-size window centered on the player's current room.** No zoom in v1; rooms outside the window are simply not drawn.
- **Fog-of-war**: only visited rooms (per the `RoomVisit`-derived payload) are rendered. Unvisited rooms do not appear, even as placeholders.
- **The right pane is widened to accommodate a square map area.** This interacts directly with the Right Pane Design issue (#2) — the map is one of its planned occupants, and the two must be designed together.
- **Screen reader handling: the map is `aria-hidden`.** The map is a redundant visual convenience; room descriptions and exits remain the accessible source of truth. This is the ruled v1 stance.

## Scope

- Vanilla JS rendering (no framework dependency, per stack rules), responsive down to phone width
- Redraw on movement / map payload update
- Visual treatment of the current-room marker and exit lines

## Not in scope

- Backend MapFrag computation and payload (companion issue)
- Zoom, pan, vertical layers — deferred past v1


### Comments (2)

**KnightOfNight** — 2026-07-12:
Right-pane layout context lives in #2; the map is one of its planned occupants.

**KnightOfNight** — 2026-07-13:
V20 design session note (2026-07-13): the backend positional model was revised — map positions in the payload now come from stored Room coordinates (map-space, per-zone) rather than BFS derivation over exits. See the superseding-rulings comment on #35. No change to any ruling in this issue's body: node-and-line rendering, north-up, fixed window, fog-of-war, right-pane widening, and aria-hidden all stand as written.


## Issue #37: Universal event logging (firehose): every command, every output, every event

- State: open
- Labels: none
- Milestone: Firehose Logging
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-12
- Blocked by: #32
- Blocks: none
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
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-12
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

## Issue #39: Output colorization: section header labels ('Exits:', 'Who's here?', 'What's here?') should share one color

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-12
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/39

### Body

## Summary

Section header labels in room-look output should share a single consistent color. Companion to #14, which defines these labels ("Exits:", "Who's here?", "What's here?") as part of the look-command output structure.

## Ruled

- The color used for "Who's here?" and "What's here?" must match the color used for "Exits:".
- These are structural section-header labels, not room content — they should read as a consistent UI chrome color, distinct from the colored room/zone/area content ruled in #1.

## Needs discussion and planning

- Exact color value, and how it fits into the wider output palette (palette work already ruled separately in #1 and #13)
- Whether other structural labels (existing or future) should share this same header color
- Whether this rule covers only the three named labels or is a general "section header" rule for the whole output window

## Related

- #14 — defines the "Exits:" / "Who's here?" / "What's here?" output sections these labels belong to
- #1 — location bar / breadcrumb colorization (room content color rules)
- #13 — combat message colorization (different color category: combat feedback, not structural labels)


### Comments (0)

None.

## Issue #40: Free repair messages repeat too often (Morra example) — research spike into other duplication cases

- State: open
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
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-12
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


### Comments (0)

None.

## Issue #42: Audit: intra-MapFrag spatial consistency of The Convergence and Z01 room graphs

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-13 | Updated: 2026-07-13
- Blocked by: none
- Blocks: #35
- URL: https://github.com/KnightOfNight/games-mvc/issues/42

### Body

## Summary

Read-only analysis of the seeded world data for The Convergence (Z05) and The Verdant Reach (Z01), verifying that the existing room/exit graphs satisfy the intra-MapFrag spatial-consistency rules the v20 map system depends on. Prerequisite for the map backend (#35): the audit's findings determine which exits need the boundary flag and whether any exit wiring must be corrected before MapFrag derivation can render sanely.

## Background — the ruled map model (see #35 for full rulings)

A MapFrag is a connected component of rooms over unflagged cardinal exits (N/S/E/W) only, derived at runtime, never stored. Map positions are derived by walking the cardinal exit graph from the player's room (north = up). This derivation is only coherent if, WITHIN each MapFrag, the authored exits behave like consistent 2D geometry. Nothing in the engine has ever enforced this — exits are labeled pointers — so the as-built data must be audited.

## What to check (within each derived MapFrag)

1. **Reciprocity**: for every cardinal exit A --north--> B, verify B has a south exit back to A (and likewise for each direction pair). List every non-reciprocal cardinal exit.
2. **Path agreement / no overlap**: derive grid positions by BFS from an arbitrary root, walking cardinal exits (N = +y, S = -y, E = +x, W = -x). List every contradiction: a room reachable at two different derived positions, or two distinct rooms deriving the same position.
3. **Ring street closure**: verify the Infinity City ring street's cardinal exits actually close into a drawable loop under the derivation above, rather than accumulating drift.
4. **Valley-cave-mouth wiring**: determine how the Z01 Act 1 valley-wall cave entrances are wired. If they are cardinal exits, they merge the caves into the surface MapFrag and must be recorded as boundary-flag candidates. If they are up/down, they already break fragments and need nothing.
5. **Cross-zone gate inventory**: list every cardinal exit that crosses a zone boundary (e.g. the Tree Arch between Z05 and Z01), as candidates for a boundary-flag decision. Do not decide — inventory only.

## Output

A report document committed to the repo at `docs/shyland/Shyland_MapFrag_Audit_Z05_Z01.md` containing: the derived MapFrag inventory (fragment count, room count per fragment), every violation found for checks 1–3, the finding for check 4, the inventory for check 5, and a consolidated list of exits recommended for the boundary flag. Findings feed the #35 design brief; no fixes are made under this issue.

## Constraints

- **Read-only with respect to game data**: no model changes, no migrations, no reseeding, no exit rewiring. The only repo write is the report document.
- The boundary flag does not exist yet (#35 creates it) — this audit produces the seeding list for it, nothing more.

## Related

- #35 — map backend (blocked by this audit)
- #36 — map client (transitively downstream via #35)


### Comments (1)

**KnightOfNight** — 2026-07-13:
REVISED AUDIT SPECIFICATION (v20 design session, 2026-07-13). This comment supersedes the body's 'What to check' section. The audit brief will be self-contained and authoritative; this comment records the revised spec. Context: Room.coord_x/y/z exist and are authored for all rooms; the ruled model makes them the map's positional source of truth (see the superseding-rulings comment on #35).

REVISED CHECKS:

1. GEOMETRY AGREEMENT: for every intra-zone cardinal exit, verify the destination's stored coordinates sit exactly one cell in that direction from the source, at the same z. This single check subsumes the body's reciprocity, path-agreement, no-overlap, and ring-closure checks. Every violation is listed and categorized: (a) z-drift — correct x,y, z differs (terrain-as-elevation authoring); (b) x,y mismatch — outright layout disagreement; (c) intended-boundary candidates — exits that should be flagged once the flag exists (e.g. valley cave mouths), where non-adjacency will be intentional after relocation.

2. CELL UNIQUENESS: verify one room per (zone, x, y, z) within each zone. (Cross-zone coordinate overlap is expected and legal under per-zone spaces.)

3. CROSS-ZONE EXIT INVENTORY: list all cardinal exits crossing zone boundaries. Informational only — these are automatic boundaries under per-zone spaces and need no flag and no fix.

4. UP/DOWN: no geometric checks. Inventory only, to support the fragment-count report.

5. CAVE-MOUTH DETERMINATION (body check 4, retained): identify how each Z01 cave entrance is wired and where each cave's fragment boundary should sit (mouth vs. first vertical exit), producing the boundary-flag seeding list and the cave-relocation list.

REVISED OUTPUT: the report (same path as the body) delivers (a) the violation lists by category, (b) the boundary-flag seeding list, (c) a coordinate re-author plan: Z01 surface flattened to one z-plane, Convergence ring/path re-layout, valley-cave fragment relocation to their own z-planes, (d) the derived MapFrag inventory under the settled model.

PRELIMINARY QUANTIFICATION (from design-session static analysis of seed_world.py; the audit confirms authoritatively): of 386 directed intra-zone cardinal edges, ~330 already satisfy geometry agreement; ~24 show z-drift (the Z01 stair/ridge climb); ~30 show x,y mismatch (mostly the Convergence ring street, which does not close cleanly on the grid); the valley cave mouths are currently grid-adjacent (continuous) and become flag-plus-relocation work by design intent.

PROCESS (per the v20 triage ruling): this audit is triage and does not count against the five-brief cap. Findings become GitHub issues, milestoned Version 20, and are fixed inside the map implementation brief — including any NPC dialogue compass-direction re-checks required by rewired or re-laid rooms (geography audit rule).


## Closed Issues — Summary Table

| # | Title | Labels | Closed |
|---|---|---|---|
| 34 | Aldric's help response gives wrong direction to the Verdant Reach gate | bug | 2026-07-12 |
