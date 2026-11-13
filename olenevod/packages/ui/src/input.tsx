import React from "react"
import "./olenevod.css"

export interface FieldProps extends React.HTMLAttributes<HTMLDivElement> {
  label?: string
  error?: string
  state?: "default" | "error"
}

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, ...rest }, ref) => (
    <div className={["ol-field", className].filter(Boolean).join(" ")} data-state={error ? "error" : "default"}>
      {label && <label className="ol-label">{label}</label>}
      <input
        ref={ref}
        className="ol-input"
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? undefined : rest["aria-describedby"]}
        {...rest}
      />
      {error && <p className="ol-error-text" id="ol-error">{error}</p>}
    </div>
  )
)
Input.displayName = "Input"

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, children, ...rest }, ref) => (
    <div className={["ol-field", className].filter(Boolean).join(" ")} data-state={error ? "error" : "default"}>
      {label && <label className="ol-label">{label}</label>}
      <select ref={ref} className="ol-select" aria-invalid={error ? true : undefined} {...rest}>
        {children}
      </select>
      {error && <p className="ol-error-text">{error}</p>}
    </div>
  )
)
Select.displayName = "Select"

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, ...rest }, ref) => (
    <div className={["ol-field", className].filter(Boolean).join(" ")} data-state={error ? "error" : "default"}>
      {label && <label className="ol-label">{label}</label>}
      <textarea ref={ref} className="ol-textarea" aria-invalid={error ? true : undefined} {...rest} />
      {error && <p className="ol-error-text">{error}</p>}
    </div>
  )
)
Textarea.displayName = "Textarea"
