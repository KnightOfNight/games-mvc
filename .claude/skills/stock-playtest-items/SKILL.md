---
name: stock-playtest-items
description: Stock a Shyland character's inventory with generated playtest items (weapons, armor, materials) for sell/loot command testing. Use when the operator asks to fill an inventory with sellable test items. Accepts total count, per-item minimums, exclusions, and target character as arguments.
---

# Stock Playtest Items

Fill a Shyland character's inventory with realistically rolled, sellable items
so the operator can playtest vendor/inventory commands. This is a
database-rows-only operation on the live deployment: never touch seed data,
code, or git contents.

## Arguments

Parse from the invocation, with these defaults:

- **Target character** — required; e.g. `Shy-Guy`. Look up case-insensitively.
- **Total count** — default 150.
- **Minimums** — e.g. "at least 10 hides"; honor them, then fill the rest
  with weapons and armor.
- **Exclusions** — always exclude consumables (Healing Draught, Focus Tonic,
  Repair Kit) and zero-`base_value` starter gear unless the operator
  explicitly asks for them. Honor any additional exclusions given.

## Pre-flight (hard gate)

Run the repo's pre-flight check script and gate on its exit code:

```
python3 scripts/check_docker_host.py
```

- **0** — target set and reachable; proceed.
- **1** — `DOCKER_HOST` set but unreachable; hard blocker. Stop and report
  the failure to the operator — do not fall back to a local daemon.
- **2** — `DOCKER_HOST` not set; stop and ask the operator before touching
  anything.

Container names on the deployment are `game-mvc-django`, `game-mvc-redis`,
etc. — `docker compose exec` does not work here (different compose project
name); use `docker exec -i game-mvc-django ...` directly.

## Procedure

1. **Read the live catalog.** Query `ItemDefinition` fresh each run — never
   hardcode a batch, so the skill survives content changes:

   ```
   docker exec -i game-mvc-django python manage.py shell -c "..."
   ```

   List name, `item_type`, and `base_value`; apply the exclusions above.

2. **Design the batch** before writing anything:
   - Groups are keyed by **(definition, rarity, mk_tier)** — minimum **3 per
     group**, so stacking and `sell all` grouping behave predictably.
     Keep mk_tier uniform within a group.
   - Satisfy the operator's minimums first (materials like Animal Hide /
     Insect Carapace are `item_type='material'`, common, Mk 1).
   - Spread the remainder across weapons and armor with varied rarities
     (common through legendary) and Mk tiers 1–3. Sampling every definition
     is not required.
   - Assert the batch sums to the requested total before running.

3. **Create through the real loot path.** Write a script to the scratchpad
   and pipe it via `docker exec -i game-mvc-django python manage.py shell <
   script.py`. For each item call:

   ```python
   from apps.shyland.item_utils import generate_item_instance
   inst = generate_item_instance(definition, mk_tier, rarity, owner=character)
   inst.save()
   ```

   - **`gift=False` (the default) is mandatory** — `gift=True` soulbinds,
     which makes items undroppable and defeats sell testing.
   - Do not construct `ItemInstance` directly; `generate_item_instance` rolls
     stats, damage, and rarity spreads exactly like real drops.
   - Record `inventory.count()` before and after.

4. **Verify.** Aggregate the character's inventory by
   `(definition__name, rarity, mk_tier)` with a `Count`, and check:
   - created count matches the requested total,
   - every *new* group has ≥ 3 (pre-existing inventory may show smaller or
     inflated groups — subtract what was already there before judging),
   - no excluded items were added, and none of the new items are soulbound.

5. **Report.** Summarize the breakdown (materials / weapons / armor, rarity
   spread), state the before→after inventory count, and explicitly call out
   pre-existing inventory (e.g. old Healing Draughts) so the operator does
   not mistake it for created items.
