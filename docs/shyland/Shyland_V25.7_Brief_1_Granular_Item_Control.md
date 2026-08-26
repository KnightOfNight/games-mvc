# Shyland V25.7 — Brief 1: Granular Item Control

- **Release:** Version 25.7 (milestone `Version 25.7`) · **Branch:** `version_25_7`
- **Issue set (all milestone members, all closed by this brief, gated on verification):** #287 (founding — item removal), #293 (inventory/item queries, read-side prerequisite), #288 (targeted equip/unequip), #289 (item mutation), #292 (bot URL normalization), #295 (bot management script)
- **Authored:** 2026-08-25, V25.7 design session. Rulings of record live as comments on the issues (all six, dated 2026-08-25). GDD text landed ahead: §10.11 "Granular item control (v25.7, … pending implementation)".
- **This brief is self-contained.** The implementation session reads this brief and the repo only.
- **No model changes. No migration. No seed data.** The entire game-side surface is new door handlers over existing fields.

---

## 1. Standing opening act (first brief of the release)

1. Bump `SHYLAND_VERSION` from `"25.6"` to `"25.7-DEV"` in `django/src/apps/shyland/version.py` (line 8) — **its own commit**, moving the pin test in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py` line 118 asserts `'25.6'` → assert `'25.7-DEV'`.
2. `make deploy-dev` from the worktree (the version-start deploy).

Later steps of this brief leave the constant alone; the closeout stamps `25.7`.

## 2. Technical claims — verified against the code at writing time (#252)

Every structural claim below was confirmed by file-read on `version_25_7` (tip `5c0a482`) on 2026-08-25. Load-bearing facts, with locations:

- **Dispatch is dict-driven:** `QUERY_HANDLERS` / `ACTION_HANDLERS` at `django/src/apps/shyland/mc_door.py:730-746`; `mc_consumer.py:208-209` resolves through them. Unknown kinds draw `unknown-query`/`unknown-action` in the consumer, **the MC record for every processed frame is emitted by the consumer after processing** (docstring + code, `mc_consumer.py:195-245`), and the kill switch is enforced consumer-side above dispatch — **new kinds inherit attribution and the kill switch with zero extra wiring**.
- **Addressing helpers:** `_resolve_character` (`mc_door.py:88`, `name__iexact` via `_character_by_name` at :81); `_require_str`/`_require_int` (:61/:72); `DoorError(code, detail)` (:51). `_send_player_line` (:148) carries `agent_name` and optional `event`.
- **Instance model:** `ItemInstance` (`models.py:581-665`): `owner` FK related_name **`inventory`**; fields `mk_tier`, `rarity` (+`ARTIFACT` constant), `rolled_primary_stats`, `rolled_secondary_stats`, `damage_midpoint`, `damage_spread`, `durability_current`, `is_broken`, `is_soulbound`/`soulbound_to`, `is_equipped`, `equipped_slot`, `is_cursed`, `curse_identified`, `active_curse` (FK → `EffectInstance`, related_name `cursed_item`), `is_identified`, `is_unidentifiable`. `definition` FK is **`on_delete=CASCADE`** — deleting a definition deletes its instances.
- **Curse wiring is latent:** `active_curse` is populated by **no code path today** (grep over `consumers.py`, `effect_utils.py`, `item_utils.py`: zero non-model hits) — it is admin-set data. Effect deactivation precedent is the death teardown (`management/commands/run_tick_engine.py:248-254`): `component_instances.filter(is_active=True).update(is_active=False, removed_by=…)` then the same on the `EffectInstance`.
- **Equip machinery:** the player slot-resolution algorithm is inline in `cmd_equip` (`consumers.py:1530-1631`): candidates per `defn.valid_slots` × `SLOT_CAPACITY` (`consumers.py:66`, `{'RING': 2}`) with two-hander extras; free slot wins; unambiguous single displacement auto-swaps behind `_unequip_blocked_reason`; ambiguity refuses. `_unequip_blocked_reason` (`consumers.py:1657-1669`) guards exactly two things: cursed, and bag carry-capacity. `unequip_item`/`equip_item` consumer helpers (:4486-4500) set flags and call `rescale_bars_for_gear` (lives in `combat_utils`, shared with the door — `_strip`/`_dress` call it at `mc_door.py:590/632`). `_strip` bypasses `_unequip_blocked_reason` by ruling (comment at `mc_door.py:584-586`).
- **Disposal precedent:** hard `item.delete()` — `do_sell` (`consumers.py:4644-4655`), `consume_item` (:4511-4513).
- **Artifact creation:** `_create_artifact` (`mc_door.py:507-559`) enforces `name__iexact` + slug uniqueness, `name-taken` on collision; validators `_validate_artifact_spec` (:370) and `_validate_stat_entries(entries, key, *, allow_floor)` (:342).
- **Bot generics:** `sudo_bot.py` `_execute_tool` (:686) maps tool name → door kind 1:1 against `QUERY_KINDS`/`ACTION_KINDS` frozensets (:85-88) and passes any `DoorError` code through as a tool error — new kinds need only the frozensets, `TOOLS` schemas (:128), and prompt text. `mc_door_agent.py` is a generic `query <kind> <json>` / `action <kind> <json>` REPL; its `QUERY_KINDS`/`ACTION_KINDS` tuples (:72-74) feed help/validation only.
- **#292 site:** `django_login(base_url, …)` composes `f'{base_url}/accounts/login/'` (`sudo_bot.py:530-533`); the WebSocket URL derives from the same `base_url`.
- **Tests:** door tests live in `django/src/apps/shyland/tests/test_mc_agent_door.py` (962 lines).

## 3. Game-side: two queries (`mc_door.py`)

Register in `QUERY_HANDLERS`: `'inventory': q_inventory`, `'item': q_item`.

### 3.1 `query inventory` (#293)

Params: `name` (via `_resolve_character`). Result — **uncapped**, every instance the character owns, equipped included (this is a state report, deliberately unlike the player `inventory` command's protective pools):

```json
{"character_id": N, "character_name": "...", "count": N,
 "items": [{"id": N, "slug": "...", "name": "...", "item_type": "...",
            "mk_tier": N, "rarity": "...", "durability_current": F,
            "is_broken": B, "is_soulbound": B,
            "is_equipped": B, "equipped_slot": "..."}]}
```

Query `char.inventory.select_related('definition').order_by('pk')`; `slug`/`name`/`item_type` from the definition. No cap, no truncation flag — `ITEMS_CAP` remains a catalog (`items`) concern.

### 3.2 `query item` (#293/#289)

Params: `item_id` (`_require_int`). Missing instance → `DoorError('not-found', …)`. Result: all roster fields above, plus full fidelity — `rolled_primary_stats`, `rolled_secondary_stats`, `damage_midpoint`, `damage_spread`, `is_cursed`, `curse_identified`, `is_identified`, `is_unidentifiable`, and holder context: `owner` (`{"id", "name"}` or `null`) and `room` (`_room_dict` of `current_room`, or `null`). Admin reads show **true state** — the no-leak rule governs world speech, which queries never touch.

## 4. Game-side: four actions (`mc_door.py`)

Register in `ACTION_HANDLERS`: `'remove_item'`, `'edit_item'`, `'equip_item'`, `'unequip_item'`.

**Shared addressing (all four):** params `name` + `item_id`. Resolve the character; fetch the instance; instance absent → `DoorError('not-found', …)`; instance owned by anyone else (or unowned) → `DoorError('not-owner', detail naming the actual state)`. **No string-based item resolution on any write path** — the bot resolves via `inventory` first; a stale id is a refusal, never a guess. Each handler's mutation runs in one `transaction.atomic()` block. All narration lines go through `_send_player_line` only when `_presence_online`; offline targets mutate silently. All lines are `system` category. Compose `item_ref(item)` **before** any deletion.

### 4.1 `remove_item` (#287)

1. If `active_curse_id` is set: deactivate the curse — `item.active_curse.component_instances.filter(is_active=True).update(is_active=False, removed_by='item-removed')`, then the `EffectInstance` itself (`is_active=False`, `removed_by='item-removed'`) — the death-teardown pattern applied to one effect. **The curse ends with the item** (operator-ruled).
2. Record `was_equipped = item.is_equipped`.
3. If `item.rarity == ItemInstance.ARTIFACT`: `item.definition.delete()` — the CASCADE removes the instance, and the unique name/slug free for re-authoring. `definition_removed = True`. Otherwise `item.delete()` only; `definition_removed = False`.
4. If `was_equipped`: `rescale_bars_for_gear(char)` (the bar law binds every max-changing mutation).
5. Narration: `An admin has taken {item_ref} from you.` — `event='refresh_status'` when `was_equipped`, else no event.
6. Result: `{"item_id": N, "definition_removed": B}`.

No combat gate, no protective guards — the `_strip` posture. Destruction, never transfer.

### 4.2 `edit_item` (#289)

Extra param: `changes` — a non-empty dict. Two whitelists:

- **Instance-side (any owned instance, any rarity):** `mk_tier` (int, ≥1, via `_require_int`), `rarity` (must be a valid `RARITY_CHOICES` key), `rolled_primary_stats` / `rolled_secondary_stats` (validate through `_validate_stat_entries`, same bounds as artifact creation), `damage_midpoint` / `damage_spread` (float ≥ 0, or `null` to clear the pair — both or neither non-null after the edit), `durability_current` (float 0–100; maintain the invariant `is_broken = (durability_current == 0)`).
- **Definition-side (only when `item.rarity == ARTIFACT` — an ordinary definition is a shared template and is refused with `DoorError('not-artifact', …)`):** `name`, `description`, `base_value`, `valid_slots`, `is_two_handed`, `armor_base`, `mystery_name`, `mystery_description`, `genre_tag`. Validate values through the same rules `_validate_artifact_spec` applies at creation. **Rename re-runs the unique-name law:** `name__iexact` and regenerated-slug uniqueness checks excluding the definition itself, `name-taken` on collision, empty slug → `bad-params`.

Any key outside the applicable whitelists → `DoorError('bad-params', naming the key)` — **the whole request refuses; no partial application** (the atomic block guarantees it). Raw set: the admin's values land exactly; nothing re-rolls or re-derives. `item_type` is deliberately not editable.

After a successful edit: if `item.is_equipped`, `rescale_bars_for_gear(char)` and narrate with `event='refresh_status'`; else narrate plain. Narration (composed after the edit, so a rename shows the new name): `An admin has altered {item_ref}.` Result: `{"item_id": N, "changed": [keys], "definition_changed": B}`.

### 4.3 `equip_item` (#288)

Extra param: optional `slot` (string). Target must not already be equipped → `DoorError('already-equipped', …)`.

**Extraction first:** lift the candidate computation from `cmd_equip` (`consumers.py:1537-1560`) into a pure helper `equip_candidates(definition, equipped_items)` in `item_utils.py`, returning the same `[(slot, displaced_list)]`; move `SLOT_CAPACITY` to `item_utils.py` and import it back into `consumers.py`. `cmd_equip` consumes the helper with **byte-identical player behavior — the existing player-side equip tests must pass unmodified** (any test edit here is a deviation to report).

Door logic:
- `slot` given: must be in `definition.valid_slots` → else `DoorError('bad-slot', listing valid slots)`. Displaced set = that slot's candidates from the helper (occupants per capacity + two-hander extras).
- `slot` absent: run the candidates. A displacement-free slot wins outright. Else take the minimal-displacement candidates exactly as `cmd_equip` does; if the distinct displaced items number more than one, refuse with `DoorError('ambiguous', detail naming each option as slot + displaced item name + item id)` — structured enough for the bot to ask the admin or retry with `slot`.
- Perform: unequip each displaced item (flags only — **protective guards bypassed admin-style**, the `_strip` precedent: cursed comes off, capacity ignored), then equip the target (`is_equipped=True`, `equipped_slot`, **re-soulbind: `is_soulbound=True`, `soulbound_to=char`** — byte-consistent with `equip_item`/`_dress`), then **one** `rescale_bars_for_gear(char)`.
- **Structural rules always hold** (valid slots, capacity, two-hander geometry); only protective guards yield. `outfit_snapshot` is never read, written, or consumed.
- Narration: `An admin has equipped {item_ref} on you.` — `event='refresh_status'`. Result: `{"item_id": N, "slot": "...", "displaced": [ids]}`.

### 4.4 `unequip_item` (#288)

Target must be equipped → else `DoorError('not-equipped', …)`. Flags off, `rescale_bars_for_gear`, **no protective guards** (cursed comes off; over-capacity accepted — the #275 acceptance). Curse *effects* untouched — unequip is not removal. `outfit_snapshot` untouched. Narration: `An admin has unequipped {item_ref}; it is in your inventory.` — `event='refresh_status'`. Result: `{"item_id": N}`.

## 5. Game-side tests (`tests/test_mc_agent_door.py`, extend in place)

Follow the file's existing fake/driver patterns. Required coverage, minimum:

- `inventory`: roster includes equipped **and** carried, flags correct; uncapped (seed > 50 items, all present); unknown character → `not-found`; empty inventory → `count: 0`.
- `item`: full-fidelity fields incl. curse/identification true state; ownerless (room-floor) instance carries `owner: null` + room; unknown id → `not-found`.
- Shared addressing: wrong-owner id → `not-owner` on every write kind; malformed params → `bad-params`.
- `remove_item`: ordinary → instance gone, definition survives; artifact → definition + instance gone, **re-creating the same name via `create_artifact` succeeds** (the freed-name law); equipped target → bars rescale (assert via the bar-law helpers the existing tests use); cursed target → `EffectInstance` and components deactivated with `removed_by='item-removed'`; narration line + `refresh_status` event to an online holder; silent offline.
- `edit_item`: `mk_tier` raw-set lands; unknown key refuses whole (no partial write — assert untouched fields); definition-side key on non-artifact → `not-artifact`; artifact rename → name+slug change, collision → `name-taken`, self-rename to same name allowed; `durability_current` 0 sets `is_broken`; equipped target edit rescales bars.
- `equip_item`: free-slot auto; explicit slot; invalid slot → `bad-slot`; ambiguous (two rings) → `ambiguous` naming both; displacement of a cursed equipped item succeeds (protective bypass); two-hander displaces both hands; re-soulbind asserted; `outfit_snapshot` unchanged by the action; `already-equipped` path.
- `unequip_item`: happy path; cursed comes off; `not-equipped` path; snapshot untouched.
- One test asserting the kill switch refuses the new kinds (the consumer-level gate covers them — prove it).
- Player-side regression: the full existing suite green — the `cmd_equip` extraction is behavior-neutral.

**In-container invocation (the only working form):** `python manage.py test apps/shyland/tests` via `docker exec` in the django container.

## 6. Bot-side

### 6.1 `agents/sudo_bot.py` — #292 + new tools

- **#292:** normalize once at config time in `cmd_run`: `base_url = args.url.rstrip('/')` before the config object is built — covers login and WebSocket URLs in one line. In `django_login`'s refused branch, append the response's `Location` header (when present) to the `login refused (HTTP 302)` warning. Log lines stay UTC-stamped with trailing `Z` (standing project rule).
- **New tools:** add the six kinds to the `QUERY_KINDS`/`ACTION_KINDS` frozensets and six `TOOLS` entries (tool name = door kind, exactly like the existing eleven; schemas mirror §3–§4 param shapes). `_execute_tool` needs no change (verified generic).
- **System prompt:** extend in the file's existing style (authored at implementation, creative policy) to state the new powers plus two behavioral laws: **resolve items via `inventory` (and `item` where detail matters) before proposing any item write** — never guess an id; and **destructive/mutating actions act only on an explicitly admin-named target** — when resolution is ambiguous, ask, don't pick.

### 6.2 `agents/mc_door_agent.py`

Append the six kinds to the `QUERY_KINDS`/`ACTION_KINDS` tuples (lines 72-74). No other change — the REPL is generic.

### 6.3 `agents/botctl.py` — #295 (new file)

Stdlib-only Python (`argparse`, `pathlib`, `subprocess`, `os`, `signal`, `time`), list-argv, never `shell=True`, `#!/usr/bin/env python3`, executable bit, **compatible with the system `python3` (3.9)** — no venv dependency in the manager itself (it is the tool that reports a missing venv). UTC-Z timestamps on anything it logs/prints with a timestamp.

- **Self-locating:** repo root = `Path(__file__).resolve().parent.parent`. The copy you run is the checkout it manages — main checkout for prod, the current version worktree for dev. No baked-in absolute paths anywhere.
- **CLI:** `botctl.py <prod|dev> <start|stop|restart|status|tail> [--bot NAME]` (default `sudo`).
  - `prod` → `--url https://games.magrathea.com`
  - `dev` → `--url https://emma.private.magrathea.com` **plus `--insecure`** (dev's self-signed certs; the prod path can never receive it)
  - Both URLs in one documented constants block; the script additionally `rstrip('/')`s whatever it passes (belt and suspenders with #292).
- **Derived per `--bot`:** module `agents/<name>_bot.py`, log `agents/<name>_bot.log`, key file `agents/.secrets/anthropic-api-key.<name>`. Missing bot module or key file → clear error, nonzero exit. Missing venv (`agents/venvs/mc-agent/bin/python`) → clear error naming the fix (`python3 -m venv agents/venvs/mc-agent && … pip install -r agents/requirements.txt`), **never an auto-install**.
- **`start`:** read the key file, place it in the child environment only (never argv, never echoed, never logged); spawn the venv python on the bot module's `run` subcommand detached (`start_new_session=True`, stdout/stderr → the log file, cwd = repo root); poll the bot's `status` subcommand briefly (bounded retries, ~10 s) and finish with a short log tail. Exit 0 only when status reports running.
- **`stop`:** invoke the bot's `stop`; poll `status` until down (bounded); tail; propagate failure as nonzero.
- **`restart`:** `stop` then `start`, each gated on its status poll — no blind sleeps.
- **`status`:** pass through the bot's `status`, propagate its exit code.
- **`tail`:** follow the log (`tail -f` via subprocess is acceptable here, or a Python follow loop — implementer's choice).
- Committed file contains no secret values. The operator's `$HOME` wrappers (`sudo-bot.sh`, `test-sudo-bot.sh`) are **retired by the operator, not by this session** — never delete or edit files outside the repo.

## 7. Verification

1. Full in-container suite green: `python manage.py test apps/shyland/tests` (path form, `docker exec`).
2. `make deploy-dev` (standing requirement — build + migrate against the local dev stack; the migrate is a no-op by design: this brief ships no migration).
3. Driver spot-checks against dev as the standing test agent: `mc_door_agent.py` — `query inventory`, `query item`, one `remove_item` and one `edit_item` round-trip on a seeded test character; confirm each draws an MC record attributed to the agent account (the consumer-side capture).
4. `botctl.py dev status` / `start` / `status` / `stop` cycle clean; exit codes propagate (`echo $?` checks).

All verification must pass before the issues close and before any push that claims completion.

## 8. Operator playtest checklist (dev stack)

After `make deploy-dev` and `botctl.py dev start`:

1. **Inventory read:** `sudo show me <char>'s inventory` — roster arrives with equipped items flagged; matches the character's actual state including worn gear.
2. **Removal:** `sudo take the <ordinary item> from <char>` — item vanishes from `inv`; the player pane shows `An admin has taken the … from you.`
3. **Artifact round-trip:** author an artifact via sudo; remove it; re-create under the **same name** — creation succeeds (name freed).
4. **Mutation:** `sudo raise <char>'s <item> to Mk 3` — `inv` shows the new tier; edit an **equipped** item and watch the bars rescale in the pane.
5. **Targeted equip/unequip:** equip a specific carried item; unequip one item; with both ring slots full, ask for a third ring — the bot relays the choice instead of guessing, and an explicit follow-up resolves it.
6. **Cursed item:** via the Django admin, set `is_cursed=True` on an equipped instance (deliberate admin-form data setup, not a guard test); player `unequip` refuses; `sudo` unequip succeeds; then `sudo` removal of the cursed item completes clean.
7. **Snapshot orthogonality:** `strip` a character, targeted-equip one item, then `dress` — no crash; the already-equipped item lands in the dress result's `missing` list; the rest restores.
8. **#292:** stop the bot; start it with a **trailing-slash** dev URL (bypass botctl once, invoking the bot directly) — login succeeds.
9. **botctl:** `restart`, `status`, `tail` behave; `status` exit code is honest.

## 9. PENDING DEPLOY-TIME ACTIONS

**None.** No migration, no seed, no production-side data action. Production receives this release as code alone at the closeout tail's `make deploy-prod`. (Prod bot restart after deploy is the operator's standing action, outside this brief's scope.)

## 10. Architecture doc (last, gated)

**This step is gated on all implementation and verification steps above being complete and passing.** Update `docs/shyland/Shyland_Architecture_v25.md` **in place**: stamp `25.7`; **the hash moves** (this is an architectural change — new door vocabulary). Sections to update: the MC door section (query vocabulary + the four actions, param/result shapes, the not-owner/ambiguous/not-artifact error codes, the structural-vs-protective guard law, curse-ends-with-item), the agents/ops section (`botctl.py`, the self-locating law, the prod/dev targets), and the sudo bot section (URL normalization, the six new tools).

## 11. Closeout

Closeout report (`.txt` in `docs/shyland/`, completing the Step-0 stub in place): final commit hash, the **operator playtest disposition** verbatim-style (#170), deviations (including any test-hygiene changes — e.g. if the `cmd_equip` extraction forces any test edit, report it; none is expected), and confirmation that #287, #288, #289, #292, #293, #295 closed gated on verification. Then: run the issues report.

Standing rules bind throughout: commit and push at every step boundary (branch only — never merge to main); no removal/pruning of transient documents; heredocs never; multi-line bodies via file + `--body-file`.
