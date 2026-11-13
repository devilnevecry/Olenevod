/* src/lib/api.ts — клиент API каталога Olenevod.
 *
 * Контракт этапа 4 (см. olenevod/apps/api/olenevod/interfaces/http/catalog.py):
 *   GET /cities, GET /categories, GET /products?city_id=..., GET /products/{id}?city_id=...
 * Базовый URL берётся из NEXT_PUBLIC_API_URL (по умолчанию http://localhost:8000,
 * см. .env.example API_PORT=8000). Реальные реквизиты владельца не кодируются.
 */

// Базовый URL API каталога. По умолчанию запросы идут на ту же origine через
// Next.js rewrite (/api/* → http://localhost:8000/*), что обходит CORS.
// Для продакшена NEXT_PUBLIC_API_URL задаёт внешний адрес бэкенда.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api"

export interface City {
  id: string
  slug: string
  name: string
  region: string | null
}

export interface Category {
  id: string
  slug: string
  name: string
  parent_id: string | null
  children: Category[]
}

export interface ProductItem {
  id: string
  slug: string
  name: string
  category_id: string
  variant_id: string
  sku: string
  variant_name: string
  unit_type: string
  price_kop: number
  old_price_kop: number | null
  available_qty: number
}

export interface CityStock {
  city_id: string
  city_name: string
  available_qty: number
}

export interface ProductVariantCard {
  id: string
  sku: string
  name: string
  unit_type: string
  price_kop: number
  old_price_kop: number | null
  available_by_city: CityStock[]
}

export interface ProductCard {
  id: string
  slug: string
  name: string
  description: string | null
  variants: ProductVariantCard[]
}

interface ListProductsParams {
  city_id: string
  category_id?: string
  limit?: number
  offset?: number
  search?: string
}

async function request<T>(
  path: string,
  params?: Record<string, string | number | null | undefined>
): Promise<T> {
  const fullPath = API_URL + path
  let lastError: unknown = null
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const url = new URL(fullPath, typeof window !== "undefined" ? window.location.origin : "http://localhost")
      if (params) {
        for (const [key, value] of Object.entries(params)) {
          if (value !== undefined && value !== null && value !== "") {
            url.searchParams.append(key, String(value))
          }
        }
      }
      const response = await fetch(url.toString(), { cache: "no-store" })
      if (!response.ok) {
        throw new Error(`API ${path} responded ${response.status}`)
      }
      return response.json()
    } catch (err) {
      lastError = err
      if (attempt < 2) {
        await new Promise((resolve) => setTimeout(resolve, 300 * (attempt + 1)))
      }
    }
  }
  throw lastError
}

export const catalogApi = {
  listCities: () => request<City[]>("/cities"),
  listCategories: () => request<Category[]>("/categories"),
  listProducts: (params: ListProductsParams) =>
    request<ProductItem[]>("/products", {
      city_id: params.city_id,
      category_id: params.category_id || undefined,
      limit: params.limit ?? 20,
      offset: params.offset ?? 0,
      search: params.search || undefined,
    }),
  getProduct: (product_id: string, city_id: string) =>
    request<ProductCard>(`/products/${product_id}`, { city_id }),
}

export const formatPrice = (kop: number): string => {
  const rub = kop / 100
  return rub.toLocaleString("ru-RU", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }) + " ₽"
}
