# Shyland V24.7 Brief 1 — Equipment Display

**Release:** Version 24.7 (milestone `Version 24.7`) · **Branch:** `version_24_7`
**Founding ticket:** #195 (bare `equip` equipment view) · **Dependencies:** #176 (consumed hand slots), #194 (handed-ness disclosure)
**Design session:** 2026-08-02 — all rulings operator-confirmed; recorded on the three issues. GDD text landed on this branch (commits `154e03d`, `c62100e`) with `(v24.7, pending implementation)` markers.

This is the **only planned brief** for Version 24.7 and the **first implementation brief of the release** — the version-start ritual below applies.

---

## 0. Scope and design law

Three display/communication defects, one theme: **the display never says "two-handed" and never shows its consequences.** Zero mechanics changes — the equip resolver, hand-claiming rules (#178 semantics), auto-swap/refusal logic, and all state gates except the one named in §4 below are untouched. Any behavior difference beyond output composition is a defect.

Authoritative GDD text (already on this branch): §3.6 (Handedness disclosure doctrine), §6.11 (paper-doll consumed rows; shared composition; inventory Slot-cell word), §9.1 (chart cell `equip 4 · 21`, footnote 21, state-gating matrix amendment, §9.2 superseded-verb parenthetical). Where this brief and the GDD disagree, the GDD wins; where a data table and prose disagree, the table is authoritative.

Model facts (no model changes, **no migrations**, no seed-data changes in this brief):

- `ItemDefinition.is_two_handed` — existing `BooleanField`; the only handed-ness source of truth.
- Hand-claiming invariant (existing mechanics, rely on it): a two-handed item claims MAIN_HAND and OFF_HAND from any slot it occupies; equipping any two-hander displaces every other two-hander — therefore **at most one two-handed item is ever equipped**.

---

## 1. Version start (opening act — standing requirement)

1. Bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` from `"24.6"` to `"24.7-DEV"` in **its own commit**, moving the pin test in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py:118` asserts `'24.6'` → `'24.7-DEV'`.
2. Run `make deploy-dev` from the worktree (the version-start deploy).

---

## 2. Shared paper-doll composition + bare `equip` (#195)

**Extract the paper-doll block** from `cmd_inventory` (`django/src/apps/shyland/consumers.py`, the `Equipment...` header + `Slot / Name / Details` table built over `SLOT_ORDER`/`SLOT_CAPACITY`) into one helper (suggested name `_equipment_doll_lines(equipped)`) returning the composed lines. `cmd_inventory` calls it; bare `equip` calls it. **One composition, two callers — no duplicated row-building code may remain.**

**Bare `equip`:** in `cmd_equip`, before the resolver runs, a bare invocation (no arguments after the verb, whitespace-insensitive) renders the paper-doll block and returns:

- Output is the paper-doll block **only**: the `Equipment...` header plus the 14-slot table. **No inventory table, no carry count, no wallet line** (operator-pinned exclusion).
- Sent as a **report** (`send_report_lines` — unstamped on the client, never varies), exactly like `inv`'s rendering.
- Targeted `equip <item>` behavior is byte-identical to today in every path (resolution, auto-swap, refusals) except the refusal-clause change in §3.3.

**Chart-derived surfaces:** `equip`'s usage string in `help` follows the new chart cell (`4 · 21` — target optional): `equip [item]`. Tab completion is unchanged (the noun pool still completes; a bare line is simply a valid command now).

---

## 3. The three disclosure surfaces

### 3.1 Consumed hand slots name their consumer (#176)

In the shared paper-doll helper: a MAIN_HAND or OFF_HAND row with no direct occupant, while a two-handed item is equipped in **any other slot**, is a **consumed row**, not an empty row:

- **Name cell:** the consuming item's name-with-tier (`get_display_name_with_tier`), rendered **muted** (plain text in the muted style — not the item's normal colored composition).
- **Details cell:** `(two-handed)`, muted.

Cases (these two examples are normative):

```
Main hand   Battle Axe Mk 1        100%, Uncommon, Bound
Off hand    Battle Axe Mk 1        (two-handed)
```

Battle Axe in MAIN_HAND: its own row is the home row (normal rendering, real Details); OFF_HAND is the consumed row. Hunting Bow in RANGED: RANGED is the home row; **both** MAIN_HAND and OFF_HAND are consumed rows. Genuinely free slots keep the muted `-` exactly as today. Slots other than the two hand rows never render as consumed (RANGED itself is never claimed — #178).

### 3.2 Handed-ness in item presentation (#194)

- **Examine:** in `_format_identified_item_lines` (`consumers.py`), every item with `item_type == 'weapon'` gains a `Hands:` row — value `Two-handed` when `is_two_handed`, else `One-handed` — placed immediately after the `Damage:` row (or after `Genre:` if no damage row), label-aligned with the adjacent rows. **Both values always render** — never suppress `One-handed`.
- **Listing tables:** in `_slot_cell` (`consumers.py`), when the definition is a weapon with `is_two_handed`, the Slot cell reads `<Slot name> (two-handed)` — e.g. `Ranged (two-handed)`, `Main hand (two-handed)`. Every caller of `_slot_cell` (inventory table, vendor listings) inherits automatically; do not special-case call sites.

### 3.3 Hands-conflict refusals explain themselves (#194)

In `cmd_equip`'s refusal paths (`You'd have to unequip {names} first.` — both the `min_size >= 2` form and the ambiguous-`or` form): when the displacement involves hands claimed by (or needed for) a two-hander, replace the terminal period with an explanatory clause naming the two-handed item via `item_ref`:

```
You'd have to unequip Iron Mace Mk 1 and Wooden Buckler Mk 1 first — the Battle Axe Mk 1 needs both hands.
```

- The named item is **the two-handed item creating the conflict**: the incoming item if it is two-handed; otherwise the equipped two-hander in the displacement set.
- Refusals with no two-hander involved keep their current wording byte-identical, including the both-rings line (`Both ring slots are full — …`).
- Warn category unchanged; auto-swap success sentences unchanged.

---

## 4. Combat gating (#195 addendum, operator-ruled)

**Bare `equip` is allowed in combat; targeted `equip` keeps the standing combat refusal unchanged.** The gate follows the act, not the verb: the bare form is an information rendering, and the same rows are already visible in combat via `inv`. Implement the bare-form check ahead of the combat gate for this verb (or equivalently scope the gate to targeted invocations) — whichever matches the existing gate structure with the smallest diff.

---

## 5. Verification (all steps must pass before issue closure)

**In-container suite** (the only working invocation form):

```
docker exec <django container> python manage.py test apps/shyland/tests
```

New tests (suggested file `tests/test_v24_7_brief1.py`) covering at minimum:

1. Bare `equip` returns the paper-doll block only — asserts the `Equipment...` header and 14 slot rows present; asserts **no** `Inventory (` header and **no** wallet line in the payload.
2. Bare `equip` output is byte-identical to the paper-doll block `inv` renders for the same character (the shared-composition guarantee).
3. Two-hander in MAIN_HAND → OFF_HAND row shows the consumer's name-with-tier and `(two-handed)`; two-hander in RANGED → both hand rows consumed; no two-hander → hand rows show muted `-`.
4. Examine on a two-handed weapon shows `Hands:` = `Two-handed`; on a one-handed weapon `One-handed`; on armor no `Hands:` row.
5. `_slot_cell` for a two-handed weapon reads `<Slot> (two-handed)`; unchanged for one-handers and non-weapons.
6. Hands-conflict refusal carries the `— the <item> needs both hands.` clause; a non-hands refusal (three-rings case) is byte-identical to the current wording.
7. In combat: bare `equip` renders the paper-doll; `equip <item>` still refused with the standing combat line.
8. The version pin test asserts `24.7-DEV` (moved in the §1 commit).

**Test hygiene:** existing tests that literal-pin the paper-doll's empty hand rows, `equip` usage strings, or refusal wording convert with original intent preserved as explicit assertions — report each conversion as a deviation in the closeout, never silently.

**Dev deploy (standing requirement):** once implementation and verification pass, run exactly `make deploy-dev` from the worktree.

**Deploy-time data actions: none.** No migrations, no seed changes, no PENDING DEPLOY-TIME ACTIONS block.

---

## 6. Operator playtest checklist (dev stack, after `make deploy-dev`)

1. Equip a Battle Axe. `inv`: Off hand row reads `Battle Axe Mk 1  (two-handed)` muted; Main hand is the normal home row.
2. Equip a Hunting Bow (auto-swap from the axe). `inv`: Ranged is the home row; Main hand **and** Off hand both read `Hunting Bow Mk 1  (two-handed)` muted.
3. Bare `equip`: shows exactly the equipment paper-doll — no inventory table, no carry count, **no wallet**.
4. `examine` the bow: `Hands: Two-handed` row present. `examine` a one-handed weapon (e.g. Iron Mace): `Hands: One-handed`.
5. Vendor `list` and `inv` inventory table: two-handed weapons' Slot cells read e.g. `Ranged (two-handed)`.
6. With a one-hander + shield equipped, `equip` a two-handed axe: refusal ends `— the Battle Axe Mk 1 needs both hands.`
7. Enter combat: bare `equip` renders the paper-doll; `equip <item>` is refused with the standing combat line.
8. `help`: equip usage shows the optional target.

---

## 7. Architecture doc (final, gated step)

This step is gated on all implementation and verification steps above being complete and passing.

Update `docs/shyland/Shyland_Architecture_v24.md` **in place**:

- §4.3 (WebSocket consumer): the shared paper-doll helper, bare `equip` rendering, consumed-row composition, examine `Hands:` row, `_slot_cell` two-handed word, refusal clause.
- §4.14 (Command layer): `equip` chart cell `4 · 21`, footnote 21, the combat-gate scoping (bare form allowed).
- Stamp line → 24.7; **the hash moves** (this is an architectural point release — command behavior changed).

---

## 8. Closeout requirements

Closeout report `Shyland_V24.7_Brief_1_Closeout.txt` in `docs/shyland/` (stub created and pushed at Step 0 per the implementation-session skill; completed in place), including: deviations (test-hygiene conversions itemized), final commit hash, and the operator playtest disposition line. Close #195, #176, #194 (gated on verification passing). End with the `implementation-session-end` ritual — the issues report is the formal end artifact.
