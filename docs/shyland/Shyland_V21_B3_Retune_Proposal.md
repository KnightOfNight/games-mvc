# Shyland V21 — B3 Retune Proposal (#101)

Design proposal for operator ruling. Derived from the #89 survey's expected-value model (`docs/shyland/Shyland_V21_Kill_Feasibility_Survey.md` §1) against the five ruled design parameters recorded on #101. Nothing here is implemented; after ruling, the numbers become the B3 implementation brief.

## The scheme in one paragraph

Three coordinated changes: **(1) tier dodge offsets flatten from 0/+3/+6 to 0/+2/+2** — the knife-edge softens for everyone, and boss difficulty stops living in the miss rate; **(2) boss difficulty moves into HP, damage, and escorts, retuned per-boss** so a fight runs 7–12 rounds and costs the reference build ≤8 potions (final boss ≤12), escorts included; **(3) delve escorts drop from 3 elites to 2 lighter elites** — the Verdant "boss + 2 adds" pattern becomes the ladder-wide pattern. Normals are untouched everywhere. The ×3 rooms are untouched per #102.

## Proposed boss table (the ruling surface — this table is authoritative)

Reference build = even-split-all-points (survey canonical) at the intended kill level, Uncommon band weapon, draughts 25 HP. "Enc" = the real fight, boss + adds.

| Boss | Kill L | DEX now→new | STR now→new | HP now→new | Escorts now→new | Solo len | Enc len | Potions (budget) |
|---|---|---|---|---|---|---|---|---|
| Silk Matron | 3 | 29→**25** | 17→17 | 120→**150** | 2× brood (unchanged) | 7.2r | 8.7r | **0** (≤8) |
| Whistler Below | 6 | 36→**32** | 28→28 | 260→**240** | 2× young (unchanged) | 9.5r | 12.0r | **6** (≤8) |
| Dronemother | 6 | 36→**32** | 30→30 | 320→**260** | 2× swarm (unchanged) | 10.3r | 13.0r | **8** (≤8) |
| Undercrag Weaver | 8 | 42→**38** | 40→**32** | 500→**200** | 3× elite brood → **2× (STR 25, HP 65)** | 7.9r | 11.0r | **7** (≤8) |
| Chittering King | 9 | 44→**40** | 46→**30** | 650→**220** | 3× skitterlings → **2× (STR 26, HP 60)** | 7.6r | 11.1r | **7** (≤8) |
| Crowned Devourer | 10 | 46→**42** | 49→**34** | 850→**280** | 3× drones → **2× (STR 28, HP 70)** | 9.1r | 13.0r | **10** (≤12) |

Notes: the Matron's HP *rises* — she was dying in 4 rounds and 7+ rounds is the ruled floor for a boss to feel like one. Escort stat changes are to the escort NPC definitions (delve adds keep elite tier but shed STR and HP); Verdant escorts are untouched. Boss DEX is expressed in the code as the tier offset (+6→+2); per-boss values above are the resulting numbers, shown for verification.

## Proposed elite table

Elite offset +3→+2 plus HP trims on the five heavies. Solo elites at-level: 0 potions everywhere. The ×2 aggro rooms — ruled the solo ceiling (#102) — land at 4–9 potions at-level, real but inside a stack:

| Elite | L | DEX now→new | HP now→new | ×2 room at-level |
|---|---|---|---|---|
| elder-cave-spider | 7 | 36→35 | 110→95 | 4 potions |
| elder-cave-centipede | 8 | 39→38 | 130→100 | 7 potions |
| elder-cave-beetle | 9 | 41→40 | 150→110 | 6 potions |
| prowling-mountain-lion | 9 | 41→40 | 150→110 | 6 potions |
| territorial-brown-bear | 9 | 41→40 | 170→120 | 9 potions |

Lighter elites (wild boar, buffalo, brown bear, mountain lion, weavers-brood donors) change only via the offset; their numbers already sit inside budget. The ×3 rooms inherit the trims but remain deadly (34→~18–22 potions at L9) — still "don't," now survivable enough to flee, which suits #102's signposting intent.

## What each build experiences after the retune

**Even-split reference (the ruled balance target):** at-level boss hit rate rises 25%→45%; every boss falls at its intended level inside budget; the whole ladder L3→L10 is beatable, delve trio included, with the final boss a genuine 13-round, 10-potion event.

**Your build (+1/+1 style, the 25/25 family):** the Whistler goes from *mathematically unwinnable at L8* (0% hit, ~97 potions) to 20% hit at L8 — winnable with a committed stack (~26 potions), and comfortable by L10 (~15). Same shape for the Dronemother. **The delve trio stays out of reach for this build** — at 12–16 DEX behind the curve, the d20 window still closes. That is the honest limit of a data-only retune: no number makes both builds meet the same boss without breaking one of them. The designed answer is #100 — v22 gear that grants DEX is precisely the bridge — and this retune is shaped so that wiring gear up later *completes* it rather than invalidating it.

## Explicitly unchanged

Normal-tier NPCs (all OK in the survey). Villagers. The ×3 room spawn counts (#102 owns their signposting). The Whistler's intended kill level. Potion price/healing. All code formulas — this is data plus two tier-offset constants; the contest math itself is untouched (that's v22 territory if ever).

## Confirm / adjust

1. The boss table as proposed — including the Matron's HP raise and the delve escort reduction to the ladder-wide 2-add pattern.
2. The elite table as proposed.
3. The flattened offsets 0/+2/+2 (boss and elite share a dodge tier; boss identity lives in HP/damage/escorts).
4. The accepted consequence: delve trio remains reference-build content until v22 gear ships.

Rule on these four and the B3 implementation brief follows.
