Shyland Brief — V22 B4 Travel Deferral Housekeeping
Type: ops/housekeeping (does not count against the brief cap) · Version context: 22 Scope: demote the B4 travel/attunement bucket out of Version 22; update the milestone description; run the issues report. No game code changes of any kind. Branch: run in the current CC session's working branch.
This brief is self-contained. Do not consult chat history.
Pre-flight

1. `gh` authenticated; clean tree.

Step 0 — Self-commit this brief
Save this brief verbatim to `docs/shyland/Shyland_Brief_V22_B4_Travel_Deferral_Housekeeping.md` (skip if identical file exists), commit, and push immediately. Commit and push at every step boundary below. Never merge.
Step 1 — The ruling this brief executes
Design ruling (2026-07-19): the B4 bucket (travel network / attunement) is dropped from Version 22. Travel's real redesign — zone grouping, cross-zone distance, network growth — belongs to a future version dedicated to zones and travel, where new destinations force the questions as requirements rather than speculation. Version 22 retains exactly one travel item, already captured in the B2 spec (docs/shyland/Shyland_V22_B2_Command_Spec_DD.md): the `travel` destination listing sorts ascending by distance (within-zone straight-line map-space) with each entry labeled shard or sphere.
Consequences: Version 22 is four buckets — B1 (shipped), B2, B3, B5 — four implementation briefs, within the cap. The B3 `home` command ships pointing at its default destination (The Convergence); attunement arrives with #38 whenever its version comes. The standing convention "spawn = the Heart until homes ship" survives v22 unchanged.
Step 2 — Issue demotions
For each of #30 and #38:

1. Post a comment via `gh issue comment`, beginning `Design ruling (2026-07-19).` with this text: `Deferred: the B4 travel/attunement bucket is dropped from Version 22. This item belongs to a future version dedicated to zones and travel — revisit at that version's planning, alongside #41 and #95 which carry the same disposition. Version 22 retains only the travel destination-listing order (ascending distance, shard/sphere labels), captured in the B2 spec DD. For v22, home ships pointing at its default destination (The Convergence).`
2. Remove the issue from the `Version 22` milestone (leave it unmilestoned).
3. Leave the `B4` bucket label in place if present — bucket labels are version-agnostic; the missing milestone is the disposition.

Do not touch any other issue.
Step 3 — Milestone description
Update the Version 22 milestone description (`gh api` or `gh milestone` as available) to reflect the final version shape. Set the description to exactly:
`Feature release. Four buckets: B1 Maps V2 (shipped), B2 command revamp (spec: docs/shyland/Shyland_V22_B2_Command_Spec_DD.md), B3 new commands (home, cancel, last, sudo), B5 gear combat wiring. B4 travel/attunement dropped 2026-07-19 — deferred to a future zones-and-travel version; v22 keeps only the travel destination-listing order (in B2).`
If the milestone description already contains operator-authored content, preserve it by appending the text above on a new paragraph instead of replacing, and note this in the closeout.
Closeout
Write `docs/shyland/Shyland_Brief_V22_B4_Travel_Deferral_Housekeeping_Closeout_Report.txt`: comments posted, milestone removals confirmed for #30 and #38, milestone description updated (replaced or appended), final commit hash. Commit and push. Do not remove or prune any documents.
Finally: run the issues report.
