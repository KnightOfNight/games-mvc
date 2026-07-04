# Shyland v16 Closeout — Supplemental Notes for the GDD v16 Update

Source: the Claude Code session that implemented v16. These notes cover changes
and findings that occurred during implementation, code review, and a
documentation audit — this chat's history does not contain them. Fold them into
the GDD v16 update alongside the changes already planned here.

Status: v16 is implemented, verified, committed, and pushed. The architecture
doc header hash is `05c634a`. Line numbers below refer to the GDD v15 file.

## A. Implementation refinements that changed designed behavior (record in GDD)

A post-implementation code review changed four behaviors from the brief as
written. All preserve the spirit of the settled decisions but the GDD should
record what actually shipped:

1. **Profanity exemption narrowed.** The designed rule was "profanity filter
   runs solely on overridden names." As shipped: the exemption applies only to
   a kept, *set* gamer tag. When a player has no gamer tag, the default name
   falls back to their username — which has no upstream vetting — so a
   username-derived default IS profanity-checked even when submitted unchanged.
2. **Default name is truncated to 20 characters** (usernames can be up to 150;
   the character name cap is 20), so the pre-filled default always validates.
3. **Name uniqueness is case-insensitive and database-enforced.** A functional
   unique constraint (`Lower(name)`) is the authoritative gate for every write
   path, including Django admin. The live as-you-type check is an advisory
   courtesy; concurrent submissions of the same name are handled gracefully
   (form error, never a server error).
4. **Character name is permanent and independent of the gamer tag.** It is
   initialized from the gamer tag at creation only; changing the gamer tag
   later does NOT rename the character. (This reverses the pre-v16 behavior
   where the displayed name tracked the profile live — worth an explicit note
   in the character system section.)

## B. Stale GDD passages found during a documentation audit (fix in GDD v16)

1. **§3.1 Character Creation (~line 260): remove the Portrait step.** The
   creation list still includes "Portrait (selected from a curated set grouped
   by Origin)." Portraits were explicitly cut (settled decision: "No portraits
   — considered and explicitly cut, not deferred") and v16 shipped without
   them. The GDD apparently never received this cut. Creation is exactly:
   Origin, Archetype, Name.
2. **Tech stack table (~line 1263):** the Auth row still says "character name
   from `user.profile.gamer_tag`." Update to: Django built-in auth with the
   shared gamer-tag profile system; Shyland characters have their own `name`
   field initialized from the gamer tag at creation.
3. **Not-yet-built table (~lines 1482–1483): remove both entries** — "Origin
   and Archetype Descriptions ... seeded blank" (all 14 now have real
   descriptions and attire phrases) and "In-game Character Creation ... not yet
   implemented" (shipped in v16; note its text also mentions portrait
   selection, which no longer exists). Consider adding one replacement entry:
   *"Starting attire flavor text (`Origin.attire_material` +
   `Archetype.attire_silhouette`) is seeded but not yet rendered anywhere
   in-game."*
4. **§9.1 needs no changes** — it was verified line-by-line against the code
   dispatch table during the audit and is accurate. For awareness: GDD §9 is
   now the ONLY maintained command list. The stale duplicate lists in CLAUDE.md
   and the project instructions were deleted and replaced with pointers to
   GDD §9, so keeping §9.1 in sync at closeout is now load-bearing.

## C. Already handled — no GDD action, listed so this chat is current

- **Project instructions were updated to v16 by Claude Code** (committed to the
  repo as `docs/shyland/Shyland_Project_Instructions_v16.md`): the
  character-name settled decision now reflects A1–A4 above; the soulbind
  settled decision was corrected from "on pickup" to "on equip" (matching the
  GDD's own v6 clarification and the code); the dead `architecture.md`
  filename was fixed; the command list was replaced with the GDD §9 pointer.
  Upload this file to the project, replacing v15.3.
- **Architecture doc v16 is final** (header hash `05c634a`) and documents the
  implementation-level details that don't belong in the GDD: the three-step
  name migration, the seed command's create-only balance fields, and the
  WebSocket redirect for character-less connections.
