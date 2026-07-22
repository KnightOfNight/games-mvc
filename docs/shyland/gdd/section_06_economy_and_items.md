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

**The proc rename (v22, #100 — completing #68's deferred half).** The stats formerly named `bleed_chance`, `stun_chance`, and `poison_chance` are **`bleed_factor`, `stun_factor`, `poison_factor`** — under the ruled semantics the old names lied: the rolled value V is a *factor* driving both frequency and size, not a chance. Three flavor-distinct names are kept (not collapsed to one) so weapon variety survives on examine. `crit_chance` keeps its name — under its wiring it genuinely is a chance contribution; `lifesteal` keeps its name — it genuinely steals life. The rename touched seed data and rolled instances only (the idempotent `rename_proc_stats` command); no curve values changed. Authoring rule unchanged from v21 (#68): every proc-family stat is authored at `base 0.5, factor 0.2` — the curve that guarantees Mk 1 rolls of ≥1 at every rarity. **Zero-value stats are never hidden in display** (standing ruling): a rendered zero is a bug signal, and sirens stay audible — the fix is always in the data, never in suppression.

**The secondary-stat wiring map (v22, #100 — how every rolled stat is consumed).** Scope law governs: wire what combat reads, invent nothing for absent systems.

| Rolled stat | Consumed by |
|---|---|
| `str` / `dex` / `end` / `int` / `wis` / `per` | +N via the effective-stat function (Section 3.4) — every gameplay read |
| `physical_resist` | Joins TAV (Section 3.6). Not a proc. |
| `crit_chance` | +V percentage points (summed × 0.01) inside the crit computation, still capped at CRIT_CAP |
| `bleed_factor` / `stun_factor` / `poison_factor` | **Proc factors.** Per landed player hit, each equipped item rolls each of its proc-factor stats independently: chance = V × 0.05, capped at 50%; on success, bonus damage = random 1..⌈V⌉ ("up to N"). Names are flavor only — no DoT, no stun, no status effects in v22. |
| `lifesteal` | Always-on: each landed player hit heals the attacker by the summed rolled values (flat), clamped to vitality_max. No roll, no output line — the bar moves. |
| `electric_damage_bonus` | Always-on flat +V to the gear-bonus damage pool on every landed hit |
| `spell_damage_bonus` / `mana_regen` / `magic_resist` / `radiation_resist` | **Inert by scope law** — their consuming systems (spells, mana, non-physical damage) do not exist. Visible per zeros-never-hidden; wired to nothing; the resists do NOT join TAV. |

All gear bonus damage on a hit (proc successes + electric) sums into **one parenthetical** on the hit line — `You hit the giant cave spider for 14 (+7) damage.` No gear bonus → no parenthetical, line byte-identical (the quiet-line law). NPC damage to players never gains procs — NPCs have no equipment. Deferred by ruling: min–max ranged procs ("between 10 and 20 damage") are a new weapon kind in the midpoint-and-spread family (#127); the secondary-stat curves' shallow growth vs NPC band growth is a Mk-2-era retune, not a rework (#130 — same era as #104).

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

The performance penalty applies to the item's stat contributions and weapon damage output. At 0%, the item stops functioning entirely until repaired — including its armor: **a broken piece contributes nothing to TAV** (Section 3.6), and its examine confession reads `(worn: 0 — broken)`.

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

The `inventory` command (v22 — the information standards of Section 9.1 applied) shows three sections:

1. **Equipment — the paper-doll.** A `Slot / Name / Details` table showing **all 14 slot rows, always**, in anatomical order head→feet: Head, Neck, Shoulders, Back, Chest, Main hand, Off hand, Ranged, Hands, Ring, Ring, Waist, Legs, Feet. Sentence-case labels; empty slots render a muted `-` in Name and Details. Reading your gear is reading your body.
1. **Inventory.** A `Slot / Name / Quantity / Details` table, flat alphabetical by name. The Slot cell names the item's equip slot when slotted (`Main hand`), muted `-` when slotless; identical stacks fold into the Quantity column.
1. **Wallet.** One key/value line, **byte-identical** to the `wallet` command's output — one shared renderer, by rule.

Display rules:

- **Details** reads `90%, Uncommon, Bound` — durability + rarity + binding, no brackets. The durability number is colored by the **mechanical durability band** (derived from the band table in 6.5, never its own thresholds: no penalty → value-color, penalty bands → say-color, broken → error-color); rarity words are always rarity-colored in information output; the binding flag reads `Bound | Unbound`.
- Durability appears only for items with `takes_durability_loss=True`; bags show carry bonus instead.
- Cursed items that have not been identified show no curse indicator.
- Unidentified items show only their mystery name (no rarity, no Mk tier) in place of the real item name.
- Carry count rides the section header: `Inventory (12/250)...`

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
- **Commands (v22 grammar — Section 9.1 is authoritative):** `list` (vendor stock), `buy [<N>] <item>` (numeric quantity only; `all` refused), `sell [<N>|all] <item>` and `sell all <rarity> [<item>]` (bare `sell all` is refused with wording that teaches the noun form), `repair <item>`, and `repair all` — which **loops**: passes over what is still damaged until everything is repaired, funds run out, or 5 passes (#75), each mend line printing as it lands. Bare `buy`/`sell`/`repair` prompt for a target (the v18 bare-repair convenience retired to the standard prompt). Commands route automatically: buy/sell/list to the living vendor in the room, repair to the living repairer — killed service NPCs are out of business until they respawn.
- **The vendor list (v22, #123/#58):** a `Slot / Name / Details / Price` table — Details shows rarity only (entries are definitions, not instances — no durability, no binding flag); two groups, **free first** (Price reads a muted `free`), then priced, alphabetical within groups; every price through the tier formatter.
- **Transactional aggregation (v22):** buy/sell/drop/pickup with N > 1 answer with **one count-form line per item definition** — `You buy Healing Draught Mk 1 ×100 for 9 silver.` (no article, total money) — a transaction is one act however many items it moves. `use`, `repair`, and `loot` stay **per-line**: each iteration is its own news (a swallow's effect, a mend's chance outcome, a find's identity). The count form is the deliberately plural-free first iteration; natural-English pluralization is a filed future subsystem (#126).
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

- **The free starter kit:** eleven distinct authored definitions at `base_value=0` — exploit-proof by construction (sale value is 0, and worthless items are refused: "That's not worth anything to me."). The kit covers every equipment slot except OFF_HAND and RANGED — deliberate gaps; the first slots a player must *earn* (Morra's priced tier sells them). Kit gear wears normally (`takes_durability_loss=True`) and repairs for ~nothing via **pity-repair** lines in each repairer's voice — the durability loop is onboarding, and the first lessons are free.
- **Priced tier:** a small aspiration shelf at Morra (shortsword, shield, sling, jerkin) priced for early hide-money; the full price-range spread is a future stocking pass.
- **Currency display rule:** every player-facing money amount — `list` prices, `buy`/`sell` amounts and refusals, repair quotes — renders through the shared tier formatter. Raw copper counts never reach the player; zone aliasing comes free.
- **Multi-vendor rooms** resolve `list`/`buy`/`sell`/`repair` to a deterministic serving NPC (lowest pk); at the gazebo the non-serving spouse kibitzes after transactions.

-----

