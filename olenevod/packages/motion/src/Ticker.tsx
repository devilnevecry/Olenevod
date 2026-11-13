import React from "react"

/**
 * <Ticker> — бегущая лента (ANIMATION_GUIDELINES.md A4).
 * CSS translateX(0 → -50%), linear, бесконечно; скорость 60 px/s десктоп /
 * 40 px/s мобильные; пауза по hover/фокусу. При reduced-motion — статично.
 */
export interface TickerProps {
  items: string[]
  speedDesktopPxPerS?: number
  speedMobilePxPerS?: number
  paused?: boolean
  className?: string
}

const secondsForWidth = (pxPerSecond: number, itemWidthPx: number) => itemWidthPx / pxPerSecond

export function Ticker({
  items,
  speedDesktopPxPerS = 60,
  speedMobilePxPerS = 40,
  paused = false,
  className,
}: TickerProps) {
  const list = [...items, ...items]
  return (
    <div
      className={["ol-mticker", className].filter(Boolean).join(" ")}
      data-paused={paused}
      role="region"
      aria-roledescription="лента"
      aria-label="бегущая строка"
    >
      <div className="ol-mticker-track">
        {list.map((item, i) => (
          <React.Fragment key={i}>
            <span className="ol-mticker-item">{item}</span>
            <span className="ol-mticker-star">★</span>
          </React.Fragment>
        ))}
      </div>
    </div>
  )
}
