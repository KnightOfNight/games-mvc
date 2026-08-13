# Shyland V24.26 Brief 1 — Shard Relay & Attunement

- **Release:** Version 24.26 (milestone `Version 24.26`)
- **Founding ticket:** #38 (obelisk attunement: player-set home spawn)
- **Dependency:** #30 (checkpoint shards as travel senders) — ships in this brief
- **Branch:** `version_24_26`
- **Design source:** GDD §2.11 (Network Shape relay rules; the new Attunement subsection; the home command's generalized destination), §2.6 (travel options), §3.7 (death respawn), §9 (chart row `attune`, footnote 8, gating matrix, pools, §9.2 recall retirement) — all committed on this branch with `(v24.26, pending implementation)` markers. The GDD text is authoritative; this brief operationalizes it.
- **This is the first implementation brief of the release.**

## Design rules that must not be deviated from

1. **The relay (#30):** an obelisk-type node sends to every revealed node; a checkpoint-type node sends to **revealed spheres only** — never to another shard. This is the standing membership check plus one `node_type` filter; no new revelation machinery, no new per-character state.
2. **Revelation is enforced at shard senders, explicitly (operator callout on #30):** a sphere the character has not revealed is absent from a shard's listing, absent from its tab completion, and refused on a direct `travel <name>` attempt. The verification section covers this by name.
3. **`attune` is a bare verb — no nouns, ever.** Presence is the argument. Three exhaustive cases: room has no travel node → warn; already attuned to this room's node → warn; otherwise the bond moves and the command reports the new attunement and home location. In-the-room only; no remote form.
4. **One home at a time.** Attuning replaces the previous bond — no confirmation friction, free, instant, no cooldown of its own.
5. **Any travel node is attunable** — shard and sphere alike, the Heart included. The **effective home** of a character is `attuned_node` when set, else the founding node (the Heart of the Convergence, pinned by seed-verify as `travel_name='The Convergence', node_type='obelisk'`). The already-attuned check compares against the *effective* home, so a fresh character typing `attune` at the Heart is told they are already attuned.
6. **One home concept (#38 ruling B5):** the effective home node is both where `home` delivers and where death respawn wakes. Same node, always, no separate settings.
7. **Home resolves at landing:** the `home` countdown reads the effective home at completion time — the fog takes you to your home *as it is when the fog parts*. No destination is captured at initiation.
8. **No combat gate for `attune`, structurally:** every attunable room is a safe room, so the success path cannot occur in combat — do not add `attune` to the combat-refused set; an in-combat `attune` can only ever draw the no-node warn. **While dying it refuses** like every non-whitelisted command via the central dying gate (verify the gate is deny-by-default for new verbs; if it is not, that is a deviation to report, not to silently fix differently).
9. **The recall scroll is retired (ruling C):** `Character.recall_room` is removed and every reference swept. The concept vocabulary is now *home / attunement*; no code, comment, or help text may speak of "recall" when it means home (the `NO_RECALL` room-flag constant is out of scope and stays).
10. **Home's cooldown semantics are untouched:** 5-minute completion-only, on the command — attuning never starts, resets, or clears it. Countdown timing, interruption rules, and the fog voice are untouched.
11. **Pooled speech law:** every player-facing line this brief adds that the world can say more than once ships in a pool of ≥3. The attune success is a pooled ceremony line ending in a **stable, exact parenthetical report** — the house cooldown-refusal shape: varied prose, machine-honest parens — `... (Home: {travel_name})`. The parenthetical never varies.
12. **Three-layer doctrine:** attune's no-node and already-attuned responses are **warn** (world declined); the success ceremony is success-voice. Travel's relay refusals stay in their existing layers.
13. **No new color literals** — the chart set-equality test stays green.

## Step 1 — Version constant (opening act)

In its own commit, before any other change:

- `django/src/apps/shyland/version.py` line 8: `SHYLAND_VERSION = "24.25"` → `"24.26-DEV"`.
- The pin test moves in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py` line 118, `assertEqual(SHYLAND_VERSION, '24.25')` → `'24.26-DEV'`.
- Then run the version-start `make deploy-dev` from the worktree.

## Step 2 — Model & migration

File: `django/src/apps/shyland/models.py`.

**2a. `Character` gains the bond and loses the dead field** (the `recall_room` line is at ≈ line 245):

```python
attuned_node = models.ForeignKey(
    'TravelNode', null=True, blank=True, on_delete=models.SET_NULL,
    related_name='attuned_characters',
    help_text="The character's home node (GDD §2.11, Attunement): where "
              "'home' delivers and where death respawn wakes. Null = the "
              "founding node (the Heart of the Convergence).")
```

- **Remove** `recall_room` in the same change. No data migration and no grandfather step: null means the Heart, which is what every existing character's `recall_room` pointed at — existing characters are unchanged by construction (ruling B2).
- `TravelNode` is defined after `Character` in the file — hence the string reference `'TravelNode'`.

**2b. Doc-in-code truth:** update the `TravelNode` docstring (≈ lines 975–986: "Travel is free and only initiates from a room whose node is obelisk-type; checkpoints are destinations only.") and the `node_type` help_text (≈ line 997: "Obelisks are travel sources and destinations. Checkpoints are destinations only.") to the relay model: obelisks send anywhere; checkpoints relay to revealed obelisks (GDD §2.11, v24.26).

**2c. Schema migration:** `make makemigrations APP=shyland`, then `make migrate`. Commit the generated file; never hand-edit it.

## Step 3 — Effective-home resolution (one resolver, two consumers)

The founding-node query already exists as `get_heart_room` (`django/src/apps/shyland/consumers.py` ≈ line 3065). Generalize it:

- **Consumer:** replace `get_heart_room` with `get_home_room` — resolve the character's `attuned_node` (`select_related('attuned_node__room__zone')` on the character load, or a dedicated query); when null, fall back to the founding-node query verbatim. The stale docstring ("#38 attunement is a future version") dies with it.
- **Tick engine:** `django/src/apps/shyland/management/commands/run_tick_engine.py` — `get_expired_dying` (≈ line 172) changes its `select_related` from `'recall_room__zone', 'recall_room__area'` to the attuned-node path; `execute_death` (≈ line 181) resolves `character.attuned_node.room` with the same founding-node fallback, and `character.current_room` is set to that room. The respawn message and status payload (≈ lines 218–249) keep their shape — only the resolved room changes. The `'your recall point'` fallback string in the death message becomes home vocabulary (authored at implementation).
- The resolver logic (attuned-or-founding) must be **identical** in both places; a shared helper in `models.py` or a small utility is preferred over duplication if the sync/async split allows it cleanly.

## Step 4 — The `attune` command

File: `django/src/apps/shyland/consumers.py`.

- New `cmd_attune`, registered in the `receive_json` dispatch table. Chart cell: footnote 2 (no arguments expected or required; all arguments ignored).
- Logic, exactly the three ruled cases:
  1. Current room has no `TravelNode` → warn, one line from `ATTUNE_NO_NODE_LINES`.
  2. Room's node == effective home (Step 3 resolution — null compares as the founding node) → warn, one line from `ATTUNE_ALREADY_LINES`.
  3. Otherwise → atomic update (`Character.objects.filter(pk=...).update(attuned_node=node)` — never read-modify-write on a cached object), then the success line: one line from `ATTUNE_SUCCESS_LINES` ending in the stable parenthetical `(Home: {travel_name})`, success category.
- Pools: module-level constants, ≥3 lines each, authored at implementation in the obelisk network's voice under the creative-content policy (the ceremony is the Shard or sphere acknowledging the bond — GDD §2.11). `{travel_name}` available as a slot; the parenthetical is composed outside the pool so it never varies.
- **Gating:** do *not* add `attune` to the combat-refused set (design rule 8). Confirm the dying gate refuses it by default.
- **Chart/help/completion sync (one source of truth, three surfaces):** add `attune` to the §9 chart's help rendering (the generated help in `consumers.py` ≈ line 1197 area) and to the connect-time verb list; tab completion completes the verb only — there is no noun pool.

### Step 4b — The `Home:` row in `stats` (operator-ruled 2026-08-13, on #38)

File: `django/src/apps/shyland/consumers.py`, `_send_stats` (≈ line 2749).

- The identity block gains a `Home:` row **directly under the `Player:` line**, before the blank line and the stat rows: `  Home: {travel_name}` — the effective home node's `travel_name` (a null bond renders the founding node's name, `The Convergence`). Value-color under the standing key/value form, exact, never varying (a rendering, not speech).
- Resolve via Step 3's effective-home resolution; extend the character load's `select_related` as needed — no extra query per stat row.

## Step 5 — The relay (`travel` from a shard)

File: `django/src/apps/shyland/consumers.py`.

- **The sender gate** (`cmd_travel` ≈ line 707): delete the checkpoint refusal (`'... only an obelisk itself can send you onward.'`). Both node types now proceed; the destination pool differs by sender type.
- **The pool:** `get_revealed_destinations` (≈ line 3985) gains a `spheres_only=False` parameter adding `.filter(node_type='obelisk')`. `cmd_travel` passes `spheres_only=(node.node_type != 'obelisk')`. Same call shape in `_complete_travel` (≈ line 3637): the `node_type != 'obelisk'` early-return is replaced by the sphere-filtered pool — completion completes exactly what the sender offers (design rule 2).
- **The no-node refusal** (≈ line 701, `'There is no obelisk here...'`): reword to teach obelisk-or-shard (authored at implementation; stays warn).
- **The listing** (≈ lines 716–760): format is untouched — same per-zone blocks, same hardness sort, same muted locked-zone rows (they apply at a shard listing identically). The opener line (`'The Obelisk offers passage to...'`) gains a shard-sender variant in the shard's voice (authored at implementation); the empty-pool line likewise (defensive only — the Heart reveals at first login, so a shard's sphere pool is never empty in practice).
- **Departure/arrival messaging:** untouched — the same `TravelMessage` pools fire for relay travel.
- **Zone locks (§2.12):** no changes — the lock check is transition-generic and already runs on the travel path regardless of sender type.

## Step 6 — Home delivers to the bond

File: `django/src/apps/shyland/consumers.py`, `cmd_home` (≈ line 3088) and the delayed-action completion.

- Destination: the effective home room via Step 3's `get_home_room`, **read at countdown completion** (design rule 7). If the initiation currently pre-resolves the room, move the resolution to the completion callback.
- The already-at-home kindly refusal generalizes: compare against the effective home room, not the Heart (the existing line's wording survives if it doesn't name the Heart; otherwise reword at implementation).
- Cooldown machinery (`home_last_completed`, `home_cooldown_seconds`, the wry refusal with the exact parenthetical), countdown pools, interruption rules: **untouched** (design rule 10).

## Step 7 — Reference sweep

`grep -rn 'recall_room' django/src/` must return **only** migration files when this step completes. Known sites to convert:

- `django/src/apps/shyland/views.py` ≈ line 85: character creation sets `recall_room=spawn_room` — delete the kwarg (a new character's `attuned_node` stays null = the Heart, ruling B2).
- `django/src/apps/shyland/admin.py` ≈ lines 118, 122: `raw_id_fields` and fieldsets swap `recall_room` → `attuned_node`.
- `django/src/apps/shyland/consumers.py` ≈ lines 3862, 4386: `select_related('recall_room', ...)` → the attuned-node path as Step 3 requires.
- `django/src/apps/shyland/management/commands/seed_world.py` ≈ line 2609: the `recall_room` null-backfill line is deleted (dead field; no replacement — null is the design's default). **No other seed changes. Expected deletion count: 0 (no seed-owned data is touched).**
- Test factories across `django/src/apps/shyland/tests/` that pass `recall_room=room`: drop the kwarg, or convert to `attuned_node` where the test exercises respawn/home destinations (e.g. `test_room_visits.py` ≈ line 249 `test_respawn_records_visit_at_recall_room` — converts to the attuned-node shape; the intent, respawn-records-a-visit, is preserved as an explicit assertion and the conversion is reported as a deviation-style note in the closeout).

## Step 8 — Tests

Additions (new test file(s) under `django/src/apps/shyland/tests/`; invocation, the only working form: `python manage.py test apps/shyland/tests` via `docker exec` in the django container):

1. **Model:** `Character.attuned_node` present, nullable, SET_NULL; `recall_room` absent.
2. **attune, three cases:** no-node room → warn, line in `ATTUNE_NO_NODE_LINES` (pool-membership assertion); at effective home (both the null-at-Heart case and the explicit-bond case) → warn, line in `ATTUNE_ALREADY_LINES`; at a new node → FK updated, success line in `ATTUNE_SUCCESS_LINES` ending with exact `(Home: <travel_name>)`; re-attuning at the Heart after bonding elsewhere sets the founding node explicitly.
3. **attune gating:** refused while dying; in combat in a nodeless room it draws the no-node warn (no combat refusal).
4. **Relay pools (design rule 2, the callout):** from a checkpoint node, the listing and `_complete_travel` offer exactly the revealed **spheres**; an unrevealed sphere is absent and a direct `travel <its name>` is refused; a revealed **shard** never appears from a shard sender. From an obelisk, the full revealed pool is unchanged.
5. **Relay travel:** a character at a shard with the Heart revealed travels to the Heart successfully; arrival/departure messaging fires from the standard pools.
6. **home:** delivers to the attuned node's room; null delivers to the Heart; a bond changed mid-countdown lands at the *new* home (completion-time resolution, design rule 7).
7. **Respawn:** death delivers to the attuned node's room (full bars, visit recorded); null delivers to the Heart.
8. **Chart/help sync:** help output includes `attune`; the pin test moved in Step 1.
8b. **stats:** the sheet carries `Home: The Convergence` for a bond-less character and `Home: <travel_name>` after attuning, positioned directly under the `Player:` line.
9. **Color chart:** the set-equality test stays green.
10. Full suite green.

## Step 9 — Verification (all must pass before issue closure)

1. Full in-container suite green (path form above).
2. Dev shell checks: `Character` schema shows `attuned_node` and no `recall_room`; a test character's attune → `attuned_node_id` set; `grep -rn 'recall_room' django/src/` hits migrations only.
3. **The callout check, live:** on dev, with a character who has *not* revealed the Verdant Crown, `travel` at Fordwatch lists the Heart and not the Crown; `travel the verdant crown` refuses; after standing in the Crown once, it lists.
4. `make deploy-dev` from the worktree (build + migrate) once implementation and tests pass.

## Step 10 — Operator playtest checklist (dev stack)

After Step 9's deploy-dev:

- [ ] At the Heart, `attune` → the already-attuned response (a fresh bond-less character counts as Heart-attuned).
- [ ] In a nodeless room, `attune` → the no-node warn.
- [ ] `travel fordwatch` from the Heart; at Fordwatch, `travel` → spheres only (the Heart; the Verdant Crown only if this character has revealed it), no shard rows.
- [ ] At Fordwatch, `attune` → ceremony line ending `(Home: Fordwatch)`; `stats` now shows `Home: Fordwatch` under the Player line (and showed `Home: The Convergence` before the attune).
- [ ] Walk into the wild, `home` → the fog countdown, landing at **Fordwatch**; the cooldown refusal still carries its exact parenthetical on an immediate retry.
- [ ] Die on purpose → death sequence unchanged, respawn at **Fordwatch** with full bars.
- [ ] From Fordwatch, relay to the Heart via `travel the convergence`; `attune` at the Heart → home is the Heart again.
- [ ] `help` lists `attune`; tab completion completes `attune` (verb only) and completes shard-sender `travel` to spheres only.
- [ ] Screen reader spot-check: attune's warn/success lines and the shard listing read out via the live region like any other output.

## Step 11 — Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. Update `docs/shyland/Shyland_Architecture_v24.md` **in place**: stamp → 24.26, and the header hash **moves** (this release is architectural — a Character schema change, a new command, a changed travel topology). Sections to update: §4 (the Shyland app: `Character.attuned_node` replacing `recall_room`, `TravelNode` relay semantics, `cmd_attune`, the sender-typed destination pool, home/respawn resolution through the effective-home resolver, the tick engine's death path) and any §6/§7/§8 rows that speak of recall or checkpoint destination-only semantics (sweep `recall` and `checkpoint` mentions; the `NO_RECALL` flag row, if present, stays).

## Standing requirements & closeout

- Commit and push at **every step boundary** — branch only, never merge to main.
- **PENDING DEPLOY-TIME ACTIONS: none.** The schema migration rides `make deploy-prod`'s migrate in the closeout tail; there are no seed reruns and no data actions (expected seed deletions: 0 — nothing seed-owned changes).
- Closeout report as `.txt` in `docs/shyland/`: final commit hash, operator playtest disposition (verbatim-style per #170), the Step-7 sweep result (`recall_room` grep), test-conversion notes (Step 7's factory changes), any deviations. The Step-0 stub is completed in place.
- Issues **#38** (founding) and **#30** (dependency) close gated on Step 9 passing.
- No transient-document pruning; the operator prunes.
- End with the `implementation-session-end` ritual (playtest disposition first, issues report last).
