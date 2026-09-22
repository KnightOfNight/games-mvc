# Shyland V26.3 — Brief 1: Curses in the World

**Release:** Version 26.3 (milestone `Version 26.3`) · **Branch:** `version_26_3` · **Founding ticket:** #297 (Release B of the curse arc — closes when its full title is true: curses work, in the world) · **Dependency:** #338 (out-of-combat DoTs race passive regen — closes with this release)

**Design record:** the #297 Q1–Q7 rulings (2026-09-11), the Q6 amendment (the presence sweep), the V26.2 ground-truth note (Ridge-only Rare+), and the V26.3 design session's five rulings of 2026-09-22 (agenda items 2–6 on #297; the dot-vs-regen ruling 1a–1g on #338). GDD text landed on this branch at `8306b8a` (§4.1 regen pause; §6.7 Knowledge/Removal/Acquisition rewritten; §6.9 vocabulary row; §6.12/§6.14 service NPCs; §2.10/§2.11; §5 status table; §9.1 chart rows, gating, pools) — all marked "(v26.3, pending implementation)". This brief is self-contained; the GDD sections are the design reference, the issues carry the ruling history.

**Technical coherence (#252):** every structural claim in this brief about existing code was verified against the code on this branch (tip `8306b8a`; the code is byte-identical to main `c1c4f2b` — the branch has only the GDD commit) at writing time by direct file reads. Claims are cited `file:line` as of that commit. The pre-flight diff (below) re-verifies the load-bearing ones.

---

## 1. Scope

Ships Release B — curses live in the world, with the remediation that makes catching one fair:

- **The `cleanse` service**: `cleanse <item>` at a cleanser NPC lifts a live curse from an equipped item for a price authored on the curse and scaled by the item's Mk; always succeeds; routes through the one teardown.
- **The `inspect` presence sweep**: a separate paid sweep of everything carried, 5 copper per item, naming every cursed instance (presence only) or the all-clear.
- **Cleansers**: `NpcDefinition.is_cleanser`; Mother Tansy (Convergence) and the three Z01 checkpoint Menders gain the specialty.
- **`examine` shows the cleansing price** once the curse is identified.
- **Live acquisition**: `CURSE_WILD_CHANCE` goes from `0.0` to `1/3`. Ridge bosses only, as seeded (blessed by ruling — no loot-table changes).
- **The #338 regen pause**: an active `dot_vitality` pauses passive vitality regen (bar-scoped, source-blind, silent).

**Out of scope (by ruling):** a `cleanse all` form; any pre-equip curse defusing; chapter-1 loot-table rarity changes; Sirius (#259); the agent door's item read (the door's `item` query at `mc_door.py:373–381` already carries the curse fields and is **not** touched — `cleanse_price` is player-facing via `examine` only); #336 (the next V26 point release).

---

## 2. Pre-flight

**Process assumptions:** standard v40 rituals (interactive playtest delivery, one step at a time) — no deviations known. **Prior PENDING DEPLOY-TIME ACTIONS: none open.** V26.2's block (migration `0059` + the curse seed) executed at the V26.2 closeout tail on 2026-09-16; no committed artifact recorded that execution, so the operator verified production directly on 2026-09-22 (Django admin: all eight curse Effect definitions present) — attestation recorded on #297 (2026-09-22). The implementation session's pre-flight line cites that comment; no re-confirmation needed.

**Load-bearing technical claims — verified at writing time, re-verify before implementing (mismatch = HARD STOP per #252):**

| # | Claim | Where verified |
|---|---|---|
| T1 | `CURSE_WILD_CHANCE = 0.0` (`item_utils.py:100`) and `CURSE_RARITY_GATE = ('rare', 'epic', 'legendary')` (`:104`); the wild branch in `generate_item_instance` is `elif (definition.is_cursed_template and rarity in CURSE_RARITY_GATE and random.random() < CURSE_WILD_CHANCE): latent_curse = _roll_curse_from_pool(definition)` (`:194–197`); `_roll_curse_from_pool` at `:216` | as cited |
| T2 | `curse_utils.end_curse(item, cause)` (`curse_utils.py:33`) is the one teardown: deactivates component instances + instance with `removed_by=cause`, reverses stat cuts and bar cuts, clears `is_cursed`/`latent_curse`/`active_curse`, stamps `memorial_description`, leaves `curse_identified`; its docstring lists causes `'timeout'`, `'curse-death'`, `'item-removed'`. `spring_curse` at `:15` | as cited |
| T3 | `EffectDefinition` fields: `name`, `slug`, `description`, `is_curse` (`models.py:389`), `apply_text` (`:390`), `memorial_text` (`:393`) — no price field exists. `NpcDefinition.is_repairer` is `BooleanField(default=False, help_text=...)` at `:974–978`, `is_fixture` `:979`, `attackable` `:984`. `Character.copper` is a `BigIntegerField` (`:277`). Latest migration is `0059_effectcomponent_magnitude2_base_and_more.py` | as cited |
| T4 | `ItemInstance` curse state: `is_cursed` (`:777`), `curse_identified` (`:778`), `active_curse` FK (`:779`), `latent_curse` FK (`:788`), `memorial_description` (`:796`) | as cited |
| T5 | Consumer command registry and gates: `COMMAND_TABLE` (`consumers.py:255–295`; entries are `verb: ('cmd_x', takes_args)`), `COMBAT_BLOCKED` dict of verb → authored refusal (`:310–326`), `DYING_ALLOWED` set (`:336–341`; anything absent is refused while dying), `PROMPT_VERBS` (`:347–360`), `GRAMMAR_VERBS` (`:365–373`), `HELP_SECTIONS` (`:1129ff`, tuples `(name, usage, description[, admin])`) | as cited |
| T6 | `cmd_repair` (`:2592`) is the service-routing pattern: `get_repairer_in_room(room)` → `None` → `'There is no one here who can repair.'` warn; `resolve('repair', args, items)`; refusal category via `self._refusal_category(res)`; outcomes through `npc_voice.pick(pool, name=..., cost=self.format_amount(char, cost))`; single-target success interpolates `repairer=npc_display(repairer, capitalize=True)`. `get_repairer_in_room` (`:4585–4595`) filters `NpcInstance(current_room=room, is_alive=True, definition__is_repairer=True).order_by('pk').first()` | as cited |
| T7 | `do_repair_attempt` (`:4691–4715`) is the charge pattern: `transaction.atomic()`, `Character.objects.select_for_update().get(pk=...)`, `char.copper = currency.subtract(char.copper, cost)` with `ValueError` → `('poor', cost)` and nothing saved, then `char.save(update_fields=['copper'])`, and `self.character.copper = char.copper` after. `currency.subtract` at `currency.py:101`; `format_amount(self, character, amount)` at `consumers.py:3686` reads `character.current_room.zone.slug` | as cited |
| T8 | `cmd_unequip` (`:1463`) resolves against `get_equipped_items(char)` (`:4420`, `owner=character, is_equipped=True`); `get_carried_items` (`:4406`, `owner=character` — equipped included); `_completion_candidates` (`:4008ff`) scopes `unequip` to `get_equipped_items` (`:4022`) | as cited |
| T9 | `command_grammar.POLICIES['unequip']` = `Policy(allow_quantifier=False, no_multi=..., not_found="You don't have that equipped.", bad_index="You don't have that many of those equipped.")` (`command_grammar.py:239–244`); `resolve(verb, args, candidates)` at `:390`; `complete` at `:546` | as cited |
| T10 | Examine reveal: `_format_identified_item_lines(self, item, curse_info=None)` (`consumers.py:1886`) renders the curse block at `:1955–1966` from a 3-tuple `(name, remaining, curse_desc)`; `get_curse_examine_info(self, item)` (`:1970`, `@database_sync_to_async`) builds it from `item.active_curse`; the call site is `:2024–2028` | as cited |
| T11 | Tick engine Phase 4 (`run_tick_engine.py:2011`): `get_regen_candidates` (`:2016–2035`) filters not-dying, below-max on either bar, then drops in-combat characters and attaches `char._vitality_hold`; the vitality arm is `:2048–2059` (`heal = ceil(vitality_max / VITALITY_REGEN_SECS)`, hold cap); the longevity arm `:2061–2086`. Phase 2 drift (`:1866–1877`) is the precedent for excluding by active component type (`EffectComponentInstance.objects.filter(effect_instance__target=char, is_active=True, component__component_type__in=...)`) | as cited |
| T12 | Seed: `CONVERGENCE_SERVICE_NPCS = {'morra', 'pella', 'ferwick', 'repairbot-prime'}` (`seed_world.py:2541`), `CONVERGENCE_CART_VENDORS = {'vnd-9', 'mother-tansy'}` (`:2545`); `_seed_convergence_npcs` (`:2602`) sets `'is_repairer': is_service_npc` (`:2706`) and `attackable` false for service NPCs and carts (`:2709`); `_upsert_npc_definitions` (`:7868`) sets `'is_repairer': extras.get('is_repairer', False)` (`:7901`); the Menders' extras `{'is_repairer': True, 'attackable': False, 'article': ''}` at `:7756` (Maro), `:7768` (Tavik), `:8147` (Old Brammel). Verification: vendors/repairers unattackable (`:3130–3136`), "Maro, Tavik, and Old Brammel are repairers" (`:3736–3741`) | as cited |
| T13 | `_seed_curses` (`:4244`): `_component(order, ctype, mag, mag_scale, dur, dur_scale, ...)` helper (`:4253`); the `curses` spec list (`:4276ff`) with slugs `curse-leaden-arm`, `curse-craven-edge`, `curse-copper-tithe`, `curse-moth-eaten-ward`, `curse-whisper-string`, `curse-hollowing`, `curse-gravekeepers-hold`, `curse-threefold-ruin`; the reconcile block (`:4479–4485`) passes `name/description/is_curse/apply_text/memorial_text`; template-flag self-heal (`:4500–4512`) | as cited |
| T14 | `npc_voice.pick(pool, **fields)` (`npc_voice.py:19`); `PITY_REPAIR_LINES` is a per-slug dict of ≥3 lines (`:111`) with `PITY_REPAIR_FALLBACK` (`:169`) using `{name}` | as cited |
| T15 | `SHYLAND_VERSION = "26.2"` (`version.py:8`); pin test asserts `'26.2'` (`tests/test_b2_amendment1.py:122`) | as cited |
| T16 | Loot: chapter-1 boss tables roll `uncommon: 100` (`seed_world.py:7648–7656`); Ridge `weaver-loot`/`king-loot` `rare: 100`, `devourer-loot` `epic: 100` (`:8071–8079`); villagers `{'common': 85, 'uncommon': 15}` (`:7605`, `:8057`); vendor buys generate at `rarity='common'` (V26.2 T7, unchanged) | as cited |

---

## 3. Step 0 + Step 1 — Version start (opening act)

1. Step 0 per the standing ritual: closeout-report stub (`docs/shyland/Shyland_V26.3_Brief_1_Closeout.txt`) committed and pushed.
2. Bump `SHYLAND_VERSION` to `"26.3-DEV"` in `django/src/apps/shyland/version.py`, move the pin test assertion (`tests/test_b2_amendment1.py:122`) to `'26.3-DEV'` in the **same commit** — its own commit.
3. `make deploy-dev` from the worktree (the version-start deploy).

---

## 4. Step 2 — Schema (models + migration)

All in `django/src/apps/shyland/models.py`. Field names are final.

1. **`EffectDefinition.cleanse_price`** — `models.PositiveBigIntegerField(default=0, help_text='v26.3 (#297): copper an NPC cleanser charges to lift this curse from a Mk 1 item; the charge is cleanse_price × the item\'s Mk tier. 0 on non-curses.')`. Place it with the v26.2 curse fields (after `memorial_text`).
2. **`NpcDefinition.is_cleanser`** — `models.BooleanField(default=False, help_text='v26.3 (#297): this NPC lifts item curses and sweeps packs for them. The cleanse and inspect commands route to a living cleanser in the room.')`. Place it directly after `is_repairer`.
3. `make makemigrations APP=shyland` → migration **`0060`** (two `AddField`s). Commit it.
4. Admin (`admin.py`): add `cleanse_price` to the `EffectDefinition` admin's field display beside `is_curse`; add `is_cleanser` beside `is_repairer` on the NPC admin. Read-only convenience; no new admin behavior.

---

## 5. Step 3 — The #338 regen pause (`run_tick_engine.py`, Phase 4)

Per #338 1a–1e. In `get_regen_candidates` (T11), after the in-combat exclusion and beside the `_vitality_hold` read, compute in DB context:

```python
char._vitality_dot_paused = EffectComponentInstance.objects.filter(
    effect_instance__target=char, is_active=True,
    component__component_type='dot_vitality',
).exists()
```

(Import `EffectComponentInstance` alongside the existing imports; the Phase 2 drift exclusion at `:1866–1877` is the shape precedent.) The character **stays in the candidate list** — the longevity arm must still run. In the vitality arm (`:2048`), gate the whole block: `if character.vitality_current < character.vitality_max and not getattr(character, '_vitality_dot_paused', False):`. Nothing else changes:

- Bar-scoped: the longevity arm is untouched; Phase 2 acuity drift is untouched.
- Source-blind: any `dot_vitality` component pauses it — curse, NPC proc, consumable.
- `floor_hold_vitality` does **not** trigger the pause (it is not `dot_vitality`); the hold cap logic stays as is.
- Silent: no message; the changed-fields gate already means a paused vitality-only candidate saves nothing and pushes nothing.
- Hots are effects (Phase 1), not passive regen — unaffected.

---

## 6. Step 4 — The `cleanse` command (`consumers.py`, `command_grammar.py`, `curse_utils.py`, `npc_voice.py`)

Per #297 rulings 2c, 3a–3f, 4a–4c, 4g.

**6.1 Registry (T5).** `COMMAND_TABLE`: `'cleanse': ('cmd_cleanse', True)`. `PROMPT_VERBS`: `'cleanse': 'cleanse'` (bare → `What do you want to cleanse?`, fn 10). `GRAMMAR_VERBS`: `'cleanse': 'cleanse'`. `COMBAT_BLOCKED`: `'cleanse': "There's no lifting a curse in the middle of a fight!"`. `DYING_ALLOWED`: unchanged (refused while dying by default). `HELP_SECTIONS` action row, alphabetical between `cancel` and `drop`: `('cleanse', 'cleanse <item>', 'Have a cleanser lift the curse from an equipped item.')`. `_completion_candidates`: `if verb == 'cleanse': return await self.get_equipped_items(char)`.

**6.2 Policy (T9).** `POLICIES['cleanse'] = Policy(allow_quantifier=False, no_multi="Cleanse one item at a time.", not_found="You don't have that equipped.", bad_index="You don't have that many of those equipped.")` — the `unequip` policy's messages verbatim, so the pool miss reads identically for a latent-cursed and a clean unequipped item (the no-leak rule, 4a).

**6.3 Routing helper.** `get_cleanser_in_room(self, room)` — a copy of `get_repairer_in_room` (T6) filtering `definition__is_cleanser=True`.

**6.4 `cmd_cleanse(self, args)`** — mirrors `cmd_repair`'s single-target path (T6):

1. `char = await self.get_character_fresh()`, `room`, `cleanser = await self.get_cleanser_in_room(room)`; `None` → `'There is no one here who can cleanse.'` (warn) and return.
2. `equipped = await self.get_equipped_items(char)`; `res = resolve('cleanse', args, equipped)`; not ok → `self.output(res.message, self._refusal_category(res))` and return.
3. `item = res.items[0]`. If `not (item.is_cursed and item.active_curse_id)` → `npc_voice.pick(cleanse_nothing_pool(cleanser), name=..., item=...)` (warn) and return. This one branch covers a plain equipped item **and** the admin-bypass unsprung latent alike (active curses only — Q3.5).
4. `outcome, price = await self.do_cleanse(item, char)` (6.5). `'poor'` → `npc_voice.pick(cleanse_poor_pool(cleanser), item=..., price=self.format_amount(char, price))` (warn). `'success'` → `npc_voice.pick(cleanse_success_pool(cleanser), item=..., price=...)` (success), then `await self.send_status_refresh()` (stat/bar cuts just reversed — sync the pane, the `cmd_unequip` precedent at `:1486`).

`item` display: `get_display_name_with_tier(item)` as repair uses; the item stays equipped after the cleanse (the player unequips at leisure).

**6.5 `do_cleanse(self, item, character)`** — `@database_sync_to_async`, the `do_repair_attempt` shape (T7):

```python
item = ItemInstance.objects.select_related('active_curse__definition').get(pk=item.pk)
price = item.active_curse.definition.cleanse_price * item.mk_tier
with transaction.atomic():
    char = Character.objects.select_for_update().get(pk=character.pk)
    try:
        char.copper = currency.subtract(char.copper, price)
    except ValueError:
        return ('poor', price)
    char.save(update_fields=['copper'])
    end_curse(item, 'cleansed')
self.character.copper = char.copper
return ('success', price)
```

No chance roll (3e). `end_curse` handles reversal, cleaning, and the memorial (T2); add `'cleansed'` to its docstring's cause list — no behavior change in `curse_utils.py`.

**6.6 Voice pools (`npc_voice.py`, T14).** Three per-slug dicts + fallbacks, each pool ≥3 lines, placeholders `{item}`, `{price}` (`{name}` in fallbacks): `CLEANSE_SUCCESS_LINES` / `CLEANSE_SUCCESS_FALLBACK`, `CLEANSE_POOR_LINES` / `CLEANSE_POOR_FALLBACK` (must name `{price}` — the refusal is the quote), `CLEANSE_NOTHING_LINES` / `CLEANSE_NOTHING_FALLBACK`. Slugs: `mother-tansy`, `maro-the-mender`, `tavik-the-mender`, `old-brammel`. Selection through a `_cleanser_pool(cleanser, lines, fallback)` helper in `consumers.py` mirroring `_pity_repair_line` (`consumers.py:64–74`). **Content is authored at implementation time under the creative-content policy** (§11).

---

## 7. Step 5 — The `inspect` sweep (`consumers.py`, `item_utils.py`, `npc_voice.py`)

Per #297 rulings 4d–4g and the Q6 amendment.

**7.1 Constant.** `item_utils.py`, beside `CURSE_WILD_CHANCE`: `CURSE_INSPECT_PRICE_PER_ITEM = 5` (copper per carried instance).

**7.2 Registry (T5).** `COMMAND_TABLE`: `'inspect': ('cmd_inspect', False)` (bare verb, fn 2 — args ignored, the `attune`/`heal` precedent). `COMBAT_BLOCKED`: `'inspect': "There's no time for that in the middle of a fight!"`. Not in `PROMPT_VERBS`, not in `GRAMMAR_VERBS` (no noun pool; the verb completes). `HELP_SECTIONS` action row between `home` and `loot`: `('inspect', 'inspect', 'Pay a cleanser to sweep everything you carry for curses.')`.

**7.3 `cmd_inspect(self)`:**

1. `char`, `room`, `cleanser` as in 6.4 step 1 (same no-cleanser line: `'There is no one here who can cleanse.'`).
2. `items = await self.get_carried_items(char)` (T8 — inventory **and** equipped). `n = len(items)`; `n == 0` → `'You carry nothing to inspect.'` (warn) and return, nothing charged.
3. `price = CURSE_INSPECT_PRICE_PER_ITEM * n`; `outcome = await self.do_charge(char, price)` — a small `@database_sync_to_async` helper with exactly the atomic `select_for_update` + `currency.subtract` shape of 6.5 (no item), returning `'poor'` or `'ok'`. `'poor'` → `npc_voice.pick(inspect_poor_pool(cleanser), price=...)` (warn), return.
4. `cursed = [i for i in items if i.is_cursed]` (latent or sprung alike — `is_cursed` is true for both, T4). Empty → `npc_voice.pick(inspect_clean_pool(cleanser), price=...)` (success). Otherwise `npc_voice.pick(inspect_found_pool(cleanser), count=len(cursed), price=...)` (warn), followed by **one line per cursed item**: `'  ' + compose_item_line(item)` (warn — consequence must be seen, #132), in inventory order.
5. **Sets nothing.** No `curse_identified`, no flags, no memorial. Repeat purchases allowed.

**7.4 Voice pools.** `INSPECT_CLEAN_LINES`/`_FALLBACK`, `INSPECT_FOUND_LINES`/`_FALLBACK` (`{count}`, `{price}`), `INSPECT_POOR_LINES`/`_FALLBACK` (`{price}`) — same dict-by-slug + fallback shape as 6.6; content per §11.

---

## 8. Step 6 — `examine` shows the cleansing price (`consumers.py`, T10)

Per ruling 3d. `get_curse_examine_info` returns a **4-tuple** `(name, remaining, curse_desc, price_display)` where `price_display = self.format_amount(character, instance.definition.cleanse_price * item.mk_tier)` computed **inside** the DB-context helper (it reads `current_room.zone` — never touch that FK from the async builder). The helper needs the character: pass `self.character` (it is the examining character; the item is theirs — the reveal gate `is_cursed AND curse_identified` already fired). `_format_identified_item_lines` renders one more line after the description line:

```
  Cleansing:  <price_display>
```

The generic `'  Curse:      This item carries a curse.'` row (no `curse_info`) is unchanged. Update the one call site (`:2024–2028`) and any test unpacking the 3-tuple (report as a deviation if a test changes).

---

## 9. Step 7 — Live acquisition (`item_utils.py`, T1)

Per ruling 5a–5e: `CURSE_WILD_CHANCE = 1 / 3` (replace `0.0`; update the comment: "v26.3 (#297): live — one curse in three Rare+ drops from pooled definitions"). Nothing else changes: the gate, the pool roll, the force path, the pools. Ridge-only is a consequence of the seeded rarity weights (T16), blessed — **no loot-table edits**.

---

## 10. Step 8 — Seed data (`seed_world.py`)

**10.1 Cleansers (T12).**

- `_seed_convergence_npcs`: add `CONVERGENCE_CLEANSERS = {'mother-tansy'}` beside the other sets; in the content dict add `'is_cleanser': slug in self.CONVERGENCE_CLEANSERS`. Mother Tansy is already a non-attackable cart fixture — `attackable` logic unchanged.
- `_upsert_npc_definitions`: add `'is_cleanser': extras.get('is_cleanser', False)` beside `is_repairer`. Add `'is_cleanser': True` to the three Menders' extras (`:7756`, `:7768`, `:8147`).
- Enforce-exact reconcile means every other NPC self-heals to `is_cleanser=False`.

**10.2 Curse prices (T13).** Add `'cleanse_price'` to every spec in the `curses` list and pass it through the reconcile block (`'cleanse_price': spec['cleanse_price']`). The values are law (ruling 3b/3c; Leaden Arm ruled in-session 2026-09-22):

| Curse | slug | `cleanse_price` (copper, Mk 1) |
|---|---|---|
| Curse of the Leaden Arm | `curse-leaden-arm` | 75 |
| Curse of the Craven Edge | `curse-craven-edge` | 60 |
| Tithe of the Copper Court | `curse-copper-tithe` | 90 |
| Curse of the Moth-Eaten Ward | `curse-moth-eaten-ward` | 75 |
| The Whisper in the String | `curse-whisper-string` | 120 |
| The Hollowing | `curse-hollowing` | 5000 |
| Gravekeeper's Hold | `curse-gravekeepers-hold` | 8000 |
| The Threefold Ruin | `curse-threefold-ruin` | 15000 |

The admission-test definitions (`test-mending-weak`, `test-mending-strong`, the salve's effect) keep `cleanse_price` at the default 0 — not curses.

**10.3 Verification checks (hard failures), beside the existing service-NPC checks (T12):**

- "No vendor, repairer, or cleanser NpcDefinition is attackable" — extend the `:3130` query with `| Q(is_cleanser=True)`.
- "Exactly four cleansers: Mother Tansy, Maro, Tavik, Old Brammel" — `NpcDefinition.objects.filter(is_cleanser=True)` slug set equality.
- "Every curse carries a cleanse price" — `EffectDefinition.objects.filter(is_curse=True, cleanse_price=0).count() == 0`, and no non-curse has a nonzero price.

**10.4 Expected deletions: 0** (field additions and flag flips only). In-session dev data action: `make seed` against the dev stack after the code lands (production execution: §15).

---

## 11. Step 9 — Creative content

The voice pools of §6.6 and §7.4 — four cleansers × six outcomes, ≥3 lines each, plus the six `{name}` fallbacks — are **authored at implementation time under the creative-content policy**: Mother Tansy's remedy-cart patter (her dialogue at `seed_world.py:977ff` is the voice reference), the three Menders in their checkpoint voices (Maro at Fordwatch, Tavik at Stairhead, Old Brammel on the Ridge; their pity-repair lines in `npc_voice.py` are the reference). The refusal pools must name `{price}`; the found pool must name `{count}`. Narration form, not attributed speech (the repair-outcome pattern: the NPC's name inside the line, quoted speech allowed). Never name a curse's identity or effect in an `inspect` line. The prose is yours.

---

## 12. Step 10 — Tests (`tests/test_v26_3_brief1.py`)

Harness precedents: `tests/test_v243_regen.py` (`run_regen_engine`, `:27`) for Phase 4; the consumer-level harness of `tests/test_v26_2_brief1.py` for commands and examine; `generate_item_instance(..., force_curse=True, curse=...)` for staging.

1. **Regen pause:** character below max vitality and longevity with an active `dot_vitality` component instance → one `process_effects` pass on a **non-round-boundary** tick (Phase 1 must not fire) → vitality unchanged, longevity regenerated. Same with the component `is_active=False` → vitality regenerates. Same with a `hot_vitality` and separately a `floor_hold_vitality` active (no dot) → vitality regenerates (hold-capped in the latter). Same with a `dot_longevity` → vitality regenerates (bar-scoped).
2. **Wild chance pinned:** `CURSE_WILD_CHANCE == 1 / 3`; with `random.random` mocked to `0.2` a Rare instance of a pooled template rolls a latent curse; mocked to `0.5` it does not; a Common instance never does; a non-template never does.
3. **`cleanse` happy path:** cleanser in room, equipped sprung curse (a stat cut), copper sufficient → copper reduced by exactly `cleanse_price × mk_tier`, `end_curse` effects (stat restored, `is_cursed` False, memorial stamped, `removed_by == 'cleansed'` on the instance and its components), item still equipped, success line from the pool.
4. **`cleanse` refusals:** no cleanser → the fixed line; insufficient copper → poor line naming the price and copper unchanged and curse intact; equipped uncursed item → nothing line; unequipped latent-cursed item and unequipped clean item → **byte-identical** `not_found` refusal; in combat → the `COMBAT_BLOCKED` line; while dying → refused.
5. **`inspect`:** with N carried (mix of equipped and inventory, including one latent and one sprung cursed) → copper reduced by `5 × N`, the found line, then exactly the cursed items' lines; no flag changes (`curse_identified` unchanged on the latent one); with none cursed → clean line; copper short → poor line, nothing charged; zero items → the nothing-to-inspect line and nothing charged; no cleanser → fixed line; in combat → refused.
6. **Examine price line:** identified curse at Mk 3 with `cleanse_price` 60 → the `Cleansing:` line reads the tier-formatted 180 copper; unidentified → absent.
7. **Registry:** `help` renders the two new rows for a non-admin; tab completion for `cleanse` offers exactly the equipped pool; `inspect` completes as a verb only.
8. **Seed:** after `seed_world` — the four cleanser slugs and no others; the eight `cleanse_price` values per §10.2; `CurseCandidate` count still 26.

**Suite of record:** run the full in-container suite in the path form — `python manage.py test apps/shyland/tests` via `docker exec` — and record the count (V26.2's was 1030). Zero existing tests changed unless reported as a deviation.

---

## 13. Verification

1. Full suite green in-container (path form above).
2. `make seed` on dev: reports **0 deletions**; re-run idempotent (0 changes second pass); the three new hard checks pass.
3. Shell spot-checks (dev): `NpcDefinition.objects.filter(is_cleanser=True).values_list('slug', flat=True)` == the four; `EffectDefinition.objects.filter(is_curse=True).values_list('slug', 'cleanse_price')` matches §10.2; `CurseCandidate.objects.count()` == 26; `from apps.shyland.item_utils import CURSE_WILD_CHANCE, CURSE_INSPECT_PRICE_PER_ITEM` → `1/3`, `5`.
4. Grep: `end_curse(` call sites are exactly the V26.2 three plus `do_cleanse`; no code path sets `curse_identified` from `inspect`.
5. `make deploy-dev` once implementation and verification pass.

---

## 14. Operator playtest checklist (dev stack)

Delivered interactively per the v40 Playtest delivery rule — summary first, collect the character name, then one step at a time with ready-to-paste code. Preconditions: dev deployed and seeded (§13); a test character (call them T) at the Convergence; all gifting via the shell helper (`generate_item_instance(definition, 1, 'rare', owner=T, gift=True, force_curse=True[, curse=<EffectDefinition>])` + `.save()`), never the admin add form. Mother Tansy stands at the east-ring cart room (`r40`).

1. **The cleanser is here.** Walk T to Tansy's room; `look`. **Expect:** Mother Tansy listed. **If absent → stop and report; else continue.**
2. **Sweep, all clear.** Note `wallet`; run `inspect`. **Expect:** Tansy's all-clear line; `wallet` down by exactly 5 × (number of items T carries, equipped included — count via `inventory` + `equip`). **If the line names a curse, the charge is wrong, or nothing is charged → stop and report; else continue.**
3. **Sweep finds a latent.** Gift T an `iron-mace` Rare with `force_curse=True` (pool → Leaden Arm), then `inspect`. **Expect:** the found line, then one line naming the iron mace; `examine iron mace` shows **no** curse block (the sweep set nothing). **If the mace is not named, another item is, or examine now shows the curse → stop and report; else continue.**
4. **No-leak refusal.** `cleanse iron mace` (still unequipped), then gift T a clean `iron-mace` Rare (no force) and `cleanse 2.iron mace`. **Expect:** both answer `You don't have that equipped.` — identical. **If the two lines differ in any way → stop and report; else continue.**
5. **Nothing to cleanse.** `cleanse <any equipped, uncursed item>` (e.g. `cleanse leather vest` if worn). **Expect:** Tansy's nothing-to-cleanse line, wallet unchanged. **If it charges or says anything about curses on other items → stop and report; else continue.**
6. **The price shows.** `equip` the cursed mace (the trap springs, STR cut), then `examine iron mace`. **Expect:** the curse block with a new `Cleansing:` line reading 75 coppers (Leaden Arm, Mk 1). **If the line is absent or the amount differs → stop and report; else continue.**
7. **Too poor.** Shell: set T's `copper` to 10. `cleanse iron mace`. **Expect:** Tansy's refusal naming 75 coppers; wallet still 10; STR still cut; `examine` still shows the live curse. **If anything was charged or the curse ended → stop and report; else continue.**
8. **Cleanse succeeds.** Shell: set `copper` to 1000. `cleanse iron mace`. **Expect:** Tansy's success line; `wallet` 925; STR restored to the pre-equip value (stats sheet); `examine` shows no curse block and the memorial paragraph; `unequip iron mace` succeeds; `equip iron mace` again springs nothing. **If any of the six facts fails → stop and report; else continue.**
9. **Regen pauses under a drain.** Shell: set T's `vitality_current` to half of max and `longevity_current` to half of max. Gift + equip a Rare item with `curse=<Tithe of the Copper Court>` (`curse-copper-tithe`: 3/round at Mk 1, 180 s). **Expect:** over the next rounds the vitality bar falls by exactly 3 per round and **never climbs**; the longevity bar keeps climbing. **If vitality oscillates or climbs, or longevity stalls → stop and report; else continue.**
10. **Regen resumes on cleanse.** `cleanse <the Tithe item>` (price 90). **Expect:** success line; within a second or two the vitality bar starts climbing again. **If regen stays paused → stop and report; else continue.**
11. **Combat gating.** Walk T to any attackable NPC and `attack` it, then `cleanse iron mace` and `inspect` mid-fight. **Expect:** both refused with their authored in-combat lines; nothing charged. `flee` (or finish the fight). **If either runs → stop and report; else continue.**
12. **A Z01 cleanser.** `travel` to Cragfoot (or walk). `inspect`. **Expect:** Old Brammel's own all-clear (or found) line, charged as in step 2. **If no cleanser answers at the checkpoint → stop and report; else continue.**
13. **Wild drop (bonus, not required).** If time allows, kill the Undercrag Weaver up to six times and `inspect` after each Rare drop. **Expect (statistically):** at least one curse named across six drops (probability ≈ 91%). **Record the observation either way; zero in six is a note, not a failure.** Done.

---

## 15. PENDING DEPLOY-TIME ACTIONS

| Action | Executor | Expected |
|---|---|---|
| Migration `0060` (Step 2) on production | `make deploy-prod` (closeout tail, standard) | applies cleanly |
| Production seed — `is_cleanser` on the four cleansers, `cleanse_price` on the eight curses, the three new hard checks | `make seed-prod`, bare, on its own operator confirmation in the closeout tail | **deletions: 0**; counts as §13.3 |

Dev-side executions of both happen in-session (Steps 2, 13). This block stays open until the production executions at release deploy. Code first, data second: the deploy precedes the seed.

---

## 16. Architecture doc (LAST, gated)

This step is gated on all implementation and verification steps above being complete and passing. Update `Shyland_Architecture_v26.md` **in place**: stamp to 26.3; **the hash moves** (architectural release — engine, commands, schema). Sections (anchors as of `8306b8a`): §4.1 models — `NpcDefinition.is_cleanser` beside the `is_repairer` entry (`:517`), `EffectDefinition.cleanse_price` in the effect-model block (`:559ff`), migration `0060`; §4.3 consumer — the commerce/routing block (`:751–836`): `cmd_cleanse`, `cmd_inspect`, `do_cleanse`, `do_charge`, `get_cleanser_in_room`, the examine price line (T10 block); §4.6 item utilities — `CURSE_WILD_CHANCE = 1/3` and `CURSE_INSPECT_PRICE_PER_ITEM` in the latent-roll paragraph (`:1047`); §4.8 seed — service flags (`:1109`) and the verification rule (`:1132`), the curse price column; §4.9 tick engine — the regen-law paragraph (`:1234`): the `dot_vitality` pause; §4.14 command layer — chart rows, `COMBAT_BLOCKED`, help (`:1486–1512`); §4.17 voice pools — the pool inventory (`:1635`). Header: a Version 26.3 paragraph in the standing form.

## 17. Closeout report

`docs/shyland/Shyland_V26.3_Brief_1_Closeout.txt`, completed in place: final commit hash, deviations (any 3-tuple → 4-tuple test conversions from §8; anything found at the T-claims pre-flight), actual-vs-expected seed deletions, the PENDING block, and the **operator playtest disposition** (verbatim-style, per #170). Issues **#297 and #338 close gated on verification passing** (#297's title is true once the dev stack runs this brief). End with the `implementation-session-end` ritual (which runs the issues report).
