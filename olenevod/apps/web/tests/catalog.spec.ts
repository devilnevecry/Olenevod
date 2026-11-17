import { test, expect } from "@playwright/test"
import { seedCatalog } from "./seed"

// E2E сценарии этапа 12 (шаги 1–4 S1) на реальных seed-данных.
// Требуют запущенного API (порт 8000, БД olenevod_test с сидом каталога)
// и dev-сервера Next.js (порт 3000).
//
// beforeAll сидит города, категории, товары и остатки через прямой SQL
// в olenevod_test (та же схема, что seed_catalog.sql / seed_orders.sql).

const MOSCOW_ID = "11111111-1111-1111-1111-111111111001"
const PRODUCT_SLUG = "moloko-klassicheskoe"

test.beforeAll(async () => {
  await seedCatalog()
})

test.describe("Витрина этапа 12", () => {
  test("страница главной загружается и показывает города", async ({ page }) => {
    await page.goto("/")
    await expect(page.locator("h1")).toContainText("ОЛЕНЕВОД")
    // На главной рендерятся два 도시-списка (в Header и в CitySelector),
    // поэтому берём первую вкладку "Москва".
    await expect(page.getByRole("tab", { name: "Москва", exact: true }).first()).toBeVisible()
    await expect(page.getByRole("heading", { name: "Категории" })).toBeVisible()
  })

  test("каталог показывает товары города", async ({ page }) => {
    await page.goto(`/catalog?city_id=${MOSCOW_ID}`)
    await expect(page.getByRole("heading", { name: "Каталог" })).toBeVisible()
    await expect(page.getByRole("heading", { name: "Молоко классическое" })).toBeVisible()
  })

  test("товары фильтруются по категории", async ({ page }) => {
    await page.goto(`/catalog?city_id=${MOSCOW_ID}`)
    // без фильтра оба товара с наличием в Москве видны
    await expect(page.getByRole("heading", { name: "Молоко классическое" })).toBeVisible()
    await expect(page.getByRole("heading", { name: "Продукт для заказа" })).toBeVisible()
    // фильтр по категории "Тест заказов" оставляет только "Продукт для заказа"
    await page.getByRole("button", { name: "Тест заказов", exact: false }).click()
    await expect(page.getByRole("heading", { name: "Продукт для заказа" })).toBeVisible()
    await expect(page.getByRole("heading", { name: "Молоко классическое" })).not.toBeVisible()
  })

  test("карточка товара показывает наличие по городу", async ({ page }) => {
    await page.goto(`/products/${PRODUCT_SLUG}?city_id=${MOSCOW_ID}`)
    await expect(page.getByRole("heading", { name: "Молоко классическое" })).toBeVisible()
    await expect(page.getByText(/В наличии \(\d+\)/).first()).toBeVisible()
  })
})
