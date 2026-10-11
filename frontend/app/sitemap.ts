import type { MetadataRoute } from "next";

const siteUrl = "https://finanalyser.com.br";
const publicPages = ["", "/privacy", "/terms", "/refund"];

export default function sitemap(): MetadataRoute.Sitemap {
  return publicPages.flatMap((page) =>
    (["pt", "en"] as const).map((locale) => ({
      url: `${siteUrl}/${locale}${page}`,
      changeFrequency: page === "" ? "weekly" as const : "yearly" as const,
      priority: page === "" ? 1 : 0.3,
      alternates: {
        languages: {
          "pt-BR": `${siteUrl}/pt${page}`,
          en: `${siteUrl}/en${page}`,
          "x-default": `${siteUrl}/pt${page}`,
        },
      },
    })),
  );
}
