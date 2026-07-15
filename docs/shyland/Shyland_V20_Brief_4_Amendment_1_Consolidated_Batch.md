# Shyland V20 Brief 4 — Amendment 1 (Consolidated Batch): Header Name, Stat Bars, Viewport Fit, Repair Splitting

Combined file-and-fix brief: Part 1 files four issues and captures their numbers; Part 2 implements all fixes and closes them **plus pre-existing #51**, which the viewport fix resolves. Self-contained. **Never remove or prune any transient document** — the operator prunes. Amendments do not count against the brief cap.

This brief **supersedes** the earlier standalone `Shyland_V20_Brief_4_Amendment_1_Stats_Header_Name.md`, which was never run — the operator will discard it.

**HARD GATE:** if anything in Part 1 cannot be completed exactly as prescribed — an issue fails to create, a verification mismatches, a number cannot be captured unambiguously — **STOP: run the issues report, deliver a closeout explaining the deviation, make no code changes.**

---

## Part 1 — File the issues

Milestone name exactly `Version 20`. Capture each number from the URL `gh issue create` prints; verify each with `gh issue view` (open, milestone, label where given, full body). Any mismatch → the hard gate. Also verify `gh issue view 51` shows an OPEN issue titled about right-pane scrollbars — do not modify it in this part.

### 1a. Issue A — stats header name

```
gh issue create --title "Right-pane stats header says SHYLAND instead of the character name" \
  --milestone "Version 20" --assignee KnightOfNight --label bug \
  --body "Found in v20 Brief 4 playtesting. The player-stats section header reads the app label 'SHYLAND' — a placeholder-era carryover — instead of identifying whose stats they are. RULED (2026-07-15): the header shows Character.name VERBATIM — byte-for-byte, no text-transform, no case styling of any kind (Shy-Guy renders Shy-Guy; HiMyNameIsMud renders HiMyNameIsMud). Server-supplied via state sync, never client-derived. Fix: v20 Brief 4 Amendment 1 (consolidated)."
```

### 1b. Issue B — stat bars and the Acuity band gauge

```
gh issue create --title "Player stats render as plain text; make V/L bars and A a band gauge like the fight panel" \
  --milestone "Version 20" --assignee KnightOfNight \
  --body "$(cat <<'EOF'
Found in v20 Brief 4 playtesting: next to the fight panel's health bars, the plain-text V/A/L lines look out of place.

RULED (2026-07-15):
- Vitality: horizontal ratio bar (fill = current/max), fill color #8FCF9F, numerals kept alongside ("226 / 345") in dim text.
- Longevity: same bar treatment, fill #D8B45A, numerals alongside.
- Acuity: NOT a ratio — a BAND GAUGE. Fixed track domain 0.0–2.0 (uniform across Origins for v1); the character's Origin optimal band (acuity_band_low..acuity_band_high) rendered as a shaded region; current acuity as a position tick (#40B58C), clamped to the track; numeral alongside ("1.0"). This is the first UI surface that teaches the band mechanic rather than reporting a number.
- State sync carries whatever the client lacks: character name (issue A), acuity band low/high (server-supplied from the Origin; never client-derived).
- The combat-red section treatment continues to apply to the whole stats section, bars included, unchanged.
EOF
)"
```

### 1c. Issue C — window scrollbar / viewport fit

```
gh issue create --title "Browser window scrollbar present at every size; app should fit the viewport exactly" \
  --milestone "Version 20" --assignee KnightOfNight --label bug \
  --body "Found in v20 Brief 4 playtesting: a window-level scrollbar exists regardless of browser size — the page's height exceeds the viewport by a constant (classic 100vh-plus-unaccounted-margins/borders overflow accounting). RULED (2026-07-15): the app fills the viewport exactly; the PAGE never scrolls; only interior panes scroll themselves (the output pane, and the fight-info region of the right pane). Sibling: pre-existing #51 (right pane horizontal and vertical scrollbars) is the same overflow-accounting disease inside the pane — this fix resolves both, and #51 closes with this issue."
```

### 1d. Issue D — bulk repair message splitting

```
gh issue create --title "Bulk repair joins all lines into one message; split per-repair per the #63 ruling" \
  --milestone "Version 20" --assignee KnightOfNight --label bug \
  --body "$(cat <<'EOF'
Found in v20 Brief 4 playtesting — the #63 disease in a limb the Brief 3 Amendment 1 audit didn't reach (its stated scope was bulk emitters introduced BY Brief 3; bulk repair predates it):

    [14:34:13.83] Battle Axe Mk 1 is restored to full condition. (9 coppers) Leather Vest Mk 1 is restored to full condition. (2 coppers) ... Repaired 6 items, 0 attempts failed, 1 silver, 6 coppers spent.

RULED (already, on #63; applies here): bulk operations narrate as streams of events — each repair line its own message (own ts/seq, commerce category, stamped), the summary its own message. ADDITIONALLY RULED: the fix audits EVERY multi-item emitter in the codebase regardless of vintage for the joined-batch pattern, fixes all found the same way, and lists them in the closeout — ending the whack-a-mole.
EOF
)"
```

## Part 2 — Implementation (only on a perfect Part 1)

**2a (A):** Header renders `Character.name` verbatim from state sync (add the name to the payload if absent). No text-transform anywhere in the header's CSS/JS path. Combat-red treatment untouched.

**2b (B):** Replace the V/A/L text lines with: V and L ratio bars (track in the pane's dark neutral, fills `#8FCF9F` / `#D8B45A`, height matching the fight panel's bars, numerals alongside in dim text, right-aligned); the Acuity band gauge exactly as ruled (track 0.0–2.0, shaded Origin band from server-supplied `acuity_band_low/high`, tick `#40B58C` clamped to track, numeral alongside). All values update from the existing status/state messages; band bounds ride state sync (server-supplied). Layout stays within the fixed 300 px pane; screen-reader consideration: the numerals remain real text (the accessible values); bars/gauge are decorative (`aria-hidden`).

**2c (C, closes #51 too):** Fix the root overflow accounting so the app grid fits the viewport exactly at every window size — no window-level scrollbar, ever. Inside the right pane: the pane as a whole does not scroll; only the fight-info region scrolls (its ruled behavior); no horizontal scrollbar at any pane content state. The output pane keeps its own internal scroll. Verify borders/margins/padding are inside the height math (border-box throughout or equivalent).

**2d (D):** Bulk repair emits one message per repaired item (commerce category, stamped, through the choke point) and a separate summary message; failed attempts likewise per-attempt. Then the broadened audit: find every remaining multi-item emitter of any vintage that joins lines into one message; fix each identically; list all found (and all clean) in the closeout.

## Part 3 — Verification (all must pass before closing or the doc touch)

1. Header shows the exact character name casing for Shy-Guy and for a test character with mixed casing; combat-red still engages/clears with the header inside it.
2. Bars: V bar tracks damage and healing live in combat; L bar full (known — no drain exists yet); numerals match `stats` output exactly.
3. Gauge: band shading spans the character's Origin band; the tick sits at current acuity; create-or-use a non-default-Origin test character (e.g. Voidtouched-band values) to confirm band bounds are server-supplied per Origin, not hardcoded.
4. No window scrollbar at any of: 1000 px baseline, wide desktop, narrow desktop, phone breakpoint. No right-pane horizontal or whole-pane vertical scrollbar in any content state; fight region still scrolls internally when overfull; output pane scroll unchanged.
5. The repair reproduction: repairing a six-item kit yields six separately stamped lines plus a stamped summary, each on its own line; a failed attempt renders as its own line.
6. The emitter audit list is complete: every multi-item output path in the codebase named, each marked fixed-here, fixed-previously, or verified-clean.
7. Envelope and map regressions: `seq` monotonic through a bulk repair; the map renders byte-identically (this amendment must not touch it).

Close **A, B, C, D, and #51** (closing comments referencing this amendment; #51's comment notes it was resolved by C's viewport fix), gated on all checks above.

## Part 4 — Architecture doc touch (LAST, gated)

In `docs/shyland/Shyland_Architecture_v20.md`: the stats-pane description (header = verbatim character name; V/L ratio bars; the Acuity band gauge with its 0.0–2.0 track and server-supplied band bounds; state-sync additions), the viewport-fit layout rule (app fits viewport, page never scrolls, only designated panes scroll), and the bulk-operation messaging note extended with the completed all-vintage emitter audit. No version bump, no file removals.

## Part 5

Run the issues report. Include the final commit hash in the closeout.

## Closeout report

A–D numbers and URLs, Part 1 verifications, the full emitter-audit list, all Part 3 results, commit hashes, and confirmation A, B, C, D, #51 are closed.
