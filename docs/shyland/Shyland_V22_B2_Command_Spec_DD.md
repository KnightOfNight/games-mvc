# Shyland V22 B2 Command Specification — Design Document

Status: complete design record of the B2 design session, 2026-07-19. Authoritative until absorbed into the GDD at v22 closeout. Implementation briefs derive from this document.

## 1. Command Chart

Types: action, information, movement, settings. Cell notation: footnote numbers listed left-to-right in argument order; listed = admitted; requiredness per footnote text; `|` = alternatives; `·` separates behavior notes from argument slots.

| Type | Command | Arguments | New in v22 |
|---|---|---|---|
| action | attack (kill, k) | 5 \| 6 · 10 | |
| | buy | 11 4 · 10 | |
| | cancel | 12 | YES |
| | drop | 11 4 · 10 · 16 | |
| | equip (eq) | 4 · 10 | |
| | examine (ex) | 4 \| 5 \| 6 · 10 | |
| | flee | 2 | |
| | home | 2 | YES |
| | loot | 3 \| 5 · 10 | |
| | pickup (p) | 7 4 · 10 · 13 | |
| | quit | 2 | |
| | repair | 3 \| 4 · 10 | |
| | say | 9 · 10 | |
| | sell | 7 4 · 10 · 13 · 17 | |
| | spend | 7 14 · 10 · 15 | |
| | sudo | 9 · 18 | YES |
| | travel | 8 | |
| | unequip (uneq) | 4 · 10 | |
| | use | 11 4 · 10 | |
| information | help (?) | 2 | |
| | inventory (inv) | 2 | |
| | last | 2 · 18 | YES |
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
| | echo | 1 | YES |
| | timestamps | 1 | |

### Footnotes (stable numbering; never renumbered)

1. one optional argument, a human-readable boolean: exactly on, off, yes, no, true, false. case-insensitive.
2. no arguments expected or required; all arguments are ignored.
3. a literal "all" targeting all possible matches for the command.
4. \<item\> match against an item name (with or without rarity words).
5. \<NPC\> match against an NPC name.
6. \<player\> match against a player name.
7. \<quantity\> optional; a number or the literal "all" (as many as match).
8. \<destination\> match against a sphere or shard travel destination name.
9. \<\*\> any arguments are accepted.
10. a target is required: at least one listed argument must be present. bare invocation responds with the standard prompt "What do you want to \<verb\>?" (error-color).
11. \<quantity\> as footnote 7, but "all" not accepted (numeric only).
12. \<command\> optional; match against the name of a currently running command (e.g. home).
13. a numeric \<quantity\> must be accompanied by a target argument; "all" may stand alone. bare numeric responds "\<verb\> \<N\> what?" (error-color).
14. \<stat\> match against a stat name (str dex end int wis per).
15. as footnote 13, but the bare-numeric response is "spend \<N\> points on which stat?"
16. bound items are excluded from this command's candidate pool.
17. "all" requires the target argument for this command: bare "\<verb\> all" is refused (warn-color) with wording that teaches the noun form.
18. admin-gated with stealth: requires membership in the shyland admin Django auth Group, checked live per attempt. For non-members the command does not exist — absent from help, absent from tab completion, and attempts return the standard unknown-command response.

Additional grammar: N.noun ordinal selection (e.g. `attack 2.lion`) survives as input-only CLI shorthand across all noun-matching arguments; the game never speaks ordinals except the duplicate-only display ordinals already shipped in v21 (#64). Argument order is as listed (spend is `spend <quantity> <stat>`, flipping the old order).

## 2. Named Palette (complete)

| Name | Value | Voice |
|---|---|---|
| key-color | #7FB3D5 | labels; section headers; the map here-dot |
| value-color | #E8E4D8 | content; success prose; the known |
| muted-color | #6b6b80 | column guides, command echo, the unknown, combat misses |
| error-color / agro-color | #cc4444 | CLI errors; hostile rooms |
| say-color | #f0c060 | speech (was --chat) |
| warn-color | #E8D44D | the world declined (resolution + mechanical failures) |
| loot-color | #4caf7d | gains: reward category, NPC death_message broadcasts, pickup lines, heal-to-full, #109 refill line |

Combat family: hit-out #C4453F · crit-out #E24B4A bold · hit-in #E0724A · crit-in #F08A50 bold (NEW; ships dormant if NPC crits don't yet occur) · miss = muted-color (#8A887F deleted). Direction axis: red = dealing, orange = taking; crits brighter + bold.

Known defect: `.msg-error` is hard-coded #C08A3E (amber) and ignores `--error` — every "error" currently renders amber. Fix is not a one-liner: all error-emitting call sites re-tag into the three-layer doctrine below.

## 3. Three-Layer Response Doctrine

- **CLI error (error-color):** the parser refused — bad syntax, missing required argument (footnote 10/13/15 standard prompts), unknown command.
- **World declined (warn-color):** valid command, world says no — resolution failure (no match in pool) and mechanical failure (failed flee, can't afford, repair didn't hold, heal at full, state-gate refusals, sell-all block, bound-drop attempt, unequip with full bags).
- **World answered (normal voices):** success prose per section 6; combat family; loot-color gains.

## 4. Firehose & Echo Doctrine

Everything flows except a deliberate exclusion list: (1) information command **results** (commands + errors still flow), (2) successful examine output. Say output flows as the bare utterance only, no metadata (the command record carries the metadata). Movement moves are events. All world-generated output (combat, aggro, respawn, others' visible acts) flows. Echo is pane-only (suppresses the player's own muted arrow-echo line); timestamps pane-only; both never affect the firehose. Every command is timestamped and firehosed. Admin-gating denials render as unknown-command and flow as errors.

## 5. State-Gating Matrix

In combat — **allowed:** attack, flee, use, spend (#109: bar refill = bankable heal, loot-color line), examine, cancel, say, sudo, quit, all information, all settings. **Refused (warn-color):** buy, sell, list-as-commerce n/a (list allowed — information), repair, drop, pickup, loot (#29), equip, unequip, home, travel, all movement.
Correction for precision: all eight information commands are allowed in combat, including list.
While dying — **allowed:** use (self-rescue heal — deliberate design), cancel, say, sudo, quit, information, settings. Everything else refused (warn-color).
Quit is allowed in both states; **combat continues after quit — the player can die logged out** (CombatSession is DB state). Tab-closing and quitting are identical in cost.

## 6. Success Output Standards (transactional ten)

One plain sentence, past-tense of done, item names verbatim with rarity words in rarity color, article logic reused from the NPC article machinery. Multi-item operations print one line per item as they land. Colors: value-color default; loot-color = gained for free (pickup lines, heal-to-full, #109 refill); commerce plain with amounts.

- buy: "You buy the Iron Mace Mk 1 for 9 coppers."
- sell: "You sell the Leather Gloves Mk 1 for 3 coppers." Partial: "You only had 3 — the vendor was happy to take them."
- drop: "You drop the Battle Axe Mk 1."
- pickup (loot-color): "You pick up the Healing Draught Mk 1."
- equip: "You equip the Iron Mace Mk 1." Swap: "You equip the Battle Axe Mk 1, replacing the Iron Mace Mk 1."
- unequip: "You unequip the Iron Mace Mk 1."
- use: "You use a Healing Draught Mk 1." + effect line; stop-at-full (loot-color): "You have been restored to full health."
- repair: current line stands: "Leather Gloves Mk 1 is restored to full condition. (1 copper)"
- spend: "You spend 3 points on Dexterity." + new value; in-combat refill line loot-color.
- cancel: named per canceled action: "You stop heading home."

## 7. Partial Fulfillment Doctrine

Do the possible part and report warmly; fail with warn-color only when nothing is possible (any pickup at capacity fails outright); stop when purpose is fulfilled (heal-to-full stops the sequence; any heal at full fails, warn — #61 generalized). Deterministic order where selection matters: partial `pickup all` takes oldest-dropped-first. Bounded retries where chance is involved: `repair all` loops until all repaired, funds exhausted, or 5 attempts (#75). Applies by analogy to buy/drop shortfalls.

## 8. Resolution Scope Pools

buy: room vendor stock · sell: inventory excluding equipped (bound sellable — vendors are the designed sink) · drop: inventory excluding equipped and excluding bound (footnote 16) · pickup: room floor · equip: inventory (equippability = mechanical layer) · unequip: equipped only (requires inventory room = mechanical layer) · use: inventory excluding equipped, never vendor stock · repair: your items including equipped · examine: union of inventory + equipped + room floor + vendor stock + NPCs here + players here (fixes the vendor-examine gap) · attack: living NPCs and players in room · loot: lootable corpses here · travel: all sphere/shard destination names (fog = mechanical refusal) · spend: the six stats · cancel: your running delayed actions.
Tab completion completes exactly the pool, per command per position, literals included ("all"). Pool miss = warn-color. Same-segment ambiguity: nearest wins (self before room before vendor), ordinals/tab disambiguate.
**Name invariant: a player and an NPC may never share a name.** Two enforcement edges: character creation rejects names matching any NPC definition name (case-insensitive, joining existing uniqueness+profanity checks), and seed-verify checks no NPC definition name collides with any existing character.

## 9. Information Output Standards

Three kinds: **Kind 1** Key: Value (key-color key+colon, value-color single value; archetype wallet). **Kind 2** Key… + indented value-color list (ellipsis when structure follows). **Kind 3** Key… + table (muted-color column headers, value-color rows). Headers uniformly key-color including embedded counts; "items" removed: `Inventory (12/250)...`.
- wallet: unchanged (Kind 1 archetype). inv's Wallet line matches exactly (newline removed); **shared renderer required**.
- inv: Equipment (Kind 3), Inventory (Kind 3), Wallet (Kind 1).
- Equipment table: columns Slot/Name/Details. All slots always shown, anatomical order head→feet: Head, Neck, Shoulders, Back, Chest, Main hand, Off hand, Ranged, Hands, Ring, Ring, Waist, Legs, Feet (SLOT_ORDER re-authored; sentence-case labels, bracket codes dead). Empty slots: muted "-" in Name and Details. Details = durability + flags, no brackets: "90%, Uncommon, Bound"; durability number colored by the **mechanical durability band** (derive, never own thresholds): no-penalty→value, penalty bands→say, severe/non-functional→error. Rarity words always rarity-colored in information output.
- Inventory table: + Quantity after Name; Slot column empty unless slotted; flat alphabetical by name.
- list: same table + Price column (durability kept); two groups, free first (Price reads muted "free"), then priced; alphabetical within groups.
- who: one line: `Players online (3): Shy-Guy, Sharon-Love, Marvin` (key-color label, value-color names).
- stats: as-is + blank line before Unspent stat points; inherits general rules.
- last: Kind 3, columns Character/Status/Time Last Seen; Character composite "Shy-Guy - Level 10 Highborn Blade"; Status Online/Offline; most recent first. Admin-gated (footnote 18).
- look: unchanged.

## 10. Settings Standards

Six accepted words (footnote 1). Bare: "brief room display is on" (set message minus "now"). Set: "brief room display is now on" / "command echo is now on" / "output timestamps are now on" — stateless, idempotent, plain prose, no color play. CLI error: error-color `Usage: brief [on|off]` (canonical pair shown; synonyms silently accepted). Defaults (every setting lists one): **brief off, echo on, timestamps on.** Fully firehosed.

## 11. Help

Generated structure derived from the chart: four type sections (key-color "..." headers), Kind-3 tables (Command/Usage/Description, muted headers), BASH notation compiled from cells (`<>` required, `[]` optional, `|` alternatives), authored example-free descriptions, shared bottom sections (Arguments, Quantities, Settings, Tab completion). Admin commands hidden from non-members. Reference mock exists from the design session.

## 12. Admin Gating

Django auth Group (seeded by the implementing brief); grants in-game admin. sudo and last gate on membership, checked live per attempt (revocation instant). Stealth per footnote 18. sudo never receives a game response by design (firehose-AI command; the monitor arrives with #37).

## 13. Combat Voice

The shipped v21 transcript is ratified as the spec: authored per-NPC attack variety, wound ladder (moderately/badly wounded, near death, dead), duplicate-only ordinals with retarget line, engagement lines, "You have slain X! (+N XP)" in loot-color (reward category), death_message broadcasts in loot-color. Deltas: crit-in class added; miss re-colored muted; the borrowed-genre flavor (snarling beetles) is intentional.
