import { redirect } from "next/navigation"

import "./ui.css"

/**
 * Страница /_styleguide — витрина всех компонентов и состояний дизайн-системы.
 * Доступна только при APP_MODE=demo | dev (см. .env.example). На остальных
 * режимах перенаправляет на главную.
 */
export default function StyleguidePage() {
  const mode = process.env.NEXT_PUBLIC_APP_MODE
  if (mode !== "demo" && mode !== "dev") redirect("/")

  return (
    <div style={{ maxWidth: 940, margin: "0 auto", padding: 24 }}>
      <nav className="ol-header">
        <div className="ol-brand">
          <span className="ol-seal" style={{ width: 40, height: 40 }} aria-hidden="true" />
          <span className="ol-wordmark">Оленевод</span>
        </div>
        <div className="ol-nav">
          <a href="/">Витрина</a>
          <a href="/brand/index.html" target="_blank" rel="noopener noreferrer">Бренд-кит</a>
        </div>
        <div className="ol-cart">Корзина <span aria-hidden="true">· 3</span></div>
      </nav>

      <h1 style={{ marginBottom: 8 }}>Стильгайд Olenevod</h1>
      <p className="sg-note">Режим: {mode}. Доступно только при APP_MODE=demo / dev.</p>
      <p>
        Компоненты собраны на токенах <code>packages/design-tokens/tokens.json</code> (CSS-переменные
        <code>--ol-*</code> генерируются через <code>npm run build</code> в
        <code>packages/design-tokens</code>). Шрифты самодешрифтовые: Oswald, Golos Text,
        IBM Plex Mono (cyrillic + latin, <code>font-display: swap</code>, <code>preload</code>).
        Готовые UI-киты не используются — только собственная разметка на токенах.
      </p>
      <p>
        Логотип:{" "}
        <a href="/brand/index.html" target="_blank" rel="noopener noreferrer">brand/index.html</a>{" "}
        · проверка оригинальности: <code>brand/logo-originality.md</code>.
      </p>

      <section className="sg-section">
        <h2>Цветовые токены</h2>
        <div className="sg-grid">
          {[
            ["ink-900", "#14100D", "основной текст"],
            ["ink-850", "#1A1511", "поверхности"],
            ["ink-800", "#211B16", "вторичный текст"],
            ["paper-100", "#F2EADB", "акцентный текст"],
            ["ember-600", "#B33A20", "кнопка primary"],
            ["brass-400", "#C8A468", "латунь / декор"],
            ["danger", "#E0524A", "ошибка"],
            ["paper-bg", "#E9E0CE", "бумажный фон"],
          ].map(([name, hex, role]) => (
            <div
              key={name}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 6,
                padding: 12,
                background: "var(--ol-color-ink-850)",
                border: "1px solid var(--ol-color-line)",
                borderRadius: "var(--ol-radius-sm)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span
                  style={{
                    width: 32,
                    height: 24,
                    background: hex,
                    borderRadius: 2,
                    border: "1px solid var(--ol-color-line)",
                  }}
                />
                <span
                  style={{
                    fontFamily: "var(--ol-font-family-mono)",
                    fontSize: 12,
                    color: "var(--ol-color-paper-300)",
                    letterSpacing: "0.06em",
                  }}
                >
                  {name}
                </span>
              </div>
              <span
                style={{
                  fontFamily: "var(--ol-font-family-mono)",
                  fontSize: 11,
                  color: hex,
                  letterSpacing: "0.06em",
                }}
              >
                {hex}
              </span>
              <span style={{ fontSize: 12, color: "var(--ol-color-paper-500)" }}>{role}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="sg-section">
        <h2>Шрифты</h2>
        <p
          style={{
            fontFamily: "var(--ol-font-family-display)",
            fontSize: "34px",
            letterSpacing: "0.02em",
            textTransform: "uppercase",
            marginBottom: 8,
          }}
        >
          Oswald 700 — дисплей
        </p>
        <p style={{ fontFamily: "var(--ol-font-family-text)", fontSize: "18px", marginBottom: 8 }}>
          Golos Text — основной текст, кириллица + латиница
        </p>
        <p
          style={{
            fontFamily: "var(--ol-font-family-mono)",
            fontSize: "14px",
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            marginBottom: 8,
          }}
        >
          IBM Plex Mono — метки, моно
        </p>
        <p className="sg-note">
          font-display: swap;           preload через &lt;link rel="preload"&gt; в &lt;head&gt;; файлы в
          brand/fonts/ (запросов к Google Fonts нет).
        </p>
      </section>

      <section className="sg-section">
        <h2>Кнопки (default / hover / focus-visible / active / disabled / loading)</h2>
        <div className="sg-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}>
          <button className="ol-btn" data-variant="primary">
            Primary
          </button>
          <button className="ol-btn" data-variant="primary" data-state="active">
            Primary active
          </button>
          <button className="ol-btn" data-variant="primary" data-state="loading">
            Primary loading
          </button>
          <button className="ol-btn" data-variant="primary" disabled>
            Primary disabled
          </button>
          <button className="ol-btn" data-variant="secondary">Secondary</button>
          <button className="ol-btn" data-variant="secondary" disabled>
            Secondary disabled
          </button>
          <button className="ol-btn" data-variant="ghost">Ghost</button>
          <button className="ol-btn" data-variant="ghost" disabled>
            Ghost disabled
          </button>
        </div>
      </section>

      <section className="sg-section">
        <h2>Чипы</h2>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <span className="ol-chip">Город</span>
          <span className="ol-chip" data-state="selected">
            Выбран
          </span>
          <span className="ol-chip" data-state="disabled">Заблокирован</span>
        </div>
      </section>

      <section className="sg-section">
        <h2>Бейджи</h2>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <span className="ol-badge" data-type="stock">В наличии</span>
          <span className="ol-badge" data-type="low">Мало на складе</span>
          <span className="ol-badge" data-type="out">Нет в наличии</span>
          <span className="ol-badge" data-type="cold">Заморозка −18°</span>
          <span className="ol-badge" data-type="demo">Демо</span>
        </div>
      </section>

      <section className="sg-section">
        <h2>Поля ввода (default / focus / error / disabled)</h2>
        <div className="sg-grid">
          <div className="ol-field">
            <label className="ol-label">Email</label>
            <input className="ol-input" placeholder="иван@olenevod.ru" />
          </div>
          <div className="ol-field" data-state="error">
            <label className="ol-label">Телефон</label>
            <input className="ol-input" placeholder="+7 ___ ___ __ __" />
            <p className="ol-error-text">Неверный формат телефона</p>
          </div>
          <div className="ol-field">
            <label className="ol-label">Город</label>
            <select className="ol-select">
              <option>Воркута</option>
              <option>Сыктывкар</option>
            </select>
          </div>
          <div className="ol-field" data-state="error">
            <label className="ol-label">Комментарий</label>
            <textarea className="ol-textarea" placeholder="…" />
            <p className="ol-error-text">Поле обязательно</p>
          </div>
          <div className="ol-field">
            <label className="ol-label">Заблокировано</label>
            <input className="ol-input" disabled placeholder="Недоступно" />
          </div>
        </div>
      </section>

      <section className="sg-section">
        <h2>Бегущая лента (Ticker)</h2>
        <div className="ol-ticker" data-kind="promo">
          <div className="ol-ticker-track">
            ПОПУЛЯРНОЕ!{" "}
            <span className="ol-star">★</span>{" "}
            НОВИНКИ!{" "}
            <span className="ol-star">★</span>{" "}
            СЫРОВЯЛЕНАЯ ОЛЕНИНА{" "}
            <span className="ol-star">★</span>{" "}
            ДОСТАВКА ПО ТУНДРЕ{" "}
            <span className="ol-star">★</span>
          </div>
        </div>
        <div className="ol-ticker" data-kind="info" data-paused>
          <div className="ol-ticker-track">
            ТУНДРА • СВЕЖЕЕ • БЕЗ КОНСЕРВАНТОВ{" "}
            <span className="ol-star">★</span>
          </div>
        </div>
        <p className="sg-note">
          При prefers-reduced-motion: reduce лента статична (animation: none).
        </p>
      </section>

      <section className="sg-section">
        <h2>Печать (Seal)</h2>
        <div style={{ display: "flex", gap: 20, alignItems: "center", flexWrap: "wrap" }}>
          <span className="ol-seal" aria-hidden="true" />
          <span className="ol-seal" data-variant="ink" style={{ width: 64, height: 64 }} aria-hidden="true" />
          <span className="ol-seal" data-variant="white" style={{ width: 64, height: 64 }} aria-hidden="true" />
        </div>
      </section>

      <section className="sg-section">
        <h2>Карточки</h2>
        <div className="sg-grid">
          <article className="ol-card" style={{ height: 420 }}>
            <div className="ol-card-photo" style={{ aspectRatio: "4/5" }}>
              <div className="ol-skeleton circle" style={{ width: 90, height: 112, margin: "auto" }} />
            </div>
            <div className="ol-card-body">
              <span className="ol-badge" data-type="stock">В наличии</span>
              <h3 className="ol-card-name">Сыровяленая оленина</h3>
              <p className="ol-card-meta">Упаковка 200 г · Воркута</p>
              <div className="ol-card-price">1 450 ₽</div>
              <button className="ol-btn" data-variant="primary">
                В корзину
              </button>
            </div>
          </article>
          <article className="ol-card" data-state="empty" style={{ height: 420, opacity: 0.55 }}>
            <div className="ol-card-photo" style={{ aspectRatio: "4/5" }}>
              <div className="ol-skeleton circle" style={{ width: 90, height: 112, margin: "auto" }} />
            </div>
            <div className="ol-card-body">
              <span className="ol-badge" data-type="out">Нет в наличии</span>
              <h3 className="ol-card-name">Сыровяленая оленина</h3>
              <button className="ol-btn" data-variant="primary" disabled>
                Сообщить о поступлении
              </button>
            </div>
          </article>
          <article className="ol-card" style={{ height: 420 }}>
            <div className="ol-card-photo" style={{ aspectRatio: "4/5" }}>
              <img
                src="/brand/logo-emblem.svg"
                alt=""
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            </div>
            <div className="ol-card-body">
              <span className="ol-old-price">1 790 ₽</span>
              <h3 className="ol-card-name">Оленина марбловая</h3>
              <div className="ol-card-price">1 450 ₽</div>
              <button className="ol-btn" data-variant="primary">
                В корзину
              </button>
            </div>
          </article>
          <article className="ol-card" style={{ height: 420 }}>
            <div className="ol-category-photo" style={{ aspectRatio: "3/4" }}>
              <div className="ol-skeleton" style={{ width: "100%", height: "100%" }} />
              <div className="ol-category-name-overlay">
                <h3>Заготовки</h3>
                <span className="ol-category-count">12</span>
              </div>
            </div>
            <button className="ol-btn" data-variant="primary">
              Выбрать
            </button>
          </article>
        </div>
      </section>

      <section className="sg-section">
        <h2>Корзина (Cart drawer, состояние open)</h2>
        <div className="ol-cart-drawer open" role="dialog" aria-modal="true" aria-label="Корзина">
          <div className="ol-cart-overlay" />
          <div className="ol-cart-panel">
            <div className="ol-cart-header">
              <h3>Корзина</h3>
              <button className="ol-btn" data-variant="ghost">Закрыть</button>
            </div>
            <div className="ol-cart-list">
              <div className="ol-cart-row">
                <div className="ol-cart-img" style={{ background: "var(--ol-color-ink-850)" }} />
                <div className="ol-cart-info">
                  <div className="ol-cart-name">Сыровяленая оленина, 200 г</div>
                  <div className="ol-cart-price">1 450 ₽</div>
                </div>
                <div className="ol-cart-qty">
                  <button className="ol-chip" type="button">
                    −
                  </button>
                  <span>2</span>
                  <button className="ol-chip" type="button">+</button>
                </div>
              </div>
              <div className="ol-cart-row">
                <div className="ol-skeleton circle" style={{ width: 56, height: 56 }} />
                <div className="ol-cart-info">
                  <div className="ol-cart-name">Мороженая печень, 500 г</div>
                  <div className="ol-cart-price">890 ₽</div>
                </div>
                <div className="ol-cart-qty">
                  <button className="ol-chip" type="button">−</button>
                  <span>1</span>
                  <button className="ol-chip" type="button">+</button>
                </div>
              </div>
            </div>
            <div className="ol-cart-total">
              <div>Итого</div>
              <div>3 790 ₽</div>
            </div>
          </div>
        </div>
        <p className="sg-note">
          Выезжает справа (z-drawer = 30). При reduced-motion анимация выезда отключена.
        </p>
      </section>

      <section className="sg-section">
        <h2>Тост (Toast)</h2>
        <div className="ol-toast" data-state="visible" role="status" aria-live="polite">
          Добавлено в корзину: сыровяленая оленина
        </div>
        <p className="sg-note">Автоскрытие через ~4 с, z-index toast = 50.</p>
      </section>

      <section className="sg-section">
        <h2>Модалки (Modal / Sheet)</h2>
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "start" }}>
          <div className="ol-modal open">
            <div className="ol-modal-overlay" />
            <div className="ol-modal-panel">
              <button className="ol-btn" data-variant="ghost" style={{ float: "right", marginBottom: 8 }}>
                ×
              </button>
              <h3>Подтвердите заказ</h3>
              <p>Оформить заказ на 3 790 ₽ с доставкой в Воркуту?</p>
              <button className="ol-btn" data-variant="primary" style={{ marginTop: 12 }}>
                Оформить
              </button>
            </div>
          </div>
          <div className="ol-sheet open">
            <div className="ol-sheet-overlay" />
            <div className="ol-sheet-panel">
              <button className="ol-btn" data-variant="ghost" style={{ float: "right", marginBottom: 8 }}>
                ×
              </button>
              <h3>Выберите город</h3>
              <p>Доставка доступна в Воркуте и Сыктывкаре.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="sg-section">
        <h2>Выбор города (City picker)</h2>
        <div className="ol-city-picker open" role="dialog" aria-modal="true" aria-label="Выбор города">
          <div className="ol-city-overlay" />
          <div className="ol-city-panel">
            <div className="ol-city-header">
              <h3>Выберите город</h3>
              <button className="ol-btn" data-variant="ghost">Закрыть</button>
            </div>
            <div className="ol-field ol-city-search">
              <label className="ol-label">Поиск города</label>
              <input className="ol-input" placeholder="Воркута, Сыктывкар…" />
            </div>
            <div className="ol-city-list">
              <button className="ol-city-item selected" type="button">
                <span className="ol-city-name">Воркута</span>
                <span className="ol-city-status">Доставка завтра</span>
              </button>
              <button className="ol-city-item" type="button">
                <span className="ol-city-name">Сыктывкар</span>
                <span className="ol-city-region">Республика Коми</span>
                <span className="ol-city-status">Самовывоз сегодня</span>
              </button>
              <button className="ol-city-item" type="button">
                Другой город / доставка по России
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="sg-section">
        <h2>Скелетоны (Skeleton)</h2>
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <div className="ol-skeleton circle" style={{ width: 48, height: 48 }} />
          <div className="ol-skeleton" style={{ width: 120, height: 16 }} />
          <div className="ol-skeleton" style={{ width: 240, height: 200 }} />
          <div className="ol-skeleton circle" style={{ width: 96, height: 96 }} />
        </div>
        <p className="sg-note">Шиммер отключен при prefers-reduced-motion: reduce.</p>
      </section>

      <section className="sg-section">
        <h2>Пустое состояние (Empty state)</h2>
        <div className="ol-empty">
          <span className="ol-seal" data-variant="white" style={{ width: 88, height: 88 }} />
          <h3>Тут пока ничего нет</h3>
          <p>Добавьте первые товары из каталога.</p>
          <button className="ol-btn" data-variant="primary">
            Перейти в каталог
          </button>
        </div>
      </section>

      <section className="sg-section">
        <h2>Таблица админки (default / loading / error / empty)</h2>
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          <div style={{ maxWidth: 560 }}>
            <h3>Заказы</h3>
            <div className="ol-admin-table">
              <div className="ol-admin-table-header" style={{ gridTemplateColumns: "1fr 1fr 1fr 100px 120px" }}>
                <div>№ заказа</div>
                <div>Город</div>
                <div>Статус</div>
                <div className="ol-mono">Сумма</div>
                <div className="ol-mono">Дата</div>
              </div>
              <div className="ol-admin-table-body">
                <div className="ol-admin-table-row">
                  <div className="ol-mono">#00142</div>
                  <div>Воркута</div>
                  <div>Сборка</div>
                  <div className="ol-mono">3 790 ₽</div>
                  <div className="ol-mono">14:32</div>
                </div>
                <div className="ol-admin-table-row">
                  <div className="ol-mono">#00141</div>
                  <div>Сыктывкар</div>
                  <div>Новый</div>
                  <div className="ol-mono">1 250 ₽</div>
                  <div className="ol-mono">14:10</div>
                </div>
              </div>
            </div>
          </div>
          <div style={{ maxWidth: 300 }}>
            <h3>Пусто</h3>
            <div className="ol-empty" style={{ padding: 20, background: "transparent" }}>
              <h3 style={{ fontSize: 16, textTransform: "none", fontFamily: "var(--ol-font-family-text)" }}>
                Записей нет
              </h3>
            </div>
          </div>
        </div>
        <p className="sg-note">В реальной админке здесь сортировка, фильтры и переходы статусов.</p>
      </section>

      <section className="sg-section">
        <h2>Reduced motion</h2>
        <p>
          Все декоративные анимации (лента, шиммер скелетонов, выезд корзины, модалки) отключаются при
          <code>prefers-reduced-motion: reduce</code>. Компоненты анимации{" "}
          <code>packages/motion</code> проверяют <code>matchMedia</code>. Проверка: включите
          «Уменьшение движения» в настройках ОС — анимации остановятся.
        </p>
      </section>
    </div>
  )
}
