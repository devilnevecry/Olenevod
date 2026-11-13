/* src/lib/cart.ts — типы и хранение корзины (этап 13).
 *
 * Состояние живёт в React-компоненте CartProvider (src/components/cart-provider.tsx);
 * здесь только типы и чтение/запись localStorage для чёрновика корзины.
 */

export interface CartItem {
  product_variant_id: string
  name: string
  price: number
  qty: number
}

export interface CartActions {
  add: (item: CartItem) => void
  remove: (product_variant_id: string) => void
  changeQty: (product_variant_id: string, qty: number) => void
  clear: () => void
}

export interface CartState extends CartActions {
  items: CartItem[]
  itemQty: (product_variant_id: string) => number
  total: number
  count: number
}

const STORAGE_KEY = "olenevod_cart"

export function loadCart(): CartItem[] {
  if (typeof window === "undefined") return []
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as CartItem[]) : []
  } catch {
    return []
  }
}

export function saveCart(items: CartItem[]) {
  if (typeof window === "undefined") return
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
}
