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

