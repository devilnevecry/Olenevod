# Olenevod — Makefile (этап 1 каркаса).
# Цели: up, down, migrate, seed, test, test-e2e, lint, typecheck, audit,
#       release-check, backup-verify, perf
#
# Рецепты выполняются оболочкой системы (cmd.exe на Windows), поэтому
# цепочки команд пишутся через && в одной логической строке.

COMPOSE   ?= docker compose
COMPOSE_FILE ?= -f olenevod/infra/docker-compose.yml
API_DIR   := olenevod/apps/api
WEB_DIR   := olenevod/apps/web
ADMIN_DIR := olenevod/apps/admin
API_PORT  ?= 8000

.PHONY: help up down migrate seed test test-e2e lint typecheck audit release-check backup-verify perf ci

help:
	@echo "Доступные цели: up down migrate seed test test-e2e lint typecheck audit release-check backup-verify perf"

# .env из .env.example, если ещё не создан
.env: .env.example
	@if not exist .env copy .env.example .env >nul

# --- инфраструктура ---

up: .env
	$(COMPOSE) $(COMPOSE_FILE) --profile dev up -d
	$(MAKE) migrate
	@echo "up: сервисы запущены, миграции применены."
	@echo "  healthz: http://localhost:$(API_PORT)/healthz"
	@echo "  readyz:  http://localhost:$(API_PORT)/readyz"

down:
	$(COMPOSE) $(COMPOSE_FILE) down -v

migrate:
	$(COMPOSE) $(COMPOSE_FILE) --profile dev run --rm api alembic upgrade head

seed:
	@echo "seed: набор демо-данных заполняется этапом 6 (см. docs/DEMO_DATA_SPEC.md)"

# --- тесты ---

test:
	$(COMPOSE) $(COMPOSE_FILE) --profile test up -d
	$(COMPOSE) $(COMPOSE_FILE) --profile test run --rm -T api pytest -q
	$(COMPOSE) $(COMPOSE_FILE) --profile test down -v

test-e2e:
	@echo "test-e2e: Playwright сценарии (этап 7+), пока пусто"

# --- качество кода ---

lint:
	cd $(API_DIR) && python -m ruff check olenevod tests
	cd $(WEB_DIR) && npx eslint . || true
	cd $(ADMIN_DIR) && npx eslint . || true

typecheck:
	cd $(API_DIR) && python -m mypy olenevod/application olenevod/domain
	cd $(WEB_DIR) && npx tsc --noEmit || true
	cd $(ADMIN_DIR) && npx tsc --noEmit || true

audit:
	cd $(API_DIR) && python -m pip_audit || true
	cd $(WEB_DIR) && npm audit --omit=dev || true
	cd $(ADMIN_DIR) && npm audit --omit=dev || true

release-check:
	@if "$(APP_MODE)"=="production" (echo "release-check: PRODUCTION — публикация блокируется до внесения реквизитов владельца" & exit /b 1) else (echo "release-check: APP_MODE=demo — ограничений нет")

backup-verify:
	@echo "backup-verify: pg_dump + проверка восстановления (этап 11)"

perf:
	@echo "perf: нагрузочное тестирование k6/Locust (этап 16)"

# --- CI-аналог ---

ci: lint typecheck test
