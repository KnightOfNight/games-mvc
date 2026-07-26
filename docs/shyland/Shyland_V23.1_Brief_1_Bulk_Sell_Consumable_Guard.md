# Shyland V23.1 Brief 1 — Bulk-Sell Consumable Guard (#150)

- **Produced by:** the Version 23.1 design session, 2026-07-26 (branch `version_23_1`)
- **Milestone:** Version 23.1 (point release — scope law: one bucket B1, one implementation brief, one founding ticket)
- **Founding ticket:** #150 (`emergent`, `triaged`, ruling + precision recorded as issue comments 2026-07-26)
- **GDD:** ruling already landed on this branch (commit `978a493`) — §9.1 footnote 19, §9 grammar/response-doctrine notes, §6 vendor-commands bullet, all marked "(v23.1, pending implementation)". Marker removal is design-session work; do not touch GDD source.
- **Pre-flight (deploy-time actions ledger):** no prior pending deploy-time actions are outstanding — v23 closed clean (PR #153 merged 2026-07-25; all v23 deploy-time actions confirmed executed).

## Problem

`sell all <rarity>` (e.g. `sell all common`, the inventory-dump workhorse) includes every potion the player owns. It is far too easy to walk out of a vendor stop with zero Healing Draughts. The v23 stacking work made hauling hoards tidier, which increases the dump temptation; sell resolution is deliberately stacking-agnostic, so display grouping offers no protection.

## The ruling (law — do not deviate)

Operator-confirmed 2026-07-26 on #150 (Option 3 — grammar-level exclusion):

1. **Guarded form: exactly the noun-less `sell all <rarity>`.** Bare `sell all` remains refused with the v22 teaching wording (§9.1 footnote 17) — this release does **not** legalize it. Every noun-carrying form (`sell all draught`, `sell 5 draught`, `sell draught`, `sell all common draught`) bypasses the guard and reaches consumables normally. `drop` is untouched.
2. **Excluded type: `consumable` only** (`ItemDefinition.CONSUMABLE`). Materials, readables, and keys stay bulk-sellable. The existing equipped-items exclusion and rarity-aware lowest-first selection order are unchanged. (Seed audit: the guard touches exactly three definitions — Healing Draught, Focus Tonic, Repair Kit.)
3. **Announced, not silent.** When a noun-less bulk sell skips consumables, the sell output carries **one** note line (warn-color) after the sale lines, teaching the named form. When the noun-less bulk sell's matches are *all* consumables, the command is refused as a world-declined response (warn-color) — nothing sold, not a bare "nothing to sell."
4. **#138 compatibility preserved.** Zero-value disposal is unaffected for non-consumable junk; consumable junk still exits via the named-noun form. The guard narrows *default* reach, not sellability. The worthless-sell (Artifact no-leak) refusal is untouched.

## Authored wording (use verbatim — authored by the design session under creative policy)

- Skip note line (warn-color, one line, after the aggregated sale lines):
  `Your consumables stay in your pack — name them ('sell all draught') to sell them.`
- All-consumables refusal (warn-color, nothing sold):
  `That's all consumables — name them ('sell all draught') if you mean to sell them.`

## Implementation

1. **Version constant.** This is the release's only implementation brief: bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` from `"23.0"` to `"23.1-DEV"` as the first code change. (The closeout ritual moves it to `"23.1"`.)
2. **The guard.** Apply the consumable-type exclusion at candidate-pool construction for the sell command's noun-less bulk path — the rarity-filtered, no-noun-token branch only. Relevant sites: the shared resolver's bulk path in `django/src/apps/shyland/command_grammar.py` (the sell spec is at ~line 228, `bare_all_msg` at ~line 234; the explicit-`all`-no-noun branch at ~line 441) and `cmd_sell` in `django/src/apps/shyland/consumers.py` (~line 1995). The implementation session chooses the exact choke point, but the guard must run **before** value math and selection, and must key on the *absence of a noun token*, never on what the noun matched.
3. **Output.** Successful guarded sells keep the v22 count-form aggregation exactly as-is (one count-form line per definition, total money, warm shortfall notes preceding); the skip note is one additional warn line after them. The all-consumables refusal replaces the transaction entirely.
4. **No model changes → no migration.** State in the closeout that no migration was created.
5. **No seed changes → PENDING DEPLOY-TIME ACTIONS: none.**
6. Tab completion is unaffected (noun pools don't change; the guard alters only noun-less selection).

## Tests

Add coverage (in `django/src/apps/shyland/tests/`), at minimum:

- Mixed inventory (draughts + hides + unequipped gear): `sell all common` sells the non-consumables, keeps every consumable, emits exactly one skip note line at warn.
- Consumables-only match: `sell all common` refuses (warn), sells nothing, wallet unchanged.
- Bypass forms: `sell all draught`, `sell 5 draught`, `sell draught` still sell consumables; `sell all common draught` (rarity + noun) sells common draughts.
- Bare `sell all` still returns the v22 teaching refusal verbatim.
- #138 regression: bound zero-value non-consumable junk still bulk-sells for 0 copper.
- Materials unaffected: hides/carapaces still included in `sell all common`.

Existing sell tests must not be weakened. If any literal-pinning test collides with the new note line, apply the standing conversion rule (pool-membership / intent-preserving assertions) and report it as a deviation in the closeout. The full suite must pass (v23 baseline: 354; expect net additions only).

## Verification (all must pass before closing #150)

Run in the dev stack (`make deploy-dev` or `make build && make restart`), with a test character:

1. Stock inventory with Healing Draughts, Animal Hides, and unequipped common gear → `sell all common` → gear and hides sold (count-form lines), draughts remain, one skip note line present.
2. Inventory holding only common draughts → `sell all common` → authored refusal, zero sales, copper unchanged.
3. `sell all draught` → all draughts sold.
4. Bare `sell all` → `Sell all of what? Try 'sell all <item>' or 'sell all <rarity>'.`
5. Full test suite green.

Close #150 only after all verification steps pass.

## Architecture doc (LAST, gated)

This step is gated on all implementation and verification steps above being complete and passing.

Point release: **update `Shyland_Architecture_v23.md` in place — never create a new file.** The stamp moves to **23.1**; the header hash **moves** (this is an architectural point release — code changed). Sections that change, exactly:

- **Header block** — new commit hash + one-line v23.1 summary (bulk-sell consumable guard, #150).
- **§4.3, "The sell partition (v23 brief 4, #138)"** — add the consumable guard to the sell-partition description (or an adjacent v23.1-labeled subsection if cleaner), including the two authored lines and the noun-less-only scope.
- **§4.14, Command layer** — the resolver's bulk-form policy and the response-layers list gain the guard and the consumables-only refusal.

## Deploy (operator-authorized, in-session)

- Exactly `make deploy-prod` — never hand-rolled. It refuses to run if a `DOCKER_HOST` is already in the environment (investigate stale state, don't inherit it). If it fails partway, `.env` deliberately remains in prod posture — report that state, never repair it silently.
- No deploy-time data actions for this brief.

## Ready after deploy — operator playtest checklist

1. At a vendor with potions + hides + junk gear in inventory: `sell all common` — confirm gear and hides sell, potions stay, and the skip note reads correctly in the pane (warn-color).
2. With only potions matching: `sell all common` — confirm the refusal line, nothing sold.
3. `sell all draught` — confirm potions sell when named.
4. Bare `sell all` — confirm the v22 teaching refusal is unchanged.
5. Starter-kit junk dump still works end-to-end (#138 path).
6. `help` output shows `Version: 23.1-DEV` (until closeout stamps 23.1).

## Closeout

Standing process applies (Step 0 stub + push as the work-started signal; commit/push at every step boundary; branch `version_23_1` only, never merge). The closeout report records: no migration created, no deploy-time actions pending, actual-vs-expected test counts, any test-conversion deviations, and the final commit hash.

End by: **run the issues report.**
