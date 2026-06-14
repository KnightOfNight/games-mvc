# CLAUDE.md

`games-mvc` is a Docker-based platform for hosting multiple web games under a single Django deployment. Each game is a Django app living in `django/src/apps/`. All games share one database, one user/auth system, one Redis channel layer, and one nginx front door. The same codebase can be spun up as a separate installation for a single-game deployment — run a second copy, point it at a different domain and port.

Games currently in this repo:

| App | Type | URL |
|-----|------|-----|
| **Shyland** | Web-based MUD (Multi-User Dungeon) | `/shyland/` |
| **Shyship** | Battleship clone | `/shyship/` |
| **Shydle** | Browser word game | `/shydle` |

Docs: `docs/shyland/`

---

## Infrastructure at a Glance

| Container | Image | Role |
|---|---|---|
| `nginx` | nginx:alpine | SSL termination, WebSocket proxy at `/ws/` |
| `django` | python:3.12-slim + Daphne | ASGI server: Django 5 + Channels |
| `postgres` | postgres:16-alpine | Primary database (persistent volume `pgdata`) |
| `redis` | redis:7-alpine | Django Channels layer — WebSocket routing |

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
```

**Daily workflow:**
```
make start          # start all containers
make stop           # stop all containers (data preserved)
make restart        # stop + start
make logs           # follow live logs from all containers
make build          # rebuild Django image and recreate containers
```

> **Critical:** Source is baked into the Docker image at build time. After editing any file under `django/src/`, run `make build` before testing. `make restart` alone picks up no Python, template, or settings changes.

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
│       ├── Shyland_GDD_v3.md    ← full game design document
│       └── Shyland_Architecture.md ← technical architecture reference
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
- `models.py` — `Zone`, `Room`, `Character`, `RoomVisit`
- `consumers.py` — `SkylandConsumer` (movement, look, say, who)
- `currency.py` — currency utility (single `copper` BigIntegerField, escalating-multiplier tiers)
- `management/commands/seed_world.py` — creates The Convergence (5-room starter zone)

**Commands implemented:** `look`/`l`, `north`/`n`, `south`/`s`, `east`/`e`, `west`/`w`, `up`/`u`, `down`/`d`, `say`, `who`

**Client output message types:**
```json
{"type": "output", "text": "...", "category": "room|chat|system|error"}
{"type": "status", "vitality": N, "acuity": N, "longevity": N, "room_name": "..."}
```

**Architecture reference:** `docs/shyland/Shyland_Architecture.md`
**Game design reference:** `docs/shyland/Shyland_GDD_v3.md`

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

**SSL certs** — two files must exist in `ssl/` before `make start` will succeed:
```
ssl/<TLS_CERT_NAME>.crt
ssl/<TLS_CERT_NAME>.key
```

For local dev without real certs: `make gen-certs` (requires `make init` first).

---

## Shared Infrastructure Notes

**Auth:** Django's built-in auth system. Login at `/accounts/login/`. All WebSocket consumers should reject unauthenticated connections (check `self.scope['user'].is_authenticated` in `connect()`).

**User profile:** `apps.profiles` provides `UserProfile` — a one-to-one extension of `auth.User` with a `gamer_tag` field (max 20 chars, unique, nullable). A `post_save` signal auto-creates a `UserProfile` for each new `User`. Any game needing a display name should use `select_related('user__profile')` and access `user.profile.gamer_tag` (falling back to `user.username`). Do not add a separate name field to game-specific character models.

**Database:** Single PostgreSQL instance shared by all games. Each game's models live in their own app and migration history. No cross-app foreign keys between game apps — only FK to `auth.User`.

**Redis:** Used exclusively as the Django Channels channel layer. Not a general-purpose cache.

**Admin:** Django admin at `/admin/`. Each game registers its models in its own `admin.py`.
