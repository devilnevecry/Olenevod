import tsParser from "@typescript-eslint/parser"
import nextPlugin from "@next/eslint-plugin-next"

// ESLint 9 flat config (eslint-config-next is incompatible with the rushstack
// eslint-patch on this Node version, so rules are wired directly).
export default [
  {
    ignores: ["node_modules", ".next", "out", "build"],
  },
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
      },
    },
    plugins: {
      "@next/next": nextPlugin,
    },
    rules: {
      "@next/next/no-html-link-for-pages": "off",
    },
  },
  {
    files: ["**/*.{js,mjs,cjs}"],
    languageOptions: {
      sourceType: "module",
    },
  },
]
