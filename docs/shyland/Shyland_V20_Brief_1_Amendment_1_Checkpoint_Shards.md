# Shyland V20 Brief 1 — Amendment 1: Checkpoint Shard Wording

Implements GitHub issue **#49** (checkpoint shard wording). Amendment to the applied v20 Brief 1; does not count against the brief cap. Self-contained. **Never remove or prune any transient document** — the operator prunes.

All changes are wording-only data edits in `django/src/apps/shyland/management/commands/seed_world.py`, followed by an enforce-exact reseed. No models, no migrations, no geometry, no mechanics.

## The rule

Checkpoint obelisk lights (Fordwatch, Stairhead, Cragfoot) are Verdant **Shards**. "Sphere" is reserved for the two source-node objects: the **Primordial Sphere** (Heart of the Convergence, white) and the **Verdant Sphere** (the Verdant Crown, green). Display text referring to a checkpoint light as a "sphere" is wrong; references to either source-node sphere are correct and must not change.

## Step 1 — Known replacements (exact)

| Location | From | To |
|---|---|---|
| Stairhead brief description | `A green sphere rides the wind above a trodden waystation.` | `A green shard rides the wind above a trodden waystation.` |
| Stairhead full description | `A small sphere of green light rides the wind here` | `A small shard of green light rides the wind here` |
| Cragfoot brief description | `A green sphere warms itself by a fire at the mountains' feet.` | `A green shard warms itself by a fire at the mountains' feet.` |
| Cragfoot full description | `A small sphere of green light hangs near the flames` | `A small shard of green light hangs near the flames` |
| Checkpoint shard entity description | `A small sphere of soft green light, unattached to anything` | `A small shard of soft green light, unattached to anything` |
| Villager description (Cragfoot-area) | `stayed for the sphere, which he talks to` | `stayed for the shard, which he talks to` |
| Villager description (same cluster) | `sphere "the little lamp"` | `shard "the little lamp"` |

Preserve all surrounding text exactly; only the word changes.

## Step 2 — Survey (required)

Search the entire seed for every occurrence of `sphere` (case-insensitive). Classify each against the rule above:

- **Checkpoint-cluster display text** (room descriptions, NPC descriptions, dialogue *display* lines referring to a checkpoint light): fix to `shard`, matching case. Report any occurrence fixed beyond the Step 1 table.
- **Source-node references** (Primordial Sphere, Verdant Sphere, including summit-referencing dialogue like "a green sphere in an obelisk" and both entity descriptions/slugs): leave untouched.
- **Dialogue listening keywords**: where a checkpoint-related NPC's keyword list contains `sphere`, ADD `shard` and KEEP `sphere` (players will still say it). Source-node NPC keyword lists unchanged.
- Anything ambiguous: stop and flag in the closeout rather than guessing.

## Step 3 — Reseed and verify

1. Enforce-exact reseed; the extended seed verification passes (no geometry was touched, so any failure is a red flag — stop).
2. Grep assertions: none of the Step 1 "From" strings remain; both source-node descriptions and the summit dialogue line remain byte-identical.
3. In-game spot check: `look` at Fordwatch, Stairhead, Cragfoot — all three read "shard" in brief and full; the Heart and the Crown still read "sphere".

Close **#49** with a closing comment referencing this amendment, gated on Step 3.

## Step 4 — Architecture doc touch (LAST, gated on Step 3)

In `docs/shyland/Shyland_Architecture_v20.md`, extend the Brief 1 sentence that mentions "the Fordwatch sphere→shard wording fix (issue #46)" to "...the checkpoint sphere→shard wording fixes (issues #46, #49 — Fordwatch, Stairhead, Cragfoot, and the shard entity)". No version bump, no other doc changes, no file removals.

## Closeout report

The full survey classification (every occurrence and its disposition), grep assertion results, spot-check confirmation, and #49 closed.
