/**
 * build-brand.mjs
 *
 * Генерирует растровые производные бренда из исходных SVG:
 *   avatars 640×640 (telegram/vk/max), favicon.ico (32+16), favicon-32.png,
 *   apple-touch-icon 180, icon-192/512, maskable-512, og-default 1200×630.
 *
 * Требует sharp (npm install sharp). Если sharp не установлен — скрипт только
 * печатает инструкцию; растровые файлы уже лежат в brand/ (собраны отдельно).
 *
 * Запуск: node brand/build-brand.mjs   (из корня репозитория)
 */

import fs from "node:fs"
import path from "node:path"

const ROOT = path.resolve(process.cwd())
const BRAND = path.join(ROOT, "olenevod", "brand")

const AVATARS = [
  { svg: "logo-emblem-seal.svg", out: "avatar-telegram.png", w: 640 },
  { svg: "logo-emblem-seal.svg", out: "avatar-vk.png", w: 640 },
  { svg: "logo-emblem-seal.svg", out: "avatar-max.png", w: 640 },
]

const ICONS = [
  { svg: "logo-icon.svg", out: "favicon-32.png", w: 32 },
  { svg: "logo-icon.svg", out: "apple-touch-icon.png", w: 180 },
  { svg: "logo-icon.svg", out: "icon-192.png", w: 192 },
  { svg: "logo-icon.svg", out: "icon-512.png", w: 512 },
  { svg: "logo-icon.svg", out: "maskable-512.png", w: 512, scale: 0.6 },
]

const OG = { svg: "logo-emblem-seal.svg", out: "og-default.png", w: 1200, h: 630 }

let sharp
try {
  sharp = (await import("sharp")).default
} catch {
  sharp = null
}

function svgPath(name) {
  return path.join(BRAND, name)
}

async function renderPng({ svg, out, w, h, scale = 1 }) {
  if (!sharp) {
    console.log(`[skip] ${out}: sharp не установлен (npm install sharp)`)
    return
  }
  const input = fs.readFileSync(svgPath(svg))
  const height = h || Math.round(w * 1.0) // квадрат по умолчанию; og — 1200×630
  await sharp(input)
    .resize(Math.round(w * scale), height ? Math.round(height * scale) : undefined, {
      fit: "inside",
      position: "centre",
      background: { r: 20, g: 16, b: 13, alpha: 1 }, // ink-900
    })
    .png()
    .toFile(path.join(BRAND, out))
  console.log(`[ok] ${out} (${w}×${height || w})`)
}

async function main() {
  if (!sharp) {
    console.log(
      "sharp не найден. Установите: npm install sharp --prefix olenevod/brand  (devDep), " +
        "затем запустите node brand/build-brand.mjs\nРастровые файлы уже собраны в brand/*.png"
    )
  }
  for (const a of AVATARS) await renderPng({ ...a, h: a.w })
  await renderPng({ svg: "logo-icon.svg", out: "favicon-32.png", w: 32, h: 32 })
  await renderPng({ svg: "logo-icon.svg", out: "og-default.png", ...OG })
  await renderPng({ svg: "logo-icon.svg", out: "apple-touch-icon.png", w: 180, h: 180 })
  await renderPng({ svg: "logo-icon.svg", out: "icon-192.png", w: 192, h: 192 })
  await renderPng({ svg: "logo-icon.svg", out: "icon-512.png", w: 512, h: 512 })
  await renderPng({ svg: "logo-icon.svg", out: "maskable-512.png", w: 512, h: 512, scale: 0.6 })
  // favicon.ico из favicon-32.png + 16×16 варианта — собирается отдельно (ICO-контейнер)
  console.log("Готово. Файлы: brand/*.png, brand/favicon.ico")
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
