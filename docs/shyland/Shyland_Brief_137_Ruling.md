Shyland Brief: Issue #137 Ruling Recorded
Type: Ops / housekeeping brief — runs on `main`, no worktree, no code changes of any kind. Issues touched: #137 (comment only). No state changes: no closes, no label changes, no milestone changes, no assignee changes, no dependency links.
Pre-flight

1. Working tree is clean and you are on `main`. If either is false, STOP and report.
2. No deployment surface is touched by this brief.

Step 0 — Self-commit
Save this brief's full text verbatim to `docs/shyland/Shyland_Brief_137_Ruling.md` (skip the write if an identical file already exists). Commit on `main` and push immediately.
Step 1 — Post the ruling comment on #137
Add the following comment to #137, verbatim:
Design-chat ruling 2026-07-23 — all four parts confirmed by the operator. This comment is the authoritative design direction for the fix; the implementation brief will cite it.

1. Vanish on decay. Corpse contents do not outlive the corpse. Decayed loot is gone — no spill-to-ground. (Spill-to-ground remains available as a deliberate future feature; nothing in this fix forecloses it, since a spill would relocate items before corpse deletion.)
2. CASCADE. `ItemInstance.corpse` changes from `on_delete=SET_NULL` to `on_delete=CASCADE` (migration required). This makes the leak structurally impossible from any corpse-deletion path, not just the decay sweep. Rationale: corpse contents are by definition unowned, unequipped, unbound loot — unconditional destruction on corpse delete is always correct.
3. Tighten the location invariant to exactly-one. `ItemInstance.save()` currently rejects only more than one of owner/current_room/corpse being set; zero locations passes silently, which is what let this leak stay invisible. The check becomes exactly one. Implementation caveat (part of the fix, not optional): before tightening, verify that no legitimate transient zero-location state exists in any creation, transfer, loot, or drop flow — if one is found, STOP and report back to the design chat rather than working around it. The one-time purge (part 4) removes all currently-violating rows before the tightened check can encounter them.
4. Purge with post-run verification. One-time cleanup of existing orphans via a management command (pattern: `fix_zero_secondary_stats`). Filter is exact: `owner`, `current_room`, and `corpse` all NULL. The count is re-checked at run time, not assumed to be the 87 observed on 2026-07-22 — the leak is ongoing. The command must verify its own result: after the delete, it re-runs the orphan query and asserts a count of zero, reporting both the deleted count and the post-run count. The database must be provably clean at completion. This is a deploy-time data action: the implementing brief's closeout carries it in a PENDING DEPLOY-TIME ACTIONS block, and it stays an open verification item until its production execution — including the zero-count confirmation — is reported.

Sequencing note for the implementer: purge orphans → CASCADE migration → invariant tightening land together in one brief; the decay-path behavior itself needs no code change beyond the migration (the existing `Corpse.objects.filter(pk=pk).delete()` becomes correct under CASCADE).
Closeout

1. Commit a closeout report as `docs/shyland/Shyland_Brief_137_Ruling_Closeout.txt` on `main`: confirmation the comment was posted verbatim, confirmation of zero state changes, final commit hash.
2. Push.
3. Run the issues report.
