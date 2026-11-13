import React from "react"
import "./olenevod.css"

export interface ChipProps extends React.HTMLAttributes<HTMLSpanElement> {
  selected?: boolean
  count?: number
}

export const Chip = React.forwardRef<HTMLSpanElement, ChipProps>(
  ({ className, selected = false, count, children, ...rest }, ref) => (
    <span
      ref={ref}
      className={["ol-chip", className].filter(Boolean).join(" ")}
      data-state={selected ? "selected" : "default"}
      role={rest.role ?? "button"}
      aria-pressed={selected}
      {...rest}
    >
      {children}
      {count != null && <span className="ol-chip-count">{count}</span>}
    </span>
  )
)
Chip.displayName = "Chip"
