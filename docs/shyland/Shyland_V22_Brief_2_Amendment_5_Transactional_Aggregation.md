Shyland V22 Brief 2 — Amendment 5 — Transactional Aggregation (×N)
Amends: `Shyland_V22_Brief_2_Command_Revamp.md` (DD §6 success sentences) · Version: 22 · Bucket: B2 Issues: none founded for the change itself (design rulings 2026-07-20, recorded below); Step 5 files one new issue and captures its number at runtime. Branch: the v22 worktree branch. Never merge.
This amendment is self-contained.
Pre-flight

1. Verify `DOCKER_HOST` before any deployment-touching action.
2. v22 worktree branch, clean tree aside from committed work.

Step 0 — Self-commit this amendment
Save verbatim to `docs/shyland/Shyland_V22_Brief_2_Amendment_5_Transactional_Aggregation.md` (skip if identical exists), commit, push immediately. Commit and push at every step boundary. Never merge.
Step 1 — The rulings this amendment executes
Ruled 2026-07-20:

1. Multi-item success output splits by nature. Aggregate (one line per item definition, count folded in): buy, sell, drop, pickup — a transaction is one act however many items it moves. Per-line (each line is its own news): use, repair, loot — each iteration is a distinct world event (a swallow's effect and the stop-at-full check, a mend's chance outcome, a find's identity). Use in particular must never pre-announce a count: the number actually applied is unknowable in advance (combat interleaves; stop-at-full fires mid-sequence).
2. Aggregate form is the count form — first iteration, deliberately plural-free: `<name> ×<N>`. Natural-English pluralization is a future subsystem (Step 5 files it); the count form is never wrong in the meantime.

Step 2 — Aggregate success sentences
File: `django/src/apps/shyland/consumers.py` (the DD §6 sentence sites for buy/sell/drop/pickup).

1. N = 1: unchanged. The existing singular sentences stand exactly as shipped (articles and all): `You buy the Iron Mace Mk 1 for 9 coppers.`
2. N > 1: one aggregate line per item definition, no article, name verbatim (rarity words still rarity-colored), count form, total money where money moves:
   * buy — `You buy Healing Draught Mk 1 ×100 for 9 silver.` (total price through the tier formatter)
   * sell — `You sell Healing Draught Mk 1 ×100 for 4 silver 50 coppers.` (total)
   * drop — `You drop Battle Axe Mk 1 ×5.`
   * pickup — `You pick up Insect Carapace Mk 1 ×12.` (loot-color, as ruled)
3. Mixed multi-definition operations (`pickup all` over varied litter): one aggregate line per definition, printed in the order the executor first reaches each definition (oldest-first floor order drives it); singles among them use the N=1 form.
4. Partial fulfillment unchanged: the warm shortfall line precedes the aggregate, and the aggregate's N is the actual count moved: `You only had 3 — the vendor was happy to take them.` then `You sell Healing Draught Mk 1 ×3 for 13 coppers.` (If the actual count is 1, the singular sentence follows the warm line.)
5. use, repair, loot: untouched. Their per-line output stands byte-identical.

Step 3 — Tests
Extend the suite (`apps.shyland.tests`):

1. buy/sell/drop/pickup at N=1: existing singular sentences unchanged.
2. Each at N>1: exactly one aggregate line per definition, count form correct, total (not unit) price, no article before the name.
3. pickup aggregate emits the loot/reward category.
4. Mixed `pickup all`: per-definition lines, order per floor order, singles singular.
5. Sell shortfall: warm line + actual-count aggregate.
6. use N: still one line per application (assert multiple lines for a multi-use sequence); repair-all still per-mend.
7. Full suite green; report counts.

Step 4 — Operator playtest checklist
Ready after deploy: `buy 100` of a cheap vendor item — one line, total price; `sell 100` back — one line (plus warmth if short); `pickup all` over mixed dropped litter — a handful of per-definition lines, greens green; `use 5` draughts while hurt — per-swallow lines ending in the stop-at-full line.
Step 5 — File the pluralization subsystem issue
Via `gh issue create`, capture the number at runtime. Title: `pluralization subsystem — natural-English plurals for aggregate output`. No milestone, no labels. Body: `Ruled 2026-07-20 (V22 B2 Amendment 5): aggregate transactional output ships with the count form ('Healing Draught Mk 1 ×100') as a deliberately plural-free first iteration. The upgrade is a shared pluralization subsystem callable from any output site: forward pluralization rules (inverting the resolver's _plural_variants de-pluralizer), an authored plural-name override field on ItemDefinition for irregulars, and multi-word head-noun handling ('Boots of the Marsh'). When it ships, the ×N aggregates upgrade to natural English ('You buy 100 Healing Draughts Mk 1 …'). Future version; scope deliberately excluded from v22.`
Step 6 — Architecture doc (gated last)
Gated on Steps 2–3 complete and passing. Update `docs/shyland/Shyland_Architecture_v22.md` in place: the aggregate/per-line output split and the count form, with the subsystem issue referenced by its runtime-captured number.
Closeout
`docs/shyland/Shyland_V22_Brief_2_Amendment_5_Closeout_Report.txt`: per-step results, the new issue's number, test totals, deviations, final commit hash. Commit and push. Do not remove or prune any documents. No issues to close.
Finally: run the issues report.
