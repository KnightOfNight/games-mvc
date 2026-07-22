## 4. The Three Bars — Vitality, Acuity, Longevity

This is one of Shyland's most distinctive systems. All characters have three resource bars, each governing a different dimension of their condition. They are not separate — they interact and influence each other. The separation into three bars is a mechanical convenience, not a philosophical statement that mind and body are distinct.

### 4.1 Vitality

**What it is:** The body's immediate physical condition.

**Mechanical effects:**

- Melee damage dealt and received scales with current Vitality as a percentage of maximum (low Vitality = hitting and being hit harder proportionally)
- Movement speed degrades at low Vitality
- Physical resistance degrades at low Vitality
- Reaching 0 Vitality triggers the Dying state

**Recovery:** Healing spells, medkits, potions, and passive natural regeneration. Passive regen is always active when not in combat and not in the Dying state — no rest command required. Formula: `ceil((vitality_max - vitality_current) / VITALITY_REGEN_SECS)` per tick, minimum 1 point per tick when any healing is due. At the default constant of 120 seconds, a character at zero Vitality reaches full in at most 120 seconds; a character missing one point heals in a single tick. Regen is silent — no message is sent; players observe recovery through the status bar.

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
- Rest and time naturally return Acuity toward a character's baseline (passive Acuity drift is implemented)

**Manipulation:** Players can actively shift their own Acuity intentionally. Pushing it high before a single-target duel, then managing the aftermath, is a valid play style. The system rewards players who understand their character's band and manage it actively.

### 4.3 Longevity

**What it is:** The slow burn. Accumulated resilience — the will and capacity to keep going over time.

**Mechanical effects:**

- Controls stamina duration — how long a character can sprint, sustain effort, or maintain concentration
- Governs duration of sustained effects: a character's own damage-over-time effects last longer at high Longevity; enemy DoTs applied to them expire faster
- Controls the window of long-lasting buffs and debuffs
- At low Longevity: sustained spells collapse early, long fights become increasingly punishing

**Recovery:** Longevity recovers passively out of combat using the same formula as Vitality but with a much slower time constant (`LONGEVITY_REGEN_SECS = 3600`): `ceil((longevity_max - longevity_current) / LONGEVITY_REGEN_SECS)` per tick, minimum 1 point per tick when any healing is due. At 3600 seconds, full Longevity recovery from zero takes at most one hour — 30× slower than Vitality. Warden abilities can accelerate this. It is the hardest bar to restore and the one players are most likely to mismanage over a long dungeon run.

**Design intent:** Longevity is the dungeon stamina resource. A player might enter a dungeon with full Vitality and Acuity but low Longevity from previous fights, and feel it immediately in their sustained performance. It rewards planning and discourages endless grinding without rest.

### 4.4 Interactions Between the Three Bars

The bars are not isolated:

- Critically low Vitality causes Acuity to spike (panic response — hyper-focus with all its drawbacks)
- Severely low Longevity causes both Vitality regen and Acuity recovery to slow
- Certain eldritch effects damage all three bars simultaneously
- A skilled Warden manages all three for the party — not just the green bar

**The bar law (v22, #100/#109/#110 — standing invariant).** Fill fraction is invariant under **every** max-changing mutation — equip, unequip, and stat spend alike. When a bar's maximum changes, the current value rescales proportionally (`current × new_max ÷ old_max`, rounded to nearest, floored at 1 while alive; a dying 0 stays 0; full bars stay exactly full — no drift). The bar grows or shrinks; the percentage holds; **nothing refills**. One law, no special cases, exploit-proof by construction: equipping END gear at 40% leaves you at 40% of the larger bar, and the once-bankable mid-combat spend heal cannot exist. The rescale is one atomic database update in the #52 style — the consumer never reads-modifies-writes bar or stat fields on a cached object — which is also where #110's stat-field race died. Level-up keeps its own behavior (full refill on both bars) — leveling is an earned moment, not a mutation.

-----

