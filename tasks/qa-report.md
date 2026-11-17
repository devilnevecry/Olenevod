# QA-rapport — Этап 48: полный сквозной регрессионный прогон

## Окружение
- API: http://127.0.0.1:8000 (`uvicorn olenevod.interfaces.http.app:app`, cwd `olenevod/apps/api`, `SECRET_KEY` через переменную окружения)
- Админка: http://localhost:5173 (Vite dev, `olenevod/apps/admin`, `npm install` + `npm run dev`)
- БД: PostgreSQL `olenevod_test`, port 5432, `olenevod/olenevod_dev`; Redis `localhost:6379`
- Playwright Chromium (bundled, `ms-playwright\chromium-1255`), Node 26.13, Python 3.12
- Скриншоты и логи: `tasks/qa/` (`results.json`, `*.png`, скрипт `verify_e2e.js`)

Сценарии stage-48 и docs/TEST_SCENARIOS.md отсутствовали в ветке — план составлен по описанию задачи (см. `tasks/plan.md`). Продуктовый код не изменялся. Оба сервиса остановлены после проверки.

## Данные теста (реальные, из БД olenevod_test)
- Пользователь: `ivan@example.com` (UUID ...6951, verified), пароль DemoPass123 — JWT получен через реальный `/auth/login`.
- Город Москва: `11111111-1111-1111-1111-111111111001`; склад "Склад заказы" `...5003`; товар "Продукт для заказа" / вариант ZAKAZ-001 `...4002`; цена 9500 коп; остаток on_hand=10 reserved=2 (доступно 8).
- Город Test City E2E `01399bf6-...` без остатков.
- `delivery_zones` / `delivery_tariffs` — пустые.

## Результаты по сценариям

| № | Сценарий | Статус | Деталь |
|---|----------|--------|--------|
| S1 | Создание заказа (POST /orders, резерв стока) | PASS | 201, status=pending_payment, total=9500, user_id=null (демо) |
| S1-bis | Идемпотентность (одинаковый ключ → один заказ) | PASS | тот же order_id, reserva не удваивается |
| S2 | Вход в админку через форму (реальный /auth/login) | PASS | редирект на /cities, токен в localStorage |
| S2 | Заказ виден в списке админки /admin/orders | PASS | строка заказа найдена |
| S3 | Смена статуса pending_payment → new (UI + API) | PASS | status=new подтверждено через GET |
| S3-bis | Смена статуса new → paid | FAIL | HTTP 500 (см. дефект D1) |
| S4 | Остатки на складах (GET /admin/stock) | PASS | страница загружена, остатки отображены |
| S5 | Перемещения между складами (страница + POST draft) | PASS | страница /transfers загружена; POST /admin/transfers status=draft → 201 |
| S6 | Девис доставки GET /delivery/quote (Москва) | INFO | 404 `delivery_zone not found` — таблицы delivery_zones/tariffs пусты (отсутствуют seeded зоны); логика эндпоинта верна (404 при отсутствии зоны) |
| S7 | Разные города (Москва vs Test City) | PASS | Москва: 1 продукт (доступно 8); Test City: 0 |
| S8 | Товар без наличия (qty 100 > доступно 8) | PASS | HTTP 409 `insufficient stock` |
| S9.i | Права: админ без токена → 401 | PASS | GET /admin/orders → 401 |
| S9.ii | Права: заказ без токена → 200 (демо) | PASS | GET /orders/{id} → 200 |
| S9.iii | Права: заказ соу token, ownerless demo → 403 | PASS | GET /orders/{id} → 403 |
| S10 | Сохранность после перезапуска API | PASS | после рестарта заказ всё еще в БД (status=confirmed) |

## Дефекты

### D1 — HIGH: смена статуса заказа на "paid" возвращает HTTP 500
**Шаги воспроизведения:**
1. Получить админ-JWT (ivan@example.com / DemoPass123).
2. `PATCH /admin/orders/{order_id}/status` с телом `{"status":"paid"}` и заголовком `Authorization: Bearer <jwt>`.
**Ожидаемое:** HTTP 200, статус заказа обновлён.
**Фактическое:** HTTP 500 Internal Server Error.
**Причина:** columna `orders.status` — PostgreSQL ENUM `order_status` со значениями `pending_payment, new, confirmed, assembling, ready, shipped, delivered, cancelled, returned`. Значение `"paid"` в перечислении отсутствует, поэтому `UPDATE … SET status='paid'` падает с `invalid input value for enum order_status: "paid"` (traceback в логах uvicorn). Админ-UI (поле Статус в карточке заказа) предлагает `"paid"`, которое нельзя сохранить. Валидное значение `"confirmed"` работает (PATCH → 200).
**Скрипт/доказательство:** `tasks/qa/api_checks.ps1`, лог uvicorn (traceback), `tasks/qa/results.json` (S3-bis FAIL).
**Связано со сценарием:** S3 (полный цикл статусов невозможен через админку).

### D2 — MEDIUM: GET /delivery/quote возвращает 404 для любого города
**Шаги воспроизведения:** `GET /delivery/quote?city_id=11111111-1111-1111-1111-111111111001`.
**Ожидаемое:** расчёт доставки (zone, fee, estimated_days).
**Фактическое:** HTTP 404 `{"detail":"delivery_zone not found: ...1001"}`.
**Причина:** в `olenevod_test` нет строк в `delivery_zones`/`delivery_tariffs` (не засиданы зоны доставки). Код эндпоинта отрабатывает верно (404 при отсутствии зоны), но сценарий логистики не может быть полностью проверен без сида зон.
**Скриншот/доказательство:** `tasks/qa/results.json` (S6, INFO).
**Связано со сценарием:** S6 (связь логистики с заказами).

### Наблюдения (не блокируют)
- Консоль админки: предупреждения React Router (будущие флаги v7), предупреждение CrudPage "Each child in a list should have a unique key prop" на `/cities`, 404 на `favicon.ico` — некритично, функциональность не затронута.
- CORS настроен корректно (preflight OPTIONS возвращает `access-control-allow-origin: http://localhost:5173`); сообщение CORS в браузере у S3-bis было вторичным эффектом HTTP 500.
- Заказы в демо-режиме имеют `user_id=NULL`: без токена доступны (200), с любым токеном — 403 (по設計 этапа 11-fix, владельца нет).

## Регрессия BUG-01, 06, 07, 08, 12, 13, 15, 16, 18
Определения этих багов и файл `docs/TEST_SCENARIOS.md` отсутствовали в ветке, поэтому точная повторная верификация каждого бага по его критериям не была возможна. Выполнена общая регрессионная проверка: все 11 разделов админки (`/cities, /warehouses, /products, /variants, /offers, /stock, /transfers, /orders, /customers` + `/routes, /carriers`) открываются, `/routes` и `/carriers` возвращают 501 (ожидаемо, ORM-моделей нет — вне моих путей), новых ошибок консоли/сети, ломающих функционал, не выявлено за исключением D1. BUG-18 (витрина, 500 Rules of Hooks) относится к фронтенду веб-магазина (Next.js, порт 3000), который не был развёрнут в этой сессии (нет node_modules) — не проверено.

## Итог
Пройдено: 13 из 14 выполнимых проверок (сценарные PASS). 1 сценарий упал (S3-bis), 1 информативный (S6 — отсутствие seeded зон доставки). Критический дефект D1 bloqueет полный цикл смены статусов заказа через админку.
