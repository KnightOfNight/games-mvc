Shyland Brief: Issue #138 Ruling Recorded
Type: Ops / housekeeping brief — runs on `main`, no worktree, no code changes of any kind. Issues touched: #138 (comment only). No state changes: no closes, no label changes, no milestone changes, no assignee changes, no dependency links.
Pre-flight

1. Working tree is clean and you are on `main`. If either is false, STOP and report.
2. No deployment surface is touched by this brief.

Step 0 — Self-commit
Save this brief's full text verbatim to `docs/shyland/Shyland_Brief_138_Ruling.md` (skip the write if an identical file already exists). Commit on `main` and push immediately.
Step 1 — Post the ruling comment on #138
Add the following comment to #138, verbatim:
Design-chat ruling 2026-07-23 — settled in full by the operator. This comment is the authoritative design direction for the fix; the implementation brief will cite it. Option 1 from the issue body, refined:

1. Vendors accept worthless items — uniformly. The `base_value=0` sell refusal ("That's not worth anything to me.") is removed. Vendors accept zero-value items, bound or unbound, for 0 copper; the instance is deleted per normal compensated disposal. The exploit-proofing holds by arithmetic: selling for 0 pays nothing. The binding system is untouched — no soulbind changes, no migration, no data fix (existing stuck kit pieces become disposable the moment this ships).
2. Exception: vendors never buy Artifact-rarity items, at any value. Artifact is the top rarity tier (one-of-a-kind, hand-authored); this refusal protects every artifact from disposal-by-accident — including the previously-existing hazard of a valued artifact being compensated-disposed for ⅓ price and deleted forever. Ruled intentional consequence: a bound artifact has no disposal path at all. A one-of-a-kind gift is yours, forever. If a buggy artifact ever needs removing, that is an admin action, not a game mechanic.
3. Voice and flavor:
   * Zero-value acceptance is a success — normal voice. The vendor's snarky remark replaces the payment sentence on transactions that net 0 ("taking out your trash" flavor); it draws from a proper variant pool, not a single line — per the #40 spike findings, the sell path currently has no NPC flavor at all, so this is the first vendor line site born variant-ready rather than joining the one-line-forever club.
   * On mixed bulk sells (paying items + worthless riders in one `sell all`): the normal payment sentence covers the paid total, and the snark appends as a trailing remark ("...oh, and I'll take that crap too" energy). Sanctioned fallback if the v22 aggregation plumbing makes the trailing form disproportionate: snark on all-worthless transactions only, mixed transactions silent about the riders — the implementing brief reports which form shipped.
   * The Artifact refusal is world-declined — warn voice (three-layer doctrine). Flavor direction: the refusal is about pricelessness, not worthlessness ("I couldn't put a price on that" energy). Variant pool here too.
4. Doctrine amendment (GDD §6.12 at version closeout): compensated disposal — "soulbound CAN be sold" — gains its one exception: except Artifact rarity, which no vendor will buy. Zero-value acceptance is recorded alongside: worthless items are accepted for nothing; the refusal that closed #138's trap is gone.

Not adopted, recorded for the archive: option 4 (exempting `base_value=0` from soulbind) was examined and rejected as the more intrusive change — it touched the binding system, required a data fix with deploy-time verification, opened a gift-path edge, and created a ground-litter problem (no ground-item decay sweep exists). Option 1 dissolves all four concerns. A seed-enforced `base_value ≥ 1` invariant for artifacts was likewise superseded by the vendor refusal, which protects artifacts at any authored value.
Closeout

1. Commit a closeout report as `docs/shyland/Shyland_Brief_138_Ruling_Closeout.txt` on `main`: confirmation the comment was posted verbatim, confirmation of zero state changes, final commit hash.
2. Push.
3. Run the issues report.
