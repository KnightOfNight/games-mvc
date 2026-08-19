# Shyland V25.2 Brief 1 — Combat Instrumentation

**Release:** Version 25.2 (milestone `Version 25.2`) · **Founding ticket:** #33 · **Branch:** `version_25_2`
**Written:** 2026-08-19, V25.2 design session · **Design of record:** GDD §10.11 "Combat internals — the `combat_*` family" (committed `40cba4f`) + rulings 1–10 on #33 (comments dated 2026-08-19).

This is the release's **only** brief (scope law) and the release's **first** implementation brief (version-start duties apply). It instruments combat at the internals: seven `combat_*` record kinds join the MC stream, capturing what the engine rolls — including what no player ever sees. **No combat mechanic, message, or outcome changes.** No model changes, no migration, no seed.

---

## 1. Technical claims — verified at writing time (#252)

Every structural claim below was read from the code on `version_25_2` at `40cba4f` during the design session. Line numbers are anchors, not contracts — verify each at implementation pre-flight and hard-stop on load-bearing drift.

**The MC machinery (v25.1, all unchanged by this brief except where §5 says so):**
- `mc.mc_emit(kind, *, actor_id=None, actor_name='', room_id=None, audience=(), data=None)` — `mc.py:56`; fire-and-forget by construction; `XADD` with `maxlen=settings.MC_STREAM_MAXLEN, approximate=True` (`mc.py:74-77`). Doctrine (module docstring): game code imports `mc`, never the reverse.
- `MC_STREAM_MAXLEN = env.int('MC_STREAM_MAXLEN', default=100000)` — `game_mvc/settings/base.py:80`.
- `MCEvent.kind` is `CharField(max_length=16)` (`models.py:1245`); the longest new kind, `combat_action`, is 13 chars. The persister is kind-agnostic (`entry_to_row`, `run_mc_persister.py:38-64`) — **zero persister changes**.

**The combat round (ticker):**
- `process_combat` at `run_tick_engine.py:87`; rounds gate on `tick_counter % COMBAT_ROUND_TICKS` (line 342); `COMBAT_ROUND_TICKS = 3`, `DYING_DURATION_SECS = 30`, `STALE_SESSION_SECS = 30` (`models.py:6-9`).
- `execute_actions` (lines 457–824) is **sync under `database_sync_to_async`** and returns `(messages, statuses, room_messages, ended_sessions)`; the caller flushes at lines 826–846. `mc_emit` cannot be awaited inside it — records must accumulate and emit on return.
- Round ordering (lines 430–454): round 1 orders by `session.first_attacker` — **no initiative rolls on round 1**; later rounds roll `roll_initiative` for the character (effective DEX/PER) and per-NPC, ordering by character-vs-NPC-average.
- Player-attack block lines 508–726 (miss short-circuits at 533-536; graze falls through the hit path at half damage — **graze is invisible in player output**); NPC-attack block lines 729–822; the dying fall at 767–793.
- End sites, exhaustively: kill-path close (701–718), M2M sibling close (680–692), `self_heal_close` (302–313), `close_session` (127–140; called by the stale sweep and by the empty-participants close at 383–390), consumer `end_combat_session` (`consumers.py:4820-4825`; called on flee success at 2850 and the no-NPCs flee at 2823), and the death close inside `execute_death` (`run_tick_engine.py:229-236`). Quit does **not** end a session (combat continues after quit; the stale sweep closes it).

**The roll helpers (`combat_utils.py`):**
- `roll_initiative(stat_dex, stat_per)` :278 — `dex + per + randint(1,10)`, returns the total only.
- `resolve_hit(attacker_dex, target_dodge, crit_bonus=0.0)` :283 — `randint(1,20) + attacker_dex` vs `TO_HIT_DEFENSE_BASE + target_dodge`; on success one `random.random()` against the capped crit chance; graze window on near-miss. Returns **the string only** — die, defense, and crit chance are discarded.
- `calculate_damage(base_damage, stat_bonus, acuity_mod, durability_mod, hit_result, is_focus_target=True)` :305 — no randomness; returns the final float only.
- `composite_weapon_term(weapons, eff_str, eff_dex)` :319 — one `random.uniform` per weapon in iteration order; returns the total only.
- `roll_gear_bonus_damage(equipped_items)` :185 — per rolled proc entry: one `random.random()` chance gate, then one `randint` on success; flat `electric_damage_bonus` adds without a roll. Returns the int total only.
- `apply_npc_effects(npc_instance, target_character)` :484 — one `random.random()` per `NpcEffect` candidate; returns **display strings only**.
- `acuity_damage_modifier` :265, `apply_armor_mitigation(damage, tav)` :174, `effective_stats` :130 (base `stat_*` + gear, keys = the six primary stats), `get_npc_stats` :372 (dex/str/per/int/vitality), `npc_level` :358, `flee_contest_npc_side` :399 (session mean of effective PER), `total_armor_value` :154.

**Session lifecycle:**
- `CombatSession` fields (`models.py:1085-1102`): `characters` M2M, `npcs` M2M, `room` FK, `started_at`, `tick_counter`, `is_active`, `first_attacker`, `focus_npc`.
- `NpcInstance` fields (`models.py:845-858`): `definition` FK, `mk_tier`, `vitality_current/max`, `is_alive`; `NpcDefinition` carries `slug`, `name`, `combat_tier`.
- `start_combat(self, npcs, first_attacker='character', focus_npc=None)` (`consumers.py:4736-4754`) — sync under `database_sync_to_async`; **creates a session or joins NPCs into the character's existing one**; returns the session only. Exactly **three callers**: `consumers.py:850` (walk-in aggro), `:2799` (attack command), `:2884` (flee-into-aggro).
- Ticker respawn engagement: `engage` inside `engage_respawned_aggro` (`run_tick_engine.py:1024-1072`) — same create-or-join shape, returns `(new_npcs, fight_rows, status)` or `None`; emission-ready results collected in the loop at 1074–1082, sends at 1086–1103.
- The flee contest (`consumers.py:2832-2836`): `success = (eff['dex'] + random.randint(1, 20)) > avg_per` — the d20 is inline and unnamed today.
- `execute_death` (`run_tick_engine.py:202-237`) — sync; death penalties, respawn-at-home, effect cancellation, session close when the character was the last member; async dying loop at 239–274.

**Tests:** 8 existing files reference the roll helpers (`test_b2_amendment1`, `test_v24_10_brief1`, `test_gear_combat`, `test_b5_amendment1`, `test_v24_6_brief1`, `test_command_revamp`, `test_zombie_sessions`, `test_levelup_display`). The delegation strategy in §5.3 keeps every one untouched. `test_mc_sink.py` ships the `EmitRecorder` / `FakeStreamClient` patterns (`tests/test_mc_sink.py:58-92`) — reuse them.

---

## 2. Design rules — never deviate

1. **Capture is never load-bearing** (#33 body; GDD §10.11): every emission is fire-and-forget through `mc.mc_emit`; a sink failure drops a record, never a game action.
2. **No combat outcome changes.** The detailed helper variants make **the same random calls in the same order** as today's helpers; no new random calls anywhere in a combat path. Player-visible output is byte-identical.
3. **Envelope discipline (ruling 6):** `actor` = the acting entity — player-acted records carry `actor_id` = character pk + `actor_name` = character name; NPC-acted records carry `actor_id=None` + `actor_name` = the NPC definition name, with instance/definition pks in `data`. Session-scoped records (`combat_start`, `combat_join`, `combat_round`, `combat_flee`, `combat_death`, `combat_end`) carry the session's character as actor. **`audience=[]` always.** `room_id` = the session's room. Every combat record's `data` carries `session` (the CombatSession pk) as the encounter join key.
4. **Ordering (ruling 7):** a round's internals emit before the round's player-facing sends, in the exact order actions resolved. At every other site: emit the combat record before the outcome's sends fire (emit-before-send).
5. **Out of scope (ruling 3):** per-tick DoT/HoT effect internals in `process_effects`; analysis tooling of any kind (ruling 10); any retention/pruning change beyond §5.2 (ruling 9).
6. All seven kinds ≤ 16 characters: `combat_start`(12) `combat_join`(11) `combat_round`(12) `combat_action`(13) `combat_flee`(11) `combat_death`(12) `combat_end`(10).

---

## 3. Record schemas (the contract)

All values JSON-serializable; ints for pks; floats where the math is float. Field absence means not-applicable (never null-padding). Every `data` dict includes `session` and, where a round exists, `round` (= `tick_counter // COMBAT_ROUND_TICKS` at emission).

**`combat_start`** — one per `CombatSession.objects.create`, from any site.
`data`: `session`, `room` (pk), `zone` (name), `area` (name or absent), `origin` (`'attack' | 'aggro' | 'flee_aggro' | 'respawn_aggro'`), `first_attacker`, `character` (snapshot), `npcs` (list of NPC snapshots — the initial set added in the same motion).
Character snapshot: `{id, name, level, archetype, origin, stats: {str,dex,int,wis,end,per} (effective), gear_bonus: {six} (from gear_stat_bonus), tav, vitality: [cur,max], acuity: [cur, baseline, band_low, band_high], longevity: [cur,max]}`.
NPC snapshot: `{instance, definition, slug, name, combat_tier, mk_tier, level (npc_level), stats: {dex,str,per,int} (get_npc_stats minus vitality), vitality: [cur,max]}`.

**`combat_join`** — NPCs added to an already-active session (the join half of `start_combat` / ticker `engage`).
`data`: `session`, `room`, `origin` (same vocabulary), `npcs` (snapshots of the newly added only).

**`combat_round`** — one per resolved round, emitted after ordering is decided, before `execute_actions`.
`data`: `session`, `round`, `basis` (`'first_attacker'` on round 1, `'initiative'` after), and — initiative rounds only — `character_roll: {dex, per, die, total}`, `npc_rolls: [{instance, dex, per, die, total}]`, `npc_avg` (float), `order` (`'character_first' | 'npcs_first'`). Round 1 instead carries `first_attacker`.

**`combat_action`** — one per resolved attack action (skipped-dead/dying continues emit nothing).
Player→NPC `data`: `session`, `round`, `target: {instance, definition, mk_tier}`, `focus` (bool), `to_hit: {die, attack_total, defense, margin, result, crit_chance?, crit_die?}` (crit fields only when the hit landed and the crit roll ran), and on non-miss: `damage: {weapons: [{instance, definition, slot, roll, stat, durability, factor, term}] , unarmed_base?, stat_bonus, acuity_mod, hit_multiplier, raw, final}` (`weapons` on the armed path, `unarmed_base` on the unarmed path), `gear_bonus: {total, procs: [{stat, value, chance, fired, rolled?}], flat}` , `lifesteal` (int, when > 0), `target_vitality: [before, after]`, and on a kill: `kill: true, xp, level_ups` (count).
NPC→Player `data`: `session`, `round`, `attacker: {instance, definition, mk_tier}`, `to_hit: {…same}`, and on non-miss: `damage: {base_roll, str_basis: [low, high], hit_multiplier, raw, pre_mitigation, tav, final}`, `effects: [{name, chance, fired}]` (every candidate, fired or not), `target_vitality: [before, after]`, `target_fell` (bool).
Envelope: player action → actor = character; NPC action → `actor_id=None`, `actor_name` = definition name, pks in `data.attacker`.

**`combat_flee`** — one per rolled flee contest (`cmd_flee`; the pre-contest refusals are already `cmd` records).
`data`: `session`, `character`, `dex`, `die`, `total`, `npc_avg_per`, `success`, plus on success: `destination` (room pk) + `direction`, or `blocked: 'nowhere_to_run'` when the contest won but no exit existed.

**`combat_death`** — two phases.
Fall (from `execute_actions`, appended right after the fall at :767-793): `data`: `session`, `round`, `phase: 'fall'`, `character`, `killer: {instance, definition, mk_tier}`.
Death (from the dying loop, after `execute_death` returns): `data`: `phase: 'death'`, `character`, `home_room` (pk), `broken_items` (list of names, may be empty), `sessions_closed` (list of pks, may be empty).

**`combat_end`** — one per session close, at every end site.
`data`: `session`, `outcome` (`'win' | 'loss' | 'flee' | 'disengage'`), `reason` (`'kill' | 'sibling_kill' | 'death' | 'flee' | 'stale' | 'self_heal' | 'empty' | 'flee_empty'`), `rounds` (`tick_counter // COMBAT_ROUND_TICKS`), `duration_secs` (float, close-time minus `started_at`), `npcs_remaining: [{instance, vitality: [cur,max]}]` (state **before** `release_session_npcs` resets them; empty on win).
Outcome↔reason mapping: kill→win, sibling_kill→win, death→loss, flee→flee, stale/self_heal/empty/flee_empty→disengage. **`wipe`** (GDD §10.11's fifth outcome word) is defined but never emitted while sessions hold one character — it becomes distinct from `loss` only if multi-character sessions ship (#220's territory); note this in the arch doc.

---

## 4. Version start — the opening act (standing requirement)

1. `SHYLAND_VERSION` → `"25.2-DEV"` (`django/src/apps/shyland/version.py:8`) in **its own commit**, the pin-test assertion moved in the same commit.
2. `make deploy-dev` from the worktree (the version-start deploy).

(Step 0 — the closeout-report stub commit + push — precedes this per the standing implementation ritual.)

## 5. Implementation

**5.1 — `MC_STREAM_MAXLEN` default 100000 → 250000** (`base.py:80`; ruling 8). Shared-surface note: `base.py` is settings — this single-line default change is operator-authorized by the design session's ruling 8 (recorded on #33, 2026-08-19); touch nothing else in the file.

**5.2 — Detailed helper variants (`combat_utils.py`).** For each helper below, add a `<name>_detailed(...)` returning `(existing_return_value, detail_dict)`. **Move the original body into the detailed form; the plain name becomes a one-line delegation that discards the detail.** Every existing caller and all 8 test files stay untouched and green. Identical random-call order is a hard requirement (§2.2).
- `roll_initiative_detailed(stat_dex, stat_per)` → detail `{dex, per, die, total}`.
- `resolve_hit_detailed(attacker_dex, target_dodge, crit_bonus=0.0)` → detail `{die, attack_total, defense, margin, result, crit_chance?, crit_die?}` (`margin = total - defense`; crit fields present only when the success branch rolled them — capture the `random.random()` value as `crit_die`).
- `calculate_damage_detailed(...)` → detail `{effective_acuity, hit_multiplier, raw, final}` (no randomness).
- `composite_weapon_term_detailed(weapons, eff_str, eff_dex)` → detail `{primary_slot, weapons: [{instance, definition, slot, roll, stat, durability, factor, term}]}` (same iteration order → same `random.uniform` order).
- `roll_gear_bonus_damage_detailed(equipped_items)` → detail `{total, procs: [{stat, value, chance, fired, rolled?}], flat}` — one entry per proc-factor candidate whether it fired or not (`rolled` = the randint result, present only when fired); `flat` = summed electric bonus. Chance-gate and randint order unchanged.
- `apply_npc_effects_detailed(npc_instance, target_character)` → `(messages, candidates)` with `candidates = [{name, chance, fired}]` for **every** `NpcEffect` row evaluated. One `random.random()` per candidate, exactly as today.

**5.3 — Snapshot builders (`combat_utils.py`, sync, DB-context):** `combat_snapshot_character(character, equipped_items=None)` and `combat_snapshot_npc(npc)` returning the §3 snapshot dicts. They live in `combat_utils`, **not `mc.py`** — mc.py's import direction is doctrine (§1). Reuse `effective_stats`, `gear_stat_bonus`, `total_armor_value`, `get_npc_stats`, `npc_level`; no new queries beyond one equipped-set load when `equipped_items` isn't passed.

**5.4 — `combat_start` / `combat_join` from the consumer.** `start_combat` (`consumers.py:4736`) builds the record dict(s) inside (it has the DB context) and returns `(session, records)` where `records` is a list of ready-to-emit dicts (`{kind, actor_id, actor_name, room_id, audience, data}`). Created → one `combat_start` (with the just-added NPC snapshots); joined-with-new-NPCs → one `combat_join`; joined-with-nothing-new → empty list. Add an `origin` parameter (`'attack'`/`'aggro'`/`'flee_aggro'`). Update the **three callers** (`:850` origin `'aggro'`, `:2799` origin `'attack'`, `:2884` origin `'flee_aggro'`) to unpack and emit each record via `await mc.mc_emit(**r)` immediately after the call returns, before any subsequent send.

**5.5 — `combat_start` / `combat_join` from the ticker.** `engage` (`run_tick_engine.py:1024`) builds and returns the record(s) the same way (origin `'respawn_aggro'`); `engage_respawned_aggro` collects them in its results loop (1074–1082) and emits **all records before** the engagement-line broadcasts and fight payloads (1086–1103).

**5.6 — `combat_round`.** In the ordering block (430–454): switch `char_initiative` and the per-NPC loop to `roll_initiative_detailed`; build the §3 record (round-1 form on `is_first_round`); `await mc.mc_emit(...)` **before** `execute_actions` runs.

**5.7 — `combat_action` + the fall.** `execute_actions` accumulates `mc_records` (ready-to-emit dicts, in resolution order) and returns a 5-tuple `(messages, statuses, room_messages, ended_sessions, mc_records)`. Inside: switch the combat paths to the detailed variants (`resolve_hit_detailed` at :527 and :738, `calculate_damage_detailed` at :555 and :754, `composite_weapon_term_detailed` at :544, `roll_gear_bonus_damage_detailed` at :564, `apply_npc_effects_detailed` at :812); capture `target_vitality` before/after around the existing writes; append one `combat_action` per resolved action (miss actions carry `to_hit` only); on the dying fall (:767-793) append the `combat_death` fall record after the action record that caused it; on kills append `kill/xp/level_ups` to the action record (count the level-up loop's iterations). The caller (826–846) emits every `mc_records` entry first, then flushes messages/statuses/rooms exactly as today.

**5.8 — `combat_flee`.** In `cmd_flee`: name the inline d20 (`die = random.randint(1, 20)` replacing the anonymous roll at :2836 — same single call), build the §3 record, `await mc.mc_emit(...)` immediately after the contest resolves (both success and failure), before any outcome send; fill `destination/direction` or `blocked` in the success branch as it resolves.

**5.9 — `combat_end` at every end site.** Sync closers build and return record dicts; their async callers emit before sends:
- Kill-path close (701–718): append `combat_end` (win/kill) to `mc_records`.
- Sibling close (680–692): append `combat_end` (win/sibling_kill) for the sibling session to `mc_records`.
- `self_heal_close` (302–313): return the record too; emit in the 327–337 loop before `send_to_player`.
- `close_session` (127–140): add a `reason` parameter (`'stale'` from the sweep, `'empty'` from :383-390); return the record; emit before the payload sends at both call sites.
- Consumer `end_combat_session` (4820): add a `reason` parameter and return the record; flee-success caller (:2850) emits flee/flee, no-NPCs caller (:2823) emits disengage/flee_empty. Emit before the subsequent sends.
- `execute_death` (202–237): also build the death-phase `combat_death` record and a `combat_end` (loss/death) per session it closed; return them; the dying loop (239–274) emits all before its sends.
`npcs_remaining` is captured **before** `release_session_npcs` runs at each site (empty list on win closes).

**5.10 — No migration.** No model changes anywhere in this brief. State this in the closeout.

## 6. Tests

New file `django/src/apps/shyland/tests/test_combat_instrumentation.py`, reusing `test_mc_sink.py`'s `EmitRecorder` pattern (patch `mc.mc_emit` / the module references the emitting code holds). Required coverage:
1. **Equivalence pins, one per detailed variant:** with `random.seed(k)`, the plain helper's return equals `_detailed(...)[0]` under the same seed, and `random.getstate()` after each matches — proving identical value and identical consumption. (For `apply_npc_effects` use a seeded DB fixture.)
2. `resolve_hit_detailed` branch coverage: miss / graze / hit / critical detail contents via patched randomness.
3. `start_combat` create → `combat_start` with complete character + NPC snapshots; join → `combat_join` with only the new NPCs; no-new-NPCs → no record.
4. Envelope discipline: every emitted combat record has `audience == []`; NPC-acted `combat_action` has `actor_id is None` and pks in data; every record's `data.session` present.
5. Ordering: drive one round through `process_combat` with recorder + patched sends; assert the emission sequence `combat_round` → `combat_action`(s) in resolution order → first player-facing send.
6. `combat_end` outcome mapping: one test per end site (kill, sibling_kill via a shared-NPC second session, death, flee, stale, self_heal, empty, flee_empty) asserting outcome + reason + `npcs_remaining` semantics.
7. Kind-length invariant: every new kind string ≤ 16 chars (pins the `MCEvent.kind` fit).
8. The fall: a killing NPC blow emits the action record with `target_fell` and a `combat_death` fall record after it; `execute_death` emits the death-phase record + loss `combat_end`.

The suite baseline is **702**; report the new total with explicit arithmetic in the closeout.

## 7. Verification (all must pass before commit of the closeout)

1. Full in-container suite — the only working form: `python manage.py test apps/shyland/tests` via `docker exec` in the django container.
2. Discipline greps (single-quoted patterns):
   - `grep -n 'resolve_hit(' run_tick_engine.py` → zero hits (both combat blocks use `resolve_hit_detailed`); same check for `calculate_damage(`, `composite_weapon_term(`, `roll_gear_bonus_damage(`, `apply_npc_effects(` in `run_tick_engine.py`.
   - `grep -rn 'mc_emit' django/src/apps/shyland/` → emission sites are exactly those this brief names.
3. In-container settings check: `settings.MC_STREAM_MAXLEN == 250000` (dev `.env` files set no override — verify that assumption too).
4. Live dev-stack fight (after §8's deploy): scripted throwaway character (created and deleted by the verification script, the 25.1 pattern) placed with a seeded NPC; let the live ticker run a real fight to a kill; then assert via shell + `redis-cli`/ORM: the session's `combat_start`, ≥1 `combat_round`, ≥2 `combat_action` (both directions), `combat_end` (win/kill) all present in stream **and** `MCEvent` rows; `audience == []` on every combat record; within one round, every combat record's stream id precedes the round's first `out` record's id. Run a flee case (success or failure both acceptable — assert the `combat_flee` record matches what happened).
5. **Volume data point (closeout requirement):** report the sample fight's combat-record count and records/sec alongside 25.1's 24-records/40s non-combat baseline — this is the combat number GDD §10.11's retention posture has been waiting for.

## 8. Deploy (standing requirement)

`make deploy-dev` from the worktree once implementation and §6–§7 pass (plus the version-start deploy in §4). Production is never touched from this session (Deployment Law).

## 9. Architecture doc — last, gated

**This step is gated on all implementation and verification steps above being complete and passing.** Update `docs/shyland/Shyland_Architecture_v25.md` **in place**: stamp → 25.2; the header hash **moves** to this brief's final implementation commit (architectural change). Sections: **§4.19 (the MC sink)** gains the combat family — the seven kinds and their schemas (§3 above), the detailed-variant helper pattern and its equivalence guarantee, the snapshot builders, the emission sites (consumer + ticker), the internals-first ordering contract, the `wipe` reserved-not-emitted note, and the MAXLEN default change. Update the GDD-lockstep line the doc's header carries as its convention requires. No other section changes.

## 10. Operator playtest checklist (dev stack)

After §8's deploy:
1. Fight and kill an NPC. Combat must feel and read **exactly** as before — no new lines, no changed lines, no latency change in the 3-second rounds.
2. Flee a fight (try until you see both a success and a failure).
3. Die to an NPC; confirm the dying window and respawn behave as before.
4. Admin → MC events (read-only): filter kind `combat_action` — rows carry to-hit and damage detail; find your fight's `combat_start` and confirm the snapshot reads correctly (your level/archetype/origin/stats, the NPC's definition/Mk/level); confirm the `combat_end` row's outcome matches what happened.
5. Confirm a graze exists in the data that you never saw in output (filter `combat_action` rows for `result: graze` from your fight — the line on screen said an ordinary hit).

## 11. Closeout requirements

The closeout report (`.txt`, completed in place from the Step-0 stub) includes: the technical pre-flight result (§1 claims diffed against the branch tip); the commit list with the final implementation hash; deviations (none silent); §7's verification outcomes including the volume data point; suite arithmetic (702 + N = total); the explicit no-migration statement; **PENDING DEPLOY-TIME ACTIONS: none** (the closeout tail's `make deploy-prod` ships this as ordinary image build + restart; no data actions, no seed, no migration); and the **operator playtest disposition** (#170) verbatim-style. Issue #33 closes gated on §7 passing, with a comment naming this brief and the final hash. End with the `implementation-session-end` ritual (which runs the issues report).

---

*Self-consistency read performed at writing time: schemas in §3, emission sites in §5, and tests in §6 cross-checked against each other and against the §1 verified claims; no internal contradictions found. The GDD §10.11 family text (40cba4f) is the design of record; this brief is its implementation contract.*
