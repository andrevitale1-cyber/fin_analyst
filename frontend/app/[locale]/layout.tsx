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

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const isEnglish = locale === "en";

  return {
    metadataBase: new URL("https://finanalyser.com.br"),
    title: {
      default: isEnglish
        ? "FinAnalyzer | AI-powered financial statement analysis"
        : "FinAnalyzer | Análise de resultados financeiros com IA",
      template: "%s | FinAnalyzer",
    },
    description: isEnglish
      ? "Find official company earnings releases and earnings call transcripts automatically. Analyze financial performance with AI, clear metrics, and source links."
      : "Encontre releases de resultados e transcripts de empresas automaticamente. Analise o desempenho financeiro com IA, indicadores claros e links para as fontes.",
    applicationName: "FinAnalyzer",
    openGraph: {
      type: "website",
      siteName: "FinAnalyzer",
      locale: isEnglish ? "en_US" : "pt_BR",
      title: isEnglish
        ? "FinAnalyzer | AI-powered financial analysis"
        : "FinAnalyzer | Análise financeira com inteligência artificial",
      description: isEnglish
        ? "Analyze company earnings releases and call transcripts with AI and traceable sources."
        : "Analise releases de resultados e transcripts de calls com IA e fontes verificáveis.",
    },
    twitter: {
      card: "summary_large_image",
      title: isEnglish
        ? "FinAnalyzer | AI-powered financial analysis"
        : "FinAnalyzer | Análise financeira com inteligência artificial",
      description: isEnglish
        ? "Find and analyze company earnings documents with AI and source links."
        : "Encontre e analise documentos financeiros com IA e links para as fontes.",
    },
  };
}

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
