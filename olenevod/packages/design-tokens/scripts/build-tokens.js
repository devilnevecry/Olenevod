/**
 * build-tokens.js
 *
 * Читает packages/design-tokens/tokens.json и генерирует:
 *   - css/tokens.css      — CSS custom properties (--ol-*)
 *   - tailwind/preset.js  — Tailwind preset (theme.extend)
 *
 * Запуск: node scripts/build-tokens.js  (из корня packages/design-tokens)
 */

import fs from "node:fs"
import path from "node:path"

const ROOT = path.resolve(process.cwd())
const TOKENS_PATH = path.join(ROOT, "tokens.json")
const CSS_OUT = path.join(ROOT, "css", "tokens.css")
const PRESET_OUT = path.join(ROOT, "tailwind", "preset.js")

function readTokens() {
  const raw = fs.readFileSync(TOKENS_PATH, "utf8")
  return JSON.parse(raw)
}

function sanitizeName(name) {
  return name.replace(/[^a-z0-9-]/gi, "-")
}

function px(value) {
  return typeof value === "number" ? `${value}px` : value
}

function generateCSS(tokens) {
  const lines = []
  lines.push("/*")
  lines.push(" * ОКНО: этот файл сгенерирован автоматически из tokens.json.")
  lines.push(" * Не править вручную — править tokens.json и пересобирать: npm run build")
  lines.push(" */")
  lines.push("")
  lines.push(":root {")

  // Цвета
  lines.push("  /* Цвета (DESIGN_SYSTEM §2) */")
  for (const [name, value] of Object.entries(tokens.color || {})) {
    lines.push(`  --ol-color-${sanitizeName(name)}: ${value};`)
  }

  // Шрифты
  lines.push("")
  lines.push("  /* Шрифты (DESIGN_SYSTEM §3) */")
  const tf = tokens.typography || {}
  if (tf.fontFamily) {
    for (const [role, stack] of Object.entries(tf.fontFamily)) {
      lines.push(`  --ol-font-family-${role}: ${JSON.stringify(stack)};`)
    }
  }
  if (tf.fontSize) {
    for (const [name, value] of Object.entries(tf.fontSize)) {
      lines.push(`  --ol-font-size-${sanitizeName(name)}: ${value};`)
    }
  }
  if (tf.lineHeight) {
    for (const [name, value] of Object.entries(tf.lineHeight)) {
      lines.push(`  --ol-line-height-${sanitizeName(name)}: ${value};`)
    }
  }
  if (tf.letterSpacing) {
    for (const [name, value] of Object.entries(tf.letterSpacing)) {
      lines.push(`  --ol-letter-spacing-${sanitizeName(name)}: ${value};`)
    }
  }
  if (tf.fontWeight) {
    for (const [name, value] of Object.entries(tf.fontWeight)) {
      lines.push(`  --ol-font-weight-${sanitizeName(name)}: ${value};`)
    }
  }

  // Отступы
  lines.push("")
  lines.push("  /* Отступы (базовая единица 4px, DESIGN_SYSTEM §4) */")
  tokens.spacing.forEach((v, i) => {
    lines.push(`  --ol-space-${i}: ${v}px;`)
  })

  // Брейкпоинты
  lines.push("")
  lines.push("  /* Брейкпоинты (DESIGN_SYSTEM §4) */")
  for (const [name, value] of Object.entries(tokens.breakpoints || {})) {
    lines.push(`  --ol-breakpoint-${name}: ${value}px;`)
  }

  // z-индексы
  lines.push("")
  lines.push("  /* Z-индексы (DESIGN_SYSTEM §4) */")
  for (const [name, value] of Object.entries(tokens.zIndex || {})) {
    lines.push(`  --ol-z-${sanitizeName(name)}: ${value};`)
  }

  // Радиусы/границы
  lines.push("")
  lines.push("  /* Радиусы и границы (DESIGN_SYSTEM §5) */")
  for (const [name, value] of Object.entries(tokens.borderRadius || {})) {
    lines.push(`  --ol-radius-${sanitizeName(name)}: ${value}px;`)
  }
  for (const [name, value] of Object.entries(tokens.borderWidth || {})) {
    lines.push(`  --ol-border-${sanitizeName(name)}: ${value}px;`)
  }

  // Токены движения (ANIMATION_GUIDELINES §2)
  lines.push("")
  lines.push("  /* Токены движения (ANIMATION_GUIDELINES §2) */")
  const motion = tokens.motion || {}
  for (const [name, value] of Object.entries(motion)) {
    if (name === "springCart" || name === "springDrawer") continue
    lines.push(`  --ol-motion-${sanitizeName(name)}: ${value};`)
  }
  lines.push(`  --ol-motion-spring-cart: ${motion.springCart?.stiffness ?? 380} ${motion.springCart?.damping ?? 28} ${motion.springCart?.mass ?? 1};`)
  lines.push(`  --ol-motion-spring-drawer: ${motion.springDrawer?.stiffness ?? 300} ${motion.springDrawer?.damping ?? 34};`)
  lines.push(`  --ol-motion-scale: ${motion.motionScale ?? 1};`)

  lines.push("}")
  lines.push("")

  // Утилитарные классы поверх переменных (опционально, удобно для верстки)
  lines.push("/* Утилиты на базе токенов */")
  lines.push(".ol-color-ink-900 { color: var(--ol-color-ink-900); }")
  lines.push(".ol-bg-ink-900 { background-color: var(--ol-color-ink-900); }")
  lines.push(".ol-color-paper-100 { color: var(--ol-color-paper-100); }")
  lines.push(".ol-color-ember-600 { color: var(--ol-color-ember-600); }")
  lines.push(".ol-color-ink-950 { color: var(--ol-color-ink-950); }")
  lines.push("")

  fs.mkdirSync(path.dirname(CSS_OUT), { recursive: true })
  fs.writeFileSync(CSS_OUT, lines.join("\n") + "\n")
  return CSS_OUT
}

function generateTailwindPreset(tokens) {
  const tf = tokens.typography || {}
  const fontFamily = {}
  if (tf.fontFamily) {
    for (const [role, stack] of Object.entries(tf.fontFamily)) {
      fontFamily[role] = ["var(--ol-font-family-" + role + ")", ...stack]
    }
  }
  const fontSize = {}
  if (tf.fontSize) {
    for (const [name, value] of Object.entries(tf.fontSize)) {
      fontSize[name] = [value, { lineHeight: tf.lineHeight?.[name], letterSpacing: tf.letterSpacing?.[name] }]
    }
  }

  const screens = {}
  for (const [name, value] of Object.entries(tokens.breakpoints || {})) {
    screens[name] = `${value}px`
  }

  const colors = {}
  for (const [name, value] of Object.entries(tokens.color || {})) {
    colors[name] = { DEFAULT: value }
  }

  const spacing = {}
  tokens.spacing.forEach((v, i) => {
    spacing[i] = `${v}px`
  })

  const zIndex = {}
  for (const [name, value] of Object.entries(tokens.zIndex || {})) {
    zIndex[name] = value
  }

  const borderRadius = {}
  for (const [name, value] of Object.entries(tokens.borderRadius || {})) {
    borderRadius[name] = `${value}px`
  }

  const borderWidth = {}
  for (const [name, value] of Object.entries(tokens.borderWidth || {})) {
    borderWidth[name] = `${value}px`
  }

  const preset = {
    prefix: "",
    important: false,
    separator: ":",
    theme: {
      screens,
      colors,
      spacing,
      fontFamily,
      fontSize,
      lineHeight: tf.lineHeight || {},
      letterSpacing: tf.letterSpacing || {},
      fontWeight: tf.fontWeight || {},
      borderRadius,
      borderWidth,
      zIndex,
      extend: {}
    },
    corePlugins: [],
    plugins: []
  }

  const code =
    "// ОКНО: этот файл сгенерирован автоматически из tokens.json.\n" +
    "// Не править вручную — править tokens.json и пересобирать: npm run build\n" +
    "\n" +
    "export default " + JSON.stringify(preset, null, 2) + "\n"

  fs.mkdirSync(path.dirname(PRESET_OUT), { recursive: true })
  fs.writeFileSync(PRESET_OUT, code)
  return PRESET_OUT
}

const tokens = readTokens()
const cssPath = generateCSS(tokens)
const presetPath = generateTailwindPreset(tokens)

console.log(`tokens.json → ${cssPath}`)
console.log(`tokens.json → ${presetPath}`)
