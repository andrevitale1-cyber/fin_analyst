"use client";

import type { InvestmentModel, ModelMethod } from "../lib/investmentModel";
import { formatReportMoney, formatReportNumber } from "../lib/reportNumbers";
import FinancialChart from "./ReportFinancialChart";
import OilModelPanel from "./OilModelPanel";

type Props = { model: InvestmentModel; locale: string; mode: "forecast" | "valuation"; selectedCase: string; onCaseChange: (name: string) => void };

export default function OperatingModelPanel({ model, locale, mode, selectedCase, onCaseChange }: Props) {
  if (model.oil_inputs) return <OilModelPanel model={model} locale={locale} mode={mode} selectedCase={selectedCase} onCaseChange={onCaseChange} />;
  const pt = locale.startsWith("pt");
  const active = model.cases.find(item => item.case === selectedCase) || model.cases[1];
  if (!active) return null;
  const names = { bear: pt ? "Pessimista" : "Bear", base: pt ? "Base" : "Base", bull: pt ? "Otimista" : "Bull" };
  const methods: Record<ModelMethod, string> = { pe: pt ? "P/L projetado" : "Projected P/E", normalized_pe: pt ? "P/L normalizado" : "Normalized P/E",
    dcf: pt ? "Fluxo de caixa descontado" : "Discounted cash flow", ev_ebitda: "EV/EBITDA", price_to_book: pt ? "Preço / patrimônio" : "Price / book" };
  const money = (value: number | null, compact = true) => formatReportMoney(value, model.baseline.currency, locale, compact);
  const percent = (value: number) => `${formatReportNumber(value, locale, false)}%`;
  const selectedPrice = active.methods.find(item => item.method === model.selected_method);
  const assumptions = active.assumptions;
  return <div className="mt-6 min-w-0 rounded-2xl border border-sky-100 bg-sky-50/30 p-4 sm:p-5">
    <div className="flex flex-wrap items-center justify-between gap-3"><p className="text-xs font-bold uppercase tracking-wide text-sky-800">{pt ? "Modelo de cenários" : "Scenario model"}</p><span className="rounded-full bg-white px-3 py-1 text-[10px] font-semibold text-slate-600">{pt ? "Premissas da IA · não é consenso" : "AI assumptions · not consensus"}</span></div>
    <div aria-label={pt ? "Escolher cenário" : "Choose scenario"} className="mt-4 grid grid-cols-3 gap-2">{model.cases.map(item => <button key={item.case} type="button" aria-pressed={item.case === active.case} onClick={() => onCaseChange(item.case)} className={`min-h-11 rounded-xl border px-2 py-3 text-xs font-semibold transition ${item.case === active.case ? "border-sky-400 bg-white text-sky-900 shadow-sm" : "border-slate-200 bg-white/60 text-slate-600 hover:border-sky-200"}`}>{names[item.case]}</button>)}</div>
    {mode === "forecast" ? <>
      <p className="mt-4 text-xs leading-5 text-slate-600">{model.assumptions.capacity_driver}: <strong>{percent(assumptions.capacity_growth_percent)}</strong> · {model.assumptions.productivity_driver}: <strong>{percent(assumptions.productivity_growth_percent)}</strong></p>
      <FinancialChart rows={active.projections.map(row => ({...row, free_cash_flow: null, source_id: model.baseline.source_id}))} field="revenue" title={pt ? "Receita projetada · hipótese da IA" : "Projected revenue · AI assumption"} locale={locale} />
      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white"><table className="w-full min-w-[520px] text-left text-xs"><caption className="sr-only">{pt ? "Projeções condicionais da IA" : "Conditional AI projections"}</caption><thead className="bg-slate-50 text-slate-500"><tr>{[pt ? "Exercício" : "Fiscal year", pt ? "Receita" : "Revenue", pt ? "Lucro líquido" : "Net income", "EPS", "FCFF"].map(label => <th key={label} className="px-3 py-3">{label}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{active.projections.map(row => <tr key={row.period}><th className="px-3 py-3 font-medium">{row.period}</th><td className="px-3">{money(row.revenue)}</td><td className="px-3">{money(row.net_income)}</td><td className="px-3">{money(row.eps, false)}</td><td className="px-3">{money(row.fcff)}</td></tr>)}</tbody></table></div>
      <p className="mt-3 text-[11px] leading-5 text-slate-500">{pt ? "FCFF é o fluxo de caixa livre da firma calculado pelo modelo. Base realizada: " : "FCFF is the model's calculated free cash flow to the firm. Reported baseline: "}{model.baseline.period}. {pt ? "Cinco exercícios projetados, separados dos resultados realizados e das projeções divulgadas pela empresa." : "Five projected fiscal periods, separated from reported actuals and company guidance."}</p>
    </> : <>
      {selectedPrice && <div className="mt-5 rounded-xl bg-white p-5"><p className="text-[10px] font-bold uppercase text-slate-400">{pt ? "Valor estimado por ação · valor presente" : "Estimated per-share value · present value"}</p><p className="mt-2 text-3xl font-bold tracking-tight text-sky-900">{money(selectedPrice.present_value, false)}</p><p className="mt-2 text-xs text-slate-500">{methods[selectedPrice.method]}</p></div>}
      {active.methods.length > 0 && <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white"><table className="w-full min-w-[340px] text-left text-xs"><caption className="sr-only">{pt ? "Comparação de métodos de valuation" : "Valuation method comparison"}</caption><thead className="bg-slate-50 text-slate-500"><tr><th className="px-4 py-3">{pt ? "Método" : "Method"}</th><th className="px-4 py-3">{pt ? "Valor por ação" : "Per-share value"}</th></tr></thead><tbody className="divide-y divide-slate-100">{active.methods.map(method => <tr key={method.method}><th className="px-4 py-3 font-medium">{methods[method.method]}</th><td className="px-4 py-3 font-semibold">{money(method.present_value, false)}</td></tr>)}</tbody></table></div>}
      {active.methods.length > 1 && <p className="mt-3 text-[11px] leading-5 text-slate-500">{pt ? "Os métodos têm premissas diferentes. A comparação é uma checagem de sensibilidade, não uma garantia de concordância." : "Methods use different assumptions. This comparison is a sensitivity cross-check, not a guarantee of agreement."}</p>}
    </>}
    <details className="mt-5 rounded-xl border border-slate-200 bg-white"><summary className="cursor-pointer px-4 py-3 text-xs font-semibold text-slate-700">{pt ? "Premissas e limites do modelo" : "Model assumptions and limits"}</summary><div className="px-4 pb-4"><p className="text-xs leading-5 text-slate-600">{assumptions.rationale}</p><dl className="mt-4 grid grid-cols-2 gap-4 text-xs">{[
      [pt ? "Margem líquida terminal" : "Terminal net margin", percent(assumptions.terminal_net_margin_percent)],
      [pt ? "Margem EBIT terminal" : "Terminal EBIT margin", percent(assumptions.terminal_operating_margin_percent)],
      [pt ? "Capex / receita" : "Capex / revenue", percent(assumptions.capex_percent)], ["WACC", percent(assumptions.discount_percent)],
      [pt ? "Custo de capital próprio" : "Cost of equity", percent(assumptions.equity_discount_percent)],
      [pt ? "Crescimento perpetuidade" : "Perpetual growth", percent(assumptions.perpetual_growth_percent)], ["P/E · EV/EBITDA", `${assumptions.terminal_pe}× · ${assumptions.terminal_ev_ebitda}×`],
    ].map(([label, value]) => <div key={label}><dt className="text-slate-400">{label}</dt><dd className="mt-1 font-semibold text-slate-800">{value}</dd></div>)}</dl><p className="mt-4 text-[11px] leading-5 text-slate-500">{pt ? "Ações e dívida líquida constantes; margens em transição linear. Desconto pela distância entre a data da pesquisa e o fim de cada exercício." : "Constant shares and net debt; linear margin transitions. Discounting uses the time from the research date to each fiscal period end."}</p>{model.baseline.share_basis?.startsWith("calculated_") && <p className="mt-2 text-[11px] leading-5 text-slate-500">{pt ? "Quantidade diluída de ações aproximada a partir do lucro atribuível e EPS reportados; sujeita ao arredondamento do EPS." : "Diluted share count approximated from reported attributable profit and EPS; subject to EPS rounding."}</p>}</div></details>
  </div>;
}
