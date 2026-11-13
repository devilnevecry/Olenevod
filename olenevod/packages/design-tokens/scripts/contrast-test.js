/**
 * contrast-test.js
 *
 * Проверяет пары цветов контраста по DESIGN_SYSTEM §2.2 (WCAG 2.2 AA):
 *   обычный текст — ≥ 4.5:1
 *   крупный текст и графика (≥24px или ≥18.66px жирный) — ≥ 3:1
 *
 * Пары (текст / фон) — как в DESIGN_SYSTEM §2.2:
 *   paper-100/ink-900, paper-300/ink-800, paper-500/ink-900 (≥14px),
 *   ember-300/ink-900, paper-100/ember-600 (кнопка),
 *   ink-900/brass-400, paper-ink/paper-bg, ember-500/ink-900 (только крупное)
 *
 * Запуск: node scripts/contrast-test.js  (из корня packages/design-tokens)
 *         npm run test:contrast
 */

import fs from "node:fs"
import path from "node:path"

const TOKENS_PATH = path.resolve(process.cwd(), "tokens.json")

function parseHex(hex) {
  hex = hex.replace(/^#/, "")
  if (hex.length === 3) hex = hex.split("").map((c) => c + c).join("")
  return {
    r: parseInt(hex.slice(0, 2), 16) / 255,
    g: parseInt(hex.slice(2, 4), 16) / 255,
    b: parseInt(hex.slice(4, 6), 16) / 255,
  }
}

function linearize(c) {
  return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
}

function luminance(hex) {
  const c = parseHex(hex)
  return 0.2126 * linearize(c.r) + 0.7152 * linearize(c.g) + 0.0722 * linearize(c.b)
}

function contrast(a, b) {
  const la = luminance(a)
  const lb = luminance(b)
  const light = Math.max(la, lb)
  const dark = Math.min(la, lb)
  return (light + 0.05) / (dark + 0.05)
}

function fmt(n) {
  return Number(n).toFixed(2)
}

const tokens = JSON.parse(fs.readFileSync(TOKENS_PATH, "utf8"))
const C = tokens.color

// [текст, фон, минимум, подпись]
const CASES = [
  ["paper-100", "ink-900", 4.5, "основной текст"],
  ["paper-300", "ink-800", 4.5, "вторичный текст"],
  ["paper-500", "ink-900", 4.5, "третичный текст (≥14px)"],
  ["ember-300", "ink-900", 4.5, "акцентный мелкий текст / ссылки"],
  ["paper-100", "ember-600", 4.5, "кнопка primary"],
  ["ink-900", "brass-400", 4.5, "текст на латуни"],
  ["paper-ink", "paper-bg", 4.5, "инверсная бумажная секция"],
  ["ember-500", "ink-900", 3.0, "акцент крупный (≥24px / графика)"],
]

let failed = 0
console.log("Контрастные пары (WCAG 2.2 AA):\n")
console.log("пара                    контраст  минимум  статус")
console.log("--------------------------------------------------")

for (const [fg, bg, min, label] of CASES) {
  const value = contrast(C[fg], C[bg])
  const ok = value >= min
  if (!ok) failed++
  const status = ok ? "OK  " : "FAIL"
  console.log(
    `${fg.padEnd(10)}/${bg.padEnd(9)}`.padEnd(23) +
      `${fmt(value)}:1`.padEnd(10) +
      `${fmt(min)}:1`.padEnd(10) +
      `${status}  ${label}`
  )
}

console.log("")
if (failed === 0) {
  console.log(`Все ${CASES.length} пар прошли порог WCAG AA. ТЕСТ ЗЕЛЁНЫЙ.`)
  process.exit(0)
} else {
  console.error(`${failed} пара(ы) не прошли порог контраста. ТЕКСТ: скорректируйте токены минимально (см. DESIGN_SYSTEM §2.2).`)
  process.exit(1)
}
