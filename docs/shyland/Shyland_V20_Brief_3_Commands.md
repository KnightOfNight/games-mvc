# Shyland V20 Brief 3 — Commands

Implements GitHub issues **#22** (grammar foundation), **#3** (loot all), **#21** (sell all), **#19** (tab completion), **#20** (dispatch guard), **#23** (movement-in-combat bug), **#45** (timestamps toggle), and **#48** (rarity display move). Self-contained; do not consult chat history. Applies third, after Brief 1 (Map System) and Brief 2 (Output Envelope). **Never remove or prune any transient document** — the operator prunes.

---

## Part A — The resolver (one module, authoritative spec)

Create `django/src/apps/shyland/command_grammar.py`. It replaces every existing item-matching path (`parse_item_noun`, the `startswith` matchers in `cmd_buy`/`cmd_sell`, and any others found). `parse_item_noun` may remain as a thin wrapper or be deleted at call sites — no second matcher may survive.

### A1. Reference grammar

```
<verb> [all | N] [rarity] [noun]     and the retained index form: <verb> [rarity] N.noun
```

- `all` — every matching instance. `N` (positive integer) — exactly N, all-or-nothing.
- `rarity` — closed vocabulary: `common uncommon rare epic legendary artifact`. An instance FILTER applied before matching and selection. **Authoring law (enforce in the extended seed verify): no ItemDefinition name begins with a rarity word.**
- Noun may be omitted **only when a rarity qualifier is present** (e.g. `sell all common`). A bare `sell all` (no rarity, no noun) is refused: "Sell all of what? Try 'sell all <item>' or 'sell all <rarity>'."
- `N.noun` — the Nth matching instance (existing syntax, kept). Combines with rarity: `sell common 2.axe`.

### A2. Matching

- Match target per item: the tokens of the **player-visible name with tier** — `get_display_name_with_tier` tokens, lowercased (e.g. `battle axe mk 1` → `[battle, axe, mk, 1]`; suppressed-suffix items have no `mk N` tokens; unidentified items use their mystery name as shown). **Rarity is never a name token.**
- A reference matches when its tokens prefix-match name tokens as an **ordered subsequence** (`axe` ✓, `battle axe` ✓, `axe 1` ✓, `b a` ✓; `rap` does NOT match `carapace`).
- Case-insensitive. Plural fallbacks on a token with no match, tried in order: strip `es` then `s`; `ves`→`fe` (knives→knife); `ies`→`y` (berries→berry).

### A3. Ambiguity and selection

- Matches spanning **multiple distinct ItemDefinitions** → refuse with a one-line disambiguation list of the distinct names ("Which do you mean: Healing Draught, Hearty Draught?"). Never guess across definitions.
- Multiple instances of the **same definition** → deterministic selection: `sell`/`drop` pick lowest rarity, then most damaged, then oldest; `equip` picks highest rarity, then best condition, then oldest; all other commands pick oldest. A rarity qualifier overrides the rarity dimension by filtering first.
- **Equipped items are always excluded** from `sell` and `drop` resolution, including `all`. If the only matches were equipped: "You'll have to unequip it first."

### A4. Candidate scoping

The resolver takes a candidate list; each command supplies its own: `use` → carried consumables; `equip` → carried equippables; `unequip` → equipped items; `sell`/`drop` → carried unequipped; `buy` → the room vendor's stock (ItemDefinitions — match on definition name + rarity of the stock entry); `pickup` → items on the ground here; `loot` → the corpse's contents; `examine` → carried + ground; `repair` → carried + equipped. `attack`/`kill` → room NPCs, same ordered token-prefix matching, no all/N/plurals/rarity.

### A5. Authoritative unit-test table

Ship as a pytest suite (`test_command_grammar.py`); this table is authoritative — implement to it, and add cases freely but change none. Inventory fixture: Battle Axe Mk 1 ×2 (one Uncommon 100%, one Common 60%), Iron Mace Mk 1 (Common, equipped, bound), Healing Draught ×7 (Common, suppressed suffix? — use actual definition config), Animal Hide ×3 (Common), Insect Carapace ×2 (Common), Hunting Knife ×2 (one Common, one Rare), one unidentified item with mystery name "a strange trinket".

| # | Command args | Candidates | Expected |
|---|---|---|---|
| 1 | `axe` | sell | Common Battle Axe (lowest rarity first) |
| 2 | `battle axe mk 1` | sell | Common Battle Axe |
| 3 | `uncommon axe` | sell | Uncommon Battle Axe (qualifier filter) |
| 4 | `axe` | equip | Uncommon Battle Axe (highest rarity first) |
| 5 | `all axes` | sell | both Battle Axes (plural strip; equipped-exclusion N/A) |
| 6 | `2.axe` | sell | second axe in stable order |
| 7 | `mace` | sell | refuse — only match is equipped |
| 8 | `mace 1` | unequip | Iron Mace (tokens mace,1 ordered) |
| 9 | `draught` | use | a Healing Draught |
| 10 | `draughts` | use | a Healing Draught (plural) |
| 11 | `10 draughts` | buy(vendor stocking them) | 10× purchase, all-or-nothing |
| 12 | `5 hides` | sell | refuse — "You only have 3." |
| 13 | `all hides` | sell | all 3 Animal Hides |
| 14 | `all carapaces` | sell | both (es-strip) |
| 15 | `knives` | sell | Common Hunting Knife (ves→fe plural matches both; both are one definition, so lowest-rarity selection applies — no refuse-list) |
| 16 | `rare knife` | sell | Rare Hunting Knife |
| 17 | `all common` | sell | every unequipped Common item; zero-value items skipped with summary line |
| 18 | `all` | sell | refuse with usage line |
| 19 | `h d` | use | Healing Draught (ordered subsequence) |
| 20 | `d h` | use | not found (order violated) |
| 21 | `rap` | sell | not found (no mid-word matches) |
| 22 | `strange` | examine | the mystery-named item |
| 23 | `trinket` | use (not a consumable) | "You aren't carrying that." (candidate scoping) |
| 24 | `hide` vs `hides` casing `HIDE` | sell | case-insensitive match |
| 25 | `epic axe` | sell | not found (qualifier filters to empty) |
| 26 | `common 2.knife` | sell | refuse — only one Common knife ("bad index" path) |
| 27 | `dra` | buy (vendor stocking Healing Draught AND Draught of Vigor — add the second definition to the vendor fixture) | refuse with disambiguation list naming both |
| 28 | NPC: `spider` among cave spider + spitting spider | attack | refuse-list across NPC names? — same rule: multiple distinct NPC definitions → disambiguation list |
| 29 | NPC: `cave` | attack | cave spider |
| 30 | `all spiders` | attack | refuse — all/N not valid for attack ("You can only attack one target.") |

Add coverage for: suppressed-suffix names carrying no `mk` tokens; `sell uncommon` with exactly one uncommon (sells it) and with two distinct uncommon definitions (refuse-list); ordering stability of `N.noun` across calls.

## Part B — Adopt the resolver everywhere

Rewrite the argument handling of `cmd_use`, `cmd_sell`, `cmd_buy`, `cmd_pickup`, `cmd_drop`, `cmd_equip`, `cmd_unequip`, `cmd_examine`, `cmd_loot`, `cmd_repair`, `cmd_attack` onto Part A. New behaviors: **#3 `loot all`** — loots everything on the targeted corpse, listing each item; usual messaging when nothing to loot. **#21 `sell all <noun>` / `sell N <noun>` / `sell all <rarity>`** — per grammar; each sale line as today, plus a one-line total ("Sold 3 items for 2s 4c."); zero-value items skipped with a summary mention. `buy N` checks funds and carry capacity up front. Messaging keeps the existing voice ("You aren't carrying that.", "They don't sell that.").

## Part C — Dispatch guard (#20)

Wrap the entire verb dispatch in `receive_json` in a catch-all: on any handler exception, log the full traceback server-side, send the player one `error`-category line — "Something went wrong with that command." — and keep the connection alive. Verify with a deliberately raising test hook (removed after) or a unit test around the dispatcher. The original `loot all` crash trigger is fixed by Part B regardless; the guard must land independently.

## Part D — Movement blocked in combat (#23)

Directional movement while in an active combat session refuses without moving: "You can't just walk away from a fight — flee!" (`error` category). `flee` behavior unchanged. Applies to all six directions; `travel` already requires non-combat context (verify; align its message style if it doesn't).

## Part E — Timestamps toggle (#45; migration required)

`Character.show_timestamps = models.BooleanField(default=True)`. New command `timestamps on|off` (explicit value required; bare `timestamps` → usage: "Usage: timestamps on|off"). Writes the field, confirms ("Timestamps are now on."), and the client-state sync payload carries it; the client shows/hides the `[HH:MM:SS.ss]` prefix accordingly, including on reconnect and across devices. Envelope fields themselves always present regardless.

## Part F — Rarity display move (#48; atomic with the parser)

Introduce one shared composition helper and adopt it at **every** item-line site (inventory, equipment, examine, loot listings, ground/what's-here listings): `<name with tier>[ xN]  <existing suffix e.g. durability>  [<Rarity>, Bound|Droppable]`. Rarity capitalized; `Bound` = soulbound by any route; `Droppable` = unbound. Unidentified items show no rarity in the block (`[Bound]`/`[Droppable]` alone). The old leading `Rarity` column/prefix is removed everywhere. Flag-block styling (colors, whether Common displays) is explicitly left for the output & messaging brief — this brief ships the plain-text form only.

## Part G — Tab completion (#19)

- On connect, the server sends the verb+alias list (from the dispatch table — GDD §9 sync happens at closeout as usual).
- Client Tab in the command bar: at verb position, complete/cycle from the verb list; at argument position, send `{"type":"complete","text":"<current line>"}`; server replies `{"type":"complete","options":[...]}` with context-correct candidates per Part A4's scoping for the parsed verb, including grammar qualifier words (`all`, rarity words) where valid. Repeated Tab cycles options; Escape or typing resumes normal input. No completion is offered for verbs without noun arguments.
- All completion is server-computed from the same resolver candidate providers — one source of truth; nothing trusted from the client.

## Part H — Verification (all must pass before the architecture doc step)

1. The Part A5 suite passes in full, including the added coverage cases.
2. Seed verify extended with the authoring law: no ItemDefinition (or NpcDefinition) name begins with a rarity word.
3. Manual checklist with the real kit: `sell axe` / `sell uncommon axe` / `equip axe` selection order observed as specified; `sell all hides` and `sell 2 hides` at a vendor; `buy 10 draughts` at a ring cart (VND-9 or Mother Tansy); `loot all` on a boss corpse lists everything; `sell all common` flushes trash with zero-value summary; `2.axe` picks the second; disambiguation list fires when two definitions match; equipped Iron Mace refuses to sell until unequipped.
4. Every item line everywhere shows the Part F composition; no leading rarity remains anywhere; `[Uncommon, Droppable]` and `[Common, Bound]` forms confirmed in play.
5. `timestamps off` hides prefixes immediately, survives reconnect and a second browser; `timestamps` alone shows usage; migration applied.
6. Directional movement during combat refuses with the message; `flee` still works; movement fine out of combat.
7. Dispatch guard: a forced handler exception produces the error line, a server-side traceback log, and a live connection.
8. Tab completion: verb-position cycling; argument completion for use/buy/sell/attack contexts each verified; qualifier words offered where valid; behavior sane with an empty candidate set.
9. No regressions in commands not listed (look, say, who, travel, spend, brief, stats, quit, help).

Close **#22, #3, #21, #19, #20, #23, #45, #48** (closing comments referencing this brief), gated on all checks above.

## Part I — Architecture doc update (LAST — gated on all implementation and verification above passing)

Update `docs/shyland/Shyland_Architecture_v20.md` in place, no version bump: the command grammar module and its spec (grammar, matching, ambiguity/selection, candidate scoping), the dispatch guard, the movement-in-combat rule, `Character.show_timestamps`, the item-line composition helper and flag block, and the `complete` message pair plus connect-time verb list in the message reference. Do not remove any file.

## Closeout report

Commit hashes, full Part H results (including the unit-suite count), and confirmation all eight issues are closed.
