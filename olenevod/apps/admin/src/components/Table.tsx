import React from "react";
import { Button } from "./Button";

export interface Column<T> {
  key: string;
  label: string;
  render?: (item: T) => React.ReactNode;
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  onEdit?: (item: T) => void;
  onDelete?: (item: T) => void;
  editLabel?: string;
  deleteLabel?: string;
}

export function Table<T>({ columns, data, onEdit, onDelete, editLabel = "Редактировать", deleteLabel = "Удалить" }: TableProps<T>) {
  const headerStyle: React.CSSProperties = {
    background: "#f8fafc",
    borderBottom: "1px solid #e2e8f0",
    textAlign: "left",
    fontSize: 12,
    fontWeight: 700,
    color: "#475569",
    padding: "8px 10px",
  };
  const cellStyle: React.CSSProperties = { padding: "8px 10px", borderBottom: "1px solid #e2e8f0", fontSize: 13 };

  return (
    <div style={{ border: "1px solid #e2e8f0", borderRadius: 6, overflow: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} style={headerStyle}>
                {c.label}
              </th>
            ))}
            {onEdit || onDelete ? <th style={{ ...headerStyle, width: 120 }}>Действия</th> : null}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length + (onEdit || onDelete ? 1 : 0)}
                style={{ ...cellStyle, textAlign: "center", color: "#64748b", padding: 16 }}
              >
                Нет данных
              </td>
            </tr>
          ) : (
            data.map((item) => {
              const rowKey = (item as any).id ?? item;
              return (
                <tr key={String(rowKey)}>
                  {columns.map((c) => (
                    <td key={c.key} style={cellStyle}>
                      {c.render ? c.render(item) : String((item as any)[c.key] ?? "-")}
                    </td>
                  ))}
                  {onEdit || onDelete ? (
                    <td style={{ ...cellStyle, whiteSpace: "nowrap" }}>
                      {onEdit && (
                        <Button
                          variant="ghost"
                          onClick={(e: React.MouseEvent) => { e.stopPropagation(); onEdit(item); }}
                          style={{ fontSize: 12, padding: "4px 8px", marginRight: 6 }}
                        >
                          {editLabel}
                        </Button>
                      )}
                      {onDelete && (
                        <Button
                          variant="danger"
                          onClick={(e: React.MouseEvent) => { e.stopPropagation(); onDelete(item); }}
                          style={{ fontSize: 12, padding: "4px 8px" }}
                        >
                          {deleteLabel}
                        </Button>
                      )}
                    </td>
                  ) : null}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
