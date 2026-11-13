"use client"

import { useEffect, useState } from "react"

import { Button, Seal } from "@olenevod/ui"

export default function Error({
  error,
  reset,
}: Readonly<{
  error: Error
  reset: () => void
}>) {
  const [recovered, setRecovered] = useState(false)

  useEffect(() => {
    console.error("[olenevod] 500 error boundary:", error)
  }, [error])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-ink-900 text-paper-100 p-6">
      <div className="flex flex-col items-center gap-6">
        <Seal variant="ink" className="w-48 h-48" />
        <div className="text-center">
          <h1 className="font-display text-display-xxl text-paper-100 uppercase tracking-[-0.01em] leading-[0.82]">
            500
          </h1>
          <p className="mono-s text-paper-300 mt-2">Внутренняя ошибка витрины</p>
        </div>
        {recovered ? null : (
          <Button variant="primary" onClick={() => {
            reset()
            setRecovered(true)
          }}>
            Попробовать ещё раз
          </Button>
        )}
        {!recovered && (
          <Button variant="ghost" onClick={() => window.location.href="/"}>
            Вернуться на главную
          </Button>
        )}
      </div>
    </div>
  )
}
