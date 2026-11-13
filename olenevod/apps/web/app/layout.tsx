import type { Metadata } from "next"

import { CartProvider } from "@/components/cart-provider"
import { CookieBanner } from "@/components/cookie-banner"
import "./globals.css"

export const metadata: Metadata = {
  title: "Оленевод — сыровяленая оленина с доставкой по tundre",
  description: "Северная деликатесная лавка. Сыровяленая оленина, мороженая печень и другие заготовки с доставкой в ваш город.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ru">
      <body>
        <CartProvider>{children}</CartProvider>
        <CookieBanner />
      </body>
    </html>
  )
}
