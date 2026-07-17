# Shyland — Game Design Document

**Version 21.0 — Closed**

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

**The Convergence (Z05)** is the game's social hub — a permanent sanctuary zone where PvP is disabled, vendors of all types exist, and players from all backgrounds congregate. It is the point where all universes overlap and stillness holds. It is also the default logout and recall destination. The starting area within The Convergence is **Infinity City** — see Section 2.9.

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

**The payload:** server-computed on connect and on every room change — the current room plus the visited members of its MapFrag, each with per-zone coordinates, per-direction exit status (`open` to a drawn room, `unexplored` stub, `boundary` tick), and up/down presence. The client is dumb: it renders exactly what it is sent.

**The client map:** a fixed **300×300px square at the bottom of the right pane** — rooms as circles, exits as lines, **north up**, a 9×9-cell window centered on the current room (no zoom), the current room highlighted, unexplored exits as short dashed stubs, boundaries as dashed stubs with a terminal tick, U/D letter badges on rooms with vertical exits. `aria-hidden` — the map adds no information not already present in text, and the text remains the accessible source of truth.

**Design-tool rule:** visual MapFrag diagrams (the same node-and-line rendering) are **required** for all world-layout design work — the map the game draws is the map the designers draw first.
### 2.6 Travel & Navigation

Players move using directional commands: `north`, `south`, `east`, `west`, `up`, `down` (and abbreviations: `n`, `s`, `e`, `w`, `u`, `d`). Named exits use the exit name directly (e.g., `enter portal`).

**Movement costs no action economy in normal exploration.** Combat changes this (see Section 5).

Special travel options:

- **Recall scroll** — teleports player to their bound recall point (default: The Convergence)
- **The Obelisk Network** — the game's fast-travel system: obelisk rooms are travel sources; checkpoints and obelisks are destinations, revealed per-character by visiting them. Free, global, and command-driven (`travel`). Full design in Section 2.11.
- **Zone gates** — the sealed genre-zone gates on the Convergence ring are authored prose (opened per zone as its content ships — the Verdant gate opened in v18). The `ZoneGate` model was superseded and deleted in v18 (Brief 2, migration 0019); the Obelisk Network above is the game's fast-travel system.

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

The starting room and default recall destination. At its center stands **the Obelisk** — a dark, smooth monolith with as many facets as there are universes, each face ground to a perfect plane that catches light differently. At the Obelisk's heart, suspended inside the stone, is a small sphere that glows white. Steadily. Without flickering. It simply is.

The Obelisk serves as an information point for new players. It speaks in as few words as possible, always the best ones.

#### Convergence Park

A rectangular park (9 rooms wide, 7 rooms tall on the coordinate grid) surrounding the Obelisk. The park is tended but not controlled — nature was here first and the city has respected that. Not all park rooms are navigable paths. Four paths wind outward from the Obelisk to the ring street:

| Path | Direction | Material | Rooms |
|---|---|---|---|
| Wisteria Walk | North | Pale grey stone + wisteria trellises | 4 |
| Bamboo Run | East | Crushed amber gravel + bamboo stands | 3 |
| Basalt Way | South | Dark basalt slabs + flowering moss | 5 |
| Fern Boards | West | Dark timber boardwalk + ferns | 4 |

Each path has a continuous sensory identity maintained through all its rooms. Non-path park rooms are not navigable; rooms adjacent to lawn areas have custom `no_exit_*_msg` text directing players to stay on the paths.

#### The Ring Street

A 35-room ring street surrounds the park, approximating a circle in the square-room coordinate system. The ring connects to each path at its cardinal intersection. Walking the ring clockwise from north, players encounter:

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

- **Animals drop no items** — a bear carrying a sword makes no sense. Animals give XP plus a dice-roll chance at a generic **Animal Hide**; cave insects the same with **Insect Carapace**. One ItemDefinition each for now — pure vendor-sellables. Crafting uses for hides and carapaces come much later (see Section 12).
- **Villagers drop money and gear** — Common trash, the zone's baseline loot source.
- **Pre-boss rarity is deliberately unimpressive.** Everything before a boss is Mk 1 with at most a few points in a single stat — Common with occasional Uncommon. Nothing fancier ever rolls from trash.
- **Boss drop category rotation:** weapon → armor → accessory, looping boss by boss through the zone. ("Accessory" is the real item-type word — see Section 3.6; "trinket" is a conversational alias only and never appears in code or data.) Cave 2 = weapon, Cave 3 = armor, Cave 4 = accessory; the mountain caves repeat the cycle at higher rarity: Cave 5 = weapon, Cave 6 = armor, Cave 7 = accessory. Accessories fill the NECK and RING (×2) slots. Loot mechanism (settled at brief time): guaranteed-group entries on loot tables — each labeled group yields exactly one weighted pick per kill, so a boss always drops exactly one item from its rotation category, with rarity floors expressed through the existing rarity weights; ungrouped entries still roll independently for bonus drops. A player who clears all six bosses touches every equipment category twice — once in cheap versions, once in the good stuff. The "full set of the zone's best" is therefore a concrete checklist: seven armor slots, the weapon slots, one neck, two rings.
- **Boss rarity ladder:** Caves 2–4 guarantee **Uncommon** (visibly better than anything looted off a villager, but modest). Caves 5–6 guarantee **Rare**. Cave 7 guarantees **Epic**. **Legendary never drops in the Reach** — the first one a player ever sees should mean something.
- **The full-set hunt:** a player who clears the mountains, with some replays, should walk out wearing a complete set of the zone's best. Missing pieces are farmable on replay, at reduced XP since the player has outleveled the content. The rule (settled in v18): full XP while within the NPC's Mk level band (band top = Mk tier × 10); −20% per character level beyond the band top; floored at 10% of base and never less than 1 XP. Outleveled content always pays something — helping a friend or farming a missing Epic never feels like nothing.
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

- **Obelisks are sources and destinations.** To travel, a player must be standing in an obelisk room. Every zone-end obelisk is a network node, as is the Obelisk at the Heart of the Convergence.
- **Checkpoints are destinations only.** A player can arrive at a checkpoint but never depart from one. From a checkpoint, you walk — the zone content stays meaningful.
- **The network is global, never zone-scoped.** From any obelisk, a player can travel to any checkpoint or obelisk they have revealed — no zone boundaries, no special-casing the Convergence. Cross-battle-zone travel is allowed by design (a high-level player warping to a beginner-zone checkpoint to help a friend is a feature, not an exploit). One flat rule — *destination revealed? travel permitted* — keeps the implementation simple: a single per-character set of revealed nodes and one membership check.

The Convergence Obelisk is not mechanically special — it is simply the first node every character reveals, at minute zero. Special in lore, ordinary in code.

#### Revelation

A node becomes an available destination the moment the player sees its room. **Revelation is per-character and permanent** — once revealed, a node never un-reveals, and revealed nodes are never shared between players (your friend still has to reach you the first time).

The Heart of the Convergence reveals at first login — every character is born there — but the network starts empty of anywhere to *go*. The destination list grows as the player explores. A brand-new player standing at the Obelisk with zero destinations is a natural lore beat: the Obelisk has nothing to show them yet.

A player deep in a zone therefore has exactly three ways out: walk, recall scroll (to the Convergence), or push forward to the summit obelisk. (Note, recorded at Brief 2 closeout: the recall command is designed but not yet implemented — §9.2 — so until it ships, deep-zone players have two ways out. Accepted for The Verdant Reach's launch.) Conquering a zone's obelisk is what turns that zone from a place you trek through into a place you command.

#### The `travel` Command

Travel is a simple command — no dialogue system required:

- `travel` — lists the player's revealed destinations. Only meaningful in an obelisk room; elsewhere it explains that travel requires an obelisk.
- `travel <destination>` — travels there, if the destination is revealed and the player stands at an obelisk.

Destination names are unique across the entire network and typeable (Fordwatch, Stairhead, Cragfoot — every future zone's node names must keep that promise). Multi-word destinations accept case-insensitive prefix matching, consistent with MUD command feel.

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

The recurring signature players learn across every zone: see a Shard, you're safe, services are near, and you can arrive here from any obelisk.

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

-----

## 3. Character System

### 3.1 Character Creation

Shyland is web-based. When a player who has access to the game presses play and has no existing character, they are routed directly into the character creator. While in this state, the only two things the player can do are: (1) complete character creation, or (2) return to the game system's front page — the root URL of the multi-game platform, not just closing the creator window. There is no partial or read-only access to the world without a character.

**One character per account.** A player has exactly one Shyland character tied to their account. There are no character slots, no alts, and no way to create a second character while the first exists.

The creation form is a normal web form: the player may change Origin, Archetype, or name as many times as they like before submitting. Nothing is locked in until the form is submitted.

New players choose:

1. **Origin** (replaces traditional race — see 3.2)
1. **Archetype** (replaces traditional class — see 3.3)
1. **Name** — defaults to the player's `user.profile` gamer tag; the player may override it with a custom name. Name length is constrained to match the existing `UserProfile.gamer_tag` field (max 20 characters); the default is truncated to 20 characters when necessary, since a player with no gamer tag falls back to their username, which can run up to 150 characters. Uniqueness is checked in real time as the player types the override, not only when the form is submitted, so they get immediate feedback before attempting to finalize the character — but that live check is an advisory courtesy only. The authoritative gate is a case-insensitive, database-level uniqueness constraint enforced on every write path, including Django admin, so a name collision can never slip through regardless of how a `Character` row is created. A profanity filter runs on the submitted name unless it exactly matches a gamer tag the player has actually set — a username-derived default has no upstream vetting and is always checked, even if the player submits it unchanged. The filter must use a well-maintained, publicly available library rather than a custom wordlist — consistent with the project's general preference to reuse existing solutions rather than write new ones where one already exists. Once set at creation, the name is permanent and independent of the account's gamer tag — changing the gamer tag later does not rename the character.

There is no portrait selection. Portraits were considered and explicitly cut — not deferred — from character creation. Characters have no visual avatar.

On successful creation, the character spawns at **Heart of the Convergence (0,0,0)** — the same room used as the default recall destination.

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
|Carry Weight    |STR × 10 (in arbitrary units) + equipped bag bonuses       |

### 3.5 Progression & Leveling

**No hard level cap.** Progression is continuous. In practice, a soft cap exists at the frontier of published content — XP return diminishes sharply below a character's level, so grinding low-level content eventually becomes inefficient. The Wastelands always provides a level-appropriate alternative.

**XP Sources:**

- Killing enemies (scaled to level differential)
- Quest completion (primary XP source)
- Exploration (first visit to a new room grants a small XP bonus)
- Crafting milestones
- PvP kills in PvP zones (reduced rate, separate PvP XP track)

**XP Threshold:** `level² × 100`. Level 1→2 costs 100 XP; level 10→11 costs 10,000 XP. The formula extends infinitely. Multiple levels from a single kill are each resolved and announced separately.

**On Level Up:**

- **+5 unspent stat points** (`STAT_POINTS_PER_LEVEL = 5`), accumulated on `Character.unspent_stat_points`. Never expire.
- Vitality and Longevity maximums recalculate and current values are set to the new maximums (level-up fully restores both bars):
  - `vitality_max = (END × 10) + (STR × 3) + (level × 5)`
  - `longevity_max = (END × 8) + (WIS × 5) + (level × 5)`
- +1 skill point (deferred — skill tree not yet implemented)
- New abilities may unlock at certain level thresholds (deferred)

**Spending stat points:** `spend <stat> <amount>` allocates unspent points. Valid stats: `str`, `dex`, `end`, `int`, `wis`, `per`. Spending `end`, `str`, or `wis` immediately triggers bar recalculation. `stats` shows the full stat block with current XP, XP to next level, and unspent points.

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

**Handedness.** Weapons are one-handed or two-handed (`ItemDefinition.is_two_handed`). A two-handed item occupies the character's hands regardless of which slot it sits in — a two-handed bow in RANGED still claims both hands. **All bows are two-handed for now.**

**Equip exchange rule (general, all slots).** When equipping an item, count the currently equipped items that must come off to make room:

- **Zero** — the item equips into a free valid slot.
- **Exactly one, unambiguously** — the swap is **automatic**: the old item is unequipped and the new one equipped in a single command, with output describing the exchange. Never silent, always messaged. Examples: wielding a two-handed sword and equipping a bow (auto), wielding a bow and equipping a two-handed sword (auto), wearing a cap and equipping a different cap (auto). The edge case is intended and accepted: wielding a two-handed weapon and equipping a shield auto-swaps — leaving no weapon in hand. Consistent and flexible.
- **Two or more** — **refuse** with a message naming what must be unequipped first. Example: sword and shield equipped, equipping a two-handed axe refuses; unequip either one and the now one-for-one swap autos.
- **Exactly one, but ambiguous** — refuse, naming the candidates. Canonical case: both RING slots full and a third ring equipped — the game cannot know which ring to displace. Same rule for any item valid in multiple slots that are all occupied (e.g. a knife valid in either hand while both hands are full).

Auto-swap respects every existing unequip constraint: a cursed item cannot be displaced, and a displacement that would violate the carry limit (bags) refuses instead.

**Slot capacity.** Characters have exactly two RING slots; every other equipment slot holds exactly one item. (Implemented in v18 as a slot-capacity mechanism; RING is currently the only multi-capacity slot.)

**Carry limit:** Base carry weight is STR × 10. Bags equipped in valid slots add a carry bonus on top of that. No off-body storage, no bank, no shared stash.

### 3.7 Death & Resurrection

Death in Shyland is meaningful but not brutal. The full dying-and-death sequence was rebuilt in v19:

- Player reaches 0 Vitality → **Dying** state (30-second window). The fatal blow ends combat in both directions for the fallen: their queued and same-round attacks are **discarded** (no posthumous death blows), incoming hits stop mattering and stop printing, and every active effect on them is cancelled (`removed_by='dying'`) — the character's own DoTs already burning on NPCs keep running.
- **Presentation:** the fallen player's output pane clears; a red fatal-blow line opens the sequence ("You have been dealt a fatal blow…"); a lore ladder escalates through the window (a line every ~5 seconds, then every second at the end) — all lore, never mechanical time units. No combat output of any kind reaches the dying player. The room sees the third-person fall announcement (excluding the fallen).
- All commands except `use` are blocked while Dying — including `quit`; there is no exit but the outcome.
- **Revival:** any vitality restoration above zero while Dying clears the state — the character rises with **exactly the healed amount** (a strong enough potion may legitimately restore full; a weak one stands you up at a sliver into whatever is still swinging). Combat resumes naturally: the character was never removed from the session. Any other player in the room can also revive them with an item or ability once such tools exist — no group membership required.
- If not revived within 30 seconds → **Dead**. A death declaration ("The darkness takes you."), then the player respawns at their bound recall point (default: The Convergence) with full bars, the client fully re-synced (fresh room output, channel-group swap).
- On death: all remaining `EffectInstance` rows cleared; pending combat actions cleared; the `CombatSession` ends; Acuity resets (death resets it; level-ups do not).
- **XP loss:** 10% of current XP (cannot lose a level); applies at level 10+ only.
- **Durability loss:** all equipped items with `takes_durability_loss=True` lose 10% per death; after 10 unrepaired deaths an item breaks. The flag is the only gate. (v19 convention: `takes_durability_loss=False` is reserved for genuinely rare items and Artifacts — ordinary gear wears, including the free starter kit; the durability loop is part of onboarding.)
- **Link-dead policy (ruled, deliberate):** closing the browser mid-combat abandons the character to the fight — the world keeps happening to link-dead characters, and dying offline runs the full sequence to an unattended death. This is what makes the `quit` combat-block meaningful rather than theater.
- In PvP zones only: chance to drop one non-equipped carried item
- A **Death Shard** item is left at the death location; player can retrieve it within 30 minutes to recover any dropped item

**Hardcore Mode** (optional, on character creation): permadeath. Character deleted on death. Hardcore characters are flagged visually and have a separate leaderboard.

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

**Recovery:** Healing spells, medkits, potions, and passive natural regeneration. Passive regen is always active when not in combat and not in the Dying state — no rest command required. Formula: `ceil((vitality_max - vitality_current) / VITALITY_REGEN_SECS)` per tick, minimum 1 point per tick when any healing is due. At the default constant of 120 seconds, a character at zero Vitality reaches full in at most 120 seconds; a character missing one point heals in a single tick. Regen is silent — no message is sent; players observe recovery through the status bar.

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
- Rest and time naturally return Acuity toward a character's baseline (passive Acuity drift is implemented)

**Manipulation:** Players can actively shift their own Acuity intentionally. Pushing it high before a single-target duel, then managing the aftermath, is a valid play style. The system rewards players who understand their character's band and manage it actively.

### 4.3 Longevity

**What it is:** The slow burn. Accumulated resilience — the will and capacity to keep going over time.

**Mechanical effects:**

- Controls stamina duration — how long a character can sprint, sustain effort, or maintain concentration
- Governs duration of sustained effects: a character's own damage-over-time effects last longer at high Longevity; enemy DoTs applied to them expire faster
- Controls the window of long-lasting buffs and debuffs
- At low Longevity: sustained spells collapse early, long fights become increasingly punishing

**Recovery:** Longevity recovers passively out of combat using the same formula as Vitality but with a much slower time constant (`LONGEVITY_REGEN_SECS = 3600`): `ceil((longevity_max - longevity_current) / LONGEVITY_REGEN_SECS)` per tick, minimum 1 point per tick when any healing is due. At 3600 seconds, full Longevity recovery from zero takes at most one hour — 30× slower than Vitality. Warden abilities can accelerate this. It is the hardest bar to restore and the one players are most likely to mismanage over a long dungeon run.

**Design intent:** Longevity is the dungeon stamina resource. A player might enter a dungeon with full Vitality and Acuity but low Longevity from previous fights, and feel it immediately in their sustained performance. It rewards planning and discourages endless grinding without rest.

### 4.4 Interactions Between the Three Bars

The bars are not isolated:

- Critically low Vitality causes Acuity to spike (panic response — hyper-focus with all its drawbacks)
- Severely low Longevity causes both Vitality regen and Acuity recovery to slow
- Certain eldritch effects damage all three bars simultaneously
- A skilled Warden manages all three for the party — not just the green bar

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

**Auto-attack and attack focus (v19):** If no player action is queued when a round fires, the tick engine creates an auto-attack targeting the session's **focus NPC** (`CombatSession.focus_npc`; falls back to the first live NPC if unset). Players are never idle. Focus is player-controlled: engaging a target — starting combat or adding a new NPC mid-fight — sets focus to it; `kill <target>` against an in-session, non-focused target **refocuses** ("You change your attacks to focus on…"); the same command against the current focus reports "You're already fighting…". When the focused NPC dies with others still live, focus auto-shifts to the next live NPC with an announcement — focus changes are never silent. The Acuity single-target bonus rides the same field: player-controlled focus and the Acuity focus target are one concept. Multi-target damage (cleave/AoE) remains deliberately unbuilt. Where multiple same-name NPCs share a room, engagement, hit, kill, wound-state, and focus messages carry **positional ordinals** ("the second black bear") — positional in room parse order, so ordinals reflow as NPCs die; dot-notation (`kill 2.bear`) selects among same-name targets.

**Initiative (rounds 2+):** Each round after the first, initiative is rolled for all participants: `d10 + DEX + PER`. Highest total acts first; ties go to the player. In round 1, whoever initiated combat acts first (player if they used `kill`/`attack`; NPC if they aggro'd on room entry).

### 5.4 Attack Resolution

```
1. Hit check (v19 — contested d20 with independent critical):
   total   = d20 + attacker DEX
   defense = TO_HIT_DEFENSE_BASE (10) + defender DEX
   → total ≥ defense                      : success — roll the independent critical check
   → short by 1..GRAZE_WINDOW (3)         : Graze (50% damage)
   → short by more                        : Miss
   Critical (on any success): chance = CRIT_BASE (5%) + 1%/point of DEX advantage,
   floored at 5%, capped at CRIT_CAP (25%). Criticals are an independent roll on
   successful hits — never a band of the to-hit roll. All five constants are named,
   tunable module-level values. Design intent: at large stat advantage always-hitting
   is deliberate (outleveled content is trivially hittable); the crit cap bounds the
   multiplier at any stat spread.

   NPC contest stats (v19 — "contests add, quantities multiply"): the stats NPCs bring
   to opposed rolls grow ADDITIVELY on the player curve. npc_level = scaling_factor +
   10 × (mk_tier − 1); DEX = round(18 + 2.5 × (level − 1)) + tier offset (**v21:
   normal +0 / elite +2 / boss +2 — re-blessed at-level hit rates of 55% / 45% / 45%**;
   the v19 offsets of +3/+6 concentrated boss difficulty in the miss rate and made the
   blessed targets real only for max-DEX builds — the #89 survey's knife-edge finding.
   Boss difficulty now lives in HP, damage, and escorts instead; see §5.9);
   STR/PER/INT = authored base + round(2.5 × (level − 1)), preserving species
   identity. Vitality keeps its multiplicative scaling — pools are quantities, not
   contests. `scaling_factor` encodes the NPC's within-band level (1–10).

2. Damage calculation:
   base_damage    = weapon damage roll (random within midpoint ± spread)
                    If no weapon is equipped, base_damage = 0 (only stat_bonus applies)
   stat_bonus     = relevant stat value (STR melee / DEX ranged / INT spells)
   acuity_mod     = band-relative deviation modifier (Section 4.2): 1.0 inside the
                    Origin band; 1.0 + distance above band_high (focus target only);
                    1.0 − distance below band_low (all targets).
   durability_mod = performance multiplier from weapon's durability table (1.0 = no penalty;
                    1.0 if no weapon equipped)
   raw_damage     = (base_damage + stat_bonus) × acuity_mod × durability_mod

3. Hit multiplier applied:
   final_damage = raw_damage × hit_multiplier (0.5 graze / 1.0 hit / 1.5 critical), minimum 1

4. Mitigation (future):
   final_damage = final_damage - target defense value (minimum 1)

5. Elemental/type resistances apply as percentage reduction after armor (future)
```

**Unarmed combat:** A character with no weapon equipped can still attack. `base_damage` is 0 — there is no weapon damage roll — but `stat_bonus` and `acuity_mod` still apply, making unarmed attacks weaker but functional. This is intentional design, not a fallback. Attack flavor text for unarmed combat is drawn from the attacker's `UnarmedMessagePool` (configured on the `Archetype` model, falling back to the default pool). NPCs without a weapon also resolve unarmed attacks the same way, drawing from their `NpcDefinition.unarmed_message_pool`.

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

### 5.7 Flee & Escape

`flee` command. Success roll: **player DEX + d20 vs. average PER of all NPCs in the session**.

**Flee direction:** On success, the character exits via the reverse of the direction they entered the room (the way they came in). If that exit is not available, a random adjacent exit is chosen. If no exits exist, flee fails automatically regardless of the roll (`"There is nowhere to run!"`).

**Cooldown:** A failed flee attempt sets a cooldown of `FLEE_COOLDOWN_TICKS × COMBAT_ROUND_TICKS` seconds before another attempt is allowed. Cooldown is tracked per character per session. Successfully fleeing ends the session with no cooldown.

**On success:** The combat session ends. NPCs remain in the room at their current Vitality (no reset). The player enters the destination room and the normal aggro check fires — if that room also has aggressive NPCs, a new combat begins.

**Messages:**
- Player (success): `"You have successfully fled from your enemies."`
- Room (success): `"{Name} fled the room leaving the enemies looking confused."`
- Player (failure): `"You tried to flee but your enemies are too strong."`
- Room (failure): `"{Name} tried to flee combat but could not slip away."`

Boss encounters may apply additional flee penalties in future content.

### 5.8 Group Combat

Parties of up to 6 players. Enemies maintain a threat table — highest threat character receives the majority of attacks. Bulwarks generate extra threat; Shades reduce theirs.

### 5.9 NPC & Enemy Design

Enemies have:

- A **combat tier** — one of: Normal, Elite, Champion, Boss, World Boss. Stored as `NpcDefinition.combat_tier`. All existing NPCs default to Normal. The field exists for display, content authoring, and future AI/balance differentiation; no tier-specific behavior is implemented yet.
- **Archetype flags** governing tactics
- **Effects list** — each NPC definition carries a list of `NpcEffect` entries. Each entry links to an `EffectDefinition` and has a per-entry `effect_chance` (0.0–1.0). On each NPC attack, every entry is rolled independently; those that fire are applied via the shared `EffectInstance` system and appended to the attack message. An NPC with no effects is a pure auto-attacker. Higher-Mk NPC definitions can carry longer effect lists or higher-magnitude effects to increase difficulty. Telegraph and phase-change mechanics are deferred to later content work
- **Unarmed message pool** — an optional FK on `NpcDefinition` to an `UnarmedMessagePool`. If null, falls back to the default pool. Used when the NPC has no weapon equipped
- **Loot tables** — normalized `LootTable` and `LootTableEntry` models; one table can be shared across multiple NPC definitions

NPCs are defined by an **`NpcDefinition`** (the template — name, stats, loot table, behavior flags, respawn timer, combat tier) and spawned as **`NpcInstance`** rows (live copies in specific rooms at a specific Mk tier). Mk tier is instance-specific — the same definition can spawn as Mk 1 goblins in a starter zone and Mk 5 goblins in a harder one.

**Room population is configured via `RoomSpawn`.** Each `RoomSpawn` row declares that a specific room should contain a specific count of a specific NpcDefinition at a specific Mk tier. The tick engine uses this as the sole source of truth for NPC population — it does not infer spawn configuration from existing instance rows. Fields: `room`, `npc_definition`, `mk_tier`, `count` (desired live instances), `is_active`. Unique on `(room, npc_definition, mk_tier)`.

**Respawn mechanics:** When an NPC dies, the `NpcInstance` row is marked dead (`is_alive=False`) with a `respawn_at` timestamp set based on `NpcDefinition.respawn_minutes`. Each tick, the engine clears dead instances whose `respawn_at` has passed, then fills any gap between the current live count and the configured `count`, subject to a total cap of `count × 2` instances (live + dead combined). This cap prevents unbounded dead-instance accumulation while still allowing the respawn timer to control when replacements appear. **(v21, #17)** When an `is_aggressive` NPC (re)spawns into a room containing living player characters, it engages on the spawn tick — same behavior as a player walking in: engagement lines and combat start (joining any active session, as multi-NPC encounters support), with the standing article grammar and #81's room-context-before-ambush ordering. The check runs inside the respawn path only — zero new recurring per-tick queries (the #107 discipline).

**Corpses** are temporary loot containers in the room. Only the killing character may loot items from a corpse. Currency is visible to all via `examine` but only transferred to the killer. Corpses are deleted when fully looted; unlooted corpses are deleted after `CORPSE_DECAY_MINUTES` (10 minutes) by the decay sweep.

**Currency drops** are rolled at death using the formula: `random.randint(currency_drop_min × mk_tier, currency_drop_max × mk_tier)`. Currency display respects zone aliases via `display_for_zone()`.

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

**Tier materials suppress the Mk suffix (display only).** Items whose names carry a **tier material** — the copper → silver → gold → platinum ladder that tracks the currency table — do not display a Mark suffix, because the material already says the tier: a *Copper Ring of Strength* is `mk_tier=1` under the hood with standard scaling and rarity machinery, but never prints "Mk 1." This is the same pattern as local zone currencies: a display alias, same math, zero engine change. The rule is deliberately narrow — it applies **only** to tier materials. Flavor materials (iron, wood, leather, and the like) do not suppress anything: an Iron Sword still reads "Iron Sword Mk 1." Today the tier-material rule covers accessories only; later zones extend the ladder upward with the nobler metals as Mk tiers rise.

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

**Proc-family authoring rule (v21, #68):** every proc-style secondary stat (crit_chance, bleed_chance, stun_chance, lifesteal, poison_chance, electric_damage_bonus, mana_regen) is authored at `base 0.5, factor 0.2` — the curve that guarantees Mk 1 rolls of ≥1 at every rarity. The four stats previously authored below this threshold rolled a deterministic 0 at Mk 1–2 forever. **Zero-value stats are never hidden in display** (ruled): a rendered zero is a bug signal, and sirens stay audible — the fix is always in the data, never in suppression. Stored zeros from the pre-fix era were re-rolled once by the idempotent `fix_zero_secondary_stats` management command (the stat identity kept, the value made real).

**Slot counts are pool-capped** (settled at v18 closeout): an instance rolls `min(rarity's slot count, size of the item's secondary stat pool)`. Legendary's "all in pool" is this same principle stated at the ceiling — every rarity is implicitly "at most all in pool." A small-pool item therefore maxes out early: the copper accessories, with their deliberate two-stat pools, roll both secondaries at Epic and above — three stat lines total counting the primary. The rarity guarantee is about the roll's ceiling, not a promise that every item type can express every tier's slot count.

#### Weapon Damage

Weapon damage is stored as a midpoint and a spread:

- **Midpoint** — scaled by Mk tier and rarity (same formula as stats above)
- **Spread** — a fixed width defining the range of the damage die. This is an identity property of the weapon type, not affected by rarity. A high-variance weapon (greatsword, shotgun) has a wide spread; a low-variance weapon (rapier, laser pistol) has a narrow one.

Every attack rolls within `midpoint ± spread`. Rarity makes weapons hit harder on average; spread defines how swingy they are regardless of rarity.

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

The performance penalty applies to the item's stat contributions and weapon damage output. At 0%, the item stops functioning entirely until repaired.

#### Degradation Rate

Each ItemDefinition carries its own durability table defining the degradation rate — how quickly it moves through the threshold bands. Different item types degrade at different rates: swords degrade faster than firearms due to physical impact; armor degrades slower than weapons. Builders can override per-item; new items pre-populate with a sensible default for their type.

#### Repair

- **Above 0% durability:** Always repairable. Success chance scales with current durability — a well-maintained item is easy to repair; a nearly broken one is harder.
- **At 0% durability:** Repairable, but a very difficult roll. Most repairs at 0% will fail. Players who let items reach zero are taking a real risk.
- Repair is performed by repair vendors (currency cost) or via the Smithing/Tinkering crafting disciplines.

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

Items in Shyland have an identified state that controls what information is visible to the player. This system enables mystery items, cursed items with hidden properties, and one-of-a-kind Artifacts whose true nature is a permanent secret.

#### Default Behavior

Items default to identified. The vast majority of items in the game — standard drops, crafted gear, vendor stock — are immediately readable by any player who picks them up. The identification system only activates when a builder or super user deliberately marks an item as mysterious.

#### Unidentified Items

When a builder creates an item they want to be mysterious, they set `is_identified = False` on the item and configure two optional fields on the item definition:

- **Mystery name** — the name shown to players before identification. Examples: `"an unknown sword"`, `"a fragment of something"`, `"a device you don't recognise"`. If not set, falls back to `"an unidentified [item type]"`.
- **Mystery description** — the text shown when the player examines the item. Can be evocative atmosphere, deliberate misdirection, partial lore, or simply `"You can't determine anything about it."` If not set, falls back to that generic message.

Unidentified items show only their mystery name and mystery description. No real name, no rarity, no Mk tier, no stats, no damage range — nothing mechanical is revealed. A player can pick up an unidentified item, carry it, and even equip it (soulbinding it in the process) without knowing what it truly is.

#### Identification Is Per-Character Knowledge

Identification is not a property of the item object — it is knowledge the current holder has about it. When a character drops an unidentified item, that knowledge is lost. The next character to pick it up starts fresh with no identification.

**v20 status and redesign direction (#80):** the drop-loses-knowledge rule shipped in v18 (drop flips `is_identified` False) but the identification *service* never did — making drop a one-way trapdoor discovered in v20 play. The database record stays fully intact; the boolean is purely a presentation gate. The ruled future direction, deliberately unmilestoned: knowledge is a property of **holding** — ground items show mystery names to the room and observers; `examine` (close inspection) reveals real details *without* pickup; **picking the item up** flips the boolean and permanently unlocks normal display; drop re-veils. The identification service then concerns curses and deeper properties, not basic nature.

This means the same physical item can be identified to one character and unidentified to another, depending on their history with it. There is no shared identification state across characters.

#### Permanently Unidentifiable Items

A super user can mark a specific item instance as `is_unidentifiable = True`. No in-game mechanism — NPC sage, Warden ability, identification scroll — can ever identify such an item. The mystery name and mystery description are all any player will ever see through normal play.

This is intended for one-of-a-kind Artifacts whose true nature is a permanent secret of the game world itself. Players can examine them, read whatever lore the super user wrote into the mystery description, and speculate — but the mechanical truth never surfaces.

#### Identification Trigger

The in-game mechanism for identifying items — NPC sage service, Warden class ability, consumable identification scroll — is designed but not yet implemented. See Section 12.

#### Interaction with Curses

An unidentified item may also be cursed. Identifying the item reveals both its true nature and its curse status simultaneously, allowing the player to make an informed decision before equipping. Without identification, equipping a cursed item is a risk the player takes knowingly.

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

### 6.10 Bags and Carry Capacity

Bags are equipment items that expand carry capacity. They occupy equipment slots (BACK is the primary bag slot; future slots such as a hip slot for courier bags are planned).

- Base carry capacity: STR × 10
- Equipping a bag adds its `carry_bonus` to the total
- The inventory is a flat pool — players do not manage which specific item is in which pocket
- **A bag cannot be unequipped if doing so would put the character over their carry limit**
- The slot a bag occupies creates meaningful trade-offs — a courier bag on a hip slot means no pistol there

### 6.11 Inventory Display

The `inventory` command shows:

1. **Equipped items** — shown first, grouped by slot in order: HEAD, NECK, SHOULDERS, CHEST, HANDS, WAIST, LEGS, FEET, RING, MAIN_HAND, OFF_HAND, RANGED, BACK. Empty slots are omitted.
1. **Carried items** — sorted by item type, then Mk tier (ascending), then rarity (ascending by power: Common → Uncommon → Rare → Epic → Legendary → Artifact), then name.

Display rules:

- Durability shown for items where `takes_durability_loss=True`; omitted for others (rings, etc.)
- Bags show carry bonus instead of durability
- Consumables of identical type and Mk tier are stacked with an `xN` count
- Broken items show `BROKEN` instead of durability percentage
- Carry count shown as `(current/max items)`
- Cursed items that have not been identified show no curse indicator
- Every item line shows a soulbind indicator: `[bound]` if soulbound to the character, `[drop]` if not yet bound and still droppable
- Unidentified items show only their mystery name (no rarity, no Mk tier) in place of the real item name

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
- **Commands:** `list` (vendor stock with prices), `buy <item>`, `sell <item>`, `repair <item>`, bare `repair` (targets the most-damaged item; repeated use walks the damage list; reports "nothing to repair" when done), and `repair all` (one paid attempt per damaged item, most-damaged first, individual attempts may fail, stops if copper runs out). Commands route automatically: buy/sell/list to the living vendor in the room, repair to the living repairer — killed service NPCs are out of business until they respawn.
- **Materials** are an item type (`material`) — no slots, stats, or durability; pure vendor-sellables (Animal Hide, Insect Carapace, and their future kin). Animals drop no copper — only higher sentient species carry money.

**Combat QoL (settled alongside commerce):** targetless `attack`/`kill` auto-targets **only while the player has aggro** — "ouch, you hit me, I'm hitting you back." The target is the first attacker (earliest-engaged living NPC in the session); spamming the bare command stays on that enemy until it dies, then rolls to the next. With no aggro, a target is still required — auto-targeting a peaceful room would turn a typo into a murder.

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

- **The free starter kit:** eleven distinct authored definitions at `base_value=0` — exploit-proof by construction (sale value is 0, and worthless items are refused: "That's not worth anything to me."). The kit covers every equipment slot except OFF_HAND and RANGED — deliberate gaps; the first slots a player must *earn* (Morra's priced tier sells them). Kit gear wears normally (`takes_durability_loss=True`) and repairs for ~nothing via **pity-repair** lines in each repairer's voice — the durability loop is onboarding, and the first lessons are free.
- **Priced tier:** a small aspiration shelf at Morra (shortsword, shield, sling, jerkin) priced for early hide-money; the full price-range spread is a future stocking pass.
- **Currency display rule:** every player-facing money amount — `list` prices, `buy`/`sell` amounts and refusals, repair quotes — renders through the shared tier formatter. Raw copper counts never reach the player; zone aliasing comes free.
- **Multi-vendor rooms** resolve `list`/`buy`/`sell`/`repair` to a deterministic serving NPC (lowest pk); at the gazebo the non-serving spouse kibitzes after transactions.

-----

## 7. Social Systems

### 7.1 Communication Channels

|Channel|Command             |Scope                          |
|-------|--------------------|-------------------------------|
|Say    |`say <text>`        |Current room only              |
|Yell   |`yell <text>`       |Current room + adjacent rooms  |
|Tell   |`tell <name> <text>`|Private, anywhere              |
|Party  |`party <text>`      |All party members              |
|Guild  |`guild <text>`      |All online guild members       |
|Zone   |`zone <text>`       |All players in current zone    |
|General|`general <text>`    |All players online (throttled) |
|Emote  |`emote <text>`      |Freeform action in current room|

All channels are logged server-side for moderation.

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

### 7.6 NPC Dialogue — The Listening Model (v19)

NPCs are not addressed; they **listen**. There is no `talk` or `ask` verb by ruling — dialogue is diegetic room speech: you say things aloud, and inhabitants who know something about what you said may answer. The mechanic is the fiction.

**Mechanics (all ruled v19):**

- Per-NPC keyword→response maps (`DialogueEntry` with lowercase single-word keywords, `DialogueResponse` pools). Matching is dumb word-level containment — no NLP. Unmapped NPCs stay silent.
- One utterance → each eligible NPC answers **once**. **Entry-first draw:** among an NPC's matched entries, one entry is chosen at random, then one response from its pool — each matched *topic* gets equal voice regardless of pool depth. Re-asking re-rolls.
- **No consecutive self-repeats:** an NPC avoids the response it gave last time when its pool offers an alternative.
- Multiple responders: **random shuffle per utterance**, delivered tick-staggered at **2 ticks between speakers** ("less than combat, a little more sociable, less interrupty"). Second and later speakers are introduced by position-aware **connective color** drawn from pooled templates ("{name} also looks up and answers." / "{name} chimes in, not to be left out.").
- Responses **broadcast to the room**, riding the standard `say` formatting — identical for asker and witnesses. Responses **always land**, even if the asker has left; if the asker is gone when the final response fires, that last speaker may add one lore-voiced **departure reaction** (Aldric snorts. "Youth," he mutters, to no one in particular.).
- **Greetings:** an NPC with a greeting entry emits one line the first time a given character enters its room — once per character, forever.
- **Discoverability:** examine-text hints on talkative NPCs, a `help` line, greetings demonstrating that NPCs speak, and room-broadcast answers teaching bystanders — discoverable, never announced.
- Authored dialogue carrying directional or locational claims is verified against the room graph before shipping (standing rule from issue #34).

The v19 roster: Aldric, Info Prime, Morra, Pella, Ferwick, Repairbot Prime, Seris, Veris. The Obelisk and the spheres remain silent by ruling — mystery preserved. Persistent NPC memory (Sirius-class entities) remains a future tier.

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

### 9.1 Implemented Commands (v1)

These commands exist in the current codebase and are available to all players.

#### Navigation

|Command|Alias|Description                 |
|-------|-----|----------------------------|
|`north`|`n`  |Move north if an exit exists|
|`south`|`s`  |Move south if an exit exists|
|`east` |`e`  |Move east if an exit exists |
|`west` |`w`  |Move west if an exit exists |
|`up`   |`u`  |Move up if an exit exists   |
|`down` |`d`  |Move down if an exit exists |
|`travel`|—    |List revealed Obelisk Network destinations (obelisk rooms only — Section 2.11)|
|`travel <destination>`|—    |Travel to a revealed checkpoint or obelisk (obelisk rooms only; case-insensitive prefix match, leading-The tolerance)|

If no exit exists in the requested direction, the server responds with a message and no movement occurs. The message is either a custom per-direction message set on the room (via `no_exit_*_msg` fields) or the hardcoded default for that direction. Movement has no action economy cost outside of combat. **Directional movement is refused during active combat** ("You can't just walk away from a fight — flee!") — `flee` is the deliberate exit.

#### Exploration

|Command|Alias|Description                                                                  |
|-------|-----|-----------------------------------------------------------------------------|
|`look` |`l`  |Display the current room's full output — area description (if any) + long description, exits, occupants, players. Always full regardless of brief mode.|

#### Communication

|Command     |Alias|Description                             |
|------------|-----|----------------------------------------|
|`say <text>`|—    |Speak to all players in the current room. **Some NPCs listen** (Section 7.6) and answer in the room|

#### Information

|Command|Alias|Description                                                     |
|-------|-----|----------------------------------------------------------------|
|`who`  |—    |List all players currently online (uses Redis presence tracking)|
|`wallet`|—   |Show your money (tier-formatted) as one key/value line — `Wallet:` in key-color, amounts in value-color **(v21)**. `inventory` shows the identical Wallet section|
|`help` |`?`  |Display the command reference **(v21)**: static six-direction movement line (documents the command set, not the current room), commands alphabetized, one-line `say` entry, `brief` documented, the `<item selection>` convention with a single grammar section, uniform `[x \| y]` spacing, section headers in key-color and content in value-color|

#### Session

|Command|Alias|Description|
|-------|-----|-----------|
|`quit` |—    |Leave the game and return to the games lobby. Blocked in combat (flee first) and while Dying|

#### Character & Inventory

|Command    |Alias|Description                              |
|-----------|-----|-----------------------------------------|
|`inventory`|`inv`|Show equipment, inventory, and wallet **(v21)**: `Equipment:` (slot-prefixed lines), `Inventory (N/M items):`, and `Wallet:` headers in key-color; every content line in value-color; item flag blocks keep their rarity colorization inside value lines|
|`stats`    |—    |Show the character sheet **(v21)**: `Character Stats:` header in key-color; the Player line `Player: <name> - Level <N> <Origin> <Archetype>`; the full stat block, XP progress, and unspent points — everything under the header in value-color (no bracketed header; subkey-color considered and deferred)|
|`spend <stat> <amount>`|—|Allocate unspent stat points to a primary stat (str, dex, end, int, wis, per)|

#### Settings

|Command      |Alias|Description                                                              |
|-------------|-----|-------------------------------------------------------------------------|
|`brief`      |—    |Report the current brief-mode setting (bare form queries; it never sets) |
|`brief on`   |—    |Enable brief mode (default): revisited rooms show the brief description only|
|`brief off`  |—    |Disable brief mode: every entry shows the full area + long description   |
|`timestamps` |—    |Report the current timestamp-display setting (bare form queries)         |
|`timestamps on`|—  |Show the `[HH:MM:SS.ss]` prefix on stamped output lines (default; stored per character, survives reconnect and devices)|
|`timestamps off`|— |Hide the timestamp prefix (the envelope's `ts`/`seq` remain on every message regardless)|

First entry to any room always shows the full text in both modes.

#### Combat

|Command                            |Alias|Description                  |
|-----------------------------------|-----|-----------------------------|
|`kill <target>` / `attack <target>`|`k`  |Initiate combat with a target|
|`kill` / `attack` (bare)           |`k`  |Auto-target the first attacker — only while under aggro; refuses with no target otherwise|
|`flee`                             |—    |Attempt to escape combat     |

#### Commerce

|Command|Alias|Description|
|-------|-----|-----------|
|`list`|—    |Show the room vendor's stock and prices (Section 6.12)|
|`buy <item>`|—    |Buy from the room's living vendor (always Common rarity, entry's Mk tier)|
|`sell <item>`|—    |Sell an unequipped item for one third of its value (soulbound OK; instance deleted)|
|`sell all <item>` / `sell N <item>`|—|Bulk sell per the v20 grammar — per-sale messages plus a one-line total; `N` is all-or-nothing|
|`sell all <rarity>` / `sell all <rarity> <item>`|—|Rarity-filtered bulk sell; noun optional with a rarity word (`sell all common` flushes every unequipped Common item; zero-value items skipped with a summary)|
|`repair <item>`|—  |One paid repair attempt via the room's living repairer|
|`repair`|—    |Bare form: targets the most-damaged item; repeated use walks the damage list|
|`repair all`|—    |One paid attempt per damaged item, most-damaged first; stops if copper runs out|

#### Item Interaction

|Command         |Alias|Description                                         |
|----------------|-----|----------------------------------------------------|
|`pickup <item>` |`p`  |Pick up a loose item from the current room          |
|`drop <item>`   |—    |Drop a carried, unbound item into the current room  |
|`equip <item>`  |`eq` |Equip a carried item into an equipment slot         |
|`unequip <item>`|`uneq`|Move an equipped item back to carried inventory   |
|`use <item>`    |—    |Use a consumable item                               |
|`examine <item>`|`ex` |Inspect an item, live NPC, or corpse in detail      |

#### Corpse Interaction

|Command               |Alias|Description                                                          |
|----------------------|-----|---------------------------------------------------------------------|
|`loot [corpse] [item]`|—    |Loot a corpse; bare `loot` takes everything from the most recent kill|
|`loot all`            |—    |**(v20)** Sweep EVERY corpse in the room — per-item loot lines, then a summary ("Looted 3 corpses; 2 carried nothing worth taking."); ownership rules enforced per corpse|
|`loot all <item>` / `loot N <item>`|—|Item-quantified loot against the union of all corpse contents in the room|

**Corpse noun syntax:** `loot` targets the most recently created corpse in the room. `loot 2.corpse` targets the second most recent. `loot goblin` targets the first corpse whose name contains "goblin". An item noun may follow: `loot 2.corpse sword` loots the first sword from the second corpse. Only the killing character may loot items. Currency is always transferred on first loot of a corpse regardless of item noun. Bare `loot` after a corpse is emptied automatically targets the next most recent corpse in the room.

**Command grammar (v20 — one resolver for every noun-taking command):** `<verb> [all | N] [rarity] [noun]`, plus the retained `N.noun` index form. Matching is **ordered token-prefix** against the player-visible name-with-tier tokens (`battle axe mk 1` → any ordered-subsequence prefix reference matches: `axe`, `battle axe`, `axe 1`, `b a`; no mid-word matches). Case-insensitive; plural fallbacks tried in order (strip `es`/`s`, `ves`→`fe`, `ies`→`y`). **Rarity is never a name token** — it is a closed-vocabulary instance *filter* (`common`…`artifact`; item names never begin with a rarity word, enforced by seed verification), and with a rarity present the noun may be omitted. `all` = every match; `N` = exactly N, all-or-nothing. Ambiguity across *different* definitions → a refuse-list, never a guess. Multiple instances of the *same* definition select deterministically and protectively: `sell`/`drop` lowest rarity then most damaged; `equip` highest rarity then best condition; others oldest. **Equipped items are always excluded from `sell`/`drop`, including `all`.** Unidentified items match by their mystery name — what you see is what you type. The same token-prefix matching (no quantifiers) targets NPCs for `attack`/`kill`. **Tab completion is server-authoritative:** the client round-trips the current line and receives context-correct candidates (inventory, vendor stock, room NPCs, corpse contents, grammar words) and cycles them; the verb list arrives at connect. A **dispatch guard** wraps every command: no input, however malformed, can drop the connection — failures log server-side and answer with one error line.

The `help` output is context-aware — it shows only the exits that actually exist in the current room, not a fixed list of all possible directions.

The unknown command response directs players to `help`: *"Unknown command. Type 'help' for a list of commands."*

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
|`equipment` / `eq`|Show equipped items only |
|`quests`          |Show active quest journal|

#### Travel

|Command            |Description                                            |
|-------------------|-------------------------------------------------------|
|`recall`           |Teleport to bound recall point (requires recall scroll)|
|`enter <exit name>`|Use a named exit (non-directional)                     |

### 9.3 Command Design Rules

- Every command must work via keyboard input only — no mouse-only interactions. Screen reader users must be able to access all functionality through the input line.
- Commands should be short, memorable, and consistent with classic MUD conventions where possible.
- Every unrecognised command gets a helpful redirect, not a bare error. Currently: *"Unknown command. Type 'help' for a list of commands."*
- `help` output must stay current as new commands are added. When a new command is implemented, update both this section of the GDD and the `cmd_help()` method in `consumers.py`.
- **Boolean commands always require an explicit value.** Never a bare toggle. `brief on` / `brief off`, not bare `brief`. This rule applies to all future boolean-setting commands. (The bare form *queries*; querying is not setting — `brief` and `timestamps` both report their current value.)
- **Every submitted command echoes** into the output pane before its result — `> command as typed`, dim gray, timestamped — a transcript of the player, never re-broadcast to others, echoed even for invalid input so errors keep their context.
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

**Right pane (fixed 300px):** the stats section — headed by the **character name, verbatim casing** — with Vitality and Longevity as ratio bars (numerals alongside) and **Acuity as a band gauge** (fixed 0.0–2.0 track, the Origin's optimal band shaded from server-supplied bounds, a tick at current value): the first surface that teaches the three-bars design. The whole section turns **combat-red** (from the state-sync combat boolean). Below it, the **fight panel**: one row per session enemy — name, hp bar, `hp/hp_max`, and the focus marker `»` — fed by a `fight` message each combat tick, empty outside combat, scrolling on overflow. The **map** (Section 2.5) sits fixed at the bottom.

**Command bar:** input line with the send button inside and the **connection indicator** at its right — a dot plus latency (client pings every 10s, server echoes; green healthy, amber degraded, red pulsing on reconnect, gray dead; accessible label, never announced).

**The output envelope:** every outbound WebSocket message carries `ts` (epoch ms UTC, stamped at creation) and `seq` (per-connection monotonic, stamped at one audited delivery choke point — the designated future firehose tap; nothing may bypass it). **`seq` order is authoritative for rendering;** `ts` may lawfully be non-monotonic against it. **Display rule — timestamps mark events, not renderings:** combat, chat, presence, commerce, XP, errors, system/ambient, setting-change confirmations, and command echoes display the dim `[HH:MM:SS.ss]` local-time prefix (aria-hidden; governed by the `timestamps` preference); room renders and state reports (inventory, stats, vendor lists, examine, help) do not.

**The output palette:** client-side styling driven by server-sent semantic categories (the server never sends hex for message text). **(v21) Named palette vocabulary:** **key-color** (`#7FB3D5`, the structural-header blue) and **value-color** (`#E8E4D8`, the room-content near-white) are CSS variables and citable design vocabulary; subcategories deferred until needed. Structural section headers share key-color — *every* header, present and future. Room-content lines (names, occupants, items) in value-color; **(v21)** room description prose also in value-color, and area description prose in the Area's `theme_color` — the two prose levels visually distinct, delivered as separate payload fields. **(v21) Structured key/value reports:** `report` messages may carry server-tagged lines (`k`/`v` per line); the client renders keys in key-color and values in value-color — adopted by `inv`, `stats`, `wallet`, and `help`; item flag blocks keep their colorization inside value lines. Who's-here / What's-here entries are bare noun phrases **(v21)** — no "is here"/"lies here" suffixes. Combat: outgoing `#C4453F`, crits `#E24B4A` bold, incoming `#E0724A` (direction readable at a glance — directional arrows were designed and **abandoned**), misses gray, kills/XP gold, success green, errors amber. Rarity colorizes the item flag block only (Common gray → Artifact red); the binding flag reads `Bound | Unbound` **(v21 rename from Droppable)**. **(v21) Zone-colored chrome:** all five pane borders (location bar/output, the full-height vertical divider, output/command bar, stats/fight, fight/map) render 5px in the current Zone's `theme_color` at ~0.75 alpha, re-tinting on zone change (`#CCCCCC` pre-first-render fallback); the combat-red takeover keeps precedence on the stats/fight border during a fight; the room separator runs slimmer at 3px so the frame outweighs the punctuation.

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

#### Written to DB on interval (every 60 seconds):

- Character XP
- Currency amounts
- Item durability values

#### In-memory only (Redis):

- Online presence keys (`shyland:online:*`) — self-healing on reconnect; TTL 90s
- Django Channels channel layer (WebSocket group routing)

**Redis is not used for combat state, effect state, or any game data where loss would affect player experience or require recovery logic.** All combat state (`CombatSession`, `CombatAction`) lives in PostgreSQL.

#### Never persisted:

- Chat messages (ephemeral; stored only if reported for moderation)
- Combat log

### 10.6 World State & Instancing

Shared persistent world — all players inhabit the same rooms. No instancing for standard content.

**Dungeons:** Semi-instanced. One party per dungeon copy. Additional parties queue or enter a parallel copy. Dungeon state resets on a timer (default: 6 hours).

**Guild halls:** Fully instanced per guild.

**The Wastelands:** Shared world but all content is dynamically scaled — no instancing required. Scaling is computed server-side at spawn time based on the highest-level player in the triggering party.

### 10.7 Admin / Super User Infrastructure

Super user tools are **v1 critical infrastructure** — not an afterthought.

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

### 10.10 Standing Engineering Tenets (v19)

Adopted as version-level law during v19, recorded here and in the architecture doc's design principles:

- **The code is definitive.** Reseeding restores the exact coded world configuration: every seed-owned table is enforced to authored values on every run, operator-added extras are deleted (cascades reported loudly), and a second consecutive run must report zero changes. Live-database edits are emergency mitigations at most — real changes go through the issue → design → brief → deploy workflow.
- **Status payloads are always built from fresh DB reads, and every engine-side mutation of player-visible state pushes an update to the client.** The complement of "the server is the authority": the server must also *speak*.
- **Contests add, quantities multiply.** Stats fed into opposed rolls grow additively on the player curve; pools and payouts may scale multiplicatively.
- **Criticals are an independent roll on successful hits** — never a band of the to-hit roll.
- **Dying interrupts combat in both directions**; revival restores exactly what the potion heals.
- **Presence is ownership-tokened**: connect takes the key unconditionally; heartbeat and delete are guarded Lua operations; the heartbeat self-heals a lost key.
- **The only legitimate exit from combat is `flee`** — `quit` refuses, and abandoning the connection abandons the character to the fight.
- **NPC-level protection is independent of room safety**: `attackable=False` refuses everywhere; safe rooms remain their own layer.

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
| Gear combat wiring (#100, v22) | No rolled item stat is currently applied to combat — player defense is raw DEX, NPC damage takes no mitigation; five of eight boss-loot groups are combat-inert. The v22 design pass rules how stat bonuses apply, whether armor mitigates, and how gear bridges the d20 contest window (the designed answer to the #89 knife-edge — and what unlocks the delve trio for non-reference builds). Includes the proc-stat semantics deferred from #68 and the #110 stat-field race. |
| Mid-combat spend refill (#109, v22) | Spending a point in END/STR/WIS refills both bars to their new max — the level-up-refill family, but stat points are bankable on demand: a free full heal in any fight. Ruling due in v22: out-of-combat-only refill, delta refills, or keep as a deliberate mechanic. |
| Mk-2 NPC HP scaling (#104) | NPC vitality does not scale with level/Mk tier (contest stats do) — the first Mk 2 spawn authored would carry level-12+ contest stats with Mk 1 HP. MUST be resolved before any Mk 2 content exists; blocks Mk 2 spawn authoring. |
|**Mounts**                             |Deferred. Super user teleportation covers testing needs in v1.                                                                     |
|**Housing**                            |Deferred. No player housing in v1.                                                                                                 |
|**Auction House**                      |Permanently excluded. Items are soulbound; no player item trading ever.                                                            |
|**Seasonal Content**                   |Permanently excluded. World freshness comes from regular content updates only.                                                     |
|**Mobile Native App**                  |Deferred. Web responsive is v1 target.                                                                                             |
|**Localization**                       |Deferred. English only in v1.                                                                                                      |
|**The Robotic Helper NPC**             |Partially designed. Unique, unreliable, mobile vendor. Full design TBD.                                                            |
|**Courier Bag / Hip Slot**             |Bags that occupy a hip slot instead of BACK, trading carry capacity for weapon slot access. Planned but not yet designed in detail.|
|**Item Identification Trigger**        |NPC sage service, Warden ability, and identification scrolls — fields and display logic are in place; trigger mechanism not yet implemented.|
|**Loot System**                        |Loot table models (`LootTable`, `LootTableEntry`) and `loot` command implemented. Corpse decay sweep and NPC respawn implemented in tick engine. Full NPC AI deferred.|
|**Super User Item Gifting (in-game)**  |Admin gifting flow via in-game command not yet implemented. Django admin gifting works.                                            |
|**Buy/Sell Commands**                  |`VendorEntry` model exists; vendor inventories can be authored in admin. No `buy` or `sell` commands yet implemented.              |
|**Zone Gate Travel Command**           |`ZoneGate` model exists; gate configurations can be authored in admin. No travel command yet implemented.                          |
|**Per-Combat-Tier NPC Behavior**       |`NpcDefinition.combat_tier` field exists (Normal/Elite/Champion/Boss/World Boss). No differentiated AI or balance behavior yet.    |
|**Durability Degradation Tick**        |Model field exists; tick logic not yet implemented.                                                                                |
|**Repair Mechanic**                    |Repair vendors and crafting-based repair not yet implemented.                                                                      |
|**Minimap**                            |`RoomVisit` fog-of-war records exist but minimap rendering not yet built.                                                          |
|**Acuity Bar Band Indicator**          |Acuity band and baseline values are now in the status payload; UI rendering of the band on the Acuity bar is deferred.            |
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
|**Battle Zones Beyond The Convergence**|Infinity City (The Convergence, Z05) and The Verdant Reach (Z01, levels 1–10) are fully seeded and live. Remaining zones (Z02–Z04, Z06–Z08) follow in zone build order; each opening also opens new level content. Note for the next zone pass: the Convergence itself has no commerce yet — the Reach's checkpoint NPCs are the game's only vendors and repairers (architecture doc §7).|
|**Checkpoint & Obelisk Fast-Travel Network**|**Design complete (Section 2.11); implementation pending.** Global network, destination-only checkpoints, per-character permanent revelation, free `travel` command, obelisk-sourced safe rooms, Shards. Open implementation-mapping questions for brief time: relationship to the existing `ZoneGate` model; whether revelation reuses `RoomVisit`; message pool machinery; Shard representation.|
|**Outleveled-Content XP Reduction**    |**Designed and in v18** (carried in the engine mechanics brief). Full XP within the NPC's Mk band (band top = Mk tier × 10); −20% per level beyond it; multiplier floor 10%; absolute minimum 1 XP — outleveled kills always pay something.|
|**Hide & Carapace Crafting**           |Animal Hide and Insect Carapace are vendor-sellables only for now. Giving players something to make with them is deferred — much later, alongside the crafting system (Section 6.13).|
|**NPC Dialogue — deeper tiers**|The v19 listening system (Section 7.6) shipped keyword maps, greetings, and departure reactions for the Convergence roster. Future tiers: keyword vocabularies across battle zones, quest hooks, reputation-conditional responses, and Sirius-class persistent-memory entities.|
|**Combat loot blocking**|Deferred by v19 ruling (issue filed): `loot`/`pickup`/`equip` restrictions during combat, corpse-decay interaction.|
|**Attunement / home spawn & shard travel senders**|Deferred by v19 ruling (issues filed): player-set respawn via `attune` at network nodes; whether checkpoint shards may initiate travel.|
|**Co-op combat rules**|Emergent v19 finding: shared-target combat exists accidentally (per-character sessions, racy kill credit, per-session NPC double actions). Kill credit, XP/loot sharing, and session semantics need a designed system.|
|**Sirius — Special Vendor Entity**     |Unique bipedal feline special vendor (Section 6.12). Wish mechanics and persistent memory system need a dedicated design session before implementation.|
|**Stat Respec Mechanic**               |Allow players to rebalance already-spent stat points using in-game currency. Needs a dedicated design session.|

-----

*Document version 21.0 — Shyland, Closed*
*All systems subject to revision during development.*
