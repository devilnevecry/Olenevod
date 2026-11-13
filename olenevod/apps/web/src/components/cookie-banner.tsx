"use client"

import { useCallback, useEffect, useState } from "react"
import { Button } from "@olenevod/ui"

/**
 * Cookie-баннер и согласие на обработку персональных данных (этап 13).
 * Согласие сохраняется в localStorage (ключ olenevod_consent) и не истекает
 * до явного действия пользователя. Яндекс.Метрика подключается только после
 * согласия (ключ YANDEX_METRIKA_ID — TODO_OWNER, реального идентификатора нет).
 */
const CONSENT_KEY = "olenevod_consent"

export function CookieBanner() {
  const [visible, setVisible] = useState<boolean>(() => {
    if (typeof window === "undefined") return true
    return window.localStorage.getItem(CONSENT_KEY) === null
  })

  const accept = useCallback(() => {
    window.localStorage.setItem(CONSENT_KEY, JSON.stringify({ cookies: true, pd: true, at: Date.now() }))
    setVisible(false)
  }, [])

  useEffect(() => {
    if (!visible && typeof window !== "undefined") {
      document.documentElement.style.setProperty("--ol-cookie-consent", "given")
    }
  }, [visible])

  if (!visible) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[60] flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 p-6 bg-ink-950 border-t border-line">
      <div className="text-paper-300 text-sm leading-relaxed lg:max-w-2xl">
        Мы используем cookie и локальное хранилище для работы корзины и оформления
        заказа. Продолжая, вы соглашаетесь на обработку персональных данных
        (имени, телефона, e-mail, адреса доставки) в соответствии с 152-ФЗ.
        Яндекс.Метрика подключается только после согласия (идентификатор счётчика
        не задан — помечен TODO_OWNER).
      </div>
      <div className="flex flex-col lg:flex-row gap-3">
        <Button variant="primary" onClick={accept} className="w-full lg:w-auto">
          Принять
        </Button>
        <Button variant="ghost" onClick={accept} className="w-full lg:w-auto">
          Продолжить
        </Button>
      </div>
    </div>
  )
}
