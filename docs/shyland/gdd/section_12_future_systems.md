## 12. Future Systems

These are explicitly deferred — not in scope for v1, documented here for future design sessions:

|System                                 |Notes                                                                                                                              |
|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| Longevity's first drain (#70) | Nothing consumes `longevity_current` yet — the slow-burn bar is regen-only scaffolding. Candidates: flee exertion (the fiction already charges for it), sustained actions, DoT budgets. A features-version question. |
| Identification visibility redesign (#80) | Knowledge-by-holding: mystery to observers, `examine` reveals without pickup, pickup unlocks, drop re-veils. Includes the examine double-line cleanup and the durability-leak question. |
| Zones-and-travel version (#30, #38, #41, #95) | The B4 bucket dropped whole from v22 by ruling: shard travel senders, obelisk attunement (player-set home destinations — `home` ships pointing at the Heart until then), Convergence-completion gating, and the ring's missing Area all belong to a future version dedicated to zones and travel, where new destinations force the questions as requirements rather than speculation. v22 kept only the destination-listing order. |
| Pluralization subsystem (#126) | Aggregate transactional output ships with the deliberately plural-free count form (`Healing Draught Mk 1 ×100`). The upgrade: forward pluralization rules, an authored plural-name override for irregulars, multi-word head-noun handling — then the aggregates speak natural English. |
| Ranged proc damage (#127) | "Between X and Y" proc floors — a second number per proc is a generation + stat-table + display + rolled-stat structure change: a new weapon kind in the midpoint-and-spread family, for a future itemization version. |
| Authored per-item armor bases (#129) | A real armor field on ItemDefinition would let a set guarantee minimum coverage, with rolled `physical_resist` as bonus above it; v22's derived slot-weight table retires gracefully into it. Same family as #127's itemization deepening. |
| Secondary-stat curves vs Mk band growth (#130) | Flat-value gear effects that matter at Mk 1 shrink toward irrelevance by Mk 3 if curves stay as seeded (midpoints grow +0.2/band while NPC numbers roughly double). A retune, not a rework — audit when Mk 2 content is designed, same era as #104. |
| Mk-2 NPC HP scaling (#104) | NPC vitality does not scale with level/Mk tier (contest stats do) — the first Mk 2 spawn authored would carry level-12+ contest stats with Mk 1 HP. MUST be resolved before any Mk 2 content exists; blocks Mk 2 spawn authoring. |
| Player macro/alias system (#125) | Client- or server-side command aliases. Unruled; filed during B3 planning. |
| Repair kit (#134) | The seeded repair-kit consumable has no wired effect. Unruled. |
| The firehose (#33, #37) | Universal event logging: every command, every output, every event through the envelope choke point. `sudo`'s listener arrives with it. |
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
|**Battle Zones Beyond The Convergence**|Infinity City (The Convergence, Z05) and The Verdant Reach (Z01, levels 1–10) are fully seeded and live. Remaining zones (Z02–Z04, Z06–Z08) follow in zone build order; each opening also opens new level content. Note for the next zone pass: the Convergence itself has no commerce yet — the Reach's checkpoint NPCs are the game's only vendors and repairers (architecture doc §7).|
|**Outleveled-Content XP Reduction**    |**Designed and in v18** (carried in the engine mechanics brief). Full XP within the NPC's Mk band (band top = Mk tier × 10); −20% per level beyond it; multiplier floor 10%; absolute minimum 1 XP — outleveled kills always pay something.|
|**Hide & Carapace Crafting**           |Animal Hide and Insect Carapace are vendor-sellables only for now. Giving players something to make with them is deferred — much later, alongside the crafting system (Section 6.13).|
|**NPC Dialogue — deeper tiers**|The v19 listening system (Section 7.6) shipped keyword maps, greetings, and departure reactions for the Convergence roster. Future tiers: keyword vocabularies across battle zones, quest hooks, reputation-conditional responses, and Sirius-class persistent-memory entities.|
|**Co-op combat rules**|Emergent v19 finding: shared-target combat exists accidentally (per-character sessions, racy kill credit, per-session NPC double actions). Kill credit, XP/loot sharing, and session semantics need a designed system.|
|**Sirius — Special Vendor Entity**     |Unique bipedal feline special vendor (Section 6.12). Wish mechanics and persistent memory system need a dedicated design session before implementation.|
|**Stat Respec Mechanic**               |Allow players to rebalance already-spent stat points using in-game currency. Needs a dedicated design session.|

-----

*Document version 22.0 — Shyland, Closed*
*All systems subject to revision during development.*
