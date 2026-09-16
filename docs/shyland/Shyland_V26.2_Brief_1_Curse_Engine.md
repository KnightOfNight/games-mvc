# Shyland V26.2 — Brief 1: The Curse Engine

**Release:** Version 26.2 (milestone `Version 26.2`) · **Branch:** `version_26_2` · **Founding ticket:** #330 (Release A of the #297 curse arc) · **Dependency:** #331 (stacked-effect staleness + admission policy — closes with this release)

**Design record:** the #297 Q1–Q7 rulings (2026-09-11), the #330 shape-set rulings items 2–6 (2026-09-14), and the #331 admission-policy rulings Q1–Q7 (2026-09-14). GDD text landed on this branch at `1ba5601` (§6.7 rewritten, §6.8 aligned, §6.9 admission + vocabulary, §5.6 touches) — all marked "(v26.2, pending implementation)". This brief is self-contained; the GDD sections are the design reference, the issues carry the ruling history.

**Technical coherence (#252):** every structural claim in this brief about existing code was verified against the code on this branch (tip `1ba5601`) at writing time by direct file reads. Claims are cited `file:line` as of that commit. The pre-flight diff (below) re-verifies the load-bearing ones.

---

## 1. Scope

Ships the complete curse engine, playtestable end to end, with acquisition **admin-only**:

- The #331 fix: stacked same-character effects compute from fresh state, fire in apply order, apply cumulatively — plus the ruled admission policy (six dot/hot lanes).
- Schema: `latent_curse`, `CurseCandidate`, curse fields on `EffectDefinition`, second magnitude pair + `no_expiry` on `EffectComponent`, memorial field on `ItemInstance`.
- New component types: `stat_cut_percent`, `cut_vitality_max`, `cut_longevity_max`, `damage_cut`, `armor_cut`, `floor_hold_vitality`.
- The apply loop (equip springs the trap), lifecycle (one end, clean item, memorial), death semantics (source-controlled), and the seed set (5 real Ridge curses + 3 high-tier test curses).
- The wild generation-time roll ships **wired but dormant** (chance constant 0.0). No live drops. Release B (#297) turns it on.

**Out of scope (Release B):** the `cleanse` service, the presence-detection sweep, cleanser NPC placement, any nonzero live drop chance.

---

## 2. Pre-flight

Process assumptions: standard v39 rituals — no deviations known. **No PENDING DEPLOY-TIME ACTIONS are open from prior releases** (V26.1's block closed at its deploy, 2026-09-14).

**Load-bearing technical claims — verified at writing time, re-verify before implementing (mismatch = HARD STOP per #252):**

| # | Claim | Where verified |
|---|---|---|
| T1 | `apply_effect_definition(definition, target, mk_tier, removed_by_label='consumable')` is the single application funnel; its same-definition block deactivates on `mk_tier >=` with `removed_by='reapplication'` and returns `[]` on lower-Mk | `effect_utils.py:25`, 39–58 |
| T2 | Its two callers: the use pipeline via `do_apply_effect` (`consumers.py:4405`; per-item loop applies at `consumers.py:1604` then consumes **unconditionally** at 1605) and the NPC proc path (`combat_utils.py:583`, apply at 612) | as cited |
| T3 | `process_effects` (`run_tick_engine.py:1431`) loads all ticking `EffectComponentInstance` rows in one query with `select_related` to the target — two rows on one character get two separate in-memory Characters (the #331 bug); the `newly_dying` set (1485) guards only the dying case | as cited |
| T4 | The out-of-combat `dot_vitality` fall (1495–1516) and the in-combat kill (1038–1050) both cancel ALL active effects `removed_by='dying'`; `execute_death` (216–256) refills all three bars and cancels ALL active effects `removed_by='death'` | as cited |
| T5 | `EffectDefinition` = name/slug/description only (`models.py:381–387`); `EffectComponent` fields per `models.py:420–446` (`is_instantaneous()` = both durations 0.0); `EffectComponentInstance.expires_at` is `null=True` (`models.py:812`) | as cited |
| T6 | `ItemInstance.is_cursed`/`curse_identified`/`active_curse` at `models.py:725–727`; `ItemDefinition.is_cursed_template` at `models.py:597` | as cited |
| T7 | `generate_item_instance(definition, mk_tier, rarity, owner=None, room=None, gift=False)` (`item_utils.py:98`) returns an **unsaved** instance; all generation funnels through it — loot drops via `generate_loot_from_table` (`item_utils.py:344–383`, rarity rolled at 372–374), vendor buys at `rarity='common'` (`consumers.py:4531–4536`), door gifts (`mc_door.py:461`) | as cited |
| T8 | Player equip success funnels through `equip_item` (`consumers.py:4385–4391` — sets `is_equipped`, `equipped_slot`, soulbind, bar rescale); `cmd_equip` (1353) has a free-slot success path and displacement success path(s) | as cited |
| T9 | Unequip curse guard in `_unequip_blocked_reason` (`consumers.py:1480`, `is_cursed` at 1482); examine reveal gate `is_cursed and curse_identified` (`consumers.py:1910`); description chokepoint `get_display_description` (`item_utils.py:252`) | as cited |
| T10 | v25.7 sudo curse teardown at `mc_door.py:1037–1042` (`removed_by='item-removed'`, does NOT touch `is_cursed`) | as cited |
| T11 | Z01 boss loot: `matron-loot`/`whistler-loot`/`dronemother-loot` roll `uncommon:100` (`seed_world.py:7307–7315`); Ridge `weaver-loot`/`king-loot` roll `rare:100`, `devourer-loot` `epic:100` (7730–7738); all entries Mk 1; seed uses `_reconcile` enforce-exact | as cited |
| T12 | `SHYLAND_VERSION = "26.1"` (`version.py:8`); pin test asserts `'26.1'` (`tests/test_b2_amendment1.py:122`) | as cited |
| T13 | Combat read points: player outgoing damage builds from `composite_weapon_term_detailed` (`run_tick_engine.py:711`); character TAV loaded once per round as `char_tav = total_armor_value(...)` (`run_tick_engine.py:646`) | as cited |

---

## 3. Step 0 + Step 1 — Version start (opening act)

1. Step 0 per the standing ritual: closeout-report stub committed and pushed.
2. Bump `SHYLAND_VERSION` to `"26.2-DEV"` in `django/src/apps/shyland/version.py`, move the pin test assertion (`tests/test_b2_amendment1.py:122`) to `'26.2-DEV'` in the **same commit** — its own commit.
3. `make deploy-dev` from the worktree (the version-start deploy).

---

## 4. Step 2 — Schema (models + migration)

All in `django/src/apps/shyland/models.py`. Field names below are final.

**`EffectDefinition`** gains:
- `is_curse = models.BooleanField(default=False)`
- `apply_text = models.TextField(blank=True, default='')` — the equip-time theater; newline-separated lines
- `memorial_text = models.TextField(blank=True, default='')` — stamped onto the item at curse end

**`EffectComponent`** gains:
- `magnitude2_base = models.FloatField(null=True, blank=True)`
- `magnitude2_scaling = models.FloatField(null=True, blank=True)` — computed as `magnitude2_base + magnitude2_scaling × mk_tier` (mirror of `computed_magnitude`, `models.py:442–443`); only `floor_hold_vitality` reads it
- `no_expiry = models.BooleanField(default=False)` — instances created with `expires_at=None`; the expiry sweep must skip null. `duration == 0` keeps meaning instantaneous; a `no_expiry` component's duration fields are ignored.

**`ItemInstance`** gains:
- `latent_curse = models.ForeignKey('EffectDefinition', null=True, blank=True, on_delete=models.SET_NULL, related_name='latent_on_instances')`
- `memorial_description = models.TextField(blank=True, default='')`

**New model `CurseCandidate`:**
- `item_definition = models.ForeignKey('ItemDefinition', on_delete=models.CASCADE, related_name='curse_candidates')`
- `curse = models.ForeignKey('EffectDefinition', on_delete=models.CASCADE, related_name='candidate_on')`
- `weight = models.IntegerField(default=1)`
- `Meta: unique_together (item_definition, curse)`

**New component type choices** appended to `COMPONENT_TYPE_CHOICES` (`models.py:390–408`): `stat_cut_percent`, `cut_vitality_max`, `cut_longevity_max`, `damage_cut`, `armor_cut`, `floor_hold_vitality`. **`curse_generic` stays in the list** (retired in place — nothing seeds it, no code applies it).

**Migration:** `make makemigrations APP=shyland && make migrate` — expect one migration. Commit it.

---

## 5. Step 3 — The #331 fix + admission (effect_utils + tick engine)

### 5.1 Refusal contract

New exception in `effect_utils.py`: `class EffectRefused(Exception)` carrying the **blocking active effect's definition name**. `apply_effect_definition` raises it instead of silently returning `[]`:

- Same-definition lower-Mk (today's T1 `return []` branch) → raise.
- New: the admission gate (5.2) → raise.

Caller changes (both verified in T2):
- **Use pipeline** (`consumers.py:1604`): catch `EffectRefused` → do **NOT** consume the item, print a warn-category line naming the blocker, e.g. `The {blocking name} coursing through you is stronger — the {item name} would be wasted.` (exact wording implementer's latitude, warn layer, names both), and **stop the use loop** (no further items of this stack are attempted). This deliberately converts the old silently-spent lower-Mk path to kept-plus-warn (#331 Q6a — a ruled behavior change; existing tests pinning silent-spend convert per the test-hygiene rule, reported as deviations).
- **NPC proc path** (`combat_utils.py:612`): catch `EffectRefused` → skip silently; the effect's name is **not** appended to the attack messages (#331 Q6b).

### 5.2 The admission gate (in `apply_effect_definition`, after the same-definition check)

- Lanes: the six ticking types `dot_vitality`, `hot_vitality`, `dot_longevity`, `hot_longevity`, `dot_acuity`, `hot_acuity`. Shifts, stat effects, instants: ungated.
- For each **gated** component of the incoming definition, compute its magnitude at the incoming `mk_tier` and compare against every **active** `EffectComponentInstance` of the **same component type** on the target: admit only if strictly greater than all of them (a stronger HoT heals harder; a "worse" DoT hits harder — same comparison, per #331 Q2). Equal → refused. Duration plays no role.
- **Whole-effect atomicity (brief-time detail under the rulings):** if ANY gated component of a multi-component definition is refused, the whole application is refused — no partial applications, the consumable is kept whole. The raised refusal names the first blocking effect.
- **Admission = join:** on admit, create alongside the existing instances — never deactivate a cross-definition incumbent.
- **Curse bypass — both directions (#331 Q5):** curse applications (Step 6, the trap) do not pass through this gate at all, AND active curse-sourced component instances (`effect_instance.definition.is_curse`) are **excluded from the incumbent comparison set** — a live curse never blocks an ordinary effect's admission into its lane.

### 5.3 The staleness fix (`process_effects`, `run_tick_engine.py:1431`)

Phase 1 invariants (mechanics implementer's latitude, invariants pinned by tests):
- **One in-memory `Character` per target per pass** — all of a character's ticking components read and mutate the same object; deltas are cumulative (two 10-damage dots on 100 leave 80).
- **Apply order:** components fire ordered by `(effect_instance.applied_at, component instance pk)` per character.
- Each component's `old` is the state left by the previous component this pass; the #133/#145 announcement doctrine then holds automatically — a tick that changes nothing (`new == old` against true state) is genuinely silent.
- The `newly_dying` skip (T3) keeps its behavior.

---

## 6. Step 4 — The six new component types

**`stat_cut_percent`** (duration-based, once, reversible): on apply, `delta = int(magnitude × current stat value)` computed once, **stored as the component instance's `magnitude`** (the fraction lives on the component; the instance stores the flat delta — exact reversal, no drift; same storage trick as `apply_stat_effect`'s delta model, `effect_utils.py:240–263`). Apply/reverse via the existing `apply_stat_effect` path (target_stat reuse; floor of 1 per its existing `max(1, …)`).

**`cut_vitality_max` / `cut_longevity_max`** (duration-based, once, reversible): on apply, cut the bar's max by `magnitude` (fraction) through **the standing bar-law rescale** (fill fraction invariant — the same atomic rescale gear equip uses, `_rescale_bars_for_gear` family). Store the flat max-delta on the instance; reverse restores it through the same rescale. Acuity deliberately has no cut type.

**`damage_cut` / `armor_cut`** (duration-based, passive — no per-tick action): read as multipliers at the two combat read points (T13). `factor = 1 - magnitude` per active instance; multiple actives multiply. `damage_cut` scales the player's outgoing damage term after composition; `armor_cut` scales `char_tav` before the armor curve. One shared reader (e.g. `combat_utils.curse_output_factor(character)` / `curse_armor_factor(character)`) — query active component instances of the type for the character; keep it out of per-action hot loops (read once per round alongside the equipped-set load, `run_tick_engine.py:642–650`).

**`floor_hold_vitality`** (duration-based, ticking): `magnitude` = drain per round; `magnitude2` = hold fraction; `hold_value = max(1, ceil(magnitude2 × vitality_max))`.
- Each round boundary: if `vitality_current > hold_value` → drain `min(magnitude, current − hold_value)` (announce the actual delta, #133 doctrine); on arrival exactly at the hold print one terminal line; at or below the hold → silent no-op.
- **Heal ceiling while active:** any vitality-increasing write on the target clamps to `max(current_before_heal, hold_value)` — below the hold, heals work up to the hold; above it, heals are no-ops. Enforce at the vitality-heal write paths: the instant restores (`effect_utils._apply_instant_component`, vitality branches) and `hot_vitality` ticking. Combat damage is untouched (it can take the character below the hold; the drain never does).
- The floor-hold does **not** itself kill — it pins above zero by construction (`hold_value >= 1`).

---

## 7. Step 5 — Generation: the latent roll

In `generate_item_instance` (`item_utils.py:98`) — new parameters `force_curse=False, curse=None`:

- **Natural path (dormant):** module constant `CURSE_WILD_CHANCE = 0.0` with a comment naming Release B (#297) as its activation. When `definition.is_cursed_template` is True, the definition has `CurseCandidate` rows, the rolled `rarity` is in `('rare', 'epic', 'legendary')`, and `random.random() < CURSE_WILD_CHANCE` → roll `latent_curse` weighted by `CurseCandidate.weight`, set `is_cursed=True`. At 0.0 this never fires — zero wild drops in this release.
- **Force path:** `force_curse=True` → skip the chance AND the rarity gate. `curse=<EffectDefinition>` given → use it directly (must have `is_curse=True`, else `ValueError`); omitted → weighted pool roll (empty pool = `ValueError`). This is the gifting/playtest path.
- Vendor buys (T7, always `'common'`) can never roll cursed on the natural path — deliberate.

**Shell-helper doctrine:** gifting a cursed item = `generate_item_instance(definition, mk_tier, rarity, owner=character, gift=True, force_curse=True[, curse=...])` then `.save()` — the standing gift-via-the-shell-helper language extends with the curse parameters.

---

## 8. Step 6 — The trap: equip springs it

New function (suggested home: a new `curse_utils.py`, or `effect_utils` — implementer's call, one home): `spring_curse(item, character)`:

1. Create the curse `EffectInstance` at the **item's** `mk_tier` via the shared internals with **all gates bypassed** (no admission, no same-definition check — two items with the same curse each spring independently, per #330 item 5c).
2. Set `item.active_curse` to it; set `item.curse_identified = True` in the same motion (springing IS the identification).
3. Return the theater lines: `apply_text` split on newlines, empties dropped.

Hook: every **player equip success path** in `cmd_equip` (T8 — the free-slot path at `consumers.py:1384–1393` and the displacement path(s) below it; find every call of `equip_item` in the command and hook after the success output). Ordering per #330 item 5b: the standard `You equip …` success line prints **first**, then each theater line as its own output message — **narration voice** (the value-color/default category the standing narration output uses — match the existing ambient-narration category in `consumers.py`, do not invent a new one). Private: no room broadcast. Fires only when `is_cursed and latent_curse_id and active_curse_id is None`.

Audit at implementation: any **other** path that sets `is_equipped=True` on a player-owned latent-cursed item (e.g. door-side operations) — if one exists, it must either spring the curse or be an explicitly documented admin bypass (the v25.7 sudo-unequip precedent). Record the finding in the closeout.

---

## 9. Step 7 — Lifecycle: the shared teardown + death semantics

### 9.1 `end_curse(item, cause)` — the one teardown (per #330 item 4b)

For the item's `active_curse`: deactivate all component instances + the instance with `removed_by=cause`; **reverse every reversible component** (stat cuts by stored delta; bar cuts via the bar-law rescale); clear `item.is_cursed = False` and `item.latent_curse = None`; stamp `item.memorial_description = definition.memorial_text`; leave `curse_identified` untouched; clear `item.active_curse = None`. Causes: `'timeout'` (expiry), `'curse-death'`, `'item-removed'` (sudo). One curse life per instance — with `latent_curse` cleared, no path ever re-springs.

Callers:
- **Expiry:** when the effect-expiry sweep closes a curse `EffectInstance` (all components expired), route through `end_curse` (locate the item via `active_curse` reverse lookup) so the clean + memorial ride expiry too. Expiring curse components use the standing expiry-message machinery; the memorial does the storytelling afterward.
- **Sudo removal** (`mc_door.py:1037–1042`, T10): replace the inline teardown with an `end_curse(item, 'item-removed')` call — the v25.7 behavior plus the newly ruled latent-flag clean.
- **Curse-caused death** (9.2).

`get_display_description` (`item_utils.py:252`): when `memorial_description` is non-empty, append it as a closing paragraph to whatever the function returns for the identified branch.

### 9.2 Death semantics (per #330 item 4d/4e — both cancel sites, T4)

- In all three cancel blocks (fall in combat 1043–1050, fall out of combat via `fall_and_cancel` 1465–1477, `execute_death` 248–255): **exclude curse-sourced instances** (`definition.is_curse=True`) from the cancel.
- **Cause detection at the fall:** in the `dot_vitality`/`floor_hold_vitality` fall branch, if the component that carried vitality to 0 belongs to a curse instance → that one curse ends via `end_curse(item, 'curse-death')` (item located by `active_curse` reverse lookup); every other curse rides through. (The floor-hold cannot cause a fall by construction; the branch guard is for dots.)
- A persisting curse never suspends: no special-casing in `process_effects` — its ticks on emptied bars are no-ops under the change-only doctrine, its cuts stay applied, and `execute_death`'s refill (T4) naturally fills to the **cut** max because the cut components were not reversed.

---

## 10. Step 8 — Display, examine, and the door mirror

- **Examine reveal** (gate at `consumers.py:1910`, unchanged): the revealed block shows the curse's **name**, **time remaining** (`permanent` when the instance has only `no_expiry`/never-expiring components — #47's ruled vocabulary), and the curse definition's `description`. Composition matches the existing detail-block style (`Curse:` tail row per §6.8/#203).
- **Unequip refusal** (`consumers.py:1480–1482`): unchanged — it already keys on `is_cursed`, which the teardown now clears.
- **Door `edit_item` mirror (25.16 precedent):** check the agent door's `edit_item` schema — if it enumerates `ItemInstance`/`ItemDefinition` fields, mirror the new fields (`latent_curse`, `memorial_description`, curse fields) with appropriate read-only/validation posture; verify the shape at implementation and record what was done in the closeout.

---

## 11. Step 9 — Seed data (`seed_world.py`, `_seed_effects` + a new `_seed_curses`)

All curse `EffectDefinition`s carry `is_curse=True`, authored `description`, `apply_text` (the theater — em-dash-free lines, one output line each), and `memorial_text`. `_reconcile` enforce-exact throughout. **Expected deletions: 0** (purely additive; report actual-vs-expected in the closeout).

### 11.1 The five real Ridge curses (expiring tier)

Pools per the low-level rule: pool of one, same make/model → same curse; assigned to the **Ridge-boss loot definitions** (T11 — the Rare+ habitat). Each listed definition gets `is_cursed_template=True` plus one `CurseCandidate(weight=1)` row.

| Curse (slug) | Components (base/scaling; duration secs) | Pool definitions |
|---|---|---|
| **Curse of the Leaden Arm** (`curse-leaden-arm`) | `stat_cut_percent` STR, magnitude 0.25/0.0; duration 300/0 | `iron-mace`, `battle-axe` |
| **Curse of the Craven Edge** (`curse-craven-edge`) | `damage_cut` magnitude 0.20/0.0; duration 240/0 | `iron-sword`, `broadsword`, `combat-knife` |
| **Tithe of the Copper Court** (`curse-copper-tithe`) | `dot_vitality` magnitude 2.0/1.0; duration 180/0 | all 12 `copper-{ring,amulet}-of-{stat}` |
| **Curse of the Moth-Eaten Ward** (`curse-moth-eaten-ward`) | `armor_cut` magnitude 0.30/0.0; duration 360/0 | `leather-cap`, `leather-shoulders`, `leather-vest`, `leather-gloves`, `leather-belt`, `leather-leggings`, `leather-boots`, `wooden-shield` |
| **The Whisper in the String** (`curse-whisper-string`) | `stat_cut_percent` DEX 0.15/0.0 + `dot_longevity` 3.0/2.0; both duration 180/0 | `hunting-bow` |

All durations sit in the ruled 3–10 minute band. The `insect-carapace` entries in the boss tables are materials outside the equipment rotation — no pool (and `common:100` anyway). (Deliberate: no curse in this set carries `dot_acuity` — its tick branch still stores 1-decimal rounds (`run_tick_engine.py:1556`), the erased-small-magnitude shape #333 is auditing; authored acuity curses wait for that doctrine.)

### 11.2 The three high-tier test curses (no pools — explicit-override gifting only)

| Curse (slug) | Components |
|---|---|
| **The Hollowing** (`curse-hollowing`) | `dot_vitality` 5.0/3.0, `no_expiry=True` — the DoT-to-death: it kills you, the curse ends, the item is yours |
| **Gravekeeper's Hold** (`curse-gravekeepers-hold`) | `floor_hold_vitality` magnitude 8.0/4.0, magnitude2 0.05/0.0, `no_expiry=True` — pins at 5% of max |
| **The Threefold Ruin** (`curse-threefold-ruin`) | `stat_cut_percent` STR 0.50/0.0 + `damage_cut` 0.35/0.0 + `dot_longevity` 5.0/2.0, all `no_expiry=True` |

### 11.2b Admission-test definitions (not curses)

So the admission playtest is mechanically executable, seed two plain HoT `EffectDefinition`s and one test consumable:

- `test-mending-weak` — `hot_vitality` 3.0/0.0, duration 60/0
- `test-mending-strong` — `hot_vitality` 6.0/0.0, duration 60/0
- `ItemDefinition` **`weak-mending-salve`** — consumable, `effect` → `test-mending-weak`, mirroring the `healing-draught` consumable seed shape; **no vendor entries, no loot entries** (shell-gift only). Names/descriptions author freely.

### 11.3 Creative content

`description`, `apply_text` (1–4 lines each; The Hollowing gets the full vision-theater treatment — a carried-to-another-world sequence per the Q2.4 ruling), and `memorial_text` (1–2 lines each) are **authored at implementation-time seed-writing under the creative-content policy** — written into the seed by the implementation session, flowing freely, not operator-reviewed (surface only systemic implications). The structural fields above are law; the prose is yours.

In-session dev data action: `make seed` against the dev stack after the code lands. (Production execution: PENDING DEPLOY-TIME ACTIONS.)

---

## 12. Step 10 — Tests

Directory-path invocation only: `python manage.py test apps/shyland/tests` via `docker exec` in the django container.

Required coverage (new tests; suite grows from 990 — zero existing tests change except those pinning behavior this brief deliberately changes, reported as deviations):

1. **Admission:** strict-greater admits (HoT and DoT), equal refused both directions, duration-blind, per-lane isolation (dot never gates hot; bars never cross), shifts/stats ungated, join-not-replace (both instances live), same-definition ≥-Mk refresh unchanged, lower-Mk raises `EffectRefused`, whole-effect atomicity on multi-component refusal.
2. **Refusal surfacing:** use path keeps the consumable + warns; NPC path silent skip (no name appended).
3. **Staleness (#331):** two same-lane HoTs on one damaged character at one boundary → cumulative delta, correct per-component announcements, second-at-full silent; dot+dot cumulative; apply-order honored.
4. **Generation:** natural roll never fires at chance 0.0; force path rolls from pool (weighted), respects explicit `curse` override, bypasses rarity gate; `ValueError` on non-curse override / empty pool; natural-path rarity gate logic exercised with the constant patched nonzero.
5. **The trap:** equip springs (active_curse populated, curse_identified set, theater lines returned in authored order), fires only once, soulbind unchanged, second same-curse item springs independently.
6. **Components:** stat cut exact reversal (including after a mid-curse stat change), bar cuts rescale on apply and reverse (fill fraction invariant), damage/armor factors multiply and read at the round points, floor-hold drain/arrival-line/pin-silence/heal-ceiling (below-hold heal up to hold; above-hold heal no-op; combat damage below hold; heal back up to hold), floor-hold never kills.
7. **Lifecycle:** expiry cleans (flags cleared, components reversed, memorial stamped, unequip then free, re-equip springs nothing); `get_display_description` appends the memorial; sudo teardown cleans the latent flag.
8. **Death semantics:** curse-dot fall → that curse ends `curse-death`, item clean; other-cause death → curse persists through both cancel sites, still active post-respawn, cuts still applied (respawn fills to cut max); multi-curse: only the causing one ends.
9. **Version pin** moved with the bump (Step 1).

---

## 13. Verification

1. Full suite green in-container (path form above).
2. `make seed` on dev: reports **0 deletions**; re-run idempotent (0 changes second pass).
3. Shell spot-checks (dev): `CurseCandidate.objects.count()` == 26 (2+3+12+8+1); `EffectDefinition.objects.filter(is_curse=True).count()` == 8; the 26 pooled definitions all `is_cursed_template=True`; the three test curses have zero `CurseCandidate` rows; `test-mending-weak`/`test-mending-strong`/`weak-mending-salve` exist, the salve has no vendor or loot entries, and neither mending definition is `is_curse`.
4. Grep: no code path applies `curse_generic`; `CURSE_WILD_CHANCE == 0.0`.
5. `make deploy-dev` once implementation and verification pass.

---

## 14. Operator playtest checklist (dev stack)

Preconditions: dev deployed and seeded (Step 13); a test character (call them T) at the shell's disposal; all gifting via the shell helper (`generate_item_instance(..., gift=True, force_curse=True[, curse=...])` + `.save()`), never the admin add form.

1. **Latent invisibility.** Gift T an `iron-mace` Mk 1 Rare with `force_curse=True` (pool → Leaden Arm). Run `inventory` and `examine` on it. **Expect:** no curse indicator anywhere (latent curse set, `curse_identified` False). **If any curse hint shows → stop and report; else continue.**
2. **The trap.** `equip` the mace. **Expect:** `You equip the Iron Mace Mk 1.` first, then the Leaden Arm's theater line(s) in narration color; the stats sheet shows STR visibly reduced (the cut is 25% of the pre-cut base stat; the displayed effective STR includes gear, so expect a drop of that flat amount, not exactly 25% of the displayed number). **If the theater is missing, precedes the equip line, or STR is uncut → stop and report; else continue.**
3. **Identified reveal.** `examine` the mace. **Expect:** curse block — name, time remaining counting down from 5:00, description. **If absent or shows `permanent` → stop and report; else continue.**
4. **Teeth while live.** `unequip` the mace. **Expect:** refusal (the standing cursed-unequip refusal). **If it unequips → stop and report; else continue.**
5. **Expiry cleans.** Wait out the 5 minutes. **Expect:** curse expiry message; STR restored to the pre-equip value; `examine` now shows **no** curse block and the memorial paragraph at the description's end; `unequip` then `equip` again succeeds with no theater, no re-curse. **If any of the five facts fails → stop and report; else continue.**
6. **Admission — climb admits.** Out of combat, damage T (shell: set `vitality_current` to half its max), then shell-apply `test-mending-weak` and then `test-mending-strong` (`apply_effect_definition(<def>, character, 1)` each). **Expect:** both active; healing per round = 9 (the sum), announced as each component's own actual delta in apply order; once full, further ticks are silent. **If the stronger is refused, deltas double-count, or full-bar ticks announce → stop and report; else continue.**
7. **Admission — weaker refused, potion kept.** Shell-damage T again so healing is meaningful, shell-apply `test-mending-strong` (60-second window), gift T a `weak-mending-salve` via the shell helper, and `use` it while the strong mend is active. **Expect:** a warn line naming the stronger effect; the salve **still in inventory** (count unchanged). **If the salve is consumed or the refusal is silent → stop and report; else continue.**
8. **Floor-hold.** Gift + equip a Rare item with `curse=Gravekeeper's Hold`. **Expect:** vitality drains 8/round with actual-delta lines, one arrival line at 5% of max, then silence; `use` a Healing Draught → vitality does **not** rise above the hold and the draught is consumed with its heal capped (or no-op'd at the hold). **If it drains below the hold, kills, or heals above the hold → stop and report; else continue.** (Leave it equipped for step 10.)
9. **DoT-to-death — the ordeal.** On a second item, gift + equip `curse=The Hollowing` (shell-lower `vitality_current` first to shorten the wait — the drain is 8/round at Mk 1). **Expect:** the vision theater on equip; the drain carries T to the fall ("fatal blow" line), the standard dying window and respawn run; after respawn the Hollowing item is **clean** — `examine` shows memorial, no curse; unequip works; T keeps it forever. **If the curse survives its own kill or the fall path breaks → stop and report; else continue.**
10. **Other-cause death — the curse persists.** The Gravekeeper's Hold item is still equipped (step 8). Get T killed by an NPC (shell-lower vitality near zero and engage). **Expect:** through dying + respawn the Hold is **still active** — `examine` shows the live curse, and over the following rounds the drain pulls the refilled bar back down toward the hold (8/round; re-pinning takes a while from full — the direction is the check, not instant arrival). **If the Hold was cleaned by the unrelated death → stop and report; else continue.**
11. **Sudo containment.** Have the admin remove the Hold via the standing `sudo` removal path. **Expect:** effect ends, item clean (memorial stamped, unequip free, no re-spring on re-equip). **If the latent state survives → stop and report; else continue.**
12. **NPC refusal silence.** (Optional if a suitable NPC dot is at hand:) with a strong shell-applied `dot_vitality` active, fight the Fracture Wraith. **Expect:** when its weaker poison procs, the attack line names no effect and nothing applies; with the strong dot expired, the poison lands normally. **If a weaker NPC dot stacks or announces → stop and report; else done.**

---

## 15. PENDING DEPLOY-TIME ACTIONS

| Action | Executor | Expected |
|---|---|---|
| Migration (Step 2) on production | `make deploy-prod` (closeout tail, standard) | applies cleanly |
| Production seed — curse definitions/components, 26 `CurseCandidate` rows, 26 `is_cursed_template` flags | `make seed-prod`, bare, on its own operator confirmation in the closeout tail | **deletions: 0**; counts as §13.3 |

Dev-side executions of both happen in-session (Steps 2, 13). This block stays open until the production executions at release deploy.

---

## 16. Architecture doc (LAST, gated)

This step is gated on all implementation and verification steps above being complete and passing. Update `Shyland_Architecture_v26.md` **in place**: stamp to 26.2; **the hash moves** (architectural release). Sections: the effect-system section (admission gate, refusal contract, staleness fix, new component types, second magnitude pair, `no_expiry`), the item-system section (latent curse, `CurseCandidate`, generation parameters, memorial), the tick-engine section (per-character fresh-state pass, curse-exempt cancels, curse-death attribution), and the door section (edit_item mirror if changed).

## 17. Closeout report

`docs/shyland/` `.txt` per the standing ritual: final commit hash, deviations (including any test conversions from §12's behavior changes and the §8 equip-path audit finding), actual-vs-expected seed deletions, the PENDING block, and the **operator playtest disposition** (verbatim-style, per #170). Issues #330 and #331 close gated on verification passing. End with the `implementation-session-end` ritual (which runs the issues report).
