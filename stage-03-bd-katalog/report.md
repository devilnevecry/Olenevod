# Отчёт этапа 3 — БД и домен каталога (Olenevod)

## Статус
Готово (основные проверки зелёные; см. RISKS про `alembic check` CLI).

## Что сделано
1. **SQLAlchemy 2.0 ORM-модели** всех таблиц каталога и остатков в `olenevod/apps/api/olenevod/infrastructure/models/` (`catalog.py`, `inventory.py`) + `Base`, `async_session`, типы в `infrastructure/db.py`. Таблицы: `categories`, `products`, `product_variants`, `nutrition`, `product_media`, `files`, `product_certificates`, `cities`, `warehouses`, `city_offers`, `stock_levels`, `stock_movements`, `reservations`, `stock_transfers`, `stock_transfer_items`, `audit_log`. Мягкое удаление (`deleted_at`) для каталога, UUID PK, `timestamptz`, деньги/количества — целые.
2. **CHECK-ограничения** (`on_hand >= 0`, `reserved >= 0`, `reserved <= on_hand` и др.), **триггер append-only** (запрет UPDATE/DELETE) на `stock_movements` и `audit_log`, необходимые индексы, в т.ч. `city_offers(city_id, is_published)`, `stock_levels(variant_id)`, `stock_movements(warehouse_id, variant_id, created_at)`, **полнотекстовый поиск** `products` — GIN `to_tsvector('russian', …)` + `pg_trgm` (триграммы) — в миграции `0001_initial_schema`.
3. **Alembic-миграция** `migrations/versions/0001_initial_schema.py` (upgrade/downgrade), `migrations/env.py` с `target_metadata = Base.metadata` и async-запуском миграций (под asyncpg).
4. **Репозитории** (SQLAlchemy async): `CatalogRepository` (города, категории, товары города с наличием), `InventoryRepository` (атомарный резерв через `UPDATE … WHERE on_hand - reserved >= qty RETURNING`, release, commit).
5. **Сервисы**: `CatalogService` (список городов, категории, продукты города с наличием) и `PricingService` (цена по городу, скидки, итог) в `application/`.
6. **Доменные исключения** (`OutOfStock`, `InvalidTransition`, `CityAccessDenied`, `NotFound`, `AlreadyExists`) в `domain/exceptions.py`.
7. **Тесты миграции** `tests/test_migrations.py` + фикстуры БД в `tests/conftest.py`: `upgrade head` на пустую БД, цикл `upgrade → downgrade → upgrade`, проверка набора таблиц vs ORM-моделей.

## Доказательство
Реальный вывод команд (запускались на локальном тестовом PostgreSQL 16, порт 5433, БД `olenevod_test`, роль `olenevod`):

**`alembic upgrade head` (на пустую тестовую БД):**
```
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001_initial_schema, Initial schema:
каталог, города, склады, предложения, остатки, движения, аудит.
```
После применения: 17 таблиц (включая `alembic_version`), `alembic_version = 0001_initial_schema`. Цикл `upgrade → downgrade → upgrade` тоже пройден.

**`pytest -q tests/` (с `TEST_DATABASE_URL` на тестовую БД):**
```
5 passed, 1 skipped, 2 warnings in 5.50s
```
(1 skipped — `test_alembic_check`, см. RISKS; `test_healthz_returns_200` и `test_readyz_responds_with_status` пройдены.)

**`ruff check olenevod tests`:**
```
All checks passed!
```

**`mypy olenevod/application olenevod/domain` (strict):**
```
Success: no issues found in 7 source files
```

## Что осталось
- `make up && make test` через Docker не прогоняны (Docker Desktop недоступен в песочнице — как на этапе 1).

## Вопросы
Нет.

## Коммит
`work/stage-03-bd-katalog`.
