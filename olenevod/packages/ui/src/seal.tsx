import React from "react"
import "./olenevod.css"

export type SealVariant = "default" | "ink" | "white"

export interface SealProps extends React.SVGAttributes<SVGSVGElement> {
  variant?: SealVariant
  size?: number
}

export const Seal = React.forwardRef<SVGSVGElement, SealProps>(
  ({ className, variant = "default", size = 112, ...rest }, ref) => (
    <svg
      ref={ref}
      className={["ol-seal", className].filter(Boolean).join(" ")}
      data-variant={variant}
      width={size}
      height={size}
      viewBox="0 0 120 120"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Печать Оленевод"
      {...rest}
    >
      <defs>
        <filter id="ol-seal-seal" x="-10%" y="-10%" width="120%" height="120%">
          <feTurbulence type="fractalNoise" baseFrequency="0.6" numOctaves="3" result="noise" />
          <feDiffuseLighting in="noise" lighting-color="#c8a468" surfaceScale="2">
            <feDistantLight azimuth="45" elevation="60" />
          </feDiffuseLighting>
          <feComposite operator="in" in2="SourceGraphic" />
        </filter>
      </defs>
      <circle cx="60" cy="60" r="54" fill="none" stroke="var(--ol-color-brass-400)" stroke-width="4" />
      <path
        d="M 60 14 A 46 46 0 0 1 98 46 A 46 46 0 0 1 60 92 A 46 46 0 0 1 22 46 A 46 46 0 0 1 60 14 Z"
        fill="none"
        stroke="var(--ol-color-brass-400)"
        stroke-width="2"
      />
      <text text-anchor="middle" dy="0.35em" x="60" y="66" fill="var(--ol-color-brass-400)" font-family="var(--ol-font-family-mono)" font-size="10" letter-spacing="0.08em">
        ОЛЕНЕВОД
      </text>
    </svg>
  )
)
Seal.displayName = "Seal"
