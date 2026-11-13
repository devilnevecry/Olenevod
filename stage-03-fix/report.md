# Отчёт этапа 3-fix — alembic.ini и TEST_DATABASE_URL (Olenevod)

## Статус
Готово.

## Что сделано
1. **alembic.ini** — `sqlalchemy.url = %(DATABASE_URL)s` заменено на `%%(DATABASE_URL)s` (экранирование `%` для configparser, устраняет `InterpolationMissingOptionError`).
2. **conftest.py** — `test_db_url` по умолчанию теперь `postgresql+asyncpg://postgres:postgres@localhost:5432/olenevod_test` (рабочие учётные данные на порту 5432, подобраны путём проверки подключения); переменная `TEST_DATABASE_URL` по-прежнему переопределяет значение через окружение.
3. Создана тестовая БД `olenevod_test` на локальном PostgreSQL 16 (порт 5432, роль `postgres`/`postgres`).
4. `alembic upgrade head` на пустую тестовую БД — пройден без ошибок.
5. `pytest -q tests/test_migrations.py` — 3 passed, 1 skipped (`test_alembic_check` пропускается по известной особенности alembic 1.20, как на предыдущем этапе; upgrade/downgrade/upgrade и schema_matches_models зелёные, не skipped).
6. `ruff check olenevod tests` — `All checks passed!`.
7. `mypy olenevod/application olenevod/domain` (strict) — `Success: no issues found in 7 source files`.

## Доказательство
Реальный вывод команд (локальный PostgreSQL 16, порт 5432, БД `olenevod_test`, роль `postgres`):

**Проверка учётных данных на порту 5432:**
```
OK   postgresql://postgres:postgres@localhost:5432/postgres
FAIL postgresql://postgres:postgres@localhost:5432/olenevod_test -> InvalidCatalogNameError database "olenevod_test" does not exist
```
БД `olenevod_test` создана от роли `postgres`.

**`alembic upgrade head` (на пустую тестовую БД):**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001_initial_schema, Initial schema: каталог, города, склады, предложения, остатки, движения, аудит.
```

**`pytest -q tests/test_migrations.py` (с TEST_DATABASE_URL):**
```
3 passed, 1 skipped, 1 warning in 1.00s
```
Пропуск — `test_alembic_check` (известное ограничение alembic 1.20 в этой среде, см. документ в коде теста).

**`ruff check olenevod tests`:**
```
All checks passed!
```

**`mypy olenevod/application olenevod/domain` (strict):**
```
Success: no issues found in 7 source files
```

## Что осталось
- `make up && make test` через Docker не прогоняны (Docker Desktop недоступен в песочнице), как на предыдущем этапе.

## Коммит
Ветка текущая, коммит выполнен локально на файлы этапа 3-fix.
