import { useEffect, useRef, useState, useCallback } from "react"

/**
 * <NumberRoll> — «ролл» числа: старое уходит вверх, новое приходит снизу,
 * 200 мс (ANIMATION_GUIDELINES.md A9, A14). При reduced-motion — мгновенная смена.
 */
export interface NumberRollProps {
  value: number | string
  format?: (n: number) => string
  durationMs?: number
  className?: string
}

function easeOutCubic(t: number) {
  return 1 - Math.pow(1 - t, 3)
}

export function NumberRoll({
  value,
  format = (n) => n.toLocaleString("ru-RU"),
  durationMs = 200,
  className,
}: NumberRollProps) {
  const [current, setCurrent] = useState(String(value))
  const prevValue = useRef(String(value))
  const frame = useRef<number | null>(null)

  const run = useCallback(() => {
    const from = parseFloat(prevValue.current.replace(/[^0-9.,-]/g, "").replace(",", ".")) ?? 0
    const to = parseFloat(String(value).replace(/[^0-9.,-]/g, "").replace(",", ".")) ?? 0
    if (!Number.isFinite(from) || !Number.isFinite(to) || from === to) {
      setCurrent(String(value))
      return
    }
    const t0 = performance.now()
    ;(function loop() {
      if (frame.current !== null) cancelAnimationFrame(frame.current)
      const now = performance.now()
      const p = Math.min((now - t0) / durationMs, 1)
      const ease = easeOutCubic(p)
      setCurrent(format(from + (to - from) * ease))
      prevValue.current = String(value)
      if (p < 1) {
        frame.current = requestAnimationFrame(loop)
      }
    })()
  }, [value, durationMs, format])

  useEffect(() => {
    run()
  }, [run])

  useEffect(() => {
    return () => {
      if (frame.current !== null) cancelAnimationFrame(frame.current)
    }
  }, [])

  const reduced =
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches

  return (
    <span className={["ol-numberroll", className].filter(Boolean).join(" ")} style={{ display: "inline-block" }}>
      {reduced ? format(Number(String(value).replace(/[^0-9.,-]/g, "").replace(",", ".")) || 0) : current}
    </span>
  )
}
