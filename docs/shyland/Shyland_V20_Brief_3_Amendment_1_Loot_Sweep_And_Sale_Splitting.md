# Shyland V20 Brief 3 — Amendment 1: Loot Sweep + Bulk-Sale Message Splitting (Combined File-and-Fix)

This is a **combined brief**: Part 1 files the GitHub issues and captures their numbers; Part 2 implements the fixes and closes them. Self-contained. **Never remove or prune any transient document** — the operator prunes. Amendments do not count against the brief cap.

**HARD GATE between the parts:** if anything in Part 1 cannot be completed *exactly* as prescribed — an issue fails to create, a verification check mismatches, a number cannot be captured unambiguously — **STOP. Run the issues report, deliver a closeout explaining the deviation, and make no code changes.** Part 2 executes only on a perfect Part 1.

---

## Part 1 — File the issues (capture numbers at runtime)

Milestone name exactly `Version 20`.

### 1a. Issue A — loot sweep

```
gh issue create \
  --title "loot all should sweep every corpse in the room, not one corpse" \
  --milestone "Version 20" \
  --assignee KnightOfNight \
  --body "$(cat <<'EOF'
Found in v20 Brief 3 playtesting. The shipped `loot all` empties ONE corpse — matching the brief as written, but not the intent behind #3. Battle-zone fights leave a pile of corpses; the useful command is a room sweep. Design gap, not implementation error.

RULED SEMANTICS (design chat, 2026-07-15):
- `loot all` — loots EVERY corpse in the room, everything on each. Per-item loot lines as today, ending with a one-line summary: "Looted 3 corpses; 2 carried nothing worth taking." Empty corpses produce no individual noise inside a sweep — counted in the summary only. Coins included as today.
- `loot all <noun>` / `loot <N> <noun>` — quantifiers keep meaning ITEMS (consistent with sell/buy); the candidate pool becomes the union of all corpse contents in the room.
- Bare `loot` — unchanged: the single/first corpse, as today.
- Boundary: the sweep respects existing guaranteed-group-loot ownership rules exactly — a convenience over corpse-by-corpse looting, never a way to take loot that is not the player's.

Fix: v20 Brief 3 Amendment 1 (this combined brief).
EOF
)"
```

Capture the created issue number as **A** (parse it from the URL `gh issue create` prints). Verify: `gh issue view <A>` shows open, milestone `Version 20`, assignee, and the full body. Any mismatch → the hard gate.

### 1b. Issue B — bulk-sale message splitting

```
gh issue create \
  --title "Bulk sell batches all sale lines into one message; split per-sale like loot" \
  --milestone "Version 20" \
  --assignee KnightOfNight \
  --label bug \
  --body "$(cat <<'EOF'
Found in v20 Brief 3 playtesting. `sell 3 cara` emitted one message containing all three sale sentences plus the summary, joined without line breaks and carrying a single timestamp:

    [06:30:33.91] You sell Insect Carapace Mk 1 for 2 coppers. You sell Insect Carapace Mk 1 for 2 coppers. You sell Insect Carapace Mk 1 for 2 coppers. Sold 3 items for 6 coppers.

Contrast loot, which correctly emits per-item messages with distinct ts/seq. One trip through the delivery choke point = one envelope = one stamp and no line breaks.

RULED (design chat, 2026-07-15): bulk operations narrate as streams of events. Each sale line is its own message (own ts/seq, stamped — sales are commerce events); the summary line is its own message (also stamped). Applies to all bulk-sell forms (`sell all <noun>`, `sell N <noun>`, `sell all <rarity>`, `sell all common`-style flushes).

Fix: v20 Brief 3 Amendment 1 (this combined brief).
EOF
)"
```

Capture as **B**; verify identically. Any mismatch → the hard gate.

## Part 2 — Implementation (only on a perfect Part 1)

### 2a. Loot sweep (issue A)

Rework `cmd_loot` per the ruled semantics in A's body, exactly:

- `loot all` iterates every corpse in the room the character may loot (existing ownership rules unchanged and enforced per corpse). Per-item loot lines and coin lines exactly as the single-corpse path emits them today — each its own message. One final summary message: `Looted <N> corpses; <M> carried nothing worth taking.` (omit the second clause when M = 0; `Looted 1 corpse` singular). Emptied corpses trigger their existing immediate-disappear behavior (the #3 prefetch fix must keep working across the sweep).
- Inside a sweep, an empty corpse emits **no** individual "carried nothing" line — the summary counts it. Single-corpse `loot` on an empty corpse keeps its existing line.
- `loot all <noun>` / `loot <N> <noun>`: resolver candidate pool = union of all lootable corpse contents in the room; quantifiers mean items; all-or-nothing count semantics for N as elsewhere.
- Bare `loot`: byte-identical behavior to today.

### 2b. Bulk-sale splitting (issue B)

Every bulk-sell form emits one message per sale (through the standard choke point — each gets its own `ts`/`seq`, commerce category, stamped) and one summary message. The zero-value skip summary in `sell all <rarity>` remains its own message. No change to sale mechanics, prices, or the summary wording.

While in there, audit the other bulk emitters introduced by Brief 3 (`buy N` confirmation output, and the new sweep from 2a) for the same joined-message pattern; fix any found the same way and list them in the closeout.

## Part 3 — Verification (all must pass before closing or the doc touch)

1. Multi-corpse room (kill three NPCs, at least one dropping nothing): `loot all` empties all three — per-item stamped lines, distinct `ts` values, correct summary with the carried-nothing count, corpses disappearing as emptied.
2. `loot all <noun>` takes matching items from multiple corpses in one command; `loot 2 <noun>` all-or-nothing against the union pool.
3. Bare `loot`: unchanged single-corpse behavior, including the empty-corpse line.
4. Ownership boundary asserted in code/tests: the sweep loots only corpses the character could loot individually. (Multiplayer confirmation deferred to the operator's playtest.)
5. The reproduction case: `sell 3 cara` now renders three separately stamped sale lines plus a stamped summary line, each on its own line.
6. `sell all common` at volume: per-sale messages, distinct stamps, one summary, zero-value skip summary intact.
7. Envelope regression: `seq` strictly increasing through a sweep and a bulk sale; no message bypasses the choke point.
8. Resolver regression: the Brief 3 unit suite still passes untouched.

Close **A** and **B** with closing comments referencing this amendment, gated on all checks above.

## Part 4 — Architecture doc touch (LAST, gated)

In `docs/shyland/Shyland_Architecture_v20.md`: update the loot command semantics (room sweep, quantifier-over-union, summary line) and add the bulk-operation messaging rule (streams of per-event messages plus a summary message, never joined batches). No version bump, no file removals.

## Part 5

Run the issues report.

## Closeout report

A and B's numbers and URLs, the Part 1 verification results, the bulk-emitter audit findings from 2b, all Part 3 results, commit hashes, and confirmation both issues are closed.
