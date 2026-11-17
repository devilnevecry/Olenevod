# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin-crud.spec.ts >> BUG-05: Admin CRUD — 11 разделов >> склады: создание, редактирование, связь с городом
- Location: tests\admin-crud.spec.ts:100:3

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: 4
Received: 3
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
      - generic [ref=e22]:
        - heading "Склады" [level=2] [ref=e23]
        - button "Добавить" [ref=e24]
      - generic [ref=e25]: "Error: 422 {\"detail\":[{\"type\":\"uuid_parsing\",\"loc\":[\"body\",\"city_id\"],\"msg\":\"Input should be a valid UUID, invalid length: found 0\",\"input\":\"\",\"ctx\":{\"error\":\"invalid length: found 0\"}}]}"
      - table [ref=e27]:
        - rowgroup [ref=e28]:
          - row [ref=e29]:
            - columnheader "ID" [ref=e30]
            - columnheader "Город (ID)" [ref=e31]
            - columnheader "Название" [ref=e32]
            - columnheader "Адрес" [ref=e33]
            - columnheader "Активен" [ref=e34]
            - columnheader "Действия" [ref=e35]
        - rowgroup [ref=e36]:
          - row [ref=e37]:
            - cell "55555555-5555-5555-5555-555555555003" [ref=e38]
            - cell "11111111-1111-1111-1111-111111111001" [ref=e39]
            - cell "Склад заказы" [ref=e40]
            - cell "-" [ref=e41]
            - cell "Да" [ref=e42]
            - cell [ref=e43]:
              - button "Редактировать" [ref=e44]
              - button "Удалить" [ref=e45]
          - row [ref=e46]:
            - cell "55555555-5555-5555-5555-555555555004" [ref=e47]
            - cell "11111111-1111-1111-1111-111111111004" [ref=e48]
            - cell "Склад оплаты" [ref=e49]
            - cell "-" [ref=e50]
            - cell "Да" [ref=e51]
            - cell [ref=e52]:
              - button "Редактировать" [ref=e53]
              - button "Удалить" [ref=e54]
          - row [ref=e55]:
            - cell "55555555-5555-5555-5555-555555555006" [ref=e56]
            - cell "11111111-1111-1111-1111-111111111005" [ref=e57]
            - cell "Склад уведомлений" [ref=e58]
            - cell "-" [ref=e59]
            - cell "Да" [ref=e60]
            - cell [ref=e61]:
              - button "Редактировать" [ref=e62]
              - button "Удалить" [ref=e63]
      - generic [ref=e65]:
        - heading "Создать" [level=2] [ref=e66]
        - generic [ref=e67]:
          - generic [ref=e68]:
            - generic [ref=e69]: Город (ID)
            - textbox [ref=e70]
          - generic [ref=e71]:
            - generic [ref=e72]: Название
            - textbox [ref=e73]: Test Warehouse E2E
          - generic [ref=e74]:
            - generic [ref=e75]: Адрес
            - textbox [ref=e76]: Test Address 123
          - combobox [ref=e77]:
            - option "Да" [selected]
            - option "Нет"
          - button "Сохранить" [active] [ref=e78] [cursor=pointer]
```

# Test source

```ts
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
  43  |   await page.click('button:has-text("Добавить")')
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
> 111 |     expect(afterCreate).toBe(initialCount + 1)
      |                         ^ Error: expect(received).toBe(expected) // Object.is equality
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
  144 |     await page.click('button:has-text("Сохранить")')
  145 |     await page.waitForTimeout(2000)
  146 | 
  147 |     const afterCreate = await page.locator("table tbody tr").count()
  148 |     expect(afterCreate).toBe(initialCount + 1)
  149 | 
  150 |     await page.screenshot({ path: "tests/output/products-create.png", fullPage: true })
  151 |   })
  152 | 
  153 |   test("варианты: создание, удаление", async ({ page }) => {
  154 |     await setTokenAndGoto(page, token, "/variants")
  155 |     const initialCount = await page.locator("table tbody tr").count()
  156 | 
  157 |     await openCreateDialog(page)
  158 |     await page.fill('input[name="sku"]', "TEST-SKU-E2E")
  159 |     await page.fill('input[name="name"]', "Test Variant E2E")
  160 |     await page.selectOption('select[name="unit_type"]', "piece")
  161 |     await page.click('button:has-text("Сохранить")')
  162 |     await page.waitForTimeout(2000)
  163 | 
  164 |     const afterCreate = await page.locator("table tbody tr").count()
  165 |     expect(afterCreate).toBe(initialCount + 1)
  166 | 
  167 |     await page.screenshot({ path: "tests/output/variants-create.png", fullPage: true })
  168 |   })
  169 | 
  170 |   test("предложения: создание, удаление", async ({ page }) => {
  171 |     await setTokenAndGoto(page, token, "/offers")
  172 |     const initialCount = await page.locator("table tbody tr").count()
  173 | 
  174 |     await openCreateDialog(page)
  175 |     await page.fill('input[name="price_kop"]', "10000")
  176 |     await page.selectOption('select[name="is_published"]', "true")
  177 |     await page.click('button:has-text("Сохранить")')
  178 |     await page.waitForTimeout(2000)
  179 | 
  180 |     const afterCreate = await page.locator("table tbody tr").count()
  181 |     expect(afterCreate).toBe(initialCount + 1)
  182 | 
  183 |     await page.screenshot({ path: "tests/output/offers-create.png", fullPage: true })
  184 |   })
  185 | 
  186 |   test("остатки: создание, удаление", async ({ page }) => {
  187 |     await setTokenAndGoto(page, token, "/stock")
  188 |     const initialCount = await page.locator("table tbody tr").count()
  189 | 
  190 |     await openCreateDialog(page)
  191 |     await page.fill('input[name="on_hand"]', "100")
  192 |     await page.fill('input[name="reserved"]', "0")
  193 |     await page.click('button:has-text("Сохранить")')
  194 |     await page.waitForTimeout(1000)
  195 | 
  196 |     const afterCreate = await page.locator("table tbody tr").count()
  197 |     expect(afterCreate).toBe(initialCount + 1)
  198 | 
  199 |     await page.screenshot({ path: "tests/output/stock-create.png", fullPage: true })
  200 |   })
  201 | 
  202 |   test("перемещения: создание, удаление", async ({ page }) => {
  203 |     await setTokenAndGoto(page, token, "/transfers")
  204 |     const initialCount = await page.locator("table tbody tr").count()
  205 | 
  206 |     await openCreateDialog(page)
  207 |     await page.fill('input[name="status"]', "draft")
  208 |     await page.click('button:has-text("Сохранить")')
  209 |     await page.waitForTimeout(1000)
  210 | 
  211 |     const afterCreate = await page.locator("table tbody tr").count()
```