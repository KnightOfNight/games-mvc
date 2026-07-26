# Shyland V23 Brief 5 — Voice Content & Coverage (B4 data half)
**Version:** 23 (ODD — fix/refinement)
**Bucket:** B4 — NPC Voice
**Issues:** #40 (closes — the data half; Brief 4 shipped the code half), #144 (closes — six silent NPCs), plus one issue filed by this brief at Step 1 and closed by it.
**Branch:** `version_23` (existing — do not create a new one)
**Model/effort:** Opus, high effort. This brief is mostly authored content; precision on the data structures and the render rule matters more than speed.
---
## 0. Pre-flight
Verify and report each of these before touching anything. Any failure = stop and report.
1. `DOCKER_HOST` is set and the daemon is reachable (standing Shyland rule).
2. On branch `version_23`, working tree clean, synced with origin.
3. `django/src/apps/shyland/version.py` reads `SHYLAND_VERSION = "23.0-DEV"`. **This brief does not touch it** — Brief 2 set it; the closeout ritual bumps it to `23.0`.
4. **Pending deploy-time actions from prior V23 briefs:** report status. Expected at Brief 4's close: **none outstanding** (B2's `purge_orphaned_items` confirmed executed, 87/87/0 then 0/0/0; B1, B3, B4 left none). If anything is outstanding, report it and stop.
5. Test suite baseline: `python manage.py test apps.shyland -t /app` — expected **333 OK** at Brief 4's close. Record the actual number.
6. `python manage.py makemigrations --check` reports **no changes**. This brief introduces **no model changes and no migration**; if `--check` ever reports changes during this brief, stop.
---
## Step 0 — Brief self-commit (first action, before any other work)
Save this brief's full text verbatim to `docs/shyland/Shyland_V23_Brief_5_Voice_Content_And_Coverage.md` (skip the write if a byte-identical file already exists), commit on `version_23`, and **push immediately**. That push is the operator's work-has-started signal.
Commit and push at every step boundary thereafter. **Branch only — never merge to main on your own initiative.**
---
## 1. Filing step — one new issue (HARD GATE)
A defect was found in design review while authoring this brief's content. File it before implementing, so the tracker never lags the chat.
```
gh issue create \
  --title "First-contact greetings render as speech — the NPC's name is printed twice" \
  --milestone "Version 23" \
  --label bug --label B4 --label triaged \
  --assignee "@me" \
  --body "<body below>"
```
**Body:**
> Found in design review for V23 Brief 5 (2026-07-25), while authoring greetings for the six NPCs of #144.
>
> `deliver_dialogue_response` (`run_tick_engine.py`) renders **every** pending dialogue row the same way: `f'{npc_name}: {response_text}'`, category `say`. Greeting and departure entries ride the same machinery as keyword entries, but their authored text is **third-person narration**, not speech. The greeting path therefore prints the name twice:
>
> `Aldric: Aldric looks you over once, unhurried, and nods as if confirming a private guess.`
> `Info Prime: Info Prime's lenses rotate toward you with a soft click. "NEW ENTITY LOGGED. WELCOME."`
>
> Eight of the ten seeded greetings are narration and render doubled; two (VND-9, Mother Tansy) are authored as bare speech and render correctly by accident. Departure reactions are already broadcast unprefixed at category `room` by a separate call and are unaffected.
>
> A second symptom on the same path: multi-NPC greetings draw a **connective** ("… also looks up and answers.") at positions 1+, which announces an answer to a question nobody asked. Connectives belong to the say-response path only.
>
> Greetings fire once per character per NPC forever, so this has been largely invisible in play — existing characters already hold their `DialogueGreetingRecord`s for the Convergence roster.
>
> **Ruled fix (design chat, 2026-07-25):** speech is prefixed and say-colored; narration is not. Keyword responses keep `Name: text` at category `say`. Greeting and departed entries broadcast their text **verbatim, unprefixed, at category `room`** — exactly as departures already do — and take **no connective**. The two speech-form greetings (VND-9, Mother Tansy) are re-authored into narration form as part of the same fix. This is the same governing line as Brief 4's ruling: **speech gets pooled and prefixed; renderings and narration do not.**
>
> Ships in V23 Brief 5 alongside #40's data half and #144.
**HARD GATE.** After creation, verify with `gh issue view <N>` that the issue exists with milestone `Version 23`, labels `bug`, `B4`, `triaged`, and the assignee resolved to `KnightOfNight`. **Any deviation in creation or verification = stop, run the issues report, write a closeout explaining, make zero code changes.**
Capture the issue number at runtime. Everywhere below that says `#GREET`, substitute the real number. **No placeholders survive into committed code, comments, or documents.**
---
## 2. The seed data lift — dialogue content moves to module level
All paths are under `django/src/apps/shyland/`.
Today the dialogue content lives inline inside `Command._seed_dialogue()` in `management/commands/seed_world.py` — roughly 440 lines of authored text embedded in method calls, unreachable by any test that does not run the whole seed. This brief roughly triples that content, so it is lifted out first.
**2.1 — Move `DIALOGUE_CONNECTIVES` from a class attribute to a module-level constant**, keeping its current shape exactly (dict keyed by `DialogueConnective.POSITION_SECOND` / `POSITION_LATER`, values are lists of `{name}` templates). Update its one reader, `_seed_dialogue_connectives`, to read the module-level name.
**2.2 — Add a module-level `NPC_DIALOGUE` mapping**, placed immediately after `DIALOGUE_CONNECTIVES`:
```python
# v23 brief 5 (#40 data half, #144): every authored NPC voice, lifted out of
# the seeding method so the content is testable without a database. Ordered
# by seeding order: the Convergence roster, then the two ring carts, then the
# Verdant Reach checkpoint services. Slug -> list of entry specs.
#
# THE POOL FLOOR: every keyword and departed entry carries at least three
# responses. Greetings carry exactly one — a greeting fires once per character
# per NPC, forever, so variety in that pool is invisible by construction.
#
# The (npc, entry_type, note) triple is the seed's lookup key: two entries of
# the same type on the same NPC must never share a note.
NPC_DIALOGUE = {
    'aldric': [ ... ],
    ...
}
```
Each entry spec keeps the existing four-key shape exactly: `entry_type`, `note`, `keywords`, `responses`.
**2.3 — `_seed_dialogue` becomes a loop:**
```python
def _seed_dialogue(self):
    self._seed_dialogue_connectives()
    for npc_slug, entry_specs in NPC_DIALOGUE.items():
        self._seed_npc_dialogue(npc_slug, entry_specs)
    self.stdout.write(
        f'  Dialogue seeded: connectives + {len(NPC_DIALOGUE)} NPC voices.'
    )
```
`_seed_npc_dialogue` and `_seed_dialogue_connectives` are otherwise **unchanged**.
**2.4 — Move the `_seed_dialogue()` call in `handle()` (load-bearing).** It currently sits at the Convergence stage, **before** `_seed_verdant_npcs()` and `_seed_ridge_npcs()`. `_seed_npc_dialogue` does `NpcDefinition.objects.get(slug=...)`, so seeding dialogue for Maro, Essa, Tavik, Sona, Old Brammel, and Ridda from that position raises `DoesNotExist` on a **fresh database** — the definitions do not exist yet. (An already-seeded database would hide this completely. It is a fresh-install trap, not a theoretical one.)
Move the single line `self._seed_dialogue()` from its current position (between `_seed_primordial_sphere()` and `_seed_travel_nodes()`) to **immediately after `self._seed_ridge_vendors()`**, i.e. the last seeding call before `self._sweep_all()`. Nothing between the two positions reads dialogue; dialogue reads only `NpcDefinition`.
Leave a comment at the call site:
```python
        # v23 brief 5: dialogue seeds LAST — _seed_npc_dialogue resolves NPC
        # definitions by slug, and the Verdant/Ridge service NPCs are not
        # defined until their zone stages have run. Fresh-database ordering.
        self._seed_dialogue()
```
---
## 3. The render rule — greetings and departures are narration (#GREET)
**3.1 — `npc_voice.py` gains the composer.** Add to the module (it is now the home of every voice-composition rule):
```python
# v23 brief 5 (#GREET): the render rule. Keyword responses are SPEECH — they
# take the 'Name: ' attribution and the say color, matching player speech.
# Greeting and departure entries are NARRATION — authored in the third person,
# they broadcast verbatim at category 'room', unprefixed and unconnectived.
# Mirrors DialogueEntry.ENTRY_KEYWORD; the lockstep is guarded by test.
SPEECH_ENTRY_TYPES = ('keyword',)
def dialogue_line(entry_type, npc_name, text):
    """Compose one delivered dialogue line. Returns (text, category)."""
    if entry_type in SPEECH_ENTRY_TYPES:
        return (f'{npc_name}: {text}', 'say')
    return (text, 'room')
```
**3.2 — `run_tick_engine.py`, `deliver_dialogue_response`.** Two changes, nothing else in the method moves:
- **Gate the connective block** on the row being a speech entry: the `position == 1` / `position >= 2` connective draws run only when `row.entry.entry_type in npc_voice.SPEECH_ENTRY_TYPES`. (`entry` is already `select_related` on the due-rows query — no new query.)
- **Compose the broadcast through the helper** instead of the inline f-string:
```python
        line, category = npc_voice.dialogue_line(
            row.entry.entry_type, npc_name, response_text,
        )
        await self.broadcast_to_room(row.room_id, line, category=category)
```
The departure-reaction broadcast in the `is_final` block already sends unprefixed text at category `room`; route it through `dialogue_line(DialogueEntry.ENTRY_DEPARTED, npc_name, departure_line)` as well so there is exactly one place that decides this, and its output is byte-identical to today's.
`npc_display(..., capitalize=True)` still composes `npc_name`, and is still computed for every row — narration lines do not use it, but the connective gate and the departure path do.
**3.3 — The two speech-form greetings are re-authored into narration form** (VND-9 and Mother Tansy) — see the content in §4.
---
## 4. The content
Everything in this section is final authored text. Reproduce it **exactly** — punctuation, casing, and curly-quote-free apostrophes as written. Where a line contains a double quote, use the surrounding-quote style already used in `seed_world.py` (single-quoted Python strings containing `"`, or double-quoted strings containing `'`), and never change the text to suit the quoting.
**Structural rules that must hold across every NPC below:**
- keyword entry → `keywords` is a non-empty list of lowercase single-word tokens; `note` is the entry's unique-per-NPC key
- greeting entry → `note: ''`, `keywords: []`, **exactly one** response
- departed entry → `note: ''`, `keywords: []`, **three** responses
- every keyword entry → **at least three** responses
### 4.1 The six silent NPCs (#144)
These six have never had a single dialogue row. Each gets three keyword entries, a greeting, and a departure pool.
#### `maro-the-mender` — Maro the Mender (Fordwatch)
**keyword, note `repair`, keywords `['repair', 'mend', 'fix', 'broken', 'bench']`**
1. `Set it on the bench and I'll have a look. Most things are less broken than their owners think.`
2. `I can mend it. Whether it stays mended depends on what you do to it next, which is your business.`
3. `Reedmere taught me to fix nets. A net or a boot buckle is the same argument with the same thread.`
**keyword, note `shard`, keywords `['shard', 'light', 'green', 'travel', 'lamp']`**
1. `It came for the crossing and stayed, same as I did. Stand near it long enough and it will take you elsewhere. Don't ask me how.`
2. `I talk to it sometimes. It never answers. That's most of the appeal.`
3. `People step out of that light three or four times a day. I've stopped looking up.`
**keyword, note `help`, keywords `['help', 'lost', 'new', 'where', 'directions']`**
1. `Lost? The arch back to the Convergence is south, the way you came. Reedmere is north up the valley, then west at the approach. Everything else out here is weather and animals.`
2. `Help is cheap and I have plenty. Keep your boots dry, keep your gear whole, and don't argue with anything that has more legs than you.`
3. `Ask Essa if you need goods. Ask me if you need something held together. Ask the fog nothing; it has never once answered.`
**greeting** (1)
1. `Maro looks up from his bench, takes in your boots first and the rest of you second, and nods.`
**departed** (3)
1. `Maro turns back to his bench without any sign of surprise.`
2. `Maro shakes his head slowly. "Always in a hurry, that lot," he tells the shard.`
3. `Maro sets down his awl, considers the empty space where you were standing, and picks it up again.`
#### `essa-the-trader` — Essa the Trader (Fordwatch)
**keyword, note `wares`, keywords `['wares', 'buy', 'sell', 'browse', 'stock', 'trade', 'goods']`**
1. `Draughts, a knife, boots, gloves. It isn't much of a blanket, but everything on it has kept someone alive.`
2. `Buy before you climb, not after. The stair sells nothing, and neither do the bears.`
3. `I'll take what you've outgrown, too, at a fair price. Fair, mind. Not generous.`
**keyword, note `help`, keywords `['help', 'lost', 'new', 'advice', 'welcome']`**
1. `New, then. Boots first, love. Everything else in the Reach can wait; your feet can't.`
2. `The path south takes you back to the arch and the city. North it opens out — green and lovely and full of teeth.`
3. `Maro will mend what you break. I'll sell you what you didn't know to bring. Between the two of us you'll manage.`
**keyword, note `danger`, keywords `['danger', 'dangerous', 'safe', 'beast', 'bear', 'lion', 'spider', 'careful']`**
1. `Bears fish the shallows well north of here, and they don't share. The lions keep to the cliffs and consider the path theirs.`
2. `There's silk in the gully east of the bramble cut. Whatever spins it is not small. Please don't go and look.`
3. `Nothing crosses into this clearing. The shard sees to it, or the crossing does. Past the ford you're on your own.`
**greeting** (1)
1. `Essa glances up from her blanket, prices you kindly at a glance, and smiles as though you passed.`
**departed** (3)
1. `Essa smooths the corner of her blanket and lets you go without comment.`
2. `Essa calls after the empty air: "Boots! At least look at the boots!"`
3. `Essa shares a look with Maro. Neither of them says anything; both of them mean it.`
#### `tavik-the-mender` — Tavik the Mender (Stairhead)
**keyword, note `repair`, keywords `['repair', 'mend', 'fix', 'broken', 'stitch']`**
1. `Hand it here. Needle, awl, patience — in that order, and I have all three.`
2. `The wind takes the stitching out of everything up here. That isn't your fault. It is my living.`
3. `I can save it. I can't make it new. Nobody makes anything new; we only argue with the wearing-out.`
**keyword, note `shard`, keywords `['shard', 'light', 'green', 'travel', 'wind']`**
1. `It rides the wind — climbs, drops, climbs again. Somebody built the network it belongs to. Nobody built that.`
2. `Stand near it and you can go where you have already been. Efficient. Unsettling. Free.`
3. `Windhome sends its children up to watch it. Half of them stay for the travelers instead.`
**keyword, note `help`, keywords `['help', 'lost', 'new', 'where', 'directions']`**
1. `The stair drops away south behind you, back to the vale. Windhome is north, then west off the grass. Everything between is grass and the things that live in grass.`
2. `Sona sells, I mend, the wind does the rest whether you asked it to or not.`
3. `Keep something to drink on you. The flats look kind. The flats are simply large.`
**greeting** (1)
1. `Tavik glances up from his hide, needle still moving, and tips his chin at you.`
**departed** (3)
1. `Tavik doesn't look up. The needle keeps its rhythm.`
2. `Tavik snorts. "The wind takes them too," he says, to nobody in particular.`
3. `Tavik marks his place in the stitching, looks at the empty ground, and carries on.`
#### `sona-the-trader` — Sona the Trader (Stairhead)
**keyword, note `wares`, keywords `['wares', 'buy', 'sell', 'browse', 'stock', 'trade', 'goods', 'bow']`**
1. `A bow, a vest, leggings, and draughts. Weighted down, all of it, or the wind would carry my whole living north.`
2. `The bow is the honest purchase. Everything on these flats sees you coming from a long way off.`
3. `I buy as well as sell. Bring me what the caves gave you — I'm curious what the caves are handing out these days.`
**keyword, note `help`, keywords `['help', 'lost', 'new', 'advice', 'language', 'languages']`**
1. `You came up the stair, so you've done the hard part twice — once climbing it and once deciding to. Windhome is north and west if you want a roof.`
2. `People arrive beside that shard speaking languages I have never heard. I've learned three. I'm working on a fourth. Say something strange and I'll write it down.`
3. `One of you called their armor "kevlar" once. I still don't know what that is. I put it in the book anyway.`
**keyword, note `danger`, keywords `['danger', 'dangerous', 'safe', 'beast', 'buffalo', 'grass', 'careful']`**
1. `The buffalo will let you walk right up to them. That is not an invitation, and they are not slow.`
2. `Nothing out there hunts you. Several things will object to you. It comes to the same bruises.`
3. `This clearing is safe. I don't know why, and I've stopped asking — the light hangs here and nothing comes.`
**greeting** (1)
1. `Sona looks up, takes in your gear with frank professional interest, and beckons you closer out of the wind.`
**departed** (3)
1. `Sona weights the corner of her goods down again and lets the moment pass.`
2. `Sona shrugs. "They always come back for the bow," she says.`
3. `Sona watches the empty ground for a breath, then writes something small in her book.`
#### `old-brammel` — Old Brammel the Mender (Cragfoot)
**keyword, note `repair`, keywords `['repair', 'mend', 'fix', 'broken', 'bench']`**
1. `Sit, sit. Put it on the bench. Everything that comes down this mountain comes down broken, the people included.`
2. `I mended for Lastlight forty years before I came down here. Stone, leather, iron, pride — I've had a go at all of them.`
3. `It will hold. It won't hold forever. Come back and see me; that's rather the arrangement.`
**keyword, note `shard`, keywords `['shard', 'light', 'lamp', 'green', 'travel', 'fire']`**
1. `The little lamp? Best company on the mountain. It warms itself at my fire, which it does not need, which is exactly why I like it.`
2. `Stand close and it will send you off to the Heart, or back down to the crossings. It has never once asked me for anything in return.`
3. `It arrived the same year I did. I have decided that means something. Nobody has argued with me yet.`
**keyword, note `help`, keywords `['help', 'lost', 'new', 'where', 'directions', 'mountain']`**
1. `Lost? Then you're at the right fire. The flats are south behind you. The switchbacks start north and don't stop, and Lastlight sits east off the path once you're high enough.`
2. `Take the climb in pieces. The mountain is in no hurry, and neither should you be.`
3. `Ridda has the iron, I have the bench, the fire is free. The mountain has everything else and it doesn't sell.`
**greeting** (1)
1. `Old Brammel looks up from the fire, delighted, as though you were a rumor he had been hoping to confirm.`
**departed** (3)
1. `Old Brammel chuckles. "Off they go," he tells the fire. "Off they always go."`
2. `Old Brammel settles back against the stone and lets the quiet come back.`
3. `Old Brammel looks at the little lamp. "Just you and me again," he says, entirely content.`
#### `ridda-the-trader` — Ridda the Trader (Cragfoot)
**keyword, note `wares`, keywords `['wares', 'buy', 'sell', 'browse', 'stock', 'trade', 'goods', 'iron']`**
1. `Mace, sword, shield, cap, and something to drink. Everything a person wishes they had bought before the first switchback.`
2. `The shield is the one you'll thank me for. Nobody has ever come back down and thanked me for the cap. They should.`
3. `I'll buy what you haul out of the deep places, too. Fair weight, fair price, and no questions I'd rather not have answered.`
**keyword, note `help`, keywords `['help', 'lost', 'new', 'advice', 'climb']`**
1. `Buy low, climb high. That's the whole of my advice and it cost me nothing to give.`
2. `Brammel mends, I sell, the fire is free, and the light does as it likes. That's Cragfoot.`
3. `You want warnings? Those are free as well. Ask me about the mountain.`
**keyword, note `danger`, keywords `['danger', 'dangerous', 'safe', 'beast', 'bear', 'lion', 'mountain', 'careful']`**
1. `Brown bears hold the lower slopes and mountain lions hold everything above them. Neither of them negotiates.`
2. `There are ways into the mountain up there — the crag, the chittering hole, the crown. Things live in all three, and they were doing perfectly well before we arrived.`
3. `If a hunter off the Ridge tells you a ground is forbidden, it is forbidden. They lost people learning that so you wouldn't have to.`
**greeting** (1)
1. `Ridda looks you over once — gear, boots, the set of your shoulders — and decides you're worth talking to.`
**departed** (3)
1. `Ridda pulls the oilcloth straight over her goods and thinks nothing of it.`
2. `Ridda snorts. "Come back when the mountain has explained it," she says.`
3. `Ridda glances at Brammel. Brammel is already talking to the light.`
### 4.2 Top-ups to the existing roster (#40 data half)
Every existing response stays exactly as it is. **Add** the lines below to the named entries; keep the existing lines first, in their current order, and append the new ones.
#### `aldric`
- **keyword `obelisk`** — add:
  1. `It doesn't do anything. That is the considered opinion of everyone who has stood near it for less than a minute.`
- **departed** — add:
  1. `Aldric watches the empty doorway a moment. "And they say I don't listen," he says.`
  2. `Aldric goes back to whatever he was thinking about before you interrupted it.`
#### `info-prime`
- **keyword `help`** — add:
  1. `QUERY FORMAT ACCEPTED: SPEAK A SUBJECT ALOUD. THIS UNIT HEARS EVERYTHING SAID IN THIS DISTRICT AND ANSWERS ONLY WHAT IS ASKED. A COURTESY.`
- **keyword `network`** — add:
  1. `NODE STATUS: THE HEART IS ALWAYS AVAILABLE. OTHER NODES REQUIRE PRIOR VISITATION. THE NETWORK WILL NOT DELIVER YOU SOMEWHERE YOU HAVE NEVER BEEN. POLICY, NOT LIMITATION.`
  2. `CORRECTION FREQUENTLY REQUIRED: THE STONES ARE NOT DOORS. THE STONES ARE ADDRESSES. THE DISTINCTION MATTERS TO THE STONES.`
- **departed** — add:
  1. `Info Prime's lenses hold on the empty air. "SESSION TERMINATED BY CLIENT. NO FAULT ASSIGNED."`
  2. `Info Prime files something with a soft click. "INCOMPLETE QUERIES: ONE. RUNNING TOTAL: SUBSTANTIAL."`
#### `morra`
- **keyword `help`** — add:
  1. `You want the truth? Mend your own gear when you can, pay me when you can't, and don't stand between me and the fire.`
- **departed** — add:
  1. `Morra doesn't stop hammering. She wasn't going to anyway.`
  2. `Morra glances at the empty doorway. "Come back when it breaks," she says, certain that it will.`
#### `pella`
- **keyword `bag`** — add:
  1. `Hands full already, look at you. Take the satchel before you drop something precious in the road.`
- **departed** — add:
  1. `Pella waves at the doorway anyway, in case you turn around.`
  2. `Pella sighs happily. "They're always in such a rush at that age," she says, of an age she has not specified.`
#### `ferwick`
- **keyword `bag`** — add:
  1. `One satchel, no charge, and no I will not itemize it. Pella has already won that argument on your behalf.`
- **departed** — add:
  1. `Ferwick makes a small note in the ledger. "Browsed," he writes. "Bought nothing."`
  2. `Ferwick straightens the table by an inch that did not need straightening.`
#### `repairbot-prime`
- **keyword `help`** — add:
  1. `FUNCTIONAL SUMMARY: THIS UNIT RESTORES DURABILITY. THIS UNIT DOES NOT RESTORE JUDGMENT. PRESENT ITEMS, NOT DECISIONS.`
  2. `ADVISORY: EQUIPMENT DEGRADES CONTINUOUSLY AND SILENTLY. YOU WILL NOTICE AT THE WORST AVAILABLE MOMENT. THIS UNIT SUGGESTS EARLIER.`
- **departed** — add:
  1. `Repairbot Prime powers down its work lamp. "QUEUE EMPTY. RESUMING STANDBY."`
  2. `Repairbot Prime records something. "CLIENT PATTERN: RETURNS WHEN BROKEN. CONSISTENT WITH ALL CLIENTS."`
#### `seris`
- **keyword `help`** — add:
  1. `We can tell you what a thing is. Where it is, you will have to walk.`
- **departed** — **new entry** (`note: ''`, `keywords: []`), three responses:
  1. `Seris turns back toward the stone, the question already forgotten or already answered.`
  2. `Seris dims by a shade, the way a held breath is let go.`
  3. `The light within Seris settles, patient as a lamp left burning for someone.`
#### `veris`
- **keyword `help`** — add:
  1. `Ask us at the end. We are better at endings.`
- **departed** — **new entry**, three responses:
  1. `Veris regards the empty air with something that is almost, but not quite, disappointment.`
  2. `Veris turns a slow degree back toward the obelisk and resumes attending.`
  3. `Veris says, "Later, then," to no one at all, and means it.`
#### `vnd-9`
- **keyword `wares`** — add:
  1. `STOCK LEVELS: SUFFICIENT. STOCK VARIETY: RESTORATIVES. STOCK OPINION: YOU LOOK LIKE YOU NEED ONE.`
  2. `RECOMMENDED PURCHASE: THE DRAUGHT. ALTERNATIVE RECOMMENDATION: THE DRAUGHT. THIS UNIT STOCKS ONE PRODUCT AND ENORMOUS CONVICTION.`
- **keyword `thanks`** — add:
  1. `GRATITUDE LOGGED. GRATITUDE UNNECESSARY. GRATITUDE APPRECIATED REGARDLESS.`
  2. `CUSTOMER DEPARTING IN GOOD CONDITION. THIS UNIT RECORDS THAT AS A SALE WELL MADE.`
- **greeting** — **REPLACE** the existing single response (`WELCOME, TRAVELER. HYDRATION IS SURVIVAL. SURVIVAL IS CUSTOMER RETENTION.`) with the narration form required by #GREET:
  1. `VND-9's front panel flickers awake as you approach. "WELCOME, TRAVELER. HYDRATION IS SURVIVAL. SURVIVAL IS CUSTOMER RETENTION."`
- **departed** — **new entry**, three responses:
  1. `VND-9's panel dims by one increment. "CUSTOMER LOST. CAUSE: LEGS."`
  2. `VND-9 hums to itself. "STANDING BY. STANDING IS THE ENTIRETY OF THE JOB."`
  3. `VND-9 cycles its display through the full stock list for nobody at all.`
#### `mother-tansy`
- **keyword `wares`** — add:
  1. `Draughts, love, and nothing else worth carrying. I don't hold with clutter.`
  2. `Two coppers' worth of foresight beats a whole purse of regret. Take one before you walk out through the green gate.`
- **keyword `thanks`** — add:
  1. `Go on, then. Mind the road and mind yourself.`
  2. `Thank me by coming back needing less. It would be a first.`
- **greeting** — **REPLACE** the existing single response (`Come closer, love — everyone limps past this corner eventually.`) with the narration form required by #GREET:
  1. `Mother Tansy beckons you over without getting up. "Come closer, love — everyone limps past this corner eventually."`
- **departed** — **new entry**, three responses:
  1. `Mother Tansy tuts fondly at the empty street.`
  2. `Mother Tansy shakes her head. "They never take enough," she says to her cart.`
  3. `Mother Tansy goes back to her stock, unbothered. They all come back this way eventually.`
### 4.3 Connectives
Keep the six existing templates exactly as they are and append three to each class.
**`POSITION_SECOND`** — add:
1. `{name} looks over and takes up the thread.`
2. `{name} answers before the words have quite settled.`
3. `{name} has something to add, and adds it.`
**`POSITION_LATER`** — add:
1. `{name} puts in a word, unhurried.`
2. `Not to be outdone, {name} speaks up.`
3. `{name} rounds it off from across the way.`
### 4.4 Geography audit (standing rule — record this in the closeout)
Every directional claim in the new content was checked against the seeded room graph before authoring. Confirm each against `seed_world.py` and report the result:
| Claim | Speaker | Check |
|---|---|---|
| The arch back to the Convergence is **south** of Fordwatch | Maro, Essa | `vr-v01` (0,0) … `vr-v07` (0,5), straight y-run |
| Reedmere is **north up the valley, then west** | Maro | `vr-v11` (0,9) → `vr-rm1` (-1,9) |
| Bears at the shallows, **well north** of Fordwatch | Essa | `vr-v21` (-1,12) vs `vr-v07` (0,5) |
| Lions on the cliffs (the cliff path, north) | Essa | `vr-v10` (0,8), `vr-v18` (1,8) |
| Silk in the gully **east of the bramble cut** | Essa | `vr-v13` (0,11) → east → `vr-v20` (1,11) |
| The stair drops **south** from Stairhead | Tavik | `vr-s5` → north → `vr-f01` (0,20) |
| Windhome is **north, then west** | Tavik, Sona | `vr-f05` (0,24) → `vr-w1` (-1,24) |
| The flats are **south behind** Cragfoot | Old Brammel | `vr-f18` (0,30) → north → `vr-c01` (0,31) |
| The switchbacks start **north** of Cragfoot | Old Brammel, Ridda | `vr-m01` (0,32) |
| Lastlight sits **east off the path** high up | Old Brammel | `vr-m31` (0,52) → `vr-ll1` (1,52) |
| The three delve mouths are up the mountain | Ridda | `vr-m13`, `vr-m25`, `vr-m40` east mouths |
| Fordwatch / Stairhead / Cragfoot are safe rooms | Essa, Sona | all three seeded `safe=True` |
| The green gate is out through the ring, not a compass claim | Mother Tansy | deliberately direction-free |
---
## 5. Seed invariants
Add a `_verify_dialogue` block to the seed's verification stage (with the other `_check` calls; place it after the Verdant checks). Each is a `self._check(...)`:
1. **Roster closure.** `set(NPC_DIALOGUE) == set of slugs with at least one DialogueEntry in the database` — no NPC has dialogue that the authored map does not declare, and every declared NPC resolved.
2. **Silent by ruling stay silent.** `the-primordial-sphere`, `the-verdant-sphere`, `the-verdant-obelisk`, `verdant-shard` have **zero** `DialogueEntry` rows. (Mystery is preserved by ruling — the spheres, the obelisks, and the shard do not speak.)
3. **The pool floor.** Every `DialogueEntry` of type `keyword` or `departed` has **≥ 3** `DialogueResponse` rows.
4. **Greeting shape.** Every roster NPC has exactly one `greeting` entry, and it has exactly one response.
5. **Voice completeness.** Every roster NPC has ≥ 2 `keyword` entries, exactly one `greeting`, and exactly one `departed`.
6. **Connective pools.** Each `position_class` has ≥ 6 `DialogueConnective` rows.
7. **The six are covered (#144).** `maro-the-mender`, `essa-the-trader`, `tavik-the-mender`, `sona-the-trader`, `old-brammel`, `ridda-the-trader` each have ≥ 3 keyword entries, a greeting, and a departed entry.
Report each with a readable message in the existing `_check` style, including counts where a count makes the failure diagnosable.
---
## 6. Tests
New file `tests/test_npc_dialogue_data.py`. Use `SimpleTestCase` — every assertion below reads the authored constants or module source, so **no database and no seed run is required**. Import the data from `apps.shyland.management.commands.seed_world`.
Docstring: `v23 brief 5 (#40 data half, #144, #GREET): the authored dialogue corpus and the speech-vs-narration render rule.`
1. **Pool floor** — for every NPC, every `keyword` and `departed` entry has ≥ 3 responses. Failure message names the offending NPC and note.
2. **Greeting shape** — every NPC has exactly one greeting entry with exactly one response, `note == ''`, `keywords == []`.
3. **Departure shape** — every NPC has exactly one departed entry, `note == ''`, `keywords == []`, exactly 3 responses.
4. **Keyword entry shape** — every NPC has ≥ 2 keyword entries; each has a non-empty `note` and ≥ 1 keyword.
5. **Note uniqueness** — within one NPC, no two entries share `(entry_type, note)`. (This is the seed's reconcile key; a collision would silently merge two pools.)
6. **Keyword token legality** — every keyword token is lowercase, non-empty, and survives the real tokenizer: `_tokenize_said_words(token) == {token}` (import it from `apps.shyland.consumers`). A multi-word or punctuated token can never match anything a player says.
7. **No duplicate responses** — within one entry, response texts are unique. Across the whole corpus, report (do not fail on) any text appearing under two NPCs.
8. **#144 coverage** — the six slugs are present with ≥ 3 keyword entries each.
9. **Silent roster** — the four silent slugs are absent from `NPC_DIALOGUE`.
10. **Connectives** — ≥ 6 templates per position class, all unique, every one containing `{name}`.
11. **Render rule** — `npc_voice.dialogue_line`: keyword → `('Name: text', 'say')`; greeting and departed → `('text', 'room')`.
12. **Render-rule lockstep** — `npc_voice.SPEECH_ENTRY_TYPES == (DialogueEntry.ENTRY_KEYWORD,)`, so the string literal in `npc_voice` can never drift from the model.
13. **Connective gating** — read `inspect.getsource(TickEngine.deliver_dialogue_response)` (or the enclosing class as named in the file) and assert that `SPEECH_ENTRY_TYPES` appears in it, and that no bare `f'{npc_name}: '` composition remains. A source-level guard is acceptable here; the behavioral truth is covered by test 11.
14. **Seed call ordering** — read `inspect.getsource(Command.handle)` and assert the index of `_seed_dialogue()` is **greater** than the index of `_seed_ridge_npcs()`. This is the fresh-database trap from §2.4; it must not silently regress.
Do not modify existing tests unless one of them pins a string this brief changed; if any does, report it in the closeout as a deviation with the original intent preserved as an explicit assertion (the hygiene pattern established in Brief 4).
---
## 7. Verification
Run and record verbatim output for each.
7.1 `python manage.py makemigrations --check` → **no changes detected** (this brief adds no model changes).
7.2 `grep -rn "SPEECH_ENTRY_TYPES\|dialogue_line" apps/shyland/ --include=*.py | grep -v tests/` → hits in `npc_voice.py` (definition) and `management/commands/run_tick_engine.py` (use) only.
7.3 `grep -n "npc_name}: " apps/shyland/management/commands/run_tick_engine.py` → **no output**. The inline speech composition is gone.
7.4 `grep -c "'responses'" apps/shyland/management/commands/seed_world.py` → record the count; it is the authored entry count and belongs in the closeout.
7.5 `python manage.py seed_world` on a database that already holds the pre-brief content → the reconciliation report shows **created** `DialogueEntry`/`DialogueResponse`/`DialogueConnective` rows, **zero deletions**, and every `_check` in §5 passing. Record the created counts per model.
7.6 `python manage.py seed_world` a **second** time → `No differences — database matches coded configuration exactly.` (Idempotence; the enforce-exact sweep leaves the new rows alone.)
7.7 Full suite: `python manage.py test apps.shyland -t /app` → all green. Record the total; it should be the pre-flight baseline plus the new tests.
7.8 Fresh-database ordering proof (the §2.4 trap). Either run `make reset` in the dev environment, or run `seed_world` against an empty database created for the purpose, and confirm it completes without `NpcDefinition.DoesNotExist`. If neither is available in-session, say so plainly in the closeout and record test 14 as the standing guard — do not claim a run that did not happen.
---
## 8. Architecture doc — LAST STEP, GATED
**This step is gated on every implementation and verification step above being complete and passing.**
`docs/shyland/Shyland_Architecture_v23.md` already exists (Brief 2 created it; Briefs 1, 3, and 4 updated it in place). **Update it in place — do not create a new file, do not bump the version stamp.** Move the header's commit hash to this brief's final implementation commit.
Sections to change:
- **Header block** — prepend this brief's summary to the "as of commit …" narrative in the established style, and extend the "Version 23.0 — IN PROGRESS" line with: Brief 5 (B4 Voice Content & Coverage: #40 data half — the authored corpus tripled onto a three-response pool floor; #144 — six silent service NPCs given voices; #GREET — the speech-vs-narration render rule) applied fifth.
- **§4.8 Seed data** — the dialogue content is now the module-level `NPC_DIALOGUE` map (slug → entry specs) and `DIALOGUE_CONNECTIVES`, with `_seed_dialogue` a loop over the map; the seeding call **moved to the end of `handle()`** because dialogue resolves NPC definitions by slug and the Verdant/Ridge services are defined in later stages; the seven new dialogue `_check` invariants (roster closure, silent-by-ruling, pool floor, greeting shape, voice completeness, connective pools, #144 coverage); the corpus shape (16 voices, pool floor of 3 on keyword and departed entries, greetings exactly one because they fire once per character forever).
- **The NPC-dialogue delivery section** (the `say` hook / greetings section under §4, and the tick-engine dialogue delivery text) — the render rule: keyword responses are speech (`Name: text`, category `say`); greeting and departed entries are narration (verbatim, unprefixed, category `room`) and take no connective; both compose through `npc_voice.dialogue_line`.
- **§4.17 NPC voice pools** — `npc_voice.py` gains `SPEECH_ENTRY_TYPES` and `dialogue_line`, making it the single home of the speech-vs-narration decision.
Write header-first, then one section at a time — never one giant operation.
---
## 9. Issue closes — gated
Gated on §7 passing. Close with a comment recording what shipped and the final implementation commit hash:
- **#144** — the six service NPCs have voices; keyword/greeting/departure counts stated.
- **#40** — closed by this brief, the data half, completing the bucket Brief 4 opened. The comment must state: the pool floor of three across every keyword and departed entry; the thin entries topped up (Info Prime `network`, Repairbot Prime `help`, VND-9 and Mother Tansy `wares`/`thanks`); departure pools grown, and departures added for the four NPCs that had none; connectives grown to six per class; `death_message` remained **cut from scope** by the 2026-07-24 ruling; report-category renderings remained **out of the sweep**.
- **#GREET** — the render rule shipped; the two speech-form greetings re-authored as narration.
---
## 10. Deploy — operator-authorized, in-session
Deploy invocation, exactly: **`make build && make migrate`** (never `make prod`, never `make deploy`; `DOCKER_HOST` verified in pre-flight).
**Deploy-time data action — this brief has one, and it is the whole point of the brief:** the content lives in the seed, so `make seed` must run against production or none of it exists in the world. Immediately after the deploy, run:
```
make seed
```
Record in the closeout: the reconciliation report's created/updated/deleted counts for `DialogueEntry`, `DialogueResponse`, and `DialogueConnective`, and the pass/fail line of each §5 `_check`. **Deletions of dialogue rows are not expected — if any appear, report them prominently.**
If the deploy is not authorized in-session, list `make seed` in a dedicated **PENDING DEPLOY-TIME ACTIONS** block in the closeout, and every subsequent brief or amendment in Version 23 pre-flights it until it is confirmed done.
Post-deploy sanity: `SHYLAND_VERSION` still reads `23.0-DEV`, the tick engine is running, `/shyland/` returns 200.
---
## 11. Ready after deploy — operator playtest checklist
1. **The six speak.** Walk to Fordwatch, Stairhead, and Cragfoot. On entry each mender and trader should greet you — narration, **no `Name:` prefix, no doubled name**, and **no connective line** between the two greeters.
2. `say help` at each checkpoint — both NPCs in the room should answer, staggered, with a connective before the second speaker.
3. `say repair` at a mender, `say wares` at a trader, `say shard` at a mender, `say danger` at a trader — each should answer in that NPC's voice.
4. **Variety.** Ask the same keyword four or five times in a row at one NPC: no line should repeat back-to-back.
5. **Departure.** Say something to an NPC and walk out immediately — the departure reaction should fire in the room you left, unprefixed narration, and vary across attempts.
6. Convergence spot-check: `say network` at Info Prime, `say help` at Repairbot Prime, `say wares` at VND-9 and Mother Tansy — all previously single-line, all should now vary.
7. Seris and Veris now have departure reactions; VND-9 and Mother Tansy do too. Walk out on each.
8. Greetings fire **once ever per character** — a second visit is silent. Correct behavior, not a bug.
9. Nothing else changed voice: vendor list captions, the nothing-left-for-sale line, and repair sweep summaries are renderings and stay stable.
10. The shard, the spheres, and the obelisks remain silent. Say anything to them; nothing answers.
---
## 12. Closeout
Write `docs/shyland/Shyland_V23_Brief_5_Closeout_Report.txt` in the established format: pre-flight results, the Step 1 filing and its gate, what shipped, **no migration** (state it explicitly), test results with before/after totals, the §7 verification output verbatim, the geography audit table result, the deploy and the `make seed` reconciliation counts, **PENDING DEPLOY-TIME ACTIONS** (expected: none, if `make seed` ran), deviations/discrepancies, the commit list with the final implementation commit hash called out, and the operator playtest checklist as OPEN.
Then, as the final instruction of this brief: **run the issues report.**
