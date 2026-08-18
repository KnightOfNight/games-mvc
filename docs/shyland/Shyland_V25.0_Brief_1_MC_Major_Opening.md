# Shyland V25.0 — Brief 1: MC Major Opening

- **Release:** Version 25.0 (major-opening release, `N.0`) — milestone `Version 25.0`
- **Branch:** `version_25_0`
- **Founding ticket:** #269 — *V25.0 founding ticket: MC (Monitoring and Command) — the major design pass and version opening*
- **Related:** #260 (total-capture GDD harmonization) and #264 (terminology sweep + zones retheme) — milestone siblings; their deliverables landed with the design session's doc pass (commit `5da479f`) and they close with this release. The full 2026-08-17 ruling set is indexed on #269.
- **Written by:** the V25.0 design session, 2026-08-17.

---

## 1. The release and its rulings

**V25 = MC — Monitoring and Command** (operator ruling 2026-08-16: the firehose is renamed MC, and the major ships ahead of new zones so AI actors are unblocked). **V25.0 ships no functional change** — the design pass, the doc pass, and the version bump only; 25.1 (#37, the sink) sees the first real change (operator expectation recorded on #269).

The GDD/doc payload of this release **already landed on this branch** at commit `5da479f`, authored by the design session per the GDD-first law: new GDD §10.11 (the total-capture doctrine, #260), the §10.5/§7.1 re-pointing, the nine-reference firehose→MC sweep, and the zones retheme (#264). **Implementation sessions never edit GDD source** — this brief's payload is deliberately thin: the version-start ritual, a **comment-and-docstring-only** terminology sweep in the game code (five references, enumerated in §2), and the closing bookkeeping. Server behavior is byte-identical before and after.

**No model change, no migration, no seed change, no template/static change.**

## 2. Technical claims — verified per the v36 technical-coherence rule

Every claim below was **confirmed against the code at writing time** (branch `version_25_0` at commit `5da479f`). Line numbers are indicative at that commit, not load-bearing.

1. **Version constant:** `django/src/apps/shyland/version.py` line 8 (`SHYLAND_VERSION = "24.31"`); pin test `django/src/apps/shyland/tests/test_b2_amendment1.py` line 118 (`self.assertEqual(SHYLAND_VERSION, '24.31')`).
2. **Exactly five code-side "firehose" references exist, all in comments or docstrings, none in executable code** (`grep -rni firehose django/src/` returns exactly these):
   - `models.py:284` — the `echo_mode` field comment: "Never affects the firehose or anything server-side beyond the flag itself."
   - `consumers.py:403` — the `send_json` docstring: "This is the designated tap point for the Firehose Logging milestone (#37/#33)."
   - `consumers.py:2965` — the settings-standard block comment: "Fully firehosed: stamped like every other event."
   - `consumers.py:2996` — the `cmd_echo` comment: "the preference is pane-only and never touches the firehose."
   - `envelope.py:14` — the module docstring: "The choke point is the designated tap for the Firehose Logging milestone (#37/#33). No persistence happens here."
3. **Two of the five (consumers.py:403, envelope.py:14) assert the designated-tap claim that the 2026-08-17 capture ruling on #37 reversed** — the delivery choke point is the envelope stamp, *not* the MC capture point; MC taps at creation level. Renaming alone would re-ship a false architectural claim in fresh vocabulary; both get the corrected sentence (§4).
4. **Suite baseline: 687** (V24.31 closeout, unchanged since — confirm the number at run time; it is the regression bar).
5. **Docstrings are runtime objects** (`__doc__`) — editing them changes no behavior; nothing reads these docstrings programmatically.

Self-consistency: this brief was given one end-to-end read before commit; §2's claims, §4's steps, and §8's arch-doc scope agree.

## 3. Step 1 — version start (opening act, standing requirement)

1. In its **own commit**: `SHYLAND_VERSION = "25.0-DEV"` in `django/src/apps/shyland/version.py`, and the pin test in `tests/test_b2_amendment1.py` moved to `'25.0-DEV'` in the same commit.
2. `make deploy-dev` from the worktree (the version-start deploy).

## 4. Step 2 — implementation (comment/docstring sweep only)

All five edits below change comments or docstrings only. **No executable line may change in this brief.** House style per the #264 ruling: first mention in a file spells out "Monitoring and Command (MC)"; later mentions say "MC."

1. **`envelope.py` module docstring** — replace the tap paragraph:
   > The choke point is the designated tap for the Firehose Logging milestone (#37/#33). No persistence happens here.

   with:
   > The choke point is the envelope stamp — not the capture point for Monitoring and Command (MC, #37/#33), which taps at creation level: one record per event; a per-connection delivery tap would record one row per recipient. No persistence happens here.
2. **`consumers.py` `send_json` docstring** — replace the final sentence (§2 claim 2, second bullet) with:
   > This is the envelope stamp — not the MC capture point (#37/#33): MC taps at creation level.
3. **`consumers.py` settings-standard block comment** — "Fully firehosed: stamped like every other event." becomes "Fully captured by MC: stamped like every other event."
4. **`consumers.py` `cmd_echo` comment** — "never touches the firehose" becomes "never touches MC capture."
5. **`models.py` `echo_mode` field comment** — "Never affects the firehose or anything server-side beyond the flag itself." becomes "Never affects MC capture or anything server-side beyond the flag itself."

**Migration step: none.** No model changes — a field comment is not schema. (Stated explicitly per the brief rules.)

## 5. Step 3 — tests

**No new tests.** There is no behavior to pin — the sweep is textual. The existing suite passes **unedited** at exactly the §2 baseline count; if any assertion fails, that is a deviation to stop and report, not a test to edit. The suite count must not change in this release.

## 6. Verification

1. Full suite, in-container, the only working form: `python manage.py test apps/shyland/tests` (via `docker exec` in the django container). All pass; count exactly the §2 baseline.
2. `grep -rni firehose django/src/` — **zero hits**.
3. `grep -rni firehose docs/shyland/gdd/ | grep -v _01_version_history` — **zero hits** (the design session's sweep held; version-history rows are the historical record and keep theirs).
4. `make deploy-dev` from the worktree once 1–3 pass.

## 7. Operator playtest checklist (dev stack)

Ready after this brief's `make deploy-dev`. Nothing player-visible changed, so this is a smoke pass; "No playtests for this brief" is an expected disposition (V24.31 precedent).

1. `help` → ends with `Version: 25.0-DEV`.
2. `say hello` in a populated room → renders exactly as before.
3. `echo off`, type any command → echo suppressed; `echo on` → returns. (Exercises the files the sweep touched.)

## 8. Architecture doc — last, gated

This step is gated on all implementation and verification steps above being complete and passing.

`docs/shyland/Shyland_Architecture_v24.md`, updated **in place**:

- Stamp line → **25.0**; the header's "as of commit" hash **does not move** — a comment-only sweep is not an architectural change, and the doc's own MC retheme was already applied by the design session at `5da479f`. Append the one-line summary in the header's established style (MC major opens; doc pass + comment sweep; no behavior change).
- No other passages change — the design session already rewrote the delivery-choke-point passage per the capture ruling.

*(The arch doc's rename/re-version for the V25 era, like the GDD's `GDD_MAJOR` bump and monolith rename, is **closeout work** under the standing major-opening mechanics — not this brief's.)*

## 9. Issue closes — gated on §6

After verification passes and the closeout report is completed in place: close **#260** and **#264**, each with a comment naming `5da479f` (the doc-pass landing) and this brief's final commit; close **#269** with a comment naming the release. This leaves milestone `Version 25.0` at 3/3 closed for the closeout entry gate.

## 10. Closeout report

`docs/shyland/Shyland_V25.0_Brief_1_Closeout.txt` (stub created and pushed at Step 0 per the standing ritual, completed in place): final commit hash, suite count, verification results including §6.2/§6.3's greps, any deviations, and the **operator playtest disposition** line (#170) — one of "Operator reports playtest successful" / "No playtests for this brief" / "Operator deferring playtest".

**No PENDING DEPLOY-TIME ACTIONS.** No migration, no seed, no data actions — nothing for the closeout tail beyond the ordinary operator-authorized `make deploy-prod` (executor: the closeout session's tail, per standing law). The closeout additionally runs the **major-opening mechanics** (`GDD_MAJOR` → 25, monolith renamed `Shyland_GDD_v25.md`, old monolith `git rm`'d) — standing law, noted here so the tail expects it.
