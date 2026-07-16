# Shyland V20 Brief 5 — Amendment 1 (Consolidated Batch): Room Header Removal, Zone Separator, Indefinite Articles, Identification Filing

Combined file-and-fix brief: Part 1 files four issues and captures their numbers; Part 2 implements and closes the first three. **Issue D is file-only — no code changes for it in this brief.** Self-contained. **Never remove or prune any transient document** — the operator prunes. Amendments do not count against the brief cap.

**HARD GATE:** if anything in Part 1 cannot be completed exactly as prescribed — an issue fails to create, a verification mismatches, a number cannot be captured unambiguously — **STOP: run the issues report, deliver a closeout explaining the deviation, make no code changes.**

---

## Part 1 — File the issues

Issues A–C: milestone exactly `Version 20`. Issue D: **NO milestone.** Capture each number from the printed URL; verify each with `gh issue view`. Any mismatch → the hard gate.

### 1a. Issue A — bracket room header

```
gh issue create --title "Remove the bracketed room header from the output pane" \
  --milestone "Version 20" --assignee KnightOfNight \
  --body "Found in v20 Brief 5 playtesting. Each room render opens with '[ Area Name — Room Name ]', duplicating the location bar. The transcript argument for keeping it is invalid: the output pane clears on every room entry (ruled to stay that way, 2026-07-15). RULED: the bracket header is removed from the room render entirely (entry and look); the render begins with the description prose; place identity lives in the location bar alone. Fix: v20 Brief 5 Amendment 1."
```

### 1b. Issue B — zone-colored separator

```
gh issue create --title "Add a zone-colored separator between the room block and event lines" \
  --milestone "Version 20" --assignee KnightOfNight \
  --body "$(cat <<'EOF'
Found in v20 Brief 5 playtesting: with the bracket header gone (companion issue), nothing frames the room block against the events below it.

RULED (2026-07-15, samples reviewed): a horizontal rule after the entire room render (below the last occupant/item line, before anything that happens) — a SOLID bar, 5px tall, rounded ends, fill = the current Zone.theme_color at ~0.75 opacity, with vertical padding so the whole divider occupies at least one text line's height. Green rules in the Verdant Reach, violet in the Convergence, every future zone brings its own. Renders once per room render (the pane clears per room, so it always frames the top block). Part of the room-rendering category: unstamped, and aria-hidden (decorative — it conveys nothing absent from the text structure). CSS taste iteration may follow later; this spec ships now.
EOF
)"
```

### 1c. Issue C — indefinite-article introductions

```
gh issue create --title "NPC grammar: indefinite article on first presentation; occupant lines capitalized" \
  --milestone "Version 20" --assignee KnightOfNight --label bug \
  --body "$(cat <<'EOF'
Found in v20 Brief 5 playtesting: occupant lines read "the black bear is here." — wrong article and lowercase. #24's system has only a definite article; English wants indefinite on first presentation, definite thereafter.

RULED (2026-07-15):
- NpcDefinition gains indefinite_article (CharField, max_length 8, default 'a'; 'an' where vowels demand; BLANK for proper nouns so Morra never becomes 'a Morra'). Migration.
- The display helper gains an INTRODUCTION context, used by exactly two template families: room occupant lines ("A black bear is here.") and aggro-engagement lines ("A giant cave spider snarls and moves to attack!"). Definite article everywhere else, unchanged.
- Occupant lines are sentence-capitalized. plural_phrase names use the phrase verbatim, capitalized at sentence start ("One of the Matron's brood is here.").
- Data pass across all seeded NPCs setting indefinite_article appropriately; two identical NPCs correctly read "A black bear is here." twice (ordinal distinction is #64, v21).
- The #24 acceptance strings for definite contexts remain byte-identical.
EOF
)"
```

### 1d. Issue D — identification visibility design (FILE ONLY, no milestone, no code)

```
gh issue create --title "Design: item identification visibility — knowledge by holding" \
  --assignee KnightOfNight \
  --body "$(cat <<'EOF'
Found in v20 Brief 5 playtesting: dropping an item flips is_identified False (deliberate v18 behavior, per the model help text) but the identification system it fed was never built — a one-way trapdoor: any dropped item is mystery-named forever, for everyone, including its original owner on re-pickup. The database record is fully intact; the boolean is purely a presentation gate.

RULED DESIGN DIRECTION (2026-07-15, for a future version — deliberately unmilestoned):
- Knowledge is a property of HOLDING; single boolean, no per-character tracking.
- A ground item shows its mystery name in the room listing and to all observers.
- `examine` is close inspection: it reveals the item's REAL details without requiring pickup.
- Picking the item up flips is_identified True — permanent unlock of normal display.
- Drop continues to re-veil (flips False) — the item becomes a stranger the moment it leaves hands.
- The future identification SERVICE (NPC/skill, per the GDD) then concerns curses and deeper properties, not basic nature. is_unidentifiable interplay preserved.
- Ride-along cleanup for that fix: examine's unidentified branch currently prints two redundant cannot-determine lines; also durability displays truthfully on unidentified items (arguably leaks real data through the veil) — resolve both in the same design pass.

No code changes in v20; filed for a future version's triage.
EOF
)"
```

## Part 2 — Implementation (only on a perfect Part 1; issues A–C only)

**2a (A):** Remove the `[ Area — Room ]` header line from the room render, on entry and on `look`. The render begins with the description prose. The GDD's room-header format is superseded for the output pane (the design-doc capture happens at version closeout, not here). Location bar untouched.

**2b (B):** Implement the separator exactly per B's ruled spec: rendered by the client as part of the room-rendering block, a solid 5px bar, rounded ends, `Zone.theme_color` fill at ~0.75 opacity (the zone color already rides the location payload — reuse it; never hardcode), vertical padding totaling at least one text line's height, once per room render, after the final room-block line. Unstamped (room-rendering category), `aria-hidden="true"`.

**2c (C):** The `indefinite_article` field + migration; the display helper's introduction context; occupant and aggro-engagement templates switch to it with sentence capitalization; the data pass over all seeded NPCs (proper nouns blank; 'an' where needed — e.g. any name starting with a vowel sound); enforce-exact reseed. Extend the seed verification: every NpcDefinition has a non-null indefinite_article field value (blank allowed), and the existing no-leading-article name law still passes.

## Part 3 — Verification (all must pass before closing or the doc touch)

1. Entering a room and `look`: no bracket header anywhere; prose first; the separator renders after the room block, correct thickness and padding, **green in the Verdant Reach and violet in the Convergence** (verify both zones), unstamped, invisible to the screen reader.
2. Two black bears: "A black bear is here." twice, capitalized. A proper-noun NPC: "Morra is here." — no article. A brood minion room: "One of the Matron's brood is here."
3. Aggro entry: "A giant cave spider snarls and moves to attack!" (indefinite). Mid-combat lines unchanged: "The giant cave spider misses you." The #24 acceptance strings for definite contexts render byte-identical.
4. Issue D exists, unmilestoned, full body — and **zero code changed** for it (drop still re-veils; this is verified as UNCHANGED behavior).
5. Regressions: look sections and empty-section omission intact; command echo intact; decay suppression intact; the separator does not appear anywhere except after room renders; envelope `seq` monotonic; the map untouched.

Close **A, B, C** with closing comments referencing this amendment. **D stays open.** Gated on all checks above.

## Part 4 — Architecture doc touch (LAST, gated)

In `docs/shyland/Shyland_Architecture_v20.md`: the room-render structure (no header; prose-first; the zone-colored separator spec), the `indefinite_article` field and the display helper's introduction context (plus the extended seed check), and a one-line note that identification visibility is filed as future design (issue D). No version bump, no file removals.

## Part 5

Run the issues report. Include the final commit hash in the closeout.

## Closeout report

A–D numbers and URLs, Part 1 verifications, the NPC data-pass count, all Part 3 results, commit hashes, and confirmation A/B/C closed and D open-unmilestoned.
