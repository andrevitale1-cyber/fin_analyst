export type ReportMetric = {
  value: string;
  numeric_value?: number | null;
  currency?: string | null;
  unit?: "currency" | "currency_per_share" | "percent" | "multiple" | "number" | null;
};

export function formatReportNumber(value: number, locale: string, compact = true): string {
  const pt = locale.startsWith("pt");
  const scale = compact ? [1e12, 1e9, 1e6].find(size => Math.abs(value) >= size) : undefined;
  const suffix = scale ? (pt ? { 1e12: "tri", 1e9: "bi", 1e6: "mi" } : { 1e12: "T", 1e9: "B", 1e6: "M" })[scale] : "";
  const number = value / (scale || 1);
  const precision = number !== 0 && Math.abs(number) < 0.01 ? { maximumSignificantDigits: 3 } : { maximumFractionDigits: 2 };
  return new Intl.NumberFormat(locale, precision).format(number) + (suffix ? `${pt ? " " : ""}${suffix}` : "");
}

export function formatReportMoney(value: number | null | undefined, currency: string | null | undefined, locale: string, compact = true): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  const symbol = currency === "USD" && locale.startsWith("pt") ? "US$" : currency === "BRL" ? "R$" : currency;
  return `${symbol ? `${symbol} ` : ""}${formatReportNumber(value, locale, compact)}`;
}

export function formatMetricValue(metric: ReportMetric, locale: string): string {
  // Old reports keep their original units; only unambiguous bare numbers are parsed.
  const raw = metric.value.trim();
  const value = metric.numeric_value ?? (/^-?\d+(?:\.\d+)?$/.test(raw) ? Number(raw) : null);
  if (value === null || !Number.isFinite(value)) return metric.value;
  if (metric.unit === "percent") return `${formatReportNumber(value, locale, false)}%`;
  if (metric.unit === "multiple") return `${formatReportNumber(value, locale, false)}×`;
  return formatReportMoney(value, metric.currency, locale, metric.unit !== "currency_per_share");
}
