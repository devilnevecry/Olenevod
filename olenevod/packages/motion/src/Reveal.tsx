import React, { ReactNode, useCallback, useEffect, useRef, useState } from "react"

/**
 * <Reveal> — появление элемента при входе во viewport
 * (IntersectionObserver: threshold 0.2, rootMargin "-10% 0px", один раз по
 * умолчанию). Анимация: opacity 0→1, y 24→0, 420 мс ease-out. Дети раскрываются
 * с stagger 70 мс (не более 8 элементов). При prefers-reduced-motion — только
 * fade 100 мс. См. ANIMATION_GUIDELINES.md A2.
 */
export interface RevealProps {
  children: ReactNode
  once?: boolean
  threshold?: number
  rootMargin?: string
  className?: string
}

export function Reveal({
  children,
  once = true,
  threshold = 0.2,
  rootMargin = "-10% 0px",
  className,
}: RevealProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)

  const handleIntersect = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [entry] = entries
      if (entry?.isIntersecting) {
        setVisible(true)
        if (once) observerRef.current?.disconnect()
      } else if (!once) {
        setVisible(false)
      }
    },
    [once]
  )

  const observerRef = useRef<IntersectionObserver | null>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    observerRef.current = new IntersectionObserver(handleIntersect, { threshold, rootMargin })
    observerRef.current.observe(el)
    return () => observerRef.current?.disconnect()
  }, [handleIntersect, threshold, rootMargin])

  const reduced =
    typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches

  const childList = React.Children.toArray(children)
  const maxStaggered = 8

  return (
    <div ref={ref} className={className} style={{ position: "relative" }} data-reveal={visible ? "visible" : "hidden"}>
      {childList.map((child, i) => {
        const offset = Math.min(i, maxStaggered - 1) * 70
        return (
          <div
            key={String(i)}
            style={{
              transitionDelay: `${offset}ms`,
              opacity: visible ? 1 : 0,
              transform: visible ? "none" : "translateY(24px)",
              transition: reduced
                ? "opacity 100ms linear"
                : `opacity 420ms cubic-bezier(0.16, 1, 0.3, 1), transform 420ms cubic-bezier(0.16, 1, 0.3, 1)`,
            }}
          >
            {child}
          </div>
        )
      })}
    </div>
  )
}
