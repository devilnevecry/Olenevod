/** @type {import('tailwindcss').Config} */
const designTokens = require("../../packages/design-tokens/tailwind/preset.js").default

module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: designTokens.theme,
  },
  plugins: [],
}
