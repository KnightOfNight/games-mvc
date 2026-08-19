# CLAUDE.md

`games-mvc` is a Docker-based platform for hosting multiple web games under a single Django deployment. Each game is a Django app living in `django/src/apps/`. All games share one database, one user/auth system, one Redis channel layer, and one nginx front door. The same codebase can be spun up as a separate installation for a single-game deployment — run a second copy, point it at a different domain and port.

Games currently in this repo:

| App | Type | URL |
|-----|------|-----|
| **Shyland** | Web-based MUD (Multi-User Dungeon) | `/shyland/` |
| **Shyship** | Battleship clone | `/shyship/` |
| **Shydle** | Browser word game | `/shydle` |

Docs: `docs/shyland/`

## Session Pre-Flight — Deployment Target

**Check this before starting work on any brief — implementation, verification/test, or ops alike.**

Run the pre-flight check script and gate on its exit code:

```
python3 scripts/check_docker_host.py
```

- **Exit 0** — target identified (the script prints **PRODUCTION** or **local dev**), posture coherent, daemon reachable. Proceed — but confirm the printed target matches the session's intent: production is for ops sessions and operator-authorized deploys only; design/implementation sessions belong on local dev.
- **Exit 1** — the target daemon is unreachable. This is a **hard blocker**: stop immediately, report the connectivity failure to the operator, and do no further work on the brief. Do not fall back to a different daemon. (For production, a common cause is an unloaded SSH key — the operator may only need an `ssh-add`; for local dev, the daemon may simply not be running. Diagnosing and fixing connectivity is the operator's call, not yours.)
- **Exit 2** — posture incoherent: `.env` is missing or does not match the env file the target implies (`.env.prod` when `DOCKER_HOST` is set, `.env.dev` when unset). Stop and report to the operator. **Never copy or edit an env file to make the check pass** — switching posture is the operator's deliberate act.

Rationale: the deployment target is production infrastructure. A brief that runs migrations, reseeds, or `docker` commands against the wrong daemon fails in the worst way — silently, against the wrong world.

### The standing target rule

**`DOCKER_HOST` set — any value — means production. Unset means the local dev daemon.** There is no third target; expanding this rule is an operator decision. The active `.env` must be a byte-for-byte copy of the matching target file — `.env.prod` when `DOCKER_HOST` is set, `.env.dev` when unset. The `crosscheck-env` Make guard enforces this automatically before every daemon-touching, state-changing target (`build`, `start`, `migrate`, `seed`, `verify`, `shell`, `makemigrations`, `createsuperuser`, `push-certs`); `require-local` blocks `nuke` outright when `DOCKER_HOST` is set. Both guards are check-only — they stop on mismatch and never copy or repair anything. Switching posture (`cp .env.prod .env` / `cp .env.dev .env`) is always a deliberate act, never something Claude does silently to make a guard pass.

Worktrees are initialized automatically: the committed `post-checkout` hook (activated once per clone with `make hooks`) copies `.env.dev`, `.env.prod`, and `ssl/` certs from the main checkout into a new worktree and sets its `.env` to **dev posture** — worktrees host design/implementation work, and a dev `.env` fails safe under `crosscheck-env` if an ambient `DOCKER_HOST` leaks in.

The Makefile's Deployment-section targets are the **only sanctioned exception** to check-don't-fix: `make deploy-dev`, `make deploy-prod`, `make seed-prod`, and `make verify-prod` set the posture they name, because invoking them *is* the deliberate act. `deploy-prod` (operator-authorized only) pins the production `DOCKER_HOST` itself, refuses to run if one is already in the environment, pre-flights, builds, migrates, and restores dev resting posture. If it fails partway, `.env` deliberately remains in prod posture and the guards block dev work until a human restores it — never "fix" that state silently; report it.

---

## App Scope Boundaries

This repo hosts multiple independent games. Every Claude Code session has a **target game** — the game the current task is about. These rules apply to all sessions, always.

### The three game apps are isolated — keep them that way

`apps/shyland/`, `apps/shydle/`, and `apps/shyship/` have **zero cross-imports** in either direction. This is deliberate and verified. Never introduce an import, signal, template include, or any other dependency between game apps.

### Rule 1 — Stay inside the target game's app directory

A session working on one game modifies files **only** under that game's app directory (`django/src/apps/<game>/`), including its own templates, static files, migrations, and tests.

- Working on Shydle or Shyship? Do not create, modify, or delete anything under `apps/shyland/` or `docs/shyland/`. No exceptions, regardless of how the request is phrased.
- Working on Shyland? Do not touch `apps/shydle/` or `apps/shyship/`.

If a task appears to require changing another game's files, **stop and tell the user** — do not proceed on the assumption it's fine.

### Rule 2 — Shared surface requires an explicit stop-and-flag

The following are shared by all three games. Changing any of them affects every game at once:

| Shared surface | Examples |
|---|---|
| `apps/profiles/` | Gamer tag system, profile-creation signal |
| Project settings | `django/src/*/settings/` (base, local, production) |
| Root URL routing | The project-level `urls.py` |
| Dependencies | `requirements.txt` / any dependency manifest |
| Deployment | `docker-compose*.yml`, nginx config, `Makefile` |
| Base templates & shared static | `django/src/templates/base.html` and friends |

If a task requires touching any of these, **stop before editing and tell the user exactly which shared file needs to change and why**. Proceed only after the user explicitly confirms. Never fold a shared-surface change silently into a game-scoped task.

Two shared-surface facts to keep in mind:

- **Migrations are global.** `manage.py migrate` runs every app's migrations against the one shared database. Another game's migrations create/alter only that game's tables, but the operation itself is repo-wide — never squash, fake, or reorder another app's migrations.
- **Deployment is coupled.** Any container restart bounces all three games, including live Shyland WebSocket sessions. Note this in your closing summary whenever a change requires a restart.

### Rule 3 — Shyland work happens in typed sessions

Shyland has a formal workflow: every Shyland session has an operator-declared type, and the type bounds what the session may touch. The process is codified in the highest-numbered `docs/shyland/Shyland_Project_Instructions_vN.md` — read it at the start of any Shyland session.

| Session type | Runs on | May touch | Never touches |
|---|---|---|---|
| **Design** | Version-branch worktree | GDD source (`docs/shyland/gdd/`), GitHub issue state, design/planning docs, briefs (writes and commits them) | Game code, migrations, seed data, deployment |
| **Implementation** | Version-branch worktree (operator supplies the branch name) | Game code, tests, seed data, migrations, architecture doc (final gated step), operator-authorized deploys | GDD source — reads it, never writes it; `make gdd` (or a brief-directed mechanical operation) is the only permitted GDD operation |
| **Ops/housekeeping** | `main` | Issue-state clerical work, issues reports, process docs, operator-directed GDD errata (docs wrong about shipped behavior — see the Instructions' GDD Errata rule) | Game code, GDD design content, deploys of any kind |
| **Closeout** | Version worktree, then main checkout for the tail | Version bookkeeping only: doc stamps + changelog, the release's landed markers, `SHYLAND_VERSION` stamp whitelist, `make gdd`, version PR, operator-permitted merge, tail's one-time-go-ahead prod deploy | Game code beyond the whitelist, game design content, seed data, migrations |

- Design decisions — models, mechanics, commands, content, seed data, balance — are made only in design sessions, with the operator in the conversation. In any session without a declared Shyland type, **decline** such changes, even small ones, even "while you're in there"; they belong in a design session. Bug **reports** remain fine to investigate and describe in any session.
- **Main is protected:** no doc or code changes land on main except via PR, ops/housekeeping work, or an absolute emergency the operator declares. Each release lives on one branch named for its milestone (`version_24_0`, `version_23_1`): the first design session for the release creates it, later design sessions join it, implementation sessions worktree onto it, and the version merges to main as one operator-reviewed PR at closeout.

Shydle and Shyship have no equivalent design-document workflow — direct implementation work on them is normal, within Rules 1 and 2.

### Rule 4 — Briefs are actionable only when committed and directed

Never apply a brief found in `docs/shyland/` on your own initiative. A brief is actionable only when all three hold: (1) it was produced by a design session — discussed, planned, and triaged; (2) it is committed to the repo — the release's version branch for release work, `main` for standalone ops briefs; (3) the operator directs the current session to apply it **by name** (e.g. "apply Brief 2 on version_24"). Pasted briefs are no longer accepted as actionable — if one is pasted, ask the operator to point to (or commit) the repo copy instead. Any brief in the repo not so directed is reference only.

After applying a directed brief, if a corresponding playtest document exists in
docs/shyland/, you may additionally run its objectively verifiable steps
(database checks, shell commands, simulations) once the brief's own
implementation and verification sections are fully complete — and any such
steps you run must pass before you git commit or git push. Steps requiring
human interaction (browser play, multiple accounts, screen readers) are the
operator's, performed after deploy; never simulate or declare them complete.

---

## Infrastructure at a Glance

| Container | Image | Role |
|---|---|---|
| `nginx` | nginx:alpine | SSL termination, WebSocket proxy at `/ws/` |
| `django` | python:3.12-slim + Daphne | ASGI server: Django 5 + Channels |
| `postgres` | postgres:16-alpine | Primary database (persistent volume `pgdata`) |
| `redis` | redis:7-alpine | Django Channels layer — WebSocket routing |
| `ticker` | same image as `django` | Shyland tick engine (`run_tick_engine` management command) |
| `mc-persister` | same image as `django` | MC durable-record persister (`run_mc_persister` management command) |

Architecture flow:

```
Browser (HTTPS :40443)
  → nginx  (SSL termination, /ws/ proxied with 24hr read timeout)
  → Daphne (ASGI — HTTP → Django, /ws/* → Channels consumers)
  → postgres (ORM) / redis (channel layer)
```

Services address each other by container name (`postgres`, `redis`, `django`). Only nginx is exposed to the host.

---

## Essential Make Commands

**First-time setup:**
```
make setup          # wizard + build + start (single command for fresh install)
make init           # wizard only — writes .env
make gen-certs      # self-signed TLS certs for local dev (requires make init first)
make check-secrets  # validates .env and SSL certs (auto-runs before make start)
make hooks          # activate committed git hooks (one-time per clone; auto-inits worktree env files)
```

**Daily workflow:**
```
make start          # start all containers
make stop           # stop all containers (data preserved)
make restart        # stop + start
make logs           # follow live logs from all containers
make build          # rebuild Django image and recreate containers
```

**Deploy:**
```
make deploy-dev     # deploy current source to the local dev stack (build + migrate)
make deploy-prod    # OPERATOR-AUTHORIZED ONLY: production deploy — flips posture,
                    # pre-flights, builds, migrates, restores dev posture
make seed-prod      # OPERATOR-AUTHORIZED ONLY: production seed — same contract as
                    # deploy-prod (flips posture, pre-flights, seeds, restores);
                    # the sanctioned path for closeout-tail data actions (#187)
make verify-prod    # OPERATOR-AUTHORIZED ONLY: read-only production verification —
                    # same posture contract; runs one brief-shipped verify_* command
                    # (VERIFY=verify_<name>) under the forced-rollback harness (#249)
```

> **Deployment law:** production runs `main` only — `make deploy-prod` runs from the main checkout, after the release PR merges, only in a closeout session's tail on the operator's one-time in-conversation go-ahead (one exact occurrence, no future permission implied). Never from a worktree, never with unmerged code, never from any other session type. `SHYLAND_VERSION` on main never carries a `-DEV` suffix (CI-enforced on PRs).

> **Critical:** Source is baked into the Docker image at build time. After editing any file under `django/src/`, run `make build` before testing. `make restart` alone picks up no Python, template, or settings changes.

> **Guards:** `build`, `start`, `migrate`, `seed`, `verify`, `shell`, `makemigrations`, `createsuperuser`, and `push-certs` all run `crosscheck-env` first, and `nuke` runs `require-local` (see the standing target rule in Session Pre-Flight). A guard failure means the posture is wrong — stop and resolve it deliberately; never copy an env file just to get past the guard.

**Django:**
```
make shell                          # Django shell inside running container
make migrate                        # run migrations
make makemigrations [APP=<name>]    # create migrations + auto-sync to local filesystem
make createsuperuser
```

**Games:**
```
make new-app NAME=<name>   # scaffold a new game app in django/src/apps/<name>/
```

After `make new-app NAME=<name>`, follow the printed instructions:
1. Add `'apps.<name>'` to `INSTALLED_APPS` in `django/src/game_mvc/settings/base.py`
2. Add URL patterns to `django/src/game_mvc/urls.py`
3. If the game uses WebSockets, register consumer routes in `django/src/game_mvc/routing.py`
4. Run `make makemigrations APP=<name> && make migrate`
5. Run `make build && make restart` to pick up the new app

---

## Project Layout

```
games-mvc/
├── CLAUDE.md                    ← you are here
├── Makefile                     ← all build and management commands
├── docker-compose.yml           ← four-container stack definition
├── .env.example                 ← template for required config values
├── nginx/conf/
│   └── default.conf.template    ← nginx config (envsubst fills DOMAIN, TLS_CERT_NAME)
├── django/
│   ├── Dockerfile               ← python:3.12-slim, installs requirements, runs entrypoint
│   ├── entrypoint.sh            ← collectstatic, then Daphne
│   ├── requirements.txt         ← pinned packages (Django, Channels, DRF, psycopg2, etc.)
│   └── src/
│       ├── manage.py
│       ├── apps/                ← one Django app per game (plus shared platform apps)
│       │   ├── profiles/        ← shared: UserProfile / gamer tag system
│       │   ├── shydle/          ← Shydle word game
│       │   ├── shyship/         ← Shyship Battleship clone
│       │   └── shyland/         ← Shyland MUD
│       └── game_mvc/            ← Django project package
│           ├── asgi.py          ← ASGI router (HTTP → Django, /ws/* → Channels)
│           ├── routing.py       ← WebSocket URL registry
│           ├── urls.py          ← HTTP URL config
│           ├── settings/
│           │   ├── base.py      ← shared settings (reads from .env)
│           │   ├── production.py← DEBUG=False, locked ALLOWED_HOSTS
│           │   └── local.py     ← DEBUG=True, InMemoryChannelLayer
│           └── context_processors.py
├── docs/
│   └── shyland/                 ← Shyland documentation
│       ├── Shyland_GDD_vN.md    ← GENERATED game design document build (do not edit; rebuilt by `make gdd`)
│       ├── gdd/                 ← GDD source: index + one file per section (authoritative)
│       └── Shyland_Architecture_vN.md ← technical architecture reference (versioned; use the highest N present)
├── scripts/
│   ├── init.py                  ← setup wizard (writes .env)
│   └── check_secrets.py         ← pre-start validation
└── ssl/                         ← TLS certs (gitignored)
```

---

## Django Project Internals

**`asgi.py`** — Routes HTTP to Django and WebSocket connections through `AuthMiddlewareStack` to the consumer registry in `routing.py`. Every WebSocket connection has the authenticated `request.user` available via `self.scope['user']`. Unauthenticated connections can be rejected in individual consumers.

**`routing.py`** — WebSocket URL registry. Current registrations:
```python
path('ws/shyship/<uuid:game_id>/', ShyshipConsumer.as_asgi())
path('ws/shyland/',               SkylandConsumer.as_asgi())
```

**`urls.py`** — HTTP routes. Current registrations:
- `/` → `HomeView` (game lobby)
- `/admin/` → Django admin
- `/accounts/` → `django.contrib.auth.urls` (login, logout, password)
- `/api/auth/` → DRF browsable API auth
- `/shydle` → Shydle app
- `/shyship/` → Shyship app
- `/shyland/` → Shyland app

**Settings:**
- `base.py` — PostgreSQL pointed at container `postgres`, Redis channel layer pointed at container `redis`, WhiteNoise for static files, DRF with session auth, reads all secrets from `.env` via `django-environ`
- `production.py` — `DEBUG=False`, locked `ALLOWED_HOSTS`, `SECURE_PROXY_SSL_HEADER` set for nginx termination, secure cookie flags
- `local.py` — `DEBUG=True`, open `ALLOWED_HOSTS`, `InMemoryChannelLayer` (no Redis needed for local dev)

**Templates:** Project-level templates at `django/src/templates/` (`base.html`, `registration/login.html`). Game-specific templates live inside each app's own `templates/` directory.

---

## Adding a New Game

```bash
make new-app NAME=mygame
```

Then:
1. Add `'apps.mygame'` to `INSTALLED_APPS` in `django/src/game_mvc/settings/base.py`
2. Add URL patterns to `django/src/game_mvc/urls.py`
3. If the game uses WebSockets, register consumer routes in `django/src/game_mvc/routing.py`
4. Run `make makemigrations APP=mygame && make migrate`
5. Run `make build && make restart`

---

## Games in This Repo

### Shyland

A web-based MUD (Multi-User Dungeon). Genre-collision setting where players move through text-described rooms, fight enemies, and interact in a persistent shared world.

**App:** `django/src/apps/shyland/`
**WebSocket:** `wss://<host>/ws/shyland/` → `SkylandConsumer`
**HTTP:** `/shyland/play/` → game client (login required)
**Docs:** `docs/shyland/`

**Key files:**
- `models.py` — `Zone`, `Room`, `Character`, `RoomVisit` (plus `Origin`, `Archetype`, items, NPCs, combat)
- `consumers.py` — `SkylandConsumer` (movement, look, say, who)
- `views.py` / `forms.py` — character creation flow (`/shyland/create/`, real-time name check)
- `currency.py` — currency utility (single `copper` BigIntegerField, escalating-multiplier tiers)
- `management/commands/seed_world.py` — creates The Convergence (5-room starter zone)

**Commands implemented:** see the dispatch table in `consumers.py` (`receive_json`) — that is the source of truth. The authoritative player-facing reference with aliases and noun syntax is GDD Section 9. Do not maintain a command list here.

**Client output message types:**
```json
{"type": "output", "text": "...", "category": "room|chat|system|error"}
{"type": "status", "vitality": N, "acuity": N, "longevity": N, "room_name": "..."}
{"type": "redirect", "url": "..."}
```

**Architecture reference:** the highest-numbered `docs/shyland/Shyland_Architecture_vN.md`
**Game design reference:** `docs/shyland/gdd/` (index `Shyland_GDD.md` plus one file per section — the authoritative source). The highest-numbered `docs/shyland/Shyland_GDD_vN.md` is the generated single-file build of the same content (`make gdd`); the section files win if they ever disagree.

---

### Shyship

Battleship clone. Players place ships and take turns attacking.

**App:** `django/src/apps/shyship/`
**WebSocket:** `wss://<host>/ws/shyship/<uuid:game_id>/` → `ShyshipConsumer`
**HTTP:** `/shyship/`

**Key files:**
- `models.py` — game session, ship placement, board state
- `consumers.py` — `ShyshipConsumer`
- `bot.py` — computer opponent logic

---

### Shydle

Browser word game.

**App:** `django/src/apps/shydle/`
**HTTP:** `/shydle` (no WebSocket)

---

## Conventions and Rules

### Shell commands (all sessions, all session types)

- **Never use a heredoc.** They fail intermittently in this environment's shell and the retry ends up at a temp file anyway — skip the failed attempt: **always write multi-line content (commit messages, issue/PR bodies, comments) to a temporary file first** (e.g. via the Write tool to `/tmp/…`) and pass it with `-F` / `--body-file` / the command's file-input flag.
- **Single-quote every grep/sed/awk pattern**, and never place backticks or `$( )` inside double-quoted shell arguments — command substitution inside a quoted pattern once executed an accidental production deploy (2026-07-27).

### Migrations

- Always run `make makemigrations APP=<name>` not bare `makemigrations` — the enhanced target syncs generated files back to the local filesystem automatically (Django generates them inside the container's ephemeral filesystem; they would be lost on the next `make build` otherwise)
- Never hand-edit migration files
- Always commit migration files

### Build cycle

After any edit to files under `django/src/` (Python, templates, static files, settings):

```bash
make build && make restart
```

`make restart` alone picks up nothing — source is baked into the image at build time.

### WebSocket consumers

- All consumers extend `AsyncJsonWebsocketConsumer`
- All ORM calls are wrapped in `@database_sync_to_async` — never call ORM methods directly from async context
- Use `select_related` on all character/room queries to avoid N+1 problems (and to avoid `SynchronousOnlyOperation` crashes when accessing FK descriptors in async context)
- Room-scoped broadcasts use `channel_layer.group_send()` with group name `room_{room_id}`

### Currency (Shyland)

- All currency stored as a single `BigIntegerField` named `copper` on `Character`
- All currency math goes through `apps.shyland.currency` — never inline
- `currency.subtract()` raises `ValueError` on insufficient funds — callers must catch and send an error to the player

### Security

- All game logic runs server-side — the client is a dumb terminal
- Never trust any value from the client for item quantities, currency, stats, or position
- Item soulbind status is enforced server-side on every write path

### Settings

- Never hardcode secrets — everything reads from `.env` via `django-environ`
- Use `production.py` in containers, `local.py` for development outside Docker

### Static files

- WhiteNoise serves static files from Django — no separate static file server
- `collectstatic` runs automatically in `entrypoint.sh` on container start

---

## Environment Setup

Required `.env` keys (template at `.env.example`; generate with `make init`):

| Key | Description | Source |
|-----|-------------|--------|
| `DOMAIN` | Hostname for this deployment | Prompted by wizard |
| `TLS_CERT_NAME` | Filename prefix for cert files in `ssl/` | Prompted by wizard |
| `SITE_TITLE` | Shown in admin and auth pages | Prompted by wizard |
| `DB_PASSWORD` | PostgreSQL password | Auto-generated if blank |
| `DJANGO_SECRET_KEY` | Django secret key | Auto-generated if blank |
| `HOST_PORT` | SSL port (default: `40443`) | Prompted by wizard |
| `DJANGO_SETTINGS_MODULE` | Settings module to use | Set to `game_mvc.settings.production` by wizard |
| `POSTGRES_DATA_VOLUME` | Postgres data location: `pgdata` named volume (dev) or `/mnt/postgresqldb` EBS bind mount (prod) | Per-target env file |

**Per-target env files:** `.env.prod` and `.env.dev` live alongside `.env` (all gitignored). The active `.env` is always a byte-for-byte copy of one of them — see the standing target rule in Session Pre-Flight. `crosscheck-env` blocks daemon-touching targets when they disagree.

**SSL certs** — two files must exist in `ssl/` before `make start` will succeed:
```
ssl/<TLS_CERT_NAME>.crt
ssl/<TLS_CERT_NAME>.key
```

For local dev without real certs: `make gen-certs` (requires `make init` first).

---

## Shared Infrastructure Notes

**Auth:** Django's built-in auth system. Login at `/accounts/login/`. All WebSocket consumers should reject unauthenticated connections (check `self.scope['user'].is_authenticated` in `connect()`).

**User profile:** `apps.profiles` provides `UserProfile` — a one-to-one extension of `auth.User` with a `gamer_tag` field (max 20 chars, unique, nullable). A `post_save` signal auto-creates a `UserProfile` for each new `User`. Games without per-character identity should use `select_related('user__profile')` and access `user.profile.gamer_tag` (falling back to `user.username`) rather than adding their own name field. **Exception (Shyland, v16):** `shyland.Character` has its own `name` field — a per-character identity chosen in the character creator, initialized from the gamer tag but independent of it afterward (case-insensitively unique via a DB constraint). Do not derive Shyland display names from the profile at read time.

**Database:** Single PostgreSQL instance shared by all games. Each game's models live in their own app and migration history. No cross-app foreign keys between game apps — only FK to `auth.User`.

**Redis:** the Django Channels channel layer, the Shyland presence keys, and the MC event stream (hot tier — Streams, bounded window). Not a general-purpose cache.

**Admin:** Django admin at `/admin/`. Each game registers its models in its own `admin.py`.
