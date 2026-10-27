const COMPETITORS: Record<string, { name: string; ticker: string }[]> = {
  NVDA: [{ name: "AMD", ticker: "AMD" }, { name: "Alphabet", ticker: "GOOG" }, { name: "Amazon", ticker: "AMZN" }],
  AAPL: [{ name: "Alphabet", ticker: "GOOG" }, { name: "Microsoft", ticker: "MSFT" }],
};
const COMPANIES = [
  { name: "NVIDIA", ticker: "NVDA", match: /\b(?:nvidia|nvda)\b/i },
  { name: "Apple", ticker: "AAPL", match: /\b(?:apple|aapl)\b/i },
  { name: "AMD", ticker: "AMD", match: /\b(?:amd|advanced micro devices)\b/i },
  { name: "Alphabet", ticker: "GOOG", match: /\b(?:alphabet|google|googl?)\b/i },
  { name: "Amazon", ticker: "AMZN", match: /\b(?:amazon|amzn)\b/i },
  { name: "Microsoft", ticker: "MSFT", match: /\b(?:microsoft|msft)\b/i },
  { name: "Intel", ticker: "INTC", match: /\b(?:intel|intc)\b/i },
  { name: "Broadcom", ticker: "AVGO", match: /\b(?:broadcom|avgo)\b/i },
  { name: "Micron", ticker: "MU", match: /\bmicron\b/i },
  { name: "Oracle", ticker: "ORCL", match: /\b(?:oracle|orcl)\b/i },
  { name: "Meta", ticker: "META", match: /\b(?:meta platforms|facebook)\b/i },
  { name: "Tesla", ticker: "TSLA", match: /\b(?:tesla|tsla)\b/i },
];

export default function ReportCompetitors({ company, locale, narrative }: { company: string; locale: string; narrative: string }) {
  const normalized = company.toUpperCase();
  const issuer = COMPANIES.find(item => item.ticker === normalized || item.name.toUpperCase() === normalized)?.ticker;
  const candidates = [...(COMPETITORS[issuer || normalized] || []), ...COMPANIES.filter(item => item.match.test(narrative))];
  const items = candidates.filter((item, index) => item.ticker !== issuer && candidates.findIndex(other => other.ticker === item.ticker) === index);
  if (!items.length) return null;
  const en = locale === "en";
  return <aside className="mt-7" aria-label={en ? "Competitors" : "Concorrentes"}>
    <h3 className="text-sm font-bold text-slate-900">{en ? "Competitors" : "Concorrentes"}</h3>
    <p className="mt-2 text-xs leading-5 text-slate-500">{en ? "Open a company to check report availability." : "Abra uma empresa para consultar a disponibilidade do relatório."}</p>
    <ul className="mt-4 overflow-hidden rounded-xl border border-slate-200">{items.map(item => <li key={item.ticker} className="border-b border-slate-100 last:border-b-0"><a className="flex min-h-[68px] items-center gap-3 px-4 py-3 hover:bg-slate-50" href={`/${locale}/dashboard/reports?company=${encodeURIComponent(item.ticker)}`}><img className="h-10 w-10 rounded-md object-contain" src={`/benefits/company-logos/${item.ticker}.webp`} width="40" height="40" alt=""/><span className="font-semibold text-slate-900">{item.name} <span className="ml-2 text-xs text-slate-400">{item.ticker}</span></span><span className="ml-auto text-xl text-slate-400" aria-hidden="true">›</span></a></li>)}</ul>
  </aside>;
}
