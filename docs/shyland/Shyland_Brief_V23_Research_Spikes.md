Shyland Brief: V23 Research Spikes (#27, #40)
Type: Research / ops brief — runs on `main`, no worktree, no code changes of any kind. Issues touched: #27 (comment only), #40 (comment only). No issue state changes: no closes, no label changes, no milestone changes. Version context: Version 23 planning. These spikes produce findings that the design chat will rule on later. Your job is facts, not verdicts.
Pre-flight

1. Working tree is clean and you are on `main`. If either is false, STOP and report.
2. Pending deploy-time actions from prior versions: none known (v22's `seed_world` + `rename_proc_stats` were confirmed executed on production 2026-07-21). If you discover evidence to the contrary while reading, note it in the closeout report but take no action.
3. This brief touches no deployment surface. Do not build, deploy, restart, or run any management command against any database. Read-only access to code and seed data only.

Step 0 — Self-commit
Save this brief's full text verbatim to `docs/shyland/Shyland_Brief_V23_Research_Spikes.md` (skip the write if an identical file already exists). Commit on `main` and push immediately — the push is the work-has-started signal.
Spike A — Issue #27: passive regen ticks landing after combat engagement
Observed (v19 combat log, from the issue): two passive regen ticks ("You feel your body recover. (+25 Vitality)") landed after NPC aggro engagement lines ("moves to attack!") but before first blows.
Your task — establish the code facts:

1. Read the tick engine (`django/src/apps/shyland/management/commands/run_tick_engine.py`) end to end for this question. Identify:
   * The passive regen pass: exactly where it runs in the tick, and what its character-selection query is.
   * Whether that selection checks combat-session membership (CombatSession or equivalent) to exclude in-combat characters — cite the exact filter, or its absence, with file and line.
   * The aggro-engagement path: where an NPC engaging a player creates/joins the combat session, and where in the tick ordering that happens relative to the regen pass.
2. Determine which of these explains the observed log, with evidence:
   * (a) Missing check: regen simply never excludes in-combat characters — it would tick during active combat too, not just at engagement.
   * (b) Same-tick ordering race: regen excludes in-combat characters, but within a single tick the regen pass runs before (or concurrently with) the engagement write, so a character engaged mid-tick still receives that tick's regen.
   * (c) Something else — describe it precisely.
3. If (b), state the exact ordering: which sweep runs first in the tick loop, and whether the race window is one tick wide or wider.
4. Note whether the same regen pass touches Acuity and Longevity, and whether any answer differs per bar.
5. Check whether v21's respawn-tick aggro engagement change (#17) or v22's B6 async-safety change (#135) altered this territory — the observation is from v19; confirm whether the mechanism you find still matches current code, and say so explicitly either way.

Deliverable: a structured comment on #27 containing: the mechanism verdict (a/b/c) with file/line citations for every claim; the tick-ordering narrative if (b); the per-bar note; the still-current-vs-v19 confirmation. Quote the relevant code lines verbatim in the comment (short excerpts).
Do NOT: decide whether in-combat regen is intended. Do NOT add or remove the `bug` label — the issue body ties the label to an intent ruling that has not been made. Classification happens in the design chat.
Spike B — Issue #40: repeated verbatim NPC messages (free repairs and beyond)
Observed (from the issue): Morra has exactly one free-repair flavor line, so every free repair from her produces identical text. Suspicion: the pattern is widespread.
Your task — inventory the duplication landscape. Read seed data (`django/src/apps/shyland/management/commands/seed_world.py`) and any consumer/dispatch code that composes NPC service messages (`django/src/apps/shyland/consumers.py` and neighbors). Produce:

1. Free-repair audit: every NPC that offers free repairs, and for each, how many distinct flavor-message variants exist (cite where the variants live). Expected finding per the issue: one each — confirm or refute.
2. Paid-repair audit: same question for paid repairs — does each repairer have one line or several? Include success/failure variants if they exist.
3. Wider single-line pattern sweep: other NPC interactions where a single authored line repeats verbatim on every occurrence. Sweep at minimum: vendor buy/sell transaction flavor, vendor greeting/browse lines, healer/service NPC lines, dialogue-response NPCs (talk targets), and any ambient/idle NPC barks if they exist. For each site: NPC (or system), trigger, variant count, where the text lives.
4. Mechanism note: for each category above, state whether variety would be a pure data change (add strings to an existing list the code already picks from randomly) or requires code changes (the composition site hardcodes one string / has no variant-selection machinery). This is the fact the design chat most needs for scoping the follow-up.
5. Summary table at the top of the comment: site | NPC(s) | variant count | data-only or code-change. One row per distinct message site.

Deliverable: a structured comment on #40 with the summary table and the detail beneath it, file/line citations throughout.
Do NOT: write any new flavor variants. Do NOT change any code or seed data. Explicitly out of scope per the issue.
Closeout

1. Commit a closeout report as `docs/shyland/Shyland_Brief_V23_Research_Spikes_Closeout.txt` on `main` summarizing: what was read, the #27 mechanism verdict, the #40 headline counts, any surprises, and confirmation that zero code changes were made. Include the final commit hash.
2. Push.
3. Run the issues report.
