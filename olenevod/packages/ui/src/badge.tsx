import React from "react"
import "./olenevod.css"

export type BadgeType = "stock" | "low" | "out" | "cold" | "demo"

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  type?: BadgeType
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, type = "stock", children, ...rest }, ref) => (
    <span
      ref={ref}
      className={["ol-badge", className].filter(Boolean).join(" ")}
      data-type={type}
      {...rest}
    >
      {children}
    </span>
  )
)
Badge.displayName = "Badge"
