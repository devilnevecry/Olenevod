import React from "react"
import "./olenevod.css"

export interface CategoryCardProps {
  className?: string
  image?: string
  name: string
  count?: number
  onPress?: () => void
}

export const CategoryCard = React.forwardRef<HTMLDivElement, CategoryCardProps>(
  ({ className, image, name, count, onPress }, ref) => (
    <article
      ref={ref}
      className={["ol-card", className].filter(Boolean).join(" ")}
      data-state="default"
    >
      <div className="ol-category-photo" style={{ aspectRatio: "3/4" }}>
        {image ? (
          <img src={image} alt={name} className="ol-category-img" loading="lazy" />
        ) : (
          <div className="ol-skeleton" style={{ width: "100%", height: "100%" }} />
        )}
        <div className="ol-category-name-overlay">
          <h3>{name}</h3>
          {count != null && <span className="ol-category-count">{count}</span>}
        </div>
      </div>
      <button type="button" className="ol-btn" data-variant="primary" onClick={onPress}>
        Выбрать категорию
      </button>
    </article>
  )
)
CategoryCard.displayName = "CategoryCard"
