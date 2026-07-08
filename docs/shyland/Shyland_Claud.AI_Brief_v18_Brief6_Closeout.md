# Shyland v18 Brief 6 Closeout — Notes for the Design Chat

Source: the Claude Code session that implemented v18 Brief 6 (The Verdant Reach
World Seed, Part 2: Ridge & Crown). Status: implemented, verified, committed and
pushed — code commit `1b40395`, architecture doc updated in place and stamped
`1b40395` (docs commit `3832f5d`). **This closes the v18 implementation series
(briefs 1–6).** Final version-stamp reconciliation and GDD sync are now due in
the design chat.

## What shipped

Exactly what the brief specified, prose verbatim: the four new areas (The
Viridian Ridge, The Undercrag, Chitterdeep, Hollowcrown); all 81 rooms (the
51-room Ridge with Cragfoot, the three villages and their four warned-about
aggro offshoots, the vistas, and the Verdant Crown; the 9/10/11-room delves);
`vr-f18`'s reserved north exit wired to Cragfoot with its pending message
removed; the three ridge unarmed pools (elder variants); all 20 NPC definitions
(including the two aggressive surface variants, Old Brammel and Ridda, the
unique Verdant Sphere, the three bosses with their verbatim death messages, and
the three boss-gated minions); the five loot tables (Weaver → guaranteed Rare
weapon, King → guaranteed Rare armor, Devourer → guaranteed **Epic** accessory);
72 spawns; Ridda's five vendor rows; and the Cragfoot checkpoint plus The
Verdant Crown obelisk — the Obelisk Network's second travel source.

**Z01 stands complete at 150 rooms and 10 areas.**

Every verification step ran and passed except the one flagged below: double-run
idempotency (second run creates nothing); the full topology walk both ways
including every delve up/down pair; the aggro pattern (all four offshoot
grounds and every delve room fire on entry; the passive spine lions at vr-m19
and vr-m33 do not); all three bosses killed end-to-end against the live tick
engine (death message broadcast to the room, exactly one guaranteed drop at the
correct rarity and category, copper in range, minion respawns gated correctly
in both directions under shell-accelerated timers); the Convergence↔Crown
travel round trip including Cragfoot's destination-only refusal; `list`/`buy`
against Ridda and `repair` against Old Brammel; the XP spot checks (90 / 54 /
300); and the existing test suite (20/20).

## Flagged items

1. **Verification step 6's "verify the accessory rolls 3 secondary stats" is
   unsatisfiable as written — decision needed at closeout.** The GDD's rarity
   table says Epic carries 3 secondary stats, but Brief 1 authored all twelve
   copper accessories with **2-entry** `secondary_stat_pool`s (the primary stat
   plus two themed secondaries), and the drop machinery draws without
   replacement, capped at pool size. An Epic copper accessory therefore rolls
   its full pool of **2** secondaries — which does put **3 stat lines total**
   on the item counting the primary, and that may be what the design intended
   to count. Implemented data was left untouched (enlarging twelve stat pools
   is a balance/design change outside this brief's mandate); the guaranteed
   Epic drop itself, its rarity weights, and the full-pool roll all verified.
   Recorded in the architecture doc's Known Issues. The design chat should
   either (a) bless the "3 stat lines total" reading and adjust the GDD table's
   framing for small-pool items, or (b) author a third secondary for each
   copper accessory in a follow-up brief.

2. **Minion `combat_tier` was inferred, not specified.** The brief's minion
   table gives stats ("as elder-cave-X, VIT n"), scaling factor, and pool, but
   no tier column. Brief 5's minions inherited their stat donor's tier, so the
   Brief 6 minions shipped as `elite` (their elder-insect donors are elite;
   Brief 5's were normal). The field is currently display-only — no mechanics
   ride on it — so this costs nothing to change if the design says otherwise.

3. **Loot-table display names were authored in-session.** The brief specifies
   table slugs only; the human-readable `LootTable.name` values shipped as
   "Ridge Gear", "Ridge Hunter Gear", "Undercrag Weaver Loot", "Chittering King
   Loot", "Crowned Devourer Loot". Admin-facing only.

4. **GDD §9 needs no change.** Brief 6 shipped no new player commands — all
   interaction runs through the existing movement, combat, commerce, and
   `travel` verbs.

## For the closeout checklist

- The architecture doc (`Shyland_Architecture_v18.md`, header hash `1b40395`)
  already records the completed zone, the full ridge/delve seed inventory, the
  re-baselined verification numbers, and the Epic-accessory flag — the GDD side
  of the sync can be written from its §1 overview and §4.8 brief-6 block.
- The Obelisk Network now has two sources (The Convergence, The Verdant Crown)
  and three checkpoints (Fordwatch, Stairhead, Cragfoot); revelation-by-visit
  behaves per GDD 2.11 with no deviations.
- No migrations shipped in briefs 5–6; the entire Verdant Reach is seed data.
