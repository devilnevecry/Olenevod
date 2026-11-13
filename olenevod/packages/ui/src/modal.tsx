import React from "react"
import "./olenevod.css"

export interface ModalProps extends React.HTMLAttributes<HTMLDivElement> {
  open: boolean
  onClose: () => void
}

export const Modal = React.forwardRef<HTMLDivElement, ModalProps>(
  ({ className, open, onClose, children, ...rest }, ref) => (
    <div
      ref={ref}
      className={["ol-modal", className, open ? "open" : ""].filter(Boolean).join(" ")}
      hidden={!open}
      role="dialog"
      aria-modal="true"
      {...rest}
    >
      <div className="ol-modal-overlay" onClick={onClose} />
      <div className="ol-modal-panel" onClick={(e) => e.stopPropagation()}>
        <button type="button" className="ol-btn" data-variant="ghost" onClick={onClose} aria-label="Закрыть">×</button>
        {children}
      </div>
    </div>
  )
)
Modal.displayName = "Modal"

export interface SheetProps extends ModalProps {}

export const Sheet = React.forwardRef<HTMLDivElement, SheetProps>(
  ({ className, open, onClose, children, ...rest }, ref) => (
    <div
      ref={ref}
      className={["ol-sheet", className, open ? "open" : ""].filter(Boolean).join(" ")}
      hidden={!open}
      role="dialog"
      aria-modal="true"
      {...rest}
    >
      <div className="ol-sheet-overlay" onClick={onClose} />
      <div className="ol-sheet-panel" onClick={(e) => e.stopPropagation()}>
        <button type="button" className="ol-btn" data-variant="ghost" onClick={onClose} aria-label="Закрыть">×</button>
        {children}
      </div>
    </div>
  )
)
Sheet.displayName = "Sheet"
