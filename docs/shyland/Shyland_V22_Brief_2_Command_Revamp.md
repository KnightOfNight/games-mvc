Shyland V22 Brief 2 — Command Revamp (B2)
Version: 22 · Bucket: B2 · Brief: 2 of 4 Issues (all close at closeout, gated on verification): #111 (parent), #29, #54, #58, #59, #61, #65, #67, #75, #96, #98, #121, #122 Normative specification: `docs/shyland/Shyland_V22_B2_Command_Spec_DD.md` (committed at 40656a0; present in the working tree). The DD is authoritative for every behavior in this brief. This brief adds sequencing, file paths, migrations, authored help text, tests, and verification — it restates the DD only where emphasis prevents error. Where this brief and the DD disagree, the DD wins; stop and flag. Branch: the v22 worktree branch. Never merge; merging is the operator's action.
Out of scope, explicitly: the B3 commands (home, cancel, last, sudo) and DD §12 admin gating; the B5 issues (#100/#109/#110); the firehose itself (#33/#37 — the DD §4 doctrine governs future tagging; build nothing for it now); travel redesign beyond the destination-listing order.
Pre-flight

1. Verify `DOCKER_HOST` before any deployment-touching action.
2. v22 worktree branch, clean tree.

Step 0 — Self-commit this brief
Save verbatim to `docs/shyland/Shyland_V22_Brief_2_Command_Revamp.md` (skip if identical exists), commit, push immediately. Commit and push at every step boundary. Never merge.
Step 1 — Migration (model changes first)
File: `django/src/apps/shyland/models.py`. One migration:

1. `Character.echo_mode` — `BooleanField(default=True)` (DD §10: echo on by default; pane-only preference, suppresses the player's own command-echo line).
2. `Character.brief_mode` — change the field default to False (DD §10: brief off by default). Do not alter existing rows; existing players keep their current setting.

Run `makemigrations` + `migrate`.
Step 2 — Palette and client classes
File: `django/src/apps/shyland/templates/shyland/game.html`.

1. Add `--warn-color: #E8D44D;` and `--say-color: #f0c060;` (say-color is the named form of `--chat`; migrate map/say usage to the new name, keep `--chat` as an alias only if other call sites still read it) and `--loot-color: #4caf7d;` (named form of the reward green).
2. `.msg-error` → `color: var(--error);` — the hard-coded `#C08A3E` amber dies (#121).
3. New `.msg-warn { color: var(--warn-color); }`.
4. Combat family (DD §2): add `.msg-combat-crit-in { color: #F08A50; font-weight: bold; }` (ships dormant if NPC crits don't occur mechanically — wire the class and the category plumbing regardless); change `.msg-combat-miss` to `color: var(--muted);` and delete `#8A887F` from the file entirely.
5. `.msg-reward` reads `var(--loot-color)`.

Step 3 — Three-layer re-tag (#121, DD §3)
Server: audit every output call site in `django/src/apps/shyland/consumers.py` and the tick engine that currently emits category `error` (or ad-hoc `system` for failures) and re-tag each as:

* `error` — CLI only: unknown command, bad syntax, footnote 10/13/15 prompts, settings usage lines.
* `warn` (new category, plumbed through the envelope choke point like any other): resolution failures (pool miss: "no X here answers to that name" family) and mechanical failures (state-gate refusals, can't afford, repair didn't hold, heal at full, sell-all block, bound-drop attempt, unequip without bag room, failed flee).

The closeout must state the count of call sites re-tagged into each layer.
Step 4 — Parser conformance to the chart (DD §1)
Files: `django/src/apps/shyland/consumers.py`, `django/src/apps/shyland/command_grammar.py`.
Bring every existing command's argument handling to its chart cell exactly. The deltas from current behavior (non-exhaustive — the chart is the checklist; the closeout lists any further deltas found):

* Footnote 10 standard prompts everywhere a target is required: `What do you want to <verb>?` (error). "Attack what?", "Say what?" and kin die.
* Footnote 13/15 bare-numeric errors: `<verb> <N> what?`; spend's variant `spend <N> points on which stat?`
* spend argument order flips to `spend <quantity> <stat>` (footnotes 7 14; "all" legal = all unspent points). Old order dies.
* use accepts `[<quantity>] <item>` numeric-only (#65) — the "can't use everything at once" refusal dies.
* buy and drop reject "all" (footnote 11). drop excludes bound items from its pool (footnote 16, warn on attempt via resolution/mechanical layering per DD).
* sell: `all` alone legal; bare `sell all` blocked (footnote 17, warn, wording that teaches: name what to sell).
* loot: `all | <NPC>` only — no numeric quantity.
* repair: `all | <item>`.
* attack: `<NPC>|<player>`, target required — targetless attack under aggro is removed (fossil; aggro NPCs self-engage since v21 #17).
* flee, quit, movement, information commands: footnote 2 — all arguments ignored (today some error; conform).
* N.noun ordinal input survives across all noun arguments; game output never speaks ordinals beyond the v21 duplicate-only display rule.
* settings (brief, timestamps, + new echo): exactly six accepted words, case-insensitive (on/off/yes/no/true/false); bare = current-setting sentence; set = "now" sentence; invalid = error `Usage: <cmd> [on|off]`. Sentences verbatim from DD §10. Implement `cmd_echo`; the client suppresses the player's own echo line when off (pane-only; nothing else changes).
* Every command echo line is an event: timestamped per the standing envelope rules (#59's buy/sell gap conforms here).

Step 5 — State-gating matrix (DD §5)
Implement the matrix for existing commands: combat refuses commerce (buy/sell/repair), inventory manipulation (drop/pickup/loot — #29), gear (equip/unequip), travel, movement; combat allows attack, flee, use, spend, examine, say, quit, all information, all settings. Dying allows use (self-rescue), say, quit, information, settings; refuses the rest. All refusals warn-color with in-voice wording. Quit is allowed in combat and combat continues after quit — verify no code path ends a CombatSession on disconnect; the player can die logged out (already true via CombatSession-as-DB-state; add a test proving it).
Step 6 — Resolution pools (DD §8) and the name invariant (#122)
Conform every pool per DD §8. The two changes from current behavior to call out: examine's pool becomes the union (inventory + equipped + floor + vendor stock + NPCs + players — fixes vendor-examine); drop excludes bound. Nearest-wins tiebreak (self before room before vendor) where segments overlap.
Name invariant (#122), both edges: (1) the character-creation validation (the v16 creator form) rejects any name matching an `NpcDefinition.name`, case-insensitive, alongside the existing uniqueness/profanity checks, with a plain refusal message; (2) `seed_world` `_verify` gains the permanent check `no NPC definition name collides with any existing character name`.
Tab completion (#67, #96): the completer offers exactly each command's pool at each position, literals included ("all", the six booleans, stat names, running-command names), and ordinal forms when duplicates exist.
Step 7 — Partial fulfillment (DD §7) and sequences

* Shortfalls do the possible part with the warm report (sell's line verbatim from DD §6); any pickup at capacity fails outright (warn); partial `pickup all` takes oldest-on-floor first — use the best existing signal for floor-arrival order (an updated/moved timestamp); if genuinely none serves, use pk order and document the proxy in the closeout; add a field only as last resort (with migration).
* `use N` heal sequences stop at full with the loot-color line "You have been restored to full health."; any heal attempted at full fails (warn) — #61 generalized.
* `repair all` loops until all repaired / funds exhausted / 5 attempts (#75); each mend line prints as it lands.

Step 8 — Success sentences and say (DD §6, §13)
Implement the ten transactional sentences verbatim from DD §6, colors as ruled (pickup and heal-to-full loot-color; buy plain; equip swap-aware; cancel is B3 — skip). Reuse the NPC article machinery for item articles. Rarity words rarity-colored wherever item names render.
Say: the `[say] `prefix dies at both sites — the player path (`consumers.py` cmd_say) and the NPC dialogue-response path (`run_tick_engine.py`, the v20 §7.6 responder) — output becomes `Name: message` in say-color for players and NPCs alike; bare say gets the footnote-10 prompt; the speaker keeps receiving their own broadcast (double vision is intentional; echo-off is the remedy).
Combat (#54): ratified as shipped — deltas are Step 2's crit-in class, the miss recolor, and the `[Critical]` bracket prefix removal (both tick-engine sites: the unarmed player-crit path and the NPC-crit-on-player path). The doctrine: color carries the category, words carry the fiction. On the authored-flavor paths, the word moves into prose — the damage clause becomes `for a critical {N} damage!` (e.g. "…wings roaring for a critical 28 damage!"). The weapon path's existing prose ("You land a critical hit on…") already conforms and stands. The NPC-crit path emits category `combat-crit-in` (the new class). No other combat prose changes.
Step 9 — Information output standards (DD §9)
Implement all of DD §9 for the seven existing information commands (last is B3): the three kinds; header punctuation law (colon = value on the line; ellipsis = structure below); headers uniformly key-color, `Inventory (12/250)...`; muted column headers; the Equipment paper-doll (all 14 slot rows always, re-authored anatomical `SLOT_ORDER` — Head, Neck, Shoulders, Back, Chest, Main hand, Off hand, Ranged, Hands, Ring, Ring, Waist, Legs, Feet — sentence-case labels, muted "-" empties); the Inventory table (Quantity column, flat alpha); Details = `90%, Uncommon, Bound` with durability colored by the mechanical band, derived never owned; list's table + Price with free-group-first and muted `free`; the shared wallet-line renderer used by both `wallet` and inv's Wallet section; who's one-liner (#98); stats' blank line before Unspent; look untouched.
Step 10 — Help regeneration (DD §11)
Rebuild help: four type sections (key-color `...` headers), Kind-3 tables (Command / Usage / Description, muted headers), usage strings compiled from the chart (BASH notation: `<>` required, `[]` optional, `|` alternatives), the four bottom sections (Arguments, Quantities, Settings, Tab completion) with content per the DD's token/quantity/settings/completion rules. B3 commands and echo: include echo (it ships in this brief); exclude home/cancel/last/sudo (B3 adds them, with gating). Authored descriptions, verbatim:
attack: Engage a target in combat. · buy: Buy from a vendor in the room. · drop: Drop an item on the ground. · equip: Equip an item from your inventory. · examine: Take a close look at something. · flee: Escape from combat. · loot: Loot a corpse, or every corpse here. · pickup: Pick up items from the ground. · quit: Leave the game. · repair: Have a repairer fix your gear. · say: Speak to everyone in the room. · sell: Sell to a vendor in the room. · spend: Spend unspent stat points. · travel: Travel the obelisk network. · unequip: Unequip an item you are wearing. · use: Use a consumable item. · help: Show this help. · inventory: Show your equipment, inventory, and wallet. · list: List what a vendor here has for sale. · look: Look at the room again. · stats: Show your character sheet. · wallet: Show your money. · who: Show who is online. · north/south/east/west: Walk that direction. · up: Climb or ascend. · down: Descend. · brief: Short room descriptions. Default: off. · echo: Show your own commands in the output. Default: on. · timestamps: Show timestamps on events. Default: on.
Step 11 — Travel listing (interim)
Destination listing sorts ascending by straight-line map-space distance from the player (within-zone; cross-zone moot with one destination zone), each entry labeled shard or sphere. Nothing else about travel changes.
Step 12 — Tests
Extend/create under `django/src/apps/shyland/tests/` (suite runs as `python manage.py test apps.shyland.tests -t /app` per #117; do not fix #117). Required coverage, minimum:

1. Chart conformance: for every command, a bare-invocation case and (where applicable) footnote 10/13/15/17 prompt/error cases with correct category (error vs warn).
2. spend order flip; old order errors. use-with-quantity works (#65).
3. sell-all blocked; sell-all-with-noun works; buy/drop reject "all"; drop refuses bound (warn) and excludes it from resolution.
4. State matrix: loot/buy/sell/equip refused in combat (warn) (#29); use/spend/examine/attack/flee allowed; dying allows use and quit, refuses pickup; quit mid-combat leaves the CombatSession live.
5. Pools: examine resolves a vendor-stock item and an NPC (#96 by extension); use cannot resolve vendor stock; nearest-wins where inventory and vendor share a name.
6. Name invariant: creation rejects an NPC-colliding name case-insensitively; seed-verify check present and passing.
7. Partial fulfillment: sell shortfall sells-and-reports; pickup at capacity fails outright; heal sequence stops at full with the loot-color line; heal at full refused (warn) (#61); repair-all 5-attempt cap (#75).
8. Settings: six words accepted any case, seventh word → usage error; bare reports; sentences exact; echo_mode persists; brief default False for a new character.
9. Say: no prefix on player OR NPC speech, say-color category, bare prompt.
10. Crits: no `[Critical]` bracket anywhere; unarmed player crit and NPC crit lines carry "for a critical N damage!"; NPC crit emits `combat-crit-in`.
11. Completion: equip completes inventory (#67); settings complete the six words; "all" offered where legal.

Full suite green; report counts.
Step 13 — Operator playtest checklist
State in the closeout, ready after deploy: bare-prompt tour (attack/say/loot/sell 3); spend flip; sell-all block wording; drop-bound refusal; examine a vendor item and an NPC; combat refusals (loot mid-fight); use 3 draughts stopping at full; repair-all loop; the new inv paper-doll with empties; list's free group; who; help end to end; brief/echo/timestamps sentences and defaults; say's clean line; amber gone — errors red, world-declines yellow.
Step 14 — Architecture doc (gated last)
Gated on all implementation and verification above passing. Update `docs/shyland/Shyland_Architecture_v22.md` in place (no new file; header hash moves — architectural changes): §4.14 (command layer) rewritten to the chart/parser/pool/matrix reality with the DD cited as design source; §4.15/§4.16 (output/display) updated for the three kinds, palette additions, three-layer categories, help generation, settings; note the echo/brief model fields and migration.
Closeout
`docs/shyland/Shyland_V22_Brief_2_Command_Revamp_Closeout_Report.txt`: what shipped per step, the Step 3 re-tag counts, any conformance deltas found beyond Step 4's list, test totals, playtest-pending note, deviations, final commit hash. Close #111, #29, #54, #58, #59, #61, #65, #67, #75, #96, #98, #121, #122 — gated on verification. Commit and push. Do not remove or prune any documents.
Finally: run the issues report.
