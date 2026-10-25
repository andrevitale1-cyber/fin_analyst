import type { FullReport } from "../components/FullReports";

// Keep stored editions intact; readers show analyst targets rather than our model prices.
export function analystTargetsOnly(report: FullReport): FullReport {
  const proprietary = (text: string) => /\bDCF\b|\bWACC\b|discounted cash flow|fair[- ]value|intrinsic value|valor justo|valor intr[ií]nseco|valor estimado (?:por a[cç][aã]o|no cen[aá]rio)/i.test(text);
  return {
    ...report,
    sections: report.sections.filter(section => section.id !== "valuation").map(section => ({
      ...section,
      summary: proprietary(section.summary) ? "" : section.summary,
      paragraphs: section.paragraphs.filter(text => !proprietary(text)),
      bullets: section.bullets.filter(text => !proprietary(text)),
    })),
    signals: report.signals?.filter(signal => signal.id !== "valuation" && !proprietary(signal.value)),
    metrics: report.metrics.filter(metric => !proprietary(metric.label)),
    watchpoints: report.watchpoints.filter(text => !proprietary(text)),
  };
}
