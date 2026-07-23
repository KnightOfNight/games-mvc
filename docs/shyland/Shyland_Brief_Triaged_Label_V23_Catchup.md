Shyland Brief: Apply `triaged` Label — V23 Catch-Up Pass
Type: Ops / housekeeping brief — runs on `main`, no worktree, no code changes of any kind. Issues touched: #117, #137, #138, #141 — label addition only. No other state changes: no closes, no milestone changes, no assignee changes, no comments, no dependency links.
Context
The operator has created a `triaged` label. Definition (standing, ruled 2026-07-23): an issue is triaged only when it contains enough information for a brand-new design chat to pick it up cold — complete diagnosis plus ruling (or unambiguous fix) on the issue itself. Symptoms-only filings and issues with pending rulings do not qualify.
This brief is the one-time catch-up pass over the Version 23 milestone. Going forward, ruling-recording housekeeping briefs add the label in the same motion, so this pass should not need repeating.
Pre-flight

1. Working tree is clean and you are on `main`. If either is false, STOP and report.
2. Confirm the label `triaged` exists in the repo. If it does not, STOP and report — do not create it.
3. No deployment surface is touched by this brief.

Step 0 — Self-commit
Save this brief's full text verbatim to `docs/shyland/Shyland_Brief_Triaged_Label_V23_Catchup.md` (skip the write if an identical file already exists). Commit on `main` and push immediately.
Step 1 — Add the `triaged` label to exactly these four issues

* #117 — stub tests.py shadows tests/ package (filing carries complete diagnosis + unambiguous fix)
* #137 — corpse decay orphans (four-part design ruling recorded 2026-07-23)
* #138 — bound zero-value disposal (full Option 1 ruling recorded 2026-07-23)
* #141 — text cleanup (fat triage + wording ruling recorded; no open questions)

Add the label only. Do not remove or modify any existing labels (e.g. `bug` stays where present). Do not label any other issue — in particular, #18, #119, #25, #40, and #133 remain unlabeled by this brief per the operator's applied definition.
Closeout

1. Commit a closeout report as `docs/shyland/Shyland_Brief_Triaged_Label_V23_Catchup_Closeout.txt` on `main`: per-issue confirmation of the label addition, confirmation that no other issue was touched and no other state changed, final commit hash.
2. Push.
3. Run the issues report.
