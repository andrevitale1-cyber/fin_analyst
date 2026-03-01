import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

const playfair = Playfair_Display({ 
  subsets: ["latin"],
  weight: ["700", "800", "900"],
  variable: "--font-playfair"
});

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
    <ClerkProvider>
      <html lang="pt-br" className={playfair.variable}>
        <body className={inter.className}>{children}</body>
      </html>
    </ClerkProvider>
  );
}