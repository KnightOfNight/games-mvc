# Shyland V25.14 — Brief 1: Copper Management and the Open Filing Vocabulary

**Release:** Version 25.14 (milestone 66) · **Branch:** `version_25_14`
**Founding ticket:** #320 (agent door / sudo bot: full copper management — grant and deduct)
**Dependency riding the release:** #317 (sudo bot: `file_issue` carries operator-named labels)
**Authored:** V25.14 design session, 2026-09-01. GDD §10 passage committed at `b57b758` with the `(v25.14, #320/#317, pending implementation)` marker.

This brief is self-contained. It ships two admin capabilities: two new agent-door
actions (`grant_copper`, `deduct_copper`) mirrored into the sudo bot, and an
optional label set on the bot's `file_issue` backed by a new bot-side live
label-list query. **No model changes, no migrations, no seed changes, no
new dependencies.** There are **no pending deploy-time actions** — this release
is code-only; the prod migrate at closeout will be a no-op (migration head
stays `0056`).

**Technical coherence note (#252):** every structural claim below about existing
code was verified against the branch tip (`b57b758`, 2026-09-01) at writing
time by the design session — file and line references are to that tip. A
mismatch on a load-bearing claim at implementation pre-flight is a HARD STOP
back to the operator.

---

## 1. Opening act — version constant (standing requirement)

First commit of the release, before anything else:

- `django/src/apps/shyland/version.py` line 8: `SHYLAND_VERSION = "25.13"` → `"25.14-DEV"` *(verified: the constant reads `"25.13"` at the tip)*.
- The pin test moves in the same commit: `django/src/apps/shyland/tests/test_b2_amendment1.py` line 122, `self.assertEqual(SHYLAND_VERSION, '25.13')` → `'25.14-DEV'` *(verified at the tip)*.
- Then the version-start `make deploy-dev` from the worktree.

Commit and push (Step 0's closeout-report stub push precedes this per the
implementation-session ritual).

---

## 2. Design rules (do not deviate)

1. **The denomination is required and never assumed.** Both door actions take
   denominated fields — `platinum`, `gold`, `silver`, `copper` — each an
   optional **positive** integer, **at least one required**. There is no
   single `amount` field. The bot's tool schemas mirror this exactly, and the
   tool descriptions instruct the model: if the admin gives a bare number with
   no currency name, **ask which currency — never assume, never convert**.
   The model performs no currency arithmetic anywhere.
2. **All currency math through `apps/shyland/currency.py`** (standing law):
   `to_copper()` sums the denominations, `add()`/`subtract()` mutate,
   `display()`/`display_for_zone()` render. Never inline tier math.
3. **No upper bound** beyond positive-integer validation (operator-ruled).
   Deduction is **exact or refused** — insufficient funds draw a legible
   refusal naming the balance; never a clamp, never a partial.
4. **Atomicity matches the money paths:** `transaction.atomic()` +
   `Character.objects.select_for_update().get(pk=…)`, then
   `save(update_fields=['copper'])` — the exact discipline `do_buy`/`do_sell`
   use (verified: `django/src/apps/shyland/consumers.py`, `do_buy` ~4464–4494,
   `do_sell` ~4496–4508).
5. **Transparent narration (#261):** grant renders to an online recipient in
   category `'reward'` (the gift line's sibling — verified: `a_gift` sends its
   giving line with category `'reward'`, `mc_door.py:486`); deduct renders in
   category `'system'` (the move line's pattern — verified: `a_move` sends
   `'An admin moved you to a new room.'` with category `'system'`,
   `mc_door.py:911–912`). Offline targets get the DB update only, no line
   (the `a_gift`/`a_move` posture). Player-facing amounts render zone-local
   via `currency.display_for_zone`; receipts and door result data use engine
   names via `currency.display`.
6. **Everything on the record:** the MC record per action is emitted by the
   egress dispatch automatically — `_handle_request` in
   `django/src/apps/shyland/mc_consumer.py` (~line 225) emits one record per
   processed frame (verified). The new actions get this for free; no extra
   record code.
7. **Labels (#317):** the bot applies **existing labels only**, validated
   against the **live** repo label list — never a hardcoded list, never label
   creation or editing. **`triaged` is always refused** (a design-session
   act). Validation happens both at draft time (the model checks via the new
   label query and reads the labels back) and at filing time in machinery
   (`_file_issue` re-validates against a fresh fetch — the model is never
   trusted to have checked). The receipt reports the labels **actually
   applied, from the API response** — never model-typed (#306).
8. **Read-back covers labels:** the confirm gate's read-back includes the
   label set (or explicitly "no labels"); the explicit yes covers the whole
   draft including labels.
9. The thin-filing doctrine otherwise stands: unlabeled filings stay the norm;
   assignee and provenance footer unchanged.

---

## 3. Game side — `django/src/apps/shyland/mc_door.py`

### 3.1 Imports

Add `currency` to the module's relative imports (the module currently does
**not** import it — verified; it imports siblings as `from . import mc`, and
`transaction` is already imported from `django.db`).

### 3.2 The shared amount parser

One helper used by both handlers:

```python
DENOMINATIONS = ('platinum', 'gold', 'silver', 'copper')

def _require_amount(params):
    """Denominated amount → total copper. Each present denomination must
    be a positive integer; at least one is required (#320 — the
    denomination is never assumed)."""
    kwargs = {}
    for denom in DENOMINATIONS:
        if denom in params:
            kwargs[denom] = _require_int(params.get(denom), denom, minimum=1)
    if not kwargs:
        raise DoorError(
            'bad-params',
            "At least one of 'platinum', 'gold', 'silver', or 'copper' "
            "is required (a positive integer).")
    return currency.to_copper(**kwargs)
```

*(Verified: `_require_int(value, key, *, minimum=None)` exists with exactly
this signature and raises `bad-params` DoorErrors; `currency.to_copper` takes
`platinum/gold/silver/copper` keyword args, `currency.py:33`.)*

### 3.3 The DB write

One `@database_sync_to_async` helper, both directions:

```python
@database_sync_to_async
def _adjust_copper(char_pk, total, direction):
    """Atomic copper mutation under the money paths' locking discipline
    (the do_buy/do_sell pattern). Returns the new balance. Raises
    ValueError('Insufficient funds.') from currency.subtract."""
    with transaction.atomic():
        fresh = Character.objects.select_for_update().get(pk=char_pk)
        if direction == 'grant':
            fresh.copper = currency.add(fresh.copper, total)
        else:
            fresh.copper = currency.subtract(fresh.copper, total)
        fresh.save(update_fields=['copper'])
        return fresh.copper
```

*(Verified: `currency.add` raises `ValueError` only on negative amounts —
unreachable here; `currency.subtract` raises `ValueError('Insufficient
funds.')` when `amount > total`, `currency.py:101–110`. `Character` is already
imported in `mc_door.py`.)*

**Consumer-cache note (verified, no code needed):** the player consumer's
money paths pre-check funds on a fresh fetch (`get_character_fresh`, see the
`cmd_buy` path ~`consumers.py:2267`) and mutate under `select_for_update`, so
a door-side copper change concurrent with buy/sell cannot lose an update. The
consumer's cached `self.character.copper` may be momentarily stale for display
only — the same exposure every existing door write to shared state has
(#243's known family); do not build anything for it.

### 3.4 The handlers

```python
async def a_grant_copper(params, agent_name):
    char = await _resolve_character(params, key='to')
    total = _require_amount(params)
    balance = await _adjust_copper(char.pk, total, 'grant')
    if await _presence_online(char.pk):
        zone_slug = (char.current_room.zone.slug
                     if char.current_room_id else None)
        line = (f'An admin granted you '
                f'{currency.display_for_zone(total, zone_slug)}.')
        await _send_player_line(char.pk, line, 'reward',
                                agent_name=agent_name)
    return {'granted_copper': total,
            'amount_display': currency.display(total),
            'balance_copper': balance,
            'balance_display': currency.display(balance)}
```

`a_deduct_copper`: identical shape, direction `'deduct'`, with:

- the `ValueError` from `_adjust_copper` caught and re-raised as
  `DoorError('insufficient-funds', f'{char.name} has '
  f'{currency.display(balance)}; cannot deduct {currency.display(total)}.')`
  — the balance for the refusal is the resolved `char.copper`
  (`_resolve_character` returns the full row; the value is milliseconds old
  and the refusal is informational). **`insufficient-funds` is a
  new DoorError code** — record it in the arch doc (§8 below).
- the online line: `f'An admin took {currency.display_for_zone(total, zone_slug)} from you.'`,
  category `'system'`.
- result keys `deducted_copper` / `amount_display` / `balance_copper` /
  `balance_display`.

Narration wording is authored by this brief (creative-content policy) — use
the exact strings above. `display_for_zone(total, None)` falls back to
standard names (verified: `ZONE_CURRENCY_DISPLAY.get(None)` → `None` →
standard names); a room-less character gets engine names, which is correct.

*(Verified helpers: `_resolve_character(params, key='to')` resolves
case-insensitively and raises `not-found`, `mc_door.py:128–135`;
`_character_by_name` `select_related`s `current_room__zone`, so
`char.current_room.zone.slug` triggers no extra query and no async
descriptor access, `mc_door.py:120–125`; `_presence_online`, `mc_door.py:138`;
`_send_player_line(pk, text, category, *, agent_name)`, `mc_door.py:188`.)*

### 3.5 Registration

`ACTION_HANDLERS` (`mc_door.py:1923`, currently 13 entries ending
`'report': a_report` — verified) gains:

```python
    'grant_copper': a_grant_copper,
    'deduct_copper': a_deduct_copper,
```

No consumer change: the egress dispatch reads `ACTION_HANDLERS` dynamically
(verified, `mc_consumer.py` ~242).

---

## 4. Bot side — `agents/sudo_bot.py`

### 4.1 Kind sets

- `ACTION_KINDS` (frozenset, ~line 111 — verified) gains `'grant_copper'`
  and `'deduct_copper'` (they are door actions; the existing success path
  then adds their receipts automatically via `actions.add`).
- New frozenset beside `BOT_ACTIONS = frozenset({'file_issue'})` (~line 118 —
  verified):

  ```python
  BOT_QUERIES = frozenset({'issue_labels'})
  ```

- `_execute_tool` (~line 1519 — verified): include `BOT_QUERIES` in the
  unknown-tool check, and route it before the door branch:

  ```python
  if name in BOT_ACTIONS:
      result = await self._file_issue(actor_name, params)
  elif name in BOT_QUERIES:
      result = await self._issue_labels()
  else:
      result = await self.door_request(name, params)
  ```

  The success path needs no change for `issue_labels`: it is not in
  `BOT_ACTIONS` (no receipt) and `ledger.harvest` is keyed by tool name
  (`HARVEST.get(tool, ())` — verified, no-op for unknown tools).

### 4.2 The label-list query

New method beside `_file_issue`, same helper style (requests via
`asyncio.to_thread`, same headers, `GITHUB_TIMEOUT`, door-result shape,
response bodies never echoed into details — the `_file_issue` conventions,
verified ~lines 1576–1633):

- `GET {GITHUB_API}/repos/{GITHUB_REPO}/labels?per_page=100` — one page is
  the whole vocabulary at this repo's size; note the cap in a comment.
- Send the `Authorization` header only when `self.cfg.github_token` is set
  (the list is public-readable; filing remains token-gated exactly as today).
- On 200: return `{'ok': True, 'data': {'labels': [{'name': …,
  'description': …}, …]}}` — **with `triaged` filtered out** (it is not part
  of the filing vocabulary; the bot never offers or applies it).
- On errors: the `_file_issue` error shapes (`{'ok': False, 'error':
  'github', 'detail': 'HTTP <code>'}` / `'request failed'`).

### 4.3 `_file_issue` — labels

(Current body verified ~lines 1576–1633: validates `title`/`body`, token
gate, UTC provenance footer, POST `{'title', 'body', 'assignees':
[GITHUB_ASSIGNEE]}`, receipt data `{'number', 'url', 'title'}`.)

- Accept optional `labels` param: if present it must be a list of non-empty
  strings, else `bad-params`.
- When non-empty: fetch the live list (reuse the `issue_labels` fetch —
  fresh, machinery-side; the model's earlier query is not trusted), match
  **case-insensitively**, and apply the **canonical cased names** from the
  list. Any unknown name, or `triaged` in any casing, refuses the whole
  filing: `{'ok': False, 'error': 'bad-params', 'detail': …}` naming every
  offending label. Nothing is filed on a refused label set.
- Add the validated canonical `labels` list to the POST json.
- Receipt data gains `'labels': [<names from the response payload's
  'labels' entries>]` — the applied set from the API response, never the
  request echo (#306).
- Update the docstring's "no labels — triage fattens them" sentence to the
  v25.14 shape: labels optional, live-list-validated, `triaged` excluded,
  label CRUD stays human.

### 4.4 Tool schemas (`TOOLS`, ~line 167 — verified)

- **`grant_copper`** and **`deduct_copper`** — mirror the door params:
  `to` (string, required), `platinum`/`gold`/`silver`/`copper` (integers,
  each ≥ 1, all optional, **at least one required** — state this in the
  description; JSON Schema `required` cannot express it, so the door and the
  description carry it). Descriptions must include, verbatim in spirit:
  amounts are denominated — **if the admin names no currency ("give her
  100"), ask which currency; never assume a denomination and never convert
  between tiers yourself.** Note grant lands regardless of carry state
  (currency has none) and deduct refuses when the target lacks the funds.
- **`issue_labels`** — no parameters; description: the live repo label list
  for filings; call it when the admin wants labels on an issue, both to
  validate names and to answer "what labels are there".
- **`file_issue`** — schema gains optional
  `'labels': {'type': 'array', 'items': {'type': 'string'}}`; description
  updated (current text verified ~lines 733–745): gather title, body, **and
  any labels** conversationally; validate label names via `issue_labels`;
  read the COMPLETE draft back verbatim — title, full body, **and the label
  set (or "no labels")**; file only on the explicit yes, which covers the
  labels too.

### 4.5 Receipts (`_compose_receipt`, ~line 996 — verified)

New cases, composed from params and door data only:

- `grant_copper`: `f"granted {data.get('amount_display')} to {params.get('to')} (balance {data.get('balance_display')})"`
- `deduct_copper`: `f"deducted {data.get('amount_display')} from {params.get('to')} (balance {data.get('balance_display')})"`
- `file_issue` (existing case, ~line 1041): when the result data carries
  applied labels, append ` [labels: a, b]`; unchanged otherwise.

No `SYSTEM_TEMPLATE` change is required — the currency and label rules ride
the tool descriptions; do not restate them in the persona (keeps the prompt
surface small, the v25.6 posture).

---

## 5. Tests — `django/src/apps/shyland/tests/test_mc_agent_door.py`

Door tests only (the bot process lives outside the game image and is
exercised on the dev stack, consistent with every bot release since v25.6).
Use the file's existing fixtures/harness patterns. Cover at minimum:

1. `grant_copper` happy path: denominated params (e.g. `{'gold': 2,
   'silver': 5}`) → balance rises by exactly `to_copper(gold=2, silver=5)` =
   2,050; result carries `granted_copper`, `amount_display`,
   `balance_copper`, `balance_display` with engine-name rendering.
2. Online grant sends one `player_message` with category `'reward'` and the
   exact authored line (zone-local names when the target's zone has aliases —
   reuse however the existing door tests assert `_send_player_line` output);
   offline grant sends nothing.
3. `deduct_copper` happy path: balance falls exactly; online line category
   `'system'`, exact authored wording.
4. Insufficient funds: `deduct_copper` for more than the balance →
   `insufficient-funds` error, detail names the balance, **balance
   unchanged**.
5. Validation: no denomination → `bad-params`; a zero, negative, boolean, or
   non-int denomination → `bad-params`; unknown character → `not-found`;
   each refusal leaves the balance unchanged.
6. Registration: both kinds present in `ACTION_HANDLERS`; the MC record
   emission needs no new test (it is the dispatch's, already pinned).

The full suite must pass in-container using the only working invocation form:
`python manage.py test apps/shyland/tests` (directory-path form via
`docker exec`). Do not pin an absolute suite count; assert the invariant —
prior tests all green, new tests added and green.

---

## 6. Deploy and dev-stack verification

After implementation and tests pass:

1. `make deploy-dev` from the worktree (build + migrate; migrate is a no-op).
2. Restart the **dev** sudo bot from this worktree so the new tools load
   (`agents/botctl.py` — stop/start against the dev target, filing enabled as
   currently configured on dev). The prod bot is untouched — this release's
   bot changes reach production only after the closeout-tail deploy, on the
   operator's standing bot-restart action.

---

## 7. Operator playtest checklist (dev stack)

As an admin, with a fundable test character (its copper visible via `score`
or `sudo character <name>` — the player-detail query already returns
`copper`, verified `mc_door.py:260`):

1. `sudo give <char> 2 gold and 5 silver` → grant executes immediately (no
   confirm gate); the online recipient sees `An admin granted you 2 golds,
   5 silvers.` (zone-local names in aliased zones) in the reward color;
   balance rises by 2,050 copper; the admin's pane shows
   `sudo did: granted 2 golds, 5 silvers to <char> (balance …)`.
2. `sudo take 1 gold from <char>` → deduction lands; the recipient's line
   renders in the system register; receipt shows the new balance.
3. `sudo give <char> 100` (no currency named) → the bot asks which currency
   and takes **no** action until one is named.
4. Deduct more than the balance → legible refusal naming the balance; no
   change.
5. Grant to an **offline** character → no line anywhere; balance correct at
   next login.
6. `sudo what labels are there?` → the live label list, without `triaged`.
7. File a ticket naming labels (e.g. `bug`, `output`): the bot validates,
   reads back title + body + labels, files only on the explicit yes; the
   receipt carries the real number, URL, and applied labels; verify on
   GitHub, then close the test issue (operator action).
8. Ask for label `triaged`, and separately a nonsense label → both refused
   legibly at draft time; nothing filed.
9. Confirm the MC record: `sudo events` (or the record query) shows the
   grant/deduct actions attributed to `agent-sudo`.

---

## 8. Architecture doc — last, gated

This step is gated on all implementation and verification steps above being
complete and passing. `docs/shyland/Shyland_Architecture_v25.md`, updated in
place:

- Header stamp 25.13 → **25.14**; the header hash **moves** (architectural
  change: new door vocabulary, new error code, new bot tools).
- **§4.22 (the agent door, `mc_door.py`):** the two new actions — param
  shape (denominated, at least one positive), atomic write discipline,
  `insufficient-funds` as a new DoorError code, narration categories,
  result shapes, engine-name vs zone-local rendering split.
- **§4.23 (the sudo bot):** the two mirrored tools and the
  never-assume-a-denomination rule; `BOT_QUERIES` and the `issue_labels`
  live-list query (triaged filtered, token optional for the read);
  `file_issue` labels — draft-time and filing-time validation, canonical
  casing, read-back and confirm coverage, receipt labels from the API
  response.
- Append the release's summary line to the version-notes block at the top of
  the doc, following the existing per-release pattern.

---

## 9. Closeout

- Close **#320** and **#317**, gated on the verification section passing.
- Complete the closeout report stub in place
  (`docs/shyland/…closeout….txt`, created at Step 0): final commit hash,
  deviations if any, **and the operator playtest disposition** (one of the
  three #170 forms, verbatim-style).
- PENDING DEPLOY-TIME ACTIONS: **none** (restate in the report).
- End with the `implementation-session-end` ritual.
