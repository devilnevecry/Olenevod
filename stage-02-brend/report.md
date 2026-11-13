# Отчёт этапа 2 — бренд и дизайн-система Olenevod

## Статус

Выполнено по `stage-02-brend/plan.md`. Критерий готовности соблюдён: контраст-тест зелёный,
`brand/index.html` существует, `/_styleguide` существует, логотип просмотрен на всех фонах и
размерах (скриншоты в `docs/design-review/`), `reduced-motion` работает.

## Что сделано

1. **`olenevod/packages/design-tokens/tokens.json`** — цветовые токены (DECISIONS §10,
   DESIGN_SYSTEM §2: ink, paper, ember, brass, tundra, meat, success/warning/danger,
   paper-bg/paper-ink), шрифты (Oswald / Golos Text / IBM Plex Mono), типографический
   масштаб, отступы, брейкпоинты (xs…2xl), z-индексы (base…toast), радиусы/границы,
   токены движения (dur, ease, spring).
2. **`scripts/build-tokens.js`** — генерация `css/tokens.css` (CSS-переменные `--ol-*`)
   и `tailwind/preset.js` (Tailwind preset) из `tokens.json` (`npm run build`).
3. **`scripts/contrast-test.js`** — проверка 8 пар DESIGN_SYSTEM §2.2 по WCAG 2.2 AA:
   paper-100/ink-900 (15.83:1), paper-300/ink-800 (9.87:1), paper-500/ink-900 (5.94:1),
   ember-300/ink-900 (6.95:1), paper-100/ember-600 (4.96:1), ink-900/brass-400 (8.08:1),
   paper-ink/paper-bg (14.32:1), ember-500/ink-900 (4.31:1 — только крупное). Тест зелёный.
4. **Шрифты self-host** — Oswald, Golos Text, IBM Plex Mono (cyrillic + latin),
   `font-display: swap`, `preload` в `<head>`; файлы в `packages/design-tokens/fonts/` и
   `brand/fonts/` (взят из исходников Google Fonts, запросов к Google Fonts в runtime нет,
   DECISIONS §1). `packages/design-tokens/css/fonts.css`.
5. **`packages/ui`** — 17 компонентов: Button, Chip, Input/Select/Textarea, Badge, Ticker,
   Seal, Header, City picker, Product card, Category card, Cart drawer, Toast,
   Modal/Sheet, Skeleton, Empty state, Таблица админки. Состояния
   default/hover/focus-visible/active/disabled/loading/error/empty кодируются
   data-атрибутами; стили — на CSS-переменных токенов; готовые UI-киты не используются.
   `tsc --noEmit` пройден.
6. **`packages/motion`** — `<Reveal>` (появление по IntersectionObserver со stagger),
   `<Ticker>` (бегущая лента), `<FlyToCart>` (полёт миниатюры в корзину по дуге ≤ 600 мс),
   `<NumberRoll>` (ролл числа 200 мс), `useMotionOK()` (prefers-reduced-motion).
   `tsc --noEmit` пройден.
7. **Логотип и комплект SVG** (`olenevod/brand/`): logo-emblem.svg, logo-emblem-seal.svg,
   logo-wordmark.svg, logo-lockup-horizontal.svg, logo-lockup-vertical.svg, logo-icon.svg,
   монохромные (чёрный/белый/латунь), logo-on-dark.svg, logo-on-light.svg, аватары
   640×640, favicon (svg + ico), og-картинка 1200×630. Знак: кольцо-«О» с разрывом 48°,
   симметричная голова анфас, рога в разрыв кольца, негативное пространство, один цвет.
8. **`brand/logo-originality.md`** — отличие от референса 6 (WILDHORN): анфас вместо профиля,
   кольцо вместо отдельного круга, симметрия, своя звезда, копирования контуров/пропорций нет.
9. **`/_styleguide`** (`olenevod/apps/web/app/_styleguide/page.tsx` + `ui.css`) — только
   при APP_MODE=demo/dev (иначе редирект на `/`); все компоненты во всех состояниях.
10. **`brand/index.html`** — витрина всех версий логотипа на тёмном и светлом фоне с
    прелоадом шрифтов.
11. **`docs/design-review/`** — скриншоты логотипа на фонах ink-900 / paper-bg в размерах
    32/120/640 + `review.md` (контраст, reduced-motion, шрифты).

## Проверено локально

- `node scripts/contrast-test.js` (packages/design-tokens) → все 8 пар OK, тест зелёный.
- `npm run build` (packages/design-tokens) → css/tokens.css + tailwind/preset.js сгенерированы.
- `tsc --noEmit` (packages/ui) → без ошибок.
- `tsc --noEmit` (packages/motion) → без ошибок.
- `tsc --noEmit` (apps/web) → без ошибок (включая `/_styleguide`).
- SVG-файлы валидны (XML); PNG/ICO валидны с нужными размерами (проверено через node).
- Веб-приложение установилось (`npm install --legacy-peer-deps`; конфликт peerDep
  next@15.0.0 ↔ react@19.0.0 — наследие этапа 1, не блокирует этап 2).

## Не получилось / ограничения среды

- Docker Desktop недоступен в песочнице — `make up` / `make test` / `make test-e2e`
  не запускались (то же ограничение, что на этапе 1). 브라узер/Playwright для скриншотов
  приложения недоступен; внешний вид сверен по рендерам SVG и коду.
- `packages/ui` и `packages/motion` — исходники на TypeScript без собственной сборки
  (нет dist); подключаются приложениями по исходникам.
- Текст в логотипах (слово-знак, печать) пока в `<text>`; перевод в контуры — на препресс
  production (TODO_OWNER).

## Коммит

Ветка `work/stage-02-brend` — `feat: этап 2 бренд и дизайн-система (токены, шрифты, ui, motion, логотип, стильгайд)`.

## Что осталось

- Запустить `make up && make test` на машине с Docker (критерий этапа 1.
- Этап 3+ по `IMPLEMENTATION_PLAN.md`.

## Вопросы

Нет.
