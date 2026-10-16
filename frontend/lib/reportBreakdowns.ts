import { formatReportMoney } from "./reportNumbers";

export type ReportBreakdown = { category: "segment" | "geography"; label: string; value: string; share: number | null; source_id: string; numeric_value?: number | null; currency?: string | null; period?: string | null; group_complete?: boolean };
type History = { period: string; currency: string | null; revenue: number | null };

export function selectSegmentBreakdowns(items: ReportBreakdown[]): ReportBreakdown[] {
  const rows = items.filter(item => item.category === "segment");
  // Saved reports can contain overlapping operating segments and product platforms.
  const segments = rows.filter(item => !/\([^)]*\b(?:platform|plataforma)s?\b/i.test(item.label));
  const selected = segments.length ? segments : rows;
  const unique = new Map<string, ReportBreakdown>();
  for (const item of selected) {
    const key = `${item.label.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().replace(/&/g, " and ").replace(/[^\p{L}\p{N}]/gu, "")}|${item.period || ""}|${item.currency || ""}`;
    const previous = unique.get(key);
    if (!previous || (previous.numeric_value == null && item.numeric_value != null)) unique.set(key, item);
  }
  return [...unique.values()];
}

export function breakdownAmount(item: ReportBreakdown): { amount: number; currency: string } | null {
  if (item.numeric_value != null && Number.isFinite(item.numeric_value) && item.currency) return { amount: item.numeric_value, currency: item.currency };
  // Compatibility with saved monetary strings; never guess a currency from an issuer.
  const match = item.value.trim().match(/^(US\$|R\$|[A-Z]{3})\s+(-?[\d.,]+)$/);
  if (!match) return null;
  let value = match[2];
  if (/^-?\d{1,3}(?:[.,]\d{3}){2,}$/.test(value)) value = value.replace(/[.,]/g, "");
  else if (/^-?\d+,\d{1,2}$/.test(value)) value = value.replace(",", ".");
  else if (!/^-?\d+(?:\.\d+)?$/.test(value)) return null;
  const amount = Number(value);
  return Number.isFinite(amount) ? { amount, currency: match[1] === "US$" ? "USD" : match[1] === "R$" ? "BRL" : match[1] } : null;
}

export function prepareBreakdowns(items: ReportBreakdown[], history: History[] = []): ReportBreakdown[] {
  if (items.length < 2 || items.some(item => item.share == null || item.share < 0 || item.share > 1)) return items;
  const sum = items.reduce((value, item) => value + item.share!, 0);
  if (Math.abs(sum - 1) > 0.001) return items;
  const periods = items.map(item => (item.period || item.label).match(/\b(?:19|20)\d{2}\b/)?.[0]);
  const samePeriod = periods.every(period => period && period === periods[0]);
  const amounts = items.map(breakdownAmount);
  const total = amounts.reduce((value, item) => value + (item?.amount || 0), 0);
  const matchingRevenue = samePeriod && amounts.every(item => item && item.currency === amounts[0]?.currency) && history.some(row => row.period.includes(periods[0]!) && row.currency === amounts[0]?.currency && row.revenue && Math.abs(total - row.revenue) <= Math.abs(row.revenue) * 0.001);
  const explicitComplete = items.every(item => item.group_complete) && items.every(item => item.source_id === items[0].source_id && item.period === items[0].period);
  return explicitComplete || matchingRevenue ? items.map(item => ({ ...item, share: item.share! * 100 })) : items;
}

export function breakdownValue(item: ReportBreakdown, locale: string): string {
  const amount = breakdownAmount(item);
  return amount ? formatReportMoney(amount.amount, amount.currency, locale) : item.value;
}
