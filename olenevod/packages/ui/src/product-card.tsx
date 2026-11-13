import React from "react"
import "./olenevod.css"

export interface ProductCardProps {
  className?: string
  image?: string
  name: string
  meta?: string
  price: number
  oldPrice?: number
  inStock?: boolean
  onAdd?: () => void
}

export const ProductCard = React.forwardRef<HTMLDivElement, ProductCardProps>(
  ({ className, image, name, meta, price, oldPrice, inStock = true, onAdd }, ref) => {
    const format = (n: number) => n.toLocaleString("ru-RU")
    return (
      <article
        ref={ref}
        className={["ol-card", className].filter(Boolean).join(" ")}
        data-state={inStock ? "default" : "empty"}
      >
        {image ? (
          <div className="ol-card-photo" style={{ aspectRatio: "4/5" }}>
            <img src={image} alt={name} className="ol-card-img" loading="lazy" />
          </div>
        ) : (
          <div className="ol-card-photo" style={{ aspectRatio: "4/5" }}>
            <div className="ol-skeleton circle" style={{ width: 56, height: 70 }} />
          </div>
        )}
        <div className="ol-card-body">
          {oldPrice && (
            <span className="ol-old-price">{format(oldPrice)} ₽</span>
          )}
          <h3 className="ol-card-name">{name}</h3>
          {meta && <p className="ol-card-meta">{meta}</p>}
          <div className="ol-card-price">{format(price)} ₽</div>
          {oldPrice && <span className="ol-old-price">{format(oldPrice)} ₽</span>}
          <button
            type="button"
            className="ol-btn"
            data-variant="primary"
            disabled={!inStock}
            onClick={onAdd}
          >
            {inStock ? "В корзину" : "Сообщить о поступлении"}
          </button>
        </div>
      </article>
    )
  }
)
ProductCard.displayName = "ProductCard"
