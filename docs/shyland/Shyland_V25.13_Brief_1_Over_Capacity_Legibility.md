# Shyland V25.13 — Brief 1: Over-Capacity Legibility

- **Release:** Version 25.13 (milestone) · **Branch:** `version_25_13`
- **Founding ticket:** #275 (unequipping +STR gear silently strands over carry capacity) · **Dependency:** #319 (pickup/buy load-counting basis disagrees with loot/header/bag-guard)
- **Design session:** 2026-08-31 · **Rulings:** recorded on #275 and #319 · **GDD:** §6.10 + §3 updated at `4c10a98` (markers `v25.13, pending implementation`)
- **Scope:** code + tests only. **No migration** (no model change), **no seed change**, **no client change** (warn is an existing output category), **PENDING DEPLOY-TIME ACTIONS: NONE.**

## 1. The ruling being implemented

**The over-capacity state is legal; this release makes it legible (Direction B, operator-ruled 2026-08-31).** Unequipping (or auto-swap-displacing) stat-granting gear may drop carry capacity below current load — the action succeeds and warns; it is never refused. The **bag guard stays byte-identical** (operator: "keep the guard on bags since it is 100% consistent"). Three legibility surfaces: a warn at the moment of stranding, honest over-limit refusals in pickup/loot/buy, and the `inventory` header's numbers (which already render the state — no change there). Folded in per #319: pickup and buy unify onto the unequipped-only load count the rest of the game already uses.

Out of scope, deliberately: the agent door's `strip` action already bypasses `_unequip_blocked_reason` knowingly (v25.5 — "the #275 over-capacity state accepted knowingly"); no door changes. The `inventory` header: no change.

## 2. Verified technical claims (#252 receipts)

Every claim below was **verified against `version_25_13` @ `4c10a98` on 2026-08-31** by the authoring design session. Line numbers are from that commit; re-locate by content if drift has occurred, and treat any load-bearing mismatch as a HARD STOP per v37.

1. **The capacity formula** is `item_utils.carry_capacity(character, equipped_items)` (`item_utils.py:272`): `effective_STR × 10 × (100 + Σ bag_pct) // 100`.
2. **The unequipped-only counter** is `loot_utils.get_carry_counts(character)` (`loot_utils.py:26–35`): returns `(current, max_carry)` with `current` = unequipped instances only. The consumer wraps it as `get_carry_counts` (`consumers.py:4372–4374`, `@database_sync_to_async`).
3. **The all-items outlier** is `consumers.get_carry_capacity` (`consumers.py:4269–4276`): `current_count = ItemInstance.objects.filter(owner=character).count()` — **equipped included**. Its complete caller set: `cmd_pickup` (`consumers.py:1249`), `cmd_buy` (`consumers.py:2247`), and `tests/test_gear_combat.py:134` (which uses only the max element of the tuple). No other references repo-wide.
4. **Pickup refusals** (`consumers.py:1248–1284`): outright gate `current_count >= max_capacity` → `"You can't carry any more. ({current_count}/{max_capacity} items)"` (warn); mid-sweep partial gate → `"You can't carry the rest. ({current_count}/{max_capacity} items)"` (warn). The mid-sweep line is reachable only when increments reach exactly `== max` (the outright gate has already passed), so it never fires in the over state.
5. **Buy refusal** (`consumers.py:2247–2254`): gate `current_count + qty > max_capacity` with qty-1 / qty-N string variants, both `"You can't carry ..."` + numbers (warn).
6. **Single-corpse loot** (`consumers.py:2103–2116`): uses the `get_carry_counts` wrapper; in-loop gate `current_count >= max_carry` → `"You can't carry any more. ({current_count}/{max_carry} items)"` (warn). Reachable in the over state on the first iteration.
7. **Sweep loot** (`loot_utils.py:162–191`, inside `sweep_corpses`): module-level `get_carry_counts`; in-loop gate at `loot_utils.py:180` with the same string (`loot_utils.py:182`). Plunder's output is the sweep's output verbatim (GDD §9), so this site is plunder's refusal too.
8. **`cmd_unequip`** (`consumers.py:1446–1468`): resolve → bag-only `count_unequipped_items` fetch → `_unequip_blocked_reason` → `unequip_item` → success line `You unequip {item_ref}.` → `send_status_refresh()`.
9. **`_unequip_blocked_reason`** (`consumers.py:1470–1482`): cursed check, then bag-only capacity check (`(unequipped_count + 1) > new_limit` against `carry_capacity` over the reduced equipped list). **This function is not modified by this brief.**
10. **`cmd_equip`** (`consumers.py:1346–1444`): bare form renders the paper-doll and returns (`:1351–1355`); **free-slot branch** (`:1376–1385`) equips → success line → `send_status_refresh()` → return; **auto-swap branch** (`:1423–1444`) checks the displaced item via `_unequip_blocked_reason` (bag displacement refuses, `:1429–1434`), then `unequip_item` + `equip_item` → swap sentence (`You equip X, replacing Y.`) → `send_status_refresh()`.
11. **Inventory header** (`consumers.py:1099–1110`): `current_carry = len(unequipped)`, `max_carry = carry_capacity(char, equipped)` → `inventory_table_lines` renders `Inventory ({current}/{max})...` (`item_utils.py:621`). Already renders the over state; untouched.
12. **Version pin:** `version.py:8` reads `SHYLAND_VERSION = "25.12"`; the pin test is `tests/test_b2_amendment1.py:122` (`assertEqual(SHYLAND_VERSION, '25.12')`).
13. **Suite size:** 915 at branch cut (source: the architecture doc's 25.12 header paragraph).

## 3. Implementation steps

### Step 1 — version start (opening act; standing requirement)

In one commit of its own: `SHYLAND_VERSION` → `"25.13-DEV"` (`version.py`), and the pin test assertion (`tests/test_b2_amendment1.py:122`) → `'25.13-DEV'`. Then run the version-start `make deploy-dev` from the worktree.

### Step 2 — #319: unify the load count (unequipped-only, everywhere)

1. In `cmd_pickup` and `cmd_buy`, replace `await self.get_carry_capacity(char)` with `await self.get_carry_counts(char)` (same `(current, max)` tuple shape — claim 2/3).
2. Delete `consumers.get_carry_capacity` (claim 3).
3. In `tests/test_gear_combat.py:134`, replace `consumer.get_carry_capacity(char)` with `consumer.get_carry_counts(char)`.
4. Guard: `grep -rn 'get_carry_capacity' django/src/` must return **zero** hits after this step. (`item_utils.carry_capacity` — no `get_` prefix — is the formula helper and stays.)

### Step 3 — honest refusals (the over-limit variant, four sites)

**The law:** when a capacity gate trips while the character is **strictly over** capacity (`current > max`), the refusal line is, at every site, exactly:

```
You're over your carry limit. ({current}/{max} items)
```

warn category, one f-string shape. When the gate trips at ordinary fullness (`current == max`, or a quantity would merely exceed), the **existing strings are unchanged**. Site by site:

1. **`cmd_pickup` outright gate:** `if current > max` → the over-limit line; `elif current >= max` → the existing `"You can't carry any more."` line. The mid-sweep `"You can't carry the rest."` line is untouched (unreachable in the over state — claim 4).
2. **`cmd_buy`:** before the existing `current + qty > max` check, `if current > max` → the over-limit line and return. The existing qty-variant strings are otherwise unchanged.
3. **Single-corpse loot in-loop gate:** `if current > max` → the over-limit line (break as today); else the existing line.
4. **`sweep_corpses` in-loop gate (`loot_utils.py`):** same split as site 3. This covers typed `loot`, `loot all`, and plunder in one edit.

### Step 4 — the stranding warn

New private consumer helper (suggested: `async def _warn_if_over_capacity(self, char)`): fetch `await self.get_carry_counts(char)`; if `current > max`, output warn:

```
You're over your carry limit ({current}/{max} items) — you can't pick up, loot, or buy anything until you're under it.
```

**Call it in exactly three completion paths, after the action's success output and immediately before `send_status_refresh()`:**

1. `cmd_unequip` success path (after the `You unequip ...` line — claim 8).
2. `cmd_equip` free-slot branch (after the `You equip ...` line — claim 10).
3. `cmd_equip` auto-swap branch (after the `You equip X, replacing Y.` line — claim 10).

**Semantics (ruled):** the warn renders whenever the completed action leaves the character strictly over capacity — the stranding action itself, and any subsequent equip/unequip performed while still over (a deliberate restatement; the state must be unmissable). It never renders at or under capacity, so normal play never sees it. The free-slot-equip call site is deliberate uniformity: equip lowers load and normally raises capacity, so it fires only when the character remains over (or gear sums negative).

The bag guard and `_unequip_blocked_reason` are **not modified** — a bag unequip that would strand still refuses with its existing string before any of this runs.

### Step 5 — tests (`tests/test_v25_13_brief1.py`)

New file, covering at minimum:

1. Unequip of stat-granting gear that strands → action succeeds, warn line present with exact numbers, character over capacity afterward.
2. Auto-swap that strands (equip a lesser item displacing +STR gear) → swap sentence + the warn.
3. Unequip that lands at or under capacity → **no** warn line.
4. While over capacity: pickup, buy, single-corpse loot, and sweep loot each refuse with the exact over-limit string (four assertions, one per site).
5. At exactly full (`current == max`): pickup and buy keep their existing refusal strings (no over-limit line).
6. Count basis (#319): a character with equipped items does not have them counted — with `U` unequipped, `E > 0` equipped, and capacity `M` where `U < M ≤ U + E`, pickup succeeds (the old all-items count would have refused).
7. Bag guard regression: a bag unequip that would strand still refuses with the existing `"You're carrying too many items to remove your ..."` string, and no stranding warn is emitted.
8. Recovery: re-equipping the stat gear from the over state, landing under capacity → no warn, and acquisition succeeds again.

Update `tests/test_gear_combat.py:134` per Step 2. No other existing tests pin the touched strings against the over state (the over state was previously unreachable in tests without stat-gear stranding); if the suite surfaces a pinned string this analysis missed, record it as a deviation and convert with intent preserved, per the standing test-hygiene rule.

### Step 6 — verification

- Full suite, in-container, the only working form: `python manage.py test apps/shyland/tests` (directory-path form via `docker exec` in the django container). Expected: **915 + the new test count, zero failures.**
- `make deploy-dev` from the worktree once green.

### Step 7 — operator playtest checklist (dev stack)

Ready after Step 6's deploy. If the test character lacks suitable gear, **gift via the shell helper** (`generate_item_instance(definition, mk_tier, rarity, owner=character)`) — never the admin add form.

1. Equip +STR gear, then fill the inventory to at or near the (raised) capacity — `inv` header shows the numbers.
2. `unequip` the +STR item → the unequip succeeds **and** the warn line renders with the numbers; `inv` header now shows over-limit numbers (e.g. `443/408`).
3. `pickup` anything → `You're over your carry limit. (N/M items)`.
4. `buy` from a vendor → same line. Kill something and `loot` → same line.
5. Re-equip the +STR gear → no warn (back under); pickup/loot/buy work again.
6. Auto-swap: while near-full, equip a weaker same-slot weapon → the replacing sentence plus the warn.
7. Bag regression: with load above what capacity-without-the-bag would allow, `unequip <bag>` → the existing refusal (no unequip, no warn).
8. Numbers agreement (#319): with gear equipped, the `inv` header's `(current/max)` and any refusal's `(current/max)` are the **same numbers** — previously they disagreed by the equipped count.

### Step 8 — close the issues

Close **#275** and **#319**, gated on Step 6 passing (suite green + dev deploy done).

### Step 9 — architecture doc (LAST; gated)

This step is gated on all implementation and verification steps above being complete and passing. `Shyland_Architecture_v25.md`, updated in place per the point-release rule:

- Header: new **Version 25.13** paragraph in the house style (the ruling, the four refusal sites, the warn semantics, the #319 unification and `get_carry_capacity` retirement, suite delta). Stamp `25.12 → 25.13`; **the hash moves** (architectural change: a consumer DB-helper retired, refusal semantics changed across the consumer and `loot_utils`) to the release's final code commit.
- Body, the verified surfaces: the `carry_capacity` helper bullet region (~`:991` — note `get_carry_counts` as the single load counter and the outlier's retirement), the `buy` command checks paragraph (~`:730`), and the pickup/loot/unequip flow text wherever the old capacity behavior is described. Locate exactly at write time.

## 4. Closeout report

Standard form: `.txt` in `docs/shyland/`, stub pushed at session start (Step 0 of the implementation ritual), completed in place at the end — including the final commit hash and the operator playtest disposition line (#170).
