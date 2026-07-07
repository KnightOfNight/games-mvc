# Shyland v18 Brief 1 Closeout — Notes for the Design Chat

Source: the Claude Code session that implemented v18 Brief 1 (Mk 1 Item Kit, Leather).
Status: implemented, all verification steps pass, committed and pushed. Architecture
doc is now `Shyland_Architecture_v18.md`, header hash `b2d0914`; it will be updated
in place by subsequent v18 briefs.

## What shipped

Exactly what the brief specified: `ItemDefinition.suppress_mk_suffix` (migration
0018), the `get_display_name_with_tier()` helper as the single source of truth for
name-plus-tier display, the general equip exchange rule (auto-swap / refusals /
two-handed hands-claim / unequip-constraint deferral), and the Part D seed data
verbatim — leather set, Wooden Shield, Iron Mace, Broadsword, Battle Axe, Hunting
Bow, 12 copper accessories, with the legacy `copper-ring` absorbed in place as
Copper Ring of Wisdom. No zone content. Pulse Pistol untouched; Leather Vest
verified byte-identical. All worked-case rows in the brief's Part C table behave
exactly as specified, including the curse-blocked swap.

## Flagged items

1. **The brief's item arithmetic is off by one.** The Context section says "23
   net-new seed rows" and "5 weapons"; Part D defines **4** weapons and yields
   **22** net-new rows on an existing database (the 12th accessory is the
   *absorbed* legacy ring — renamed, not created). Verification step 2's
   "increased by exactly 23" is therefore unsatisfiable as written; actual result
   was 11 → 33 (+22), second run creates 0, no `copper-ring` remains. Part D was
   implemented verbatim per Design Rule 6 ("do not invent or add items"). **If a
   fifth weapon was intended, it never made it into Part D and needs a follow-up
   brief.** If not, it was just a miscount and nothing is missing.

2. **Two ring slots did not exist in the code — they do now.** The brief's worked
   cases assume a character can wear two rings ("both RING slots are full",
   "equips into free RING slot"), but the v17 code had a single RING slot. Brief 1
   added a slot-capacity mechanism (`SLOT_CAPACITY = {'RING': 2}`; every other
   slot holds one). If the GDD doesn't already state that characters have exactly
   two ring slots (and one of everything else), it should record it.

3. **Non-ring ambiguous-refusal wording was authored, not specified.** The brief
   gave exact text only for the ring case ("Both ring slots are full — unequip
   your X or your Y first."). The generic ambiguous case (e.g. a knife with both
   hands full of different items) shipped as: `You'd have to unequip your Iron
   Sword or your Wooden Shield first.` — same shape as the multi-item refusal but
   with "or". Multi-item refusals join with "and" (Oxford comma at 3+).

4. **Eleven accessory descriptions were authored in-session** following the one
   given example's register (plain copper band / copper pendant on a leather
   cord, faintly warm, one concrete image of the stat's effect, no proper nouns).
   They live in `seed_world.py` — worth a read if the design chat wants to adjust
   any wording; accessories re-seed via `update_or_create`, so edits propagate.

5. **Admin visibility fix beyond the brief's text.** `ItemDefinitionAdmin`
   declares explicit fieldsets, so the new `suppress_mk_suffix` field would have
   been invisible in Django admin; it was added to the Identification fieldset.
   No design impact.

6. **Scope line drawn on Mk formatting:** model `__str__` methods and tick-engine
   log lines still say "Mk N" — they are admin/debug representations, not
   player-facing display names, and deliberately do not use the helper. Every
   player-facing site goes through `get_display_name_with_tier()`.

## Environment note (no design impact)

The dev database was found completely wiped at session start (volumes had been
dropped ~2 days earlier without re-running migrate/seed; the ticker container was
crash-looping as a result). A clean v17 baseline was rebuilt before implementation
and doubled as the "existing database" for the idempotency verification. Any dev
accounts/characters were already gone before this session.
