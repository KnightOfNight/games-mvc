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
   stat_bonus     = relevant EFFECTIVE stat value (STR melee / DEX ranged / INT spells)
   acuity_mod     = band-relative deviation modifier (Section 4.2): 1.0 inside the
                    Origin band; 1.0 + distance above band_high (focus target only);
                    1.0 − distance below band_low (all targets).
   durability_mod = performance multiplier from weapon's durability table (1.0 = no penalty;
                    1.0 if no weapon equipped)
   raw_damage     = (base_damage + stat_bonus) × acuity_mod × durability_mod

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

5. Armor mitigation (v22 — NPC→player damage only; Section 3.6):
   reduction = max(1, round(damage × TAV / (TAV + 48)))  when TAV > 0
   landed    = max(1, damage − reduction)
   Deterministic per hit. The incoming line's number is the damage that moved the bar.

6. Elemental/type resistances as percentage reduction after armor (future — damage
   types are not modeled in v22; proc names are flavor)
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

**v22 status note:** damage types are **not modeled** in v22 — all damage is untyped, and the proc-family stat names (bleed, stun, poison, electric) are flavor vocabulary only: they add damage, they carry no status effects and no elemental mechanics. The table above remains the design target for the future typed-damage system; when it ships, `magic_resist` and `radiation_resist` (deliberately inert in v22) gain their consumers.

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

**The v22 armored re-bless (B5 budget guard).** With armor live, the six boss budgets were recomputed survey-lite for the 25/25 reference build in full Common Mk 1 armor (TAV 13, ~21% mitigation): expected rounds unchanged by construction (armor touches only incoming damage), expected potions 0/4/6/6/6/10 vs the naked 0/6/8/7/7/10. **No boss dropped to a zero-potion fight** (the Matron was already zero-potion naked) and the Crowned Devourer still demands 10 — the mitigation constant **K = 48 stands blessed**. The intended shape held: armor softens the ladder without trivializing it, and gear — not retuning — is what opens the delve trio to non-reference builds.

-----

