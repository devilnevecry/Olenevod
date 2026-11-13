"use client"

import { Reveal } from "@olenevod/motion"
import { Button, Seal, Ticker } from "@olenevod/ui"

export default function AboutPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <section className="border-b border-line bg-ink-900 py-4">
        <div className="mx-auto max-w-[1440px] px-4">
          <h1 className="font-display text-display-xl text-paper-100 uppercase tracking-[0.005em] leading-[0.86]">
            О нас
          </h1>
        </div>
      </section>

      <section className="bg-ink-900 py-12">
        <div className="mx-auto max-w-[1440px] px-4">
          <div className="flex flex-col lg:flex-row gap-12 items-start">
            <div className="flex-none lg:w-96">
              <Seal variant="ink" />
            </div>
            <div className="flex-1 space-y-6">
              <Reveal once={true}>
                <h2 className="font-display text-display-lg text-paper-100 uppercase tracking-[0.005em] leading-[0.95]">
                  История бренда
                </h2>
                <p className="text-paper-300" data-font="text">
                  Лавка сыровяленой оленины «Оленевод» — проект о северных заготовках, 전통ных рецептах и
                  холодовой цепи от Воркуты до вашего города.
                </p>
                <p className="text-paper-300" data-font="text">
                  Подробные утверждения о компании публикуются только после подтверждения владельцем
                  (поле помечено <code className="text-ember-300">TODO_OWNER</code>; в production не
                  публикуется без согласования).
                </p>
              </Reveal>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-ink-950 py-3">
        <Ticker kind="promo" items={"ПОПУЛЯРНОЕ!".split("")} speedSeconds={35} />
      </section>
    </div>
  )
}
