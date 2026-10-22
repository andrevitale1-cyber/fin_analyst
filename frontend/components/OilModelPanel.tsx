"use client";

import type { InvestmentModel } from "../lib/investmentModel";
import { formatReportMoney, formatReportNumber } from "../lib/reportNumbers";

type Props = {model: InvestmentModel; locale: string; mode: "forecast" | "valuation"; selectedCase: string; onCaseChange: (name: string) => void};

export default function OilModelPanel({model, locale, mode, selectedCase, onCaseChange}: Props) {
  const pt = locale.startsWith("pt");
  const active = model.cases.find(c => c.case === selectedCase) || model.cases[1];
  const bridge = active?.equity_bridge;
  if (!active || !bridge) return null;
  const money = (n: number, compact = true) => formatReportMoney(n, "BRL", locale, compact);
  const number = (n: number) => formatReportNumber(n, locale, false);
  const names = {bear: pt ? "Pessimista" : "Bear", base: "Base", bull: pt ? "Otimista" : "Bull"};
  return <div className="mt-6 min-w-0 rounded-2xl border border-sky-100 bg-sky-50/30 p-4 sm:p-5">
    <p className="text-xs font-bold uppercase tracking-wide text-sky-800">{pt ? "Modelo operacional · petróleo e gás" : "Operating model · oil and gas"}</p>
    <p className="mt-2 text-xs leading-5 text-slate-500">{pt ? "Projeções condicionais da IA, separadas de resultados realizados e guidance." : "Conditional AI forecasts, separate from reported results and guidance."}</p>
    <div aria-label={pt ? "Escolher cenário" : "Choose scenario"} className="mt-4 grid grid-cols-3 gap-2">{model.cases.map(c => <button key={c.case} type="button" aria-pressed={active.case === c.case} onClick={() => onCaseChange(c.case)} className={`min-h-11 rounded-xl border px-2 py-3 text-xs font-semibold ${active.case === c.case ? "border-sky-400 bg-white text-sky-900" : "border-slate-200 text-slate-600"}`}>{names[c.case]}</button>)}</div>
    <p className="mt-4 text-xs leading-5 text-slate-600">{active.assumptions.rationale}</p>
    {mode === "forecast" ? <>
      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white"><table className="w-full min-w-[720px] text-left text-xs"><caption className="sr-only">{pt ? "Premissas operacionais e fluxo de caixa por exercício" : "Annual operating assumptions and cash flows"}</caption><thead className="bg-slate-50"><tr>{[pt ? "Exercício" : "Year", "Brent · US$/bbl", "R$/US$", pt ? "Produção · kboe/d" : "Production · kboe/d", pt ? "Receita externa" : "External revenue", "EBITDA", "Capex", "FCFF"].map(label => <th key={label} className="px-3 py-3">{label}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{active.projections.map(row => <tr key={row.period}><th className="px-3 py-3">{row.period}</th><td className="px-3">{number(row.oil_drivers!.brent_usd)}</td><td className="px-3">{number(row.oil_drivers!.usd_brl)}</td><td className="px-3">{number(row.oil_drivers!.production_kboed)}</td><td className="px-3">{money(row.revenue)}</td><td className="px-3">{money(row.ebitda)}</td><td className="px-3">{money(row.capex)}</td><td className="px-3">{money(row.fcff)}</td></tr>)}</tbody></table></div>
      <details className="mt-4 rounded-xl bg-white p-4 text-xs"><summary className="cursor-pointer font-semibold">{pt ? "Economia por atividade e premissas anuais" : "Segment economics and annual assumptions"}</summary>{active.projections.map(row => <div key={row.period} className="mt-4 border-t border-slate-100 pt-3"><p className="font-semibold">{row.period}</p><p className="mt-1">E&P: {money(row.oil_drivers!.upstream_ebitda_brl)} · {pt ? "Refino e comercialização" : "Refining and marketing"}: {money(row.oil_drivers!.downstream_ebitda_brl)} · {pt ? "Outros e eliminações" : "Other and eliminations"}: {money(row.oil_drivers!.other_and_eliminations_ebitda_brl)}</p><p className="mt-2 leading-5 text-slate-600">{row.oil_drivers!.rationale}</p></div>)}</details>
    </> : <>
      <div className="mt-5 rounded-xl bg-white p-5"><p className="text-xs text-slate-500">{pt ? "Valor econômico por ação · DCF" : "Economic value per share · DCF"}</p><p className="mt-2 text-3xl font-bold text-sky-900">{money(bridge.present_value, false)}</p><p className="mt-2 text-xs leading-5 text-slate-500">{pt ? "Alocação econômica aproximada entre ações ON e PN; não é uma previsão do preço de cada classe." : "Approximate economic allocation across ON and PN shares; not a forecast of each class's trading price."}</p></div>
      {bridge.residual_negative && <p className="mt-3 rounded-xl bg-amber-50 p-4 text-xs leading-5 text-amber-900">{pt ? "Neste cenário, o DCF não deixa valor residual após a dívida. Zero é o piso do cálculo, não uma previsão de cotação ou falência; o valor de opção do patrimônio não foi modelado." : "This scenario's DCF leaves no residual after debt. Zero is the calculation floor, not a trading-price or bankruptcy forecast; equity option value is not modeled."}</p>}
      <dl className="mt-4 grid gap-3 rounded-xl bg-white p-4 text-xs sm:grid-cols-2">{[
        [pt ? "Valor das operações" : "Enterprise value", money(bridge.enterprise_value)],
        [pt ? "Dívida bruta com arrendamentos" : "Gross debt including leases", money(bridge.gross_debt)],
        [pt ? "Caixa e equivalentes" : "Cash and equivalents", money(bridge.cash)],
        [pt ? "Aplicações financeiras" : "Marketable securities", money(bridge.marketable_securities)],
        [pt ? "Dívida líquida com arrendamentos" : "Net debt including leases", money(bridge.net_debt)],
        [pt ? "Não controladores" : "Noncontrolling interests", money(bridge.noncontrolling_interests)],
        [pt ? "Valor dos acionistas" : "Equity value", money(bridge.equity_value)],
        [pt ? "Ações ON + PN em circulação" : "Outstanding ON + PN shares", number(bridge.shares)],
        [pt ? "Verificação EV/EBITDA" : "EV/EBITDA cross-check", money(active.methods.find(m => m.method === "ev_ebitda")!.present_value, false)],
      ].map(([label, value]) => <div key={label}><dt className="leading-5 text-slate-500">{label}</dt><dd className="mt-1 font-semibold">{value}</dd></div>)}</dl>
      <p className="mt-3 text-xs text-slate-500">WACC: {number(active.assumptions.discount_percent)}% · {pt ? "Crescimento terminal" : "Terminal growth"}: {number(active.assumptions.perpetual_growth_percent)}% · {pt ? "Peso da perpetuidade no valor operacional" : "Terminal share of enterprise value"}: {number(active.terminal_value_share_percent!)}%</p>
      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white"><table className="w-full text-left text-xs"><caption className="px-3 py-3 text-left font-semibold">{pt ? "Sensibilidade do DCF" : "DCF sensitivity"}</caption><thead><tr>{["WACC", pt ? "Crescimento terminal" : "Terminal growth", pt ? "Valor por ação" : "Per-share value"].map(label => <th className="px-3 py-2" key={label}>{label}</th>)}</tr></thead><tbody>{active.sensitivity?.map((s, i) => <tr key={i} className="border-t border-slate-100"><td className="px-3 py-2">{number(s.wacc_percent)}%</td><td className="px-3 py-2">{number(s.growth_percent)}%</td><td className="px-3 py-2 font-semibold">{money(s.value, false)}</td></tr>)}</tbody></table></div>
    </>}
    <details className="mt-4 rounded-xl bg-white p-4 text-xs leading-5 text-slate-600"><summary className="cursor-pointer font-semibold">{pt ? "Reinvestimento, arrendamentos e convenções" : "Reinvestment, leases and conventions"}</summary><p className="mt-3">{model.oil_inputs!.bridge.lease_treatment}</p><p className="mt-3">{model.oil_inputs!.scenarios.find(c => c.case === active.case)?.terminal_reinvestment_rationale}</p><p className="mt-3">{pt ? "Cinco exercícios completos após o ano da pesquisa; o restante do ano corrente não entra no DCF. Estrutura de capital observada mantida na ponte; patrimônio de minoritários usado como aproximação. FCFF não representa dividendos disponíveis." : "Five full fiscal years after the research year; remaining current-year cash is omitted. The equity bridge holds observed capital structure constant and uses book NCI as a proxy. FCFF is not distributable dividends."}</p></details>
  </div>;
}
