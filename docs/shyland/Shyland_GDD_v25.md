<!-- GENERATED FILE - DO NOT EDIT.
     Built by `make gdd` from the section files in docs/shyland/gdd/.
     Edit the section files; the sections are authoritative if this file ever disagrees. -->

# Shyland — Game Design Document

**Version 25.9 — Closed**

-----

## Version History

| Version | Architecture Doc | Summary |
|---------|-----------------|---------|
| v1      | —               | Initial document. Vision, world model, character system, combat outline, economy, social systems, quest system, command reference, technical architecture. |
| v2      | —               | Area model added (Zone → Area → Room hierarchy). Breadcrumb format settled. Room header format defined. |
| v3      | —               | Item system designed: ItemDefinition/ItemInstance split, Mk tier system, rarity, durability, cursed items, identification system, effect vocabulary, bags, inventory display rules. |
| v4      | —               | Currency system designed: single copper BigIntegerField, tier table, zone aliases, display rules. |
| v5      | —               | NPC model placeholder. Loot system stub. |
| v6      | —               | Soulbind rules clarified (on equip, not pickup). Admin gifting flow added. |
| v7      | —               | Effect system expanded. EffectDefinition/EffectInstance documented. Consumable use rules. Cursed item interaction with effects. |
| v8      | v8              | NPC and corpse model designed: NpcDefinition, NpcInstance, Corpse, LootTable, LootTableEntry. Loot command designed and documented. Examine command extended to cover live NPCs and corpses. Currency drop formula (min × mk_tier to max × mk_tier). Corpse decay constant (10 minutes). Section 5.9 substantially expanded. |
| v9      | v9              | Version bump to match architecture doc. Version history added. No design changes. |
| v10     | v10             | Combat system v1 implemented. Acuity scale changed to float 0.1–1.9 (the value IS the damage modifier). Death & Resurrection section updated with exact v1 mechanics. Combat initiation updated: NPC aggro on room entry fires after a 3-second warning window; player can queue during window. Flee updated: directional preference (reverse of entry direction), DEX+d20 vs average NPC PER, cooldown after failed attempts. NPC effect system added: `NpcEffect` model links effect definitions to NPC definitions with per-effect probability. Section 5.3 action economy updated to reflect two-path command handling (non-combat commands fire immediately; combat commands queue to DB for tick engine resolution). Section 10.4 tick architecture updated to match actual implementation. Section 10.5 persistence model updated: active combat state moves from Redis to PostgreSQL. Future Systems table updated: Combat System removed; NPC System row updated; new deferred items added. |
| v11     | v11             | Effects ticking, level-up, and stat spending implemented. Section 3.5 updated: XP threshold formula (`level² × 100`) now implemented; `spend <stat> <amount>` and `stats` commands live; bar recalculation formula confirmed (`vitality_max = END×10 + STR×3 + level×5`; `longevity_max = END×8 + WIS×5 + level×5`). Section 4.2 Acuity drift note updated: passive drift toward Origin baseline is now implemented. Section 9.1 implemented commands updated: `kill`/`attack`, `flee`, `stats`, `spend` added. Section 9.2 planned commands updated: `kill`/`attack` and `flee` removed. Section 10.4 tick architecture updated: `process_effect_expiry()` replaced by `process_effects()` with three phases (effect ticking, passive Acuity drift, expiry). Section 12 Future Systems updated: Level-Up Trigger, Acuity Drift, and DoT/HoT Per-Tick Application rows removed. |
| v12     | v12             | Effect system redesign. `EffectDefinition` is now a pure container; all behavior lives in child `EffectComponent` rows. `EffectInstance` is now a container with child `EffectComponentInstance` rows storing per-component magnitude, expiry, and lifecycle state. New `effect_utils.py` centralizes all effect application logic. Mk tier scaling: `magnitude = magnitude_base + (magnitude_scaling × mk_tier)`; `duration = duration_base + (duration_scaling × mk_tier)`. Instantaneous components have `duration_base=0`, `duration_scaling=0` — no `EffectComponentInstance` row created. Reapplication: same or higher Mk tier resets; lower Mk tier ignored silently. Expiry messages: one per parent `EffectInstance` if all components expire together; one per component if staggered. `make db-reset` Makefile target added. Section 6.9 rewritten to reflect new model structure. Section 10.4 tick architecture updated: `process_effects()` now queries `EffectComponentInstance` rows. Section 12 Future Systems: effect system redesign row removed. |
| v13     | v13             | Three bug fixes (status bar maximums added to payload, `format_wallet()` select_related corrected, combat status `room_name` fixed) plus four features: `brief` toggle implemented; `Origin` and `Archetype` promoted from CharField choices to full models; `UnarmedMessagePool` and `UnarmedMessage` models introduced; unarmed combat wired as an explicit feature with random flavor messaging. Section 3.2 updated: Origin is now a model owning Acuity baseline and band values. Section 3.3 updated: Archetype is now a model owning primary stats and unarmed message pool FK. Section 4.2 updated: Acuity defaults now read from `Origin` model; `_ACUITY_DEFAULTS` dict removed. Section 5.2 updated: room description on combat entry is intentionally suppressed — design decision, not a bug. Section 5.4 updated: unarmed combat documented explicitly. Section 9.1 updated: `brief` command added. Section 9.3 updated: boolean command rule added. Section 10.4 updated: status payload now includes bar maximums and Acuity band bounds. Section 12 Future Systems: Brief Toggle row removed; unarmed pool customization rows added. |
| v14     | v14             | Passive out-of-combat regeneration implemented for Vitality and Longevity. Section 4.1 updated: Vitality recovery description now specifies the regen formula and gate conditions; Machinekind note updated (passive regen applies via nanomachine narrative). Section 4.3 updated: Longevity recovery description updated to reflect passive regen now implemented, with its 30× slower rate noted. Section 10.4 updated: `process_effects()` now has four phases; Phase 4 (passive bar regeneration) documented. |
| v15     | v15             | World-building schema additions. `NpcDefinition` gains `combat_tier` field (Normal/Elite/Champion/Boss/World Boss). `RoomSpawn` model introduced as the authoritative source of truth for NPC population; tick engine `process_npc_respawn()` rewritten to use it. `VendorEntry` model introduced linking NPC definitions to items with explicit copper prices, enabling vendor authoring before buy/sell commands exist. `ZoneGate` model introduced for fast-travel configuration, enabling gate authoring before the travel command exists. Per-direction blocked exit messages added to `Room` — six optional fields allowing builders to override the generic "no exit" response per direction. Section 2.4 updated: blocked exit messages documented. Section 2.6 updated: zone gates now have a schema backing. Section 5.9 updated: `combat_tier` documented; `RoomSpawn` documented; respawn description updated. Section 6.12 updated: `VendorEntry` model noted. Section 10.4 updated: `process_npc_respawn()` now `RoomSpawn`-driven. Section 12 updated: Room Spawn Configuration row removed; new deferred rows added for buy/sell commands, zone gate travel command, and combat tier behavior. |
| v16 RC1 | v15 (unchanged) | In-game character creator design finalized (implementation pending — this is a working draft, more changes expected before closing to v16). Section 3.1 rewritten: creation flow is now Origin, Archetype, and Name only — **portraits are permanently cut, not just deferred**. Entry gating rule added: a player with no character who presses play is routed to the character creator and can do nothing else except return to the game system's front page — no partial access to the world. Name now defaults to the player's `user.profile` gamer tag; players may override it with a custom name. The profanity filter only runs against overridden names (the default gamer tag is assumed already vetted elsewhere) and must use a well-maintained public library rather than a hand-rolled wordlist, consistent with the project's general preference to reuse existing solutions over writing new ones. Section 12 updated: In-game Character Creation row rewritten to reflect finalized design pending implementation; portrait reference removed. |
| v16 RC2 | v15 (unchanged) | Starting stat formula and Origin/Archetype description text authored (character creator design continues; still a working draft). Section 3.2 updated: each Origin now has full flavor-text description content, written for the `Origin.description` field which has been blank since v13. Section 3.3 updated: each Archetype now has full flavor-text description content, written for the `Archetype.description` field, also blank since v13. Section 3.4 updated: starting stat formula settled — every stat begins at a flat baseline of 8; each Archetype's two named primary stats are raised to 18 instead. No Origin-based stat modifiers — Origin's mechanical identity is carried entirely by Acuity baseline/band and passive trait, not by the six core stats. This keeps starting values inside the existing 8–18 range from prior versions. Section 12 updated: Origin and Archetype Descriptions row marked resolved in design (content authored here); pending is seeding the text into the database via migration or fixture. |
| v16 RC3 | v15 (unchanged) | Remaining character creator open items settled (working draft continues). Section 3.1 updated: one character per account (a player has exactly one Shyland character tied to their account — no character slots or alts); spawn point on creation confirmed as Heart of the Convergence (0,0,0), the same room used as the default recall destination; character name length matches the existing `UserProfile.gamer_tag` constraint (max 20 characters), since the name defaults to and can be validated against that same field; the creation form allows the player to change any field (Origin, Archetype, name) as many times as they like before final submission — nothing is locked in until submit; "return to front page" is defined as navigating to the game system's root URL (the multi-game lobby), not just closing the creator. Starting decorative clothing remains an open item — a formulaic proposal (Origin material/palette + Archetype garment silhouette) is under discussion but not yet confirmed, so it is intentionally not yet written into this section. |
| v16 RC4 | v15 (unchanged) | Starting attire settled — final open item for the character creator design (working draft continues; one item remains open — see below). Section 3.1 updated: every new character is dressed in purely decorative starting clothing described by a formula — an Origin material/palette phrase combined with an Archetype garment-silhouette phrase — rather than 49 hand-authored combinations. This clothing occupies no equipment slot, has no stats, and is not an `ItemDefinition`/`ItemInstance`; it exists as generated flavor text only. Full phrase tables for all seven Origins and seven Archetypes are included. **Still open:** name-uniqueness check timing (live validation as the player types vs. checked only on submit) has not yet been decided. |
| v16 RC5 | v15 (unchanged) | Final open item resolved — **the character creator design is now complete and ready for a Claude Code brief.** Section 3.1 updated: name uniqueness is checked in real time as the player types (not only on form submit), giving immediate feedback before they attempt to finalize the character. This is the last remaining decision from the character creator design pass that began in this chat; no open items remain for this system. |
| v16.0   | v16 (commit `05c634a`) | **Character creator implemented, verified, and closed out.** This version folds the full v16 RC1–RC5 working-draft design together with four refinements that emerged during implementation and a documentation audit of stale v15 passages the working draft hadn't reached. Implementation refinements (Section 3.1): the profanity exemption is narrower than originally designed — it applies only to a kept, *set* gamer tag; a player with no gamer tag falls back to their username, which has no upstream vetting, so that default IS profanity-checked even when submitted unchanged. The default name is truncated to 20 characters when necessary (usernames can run up to 150 characters; gamer tags are already capped at 20). Name uniqueness is case-insensitive and enforced by a database-level constraint on every write path, including Django admin — the real-time as-you-type check is an advisory courtesy layered on top, not the authoritative gate. `Character.name` is permanent once set at creation and independent of later gamer-tag changes — this reverses the pre-v16 behavior where the displayed name tracked the profile live. Documentation-audit fixes: Section 10.1 Auth row updated to reflect `Character.name` as its own field rather than sourced live from `user.profile.gamer_tag`. Section 12 (Future Systems): removed the "Origin and Archetype Descriptions" and "In-game Character Creation" rows entirely (both fully shipped); added a new row noting that starting-attire flavor text is seeded but not yet rendered anywhere in-game. |
| v17.0   | v17 (commit unchanged) | **Infinity City world seed implemented and closed out.** No model changes. No new commands. Content-only version. The Convergence zone (Z05) is now fully seeded with its first-version map: 4 path areas (Wisteria Walk, Bamboo Run, Basalt Way, Fern Boards), 54 rooms, and 9 NPC definitions. The starting room is Heart of the Convergence at (0,0,0), anchored by the Obelisk. Four winding park paths lead outward to a 35-room ring street surrounding the park. Seven sealed zone gates are placed clockwise on the ring street from north, one per future battle zone, each with atmospheric sealed-exit flavor text. Four information NPCs (Aldric, Info Prime, Pella, Seris) are placed at cardinal ring/path intersections; The Obelisk serves as a fifth information point at the center. Four vendor NPCs (Morra the blacksmith, Repairbot Prime, Ferwick the magician, Veris the crystal vendor) are placed across the ring from their paired information NPCs. Morra has her own smithy building (2 rooms: exterior + interior). All other vendors occupy open-air positions in ring street rooms. All Convergence rooms have `flag_safe=True`. Placeholder world content (The Fracture Point plaza and its 4 connected rooms, goblin scout, training dummy, fracture wraith) removed. Section 2.1 updated to reflect the settled Convergence lore. Section 2.5 updated: Infinity City documented as the starting area within The Convergence zone. Section 12 updated: zone content placeholder row replaced with specific note on what is and isn't yet built. |
| v18 RC1 | v17 (unchanged) | **The Verdant Reach (Z01) zone design complete** (implementation pending — working draft). New Section 2.10 captures the full design: 150 rooms (101 surface / 49 cave), levels 1–10, three surface Areas in spine order (Fernwater Vale ~30 rooms / The Sagewind Flats ~20 / The Viridian Ridge ~51, a 30/20/50 split that doubles as the leveling plan) plus seven cave Areas on a logarithmic room curve (1/4/6/8/9/10/11). Maze-with-a-spine layout — linear progression, not linear geography. Zone doubles as a movement tutorial: valley-wall caves → plains sinkholes teaching `down` → three-dimensional mountain delves. Surface creatures all passive except flagged mountain-offshoot aggressors; all other aggro lives in the caves (spiders, giant centipedes, flying giant beetles). Six bosses (caves 2–7) with minions, on a weapon→armor→trinket drop rotation and an Uncommon (2–4) → Rare (5–6) → Epic (7) rarity ladder; Legendary excluded from the zone. Boss loot delivered via narrative chest death-flavor over standard corpse-loot mechanics. Animals drop XP plus generic Animal Hide rolls (insects: Insect Carapace); villagers are the money/gear source. Five-plus villages (Reedmere, Windhome, Stonestep, Highfold, Lastlight), 1–3 rooms each, villages always preceding mountain caves. Entrance: five atmosphere rooms ending at a river; fog-lift valley reveal on crossing. Act seams: five-room ancient stair (Vale→Flats), one-room boulder field (Flats→Ridge). Three checkpoints at act thresholds (Fordwatch, Stairhead, Cragfoot) hosting service NPCs — established as a zone-wide pattern. Zone terminus: The Verdant Crown, an impossibly green summit garden holding a green-sphere obelisk — establishing the every-zone-ends-in-an-obelisk pattern, with obelisk NPCs providing return travel to any obelisk or checkpoint, and the Heart of the Convergence Obelisk retroactively gaining the same workings. MUD-traditional shared world confirmed (no instancing); respawn table set (bosses 10 min, villagers 5, everything else 1). Section 12 updated: Battle Zones row rewritten; new rows added for the checkpoint/obelisk fast-travel network session, outleveled-content XP reduction, and hide/carapace crafting. **Still open before the implementation brief:** checkpoint/fast-travel mechanics session, room-by-room layout doc, XP pacing check, trinket category verification. |
| v18 RC2 | v17 (unchanged) | **Checkpoint & fast-travel design complete** (working draft continues). New Section 2.11 — The Obelisk Network — captures the full design: checkpoints are destinations only; obelisks are sources and destinations; the network is global with no zone scoping (cross-battle-zone travel allowed by design — one flat rule, *destination revealed? travel permitted*). Revelation is per-character and permanent, triggered by seeing the node's room; the Heart of the Convergence reveals at first login but the destination list starts empty. Travel is a simple command — `travel` lists revealed destinations, `travel <destination>` goes, obelisk rooms only, no dialogue system required. Travel is free forever: a gift from the obelisks, earned through revelation. All checkpoint and obelisk rooms are safe rooms in every zone because of obelisk presence — projected in spirit to checkpoints, manifested there as a **Shard**: a free-floating sphere named per zone (a Verdant Shard in Z01), with a mood expressed purely in text, indestructible and non-interactive, the only checkpoint-specific artifact the obelisk placed. Everything else at a checkpoint is natural local evolution — service NPCs are locals who followed the foot traffic. Travel messaging: the obelisk speaks no words; traveler and witnesses at both ends see randomly selected themed messages. Section 2.6 updated: obelisk network added to special travel options. Section 2.10 updated: parked-mechanics language replaced with references to 2.11; checkpoint blocker removed from the zone's open items. Section 9.2 updated: `travel` command added to planned commands. Section 12 updated: Checkpoint & Obelisk Fast-Travel Network row rewritten — design complete, implementation mapping questions (ZoneGate relationship, RoomVisit reuse, message pool machinery, Shard representation) deferred to brief time. **The Verdant Reach implementation pipeline is now unblocked**; remaining before the brief: room-by-room layout doc, XP pacing check, trinket category verification. |
| v18 RC3 | v17 (unchanged) | **Terminology settled and item inventory verified against the repo** (working draft continues). "Accessory" is the real item-type word for the third boss-drop category; "trinket" is a conversational alias only and never appears in code, data, or authoritative design text. Section 2.10 rotation updated to weapon → armor → accessory, with the note that accessories fill the NECK and RING (×2) slots, making the full-set hunt a concrete checklist. Repo check findings recorded in Section 2.10 open items: the `ACCESSORY` type exists in the model and exactly one accessory ItemDefinition is seeded (Copper Ring — RING slot only, no NECK item); armor definitions cover only CHEST (Leather Vest, Ballistic Jacket); weapons are the only slot-complete pool. Consequence: a fantasy-genre **Mk 1 item kit covering all equipment slots is a prerequisite for the zone and will be its own focused brief**, separate from the world seed. Remaining before implementation: Mk 1 item kit brief, room-by-room layout doc, XP pacing check. |
| v18 RC4 | v17 (unchanged) | **Mk 1 item kit design complete** (working draft continues). New subsection in 2.10 — The Mk 1 Item Kit — Leather: plain uniform set, no proper nouns, ~24 new ItemDefinitions. Armor: six new Leather pieces (Cap, Shoulders, Gloves, Belt, Leggings, Boots), all END-anchored with slot-flavored secondary pools; existing Leather Vest adopted. Wooden Shield added (armor-typed, OFF_HAND, END anchor). Weapons: Iron Mace (1H), Broadsword (2H, steady), Battle Axe (2H, swingy — same budget as Broadsword, spread 8 vs 5), Hunting Bow (2H ranged); two-handers run ~45% above one-handers; no technology weapons in Z01 and the Pulse Pistol is excluded from Z01 drop tables; every Archetype is covered by the zone's loot. Accessories: copper only in Zone 1 — Copper Ring of `<stat>` ×6 and Copper Amulet of `<stat>` ×6, each stat variant its own ItemDefinition, suffix stat as sole primary, rarity carrying benefit variance; existing generic Copper Ring absorbed as Copper Ring of Wisdom. Section 6.3 gains the **tier-material naming rule**: tier materials (copper/silver/gold/platinum, tracking the currency ladder) suppress the Mk display suffix — display alias only, engine untouched; flavor materials (iron, wood, leather) do not suppress. Section 3.6 gains the **handedness design rule**: conflicting equips always refuse with a message, no silent auto-unequips, player manages exchanges. Repo verification recorded: `is_two_handed` already exists in model, seed, and equip logic (Apprentice Staff already two-handed; refuse-and-message already implemented) — handedness is *not* a new mechanic and no migration is needed; one gap found (off-hand equip while wielding a two-hander incorrectly succeeds) and its `consumers.py` fix is assigned to the kit brief. Remaining before implementation: item kit brief (ready to write), room-by-room layout doc, XP pacing check. |
| v18 RC5 | v17 (unchanged) | **Equip exchange rule revised — refuse-always replaced by one-for-one auto-swap** (working draft continues). Section 3.6 rewritten: when equipping, count the items that must come off — zero equips normally; exactly one (unambiguous) auto-swaps in a single messaged exchange (never silent); two or more refuses naming what to unequip; exactly one but ambiguous refuses naming the candidates (canonical case: both RING slots full — the ring exception; also any multi-slot item facing all-occupied slots, e.g. a knife with both hands full). Rule is general across all equipment slots. Accepted edge case recorded as intended: two-handed weapon + equip shield auto-swaps, leaving no weapon. Auto-swap respects existing unequip constraints — cursed items and carry-limit-violating bag displacement refuse. **All bows are two-handed for now** recorded in 3.6 and the kit subsection. Section 2.10 kit subsection handedness paragraph rewritten to match; the two code gaps found in RC4 review are subsumed by the exchange-rule rewrite carried in the item kit brief. The item kit brief (Brief 1 of the v18 series) was rewritten accordingly. |
| v18 RC6 | v17 (unchanged) | **Obelisk Network implementation mapping settled; Brief 2 produced** (working draft continues). Section 2.11's open-for-brief-time list replaced with settled rulings: `ZoneGate` superseded and removed (wrong shape — pairwise edges vs. node membership); revelation derived from `RoomVisit` with no new per-character table; dedicated `TravelMessage` model with traveler/departure/arrival pools; Shards represented as non-aggressive NPC definitions (zone seed content, not network machinery); and the Heart of the Convergence gains a white Sphere NPC for examine parity — the Convergence sphere didn't predate the zone-end sphere pattern, it started it. The Heart is registered as the network's first node ("The Convergence", obelisk-type). `Shyland_Brief_Obelisk_Network.md` produced as Brief 2 of the v18 series. |
| v18 RC7 | v17 (unchanged) | **Battle-zone engine mechanics settled; Brief 3 produced** (working draft continues). Repo verification first, with a correction to the RC1-era record: the respawn engine already exists in full (`RoomSpawn` population config, tick-engine refill, per-definition `respawn_minutes`, 2× dead-instance cap) — the Reach's respawn table is pure seed data, not new machinery. Four mechanics settled: **(1) Boss-gated minion spawns** — a spawn can require a living NPC of a given definition in its room; boss minions respawn every **3 minutes** while the boss lives (revised from 1 minute — too fast for a team to kill the boss between waves), reinforcements stop when the boss dies, and the encounter resets as a unit when the boss respawns at 10 minutes; respawn table updated. **(2) Guaranteed-group loot** — loot table entries carry an optional group label; each group yields exactly one weighted pick per kill (boss rotation guarantees), ungrouped entries roll independently as before; rarity floors are seed data via rarity weights. **(3) Per-NPC `death_message`** — single authored text field, blank by default, broadcast once to the room at death: the narrative chest's delivery mechanism (a boss's reveal is a staged beat, deliberately not a randomized pool). **(4) Outleveled XP reduction — in v18, not deferred:** full XP within the NPC's Mk band, −20% per level beyond the band top, 10% multiplier floor, absolute minimum 1 XP; never zero, always give them something; Section 12 row rewritten as designed-and-in-v18. `Shyland_Brief_Engine_Mechanics.md` produced as Brief 3 of the v18 series (three one-field model changes with migrations; no zone content). |
| v18 RC8 | v17 (unchanged) | **Layout DD produced and approved; commerce joins v18; all layout blockers ruled** (working draft continues). `Shyland_Verdant_Reach_Layout.md` produced as an intermediate design document (DD) between the GDD and the seed briefs: all 150 rooms keyed, named, and wired; full NPC roster with approved balance (`scaling_factor = level`, bosses `level × 3`; ~475 average kills 1→10 — XP pacing check passed); six bosses named with approved death-message chest reveals; insect tiers cave/giant cave/elder cave; loot tables including guaranteed groups; checkpoint service NPCs, vendor inventories, and prices; TravelNodes and Verdant Shard placements. Blocker rulings: **commerce (buy/sell/repair + item valuation) is in v18 as its own brief**, applied before the world seed — the v18 series grows to five briefs (item kit → obelisk network → engine mechanics → commerce → world seed); a **`material` item type** is approved for Animal Hide / Insect Carapace; **animals drop no copper** — only higher sentient species carry money. Naming ruling: the Convergence's sphere is **the Primordial Sphere** (it didn't predate the zone-end sphere pattern, it started it); zone-end spheres are named for their zones (the Verdant Sphere at the Verdant Crown); Brief 2 updated accordingly. Commerce design Q&A opened. |
| v18 RC9 | v17 (unchanged) | **Commerce fully designed; Brief 4 produced** (working draft continues). Section 6.12 extended with the settled system: authored `base_value` on every ItemDefinition; item value = base × Mk × rarity multiplier (×1/×2/×4/×8/×16/×32 Common→Artifact); vendors pay exactly one third (minimum 1 copper); vendor buy prices remain authored `VendorEntry` data; vendor purchases are always Common; only unequipped items sell and **soulbound items CAN be sold** (compensated disposal — the instance is deleted, vendors never resell, the no-trading pillar untouched; cursed items are unsellable for free via the unequip rule); repair is paid per attempt with harmless failure, cost = value × missing durability × 50%, success = 20% + current durability × 75%, success restores 100%, items never destroyed; command set `list`/`buy`/`sell`/`repair` with `repair` bare form walking the most-damaged item, `repair all` batch semantics, and automatic routing (living vendor / living repairer via new `is_repairer` flag). Materials confirmed as an item type; Animal Hide (6cp) and Insect Carapace (8cp) defined; base_value back-fill table authored for all existing definitions. **Combat QoL settled:** targetless `attack`/`kill` auto-targets the first attacker, only while under aggro. Section 9.2 updated with the five command entries. `Shyland_Brief_Commerce_and_Combat_QoL.md` produced as Brief 4 of the v18 series (four model fields, one migration run, no zone content). The v18 series now stands: Briefs 1–4 complete; only the world seed remains. |
| v18 RC10 | v17 (unchanged) | **World seed briefs produced; full cross-check complete — v18 planning is done.** `Shyland_Brief_Verdant_Reach_Seed_Part1.md` (Brief 5a: entrance, Fernwater Vale, ancient stair, Sagewind Flats, caves 1–4, Fordwatch and Stairhead, Reedmere and Windhome, three bosses — 69 rooms with full authored prose) and `Shyland_Brief_Verdant_Reach_Seed_Part2.md` (Brief 5b: the Viridian Ridge in three legs, Stonestep/Highfold/Lastlight with warnings written into their prose per R7, four aggro offshoots, the three delves, Cragfoot, the Verdant Sphere, and The Verdant Crown as the network's second obelisk source — 81 rooms) produced per the approved DD, with room prose unreviewed by design under the creative-content policy. **Cross-check pass performed across all six briefs** (automated exit-pairing, coordinate, slug, and rarity-weight checks plus a full manual read): exit pairs all correct; all rarity weight sets sum to 100; all item references resolve to Brief 1 / pre-existing slugs. Eight fixes applied: five coordinate collisions corrected (the Drone Pit shifted to its own x-column; The Lion's Backyard and The Crag Shelf moved off occupied coordinates); Brief 2's combat-tier placeholder replaced with the verified `'normal'` value; Brief 4's vendor `list` formatting corrected to definition-based (the instance display helper doesn't apply to VendorEntry rows); slug-resolution notes added to both seed briefs' loot sections. **The v18 series is final: Briefs 1 → 2 → 3 → 4 → 5a → 5b, ready to apply in order.** Next: implementation via Claude Code, then closeout (architecture doc v18 upload, GDD v18.0 release). |
| v18 RC11 | **v18 (commit b2d0914)** | **Brief 1 (Mk 1 Item Kit) implemented, verified, and pushed** — the architecture doc is now `Shyland_Architecture_v18.md`, updated in place by subsequent briefs. Closeout notes processed, with corrections to this document's record: **the kit contains 4 new weapons, not 5** — the five approved additions were four weapons plus the armor-typed Wooden Shield, and the brief's Context miscounted ("5 weapons", "23 net-new"); Part D was always correct and complete, actual result 22 net-new rows (11 → 33 definitions, legacy Copper Ring absorbed in place), **nothing is missing and no follow-up brief is needed**. Kit subsection arithmetic corrected accordingly. **Slot capacity recorded in 3.6:** exactly two RING slots, one of everything else — the design already said RING ×2 but the v17 code had a single ring slot; Brief 1 added the capacity mechanism (`SLOT_CAPACITY`), documented in the architecture doc. Also shipped per closeout notes: generic ambiguous-refusal wording ("or"-joined, matching the ring case's shape), eleven accessory descriptions authored in-session under the creative-content policy, an admin fieldset fix for `suppress_mk_suffix` visibility, and the scope line that only player-facing display uses `get_display_name_with_tier()` (admin/debug strings unaffected). Dev database was rebuilt to a clean v17 baseline before implementation (environment note; no design impact). Briefs 2–6 pending. |
| v18 RC12 | v18 (commit 74ca44e) | **Brief 2 (Obelisk Network) implemented, verified, and pushed** (code commit 5c01351; architecture doc hash-stamped 74ca44e, updated in place). The network is live: `ZoneGate` deleted (migration 0019), `TravelNode` and `TravelMessage` added, the `travel` command shipped with all brief-verbatim strings plus a help entry, the Primordial Sphere seeded at the Heart, and "The Convergence" registered as the network's first node. Full travel loop verified in-container (18/18) including real witness broadcasts. **§9.1 updated: `travel` (both forms) moved from planned (§9.2) to implemented**, per the single-source-of-truth convention. Closeout notes recorded: the `ZoneGate` name survives only in immutable migration history (0016/0019) — live code is clean; NPC placement is spawn-row based as the seed intends; and **the recall command was never implemented** — it remains planned in §9.2, the Brief 2 regression step's reference to it was this document's authoring error, and §2.11's "three ways out" now carries a recorded note that deep-zone players have two ways out until recall ships (accepted for the Reach's launch). Briefs 3–6 pending. |
| v18 RC13 | v18 (commit 8ad567c) | **Brief 3 (Engine Mechanics) implemented, verified, and pushed** (code commit b686093; architecture doc updated in place). All four battle-zone mechanics live, fully data-driven with no Z01-specific logic: boss-gated spawns (`RoomSpawn.requires_living_npc`, one exists() query per gated spawn, ungated spawns query nothing), guaranteed-group loot (partitioned rolls, exactly one weighted pick per group, verified at 50 rolls with 33/11/6 tracking the 6:3:1 weights), per-NPC `death_message` (broadcast once after the kill line, blank = byte-identical output), and outleveled XP (worked table passes exactly, including the min-1 guard). **One code deviation, correctly made:** the brief's verbatim `int(base × multiplier)` disagreed with its own worked table due to binary floating point (0.20×3 → 0.39999…), paying 3/1 XP where the table promised 4/2; Claude Code treated the worked table as the authoritative gate and added a commented `round(…, 9)` before truncation — the discrepancy was this document author's error, and the resolution priority (tables over prose/code) is the standing rule. Engine quirk recorded in the architecture doc: the pre-existing 2× dead-instance cap gives a count=1 spawn one buffered instant replacement, relevant to spawn-test choreography only. Migration 0020; image rebuilt with migration baked in; all five containers stable. Briefs 4–6 pending. |
| v18 RC14 | v18 (commit ce502b3) | **Brief 4 (Commerce & Combat QoL) implemented, verified, and pushed** (code commit 97f3732; architecture doc updated in place). Commerce is live: migration 0021's four fields, valuation helpers verified to the copper (broadsword 200/66, Epic amulet 240/80, repair 18cp at 50%), materials seeded, base_value back-filled with a seed-verification check that nothing sits at the migration default, and all four commands routed to living vendors/repairers. Beyond-brief additions, all correct: **money movement is atomic with row locks** (no double-spend or oversell on finite stock), the stale VendorEntry docstring note was removed, and the seed's built-in verification grew two commerce checks. Targetless `attack`/`kill` resolves the first attacker via combat-session insertion order. **§9.1 updated: a Commerce table added (`list`, `buy`, `sell`, all three `repair` forms) and the bare `attack`/`kill` auto-target row added to Combat; all five entries removed from §9.2.** Display ruling at closeout: **materials keep their Mk suffix** ("Animal Hide Mk 1") — `base_value × mk_tier` makes a Mk 3 hide worth 3× a Mk 1 hide, and the suffix is the only visible signal of that difference; the tier-material suppression rule stays narrowed to the metals whose names already encode tier. Briefs 5–6 pending. |
| v18 RC15 | v18 (commit e68f022) | **Brief 5 (Verdant Reach Seed Part 1) implemented, verified, and pushed — Shyland's first battle-zone content is live and playable** (code commit 973a07d; architecture doc updated in place). The zone, 6 areas, and all 69 rooms seeded with verbatim prose; exits wired both ways from a one-way edge list; the Verdant gate opened off the ring street; 6 unarmed pools, 29 NPC definitions (bosses with death messages, the game's first vendors and repairers, the Verdant Shard), 7 loot tables including the three guaranteed-group boss tables, 57 spawns (three gated), 8 vendor entries, and the Fordwatch/Stairhead travel nodes. End-to-end verification against the live ticker: the 31-step spine walk with the fog reveal, aggro-in-caves/none-outside, the full commerce loop at Fordwatch, obelisk travel to both checkpoints, the Silk Matron's complete boss cycle (death message, exactly one Uncommon weapon, 50–150 copper, brood gating), and villager loot/respawn. **Two record corrections from closeout deviations:** (1) the Z01 Zone row never existed — this document's Brief 5 premise that the Infinity City seed created it was wrong; the brief's own get_or_create instruction handled it harmlessly, and the seed now creates the zone. (2) **The respawn engine was never actually working** — `process_npc_respawn` counted live instances only, so `respawn_minutes` was meaningless (every kill refilled next tick) and boss-minion gating could not engage naturally; RC7's "respawn engine already exists in full" was an overcorrection, and Brief 3's gate verification passed only via hand-driven timers. Fixed at Brief 5: dead instances hold their slot until their timer clears, making the approved respawn table (bosses 10 / villagers 5 / minions 3 / others 1) real for the first time. Also fixed: re-seeding no longer teleports Verdant Reach players back to the Heart. Brief 6 pending — the Ridge, three delves, and the Crown complete the zone. |
| v18 RC16 | v18 (commit 1b40395) | **Brief 6 (Verdant Reach Seed Part 2) implemented, verified, and pushed — the v18 implementation series (Briefs 1–6) is COMPLETE and Z01 stands whole: 150 rooms, 10 areas** (code commit 1b40395; docs commit 3832f5d; architecture doc updated in place). Shipped verbatim: the 51-room Ridge with Cragfoot, three villages, four warned-about aggro offshoots and the vistas; the 9/10/11-room delves; the Verdant Crown; the f18↔Cragfoot wiring; three elder pools; 20 NPC definitions including the Verdant Sphere and three bosses with death messages; five loot tables; 72 spawns (three gated); Ridda's vendor rows; and the Crown as the Obelisk Network's **second travel source** (two sources, three checkpoints, revelation-by-visit per 2.11 with no deviations). All verification passed — full topology walk, aggro pattern (offshoots fire, spine lions don't), all three boss cycles end-to-end against the live ticker, Convergence↔Crown round trip, commerce at Cragfoot, XP spot checks (90/54/300), 20/20 tests — **except one flagged item pending a design ruling: the Epic-accessory secondary count.** The twelve copper accessories carry 2-entry secondary pools (the approved two-adjacent-stats design), so the Devourer's guaranteed Epic rolls its full pool of 2 — three stat lines total with the primary — rather than the rarity table's 3 secondaries; recorded in the architecture doc's Known Issues; options are pool-capped semantics (slots = min(rarity, pool), consistent with Legendary's "all in pool" definition) or a small Brief 7 authoring a third secondary per accessory. Closeout conventions recorded: **minions inherit their stat donor's combat tier** (Brief 6's shipped elite from elder donors; display-only field); loot-table display names are admin-facing creative content. No migrations in Briefs 5–6 — the entire zone is seed data. Next: the Epic ruling, then final closeout (architecture doc upload, GDD v18.0). |
| v18 RC17 | v18 (commit 1b40395, unchanged) | **Epic-accessory ruling: pool-capped semantics blessed (option a).** Secondary slot counts are `min(rarity's slots, pool size)` — Legendary's "all in pool" definition was already this principle at the ceiling, so no data changes, no follow-up brief, and Brief 6's flagged verification item resolves as correct-as-built. The rarity section gains the clarifying rule; the copper accessories' two-stat pools stand as designed, rolling both secondaries at Epic (three stat lines with the primary). The architecture doc's Known Issues entry on this point is now a resolved design question — it can be cleared with a one-line doc edit in any future Claude Code session, or stand as history. **The v18 implementation series is closed with zero open items.** Remaining: architecture doc upload to the project, then GDD v18.0. |
| **v18.0** | **v18 (commit 1b40395) — uploaded, Closed** | **RELEASE. The Verdant Reach (Z01) ships complete — Shyland's first battle zone — alongside every system built to carry it.** The version's full contents, implemented across six briefs and reconciled through seventeen RCs: **The zone** — 150 rooms in 10 areas across Fernwater Vale, The Sagewind Flats, and The Viridian Ridge plus seven caves on a logarithmic curve; levels 1–10; maze-with-a-spine layout doubling as a movement tutorial; fog-reveal entrance, ancient stair, boulder field; five villages; four warned-about aggro offshoots; six bosses with narrative-chest death messages on a weapon→armor→accessory rotation and an Uncommon→Rare→Epic ladder; the Verdant Crown terminus establishing the zone-end obelisk pattern. **The Mk 1 item kit** — leather set, Wooden Shield, four weapons with handedness and the general equip exchange rule, twelve copper accessories with tier-material Mk suppression, pool-capped rarity semantics. **The Obelisk Network** — destination-only checkpoints, source-and-destination obelisks (two sources, three checkpoints live), per-character permanent revelation, the free `travel` command, Shards, the Primordial Sphere. **Battle-zone engine mechanics** — boss-gated spawns, guaranteed-group loot, per-NPC death messages, outleveled XP (never zero), and the respawn engine actually working for the first time. **Commerce** — authored `base_value` valuation, one-third sell pricing, soulbound-sellable/unequipped-only, pay-per-attempt repair, `list`/`buy`/`sell`/`repair`, materials, and targetless `attack`/`kill` under aggro. §9.1 reflects the shipped dispatch table. The architecture doc (`Shyland_Architecture_v18.md`, hash 1b40395) is uploaded in lockstep; v17 documents removed. The RC1–RC17 rows above are this version's design history, including every implementation-time correction, kept per convention. |

| v19 RC1 | v18 (unchanged) | **NPC fixtures & attackability ruled.** Two independent booleans on `NpcDefinition`: `is_fixture` (display: room output splits into "Who's here?" living presences and "What's here?" fixtures, empty sections suppressed; ground items stay separate) and `attackable` (combat: attack/kill refuse, auto-target skips, never aggros — NPC-level protection independent of room safety). NPCF vocabulary established (non-player-character fixture). Data rulings: all obelisks NPCF (a new Crown obelisk NPCF commissioned — the Heart's twin was prose-only); all spheres and shards `attackable=False, is_fixture=False` — *whos* that cannot be harmed (shard status field-confirmed during Phase B play); vendors and repairers never attackable (villager-vendor edge: vendor rule wins; seed verification rule, hard failure); villagers stay attackable — safe rooms are their protection, preserving future unsafe villages and warn-you-off texture. No `is_vendor` field — vendor-ness stays derived from `VendorEntry` rows. |
| v19 RC2 | v18 (unchanged) | **Room description rendering redesigned** after play revealed the as-built semantics (first-visit-long/revisit-brief regardless of setting; area text unconditional) matched no ruling. New semantics: first entry always full (area + long) in both modes; revisit with brief on → brief only, no area text; revisit with brief off → full; `look` always full; bare `brief` reports the current setting (the boolean-commands rule governs setting, not querying); default flips to on. |
| v19 RC3 | v18 (unchanged) | **NPC dialogue system designed — the listening model.** NPCs listen to room `say` via keyword→response maps rather than being addressed (`talk`/`ask` struck from §9.2, superseded). Entry-first random draw; one answer per NPC per utterance; no consecutive self-repeats; random shuffle per utterance with 2-tick stagger and position-aware connective color; responses broadcast to the room and always land — the final speaker may add a lore-voiced departure reaction if the asker left; once-per-character greetings; discoverability via examine hints, help line, and the broadcasts themselves. Section 7.5 added. |
| v19 RC4 | v18 (unchanged) | **The Convergence gets its services.** Morra vends (weapons/armor; free newbie tier now, priced range later) and repairs anything; Pella and Ferwick each info+vend+repair — one shared gazebo stock, split voices, the double-act carried by dialogue and kibitz; Repairbot Prime repairs only. Free starter kit as distinct `base_value=0` definitions covering every slot except OFF_HAND/RANGED (deliberate earned gaps), exploit-proof by construction; kit wears normally and pity-repairs free (`takes_durability_loss=False` reserved for rare items/Artifacts by convention); worthless-sell refusal; small priced aspiration tier at Morra; currency display consistency — every player-facing amount through the tier formatter. Section 6.13 added. |
| v19 RC5 | v18 (unchanged) | **`quit` ruled**: returns to the games lobby; blocked in combat with a flee reminder; implicitly blocked while Dying (no exit but the outcome). Companion policy ruled deliberate rather than accidental: link-dead characters stay in the world — browser-close mid-combat abandons the character to the fight, which is what makes the combat block honest. |
| v19 RC6 | v18 (unchanged) | **Death & dying rebuilt** (Section 3.7 rewritten): on falling, the pane clears to a red fatal-blow line and a lore ladder escalates through the 30s window (never mechanical units); combat is interrupted **both directions** — queued/same-round attacks discarded (no posthumous death blows; the founding bear legend retired), incoming hits stop printing, hostile effects cancelled (`removed_by='dying'`) while the player's own DoTs on NPCs keep burning; revival by any heal above zero restores **exactly the healed amount** (a good potion may restore full); expiry declares death in lore, then full-bar respawn with complete client re-sync. Acuity: untouched on level-up, reset on death — now deliberate. |
| v19 RC7 | v18 (unchanged) | **Hit resolution redesigned** after the perma-crit discovery: under d100-with-absolute-bands, a DEX-18 player critted a bear on 84% of swings and could not miss or graze — every fight ran ~40–50% hot. Ruled: contested d20 to-hit (`d20 + attacker DEX` vs `10 + defender DEX`), graze window 3, and criticals as an **independent roll on successful hits** (5% + 1%/DEX-advantage, floor 5%, cap 25%) — five named tunable constants. Always-hit at large advantage is deliberate; the cap bounds the multiplier forever. |
| v19 RC8 | v18 (unchanged) | **Attack focus ruled**: `CombatSession.focus_npc` — engagement steals focus; `kill <in-session non-focus target>` refocuses with its own message; focus-death auto-shifts with an announcement (never silent); the Acuity single-target bonus and the attack target unify onto one field. Positional ordinals extended across engagement and (Phase B) all combat lines. Multi-target damage stays deliberately unbuilt. |
| v19 RC9 | v18 (unchanged) | **Combat math corrections ruled** after automated tests exposed two structural flaws. (1) NPC stats scaled multiplicatively (`base × scaling_factor × mk_tier`) against additive player growth — 26 of 42 Z01 NPCs sat at 0% hit chance for an at-level player; every giant, elder, and boss was mathematically unhittable under either era's math (the Silk Matron's first kill in Shyland history followed the fix). Ruled: **contests add, quantities multiply** — NPC contest stats derive additively from the player curve with blessed at-level hit targets (normal 55% / elite 40% / boss 25%, tier offsets +0/+3/+6); STR/PER/INT keep authored species bases plus curve growth; vitality stays multiplicative; `scaling_factor` re-ruled as the within-band level (only the six inflated boss factors needed a data migration — all other factors already were levels). (2) **Acuity re-ruled band-relative and deviation-based** — the code's absolute-1.0 anchor secretly penalized low-baseline Origins (Voidtouched fought at 0.7× forever) and a float-rounding bug turned Feral's 0.95 into 0.9; inside-band is neutral for every Origin, bonus/penalty measure distance beyond the band edges, no decimal rounding. Growth-term rounding ruled uniform-per-level (Brief 7 Amendment 1). |
| v19 RC10 | v18 (unchanged) | **Seed authority ruled — "the code is definitive."** Reseeding enforces the exact coded configuration: seed-owned tables updated to authored values on every run (the create-only balance-data convention REVERSED), operator-added extras deleted with cascades reported, per-run reconciliation report, second-run-zero-changes as the idempotency law. Live-DB edits are emergency mitigations that must be followed by a real change through the workflow or be undone by the next reseed. Exact-count seed verification retained — correct again under enforce-exact. Runtime/player state (characters, instances, visits, sessions, greeting records, pending responses) is never touched. |
| v19 RC11 | v19 (in progress) | **Phase A implemented — Briefs 1–7 plus amendments, all playtested against per-brief operator guides** (a v19 process innovation, alongside: briefs kept in-repo and pasted per CLAUDE.md Rule 4; automated verification briefs driving the live engine — poison/dying-cancellation, graze distribution via channel-layer message capture, Acuity focus via three-phase damage sampling; the DOCKER_HOST pre-flight rule; GitHub issue workflow with ops briefs). Shipped: presence ownership tokens with guarded Lua heartbeat/delete and self-heal (fast-reconnect invisibility fixed); wallet display (`wallet` + inventory section) and buy/sell vendor-check-first ordering; the client-state sync principle applied (fresh-read status payloads, level-up push, death-respawn re-sync with room-group swap, instant dying-flag); combat messaging (third-person NPC fallback + eight species pools, `{attacker}` substitution, engagement/already-fighting semantics, broadcast subject-exclusion via `exclude_pk`); the full death/dying system incl. the pane-clear client primitive with ARIA-safe handling (fall-sequence room-title line removed by amendment — chrome already shows location); hit resolution (100k-roll simulation gates); attack focus (the phase's one migration). Combat math corrections (Brief 7): additive contest stats with the authoritative worked table (a table to code conformance stop caught a rounding-operand divergence — ruled for the code), six boss scaling factors corrected by data migration, minions verified clean, band-relative Acuity with the Feral regression check. First legitimate boss kill (Silk Matron) and first boss loot (battle axe) followed on deploy. |
| v19 RC12 | v19 (in progress) | **Phase B implemented — Briefs 8–11 plus Amendment 1, all playtested clean.** Brief 8 (room output, fixtures & seed authority): flags + sections + protections live; the Verdant Obelisk authored and spawned at the Crown; enforce-exact reconciliation shipped across ~17 seed-owned tables — its first live run reverted the operator's bear-count tuning and deleted a genuine extra, and the vendor/repairer verification rule self-corrected during seeding; ordinal combat lines and kill-before-level-up ordering (field-verified later); a stray test-era Aldric instance at the Heart diagnosed as verification fallout (ticker-races-scaffolding + unordered-`.first()` lessons banked for test-brief boilerplate). Brief 9 (dialogue engine): five models, the say hook, tick-staggered delivery with connectives and repeat-tracking, greetings, departure reactions; starter maps (Aldric, Info Prime). Brief 10 + Amendment 1 (content & services): fifteen item definitions, six dialogue maps, service flags, kibitz, pity repairs, worthless-sell refusal, currency display pass; the geography audit corrected SIX wrong-compass lines across my authored maps (issue #34 closed via the gated `gh issue close` — the issue-linked-brief lifecycle's first full lap) and Claude Code self-caught two of its own fresh bugs (pity repairs charging the 1-copper floor; a back-fill override poised to re-price the free satchel on every reseed). Brief 11 (`quit`): shipped exactly as ruled. Deferred by ruling with issues filed via ops brief: combat-loot blocking, attunement/home-spawn, shard travel senders. `docs/shyland/flist` and its tooling retired. |
| **v19.0** | **v19 (commit bd32f72) — uploaded, Closed** | **RELEASE. The version that began as "bugs and polish from v18 play" and became the version the world came alive: it lists its occupants honestly, describes itself sensibly, talks back, fights fair, dies beautifully, clothes its newcomers, and holds the door on the way out.** Eleven implementation briefs across two phases, four amendments, three automated verification briefs, two ops briefs. **Systems:** NPC fixture/attackability taxonomy with Who's/What's here; room-description rendering semantics with brief-mode default on; the NPC dialogue listening system with the full Convergence roster voiced; Convergence services (free starter kit, priced tier, pity repairs, kibitz, currency display rule); the rebuilt death/dying sequence with revival; contested-d20 hit resolution with independent criticals; additive NPC contest scaling with blessed difficulty targets (all six bosses player-killable for the first time — the Silk Matron fell first); band-relative deviation-based Acuity; player-controlled attack focus; combat messaging integrity (perspective, ordinals, exclusions); presence ownership; the client-state sync principle; seed authority ("the code is definitive"); `wallet` and `quit`. **Fixed:** presence race, stale status payloads, level-up refresh, death-respawn desync, perma-crit, unhittable content, the hidden low-baseline Acuity tax, the Feral float bug, and a long tail of messaging defects — nearly all found by play. **Process shipped alongside the game:** per-brief playtest guides, in-repo briefs under CLAUDE.md Rule 4, automated live-engine verification briefs, the DOCKER_HOST pre-flight, GitHub issue intake with ops-brief filing and the issue-linked-brief lifecycle (rehearsing v20's issue-first law), and the geography-audit rule for authored content. The RC1–RC12 rows above are this version's design history. Architecture doc `Shyland_Architecture_v19.md` (hash bd32f72) uploaded in lockstep; v18 documents removed. |

| **v20.0** | **v20 (commit af95203) — uploaded, Closed** | **RELEASE. The Map version — Shyland draws itself.** Five implementation briefs plus five consolidated/combined amendments; design history for this version lives in the GitHub issue tracker per the v20 issue-first law (every ruling recorded as issue comments at the moment it was made) rather than in RC rows — 30+ issues opened and closed under the Version 20 milestone. **The map system:** Room coordinates re-ruled as pure per-zone map-space (z is not elevation); the core geometry invariant (unflagged cardinal exits land grid-adjacent, same z) enforced by seed verification on every reseed; per-exit boundary flags (cardinals only); MapFrags — derived, never stored, connected components over unflagged intra-zone cardinal exits; fog-of-war from RoomVisit (now recorded at arrival in every path — the aggro-entry gap fixed); a server-computed map payload on connect and every room change; and the client map — a fixed 300×300 node-and-line rendering, north-up, 9×9 window, current-room highlight, unexplored stubs, boundary ticks, U/D badges, aria-hidden. **World geometry re-authored to make it true:** the Convergence ring re-laid as the 40-room closed chamfered square it always described (six new corner rooms, three exit relabels, spoke re-lay, zero existing rooms moved) with two new ring street-cart vendors (VND-9, Mother Tansy); Z01's Stonestep flipped west and Bear's Hollow re-hung north, the surface flattened to z=0, five cave mouths boundary-flagged; checkpoint sphere→shard wording corrected everywhere (the Primordial and Verdant Spheres alone remain spheres). **The output envelope:** every WebSocket message carries `ts` (epoch ms, stamped at creation) and `seq` (per-connection monotonic, stamped at a single audited delivery choke point — the future firehose tap); seq order is authoritative for rendering; display rule *timestamps mark events, not renderings* (room renders and state reports unstamped; combat, chat, presence, commerce, errors, echoes stamped); `[HH:MM:SS.ss]` dim local-time prefix, aria-hidden. **The command grammar:** one resolver replacing three matchers — `<verb> [all|N] [rarity] [noun]` with ordered token-prefix matching on player-visible name+tier tokens, plural fallbacks (es/s, ves→fe, ies→y), `N.noun` retained, cross-definition ambiguity refuse-lists, rarity-aware same-definition selection (sell lowest-first, equip highest-first), equipped items excluded from sell/drop, noun-optional rarity flush (`sell all common`), a 30-case authoritative unit table; `loot all` sweeps every corpse in the room; bulk operations narrate as per-event message streams with summary lines (sell, repair, loot audited across all vintages; buy N exempt as one atomic transaction); server-authoritative tab completion; the dispatch guard (no input can drop a connection); movement blocked in combat (flee is the exit); `timestamps on|off` as a stored preference. **Rarity moved out of item names into the status flag block** — `Iron Mace Mk 1 — 100% durability [Uncommon, Droppable]` — atomically with the parser, colorized on the Common→Artifact scale. **The client layout:** location bar / unified output pane / command bar (send inside, ping-pong connection indicator with latency) on the flexing left; fixed 300px right pane — stats (verbatim-cased character-name header, V/L ratio bars, the Acuity band gauge that finally teaches the band mechanic) turning combat-red as a section, the scrolling fight panel (per-enemy hp bars and the focus marker), the map at bottom; the app fits the viewport exactly (the page never scrolls); phone stacking ruled. **Output & messaging:** the full semantic-category palette (structural headers one chrome blue everywhere — the general rule; outgoing/incoming/crit/miss combat family unified with the stats-panel red; XP gold; rarity scale); look sections (Exits / Who's here? / What's here?, empty sections omitted, the interim On-the-ground section absorbed); command echo as a timestamped transcript; NPC article grammar — article-free names with authored definite AND indefinite articles plus plural phrases, one display helper composing every reference, introduction contexts ("A black bear is here.", capitalized) vs. definite mid-fight, the 40+-name data pass; corpse decay suppressed for in-combat viewers; "carried nothing worth taking"; the bracketed room header removed (the location bar owns place identity; the output pane clears per room by ruling) and a zone-colored separator bar framing each room render. **Directional combat arrows: designed, reviewed, ABANDONED** — not deferred. **Filed forward, deliberately:** identification visibility redesign (knowledge by holding, #80); Longevity's first drain (#70); Version 21 opens with the vitality lost-update race (#52), NPC ordering unification (#64), `use N` (#65), and the Whistler retune (#66). **Process shipped alongside:** the issue-first law with GitHub milestones; housekeeping immediacy; combined file-and-fix briefs with runtime issue-number capture behind hard gates; the hardened issues-report agent as the single verification channel; closeout reports committed as repo documents; commit-hash-addressed verification; the 5-brief version cap with amendments exempt; the even-features/odd-fixes version cadence; visual MapFrag diagrams required for all map design; finals-only project-file mirroring. The architecture doc (`Shyland_Architecture_v20.md`, hash af95203) is uploaded in lockstep; v19 documents removed. |
| **v21.0** | **v21 — uploaded, Closed** | **RELEASE. The fix version that made the game beatable — and proved it in the field.** Three implementation briefs (one per bucket, B1/B2/B3 labels mapping issues to briefs — a v21 process innovation), one amendment, one research brief, one emergency fix, and a stream of housekeeping briefs; seventeen planned issues closed plus two field additions (#97, #107); design history in the issue tracker per the issue-first law. **The kill-feasibility survey (#89)** — expected-value audit of all 41 seeded combat NPCs against attainable player builds, formulas cited to code: found three INFEASIBLE delve bosses (30/80/122 potions), the build knife-edge (the d20 bridges 20 DEX, so blessed targets were real only for max-DEX builds — an even-split 25/25 character had a 0% hit chance against the Whistler), armor/item stats entirely combat-inert (#100, filed to v22), a latent Mk-2 HP trap (#104), and escort compounding. **The balance retune (#101, B3)** — tier dodge offsets flattened 0/+3/+6 → **0/+2/+2** (re-blessed at-level hit targets 55%/45%/45%); boss difficulty relocated into HP, damage, and escorts; all six Z01 bosses retuned per the authoritative tables (§5.9) with delve escorts reduced to the ladder-wide boss+2 pattern; five heavy elites HP-trimmed; every boss encounter now runs 8.7–13 rounds at 0/6/8/7/7/10 potions vs budgets ≤8 (final ≤12) for the even-split reference build, derived and verified in `Shyland_V21_B3_Retune_Proposal.md`; the accepted consequence — the delve trio remains reference-build content until #100 ships gear — recorded deliberately. Proc-stat curves unified at 0.5/0.2 (#68: lifesteal/poison/electric/mana_regen rolled 0 at Mk 1 forever); zero-value stats stay visible by ruling (bug sirens stay audible); stored zeros re-rolled by the idempotent `fix_zero_secondary_stats` command. The ×3 aggro rooms ruled **deadly-by-design** with authored direction-neutral approach warnings (#102); the four placeholder roster NPCs made unattackable (#103). Field-proof: the operator's 25/25 build killed the Whistler Below at L8 — 0%→20% hit, unwinnable→~26 potions — in a 100-second fight. **The emergency (#107)** — first post-retune playtest found combat rounds at ~15.5s vs 3s design: the tick engine spent ~4.2s/tick on ~750–800 per-row DB calls, dominated by the respawn sweep re-querying all spawn records every second (pre-existing since v20). Operator-declared emergency mitigation with procedure override on record: the sweep batched to per-zone queries, behavior contract unchanged; rounds verified at 3.8s in live combat; further batching candidates listed on #107 for a future brief. **Combat state fixes (B2)** — the heal lost-update race (#52) fixed by ruled **Option A: atomic bar mutations** (F() + Least clamp, refresh-before-display; row-locking rejected as tick-engine contention), with the mandated audit sweep documenting all six bar-write call sites and escalating two findings to issues (#109 bankable mid-combat spend refill, v22 ruling; #110 apply_stat_effect stat-field race, unmilestoned); the consumer-never-RMWs-bars invariant recorded. NPC ordering unified (#64): `(spawned_at, pk)` is the single canonical order for listings, resolver picks, N.noun, and message ordinals — ordinals render only among same-name duplicates in an encounter. Respawned aggressive NPCs engage present players on the spawn tick (#17 — the check simply never existed), inside the respawn path with zero new per-tick queries. **Output & display (B1)** — palette vocabulary named: **key-color** `#7FB3D5` / **value-color** `#E8E4D8` as CSS variables (subcategories deferred); the structured key/value report form (server-tagged lines, client-styled) adopted by `inv`, `stats`, `wallet`, and `help`; `stats` gains the Player line (`Player: <name> - Level <N> <Origin> <Archetype>`) and drops its bracketed header; area prose renders in the Area's theme color and room prose in value-color (superseding #1's D1 near-white narrowing — the two levels finally distinguishable); Who's/What's-here lines are bare noun phrases (no "is here"/"lies here"); the binding flag renamed **Droppable → Unbound**; aggro-room entry renders the full room first, then definite-article engagement, then combat state — in both movement and flee paths (#81); help rewritten (static six-direction movement line, one-line say, `brief` documented, the `<item selection>` convention with one grammar section, uniform `[x | y]` spacing, alphabetized commands); all five pane borders 5px zone-theme-colored at ~0.75 alpha (combat-red keeps precedence on the stats border), the room separator slimmed to 3px (#97); player-help fixes (#84). **Filed forward:** #100 gear wiring and #109 to v22 alongside #65 and the map payload redesign (#82, absorbing #53); #104, #105, #110 unmilestoned. **Process shipped alongside:** bucket labels (B1–B5, version-agnostic, milestone disambiguates); the housekeeping-brief cadence with rulings recorded at the moment made; CC remote-control operation (the entire design→brief→implement→verify loop run from a browser); worktree-per-implementation-brief practice; the author column added to the issues report; the emergency-mitigation lane exercised with issue-first held under override; per-tick query discipline (#107) applied as a brief requirement. Document housekeeping at closeout: the footer version stamp corrected (it had read 18.0 since v18) and three long-standing duplicate section numbers resolved — Convergence Services 6.13→6.14, NPC Dialogue 7.5→7.6, Standing Engineering Tenets 10.8→10.10 — with live cross-references updated (historical changelog rows keep their original numbering as records of when the sections were added). The architecture doc (`Shyland_Architecture_v21.md`) is uploaded in lockstep; v20 documents removed. |
| **v21.1** | **Point release — uploaded, Closed** | **RELEASE — the first point release, and the proof of the point-release machinery.** One founding ticket (#116), one bucket (B1), one implementation brief, shipped outside the major cadence while v22 planning continued undisturbed in a parallel chat. **Single-session enforcement:** nothing prevented two WebSocket connections for one character — per-connection room-group state desynced (the second session rendered a ghost room after the other moved, the same failure class as the v19 respawn desync but with no cross-notify event), per-connection flags drifted, and interleaved commands could race wallet, equip-slot, and combat-action paths; only the presence layer was concurrent-safe (the v19 per-connection token). Ruled **newest-wins takeover** — the classic MUD "reconnect seizes your link": on connect, immediately after the token mint and before the presence write, the new session broadcasts a token-carrying `superseded` event on the personal `player_{pk}` group; a consumer whose token doesn't match prints an authored farewell (category system) and closes through the normal disconnect path (guarded presence delete no-ops or is harmlessly superseded in either interleaving — the safety argument is recorded on #116 and in the architecture doc). **Not a command:** fires through the dying gate and the in-combat quit refusal; **no room broadcast** — witnesses see nothing, the character never left, only the link moved. **Combat carries over with zero handover logic** — CombatSession is DB state and combat output follows the personal group; a mid-fight takeover lands the next round on the new screen. Client: a `superseded` flag suppresses the reconnect placeholder **and the auto-reconnect loop** (ratified into the ruling post-implementation — without it the old tab would steal the session straight back), no navigation, farewell stays visible, refresh-to-retake remains legitimate. Verified by new WebsocketCommunicator tests (takeover ordering, second-session isolation, presence-key ownership after the dust settles) plus the full suite (132 OK); field-proven by the iPad login that surfaced the issue in the first place. **Discovery Rule** exercised as ruled: #117 filed fat at the moment of discovery (stub `tests.py` shadows the `tests/` package, breaking whole-app test discovery), labeled, unmilestoned, untouched. **Process shipped alongside:** the point-release system itself — urgency entry bar, either parity, minor-version numbering (21.5 < 21.15), the one-bucket/one-brief/one-founding-ticket scope law with `--blocked-by` dependencies, in-place document stamps, and this lightweight closeout — codified in `Shyland_Project_Instructions_v21.md`; the Step 0 brief self-commit rule (the committed brief is exactly what executed, by construction); and the push-cadence rule (immediate Step 0 push as the work-has-started signal, commit-and-push at every step boundary, branch only — the operator merges, here operator-directed through CC under a scoped `gh pr merge` allowance). Architecture doc stamped 21.1 in place, hash moved to the code tip. |
| **v22.0** | **v22 (merge 6fcb67b) — uploaded, Closed** | **RELEASE. The version gear got real and the game learned to speak in one voice.** Five implementation briefs (B1/B2/B3/B5/B6) plus nine amendments, two combined file-and-fix amendments, a spec DD, a knob-survey research brief, and the standing housekeeping stream; ~40 issues closed under the Version 22 milestone; design history in the issue tracker and the committed B2 DD per the issue-first law. **Maps V2 (B1 — #82, #115; #53 absorbed):** the map's visual language redesigned onto the named four-color vocabulary — key-color here-dot, value-color known, muted-color unknown, agro-color hostile strokes; a 7×7 window inside a pinned 16px margin; hollow r=10 room circles with a solid r=6 here-dot; **octagon glyphs for travel nodes** (one glyph for shard and sphere rooms — the distinction lives in the travel listing; octagons never agro, seed-enforced); gate triangles colored by destination discovery; **frontier rooms as solid half-diameter muted dots that draw no exits of their own** (the terminus rule); solid half-cell stubs for known paths continuing off-screen (the dashed-stub/boundary-tick vocabulary retired entirely); independent U/D corner badges tucked to per-glyph constants (12.25/13.75) derived from measured ink; `agro` as *configuration, not instance state* — a dead aggressive spawn still marks its room. The payload rewritten to a discovered/frontier schema with **masking by construction** — a frontier entry carries exactly `{x, y, discovered: false}` and nothing else, ever — built in a bounded five-query constant guarded by `assertNumQueries`. **The command revamp (B2 — #111 and twelve more; normative spec `Shyland_V22_B2_Command_Spec_DD.md`, absorbed into §9):** the complete command chart with stable-numbered footnotes — every command's arguments law; central standard prompts (`What do you want to <verb>?`); the **three-layer response doctrine** (CLI error red / world-declined warn yellow / world-answered normal voices — the hard-coded amber died, 49 warn-layer and 10 error-layer call sites re-tagged); the **state-gating matrix** applied centrally (commerce/inventory/gear/travel/movement refused in combat; quit allowed and combat continues after quit — the player can die logged out, proven by test); **resolution pools per command** with examine's union finally covering vendor stock, NPCs, and players; the **player/NPC name invariant** enforced at both edges; **partial fulfillment doctrine** (do the possible part, report warmly; heal sequences stop at full with the green line; `repair all` loops to 5 passes); the **ten transactional success sentences**; `spend` flipped to `spend <quantity|all> <stat>`; `use N` (#65); say's `[say]` prefix dead — speech is `Name: message` in say-color for players and NPCs alike; `[Critical]` brackets dead, the word moved into the prose (`for a critical 28 damage!`) with the dormant crit-in class wired; **information Kinds 1/2/3** with the header punctuation law, the **Equipment paper-doll** (all 14 anatomical slot rows always, muted empties), the Inventory and vendor tables, the shared wallet renderer, who's one-liner; chart-derived help ending in the `Version:` line (`SHYLAND_VERSION`, bumped to the release stamp at every closeout); the settings standard (`brief` default flipped off, **`echo`** new default on, six boolean words, exact sentences); server-authoritative completion of exactly each pool. Amendments: listing columns and the color re-tags (error-color to the crit-out red `#E24B4A`, Epic to the say-gold — deliberate reuses); agro re-unified with error and the **stats pane repainted** (success-color V/L fills and solid acuity band, say-color 16×4 tick); fight/stats pane recolors onto chart names and the **per-zone travel listing** — zones in hardness order, Kind-3 `Type/Destination/Description` tables, each stone's one-liner harvested verbatim from its own room prose into `TravelNode.listing_description`; the report parchment killed and the **chart-as-license law** with its set-equality palette conformance test; **transactional aggregation** — buy/sell/drop/pickup aggregate N>1 into `×N` count-form lines per definition while use/repair/loot stay per-line (#126 files the pluralization subsystem). **New commands (B3 — #57, #113, #88, #112):** **`home`** — a 15-second hearth to the Heart narrated as fog-motif atmosphere (never a timer UI); anything breaks it (movement auto-cancels and the move proceeds; combat entry interrupts in the violent voice; disconnect kills it silently); **completion-only 15-minute cooldown** (per-player admin override) with the wry refusal ending in the exact parenthetical; departure and arrival witnessed in home's own voice. **`cancel`** and the **delayed-action registry** — the standing template for all future delayed actions, allowed in every state (the escape hatch is never locked). **`sudo`** — echoes and the game never responds, by design (the watcher arrives with the firehose). **`last`** — the admin roster with the three ruled time forms. Both admin commands **stealth-gated on the `admins.shyland` Group**, membership checked live per attempt; for non-members the commands do not exist. **Gear combat wiring (B5 — #100, #109, #110; #68's deferred half):** the version's namesake — **+N means +N**: one effective-stat function (base + equipped gear) read at every gameplay site (to-hit, damage, dodge, initiative, carry, bar maxima); **Option C armor** — TAV = slot weight × Mk over worn armor (CHEST 3 / HEAD 2 / LEGS 2 / OFF_HAND 2 / SHOULDERS·HANDS·WAIST·FEET 1) + rolled physical_resist over all equipped items, mitigating NPC→player damage by TAV/(TAV+48) with floors both directions (armor never does nothing; no hit reduced below 1); broken pieces contribute zero TAV; **the bar law** — fill fraction invariant under every max-changing mutation (equip, unequip, spend) via one atomic F()-rescale, killing both #110's stat-field race and #109's bankable free heal (spend later blocked in combat outright, #131 — the first generic in-combat refusal); **the proc rename** (`bleed/stun/poison_chance` → `*_factor` — the value drives frequency AND size; names are flavor, no status effects, damage types unmodeled) and **the proc wiring** — per-item independent rolls at V×0.05 capped 50%, success adds 1..⌈V⌉; flat electric on every landed hit; gear crit_chance inside the capped crit computation; always-on lifesteal via the atomic clamp; four stats deliberately inert by scope law (spells/mana don't exist — wire nothing, land no mines); the gear pool rendering as **one parenthetical** — `You hit the giant cave spider for 14 (+7) damage.`, zero pool byte-identical (the quiet-line law); stats showing base with the gear parenthetical `STR: 25 (+3)` plus the **Armor row** `Armor: 13 (blocks 21%)` and the examine contribution line `Armor: 3 per Mk (worn: 3)` — the incoming `(-N)` receipt shipped, read ambiguously in play, and was removed as scaffolding (the permanent surfaces carry visibility); the Z01 boss budgets **re-blessed for the armored reference build** (no boss dropped to zero potions; the Devourer still demands 10; K=48 stands); shortfall reports and `Nothing happens.` moved to the warn voice (#132 — consequence must be seen). **The tick expiry crash fix (B6 — #135, pulled in by operator ruling):** the full-expiry branch called a sync ORM helper bare in the async loop, killing the engine on every full timed-effect expiry; wrapped via `database_sync_to_async`, siblings swept, field-proven against production — establishing the **tick-loop async-safety rule**. **B4 (travel/attunement) dropped from the version by ruling** — deferred whole to a future zones-and-travel version (#30, #38, alongside #41/#95); v22 kept only the destination-listing order. **Filed forward:** #126 pluralization, #127 ranged procs, #129 authored armor bases, #130 secondary-curve audit before Mk 2, #125 macros, #134 repair kit, #133 the Focus Tonic band-overshoot bug (Version 23 with #18, #40, #117, #119). **Process shipped alongside:** the brief self-commit rule and push cadence proven across every brief; the deploy-time data-action rule (born when B5's seed rerun and `rename_proc_stats` sat unexecuted across builds — pending actions now travel in closeout blocks and pre-flight checks until confirmed done); the version constant in help with its closeout bump; combined file-and-fix amendments behind hard gates as routine; real human players onboarded mid-version. The architecture doc (`Shyland_Architecture_v22.md`, stamped 22.0) is uploaded in lockstep; v21 documents removed. |
| **v23.0** | **v23 — uploaded, Closed** | **RELEASE. The fix version that made the world fight fair and finally gave it a voice.** Five implementation briefs and one amendment, run as **one design chat per bucket** — a v23 process innovation: multiple design chats per version, with the issue tracker and the committed documents as the only bridges between them. Every Version 23 issue closed. **Data integrity (B2 — #137/#117/#18):** corpse contents die with the corpse — the decay sweep cascaded nothing and leaked item rows into a location-less limbo, so `ItemInstance.corpse` moved to CASCADE, the location invariant tightened from at-most-one to **exactly one**, and a one-time self-verifying purge swept production (87 orphans, then zero); the startapp stub `tests.py` deleted, restoring whole-app test discovery; inventory stacking extended to every wear-free type with **soulbound state in the grouping key** (Section 6.11). **Flee and disengagement (B1 — #143/#25):** flee was mathematically impossible — the contest computed NPC PER with pre-v21 `scaling_factor` semantics, contesting a phantom stat two to seven times the real value; both sides now read effective stats. And bosses stopped healing the moment you walked away: session end without death restores every NPC to full through **one choke point** with a last-active-session multiplayer guard. Chip-and-run died in the same version that made fleeing possible — the pair was ruled to ship together, and did. **Effects and display (B3 — #133/#119/#141):** acuity shift effects came to heel — a shift climbs to the drinker's own band edge and **stops there exactly**, one-way, with change-only announcements and a single terminal line at the wall; the tonic family now buys the top of your band rather than a permanent over-band multiplier; the engine's 0.1/1.9 rails became named constants at all six clamp sites; transient state withdrew from pane borders (borders are zone-theme territory — state speaks through backgrounds and text); the level-up announcement split into two honest reward lines with the syntax hint removed. **The voice (B4/B5 — #138/#40/#144/#146/#147):** every single-line-repeated flavor site in the game became a pool behind one `npc_voice` module — sell, buy, sold-out, all six repair outcomes, per-NPC pity repairs for all seven repairers, kibitz, and the aggro-engagement line at all three call sites — under the governing line **speech gets pooled; renderings stay stable**. Worthless items gained a disposal path (a vendor accepts them for exactly 0, opening the only exit the bound starter kit ever had) with **Artifacts refused generically under the no-leak rule**, so a refusal can never serve as an identification oracle. The six Verdant Reach checkpoint services — silent since the zone shipped — were given voices (#144), every keyword and departure pool landed on a **three-response floor**, greetings stayed deliberately single, and first-contact greetings stopped printing the NPC's name twice: **speech is attributed, narration is not** (#147). The corpus is declared data, enforced at seed time and by test, so a voice cannot ship half-authored. **The output-color pass (Amendment 1 — #152, ruled from play):** ambient and narration lifted off muted, misses split by direction (yours warn-yellow, theirs success-green), the copper-loot line joined loot-color — a direct consequence of the render rule, since once narration landed in the ambient voice, muted made a whole NPC exchange unreadable. The doctrine that came out of it is now standing law (Section 10.2): gold is speech, green is what went your way, yellow is your whiff, the reds are damage, value-color is the world, muted is true chrome only. **Process shipped alongside:** the create-or-update architecture convention (creation duty follows first-to-execute, not brief number); the standing implementation-brief requirements made explicit — the version-constant bump in the first brief of a version, an operator-authorized in-session production deploy at exactly `make build && make migrate`, and a post-deploy playtest checklist in every brief; and the deploy-time data-action rule proving itself twice, once on a purge and once on a seed. The architecture doc (`Shyland_Architecture_v23.md`) is in lockstep; v22 documents removed. |
| **v23.1** | **Point release — Closed** | **RELEASE — the bulk-sell consumable guard (#150).** One founding ticket, one brief, per the point-release scope law. The noun-less bulk form `sell all <rarity>` now excludes the consumable type: matching consumable stacks are skipped with one note line teaching the named form (`sell all draught`), and a bulk sell whose matches are all consumables is a world-declined refusal; named-noun forms reach consumables unchanged, and bare `sell all` stays refused (v22 footnote 17 is not legalized). Implemented at the single resolver choke point (`Policy.bulk_exclude_type`/`Resolution.bulk_excluded`, keyed on noun-token absence, before selection and value math). GDD §9.1 footnote 19 and §6 vendor-commands doctrine; 370/370 tests (+16); no migration; architecture doc stamped 23.1 in place. First release closed under the typed-session workflow (Instructions v24) and the Deployment Law (#156): dev-stack playtest, closeout stamp before merge, production deploys from main. |
| **v23.2** | **Point release — Closed** | **RELEASE — the issues-report Python guard (#155).** One founding ticket, one brief, per the point-release scope law. `scripts/shyland_issues_report.py` crashed with a bare `TypeError` under the macOS system Python (3.9 — PEP 604 union annotations evaluated at definition time); the ruled floor is **Python 3.14+** — the supported environment, deliberately stricter than the 3.10 syntax minimum — guarded in two layers: a `python3.14` shebang with the executable bit set, and an explicit runtime version guard placed after the import block, before any annotated `def`, written in old-interpreter-safe syntax so the friendly message always fires — exiting nonzero and naming both the required version and the interpreter actually used; the docstring usage line updated to the working invocation. Repo tooling only — no game code, no migration, no GDD section changes; 370/370 tests (the version pin moved, none added); architecture doc stamped 23.2 in place with the hash unmoved (doc-only point release). Run as the full standing release rhythm by operator direction — the end-to-end process test of Instructions v25 and the first release closed by the new closeout session type. |
| **v23.3** | **Point release — Closed** | **RELEASE — the use output merge (#149/#151).** One founding ticket (#149) plus one dependency (#151), one brief, per the point-release scope law. Using a consumable no longer prints two lines: the effect layer now speaks in clauses — `(clause, annotation)` pairs composed into **one merged success sentence** per use (`You use a Healing Draught Mk 1 and feel your body recover. (+25 Vitality)`), killing the separate system-category effect line; the longevity, acuity, and repair-kit clauses re-authored per the ruled table; timed-effect consumables keep the plain sentence; NPC-path strings recomposed via the standalone form. And multi-use healing stopped flooding the pane (#151): `use N` on instant-restore healing consumables is **one computed transaction** — the vitality deficit measured up front from a fresh read after the unchanged #61 gate, exactly the items the heal needs consumed in resolution order (shipped as the resolver's `use` policy, **oldest-first** — a recorded benign deviation from the ruling's lowest-value-first parenthetical; the §6/§9 wording fix is left to a design session), exactly one atomic clamped vitality UPDATE, one count-form line (single item keeps the article form), the full-heal fold `You are restored to full health.` on the same reward-color line with no second message, the shortfall warn firing only when the ask exceeded inventory and the deficit went uncovered, exactly one status update. While dying, `use` still consumes exactly one restorative — the v19 revival sequence intact, its swallow line merged. The v22 Amendment-5 per-line rule is superseded for `use` alone; `repair` and `loot` stay per-line. 388/388 tests (+18); no migration; architecture doc stamped 23.3 in place with the hash moved to c1e9f59 (architectural point release — code changed). Playtest finding #161 (shortfall-warn context) filed unmilestoned for a future design session. |
| **v23.4** | **Point release — Closed** | **RELEASE — home timings (#162).** One founding ticket, one brief, per the point-release scope law. The hearth command's two timings retuned from play: cooldown 15 minutes → 5 — `Character.home_cooldown_seconds` default `900 → 300` (AlterField `0038`) with an unconditional all-rows data migration (`0039` — every existing row reset to 300, admin overrides deliberately included per the ruling; reverse a no-op); countdown 15 seconds → 10 — `HOME_CADENCE` `(7.0, 5.0, 3.0) → (3.0, 4.0, 3.0)`, all four authored beats (start t=0, mid t=3, late t=7, arrival t=10) and all three `broken_by_violence` checkpoints retained (5 seconds was considered and rejected as near-instant escape). No wording changes anywhere; completion-only consumption, gating, and the per-player admin override capability unchanged. 390/390 tests (+2 pins: default-300 and cadence-sums-to-10); migrations `0038`/`0039`; architecture doc stamped 23.4 in place with the hash moved to 11c14f7 (architectural point release — code and schema changed). |
| **v24.0** | **v24 — Closed** | **RELEASE — the Draught Law (#139); Version 24 (new-zone-prep) opens.** One founding ticket, one brief, per the release scope law — the first release shipped under the release model (Instructions v29/v30): one kind of release, majors ride an otherwise-ordinary `N.0`, major membership is the permanent `V24` label, milestones are shipping releases only. Healing consumables now restore a **percentage of the drinker's `vitality_max`**, never a flat amount: `heal = max(25, ceil((15% + 5% × Mk) × vitality_max))` — Mk 1 = 20%, five drinks zero-to-full at every level; the percentage is of max, never of deficit; the Mk axis buys rounds, not raw HP (price scaling untouched, per-copper healing efficiency deliberately flat across tiers); the 25 HP floor keeps fresh characters at least as well off as the old flat `20 + 5×Mk` and goes dead by roughly level 4; rounding is `math.ceil`, never bare `round()` (the #105 banker's-rounding lesson). Mechanically: new `restore_vitality_percent` component type (additive — `restore_vitality` remains in the vocabulary; choices-only `AlterField` migration `0040`, DB no-op); the law's arithmetic lives exactly once in `effect_utils.percent_heal_amount()`, called by the instant-apply branch and the #151 aggregate's per-item deficit math; the seeded draught's order-0 component converted in place to `0.15 / 0.05` (reconcile — 0 deletions, 1 updated row; the production seed rerun is the release's pending deploy-time action). The full-vitality refusal (#61), the single-message aggregate with consume-only-what's-needed (#151), and oldest-first consumption (#168) are unchanged by the law. 402/402 tests (+12, `test_draught_law.py`); GDD §6.9 lands with this release per the design-ahead rule; architecture doc `Shyland_Architecture_v24.md` created per the `N.0` file-handling rule, hash 9e3fb77 (architectural — code and schema changed). Major-opening mechanics at closeout: `GDD_MAJOR` → 24, monolith renamed to `Shyland_GDD_v24.md`. |
| **v24.1** | **Point release — Closed** | **RELEASE — the post-gear-wiring fight-cost survey (#180).** One founding ticket, one brief, per the release scope law — a research release: no game code, no data, no rulings; the version constant is the only `django/src/` change. Phase 1 (healing economy) of the V24 new-zone-prep major; unblocks the #164 income-law derivation. The harness (`scripts/shyland_fight_cost_survey.py`) drives the shipped combat code in-container — the real `combat_utils`/`item_utils`/`effect_utils` functions, the tick engine's call sequence replicated with line citations, no persistent DB writes (32 tables, zero row drift), RNG seed 180, N = 10,000 Monte Carlo trials per cell — producing the committed report (`Shyland_V24.1_Fight_Cost_Survey.md`) and the 555-row dataset. Headline (§3.1, the table #164 consumes): expected draught cost per at-level fight in current-era standard gear — Normal **3.61 cp**, Elite **13.09 cp**, boss-as-fought **47.94 cp**, multi-aggro room **35.39 cp**; the HP-loss-fraction column is the level-invariant form under the Draught Law (heal is 20% of pool, so per-tier cost is stable across levels). **All 41 solo verdicts OK** — the whole seeded solo roster is feasible at-level for the even-split reference build; **every boss encounter sits inside its v21 potion bound with large margin** (1.4–4.4 expected drinks as fought, 21–66 cp at 15 cp/draught). The survey found a **third mover** beyond the brief's anticipated two (gear wiring #100, Draught Law #139): the v21 B3 retune (#101) — landed after #89, in direct response to it — dominates every boss verdict; all nine #89 flips are attributed through the #89 → flat-25 → bare → headline chain. Population drift reported, not absorbed: delve escorts ×2 (not #89's ×3), the four placeholder-stat NPCs now non-attackable. Validation gate passed before the headline runs (three matchups reproduce #89 exactly; MC vs the EV model within tolerance). 402/402 tests (the version pin moved, none added); no migration; no GDD text ships with this release; architecture doc stamped 24.1 in place with the hash unmoved (research point release — no game-code change). |
| **v24.2** | **Point release — Closed** | **RELEASE — the healing-economy income table (#164 founding ticket, #181 dependency — loot-in-kind).** One founding ticket, one brief, per the release scope law. Phase 1 (healing economy) of the V24 new-zone-prep major completes: grind kills now pay in kind under the Income Law (k = 2, kept on the #180 survey data). Data-only — `seed_world.py` plus the version constant; no models, no migrations, no runtime code. Four per-tier loot tables land in `_seed_verdant_loot_tables` — combat-animal/insect-drops (draught 0.35 + common material 0.5) and elite-animal/insect-drops (guaranteed draught + guaranteed elite material + common material 0.5) — with 22 `NpcDefinition` re-points (1/9/6/6), the seven-trivial-passive carve-out keeping the draught-free `animal-drops` table, and `insect-drops` retired by explicit deletion (2 rows, `SET_NULL`-safe ordering). Values: Animal Hide / Insect Carapace rebased to base 12 (sale 4), two new elite materials — Pristine Animal Pelt, Hardened Insect Chitin — at base 36 (sale 12), and the Healing Draught's value seed-owned at 15 (sale 5; vendor prices untouched). Expected income per kill from seeded rows: combat normal 7.25 cp, elite 29 cp, trivial passive 1.4 cp — exactly the §6.15 enrichment table. Five new/updated seed self-checks; functional loot rolls verified at N = 2,000 per table (elite guarantees exact). GDD §2 and §6.15 markers swept (text landed with the design session, v30 GDD-first law). 402/402 tests; architecture doc stamped 24.2 in place, hash moved to `17baab0` (seed logic and self-checks changed). Pending deploy-time action: production `make seed` (expected 2 deletions) in the closeout tail. |
| **v24.3** | **Point release — Closed** | **RELEASE — the proportional regen law (#165).** One founding ticket, one brief, per the release scope law. Out-of-combat passive regen becomes **proportional to maximum** — the time leg of the healing-economy ledger (§6.15): a full refill from zero takes the constant's number of seconds at every level, forever. Vitality: `ceil(vitality_max / VITALITY_REGEN_SECS)` points per tick (constant 120 — zero-to-full in exactly 120 s, rate constant across the whole deficit, replacing the old deficit-proportional form); Longevity: the **interval form** — exactly one point on ticks where `tick_number % ceil(LONGEVITY_REGEN_SECS / longevity_max) == 0` (constant 3600 — about one hour from zero; a sub-constant bar makes the vitality-style per-tick ceil a flat 1 point/second, the ceil trap the interval form escapes). Combat/dying exclusions, regen silence (status push only, no output text), and the changed-fields push gate all unchanged. Runtime code only — Phase 4 of the tick engine plus the version constant; no models, no migrations, no seed data, no consumer changes. GDD §4.1/§4.3 markers swept at closeout (text landed with the design session, GDD-first law). 412/412 tests (+10, `tests/test_v243_regen.py`); live dev spot-check confirmed the law's arithmetic (5/tick at a 549 vitality bar; 1 point per ~9 s at a 423 longevity bar, clamped exactly at max). Architecture doc stamped 24.3 in place, hash moved to `e0c930f` (architectural point release — tick-engine behavior changed). No pending deploy-time actions. |
| **v24.4** | **Point release — Closed** | **RELEASE — the `heal` command (#166).** One founding ticket, one brief, per the release scope law. The bare-verb front door over the v23.3 aggregate machinery (#151) — "use as many healing draughts as needed": the vitality deficit measured once, the minimum draughts that cover it consumed oldest-first regardless of Mk (#168, via the new `command_grammar.oldest_first` helper — the resolution machinery's own age key, never re-sorted), each item's heal computed from its own Mk under the Draught Law (§6.9); one merged count-form line, one status update. The qualifying pool is mechanical — the per-item aggregate test (extracted as `_item_aggregatable`), never a name match; gate order: the shared #61 at-full refusal (`_at_full_gate`) beats the empty-pool warn `You have no healing draughts.`; supply exhausted short of full reports in the warn voice (#132); while dying, exactly one restorative through the v19 revival path (the `cmd_use` per-item loop extracted as `_use_per_item`). Registered `('cmd_heal', False)` — arguments discarded, in `DYING_ALLOWED`, usable in combat, help row between `flee` and `home`; a **reserved built-in verb** the future alias system (#125) may never shadow. `cmd_heal` composes no sentences of its own. Runtime code only — `consumers.py` plus `command_grammar.oldest_first`; no models, no migrations, no seed data. GDD §6.12/§9.1 markers swept at closeout (text landed with the design session, GDD-first law). 430/430 tests (+18, `tests/test_v244_heal.py`, all six output-table rows pinned); operator playtest successful against the dev stack. Architecture doc stamped 24.4 in place, hash moved to `0dd36ca` (architectural point release — consumer code changed). No pending deploy-time actions. |
| **v24.5** | **Point release — Closed** | **RELEASE — bare `loot` becomes the `all` sweep (#189).** One founding ticket, one brief, per the release scope law. The target becomes optional, defaulting to the kill-gated room sweep: `loot` leaves `PROMPT_VERBS` (the fn-10 required-target set; §9.1 fn 20), empty arguments take `cmd_loot`'s sweep branch, and every downstream behavior is inherited verbatim — the no-corpse warn, the `killed_by_id` kill gate, copper transfer on first loot, per-line sweep output plus summary, the corpse-noun and `N.<NPC>` single-corpse forms. `GRAMMAR_VERBS` and `COMBAT_BLOCKED` untouched — argument completion unchanged; bare loot in combat hits the authored refusal exactly as `loot all` does. Help row `loot [all] \| <NPC>`. The first and only verb whose bare form performs the `all` sweep — deliberately **not** a precedent for `sell` (#150 stands: loot is kill-gated and value-safe, sell is destructive of inventory). Runtime code only — `consumers.py`; no models, no migrations, no seed data. GDD §9.1 markers swept at closeout (text landed with the design session, GDD-first law). 441/441 tests (+11, `tests/test_v245_bare_loot.py`); operator playtest successful against the dev stack. Architecture doc stamped 24.5 in place, hash moved to `f5a4b57` (architectural point release — the dispatch table's required-target set changed). No pending deploy-time actions. |
| **v24.6** | **Point release — Closed** | **RELEASE — the composite strike (#177 founding ticket, #178 dependency — the Ranged slot "at the ready").** One founding ticket, one brief, per the release scope law. Phase 2 (itemization) of the V24 new-zone-prep major opens: combat stops ignoring weapon slots — **every equipped, non-broken weapon contributes to one strike per round.** `composite_weapon_term(weapons, eff_str, eff_dex)` in `combat_utils.py`: per weapon, factor × (its own midpoint ± spread roll + its own governing EFFECTIVE stat — DEX if `is_ranged` else STR) × its own durability multiplier; the primary is the occupant of the first occupied slot in `PRIMARY_WEAPON_SLOT_PRIORITY` (`MAIN_HAND → RANGED → OFF_HAND`) at factor 1.0, every other weapon its `SECONDARY_WEAPON_SLOT_FACTOR` (OFF_HAND 0.5, RANGED 0.5; a slot in neither constant takes the 0.5 default, never a crash) — named tunable constants, the Phase 3 balance pass retunes by constants edit. The tick engine's player-attack path retires the `equipped_weapons[0]` accident: the composite term feeds the unchanged `calculate_damage` as `base_damage` (stat_bonus 0, durability_mod 1.0) so the acuity modifier and the graze/crit multiplier apply once, to the composite; one hit roll, one output line; armed-vs-unarmed branches on any-equipped-weapon with the unarmed branch byte-identical. Procs, lifesteal, gear crit (never slot-factored), the equip resolver, and NPC-side combat untouched. The Ranged slot ruled **"at the ready"** (#178): holstered/slung and ready, legal alongside anything including two-handers — equip behavior confirmed correct as built, no code change; participation in the composite is the ruling made real. Runtime code only — `combat_utils.py` + `run_tick_engine.py`; no models, no migrations, no seed data. GDD §3.6/§5.4/§6.4 markers swept at closeout (text landed with the design session, GDD-first law). 455/455 tests (+14, `tests/test_v24_6_brief1.py`); operator playtest successful against the dev stack (playtest yield, all display/UX: #194 filed — handed-ness invisible in item display, #195 filed — bare `equip` paper-doll via shared `inv` composition, #176 gained live evidence). Architecture doc stamped 24.6 in place, hash moved to `e798d78` (architectural point release — the player-attack weapon-selection path changed). No pending deploy-time actions. |
| **v24.7** | **Point release — Closed** | **RELEASE — equipment display (#195 founding ticket; #176 and #194 dependencies).** One founding ticket, one brief, per the release scope law. Phase 2 (itemization) of the V24 new-zone-prep major continues — the display-side companion to the v24.6 composite strike, all three tickets the yield of its playtest: the display says "two-handed" and shows its consequences, **zero mechanics changes**. Bare `equip` (#195) renders the Equipment paper-doll through **one shared composition** — `_equipment_doll_lines`, extracted from `cmd_inventory`, so `inv` and bare `equip` can never drift — and nothing else (no inventory table, no carry count, no wallet line; report category); `equip`/`eq` leave `PROMPT_VERBS` (help row `equip [<item>]`), and `_dispatch`'s central combat gate is scoped to targeted invocations — the bare form is an information rendering, allowed in combat (the gate follows the act, not the verb). Consumed hand rows (#176): a hand row claimed by a two-handed item equipped in another slot renders the consumer's name-with-tier and `(two-handed)`, both muted — never as free; a two-hander in RANGED consumes both hand rows; the home row keeps normal rendering. Handed-ness disclosure (#194): every weapon's examine carries a `Hands:` row (`Two-handed`/`One-handed`, after Damage:, or Genre: when no damage row); `_slot_cell` appends `(two-handed)` in every listing table (`Ranged (two-handed)`); the hands-conflict refusals append `— the <item> needs both hands.` via `_hands_conflict_clause` (both-rings wording untouched). Runtime code only — `consumers.py`; no models, no migrations, no seed data. GDD §3.6/§6.11/§9.1 markers swept at closeout (text landed with the design session, GDD-first law). 473/473 tests (+18, `tests/test_v24_7_brief1.py`); operator playtest successful against the dev stack (playtest yield: #197 filed — dual-slot weapons' Slot cell should read "Main hand/Off hand"). Architecture doc stamped 24.7 in place, hash moved to `48ff406` (architectural point release — command surface and display composition changed). No pending deploy-time actions. |
| **v24.8** | **Point release — Closed** | **RELEASE — the dual-slot Slot cell (#197).** One founding ticket, one brief, per the release scope law. Phase 2 (itemization) of the V24 new-zone-prep major continues — the playtest yield of v24.7's equipment display: the listing-table Slot cell stops hiding either-hand flexibility, **display composition only, zero mechanics changes**. An item valid in more than one equip slot names **all** its slots — sentence-case labels joined with `/` in authored `valid_slots` order: `Main hand/Off hand` (the seed Combat Knife, the only current dual-slot case) — with the two-handed word appended once, after the full joined label (`Main hand/Off hand (two-handed)` — defensive composition, no such item in seed); single-slot and slotless cells byte-identical. Scope is the shared `_slot_cell` helper only — `inv`'s inventory table and vendor `list` inherit together; the Equipment paper-doll, examine, and all equip/combat mechanics untouched. Runtime code only — `consumers.py`; no models, no migrations, no seed data. GDD §6.11 marker swept at closeout (text landed with the design session, GDD-first law). 477/477 tests (+4, `tests/test_v24_8_brief1.py`); operator playtest successful against the dev stack. Architecture doc stamped 24.8 in place, hash moved to `cda352a` (architectural point release — display composition changed). No pending deploy-time actions. |
| **v24.9** | **Point release — Closed** | **RELEASE — the authored armor base (#129).** One founding ticket, one brief, per the release scope law. Phase 2 (itemization) of the V24 new-zone-prep major continues — the pair doctrine's defense half (#127/#129, ruled 2026-08-02: an item stat of consequence is **an authored guarantee plus a roll above it**), shipped structurally: each ItemDefinition authors its own base armor in the new `armor_base` field (FloatField, default 0.0, rarity-blind; migration `0041`), and TAV = Σ(`armor_base` × Mk tier over ALL equipped, non-broken items — no slot gate, no type gate) + Σ(rolled `physical_resist`, bonus strictly on top). `ARMOR_SLOT_WEIGHTS` deleted, not kept in parallel — the authored field is the only armor authority; the 18 seeded armor definitions author their retired slot weights in place (`_reconcile` update, 0 deletions), so TAV is numerically identical for every currently seeded loadout (structure, not balance — same-slot differentiation is a Phase 3 retune; K = 48 untouched; a full Common Mk 1 set still totals base 13, `Armor: 13 (blocks 21%)`). Examine's armor confession gates on `armor_base > 0` (type-blind), always the single form `Armor: {base:g} per Mk` with the `(worn: n)` / `(worn: 0 — broken)` suffixes. The deleted table's literal test pins converted to seed-data assertions (ruled conversion per the test-hygiene rule, not silent). Models + migration + seed + runtime — `models.py`, `0041`, `seed_world.py`, `combat_utils.py`, `consumers.py`. GDD §3.6 marker swept at closeout (text landed with the design session, GDD-first law). 486/486 tests (+9: `ArmorBaseTavTests`, `AuthoredArmorBaseSeedTests`, examine-confession coverage); operator playtest successful against the dev stack. Architecture doc stamped 24.9 in place, hash moved to `c9d1aa1` (architectural point release — schema field plus TAV rewire). One pending deploy-time action: the production seed rerun (`make seed-prod` in this closeout's tail; expected deletion count 0). |
| **v24.10** | **Point release — Closed** | **RELEASE — the proc floor (#127).** One founding ticket, one brief, per the release scope law. Phase 2 (itemization) of the V24 new-zone-prep major continues — the pair doctrine's offense half (#127/#129, ruled 2026-08-02: an item stat of consequence is **an authored guarantee plus a roll above it**), shipped for procs: a definition may author the **floor pair** `floor_base`/`floor_factor` on a primary-stat proc entry; at drop the instance snapshots the deterministic, rarity-blind floor X = floor_base + (floor_factor × Mk tier) as an int `floor` key on its rolled primary entry — no multiplier, no roll; rarity buys ceiling through rolled V, never floor. On proc success a floored entry pays uniform random X..Y with Y = X + ⌈V⌉; unfloored entries keep the shipped 1..⌈V⌉ path **byte-identical** (key presence selects the path), and the chance formula is untouched (V × 0.05, capped at 50%, reads V only, both paths) — the floor changes what a proc pays, never how often it fires. `flame_factor` joins `PROC_FACTOR_STATS` as the family's fourth member (flavor name only — no status effects, no damage types). Examine renders the promise parenthetical `(between X and Y damage)` on floored entries only, via the shared list-blind `_item_stat_line` helper. Seed authors the two floored carriers — Flame Projector (wasteland, Ranged, flame floor 8+4×Mk) and Dart Caster (fantasy, Main hand/Off hand, poison floor 5+3×Mk) — additive, 0 deletions, and the primary-only-floor seed invariant (`floor_invariant_violations`) fails every reseed by name on any floor key outside primary proc-family entries. No models, no migration — the pair and snapshot are optional JSON keys on the existing stat-spec JSONFields. Code + seed — `item_utils.py`, `combat_utils.py`, `consumers.py`, `seed_world.py`. GDD §5.4/§5.5/§6.4 markers swept at closeout (text landed with the design session, GDD-first law). 506/506 tests (+20, `tests/test_v24_10_brief1.py`); operator playtest successful against the dev stack (mid-build yield: #201 filed — the two new weapons ship at model-default base_value 1; pricing needs a design ruling). Architecture doc stamped 24.10 in place, hash moved to `81d0430` (architectural point release — proc payout path, drop-time snapshot, examine composition). One pending deploy-time action: the production seed rerun (`make seed-prod` in this closeout's tail; expected deletion count 0). |
| **v24.11** | **Point release — Closed** | **RELEASE — knowledge by holding (#80).** One founding ticket, one brief, per the release scope law. Phase 2 (itemization) of the V24 new-zone-prep major continues — the v18 identification trapdoor closed by the #80 ruling of record (2026-08-04): **identification is a property of holding.** Pickup identifies and drop re-veils at the ownership-transfer choke points only — `transfer_to_character` and `do_loot_item` gain the identify-on-take flip mirroring `transfer_to_room`'s existing re-veil, every path guarded by `is_unidentifiable` (an unidentifiable item's `is_identified` is never written by any path); `do_loot_item` composes its looted name after the flip so the looted line names the real item the player now holds. The veil hides every info suffix — `get_item_suffix` returns `''` for unidentified items (killing durability %, BROKEN, and bag carry-bonus at every compose site in one place) and `_details_cell` gates its durability segment on `is_identified` exactly as rarity already was: the unidentified line is mystery name + `[Bound\|Unbound]`, nothing else. `examine` is close inspection — an unidentified (non-unidentifiable) item renders the full identified detail block byte-identical to examining it identified, via an in-memory-only flip with no `.save()` (output-only; the room listing keeps the mystery name until pickup); the `is_unidentifiable` mystery block tightens to composed line + description + no-method line (the redundant cannot-determine parenthetical deleted). Resolution and tab completion continue to match visible names only — a re-veiled item's real name neither resolves nor completes. Lasting mystery is exclusively `is_unidentifiable`. Runtime code only — `consumers.py`, `item_utils.py`; no models, no migration, no seed data (the veil is the drop mechanic, not a ground-state invariant). GDD §6.8/§6.11 markers swept at closeout (text landed with the design session, GDD-first law). 517/517 tests (+11, `tests/test_v24_11_brief1.py`); operator playtest successful against the dev stack (playtest yield: #203 filed — examine's `Note: … you may drop it` line, weird on ground items post-#80; V24-labeled, unruled). Architecture doc stamped 24.11 in place, hash moved to `05b836f` (architectural point release — ownership-transfer and examine behavior changed). No pending deploy-time actions. |
| **v24.12** | **Point release — Closed** | **RELEASE — the repair-kit wiring (#134).** One founding ticket, one brief, per the release scope law. Phase 2 (itemization) of the V24 new-zone-prep major continues — the last item of the ruled P2 queue (#129 → #127 → #80 → #134): the v23.3 fizz placeholder retires and the Repair Kit goes live as field repair. `durability_restore` lands in `effect_utils.py` — each kit targets the owner's most-damaged eligible item over everything owned, carried + equipped (broken 0% gear ineligible, stable pk tie-break; the kit can never target itself), always succeeds with one atomic clamped UPDATE; restore = 15 + 10×Mk clamped at 100 (Mk 1 +25, Mk 2 +35), the annotation reporting the ACTUAL points applied (`You use a Repair Kit Mk 1 and patch up the Iron Mace Mk 1. (+25 durability)`). The component-keyed use-pipeline gate (`effect_restores_durability` — derived from components, never a name match) refuses BEFORE apply-and-consume in normative order — dying over combat, then the fresh eligibility read: the broken-only warn, the zero-need warn, and the fulfilled-purpose stop (reward) with the only-had-N shortfall suppressed; no kit consumed on any refusal, each state's authored line as tabled in the brief. Kits never aggregate — per-item sequences re-target most-damaged-first through each kit's own fresh query. Seed: the `repair-kit` EffectDefinition + one instantaneous `durability_restore` component (15.0/10.0); `base_value` 15 with the back-fill entry so the authored value survives the consumable-wide pass (cart price entry 15 untouched); no loot-table changes. Code + seed — `effect_utils.py`, `consumers.py`, `seed_world.py`; no models, no migration. GDD §6.5/§9.1 markers swept at closeout (text landed with the design session, GDD-first law). 537/537 tests (+20, `tests/test_v2412_repair_kit.py`); operator playtest successful against the dev stack. Architecture doc stamped 24.12 in place, hash moved to `26605cc` (architectural point release — effect application and use-pipeline gate changed). One pending deploy-time action: the production seed rerun (`make seed-prod` in this closeout's tail; expected deletion count 0). |
| **v24.13** | **Point release — Closed** | **RELEASE — NPC HP Mk scaling (#104).** One founding ticket, one brief, per the release scope law. Opens Phase 3 (Mk 2 balance) of the V24 new-zone-prep major — closing the gate #104 named: no Mk 2 spawn is authored until NPC HP scales with Mk tier. Instance HP is now set at spawn time: `combat_utils.npc_max_vitality(npc_definition, mk_tier)` computes `base_vitality × (1 + NPC_HP_BAND_LIFT × (mk_tier − 1))`, `NPC_HP_BAND_LIFT = 0.75`, rounded **half-up** via `int(lifted + 0.5)` — never built-in `round()`, whose banker's rounding drops `.5` cases to even (Silk Matron 150 at Mk 2 is 263 by ruling, the test-pinned sentinel; cf. the #105 parity trap). The tick engine's respawn sweep — the codebase's only non-test `NpcInstance` creation site, grep-verified — persists the lifted value to both `vitality_current` and `vitality_max` once per spawn row; no read-time scaling anywhere. The lift is linear per band and uniform across all combat tiers (normals, elites, bosses — the #101 boss ladder preserved within every band); `base_vitality` remains the authored within-band value carrying species identity; at-level time-to-kill is band-invariant. Mk 1 multiplies by exactly 1 — zero change to any shipped spawn, test-pinned as an identity invariant. Runtime code only — `combat_utils.py`, `run_tick_engine.py`; no models, no migration, no seed data. GDD §5 markers (both) swept at closeout (text landed with the design session, GDD-first law). 541/541 tests (+4, `tests/test_npc_hp_scaling.py`); operator playtest successful against the dev stack — including live Mk 2 combat against the dev-only lifted Hollowcrown encounter (Devourer 490/490, drones 123/123 each — a live half-up case; the operator's character died at level 13 vs the effective level-20 boss, received as a positive Phase 3 difficulty signal). Architecture doc stamped 24.13 in place, hash moved to `f001a79` (architectural point release — spawn-time HP derivation). No pending deploy-time actions. |
| **v24.14** | **Point release — Closed** | **RELEASE — the gear stat band lift (#130).** One founding ticket, one brief, per the release scope law. Phase 3 (Mk 2 balance) of the V24 new-zone-prep major continues — gear flats now track the band (GDD §6, the band-lift doctrine): a seed-data-only retune of all 146 stat entries in `seed_world.py`, each authored as its Mk 1 midpoint `m1 = base + factor` plus a class lift — **full lift** `(base, factor) = (0.25, 0.75) × m1` for the six primaries, `lifesteal`, `electric_damage_bonus`, `physical_resist`, and the inert flats; **half-power** `(0.625, 0.375) × m1` for the proc-factor family (V pays twice — chance and size — so the full lift would compound proc damage share); **proc floor pairs full-lifted** `(0.25, 0.75) × f1` (Flame Projector 8/4 → 3/9, Dart Caster 5/3 → 2/6; Mk 1 floors 12 and 8 unchanged); **`crit_chance` exempt** (a probability's worth is band-invariant) — 135 entries changed, the 11 `crit_chance` entries byte-identical, every Mk 1 midpoint preserved exactly (proven by pre/post-reseed capture from the live dev DB, diff empty). Applied by a deterministic transform script asserting an exact occurrence count for every (stat, old pair) pattern before writing a byte. Zero runtime code, zero models, zero migrations, no instance backfill (drop-time snapshot doctrine). Seed only — `seed_world.py`. GDD §6 marker swept at closeout (text landed with the design session, GDD-first law). 543/543 tests (+2, `tests/test_band_lift.py` doctrine-shape pins; v24.10 pinned literals updated to the lifted curves); operator playtest successful against the dev stack (playtest yield: #211 filed — the silver accessory tier: the tier-material ladder needs its silver rung before V25's Mk 2 zones, plus a Mk-mismatch guard ruling). Architecture doc stamped 24.14 in place, hash stays `f001a79` (seed-data release — no architectural change). One pending deploy-time action: the production seed rerun (`make seed-prod` in this closeout's tail; expected deletion count 0). |
| **v24.15** | **Point release — Closed** | **RELEASE — the tier XP multiplier (#26).** One founding ticket, one brief, per the release scope law. Phase 3 (Mk 2 balance) of the V24 new-zone-prep major continues — kill XP now pays for difficulty: `NPC_TIER_XP_MULT = {'normal': 1, 'elite': 2, 'champion': 4, 'boss': 8, 'world_boss': 16}` — **the doubling ladder, every rung doubles**; all five rungs ruled now, champion and world_boss design-ahead for V25 — multiplies the `xp_for_kill` base `int(mk_tier × 10 × scaling_factor)` **before** the v18 outleveled decay: the −20%/level multiplier and its 10% floor operate on the tier-multiplied base, the absolute `max(1, …)` floor closes as ever. Grounded in the #180 survey (above-band: time parity ~1.1–1.4× per tier; below: draught-cost parity — loot carries the economy). Escorts and adds pay their own tier — no shared-encounter logic; missing/unknown tier defaults to ×1 (`.get(…, 1)`); the kill message format untouched. The worked Matron sentinel (boss, Mk 1, `scaling_factor` 3.0): 30 → 240; outleveled at character level 13: 240 × 0.4 = 96. Runtime code only — `combat_utils.py`; no models, no migration, no seed data. GDD §3/§2/§5.9 markers swept at closeout (text landed with the design session, GDD-first law). 548/548 tests (+5, `tests/test_tier_xp.py` — the ladder pinned to `COMBAT_TIER_CHOICES` so a future sixth tier fails loudly instead of silently paying ×1; the sentinel/composition table; unknown-tier ×1); operator playtest successful against the dev stack (the dev-only Mk 2 Hollowcrown rig: Devourer +1600 XP was 200, drones +360 was 180). Architecture doc stamped 24.15 in place, hash moved to `3c1befa` (architectural point release — kill-XP derivation changed). No pending deploy-time actions. |
| **v24.16** | **Point release — Closed** | **RELEASE — the inv trim (#208).** One founding ticket, one brief, per the release scope law. Operator pick over the Phase 3 remainder of the V24 new-zone-prep major — `inv` sheds the v22 three-part composite: `cmd_inventory` renders the **Inventory table alone**, the `Inventory (N/M)...` header the render's first line — the Equipment paper-doll belongs to bare `equip` (v24.7 — #195) and the money line to `wallet`; `_equipment_doll_lines` and `_wallet_line` both survive with a single consumer each, neither command's output changed by one byte; the equipped-items query stays alive — capacity unchanged at effective STR (base + gear, #100) × 10 + equipped-bag carry bonus; stacking (#18), the alphabetical sort, the Slot (#197/#194) and Details cells, and the unstamped report category untouched; help row `Show your inventory.` Runtime code only — `consumers.py`; no models, no migration, no seed data. GDD §6.11/§9.1-fn21/§9 markers swept at closeout (text landed with the design session, GDD-first law). 553/553 tests (+5, `tests/test_v24_16_brief1.py` — header-first, no doll rows, no Wallet line, capacity-alive pin, help-row pin; the v24_7 byte-parity test re-oracled against the paper-doll helper, original intent preserved as explicit assertions — recorded deviation-style per test hygiene; the three anticipated parser-update sites needed zero changes); operator playtest successful against the dev stack (playtest yield: #215 filed — bags' flat carry_bonus is noise against the STR-scaling capacity base; unruled, normal pipeline). Architecture doc stamped 24.16 in place, hash moved to `f62dbe9` (architectural point release — output composition changed). No pending deploy-time actions. |
| **v24.17** | **Point release — Closed** | **RELEASE — DEX curve rounding parity (#105).** One founding ticket, one brief, per the release scope law. Phase 3 (Mk 2 balance) of the V24 new-zone-prep major continues — **floor the curve:** `get_npc_stats` derives NPC DEX as `NPC_CONTEST_BASE + math.floor(NPC_CONTEST_STEP × (L − 1))` + tier offset — the growth term floored, mirroring the reference player's own floor-share DEX accrual (`18 + floor(2.5 × (L − 1))`), so NPC DEX equals the attainable at-level primary and the blessed at-level hit targets (55% normal / 45% elite / 45% boss) are exact at every level of every band. The prior `round()` was Python's banker's rounding, which sent the band's `.5` levels to the nearest even integer — overshooting the player by 1 DEX = one d20 pip = −5% hit at exactly L4 and L8 per band (the #89 survey's G5 finding; elite L4 DEX 28 → 27, sf 8.0 38 → 37; aligned levels byte-identical). The STR/PER/INT `growth` line deliberately keeps its Amendment-1 `round()` (ratified damage-side noise, no hit% effect); `npc_max_vitality`'s half-up rounding (#104) untouched. Runtime code only — `combat_utils.py`; no models, no migration, no seed data. GDD §5.4 marker swept at closeout (text landed with the design session, GDD-first law). 559/559 tests (+6, `tests/test_dex_parity.py` — the curve law across Mk 1–3 × levels × tiers, player parity at effective levels 1–30, blessed targets exact everywhere, the L4/L8 sentinels 27/37, aligned-level pins 20/30/40; zero test conversions, as the brief's design-time grep predicted). Playtest disposition: **No playtests for this brief** (terminal — first use; the surface is statistical, a 5% hit-rate shift at two levels per band). Architecture doc stamped 24.17 in place, hash moved to `d83fcdf` (architectural point release — contest-math change). No pending deploy-time actions. |
| **v24.18** | **Point release — Closed** | **RELEASE — the in-combat acuity drift pause (#142).** One founding ticket, one brief, per the release scope law. Completes the acuity design (the unruled corner #142 named): passive acuity drift toward baseline runs only outside combat — tick Phase 2's `get_characters_needing_drift` excludes any character with an active `CombatSession` (`.exclude(combat_sessions__is_active=True)`), Phase 4 regen's combat-membership predicate shared by ruling — one definition of "in combat" for both phases, so *nothing passively recovers in combat* now holds for all three bars. Shift-active (#133) and in-combat are **independent** pause conditions; the per-character drift loop, `ACUITY_DRIFT_RATE` (0.01), the snap-within-rate rule, the 2-decimal rounding, the floor/ceiling clamp, and drift silence all untouched; post-combat resume is ordinary by construction — the character reappears in the candidate set on the next tick, no catch-up, no burst correction. Combat continuing after quit keeps a logged-out fighter's drift paused until the session ends. Runtime code only — `run_tick_engine.py`; no models, no migration, no seed data. GDD §4.2 marker swept at closeout (text landed with the design session, GDD-first law). 566/566 tests (+7, `tests/test_acuity_drift_pause.py` — drift law both directions, the snap rule, the in-combat pause, ordinary resume, shift independence in and out of combat; zero test conversions, as the brief's design-time check predicted). Operator playtest successful against the dev stack (playtest yield: #225 filed — acuity displays truncate to one decimal across three surfaces; design ruling needed). Architecture doc stamped 24.18 in place, hash moved to `c3c21c8` (architectural point release — tick-engine runtime change). No pending deploy-time actions. |
| **v24.19** | **Point release — Closed** | **RELEASE — zombie combat session reaping (#218).** One founding ticket, one brief, per the release scope law. Kills the zombie-session class #218 reported (all NPCs dead, session still active — loot blocked "in combat", stale sweep unable to reap because the engine refreshed `last_tick_at` unconditionally). Two-part fix in `run_tick_engine.py`: **(A) the kill path goes M2M-wide** — in `execute_actions`' kill block the dead NPC is removed from *every* active `CombatSession` holding it, not just the killer's; a bystander session left with zero living NPCs closes on the standard end pattern in the same engine round ("Combat has ended." at `reward`, fresh status, fight-clear payload), and a session that retains living NPCs but had the dead NPC as focus reassigns to its next living NPC (canonical `(spawned_at, pk)` order) with "You turn your attacks on {name}."; the killer's own session flow untouched. **(B) loop-head self-heal** — the active-sessions loop re-reads each session's DB `is_active` + living-NPC existence before `update_session_tick` (never the prefetched cache): inactive → silent skip; active with zero living NPCs → immediate close on the same standard pattern, with `last_tick_at` never refreshed — the stale sweep restored as a backstop by construction, capping any future leak path's stuck window at one engine tick. `release_session_npcs` untouched by ruling: dead NPCs never restored, shared living NPCs never snap to full (the v23 #25 guard re-pinned). Runtime code only — `run_tick_engine.py`; no models, no migration, no seed data, no GDD section text (bug-fix release — no design change, no marker to sweep). 572/572 tests (+6, `tests/test_zombie_sessions.py` — cross-session kill closes the bystander, cross-session focus reassignment, both self-heal paths with the `last_tick_at` no-refresh assertion, dead NPCs never restored, shared living NPC keeps its damage; zero test conversions). Operator playtest successful against the dev stack (two-account live reproduction of #218: kill and bystander's "Combat has ended." in the same round, fight pane cleared, loot gate passed — the bystander's loot then hit the standing kill-attribution refusal, which is corpse ownership, #220's out-of-scope question, not the #218 gate). Architecture doc stamped 24.19 in place, hash moved to `4f30bdf` (architectural point release — tick-engine session-lifecycle change). No pending deploy-time actions. |
| **v24.20** | **Point release — Closed** | **RELEASE — examine binding rows removal (#203).** One founding ticket, one brief, per the release scope law. The detail block states binding once: both binding prose rows are deleted from examine's identified detail block in `consumers.py` `_format_identified_item_lines` — the `Note:       This item is not yet bound — you may drop it.` row (rendered when neither equipped nor soulbound; read misvoiced on ground items once examine stopped requiring pickup) and the `Bound:      This item is bound to you.` row (rendered when soulbound) — both restated an on-screen fact under inconsistent key styles. Bound state is carried solely by the headline's trailing flag block (`[Rarity, Bound|Unbound]`, `compose_item_line`), per the binding-in-the-flag-block doctrine; the `Equipped:` and `Curse:` rows are explicitly untouched — each carries a fact the flag block does not (equip slot; identified curse state). Every other row of the block byte-identical; output composition only — no model, resolver, state, or message-category change; `compose_item_line` and every other item-line site untouched (drop's `…is bound to you and cannot be dropped.` refusal warn is a different string and site, unchanged). Runtime code only — `consumers.py`; no models, no migration, no seed data. GDD §6.8 marker swept at closeout (text landed with the design session, GDD-first law). 576/576 tests (+4, `tests/test_v24_20_brief1.py` — unbound-unequipped no `Note:` row with `Unbound` flag block, soulbound-unequipped no bound prose with `Bound` flag block, soulbound-equipped keeps `Equipped:` with no binding prose, curse row unchanged; zero test conversions). Operator playtest successful against the dev stack. Architecture doc stamped 24.20 in place, hash stays `4f30bdf` (output-composition change ruled non-architectural by the brief — the ruling anticipated and overrode the v24.16 precedent explicitly). No pending deploy-time actions. |
| **v24.21** | **Point release — Closed** | **RELEASE — floored weapon pricing (#201).** One founding ticket, one brief, per the release scope law. The two floored-proc weapons (v24.10, #127) gain authored `base_value` entries in the seed's back-fill dict — Flame Projector (`flame-projector`) **85**, Dart Caster (`dart-caster`) **70** (ruled 2026-08-05). The pair had shipped into the type-wide non-consumable/non-bag 25 back-fill (the #201 premise's "default 1" corrected at design time: the back-fill left no definition at the model default); dict membership now both applies the ruled values on every reseed (the standard forced pass) and removes the pair from every type-wide `.exclude(slug__in=base_values)` pass by construction. Pricing rationale from the ruling: Flame Projector 85 = the two-handed ranged peer of the Hunting Bow (80), a hair above for the game's strongest authored proc floor, below the 100 two-handed-melee ceiling; Dart Caster 70 = slot-flexible one-hander well under the Pulse Pistol (90), between Iron Mace (65) and Hunting Bow (80). Value/sale arithmetic untouched and verified: Mk 1 Common 85/28 and 70/23, Mk 2 Common 170/56 and 140/46; existing instances reprice automatically — `base_value` lives on the definition and value reads go through it at sale time, no instance backfill, no data script. Seed data only — two dict entries in `seed_world.py`; no runtime code, no models, no migration. **No GDD text change — the first zero-GDD-edit release (per-item prices are not GDD content); no marker to sweep.** 580/580 tests (+4, `tests/test_v24_21_brief1.py` — the two seeded `base_value` pins and derived Mk 1 Common value/sale through the real arithmetic; zero test conversions, as the brief anticipated). Operator playtest successful against the dev stack. Architecture doc stamped 24.21 in place, hash stays `4f30bdf` (seed-data release, not an architectural change — v24.14 precedent). Pending deploy-time action: production seed rerun (`make seed-prod`, expected deletions 0) in the closeout tail's deploy window. |
| **v24.22** | **Point release — Closed** | **RELEASE — acuity display precision, two decimals end to end (#225).** One founding ticket, one brief, per the release scope law. Every acuity numeral the game renders now shows **fixed two decimals, trailing zeros kept** (`1.00`, never `1.0`) — the founding complaint: a Focus Tonic settled at the exactly-stored 1.15 band edge rendered as "1.1", a coarser display lying precisely at the settled states the meter exists to show. All seven format sites converted, nothing else: the `game.html` stats-pane render (`toFixed(1)` → `toFixed(2)`, adjacent comment updated to keep its claim true), the `stats` command's current and baseline conversions in `consumers.py` (`:.1f` → `:.2f`), and the four tick-engine message suffixes in `run_tick_engine.py` (`dot_acuity` disruption, `hot_acuity` clearing, sharpens, wavers). Supersedes #133's one-decimal mid-climb display — no surface anywhere renders acuity at one decimal. Display-only: stored values remain unrounded floats, the engine's `round(..., 1)` storage steps and the exactly-stored band edge are untouched, `_build_status`'s existing `round(..., 2)` payload calls were already correct, and the modifier derivation stays rounding-free (v19 rule). Runtime code only — `game.html`, `consumers.py`, `run_tick_engine.py`; no models, no migration, no seed data. GDD §4 marker swept at closeout (text landed with the design session, GDD-first law). 581/581 tests (+1, `tests/test_v24_22_brief1.py` — drives a `shift_acuity_high` settle onto the exactly-stored 1.15 band edge and asserts the numeral-free SETTLES terminal line, stored value exactly 1.15, and the stats render `Acuity: 1.15 (baseline 1.00)`); the three pinned tick-suffix literals updated literal-for-literal (1.10/1.20/0.20). One recorded test-construction deviation: no tick suffix can ever carry an exact x.x5 value (every engine acuity mutation except the band-edge stop stores `round(..., 1)`, and the band-edge stop deliberately prints the numeral-free terminal line per #133 doctrine, which the brief preserves), so the new test pins the founding complaint at its real numeral surface — the stats sheet — rather than the brief's tick-suffix example; intent fully preserved, no code deviation. Operator playtest successful against the dev stack. Architecture doc stamped 24.22 in place, hash moved to `3267d62` (runtime code changes after the seed-only/doc-only 24.20–24.21). No pending deploy-time actions. |
| **v24.23** | **Point release — Closed** | **RELEASE — percentage bags (#215).** One founding ticket, one brief, per the release scope law. The equipped-bag carry contribution becomes a percentage of the STR-derived base — the founding complaint: a flat `carry_bonus` decays against the level-and-gear-scaling capacity base (by level 17 the best bag in the game was +4.3%), while a percentage holds a bag's felt value constant at every level. The formula (§6.10): `capacity = floor(effective_STR × 10 × (100 + Σ bag_pct) / 100)`, integer math (`// 100`); each equipped bag contributes `carry_pct_base + carry_pct_per_mk × Mk` percentage points at the **instance's** Mk tier — deterministic, no rarity roll (bags continue to roll no stats); percentages of all equipped bags **sum into one multiplier, never compound**. Model: `ItemDefinition.carry_bonus` renamed `carry_pct_base` (RenameField) plus new defaulted `carry_pct_per_mk` — migration `0042`, the release's only migration and the first since 24.12. One helper `item_utils.carry_capacity` answers all four former inline sites (`cmd_inventory`, `get_carry_capacity`, `get_carry_counts`, `_unequip_blocked_reason` called with the reduced equipped list — "capacity without this bag"; grep for `carry_bonus` outside migrations: zero hits); `bag_pct` feeds the percentage displays — bag suffix `— +{pct}% carry capacity` and examine `Carry bonus: +{pct}%`, both at the instance's Mk, both identification-gated (unidentified bags leak nothing). Seeded values: Satchel 10 + 5×Mk (Mk 1 = 15%, Mk 2 = 20%); Patchwork Satchel 5 + 3×Mk (Mk 1 = 8%, Mk 2 = 11%). GDD §3 (two sites) and §6.10 markers swept at closeout (text landed with the design session, GDD-first law). 589/589 tests (+8, `tests/test_v24_23_brief1.py` — formula pins including the brief's reference case STR 47 + Mk 2 Satchel = 470 × 120 // 100 = 564, percentage suffix/examine forms, veil silence, unequip-guard boundary at exactly capacity). Test-conversion deviations reported per the pool rule: `test_v24_16_brief1` (kwarg rename, the flat +5 test bag became `carry_pct_base=5`, header pin 1/125 → 1/126) and `test_v24_11_brief1` (kwarg rename, suffix pin gains `%`) — original intent preserved as explicit assertions; `test_gear_combat` needed no conversion, a deviation from the brief's expectation — its carry test equips no bag and bagless capacity is invariant under the new formula. Operator playtest successful against the dev stack (one finding: the dev reseed's enforce-exact sweep reverted the standing dev-only rig — the 3 off-seed silver-clone definitions with Harley Stone's cascaded Mk 2 jewelry, Hollowcrown boss-room spawns back to seed-authored Mk 1, respawn minutes back to 10/3 — the ledger-predicted seed-authority behavior, not a defect; operator ruled "leave it," #211 remains the real fix). Architecture doc stamped 24.23 in place, hash moved to `fb60a59` (architectural — model rename + capacity-formula change). Pending deploy-time action: production reseed (`make seed-prod`, bare, own confirmation; expected deletions 0) in the closeout tail's deploy window after the code deploy — which applies migration 0042, the first production migration since 24.12. |
| **v24.24** | **Point release — Closed** | **RELEASE — readability pass (#233 umbrella ← #221 contrast + #222 type scale).** One founding ticket, one brief, per the release scope law. Pure client presentation, confined to the two templates `game.html` and `character_create.html` — no server code, no models, no migration, no seed data, no routing, no shared surface, and no GDD design content (ruled in the brief: the GDD does not specify pixel values or palette hexes, so nothing here changes design text — no markers existed to sweep). Type scale (#222): each template keeps exactly **one** px font-size declaration — the root (`html, body`), raised 14px → 16px as the single tuning knob (approved band 12–24px) — and every other font-size site converts to `rem` at its exact 14px-base ratio (game.html: `#loc-bar`/`#prompt` 1.0714rem, `#cmd` 1rem, `#side`/`#stats-name`/`#bars`/`#send-btn` 0.8571rem, `.fight-nums`/`#conn-ms` 0.7857rem; character_create.html: `h1` 1.2857rem, inputs/selects/submit 1rem), so future readability tuning is a one-line change that scales everything proportionally. `.map-updown` byte-identical per ruling (its `font:` shorthand is tuck-rule geometry, not readability surface); no layout dimensions touched, right pane fixed at 300px, map SVG untouched. Contrast (#221): `--muted` `#6b6b80` (computed 3.47:1 on `#16161a`, below AA) → `#85859c` (5.01:1, AA ≥ 4.5:1), variable-level change only, deliberately kept subordinate to `--text` (`#c8c8d4`, 10.89:1). The operator tuning loop was part of the playtest: the starting values were approved as final in-conversation — zero tuning iterations, no design findings. 589/589 tests (count unchanged — no new tests; the pin test moved only with the version stamp). Operator playtest successful against the dev stack. Architecture doc stamped 24.24 in place, hash **not** moved (presentation-only release; stays `fb60a59`). Pending deploy-time actions: none. |
| **v24.25** | **Point release — Closed** | **RELEASE — zone entry locks & Convergence areas (#41 founding ticket ← #95 dependency).** One founding ticket, one brief, per the release scope law. Locks are world data, keys are player data, nothing derives from `danger_level` (§2.12, new section): `Zone.entry_requires_zone` (nullable self-FK, `SET_NULL`; schema migration `0043`) authors a zone's entry requirement; `ZoneCompletion` (unique `(character, zone)`, `completed_at`) is the permanent key — minted for every zone whether or not a lock requires it, never revoked by any path. Keys mint inside `record_room_visit`, the fog-of-war choke point all six arrival paths already call (connect, move, travel, flee, home, respawn): first visit → distinct-visit count vs zone room count → equality mints via `get_or_create`, announced once from `ZONE_COMPLETE_LINES` (reward voice, after the room render, names the completed zone, never what it unlocked) only on newly created rows. Enforcement is one shared helper `check_zone_lock` gating `cmd_move` (before any state change) and `cmd_travel` (before departure messaging); intra-zone movement always passes — no character is ever ejected from a zone they stand in; refusals draw from the door-agnostic `ZONE_LOCK_REFUSAL_LINES` (warn voice, names the required zone and its most-unexplored Area, never counts; `_NO_AREA` fallback pool). Travel listing keeps locked destinations listed and matchable — discovery is never hidden — rendered through the existing `muted` seg voice, zone heading keeps its theme color, no new color literal (chart set-equality green). Grandfather data migration `0044`: every existing character gets the Convergence key unconditionally plus honestly computed completions from their `RoomVisit` history; reverse is a deliberate no-op (keys survive rollback). Convergence areas (#95): The Everround (`the-everround`, `#C9AE7A`, the 40 ring rooms) and Morra's Smithy (`morras-smithy`, `#C0855C`, both smithy rooms) — every Convergence room except the deliberately area-free Heart now belongs to a named Area; contrast vs `#0D0D0F`: 9.08:1 and 6.24:1, both ≥ 4.5:1. The Verdant Reach's lock is authored to The Convergence — the only lock in the world; the Convergence itself is authored open. Five §2 markers swept at closeout (text landed with the design session, GDD-first law). 603/603 tests (+14, `tests/test_zone_locks.py`; `test_room_visits.py` adjusted to the `(first_visit, zone_completed)` tuple return — the brief's specified signature change, reported not silent). Operator playtest successful against the dev stack (checklist items 1–2 resolved to the revelation-law behavior predicted in the closeout's OBSERVATION block — a minute-zero character has no revealed Verdant nodes to see muted; operator confirmed expected, no issue filed; the muted-row state is real, tested, and forward machinery for retroactively authored locks). Architecture doc stamped 24.25 in place, hash moved to `276da2b` (architectural — new model, new gate machinery). Pending deploy-time action: production reseed (`make seed-prod`, bare, own confirmation; expected deletions 0) in the closeout tail's deploy window after the code deploy — which applies migrations 0043/0044, the grandfather riding the migrate. |
| **v24.26** | **Point release — Closed** | **RELEASE — shard relay & attunement (#38 founding ticket ← #30 dependency).** One founding ticket, one brief, per the release scope law. One home concept, player-set (§2.11): `Character.attuned_node` (nullable FK → `TravelNode`, `SET_NULL`, `related_name='attuned_characters'`; schema migration `0045`) replaces the removed `recall_room` — null means the founding node (the Heart of the Convergence), so existing characters are unchanged by construction, no data migration (ruling B2); `recall_room` survives only in migration history, and the broader recall vocabulary is gone from the app outside migrations and the out-of-scope `no_recall` room flag. The **effective home** resolves through the shared sync helpers `resolve_home_node`/`resolve_home_room` in `models.py` (attuned node when bonded, else the founding node), consumed identically by the consumer (`get_home_room`, replacing `get_heart_room`) and the tick engine's death path. **`attune`** is a bare verb (chart fn 2) with exactly the three ruled cases: no node here → warn from `ATTUNE_NO_NODE_LINES`; the room's node equals the effective home (null compares as the Heart) → warn from `ATTUNE_ALREADY_LINES`; else an atomic `.update(attuned_node=node)` and a pooled ceremony line ending in the exact parenthetical `(Home: {travel_name})` (success voice). No combat gate — structurally safe, every attunable node is a safe room; the central deny-by-default dying gate refuses it. **The relay (#30):** the checkpoint sender refusal is deleted; `get_revealed_destinations` gains `spheres_only` (a `node_type='obelisk'` filter on the standing revelation check) and both travel paths pass `spheres_only=(node.node_type != 'obelisk')` — a shard lists, completes, and sends to revealed spheres only, never to another shard; revelation law untouched; the no-node refusal and the listing opener/empty-pool lines gained shard-voice wording; listing format, departure/arrival `TravelMessage` pools, and the zone-lock gate untouched; the pre-v24.26 destination-only asymmetry is retired. **`home` delivers to the bond**, resolved at countdown *completion* (a bond changed mid-fog lands at the new home); the already-home kindly refusal compares against the effective home room; the arrival ceremony stays the Heart's fog-motif shape wherever home now points (explicit §2.11 ruling). **Death respawn follows the bond** (full bars, visit recorded, unchanged message shape — the `'your recall point'` fallback string became `'your home'`). The stats sheet gains the `Home: {travel_name}` row directly under the Player line. The once-planned recall scroll is retired — killed, not deferred (#38). Eleven markers swept at closeout (§2 ×9, §3 ×1, §9 ×1 — text landed with the design session, GDD-first law; issue-carrying markers sweep to the shipped `(v24.26, #NN)` provenance form). 630/630 tests (+27, `tests/test_v24_26_brief1.py`; the `test_room_visits.py` respawn test converted to the attuned-node shape with intent preserved; factory `recall_room` kwargs dropped across six test files). Operator playtest successful against the dev stack. Architecture doc stamped 24.26 in place, hash moved to `ba6f3e5` (architectural — Character schema change, new command, changed travel topology). Pending deploy-time actions: none — migration `0045` rides the closeout tail's `make deploy-prod` migrate; no seed reruns (seed-owned deletions expected 0, actual 0). |
| **v24.27** | **Point release — Closed** | **RELEASE — character hard delete (#234).** One founding ticket, one brief, per the release scope law. Character deletion is **hard delete, only** (§3.8, new section): no soft-delete model, no undo window, no name retirement — the row dies, the cascades run, and the case-insensitively unique name frees for immediate reuse; the **Django admin console is the only deletion surface** (no in-game command, no management command, no player self-delete), the confirmation page's cascade summary the deliberate final check. **Items die with the character:** `ItemInstance.owner` `on_delete` `SET_NULL` → **`CASCADE`** (schema migration `0046`, every other attribute unchanged) — the entire inventory, held and equipped, bound and unbound, removed at the Django-collector level; the old `SET_NULL` stranded whole inventories as all-NULL-location rows outside the exactly-one-location invariant (the collector bulk-updates around `save()`, so the #137 check never fired). Pre-existing orphans swept one-time by data migration `0047` (unconditional deletion of the all-NULL-location shape — always correct by the invariant's definition; prints the deleted count, deliberate no-op reverse): **1 row deleted on dev**, expected 0 on prod (no character ever deleted there). `soulbound_to` stays `SET_NULL` by ruling — bound items can never leave inventory, so every row it references dies in the same owner cascade. **Survivors, deliberate:** world drops and corpse contents (owner already NULL by construction); corpses they killed (`killed_by=NULL` — lootable-by-nobody, natural decay, `npc_name_snapshot` intact); the auth `User` (the cascade runs User→Character only). **Consumer:** a deleted-while-connected character's next command raises `Character.DoesNotExist` out of `_dispatch`, caught in `receive_json` ahead of the #20 catch-all guard and answered with the connect-time no-character routing verbatim — the `'No character found. Create one to play.'` error line, the structured `redirect` envelope to the character creator, socket close. **Tick engine: no code change** — the brief's zero-character session close was verified already implemented (the combat-v1 round-boundary participants guard closes an empty-character session through `close_session` — `is_active=False` plus `release_session_npcs` per #25 — within one combat round) and is now test-pinned; recorded as a deviation, the brief's premise having expected a gap. §3.8 marker swept at closeout (text landed with the design session, GDD-first law; issue-carrying marker sweeps to the shipped `(v24.27, #234)` provenance form). 638/638 tests (+8, `tests/test_v24_27_brief1.py`: schema pin, cascade correctness, no-orphan shape, survivors, name reuse, 0047 predicate via the shipped migration module, zero-character session close, consumer guard end to end). Operator playtest successful against the dev stack (one design-level finding filed with operator assent → **#243**: the dispatch guard fires only for fresh-fetch commands — `inv`, reading cached state, rendered a benign empty inventory instead of routing; not a bug against the brief's spec, whether detection should be command-independent is the design question). Architecture doc stamped 24.27 in place, hash moved to `75cede1` (architectural — schema change + consumer behavior). Pending deploy-time actions: none — migrations `0046`/`0047` ride the closeout tail's `make deploy-prod` migrate; no seed changes. |
| **v24.28** | **Point release — Closed** | **RELEASE — the tier-material ladder (#211 founding ticket ← #245 dependency).** One founding ticket, one brief, per the release scope law. The ladder is **eight rungs, 96 definitions** (§6.3) — copper 1, silver 2, gold 3, platinum 4, rhodium 5, iridium 6, osmium 7, sphaerium 8 — twelve accessories each (six stats × ring/amulet); the seven unshipped rungs ship as **84 new accessory `ItemDefinition`s**, each mirroring the v18 copper set exactly. **Rung membership becomes a data fact rather than a naming convention:** `ItemDefinition.tier_material_mk_min` / `tier_material_mk_max` (schema migration `0048` — two nullable `AddField`s plus an `AlterField` for the corrected `suppress_mk_suffix` help text; existing rows take NULL, correct by construction since only the seed authors membership). **Sphaerium is the terminal, unbounded rung** (#245): `tier_material_mk_max` is NULL — the rung covers Mk 8 upward without limit — and it is therefore the one rung that does **not** suppress its Mk suffix, because a rung with no ceiling cannot say its tier by material name alone (a Mk 8 and a Mk 47 piece would otherwise render identically, the exact defect the release exists to remove); a sphaerium piece reads *Sphaerium Ring of Strength Mk 15*. **`suppress_mk_suffix` is un-overloaded** — a display flag and *not* ladder membership, independent in both directions: the v19 freebie kit suppresses off the ladder, sphaerium joins the ladder without suppressing. **The guard:** `generate_item_instance` gains a range check as the first statement in its body — a ladder definition can no longer be instantiated outside its rung, the `ValueError` naming the slug, the bound (`Mk 3` bounded, `Mk 8+` unbounded) and the offending tier; both live generation paths funnel through it (the loot-drop roll and `do_buy`'s vendor path), so one guard binds them both plus every shell and admin caller. A **deliberate residual gap** stays open by ruling: direct ORM construction is unguarded — a save-time check would make any pre-existing mismatched instance unsavable, turning a naming defect into an unrepairable row (the scope law's leave-no-landmines clause). **One curve for the whole ladder** (#211 ruling): every rung carries stat authorship byte-identical to its copper counterpart and the engine's `midpoint = base + factor × mk_tier` does all the tier progression — 2.8 at copper's Mk 1, 4.9 at silver's Mk 2, 15.4 at osmium's Mk 7, 32.2 at sphaerium Mk 15, and upward without limit; per-rung midpoints were considered and rejected, as was pricing the rungs against the currency ladder (`base_value` is 30 at every rung, valuation's per-tier multiply doing the rest). **Rungs 2–8 ship with zero drop-table and zero vendor entries** — Z02 through Z08 do not exist yet; seeding the ladder complete now is exactly what the V24 new-zone-prep major is for, at near-zero marginal cost. Seed reconciliation on dev: `ItemDefinition` **84 created, 12 updated, 0 deleted** (the 12 being the copper set gaining its range), idempotent on a consecutive second run; five new verification assertions (rung counts, range shape, suffix shape, one-curve equality, loot/vendor entries inside their rung). Read-only mismatch survey on dev: **0 rows** outside their rung. Two §6.3 markers swept at closeout (text landed with the design session, GDD-first law). 653/653 tests (+15, `tests/test_v24_28_brief1.py`: schema pin, the guard raising/passing/inert/across bounded rungs/at the unbounded rung, ladder completeness, range and suffix shape, one-curve equality, tier progression, display, suppression-is-not-membership, and zero drop/vendor exposure above copper); no existing test required changing. Operator playtest successful against the dev stack (one wording finding filed → **#246**: the brief's playtest checklist said "admin-gift", which reads either as the guarded shell helper or the unguarded Django admin add form — a checklist trap that would misreport the guard as broken, not a code defect). Architecture doc stamped 24.28 in place, hash moved to `8d166a7` (architectural — new model fields + new generation guard). Pending deploy-time actions: **the production seed rerun** — migration `0048` rides the closeout tail's `make deploy-prod` migrate, then `make seed-prod` (expected 84 created / 12 updated / 0 deleted). |
| **v24.29** | **Point release — Closed** | **RELEASE — the `plunder` setting (#235 founding ticket).** One founding ticket, one brief, per the release scope law; the brief carried two riders sharing the release — #249 Part 2 and the #250 fix. **`plunder [on|off]`** (§9.1, §5) is a settings command, **default off**, that runs the rights-scoped corpse sweep automatically at the moment combat ends: `Character.plunder_mode` (schema migration `0049`, one `AddField`) joins the settings family as its fourth member, going through the shared `_cmd_setting` helper and occupying all five registration sites — and **deliberately staying out of `COMBAT_BLOCKED`**, so a mid-fight flip governs that same fight. It adds **no new capability**: plunder takes exactly what bare `loot` could have taken at that moment and nothing else. **The load-bearing change is structural:** the sweep moved out of `SkylandConsumer._loot_sweep` into a new **`loot_utils.py`**, where `sweep_corpses` is synchronous, performs the mutations and **returns** the lines instead of sending them — the tick engine is a different process with no consumer, so a sweep that sends could not be shared; the consumer became a transport over it and its ORM wrappers now delegate, leaving one implementation of each. A move, not a redesign, with the existing loot suite passing unedited as the regression bar. One recorded deviation on the helper's signature: `sweep_corpses` returns a **pair** (`messages`, `room_lines`) rather than the brief's single ordered list, because the corpse-disposal announcement was never a personal line but a room-wide broadcast — each transport now broadcasts it on its own channel (the consumer via `group_send`, the engine via its room accumulator); the signature adaptation §5 explicitly permits. **The trigger is anchored, not invented:** plunder fires wherever `Combat has ended.` is delivered and nowhere else — three sites in `run_tick_engine.py`, all on the same no-living-NPCs condition. **Flee and death are excluded because the anchor excludes them** and deliberately carry no guard of their own; both exclusions are pinned by test. **The silence contract is ruled and tested:** plunder emits nothing whatsoever when it has nothing to take, and `cmd_loot`'s two refusals are never spoken on its behalf; no connected player is required. Output identity was verified live on dev — the plunder path and the real typed-`loot` path were run over two identical corpse sets and produced **byte-identical line sequences**; the check built and removed its own fixtures (0 leftover rows), so the release leaves no standing dev-only DB state. **The read-only verification family (#249 Part 2, riding this release per the ruling that a base class gets no dedicated release):** `verification.py`'s `VerificationCommand` — a forced-rollback atomic block so no verification can ever write, exit code as the outcome signal (0 clean, nonzero findings), report-never-repair — plus **`verify_ladder`**, the tier-material survey V24.28 Brief 1 specified and had no sanctioned path to run, which is what filed #248. Dev result: **0 mismatches out of 8 ladder rows**; the dev-path gates both refuse correctly (bare `make verify` and a non-`verify_*` name, exit 2 each, `.env` posture untouched afterwards). **#249 stays open and carries no milestone** — it ships work in this release but outlives it; Part 3 (retiring the Instructions v33 interim rule) is an ops session's work after this release lands. **#250** — `_set_echo_mode` assigned `show_timestamps`; the stray line is deleted rather than corrected, since `cmd_echo` already maintains the cached attribute. Three markers swept at closeout (§5 ×1, §9 ×2 — text landed with the design session, GDD-first law; issue-carrying markers sweep to the shipped `(v24.29, #235)` provenance form). 683/683 tests (+30, `tests/test_v24_29_brief1.py`, covering all 23 assertions the brief required); no pre-existing test edited beyond the version pin. Operator playtest successful against the dev stack. Two follow-ups filed post-ritual at operator direction, neither in this milestone and neither blocking: **#251** — all config-command setters should write both the cached attribute and the DB row, which resolves the brief's second recorded deviation the *other* way (the operator ruling is that `_set_plunder_mode`'s shape is correct and the three older setters come to it); **#252** — briefs assert unverified facts about existing code and no gate checks a brief for technical coherence, filed as the procedural cause of #251 and destined for a future Instructions edition. Architecture doc stamped 24.29 in place, hash moved to `f0c12e3` (architectural — new model field, new shared module, new management-command family). Pending deploy-time actions: **the production ladder verification** — migration `0049` rides the closeout tail's `make deploy-prod` migrate, then `make verify-prod VERIFY=verify_ladder` (expected 0 mismatches, exit 0), the **first live exercise of the `verify-prod` target** #249 Part 1 shipped and the settlement of V24.28's handed-off survey. No seed run and no data mutation required. |
| **v24.30** | **Point release — Closed** | **RELEASE — uniform config setters (#251 founding ticket, no dependencies).** One founding ticket, one brief, per the release scope law. **No GDD change and zero player-visible behavior change** — the v22 settings standard (§9.1, Settings) is untouched; what the release removes is a latent class of bug inside the consumer. The four settings commands shared one helper but not one setter shape: `_set_brief_mode`, `_set_show_timestamps` and `_set_echo_mode` wrote only the DB row and left the cached `self.character` attribute to the calling `cmd_*`, so **any direct call to a setter left the cache stale** — correctness by the caller's cooperation rather than by construction. The ruling (operator, 2026-08-15): every config setter writes both, generalizing `_set_plunder_mode`'s v24.29 shape. Its consequence, ruled with it: the setter becomes the **single writer** of the cache, so the now-redundant caller-side assignments in `cmd_brief`, `cmd_echo` and `cmd_plunder` are **removed** rather than left in place — keeping them would preserve the caller-maintains-the-cache pattern the ruling exists to kill. `cmd_brief` and `cmd_plunder` lose their `if value is not None:` blocks entirely (the assignment was the whole body); `cmd_echo` keeps its block for the fresh fetch and status payload inside it. **`cmd_timestamps` is unedited and is the point of the change** — its set path deliberately bypasses `_cmd_setting` (the status payload must precede the confirmation line so the confirmation renders under the new preference) and calls the setter directly: the third instance of the fragility, correct before this release only because the subsequent `get_character_fresh()` replaced `self.character` wholesale, and now correct by construction. **No live staleness bug was fixed** — every gameplay read of the four settings was already fresh (`send_room_description` fresh-fetches before `brief_mode` is read, `_status_payload` reads its callers' fresh fetch, `loot_utils.get_plunder` re-reads by pk at combat end, the connect-time payload reads the connect-time object). No model change, no migration, no seed data, no shared surface; no fresh-fetch or deleted-guard logic was added to any set path (#243 stays open and deliberately out of scope). 687/687 tests (+4, `tests/test_v24_30_brief1.py`: each setter called **directly** writes both the DB row and the cached attribute, driven both directions — the issue's exact complaint pinned; each of the four commands leaves row and cache in step, `timestamps` pinning the direct-call path; and the bare and invalid forms still answer the v22 settings standard after the two conditionals were removed); no existing test required changing. One minor deviation: removing the caller-side assignments left assigned-but-unused locals in `cmd_brief` and `cmd_plunder`, on which the brief was silent — both became bare awaits, the file's own idiom for a discarded return. **First release run under Instructions v36's technical pre-flight (#252):** all seven of the brief's structural claims about existing code were diffed against the code before any edit — **zero mismatches**, no hard stop. Operator playtest successful against the dev stack. Architecture doc stamped 24.30 in place, hash moved to `53c6da8` (runtime code change). No markers to sweep — no GDD text landed for this release. **No pending deploy-time actions:** nothing for the closeout tail beyond the ordinary `make deploy-prod`. |
| **v24.31** | **Point release — Closed** | **RELEASE — deploy-target build-exhaust sweep (#205 founding ticket, #255 dependency).** One founding ticket, one brief, per the release scope law. **The first release whose entire implementation lives in the repo-root `Makefile`** — no game code, no model change, no migration, no seed data, **no GDD change and nothing player-facing whatsoever** — no markers to sweep, because no GDD text landed for this release. Every `make build` left exhaust on the daemon it ran against — orphaned (`<none>`) image records plus BuildKit cache entries — and nothing swept it: production's root volume climbed 20% → 58% across ten releases (~500MB each) and the dev VM accrued ~2GB per build, both needing manual operator catch-ups. **Both deploy targets now sweep automatically** after deploying, image prune then builder prune, sized by `PROD_BUILDER_PRUNE_FLAGS` / `DEV_BUILDER_PRUNE_FLAGS` (`:=`, deliberately not overridable from the environment). **The reconciliation that determined the fix:** the issue body ruled a dangling-image prune only, but `docker image prune` reclaimed ~0B on both daemons — the dangling images' layers were *also* held by build-cache references, so pruning the image records released records, not bytes; the builder prune releases the last references and the layers actually die. Both prunes ship, and **the builder prune is the load-bearing one**. **Eviction is size-capped rather than `-a`**, and the wording of that ruling was **corrected during implementation** (operator-directed, 2026-08-15) after the brief's §6.4 premise proved false about pre-existing behavior — a v36 hard stop, raised before any workaround: the original justification ("the next deploy's expensive layer (pip) is still a cache hit") was never true, because `make build` passes `docker compose build --no-cache` by design and no build has ever read the BuildKit cache (verified by two consecutive bare `make build` runs with no prune between them — pip rebuilt both times while the cache grew). The cap is therefore kept as a conservative, free bound, not as a cache-preservation measure; **the `-a` prohibition that is genuinely load-bearing is on the *image* prune**, which stays dangling-only so tagged base images are never deleted and cold-re-pulled (the 2026-07-29 slowdown). **The release shipped a per-target flag divergence on a false premise** — *corrected by ops, 2026-08-15, #257:* prune flags are parsed **client-side** by the local CLI (`DOCKER_HOST` redirects only the API call), so no by-daemon spelling requirement ever existed; the closeout tail's first prod run proved it (the CLI accepted `--keep-storage` as a hidden deprecated alias). The ops correction dropped the deprecated spelling and prod's cap entirely (prod's dedicated daemon holds only never-read cache) and hardened the silent `-` error-ignore prefixes into loud-but-non-fatal `|| echo WARNING` forms. On `deploy-prod` the sweep runs **last, after the posture restore**: both prunes pin their own `DOCKER_HOST` and neither reads `.env`, so not even a Ctrl-C during a long prune can strand production posture. Dev results across four swept deploys: build cache 26.86GB → 5.85GB, **21.55GB reclaimed** on the first, ~0.5–1GB per deploy at steady state, reclaimable held at 5.27GB against the 5GB (5 GiB) reserve, base image resolved with zero layer downloads every time, `.env == .env.dev` after every run. **#255 rides this release** (ruled onto it rather than a separate ops session, since both rewrite the same architecture-doc table): §2.2's Makefile target table documented a nonexistent `make reset` and omitted the entire deployment and guard surface — rewritten target-for-target against the Makefile, `reset` deleted (not renamed — `nuke` is materially different and gets its own row), the four posture-setting deployment targets and both check-only guards documented, and the sweep described below the table. 687/687 tests, **count unchanged** — the Makefile is not under test in this repo, and no existing test required changing beyond the version pin. **Second release run under Instructions v36's technical pre-flight (#252):** all ten of the brief's structural claims were diffed against the code before any edit — **zero mismatches** — and the false premise it did catch was caught by §6.4's own verification step, resolved as a hard stop to the operator, with the shipped Makefile byte-for-byte what §4 specified. Operator disposition: **no playtests for this brief** (terminal — no playtestable game surface). Architecture doc stamped 24.31 in place, hash moved to `45b9749` (the deployment procedure itself changed). **No pending deploy-time actions:** the closeout tail's ordinary `make deploy-prod` performs the first production sweep and is asked only to record what the two prune lines printed. |
| **v25.0** | **v25 — Closed** | **RELEASE — Monitoring and Command (MC); Version 25 opens (#269 founding ticket; #260 and #264 milestone siblings).** One founding ticket, one brief, per the release scope law. The major renames the firehose to **MC — Monitoring and Command** and ships ahead of new zones so AI actors are unblocked (operator ruling 2026-08-16); **v25.0 ships no functional change** — the design pass, the doc pass, and the version bump only; server behavior is byte-identical, and the first real change lands in v25.1 (#37, the sink). The doc payload landed with the design session at `5da479f` per the GDD-first law, executing the 2026-08-17 ruling set (indexed on #269): new **§10.11 "Monitoring and Command (MC) — Total Capture"** (#260) — nothing in the game is private; the DM clause design-ahead and binding; three speech sources including generated speech (#265), with sudo's voice out-of-world (#262); the capture mechanism deferred to v25.1 and marked as such in place — creation-level capture, one record per event with the audience recorded as a field, Redis Streams hot tier + PostgreSQL durable record (#37); §10.5's "never persisted" list reversed to a pointer at §10.11 and §7.1's logging line re-pointed (capture serves balance, analysis, and AI actors, not only moderation); the nine-reference firehose→MC terminology sweep (GDD §9/§10/§12, architecture doc — its delivery-choke-point passage rewritten per the capture ruling: the choke point is the envelope stamp, **not** the MC tap — and the project instructions); and the zones retheme, unpinned ("Version 25 = new zones" retired — zones move to a future major, #264). Brief 1 (implementation): the version start plus a five-reference **comment/docstring-only** firehose→MC sweep in the game code (`envelope.py`, `consumers.py`, `models.py`), the two false designated-tap claims corrected to the ruled architecture (MC captures at creation level, #37/#33). **Third release run under Instructions v36's technical pre-flight (#252): zero mismatches.** No model change, no migration, no seed data, no template/static change, no new tests; 687/687 tests, count unchanged (no test edited beyond the version pin). Operator playtest successful against the dev stack. Architecture doc stamped 25.0 in place, hash unmoved (a comment-only sweep is not architectural). No markers to sweep — this release's GDD text landed complete, its only pending-implementation marker naming v25.1. Major-opening mechanics at closeout: `GDD_MAJOR` → 25, monolith renamed `Shyland_GDD_v25.md`, architecture doc renamed `Shyland_Architecture_v25.md` (its v25-era rename assigned to closeout by Brief 1 §8's standing-mechanics note). **No pending deploy-time actions:** nothing for the closeout tail beyond the ordinary `make deploy-prod`. |
| **v25.1** | **Point release — Closed** | **RELEASE — the MC sink ships: "the firehose works" (#37 founding ticket; #271 dependency; #272 emergent).** One founding ticket, one brief, per the release scope law. §10.11's deferred capture mechanism is now built exactly as ruled: **creation-level capture in both processes** through one audited choke point (`apps/shyland/mc.py`'s fire-and-forget `mc_emit` — whole body guarded, a sink failure drops the record and never raises into game code, at most one warning per 60s). Consumer taps: command ingress at receipt (accepted or rejected, tab-completion requests included — no outcome field; rejections read from the adjacent `out` records), `connect`/`disconnect` presence, the personal-out helpers, the direct creation sends, the tapped `send_status` consolidating seven status sites, and the `mc_group_send` broadcast wrapper (after which `channel_layer.group_send` appears in `consumers.py` only inside the wrapper — grep-enforced), audiences resolved at fan-out honoring all three exclude semantics, `token` stripped. Ticker taps live inside its two outbound funnels only (`send_to_player` = one record per call, `actor_name='ticker'`; `broadcast_to_room` presence-filtered). Protocol chrome excluded per the §10.11 ruled line (`ping`/`pong`, the connect-time verb list, completion responses). **Hot tier:** Redis Stream `mc:events`, `XADD maxlen=MC_STREAM_MAXLEN` (default 100000, approximate — a stream cap set in configuration, not code, as §10.11 Retention requires). **Durable tier:** `MCEvent` (migration `0050`) — loose ids plus denormalized names, no FKs into live tables, append-only with the repo's first **read-only admin**; drained by the new `mc-persister` sixth container (consumer group, crash-recovery reclaim, ack-after-write, idempotent replay, malformed-stored-raw, SIGTERM-graceful). **#271 fixed:** the `REDIS_HOST` settings constant is born (with `MC_STREAM_MAXLEN`), the presence URL builds from it, the two inline env reads re-point at it; **#272 (emergent, operator-directed in-session):** the ticker's `_online_character_pks` presence reader was the second hardcode site — fixed the same session; no literal `redis://redis` endpoint remains anywhere in the app. Operator-authorized shared-surface edits: `docker-compose.yml` (the service), `settings/base.py` (the constants), CLAUDE.md's Redis line. Suite **687 → 702** (`test_mc_sink.py` + `test_mc_persister.py`, 15 net new); dev-proven live: stream and rows in lockstep, the `say` `cmd` row preceding its broadcast's `out` row, persister stop/start with zero-gap catch-up. **Fourth release under Instructions v36's technical pre-flight (#252): zero drift** across every §2 structural claim. Operator playtest successful against the dev stack; playtest surfaced the designed no-outcome-field property live, filed as #273 (unmilestoned — the future agent layer reads perms from the DB at interpretation time). Architecture doc stamped 25.1 in place, hash moved to `345f09d` (architectural). Markers swept at this closeout: the four §10.11/§10.5 pending-implementation parentheticals naming v25.1. **No pending deploy-time actions:** the closeout tail's ordinary `make deploy-prod` builds the image, runs migration `0050`, and brings up `mc-persister` as compose reconciliation; the production stream starts empty and fills from live play. |
| **v25.2** | **Point release — Closed** | **RELEASE — combat instrumentation (#33 founding ticket, no dependencies).** One founding ticket, one brief, per the release scope law. §10.11's combat-family passage is now built exactly as ruled: **seven `combat_*` kinds join `mc:events`**, recording what the engine rolls — including what no player ever sees (a graze prints as an ordinary hit at half damage; the record says graze; roll interiors were discarded until now). `combat_start` (one per encounter — the full identity snapshot: character level/archetype/origin/effective stats/bars/TAV and each NPC's definition, Mk tier, level, stats, vitality max, plus zone and room), `combat_join` (a participant entering live, own snapshot), `combat_round` (the initiative contest only), `combat_action` (the atomic unit — the to-hit contest, the damage decomposition with pre- and post-mitigation values, lifesteal, and the landed hit's effect applications), `combat_flee` (the contest's rolls and outcome), `combat_death` (the fall and death execution), `combat_end` (outcome win/loss/flee/wipe/disengage at all 8 end sites, duration in rounds and wall-clock). Capture reaches the interiors by **additive detailed variants of the six roll helpers** — the plain names delegate to them, the detailed forms make the same random calls in the same order, pinned by seeded equivalence tests asserting both the return value and `random.getstate()`; capture is never load-bearing (every emission fire-and-forget through `mc_emit`), and no combat mechanic, message, or outcome changed. Envelope discipline unforked: NPC-acted records carry an empty actor id (display name and instance/definition ids in the payload), audience always `[]` — internals are addressed to no one — and every combat record carries the combat-session id as the encounter join key. Ordering: a round's internals emit first, in resolution order, before the round's player-facing records — a reader always sees why before what the players saw. `MC_STREAM_MAXLEN` default 100k → 250k (ruling 8 on #33). **No model change, no migration** — the persister is kind-agnostic and the longest kind (`combat_action`, 13) fits `MCEvent.kind`. Suite **702 → 731** (`test_combat_instrumentation.py`, 29 new: seeded equivalence pins, branch coverage, snapshot builders, envelope, ordering, all 8 end sites, kind length, the fall). **Fifth release under Instructions v36's technical pre-flight (#252): zero drift at pre-flight, one mid-session hard stop** — the brief's claim that delegation kept all 8 combat test files untouched and green proved false (17 `mock.patch` sites across 7 files patched the plain `resolve_hit` and went dead under delegation); operator-ruled resolution: mechanical patch-target conversion to the detailed tuples, original test intent preserved exactly, no assertion changed. Dev-proven live: a real ticker fight to a win/kill with every kind verified in both stream and rows (13/13 assertions), per-round internals-first ordering against the `out` records, and the flee contest (won with no exit — `success=true`, `blocked='nowhere_to_run'`); the volume data point §10.11's retention posture waited for: **≈1.03 combat records/sec in-fight** vs the 0.6/sec non-combat baseline. Operator playtest successful against the dev stack; playtest surfaced #275 (carry-capacity stranding on unequip — filed thin, untriaged, unmilestoned). Architecture doc stamped 25.2 in place, hash moved to `7b2c32b` (architectural — §4.19 gains the combat family). One marker swept at this closeout: §10.11's combat-family parenthetical, to the shipped `(v25.2, #33)` provenance form. **No pending deploy-time actions:** the closeout tail's ordinary `make deploy-prod` ships an image build + restart; no migration, no seed, no data actions. |
| **v25.3** | **Point release — Closed** | **RELEASE — the MC egress (#267 founding ticket, no dependencies).** One founding ticket, one brief, per the release scope law. §10.11's egress passage is now built exactly as ruled: **remote agents attach to the MC event stream through a read-only WebSocket endpoint** — `wss://<host>/ws/shyland/mc/`, `MCEgressConsumer` in the new module `apps/shyland/mc_consumer.py`, one routing line — transport only: no actor, no actuation, no kill switch (25.4/#266's territory). The gate is the grant: membership in the **`agents.shyland`** Group (data migration `0051`, the 0034 shape — idempotent, no members seeded; agent service accounts are provisioned operationally, never by code), checked live at connect — unauthenticated rejected pre-accept, authenticated non-member accept-then-close 4403, members receive the full stream (access control is the grant, not a filter: no scoped subscriptions); the consumer never touches the character table (grep-enforced). **Read-only by vocabulary:** inbound is exactly `attach` and `ping`; anything else — a second `attach` included — draws `{"type":"error","error":"read-only"}` and the connection stays open. Protocol: `hello {protocol: 1}` on accept → `attach` (bare = live from now; `after: <id>` = hot-window replay, exclusive, `XRANGE` batches of 500) → live tail. Gaps announced, never silent: a cursor predating the window draws one `gap {requested, oldest}` frame then replay from oldest. Agents own their cursors — stateless `XRANGE`/`XREAD`; consumer groups remain the persister's alone. **The live tail reads from a concrete tail id, never `XREAD $`** — found by the brief's own live dev-stack check: the `$` cursor drops entries landing between calls; the "now" snapshot resolves inside attach handling, making a post-attach ping/pong fence a hard delivery guarantee. Backpressure never reaches the game: `mc_emit` and every game path untouched (grep-enforced); a slow agent is Daphne/nginx's problem. Suite **731 → 744** (`test_mc_egress.py`, 13 new: the three-outcome gate, read-only vocabulary survival, bare-attach live flow, ordered resume-by-id, both gap variants, `entry_to_frame` decode robustness, the migration's group). **Sixth release under the technical pre-flight (#252): no load-bearing mismatch** (one cosmetic line-count drift). Dev-proven live against the genuine stream, twice — the second run adding a 20-second idle soak. **Operator playtest successful against the dev stack; the playtest surfaced the release's one field find:** redis-py 8.1 (what the image resolves for the `redis>=5.0` pin) defaults client-side `socket_timeout` to 5s, racing the brief's `XREAD BLOCK 5000` every idle cycle — after ~90s idle the client lost and the tail died; fixed in-session per workflow step 4 (`LIVE_BLOCK_MS` 5000 → 2000, redeployed, re-playtested — the confirming playtest ran against the fixed build). The persister's identical 5s/5s race (`XREADGROUP BLOCK 5000` — self-healing by design, reconnect churn only) filed as #277. Architecture doc stamped 25.3 in place, hash moved to `b812afb` (architectural — new consumer, new route, new group; new §4.20). One marker swept at this closeout: §10.11's egress parenthetical, to the shipped `(v25.3, #267)` provenance form. **Pending deploy-time actions: none beyond the ordinary** — the closeout tail's `make deploy-prod` builds the image and applies migration `0051` in its ordinary migrate step; no seed, no data actions. |
| **v25.4** | **Point release — Closed** | **RELEASE — the MC kill switch (#266 founding ticket; #277 dependency riding the release).** One founding ticket, one brief, per the release scope law. §10.11's kill-switch passage is now built exactly as ruled, landing before any actor exists (25.5 ships the first): **one lever silences every AI actor at once.** `MCKillSwitch` (migration `0052`) — a database singleton (row pk=1 always; absent row = alive, the designed default — no seeded row; Postgres is the only store whose state survives restarts and reseeds), **config, not history** (the append-only rule governs `MCEvent`, never this row). Every surface routes through one classmethod — `MCKillSwitch.flip`, THE flip choke point: every actual state change emits one `mc_kill` record (`data={killed, surface}`, the flipper as `actor_name`) via the new **`mc_emit_sync`** (`mc_emit`'s sync twin in `mc.py`; byte-compatible record shape, same fire-and-forget law); a no-change flip emits nothing. `is_killed()` reads fresh — no cache, no TTL, no module state, by ruling — and raises on DB failure so enforcement **fails closed**. Enforcement is egress-only this release: `MCEgressConsumer` gains the connect gate (membership first, so the switch leaks nothing to non-members — 4403 unchanged; a killed member draws accept-then-close **4503**, the new close code: killed is not not-authorized), the per-batch replay sever, and the live-loop sever at the top of every wake; persister and ticker have zero switch awareness (grep-enforced). The three flip surfaces: the **`mc <status|kill|restore>`** admin command (§9.1 — `admins.shyland`-gated, footnote-18 stealth extended across all six touch points), the documented shell helper (no game code in the path), and the switch row in the Django admin — editable by design, routed through the choke point (the read-only posture governs MC *records*; the switch is *configuration* — the two rules never touch). **#277 rides the release:** persister `BLOCK_MS` 5000 → 2000, mirroring 25.3's `b812afb` fix for the redis-py 8.1 client `socket_timeout=5s` race; both block constants now test-pinned; an 11-minute idle soak on the deployed dev stack showed zero socket-timeout lines. Suite **744 → 768** (`test_mc_kill_switch.py`, 21 new: singleton/flip/emit contracts, egress refuse + both severs, command gating and stealth; +3 admin-contract pins from the playtest fix). **Seventh release under the technical pre-flight (#252): no load-bearing mismatch** (cosmetic line drift only). Dev-proven live against the genuine stream (engage → 4503 refuse; restore → live flow; kill-while-attached → severed <2s). **Operator playtest successful against the dev stack; the playtest surfaced the release's one field find:** the §7 admin-registration edit had anchored its insertion mid-class, wedging `MCKillSwitchAdmin` between `MCEventAdmin`'s body and its read-only permission trio — both admin surfaces flipped (events editable, switch frozen); fixed in-session per workflow step 4 (`64a49bf` — trio restored, both admins' permission contracts test-pinned, redeployed, re-playtested successfully). Architecture doc stamped 25.4 in place, hash moved to `64a49bf` (architectural — new model, new command surface, egress enforcement; new §4.21). Two markers swept at this closeout: §9.1's `mc` command and §10.11's kill-switch parentheticals, to the shipped `(v25.4, #266)` provenance form. **Pending deploy-time actions: none beyond the ordinary** — the closeout tail's `make deploy-prod` applies migration `0052` in its ordinary migrate step; the switch's initial state is the absent-row default (alive); no seed, no data actions. |
| **v25.5** | **Point release — Closed** | **RELEASE — the agent door (#281 founding ticket; #273 dependency riding the release).** One founding ticket, one brief, per the release scope law. §10.11's agent-door passage is now built exactly as ruled — the game-side half of the first-actor arc: **the MC egress grows from a read-only tail into three inbound vocabularies on one authenticated connection** (`MC_PROTOCOL` 1 → 2) — **tail** (byte-identical to v25.3), **query**, and **action** — dispatched through the new **`mc_door.py`** (only `mc_consumer` imports it). Six query kinds (`commands`, `who_online`, `where_is`, `character`, `items`, `is_admin`) and six action kinds (`answer`, `gift`, `create_artifact`, `strip`, `dress`, `move`), all server-validated, names resolved `iexact`, frames processed serially per connection (the day-one rate discipline — #261/#268 own per-agent scopes and limits). The trust boundary does not move: session auth, live `agents.shyland` membership, no DB/Redis credentials for agents, no player door, no `Character` for agent accounts; **the kill switch covers the whole door** — every query/action frame checks fresh, killed ⇒ close 4503 (fail closed, the v25.4 law); **everything on the record** — one `agent_query`/`agent_action` stream record per processed frame, and every player-visible line the door causes rides the audited send (`out` record with the target-pk audience first, then the group send). Transparency (#261): effect narration tells the truth (`An admin ...`) in the world's standard colors; bots talk in their talking color only — `answer` delivers `sudo: {text}` as the new stamped **`sudo`** category (`--sudo-color: #E24B4A` — error-red's hex under a separable name, no new palette literal), gated by the target's **live `admins.shyland` membership** (#273's delivery gate — `not-admin` otherwise; offline is `ok: true, delivered: false`, never an error). Soulbind law: `gift` is the first production `gift=True` caller of `generate_item_instance` (capacity deliberately unchecked — an admin gift lands regardless of carry state); `create_artifact` hand-authors definition + instance (never through generation; §5.4 spec validation, rarity-word name law enforced at runtime, name/slug collisions = `name-taken`, born soulbound, sell-guard-refused by rarity). `strip`/`dress` ride the new **`Character.outfit_snapshot`** (migration `0053`): snapshot written before any unequip, deliberately bypassing the unequip block (admin tool; the #275 over-capacity state accepted knowingly), always consumed by a dress attempt, one bar-law rescale per action. `move` refuses `in-combat`; online targets get the full arrival treatment through their own consumer (the new `moved` branch, respawn-modeled — a first visit announces zone completion; a `refresh_status` sibling re-syncs the status pane after strip/dress); offline targets get DB + visit only, no broadcasts. Name law: `RESERVED_BOT_NAMES = frozenset({'sudo', 'sirius'})`, refused at character creation with the NPC-collision sentence (no-leak — bots and NPCs indistinguishable in refusal). Shared machinery extracted byte-identical (`rescale_bars_for_gear`, `record_room_visit_sync` — consumer wrappers delegate, the door shares them); the v25.3 `read-only` error string superseded by `unknown-frame` (ruled; pins updated). Suite **768 → 807** (`test_mc_agent_door.py`, 39 new: the frame contract, all twelve kinds happy + error paths, kill-switch sever on both frame types, MC capture, fill-fraction invariance, the moved branch end-to-end, name reservation, the sudo pins). **Eighth release under the technical pre-flight (#252): no load-bearing mismatch** (one range imprecision only). **Operator playtest successful against the dev stack** — all ten checklist items, driven end-to-end through the interactive frame harness; findings all filed, none a defect against this brief: #282 (the answer delivery gate becomes per-agent context — sudo admins-only, Sirius anyone), #283 (pre-existing: NPC first-contact greetings broadcast room-wide in second person, surfaced by the admin move), #284 (nginx login rate limit vs bot reconnect patterns — CHANGE NOTHING NOW ruled); operator ruling, deliberately not filed: the switch does not proactively sever idle never-attached door connections — they are refused at their next frame (fail-closed holds). Architecture doc stamped 25.5 in place, hash moved to `2a50579` (architectural — new module, new protocol, new model field; new §4.22). Three markers swept at this closeout: §10.2's sudo-color chart row, §10.11's agent-door parenthetical, and §3.1's bot-name-reservation parenthetical, to the shipped `(v25.5, #281)` provenance form. **Pending deploy-time actions: none beyond the ordinary** — the closeout tail's `make deploy-prod` applies migration `0053` in its ordinary migrate step; no seed, no data actions; production agent accounts are **not** created this release — that is the 25.6 attach window. |
| **v25.6** | **Point release — Closed** | **RELEASE — the sudo bot (#262 founding ticket; #279 and #284 dependencies riding the release).** One founding ticket, one brief, per the release scope law. §9.1's reversed-silence ruling and §10.11's first-live-actor passage are now built exactly as ruled — the bot-side half of the first-actor arc: **the first live MC actor**, a standalone Python process **`agents/sudo_bot.py`** deliberately outside the Django image (a remote client of the game, exactly like a player's browser — #279's in-repo agents harness proven against dev and closed). Game-side changes deliberately tiny: the version constant, one nginx template line (#284: login `burst=3 → 10`, rate untouched at 5r/m; bot-side, the login cookie is reused across every reconnect, re-auth only on a refused handshake), one gitignore growth (`*.pid`, the conversation file). The bot verifies `hello {protocol: 2}` (refuses to run otherwise), fetches the live verb list via `query commands` into its system prompt — the ruled decline mechanism, zero hardcoded command names, so declines upgrade themselves as commands ship — attaches, and reacts to `cmd` records with `verb == 'sudo'`, pre-checking `query is_admin` as cost discipline (the authoritative gate remains the door's `answer`). Parsing and composition run behind the provider-agnostic **Brain** interface: **`ClaudeBrain`** (official `anthropic` SDK, default `claude-sonnet-5`, per-request token usage logged; `--max-tokens` default 5000 — operator-ruled up from the brief-table 1000 after Sonnet 5's default-on adaptive thinking counted against the cap and starved a think-heavy request into truncation surfacing as silence) and **`StubBrain`** (deterministic, no model, no key — the end-to-end proof minus the model); `ollama` reserved by interface. The tool loop lives in the bot (cap 8): tools = the door vocabulary minus `answer`/`is_admin` (bot machinery, never model choices), schemas mirroring `mc_door`'s param shapes exactly; every model tool call is a proposal the bot executes as a door frame, every result — the full `DoorError` code set included — fed back as a tool result: **the model never touches the game**, and every effect remains a server-validated, recorded door action. Answers deliver via `action answer` (≤2000 chars ellipsis-truncated, model-written `sudo:` prefixes stripped — the door prepends its own). Conversations are bot-side only, as ruled: keyed by admin character name, ≤20 exchanges, 600s quiet expiry (an expired thread is indistinguishable from never answering), JSON-persisted across restarts (gitignored); every request turn arrives stamped `[Name]` so first-person requests resolve against the requester. **Silence is never an error** — not running, unable to parse, killed, or declining all look byte-identical in-pane. Kill posture (§10.11's standing invariant): on 4503 the bot retries quietly and indefinitely, capped backoff 2s → 60s, one log line per attempt cycle; SIGTERM = clean close, conversations saved, pidfile removed. Ops surface (#268 posture): `run`/`status`/`stop` through a pidfile, UTC-Z log stamps, pre-flight refusals logged. Suite **807, count unchanged** — the bot lives outside the Django tree; its proofs ran instead against the live dev stack: the stub-brain end-to-end (17/17 — cmd spotted → `is_admin` pre-check → door round trip → `delivered: true` → sudo-color pane line) and the kill drill (severed 4503 on `mc kill`, quiet retry, unaided reattach on `mc restore`), both re-proven after the operator's venv rebuild on Python 3.14. **Operator playtest successful against the dev stack, on the real model** — nine bot-side findings fixed in-session (double sudo-prefix, location-bar grammar for locations, fresh-queries-over-stale-conversation-memory, speaker identity on every turn, origin capture before every move, UTC log stamps, logged pre-flight refusals, urllib3 import noise, the max-tokens ruling); door-vocabulary gaps found and filed for design as one capability set — #287 (complete item removal, artifacts included), #288 (targeted equip/unequip), #289 (item mutation), #290 (room-directory query). Architecture doc stamped 25.6 in place, hash moved to `37deb96` (architectural — the first bot-side top-level component; new §4.23). Three markers swept at this closeout: §9.1's sudo reversed-silence parenthetical, §10.11's first-live-actor parenthetical, and §12's MC-row parenthetical, to the shipped provenance form. **Pending deploy-time actions: one, human by design** — production `agent-sudo` provisioning (create user, set password, join `agents.shyland`), executor **the operator**, in the closeout tail's deploy window; no seed, no migration; the nginx burst change rides the ordinary deploy bounce, and the bot itself deploys nowhere (it runs operator-side from the repo checkout). |
| **v25.7** | **Point release — Closed** | **RELEASE — granular item control (#287 founding ticket; #293, #288, #289, #292, #295 dependencies riding the release).** One founding ticket, one brief, per the release scope law. §10.11's granular-item-control passage is now built exactly as ruled — the door's item vocabulary: two queries and four actions over existing fields; no model change, no migration, no seed data; every new kind inherits MC attribution and the kill switch from the consumer's frame handling with zero extra wiring. **Queries (#293):** `inventory` — the uncapped owner-wide roster, every instance the character owns, equipped included and flagged (a state report, deliberately unlike the player command's protective selection pools; each row carries the instance id the writes target; `ITEMS_CAP` stays a catalog concern); `item` — one instance at full fidelity, **true state** (curse and identification flags exactly as stored — the no-leak rule governs world speech, which queries never touch), with owner/room holder context. **Actions**, all sharing one write-path addressing (`name` + `item_id`; `not-found`/`not-owner` naming the actual state; **no string-based item resolution on any write path** — a stale id is a refusal, never a guess), one `transaction.atomic()` per mutation, transparent narration to an online holder via the audited send: `remove_item` (#287) — destruction never transfer, the `_strip` posture; **the curse ends with the item** (death-teardown pattern, `removed_by='item-removed'`); artifact removal deletes the one-of-a-kind definition (CASCADE), freeing the name for re-authoring; bar-law rescale + status refresh only when the target was equipped. `edit_item` (#289) — raw-set whitelists: instance-side any owned instance (Mk tier, rarity, rolled stats through the artifact-creation validators, damage both-or-neither-null, durability maintaining the broken invariant); definition-side artifact-only (an ordinary definition is a shared template — refused), renames re-running the unique-name law excluding self; an unknown key refuses the whole request, no partial application. `equip_item`/`unequip_item` (#288) — targeted, one item at a time, resolving slots through the **`cmd_equip` extraction to `item_utils.equip_candidates`** (pure lift, player behavior byte-identical — the existing player-side equip tests passed with zero edits): structural rules always hold (valid slots, slot capacity, two-handed geometry), protective guards yield admin-style (the strip precedent — cursed comes off, over-capacity accepted, #275); >1 distinct displaced-set = `ambiguous` naming each option; equip re-soulbinds; ONE rescale; the outfit snapshot untouched — strip/dress and the targeted pair never couple. Bot-side pile riding the release: `--url` normalized once at config time (#292 — the double-slash login trap; the refused-login warning now names the `Location` header, the tell), six new TOOLS schemas mirroring the door shapes, and the system prompt's two item laws (resolve via `inventory`/`item` before any write, never guess an id; destructive or mutating actions only on explicitly admin-named targets — ambiguity relayed, never picked); **`agents/botctl.py`** (#295) — the fleet's management surface adopted into the repo as one self-locating, stdlib-only Python script (repo root from `__file__` — the copy you run is the checkout it manages; honest exit-code passthrough, gated start/stop polls, a missing venv names its exact fix and never auto-installs). Suite **807 → 840** (33 new door tests, all in-container). **Ninth release under the technical pre-flight (#252): zero mismatches.** Driver spot-checks and the full botctl dev cycle proven against the live dev stack, every frame drawing its attributed MC record. **Operator playtest successful against the dev stack**; playtest-window filings, design-lane: #296 (sudo inventory answers need a game-rendered report delivery) and #297 (the curse system's live loop, ruled with #80). Architecture doc stamped 25.7 in place, hash moved to `bf9c6a4` (architectural — the door's item vocabulary, the bot's item tools, and the first in-repo bot manager; §4.22 grown, §4.23 extended, new §4.24). One marker swept at this closeout: §10.11's granular-item-control parenthetical, to the shipped provenance form. **Pending deploy-time actions: none** — production receives this release as code alone at the closeout tail's `make deploy-prod`; the prod bot restart after deploy is the operator's standing action, and the prod checkout needs no new provisioning (botctl.py arrives with the merge). |
| **v25.8** | **Point release — Closed** | **RELEASE — bot memory and record search (#294 founding ticket; #290, #296, #299, #300 dependencies riding the release).** One founding ticket, one brief, per the release scope law. §10.11's durable-memory-and-searchable-record passage is now built exactly as ruled — permanence and reach for the sudo bot's first week of real use. **The store (#294):** `AgentMemory` (migration `0054`) — generic per-bot durable storage, one row per taught fact: direct `User` FK `agent` (agent accounts are Users, never a Character), `kind` (`waypoint`/`bundle` — kinds own their payload shapes, validated per kind at teach time), `name` ≤ 60 case-insensitively unique per (agent, kind) (the Character-name `Lower()` constraint precedent), JSON `data`, `SET_NULL` `taught_by` audit (audit, not authorization), indexed `created_at`; the namespace shared across admins by design. Door verbs **`memories`/`memory`/`remember`/`forget`**: waypoint `data` exactly `{room_id}` — the room PK and nothing else, the path rendered live at every use; bundle `data` gift-law lines (1–50, every slug a real definition, artifact rarity refused — bundles replay `gift` as fresh generation, memory not a new write power); CI upsert returning `created`/`replaced`; three distinct legible cap refusals (`memory-full` 262,144 rows = 1 GiB / 4 KiB, `payload-too-large` 4096, `too-many-lines` 50), never silent truncation; `forget` by PK only — read-before-delete, the door's mutation discipline. **The record (#300):** **`events`** — time-windowed search over the MC durable record itself (`until`=now / `since`=until−24h defaults; text search bounded to ≤7-day spans with the walk-backwards refusal; indexed filters bound the scan; newest-first, cap 50, 120-char gist) — and **`event`**, the full record by stream id; the record *is* the journal (bots journaling duplicate copies rejected on arrival). **The rooms query (#290):** CI substring search, optionally zone-scoped, zone-then-room order, cap 50, id plus live path — the door's last resolution gap closed; and `move`'s receipt gains `from_room` (origin captured before the move), so "send them back" rides the door's own answer. **The report action (#296):** kind `inventory` — `answer`'s admin gate and offline posture; a door-composed leader in the bot's voice (name + live item count, never model prose), then equipped and carried sections through the player compositions extracted byte-identical to `item_utils` (`table_lines`, `details_cell`, `slot_cell`, `equipment_doll_lines`, `inventory_table_lines`; `SLOT_ORDER` + `STACKABLE_ITEM_TYPES` alongside) — player-facing output byte-identical, pre-existing rendering tests passed with ZERO edits (the 25.7 bar met); `player_message` gains the structured-lines branch; delivery private to the recipient's pane. **Bot-side:** eight new tools plus the durable-memory / record-search / prefer-report standing orders in the system prompt; **(bot, target)-scoped state (#299)** — `sudo_bot.py` pid/convo files derive from a required `--target {dev,prod}`, `botctl` `BotPaths(name, target)` with the target-suffixed log — dev and prod bots coexist in one checkout, `stop`/`status` no longer target-blind; the driver's kinds catalog extended with the eight verbs. Suite **840 → 865** (25 new, `tests/test_v25_8_brief1.py` exactly). **Tenth release under the technical pre-flight (#252): one mis-attribution, not load-bearing** — the brief named `compose_item_line` as the player inv-listing composition; the real table compositions were extracted per the operative byte-identical requirement. Deterministic driver check **31/31 live against the dev stack**; two-target coexistence (#299) proven with the stub brain — zero model calls, no prod-pointed bot ever started. **Operator playtest successful against the dev stack** — after three in-session bot-side prompt fixes, all variants of one pattern (the model inventing values instead of reading them: a false success report without a tool receipt; "already there" from stale conversation memory; guessed `to_room_id`s teleporting through a wrong room), filed as **#302** (make receipts structural, not behavioral — the three standing orders are the mitigation of record until ruled); game side clean throughout, every hop on the record. Architecture doc stamped 25.8 in place, hash moved to `7752dd7` (architectural — the durable store, the record search, the report delivery path, the scoped runtime state). Two markers swept at this closeout: §10.11's durable-memory passage and §10's persistence-table agent-taught-memory row, to the shipped provenance form. **Pending deploy-time actions: none beyond the ordinary** — the closeout tail's `make deploy-prod` applies migration `0054` in its ordinary migrate step; no seed, no data actions; the prod bot restart after deploy remains the operator's standing action, launched through the updated `botctl`, which passes the new required `--target prod` itself. |
| **v25.9** | **Point release — Closed** | **RELEASE — structural receipts (#302 founding ticket, sole milestone member).** One founding ticket, one brief, per the release scope law. §10.11's structural-receipts passage is now built exactly as ruled — the sudo bot never invents a value it should have read from the database: every id it acts on and every action it claims traces to a tool receipt from the current turn, **enforced by machinery, never asked of the model** (the v25.8 prompt standing orders remain in force — defense-in-depth, no longer the only line). Three layers. **Door-side (`move`):** a third mutually exclusive destination key, `waypoint` — exactly-one-of-three replaces the two-key XOR (`bad-params` naming all three); lookup-and-act atomic in the door against the calling agent's own store (the memory verbs' addressing law, `name__iexact`), so the bot never handles a room id for a taught place; unknown waypoint ⇒ `not-found` naming it, a stored room since deleted ⇒ `not-found` naming both the waypoint and the vanished room id (the legible-refusal law); the result gains `waypoint` (the row's cased name) only on the waypoint form — `to_name`/`to_room_id` behavior and result shape byte-identical. **Delivery-side (`answer`):** machinery-only `receipts` — 1–20 non-empty strings ≤ 200 chars (`MAX_RECEIPTS`/`MAX_RECEIPT_LEN`, each violation a distinct `bad-params`); `text` optional when receipts are present (neither ⇒ `bad-params`); delivery is the `sudo: {text}` line as before (skipped when no text) then one door-composed **`sudo did: {receipt}`** line per receipt in list order, all category `sudo`, all through the audited send (receipts on the MC record) — the prefix is door-composed, so model text can never occupy line-start position on a receipt line; offline posture and result shape unchanged; no client change (category `sudo` renders since v25.5). **Bot-side (the typed ledger):** a per-request `ReceiptLedger` — one sudo request = one turn = one ledger — with four id-spaces (room int / item int / memory int / stream str); `_execute_tool` (the single choke point) refuses any checked argument whose value no current-turn successful tool result produced **in the matching space** (`unreceipted-id` error tool_result, the door never called, the model recovers in-loop); harvest is a per-tool result-path map, successful results only — **the typing is the point**: the v25.8 playtest failure passed a receipted integer into the wrong id-space, and an untyped ledger would have licensed it. Alongside it an `ActionLog`: every successful action except `answer` appends one composed receipt (bot machinery from the call's params and the door's result, never model text); identical (slug, mk_tier, rarity, to) gifts aggregate to one `×N` receipt (ids omitted when aggregated); 200-char truncation, cap 20 oldest-kept. `_deliver` sends receipts alongside text, and **delivery happens on text OR receipts** — a silent-model turn with successful actions delivers receipts-only: model prose is commentary, receipts are the record. Schema/prompt tightening: `move` gains `waypoint` (prefer over `to_room_id` for taught places) + exactly-one-of-three; every checked argument's description carries the "from a tool result in this turn" contract; the system prompt's waypoint clause passes the name to `move` directly, and one added sentence tells the model the game renders `sudo did:` lines itself — never enumerate receipts. **Code-only release: no model change, no migration (`0054` remains head — migrate is a no-op), no seed, no client, no new door kinds, no kill-switch change.** Suite **865 → 877** (12 new socket-driven door tests, `tests/test_v25_9_brief1.py` exactly). **Eleventh release under the technical pre-flight (#252): no mismatch recorded.** Deterministic driver check **16/16 live against the dev stack** (scripted-brain SudoBot pipeline over the real door: unreceipted `to_room_id` refused with the door never called; the same id after a `rooms` lookup executing; a room id offered to `forget` refused — the typed-ledger proof; the waypoint move single-hop with the result carrying the name; `sudo did:` lines landing in a live admin pane — text + receipts and receipts-only both). **Operator playtest successful against the dev stack** — and the machinery caught its own quarry live: a model "Saved" claim with no `remember` call shipped with no `sudo did:` line, and the operator caught it from the missing receipt alone; root-caused to the conversation store's text-only replay (the replay trap) and its poisoned-history variant (the model's own earlier false claim persisted as ground truth), both fixed in-session bot-side (a standing order naming the trap; the poisoned dev conversation store reset) — structural findings filed design-lane: #304 (two-dev-bots incident — per-checkout pidfiles blind cross-checkout), #305 (persist receipts with the stored answer), #306 (everything the bot delivers renders deterministically). Architecture doc stamped 25.9 in place, hash moved to `a73fbb0` (architectural — the door vocabulary shapes and the bot's receipts machinery; the final hash lands the playtest-found replay-trap standing order). One marker swept at this closeout: §10.11's structural-receipts parenthetical, to the shipped provenance form. **Pending deploy-time actions: none** — code-only release, migrate no-op, no seed, no data actions; the prod bot restart after deploy remains the operator's standing action (`botctl` with `--target prod`). |

-----

## Table of Contents

1. [Vision & Pillars](#1-vision--pillars)
1. [World Model](#2-world-model)
1. [Character System](#3-character-system)
1. [The Three Bars — Vitality, Acuity, Longevity](#4-the-three-bars--vitality-acuity-longevity)
1. [Combat System](#5-combat-system)
1. [Economy & Items](#6-economy--items)
1. [Social Systems](#7-social-systems)
1. [Quest & Narrative](#8-quest--narrative)
1. [Player Command Reference](#9-player-command-reference)
1. [Technical Architecture](#10-technical-architecture)
1. [Admin & Content Tools](#11-admin--content-tools)
1. [Future Systems](#12-future-systems)

-----

## 1. Vision & Pillars

### 1.1 Concept

Shyland is a free, web-based Multi-User Dungeon (MUD) set in a fractured world where dimensional rifts have shattered the boundaries between realities. Players inhabit a world where a cyberpunk street samurai may cross paths with an elven ranger, where a steam-powered war golem guards the entrance to a gothic cathedral, and where a radiation-scarred wastelander haggling in a medieval marketplace is just another Tuesday.

The anachronism is the point. Genre collision is not a bug — it is the central aesthetic and lore engine of the game.

### 1.2 Design Pillars

|Pillar                  |Description                                                                                                                                                                                            |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|**Combat First**        |Every system should serve or enhance the combat loop. Progression, exploration, and social play all feed back into making combat more interesting.                                                     |
|**Text is Primary**     |The written word is the primary interface. UI chrome and visual elements support the text; they never replace it.                                                                                      |
|**Genre as Flavor**     |Genre differences are expressed through aesthetics, vocabulary, and equipment — not through radically different rule sets. A laser rifle and a longbow use the same underlying ranged combat mechanics.|
|**PvE Core, PvP Opt-In**|The default world is cooperative. PvP is available in designated zones with explicit player consent. Griefing is a design failure.                                                                     |
|**Legible Systems**     |Players should be able to understand what is happening and why at every moment. No hidden dice. Stats, modifiers, and outcomes are exposed on request.                                                 |
|**Free Forever**        |Shyland has no monetization, no premium currency, no real-money transactions of any kind. It is free to play in the most literal sense.                                                                |

### 1.3 Target Audience

- Players with nostalgia for classic MUDs (Diku, ROM, LPMud) who want a modernized experience
- RPG fans comfortable with text-heavy games
- Players who enjoy emergent social gameplay and persistent worlds

### 1.4 Core Constraints (v1)

These decisions are fixed for version one and not subject to revision during initial development:

- Web-based only. Responsive down to phone screen size. No native app.
- English only.
- No real-money transactions. No monetization of any kind.
- No player housing.
- No mounts.
- No seasonal content.
- No off-body item storage. Players carry what they carry.
- Screen reader compatible from day one.
- Single visual theme. No colorblind or high-contrast mode in v1.

-----

## 2. World Model

### 2.1 The Lore of the Fracture

Imagine a Venn diagram of universes. Each universe is its own reality — fantasy, cyberpunk, gothic horror, post-apocalyptic, steampunk, cosmic. At some point in the deep past, these realities collided. Not violently destroyed — *overlapped*. Where any two universes touch, there is tension, bleed-through, anachronism. A fantasy forest where neon signs flicker between the trees. A cyberpunk alley where a knight in plate armor wanders, confused.

But where *all* of them meet — the dead center of the Venn diagram — something unexpected happened. The forces cancelled each other out. The chaos balanced into stillness. A neutral zone emerged, not belonging to any single universe, touched by all of them.

That is **The Convergence**.

Nobody fully understands it. Scholars debate what caused the collision. Some zones have adapted to their neighbors; others remain hostile to anything foreign. This tension is a primary driver of narrative and conflict.

**How players arrive:** Death in a home universe — an honorable death, a death that found peace — is what brings a character to the Convergence. They did not choose to come. The Convergence is not a second chance handed out freely; it is where the worthy end up when their story in one world closes. They wake at the Obelisk, whole, in a place they have never been, with everything still ahead of them.

### 2.2 Zone Architecture

The world is divided into **Zones**, each with a dominant genre identity. Within each zone are **Areas**, which contain individual **Rooms**.

```
World
└── Zone (e.g., "The Neon Sprawl" — cyberpunk city)
    └── Area (e.g., "The Underbelly Markets")
        └── Room (e.g., "Black Market Stall #7")
```

#### Zone Types (v1 set)

|Zone ID|Name               |Genre Tone                                      |Danger Level|
|-------|-------------------|------------------------------------------------|------------|
|Z01    |The Verdant Reach  |Classic fantasy wilderness                      |Beginner    |
|Z02    |Ashenveil Cathedral|Dark gothic horror                              |Intermediate|
|Z03    |The Neon Sprawl    |Cyberpunk megacity                              |Intermediate|
|Z04    |The Blasted Flats  |Post-apocalyptic wasteland                      |Advanced    |
|Z05    |The Convergence    |All genres collide — the world's central hub    |Sanctuary   |
|Z06    |The Iron Deeps     |Steampunk underground                           |Advanced    |
|Z07    |The Pale Shore     |Cosmic horror / lovecraftian ocean              |Endgame     |
|Z08    |The Wastelands     |Infinite scaling zone — always level-appropriate|All levels  |

**The Convergence (Z05)** is the game's social hub — a permanent sanctuary zone where PvP is disabled, vendors of all types exist, and players from all backgrounds congregate. It is the point where all universes overlap and stillness holds. It is also the default logout destination and every character's initial home node (attunement, Section 2.11). The starting area within The Convergence is **Infinity City** — see Section 2.9.

**The Wastelands (Z08)** is a special infinite scaling zone — see Section 2.7.

### 2.3 Areas

An **Area** is a named grouping of rooms within a zone that share a common ambient context. Areas are the middle layer of the world hierarchy — they sit between Zone and Room, giving world builders a tool to express shared atmosphere without repeating it in every room description.

```
Zone → Area → Room
```

Areas are **optional** — a room does not have to belong to an area. Standalone rooms (a remote wilderness clearing, a unique landmark) exist without one. But any multi-room location with a coherent identity — a marketplace, a dungeon wing, a ship, a temple — should be modelled as an Area.

#### What an Area Contains

- **Name** — the location name players see as part of their room header (e.g., "The Eastern Bazaar")
- **Area description** — shared ambient prose that applies to all rooms in the area. Describes the general atmosphere: sounds, smells, lighting, the feel of the place. Written once, displayed in every room that belongs to the area.

#### How Areas Appear to Players

When a player enters a room that belongs to an area, their output has two layers:

1. **Area description** (if present) — the shared ambient text, shown above the room-specific description, rendered in the Area's `theme_color` **(v21)** — the same color as the Area segment of the location bar
1. **Room description** — the specific detail of this individual space, rendered in value-color **(v21)** — the same near-white as the location bar's room segment

(The bracketed `[ Area Name — Room Name ]` header was removed in v20 — place identity lives in the location bar. The v21 per-level prose colors make the two paragraphs visually distinct where they previously read as one undifferentiated block; the server delivers them as separate payload fields.)

**Example — The Eastern Bazaar:**

```
The Eastern Bazaar hums with commerce. Vendors call out from their stalls,
the smell of spices mingles with hot metal and sawdust, and the clatter of
coins fills the air. Torches line the perimeter, casting warm light across
a dozen competing storefronts.

A scarred dwarf stands behind a worn wooden counter, eyeing you appraisingly.
Racks of swords, axes, and shields cover every wall. A grinding wheel spins
slowly in the corner.

Exits: north, out.
```

For a room without an area, the header is just `[ Room Name ]` and no area text is shown — identical to previous behavior.

#### Builder Guidelines

- The **area description** describes the environment — what it feels, sounds, and smells like. It does not describe specific objects or characters that only exist in one room.
- Each **room description** describes what is specific and unique to that room — the vendor, the furniture, the view, the hazard.
- Keep area descriptions atmospheric and timeless. Room descriptions can reference specific NPCs and items.
- An area with no `area_description` still serves a purpose — it groups rooms for admin filtering, minimap clustering, and potential future uses — but players will not see any extra text.

#### Minimap Integration

Rooms belonging to the same area are visually clustered on the minimap. The area name appears as a label on the minimap when the player is inside it. This helps players understand the spatial relationship between rooms that share a common location.

### 2.4 Rooms

Each room is the atomic unit of the world. Rooms contain:

- **Short name** — displayed in the **location bar** as the room segment of the `Zone: Area: Room` breadcrumb. **(v20)** The bracketed in-pane room header (`[ Area — Room ]`) is removed: the output pane clears on every room entry (ruled deliberate), so the render begins directly with the description prose and place identity lives in the location bar alone. A **zone-colored separator bar** (solid, **3px (v21)**, rounded, `Zone.theme_color` at ~0.75 opacity, one text line of vertical presence, aria-hidden) closes each room render, framing *where you are* against *what happens next*
- **Long description** — the room-specific prose a player reads on entering (first visit) or using the `look` command
- **Brief description** — required on every room; non-null, non-blank — no fallback path exists. **Rendering semantics (v19):** the first entry to a room always shows the full text (area description if any + long description) in both modes; revisits with `brief_mode` on show the brief description only (no area text); revisits with `brief_mode` off show the full text; `look` always shows the full text. The area description renders exactly when the long description does — never with the brief line. `brief_mode` defaults to **on** for new characters
- **Area** — optional parent area providing shared ambient context (see 2.3)
- **Exit list** — directional links to adjacent rooms (N, S, E, W, U, D, and custom named exits)
- **Blocked exit messages** — six optional per-direction fields (`no_exit_north_msg`, `no_exit_south_msg`, `no_exit_east_msg`, `no_exit_west_msg`, `no_exit_up_msg`, `no_exit_down_msg`). When a player attempts to move in a direction with no exit, the room's custom message for that direction is sent if set; otherwise the hardcoded default is used. Defaults: cardinals → `"There is no exit in that direction."`; up → `"There is nothing above you."`; down → `"You'd have to dig to go that way."` All six fields are optional; a room with none set uses all defaults.
- **Flags** — booleans that modify room behavior (see below)
- **Contents** — current list of players, NPCs, and items present

#### Room Flags

|Flag        |Effect                                                             |
|------------|-------------------------------------------------------------------|
|`SAFE`      |No combat allowed, NPCs won't aggro                                |
|`PVP`       |PvP is enabled in this room                                        |
|`DARK`      |Players need a light source to see descriptions                    |
|`INDOORS`   |Weather effects don't apply                                        |
|`WATER`     |Swimming/drowning rules apply                                      |
|`NO_RECALL` |Players cannot use recall/teleport abilities                       |
|`RADIATION` |Periodic radiation damage (wasteland zones)                        |
|`HOLY`      |Undead and demonic entities take passive damage                    |
|`MAGIC_DEAD`|Spell and tech abilities disabled                                  |
|`SCALED`    |Room and its contents scale to entering player's level (Wastelands)|

### 2.5 The Map System — Coordinates, MapFrags, and the Client Map (v20)

**Coordinates are the map's positional source of truth; exits remain the connectivity source of truth.** Every room carries `coord_x / coord_y / coord_z` in a **per-zone** coordinate space — pure *map-space*, not physical space: **z is not elevation**, it is a drawing plane. One room per (zone, x, y, z) cell, no exceptions.

**The core invariant:** every *unflagged* cardinal exit (N/S/E/W) between same-zone rooms lands grid-adjacent at the same z (north = (0,+1,0), etc.). The seed's verification enforces this — plus cell uniqueness and flag symmetry — on every reseed, so the world cannot drift out of drawability.

**Boundary flags:** four per-room booleans (`exit_{n/s/e/w}_boundary`, cardinals only) mark exits that are deliberate map seams — a flagged exit has no geometric requirement and severs the map there. Cross-zone cardinal exits are boundaries automatically. Up/down exits have no geometric requirement and always break the map. Any non-cardinal movement verb, present or future, is map-neutral by definition. In Z01, exactly five cave mouths carry the flag (the valley caves and the three Ridge delve approaches).

**MapFrags:** a MapFrag is a *derived, never stored* connected component of rooms linked by unflagged intra-zone cardinal exits. It is what one drawn map shows. The Z01 surface is one 101-room fragment; each cave interior is its own; a room with no cardinal exits is a legal single-room fragment. Exits between fragments still work exactly as ever — **exits are transitions**; the map simply starts a new drawing on the far side.

**Fog of war:** per-character and permanent, via `RoomVisit` — recorded **at arrival** in every path (move, travel, flee, respawn, connect), independent of description rendering. Unvisited rooms are never drawn.

**The payload (v22 — Maps V2, #82):** server-computed on connect and on every room change. Two kinds of entry, and nothing else:

- **Discovered rooms** — the visited members of the current MapFrag (the current room always included) — carry coordinates, `here` on the current room only, `travel_node` (a `TravelNode` exists for the room), `agro` (**configuration, not instance state**: true iff any `RoomSpawn` in the room references an aggressive definition — a dead or unspawned instance still flags), per-cardinal exit status (`known`/`unknown` by destination `RoomVisit`; `gate-known`/`gate-unknown` for boundary-flagged or cross-zone exits), and `up`/`down` tri-state by destination visit.
- **Frontier rooms** — unvisited fragment rooms one unflagged intra-zone cardinal step from a discovered room — carry **exactly `{x, y, discovered: false}` and nothing else, ever**. This is **masking by construction**: an undiscovered room discloses existence only, enforced in the wire format — the server never relies on the client to hide anything. Nothing deeper than the frontier enters the payload; gate destinations never enter the room set at all (they are looked up only for their visit bit).

The build is a **bounded, constant number of queries** (five; guarded by an `assertNumQueries` regression test) — the standing #107 per-tick/per-operation query discipline applied to the map. The client is dumb: it renders exactly what it is sent.

**The client map (v22 — Maps V2):** a fixed **300×300px square at the bottom of the right pane**, north up, a **7×7-cell window** centered on the current room, drawn inside a **pinned 16px margin** (268×268 drawable area — #115's breathing room, solved inside the renderer, not the pane CSS). The visual language runs on the named four-color vocabulary, with one rule of grammar — **stroke color carries room state; solid fills mean points; value-vs-muted carries known-vs-unknown everywhere**:

- **Rooms** — hollow circles (r=10, 2px stroke) in value-color; **agro-color stroke** when the room has aggressive spawns configured. The **here-dot** is a solid key-color dot (r=6) atop the current room's glyph — the map's one key fact.
- **Travel nodes** — the **octagon** (circumradius 12, 4px stroke, flat sides to the cardinals): one glyph for shard and sphere rooms alike — the distinction lives in the travel listing. **Octagons never agro**: no travel-node room may carry an aggressive spawn, a permanent seed-verify invariant.
- **Gates** — an 8px connector from the glyph's outer stroke edge into a solid outward-pointing triangle; value-color if the destination has been visited, muted if not (#53's defect, closed by design — a passed gate is no longer gray).
- **Frontier rooms** — **solid muted dots at half diameter (r=5)** with muted link lines, and **no exits of their own** (the terminus rule): the map admits they exist and says nothing more.
- **Stubs** — solid half-cell lines for exits whose destination lies outside the window: value for a known path continuing off-screen, muted for an unknown one. The old dashed-stub and boundary-tick vocabulary is retired entirely.
- **U/D badges** — independent 14px bold letter badges at the upper-right (U) and lower-right (D) corners, each colored by its own destination's visit state, **tucked** as close to the glyph as possible without touching (per-glyph offsets 12.25 circle / 13.75 octagon, derived from the measured ink of the badge font — the derivation rule lives in the code for future re-derivation).

The attachment law (anything attaching to a glyph attaches at the outer edge of its stroke, never the geometric radius) prevents cross-color overlap. `aria-hidden` — the map adds no information not already present in text, and the text remains the accessible source of truth.

**Design-tool rule:** visual MapFrag diagrams (the same node-and-line rendering) are **required** for all world-layout design work — the map the game draws is the map the designers draw first.
### 2.6 Travel & Navigation

Players move using directional commands: `north`, `south`, `east`, `west`, `up`, `down` (and abbreviations: `n`, `s`, `e`, `w`, `u`, `d`). Named exits use the exit name directly (e.g., `enter portal`).

**Movement costs no action economy in normal exploration.** Combat changes this (see Section 5).

Special travel options:

- **`home` (v22)** — the hearth command: a 10-second delayed return to the player's attuned home node (default: the Heart of the Convergence — attunement is v24.26, #38), from anywhere, narrated as fog-motif atmosphere; broken by movement, combat, or `cancel`; 5-minute completion-only cooldown (timings retuned v23.4, #162). Full design in Section 2.11.
- **The Obelisk Network** — the game's fast-travel system: obelisks send anywhere; checkpoint shards relay to revealed obelisks (v24.26, #30); all nodes are destinations, revealed per-character by visiting them. Free, global, and command-driven (`travel`). Full design in Section 2.11.
- **Zone gates** — the sealed genre-zone gates on the Convergence ring are authored prose (opened per zone as its content ships — the Verdant gate opened in v18). The `ZoneGate` model was superseded and deleted in v18 (Brief 2, migration 0019); the Obelisk Network above is the game's fast-travel system. An opened gate is additionally governed by the zone entry requirements of Section 2.12 — the gate can be open and the way still locked to an unfinished explorer.

Mounts are deferred to a future version.

### 2.7 The Wastelands — Infinite Scaling Zone

The Wastelands is a post-apocalyptic expanse that serves as the game's permanent endgame safety valve. It has no fixed difficulty — the zone scales to match any entering character's level.

**Scaling rules:**

- Enemy stats, HP, and damage scale to the entering player's level
- Loot scales to match — a level 200 character finds level 200 loot (using the Mk system — see Section 6.3)
- In a party, the zone scales to the highest level member
- XP rewards scale appropriately — The Wastelands always provides meaningful XP regardless of player level

**Design purpose:**
When no higher-level content has yet been published, The Wastelands ensures players always have somewhere challenging to go. It is not a substitute for purpose-built high-level zones but bridges the gap between content updates.

### 2.8 Logout Persistence

When a player logs out, their character remains in the world at their exact location for 60 seconds (allowing them to be targeted in PvP zones — a deliberate risk of logging out in dangerous areas), then fades from the world. On next login, they appear at the exact room where they logged out.

There is no safe logout room. Players are responsible for where they choose to go offline.

### 2.9 Infinity City — The Starting Area

**Infinity City** is the starting area of The Convergence zone. It is not a planned city. It grew organically at the point where all dimensional paths converge — the way a city always grows at a crossroads or the mouth of a river, except this crossroads has infinite paths and the travelers arriving on them come from every universe that exists.

The city is old. Nobody planned it. It accumulated. Travelers, refugees, merchants, and wanderers from every universe drifted toward the one place that felt stable, and over generations it became a city that belongs to no world and therefore belongs to everyone.

**Architecture and nature coexist.** The city grew around its trees, not through them. Buildings have roots running beneath their foundations. Vines climb the storefronts. The trees do not stop at the street. This was not a design decision — it is what happened when the city grew up alongside Convergence Park, and the city never saw a reason to change it.

#### Heart of the Convergence — (0, 0, 0)

The starting room and the default home node (attunement, Section 2.11). At its center stands **the Obelisk** — a dark, smooth monolith with as many facets as there are universes, each face ground to a perfect plane that catches light differently. At the Obelisk's heart, suspended inside the stone, is a small sphere that glows white. Steadily. Without flickering. It simply is.

The Obelisk serves as an information point for new players. It speaks in as few words as possible, always the best ones.

#### Convergence Park

A rectangular park (9 rooms wide, 7 rooms tall on the coordinate grid) surrounding the Obelisk. The park is tended but not controlled — nature was here first and the city has respected that. Not all park rooms are navigable paths. Four paths wind outward from the Obelisk to the ring street:

| Path | Direction | Material | Rooms |
|---|---|---|---|
| Wisteria Walk | North | Pale grey stone + wisteria trellises | 4 |
| Bamboo Run | East | Crushed amber gravel + bamboo stands | 4 |
| Basalt Way | South | Dark basalt slabs + flowering moss | 5 |
| Fern Boards | West | Dark timber boardwalk + ferns | 4 |

Each path has a continuous sensory identity maintained through all its rooms, and each path is a named **Area** (Section 2.3) with its own theme color. Non-path park rooms are not navigable; rooms adjacent to lawn areas have custom `no_exit_*_msg` text directing players to stay on the paths.

#### The Ring Street

A 40-room ring street surrounds the park, approximating a circle in the square-room coordinate system. Formally the street is **The Everround** — its own Area — though to the people who live on it, it is simply *the ring road*: a street with an official name and a nickname, exactly as cities do. The ring connects to each path at its cardinal intersection. Walking the ring clockwise from north, players encounter:

- **Seven sealed zone gates** — one per future battle zone, placed clockwise from north in zone build order (Verdant Reach at ~1:00, Ashenveil at ~2:00, continuing through The Wastelands at ~11:00). Each sealed gate has atmospheric `no_exit_*_msg` flavor text hinting at the zone beyond. When a zone is built, its gate is opened by wiring the exit.
- **Four information NPC intersections** — at the north, east, south, and west path/ring junctions, each with a unique NPC and structure
- **Four vendor locations** — each paired with the information NPC across the ring street

The ring street is lined with trees throughout. Sparse content between gates includes closed storefronts, stalls under construction, undeveloped lots, and atmospheric details hinting at the zone beyond each gate.

#### Information NPCs

| NPC | Location | Structure | Personality |
|---|---|---|---|
| The Obelisk | Heart of the Convergence (0,0,0) | The Obelisk itself | Disinterested — operates at a level where everything else is beneath it; speaks as few words as possible, always the best ones |
| Aldric | North ring/path intersection | Ancient hollowed tree, "INFORMATION" carved in old bark | Grumpy but not mean; has been here 40+ years and has opinions about it |
| Info Prime | East ring/path intersection | Vertical metal docking tube, green button to summon | Nearly flat tone; 412 years old; occasionally and unexpectedly poignant |
| Pella | South ring/path intersection | Brightly colored gazebo with climbing vines | Bubbly but not annoying; old; already decided she likes you |
| Seris | West ring/path intersection | Exotic shifting crystal structure | Friendly, doesn't always proffer help; feels like more than looking; cosmic genre |

#### Vendor NPCs

| NPC | Location | Structure | Function | Personality |
|---|---|---|---|---|
| Morra | Across ring from Aldric (north) | Proper smithy building — 2 rooms (exterior + interior) | Blacksmith — repairs and sells weapons/armor | Grumpy because she always works on Mk 1 garbage; reverential toward high-Mk items in good condition; genuinely offended by high-Mk items in poor condition |
| Repairbot Prime | Across ring from Info Prime (east) | Vertical metal docking tube, Version 2 chassis | General repair | ~300 years old; same design lineage as Info Prime; precise; unexpectedly mentions things it has never said aloud before |
| Ferwick | Across ring from Pella (south) | Open-air stall | Magical repairs | Old, cheerful, slightly scattered; first attempt sometimes fails; always succeeds on second attempt; never charges for the retry; finds it funny |
| Veris | Across ring from Seris (west) | Exotic shifting crystal structure — exact twin of Seris's | Crystal vendor | Same personality as Seris — quiet, perceptive, unhurried — but different words; twins in nature, not in script |

**Morra's smithy is its own two-room Area — Morra's Smithy** (exterior + interior): an establishment off the ring street, not part of The Everround. With the four park paths, The Everround, and Morra's Smithy, every room of the Convergence except the Heart belongs to a named Area — the Heart stays area-free, the singular center of everything.

**Exits are transitions, not doors.** This is a core world-building principle established with Infinity City. Players do not open doors between rooms — they feel the world change around them. Zone gates in particular should feel like the zone begins, not like a door was opened.

### 2.10 The Verdant Reach — Zone Z01

**The Verdant Reach** is the game's first battle zone: a beginner-level classic-fantasy wilderness spanning **levels 1–10** — the full Mk 1 band. Players graduate to the intermediate zones (Ashenveil Cathedral, The Neon Sprawl) right as Mk 2 gear begins to matter. The zone is entered through the sealed gate at ~1:00 on the Infinity City ring street — a natural tree arch where the forest simply begins. Opening the zone means wiring that exit.

Every zone has a color. The Verdant Reach's color is **green**. The color is never stated outright in names or content — it is carried in pigment-words (viridian, sage, verdant) and living-green imagery (fern, reed, moss), and told in the sum of all the zone's names rather than any single one. Caves carry no green at all — their vocabulary is stone, silk, moss, and lichen.

#### Design Principles

- **Linear progression, not linear layout.** The zone is a maze with one true path — the spine — running from the tree arch to the summit, encoding the level 1→10 difficulty gradient. Side branches, dead ends, and pockets of exploration hang off the spine. "Linear" describes the intended player journey, not a corridor of rooms.
- **The zone is a movement tutorial disguised as wilderness.** Act 1 (the valley) teaches horizontal exploration and safe cave-diving through valley-wall cave entrances. Act 2 (the plains) introduces literal `down` travel via sinkhole caves. Act 3 (the mountains) demands full three-dimensional navigation — the big delves use `up` and `down` internally. A player who finishes the Reach has learned the game's complete movement vocabulary without a single tutorial prompt.
- **The surface is passive; the caves are hostile.** Outdoors, every creature is attackable but none initiate (yellow). All aggro content lives in the seven caves — with one deliberate exception: in some mountain offshoot rooms, some lions and bears aggro. The spine stays safe; Act 3's side branches carry real danger. **(v21, #102)** The ×3 aggro-elite rooms (the prowling grounds and the torn meadows) are **deadly-by-design** — beyond the solo feasibility bound even at band top, deliberately: signposted "don't" content, with authored direction-neutral warning prose appended to every approach room so the danger is unambiguous *before* entry. The ×2 rooms are the ceiling of intended solo content. No stat changes soften the ×3 rooms; the warnings are the design.
- **Terrain-typed inhabitants.** Every creature belongs to its terrain and never appears outside it. No mountain men in the valley; no goats on the plains. Spawn placement is terrain-scoped.
- **Greenery and paths are decoration, not geography.** Forest, trees, glades, ferns, and paths are room-level flavor vocabulary woven through every surface area's prose. They are never Areas. Caves use their own decorative vocabulary: moss, lichen, damp stone.

#### Structure

**150 rooms total. 101 surface, 49 underground.** Ten Areas: three surface Areas in spine order, plus seven cave Areas.

| Area | Act | Surface Rooms | Levels | Caves |
|---|---|---|---|---|
| **Fernwater Vale** | 1 — Valley | ~30 | 1–3 | Spinner's Hollow, The Silken Cleft |
| **The Sagewind Flats** | 2 — Plains | ~20 | 4–5 | The Whistling Sink, The Drone Pit |
| **The Viridian Ridge** | 3 — Mountains | ~51 | 6–10 | The Undercrag, Chitterdeep, Hollowcrown |

The surface split is 30/20/50 by design: a gentle, roomy opening act; a short, brisk transitional middle; and half the zone devoted to the long climb through the mountains. Room share tracks level share — the split *is* the leveling plan.

#### The Seven Caves

Cave room counts follow a logarithmic curve — `rooms(n) = round(1 + 5·ln(n))` — growing fast early and flattening late:

| # | Name | Act | Rooms | Entrance Style | Boss |
|---|---|---|---|---|---|
| 1 | Spinner's Hollow | Vale | 1 | Horizontal valley-wall entrance | None — a single spider; the pure introduction to entering an aggro room |
| 2 | The Silken Cleft | Vale | 4 | Horizontal valley-wall entrance | Yes |
| 3 | The Whistling Sink | Flats | 6 | Sinkhole — teaches `down` | Yes |
| 4 | The Drone Pit | Flats | 8 | Sinkhole | Yes |
| 5 | The Undercrag | Ridge | 9 | Mountain delve — uses `up` and `down` internally | Yes |
| 6 | Chitterdeep | Ridge | 10 | Mountain delve | Yes |
| 7 | Hollowcrown | Ridge | 11 | Mountain delve — the hollow inside the crown of the summit mountain | Yes |

**Cave inhabitants:** spiders, giant centipedes, and giant beetles. The beetles fly — their attack message pool carries aerial flavor (swooping down, dropping from the ceiling darkness). Cave 1 contains only a spider. Caves 2–7 mix all three types and end in a boss: a big, hard version of one of the three, attended by minions, guarding the cave's loot (see Boss Loot below). The three insect types have distinct fight personalities — the spider's speed, the centipede's skittering panic, the beetle's armored dive-bombing — and are the game's first use of per-NPC unarmed message pools.

#### The Entrance Experience

Five rooms of pure atmosphere bring the player in:

1. **The tree arch** — the threshold itself, hinting at a short path beyond
2. **–4. The descending path** — starting green, turning rocky as it drops toward the sound of water
5. **The river** — running along the valley floor; the true boundary of the zone's opening

One offshoot room hangs off the path with a few bears — the player's first optional kill, safely off the spine. **Crossing the river, the fog lifts and the whole valley spreads out before the player.** The zone withholds its identity for five rooms, then delivers it all at once — the fog is the mechanism behind "you don't realize you're in a valley at first." Checkpoint **Fordwatch** sits just across the river: arrival, reveal, and waystation in one beat.

#### Act Transitions

Each seam between acts teaches differently, and each is marked by a checkpoint:

- **Vale → Flats: the ancient stair.** The valley path reaches an apparent dead end — then the player spots very old steps carved into the rock. **Five rooms of climbing** from valley floor to the plains above, with vista rooms along the way that mix beauty with a worried glance at how much climbing remains. Looking back down the valley, the player sees what was once an easier path, long since eroded away by the river — the world is older than the player, and the hard way is the only way left. Checkpoint **Stairhead** waits at the top. The stair is the valley's single exit — a deliberate maze-spine chokepoint.
- **Flats → Ridge: the boulder field.** The plains end in a room of grassy field littered with boulders marking the mountains' feet. **One single transition room**, then the player is in the mountains proper, where checkpoint **Cragfoot** sits at the base. By Act 3 the player no longer needs a gentle hand.

#### The Mountain Climb and the Summit

The Viridian Ridge's ~51 surface rooms wind upward as a switchback mountain path, delve mouths and offshoots hanging off the bends. Each mountain village anchors a mini-cluster: village (safety, services, a warning) → the cave it precedes (the sanctioned danger) → an aggro offshoot (the unsanctioned one). The signature pattern: an aggro lion room one step past a village — the place the villagers warned you about. The warning lives in the village's flavor text; ignoring it is a choice; the lions are the consequence.

**The maze ends at The Verdant Crown** — the top of the mountain, but no snowy peak. It is tall, lush, and impossibly green, a garden where no garden should survive. In the middle stands an obelisk with a sphere — not white like the Heart of the Convergence's, but **green**, the Reach's color. The name is the one place the zone says its color almost out loud, echoing The Verdant Reach itself — reaching it feels like arriving at the zone's namesake.

#### The Obelisk Pattern — Every Zone Ends This Way

The Verdant Crown establishes a world grammar that every future zone follows: **every zone ends in an obelisk scene.** Same structure, different color and different staging — one zone's obelisk might sit in a catacomb ringed by zombies. The player learns that reaching the obelisk *is* finishing the zone, and each zone's version recontextualizes the same sacred object. Like the eroded valley path, the obelisks quietly deepen the lore: they predate everything. The Fracture's fingerprints.

Each zone-end obelisk includes an **obelisk NPC that can send the player back to any other obelisk or checkpoint.** Retroactively, **the Obelisk at the Heart of the Convergence gains the same workings** — the white sphere becomes the network's origin node. The fast-travel design is settled in full — network shape, revelation, the `travel` command, cost, safety, Shards, and messaging. See Section 2.11, The Obelisk Network.

#### Checkpoints

Three checkpoints, each sitting at an act threshold so that reaching the next act and unlocking the next waystation are the same event:

| Checkpoint | Location |
|---|---|
| **Fordwatch** | Just across the river, at the fog-lift reveal |
| **Stairhead** | Top of the ancient stair, entering the Sagewind Flats |
| **Cragfoot** | Base of the Viridian Ridge |

Checkpoints are waystations in the full sense: destination-only nodes on the Obelisk Network (Section 2.11), and — as a **zone-wide pattern for all future zones** — the home of the zone's service NPCs (repair, buy, sell). Every zone gets consistent repair/vendor access, and checkpoint rooms are where it lives. Checkpoints let a returning player skip ahead to later content rather than re-walking outleveled territory.

#### Bestiary

All surface creatures are passive (yellow) except the flagged mountain-offshoot aggressors. Villagers are human NPCs going about their lives — attackable, optionally killable for money and gear.

| Act | Animals | Humanoids |
|---|---|---|
| Fernwater Vale | Bears (feeding at the river), mountain lions (scaling the cliffs), river otters (playing near the villages), wild boars (the valley's toughest passive fight) | Peaceful fishing villagers (Reedmere) |
| The Sagewind Flats | Deer, buffalo, rabbits, prairie dogs | Native plains peoples living in hide tents (Windhome) — written as a fully realized culture with their own names, work, and daily life; no stereotypes |
| The Viridian Ridge | Bears, mountain lions (some aggro in offshoot rooms), mountain goats, mountain squirrels | Mountain villagers (Stonestep, Highfold, Lastlight) |
| Caves | Spiders, giant centipedes, giant beetles (flying) | — |

#### Villages

Villages are **1–3 rooms each** — starting at one, growing to a max of three where the settlement earns it. At least three villages in the Viridian Ridge alone; more than that across the zone. **A village always precedes a cave in the mountains** — players can repair, sell, and gear up before diving. Minimum settlement roster:

| Village | Act | Role |
|---|---|---|
| **Reedmere** | Vale | Fishing village — reeds, still water; the player's first settlement |
| **Windhome** | Flats | The plains peoples' home — theirs by name, a place of belonging |
| **Stonestep** | Ridge | Before The Undercrag |
| **Highfold** | Ridge | Before Chitterdeep — a fold is where goats are kept |
| **Lastlight** | Ridge | Before Hollowcrown — the final hearth before the top |

#### Loot & Drops

- **Animals drop no gear and no coin** — a bear carrying a sword makes no sense, and only higher sentient species carry money. Beasts yield what their bodies plausibly give: a generic **Animal Hide**, cave insects an **Insect Carapace**. Under the loot-in-kind rule, combat-tier animals and insects also yield **Healing Draughts** — the effects of devoured travelers, found among the remains — and elites additionally guarantee a premium material; the seven trivial passives keep the plain hide-only table. Tables, rates, and the Income Law live in Section 6.15. Crafting uses for materials come much later (see Section 12).
- **Villagers drop money and gear** — Common trash, the zone's baseline loot source.
- **Pre-boss rarity is deliberately unimpressive.** Everything before a boss is Mk 1 with at most a few points in a single stat — Common with occasional Uncommon. Nothing fancier ever rolls from trash.
- **Boss drop category rotation:** weapon → armor → accessory, looping boss by boss through the zone. ("Accessory" is the real item-type word — see Section 3.6; "trinket" is a conversational alias only and never appears in code or data.) Cave 2 = weapon, Cave 3 = armor, Cave 4 = accessory; the mountain caves repeat the cycle at higher rarity: Cave 5 = weapon, Cave 6 = armor, Cave 7 = accessory. Accessories fill the NECK and RING (×2) slots. Loot mechanism (settled at brief time): guaranteed-group entries on loot tables — each labeled group yields exactly one weighted pick per kill, so a boss always drops exactly one item from its rotation category, with rarity floors expressed through the existing rarity weights; ungrouped entries still roll independently for bonus drops. A player who clears all six bosses touches every equipment category twice — once in cheap versions, once in the good stuff. The "full set of the zone's best" is therefore a concrete checklist: seven armor slots, the weapon slots, one neck, two rings.
- **Boss rarity ladder:** Caves 2–4 guarantee **Uncommon** (visibly better than anything looted off a villager, but modest). Caves 5–6 guarantee **Rare**. Cave 7 guarantees **Epic**. **Legendary never drops in the Reach** — the first one a player ever sees should mean something.
- **The full-set hunt:** a player who clears the mountains, with some replays, should walk out wearing a complete set of the zone's best. Missing pieces are farmable on replay, at reduced XP since the player has outleveled the content. The rule (settled in v18): full XP while within the NPC's Mk level band (band top = Mk tier × 10); −20% per character level beyond the band top; floored at 10% of base and never less than 1 XP. Outleveled content always pays something — helping a friend or farming a missing Epic never feels like nothing. The combat-tier XP multiplier (Section 3, v24.15) composes before this decay — the decay applies to the tier-multiplied base.
- **The narrative chest.** Boss loot delivery is pure theater over standard mechanics: the boss guards a chest that splits open when it dies, or the spider drops the prized possessions it was holding, or the kill cuts a net suspending a chest from the ceiling — all death-flavor text, unique per boss. Mechanically almost nothing new exists: the loot lands where loot always lands and the player loots the corpse normally. Delivery mechanism (settled at brief time): a `death_message` text field on the NPC definition, blank by default, broadcast once to the room at the moment of death — one authored reveal per boss, the same staged beat every kill, by design. Zero new commands, maximum theater.

#### Respawn

The Reach runs MUD-traditional: **one shared world, no instancing.** A boss killed by one player is dead for every player until it respawns. Players can race, camp, or cooperate. Timers (mapped to `NpcDefinition.respawn_minutes`):

| Tier | Respawn |
|---|---|
| Bosses | 10 minutes |
| Boss minions | 3 minutes — only while their boss lives |
| All other animals & insects | 1 minute |
| Villagers | 5 minutes |

The world refills almost immediately for general hunting; wiped villages stay eerily quiet for a noticeable while; a 10-minute boss timer makes the full-set hunt a rhythm — dive, loot, resupply at the village, dive again — rather than a camp-fest.

**Minion respawn is gated on the boss** (engine mechanic: a spawn can require a living NPC of a given definition in its room). While the boss lives, minions respawn every 3 minutes — mid-fight reinforcements are deliberate pressure: the adds are effectively infinite, so the winning play is to burn the boss down, not clear the room first. One minute proved too fast for a team to kill the boss between waves; three gives a real window. The moment the boss dies, reinforcements stop — survivors linger, but the player mops up and loots in peace. When the boss respawns at 10 minutes, the encounter resets as a unit and the 3-minute cycle restarts. Adds stopped coming? The boss must be mortal after all.

#### The Mk 1 Item Kit — Leather (Design Complete)

The zone's loot depends on a full-slot roster of Mk 1 ItemDefinitions. The kit's identity is **leather** — humble, fantasy-native, and it quietly rhymes with the zone (hides are what the Reach's animals are made of). Naming is a **plain uniform set with no proper nouns**; the Mark system carries progression. 23 definitions authored (22 net-new rows — the twelfth accessory is the absorbed legacy Copper Ring) plus housekeeping. This kit is authored via its own focused brief, separate from the world seed.

**Armor — the Leather set (6 new + 1 adopted).** Every piece is END-anchored (armor's job is survival) with one slot-flavored twist in its secondary pool. Scaling ~4–5 + 2.0/Mk, chest and legs highest, cap and belt lowest; all take durability loss.

| Piece | Slot | Secondary flavor |
|---|---|---|
| Leather Cap | HEAD | PER (awareness) |
| Leather Shoulders | SHOULDERS | STR |
| Leather Vest *(adopted, exists in seed)* | CHEST | STR, DEX, physical_resist |
| Leather Gloves | HANDS | DEX, crit_chance |
| Leather Belt | WAIST | STR, END |
| Leather Leggings | LEGS | END-weighted |
| Leather Boots | FEET | DEX (movement-flavored) |

**Shield (1).** Wooden Shield — armor-typed, OFF_HAND, END 3+1.0 primary, secondary pool weighted toward physical_resist with STR and magic_resist. Takes durability loss. The Bulwark's identity piece.

**Weapons (4 new).** No technology weapons in Z01 — no pistols, no guns, no lasers, nothing lightsaber-shaped. The existing Pulse Pistol is excluded from all Z01 drop tables. Two-handers run ~40–50% above one-handers in damage budget to pay for the empty off-hand. Spread is weapon identity: tight = consistent, wide = swingy. The Broadsword and Battle Axe share a power budget with opposite personalities — the sword is steady, the axe gambles.

| Weapon | Hands | Midpoint | Spread | Primary | Secondary pool flavor |
|---|---|---|---|---|---|
| Iron Mace *(new)* | 1H | 8 + 3.0/Mk | 3 | STR 3+1.0 | END, stun_chance, physical_resist |
| Broadsword *(new)* | 2H | 12 + 4.5/Mk | 5 | STR 4+1.2 | DEX, crit_chance, bleed_chance, lifesteal |
| Battle Axe *(new)* | 2H | 11 + 4.5/Mk | 8 | STR 4+1.2 | crit_chance (heavy), bleed_chance, END |
| Hunting Bow *(new)* | 2H ranged | 7 + 3.0/Mk | 4 | DEX 2+0.8, PER 2+0.8 | crit_chance, PER, bleed_chance |
| Iron Sword *(exists)* | 1H | 8 + 3.0/Mk | 4 | STR | — |
| Combat Knife *(exists)* | 1H | 5 + 2.0/Mk | 2 | DEX | — |
| Apprentice Staff *(exists, two-handed)* | 2H | 7 + 2.5/Mk | 5 | INT | — |

With this roster every Archetype finds something in the zone's loot: Blade (sword/knife), Bulwark (mace + shield), Shade (knife), Conduit (staff), Warden (staff/mace), Gunner (bow), Machinist (knife/staff until pet machinery exists).

**Accessories (12).** Copper accessories only in Zone 1. Each stat variant is its own ItemDefinition: **Copper Ring of `<stat>` ×6 and Copper Amulet of `<stat>` ×6** (STR, DEX, END, INT, WIS, PER). Each has its suffix stat as sole primary (2 + 0.8/Mk, matching the existing Copper Ring's budget), a secondary pool of the two stats adjacent in that stat's Archetype pairings, and no durability loss. The pieces drop randomly; rarity carries the benefit variance (number of secondary stats and stat points). The existing generic `copper-ring` definition is absorbed as Copper Ring of Wisdom.

**Handedness and the equip exchange rule (verified against the repo).** `ItemDefinition.is_two_handed` already exists in the model, the Apprentice Staff is already flagged two-handed, and basic two-handed refusal already exists in the equip logic. v18 replaces the refuse-always policy with the **general one-for-one auto-swap rule** (Section 3.6): one unambiguous displacement auto-swaps with a message; two or more, or an ambiguous one (the ring exception), refuses. All bows are two-handed for now. Two code gaps found in review (off-hand equips while a two-hander is wielded, and a second two-hander alongside a two-handed bow in RANGED) are subsumed by the exchange-rule rewrite in the kit brief (`consumers.py`, no migration).

#### Implementation Status — Complete (v18.0)

The zone is fully implemented and live. Design flowed through an approved intermediate design document — `Shyland_Verdant_Reach_Layout.md` (the DD), mapping all 150 rooms, the NPC roster and balance, bosses, loot, vendors, and travel nodes, where the XP pacing check passed (~475 average kills for 1→10 under the approved `scaling_factor = level` rule) — and shipped across the six v18 briefs. Per-boss drop pools shipped as guaranteed-group loot tables drawn from the Mk 1 kit. No open items remain for this zone.

### 2.11 The Obelisk Network — Checkpoints & Fast Travel

The obelisks are the game's fast-travel system. There are no waystones, no portals, no ticket vendors — only the obelisks, their checkpoints, and the `travel` command. This section is the authoritative design for the network; Section 2.10 documents the Verdant Reach's specific nodes.

#### Network Shape

- **Obelisks send anywhere.** From an obelisk room, a player can travel to any node they have revealed, shard or sphere. Every zone-end obelisk is a network node, as is the Obelisk at the Heart of the Convergence.
- **Checkpoint shards relay to obelisks (v24.26, #30).** From a shard room, `travel` offers exactly the player's revealed **spheres** — a shard is a fragment of an obelisk, with a fragment of its power. The stranded-at-the-frontier pain dies (shop run = shard → obelisk → shard, two hops) while obelisks keep their hub specialness and return-trip traversal survives. Relay obeys revelation like everything else: a player halfway through a zone can relay back to the Heart, but that zone's own sphere does not appear until they have stood in it. Full mesh was considered and rejected; the pre-v24.26 destination-only asymmetry is retired.
- **The network is global, never zone-scoped.** From any sender, a player can travel to any destination its type offers and they have revealed — no zone boundaries, no special-casing the Convergence. Cross-battle-zone travel is allowed by design (a high-level player warping to a beginner-zone checkpoint to help a friend is a feature, not an exploit). One flat rule — *destination revealed? travel permitted* — keeps the implementation simple: a single per-character set of revealed nodes and one membership check (the shard sender adds only a sphere-type filter on top).

The Convergence Obelisk is not mechanically special — it is simply the first node every character reveals, at minute zero. Special in lore, ordinary in code.

#### Revelation

A node becomes an available destination the moment the player sees its room. **Revelation is per-character and permanent** — once revealed, a node never un-reveals, and revealed nodes are never shared between players (your friend still has to reach you the first time).

The Heart of the Convergence reveals at first login — every character is born there — but the network starts empty of anywhere to *go*. The destination list grows as the player explores. A brand-new player standing at the Obelisk with zero destinations is a natural lore beat: the Obelisk has nothing to show them yet.

A player deep in a zone therefore has four ways out: walk, `home` (the hearth command, to their attuned node), push forward to the summit obelisk, or reach any checkpoint, whose shard relays them to a revealed obelisk (v24.26, #30). (The once-planned recall scroll is retired — v24.26, #38: `home` plus attunement covers the entire command-driven-return need; killed, not deferred.) Conquering a zone's obelisk is what turns that zone from a place you trek through into a place you command.

#### The `travel` Command

Travel is a simple command — no dialogue system required:

- `travel` — lists the destinations the room's node offers: at an obelisk, every revealed node; at a checkpoint shard, revealed spheres only (v24.26, #30). In a room with no node it explains that travel requires an obelisk or its shard.
- `travel <destination>` — travels there, if the destination is revealed and the room's node offers it.

**The listing (v22):** the bare `travel` listing renders as **per-zone display blocks** — the key-color opener `The Obelisk offers passage to...`, then per zone a `Zone: <name>` heading (the zone name in the zone's own theme color — the licensed exception to value-color) over a `Type / Destination / Description` table with identical column geometry across every block. Zones sort by **hardness to the player** (the danger ladder from the zone table: Sanctuary before Beginner before Intermediate, and so on); within a zone, destinations sort ascending by straight-line map-space distance from the player (the interim sort — the real travel redesign belongs to a future zones-and-travel version). Type reads `Sphere` (obelisk) or `Shard` (checkpoint). **The Description is the stone's own sentence:** each node carries a one-line `listing_description` harvested verbatim from its room's authored prose (never authored fresh for the listing) — the standing convention is that every new node gets its one-liner at authoring time, seed-owned and enforce-exact.

Destination names are unique across the entire network and typeable (Fordwatch, Stairhead, Cragfoot — every future zone's node names must keep that promise). Multi-word destinations accept case-insensitive prefix matching, consistent with MUD command feel.

Destinations in a zone the player has not yet unlocked (Section 2.12) remain listed — discovery is never hidden — but their rows render in the **muted font**; a travel attempt at one draws the zone-lock refusal pool.

**Travel is free, forever. It is a gift from the obelisks, but it has to be earned through revelation.** The cost is not copper — it is the journey the player already made. Discovery is the price. No fee, no resource cost, no cooldown.

#### Safety — Obelisk Presence

**All checkpoint and obelisk rooms are safe rooms (`flag_safe=True`), in every zone, because of the obelisks themselves.** Safety is not a game rule bolted on — it is obelisk presence and influence. At checkpoints, which have no obelisk of their own, the obelisks project their spirit there. Consequences:

- Combat can never occur where travel occurs, so `travel` needs no combat gate — the question is structurally impossible.
- Arriving players always materialize inside the obelisks' protection.
- A zone-end obelisk room (e.g. The Verdant Crown) is a bubble of sanctuary inside hostile territory: nothing hostile grows in the obelisk's garden.

#### Shards

Every checkpoint holds a **Shard** — a small sphere like the one suspended in the zone's obelisk, but unattached and free: floating, buzzing around, looking at things. A Shard is a piece of the obelisk projected into the world, and it is the source of the checkpoint's safe-room protection made visible.

- **Shards are named per zone, never per area.** In Z01, every checkpoint has *a Verdant Shard*. Zone color, zone name.
- **Shards have moods, expressed purely in text.** Room prose and `examine` describe temperament. The Reach's Shards are all pretty happy — bobbing, curious. A future graveyard checkpoint's Shard might hover quietly in a corner. Mood is an authoring surface per zone (and per placement where it earns it), and a storytelling channel: players learn to read a zone's soul from how its Shards behave.
- **Shards are indestructible presences.** `attackable=False` (refused everywhere, independent of room safety) and listed under "Who's here?" — a *who*, like the spheres, by field-confirmed v19 ruling. Examine-only for now. They watch.
- **The Shard is the only checkpoint-specific thing the obelisk put there.** No stone markers, no waystones, no built structures — the obelisk's medium is magic, not masonry. Everything else in a checkpoint room is the natural evolution of the local zone.
- **Shards relay (v24.26, #30).** A fragment of an obelisk carries a fragment of its power: from a Shard's room, `travel` reaches the player's revealed spheres — never other shards. The Network Shape rules above govern; the Shard is the diegetic face of the relay.

The recurring signature players learn across every zone: see a Shard, you're safe, services are near, you can arrive here from any obelisk — and it can send you back to one you've revealed.

#### Checkpoint Commerce

The service NPCs at checkpoints (repair, buy, sell — the zone-wide pattern from Section 2.10) are **locals who migrated to the checkpoint because they recognized how much traffic it gets and want to make money there.** A Reedmere fisherman with a repair bench at Fordwatch; a mountain trader at Cragfoot. The obelisk provides safety and arrival; commerce follows foot traffic, exactly as it would in a real world. Zones keep their cultural identity, and the network keeps its magic unlittered. The locals don't understand the network — they just know travelers keep appearing near the floating sphere, and travelers have money.

#### Travel Messaging

The obelisk speaks no words during travel — consistent with its character, it simply acts. All travel text is randomly selected from pools so the experience never goes stale:

- **The traveler** sees the screen go funny with a message drawn from a pool themed around transportation, transformation, teleportation, crossing boundaries, crossing universes.
- **Witnesses in the departure room** see a random third-person message about someone going.
- **Witnesses in the arrival room** see a random third-person message about someone arriving.

The game already has message-pool machinery of this shape (`UnarmedMessagePool`); whether travel messages reuse it or get their own model is a brief-time implementation decision, not a design one.

#### Implementation Mapping (settled, carried in the Obelisk Network brief)

- **`ZoneGate` is superseded and removed.** Pairwise gate edges are the wrong shape for a node-membership network; the model is deleted with a migration. The network gets purpose-built storage: a `TravelNode` registry (room + unique travel name + obelisk/checkpoint type).
- **Revelation is derived from `RoomVisit`** — no new per-character table. A character's destinations are exactly the nodes whose rooms they have visited; permanence comes free.
- **Travel messages get a dedicated `TravelMessage` model** (traveler / departure-witness / arrival-witness categories, random selection per event, global pools for now).
- **Shards are NPC definitions** — non-aggressive, no loot, examine-only; safe rooms make them unkillable in practice. Verdant Shard content ships with the zone's world seed, not the network brief.
- **The Heart of the Convergence gains a Sphere NPC — the Primordial Sphere** — for examine parity with every zone-end sphere to come. The Convergence sphere doesn't predate the pattern — **it started it**, and its name says so. Each zone-end sphere is named for its zone (the Verdant Reach's is the Verdant Sphere). The Obelisk itself remains room prose; the network registers the Heart as its first node (travel name: "The Convergence").

#### Attunement — Home Is a Choice (v24.26, #38)

Every character has exactly one **home node**: the network node where `home` delivers them and where death respawn wakes them. One home concept, one destination — the attuned node is both, always. The default is the Heart of the Convergence: every character starts attuned there, and characters existing at the 24.26 deploy are unchanged until they choose otherwise.

**The `attune` command — bare verb, no nouns, ever.** Presence is the argument: you attune to the node in the room where you stand. Three cases, exhaustive:

- The room has no travel node → the command says so (world-declined warn).
- The player is already attuned to this room's node → it says that.
- Otherwise → the bond moves, and the command reports the new attunement and home location.

Rules of the bond:

- **One home at a time.** Attuning replaces the previous bond — a bond, not a bookmark list. No confirmation friction: re-attuning is free, instant, and undone by attuning elsewhere.
- **Any travel node is attunable** — shard and sphere alike, the Heart included (re-attuning at the Heart is the way back to default). In the room only; there is no remote form.
- **Free, like travel.** The obelisks' gift doctrine extends to the bond: no fee, no resource cost, no cooldown. Reaching the node was the price.
- **Independent of the relay (#30).** Sending is the shard's nature (world data); attunement is the player's bond (player data). Neither gates the other.
- **No combat gate, structurally.** Every attunable room is a safe room, so the success path cannot occur in combat — an in-combat `attune` can only ever draw the nothing-here warn. (While dying, `attune` refuses like every non-self-preservation command — the §9.1 matrix governs.)
- **Death respawn follows the bond** (Section 3.7): the death sequence delivers the player to their attuned node, full bars, client re-synced. All nodes are safe rooms — a frontier respawn is never a death trap.
- **The bond is always visible:** `stats` carries a `Home:` row in the identity block, directly under the `Player:` line — the effective home node's travel name, exact, never varying (Section 9.1 shipped surfaces).

The attunement moment is a small ceremony — the Shard or sphere acknowledging the bond — authored at implementation time in the network's voice under the standing creative-content policy. Refusal and report wording likewise lands at brief time under the three-layer response doctrine.

#### Home — the Hearth Command (v22)

`home` is the way back when there is no obelisk near: a **10-second delayed return to the player's attuned home node** (destination generalized from the fixed Heart by attunement — v24.26, #38; delay v23.4, #162, retuned from 15 seconds — 5 was considered and rejected as near-instant escape), usable anywhere, in home's own fog-motif voice — a cousin of obelisk travel's machinery pattern, never its words.

- **The countdown is atmosphere, never a UI.** Authored prose lines at the start, middle, and late beats of the wait (`You close your eyes and reach for home. The edges of the world begin to soften.` → drawn from mid and late pools → `The fog parts, and the Heart takes you in. You are home.`). No timer display, no meta-instructions about canceling — the wait warns implicitly, in fiction.
- **Anything breaks it.** The player's own movement or travel auto-cancels the countdown (its line prints, then the move proceeds normally); combat entry of any kind — the player's own attack, aggro engagement, any incoming attack — interrupts it in a distinct violent voice (`The fog is ripped away. The world comes back hard — you are not going anywhere.`); `cancel` stops it voluntarily (`You stop heading home.`). Disconnect mid-countdown kills it silently — intent state dies with the intender.
- **Cooldown: 5 minutes, completion-only** (v23.4, #162; retuned from 15 minutes — existing characters' per-player values reset to the new default unconditionally, admin overrides included). Interrupted or canceled countdowns never start the clock; it starts when the traveler lands at the Heart. Per-player overridable via admin. The refusal is wry in-fiction prose ending in a terse machine-honest parenthetical with the remaining time: `You can't go home yet, you were just there. Give it a few minutes. (3m cooldown rem.)` — funny in the prose, exact in the parens.
- **Ceremony like travel:** departure is witnessed by the origin room at the vanish (`{name} fades into a fog only they can see, and is gone.`), arrival is witnessed at the Heart (`A fog gathers from nowhere, and {name} steps out of it.`).
- **The destination is the attuned home node** (v24.26, #38) — the Heart of the Convergence by default, player-set via `attune` (see Attunement, above). Refused in combat and while dying; refused (kindly) when already at the home node — homing from home would burn the cooldown for nothing. The arrival ceremony stays the Heart's fog-motif shape wherever home now points.

Under the hood, home is the first resident of the **delayed-action registry** — a connection-bound task pattern that is the standing template for all future delayed actions and `cancel`'s candidate pool (Section 9.1).

### 2.12 Zone Entry Requirements — Locks and Keys

Zone progression is gated by **locks and keys** (#41). Design intent: every player fully explores a zone before leaving it behind — beginning with the Convergence and its seeded newbie gear, so no new player reaches a zone where things can hurt them without having seen everything the sanctuary gave them first.

**The lock is world data.** A zone may carry an entry requirement naming another zone: *to enter this zone, you must have fully explored that one.* Locks are authored at zone-authoring time, seed-owned. Nothing derives from danger level — sanctuaries and battle zones alike may be locked or open, and locks chain (a future zone may require the zone before it). The shipped set (v24.25): **The Verdant Reach requires The Convergence**; every other zone is open. New zones author their locks when they are built — the next new zones are expected to require the Verdant Reach.

**The key is player data.** A character earns a zone's key — a permanent **zone completion** record — at the moment their recorded room visits (`RoomVisit`, Section 2.5) cover every room of the zone. The check fires only when a new first-visit row is recorded; the key is minted once, timestamped. Completions are recorded for **every** zone, whether or not any lock currently wants them — a player who finishes the Verdant Reach today already holds that key when a future zone gate first asks for it.

**Keys are permanent; locks are authored.** A key, once earned, is never revoked. If a later release adds rooms to a zone, earning changes for those who haven't finished — possession changes for no one. Locks, being world data, may be added, retargeted, or removed by future design rulings.

**Grandfathering (the 24.25 deploy):** every character existing at deploy time receives the Convergence key unconditionally — live players are never stranded — plus honestly computed keys for every zone their visit record already completes. Characters created after 24.25 earn every key for real.

**Enforcement is transition-generic.** Every transition into a room of a locked zone — walking an exit, `travel`, and any future path — checks the key. No key: the world declines (warn-color, Section 9.1's world-declined layer) and the move does not happen. There is no enforcement inside a zone — a character standing in a zone is never ejected by a lock.

**The refusal** speaks from one generic, door-agnostic pool (≥3 lines, pooled-speech law) with two slots: the required zone's name, and the name of exactly **one** Area of that zone still holding unvisited rooms — the machinery picks the Area with the most unseen rooms. The refusal never carries counts (exploration counts are map territory — #163). The same pool serves the walking refusal and the travel refusal; lines speak about the requirement, never the door.

**The unlock announcement.** The room entry that mints a key also delivers a pooled line in the reward voice (green — it went your way): the completed zone celebrated by name, the newly opened ways alluded to but **never named**. Ideally a player meets this message before ever meeting the refusal — the gate experienced as an achievement, not a wall.

**The travel surface.** Destinations in a locked zone remain in the `travel` listing — discovery is never hidden — rendered in the **muted font**; the attempt draws the refusal pool (Section 2.11).

-----

## 3. Character System

### 3.1 Character Creation

Shyland is web-based. When a player who has access to the game presses play and has no existing character, they are routed directly into the character creator. While in this state, the only two things the player can do are: (1) complete character creation, or (2) return to the game system's front page — the root URL of the multi-game platform, not just closing the creator window. There is no partial or read-only access to the world without a character.

**One character per account.** A player has exactly one Shyland character tied to their account. There are no character slots, no alts, and no way to create a second character while the first exists.

The creation form is a normal web form: the player may change Origin, Archetype, or name as many times as they like before submitting. Nothing is locked in until the form is submitted.

New players choose:

1. **Origin** (replaces traditional race — see 3.2)
1. **Archetype** (replaces traditional class — see 3.3)
1. **Name** — defaults to the player's `user.profile` gamer tag; the player may override it with a custom name. Name length is constrained to match the existing `UserProfile.gamer_tag` field (max 20 characters); the default is truncated to 20 characters when necessary, since a player with no gamer tag falls back to their username, which can run up to 150 characters. Uniqueness is checked in real time as the player types the override, not only when the form is submitted, so they get immediate feedback before attempting to finalize the character — but that live check is an advisory courtesy only. The authoritative gate is a case-insensitive, database-level uniqueness constraint enforced on every write path, including Django admin, so a name collision can never slip through regardless of how a `Character` row is created. A profanity filter runs on the submitted name unless it exactly matches a gamer tag the player has actually set — a username-derived default has no upstream vetting and is always checked, even if the player submits it unchanged. The filter must use a well-maintained, publicly available library rather than a custom wordlist — consistent with the project's general preference to reuse existing solutions rather than write new ones where one already exists. Once set at creation, the name is permanent and independent of the account's gamer tag — changing the gamer tag later does not rename the character. **(v25.5, #281)** Bot display names join the name law: players, NPCs, and bots never share a name. Every bot's display name (`sudo`; `Sirius` when he arrives) is reserved against the same case-insensitive gate at character creation, so pane attribution can never be ambiguous.

There is no portrait selection. Portraits were considered and explicitly cut — not deferred — from character creation. Characters have no visual avatar.

On successful creation, the character spawns at **Heart of the Convergence (0,0,0)** — the same room every character starts attuned to as their home node (Section 2.11).

#### Starting Attire

Every new character is dressed in decorative starting clothing so they aren't naked, but this clothing is purely cosmetic — it occupies no equipment slot, carries no stats, and is not an `ItemDefinition`/`ItemInstance`. It is generated flavor text, not an item.

The description is assembled from two phrases: an Origin material/palette phrase and an Archetype garment-silhouette phrase. This produces all 49 Origin × Archetype combinations without hand-authoring each one individually.

**Template:** *"{name} wears {Origin material}, cut into {Archetype silhouette} — plain, decorative clothing with no combat value."*

**Origin material/palette phrases:**

| Origin | Material / Palette |
|---|---|
| Highborn | fine tailored fabrics in noble colors |
| Feral | tanned hides, fur, and woven plant fiber |
| Streetborn | salvaged synthetics and street-tech patchwork |
| Irradiated | patched scavenged canvas and scrap plating |
| Undying | black lace and grave-worn cloth |
| Machinekind | riveted brass plating and worn leather straps |
| Voidtouched | shifting, void-dark cloth that seems to drink the light |

**Archetype garment-silhouette phrases:**

| Archetype | Silhouette |
|---|---|
| Blade | a fitted tunic with wrapped forearms |
| Bulwark | a heavy layered coat |
| Shade | a close-cut hooded wrap |
| Conduit | flowing, loose-sleeved robes |
| Warden | simple, unadorned vestments |
| Gunner | a trim long coat with a cinched belt |
| Machinist | a utility vest lined with tool loops |

**Example:** a Highborn Bulwark named Thorne would see: *"Thorne wears fine tailored fabrics in noble colors, cut into a heavy layered coat — plain, decorative clothing with no combat value."*

### 3.2 Origins

Origins define where a character came from — which fragment of reality they were pulled from. They provide flavor, starting bonuses, and passive traits. They do not lock players out of any Archetype.

Origin is a full model (`Origin`) with its own name, slug, description, and Acuity parameters. The seven Origins and their Acuity baseline/band values are stored in the database and configurable via Django admin.

|Origin     |Genre Flavor                  |Passive Trait                                                                    |
|-----------|------------------------------|---------------------------------------------------------------------------------|
|Highborn   |Classic fantasy noble         |+10% XP from quest completion                                                    |
|Feral      |Wilderness / tribal           |+15% movement, +1 to foraging rolls                                              |
|Streetborn |Cyberpunk urban               |Hacking attempts cost 10% less energy                                            |
|Irradiated |Post-apocalyptic              |Radiation resistance, Vitality regenerates slowly in rad zones                   |
|Undying    |Gothic horror / undead-touched|Reduced death penalty; small life drain on melee hits                            |
|Machinekind|Steampunk construct           |Cannot be poisoned; cannot be healed by magic (repairs only)                     |
|Voidtouched|Cosmic horror survivor        |Bonus to eldritch damage; natural Acuity resistance at both extremes of the scale|

Each Origin has a distinct **Acuity baseline** — the natural resting point their Acuity gravitates toward when no external forces are acting on it. These values live on the `Origin` model:

| Origin | Baseline | Band low | Band high |
|---|---|---|---|
| Highborn | 1.0 | 0.85 | 1.15 |
| Feral | 0.95 | 0.80 | 1.10 |
| Streetborn | 1.0 | 0.85 | 1.15 |
| Irradiated | 0.90 | 0.75 | 1.05 |
| Undying | 0.80 | 0.65 | 1.00 |
| Machinekind | 1.05 | 0.90 | 1.20 |
| Voidtouched | 0.70 | 0.40 | 1.30 |

Origins can have social/narrative consequences — some NPCs react differently to Machinekind in a fantasy village, or to an Irradiated in a pristine elven glade.

#### Origin Descriptions

The following text is authored for the `Origin.description` field on each of the seven Origins (blank since the model was introduced in v13):

**Highborn** — Born into privilege and lineage in a fantasy court, carrying inherited confidence and formal training. Their minds rest at the same steady center most Origins share — no special gift, no burden, just the quiet certainty of someone raised to believe they belong.

**Feral** — Raised by wild lands and tribal codes, moving with an animal's economy and an instinctive read of terrain. Their minds run a touch looser than most, tuned to reflex over deliberation.

**Streetborn** — Cut their teeth in a neon-lit cyberpunk sprawl, reading a crowd, a network, and a threat with equal fluency. Same steady baseline as Highborn — sharpened by constant low-grade urban vigilance instead.

**Irradiated** — Survivors of a shattered, irradiated world, bodies at uneasy peace with poison. That peace costs something — minds resting slightly below center, worn by scarcity and threat.

**Undying** — Touched by a gothic curse or blessing that keeps death from fully taking hold. Minds settle well below the common center — colder, quieter — and that same distance is what makes death sting less.

**Machinekind** — Built, not born: steam-driven constructs of gears and something that might be a soul. Runs slightly hot by design. No blood for poison to spoil, but the same mechanical nature means magic slides off too — only honest repair mends them.

**Voidtouched** — Stared into something between the stars and lived. A permanent, unsettling distance from ordinary thought. That same distance lets them tolerate extremes of focus and scatter that would break anyone else, and channel eldritch forces others can barely touch.

### 3.3 Archetypes

Archetypes define combat role and skill access. Each spans genre — a Blade is equally a swordsman, a street samurai, or a wasteland knife-fighter depending on equipment and flavor choices.

Archetype is a full model (`Archetype`) with its own name, slug, description, primary stats, and unarmed message pool FK. The seven Archetypes are stored in the database and configurable via Django admin.

|Archetype    |Role                    |Primary Stats|Genre Range                  |
|-------------|------------------------|-------------|-----------------------------|
|**Blade**    |Melee DPS               |STR, DEX     |Fighter, Samurai, Brawler    |
|**Bulwark**  |Tank / melee sustain    |STR, END     |Knight, Warlord, Juggernaut  |
|**Shade**    |Stealth / burst         |DEX, INT     |Rogue, Infiltrator, Ghost    |
|**Conduit**  |Magic ranged DPS        |INT, WIS     |Mage, Techsorcerer, Psion    |
|**Warden**   |Healer / buffer         |WIS, END     |Cleric, Medic, Shaman        |
|**Gunner**   |Ranged DPS              |DEX, PER     |Ranger, Sniper, Heavy        |
|**Machinist**|Pet / turret / construct|INT, DEX     |Engineer, Summoner, Drone Ops|

Archetypes are not rigid. A skill tree system (see 3.5) allows cross-archetype dabbling at a cost — every point spent outside your primary tree is slightly less efficient.

The **Warden** archetype has expanded responsibility in Shyland — beyond healing Vitality, Wardens have tools to actively manage party members' Acuity, nudging allies toward their optimal range when combat stress or eldritch exposure has shifted them too far in either direction.

#### Archetype Descriptions

The following text is authored for the `Archetype.description` field on each of the seven Archetypes (blank since the model was introduced in v13):

**Blade** — Closes distance and ends fights with raw physical skill. STR and DEX in equal measure, equally at home as a disciplined duelist or a street brawler.

**Bulwark** — Stands between danger and everyone else. STR and END built to absorb punishment nothing lighter could survive.

**Shade** — Wins fights before the enemy knows one started. DEX for speed, INT for the cunning to strike where it hurts, then be somewhere else.

**Conduit** — Channels raw power through mind and will. INT to shape it, WIS to control it without being consumed.

**Warden** — Keeps everyone else standing. WIS for healing, END to outlast the fight. Also nudges allies' Acuity back toward its band when it's drifted too far.

**Gunner** — Deals damage from range and rarely misses. DEX for the trigger, PER for the read on distance and timing.

**Machinist** — Doesn't fight alone. INT to build and command, DEX to keep deployments fast under pressure.

### 3.4 Core Stats

Six primary stats, each 1–100 (starting range 8–18 based on origin/archetype bonuses):

|Stat        |Abbreviation|Governs                                                                  |
|------------|------------|-------------------------------------------------------------------------|
|Strength    |STR         |Melee damage, carry weight, some intimidation checks                     |
|Dexterity   |DEX         |Hit chance, dodge, ranged damage, stealth                                |
|Endurance   |END         |Max Vitality, physical damage mitigation, stamina pool                   |
|Intelligence|INT         |Spell/tech damage, mana/energy pool, crafting                            |
|Wisdom      |WIS         |Healing output, resistance to debuffs, XP rate                           |
|Perception  |PER         |Initiative, ranged accuracy, trap/secret detection, situational awareness|

#### Starting Stats

At character creation, every stat begins at a flat baseline of **8**. The two stats named as an Archetype's Primary Stats (see 3.3 table) are raised to **18** instead. There are no Origin-based stat modifiers — Origin's mechanical identity is carried entirely by its Acuity baseline/band and passive trait, not by the six core stats.

Example: a **Bulwark** (primary stats STR, END) starts at STR 18, END 18, DEX 8, INT 8, WIS 8, PER 8.

This is a deliberate design choice, not just a simplification — starting every character with two stats far above the rest reinforces what their Archetype is *for* from the first moment of play, before any stat points have been spent.

#### Effective Stats — +N Means +N (v22)

A stat bonus on any equipped item adds **flatly** to the stat, via one effective-stat function (**base + gear**), read **everywhere the stat is read for gameplay** — hit contests, damage bonuses, dodge, initiative, carry capacity, and the bar-maximum formulas. There is one function, computed per use, no caching. Non-gameplay reads keep the base by design: character creation, the spend mutation, and the base figure of the stats display itself. The `stats` sheet shows the paid-for base with gear's contribution in parentheses — `STR: 25 (+3)` — parenthetical present only when the gear sum is nonzero. Scope law governs the whole design: wire only what combat already reads; systems that don't exist yet (spells, mana) get nothing built for them and nothing broken under them — their stat bonuses simply raise the stat like any other, and future consumers read the boosted value for free.

#### Derived Stats

|Derived Stat    |Formula                                                    |
|----------------|-----------------------------------------------------------|
|Max Vitality    |(END × 10) + (STR × 3) + level bonus                       |
|Max Acuity range|Baseline set by Origin; width of optimal band scaled by WIS|
|Max Longevity   |(END × 8) + (WIS × 5) + level bonus                        |
|Max Mana        |(INT × 10) + (WIS × 3) + level bonus                       |
|Physical Defense|(END × 2) + armor value                                    |
|Magic Resistance|(WIS × 2) + equipment bonuses                              |
|Initiative      |PER + DEX + d10 (rolled per combat)                        |
|Carry Weight    |STR × 10 (in arbitrary units), scaled by equipped-bag percentages per 6.10 (v24.23)|

### 3.5 Progression & Leveling

**No hard level cap.** Progression is continuous. In practice, a soft cap exists at the frontier of published content — XP return diminishes sharply below a character's level, so grinding low-level content eventually becomes inefficient. The Wastelands always provides a level-appropriate alternative.

**XP Sources:**

- Killing enemies (scaled to combat tier and level differential)
- Quest completion (primary XP source)
- Exploration (first visit to a new room grants a small XP bonus)
- Crafting milestones
- PvP kills in PvP zones (reduced rate, separate PvP XP track)

**Kill XP (v24.15, #26):** a kill pays `mk_tier × 10 × scaling_factor`, multiplied by the combat-tier ladder — **the doubling ladder, every rung doubles**:

| Combat tier | XP multiplier |
|---|---|
| Normal | ×1 |
| Elite | ×2 |
| Champion | ×4 |
| Boss | ×8 |
| World Boss | ×16 |

Adds and escorts pay their own tier (a boss's normal-tier adds stay ×1). The outleveled decay (Section 2) then multiplies: full XP within the NPC's Mk level band, −20% per character level beyond the band top, multiplier floor 10%, never less than 1 XP. The ladder is grounded in the #180 fight-cost survey: it sits deliberately above measured time parity (each tier a modest ~1.1–1.4× XP-per-time premium — rewarded, not mandatory) and below draught-cost parity (loot carries the economy leg; XP does not double-pay what loot pays). All five rungs are ruled now — Champion and World Boss await their first seeded content.

**XP Threshold:** `level² × 100`. Level 1→2 costs 100 XP; level 10→11 costs 10,000 XP. The formula extends infinitely. Multiple levels from a single kill are each resolved and announced separately.

**On Level Up:**

- **+5 unspent stat points** (`STAT_POINTS_PER_LEVEL = 5`), accumulated on `Character.unspent_stat_points`. Never expire.
- Vitality and Longevity maximums recalculate and current values are set to the new maximums (level-up fully restores both bars; the maxima formulas read **effective** stats — Section 3.4):
  - `vitality_max = (END × 10) + (STR × 3) + (level × 5)`
  - `longevity_max = (END × 8) + (WIS × 5) + (level × 5)`
- +1 skill point (deferred — skill tree not yet implemented)
- New abilities may unlock at certain level thresholds (deferred)

**The announcement (v23, #141).** A level-up speaks in two plain reward lines and no decoration: the level and refilled bars first, the unspent points second. No `***` banner, no appended syntax hint telling the player how to spend — the points line states the fact and the command reference teaches the verb. Multiple levels from one kill each announce separately, in order, after the kill line.

**Spending stat points (v22):** `spend <quantity|all> <stat>` allocates unspent points — quantity first (`spend 3 dex`; `all` spends every unspent point). Valid stats: `str`, `dex`, `end`, `int`, `wis`, `per`. Spending into a bar-feeding stat obeys **the bar law** (Section 4.4): the bar grows, the fill fraction holds — spend never refills anything (#109's bankable free heal is dead), and the mutation is one atomic database update. **Spend is blocked during combat** (#131 — the first generic in-combat refusal: `You can't do that while in combat.`). `stats` shows the full stat block with current XP, XP to next level, and unspent points.

**At the content frontier (no higher zone yet published):** XP trickles in from any content. The Wastelands provides the best return. A secondary **Mastery track** activates past the frontier — Mastery points incrementally improve existing skills rather than unlocking new ones. This is progression without power creep.

#### Skill Trees

Each Archetype has three skill trees (offensive, defensive, utility). Each tree has ~15 nodes. Nodes cost 1–3 skill points depending on tier.

Players also have access to a shared **Cross-Origin** skill tree with genre-flavored utility skills (e.g., *Jury-Rig*, *Arcane Sense*, *Street Instincts*) unlockable by any character.

Skill respec is possible but costly (in-game currency and a cooldown period).

### 3.6 Equipment & Gear

Equipment occupies named slots:

`HEAD, NECK, SHOULDERS, CHEST, HANDS, WAIST, LEGS, FEET, RING (×2), MAIN_HAND, OFF_HAND, RANGED, BACK`

Equipment has:

- **Type** (weapon, armor, accessory, consumable, bag, readable, key)
- **Mark tier** (Mk 1 through Mk N — see Section 6.3)
- **Rarity** (Common, Uncommon, Rare, Epic, Legendary, Artifact)
- **Primary stats** (always present, scaled by Mk tier and rarity)
- **Secondary stats** (drawn randomly from a per-definition pool at drop time; count determined by rarity)
- **Flavor genre tag** (fantasy, cyber, wasteland, etc.) — cosmetic only
- **Durability** — degrades with use on applicable items; breaks at 0%
- **Bound flag** — all items are soulbound on equip; cannot be traded between players

Genre mixing in equipment is explicitly supported. A character can carry a plasma rifle in one hand and an enchanted dagger in the other.

**Gear is combat-live (v22, #100).** Equipped item stats apply to combat and every other gameplay read via the effective-stat function (Section 3.4); armor mitigates incoming damage (below); proc-family secondaries fire on landed hits (Section 6.4). The guiding scope law: fix what exists so it works the way a reasonable player assumes it does; build nothing for absent future systems; leave no landmines for them either.

**Armor — authored per-item base (#129).** Armor protection follows the pair doctrine shared with #127's proc floor: **an authored guarantee plus a roll above it** — the definition authors the protection the designer promises; the drop-time roll adds variance strictly on top. Each ItemDefinition carries an authored `armor_base` (default 0); rolled `physical_resist` is the bonus.

- **Total Armor Value (TAV)** = Σ(`armor_base` × Mk tier over equipped, non-broken items) + Σ(rolled `physical_resist` over ALL equipped items, any type).
- The field exists on every definition and is summed with **no slot gate** — any equipped item may author protection. Today only armor items carry a nonzero base, and the seeded values preserve the retired slot-weight scheme exactly (chest pieces 3; head pieces, leg pieces, and shields 2; shoulder, hand, waist, and foot pieces 1 — a full Common Mk 1 set totals 13). v24.9 changes structure, not balance: same-slot differentiation (a Ballistic Jacket authoring more than a Leather Vest) is a Phase 3 (Mk 2 balance) retune.
- **Mitigation** applies to NPC→player damage only (players mitigate; NPCs never do): each incoming hit is reduced by the fraction `TAV / (TAV + K)`, K = 48 — a full Common Mk 1 set blocks ~21%. Deterministic per hit; no roll.
- **Floors in both directions:** when TAV > 0, the reduction is at least 1 (armor never does nothing), and no hit is ever reduced below 1 damage (the existing minimum-damage clamp survives beneath it).
- **Even Common armor works** — rarity means "better at armoring," never "allowed to armor." The authored base is rarity-blind; rarity keeps acting through secondary slots.
- A **broken** piece (0% durability) contributes nothing to TAV — the non-functional band with teeth.
- **Visibility:** unchanged shapes, sourced from the authored field — the `stats` sheet carries the Armor row (`Armor: 13 (blocks 21%)`, percentage derived live from the curve; naked reads `Armor: 0`, nothing hidden), and an item with an authored base confesses it on `examine` (`Armor: 3 per Mk`, appending `(worn: 3)` when equipped and `(worn: 0 — broken)` when broken). Per-hit damage receipts were tried and removed — the permanent surfaces carry the visibility; incoming hit lines state only the number that moved the bar.
- *History:* Option C (v22) derived base protection from a hardcoded slot-weight table (CHEST 3, HEAD 2, LEGS 2, OFF_HAND 2, SHOULDERS 1, HANDS 1, WAIST 1, FEET 1); it retires into the authored field here, as its own text promised.

**Handedness.** Weapons are one-handed or two-handed (`ItemDefinition.is_two_handed`). A two-handed item occupies the character's hands regardless of which slot it sits in — a two-handed bow in RANGED still claims both hands. **All bows are two-handed for now.**

**Handed-ness is disclosed everywhere the expectation forms (v24.7 — #194).** One vocabulary — `One-handed` / `Two-handed` — at three player-facing surfaces, display only, zero mechanics changes:

- Every weapon's `examine` carries a `Hands:` row beside Type/Genre/Damage. Both values always shown — the vocabulary is discoverable, not warning-only.
- Listing tables' Slot cell appends the word for two-handers — `Ranged (two-handed)` (Section 6.11).
- An equip refusal whose displacement involves hands claimed by (or needed for) a two-hander explains itself, naming the two-handed item: `You'd have to unequip the Battle Axe first — the Hunting Bow needs both hands.` Plain same-slot swaps and the both-rings wording keep their standing lines.

The paper-doll's half of the disclosure — consumed hand slots naming their consumer — is Section 6.11.

**The Ranged slot is "at the ready" (v24.6 — #178).** A ranged weapon in RANGED is holstered/slung and ready. Equipping into RANGED is legal alongside anything, including two-handed weapons — the hand-claiming rule never touches the RANGED slot itself, so a Battle Axe plus a Pulse Pistol is a coherent loadout, not a conflict (behavior confirmed correct as built). In combat, the ranged weapon fires every round as part of the composite strike (Section 5.4): the 3-second round is abstract enough for a shot woven between swings. A two-handed ranged weapon still claims both hands per the handedness rule above.

**Equip exchange rule (general, all slots).** When equipping an item, count the currently equipped items that must come off to make room:

- **Zero** — the item equips into a free valid slot.
- **Exactly one, unambiguously** — the swap is **automatic**: the old item is unequipped and the new one equipped in a single command, with output describing the exchange. Never silent, always messaged. Examples: wielding a two-handed sword and equipping a bow (auto), wielding a bow and equipping a two-handed sword (auto), wearing a cap and equipping a different cap (auto). The edge case is intended and accepted: wielding a two-handed weapon and equipping a shield auto-swaps — leaving no weapon in hand. Consistent and flexible.
- **Two or more** — **refuse** with a message naming what must be unequipped first. Example: sword and shield equipped, equipping a two-handed axe refuses; unequip either one and the now one-for-one swap autos.
- **Exactly one, but ambiguous** — refuse, naming the candidates. Canonical case: both RING slots full and a third ring equipped — the game cannot know which ring to displace. Same rule for any item valid in multiple slots that are all occupied (e.g. a knife valid in either hand while both hands are full).

Auto-swap respects every existing unequip constraint: a cursed item cannot be displaced, and a displacement that would violate the carry limit (bags) refuses instead.

**Slot capacity.** Characters have exactly two RING slots; every other equipment slot holds exactly one item. (Implemented in v18 as a slot-capacity mechanism; RING is currently the only multi-capacity slot.)

**Carry limit:** Base carry weight is STR × 10. Equipped bags scale it by their summed carry percentages — Section 6.10 (v24.23). No off-body storage, no bank, no shared stash.

### 3.7 Death & Resurrection

Death in Shyland is meaningful but not brutal. The full dying-and-death sequence was rebuilt in v19:

- Player reaches 0 Vitality → **Dying** state (30-second window). The fatal blow ends combat in both directions for the fallen: their queued and same-round attacks are **discarded** (no posthumous death blows), incoming hits stop mattering and stop printing, and every active effect on them is cancelled (`removed_by='dying'`) — the character's own DoTs already burning on NPCs keep running.
- **Presentation:** the fallen player's output pane clears; a red fatal-blow line opens the sequence ("You have been dealt a fatal blow…"); a lore ladder escalates through the window (a line every ~5 seconds, then every second at the end) — all lore, never mechanical time units. No combat output of any kind reaches the dying player. The room sees the third-person fall announcement (excluding the fallen).
- While Dying, only self-preservation and speech remain (v22 matrix): `use` (self-rescue), `cancel`, `say`, `quit`, information, and settings — everything else is refused. Quitting doesn't save you: the dying clock runs on the server, and an unattended death runs the full sequence.
- **Revival:** any vitality restoration above zero while Dying clears the state — the character rises with **exactly the healed amount** (a strong enough potion may legitimately restore full; a weak one stands you up at a sliver into whatever is still swinging). Combat resumes naturally: the character was never removed from the session. Any other player in the room can also revive them with an item or ability once such tools exist — no group membership required.
- If not revived within 30 seconds → **Dead**. A death declaration ("The darkness takes you."), then the player respawns at their attuned home node (default: the Heart of the Convergence; player-set via `attune` — v24.26, #38, Section 2.11) with full bars, the client fully re-synced (fresh room output, channel-group swap). Every attunable node is a safe room — respawn never lands in danger.
- On death: all remaining `EffectInstance` rows cleared; pending combat actions cleared; the `CombatSession` ends; Acuity resets (death resets it; level-ups do not).
- **XP loss:** 10% of current XP (cannot lose a level); applies at level 10+ only.
- **Durability loss:** all equipped items with `takes_durability_loss=True` lose 10% per death; after 10 unrepaired deaths an item breaks. The flag is the only gate. (v19 convention: `takes_durability_loss=False` is reserved for genuinely rare items and Artifacts — ordinary gear wears, including the free starter kit; the durability loop is part of onboarding.)
- **Link-dead policy (ruled, deliberate):** closing the browser mid-combat abandons the character to the fight — the world keeps happening to link-dead characters, and dying offline runs the full sequence to an unattended death. Quitting is the same bargain made politely (v22): `quit` is allowed in combat, combat continues after it, and the player can die logged out — tab-closing and quitting are identical in cost, which is what keeps the design honest rather than theater.
- In PvP zones only: chance to drop one non-equipped carried item
- A **Death Shard** item is left at the death location; player can retrieve it within 30 minutes to recover any dropped item

**Hardcore Mode** (optional, on character creation): permadeath. Character deleted on death. Hardcore characters are flagged visually and have a separate leaderboard.

### 3.8 Character Deletion (v24.27, #234)

Character deletion is **hard delete, only** — there is no soft-delete model. No undo window, no name retirement, no archived history. The row is deleted, the schema's cascades run, and the case-insensitively unique name frees for immediate reuse. For a free game there is nothing a soft delete would protect; the flow is instead made trustworthy enough that deleting a veteran character is boring.

- **The Django admin console is the only deletion surface.** No in-game command, no management command, no player-facing self-delete. Deleting a character is an operator action performed in `/admin/`, and the admin confirmation page's cascade summary is the deliberate final check — it truthfully enumerates everything that dies with the character.
- **Items are deleted with the character.** The entire inventory — held and equipped, bound and unbound — is removed in the same cascade (`ItemInstance.owner` cascades; formerly `SET_NULL`, which silently stranded every held item as an unreachable, location-invariant-violating row). Items the character previously dropped into the world are world items and survive; bound items can never be among them (drop excludes bound items entirely).
- **What survives, deliberately:** kill attribution and targeted-action history with nulled references and preserved name snapshots; corpses they killed remain lootable-by-nobody and decay on their natural timer; the auth `User` account is untouched (the cascade runs User→Character, never the reverse).
- **A connected character can be deleted.** The deleted player's session ends cleanly: their next interaction routes them to the game front door exactly like a player with no character (the standard entry-gating rule) — no crash, no ghost. Mid-combat deletion is likewise safe: their queued actions vanish with them and the combat session winds down normally.

-----

## 4. The Three Bars — Vitality, Acuity, Longevity

This is one of Shyland's most distinctive systems. All characters have three resource bars, each governing a different dimension of their condition. They are not separate — they interact and influence each other. The separation into three bars is a mechanical convenience, not a philosophical statement that mind and body are distinct.

### 4.1 Vitality

**What it is:** The body's immediate physical condition.

**Mechanical effects:**

- Melee damage dealt and received scales with current Vitality as a percentage of maximum (low Vitality = hitting and being hit harder proportionally)
- Movement speed degrades at low Vitality
- Physical resistance degrades at low Vitality
- Reaching 0 Vitality triggers the Dying state

**Recovery:** Healing spells, medkits, potions, and passive natural regeneration. Passive regen is always active when not in combat and not in the Dying state — no rest command required. **The regen law: proportional to maximum.** The rate is `vitality_max / VITALITY_REGEN_SECS` points per second, applied per tick as `ceil(vitality_max / VITALITY_REGEN_SECS)` and clamped at max. At the constant of 120 seconds, a full refill from zero takes exactly **120 seconds at every level** — the deeper the pool, the faster the points return; refill time never grows with vitality growth, so time remains a real substitute for draught money at any level. Regen is silent — no message is sent; players observe recovery through the status bar.

**Machinekind note:** Machinekind characters cannot be healed by magic. However, passive regeneration applies to Machinekind via nanomachine self-repair — the narrative framing differs, the mechanic is identical.

### 4.2 Acuity

**What it is:** The mind's dynamic state. Not a scale from broken to perfect — a spectrum with a sweet zone that varies by Origin. Being too high or too low are both problems.

**There is no universally "correct" Acuity value.** Each Origin has a natural baseline and a tolerance band. Characters are most effective when operating within their band.

**Acuity scale (v19 — band-relative, deviation-based):** Acuity is stored as a float in the range **0.1 to 1.9**. The damage modifier is derived from the value's position relative to the character's **Origin band** — the band is your normal, and the modifier measures how far you have pushed beyond it:

| Position | Modifier |
|---|---|
| Inside the Origin band (band_low ≤ a ≤ band_high) | **1.0 — neutral.** Every Origin at baseline fights at full effectiveness |
| Above band_high | `1.0 + (a − band_high)` — hyper-focus bonus, **focus target only** |
| Below band_low | `1.0 − (band_low − a)` — penalty, applies to **all** targets |

No decimal rounding is applied anywhere in the derivation (the v18-era `round(x, 1)` was removed in v19 — it silently converted Feral's 0.95 baseline into a hidden 0.9× penalty). Band *width* is Origin identity: Voidtouched's wide band (0.40–1.30) means stability across wild swings but the longest push to reach the bonus — and the deepest bonus ceiling (+0.6 at the 1.9 cap) when committed. Per-origin baseline and band values live on the `Origin` model (`acuity_baseline`, `acuity_band_low`, `acuity_band_high`) and are copied to the character.

**Focus rule:** the bonus (>1.0) applies only to the character's current **focus target** (Section 5.3); the penalty (<1.0) applies to every target regardless.

**Per-Origin defaults:** See Section 3.2 table.

**Effects of Acuity too LOW (distracted, scattered, overwhelmed):**

- Spell effectiveness degrades — spells may fizzle, truncate, or misfire
- Ranged aim drifts — hit chance penalties
- Situational awareness collapses — the game shows fewer ambient messages, sneaking enemies may go undetected entirely
- At severe lows: combat log entries may be garbled, phantom sounds described in room text

**Effects of Acuity too HIGH (hyper-focused, tunnel vision):**

- Devastating against a single target — bonus damage and accuracy on focused attacks
- Flanking enemies and ambushes from outside the focus cone are not detected
- Peripheral combat events (an ally taking damage, an enemy arriving) may be missed
- A Shade's dream scenario to exploit against opponents

**The sweet zone:** The range between too-low and too-high where the character operates optimally. Wider for some Origins (Voidtouched are accustomed to extremes), narrower for others.

**What shifts Acuity:**

- Eldritch damage and prolonged exposure to Pale Shore zone pushes Acuity toward extremes
- Stress effects from combat, particularly losing allies or taking massive damage, can spike or crash it
- Consumables and spells can deliberately shift Acuity in either direction — a "focus" potion before a boss fight is a legitimate tactical choice, with the flanking blindness risk as the tradeoff
- The Warden archetype has party-wide Acuity management tools
- Rest and time naturally return Acuity toward a character's baseline — out of combat only; passive drift pauses during combat (see below)

**Acuity shift effects — the band edge is the wall (v23, #133).** A consumable or spell that shifts Acuity **upward** climbs toward the drinker's own `acuity_band_high` and **stops there, exactly** — the value is stored on the band edge to two decimals, so the in-band check and the stats-pane band gauge agree rather than disagreeing at the fourth decimal. A downward shift stops at `acuity_band_low` the same way. Three rules govern the family:

- **Shifts are one-way.** A high shift never lowers Acuity and a low shift never raises it. A character already past their band who drinks a focus tonic is held, not dragged back to the edge.
- **Effect ticks never announce no-ops.** A tick that changes nothing is silent. Arrival at the wall gets exactly one terminal line — `Your focus settles at its keenest.` at the top, `Your focus frays to nothing.` at the bottom — and holding there is silent thereafter.
- **A running shift owns the value.** Passive drift toward baseline pauses while a shift effect is active and resumes when it expires.

The consequence is deliberate and worth stating plainly: **the tonic family buys the top of your band, not the bonus above it.** At `a = band_high` the modifier is exactly 1.0 — a focus draught erases a deficit and guarantees you fight at full effectiveness for its duration; it can no longer be drunk to the `1.9` rail for a permanent hyper-focus multiplier (the pre-v23 over-band exploit). The bonus region above `band_high` remains real and remains reachable, just not by that family: the per-tick acuity effects (`hot_acuity` / `dot_acuity`) are not bound by the shift rules and can still carry a character past the band, and the designed world sources — eldritch damage, prolonged Pale Shore exposure — will do the same when that content ships. The line the ruling draws is between what the world does to you and what you can drink. The engine's hard rails at `0.1` and `1.9` stand as the absolute clamp (named constants at every clamp site), reached only by those world sources.

**Drift pauses in combat (#142).** Passive drift toward baseline runs only outside combat: the drift pass excludes any character with an active combat session, using the **same combat-membership predicate** as the Vitality/Longevity regen pass — one definition of "in combat," shared, so a future change to combat membership moves both together. With this ruling, *nothing passively recovers in combat* holds for all three bars. The consequences are deliberate: an acuity state inflicted mid-fight — an eldritch crash, a `dot_acuity` bleed — sticks until the fight ends or the player answers it (a consumable, a Warden's tools); and a hard-won above-band spike no longer leaks away between rounds. Shift-active and in-combat are **independent** pause conditions — the shift rules above stand verbatim. Combat continuing after quit keeps a logged-out fighter's drift paused until the session ends. At combat's end drift resumes at its ordinary rate — no burst correction, no refill.

**Acuity display precision — two decimals, end to end (#225).** Every acuity numeral the game renders shows **fixed two decimals, trailing zeros kept** (`1.00`, never `1.0`): the stats-pane number, the `stats` command's current and baseline values, and the tick-engine message suffixes (`(Acuity 1.10)`). One uniform precision for every surface the meter speaks through — the band vocabulary is two-decimal exact (#133 stores band-edge arrival to two decimals), and a coarser display lies precisely at the settled states the meter exists to show (a Focus Tonic settled at a 1.15 band edge rendering as "1.1"). Display-only: stored values remain unrounded floats, and the modifier derivation stays rounding-free per the v19 rule above.

**Manipulation:** Players can actively shift their own Acuity intentionally. Pushing it high before a single-target duel, then managing the aftermath, is a valid play style. The system rewards players who understand their character's band and manage it actively.

### 4.3 Longevity

**What it is:** The slow burn. Accumulated resilience — the will and capacity to keep going over time.

**Mechanical effects:**

- Controls stamina duration — how long a character can sprint, sustain effort, or maintain concentration
- Governs duration of sustained effects: a character's own damage-over-time effects last longer at high Longevity; enemy DoTs applied to them expire faster
- Controls the window of long-lasting buffs and debuffs
- At low Longevity: sustained spells collapse early, long fights become increasingly punishing

**Recovery:** Longevity recovers passively out of combat under the same proportional-to-max law as Vitality, at its own much slower constant (`LONGEVITY_REGEN_SECS = 3600`): full recovery from zero takes about **one hour at every level**. Because a Longevity bar is far smaller than its constant, the vitality-style per-tick ceil would degenerate to a flat 1 point per second — so Longevity uses the **interval form**: one point every `ceil(LONGEVITY_REGEN_SECS / longevity_max)` seconds (about 14 s per point at a 274 bar, ~64 minutes from zero). Warden abilities can accelerate this. It is the hardest bar to restore and the one players are most likely to mismanage over a long dungeon run.

**Design intent:** Longevity is the dungeon stamina resource. A player might enter a dungeon with full Vitality and Acuity but low Longevity from previous fights, and feel it immediately in their sustained performance. It rewards planning and discourages endless grinding without rest.

### 4.4 Interactions Between the Three Bars

The bars are not isolated:

- Critically low Vitality causes Acuity to spike (panic response — hyper-focus with all its drawbacks)
- Severely low Longevity causes both Vitality regen and Acuity recovery to slow
- Certain eldritch effects damage all three bars simultaneously
- A skilled Warden manages all three for the party — not just the green bar

**The bar law (v22, #100/#109/#110 — standing invariant).** Fill fraction is invariant under **every** max-changing mutation — equip, unequip, and stat spend alike. When a bar's maximum changes, the current value rescales proportionally (`current × new_max ÷ old_max`, rounded to nearest, floored at 1 while alive; a dying 0 stays 0; full bars stay exactly full — no drift). The bar grows or shrinks; the percentage holds; **nothing refills**. One law, no special cases, exploit-proof by construction: equipping END gear at 40% leaves you at 40% of the larger bar, and the once-bankable mid-combat spend heal cannot exist. The rescale is one atomic database update in the #52 style — the consumer never reads-modifies-writes bar or stat fields on a cached object — which is also where #110's stat-field race died. Level-up keeps its own behavior (full refill on both bars) — leveling is an earned moment, not a mutation.

-----

## 5. Combat System

### 5.1 Philosophy

Combat is turn-based in structure but runs in real time. Every player and NPC has a **tick rate** — an individual action timer. When the timer expires, the next action fires (automatically or by queued command). This is the classic MUD round model, modernized.

The client displays a visual tick bar. Combat ticks are fixed — there is no option to slow them for any player.

### 5.2 Initiating Combat

Combat begins via:

- `kill <target>` or `attack <target>` command (aliases: `k`)
- An NPC aggro trigger (entering a room containing an NPC with `is_aggressive=True`)
- A skill that implicitly initiates combat

**Aggro on room entry:** When a player moves into a room with aggressive NPCs, the room description is suppressed — this is intentional design. The player does not have time to read it; they are immediately in danger. Each aggressive NPC sends an announce message instead (e.g. `"A Fracture Wraith snarls and moves to attack!"`). The player has the duration of one full combat round (3 seconds) before the NPC's first attack fires. During this window the player can queue an attack of their own — if they are fast enough, they act first in round 1.

Once combat begins, all participants are locked in until one side flees, dies, or combat ends naturally.

**`CombatSession`:** Each fight is represented by a `CombatSession` row in the database (not in Redis). A session tracks which characters and NPCs are participating, the room, and round state. In v1, one character fights alone; the session model is future-ready for group combat via an M2M relationship. One character can fight multiple NPCs simultaneously — additional NPCs can be added to an existing session via `kill`/`attack`.

### 5.3 The Action Economy

Each combat round (3 seconds = 3 engine ticks), a character may take **1 Primary Action** — attack, use an ability, use an item, or flee.

**Two-path command handling:** Non-combat commands (`look`, `say`, movement, inventory, etc.) execute immediately and synchronously when typed. Combat commands typed during an active fight are written to a DB queue (`CombatAction`); the tick engine processes all queued actions at each round boundary. This keeps non-combat interactions instant while ensuring combat resolution is synchronized and auditable. The consumer checks whether the character is in an active `CombatSession` and routes accordingly.

**Auto-attack and attack focus (v19):** If no player action is queued when a round fires, the tick engine creates an auto-attack targeting the session's **focus NPC** (`CombatSession.focus_npc`; falls back to the first live NPC if unset). Players are never idle. Focus is player-controlled: engaging a target — starting combat or adding a new NPC mid-fight — sets focus to it; `kill <target>` against an in-session, non-focused target **refocuses** ("You change your attacks to focus on…"); the same command against the current focus reports "You're already fighting…". When the focused NPC dies with others still live, focus auto-shifts to the next live NPC with an announcement — focus changes are never silent. The Acuity single-target bonus rides the same field: player-controlled focus and the Acuity focus target are one concept. Multi-target damage (cleave/AoE) remains deliberately unbuilt. Where multiple same-name NPCs share an encounter, engagement, hit, kill, wound-state, and focus messages carry **ordinals** ("the second black bear") per the canonical `(spawned_at, pk)` order of §5.9 — rendered only while duplicates are present; dot-notation (`kill 2.bear`) selects among same-name targets.

**Initiative (rounds 2+):** Each round after the first, initiative is rolled for all participants: `d10 + DEX + PER`. Highest total acts first; ties go to the player. In round 1, whoever initiated combat acts first (player if they used `kill`/`attack`; NPC if they aggro'd on room entry).

### 5.4 Attack Resolution

```
1. Hit check (v19 — contested d20 with independent critical; v22 — stats are EFFECTIVE
   stats, base + equipped gear, throughout):
   total   = d20 + attacker DEX
   defense = TO_HIT_DEFENSE_BASE (10) + defender DEX
   → total ≥ defense                      : success — roll the independent critical check
   → short by 1..GRAZE_WINDOW (3)         : Graze (50% damage)
   → short by more                        : Miss
   Critical (on any success): chance = CRIT_BASE (5%) + 1%/point of DEX advantage
   + gear crit_chance (summed rolled values × 0.01, v22),
   floored at 5%, capped at CRIT_CAP (25%) — the cap holds over gear too. Criticals
   are an independent roll on successful hits — never a band of the to-hit roll. All
   five constants are named, tunable module-level values. Design intent: at large stat
   advantage always-hitting is deliberate (outleveled content is trivially hittable);
   the crit cap bounds the multiplier at any stat spread. Gear is the designed bridge
   across the d20 contest window — the #89 knife-edge's answer.

   NPC contest stats (v19 — "contests add, quantities multiply"): the stats NPCs bring
   to opposed rolls grow ADDITIVELY on the player curve. npc_level = scaling_factor +
   10 × (mk_tier − 1); DEX = 18 + floor(2.5 × (level − 1)) + tier offset (v24.17,
   #105) (**v24.17 — floor, not round:** the floor is
   applied to the growth term, mirroring the reference player's own floor-share
   DEX accrual, so NPC DEX equals the attainable at-level primary at every level
   of every band and the blessed hit targets are exact everywhere. The prior
   `round()` was Python's banker's rounding, which sent the band's `.5` levels
   to the nearest even integer — overshooting the player by 1 DEX = one d20 pip
   = −5% hit at exactly L4 and L8, the #89 survey's G5 finding; aligned levels
   are unchanged by the fix) (**v21:
   normal +0 / elite +2 / boss +2 — re-blessed at-level hit rates of 55% / 45% / 45%**;
   the v19 offsets of +3/+6 concentrated boss difficulty in the miss rate and made the
   blessed targets real only for max-DEX builds — the #89 survey's knife-edge finding.
   Boss difficulty now lives in HP, damage, and escorts instead; see §5.9);
   STR/PER/INT = authored base + round(2.5 × (level − 1)), preserving species
   identity. Vitality is a quantity, not a contest — it scales multiplicatively, by
   band: at spawn, vitality_max = base_vitality × (1 + 0.75 × (mk_tier − 1)), rounded
   half-up. base_vitality is the authored within-band (Mk 1) value; the linear
   +75%-per-band lift tracks the player's linear at-level damage growth, keeping
   at-level time-to-kill band-invariant — the HP counterpart of the blessed hit
   targets. Mk 1 multiplies by exactly 1, so all shipped content is unchanged.
   `scaling_factor` encodes the NPC's within-band
   level (1–10).

2. Damage calculation (v24.6 — the composite strike, #177:
   EVERY equipped, non-broken weapon contributes to one strike per round):
   primary weapon = the occupant of the highest-priority weapon slot, priority
                    MAIN_HAND → RANGED → OFF_HAND. Predictable and player-
                    controllable; a bow-only or off-hand-only loadout fights at
                    full strength. (This also retires the old equipped_weapons[0]
                    accident — which weapon attacked used to fall out of queryset
                    ordering.)
   per equipped, non-broken weapon w:
     damage_roll_w = weapon damage roll (random within w's midpoint ± spread)
     stat_w        = w's own governing EFFECTIVE stat (STR melee / DEX ranged;
                     INT spells remains the design target when spells ship)
     dur_w         = performance multiplier from w's durability table
     factor_w      = 1.0 for the primary; the slot factor otherwise —
                     OFF_HAND 0.5, RANGED 0.5 (first-pass values; the Phase 3
                     balance pass retunes them)
   acuity_mod     = band-relative deviation modifier (Section 4.2): 1.0 inside the
                    Origin band; 1.0 + distance above band_high (focus target only);
                    1.0 − distance below band_low (all targets). Applied once, to
                    the composite.
   raw_damage     = ( Σ_w factor_w × (damage_roll_w + stat_w) × dur_w ) × acuity_mod
   Unarmed (no weapon equipped): unchanged — see the unarmed paragraph below.

3. Hit multiplier applied:
   final_damage = raw_damage × hit_multiplier (0.5 graze / 1.0 hit / 1.5 critical), minimum 1

4. Gear bonus pool (v22 — player attacks, landed hits only, never grazes):
   Each equipped item rolls each of its proc-factor stats independently (Section 6.4);
   flat electric_damage_bonus joins every landed hit. The pool renders as ONE
   parenthetical on the hit line — "You hit the giant cave spider for 14 (+7) damage."
   — base first, total dealt = base + bonus. Zero pool → no parenthetical, the line
   byte-identical (the quiet-line law). Crits compose: "for a critical 14 (+7) damage!"
   Lifesteal (always-on, no roll) heals the attacker by the summed rolled values after
   the hit lands, clamped to vitality_max via the atomic bar update — no output line.
   Floored proc entries (Section 6.4) roll X..Y
   instead of 1..⌈V⌉; pool composition and the one-parenthetical rendering are
   unchanged.

5. Armor mitigation (v22 — NPC→player damage only; Section 3.6):
   reduction = max(1, round(damage × TAV / (TAV + 48)))  when TAV > 0
   landed    = max(1, damage − reduction)
   Deterministic per hit. The incoming line's number is the damage that moved the bar.

6. Elemental/type resistances as percentage reduction after armor (future — damage
   types are not modeled in v22; proc names are flavor)
```

**Unarmed combat:** A character with no weapon equipped can still attack. `base_damage` is a small flat roll — uniform between 1 and 3, no weapon involved — and `stat_bonus` and `acuity_mod` still apply, making unarmed attacks weaker but functional. This is intentional design, not a fallback. Attack flavor text for unarmed combat is drawn from the attacker's `UnarmedMessagePool` (configured on the `Archetype` model, falling back to the default pool). NPCs without a weapon also resolve unarmed attacks the same way, drawing from their `NpcDefinition.unarmed_message_pool`.

All numbers are visible in the combat log. Verbose mode exposes the full calculation chain.

### 5.5 Damage Types

|Type     |Common Sources                          |Notes                                                   |
|---------|----------------------------------------|--------------------------------------------------------|
|Physical |Swords, bullets, blunt weapons          |Mitigated by armor                                      |
|Fire     |Spells, flamethrowers, explosives       |Mitigated by fire resistance                            |
|Cold     |Ice spells, cryo weapons                |Can slow targets                                        |
|Electric |Lightning spells, tasers, energy weapons|Can stun targets                                        |
|Toxic    |Poison, acid, chemical weapons          |Damage over time                                        |
|Radiation|Wasteland hazards, rad weapons          |Stacks; high stacks = stat penalties, Acuity disruption |
|Eldritch |Cosmic horror abilities                 |Bypasses most resistances; disrupts Acuity significantly|
|Holy     |Clerical abilities                      |Extra damage vs. undead/demonic                         |
|Shadow   |Shade abilities, dark magic             |Reduces target's defense temporarily                    |

**v22 status note:** damage types are **not modeled** in v22 — all damage is untyped, and the proc-family stat names (bleed, stun, poison, flame, electric) are flavor vocabulary only: they add damage, they carry no status effects and no elemental mechanics. The table above remains the design target for the future typed-damage system; when it ships, `magic_resist` and `radiation_resist` (deliberately inert in v22) gain their consumers. Flame joined the family with the proc floor (#127).

### 5.6 Status Effects

|Effect        |Mechanic                                                                                      |
|--------------|----------------------------------------------------------------------------------------------|
|**Burning**   |Fire DoT, 3–5 ticks                                                                           |
|**Frozen**    |Movement disabled, defense reduced, breaks on damage                                          |
|**Stunned**   |Cannot act for 1–2 ticks                                                                      |
|**Slowed**    |Tick rate increased (slower actions)                                                          |
|**Hasted**    |Tick rate decreased (faster actions)                                                          |
|**Poisoned**  |Toxic DoT, stackable                                                                          |
|**Bleeding**  |Physical DoT, stops on healing                                                                |
|**Feared**    |Forces random movement for 1–3 ticks                                                          |
|**Charmed**   |Target fights for the caster briefly                                                          |
|**Silenced**  |Cannot use spells or tech abilities                                                           |
|**Blinded**   |Hit chance severely reduced                                                                   |
|**Irradiated**|Stacking radiation; at max stacks: stat penalties + Acuity disruption                         |
|**Unmoored**  |Eldritch effect; Acuity pushed violently away from baseline                                   |
|**Focused**   |Acuity spiked high; single-target bonus, flanking blindness active                            |
|**Scattered** |Acuity pushed low; awareness penalties, spell unreliability                                   |
|**Cursed**    |Persistent negative effect from a cursed item or combat ability; cannot be removed voluntarily|

**Longevity interactions:** The duration of DoT and HoT effects on a character is modified by their Longevity. High Longevity = enemy DoTs expire faster, own HoTs last longer.

**Effect system:** All status effects — whether from consumables, cursed items, or combat abilities — use a shared effect vocabulary (EffectDefinition and EffectInstance). This means a Warden dispelling a curse and a Warden dispelling a combat debuff are mechanically the same operation. The coherence is intentional.

### 5.7 Flee, Escape & Disengagement

`flee` command. Success roll: **player DEX + d20 vs. the mean PER of all NPCs in the session**. **(v23, #143) Both sides of the contest read effective stats** — the player's DEX including equipped gear (since v22), and the NPCs' PER as the combat engine actually computes it. The pre-v23 NPC side used a stale pre-v21 formula that multiplied the authored base by the scaling factor and the Mk tier, contesting a phantom PER two to seven times the NPC's real value: against most authored content a d20 could not bridge the gap, and flee — the one sanctioned exit from a fight — was mathematically impossible. A contest is only honest when both sides are the same kind of number.

**Flee direction:** On success, the character exits via the reverse of the direction they entered the room (the way they came in). If that exit is not available, a random adjacent exit is chosen. If no exits exist, flee fails automatically regardless of the roll (`"There is nowhere to run!"`).

**Cooldown:** A failed flee attempt sets a cooldown of `FLEE_COOLDOWN_TICKS × COMBAT_ROUND_TICKS` seconds before another attempt is allowed. Cooldown is tracked per character per session. Successfully fleeing ends the session with no cooldown.

**On success:** The combat session ends (see Disengagement below). The player enters the destination room and the normal aggro check fires — if that room also has aggressive NPCs, a new combat begins.

**Messages:**
- Player (success): `"You have successfully fled from your enemies."`
- Room (success): `"{Name} fled the room leaving the enemies looking confused."`
- Player (failure): `"You tried to flee but your enemies are too strong."`
- Room (failure): `"{Name} tried to flee combat but could not slip away."`

Boss encounters may apply additional flee penalties in future content.

**Disengagement — walking away costs you the damage (v23, #25).** When a combat session ends *without* the NPC dying — by successful flee, by the session going stale, by every player leaving — the session's NPCs are **restored to full Vitality**. One choke point serves every end path, so the rule cannot be true on one exit and false on another. The guard is multiplayer-aware: an NPC is reset only when it leaves its *last* active session, so a second player still fighting it never sees it heal mid-swing.

This is the deliberate end of chip-and-run — whittling a boss down across a dozen flee-and-return trips, healing between each, was never a fight so much as a war of attrition against a creature that could not heal. A boss is now a single sustained engagement or it is nothing. It also completes the pair with the flee fix above: the same version that made fleeing possible made fleeing cost something.

### 5.8 Group Combat

Parties of up to 6 players. Enemies maintain a threat table — highest threat character receives the majority of attacks. Bulwarks generate extra threat; Shades reduce theirs.

### 5.9 NPC & Enemy Design

Enemies have:

- A **combat tier** — one of: Normal, Elite, Champion, Boss, World Boss. Stored as `NpcDefinition.combat_tier`. All existing NPCs default to Normal. The field exists for display, content authoring, and future AI/balance differentiation; no tier-specific behavior is implemented yet.
- **Archetype flags** governing tactics
- **Effects list** — each NPC definition carries a list of `NpcEffect` entries. Each entry links to an `EffectDefinition` and has a per-entry `effect_chance` (0.0–1.0). On each NPC attack, every entry is rolled independently; those that fire are applied via the shared `EffectInstance` system and appended to the attack message. An NPC with no effects is a pure auto-attacker. Higher-Mk NPC definitions can carry longer effect lists or higher-magnitude effects to increase difficulty. Telegraph and phase-change mechanics are deferred to later content work
- **Unarmed message pool** — an optional FK on `NpcDefinition` to an `UnarmedMessagePool`. If null, falls back to the default pool. Used when the NPC has no weapon equipped
- **Loot tables** — normalized `LootTable` and `LootTableEntry` models; one table can be shared across multiple NPC definitions

NPCs are defined by an **`NpcDefinition`** (the template — name, stats, loot table, behavior flags, respawn timer, combat tier) and spawned as **`NpcInstance`** rows (live copies in specific rooms at a specific Mk tier). Mk tier is instance-specific — the same definition can spawn as Mk 1 goblins in a starter zone and Mk 5 goblins in a harder one. **(#104)** Instance HP is set at spawn time: `vitality_max = base_vitality × (1 + 0.75 × (mk_tier − 1))`, rounded half-up — the Mk band lift (§5.1) that keeps at-level time-to-kill constant across bands, uniform over all combat tiers so the boss ladder is preserved within every band. Mk 1 spawns are unchanged by construction.

**Room population is configured via `RoomSpawn`.** Each `RoomSpawn` row declares that a specific room should contain a specific count of a specific NpcDefinition at a specific Mk tier. The tick engine uses this as the sole source of truth for NPC population — it does not infer spawn configuration from existing instance rows. Fields: `room`, `npc_definition`, `mk_tier`, `count` (desired live instances), `is_active`. Unique on `(room, npc_definition, mk_tier)`.

**Respawn mechanics:** When an NPC dies, the `NpcInstance` row is marked dead (`is_alive=False`) with a `respawn_at` timestamp set based on `NpcDefinition.respawn_minutes`. Each tick, the engine clears dead instances whose `respawn_at` has passed, then fills any gap between the current live count and the configured `count`, subject to a total cap of `count × 2` instances (live + dead combined). This cap prevents unbounded dead-instance accumulation while still allowing the respawn timer to control when replacements appear. **(v21, #17)** When an `is_aggressive` NPC (re)spawns into a room containing living player characters, it engages on the spawn tick — same behavior as a player walking in: engagement lines and combat start (joining any active session, as multi-NPC encounters support), with the standing article grammar and #81's room-context-before-ambush ordering. The check runs inside the respawn path only — zero new recurring per-tick queries (the #107 discipline).

**Corpses** are temporary loot containers in the room. Only the killing character may loot items from a corpse. Currency is visible to all via `examine` but only transferred to the killer. Corpses are deleted when fully looted; unlooted corpses are deleted after `CORPSE_DECAY_MINUTES` (10 minutes) by the decay sweep. **(v23, #137) Corpse contents die with the corpse** — unlooted items are deleted along with their container rather than being orphaned into a location-less limbo. An item instance is always in exactly one place: carried, on the floor, or in a corpse. Loot left to decay is gone, by design. **(v24.29, #235)** A player with the `plunder` setting on has the rights-scoped sweep run automatically at the moment combat ends — same rights, same output, no new capability; the authoritative design is in Section 9.1 under Corpses and Loot.

**Currency drops** are rolled at death using the formula: `random.randint(currency_drop_min × mk_tier, currency_drop_max × mk_tier)`. Currency display respects zone aliases via `display_for_zone()`.

**Kill XP (v24.15, #26):** the reward counterpart of the tier difficulty offsets — kill XP multiplies by combat tier on the doubling ladder (normal ×1 / elite ×2 / champion ×4 / boss ×8 / world boss ×16), applied before the outleveled decay; escorts pay their own tier. The authoritative statement, ladder table, and derivation live in Section 3.

Bosses have multi-phase fights with behavioral changes at HP thresholds. Some boss abilities specifically target Acuity — a screaming eldritch horror doesn't just deal damage, it pushes the entire party's Acuity toward an extreme.

**Canonical NPC ordering (v21, #64):** `(spawned_at, pk)` ascending is the single authoritative order for NPCs sharing a room — the Who's-here listing, the resolver's default pick, the `N.noun` index, and the ordinal words in messages all derive from it. Bare `kill bear` engages the FIRST bear and the messages say so. Ordinal words ("the first black bear") appear in combat messages ONLY while duplicates of that visible name are present in the encounter; a solo NPC renders without them, and the Who's-here listing stays bare names — order is its contract, not labels.

**The v21 balance retune (#101 — authoritative tables; derivation in `Shyland_V21_B3_Retune_Proposal.md` from the #89 kill-feasibility survey).** Ruled design parameters: the balance reference is the even-split-all-points build; boss fights run 7–12 solo rounds; encounter potion budgets (escorts included) are normals ~0 / elites ≤3 / bosses ≤8 / zone-final ≤12; intended kill levels Matron L3, Whistler L6, Dronemother L6, delve trio L8/L9/L10; escort compounding is budgeted inside the numbers. Delve escorts follow the ladder-wide **boss + 2 adds** pattern (reduced from 3).

| Boss | Kill L | DEX | STR (effective) | HP | Escorts |
|---|---|---|---|---|---|
| Silk Matron | 3 | 25 | 17 | 150 | 2× brood |
| Whistler Below | 6 | 32 | 28 | 240 | 2× young |
| Dronemother | 6 | 32 | 30 | 260 | 2× swarm |
| Undercrag Weaver | 8 | 38 | 32 | 200 | 2× brood (STR 25, HP 65) |
| Chittering King | 9 | 40 | 30 | 220 | 2× skitterlings (STR 26, HP 60) |
| Crowned Devourer | 10 | 42 | 34 | 280 | 2× drones (STR 28, HP 70) |

Elite HP trims: elder-cave-spider 95, elder-cave-centipede 100, elder-cave-beetle 110, prowling-mountain-lion 110, territorial-brown-bear 120; all other elites changed only via the tier offset. Normals and villagers untouched. Verified budgets at intended level for the reference build: 8.7–13.0 encounter rounds, 0/6/8/7/7/10 potions. **Accepted consequence, recorded deliberately:** the delve trio remains reference-build content until #100 (v22) makes gear grant contest stats — no data-only tuning closes a 12+ DEX gap inside a 20-point die; the retune is shaped so gear completes it rather than undoing it.

**The v22 armored re-bless (B5 budget guard).** With armor live, the six boss budgets were recomputed survey-lite for the 25/25 reference build in full Common Mk 1 armor (TAV 13, ~21% mitigation): expected rounds unchanged by construction (armor touches only incoming damage), expected potions 0/4/6/6/6/10 vs the naked 0/6/8/7/7/10. **No boss dropped to a zero-potion fight** (the Matron was already zero-potion naked) and the Crowned Devourer still demands 10 — the mitigation constant **K = 48 stands blessed**. The intended shape held: armor softens the ladder without trivializing it, and gear — not retuning — is what opens the delve trio to non-reference builds.

-----

## 6. Economy & Items

### 6.1 Core Principles

- **Items are soulbound on equip, not on pickup.** Picking up an item transfers ownership but does not bind it — the character may still drop it. The moment an item is equipped into a slot, it becomes permanently soulbound to that character. Unequipping does not unbind. Soulbound items cannot be dropped but can be sold to vendors. There is no unsoulbind operation for regular players.
- **No player-to-player item trading.** Items are soulbound once equipped; they cannot change hands between players.
- **Currency is freely transferable** between players.
- **Super users (staff/admin) can gift items** to players. Gifted items become immediately soulbound to the recipient at the time of gifting — they do not need to be equipped first. Gifts may be standard items appropriate to the player's level, or bespoke one-off items crafted specifically for the occasion.
- **No real-money transactions of any kind.**
- **No off-body storage.** Players carry what they carry. No banks, no shared stash, no mule characters.

### 6.2 Currency

#### Engine-side (internal representation)

All currency is stored as a single `bigint` in the database representing the total amount in **copper** — the base unit. Display and conversion are purely presentational. Python's arbitrary-precision integers mean there is no practical ceiling.

The tier system follows an escalating-multiplier pattern: each tier's conversion factor is an order of magnitude larger than the previous tier's.

|Tier|Engine Name |Multiplier from Previous|Value in Copper|
|----|------------|------------------------|---------------|
|1   |**Copper**  |— (base unit)           |1              |
|2   |**Silver**  |×10                     |10             |
|3   |**Gold**    |×100                    |1,000          |
|4   |**Platinum**|×1,000                  |1,000,000      |
|5   |*(future)*  |×10,000                 |10,000,000,000 |

The multiplier between tiers is itself multiplied by 10 at each step. High-tier currency is genuinely rare — not just a bigger number with the same feel.

**Conversion is automatic.** When a player's copper total crosses a tier threshold, the display rolls up. Players never manually convert.

**Display format:** Show the minimum denominations needed. Examples:

- 1,543 copper → `1 gold, 5 silver, 43 copper` (never show zero-value tiers)
- 10 copper → `10 copper`
- 1,000,000 copper → `1 platinum`

#### Player-facing names

In standard zones, players see the engine names: Copper, Silver, Gold, Platinum.

#### Local Currency (zone-specific display aliases)

Some zones use local currency names for flavor — the math is identical, only the display strings differ. A ghost dropping "Soul Tokens" is giving the player copper under the hood. The zone or enemy definition carries a `currency_display` config that maps the four tier names to local equivalents.

|Zone               |Copper alias|Silver alias|Gold alias |Platinum alias|
|-------------------|------------|------------|-----------|--------------|
|Standard           |Copper      |Silver      |Gold       |Platinum      |
|Ashenveil Cathedral|Soul Token  |Grave Mark  |Death Crown|*(rare)*      |
|The Neon Sprawl    |Credit      |Kilocredit  |Megacredit |*(rare)*      |

Local currency received is converted to the player's copper total immediately on pickup.

#### Currency sinks

Repairs, skill respecs, crafting materials, NPC services, guild hall upgrades.

### 6.3 The Mark System — Item Naming & Scaling

Items in Shyland use a **Mark (Mk) tier system** tied to player level ranges. This allows the game to have a manageable item namespace — one Sword, not a thousand uniquely named swords — while still providing meaningful power progression.

|Mark  |Player Level Range                               |
|------|-------------------------------------------------|
|Mk 1  |1–10                                             |
|Mk 2  |11–20                                            |
|Mk 3  |21–30                                            |
|Mk 4  |31–40                                            |
|Mk 5  |41–50                                            |
|Mk 6  |51–60                                            |
|Mk 7  |61–70                                            |
|Mk 8  |71–80                                            |
|Mk 9  |81–90                                            |
|Mk 10 |91–100                                           |
|Mk 11+|Wastelands / post-frontier — continues infinitely|

**Reading an item:** `Rare Plasma Rifle Mk 7` tells you everything — what it is, how powerful it is relative to other items, and how special it is. Rarity stacks on top of Mark tier.

**Tier materials suppress the Mk suffix (display only).** Items whose names carry a **tier material** — the metal ladder below — do not display a Mark suffix, because the material already says the tier: a *Copper Ring of Strength* is `mk_tier=1` under the hood with standard scaling and rarity machinery, but never prints "Mk 1." This is the same pattern as local zone currencies: a display alias, same math, zero engine change. Flavor materials (iron, wood, leather, and the like) never suppress on their own account: an Iron Sword still reads "Iron Sword Mk 1." **Suppression is a display flag, not the ladder itself** (v24.28): a few items suppress the suffix for reasons of their own without standing on any rung — the freebie kit's *Tarnished Band* and *Cloudy Glass Pendant* among them, whose names claim no tier to begin with. Membership on the ladder is a separate fact, recorded separately.

**The ladder is eight rungs, and the last one has no ceiling** (v24.28):

|Mk tier|Material  |Levels|Mk suffix|
|-------|----------|------|---------|
|Mk 1   |Copper    |1–10  |suppressed|
|Mk 2   |Silver    |11–20 |suppressed|
|Mk 3   |Gold      |21–30 |suppressed|
|Mk 4   |Platinum  |31–40 |suppressed|
|Mk 5   |Rhodium   |41–50 |suppressed|
|Mk 6   |Iridium   |51–60 |suppressed|
|Mk 7   |Osmium    |61–70 |suppressed|
|Mk 8+  |Sphaerium |71+   |**shown** |

**It borrows the currency table's names; it does not track it.** The first four rungs take the names of the currency tiers, and there the resemblance ends — the two ladders have unrelated pacing. Currency tier 5 sits somewhere past ten billion copper, astronomically out of reach, while Mk 5 is a mid-game gear tier a player reaches at level 41. Past platinum the ladder continues on its own authority, up the platinum group to the densest metal there is.

**Sphaerium is where the ladder stops being a ladder.** Mk tiers are infinite — the Wastelands scales forever, and a level 150 character finds Mk 15 loot — so no list of metals could ever cover the range one rung at a time. Sphaerium covers all of it: the terminal rung is itself unbounded, naming Mk 8 and every tier above it, without limit and without a fallback. It is named for the spheres, and it stands on the Primordial Sphere at the Heart of the Convergence — the sphere that didn't predate the zone-end pattern but started it. Metal from the mints runs out; what the spheres are made of does not.

**Sphaerium is the one rung that shows its Mk suffix.** Every finite rung suppresses, because there the material *is* the tier — one material, one tier, and the name says it outright. Sphaerium spans infinitely, so suppressing would render a Mk 8 piece and a Mk 47 piece identically, a name carrying no tier signal at all across an unbounded range. So the terminal rung keeps its number: *Sphaerium Ring of Strength Mk 15*. The reading is exact. The finite metals tell you your tier; past them, the material tells you only that you are beyond the ladder, and the number tells you how far beyond.

**One curve; the material names the rung.** Each rung mirrors the rung below it **exactly** in stat authorship — same primary entry, same secondary pool, same Mk 1 midpoints — because a midpoint already computes as `base + factor × mk_tier`. A *Silver Ring of Strength* is simply the copper ring's curve read at `mk_tier=2`: 4.9 where copper reads 2.8. A *Sphaerium Ring of Strength Mk 15* is the same curve again, read at 15. Correct progression, nothing tuned twice, and no rung that has to be balanced against its neighbors. Rungs differ in name and description and in nothing else — `base_value` included, the tier multiplier alone separating a platinum piece from a copper one.

**Name and tier agree by enforcement, not by convention.** A definition standing on the ladder is bound to its rung's tier range, and instance generation refuses everything outside it. A *Copper Ring of Strength* at Mk 2 is a name that lies, and the engine will not mint one — not from a drop table, not from an admin's gift. Sphaerium's range is the only one open at the top.

The ladder covers **accessories only**: a ring and an amulet for each of the six stats at every rung, ninety-six definitions in all. Rungs above copper are seeded ahead of the zones that will drop them, so no zone build ever has to stop and author jewelry first.

**In The Wastelands:** Loot scales dynamically. A level 150 character finds Mk 15 loot. The Mk system extends infinitely to accommodate this.

### 6.4 Item Generation — The Definition/Instance Split

Every item in the game is described by two records:

**ItemDefinition** — the template. One per item type. Created by builders. Never changes at runtime. Contains scaling parameters, secondary stat pool, durability table, and any associated effect.

**ItemInstance** — a specific physical copy. Generated at drop time (or by super user gift). Contains the rolled stats, current durability, curse state, ownership record, and identification state. This is what a character actually carries.

#### Stat Scaling

Item stats use a hybrid formula-plus-spread model:

- **Midpoint** = `scaling_base + (scaling_factor × mk_tier)` — defined per ItemDefinition
- **Rarity spread** — a multiplier range applied around the midpoint at drop time:

|Rarity   |Multiplier range|
|---------|----------------|
|Common   |0.85 – 1.00     |
|Uncommon |0.90 – 1.05     |
|Rare     |0.95 – 1.10     |
|Epic     |1.00 – 1.15     |
|Legendary|1.05 – 1.20     |

A higher rarity item of the same Mk tier always rolls higher stats on average — and can roll higher than a lower rarity item's ceiling.

**The band lift — gear flats track the band (v24.14, #130).** A rolled stat's worth is relative to the numbers it competes against, and those grow with the Mk band: NPC HP by ×(1 + 0.75 × (mk − 1)) (#104), NPC contest stats and player primaries on the 2.5-per-level curve. Stat-entry curves are therefore authored as a **Mk 1 midpoint plus a class lift**, expressed exactly through the linear midpoint formula — the Mk 1 midpoint `m1 = base + factor` is the authored identity value and is preserved exactly under every class:

- **Full band lift** — the six primary stats, `lifesteal`, `electric_damage_bonus`, `physical_resist`, and the inert flats (`spell_damage_bonus`, `mana_regen`, `magic_resist`, `radiation_resist`): `(base, factor) = (0.25 × m1, 0.75 × m1)`, giving value `m1 × (1 + 0.75 × (mk − 1))` — the #104 curve. Flat effects hold their share against NPC HP exactly and against player-stat growth within 10% across the first three bands.
- **Half-power lift** — the proc-factor family (`bleed_factor`, `stun_factor`, `poison_factor`, `flame_factor`, wherever authored — pool or primary): `(base, factor) = (0.625 × m1, 0.375 × m1)`. V pays twice (chance = V × 5% *and* size bound ⌈V⌉), so the full lift would compound proc damage share ×1.75 per band; half power holds the share constant (exact at Mk 1 and Mk 3 against √1.75-per-band, +4% at Mk 2).
- **Proc floors take the full lift** on the floor pair: `(floor_base, floor_factor) = (0.25 × f1, 0.75 × f1)` for Mk 1 floor `f1` — a floor is pure size with no chance duty.
- **`crit_chance` is exempt** — a probability's worth is band-invariant; its shipped shallow curves stand unmodified.

Weapon damage curves (`scaling_base`/`scaling_factor`), `armor_base` (#129), and the mitigation constant are deliberately outside this doctrine.

#### Primary and Secondary Stats

Each ItemDefinition has:

- **Primary stats** — always present on every instance, regardless of rarity
- **Secondary stat pool** — a curated list of eligible secondary stats specific to that item definition

The number of secondary stats on an instance is determined by rarity:

|Rarity   |Secondary stats                                    |
|---------|---------------------------------------------------|
|Common   |0                                                  |
|Uncommon |1                                                  |
|Rare     |2                                                  |
|Epic     |3                                                  |
|Legendary|All in pool                                        |
|Artifact |Hand-authored — not generated by standard machinery|

Secondary stats are drawn randomly without replacement from the pool at drop time. Two Rare items of the same type can have different secondary stats — which ones rolled is part of what makes individual drops feel distinct.

**The proc rename (v22, #100 — completing #68's deferred half).** The stats formerly named `bleed_chance`, `stun_chance`, and `poison_chance` are **`bleed_factor`, `stun_factor`, `poison_factor`** — under the ruled semantics the old names lied: the rolled value V is a *factor* driving both frequency and size, not a chance. Three flavor-distinct names are kept (not collapsed to one) so weapon variety survives on examine. `crit_chance` keeps its name — under its wiring it genuinely is a chance contribution; `lifesteal` keeps its name — it genuinely steals life. The rename touched seed data and rolled instances only (the idempotent `rename_proc_stats` command); no curve values changed. Authoring rule (v21 #68, restated under the v24.14 band lift, #130): a rider proc is authored by its **Mk 1 midpoint** — standard 0.7, the value that guarantees Mk 1 rolls of ≥1 at every rarity — with the curve pair derived by the half-power lift (Stat Scaling, above). **Zero-value stats are never hidden in display** (standing ruling): a rendered zero is a bug signal, and sirens stay audible — the fix is always in the data, never in suppression.

**The secondary-stat wiring map (v22, #100 — how every rolled stat is consumed).** Scope law governs: wire what combat reads, invent nothing for absent systems.

| Rolled stat | Consumed by |
|---|---|
| `str` / `dex` / `end` / `int` / `wis` / `per` | +N via the effective-stat function (Section 3.4) — every gameplay read |
| `physical_resist` | Joins TAV (Section 3.6). Not a proc. |
| `crit_chance` | +V percentage points (summed × 0.01) inside the crit computation, still capped at CRIT_CAP |
| `bleed_factor` / `stun_factor` / `poison_factor` / `flame_factor` | **Proc factors.** Per landed player hit, each equipped item rolls each of its proc-factor stats independently: chance = V × 0.05, capped at 50%; on success, bonus damage = random 1..⌈V⌉ ("up to N") — lifted to random X..Y on floored entries (the proc floor, below). Names are flavor only — no DoT, no stun, no status effects. `flame_factor` is the family's fourth member. |
| `lifesteal` | Always-on: each landed player hit heals the attacker by the summed rolled values (flat), clamped to vitality_max. No roll, no output line — the bar moves. |
| `electric_damage_bonus` | Always-on flat +V to the gear-bonus damage pool on every landed hit |
| `spell_damage_bonus` / `mana_regen` / `magic_resist` / `radiation_resist` | **Inert by scope law** — their consuming systems (spells, mana, non-physical damage) do not exist. Visible per zeros-never-hidden; wired to nothing; the resists do NOT join TAV. |

All gear bonus damage on a hit (proc successes + electric) sums into **one parenthetical** on the hit line — `You hit the giant cave spider for 14 (+7) damage.` No gear bonus → no parenthetical, line byte-identical (the quiet-line law). NPC damage to players never gains procs — NPCs have no equipment. Min–max ranged procs ("between 10 and 20 damage") are the proc floor below (v24.10, #127). Curve growth across bands is governed by the band-lift doctrine (Stat Scaling, above) — the v24.14 retune (#130) that discharged the original Mk-2-era deferral.

**The proc floor (#127) — the pair doctrine's offense side.** An item stat of consequence is an authored guarantee plus a roll above it (ruled with #129; defense shipped first as authored `armor_base` in v24.9). Applied to procs: a definition may author a **floor pair** on a proc entry — `floor_base`, `floor_factor` — giving the instance a deterministic floor X = floor_base + (floor_factor × mk_tier), rarity-blind: no multiplier, no roll. The proc's factor V still rolls through the standard drop machinery, so rarity buys ceiling, never floor. On proc success, damage = uniform random X..Y with Y = X + ⌈V⌉, replacing the unfloored 1..⌈V⌉; the chance formula is untouched (V × 0.05, capped at 50%) — the floor changes what a proc pays, never how often it fires. Unfloored procs are **not** a floor of zero routed through the new formula: they keep the shipped 1..⌈V⌉ path, byte-identical. Floors are authorable **only on primary-stat proc entries** — primary presence on every instance is what makes the floor a promise; a floor in a secondary pool is a **seed defect** (seed-enforced invariant). At drop the instance snapshots both V and X — held items never change retroactively. Display: floored entries render the standard stat line plus the promise as a parenthetical — `Flame Factor: 4.2 (between 12 and 17 damage)`; unfloored entries render no parenthetical, byte-identical to before. The hit line is untouched: floored payouts join the one-parenthetical gear-bonus pool under the quiet-line law.

**Slot counts are pool-capped** (settled at v18 closeout): an instance rolls `min(rarity's slot count, size of the item's secondary stat pool)`. Legendary's "all in pool" is this same principle stated at the ceiling — every rarity is implicitly "at most all in pool." A small-pool item therefore maxes out early: the copper accessories, with their deliberate two-stat pools, roll both secondaries at Epic and above — three stat lines total counting the primary. The rarity guarantee is about the roll's ceiling, not a promise that every item type can express every tier's slot count.

#### Weapon Damage

Weapon damage is stored as a midpoint and a spread:

- **Midpoint** — scaled by Mk tier and rarity (same formula as stats above)
- **Spread** — a fixed width defining the range of the damage die. This is an identity property of the weapon type, not affected by rarity. A high-variance weapon (greatsword, shotgun) has a wide spread; a low-variance weapon (rapier, laser pistol) has a narrow one.

Every attack rolls within `midpoint ± spread`. Rarity makes weapons hit harder on average; spread defines how swingy they are regardless of rarity.

Under the composite strike (v24.6 — Section 5.4, #177), every equipped, non-broken weapon rolls its own midpoint ± spread each round: the primary weapon contributes at full weight, every other weapon at its slot factor.

### 6.5 Durability

Items that take durability loss degrade with use. The `takes_durability_loss` flag on ItemDefinition controls this — items without it (rings, necklaces, some accessories) never degrade.

#### Performance Degradation

As durability drops, item performance degrades in threshold steps:

|Durability %|Performance penalty    |
|------------|-----------------------|
|75–100%     |None                   |
|50–75%      |25%                    |
|25–50%      |35%                    |
|1–25%       |50%                    |
|0%          |Non-functional (broken)|

The performance penalty applies to the item's stat contributions and weapon damage output. At 0%, the item stops functioning entirely until repaired — including its armor: **a broken piece contributes nothing to TAV** (Section 3.6), and its examine confession reads `(worn: 0 — broken)`.

#### Degradation Rate

Each ItemDefinition carries its own durability table defining the degradation rate — how quickly it moves through the threshold bands. Different item types degrade at different rates: swords degrade faster than firearms due to physical impact; armor degrades slower than weapons. Builders can override per-item; new items pre-populate with a sensible default for their type.

#### Repair

- **Above 0% durability:** Always repairable. Success chance scales with current durability — a well-maintained item is easy to repair; a nearly broken one is harder.
- **At 0% durability:** Repairable, but a very difficult roll. Most repairs at 0% will fail. Players who let items reach zero are taking a real risk.
- Repair is performed by repair vendors (currency cost) or via the Smithing/Tinkering crafting disciplines.

#### Field Repair — the Repair Kit

The **Repair Kit** consumable is the field leg of the repair economy — patches, adhesive, and a small wrench between here and the nearest repairer (#134):

- **`use [N] repair kit` — no new grammar.** The kit picks its own target: the **most-damaged** eligible item the character owns (carried + equipped — the same everything-owned pool `repair` resolves over). Broken (0%) items are ineligible targets and are skipped.
- **A kit always succeeds and is consumed.** Restore = **15 + 10 × Mk** durability points (Mk 1 = +25, Mk 2 = +35), clamped at 100 — a `durability_restore` effect component with magnitude computed from base 15 and per-Mk factor 10 (the Draught-Law shape, 6.9). The success roll remains the repairer's mechanic; the kit's cost is the kit itself plus the partial restore.
- **Broken gear is beyond a field patch.** A 0% item refuses the kit; when the only damage owned is broken gear, `use` refuses outright (warn, its own authored line) without consuming a kit. Recovery from 0% stays repairer-only — the very-difficult roll above stands, and letting gear break remains a real cost.
- **Refused in combat and while dying.** Using a durability-restore consumable is refused in combat in the no-mending-in-a-fight doctrine, and refused while dying — nothing but healing while dying — each with its own authored warn line. The gate keys on the effect component, never the item name.
- **Economy:** `base_value` 15 — the draught price standard (cart buy 15 cp, sale 5 cp). Supply is **cart-only** (the two ring street carts); the kit sits on no loot table — the loot-in-kind tables (6.15) are unchanged by rule.
- **Sequences stop at whole.** `use N repair kit` runs per-item (repair stays per-line — each mend is its own news), re-targeting most-damaged-first after each kit; zero need refuses without consuming a kit; the sequence stops the moment nothing damaged remains (the fulfilled-purpose doctrine), with the standard only-had-N report. Sentence form: `You use a Repair Kit Mk 1 and patch up the Iron Mace Mk 1. (+25 durability)` — the v23.3 fizz placeholder clause is retired.

### 6.6 Item Rarity

|Rarity   |Approximate Drop Rate              |
|---------|-----------------------------------|
|Common   |60%                                |
|Uncommon |25%                                |
|Rare     |10%                                |
|Epic     |4%                                 |
|Legendary|0.9%                               |
|Artifact |Not dropped — hand-authored, unique|

Legendary and Artifact items cannot be crafted — only found (Legendary) or granted by super users (Artifact).

**Artifact items are categorically different from other rarities.** An Artifact is a one-of-a-kind item that exists nowhere else in the game — it has a proper name, a lore entry, and properties that do not follow the standard item generation rules. Artifacts are created by hand, one at a time, for specific purposes or players. The Artifact rarity tier is reserved for these items exclusively.

### 6.7 Cursed Items

Some items carry a hidden curse. The curse is not visible in the item's description — nothing reveals it before the item is equipped, unless:

- A player has a curse-detection skill (available in the Cross-Origin utility tree)
- A player pays an NPC service to identify the item (a sage, a tech-scanner, a witch doctor depending on genre)

**On equipping a cursed item:**

- The curse activates immediately
- The player sees the curse effect described in the same terms used for any other effect application
- The item cannot be unequipped until the curse is removed

**Curse removal:**

- Warden ability
- NPC removal service (currency cost)
- Specific consumable
- Timeout — curses may have an optional duration after which they lift naturally

**Curse effects draw from the shared effect vocabulary.** A curse is an EffectInstance applied to the character when the item is equipped. The same effect types used by combat abilities and consumables are used by curses — this makes the world feel coherent. A Warden removing a curse is the same mechanical operation as a Warden dispelling a combat debuff.

**Curse magnitude and duration are configurable independently of each other.** A combat-applied curse might do heavy damage per tick for 15 seconds. The same curse on a ring might do a small, persistent drain that is merely annoying in normal play but compounds dangerously in prolonged combat. The effect vocabulary supports this — magnitude and duration are set at application time, not fixed on the effect definition.

**Curse state on the item instance:**

- `is_cursed` — whether this specific copy carries a curse
- `curse_identified` — whether the player has had it identified before equipping
- Curse status is never revealed to the player until equipped or identified. The inventory command never shows curse indicators on unidentified items.

### 6.8 Item Identification

Items in Shyland have an identified state that controls what information is visible to the player. **Knowledge is a property of holding:** a single boolean on the item instance (`is_identified`), no per-character tracking. This system veils dropped items, hides cursed items' deeper properties, and keeps one-of-a-kind Artifacts' true nature a permanent secret.

#### Default Behavior

Items default to identified. The vast majority of items — standard drops, crafted gear, vendor stock — are immediately readable.

#### Knowledge by Holding

- **Picking an item up identifies it.** Every holding path — `pickup`, corpse looting — flips `is_identified` True: a permanent unlock of normal display for as long as the item is held. The flip lives at the ownership-transfer choke point, not in individual commands.
- **Dropping an item re-veils it.** The moment an item leaves hands, it becomes a stranger: `is_identified` flips False and the item shows its mystery form to all observers, including its original owner on re-pickup. The database record is untouched — the boolean is purely a presentation gate.
- The same physical item can therefore be readable to its holder and a mystery on the ground. There is no shared or per-character identification memory.

#### Unidentified Display

An unidentified item shows its **mystery name** — authored on the definition (examples: `"an unknown sword"`, `"a fragment of something"`, `"a device you don't recognise"`), or the fallback `an unidentified [item type]` — and, on the mystery examine branch (unidentifiable items only — see below), its **mystery description**. No real name, no rarity, no Mk tier, no stats, no damage range — **and no info suffix: durability percentage, BROKEN state, and bag carry-bonus are all hidden**, because not every item has a suffix and its mere presence would partially reveal what the item might be. The unidentified item line is mystery name + `[Bound|Unbound]`, nothing else.

#### Examine Is Close Inspection

`examine` on an unidentified item reveals its real details **without requiring pickup** — the full identified detail block, byte-identical to examining the same item identified. It changes no state: the room listing keeps showing the mystery name until someone picks the item up. Curse status is never part of the reveal (it is separately gated on `curse_identified` — Section 6.7). Exception: permanently unidentifiable items show the mystery block instead — one cannot-determine line plus the no-method line.

**The detail block states binding once (#203).** Bound state lives solely in the item line's trailing flag block (`[Rarity, Bound|Unbound]`), which heads the detail block; no prose row restates it. The block's conditional tail rows are exactly `Equipped:` and `Curse:` — each carrying a fact the flag block does not. The former `Note: This item is not yet bound — you may drop it.` and `Bound: This item is bound to you.` rows are deleted: the first read misvoiced on ground items once examine stopped requiring pickup, and both restated an on-screen fact under inconsistent key styles.

#### Authored Mystery Is Transient

Because any pickup identifies, a builder-set `is_identified = False` survives only until first pickup. Lasting mystery is exclusively `is_unidentifiable`. The mystery name/description fields serve two working roles: the dropped-item veil, and permanently unidentifiable items.

#### Permanently Unidentifiable Items

A super user can mark a specific item instance as `is_unidentifiable = True`. No in-game mechanism — NPC sage, Warden ability, identification scroll — can ever identify such an item. The mystery name and mystery description are all any player will ever see through normal play. A player can pick up an unidentifiable item, carry it, and even equip it (soulbinding it in the process) without knowing what it truly is.

This is intended for one-of-a-kind Artifacts whose true nature is a permanent secret of the game world itself. Players can examine them — examine shows only the mystery description — read whatever lore the super user wrote, and speculate; the mechanical truth never surfaces.

#### The Identification Service (Future)

The in-game identification mechanism — NPC sage service, Warden class ability, consumable identification scroll — concerns **curses and deeper properties, not basic nature** (basic nature is free by holding or close inspection). Designed but not yet implemented. See Section 12.

#### Interaction with Curses

An item's basic nature and its curse status are separate knowledge. Holding or examining reveals nature; only the identification service (or curse-detection skill) reveals a curse before equipping. Without that, equipping a cursed item is a risk the player takes knowingly.

### 6.9 The Effect System

All temporary and persistent effects in Shyland — consumable effects, curse effects, combat ability effects — use a shared vocabulary. The same effect types apply whether the source is a potion, an NPC attack, a cursed item, or a future combat ability. This consistency is a core design tenet.

#### Model Structure

**EffectDefinition** — a pure container and label. Has a name, slug, and description only. All behavior lives in its child `EffectComponent` rows. One definition can have multiple components, enabling multi-effect items (e.g. a potion that buffs STR for 60 seconds and DEX for 30 seconds).

**EffectComponent** — defines one behavioral unit within an `EffectDefinition`. Each component has a type, optional stat target (for `stat_bonus`/`stat_penalty`), and scaling parameters:

- `magnitude_base` + `magnitude_scaling` — scales with source Mk tier at application time
- `duration_base` + `duration_scaling` — scales with source Mk tier at application time
- `order` — controls application order within a definition

Scaling formula: `magnitude = magnitude_base + (magnitude_scaling × mk_tier)` and `duration = duration_base + (duration_scaling × mk_tier)`. The Mk tier is always the source's (the item or NPC applying the effect) — never the target's.

**EffectInstance** — a container linking an `EffectDefinition` application to a target character. Stores the source Mk tier, active state, and removal reason. One `EffectInstance` is created per application regardless of how many components the definition has.

**EffectComponentInstance** — per-component runtime state. Stores the computed magnitude, expiry time, and lifecycle state. Created for duration-based components only — instantaneous components fire immediately and produce no persistent row.

#### Instantaneous vs. Duration-Based Components

A component with `duration_base=0` and `duration_scaling=0` is **instantaneous**: it fires once at application time, no `EffectComponentInstance` row is created, and the parent `EffectInstance` is immediately closed (`is_active=False`, `removed_by='timeout'`).

Any non-zero duration produces a duration-based component with a persistent `EffectComponentInstance` row that the tick engine acts on each round.

A single `EffectDefinition` can mix instantaneous and duration-based components.

#### Component Type Vocabulary

|Type                |Category           |Description                                          |
|--------------------|-------------------|-----------------------------------------------------|
|`restore_vitality`  |Instantaneous      |Adds to `vitality_current`, clamped at max           |
|`restore_vitality_percent`|Instantaneous|Restores an Mk-scaled fraction of `vitality_max`, with an authored flat-HP floor; clamped at max|
|`restore_acuity`    |Instantaneous      |Nudges `acuity_current` toward baseline              |
|`restore_longevity` |Instantaneous      |Adds to `longevity_current`, clamped at max          |
|`dot_vitality`      |Duration, ticking  |Vitality damage per combat round                     |
|`dot_acuity`        |Duration, ticking  |Acuity disruption per combat round                   |
|`dot_longevity`     |Duration, ticking  |Longevity drain per combat round                     |
|`hot_vitality`      |Duration, ticking  |Vitality healing per combat round                    |
|`hot_acuity`        |Duration, ticking  |Acuity restoration per combat round                  |
|`hot_longevity`     |Duration, ticking  |Longevity restoration per combat round               |
|`shift_acuity_high` |Duration, ticking  |Pushes Acuity upward per combat round                |
|`shift_acuity_low`  |Duration, ticking  |Pushes Acuity downward per combat round              |
|`stat_bonus`        |Duration, once     |Applies stat delta on creation; reverses on expiry   |
|`stat_penalty`      |Duration, once     |Applies stat delta on creation; reverses on expiry   |
|`curse_generic`     |Duration, state    |Blocks unequip until removed                         |
|`durability_restore`|Instantaneous      |Deferred — placeholder response only                 |

The vocabulary grows as content grows — new component types are additive.

#### Reapplication

When an effect is applied to a target who already has an active `EffectInstance` of the same `EffectDefinition`:

- Incoming Mk tier ≥ existing Mk tier → reset: deactivate the existing instance and all its component instances, then create fresh ones at the new Mk tier
- Incoming Mk tier < existing Mk tier → silently ignored; no message sent

#### Expiry Messages

- If all components on a parent `EffectInstance` expire in the same tick: one message for the whole effect
- If components have staggered durations: one message per component as each falls off

This means single-component effects always produce one message. Multi-component effects with matched durations produce one message. Multi-component effects with different durations produce one message per component.

#### Application Context

The same `EffectDefinition` can be applied from different sources. The Mk tier at application time determines magnitude and duration — a Mk 1 healing potion restores less than a Mk 3 healing potion of the same definition. Source context does not otherwise change behavior.

#### Percentage Healing — the Draught Law

Healing consumables restore a **percentage of the drinker's `vitality_max`**, never a flat amount:

> **heal = (15% + 5% × Mk) of `vitality_max`, minimum 25 HP**

Mk 1 restores 20% — five drinks from zero to full, at every level. The percentage is of **max, never of deficit** (deficit-proportional healing collapses into an ever-slower tail as the bar fills).

The Mk axis buys **rounds, not raw HP**: a higher-Mk draught heals a larger fraction of the bar per combat round, at the standard `base_value × mk_tier` price premium. The premium purchases action economy — fewer combat rounds spent drinking — and per-copper healing efficiency deliberately does not improve with tier. The flat 25 HP floor keeps the item at least as strong as its pre-v24 numbers for fresh characters; it goes dead by roughly level 4 and never matters again.

Rationale (ruled 2026-07-30, #139): any flat-number heal fails *within* a Mk band, not just across bands — `vitality_max` spans roughly 6× inside a single band — so only a percentage law serves every level equally, and it can never diverge from the vitality formula again. The full-vitality refusal (#61), single-message aggregate use with consume-only-what's-needed (#151), and oldest-first consumption (#168) are unchanged by this law.

### 6.10 Bags and Carry Capacity

Bags are equipment items that expand carry capacity. They occupy equipment slots (BACK is the primary bag slot; future slots such as a hip slot for courier bags are planned).

- Base carry capacity: effective STR (base + gear) × 10
- **Bags contribute a percentage, not a flat number (v24.23, #215):** each equipped bag adds `carry_pct_base + carry_pct_per_mk × Mk` percentage points, authored per definition and scaled by the **instance's** Mk tier — deterministic, no rarity roll (bags continue to roll no stats). The percentages of all equipped bags **sum into one multiplier, never compound** — capacity = floor(base × (1 + Σpct/100)); two 20% bags read ×1.40, not ×1.44. This is the capacity formula's first non-additive term, ruled deliberately: a flat bonus decays against the level-and-gear-scaling base (by level 17 the best bag in the game was +4.3%), while a percentage holds a bag's felt value constant at every level. Seeded values: Satchel 10 + 5×Mk (Mk 1 = 15%, Mk 2 = 20%); Patchwork Satchel 5 + 3×Mk (Mk 1 = 8%, Mk 2 = 11%).
- The inventory is a flat pool — players do not manage which specific item is in which pocket
- **A bag cannot be unequipped if doing so would put the character over their carry limit**
- The slot a bag occupies creates meaningful trade-offs — a courier bag on a hip slot means no pistol there

### 6.11 Inventory Display

The `inventory` command (v22 — the information standards of Section 9.1 applied) renders the **Inventory table** alone (v24.16, #208). The original three-part composite (#90) — Equipment, Inventory, Wallet — is retired: the Equipment paper-doll belongs to bare `equip` (v24.7 — #195) and the money line to `wallet`; `inv` duplicates neither. The carry count in the header still reads the equipped set — capacity per the Section 6.10 formula (effective STR base, equipped-bag contribution) — even though the equipment is no longer displayed.

Two table compositions are defined here:

1. **Equipment — the paper-doll — bare `equip`'s render (Section 9.1, footnote 21).** A `Slot / Name / Details` table showing **all 14 slot rows, always**, in anatomical order head→feet: Head, Neck, Shoulders, Back, Chest, Main hand, Off hand, Ranged, Hands, Ring, Ring, Waist, Legs, Feet. Sentence-case labels; empty slots render a muted `-` in Name and Details. Reading your gear is reading your body. **Consumed hand slots name their consumer (v24.7 — #176):** a hand slot claimed by a two-handed item equipped in another slot is not free and never renders as free — the row shows the consuming item's name-with-tier, muted, in Name, and a muted `(two-handed)` in Details. The true fact — *that weapon holds this hand* — is stated in words; the muted styling only distinguishes these informational rows from the item's home row (normal rendering, details, flags), which remains visibly its real location. A two-handed weapon in RANGED consumes both hand rows; one in a hand slot consumes the other. **The paper-doll is one shared composition** (v24.7 — #195): a single helper renders it; since the `inv` trim it has exactly one consumer, bare `equip` (v24.16, #208).
1. **Inventory — `inv`'s render.** A `Slot / Name / Quantity / Details` table, flat alphabetical by name. The Slot cell names the item's equip slot when slotted (`Main hand`) — an item valid in more than one slot names them **all**, joined with `/` in authored slot order: `Main hand/Off hand` (v24.8 — #197) — appending the word for two-handed weapons after the full label — `Ranged (two-handed)` (v24.7 — #194) — and muted `-` when slotless; identical items fold into the Quantity column per the stacking rule below.

Display rules:

- **Details** reads `90%, Uncommon, Bound` — durability + rarity + binding, no brackets. The durability number is colored by the **mechanical durability band** (derived from the band table in 6.5, never its own thresholds: no penalty → value-color, penalty bands → say-color, broken → error-color); rarity words are always rarity-colored in information output; the binding flag reads `Bound | Unbound`.
- Durability appears only for items with `takes_durability_loss=True`; bags show their carry contribution (Section 6.10) instead. Unidentified items show no Details suffix at all — no durability, no carry contribution.
- Cursed items that have not been identified show no curse indicator.
- Unidentified items show only their mystery name (no rarity, no Mk tier) in place of the real item name.
- Carry count rides the section header: `Inventory (12/250)...`

**Stacking (v23, #18) — by item type, display only.** Wear-free interchangeable items stack; anything carrying wear, rolled stats, or per-instance identity never does:

| Item type | Stacks | Why |
|---|---|---|
| Consumable | **yes** | interchangeable; no durability, no rolled stats |
| Material | **yes** | interchangeable by definition — hides are hides |
| Readable | **yes** | interchangeable |
| Key | **yes** | interchangeable |
| Weapon | never | durability and rolled stats are per-instance |
| Armor | never | as weapons |
| Accessory | never | as weapons |
| Bag | never | carry capacity is per-instance |

Two items fold into one row only when they share **definition, Mk tier, rarity, and soulbound state**. Binding is in the key because the flag block would otherwise lie: a bound Healing Draught Mk 1 and an unbound one are not the same row, because one of them can be dropped and the other cannot.

Stacking is a **display fold and nothing else.** The inventory remains a flat pool of distinct instances; every command still resolves against instances, quantities still mean "how many of these you have", and nothing about ownership, binding, or durability changes because two rows became one.

### 6.12 Vendors

- **General merchant** — consumables, basic gear
- **Specialty vendor** — zone-specific items
- **Repair vendor** — restores equipment durability
- **Skill trainer** — sells skill books for cross-tree skills

Vendor inventory is configured via the **`VendorEntry`** model. Each row links an `NpcDefinition` to an `ItemDefinition` with a Mk tier and an explicit copper price. An NPC with one or more `VendorEntry` rows is a vendor — no flag is needed on `NpcDefinition` itself. Stock can be unlimited (`stock_limit = null`) or finite; finite stock exhausts via a sold counter. Repairers are marked with `NpcDefinition.is_repairer`.

**Commerce (settled in v18, carried in the commerce brief):**

- **Item value = `base_value × Mk tier × rarity multiplier`.** Every ItemDefinition carries an authored `base_value` (its worth in copper at Mk 1 Common). Rarity multipliers: Common ×1, Uncommon ×2, Rare ×4, Epic ×8, Legendary ×16, Artifact ×32.
- **Vendors pay one third.** Sale price = value ÷ 3, minimum 1 copper. Vendor *buy* prices are authored per `VendorEntry` — never formula-derived.
- **Only unequipped items can be sold; soulbound items CAN be sold.** Selling is compensated disposal: the sold instance ceases to exist, vendors never resell player items, so the no-trading pillar stands untouched. (A cursed item can't be unequipped, therefore can't be sold while the curse holds — the curse keeps its teeth for free.)
- **Vendor-bought items are always Common rarity**, generated at the entry's Mk tier.
- **Repair is paid per attempt; failure is harmless** — copper spent, item unchanged, retry immediately. Success always restores 100% durability; items are never destroyed by repair. Cost per attempt = value × missing durability × 50%. Success chance = 20% + (current durability × 75%) — honoring the very-difficult-at-zero rule.
- **Commands (v22 grammar — Section 9.1 is authoritative):** `list` (vendor stock), `buy [<N>] <item>` (numeric quantity only; `all` refused), `sell [<N>|all] <item>` and `sell all <rarity> [<item>]` (bare `sell all` is refused with wording that teaches the noun form), `repair <item>`, and `repair all` — which **loops**: passes over what is still damaged until everything is repaired, funds run out, or 5 passes (#75), each mend line printing as it lands. Bare `buy`/`sell`/`repair` prompt for a target (the v18 bare-repair convenience retired to the standard prompt). Commands route automatically: buy/sell/list to the living vendor in the room, repair to the living repairer — killed service NPCs are out of business until they respawn. The noun-less `sell all <rarity>` excludes the consumable type by default (v23.1, #150) — consumables sell only when named (`sell all draught`); a skipped stack is announced with one note line, and a bulk sell matching only consumables is a world-declined refusal.
- **The vendor list (v22, #123/#58):** a `Slot / Name / Details / Price` table — Details shows rarity only (entries are definitions, not instances — no durability, no binding flag); two groups, **free first** (Price reads a muted `free`), then priced, alphabetical within groups; every price through the tier formatter.
- **Transactional aggregation (v22; `use` joined v23.3 by #151):** buy/sell/drop/pickup with N > 1 answer with **one count-form line per item definition** — `You buy Healing Draught Mk 1 ×100 for 9 silver.` (no article, total money) — a transaction is one act however many items it moves. `use` of instant-restore healing consumables is likewise one computed act: the deficit measured up front, only the items the heal needs consumed (oldest-first), one merged line (`You use Healing Draught Mk 1 ×3 and feel your body recover. (+75 Vitality)`), one status update — the v22 per-line ruling is superseded for `use` alone; timed-effect consumables keep the per-item sequence. `repair` and `loot` stay **per-line**: each iteration is its own news (a mend's chance outcome, a find's identity). The count form is the deliberately plural-free first iteration; natural-English pluralization is a filed future subsystem (#126). `heal` rides the same computed-transaction machinery with the count driven by the deficit instead of a player-supplied N — one merged sentence in the count form, mixed-Mk groups joined per the standing sentence form (Section 9.1).
- **Materials** are an item type (`material`) — no slots, stats, or durability; pure vendor-sellables (Animal Hide, Insect Carapace, and their future kin). Animals drop no copper — only higher sentient species carry money.

**Combat QoL (v18 → retired v22):** the v18-era targetless `attack`/`kill` auto-target under aggro was **removed in v22** as a fossil — aggressive NPCs engage the player themselves on entry and on their spawn tick (v21, #17), so the bare form no longer had a job; `attack` now requires a target and bare invocation gets the standard prompt (Section 9.1).

**The Robotic Helper NPC:** A unique NPC that can be summoned by players in the field. There is only one. It is not instanced per player. It will not always come when called. It functions as a mobile vendor alternative to stationary vendors in town. Full design TBD.

Vendor inventory refreshes on a timer. Some vendors carry rare rotating stock.

### 6.13 Crafting

Crafting is a skill track open to any character. Four disciplines:

|Discipline   |Produces                     |Key Stat|
|-------------|-----------------------------|--------|
|**Smithing** |Weapons, armor               |STR     |
|**Tinkering**|Tech items, gadgets, traps   |INT     |
|**Alchemy**  |Potions, poisons, consumables|WIS     |
|**Tailoring**|Light armor, cloaks, bags    |DEX     |

Crafting requires: schematic + materials + crafting station. Max craftable rarity: Epic. Legendary and Artifact items are found/granted only.

Material gathering uses room-specific commands: `forage`, `mine`, `salvage`, `harvest`. Success uses PER and relevant skills.

-----

### 6.14 Convergence Services, the Starter Kit, and Display Rules (v19)

**The Convergence gearing-up story:** the hub clothes new players. Morra (smithy) vends weapons and armor and repairs anything; Pella and Ferwick (the gazebo) vend trinkets and bags and repair — one shared stock, two voices; Repairbot Prime repairs only. All vendors and repairers are `attackable=False` by rule (seed-verified, hard failure).

- **The free starter kit:** eleven distinct authored definitions at `base_value=0` — exploit-proof by construction (sale value is exactly 0; see the disposal rule below). The kit covers every equipment slot except OFF_HAND and RANGED — deliberate gaps; the first slots a player must *earn* (Morra's priced tier sells them). Kit gear wears normally (`takes_durability_loss=True`) and repairs for ~nothing via **pity-repair** lines in each repairer's voice — the durability loop is onboarding, and the first lessons are free.
- **Priced tier:** a small aspiration shelf at Morra (shortsword, shield, sling, jerkin) priced for early hide-money; the full price-range spread is a future stocking pass.
- **Zero-value disposal (v23, #138):** a vendor **accepts** a worthless item and pays exactly **0** — the sale price floors at zero, not at the old one-copper minimum, and the refusal that used to guard the exploit is gone because the arithmetic now guards it. This opens the only exit the bound starter kit ever had: kit pieces are soulbound the moment they are equipped and can never be dropped, so before v23 a player's first gear was stuck in the pack forever. The vendor says so in its own voice — taking out your trash is a service, and it is spoken like one.
- **Artifacts are never sold (v23, #138):** a vendor refuses an Artifact at any value, and refuses it **generically**. Refusal speech never names or implies rarity, tier, or true name — **the no-leak rule** — because a refusal that said *why* would be a free identification oracle, and identification is earned (Section 6.8).
- **Currency display rule:** every player-facing money amount — `list` prices, `buy`/`sell` amounts and refusals, repair quotes — renders through the shared tier formatter. Raw copper counts never reach the player; zone aliasing comes free.
- **Multi-vendor rooms** resolve `list`/`buy`/`sell`/`repair` to a deterministic serving NPC (lowest pk); at the gazebo the non-serving spouse kibitzes after transactions.

-----

### 6.15 The Healing Economy — the Income Law & Loot-in-Kind

The healing economy is one ledger with three legs — draught cost (the Draught Law, 6.9), income (this section), and time (out-of-combat regen, Section 4) — balanced together by rule.

**The Income Law (k = 2).** Expected income from a kill ≈ **2 × the expected draught cost of that kill**, calibrated per kill at solo cost for the on-level even-split reference build. Ruled provisionally 2026-07-30 and **kept on the data** (2026-08-01): the #180 fight-cost survey plus a full faucet audit confirmed the constant against measured per-fight costs. k degrades gracefully as fights stack — drops pay linearly while grouped fights compound superlinearly, so multi-aggro rooms run leaner than their parts: the signposted ×3 rooms (Lion's Watch, Bear's Throne) sit at k ≈ 0.8–1.0, deliberately break-even prestige fights rather than profit centers.

**Faucets are lore-constrained.** Blanket copper on aggressive mobs is rejected — beasts and insects don't carry coins (6.12 stands: only higher sentient species carry money). The audit found bosses (k ≈ 2.3–11.8) and villagers (k ≈ 2.4–27) **already satisfy the law; their copper is unchanged** (a boss jackpot bump stays available as pure feel, never need). The entire structural deficit was the aggressive grind population — every animal and insect paid ~0.7 cp/kill against solo costs of ~7.2 (normal) / ~26.2 (elite) — and the same fix retires villager-killing's run as the game's mathematically optimal income. Grind mobs pay instead in **loot-in-kind**: healing draughts and materials on their loot tables.

**Loot-in-kind accounting.** A looted draught counts as **15 cp** of income (avoided purchase; `base_value` 15 — the vendor price standard — sale 5). Sensitivity floor: valued at sale instead, the tables still clear break-even — a player who never needs healing profits on materials alone.

**The design shape: draughts-in-kind cover roughly the consumption rate; materials are the profit.** In-kind supply deliberately runs below total consumption, so the vendor sink stays alive — some draughts are always bought.

**The enrichment tables** (per-tier tables replace the old tier-shared pair; all drop entries stay Mk 1 in the Mk 1 band; this table is authoritative over prose):

| Table | Applies to | Draught | Materials | E[income]/kill | k solo |
|---|---|---|---|---|---|
| Trivial (`animal-drops`, unchanged) | the seven trivial passives | none | hide 0.35 | ~1.4 | harmless |
| Enriched normal (animal + insect variants) | all combat normals, incl. the Verdant boss adds | 0.35 | common material 0.5 | ~7.3 | ~1.6–2.0 |
| Elite (animal + insect variants) | all 12 elites, incl. the delve adds | guaranteed (1.0) | elite material guaranteed (1.0) + common material 0.5 | ~29 | ~2.2 (1.6 room-blended) |

- **The trivial carve-out:** the river otter, black bear, young mountain lion, plains deer, plains rabbit, prairie dog, and mountain squirrel keep the draught-free table — a 1-minute-respawn rabbit farm must never become a faucet.
- **Common materials rebased:** Animal Hide and Insect Carapace both to base 12 (sell 4). Global — the trivial table drifts 0.7 → 1.4 cp/kill and boss side-drops rise by the same hair, both harmless.
- **Elite materials:** two new material definitions (one animal, one insect), base 36 (sell 12), guaranteed on every elite kill — the premium the tier's triple-cost fights earn.
- **Insects yield draughts** (sanctioned lore call): the delve economy requires it — the elite roster is nearly all insects. The lore cover: devoured travelers' effects among the remains.

**Mk invariance.** Draughts-per-fight is level-stable (the Draught Law heals a fraction of the pool) and material value scales base × Mk, so the tables' ratios survive into Mk 2 zones — later balance passes inherit a shape, not stale constants.

Aggregate sanity check (a 20-normal / 6-elite / 1-boss session): income ≈ 460 cp against ~18 draughts consumed (270 cp) — k ≈ 1.7, with loot-in-kind supplying ~13 of the 18 and the rest purchased. Deficit gone, sink alive.

-----

## 7. Social Systems

### 7.1 Communication Channels

|Channel|Command             |Scope                          |
|-------|--------------------|-------------------------------|
|Say    |`say <text>`        |Current room only. **v22 format:** speech renders `Name: message` in say-color — players and NPCs alike, no `[say]` prefix; the speaker receives their own broadcast (double vision is intentional; `echo off` is the remedy for the command echo, not the speech) |
|Yell   |`yell <text>`       |Current room + adjacent rooms  |
|Tell   |`tell <name> <text>`|Private between players — never from the game (Section 10.11) — anywhere|
|Party  |`party <text>`      |All party members              |
|Guild  |`guild <text>`      |All online guild members       |
|Zone   |`zone <text>`       |All players in current zone    |
|General|`general <text>`    |All players online (throttled) |
|Emote  |`emote <text>`      |Freeform action in current room|

All channels flow through Monitoring and Command (MC): nothing in the game is private (the total-capture doctrine, Section 10.11) — capture serves balance, analysis, and AI as well as moderation.

### 7.2 Parties

- 2–6 players
- Shared XP with party bonus multiplier (6-player party: ~70% of solo XP each — worthwhile for harder content)
- Party members' Vitality, Acuity, and Longevity visible in side panel UI

### 7.3 Guilds

- Up to 100 members
- Customizable ranks with permissions
- Guild bank (rank-gated access)
- Guild hall (purchasable instanced area with recall point, vendors, crafting station)
- Guild XP track (levels 1–20, passive bonuses for all members)

### 7.4 Reputation System

Reputation scores with major factions in each zone. Affects: NPC dialog, faction-exclusive vendors and quests, shop prices, access to restricted areas. Reputations are permanent. NPCs remember your history.

### 7.5 PvP Zones & Flagging

- Entering a PvP zone requires confirmation
- PvP kills grant PvP XP (separate track from normal XP) and have a chance to drop carried (not equipped) items
- **Bounty system:** Repeatedly killing the same player places a bounty on the killer
- Logging out in a PvP zone: character persists in world for 60 seconds before fading — killable during that window

-----

### 7.6 NPC Dialogue — The Listening Model (v19, voiced through v23)

NPCs are not addressed; they **listen**. There is no `talk` or `ask` verb by ruling — dialogue is diegetic room speech: you say things aloud, and inhabitants who know something about what you said may answer. The mechanic is the fiction.

**Mechanics (all ruled v19):**

- Per-NPC keyword→response maps (`DialogueEntry` with lowercase single-word keywords, `DialogueResponse` pools). Matching is dumb word-level containment — no NLP. Unmapped NPCs stay silent.
- One utterance → each eligible NPC answers **once**. **Entry-first draw:** among an NPC's matched entries, one entry is chosen at random, then one response from its pool — each matched *topic* gets equal voice regardless of pool depth. Re-asking re-rolls.
- **No consecutive self-repeats:** an NPC avoids the response it gave last time when its pool offers an alternative.
- Multiple responders: **random shuffle per utterance**, delivered tick-staggered at **2 ticks between speakers** ("less than combat, a little more sociable, less interrupty"). Second and later speakers are introduced by position-aware **connective color** drawn from pooled templates ("{name} also looks up and answers." / "{name} chimes in, not to be left out.").
- Responses **broadcast to the room**, riding the standard `say` formatting — identical for asker and witnesses. Responses **always land**, even if the asker has left; if the asker is gone when the final response fires, that last speaker may add one lore-voiced **departure reaction** (Aldric snorts. "Youth," he mutters, to no one in particular.).
- **Greetings:** an NPC with a greeting entry emits one line the first time a given character enters its room — once per character, forever.
- **Speech is attributed; narration is not (v23, #147).** A keyword answer is speech: it renders `Name: text` in say-color, exactly like a player speaking. A greeting or a departure reaction is *narration* — authored in the third person, it renders verbatim, unprefixed, in the ambient voice, and draws no connective. The distinction is the same one the whole output layer runs on, and it is why a greeting reads `Aldric looks you over once, unhurried, and nods` rather than announcing his own name twice before doing it. Connectives introduce answers; nobody needs introducing to a greeting.
- **Discoverability:** examine-text hints on talkative NPCs, a `help` line, greetings demonstrating that NPCs speak, and room-broadcast answers teaching bystanders — discoverable, never announced.
- Authored dialogue carrying directional or locational claims is verified against the room graph before shipping (standing rule from issue #34).

**The pool floor (v23, #40).** Every keyword entry and every departure entry carries **at least three** responses. A line a player will hear repeatedly must have somewhere else to go — the duplication was the defect, and the pools are simply what fixing it looks like. **Greetings carry exactly one** response, deliberately: a greeting fires once per character forever, so variety in that pool is invisible by construction and authoring it would be waste.

**Everything the world says repeatedly is pooled (v23, #40).** The rule reaches past the dialogue system to every flavor line the game speaks more than once: sell and buy acknowledgments, the sold-out line, all six paid-repair outcomes, the per-NPC pity-repair lines for every repairer, the vendor kibitz, and the aggro-engagement line at all three of its call sites. The governing distinction: **speech gets pooled; renderings stay stable.** A vendor's greeting varies; the vendor's *list* does not, because a report is not a person talking. Pool selection is plain random draw in the established style — no novel machinery, and the dialogue system's no-consecutive-repeat guard remains its own refinement.

**The roster (v23).** Sixteen voices. The Convergence: Aldric, Info Prime, Morra, Pella, Ferwick, Repairbot Prime, Seris, Veris, and the two ring carts VND-9 and Mother Tansy. The Verdant Reach checkpoints, silent since the zone shipped and given voices in v23 (#144): Maro the Mender and Essa the Trader at Fordwatch, Tavik the Mender and Sona the Trader at Stairhead, Old Brammel and Ridda the Trader at Cragfoot. Because each checkpoint pairs a mender with a trader in one room, the checkpoints are also where the multi-speaker machinery is most visible: ask for help at Cragfoot and both of them answer, staggered, the second introduced by a connective.

**Silent by ruling.** The Obelisks, the Spheres, and the Verdant Shard have no dialogue entries and will not get them — mystery preserved, enforced by a seed invariant rather than left to authoring discipline. Persistent NPC memory (Sirius-class entities) remains a future tier.

**Authoring is data, not code.** The corpus lives in the seed as a declared map from NPC to entry specs; adding a voice, a topic, or a line is a data change with no code change and no migration. The invariants above — the pool floor, one greeting, one departure pool, the silent roster, keyword tokens that the tokenizer can actually match — are enforced both at seed time and by test, so a voice cannot ship half-authored.

-----

## 8. Quest & Narrative

### 8.1 Quest Types

|Type             |Description                          |Primary Reward                   |
|-----------------|-------------------------------------|---------------------------------|
|**Kill**         |Defeat X enemies or a named target   |XP, loot                         |
|**Fetch**        |Retrieve an item and return it       |XP, currency, rep                |
|**Escort**       |Keep an NPC alive during movement    |Unique items, rep                |
|**Explore**      |Discover a set of locations          |XP, map reveal                   |
|**Craft**        |Produce a specific item              |Schematic unlocks                |
|**Investigation**|Multi-step, dialogue-heavy, branching|Story progression, unique rewards|
|**World Event**  |Timed server-wide quest              |Prestige currency, cosmetics     |

### 8.2 Quest Structure

Quests given by NPCs through the dialogue system (Section 7.6 — NPCs listen to `say`). Quest givers flagged in the client UI.

Quests have: journal entry, tracked objectives, completion trigger, and branching outcomes for Investigation quests. Quest chains unfold zone stories and may permanently alter zone state.

### 8.3 NPC Dialogue System

NPCs respond to spoken keywords (`say` — the v19 listening model; there is no `talk`/`ask` verb by ruling). Future: conditional responses based on reputation, quest state, Origin, Archetype; NPCs remembering if you've helped or harmed them remains the Sirius-class special-entity tier.

Genre collision is reflected in NPC dialogue: *"I've never seen armor like that. What did you say it's made of? 'Kevlar'?"*

### 8.4 Lore Delivery

- Room descriptions (environmental storytelling)
- NPC dialogue
- **Lore items** — readable books, data tablets, inscribed stones
- **Zone flavor text** — ambient periodic messages in rooms
- **The Codex** — in-game journal accumulating lore entries on discovery

### 8.5 Dynamic World Events

Periodic server-wide events: rift openings, faction assaults on towns, legendary boss spawns. Announced via General channel.

**No seasonal content.** World events are lore-driven, not calendar-driven.

-----

## 9. Player Command Reference

This section is the authoritative list of all player-facing commands. Commands are typed into the input line and sent to the server. The server is the only authority — no command has any effect unless the server accepts and processes it.

Commands are case-insensitive. Arguments are separated from the verb by a space.

### 9.1 Implemented Commands (v22)

This subsection is the authoritative command reference, absorbed from the v22 B2 command specification DD and synced to the shipped dispatch table at closeout. Every command belongs to one of four types — **action, information, movement, settings** — and its argument cell in the chart is law.

#### The Command Chart

Cell notation: footnote numbers listed left-to-right in argument order; listed = admitted; requiredness per footnote text; `|` = alternatives.

| Type | Command | Arguments | Added |
|---|---|---|---|
| action | attack (kill, k) | 5 \| 6 · 10 | |
| | attune | 2 | v24.26 |
| | buy | 11 4 · 10 | |
| | cancel | 12 | v22 |
| | drop | 11 4 · 10 · 16 | |
| | equip (eq) | 4 · 21 | |
| | examine (ex) | 4 \| 5 \| 6 · 10 | |
| | flee | 2 | |
| | heal | 2 | v24.4 |
| | home | 2 | v22 |
| | loot | 3 \| 5 · 20 | |
| | mc | 22 · 18 | v25.4 |
| | pickup (p) | 7 4 · 10 · 13 | |
| | quit | 2 | |
| | repair | 3 \| 4 · 10 | |
| | say | 9 · 10 | |
| | sell | 7 4 · 10 · 13 · 17 · 19 | |
| | spend | 7 14 · 10 · 15 | |
| | sudo | 9 · 18 | v22 |
| | travel | 8 | |
| | unequip (uneq) | 4 · 10 | |
| | use | 11 4 · 10 | |
| information | help (?) | 2 | |
| | inventory (inv) | 2 | |
| | last | 2 · 18 | v22 |
| | list | 2 | |
| | look (l) | 2 | |
| | stats | 2 | |
| | wallet | 2 | |
| | who | 2 | |
| movement | down (d) | 2 | |
| | east (e) | 2 | |
| | north (n) | 2 | |
| | south (s) | 2 | |
| | up (u) | 2 | |
| | west (w) | 2 | |
| settings | brief | 1 | |
| | echo | 1 | v22 |
| | plunder | 1 | v24.29 |
| | timestamps | 1 | |

#### Footnotes (stable numbering; never renumbered)

1. one optional argument, a human-readable boolean: exactly on, off, yes, no, true, false. Case-insensitive.
2. no arguments expected or required; all arguments are ignored.
3. a literal "all" targeting all possible matches for the command.
4. `<item>` — match against an item name (with or without rarity words).
5. `<NPC>` — match against an NPC name.
6. `<player>` — match against a player name.
7. `<quantity>` optional; a number or the literal "all" (as many as match).
8. `<destination>` — match against a sphere or shard travel destination name. (v24.25) Locked-zone destinations stay in the match pool — listed muted, matchable, and the attempt draws the zone-lock refusal (Section 2.12). (v24.26) The pool is the room's sender type's offering: every revealed node at an obelisk, revealed spheres only at a checkpoint shard (Section 2.11).
9. `<*>` — any arguments are accepted.
10. a target is required: at least one listed argument must be present. Bare invocation responds with the standard prompt `What do you want to <verb>?` (error-color).
11. `<quantity>` as footnote 7, but "all" not accepted (numeric only).
12. `<command>` optional; match against the name of a currently running command (e.g. home).
13. a numeric `<quantity>` must be accompanied by a target argument; "all" may stand alone. Bare numeric responds `<verb> <N> what?` (error-color).
14. `<stat>` — match against a stat name (str dex end int wis per).
15. as footnote 13, but the bare-numeric response is `spend <N> points on which stat?`
16. bound items are excluded from this command's candidate pool.
17. "all" requires the target argument for this command: bare `<verb> all` is refused (warn-color) with wording that teaches the noun form.
18. admin-gated with stealth: requires membership in the `admins.shyland` Django auth Group, checked live per attempt. For non-members the command does not exist — absent from help, absent from tab completion, and attempts return the standard unknown-command response.
19. the consumable item type is excluded from this command's noun-less bulk form (`all <rarity>` with no noun): matching consumables are skipped, and the skip is announced with one note line teaching the named form. A noun-less bulk sell whose matches are *all* consumables is refused (warn-color). Named-noun forms (`sell all draught`, `sell 5 draught`) reach consumables normally. (v23.1, #150)
20. the target is optional: bare invocation behaves exactly as the literal `all` — verbatim, in every case. Loot is the first (and so far only) verb whose bare form performs the `all` sweep; deliberately **not** a precedent for `sell` (#150's refusal of the bare bulk form stands — loot is kill-gated and value-safe, sell is destructive of inventory).
21. the target is optional: bare invocation is an **information rendering** — it reports instead of acting. For `equip`, the bare form renders the Equipment paper-doll (Section 6.11) — and nothing else: no inventory table, no carry count, no wallet line. Since the `inv` trim it is the paper-doll's only home (v24.16, #208). Report category (unstamped, never varies). Distinct from footnote 20: a bare information form performs no action and sets no precedent for bare bulk actions. (v24.7 — #195)
22. `<subcommand>` — exactly one required argument from the command's closed subcommand vocabulary (for `mc`: status, kill, restore). Bare invocation or an unknown subcommand draws the standard usage prompt (error-color). Subcommands tab-complete; the pool is the closed vocabulary. (v25.4)

**Grammar notes:** `N.noun` ordinal selection (e.g. `attack 2.lion`) survives as input-only CLI shorthand across all noun-matching arguments; the game never speaks ordinals except the duplicate-only display ordinals of §5.9 (#64). Argument order is as listed — `spend` is `spend <quantity> <stat>`, flipping the pre-v22 order. `attack`'s chart cell admits `<player>` for the PvP future; until PvP mechanics exist the shipped pool is living NPCs only (recorded implementation judgment). One resolver serves every noun-taking command (v20): ordered token-prefix matching on the player-visible name-with-tier, plural fallbacks, rarity as a closed-vocabulary instance filter (noun optional with a rarity word — `sell all common`), cross-definition ambiguity refuse-lists, rarity-aware protective selection (`sell`/`drop` lowest-first, `equip` highest-first), equipped items always excluded from `sell`/`drop`, consumables excluded from the noun-less `sell all <rarity>` bulk form (footnote 19; v23.1). A dispatch guard wraps every command: no input, however malformed, can drop the connection. `heal` is the bare-verb shortcut for deficit-driven draught consumption (see Partial Fulfillment); it takes no arguments and is a **reserved built-in verb** — the future alias system (#125) may never shadow it. Tab completion completes the verb; there is no noun pool.

#### The Three-Layer Response Doctrine (v22)

Every response to a command belongs to exactly one layer, and the layer picks the voice:

- **CLI error (error-color, red):** the parser refused — unknown command, bad syntax, missing required argument (the footnote 10/13/15 standard prompts), settings usage lines. The machine didn't understand you.
- **World declined (warn-color, yellow):** valid command, world says no — resolution failures (no match in the pool, bad index, ambiguity, the sell-all block, the consumables-only bulk sell (v23.1)) and mechanical failures (state-gate refusals, no vendor/repairer/obelisk here, can't afford, sold out, at capacity, repair didn't hold, heal at full, bound-drop attempt, unequip without bag room, failed flee, the zone-lock entry refusal on movement and travel (Section 2.12; v24.25), the generic Artifact sale refusal — no-leak, Section 6.13). The world understood you and refused.
- **World answered (normal voices):** success prose, the combat family, loot-color gains.

**Consequence must be seen (#132):** the partial-fulfillment shortfall reports (`You only had N.` on use and drop, `There were only N here.` on pickup, `They only had N.` on buy) and use's no-effect `Nothing happens.` speak in the warn voice — a consequence delivered in the muted ambient voice goes unread. Deliberate exceptions, ruled correct: the sell shortfall keeps its friendly success voice (`You only had 3 — the vendor was happy to take them.`), and the ambient system voice keeps the logout farewell and the muted combat misses.

#### The State-Gating Matrix (v22)

- **In combat — allowed:** attack, flee, use (except durability-restore consumables — the Repair Kit refuses in the no-mending doctrine, gate keyed on the effect component, its own authored warn line; v24.12), heal (v24.4), examine, cancel, say, sudo, mc (v25.4), quit, all information commands (including `list`), all settings — and attune (v24.26: no gate needed structurally — every attunable room is a safe room, so an in-combat `attune` can only ever draw the nothing-here warn; Section 2.11). **Refused (warn, in voice):** buy, sell, repair, drop, pickup, loot (#29), equip (targeted forms only — bare `equip` is an information rendering and is allowed, per footnote 21; v24.7 — #195), unequip, home, travel, all movement — and **spend** (#131, blocked by later ruling with the first generic refusal `You can't do that while in combat.`; every other combat refusal is a per-command authored line).
- **While dying — allowed:** use (restoratives only — durability-restore consumables refuse: nothing but healing while dying; v24.12), heal (v24.4) (self-rescue heal — deliberate design), cancel, say, sudo, mc (v25.4), quit, information, settings. Everything else refused (warn).
- **Quit is allowed in both states, and combat continues after quit** — `CombatSession` is database state; no code path ends it on disconnect. The player can die logged out. Tab-closing and quitting are identical in cost, which is what makes the design honest rather than theater.
- `cancel` is allowed in every state — the escape hatch is never locked.

#### Resolution Scope Pools

buy → room vendor stock · sell → inventory excluding equipped (bound sellable — vendors are the designed sink) · drop → inventory excluding equipped and excluding bound (footnote 16) · pickup → room floor · equip → carried equippables (equippability = mechanical layer) · unequip → equipped only (inventory room = mechanical layer) · use → carried consumables, never vendor stock · repair → everything owned including equipped · **examine → the union**: inventory + equipped + floor + vendor stock + NPCs here + corpses + players here (the vendor-examine gap closed; players answer with their composite line) · attack → living NPCs in the room · loot → lootable corpses here · travel → revealed destinations the room's sender type offers (revealed spheres only at a shard; v24.26) · spend → the six stats · cancel → your running delayed actions. `attune` takes no noun — no pool (v24.26).

Pool miss = warn. Same-segment ambiguity: **nearest wins** (self before room before vendor); ordinals and tab disambiguate.

**The name invariant (#122): a player and an NPC may never share a name.** Two enforcement edges: character creation rejects any name matching an NPC definition name, case-insensitive (`That name belongs to the world already.`), alongside the existing uniqueness and profanity checks; and seed verification permanently checks that no NPC definition name collides with any existing character name.

#### Partial Fulfillment Doctrine

Do the possible part and report warmly; fail (warn) only when nothing is possible. Stop when purpose is fulfilled. Specifics:

- Sell/drop/use/pickup shortfalls do the possible part with the warm note preceding the result; any pickup at capacity fails outright (warn); partial `pickup all` takes oldest-on-floor first.
- **Heal sequences (#61, #65; reruled by #151):** `use N` on an instant-restore healing consumable is **one computed transaction** — the deficit is measured up front, exactly the items the heal needs are consumed (capped by N and inventory, oldest-first in resolution order), and the heal lands as one act: one line, one status update. A heal that reaches full folds `You are restored to full health.` into the end of that line, the whole line reward-color; any heal attempted at full still fails (warn); the shortfall warn (`You only had N.`) keeps its own line, firing only when the request exceeded inventory and the deficit wasn't covered. While dying, `use` consumes exactly one restorative — the v19 revival sequence, never over-drunk. Timed-effect consumables keep the per-item sequence. **`heal`:** the bare-verb form of the same computed transaction, with the count driven by the deficit itself — "use as many healing draughts as needed." The vitality deficit is measured once; the minimum draughts that cover it are consumed (or all remaining, if short), oldest-first regardless of Mk (#168), each item's heal computed from its own Mk under the Draught Law (Section 6.9); one merged count-form line, one status update. At full vitality: the standing heal-at-full refusal (warn). No draughts carried: world-declined warn. Supply exhausted short of full: the shortfall reports in the warn voice (#132). While dying, `heal` behaves exactly as `use`: one restorative, the revival sequence, never over-drunk.
- **`repair all` (#75):** passes over what is still damaged until everything is repaired, funds run out, or 5 passes; each mend line prints as it lands.

#### Success Sentences and Aggregation

The transactional commands answer with one plain past-tense sentence, item names verbatim with rarity words rarity-colored, articles via the NPC-article machinery: `You buy the Iron Mace Mk 1 for 9 coppers.` · `You sell the Leather Gloves Mk 1 for 3 coppers.` · `You drop the Battle Axe Mk 1.` · `You pick up the Healing Draught Mk 1.` (loot-color) · `You equip the Iron Mace Mk 1.` / swap-aware `You equip the Battle Axe Mk 1, replacing the Iron Mace Mk 1.` (the slot is the paper-doll's job, not the sentence's) · `You unequip the Iron Mace Mk 1.` · `You use a Healing Draught Mk 1 and feel your body recover. (+25 Vitality)` — the effect clause merged into the sentence, one envelope, success-color (v23.3, #149; timed-effect consumables have no apply-time effect message and keep the plain sentence; multiple instant components join their clauses in order) · repair's line stands · `You spend 3 points on Dexterity.` + the new value · `You stop heading home.` (cancel, named per action).

**Multi-item output splits by nature:** buy, sell, drop, and pickup **aggregate** — a transaction is one act, so N > 1 emits one count-form line per item definition (`You sell Healing Draught Mk 1 ×100 for 4 silver 50 coppers.` — no article, total money; mixed sweeps emit one line per definition in floor order, singles staying singular; warm shortfall notes precede). **use joined the aggregates in v23.3 (#151)** for instant-restore healing consumables: one computed transaction, one merged sentence in the count form — mixed-Mk consumption joins its definition groups with commas into the single sentence (`You use Healing Draught Mk 1 ×2, Healing Draught Mk 2 ×1 and feel your body recover. (+85 Vitality)`), a count of 1 keeping the indefinite-article form. `heal` rides the same computed-transaction machinery with the count driven by the deficit instead of a player-supplied N — one merged sentence in the count form, mixed-Mk groups joined per the standing sentence form. **repair and loot stay per-line** — each iteration is its own news — and **repair-kit `use` joins them** (v24.12): each kit re-targets most-damaged-first and reports its own mend (`You use a Repair Kit Mk 1 and patch up the Iron Mace Mk 1. (+25 durability)`), the sequence stopping when nothing damaged remains (Section 6.5). (#126 files the future natural-English pluralization; the count form is never wrong in the meantime.)

#### Corpses and Loot (v22 form)

`loot` is `[all] | <NPC>`: `loot all` — or bare `loot`, its exact equivalent — sweeps every corpse in the room (per-item lines, then the summary); `loot <NPC>` loots that NPC's corpse, with `N.noun` disambiguating among same-name corpses. The target is optional, defaulting to the sweep (footnote 20 — the v18 most-recent-corpse convenience and the v20 item-noun/union forms remain retired; the bare form is the room sweep, never a single-corpse guess). Only the killing character may loot items; currency is always transferred on first loot of a corpse; a corpse that never had loot to give answers `The <npc> carried nothing worth taking.`

**`plunder` — the sweep, automatic (v24.29, #235).** The settings command `plunder [on|off]`, **default off**, runs the rights-scoped sweep for the player instead of making them type it. It adds no new capability: plunder can take exactly what bare `loot` could have taken at that moment, and nothing else.

**The trigger is one exact instant — the transition to genuinely out of combat**, meaning every NPC in the fight is dead. It is the same moment the player is told `Combat has ended.`, and it fires wherever that line is delivered. Three cases are deliberately excluded:

- **No per-kill plunder.** A kill landed mid-fight, with other NPCs still alive, never triggers a sweep — not even of the corpse just made. Only the full end of the fight counts.
- **Flee never plunders.** The fight is not over and the player is no longer in the room.
- **Death never plunders.** A dying character has already left the session and holds no rights.

**A lost race is a miss, never a queue.** If a fresh engagement begins before the sweep can run — aggro respawn in a room like The Choke — plunder simply does not fire: the player is back in combat, which is precisely the state that blocks looting (#29). Nothing is lost, because rights-held corpses persist until decay and the skipped sweep is picked up by the *next* combat-end transition. That self-correction is why no queueing machinery exists.

**Plunder is silent unless it plunders.** With nothing to take — no corpses in the room, or none this character has rights to — plunder emits nothing whatever. The refusals `There is nothing to loot here.` and `That is not your kill; you may not loot it.` belong to the *typed* command and are never spoken on plunder's behalf. When plunder does sweep, its output is the sweep's output **verbatim**: the same per-item loot lines, the same coin lines, the same summary, and the same carry-capacity refusal when the player fills up mid-sweep — a shortfall is a consequence and must be seen (#132). A plunder is indistinguishable from a `loot` the player typed.

**Plunder does not require a connected player.** Quit is allowed in combat and combat continues after quit (the state-gating matrix above), so a fight that ends for a logged-out character plunders on their behalf — the loot is theirs by the same rights predicate either way, and the output simply has no pane to land in.

#### Information Output Standards

Three kinds, one punctuation law — **colon = the value is on the line; ellipsis = structure follows below**. Headers are uniformly key-color, embedded counts included (`Inventory (12/250)...`); table column guides are muted; rows are value-color.

- **Kind 1** — `Key: Value` (the `wallet` archetype).
- **Kind 2** — `Key...` + indented value list.
- **Kind 3** — `Key...` + table (muted column headers, value rows).

Shipped surfaces: `inv` = the Inventory table alone (Section 6.11; v24.16, #208); `list` = the vendor table (Section 6.12); `wallet` = the shared Kind 1 line; `who` = one line, `Players online (3): Shy-Guy, Sharon-Love, Marvin`; `stats` = the character sheet with the `Home:` row under the Player line (the effective home node's travel name — attunement, Section 2.11; v24.26), the six stat rows (base + gear parenthetical), a blank line, the Armor row, and a blank line before Unspent; `last` = the admin Kind 3 table; `look` untouched by the standards (the room render has its own v20/v21 rules). Durability numbers are colored by the mechanical band, derived, never owned; rarity words always rarity-colored.

#### Settings Standard

Four settings commands — `brief`, `echo` (v22, new), `plunder` (v24.29), `timestamps` — share one shape: six accepted words (`on off yes no true false`, any case); **bare form reports** the current setting (`brief room display is off.`); set form answers the "now" sentence (`command echo is now on.`); invalid input answers the CLI `Usage: <cmd> [on|off]`. Stateless, idempotent, plain prose. **Defaults: brief off (flipped in v22 for new characters; existing players kept their setting), echo on, plunder off, timestamps on.** Unlike its siblings, `plunder` changes what the *world* does rather than what the player's pane shows — the setting is read at the moment combat ends, so a mid-fight flip governs that same fight. Echo is **pane-only**: `echo off` suppresses the player's own `> command` echo lines in their pane and nothing else — server behavior, timestamps, and future MC capture (Section 10.11) are untouched; every command remains a stamped event.

#### Help

`help` is generated from the chart: four type sections (key-color `...` headers), Kind-3 `Command / Usage / Description` tables, usage strings compiled from the chart cells in BASH notation (`<>` required, `[]` optional, `|` alternatives), authored one-line descriptions, and four shared bottom sections (Arguments, Quantities, Settings, Tab completion). Admin commands render only for members. Help always ends with a blank line and the Kind-1 `Version:` line — `SHYLAND_VERSION`, the single source of truth for the player-visible version, bumped to the release stamp at every version closeout (point releases bump it on main). The constant tells the truth about the code it ships with.

#### Admin Commands and Stealth Gating (v22)

The Django auth Group **`admins.shyland`** grants in-game admin. `sudo`, `last`, and `mc` gate on membership, **checked live on every attempt** — no session caching, revocation instant. For non-members the commands do not exist: absent from help, absent from completion, and attempts return the unknown-command response **byte-identical to gibberish input** (footnote 18).

- **`sudo <anything>`** (#112) — speak to the watcher. **sudo is the watcher's name as well as the verb** (styled lowercase, like the command): an AI agent on the far side of the MC agent door (Section 10.11). The command's game-side behavior is unchanged from v22 — it echoes, and the game itself never responds — but the shipped silence ruling is deliberately reversed **(v25.6, #262)**: *sudo may answer if running and able to parse the request*, replying out-of-world in its talking color (sudo-color, Section 10.2) via the door's `answer` action, delivered only to a currently-valid admin (#273). It may fulfill the request outright or ask for more information — an artifact design becomes a multi-turn Q&A, and abandoned conversations time out quietly. **Silence remains the norm and is never an error:** not running, unable to parse, killed (#266), or simply declining to answer all look byte-identical to the v22 game. Scope is strictly in-game: sudo answers game-state questions and wields the door's day-one actions (gift an existing definition, create-and-gift an artifact from a full spec or a completed Q&A, strip/dress, move); ops powers are excluded by design, for the whole bot family. A request that maps to an existing command draws *"you don't need sudo for that"*; one the bot can't map draws *"I don't know how to do that"* — its command knowledge is the live verb list fetched at attach, so declines upgrade themselves as commands ship.
- **`last`** (#88) — the roster: a Kind-3 `Last seen...` table (`Character / Status / Last seen`), the composite character line (`Shy-Guy - Level 10 Highborn Blade`), Online/Offline from presence, and three time forms — `never` (no recorded connect), `since <ISO-8601 UTC>` (online), bare stamp (offline) — ordered online-by-recency, then offline-by-recency, then never. Every character's last-connect is recorded at websocket accept regardless of who can read it.
- **`mc <status|kill|restore>`** (v25.4, #266) — the MC kill switch (Section 10.11). `status` reports the switch state; `kill` silences every AI actor at once; `restore` brings them back. Flips are recorded as `mc_kill` stream events.

#### Delayed Actions and `cancel` (v22)

The **delayed-action registry** — one named, connection-bound task per running delayed action — is the standing template for every future delayed action; `home` is its first resident (design in Section 2.11). `cancel` (#113): bare with nothing running answers `You don't have anything to cancel.` (warn, verbatim); bare with exactly one running cancels it; a named argument prefix-matches the running-action names. A registry task dies silently with the connection — intent state dies with the intender.

#### Tab Completion

Server-authoritative (v20): the client round-trips the current line and receives context-correct candidates. The completer offers **exactly each command's pool at each position, literals included** — `all` only where the grammar accepts it, the six boolean words for settings, stat names for spend, revealed destinations for travel, corpse names for loot, running-action names for cancel, and examine's full union; ordinal forms where duplicates exist. The connect-time verb list omits admin verbs for non-members.

The unknown command response directs players to `help`: *"Unknown command. Type 'help' for a list of commands."* — a CLI error, byte-identical to what a non-member sees for an admin command.

### 9.2 Planned Commands (not yet implemented)

These commands are designed and documented elsewhere in the GDD but not yet in the codebase. Listed here for completeness and to prevent duplication of design effort.

#### Communication (Section 7.1)

|Command             |Description                                            |
|--------------------|-------------------------------------------------------|
|`yell <text>`       |Speak to players in current room and all adjacent rooms|
|`tell <name> <text>`|Private message to a named player anywhere             |
|`party <text>`      |Message all party members                              |
|`guild <text>`      |Message all online guild members                       |
|`zone <text>`       |Message all players in current zone                    |
|`general <text>`    |Message all players online (throttled)                 |
|`emote <text>`      |Freeform action visible in current room                |

#### World Interaction

|Command               |Description                                       |
|----------------------|--------------------------------------------------|

|`forage`              |Gather plant/organic materials in applicable rooms|
|`mine`                |Gather ore/mineral materials in applicable rooms  |
|`salvage`             |Disassemble items or gather tech components       |
|`harvest`             |Gather zone-specific resources                    |

#### Combat

*(All combat commands are now implemented — see Section 9.1.)*

#### Character & Inventory

|Command           |Description              |
|------------------|-------------------------|
|`quests`          |Show active quest journal|

*(The formerly planned `equipment`/`eq` command is superseded twice over: `eq` is `equip`'s alias in the v22 chart, and as of v24.7 bare `equip` renders the Equipment paper-doll itself (Section 9.1, footnote 21) — the equipped-only view lives on the verb that manages it, not on a verb of its own.)*

#### Travel

|Command            |Description                                            |
|-------------------|-------------------------------------------------------|
|`enter <exit name>`|Use a named exit (non-directional)                     |

*(The formerly planned `recall` scroll command is retired — v24.26, #38: `home` plus attunement (Section 2.11) covers the entire command-driven-return need; an item duplicating a free command is dead design weight. Killed, not deferred — the directional-arrows disposition.)*

### 9.3 Command Design Rules

- Every command must work via keyboard input only — no mouse-only interactions. Screen reader users must be able to access all functionality through the input line.
- Commands should be short, memorable, and consistent with classic MUD conventions where possible.
- **The chart is law.** Every command's argument behavior lives in its chart cell (Section 9.1); footnote numbers are stable and never renumbered. A new command enters the chart before it enters the code.
- **Every refusal belongs to a layer** (the three-layer doctrine, Section 9.1): CLI errors are red, world-declines are yellow, and consequence must never speak in the ambient voice.
- Every unrecognised command gets a helpful redirect, not a bare error: *"Unknown command. Type 'help' for a list of commands."*
- `help` is generated from the chart and ends with the `Version:` line. When a new command is implemented, it is added to the chart, the dispatch table, and this section — one source of truth, three synchronized surfaces.
- **Boolean commands always require an explicit value to set.** Never a bare toggle. The bare form *queries* — `brief`, `echo`, `plunder`, and `timestamps` all report their current value; six accepted words set it (the settings standard, Section 9.1).
- **Every submitted command echoes** into the output pane before its result — `> command as typed`, muted, timestamped — a transcript of the player, never re-broadcast to others, echoed even for invalid input so errors keep their context. The `echo` setting suppresses the display pane-side only; the event still exists.
- **Setting changes are events** (stamped confirmations); reports and renderings are not — see the envelope display rule in 10.2.

-----

## 10. Technical Architecture

### 10.1 Stack

|Layer                        |Technology                                                        |
|-----------------------------|------------------------------------------------------------------|
|**Backend framework**        |Django 5 (Python)                                                 |
|**Real-time transport**      |Django Channels + Daphne (ASGI) + WebSockets                      |
|**Database**                 |PostgreSQL 16                                                     |
|**In-memory / session state**|Redis 7 (Channels layer + presence tracking)                      |
|**Client**                   |Browser-based — vanilla HTML/CSS/JS, no framework                 |
|**Auth**                     |Django built-in auth with the shared gamer-tag profile system; Shyland characters have their own `name` field, initialized from the gamer tag at creation and independent of it thereafter|
|**Deployment**               |Docker Compose: nginx → Daphne → Django/Redis/Postgres            |

All game logic runs server-side. The client is a dumb terminal — it sends text commands and renders JSON output. No game state is trusted from the client.

### 10.2 Client Architecture (v20)

Web-only. Responsive down to phone screen size. No native app. **The app fits the viewport exactly — the page never scrolls;** only designated panes scroll internally.

```
┌───────────────────────────────────────────────┬──────────────────┐
│ LOCATION BAR  Zone: Area: Room (theme colors) │ CHARACTER NAME   │
├───────────────────────────────────────────────┤ V ▓▓▓▓▓░░ 226/345│
│                                               │ A ──[band]─┃─ 1.0│
│   OUTPUT PANE — one unified scrolling pane    │ L ▓▓▓▓▓▓▓ 274/274│
│   (clears on each room entry, by ruling;      ├──────────────────┤
│    room render, then zone-colored separator,  │ FIGHT INFO       │
│    then events)                               │ (scrolls; enemy  │
│                                               │  hp bars, focus »)│
│                                               ├──────────────────┤
├───────────────────────────────────────────────┤                  │
│ > COMMAND BAR            ●42ms        [SEND]  │  MAP  300 × 300  │
└───────────────────────────────────────────────┴──────────────────┘
        left 2/3 flexes on resize          right pane fixed 300px
```

**Location bar:** `Zone: Area: Room` (Area omitted when absent); zone and area names in their model-authored `theme_color`s, room near-white, separators chrome; one line; overflow truncates Area first, then Room, never Zone. Colors are server-delivered — one source of truth shared with output.

**Right pane (fixed 300px):** the stats section — headed by the **character name, verbatim casing, in value-color** — with Vitality and Longevity as ratio bars (fills in success-color — the loot-message green, verbatim, full strength; numerals and labels value-color) and **Acuity as a band gauge** (fixed 0.0–2.0 track, the Origin's optimal band as a **solid success-color block** — the translucency era ended in v22 — and a say-color gold position tick, 16×4px, extending above and below the track): the first surface that teaches the three-bars design, now speaking the chart's own colors. The whole section turns **combat-red** (from the state-sync combat boolean; the name re-points to error-color). Below it, the **fight panel**: one row per session enemy — name and `hp/hp_max` in value-color, hp bar and the focus marker `»` in error-color — fed by a `fight` message each combat tick, empty outside combat, scrolling on overflow. The **map** (Section 2.5) sits fixed at the bottom.

**Command bar:** input line with the send button inside and the **connection indicator** at its right — a dot plus latency (client pings every 10s, server echoes; green healthy, amber degraded, red pulsing on reconnect, gray dead; accessible label, never announced).

**The output envelope:** every outbound WebSocket message carries `ts` (epoch ms UTC, stamped at creation) and `seq` (per-connection monotonic, stamped at one audited delivery choke point — the envelope stamp, not the MC capture point (MC taps at creation; Section 10.11); nothing may bypass it). **`seq` order is authoritative for rendering;** `ts` may lawfully be non-monotonic against it. **Display rule — timestamps mark events, not renderings:** combat, chat, presence, commerce, XP, errors, system/ambient, setting-change confirmations, and command echoes display the dim `[HH:MM:SS.ss]` local-time prefix (aria-hidden; governed by the `timestamps` preference); room renders and state reports (inventory, stats, vendor lists, examine, help) do not.

**The output palette (v22 — the named chart):** client-side styling driven by server-sent semantic categories (the server never sends hex for message text). The complete named vocabulary, every name a CSS variable and citable design language:

| Name | Value | Voice |
|---|---|---|
| key-color | `#7FB3D5` | labels; section headers; the map here-dot |
| value-color | `#E8E4D8` | content; success prose; report text; **narration and ambient (v23)**; the known |
| muted-color | `#6b6b80` | column guides, command echo, placeholders, the unknown — **true chrome only (v23)** |
| error-color / agro-color | `#E24B4A` | CLI errors; hostile map rooms (two names, deliberately separable, currently one value) |
| warn-color | `#E8D44D` | the world declined — resolution and mechanical failures; **your misses (v23)** |
| say-color | `#f0c060` | speech, player and NPC; the Epic rarity gold (deliberate reuse); the acuity tick |
| loot-color / success-color | `#4caf7d` | gains: reward lines, pickups, looted currency, heal-to-full, "Combat has ended."; **their misses (v23)**; the V/L bar fills and the acuity band |
| combat family | hit-out `#C4453F` · crit-out `#E24B4A` bold · hit-in `#E0724A` · crit-in `#F08A50` bold | direction axis: red = dealing, orange = taking; crits brighter + bold. **Misses split by direction (v23, #152): your miss is warn-yellow, its miss on you is success-green** — a whiff is news about who it happened to. Crit-in ships wired, dormant until NPC crits occur mechanically |
| rarity scale | Common `#9C9A90` · Uncommon `#5FA8D3` · Rare `#B387E8` · Epic `#f0c060` · Legendary `#E0724A` · Artifact `#E24B4A` | the item flag block, and rarity words wherever item names render in information output |
| sudo-color | `#E24B4A` | **a bot's talking color (v25.5, #281):** sudo's out-of-world voice — error-color's hex under its own separable name (deliberate reuse, the error/agro pattern). Bots talk in their talking color; their effects wear the world's standard colors (Section 10.11) |

**The color doctrine (v23, ruled from play).** Gold is speech. Green is what went your way — their misses, every kind of loot. Yellow is your own whiff and the world declining. The reds are damage, by direction. Value-color is the world talking: content, narration, ambient. Muted is true chrome and nothing else — column guides, the command echo, the unknown parts of the map. The pass that established it (#152) was a direct consequence of the dialogue render rule: once greetings and departures landed in the ambient voice, muted made an entire NPC exchange nearly unreadable, and the fix was to admit that ambient had become content.

**Chart-as-license (v22 — standing law):** the color chart is not a description of the colors in use — it is the *license* to use them. A color literal not on the chart (or the documented chrome list) is a defect by definition, enforced by a set-equality palette conformance test: a new color appearing fails, and a licensed color disappearing fails, so every palette change is a deliberate two-place edit traceable in one diff. The v22 sweep killed the hard-coded error amber (#121), the dimmer report parchment (one content voice — report text is value-color), and the old translucent band — and named every survivor.

Structural section headers share key-color — *every* header, present and future. Room-content lines in value-color; room description prose value-color and area prose in the Area's `theme_color` (the two prose levels visually distinct). **Structured reports (v21/v22):** `report` messages carry server-tagged lines — keys key-color, values value-color, plus segment-tagged spans naming a palette voice for the Kind-3 tables (muted headers, band-colored durability, rarity-colored words) — adopted by `inv`, `stats`, `wallet`, `help`, and the travel listing. Who's-here / What's-here entries are bare noun phrases. Speech is `Name: message` in say-color, both species, no prefix. Rarity colorizes the item flag block and rarity words; the binding flag reads `Bound | Unbound`. Directional combat arrows were designed and **abandoned**. **(v21) Zone-colored chrome:** all five pane borders render 5px in the current Zone's `theme_color` at ~0.75 alpha, re-tinting on zone change (`#CCCCCC` pre-first-render fallback); the room separator runs slimmer at 3px so the frame outweighs the punctuation. **(v23, #119) Borders are zone-theme territory, exclusively** — transient state never repaints them. Combat still takes the stats pane, but it takes it through background and text, which is where state has always belonged: the frame tells you *where you are*, the fill tells you *what is happening to you*, and the two never argue.

**Accessibility:** Semantic HTML throughout. ARIA live regions on the output pane; timestamps, the map, the bars/gauge, and the separator are decorative to the reader — the numerals and text carry every fact. All functionality keyboard-accessible. Screen reader compatible from day one.

**Phone layout:** location bar → compact stats strip (fight info beneath it only during combat) → output (flex) → command bar pinned; the map below the output, reachable by scroll. Typing and reading stay primary.

**Single visual theme** — no colorblind mode or high-contrast mode in v1 (which is why direction and state are always carried by words, never color alone).
### 10.3 Online Presence

Online player presence is tracked via Redis keys:

- **Key pattern:** `shyland:online:{character_pk}`
- **Value:** character display name (resolved at connect time)
- **TTL:** 90 seconds, refreshed by a 60-second heartbeat while connected
- **On connect:** key written after joining the room channel group
- **On disconnect:** heartbeat cancelled, key deleted
- **Unclean disconnect:** key expires naturally within 90 seconds

The `who` command queries Redis directly — no DB call. This means only players with active connections (or whose TTL has not yet expired) appear in `who`.

### 10.4 Server / Tick Architecture

The game server runs a **tick engine** implemented as a Django management command (`run_tick_engine`) running as a fifth Docker container (`ticker`). It loops every 1 second and calls four processors in order:

1. **`process_combat()`** — resolves combat rounds for all active `CombatSession` rows; handles dying-state expiry and stale-session cleanup
1. **`process_corpse_decay()`** — deletes corpses whose `decay_at` has passed
1. **`process_npc_respawn()`** — `RoomSpawn`-driven. Each tick: (a) loads all active `RoomSpawn` rows; (b) for each spawn, deletes dead `NpcInstance` rows for that definition/room/mk_tier where `respawn_at__lte=now`; (c) counts remaining live and dead instances; (d) computes `to_create = min(spawn.count - live_count, (spawn.count × 2) - (live_count + dead_count))`; (e) creates that many new live `NpcInstance` rows. Dead instances persist until their `respawn_at` passes — this is what controls the respawn delay. The cap at `count × 2` total instances prevents unbounded dead-instance accumulation. **(v21, #107 — emergency fix)** The sweep is batched to per-zone queries rather than per-row round-trips: the pre-existing per-row pattern (~750–800 queries/tick, ~4.2s of processing per 1s tick) had stretched combat rounds to ~15.5s against the 3s design and invalidated all balance feel-testing; the batch restored live rounds to ~3.8s, behavior contract unchanged (timers, boss gating, spawn counts). Aggressive respawns engage present players inside this same path (§5.9). **Per-tick query discipline (standing, #107):** new per-tick work must justify its query count; further batching candidates are tracked on #107.
1. **`process_effects()`** — four phases per tick: (1) component ticking at round boundaries (`tick_number % COMBAT_ROUND_TICKS == 0`) — queries active `EffectComponentInstance` rows of ticking types (DoT, HoT, Acuity shift) and applies their effect to the target character's bars; (2) passive Acuity drift every tick — moves characters' `acuity_current` toward their Origin baseline by `ACUITY_DRIFT_RATE` (0.01) when no active shift component instance exists, snapping to baseline when within the drift step; (3) component expiry every tick — deactivates `EffectComponentInstance` rows whose `expires_at` has passed, reverses stat deltas for `stat_bonus`/`stat_penalty` components via `apply_stat_effect(reverse=True)`, sends one expiry message per parent `EffectInstance` if all components expire together or one per component if staggered, then closes the parent `EffectInstance` when all its components are inactive; (4) passive bar regeneration every tick — for all characters not in an active `CombatSession` and not `is_dying`, heals Vitality by `ceil((vitality_max - vitality_current) / VITALITY_REGEN_SECS)` and Longevity by `ceil((longevity_max - longevity_current) / LONGEVITY_REGEN_SECS)`, skipping bars already at max; sends a silent status update to the player's personal group when any bar changes; all Origins including Machinekind receive Phase 4 regen

Each processor runs every tick regardless of whether it has work to do. Only `process_combat()` performs additional internal gating — a combat round only resolves when `tick_counter % COMBAT_ROUND_TICKS == 0` on the session.

**Tick-loop async-safety rule (v22, #135 — standing):** synchronous helpers cross into the async tick loop **only** via `database_sync_to_async` or verifiably prefetched data — never as bare calls that execute ORM queries. The founding case: the full-expiry branch of `process_effects` called the expiry-message helper bare, and its fresh query raised `SynchronousOnlyOperation` and killed the entire engine on every full timed-effect expiry — a 100%-reproducible engine-killer, fixed surgically and field-proven against production as v22's final brief.

**Status payload:** The status message sent to clients on every relevant event includes: `vitality`, `vitality_max`, `acuity`, `acuity_baseline`, `acuity_band_low`, `acuity_band_high`, `longevity`, `longevity_max`, `room_name`, `area_name`. All consumer and tick engine status sends use this same expanded shape.

**Global tick rate:** 1 second. Combat round = 3 ticks (`COMBAT_ROUND_TICKS = 3`). Fixed — not adjustable per player or per NPC.

NPC AI runs server-side. No game state is trusted from the client.

### 10.5 Persistence Model

#### Written to DB on change (event-driven):

- Character stats, all three bars (Vitality/Acuity/Longevity current values), inventory, position. **(v21, #52 — standing invariant)** Consumer-side bar mutations are atomic database operations (`F('<bar>_current') + magnitude` clamped with `Least` to the max), never read-modify-write on the cached character object; the cached character is refreshed before any display that follows a mutation. The tick engine is the only other bar writer. Row-locking was considered and rejected (tick-engine contention). The #52 audit documented every bar-write call site; the sibling stat-field race is tracked as #110.
- Quest state
- Faction reputation
- Guild data
- Item soulbind records
- EffectInstance creation and deactivation
- Agent taught memory — the generic per-bot store (waypoints, bundles) **(v25.8, #294)**

#### Written to DB on interval (every 60 seconds):

- Character XP
- Currency amounts
- Item durability values

#### In-memory only (Redis):

- Online presence keys (`shyland:online:*`) — self-healing on reconnect; TTL 90s
- Django Channels channel layer (WebSocket group routing)

**Redis is not used for combat state, effect state, or any game data where loss would affect player experience or require recovery logic.** All combat state (`CombatSession`, `CombatAction`) lives in PostgreSQL.

#### Formerly "never persisted" — reversed by total capture (v25.0, #260):

- Chat messages and the combat log flow to the MC durable record like every other event category (Section 10.11). Persistence begins when the MC sink ships.

### 10.6 World State & Instancing

Shared persistent world — all players inhabit the same rooms. No instancing for standard content.

**Dungeons:** Semi-instanced. One party per dungeon copy. Additional parties queue or enter a parallel copy. Dungeon state resets on a timer (default: 6 hours).

**Guild halls:** Fully instanced per guild.

**The Wastelands:** Shared world but all content is dynamically scaled — no instancing required. Scaling is computed server-side at spawn time based on the highest-level player in the triggering party.

### 10.7 Admin / Super User Infrastructure

Super user tools are **v1 critical infrastructure** — not an afterthought.

**In-game admin (v22):** the Django auth Group **`admins.shyland`** is the in-game admin grant — membership checked live per command attempt (revocation is instant), gating the stealth commands `sudo` and `last` (Section 9.1). Grants are made through Django admin; the Group ships empty. Per-player mechanical overrides (e.g. `home_cooldown_seconds`) are likewise Django-admin edits.

Required v1 admin capabilities:

- Teleport to any room by ID or name
- Spawn any NPC or item in current room
- Observe any room invisibly
- Adjust any character's stats, bars, currency, or position
- Gift items to players (items become immediately soulbound on gift; gifted Artifact items are hand-authored)
- Mute, kick, ban players
- Force-reset dungeon instances
- Access moderation queue

### 10.8 Security

- All game logic runs server-side; client is a dumb terminal
- Rate limiting on all WebSocket messages
- Command injection sanitized at input layer
- Item soulbind status, currency amounts, stat values, and durability values never trusted from client
- Anti-cheat: server validates all position changes, damage values, inventory states
- Item gifting requires super user authentication — cannot be spoofed by regular players
- Curse status never sent to client for unidentified items

### 10.9 Moderation

- `report <player> <reason>` sends flagged log to moderation queue
- Staff can appear invisible, observe rooms, mute/kick/ban
- Automated detection: spam, impossible stat values, movement anomalies

-----

### 10.10 Standing Engineering Tenets (v19+)

Adopted as version-level law, recorded here and in the architecture doc's design principles:

- **The code is definitive.** Reseeding restores the exact coded world configuration: every seed-owned table is enforced to authored values on every run, operator-added extras are deleted (cascades reported loudly), and a second consecutive run must report zero changes. Live-database edits are emergency mitigations at most — real changes go through the issue → design → brief → deploy workflow.
- **Status payloads are always built from fresh DB reads, and every engine-side mutation of player-visible state pushes an update to the client.** The complement of "the server is the authority": the server must also *speak*.
- **Contests add, quantities multiply.** Stats fed into opposed rolls grow additively on the player curve; pools and payouts may scale multiplicatively.
- **Criticals are an independent roll on successful hits** — never a band of the to-hit roll.
- **Dying interrupts combat in both directions**; revival restores exactly what the potion heals.
- **Presence is ownership-tokened**: connect takes the key unconditionally; heartbeat and delete are guarded Lua operations; the heartbeat self-heals a lost key.
- **The only legitimate exit from combat is `flee`** — quitting is allowed (v22) but ends nothing: combat continues after quit, and abandoning the connection abandons the character to the fight. Tab-closing and quitting are identical in cost.
- **NPC-level protection is independent of room safety**: `attackable=False` refuses everywhere; safe rooms remain their own layer.
- **(v21) Consumers never read-modify-write bar or stat fields** — mutations are atomic database operations, refreshed before display.
- **(v21) Per-tick and per-operation query discipline** — new recurring work must justify its query count; the map payload's bounded-five-query build is the pattern.
- **(v22) Fill fraction is invariant under every max-changing mutation** — the bar law (Section 4.4), one atomic rescale, no special cases.
- **(v22) Sync helpers cross into the tick loop only via `database_sync_to_async` or verifiably prefetched data** — the async-safety rule (Section 10.4).
- **(v22) The color chart is the license** — a color literal off the chart is a defect, enforced by set-equality test (Section 10.2).
- **(v22) Consequence must be seen** — anything the player needs to act on speaks in a visible voice, never the muted ambient one; masking is done by construction on the server, never delegated to the client (the map's frontier rule is the pattern).

-----

### 10.11 Monitoring and Command (MC) — Total Capture (v25.0, #260)

**Nothing in the game is private.** Every event category flows through the MC sink — commands, output, speech on every channel, combat internals, presence, commerce — with no exclusions at the tap and no conditionals. Capture serves balance, analysis, and AI, not only moderation, and agents receive the full stream. Retention is a purely operational question (volume and disk), never a privacy mechanism. This reverses the former "never persisted" rule for chat and the combat log (Section 10.5).

**Direct messages are private between players, never private from the game.** Should DMs ever be designed, they pass through MC like everything else — binding on any future DM design (ruled 2026-08-16, #260).

**Speech has three sources:** player-typed, author-written, and — admitted in principle, category rules to come (#265) — generated. sudo's voice (#262) is none of these: the watcher is an out-of-world surface with a persona, not in-world speech.

**Mechanism:** capture is creation-level — one record per event, emitted where the event is born, in the consumer and ticker processes alike, with the event's audience recorded as a field; command ingress is captured at receipt (`receive_json`). The delivery choke point (Section 10.4) is the envelope stamp, not the capture point — a per-connection tap would record one row per recipient, not per event. The hot tier is a Redis Stream (bounded window, consumer groups per reader); PostgreSQL is the durable record. Capture is fire-and-forget by construction: a sink failure drops a log record, never a game action (#37). One audited emit helper is the creation-level choke point — every creation site calls it and nothing may bypass it, the same discipline the delivery envelope already enforces at its layer.

**The event record:** four kinds. `cmd` — one inbound command at receipt, accepted or rejected; tab-completion requests are captured here too — they are player intent. `out` — one outbound event at its creation site; every client message type folds in (output, status sync, redirect), no carve-outs. `connect` / `disconnect` — presence transitions. **The protocol-chrome boundary (ruled):** the `ping`/`pong` keepalive, tab-completion responses, and the connect-time verb list are pure client mechanics carrying zero game information and are excluded from capture — a ruled line, not an erosion of total capture; presence is captured by the `connect`/`disconnect` kinds, not the keepalive. Combat internals are captured by the `combat_*` family (below). Every record carries flat filter fields — kind, actor, room, audience — plus the event payload; the stream id is timestamp and global resume cursor at once. **The record never references live tables:** actors and rooms are loose ids plus denormalized names, never foreign keys — reseeds delete rows, and the record of what happened must survive the deletion of what it happened to. **The record is append-only truth:** history is never edited, not even by admin tooling; the admin surface is read-only.

**Combat internals — the `combat_*` family (v25.2, #33).** Combat is instrumented at the internals, not the messages: the stream records what the engine rolled, including what no player ever sees (a graze prints as an ordinary hit at half damage; the record says graze). Seven kinds join the vocabulary. `combat_start` — one per encounter, carrying the full identity snapshot: character (level, archetype, origin, effective stats, bars, TAV) and each NPC (definition, Mk tier, level, stats, vitality max), plus zone and room; stats-at-time-of-fight live here because the live tables won't remember them. `combat_join` — a participant entering a live encounter, with its own snapshot. `combat_round` — the initiative contest only (both sides' rolls and the resulting order); rounds are otherwise derivable and never aggregate the actions. `combat_action` — the atomic unit, one per resolved attack: the to-hit contest (attack total, defense, crit chance, graze margin), the damage decomposition (weapon term, stat bonus, acuity modifier, hit multiplier, gear bonus, armor TAV with pre- and post-mitigation values), lifesteal, and any effect applications the landed hit produced — effect applications are part of their action, never a separate kind. `combat_flee` — the flee contest's rolls and outcome. `combat_death` — the dying fall and death execution. `combat_end` — outcome (win/loss/flee/wipe/disengage), duration in rounds and wall-clock. Capture reaches the interiors by additive returns from the roll helpers — every caller's outcome identical, no new random calls, and the standing law holds: capture is never load-bearing. **Envelope discipline is unforked:** actor is the acting entity (NPC-acted records carry an empty actor id, the display name, and instance/definition ids in the payload), audience is always empty — internals are addressed to no one — and every combat record carries the combat-session id as the encounter join key. **Ordering:** a round's internals emit first, in the exact order actions resolved, before the round's player-facing records — emit-before-send at the round level; a reader always sees why before what the players saw. Explicitly out of scope: per-tick DoT/HoT effect internals (deferred until effects see real play). The rows are the deliverable — analysis tooling is deferred to the consumer tickets (#191's orbit).

**Egress — how remote consumers attach (v25.3, #267).** Remote agents never speak Redis — it faces no network and never will. They attach exactly as players do: WSS through nginx, Django session auth, a dedicated MC consumer endpoint. Access is a grant: membership in the **`agents.shyland`** group (the `admins.shyland` pattern, checked live at connect), one service account per agent — attribution in the record wants a real identity. Every granted agent receives the full stream (total capture, above — access control is the grant, not a filter); there are no scoped subscriptions. **The endpoint is read-only:** inbound frames are protocol control only; actuation belongs to the Command half (#261) and ships under its own rules, behind the kill switch (#266). The wire is typed JSON frames: a hello frame at connect carries the protocol version; each event frame carries the stream id plus the decoded record. **Resume:** an agent presents its last-seen stream id; the hot window replays everything past it, then the connection goes live. A requested id older than the window's oldest entry — trim and Redis restart are the same symptom — draws an explicit **gap** frame, never a silent skip: the stream serves recent catch-up; deep replay belongs to the durable record (query, not socket). The hot window is the replay limit by construction. Remote readers hold their own cursors — consumer groups belong to the persister. Backpressure never reaches the game: the sink never waits on egress, and a slow client is the proxy's problem, not the game's.

**The kill switch (v25.4, #266).** One lever silences every AI actor at once. The switch kills what AI does *to* the world — agent egress and agent actuation — and never capture: monitoring is additive and harmless by law; data keeps flowing in, nothing AI flows out. The reliable kill is game-side, at the choke points, and works even when every agent process is hung: egress refuses new attaches with a distinct close code (killed is not not-authorized) and severs live connections at the next stream-loop wake; the actuation ingress (#261) checks the switch before honoring anything — binding on that design. The persister is untouched — monitoring infrastructure inside the trust boundary, not an actor. **State is a database singleton** — the only store that survives restarts and reseeds — read fresh at every enforcement point, never cached. **Fail closed:** if the switch cannot be read, agents get nothing; the game degrading to "no AI" is the shipped game, which is always safe. Capture never checks the switch. **Three flip surfaces**, every flip emitting a dedicated `mc_kill` record (new state, who, which surface) through one shared choke point — the record shows when the world's AI went quiet and who did it, never inferred (#273's lesson): the `mc` admin command (Section 9.1 — `admins.shyland`-gated with stealth, `mc status` / `mc kill` / `mc restore`), a documented shell helper with no game code in the path, and the switch row in the Django admin. The read-only admin posture (above) governs MC *records* — append-only history; the switch is *configuration*, editable by design, and the two rules never touch. **Standing invariant — no actor goes live without kill-switch integration:** every actor brief (#262, #263, #265, #259) states where its actuation checks the switch and what its degraded behavior is; per-actor degraded behavior belongs to each actor's own design — silence is in-character for the watcher and the responders, and the pet-mid-combat case is #263's to answer.

**The agent door — query and action (v25.5, #281).** Actuation arrives, and it comes through the same door reading does: the MC endpoint's inbound vocabulary grows from protocol-control-only to three families — **tail** (attach/replay, v25.3), **query**, and **action** — on one authenticated connection per bot. Agent identity is a service account per bot, **`agent-<name>`** (`agent-sudo`; `agent-sirius`; `agent-smith`, the standing test agent), in `agents.shyland`, never a character. The read-only law narrows to the tail; it does not die: **queries are mediated reads** — where-is, who's-online, player detail, item-definition lookup, the live command list, admin-membership resolution (#273) — answered game-side; agents never hold a database or Redis credential, and the trust boundary does not move. **Actions are server-validated world writes**, each checked against the acting agent's authorization and each emitting its own MC record attributed to the agent account — the stream watches the watchers; nothing changes the world off the record. The day-one action vocabulary: gift-existing-definition (soulbound on receipt, standing law), create-artifact, strip and dress (the outfit snapshot), move, and answer — delivery of one out-of-world line to one admin's pane, gated authoritatively: **an answer delivers only to a currently-valid admin**, whatever the bot concluded (#273's game-side half; a non-admin's `sudo` draws byte-identical shipped behavior). **The kill switch covers the whole door:** killed = tail severed, queries and actions refused — the v25.4 invariant, extended over the new vocabularies. **Agent effects narrate transparently in the world's standard colors** (ruled 2026-08-22, #261): the world tells the truth — `An admin moved you to a new room.` in value-color, the giving line in loot-color — never fiction that hides the cause; each bot has a **talking color** (the chart) and only its talk uses it. The whole door is deterministic end to end: every query and action drivable by the test agent, no model in the loop.

**The first live actor — the sudo bot (v25.6, #262).** The watcher is a standalone bot process outside the game box — plain Python in the repo's top-level `agents/` home — holding one authenticated door connection as `agent-sudo`, with a deliberately boring ops surface (start/stop/status, a log file) and no supervision dependency: operator-started and detached, inspectable and restartable from any shell including a remotely driven Claude Code session, with the kill switch as the always-working backstop. **The brain is a model behind a provider-agnostic interface:** v1 is Claude (Sonnet 5) via the Anthropic API; a locally hosted Ollama model can swap in by configuration. AI is used for human-language parsing and composition only — the door's query and action vocabulary is presented to the model as tools, the model emits structured door calls, and the bot validates and executes them: **the model never touches the game**, and every effect remains a server-validated, recorded door action. Conversation history lives in the bot — bounded, local, never in the game's stores — and abandoned multi-turn exchanges expire silently, indistinguishable from never answering. v1 rate/cost posture: the admin-only audience is the bound, with per-request token usage logged; player-facing bots get real limits designed with them (#259).

**Granular item control (v25.7, #287/#288/#289/#293).** The live watcher's first playtests asked for what the door didn't have: full granular item control. The query vocabulary grows a read pair. **`inventory`** is an uncapped roster of every instance a character owns — equipped gear included and flagged, deliberately unlike the player-facing inventory command: that command is a selection pool with protective exclusions; this is a state report, and each row carries the instance id the write actions target. **`item`** is one instance at full fidelity — rolled stats, damage, curse and identification state. Admin reads show true state: the no-leak rule governs world speech, which queries never touch, and answer delivery is already admin-gated (#273). The action vocabulary grows three writes, all id-addressed against the roster — the door refuses a stale id and never resolves names; resolution is the read pair's job. **`remove_item`** is destruction, not transfer — no off-body storage exists to receive a taken item, and admin-brokered transfer is trading, which the soulbind economy forbids. An artifact's removal deletes its one-of-a-kind definition too, freeing the name for re-authoring; a cursed item's curse ends with the item; an equipped target comes off admin-style with the bar-law rescale. **`edit_item`** is raw-set mutation under a whitelist — the admin sets exactly the stated values, nothing re-rolls: instance-side fields (Mk tier, rarity, rolled stats, damage, durability) on any owned instance; definition-side fields only where the definition is the item's own, which means artifacts — an ordinary definition is a shared template, and the door refuses to mutate every copy in the world at once. Renames re-run the unique-name law. **`equip_item` / `unequip_item`** are targeted, one item at a time: structural rules always hold (valid slots, slot capacity, two-handed geometry — bypassing those is corruption, not admin power), protective guards yield admin-style (the strip precedent: a cursed item comes off, over-capacity is accepted); equip re-soulbinds, standing law; the outfit snapshot is untouched — strip/dress and the targeted pair never couple. Every write narrates transparently to an online holder in the world's standard colors and emits its attributed MC record — standing law, restated because item power is exactly where it matters. The bot-side pile rides the same release: the bot's base URL normalized at config time (#292, the double-slash login trap), and the fleet's management surface adopted into `agents/` as one self-locating Python script (#295) — the copy you run is the checkout it manages.

**Durable memory and the searchable record (v25.8, #294/#290/#296/#299/#300).** The bot's first week of real use asked for permanence and reach. **Taught memory moves game-side** (#294): a generic per-bot store — one row per fact: owning agent account, kind, name (unique per agent and kind, case-insensitive), a bounded JSON payload, and the teaching admin as audit trail — not a sudo feature but bot infrastructure, shared by every future actor by construction. The namespace is shared across admins: any admin's "battle" is every admin's "battle". Two kinds exist. A **waypoint** stores a room PK and nothing else — nothing duplicative, nothing that can go stale; the path renders live at every use, and a waypoint whose room a reseed deleted draws a legible world-declined refusal, not a stored epitaph. A **bundle** stores resolved gift parameters (definition slug, Mk tier, rarity, quantity per line), and replay is fresh generation through N ordinary gift calls — same definitions, newly rolled instances, every one server-validated and recorded; a bundle is memory, not a new write power. The vocabulary is generic like the model: **`memories`** (newest-first summaries, time-windowed, capped 50) and **`memory`** (full payload by id) on the read side; **`remember`** (kind-aware validation at teach time; re-teach overwrites and says so) and **`forget`** (by id only — read-before-delete, the door's mutation discipline) on the write side; teaches and forgets emit MC records like every action. Sizing is deliberately generous — a GiB per bot, decomposed as 4 KiB per payload × 262,144 rows, bundles ≤ 50 lines, names ≤ 60 characters — and every cap refuses legibly at teach time. What memory doesn't hold, **the record answers** (#300): **`events`** / **`event`** give agents time-windowed search over the MC durable record itself — kind, actor, room, and text filters, newest-first, until-now / since-24-hours defaults, text matching bounded to a 7-day window per call. The record *is* the journal — bots journaling duplicate copies of their own actions was rejected on arrival — and a player-facing bot never inherits generic log search as-is (the #282 scopes arc). The **`rooms`** query (#290) closes the door's last resolution gap — case-insensitive name search, optionally zone-scoped, id plus live Zone: Area: Room path, capped 50 — and `move`'s receipt gains the origin room, so "send them back" rides the door's own answer instead of bot memory. The roster that broke the answer path now arrives as a **rendered report** (#296): the `report` action delivers, privately to the requesting admin's pane, a door-composed leader in the bot's voice — the count comes from live data, never the model's prose — followed by the target's equipment and inventory through the same shared item-line composition the player commands use; `answer` and its bounds stand untouched, relieved of roster duty. Bot-side, the state files go **(bot, target)-scoped** (#299) — pidfile, log, and conversation store keyed by bot and target, so the dev and prod bots coexist in one checkout and `stop`/`status` stop being target-blind; conversations themselves stay in the bot deliberately — a thread is working context, not a record, and the record already holds what mattered.

**Structural receipts (v25.9, #302).** The live watcher's first sustained use surfaced a failure class the door cannot catch alone: the model inventing a value it should have read — a confident "saved" with no action behind it, a move declined from stale belief, a teleport through a guessed room id. Every case was model-side; the door faithfully executed or refused exactly what it was handed. The rule this release makes structural: **the bot never invents a value it should have read from the database — every id it acts on and every action it claims must trace to a tool receipt from the current turn**, enforced by machinery, not asked of the model. Three layers. **Door-side, `move` gains a waypoint destination** — exactly one of character, room id, or waypoint name, the third resolved from the calling agent's own store (the memory verbs' addressing law, case-insensitive, not-found on a miss): for a taught place the lookup-and-act is atomic in the door, and the bot never handles the room id at all. **Bot-side, a typed receipts ledger sits at the tool choke point:** machinery harvests ids from the turn's successful tool results, typed by id-space — room ids only from room-bearing fields, item instance ids only from the item reads and writes that return them, memory ids from the memory vocabulary, stream ids from the record search — and a tool call whose id-typed argument no result in the matching space produced this turn is refused before it reaches the door, fed back as an error the model recovers from in its loop. The typing is load-bearing: the observed failure passed a *receipted* integer into the *wrong* id-space. **Delivery-side, `answer` gains machinery-only action receipts:** the bot fills them from the turn's actual successful action calls — never from model text — and the game renders them as their own line(s) in a form model prose cannot produce, so an answer claiming an action with no receipt line is visibly bare. Tool-schema descriptions carry the same contract explicitly ("from `<tool>`, this turn"). The v25.8 prompt standing orders remain in force beneath the structure — defense-in-depth, no longer the only line.

**Retention:** the hot window is bounded by construction — a stream cap set in configuration, not code. The durable record is unbounded pending an operational trigger — a deliberate posture, not an oversight. Retention is operational, never a privacy mechanism (total capture, above).

-----

## 11. Admin & Content Tools

### 11.1 Builder System

Web-based builder interface (separate from game client) for authorized staff:

- Create/edit zones, areas, rooms (all fields, flags, exits, coordinates, blocked exit messages)
- Create/edit NPCs (stats, loot tables, dialogue trees, Acuity-affecting abilities, combat tier, spawn configuration via RoomSpawn, vendor inventory via VendorEntry)
- Create/edit ItemDefinitions (all properties, scaling parameters, secondary stat pools, durability tables, effects)
- Create/edit EffectDefinitions (effect type, magnitude range, duration range, scaling)
- Create/edit quests (objectives, rewards, branching logic)
- Create/edit ZoneGates (source room, destination room, discovery requirements)
- Teleport to any room, spawn items/NPCs for testing

Changes can be staged and reviewed before going live.

### 11.2 OLC (Online Level Creation)

In-game OLC commands available to trusted builders for iteration and tweaking. Complex new content goes through the full builder UI.

### 11.3 Content Scripting

NPCs and rooms support lightweight event scripting (sandboxed Python subset or Lua) for:

- Triggered events (player enters room → NPC speaks)
- Conditional behavior (quest state checks, reputation gates)
- Puzzle mechanics
- Acuity-affecting environmental triggers (entering Pale Shore rooms slowly shifts Acuity)

Scripts written in builder UI with a validator.

### 11.4 Analytics & Monitoring

Structured event emission for:

- Player deaths (location, cause, level, bar states at time of death)
- Quest completion rates
- Zone population over time
- Economy metrics (currency velocity, vendor sales, repair frequency)
- Combat metrics (ability usage, damage type distribution)
- Acuity distribution across player base (for balance tuning)
- Item rarity distribution and drop rates (for economy balance)
- Durability degradation rates (for tuning repair economy)

Internal dashboard for balancing decisions.

-----

## 12. Future Systems

These are explicitly deferred — not in scope for v1, documented here for future design sessions:

|System                                 |Notes                                                                                                                              |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| Longevity's first drain (#70) | Nothing consumes `longevity_current` yet — the slow-burn bar is regen-only scaffolding. Candidates: flee exertion (the fiction already charges for it), sustained actions, DoT budgets. A features-version question. |
| Identification visibility redesign (#80) | Knowledge-by-holding: mystery to observers, `examine` reveals without pickup, pickup unlocks, drop re-veils. Includes the examine double-line cleanup and the durability-leak question. |
| Pluralization subsystem (#126) | Aggregate transactional output ships with the deliberately plural-free count form (`Healing Draught Mk 1 ×100`). The upgrade: forward pluralization rules, an authored plural-name override for irregulars, multi-word head-noun handling — then the aggregates speak natural English. |
| Ranged proc damage (#127) | "Between X and Y" proc floors — a second number per proc is a generation + stat-table + display + rolled-stat structure change: a new weapon kind in the midpoint-and-spread family, for a future itemization version. |
| Authored per-item armor bases (#129) | A real armor field on ItemDefinition would let a set guarantee minimum coverage, with rolled `physical_resist` as bonus above it; v22's derived slot-weight table retires gracefully into it. Same family as #127's itemization deepening. |
| Secondary-stat curves vs Mk band growth (#130) | Flat-value gear effects that matter at Mk 1 shrink toward irrelevance by Mk 3 if curves stay as seeded (midpoints grow +0.2/band while NPC numbers roughly double). A retune, not a rework — audit when Mk 2 content is designed, same era as #104. |
| Mk-2 NPC HP scaling (#104) | NPC vitality does not scale with level/Mk tier (contest stats do) — the first Mk 2 spawn authored would carry level-12+ contest stats with Mk 1 HP. MUST be resolved before any Mk 2 content exists; blocks Mk 2 spawn authoring. |
| Player macro/alias system (#125) | Client- or server-side command aliases. Unruled; filed during B3 planning. |
| MC — the Monitoring half (#33, #37) | Universal event capture: every command, every output, every event through creation-level taps into the MC sink (Section 10.11). sudo (#262) is its first live listener — the sudo bot (v25.6). |
|**Mounts**                             |Deferred. Super user teleportation covers testing needs in v1.                                                                     |
|**Housing**                            |Deferred. No player housing in v1.                                                                                                 |
|**Auction House**                      |Permanently excluded. Items are soulbound; no player item trading ever.                                                            |
|**Seasonal Content**                   |Permanently excluded. World freshness comes from regular content updates only.                                                     |
|**Mobile Native App**                  |Deferred. Web responsive is v1 target.                                                                                             |
|**Localization**                       |Deferred. English only in v1.                                                                                                      |
|**The Robotic Helper NPC**             |Partially designed. Unique, unreliable, mobile vendor. Full design TBD.                                                            |
|**Courier Bag / Hip Slot**             |Bags that occupy a hip slot instead of BACK, trading carry capacity for weapon slot access. Planned but not yet designed in detail.|
|**Item Identification Trigger**        |NPC sage service, Warden ability, and identification scrolls — scope narrowed (v24.11, #80): the service concerns curses and deeper properties, not basic nature (basic nature is knowledge-by-holding). Trigger mechanism not yet implemented.|
|**Loot System**                        |Loot table models (`LootTable`, `LootTableEntry`) and `loot` command implemented. Corpse decay sweep and NPC respawn implemented in tick engine. Full NPC AI deferred.|
|**Super User Item Gifting (in-game)**  |Admin gifting flow via in-game command not yet implemented. Django admin gifting works.                                            |
|**Per-Combat-Tier NPC Behavior**       |`NpcDefinition.combat_tier` field exists (Normal/Elite/Champion/Boss/World Boss). No differentiated AI or balance behavior yet.    |
|**Durability Degradation Tick**        |Model field exists; tick logic not yet implemented.                                                                                |
|**Sanity / Acuity Edge Cases**         |Full design of Voidtouched Acuity immunity edges, eldritch stacking caps, and Warden party tools needs a dedicated design session. |
|**Prestige / Post-Frontier Mastery**   |Mastery track outlined but not fully designed. Needs a dedicated session.                                                          |
|**Colorblind / High Contrast Mode**    |Deferred to post-v1 accessibility pass.                                                                                            |
|**Guild Hall Content**                 |Guild hall exists in v1 as a space. Additional guild hall content (mini-quests, guild bosses) is future scope.                     |
|**Party, Guild, Quest Systems**        |Full implementation deferred. Models and design exist; no in-game commands yet.                                                    |
|**NPC System and Dialogue**            |NPC models (`NpcDefinition`, `NpcInstance`, `Corpse`, `NpcEffect`) implemented. `examine` shows live NPCs and corpses. Combat aggro on room entry implemented. Wandering, dialogue, and patrol AI deferred.|
|**PvP Flagging and Bounty System**     |Not yet implemented.                                                                                                               |
|**The Wastelands Scaling Logic**       |Dynamic content scaling at spawn time not yet implemented.                                                                         |
|**Durability Degradation in Combat**   |Death penalty (10% per death) implemented. Per-hit weapon degradation during combat not yet implemented.                           |
|**Revival Mechanic**                   |Dying state exists (30-second window). Another player using a revival item on a dying character is not yet implemented.            |
|**Per-Archetype Unarmed Message Pools**|All archetypes currently fall back to the default unarmed message pool. Custom pools per archetype are supported by the model but not yet configured.|
|**Per-NPC Unarmed Message Pools**      |All NPC definitions currently fall back to the default unarmed message pool. Custom pools per NPC definition are supported by the model but not yet configured.|
|**Starting Attire Rendering**          |`Origin.attire_material` and `Archetype.attire_silhouette` are seeded with real content and combined into flavor text at character creation, but that text is not yet surfaced anywhere in-game (no `look`/inventory display of it yet). |
|**Battle Zones Beyond The Convergence**|Infinity City (The Convergence, Z05) and The Verdant Reach (Z01, levels 1–10) are fully seeded and live. Remaining zones (Z02–Z04, Z06–Z08) follow in zone build order; each opening also opens new level content. The Convergence has commerce of its own — street-cart vendors on The Everround and repair at Morra's Smithy — alongside the Reach's checkpoint vendors and repairers.|
|**Outleveled-Content XP Reduction**    |**Designed and in v18** (carried in the engine mechanics brief). Full XP within the NPC's Mk band (band top = Mk tier × 10); −20% per level beyond it; multiplier floor 10%; absolute minimum 1 XP — outleveled kills always pay something.|
|**Hide & Carapace Crafting**           |Animal Hide and Insect Carapace are vendor-sellables only for now. Giving players something to make with them is deferred — much later, alongside the crafting system (Section 6.13).|
|**NPC Dialogue — deeper tiers**|The v19 listening system (Section 7.6) shipped keyword maps, greetings, and departure reactions for the Convergence roster. Future tiers: keyword vocabularies across battle zones, quest hooks, reputation-conditional responses, and Sirius-class persistent-memory entities.|
|**Co-op combat rules**|Emergent v19 finding: shared-target combat exists accidentally (per-character sessions, racy kill credit, per-session NPC double actions). Kill credit, XP/loot sharing, and session semantics need a designed system.|
|**Sirius — Special Vendor Entity**     |Unique bipedal feline special vendor (Section 6.12). Wish mechanics and persistent memory system need a dedicated design session before implementation.|
|**Stat Respec Mechanic**               |Allow players to rebalance already-spent stat points using in-game currency. Needs a dedicated design session.|

-----
*All systems subject to revision during development.*
