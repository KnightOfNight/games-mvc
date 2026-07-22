# Shyland Brief — B2 Design Rulings Housekeeping

**Type:** ops/housekeeping (does not count against the brief cap) · **Version context:** 22, bucket B2 design session complete
**Scope:** commit the B2 design document; comment, close, and file issues to capture the complete design record; run the issues report. **No game code changes of any kind.**
**Branch:** run in the current CC session's working branch.

This brief is self-contained. Do not consult chat history.

---

## Pre-flight

1. `gh` authenticated; clean tree.

## Step 0 — Self-commit this brief

Save this brief verbatim to `docs/shyland/Shyland_Brief_B2_Design_Rulings_Housekeeping.md` (skip if identical file exists), commit, and **push immediately**. Commit and push at every step boundary below. Never merge.

---

## Step 1 — Commit the design document

Create `docs/shyland/Shyland_V22_B2_Command_Spec_DD.md` with **exactly** the content between the DD-START and DD-END markers below (exclusive of the markers). Commit and push. This DD is the authoritative capture of the B2 design session (2026-07-19); the GDD absorbs it at version closeout; it is transient and will be pruned by the operator only.

<!-- DD-START -->
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
<!-- DD-END -->

Commit and push the DD.

---

## Step 2 — Issue comments

Post each comment via `gh issue comment`. Every comment begins: `Design ruling (2026-07-19 B2 design session). Full spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md.` then the issue-specific text below. Do not close any issue in this step.

- **#111:** The complete command specification exists — chart, footnotes, palette, three-layer response doctrine (error/warn/success), firehose+echo doctrine, state-gating matrix, partial-fulfillment doctrine, resolution pools with the player/NPC name invariant, success sentence standards, information-output kinds, settings standards, chart-derived help, admin gating, combat voice ratification. The DD is the conformance spec the revamp implements. Notable rulings: spend argument order flips to `spend <quantity> <stat>`; bare `sell all` blocked; drop excludes bound items and loses "all"; buy loses "all"; targetless attack removed (aggro auto-engagement made it a fossil); N.noun survives input-only; vendor stock joins examine's pool; `.msg-error` amber defect found (all error call sites re-tag under the doctrine); new commands echo (settings) and the four B3 arrivals are charted.
- **#29:** Ruled via the state-gating matrix: loot (with drop, pickup, equip, unequip, commerce, repair, home, travel, movement) is refused in combat, warn-color. Full matrix in DD §5.
- **#54:** The shipped combat transcript is ratified as the language spec — the v21 work (#64 ordinals, authored attack variety, wound ladder) answered this ticket's complaint. Remaining deltas are color only: crit-in #F08A50 bold added; miss re-colored to muted-color. Implementation rides the B2 output brief.
- **#57:** The chart rules `home` takes no arguments (footnote 2). The "home now" instant variant is DEAD — superseded; home is always the delayed action with cancel as the escape. State matrix: refused in combat and while dying. Remaining design (delay mechanics, arrival) belongs to the B3 pass.
- **#58:** Fully ruled: list renders as the standard table (Slot/Name/Quantity/Details/Price), rarity words rarity-colored in Details, two groups free-first (Price shows muted "free"), alphabetical within groups. DD §9.
- **#59:** Answered by doctrine: every command is timestamped and firehosed as an event; the settings standards fix the specific inconsistencies. Implementation rides the revamp.
- **#61:** Ruled and generalized: any heal attempted at full vitality fails (warn-color); multi-use sequences stop at full with the loot-color line "You have been restored to full health."; use while dying is allowed (self-rescue is deliberate design). DD §7.
- **#65:** The chart rules `use [<quantity>] <item>` (numeric only) — `use 3 healing draught` is legal; the current refusal dies. Sequence semantics per DD §7.
- **#67:** Covered by the completion rule: tab completes exactly each command's pool, per position — equip completes inventory item names. DD §8.
- **#75:** Ruled: `repair all` loops until everything is repaired, funds run out, or 5 attempts; each mend line prints as it lands. DD §7.
- **#88:** Reclassified **information** (not action). No arguments. Admin-gated with stealth (footnote 18; Django Group, live check). Output: Kind 3 table — Character / Status / Time Last Seen; Character as the composite status-page line; Status Online/Offline for now; most recent first. DD §9, §12.
- **#93:** Research question resolved by design: all commands are events (timestamped, firehosed); the settings standards (DD §10) specify every bare/argument behavior. Nothing further to investigate.
- **#96:** Covered by the completion rule: examine completes its full pool union — including NPCs here. DD §8.
- **#98:** Ruled: who becomes one line — `Players online (3): name, name, name` — key-color label, value-color names. DD §9.
- **#109:** Confirmed in the state matrix: spend allowed in combat; the bar refill stands as the bankable free heal, priced-in design; the refill line renders loot-color. DD §5, §6.
- **#112:** Chart: footnote 9 (any arguments accepted) + footnote 18 (admin stealth gating — Django Group, live per-attempt check; non-members get unknown-command; hidden from help and completion). The game never responds to sudo by design; arguments pass to the firehose for the watcher. DD §12.
- **#113:** Chart: `cancel [<command>]` (footnote 12) — optional argument matching a running command; today's pool has at most one member. Allowed in ALL states including combat and dying (the escape hatch is never locked). Success line named per action: "You stop heading home."
- **#76:** This ticket dies: superseded by the command chart — inventory takes no arguments (footnote 2), all arguments ignored. The filtering desire may earn its way back through some future information design, but not through inv's arguments.

## Step 3 — Close two issues

Gated on Step 2 comments landing: close **#76** (not planned / superseded by the chart) and close **#93** (research complete — answered by design; implementation tracked by #111/#59).

## Step 4 — File two new issues (capture numbers at runtime)

1. Title: `client renders error category as amber, ignoring --error` — label `bug`, milestone `Version 22`, label `B2`. Body: `.msg-error` is hard-coded `#C08A3E` (commented "amber") and does not use `--error: #cc4444`. Every error line in the game renders amber. The fix is not a recolor: under the three-layer doctrine (DD §3, docs/shyland/Shyland_V22_B2_Command_Spec_DD.md), every error-emitting call site must be re-tagged as CLI error (error-color) or world-declined (warn-color #E8D44D). Found during the 2026-07-19 design session playtest.
2. Title: `invariant: players and NPCs may never share a name` — milestone `Version 22`, label `B2`. Body: Ruled 2026-07-19 (DD §8): a player character and an NPC may never share a name, ever. Two enforcement edges: (1) character creation rejects any name matching an NPC definition name, case-insensitive, alongside the existing uniqueness and profanity checks; (2) seed-verify gains a check that no NPC definition name collides with any existing character name. Motivated by attack/examine ambiguity resolution — cross-segment ambiguity dies by fiat.

## Closeout

Write `docs/shyland/Shyland_Brief_B2_Design_Rulings_Housekeeping_Closeout_Report.txt`: comments posted (list issue numbers), issues closed, new issue numbers captured, final commit hash. Commit and push. Do not remove or prune any documents.

Finally: run the issues report.
