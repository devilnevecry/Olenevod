"use client"

import { createContext, useCallback, useContext, useEffect, useState } from "react"

import { CartItem, CartState, loadCart, saveCart } from "@/lib/cart"

const CartContext = createContext<CartState | null>(null)

export function CartProvider({ children }: Readonly<{ children: React.ReactNode }>) {
  const [items, setItems] = useState<CartItem[]>(() => loadCart())

  useEffect(() => {
    saveCart(items)
  }, [items])

  const itemQty = useCallback(
    (product_variant_id: string) => items.find((i) => i.product_variant_id === product_variant_id)?.qty ?? 0,
    [items],
  )

  const total = items.reduce((sum, i) => sum + i.price * i.qty, 0)
  const count = items.reduce((sum, i) => sum + i.qty, 0)

  const add = useCallback((item: CartItem) => {
    setItems((prev) => {
      const existing = prev.find((i) => i.product_variant_id === item.product_variant_id)
      if (existing) {
        existing.qty += item.qty
        return [...prev]
      }
      return [...prev, { ...item }]
    })
  }, [])

  const remove = useCallback((product_variant_id: string) => {
    setItems((prev) => prev.filter((i) => i.product_variant_id !== product_variant_id))
  }, [])

  const changeQty = useCallback((product_variant_id: string, qty: number) => {
    setItems((prev) => {
      const next = prev.map((i) => (i.product_variant_id === product_variant_id ? { ...i, qty: Math.max(0, qty) } : i))
      return next.filter((i) => i.qty > 0)
    })
  }, [])

  const clear = useCallback(() => setItems([]), [])

  const value: CartState = {
    items,
    itemQty,
    total,
    count,
    add,
    remove,
    changeQty,
    clear,
  }

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart(): CartState {
  const ctx = useContext(CartContext)
  if (ctx === null) {
    throw new Error("useCart must be used within CartProvider")
  }
  return ctx
}
