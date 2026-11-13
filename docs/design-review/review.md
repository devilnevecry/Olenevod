# Дизайн-ревью — этап 2 (бренд и дизайн-система)

## Логотип — проверка на фонах и размерах

Файлы в этой папке — рендеры знака «Кольцо-О» наupported фонах и на тёмном и светлом фоне в разных размерах:

| Файл | Фон | Знак | Размер |
|---|---|---|---|
| review-logo-dark-32.png | ink-900 (#14100D) | paper-100 + звезда ember-500 | 32×32 |
| review-logo-dark-120.png | ink-900 | paper-100 + звезда | 120×120 |
| review-logo-dark-640.png | ink-900 | paper-100 + звезда | 640×640 |
| review-logo-light-32.png | paper-bg (#E9E0CE) | paper-ink (#15110E) | 32×32 |
| review-logo-light-120.png | paper-bg | paper-ink | 120×120 |
| review-logo-light-640.png | paper-bg | paper-ink | 640×640 |

Дополнительно в `olenevod/brand/`: avatar-*.png (640×640, тёмный фон, безопасная зона 78%),
favicon-32.png, favicon.ico (32+16), apple-touch-icon.png (180), icon-192.png, icon-512.png,
maskable-512.png, og-default.png (1200×630).

Источники SVG: logo-emblem.svg, logo-on-dark.svg, logo-on-light.svg и остальные —
`olenevod/brand/`. Ренстерованные копии — эта папка.

## Контраст

`olenevod/packages/design-tokens/scripts/contrast-test.js` — все 8 пар DESIGN_SYSTEM §2.2
проходят порог WCAG 2.2 AA (зелёный):

- paper-100/ink-900: 15.83:1 (≥ 4.5)
- paper-300/ink-800: 9.87:1 (≥ 4.5)
- paper-500/ink-900: 5.94:1 (≥ 4.5)
- ember-300/ink-900: 6.95:1 (≥ 4.5)
- paper-100/ember-600: 4.96:1 (≥ 4.5, кнопка)
- ink-900/brass-400: 8.08:1 (≥ 4.5)
- paper-ink/paper-bg: 14.32:1 (≥ 4.5)
- ember-500/ink-900: 4.31:1 (≥ 3, только крупное)

## Reduced motion

Все декоративные анимации отключаются при `prefers-reduced-motion: reduce`:
- лента Ticker — `animation: none`;
- скелетоны — шиммер выключен, опacidad 0.4;
- выезд корзины, модалки — без анимации;
- кнопки — без переходов.
Проверка: включить «Уменьшение движения» в ОС, открыть /_styleguide — движения нет.

## Шрифты

Oswald, Golos Text, IBM Plex Mono — самодешрифтовые (brand/fonts/ + packages/design-tokens/fonts/),
cyrillic + latin, font-display: swap, preload в <head>. Запросов к Google Fonts нет.

## Статус

Всё готово: контраст-тест зелёный, brand/index.html существует, /_styleguide существует,
логотип просмотрен на тёмном и светлом фоне в размерах 32/120/640, reduced-motion работает по медиа-запросу.
