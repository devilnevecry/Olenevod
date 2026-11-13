import { useEffect, useState } from "react"

/**
 * useMotionOK — возвращает true, если анимации разрешены
 * (не стоит prefers-reduced-motion: reduce).
 * См. ANIMATION_GUIDELINES.md §1.4, §4.
 */
export function useMotionOK(): boolean {
  const [ok, setOk] = useState(true)
  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)")
    const update = () => setOk(!mq.matches)
    update()
    mq.addEventListener("change", update)
    return () => mq.removeEventListener("change", update)
  }, [])
  return ok
}
