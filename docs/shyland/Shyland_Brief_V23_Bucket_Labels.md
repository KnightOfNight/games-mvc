# Shyland Brief — V23 Bucket Labels

**Type:** Ops / housekeeping brief (issues update only — zero code changes)
**Repo:** `KnightOfNight/games-mvc`
**Working branch:** `main` (ops briefs commit to main immediately)

---

## Purpose

Version 23 planning has assigned all 11 milestoned issues to four implementation buckets. This brief applies one bucket label to each issue so that each bucket's design chat can pull its scope by label. No milestones change, no issues are filed or closed, no comments are added, no code is touched.

## Pre-flight

- Confirm `gh` CLI is authenticated (`gh auth status`).
- Confirm the working tree is clean and the current branch is `main`.

## Step 0 — Self-commit this brief

Save this brief's full text verbatim to `docs/shyland/Shyland_Brief_V23_Bucket_Labels.md` (skip the write if an identical file already exists), commit on `main` with message `V23: bucket-labels housekeeping brief`, and **push immediately**.

## Step 1 — Ensure the four bucket labels exist

The repo has used labels `B1`, `B2`, `B3`, and `B5` in prior versions; `B4` may not exist (v22's B4 bucket was dropped before labeling).

For each of `B1`, `B2`, `B3`, `B4`:

- If the label already exists, leave it exactly as it is (name, color, description untouched).
- If it does not exist, create it: `gh label create B4 --description "Version bucket 4"` (color: gh default is acceptable; do not overwrite existing label colors).

## Step 2 — Apply bucket labels

Apply exactly one bucket label to each issue below. **Add** the label — do not remove or modify any existing labels (`bug`, `triaged`, etc. all stay).

| Label | Issues |
|---|---|
| `B1` | #143, #25 |
| `B2` | #137, #117, #18 |
| `B3` | #133, #119, #141 |
| `B4` | #40, #144, #138 |

Command pattern: `gh issue edit <N> --add-label <bucket>`

## Verification

- Each of the 11 issues (#18, #25, #40, #117, #119, #133, #137, #138, #141, #143, #144) carries **exactly one** of the labels `B1`/`B2`/`B3`/`B4`, matching the table above.
- Every pre-existing label on each issue is still present.
- No other open issue gained or lost a bucket label as a result of this brief.
- All 11 issues remain milestoned to **Version 23**; no milestone changed on any issue.
- No issue was opened, closed, or commented on.

## Closeout

Commit a closeout report as `docs/shyland/Shyland_Brief_V23_Bucket_Labels_Closeout_Report.txt` on `main`, listing the labels applied per issue and whether `B4` was created or pre-existing. Include the final commit hash. Push.

Then: **run the issues report**
