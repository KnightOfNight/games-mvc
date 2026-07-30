# V24 Phase 1 — Healing Economy Design Prep

**Status: PREP DOCUMENT — no rulings in here.** Produced by the V24.0 design session (2026-07-30) ahead of the Phase 1 design pass. All code facts verified against `version_24_0` at the branch tip (post v30 forward-merge, `f27f400`). This document frames the pass; the operator rules in-session and the GDD text lands with the releases that ship it.

**Scope: the four Phase 1 issues** — #139 (draught evolution, founding ticket of Version 24.0), #164 (income vs draught cost), #165 (out-of-combat regen), #166 (`heal` command). Series plan of record: the #139 comment thread.

---

## 1. Verified fact base

### The bar being healed

- `vitality_max = (effective END × 10) + (effective STR × 3) + (level × 5)` — `combat_utils.py:508`, effective stats include equipped gear.
- Reference points: fresh character ≈ 100; the #139 field case is L12 with `vitality_max = 718`.

### The only healing consumable

- **Healing Draught** (`seed_world.py` `_seed_effects`): instant `restore_vitality`, `magnitude_base 20.0, magnitude_scaling 5.0` → **heals 20 + 5×Mk** (Mk 1 = 25, Mk 2 = 30, Mk 10 = 70).
- Vendor price **15 cp at Mk 1** everywhere (5 vendors, unlimited stock, Mk 1 only). Cost per HP ≈ 0.6 cp.
- The healing curve is linear-shallow; the health curve is stat-driven into the many hundreds. **They diverge at every Mk — this is structural, not a tuning miss** (#139's core claim, confirmed in code).
- Use machinery already shipped (v23.3, #149/#151): aggregate use computes the heal once, consumes only what's needed, sends one message; consumption order is **oldest-first (law — erratum #168)**.

### Out-of-combat regen (tick engine Phase 4, `run_tick_engine.py:1313`)

- Every 1s engine tick, out-of-combat, not-dying characters heal `ceil(deficit / 120)` vitality (`VITALITY_REGEN_SECS = 120`; longevity same shape at 3600).
- **The constant's comment ("seconds to regen full Vitality from zero") does not describe the implementation.** Healing proportional to *deficit* is exponential decay plus a 1 HP/s tail — NOT a 120-second refill:
  - Refill-from-zero ≈ `120×ln(max/120) + 120` seconds: **~100 s at max 100 (L1), ~5.6 min at max 718 (L12), ~7 min at max ~1500.**
  - The final ~120 HP always crawl at 1 HP/s regardless of bar size — the near-full tail is 2 minutes flat at every level, an ever-smaller fraction of an ever-bigger bar.
- So both #165 claims verify: slow in absolute terms, and slower with growth. Regen is currently **silent** (status-pane update only, no output line).

### Income (the #164 side)

- Item value = `base_value × mk_tier × rarity_mult`; **vendors pay one third** (min 1 cp; 0 stays 0) — `item_utils.get_sale_price`.
- Combat materials: Animal Hide `base_value 6` → sells **2 cp**; Insect Carapace `8` → **2 cp**. Drop chance **0.35, one entry, one item** (`animal-drops` / `insect-drops` tables).
- **Every grind mob drops zero copper.** All wildlife and all cave insects (the entire aggressive Z01 population below boss tier) seed `(copper_min, copper_max) = (0, 0)`. Copper comes only from: villagers (2–8 or 4–12 — passive NPCs), and the three bosses (50–150, 10-min respawn). Money drop = `randint(min×Mk, max×Mk)` (`item_utils.py:329`) — the Mk scaling machinery already exists; this is pure seed data.
- **Expected grind income ≈ 0.7 cp/kill** (0.35 × 2 cp). One draught = **~21 kills of income**; it heals 3.5% of a L12 bar. A fight costing 200 HP needs ~120 cp of draughts against ~0.7 cp earned. The deficit isn't a gap, it's a cliff — matching the operator's field evidence (Harley underwater from scratch; Shy-Guy's 100-gold gift = 100,000 cp ≈ 6,600 draughts, drawn down since).
- Secondary income exists but is villager-kill gated (leather pieces ~10–12% drop, sell 11–15 cp; hunting bow 26 cp) or boss-gated.

### Adjacent settled law (do not re-litigate)

- Three-layer response doctrine, world-declined refusals, §9.1 chart conventions, tab-completion pools (v22).
- Oldest-first consumption (#168), single-message aggregate use (#151), full-vitality refusal of a heal (#61, v22).
- v21 boss potion budgets (≤8/encounter, zone-final ≤12) were computed against the 25 HP draught at L3–L10 — **those budgets need re-derivation after this pass** (already flagged in #139).
- Currency law: single `copper` field, all math through `currency.py`.

---

## 2. The design questions, per issue

### #139 — the draught shape (the founding ruling; everything else keys off it)

Option space (combinable):

- **A. Percentage-of-max healing** — e.g. a draught heals N% of `vitality_max`. Self-scaling forever; Mk tiers then modulate the % (or price). Watch: interacts with gear-stacked END (percentage heals get free scaling), and makes the item's power opaque compared to "+25".
- **B. Retuned absolute curve** — keep flat numbers, re-author `magnitude_base/scaling` so Mk-band healing tracks expected `vitality_max` at that band (e.g. roughly double per band, matching NPC growth). Keeps numbers legible; needs re-tuning whenever the vitality formula moves.
- **C. Named tier ladder** — Draught / Greater / Superior as separate items with authored bases. More content surface (names, vendors, loot), same divergence risk as B unless bases are authored per band.
- **D. HoT variants** — out-of-combat-efficient heal-over-time sibling (cheap, slow) vs instant (premium). Gives the economy two price points and gives effects content real play (#47's eventual feed). Watch: HoT + regen redesign (#165) overlap.

Structural questions: does Mk tier remain the scaling axis (Mk item system is settled law — a draught is an Mk item), or does the *effect* scale by drinker rather than item? Who stocks what where (frontier vendors' sold counters show demand concentrates at the delve staging point)?

### #164 — the income targets (pure seed data once ruled)

- Which faucets open: copper on grind mobs (machinery exists, seed `(0,0)` today), material value/drop-rate raises, or both. Bosses already pay.
- The balance target wants stating as a ratio, not absolutes: **income per typical fight ÷ healing cost per typical fight = k**, with k comfortably above 1 (draughts stay a real sink; margin funds repair and gear). Suggested framing for the session: pick k per tier (normal/elite/boss) and per intended level band, then derive seed numbers.
- Sequencing trap: if the #139 ruling raises per-unit draught prices at higher tiers, income must land **no later** than the price change or the live game gets worse in the gap. (Phase-internal release order is ruled in-session.)

### #165 — the regen law (tick engine change)

- Candidate laws: **(a) proportional-to-max** — `heal/sec = vitality_max / T` → full refill in exactly T seconds at every level (T is the whole ruling: 90 s? 120 s?); **(b) keep deficit-decay but fix the constant/tail**; (c) banded rates. (a) is the simplest true fix of "doesn't scale" and makes the comment finally true.
- The time-vs-money dial: T prices the free alternative. Too short and draughts stop being a sink out of combat; too long and the game is standing still. Interacts directly with the #164 k-ratio and any HoT item from #139-D.
- Mechanical notes: in-combat exclusion stays (settled asymmetry for vitality; the *acuity* half is #142, Phase 3 — do not pull it in here). Regen stays silent presumably; ceil() keeps the tail from stalling. Async-safety and round-boundary conventions bind.

### #166 — the `heal` command (rides the #151 machinery)

- Semantics: "use infinity healing draughts" — drink until full or supply exhausted, one consolidated message, refusal when already full (world-declined, per #61's precedent).
- Grammar for the session: bare verb only, or noun-taking (`heal` vs `heal <consumable>`)? §9.1 chart entry, footnotes, tab-completion pool, state gating (in-combat use is currently allowed for consumables — confirm and keep?).
- Selection order: oldest-first is law for like items; if #139 ships a tier ladder, cross-tier selection needs a ruling (oldest-first regardless of tier? smallest-sufficient-first to limit waste? the #151 "consume only what's needed" principle extends naturally).
- Interplay: once `heal` is built-in, `alias heal <anything>` must refuse (operator note on #125 — the deferred alias system must not shadow built-ins; worth a one-line GDD/§9 note when this ships).

---

## 3. Interactions to keep on the table

- **#139 ↔ #164:** the draught's price/heal ratio and the income faucets are one equation; rule them against the same fight model.
- **#139/#164/#165 ↔ Phase 3 (#104/#130):** Mk 2 NPC damage output defines required healing throughput at 11–20. This pass sets the healing side *shape*; Phase 3 verifies the numbers against Mk 2 NPCs — expect a small re-tune there, not a re-design.
- **#165 ↔ #139-D:** a HoT draught and faster regen occupy the same niche; if both ship, differentiate (regen = free + slow + interruptible; HoT = paid + faster + combat-adjacent).
- **#166 ↔ #139:** ship `heal` before the tier ladder and its selection ruling is trivial; after, it needs the cross-tier rule. Cheap to ship early.
- **Fight model for all targets:** 3-second rounds, one consumable per round; drinking must out-pace intended-level boss DPS by a margin the session picks (the v21 budget re-derivation).

## 4. Suggested pass agenda (operator rules each in turn)

1. Rule the #139 shape (A/B/C/D or combination) and the staple's intended "bar fraction per drink" at on-level play.
2. Rule the fight model targets: draughts-per-normal-fight, per-boss budget, and the income ratio k per tier (#164).
3. Rule the regen law and T (#165).
4. Rule `heal` grammar, gating, and selection (#166).
5. Rule phase-internal release order (default sketch: 24.0 = #139, then #164, #165, #166 — with the #164-before-price-rise trap in mind and #166 free to move early).
6. GDD-first: §4 (Three Bars — regen law), §6 (Economy & Items — draught/economy), §9 (command reference — `heal`) updated as rulings settle; briefs written and committed per release.

## 5. Open verification items for the pass (small)

- Confirm consumable use is permitted in combat in the current state-gating matrix (GDD §9.1) before ruling `heal`'s gating.
- Confirm draught vendor `sold` counters read as demand signal (Ridda 1,328 / Sona 475 / Essa 261 — from #139, production 2026-07-22) if stocking rulings depend on them.
