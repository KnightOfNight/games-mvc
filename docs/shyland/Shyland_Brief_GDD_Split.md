# Shyland Ops Brief — GDD Split
**Type:** ops/housekeeping brief (does not count against any version's brief cap)
**Branch:** main — this brief runs directly on main. No worktree.
**Scope:** documentation and build tooling only. No models, no migrations, no application code, no deployment, no seed changes. DOCKER_HOST pre-flight is not required (nothing deployment-touching).
This is a **combined file-and-fix brief**: it files its own founding issue at runtime (Step 1), captures the number, and proceeds through a HARD GATE.
---
## Context — the rulings this brief executes
Ruled in the design chat, 2026-07-22 (all four confirmed by the operator):
1. **The GDD is split per top-level section.** One file per `##` section of the current GDD, living in `docs/shyland/gdd/`. Section filenames are unversioned. Section numbering and every internal heading are preserved **verbatim** so that all existing §-references (e.g. GDD §5.9, GDD §6.12 — cited throughout the issue tracker and both documents) remain valid without any sweep.
2. **The monolithic GDD becomes a generated build artifact.** A `make gdd` target concatenates the section files in order, prepends a generated-file banner, and writes `docs/shyland/Shyland_GDD_v22.md`. That built file is what mirrors to the design project. **The section files are authoritative; if the monolith and the sections ever disagree, the sections win.** The concatenation is also the standing structural verification.
3. **The architecture doc stays monolithic.** This brief does not touch `Shyland_Architecture_v22.md` in any way. All of its GDD references are by section number and survive the split unchanged.
4. **Executed now, against the closed v22 GDD**, so Version 23 starts life on the new structure.
**Authorization note:** `CLAUDE.md` currently states that the GDD is never edited by Claude Code. This brief explicitly directs the mechanical operations below (a verbatim carve and a deterministic build), and Step 6 amends `CLAUDE.md` to codify that mechanical generation under an explicit brief is not editing. The carve is verbatim and byte-verified; no GDD prose is authored or altered by this brief.
---
## Pre-flight
1. Confirm you are on `main` with a clean working tree and are up to date with `origin/main` (`git status`, `git pull`).
2. Confirm `docs/shyland/Shyland_GDD_v22.md` exists.
3. Save a pristine copy outside the repo before touching anything:
   ```
   cp docs/shyland/Shyland_GDD_v22.md /tmp/gdd_v22_original.md
   ```
4. Sanity-check the structure of the original. Expected (stop and flag in the closeout if these do not hold — do not improvise):
   - `grep -c '^## ' /tmp/gdd_v22_original.md` → exactly **14**
   - `wc -l /tmp/gdd_v22_original.md` → **2240**
   - Line 1 is `# Shyland — Game Design Document`
   - The 14 `## ` headings, in file order: `## Version History`, `## Table of Contents`, `## 1. Vision & Pillars`, `## 2. World Model`, `## 3. Character System`, `## 4. The Three Bars — Vitality, Acuity, Longevity`, `## 5. Combat System`, `## 6. Economy & Items`, `## 7. Social Systems`, `## 8. Quest & Narrative`, `## 9. Player Command Reference`, `## 10. Technical Architecture`, `## 11. Admin & Content Tools`, `## 12. Future Systems`
**PENDING DEPLOY-TIME ACTIONS from prior briefs:** none known to this brief. If your session context says otherwise, report it in the closeout.
---
## Step 0 — Self-commit (first action, always)
Save this brief's full text **verbatim** to `docs/shyland/Shyland_Brief_GDD_Split.md` (skip the write if an identical file already exists). Commit it on `main` and **push immediately** — the push is the work-has-started signal.
**Standing rule for this session:** commit and push at every step boundary below. This is an ops brief on main; commits go to main directly.
---
## Step 1 — File the founding issue
Create the founding issue with `gh issue create`:
- **Title:** `GDD split: per-section source files with a generated monolith`
- **Body:**
  ```
  Process ruling (design chat, 2026-07-22), executed by Shyland_Brief_GDD_Split.md:
  1. The GDD is split into one source file per top-level section under
     docs/shyland/gdd/, section numbering preserved verbatim so all existing
     §-references remain valid.
  2. The monolithic docs/shyland/Shyland_GDD_v22.md becomes a generated build
     artifact (`make gdd`): banner + concatenation of the section files in
     order. Sections are authoritative if the two ever disagree. The built
     monolith remains the file mirrored to the design project.
  3. The architecture doc stays monolithic (unchanged by this work).
  4. Executed immediately against the closed v22 GDD so Version 23 starts on
     the new structure.
  Rationale: the closeout ritual regenerated the entire ~288KB GDD every
  version even though a version touches only a handful of sections. The unit
  of authorship now matches the unit of change.
  ```
- **No milestone. No label.** This is a process change outside the version cadence.
Capture the issue number from the command output.
### HARD GATE
If `gh issue create` fails, or its output is ambiguous, or the issue number cannot be captured with certainty: **STOP.** Make no further changes. Run the issues report, and write a closeout explaining what happened. Zero file changes beyond Step 0.
Only proceed past this gate with a confirmed issue number in hand.
---
## Step 2 — Carve the GDD into section files
Create `docs/shyland/gdd/` and split `/tmp/gdd_v22_original.md` into **15 files**. The carve rule: the file is cut at every line beginning `## `. Chunk 0 is everything **before** the first `## ` line (the title, the version stamp, and the horizontal rule). Each subsequent chunk runs from its `## ` line up to (not including) the next `## ` line; the final chunk runs to end of file. **No bytes are added, removed, or altered — including trailing newlines.** Any mechanically sound method is acceptable (`csplit`, `awk`, Python); the invariant below is what matters.
Target files, in build order:
| # | File | First line of content |
|---|---|---|
| 1 | `docs/shyland/gdd/_00_header.md` | `# Shyland — Game Design Document` |
| 2 | `docs/shyland/gdd/_01_version_history.md` | `## Version History` |
| 3 | `docs/shyland/gdd/_02_table_of_contents.md` | `## Table of Contents` |
| 4 | `docs/shyland/gdd/section_01_vision_and_pillars.md` | `## 1. Vision & Pillars` |
| 5 | `docs/shyland/gdd/section_02_world_model.md` | `## 2. World Model` |
| 6 | `docs/shyland/gdd/section_03_character_system.md` | `## 3. Character System` |
| 7 | `docs/shyland/gdd/section_04_the_three_bars.md` | `## 4. The Three Bars — Vitality, Acuity, Longevity` |
| 8 | `docs/shyland/gdd/section_05_combat_system.md` | `## 5. Combat System` |
| 9 | `docs/shyland/gdd/section_06_economy_and_items.md` | `## 6. Economy & Items` |
| 10 | `docs/shyland/gdd/section_07_social_systems.md` | `## 7. Social Systems` |
| 11 | `docs/shyland/gdd/section_08_quest_and_narrative.md` | `## 8. Quest & Narrative` |
| 12 | `docs/shyland/gdd/section_09_player_command_reference.md` | `## 9. Player Command Reference` |
| 13 | `docs/shyland/gdd/section_10_technical_architecture.md` | `## 10. Technical Architecture` |
| 14 | `docs/shyland/gdd/section_11_admin_and_content_tools.md` | `## 11. Admin & Content Tools` |
| 15 | `docs/shyland/gdd/section_12_future_systems.md` | `## 12. Future Systems` |
**Carve invariant (verify immediately, before proceeding):**
```
cat docs/shyland/gdd/_00_header.md \
    docs/shyland/gdd/_01_version_history.md \
    docs/shyland/gdd/_02_table_of_contents.md \
    docs/shyland/gdd/section_01_vision_and_pillars.md \
    docs/shyland/gdd/section_02_world_model.md \
    docs/shyland/gdd/section_03_character_system.md \
    docs/shyland/gdd/section_04_the_three_bars.md \
    docs/shyland/gdd/section_05_combat_system.md \
    docs/shyland/gdd/section_06_economy_and_items.md \
    docs/shyland/gdd/section_07_social_systems.md \
    docs/shyland/gdd/section_08_quest_and_narrative.md \
    docs/shyland/gdd/section_09_player_command_reference.md \
    docs/shyland/gdd/section_10_technical_architecture.md \
    docs/shyland/gdd/section_11_admin_and_content_tools.md \
    docs/shyland/gdd/section_12_future_systems.md \
  | cmp - /tmp/gdd_v22_original.md
```
`cmp` must exit 0 (byte-identical). If it does not, fix the carve until it does — do not proceed on a failing carve.
---
## Step 3 — Create the index file
Create `docs/shyland/gdd/Shyland_GDD.md` with **exactly** this content (this file is new authored content, not part of the build concatenation):
```markdown
# Shyland — Game Design Document (Index)
**Version 22.0 — Closed** — in lockstep with `Shyland_Architecture_v22.md`.
This directory is the authoritative source of the Shyland GDD, one file per
top-level section. The monolithic `docs/shyland/Shyland_GDD_v22.md` is a
**generated build artifact** produced by `make gdd` (banner + concatenation of
the section files in build order); it exists for single-file grounding and for
mirroring to the design project. **If the monolith and the section files ever
disagree, the section files win.**
Section numbering inside the files is authoritative and stable: every
§-reference in the issue tracker, the architecture document, and past rulings
(e.g. GDD §6.12) resolves against these files unchanged.
The version stamp above is the GDD's version of record. At each closeout the
stamp moves here, in `_00_header.md`, and in the changelog
(`_01_version_history.md`), and the monolith is rebuilt with `make gdd`.
## Build order
| File | Contents |
|---|---|
| `_00_header.md` | Title and version stamp |
| `_01_version_history.md` | Version History (changelog) |
| `_02_table_of_contents.md` | Table of Contents (in-monolith anchors) |
| `section_01_vision_and_pillars.md` | §1 Vision & Pillars |
| `section_02_world_model.md` | §2 World Model |
| `section_03_character_system.md` | §3 Character System |
| `section_04_the_three_bars.md` | §4 The Three Bars — Vitality, Acuity, Longevity |
| `section_05_combat_system.md` | §5 Combat System |
| `section_06_economy_and_items.md` | §6 Economy & Items |
| `section_07_social_systems.md` | §7 Social Systems |
| `section_08_quest_and_narrative.md` | §8 Quest & Narrative |
| `section_09_player_command_reference.md` | §9 Player Command Reference |
| `section_10_technical_architecture.md` | §10 Technical Architecture |
| `section_11_admin_and_content_tools.md` | §11 Admin & Content Tools |
| `section_12_future_systems.md` | §12 Future Systems |
```
---
## Step 4 — Add the `make gdd` build target
Edit the repo `Makefile`. Add a `GDD_MAJOR` variable, a `GDD_SECTIONS` file list, and a `gdd` target. Match the existing Makefile's style (recipe lines are tab-indented; place the variable definitions near other top-of-file variables and the target alongside the other targets; add a line to the `help` target's output if `help` enumerates targets).
Variable definitions:
```make
GDD_MAJOR := 22
GDD_SECTIONS := docs/shyland/gdd/_00_header.md \
                docs/shyland/gdd/_01_version_history.md \
                docs/shyland/gdd/_02_table_of_contents.md \
                docs/shyland/gdd/section_01_vision_and_pillars.md \
                docs/shyland/gdd/section_02_world_model.md \
                docs/shyland/gdd/section_03_character_system.md \
                docs/shyland/gdd/section_04_the_three_bars.md \
                docs/shyland/gdd/section_05_combat_system.md \
                docs/shyland/gdd/section_06_economy_and_items.md \
                docs/shyland/gdd/section_07_social_systems.md \
                docs/shyland/gdd/section_08_quest_and_narrative.md \
                docs/shyland/gdd/section_09_player_command_reference.md \
                docs/shyland/gdd/section_10_technical_architecture.md \
                docs/shyland/gdd/section_11_admin_and_content_tools.md \
                docs/shyland/gdd/section_12_future_systems.md
```
Target:
```make
gdd:
	{ printf '<!-- GENERATED FILE - DO NOT EDIT.\n     Built by `make gdd` from the section files in docs/shyland/gdd/.\n     Edit the section files; the sections are authoritative if this file ever disagrees. -->\n\n'; cat $(GDD_SECTIONS); } > docs/shyland/Shyland_GDD_v$(GDD_MAJOR).md
```
The banner is **exactly 4 lines** (three comment lines, one blank line); the original document's first line therefore becomes line 5 of the built file. The section list is explicit and ordered — never a glob.
---
## Step 5 — Build and verify
1. Run `make gdd`. It must overwrite `docs/shyland/Shyland_GDD_v22.md` in place.
2. **Build invariant:** the built file minus its 4-line banner is byte-identical to the pristine original:
   ```
   tail -n +5 docs/shyland/Shyland_GDD_v22.md | cmp - /tmp/gdd_v22_original.md
   ```
   `cmp` must exit 0.
3. **Banner check:** `head -4 docs/shyland/Shyland_GDD_v22.md` shows exactly the banner (three comment lines then a blank line), and line 5 is `# Shyland — Game Design Document`.
4. **Idempotence:** run `make gdd` a second time; the file must be unchanged (`git status` shows no new modification after the second run, or a saved copy compares identical).
Do not proceed to Step 6 until all four checks pass.
---
## Step 6 — Update CLAUDE.md
Three surgical edits. In each case, locate the quoted current text; if the text found in the file differs materially from what is quoted here, **stop and flag it in the closeout** rather than improvising — do not make the other edits by guesswork.
**Edit 1 — the repo tree diagram.** Current line:
```
│       ├── Shyland_GDD_vN.md    ← full game design document (versioned; use the highest N present)
```
Replace with these two lines (preserve the tree's exact indentation and box-drawing characters):
```
│       ├── Shyland_GDD_vN.md    ← GENERATED game design document build (do not edit; rebuilt by `make gdd`)
│       ├── gdd/                 ← GDD source: index + one file per section (authoritative)
```
**Edit 2 — the game design reference pointer.** Current line:
```
**Game design reference:** the highest-numbered `docs/shyland/Shyland_GDD_vN.md`
```
Replace with:
```
**Game design reference:** `docs/shyland/gdd/` (index `Shyland_GDD.md` plus one file per section — the authoritative source). The highest-numbered `docs/shyland/Shyland_GDD_vN.md` is the generated single-file build of the same content (`make gdd`); the section files win if they ever disagree.
```
**Edit 3 — the never-edit rule.** Current bullet:
```
- **Never edit** anything under `docs/shyland/`. The architecture doc is updated only as the final gated step of a Shyland brief; the GDD is never edited by Claude Code at all.
```
Replace with:
```
- **Never edit** anything under `docs/shyland/`. The architecture doc is updated only as the final gated step of a Shyland brief; the GDD source files under `docs/shyland/gdd/` are never authored or edited by Claude Code — the only permitted GDD operation is running `make gdd` (or another mechanical operation explicitly directed by a brief), which regenerates the monolithic build artifact without changing content.
```
---
## Step 7 — Close out
All of the following, gated on every verification in Steps 2, 5, and 6 having passed:
1. Commit and push any remaining changes on main.
2. Close the founding issue with a comment summarizing what shipped (file list, the two byte-identity checks passing, the Makefile target, the CLAUDE.md edits) — closing is **gated on verification passing**.
3. Write the closeout report to `docs/shyland/Shyland_Brief_GDD_Split_Closeout.txt`, containing:
   - The founding issue number (filed and closed by this brief)
   - The results of the carve invariant, build invariant, banner check, and idempotence check (verbatim command + exit status)
   - Confirmation of the three CLAUDE.md edits, or a stop-and-flag note for any that did not match
   - A **PENDING DEPLOY-TIME ACTIONS** block (expected: `none — documentation and build tooling only`)
   - The **final commit hash** on main
4. Commit and push the closeout report.
5. Run the issues report.
---
## Verification arithmetic (invariants, not absolute counts)
- Exactly **16** new files exist under `docs/shyland/gdd/` (15 build files + 1 index).
- Exactly **one** issue was created by this brief, and exactly that one issue was closed by it.
- `docs/shyland/Shyland_GDD_v22.md` exists at its original path, now carrying the 4-line banner; stripped of the banner it is byte-identical to the pre-brief committed content.
- `Shyland_Architecture_v22.md` is untouched (no diff).
- No files under `django/` changed. No migrations. Working tree clean at the end.
