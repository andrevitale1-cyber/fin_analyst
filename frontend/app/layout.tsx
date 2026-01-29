import type { Metadata } from "next";
import { Inter } from "next/font/google"; // Trocamos Geist por Inter
import "./globals.css";

// Configura a fonte Inter (padrão e compatível)
const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FinAnalyzer.AI",
  description: "Análise financeira com IA",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-br">
      {/* Aplicamos a classe da fonte Inter no corpo do site */}
      <body className={inter.className}>{children}</body>
    </html>
  );
}