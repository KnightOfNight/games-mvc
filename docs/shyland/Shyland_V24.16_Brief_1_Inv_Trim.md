# Shyland V24.16 — Brief 1: Inv Trim (#208)

- **Release:** Version 24.16 (milestone #36) — founding ticket **#208**, no dependencies
- **Branch:** `version_24_16` (cut from main `be0ab01`, the 24.15 merge)
- **Produced by:** the V24.16 design session, 2026-08-07; ruling recorded on #208 the same day
- **GDD doctrine (already committed on this branch, `43eae4f`):** §6.11 single-table render, §9.1 footnote 21 re-anchor, §9 shipped-surfaces line — all carrying `(v24.16, pending implementation) (#208)` markers. Implementation sessions never edit GDD source; the markers are swept at closeout.

## Pre-flight

- Session type: **implementation**, on a worktree of `version_24_16`. Run the standard hard pre-flight (`python3 scripts/check_docker_host.py` — exit 0, local dev) and verify this brief exists verbatim at the branch tip.
- **Step 0 (verify-and-signal):** create `docs/shyland/Shyland_V24.16_Brief_1_Closeout.txt` as a stub (one-line session-start record: date, brief name, branch), commit, push immediately. Completed in place at closeout.
- **Prior pending deploy-time actions: none.** V24.15 was runtime-only with an empty tail; V24.14's production seed executed at its closeout tail. No open PENDING DEPLOY-TIME ACTIONS blocks exist anywhere.
- Commit and push at every step boundary — branch only, never merge to main.

## Scope and shape

Runtime code only — `django/src/apps/shyland/consumers.py` plus tests. **No model changes, no migration, no seed changes, no data actions. Expected deletions: 0** (no seed-owned replacement runs). The architecture doc hash **moves** (output-composition change; v24.7/v24.8 precedent).

**Design rules that must not be deviated from:**

1. `inv` / `inventory` renders the **Inventory table only**: the `Inventory (N/M)...` header plus the `Slot / Name / Quantity / Details` table, flat alphabetical by name. No Equipment paper-doll section, no wallet line, no leading blank line — the header is the first line of the render.
2. **The equipped-items query stays.** Capacity is unchanged: effective STR (base + gear, #100) × 10 + equipped-bag `carry_bonus`. The equipped set keeps informing the numbers without being displayed.
3. **`_equipment_doll_lines` and `_wallet_line` are NOT deleted.** Bare `equip` (#195) becomes the paper-doll helper's sole consumer; `wallet` keeps its shared renderer. Neither command's output changes by one byte.
4. Stacking (#18), sorting, the Slot cell (#197/#194), and the Details cell are untouched — the table rows render exactly as today.
5. Report category (unstamped) unchanged.

## Step 1 — Version start (opening act, own commit)

First brief of the release: bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` from `"24.15"` to `"24.16-DEV"`, moving the pin test in the same commit (`django/src/apps/shyland/tests/test_b2_amendment1.py`, the `assertEqual(SHYLAND_VERSION, '24.15')` assertion → `'24.16-DEV'`). Then the version-start `make deploy-dev` from the worktree.

## Step 2 — Implementation (`django/src/apps/shyland/consumers.py`)

In `cmd_inventory` (~line 967):

- Remove the paper-doll block: the `lines = self._equipment_doll_lines(equipped)` call and the blank-line separator that currently precedes the `Inventory (N/M)...` header (`lines.append({})`). The render now starts with the header.
- Remove the wallet tail: the `get_character_fresh()` call, the blank-line separator, and the `_wallet_line` append.
- Keep everything else: `get_inventory()`, the equipped/unequipped split, `bag_bonus`, `max_carry`, `current_carry`, the header, the sort, the stacking walk, `_table_lines`, and the send.

Help text (~line 1076): the `('inventory (inv)', 'inventory', 'Show your equipment, inventory, and wallet.')` tuple's description becomes `'Show your inventory.'`

## Step 3 — Tests

- **`tests/test_v24_7_brief1.py`** — `test_bare_equip_matches_inv_paper_doll_byte_identical` loses its oracle (inv's doll block no longer exists). Convert: compare bare `equip` output against `_equipment_doll_lines(equipped)` rendered directly — original intent (the paper-doll composition is pinned as bare `equip`'s exact render) preserved as explicit assertions. Update the module docstring's "shared composition inv" line. **Report this conversion as a deviation-style note in the closeout** per the standing test-hygiene rule.
- **Tests that parse `cmd_inventory` output** — `tests/test_b2_amendment1.py::test_inventory_slot_cell_populated`, `tests/test_v24_8_brief1.py::DualSlotInventoryTests`, `tests/test_data_integrity.py::InventoryStackingTests` (`_inventory_rows`): update section-locating / row-index logic for the new single-table shape as needed; every assertion's intent unchanged.
- **New `tests/test_v24_16_brief1.py`** pinning the doctrine, with gear + items + a bag equipped where relevant:
  1. `inv` output's first line is the `Inventory (N/M)...` header (no leading blank, no `Equipment...` header anywhere).
  2. No paper-doll rows: with an item equipped, no slot-label rows render and the equipped item's name is absent from the output.
  3. No wallet line: no `Wallet` key in any line.
  4. The header's capacity still reads effective STR + bag bonus (equip a bag, assert M includes `carry_bonus`; the equipped query is alive).
  5. The help table's `inventory (inv)` row reads `Show your inventory.`
- **Full suite in-container** (the only working form, via `docker exec` in the django container): `python manage.py test apps/shyland/tests`. All tests pass.

## Step 4 — Dev deploy

`make deploy-dev` from the worktree once implementation and verification pass.

## Step 5 — Operator playtest checklist (dev stack)

1. `inv` with items carried and gear equipped: single Inventory table, sane `(N/M)` header, no Equipment section, no Wallet line.
2. `equip` (bare): the paper-doll renders unchanged — 14 rows, consumed-hand rendering intact.
3. `wallet`: money line unchanged.
4. Equip then unequip a bag: `inv`'s header M rises and falls by the bag's carry bonus.
5. `help`: the `inventory (inv)` row reads "Show your inventory."; the Version line reads `24.16-DEV`.
6. Stacked consumables still fold into Quantity; a bound and an unbound stack still render as two rows.

## Step 6 — Architecture doc (LAST, gated)

This step is gated on all implementation and verification steps above being complete and passing. `docs/shyland/Shyland_Architecture_v24.md`, updated in place — stamp **24.16**, header hash **moves** to the release's code commit. Exactly these changes:

1. The header note gains the v24.16 entry (per-release blockquote, matching the v24.7/v24.8 form): the inv trim — `cmd_inventory` renders the Inventory table alone; paper-doll owned by bare `equip`, money line by `wallet`; equipped query retained for capacity; runtime code only.
2. §4.3's "Changed in ..." run gains a v24.16 sentence.
3. §4.3's equipment-display subsection (v24.7 — the sentence "`cmd_inventory` and bare `equip` are its only callers, so the two renderings can never drift"): updated — bare `equip` is the sole caller since v24.16 (#208).
4. Any other **present-tense current-state claim** of the three-part composite gets a trailing "(until v24.16 — #208 …)" parenthetical; historical brief narratives (v19 wallet section, v22 standards paragraph) stay as history, unrewritten.

No other sections change.

## Step 7 — Closeout

Complete `docs/shyland/Shyland_V24.16_Brief_1_Closeout.txt` in place: final commit hash, the test-conversion note, **PENDING DEPLOY-TIME ACTIONS: none**, and the operator playtest disposition line (verbatim-style, per #170). Close #208 gated on verification passing. End with the `implementation-session-end` ritual (disposition gate first; issues report as the formal end artifact).
