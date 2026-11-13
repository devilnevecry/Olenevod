# Отчёт этапа 12 — Витрина I (Next.js, Olenevod)

## Статус
Готово

## Что сделано
Все шаги плана `stage-12-frontend-i/plan.md` выполнены в рамках `olenevod/apps/web/**`:

1. **Конфигурация Next.js 15 + TypeScript + Tailwind CSS 4** — `package.json`, `next.config.js`, `tsconfig.json` (strict), `postcss.config.js`, `tailwind.config.js`. Зависимости `@olenevod/ui`, `@olenevod/motion`, `@olenevod/design-tokens` подключены как локальные пакеты репо (`file:`), транспилируются через `transpilePackages`. ESLint переведён на flat config (eslint 9).
2. **Страница `/`** — герой со словом "ОЛЕНЕВОД", выбор города (чипы), категории, тикеры.
3. **Страница `/catalog`** — список товаров города с фильтрацией по категории (чипы реально меняют `category_id` в URL и перезагружают товары), поиском и пагинацией.
4. **Страница `/products/[slug]`** — карточка товара: заглушка фото (Skeleton), цена (NumberRoll), наличие по городам (бэджи), кнопка "В корзину".
5. **Дизайн-система** — CSS-переменные токенов из `packages/design-tokens` (`tokens.css`), компоненты `@olenevod/ui` (Button, Chip, Badge, ProductCard, CategoryCard, Skeleton, EmptyState, Ticker) без готовых UI-китов.
6. **Анимации** — `Reveal` (герой, секции), `Ticker` (промо-лента), `NumberRoll` (цена), hover карточки (A5), скелетоны (A15), синие чекбоксы/печать (A16) через `@olenevod/motion` и `@olenevod/ui`.
7. **API каталога** — `GET /cities`, `GET /categories`, `GET /products`, `GET /products/{id}` через `src/lib/api.ts`. Запросы идут через Next.js rewrite `/api/* → http://localhost:8000/*` (обход CORS, бэкенд не менялся). Добавлены ретраи на 5xx.
8. **Тесты** — E2E Playwright на реальных seed-данных (город Москва, товары из БД `olenevod_test`).
9. **Проверка** — `tsc --noEmit` clean, `eslint` clean, E2E 4/4 зелёные.

## Проверка
- `tsc --noEmit` — clean (no issues found).
- `eslint .` — clean (no issues found).
- `npx playwright test` — 4 passed (чROMIUM):
  1. страница главной загружается и показывает города
  2. каталог показывает товары города
  3. товары фильтруются по категории
  4. карточка товара показывает наличие по городу
- Бэкенд API (порт 8000) подключён к БД `olenevod_test` с сидом каталога (`tests/seed_catalog.sql`).

## Границы
- Файлы вне `olenevod/apps/web/**` и `stage-12-frontend-i/report.md` не менялись (этапы 0–11, пакеты репо нетронуты).
- Готовых UI-китов не использовалось — только безголые примитивы `@olenevod/ui`.
- Реальных товаров/реквизитов владельца не придумано — только seed-данные из БД.
- Токены владельца не кодируются.

## Что осталось
- Временный отладочный файл `olenevod/apps/web/debug_check.cjs` не удалён (удаление файлов заблокировано в окружении), не коммитится.
- package-lock.json, tsconfig.tsbuildinfo, next-env.d.ts, test-results/, playwright-report/ не коммитится (артефакты сборки/тестов).
- `next build` (production) не прогонялся — критерий готовности ограничен tsc + eslint + E2E.
- Интеграция корзины/оформления (кнопка "В корзину" — заглушка) относится к этапу 13.

## Коммит
`work/stage-12-frontend-i`: `feat: этап 12 витрина Next.js (/, /catalog, /products/[slug], каталог API, E2E)`
