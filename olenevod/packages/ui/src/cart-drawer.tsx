import React from "react"
import "./olenevod.css"

export interface CartItem {
  id: string
  image?: string
  name: string
  price: number
  qty: number
}

export interface CartDrawerProps {
  className?: string
  open: boolean
  onClose: () => void
  items: CartItem[]
  total: number
  onRemove: (id: string) => void
  onChangeQty: (id: string, delta: number) => void
}

export const CartDrawer = React.forwardRef<HTMLDivElement, CartDrawerProps>(
  ({ className, open, onClose, items, total, onRemove, onChangeQty }, ref) => {
    const format = (n: number) => n.toLocaleString("ru-RU")
    return (
      <div
        ref={ref}
        className={["ol-cart-drawer", className, open ? "open" : ""].filter(Boolean).join(" ")}
        hidden={!open}
        role="dialog"
        aria-modal="true"
        aria-label="Корзина"
      >
        <div className="ol-cart-overlay" onClick={onClose} />
        <div className="ol-cart-panel">
          <div className="ol-cart-header">
            <h3>Корзина</h3>
            <button type="button" className="ol-btn" data-variant="ghost" onClick={onClose}>
              Закрыть
            </button>
          </div>
          <div className="ol-cart-list">
            {items.length === 0 ? (
              <div className="ol-empty" style={{ padding: 24 }}>
                <h3 style={{ fontSize: "16px", fontFamily: "var(--ol-font-family-text)", textTransform: "none" }}>
                  Корзина пуста
                </h3>
              </div>
            ) : (
              items.map((item) => (
                <div key={item.id} className="ol-cart-row">
                  {item.image ? (
                    <img src={item.image} alt={item.name} className="ol-cart-img" />
                  ) : (
                    <div className="ol-skeleton circle" style={{ width: 56, height: 56 }} />
                  )}
                  <div className="ol-cart-info">
                    <div className="ol-cart-name">{item.name}</div>
                    <div className="ol-cart-price">{format(item.price)} ₽</div>
                  </div>
                  <div className="ol-cart-qty">
                    <button type="button" className="ol-chip" onClick={() => onChangeQty(item.id, -1)}>−</button>
                    {item.qty}
                    <button type="button" className="ol-chip" onClick={() => onChangeQty(item.id, 1)}>+</button>
                    <button type="button" className="ol-btn" data-variant="ghost" onClick={() => onRemove(item.id)} title="Удалить">×</button>
                  </div>
                </div>
              ))
            )}
          </div>
          <div className="ol-cart-total">
            <div>Итого</div>
            <div style={{ fontWeight: 700 }}>{format(total)} ₽</div>
          </div>
        </div>
      </div>
    )
  }
)
CartDrawer.displayName = "CartDrawer"
