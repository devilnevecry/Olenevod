import React from "react";

export interface Option {
  value: string;
  label: string;
}

export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "onChange"> {
  label?: string;
  options: Option[];
  value: string;
  onChange: (value: string) => void;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(({ label, options, value, onChange, ...rest }, ref) => {
  const selectStyle: React.CSSProperties = {
    width: "100%",
    padding: "6px 10px",
    fontSize: 14,
    border: "1px solid #cbd5e1",
    borderRadius: 6,
    outline: "none",
    background: "#fff",
  };
  return (
    <div style={{ marginBottom: 12 }}>
      {label && (
        <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 4, color: "#374151" }}>
          {label}
        </label>
      )}
      <select ref={ref} value={value} onChange={(e) => onChange(e.target.value)} style={selectStyle} {...rest}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
});
Select.displayName = "Select";

export function Badge({ children, variant = "default" }: { children: React.ReactNode; variant?: "default" | "success" | "warning" | "danger" }) {
  const styles: Record<string, React.CSSProperties> = {
    default: { background: "#e5e7eb", color: "#374151" },
    success: { background: "#dcfce7", color: "#166534" },
    warning: { background: "#fef3c7", color: "#92400e" },
    danger: { background: "#fee2e2", color: "#991b1b" },
  };
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 9999,
        fontSize: 12,
        fontWeight: 600,
        ...styles[variant],
      }}
    >
      {children}
    </span>
  );
}
