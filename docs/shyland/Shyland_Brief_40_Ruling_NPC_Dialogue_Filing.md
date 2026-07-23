Shyland Brief: Issue #40 Full-Sweep Ruling + Triaged, and File the Dialogue-less NPC Bug
Type: Ops / housekeeping brief — runs on `main`, no worktree, no code changes of any kind. Issues touched: #40 (comment + add `triaged` label), one NEW issue (create, milestone, labels, assignee, one cross-link comment on it). No other state changes anywhere. No dependency links — relationships are body/comment text only.
Pre-flight

1. Working tree is clean and you are on `main`. If either is false, STOP and report.
2. Confirm labels `bug` and `triaged` both exist. If either is missing, STOP and report.
3. No deployment surface is touched by this brief.

Step 0 — Self-commit
Save this brief's full text verbatim to `docs/shyland/Shyland_Brief_40_Ruling_NPC_Dialogue_Filing.md` (skip if an identical file exists). Commit on `main` and push immediately.
Step 1 — Post the ruling comment on #40
Add the following comment to #40, verbatim:
Design-chat ruling 2026-07-23 — settled by the operator. This comment is the authoritative scope for the fix; the implementation brief will cite it.
Scope: the FULL SWEEP. Every single-line-repeated site in the spike's inventory table (findings comment above) gets a proper variant pool. Explicitly ruled as bug-release scope under the deliberately-gray odd-version line: the duplication is the defect; the pools are simply what fixing it looks like — and this fix unlocks the variant machinery every future NPC interaction will use.
Components:

1. Free-repair pity lines — data-only: variants added to the existing random-pick structure, per NPC, in the NPC's voice.
2. Paid-repair outcome templates — the shared single strings gain variant-selection machinery at the composition site; success and failure each get a pool. Per-repairer voice where the site allows it without new architecture; shared pools where it doesn't.
3. Vendor transactional flavor — built new. Buy and sell acknowledgments get pools. This includes the two pools already mandated by #138's ruling (the zero-value "taking out your trash" snark and the Artifact "couldn't put a price on that" refusal) — one variant system serves all of it.
4. Every other single-line site in the spike's table — including any requiring the `death_message`-style migration the spike flagged; migrations included where a model change is needed.

Authorship: all pool content is Claude-authored flavor (standing creative-content rule — authored freely, discovered in play). Pool mechanics follow the existing random-pick pattern (kibitz-style); no novel selection architecture.
Explicitly out of scope here: the six service NPCs with zero dialogue entries — that is its own bug, filed separately today (cross-referenced in the comment below this one or by number once filed). This issue fixes repetition at sites that have lines; that issue gives lines to NPCs that have none.
Step 2 — Add the `triaged` label to #40
Per the standing definition — spike diagnosis plus scope ruling on-issue. Leave all other labels and state untouched.
Step 3 — File the dialogue-less NPC bug
Create a new issue with the title:
Six service NPCs have zero dialogue entries — they have never greeted anyone
Milestone: `Version 23`. Labels: `bug`, `triaged`. Assignee: the operator (`--assignee "@me"`, standing convention). Body as follows — where the body says [THE SIX], enumerate the six NPCs by name/slug exactly as listed in the #40 spike findings comment (pull them from that comment at runtime; if the spike comment does not contain an unambiguous list of exactly six, STOP and report rather than guessing):
Found by the #40 research spike (2026-07-23, findings comment on #40): the following service NPCs have no keyword dialogue entries at all — a player who talks to them gets nothing. They have never greeted anyone:
[THE SIX]
Diagnosis: the keyword-dialogue system is the game's variant-ready NPC speech mechanism and these NPCs simply have no entries seeded for it. Pure data gap — no code change, no migration.
Ruled fix direction (design-chat ruling 2026-07-23, operator-confirmed): author and seed keyword dialogue entries for all six, in each NPC's voice, covering at minimum a greeting and their service domain. Content is Claude-authored flavor per the standing creative-content rule. Ships in Version 23.
Relationship: sibling of #40 (same spike, same territory) — #40 fixes repetition at sites that have lines; this issue gives lines to NPCs that have none. No dependency link; either can land first.
Capture the new issue's number at runtime for the closeout report.
Closeout

1. Commit a closeout report as `docs/shyland/Shyland_Brief_40_Ruling_NPC_Dialogue_Filing_Closeout.txt` on `main`: confirmation the #40 comment was posted verbatim, the label addition, the new issue number with its milestone/labels/assignee, the six NPC names as enumerated, confirmation of zero other state changes, final commit hash.
2. Push.
3. Run the issues report.
