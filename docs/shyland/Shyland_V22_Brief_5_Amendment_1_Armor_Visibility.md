Shyland V22 Brief 5 — Amendment 1 — Armor Visibility
Type: amendment to `Shyland_V22_Brief_5_Gear_Combat_Wiring.md` (does not count against the cap) Branch: the current Version 22 worktree branch (`version_22`) — all work, commits, and pushes on that branch Issues: #100 (ruling comment; if already closed by the parent brief, comment anyway — do NOT reopen) Migrations: NONE.
The parent brief wired armor but left it invisible: a player cannot see their Total Armor Value, what a piece contributes, or what armor did on any given hit. Three display rulings, operator-confirmed, close that gap. All vocabulary from the parent brief applies (TAV, `ARMOR_SLOT_WEIGHTS`, `ARMOR_MITIGATION_K`, `total_armor_value`, `apply_armor_mitigation`). Data tables are authoritative over prose if they disagree.
Standing rules

* Work in the Version 22 worktree on its branch. Commit and push at every step boundary — branch only, NEVER merge to main on your own initiative.
* Never remove, prune, or clean up any transient document.
* Test suite runs as `apps.shyland.tests` (#117 workaround, unchanged).
* If any repo fact contradicts this amendment, stop and record the contradiction in the closeout rather than improvising.

Pre-flight

1. Version 22 worktree, tree clean, branch synced. The parent brief's Steps 2–7 must already be present on the branch (this amendment builds on `total_armor_value` and the hit-line composition). If they are not, STOP — this amendment runs after the parent brief, never before.
2. `gh auth status` shows repo access.

Step 0 — Self-commit this amendment
Save verbatim to `docs/shyland/Shyland_V22_Brief_5_Amendment_1_Armor_Visibility.md` (skip if identical file exists). Commit and push immediately.
Step 1 — Housekeeping
Post this comment on #100, verbatim (comment even if the issue is closed; do not reopen):

```
B5 Amendment 1 — armor visibility rulings, confirmed by the operator
(designed after the implementation brief shipped; delivered as the
consolidated amendment):

1. STATS SHEET ARMOR ROW: the stats report gains a kind-1 key/value row —
   "Armor: 13 (blocks 21%)" — TAV, then its current mitigation in words.
   The percentage is derived live from TAV/(TAV + K), rounded to nearest.
   Naked: "Armor: 0", no parenthetical (zeros never hidden; nothing blocked
   to report).

2. EXAMINE CONFESSES CONTRIBUTION: an armor item's examine detail gains a
   line — "Armor: 3 per Mk" — the slot weight; when the piece is currently
   equipped, it appends the piece's actual current slot-weight contribution:
   "Armor: 3 per Mk (worn: 3)". A broken piece contributes 0 and the
   parenthetical says so. Rolled physical_resist keeps showing on its own
   stat lines — it is not folded into this line.

3. INCOMING HITS MIRROR THE OUTGOING GRAMMAR: one vocabulary — the
   parenthetical is always your gear's contribution to the number, and the
   leading number is always the one that moved a bar. Outgoing: "You hit
   the giant cave spider for 14 (+7) damage." Incoming: "The giant cave
   spider hits you for 14 (-6) damage." — you took 14, armor ate 6, raw
   was 20. Applies to hits, crits, and grazes alike. No armor (TAV 0) →
   no parenthetical, line byte-identical to today — the same quiet-line
   law as procs.

Declined by ruling: no persistent armor readout in the right pane — the
stats row and per-hit receipts cover the need.

```

Commit and push (the amendment file may be the only tracked change; fine).
Step 2 — Stats sheet Armor row
In the `stats` report (parent brief Step 6 territory), add one kind-1 key/value row after the six stat rows:

* Key `Armor`, value = `total_armor_value(character)`.
* When TAV > 0, append the parenthetical `(blocks N%)` where `N = round(100 × TAV / (TAV + ARMOR_MITIGATION_K))` — computed from the live constant, never a hardcoded copy.
* When TAV = 0: `Armor: 0`, no parenthetical.
* Existing key/value color vocabulary; no new palette entries.

Tests: naked → `Armor: 0` exactly; full Common Mk 1 set → `Armor: 13 (blocks 21%)`; broken chestpiece lowers both numbers consistently.
Step 3 — Examine contribution line
In the item examine detail for items whose `definition.item_type == 'armor'` and whose definition occupies a slot present in `ARMOR_SLOT_WEIGHTS` (resolve via `valid_slots`; if multiple valid slots, show the weight per slot only if they differ, else the single weight):

* Line: `Armor: <weight> per Mk`.
* If the instance `is_equipped`: append `(worn: <contribution>)` where contribution = the piece's actual current slot-weight-side TAV contribution (`weight × mk_tier`, and `0` if the piece is broken — render `(worn: 0 — broken)` in that case).
* `physical_resist` continues to render on its normal stat lines, untouched — it is not folded in here.
* Placement: with the item's other property lines, position per the existing examine composition order (cite the chosen position in the closeout).

Tests: held unworn piece shows `Armor: 3 per Mk` with no parenthetical; equipped Mk 1 chestpiece shows `(worn: 3)`; broken equipped piece shows `(worn: 0 — broken)`; non-armor items gain no line.
Step 4 — Incoming hit parenthetical
In the NPC→player damage display path (where the parent brief's Step 3 inserted `apply_armor_mitigation`):

* The line's leading number is the damage that actually landed (post-mitigation, post-clamp) — the number that moved the bar.
* When mitigation reduced the hit (TAV > 0), append the parenthetical with an ASCII hyphen-minus: `for 14 (-6) damage` where 6 = raw − landed.
* TAV 0 → no parenthetical; the line is byte-identical to today.
* Applies to hit, critical, and graze renderings alike; composes with the existing crit/graze phrasing the same way the outgoing proc parenthetical composes.
* The parenthetical inherits the line's existing color; no new palette entries.

Tests: unarmored → line unchanged byte-for-byte; armored → leading number equals the bar delta and the parenthetical equals raw − landed; graze and crit lines compose correctly; floor case (TAV 1, small hit) shows `(-1)`.
Step 5 — Verification
Full suite green (`apps.shyland.tests`) plus all new tests above. No re-bless needed — mitigation math is untouched; this amendment is display only.
Step 6 — Architecture doc (GATED, last)
Gated on all steps above complete and passing. Update `docs/shyland/Shyland_Architecture_v22.md` in place (no new file, no version bump; display-only architectural addition — the header hash moves with this commit): the stats-report section gains the Armor row, the examine composition gains the contribution line, and the combat display section gains the incoming parenthetical under the one-vocabulary rule (parenthetical = gear's contribution; leading number = what moved the bar).
Step 7 — Closeout
Write `docs/shyland/Shyland_V22_Brief_5_Amendment_1_Closeout_Report.txt`: the examine-line placement chosen, confirmation of byte-identical unarmored lines, any discrepancies, and the final commit hash. Commit and push.
Step 8 — Final instruction
run the issues report
