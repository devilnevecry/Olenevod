# Отчёт этапа 9 — DeliveryService (Olenevod)

## Статус
Готово

## Что сделано
1. **Аlembic-миграция `0005_delivery`** (Revises: `0004_inventory`) создаёт таблицы:
   - `delivery_zones` — `id`, `city_id` (FK cities, unique), `zone_name`, `base_fee`, `per_kg_fee`, `free_from_amount`, `created_at`; CHECK-ограничения на неотрицательные суммы, индекс на `city_id`.
   - `delivery_tariffs` — `id`, `zone_id` (FK delivery_zones, unique), `name`, `estimated_days`, `is_active`, `created_at`; CHECK на `estimated_days >= 0`, индекс на `zone_id`.
2. **ORM-модели** `DeliveryZone`, `DeliveryTariff` в `olenevod/infrastructure/models/delivery.py`, зарегистрированы в `infrastructure/models/__init__.py` (попадают в `Base.metadata` для Alembic).
3. **`olenevod/application/delivery_service.py`** — класс `DeliveryService` с методом `calculate_delivery(city_id, items, total_amount) -> {fee, free_delivery, estimated_days, zone}`:
   - несуществующий город → `NotFound` (HTTP 404);
   - город без зоны доставки → `NotFound` (HTTP 404);
   - вес позиции берётся из `product_variants.pack_weight_g` (г), `fee = base_fee + per_kg_fee * ceil(weight_kg)`;
   - при `total_amount >= free_from_amount` доставка бесплатная (`fee = 0`, `free_delivery = true`);
   - `estimated_days` и `zone` из `delivery_tariffs` / `delivery_zones`.
4. **HTTP-роуты** `olenevod/interfaces/http/delivery.py` — `GET /delivery/quote?city_id=&items[]=&total_amount=` с ответом `{city_id, zone, fee, free_delivery, estimated_days}`.
5. **Роутер подключён в `olenevod/main.py`** (`app.include_router(delivery_router)`).
6. **Тесты `olenevod/apps/api/tests/test_delivery.py`** на реальной тестовой PostgreSQL 16 (`olenevod_test`):
   - расчёт для Москвы (платная, 1 кг, fee=600, срок 3 дн., зона Центральный);
   - бесплатная доставка при сумме выше порога (fee=0, free_delivery=true);
   - расчёт для СПб (тяжёлый вариант, fee=1000, срок 2 дн.);
   - несколько позиций (сумма веса, округление вверх до кг);
   - неизвестный город → 404;
   - известный город без зоны → 404.
   Данные сидятся прямыми INSERT'ами (idem-потентно), моки не используются, сессия — NullPool, каждый тест — sync-функция с `anyio.run` + `httpx.ASGITransport`.

## Проверка
- **pytest:** `pytest -q tests/` → 32 passed, 1 skipped (пред existing skip `test_migrations.py:80` — `alembic check` не запускается в этой среде из-за `to_tsvector('russian', ...)`, не связано с этапом 9); все 6 тестов доставки проходят на реальной БД.
- **ruff check olenevod tests:** All checks passed!
- **mypy `olenevod application olenevod domain`:** Success: no issues found in 12 source files (включая новый `delivery_service.py`).
- `alembic upgrade head` применяется чисто до `0005_delivery`.
- `GET /delivery/quote` возвращает корректный расчёт на реальных данных.

## Границы
- Код вне этапа 9 не менялся (этапы 0–8 нетронуты), за исключением подключения роутера в `main.py` (требуется по плану).
- Реальных реквизитов владельца не придумано; TODO_OWNER не требуется на этом этапе.
- Моков нет — только реальная БД.
- Внесённые изменения ограничены путями задачи: `olenevod/apps/api/olenevod/application/delivery_service.py`, `olenevod/apps/api/migrations/versions/0005_delivery.py`, `olenevod/apps/api/olenevod/interfaces/http/delivery.py`, `olenevod/apps/api/olenevod/main.py`, `olenevod/apps/api/tests/test_delivery.py`, плюс модели `infrastructure/models/delivery.py` и `__init__.py` (необходимы для ORM-запросов и Alembic метаданных).

## Что осталось
- Ничего по этапу 9. Этап 10 (auth) выполняется отдельным агентом.

## Коммит
`work/stage-09-delivery`: `feat: этап 9 доставка (DeliveryService, таблицы delivery_zones/delivery_tariffs, роут GET /delivery/quote, тесты на реальной БД)`
