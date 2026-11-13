"use client"

import { useEffect, useState } from "react"
import { Reveal, NumberRoll } from "@olenevod/motion"
import { Button, Badge, Skeleton } from "@olenevod/ui"
import { catalogApi, formatPrice, type City, type ProductCard as ProductCardDto } from "@/lib/api"
import { CitySelector } from "@/components/header"

type ProductState = {
  cities: City[]
  card: ProductCardDto | null
  city: City | null
  loading: boolean
  error: string | null
}

export default function ProductPage({
  params,
  searchParams,
}: Readonly<{
  params: Promise<{ slug: string }>
  searchParams: Promise<{ city_id?: string }>
}>) {
  const [state, setState] = useState<ProductState>({
    cities: [],
    card: null,
    city: null,
    loading: true,
    error: null,
  })

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const [{ slug }, { city_id }] = await Promise.all([params, searchParams])
        const cities = await catalogApi.listCities()
        const city = cities.find((c) => c.id === city_id) ?? cities[0]
        if (!city) {
          if (!cancelled) setState((s) => ({ ...s, loading: false, error: "Город не найден" }))
          return
        }
        const items = await catalogApi.listProducts({ city_id: city.id, limit: 100, offset: 0 })
        const found = items.find((item) => item.slug === slug)
        if (!found) {
          if (!cancelled) setState((s) => ({ ...s, loading: false, error: "Товар не найден" }))
          return
        }
        const card = await catalogApi.getProduct(found.id, city.id)
        if (!cancelled) {
          setState({ cities, card, city, loading: false, error: null })
        }
      } catch (err) {
        if (!cancelled) {
          setState((s) => ({ ...s, loading: false, error: String(err) }))
        }
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [params, searchParams])

  const { cities, card, city, loading, error } = state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ink-900 text-paper-300">
        {error}
      </div>
    )
  }
  if (loading || !card || !city) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ink-900">
        <Skeleton className="w-48 h-8 mx-auto" />
      </div>
    )
  }

  const mainVariant = card.variants[0]
  const inStock = mainVariant.available_by_city.some(
    (s) => s.city_id === city.id && s.available_qty > 0
  )
  const cityStock = mainVariant.available_by_city.find((s) => s.city_id === city.id)

  return (
    <div className="min-h-screen flex flex-col">
      <section className="border-b border-line bg-ink-900 py-4">
        <div className="mx-auto max-w-[1440px] px-4">
          <div className="flex items-baseline gap-4 mb-2">
            <h1 className="font-display text-display-md text-paper-100 uppercase tracking-[0.005em] leading-[0.95]">
              {card.name}
            </h1>
            <Badge type={inStock ? "stock" : "out"}>
              {inStock ? "В наличии" : "Нет в наличии"}
            </Badge>
          </div>
          <CitySelector
            cities={cities.map((c) => ({ id: c.id, name: c.name }))}
            selectedId={city.id}
            onSelect={() => {}}
          />
          {card.description && (
            <p className="mt-3 text-paper-300" data-font="text">
              {card.description}
            </p>
          )}
        </div>
      </section>

      <section className="bg-ink-900 py-10">
        <div className="mx-auto max-w-[1440px] px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
            <div className="flex flex-col gap-3">
              <div className="relative aspect-[4/5] bg-ink-850 border border-line overflow-hidden">
                <Reveal once={true}>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Skeleton className="w-full h-full" />
                  </div>
                </Reveal>
              </div>
              <p className="mono-s text-paper-500 text-xs">
                DEMO-изображение — placeholder (DESIGN_SYSTEM §6.4)
              </p>
            </div>

            <div className="flex flex-col gap-6">
              <div>
                <p className="mono-s text-paper-500 uppercase tracking-[0.08em] mb-1">
                  {mainVariant.unit_type.toUpperCase()}
                </p>
                <div className="flex items-baseline gap-3">
                  <NumberRoll value={mainVariant.price_kop / 100} className="font-text font-semibold text-[28px] tabular-nums text-paper-100" />
                  <span className="text-paper-500">₽</span>
                </div>
                {mainVariant.old_price_kop && (
                  <p className="mono-s text-paper-500 line-through mt-1">
                    {formatPrice(mainVariant.old_price_kop)}
                  </p>
                )}
              </div>

              <div className="flex flex-col gap-3 border-t border-line pt-4">
                <h3 className="mono-s text-paper-500 uppercase tracking-[0.06em] text-sm">
                  Наличие по городам
                </h3>
                {mainVariant.available_by_city.map((s) => (
                  <div key={s.city_id} className="flex justify-between items-center">
                    <span className="text-paper-300">{s.city_name}</span>
                    <Badge type={s.available_qty > 0 ? "stock" : "out"}>
                      {s.available_qty > 0 ? `В наличии (${s.available_qty})` : "Нет в наличии"}
                    </Badge>
                  </div>
                ))}
              </div>

              <Button
                variant="primary"
                disabled={!inStock}
                onClick={() => {}}
                className="w-full"
              >
                {inStock ? "В корзину" : "Сообщить о поступлении"}
              </Button>
              {!inStock && (
                <p className="mono-s text-paper-500 text-sm">
                  Подписка на уведомление о поступлении (через канал клиента)
                </p>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
