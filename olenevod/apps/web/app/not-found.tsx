"use client"

import { Reveal } from "@olenevod/motion"
import { Button, Seal } from "@olenevod/ui"

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-ink-900 text-paper-100 p-6">
      <div className="flex flex-col items-center gap-6">
        <Seal variant="ink" className="w-48 h-48" />
        <Reveal once={true}>
          <div className="relative w-48 h-48">
            <svg width="256" height="256" viewBox="0 0 256 256" aria-hidden="true">
              <defs>
                <marker id="hoof" markerWidth="12" markerHeight="12" refX="6" refY="6" markerUnits="strokeWidth">
                  <circle cx="6" cy="6" r="5" fill="#EE7D5A" />
                </marker>
              </defs>
              <path
                d="M 40 200 Q 70 170 110 190 Q 150 210 190 190 Q 230 170 256 200"
                fill="none"
                stroke="#14100D"
                strokeWidth="4"
                strokeLinecap="round"
              />
              <path
                className="ol-deer-track"
                d="M 40 200 Q 70 170 110 190 Q 150 210 190 190 Q 230 170 256 200"
                fill="none"
                stroke="#EE7D5A"
                strokeWidth="5"
                strokeLinecap="round"
                strokeDasharray="420"
                strokeDashoffset="420"
              />
            </svg>
            <p className="absolute -bottom-6 text-xs mono-s text-paper-500 uppercase tracking-[0.08em]">
              след потерян
            </p>
          </div>
        </Reveal>
        <div className="text-center">
          <h1 className="font-display text-display-xxl text-paper-100 uppercase tracking-[-0.01em] leading-[0.82]">
            404
          </h1>
          <p className="mono-s text-paper-300 mt-2">Страница не найдена</p>
        </div>
        <Button variant="primary" onClick={() => window.location.href="/"}>
          Вернуться на главную
        </Button>
      </div>
    </div>
  )
}
