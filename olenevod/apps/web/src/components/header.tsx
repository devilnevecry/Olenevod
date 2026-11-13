"use client"

import * as React from "react"
import { Chip, Button } from "@olenevod/ui"

export interface CityPill {
  id: string
  name: string
}

interface CitySelectorProps {
  cities: CityPill[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export function CitySelector({ cities, selectedId, onSelect }: CitySelectorProps) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide" role="tablist" aria-label="Выбор города">
      {cities.map((city) => (
        <Chip
          key={city.id}
          selected={selectedId === city.id}
          onClick={() => onSelect(city.id)}
          role="tab"
          aria-selected={selectedId === city.id}
        >
          {city.name}
        </Chip>
      ))}
    </div>
  )
}
