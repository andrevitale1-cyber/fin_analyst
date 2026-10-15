"use client";

import { useAuth, UserButton } from "@clerk/nextjs";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlertCircle, ArrowLeft, ArrowRight, BookOpen, Building2, CalendarDays, ChevronRight, FileText, Loader2, Search } from "lucide-react";
import LanguageSwitcher from "./LanguageSwitcher";
import { splitBold } from "../lib/analysisText";
import { calculateIllustrativeValue, type ValuationInputs } from "../lib/fullReportValuation";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "https://api-finanalyzer.onrender.com";
const SECTION_IDS = ["thesis", "business", "financials", "moat", "management", "risks", "valuation"] as const;
type SectionId = typeof SECTION_IDS[number];
type FullReportSection = { id: SectionId; title: string; summary: string; paragraphs: string[]; bullets: string[]; source_ids: string[] };
type FullReport = {
  id: string; company: string; period: string; locale: "en" | "pt"; kind: "report" | "transcript"; created_at: string; score: number | null;
  coverage: string; sections: FullReportSection[]; metrics: { label: string; value: string; source_id: string }[];
  watchpoints: string[]; sources: { id: string; title: string; url: string | null }[];
  valuation: { available: boolean; base_eps: number | null; currency: string | null; source_id: string | null; reason: string };
};
type ReportSummary = Pick<FullReport, "id" | "company" | "period" | "locale" | "kind" | "created_at" | "score">;
type RouteTarget = { type: "library" } | { type: "generate"; analysisId: string } | { type: "saved"; reportId: string };
const SCENARIOS: { key: "bear" | "base" | "bull"; growthPercent: number; peMultiple: number; discountPercent: number }[] = [
  { key: "bear", growthPercent: 0, peMultiple: 12, discountPercent: 12 },
  { key: "base", growthPercent: 10, peMultiple: 15, discountPercent: 10 },
  { key: "bull", growthPercent: 20, peMultiple: 20, discountPercent: 8 },
];

function reportText(text: string) {
  return splitBold(text).map((part, index) => part.bold ? <strong key={index} className="font-semibold text-slate-900">{part.text}</strong> : part.text);
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
    setTarget(analysisId ? { type: "generate", analysisId } : reportId ? { type: "saved", reportId } : { type: "library" });
    setRouteReady(true);
  }, []);

  const authorizedFetch = useCallback(async (path: string, init: RequestInit = {}) => {
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
    const timeout = setTimeout(() => { timedOut = true; controller.abort(); }, 180_000);
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
    setError(""); setLoading(true); setRetryCount(value => value + 1);
  };

  const visibleReport = reportOwnerId === userId ? report : null;
  const visibleReports = libraryOwnerId === userId ? reports : [];
  const filteredReports = useMemo(() => {
    const term = query.trim().toLocaleLowerCase();
    return term ? visibleReports.filter(item => `${item.company} ${item.period}`.toLocaleLowerCase().includes(term)) : visibleReports;
  }, [query, visibleReports]);
  const selectedSection = reportOwnerId === userId ? report?.sections.find(section => section.id === activeSection) : undefined;
  const sourceMap = useMemo(() => new Map(visibleReport?.sources.map(source => [source.id, source]) || []), [visibleReport]);
  const formatDate = (value: string) => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(date);
  };
  const selectSavedReport = (id: string) => {
    setTarget({ type: "saved", reportId: id });
    router.replace(`/${locale}/dashboard/reports?reportId=${encodeURIComponent(id)}`);
  };
  const sourceLink = (sourceId: string) => {
    const source = sourceMap.get(sourceId);
    return source ? <a key={sourceId} href={`#source-${encodeURIComponent(sourceId)}`} className="inline-flex items-center gap-1 rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-800 hover:bg-sky-100">{source.title}<ChevronRight size={13} /></a> : null;
  };
  const formatScenarioValue = (value: number | null, currency: string | null) => value === null
    ? t("scenarioUnavailable")
    : `${currency ? `${currency} ` : ""}${new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(value)}`;

  return (
    <div className="min-h-screen bg-[#f4f8fc] text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between px-4 py-3 md:px-8">
          <div className="flex items-center gap-3"><button onClick={() => router.push(`/${locale}/dashboard`)} className="rounded-xl p-2 text-slate-600 hover:bg-slate-100" aria-label={t("backDashboard")}><ArrowLeft size={19} /></button><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-700 text-white"><BookOpen size={18} /></div><span className="font-bold tracking-tight">FinAnalyzer</span></div>
          <div className="flex items-center gap-3"><LanguageSwitcher /><UserButton appearance={{ elements: { avatarBox: "h-9 w-9" } }} /></div>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1440px] gap-6 px-4 py-6 md:px-8 lg:grid-cols-[290px_minmax(0,1fr)] lg:py-9">
        <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:sticky lg:top-24">
          <div className="flex items-center justify-between px-2 pb-3"><div><p className="text-xs font-bold uppercase tracking-[.14em] text-sky-800">{t("libraryEyebrow")}</p><h2 className="mt-1 text-lg font-bold">{t("libraryTitle")}</h2></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">{visibleReports.length}</span></div>
          <label className="relative block"><span className="sr-only">{t("searchPlaceholder")}</span><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} /><input value={query} onChange={event => setQuery(event.target.value)} placeholder={t("searchPlaceholder")} className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 text-sm outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100" /></label>
          {loading && !visibleReport ? <div className="flex items-center gap-2 px-2 py-6 text-sm text-slate-500"><Loader2 className="animate-spin" size={17} />{t("loading")}</div> : null}
          {!loading && !error && filteredReports.length === 0 ? <p className="px-2 py-6 text-sm leading-relaxed text-slate-500">{query ? t("noMatches") : t("emptyLibrary")}</p> : null}
          <div className="mt-3 max-h-[58vh] space-y-1 overflow-y-auto">{filteredReports.map(item => <button key={item.id} aria-pressed={visibleReport?.id === item.id} onClick={() => selectSavedReport(item.id)} className={`w-full rounded-xl border p-3 text-left transition hover:border-sky-200 hover:bg-sky-50 ${visibleReport?.id === item.id ? "border-sky-200 bg-sky-50" : "border-transparent"}`}><span className="flex items-center justify-between gap-2"><span className="truncate text-sm font-bold text-slate-800">{item.company}</span><ChevronRight size={15} className="shrink-0 text-slate-400" /></span><span className="mt-1 block text-xs text-slate-500">{item.period} · {item.kind === "transcript" ? t("transcript") : t("report")}</span><span className="mt-1 block text-[11px] text-slate-400">{formatDate(item.created_at)}</span></button>)}</div>
        </aside>

        <main className="min-w-0">
          {error && <div role="alert" className="mb-5 flex items-start gap-3 rounded-2xl border border-rose-200 bg-white p-5 text-rose-800 shadow-sm"><AlertCircle className="mt-0.5 shrink-0" size={19} /><div className="flex-1"><p className="font-semibold">{t("errorTitle")}</p><p className="mt-1 text-sm">{error}</p></div><button onClick={retry} className="rounded-lg bg-rose-50 px-3 py-2 text-sm font-semibold hover:bg-rose-100">{t("retry")}</button></div>}
          {loading && !visibleReport ? <div className="flex min-h-[50vh] items-center justify-center rounded-3xl border border-slate-200 bg-white text-slate-500"><div className="flex items-center gap-3"><Loader2 className="animate-spin text-sky-700" />{target.type === "generate" ? t("generating") : t("loading")}</div></div> : null}
          {!loading && !visibleReport && !error ? <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm md:p-12"><div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-50 text-sky-800"><FileText /></div><h1 className="text-3xl font-bold tracking-tight">{t("welcomeTitle")}</h1><p className="mt-3 max-w-2xl leading-relaxed text-slate-600">{t("welcomeBody")}</p><button onClick={() => router.push(`/${locale}/dashboard`)} className="mt-6 inline-flex items-center gap-2 rounded-xl bg-sky-700 px-4 py-3 text-sm font-bold text-white hover:bg-sky-800">{t("newAnalysis")}<ArrowRight size={16} /></button></div> : null}
          {visibleReport && <article className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
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
