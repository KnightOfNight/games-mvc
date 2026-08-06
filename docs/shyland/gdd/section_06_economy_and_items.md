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
| `bleed_factor` / `stun_factor` / `poison_factor` / `flame_factor` | **Proc factors.** Per landed player hit, each equipped item rolls each of its proc-factor stats independently: chance = V × 0.05, capped at 50%; on success, bonus damage = random 1..⌈V⌉ ("up to N") — lifted to random X..Y on floored entries (the proc floor, below). Names are flavor only — no DoT, no stun, no status effects. `flame_factor` is the family's fourth member. |
| `lifesteal` | Always-on: each landed player hit heals the attacker by the summed rolled values (flat), clamped to vitality_max. No roll, no output line — the bar moves. |
| `electric_damage_bonus` | Always-on flat +V to the gear-bonus damage pool on every landed hit |
| `spell_damage_bonus` / `mana_regen` / `magic_resist` / `radiation_resist` | **Inert by scope law** — their consuming systems (spells, mana, non-physical damage) do not exist. Visible per zeros-never-hidden; wired to nothing; the resists do NOT join TAV. |

All gear bonus damage on a hit (proc successes + electric) sums into **one parenthetical** on the hit line — `You hit the giant cave spider for 14 (+7) damage.` No gear bonus → no parenthetical, line byte-identical (the quiet-line law). NPC damage to players never gains procs — NPCs have no equipment. Min–max ranged procs ("between 10 and 20 damage") are the proc floor below (v24.10, #127). Deferred by ruling: the secondary-stat curves' shallow growth vs NPC band growth is a Mk-2-era retune, not a rework (#130 — same era as #104).

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

- Base carry capacity: STR × 10
- Equipping a bag adds its `carry_bonus` to the total
- The inventory is a flat pool — players do not manage which specific item is in which pocket
- **A bag cannot be unequipped if doing so would put the character over their carry limit**
- The slot a bag occupies creates meaningful trade-offs — a courier bag on a hip slot means no pistol there

### 6.11 Inventory Display

The `inventory` command (v22 — the information standards of Section 9.1 applied) shows three sections:

1. **Equipment — the paper-doll.** A `Slot / Name / Details` table showing **all 14 slot rows, always**, in anatomical order head→feet: Head, Neck, Shoulders, Back, Chest, Main hand, Off hand, Ranged, Hands, Ring, Ring, Waist, Legs, Feet. Sentence-case labels; empty slots render a muted `-` in Name and Details. Reading your gear is reading your body. **Consumed hand slots name their consumer (v24.7 — #176):** a hand slot claimed by a two-handed item equipped in another slot is not free and never renders as free — the row shows the consuming item's name-with-tier, muted, in Name, and a muted `(two-handed)` in Details. The true fact — *that weapon holds this hand* — is stated in words; the muted styling only distinguishes these informational rows from the item's home row (normal rendering, details, flags), which remains visibly its real location. A two-handed weapon in RANGED consumes both hand rows; one in a hand slot consumes the other. **The paper-doll is one shared composition** (v24.7 — #195): `inv` and bare `equip` render it through the same helper and can never drift (Section 9.1, footnote 21).
1. **Inventory.** A `Slot / Name / Quantity / Details` table, flat alphabetical by name. The Slot cell names the item's equip slot when slotted (`Main hand`) — an item valid in more than one slot names them **all**, joined with `/` in authored slot order: `Main hand/Off hand` (v24.8 — #197) — appending the word for two-handed weapons after the full label — `Ranged (two-handed)` (v24.7 — #194) — and muted `-` when slotless; identical items fold into the Quantity column per the stacking rule below.
1. **Wallet.** One key/value line, **byte-identical** to the `wallet` command's output — one shared renderer, by rule.

Display rules:

- **Details** reads `90%, Uncommon, Bound` — durability + rarity + binding, no brackets. The durability number is colored by the **mechanical durability band** (derived from the band table in 6.5, never its own thresholds: no penalty → value-color, penalty bands → say-color, broken → error-color); rarity words are always rarity-colored in information output; the binding flag reads `Bound | Unbound`.
- Durability appears only for items with `takes_durability_loss=True`; bags show carry bonus instead. Unidentified items show no Details suffix at all — no durability, no carry bonus.
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

