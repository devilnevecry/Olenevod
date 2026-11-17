import React, { useCallback, useEffect, useState } from "react";
import { get, post } from "../api";
import { Button } from "../components/Button";
import { Input } from "../components/Input";
import { Select } from "../components/Select";
import { Dialog } from "../components/Dialog";

interface Transfer {
  id: string;
  from_warehouse_id: string;
  to_warehouse_id: string;
  status: string;
}

interface TransferItem {
  transfer_id: string;
  variant_id: string;
  qty: number;
  received_qty: number | null;
}

export default function TransfersPage() {
  const [items, setItems] = useState<Transfer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ from_warehouse_id: "", to_warehouse_id: "", status: "draft" });
  const [itemsOpen, setItemsOpen] = useState(false);
  const [transferItems, setTransferItems] = useState<TransferItem[]>([]);
  const [currentTransfer, setCurrentTransfer] = useState<Transfer | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await get<Transfer[]>("/admin/transfers");
      setItems(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(String(e) || "Ошибка загрузки перемещений");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const loadItems = async (id: string) => {
    try {
      const data = await get<TransferItem[]>(`/admin/transfers/${id}/items`);
      setTransferItems(Array.isArray(data) ? data : []);
      setCurrentTransfer(items.find((t) => t.id === id) ?? null);
      setItemsOpen(true);
    } catch (e: any) {
      setError(String(e) || "Ошибка загрузки позиций");
    }
  };

  const handleSave = async () => {
    try {
      await post("/admin/transfers", {
        from_warehouse_id: form.from_warehouse_id,
        to_warehouse_id: form.to_warehouse_id,
        status: form.status,
      });
      setOpen(false);
      setForm({ from_warehouse_id: "", to_warehouse_id: "", status: "draft" });
      await load();
    } catch (e: any) {
      setError(String(e) || "Ошибка создания перемещения");
    }
  };

  const statusStyle: Record<string, React.CSSProperties> = {
    draft: { background: "#e5e7eb", color: "#374151" },
    in_transit: { background: "#dbeafe", color: "#1e40af" },
    received: { background: "#dcfce7", color: "#166534" },
    cancelled: { background: "#fee2e2", color: "#991b1b" },
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Перемещения стока</h2>
        <Button variant="primary" onClick={() => setOpen(true)}>
          Новое перемещение
        </Button>
      </div>
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
              <th style={{ ...thStyle }}>От склада</th>
              <th style={{ ...thStyle }}>На склад</th>
              <th style={{ ...thStyle }}>Статус</th>
              <th style={{ ...thStyle, width: 120 }}>Позиции</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ ...tdStyle, textAlign: "center", color: "#64748b", padding: 16 }}>
                  Нет данных
                </td>
              </tr>
            ) : (
              items.map((t) => (
                <tr key={t.id} style={{ ...trStyle }}>
                  <td style={tdStyle}>{t.id}</td>
                  <td style={tdStyle}>{t.from_warehouse_id}</td>
                  <td style={tdStyle}>{t.to_warehouse_id}</td>
                  <td style={tdStyle}>
                    <span style={{ ...statusStyle[t.status], padding: "2px 8px", borderRadius: 9999, fontSize: 12, fontWeight: 600 }}>
                      {t.status}
                    </span>
                  </td>
                  <td style={tdStyle}>
                    <Button variant="ghost" onClick={() => loadItems(t.id)} style={{ fontSize: 12, padding: "4px 8px" }}>
                      Позиции
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <Dialog open={open} onClose={() => setOpen(false)} title="Новое перемещение">
        <form
          onSubmit={(e) => { e.preventDefault(); handleSave(); }}
          style={{ display: "flex", flexDirection: "column", gap: 10 }}
        >
          <Input label="От склада (ID)" value={form.from_warehouse_id} onChange={(e) => setForm({ ...form, from_warehouse_id: e.target.value })} />
          <Input label="На склад (ID)" value={form.to_warehouse_id} onChange={(e) => setForm({ ...form, to_warehouse_id: e.target.value })} />
          <Select
            label="Статус"
            value={form.status}
            onChange={(v) => setForm({ ...form, status: v })}
            options={[
              { value: "draft", label: "Черновик" },
              { value: "in_transit", label: "В пути" },
              { value: "received", label: "Получено" },
              { value: "cancelled", label: "Отменено" },
            ]}
          />
          <Button type="submit" variant="primary">
            Создать
          </Button>
        </form>
      </Dialog>
      <Dialog open={itemsOpen} onClose={() => setItemsOpen(false)} title={`Позиции перемещения${currentTransfer ? ` (${currentTransfer.id})` : ""}`}>
        <div style={{ border: "1px solid #e2e8f0", borderRadius: 6, overflow: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ ...thStyle }}>Вариант (ID)</th>
                <th style={{ ...thStyle }}>Количество</th>
                <th style={{ ...thStyle }}>Получено</th>
              </tr>
            </thead>
            <tbody>
              {transferItems.length === 0 ? (
                <tr>
                  <td colSpan={3} style={{ ...tdStyle, textAlign: "center", color: "#64748b", padding: 16 }}>
                    Нет позиций
                  </td>
                </tr>
              ) : (
                transferItems.map((it) => (
                  <tr key={`${it.transfer_id}:${it.variant_id}`} style={{ ...trStyle }}>
                    <td style={tdStyle}>{it.variant_id}</td>
                    <td style={tdStyle}>{it.qty}</td>
                    <td style={tdStyle}>{it.received_qty ?? "-"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
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
