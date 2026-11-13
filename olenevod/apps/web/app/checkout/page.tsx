"use client"

import React from "react"
import { useCallback, useEffect, useState } from "react"
import { NumberRoll, Reveal } from "@olenevod/motion"
import { Badge, Button, EmptyState, Input, Select, Toast } from "@olenevod/ui"
import { useCart } from "@/components/cart-provider"
import { Header } from "@/components/header"
import {
  catalogApi,
  deliveryApi,
  formatPrice,
  ordersApi,
  paymentsApi,
  type City,
  type DeliveryQuote,
} from "@/lib/api"

type CheckoutStep = "contacts" | "delivery" | "payment" | "confirm" | "success"

interface CheckoutForm {
  customer_name: string
  customer_phone: string
  email: string
  city_id: string
  payment_method: string
  agree_offer: boolean
  agree_pd: boolean
  agree_ads: boolean
}

const INITIAL_FORM: CheckoutForm = {
  customer_name: "",
  customer_phone: "",
  email: "",
  city_id: "",
  payment_method: "yukassa",
  agree_offer: false,
  agree_pd: false,
  agree_ads: false,
}

export default function CheckoutPage() {
  const cart = useCart()
  const [cities, setCities] = useState<City[]>([])
  const [step, setStep] = useState<CheckoutStep>("contacts")
  const [form, setForm] = useState<CheckoutForm>(INITIAL_FORM)
  const [quote, setQuote] = useState<DeliveryQuote | null>(null)
  const [quoteLoading, setQuoteLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string | undefined>>({})
  const [order, setOrder] = useState<{ id: string; status: string; total_amount: number } | null>(null)
  const [paymentStatus, setPaymentStatus] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [toast, setToast] = useState<{ message: string; visible: boolean }>({
    message: "",
    visible: false,
  })

  const showToast = useCallback((message: string) => {
    setToast({ message, visible: true })
    setTimeout(() => setToast((t) => ({ ...t, visible: false })), 3000)
  }, [])

  useEffect(() => {
    let cancelled = false
    catalogApi.listCities().then((loaded) => {
      if (!cancelled) setCities(loaded)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const deliveryItems = useCallback(() => {
    const ids: string[] = []
    for (const item of cart.items) {
      for (let i = 0; i < item.qty; i++) {
        ids.push(item.product_variant_id)
      }
    }
    return ids
  }, [cart.items])

  const fetchQuote = useCallback(async () => {
    if (!form.city_id) {
      setQuote(null)
      return
    }
    setQuoteLoading(true)
    try {
      const result = await deliveryApi.quote(form.city_id, deliveryItems(), cart.total * 100)
      setQuote(result)
    } catch {
      setQuote(null)
    } finally {
      setQuoteLoading(false)
    }
  }, [form.city_id, deliveryItems, cart.total])

  useEffect(() => {
    fetchQuote()
  }, [fetchQuote])

  const setField = useCallback((key: keyof CheckoutForm, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [key]: value }))
    setErrors((prev) => ({ ...prev, [key]: undefined }))
  }, [])

  const validateContacts = useCallback(() => {
    const next: Record<string, string> = {}
    if (!form.customer_name.trim()) next.customer_name = "Укажите имя"
    if (!/^\+?\d{7,15}$/.test(form.customer_phone.replace(/\s/g, "")))
      next.customer_phone = "Укажите телефон в формате +79000000000"
    if (!form.email.includes("@")) next.email = "Укажите e-mail"
    setErrors(next)
    return Object.keys(next).length === 0
  }, [form])

  const validateConfirm = useCallback(() => {
    const next: Record<string, string> = {}
    if (!form.agree_offer) next.agree_offer = "Требуется согласие с офертой"
    if (!form.agree_pd) next.agree_pd = "Требуется согласие на обработку персональных данных"
    setErrors(next)
    return Object.keys(next).length === 0
  }, [form])

  const nextStep = useCallback(() => {
    if (step === "contacts") {
      if (!validateContacts()) return
      setStep("delivery")
    } else if (step === "delivery") {
      if (!form.city_id) return
      setStep("payment")
    } else if (step === "payment") {
      setStep("confirm")
    }
  }, [step, form, validateContacts])

  const prevStep = useCallback(() => {
    if (step === "delivery") setStep("contacts")
    else if (step === "payment") setStep("delivery")
    else if (step === "confirm") setStep("payment")
  }, [step])

  const placeOrder = useCallback(async () => {
    if (!validateConfirm()) return
    if (!cart.items.length) return
    setSubmitting(true)
    try {
      const created = await ordersApi.create({
        city_id: form.city_id,
        customer_name: form.customer_name.trim(),
        customer_phone: form.customer_phone.trim(),
        items: cart.items.map((i) => ({
          product_variant_id: i.product_variant_id,
          qty: i.qty,
        })),
      })
      setOrder({ id: created.id, status: created.status, total_amount: created.total_amount })
      setStep("success")
      showToast(`Заказ №${created.id.slice(-4)} оформлен`)
      try {
        const history = JSON.parse(window.localStorage.getItem("olenevod_account_orders") ?? "[]")
        if (!history.includes(created.id)) {
          history.unshift(created.id)
          window.localStorage.setItem("olenevod_account_orders", JSON.stringify(history))
        }
      } catch {
        /* ignore storage errors */
      }
      cart.clear()
    } catch (err) {
      showToast(String(err ?? "Не удалось оформить заказ"))
    } finally {
      setSubmitting(false)
    }
  }, [cart.items, cart.clear, form, validateConfirm])

  const simulatePayment = useCallback(async () => {
    if (!order) return
    try {
      await paymentsApi.webhook("yukassa", { order_id: order.id })
      const status = await paymentsApi.status(order.id)
      setPaymentStatus(status.status)
      showToast("Оплата подтверждена провайдером")
    } catch (err) {
      showToast(`Платёж не найден у провайдера: ${String(err ?? "")}`)
    }
  }, [order])

  const { items, total, count } = cart
  const city = cities.find((c) => c.id === form.city_id)
  const deliveryFee = quote?.free_delivery ? 0 : quote?.fee ?? 0
  const grandTotal = total * 100 + deliveryFee

  const stepOrder: CheckoutStep[] = ["contacts", "delivery", "payment", "confirm"]
  const stepIndex = stepOrder.indexOf(step)
  const stepLabel: Record<CheckoutStep, string> = {
    contacts: "1. Контакты",
    delivery: "2. Доставка",
    payment: "3. Оплата",
    confirm: "4. Подтверждение",
    success: "Заказ оформлен",
  }

  if (items.length === 0 && step !== "success") {
    return (
      <div className="min-h-screen flex flex-col">
        <section className="border-b border-line bg-ink-900 py-4">
          <div className="mx-auto max-w-[1440px] px-4">
            <h1 className="font-display text-display-lg text-paper-100 uppercase tracking-[0.005em] leading-[0.95]">
              Оформление заказа
            </h1>
          </div>
        </section>
        <section className="bg-ink-900 py-12">
          <div className="mx-auto max-w-[1440px] px-4">
            <EmptyState
              title="Корзина пуста"
              description="Добавьте товары из каталога, чтобы оформить заказ."
              ctaLabel="Перейти в корзину"
              onCta={() => {
                window.location.href = "/cart"
              }}
            />
          </div>
        </section>
        <Toast message={toast.message} visible={toast.visible} onDismiss={() => setToast((t) => ({ ...t, visible: false }))} />
      </div>
    )
  }

  const field = (key: keyof CheckoutForm) => ({
    value: String(form[key] ?? ""),
    error: errors[key],
  })

  return (
    <div className="min-h-screen flex flex-col">
      <section className="border-b border-line bg-ink-900 py-4">
        <div className="mx-auto max-w-[1440px] px-4">
          <h1 className="font-display text-display-lg text-paper-100 uppercase tracking-[0.005em] leading-[0.95]">
            Оформление заказа
          </h1>
          <p className="mono-s text-paper-300 mt-1">
            {count} позиций на {formatPrice(total)}
          </p>
        </div>
      </section>

      <section className="bg-ink-900 py-8">
        <div className="mx-auto max-w-[1440px] px-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-8">
              <nav className="flex items-center gap-2 text-mono-s text-paper-500 uppercase mb-6">
                {stepOrder.map((s, i) => (
                  <React.Fragment key={s}>
                    <span
                      className={stepIndex >= i ? "text-paper-100 font-semibold" : "text-paper-500"}
                    >
                      {stepLabel[s]}
                    </span>
                    {i < stepOrder.length - 1 && <span>&rarr;</span>}
                  </React.Fragment>
                ))}
              </nav>

              <Reveal once={true}>
                {step === "contacts" && (
                  <section className="space-y-4">
                    <h2 className="text-paper-100 font-semibold mb-2">Контакты</h2>
                    <Input
                      label="Имя"
                      value={field("customer_name").value}
                      error={errors.customer_name}
                      onChange={(e) => setField("customer_name", e.target.value)}
                      placeholder="Иван Иванов"
                    />
                    <Input
                      label="Телефон"
                      value={field("customer_phone").value}
                      error={errors.customer_phone}
                      onChange={(e) => setField("customer_phone", e.target.value)}
                      placeholder="+7 900 000 00 00"
                    />
                    <Input
                      label="E-mail"
                      value={field("email").value}
                      error={errors.email}
                      onChange={(e) => setField("email", e.target.value)}
                      placeholder="ivan@example.com"
                    />
                  </section>
                )}
                {step === "delivery" && (
                  <section className="space-y-4">
                    <h2 className="text-paper-100 font-semibold mb-2">Доставка</h2>
                    <Select
                      label="Город доставки"
                      value={form.city_id}
                      error={errors.city_id}
                      onChange={(e) => setField("city_id", e.target.value)}
                    >
                      <option value="">Выберите город</option>
                      {cities.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                    </Select>
                    {quote && (
                      <div className="border border-line bg-ink-850 p-4">
                        <div className="flex justify-between mb-1">
                          <span className="text-paper-300">Зона доставки</span>
                          <span className="text-paper-100">{quote.zone}</span>
                        </div>
                        <div className="flex justify-between mb-1">
                          <span className="text-paper-300">Стоимость доставки</span>
                          <span className="text-paper-100">
                            {quote.free_delivery ? "Бесплатно" : formatPrice(quote.fee)}
                          </span>
                        </div>
                        {quote.estimated_days != null && (
                          <div className="flex justify-between">
                            <span className="text-paper-300">Срок доставки</span>
                            <span className="text-paper-100">{quote.estimated_days} дн.</span>
                          </div>
                        )}
                      </div>
                    )}
                    {quoteLoading && <p className="mono-s text-paper-500">Расчёт доставки…</p>}
                  </section>
                )}
                {step === "payment" && (
                  <section className="space-y-4">
                    <h2 className="text-paper-100 font-semibold mb-2">Оплата</h2>
                    <div className="border border-line bg-ink-850 p-4">
                      <div className="flex items-start gap-3">
                        <input
                          id="payment-yukassa"
                          type="radio"
                          name="payment_method"
                          checked={form.payment_method === "yukassa"}
                          onChange={() => setField("payment_method", "yukassa")}
                          className="mt-1"
                        />
                        <label htmlFor="payment-yukassa" className="cursor-pointer text-paper-100">
                          <div className="font-semibold">ЮKassa — банковская карта</div>
                          <div className="mono-s text-paper-500 text-sm">
                            Симуляция провайдера (без реальных списаний)
                          </div>
                        </label>
                      </div>
                    </div>
                  </section>
                )}
                {step === "confirm" && (
                  <section className="space-y-4">
                    <h2 className="text-paper-100 font-semibold mb-2">Подтверждение</h2>
                    <p className="text-paper-300 text-sm">
                      Заказ №{order?.id.slice(-4)} на сумму {formatPrice(order?.total_amount ?? total * 100)} будет
                      оформлен в городе {city?.name ?? form.city_id}.
                    </p>
                    <div className="space-y-3">
                      <label className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={form.agree_offer}
                          onChange={() => setField("agree_offer", !form.agree_offer)}
                          className="mt-1"
                        />
                        <div>
                          <div className="text-paper-100 font-semibold">Согласие с офертой публичной</div>
                          <div className="mono-s text-paper-500 text-sm">Публичная оферта интернет-магазина</div>
                        </div>
                        {errors.agree_offer && <span className="text-danger text-sm">{errors.agree_offer}</span>}
                      </label>
                      <label className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={form.agree_pd}
                          onChange={() => setField("agree_pd", !form.agree_pd)}
                          className="mt-1"
                        />
                        <div>
                          <div className="text-paper-100 font-semibold">
                            Согласие на обработку персональных данных
                          </div>
                          <div className="mono-s text-paper-500 text-sm">В соответствии с 152-ФЗ</div>
                        </div>
                        {errors.agree_pd && <span className="text-danger text-sm">{errors.agree_pd}</span>}
                      </label>
                      <label className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={form.agree_ads}
                          onChange={() => setField("agree_ads", !form.agree_ads)}
                          className="mt-1"
                        />
                        <div>
                          <div className="text-paper-100 font-semibold">Рассылка новостей и акций</div>
                          <div className="mono-s text-paper-500 text-sm">Не обязательно</div>
                        </div>
                      </label>
                    </div>
                    <Button
                      variant="primary"
                      disabled={submitting}
                      onClick={placeOrder}
                      className="w-full mt-4"
                      loading={submitting}
                    >
                      Оформить заказ
                    </Button>
                  </section>
                )}
                {step === "success" && order && (
                  <section className="space-y-4">
                    <h2 className="text-paper-100 font-semibold mb-2">Заказ оформлен</h2>
                    <div className="border border-line bg-ink-850 p-4">
                      <div className="flex justify-between mb-1">
                        <span className="text-paper-300">Номер заказа</span>
                        <span className="font-mono text-paper-100">№{order.id}</span>
                      </div>
                      <div className="flex justify-between mb-1">
                        <span className="text-paper-300">Статус</span>
                        <Badge
                          type={order.status === "pending_payment" ? "low" : "stock"}
                        >
                          {order.status === "pending_payment" ? "Ожидает оплаты" : "Оплачен"}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-paper-300">Итого</span>
                        <span className="font-text font-semibold text-paper-100 tabular-nums">
                          {formatPrice(order.total_amount)}
                        </span>
                      </div>
                    </div>
                    {order.status === "pending_payment" && (
                      <div className="space-y-3">
                        <p className="text-paper-300 text-sm">
                          Для перехода к оплате нажмите «Оплатить» — платёж создаётся у провайдера (симуляция).
                        </p>
                        <Button variant="primary" onClick={simulatePayment} className="w-full">
                          Оплатить (ЮKassa, симуляция)
                        </Button>
                        {paymentStatus && (
                          <p className={`mono-s text-sm ${paymentStatus === "paid" ? "text-success" : "text-paper-300"}`}>
                            Статус оплаты: {paymentStatus}
                          </p>
                        )}
                      </div>
                    )}
                    <Button variant="ghost" onClick={() => window.location.href="/account"} className="w-full mt-4">
                      В личный кабинет
                    </Button>
                  </section>
                )}
              </Reveal>
            </div>

            <div className="lg:col-span-4">
              <div className="border border-line bg-ink-850 p-6 sticky top-24">
                <h3 className="font-display text-display-md text-paper-100 uppercase mb-6">Итог заказа</h3>
                <div className="space-y-4 mb-6">
                  {items.map((item) => (
                    <div key={item.product_variant_id} className="flex justify-between items-baseline">
                      <div>
                        <span className="text-paper-100">{item.name}</span>
                        <p className="mono-s text-paper-500 text-xs">
                          ×{item.qty} · {item.price.toLocaleString("ru-RU")} ₽
                        </p>
                      </div>
                      <span className="font-mono text-paper-100 tabular-nums">
                        {formatPrice(item.price * item.qty * 100)}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="border-t border-line pt-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-paper-300">Товары</span>
                    <span className="text-paper-100 tabular-nums">{formatPrice(total * 100)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-paper-300">
                      Доставка{quote?.free_delivery ? " (бесплатно)" : ""}
                    </span>
                    <span className={`tabular-nums ${deliveryFee === 0 ? "text-success" : "text-paper-100"}`}>
                      {formatPrice(deliveryFee)}
                    </span>
                  </div>
                  <div className="flex justify-between font-semibold pt-2 border-t border-line">
                    <span className="text-paper-100">Итого к оплате</span>
                    <NumberRoll value={grandTotal / 100} className="text-paper-100 tabular-nums" />
                    <span className="text-paper-500">₽</span>
                  </div>
                </div>
                <p className="mono-s text-paper-500 text-xs mt-4">
                  Согласия разделяются и не предварительно отмечены. Отказ от рекламы не влияет на оформление.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="flex justify-center gap-2 mt-6 mb-8">
        {stepOrder.map((s, i) => (
          <button
            key={s}
            type="button"
            disabled={step === "success" || step === s}
            onClick={() => {
              if (s === "contacts") setStep("contacts")
              else if (s === "delivery") setStep("delivery")
              else if (s === "payment") setStep("payment")
              else if (s === "confirm") setStep("confirm")
            }}
            className={`w-8 h-8 rounded-full border flex items-center justify-center text-xs mono-s transition-colors ${
              stepIndex >= i ? "border-ember-600 bg-ember-600 text-paper-100" : "border-line bg-ink-850 text-paper-300"
            }`}
            aria-label={`Шаг ${i + 1}: ${stepLabel[s]}`}
          >
            {stepIndex >= i ? i + 1 : ""}
          </button>
        ))}
      </div>

      <div className="flex justify-between items-center px-4 py-4 border-t border-line bg-ink-900">
        <div className="flex items-center gap-2">
          <Button variant="ghost" disabled={step === "contacts" || step === "success"} onClick={prevStep}>
            Назад
          </Button>
          <Button variant="primary" disabled={step === "success"} onClick={nextStep}>
            Далее
          </Button>
        </div>
        {step !== "success" && (
          <a href="/cart" className="mono-s text-ember-300 underline-offset-4">
            Вернуться в корзину &rarr;
          </a>
        )}
      </div>

      <Toast message={toast.message} visible={toast.visible} onDismiss={() => setToast((t) => ({ ...t, visible: false }))} />
    </div>
  )
}
