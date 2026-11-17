import React, { useCallback, useEffect, useState } from "react";
import { get, patch } from "../api";
import { Button } from "../components/Button";
import { Select } from "../components/Select";
import { Dialog } from "../components/Dialog";
import { Badge } from "../components/Select";

interface Order {
  id: string;
  city_id: string;
  customer_name: string;
  customer_phone: string;
  status: string;
  total_amount: number;
}

export default function OrdersPage() {
  const [items, setItems] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cardOpen, setCardOpen] = useState(false);
  const [order, setOrder] = useState<Order | null>(null);
  const [status, setStatus] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await get<Order[]>("/admin/orders");
      setItems(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(String(e) || "Ошибка загрузки заказов");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const openCard = (o: Order) => {
    setOrder(o);
    setStatus(o.status);
    setCardOpen(true);
  };

  const saveStatus = async () => {
    if (!order) return;
    try {
      await patch(`/admin/orders/${order.id}/status`, { status });
      setOrder((o) => (o ? { ...o, status } : null));
      await load();
    } catch (e: any) {
      setError(String(e) || "Ошибка смены статуса");
    }
  };

  const statusStyle: Record<string, React.CSSProperties> = {
    pending_payment: { background: "#e5e7eb", color: "#374151" },
    new: { background: "#dbeafe", color: "#1e40af" },
    paid: { background: "#dcfce7", color: "#166534" },
    cancelled: { background: "#fee2e2", color: "#991b1b" },
    shipped: { background: "#dbeafe", color: "#1e40af" },
    delivered: { background: "#dcfce7", color: "#166534" },
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Заказы</h2>
      {error && (
        <div style={{ color: "#b91c1c", background: "#fee2e2", padding: 8, borderRadius: 6 }}>
          {error}
        </div>
      )}
      <div style={{ border: "1px solid #e2e8f0", borderRadius: 6, overflow: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ ...thStyle }}>ID</th>
              <th style={{ ...thStyle }}>Город (ID)</th>
              <th style={{ ...thStyle }}>Покупатель</th>
              <th style={{ ...thStyle }}>Телефон</th>
              <th style={{ ...thStyle }}>Статус</th>
              <th style={{ ...thStyle }}>Сумма (коп)</th>
              <th style={{ ...thStyle, width: 120 }}>Действие</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ ...tdStyle, textAlign: "center", color: "#64748b", padding: 16 }}>
                  Нет данных
                </td>
              </tr>
            ) : (
              items.map((o) => (
                <tr key={o.id} style={{ ...trStyle }}>
                  <td style={tdStyle}>{o.id}</td>
                  <td style={tdStyle}>{o.city_id}</td>
                  <td style={tdStyle}>{o.customer_name}</td>
                  <td style={tdStyle}>{o.customer_phone}</td>
                  <td style={tdStyle}>
                    <span style={{ ...statusStyle[o.status], padding: "2px 8px", borderRadius: 9999, fontSize: 12, fontWeight: 600 }}>
                      {o.status}
                    </span>
                  </td>
                  <td style={tdStyle}>{o.total_amount}</td>
                  <td style={tdStyle}>
                    <Button variant="ghost" onClick={() => openCard(o)} style={{ fontSize: 12, padding: "4px 8px" }}>
                      Карточка
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <Dialog open={cardOpen} onClose={() => setCardOpen(false)} title={`Заказ ${order?.id ?? ""}`}>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: "#64748b" }}>Статус</label>
              <Select
                value={status}
                onChange={(v) => setStatus(v)}
                options={[
                  { value: "pending_payment", label: "Ожидает оплату" },
                  { value: "new", label: "Новый" },
                  { value: "paid", label: "Оплачен" },
                  { value: "shipped", label: "Отправлен" },
                  { value: "delivered", label: "Доставлен" },
                  { value: "cancelled", label: "Отменён" },
                ]}
              />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: "#64748b" }}>Сумма (коп)</label>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{order?.total_amount ?? "-"}</div>
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: "#64748b" }}>Покупатель</label>
            <div style={{ fontSize: 14 }}>{order?.customer_name ?? "-"}</div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: "#64748b" }}>Телефон</label>
            <div style={{ fontSize: 14 }}>{order?.customer_phone ?? "-"}</div>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <Button variant="primary" onClick={saveStatus} disabled={!order}>
              Сохранить статус
            </Button>
            <Button variant="ghost" onClick={() => setCardOpen(false)}>
              Закрыть
            </Button>
          </div>
        </div>
      </Dialog>
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
