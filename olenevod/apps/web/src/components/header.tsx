"use client"

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

const NAV_LINKS = [
  { href: "/catalog", label: "Каталог" },
  { href: "/delivery", label: "Доставка" },
  { href: "/about", label: "О нас" },
  { href: "/contacts", label: "Контакты" },
]

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

export function Header({ cities, selectedId, onSelect }: Readonly<{ cities: CityPill[]; selectedId: string | null; onSelect: (id: string) => void }>) {
  return (
    <header className="ol-header">
      <div className="ol-brand">
        <a href="/" className="ol-wordmark" aria-label="Оленевод — на главную">
          ОЛЕНЕВОД
        </a>
      </div>
      <nav className="ol-nav">
        {NAV_LINKS.map((link) => (
          <a key={link.href} href={link.href}>{link.label}</a>
        ))}
      </nav>
      <div className="ol-cart" role="group" aria-label="Корзина">
        <Button variant="ghost" data-state="default" onClick={() => {
          window.location.href = "/cart"
        }}>
          Корзина
        </Button>
      </div>
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
    </header>
  )
}

Header.displayName = "Header"
