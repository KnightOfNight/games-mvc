# Shyland — Game Design Document

**Version 10.0 — Working Draft**

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

Long ago, the world of Shyland was a single coherent reality. A catastrophic event known as **The Fracture** shattered dimensional membranes, pulling fragments of other realities into permanent collision with this one. The result is a patchwork world where zones retain their original genre identity but exist in geographic proximity to radically different ones.

Nobody fully understands The Fracture. Scholars debate its cause. Some zones have adapted to their neighbors; others remain hostile to anything foreign. This tension is a primary driver of narrative and conflict.

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
|Z05    |The Convergence    |All genres collide — the world’s central hub    |Sanctuary   |
|Z06    |The Iron Deeps     |Steampunk underground                           |Advanced    |
|Z07    |The Pale Shore     |Cosmic horror / lovecraftian ocean              |Endgame     |
|Z08    |The Wastelands     |Infinite scaling zone — always level-appropriate|All levels  |

**The Convergence (Z05)** is the game’s social hub — a permanent sanctuary zone where PvP is disabled, vendors of all types exist, and players from all backgrounds congregate. Lore-wise, it is the epicenter of The Fracture. It is also the default logout and recall destination.

**The Wastelands (Z08)** is a special infinite scaling zone — see Section 2.7.

### 2.3 Areas

An **Area** is a named grouping of rooms within a zone that share a common ambient context. Areas are the middle layer of the world hierarchy — they sit between Zone and Room, giving world builders a tool to express shared atmosphere without repeating it in every room description.

```
Zone → Area → Room
```

Areas are **optional** — a room does not have to belong to an area. Standalone rooms (a remote wilderness clearing, a unique landmark) exist without one. But any multi-room location with a coherent identity — a marketplace, a dungeon wing, a ship, a temple — should be modelled as an Area.

#### What an Area Contains

- **Name** — the location name players see as part of their room header (e.g., “The Eastern Bazaar”)
- **Area description** — shared ambient prose that applies to all rooms in the area. Describes the general atmosphere: sounds, smells, lighting, the feel of the place. Written once, displayed in every room that belongs to the area.

#### How Areas Appear to Players

When a player enters a room that belongs to an area, their output has two layers:

1. **Header:** `[ Area Name — Room Name ]` — they always know where they are in the broader location
1. **Area description** (if present) — the shared ambient text, shown above the room-specific description
1. **Room description** — the specific detail of this individual space

**Example — The Eastern Bazaar:**

```
[ The Eastern Bazaar — Stall 3: The Armorer ]

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

- **Short name** — displayed in the room header alongside the area name if present (e.g., `[ The Eastern Bazaar — Stall 3: The Armorer ]`)
- **Long description** — the room-specific prose a player reads on entering or using the `look` command
- **Brief description** — one-line version shown when the player has visited before (toggleable)
- **Area** — optional parent area providing shared ambient context (see 2.3)
- **Exit list** — directional links to adjacent rooms (N, S, E, W, U, D, and custom named exits)
- **Flags** — booleans that modify room behavior (see below)
- **Contents** — current list of players, NPCs, and items present

#### Room Flags

|Flag        |Effect                                                             |
|------------|-------------------------------------------------------------------|
|`SAFE`      |No combat allowed, NPCs won’t aggro                                |
|`PVP`       |PvP is enabled in this room                                        |
|`DARK`      |Players need a light source to see descriptions                    |
|`INDOORS`   |Weather effects don’t apply                                        |
|`WATER`     |Swimming/drowning rules apply                                      |
|`NO_RECALL` |Players cannot use recall/teleport abilities                       |
|`RADIATION` |Periodic radiation damage (wasteland zones)                        |
|`HOLY`      |Undead and demonic entities take passive damage                    |
|`MAGIC_DEAD`|Spell and tech abilities disabled                                  |
|`SCALED`    |Room and its contents scale to entering player’s level (Wastelands)|

### 2.5 The Visual Map Layer

Rooms belong to a coordinate grid within their zone. The client renders a small ASCII/SVG minimap (configurable size, default 5×5 tiles centered on the player) showing:

- Current room (highlighted)
- Adjacent visited rooms
- Unexplored exits (shown as dotted connections)
- Special room types (shops, quest givers, danger) via icon overlays
- Area boundaries — rooms sharing an area are visually clustered and labelled with the area name

The map does not replace text navigation — it is supplementary. Players can hide it. The map only reveals rooms the player has personally visited (fog of war).

### 2.6 Travel & Navigation

Players move using directional commands: `north`, `south`, `east`, `west`, `up`, `down` (and abbreviations: `n`, `s`, `e`, `w`, `u`, `d`). Named exits use the exit name directly (e.g., `enter portal`).

**Movement costs no action economy in normal exploration.** Combat changes this (see Section 5).

Special travel options:

- **Recall scroll** — teleports player to their bound recall point (default: The Convergence)
- **Zone gates** — fixed fast-travel points between zones, requiring discovery first

Mounts are deferred to a future version.

### 2.7 The Wastelands — Infinite Scaling Zone

The Wastelands is a post-apocalyptic expanse that serves as the game’s permanent endgame safety valve. It has no fixed difficulty — the zone scales to match any entering character’s level.

**Scaling rules:**

- Enemy stats, HP, and damage scale to the entering player’s level
- Loot scales to match — a level 200 character finds level 200 loot (using the Mk system — see Section 6.3)
- In a party, the zone scales to the highest level member
- XP rewards scale appropriately — The Wastelands always provides meaningful XP regardless of player level

**Design purpose:**
When no higher-level content has yet been published, The Wastelands ensures players always have somewhere challenging to go. It is not a substitute for purpose-built high-level zones but bridges the gap between content updates.

### 2.8 Logout Persistence

When a player logs out, their character remains in the world at their exact location for 60 seconds (allowing them to be targeted in PvP zones — a deliberate risk of logging out in dangerous areas), then fades from the world. On next login, they appear at the exact room where they logged out.

There is no safe logout room. Players are responsible for where they choose to go offline.

-----

## 3. Character System

### 3.1 Character Creation

New players choose:

1. **Origin** (replaces traditional race — see 3.2)
1. **Archetype** (replaces traditional class — see 3.3)
1. **Name** (profanity filtered, uniqueness enforced)
1. **Portrait** (selected from a curated set grouped by Origin; visual element displayed in UI)

### 3.2 Origins

Origins define where a character came from — which fragment of reality they were pulled from. They provide flavor, starting bonuses, and passive traits. They do not lock players out of any Archetype.

|Origin     |Genre Flavor                  |Passive Trait                                                                    |
|-----------|------------------------------|---------------------------------------------------------------------------------|
|Highborn   |Classic fantasy noble         |+10% XP from quest completion                                                    |
|Feral      |Wilderness / tribal           |+15% movement, +1 to foraging rolls                                              |
|Streetborn |Cyberpunk urban               |Hacking attempts cost 10% less energy                                            |
|Irradiated |Post-apocalyptic              |Radiation resistance, Vitality regenerates slowly in rad zones                   |
|Undying    |Gothic horror / undead-touched|Reduced death penalty; small life drain on melee hits                            |
|Machinekind|Steampunk construct           |Cannot be poisoned; cannot be healed by magic (repairs only)                     |
|Voidtouched|Cosmic horror survivor        |Bonus to eldritch damage; natural Acuity resistance at both extremes of the scale|

Each Origin has a distinct **Acuity baseline** — the natural resting point their Acuity gravitates toward when no external forces are acting on it. A Voidtouched character’s baseline is shifted toward the lower end of the scale; they are accustomed to the strange. A Highborn’s baseline sits in the mid-range.

Origins can have social/narrative consequences — some NPCs react differently to Machinekind in a fantasy village, or to an Irradiated in a pristine elven glade.

### 3.3 Archetypes

Archetypes define combat role and skill access. Each spans genre — a Blade is equally a swordsman, a street samurai, or a wasteland knife-fighter depending on equipment and flavor choices.

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

The **Warden** archetype has expanded responsibility in Shyland — beyond healing Vitality, Wardens have tools to actively manage party members’ Acuity, nudging allies toward their optimal range when combat stress or eldritch exposure has shifted them too far in either direction.

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

**No hard level cap.** Progression is continuous. In practice, a soft cap exists at the frontier of published content — XP return diminishes sharply below a character’s level, so grinding low-level content eventually becomes inefficient. The Wastelands always provides a level-appropriate alternative.

**XP Sources:**

- Killing enemies (scaled to level differential)
- Quest completion (primary XP source)
- Exploration (first visit to a new room grants a small XP bonus)
- Crafting milestones
- PvP kills in PvP zones (reduced rate, separate PvP XP track)

**On Level Up:**

- +5 stat points to distribute freely
- +1 skill point
- Vitality/Longevity/Mana recalculated
- New abilities may unlock at certain level thresholds

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

**Carry limit:** Base carry weight is STR × 10. Bags equipped in valid slots add a carry bonus on top of that. No off-body storage, no bank, no shared stash.

### 3.7 Death & Resurrection

Death in Shyland is meaningful but not brutal:

- Player reaches 0 Vitality → enters **Dying** state (30-second window)
- During Dying state: the character can use revival consumables or abilities on themselves; any other player in the room can also use a revival item or ability on them — no group membership required
- All commands except `use` are blocked while in Dying state
- If not revived within 30 seconds → **Dead**. Player respawns at their bound recall point (default: The Convergence) with full bars
- On death: all active `EffectInstance` rows are cleared; all pending combat actions are cleared; the `CombatSession` ends
- **XP loss:** 10% of current XP (cannot lose a level). This penalty only applies at level 10 and above — new players below level 10 take no XP penalty on death
- **Durability loss:** All equipped items with `takes_durability_loss=True` lose 10% durability per death. After 10 deaths without repair, an item breaks (`is_broken=True`). Bags and jewelry are naturally exempt because their definitions have `takes_durability_loss=False`. The flag on `ItemDefinition` is the only gate — any item type with the flag set takes the penalty.
- In PvP zones only: chance to drop one non-equipped carried item
- A **Death Shard** item is left at the death location; player can retrieve it within 30 minutes to recover any dropped item

**Hardcore Mode** (optional, on character creation): permadeath. Character deleted on death. Hardcore characters are flagged visually and have a separate leaderboard.

-----

## 4. The Three Bars — Vitality, Acuity, Longevity

This is one of Shyland’s most distinctive systems. All characters have three resource bars, each governing a different dimension of their condition. They are not separate — they interact and influence each other. The separation into three bars is a mechanical convenience, not a philosophical statement that mind and body are distinct.

### 4.1 Vitality

**What it is:** The body’s immediate physical condition.

**Mechanical effects:**

- Melee damage dealt and received scales with current Vitality as a percentage of maximum (low Vitality = hitting and being hit harder proportionally)
- Movement speed degrades at low Vitality
- Physical resistance degrades at low Vitality
- Reaching 0 Vitality triggers the Dying state

**Recovery:** Healing spells, medkits, potions, natural regen (slow, out of combat only).

**Machinekind note:** Machinekind characters cannot be healed by magic. Their Vitality is restored only through repair items and the Machinist archetype’s self-repair abilities.

### 4.2 Acuity

**What it is:** The mind’s dynamic state. Not a scale from broken to perfect — a spectrum with a sweet zone that varies by Origin. Being too high or too low are both problems.

**There is no universally “correct” Acuity value.** Each Origin has a natural baseline and a tolerance band. Characters are most effective when operating within their band.

**Acuity scale:** Acuity is stored as a float in the range **0.1 to 1.9**, in 0.1 increments. The stored value IS the damage modifier applied in combat — 1.0 is neutral, above 1.0 is a bonus, below 1.0 is a penalty. Per-origin baseline and band values are defined in `_ACUITY_DEFAULTS` in `models.py`.

| Value | State | Effect |
|---|---|---|
| 1.9 | Maximum focus | +90% damage (single-target only) |
| 1.1–1.8 | Focused | Proportional damage bonus |
| 1.0 | Optimal | No modifier |
| 0.2–0.9 | Scattered | Proportional damage penalty |
| 0.1 | Minimum | −90% damage |

**AoE rule:** When a character hits multiple targets with an area-of-effect attack, the Acuity bonus (above 1.0) applies to exactly one focus target. The penalty (below 1.0) applies to all targets regardless.

**Per-Origin defaults:**

| Origin | Baseline | Band low | Band high |
|---|---|---|---|
| Highborn | 1.0 | 0.85 | 1.15 |
| Feral | 0.95 | 0.80 | 1.10 |
| Streetborn | 1.0 | 0.85 | 1.15 |
| Irradiated | 0.90 | 0.75 | 1.05 |
| Undying | 0.80 | 0.65 | 1.00 |
| Machinekind | 1.05 | 0.90 | 1.20 |
| Voidtouched | 0.70 | 0.40 | 1.30 |

**Effects of Acuity too LOW (distracted, scattered, overwhelmed):**

- Spell effectiveness degrades — spells may fizzle, truncate, or misfire
- Ranged aim drifts — hit chance penalties
- Situational awareness collapses — the game shows fewer ambient messages, sneaking enemies may go undetected entirely
- At severe lows: combat log entries may be garbled, phantom sounds described in room text

**Effects of Acuity too HIGH (hyper-focused, tunnel vision):**

- Devastating against a single target — bonus damage and accuracy on focused attacks
- Flanking enemies and ambushes from outside the focus cone are not detected
- Peripheral combat events (an ally taking damage, an enemy arriving) may be missed
- A Shade’s dream scenario to exploit against opponents

**The sweet zone:** The range between too-low and too-high where the character operates optimally. Wider for some Origins (Voidtouched are accustomed to extremes), narrower for others.

**What shifts Acuity:**

- Eldritch damage and prolonged exposure to Pale Shore zone pushes Acuity toward extremes
- Stress effects from combat, particularly losing allies or taking massive damage, can spike or crash it
- Consumables and spells can deliberately shift Acuity in either direction — a “focus” potion before a boss fight is a legitimate tactical choice, with the flanking blindness risk as the tradeoff
- The Warden archetype has party-wide Acuity management tools
- Rest and time naturally return Acuity toward a character’s baseline (Acuity drift — not yet implemented)

**Manipulation:** Players can actively shift their own Acuity intentionally. Pushing it high before a single-target duel, then managing the aftermath, is a valid play style. The system rewards players who understand their character’s band and manage it actively.

### 4.3 Longevity

**What it is:** The slow burn. Accumulated resilience — the will and capacity to keep going over time.

**Mechanical effects:**

- Controls stamina duration — how long a character can sprint, sustain effort, or maintain concentration
- Governs duration of sustained effects: a character’s own damage-over-time effects last longer at high Longevity; enemy DoTs applied to them expire faster
- Controls the window of long-lasting buffs and debuffs
- At low Longevity: sustained spells collapse early, long fights become increasingly punishing

**Recovery:** Longevity recovers slowly — much slower than Vitality. Short rests help slightly. Full recovery requires extended downtime or specific Warden abilities. It is the hardest bar to restore and the one players are most likely to mismanage over a long dungeon run.

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

**Aggro on room entry:** When a player moves into a room with aggressive NPCs, the room description is suppressed. Instead, each aggressive NPC sends an announce message (e.g. `"A Fracture Wraith snarls and moves to attack!"`). The player has the duration of one full combat round (3 seconds) before the NPC's first attack fires. During this window the player can queue an attack of their own — if they are fast enough, they act first in round 1.

Once combat begins, all participants are locked in until one side flees, dies, or combat ends naturally.

**`CombatSession`:** Each fight is represented by a `CombatSession` row in the database (not in Redis). A session tracks which characters and NPCs are participating, the room, and round state. In v1, one character fights alone; the session model is future-ready for group combat via an M2M relationship. One character can fight multiple NPCs simultaneously — additional NPCs can be added to an existing session via `kill`/`attack`.

### 5.3 The Action Economy

Each combat round (3 seconds = 3 engine ticks), a character may take **1 Primary Action** — attack, use an ability, use an item, or flee.

**Two-path command handling:** Non-combat commands (`look`, `say`, movement, inventory, etc.) execute immediately and synchronously when typed. Combat commands typed during an active fight are written to a DB queue (`CombatAction`); the tick engine processes all queued actions at each round boundary. This keeps non-combat interactions instant while ensuring combat resolution is synchronized and auditable. The consumer checks whether the character is in an active `CombatSession` and routes accordingly.

**Auto-attack:** If no player action is queued when a round fires, the tick engine creates an auto-attack action targeting the first NPC in the session. Players are never idle.

**Initiative (rounds 2+):** Each round after the first, initiative is rolled for all participants: `d10 + DEX + PER`. Highest total acts first; ties go to the player. In round 1, whoever initiated combat acts first (player if they used `kill`/`attack`; NPC if they aggro’d on room entry).

### 5.4 Attack Resolution

```
1. Hit check:
   d100 + attacker DEX vs. target dodge (target DEX)
   → Miss:     roll < target_dodge
   → Graze:    target_dodge ≤ roll < target_dodge + 10  (50% damage)
   → Hit:      target_dodge + 10 ≤ roll < target_dodge + 30  (100% damage)
   → Critical: roll ≥ target_dodge + 30  (150% damage)

2. Damage calculation:
   base_damage    = weapon damage roll (random within midpoint ± spread)
   stat_bonus     = relevant stat value (STR melee / DEX ranged / INT spells)
   acuity_mod     = character's current Acuity value (0.1–1.9 float; IS the modifier)
                    Bonus (>1.0) applies to the focus target only in AoE.
                    Penalty (<1.0) applies to all targets.
   durability_mod = performance multiplier from weapon's durability table (1.0 = no penalty)
   raw_damage     = (base_damage + stat_bonus) × acuity_mod × durability_mod

3. Hit multiplier applied:
   final_damage = raw_damage × hit_multiplier (0.5 graze / 1.0 hit / 1.5 critical), minimum 1

4. Mitigation (future):
   final_damage = final_damage - target defense value (minimum 1)

5. Elemental/type resistances apply as percentage reduction after armor (future)
```

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
|Shadow   |Shade abilities, dark magic             |Reduces target’s defense temporarily                    |

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

- A **combat tier** (Normal, Elite, Champion, Boss, World Boss)
- **Archetype flags** governing tactics
- **Effects list** — each NPC definition carries a list of `NpcEffect` entries. Each entry links to an `EffectDefinition` and has a per-entry `effect_chance` (0.0–1.0). On each NPC attack, every entry is rolled independently; those that fire are applied via the shared `EffectInstance` system and appended to the attack message. An NPC with no effects is a pure auto-attacker. Higher-Mk NPC definitions can carry longer effect lists or higher-magnitude effects to increase difficulty. Telegraph and phase-change mechanics are deferred to later content work
- **Loot tables** — normalized `LootTable` and `LootTableEntry` models; one table can be shared across multiple NPC definitions

NPCs are defined by an **`NpcDefinition`** (the template — name, stats, loot table, behavior flags, respawn timer) and spawned as **`NpcInstance`** rows (live copies in specific rooms at a specific Mk tier). Mk tier is instance-specific — the same definition can spawn as Mk 1 goblins in a starter zone and Mk 5 goblins in a harder one.

**On death:** a `Corpse` is created from the `NpcInstance`. The `NpcInstance` row is deleted; a new row is created when the respawn timer fires. Dead NPCs are never reused — respawn always creates a fresh instance.

**Corpses** are temporary loot containers in the room. Only the killing character may loot items from a corpse. Currency is visible to all via `examine` but only transferred to the killer. Corpses are deleted when fully looted; unlooted corpses are deleted after `CORPSE_DECAY_MINUTES` (10 minutes) by the decay sweep (deferred to tick engine).

**Currency drops** are rolled at death using the formula: `random.randint(currency_drop_min × mk_tier, currency_drop_max × mk_tier)`. Currency display respects zone aliases via `display_for_zone()`.

Bosses have multi-phase fights with behavioral changes at HP thresholds. Some boss abilities specifically target Acuity — a screaming eldritch horror doesn’t just deal damage, it pushes the entire party’s Acuity toward an extreme.

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

All currency is stored as a single `bigint` in the database representing the total amount in **copper** — the base unit. Display and conversion are purely presentational. Python’s arbitrary-precision integers mean there is no practical ceiling.

The tier system follows an escalating-multiplier pattern: each tier’s conversion factor is an order of magnitude larger than the previous tier’s.

|Tier|Engine Name |Multiplier from Previous|Value in Copper|
|----|------------|------------------------|---------------|
|1   |**Copper**  |— (base unit)           |1              |
|2   |**Silver**  |×10                     |10             |
|3   |**Gold**    |×100                    |1,000          |
|4   |**Platinum**|×1,000                  |1,000,000      |
|5   |*(future)*  |×10,000                 |10,000,000,000 |

The multiplier between tiers is itself multiplied by 10 at each step. High-tier currency is genuinely rare — not just a bigger number with the same feel.

**Conversion is automatic.** When a player’s copper total crosses a tier threshold, the display rolls up. Players never manually convert.

**Display format:** Show the minimum denominations needed. Examples:

- 1,543 copper → `1 gold, 5 silver, 43 copper` (never show zero-value tiers)
- 10 copper → `10 copper`
- 1,000,000 copper → `1 platinum`

#### Player-facing names

In standard zones, players see the engine names: Copper, Silver, Gold, Platinum.

#### Local Currency (zone-specific display aliases)

Some zones use local currency names for flavor — the math is identical, only the display strings differ. A ghost dropping “Soul Tokens” is giving the player copper under the hood. The zone or enemy definition carries a `currency_display` config that maps the four tier names to local equivalents.

|Zone               |Copper alias|Silver alias|Gold alias |Platinum alias|
|-------------------|------------|------------|-----------|--------------|
|Standard           |Copper      |Silver      |Gold       |Platinum      |
|Ashenveil Cathedral|Soul Token  |Grave Mark  |Death Crown|*(rare)*      |
|The Neon Sprawl    |Credit      |Kilocredit  |Megacredit |*(rare)*      |

Local currency received is converted to the player’s copper total immediately on pickup.

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

A higher rarity item of the same Mk tier always rolls higher stats on average — and can roll higher than a lower rarity item’s ceiling.

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

The performance penalty applies to the item’s stat contributions and weapon damage output. At 0%, the item stops functioning entirely until repaired.

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

Some items carry a hidden curse. The curse is not visible in the item’s description — nothing reveals it before the item is equipped, unless:

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

This means the same physical item can be identified to one character and unidentified to another, depending on their history with it. There is no shared identification state across characters.

#### Permanently Unidentifiable Items

A super user can mark a specific item instance as `is_unidentifiable = True`. No in-game mechanism — NPC sage, Warden ability, identification scroll — can ever identify such an item. The mystery name and mystery description are all any player will ever see through normal play.

This is intended for one-of-a-kind Artifacts whose true nature is a permanent secret of the game world itself. Players can examine them, read whatever lore the super user wrote into the mystery description, and speculate — but the mechanical truth never surfaces.

#### Identification Trigger

The in-game mechanism for identifying items — NPC sage service, Warden class ability, consumable identification scroll — is designed but not yet implemented. See Section 12.

#### Interaction with Curses

An unidentified item may also be cursed. Identifying the item reveals both its true nature and its curse status simultaneously, allowing the player to make an informed decision before equipping. Without identification, equipping a cursed item is a risk the player takes knowingly.

### 6.9 The Effect System

All temporary and persistent effects in Shyland — consumable effects, curse effects, combat ability effects — use a shared vocabulary:

**EffectDefinition** — the template for an effect type. Defines what kind of effect it is, the valid magnitude range, the valid duration range, and whether it scales with Mk tier.

**EffectInstance** — a specific application of an effect to a character. Stores the actual magnitude and duration rolled at application time, when it was applied, when it expires, and what removed it.

#### Effect Types

|Type                |Description                                |
|--------------------|-------------------------------------------|
|`restore_vitality`  |Immediate or over-time Vitality restoration|
|`restore_acuity`    |Nudges Acuity toward baseline              |
|`restore_longevity` |Longevity restoration                      |
|`dot_vitality`      |Vitality damage over time                  |
|`dot_acuity`        |Acuity disruption over time                |
|`dot_longevity`     |Longevity drain over time                  |
|`shift_acuity_high` |Pushes Acuity upward (focus effect)        |
|`shift_acuity_low`  |Pushes Acuity downward (scatter effect)    |
|`stat_bonus`        |Temporary stat increase                    |
|`stat_penalty`      |Temporary stat reduction                   |
|`durability_restore`|Restores item durability                   |
|`curse_generic`     |Persistent curse effect                    |

The vocabulary grows as content grows — new effect types are additive.

#### Application Context

The same EffectDefinition can be applied with different magnitude and duration depending on source:

- A consumable applies it once with fixed parameters for that item type
- A combat ability applies it with parameters scaled to the caster’s level and stats
- A cursed item applies it with parameters appropriate for hours or days of wear

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
- Party members’ Vitality, Acuity, and Longevity visible in side panel UI

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

Quests given by NPCs via `talk` or `ask`. Quest givers flagged in the client UI.

Quests have: journal entry, tracked objectives, completion trigger, and branching outcomes for Investigation quests. Quest chains unfold zone stories and may permanently alter zone state.

### 8.3 NPC Dialogue System

NPCs respond to `talk`, `ask <topic>`, `say <keyword>`. Conditional responses based on reputation, quest state, Origin, Archetype. NPCs remember if you’ve helped or harmed them.

Genre collision is reflected in NPC dialogue: *“I’ve never seen armor like that. What did you say it’s made of? ‘Kevlar’?”*

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

If no exit exists in the requested direction, the server responds with a message and no movement occurs. Movement has no action economy cost outside of combat.

#### Exploration

|Command|Alias|Description                                                                  |
|-------|-----|-----------------------------------------------------------------------------|
|`look` |`l`  |Display the current room’s full description, exits, and other players present|

#### Communication

|Command     |Alias|Description                             |
|------------|-----|----------------------------------------|
|`say <text>`|—    |Speak to all players in the current room|

#### Information

|Command|Alias|Description                                                     |
|-------|-----|----------------------------------------------------------------|
|`who`  |—    |List all players currently online (uses Redis presence tracking)|
|`help` |`?`  |Display available commands and current room exits               |

#### Character & Inventory

|Command    |Alias|Description                              |
|-----------|-----|-----------------------------------------|
|`inventory`|`inv`|Show equipped items and carried inventory|

#### Item Interaction

|Command         |Alias|Description                                         |
|----------------|-----|----------------------------------------------------|
|`pickup <item>` |`p`  |Pick up a loose item from the current room          |
|`drop <item>`   |—    |Drop a carried, unbound item into the current room  |
|`equip <item>`  |`eq` |Equip a carried item into an equipment slot         |
|`unequip <item>`|`uneq`|Move an equipped item back to carried inventory   |
|`use <item>`    |—    |Use a consumable item                               |
|`examine <item>`|`ex` |Inspect an item, live NPC, or corpse in detail      |

**#### Corpse Interaction

|Command                  |Alias|Description                                                        |
|-------------------------|-----|-------------------------------------------------------------------|
|`loot [corpse] [item]` |—    |Loot a corpse; bare `loot` takes everything from the most recent kill|

**Corpse noun syntax:** `loot` targets the most recently created corpse in the room. `loot 2.corpse` targets the second most recent. `loot goblin` targets the first corpse whose name contains “goblin”. An item noun may follow: `loot 2.corpse sword` loots the first sword from the second corpse. Only the killing character may loot items. Currency is always transferred on first loot of a corpse regardless of item noun. Bare `loot` after a corpse is emptied automatically targets the next most recent corpse in the room.

Item noun syntax:** Classic MUD convention applies to all item commands. `sword` targets the first item whose name contains "sword"; `2.sword` targets the second; `all` targets every eligible item (where supported by the command). Matching is case-insensitive and works against the item's display name — so unidentified items can be referenced by their mystery name.

The `help` output is context-aware — it shows only the exits that actually exist in the current room, not a fixed list of all possible directions.

The unknown command response directs players to `help`: *“Unknown command. Type ‘help’ for a list of commands.”*

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
|`talk` / `ask <topic>`|Initiate NPC dialogue                             |
|`forage`              |Gather plant/organic materials in applicable rooms|
|`mine`                |Gather ore/mineral materials in applicable rooms  |
|`salvage`             |Disassemble items or gather tech components       |
|`harvest`             |Gather zone-specific resources                    |

#### Combat (Section 5)

|Command                            |Description                  |
|-----------------------------------|-----------------------------|
|`kill <target>` / `attack <target>`|Initiate combat with a target|
|`flee`                             |Attempt to escape combat     |

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
- Every unrecognised command gets a helpful redirect, not a bare error. Currently: *“Unknown command. Type ‘help’ for a list of commands.”*
- `help` output must stay current as new commands are added. When a new command is implemented, update both this section of the GDD and the `cmd_help()` method in `consumers.py`.

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
|**Auth**                     |Django built-in auth; character name from `user.profile.gamer_tag`|
|**Deployment**               |Docker Compose: nginx → Daphne → Django/Redis/Postgres            |

All game logic runs server-side. The client is a dumb terminal — it sends text commands and renders JSON output. No game state is trusted from the client.

### 10.2 Client Architecture

Web-only. Responsive down to phone screen size. No native app.

```
┌─────────────────────────────────────────────────────────┐
│  [MINIMAP]          [THREE BAR STATUS — V / A / L]      │
├──────────────────────────────┬──────────────────────────┤
│                              │                          │
│   MAIN OUTPUT PANE           │   SIDE PANEL             │
│   (scrolling text log)       │   (party / inventory /   │
│                              │    character sheet —     │
│                              │    tabbed)               │
├──────────────────────────────┴──────────────────────────┤
│  [COMBAT TICK BAR]                                      │
├─────────────────────────────────────────────────────────┤
│  > INPUT LINE                                 [SEND]    │
└─────────────────────────────────────────────────────────┘
```

**Accessibility:** Semantic HTML throughout. ARIA live regions on the output pane (`aria-live="polite"` for normal output, `aria-live="assertive"` for combat/urgent events). All functionality accessible via keyboard. Screen reader compatible from day one.

**Status bar:** Displays all three bars — Vitality (V), Acuity (A), Longevity (L) — with visual indication of the Acuity “sweet zone” band for the current character’s Origin.

**Phone layout:** Side panel collapses to a bottom drawer. Minimap collapses to an icon that expands on tap. Input line remains always accessible.

**Single visual theme** — no colorblind mode or high-contrast mode in v1.

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
1. **`process_npc_respawn()`** — creates fresh `NpcInstance` rows for dead NPCs whose `respawn_at` has passed
1. **`process_effect_expiry()`** — deactivates `EffectInstance` rows whose `expires_at` has passed and notifies the player

Each processor runs every tick regardless of whether it has work to do. Only `process_combat()` performs additional internal gating — a combat round only resolves when `tick_counter % COMBAT_ROUND_TICKS == 0` on the session.

**Global tick rate:** 1 second. Combat round = 3 ticks (`COMBAT_ROUND_TICKS = 3`). Fixed — not adjustable per player or per NPC.

**Planned but not yet implemented:** Acuity drift (characters’ Acuity drifting toward their Origin baseline each tick), DoT/HoT per-tick stat application, zone events.

NPC AI runs server-side. No game state is trusted from the client.

### 10.5 Persistence Model

#### Written to DB on change (event-driven):

- Character stats, all three bars (Vitality/Acuity/Longevity current values), inventory, position
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
- Adjust any character’s stats, bars, currency, or position
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

## 11. Admin & Content Tools

### 11.1 Builder System

Web-based builder interface (separate from game client) for authorized staff:

- Create/edit zones, areas, rooms (all fields, flags, exits, coordinates)
- Create/edit NPCs (stats, loot tables, dialogue trees, Acuity-affecting abilities)
- Create/edit ItemDefinitions (all properties, scaling parameters, secondary stat pools, durability tables, effects)
- Create/edit EffectDefinitions (effect type, magnitude range, duration range, scaling)
- Create/edit quests (objectives, rewards, branching logic)
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
|**Durability Degradation Tick**        |Model field exists; tick logic not yet implemented.                                                                                |
|**Repair Mechanic**                    |Repair vendors and crafting-based repair not yet implemented.                                                                      |
|**Brief Toggle**                       |First visit shows full room description; repeat visits show `brief_description`. Not yet implemented.                              |
|**Minimap**                            |`RoomVisit` fog-of-war records exist but minimap rendering not yet built.                                                          |
|**Sanity / Acuity Edge Cases**         |Full design of Voidtouched Acuity immunity edges, eldritch stacking caps, and Warden party tools needs a dedicated design session. |
|**Prestige / Post-Frontier Mastery**   |Mastery track outlined but not fully designed. Needs a dedicated session.                                                          |
|**Colorblind / High Contrast Mode**    |Deferred to post-v1 accessibility pass.                                                                                            |
|**Guild Hall Content**                 |Guild hall exists in v1 as a space. Additional guild hall content (mini-quests, guild bosses) is future scope.                     |
|**Party, Guild, Quest Systems**        |Full implementation deferred. Models and design exist; no in-game commands yet.                                                    |
|**NPC System and Dialogue**            |NPC models (`NpcDefinition`, `NpcInstance`, `Corpse`, `NpcEffect`) implemented. `examine` shows live NPCs and corpses. Combat aggro on room entry implemented. Wandering, dialogue, and patrol AI deferred.|
|**PvP Flagging and Bounty System**     |Not yet implemented.                                                                                                               |
|**The Wastelands Scaling Logic**       |Dynamic content scaling at spawn time not yet implemented.                                                                         |
|**Acuity Drift**                       |Acuity does not yet drift toward the character’s Origin baseline between combat rounds. Planned as a tick engine processor addition.|
|**DoT/HoT Per-Tick Application**       |`EffectInstance` rows expire correctly but do not apply per-tick stat changes. A `dot_vitality` effect currently expires without dealing damage.|
|**Durability Degradation in Combat**   |Death penalty (10% per death) implemented. Per-hit weapon degradation during combat not yet implemented.|
|**Revival Mechanic**                   |Dying state exists (30-second window). Another player using a revival item on a dying character is not yet implemented.|
|**Level-Up Trigger**                   |XP accrual on kill implemented. No level-up trigger, stat distribution, or XP threshold table yet.|
|**Room Spawn Configuration**           |No builder tool yet for configuring NPC spawns in rooms. NPCs are placed via seed command or Django admin.|

-----

*Document version 10.0 — Shyland Working Draft*
*All systems subject to revision during development.*