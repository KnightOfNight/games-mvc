# Shyland V20 — Playtest Checklists

One checklist per brief, run after that brief's Claude Code session closes and before the next brief begins. These are *your* passes — CC has already run its own verification; this is the human layer that catches what tests don't: feel, readability, and "does this actually look right."

Character notes: play as Shy-Guy; Marvin (pk 23) and Nivram (pk 24) remain available as test characters. Multiplayer checks use the partner account (Sharon-Love) in an incognito window.

Anything that fails, or feels wrong even if it technically passes, becomes an amendment (amendments don't count against the brief cap) or a new issue for a later version.

---

## After Brief 1 — Map System

**The map itself**
- [ ] Fresh character in the Heart: map shows one room, four unexplored stubs, nothing else. Fog-of-war is real — you see only where you've been.
- [ ] Walk the ring street a full lap. Does it *close*? The last room should connect back to the first with no visual weirdness, no overlap, no drift.
- [ ] Walk the four park paths from the Heart outward. Each should run straight from the Heart to the ring — no jogs, no kinks.
- [ ] Enter a new room: does the map recenter smoothly? Is the current-room highlight obvious at a glance?
- [ ] Walk to a room with an unvisited neighbor: unexplored stub renders where the exit is.
- [ ] Cross the Tree Arch into the Verdant Reach: does the map switch cleanly to a fresh fragment (Convergence rooms gone, not drawn alongside)?
- [ ] Enter a valley cave (Spinner's Hollow, the Silken Cleft): map switches to the cave's own fragment. Leave: surface fragment returns, still showing everything you'd visited.
- [ ] Descend a sinkhole (Whistling Sink, Drone Pit): same fragment switch on `down`.
- [ ] `travel` from the Heart to a Z01 checkpoint: map recenters far away, same fragment (this is correct — travel is fragment-neutral).
- [ ] Climb the ancient stair and the Viridian Ridge: map stays one continuous surface, no vertical stacking, no gaps. (The z-flattening working.)
- [ ] Up/down badges (U/D) appear on rooms that have vertical exits, and only those.
- [ ] Nine-by-nine window: when you're deep in a mapped area, rooms outside the window simply aren't drawn — no clipping artifacts, no half-rooms.

**The world changes**
- [ ] Visit the six new ring rooms. Read them. Do they feel like Infinity City, or like filler? (Names and prose are mine — this is your first read as a player.)
- [ ] Find both street carts. Buy a Healing Draught from each. Talk to VND-9 and Mother Tansy — try the greeting/wares/farewell keywords.
- [ ] Fordwatch (Fernwater Vale): both descriptions say "shard," not "sphere."
- [ ] Walk the Ridge past Stonestep and Highfold. The villages sit where the map says they sit. Bear's Hollow is north of Highfold now.
- [ ] Ask NPCs for directions anywhere the geography changed (the ring, Wisteria Walk, Basalt Way, the Ridge villages). Do their compass references still hold? (Geography audit rule — CC checked, you're confirming.)

**Regression**
- [ ] Combat, looting, vendors, repairs, travel, obelisks all behave exactly as before. Nothing about the world *plays* differently.

---

## After Brief 2 — Output Envelope

- [ ] Timestamps appear on every output line, dim, `[HH:MM:SS.ss]` with two decimals, in your local time.
- [ ] They're unobtrusive — you can read the game text without the timestamps fighting it. (If they're too loud, that's a styling amendment.)
- [ ] Long combat: lines land in a sensible order. Nothing arrives visibly out of sequence.
- [ ] Chaos test: stand in a room with another character (Sharon-Love), both fighting, both moving, both talking. Order stays coherent for each of you.
- [ ] Reload the page mid-session: reconnection is clean, timestamps resume, no stale-order weirdness.
- [ ] Screen reader pass (or browser reader mode): the output reads as clean sentences — no timestamps announced.

---

## After Brief 3 — Commands

**The resolver — the big one**
- [ ] `sell axe` with both a Common and an Uncommon Battle Axe carried: sells the *Common* one (protective default).
- [ ] `equip axe` in the same state: equips the *Uncommon* (best-first).
- [ ] `sell uncommon axe`: sells the Uncommon explicitly.
- [ ] `equip battle axe mk 1` — the full name as printed on screen — works. So does `equip axe 1`, `equip b axe`.
- [ ] `sell mace` while the Iron Mace is equipped: refuses, tells you to unequip.
- [ ] `use draught`, `use draughts`, `use h d`, `use healing`: all work.
- [ ] `use d h`: does *not* work (order matters). `sell rap`: does not match carapace.
- [ ] `sell all hides` at a vendor: sells all three, one total line.
- [ ] `sell 5 hides` with three: refuses with a count, sells nothing.
- [ ] `buy 10 draughts` at a ring cart: funds and capacity checked up front, all-or-nothing.
- [ ] `sell all common` at a vendor: flushes every unequipped Common item; equipped gear untouched; zero-value items summarized.
- [ ] `sell all` with no qualifier: refused with usage.
- [ ] `2.axe`: picks the second one. Stable across repeats.
- [ ] Two definitions matching one word (e.g. two draught types at a vendor): disambiguation list, no guess.
- [ ] `loot all` on a boss corpse: takes everything, lists it.
- [ ] `attack spider` with two spider *types* in the room: disambiguation list. `attack cave`: works.

**Display**
- [ ] Item lines read `Iron Mace Mk 1 — 100% durability [Uncommon, Droppable]`. No leading rarity anywhere. Equipment, inventory, examine, loot lists, ground items — all the same shape.
- [ ] What's on screen is what you can type. Pick any item line and type its name verbatim into a command — it resolves.

**Tab completion**
- [ ] `use h` + Tab: completes to a carried consumable. Tab again: cycles.
- [ ] `buy ` + Tab at a cart: offers vendor stock, not your inventory.
- [ ] `attack ` + Tab: offers NPCs in the room.
- [ ] Tab at verb position: cycles commands.
- [ ] Tab with no candidates: nothing breaks.

**The rest**
- [ ] Try to walk out of a fight with `north`: refused, in-fiction, you don't move. `flee` still works.
- [ ] `timestamps off`: prefixes vanish. Reload: still off. Log in from another browser: still off. `timestamps on`: back. Bare `timestamps`: usage line.
- [ ] Old crash: `loot all` with no corpse, garbage arguments, weird input — connection *never* drops. (If you can find any input that kills the websocket, that's a bug worth an amendment.)

---

## After Brief 4 — UI Layout

- [ ] The three left regions and the right pane sit where the design says. Location bar is one line; output is unified (no separate description pane); send button is inside the command bar.
- [ ] Widen the browser: right pane stays 300px, left regions grow. Narrow it back: nothing breaks.
- [ ] Location bar: `Zone: Area: Room`, colored per the theme palette. Rooms with no Area show `Zone: Room`.
- [ ] The zone/area colors — do you *like* them? (Authored by me; first look.) Especially: the Convergence violet, the Verdant Reach green, the Ridge teal, the cave colors against the background.
- [ ] Long room name in a long area: Area truncates first, Zone never.
- [ ] Enter combat: the whole stats section turns red. Win, flee, and die — it clears every time.
- [ ] Fight info panel: enemy rows with health bars, tracking damage per tick. Fight a group (a boss with minions) — all enemies listed. Change attack focus: the marker moves.
- [ ] Panel clears completely when combat ends.
- [ ] Connection indicator (right end of command bar): green with a live latency number. Stop the server: red pulsing. Restart: recovers to green.
- [ ] Phone width: location bar, stats, output, command bar — typing and reading are comfortable. Map is below, reachable by scroll.
- [ ] The map still renders exactly as it did after Brief 1 (regression).

---

## After Brief 5 — Output & Messaging

**Read a fight. Just read it.**
- [ ] Can you tell at a glance who's hitting whom, without reading the words? (Outgoing red vs incoming orange-red.)
- [ ] Criticals stand out. Misses recede. Kills and XP read as reward.
- [ ] Nothing is too dark against the background. Nothing is garish.
- [ ] The combat red in the text and the combat red in the stats panel look like the same red.

**Structure**
- [ ] `look` output matches the design: exits, blank, who's here, blank, what's here. Empty sections just aren't there.
- [ ] All three section headers share one color; it's distinct from room content.
- [ ] Every command you type echoes as `> command` above its result. Invalid commands too — "You don't see that here." now has context.
- [ ] Sharon-Love does *not* see your command echoes.

**NPC grammar — the Silk Matron test**
- [ ] Fight the Silk Matron and her brood start to finish. Read every line: aggro, hits, crits, misses, kills, corpses, the fight panel. Zero doubled articles ("the the"), zero missing ones ("A the").
- [ ] Talk to proper-noun NPCs (Morra, Aldric, Mother Tansy, VND-9): never "the Morra."
- [ ] Room occupant lines read naturally.

**Corpses**
- [ ] Kill something mid-fight with other enemies still up: no decay spam interrupts the fight.
- [ ] Have Sharon-Love stand in the room *not* fighting: she sees the decay line.
- [ ] Kill a normal-tier NPC and loot it: "carried nothing worth taking" — it should not feel like you missed loot.
- [ ] Loot a boss corpse twice: the second try says you already took everything.

**Rarity colors**
- [ ] The flag block scale (Common gray → Artifact red) is legible and pleasing. Common recedes without disappearing.

**Whole-version regression**
- [ ] Play for twenty minutes like a player, not a tester. Does anything feel worse than v19? That's the real test.
