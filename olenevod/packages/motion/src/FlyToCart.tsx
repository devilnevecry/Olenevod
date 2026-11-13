import { useEffect, useRef, useState, useCallback } from "react"

/**
 * <FlyToCart> — копия миниатюры товара летит по дуге к иконке корзины
 * (ANIMATION_GUIDELINES.md A7). spring-cart, ≤ 600 мс, pointer-events:none.
 * Серверный запрос идёт параллельно анимации.
 */
export interface FlyToCartProps {
  active: boolean
  from: { x: number; y: number }
  to: { x: number; y: number }
  src: string
  size?: number
  durationMs?: number
  onFinish?: () => void
}

function easeOutCubic(t: number) {
  return 1 - Math.pow(1 - t, 3)
}

export function FlyToCart({
  active,
  from,
  to,
  src,
  size = 48,
  durationMs = 550,
  onFinish,
}: FlyToCartProps) {
  const frame = useRef<number | null>(null)
  const start = useRef<number | null>(null)
  const [progress, setProgress] = useState(0)

  const run = useCallback(() => {
    const t0 = performance.now()
    start.current = t0
    setProgress(0)
    ;(function loop() {
      if (frame.current !== null) cancelAnimationFrame(frame.current)
      const now = performance.now()
      const p = Math.min((now - t0) / durationMs, 1)
      const ease = easeOutCubic(p)
      setProgress(ease)
      if (p < 1) {
        frame.current = requestAnimationFrame(loop)
      } else {
        setProgress(0)
        onFinish?.()
      }
    })()
  }, [durationMs, onFinish])

  useEffect(() => {
    if (!active) return
    run()
  }, [active, run])

  useEffect(() => {
    return () => {
      if (frame.current !== null) cancelAnimationFrame(frame.current)
    }
  }, [])

  if (!active) return null

  const x = from.x + (to.x - from.x) * progress
  const y = from.y + (to.y - from.y) * progress - 120 * progress * (1 - progress) // дуга вверх

  return (
    <img
      src={src}
      alt=""
      aria-hidden="true"
      style={{
        position: "fixed",
        left: x - size / 2,
        top: y - size / 2,
        width: size,
        height: size,
        borderRadius: "50%",
        objectFit: "cover",
        pointerEvents: "none",
        zIndex: 9999,
        boxShadow: "0 24px 48px -24px rgba(0,0,0,0.6)",
      }}
    />
  )
}
