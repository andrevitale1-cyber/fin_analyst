import type { FullReport } from "./FullReports";
import { formatReportMoney, formatReportNumber } from "../lib/reportNumbers";

type Consensus = NonNullable<FullReport["analyst_consensus"]>;
export default function ReportAnalystConsensus({ consensus, market, locale, formatDate }: { consensus: Consensus; market: FullReport["market"]; locale: string; formatDate: (value: string) => string }) {
  const en = locale === "en";
  const counts = [consensus.bullish, consensus.neutral, consensus.bearish];
  const complete = counts.every(value => value !== null) && counts.reduce<number>((sum, value) => sum + (value ?? 0), 0) > 0;
  const total = counts.reduce<number>((sum, value) => sum + (value ?? 0), 0);
  const compatiblePrice = market?.currency === consensus.currency ? market?.price : null;
  const upside = consensus.target_mean != null && compatiblePrice && compatiblePrice > 0 ? (consensus.target_mean / compatiblePrice - 1) * 100 : null;
  const low = consensus.target_low, high = consensus.target_high;
  const hasRange = low != null && high != null && high > low;
  const priceOnRange = hasRange && compatiblePrice != null && compatiblePrice >= low! && compatiblePrice <= high!;
  const marker = (value: number) => `${Math.max(0, Math.min(100, (value - low!) / (high! - low!) * 100))}%`;
  const money = (value: number | null) => formatReportMoney(value, consensus.currency, locale);
  const number = (value: number) => formatReportNumber(value, locale, false);
  const labels = en ? ["buy", "hold", "sell"] : ["compra", "neutras", "venda"];
  return <div className="mt-6 grid gap-6 rounded-xl border border-slate-200 bg-white p-5 sm:grid-cols-2 sm:p-6">
    <div>
      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{en ? "Analyst consensus" : "Consenso de analistas"}</p>
      {consensus.rating && <h3 className="mt-2 text-xl font-bold leading-7 text-slate-900">{consensus.rating}</h3>}
      <p className="mt-3 text-xs leading-5 text-slate-500">{consensus.as_of ? formatDate(consensus.as_of) : ""}{consensus.analyst_count != null ? ` · ${consensus.analyst_count} ${en ? "analysts" : "analistas"}` : ""}</p>
      {complete && <><div className="mt-5 flex h-2.5 overflow-hidden rounded-full" role="img" aria-label={counts.map((count, index) => `${count} ${labels[index]}`).join(", ")}>{counts.map((count, index) => <span key={labels[index]} style={{width:`${count! / total * 100}%`,background:["#18a875", "#b8c2ce", "#ed7b76"][index]}} />)}</div><div className="mt-3 grid grid-cols-3 gap-2 text-xs text-slate-500">{counts.map((count, index) => <p key={labels[index]}><strong className="block text-base text-slate-800">{count}</strong>{labels[index]}</p>)}</div></>}
      {!complete && counts.some(value => value !== null) && <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-500">{counts.map((value, index) => value == null ? null : <span key={labels[index]}>{value} {labels[index]}</span>)}</div>}
    </div>
    <div className="border-t border-slate-100 pt-5 sm:border-l sm:border-t-0 sm:pl-6 sm:pt-0">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">{en ? "Average analyst target" : "Preço-alvo médio dos analistas"}</p>
      <p className="mt-1 text-3xl font-bold tracking-tight text-slate-900">{money(consensus.target_mean)}</p>
      {upside != null && <p className={`mt-2 text-xs ${upside >= 0 ? "text-emerald-700" : "text-rose-700"}`}>{upside >= 0 ? "+" : ""}{number(upside)}% {en ? "versus" : "versus"} {money(compatiblePrice ?? null)}</p>}
      {hasRange && <><div className="relative mt-8 h-1.5 rounded bg-slate-200" aria-label={`${en ? "Low" : "Mínimo"} ${money(low)}, ${en ? "high" : "máximo"} ${money(high)}`}>
        {consensus.target_mean != null && <i className="absolute -top-1.5 h-5 w-1 bg-violet-500" style={{left:marker(consensus.target_mean)}} />}
        {priceOnRange && <i className="absolute -top-1.5 h-5 w-1 bg-slate-900" style={{left:marker(compatiblePrice!)}} />}
      </div><div className="mt-3 flex justify-between gap-4 text-xs text-slate-500"><span>{money(low)}<br/>{en ? "Low" : "Mínimo"}</span><span className="text-right">{money(high)}<br/>{en ? "High" : "Máximo"}</span></div><p className="mt-3 text-[10px] text-slate-500">{en ? "Average" : "Média"} <span className="inline-block h-2 w-2 rounded-full bg-violet-500" />{priceOnRange && <> · {en ? "Share price" : "Cotação"} <span className="inline-block h-2 w-2 rounded-full bg-slate-900" /></>}{compatiblePrice != null && !priceOnRange && <> · {en ? "Share price outside range:" : "Cotação fora da faixa:"} {money(compatiblePrice)}</>}</p></>}
    </div>
  </div>;
}
