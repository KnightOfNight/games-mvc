# Shyland V23 — Brief 4: Voice Machinery & Transactions
**Model:** Opus · **Effort:** high
**Branch:** `version_23` (worktree)
**Issues:** #138 (closes), #40 (partial — stays open, closed by Brief 5)
**Bucket:** B4 (NPC Voice), part 1 of 2
---
## 0. Context (read this first)
This is the fourth implementation brief of Version 23. Bucket B4 splits into two
briefs by mechanism:
- **This brief (4)** — the sites where a hardcoded single string must become a
  pool plus a random pick, plus #138's rules change to the sell path. All code.
- **Brief 5** — the sites where the pool machinery already exists and only seed
  rows are missing (#144's six silent NPCs, thin keyword entries, departure
  reactions, connectives). All data, no code.
`#40` is closed by Brief 5, not this one. This brief does the code half.
**Authoritative rulings this brief implements** (do not re-derive; do not
deviate):
- `#40` — the design-chat ruling comment of 2026-07-23 (full sweep of
  single-line sites; pool mechanics follow the existing kibitz-style
  random-pick pattern; no novel selection architecture; all pool content is
  authored flavor).
- `#138` — the design-chat ruling comment of 2026-07-23 (vendors accept
  worthless items for 0 copper; vendors never buy Artifact rarity at any value;
  the binding system is untouched).
- **Design-chat amendments of 2026-07-24**, ruled by the operator in this
  session and carried by Step 1 of this brief onto the issues:
  1. Boss `death_message` is **cut from #40's scope**. It stays a scalar
     `TextField`. No migration, no child table, no seed change. This brief and
     Brief 5 are both migration-free.
  2. The artifact refusal is **generic and never names a rarity** — not in any
     pool line, not in any fallback. This is a standing no-leak rule for vendor
     messages (see §3.4).
  3. Report-category renderings are **excluded** from the sweep (see §3.9).
  4. `ItemInstance.is_artifact` is **removed from the database entirely**
     (see §3.10). It is a v15-era vestige that nothing reads, presented in
     admin as an authoritative-looking flag. Because artifacts are, by settled
     design, hand-authored by super-users through admin, a dead checkbox
     labelled `is_artifact` is a trap: ticking it would produce an artifact
     with none of #138's protection, silently. Killing the field makes
     `rarity` the single unambiguous marker. **This brief therefore carries
     one migration** (`0037`), reversing the migration-free property the
     earlier amendments produced.
---
## 1. Pre-flight (do this before anything else; stop and report on any failure)
1. `echo $DOCKER_HOST` — must be set. If empty, **stop** and report.
2. Confirm the worktree is on branch `version_23` and the tree is clean.
3. **Prior pending deploy-time actions:** Brief 2's `purge_orphaned_items`
   production run is **confirmed executed** (87/87/0 then 0/0/0). Brief 1 and
   Brief 3 left none. Report one line confirming **no prior pending deploy-time
   actions are outstanding**. If your own inspection disagrees, stop and report.
4. Confirm `django/src/apps/shyland/version.py` reads
   `SHYLAND_VERSION = "23.0-DEV"`. Brief 2 already set it. **Do not change it.**
   If it reads anything else, stop and report.
5. Confirm `docs/shyland/Shyland_Architecture_v23.md` exists. It does. This
   brief **updates it in place** and does **not** bump its version stamp.
---
## 2. Step 0 — self-commit and push (first action after pre-flight)
Save the full verbatim text of this brief to
`docs/shyland/Shyland_V23_Brief_4_Voice_Machinery_And_Transactions.md`
(skip the write if an identical file already exists), commit it on the
`version_23` worktree branch, and **push immediately**. The push is the
operator's work-has-started signal.
Commit and push at every step boundary thereafter. **Branch only — never merge
to main on your own initiative.**
---
## 2a. Step 1 — housekeeping: carry the 2026-07-24 rulings onto the issues
Immediately after Step 0, before any code change, post the design-chat
amendments to GitHub so the tracker never lags the design chat.
On **#40**, comment: the bucket splits into two briefs (this one, the code
half; Brief 5, the data half, which closes the issue); boss `death_message` is
**cut from scope** by operator ruling of 2026-07-24 and stays a scalar
`TextField` with no migration; report-category renderings (the vendor list
caption, the nothing-left-for-sale line, the repair sweep summary) are ruled
**out of scope** — speech gets pooled, renderings stay stable.
On **#138**, comment: the artifact refusal is **generic and never names a
rarity**, in any pool line or fallback, because unidentified items veil rarity
and vendor speech must not lift the veil — this is a standing no-leak rule on
vendor messages; the refusal pools therefore cover any future non-sellable
category without new lines; `get_sale_price` gains a zero floor, which is where
the exploit-proofing formerly provided by the worthless-sell refusal now lives.
Commit and push.
### Step 1b — file the `is_artifact` issue (combined file-and-fix)
The field removal in §3.10 was discovered while parsing this brief and has no
issue number yet. Issue-first law applies, so **file it now and capture the
number at runtime** — do not use a placeholder anywhere.
```
gh issue create \
  --title "Remove dead ItemInstance.is_artifact field — a trap for hand-authored artifacts" \
  --body "<see below>" \
  --milestone "Version 23" \
  --label bug --label B4 --label triaged \
  --assignee KnightOfNight/@me
```
Body content: `ItemInstance.is_artifact` (`models.py`, `default=False`) is read
by no code anywhere in the app and written by nothing — no seed row, no
generation path, no command. Its only presence is `admin.py`, where it is
surfaced in a fieldset labelled **Flags**. Artifacts are by settled design
one-of-a-kind items hand-authored by super-users through admin, so a
super-user creating one is looking at an authoritative-seeming checkbox that
does nothing; ticking it and leaving `rarity` alone yields an artifact with
none of #138's vendor protection, silently. `rarity` is the real marker
everywhere else (`RARITY_VALUE_MULTIPLIERS`, `RARITY_SECONDARY_SLOTS`,
`get_rarity_flag`, the seed's closed rarity-word vocabulary). Ruled in the
design chat 2026-07-24: delete the field so `rarity` is unambiguous. Fixed in
V23 Brief 4 (migration `0037`).
**HARD GATE.** Capture the issue number from the `gh issue create` output and
use it in every subsequent reference. If issue creation fails, if the number
cannot be captured cleanly, or if the created issue does not verify (correct
milestone, labels, assignee), then **stop immediately**: make zero code
changes, run the issues report, and write a closeout explaining what happened.
Do not proceed into §3 on a guess.
Commit and push.
---
## 3. Implementation
All paths are relative to `django/src/apps/shyland/`.
### 3.1 New module: `npc_voice.py`
Create a new module `npc_voice.py` holding every flavor pool this brief adds
plus one shared picker. Rationale: `consumers.py` is already ~4,060 lines and
this brief adds ~150 lines of pure content; the pools are data-shaped and
belong in one findable place. Brief 5 does not touch this module (its content
is seed data), but future voice work has a home.
The module's only import needs are `random`.
```python
"""v23 B4 (#40): the NPC voice pools.
Every transactional and reactive line that used to be a single hardcoded
string lives here as a pool. Selection is plain random choice — the
kibitz-style pattern that already existed, per the #40 ruling. No
per-player last-line state is tracked; these lines are low-frequency
enough that consecutive repeats are acceptable and stateful selection
would be novel architecture the ruling excluded.
NO-LEAK RULE (#138, operator ruling 2026-07-24): no line in this module
may name or imply an item's rarity, tier, or true name. Unidentified
items veil all three, and vendor speech must not lift the veil. Refusal
pools are deliberately generic so that they read correctly for any
non-sellable category, present or future.
"""
import random
def pick(pool, **fields):
    """Choose a line at random and substitute {placeholders}."""
    line = random.choice(pool)
    for key, value in fields.items():
        line = line.replace('{' + key + '}', str(value))
    return line
```
Every pool below is a module-level list in `npc_voice.py`. Every call site uses
`pick(POOL_NAME, field=value, ...)`.
### 3.2 `item_utils.get_sale_price` — the zero floor
**This is the load-bearing change for #138. Do not skip it.**
Current text in `item_utils.py`:
```python
def get_sale_price(item):
    """What a vendor pays: one third of value, minimum 1 copper."""
    return max(1, get_item_value(item) // 3)
```
Replace with:
```python
def get_sale_price(item):
    """What a vendor pays: one third of value, minimum 1 copper — except a
    worthless item, which pays nothing at all.
    v23 B4 (#138): vendors now accept zero-value items instead of refusing
    them, which reopens the disposal path for bound starter-kit junk. The
    zero floor is what keeps that from becoming a copper faucet — the free
    kit on Morra's shelf would otherwise sell back at 1 copper a piece,
    forever. The exploit-proofing that the old refusal provided now lives
    here, in arithmetic.
    """
    value = get_item_value(item)
    if value == 0:
        return 0
    return max(1, value // 3)
```
### 3.3 `cmd_sell` — the #138 rework
Three behavioral changes, all inside `cmd_sell` in `consumers.py`:
1. The `base_value == 0` refusal is **deleted** in both the single and bulk
   paths. Worthless items sell, for 0 copper, and the instance is deleted by
   the existing `do_sell` (compensated disposal, uncompensated).
2. Artifact-rarity items are **refused**, in both paths.
3. The `skipped` counter and the `Nothing sold — N worthless items skipped.`
   branch are **deleted entirely**. After this change, worthless items are no
   longer skipped, so that branch's only remaining population would be
   artifacts, which now have their own refusal lines.
**Single / index mode.** Current text:
```python
        if res.mode in ('single', 'index'):
            item = res.items[0]
            if get_item_value(item) == 0:
                await self.output("That's not worth anything to me.", 'warn')
                return
            display = item_ref(item)
            price = await self.do_sell(item, char)
            await self.output(f'You sell {display} for {self.format_amount(char, price)}.', 'success')
            await self.maybe_kibitz(room, vendor)
            return
```
Replace with:
```python
        if res.mode in ('single', 'index'):
            item = res.items[0]
            # v23 B4 (#138): artifacts are never bought, at any value. The
            # refusal is deliberately generic — it never names the rarity,
            # because an unidentified item veils it and vendor speech must
            # not lift the veil.
            if item.rarity == 'artifact':
                await self.output(
                    npc_voice.pick(
                        npc_voice.SELL_REFUSAL_SINGLE,
                        vendor=npc_display(vendor, capitalize=True),
                    ),
                    'warn',
                )
                return
            display = item_ref(item)
            price = await self.do_sell(item, char)
            # v23 B4 (#138): a transaction that nets nothing replaces the
            # payment sentence with the snark. The player still learns the
            # item is gone.
            if price == 0:
                await self.output(
                    npc_voice.pick(
                        npc_voice.SELL_WORTHLESS_SINGLE,
                        vendor=npc_display(vendor, capitalize=True),
                        name=display,
                    ),
                    'success',
                )
            else:
                await self.output(
                    npc_voice.pick(
                        npc_voice.SELL_SINGLE,
                        vendor=npc_display(vendor, capitalize=True),
                        name=display,
                        amount=self.format_amount(char, price),
                    ),
                    'success',
                )
            await self.maybe_kibitz(room, vendor)
            return
```
**Bulk mode.** The existing loop and its reporting block are replaced whole.
The new logic partitions into three groups and reports in a fixed order.
```python
        # v23 B4 (#138): artifacts are refused; everything else sells,
        # including worthless items (which pay 0 — see get_sale_price).
        sold_items = []
        prices = {}
        refused = 0
        for item in res.items:
            if item.rarity == 'artifact':
                refused += 1
                continue
            price = await self.do_sell(item, char)
            sold_items.append(item)
            prices[item.pk] = price
        paying = [i for i in sold_items if prices[i.pk] > 0]
        worthless = [i for i in sold_items if prices[i.pk] == 0]
        vendor_name = npc_display(vendor, capitalize=True)
        if sold_items:
            # v22 brief 2 (DD §6/§7): the shortfall report, verbatim.
            if res.requested:
                await self.output(
                    f'You only had {len(sold_items)} — the vendor was happy to take them.',
                    'success',
                )
            for name, group in self._aggregate_by_name(paying):
                group_total = sum(prices[i.pk] for i in group)
                if len(group) == 1:
                    await self.output(
                        npc_voice.pick(
                            npc_voice.SELL_SINGLE,
                            vendor=vendor_name,
                            name=item_ref(group[0]),
                            amount=self.format_amount(char, group_total),
                        ),
                        'success',
                    )
                else:
                    await self.output(
                        npc_voice.pick(
                            npc_voice.SELL_BULK,
                            vendor=vendor_name,
                            name=name,
                            qty=len(group),
                            amount=self.format_amount(char, group_total),
                        ),
                        'success',
                    )
            # One trailing remark covers every worthless rider, however many.
            if worthless:
                await self.output(
                    npc_voice.pick(
                        npc_voice.SELL_WORTHLESS_TRAILING, vendor=vendor_name,
                    ),
                    'success',
                )
            # One trailing remark covers every refused item, however many.
            if refused:
                await self.output(
                    npc_voice.pick(
                        npc_voice.SELL_REFUSAL_PARTIAL, vendor=vendor_name,
                    ),
                    'warn',
                )
            await self.maybe_kibitz(room, vendor)
        else:
            # Nothing moved at all — everything in the batch was refused.
            await self.output(
                npc_voice.pick(
                    npc_voice.SELL_REFUSAL_NONE, vendor=vendor_name,
                ),
                'warn',
            )
```
**Ruled reporting form, for the closeout:** the trailing form shipped. The
ruling on #138 sanctioned a fallback (snark on all-worthless transactions only,
mixed transactions silent) if the v22 aggregation plumbing made the trailing
form disproportionate. It did not — `_aggregate_by_name` takes a list and the
partition is clean. Report in the closeout that **the trailing form shipped**,
not the fallback.
**Note on the shortfall line:** it now counts `sold_items`, not the old `sold`
variable. Behavior is unchanged when no artifacts are present.
### 3.4 Sell refusal pools (`npc_voice.py`)
Generic by ruling. No line names a rarity, a tier, or a true name. These read
correctly for artifacts today and for any future non-sellable category.
```python
# --- Sell refusals (#138). Generic by ruling: never name the rarity. ---
SELL_REFUSAL_SINGLE = [
    '{vendor} looks it over and pushes it back toward you. "I\'m not interested in that."',
    '{vendor} does not reach for it. "I don\'t want to buy that."',
    '{vendor} declines. "That is not something I can put a number on."',
    '"No," {vendor} says. "Not that one."',
    '{vendor} returns it to you unpriced. "Keep it."',
    '{vendor} considers it, then sets it down again. "I would not know what to ask for it."',
]
SELL_REFUSAL_PARTIAL = [
    '{vendor} counts out the coin. "I took what I wanted, you can keep the rest."',
    '"That\'s all I want from you today," {vendor} says. "You can keep the other items for now."',
    '{vendor} pushes the remainder back across to you. "The rest stays yours."',
    '"I\'ll take these," {vendor} says. "Not the rest."',
]
SELL_REFUSAL_NONE = [
    '{vendor} looks over what you\'re carrying and declines all of it. "I\'m not interested in any of it."',
    '"I don\'t recognize anything you\'re carrying," {vendor} says, "and I wouldn\'t even know how much to pay you for it."',
    '{vendor} takes nothing. "There\'s nothing here I can use."',
    '"Not today," {vendor} says. "None of it."',
]
# Last-ditch guard rail. Not a pool: it has no population today (after
# #138, artifacts are the only refusable category and they have voiced
# pools above). If this string ever appears in play, that is the signal
# that a new non-sellable category shipped without its own voice — author
# a proper pool then.
SELL_REFUSAL_FALLBACK = "You can't sell that."
```
`SELL_REFUSAL_FALLBACK` is defined and exported but has **no call site in this
brief**. That is intentional and must not be "fixed" by wiring it somewhere.
### 3.5 Sell and buy transaction pools (`npc_voice.py`)
```python
# --- Sell acknowledgments (#40). ---
SELL_SINGLE = [
    'You sell {name} for {amount}.',
    '{vendor} takes {name} and pays you {amount}.',
    '{name} changes hands for {amount}.',
    'You part with {name}. {vendor} parts with {amount}.',
]
SELL_BULK = [
    'You sell {name} ×{qty} for {amount}.',
    '{vendor} takes {name} ×{qty} and counts out {amount}.',
    'You sell {name} ×{qty}. {amount} for the lot.',
]
# --- Worthless acceptance (#138). Replaces the payment sentence. ---
SELL_WORTHLESS_SINGLE = [
    '{vendor} takes {name} off your hands. No coin changes hands, and none was going to.',
    '"I\'ll get rid of that for you," {vendor} says, taking {name}. "Free of charge. Mine, not yours."',
    '{vendor} accepts {name} the way one accepts trash from a guest: politely, and straight into the bin.',
    '{vendor} takes {name} and pays you exactly what it\'s worth. Nothing.',
    '"You want this gone? It\'s gone," {vendor} says, and {name} disappears under the counter. No coin follows.',
]
SELL_WORTHLESS_TRAILING = [
    '{vendor} sweeps the rest off the counter too. "That I\'ll take for free — call it a courtesy."',
    '"And I\'ll take the junk off your hands as well," {vendor} adds. "No charge. To either of us."',
    '{vendor} takes the worthless remainder as well, and pays for exactly none of it.',
    '"The rest isn\'t worth coin," {vendor} says, dropping it out of sight anyway. "But it\'s gone."',
]
# --- Buy acknowledgments (#40). The vendor never spoke here before. ---
BUY_SINGLE = [
    'You buy {name} for {amount}.',
    '{vendor} takes your coin and hands over {name}. ({amount})',
    'You hand over {amount}; {vendor} hands over {name}.',
    '{name} is yours for {amount}.',
]
BUY_BULK = [
    'You buy {name} ×{qty} for {amount}.',
    '{vendor} counts out {name} ×{qty} and takes {amount} for the lot.',
    'You buy {name} ×{qty}. {amount}, all told.',
]
SOLD_OUT = [
    'Sold out.',
    'That shelf is empty.',
    '{vendor} has none of those left.',
]
```
### 3.6 `cmd_buy` — wire the buy pools
In `cmd_buy`, replace the two success outputs and the sold-out output with
`npc_voice.pick` calls against `BUY_SINGLE`, `BUY_BULK`, and `SOLD_OUT`.
Interpolate `vendor=npc_display(vendor, capitalize=True)`,
`name=item_ref(result[0])` for the single form,
`name=get_display_name_with_tier(result[0])` and `qty=qty` for the bulk form,
and `amount=self.format_amount(char, total)`.
Categories are unchanged: successes stay `'success'`, sold-out stays `'warn'`.
Leave the shortfall line (`They only had {qty}.`) and both can't-afford lines
exactly as they are — they are already covered by the v22 B5 amendment 3
shortfall ruling and are not flavor sites.
### 3.7 Repair pools (`npc_voice.py`)
Free ("pity") repair lines become per-NPC pools. The three Verdant menders get
their own pools rather than sharing the generic fallback — their voices are
authored in their NPC descriptions and the fallback exists for future
repairers, not for them.
```python
# --- Free repair (#40). Keyed by NPC slug; per-NPC voice. ---
PITY_REPAIR_LINES = {
    'morra': [
        'Morra turns the piece over once, snorts softly, and fixes it for '
        'nothing. "Come back when you\'ve got something worth charging for."',
        'Morra fixes it without asking and without charging. "I\'m not taking '
        'coin for that. I\'d be embarrassed."',
        'Morra works the damage out in three motions and waves you off. '
        '"Don\'t. Just don\'t."',
    ],
    'pella': [
        "Pella tuts over the wear like it's a personal affront and mends it "
        'free. "There. Don\'t thank me, just eat something."',
        'Pella has it mended before you\'ve finished offering to pay. "Coin? '
        'For that? Absolutely not."',
        'Pella repairs it and presses it back into your hands. "No charge. '
        'You\'ll be back with something worse, and I\'ll charge you then."',
    ],
    'ferwick': [
        'Ferwick waves off payment before you can reach for your purse. '
        '"The city gave it to you; the city can keep it standing."',
        'Ferwick mends it and refuses your coin twice. "It costs the city '
        'nothing. It costs you nothing. Good."',
        'Ferwick sets it right and shrugs. "Free issue, free repair. That\'s '
        'how it was explained to me, anyway."',
    ],
    'repairbot-prime': [
        'Repairbot Prime completes the work in silence. "COST: NEGLIGIBLE. '
        'WAIVED. MAINTAIN YOUR EQUIPMENT."',
        'Repairbot Prime restores the item in four seconds. "BILLING SKIPPED. '
        'VALUE BELOW THRESHOLD. NEXT."',
        'Repairbot Prime repairs it without prompting. "NO CHARGE ISSUED. THIS '
        'UNIT DECLINES TO INVOICE FOR THAT."',
    ],
    'maro-the-mender': [
        'Maro mends it on the bench without looking up. "That one\'s free. '
        'Wouldn\'t feel right otherwise."',
        'Maro turns it in the light, fixes it, and hands it back. "No charge. '
        'Bring me something harder next time."',
        'Maro repairs it and glances at the shard as if checking. "Free," he '
        'says. "We agree on that."',
    ],
    'tavik-the-mender': [
        'Tavik has it stitched before you sit down. "Nothing owed. It was '
        'barely work."',
        'Tavik mends it and sets it beside you. "Travelers always need '
        'something sewn. I don\'t charge for the easy ones."',
        'Tavik works the awl through twice and calls it done. "Keep your coin. '
        'That wasn\'t worth taking it for."',
    ],
    'old-brammel': [
        'Old Brammel repairs it by the light of the little lamp and refuses '
        'payment. "Not for that, friend. Not for that."',
        'Old Brammel mends it, slow and sure. "No coin. I\'ve been doing this '
        'longer than that thing\'s been broken."',
        'Old Brammel hands it back mended. "Free. Tell the lamp I said so."',
    ],
}
PITY_REPAIR_FALLBACK = [
    '{name} looks your battered gear over, takes pity, and repairs it for nothing.',
    '{name} fixes it without mentioning a price, which is its own kind of answer.',
    '{name} makes the repair and waves off your coin.',
]
# --- Paid repair outcomes (#40). Shared pools: the composition sites
# interpolate the repairer where they already had it, and the bulk sweep
# never named the repairer to begin with. Per-repairer voice here would
# need architecture the ruling excluded. ---
REPAIR_SUCCESS_BULK = [
    '{name} is restored to full condition. ({cost})',
    '{name} comes back sound. ({cost})',
    '{name} is whole again. ({cost})',
    'The work holds — {name} is as good as it was. ({cost})',
]
REPAIR_SUCCESS_SINGLE = [
    '{repairer} restores your {name} to full condition. ({cost})',
    '{repairer} works the damage out of your {name} and hands it back sound. ({cost})',
    '{repairer} takes your {name}, takes their time, and returns it whole. ({cost})',
    'Your {name} comes back from {repairer} in full condition. ({cost})',
]
REPAIR_FAIL_BULK = [
    "The mending on {name} didn't take. ({cost})",
    'The repair on {name} fails to hold. ({cost})',
    '{name} resists the work — no better than before. ({cost})',
    'The fix on {name} comes apart under the tools. ({cost})',
]
REPAIR_FAIL_SINGLE = [
    "{repairer} works on your {name}, but the mending didn't take. ({cost})",
    '{repairer} tries your {name} twice and gives up. Nothing holds. ({cost})',
    '{repairer} does the work, but your {name} is no better for it. ({cost})',
    'Your {name} defeats {repairer} — the repair simply refuses to set. ({cost})',
]
REPAIR_POOR_BULK = [
    "You can't afford to repair {name} ({cost}) — you stop there.",
    'Repairing {name} would cost {cost}. You stop there.',
    "{name} needs {cost} you don't have. The sweep stops there.",
]
REPAIR_POOR_SINGLE = [
    "Repairing your {name} costs {cost} — you can't afford it.",
    'Your {name} would take {cost} to mend. You have less.',
    "{cost} to fix your {name}. You can't cover it.",
]
```
### 3.8 `cmd_repair` — wire the repair pools
Replace `_pity_repair_line` in `consumers.py` with a version that picks from
the pools:
```python
def _pity_repair_line(repairer):
    pool = npc_voice.PITY_REPAIR_LINES.get(repairer.definition.slug)
    if pool:
        return npc_voice.pick(pool)
    return npc_voice.pick(
        npc_voice.PITY_REPAIR_FALLBACK,
        name=npc_display(repairer, capitalize=True),
    )
```
Delete the old module-level `KIBITZ_LINES`, `PITY_REPAIR_LINES`, and
`PITY_REPAIR_FALLBACK` constants from `consumers.py` — they now live in
`npc_voice.py`.
In `cmd_repair`, replace the six hardcoded outcome f-strings with `pick` calls:
| Site | Pool | Fields |
|---|---|---|
| bulk, can't afford | `REPAIR_POOR_BULK` | `name`, `cost` |
| bulk, success (paid) | `REPAIR_SUCCESS_BULK` | `name`, `cost` |
| bulk, failure | `REPAIR_FAIL_BULK` | `name`, `cost` |
| single, can't afford | `REPAIR_POOR_SINGLE` | `name`, `cost` |
| single, success (paid) | `REPAIR_SUCCESS_SINGLE` | `repairer`, `name`, `cost` |
| single, failure | `REPAIR_FAIL_SINGLE` | `repairer`, `name`, `cost` |
`cost` is `self.format_amount(char, cost)`. `repairer` is
`npc_display(repairer, capitalize=True)`. `name` is the already-computed
`get_display_name_with_tier(item)` local.
Message categories are unchanged (`success` for success, `warn` for failure and
can't-afford). The bulk sweep's closing `Repaired N items, ...` summary line is
a **report**, not speech — leave it exactly as it is (see §3.9).
The free-repair branch condition stays `get_item_value(item) == 0`. It is
unchanged by #138: a repair that costs nothing and a sale that pays nothing are
independent behaviors.
### 3.9 Kibitz and aggro pools (`npc_voice.py`), and the ruled exceptions
```python
# --- Kibitz (#40). Machinery already existed; the pool grows. ---
KIBITZ_LINES = [
    '{other} watches the exchange and nods approvingly.',
    '{other} pretends not to supervise, and supervises.',
    '{other} rearranges the shelf, satisfied.',
    '{other} makes a small noise that could be approval or indigestion.',
    '{other} counts something on the far shelf, twice, loudly.',
    '{other} looks away the instant you glance over.',
]
# --- Aggro engagement (#40). One string served every aggressive NPC in
# the game at three call sites. {name} is the ordinal-aware display name.
AGGRO_ENGAGE = [
    '{name} snarls and moves to attack!',
    '{name} closes on you without warning!',
    '{name} sees you and comes straight in!',
    '{name} breaks toward you, fast!',
    '{name} gives no warning at all — it attacks!',
    '{name} turns on you and charges!',
]
```
**Wire `AGGRO_ENGAGE` at all three sites**, which must stay in lockstep:
- `consumers.py`, the walk-in aggro branch of the movement path
- `consumers.py`, the flee-into-aggro branch
- `management/commands/run_tick_engine.py`, the respawn-engagement branch
Each currently builds `f"{npc_display_name(npc, aggro_npcs, capitalize=True)} snarls and moves to attack!"`.
Replace each with
`npc_voice.pick(npc_voice.AGGRO_ENGAGE, name=npc_display_name(npc, aggro_npcs, capitalize=True))`.
Categories stay `'combat'`. The tick-engine site must import `npc_voice` at
module level — `pick` touches no ORM, so no `database_sync_to_async` wrapper is
needed there.
Move `KIBITZ_LINES` out of `consumers.py` and update `maybe_kibitz` to call
`npc_voice.pick(npc_voice.KIBITZ_LINES, other=npc_display(other, capitalize=True))`.
**Ruled exceptions — do NOT pool these** (operator ruling 2026-07-24):
| Site | Why excluded |
|---|---|
| Vendor list caption (`{Vendor} offers...`) | Table chrome in the `report` category. A caption that changes between identical `list` commands is instability, not voice. |
| `{Vendor} has nothing left for sale.` | `report` category — a status rendering, not speech. |
| Repair sweep summary (`Repaired N items, ...`) | `system` category — a tally. |
| `NpcDefinition.death_message` | Cut from scope. Stays a scalar `TextField`. No migration. |
The governing line: **speech gets pooled; renderings stay stable.** This is
consistent with the standing distinction that timestamps mark events, not
renderings.
### 3.10 Remove `ItemInstance.is_artifact` (migration `0037`)
Three edits plus one migration. Cite the issue number captured in Step 1b in
every comment and in the migration's docstring.
1. **`models.py`** — delete the field:
   ```python
   is_artifact = models.BooleanField(default=False)
   ```
   Delete the blank line that isolated it as well, so `active_curse` and
   `is_identified` sit in their natural order.
2. **`admin.py`** — delete the entire fieldset group. It is the only field in
   the group, so the group goes with it:
   ```python
   ('Flags', {'fields': ('is_artifact',)}),
   ```
   Verify no `list_display`, `list_filter`, `search_fields`, or `readonly_fields`
   entry references `is_artifact` before finishing — Django raises at startup on
   a dangling admin reference, and the current `list_filter` is
   `('rarity', 'is_equipped', 'is_broken', 'is_unidentifiable')`, which is clean.
3. **Migration** — generate it, do not hand-write it:
   ```
   manage.py makemigrations shyland
   ```
   Expect exactly one operation, `RemoveField(model_name='iteminstance', name='is_artifact')`,
   landing as `0037_remove_iteminstance_is_artifact.py`. If the generated
   migration contains any other operation, **stop and report** — that means
   something else drifted and this brief is not the place to absorb it.
   Add a docstring to the generated migration naming the issue and the reason:
   the field was dead weight that read as authoritative in admin, and `rarity`
   is the single artifact marker.
4. The refusal condition in §3.3 stays exactly `item.rarity == 'artifact'`.
   With the boolean gone there is no second marker to consider, and no
   defensive `or` clause is warranted. Do not add one.
**Data safety.** No code reads the field and no seed writes it, so no data
migration, no back-fill, and no deploy-time data action are required. The
column drop applies with the ordinary `make migrate` in §8.
---
## 4. Tests
Add `django/src/apps/shyland/tests/test_npc_voice.py`. Required coverage:
1. **Zero floor.** `get_sale_price` returns exactly `0` for an item whose
   `get_item_value` is 0, and `max(1, value // 3)` otherwise. Assert the
   1-copper case explicitly (a `base_value=1`, `mk_tier=1`, common item pays 1,
   not 0) so the floor is not over-corrected.
2. **Worthless sell succeeds.** Selling a `base_value=0` item deletes the
   instance, leaves `character.copper` unchanged, and emits a line drawn from
   `SELL_WORTHLESS_SINGLE`. Assert the emitted line is a member of the pool
   (after substitution) rather than asserting one exact string.
3. **Bound worthless sell succeeds.** Same as (2) with `is_soulbound=True` —
   this is the #138 trap, and it must open. Assert the instance is gone.
4. **Artifact refused, single.** Selling an artifact emits a `warn` line from
   `SELL_REFUSAL_SINGLE` and the instance still exists.
5. **Artifact refused, bulk partial.** A batch of paying items plus one
   artifact: the paying items sell, the artifact survives, exactly one
   `SELL_REFUSAL_PARTIAL` line is emitted.
6. **Artifact refused, bulk total.** A batch of artifacts only: nothing sells,
   exactly one `SELL_REFUSAL_NONE` line is emitted, no `SELL_REFUSAL_PARTIAL`
   line is emitted.
7. **Mixed bulk trailing form.** Paying items plus worthless riders: the
   payment aggregate lines appear, followed by exactly one
   `SELL_WORTHLESS_TRAILING` line. Assert the trailing line comes after the
   payment lines in sequence order.
8. **No-leak invariant.** Iterate every string in `SELL_REFUSAL_SINGLE`,
   `SELL_REFUSAL_PARTIAL`, `SELL_REFUSAL_NONE`, and `SELL_REFUSAL_FALLBACK` and
   assert none contains any of `artifact`, `legendary`, `epic`, `rare`,
   `uncommon`, `common`, or `Mk` (case-insensitive). This test is the standing
   guard on the no-leak rule.
9. **Pity pool coverage.** Every slug in `PITY_REPAIR_LINES` has at least 3
   entries, and every one of the seven repairer slugs
   (`morra`, `pella`, `ferwick`, `repairbot-prime`, `maro-the-mender`,
   `tavik-the-mender`, `old-brammel`) is a key.
10. **Aggro lockstep.** Assert `AGGRO_ENGAGE` has more than one entry, and that
    the literal string `snarls and moves to attack` appears in **no** Python
    source file under `apps/shyland/` outside `npc_voice.py` — the guard that
    all three call sites were converted.
11. **Substitution completeness.** For every pool in `npc_voice.py`, assert
    that after substituting the fields its call site supplies, no `{` remains
    in the rendered line. A table of pool → expected field names is
    authoritative for this test.
12. **Field is gone.** Assert `'is_artifact'` is absent from
    `[f.name for f in ItemInstance._meta.get_fields()]`, and that the string
    `is_artifact` appears in no Python source file under `apps/shyland/`
    outside `migrations/`. This is the guard that the model, the admin
    fieldset, and any stray reference all went together.
Run the whole suite: `manage.py test apps.shyland -t /app`. Report the final
count. The suite stood at **321/321** at the close of Brief 3; it must be
321 + your new tests, with **zero failures and zero errors**.
---
## 5. Verification
1. Full suite green (§4).
2. `grep -rn "That's not worth anything to me" apps/shyland/` returns nothing.
3. `grep -rn "worthless item" apps/shyland/consumers.py` returns nothing — the
   skipped-counter reporting is gone.
4. `grep -rn "snarls and moves to attack" apps/shyland/` returns exactly one
   hit, in `npc_voice.py`.
5. `grep -rn "PITY_REPAIR_LINES\|KIBITZ_LINES" apps/shyland/consumers.py`
   returns only the `npc_voice.`-qualified references, not definitions.
6. Confirm the migration inventory is exactly right: `0037_remove_iteminstance_is_artifact.py`
   exists and contains exactly one `RemoveField` operation, and
   `manage.py makemigrations --check --dry-run` reports **no further changes**
   once it is in place. **If any second migration is wanted, stop and report** —
   this brief authorizes precisely one.
7. Confirm the Django admin loads: `manage.py check` passes with no
   `admin.E***` errors (the dangling-fieldset failure mode).
8. `grep -rn "is_artifact" apps/shyland/ --include=*.py | grep -v migrations/`
   returns nothing.
---
## 6. Issue closure (gated on §4 and §5 passing)
- **Close `#138`** with a comment summarizing: the zero floor in
  `get_sale_price`, the removed refusal, the artifact refusal in both paths,
  the generic no-leak pools, and the fact that the trailing form shipped.
- **Close the Step 1b issue** (the `is_artifact` removal) with a comment
  naming migration `0037` and confirming the admin fieldset went with the
  field.
- **Do NOT close `#40`.** Comment on it recording which half landed (the code
  sites) and that Brief 5 closes it with the data half. State explicitly in the
  comment that `death_message` was cut from scope by the 2026-07-24 ruling.
---
## 7. Architecture doc update (LAST STEP — gated)
**This step is gated on all implementation and verification steps above being
complete and passing.**
Update `docs/shyland/Shyland_Architecture_v23.md` **in place**. Do not create a
new file. Do not bump the version stamp — it stays at Version 23.0. Update the
header's commit hash to this brief's final implementation commit.
Sections to change:
- **Header blockquote** — extend the leading commit-hash sentence with a v23
  brief 4 clause covering: vendors accept worthless items for 0 copper with the
  zero floor moved into `get_sale_price` (#138), artifacts refused at any value
  in both sell paths with generic no-leak refusal pools, and the new
  `npc_voice.py` pool module replacing single hardcoded strings at the repair,
  vendor, kibitz, and aggro-engagement sites (#40, code half). Add to the
  **Version 23.0 — IN PROGRESS** paragraph that Brief 4 applied fourth.
- **§1 Overview** — one sentence in the v23 run describing Brief 4.
- **§4.3 WebSocket consumer** — `cmd_sell`'s new three-way partition
  (paying / worthless / refused), the deleted skipped-counter branch, and the
  fixed report ordering.
- **§4.1 Models** — `ItemInstance.is_artifact` removed (migration `0037`);
  `rarity` is the single artifact marker. Record why: the field was read by
  nothing while presenting as authoritative in admin, and artifacts are
  hand-authored through admin.
- **§4.6 Item generation and utilities** — `get_sale_price`'s zero floor and
  why it carries the exploit-proofing the old refusal used to.
- **§4.14 Command layer** — the sell refusal's place in the three-layer
  doctrine (world-declined, warn voice) and the no-leak rule on vendor speech.
- **New §4.17 — NPC voice pools (`npc_voice.py`)** — the module's purpose, the
  `pick` helper, the pool inventory, the no-leak rule, and the ruled exceptions
  (report-category renderings and `death_message` stay unpooled).
Write the architecture doc **header first, then one section at a time** — never
one giant operation.
---
## 8. Deploy (operator-authorized, in session)
After the architecture doc is committed and pushed, deploy to production so the
operator can playtest:
```
make build && make migrate
```
**Exactly this invocation.** Not `make prod`. Not `make deploy`. `DOCKER_HOST`
must already be verified from pre-flight.
**PENDING DEPLOY-TIME ACTIONS: none.** The brief's one migration (`0037`) is a
plain column drop applied by `make migrate` in this same step; there is no data
command to run separately and nothing to defer. If the deploy is not authorized in session, say so in the closeout.
---
## 9. Ready after deploy — operator playtest checklist
1. Equip a free starter-kit piece (binds it), then `sell` it to any vendor —
   it should leave your inventory with a snarky line and no payment. **This is
   the #138 trap opening.**
2. `sell all` with a mix of paying items and bound kit junk — payment lines
   first, then one trailing remark covering the junk.
3. `sell` the same worthless item type several times across a few visits —
   confirm the snark varies.
4. `repair` a free kit item at Morra, Pella, Ferwick, Repairbot Prime, Maro,
   Tavik, and Old Brammel — each should speak in their own voice, and repeat
   visits should vary.
5. `repair` a paid item several times, succeeding and failing — confirm both
   outcome pools vary.
6. `buy` something several times, singly and in quantity — confirm the vendor
   now speaks and varies.
7. Complete a trade in a gazebo with two vendors present — confirm kibitz has
   new lines.
8. Walk into an aggro room several times — confirm the engagement line varies,
   and check the same after a failed flee and after a respawn tick.
9. `list` at any vendor several times — the caption must **not** vary.
10. Kill a boss — the death message must be unchanged.
11. Open an `ItemInstance` in the Django admin — the **Flags** section should
    be gone entirely, and every other fieldset should render normally.
---
## 10. Closeout report
Commit as `docs/shyland/Shyland_V23_Brief_4_Closeout_Report.txt`. Include:
- Final commit hash of the implementation
- Full test suite count and result
- The Step 1b issue number, and confirmation of its milestone/labels/assignee
- Confirmation that exactly one migration was generated (`0037`), with its operation list
- Confirmation that **the trailing form shipped** for mixed bulk sells
- The §5 grep results, verbatim
- **PENDING DEPLOY-TIME ACTIONS: none**
- Deploy result (authorized / executed / output summary)
- Issue state: `#138` closed, the Step 1b issue closed, `#40` open with a comment
- Any discrepancies, including whitespace drift on the Step 0 self-commit
## 11. Final step
Run the issues report.
