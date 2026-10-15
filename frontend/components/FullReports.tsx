"use client";

import { useAuth, UserButton } from "@clerk/nextjs";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { type FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlertCircle, ArrowLeft, ArrowRight, BookOpen, Building2, CalendarDays, ChevronRight, Loader2, Search, Sparkles, TrendingUp } from "lucide-react";
import LanguageSwitcher from "./LanguageSwitcher";
import { splitBold } from "../lib/analysisText";
import { calculateIllustrativeValue, type ValuationInputs } from "../lib/fullReportValuation";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "https://api-finanalyzer.onrender.com";
const SECTION_IDS = ["thesis", "business", "financials", "moat", "management", "risks", "valuation"] as const;
const COMPANY_SECTION_IDS = ["thesis", "business", "financials", "moat", "management", "sentiment", "outlook", "risks", "valuation", "verdict"] as const;
const POPULAR_COMPANIES = [
  { name: "Microsoft", ticker: "MSFT" }, { name: "NVIDIA", ticker: "NVDA" }, { name: "Google", ticker: "GOOGL" },
  { name: "Meta", ticker: "META" }, { name: "Amazon", ticker: "AMZN" }, { name: "Micron", ticker: "MU" },
  { name: "AMD", ticker: "AMD" }, { name: "ServiceNow", ticker: "NOW" },
];
type SectionId = typeof SECTION_IDS[number];
type CompanySectionId = typeof COMPANY_SECTION_IDS[number];
type FullReportSection = { id: SectionId | CompanySectionId; title: string; summary: string; paragraphs: string[]; bullets: string[]; source_ids: string[] };
type FullReport = {
  id: string; company: string; company_name?: string | null; symbol?: string | null; period: string; scope?: "company" | "period"; as_of?: string | null; locale: "en" | "pt"; kind: "report" | "transcript" | "company"; created_at: string; score: number | null; is_public?: boolean;
  coverage: string; sections: FullReportSection[]; metrics: { label: string; value: string; group?: "scale" | "performance" | "valuation"; as_of?: string | null; source_id: string }[];
  signals?: { id: string; label: string; value: string; tone: "positive" | "neutral" | "negative" | "unknown"; source_ids: string[] }[];
  scorecard?: { id: string; label: string; score: number | null; reason: string; source_ids: string[] }[];
  tracking_metrics?: { label: string; expectation: string; status: string; source_ids: string[] }[];
  breakdowns?: { category: "segment" | "geography"; label: string; value: string; share: number | null; source_id: string }[];
  financial_history?: { period: string; currency: string | null; revenue: number | null; net_income: number | null; free_cash_flow: number | null; source_id: string }[];
  projections?: { period: string; currency: string | null; revenue: number | null; eps: number | null; basis: "management_guidance" | "analyst_consensus"; source_id: string }[];
  market?: { price: number | null; change_percent: number | null; currency: string | null; as_of: string | null; source_id: string | null };
  watchpoints: string[]; sources: { id: string; title: string; url: string | null }[];
  valuation: { available: boolean; base_eps: number | null; currency: string | null; source_id: string | null; reason: string; method?: string | null; fair_value?: number | null; scenarios?: { case: "bear" | "base" | "bull"; growth_percent: number; pe_multiple: number; discount_percent: number; rationale: string; future_value: number | null; present_value: number | null; upside_percent: number | null }[] };
};
type ReportSummary = Pick<FullReport, "id" | "company" | "company_name" | "symbol" | "period" | "scope" | "as_of" | "locale" | "kind" | "created_at" | "score" | "is_public">;
type RouteTarget = { type: "library" } | { type: "generate"; analysisId: string } | { type: "company"; company: string } | { type: "saved"; reportId: string };
const SCENARIOS: { key: "bear" | "base" | "bull"; growthPercent: number; peMultiple: number; discountPercent: number }[] = [
  { key: "bear", growthPercent: 0, peMultiple: 12, discountPercent: 12 },
  { key: "base", growthPercent: 10, peMultiple: 15, discountPercent: 10 },
  { key: "bull", growthPercent: 20, peMultiple: 20, discountPercent: 8 },
];

function reportText(text: string) {
  return splitBold(text).map((part, index) => part.bold ? <strong key={index} className="font-semibold text-slate-900">{part.text}</strong> : part.text);
}

function formatReportDate(value: string, locale: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium", ...(/^\d{4}-\d{2}-\d{2}$/.test(value) ? { timeZone: "UTC" } : {}),
  }).format(parsed);
}

function companyLogoPath(symbol: string) {
  const asset = symbol === "GOOGL" ? "GOOG" : symbol;
  return `/benefits/company-logos/${encodeURIComponent(asset)}.${symbol === "NOW" ? "png" : "webp"}`;
}

function CompanyLogo({ symbol, company }: { symbol?: string | null; company: string }) {
  const [failed, setFailed] = useState(false);
  const safeSymbol = symbol && /^[A-Za-z0-9.-]+$/.test(symbol) ? symbol : null;
  return safeSymbol && !failed
    ? <img src={companyLogoPath(safeSymbol)} alt="" width={48} height={48} onError={() => setFailed(true)} className="h-12 w-12 rounded-xl object-contain" />
    : <div aria-label={company} className="flex h-12 w-12 items-center justify-center rounded-xl bg-sky-50 text-sky-800"><Building2 size={22} /></div>;
}

type CompanyTranslate = (key: string, values?: Record<string, string | number>) => string;

function CompanyReportReader({ report, locale, t, onDashboard, onBack }: { report: FullReport; locale: string; t: CompanyTranslate; onDashboard: () => void; onBack: () => void }) {
  const sectionById = new Map(report.sections.map(section => [section.id, section]));
  const sourceById = new Map(report.sources.map(source => [source.id, source]));
  const date = (value?: string | null) => value ? formatReportDate(value, locale) : "";
  const sourceLink = (id?: string | null) => {
    if (!id) return null;
    const source = sourceById.get(id);
    return source ? <a href={`#source-${encodeURIComponent(id)}`} title={source.title} aria-label={`${t("sources")}: ${source.title}`} className="ml-2 inline-flex align-middle text-xs font-semibold text-sky-800 underline decoration-sky-200 underline-offset-2 hover:text-sky-950">[{report.sources.indexOf(source) + 1}]</a> : null;
  };
  const sectionBody = (id: CompanySectionId) => {
    const section = sectionById.get(id);
    if (!section) return <p className="mt-3 text-sm text-slate-500">{t("companyNoSection")}</p>;
    return <div className="mt-4"><p className="text-base leading-7 text-slate-700">{reportText(section.summary)}</p>{section.paragraphs.length > 0 && <div className="mt-4 space-y-4 font-serif text-[16px] leading-8 text-slate-700">{section.paragraphs.map((paragraph, index) => <p key={index}>{reportText(paragraph)}</p>)}</div>}{section.bullets.length > 0 && <ul className="mt-5 space-y-3">{section.bullets.map((bullet, index) => <li key={index} className="flex gap-3 text-sm leading-6 text-slate-700"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-sky-600" /><span>{reportText(bullet)}</span></li>)}</ul>}{section.source_ids.length > 0 && <p className="mt-4">{section.source_ids.map(sourceLink)}</p>}</div>;
  };
  const sectionTitle = (id: CompanySectionId) => sectionById.get(id)?.title || t(`companySections.${id}`);
  const groupLabels = ["scale", "performance", "valuation"] as const;
  const groupedMetrics = groupLabels.map(group => ({ group, items: (report.metrics || []).filter(metric => metric.group === group) })).filter(item => item.items.length > 0);
  const history = report.financial_history || [];
  const maxRevenue = new Set(history.map(item => item.currency)).size === 1 ? Math.max(0, ...history.map(item => item.revenue || 0)) : 0;
  const breakdowns = report.breakdowns || [];
  const market = report.market;
  const valuationScenarios = report.valuation.scenarios || [];
  const signals = report.signals || [];
  const scorecard = report.scorecard || [];
  const companyName = report.company_name || report.company;
  const ticker = report.company && report.company !== companyName ? report.company : "";
  const money = (value: number | null | undefined, currency?: string | null) => value === null || value === undefined ? "—" : `${currency ? `${currency} ` : ""}${new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(value)}`;
  const tone = (value: string) => value === "positive" ? "border-emerald-100 bg-emerald-50 text-emerald-800" : value === "negative" ? "border-rose-100 bg-rose-50 text-rose-800" : value === "neutral" ? "border-slate-200 bg-slate-50 text-slate-700" : "border-amber-100 bg-amber-50 text-amber-800";
  const scoreTone = (score: number | null) => score === null ? "bg-slate-100 text-slate-500" : score >= 4 ? "bg-emerald-50 text-emerald-800" : score <= 2 ? "bg-rose-50 text-rose-800" : "bg-amber-50 text-amber-800";

  return <article className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-100 px-5 py-3 md:px-8"><button onClick={onBack} className="inline-flex items-center gap-2 rounded-lg px-2 py-2 text-sm font-semibold text-sky-800 hover:bg-sky-50"><ArrowLeft size={16} />{t("backToGallery")}</button></div>
    <header className="bg-[#0c1e35] px-5 py-8 text-white [&_a]:text-sky-200 md:px-10 md:py-11">
      <div className="flex flex-col justify-between gap-6 md:flex-row md:items-center"><div className="flex min-w-0 items-center gap-4"><img src={companyLogoPath(report.symbol || report.company)} alt="" width={64} height={64} onError={event => { event.currentTarget.style.display = "none"; }} className="h-14 w-14 shrink-0 rounded-2xl bg-white p-2 object-contain" /><div><p className="text-xs font-bold uppercase tracking-[.18em] text-sky-200">{t("companyOverview")}</p><h1 className="mt-1 text-3xl font-bold tracking-tight md:text-5xl">{companyName}</h1><div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-slate-300">{ticker && <span>{ticker}</span>}{report.as_of && <span>{t("companyAsOf", { date: date(report.as_of) })}</span>}</div></div></div>
        <div className="flex flex-wrap items-center gap-3">{market?.price !== null && market?.price !== undefined && <div className="rounded-2xl border border-white/15 bg-white/5 px-4 py-3"><p className="text-xs uppercase tracking-wide text-slate-300">{t("marketPrice")}</p><p className="mt-1 text-xl font-bold">{money(market.price, market.currency)}</p>{market.change_percent !== null && <p className={`text-xs ${market.change_percent >= 0 ? "text-emerald-300" : "text-rose-300"}`}>{market.change_percent > 0 ? "+" : ""}{market.change_percent}%</p>}</div>}{report.score !== null && <div className="rounded-2xl border border-white/15 bg-white/5 px-4 py-3"><p className="text-xs uppercase tracking-wide text-slate-300">{t("qualityScore")}</p><p className="mt-1 text-2xl font-bold">{report.score}<span className="text-sm font-medium text-slate-300"> / 5</span></p></div>}</div></div>
      <p className="mt-6 max-w-4xl text-sm leading-6 text-slate-300">{report.coverage}</p>{market?.source_id && <p className="mt-2 text-xs text-slate-400">{t("marketAsOf", { date: date(market.as_of) })}{sourceLink(market.source_id)}</p>}
    </header>

    {signals.length > 0 && <section className="grid grid-cols-2 gap-px border-b border-slate-100 bg-slate-100 md:grid-cols-3 xl:grid-cols-6">{signals.slice(0, 6).map(signal => <div key={signal.id} className="bg-white p-4 md:p-5"><p className="text-[11px] font-bold uppercase tracking-wide text-slate-500">{signal.label}</p><span className={`mt-2 inline-flex max-w-full rounded-full border px-2.5 py-1 text-xs font-semibold ${tone(signal.tone)}`}>{signal.value}</span><p className="mt-2">{signal.source_ids.map(sourceLink)}</p></div>)}</section>}

    <div className="grid lg:grid-cols-[210px_minmax(0,1fr)]"><nav aria-label={t("companyContents")} className="flex gap-1 overflow-x-auto border-b border-slate-100 p-3 lg:sticky lg:top-20 lg:block lg:h-fit lg:border-b-0 lg:border-r lg:p-4">{COMPANY_SECTION_IDS.map(id => <a key={id} href={`#company-section-${id}`} className="whitespace-nowrap rounded-lg px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-sky-50 hover:text-sky-900 lg:mb-1 lg:block">{t(`companySections.${id}`)}</a>)}</nav>
      <div className="min-w-0 divide-y divide-slate-100">
        <section id="company-section-thesis" className="scroll-mt-24 p-6 md:p-9"><p className="text-xs font-bold uppercase tracking-[.15em] text-sky-800">{t("companySections.thesis")}</p><h2 className="mt-2 font-serif text-2xl font-bold tracking-tight text-slate-950 md:text-3xl">{sectionTitle("thesis")}</h2><div className="mt-5 rounded-2xl border-l-4 border-sky-500 bg-sky-50/70 p-5 font-serif text-lg leading-8 text-slate-800">{sectionBody("thesis")}</div></section>
        <section className="p-6 md:p-9">{(report.tracking_metrics || []).length > 0 && <div className="mt-8 overflow-x-auto rounded-2xl border border-slate-200"><table className="w-full min-w-[540px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-4 py-3">{t("trackingMetrics")}</th><th className="px-4 py-3">{t("expectation")}</th><th className="px-4 py-3">{t("status")}</th></tr></thead><tbody className="divide-y divide-slate-100">{report.tracking_metrics!.map((item, index) => <tr key={`${item.label}-${index}`}><th className="px-4 py-3 font-semibold">{item.label}{item.source_ids.map(sourceLink)}</th><td className="px-4 py-3">{item.expectation}</td><td className="px-4 py-3">{item.status}</td></tr>)}</tbody></table></div>}{scorecard.length > 0 && <div className="mt-8 rounded-2xl border border-slate-200 p-5"><h3 className="font-bold">{t("qualityScorecard")}</h3><ul className="mt-4 divide-y divide-slate-100">{scorecard.map(item => <li key={item.id} className="flex flex-wrap items-center gap-3 py-3"><span className={`min-w-12 rounded-full px-3 py-1 text-center text-sm font-bold ${scoreTone(item.score)}`}>{item.score ?? "—"}/5</span><span className="font-semibold">{item.label}</span><span className="min-w-0 flex-1 text-sm text-slate-600">{item.reason}</span>{item.source_ids.map(sourceLink)}</li>)}</ul></div>}</section>
        {groupedMetrics.length > 0 && <section className="p-6 md:p-9"><h2 className="font-serif text-2xl font-bold text-slate-950">{t("numbersAtGlance")}</h2>{groupedMetrics.length > 0 && <div className="mt-7 grid gap-4 md:grid-cols-3">{groupedMetrics.map(({ group, items }) => <div key={group} className="rounded-2xl bg-slate-50 p-4"><h3 className="text-xs font-bold uppercase tracking-wide text-slate-500">{t(`metricGroups.${group}`)}</h3><dl className="mt-3 space-y-3">{items.map((metric, index) => <div key={`${metric.label}-${index}`}><dt className="text-xs text-slate-500">{metric.label}{metric.as_of && ` · ${date(metric.as_of)}`}</dt><dd className="mt-1 font-bold text-slate-900">{reportText(metric.value)}{sourceLink(metric.source_id)}</dd></div>)}</dl></div>)}</div>}</section>}
        <section id="company-section-business" className="scroll-mt-24 p-6 md:p-9"><p className="text-xs font-bold uppercase tracking-[.15em] text-sky-800">{t("companySections.business")}</p><h2 className="mt-2 font-serif text-2xl font-bold text-slate-950">{sectionTitle("business")}</h2>{sectionBody("business")}{breakdowns.length > 0 && <div className="mt-8 grid gap-6 xl:grid-cols-2">{(["segment", "geography"] as const).map(category => { const items = breakdowns.filter(item => item.category === category); return items.length ? <div key={category} className="rounded-2xl border border-slate-200 p-5"><h3 className="font-bold">{t(category === "segment" ? "segments" : "geography")}</h3>{items.some(item => item.share !== null) && <div className="mx-auto mt-5 flex h-36 w-36 items-center justify-center rounded-full" style={{ background: `conic-gradient(${items.map((item, index) => { const value = Math.max(0, Math.min(100, item.share || 0)); const previous = items.slice(0, index).reduce((sum, row) => sum + Math.max(0, Math.min(100, row.share || 0)), 0); const colors = ["#0284c7", "#38bdf8", "#7dd3fc", "#0f766e", "#34d399", "#64748b"]; return `${colors[index % colors.length]} ${previous}% ${previous + value}%`; }).join(", ")})` }}><div className="flex h-20 w-20 items-center justify-center rounded-full bg-white text-center text-xs font-semibold text-slate-500">{t("reportedMix")}</div></div>}<ul className="mt-4 space-y-2">{items.map((item, index) => <li key={`${item.label}-${index}`} className="flex items-start justify-between gap-3 border-b border-slate-100 pb-2 text-sm"><span>{item.label}</span><span className="text-right font-semibold">{item.value}{item.share !== null ? ` · ${item.share}%` : ""}{sourceLink(item.source_id)}</span></li>)}</ul></div> : null; })}</div>}</section>
        <section id="company-section-financials" className="scroll-mt-24 p-6 md:p-9"><p className="text-xs font-bold uppercase tracking-[.15em] text-sky-800">{t("companySections.financials")}</p><h2 className="mt-2 font-serif text-2xl font-bold text-slate-950">{sectionTitle("financials")}</h2>{sectionBody("financials")}{history.length > 0 && <div className="mt-8 overflow-hidden rounded-2xl border border-slate-200"><div className="border-b border-slate-100 px-4 py-3"><h3 className="font-bold">{t("financialHistory")}</h3><p className="text-xs text-slate-500">{t("historyChartNote")}</p></div><div className="overflow-x-auto"><table className="w-full min-w-[640px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-4 py-3">{t("period")}</th><th className="px-4 py-3">{t("revenue")}</th><th className="px-4 py-3">{t("netIncome")}</th><th className="px-4 py-3">{t("freeCashFlow")}</th><th className="px-4 py-3">{t("sources")}</th></tr></thead><tbody className="divide-y divide-slate-100">{history.map((row, index) => <tr key={`${row.period}-${index}`}><th className="px-4 py-3 font-semibold">{row.period}</th><td className="px-4 py-3"><div>{money(row.revenue, row.currency)}</div>{row.revenue !== null && maxRevenue > 0 && <div className="mt-1 h-1.5 w-full max-w-32 rounded bg-slate-100"><div className="h-1.5 rounded bg-sky-500" style={{ width: `${Math.max(0, Math.min(100, row.revenue / maxRevenue * 100))}%` }} /></div>}</td><td className="px-4 py-3">{money(row.net_income, row.currency)}</td><td className="px-4 py-3">{money(row.free_cash_flow, row.currency)}</td><td className="px-4 py-3">{sourceLink(row.source_id)}</td></tr>)}</tbody></table></div></div>}</section>
        <section id="company-section-moat" className="scroll-mt-24 p-6 md:p-9"><p className="text-xs font-bold uppercase tracking-[.15em] text-sky-800">{t("companySections.moat")}</p><h2 className="mt-2 font-serif text-2xl font-bold text-slate-950">{sectionTitle("moat")}</h2>{sectionBody("moat")}</section>
        <section id="company-section-management" className="scroll-mt-24 p-6 md:p-9"><p className="text-xs font-bold uppercase tracking-[.15em] text-sky-800">{t("companySections.management")}</p><h2 className="mt-2 font-serif text-2xl font-bold text-slate-950">{sectionTitle("management")}</h2>{sectionBody("management")}</section>
        <section id="company-section-sentiment" className="scroll-mt-24 p-6 md:p-9"><p className="text-xs font-bold uppercase tracking-[.15em] text-sky-800">{t("companySections.sentiment")}</p><h2 className="mt-2 font-serif text-2xl font-bold text-slate-950">{sectionTitle("sentiment")}</h2>{sectionBody("sentiment")}{market && <div className="mt-5 grid gap-3 sm:grid-cols-2">{market.price !== null && <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs uppercase text-slate-500">{t("marketPrice")}</p><p className="mt-2 text-xl font-bold">{money(market.price, market.currency)}</p><p className="mt-1 text-xs text-slate-500">{date(market.as_of)}{sourceLink(market.source_id)}</p></div>}{market.change_percent !== null && <div className="rounded-xl bg-slate-50 p-4"><p className="text-xs uppercase text-slate-500">{t("marketChange")}</p><p className="mt-2 text-xl font-bold">{market.change_percent > 0 ? "+" : ""}{market.change_percent}%</p><p className="mt-1 text-xs text-slate-500">{date(market.as_of)}{sourceLink(market.source_id)}</p></div>}</div>}</section>
        <section id="company-section-outlook" className="scroll-mt-24 p-6 md:p-9"><p className="text-xs font-bold uppercase tracking-[.15em] text-sky-800">{t("companySections.outlook")}</p><h2 className="mt-2 font-serif text-2xl font-bold text-slate-950">{sectionTitle("outlook")}</h2>{sectionBody("outlook")}{(report.projections || []).length > 0 && <div className="mt-7 overflow-x-auto rounded-2xl border border-slate-200"><table className="w-full min-w-[560px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="px-4 py-3">{t("period")}</th><th className="px-4 py-3">{t("revenue")}</th><th className="px-4 py-3">EPS</th><th className="px-4 py-3">{t("basis")}</th><th className="px-4 py-3">{t("sources")}</th></tr></thead><tbody className="divide-y divide-slate-100">{report.projections!.map((row, index) => <tr key={`${row.period}-${index}`}><th className="px-4 py-3 font-semibold">{row.period}</th><td className="px-4 py-3">{money(row.revenue, row.currency)}</td><td className="px-4 py-3">{money(row.eps, row.currency)}</td><td className="px-4 py-3">{t(row.basis === "management_guidance" ? "managementGuidance" : "analystConsensus")}</td><td className="px-4 py-3">{sourceLink(row.source_id)}</td></tr>)}</tbody></table></div>}</section>
        <section id="company-section-risks" className="scroll-mt-24 p-6 md:p-9"><p className="text-xs font-bold uppercase tracking-[.15em] text-sky-800">{t("companySections.risks")}</p><h2 className="mt-2 font-serif text-2xl font-bold text-slate-950">{sectionTitle("risks")}</h2>{sectionBody("risks")}{report.watchpoints.length > 0 && <ul className="mt-6 space-y-3 rounded-2xl border border-amber-100 bg-amber-50/50 p-5">{report.watchpoints.map((item, index) => <li key={index} className="flex gap-3 text-sm leading-6 text-slate-700"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />{reportText(item)}</li>)}</ul>}</section>
        <section id="company-section-valuation" className="scroll-mt-24 p-6 md:p-9"><p className="text-xs font-bold uppercase tracking-[.15em] text-sky-800">{t("companySections.valuation")}</p><h2 className="mt-2 font-serif text-2xl font-bold text-slate-950">{sectionTitle("valuation")}</h2>{sectionBody("valuation")}<p className="mt-4 text-sm leading-6 text-slate-500">{report.valuation.available ? t("companyScenarioNote") : report.valuation.reason || t("valuationUnavailable")}</p>{report.valuation.fair_value !== null && report.valuation.fair_value !== undefined && <p className="mt-5 rounded-xl bg-sky-50 p-4 text-sm text-slate-700">{t("fairValue")}: <strong>{money(report.valuation.fair_value, report.valuation.currency)}</strong>{report.valuation.source_id && sourceLink(report.valuation.source_id)}</p>}{valuationScenarios.length > 0 && <div className="mt-7 grid gap-4 md:grid-cols-3">{valuationScenarios.map(item => <div key={item.case} className="rounded-2xl border border-slate-200 p-5"><h3 className="font-bold capitalize">{t(`scenarios.${item.case}`)}</h3><p className="mt-1 text-xs text-slate-500">{item.rationale}</p><dl className="mt-4 space-y-2 text-sm"><div className="flex justify-between gap-3"><dt>{t("futureValue")}</dt><dd className="font-semibold">{money(item.future_value, report.valuation.currency)}</dd></div><div className="flex justify-between gap-3"><dt>{t("presentValue")}</dt><dd className="font-semibold">{money(item.present_value, report.valuation.currency)}</dd></div><div className="flex justify-between gap-3"><dt>{t("growthAssumption")}</dt><dd>{item.growth_percent}%</dd></div><div className="flex justify-between gap-3"><dt>P/E</dt><dd>{item.pe_multiple}</dd></div><div className="flex justify-between gap-3"><dt>{t("discountAssumption")}</dt><dd>{item.discount_percent}%</dd></div></dl>{report.valuation.source_id && <p className="mt-3">{sourceLink(report.valuation.source_id)}</p>}</div>)}</div>}</section>
        <section id="company-section-verdict" className="scroll-mt-24 p-6 md:p-9"><p className="text-xs font-bold uppercase tracking-[.15em] text-sky-800">{t("companySections.verdict")}</p><h2 className="mt-2 font-serif text-2xl font-bold text-slate-950">{sectionTitle("verdict")}</h2>{sectionBody("verdict")}</section>
        <section className="p-6 md:p-9"><h2 className="font-serif text-2xl font-bold text-slate-950">{t("sources")}</h2><ol className="mt-5 grid gap-3 md:grid-cols-2">{report.sources.map((source, index) => <li id={`source-${encodeURIComponent(source.id)}`} key={source.id} className="scroll-mt-28 rounded-xl border border-slate-200 bg-slate-50 p-4"><span className="mr-2 text-xs font-bold text-sky-800">[{index + 1}]</span>{source.url && /^https?:\/\//i.test(source.url) ? <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold text-slate-800 underline decoration-slate-300 underline-offset-4 hover:text-sky-800">{source.title}</a> : <span className="text-sm font-semibold text-slate-800">{source.title}</span>}</li>)}</ol><button onClick={onDashboard} className="mt-8 inline-flex items-center gap-2 rounded-xl bg-sky-700 px-5 py-3 text-sm font-bold text-white hover:bg-sky-800"><TrendingUp size={17} />{t("analyzeSpecificResult")}</button></section>
      </div>
    </div>
  </article>;
}

export default function FullReports() {
  const { getToken, userId, isLoaded } = useAuth();
  const locale = useLocale();
  const t = useTranslations("FullReports");
  const router = useRouter();
  const [routeReady, setRouteReady] = useState(false);
  const [target, setTarget] = useState<RouteTarget>({ type: "library" });
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [report, setReport] = useState<FullReport | null>(null);
  const [libraryOwnerId, setLibraryOwnerId] = useState<string | null>(null);
  const [reportOwnerId, setReportOwnerId] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<SectionId>("thesis");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reused, setReused] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [scenarioInputs, setScenarioInputs] = useState<Record<"bear" | "base" | "bull", ValuationInputs>>(() => Object.fromEntries(SCENARIOS.map(({ key, ...values }) => [key, values])) as Record<"bear" | "base" | "bull", ValuationInputs>);
  const requestRef = useRef<AbortController | null>(null);
  const generationRef = useRef(new Map<string, Promise<{ report: FullReport; reused: boolean }>>());
  const sequenceRef = useRef(0);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const analysisId = params.get("analysisId") || "";
    const reportId = params.get("reportId") || "";
    const company = params.get("company")?.trim() || "";
    setQuery(company);
    setTarget(company ? { type: "company", company } : analysisId ? { type: "generate", analysisId } : reportId ? { type: "saved", reportId } : { type: "library" });
    setRouteReady(true);
  }, []);

  const authorizedFetch = useCallback(async (path: string, init: RequestInit = {}, timeoutMs = 180_000) => {
    const token = await getToken();
    if (!token) throw new Error(t("authError"));
    const headers = new Headers(init.headers);
    headers.set("Authorization", `Bearer ${token}`);
    if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    const controller = new AbortController();
    const cancel = () => controller.abort();
    init.signal?.addEventListener("abort", cancel, { once: true });
    if (init.signal?.aborted) controller.abort();
    let timedOut = false;
    const timeout = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
    try {
      return await fetch(`${API_BASE}${path}`, { ...init, headers, signal: controller.signal });
    } catch (cause) {
      if (timedOut) throw new Error(t("requestTimeout"));
      throw cause;
    } finally {
      clearTimeout(timeout);
      init.signal?.removeEventListener("abort", cancel);
    }
  }, [getToken, t]);

  const readJson = useCallback(async <T,>(response: Response): Promise<T> => {
    if (!response.ok) {
      let detail = "";
      try { detail = (await response.json()).detail || ""; } catch { /* response may not be JSON */ }
      throw new Error(detail || t("requestError", { status: response.status }));
    }
    return response.json() as Promise<T>;
  }, [t]);

  const loadLibrary = useCallback(async (signal: AbortSignal) => {
    const response = await authorizedFetch("/api/full-reports", { signal });
    return readJson<{ reports: ReportSummary[] }>(response);
  }, [authorizedFetch, readJson]);

  const openReport = useCallback(async (id: string, signal: AbortSignal) => {
    const response = await authorizedFetch(`/api/full-reports/${encodeURIComponent(id)}`, { signal });
    return readJson<{ report: FullReport }>(response);
  }, [authorizedFetch, readJson]);

  useEffect(() => {
    if (!routeReady || !isLoaded || !userId) return;
    const sequence = ++sequenceRef.current;
    const controller = new AbortController();
    requestRef.current?.abort();
    requestRef.current = controller;
    setLoading(true);
    setError("");
    setReport(null);
    setReportOwnerId(null);
    setReports([]);
    setLibraryOwnerId(null);
    setReused(false);

    const run = async () => {
      try {
        if (target.type === "generate") {
          if (!/^\d+$/.test(target.analysisId)) throw new Error(t("invalidAnalysis"));
          const key = `${userId}:${target.analysisId}:${locale}`;
          let pending = generationRef.current.get(key);
          if (!pending) {
            pending = (async () => {
              const response = await authorizedFetch("/api/full-reports", {
                method: "POST", body: JSON.stringify({ analysis_id: Number(target.analysisId), locale }),
              });
              return readJson<{ report: FullReport; reused: boolean }>(response);
            })();
            generationRef.current.set(key, pending);
            pending.catch(() => generationRef.current.delete(key));
          }
          const result = await pending;
          if (sequence !== sequenceRef.current) return;
          setReport(result.report);
          setReportOwnerId(userId);
          setReused(result.reused);
          const list = await loadLibrary(controller.signal);
          if (sequence === sequenceRef.current) { setReports(list.reports || []); setLibraryOwnerId(userId); }
        } else if (target.type === "company") {
          const company = target.company.trim();
          if (!company || company.length > 100 || /[\u0000-\u001f]/.test(company)) throw new Error(t("invalidCompany"));
          const key = `${userId}:${company.toLocaleLowerCase()}:${locale}`;
          let pending = generationRef.current.get(key);
          if (!pending) {
            pending = (async () => {
              const response = await authorizedFetch("/api/full-reports/company", {
                method: "POST", body: JSON.stringify({ company, locale }),
              }, 240_000);
              return readJson<{ report: FullReport; reused: boolean }>(response);
            })();
            generationRef.current.set(key, pending);
            pending.catch(() => generationRef.current.delete(key));
          }
          const result = await pending;
          if (sequence !== sequenceRef.current) return;
          setReport(result.report); setReportOwnerId(userId); setReused(result.reused);
          const list = await loadLibrary(controller.signal);
          if (sequence === sequenceRef.current) { setReports(list.reports || []); setLibraryOwnerId(userId); }
        } else if (target.type === "saved") {
          const result = await openReport(target.reportId, controller.signal);
          if (sequence === sequenceRef.current) { setReport(result.report); setReportOwnerId(userId); setActiveSection("thesis"); setReused(true); }
          const list = await loadLibrary(controller.signal);
          if (sequence === sequenceRef.current) { setReports(list.reports || []); setLibraryOwnerId(userId); }
        } else {
          const list = await loadLibrary(controller.signal);
          if (sequence === sequenceRef.current) { setReports(list.reports || []); setLibraryOwnerId(userId); }
        }
      } catch (cause) {
        if (controller.signal.aborted || sequence !== sequenceRef.current) return;
        setError(cause instanceof Error ? cause.message : t("requestError", { status: 0 }));
      } finally {
        if (sequence === sequenceRef.current) setLoading(false);
      }
    };
    void run();
    return () => controller.abort();
  }, [routeReady, target, authorizedFetch, isLoaded, loadLibrary, locale, openReport, readJson, retryCount, t, userId]);

  useEffect(() => {
    if (!isLoaded) return;
    if (!userId) {
      requestRef.current?.abort();
      sequenceRef.current += 1;
      setReports([]); setReport(null); setReportOwnerId(null); setLibraryOwnerId(null); setError(""); setLoading(false);
    }
  }, [isLoaded, userId]);

  const retry = () => {
    if (target.type === "generate") generationRef.current.delete(`${userId}:${target.analysisId}:${locale}`);
    if (target.type === "company") generationRef.current.delete(`${userId}:${target.company.toLocaleLowerCase()}:${locale}`);
    setError(""); setLoading(true); setRetryCount(value => value + 1);
  };

  const visibleReport = reportOwnerId === userId ? report : null;
  const visibleReports = libraryOwnerId === userId ? reports : [];
  const filteredReports = useMemo(() => {
    const term = query.trim().toLocaleLowerCase();
    return term ? visibleReports.filter(item => `${item.company} ${item.company_name || ""} ${item.period}`.toLocaleLowerCase().includes(term)) : visibleReports;
  }, [query, visibleReports]);
  const publicReports = filteredReports.filter(item => item.is_public === true);
  const publicCompanyReports = publicReports.filter(item => item.scope === "company");
  const publicPeriodReports = publicReports.filter(item => item.scope !== "company");
  const privateReports = filteredReports.filter(item => item.is_public !== true);
  const selectedSection = reportOwnerId === userId ? report?.sections.find(section => section.id === activeSection) : undefined;
  const sourceMap = useMemo(() => new Map(visibleReport?.sources.map(source => [source.id, source]) || []), [visibleReport]);
  const formatDate = (value: string) => formatReportDate(value, locale);
  const selectSavedReport = (id: string) => {
    setTarget({ type: "saved", reportId: id });
    setReused(false);
    router.replace(`/${locale}/dashboard/reports?reportId=${encodeURIComponent(id)}`);
  };
  const returnToGallery = () => {
    setTarget({ type: "library" });
    setReport(null); setReportOwnerId(null); setError(""); setReused(false); setQuery("");
    router.replace(`/${locale}/dashboard/reports`);
  };
  const generateCompany = (company: string) => {
    const normalized = company.trim();
    if (!normalized) return;
    setQuery(normalized);
    setTarget({ type: "company", company: normalized });
    setError(""); setReport(null); setReportOwnerId(null); setReused(false);
    router.replace(`/${locale}/dashboard/reports?company=${encodeURIComponent(normalized)}`);
  };
  const choosePopularCompany = (company: string) => {
    const normalized = company.trim().toLocaleUpperCase();
    const cached = visibleReports.find(item => item.scope === "company" && item.locale === locale && (item.company.toLocaleUpperCase() === normalized || item.company_name?.toLocaleUpperCase() === normalized));
    if (cached) { selectSavedReport(cached.id); return; }
    generateCompany(company);
  };
  const submitCompanySearch = (event: FormEvent) => {
    event.preventDefault();
    if (query.trim()) generateCompany(query);
  };
  const sourceLink = (sourceId: string) => {
    const source = sourceMap.get(sourceId);
    return source ? <a key={sourceId} href={`#source-${encodeURIComponent(sourceId)}`} className="inline-flex items-center gap-1 rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-800 hover:bg-sky-100">{source.title}<ChevronRight size={13} /></a> : null;
  };
  const formatScenarioValue = (value: number | null, currency: string | null) => value === null
    ? t("scenarioUnavailable")
    : `${currency ? `${currency} ` : ""}${new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(value)}`;
  const reportCard = (item: ReportSummary, isPublic: boolean) => <button key={item.id} onClick={() => selectSavedReport(item.id)} className="group flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-sky-200 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-700">
    <div className="flex w-full items-start justify-between gap-3"><div className="flex min-w-0 items-center gap-3"><CompanyLogo symbol={item.symbol || item.company} company={item.company_name || item.company} /><div className="min-w-0"><h3 className="truncate text-lg font-bold text-slate-900">{item.company_name || item.company}</h3><p className="mt-0.5 text-sm text-slate-500">{item.scope === "company" ? item.company : item.period}</p></div></div><span className={`shrink-0 rounded-full px-2.5 py-1 text-[11px] font-bold ${isPublic ? "bg-emerald-50 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>{isPublic ? t("publicBadge") : t("privateBadge")}</span></div>
    <div className="mt-5 flex flex-wrap gap-2 text-xs text-slate-500"><span className="rounded-lg bg-slate-50 px-2.5 py-1.5">{item.scope === "company" ? t("companyOverview") : item.kind === "transcript" ? t("transcript") : t("report")}</span><span className="rounded-lg bg-slate-50 px-2.5 py-1.5">{item.locale === "pt" ? t("localePortuguese") : t("localeEnglish")}</span><span className="rounded-lg bg-slate-50 px-2.5 py-1.5">{formatDate(item.created_at)}</span></div>
    <span className="mt-auto inline-flex items-center gap-1 pt-5 text-sm font-semibold text-sky-800">{t("openReport")}<ArrowRight size={15} className="transition-transform group-hover:translate-x-0.5" /></span>
  </button>;

  return (
    <div className="min-h-screen bg-[#f4f8fc] text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between px-4 py-3 md:px-8">
          <div className="flex items-center gap-3"><button onClick={() => router.push(`/${locale}/dashboard`)} className="rounded-xl p-2 text-slate-600 hover:bg-slate-100" aria-label={t("backDashboard")}><ArrowLeft size={19} /></button><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-700 text-white"><BookOpen size={18} /></div><span className="font-bold tracking-tight">FinAnalyzer</span></div>
          <div className="flex items-center gap-3"><LanguageSwitcher /><UserButton appearance={{ elements: { avatarBox: "h-9 w-9" } }} /></div>
        </div>
      </header>

      {!visibleReport && <section className="relative isolate overflow-hidden border-b border-sky-100 bg-[radial-gradient(ellipse_at_top,_rgba(186,230,253,0.45),_transparent_65%)] px-4 py-12 md:px-8 md:py-16">
        <div aria-hidden="true" className="absolute inset-0 -z-10 opacity-40" style={{ backgroundImage: "radial-gradient(#94a3b8 0.7px, transparent 0.7px)", backgroundSize: "20px 20px" }} />
        <div className="mx-auto max-w-4xl text-center"><p className="text-xs font-bold uppercase tracking-[.2em] text-sky-800">{t("libraryEyebrow")}</p><h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950 md:text-5xl">{t("companyHeroTitle")}</h1><p className="mx-auto mt-3 max-w-2xl text-sm leading-relaxed text-slate-600 md:text-base">{t("companyHeroDescription")}</p>
          <form onSubmit={submitCompanySearch} className="mx-auto mt-8 flex max-w-3xl flex-col gap-2 rounded-[1.4rem] border border-slate-200 bg-white p-2 shadow-[0_18px_50px_rgba(14,116,144,0.12)] sm:flex-row"><label className="relative min-w-0 flex-1"><span className="sr-only">{t("companySearchLabel")}</span><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} /><input value={query} onChange={event => setQuery(event.target.value)} placeholder={t("companySearchPlaceholder")} className="w-full rounded-xl bg-white py-4 pl-12 pr-4 text-base outline-none placeholder:text-slate-400 focus:ring-2 focus:ring-sky-100" /></label><button type="submit" disabled={!query.trim() || loading} className="inline-flex items-center justify-center gap-2 rounded-xl bg-sky-700 px-6 py-3 text-sm font-bold text-white transition hover:bg-sky-800 disabled:cursor-not-allowed disabled:opacity-50"><Search size={17} />{t("companySearchAction")}</button></form>
          <div className="mt-6"><p className="mb-3 text-xs font-semibold uppercase tracking-[.15em] text-slate-500">{t("popularCompanies")}</p><div className="flex flex-wrap justify-center gap-2">{POPULAR_COMPANIES.map(company => <button key={company.ticker} type="button" aria-label={`${company.name} (${company.ticker})`} onClick={() => choosePopularCompany(company.ticker)} disabled={loading} className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 py-1.5 pl-2 pr-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-sky-200 hover:bg-sky-50 disabled:opacity-60"><CompanyLogo symbol={company.ticker} company={company.name} /><span className="text-left leading-tight">{company.name}<span className="ml-1.5 text-xs font-medium text-slate-400">{company.ticker}</span></span></button>)}</div></div>
        </div>
      </section>}

      <div className={`mx-auto grid max-w-[1440px] gap-6 px-4 py-6 md:px-8 lg:py-9 ${visibleReport && visibleReport.scope !== "company" ? "lg:grid-cols-[290px_minmax(0,1fr)]" : ""}`}>
        {visibleReport && visibleReport.scope !== "company" && <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:sticky lg:top-24">
          <button onClick={returnToGallery} className="mb-4 flex w-full items-center gap-2 rounded-xl bg-sky-50 px-3 py-2.5 text-sm font-semibold text-sky-900 hover:bg-sky-100"><ArrowLeft size={16} />{t("backToGallery")}</button>
          <div className="flex items-center justify-between px-2 pb-3"><div><p className="text-xs font-bold uppercase tracking-[.14em] text-sky-800">{t("libraryEyebrow")}</p><h2 className="mt-1 text-lg font-bold">{t("libraryTitle")}</h2></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">{filteredReports.length}</span></div>
          {loading && <div className="flex items-center gap-2 px-2 py-6 text-sm text-slate-500"><Loader2 className="animate-spin" size={17} />{t("loading")}</div>}
          {!loading && !error && filteredReports.length === 0 && <p className="px-2 py-4 text-sm leading-relaxed text-slate-500">{query ? t("noMatches") : t("emptyLibrary")}</p>}
          <div className="max-h-[58vh] space-y-1 overflow-y-auto">{filteredReports.map(item => <button key={item.id} aria-pressed={visibleReport.id === item.id} onClick={() => selectSavedReport(item.id)} className={`w-full rounded-xl border p-3 text-left transition hover:border-sky-200 hover:bg-sky-50 ${visibleReport.id === item.id ? "border-sky-200 bg-sky-50" : "border-transparent"}`}><span className="flex items-center justify-between gap-2"><span className="truncate text-sm font-bold text-slate-800">{item.company}</span><ChevronRight size={15} className="shrink-0 text-slate-400" /></span><span className="mt-1 block text-xs text-slate-500">{item.period} · {item.scope === "company" ? t("companyOverview") : item.kind === "transcript" ? t("transcript") : t("report")}</span><span className="mt-1 block text-[11px] text-slate-400">{item.is_public ? t("publicBadge") : t("privateBadge")} · {formatDate(item.created_at)}</span></button>)}</div>
        </aside>}

        <main className="min-w-0">
          {error && <div role="alert" className="mb-5 flex flex-wrap items-start gap-3 rounded-2xl border border-rose-200 bg-white p-5 text-rose-800 shadow-sm"><AlertCircle className="mt-0.5 shrink-0" size={19} /><div className="min-w-0 flex-1"><p className="font-semibold">{t("errorTitle")}</p><p className="mt-1 text-sm">{error}</p></div><button onClick={retry} className="rounded-lg bg-rose-50 px-3 py-2 text-sm font-semibold hover:bg-rose-100">{t("retry")}</button><button onClick={returnToGallery} className="rounded-lg bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-200">{t("backToGallery")}</button></div>}
          {loading && !visibleReport ? <div className="flex min-h-[40vh] items-center justify-center rounded-3xl border border-slate-200 bg-white text-slate-500"><div className="flex items-center gap-3"><Loader2 className="animate-spin text-sky-700" />{target.type === "generate" ? t("generating") : target.type === "company" ? t("companyGenerating") : t("loading")}</div></div> : null}
          {!loading && !visibleReport && !error && <div className="space-y-10">
            <section><div className="mb-5"><h2 className="text-xl font-bold text-slate-900">{t("companyReports")}</h2><p className="mt-1 text-sm text-slate-500">{t("companyReportsDescription")}</p></div>
              {publicCompanyReports.length > 0 ? <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{publicCompanyReports.map(item => reportCard(item, true))}</div> : <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm leading-relaxed text-slate-600">{query ? t("noMatches") : t("publicEmpty")}</div>}
            </section>
            {publicPeriodReports.length > 0 && <section><div className="mb-5"><h2 className="text-xl font-bold text-slate-900">{t("periodReports")}</h2><p className="mt-1 text-sm text-slate-500">{t("periodReportsDescription")}</p></div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{publicPeriodReports.map(item => reportCard(item, true))}</div></section>}
            {privateReports.length > 0 && <section><div className="mb-4"><h2 className="text-xl font-bold text-slate-900">{t("yourPrivateReports")}</h2><p className="mt-1 text-sm text-slate-500">{t("privateDescription")}</p></div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{privateReports.map(item => reportCard(item, false))}</div></section>}
          </div>}
          {visibleReport?.scope === "company" && <CompanyReportReader report={visibleReport} locale={locale} t={t} onBack={returnToGallery} onDashboard={() => router.push(`/${locale}/dashboard?company=${encodeURIComponent(visibleReport.company)}`)} />}
          {visibleReport && visibleReport.scope !== "company" && <article className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-6 pt-5 md:px-10"><button onClick={returnToGallery} className="mb-4 inline-flex items-center gap-2 rounded-lg px-2 py-2 text-sm font-semibold text-sky-800 hover:bg-sky-50"><ArrowLeft size={16} />{t("backToGallery")}</button></div>
            <div className="border-b border-slate-100 bg-gradient-to-br from-white via-white to-sky-50/80 p-6 md:p-10">
              <div className="mb-5 flex flex-wrap items-center gap-2"><span className="rounded-full border border-sky-100 bg-sky-50 px-3 py-1 text-xs font-bold uppercase tracking-wide text-sky-800">{visibleReport.kind === "transcript" ? t("transcript") : t("report")}</span>{reused && <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">{t("reused")}</span>}</div>
              <p className="text-xs font-bold uppercase tracking-[.15em] text-sky-800">{t("reportEyebrow")}</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 md:text-5xl">{visibleReport.company}</h1>
              <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-500"><span className="inline-flex items-center gap-2"><Building2 size={15} />{visibleReport.period}</span><span className="inline-flex items-center gap-2"><CalendarDays size={15} />{t("created", { date: formatDate(visibleReport.created_at) })}</span>{visibleReport.score !== null && <span className="font-semibold text-sky-800">{t("score", { score: visibleReport.score })}</span>}</div>
              <div className="mt-7 rounded-2xl border border-sky-100 bg-[#f3f9ff] p-5 md:p-6"><p className="mb-2 text-xs font-bold uppercase tracking-[.14em] text-sky-800">{t("thesisCallout")}</p><p className="text-lg font-medium leading-relaxed text-slate-800">{reportText(visibleReport.sections.find(section => section.id === "thesis")?.summary || visibleReport.sections.find(section => section.id === "thesis")?.paragraphs?.[0] || t("noThesis"))}</p></div>
            </div>
            {visibleReport.metrics.length > 0 && <section className="grid gap-px border-b border-slate-100 bg-slate-100 sm:grid-cols-2 xl:grid-cols-4">{visibleReport.metrics.map((metric, index) => <div key={`${metric.label}-${index}`} className="bg-white p-5 md:p-6"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{metric.label}</p><p className="mt-2 break-words text-2xl font-bold text-slate-900">{reportText(metric.value)}</p><div className="mt-3">{sourceLink(metric.source_id)}</div></div>)}</section>}
            <div className="grid lg:grid-cols-[220px_minmax(0,1fr)]">
              <nav aria-label={t("sectionsLabel")} className="flex gap-1 overflow-x-auto border-b border-slate-100 p-3 lg:block lg:border-b-0 lg:border-r lg:p-4">{SECTION_IDS.map(id => <button key={id} aria-current={activeSection === id ? "page" : undefined} onClick={() => setActiveSection(id)} className={`whitespace-nowrap rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition lg:mb-1 lg:w-full ${activeSection === id ? "bg-sky-50 text-sky-900" : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"}`}>{t(`sections.${id}`)}</button>)}</nav>
              <section className="min-h-[400px] p-6 md:p-10"><p className="text-xs font-bold uppercase tracking-[.14em] text-sky-800">{t("sectionLabel")}</p><h2 className="mt-2 text-2xl font-bold tracking-tight">{selectedSection?.title || t(`sections.${activeSection}`)}</h2>
                {selectedSection ? <><p className="mt-4 text-lg leading-relaxed text-slate-700">{reportText(selectedSection.summary)}</p><div className="mt-6 space-y-4 text-[15px] leading-7 text-slate-600">{selectedSection.paragraphs.map((paragraph, index) => <p key={index}>{reportText(paragraph)}</p>)}</div>{selectedSection.bullets.length > 0 && <ul className="mt-6 space-y-3">{selectedSection.bullets.map((bullet, index) => <li key={index} className="flex gap-3 text-sm leading-relaxed text-slate-700"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-sky-600" /><span>{reportText(bullet)}</span></li>)}</ul>}{selectedSection.source_ids.length > 0 && <div className="mt-8 border-t border-slate-100 pt-5"><p className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">{t("sectionSources")}</p><div className="flex flex-wrap gap-2">{selectedSection.source_ids.map(sourceLink)}</div></div>}</> : <p className="mt-4 text-slate-500">{t("sectionUnavailable")}</p>}
              </section>
            </div>
            {(visibleReport.watchpoints.length > 0 || visibleReport.valuation) && <div className="grid gap-6 border-t border-slate-100 bg-slate-50/70 p-6 md:p-8 xl:grid-cols-2">{visibleReport.watchpoints.length > 0 && <section className="rounded-2xl border border-amber-100 bg-white p-5"><h3 className="font-bold text-slate-900">{t("watchpoints")}</h3><ul className="mt-4 space-y-3">{visibleReport.watchpoints.map((point, index) => <li key={index} className="flex gap-3 text-sm leading-relaxed text-slate-600"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />{reportText(point)}</li>)}</ul></section>}{visibleReport.valuation && <section className="rounded-2xl border border-slate-200 bg-white p-5"><h3 className="font-bold text-slate-900">{t("valuation")}</h3><p className="mt-3 text-sm leading-relaxed text-slate-600">{visibleReport.valuation.available && visibleReport.valuation.base_eps !== null ? t("valuationBasis", { eps: visibleReport.valuation.base_eps, currency: visibleReport.valuation.currency || "" }) : visibleReport.valuation.reason || t("valuationUnavailable")}</p>{visibleReport.valuation.source_id && <div className="mt-3">{sourceLink(visibleReport.valuation.source_id)}</div>}
              {visibleReport.valuation.available && visibleReport.valuation.base_eps !== null && visibleReport.valuation.base_eps > 0 && <div className="mt-6 border-t border-slate-100 pt-5"><h4 className="font-semibold text-slate-900">{t("scenarioTitle")}</h4><p className="mt-1 text-xs leading-relaxed text-slate-500">{t("scenarioDisclaimer")}</p><div className="mt-4 space-y-4">{SCENARIOS.map(scenario => {
                const inputs = scenarioInputs[scenario.key];
                const value = calculateIllustrativeValue(visibleReport.valuation.base_eps!, inputs);
                const update = (field: keyof ValuationInputs, raw: string) => setScenarioInputs(current => ({ ...current, [scenario.key]: { ...current[scenario.key], [field]: Number(raw) } }));
                return <div key={scenario.key} className="rounded-xl bg-slate-50 p-3"><div className="flex items-center justify-between gap-3"><span className="text-sm font-semibold text-slate-800">{t(`scenarios.${scenario.key}`)}</span><span className="text-sm font-bold text-sky-800">{formatScenarioValue(value, visibleReport.valuation.currency)}</span></div><div className="mt-3 grid grid-cols-3 gap-2"><label className="text-[11px] font-medium text-slate-500">{t("growthInput")}<input aria-label={`${t(`scenarios.${scenario.key}`)} ${t("growthInput")}`} type="number" min="-50" max="100" step="1" value={inputs.growthPercent} onChange={event => update("growthPercent", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-800" /></label><label className="text-[11px] font-medium text-slate-500">{t("peInput")}<input aria-label={`${t(`scenarios.${scenario.key}`)} ${t("peInput")}`} type="number" min="1" max="100" step="1" value={inputs.peMultiple} onChange={event => update("peMultiple", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-800" /></label><label className="text-[11px] font-medium text-slate-500">{t("discountInput")}<input aria-label={`${t(`scenarios.${scenario.key}`)} ${t("discountInput")}`} type="number" min="0" max="50" step="1" value={inputs.discountPercent} onChange={event => update("discountPercent", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-800" /></label></div></div>;
              })}</div><p className="mt-3 text-xs text-slate-500">{t("scenarioFormula")}</p></div>}
            </section>}</div>}
            <section className="border-t border-slate-100 p-6 md:p-8"><h3 className="text-xl font-bold">{t("sources")}</h3><p className="mt-1 text-sm text-slate-500">{t("coverageDisclaimer", { coverage: visibleReport.coverage })}</p><ol className="mt-5 grid gap-3 md:grid-cols-2">{visibleReport.sources.map((source, index) => { const validUrl = source.url && /^https?:\/\//i.test(source.url); return <li id={`source-${encodeURIComponent(source.id)}`} key={source.id} className="scroll-mt-28 rounded-xl border border-slate-200 bg-slate-50 p-4"><span className="mr-2 text-xs font-bold text-sky-800">[{index + 1}]</span>{validUrl ? <a href={source.url!} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold text-slate-800 underline decoration-slate-300 underline-offset-4 hover:text-sky-800">{source.title}</a> : <span className="text-sm font-semibold text-slate-800">{source.title}</span>}</li>; })}</ol></section>
          </article>}
        </main>
      </div>
    </div>
  );
}
