import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import "../globals.css";

const inter = Inter({ subsets: ["latin"] });

const playfair = Playfair_Display({ 
  subsets: ["latin"],
  weight: ["700", "800", "900"],
  variable: "--font-playfair"
});

export const metadata: Metadata = {
  title: "FinAnalyzer",
  description: "AI Financial Analysis",
};

export default async function RootLayout({
  children,
  params,
}: Readonly<{
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}>) {
  const { locale } = await params;
  const messages = await getMessages();

  return (
    <ClerkProvider>
      <html lang={locale} className={playfair.variable}>
        <body className={inter.className}>
          <NextIntlClientProvider messages={messages}>
            {children}
          </NextIntlClientProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}