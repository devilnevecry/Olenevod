# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin-crud.spec.ts >> BUG-05: Admin CRUD — 11 разделов >> остатки: создание, удаление
- Location: tests\admin-crud.spec.ts:186:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('button:has-text("Добавить")')

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - complementary [ref=e4]:
    - generic [ref=e5]: Olenevod Admin
    - navigation [ref=e6]:
      - link "Города" [ref=e7] [cursor=pointer]:
        - /url: /cities
      - link "Склады" [ref=e8] [cursor=pointer]:
        - /url: /warehouses
      - link "Товары" [ref=e9] [cursor=pointer]:
        - /url: /products
      - link "Варианты" [ref=e10] [cursor=pointer]:
        - /url: /variants
      - link "Предложения" [ref=e11] [cursor=pointer]:
        - /url: /offers
      - link "Остатки" [ref=e12] [cursor=pointer]:
        - /url: /stock
      - link "Перемещения" [ref=e13] [cursor=pointer]:
        - /url: /transfers
      - link "Маршруты" [ref=e14] [cursor=pointer]:
        - /url: /routes
      - link "Перевозчики" [ref=e15] [cursor=pointer]:
        - /url: /carriers
      - link "Заказы" [ref=e16] [cursor=pointer]:
        - /url: /orders
      - link "Покупатели" [ref=e17] [cursor=pointer]:
        - /url: /customers
      - separator [ref=e18]
      - button "Выйти" [ref=e19]
  - main [ref=e20]:
    - generic [ref=e21]:
      - heading "Остатки товара на складах" [level=2] [ref=e22]
      - table [ref=e24]:
        - rowgroup [ref=e25]:
          - row [ref=e26]:
            - columnheader "Склад (ID)" [ref=e27]
            - columnheader "Вариант (ID)" [ref=e28]
            - columnheader "on_hand" [ref=e29]
            - columnheader "reserved" [ref=e30]
            - columnheader "доступно" [ref=e31]
            - columnheader "Сохранить" [ref=e32]
        - rowgroup [ref=e33]:
          - row [ref=e34]:
            - cell "55555555-5555-5555-5555-555555555003" [ref=e35]
            - cell "44444444-4444-4444-4444-444444444002" [ref=e36]
            - cell [ref=e37]:
              - textbox [ref=e38]: "10"
            - cell [ref=e39]:
              - textbox [ref=e40]: "2"
            - cell "8" [ref=e41]
            - cell [ref=e43]:
              - button "Сохранить" [ref=e44]
          - row [ref=e45]:
            - cell "55555555-5555-5555-5555-555555555004" [ref=e46]
            - cell "44444444-4444-4444-4444-444444444003" [ref=e47]
            - cell [ref=e48]:
              - textbox [ref=e49]: "100"
            - cell [ref=e50]:
              - textbox [ref=e51]: "0"
            - cell "100" [ref=e52]
            - cell [ref=e54]:
              - button "Сохранить" [ref=e55]
          - row [ref=e56]:
            - cell "55555555-5555-5555-5555-555555555006" [ref=e57]
            - cell "44444444-4444-4444-4444-444444444004" [ref=e58]
            - cell [ref=e59]:
              - textbox [ref=e60]: "100"
            - cell [ref=e61]:
              - textbox [ref=e62]: "0"
            - cell "100" [ref=e63]
            - cell [ref=e65]:
              - button "Сохранить" [ref=e66]
```

# Test source

```ts
  1   | import { test, expect, APIRequestContext } from "@playwright/test"
  2   | 
  3   | const API_BASE = "http://localhost:8002"
  4   | const ADMIN_EMAIL = "ivan@example.com"
  5   | const ADMIN_PASSWORD = "DemoPass123"
  6   | 
  7   | const SECTIONS = [
  8   |   { name: "cities", path: "/cities", title: "Города" },
  9   |   { name: "warehouses", path: "/warehouses", title: "Склады" },
  10  |   { name: "products", path: "/products", title: "Товары" },
  11  |   { name: "variants", path: "/variants", title: "Варианты товара" },
  12  |   { name: "offers", path: "/offers", title: "Предложения города" },
  13  |   { name: "stock", path: "/stock", title: "Остатки товара на складах" },
  14  |   { name: "transfers", path: "/transfers", title: "Перемещения" },
  15  |   { name: "routes", path: "/routes", title: "Маршруты" },
  16  |   { name: "carriers", path: "/carriers", title: "Перевозчики" },
  17  |   { name: "orders", path: "/orders", title: "Заказы" },
  18  |   { name: "customers", path: "/customers", title: "Покупатели" },
  19  | ]
  20  | 
  21  | async function getAdminToken(request: APIRequestContext): Promise<string> {
  22  |   const resp = await request.post(`${API_BASE}/auth/login`, {
  23  |     data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
  24  |   })
  25  |   expect(resp.ok()).toBeTruthy()
  26  |   const body = await resp.json()
  27  |   return body.access_token
  28  | }
  29  | 
  30  | async function setTokenAndGoto(page: any, token: string, path: string) {
  31  |   await page.context().addInitScript((t: string) => {
  32  |     localStorage.setItem("admin_token", t)
  33  |   }, token)
  34  |   await page.goto(path)
  35  |   await page.waitForTimeout(2000)
  36  | }
  37  | 
  38  | async function openCreateDialog(page: any) {
  39  |   const h2 = await page.locator("h2").textContent().catch(() => "no h2")
  40  |   console.log(`DEBUG: page h2 = "${h2}"`)
  41  |   const bodyText = await page.locator("body").textContent().catch(() => "no body")
  42  |   console.log(`DEBUG: body starts with = "${bodyText?.substring(0, 200)}"`)
> 43  |   await page.click('button:has-text("Добавить")')
      |              ^ Error: page.click: Test timeout of 30000ms exceeded.
  44  |   await page.waitForSelector('h2:has-text("Создать")', { state: "visible" })
  45  | }
  46  | 
  47  | test.describe("BUG-05: Admin CRUD — 11 разделов", () => {
  48  |   const token =
  49  |     "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2NjY2NjY2Ni02NjY2LTY2NjYtNjY2Ni02NjY2NjY2NjY5NTEiLCJpYXQiOjE3OTQ5MDU5OTcsImV4cCI6MTc5NDk5MjM5N30.vp9qt6tLbh4X_piNLdIiBSPK9HsEet7BygdJtmPU0H8"
  50  | 
  51  |   async function loginAsAdmin(page: any) {
  52  |   await page.goto("/login")
  53  |   await page.fill('input[type="email"]', ADMIN_EMAIL)
  54  |   await page.fill('input[type="password"]', ADMIN_PASSWORD)
  55  |   await page.click('button[type="submit"]')
  56  |   // Ждём ухода со страницы логина (редирект на /cities)
  57  |   await page.waitForURL((url) => !url.pathname.includes("/login"), { timeout: 15000 })
  58  | }
  59  | 
  60  |   test("города: создание, редактирование, удаление, обновление после перезагрузки", async ({ page }) => {
  61  |     await setTokenAndGoto(page, token, "/cities")
  62  |     const initialCount = await page.locator("table tbody tr").count()
  63  | 
  64  |     await openCreateDialog(page)
  65  |     await page.fill('input[name="slug"]', "test-city-e2e")
  66  |     await page.fill('input[name="name"]', "Test City E2E")
  67  |     await page.fill('input[name="region"]', "Test Region")
  68  |     await page.fill('input[name="timezone"]', "UTC")
  69  |     await page.click('button:has-text("Сохранить")')
  70  |     await page.waitForTimeout(2000)
  71  | 
  72  |     const afterCreate = await page.locator("table tbody tr").count()
  73  |     expect(afterCreate).toBe(initialCount + 1)
  74  | 
  75  |     // Перезагрузка — данные сохраняются
  76  |     await page.reload()
  77  |     await page.waitForTimeout(1000)
  78  |     const afterReload = await page.locator("table tbody tr").count()
  79  |     expect(afterReload).toBe(afterCreate)
  80  | 
  81  |     await page.screenshot({ path: "tests/output/cities-after-reload.png", fullPage: true })
  82  | 
  83  |     // Удаление
  84  |     const rows = page.locator("table tbody tr")
  85  |     let deleted = false
  86  |     for (let i = 0; i < (await rows.count()); i++) {
  87  |       const row = rows.nth(i)
  88  |       const text = await row.textContent()
  89  |       if (text && text.includes("test-city-e2e")) {
  90  |         await row.locator('button:has-text("Удалить")').first().click()
  91  |         await page.click('button:has-text("Удалить")')
  92  |         await page.waitForTimeout(1000)
  93  |         deleted = true
  94  |         break
  95  |       }
  96  |     }
  97  |     expect(deleted).toBe(true)
  98  |   })
  99  | 
  100 |   test("склады: создание, редактирование, связь с городом", async ({ page }) => {
  101 |     await setTokenAndGoto(page, token, "/warehouses")
  102 |     const initialCount = await page.locator("table tbody tr").count()
  103 | 
  104 |     await openCreateDialog(page)
  105 |     await page.fill('input[name="name"]', "Test Warehouse E2E")
  106 |     await page.fill('input[name="address"]', "Test Address 123")
  107 |     await page.click('button:has-text("Сохранить")')
  108 |     await page.waitForTimeout(2000)
  109 | 
  110 |     const afterCreate = await page.locator("table tbody tr").count()
  111 |     expect(afterCreate).toBe(initialCount + 1)
  112 | 
  113 |     // Редактирование
  114 |     const rows = page.locator("table tbody tr")
  115 |     for (let i = 0; i < (await rows.count()); i++) {
  116 |       const row = rows.nth(i)
  117 |       const text = await row.textContent()
  118 |       if (text && text.includes("Test Warehouse E2E")) {
  119 |         await row.locator('button:has-text("Редактировать")').first().click()
  120 |         await page.waitForSelector('[role="dialog"]', { state: "visible" })
  121 |         await page.fill('input[name="name"]', "Test Warehouse E2E Updated")
  122 |         await page.click('button:has-text("Сохранить")')
  123 |         await page.waitForTimeout(1000)
  124 |         break
  125 |       }
  126 |     }
  127 | 
  128 |     await page.reload()
  129 |     await page.waitForTimeout(1000)
  130 |     const updatedText = await page.locator("table tbody tr").first().textContent()
  131 |     expect(updatedText).toContain("Test Warehouse E2E Updated")
  132 | 
  133 |     await page.screenshot({ path: "tests/output/warehouses-edit.png", fullPage: true })
  134 |   })
  135 | 
  136 |   test("товары: создание, удаление", async ({ page }) => {
  137 |     await setTokenAndGoto(page, token, "/products")
  138 |     const initialCount = await page.locator("table tbody tr").count()
  139 | 
  140 |     await openCreateDialog(page)
  141 |     await page.fill('input[name="slug"]', "test-product-e2e")
  142 |     await page.fill('input[name="name"]', "Test Product E2E")
  143 |     await page.fill('input[name="short_description"]', "Test description")
```