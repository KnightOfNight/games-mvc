# game-mvc — unified Makefile
#
# Quick start:
#   make setup    — interactive first-time setup + build + start

-include .env

DOCKER_COMPOSE  := docker compose
COMPOSE_PROJECT := game-mvc
PROJECT_DIR     := $(shell pwd)

# The production Docker daemon. Owned by deploy-prod, which pins it per
# command — this value is never exported ambiently and nothing else uses it.
PROD_DOCKER_HOST := ssh://ec2-user@games.magrathea.com

# Build-exhaust sweep caps (#205). Every build orphans image layers and leaves
# BuildKit cache entries behind; unswept, prod's root volume grows ~500MB per
# release and Emma's dev VM ~2GB per build. Eviction is capped rather than a
# full prune — a conservative bound that is free: `build` runs `docker compose
# build --no-cache` by design, so no build reads this cache and the cap costs
# nothing in build time either way. The -a prohibition that IS load-bearing is
# on the image prune above, which stays dangling-only so tagged base images are
# never deleted and re-pulled.
# The flag name diverges by daemon version: --keep-storage was
# renamed --reserved-space in Docker 28. Prod runs Docker Engine 25.0.16
# (linux/arm64); Emma's dev daemon runs 29.6.2-rd.
PROD_BUILDER_PRUNE_FLAGS := --keep-storage 5GB
DEV_BUILDER_PRUNE_FLAGS  := --reserved-space 5GB

GDD_MAJOR := 24
GDD_SECTIONS := docs/shyland/gdd/_00_header.md \
                docs/shyland/gdd/_01_version_history.md \
                docs/shyland/gdd/_02_table_of_contents.md \
                docs/shyland/gdd/section_01_vision_and_pillars.md \
                docs/shyland/gdd/section_02_world_model.md \
                docs/shyland/gdd/section_03_character_system.md \
                docs/shyland/gdd/section_04_the_three_bars.md \
                docs/shyland/gdd/section_05_combat_system.md \
                docs/shyland/gdd/section_06_economy_and_items.md \
                docs/shyland/gdd/section_07_social_systems.md \
                docs/shyland/gdd/section_08_quest_and_narrative.md \
                docs/shyland/gdd/section_09_player_command_reference.md \
                docs/shyland/gdd/section_10_technical_architecture.md \
                docs/shyland/gdd/section_11_admin_and_content_tools.md \
                docs/shyland/gdd/section_12_future_systems.md

.PHONY: setup init build start stop restart nuke logs tick-logs shell \
        migrate makemigrations createsuperuser gen-certs check-secrets \
        new-app push-certs seed gdd help require-local crosscheck-env hooks \
        deploy-dev deploy-prod seed-prod verify verify-prod

# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

# Prerequisite guard: add `require-local` to any target that must never run
# against a remote daemon. Catches DOCKER_HOST from the environment and from
# the included .env alike.
require-local:
	@test -z "$(DOCKER_HOST)" || (echo "ERROR: DOCKER_HOST is set ($(DOCKER_HOST)) — this target is local-only. Refusing to run against a remote daemon." && exit 1)

# Prerequisite guard: verify .env matches the deployment target implied by
# DOCKER_HOST before any daemon-touching operation runs. Standing rule:
# DOCKER_HOST set — any value — means PRODUCTION, so .env must be identical
# to .env.prod; unset means the local dev daemon, so .env must be identical
# to .env.dev. Expand this guard before ever pointing DOCKER_HOST at a
# non-production remote host.
crosscheck-env:
	@if [ -n "$(DOCKER_HOST)" ]; then \
	    test -s .env.prod || { echo "ERROR: .env.prod missing or empty."; exit 1; }; \
	    cmp -s .env .env.prod || { echo "ERROR: DOCKER_HOST is set — target is PRODUCTION — but .env does not match .env.prod."; exit 1; }; \
	    echo "crosscheck-env: PRODUCTION posture OK (.env == .env.prod, DOCKER_HOST=$(DOCKER_HOST))"; \
	else \
	    test -s .env.dev || { echo "ERROR: .env.dev missing or empty."; exit 1; }; \
	    cmp -s .env .env.dev || { echo "ERROR: DOCKER_HOST is unset — target is local dev — but .env does not match .env.dev."; exit 1; }; \
	    echo "crosscheck-env: dev posture OK (.env == .env.dev)"; \
	fi

# ---------------------------------------------------------------------------
# First-time setup
#
# There is no one-button bootstrap anymore, and there isn't going to be one.
# These are real servers now, with real data, and the last thing anyone needs
# is a make target cheerfully rebuilding production because somebody was in
# the wrong terminal. Standing up a fleet is a deliberate, manual, eyes-open
# procedure — wizard, certs, build, migrate, seed, superuser — typed one
# command at a time by a human who read the output and can be blamed
# afterward. The guards below will catch the common accidents. They will not
# catch ambition.
# ---------------------------------------------------------------------------

## setup: wizard + build + start (single command for a fresh install)
setup: init check-secrets push-certs build start
	@echo ""
	@echo "game-mvc is running at https://$(DOMAIN):$(HOST_PORT)"

## init: wizard only — prompts for config, writes .env
init:
	python3 scripts/init.py

## hooks: activate the committed git hooks (one-time per clone)
hooks:
	git config core.hooksPath scripts/git-hooks
	@echo "git core.hooksPath -> scripts/git-hooks (worktrees now auto-initialize env files)"

# ---------------------------------------------------------------------------
# SSL certs
# ---------------------------------------------------------------------------

## push-certs: upload local ssl/ certs into the Docker ssl volume (works with DOCKER_HOST)
push-certs: crosscheck-env
	@test -n "$(TLS_CERT_NAME)" || (echo "Run 'make init' first to set TLS_CERT_NAME" && exit 1)
	docker run -d --name ssl-tmp -v $(COMPOSE_PROJECT)_ssldata:/ssl alpine tail -f /dev/null
	docker cp ssl/. ssl-tmp:/ssl/
	docker rm -f ssl-tmp
	@echo "SSL certs pushed to volume $(COMPOSE_PROJECT)_ssldata"

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

## build: build Docker images and recreate containers
build: crosscheck-env check-secrets
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) build --no-cache
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) up -d --force-recreate

## start: start all containers
start: crosscheck-env check-secrets
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) up -d

## stop: stop all containers
stop:
	-$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) down
	-$(DOCKER_COMPOSE) down

## restart: stop + start
restart: stop start

## nuke: remove all containers, volumes, and images for this project (local daemon only)
nuke: require-local
	-$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) down -v
	-docker volume rm $(COMPOSE_PROJECT)_ssldata
	-docker rmi shyland-django $(COMPOSE_PROJECT)-nginx

## logs: follow all container logs
logs:
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) logs -f

## tick-logs: follow ticker container logs only
tick-logs:
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) logs -f ticker

# ---------------------------------------------------------------------------
# Deployment
#
# The targets in this section are the only things in this Makefile permitted
# to set the posture (.env) — declaring the target IS the deliberate act.
# Everything else checks and stops.
# ---------------------------------------------------------------------------

## deploy-dev: deploy current source to the local dev stack (build + migrate)
deploy-dev: require-local
	@test -s .env.dev || (echo "ERROR: .env.dev missing or empty." && exit 1)
	cp .env.dev .env
	python3 scripts/check_docker_host.py
	$(MAKE) build
	$(MAKE) migrate
	-docker image prune -f
	-docker builder prune -f $(DEV_BUILDER_PRUNE_FLAGS)
	@echo "deploy-dev complete — local dev stack refreshed, build exhaust swept."

## deploy-prod: operator-authorized production deploy — flips posture, deploys, restores
# Pins its own DOCKER_HOST; refuses to run if one is already in the
# environment (nothing should be ambient anymore — a set DOCKER_HOST here
# means stale state, and stale state gets investigated, not inherited).
# If this fails partway, .env deliberately REMAINS in prod posture: a
# half-finished production deploy needs a human, and the guards will block
# all dev work until the posture is restored by hand (cp .env.dev .env).
# The build-exhaust sweep (#205) runs LAST, after the posture restore, and is
# non-fatal. Both prunes pin their own DOCKER_HOST and neither reads .env, so
# posture is irrelevant to them — running them after the restore means not even
# an operator Ctrl-C during a long prune can strand production posture.
deploy-prod:
	@test -z "$(DOCKER_HOST)" || (echo "ERROR: DOCKER_HOST is already set ($(DOCKER_HOST)). deploy-prod pins its own target; investigate why it is set, unset it, and retry." && exit 1)
	@test -s .env.prod || (echo "ERROR: .env.prod missing or empty." && exit 1)
	@test -s .env.dev || (echo "ERROR: .env.dev missing or empty — deploy-prod needs it to restore the resting posture." && exit 1)
	cp .env.prod .env
	DOCKER_HOST=$(PROD_DOCKER_HOST) python3 scripts/check_docker_host.py
	DOCKER_HOST=$(PROD_DOCKER_HOST) $(MAKE) build
	DOCKER_HOST=$(PROD_DOCKER_HOST) $(MAKE) migrate
	cp .env.dev .env
	-DOCKER_HOST=$(PROD_DOCKER_HOST) docker image prune -f
	-DOCKER_HOST=$(PROD_DOCKER_HOST) docker builder prune -f $(PROD_BUILDER_PRUNE_FLAGS)
	@echo "deploy-prod complete — production deployed, build exhaust swept, resting posture restored (.env == .env.dev)."

## seed-prod: operator-authorized production seed — flips posture, seeds, restores
# Same contract as the production deploy target: pins its own DOCKER_HOST,
# refuses an ambient one, and if it fails partway .env deliberately REMAINS
# in prod posture for a human. Exists so closeout tails have a sanctioned
# path for deploy-time data actions (#187 — the V24.2 hiccup: no such path
# existed after the deploy target restored resting posture).
seed-prod:
	@test -z "$(DOCKER_HOST)" || (echo "ERROR: DOCKER_HOST is already set ($(DOCKER_HOST)). seed-prod pins its own target; investigate why it is set, unset it, and retry." && exit 1)
	@test -s .env.prod || (echo "ERROR: .env.prod missing or empty." && exit 1)
	@test -s .env.dev || (echo "ERROR: .env.dev missing or empty — seed-prod needs it to restore the resting posture." && exit 1)
	cp .env.prod .env
	DOCKER_HOST=$(PROD_DOCKER_HOST) python3 scripts/check_docker_host.py
	DOCKER_HOST=$(PROD_DOCKER_HOST) $(MAKE) seed
	cp .env.dev .env
	@echo "seed-prod complete — production reseeded, resting posture restored (.env == .env.dev)."

## verify-prod: operator-authorized read-only production verification — flips posture, runs one verify_* command, restores
# Same contract as the other two posture-setting targets: pins its own
# DOCKER_HOST, refuses an ambient one, and if it fails partway .env
# deliberately REMAINS in prod posture for a human. Exists so closeout
# tails can run a brief's read-only prod verification step (#248/#249 —
# the read-only twin of #187). Runs ONLY a manage.py command in the
# verify_* family, one per invocation; the commands themselves are
# brief-shipped, dev-tested code and reach production via release
# deploys — this target has nothing to run until the first one ships.
# The VERIFY gates run BEFORE the posture flip: a bad invocation never
# leaves resting posture.
verify-prod:
	@test -n "$(VERIFY)" || (echo "ERROR: usage: make verify-prod VERIFY=verify_<name> — names a brief-shipped manage.py verification command (#249)." && exit 1)
	@case "$(VERIFY)" in verify_*) ;; *) echo "ERROR: VERIFY must name a verify_* management command (read-only verification family, #249)."; exit 1;; esac
	@test -z "$(DOCKER_HOST)" || (echo "ERROR: DOCKER_HOST is already set ($(DOCKER_HOST)). verify-prod pins its own target; investigate why it is set, unset it, and retry." && exit 1)
	@test -s .env.prod || (echo "ERROR: .env.prod missing or empty." && exit 1)
	@test -s .env.dev || (echo "ERROR: .env.dev missing or empty — verify-prod needs it to restore the resting posture." && exit 1)
	cp .env.prod .env
	DOCKER_HOST=$(PROD_DOCKER_HOST) python3 scripts/check_docker_host.py
	DOCKER_HOST=$(PROD_DOCKER_HOST) $(MAKE) verify VERIFY=$(VERIFY)
	cp .env.dev .env
	@echo "verify-prod complete — production verification ran read-only, resting posture restored (.env == .env.dev)."

# ---------------------------------------------------------------------------
# Django management
# ---------------------------------------------------------------------------

## shell: Django shell inside the container
shell: crosscheck-env
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) \
	    exec django python manage.py shell

## migrate: run database migrations
migrate: crosscheck-env
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) \
	    exec django python manage.py migrate

## makemigrations: make migrations (APP=<name> optional) and sync generated files to local tree
makemigrations: crosscheck-env
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) \
	    exec django python manage.py makemigrations $(APP)
	@for app in $$(ls $(PROJECT_DIR)/django/src/apps/); do \
	    $(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) \
	        cp django:/app/apps/$$app/migrations/. \
	        $(PROJECT_DIR)/django/src/apps/$$app/migrations/ 2>/dev/null || true; \
	done
	@echo "  → migrations synced to local filesystem"

## createsuperuser: create a Django admin superuser
createsuperuser: crosscheck-env
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) \
	    exec django python manage.py createsuperuser

## createuser: create a new player account and assign game group memberships
createuser:
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) \
	    exec django python manage.py createuser

# ---------------------------------------------------------------------------
# App scaffolding
# ---------------------------------------------------------------------------

## new-app NAME=<name>: scaffold a new game app in apps/
new-app:
	@test -n "$(NAME)" || (echo "Usage: make new-app NAME=<appname>" && exit 1)
	mkdir -p $(PROJECT_DIR)/django/src/apps/$(NAME)
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) run --rm \
	    -v $(PROJECT_DIR)/django/src:/app \
	    django python manage.py startapp $(NAME) apps/$(NAME)
	sed -i '' "s/name = '$(NAME)'/name = 'apps.$(NAME)'/" \
	    $(PROJECT_DIR)/django/src/apps/$(NAME)/apps.py
	printf "from django.urls import path\nfrom . import views\n\napp_name = '$(NAME)'\n\nurlpatterns = [\n]\n" \
	    > $(PROJECT_DIR)/django/src/apps/$(NAME)/urls.py
	@echo ""
	@echo "App '$(NAME)' created at django/src/apps/$(NAME)/"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Add 'apps.$(NAME)' to INSTALLED_APPS in django/src/game_mvc/settings/base.py"
	@echo "  2. Add URL patterns to django/src/game_mvc/urls.py"
	@echo "  3. Add WebSocket patterns to django/src/game_mvc/routing.py (if needed)"
	@echo "  4. Run: make makemigrations APP=$(NAME) && make migrate"

# ---------------------------------------------------------------------------
# SSL
# ---------------------------------------------------------------------------

## gen-certs: generate self-signed test certs via OpenSSL
gen-certs:
	@test -n "$(DOMAIN)" || (echo "Run 'make init' first to set DOMAIN" && exit 1)
	@test -n "$(TLS_CERT_NAME)" || (echo "Run 'make init' first to set TLS_CERT_NAME" && exit 1)
	@mkdir -p ssl
	@echo "Generating self-signed cert (10 years, CN=$(DOMAIN))..."
	openssl req -x509 -newkey rsa:4096 -sha256 -days 3650 -nodes \
	    -keyout ssl/$(TLS_CERT_NAME).key \
	    -out ssl/$(TLS_CERT_NAME).crt \
	    -subj "/CN=$(DOMAIN)" \
	    -addext "subjectAltName=DNS:$(DOMAIN)"
	@echo ""
	@echo "Generated:"
	@echo "  ssl/$(TLS_CERT_NAME).crt  (self-signed certificate)"
	@echo "  ssl/$(TLS_CERT_NAME).key  (private key)"
	@echo ""
	@echo "NOTE: Browsers will show a security warning for self-signed certs."
	@echo "      Use your vendor certs for a trusted connection."
	$(MAKE) push-certs

## seed: run seed_world to populate game world data
seed: crosscheck-env
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) \
	    exec django python manage.py seed_world

## verify: run a verify_* management command against the current target (VERIFY=verify_<name>)
# The read-only verification family (#248/#249). From resting posture this
# targets dev — the "tested on dev" path for every brief-shipped
# verification command. Production runs go through verify-prod only.
verify: crosscheck-env
	@test -n "$(VERIFY)" || (echo "ERROR: usage: make verify VERIFY=verify_<name>" && exit 1)
	@case "$(VERIFY)" in verify_*) ;; *) echo "ERROR: VERIFY must name a verify_* management command (read-only verification family, #249)."; exit 1;; esac
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) \
	    exec django python manage.py $(VERIFY)

## check-secrets: verify .env and cert files exist before allowing start
check-secrets:
	@python3 scripts/check_secrets.py

# ---------------------------------------------------------------------------
# Docs
# ---------------------------------------------------------------------------

## gdd: rebuild the monolithic GDD from the section files in docs/shyland/gdd/
gdd:
	{ printf '<!-- GENERATED FILE - DO NOT EDIT.\n     Built by `make gdd` from the section files in docs/shyland/gdd/.\n     Edit the section files; the sections are authoritative if this file ever disagrees. -->\n\n'; cat $(GDD_SECTIONS); } > docs/shyland/Shyland_GDD_v$(GDD_MAJOR).md

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

## help: list all targets
help:
	@echo "game-mvc — available make targets"
	@echo ""
	@echo "First-time setup:"
	@echo "  setup                  Wizard + build + start (fresh install)"
	@echo "  init                   Wizard only — generates .env"
	@echo ""
	@echo "Docker:"
	@echo "  build                  Build Docker images"
	@echo "  start                  Start all containers"
	@echo "  stop                   Stop all containers"
	@echo "  restart                stop + start"
	@echo "  nuke                   Remove containers, volumes, images (local daemon only)"
	@echo "  logs                   Follow all container logs"
	@echo "  tick-logs              Follow ticker container logs only"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy-dev             Deploy current source to the local dev stack (build + migrate"
	@echo "                         + exhaust sweep)"
	@echo "  deploy-prod            Operator-authorized production deploy (flips posture,"
	@echo "                         pre-flights, builds, migrates, sweeps exhaust,"
	@echo "                         restores dev posture)"
	@echo "  seed-prod              Operator-authorized production seed (same posture contract, #187)"
	@echo "  verify-prod            Operator-authorized read-only production verification"
	@echo "                         (VERIFY=verify_<name>; same posture contract, #249)"
	@echo ""
	@echo "Django:"
	@echo "  shell                  Django shell in the container"
	@echo "  migrate                Run database migrations"
	@echo "  makemigrations         Make migrations (APP=<name> optional)"
	@echo "  createsuperuser        Create a Django admin superuser"
	@echo "  seed                   Run seed_world to populate game world data"
	@echo "  verify                 Run a verify_* command against the current target (VERIFY=verify_<name>)"
	@echo ""
	@echo "Games:"
	@echo "  new-app NAME=<name>    Scaffold a new game app in apps/"
	@echo ""
	@echo "SSL:"
	@echo "  gen-certs              Generate self-signed test certs via OpenSSL"
	@echo "  push-certs             Upload local ssl/ certs into the Docker ssl volume"
	@echo "  check-secrets          Verify .env and cert files exist"
	@echo ""
	@echo "Guards (run automatically; check-only, never fix):"
	@echo "  require-local          Block when DOCKER_HOST is set (nuke)"
	@echo "  crosscheck-env         DOCKER_HOST set = production, .env must match .env.prod;"
	@echo "                         unset = local dev, .env must match .env.dev"
	@echo ""
	@echo "Setup:"
	@echo "  hooks                  Activate committed git hooks (one-time per clone)"
	@echo ""
	@echo "Docs:"
	@echo "  gdd                    Rebuild the monolithic GDD from docs/shyland/gdd/"
