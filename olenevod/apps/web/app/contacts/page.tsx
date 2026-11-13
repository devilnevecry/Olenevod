"use client"

import { Reveal } from "@olenevod/motion"
import { Button, Seal, Ticker } from "@olenevod/ui"

export default function ContactsPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <section className="border-b border-line bg-ink-900 py-4">
        <div className="mx-auto max-w-[1440px] px-4">
          <h1 className="font-display text-display-xl text-paper-100 uppercase tracking-[0.005em] leading-[0.86]">
            Контакты
          </h1>
        </div>
      </section>

      <section className="bg-ink-900 py-12">
        <div className="mx-auto max-w-[1440px] px-4">
          <Reveal once={true}>
            <div className="border border-line bg-ink-850 p-8">
              <h2 className="font-display text-display-lg text-paper-100 uppercase tracking-[0.005em] leading-[0.95] mb-4">
                Обратная связь
              </h2>
              <p className="text-paper-300" data-font="text">
                Интернет-магазин сыровяленой оленины «Оленевод». Заказы оформляются на этом сайте;
                вопросы по доставке и оплате — в личном кабинете по номеру заказа.
              </p>
              <div className="mt-6 space-y-3 mono-s text-paper-300">
                <div>E-mail: <a className="text-ember-300">hello@olenevod.test</a></div>
                <div>Телефон: <a className="text-ember-300">+8 800 000 00 00</a></div>
                <div>Города доставки: Москва, Санкт-Петербург (из seed-каталога)</div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="bg-ink-950 py-3">
        <Ticker kind="info" items={["СВЯЗЬ С НАМИ", "ОТВЕЧАЕМ В ТЕЧЕНИЕ ДНЯ"]} speedSeconds={40} />
      </section>
    </div>
  )
}
