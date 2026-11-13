import React from "react"
import "./olenevod.css"

export interface ToastProps {
  className?: string
  message: string
  visible?: boolean
  onDismiss?: () => void
}

export const Toast = React.forwardRef<HTMLDivElement, ToastProps>(
  ({ className, message, visible = false, onDismiss }, ref) => (
    <div
      ref={ref}
      className={["ol-toast", className].filter(Boolean).join(" ")}
      data-state={visible ? "visible" : "default"}
      role="status"
      aria-live="polite"
    >
      {message}
      {visible && onDismiss && (
        <button type="button" className="ol-btn" data-variant="ghost" onClick={onDismiss} style={{ marginLeft: 10 }}>
          Закрыть
        </button>
      )}
    </div>
  )
)
Toast.displayName = "Toast"
