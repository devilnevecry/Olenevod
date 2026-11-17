// Verification script for BUG-17: admin responsiveness on 5 viewports.
// Standalone Playwright script; NOT a repo test file (no new tests added to tests/).
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const VIEWPORTS = [
  { name: "vp-360x760", width: 360, height: 760 },
  { name: "vp-390x844", width: 390, height: 844 },
  { name: "vp-768x1024", width: 768, height: 1024 },
  { name: "vp-1280x800", width: 1280, height: 800 },
  { name: "vp-1440x900", width: 1440, height: 900 },
];

const SECTIONS = [
  "/cities", "/warehouses", "/products", "/variants", "/offers",
  "/stock", "/transfers", "/routes", "/carriers", "/orders", "/customers",
];

const OUT = path.join(__dirname, "verify-bug17-out");
fs.mkdirSync(OUT, { recursive: true });

(async () => {
const results = [];
const browser = await chromium.launch({ headless: true });

for (const vp of VIEWPORTS) {
  const dir = path.join(OUT, vp.name);
  fs.mkdirSync(dir, { recursive: true });
  const logs = [];
  const errors = [];
  const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  const page = await context.newPage();
  page.on("console", (m) => logs.push(`[${m.type()}] ${m.text()}`));
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("requestfailed", (r) => logs.push(`[req-fail] ${r.url()} ${r.failure() ? r.failure().errorText : ""}`));

  const entry = { viewport: vp };

  try {
    // Токен ставим прямо в localStorage (обход ProtectedRoute — мок API не ставим,
    // достаточно наличия токена для рендеринга разделов; данные грузятся с реального API).
    await page.goto("http://localhost:5173/login", { waitUntil: "domcontentloaded" });
    await page.evaluate(() => localStorage.setItem("admin_token", "demo-verification"));
    await page.goto("http://localhost:5173/cities", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1500);
    await page.waitForURL("**/cities");

    entry.loadedUrl = page.url();

    // 1. Отсутствие горизонтального скролла (до открытия диалога)
    const scroll = await page.evaluate(() => ({
      documentScrollWidth: document.documentElement.scrollWidth,
      bodyScrollWidth: document.body.scrollWidth,
      windowInnerWidth: window.innerWidth,
    }));
    entry.hScrollBefore = scroll.documentScrollWidth > scroll.windowInnerWidth;
    entry.scroll = scroll;

    // 2. Загрузка шрифтов
    entry.fonts = await page.evaluate(() => document.fonts.status);

    // 3. Тач-цели >= 44x44
    const touch = await page.evaluate(() => {
      const els = Array.from(document.querySelectorAll("button, a[href], input, select"));
      const bad = [];
      for (const el of els) {
        const r = el.getBoundingClientRect();
        if (r.width < 44 || r.height < 44) {
          bad.push({
            tag: el.tagName,
            text: (el.innerText || el.value || "").trim().slice(0, 40),
            w: Math.round(r.width),
            h: Math.round(r.height),
          });
        }
      }
      return { total: els.length, badCount: bad.length, bad: bad.slice(0, 25) };
    });
    entry.touch = touch;

    // 4. Геометрия сайдбара/контента (перекрытия, адаптивность)
    const geom = await page.evaluate(() => {
      const sidebar = document.querySelector("aside");
      const main = document.querySelector("main");
      const s = sidebar ? sidebar.getBoundingClientRect() : null;
      const m = main ? main.getBoundingClientRect() : null;
      return {
        vw: window.innerWidth,
        sidebarW: s ? Math.round(s.width) : null,
        sidebarRight: s ? Math.round(s.right) : null,
        mainLeft: m ? Math.round(m.left) : null,
        mainW: m ? Math.round(m.width) : null,
        mainRight: m ? Math.round(m.right) : null,
      };
    });
    entry.geom = geom;

    // 5. Навигация между разделами
    const nav = [];
    for (const s of SECTIONS) {
      try {
        const loc = page.locator(`a[href="${s}"]`).first();
        if ((await loc.count()) > 0) {
          await loc.click();
          await page.waitForTimeout(400);
          nav.push({ to: s, url: page.url(), ok: page.url().includes(s) });
        } else {
          nav.push({ to: s, ok: false, reason: "link not found" });
        }
      } catch (e) {
        nav.push({ to: s, ok: false, reason: String(e) });
      }
    }
    entry.nav = nav;

    // Вернуться на города, открыть диалог "Добавить" (проверка перекрытий на узких экранах)
    await page.goto("http://localhost:5173/cities", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(800);
    const addBtn = page.locator("button:has-text('Добавить')").first();
    if ((await addBtn.count()) > 0) {
      await addBtn.click();
      await page.waitForTimeout(600);
      const scrollAfter = await page.evaluate(() => ({
        documentScrollWidth: document.documentElement.scrollWidth,
        windowInnerWidth: window.innerWidth,
      }));
      entry.hScrollAfterDialog = scrollAfter.documentScrollWidth > scrollAfter.windowInnerWidth;
      entry.dialog = await page.evaluate(() => {
        const panel = document.querySelector("div[style*='maxWidth: 700']");
        if (!panel) return null;
        const r = panel.getBoundingClientRect();
        return { panelW: Math.round(r.width), panelH: Math.round(r.height), panelLeft: Math.round(r.left), panelRight: Math.round(r.right) };
      });
      const overlay = page.locator('[style*="z-index: 50"]').first();
      if ((await overlay.count()) > 0) await overlay.click({ position: { x: 10, y: 10 } });
      await page.waitForTimeout(300);
    }

    entry.errors = errors;
  } catch (e) {
    entry.fatal = String(e);
    entry.errors = errors;
  }

  await page.screenshot({ path: path.join(dir, "full.png"), fullPage: true });
  await context.tracing.stop({ path: path.join(dir, "trace.zip") });
  fs.writeFileSync(path.join(dir, "console.log"), logs.join("\n"));
  fs.writeFileSync(path.join(dir, "errors.log"), errors.join("\n"));
  fs.writeFileSync(path.join(dir, "result.json"), JSON.stringify(entry, null, 2));
  results.push(entry);
  await context.close();
}

await browser.close();
fs.writeFileSync(path.join(OUT, "summary.json"), JSON.stringify(results, null, 2));
console.log("=== BUG-17 VERIFICATION SUMMARY ===");
console.log(JSON.stringify(results, null, 2));
})();
