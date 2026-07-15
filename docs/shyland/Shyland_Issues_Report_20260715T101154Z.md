# Shyland Issues Report

- Generated: 20260715T101154Z
- Repo: KnightOfNight/games-mvc
- Open issues: 39
- Closed issues: 20
- Dependency data: available

## Open Issues — Summary Table

| # | Title | Labels | Milestone | Updated |
|---|---|---|---|---|
| 1 | Location Bar Updates - Complete Breadcrumb Trail by Name |  | Version 20 | 2026-07-13 |
| 2 | Right Pane Design |  | Version 20 | 2026-07-13 |
| 4 | Build Zone: Ashenveil Cathedral (Z02) |  | Z02 - Ashenveil Cathedral | 2026-07-12 |
| 5 | Build Zone: The Neon Sprawl (Z03) |  | Z03 - The Neon Sprawl | 2026-07-12 |
| 6 | Build Zone: The Blasted Flats (Z04) |  | Z04 - The Blasted Flats | 2026-07-12 |
| 7 | Build Zone: The Iron Deeps (Z06) |  | Z06 - The Iron Deeps | 2026-07-12 |
| 8 | Build Zone: The Pale Shore (Z07) |  | Z07 - The Pale Shore | 2026-07-12 |
| 9 | Build Zone: The Wastelands (Z08) |  | Z08 - The Wastelands | 2026-07-12 |
| 10 | Transactional email via Postmark (password resets) |  |  | 2026-07-12 |
| 11 | Account onboarding via unusable password + reset link (no temp passwords) |  |  | 2026-07-12 |
| 12 | Two-factor authentication via TOTP (django-otp) |  |  | 2026-07-12 |
| 13 | Combat Messages Colors |  | Version 20 | 2026-07-14 |
| 14 | Look-Command Output Sections |  | Version 20 | 2026-07-14 |
| 15 | Show Commands in Output Window for Context |  | Version 20 | 2026-07-14 |
| 17 | New NPC Spawn Doesn't Agro Immediately | bug |  | 2026-07-11 |
| 18 | Animal Hides Don't Stack in Inventory | bug |  | 2026-07-13 |
| 24 | NPC display grammar: article stacking in combat messages |  | Version 20 | 2026-07-14 |
| 25 | Bosses do not heal when the player disengages | bug |  | 2026-07-12 |
| 26 | Boss and elite kills pay flat XP — no tier multiplier |  |  | 2026-07-12 |
| 27 | Research: passive regen ticks landing after combat engagement |  |  | 2026-07-12 |
| 28 | Corpse decay and empty-loot messaging is noisy and misleading |  | Version 20 | 2026-07-14 |
| 29 | Block looting (and related inventory commands) during combat |  |  | 2026-07-13 |
| 30 | Travel network: should checkpoints (shards) also be travel senders? |  |  | 2026-07-12 |
| 31 | Shyland: richer live connection status indicator (beyond static "Connected to Shyland") |  | Version 20 | 2026-07-13 |
| 33 | Shyland: persist detailed combat logs for balance analysis |  | Firehose Logging | 2026-07-12 |
| 37 | Universal event logging (firehose): every command, every output, every event |  | Firehose Logging | 2026-07-12 |
| 38 | Obelisk attunement: player-set home spawn at checkpoint shards |  |  | 2026-07-12 |
| 39 | Output colorization: section header labels ('Exits:', 'Who's here?', 'What's here?') should share one color |  | Version 20 | 2026-07-14 |
| 40 | Free repair messages repeat too often (Morra example) — research spike into other duplication cases |  |  | 2026-07-12 |
| 41 | Lock battle-zone access until a new player has visited all of The Convergence |  |  | 2026-07-12 |
| 47 | Right pane: player effects display (sent and received) |  |  | 2026-07-13 |
| 51 | right pane has horizontal and vertical scrollbars | bug |  | 2026-07-14 |
| 52 | In-combat heals apply on stale character state, resurrecting persisted damage (lost-update race) | bug | Version 21 | 2026-07-14 |
| 53 | map gates are gray (ed out) even if they have been passed by the player | bug |  | 2026-07-14 |
| 54 | consider how to simplify combat language and make it more human |  |  | 2026-07-14 |
| 55 | "who's here" list doesn't need "is here" at the end of every line | bug |  | 2026-07-14 |
| 57 | new command: home [now] |  |  | 2026-07-14 |
| 58 | vendor for-sale list changes |  |  | 2026-07-15 |
| 59 | some commands not logged in timestamped output | bug |  | 2026-07-15 |

## Open Issues — Full Detail

## Issue #1: Location Bar Updates - Complete Breadcrumb Trail by Name

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-13
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


### Comments (2)

**KnightOfNight** — 2026-07-13:
V20 layout pre-decision (2026-07-13): the location bar is the top region of the left 2/3 of the screen, one line of text high — a less-wide version of the current bar (the right 1/3 is the fixed-width right pane, #2). With the unified output pane ruling (#16 closed), this bar is the persistent carrier of zone/area/room identity; the breadcrumb and color rules in this issue's body stand unchanged.

**KnightOfNight** — 2026-07-13:
V20 layout design pass rulings (2026-07-13):

D1 — THEME COLORS AS MODEL FIELDS (data-into-models): Zone.theme_color and Area.theme_color (hex strings) become seeded model fields — one authoritative source read by the location bar now and by the output-colorization work later, satisfying this issue's 'output matches breadcrumbs' rule. Concrete color values are authored creative content in the layout brief. Room text: fixed near-white client style. Colors are delivered server-side with location updates; the client renders what it is sent.

D2 — OVERFLOW: the bar is one line; on overflow the Area segment truncates first (ellipsis), then Room; Zone never truncates.


## Issue #2: Right Pane Design

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-13
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/2

### Body

Map. 

Enemy stats. 

Player effects sent and received. 

### Comments (4)

**KnightOfNight** — 2026-07-12:
Map system issues filed: backend #35, client #36. The client issue widens the right pane for a square map area — the right-pane layout design here must account for it.

**KnightOfNight** — 2026-07-13:
V20 layout pre-decision (2026-07-13) — ruled skeleton and vocabulary, recorded here as the right-pane design issue:

LEFT 2/3 (baseline 700px), three stacked regions:
- LOCATION BAR: top, one line of text high — a less-wide version of today's bar (see #1).
- OUTPUT PANE: one unified scrolling pane for ALL output — zone/area/room text, who's here, what's here, commands and their results. The separate-description-pane idea is superseded (#16 closed).
- COMMAND BAR: bottom; the send button lives INSIDE the command bar area.

RIGHT PANE: right 1/3, FIXED width (300px content), top to bottom:
- Top: current player stats as today; the whole stats subsection turns RED during combat.
- Middle: current-fight information (enemy count, health, targeting) — a SCROLLING area.
- Bottom: the map, a fixed 300x300px square (#35/#36).

Baseline total 1000px. On window expansion the right pane keeps its fixed width; only the left regions grow. Responsive/phone stacking remains a design item for this issue's brief. The map's geometry is FINAL and ships in the map brief; this issue's brief later fills the pane's middle region and the combat-red stats treatment around it.


**KnightOfNight** — 2026-07-13:
V20 layout design pass rulings (2026-07-13), completing this issue's design:

D3 — COMBAT-RED MECHANISM: the stats section carries an in-combat CSS class driven by the existing client-state sync (a combat-membership boolean is added to the state payload if not already present). The layout brief defines the base combat-red family values; the v20 output/messaging palette derives its hit-severity shades from the same family (see note on #13).

D4 — FIGHT-INFO FEED: a new structured 'fight' message on each combat tick to the involved player: enemy list with name, hp/hp_max, and focused-target marker; also sent on engagement and on combat end (inactive state clears the region). Middle region renders name + bar + numbers + focus marker rows, scrolling on overflow, empty outside combat.

DEFERRAL: 'Player effects sent and received' from this issue's body is deferred out of Version 20 — filed as its own unmilestoned issue (see cross-link comment). v20 right pane ships stats / fight info / map only.

D6 — PHONE STACKING: location bar, compact stats strip (fight info under it only during combat), output (flex), command bar pinned last; the map renders below the output, reachable by scroll.


**KnightOfNight** — 2026-07-13:
Deferred effects-display portion filed as #47.


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
- Created: 2026-07-11 | Updated: 2026-07-14
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/13

### Body

Combat Messages should be different colors.

There should be different shades of red for different levels of hit.

A miss should be gray.

Consider adding arrows showing the direction of the attack. A hit from an NPC you can start the line of text with an arrow pointing left. A hit from a player can end with a arrow pointing right.

### Comments (2)

**KnightOfNight** — 2026-07-13:
V20 layout pre-decision note (2026-07-13): the right pane's player-stats subsection turns red during combat (ruled on #2). When this issue's palette is designed, treat 'combat red' as ONE coordinated color family spanning combat message text (this issue) and the stats-panel combat state — not two independent reds.

**KnightOfNight** — 2026-07-14:
V20 output & messaging design pass rulings (2026-07-13):

PALETTE (ruled, ships in the v20 output & messaging brief): outgoing hit #C4453F; outgoing critical #E24B4A bold; INCOMING hit (NPC hits the player) #E0724A — a distinct orange-red, so attack direction reads at a glance without arrows; miss #8A887F gray; kill/XP/reward #D8B45A gold. All reds belong to ONE family with the stats-panel combat state (#E24B4A accent, #3A1212 tint) from the layout brief — no second red anywhere.

ARROWS: ABANDONED. The proposed directional arrows on combat lines (-> outgoing, <- incoming) were designed, reviewed, and struck during this pass. They are NOT deferred and are NOT tracked for future consideration. Attack direction is carried by the message text itself plus the incoming/outgoing color distinction above.

Colorization is client-side styling driven by server-supplied semantic categories; the server never sends hex colors for message text.

## Issue #14: Look-Command Output Sections

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-11 | Updated: 2026-07-14
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

### Comments (2)

**KnightOfNight** — 2026-07-12:
Color requirement filed as #39: the "Who's here?" and "What's here?" labels defined here should match the color of "Exits:". This issue defines the section structure; #39 rules the color consistency across those labels.

**KnightOfNight** — 2026-07-14:
V20 output & messaging design ruling (2026-07-13): look output renders exactly as this issue's body specifies (Exits: line, blank, Who's here? + occupant lines, blank, What's here? + item lines). Sections with no content are OMITTED ENTIRELY — no empty header, no 'nobody here' line. Header labels take the shared structural-header color (#39).

## Issue #15: Show Commands in Output Window for Context

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: none
- Created: 2026-07-11 | Updated: 2026-07-14
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/15

### Body

"You don't see that here." by itself loses context.

Print player commands in the output window.

### Comments (1)

**KnightOfNight** — 2026-07-14:
V20 output & messaging design ruling (2026-07-13): every submitted command echoes into the output pane BEFORE its result as '> <command as typed>', in gray (#8A887F), carrying the standard timestamp prefix. It is a transcript of the player — never re-broadcast to other players, never styled as system output. Echoes for invalid commands too, so 'You don't see that here.' always has its context directly above it.

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

## Issue #24: NPC display grammar: article stacking in combat messages

- State: open
- Labels: none
- Milestone: Version 20
- Assignees: KnightOfNight
- Created: 2026-07-12 | Updated: 2026-07-14
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


### Comments (2)

**KnightOfNight** — 2026-07-13:
V20 planning ruling: ships in Version 20 (milestone added).

Rides with the output & messaging work (#13, #14, #39): combat message templates are opened once in v20 for colorization, and the article fix lands in the same pass rather than reopening the templates next version. The structural fix direction in the body stands (article-free authored names plus display-name/article support, not per-template patching). Note for planning: this is the one migration-carrying item in the output & messaging group — exact field shape on NpcDefinition is a design-brief decision, and it includes a data pass over the existing NPC names.

**KnightOfNight** — 2026-07-14:
V20 output & messaging design ruling (2026-07-13): the structural fix is adopted. NpcDefinition.name becomes ARTICLE-FREE ('Silk Matron', 'cave spider'); new fields article (CharField, default 'the', BLANK for proper nouns like Morra/Mother Tansy/VND-9) and plural_phrase (CharField, blank; used verbatim for group-phrase names like 'one of the Matron's brood'). One display helper composes every player-visible NPC reference; NO template may prepend its own article. Migration plus a data pass over all seeded NPC names ship in the v20 output & messaging brief. Seed verify gains the authoring law: no NpcDefinition name begins with an article.

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
- Created: 2026-07-12 | Updated: 2026-07-14
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/28

### Body

Two related texture problems from v19 play:

1. Corpse decay announces itself for every corpse, including mid-combat ("The corpse of cave centipede slowly disappears." interleaved with active fight lines), adding noise at the worst moment.
2. Lootless kills (normal-tier NPCs, which by design drop nothing) answer `loot` with "The corpse of X is already empty." / "There is nothing to loot here." — to a new player this reads as *I missed the loot* rather than *normals don't drop*.

Needs discussion and planning: quieter decay (suppress during the looter's active combat? decay silently?), and empty-corpse messaging that doesn't imply missed treasure. Interacts with the planned combat-message colorization work (#13), so they may want to ride together.


### Comments (2)

**KnightOfNight** — 2026-07-13:
V20 planning ruling: ships in Version 20 (milestone added).

Rides with the output & messaging work (#13, #14, #39), per the interaction with #13 already flagged in the body. Scope boundary for the design pass: corpse decay timing and loot mechanics are unchanged — this issue governs only when and how the decay and empty-loot messages are emitted (suppression during the looter's active combat, and empty-corpse wording that does not imply missed treasure).

**KnightOfNight** — 2026-07-14:
V20 output & messaging design rulings (2026-07-13): DECAY — corpse-decay messages are NOT sent to any player currently in an active combat session (dropped, not deferred); non-fighting players in the room still see them, in ambient gray. Decay timing and loot mechanics are unchanged. EMPTY CORPSE — a corpse that never had loot answers 'The <npc> carried nothing worth taking.' (composed via the #24 display helper). A corpse the player already emptied keeps a distinct accurate line: 'You've already taken everything from the <npc>.'

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

### Comments (1)

**KnightOfNight** — 2026-07-13:
V20 layout design pass ruling (2026-07-13) — D5: the indicator lives at the right end of the command bar (always visible at the typing focus). Dot + latency readout: green healthy, amber (latency above threshold or one missed pong), red pulsing while reconnecting, gray disconnected. Client-side ping every 10s over the existing WebSocket, server echoes, RTT computed client-side, nothing trusted from the client. Accessible label present but not announced on every update. Ships in the v20 UI layout brief.


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
- Created: 2026-07-12 | Updated: 2026-07-14
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


### Comments (1)

**KnightOfNight** — 2026-07-14:
V20 output & messaging design ruling (2026-07-13): the open question in this issue's body is settled the GENERAL way — every structural section-header label, present and future, shares one chrome color (#7FB3D5). Not just the three named labels. Room content, prose, and zone/area names are separate color roles and never use it.

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

## Issue #47: Right pane: player effects display (sent and received)

- State: open
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

## Issue #51: right pane has horizontal and vertical scrollbars

- State: open
- Labels: bug
- Milestone: none
- Assignees: none
- Created: 2026-07-14 | Updated: 2026-07-14
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/51

### Body

These may disappear after all of version 20 has shipped.  If not, the bug will remain.

### Comments (0)

None.

## Issue #52: In-combat heals apply on stale character state, resurrecting persisted damage (lost-update race)

- State: open
- Labels: bug
- Milestone: Version 21
- Assignees: KnightOfNight
- Created: 2026-07-14 | Updated: 2026-07-14
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/52

### Body

## Symptom

Drinking a Healing Draught (+25) during combat frequently raises the Vitality bar by far more than 25. Observed in v20 Brief 1 playtesting. Not related to level-up (which does fully restore bars by design — separate, documented-elsewhere behavior) and not passive regen (correctly excluded for characters in an active combat session). Both alternates were verified clean during diagnosis.

## Root cause (diagnosed 2026-07-14, design chat)

Classic lost-update race between the consumer and the tick engine on `vitality_current`:

- `cmd_use` applies the heal to `self.character` — an in-memory object the consumer caches at connect (`consumers.py` ~line 197) and refreshes only when a code path calls `get_character_fresh()` (~line 2304, which reassigns `self.character`).
- During combat, the tick engine damages the character and saves `vitality_current` to the database every round. The consumer's cached object never sees those writes.
- `_apply_instant_component` (`effect_utils.py`, `restore_vitality`) computes `stale_vitality + magnitude` from the cached object and saves it (`update_fields=['vitality_current']`), silently overwriting — i.e. resurrecting — every point of damage the tick engine persisted since the consumer's last refresh.

The effect message honestly prints the magnitude actually added to the stale value ("+25 Vitality"), but the persisted bar jumps by 25 plus all damage taken since the last consumer refresh. The longer the fight before drinking, the larger the phantom heal.

## Severity notes

- This is data corruption, not display: real damage is erased from the database.
- Exploitable once understood: take hits, then drink — an effectively free full heal.
- The same read-modify-write-on-cached-object pattern likely afflicts sibling paths: `restore_longevity`, `restore_acuity`, and any other consumer-side mutation of character bars while the tick engine runs. The fix must include an audit sweep, not just the vitality line.

## Fix shape (for the v21 design pass; not ruled yet)

Bar mutations become atomic database operations — e.g. `F('vitality_current') + magnitude` with a clamp to the maximum (or refresh-and-apply inside a transaction with a row lock) — instead of object-arithmetic-then-save. Plus the sibling audit above, and a regression test that interleaves tick-engine damage with a consumer heal.

## Provenance

Found while investigating over-strength in-combat heals during v20 Brief 1 playtesting; diagnosed by code inspection in the design chat. Deferred to Version 21 by explicit ruling (2026-07-14): v20 is big enough.


### Comments (0)

None.

## Issue #53: map gates are gray (ed out) even if they have been passed by the player

- State: open
- Labels: bug
- Milestone: none
- Assignees: none
- Created: 2026-07-14 | Updated: 2026-07-14
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/53

### Body

Similar to the Up/Down indicators...

### Comments (0)

None.

## Issue #54: consider how to simplify combat language and make it more human

- State: open
- Labels: none
- Milestone: none
- Assignees: none
- Created: 2026-07-14 | Updated: 2026-07-14
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/54

### Body

Example: when fighting multiple monsters, instead of "You hit the first giant cave spider for 19 damage. The first giant cave spider is dead.", what about "You hit a giant cave spider for 19 damage. One of giant cave spiders is dead."

The engine only needs to track quantity of monsters and pluralization.

### Comments (0)

None.

## Issue #55: "who's here" list doesn't need "is here" at the end of every line

- State: open
- Labels: bug
- Milestone: none
- Assignees: none
- Created: 2026-07-14 | Updated: 2026-07-14
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/55

### Body

check "what's here" for similar issue.

### Comments (0)

None.

## Issue #57: new command: home [now]

- State: open
- Labels: none
- Milestone: none
- Assignees: none
- Created: 2026-07-14 | Updated: 2026-07-14
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/57

### Body

sends the player home in 15 seconds.  player can type cancel to stop the request.

### Comments (0)

None.

## Issue #58: vendor for-sale list changes

- State: open
- Labels: none
- Milestone: none
- Assignees: none
- Created: 2026-07-15 | Updated: 2026-07-15
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/58

### Body

display rarity
display free items separately
sort groups of items (free, not-free, other groups later) by name


### Comments (0)

None.

## Issue #59: some commands not logged in timestamped output

- State: open
- Labels: bug
- Milestone: none
- Assignees: none
- Created: 2026-07-15 | Updated: 2026-07-15
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/59

### Body

buy
sell

it might be all commands right now


### Comments (0)

None.

## Closed Issues — Summary Table

| # | Title | Labels | Closed |
|---|---|---|---|
| 48 | Move rarity out of item display names into the status flag block |  | 2026-07-15 |
| 45 | New command: timestamps on\|off (player preference for output timestamp display) |  | 2026-07-15 |
| 23 | Leaving a room by cardinal direction command does not end combat like 'flee' does. | bug | 2026-07-15 |
| 20 | Command 'loot all' throws hidden unhandled exception and disconnects player websocket | bug | 2026-07-15 |
| 19 | Automatic command completion |  | 2026-07-15 |
| 21 | New command: sell all |  | 2026-07-15 |
| 3 | New Command: loot all |  | 2026-07-15 |
| 22 | Command nouns and verbs: allow better item references, allow plural references |  | 2026-07-15 |
| 56 | Timestamps display on renderings and state reports; should mark events only | bug | 2026-07-15 |
| 32 | Shyland: output messages need timestamps and guaranteed ordering |  | 2026-07-14 |
| 50 | map only displays one circle with gray lines when you enter a new room with agro | bug | 2026-07-14 |
| 49 | Checkpoint shard wording: remaining sphere->shard fixes (Stairhead, Cragfoot, shard entity, villager lines) | bug | 2026-07-14 |
| 36 | Map system client: right-pane map rendering (node-and-line, fog-of-war) |  | 2026-07-14 |
| 35 | Map system backend: MapFrag derivation, exit boundary flags, map data payload |  | 2026-07-14 |
| 46 | Fordwatch (vr-v07) brief description: "sphere" should be "shard" | bug | 2026-07-14 |
| 44 | Z01 geometry fixes: Stonestep/Highfold relabels, surface z-flattening, boundary-flag seeding list |  | 2026-07-14 |
| 43 | Z05 ring re-lay: realize the chamfer (6 rooms, 3 relabels, spoke re-lay, 2 ring vendors) |  | 2026-07-14 |
| 16 | Change Description and Output to be Different Panes |  | 2026-07-13 |
| 42 | Audit: intra-MapFrag spatial consistency of The Convergence and Z01 room graphs |  | 2026-07-13 |
| 34 | Aldric's help response gives wrong direction to the Verdant Reach gate | bug | 2026-07-12 |
