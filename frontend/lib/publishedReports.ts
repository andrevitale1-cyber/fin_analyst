// Editorial HTML editions retain their original audit status; no automatic audit is bypassed.
export const PUBLISHED_REPORTS = [{
  id: "editorial-nvda-20261022",
  company: "NVDA",
  company_name: "NVIDIA Corporation",
  symbol: "NVDA",
  period: "Company overview",
  scope: "company" as const,
  locale: "pt" as const,
  kind: "company" as const,
  created_at: "2026-10-22T15:00:00Z",
  as_of: "2026-10-22",
  score: 4,
  is_public: true,
  url: "/published-reports/nvda-20261022.html",
}];

export function publishedReportsForLocale(locale: string) {
  return PUBLISHED_REPORTS.map(report => ({
    ...report,
    locale: locale === "en" ? "en" as const : "pt" as const,
    url: locale === "en" ? report.url.replace(/\.html$/, "-en.html") : report.url,
  }));
}

export function publishedReportForCompany(company: string, locale = "pt") {
  const normalized = company.trim().toUpperCase().replace(/[^A-Z0-9]/g, "");
  return publishedReportsForLocale(locale).find(report => [report.company, "NVIDIA", "NVIDIACORPORATION"].includes(normalized));
}
