# games-mvc

A Docker-based server infrastructure for building and hosting web games. The stack is intentionally general-purpose: one deployment can run multiple games simultaneously, each as its own Django app, all sharing a single database and user account system. The same codebase can also be deployed as a single-game installation — spin up a second copy, point it at a different domain, and it runs independently.

The MVP entry point is `make setup`, which walks through configuration interactively, builds everything, and starts the server.

---

## Quick Start

```bash
make setup        # wizard + build + start
make migrate      # run initial database migrations
make createsuperuser
```

Then visit `https://<your-domain>:40443`.

If you don't have real SSL certs yet, generate self-signed test certs first:

```bash
make init         # run the wizard first (creates .env)
make gen-certs    # generate test certs from .env values
make setup        # build and start
```

---

## Prerequisites

- [Rancher Desktop](https://rancherdesktop.io/) (or Docker Desktop) — provides `docker` and `docker compose`
- Python 3 — for the setup wizard and secrets check
- OpenSSL — for `make gen-certs` (included on macOS)
- `envsubst` — for nginx config generation (included on macOS via `gettext`)

If `docker` is not in your `$PATH`, Rancher Desktop installs it at `~/.rd/bin`. Add that to your shell profile:

```bash
export PATH="$HOME/.rd/bin:$PATH"
```

---

## Getting Started (detailed)

### 1. Run the wizard

```bash
make init
```

The wizard prompts for:

| Prompt | Description |
|--------|-------------|
| Domain name | The hostname this server is accessed at (e.g. `battleship.private.magrathea.com`) |
| TLS cert name | Filename prefix for your cert files in `ssl/` (e.g. `battleship`) |
| Site title | Shown in the admin panel and auth pages |
| DB password | Auto-generated if you press Enter |
| Django secret key | Auto-generated if you press Enter |
| Host port | SSL port — defaults to `40443`, change per-installation for multi-game routing |

This writes a gitignored `.env` file. Re-running the wizard shows existing values as defaults — only enter what you want to change.

### 2. Place SSL certificates

Put your cert files in `ssl/`:

```
ssl/<cert-name>.crt   ← full chain (domain cert + all intermediates concatenated)
ssl/<cert-name>.key   ← private key
```

The cert name matches what you entered in the wizard. If your CA provides separate files, combine them:

```bash
cat domain.crt intermediate.crt > ssl/battleship.crt
```

For testing without real certs:

```bash
make gen-certs
```

This generates a self-signed cert using the domain and cert name from `.env`. Browsers will show a security warning — use your vendor certs for a trusted connection.

### 3. Build and start

```bash
make build    # build Docker images
make start    # start all containers
```

Or combine all steps with `make setup`.

### 4. Run migrations

```bash
make migrate
```

Run this once after the initial start, and again after adding a new game app or changing models.

### 5. Create a superuser

```bash
make createsuperuser
```

The Django admin is at `https://<your-domain>:40443/admin/`.

---

## Make Targets

### Setup

| Target | Description |
|--------|-------------|
| `make setup` | Full first-time setup: runs the wizard, checks secrets, generates the nginx config, builds Docker images, and starts all containers. The single command for a fresh install. |
| `make init` | Runs the setup wizard only. Prompts for configuration and writes `.env`. Safe to re-run — existing values are shown as defaults. |

### Docker

| Target | Description |
|--------|-------------|
| `make build` | Builds the Django Docker image. The nginx, postgres, and redis containers use pre-built images and are not rebuilt here. |
| `make start` | Starts all four containers in the background (`docker compose up -d`). Runs `check-secrets` and regenerates the nginx config first. |
| `make stop` | Stops all containers (`docker compose down`). Data in the postgres volume is preserved. |
| `make restart` | Runs `stop` then `start`. |
| `make logs` | Follows live log output from all containers. Ctrl-C to stop. |
| `make tick-logs` | Follows logs from the `ticker` container only. |
| `make nuke` | Removes all containers, volumes, and images for this project. More destructive than `make stop` — wipes the database and SSL volume entirely. |

### Django

| Target | Description |
|--------|-------------|
| `make shell` | Opens a Django shell (`manage.py shell`) inside the running Django container. |
| `make migrate` | Runs `manage.py migrate` inside the running Django container. Run this after the initial start and after any model changes. |
| `make makemigrations` | Runs `manage.py makemigrations`. Pass `APP=<name>` to limit to a specific app: `make makemigrations APP=battleship`. |
| `make createsuperuser` | Creates a Django admin superuser interactively inside the running Django container. |
| `make db-reset` | Drops all volumes, rebuilds, starts, runs migrations, and calls `seed_world`. A full database wipe and re-seed in one command. |

### Games

| Target | Description |
|--------|-------------|
| `make new-app NAME=<name>` | Scaffolds a new game app inside `django/src/apps/<name>/` using `manage.py startapp`. After running, follow the printed instructions to wire the app into the project. |

### SSL

| Target | Description |
|--------|-------------|
| `make gen-certs` | Generates a self-signed TLS cert (10-year validity) using the `DOMAIN` and `TLS_CERT_NAME` values from `.env`. Writes `ssl/<name>.crt` and `ssl/<name>.key`. Requires `make init` to have run first. |
| `make push-certs` | Copies local `ssl/` cert files into the Docker `ssldata` volume. Runs automatically as part of `make setup` and `make gen-certs`. Run standalone when deploying with `DOCKER_HOST` pointing at a remote daemon. |
| `make check-secrets` | Validates that `.env` exists with all required keys and that both SSL cert files are present. Runs automatically before `make start`. Exits with an error and explanation if anything is missing. |

### Help

| Target | Description |
|--------|-------------|
| `make help` | Prints a summary of all available targets. |

---

## Adding a Game

```bash
make new-app NAME=battleship
```

This creates `django/src/apps/battleship/` with the standard Django app skeleton. Follow the printed instructions:

1. Add `'apps.battleship'` to `INSTALLED_APPS` in `django/src/game_mvc/settings/base.py`
2. Add URL patterns to `django/src/game_mvc/urls.py`
3. If the game uses WebSockets, register consumer routes in `django/src/game_mvc/routing.py`
4. Run `make makemigrations APP=battleship && make migrate`
5. Run `make build && make restart` to pick up the new app

---

## Repository Contents

```
mvc/
├── Makefile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── nginx/
│   └── conf/
│       └── default.conf.template
├── django/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   └── src/
│       ├── manage.py
│       ├── apps/
│       └── game_mvc/
│           ├── settings/
│           │   ├── base.py
│           │   ├── local.py
│           │   └── production.py
│           ├── asgi.py
│           ├── context_processors.py
│           ├── routing.py
│           ├── urls.py
│           └── wsgi.py
├── django/src/templates/
│   ├── base.html
│   └── registration/
│       └── login.html
├── ssl/
│   └── .gitignore
└── scripts/
    ├── init.py
    └── check_secrets.py
```

### Top-level

**`Makefile`**
All build, deployment, and management commands. Loads `.env` automatically so Make variables like `DOMAIN` and `TLS_CERT_NAME` are available to targets.

**`docker-compose.yml`**
Defines the four containers (`nginx`, `django`, `postgres`, `redis`) and the `pgdata` volume. Reads configuration from `.env`. The `postgres` container has a healthcheck; `django` waits for it before starting.

**`.env.example`**
A template showing every required `.env` key with placeholder values. Copy and edit to create `.env`, or just run `make init`.

**`.gitignore`**
Excludes `.env`, all files in `ssl/` (certs and keys), the generated `nginx/conf/default.conf`, Python cache files, and the Django `staticfiles/` build directory.

---

### `nginx/`

**`nginx/conf/default.conf.template`**
nginx virtual host configuration template. Contains `${DOMAIN}` and `${TLS_CERT_NAME}` placeholders that are substituted by `make start` using `envsubst`. The generated `nginx/conf/default.conf` (gitignored) is what gets mounted into the nginx container.

Key behaviors:
- Listens on port `40443`, SSL only — no insecure port
- `/ws/` paths are proxied with WebSocket upgrade headers and a 24-hour read timeout
- All other paths are proxied to the Django container at `django:8000`
- Sets `X-Forwarded-Proto: https` so Django knows the connection is secure

---

### `django/`

**`django/Dockerfile`**
Multi-stage-friendly Python 3.12-slim image. Installs system deps (`libpq-dev`, `gcc`) for psycopg2, installs Python packages from `requirements.txt`, copies source, and runs Daphne as the entrypoint via `entrypoint.sh`.

**`django/entrypoint.sh`**
Runs `manage.py collectstatic --noinput` before starting Daphne so static files are always up to date when the container starts. WhiteNoise then serves them directly from Django.

**`django/requirements.txt`**
Pinned package ranges for the full Django stack:

| Package | Purpose |
|---------|---------|
| `Django` | Web framework |
| `djangorestframework` | REST API support |
| `django-environ` | Reads `.env` values into Django settings |
| `channels` | WebSocket and async protocol support (official Django project) |
| `channels-redis` | Redis-backed channel layer for WebSocket routing (official Django project) |
| `daphne` | ASGI server — handles HTTP and WebSocket in one process (official Django project) |
| `psycopg2-binary` | PostgreSQL driver |
| `whitenoise` | Static file serving directly from Django |
| `redis` | Python Redis client (used by channels-redis) |

---

### `django/src/`

**`manage.py`**
Standard Django management script. Defaults to `game_mvc.settings.production`; override with `DJANGO_SETTINGS_MODULE` env var for local development.

**`apps/`**
Empty directory (tracked via `.gitkeep`) where game apps live. Each app created by `make new-app NAME=<name>` appears here as `apps/<name>/`.

---

### `django/src/game_mvc/`

The Django project package.

**`settings/base.py`**
Core settings shared by all environments. Reads all secrets and config from environment variables via `django-environ`. Key configuration:
- PostgreSQL database (host `postgres`, credentials from env)
- Redis channel layer (host `redis`)
- WhiteNoise static file serving with compressed manifests
- Django REST Framework with session authentication
- `SITE_TITLE` setting read from env and made available in all templates via context processor
- `INSTALLED_APPS` has a commented block showing where to add game apps

**`settings/production.py`**
Extends `base.py` for production use. Sets `DEBUG=False`, locks `ALLOWED_HOSTS` to the configured domain, sets `SECURE_PROXY_SSL_HEADER` so Django recognizes the nginx SSL termination, and enables secure cookie flags.

**`settings/local.py`**
Extends `base.py` for local development without Docker. Sets `DEBUG=True`, opens `ALLOWED_HOSTS`, and uses Django Channels' `InMemoryChannelLayer` so WebSockets work without a Redis container.

**`asgi.py`**
ASGI application entry point. Wires the Channels `ProtocolTypeRouter` to route HTTP traffic to Django and WebSocket traffic through `AuthMiddlewareStack` to the URL patterns defined in `routing.py`. WebSocket connections automatically have the session user available.

**`routing.py`**
Central registry for WebSocket URL patterns. Add a `path()` entry here for each game app's WebSocket consumer. Kept separate from `asgi.py` so game apps have a clean place to register routes without editing core infrastructure files.

**`urls.py`**
Project URL configuration. Includes:
- `admin/` — Django admin
- `accounts/` — Django's built-in auth views (login, logout, password change/reset)
- `api/auth/` — DRF's browseable API login/logout
- Commented examples showing how to add game app URL includes

**`context_processors.py`**
Injects `SITE_TITLE` into every template context so it's available in `base.html` and all templates that extend it without passing it manually in every view.

**`wsgi.py`**
WSGI entry point included for completeness. Not used in production (Daphne runs as ASGI), but available for tooling that expects it.

---

### `django/src/templates/`

Project-level templates that override Django's defaults. App-specific templates live inside each app's own `templates/` directory.

**`base.html`**
Minimal base template. Defines `{% block title %}`, `{% block head %}`, and `{% block content %}`. Renders Django messages (success/error flash messages) automatically. All game and auth templates should extend this.

**`registration/login.html`**
Overrides Django's default login page. Extends `base.html`. Replace the contents with your own design — Django's login view will use this template automatically.

Django's other auth templates (logout confirmation, password change, password reset) can be added to `registration/` to customize those pages as well.

---

### `ssl/`

Gitignored directory for TLS certificate files. The `.gitignore` inside excludes `*.crt`, `*.key`, and `*.pem` while keeping itself tracked.

Place two files here before running `make start`:

```
ssl/<cert-name>.crt   ← full certificate chain
ssl/<cert-name>.key   ← private key
```

The cert name is set in `.env` as `TLS_CERT_NAME` and prompted for during `make init`.

---

### `scripts/`

**`scripts/init.py`**
Interactive setup wizard. Prompts for all configuration values, auto-generates strong random passwords and Django secret keys, and writes `.env`. Re-run safely at any time — existing values are shown as defaults.

**`scripts/check_secrets.py`**
Pre-start validation guard. Checks that `.env` exists and contains all required keys, and that both SSL cert files are present. Called automatically by `make start` and `make setup`. Exits non-zero with a clear error message if anything is missing, blocking the containers from starting in a broken state.

---

## Architecture

```
Browser
  │
  │ HTTPS :40443
  ▼
┌─────────────────────────────────────────────────┐
│ nginx:alpine                                    │
│  • SSL termination                              │
│  • /ws/ → WebSocket proxy (24hr timeout)        │
│  • everything else → Django proxy               │
└─────────────────┬───────────────────────────────┘
                  │ HTTP :8000
                  ▼
┌─────────────────────────────────────────────────┐
│ python:3.12-slim  (Daphne ASGI)                 │
│  • Django 5 + Django REST Framework             │
│  • Django Channels (WebSocket support)          │
│  • WhiteNoise (static files)                    │
│  • apps/ (one Django app per game)              │
└────────┬─────────────────────────┬──────────────┘
         │                         │
         ▼                         ▼
┌────────────────┐       ┌──────────────────────┐
│ postgres:16    │       │ redis:7               │
│ (pgdata vol.)  │       │ (channel layer)       │
└────────────────┘       └──────────────────────┘
```

All four containers run on a Docker Compose managed network. Services address each other by container name (`postgres`, `redis`, `django`). Only nginx is exposed to the host, on port `40443`.
