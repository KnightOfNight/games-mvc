# Shyland V24.24 Brief 1 — Readability Pass

- **Release:** Version 24.24 (milestone `Version 24.24`)
- **Branch:** `version_24_24`
- **Founding issue:** #233 (umbrella) — dependencies #221 (contrast), #222 (type scale)
- **Authored:** V24.24 design session, 2026-08-12 (operator-confirmed rulings recorded on #233, #221, #222)
- **Session type to apply this brief:** Implementation

This brief is self-contained. It is the **first (and only planned) implementation brief of Version 24.24** — it performs the version-start rituals.

---

## 1. Context and goal

One problem, one release: **the game's text is hard to read.** Two axes:

- **#222 — size:** the type scale is too small (base 14px, hardcoded px at ~10 sites in the game client).
- **#221 — contrast:** the character-creation screen's `--muted` text computes to **3.47:1** on its #16161a background — below the WCAG AA minimum of 4.5:1 for normal-size text.

The fix is pure client presentation confined to two templates:

- `django/src/apps/shyland/templates/shyland/game.html`
- `django/src/apps/shyland/templates/shyland/character_create.html`

**No server code, no models, no migrations, no seed data, no routing, no shared surface.** No color-doctrine impact: the creation screen's palette is self-contained (independent of the game client's color system), and the game client's colors do not change at all.

## 2. Design rulings — binding, do not deviate

1. **Mechanism:** each template keeps exactly **one px type declaration** — the root (`html, body`). Every other type site converts to **`rem`**, preserving the current size ratios exactly (value = current px ÷ 14, four decimal places). Future size changes are then a one-line root edit.
2. **Starting values:** root **16px** (both templates); creation-screen `--muted` **#85859c** (5.01:1 on #16161a).
3. **Operator tuning loop with bounded authority** (§7): the starting values are deliberately not final — the operator judges them live on dev and directs adjustments in-conversation. **Band: base size 12–24px; `--muted` any value with ≥ 4.5:1 contrast on #16161a that stays visually subordinate to `--text` (#c8c8d4, 10.89:1).** Size adjustments move the root only — never per-site values (ratios are fixed by ruling). Any request outside the band is a **design-level finding**: stop tuning, file it, get it ruled — never apply silently.
4. **Exclusions:**
   - `.map-updown` (`game.html`, `font: bold 14px 'Courier New', Courier, monospace;` — note it is a `font:` **shorthand**, not `font-size:`) stays **byte-identical**. The map's U/D badge offsets are derived from the measured ink of 14px bold Courier (arch doc "tuck rule"); scaling it breaks map geometry. It is px, so it is naturally immune to the root change — leave it alone.
   - The right pane stays **fixed at 300px**; the map SVG (fixed 300×300, all internal geometry) is untouched.
5. **GDD:** no GDD edits this release (ruled — the GDD documents no type sizes and not the creation-screen palette). Architecture doc: stamp-only (§9).
6. **Final tuned values** are recorded in the closeout report and echoed onto #233 at close (§8).

## 3. Pre-flight

- Standing pre-flight line: **no prior PENDING DEPLOY-TIME ACTIONS are outstanding** — Version 24.23's production seed executed at its closeout tail (verified complete, deletions 0=0). This brief itself creates **no** deploy-time data actions.
- Session pre-flight per CLAUDE.md (`python3 scripts/check_docker_host.py`, exit 0, target **local dev**).

## 4. Step 1 — Version constant (opening act)

First implementation brief of the release:

1. Edit `django/src/apps/shyland/version.py`: `SHYLAND_VERSION = "24.23"` → `"24.24-DEV"`.
2. Move the pin test **in the same commit**: `django/src/apps/shyland/tests/test_b2_amendment1.py` — `self.assertEqual(SHYLAND_VERSION, '24.23')` → `'24.24-DEV'`.
3. This is its **own commit** (version bump only), then run the version-start **`make deploy-dev`** from the worktree.

## 5. Step 2 — `game.html` type-scale conversion

All selectors are in the inline `<style>` block. **This table is authoritative** (taken from template ground truth; it supersedes the approximate table in #222's body — the two 15px sites are the location bar and the prompt; the output pane itself inherits the base):

| Selector | Today | Becomes |
|---|---|---|
| `html, body` | `font-size: 14px` | `font-size: 16px` — **the root; stays px; the only tuning knob** |
| `#loc-bar` | `font-size: 15px` | `font-size: 1.0714rem` |
| `#side` | `font-size: 12px` | `font-size: 0.8571rem` |
| `#stats-name` | `font-size: 12px` | `font-size: 0.8571rem` |
| `#bars` | `font-size: 12px` | `font-size: 0.8571rem` |
| `.fight-nums` | `font-size: 11px` | `font-size: 0.7857rem` |
| `#prompt` | `font-size: 15px` | `font-size: 1.0714rem` |
| `#cmd` | `font-size: 14px` | `font-size: 1rem` |
| `#conn-ms` | `font-size: 11px` | `font-size: 0.7857rem` |
| `#send-btn` | `font-size: 12px` | `font-size: 0.8571rem` |
| `.map-updown` | `font: bold 14px 'Courier New', …` | **UNCHANGED — byte-identical (ruling 4)** |

No other declarations in the file change. Do not touch layout dimensions (pane widths, bar heights, badge offsets, border widths).

## 6. Step 3 — `character_create.html` conversion + contrast fix

All in the inline `<style>` block:

| Site | Today | Becomes |
|---|---|---|
| `--muted` (in `:root`) | `#6b6b80` | `#85859c` — **starting value; tuning knob** |
| `html, body` | `font-size: 14px` | `font-size: 16px` — **root; stays px; tuning knob** |
| `h1` | `font-size: 18px` | `font-size: 1.2857rem` |
| `select, input[type="text"]` | `font-size: 14px` | `font-size: 1rem` |
| `button[type="submit"]` | `font-size: 14px` | `font-size: 1rem` |

The `--muted` change is variable-level only — every usage site (subtitle, helper text, back link) inherits. No other palette value changes.

## 7. Verification (before the playtest)

1. **Full test suite in-container** (the only working invocation form):
   `docker exec <django container> python manage.py test apps/shyland/tests`
   Invariant: the same tests pass as at the branch base — **zero new failures** (589 passed at the 24.23 stamp; the count may move only by tests this brief legitimately touches, i.e. the pin test's value).
2. **Template grep assertions** (run from the worktree):
   - Each template contains **exactly one** `font-size:` declaration carrying `px` (the root `html, body`); every other `font-size:` in both files is `rem`.
   - The `.map-updown` line in `game.html` is byte-identical to the branch-base version (`git diff` shows no hunk touching it).
   - `character_create.html` no longer contains `#6b6b80`.
3. **Contrast check of the final `--muted` value** (rerun after every tuning change to it):
   ```
   python3 -c '
   def lum(h):
       h=h.lstrip("#")
       def c(v):
           v=v/255
           return v/12.92 if v<=0.03928 else ((v+0.055)/1.055)**2.4
       r,g,b=(c(int(h[i:i+2],16)) for i in (0,2,4))
       return 0.2126*r+0.7152*g+0.0722*b
   fg,bg="<CANDIDATE>","16161a"
   l1,l2=sorted((lum(fg),lum(bg)),reverse=True)
   print(round((l1+0.05)/(l2+0.05),2))'
   ```
   Must print **≥ 4.5**.
4. **Diff confinement:** the release's code diff touches only the two templates, `version.py`, the pin test, the architecture doc stamp (§9), and `docs/shyland/` documents. Anything else is a deviation — stop and report.
5. **`make deploy-dev`** from the worktree once 1–4 pass.

## 8. Operator playtest — dev stack, with tuning loop

Itemized checklist (operator, on dev, after §7's deploy):

1. **Game client** (`/shyland/play/`): overall readability — output pane text, location bar, prompt and input line.
2. **Right pane at a default desktop window:** stats name, bar labels and numerals, Acuity band gauge labels; in combat, fight-panel rows render uncropped (names, `hp/hp_max` numbers).
3. **Map:** renders exactly as before — node sizes, edges, U/D badges pixel-identical (the map deliberately does not scale).
4. **Kind-3 tables** (`inv`, `stats`, `help`, the travel listing): column wrapping acceptable at a normal window, a narrow (~1024px) window, and phone width.
5. **Location bar truncation:** with a long Zone/Area/Room combination, the Area segment still truncates first and the line stays one line.
6. **Character-creation screen** (`/shyland/create/`): subtitle, helper text, and back link legible (the former `--muted` sites); overall size comfortable; no layout break.
7. **Tuning loop:** the operator directs adjustments in-conversation — root px (both templates move together) and/or `--muted` hex. Per iteration: apply the edit, rerun §7.2/§7.3 checks, `make deploy-dev`, operator re-checks. **Band per ruling 3: base 12–24px; `--muted` ≥ 4.5:1 on #16161a and subordinate to `--text`.** Iterate until the operator approves; log each iteration's values in the closeout report. An out-of-band request stops the loop (design finding — file it).

The playtest disposition line in the closeout report follows standing rules ("Operator reports playtest successful" / "No playtests for this brief" / "Operator deferring playtest"). Note: for this brief the tuning loop is part of the playtest — a "successful" disposition implies the operator approved the final values.

## 9. Close issues + architecture doc (last, gated)

1. **Close #221 and #222, then #233** — gated on §7 verification passing **and** the operator's approval of the tuned values in §8. Comment the final values (root px; `--muted` hex + computed ratio) on **#233** at close.
2. **Architecture doc — last step, gated on all implementation and verification steps above being complete and passing:** `docs/shyland/Shyland_Architecture_v24.md`, update **in place**: header stamp `24.23` → `24.24`. **The hash does not move** (presentation-only change, not architectural). No section content changes — the doc's only client-type reference (the map badge font and its ink-derived offsets) is deliberately unchanged by this brief.

## 10. Closeout report

Complete the Step-0 stub in place (`.txt` in `docs/shyland/`): final tuned values (root px, `--muted` hex + contrast ratio), tuning-iteration log, deviations (expected: none), test results (actual vs branch base), final commit hash, and the operator playtest disposition line.

Standing rules apply: commit and push at every step boundary; branch only, never merge; transient documents left in place; `SHYLAND_VERSION` stays `24.24-DEV` until closeout stamps it.
