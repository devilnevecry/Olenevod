import React from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(({ label, ...props }, ref) => {
  const inputStyle: React.CSSProperties = {
    width: "100%",
    padding: "6px 10px",
    fontSize: 14,
    border: "1px solid #cbd5e1",
    borderRadius: 6,
    outline: "none",
  };
  return (
    <div style={{ marginBottom: 12 }}>
      {label && (
        <label style={{ display: "block", fontSize: 13, fontWeight: 600, marginBottom: 4, color: "#374151" }}>
          {label}
        </label>
      )}
      <input ref={ref} style={inputStyle} {...props} />
    </div>
  );
});
Input.displayName = "Input";
