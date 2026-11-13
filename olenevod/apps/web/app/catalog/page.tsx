"use client"

import { useCallback, useEffect, useState } from "react"
import { Reveal } from "@olenevod/motion"
import {
  Button,
  Chip,
  ProductCard,
  EmptyState,
  Skeleton,
  Ticker,
  Toast,
} from "@olenevod/ui"
import { catalogApi, type City, type Category, type ProductItem } from "@/lib/api"
import { CitySelector, Header } from "@/components/header"
import { useRouter } from "next/navigation"
import { useCart } from "@/components/cart-provider"

type CatalogState = {
  cities: City[]
  categories: Category[]
  items: ProductItem[]
  loading: boolean
  error: string | null
}

export default function CatalogPage({
  searchParams,
}: Readonly<{
  searchParams: Promise<{
    city_id?: string
    category_id?: string
    search?: string
    page?: string
  }>
}>) {
  const router = useRouter()
  const cart = useCart()
  const [addedId, setAddedId] = useState<string | null>(null)
  const [toast, setToast] = useState<{ message: string; visible: boolean }>({
    message: "",
    visible: false,
  })

  const showToast = useCallback((message: string) => {
    setToast({ message, visible: true })
    setTimeout(() => setToast((t) => ({ ...t, visible: false })), 3000)
  }, [])

  const onAdd = useCallback(
    (product: ProductItem) => {
      cart.add({
        product_variant_id: product.variant_id,
        name: product.name,
        price: product.price_kop / 100,
        qty: 1,
      })
      setAddedId(product.id)
      showToast(`Добавлено: ${product.name}`)
      setTimeout(() => setAddedId(null), 900)
    },
    [cart, showToast],
  )
  const [state, setState] = useState<CatalogState>({
    cities: [],
    categories: [],
    items: [],
    loading: true,
    error: null,
  })
  const [params, setParams] = useState<{
    city_id: string
    category_id: string
    search: string
    page: number
  }>({ city_id: "", category_id: "", search: "", page: 1 })

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const p = await searchParams
        const page = parseInt(p.page ?? "1", 10) || 1
        const city_id = p.city_id ?? ""
        const category_id = p.category_id ?? ""
        const search = p.search ?? ""
        if (!cancelled) {
          setParams({ city_id, category_id, search, page })
        }

        const [cities, categories] = await Promise.all([
          catalogApi.listCities(),
          catalogApi.listCategories(),
        ])
        const city = cities.find((c) => c.id === city_id) ?? cities[0]
        const cityId = city?.id ?? ""

        const items = await catalogApi.listProducts({
          city_id: cityId,
          category_id: category_id || undefined,
          limit: 20,
          offset: (page - 1) * 20,
          search: search || undefined,
        })
        if (!cancelled) {
          setState({ cities, categories, items, loading: false, error: null })
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
  }, [searchParams, router])

  const setCategory = (category_id: string | undefined) => {
    const q = new URLSearchParams()
    q.set("city_id", params.city_id)
    if (category_id) {
      q.set("category_id", category_id)
    } else {
      q.delete("category_id")
    }
    q.set("page", "1")
    if (params.search) {
      q.set("search", params.search)
    }
    router.push(`/catalog?${q.toString()}`)
  }

  const setCity = (city_id: string) => {
    const q = new URLSearchParams()
    q.set("city_id", city_id)
    q.set("category_id", params.category_id || "")
    q.set("page", "1")
    if (params.search) {
      q.set("search", params.search)
    }
    router.push(`/catalog?${q.toString()}`)
  }

  const { cities, categories, items, loading, error } = state
  const city = cities.find((c) => c.id === params.city_id) ?? cities[0]
  if (!city) return null

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ink-900 text-paper-300">
        Ошибка загрузки: {error}
      </div>
    )
  }
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ink-900">
        <Skeleton className="w-48 h-8 mx-auto" />
      </div>
    )
  }

  const totalPages = Math.ceil(items.length / 20) || 1

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        cities={cities.map((c) => ({ id: c.id, name: c.name }))}
        selectedId={city.id}
        onSelect={() => {}}
      />
      <section className="border-b border-line bg-ink-900 py-4">
        <div className="mx-auto max-w-[1440px] px-4">
          <div className="flex items-baseline gap-4 mb-4">
            <h1 className="font-display text-display-xl text-paper-100 uppercase tracking-[0.005em] leading-[0.86]">
              Каталог
            </h1>
            <span className="mono-s text-paper-500">{items.length} товаров</span>
          </div>
          <CitySelector
            cities={cities.map((c) => ({ id: c.id, name: c.name }))}
            selectedId={city.id}
            onSelect={setCity}
          />
        </div>
      </section>

      <section className="bg-ink-900 py-6">
        <div className="mx-auto max-w-[1440px] px-4">
          <div className="flex flex-wrap gap-2 mb-6">
            <Chip
              selected={!params.category_id && !params.search}
              onClick={() => setCategory(undefined)}
            >
              Все
            </Chip>
            {categories.slice(0, 8).map((cat) => (
              <Chip
                key={cat.id}
                selected={params.category_id === cat.id}
                onClick={() => setCategory(cat.id)}
              >
                {cat.name}
              </Chip>
            ))}
            {params.search && (
              <Chip selected onClick={() => {}}>
                Поиск: {params.search}
              </Chip>
            )}
          </div>

          <Reveal once={true} className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {items.length > 0 ? (
              items.map((product) => (
                <ProductCard
                  key={product.id}
                  image={undefined}
                  name={product.name}
                  meta={`${product.variant_name} • ${product.unit_type}`}
                  price={product.price_kop / 100}
                  oldPrice={product.old_price_kop ? product.old_price_kop / 100 : undefined}
                  inStock={product.available_qty > 0}
                  onAdd={() => onAdd(product)}
                />
              ))
            ) : (
              <EmptyState
                title="Ничего не найдено"
                description="Попробуйте изменить фильтр или город."
                ctaLabel="Сбросить фильтры"
                onCta={() => {}}
              />
            )}
          </Reveal>

          {items.length > 0 && totalPages > 1 && (
            <div className="mt-8 flex justify-center gap-2">
              {params.page > 1 && (
                <Button variant="ghost" onClick={() => {}}>
                  &larr; Назад
                </Button>
              )}
              <span className="mono-s text-paper-300">
                Страница {params.page} из {totalPages}
              </span>
              {params.page < totalPages && (
                <Button variant="primary" onClick={() => {}}>
                  Показать ещё &rarr;
                </Button>
              )}
            </div>
          )}
        </div>
      </section>

      <section className="bg-ink-950 py-3">
        <Ticker kind="promo" items={["ПОПУЛЯРНОЕ!"]} speedSeconds={35} />
      </section>
      <Toast message={toast.message} visible={toast.visible} onDismiss={() => setToast((t) => ({ ...t, visible: false }))} />
    </div>
  )
}
