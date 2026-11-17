import React, { useCallback, useEffect, useState } from "react";
import { del, get, patch, post } from "../api";
import { Button } from "./Button";
import { Input } from "./Input";
import { Select } from "./Select";
import { Table } from "./Table";
import { Badge } from "./Select";
import { Dialog } from "./Dialog";
import { Confirm } from "./Dialog";

export interface Field {
  key: string;
  label: string;
  type: "text" | "number" | "boolean" | "select";
  options?: { value: string; label: string }[];
}

export interface CrudPageProps {
  title: string;
  path: string;
  columns: { key: string; label: string; render?: (item: any) => React.ReactNode }[];
  fields: Field[];
  idField: string;
  defaultForm: Record<string, any>;
  toPayload: (form: Record<string, any>) => any;
  itemToForm: (item: any) => Record<string, any>;
}

export function CrudPage({
  title,
  path,
  columns,
  fields,
  idField,
  defaultForm,
  toPayload,
  itemToForm,
}: CrudPageProps) {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<boolean>(false);
  const [itemId, setItemId] = useState<string | null>(null);
  const [form, setForm] = useState<Record<string, any>>({ ...defaultForm });
  const [delTarget, setDelTarget] = useState<{ id: string; label: string } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await get<any[]>(path);
      setItems(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(String(e) || "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = () => {
    setEditing(false);
    setForm({ ...defaultForm });
    setItemId(null);
    setOpen(true);
  };

  const handleEdit = (item: any) => {
    setEditing(true);
    setItemId(item[idField]);
    setForm(itemToForm(item));
    setOpen(true);
  };

  const handleSave = async () => {
    try {
      if (editing && itemId) {
        await patch(`${path}/${itemId}`, toPayload(form));
      } else {
        await post(path, toPayload(form));
      }
      setOpen(false);
      await load();
    } catch (e: any) {
      setError(String(e) || "Ошибка сохранения");
    }
  };

  const handleDelete = (id: string, label: string) => {
    setDelTarget({ id, label });
  };

  const handleConfirmDelete = async () => {
    if (!delTarget) return;
    try {
      await del(`${path}/${delTarget.id}`);
      setDelTarget(null);
      await load();
    } catch (e: any) {
      setError(String(e) || "Ошибка удаления");
    }
  };

  const renderCell = (item: any, col: { key: string; label: string; render?: (item: any) => React.ReactNode }) => {
    if (col.render) return col.render(item);
    const v = item[col.key];
    if (typeof v === "boolean") return <Badge variant={v ? "success" : "default"}>{v ? "Да" : "Нет"}</Badge>;
    return String(v ?? "-");
  };

  const formFields = fields.map((f) => {
    const value = form[f.key];
    let input: React.ReactNode;
    if (f.type === "boolean") {
      input = (
        <select
          value={String(value ?? false)}
          onChange={(e) => setForm({ ...form, [f.key]: e.target.value === "true" })}
          style={{ width: "100%", padding: "6px 10px", fontSize: 14, border: "1px solid #cbd5e1", borderRadius: 6 }}
        >
          <option value="true">Да</option>
          <option value="false">Нет</option>
        </select>
      );
    } else if (f.type === "select" && f.options) {
      input = (
        <Select
          key={f.key}
          label={f.label}
          value={String(value ?? "")}
          onChange={(v) => setForm({ ...form, [f.key]: v })}
          options={f.options}
        />
      );
    } else {
      input = (
        <Input
          key={f.key}
          label={f.label}
          value={String(value ?? "")}
          onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
          type={f.type === "number" ? "number" : "text"}
        />
      );
    }
    return input;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>{title}</h2>
        <Button variant="primary" onClick={handleCreate} style={{ marginLeft: "auto" }}>
          Добавить
        </Button>
      </div>
      {error && (
        <div style={{ color: "#b91c1c", background: "#fee2e2", padding: 8, borderRadius: 6, marginBottom: 8 }}>
          {error}
        </div>
      )}
      <Table
        columns={columns}
        data={items}
        onEdit={handleEdit}
        onDelete={(item) => handleDelete(item[idField], String(item.name ?? item.slug ?? item.id))}
      />
      <Dialog open={open} onClose={() => setOpen(false)} title={editing ? "Редактировать" : "Создать"}>
        <form
          onSubmit={(e) => { e.preventDefault(); handleSave(); }}
          style={{ display: "flex", flexDirection: "column", gap: 10 }}
        >
          {formFields}
          <Button type="submit" variant="primary">
            Сохранить
          </Button>
        </form>
      </Dialog>
      <Confirm
        open={!!delTarget}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDelTarget(null)}
        title="Удалить запись"
        message={`Удалить "${delTarget?.label}"?`}
      />
    </div>
  );
}

export default CrudPage;
