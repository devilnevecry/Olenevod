import React from "react"
import "./olenevod.css"

export interface AdminColumn {
  key: string
  label: string
  width?: string
  mono?: true
}

export interface AdminTableProps {
  className?: string
  columns: AdminColumn[]
  rows: Record<string, string | number>[]
  loading?: boolean
  error?: string
}

export const AdminTable = React.forwardRef<HTMLDivElement, AdminTableProps>(
  ({ className, columns, rows, loading = false, error }, ref) => (
    <div className={["ol-admin-table-wrap", className].filter(Boolean).join(" ")} data-state={loading ? "loading" : error ? "error" : rows.length ? "default" : "empty"}>
      {error && <p className="ol-error-text">{error}</p>}
      {rows.length === 0 && !loading && !error && (
        <div className="ol-empty" style={{ padding: 32 }}>
          <h3>Записей нет</h3>
        </div>
      )}
      {!error && (
        <div className="ol-admin-table" ref={ref} aria-hidden={loading || error ? true : undefined}>
          <div className="ol-admin-table-header">
            {columns.map((col) => (
              <div key={col.key} style={{ width: col.width }}>
                {col.label}
              </div>
            ))}
          </div>
          <div className="ol-admin-table-body">
            {rows.map((row, ri) => (
              <div key={ri} className="ol-admin-table-row">
                {columns.map((col) => (
                  <div key={col.key} className={["ol-admin-table-cell", col.mono ? "ol-mono" : undefined].filter(Boolean).join(" ")}>
                    {row[col.key]}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
)
AdminTable.displayName = "AdminTable"
