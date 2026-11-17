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

interface RequestOptions {
  method?: string
  body?: unknown
}

type RequestParamValue = string | number | null | undefined | (string | number)[]

async function request<T>(
  path: string,
  params?: Record<string, RequestParamValue>,
  options: RequestOptions = {},
): Promise<T> {
  const fullPath = API_URL + path
  let lastError: unknown = null
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const url = new URL(fullPath, typeof window !== "undefined" ? window.location.origin : "http://localhost:3000")
      if (params) {
        for (const [key, value] of Object.entries(params)) {
          const values = Array.isArray(value) ? value : [value]
          for (const v of values) {
            if (v !== undefined && v !== null && v !== "") {
              url.searchParams.append(key, String(v))
            }
          }
        }
      }
      const init: RequestInit = { cache: "no-store", method: options.method ?? "GET" }
      if (options.body !== undefined) {
        init.headers = { "Content-Type": "application/json" }
        init.body = JSON.stringify(options.body)
      }
      const response = await fetch(url.toString(), init)
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

// ---------- Заказы (этап 5) ----------

export interface OrderItem {
  id: string
  product_variant_id: string
  qty: number
  price: number
}

export interface Order {
  id: string
  city_id: string
  customer_name: string
  customer_phone: string
  status: string
  total_amount: number
  items: OrderItem[]
}

export interface OrderItemIn {
  product_variant_id: string
  qty: number
}

export interface OrderIn {
  city_id: string
  customer_name: string
  customer_phone: string
  items: OrderItemIn[]
}

export const ordersApi = {
  create: (data: OrderIn) => request<Order>("/orders", undefined, { method: "POST", body: data }),
  get: (order_id: string) => request<Order>(`/orders/${order_id}`),
}

// ---------- Доставка (этап 9) ----------

export interface DeliveryQuote {
  city_id: string
  zone: string
  fee: number
  free_delivery: boolean
  estimated_days: number | null
}

export const deliveryApi = {
  quote: (city_id: string, variant_ids: string[], total_amount: number) =>
    request<DeliveryQuote>("/delivery/quote", {
      city_id,
      items: variant_ids,
      total_amount,
    }),
}

// ---------- Платежи (этап 6) ----------

export interface Payment {
  id: string
  order_id: string
  provider: string
  amount: number
  status: string
  external_id: string | null
  created_at: string
}

export const paymentsApi = {
  status: (order_id: string) => request<Payment>(`/payments/${order_id}/status`),
  webhook: (provider: string, payload: unknown) =>
    request<{ order_id: string; status: string }>(`/payments/webhook/${provider}`, undefined, {
      method: "POST",
      body: payload,
    }),
}

// ---------- Аутентификация (этап 10) ----------

export interface RegisterIn {
  email: string
  name: string
  password: string
}

export interface RegisterOut {
  user_id: string
  email: string
  is_verified: boolean
  message: string
}

export interface LoginIn {
  email: string
  password: string
}

export interface LoginOut {
  access_token: string
  token_type: string
  user_id: string
}

export const authApi = {
  register: (data: RegisterIn) => request<RegisterOut>("/auth/register", undefined, { method: "POST", body: data }),
  login: (data: LoginIn) => request<LoginOut>("/auth/login", undefined, { method: "POST", body: data }),
}

