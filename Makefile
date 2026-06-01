# game-mvc — unified Makefile
#
# Quick start:
#   make setup    — interactive first-time setup + build + start

-include .env

DOCKER_COMPOSE  := docker compose
COMPOSE_PROJECT := game-mvc
PROJECT_DIR     := $(shell pwd)

.PHONY: setup init build start stop restart logs shell \
        migrate makemigrations createsuperuser gen-certs check-secrets \
        new-app _nginx-conf help

# ---------------------------------------------------------------------------
# First-time setup
# ---------------------------------------------------------------------------

## setup: wizard + build + start (single command for a fresh install)
setup: init check-secrets _nginx-conf build start
	@echo ""
	@echo "game-mvc is running at https://$(DOMAIN):$(HOST_PORT)"

## init: wizard only — prompts for config, writes .env
init:
	python3 scripts/init.py

# ---------------------------------------------------------------------------
# nginx config generation
# ---------------------------------------------------------------------------

_nginx-conf: nginx/conf/default.conf

nginx/conf/default.conf: nginx/conf/default.conf.template .env
	@set -a && . ./.env && set +a && \
	    envsubst '$$TLS_CERT_NAME $$DOMAIN' < $< > $@
	@echo "Generated nginx/conf/default.conf"

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

## build: build Docker images
build:
	$(DOCKER_COMPOSE) build --no-cache

## start: start all containers
start: check-secrets _nginx-conf
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) up -d

## stop: stop all containers
stop:
	-$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) down
	-$(DOCKER_COMPOSE) down

## restart: stop + start
restart: stop start

## logs: follow all container logs
logs:
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) logs -f

# ---------------------------------------------------------------------------
# Django management
# ---------------------------------------------------------------------------

## shell: Django shell inside the container
shell:
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) \
	    exec django python manage.py shell

## migrate: run database migrations
migrate:
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) \
	    exec django python manage.py migrate

## makemigrations: make migrations (APP=<name> optional)
makemigrations:
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) \
	    exec django python manage.py makemigrations $(APP)

## createsuperuser: create a Django admin superuser
createsuperuser:
	$(DOCKER_COMPOSE) --project-name $(COMPOSE_PROJECT) \
	    exec django python manage.py createsuperuser

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

## check-secrets: verify .env and cert files exist before allowing start
check-secrets:
	@python3 scripts/check_secrets.py

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
	@echo "  logs                   Follow all container logs"
	@echo ""
	@echo "Django:"
	@echo "  shell                  Django shell in the container"
	@echo "  migrate                Run database migrations"
	@echo "  makemigrations         Make migrations (APP=<name> optional)"
	@echo "  createsuperuser        Create a Django admin superuser"
	@echo ""
	@echo "Games:"
	@echo "  new-app NAME=<name>    Scaffold a new game app in apps/"
	@echo ""
	@echo "SSL:"
	@echo "  gen-certs              Generate self-signed test certs via OpenSSL"
	@echo "  check-secrets          Verify .env and cert files exist"
