"use client"

import { Reveal } from "@olenevod/motion"
import { Badge, Button, Seal, Ticker } from "@olenevod/ui"

export default function DeliveryPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <section className="border-b border-line bg-ink-900 py-4">
        <div className="mx-auto max-w-[1440px] px-4">
          <h1 className="font-display text-display-xl text-paper-100 uppercase tracking-[0.005em] leading-[0.86]">
            Доставка
          </h1>
        </div>
      </section>

      <section className="bg-ink-900 py-12">
        <div className="mx-auto max-w-[1440px] px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Reveal once={true}>
              <div className="border border-line bg-ink-850 p-6">
                <Badge type="cold">Холод −18°C</Badge>
                <h3 className="text-paper-100 font-semibold mt-4 mb-2">Холодовая цепь</h3>
                <p className="text-paper-300 text-sm">
                  Сыровяленая оленина и мороженые заготовки едут в изотермической упаковке с хладоэлементами;
                  температура не поднимается выше −18°C на всём пути от склада до двери.
                </p>
              </div>
            </Reveal>
            <Reveal once={true}>
              <div className="border border-line bg-ink-850 p-6 mt-12 md:mt-0">
                <Badge type="stock">В наличии</Badge>
                <h3 className="text-paper-100 font-semibold mt-4 mb-2">Сроки и тарифы</h3>
                <p className="text-paper-300 text-sm">
                  Стоимость и срок доставки рассчитываются для вашего города и состава корзины на шаге
                  «Доставка» при оформлении заказа (GET /delivery/quote). Бесплатная доставка при достижении
                  порога зоны — обнуляется в чеке.
                </p>
              </div>
            </Reveal>
            <Reveal once={true}>
              <div className="border border-line bg-ink-850 p-6 mt-24 md:mt-0">
                <Badge type="demo">Демо</Badge>
                <h3 className="text-paper-100 font-semibold mt-4 mb-2">Пункты выдачи</h3>
                <p className="text-paper-300 text-sm">
                  Самовывоз и курьерская доставка доступны в городах из списка на главной. Список городов
                  уточняйте при выборе города доставки.
                </p>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      <section className="bg-ink-950 py-3">
        <Ticker kind="info" items={["ХОЛОДНАЯ ЦЕПЬ", "ДОСТАВКА ПО ТУНДРЕ", "ВОРКУТА • МОСКВА • СANKТ-ПЕТЕРБУРГ"]} speedSeconds={40} />
      </section>
    </div>
  )
}
