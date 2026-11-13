import React from "react"
import "./olenevod.css"

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  circle?: boolean
}

export const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, circle = false, ...rest }, ref) => (
    <div
      ref={ref}
      className={["ol-skeleton", circle ? "circle" : "", className].filter(Boolean).join(" ")}
      aria-hidden="true"
      {...rest}
    />
  )
)
Skeleton.displayName = "Skeleton"
