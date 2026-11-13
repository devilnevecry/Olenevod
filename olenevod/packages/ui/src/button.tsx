import React from "react"
import "./olenevod.css"

export type ButtonVariant = "primary" | "secondary" | "ghost"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  loading?: boolean
  className?: string
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", loading = false, children, ...rest }, ref) => {
    const state = loading ? "loading" : "default"
    return (
      <button
        ref={ref}
        type="button"
        className={["ol-btn", className].filter(Boolean).join(" ")}
        data-variant={variant}
        data-state={state}
        disabled={rest.disabled || loading}
        {...rest}
      >
        <span className="ol-btn-label">{children}</span>
        <span className="ol-btn-spinner" aria-hidden="true" />
      </button>
    )
  }
)
Button.displayName = "Button"
