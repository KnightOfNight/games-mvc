# Shyland V21 Brief 1 — Output and Display Sweep

## Purpose

Implement all nine Bucket 1 (label `B1`) issues of Version 21: #55, #60, #81, #84, #85, #86, #90, #91, #92. All are output/display changes. **No model changes and no migrations** are in this brief. Server and client ship together; no backward compatibility with the old payload shapes is required.

This is Brief 1 of Version 21: it also creates the Version 21 architecture document (final, gated step).

## Pre-flight

- Verify `DOCKER_HOST` before any deployment-touching action.
- Working tree clean, on `main`.
- `gh` CLI authenticated.
- Read `CLAUDE.md` at the repo root.

Key files in this brief:

- `django/src/apps/shyland/consumers.py`
- `django/src/apps/shyland/item_utils.py`
- `django/src/apps/shyland/templates/shyland/game.html`

## Design rules that must not be deviated from

1. Colorization is client-side styling driven by server-supplied semantic structure. The server never sends hex colors for message text. (Zone/area theme colors riding payloads are the existing, allowed exception.)
2. The palette vocabulary ruled for v21: **key-color = `#7FB3D5`** (the existing structural-header blue from #39) and **value-color = `#E8E4D8`** (the existing room-content near-white). These become named CSS variables. No new hex values are introduced anywhere in this brief.
3. The trailing item status flag block keeps its existing colorization (rarity color on the rarity word, chrome on brackets/bind word) in every context, including the new value-colored report lines.
4. Where an example block in an issue and this brief's prose disagree, the example block (the table equivalent) is authoritative.

---

## Step 1 — Palette variables (foundation for #86, #90, #91, #92)

In `game.html`'s `:root` CSS block, add:

```css
--key-color: #7FB3D5;
--value-color: #E8E4D8;
```

Refactor the two existing rules that use these hexes to reference the variables (zero visual change):

- `.msg-section strong { color: #7FB3D5; }` → `color: var(--key-color);`
- `.room-content { color: #E8E4D8; }` → `color: var(--value-color);`

Do NOT change `--loc-room` (it shares the value-color hex by coincidence of ruling; it stays independently declared per #1's location-bar ruling).

Add two new message classes alongside the existing palette block:

```css
.msg-key   { color: var(--key-color); }
.msg-value { color: var(--value-color); }
```

## Step 2 — Structured key/value reports (mechanism for #90, #91, #92)

Extend the `report` output category with an optional structured form. A report message MAY carry a `lines` field instead of relying solely on `text`:

```python
{
  'type': 'output',
  'category': 'report',
  'lines': [
    {'k': 'Equipment:'},                          # key-only line
    {'v': '  [HEAD]  Leather Cap Mk 1  — ...'},   # value-only line
    {'k': 'Wallet:', 'v': ' 104 golds, 47 silvers'},  # key+value on one line
    {},                                            # blank line
  ],
  'ts': envelope_ts(),
}
```

Client handling in `game.html`:

- If a `report` message carries `lines`, render each entry as one output line: the `k` portion in a `.msg-key` span, the `v` portion in a `.msg-value` span, concatenated in that order. An entry with neither key renders as a blank line.
- Every `v` portion is rendered through the existing `appendFlaggedText()` so item flag blocks keep their rarity/chrome colorization inside value-colored lines (design rule 3).
- `report` messages carrying only `text` render exactly as today (help, who, examine, vendor list, travel listing, and the brief query are NOT converted in this brief).
- `report` remains in `UNSTAMPED_CATEGORIES` — no timestamp behavior changes.

## Step 3 — #55: drop the "is here" suffixes from room-render lists

In `consumers.py`, `send_room_description` composition:

- `who_lines`: `f'{npc_display(npc, capitalize=True, introduction=True)} is here.'` → drop the suffix and the period: each line is the introduced, capitalized noun phrase alone (e.g. `A cave centipede`).
- `what_lines`, fixture entries: same change.
- `what_lines`, corpse entries: `'... lies here.'` → the capitalized corpse display name alone (e.g. `The corpse of a giant cave spider`).
- Ground-item lines are already bare composed lines — unchanged.

No client change: the section headers ("Who's here?", "What's here?") and structure are untouched.

## Step 4 — #60: rename the "Droppable" flag to "Unbound"

All display surfaces, no data-model meaning change (`is_soulbound` semantics untouched):

1. `item_utils.py` line ~194: `bind = 'Bound' if item.is_soulbound else 'Droppable'` → `'Unbound'`.
2. Update the two docstring mentions in `item_utils.py` (lines ~191 and ~202) to say `Unbound`.
3. `game.html`: update `FLAG_RE` — `(Bound|Droppable)` → `(Bound|Unbound)`. **This regex must change in lockstep with the server rename or flag colorization silently breaks.**
4. `game.html`: update the CSS comment on `.flag-chrome` (mentions "Droppable") — cosmetic, keep comments truthful.
5. Repo-wide sweep: `grep -rn "Droppable" django/ docs/` — fix any remaining *display-surface* occurrence. Do NOT edit closed briefs, closeout reports, or issues reports in `docs/shyland/` — historical documents stay as written.

Note: issue #90's example block already shows `[Common, Unbound]` — Steps 4 and 9 must land consistently.

## Step 5 — #81: aggro-room entry renders the room like any other entry

Per the ruling recorded on #81. Two arrival paths in `consumers.py`:

**Path A — cardinal movement** (the aggro branch at ~line 475) and **Path B — flee-into-aggro** (~line 1741). In both, the current structure is: `if aggro_npcs: [snarls, start_combat, send_fight, send_status_refresh] else: [send_room_description]`, then `send_map()`.

New structure for the aggro branch, in this exact order:

1. `send_room_description(destination, entering=True, first_visit=first_visit)` — full render: pane clear, prose, exits, who's-here (which lists the attackers), zone separator. (Path B must fetch the fully-related room first, as its non-aggro branch already does via `get_current_room()`.)
2. Snarl lines — with `introduction=False` at both call sites: the who's-here section just introduced the NPC, so the snarl is a second mention and takes the definite article (`The cave centipede snarls and moves to attack!`).
3. `start_combat(...)`, `send_fight(session)`, `send_status_refresh()` — combat engagement and combat-red state land last (the ruled sequencing: `send_room_description` sends its own status payload; the combat-red refresh must be the final status the client receives).
4. `send_map()` stays after everything, unchanged.

## Step 6 — #84: player help fixes

Rewrite `cmd_help`'s text with these ruled changes (everything not listed stays):

1. **Movement line is static** — help documents the command set, not the current room: `Movement: north (n), south (s), east (e), west (w), up (u), down (d)`. Remove the per-room exit filtering.
2. **`say` line** becomes one line: `say <text>                 — speak to players here; NPCs may listen too` (delete the second explanatory line).
3. **Add the `brief` command line** (it exists — `cmd_brief`, `brief on | off` — but is missing from help): `brief on|off               — short room descriptions for rooms you have seen`. (#83 was closed into this issue; this line is its fix.)
4. **Item-selection section**: commands that take item arguments reference `<item selection>` instead of repeating grammar hints, and one section at the bottom explains the grammar once. Replace the current trailing `Item syntax:` block with:

```
Item selection:
  Commands marked <item selection> accept: a name or prefix ('axe', 'battle axe'),
  an index ('2.axe' — the second match), a quantity ('3 axes'), 'all' ('all axes'),
  and a rarity filter ('sell uncommon axe', 'sell all common').

Tab completes commands and item names.
```

   Update the affected command lines to use it, e.g. `pickup (p) <item selection>`, `drop <item selection>`, `equip (eq) <item selection>`, `unequip (uneq) <item selection>`, `use <item selection>`, `examine (ex) <item selection>`, `buy <item selection>`, `sell <item selection>`, `loot [corpse] [<item selection> | all]`, `repair [<item selection> | all]`.
5. **Blank line before the tab-completion note** (the layout above satisfies this).
6. **Standardize option spacing**: every bracketed alternative uses spaces around the pipe — `[item | all]`, `on|off` for two-state toggles stays tight only if standardized; RULING: use spaces everywhere: `brief on | off`, `timestamps on | off`, `[<item selection> | all]`. One style, no exceptions.
7. Keep the column alignment of the em-dash descriptions tidy after the edits (re-pad as needed).

Help output remains a plain-`text` report (not converted to key/value lines in this brief).

## Step 7 — #85: zone-colored pane borders

Per the rulings recorded on #85. In `game.html`:

1. All five pane borders become **5px solid**, colored with the current zone's theme color at ~0.75 opacity:
   - `#loc-bar` border-bottom (border 1)
   - the full-height vertical divider (border 2): the border-right of `#loc-bar`, `#output-wrap`, AND `#cmd-bar` (add border-right to `#cmd-bar` if absent) — all three segments identical so it reads as one line
   - `#cmd-bar` border-top (border 3)
   - `#side-stats` border-bottom (border 4)
   - `#map-wrap` border-top (border 5)
2. Mechanism: the client sets a CSS custom property when zone color arrives (the same `zone_color` the room separator already consumes from the room-render payload): `--zone-border: <hex>BF` (BF ≈ 0.75 alpha appended to the 6-digit hex in JS). Fallback before first render: `#CCCCCCBF`. All five border rules use `5px solid var(--zone-border)`.
3. **Border 4 combat precedence**: the existing `.in-combat` rule overriding `#side-stats` border-bottom-color to `--combat-accent` stays and wins during combat; zone color returns when combat ends. Verify the in-combat rule still renders correctly at 5px width.
4. Adjust paddings/sizes as needed so nothing overflows and the right pane keeps its fixed 300px content width (ruled invariant). The viewport-exact no-scrollbar behavior from v20 (#73) must survive the wider borders.
5. Responsive/mobile layout: apply the same 5px zone-colored treatment to whatever borders exist in that layout (e.g. `#map-wrap`'s full border) — implementation detail, same mechanism.
6. The room separator (`.room-sep`) is untouched. It will not touch the pane border to its right — acknowledged and fine.

## Step 8 — #86: area and room prose colorized to match the location bar

Per the issue body (it revises #1's D1 narrowing).

**Server** (`consumers.py`, `send_room_description`): the room-render payload stops concatenating prose. Replace the single `'text': f'{area_context}{description_text}'` field with:

```python
'area_text': room.area.area_description if (show_long and room.area and room.area.area_description) else None,
'area_color': room.area.theme_color if (room.area_id and room.area.theme_color) else None,
'room_text': description_text,
```

(Brief mode: `area_text` is None, `room_text` is the brief description — matching today's behavior where brief renders room prose only.)

**Client** (`renderRoom` in `game.html`):

- If `area_text` is present: render it as its own block, colored inline with `area_color` (fallback: value-color), followed by a blank line.
- Render `room_text` in **value-color** (`var(--value-color)`) — the location bar's room segment color, per the ruling.
- The old `.msg-room-render` fixed prose color (`#B8B4A6`) no longer applies to these two prose blocks. Leave the `.msg-room-render` class itself in place for the block container and any other consumers; only the prose coloring changes.
- Everything else in the render block (sections, headers, separator) is untouched.

## Step 9 — #90: `inv` output changes

Per the issue's example block (authoritative) and its recorded rulings. In `cmd_inventory`:

- Structure and content match the example: `Equipment:` section (slot-prefixed lines, unchanged composition), blank line, `Inventory (N/M items):` section, blank line, `Wallet:` section whose content line matches #92's wallet format.
- Convert the output to the Step 2 structured form: the three section headers are key-only lines; every other non-blank line is a value line.
- Rarity exception (ruled): value lines pass through `appendFlaggedText`, so flag blocks keep rarity colorization automatically — verify, don't reimplement.
- The example shows `[Common, Unbound]` — consistent with Step 4.

## Step 10 — #91: `stats` output changes

Per the issue's example block (authoritative) and its recorded rulings. In `_send_stats`:

- Drop the bracketed header line entirely (no-brackets pattern, consistent with #77).
- New first line, key-only: `Character Stats:`
- Second line, value: `  Player: {character.name} - Level {character.level} {character.origin.name} {character.archetype.name}` (ruled: Origin + Archetype, e.g. `Player: Shy-Guy - Level 10 Feral Blade`). Ensure `origin` and `archetype` are select_related where this renders (they are FKs on Character).
- Blank line, then the stats block exactly as today (stat lines, bars, XP, unspent points, and the conditional spend hint) — ALL as value lines, including stat labels like `Strength     (STR):`. A subkey-color was explicitly deferred; do not introduce one.
- `cmd_spend`'s no-args path reuses `_send_stats` and inherits this automatically — verify, no separate change.

## Step 11 — #92: `wallet` output changes

In `cmd_wallet`: convert to the structured form — one line, `{'k': 'Wallet:', 'v': f' {self.format_wallet(char)}'}`. Content unchanged.

---

## Verification

Run the stack locally and verify each numbered item. All must pass before any issue closes.

1. **Palette**: computed styles of a section header strong and a room-content line are unchanged from v20 (`#7FB3D5` / `#E8E4D8`); `--key-color`/`--value-color` resolve in devtools.
2. **#55**: enter a room with NPCs, a fixture, a corpse, and ground items: Who's-here and What's-here lines carry no "is here"/"lies here" suffixes; headers and item lines unchanged.
3. **#60**: an unbound item shows `[<Rarity>, Unbound]` in inventory, examine, loot, and room listings; the flag block still colorizes (rarity word colored, chrome gray); `grep -rn "Droppable" django/` returns nothing.
4. **#81**: walk into a seeded aggro room (e.g. cave spiders): output clears and renders prose → exits → Who's here? (attackers listed) → separator, THEN definite-article snarl lines, then the fight panel fills and stats go combat-red. Repeat via flee into an aggro room. Map updates in both. Location bar correct in both.
5. **#84**: `help` shows the static six-direction movement line, the one-line say entry, the `brief on | off` line, `<item selection>` on all item-taking commands, the Item selection section, a blank line before the tab note, and uniform `[x | y]` spacing throughout.
6. **#85**: all five borders render 5px in the current zone's color; crossing a zone boundary re-tints them (walk Z05 → Z01); entering combat flips border 4 to combat red and it reverts after; no window scrollbars at any size; right pane content width still 300px.
7. **#86**: in a room with an Area, the area paragraph renders in the Area's theme color, then a blank line, then the room paragraph in value-color; in an area-less room, only the room paragraph renders; brief mode shows brief prose in value-color with no area paragraph.
8. **#90**: `inv` matches the issue's example — key-colored headers, value-colored lines, rarity-colored flag blocks, Wallet section matching #92's format.
9. **#91**: `stats` matches the issue's example — `Character Stats:` in key-color, the Player line reading `Player: <name> - Level <N> <Origin> <Archetype>`, everything under the header in value-color; `spend` with no args shows the same.
10. **#92**: `wallet` renders `Wallet:` in key-color, contents in value-color.
11. **Regression sweep**: room renders, combat messages, rewards, errors, chat, echo, and the map all render with their v20 colors and behavior; timestamps still appear on events only.

## Issue closes

Gated on ALL verification steps passing: close #55, #60, #81, #84, #85, #86, #90, #91, #92, each with a one-line closing comment naming this brief.

## Architecture document (LAST, gated step)

This step is gated on all implementation and verification steps above being complete and passing.

Brief 1 of Version 21 creates the new versioned file:

- `git rm docs/shyland/Shyland_Architecture_v20.md`
- Create `docs/shyland/Shyland_Architecture_v21.md`, **written header-first, then one section at a time — never one giant operation**. Start from v20's content; the header records Version 21 and the commit hash of this brief's architectural changes.
- Sections to update, and what they should now say:
  - **Output palette / message categories**: add the key-color/value-color vocabulary (named CSS variables, hex values, which classes consume them); document the structured key/value `report` form (`lines` with `k`/`v`) and which commands use it (inv, stats, wallet); note flag-block colorization applies inside value lines.
  - **Item display**: flag block reads `Bound | Unbound` (renamed from Droppable in v21); composition otherwise unchanged.
  - **Room rendering**: who's-here / what's-here lines are bare noun phrases (no suffixes); the room-render payload carries `area_text` / `area_color` / `room_text` in place of the concatenated `text`; area prose renders in the area theme color, room prose in value-color; aggro-room arrival renders the full room first, then definite-article engagement lines, then combat state — in both movement and flee paths.
  - **Client layout**: the five pane borders are 5px, zone-theme-colored at ~0.75 alpha via `--zone-border`, sourced from the room-render `zone_color`; combat-red retains precedence on the stats/fight border; right-pane 300px content width and viewport-exact invariants preserved.
  - **Player help**: static movement list, `<item selection>` convention with a single grammar section, `brief` documented.

Subsequent Version 21 briefs update this file IN PLACE with no version bump.

## Closeout

Commit a closeout report as `docs/shyland/Shyland_V21_Brief_1_Closeout_Report.txt` covering: what was implemented per step, verification results per numbered item, issues closed, any deviations (there should be none), and **the final commit hash**.

Then: run the issues report.
