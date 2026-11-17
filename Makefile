# Olenevod â€” Makefile (ÑÑ‚Ð°Ð¿ 1 ÐºÐ°Ñ€ÐºÐ°ÑÐ°).
# Ð¦ÐµÐ»Ð¸: up, down, migrate, seed, test, test-e2e, lint, typecheck, audit,
#       release-check, backup-verify, perf
#
# Ð ÐµÑ†ÐµÐ¿Ñ‚Ñ‹ Ð²Ñ‹Ð¿Ð¾Ð»Ð½ÑÑŽÑ‚ÑÑ Ð¾Ð±Ð¾Ð»Ð¾Ñ‡ÐºÐ¾Ð¹ ÑÐ¸ÑÑ‚ÐµÐ¼Ñ‹ (cmd.exe Ð½Ð° Windows), Ð¿Ð¾ÑÑ‚Ð¾Ð¼Ñƒ
# Ñ†ÐµÐ¿Ð¾Ñ‡ÐºÐ¸ ÐºÐ¾Ð¼Ð°Ð½Ð´ Ð¿Ð¸ÑˆÑƒÑ‚ÑÑ Ñ‡ÐµÑ€ÐµÐ· && Ð² Ð¾Ð´Ð½Ð¾Ð¹ Ð»Ð¾Ð³Ð¸Ñ‡ÐµÑÐºÐ¾Ð¹ ÑÑ‚Ñ€Ð¾ÐºÐµ.

COMPOSE   ?= docker compose
COMPOSE_FILE ?= -f olenevod/infra/docker-compose.yml
API_DIR   := olenevod/apps/api
WEB_DIR   := olenevod/apps/web
ADMIN_DIR := olenevod/apps/admin
API_PORT  ?= 8000

.PHONY: help up down migrate seed test test-e2e lint typecheck audit release-check backup-verify perf ci

help:
	@echo "Ð”Ð¾ÑÑ‚ÑƒÐ¿Ð½Ñ‹Ðµ Ñ†ÐµÐ»Ð¸: up down migrate seed test test-e2e lint typecheck audit release-check backup-verify perf"

# .env Ð¸Ð· .env.example, ÐµÑÐ»Ð¸ ÐµÑ‰Ñ‘ Ð½Ðµ ÑÐ¾Ð·Ð´Ð°Ð½
.env: .env.example
	@if not exist .env copy .env.example .env >nul

# --- Ð¸Ð½Ñ„Ñ€Ð°ÑÑ‚Ñ€ÑƒÐºÑ‚ÑƒÑ€Ð° ---

up: .env
	$(COMPOSE) $(COMPOSE_FILE) --profile dev up -d
	$(MAKE) migrate
	@echo "up: ÑÐµÑ€Ð²Ð¸ÑÑ‹ Ð·Ð°Ð¿ÑƒÑ‰ÐµÐ½Ñ‹, Ð¼Ð¸Ð³Ñ€Ð°Ñ†Ð¸Ð¸ Ð¿Ñ€Ð¸Ð¼ÐµÐ½ÐµÐ½Ñ‹."
	@echo "  healthz: http://localhost:$(API_PORT)/healthz"
	@echo "  readyz:  http://localhost:$(API_PORT)/readyz"

down:
	$(COMPOSE) $(COMPOSE_FILE) down -v

migrate:
	$(COMPOSE) $(COMPOSE_FILE) --profile dev run --rm api alembic upgrade head

seed:
	@echo "seed: Ð½Ð°Ð±Ð¾Ñ€ Ð´ÐµÐ¼Ð¾-Ð´Ð°Ð½Ð½Ñ‹Ñ… Ð·Ð°Ð¿Ð¾Ð»Ð½ÑÐµÑ‚ÑÑ ÑÑ‚Ð°Ð¿Ð¾Ð¼ 6 (ÑÐ¼. docs/DEMO_DATA_SPEC.md)"

# --- Ñ‚ÐµÑÑ‚Ñ‹ ---

test:
	$(COMPOSE) $(COMPOSE_FILE) --profile test up -d
	$(COMPOSE) $(COMPOSE_FILE) --profile test run --rm -T api pytest -q
	$(COMPOSE) $(COMPOSE_FILE) --profile test down -v

test-e2e:
	@echo "test-e2e: Playwright ÑÑ†ÐµÐ½Ð°Ñ€Ð¸Ð¸ (ÑÑ‚Ð°Ð¿ 7+), Ð¿Ð¾ÐºÐ° Ð¿ÑƒÑÑ‚Ð¾"

# --- ÐºÐ°Ñ‡ÐµÑÑ‚Ð²Ð¾ ÐºÐ¾Ð´Ð° ---

lint:
	cd $(API_DIR) && python -m ruff check olenevod tests
	cd $(WEB_DIR) && npx eslint .
	cd $(ADMIN_DIR) && npx eslint .

typecheck:
	cd $(API_DIR) && python -m mypy olenevod/application olenevod/domain
	cd $(WEB_DIR) && npx tsc --noEmit
	cd $(ADMIN_DIR) && npx tsc --noEmit

audit:
	cd $(API_DIR) && python -m pip_audit || true
	cd $(WEB_DIR) && npm audit --omit=dev || true
	cd $(ADMIN_DIR) && npm audit --omit=dev || true

release-check:
	@if "$(APP_MODE)"=="production" (echo "release-check: PRODUCTION â€” Ð¿ÑƒÐ±Ð»Ð¸ÐºÐ°Ñ†Ð¸Ñ Ð±Ð»Ð¾ÐºÐ¸Ñ€ÑƒÐµÑ‚ÑÑ Ð´Ð¾ Ð²Ð½ÐµÑÐµÐ½Ð¸Ñ Ñ€ÐµÐºÐ²Ð¸Ð·Ð¸Ñ‚Ð¾Ð² Ð²Ð»Ð°Ð´ÐµÐ»ÑŒÑ†Ð°" & exit /b 1) else (echo "release-check: APP_MODE=demo â€” Ð¾Ð³Ñ€Ð°Ð½Ð¸Ñ‡ÐµÐ½Ð¸Ð¹ Ð½ÐµÑ‚")

backup-verify:
	@echo "backup-verify: pg_dump + Ð¿Ñ€Ð¾Ð²ÐµÑ€ÐºÐ° Ð²Ð¾ÑÑÑ‚Ð°Ð½Ð¾Ð²Ð»ÐµÐ½Ð¸Ñ (ÑÑ‚Ð°Ð¿ 11)"

perf:
	@echo "perf: Ð½Ð°Ð³Ñ€ÑƒÐ·Ð¾Ñ‡Ð½Ð¾Ðµ Ñ‚ÐµÑÑ‚Ð¸Ñ€Ð¾Ð²Ð°Ð½Ð¸Ðµ k6/Locust (ÑÑ‚Ð°Ð¿ 16)"

# --- CI-Ð°Ð½Ð°Ð»Ð¾Ð³ ---

ci: lint typecheck test

