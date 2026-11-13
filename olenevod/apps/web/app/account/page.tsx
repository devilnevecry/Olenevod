"use client"

import { useCallback, useEffect, useState } from "react"
import { NumberRoll } from "@olenevod/motion"
import { Badge, Button, Input, EmptyState, Skeleton, Toast } from "@olenevod/ui"
import { authApi, formatPrice, ordersApi } from "@/lib/api"
import { Header } from "@/components/header"
import { useCart } from "@/components/cart-provider"

// @olenevod/ui не экспортирует табы; реализуем вкладки напрямую (таблица стилей ol-tabs в olenevod.css).
const TABS = [
  { id: "orders", label: "Заказы" },
  { id: "profile", label: "Профиль" },
]

type OrderSummary = {
  id: string
  status: string
  total_amount: number
  customer_name: string
  customer_phone: string
  items: Array<{ product_variant_id: string; qty: number; price: number }>
}

export default function AccountPage() {
  const cart = useCart()
  const [token, setToken] = useState<string | null>(() => {
    if (typeof window === "undefined") return null
    return window.localStorage.getItem("olenevod_token")
  })
  const [user, setUser] = useState<{ user_id: string; email: string; name: string } | null>(null)
  const [tab, setTab] = useState("orders")
  const [orders, setOrders] = useState<OrderSummary[]>([])
  const [ordersLoading, setOrdersLoading] = useState(false)
  const [activeStep, setActiveStep] = useState<string | null>(null)
  const [form, setForm] = useState<{ email: string; password: string; name: string }>({
    email: "",
    password: "",
    name: "",
  })
  const [authMode, setAuthMode] = useState<"login" | "register">("login")
  const [errors, setErrors] = useState<Record<string, string>>({})

  const loadOrders = useCallback(async () => {
    const raw = window.localStorage.getItem("olenevod_account_orders")
    const ids: string[] = raw ? JSON.parse(raw) : []
    if (!ids.length) {
      setOrders([])
      return
    }
    setOrdersLoading(true)
    const loaded: OrderSummary[] = []
    for (const id of ids) {
      try {
        const order = await ordersApi.get(id)
        loaded.push(order)
      } catch {
        /* skip orders that cannot be fetched */
      }
    }
    setOrders(loaded.sort((a, b) => b.id.localeCompare(a.id)))
    setOrdersLoading(false)
  }, [])

  useEffect(() => {
    if (token) loadOrders()
  }, [token, loadOrders])

  const setField = useCallback((key: string, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }, [])

  const submitAuth = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})
    try {
      if (authMode === "login") {
        const result = await authApi.login({ email: form.email, password: form.password })
        setToken(result.access_token)
        window.localStorage.setItem("olenevod_token", result.access_token)
        setUser({ user_id: result.user_id, email: form.email, name: form.name })
        setAuthMode("login")
      } else {
        const result = await authApi.register({
          email: form.email,
          name: form.name,
          password: form.password,
        })
        setUser({ user_id: result.user_id, email: result.email, name: form.name })
        setErrors({ __info: result.message })
      }
    } catch (err: any) {
      setErrors({ __api: err?.message ?? "Ошибка" })
    }
  }, [authMode, form])

  const repeatOrder = useCallback((order: OrderSummary) => {
    for (const item of order.items) {
      cart.add({
        product_variant_id: item.product_variant_id,
        name: item.product_variant_id,
        price: item.price / 100,
        qty: item.qty,
      })
    }
    window.location.href = "/cart"
  }, [cart])

  const statusLabel = (status: string) => {
    switch (status) {
      case "pending_payment":
        return "Ожидает оплаты"
      case "new":
        return "Оплачен, собирается"
      case "paid":
        return "Оплачен"
      default:
        return status
    }
  }

  const orderStatusDotClasses = (status: string) => {
    switch (status) {
      case "paid":
        return "border-ember-600 bg-ember-600 animate-pulse"
      case "new":
        return "border-ember-600"
      default:
        return "border-line bg-ink-850"
    }
  }

  const statusBadge = (status: string) => {
    switch (status) {
      case "pending_payment":
        return "low"
      case "new":
      case "paid":
        return "stock"
      default:
        return "out"
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <section className="border-b border-line bg-ink-900 py-4">
        <div className="mx-auto max-w-[1440px] px-4">
          <h1 className="font-display text-display-lg text-paper-100 uppercase tracking-[0.005em] leading-[0.95]">
            Личный кабинет
          </h1>
        </div>
      </section>

      <section className="bg-ink-900 py-8">
        <div className="mx-auto max-w-[1440px] px-4">
          {!token ? (
            <div className="max-w-md space-y-6">
              <div className="border border-line bg-ink-850 p-6">
                <h2 className="text-paper-100 font-semibold mb-4">
                  {authMode === "login" ? "Вход" : "Регистрация"}
                </h2>
                <form onSubmit={submitAuth} className="space-y-4">
                  {authMode === "register" && (
                    <Input
                      label="Имя"
                      value={form.name}
                      onChange={(e) => setField("name", e.target.value)}
                      placeholder="Иван Иванов"
                    />
                  )}
                  <Input
                    label="E-mail"
                    value={form.email}
                    onChange={(e) => setField("email", e.target.value)}
                    placeholder="ivan@example.com"
                  />
                  <Input
                    label="Пароль"
                    type="password"
                    value={form.password}
                    onChange={(e) => setField("password", e.target.value)}
                    placeholder="••••••••"
                  />
                  {errors.__api && <p className="text-danger text-sm">{errors.__api}</p>}
                  {errors.__info && <p className="text-success text-sm">{errors.__info}</p>}
                  <Button variant="primary" type="submit" className="w-full">
                    {authMode === "login" ? "Войти" : "Зарегистрироваться"}
                  </Button>
                </form>
                <p className="text-center mono-s text-paper-500 text-sm mt-4">
                  {authMode === "login"
                    ? "Нет аккаунта? "
                    : "Уже есть аккаунт? "}
                  <button
                    type="button"
                    onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}
                    className="text-ember-300 underline underline-offset-2"
                  >
                    {authMode === "login" ? "Зарегистрироваться" : "Войти"}
                  </button>
                </p>
              </div>
              <Toast message={errors.__info ?? ""} visible={!!errors.__info} onDismiss={() => setErrors({})} />
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              <div className="lg:col-span-3 space-y-4">
                <div className="border border-line bg-ink-850 p-4">
                  <div className="font-mono text-paper-500 text-xs uppercase tracking-[0.06em] mb-2">
                    Профиль
                  </div>
                  <div className="text-paper-100 font-semibold">{user?.email}</div>
                  <div className="mono-s text-paper-500 text-sm">ID: {user?.user_id}</div>
                </div>
                <div className="flex gap-2">
                  {TABS.map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setTab(t.id)}
                      className={`ol-tab text-xs px-3 py-2 mono-s ${
                        tab === t.id
                          ? "text-paper-100 border-ember-600"
                          : "text-paper-300 border-transparent"
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={() => {
                    window.localStorage.removeItem("olenevod_token")
                    setToken(null)
                    setUser(null)
                    setOrders([])
                  }}
                  className="ol-btn ol-btn-ghost data-[variant=ghost]:p-0 ghost-link"
                  data-variant="ghost"
                  style={{ padding: 0, background: "none", border: "none", color: "inherit", font: "inherit" }}
                >
                  Выйти
                </button>
              </div>
              <div className="lg:col-span-9">
                {tab === "orders" && (
                  <div className="space-y-6">
                    <div className="flex items-baseline justify-between">
                      <h2 className="text-paper-100 font-semibold">Заказы</h2>
                      <span className="mono-s text-paper-500">{orders.length}</span>
                    </div>
                    {ordersLoading ? (
                      <div className="flex items-center justify-center py-20">
                        <Skeleton className="w-48 h-8 mx-auto" />
                      </div>
                    ) : orders.length === 0 ? (
                      <EmptyState
                        title="Заказов пока нет"
                        description="Оформите первый заказ в каталоге — он появится здесь со статусом."
                        ctaLabel="Перейти в каталог"
                        onCta={() => {
                          window.location.href = "/catalog"
                        }}
                      />
                    ) : (
                      <div className="space-y-4">
                        {orders.map((order) => (
                          <div
                            key={order.id}
                            className="border border-line bg-ink-850 p-4"
                          >
                            <div className="flex justify-between items-baseline mb-2">
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-paper-100">№{order.id}</span>
                                <Badge type={statusBadge(order.status)}>
                                  {statusLabel(order.status)}
                                </Badge>
                              </div>
                              <span className="font-text font-semibold text-paper-100 tabular-nums">
                                {formatPrice(order.total_amount)}
                              </span>
                            </div>
                            <div className="mt-3 mb-2 relative">
                              <div className="absolute left-1.5 top-2.5 h-[2px] w-full bg-line" />
                              <div
                                className="absolute left-1.5 top-2 h-[4px] bg-ember-600"
                                style={{
                                  width:
                                    order.status === "pending_payment"
                                      ? "0%"
                                      : order.status === "new"
                                        ? "50%"
                                        : "100%",
                                  transformOrigin: "left",
                                  transition: "width 520ms cubic-bezier(0.65, 0, 0.35, 1)",
                                }}
                              />
                              <div className="flex justify-between text-mono-s text-paper-500 text-xs mt-2">
                                <span>Оформлен</span>
                                <span>Оплачен</span>
                                <span>Собран</span>
                              </div>
                              <div className="flex justify-center mt-1">
                                <div
                                  className={`w-2.5 h-2.5 rounded-full border-2 ${orderStatusDotClasses(order.status)}`}
                                />
                              </div>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-mono-s text-paper-500 text-sm mb-3">
                              <span>{order.customer_name}</span>
                              <span>{order.customer_phone}</span>
                              <span>{order.items.reduce((s, i) => s + i.qty, 0)} позиций</span>
                            </div>
                            <div className="flex gap-2">
                              <button
                                type="button"
                                onClick={() => repeatOrder(order)}
                                className="ol-chip"
                              >
                                Повторить заказ
                              </button>
                              <button
                                type="button"
                                onClick={() => setActiveStep(order.id)}
                                className="ol-chip"
                              >
                                Состав заказа
                              </button>
                            </div>
                            {activeStep === order.id && (
                              <div className="mt-4 border-t border-line pt-4 space-y-3">
                                <h3 className="mono-s text-paper-300 text-xs uppercase tracking-[0.06em]">
                                  Состав
                                </h3>
                                {order.items.map((item) => (
                                  <div key={item.product_variant_id} className="flex justify-between">
                                    <span className="text-paper-300">{item.product_variant_id}</span>
                                    <span className="font-mono text-paper-100 tabular-nums">
                                      ×{item.qty} · {formatPrice(item.price * 100)}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                {tab === "profile" && (
                  <div className="border border-line bg-ink-850 p-6 space-y-4">
                    <h2 className="text-paper-100 font-semibold">Профиль и согласия</h2>
                    <p className="text-paper-300 text-sm">
                      E-mail: {user?.email} (верификация кода — через API регистрации, simulated SMTP).
                    </p>
                    <p className="text-paper-300 text-sm">
                      Заказы привязываются к устройству (localStorage); привязка к профилю — через e-mail при оформлении.
                    </p>
                    <div className="flex gap-2">
                      <Button variant="ghost" onClick={() => {}}>
                        Скачать данные (152-ФЗ)
                      </Button>
                      <Button variant="ghost" onClick={() => {}}>
                        Удалить данные
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
          <Toast message={""} visible={false} onDismiss={() => {}} />
        </div>
      </section>
    </div>
  )
}
