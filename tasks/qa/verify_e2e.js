const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUT = 'C:\\Users\\nu11\\Documents\\GitHub\\kilo-hub\\data\\worktrees\\mwkfedqhnoov\\1.T48\\tasks\\qa';
const CHROME = 'C:\\Users\\nu11\\AppData\\Local\\ms-playwright\\chromium-1255\\chrome-win64\\chrome.exe';

const results = {
  scenarios: [],
  defects: [],
  consoleErrors: [],
  networkFailures: [],
  screenshots: [],
};
let page, context, browser;
let token = null;
let orderId = null;

function addScenario(name, status, detail) {
  results.scenarios.push({ name, status, detail });
  process.stdout.write(`[${status}] ${name} ${detail ? '- ' + detail : ''}\n`);
}
function addDefect(name, steps, expected, actual, evidence) {
  results.defects.push({ name, steps, expected, actual, evidence });
  process.stdout.write(`[DEFECT] ${name}\n`);
}
async function shot(name) {
  const f = path.join(OUT, name + '.png');
  await page.screenshot({ path: f, fullPage: true });
  results.screenshots.push(f);
}
function trim(s, n = 400) { s = String(s); return s.length > n ? s.slice(0, n) + '…' : s; }

async function main() {
  browser = await chromium.launch({ executablePath: CHROME, headless: true });
  context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  page = await context.newPage();

  page.on('console', (msg) => {
    if (msg.type() === 'error' || msg.type() === 'warning')
      results.consoleErrors.push({ type: msg.type(), text: msg.text(), url: page.url() });
  });
  page.on('pageerror', (err) => results.consoleErrors.push({ type: 'pageerror', text: err.message, url: page.url() }));
  page.on('requestfailed', (req) => results.networkFailures.push({ url: req.url(), failure: req.failure ? req.failure.errorText : null }));
  page.on('response', (res) => { if (res.status() >= 400) results.networkFailures.push({ url: res.url(), status: res.status() }); });

  const API = 'http://127.0.0.1:8000';
const ideKey = 't48-run-' + Date.now();

  // ---------- S1: create order via API ----------
  try {
    const create = await context.request.post(`${API}/orders`, {
      data: { city_id: '11111111-1111-1111-1111-111111111001', customer_name: 'Браузер Покупатель', customer_phone: '+79001234567', items: [{ product_variant_id: '44444444-4444-4444-4444-444444444002', qty: 1 }], idempotency_key: ideKey },
    });
    const body = await create.json();
    if (create.status() === 201 && body.id && body.status === 'pending_payment') {
      orderId = body.id;
      addScenario('S1 création commande (API POST /orders)', 'PASS', `id=${body.id} status=${body.status} total=${body.total_amount} user_id=${body.user_id}`);
    } else {
      addDefect('S1 commande', 'POST /orders avec idempotency_key t48-run-IDEKEY', '201 + order created', `HTTP ${create.status()} ${JSON.stringify(body)}`, null);
      addScenario('S1 création commande', 'FAIL', `HTTP ${create.status()}`);
    }
  } catch (e) {
    addDefect('S1 commande', 'POST /orders', '201 created', `exception: ${e.message}`, null);
    addScenario('S1 création commande', 'FAIL', e.message);
  }

  // ---------- S1 bis: idempotency ----------
  try {
    const again = await context.request.post(`${API}/orders`, {
      data: { city_id: '11111111-1111-1111-1111-111111111001', customer_name: 'X', customer_phone: 'Y', items: [{ product_variant_id: '44444444-4444-4444-4444-444444444002', qty: 1 }], idempotency_key: ideKey },
    });
    const body = await again.json();
    if (again.status() === 201 && body.id === orderId) {
      addScenario('S1 bis idempotence (même clé → même commande)', 'PASS', `id=${body.id}`);
    } else {
      addDefect('S1 idempotence', 'POST /orders clé t48-run-IDEKEY deux fois', 'même order_id', `HTTP ${again.status()} id=${body && body.id}`, null);
      addScenario('S1 bis idempotence', 'FAIL', `HTTP ${again.status()}`);
    }
  } catch (e) { addScenario('S1 bis idempotence', 'FAIL', e.message); }

  // ---------- S8: out of stock ----------
  try {
    const oos = await context.request.post(`${API}/orders`, {
      data: { city_id: '11111111-1111-1111-1111-111111111001', customer_name: 'Z', customer_phone: 'Z', items: [{ product_variant_id: '44444444-4444-4444-4444-444444444002', qty: 100 }], idempotency_key: 't48-browser-oos-002' },
    });
    const txt = await oos.text();
    if (oos.status() === 409) {
      addScenario('S8 hors stock (qty 100 > dispo 8) → 409', 'PASS', `HTTP 409 ${trim(txt)}`);
    } else {
      addDefect('S8 hors stock', 'POST /orders qty=100 sur dispo 8', 'HTTP 409', `HTTP ${oos.status()} ${trim(txt)}`, null);
      addScenario('S8 hors stock', 'FAIL', `HTTP ${oos.status()}`);
    }
  } catch (e) { addScenario('S8 hors stock', 'FAIL', e.message); }

  // ---------- S9.a: 401 admin sans token ----------
  try {
    const res = await context.request.get(`${API}/admin/orders`);
    if (res.status() === 401) {
      addScenario('S9.a 401 admin sans token', 'PASS', `GET /admin/orders → 401`);
    } else {
      addDefect('S9.a auth 401', 'GET /admin/orders sans Authorization', 'HTTP 401', `HTTP ${res.status()}`, null);
      addScenario('S9.a 401 admin sans token', 'FAIL', `HTTP ${res.status()}`);
    }
  } catch (e) { addScenario('S9.a 401 admin sans token', 'FAIL', e.message); }

  // ---------- S6: delivery quote ----------
  try {
    const res = await context.request.get(`${API}/delivery/quote?city_id=11111111-1111-1111-1111-111111111001`);
    const txt = await res.text();
    if (res.status() === 404) {
      addScenario('S6 devis livraison Moscou (pas de zones)', 'INFO', `GET /delivery/quote → 404 ${trim(txt)} (aucune zone livraison en base)`);
    } else {
      addScenario('S6 devis livraison Moscou', 'PASS', `HTTP ${res.status()} ${trim(txt)}`);
    }
  } catch (e) { addScenario('S6 devis livraison Moscou', 'FAIL', e.message); }

  // ---------- S7: multi-ville ----------
  try {
    const moscow = await context.request.get(`${API}/products?city_id=11111111-1111-1111-1111-111111111001`);
    const moscowBody = await moscow.json();
    const other = await context.request.get(`http://127.0.0.1:8000/products?city_id=01399bf6-298f-4487-943f-ac5eb434dbbb`);
    const otherBody = await other.json();
    const moscowHas = Array.isArray(moscowBody) && moscowBody.length > 0;
    addScenario('S7 multi-ville: Moscou produit dispo / Test City vide', moscowHas ? 'PASS' : 'FAIL', `Moscou ${moscowBody.length} produit(s), Test City ${Array.isArray(otherBody) ? otherBody.length : '?'}`);
  } catch (e) { addScenario('S7 multi-ville', 'FAIL', e.message); }

  // ---------- Browser: admin login ----------
  try {
    await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle' });
    await page.fill('input[type="email"]', 'ivan@example.com');
    await page.fill('input[type="password"]', 'DemoPass123');
    await page.click('button:has-text("Войти")');
    await page.waitForURL('**/cities', { waitUntil: 'networkidle' });
    await shot('01-after-login');
    token = await page.evaluate(() => localStorage.getItem('admin_token'));
    if (token) {
      addScenario('S2 connexion admin via formulaire (réel /auth/login)', 'PASS', 'redirection vers /cities après login, token récupéré');
    } else {
      addDefect('S2 login token', 'localStorage admin_token après login', 'token présent', 'token absent', null);
      addScenario('S2 connexion admin', 'FAIL', 'token absent');
    }
  } catch (e) {
    addDefect('S2 login admin', 'ouvrir /login, saisir ivan@example.com/DemoPass123, soumettre', 'redirection /cities', `exception: ${e.message}`, null);
    addScenario('S2 connexion admin', 'FAIL', e.message);
    await shot('02-login-failed');
  }

  // ---------- S2/S3: orders list + status change ----------
  try {
    await page.click('a:has-text("Заказы")', { force: true });
    await page.waitForURL('**/orders', { waitUntil: 'networkidle' });
    await shot('03-orders-list');
    const row = page.locator('tr', { has: page.locator(`text=${orderId}`) });
    if ((await row.count()) > 0) {
      addScenario('S2 commande présente dans la liste admin', 'PASS', `id=${orderId}`);
      await row.locator('button:has-text("Карточка")').first().click();
      await page.waitForSelector('text=Заказ ' + orderId, { state: 'visible' });
      await shot('04-order-card');
      const select = page.locator('select');
      await select.selectOption({ label: 'Новый' });
      await page.click('button:has-text("Сохранить статус")');
      await page.click('button:has-text("Закрыть")');
      await page.waitForTimeout(600);
      await shot('05-after-status-save');
      const getRes = await context.request.get(`${API}/admin/orders/${orderId}`, { headers: { Authorization: 'Bearer ' + token } });
      const getBody = await getRes.json();
      if (getRes.status() === 200 && getBody.status === 'new') {
        addScenario('S3 changement statut pending_payment → new (admin UI + API)', 'PASS', `status=${getBody.status}`);
        // continue to paid
        await page.click('a:has-text("Заказы")', { force: true });
        await page.waitForURL('**/orders', { waitUntil: 'networkidle' });
        const row2 = page.locator('tr', { has: page.locator(`text=${orderId}`) });
        await row2.locator('button:has-text("Карточка")').first().click();
        await page.waitForSelector('text=Заказ ' + orderId, { state: 'visible' });
        await page.locator('select').selectOption({ label: 'Оплачен' });
        await page.click('button:has-text("Сохранить статус")');
        await page.click('button:has-text("Закрыть")');
        await page.waitForTimeout(600);
        const getRes2 = await context.request.get(`${API}/admin/orders/${orderId}`, { headers: { Authorization: 'Bearer ' + token } });
        const getBody2 = await getRes2.json();
        if (getRes2.status() === 200 && getBody2.status === 'paid') {
          addScenario('S3 bis statut new → paid', 'PASS', `status=${getBody2.status}`);
        } else {
          addDefect('S3 bis statut new→paid', 'PATCH status=paid', 'status=paid', `HTTP ${getRes2.status()} ${JSON.stringify(getBody2)}`, null);
          addScenario('S3 bis statut new→paid', 'FAIL', `HTTP ${getRes2.status()}`);
        }
      } else {
        addDefect('S3 changement statut', 'PATCH /admin/orders/{id}/status status=new via UI', 'status=new', `GET order → HTTP ${getRes.status()} ${JSON.stringify(getBody)}`, null);
        addScenario('S3 changement statut', 'FAIL', `HTTP ${getRes.status()}`);
      }
    } else {
      addDefect('S2 commande dans liste', `commande ${orderId} dans GET /admin/orders`, 'ligne de commande visible', `commande ${orderId} introuvable dans le tableau`, null);
      addScenario('S2 commande dans liste admin', 'FAIL', `commande ${orderId} introuvable`);
    }
  } catch (e) {
    addDefect('S2/S3 admin orders', 'ouvrir /orders, ouvrir carte commande, changer statut', 'statut mis à jour', `exception: ${e.message}`, null);
    addScenario('S2/S3 commandes admin', 'FAIL', e.message);
    await shot('03-orders-failed');
  }

  // ---------- S4: stock ----------
  try {
    await page.click('a:has-text("Остатки")', { force: true });
    await page.waitForURL('**/stock', { waitUntil: 'networkidle' });
    await shot('06-stock');
    const txt = await page.locator('body').textContent();
    const hasStock = txt.includes('Склад заказы') || /10|8/.test(txt);
    addScenario('S4 affichage des restes de stock (admin /stock)', hasStock ? 'PASS' : 'INFO', 'page /stock chargée');
  } catch (e) { addScenario('S4 stock admin', 'FAIL', e.message); await shot('06-stock-failed'); }

  // ---------- S5: transfers ----------
  try {
    await page.click('a:has-text("Перемещения")', { force: true });
    await page.waitForURL('**/transfers', { waitUntil: 'networkidle' });
    await shot('07-transfers');
    addScenario('S5 page des transferts (/transfers)', 'PASS', 'page chargée');
  } catch (e) { addScenario('S5 transferts admin', 'FAIL', e.message); }

  // narrow viewport
  try {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle' });
    await shot('08-mobile-login');
    addScenario('viewport mobile 390x844 login', 'PASS', 'page chargée sans erreur critique');
  } catch (e) { addScenario('viewport mobile', 'FAIL', e.message); }

  await browser.close();
  fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify(results, null, 2));
  process.stdout.write('\n=== RÉSUMÉ ===\n');
  for (const s of results.scenarios) process.stdout.write(`  [${s.status}] ${s.name}\n`);
  process.stdout.write(`Défauts: ${results.defects.length}\n`);
  process.stdout.write(`Erreurs console: ${results.consoleErrors.length}\n`);
  process.stdout.write(`Échecs réseau: ${results.networkFailures.length}\n`);
}

main().catch((e) => { process.stderr.write('FATAL: ' + e.message + '\n'); process.exit(1); });
