Shyland Brief: Issue #25 Ruling Recorded + Triaged
Type: Ops / housekeeping brief — runs on `main`, no worktree, no code changes of any kind. Issues touched: #25 (comment + add `triaged` label). No other state changes: no closes, no milestone changes, no assignee changes, no dependency links, no other labels modified.
Pre-flight

1. Working tree is clean and you are on `main`. If either is false, STOP and report.
2. Confirm the label `triaged` exists. If not, STOP and report.
3. No deployment surface is touched by this brief.

Step 0 — Self-commit
Save this brief's full text verbatim to `docs/shyland/Shyland_Brief_25_Ruling.md` (skip the write if an identical file already exists). Commit on `main` and push immediately.
Step 1 — Post the ruling comment on #25
Add the following comment to #25, verbatim:
Design-chat ruling 2026-07-23 — settled in full by the operator. This comment is the authoritative design direction for the fix; the implementation brief will cite it.
The rule: when a combat session ends without an NPC dying, and that NPC is participating in no other player's active combat session, the NPC resets to full vitality with its active effect instances cleared (bleeds, poisons, and any other lingering effects on it). This applies to all NPCs uniformly — no boss/elite/normal distinction.
Component rulings:

1. Full reset, not regeneration. Keep it simple: no out-of-combat NPC regen system, no partial-recovery curve. The fight either kills the NPC or never happened, health-wise.
2. All NPCs, not just bosses. One rule, no tier check. Chip-and-run against an elite is the same exploit with a smaller trophy; uniformity also means no player-facing surprise about which enemies "remember" damage.
3. The trigger is session-end-without-death — this covers every disengagement path uniformly: successful flee, player death, and any future path that ends a session, with no per-path logic.
4. The multiplayer guard: reset fires only when the NPC exits its last active combat session. If another player is still fighting it (shared NPC instance across sessions), its vitality is live state and must not snap to full. The implementation must check remaining session membership before resetting.
5. Effects cleared with the reset. A full-health NPC still ticking down from a parting bleed is a half-reset that reopens the exploit in slow motion and renders as a bug in the fight pane on re-engagement.

Context — the coupling that gates this fix: the empirical record here is from the v19 Silk Matron playtest, when flee worked. The chip-and-run exploit is currently unreachable because the flee contest is arithmetically broken (see the flee-contest bug filed 2026-07-23, Version 23); fixing flee re-arms this exploit, so the two fixes ship in the same version. If the implementation brief bundles them, flee comes first so this fix's disengagement path is testable.
Step 2 — Add the `triaged` label to #25
Per the standing definition (an issue is triaged when a brand-new design chat can pick it up cold), #25 now qualifies: complete ruling on-issue. Add `triaged`; leave `bug` and all other state untouched.
Closeout

1. Commit a closeout report as `docs/shyland/Shyland_Brief_25_Ruling_Closeout.txt` on `main`: confirmation the comment was posted verbatim, confirmation of the label addition, confirmation of zero other state changes, final commit hash.
2. Push.
3. Run the issues report.
