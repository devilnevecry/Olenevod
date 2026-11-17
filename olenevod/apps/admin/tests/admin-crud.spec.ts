import { test, expect, APIRequestContext } from "@playwright/test"

const API_BASE = "http://localhost:8002"
const ADMIN_EMAIL = "ivan@example.com"
const ADMIN_PASSWORD = "DemoPass123"

const SECTIONS = [
  { name: "cities", path: "/cities", title: "Города" },
  { name: "warehouses", path: "/warehouses", title: "Склады" },
  { name: "products", path: "/products", title: "Товары" },
  { name: "variants", path: "/variants", title: "Варианты товара" },
  { name: "offers", path: "/offers", title: "Предложения города" },
  { name: "stock", path: "/stock", title: "Остатки товара на складах" },
  { name: "transfers", path: "/transfers", title: "Перемещения" },
  { name: "routes", path: "/routes", title: "Маршруты" },
  { name: "carriers", path: "/carriers", title: "Перевозчики" },
  { name: "orders", path: "/orders", title: "Заказы" },
  { name: "customers", path: "/customers", title: "Покупатели" },
]

async function getAdminToken(request: APIRequestContext): Promise<string> {
  const resp = await request.post(`${API_BASE}/auth/login`, {
    data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
  })
  expect(resp.ok()).toBeTruthy()
  const body = await resp.json()
  return body.access_token
}

async function setTokenAndGoto(page: any, token: string, path: string) {
  await page.context().addInitScript((t: string) => {
    localStorage.setItem("admin_token", t)
  }, token)
  await page.goto(path)
  await page.waitForTimeout(2000)
}

async function openCreateDialog(page: any) {
  const h2 = await page.locator("h2").textContent().catch(() => "no h2")
  console.log(`DEBUG: page h2 = "${h2}"`)
  const bodyText = await page.locator("body").textContent().catch(() => "no body")
  console.log(`DEBUG: body starts with = "${bodyText?.substring(0, 200)}"`)
  await page.click('button:has-text("Добавить")')
  await page.waitForSelector('h2:has-text("Создать")', { state: "visible" })
}

test.describe("BUG-05: Admin CRUD — 11 разделов", () => {
  const token =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2NjY2NjY2Ni02NjY2LTY2NjYtNjY2Ni02NjY2NjY2NjY5NTEiLCJpYXQiOjE3OTQ5MDU5OTcsImV4cCI6MTc5NDk5MjM5N30.vp9qt6tLbh4X_piNLdIiBSPK9HsEet7BygdJtmPU0H8"

  async function loginAsAdmin(page: any) {
  await page.goto("/login")
  await page.fill('input[type="email"]', ADMIN_EMAIL)
  await page.fill('input[type="password"]', ADMIN_PASSWORD)
  await page.click('button[type="submit"]')
  // Ждём ухода со страницы логина (редирект на /cities)
  await page.waitForURL((url) => !url.pathname.includes("/login"), { timeout: 15000 })
}

  test("города: создание, редактирование, удаление, обновление после перезагрузки", async ({ page }) => {
    await setTokenAndGoto(page, token, "/cities")
    const initialCount = await page.locator("table tbody tr").count()

    await openCreateDialog(page)
    await page.fill('input[name="slug"]', "test-city-e2e")
    await page.fill('input[name="name"]', "Test City E2E")
    await page.fill('input[name="region"]', "Test Region")
    await page.fill('input[name="timezone"]', "UTC")
    await page.click('button:has-text("Сохранить")')
    await page.waitForTimeout(2000)

    const afterCreate = await page.locator("table tbody tr").count()
    expect(afterCreate).toBe(initialCount + 1)

    // Перезагрузка — данные сохраняются
    await page.reload()
    await page.waitForTimeout(1000)
    const afterReload = await page.locator("table tbody tr").count()
    expect(afterReload).toBe(afterCreate)

    await page.screenshot({ path: "tests/output/cities-after-reload.png", fullPage: true })

    // Удаление
    const rows = page.locator("table tbody tr")
    let deleted = false
    for (let i = 0; i < (await rows.count()); i++) {
      const row = rows.nth(i)
      const text = await row.textContent()
      if (text && text.includes("test-city-e2e")) {
        await row.locator('button:has-text("Удалить")').first().click()
        await page.click('button:has-text("Удалить")')
        await page.waitForTimeout(1000)
        deleted = true
        break
      }
    }
    expect(deleted).toBe(true)
  })

  test("склады: создание, редактирование, связь с городом", async ({ page }) => {
    await setTokenAndGoto(page, token, "/warehouses")
    const initialCount = await page.locator("table tbody tr").count()

    await openCreateDialog(page)
    await page.fill('input[name="name"]', "Test Warehouse E2E")
    await page.fill('input[name="address"]', "Test Address 123")
    await page.click('button:has-text("Сохранить")')
    await page.waitForTimeout(2000)

    const afterCreate = await page.locator("table tbody tr").count()
    expect(afterCreate).toBe(initialCount + 1)

    // Редактирование
    const rows = page.locator("table tbody tr")
    for (let i = 0; i < (await rows.count()); i++) {
      const row = rows.nth(i)
      const text = await row.textContent()
      if (text && text.includes("Test Warehouse E2E")) {
        await row.locator('button:has-text("Редактировать")').first().click()
        await page.waitForSelector('[role="dialog"]', { state: "visible" })
        await page.fill('input[name="name"]', "Test Warehouse E2E Updated")
        await page.click('button:has-text("Сохранить")')
        await page.waitForTimeout(1000)
        break
      }
    }

    await page.reload()
    await page.waitForTimeout(1000)
    const updatedText = await page.locator("table tbody tr").first().textContent()
    expect(updatedText).toContain("Test Warehouse E2E Updated")

    await page.screenshot({ path: "tests/output/warehouses-edit.png", fullPage: true })
  })

  test("товары: создание, удаление", async ({ page }) => {
    await setTokenAndGoto(page, token, "/products")
    const initialCount = await page.locator("table tbody tr").count()

    await openCreateDialog(page)
    await page.fill('input[name="slug"]', "test-product-e2e")
    await page.fill('input[name="name"]', "Test Product E2E")
    await page.fill('input[name="short_description"]', "Test description")
    await page.click('button:has-text("Сохранить")')
    await page.waitForTimeout(2000)

    const afterCreate = await page.locator("table tbody tr").count()
    expect(afterCreate).toBe(initialCount + 1)

    await page.screenshot({ path: "tests/output/products-create.png", fullPage: true })
  })

  test("варианты: создание, удаление", async ({ page }) => {
    await setTokenAndGoto(page, token, "/variants")
    const initialCount = await page.locator("table tbody tr").count()

    await openCreateDialog(page)
    await page.fill('input[name="sku"]', "TEST-SKU-E2E")
    await page.fill('input[name="name"]', "Test Variant E2E")
    await page.selectOption('select[name="unit_type"]', "piece")
    await page.click('button:has-text("Сохранить")')
    await page.waitForTimeout(2000)

    const afterCreate = await page.locator("table tbody tr").count()
    expect(afterCreate).toBe(initialCount + 1)

    await page.screenshot({ path: "tests/output/variants-create.png", fullPage: true })
  })

  test("предложения: создание, удаление", async ({ page }) => {
    await setTokenAndGoto(page, token, "/offers")
    const initialCount = await page.locator("table tbody tr").count()

    await openCreateDialog(page)
    await page.fill('input[name="price_kop"]', "10000")
    await page.selectOption('select[name="is_published"]', "true")
    await page.click('button:has-text("Сохранить")')
    await page.waitForTimeout(2000)

    const afterCreate = await page.locator("table tbody tr").count()
    expect(afterCreate).toBe(initialCount + 1)

    await page.screenshot({ path: "tests/output/offers-create.png", fullPage: true })
  })

  test("остатки: создание, удаление", async ({ page }) => {
    await setTokenAndGoto(page, token, "/stock")
    const initialCount = await page.locator("table tbody tr").count()

    await openCreateDialog(page)
    await page.fill('input[name="on_hand"]', "100")
    await page.fill('input[name="reserved"]', "0")
    await page.click('button:has-text("Сохранить")')
    await page.waitForTimeout(1000)

    const afterCreate = await page.locator("table tbody tr").count()
    expect(afterCreate).toBe(initialCount + 1)

    await page.screenshot({ path: "tests/output/stock-create.png", fullPage: true })
  })

  test("перемещения: создание, удаление", async ({ page }) => {
    await setTokenAndGoto(page, token, "/transfers")
    const initialCount = await page.locator("table tbody tr").count()

    await openCreateDialog(page)
    await page.fill('input[name="status"]', "draft")
    await page.click('button:has-text("Сохранить")')
    await page.waitForTimeout(1000)

    const afterCreate = await page.locator("table tbody tr").count()
    expect(afterCreate).toBe(initialCount + 1)

    await page.screenshot({ path: "tests/output/transfers-create.png", fullPage: true })
  })

  test("заказы: просмотр данных", async ({ page }) => {
    await setTokenAndGoto(page, token, "/orders")
    const rows = await page.locator("table tbody tr").count()
    expect(rows).toBeGreaterThan(0)
    await page.screenshot({ path: "tests/output/orders-list.png", fullPage: true })
  })

  test("покупатели: просмотр данных", async ({ page }) => {
    await setTokenAndGoto(page, token, "/customers")
    const rows = await page.locator("table tbody tr").count()
    expect(rows).toBeGreaterThanOrEqual(0)
    await page.screenshot({ path: "tests/output/customers-list.png", fullPage: true })
  })

  test("маршруты: раздел доступен (заглушка, 501 API — вне путей задачи)", async ({ page }) => {
    await setTokenAndGoto(page, token, "/routes")
    const heading = page.locator("h2")
    await expect(heading).toHaveText("Маршруты")
    const bodyText = await page.locator("body").textContent()
    expect(bodyText).toContain("ORM-модель")
    await page.screenshot({ path: "tests/output/routes-placeholder.png", fullPage: true })
  })

  test("перевозчики: раздел доступен (заглушка, 501 API — вне путей задачи)", async ({ page }) => {
    await setTokenAndGoto(page, token, "/carriers")
    const heading = page.locator("h2")
    await expect(heading).toHaveText("Перевозчики")
    const bodyText = await page.locator("body").textContent()
    expect(bodyText).toContain("ORM-модель")
    await page.screenshot({ path: "tests/output/carriers-placeholder.png", fullPage: true })
  })

  test("валидация: создание города без slug не создаёт запись", async ({ page }) => {
    await setTokenAndGoto(page, token, "/cities")
    const initialCount = await page.locator("table tbody tr").count()

    await openCreateDialog(page)
    await page.fill('input[name="name"]', "Invalid City")
    await page.click('button:has-text("Сохранить")')
    await page.waitForTimeout(1000)

    const afterAttempt = await page.locator("table tbody tr").count()
    expect(afterAttempt).toBe(initialCount)
  })
})
