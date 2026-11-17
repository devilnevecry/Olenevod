# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: login-test.spec.ts >> UI login flow
- Location: tests\login-test.spec.ts:6:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.screenshot: Target page, context or browser has been closed
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
        - heading "Города" [level=2] [ref=e23]
        - button "Добавить" [ref=e24]
      - table [ref=e26]:
        - rowgroup [ref=e27]:
          - row [ref=e28]:
            - columnheader "ID" [ref=e29]
            - columnheader "Slug" [ref=e30]
            - columnheader "Название" [ref=e31]
            - columnheader "Регион" [ref=e32]
            - columnheader "Часовой пояс" [ref=e33]
            - columnheader "Активен" [ref=e34]
            - columnheader "Действия" [ref=e35]
        - rowgroup [ref=e36]:
          - row [ref=e37]:
            - cell "01399bf6-298f-4487-943f-ac5eb434dbbb" [ref=e38]
            - cell "test-city-e2e" [ref=e39]
            - cell "Test City E2E" [ref=e40]
            - cell "Test Region" [ref=e41]
            - cell "UTC" [ref=e42]
            - cell "Да" [ref=e43]
            - cell [ref=e44]:
              - button "Редактировать" [ref=e45]
              - button "Удалить" [ref=e46]
          - row [ref=e47]:
            - cell "11111111-1111-1111-1111-111111111001" [ref=e48]
            - cell "moscow" [ref=e49]
            - cell "Москва" [ref=e50]
            - cell "Москва" [ref=e51]
            - cell "Europe/Moscow" [ref=e52]
            - cell "Да" [ref=e53]
            - cell [ref=e54]:
              - button "Редактировать" [ref=e55]
              - button "Удалить" [ref=e56]
          - row [ref=e57]:
            - cell "11111111-1111-1111-1111-111111111004" [ref=e58]
            - cell "pay-moscow" [ref=e59]
            - cell "Москва платежи" [ref=e60]
            - cell "Москва" [ref=e61]
            - cell "Europe/Moscow" [ref=e62]
            - cell "Да" [ref=e63]
            - cell [ref=e64]:
              - button "Редактировать" [ref=e65]
              - button "Удалить" [ref=e66]
          - row [ref=e67]:
            - cell "11111111-1111-1111-1111-111111111005" [ref=e68]
            - cell "notify-moscow" [ref=e69]
            - cell "Москва уведомления" [ref=e70]
            - cell "Москва" [ref=e71]
            - cell "Europe/Moscow" [ref=e72]
            - cell "Да" [ref=e73]
            - cell [ref=e74]:
              - button "Редактировать" [ref=e75]
              - button "Удалить" [ref=e76]
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test"
  2  | 
  3  | const ADMIN_EMAIL = "ivan@example.com"
  4  | const ADMIN_PASSWORD = "DemoPass123"
  5  | 
  6  | test("UI login flow", async ({ page }) => {
  7  |   const errors: string[] = []
  8  |   page.on("pageerror", (err) => errors.push(err.message))
  9  |   page.on("console", (msg) => {
  10 |     if (msg.type() === "error") errors.push(`CONSOLE: ${msg.text()}`)
  11 |   })
  12 | 
  13 |   await page.goto("/login")
  14 |   await page.waitForTimeout(500)
  15 |   await page.fill('input[type="email"]', ADMIN_EMAIL)
  16 |   await page.fill('input[type="password"]', ADMIN_PASSWORD)
  17 |   await page.click('button[type="submit"]')
  18 |   await page.waitForTimeout(3000)
  19 | 
  20 |   const url = page.url()
  21 |   console.log("URL after login: " + url)
  22 | 
  23 |   // Проверяем сообщение об ошибке на форме
  24 |   const errorText = await page.locator(".text-danger, [style*='color: #b91c1c'], .error").textContent().catch(() => "no error element")
  25 |   console.log("Error text: " + errorText)
  26 | 
  27 |   console.log("Errors: " + JSON.stringify(errors))
  28 | 
> 29 |   await page.screenshot({ path: "tests/output/login-after.png", fullPage: true })
     |              ^ Error: page.screenshot: Target page, context or browser has been closed
  30 | })
  31 | 
```