import React, { useCallback, useEffect, useState } from "react";
import { del, get, patch } from "../api";
import { Button } from "../components/Button";

interface StockLevel {
  warehouse_id: string;
  variant_id: string;
  on_hand: number;
  reserved: number;
}

export default function StockPage() {
  const [items, setItems] = useState<StockLevel[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [edits, setEdits] = useState<Record<string, { on_hand: string; reserved: string }>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await get<StockLevel[]>("/admin/stock");
      setItems(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(String(e) || "Ошибка загрузки остатков");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const setField = (key: string, field: "on_hand" | "reserved", value: string) => {
    setEdits((prev) => ({ ...prev, [key]: { ...(prev[key] ?? { on_hand: "", reserved: "" }), [field]: value } }));
  };

  const saveRow = async (item: StockLevel) => {
    const key = `${item.warehouse_id}:${item.variant_id}`;
    const e = edits[key];
    try {
      await patch(`/admin/stock/${item.warehouse_id}/${item.variant_id}`, {
        on_hand: Number(e.on_hand),
        reserved: Number(e.reserved),
      });
      setEdits((prev) => { const n = { ...prev }; delete n[key]; return n; });
      await load();
    } catch (err: any) {
      setError(String(err) || "Ошибка сохранения остатка");
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Остатки товара на складах</h2>
      {error && (
        <div style={{ color: "#b91c1c", background: "#fee2e2", padding: 8, borderRadius: 6 }}>
          {error}
        </div>
      )}
      <div style={{ border: "1px solid #e2e8f0", borderRadius: 6, overflow: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ ...thStyle }}>Склад (ID)</th>
              <th style={{ ...thStyle }}>Вариант (ID)</th>
              <th style={{ ...thStyle }}>on_hand</th>
              <th style={{ ...thStyle }}>reserved</th>
              <th style={{ ...thStyle }}>доступно</th>
              <th style={{ ...thStyle, width: 120 }}>Сохранить</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ ...tdStyle, textAlign: "center", color: "#64748b", padding: 16 }}>
                  Нет данных
                </td>
              </tr>
            ) : (
              items.map((item) => {
                const key = `${item.warehouse_id}:${item.variant_id}`;
                const e = edits[key] ?? { on_hand: String(item.on_hand), reserved: String(item.reserved) };
                return (
                  <tr key={key} style={{ ...trStyle }}>
                    <td style={tdStyle}>{item.warehouse_id}</td>
                    <td style={tdStyle}>{item.variant_id}</td>
                    <td style={tdStyle}>
                      <input
                        value={e.on_hand}
                        onChange={(ev) => setField(key, "on_hand", ev.target.value)}
                        style={inputStyle}
                      />
                    </td>
                    <td style={tdStyle}>
                      <input
                        value={e.reserved}
                        onChange={(ev) => setField(key, "reserved", ev.target.value)}
                        style={inputStyle}
                      />
                    </td>
                    <td style={tdStyle}>
                      <Badge variant="default">{Math.max(0, Number(item.on_hand) - Number(item.reserved))}</Badge>
                    </td>
                    <td style={tdStyle}>
                      <Button variant="primary" onClick={() => saveRow(item)} style={{ fontSize: 12, padding: "4px 8px" }}>
                        Сохранить
                      </Button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  background: "#f8fafc",
  borderBottom: "1px solid #e2e8f0",
  textAlign: "left",
  fontSize: 12,
  fontWeight: 700,
  color: "#475569",
  padding: "8px 10px",
};
const tdStyle: React.CSSProperties = { padding: "8px 10px", borderBottom: "1px solid #e2e8f0", fontSize: 13 };
const trStyle: React.CSSProperties = {};
const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "4px 6px",
  fontSize: 13,
  border: "1px solid #cbd5e1",
  borderRadius: 4,
};
function Badge({ children, variant = "default" }: { children: React.ReactNode; variant?: string }) {
  const styles: Record<string, React.CSSProperties> = {
    default: { background: "#e5e7eb", color: "#374151" },
    success: { background: "#dcfce7", color: "#166534" },
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
