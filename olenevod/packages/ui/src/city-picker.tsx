import React from "react"
import "./olenevod.css"
import { Input } from "./input"

export interface CityOption {
  id: string
  name: string
  region?: string
  status?: string
}

export interface CityPickerProps {
  className?: string
  open: boolean
  onClose: () => void
  cities: CityOption[]
  selectedId?: string
  onSelect: (id: string) => void
}

export const CityPicker = React.forwardRef<HTMLDivElement, CityPickerProps>(
  ({ className, open, onClose, cities, selectedId, onSelect, ...rest }, ref) => (
    <div
      ref={ref}
      className={["ol-city-picker", className, open ? "open" : ""].filter(Boolean).join(" ")}
      hidden={!open}
      role="dialog"
      aria-modal="true"
      aria-label="Выбор города"
      {...rest}
    >
      <div className="ol-city-overlay" onClick={onClose} />
      <div className="ol-city-panel" onClick={(e) => e.stopPropagation()}>
        <div className="ol-city-header">
          <h3>Выберите город</h3>
          <button type="button" className="ol-btn" data-variant="ghost" onClick={onClose}>
            Закрыть
          </button>
        </div>
        <Input
          label="Поиск города"
          placeholder="Воркута, Сыктывкар…"
          className="ol-city-search"
        />
        <div className="ol-city-list">
          {cities.map((city) => (
            <button
              key={city.id}
              type="button"
              className={["ol-city-item", selectedId === city.id ? "selected" : ""].filter(Boolean).join(" ")}
              onClick={() => onSelect(city.id)}
            >
              <div className="ol-city-name">{city.name}</div>
              {city.region && <span className="ol-city-region">{city.region}</span>}
              {city.status && <span className="ol-city-status">{city.status}</span>}
            </button>
          ))}
          <button type="button" className="ol-city-item" onClick={() => onSelect("other")}>
            <div className="ol-city-name">Другой город / доставка по России</div>
          </button>
        </div>
      </div>
    </div>
  )
)
CityPicker.displayName = "CityPicker"
