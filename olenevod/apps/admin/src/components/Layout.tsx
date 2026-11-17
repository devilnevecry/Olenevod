import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "./Button";

const SECTIONS: { to: string; label: string }[] = [
  { to: "/cities", label: "Города" },
  { to: "/warehouses", label: "Склады" },
  { to: "/products", label: "Товары" },
  { to: "/variants", label: "Варианты" },
  { to: "/offers", label: "Предложения" },
  { to: "/stock", label: "Остатки" },
  { to: "/transfers", label: "Перемещения" },
  { to: "/routes", label: "Маршруты" },
  { to: "/carriers", label: "Перевозчики" },
  { to: "/orders", label: "Заказы" },
  { to: "/customers", label: "Покупатели" },
];

export interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const token = localStorage.getItem("admin_token");

  const handleLogout = () => {
    localStorage.removeItem("admin_token");
    navigate("/login");
  };

  const sidebarStyle: React.CSSProperties = {
    position: "fixed",
    top: 0,
    bottom: 0,
    left: 0,
    width: 220,
    background: "#111827",
    color: "#fff",
    paddingTop: 16,
    paddingBottom: 16,
    boxShadow: "2px 0 4px rgba(0,0,0,0.05)",
  };
  const contentStyle: React.CSSProperties = { marginLeft: 220, padding: 24 };
  const brandStyle: React.CSSProperties = {
    fontSize: 16,
    fontWeight: 800,
    marginBottom: 24,
    padding: "0 16px",
    letterSpacing: -0.5,
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside style={sidebarStyle}>
        <div style={brandStyle}>Olenevod Admin</div>
        <nav style={{ padding: "0 8px" }}>
          {SECTIONS.map((s) => {
            const active = location.pathname === s.to || location.pathname.startsWith(s.to + "/");
            return (
              <Link
                key={s.to}
                to={s.to}
                style={{
                  display: "block",
                  padding: "8px 12px",
                  borderRadius: 6,
                  marginBottom: 4,
                  color: active ? "#fff" : "#cbd5e1",
                  textDecoration: "none",
                  fontSize: 14,
                  fontWeight: active ? 700 : 400,
                  background: active ? "#374151" : "transparent",
                }}
              >
                {s.label}
              </Link>
            );
          })}
          <hr style={{ border: 0, borderTop: "1px solid #374151", margin: "16px 8px" }} />
          <Button
            variant="ghost"
            onClick={handleLogout}
            style={{ width: "100%", marginTop: 8, color: "#cbd5e1", borderColor: "#374151" }}
          >
            Выйти
          </Button>
        </nav>
      </aside>
      <main style={contentStyle}>{children}</main>
    </div>
  );
}
