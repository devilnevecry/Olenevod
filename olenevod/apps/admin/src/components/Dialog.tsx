import React from "react";
import { Button } from "./Button";

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function Dialog({ open, onClose, title, children }: DialogProps) {
  if (!open) return null;
  const overlayStyle: React.CSSProperties = {
    position: "fixed",
    inset: 0,
    zIndex: 50,
    background: "rgba(0,0,0,0.45)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  };
  const panelStyle: React.CSSProperties = {
    background: "#fff",
    borderRadius: 8,
    padding: 24,
    minWidth: 420,
    maxWidth: 700,
    maxHeight: "85vh",
    overflow: "auto",
    boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1)",
  };
  return (
    <div style={overlayStyle} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={panelStyle} onClick={(e) => e.stopPropagation()}>
        <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, marginBottom: 16 }}>{title}</h2>
        {children}
      </div>
    </div>
  );
}

export function Confirm({
  open,
  onConfirm,
  onCancel,
  title = "Подтвердите действие",
  message,
}: {
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  title?: string;
  message?: string;
}) {
  if (!open) return null;
  return (
    <Dialog open={open} onClose={onCancel} title={title}>
      <p style={{ margin: 0, marginBottom: 16 }}>{message}</p>
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
        <Button variant="ghost" onClick={onCancel}>
          Отмена
        </Button>
        <Button variant="danger" onClick={onConfirm}>
          Удалить
        </Button>
      </div>
    </Dialog>
  );
}
