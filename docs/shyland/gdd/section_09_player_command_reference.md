## 9. Player Command Reference

This section is the authoritative list of all player-facing commands. Commands are typed into the input line and sent to the server. The server is the only authority — no command has any effect unless the server accepts and processes it.

Commands are case-insensitive. Arguments are separated from the verb by a space.

### 9.1 Implemented Commands (v22)

This subsection is the authoritative command reference, absorbed from the v22 B2 command specification DD and synced to the shipped dispatch table at closeout. Every command belongs to one of four types — **action, information, movement, settings** — and its argument cell in the chart is law.

#### The Command Chart

Cell notation: footnote numbers listed left-to-right in argument order; listed = admitted; requiredness per footnote text; `|` = alternatives.

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

#### Footnotes (stable numbering; never renumbered)

1. one optional argument, a human-readable boolean: exactly on, off, yes, no, true, false. Case-insensitive.
2. no arguments expected or required; all arguments are ignored.
3. a literal "all" targeting all possible matches for the command.
4. `<item>` — match against an item name (with or without rarity words).
5. `<NPC>` — match against an NPC name.
6. `<player>` — match against a player name.
7. `<quantity>` optional; a number or the literal "all" (as many as match).
8. `<destination>` — match against a sphere or shard travel destination name.
9. `<*>` — any arguments are accepted.
10. a target is required: at least one listed argument must be present. Bare invocation responds with the standard prompt `What do you want to <verb>?` (error-color).
11. `<quantity>` as footnote 7, but "all" not accepted (numeric only).
12. `<command>` optional; match against the name of a currently running command (e.g. home).
13. a numeric `<quantity>` must be accompanied by a target argument; "all" may stand alone. Bare numeric responds `<verb> <N> what?` (error-color).
14. `<stat>` — match against a stat name (str dex end int wis per).
15. as footnote 13, but the bare-numeric response is `spend <N> points on which stat?`
16. bound items are excluded from this command's candidate pool.
17. "all" requires the target argument for this command: bare `<verb> all` is refused (warn-color) with wording that teaches the noun form.
18. admin-gated with stealth: requires membership in the `admins.shyland` Django auth Group, checked live per attempt. For non-members the command does not exist — absent from help, absent from tab completion, and attempts return the standard unknown-command response.

**Grammar notes:** `N.noun` ordinal selection (e.g. `attack 2.lion`) survives as input-only CLI shorthand across all noun-matching arguments; the game never speaks ordinals except the duplicate-only display ordinals of §5.9 (#64). Argument order is as listed — `spend` is `spend <quantity> <stat>`, flipping the pre-v22 order. `attack`'s chart cell admits `<player>` for the PvP future; until PvP mechanics exist the shipped pool is living NPCs only (recorded implementation judgment). One resolver serves every noun-taking command (v20): ordered token-prefix matching on the player-visible name-with-tier, plural fallbacks, rarity as a closed-vocabulary instance filter (noun optional with a rarity word — `sell all common`), cross-definition ambiguity refuse-lists, rarity-aware protective selection (`sell`/`drop` lowest-first, `equip` highest-first), equipped items always excluded from `sell`/`drop`. A dispatch guard wraps every command: no input, however malformed, can drop the connection.

#### The Three-Layer Response Doctrine (v22)

Every response to a command belongs to exactly one layer, and the layer picks the voice:

- **CLI error (error-color, red):** the parser refused — unknown command, bad syntax, missing required argument (the footnote 10/13/15 standard prompts), settings usage lines. The machine didn't understand you.
- **World declined (warn-color, yellow):** valid command, world says no — resolution failures (no match in the pool, bad index, ambiguity, the sell-all block) and mechanical failures (state-gate refusals, no vendor/repairer/obelisk here, can't afford, sold out, at capacity, repair didn't hold, heal at full, bound-drop attempt, unequip without bag room, failed flee). The world understood you and refused.
- **World answered (normal voices):** success prose, the combat family, loot-color gains.

**Consequence must be seen (#132):** the partial-fulfillment shortfall reports (`You only had N.` on use and drop, `There were only N here.` on pickup, `They only had N.` on buy) and use's no-effect `Nothing happens.` speak in the warn voice — a consequence delivered in the muted ambient voice goes unread. Deliberate exceptions, ruled correct: the sell shortfall keeps its friendly success voice (`You only had 3 — the vendor was happy to take them.`), and the ambient system voice keeps the logout farewell and the muted combat misses.

#### The State-Gating Matrix (v22)

- **In combat — allowed:** attack, flee, use, examine, cancel, say, sudo, quit, all information commands (including `list`), all settings. **Refused (warn, in voice):** buy, sell, repair, drop, pickup, loot (#29), equip, unequip, home, travel, all movement — and **spend** (#131, blocked by later ruling with the first generic refusal `You can't do that while in combat.`; every other combat refusal is a per-command authored line).
- **While dying — allowed:** use (self-rescue heal — deliberate design), cancel, say, sudo, quit, information, settings. Everything else refused (warn).
- **Quit is allowed in both states, and combat continues after quit** — `CombatSession` is database state; no code path ends it on disconnect. The player can die logged out. Tab-closing and quitting are identical in cost, which is what makes the design honest rather than theater.
- `cancel` is allowed in every state — the escape hatch is never locked.

#### Resolution Scope Pools

buy → room vendor stock · sell → inventory excluding equipped (bound sellable — vendors are the designed sink) · drop → inventory excluding equipped and excluding bound (footnote 16) · pickup → room floor · equip → carried equippables (equippability = mechanical layer) · unequip → equipped only (inventory room = mechanical layer) · use → carried consumables, never vendor stock · repair → everything owned including equipped · **examine → the union**: inventory + equipped + floor + vendor stock + NPCs here + corpses + players here (the vendor-examine gap closed; players answer with their composite line) · attack → living NPCs in the room · loot → lootable corpses here · travel → revealed destinations · spend → the six stats · cancel → your running delayed actions.

Pool miss = warn. Same-segment ambiguity: **nearest wins** (self before room before vendor); ordinals and tab disambiguate.

**The name invariant (#122): a player and an NPC may never share a name.** Two enforcement edges: character creation rejects any name matching an NPC definition name, case-insensitive (`That name belongs to the world already.`), alongside the existing uniqueness and profanity checks; and seed verification permanently checks that no NPC definition name collides with any existing character name.

#### Partial Fulfillment Doctrine

Do the possible part and report warmly; fail (warn) only when nothing is possible. Stop when purpose is fulfilled. Specifics:

- Sell/drop/use/pickup shortfalls do the possible part with the warm note preceding the result; any pickup at capacity fails outright (warn); partial `pickup all` takes oldest-on-floor first.
- **Heal sequences (#61, #65):** `use N` applies one item at a time — never pre-announcing a count (combat interleaves; stop-at-full fires mid-sequence); a heal that lands at full prints the loot-color `You have been restored to full health.` and stops the sequence; any heal attempted at full fails (warn).
- **`repair all` (#75):** passes over what is still damaged until everything is repaired, funds run out, or 5 passes; each mend line prints as it lands.

#### Success Sentences and Aggregation

The transactional commands answer with one plain past-tense sentence, item names verbatim with rarity words rarity-colored, articles via the NPC-article machinery: `You buy the Iron Mace Mk 1 for 9 coppers.` · `You sell the Leather Gloves Mk 1 for 3 coppers.` · `You drop the Battle Axe Mk 1.` · `You pick up the Healing Draught Mk 1.` (loot-color) · `You equip the Iron Mace Mk 1.` / swap-aware `You equip the Battle Axe Mk 1, replacing the Iron Mace Mk 1.` (the slot is the paper-doll's job, not the sentence's) · `You unequip the Iron Mace Mk 1.` · `You use a Healing Draught Mk 1.` + effect line · repair's line stands · `You spend 3 points on Dexterity.` + the new value · `You stop heading home.` (cancel, named per action).

**Multi-item output splits by nature:** buy, sell, drop, and pickup **aggregate** — a transaction is one act, so N > 1 emits one count-form line per item definition (`You sell Healing Draught Mk 1 ×100 for 4 silver 50 coppers.` — no article, total money; mixed sweeps emit one line per definition in floor order, singles staying singular; warm shortfall notes precede). **use, repair, and loot stay per-line** — each iteration is its own news. (#126 files the future natural-English pluralization; the count form is never wrong in the meantime.)

#### Corpses and Loot (v22 form)

`loot` is `all | <NPC>`: `loot all` sweeps every corpse in the room (per-item lines, then the summary); `loot <NPC>` loots that NPC's corpse, with `N.noun` disambiguating among same-name corpses. Bare `loot` prompts (footnote 10 — the v18 most-recent-corpse convenience and the v20 item-noun/union forms are retired). Only the killing character may loot items; currency is always transferred on first loot of a corpse; a corpse that never had loot to give answers `The <npc> carried nothing worth taking.`

#### Information Output Standards

Three kinds, one punctuation law — **colon = the value is on the line; ellipsis = structure follows below**. Headers are uniformly key-color, embedded counts included (`Inventory (12/250)...`); table column guides are muted; rows are value-color.

- **Kind 1** — `Key: Value` (the `wallet` archetype).
- **Kind 2** — `Key...` + indented value list.
- **Kind 3** — `Key...` + table (muted column headers, value rows).

Shipped surfaces: `inv` = the Equipment paper-doll + Inventory table + Wallet line (Section 6.11); `list` = the vendor table (Section 6.12); `wallet` = the shared Kind 1 line; `who` = one line, `Players online (3): Shy-Guy, Sharon-Love, Marvin`; `stats` = the character sheet with the six stat rows (base + gear parenthetical), a blank line, the Armor row, and a blank line before Unspent; `last` = the admin Kind 3 table; `look` untouched by the standards (the room render has its own v20/v21 rules). Durability numbers are colored by the mechanical band, derived, never owned; rarity words always rarity-colored.

#### Settings Standard

Three settings commands — `brief`, `echo` (v22, new), `timestamps` — share one shape: six accepted words (`on off yes no true false`, any case); **bare form reports** the current setting (`brief room display is off.`); set form answers the "now" sentence (`command echo is now on.`); invalid input answers the CLI `Usage: <cmd> [on|off]`. Stateless, idempotent, plain prose. **Defaults: brief off (flipped in v22 for new characters; existing players kept their setting), echo on, timestamps on.** Echo is **pane-only**: `echo off` suppresses the player's own `> command` echo lines in their pane and nothing else — server behavior, timestamps, and the future firehose are untouched; every command remains a stamped event.

#### Help

`help` is generated from the chart: four type sections (key-color `...` headers), Kind-3 `Command / Usage / Description` tables, usage strings compiled from the chart cells in BASH notation (`<>` required, `[]` optional, `|` alternatives), authored one-line descriptions, and four shared bottom sections (Arguments, Quantities, Settings, Tab completion). Admin commands render only for members. Help always ends with a blank line and the Kind-1 `Version:` line — `SHYLAND_VERSION`, the single source of truth for the player-visible version, bumped to the release stamp at every version closeout (point releases bump it on main). The constant tells the truth about the code it ships with.

#### Admin Commands and Stealth Gating (v22)

The Django auth Group **`admins.shyland`** grants in-game admin. `sudo` and `last` gate on membership, **checked live on every attempt** — no session caching, revocation instant. For non-members the commands do not exist: absent from help, absent from completion, and attempts return the unknown-command response **byte-identical to gibberish input** (footnote 18).

- **`sudo <anything>`** (#112) — speak to the watcher: the command echoes like any command, and the game never responds — no output, no acknowledgment, by design. The arguments' journey to a listener arrives with the firehose (#33/#37).
- **`last`** (#88) — the roster: a Kind-3 `Last seen...` table (`Character / Status / Last seen`), the composite character line (`Shy-Guy - Level 10 Highborn Blade`), Online/Offline from presence, and three time forms — `never` (no recorded connect), `since <ISO-8601 UTC>` (online), bare stamp (offline) — ordered online-by-recency, then offline-by-recency, then never. Every character's last-connect is recorded at websocket accept regardless of who can read it.

#### Delayed Actions and `cancel` (v22)

The **delayed-action registry** — one named, connection-bound task per running delayed action — is the standing template for every future delayed action; `home` is its first resident (design in Section 2.11). `cancel` (#113): bare with nothing running answers `You don't have anything to cancel.` (warn, verbatim); bare with exactly one running cancels it; a named argument prefix-matches the running-action names. A registry task dies silently with the connection — intent state dies with the intender.

#### Tab Completion

Server-authoritative (v20): the client round-trips the current line and receives context-correct candidates. The completer offers **exactly each command's pool at each position, literals included** — `all` only where the grammar accepts it, the six boolean words for settings, stat names for spend, revealed destinations for travel, corpse names for loot, running-action names for cancel, and examine's full union; ordinal forms where duplicates exist. The connect-time verb list omits admin verbs for non-members.

The unknown command response directs players to `help`: *"Unknown command. Type 'help' for a list of commands."* — a CLI error, byte-identical to what a non-member sees for an admin command.

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

|`forage`              |Gather plant/organic materials in applicable rooms|
|`mine`                |Gather ore/mineral materials in applicable rooms  |
|`salvage`             |Disassemble items or gather tech components       |
|`harvest`             |Gather zone-specific resources                    |

#### Combat

*(All combat commands are now implemented — see Section 9.1.)*

#### Character & Inventory

|Command           |Description              |
|------------------|-------------------------|
|`quests`          |Show active quest journal|

*(The formerly planned `equipment`/`eq` command is superseded: `eq` is `equip`'s alias in the v22 chart, and the Equipment paper-doll in `inv` shows all 14 slots always — an equipped-only view no longer earns its own verb.)*

#### Travel

|Command            |Description                                            |
|-------------------|-------------------------------------------------------|
|`recall`           |Teleport to bound recall point (requires recall scroll). *Note (v22): the `home` command now covers the command-driven return to the Heart (Section 2.11); recall survives as the item-driven variant and awaits the zones-and-travel version alongside attunement (#38).*|
|`enter <exit name>`|Use a named exit (non-directional)                     |

### 9.3 Command Design Rules

- Every command must work via keyboard input only — no mouse-only interactions. Screen reader users must be able to access all functionality through the input line.
- Commands should be short, memorable, and consistent with classic MUD conventions where possible.
- **The chart is law.** Every command's argument behavior lives in its chart cell (Section 9.1); footnote numbers are stable and never renumbered. A new command enters the chart before it enters the code.
- **Every refusal belongs to a layer** (the three-layer doctrine, Section 9.1): CLI errors are red, world-declines are yellow, and consequence must never speak in the ambient voice.
- Every unrecognised command gets a helpful redirect, not a bare error: *"Unknown command. Type 'help' for a list of commands."*
- `help` is generated from the chart and ends with the `Version:` line. When a new command is implemented, it is added to the chart, the dispatch table, and this section — one source of truth, three synchronized surfaces.
- **Boolean commands always require an explicit value to set.** Never a bare toggle. The bare form *queries* — `brief`, `echo`, and `timestamps` all report their current value; six accepted words set it (the settings standard, Section 9.1).
- **Every submitted command echoes** into the output pane before its result — `> command as typed`, muted, timestamped — a transcript of the player, never re-broadcast to others, echoed even for invalid input so errors keep their context. The `echo` setting suppresses the display pane-side only; the event still exists.
- **Setting changes are events** (stamped confirmations); reports and renderings are not — see the envelope display rule in 10.2.

-----

