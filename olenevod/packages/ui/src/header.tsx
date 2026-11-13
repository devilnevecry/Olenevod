import React from "react"
import "./olenevod.css"

export interface HeaderProps {
  className?: string
  cartCount?: number
  city?: string
  children?: React.ReactNode
}

export const Header = React.forwardRef<HTMLDivElement, HeaderProps>(
  ({ className, cartCount = 0, city, children, ...rest }, ref) => (
    <header ref={ref} className={["ol-header", className].filter(Boolean).join(" ")} {...rest}>
      <div className="ol-brand">
        <span className="ol-seal" style={{ width: 40, height: 40 }} aria-hidden="true" />
        <span className="ol-wordmark">Оленевод</span>
      </div>
      <nav className="ol-nav">
        <a href="/catalog">Каталог</a>
        {children}
      </nav>
      <div className="ol-city-cart">
        <button type="button" className="ol-chip" aria-label="Выбрать город">
          {city ?? "Город"} <span style={{ marginLeft: 6 }} aria-hidden="true">▾</span>
        </button>
        <button type="button" className="ol-cart" aria-label={`Корзина, ${cartCount} товаров`}>
          Корзина <span aria-hidden="true">{cartCount > 0 ? `· ${cartCount}` : ""}</span>
        </button>
      </div>
    </header>
  )
)
Header.displayName = "Header"
