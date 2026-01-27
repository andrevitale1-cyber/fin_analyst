import type { Metadata } from "next";
import { Inter } from "next/font/google"; // Mudamos para Inter
import "./globals.css";
import { ClerkProvider } from "@clerk/nextjs";

const inter = Inter({ subsets: ["latin"] }); // Configuração da fonte Inter

export const metadata: Metadata = {
  title: "FinAnalyzer.AI",
  description: "Analise de balanços com IA",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="pt-br">
        <body className={inter.className}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}