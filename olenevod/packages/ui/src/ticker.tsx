import React from "react"
import "./olenevod.css"

export interface TickerProps extends React.HTMLAttributes<HTMLDivElement> {
  kind?: "info" | "promo"
  items: string[]
  paused?: boolean
  speedSeconds?: number
}

export const Ticker = React.forwardRef<HTMLDivElement, TickerProps>(
  ({ className, kind = "info", items, paused = false, speedSeconds = 40, ...rest }, ref) => {
    const list = [...items, ...items] // дублирование для бесшовной ленты
    return (
      <div
        ref={ref}
        className={["ol-ticker", className].filter(Boolean).join(" ")}
        data-kind={kind}
        data-paused={paused}
        role="region"
        aria-roledescription="лента"
        {...rest}
      >
        <div className="ol-ticker-track" style={{ animationDuration: `${speedSeconds}s` }}>
          {list.map((item, i) => (
            <React.Fragment key={i}>
              {item}
              <span className="ol-star">★</span>
            </React.Fragment>
          ))}
        </div>
      </div>
    )
  }
)
Ticker.displayName = "Ticker"
