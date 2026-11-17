# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin-crud.spec.ts >> BUG-05: Admin CRUD — 11 разделов >> предложения: создание, удаление
- Location: tests\admin-crud.spec.ts:170:3

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
        - heading "Предложения города" [level=2] [ref=e23]
        - button "Добавить" [ref=e24]
      - generic [ref=e25]: "Error: 422 {\"detail\":[{\"type\":\"uuid_parsing\",\"loc\":[\"body\",\"city_id\"],\"msg\":\"Input should be a valid UUID, invalid length: found 0\",\"input\":\"\",\"ctx\":{\"error\":\"invalid length: found 0\"}},{\"type\":\"uuid_parsing\",\"loc\":[\"body\",\"variant_id\"],\"msg\":\"Input should be a valid UUID, invalid length: found 0\",\"input\":\"\",\"ctx\":{\"error\":\"invalid length: found 0\"}}]}"
      - table [ref=e27]:
        - rowgroup [ref=e28]:
          - row [ref=e29]:
            - columnheader "ID" [ref=e30]
            - columnheader "Город (ID)" [ref=e31]
            - columnheader "Вариант (ID)" [ref=e32]
            - columnheader "Цена (коп)" [ref=e33]
            - columnheader "Опубликован" [ref=e34]
            - columnheader "Мин. qty" [ref=e35]
            - columnheader "Шаг qty" [ref=e36]
            - columnheader "Действия" [ref=e37]
        - rowgroup [ref=e38]:
          - row [ref=e39]:
            - cell "66666666-6666-6666-6666-666666666003" [ref=e40]
            - cell "11111111-1111-1111-1111-111111111001" [ref=e41]
            - cell "44444444-4444-4444-4444-444444444002" [ref=e42]
            - cell "9500" [ref=e43]
            - cell "Да" [ref=e44]
            - cell "1" [ref=e45]
            - cell "1" [ref=e46]
            - cell [ref=e47]:
              - button "Редактировать" [ref=e48]
              - button "Удалить" [ref=e49]
          - row [ref=e50]:
            - cell "66666666-6666-6666-6666-666666666004" [ref=e51]
            - cell "11111111-1111-1111-1111-111111111004" [ref=e52]
            - cell "44444444-4444-4444-4444-444444444003" [ref=e53]
            - cell "9500" [ref=e54]
            - cell "Да" [ref=e55]
            - cell "1" [ref=e56]
            - cell "1" [ref=e57]
            - cell [ref=e58]:
              - button "Редактировать" [ref=e59]
              - button "Удалить" [ref=e60]
          - row [ref=e61]:
            - cell "66666666-6666-6666-6666-666666666005" [ref=e62]
            - cell "11111111-1111-1111-1111-111111111005" [ref=e63]
            - cell "44444444-4444-4444-4444-444444444004" [ref=e64]
            - cell "9500" [ref=e65]
            - cell "Да" [ref=e66]
            - cell "1" [ref=e67]
            - cell "1" [ref=e68]
            - cell [ref=e69]:
              - button "Редактировать" [ref=e70]
              - button "Удалить" [ref=e71]
      - generic [ref=e73]:
        - heading "Создать" [level=2] [ref=e74]
        - generic [ref=e75]:
          - generic [ref=e76]:
            - generic [ref=e77]: Город (ID)
            - textbox [ref=e78]
          - generic [ref=e79]:
            - generic [ref=e80]: Вариант (ID)
            - textbox [ref=e81]
          - generic [ref=e82]:
            - generic [ref=e83]: Цена (коп)
            - spinbutton [ref=e84]: "10000"
          - generic [ref=e85]:
            - generic [ref=e86]: Старая цена (коп)
            - spinbutton [ref=e87]
          - combobox [ref=e88]:
            - option "Да" [selected]
            - option "Нет"
          - generic [ref=e89]:
            - generic [ref=e90]: Мин. qty
            - spinbutton [ref=e91]: "1"
          - generic [ref=e92]:
            - generic [ref=e93]: Шаг qty
            - spinbutton [ref=e94]: "1"
          - generic [ref=e95]:
            - generic [ref=e96]: Макс. qty в заказе
            - spinbutton [ref=e97]
          - button "Сохранить" [active] [ref=e98] [cursor=pointer]
```

# Test source

```ts
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
> 181 |     expect(afterCreate).toBe(initialCount + 1)
      |                         ^ Error: expect(received).toBe(expected) // Object.is equality
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
  212 |     expect(afterCreate).toBe(initialCount + 1)
  213 | 
  214 |     await page.screenshot({ path: "tests/output/transfers-create.png", fullPage: true })
  215 |   })
  216 | 
  217 |   test("заказы: просмотр данных", async ({ page }) => {
  218 |     await setTokenAndGoto(page, token, "/orders")
  219 |     const rows = await page.locator("table tbody tr").count()
  220 |     expect(rows).toBeGreaterThan(0)
  221 |     await page.screenshot({ path: "tests/output/orders-list.png", fullPage: true })
  222 |   })
  223 | 
  224 |   test("покупатели: просмотр данных", async ({ page }) => {
  225 |     await setTokenAndGoto(page, token, "/customers")
  226 |     const rows = await page.locator("table tbody tr").count()
  227 |     expect(rows).toBeGreaterThanOrEqual(0)
  228 |     await page.screenshot({ path: "tests/output/customers-list.png", fullPage: true })
  229 |   })
  230 | 
  231 |   test("маршруты: раздел доступен (заглушка, 501 API — вне путей задачи)", async ({ page }) => {
  232 |     await setTokenAndGoto(page, token, "/routes")
  233 |     const heading = page.locator("h2")
  234 |     await expect(heading).toHaveText("Маршруты")
  235 |     const bodyText = await page.locator("body").textContent()
  236 |     expect(bodyText).toContain("ORM-модель")
  237 |     await page.screenshot({ path: "tests/output/routes-placeholder.png", fullPage: true })
  238 |   })
  239 | 
  240 |   test("перевозчики: раздел доступен (заглушка, 501 API — вне путей задачи)", async ({ page }) => {
  241 |     await setTokenAndGoto(page, token, "/carriers")
  242 |     const heading = page.locator("h2")
  243 |     await expect(heading).toHaveText("Перевозчики")
  244 |     const bodyText = await page.locator("body").textContent()
  245 |     expect(bodyText).toContain("ORM-модель")
  246 |     await page.screenshot({ path: "tests/output/carriers-placeholder.png", fullPage: true })
  247 |   })
  248 | 
  249 |   test("валидация: создание города без slug не создаёт запись", async ({ page }) => {
  250 |     await setTokenAndGoto(page, token, "/cities")
  251 |     const initialCount = await page.locator("table tbody tr").count()
  252 | 
  253 |     await openCreateDialog(page)
  254 |     await page.fill('input[name="name"]', "Invalid City")
  255 |     await page.click('button:has-text("Сохранить")')
  256 |     await page.waitForTimeout(1000)
  257 | 
  258 |     const afterAttempt = await page.locator("table tbody tr").count()
  259 |     expect(afterAttempt).toBe(initialCount)
  260 |   })
  261 | })
  262 | 
```