# Shyland V20 Brief 5 — Output & Messaging

Implements GitHub issues **#13** (combat message colors), **#14** (look-command output sections), **#39** (section-header label color), **#15** (command echo), **#24** (NPC article grammar), **#28** (corpse decay and empty-loot messaging). Self-contained; do not consult chat history. Applies fifth and last, after Briefs 1–4 (it depends on the envelope's message pipeline, the layout brief's unified output pane and combat-red family, and the commands brief's item-line composition helper). **Never remove or prune any transient document** — the operator prunes.

---

## Part A — The output palette (authoritative)

All output colorization is **client-side styling driven by server-supplied semantic categories** — the server never sends hex colors for message text (the sole exception is the zone/area theme colors already delivered with location updates by the UI Layout brief, which come from model fields). Extend the message `category` vocabulary as needed and give each category a CSS class; define the palette in one CSS block.

| Role | Color | Notes |
|---|---|---|
| Structural section headers | `#7FB3D5` | **General rule (settles #39): every structural section-header label, present and future, uses this one color** — `Exits:`, `Who's here?`, `What's here?`, and any label added later. Not room content. |
| Room content (names, occupants, items) | `#E8E4D8` | near-white, not `#FFFFFF` |
| Room/area prose descriptions | `#B8B4A6` | slightly dimmer than content |
| Zone / Area names | model `theme_color` | from `Zone.theme_color` / `Area.theme_color`; identical values in the location bar and in output — one source of truth |
| Player's outgoing hit | `#C4453F` | |
| Player's outgoing critical | `#E24B4A`, bold | brighter member of the ruled combat-red family |
| Incoming hit (NPC hits the player) | `#E0724A` | orange-red — deliberately distinct from outgoing so attack direction is readable at a glance |
| Miss (either direction) | `#8A887F` | gray |
| Kill / XP / reward | `#D8B45A` | gold |
| Success (sales, repairs, pickups) | `#8FCF9F` | green |
| Error category | `#C08A3E` | amber |
| System / ambient (decay, connection) | `#8A887F` | gray |
| Command echo | `#8A887F` | gray, prefixed `> ` |
| Timestamp prefix | `#6E6C64` | dimmest; already `aria-hidden` per the envelope brief |
| Colons / brackets / chrome punctuation | `#8A887F` | |

**Combat-red family coordination (ruled):** the layout brief's stats-panel combat state (`#E24B4A` accent, `#3A1212` tint) and the combat text colors above are one family. Do not introduce a second red.

**Rarity scale — flag block only** (the item-line flag block introduced by the Commands brief): Common `#9C9A90`, Uncommon `#5FA8D3`, Rare `#B387E8`, Epic `#D8B45A`, Legendary `#E0724A`, Artifact `#E24B4A`. Common is still shown but visually recedes. Brackets, commas, and `Bound`/`Droppable` render `#9C9A90`. This colorizes the existing plain-text flag block; the composition itself does not change.

**Explicitly NOT in this brief:** directional arrows on combat lines (`→`/`←`) — proposed and struck during the design pass; deferred/abandoned pending a separate ruling. Do not implement arrows.

## Part B — Look-command output sections (#14, #39)

`look` (and room entry) render in this exact order:

```
[ Area Name — Room Name ]
<room description prose>

Exits: north, south

Who's here?
Maro the Mender is here.
Essa the Trader is here.

What's here?
a Verdant Shard is here.
```

- Blank line between sections; header labels take the structural-header color.
- **Absorb "On the ground:"** — the interim ground-items section introduced by Brief 3's composition work is replaced by this structure: `What's here?` becomes THE items section (composed item lines per Brief 3's helper, flag blocks and all). After this brief, exactly one items section exists in the room render; do not keep both.
- **Sections with no content are omitted entirely** — no "Who's here? (nobody)" line, no empty header.
- Exits list stays comma-separated on one line after its label. Occupant and item lines are one per line, room-content color.
- Brief mode (`brief on`) is unchanged in its existing behavior; `look` always shows the long description regardless (standing rule).

## Part C — Command echo (#15)

Every command the player submits is echoed into the output pane **before** its result, as `> <the command as typed>`, in the echo color. Echo lines are a **displayed-prefix category**: they carry and display the standard timestamp prefix exactly as output-category lines do (this extends the envelope brief's "output-only" display rule to echo), and the `timestamps on|off` preference governs them identically. It is a transcript of the player, not game output: it is not re-broadcast to anyone else, and it must never be confused with a system message. Echo happens for every command including unrecognized ones (so "You don't see that here." always has its context immediately above it).

## Part D — NPC article grammar (#24; migration required)

### D1. Model

On `NpcDefinition`:

- `name` — becomes **article-free** ("Silk Matron", "cave spider", "Matron's brood"). Authoring law, enforced in the extended seed verify: **no NpcDefinition name begins with an article** (`a`, `an`, `the`).
- `article = models.CharField(max_length=8, default='the')` — the definite article used in composed references; **blank for proper nouns** (named NPCs like Morra, Aldric, Mother Tansy, VND-9).
- `plural_phrase = models.CharField(max_length=64, blank=True)` — for names that are inherently phrases about a group ("one of the Matron's brood"); when set, it is used verbatim as the composed reference instead of `article + name`.

### D2. Display helper

One helper (in the NPC/display utils module) composes every player-visible NPC reference: `npc_display(npc, capitalize=False)` → `plural_phrase` if set, else `f"{article} {name}"` if article, else `name`. `capitalize=True` capitalizes only the first character for sentence-initial use.

**Every message template that names an NPC must call it** — combat hit/miss/crit/kill lines, aggro engagement lines, room occupant lines, corpse lines, dialogue attributions, targeting messages, `look`, and the fight-info feed from the layout brief. Templates must NOT prepend their own articles anywhere. Grep the codebase for `the {` / `A {` / `An {` patterns and eliminate all of them.

### D3. Data pass

Rewrite every seeded NPC name to be article-free and set `article` / `plural_phrase` appropriately (proper nouns get blank articles; the brood-style names get `plural_phrase`). This touches all seeded NPCs across Z05 and Z01. Reseed enforce-exact.

**Rider (one value, missed by the Brief 4 palette table):** seed `Area.theme_color` for **Spinner's Hollow** = `#C8CBB8` (pale web-green, kin to but distinct from the Silken Cleft's `#D8D4C8`), replacing its `#CCCCCC` default, and add it to the seed-verification color assertions alongside the others.

### D4. Acceptance strings

The three lines from the issue must render exactly as:

- `You land a critical hit on one of the Matron's brood for 64 damage.`
- `You hit the Silk Matron for 22 damage.`
- `The Silk Matron snarls and moves to attack!`

## Part E — Corpse and loot messaging (#28)

- **Decay suppression:** a corpse-decay message is **not sent to any player who is currently in an active combat session** — dropped, not queued or deferred (a corpse crumbling mid-fight is noise, not information). Players in the room who are not in combat still see it, in the system/ambient gray. Corpse decay timing and loot mechanics themselves are unchanged.
- **Empty-corpse response:** looting a corpse that never had loot (normal-tier NPCs, which by design drop nothing) responds `The <npc> carried nothing worth taking.` (composed via the Part D helper). The old "is already empty" / "There is nothing to loot here." wording is removed for this case — it implied missed treasure. A corpse the player already emptied themselves keeps a distinct, accurate line: `You've already taken everything from the <npc>.`

## Part F — Verification (all must pass before the architecture doc step)

1. Palette: every category in Part A renders its ruled color; no second red anywhere; the stats-panel combat state and combat text visibly belong to one family; zone/area colors in output match the location bar exactly.
2. Structural headers: `Exits:`, `Who's here?`, `What's here?` all share the header color; no other content uses it.
3. Look output matches Part B exactly, including omission of empty sections; verify in a room with NPCs and items, a room with neither, and a room with only one of the two. The interim "On the ground:" section no longer exists anywhere — `What's here?` is the sole items section, rendering composed item lines.
4. Echo: every command appears as `> ...` before its result, including invalid commands; not visible to other players; timestamped.
5. NPC grammar: the three Part D4 strings render exactly; a full combat against the Silk Matron and her brood produces no doubled or missing articles anywhere (combat lines, aggro lines, corpse lines, room lines, fight-info panel); proper-noun NPCs (Morra, Mother Tansy, VND-9) never gain an article; seed verify enforces the no-leading-article law.
6. Decay: killing an NPC mid-fight produces no decay line for the fighting player; a non-fighting observer in the room sees it; decay timing unchanged.
7. Empty corpse: a normal-tier kill answers with the "carried nothing worth taking" line; an already-looted boss corpse answers with the distinct already-taken line.
8. Rarity flag block renders its color scale; item-line composition otherwise unchanged from the Commands brief.
9. Screen reader pass: the live region reads all output text cleanly; color conveys no information not also present in words (attack direction is stated in the text itself — "You hit…" / "The X hits you…").
10. No gameplay changes: damage, XP, loot, decay timers, and command behavior are all identical to pre-brief.

Close **#13, #14, #39, #15, #24, #28** with closing comments referencing this brief, gated on all checks above.

## Part G — Architecture doc update (LAST — gated on all implementation and verification above passing)

Update `docs/shyland/Shyland_Architecture_v20.md` in place, no version bump: the client output-styling section (the full category→color palette, the structural-header rule, the rarity scale, command echo), the look-output structure, the `NpcDefinition` article/plural_phrase fields and display helper (plus the seed-verify authoring law), and the decay-suppression and empty-corpse messaging rules. Do not remove any file.

## Closeout report

Commit hashes, all Part F results, the count of NPC names rewritten in the Part D3 data pass, and confirmation that all six issues are closed.
