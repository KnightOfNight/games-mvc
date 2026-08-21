# Shyland V25.4 — Brief 1: The MC Kill Switch

**Release:** Version 25.4 (milestone 56) · **Branch:** `version_25_4` · **Founding ticket:** #266 (closes with this release) · **Dependency riding the release:** #277 (operator-ruled in, 2026-08-20; closes with this release)

Written and committed by the V25.4 design session, 2026-08-20. Rulings of record are the dated comments on #266 and #277; GDD text landed at `b376a8c` (§10.11 kill-switch block, §9.1 `mc` chart row + footnote 22 + admin-subsection bullet + state-gating additions, all carrying the v25.4 pending-implementation markers). This brief is self-contained: implement from this document and the repo alone.

**Technical coherence (#252):** every structural claim below about existing code was verified against the code at writing time, 2026-08-20, at branch tip `b376a8c` (which is `4e2e299` + GDD edits only — no code drift possible). Each claim carries its source. The implementation session's pre-flight re-diffs the load-bearing ones.

---

## 1. What ships

One lever that silences every AI actor at once (#266), landing **before** any actor exists (25.5 ships the first). Concretely:

1. `MCKillSwitch` — a new database singleton model + migration. State survives restarts and reseeds; Postgres is the only store that does.
2. A sync emit path in `mc.py` so sync contexts (shell, Django admin) can emit the flip record.
3. The flip choke point — one classmethod all three flip surfaces route through; every actual state change emits a `mc_kill` MC record.
4. Egress enforcement in `mc_consumer.py` — killed = new attaches refused (close 4503), live connections severed within one stream-loop wake. Fail closed.
5. The `mc` admin command (`mc status` / `mc kill` / `mc restore`) — `admins.shyland`-gated with stealth, exactly like `sudo`/`last`.
6. Django admin registration (editable — config, not history) routed through the flip choke point.
7. The documented shell helper (documentation only; the helper *is* the flip classmethod).
8. **#277:** persister `BLOCK_MS` 5000 → 2000, mirroring `b812afb`, plus a constants pin test.
9. Tests, dev deploy, operator playtest checklist, architecture doc (gated, last).

**Design rules that must not be deviated from (ruled on #266, 2026-08-20):**

- **Fail closed.** Any failure to read the switch state = killed. Egress refuses/severs. The game degrading to "no AI" is the shipped game.
- **Capture never checks the switch.** No `mc_emit` call site, consumer tap, ticker tap, or the persister gains any switch awareness. The persister is monitoring infrastructure inside the trust boundary, not an actor — untouched by the switch (its only change in this brief is the #277 constant).
- **Every actual flip emits `mc_kill`; a no-change flip emits nothing** (there is no state change to record).
- **Stealth is byte-identical.** For non-members `mc` does not exist: absent from help, absent from completion, attempts draw the standard unknown-command response — the existing fn-18 machinery, extended, never reimplemented.
- **The read helper is fresh, never cached.** No module-level state, no TTL, no cross-process invalidation story.

## 2. Standing requirements (never omit)

1. **Version constant — this is the release's first implementation brief.** Opening act, its own commit: `SHYLAND_VERSION = "25.3"` → `"25.4-DEV"` in `django/src/apps/shyland/version.py` (line 8 — *confirmed against the file*), with the pin test moved in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py` line 118 asserts `SHYLAND_VERSION == '25.3'` → `'25.4-DEV'` (*confirmed against the file*). Then the version-start `make deploy-dev` from the worktree.
2. **In-session dev deploy:** exactly `make deploy-dev` from the worktree once implementation and verification pass (§8).
3. **Operator playtest checklist targeting the dev stack:** §9.
4. **Prior pending deploy-time actions:** none open — V25.3's closeout executed cleanly (migration 0051 applied on prod at deploy; no PENDING blocks remain from 25.1–25.3).

**Push cadence:** commit and push at every step boundary; branch only, never merge.

## 3. The model and migration

### 3.1 `MCKillSwitch` (append to `django/src/apps/shyland/models.py`, after `MCEvent` — *`MCEvent` confirmed at models.py:1240, file ends after it*)

```python
class MCKillSwitch(models.Model):
    """v25.4 (#266): the MC kill switch singleton — one lever that
    silences every AI actor at once (GDD §10.11). Config, not history:
    editable surfaces are sanctioned (the mc admin command, the shell
    helper, the Django admin); the append-only rule governs MCEvent,
    not this row. Row pk=1 always; absent row = alive. Enforcement
    points read fresh and fail closed on any read error.

    Shell helper (the sanctioned out-of-band flip, via make shell):
        from apps.shyland.models import MCKillSwitch
        MCKillSwitch.flip(True, by='<operator>', surface='shell')
    """
    killed = models.BooleanField(default=False)
    flipped_at = models.DateTimeField(null=True, blank=True)
    flipped_by = models.CharField(max_length=64, blank=True, default='')

    @classmethod
    def is_killed(cls):
        """Fresh read, no cache. Raises on DB failure — enforcement
        sites catch and treat any error as killed (fail closed)."""
        return bool(cls.objects.filter(pk=1)
                    .values_list('killed', flat=True).first())

    @classmethod
    def flip(cls, killed, *, by, surface, actor_id=None):
        """THE flip choke point — every surface routes here. Returns
        True if the state changed. Every actual change emits one
        mc_kill record; a no-change flip emits nothing."""
        row, _created = cls.objects.get_or_create(pk=1)
        if row.killed == bool(killed):
            return False
        row.killed = bool(killed)
        row.flipped_at = timezone.now()
        row.flipped_by = by or ''
        row.save(update_fields=['killed', 'flipped_at', 'flipped_by'])
        mc_emit_sync('mc_kill', actor_id=actor_id, actor_name=by or '',
                     data={'killed': bool(killed), 'surface': surface})
        return True

    def __str__(self):
        return f'MC kill switch: {"engaged" if self.killed else "not engaged"}'
```

Import notes (*confirmed against models.py imports at writing time — the implementation session verifies*): `timezone` from `django.utils` (add if absent); `mc_emit_sync` imported from `apps.shyland.mc` **inside `flip`** (function-level import) — `mc.py`'s docstring law is "game code imports mc, never the reverse" (*confirmed, mc.py:4*), and a module-level import in `models.py` is safe in that direction but a function-level one keeps migration-time imports clean. `mc_kill` fits `kind`'s conventions (the *record's* kind field cap of 16 lives on `MCEvent.kind` — *confirmed models.py:1245* — and `mc_kill` is 7 chars).

### 3.2 Migration

`make makemigrations APP=shyland` — expected: `0052_mckillswitch` (accept the generated name; latest existing is `0051_create_shyland_agents_group.py` — *confirmed against the migrations directory*). Then `make migrate`. **Never hand-edit; always commit the migration file.** Schema-only — no data migration, no seeded row: absent row = alive is the designed default state.

## 4. The sync emit path (`django/src/apps/shyland/mc.py`)

`mc_emit` is async-only (*confirmed: `async def mc_emit`, mc.py:56, client `redis.asyncio`, mc.py:15/43*). The flip choke point is sync (ORM classmethod callable from shell and Django admin). Add a sync twin — same record shape, same fire-and-forget law, sync client:

```python
def mc_emit_sync(kind, *, actor_id=None, actor_name='', room_id=None,
                 audience=(), data=None):
    """Sync twin of mc_emit for sync creation sites (v25.4: the kill
    switch flip — shell, Django admin, and the command's ORM path).
    Identical record shape and fire-and-forget law; builds a
    short-lived sync client per call (flips are rare by definition)."""
    try:
        record = {
            'kind': kind,
            'actor_id': '' if actor_id is None else str(actor_id),
            'actor_name': actor_name or '',
            'room_id': '' if room_id is None else str(room_id),
            'audience': json.dumps(list(audience)),
            'data': json.dumps(data or {}),
        }
        client = sync_redis.Redis(host=settings.REDIS_HOST, port=6379, db=0)
        try:
            client.xadd(MC_STREAM_KEY, record,
                        maxlen=settings.MC_STREAM_MAXLEN, approximate=True)
        finally:
            client.close()
    except Exception:
        _warn('shyland mc: emit failed — record dropped (kind=%s)', kind)
```

Import `import redis as sync_redis` at module top (the sync package is installed — the persister already `import redis`, *confirmed run_mc_persister.py:16*). The record dict shape is byte-compatible with `mc_emit`'s (*confirmed mc.py:66–73*) — the persister maps it with zero changes.

## 5. Egress enforcement (`django/src/apps/shyland/mc_consumer.py`)

Close-code vocabulary: **4403** = not authorized (existing — *confirmed mc_consumer.py:92*), **4503** = killed. Killed is not not-authorized.

1. **Read helper** (module level or on the consumer):

```python
@database_sync_to_async
def _switch_killed():
    from apps.shyland.models import MCKillSwitch
    return MCKillSwitch.is_killed()

async def switch_killed():
    """Fail closed: any failure to read = killed."""
    try:
        return await _switch_killed()
    except Exception:
        return True
```

(`database_sync_to_async` already imported — *confirmed mc_consumer.py:19*. The consumer's no-character-table law (docstring, mc_consumer.py:6–8) is untouched: `MCKillSwitch` is not the character table.)

2. **Connect gate:** in `connect()`, after the `check_shyland_agent()` pass and before `accept()` (*current order confirmed mc_consumer.py:79–97*): if `await switch_killed()` → accept-then-close `4503` (the 4403 pattern: the code must reach the client). Order is deliberate — membership is checked first, so a non-member sees 4403 whether or not the switch is engaged (the switch leaks nothing to non-members).
3. **Live sever:** in `_live()` (*confirmed mc_consumer.py:211–220*), at the top of each `while True` iteration: if `await switch_killed()` → `await self.close(code=4503)`, return. The loop wakes at least every `LIVE_BLOCK_MS` (2000ms — *confirmed mc_consumer.py:32*), so a hung or rogue agent is severed within ~2s without its cooperation.
4. **Replay sever:** in `_replay()`'s batch loop (*confirmed mc_consumer.py:193–201*), the same check per batch iteration — a kill during a long catch-up must not wait for replay to finish.

Cost: one indexed single-row read per wake per agent (single-digit agents) — deliberately uncached per the ruling.

## 6. The `mc` admin command (`django/src/apps/shyland/consumers.py`)

All six touch points; the fn-18 stealth machinery is **extended, never reimplemented**:

1. **`COMMAND_TABLE`** (*confirmed consumers.py:262–300*): add `'mc': ('cmd_mc', True),` in the v22-brief-3 block alongside `sudo`/`last`.
2. **`ADMIN_VERBS`** (*confirmed consumers.py:307: `{'sudo', 'last'}`*): → `{'sudo', 'last', 'mc'}`. This alone handles: the central `_dispatch` gate with byte-identical unknown-command response (*confirmed consumers.py:744*), and the connect-time verb-list subtraction for non-members (*confirmed consumers.py:576–577*).
3. **`DYING_ALLOWED`** (*confirmed consumers.py:340–345*): add `'mc'` (GDD §9.1 state-gating: allowed while dying; admin verbs pass the gate so stealth stays byte-identical). `COMBAT_BLOCKED` is a deny-list (*confirmed consumers.py:318–333*) — `mc` is absent, therefore allowed in combat, matching the GDD edit. No `PROMPT_VERBS` entry — `cmd_mc` owns its usage line.
4. **`HELP_SECTIONS`** (*confirmed consumers.py:1290–1310; admin rows carry a 4th element `True`, rendered members-only via `cmd_help`'s `is_admin` filter, consumers.py:1340–1344*): add to the action section, alphabetically between `loot` and `pickup` (matching the §9.1 chart position): `('mc', 'mc <status|kill|restore>', 'The MC kill switch.', True),`
5. **Tab completion** (`handle_complete`, *confirmed consumers.py:3846–3883; literal-word branches use `self._complete_words(arg_text, words, first_only=True)`, e.g. the settings branch at 3857–3859*): add a branch — membership-gated, so completion never leaks the pool to non-members:

```python
elif head == 'mc':
    if await self.check_shyland_admin():
        options = self._complete_words(
            arg_text, ['kill', 'restore', 'status'], first_only=True)
```

6. **The handler** (place near `cmd_sudo`, *confirmed consumers.py:3296*):

```python
async def cmd_mc(self, args):
    # v25.4 (#266): the MC kill switch (GDD §10.11, §9.1 fn 22).
    # Closed subcommand vocabulary, prefix-matched (first letters are
    # distinct, ambiguity impossible). Renderings never vary.
    sub = args.strip().lower()
    matches = ([s for s in ('status', 'kill', 'restore')
                if s.startswith(sub)] if sub else [])
    if len(matches) != 1:
        await self.send_output('Usage: mc <status|kill|restore>', 'error')
        return
    action = matches[0]
    if action == 'status':
        killed = await database_sync_to_async(MCKillSwitch.is_killed)()
        state = ('engaged — all AI actors are silenced.' if killed
                 else 'not engaged — AI actors may act.')
        await self.send_report_lines([{'k': 'MC kill switch:', 'v': f' {state}'}])
        return
    engage = (action == 'kill')
    changed = await database_sync_to_async(MCKillSwitch.flip)(
        engage, by=self.character.name, surface='command',
        actor_id=self.character.pk)
    if engage:
        if changed:
            await self.send_output(
                'MC kill switch engaged. All AI actors are silenced.', 'success')
        else:
            await self.send_output('The kill switch is already engaged.', 'warn')
    else:
        if changed:
            await self.send_output(
                'MC kill switch released. AI actors may act again.', 'success')
        else:
            await self.send_output('The kill switch is not engaged.', 'warn')
```

Voice assignments per the three-layer doctrine: usage line = CLI error (error-color); already-in-state = world declined (warn); successful flip = world answered (success); `status` = a report rendering (Kind-1 key/value line, unstamped). `send_output`, `send_report_lines`, and the `{'k':…,'v':…}` line shape *confirmed in use at consumers.py:3293/3309 and 1347–1379*; the `status` fail posture needs no special handling — the dispatch guard (*confirmed consumers.py:693–697*) already prevents any handler crash from dropping the connection. Import `MCKillSwitch` alongside the other model imports in `consumers.py`.

## 7. Django admin (`django/src/apps/shyland/admin.py`)

Register `MCKillSwitch` **editable** (config, not history — the read-only pattern stays on `MCEvent`), routed through the choke point (*registration decorator pattern confirmed against admin.py*):

```python
@admin.register(MCKillSwitch)
class MCKillSwitchAdmin(admin.ModelAdmin):
    """v25.4 (#266): the kill switch is config, not history — editable
    by design (the read-only-admin pattern governs MCEvent). Saves
    route through MCKillSwitch.flip so every flip emits its mc_kill
    record regardless of surface."""
    list_display = ('killed', 'flipped_at', 'flipped_by')
    fields = ('killed',)
    readonly_fields = ()

    def has_add_permission(self, request):
        return not MCKillSwitch.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        MCKillSwitch.flip(obj.killed, by=request.user.username,
                          surface='django-admin')
```

`save_model` deliberately does not call `super()` — `flip` performs the write (get_or_create pk=1 + save), keeping the no-change-no-emit rule intact even from the admin form. Add `MCKillSwitch` to the admin's model import line (*import block confirmed at admin.py:6*).

## 8. #277 — the persister block constant

`django/src/apps/shyland/management/commands/run_mc_persister.py` line 28 (*confirmed: `BLOCK_MS = 5000`*): change to `2000`, with a comment mirroring the egress constant's (*mc_consumer.py:28–31*):

```python
# Must sit comfortably inside the client's socket_timeout (redis-py
# >= 8 defaults it to 5s): a server-side BLOCK equal to the client
# read cap is a coin-flip race every idle cycle (#277). 2s block,
# 5s cap, no race — the b812afb egress fix, mirrored.
BLOCK_MS = 2000
```

No other persister change of any kind (the switch never touches it).

## 9. Tests

New file `django/src/apps/shyland/tests/test_mc_kill_switch.py` (directory layout *confirmed*; reuse `test_mc_egress.py`'s communicator and patching patterns). Required coverage:

1. **Flip semantics:** default state alive (`is_killed()` False, no row); `flip(True)` → killed, row pk=1, returns True, emits exactly one `mc_kill` record (patch `mc_emit_sync` at its use site) with `data={'killed': True, 'surface': …}`; repeat `flip(True)` → returns False, **zero** emits; `flip(False)` → emits again; `flipped_at`/`flipped_by` set on change.
2. **Egress connect gate:** member + engaged switch → accept-then-close **4503**; member + alive → `hello` flows (existing test shape); non-member + engaged → **4403** (membership checked first — the switch leaks nothing).
3. **Egress live sever:** an attached live connection observes close 4503 after the switch engages (patch the switch read or flip the row mid-test).
4. **Fail closed:** with the switch read raising (patch `is_killed` to raise), connect is refused 4503.
5. **`cmd_mc`:** non-member → byte-identical unknown-command line; member: `mc` bare and `mc bogus` → the usage line (error); `mc status` both states; `mc kill` / `mc k` (prefix) flips + success line; second `mc kill` → warn, no emit; `mc restore` symmetric.
6. **Surface wiring:** `'mc'` in `COMMAND_TABLE`, in `ADMIN_VERBS`, in `DYING_ALLOWED`; help renders the `mc` row for members only; completion returns `['kill', 'restore', 'status']`-prefixed pools for members and `[]` for non-members.
7. **Constants pin (#277):** `run_mc_persister.BLOCK_MS == 2000` and `mc_consumer.LIVE_BLOCK_MS == 2000`, each asserted `< 5000` with the redis-py-8 rationale in the test docstring (no existing test pins either constant — *confirmed by grep over tests/*).
8. **Migration applied:** the table exists (the standard migration-execution smoke the suite's DB setup provides implicitly; an explicit `MCKillSwitch.objects.count()` touch suffices).

**Invocation (the only working form):** `python manage.py test apps/shyland/tests` via `docker exec` in the django container.

## 10. Verification (gate for issue closure)

| # | Check | Expectation |
|---|---|---|
| V1 | Full in-container suite | All green; count grows by this brief's tests only (744 on the 25.3 stamped build — *confirmed from the 25.3 record*; report actual vs expected) |
| V2 | `grep -n 'BLOCK_MS' django/src/apps/shyland/management/commands/run_mc_persister.py` | `2000`, with the #277 comment |
| V3 | `grep -rn 'mc_emit' django/src/apps/shyland/mc_consumer.py` | Zero hits — egress still never emits (the 25.3 grep-law holds; the switch read is ORM, not emit) |
| V4 | `grep -n 'is_killed\|MCKillSwitch' django/src/apps/shyland/management/commands/run_mc_persister.py django/src/apps/shyland/management/commands/run_tick_engine.py` | Zero hits — persister and ticker have no switch awareness |
| V5 | Dev stack after `make deploy-dev`: `mc kill` from an admin character, then attach the 25.3 agent test client | Attach draws close 4503; after `mc restore`, attach flows normally |
| V6 | Dev stack: `docker logs` on the mc-persister container over ≥10 idle minutes | Zero `redis unavailable (Timeout reading from socket)` lines (#277 fixed) |
| V7 | `MCEvent` rows | One `mc_kill` row per actual flip, `surface` correct per surface exercised, no rows for no-change flips |

When a table and prose disagree, the table is authoritative.

## 11. Deploy and playtest

**Deploy:** `make deploy-dev` from the worktree once §9/§10 pass (build + migrate; the version-start deploy already ran at step §2.1).

**PENDING DEPLOY-TIME ACTIONS: none.** The migration rides the ordinary closeout-tail `make deploy-prod` automatically; the switch's designed initial state is the absent-row default (alive); no seed change, no data action. (Executor checkpoint satisfied vacuously.)

**Operator playtest checklist (dev stack):**

1. Non-admin character: `mc` → the standard unknown-command line; `help` shows no `mc` row; tab on `mc ` offers nothing.
2. Admin character: `help` shows the `mc` row; `mc status` → "not engaged"; `mc bogus` → the usage line.
3. `mc kill` → success line; `mc status` → "engaged"; `mc kill` again → "already engaged" warn.
4. With the switch engaged, attach the agent test client (the 25.3 playtest path) → connection closes with code 4503.
5. `mc restore`, attach the agent client, confirm live events; then `mc kill` while it is attached → the connection drops within ~2 seconds.
6. Django admin (`/admin/`): flip the switch off/on; confirm the row shows `flipped_by` = your username.
7. `make shell`: `MCKillSwitch.flip(False, by='<you>', surface='shell')`; `mc status` in-game reflects it.
8. Inspect `MCEvent` (admin or shell): one `mc_kill` row per flip performed above, with the right `surface` each time.
9. Leave the dev stack idle ≥10 minutes; persister logs show no timeout churn (#277).

## 12. Architecture doc (LAST, GATED)

This step is gated on all implementation and verification steps above being complete and passing. `docs/shyland/Shyland_Architecture_v25.md`, updated in place (point-release rule): header stamp → 25.4 and **the hash moves** (architectural change: new model, new command surface, egress enforcement); new version paragraph in the header block; **new §4.21 — The MC kill switch** (`MCKillSwitch`, the flip choke point, `mc_emit_sync`, the three surfaces, close-code vocabulary, fail-closed law); touched lines in **§4.1** (models list — *section confirmed at line 243*), **§4.7** (admin — the editable-config exception beside the read-only `MCEvent` pattern — *line 988*), **§4.14** (command layer: `mc` in the chart/gating inventories — *line 1405*), **§4.19** (persister `BLOCK_MS` + #277 — *line 1581*), **§4.20** (egress: the switch gate and 4503 — *line 1615*).

## 13. Closeout

Closeout report `docs/shyland/Shyland_V25.4_Brief_1_Closeout.txt` (stub created and pushed at Step 0 per the implementation ritual; completed in place): final commit hash, actual-vs-expected on V1 and any deviations, **the operator playtest disposition verbatim-style** (#170), and the #266/#277 closures gated on §10 passing. GDD source is never touched (the design session already landed it; the markers are the next design session's/closeout's sweep). Issue-touching work ends with: **run the issues report.**
