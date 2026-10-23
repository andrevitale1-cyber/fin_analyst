// Editorial HTML editions retain their original audit status; no automatic audit is bypassed.
export const PUBLISHED_REPORTS = [{
  id: "editorial-aapl-20261022",
  company: "AAPL",
  company_name: "Apple Inc.",
  symbol: "AAPL",
  period: "Company overview",
  scope: "company" as const,
  locale: "pt" as const,
  kind: "company" as const,
  created_at: "2026-10-22T15:00:00Z",
  as_of: "2026-10-22",
  score: 3,
  is_public: true,
  url: "/published-reports/aapl-20261022.html",
}];

export function publishedReportForCompany(company: string) {
  const normalized = company.trim().toUpperCase().replace(/[^A-Z0-9]/g, "");
  return PUBLISHED_REPORTS.find(report => [report.company, "APPLE", "APPLEINC"].includes(normalized));
}
