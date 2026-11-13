import { test, expect } from "@playwright/test"

// E2E сценарии этапа 12 (шаги 1–4 S1) на реальных seed-данных.
// Требуют запущенного API (порт 8000, БД olenevod_test с сидом каталога)
// и dev-сервера Next.js (порт 3000).
//
// Сид (seed_catalog.sql): город Москва, категории Продукты / Молоко и молочные
// продукты / Тест заказов, товары "Молоко классическое" (moloko-klassicheskoe)
// и "Продукт для заказа" (zakaz-produkt) с наличием в Москве.

const MOSCOW_ID = "11111111-1111-1111-1111-111111111001"
const PRODUCT_SLUG = "moloko-klassicheskoe"

test.describe("Витрина этапа 12", () => {
  test("страница главной загружается и показывает города", async ({ page }) => {
    await page.goto("/")
    await expect(page.locator("h1")).toContainText("ОЛЕНЕВОД")
    await expect(page.getByRole("tab", { name: "Москва", exact: true })).toBeVisible()
    await expect(page.getByText("Категории")).toBeVisible()
  })

  test("каталог показывает товары города", async ({ page }) => {
    await page.goto(`/catalog?city_id=${MOSCOW_ID}`)
    await expect(page.getByText("Каталог")).toBeVisible()
    await expect(page.getByText("Молоко классическое", { exact: false })).toBeVisible()
  })

  test("товары фильтруются по категории", async ({ page }) => {
    await page.goto(`/catalog?city_id=${MOSCOW_ID}`)
    // без фильтра оба товара с наличием в Москве видны
    await expect(page.getByText("Молоко классическое", { exact: false })).toBeVisible()
    await expect(page.getByText("Продукт для заказа", { exact: false })).toBeVisible()
    // фильтр по категории "Тест заказов" оставляет только "Продукт для заказа"
    await page.getByRole("button", { name: "Тест заказов", exact: false }).click()
    await expect(page.getByText("Продукт для заказа", { exact: false })).toBeVisible()
    await expect(page.getByText("Молоко классическое", { exact: false })).not.toBeVisible()
  })

  test("карточка товара показывает наличие по городу", async ({ page }) => {
    await page.goto(`/products/${PRODUCT_SLUG}?city_id=${MOSCOW_ID}`)
    await expect(page.getByText("Молоко классическое", { exact: false })).toBeVisible()
    await expect(page.getByText(/В наличии \(\d+\)/)).toBeVisible()
  })
})
