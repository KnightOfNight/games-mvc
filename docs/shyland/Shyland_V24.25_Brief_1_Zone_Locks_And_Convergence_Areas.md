# Shyland V24.25 Brief 1 — Zone Locks & Convergence Areas

- **Release:** Version 24.25 (milestone `Version 24.25`)
- **Founding ticket:** #41 (lock battle-zone access until the Convergence is fully explored)
- **Dependency:** #95 (the ring needs an area) — ships in this brief
- **Branch:** `version_24_25`
- **Design source:** GDD §2.12 (Zone Entry Requirements — Locks and Keys), §2.9 (The Everround, Morra's Smithy), §2.11 (travel listing muted rule), §9 (footnote 8, world-declined layer) — all committed on this branch with `(v24.25, pending implementation)` markers. The GDD text is authoritative; this brief operationalizes it.
- **This is the first implementation brief of the release.**

## Design rules that must not be deviated from

1. **Locks are world data; keys are player data.** The lock is a seed-authored zone entry requirement. The key is a permanent per-character zone-completion record — **never revoked**, by any path. Nothing derives from `danger_level`.
2. **Completions are recorded for every zone**, whether or not any lock currently requires them.
3. **Enforcement is transition-generic** (walking and `travel` alike) and applies only to *entering* a locked zone. No character is ever ejected from a zone they are standing in.
4. **The refusal pool is generic and door-agnostic** — one pool for every gate, lines speak about the requirement, never the door. It names the required zone and exactly **one** Area of it still holding unvisited rooms (the Area with the most unseen rooms). **Never counts.**
5. **The unlock announcement is green (reward voice)**, celebrates the completed zone by name, and **never names** the zone(s) it unlocked.
6. **Locked destinations stay in the travel listing** (rows muted) and stay matchable — the attempt draws the refusal.
7. **Grandfathering:** every character existing at deploy time gets the Convergence key unconditionally, plus honestly computed keys for every zone their `RoomVisit` record already completes.
8. **Pooled speech law:** every pool in this brief has ≥3 lines.
9. The Heart stays area-free. The Everround and Morra's Smithy are separate areas.

## Step 1 — Version constant (opening act)

In its own commit, before any other change:

- `django/src/apps/shyland/version.py` line 8: `SHYLAND_VERSION = "24.24"` → `"24.25-DEV"`.
- The pin test moves in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py` (the `assertEqual(SHYLAND_VERSION, '24.24')` assertion → `'24.25-DEV'`).
- Then run the version-start `make deploy-dev` from the worktree.

## Step 2 — Models & migrations

File: `django/src/apps/shyland/models.py`.

**2a. `Zone` gains the lock field:**

```python
entry_requires_zone = models.ForeignKey(
    'self', null=True, blank=True, on_delete=models.SET_NULL,
    related_name='unlocked_by',
    help_text='To enter this zone, a character must have fully explored '
              'the named zone (GDD §2.12). Seed-authored; null = open.')
```

**2b. New model `ZoneCompletion`** (place near `RoomVisit`):

```python
class ZoneCompletion(models.Model):
    """A character's permanent key for a zone (GDD §2.12): minted when their
    RoomVisit records cover every room of the zone. Never deleted — keys are
    permanent; locks are authored."""
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='zone_completions')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('character', 'zone')
```

**2c. Schema migration:** `make makemigrations APP=shyland`, then `make migrate`. Commit the generated file; never hand-edit it.

**2d. Grandfather data migration** (a second migration, generated with `make makemigrations APP=shyland` using `--empty` per the enhanced target's sync, or written via the same target's flow — the file itself is authored, which is permitted for data migrations' `RunPython` bodies):

- For every `Character` existing at migration time:
  - Unconditionally create `ZoneCompletion` for the zone with slug `the-convergence`, if that zone exists (`get_or_create` — idempotent).
  - For every other zone with at least one room: if the character's distinct `RoomVisit` count for that zone equals the zone's room count, create the completion (honest keys — e.g. a genuine Verdant Reach completion gets credited now, ready for any future V25 gate).
- Must no-op gracefully on an empty database (fresh installs: no zones, no characters).
- Reverse migration: no-op (`RunPython.noop`) — keys are never revoked, including by rollback.

## Step 3 — Key minting (completion detection)

File: `django/src/apps/shyland/consumers.py`, `record_room_visit` (≈ line 3820) — the single fog-of-war choke point for every arrival path.

- When `get_or_create` reports `created=True`: count the character's distinct `RoomVisit` rows for `room.zone` and compare to that zone's room count. Equal → `ZoneCompletion.objects.get_or_create(character=..., zone=room.zone)`.
- Return enough signal (e.g. `(first_visit, zone_completed)`) for the arrival path to emit the **unlock announcement** after the room render: one line drawn from `ZONE_COMPLETE_LINES`, **reward category** (green). Every arrival path that records visits delivers it (move, travel, flee, respawn, connect — whatever path minted the key).
- The check runs only on `created=True` — revisits cost nothing.
- The completion `get_or_create` guards double-mint (e.g. the grandfather migration already created it): announce only when the completion row was newly created.

## Step 4 — The gate (enforcement)

File: `django/src/apps/shyland/consumers.py`. One shared helper (sync, `@database_sync_to_async`, `select_related` as needed), called from both sites:

- **Walking:** `cmd_move` (≈ line 581) — after the exit resolves to a destination room, before the move executes: if `destination.zone.entry_requires_zone` is set and no `ZoneCompletion(character, required_zone)` exists → send the refusal (warn category) and stop. No state changes, no cooldowns touched.
- **Travel:** `cmd_travel` (≈ line 656) — same check on the destination node's room before travel executes (before departure messaging).
- The helper also computes the `{area}` slot: among the required zone's rooms the character has **not** visited, group by `area`, exclude `area IS NULL`, pick the Area with the most unvisited rooms (ties: any stable order). If no unvisited room has an Area (edge case), use the no-area fallback lines.
- Intra-zone movement, movement into unlocked zones, and every other command are untouched. `home` is untouched (its destination is the Convergence, which is open).

**The pools** — module-level constants in `consumers.py` (the `home`-lines precedent; the generic-pool ruling says constants until pools go per-gate, at which point a model becomes right):

```python
ZONE_LOCK_REFUSAL_LINES = [
    "{zone} has not finished with you. {area} still keeps corners you haven't seen.",
    "The way senses how much of {zone} you carry, and it is not yet all of it. {area} remembers rooms you never entered.",
    "Not yet. Walk all of {zone} first — {area} is still waiting to be seen.",
]
ZONE_LOCK_REFUSAL_LINES_NO_AREA = [
    "{zone} has not finished with you. There are still places in it you haven't seen.",
    "Not yet. {zone} still holds ground your feet have never touched.",
    "The way holds fast. Walk all of {zone} first.",
]
ZONE_COMPLETE_LINES = [
    "You have walked every path of {zone}. Somewhere, a way that was closed quietly stops being closed.",
    "Every corner of {zone} knows your footsteps now. Something, somewhere, unlatches.",
    "{zone} has shown you all it has — and the world, having watched, opens a little wider.",
]
```

(Random selection per event, standard pool mechanics. `{zone}` is the zone's display name; refusal `{zone}` is the **required** zone, completion `{zone}` the completed one.)

## Step 5 — Travel listing: muted locked rows

File: `django/src/apps/shyland/consumers.py`, the `cmd_travel` listing composition (≈ line 728, the structured per-zone display blocks).

- For each zone block whose zone is locked to this character (lock set, key absent): the destination **table rows** render in the **muted font**, via the listing vocabulary's existing muted rendering (reuse the established muted mechanism — no new color literal anywhere; the chart's set-equality test must stay green).
- The zone **heading** keeps its zone-theme color — the lock mutes the destinations, not the zone's identity.
- Locked destinations remain in the match pool and in tab completion (GDD §9 footnote 8); the attempt is refused by Step 4.

## Step 6 — Seed: areas and the lock

File: `django/src/apps/shyland/management/commands/seed_world.py`.

**6a. Two new Areas in `_seed_areas`** (reconcile pattern, exactly like the four existing):

| Field | The Everround | Morra's Smithy |
|---|---|---|
| slug | `the-everround` | `morras-smithy` |
| name | `The Everround` | `Morra's Smithy` |
| theme_color | `#C9AE7A` | `#C0855C` |
| area_description | authored below | authored below |

The Everround `area_description`:

> The ring street carries the city around the park in one unbroken round, and everyone who lives on it calls it the ring road, though the old maps are firm that its name is The Everround. The paving is worn generous and smooth, patched in a dozen stones from a dozen worlds that no longer match and no longer care. Trees lean over the walk at intervals, planted by nobody, tended by everybody. Between the storefronts and the stalls and the lots still deciding what to become, the sealed gates wait with their weather leaking through — a breath of incense, a wash of neon, a cold that does not belong to the day. Walk far enough in either direction and the street makes its quiet argument: that every way around is also a way back.

Morra's Smithy `area_description`:

> The smithy announces itself before it appears — coal smoke on the air, the bright patient ring of hammer on iron, a warmth that reaches into the street. The building is proper stone and timber, built to outlast its neighbors and succeeding, its doorway wide enough for armored customers and its floor swept the way only a serious workshop's floor is swept. Everything here has a place, every place has a purpose, and the heat of the forge sits under it all like a held opinion.

**6b. Room area assignments:** the 40 `RING_WALK` rooms (`r01`–`r40`) → The Everround; `smithy_ext` and `smithy_int` → Morra's Smithy. The Heart and the non-navigable park rooms stay as they are (the Heart deliberately area-free).

**6c. The lock:** in the Verdant Reach zone reconcile, set `entry_requires_zone` to The Convergence zone. The Convergence's own field stays null.

**6d. Seed verification assertions** (extend the existing verify block):

- Both new Areas exist with the exact slugs and theme colors above.
- Area membership counts in The Convergence — **this table is authoritative**:

| Area | Rooms |
|---|---|
| The Everround | 40 |
| Morra's Smithy | 2 |
| Wisteria Walk | 4 |
| Bamboo Run | 4 |
| Basalt Way | 5 |
| Fern Boards | 4 |
| (area-free) | 1 (the Heart) |
| **Zone total** | **60** |

- The Verdant Reach's `entry_requires_zone` is The Convergence; no other zone carries a lock.

**6e. Expected deletion count: 0.** Every seed change here is reconcile-in-place or additive. The closeout reports actual against expected.

## Step 7 — Tests

Additions (new test file(s) under `django/src/apps/shyland/tests/`; invocation, the only working form: `python manage.py test apps/shyland/tests` via `docker exec` in the django container):

1. **Model:** `ZoneCompletion` uniqueness; `Zone.entry_requires_zone` present, nullable.
2. **Minting:** a character visiting the last unseen room of a zone gets exactly one `ZoneCompletion` and one reward-category line from `ZONE_COMPLETE_LINES` (pool-membership assertion); re-arrival mints nothing and announces nothing; a completion pre-created (grandfather path) suppresses the announcement.
3. **Gate, walking:** keyless character moving into a locked zone is refused — warn category, line in the refusal pools (membership assertion), `{area}` slot filled with the required zone's most-unvisited-rooms Area, character's room unchanged. With the key: the move proceeds.
4. **Gate, travel:** same pair through `cmd_travel`.
5. **No-area fallback:** when no unvisited room of the required zone has an Area, the fallback pool speaks.
6. **Travel listing:** a locked zone's destination rows carry the muted rendering; its heading keeps the zone color; an unlocked zone's rows are unchanged. Locked destinations still tab-complete.
7. **Seed:** run twice (idempotence), then assert every count in the 6d table, both theme colors, and the lock authoring.
8. **Color chart:** the set-equality chart test stays green (no new color literal may be introduced).
9. Full suite green.

## Step 8 — Verification (all must pass before issue closure)

1. Full in-container suite green (path form above).
2. `make seed` against the dev stack; seed output shows both new areas; deletion count actual = 0 (expected 0).
3. Dev shell checks: the 6d table's counts via ORM; `Zone.objects.get(slug='the-verdant-reach').entry_requires_zone.slug == 'the-convergence'`; after migration, every pre-existing character has the Convergence `ZoneCompletion`.
4. **Contrast:** compute the WCAG contrast ratios of `#C9AE7A` and `#C0855C` against the client output-pane background color; both must be ≥ 4.5:1 (the 24.24 precedent). Report the computed ratios in the closeout.
5. `make deploy-dev` from the worktree (build + migrate), then `make seed` on dev — **code first, data second**.

## Step 9 — Operator playtest checklist (dev stack)

After Step 8's deploy-dev + seed:

- [ ] New character: at the Heart, `travel` — Verdant destinations listed but **muted**; zone heading still green.
- [ ] `travel fordwatch` — refused in the warn voice; the line names The Convergence and one area still unseen; you don't move.
- [ ] Walk to the Green Gate (r02) and go north — same refusal family; still in the Convergence.
- [ ] Location bar on the ring reads `The Convergence: The Everround: <room>`; at the smithy, `The Convergence: Morra's Smithy: <room>`; at the Heart, no Area segment.
- [ ] First entry to a ring room shows The Everround's ambient paragraph above the room prose (and the smithy's at the smithy), in the area color.
- [ ] Explore every Convergence room; on the final room, the green completion line fires (and never names the Verdant Reach).
- [ ] Green Gate now opens; `travel` rows for the Reach render normally; `travel fordwatch` works.
- [ ] Existing (grandfathered) character: everything behaves exactly as before — gate open, travel normal, no completion announcement replay.
- [ ] Screen reader spot-check: the refusal and completion lines read out via the output pane's live region like any other warn/reward line.

## Step 10 — Architecture doc (last, gated)

This step is gated on all implementation and verification steps above being complete and passing. Update `docs/shyland/Shyland_Architecture_v24.md` **in place**: stamp → 24.25, and the header hash **moves** (this release is architectural — new model, new gate machinery). Sections to update: the data model section (Zone lock field, `ZoneCompletion`), the consumer/command-flow section (gate check in move/travel, minting in `record_room_visit`, the three pools), and the seed section (two areas, the lock, verification counts).

## Standing requirements & closeout

- Commit and push at **every step boundary** — branch only, never merge to main.
- **PENDING DEPLOY-TIME ACTIONS** (open until the closeout tail's deploy window):
  1. Production seed via `make seed-prod` (areas + lock authoring reach production only via seed; expected deletions 0). The grandfather migration itself rides `make deploy-prod`'s migrate — code first, data second.
- Closeout report as `.txt` in `docs/shyland/`: final commit hash, operator playtest disposition (verbatim-style per #170), actual-vs-expected deletion count, computed contrast ratios, any deviations. The Step-0 stub is completed in place.
- Issues #41 and #95 close gated on Step 8 passing.
- No transient-document pruning; the operator prunes.
- End with the `implementation-session-end` ritual (playtest disposition first, issues report last).
