# Отчёт этапа 10 — Auth (e-mail код) (Olenevod)

## Статус
Готово

## Что сделано
1. **Alembic-миграция `0006_auth.py`** — таблицы `users` (id, email, phone, name, hashed_password, is_verified, created_at, updated_at) и `email_verification_codes` (id, email, code, expires_at, used_at, created_at) с CHECK-ограничениями и индексами.
2. **`olenevod/application/auth_service.py`** — `AuthService` с методами:
   - `register(email, name, password)` — создаёт пользователя (is_verified=false), хеширует пароль PBKDF2-HMAC-SHA256, генерирует 6-значный код, инвалидирует старые коды, сохраняет в БД (SMTP не используется — VERIFIED_SIMULATED).
   - `request_code(email)` — новый код для существующего пользователя (simulated).
   - `verify_code(email, code)` — проверяет код, помечает использованным, устанавливает `is_verified=true`.
   - `login(email, password)` — валидирует пароль и верификацию, возвращает JWT-токен (HS256, ключ из `settings.secret_key`).
3. **`olenevod/interfaces/http/auth.py`** — роуты `POST /auth/register`, `POST /auth/request-code`, `POST /auth/verify-code`, `POST /auth/login` с Pydantic-схемами запроса/ответа; доменные исключения транслируются в HTTP-статусы (409, 404, 400, 401).
4. **`olenevod/main.py`** — подключён `auth_router`.
5. **`olenevod/tests/test_auth.py`** — 6 тестов на реальной PostgreSQL 16 (`olenevod_test`): регистрация + код в БД, верификация кода → is_verified=true, неверный код → 400, вход с правильным паролем → JWT-токен, неверный пароль → 401, повторная регистрация → 409. Код читается из БД (simulated SMTP), моков нет.

## Проверка
- **pytest:** 38 passed, 1 skipped (включая 6 новых тестов auth) на реальной тестовой БД
- **ruff check:** чисто для новых/изменённых файлов (ошибки только в предуществующих миграциях 0001–0003 и tmp-скриптах, не этапа 10)
- **mypy strict:** Success для `auth_service.py`, `auth.py`, `main.py` (ошибки только в предуществующих `redis.py` и `health.py`)

## Границы
- Код вне этапа 10 не менялся (кроме `main.py` — подключение роутера).
- Реальных e-mail адресов владельца не придумано (тестовые адреса вида `auth-test-<uuid>@example.com`).
- Реальных секретов и токенов владельца нет.
- Моков SMTP не написано — только VERIFIED_SIMULATED.

## Что осталось
- Запуск через Docker (`make up && make test`) не прогонян (Docker Desktop недоступен в песочнице).
- mypy strict на предуществующих файлах (`redis.py`, `health.py`) имеет ошибки, не связанные с этапом 10.

## Коммит
`work/stage-10-auth`: `feat: этап 10 auth (регистрация, код верификации e-mail, вход, JWT-токен)`
