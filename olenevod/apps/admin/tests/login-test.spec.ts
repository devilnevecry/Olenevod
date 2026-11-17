import { test, expect } from "@playwright/test"

const ADMIN_EMAIL = "ivan@example.com"
const ADMIN_PASSWORD = "DemoPass123"

test("UI login flow", async ({ page }) => {
  const errors: string[] = []
  page.on("pageerror", (err) => errors.push(err.message))
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(`CONSOLE: ${msg.text()}`)
  })

  await page.goto("/login")
  await page.waitForTimeout(500)
  await page.fill('input[type="email"]', ADMIN_EMAIL)
  await page.fill('input[type="password"]', ADMIN_PASSWORD)
  await page.click('button[type="submit"]')
  await page.waitForTimeout(3000)

  const url = page.url()
  console.log("URL after login: " + url)

  // Проверяем сообщение об ошибке на форме
  const errorText = await page.locator(".text-danger, [style*='color: #b91c1c'], .error").textContent().catch(() => "no error element")
  console.log("Error text: " + errorText)

  console.log("Errors: " + JSON.stringify(errors))

  await page.screenshot({ path: "tests/output/login-after.png", fullPage: true })
})
