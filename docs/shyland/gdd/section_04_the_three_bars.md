## 4. The Three Bars — Vitality, Acuity, Longevity

This is one of Shyland's most distinctive systems. All characters have three resource bars, each governing a different dimension of their condition. **The bars are independent — no bar ever reads or modifies another (the three-tanks doctrine, v26.1).** Vitality and Longevity are **fuel tanks**: currencies a character spends in order to act. Enough fuel buys the action; not enough refuses it; and the fuel balance never changes what the purchased action does — **the fuel tanks don't control power, they're just money.** Power comes from player, NPC, and item level, never from fuel remaining. Acuity is deliberately not a fuel tank: it is a band meter whose deviation modifies the character's own output (Section 4.2), and that identity is exactly as shipped.

**Player-facing bar ordering is Vitality, Longevity, Acuity (v26.1, pending implementation)** — the stats pane and every kindred surface render Longevity second. The subsection order below is historical and unchanged, so every §-reference stays valid; the reorder is display-side only.

### 4.1 Vitality

**What it is:** The body's immediate physical condition — the fuel tank of staying alive.

**Mechanical effects:** Vitality is a pure fuel tank — **it gates, it never scales.** Its one gate is absolute: reaching 0 Vitality triggers the Dying state. At every value above zero the character fights, moves, and resists at full effectiveness. (Canceled on paper, v26.1 — never built: melee damage scaling with current Vitality, movement-speed degradation at low Vitality, physical-resistance degradation at low Vitality. The code has been a pure tank since day one; the doctrine makes the paper match.)

**Recovery:** Healing spells, medkits, potions, and passive natural regeneration. Passive regen is always active when not in combat and not in the Dying state — no rest command required. **The regen law: proportional to maximum.** The rate is `vitality_max / VITALITY_REGEN_SECS` points per second, applied per tick as `ceil(vitality_max / VITALITY_REGEN_SECS)` and clamped at max. At the constant of 120 seconds, a full refill from zero takes exactly **120 seconds at every level** — the deeper the pool, the faster the points return; refill time never grows with vitality growth, so time remains a real substitute for draught money at any level. Regen is silent — no message is sent; players observe recovery through the status bar.

**Machinekind note:** Machinekind characters cannot be healed by magic. However, passive regeneration applies to Machinekind via nanomachine self-repair — the narrative framing differs, the mechanic is identical.

### 4.2 Acuity

**What it is:** The mind's dynamic state. Not a scale from broken to perfect — a spectrum with a sweet zone that varies by Origin. Being too high or too low are both problems.

**There is no universally "correct" Acuity value.** Each Origin has a natural baseline and a tolerance band. Characters are most effective when operating within their band.

**Acuity scale (v19 — band-relative, deviation-based):** Acuity is stored as a float in the range **0.1 to 1.9**. The damage modifier is derived from the value's position relative to the character's **Origin band** — the band is your normal, and the modifier measures how far you have pushed beyond it:

| Position | Modifier |
|---|---|
| Inside the Origin band (band_low ≤ a ≤ band_high) | **1.0 — neutral.** Every Origin at baseline fights at full effectiveness |
| Above band_high | `1.0 + (a − band_high)` — hyper-focus bonus, **focus target only** |
| Below band_low | `1.0 − (band_low − a)` — penalty, applies to **all** targets |

No decimal rounding is applied anywhere in the derivation (the v18-era `round(x, 1)` was removed in v19 — it silently converted Feral's 0.95 baseline into a hidden 0.9× penalty). Band *width* is Origin identity: Voidtouched's wide band (0.40–1.30) means stability across wild swings but the longest push to reach the bonus — and the deepest bonus ceiling (+0.6 at the 1.9 cap) when committed. Per-origin baseline and band values live on the `Origin` model (`acuity_baseline`, `acuity_band_low`, `acuity_band_high`) and are copied to the character.

**Focus rule:** the bonus (>1.0) applies only to the character's current **focus target** (Section 5.3); the penalty (<1.0) applies to every target regardless.

**Per-Origin defaults:** See Section 3.2 table.

**Effects of Acuity too LOW (distracted, scattered, overwhelmed):**

- Spell effectiveness degrades — spells may fizzle, truncate, or misfire
- Ranged aim drifts — hit chance penalties
- Situational awareness collapses — the game shows fewer ambient messages, sneaking enemies may go undetected entirely
- At severe lows: combat log entries may be garbled, phantom sounds described in room text

**Effects of Acuity too HIGH (hyper-focused, tunnel vision):**

- Devastating against a single target — bonus damage and accuracy on focused attacks
- Flanking enemies and ambushes from outside the focus cone are not detected
- Peripheral combat events (an ally taking damage, an enemy arriving) may be missed
- A Shade's dream scenario to exploit against opponents

**The sweet zone:** The range between too-low and too-high where the character operates optimally. Wider for some Origins (Voidtouched are accustomed to extremes), narrower for others.

**What shifts Acuity:**

- Eldritch damage and prolonged exposure to Pale Shore zone pushes Acuity toward extremes
- Stress effects from combat, particularly losing allies or taking massive damage, can spike or crash it
- Consumables and spells can deliberately shift Acuity in either direction — a "focus" potion before a boss fight is a legitimate tactical choice, with the flanking blindness risk as the tradeoff
- The Warden archetype has party-wide Acuity management tools
- Rest and time naturally return Acuity toward a character's baseline — out of combat only; passive drift pauses during combat (see below)

**Acuity shift effects — the band edge is the wall (v23, #133).** A consumable or spell that shifts Acuity **upward** climbs toward the drinker's own `acuity_band_high` and **stops there, exactly** — the value is stored on the band edge to two decimals, so the in-band check and the stats-pane band gauge agree rather than disagreeing at the fourth decimal. A downward shift stops at `acuity_band_low` the same way. Three rules govern the family:

- **Shifts are one-way.** A high shift never lowers Acuity and a low shift never raises it. A character already past their band who drinks a focus tonic is held, not dragged back to the edge.
- **Effect ticks never announce no-ops.** A tick that changes nothing is silent. Arrival at the wall gets exactly one terminal line — `Your focus settles at its keenest.` at the top, `Your focus frays to nothing.` at the bottom — and holding there is silent thereafter.
- **A running shift owns the value.** Passive drift toward baseline pauses while a shift effect is active and resumes when it expires.

The consequence is deliberate and worth stating plainly: **the tonic family buys the top of your band, not the bonus above it.** At `a = band_high` the modifier is exactly 1.0 — a focus draught erases a deficit and guarantees you fight at full effectiveness for its duration; it can no longer be drunk to the `1.9` rail for a permanent hyper-focus multiplier (the pre-v23 over-band exploit). The bonus region above `band_high` remains real and remains reachable, just not by that family: the per-tick acuity effects (`hot_acuity` / `dot_acuity`) are not bound by the shift rules and can still carry a character past the band, and the designed world sources — eldritch damage, prolonged Pale Shore exposure — will do the same when that content ships. The line the ruling draws is between what the world does to you and what you can drink. The engine's hard rails at `0.1` and `1.9` stand as the absolute clamp (named constants at every clamp site), reached only by those world sources.

**Drift pauses in combat (#142).** Passive drift toward baseline runs only outside combat: the drift pass excludes any character with an active combat session, using the **same combat-membership predicate** as the Vitality/Longevity regen pass — one definition of "in combat," shared, so a future change to combat membership moves both together. With this ruling, *nothing passively recovers in combat* holds for all three bars. The consequences are deliberate: an acuity state inflicted mid-fight — an eldritch crash, a `dot_acuity` bleed — sticks until the fight ends or the player answers it (a consumable, a Warden's tools); and a hard-won above-band spike no longer leaks away between rounds. Shift-active and in-combat are **independent** pause conditions — the shift rules above stand verbatim. Combat continuing after quit keeps a logged-out fighter's drift paused until the session ends. At combat's end drift resumes at its ordinary rate — no burst correction, no refill.

**Acuity display precision — two decimals, end to end (#225).** Every acuity numeral the game renders shows **fixed two decimals, trailing zeros kept** (`1.00`, never `1.0`): the stats-pane number, the `stats` command's current and baseline values, and the tick-engine message suffixes (`(Acuity 1.10)`). One uniform precision for every surface the meter speaks through — the band vocabulary is two-decimal exact (#133 stores band-edge arrival to two decimals), and a coarser display lies precisely at the settled states the meter exists to show (a Focus Tonic settled at a 1.15 band edge rendering as "1.1"). Display-only: stored values remain unrounded floats, and the modifier derivation stays rounding-free per the v19 rule above.

**Manipulation:** Players can actively shift their own Acuity intentionally. Pushing it high before a single-target duel, then managing the aftermath, is a valid play style. The system rewards players who understand their character's band and manage it actively.

### 4.3 Longevity

**What it is:** The slow burn. The deep reserve — the will and capacity to keep going — spent on acts of raw exertion and refilled slowly. Longevity is a pure fuel tank: **it gates, it never scales.** No effect's power or duration, no regen rate, no stat, and no other bar reads it. It answers exactly one question: *can you afford this action right now?*

**Spending it — flee exertion (v26.1, pending implementation):** the first consumer is **flee**. A contested flee attempt — one that reaches the escape contest — costs **25% of `longevity_max`** (`ceil(longevity_max / 4)`), at every level, whether the attempt succeeds or fails: the escape and the failed scramble exert alike, and the "still recovering from your last flee attempt" fiction finally has its cost. The gate is exact-or-refused: with `longevity_current` below the cost, the attempt is refused — **no fuel, no flee** — and the refusal is free (no Longevity spent, no flee cooldown started; a refused purchase leaves no charge). At exactly the cost, the flee fires and lands the character at zero fuel. The drained player fights, quaffs, or dies. Outside the fuel system entirely: flee outside combat remains the shipped no-op refusal, and a flee inside a session whose living opposition is already gone remains a free trivial disengage — no contest, no exertion, no cost.

**Future direction (recorded, not yet designed): Longevity is mana fuel.** Future player abilities will draw it at much smaller percentages than flee's 25%. Fuel decides whether the ability fires at all; the fired ability's power comes from level, never from the tank.

**Recovery (v26.1, pending implementation — constant retuned 3600 → 900):** Longevity recovers passively out of combat under the same proportional-to-max law as Vitality, at its own slower constant (`LONGEVITY_REGEN_SECS = 900`): full recovery from zero in a nominal **15 minutes at every level** — still 7.5× slower than Vitality, no longer an hour. The rate is `longevity_max / 900` points per second; because that is usually below one point per second, the numerical form is chosen **by regime** so the law holds at every bar size:

- **`longevity_max < 900` — the interval form:** one point every `ceil(900 / longevity_max)` seconds (4 s per point at a 274 bar, ~18 minutes from zero; one flee's worth back in roughly 4–5 minutes).
- **`longevity_max ≥ 900` — the per-tick form,** exactly Vitality's shape: `ceil(longevity_max / 900)` points per second.

The crossover is seamless — both forms approximate the same `max / 900` rate, each ceil rounding at its own regime's granularity — and refill time stays ~15 minutes however deep the tank grows; without the regime rule, the interval form's 1-second floor would make refill time grow linearly with any bar past 900. Warden abilities can accelerate this.

**Restoring it — the potion (v26.1, pending implementation):** Longevity's restorative consumable works **exactly like the Healing Draught**, under the same Draught Law shape: a percent-of-max restore of **`0.15 + 0.05×Mk`** of `longevity_max`, Common, seeded into Z01 vendor stock at the draught's 15 cp standard, vendor-only (no loot-table entries). The mismatch is deliberate: one Mk 1 potion (20%) does not fully refund one flee (25%) — fuel costs what it costs. (Name and lore are authored at brief time.)

**Design intent:** Longevity is the wallet for exertion. A player who flees twice in a dungeon has spent half their tank and will feel the third emergency before they reach it — the bar rewards planning an escape budget the way copper rewards planning a shopping trip. It is the slowest tank to refill and the one players are most likely to overdraw in a long run; what it never does is make anyone hit softer, cast shorter, or regen slower. Enough fuel buys the action. Not enough refuses it. Nothing else.

### 4.4 Independence of the Three Bars — The Three-Tanks Doctrine

**The bars are three independent tanks. No bar ever reads or modifies another bar (v26.1 doctrine — the code has worked this way since day one; this section now says so).** Two long-promised causal connections are canceled on paper, never having been built: critically-low Vitality no longer promises an Acuity panic spike, and severely-low Longevity no longer promises slowed Vitality/Acuity recovery. There are no cross-bar reads anywhere — not in regen, not in effect application, not in combat math.

What remains true — and compatible with independence:

- **One effect may carry components against multiple tanks.** Certain eldritch effects damage all three bars simultaneously — as parallel per-tank components in a single effect definition. Drainers, not connections: each component touches its own tank and reads nothing from the others.
- **A skilled Warden manages all three for the party** — not just the green bar. Fillers, not connections: Warden tools restore and steady each tank on its own terms.

**The bar law (v22, #100/#109/#110 — standing invariant).** Fill fraction is invariant under **every** max-changing mutation — equip, unequip, and stat spend alike. When a bar's maximum changes, the current value rescales proportionally (`current × new_max ÷ old_max`, rounded to nearest, floored at 1 while alive; a dying 0 stays 0; full bars stay exactly full — no drift). The bar grows or shrinks; the percentage holds; **nothing refills**. One law, no special cases, exploit-proof by construction: equipping END gear at 40% leaves you at 40% of the larger bar, and the once-bankable mid-combat spend heal cannot exist. The rescale is one atomic database update in the #52 style — the consumer never reads-modifies-writes bar or stat fields on a cached object — which is also where #110's stat-field race died. Level-up keeps its own behavior (full refill on both bars) — leveling is an earned moment, not a mutation.

-----
