# Shyland V25.15 — Brief 1: Bulk Buy/Sell Batching

- **Release:** Version 25.15 (point release) — milestone `Version 25.15`
- **Branch:** `version_25_15`
- **Founding ticket:** #321 (sole milestone member — scope law: one founding ticket, one brief)
- **Authored:** 2026-09-05, V25.15 design session
- **Session type to apply this brief:** implementation session on `version_25_15`

## 1. What this release does

`sell all <noun>` / `sell all <rarity>` and large `buy <N> <item>` take minutes at large inventory scale because the engine does the work item-by-item: the bulk-sell arm runs **one database transaction per item** (11,000 items ≈ 11,000 transactions), and buy creates instances with **one serial INSERT per unit** inside its single transaction. V25.15 batches both: a bulk sale becomes **one atomic transaction with three writes** (one character lock, one copper update, one bulk delete), and a buy persists all its instances in **one `bulk_create`**. Sub-second at any scale.

**Operator ruling (2026-09-05, recorded on #321):** the earlier "cheap cap" comment on #321 is superseded — no quantity cap ships. Batching only. **Zero player-facing behavior change: every output line, refusal, and ordering is byte-identical to 25.14.** The admin-scale inventories that surfaced this are off-design, but they point at future scaling; the O(n)-transactions shape is removed outright.

Scope per the scope law: vendor transactions (`buy`/`sell`) only. `drop`/`pickup`/`use` per-item loops are explicitly out of scope for this release.

## 2. Technical premises — verified at writing time

Per the technical-coherence rule (#252), every claim below was **confirmed by file-read against `version_25_15` @ 2766496** (the 25.14 merge tip) during the authoring session. The implementation session's pre-flight re-diffs these against the code before writing anything; a load-bearing mismatch is a HARD STOP.

1. **`do_buy(self, entry, character, qty=1)`** — `consumers.py:4464`, `@database_sync_to_async` (decorator on the preceding line). One `transaction.atomic()`: `select_for_update` on the `VendorEntry` (re-checking stock) then on `Character`; `currency.subtract` for the whole price; `fresh.sold_count += qty`; then a `for _ in range(qty)` loop calling `generate_item_instance(definition=fresh.item_definition, mk_tier=fresh.mk_tier, rarity='common', owner=char)` + `item.save()` per unit, appending to `items`. Returns `items`, or `'poor'` / `'sold_out'` sentinels. After the block: `self.character.copper = char.copper`. Sole caller: `cmd_buy` at `consumers.py:2292`.
2. **`do_sell(self, item, character)`** — `consumers.py:4497`. Computes `price = get_sale_price(item)`, then one `transaction.atomic()`: `select_for_update` on `Character`, `currency.add`, `save(update_fields=['copper'])`, `item.delete()`. Returns `price`. Exactly two callers: the single/index sell arm (`consumers.py:2369`) and the bulk arm's per-item loop (`consumers.py:2414`).
3. **`cmd_sell` bulk arm** — `consumers.py:2395`–2490: iterates `res.items`, skips `rarity == 'artifact'` (counting `refused`), awaits `do_sell` per item, keys the `prices` map by `id(item)` — the in-file comment (2404–2408) explains why: `item.delete()` nulls the in-memory pk, so pk-keying collapsed groups. Output composition after the loop: shortfall line (`res.requested`), `_aggregate_by_name(paying)` count-form lines, one worthless trailing remark, one refused trailing remark (or `SELL_REFUSAL_NONE` when nothing moved), the #150 consumable teaching note (`res.bulk_excluded`), `maybe_kibitz`.
4. **`generate_item_instance(definition, mk_tier, rarity, owner=None, room=None, gift=False)`** — `item_utils.py:98`. **Returns an unsaved `ItemInstance`** by documented design ("Generate (but do not save)… Call `.save()` on the returned instance to persist it"). All rolled state lands in fields on the instance itself (`rolled_primary_stats` / `rolled_secondary_stats` JSON fields, `damage_midpoint`/`damage_spread`); **no child rows are created**. The #211 Mk-mismatch guard runs at the top of the function body, so it fires per-generation regardless of how persistence happens.
5. **`ItemInstance.save()` override** — `models.py:761`–772: enforces the exactly-one-location invariant (exactly one of `owner_id` / `current_room_id` / `corpse_id` non-null), raising `ValidationError` otherwise. **`bulk_create` skips `save()`** — this brief must preserve the invariant explicitly (step 4.2). No other override on the model (`__str__` aside); **no `post_save`/`post_delete`/`@receiver` signal registrations exist anywhere in `apps/shyland/` non-test modules** (grep-verified).
6. **Incoming FK to `ItemInstance`:** exactly one — `CombatAction.item`, `on_delete=SET_NULL` (`models.py:1244`). Django's deletion collector honors `SET_NULL` for queryset `.delete()` exactly as for instance deletes. (`ItemInstance.owner` CASCADE etc. are *outgoing* and irrelevant to deleting instances.)
7. **`get_sale_price(item)`** — `item_utils.py:64`: pure arithmetic over `item.definition.base_value × mk_tier × rarity multiplier` (÷3, min 1, exact-0 for worthless). No queries when the definition is loaded — and it always is: **`get_carried_items` uses `.select_related('definition')`** (`consumers.py:4274`–4278), which feeds the sell resolver.
8. **`currency.add` / `currency.subtract`** — `currency.py:94`/101: pure functions on integers; `subtract` raises `ValueError` on insufficient funds. All money math goes through them (standing law).
9. **Equipped items never reach sell:** the v22 resolver excludes equipped items from sell/drop pools upstream; `do_sell` today performs no equipped check and this brief adds none — parity, not a new trust decision.
10. **Suite baseline:** 934 in-container tests green at the 25.14 closeout.

## 3. Design rules — do not deviate

- **Output is byte-identical.** No new lines, no removed lines, no reordering, in any buy/sell path. The whole diff is engine-side.
- **Single-item arms untouched:** `do_sell` and the single/index sell arm stay exactly as shipped. `cmd_buy`'s pre-checks and messages stay exactly as shipped.
- **All money math through `apps.shyland.currency`** inside `transaction.atomic()` with `select_for_update` on the Character row — the shipped locking discipline, preserved.
- **Buy stays all-or-nothing (#22).** The whole quantity succeeds or fails as one transaction, exactly as today.
- **No model schema change, no migration, no seed change, no client change.** Migration head stays `0056`. (The invariant-helper extraction in step 4.2 is pure Python on the model class.)
- **No quantity cap of any kind** — the superseded direction from #321's comment thread must not ship in any form.

## 4. Implementation steps

Commit and push at every step boundary (branch only — never merge). Step 0 (closeout-report stub push) is owned by the `implementation-session` start ritual.

### 4.1 Version start (opening act — first brief of the release)

Bump `SHYLAND_VERSION` to `"25.15-DEV"` in its own commit, moving the pin-test assertion in the same commit. Then run the version-start `make deploy-dev` from the worktree.

### 4.2 Extract the location invariant into a reusable check

On `ItemInstance`, extract the body of the `save()` override's check (models.py:762–771) into a method, e.g. `enforce_location_invariant(self)`, raising the identical `ValidationError` with the identical message. `save()` calls it then `super().save()`. Behavior byte-identical for every existing caller.

### 4.3 Batch buy persistence in `do_buy`

Inside the existing atomic block, replace the generate-and-save loop:

- Loop `range(qty)` calling `generate_item_instance(...)` exactly as today (each instance still rolls independently; the #211 guard still fires per-generation), collecting **unsaved** instances.
- Call `instance.enforce_location_invariant()` on each (this is the `save()`-skip compensation — the invariant holds by construction here, and now provably).
- Persist with one `ItemInstance.objects.bulk_create(items, batch_size=500)` (explicit batch size — do not rely on backend auto-chunking). PostgreSQL returns primary keys on the created instances.
- `items` (the returned list) keeps the exact return contract; `'poor'`/`'sold_out'` sentinels, `sold_count` increment, `currency.subtract`, and the `self.character.copper` sync are untouched.

Note: `bulk_create` sets `auto_now_add` (`created_at`) normally.

### 4.4 New `do_sell_bulk(self, items, character)`

A new `@database_sync_to_async` method beside `do_sell`, used **only** by the bulk arm:

- Compute `price = get_sale_price(item)` for every item **before** the transaction (pure Python; definitions preloaded — premise 7). Build `prices = {item.pk: price}` and `total = sum(prices.values())`.
- One `transaction.atomic()`: `Character.objects.select_for_update().get(pk=character.pk)`; `char.copper = currency.add(char.copper, total)`; `char.save(update_fields=['copper'])`; `ItemInstance.objects.filter(pk__in=list(prices)).delete()`.
- After the block: `self.character.copper = char.copper`. Return `prices`.

Crash semantics change from per-item partial progress to **all-or-nothing rollback** — an improvement, ruled acceptable on #321. Worthless items (price 0) ride the same batch: `currency.add` of their 0 contribution and deletion, same net effect as today.

### 4.5 Rewire `cmd_sell`'s bulk arm

- Partition `res.items` first: `refused` counts artifacts (unchanged rule); `sellable` is the rest.
- If `sellable` is empty, skip the sale call entirely — the existing "nothing moved" output branch already handles it (today the loop simply never sells; keep that outcome identical).
- One `prices = await self.do_sell_bulk(sellable, char)`; `sold_items = sellable`.
- **The prices map is now keyed by pk, and safely so:** queryset `.delete()` never touches the held Python instances, so their pks survive — the `id()` workaround's premise (instance `.delete()` nulling in-memory pks, comment at consumers.py:2404) no longer applies to this arm. Re-key the composition lookups (`prices[i.pk]`) and **replace that comment** with one explaining the new shape. 
- Everything downstream — shortfall line, `_aggregate_by_name` grouping and count-form lines, worthless trailing remark, refused trailing remark, `SELL_REFUSAL_NONE` branch, #150 teaching note, `maybe_kibitz` — is untouched.

### 4.6 Tests — `test_v25_15_brief1.py`

New in-container tests (invocation: `python manage.py test apps/shyland/tests` via `docker exec` — the directory-path form, the only working form):

1. **Bulk sell correctness:** character with a mixed inventory (≥2 paying definitions with multiple instances each, ≥1 worthless instance, 1 artifact). After the bulk sell: copper delta equals the sum of `get_sale_price` over non-artifact items; all non-artifact rows deleted; the artifact row survives.
2. **Group-total integrity:** multiple same-definition, same-Mk instances at different prices (different **rarities** — `_aggregate_by_name` groups by display name = definition + tier, so they land in one group while the rarity multiplier varies their prices; confirmed against `consumers.py:3590`) sum correctly per group — the regression guard for the old pk-collapse defect, now guarding the pk-keyed shape.
3. **Bulk sell query bound:** `assertNumQueries`-measured count for `do_sell_bulk` is **equal at two different inventory sizes** (e.g. 10 vs 50 items) — the count-independence assertion, stronger than pinning an exact number.
4. **Bulk buy correctness:** `do_buy` with qty ≈ 40: exactly qty instances created, each with populated `rolled_primary_stats`, owner set, unbound; copper charged `price × qty`; `sold_count` incremented by qty.
5. **Bulk buy query bound:** query count equal at qty 5 vs qty 40 (one `bulk_create` batch each at batch_size 500).
6. **Invariant helper:** `enforce_location_invariant` raises on zero and on two locations, passes on exactly one; `save()` still enforces (existing-path pin).
7. **Buy sentinels unchanged:** `'poor'` and `'sold_out'` still return from inside the transaction with no instances created.
8. Full suite green: 934 + the new tests, zero existing tests changed (any needed change is a deviation, recorded in the closeout).

### 4.7 Dev deploy + issue close

`make deploy-dev` from the worktree once implementation and all verification pass. Then close **#321** (gated on verification passing), with a closing comment naming this brief and the release.

### 4.8 Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. `Shyland_Architecture_v25.md`, updated in place per the point-release rule:

- Stamp → **25.15**; **the header hash moves** (architectural change: transaction shape of the money paths).
- Header version-note block: one new `> **Version 25.15 (point release)…**` entry in the established pattern.
- **§4.1:** the exactly-one-location invariant passage notes the check now lives in `enforce_location_invariant()` (called by `save()` and by `do_buy`'s bulk path).
- **§4.3:** the `cmd_sell` bulk-path passage (~line 556: the `id()`-keyed price-map sentence is superseded — pk-keyed, pre-delete pricing); the `buy`/`sell` command entries (~736–738: `do_buy` persists via `bulk_create`; the bulk sell arm routes through `do_sell_bulk`); the money-movement sentence (~746) adds `do_sell_bulk` to the `do_buy`/`do_sell`/`do_repair_attempt` list.

### 4.9 Closeout report

`docs/shyland/Shyland_V25.15_Brief_1_Closeout.txt`, completed in place from the Step 0 stub: final commit hash, deviations, actual vs expected test counts, and the **operator playtest disposition** line (the closeout session reads it as a gate).

## 5. Verification

1. Suite green in-container (path form), 934 + new, no existing test modified.
2. On dev, via the shell: give a character ~1,000 stackable instances of one definition (the `stock-playtest-items` skill or `generate_item_instance(...)` + save via shell — **gift via the shell helper**, never the admin add form); `sell all <noun>` completes in well under a second with the identical aggregate output shape and exact copper credit (spot-check the sum).
3. On dev: `buy 500` of a cheap cart item completes in well under a second; copper, `sold_count`, and instance count all exact.
4. `EXPLAIN`-level sanity is not required; the query-bound tests are the structural proof.

## 6. Operator playtest checklist (dev stack, after 4.7)

1. Stock your test character with a large stackable pile (operator may direct the `stock-playtest-items` skill; per-item minimums as desired).
2. `sell all <noun>` on the big pile — response is effectively instant; one count-form line with the correct total; wallet checks out.
3. `buy 200 healing draught` (or similar cart stock) — instant; wallet and inventory check out.
4. Regression feel-pass: single `sell <item>` (normal line), sell an artifact (generic refusal), `sell all <rarity>` with consumables present (teaching note appears), `buy` with insufficient funds and near carry capacity (unchanged refusals).
5. Anything odd: file thin, normal pipeline.

## 7. PENDING DEPLOY-TIME ACTIONS

**None.** Code-only release: no migration (head stays `0056`), no seed, no data actions. The production deploy at the closeout tail is the standard `make deploy-prod` with nothing riding it. (Note: any container restart bounces all three games — standard closeout-tail fact, dev deploys in-session bounce the dev stack only.)

## 8. Explicitly out of scope

- Any quantity cap (superseded ruling — must not ship).
- `drop` / `pickup` / `use` loop batching (future ticket if ever needed).
- Progress output during long operations (moot — nothing is long anymore).
- GDD changes: none. Batching alters no designed behavior; §6's compensated-disposal rule (the sold instance ceases to exist, vendors never resell) describes outcomes and stands as written.
