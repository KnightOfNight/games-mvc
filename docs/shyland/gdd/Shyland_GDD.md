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
