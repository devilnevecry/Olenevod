import React from "react"
import "./olenevod.css"
import { Seal } from "./seal"

export interface EmptyStateProps {
  className?: string
  title: string
  description?: string
  ctaLabel?: string
  onCta?: () => void
}

export const EmptyState = React.forwardRef<HTMLDivElement, EmptyStateProps>(
  ({ className, title, description, ctaLabel, onCta }, ref) => (
    <div ref={ref} className={["ol-empty", className].filter(Boolean).join(" ")} data-state="empty">
      <Seal variant="default" />
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {ctaLabel && (
        <button type="button" className="ol-btn" data-variant="primary" onClick={onCta}>
          {ctaLabel}
        </button>
      )}
    </div>
  )
)
EmptyState.displayName = "EmptyState"
