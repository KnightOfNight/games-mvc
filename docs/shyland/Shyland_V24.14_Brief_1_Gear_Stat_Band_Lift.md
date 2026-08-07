# Shyland V24.14 — Brief 1: Gear Stat Band Lift (#130)

**Release:** Version 24.14 (milestone #34) · **Founding ticket:** #130 · **Branch:** `version_24_14`
**Produced by:** V24.14 design session, 2026-08-07. Ruling of record: #130 comment thread (operator-confirmed in-session).
**Change class:** seed-data-only retune — **zero runtime code changes, zero model changes, zero migrations.**

## 1. Context

Gear-rolled stat entries grow ~×1.28 per Mk band as seeded, while the numbers they compete against grow ~×1.75 per band (NPC HP by #104's shipped lift; NPC contest stats +25/band; player primaries 28→53→78 at band mid-levels). Flat effects (lifesteal, procs, +N stats) rot to noise by Mk 3. The #104 lift is linear in `mk_tier`, so it is expressible **exactly** in the shipped midpoint formula `base + factor × mk_tier`; this brief rewrites the seed curve literals so gear flats track the band. GDD §6 "The band lift" (committed on this branch, marked `(v24.14, pending implementation)`) is the doctrine; this brief implements it.

## 2. Binding design rules — deviations require a stop and an operator ruling

1. **Mk 1 midpoint preservation is absolute.** For every rewritten entry, `new_base + new_factor` equals the old `base + factor` exactly (same for floor pairs). The live Mk 1 world must be untouched.
2. **Class assignments:**
   - **Full band lift** (`new_base = 0.25 × m1`, `new_factor = 0.75 × m1`, where `m1 = old base + old factor`): the six primary stats (`str`, `dex`, `end`, `int`, `wis`, `per`), `lifesteal`, `electric_damage_bonus`, `physical_resist`, and the inert flats (`spell_damage_bonus`, `mana_regen`, `magic_resist`, `radiation_resist`).
   - **Half-power lift** (`new_base = 0.625 × m1`, `new_factor = 0.375 × m1`): the proc-factor family (`bleed_factor`, `stun_factor`, `poison_factor`, `flame_factor`) wherever authored — pool or primary, including the #127 identity-proc V curves.
   - **Floor pairs take the full lift** (`0.25 × f1` / `0.75 × f1`, `f1 = floor_base + floor_factor`): flame-projector 8.0/4.0 → **3.0/9.0**; dart-caster 5.0/3.0 → **2.0/6.0**.
   - **`crit_chance` entries are exempt** — byte-identical, do not touch.
3. **Out of scope — do not touch:** weapon damage curves (`scaling_base`/`scaling_factor` on any definition), `armor_base` values, `ARMOR_MITIGATION_K`, composite-strike slot factors, `item_utils.py`, `combat_utils.py`, and all runtime code. `_roll_stat` and `generate_item_instance` are correct as shipped.
4. **No instance backfill.** Already-rolled ItemInstances keep their values (drop-time snapshot doctrine). No `fix_zero_secondary_stats`-style command. (Dev-only: a handful of Mk 2 drops from the operator-kept Hollowcrown encounter may carry old-curve rolls — cosmetic, no action.)
5. **The table in §3 is authoritative.** If prose and table disagree anywhere, the table wins.

## 3. The retune table — every stat entry in `seed_world.py`

Edit `django/src/apps/shyland/management/commands/seed_world.py` so each definition's `primary_stats` / `secondary_stat_pool` entries carry the **New base/factor** values below (floats as written; trailing zeros optional). 146 entries total: 135 change, 11 `crit_chance` entries stay byte-identical.

| Definition | Entry | Stat | Old base/factor | New base/factor | Class |
|---|---|---|---|---|---|
| iron-sword | P | str | 3/1 | 1/3 | full |
| iron-sword | S | dex | 1/0.5 | 0.375/1.125 | full |
| iron-sword | S | crit_chance | 0.5/0.2 | 0.5/0.2 | exempt |
| iron-sword | S | bleed_factor | 0.3/0.1 | 0.25/0.15 | half-power |
| iron-sword | S | lifesteal | 0.5/0.2 | 0.175/0.525 | full |
| combat-knife | P | dex | 3/1 | 1/3 | full |
| combat-knife | S | str | 1/0.3 | 0.325/0.975 | full |
| combat-knife | S | crit_chance | 1/0.3 | 1/0.3 | exempt |
| combat-knife | S | bleed_factor | 0.5/0.2 | 0.4375/0.2625 | half-power |
| combat-knife | S | poison_factor | 0.5/0.2 | 0.4375/0.2625 | half-power |
| pulse-pistol | P | dex | 2/0.8 | 0.7/2.1 | full |
| pulse-pistol | P | per | 2/0.8 | 0.7/2.1 | full |
| pulse-pistol | S | crit_chance | 0.5/0.2 | 0.5/0.2 | exempt |
| pulse-pistol | S | electric_damage_bonus | 0.5/0.2 | 0.175/0.525 | full |
| pulse-pistol | S | per | 1/0.4 | 0.35/1.05 | full |
| apprentice-staff | P | int | 4/1.2 | 1.3/3.9 | full |
| apprentice-staff | S | wis | 1/0.5 | 0.375/1.125 | full |
| apprentice-staff | S | spell_damage_bonus | 0.5/0.2 | 0.175/0.525 | full |
| apprentice-staff | S | mana_regen | 0.5/0.2 | 0.175/0.525 | full |
| iron-mace | P | str | 3/1 | 1/3 | full |
| iron-mace | S | end | 1/0.4 | 0.35/1.05 | full |
| iron-mace | S | stun_factor | 0.5/0.2 | 0.4375/0.2625 | half-power |
| iron-mace | S | physical_resist | 0.5/0.2 | 0.175/0.525 | full |
| broadsword | P | str | 4/1.2 | 1.3/3.9 | full |
| broadsword | S | dex | 1/0.5 | 0.375/1.125 | full |
| broadsword | S | crit_chance | 0.5/0.2 | 0.5/0.2 | exempt |
| broadsword | S | bleed_factor | 0.5/0.2 | 0.4375/0.2625 | half-power |
| broadsword | S | lifesteal | 0.5/0.2 | 0.175/0.525 | full |
| battle-axe | P | str | 4/1.2 | 1.3/3.9 | full |
| battle-axe | S | crit_chance | 1/0.3 | 1/0.3 | exempt |
| battle-axe | S | bleed_factor | 0.8/0.3 | 0.6875/0.4125 | half-power |
| battle-axe | S | end | 0.5/0.2 | 0.175/0.525 | full |
| hunting-bow | P | dex | 2/0.8 | 0.7/2.1 | full |
| hunting-bow | P | per | 2/0.8 | 0.7/2.1 | full |
| hunting-bow | S | crit_chance | 0.8/0.3 | 0.8/0.3 | exempt |
| hunting-bow | S | per | 1/0.4 | 0.35/1.05 | full |
| hunting-bow | S | bleed_factor | 0.5/0.2 | 0.4375/0.2625 | half-power |
| flame-projector | P | per | 2/0.8 | 0.7/2.1 | full |
| flame-projector | P | flame_factor | 2/1 (floor 8/4) | 1.875/1.125 (floor 3/9) | half-power |
| flame-projector | S | per | 1/0.4 | 0.35/1.05 | full |
| flame-projector | S | crit_chance | 0.5/0.2 | 0.5/0.2 | exempt |
| dart-caster | P | dex | 2/0.8 | 0.7/2.1 | full |
| dart-caster | P | poison_factor | 2/1 (floor 5/3) | 1.875/1.125 (floor 2/6) | half-power |
| dart-caster | S | dex | 1/0.4 | 0.35/1.05 | full |
| dart-caster | S | crit_chance | 0.8/0.3 | 0.8/0.3 | exempt |
| leather-vest | P | end | 3/1 | 1/3 | full |
| leather-vest | S | str | 1/0.3 | 0.325/0.975 | full |
| leather-vest | S | dex | 1/0.3 | 0.325/0.975 | full |
| leather-vest | S | physical_resist | 0.5/0.2 | 0.175/0.525 | full |
| ballistic-jacket | P | end | 3/1 | 1/3 | full |
| ballistic-jacket | P | per | 1/0.4 | 0.35/1.05 | full |
| ballistic-jacket | S | physical_resist | 0.8/0.3 | 0.275/0.825 | full |
| ballistic-jacket | S | radiation_resist | 0.5/0.2 | 0.175/0.525 | full |
| ballistic-jacket | S | dex | 0.5/0.2 | 0.175/0.525 | full |
| leather-cap | P | end | 2/0.7 | 0.675/2.025 | full |
| leather-cap | S | per | 1/0.4 | 0.35/1.05 | full |
| leather-cap | S | physical_resist | 0.5/0.2 | 0.175/0.525 | full |
| leather-cap | S | int | 0.5/0.2 | 0.175/0.525 | full |
| leather-shoulders | P | end | 2/0.7 | 0.675/2.025 | full |
| leather-shoulders | S | str | 1/0.3 | 0.325/0.975 | full |
| leather-shoulders | S | physical_resist | 0.5/0.2 | 0.175/0.525 | full |
| leather-shoulders | S | end | 0.5/0.2 | 0.175/0.525 | full |
| leather-gloves | P | end | 2/0.7 | 0.675/2.025 | full |
| leather-gloves | S | dex | 1/0.4 | 0.35/1.05 | full |
| leather-gloves | S | crit_chance | 0.5/0.2 | 0.5/0.2 | exempt |
| leather-gloves | S | str | 0.5/0.2 | 0.175/0.525 | full |
| leather-belt | P | end | 2/0.7 | 0.675/2.025 | full |
| leather-belt | S | str | 0.5/0.2 | 0.175/0.525 | full |
| leather-belt | S | end | 1/0.3 | 0.325/0.975 | full |
| leather-belt | S | physical_resist | 0.5/0.2 | 0.175/0.525 | full |
| leather-leggings | P | end | 3/1 | 1/3 | full |
| leather-leggings | S | end | 1/0.4 | 0.35/1.05 | full |
| leather-leggings | S | physical_resist | 0.8/0.3 | 0.275/0.825 | full |
| leather-leggings | S | str | 0.5/0.2 | 0.175/0.525 | full |
| leather-boots | P | end | 2/0.7 | 0.675/2.025 | full |
| leather-boots | S | dex | 1/0.4 | 0.35/1.05 | full |
| leather-boots | S | end | 0.5/0.2 | 0.175/0.525 | full |
| leather-boots | S | physical_resist | 0.5/0.2 | 0.175/0.525 | full |
| wooden-shield | P | end | 3/1 | 1/3 | full |
| wooden-shield | S | physical_resist | 1/0.4 | 0.35/1.05 | full |
| wooden-shield | S | str | 0.5/0.2 | 0.175/0.525 | full |
| wooden-shield | S | magic_resist | 0.5/0.2 | 0.175/0.525 | full |
| worn-cudgel | P | str | 1.8/0.6 | 0.6/1.8 | full |
| patched-cap | P | end | 1.2/0.4 | 0.4/1.2 | full |
| threadbare-vest | P | end | 1.8/0.6 | 0.6/1.8 | full |
| mended-leggings | P | end | 1.8/0.6 | 0.6/1.8 | full |
| scuffed-boots | P | end | 1.2/0.4 | 0.4/1.2 | full |
| frayed-gloves | P | end | 1.2/0.4 | 0.4/1.2 | full |
| moth-eaten-shoulder-wrap | P | end | 1.2/0.4 | 0.4/1.2 | full |
| rope-belt | P | end | 1.2/0.4 | 0.4/1.2 | full |
| iron-shortsword | P | str | 2.7/0.9 | 0.9/2.7 | full |
| iron-shortsword | S | dex | 1/0.5 | 0.375/1.125 | full |
| iron-shortsword | S | crit_chance | 0.5/0.2 | 0.5/0.2 | exempt |
| iron-shortsword | S | bleed_factor | 0.3/0.1 | 0.25/0.15 | half-power |
| iron-shortsword | S | lifesteal | 0.5/0.2 | 0.175/0.525 | full |
| oak-round-shield | P | end | 2.7/0.9 | 0.9/2.7 | full |
| oak-round-shield | S | physical_resist | 1/0.4 | 0.35/1.05 | full |
| oak-round-shield | S | str | 0.5/0.2 | 0.175/0.525 | full |
| oak-round-shield | S | magic_resist | 0.5/0.2 | 0.175/0.525 | full |
| hunting-sling | P | dex | 1.8/0.7 | 0.625/1.875 | full |
| hunting-sling | P | per | 1.8/0.7 | 0.625/1.875 | full |
| hunting-sling | S | crit_chance | 0.8/0.3 | 0.8/0.3 | exempt |
| hunting-sling | S | per | 1/0.4 | 0.35/1.05 | full |
| hunting-sling | S | bleed_factor | 0.5/0.2 | 0.4375/0.2625 | half-power |
| quilted-jerkin | P | end | 2.7/0.9 | 0.9/2.7 | full |
| quilted-jerkin | S | str | 1/0.3 | 0.325/0.975 | full |
| quilted-jerkin | S | dex | 1/0.3 | 0.325/0.975 | full |
| quilted-jerkin | S | physical_resist | 0.5/0.2 | 0.175/0.525 | full |
| copper-ring-of-strength | P | str | 2/0.8 | 0.7/2.1 | full |
| copper-ring-of-strength | S | dex | 0.5/0.2 | 0.175/0.525 | full |
| copper-ring-of-strength | S | end | 0.5/0.2 | 0.175/0.525 | full |
| copper-ring-of-dexterity | P | dex | 2/0.8 | 0.7/2.1 | full |
| copper-ring-of-dexterity | S | str | 0.5/0.2 | 0.175/0.525 | full |
| copper-ring-of-dexterity | S | per | 0.5/0.2 | 0.175/0.525 | full |
| copper-ring-of-endurance | P | end | 2/0.8 | 0.7/2.1 | full |
| copper-ring-of-endurance | S | str | 0.5/0.2 | 0.175/0.525 | full |
| copper-ring-of-endurance | S | wis | 0.5/0.2 | 0.175/0.525 | full |
| copper-ring-of-intelligence | P | int | 2/0.8 | 0.7/2.1 | full |
| copper-ring-of-intelligence | S | wis | 0.5/0.2 | 0.175/0.525 | full |
| copper-ring-of-intelligence | S | dex | 0.5/0.2 | 0.175/0.525 | full |
| copper-ring-of-wisdom | P | wis | 2/0.8 | 0.7/2.1 | full |
| copper-ring-of-wisdom | S | int | 0.5/0.2 | 0.175/0.525 | full |
| copper-ring-of-wisdom | S | end | 0.5/0.2 | 0.175/0.525 | full |
| copper-ring-of-perception | P | per | 2/0.8 | 0.7/2.1 | full |
| copper-ring-of-perception | S | dex | 0.5/0.2 | 0.175/0.525 | full |
| copper-ring-of-perception | S | int | 0.5/0.2 | 0.175/0.525 | full |
| copper-amulet-of-strength | P | str | 2/0.8 | 0.7/2.1 | full |
| copper-amulet-of-strength | S | dex | 0.5/0.2 | 0.175/0.525 | full |
| copper-amulet-of-strength | S | end | 0.5/0.2 | 0.175/0.525 | full |
| copper-amulet-of-dexterity | P | dex | 2/0.8 | 0.7/2.1 | full |
| copper-amulet-of-dexterity | S | str | 0.5/0.2 | 0.175/0.525 | full |
| copper-amulet-of-dexterity | S | per | 0.5/0.2 | 0.175/0.525 | full |
| copper-amulet-of-endurance | P | end | 2/0.8 | 0.7/2.1 | full |
| copper-amulet-of-endurance | S | str | 0.5/0.2 | 0.175/0.525 | full |
| copper-amulet-of-endurance | S | wis | 0.5/0.2 | 0.175/0.525 | full |
| copper-amulet-of-intelligence | P | int | 2/0.8 | 0.7/2.1 | full |
| copper-amulet-of-intelligence | S | wis | 0.5/0.2 | 0.175/0.525 | full |
| copper-amulet-of-intelligence | S | dex | 0.5/0.2 | 0.175/0.525 | full |
| copper-amulet-of-wisdom | P | wis | 2/0.8 | 0.7/2.1 | full |
| copper-amulet-of-wisdom | S | int | 0.5/0.2 | 0.175/0.525 | full |
| copper-amulet-of-wisdom | S | end | 0.5/0.2 | 0.175/0.525 | full |
| copper-amulet-of-perception | P | per | 2/0.8 | 0.7/2.1 | full |
| copper-amulet-of-perception | S | dex | 0.5/0.2 | 0.175/0.525 | full |
| copper-amulet-of-perception | S | int | 0.5/0.2 | 0.175/0.525 | full |
| tarnished-band | P | str | 1.2/0.4 | 0.4/1.2 | full |
| cloudy-glass-pendant | P | str | 1.2/0.4 | 0.4/1.2 | full |

Entries: 146 total, 135 changed, 11 exempt-unchanged

## 4. Implementation steps, in order

**Step 0 (before anything):** verify this brief at the branch tip; create and push the closeout-report stub (`docs/shyland/Shyland_V24.14_Brief_1_Closeout.txt`, one-line session-start record) — the work-has-started signal.

**Step 1 — version constant (opening act, own commit):** bump `SHYLAND_VERSION` to `"24.14-DEV"`, moving the pin-test assertion in the same commit; then run the version-start `make deploy-dev` from the worktree.

**Step 2 — seed retune:** apply §3's table to `seed_world.py`. Nothing else in the file changes — no slugs, names, descriptions, `scaling_base`/`scaling_factor`, `armor_base`, durability tables, or pool membership.

**Step 3 — tests:**
- **Update pinned literals:** `tests/test_v24_10_brief1.py` asserts the flame-projector and dart-caster seeded entries verbatim (its local fixture around line 41, the invariant-checker triple around line 213, and the seeded-definition assertions around lines 252–301). Update those expected values to §3's table (flame `flame_factor` → `1.875/1.125`, floor `3.0/9.0`; dart `poison_factor` → `1.875/1.125`, floor `2.0/6.0`; secondary entries per table). Original intent (floors seeded, invariant enforced) is preserved — these are expected-value updates, not semantic changes. Grep the whole test tree for any other assertion pinning a **seeded** definition's curve values and update likewise; tests that build their own local ItemDefinitions are out of scope.
- **New test — the doctrine invariant** (`tests/test_band_lift.py` or similar): after `call_command('seed_world')`, iterate every ItemDefinition's `primary_stats` + `secondary_stat_pool` entries and assert (float tolerance 1e-6): proc-family entries satisfy `factor == 0.6 × base` (the half-power shape); `crit_chance` entries are exempt (assert they do NOT satisfy the full-lift shape — they keep shallow curves); every other entry satisfies `factor == 3 × base` (the full-lift shape); floor pairs satisfy `floor_factor == 3 × floor_base`. This pins the doctrine for future authored items, not today's literals.

**Step 4 — no migration:** model-free change; state this in the closeout.

**Step 5 — dev deploy + reseed (code first, data second):** `make deploy-dev` from the worktree (bakes the new seed into the image), then run the seed against the dev stack (`make seed`). **Expected deletions: 0** — this is a definition-field update pass; report actual against expected in the closeout. Note: the dev DB's operator-kept Hollowcrown Mk 2 RoomSpawn tweak (rows 141/142) is live-DB state — if the seed run reverts those rows to Mk 1, report it and restore the operator's tweak (mk_tier 2 on both rows) as part of this step; it is standing dev-only state for Phase 3 testing.

## 5. Verification (all must pass before #130 closes)

1. Full in-container suite, path form: `python manage.py test apps/shyland/tests` via `docker exec` in the django container. All green.
2. The new doctrine-invariant test passes; `test_v24_10_brief1.py` passes with updated values.
3. DB spot-checks after the dev reseed (in-container shell): `iron-sword`'s `lifesteal` pool entry reads `0.175/0.525`; `flame-projector`'s `flame_factor` primary reads `1.875/1.125` with floor `3.0/9.0`; `copper-ring-of-strength`'s `str` primary reads `0.7/2.1`; every `crit_chance` entry unchanged from the old values.
4. Mk 1 midpoint invariance: for every definition, every entry's `base + factor` equals its pre-change Mk 1 midpoint (the new test's preservation assertions or a one-off shell check).
5. Actual seed deletion count reported: expected 0.

## 6. Operator playtest checklist (dev stack, after Step 5)

1. Examine a starter-kit item and a common Mk 1 drop — stat lines look exactly as before (Mk 1 untouched).
2. Admin-gift or admin-spawn a Mk 2 item (e.g. Iron Sword Mk 2, any rarity above Common) — examine shows secondary values ≈ 1.75× their Mk 1 counterparts (e.g. a rolled `dex` around 2–3 instead of 1–2).
3. Fight the operator-kept Hollowcrown Mk 2 encounter with Mk 2 gear equipped — lifesteal/proc parentheticals visibly matter against the lifted HP pools.

## 7. PENDING DEPLOY-TIME ACTIONS

- **Production seed run** at the V24.14 closeout tail's deploy window, via `make seed-prod` (bare invocation, its own operator confirmation — #187). Expected deletions: **0**. Production carries no Mk 2 instances; the run updates definition curve fields only. This block stays open until that execution.

## 8. Architecture doc (last, gated step)

This step is gated on all implementation and verification steps above being complete and passing. Update `docs/shyland/Shyland_Architecture_v24.md` **in place**: stamp → 24.14; **hash does not move** (no runtime code changed — seed-data release; hash stays f001a79). Update the "proc secondary family is uniformly authored at `base 0.5, factor 0.2`" paragraph (~line 817): the authoring rule is now Mk 1 midpoint + class lift per GDD §6 "The band lift" (#130, v24.14) — rider procs standard m1 0.7 via the half-power pair `0.4375/0.2625`; full-lift stats `0.25/0.75 × m1`; `crit_chance` exempt; floors `0.25/0.75 × f1`. Add the 24.14 line to the header version block.

## 9. Closeout report

Complete the Step-0 stub in place: summary, commits, final hash, deviations, verification results including the actual-vs-expected deletion count (0), the PENDING DEPLOY-TIME ACTIONS block from §7, and the operator playtest disposition (#170). Close #130 (gated on §5 passing). End with the `implementation-session-end` ritual.
