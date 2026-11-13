"use client"

import { useCallback, useState } from "react"
import { NumberRoll, Reveal } from "@olenevod/motion"
import { Badge, Button, EmptyState, Skeleton, Toast } from "@olenevod/ui"
import { useCart } from "@/components/cart-provider"
import { formatPrice } from "@/lib/api"

export default function CartPage() {
  const { items, total, count, changeQty, remove, clear } = useCart()
  const [toast, setToast] = useState<{ message: string; visible: boolean }>({
    message: "",
    visible: false,
  })

  const show = (message: string) => {
    setToast({ message, visible: true })
    setTimeout(() => setToast((t) => ({ ...t, visible: false })), 3000)
  }

  const onChange = (product_variant_id: string, delta: number) => {
    const item = items.find((i) => i.product_variant_id === product_variant_id)
    if (!item) return
    changeQty(product_variant_id, item.qty + delta)
    show(`Количество обновлено: ${item.name}`)
  }

  const onRemove = (product_variant_id: string) => {
    const item = items.find((i) => i.product_variant_id === product_variant_id)
    remove(product_variant_id)
    show(`Удалено из корзины: ${item?.name ?? ""}`)
  }

  return (
    <div className="min-h-screen flex flex-col">
      <section className="border-b border-line bg-ink-900 py-4">
        <div className="mx-auto max-w-[1440px] px-4">
          <h1 className="font-display text-display-lg text-paper-100 uppercase tracking-[0.005em] leading-[0.95]">
            Корзина
          </h1>
          <p className="mono-s text-paper-500 mt-1">{count} позиций</p>
        </div>
      </section>

      <section className="bg-ink-900 py-8">
        <div className="mx-auto max-w-[1440px] px-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-8">
              <div className="space-y-6">
                <Reveal once={true}>
                  {items.length === 0 ? (
                    <EmptyState
                      title="Корзина пуста"
                      description="Добавьте товары из каталога — нажмите «В корзину» на карточке товара."
                      ctaLabel="Перейти в каталог"
                      onCta={() => {
                        window.location.href = "/catalog"
                      }}
                    />
                  ) : (
                    items.map((item) => (
                      <div
                        key={item.product_variant_id}
                        className="flex items-center gap-4 border-b border-line pb-6 lg:grid lg:grid-cols-12 lg:items-center"
                      >
                        <div className="lg:col-span-4 flex flex-col gap-1">
                          <span className="text-paper-100 font-semibold">{item.name}</span>
                          <span className="mono-s text-paper-500 text-sm">
                            {item.price.toLocaleString("ru-RU")} ₽
                          </span>
                        </div>
                        <div className="lg:col-span-4 flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => onChange(item.product_variant_id, -1)}
                            className="ol-chip"
                            disabled={item.qty <= 1}
                            aria-label="Уменьшить количество"
                          >
                            −
                          </button>
                          <NumberRoll
                            value={item.qty}
                            className="font-mono tabular-nums text-paper-100 w-12 text-center"
                          />
                          <button
                            type="button"
                            onClick={() => onChange(item.product_variant_id, 1)}
                            className="ol-chip"
                            aria-label="Увеличить количество"
                          >
                            +
                          </button>
                        </div>
                        <div className="lg:col-span-2 flex items-end justify-end">
                          <NumberRoll
                            value={item.price * item.qty}
                            className="font-text font-semibold text-paper-100 tabular-nums"
                          />
                          <span className="text-paper-500">₽</span>
                        </div>
                        <div className="lg:col-span-2 flex justify-end">
                          <button
                            type="button"
                            onClick={() => onRemove(item.product_variant_id)}
                            className="ol-btn"
                            data-variant="ghost"
                            aria-label={`Удалить ${item.name}`}
                            style={{ padding: 0, width: 32, height: 32, lineHeight: 1 }}
                          >
                            ×
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </Reveal>
              </div>
            </div>
            <div className="lg:col-span-4">
              {items.length > 0 && (
                <div className="border border-line bg-ink-850 p-6">
                  <div className="flex justify-between items-baseline mb-2">
                    <span className="text-paper-300">Итого</span>
                    <div className="flex items-baseline gap-1">
                      <NumberRoll
                        value={total}
                        className="font-text font-semibold text-[24px] tabular-nums text-paper-100"
                      />
                      <span className="text-paper-500">₽</span>
                    </div>
                  </div>
                  <Button
                    variant="primary"
                    onClick={() => {
                      window.location.href = "/checkout"
                    }}
                    className="w-full mt-6"
                  >
                    Оформить заказ
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      <Toast
        message={toast.message}
        visible={toast.visible}
        onDismiss={() => setToast((t) => ({ ...t, visible: false }))}
      />
    </div>
  )
}
