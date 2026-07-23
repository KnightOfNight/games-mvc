# Shyland Brief: Issues #18 + #119 Rulings Recorded + Triaged

**Type:** Ops / housekeeping brief — runs on `main`, no worktree, no code changes of any kind.
**Issues touched:** #18 (comment + add `triaged` label), #119 (comment + add `triaged` label). No other state changes: no closes, no milestone changes, no assignee changes, no dependency links, no other labels modified.

---

## Pre-flight

1. Working tree is clean and you are on `main`. If either is false, STOP and report.
2. Confirm the label `triaged` exists. If not, STOP and report.
3. No deployment surface is touched by this brief.

## Step 0 — Self-commit

Save this brief's full text verbatim to `docs/shyland/Shyland_Brief_18_119_Rulings.md` (skip the write if an identical file already exists). Commit on `main` and **push immediately**.

## Step 1 — Post the ruling comment on #18

Add the following comment to #18, verbatim:

---

**Design-chat ruling 2026-07-23 — diagnosed and settled by the operator. This comment is the authoritative design direction for the fix; the implementation brief will cite it.**

**Diagnosis:** inventory stacking exists and works — the grouping condition in `cmd_inventory` (`consumers.py:953` area) applies only to `item_type == 'consumable'`: adjacent same-definition/mk/rarity instances collapse into one row with a Quantity count. Materials (`item_type='material'` — Animal Hide, Insect Carapace) fall through to one-row-per-instance. That is the entire bug. Command grammar, sell, and use are already stacking-agnostic per the ruled #22 resolution (recorded on this issue 2026-07-13), so this is purely an inventory-display change.

**The general stackability ruling** (answering the body's "look at all stackable-or-not issues" across the full `ITEM_TYPE_CHOICES` vocabulary):

| Stacks | Never stacks |
|---|---|
| consumable (already does) | weapon |
| material (the fix) | armor |
| readable | accessory |
| key | bag |

The rule behind the table: **wear-free interchangeable types stack; per-instance-identity types (durability, rolled stats) never stack.**

**Grouping-key refinement (part of the fix):** the stacking key extends from (definition, mk_tier, rarity) to **(definition, mk_tier, rarity, soulbound state)** — a one-tuple change preventing a bound copy (e.g. super-user gifted) merging with unbound copies. This closes a small pre-existing hole in the consumable stacking as well.

**Scope:** `cmd_inventory` display only. No grammar changes, no model changes, no migration.

---

## Step 2 — Add the `triaged` label to #18

## Step 3 — Post the ruling comment on #119

Add the following comment to #119, verbatim:

---

**Design-chat ruling 2026-07-23 — diagnosed and settled by the operator. This comment is the authoritative design direction for the fix; the implementation brief will cite it.**

**Diagnosis:** the red border is `game.html:210` — `#side-stats.in-combat { background: var(--combat-bg); border-bottom-color: var(--combat-accent); }`. The `border-bottom-color` declaration is a collision of two rulings: v20 brief 4 (#2) turned "the whole stats subsection" combat-red *including its border*, then v21 brief 1 (#85) established pane borders as zone-theme territory (`--zone-border`) — and the v20 border override survived the transition unnoticed.

**The fix:** delete the `border-bottom-color: var(--combat-accent)` declaration from the `#side-stats.in-combat` rule. The combat background (`--combat-bg`) and the name color (`--error`) stay — the stats section still visibly enters its combat state; only the border stops participating.

**Doctrine (promoted from this issue's filing):** *pane borders belong to zone/area theming exclusively; combat state — and any other transient state — expresses through backgrounds and text, never through borders.* Recorded for the GDD/architecture doc at version closeout alongside the fix.

**Scope note:** the parked "pane-not-reddening" observation from the v22 closeout reports stays parked — this fix is the border only. If other panes should ever *gain* combat states, that is a fresh thin filing, not scope here.

---

## Step 4 — Add the `triaged` label to #119

Both label additions per the standing definition: complete diagnosis plus ruling on-issue. Leave `bug` and all other state untouched on both issues.

## Closeout

1. Commit a closeout report as `docs/shyland/Shyland_Brief_18_119_Rulings_Closeout.txt` on `main`: confirmation both comments were posted verbatim, confirmation of both label additions, confirmation of zero other state changes, final commit hash.
2. Push.
3. **Run the issues report.**
