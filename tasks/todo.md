# tasks/todo.md — Этап 1: каркас монорепо

- [x] Структура папок монорепо (olenevod/apps/{api,web,admin}, packages/{design-tokens,ui,motion,api-client}, brand/, seeds/, infra/, e2e/)
- [x] .env.example с переменными окружения (без реальных значений)
- [x] Docker Compose профили dev/test/prod в olenevod/infra/
- [x] Makefile с целями up/down/migrate/seed/test/test-e2e/lint/typecheck/audit/release-check/backup-verify/perf
- [x] Линтеры/форматтеры: ruff, mypy strict (domain/application), eslint, tsc strict, pre-commit
- [x] Эндпоинты healthz (liveness) и readyz (БД, Redis, миграции) в FastAPI
- [x] CI-скрипт локально (.github/workflows/ci.yml)
- [ ] make up — не 실행 в этой среде: демон Docker недоступен (com.docker.service не стартует, WSL-дистрибутив docker-desktop останавливается)
- [ ] make test — не 실행 через Docker (то же ограничение); pytest пройден локально (2 теста: healthz 200, readyz отвечает)
