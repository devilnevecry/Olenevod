import { test, expect, type Page } from "@playwright/test"

// E2E сценарии этапа 13 (витрина II).
// Шаги S1 (корзина), S5–S7 (чекаут оформляет заказ на реальных данных),
// S9–S10, S12 (личный кабинет показывает заказы).
// Требуют запущенного API (порт 8000, БД olenevod_test с сидом stage 13)
// и dev-сервера Next.js (порт 3000).

const API_BASE = "http://localhost:8000"
const MOSCOW_ID = "11111111-1111-1111-1111-111111111001"
const VARIANT_ID = "44444444-4444-4444-4444-444444444002"

async function apiFetch(path: string, init?: RequestInit) {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) {
    throw new Error(`API ${path} responded ${response.status}: ${await response.text()}`)
  }
  return response.json()
}

async function dismissCookies(page: Page) {
  const btn = page.getByRole("button", { name: /^Принять$/ })
  if ((await btn.count()) > 0 && (await btn.isVisible())) {
    await btn.click()
  }
}

test.describe("S1 — корзина", () => {
  test("шаги 1–6: добавить в корзину, изменить количество, удалить, итог пересчитывается", async ({
    page,
  }) => {
    await page.goto(`/catalog?city_id=${MOSCOW_ID}`)
    await dismissCookies(page)
    await expect(page.getByRole("heading", { name: "Каталог" })).toBeVisible()
    await expect(page.getByText("Продукт для заказа")).toBeVisible()

    // 1–2. Добавить товар в корзину (последняя карточка — «Продукт для заказа», A7: тост).
    await page.getByRole("button", { name: /В корзину/ }).last().click()
    await expect(page.getByRole("status").filter({ hasText: /Добавлено: Продукт для заказа/ })).toBeVisible()

    // 3. Открыть корзину — товар в списке, итог 95 ₽.
    await page.getByRole("button", { name: /Корзина/ }).first().click()
    await expect(page).toHaveURL(/\/cart/)
    await expect(page.getByRole("heading", { name: "Корзина", exact: true })).toBeVisible()
    await expect(page.getByText("Продукт для заказа")).toBeVisible()
    await expect(page.getByText("95 ₽")).toBeVisible()

    // 4. Увеличить количество — итог пересчитывается (A9 NumberRoll).
    await page.getByRole("button", { name: /Увеличить количество/ }).first().click()
    await expect(page.getByText(/190\s*₽/).first()).toBeVisible()

    // 5. Уменьшить — обратно 95 ₽.
    await page.getByRole("button", { name: /Уменьшить количество/ }).first().click()
    await expect(page.getByText(/95\s*₽/).first()).toBeVisible()

    // 6. Удалить — корзина пуста.
    await page.getByRole("button", { name: /Удалить Продукт для заказа/ }).first().click()
    await expect(page.getByRole("status").filter({ hasText: /Удалено из корзины: Продукт для заказа/ })).toBeVisible()
    await expect(page.getByText("Корзина пуста")).toBeVisible()
  })
})

test.describe("S5–S7 — чекаут оформляет заказ на реальных данных", () => {
  test("оформление заказа с доставкой, проверка через API", async ({ page }) => {
    // Корзина с одним товаром (последняя карточка — «Продукт для заказа»).
    await page.goto(`/catalog?city_id=${MOSCOW_ID}`)
    await dismissCookies(page)
    await page.getByRole("button", { name: /В корзину/ }).last().click()
    await page.getByRole("button", { name: /Корзина/ }).first().click()
    await expect(page).toHaveURL(/\/cart/)
    await page.getByRole("button", { name: /Оформить заказ/ }).click()

    // Шаг 1: контакты.
    await expect(page.getByRole("heading", { name: /Контакты/ })).toBeVisible()
    await page.getByPlaceholder("Иван Иванов").fill("Тестовый Покупатель")
    await page.getByPlaceholder("+7 900 000 00 00").fill("+79000000000")
    await page.getByPlaceholder("ivan@example.com").fill("order-1@olenevod.test")
    await page.getByRole("button", { name: /Далее/ }).click()

    // Шаг 2: доставка — город Москва, расчёт доставки через GET /delivery/quote.
    await expect(page.getByRole("heading", { name: /Доставка/ })).toBeVisible()
    await page.locator("select").selectOption("Москва")
    await expect(page.getByText("Москва внутри МКАД")).toBeVisible()
    await expect(page.getByText(/6,00 ₽/).first()).toBeVisible()
    await expect(page.getByText("3 дн.")).toBeVisible()
    await page.getByRole("button", { name: /Далее/ }).click()

    // Шаг 3: оплата — ЮKassa (симуляция).
    await expect(page.getByRole("heading", { name: /Оплата/ })).toBeVisible()
    await page.getByRole("button", { name: /Далее/ }).click()

    // Шаг 4: подтверждение — согласия не предотмечены, ставим галочки.
    await expect(page.getByRole("heading", { name: /Подтверждение/ })).toBeVisible()
    await page.getByRole("checkbox", { name: /Согласие с офертой публичной/ }).check()
    await page.getByRole("checkbox", { name: /Согласие на обработку персональных данных/ }).check()
    await page.getByRole("button", { name: /Оформить заказ/ }).click()

    // Заказ создан: страница успеха с номером и статусом.
    await expect(page.getByRole("heading", { name: /Заказ оформлен/ })).toBeVisible()
    const orderNumber = page.locator('text=/^№[0-9a-f-]{36}$/')
    await expect(orderNumber).toBeVisible()
    const orderIdText = await orderNumber.textContent()
    const orderId = orderIdText!.replace("№", "").trim()
    await expect(page.getByText("Ожидает оплаты")).toBeVisible()
    await expect(page.getByText(/95,00 ₽/)).toBeVisible() // стоимость товара (доставка оплачивается отдельно)

    // Проверка заказа через реальное API.
    const order = await apiFetch(`/orders/${orderId}`)
    expect(order.status).toBe("pending_payment")
    expect(order.total_amount).toBe(9500)
    expect(order.items.length).toBe(1)
    expect(order.items[0].product_variant_id).toBe(VARIANT_ID)

    // Оплата: вызов вебхука провайдера — платёж ещё не создан провайдером (404),
    // фронтенд обрабатывает без сбоя; статус через GET /payments/{id}/status — 404.
    await page.getByRole("button", { name: /Оплатить \(ЮKassa, симуляция\)/ }).click()
    await expect(page.getByRole("status").filter({ hasText: /не найден у провайдера/ })).toBeVisible()
    const paymentResponse = await page.request.fetch(`${API_BASE}/payments/${orderId}/status`)
    expect(paymentResponse.status()).toBe(404)
  })
})

test.describe("S9–S10, S12 — личный кабинет показывает заказы", () => {
  test("история заказов, статус, состав, повтор", async ({ page }) => {
    // Создаём заказ напрямую через реальное API.
    const order = (await apiFetch("/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        city_id: MOSCOW_ID,
        customer_name: "Покупатель ЛК",
        customer_phone: "+79000000000",
        items: [{ product_variant_id: VARIANT_ID, qty: 2 }],
      }),
    })) as { id: string; status: string; total_amount: number }

    // Токен и список заказов в локальном хранилище — как после оформления через UI.
    await page.goto("/account")
    await dismissCookies(page)
    await page.evaluate(
      ([id]) => {
        localStorage.setItem("olenevod_token", "fake-token")
        localStorage.setItem("olenevod_account_orders", JSON.stringify([id]))
      },
      [order.id],
    )
    await page.reload()

    await expect(page.getByRole("heading", { name: /Личный кабинет/ })).toBeVisible()
    await expect(page.getByText(new RegExp(order.id))).toBeVisible()
    await expect(page.getByText("Ожидает оплаты")).toBeVisible()
    await expect(page.getByText(/190,00 ₽/)).toBeVisible()

    // Состав заказа (A20: хронометраж статуса).
    await page.getByRole("button", { name: /Состав заказа/ }).first().click()
    await expect(page.getByText(VARIANT_ID)).toBeVisible()

    // Повторить заказ — позиции попадают в корзину.
    await page.getByRole("button", { name: /Повторить заказ/ }).first().click()
    await expect(page.getByRole("heading", { name: "Корзина", exact: true })).toBeVisible()
    await expect(page.getByText(VARIANT_ID)).toBeVisible()
    await expect(page.getByText(/190\s*₽/).first()).toBeVisible()
  })

  test("регистрация через форму (e-mail simulated)", async ({ page }) => {
    await page.goto("/account")
    await dismissCookies(page)
    await page.getByRole("button", { name: /Зарегистрироваться/ }).click()
    await page.getByPlaceholder("Иван Иванов").fill("Тестовый")
    await page.getByPlaceholder("ivan@example.com").fill(`order-reg-${Date.now()}@olenevod.test`)
    await page.getByPlaceholder("••••••••").fill("test-password-123")
    await page.getByRole("button", { name: /Зарегистрироваться/ }).click()
    await expect(page.getByRole("status").filter({ hasText: /simulated/ })).toBeVisible()
  })
})
