import React from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "danger" | "ghost";
}

const baseStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  borderRadius: 6,
  border: "1px solid #cbd5e1",
  padding: "6px 12px",
  fontSize: 14,
  fontWeight: 500,
  cursor: "pointer",
  transition: "background 0.15s",
};
const variants: Record<string, React.CSSProperties> = {
  primary: { background: "#111827", color: "#fff", borderColor: "#111827" },
  danger: { background: "#fff", color: "#b91c1c", borderColor: "#fca5a5" },
  ghost: { background: "transparent", color: "#374151", borderColor: "transparent" },
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", className, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        style={{ ...baseStyle, ...variants[variant] }}
        disabled={disabled}
        {...props}
      >
        {props.children}
      </button>
    );
  },
);
Button.displayName = "Button";
