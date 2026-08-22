# Shyland V25.5 — Brief 1: The Agent Door

**Release:** Version 25.5 (point release under the V25 MC major)
**Founding ticket:** #281 · **Dependency (closes with the release):** #273
**Branch:** `version_25_5` · **Written & committed by:** the V25.5 design session, 2026-08-22
**Ruling record:** issues #261, #262, #273, #281 (comments dated 2026-08-22); GDD text landed at `ed0a4b9` with `(v25.5, #281, pending implementation)` markers.

**Technical coherence (#252):** every structural claim in this brief about existing code was verified against the code on this branch at writing time — by direct read of `mc_consumer.py` (whole file), `mc.py` (emit helpers), `forms.py` (whole file), `consumers.py` (lines 501–531, 557–568, 717–760, 772–861, 3560–3620, 3698–3702, 4474–4499), `item_utils.py` (lines 55–170), `game.html` (`:root` palette, `.msg-*` rules at 130–190, `FLAG_RE` at 917, `UNSTAMPED_CATEGORIES` at 898), and by located-and-quoted reads of `models.py` (Character 238–322, MCKillSwitch 1264–1305, ItemDefinition 413–544, ItemInstance 547–659), `test_b2_amendment4.py` (25–99), `routing.py`, and `verification.py`. Line numbers cited below are from this verification pass; if any load-bearing claim mismatches the code at implementation time, that is a **HARD STOP** back to the operator (#252).

---

## 1. What this release ships

The game-side half of the first-actor arc: the MC endpoint (`ws/shyland/mc/`, `MCEgressConsumer`) grows from a read-only tail into **the agent door** — three inbound vocabularies (**tail** / **query** / **action**) on one authenticated connection per bot. V25.6 ships the sudo bot itself (#262); after this release it has zero game-side blockers. Everything here is deterministically drivable by the operator's test agent (`agent-smith`) with no AI in the loop.

**Not in this release:** any bot process, model integration, or conversation logic (25.6); per-agent authorization scopes and rate governance beyond what §4 states (the #261/#268 arcs); effect-carrying artifacts (§5.4); the `wall` command (#236, its own future release).

## 2. Standing requirements (never omit)

1. **Version constant — opening act.** This is the FIRST implementation brief of the release: bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` (line 8, currently `"25.4"`) to `"25.5-DEV"` in its own commit, moving the pin-test assertion in the same commit; then run the version-start `make deploy-dev` from the worktree.
2. **In-session dev deploy:** exactly `make deploy-dev` from the worktree once implementation and verification pass (again, at the end).
3. **Operator playtest checklist:** §9, targeting the dev stack.
4. Push at every step boundary; branch only; never merge to main.

## 3. Design rules — binding, do not deviate

- **The trust boundary does not move.** Agents reach the game only through the door: Django session auth, WSS through nginx, live `agents.shyland` membership at connect (shipped, `mc_consumer.py:128-133`). Agents never hold a DB or Redis credential. Redis and Postgres continue to publish no ports.
- **No player door, no characters.** Agent accounts (`agent-<name>`) never own a `Character`. Nothing in this brief touches `SkylandConsumer.connect`.
- **Kill switch covers the whole door.** Every query and action frame checks `switch_killed()` fresh before processing (the `mc_consumer.py:82-89` helper — fail closed); killed ⇒ `close(code=4503)`, same as the tail sever. Capture never checks the switch (standing law).
- **Additive, never load-bearing.** No game mechanic may depend on anything arriving through the door. MC emits remain fire-and-forget.
- **Everything on the record.** Every processed query/action emits an MC record (§6). Every player-visible effect line is captured at creation like any other out record. Nothing changes the world off the record.
- **Transparency (ruled 2026-08-22, #261):** effect narration tells the truth (`An admin ...`) in the world's standard colors. Bots talk in their talking color only.
- **Soulbind law:** admin gifts soulbind immediately (`gift=True` — `item_utils.py:153-154`; this brief adds the first production caller).
- **Append-only record; the switch is config** — both v25.4 rules untouched.
- **Bar law:** every equip/unequip mutation runs the gear rescale (`_rescale_bars_for_gear`, `consumers.py:4474`) — strip/dress included.

## 4. The wire contract (authoritative; tables win over prose)

`MC_PROTOCOL` bumps **1 → 2** (`mc_consumer.py:26`). Inbound vocabulary: `attach`, `ping` (both byte-identical to v25.3), plus `query` and `action`. Any other frame type now draws `{"type": "error", "error": "unknown-frame"}` (replacing v25.3's `read-only` string — update `test_mc_egress.py`'s pin accordingly and note it as the ruled supersession, not drift). Frames are processed serially per connection (Channels delivers `receive_json` sequentially) — that serialization is the day-one rate discipline, recorded deliberately; per-agent scopes and limits are #261/#268 arc work.

**Request frames:**

```json
{"type": "query",  "id": "<client string ≤64>", "q":   "<kind>", "params": {...}}
{"type": "action", "id": "<client string ≤64>", "act": "<kind>", "params": {...}}
```

**Response frame (both):**

```json
{"type": "result", "id": "<echoed>", "ok": true,  "data": {...}}
{"type": "result", "id": "<echoed>", "ok": false, "error": "<code>", "detail": "<human sentence>"}
```

Missing/non-string `id` ⇒ result with `"id": null`, `ok: false`, `error: "bad-frame"`. Unknown `q`/`act` ⇒ `unknown-query` / `unknown-action`. Malformed params ⇒ `bad-params`. All character-name params resolve case-insensitively (`name__iexact`); no match ⇒ `not-found`.

### 4.1 Query kinds

| `q` | params | `data` on success |
|---|---|---|
| `commands` | `{}` | `{"verbs": [...], "admin_verbs": [...]}` — sorted; derived exactly as connect does it (`consumers.py:579-581`): `set(DIRECTIONS) \| set(SkylandConsumer.COMMAND_TABLE)`, with `ADMIN_VERBS` listed separately (agents see the full vocabulary; the split lets a bot model stealth) |
| `who_online` | `{}` | `{"characters": [{"id": <pk>, "name": "..."}]}` — from `shyland:online:*` presence keys (`consumers.py:558-566`), pks parsed from key names, names via the `parse_presence_name` tolerance (`consumers.py:221-228`) |
| `where_is` | `{"name": "..."}` | `{"id", "name", "online": bool, "room": {"id", "name", "area": <name or null>, "zone": <name>} \| null}` — room null when `current_room` is null |
| `character` | `{"name": "..."}` | `{"id", "name", "level", "xp", "origin", "archetype", "stats_base": {str,dex,end,int,wis,per}, "stats_effective": {...same keys...}, "vitality": [cur, max], "acuity": cur, "longevity": [cur, max], "copper", "unspent_stat_points", "online": bool, "room": {...as where_is...}}` — effective via `combat_utils.effective_stats` (`combat_utils.py:130`) |
| `items` | `{"contains": "<substr, optional>"}` | `{"definitions": [{"id", "slug", "name", "item_type", "valid_slots", "is_two_handed", "tier_material_mk_min", "tier_material_mk_max"}]}` — name icontains filter, ordered by name, capped 50 rows (report the cap in `data` as `"truncated": bool`) |
| `is_admin` | `{"name": "..."}` | `{"is_admin": bool}` — character → `user.groups.filter(name='admins.shyland').exists()`, live (#273) |

### 4.2 Action kinds

| `act` | params | Behavior (server-validated, in order) | Errors |
|---|---|---|---|
| `answer` | `{"to": "<char name>", "text": "<≤2000>"}` | Resolve target; **require target's user in `admins.shyland` (live)** — the #273 delivery gate, authoritative regardless of what the bot concluded; if the presence key `shyland:online:{pk}` exists, deliver `sudo: {text}` as category **`sudo`** via the door's audited send (§6) to group `player_{pk}`; result `{"delivered": true/false}` — offline is `ok: true, delivered: false`, never an error (silence is the norm) | `not-found`, `not-admin` |
| `gift` | `{"to", "slug", "mk_tier": int, "rarity"}` | Definition by slug; `rarity` must be in `RARITY_CHOICES` minus `artifact`; `generate_item_instance(definition, mk_tier, rarity, owner=char, gift=True)` then `.save()` (the Mk-mismatch guard raises `ValueError` → `invalid-item` with its message as detail). **Capacity is deliberately not checked** — an admin gift lands regardless of carry state (recorded design point). If recipient online: giving line (§5.2) | `not-found`, `bad-params`, `artifact-requires-create`, `invalid-item` |
| `create_artifact` | `{"to", "spec": {...}}` — §5.4 table | Validate spec; create the hand-authored `ItemDefinition` + the artifact `ItemInstance` (never through `generate_item_instance` — forbidden for artifacts, `item_utils.py:99`), `is_soulbound=True`, `soulbound_to=char`, `owner=char`; giving line as gift | `not-found`, `bad-params`, `name-taken` |
| `strip` | `{"name"}` | Equipped set = `char.inventory.filter(is_equipped=True)`; none ⇒ `nothing-equipped`. Write `outfit_snapshot = [{"instance_id": pk, "slot": equipped_slot}, ...]` **before** any unequip; then per item: `is_equipped=False`, `equipped_slot=''`, save — bypassing `_unequip_blocked_reason` **deliberately** (admin tool; the operator accepts the resulting #275 over-capacity state knowingly, ruled 2026-08-22); one gear rescale after the loop (§7 extraction). If online: narration §5.3 + status refresh. Result `{"stripped": N}` | `not-found`, `nothing-equipped` |
| `dress` | `{"name"}` | Snapshot absent/empty ⇒ `no-outfit`. For each entry whose instance still exists, is owned by the character, and is not equipped: `is_equipped=True`, `equipped_slot=<snapshot slot>`, `is_soulbound=True`, `soulbound_to=char` (byte-consistent with `equip_item`, `consumers.py:4486-4492`), save; one rescale after the loop. **The snapshot is always consumed** (set to null) by a dress attempt, whatever the outcome. Result `{"restored": N, "missing": [ids]}`. If online: narration §5.3 + status refresh | `not-found`, `no-outfit` |
| `move` | `{"name", "to_name"}` or `{"name", "to_room_id"}` (exactly one destination) | Resolve destination room (`to_name` → that character's `current_room`, null ⇒ `not-found`); **refuse if the target is in an active combat session** (`in-combat` — no landmines in the combat model); update `current_room`, record the visit (arrival law — §7 extraction of `record_room_visit`'s body, `consumers.py:4221-4230`); if target online: origin-room broadcast `{name} has left.` / destination `{name} has arrived.` (the `cmd_move` shapes, `consumers.py:806-828`, emitted through the door's audited group send) and a `player_message` event `moved` handled by a new consumer branch modeled on the respawn branch (`consumers.py:3603-3617`: group discard/add, visit, `send_room_description(entering=True)`, zone-completion announce, `send_map`) plus the player line §5.3. Offline: DB update + visit only, no broadcasts | `not-found`, `in-combat`, `bad-params` |

## 5. Rendering and content

### 5.1 The sudo category and color

- `game.html` `:root` gains `--sudo-color: #E24B4A;` (error-color's hex under a separable name — the documented `--error`/`--agro-color` reuse pattern at `game.html:32-35`).
- New rule `.msg-sudo { color: var(--sudo-color); }` beside the voice rules (`game.html:145-170`).
- **Palette conformance:** `#E24B4A` is already licensed, and `ALLOWED_COLORS` is a set — `test_b2_amendment4.py:84-99` passes with **no allowlist edit**. Add instead a pin test asserting the `--sudo-color` variable and `.msg-sudo` rule exist (the chart row is GDD-landed; the license must be visible in the test layer).
- `sudo` is **not** added to `UNSTAMPED_CATEGORIES` (`game.html:898`) — answers are events and carry the timestamp prefix.
- Server side composes the attribution: the delivered text is `sudo: {text}` (words carry identity; color reinforces).

### 5.2 The giving line (gift and create_artifact), category `reward` (loot-color)

> `An admin has given you {item_ref(item)}.`

using `item_utils.item_ref` (`item_utils.py:201`) — the DD §6 transactional family shape, deliberately not the listing composition (#148's lesson).

### 5.3 Effect narration (category `system` — value-color, `game.html:168`)

| Event | Line to the affected player |
|---|---|
| move | `An admin moved you to a new room.` (operator-authored, verbatim) |
| strip | `An admin has unequipped your gear; it is in your inventory.` |
| dress | `An admin has re-equipped your gear.` |

Room broadcasts for move reuse the standard `has left.` / `has arrived.` sentences. No other narration is authored by this brief.

### 5.4 The artifact spec (`create_artifact.params.spec`) — table authoritative

| Key | Required | Type / constraint |
|---|---|---|
| `name` | yes | ≤200 chars; must not match any existing `ItemDefinition.name` case-insensitively (`name-taken`) — artifacts are one-of-a-kind; must not begin with a rarity word (the seed authoring law, `seed_world.py:3157-3168`, enforced here at runtime) |
| `item_type` | yes | one of `ITEM_TYPE_CHOICES` (`models.py:414-431`) |
| `description` | yes | non-empty text (the lore from the Q&A) |
| `genre_tag` | yes | one of `GENRE_TAG_CHOICES` (`models.py:433-446`) |
| `mk_tier` | yes | int ≥ 1 |
| `base_value` | yes | int ≥ 0 (value law applies: × mk × artifact multiplier 32, `item_utils.py:49-58`) |
| `valid_slots` | equippables | list of slot codes from `SLOT_DISPLAY_NAMES` (`item_utils.py:6-21`); required non-empty for `weapon`/`armor`/`accessory`/`bag`, else `[]` |
| `is_two_handed` | no | bool, default false |
| `damage_midpoint` / `damage_spread` | weapons | floats — stored on the **instance** (`models.py:590-591`) |
| `armor_base` | armor | float ≥ 0, default 0 — stored on the **definition** (`models.py:467-473`) |
| `primary_stats` / `secondary_stats` | no | lists of `{"stat": "<key>", "value": <int>}` — **exactly the rolled-entry shape generation produces** (`item_utils.py:126-143`), stored verbatim in `rolled_primary_stats` / `rolled_secondary_stats`; optional `"floor"` int per primary entry |
| `is_unidentifiable` | no | bool, default false (`models.py:624-631` — the mystery-artifact flag) |
| `mystery_name` / `mystery_description` | no | strings, default '' — required together with `is_unidentifiable: true` |

Definition rows are created with `scaling_base=0.0, scaling_factor=0.0` (required floats, meaningless for hand-authored stats — documented in the builder), `suppress_mk_suffix=False`, `slug` slugified from name (collision ⇒ `name-taken`). **`effect` wiring is excluded from the day-one spec** — deliberate scope, not an oversight; an effect-carrying artifact is a future slice.

## 6. MC capture of door activity

Two new record kinds, emitted (fire-and-forget, `mc.mc_emit`) after each processed frame:

- `agent_query` — `data = {"q", "params", "ok", "error": <code or omitted>}`
- `agent_action` — `data = {"act", "params", "ok", "error": <code or omitted>, "result": <the result data object>}`

Envelope discipline (matches the combat family's NPC convention): `actor_id` empty, `actor_name` = the agent's username (e.g. `agent-smith`), `room_id` empty, `audience` empty. The v25.3 "egress connections are not captured" rule (`mc_consumer.py:11-12`) survives for attach/detach/tail; queries and actions are game-facing activity and are on the record.

Player-visible lines the door causes are creation-level `out` records: the door module implements one **audited send helper** — emit the `out` record (audience = the target pks), then `channel_layer.group_send` — mirroring the `mc_group_send` choke-point discipline (`consumers.py:454-487`). No bare `group_send` anywhere in door code.

## 7. Implementation steps

1. **Version bump** (§2.1) + version-start `make deploy-dev`.
2. **Migration 0053:** `Character.outfit_snapshot = models.JSONField(null=True, blank=True, default=None)` — `make makemigrations APP=shyland && make migrate`. Commit the migration file.
3. **Shared-machinery extraction** (behavior byte-identical, existing tests stay green):
   - `_rescale_bars_for_gear` (`consumers.py:4474-4483`) body → a module-level function (natural home: `item_utils.py` or `combat_utils.py`); the consumer method and the door both call it.
   - `record_room_visit`'s body (`consumers.py:4221-4230`) → a module-level sync function returning `(first_visit, zone_completed)`; consumer wrapper and door share it.
4. **`mc_door.py` (new):** sync DB functions for every query and action in §4 (called from the consumer via `database_sync_to_async`), the audited send helper (§6), the artifact builder (§5.4), narration senders (§5.2/5.3). Import direction: `mc_door` may import from `consumers`/`item_utils`/`models`/`mc`; nothing imports `mc_door` except `mc_consumer`.
5. **`mc_consumer.py`:** `MC_PROTOCOL = 2`; `receive_json` dispatches `query`/`action` (kill-switch check first, per frame); unknown-frame error string; module docstring updated (the read-only law narrows to the tail — record the supersession in the docstring).
6. **`consumers.py`:** the `moved` branch in `player_message` (modeled on respawn, §4.2 move row).
7. **Name reservation:** `RESERVED_BOT_NAMES = frozenset({'sudo', 'sirius'})` (in `models.py` near the Character model); `CharacterCreationForm.clean_name` (`forms.py:20-40`) gains, beside the NPC check, `if name.lower() in RESERVED_BOT_NAMES:` → the same `'That name belongs to the world already.'` message (no-leak: bots and NPCs indistinguishable in refusal). Verify at implementation time no existing `Character` or `NpcDefinition` holds either name (`iexact` query in the test).
8. **Client (`game.html`):** `--sudo-color` + `.msg-sudo` (§5.1).
9. **Dev agent account:** ensure `agent-smith` exists on the dev stack in `agents.shyland` (create via shell if absent; operator sets the password; credentials never recorded anywhere).
10. **Tests (§8), verification (§8), `make deploy-dev`, playtest (§9).**
11. **Issues:** close #281 and #273 with verification-passed comments — gated on §8 passing.
12. **Architecture doc — last, gated** (§10).

## 8. Tests and verification

New module `tests/test_mc_agent_door.py` (patterns: `test_mc_egress.py` / `test_mc_kill_switch.py` communicator + fake-stream fixtures). Required coverage, minimum:

- Protocol: unknown frame → `unknown-frame`; bad `id` → `bad-frame`; unknown `q`/`act`; non-member 4403 unchanged; **killed switch: query and action frames each ⇒ close 4503** (fresh-read, fail-closed).
- Every query kind: happy path + `not-found`; `commands` equals the connect-time derivation exactly; `is_admin` flips live with group membership.
- `answer`: admin-gate (`not-admin` for a non-admin target); online delivery produces category `sudo`, text `sudo: ...`; offline → `delivered: false`; MC `out` + `agent_action` records emitted.
- `gift`: soulbound-to-recipient instance created; `artifact` rarity refused with `artifact-requires-create`; Mk-mismatch `ValueError` surfaces as `invalid-item`; works with recipient over capacity.
- `create_artifact`: spec validation (each required key), `name-taken` (case-insensitive), rarity-word name refusal, instance is `rarity='artifact'`, soulbound, sellable=no (existing artifact sell-refusal paths cover it — assert via the sell guard).
- `strip`/`dress`: snapshot written before unequip; round-trip restores exact slots; fill-fraction invariance across both (bar law); snapshot consumed by dress; `missing` reporting when an item was disposed between; `nothing-equipped`/`no-outfit`.
- `move`: online (groups re-seated, visit recorded, narration + broadcasts) and offline (DB + visit only); `in-combat` refusal; `to_room_id` form.
- Name reservation: `sudo`/`Sudo`/`sirius` refused at the form; existing-collision assertion (§7.7).
- Pin: `--sudo-color` var + `.msg-sudo` rule present; `MC_PROTOCOL == 2`.

**In-container invocation (the only working form):** `python manage.py test apps/shyland/tests` via `docker exec` in the django container. Full suite green (768 + this brief's additions); record the new count in the closeout.

## 9. Operator playtest checklist (dev stack, after `make deploy-dev`)

Driver: the operator-side harness in `~/src/games-mvc-agents/` (its query/action extension is operator tooling per #268/#279 — a minimal send-frame loop over the §4 contract; not repo code in this release).

1. Attach as `agent-smith` — `hello` reports `protocol: 2`; tail still streams.
2. `query commands` — verb list matches `help` (admin verbs present, listed separately).
3. `query who_online` / `where_is` / `character` against your logged-in character — values match `who`/`stats`.
4. `action answer` to your admin character — pane shows `sudo: <text>` in the error-red voice, timestamped; to a non-admin character → `not-admin`; log out and answer → `delivered: false`, nothing when you return.
5. `action gift` (existing definition, e.g. an Iron Mace at Mk 1 uncommon) — giving line in loot-color; item arrives `[<Rarity>, Bound]`.
6. `action create_artifact` with a full spec — arrives Bound, `[Artifact, Bound]` flag; vendor refuses to buy it.
7. `action strip` on your character — gear lands in inventory, bars keep their fill fraction, capacity drops (over-capacity acquisition refusals appear — expected, #275 accepted); `action dress` — exact restoration, status pane recovers.
8. `action move` between your and a second character's rooms, both directions — mover sees `An admin moved you to a new room.` + full room render + map; rooms see left/arrived lines.
9. **Kill-switch loop:** `mc kill` in the game client — the harness connection severs 4503; reconnect refused 4503; queries/actions refused; `mc restore` — everything resumes. (The v25.4 tail behavior plus the new vocabularies.)
10. MC record check (in-container redis-cli or the persister's table): `agent_query`/`agent_action` records attributed to `agent-smith`; the answer's `out` record with your pk as audience.

## 10. Architecture doc — last, gated

This step is gated on all implementation and verification steps above being complete and passing. `Shyland_Architecture_v25.md` updated in place: stamp → **25.5**, **header hash moves** (architectural change). Sections: §4.20 (egress) — the door vocabularies, protocol 2, frame contract summary; a new subsection for `mc_door.py` (queries, actions, audited send, artifact builder); §4.1 models pointer (outfit_snapshot, RESERVED_BOT_NAMES); §4.21 kill switch — coverage extension over query/action; the client-template section — `--sudo-color`/`.msg-sudo`; suite count updated.

## 11. Closeout

Closeout report `docs/shyland/Shyland_V25.5_Brief_1_Closeout.txt` (stub committed at Step 0, completed in place): deviations, final commit hash, new suite count, **operator playtest disposition** (#170 wording), PENDING DEPLOY-TIME ACTIONS block.

**PENDING DEPLOY-TIME ACTIONS: none.** Migration 0053 rides the ordinary closeout-tail `make deploy-prod`. No seed change, no data action. Production agent accounts are **not** created in this release — that is the 25.6 attach window, operator-performed (executor: the operator, when 25.6 directs it).
