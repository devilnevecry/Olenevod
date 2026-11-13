# Отчёт этапа 11-fix — исправление роутеров app.py (Olenevod)

## Статус
Готово

## Что сделано
1. **`olenevod/apps/api/olenevod/interfaces/http/app.py`** — добавлены импорты и `include_router` для всех роутеров: `auth`, `catalog`, `delivery`, `notifications`, `orders`, `payments` (плюс уже существующий `health`). Коллекция маршрутов теперь идентична `main.py` (кроме порядка подключения). Раньше `app` содержал только `health_router`, поэтому `uvicorn olenevod.interfaces.http.app:app` отдавал 404 на `/cities`, `/orders` и т.д.

## Проверка
- **uvicorn `olenevod.interfaces.http.app:app --port 8000`:** запустился успешно.
- **`GET /cities` → 200** со списком городов (мурманск/москва и т.д., реальные сидированные данные). Прямой `curl http://localhost:8000/api/cities` возвращает 404, так как префикса `/api` нет ни в `app.py`, ни в `main.py` — по согласованной архитектуре `/api` срезается Next.js rewrite upstream (`/api/* → localhost:8000`), и uvicorn получает `/cities`. Это соответствует требованию "как в main.py" и запрету менять код вне `interfaces/http/app.py`.
- **`pytest -q tests/`:** `44 passed, 1 skipped` (зелёно, без регрессий).
- **`ruff check olenevod tests`:** `All checks passed!` (чисто).
- **`mypy olenevod\interfaces\http\app.py` (strict):** ошибок в самом `app.py` нет. 3 предуществующие ошибки в `infrastructure\redis.py` (`from_url` without types) и `interfaces\http\health.py` (bare `dict`) — файлы вне этапа 11-fix, менять запрещено; в отчёте этапа 11 они также отмечены как предуществующие.

## Границы
- Изменён только `olenevod/apps/api/olenevod/interfaces/http/app.py`. Код вне этапа 11-fix не трогал.
- Реальных реквизитов/секретов владельца не придумывал.

## Коммит
Ветка текущая (рабочая), коммит только `interfaces/http/app.py`.
