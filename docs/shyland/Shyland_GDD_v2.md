# Shyland — Game Design Document
**Version 2.0 — Working Draft**

---

## Table of Contents

1. [Vision & Pillars](#1-vision--pillars)
2. [World Model](#2-world-model)
3. [Character System](#3-character-system)
4. [The Three Bars — Vitality, Acuity, Longevity](#4-the-three-bars--vitality-acuity-longevity)
5. [Combat System](#5-combat-system)
6. [Economy & Items](#6-economy--items)
7. [Social Systems](#7-social-systems)
8. [Quest & Narrative](#8-quest--narrative)
9. [Technical Architecture](#9-technical-architecture)
10. [Admin & Content Tools](#10-admin--content-tools)
11. [Future Systems](#11-future-systems)

---

## 1. Vision & Pillars

### 1.1 Concept

Shyland is a free, web-based Multi-User Dungeon (MUD) set in a fractured world where dimensional rifts have shattered the boundaries between realities. Players inhabit a world where a cyberpunk street samurai may cross paths with an elven ranger, where a steam-powered war golem guards the entrance to a gothic cathedral, and where a radiation-scarred wastelander haggling in a medieval marketplace is just another Tuesday.

The anachronism is the point. Genre collision is not a bug — it is the central aesthetic and lore engine of the game.

### 1.2 Design Pillars

| Pillar | Description |
|---|---|
| **Combat First** | Every system should serve or enhance the combat loop. Progression, exploration, and social play all feed back into making combat more interesting. |
| **Text is Primary** | The written word is the primary interface. UI chrome and visual elements support the text; they never replace it. |
| **Genre as Flavor** | Genre differences are expressed through aesthetics, vocabulary, and equipment — not through radically different rule sets. A laser rifle and a longbow use the same underlying ranged combat mechanics. |
| **PvE Core, PvP Opt-In** | The default world is cooperative. PvP is available in designated zones with explicit player consent. Griefing is a design failure. |
| **Legible Systems** | Players should be able to understand what is happening and why at every moment. No hidden dice. Stats, modifiers, and outcomes are exposed on request. |
| **Free Forever** | Shyland has no monetization, no premium currency, no real-money transactions of any kind. It is free to play in the most literal sense. |

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

---

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

| Zone ID | Name | Genre Tone | Danger Level |
|---|---|---|---|
| Z01 | The Verdant Reach | Classic fantasy wilderness | Beginner |
| Z02 | Ashenveil Cathedral | Dark gothic horror | Intermediate |
| Z03 | The Neon Sprawl | Cyberpunk megacity | Intermediate |
| Z04 | The Blasted Flats | Post-apocalyptic wasteland | Advanced |
| Z05 | The Convergence | All genres collide — the world's central hub | Sanctuary |
| Z06 | The Iron Deeps | Steampunk underground | Advanced |
| Z07 | The Pale Shore | Cosmic horror / lovecraftian ocean | Endgame |
| Z08 | The Wastelands | Infinite scaling zone — always level-appropriate | All levels |

**The Convergence (Z05)** is the game's social hub — a permanent sanctuary zone where PvP is disabled, vendors of all types exist, and players from all backgrounds congregate. Lore-wise, it is the epicenter of The Fracture. It is also the default logout and recall destination.

**The Wastelands (Z08)** is a special infinite scaling zone — see Section 2.6.

### 2.3 Rooms

Each room is the atomic unit of the world. Rooms contain:

- **Short name** — displayed in the room header (e.g., `[Black Market Stall #7]`)
- **Long description** — the prose a player reads on entering or using the `look` command
- **Brief description** — one-line version shown when the player has visited before (toggleable)
- **Exit list** — directional links to adjacent rooms (N, S, E, W, U, D, and custom named exits)
- **Flags** — booleans that modify room behavior (see below)
- **Contents** — current list of players, NPCs, and items present

#### Room Flags

| Flag | Effect |
|---|---|
| `SAFE` | No combat allowed, NPCs won't aggro |
| `PVP` | PvP is enabled in this room |
| `DARK` | Players need a light source to see descriptions |
| `INDOORS` | Weather effects don't apply |
| `WATER` | Swimming/drowning rules apply |
| `NO_RECALL` | Players cannot use recall/teleport abilities |
| `RADIATION` | Periodic radiation damage (wasteland zones) |
| `HOLY` | Undead and demonic entities take passive damage |
| `MAGIC_DEAD` | Spell and tech abilities disabled |
| `SCALED` | Room and its contents scale to entering player's level (Wastelands) |

### 2.4 The Visual Map Layer

Rooms belong to a coordinate grid within their zone. The client renders a small ASCII/SVG minimap (configurable size, default 5×5 tiles centered on the player) showing:

- Current room (highlighted)
- Adjacent visited rooms
- Unexplored exits (shown as dotted connections)
- Special room types (shops, quest givers, danger) via icon overlays

The map does not replace text navigation — it is supplementary. Players can hide it. The map only reveals rooms the player has personally visited (fog of war).

### 2.5 Travel & Navigation

Players move using directional commands: `north`, `south`, `east`, `west`, `up`, `down` (and abbreviations: `n`, `s`, `e`, `w`, `u`, `d`). Named exits use the exit name directly (e.g., `enter portal`).

**Movement costs no action economy in normal exploration.** Combat changes this (see Section 5).

Special travel options:
- **Recall scroll** — teleports player to their bound recall point (default: The Convergence)
- **Zone gates** — fixed fast-travel points between zones, requiring discovery first

Mounts are deferred to a future version.

### 2.6 The Wastelands — Infinite Scaling Zone

The Wastelands is a post-apocalyptic expanse that serves as the game's permanent endgame safety valve. It has no fixed difficulty — the zone scales to match any entering character's level.

**Scaling rules:**
- Enemy stats, HP, and damage scale to the entering player's level
- Loot scales to match — a level 200 character finds level 200 loot (using the Mk system — see Section 6.3)
- In a party, the zone scales to the highest level member
- XP rewards scale appropriately — The Wastelands always provides meaningful XP regardless of player level

**Design purpose:**
When no higher-level content has yet been published, The Wastelands ensures players always have somewhere challenging to go. It is not a substitute for purpose-built high-level zones but bridges the gap between content updates.

### 2.7 Logout Persistence

When a player logs out, their character remains in the world at their exact location for 60 seconds (allowing them to be targeted in PvP zones — a deliberate risk of logging out in dangerous areas), then fades from the world. On next login, they appear at the exact room where they logged out.

There is no safe logout room. Players are responsible for where they choose to go offline.

---

## 3. Character System

### 3.1 Character Creation

New players choose:
1. **Origin** (replaces traditional race — see 3.2)
2. **Archetype** (replaces traditional class — see 3.3)
3. **Name** (profanity filtered, uniqueness enforced)
4. **Portrait** (selected from a curated set grouped by Origin; visual element displayed in UI)

### 3.2 Origins

Origins define where a character came from — which fragment of reality they were pulled from. They provide flavor, starting bonuses, and passive traits. They do not lock players out of any Archetype.

| Origin | Genre Flavor | Passive Trait |
|---|---|---|
| Highborn | Classic fantasy noble | +10% XP from quest completion |
| Feral | Wilderness / tribal | +15% movement, +1 to foraging rolls |
| Streetborn | Cyberpunk urban | Hacking attempts cost 10% less energy |
| Irradiated | Post-apocalyptic | Radiation resistance, Vitality regenerates slowly in rad zones |
| Undying | Gothic horror / undead-touched | Reduced death penalty; small life drain on melee hits |
| Machinekind | Steampunk construct | Cannot be poisoned; cannot be healed by magic (repairs only) |
| Voidtouched | Cosmic horror survivor | Bonus to eldritch damage; natural Acuity resistance at both extremes of the scale |

Each Origin has a distinct **Acuity baseline** — the natural resting point their Acuity gravitates toward when no external forces are acting on it. A Voidtouched character's baseline is shifted toward the lower end of the scale; they are accustomed to the strange. A Highborn's baseline sits in the mid-range.

Origins can have social/narrative consequences — some NPCs react differently to Machinekind in a fantasy village, or to an Irradiated in a pristine elven glade.

### 3.3 Archetypes

Archetypes define combat role and skill access. Each spans genre — a Blade is equally a swordsman, a street samurai, or a wasteland knife-fighter depending on equipment and flavor choices.

| Archetype | Role | Primary Stats | Genre Range |
|---|---|---|---|
| **Blade** | Melee DPS | STR, DEX | Fighter, Samurai, Brawler |
| **Bulwark** | Tank / melee sustain | STR, END | Knight, Warlord, Juggernaut |
| **Shade** | Stealth / burst | DEX, INT | Rogue, Infiltrator, Ghost |
| **Conduit** | Magic ranged DPS | INT, WIS | Mage, Techsorcerer, Psion |
| **Warden** | Healer / buffer | WIS, END | Cleric, Medic, Shaman |
| **Gunner** | Ranged DPS | DEX, PER | Ranger, Sniper, Heavy |
| **Machinist** | Pet / turret / construct | INT, DEX | Engineer, Summoner, Drone Ops |

Archetypes are not rigid. A skill tree system (see 3.5) allows cross-archetype dabbling at a cost — every point spent outside your primary tree is slightly less efficient.

The **Warden** archetype has expanded responsibility in Shyland — beyond healing Vitality, Wardens have tools to actively manage party members' Acuity, nudging allies toward their optimal range when combat stress or eldritch exposure has shifted them too far in either direction.

### 3.4 Core Stats

Six primary stats, each 1–100 (starting range 8–18 based on origin/archetype bonuses):

| Stat | Abbreviation | Governs |
|---|---|---|
| Strength | STR | Melee damage, carry weight, some intimidation checks |
| Dexterity | DEX | Hit chance, dodge, ranged damage, stealth |
| Endurance | END | Max Vitality, physical damage mitigation, stamina pool |
| Intelligence | INT | Spell/tech damage, mana/energy pool, crafting |
| Wisdom | WIS | Healing output, resistance to debuffs, XP rate |
| Perception | PER | Initiative, ranged accuracy, trap/secret detection, situational awareness |

#### Derived Stats

| Derived Stat | Formula |
|---|---|
| Max Vitality | (END × 10) + (STR × 3) + level bonus |
| Max Acuity range | Baseline set by Origin; width of optimal band scaled by WIS |
| Max Longevity | (END × 8) + (WIS × 5) + level bonus |
| Max Mana | (INT × 10) + (WIS × 3) + level bonus |
| Physical Defense | (END × 2) + armor value |
| Magic Resistance | (WIS × 2) + equipment bonuses |
| Initiative | PER + DEX + d10 (rolled per combat) |
| Carry Weight | STR × 10 (in arbitrary units) |

### 3.5 Progression & Leveling

**No hard level cap.** Progression is continuous. In practice, a soft cap exists at the frontier of published content — XP return diminishes sharply below a character's level, so grinding low-level content eventually becomes inefficient. The Wastelands always provides a level-appropriate alternative.

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
- **Type** (weapon, armor, accessory)
- **Mark tier** (Mk 1 through Mk N — see Section 6.3)
- **Rarity** (Common, Uncommon, Rare, Epic, Legendary, Artifact)
- **Stat bonuses** (flat or percentage)
- **Flags** (e.g., `TWO_HANDED`, `RANGED`, `TECH`, `CURSED`)
- **Flavor genre tag** (fantasy, cyber, wasteland, etc.) — cosmetic only
- **Durability** — degrades with use; breaks if neglected
- **Bound flag** — all items are soulbound on pickup; cannot be traded between players

Genre mixing in equipment is explicitly supported. A character can carry a plasma rifle in one hand and an enchanted dagger in the other.

**Carry limit:** Players carry what they can physically hold. No off-body storage, no bank, no shared stash. Carry weight is governed by STR. Early dungeons have loot tables weighted toward bags and backpacks to help players expand their capacity organically.

### 3.7 Death & Resurrection

Death in Shyland is meaningful but not brutal:

- Player reaches 0 Vitality → enters **Dying** state (30-second window where allies can revive)
- If not revived → **Dead**. Player respawns at their bound recall point (default: The Convergence)
- On death: 10% XP loss (softcapped — cannot lose a level), equipment durability takes a major hit
- In PvP zones only: chance to drop one non-equipped carried item
- A **Death Shard** item is left at the death location; player can retrieve it within 30 minutes to recover any dropped item

**Hardcore Mode** (optional, on character creation): permadeath. Character deleted on death. Hardcore characters are flagged visually and have a separate leaderboard.

---

## 4. The Three Bars — Vitality, Acuity, Longevity

This is one of Shyland's most distinctive systems. All characters have three resource bars, each governing a different dimension of their condition. They are not separate — they interact and influence each other. The separation into three bars is a mechanical convenience, not a philosophical statement that mind and body are distinct.

### 4.1 Vitality

**What it is:** The body's immediate physical condition.

**Mechanical effects:**
- Melee damage dealt and received scales with current Vitality as a percentage of maximum (low Vitality = hitting and being hit harder proportionally)
- Movement speed degrades at low Vitality
- Physical resistance degrades at low Vitality
- Reaching 0 Vitality triggers the Dying state

**Recovery:** Healing spells, medkits, potions, natural regen (slow, out of combat only).

**Machinekind note:** Machinekind characters cannot be healed by magic. Their Vitality is restored only through repair items and the Machinist archetype's self-repair abilities.

### 4.2 Acuity

**What it is:** The mind's dynamic state. Not a scale from broken to perfect — a spectrum with a sweet zone that varies by Origin. Being too high or too low are both problems.

**There is no universally "correct" Acuity value.** Each Origin has a natural baseline and a tolerance band. Characters are most effective when operating within their band.

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
- Rest and time naturally return Acuity toward a character's baseline

**Manipulation:** Players can actively shift their own Acuity intentionally. Pushing it high before a single-target duel, then managing the aftermath, is a valid play style. The system rewards players who understand their character's band and manage it actively.

### 4.3 Longevity

**What it is:** The slow burn. Accumulated resilience — the will and capacity to keep going over time.

**Mechanical effects:**
- Controls stamina duration — how long a character can sprint, sustain effort, or maintain concentration
- Governs duration of sustained effects: a character's own damage-over-time effects last longer at high Longevity; enemy DoTs applied to them expire faster
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

---

## 5. Combat System

### 5.1 Philosophy

Combat is turn-based in structure but runs in real time. Every player and NPC has a **tick rate** — an individual action timer. When the timer expires, the next action fires (automatically or by queued command). This is the classic MUD round model, modernized.

The client displays a visual tick bar. Combat ticks are fixed — there is no option to slow them for any player.

### 5.2 Initiating Combat

Combat begins via:
- `kill <target>` or `attack <target>` command
- An NPC aggro trigger (entering their aggro radius while flagged as a valid target)
- A skill that implicitly initiates combat

Once combat begins, all participants are locked in until one side flees, dies, or combat ends naturally.

### 5.3 The Action Economy

Each combat tick (default: 3 seconds, modified by haste/slow effects), a character may:

- **1 Primary Action** — attack, cast a spell, use an ability
- **1 Reaction** (passive, triggers on conditions) — parry, counter, shield block
- Movement within combat costs a Primary Action

Auto-attack fires automatically each tick if no manual command is given. Players can queue commands ahead of the tick.

### 5.4 Attack Resolution

```
1. Hit check:
   d100 + attacker DEX modifier vs. target dodge rating
   → Miss: no damage
   → Graze (within 10 of miss threshold): 50% damage
   → Hit: full damage
   → Critical (exceeds threshold by 20+): 150% damage + bonus effect

2. Damage calculation:
   base_damage  = weapon damage range (random roll within Mk tier)
   stat_bonus   = relevant stat modifier (STR melee / DEX ranged / INT spells)
   skill_bonus  = active skill modifiers
   acuity_mod   = multiplier based on attacker's current Acuity vs. their optimal band
   raw_damage   = (base_damage + stat_bonus + skill_bonus) × acuity_mod

3. Mitigation:
   final_damage = raw_damage - target defense value (minimum 1)

4. Elemental/type resistances apply as percentage reduction after armor
```

All numbers are visible in the combat log. Verbose mode exposes the full calculation chain.

### 5.5 Damage Types

| Type | Common Sources | Notes |
|---|---|---|
| Physical | Swords, bullets, blunt weapons | Mitigated by armor |
| Fire | Spells, flamethrowers, explosives | Mitigated by fire resistance |
| Cold | Ice spells, cryo weapons | Can slow targets |
| Electric | Lightning spells, tasers, energy weapons | Can stun targets |
| Toxic | Poison, acid, chemical weapons | Damage over time |
| Radiation | Wasteland hazards, rad weapons | Stacks; high stacks = stat penalties, Acuity disruption |
| Eldritch | Cosmic horror abilities | Bypasses most resistances; disrupts Acuity significantly |
| Holy | Clerical abilities | Extra damage vs. undead/demonic |
| Shadow | Shade abilities, dark magic | Reduces target's defense temporarily |

### 5.6 Status Effects

| Effect | Mechanic |
|---|---|
| **Burning** | Fire DoT, 3–5 ticks |
| **Frozen** | Movement disabled, defense reduced, breaks on damage |
| **Stunned** | Cannot act for 1–2 ticks |
| **Slowed** | Tick rate increased (slower actions) |
| **Hasted** | Tick rate decreased (faster actions) |
| **Poisoned** | Toxic DoT, stackable |
| **Bleeding** | Physical DoT, stops on healing |
| **Feared** | Forces random movement for 1–3 ticks |
| **Charmed** | Target fights for the caster briefly |
| **Silenced** | Cannot use spells or tech abilities |
| **Blinded** | Hit chance severely reduced |
| **Irradiated** | Stacking radiation; at max stacks: stat penalties + Acuity disruption |
| **Unmoored** | Eldritch effect; Acuity pushed violently away from baseline |
| **Focused** | Acuity spiked high; single-target bonus, flanking blindness active |
| **Scattered** | Acuity pushed low; awareness penalties, spell unreliability |

**Longevity interactions:** The duration of DoT and HoT effects on a character is modified by their Longevity. High Longevity = enemy DoTs expire faster, own HoTs last longer.

### 5.7 Flee & Escape

`flee` command. Success based on DEX vs. pursuer PER. On success: moved to a random adjacent room. On failure: tick lost. Boss encounters apply an additional flee penalty.

### 5.8 Group Combat

Parties of up to 6 players. Enemies maintain a threat table — highest threat character receives the majority of attacks. Bulwarks generate extra threat; Shades reduce theirs.

### 5.9 NPC & Enemy Design

Enemies have:
- A **combat tier** (Normal, Elite, Champion, Boss, World Boss)
- **Archetype flags** governing tactics
- **Special abilities** telegraphed in combat log before firing
- **Loot tables** — tiered probability lists

Bosses have multi-phase fights with behavioral changes at HP thresholds. Some boss abilities specifically target Acuity — a screaming eldritch horror doesn't just deal damage, it pushes the entire party's Acuity toward an extreme.

---

## 6. Economy & Items

### 6.1 Core Principles

- **All items are soulbound on pickup.** No player-to-player item trading.
- **Currency is freely transferable** between players.
- **Super users (staff/admin) can gift items** to players. Gifted items become immediately soulbound to the recipient. Gifts may be standard items appropriate to the player's level, or bespoke one-off items crafted specifically for the occasion.
- **No real-money transactions of any kind.**
- **No off-body storage.** Players carry what they carry. No banks, no shared stash, no mule characters.

### 6.2 Currency

Three tiers:

| Tier | Name | Acquisition |
|---|---|---|
| Base | **Shards** | Enemy drops, vendor sell, quests |
| Mid | **Marks** | 100 Shards = 1 Mark; quest rewards, dungeon drops |
| High | **Crowns** | 100 Marks = 1 Crown; rare drops, endgame content |

Currency sinks: repairs, skill respecs, crafting materials, NPC services.

### 6.3 The Mark System — Item Naming & Scaling

Items in Shyland use a **Mark (Mk) tier system** tied to player level ranges. This allows the game to have a manageable item namespace — one Sword, not a thousand uniquely named swords — while still providing meaningful power progression.

| Mark | Player Level Range |
|---|---|
| Mk 1 | 1–10 |
| Mk 2 | 11–20 |
| Mk 3 | 21–30 |
| Mk 4 | 31–40 |
| Mk 5 | 41–50 |
| Mk 6 | 51–60 |
| Mk 7 | 61–70 |
| Mk 8 | 71–80 |
| Mk 9 | 81–90 |
| Mk 10 | 91–100 |
| Mk 11+ | Wastelands / post-frontier — continues infinitely |

**Reading an item:** `Rare Plasma Rifle Mk 7` tells you everything — what it is, how powerful it is relative to other items, and how special it is. Rarity stacks on top of Mark tier.

**In The Wastelands:** Loot scales dynamically. A level 150 character finds Mk 15 loot. The Mk system extends infinitely to accommodate this.

**Item generation:** The engine needs one base item definition per item type. At drop time, it selects the appropriate Mk tier for the context (zone level, enemy tier, player level) and scales stats accordingly.

### 6.4 Item Rarity

| Rarity | Approximate Drop Rate |
|---|---|
| Common | 60% |
| Uncommon | 25% |
| Rare | 10% |
| Epic | 4% |
| Legendary | 0.9% |
| Artifact | 0.1% |

Legendary and Artifact items cannot be crafted — only found.

### 6.5 Vendors

- **General merchant** — consumables, basic gear
- **Specialty vendor** — zone-specific items
- **Repair vendor** — restores equipment durability
- **Skill trainer** — sells skill books for cross-tree skills

**The Robotic Helper NPC:** A unique NPC that can be summoned by players in the field. Characteristics:
- There is only one. It is not instanced per player.
- It will not always come when called — its availability is not guaranteed
- Further details TBD (this is a deliberately open design element for now)
- It functions as a mobile vendor alternative to stationary vendors in town

Vendor inventory refreshes on a timer. Some vendors carry rare rotating stock.

### 6.6 Crafting

Crafting is a skill track open to any character. Four disciplines:

| Discipline | Produces | Key Stat |
|---|---|---|
| **Smithing** | Weapons, armor | STR |
| **Tinkering** | Tech items, gadgets, traps | INT |
| **Alchemy** | Potions, poisons, consumables | WIS |
| **Tailoring** | Light armor, cloaks, bags | DEX |

Crafting requires: schematic + materials + crafting station. Max craftable rarity: Epic. Legendary and Artifact items are found only.

Material gathering uses room-specific commands: `forage`, `mine`, `salvage`, `harvest`. Success uses PER and relevant skills.

---

## 7. Social Systems

### 7.1 Communication Channels

| Channel | Command | Scope |
|---|---|---|
| Say | `say <text>` | Current room only |
| Yell | `yell <text>` | Current room + adjacent rooms |
| Tell | `tell <name> <text>` | Private, anywhere |
| Party | `party <text>` | All party members |
| Guild | `guild <text>` | All online guild members |
| Zone | `zone <text>` | All players in current zone |
| General | `general <text>` | All players online (throttled) |
| Emote | `emote <text>` | Freeform action in current room |

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

---

## 8. Quest & Narrative

### 8.1 Quest Types

| Type | Description | Primary Reward |
|---|---|---|
| **Kill** | Defeat X enemies or a named target | XP, loot |
| **Fetch** | Retrieve an item and return it | XP, currency, rep |
| **Escort** | Keep an NPC alive during movement | Unique items, rep |
| **Explore** | Discover a set of locations | XP, map reveal |
| **Craft** | Produce a specific item | Schematic unlocks |
| **Investigation** | Multi-step, dialogue-heavy, branching | Story progression, unique rewards |
| **World Event** | Timed server-wide quest | Prestige currency, cosmetics |

### 8.2 Quest Structure

Quests given by NPCs via `talk` or `ask`. Quest givers flagged in the client UI.

Quests have: journal entry, tracked objectives, completion trigger, and branching outcomes for Investigation quests. Quest chains unfold zone stories and may permanently alter zone state.

### 8.3 NPC Dialogue System

NPCs respond to `talk`, `ask <topic>`, `say <keyword>`. Conditional responses based on reputation, quest state, Origin, Archetype. NPCs remember if you've helped or harmed them.

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

---

## 9. Technical Architecture

### 9.1 Stack

Shyland is built on an existing Django-based foundation. The stack is:

| Layer | Technology |
|---|---|
| **Backend framework** | Django (Python) |
| **Real-time transport** | Django Channels (WebSocket) |
| **Database** | PostgreSQL |
| **In-memory / session state** | Redis (via Django Channels layer) |
| **Client** | Browser-based SPA — HTML/CSS/JS (framework TBD based on existing project) |
| **Auth** | Django authentication system (existing); session or JWT |
| **Hosting** | TBD — existing project infrastructure |

The Node.js/Go recommendation from v1.0 of this document is retired. The existing Django + Channels + PostgreSQL stack is the foundation.

### 9.2 Client Architecture

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

**Accessibility:** Semantic HTML throughout. Proper ARIA labels on all interactive elements. The output pane is structured so screen readers can follow the text log naturally. Clickable elements in output auto-fill the input line and are keyboard-navigable.

**Status bar:** Displays all three bars — Vitality (V), Acuity (A), Longevity (L) — with visual indication of the Acuity "sweet zone" band for the current character's Origin.

**Phone layout:** Side panel collapses to a bottom drawer. Minimap collapses to an icon that expands on tap. Input line remains always accessible.

**Single visual theme** — no colorblind mode or high-contrast mode in v1.

### 9.3 Server / Tick Architecture

The game server runs a **tick engine** implemented as a Django Channels consumer or a background async worker:

1. Process all queued player commands
2. Advance all NPC AI states
3. Apply all DoT/HoT effects (duration modified by Longevity)
4. Fire all pending combat ticks
5. Process Acuity drift (all characters' Acuity moves incrementally toward their Origin baseline each tick when not under active effects)
6. Process zone events
7. Broadcast state changes to affected clients via WebSocket

**Global tick rate:** 1 second. Combat round = 3 ticks. Fixed — not adjustable per player.

NPC AI runs server-side. No game state is trusted from the client.

### 9.4 Persistence Model

#### Written to DB on change (event-driven):
- Character stats, all three bars (Vitality/Acuity/Longevity current values), inventory, position
- Quest state
- Faction reputation
- Guild data
- Item soulbind records

#### Written to DB on interval (every 60 seconds):
- Character XP
- Currency amounts

#### In-memory only (Redis):
- Active combat state
- Active session data
- NPC positions and states (rebuilt from templates on server restart)
- Acuity drift calculations between ticks

#### Never persisted:
- Chat messages (ephemeral; stored only if reported for moderation)
- Combat log

### 9.5 World State & Instancing

Shared persistent world — all players inhabit the same rooms. No instancing for standard content.

**Dungeons:** Semi-instanced. One party per dungeon copy. Additional parties queue or enter a parallel copy. Dungeon state resets on a timer (default: 6 hours).

**Guild halls:** Fully instanced per guild.

**The Wastelands:** Shared world but all content is dynamically scaled — no instancing required. Scaling is computed server-side at spawn time based on the highest-level player in the triggering party.

### 9.6 Admin / Super User Infrastructure

Super user tools are **v1 critical infrastructure** — not an afterthought. Given no mounts and no housing, teleportation and world-inspection tools are the primary means of navigating and testing the game during development.

Required v1 admin capabilities:
- Teleport to any room by ID or name
- Spawn any NPC or item in current room
- Observe any room invisibly
- Adjust any character's stats, bars, currency, or position
- Gift items to players (items become immediately soulbound on gift)
- Mute, kick, ban players
- Force-reset dungeon instances
- Access moderation queue

### 9.7 Security

- All game logic runs server-side; client is a dumb terminal
- Rate limiting on all WebSocket messages
- Command injection sanitized at input layer
- Item soulbind status, currency amounts, and stat values never trusted from client
- Anti-cheat: server validates all position changes, damage values, inventory states
- Item gifting requires super user authentication — cannot be spoofed by regular players

### 9.8 Moderation

- `report <player> <reason>` sends flagged log to moderation queue
- Staff can appear invisible, observe rooms, mute/kick/ban
- Automated detection: spam, impossible stat values, movement anomalies

---

## 10. Admin & Content Tools

### 10.1 Builder System

Web-based builder interface (separate from game client) for authorized staff:

- Create/edit rooms (all fields, flags, exits, coordinates)
- Create/edit NPCs (stats, loot tables, dialogue trees, Acuity-affecting abilities)
- Create/edit items (all properties, Mark tier, rarity, soulbind rules)
- Create/edit quests (objectives, rewards, branching logic)
- Teleport to any room, spawn items/NPCs for testing

Changes can be staged and reviewed before going live.

### 10.2 OLC (Online Level Creation)

In-game OLC commands available to trusted builders for iteration and tweaking. Complex new content goes through the full builder UI.

### 10.3 Content Scripting

NPCs and rooms support lightweight event scripting (sandboxed Python subset or Lua) for:
- Triggered events (player enters room → NPC speaks)
- Conditional behavior (quest state checks, reputation gates)
- Puzzle mechanics
- Acuity-affecting environmental triggers (entering Pale Shore rooms slowly shifts Acuity)

Scripts written in builder UI with a validator.

### 10.4 Analytics & Monitoring

Structured event emission for:
- Player deaths (location, cause, level, bar states at time of death)
- Quest completion rates
- Zone population over time
- Economy metrics (currency velocity, vendor sales)
- Combat metrics (ability usage, damage type distribution)
- Acuity distribution across player base (for balance tuning)

Internal dashboard for balancing decisions.

---

## 11. Future Systems

These are explicitly deferred — not in scope for v1, documented here for future design sessions:

| System | Notes |
|---|---|
| **Mounts** | Deferred. Super user teleportation covers testing needs in v1. |
| **Housing** | Deferred. No player housing in v1. |
| **Auction House** | Permanently excluded. Items are soulbound; no player item trading ever. |
| **Seasonal Content** | Permanently excluded. World freshness comes from regular content updates only. |
| **Mobile Native App** | Deferred. Web responsive is v1 target. |
| **Localization** | Deferred. English only in v1. |
| **The Robotic Helper NPC** | Partially designed. Unique, unreliable, mobile vendor. Full design TBD. |
| **Sanity / Acuity Edge Cases** | Full design of Voidtouched Acuity immunity edges, eldritch stacking caps, and Warden party tools needs a dedicated design session. |
| **Prestige / Post-Frontier Mastery** | Mastery track outlined but not fully designed. Needs a dedicated session. |
| **Colorblind / High Contrast Mode** | Deferred to post-v1 accessibility pass. |
| **Guild Hall Content** | Guild hall exists in v1 as a space. Additional guild hall content (mini-quests, guild bosses) is future scope. |

---

## Technical Review Notes

*This section summarizes architectural observations made during review of the GDD against the confirmed Django/Channels/PostgreSQL stack. These are flags for the upcoming development Q&A session.*

**Where the stack fits well:**
- Django ORM maps cleanly to the relational data model (characters, items, rooms, quests, factions are all well-structured relational data)
- Django Channels handles WebSocket persistence per client naturally
- PostgreSQL is well-suited for the persistence model described
- Django's auth system covers player accounts and super user roles without additional infrastructure
- Python is well-suited for scripting NPC behaviors (sandboxed Python subset for content scripting is a natural fit)

**Where to pay attention:**
- **The tick engine:** Django is synchronous by default. The async tick loop needs to run as a Channels consumer or a Celery beat task — not a standard Django view. This is the highest-risk architectural piece and should be prototyped first.
- **Acuity drift per tick:** Running Acuity recalculation for all online players every second at scale is a non-trivial load. Redis is the right place for this; ensure it doesn't hit the DB on every tick.
- **WebSocket fan-out:** Room-based broadcasts (everyone in Room X sees the same combat log) map to Channels Groups. Verify the existing project already uses Groups — if it does, this is essentially free.
- **Item soulbind enforcement:** Soulbind status must be enforced server-side in every item transfer code path. The super user gift flow needs its own validated pathway that sets soulbind to recipient on write.
- **The Wastelands scaling:** Dynamic content scaling at spawn time is a new pattern if the existing project doesn't have it. Enemy and loot stat scaling functions need to be clean, tested, and centralized — not scattered across views.
- **Screen reader compatibility:** Ensure the WebSocket output pane uses ARIA live regions (`aria-live="polite"` for normal output, `aria-live="assertive"` for combat/urgent events) so screen readers announce new text automatically.

**Questions for the development Q&A session:**
1. What does the existing WebSocket consumer look like — is it already using Channels Groups for room broadcasts?
2. Is there an existing tick/heartbeat mechanism, or does the game engine need to be built from scratch?
3. What frontend framework is the existing project using?
4. What does the existing user/auth model look like — will it extend cleanly to character profiles?
5. What does the existing data model cover — users, rooms, anything else?
6. Is Redis already in the stack, or does it need to be added?
7. What's the current hosting environment?

---

*Document version 2.0 — Shyland Working Draft*
*All systems subject to revision during development.*
*Technical review notes are provisional pending development Q&A session.*
