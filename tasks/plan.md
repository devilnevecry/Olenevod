# tasks/plan.md — Этап 48: регрессия + Этап 49: обновление финальной документации

## Часть 1 — Этап 48: полный сквозной регрессионный прогон (копия, план не существовал в ветке)

### Цель
Провести полный сквозной регрессионный прогон всех 10 сквозных сценариев и регрессионных проверок BUG-01, 06, 07, 08, 12, 13, 15, 16, 18 против реального API + БД + Playwright.

### Окружение (контракт)
- API: http://localhost:8000 (uvicorn olenevod.interfaces.http.app:app, cwd olenevod/apps/api, env SECRET_KEY)
- Админка: http://localhost:5173 (Vite dev, olenevod/apps/admin)
- БД: PostgreSQL olenevod_test, порт 5432, olenevod/olenevod_dev
- Redis: localhost:6379
- Playwright Chromium 1.65.1, Node 26.13, Python 3.12

### Источники acceptance criteria (план stage-48 и docs/TEST_SCENARIOS.md отсутствуют в ветке)
Сценарии сформулированы по описанию задачи:
1. Создание заказа (POST /orders, резерв стока, идемпотентность)
2. Обработка заказа в админке (логин, GET /admin/orders, смена статуса PATCH /admin/orders/{id}/status)
3. Смена статуса заказа (pending_payment -> new -> paid -> shipped -> delivered)
4. Складские остатки (GET /admin/stock, изменение остатка, доступность товара)
5. Перемещение между складами (POST /admin/transfers, остатки на источниках/назначении)
6. Связь логистики с заказами (GET /delivery/quote, город, сумма)
7. Разные города (Москва / другой город, цены и наличие)
8. Товары без наличия (остаток 0 → заказ нельзя оформить, 409)
9. Разграничение прав (без токена 401 на админ, с чужым токеном 403 на заказ)
10. Сохранность после перезагрузки (корзина/заказ переживает перезагрузку API)

Регрессия BUG: BUG-01, 06, 07, 08, 12, 13, 15, 16, 18 — проверка, что дефекты не вернулись.

### Критерий готовности
Каждый сценарий выполнен через реальные запросы; согласованность frontend/БД проверена; скриншоты, traces, логи сохранены в tasks/qa/; критические и высокие сценарии пройдены.

### Запуск
- API: `SECRET_KEY=... .venv\python -m uvicorn olenevod.interfaces.http.app:app --host 127.0.0.1 --port 8000` (cwd olenevod/apps/api)
- Админка: `npm install && npm run dev` (порт 5173 по умолчанию Vite)
- Процессы останавливаются после проверки (только свои).

### Отчёт
tasks/qa-report.md: PASS/FAIL по сценарию, дефекты со сценариями воспроизведения, ожидаемым/фактическим поведением, путями к скриншотам, текстом ошибок консоли/сети.

## Часть 2 — Этап 49: обновление финальной документации (Olenevod)

### Request
Обновить docs/BUGS.md, docs/TEST_SCENARIOS.md, docs/TEST_COVERAGE.md, docs/REMAINING_WORK.md, docs/RELEASE_READINESS.md, docs/ITERATION_LOG.md, Olenevod.md, INDEX.md с фактическими результатами этапов 42–48. В RELEASE_READINESS.md указать общий статус готовности, проверенные модули, количество сценариев, результаты Playwright/pytest/сборки, открытые дефекты, блокеры, остаточные риски, ссылки на Playwright screenshots/traces/логи. Критерий готовности: все 8 документов обновлены, указано сколько багов исправлено/подтверждено/открыто/заблокировано, риски и готовность к сдаче. Продуктовый код не менять. Файлы вне docs/**, Olenevod.md, INDEX.md не трогать.

### Assumptions
- Все 8 целевых файла отсутствуют в ветке — создаются заново (docs/ содержит только design-review/).
- Источник правды этапов 42–48: полный вывод регресса 1.T48 (`data\results\mwkfedqhnoov\1.T48.md`), принятые технические решения в задании пользователя, отчёты этапов 1–13 (`stage-*/report.md`).
- Статусы сценариев ставятся только по прямым отчётам; без источника — «не проверено / нет данных», не выдумывать.
- Документы пишутся на русском (язык команды и существующих отчётов); команды, код, идентификаторы — на английском.
- tasks/qa-report.md, tasks/qa/results.json, tasks/qa/verify_e2e.js, screenshots tasks/qa/0*.png относятся к ветке этапа 48 и при слиянии появятся здесь — ссылаемся на них как на артефакты, существование в этой ветке не проверяем.
- Продуктовый код не меняется; верстка/тесты не правим.

### Architecture decisions
- Документация делят на 3 группы: bug-register (BUGS.md), сценарии/покрытие (TEST_SCENARIOS.md, TEST_COVERAGE.md), статус релиза и остаток (REMAINING_WORK.md, RELEASE_READINESS.md, ITERATION_LOG.md), плюс корневые навигационные файлы (Olenevod.md, INDEX.md).
- Подсчёт багов: исправлено — по факту слияния исправлений (BUG-02, BUG-10); подтверждено — дефект воспроизведён/исправление проверено (BUG-11, BUG-17); открыто — воспроизведён, не исправлено (BUG-05, BUG-18, paid→500, delivery/quote→404); заблокировано — нельзя проверить в среде (Docker, prod-сборка).

### Commands
- Run: none (документация, нет исполняемого кода).
- Test: none (проверка — чтение всех 8 файлов на согласованность статусов и ссылок).
- Build/lint: none.

### Definition of done (каждая задача)
- Файл создан по своему назначению, язык — русский, команды/код — английский.
- Статусы согласованы с отчётами этапов 42–48 и 1–13 (не выдуманы).
- Ссылки на arteфакты корректны по форме (пути без проверки существования вне ветки).
- Последняя задача: сверка всех 8 файлов — статистика багов и сценариев согласована между документами.

## Tasks (этап 49)

### T1: tasks/plan.md + tasks/todo.md (план этапа 49)
**Description:** Составить план и чек-лист этапа 49 по шаблонам навыка planning-and-task-breakdown.
**Acceptance criteria:**
- [ ] tasks/plan.md и tasks/todo.md созданы, все задачи имеют критерии приёмки и команду проверки.
- [ ] Не более 12 задач на фазу, размеры XS–S, есть чекпоинты.
**Verification:** чтение обоих файлов, подсчёт задач.
**Depends on:** none
**Files likely touched:** `tasks/plan.md`, `tasks/todo.md`
**Size:** XS

### Checkpoint after T1: план утверждён, можно писать документы

### T2: docs/BUGS.md (регистр багов этапов 42–48)
**Description:** Регистр багов: BUG-02, BUG-05, BUG-10, BUG-11, BUG-17, BUG-18 plus критические дефекты этапа 48 (статус заказа "paid" → 500, отсутствие значения в enum order_status; GET /delivery/quote → 404, зоны не засеяны). Статусы: исправлено / подтверждено / открыто / заблокировано, с 증거ми и ссылками на отчёты.
**Acceptance criteria:**
- [ ] Указано количество багов по категориям: исправлено 2, подтверждено 2, открыто 4.
- [ ] Каждому дефекту ставится статус только по прямому отчёту.
- [ ] Есть ссылки на отчёты этапов 42–48 и error-context.md.
**Verification:** чтение файла, сверка цифр с TEST_COVERAGE.md и RELEASE_READINESS.md.
**Depends on:** T1
**Files likely touched:** `docs/BUGS.md`
**Size:** S

### T3: docs/TEST_SCENARIOS.md (список сценариев и статусы)
**Description:** Перечень проверенных сценариев: pytest (здоровье, миграции, каталог, оплата, инвентарь, доставка, auth, уведомления) и Playwright (витрина S1/S5–S12, админ BUG-05 11 разделов, BUG-17 viewports, вход). Статусы только по прямым отчётам; без источника — «не проверено / нет данных».
**Acceptance criteria:**
- [ ] Все сценарии из отчётов этапов 42–48 и 1–13 перечислены со статусом.
- [ ] Никакого выдуманного статуса;不明ные — «не проверено / нет данных».
**Verification:** чтение файла, сверка с отчётами этапов.
**Depends on:** T1
**Files likely touched:** `docs/TEST_SCENARIOS.md`
**Size:** S

### T4: docs/TEST_COVERAGE.md (покрытие тестами)
**Description:** Покрытие: pytest 44 passed / 1 skipped (этап 11-fix/33, пропуск test_alembic_check); Playwright (витрина 8/8, админ 2/11 proved + 9 fail, BUG-17, BUG-18); линтеры/типы (ruff, mypy strict, tsc, eslint); сборка (next build не запускался, make up/test — нет Docker).
**Acceptance criteria:**
- [ ] Числа pytest/Playwright совпадают с отчётами этапов (44/1, 8/8, 2/11 proved).
- [ ] Указаны непокрытые зоны и причины.
**Verification:** чтение файла, сверка цифр с BUGS.md и RELEASE_READINESS.md.
**Depends on:** T1
**Files likely touched:** `docs/TEST_COVERAGE.md`
**Size:** S

### T5: docs/REMAINING_WORK.md (остаточные работы)
**Description:** Незавершённые работы после этапов 42–48: enum order_status (paid), seeding delivery_zones/delivery_tariffs, админ CRUD (селекты 422, кнопка "Добавить" D2, оверлей D1, 501 routes/carriers), BUG-18 витрины, вход через браузер, next build, Docker-валидация, реальные токены владельца.
**Acceptance criteria:**
- [ ] Каждый пункт со ссылкой на источник (отчёт этапа / error-context).
- [ ] Нет продуктового кода, только описание работ.
**Verification:** чтение файла.
**Depends on:** T2, T3
**Files likely touched:** `docs/REMAINING_WORK.md`
**Size:** S

### T6: docs/RELEASE_READINESS.md (готовность к релизу)
**Description:** Общий статус готовности, проверенные модули, количество сценариев, результаты pytest/Playwright/сборки, открытые дефекты, блокеры, остаточные риски, ссылки на скриншоты/трассы/логи.
**Acceptance criteria:**
- [ ] Общий статус: не готова к сдаче (критические дефекты не закрыты, нет Docker/prod-верификации).
- [ ] Указаны числа: сценарии, пройденные/проваленные, баги по категориям.
- [ ] Есть ссылки на tasks/qa/0*.png, olenevod/apps/admin/test-results/*/error-context.md, 1.T48.md.
**Verification:** чтение файла, сверка со всеми остальными docs.
**Depends on:** T2, T3, T4, T5
**Files likely touched:** `docs/RELEASE_READINESS.md`
**Size:** S

### T7: docs/ITERATION_LOG.md (логи итераций этапов 42–48)
**Description:** Поэтапный лог 1.T42–1.T48 с автором, статусом, ключевыми результатами и ссылками на коммиты/отчёты; краткая ссылка на отчёты этапов 1–13.
**Acceptance criteria:**
- [ ] Все 7 итераций 42–48 описаны со статусом и источником.
- [ ] Ссылки на stage-*/report.md для этапов 1–13.
**Verification:** чтение файла.
**Depends on:** T1
**Files likely touched:** `docs/ITERATION_LOG.md`
**Size:** S

### Checkpoint after T2–T7: все 6 документов docs/ написаны

### T8: Olenevod.md (карточка проекта в корне)
**Description:** Назначение проекта, стек, порты (API 8000, web 3000, admin 5173, PostgreSQL 5432, Redis 6379), как запускать (Makefile, .env из .env.example), текущий статус (этап 49, релиз не готов), ссылки на docs/**, ограничения среды (нет Docker), роли команды.
**Acceptance criteria:**
- [ ] Указаны все порты и переменные окружения из .env.example.
- [ ] Статус agrees с RELEASE_READINESS.md.
**Verification:** чтение файла.
**Depends on:** T6
**Files likely touched:** `Olenevod.md`
**Size:** M

### T9: INDEX.md (корневой указатель)
**Description:** Указатель на docs/**, отчёты stage-*/report.md, tasks/, порядок ориентации в репозитории.
**Acceptance criteria:**
- [ ] Все 8 целевых файла этапа 49 упомянуты со ссылками.
- [ ] Упомянуты отчёты этапов 1–13.
**Verification:** чтение файла.
**Depends on:** T6, T7
**Files likely touched:** `INDEX.md`
**Size:** M

### Checkpoint after T8–T9: корневые документы готовы

### T10: сверка всех 8 документов (финальная проверка)
**Description:** Проверить, что все 8 файлов существуют, статистика багов и сценариев согласована между BUGS.md, TEST_SCENARIOS.md, TEST_COVERAGE.md, RELEASE_READINESS.md, ссылки не биты по форме.
**Acceptance criteria:**
- [ ] 8 файлов созданы: docs/BUGS.md, docs/TEST_SCENARIOS.md, docs/TEST_COVERAGE.md, docs/REMAINING_WORK.md, docs/RELEASE_READINESS.md, docs/ITERATION_LOG.md, Olenevod.md, INDEX.md.
- [ ] Цифры согласованы: исправлено 2 / подтверждено 2 / открыто 4 / заблокировано валидация Docker и prod-сборка.
**Verification:** чтение всех 8 файлов.
**Depends on:** T2–T9
**Files likely touched:** все 8 файлов (только чтение)
**Size:** XS

### Checkpoint after T10: критерий готовности этапа 49 выполнен

## Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| tasks/qa/* артефакты этапа 48 отсутствуют в этой ветке | ссылки могут ссылаться на несуществующие файлы до слияния | ссылаться по форме, не утверждать существование |
| Статусы сценариев без прямого источника | риск выдуманных данных | ставить «не проверено / нет данных» (решение 4.c) |
| Docker и продакшн-сборка не проверялись |リリース-готовность ограничена | честный статус «не готова» в RELEASE_READINESS.md |
| Старые миграции 0001–0003 и redis.py/health-py have ruff/mypy findings | шум в линтерах, не блокирует | отметить как pre-existing, не трогать код |
