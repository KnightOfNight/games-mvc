# Shyland V20 Brief 2 — Amendment 1: Timestamps Mark Events, Not Renderings

Implements GitHub issue **#56**. Amendment to the applied v20 Brief 2 (Output Envelope); does not count against the brief cap. Self-contained. **Never remove or prune any transient document** — the operator prunes.

## The bug

The envelope brief ruled *display* of the timestamp prefix by message category, but the categories were never partitioned by content. Result (playtest, 2026-07-14): look-section lines display identical stamps while `Exits:` arrives bare:

```
Exits: north, south.
[17:19:46.56] Who's here?
[17:19:46.56] Maro the Mender is here.
[17:19:46.56] Essa the Trader is here.
[17:19:46.56] a Verdant Shard is here.
```

## The ruled principle (binding)

**Timestamps mark events, not renderings.** An event happens *at a moment* and the moment is information; a rendering is a snapshot of now, and stamping its lines adds noise.

**The envelope itself does not change.** Every outbound message still carries `ts` and `seq` through the delivery choke point; the firehose tap is untouched. This amendment is display categorization only.

## The categorization (authoritative)

| Display | Content |
|---|---|
| **Stamped** | Combat lines (hits, misses, crits, kills), damage/heal/XP lines, chat and says, presence lines (arrivals, departures, connect/disconnect notices), commerce transactions (buys, sells, repairs), error-category lines, system/ambient notices (corpse decay, connection status), and — once the output & messaging brief ships them — command echoes. |
| **Unstamped** | The **entire room-rendering block**, on both entry and `look`: room name/header, description prose, `Exits:`, `Who's here?`, `What's here?`, and every occupant/item line under them. |
| **Unstamped** | **State reports** (explicit ruling): `inventory`, `equipment`, `stats`, `help`, `score`/`who`-style listings, and similar command-response reports. |

Anything genuinely ambiguous during implementation defaults to **stamped** (events are the common case for novel messages) and is listed in the closeout for review.

## Implementation

1. Introduce (or repurpose) message categories so the client can decide display without content-sniffing: at minimum a **room-rendering category** for the entire look/entry block and a **report category** for state reports, alongside the existing stamped categories. Server-side assignment only — the client renders what it is told, and never infers stamping from text.
2. Audit **every** output-producing site in the consumer and tick engine and assign its category per the table. List the full site→category mapping in the closeout.
3. Client: display the prefix only on stamped categories. The `timestamps on|off` preference (arriving in the commands brief via #45) will govern stamped categories only — note this in code comments so the commands brief lands cleanly on top.
4. Convenient obligation, do it now: the room-rendering category introduced here is exactly what the output & messaging brief's look-section work (#14) needs — name it and structure it so that brief styles it rather than re-plumbing it.

## Verification (all must pass before the doc touch)

1. The reproduction case: enter a room and `look` — **zero** timestamps anywhere in the block (name, prose, Exits, Who's here?, What's here?, occupant/item lines), on both entry and explicit `look`.
2. `inventory`, `equipment`, `stats`, `help`: no timestamps.
3. Combat produces stamped lines throughout; chat/says stamped; a sale at a ring cart stamped; corpse decay (observed out of combat) stamped; error lines stamped.
4. Envelope regression: every outbound message type still carries `ts`/`seq` (spot-check raw frames); per-connection `seq` still strictly increasing across mixed sources; reconnect still resets cleanly.
5. Screen reader pass: unchanged (timestamps were already aria-hidden; verify the recategorization didn't disturb the live region).
6. The closeout's site→category mapping covers every send site found in the Brief 2 choke-point audit, with no orphans.

Close **#56** with a closing comment referencing this amendment, gated on the checks above.

## Architecture doc touch (LAST, gated)

In `docs/shyland/Shyland_Architecture_v20.md`, update the envelope/client-rendering section: the events-not-renderings display principle, the category table above, the room-rendering and report categories, and the note that `ts`/`seq` remain universal beneath the display rule. No version bump, no file removals.

## Closeout report

Commit hash, the site→category mapping, any ambiguous-defaulted-to-stamped items, all verification results, and #56 closed.
