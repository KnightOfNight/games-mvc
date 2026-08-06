# Shyland V24.11 — Brief 1: Knowledge by Holding (#80)

- **Date:** 2026-08-04 (V24.11 design session)
- **Branch:** `version_24_11`
- **Founding ticket:** #80 — Design: item identification visibility — knowledge by holding (milestone `Version 24.11`)
- **Ruling of record:** #80 comment, 2026-08-04 (V24.11 design session), building on the standing 2026-07-15 direction
- **GDD:** §6.8 (rewritten), §6.11 display rules, §12 future-systems row — landed on this branch at `faf3494` with `(v24.11, pending implementation — #80)` markers

## Pre-flight

- No prior pending deploy-time actions are outstanding: V24.10's production seed executed at its closeout tail via `make seed-prod` (confirmed in the V24.10 closeout — all seed checks passed).
- This brief has **no model changes, no migration, and no seed changes** — it is code-only. There is **no PENDING DEPLOY-TIME ACTIONS block**.

## Context

Identification today is a one-way trapdoor: drop flips `is_identified` False (`transfer_to_room`), nothing ever flips it back, and the identification service that was meant to was never built. The ruled fix makes knowledge a property of holding: **pickup identifies, drop re-veils, `examine` is close inspection that reveals real details without pickup.** Lasting mystery becomes exclusively `is_unidentifiable`.

The veil is the **drop mechanic**, not a ground-state invariant: seeded ground items (e.g. Convergence newbie gear) ship identified and stay identified. Do not touch seed data.

## Design rules — never deviate

1. `examine` changes **no state** — the reveal is output-only; the room listing keeps the mystery name until pickup.
2. The identify flip lives **only at the ownership-transfer choke points** — never in individual command handlers.
3. Both flips (identify on take, re-veil on drop) carry the `is_unidentifiable` guard: an unidentifiable item's `is_identified` is never written by either path.
4. The unidentified item line is mystery name + `[Bound|Unbound]` — **no info suffix of any kind**: no durability %, no BROKEN, no bag carry-bonus (operator-ruled: suffix presence partially reveals item nature).
5. Curse state is untouched by all of this — `curse_identified` gating (Section 6.7) is out of scope; examine's reveal never includes curse status.
6. Resolution and tab completion continue to match **visible** names only — a re-veiled ground item resolves by its mystery name; its real name must not resolve or complete (that would leak through the grammar).

## Implementation steps

### Step 0 (standing) — verify-and-signal

Confirm this brief exists verbatim at the `version_24_11` tip; create the closeout-report stub (`docs/shyland/Shyland_V24.11_Brief_1_Closeout.txt`, opening with the one-line session-start record), commit, push immediately.

### Step 1 (standing, opening act) — version constant

Bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` from `24.10` to `"24.11-DEV"` in its own commit, moving the pin-test assertion in the same commit. Then run the version-start `make deploy-dev` from the worktree.

### Step 2 — identify on take (the ownership-transfer flips)

Two sites in `django/src/apps/shyland/consumers.py`:

- `transfer_to_character` (~line 3921): after setting `owner`/`current_room`, add — if `not item.is_unidentifiable: item.is_identified = True` (covers `pickup`).
- `do_loot_item` (~line 4000): same flip before `item.save()` (covers corpse looting). Note this method composes its display name **before** the flip today (`name = get_display_name(item)`); after the flip the looted line should name the **real** item — compose the name **after** the flip so the player sees what they now hold. (The drop side already composes before transfer for the mirror-image reason — see the comment at ~line 1234.)

`transfer_to_room` (~line 3926) already re-veils with the correct guard — leave it as is.

### Step 3 — kill the info suffix on unidentified lines

- `django/src/apps/shyland/item_utils.py`, `get_item_suffix` (~line 210): return `''` when `not item.is_identified` (first line of the function). This removes durability, BROKEN, and bag carry-bonus from every `compose_item_line` site (inventory listings, ground listings, loot listings, examine headline) in one place.
- `django/src/apps/shyland/consumers.py`, `_details_cell` (~line 874): gate the durability segment (the `takes_durability_loss` block) on `item.is_identified` as well. Rarity is already gated; `Bound|Unbound` stays unconditional.

### Step 4 — examine is close inspection

In `cmd_examine`'s item branch (`consumers.py` ~line 1809):

- **`is_unidentifiable` items:** keep the mystery block, tightened to exactly: `compose_item_line(item)`, blank line, indented `get_display_description(item)`, then the existing no-method line (`No known method of identification will reveal its true nature.`). **Delete the `(You cannot determine anything further about this item.)` parenthetical** — that is the redundant-double-line cleanup from #80.
- **All other unidentified items:** render the full identified detail block, byte-identical to examining the item identified — set `item.is_identified = True` **in memory only** (no `.save()`, with a comment stating the reveal is output-only per #80) and call `_format_identified_item_lines(item)`.

No changes to `_format_identified_item_lines` itself, to NPC/corpse/player examine branches, or to the examine resolution pool.

### Step 5 — tests

New file `django/src/apps/shyland/tests/test_v24_11_brief1.py`. Required cases:

1. Pickup of an unidentified ground item flips `is_identified` True (DB-persisted).
2. Pickup of an `is_unidentifiable` item does **not** write `is_identified`.
3. `do_loot_item` flips `is_identified` True; the returned/looted name is the real name.
4. Drop re-veils: `transfer_to_room` flips `is_identified` False; unidentifiable guard holds.
5. `get_item_suffix` returns `''` for an unidentified durability-bearing item and an unidentified bag; unchanged output for the identified equivalents.
6. `_details_cell` omits the durability segment for an unidentified item; still emits `Bound|Unbound`.
7. Examine of an unidentified (non-unidentifiable) item outputs the real name-with-tier and stats, and **does not persist** the flip (`refresh_from_db` → still False); room listing composition still shows the mystery name.
8. Examine of an `is_unidentifiable` item outputs mystery name + description + no-method line, exactly one cannot-determine sentence, and never the real name.
9. Resolver: a re-veiled ground item resolves by mystery-name tokens; its real-name tokens do not resolve.
10. Round trip: identified item → drop → ground line is mystery name + `[Unbound]` only (no suffix) → pickup → real name-with-tier restored.

If any existing test pins the old examine parenthetical or unidentified-suffix behavior, convert it to the new contract and record the change as a deviation in the closeout (test-hygiene rule).

### Step 6 (standing) — dev deploy

`make deploy-dev` from the worktree once implementation and verification pass. Production is never deployed from an implementation session.

## Verification

- Full in-container suite — the only working form: `python manage.py test apps/shyland/tests` via `docker exec` in the django container. All tests pass, including the 10 cases above.
- Shell spot-check (dev stack, via `make shell`): create an ItemInstance with `is_identified=False` on a room floor; confirm `get_display_name` yields the mystery form, `get_item_suffix` yields `''`; simulate pickup via `transfer_to_character` logic and confirm the persisted flip.
- Closing #80 is **gated on the suite passing**.

## Operator playtest checklist (dev stack, after Step 6)

1. Drop a weapon with worn durability → room listing shows `an unidentified weapon  [Unbound]` — no durability, no rarity, no Mk tier.
2. `examine` it on the ground → full real details (name, Mk, damage, hands, durability, rarity flags); the room listing still shows the mystery name.
3. Pick it up → inventory shows the real name again; drop and re-pickup round-trips cleanly.
4. Drop a bag → ground line shows no carry-bonus suffix.
5. Tab completion on the ground item completes the mystery name; the real name neither completes nor resolves.
6. Loot a corpse → looted lines name real items and they arrive identified.
7. Normal play (buy, sell, inv, equip paper-doll) reads unchanged for identified items.

## Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. Update `docs/shyland/Shyland_Architecture_v24.md` **in place**: stamp `24.10 → 24.11`; the hash **moves** (this release ships code). Sections to update: the item display/identification passage (knowledge-by-holding choke points, the no-suffix veil rule, examine's output-only reveal) and the command-pipeline note for `examine`. No new files.

## Closeout

Complete the closeout-report stub in place (`docs/shyland/Shyland_V24.11_Brief_1_Closeout.txt`): steps executed, deviations, final commit hash, and the **operator playtest disposition** line (the closeout session reads this as a gate). Close #80 (gated on verification). Then run the issues report.
