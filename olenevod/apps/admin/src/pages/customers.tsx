import React, { useCallback, useEffect, useState } from "react";
import { get, patch } from "../api";
import { Button } from "../components/Button";
import { Input } from "../components/Input";
import { Dialog } from "../components/Dialog";

interface Customer {
  id: string;
  email: string;
  phone: string | null;
  name: string;
  is_verified: boolean;
}

export default function CustomersPage() {
  const [items, setItems] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cardOpen, setCardOpen] = useState(false);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [form, setForm] = useState({ phone: "", name: "" });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await get<Customer[]>("/admin/customers");
      setItems(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(String(e) || "Ошибка загрузки покупателей");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const openCard = (c: Customer) => {
    setCustomer(c);
    setForm({ phone: c.phone ?? "", name: c.name });
    setCardOpen(true);
  };

  const save = async () => {
    if (!customer) return;
    try {
      await patch(`/admin/customers/${customer.id}`, { phone: form.phone, name: form.name });
      setCustomer((c) => (c ? { ...c, phone: form.phone, name: form.name } : null));
      await load();
    } catch (e: any) {
      setError(String(e) || "Ошибка сохранения");
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Покупатели</h2>
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
              <th style={{ ...thStyle }}>E-mail</th>
              <th style={{ ...thStyle }}>Телефон</th>
              <th style={{ ...thStyle }}>Имя</th>
              <th style={{ ...thStyle }}>Верифицирован</th>
              <th style={{ ...thStyle, width: 120 }}>Действие</th>
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
              items.map((c) => (
                <tr key={c.id} style={{ ...trStyle }}>
                  <td style={tdStyle}>{c.id}</td>
                  <td style={tdStyle}>{c.email}</td>
                  <td style={tdStyle}>{c.phone ?? "-"}</td>
                  <td style={tdStyle}>{c.name}</td>
                  <td style={tdStyle}>{c.is_verified ? "Да" : "Нет"}</td>
                  <td style={tdStyle}>
                    <Button variant="ghost" onClick={() => openCard(c)} style={{ fontSize: 12, padding: "4px 8px" }}>
                      Карточка
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <Dialog open={cardOpen} onClose={() => setCardOpen(false)} title={`Покупатель ${customer?.id ?? ""}`}>
        <form
          onSubmit={(e) => { e.preventDefault(); save(); }}
          style={{ display: "flex", flexDirection: "column", gap: 10 }}
        >
          <Input
            label="E-mail"
            value={customer?.email ?? ""}
            onChange={(e) => setForm({ ...form, phone: form.phone })}
            disabled
          />
          <Input
            label="Телефон"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
          />
          <Input
            label="Имя"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <Button type="submit" variant="primary">
            Сохранить
          </Button>
        </form>
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
