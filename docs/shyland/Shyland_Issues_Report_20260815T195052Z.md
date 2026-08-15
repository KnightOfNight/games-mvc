# Shyland Issues Report

- Generated: 20260815T195052Z
- Repo: KnightOfNight/games-mvc
- Open issues: 34
- Closed issues: 174
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
| 33 | Shyland: persist detailed combat logs for balance analysis | KnightOfNight | firehose-logging |  | 2026-07-30 |
| 37 | Universal event logging (firehose): every command, every output, every event | KnightOfNight | firehose-logging |  | 2026-07-30 |
| 47 | Right pane: player effects display (sent and received) | KnightOfNight |  |  | 2026-07-30 |
| 70 | Feature: Longevity has no drain — the slow-burn design needs its first consuming mechanic | KnightOfNight |  |  | 2026-07-30 |
| 126 | pluralization subsystem — natural-English plurals for aggregate output | KnightOfNight |  |  | 2026-07-30 |
| 145 | hot_acuity / dot_acuity announce no-op effect ticks (doctrine from #133) | KnightOfNight |  |  | 2026-07-24 |
| 148 | Loot-take sentence embeds the listing composition — flag block and double space don't match other item output | KnightOfNight | output, commands |  | 2026-08-15 |
| 161 | Use shortfall warn lacks context — name the item and the now-empty inventory | KnightOfNight | output, commands |  | 2026-08-15 |
| 163 | Map: more information — starting with percentage of the current zone explored | KnightOfNight | commands |  | 2026-08-15 |
| 174 | Admin command: uptime (container uptimes, disk free, reclaimable space) | KnightOfNight | commands |  | 2026-08-15 |
| 179 | New-zone design rules (collecting issue) | KnightOfNight |  |  | 2026-07-30 |
| 182 | Map changes/fixes (collecting issue) | KnightOfNight |  |  | 2026-08-01 |
| 191 | Firehose consumer: command-pattern watcher — mine player behavior for the next heal/loot-shaped improvements | KnightOfNight | firehose-logging |  | 2026-08-02 |
| 205 | Production deploy target gains a dangling-only image prune — stop the ~500MB/release root-volume growth | KnightOfNight | triaged, V24, deployments |  | 2026-08-15 |
| 209 | Research spike: player info on stat points — discoverability, what each stat controls, spend preview/simulator, and respec | KnightOfNight | commands |  | 2026-08-15 |
| 214 | Move dev to AWS: prod-mirror instance (different FQDN, shared wildcard cert) + automate/document the prod setup | KnightOfNight | deployments |  | 2026-08-08 |
| 217 | 'last' should show current location for players who are currently logged in | KnightOfNight | output, commands |  | 2026-08-15 |
| 219 | In-game release notes: new 'readme' command — format and content TBD | KnightOfNight | commands |  | 2026-08-15 |
| 220 | Multiplayer combat vs a shared NPC is unmodeled — parallel 1v1 sessions: double NPC damage output, no aggro semantics, kill attribution undefined | KnightOfNight |  |  | 2026-08-08 |
| 223 | Production uptime monitoring + alerting — detect broken/unreachable including DNS; AWS-native vs AI-agent mechanism TBD | KnightOfNight | deployments |  | 2026-08-09 |
| 236 | Admin 'wall' command: broadcast to all connected players (pending-restart warning) | KnightOfNight | commands |  | 2026-08-15 |
| 243 | Deleted-while-connected: commands that never fresh-fetch (e.g. inv) render empty/stale output instead of routing to the creator | KnightOfNight | commands |  | 2026-08-15 |
| 249 | make verify-prod: sanctioned read-only production verification target (posture-setting contract of the #187 sibling family; fixed manage.py commands + rollback guard) | KnightOfNight | deployments |  | 2026-08-15 |
| 251 | All config command setters should write both the cached attribute and the DB row | KnightOfNight | commands |  | 2026-08-15 |
| 252 | Briefs assert unverified facts about existing code — no gate checks a brief for technical coherence | KnightOfNight |  |  | 2026-08-15 |

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

## Issue #205: Production deploy target gains a dangling-only image prune — stop the ~500MB/release root-volume growth

- State: open
- Author: KnightOfNight
- Labels: triaged, V24, deployments
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-07 | Updated: 2026-08-15
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


### Comments (2)

**KnightOfNight** — 2026-08-07:
**Dev-side finding (2026-08-06) — corrects this issue's optional deploy-dev rider.**

Emma's dev daemon has the same growth disease in a different organ: Rancher Desktop builds with BuildKit, so the exhaust accumulates as **builder cache**, not dangling images (census: images clean at ~0 reclaimable, but build cache at 41GB / 898 entries / 98% reclaimable, filling the Lima VM's virtual disk to 43%). Prod's daemon uses the classic builder, which is why its exhaust shows up as dangling image pairs instead.

So the sweep is per-daemon, matched to mechanism:

- **Prod / deploy target:** `docker image prune -f` (dangling-only) — as ruled in the body.
- **Dev / deploy-dev:** `docker builder prune -f --keep-storage 5GB` — LRU eviction down to a cap; the most recent build's layers are by definition kept, so the next build is not slower. This replaces the body's "same line in deploy-dev" phrasing.

One-time dev catch-up executed 2026-08-06 (operator-directed, ops session): 35.04GB reclaimed, cache now 5.9GB, VM disk 43% → 7%. The prod catch-up and both recipe changes remain pending an "apply" direction.


**KnightOfNight** — 2026-08-11:
Field data (2026-08-11 cleanup, operator-directed, between point releases): prod root had regrown 20%→58% (~10 releases since the July 29 cleanup); dev lima VM held 22.8GB of build cache (426 entries). Finding that sharpens this issue's fix: on BOTH daemons, 'docker image prune' reclaimed ~0B — the per-release growth is held as build-cache layer references, and 'docker builder prune -a' is what freed it (7.3GB prod, 22.8GB dev; prod root back to 20%). The deploy-target step this issue adds should therefore include a builder prune alongside the dangling-image prune, or it will ship and appear not to work. Dev deserves the same step in deploy-dev — its cache grows ~2GB/build.

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
- Created: 2026-08-08 | Updated: 2026-08-15
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


### Comments (1)

**KnightOfNight** — 2026-08-12:
Motivation sharpened (operator, 2026-08-12): re-examining the 2026-08-08 incident — the v24.16 deploy itself was NOT a surprise (players get out-of-band Signal notice of restarts; see #236 for the in-band future of that). What surprised the player was the BEHAVIOR change: inv silently stopped showing equipment. So restart warnings, however good, cannot prevent this class of report — the two channels answer different questions ('the server is bouncing' vs 'the game is different now'), and this issue owns the second one. A player can be fully warned about downtime and still believe they lost their items.

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


### Comments (1)

**KnightOfNight** — 2026-08-15:
This is a lower priority issue; it only affects character deletion which is only needed on the dev. server. If we give players the ability to reset themselves later, we can include this issue in that milestone.

## Issue #249: make verify-prod: sanctioned read-only production verification target (posture-setting contract of the #187 sibling family; fixed manage.py commands + rollback guard)

- State: open
- Author: KnightOfNight
- Labels: deployments
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-15 | Updated: 2026-08-15
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/249

### Body

## What

A third sibling in the posture-setting Deployment-target family: **`make verify-prod`** — the sanctioned path for **read-only production verification**, closing the gap ruled on #248 (the read-only twin of #187's data-action gap).

## Contract — exactly the deploy-prod / seed-prod shape

- Refuses an ambient `DOCKER_HOST`; pins the production one itself
- Flips posture, pre-flights, runs its one action, restores resting dev posture
- Partial failure leaves prod posture for a human — report, never repair
- Invoked **bare only**; same guard treatment as its siblings: settings.json PreToolUse hook (bare → prompt, embedded → hard deny), ask-entry, soft-deny line
- Lives in the Makefile's Deployment section alongside `deploy-prod` / `seed-prod`

## "Read-only," ruled (#248)

Not a shell. The target executes only **named `manage.py` verification commands** that the release itself shipped — written in-release, tested on dev, reviewed in the version PR like all code. Runtime backstop on top of review: the verification harness wraps execution in `transaction.atomic()` with a **forced rollback**, so an accidental write dies at the connection. No new Postgres roles, no infra.

## Interim (codified in Instructions v33)

Until this ships, a brief's prod-side read-only step is addressed **to the operator** (option 4 of #248): it stays in the PENDING DEPLOY-TIME ACTIONS block with the operator named as executor, and the closeout reports it **handed off, not done**. Permanent data-shape invariants belong in seed verification (they ride `seed-prod` and run on prod for free — the V24.28 ladder assertions are the model).

## Precedent

#187 (`make seed-prod`) — same box-out, same contract, built as an operator-directed process pass on main (e47bf78) with Instructions v31 codifying it. This ticket is that build's read-only sibling; expect Makefile + guard-hook + Instructions-reference changes, no game code.

Ruling recorded on #248 (operator, 2026-08-15).


### Comments (5)

**KnightOfNight** — 2026-08-15:
**Execution shape (operator-ruled 2026-08-15, ops session) — three parts, and Deployment Law forces the split:**

**Part 1 — the outer contract: standalone ops brief on main (the #187 shape).** The Makefile target, the PreToolUse guard hook, and the doc references (CLAUDE.md, closeout-skill mention) are deployment/process surface — ops territory, precedent `make seed-prod` (built as an operator-directed process pass on main, e47bf78). The target lands documented as **awaiting its first shipped verification command** — it has nothing to run until Part 2 exists.

**Part 2 — the in-container code rides an ordinary point release.** The forced-rollback harness and every `verify_*` command live under `django/src`, which is baked into the Docker image — code reaches production **only** via a release closeout's tail deploy. So the harness ships with the **first release that wants a prod-side verification step**: that release's brief carries the harness + its own verification command as ordinary brief scope, dev-tested like everything else. No dedicated release for a base class; it piggybacks. Operator's call which release that is.

**Part 3 — close the loop here.** After Part 2 ships, come back to this ticket: retire the v33 interim rule (prod-side read-only steps handed to the operator) with a one-line Instructions touch — the executor checkpoint's named-executor list then points at the live target — and close this issue. **This ticket stays open until Part 3 is done.**

Interim in force throughout: read-only prod steps name the operator as executor; closeouts report them handed off, not done (Instructions v33).


**KnightOfNight** — 2026-08-15:
**Part 1 APPLIED (2026-08-15, ops session, main).** Brief `Shyland_Brief_Verify_Prod_Target.md` born committed `2133830`, applied `28db69e`.

**Landed:**
- **Makefile:** `verify` (crosscheck-env-guarded, `VERIFY=verify_*` name gate — the dev-testing path for Part 2 commands) + `verify-prod` (exact sibling posture contract; `VERIFY` gates run **before** the posture flip, so a bad invocation never leaves resting posture; one command per invocation). Incidental fixes: `.PHONY` and `make help` were missing the production seed target.
- **Guard hook:** third PreToolUse entry — trimmed `make verify-prod VERIFY=verify_<name>` exactly → ask; anything else containing the target name → deny. Plus the ask-permission entry and the soft-deny line.
- **Docs:** CLAUDE.md (both guard enumerations + Deploy block + posture-exception list), version-closeout skill tail step.

**Verification results:**
- Dev-side gates all correct: missing `VERIFY` → usage error; non-`verify_*` name → refusal; well-formed name → Django `Unknown command: 'verify_smoke'` — the documented **awaiting-first-shipped-command** state. All nonzero exits, posture untouched.
- Hook validated on four paths (bare → ask, embedded → deny, bad VERIFY value → deny, unrelated command → untouched) — and the deny path additionally proved itself **live**: the hook hot-loaded mid-session and hard-blocked the session's own embedded validation command.

**State:** the outer contract is live and inert. Next: **Part 2** — the first release that wants a prod-side verification step ships the forced-rollback harness + its `verify_*` command as ordinary brief scope (operator's choice of release). Then **Part 3** — retire the v33 interim rule and close this ticket.


**KnightOfNight** — 2026-08-15:
**Part 2 carrier chosen (operator, 2026-08-15): the next release, founded on #235 (plunder).** Correction to the shape note above: no invariant-shaped issue is needed — the invariant worth verifying already shipped with V24.28 (#211, the tier-material ladder), and v33 only requires verification commands to be brief-shipped and dev-tested, not to verify their own release's changes.

**Action item for the #235 release's design session — include in Brief 1 scope:**

1. **The forced-rollback harness** — the shared base for `verify_*` management commands: wraps execution in `transaction.atomic()` with a forced rollback so an accidental write dies at the connection (the runtime backstop behind the `verify_*` name gate the Part 1 Makefile already enforces).
2. **`verify_ladder`** — the first verification command. Spec exists verbatim: **V24.28 Brief 1 verification step 8** (count `ItemInstance` rows sitting on a tier-material ladder definition outside their rung; expected on prod: **0**) — the exact survey that went to production unverified and spawned #248.
3. Both dev-tested in-release via `make verify VERIFY=verify_ladder` (the Part 1 dev path).
4. The release's PENDING DEPLOY-TIME ACTIONS block lists the prod run — executor: `make verify-prod VERIFY=verify_ladder`, bare single-command invocation, its own operator confirmation in the closeout tail. **First live exercise of the target**, and it retroactively settles V24.28's handed-off survey.

Then **Part 3** closes the loop here: retire the v33 interim rule (one-line Instructions touch) and close this ticket.


**KnightOfNight** — 2026-08-15:
**Part 2 carrier confirmed: Version 24.29 (2026-08-15, V24.29 design session).** The release is founded on #235 (plunder); branch `version_24_29` created, milestone `Version 24.29` opened. Part 2's scope rides **Brief 1** as ordinary brief scope, exactly as ruled above.

**Milestone composition — #249 is deliberately NOT in the `Version 24.29` milestone.** By its own Part 3 design this ticket stays open past the release, and the closeout entry gate queries *"every milestone issue closed N/N"* — adding it would deadlock the closeout of a release that did its job. The milestone holds **#235 only**; Part 2 is tracked as brief scope and by this comment. The scope law is satisfied rather than bent: one founding ticket, one brief, with the harness piggybacking per the ruling above ("no dedicated release for a base class").

**Part 2 scope as it will be written into Brief 1:**

**1. The forced-rollback harness.** Location: `django/src/apps/shyland/verification.py` — a module, not a command; `management/commands/` holds commands only. **Deliberately Shyland-scoped, not platform-shared:** a shared home would be shared surface under CLAUDE.md Rule 2 and require its own stop-and-flag, and Shyland is the only consumer today. If a second game ever needs it, it moves then, as its own decision.

Contract: a `BaseCommand` subclass that wraps the subclass's verification body in `transaction.atomic()` with a **forced rollback**, so an accidental write is discarded rather than committed — the runtime backstop behind the `verify_*` name gate the Part 1 Makefile already enforces. Verification bodies report via stdout and signal outcome by **exit code: 0 = clean, nonzero = findings or error**, so a failure is loud through `make verify` / `make verify-prod` rather than buried in output. Findings are *reported, never repaired* — no verification command may mutate, even to "fix" what it finds.

**2. `verify_ladder`** — `django/src/apps/shyland/management/commands/verify_ladder.py`, the first shipped verification command. Spec is verbatim **V24.28 Brief 1 §7 step 8**: count `ItemInstance` rows sitting on a tier-material ladder definition outside their rung. Ladder membership is `definition__tier_material_mk_min__isnull=False`; a row is mismatched when `mk_tier` is below `tier_material_mk_min`, or above `tier_material_mk_max` where that maximum is non-null (sphaerium's null maximum is unbounded and can never mismatch upward). Output on a finding: the count plus the offending definition slugs, then a nonzero exit. **Expected on production: 0** — the number V24.28 Brief 1 §8 predicted and could not confirm.

**3. Dev-tested in-release** via `make verify VERIFY=verify_ladder` (the Part 1 dev path), plus unit tests covering both the clean and mismatched cases and one proving a write attempted inside the harness does not survive.

**4. PENDING DEPLOY-TIME ACTIONS** will carry the prod run with a named executor: **`make verify-prod VERIFY=verify_ladder`**, bare single-command invocation, on its own operator confirmation in the closeout tail. First live exercise of the target, and it retroactively settles V24.28's handed-off survey.

Part 3 remains open here after this release ships: retire the v33 interim rule (one-line Instructions touch) and close this ticket.


**KnightOfNight** — 2026-08-15:
**Part 2 shipped** in V24.29 Brief 1 (branch `version_24_29`), commit `7a4fdb2`. This issue stays **open** for Part 3.

Part 1 (`28db69e`, on main) shipped the `verify` / `verify-prod` target pair and the guard hook — live but inert, with no command to run. Part 2 supplies the in-container half:

- **`django/src/apps/shyland/verification.py` — `VerificationCommand`.** A `BaseCommand` subclass extended by implementing `verify()` rather than overriding `handle()`. The body runs inside `transaction.atomic()` with a forced rollback, so any write it performs is discarded rather than committed — the runtime backstop behind the Makefile's `verify_*` name gate, and what makes pointing one of these at production safe. Exit code is the outcome signal (0 clean, nonzero findings or error, via `CommandError`), so a failure is loud through `make` rather than buried in stdout. Findings are reported, never repaired.
- **`verify_ladder`** — the first shipped command, spec verbatim from V24.28 Brief 1 §7 step 8: the tier-material survey that went to production unverified and filed #248. Ladder membership is a non-null `tier_material_mk_min`; sphaerium's null maximum is unbounded above and can never mismatch upward.

Deliberately Shyland-scoped rather than platform-shared — a shared home would be platform shared surface under CLAUDE.md Rule 2 and would need its own stop-and-flag.

**Dev results:** `make verify VERIFY=verify_ladder` → 0 mismatches out of 8 ladder rows, exit 0. Both dev-path gates behave: bare `make verify` gives the usage error, `VERIFY=seed_world` is refused by the name gate, both nonzero, posture untouched.

**Still to come:**

- The **first live exercise** — `make verify-prod VERIFY=verify_ladder`, in this release's closeout tail after `make deploy-prod`, which also settles V24.28's handed-off survey.
- **Part 3** — retire the Instructions v33 interim rule that routes read-only prod inspection to the operator, now that a session path exists, and close this issue. Ops-session work after this release ships.


## Issue #251: All config command setters should write both the cached attribute and the DB row

- State: open
- Author: KnightOfNight
- Labels: commands
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-15 | Updated: 2026-08-15
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/251

### Body

All config command setters should write **both** the cached attribute and the database row.

Today they are inconsistent (`consumers.py`):

- `_set_brief_mode`, `_set_show_timestamps`, `_set_echo_mode` — write only the DB row; the command maintains the cached attribute afterwards.
- `_set_plunder_mode` (v24.29, #235) — writes both.

The net effect is currently correct because each `cmd_*` assigns the cached attribute after its setter returns, but the cache is only right by the caller's cooperation. Any direct call to a setter leaves `self.character` stale.

**Ruling (operator, 2026-08-15): all config commands set cache and database.** `_set_plunder_mode` is the shape; bring the other three to it.

Related: #250 (the same family — `_set_echo_mode` was assigning the wrong cached attribute; fixed in v24.29 by deleting the stray line).


### Comments (1)

**KnightOfNight** — 2026-08-15:
**Note on the overlap with #250.** #250's fix *deleted* the cached write from `_set_echo_mode`; this issue will *add one back*. That is not a reversal.

The deleted line was `self.character.show_timestamps = value` — the **wrong field**, silently corrupting the cached `show_timestamps` on every `echo` change. It was removed rather than corrected because `cmd_echo` already assigned the right field afterwards, making it redundant as well as wrong.

Implementing this issue puts back `self.character.echo_mode = value` — the correct field, in the setter, so the cache no longer depends on the caller's cooperation.


## Issue #252: Briefs assert unverified facts about existing code — no gate checks a brief for technical coherence

- State: open
- Author: KnightOfNight
- Labels: none
- Milestone: none
- Assignees: KnightOfNight
- Created: 2026-08-15 | Updated: 2026-08-15
- Blocked by: none
- Blocks: none
- URL: https://github.com/KnightOfNight/games-mvc/issues/252

### Body

#251 exists because V24.29 Brief 1 contradicted itself and no gate caught it.

## What happened

§4.4 mandated `_set_plunder_mode` writing both the cached attribute and the DB row, justifying it as "matches `cmd_brief`'s shape" — **it does not**; `_set_brief_mode` writes only the row. §4.5 and §12 then stated the setters "uniformly write only the DB row," which the setter §4.4 mandates falsifies. Implementing §4.4 as written produced the non-uniform family #251 now has to clean up.

Three more inconsistencies rode the same brief (all recorded in `Shyland_V24.29_Brief_1_Closeout.txt`):

- §5 specified `sweep_corpses` returning a single list of `(text, category)` tuples; the corpse-disposal line is a room-wide `group_send`, so it cannot be one. The helper had to return a pair.
- §6.2 called the tick engine's accumulator `(char_pk, text, category, status)`; the fourth element is `event`.
- §1 is titled "Two things" and lists three.

## Root cause

**The brief asserted facts about existing code without verifying them.** Each was one file read away — `_set_brief_mode` is four lines; `_maybe_dispose_corpse` is a `group_send` in the method §5 names.

The discipline already exists in the same document and was applied unevenly: **§7.2 says "Field names, confirmed against the models"** and lists them. The other sections were written from recall.

## Why nothing caught it

No gate checks a brief for technical coherence:

- The design session writes it; there is no self-review against the code it describes.
- Committing is not review.
- The implementation session's Step 4 diffs the brief's **process** assumptions against the standing rituals (Instructions v33) — it ran, and correctly found none. It says nothing about **technical** claims.

The first check against reality was opening `consumers.py` to write code — the most expensive place to find it.

## Proposed fix

**Design side.** Every structural claim a brief makes about existing code — a function's body or shape, a tuple's members, a call site's behavior — is verified against the code when the brief is written, and the brief records that it was, the way §7.2 does. Recall is not a source. Plus one end-to-end read before commit, confirming the brief does not contradict itself.

**Implementation side.** Step 4's diff extends from process assumptions to technical claims on the load-bearing sections: confirm the code says what the brief says, and flag mismatches **before** writing anything.

Both would have caught all four before a line was written.

## Notes

Process-doc work — an ops session on the operator's ruling, landing as the next Instructions edition. No milestone assigned (design-session call).


### Comments (0)

None.

## Closed Issues — Summary Table

| # | Title | Author | Labels | Closed |
|---|---|---|---|---|
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
