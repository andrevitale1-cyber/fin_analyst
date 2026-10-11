import type { MetadataRoute } from "next";

const siteUrl = "https://finanalyser.com.br";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/dashboard/", "/pt/dashboard/", "/en/dashboard/", "/profile/", "/api/"],
    },
    sitemap: `${siteUrl}/sitemap.xml`,
    host: siteUrl,
  };
}
