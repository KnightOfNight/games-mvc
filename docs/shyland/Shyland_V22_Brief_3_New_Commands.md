Shyland V22 Brief 3 — New Commands (B3): home, cancel, last, sudo
Version: 22 · Bucket: B3 · Brief: 3 of 4 Issues (all close at closeout, gated on verification): #57 (home), #113 (cancel), #88 (last), #112 (sudo) Normative specification: `docs/shyland/Shyland_V22_B2_Command_Spec_DD.md` — the chart rows, footnotes (2, 9, 12, 18), state matrix (§5), success sentences (§6), information kinds (§9), and admin gating (§12) govern these commands. Step 1 records the B3 design-session rulings (2026-07-20) that complete the spec. Where anything conflicts, Step 1 wins, then the DD; stop and flag. Branch: the v22 worktree branch. Never merge.
Out of scope, explicitly: the firehose consumer (#33/#37 — sudo produces no game response and builds no pipe); attunement (#38 — the Heart is the sole home destination); any macro/alias work (#125); the parked display items (#119, pane-not-reddening).
Pre-flight

1. Verify `DOCKER_HOST` before any deployment-touching action.
2. v22 worktree branch, clean tree.

Step 0 — Self-commit this brief
Save verbatim to `docs/shyland/Shyland_V22_Brief_3_New_Commands.md` (skip if identical exists), commit, push immediately. Commit and push at every step boundary. Never merge.
Step 1 — B3 design rulings (2026-07-20, the design chat)

1. Home is a 15-second delayed action, narrated as atmosphere — authored prose lines during the wait, never a timer UI and never meta-instructions about canceling. The wait warns implicitly, in fiction.
2. Anything breaks it: the player's own movement, combat entry of any kind (their attack, aggro engagement, an incoming attack — including another player in PvP), and `cancel`. Interruption by violence gets its own authored voice distinct from voluntary cancellation. A player's movement command auto-cancels the countdown (with its line) and the movement then proceeds normally.
3. Disconnect mid-countdown: the countdown dies silently. Intent state dies with the intender.
4. Cooldown: 15 minutes, default for all players, per-player overridable (Django admin edits the field). Completion-only consumption: interrupted or canceled countdowns never start the clock; it starts when the traveler lands at the Heart.
5. Cooldown refusal voice: wry in-fiction prose ending in a terse machine-honest parenthetical with the remaining time — the template: `You can't go home yet, you were just there. Give it a few minutes. (10m cooldown rem.)` Funny in the prose, exact in the parens, warn-color.
6. Ceremony like travel: departure witnessed by the origin room at the vanish, arrival witnessed at the Heart, in home's own fog-motif voice (travel's machinery pattern, not its words). The Heart is the only destination.
7. Timer infrastructure (delegated ruling, minimal-footprint law): a connection-bound `asyncio` task on the consumer. A named registry on the consumer (delayed-action name → task) is created by this work and is `cancel`'s candidate pool and the standing template for all future delayed actions. No tick-engine involvement, no DB countdown state. The cooldown timestamp is real state and lives on the Character.
8. Bare `cancel` with nothing running: `You don't have anything to cancel.` — verbatim, warn-color.
9. Last's data: a Character timestamp recording last connect (written at websocket accept); Redis (the who machinery) supplies liveness. Display forms in the Last seen column: `never` (no recorded connect), `since <ISO-8601 UTC>` (online — the word Online lives in the Status column, not repeated here), `<ISO-8601 UTC>` (offline). Columns: Character / Status / Last seen, Status between name and time. Character uses the composite form `Shy-Guy - Level 10 Highborn Blade`. Order: online rows first (most recent connect first), then offline most-recent first, `never` rows last.
10. The admin Group is named `admins.shyland`.

Step 2 — Migration
File: `django/src/apps/shyland/models.py`. One schema migration, three fields on Character:

1. `home_cooldown_seconds` — `PositiveIntegerField(default=900)`, help_text noting per-player override via Django admin.
2. `home_last_completed` — `DateTimeField(null=True, blank=True)` — set only on completed home trips.
3. `last_connect` — `DateTimeField(null=True, blank=True)` — set at every websocket accept.

Plus one data migration creating the auth Group `admins.shyland` idempotently (get_or_create; no members seeded).
Run `makemigrations` + `migrate`.
Step 3 — Admin stealth gating (DD §12, footnote 18)
Files: `django/src/apps/shyland/consumers.py` (dispatch, help, completion).

1. Mark `sudo` and `last` as admin commands in the dispatch table's metadata.
2. On every attempt, check `admins.shyland` membership live (one query; no session caching — revocation is instant). Non-members receive the standard unknown-command response, byte-identical to gibberish input. Members proceed normally.
3. Help renders per-player: admin rows appear only for members (see Step 7). Tab completion's command-name pool likewise excludes admin commands for non-members.

Step 4 — sudo (#112)
Chart: footnote 9 (any arguments, bare included) + 18. For members: the command echoes like any command (echo/timestamps rules apply), and the game never responds — no output, no acknowledgment, by design. The arguments' journey to a listener is #33/#37's future; build nothing for it.
Step 5 — cancel (#113) and the delayed-action registry

1. Add the registry to the consumer: a dict of running delayed actions, name → asyncio task (home is its first and only resident). Registration/deregistration is the template all future delayed actions follow.
2. `cmd_cancel`: chart footnote 12. Bare with nothing running → the Step-1 verbatim line (warn). Bare with exactly one running → cancel it. With an argument → match against running-action names (the resolver's prefix rules); no match → warn. Canceling home prints the DD §6 line: `You stop heading home.` (value-color).
3. Allowed in all states including combat and dying (the matrix's standing rule — the escape hatch is never locked).
4. Tab completion for cancel's argument completes the running-action names.

Step 6 — home (#57)
`cmd_home`, chart footnote 2 (arguments ignored). Gate order on invocation:

1. State matrix: refused in combat and while dying (warn, in-voice).
2. Already at the Heart → refuse, warn: `You are already home.` (judgment call recorded: homing from home would burn the cooldown for nothing; the refusal is kindness).
3. Already counting down → refuse, warn: `You are already heading home.`
4. Cooldown: if `home_last_completed` + `home_cooldown_seconds` is in the future, refuse with a line from the cooldown pool (below), the parenthetical computed with coarse friendly units (minutes when ≥1m, else seconds): `(10m cooldown rem.)` / `(45s cooldown rem.)`.

The countdown (15s connection-bound task): authored lines at a fixed cadence — start (t=0), mid (t≈7s), late (t≈12s) — drawn from the pools below; then completion at t=15.
Interruption wiring: the dispatch path cancels the task on any movement command (line prints, then the move proceeds); combat entry of any kind cancels it (player's attack, aggro engagement at respawn or entry, any incoming attack) with the violent line. Voluntary `cancel` uses its own line (Step 5). Disconnect: the task dies with the connection — verify no line is emitted and no state is touched.
Completion: departure witness broadcast to the origin room → relocate the character to the Heart (the established spawn-relocation machinery: room move, RoomVisit, full room render, map, status sync) → traveler arrival line → arrival witness broadcast to the Heart → set `home_last_completed`.
Authored content (verbatim; the pools are complete as written):

* Start: `You close your eyes and reach for home. The edges of the world begin to soften.`
* Mid pool (one chosen at random): `You feel the world start to dissolve around you, and you know you'll soon be home.` / `The fog rises to your knees. Somewhere beyond it, the Heart is waiting.`
* Late pool (one chosen at random): `You can see home through the fog. Only a few moments now.` / `The world is thin as paper here. Home bleeds through it, warm and bright.`
* Traveler arrival: `The fog parts, and the Heart takes you in. You are home.`
* Departure witness (origin room): `{name} fades into a fog only they can see, and is gone.`
* Arrival witness (the Heart): `A fog gathers from nowhere, and {name} steps out of it.`
* Violent interruption (traveler): `The fog is ripped away. The world comes back hard — you are not going anywhere.`
* Movement auto-cancel (traveler, before the move renders): `You let the fog fall away and turn back to the world.`
* Cooldown pool (one chosen at random, parenthetical appended): `You can't go home yet, you were just there. Give it a few minutes.` / `The fog won't gather again so soon. Even homesickness has rules.`

Categories: countdown/traveler prose value-color; witnesses room-voice; refusals and both interruption lines warn-color; the arrival render follows standard room-entry output.
Step 7 — last (#88)
`cmd_last`, information, admin-gated. Set `last_connect` at websocket accept (all players, always — the data accrues regardless of who can read it). Output per DD §9 Kind 3 + Step 1.9: header `Last seen...` (key-color, ellipsis), muted column guide `Character / Status / Last seen`, value-color rows, the three time forms exactly, the ruled ordering. All characters listed (no cap — one row per character in the game).
Step 8 — Help and completion
The four rows go live from the chart: `home` and `cancel` visible to all; `last` and `sudo` rendered only for `admins.shyland` members (both the rows and the bottom-section references, if any). Usage strings compiled per the chart (`home`, `cancel [<command>]`, `last`, `sudo <anything>`). Descriptions verbatim: home `Return home after a short delay.` · cancel `Stop an in-progress command.` · last `Show characters and when they were last seen.` · sudo `Speak to the watcher.` The Version line remains last.
Step 9 — Tests
Extend the suite (`apps.shyland.tests`):

1. Stealth: non-member `sudo`/`last` responses byte-identical to an unknown command; member passes; membership checked live (revoke mid-session → next attempt refused); help/completion include admin rows for members only.
2. home: refusals (in combat, dying, at the Heart, already counting, cooldown with correct parenthetical math); override field honored (0 → immediate reuse); completion relocates to the Heart with RoomVisit + `home_last_completed` set; interruption by movement (line + move proceeds, no cooldown consumed), by aggro/attack (violent line, no cooldown), by cancel (DD line, no cooldown); disconnect mid-countdown leaves no line, no relocation, no cooldown.
3. cancel: bare-none verbatim line (warn); bare-one cancels; named match; works in combat.
4. last: the three time forms; ordering (online desc, offline desc, never last); `last_connect` written on connect; composite Character form.
5. Full suite green; report counts.

Step 10 — Operator playtest checklist
Ready after deploy: grant Shy-Guy `admins.shyland` via Django admin; `home` from deep in the Reach and stand still — the fog lines, the vanish, the Heart; watch the witness lines from Sharon-Love's incognito window; walk during a countdown; get jumped during a countdown in an aggro room; `cancel` one voluntarily; hit the cooldown and read the wry refusal; set your override to 0 and hearth freely; `last` as admin (and confirm it's gibberish to Sharon-Love); `sudo hello there` and enjoy the silence.
Step 11 — Architecture doc (gated last)
Gated on all implementation and verification above passing. Update `docs/shyland/Shyland_Architecture_v22.md` in place: the delayed-action registry and its template pattern, home's task/interruption/cooldown design (connection-bound; completion-only consumption; the three Character fields), the `admins.shyland` stealth gating (live check, per-player help/completion), last's data flow, and sudo's deliberate silence.
Closeout
`docs/shyland/Shyland_V22_Brief_3_New_Commands_Closeout_Report.txt`: per-step results, test totals, deviations, final commit hash. Close #57, #113, #88, #112 — gated on verification. Commit and push. Do not remove or prune any documents.
Finally: run the issues report.
