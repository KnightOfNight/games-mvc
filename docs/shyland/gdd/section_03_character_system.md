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
- Vitality and Longevity maximums recalculate and current values are set to the new maximums (level-up fully restores both bars; the maxima formulas read **effective** stats — Section 3.4):
  - `vitality_max = (END × 10) + (STR × 3) + (level × 5)`
  - `longevity_max = (END × 8) + (WIS × 5) + (level × 5)`
- +1 skill point (deferred — skill tree not yet implemented)
- New abilities may unlock at certain level thresholds (deferred)

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

**Armor — Option C (v22).** No schema change: armor's base protection is **derived** from slot and Mk tier, with rolled `physical_resist` as bonus on top.

- **Total Armor Value (TAV)** = Σ(slot weight × Mk tier over worn armor pieces) + Σ(rolled `physical_resist` over ALL equipped items, any type).
- **Slot weights** (the authored table; only these eight slots carry armor): CHEST 3, HEAD 2, LEGS 2, OFF_HAND 2 (shields), SHOULDERS 1, HANDS 1, WAIST 1, FEET 1. A full set = 13 per Mk tier.
- **Mitigation** applies to NPC→player damage only (players mitigate; NPCs never do): each incoming hit is reduced by the fraction `TAV / (TAV + K)`, K = 48 — a full Common Mk 1 set blocks ~21%. Deterministic per hit; no roll.
- **Floors in both directions:** when TAV > 0, the reduction is at least 1 (armor never does nothing), and no hit is ever reduced below 1 damage (the existing minimum-damage clamp survives beneath it).
- **Even Common armor works** — rarity means "better at armoring," never "allowed to armor."
- A **broken** piece (0% durability) contributes nothing to TAV — the non-functional band with teeth.
- **Visibility:** the `stats` sheet carries the Armor row (`Armor: 13 (blocks 21%)`, percentage derived live from the curve; naked reads `Armor: 0`, nothing hidden), and an armor item's `examine` confesses its contribution (`Armor: 3 per Mk`, appending `(worn: 3)` when equipped and `(worn: 0 — broken)` when broken). Per-hit damage receipts were tried and removed — the permanent surfaces carry the visibility; incoming hit lines state only the number that moved the bar.
- The derived table retires gracefully if authored per-item armor bases ever ship (#129).

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
- While Dying, only self-preservation and speech remain (v22 matrix): `use` (self-rescue), `cancel`, `say`, `quit`, information, and settings — everything else is refused. Quitting doesn't save you: the dying clock runs on the server, and an unattended death runs the full sequence.
- **Revival:** any vitality restoration above zero while Dying clears the state — the character rises with **exactly the healed amount** (a strong enough potion may legitimately restore full; a weak one stands you up at a sliver into whatever is still swinging). Combat resumes naturally: the character was never removed from the session. Any other player in the room can also revive them with an item or ability once such tools exist — no group membership required.
- If not revived within 30 seconds → **Dead**. A death declaration ("The darkness takes you."), then the player respawns at their bound recall point (default: The Convergence) with full bars, the client fully re-synced (fresh room output, channel-group swap).
- On death: all remaining `EffectInstance` rows cleared; pending combat actions cleared; the `CombatSession` ends; Acuity resets (death resets it; level-ups do not).
- **XP loss:** 10% of current XP (cannot lose a level); applies at level 10+ only.
- **Durability loss:** all equipped items with `takes_durability_loss=True` lose 10% per death; after 10 unrepaired deaths an item breaks. The flag is the only gate. (v19 convention: `takes_durability_loss=False` is reserved for genuinely rare items and Artifacts — ordinary gear wears, including the free starter kit; the durability loop is part of onboarding.)
- **Link-dead policy (ruled, deliberate):** closing the browser mid-combat abandons the character to the fight — the world keeps happening to link-dead characters, and dying offline runs the full sequence to an unattended death. Quitting is the same bargain made politely (v22): `quit` is allowed in combat, combat continues after it, and the player can die logged out — tab-closing and quitting are identical in cost, which is what keeps the design honest rather than theater.
- In PvP zones only: chance to drop one non-equipped carried item
- A **Death Shard** item is left at the death location; player can retrieve it within 30 minutes to recover any dropped item

**Hardcore Mode** (optional, on character creation): permadeath. Character deleted on death. Hardcore characters are flagged visually and have a separate leaderboard.

-----

