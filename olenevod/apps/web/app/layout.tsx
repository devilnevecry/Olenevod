import type { Metadata } from "next"

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
      <body>{children}</body>
    </html>
  )
}
