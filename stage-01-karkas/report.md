# Отчёт этапа 1 — каркас монорепо Olenevod

## Статус
Частично — структура и линтеры готовы, Docker-проверка отложена (среда без Docker).

## Что сделано
1. **Структура папок**: `olenevod/apps/{api,web,admin}`, `olenevod/packages/{design-tokens,ui,motion,api-client}`, `olenevod/brand/`, `olenevod/seeds/`, `olenevod/infra/`, `olenevod/e2e/`, `tasks/todo.md` — по `ARCHITECTURE.md §2`.
2. **`.env.example`**: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `BOT_TOKEN_*`, `SMTP_*`, `PAYMENT_PROVIDER_*`, `YANDEX_METRIKA_ID`, `APP_MODE=demo` и др. — без реальных значений; непунктуальные реквизиты помечены `TODO_OWNER`.
3. **Docker Compose** (`olenevod/infra/docker-compose.yml`): профили `dev` / `test` / `prod`; сервисы `postgres:16`, `redis:7`, `api`, `web`, `admin`, `bots`, `worker`, `caddy`; `Caddyfile`.
4. **Makefile**: цели `up`, `down`, `migrate`, `seed`, `test`, `test-e2e`, `lint`, `typecheck`, `audit`, `release-check`, `backup-verify`, `perf`, `ci`.
5. **Линтеры/форматтеры**: `ruff` (pyproject), `mypy --strict` для `domain`/`application`, `eslint`, `tsc --strict` (web/admin), `.pre-commit-config.yaml` (ruff + mypy).
6. **FastAPI эндпоинты**: `GET /healthz` (liveness, 200) и `GET /readyz` (БД + Redis + миграции; 200 если готово, иначе 503) в `olenevod/apps/api/olenevod/interfaces/http/health.py`.
7. **CI-скрипт**: `.github/workflows/ci.yml` (lint / typecheck / test на PostgreSQL 16 + Redis 7).
8. **Тесты**: `olenevod/apps/api/tests/test_health.py` — `/healthz` → 200, `/readyz` отвечает (200 при доступных зависимостях, 503 без них).

## Проверено локально
- Приложение импортируется (`from olenevod.main import app`).
- `.venv\Scripts\python.exe -m pytest -q tests/test_health.py` → 2 passed.
- `ruff check olenevod tests` → All checks passed.
- `mypy olenevod/application olenevod/domain` → Success.
- `make help`: Makefile парсится, цели отображаются.

## Не получилось
`make up` и `make test` через Docker не прогнаны — Docker Desktop недоступен в песочнице (служба `com.docker.service` не стартует, WSL-дистрибутив `docker-desktop` останавливается). Критерий готовности требует машины с Docker.

## Коммит
`work/stage-01-karkas` — `feat: этап 1 каркас монорепо (Docker Compose, Makefile, линтеры, healthz/readyz)`.

## Что осталось
- Запустить `make up && make test` на машине с Docker (критерий готовности этапа 1).
- Этап 2: бренд и дизайн-система (токены, шрифты, `packages/ui`, логотип).

## Вопросы
Нет.
