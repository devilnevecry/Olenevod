"use client"

import { useEffect, useState } from "react"
import { Reveal } from "@olenevod/motion"
import {
  Button,
  Chip,
  CategoryCard,
  ProductCard,
  Skeleton,
  Ticker,
} from "@olenevod/ui"
import { catalogApi, formatPrice, type City, type Category, type ProductItem } from "@/lib/api"
import { CitySelector } from "@/components/header"

const MOSCOW_SLUG = "moscow"

type HomeState = {
  cities: City[]
  categories: Category[]
  hits: ProductItem[]
  loading: boolean
  error: string | null
}

export default function HomePage() {
  const [state, setState] = useState<HomeState>({
    cities: [],
    categories: [],
    hits: [],
    loading: true,
    error: null,
  })

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const [cities, categories] = await Promise.all([
          catalogApi.listCities(),
          catalogApi.listCategories(),
        ])
        let hits: ProductItem[] = []
        const moscow = cities.find((c) => c.slug === MOSCOW_SLUG)
        if (moscow) {
          hits = (await catalogApi.listProducts({ city_id: moscow.id, limit: 4 })) ?? []
        }
        if (!cancelled) {
          setState({ cities, categories, hits, loading: false, error: null })
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
  }, [])

  if (state.error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ink-900 text-paper-300">
        Ошибка загрузки: {state.error}
      </div>
    )
  }

  if (state.loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ink-900">
        <Skeleton className="w-48 h-8 mx-auto" />
      </div>
    )
  }

  const { cities, categories, hits } = state
  const moscow = cities.find((c) => c.slug === MOSCOW_SLUG)
  const catsWithCount = categories.map((c) => ({ id: c.id, name: c.name, count: undefined as number | undefined }))

  return (
    <div className="relative min-h-screen flex flex-col" data-grain="off">
      <section className="relative h-[min(100svh,720px)] flex flex-col justify-between border-b border-line bg-ink-900">
        <Reveal once={true} className="pt-6 pb-4">
          <div className="flex flex-col lg:flex-row gap-6 items-end">
            <div className="flex flex-col gap-2">
              <span className="inline-block px-3 py-1 rounded-full border border-line bg-ink-850 text-ember-300 text-mono-s uppercase tracking-[0.08em]">
                Воркута • Тундра
              </span>
              <h1 className="font-display text-display-xxl text-paper-100 uppercase tracking-[-0.01em] leading-[0.82]">
                ОЛЕНЕВОД
              </h1>
              <span className="text-ember-400 font-display text-display-lg uppercase tracking-[0.005em] leading-[0.95]">
                СЫРОВЯЛЕНАЯ ОЛЕНИНА
              </span>
            </div>
            <div className="flex gap-3 mt-4 lg:mt-0">
              <Button variant="primary">Выбрать оленину</Button>
              <Button variant="secondary">Как мы доставляем</Button>
            </div>
          </div>
        </Reveal>

        <Reveal once={true} className="pb-6">
          <Ticker
            kind="promo"
            items={["ПОПУЛЯРНОЕ!", "НОВИНКИ!", "СЫРОВЯЛЕНАЯ ОЛЕНИНА", "ДОСТАВКА ПО ТУНДРЕ"]}
            speedSeconds={40}
          />
        </Reveal>
      </section>

      <section className="border-b border-line bg-ink-900 py-4">
        <div className="mx-auto max-w-[1440px] px-4">
          <p className="mono-s text-paper-500 mb-2 uppercase tracking-[0.06em]">
            Выберите город доставки
          </p>
          <CitySelector
            cities={cities.map((c) => ({ id: c.id, name: c.name }))}
            selectedId={moscow ? moscow.id : null}
            onSelect={() => {}}
          />
        </div>
      </section>

      <section className="bg-ink-900 py-12">
        <div className="mx-auto max-w-[1440px] px-4">
          <div className="flex items-baseline gap-4 mb-8">
            <h2 className="font-display text-display-lg text-paper-100 uppercase tracking-[0.005em] leading-[0.95]">
              Категории
            </h2>
            <span className="mono-s text-paper-500">{categories.length}</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {(catsWithCount.slice(0, 4).length > 0 ? catsWithCount.slice(0, 4) : [
              { id: "0", name: "Заготовки", count: 0 },
              { id: "1", name: "Мясо", count: 0 },
              { id: "2", name: "Печень", count: 0 },
              { id: "3", name: "Субпродукты", count: 0 },
            ]).map((cat) => (
              <CategoryCard
                key={cat.id}
                image={undefined}
                name={cat.name}
                count={cat.count}
                onPress={() => {}}
              />
            ))}
          </div>
        </div>
      </section>

      <section className="bg-ink-950 py-3">
        <Ticker kind="promo" items={["ПОПУЛЯРНОЕ!"]} speedSeconds={35} />
      </section>

      <section className="bg-ink-900 py-12 border-b border-line">
        <div className="mx-auto max-w-[1440px] px-4">
          <div className="flex items-baseline gap-4 mb-8">
            <h2 className="font-display text-display-lg text-paper-100 uppercase tracking-[0.005em] leading-[0.95]">
              Хиты
            </h2>
            <a
              href="/catalog"
              className="mono-s text-ember-300 hover:text-paper-100 underline-offset-4"
            >
              Весь каталог + &rarr;
            </a>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {hits.length > 0 ? (
              hits.map((product) => (
                <ProductCard
                  key={product.id}
                  image={undefined}
                  name={product.name}
                  meta={`${product.variant_name} • ${product.unit_type}`}
                  price={product.price_kop / 100}
                  oldPrice={product.old_price_kop ? product.old_price_kop / 100 : undefined}
                  inStock={product.available_qty > 0}
                  onAdd={() => {}}
                />
              ))
            ) : (
              <Skeleton className="w-full h-[420px]" />
            )}
          </div>
        </div>
      </section>
    </div>
  )
}
