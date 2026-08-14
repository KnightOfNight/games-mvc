# Shyland V24.27 — Brief 1: Character Hard Delete (#234)

**Release:** Version 24.27 (point release) · **Branch:** `version_24_27` · **Founding ticket:** #234 (no dependencies)
**Design authority:** GDD §3.8 Character Deletion (committed on this branch, `50f9c48`) and the ruling recorded on #234 (2026-08-13).

This brief is self-contained. Everything the implementation session needs is in this document, the repo, and #234.

---

## 1. Context

Deleting a character today silently orphans their entire inventory: `ItemInstance.owner` is `on_delete=SET_NULL`, so every held item becomes a row with **owner, current_room, and corpse all NULL** — a state that violates the exactly-one-location invariant enforced in `ItemInstance.save()` (Django's deletion collector bulk-updates around `save()`, so nothing catches it). The orphans are unreachable by any game path.

Everything else about deletion is already correct by schema design and stays untouched: `RoomVisit`, `ZoneCompletion`, `EffectInstance.target`, `CombatAction.character`, `PendingDialogueResponse.character`, `DialogueGreetingRecord.character` all CASCADE; `Corpse.killed_by`, `CombatAction.target_character`, `CombatSession.last_flee_character` are SET_NULL survivors; the auth `User` is untouched (the cascade runs User→Character only); the case-insensitive name constraint frees the name.

**The ruling (operator-confirmed, all three points):**

1. **Hard delete only.** No soft-delete model of any kind.
2. **Items are deleted with the character** — the entire inventory, held and equipped, bound and unbound.
3. **The Django admin console is the only deletion surface.** No in-game command, no management command, no player-facing self-delete.

**Design rules that must not be deviated from:**

- `soulbound_to` stays `SET_NULL`, untouched. Bound items can never leave inventory (drop excludes them entirely — v22 §8 fn 16; corpse contents are by definition unbound; vendor sale removes the item), so every row `soulbound_to` points at is already deleted by the owner cascade. Do not "improve" this.
- Items the character previously dropped into rooms are world items and survive. Corpse contents are corpse property and survive (until corpse decay).
- Corpses the character killed remain in the world with `killed_by=NULL` — lootable-by-nobody, decaying on their natural timer (operator-confirmed). Do not add a corpse sweep.
- No new admin UI. The stock admin delete flow (confirmation page with cascade summary) **is** the designed surface; the cascade summary truthfully enumerating everything that dies is the point.

## 2. Scope / non-goals

- **In scope:** the `owner` FK change + migration, cleanup of pre-existing orphaned rows, the consumer's deleted-character guard, the tick engine's zero-character session close, tests, arch doc.
- **Non-goals:** no seed changes (expected seed deletions: n/a — seed untouched), no new commands, no changes to `apps/profiles/` or any shared surface, no changes to death/Hardcore mechanics (§3.7), no player-facing anything.

---

## 3. Implementation steps

### Step 1 — Version constant (opening act, own commit)

Bump `SHYLAND_VERSION` in `django/src/apps/shyland/version.py` from `"24.26"` to `"24.27-DEV"`. Move the pin test with it in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py` (the `assertEqual(SHYLAND_VERSION, '24.26')` assertion, currently line 118). Then run the version-start `make deploy-dev` from the worktree.

### Step 2 — Schema change + orphan cleanup (migration)

In `django/src/apps/shyland/models.py`, change `ItemInstance.owner`:

```python
owner = models.ForeignKey(
    'Character',
    null=True, blank=True,
    on_delete=models.CASCADE,
    related_name='inventory',
)
```

Keep `null=True, blank=True` (owner is legitimately NULL for room items and corpse contents — the location invariant depends on it). Add a short comment stating the constraint the code can't show: held items die with their character by ruling (#234); room/corpse items are unaffected because their `owner` is already NULL.

Generate the migration with `make makemigrations APP=shyland` (expected `0046_…`; never hand-edit it). Then add a **data migration** (expected `0047_…`, created via `make makemigrations APP=shyland -- --empty` or the equivalent empty-migration path) that deletes every pre-existing orphan: `ItemInstance` rows where `owner`, `current_room`, and `corpse` are all NULL. These rows are unreachable by definition of the location invariant, so unconditional deletion is always correct (same logic as the #137 corpse-contents ruling). The migration must print/log the deleted count; the reverse is a deliberate no-op. Report the dev count in the closeout as actual-vs-expected (expected on dev: whatever prior test-character deletions left behind; expected on prod: 0 — no character has ever been deleted there; any nonzero is the cleanup doing its job and is safe by construction).

### Step 3 — Consumer guard: deleted-while-connected

`django/src/apps/shyland/consumers.py`. Today a mid-session deletion makes the next ORM touch raise `Character.DoesNotExist` (e.g. `get_character_fresh()` looks up by `self.character_pk`) — an unhandled crash. Add a guard at the command-dispatch level (`receive_json`): catch `Character.DoesNotExist`, then reuse the connect-time no-character routing **verbatim** — the `'No character found. Create one to play.'` error line, the structured `{'type': 'redirect', 'url': reverse('shyland:create_character'), 'ts': envelope_ts()}` envelope, then close the socket. Same message, same envelope shape, same URL as `connect()` (currently lines ~422–430); do not invent new wording. The HTTP side needs no change — the existing entry-gating rule already routes a character-less player to the creator.

### Step 4 — Tick engine: zero-character session close

`django/src/apps/shyland/management/commands/run_tick_engine.py`. Deleting an in-combat character empties the session's `characters` M2M (through-rows cascade) — but nothing closes a character-empty session: the v24.19 self-heal (#218) checks the NPC side only, and stale cleanup is time-based (`last_tick_at` keeps advancing, so it never fires). The session would tick forever holding its NPCs. Add the mirror-image guard in the combat pass: a session whose character side is empty closes through the **standard close path** — `is_active=False` plus `release_session_npcs(session)` (NPCs released and restored per the disengagement doctrine; there are no members to send fight-clear payloads to). Honor the per-tick query discipline (#107): fold the check into data the pass already loads (the participants load already fetches the character list — an empty list is the trigger); do not add a new per-session count query.

### Step 5 — Tests

New file `django/src/apps/shyland/tests/test_v24_27_brief1.py`. Required coverage (exact assertions at the session's discretion, intent fixed):

1. **Schema pin:** `ItemInstance._meta.get_field('owner').remote_field.on_delete` is `CASCADE`.
2. **Cascade correctness:** a character holding an unequipped item, an equipped item, and a soulbound-to-self equipped item → delete character → all three `ItemInstance` rows gone; a room-dropped item (owner NULL, `current_room` set) and a corpse-content item (owner NULL, `corpse` set) survive untouched.
3. **No orphan shape:** after the deletion in (2), zero `ItemInstance` rows exist with owner, current_room, and corpse all NULL.
4. **Survivors:** a `Corpse` with `killed_by=`the character keeps its row, `killed_by` NULL, `npc_name_snapshot` intact; the `User` row survives; loot rights are gone (the `killed_by_id == character.pk` predicate can never match again).
5. **Name reuse:** delete character named `Foo` → creating `foo` (case-insensitive collision form) succeeds.
6. **Orphan-cleanup migration logic:** the 0047 deletion predicate removes an artificially created all-NULL-location row and touches nothing else. (Constructing that row must bypass `save()` — use a bulk path such as `QuerySet.update()` on a legally created row, mirroring how real orphans were made.)
7. **Zero-character session close:** an active `CombatSession` with one character and one NPC; delete the character; run the combat pass; the session ends `is_active=False` with its NPCs released.
8. **Consumer guard:** via the existing communicator pattern (see `tests/test_session_takeover.py`): connect a character, delete the row out from under the session, send any command; expect the error line, the redirect envelope to the creator URL, and a closed socket — no exception.

The in-container invocation form is the only working one: `python manage.py test apps/shyland/tests` via `docker exec` in the django container. Full suite must pass: baseline 630 at the 24.26 stamp + this brief's new tests, no other count changes expected.

### Step 6 — Dev deploy

`make deploy-dev` from the worktree once implementation and all verification below pass (build + migrate against the local dev stack; never hand-rolled).

### Step 7 — Close the founding ticket

Close #234 with a comment linking the closeout report — gated on the verification section passing.

### Step 8 — Architecture doc (LAST, gated)

This step is gated on all implementation and verification steps above being complete and passing. `docs/shyland/Shyland_Architecture_v24.md`, updated in place per the point-release document rule:

- Stamp → **24.27**; the header **hash moves** (architectural: schema change + engine/consumer behavior).
- New header version paragraph in the established pattern (`Version 24.27 (point release) — Brief 1 applied on branch version_24_27: …`) covering: the `owner` CASCADE change (migration 0046), the orphan-cleanup data migration (0047, with counts), the consumer's deleted-character guard, and the tick engine's zero-character session close.
- §4 (The Shyland App): update the `ItemInstance.owner` description and the tick-engine combat-pass description to match.

---

## 4. Verification

Run after Step 5, before Steps 6–8:

1. Full in-container suite green: `python manage.py test apps/shyland/tests` (baseline 630 + new tests).
2. Post-migrate on dev: `ItemInstance.objects.filter(owner__isnull=True, current_room__isnull=True, corpse__isnull=True).count()` == **0**.
3. `showmigrations` shows 0046 and 0047 applied; migration files committed.
4. Manual cascade check on dev (shell): create a throwaway character with items via ORM, `.delete()`, confirm the returned collector dict counts the `ItemInstance` rows, and re-run check 2.

If a data table and prose in this brief disagree, the table is authoritative. There are no tables carrying numbers other than the counts above.

**PENDING DEPLOY-TIME ACTIONS:** none. The orphan cleanup is a migration and rides the ordinary migrate in every deploy path — nothing waits for the closeout tail beyond the deploy itself.

---

## 5. Operator playtest checklist (dev stack)

Ready after Step 6's `make deploy-dev`:

1. In `/admin/`, open a disposable test character who holds several items (at least one equipped). If none exists, create one via the game and grab items (or use `/stock-playtest-items`).
2. Delete the character from the admin. **Confirm the confirmation page's cascade summary lists the item instances** (plus visits/effects/etc.) — this enumeration is the designed final check.
3. After deletion: in admin, filter `ItemInstance` — no rows with empty owner+room+corpse.
4. Name reuse: create a new character with the deleted character's name (any casing) — accepted.
5. Deleted-while-connected: log the test character in in a browser, delete it from admin in another tab, then send any command in the game — expect "No character found. Create one to play." and routing to the character creator, not a dead socket.
6. (Optional) Mid-combat: start a fight with the test character, delete from admin, watch the NPC return to its room at full health within a few ticks.

---

## Closeout report requirements

`.txt` in `docs/shyland/` per standing convention: final commit hash, actual-vs-expected orphan-deletion count from migration 0047 on dev, any test-hygiene deviations, and the operator playtest disposition line (the closeout session reads it as a gate).
