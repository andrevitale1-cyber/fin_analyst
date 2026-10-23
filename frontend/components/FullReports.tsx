"use client";

import { useAuth, UserButton } from "@clerk/nextjs";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { type FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlertCircle, ArrowLeft, ArrowRight, BookOpen, Building2, CalendarDays, ChevronRight, Loader2, Search, Trash2 } from "lucide-react";
import LanguageSwitcher from "./LanguageSwitcher";
import CompanyReportReader from "./CompanyReportReader";
import CompanyLogo from "./CompanyLogo";
import ConfirmDeleteDialog from "./ConfirmDeleteDialog";
import ReportSources from "./ReportSources";
import { reportCitationIds, stripReportCitations } from "../lib/reportCitations";
import { splitBold } from "../lib/analysisText";
import { type ReportMetric } from "../lib/reportNumbers";
import { calculateIllustrativeValue, type ValuationInputs } from "../lib/fullReportValuation";
import { PUBLISHED_REPORTS, publishedReportForCompany } from "../lib/publishedReports";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "https://api-finanalyzer.onrender.com";
const SECTION_IDS = ["thesis", "business", "financials", "moat", "management", "risks", "valuation"] as const;
const COMPANY_SECTION_IDS = ["thesis", "business", "financials", "moat", "management", "sentiment", "outlook", "risks", "valuation", "verdict"] as const;
const POPULAR_COMPANIES = [
  {name: "Microsoft", ticker: "MSFT"}, {name: "NVIDIA", ticker: "NVDA"}, {name: "Apple", ticker: "AAPL"},
  {name: "Google", ticker: "GOOGL"}, {name: "Amazon", ticker: "AMZN"}, {name: "Meta", ticker: "META"},
  {name: "Petrobras", ticker: "PETR4"}, {name: "WEG", ticker: "WEGE3"}, {name: "Vivara", ticker: "VIVA3"},
];
type SectionId = typeof SECTION_IDS[number];
type CompanySectionId = typeof COMPANY_SECTION_IDS[number];
type FullReportSection = { id: SectionId | CompanySectionId; title: string; summary: string; paragraphs: string[]; bullets: string[]; source_ids: string[] };
export type FullReport = {
  publication?: {reviewed: boolean; covered_year: number; covered_quarter: number};
  editorial_status?: {state: string; latest_year: number | null; latest_quarter: number | null};
  id: string; company: string; company_name?: string | null; symbol?: string | null; period: string; scope?: "company" | "period"; as_of?: string | null; locale: "en" | "pt"; kind: "report" | "transcript" | "company"; created_at: string; report_version?: string; score: number | null; is_public?: boolean;
  coverage: string; sections: FullReportSection[]; metrics: (ReportMetric & { label: string; value: string; group?: "scale" | "performance" | "valuation"; as_of?: string | null; source_id: string })[];
  signals?: { id: string; label: string; value: string; tone: "positive" | "neutral" | "negative" | "unknown"; source_ids: string[] }[];
  scorecard?: { id: string; label: string; score: number | null; reason: string; source_ids: string[] }[];
  tracking_metrics?: { label: string; expectation: string; status: string; source_ids: string[] }[];
  breakdowns?: import("../lib/reportBreakdowns").ReportBreakdown[];
  analyst_consensus?: {rating: string | null; analyst_count: number | null; target_mean: number | null; target_low: number | null; target_high: number | null; bullish: number | null; neutral: number | null; bearish: number | null; currency: string | null; as_of: string | null; source_ids: string[]} | null;
  financial_history?: { period: string; currency: string | null; revenue: number | null; net_income: number | null; free_cash_flow: number | null; source_id: string }[];
  projections?: { period: string; currency: string | null; revenue: number | null; eps: number | null; basis: "management_guidance" | "analyst_consensus"; source_id: string }[];
  market?: { price: number | null; change_percent: number | null; currency: string | null; as_of: string | null; source_id: string | null };
  watchpoints: string[]; sources: { id: string; title: string; url: string | null }[];
  valuation: { available: boolean; base_eps: number | null; currency: string | null; source_id: string | null; reason: string; method?: string | null; fair_value?: number | null; scenarios?: { case: "bear" | "base" | "bull"; growth_percent: number; pe_multiple: number; discount_percent: number; rationale: string; future_value: number | null; present_value: number | null; upside_percent: number | null }[] };
  investment_model?: import("../lib/investmentModel").InvestmentModel;
};
type ReportSummary = Pick<FullReport, "id" | "company" | "company_name" | "symbol" | "period" | "scope" | "as_of" | "locale" | "kind" | "created_at" | "report_version" | "score" | "is_public">;
type RouteTarget = { type: "library" } | { type: "generate"; analysisId: string } | { type: "company"; company: string } | { type: "saved"; reportId: string } | { type: "job"; jobId: string; company: string };
const SCENARIOS: { key: "bear" | "base" | "bull"; growthPercent: number; peMultiple: number; discountPercent: number }[] = [
  { key: "bear", growthPercent: 0, peMultiple: 12, discountPercent: 12 },
  { key: "base", growthPercent: 10, peMultiple: 15, discountPercent: 10 },
  { key: "bull", growthPercent: 20, peMultiple: 20, discountPercent: 8 },
];

function formatReportDate(value: string, locale: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium", ...(/^\d{4}-\d{2}-\d{2}$/.test(value) ? { timeZone: "UTC" } : {}),
  }).format(parsed);
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
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchIndex, setSearchIndex] = useState(-1);
  const searchRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const focusSearch = (event: KeyboardEvent) => {
      const element = event.target as HTMLElement;
      if (event.key === "/" && !event.metaKey && !event.ctrlKey && !element.isContentEditable && !["INPUT", "TEXTAREA", "SELECT"].includes(element.tagName)) { event.preventDefault(); searchRef.current?.focus(); }
    };
    document.addEventListener("keydown", focusSearch);
    return () => document.removeEventListener("keydown", focusSearch);
  }, []);
  const [loading, setLoading] = useState(true);
  const [coverageTarget, setCoverageTarget] = useState<{company: string; state: string; owner: string} | null>(null);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ReportSummary | null>(null);
  const [deleteError, setDeleteError] = useState("");
  const [deleteNotice, setDeleteNotice] = useState("");
  const deleteSubject = useMemo(() => deleteTarget ? { company: deleteTarget.company_name || deleteTarget.company, symbol: deleteTarget.symbol || deleteTarget.company, detail: deleteTarget.period } : null, [deleteTarget]);
  const accountRef = useRef(userId);
  accountRef.current = userId;
  const [reused, setReused] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [scenarioInputs, setScenarioInputs] = useState<Record<"bear" | "base" | "bull", ValuationInputs>>(() => Object.fromEntries(SCENARIOS.map(({ key, ...values }) => [key, values])) as Record<"bear" | "base" | "bull", ValuationInputs>);
  const requestRef = useRef<AbortController | null>(null);
  const sequenceRef = useRef(0);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const analysisId = params.get("analysisId") || "";
    const reportId = params.get("reportId") || "";
    const company = params.get("company")?.trim() || "";
    const jobId = params.get("jobId") || "";
    const published = company ? publishedReportForCompany(company) : PUBLISHED_REPORTS.find(item => item.id === reportId);
    if (published) { window.location.replace(published.url); return; }
    setQuery(company);
    setTarget(company ? { type: "company", company } : jobId ? { type: "job", jobId, company } : analysisId ? { type: "generate", analysisId } : reportId ? { type: "saved", reportId } : { type: "library" });
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
    const result = await readJson<{ reports: ReportSummary[] }>(response);
    return { reports: [...PUBLISHED_REPORTS, ...result.reports.filter(item => !(item.is_public && item.scope === "company" && publishedReportForCompany(item.company)))] };
  }, [authorizedFetch, readJson]);

  const openReport = useCallback(async (id: string, signal: AbortSignal) => {
    const response = await authorizedFetch(`/api/full-reports/${encodeURIComponent(id)}`, { signal });
    return readJson<{ report: FullReport }>(response);
  }, [authorizedFetch, readJson]);

  const awaitJob = useCallback(async (jobId: string, signal: AbortSignal) => {
    type JobResult = { state: string; stage?: string; detail?: string; report?: FullReport; reused?: boolean };
    for (;;) {
      const response = await authorizedFetch(`/api/report-jobs/${encodeURIComponent(jobId)}`, { signal }, 30_000);
      const job = await readJson<JobResult>(response);
      if (signal.aborted) throw new DOMException("Aborted", "AbortError");
      if (job.state === "completed" && job.report) return { report: job.report, reused: Boolean(job.reused) };
      if (job.state === "failed") throw new Error(job.detail || t("generationError"));
      await new Promise<void>((resolve, reject) => {
        const abort = () => { clearTimeout(timer); reject(new DOMException("Aborted", "AbortError")); };
        const timer = setTimeout(() => { signal.removeEventListener("abort", abort); resolve(); }, 2500);
        signal.addEventListener("abort", abort, { once: true });
        if (signal.aborted) abort();
      });
    }
  }, [authorizedFetch, readJson, t]);

  const lookupThesis = useCallback(async (body: {company?: string; analysis_id?: number; locale: string}, signal: AbortSignal) => {
    const response = await authorizedFetch(body.analysis_id ? "/api/full-reports" : "/api/thesis-library/resolve", { method: "POST", body: JSON.stringify(body), signal }, 30_000);
    const result = await readJson<{ state?: string; job_id?: string; company: string; report?: FullReport; reused?: boolean }>(response);
    if (signal.aborted) throw new DOMException("Aborted", "AbortError");
    const published = publishedReportForCompany(result.company || result.report?.company || "");
    if (published) {
      window.location.assign(published.url);
      return { report: undefined, reused: true, company: published.company, state: "completed" };
    }
    if (result.report) return { report: result.report, reused: Boolean(result.reused) };
    if (!result.job_id) return {report: undefined, reused: false, company: result.company, state: result.state || "unavailable"};
    const params = new URLSearchParams({company: result.company, jobId: result.job_id});
    window.history.replaceState(null, "", `${window.location.pathname}?${params}`);
    return awaitJob(result.job_id, signal);
  }, [authorizedFetch, readJson, awaitJob, t]);

  useEffect(() => {
    if (!routeReady || !isLoaded || !userId) return;
    const sequence = ++sequenceRef.current;
    const controller = new AbortController();
    requestRef.current?.abort();
    requestRef.current = controller;
    setLoading(true);
    setCoverageTarget(null);
    setError("");
    setDeleteError(""); setDeleteNotice(""); setDeletingId(null); setDeleteTarget(null);
    setReport(null);
    setReportOwnerId(null);
    setReports([]);
    setLibraryOwnerId(null);
    setReused(false);

    const refreshLibrary = async (optional = false) => {
      const list = await loadLibrary(controller.signal).catch(cause => {
        if (!optional) throw cause;
        return null;
      });
      if (list && sequence === sequenceRef.current) { setReports(list.reports || []); setLibraryOwnerId(userId); }
    };
    const run = async () => {
      try {
        if (target.type === "generate") {
          if (!/^\d+$/.test(target.analysisId)) throw new Error(t("invalidAnalysis"));
          const result = await lookupThesis({ analysis_id: Number(target.analysisId), locale }, controller.signal);
          if (sequence !== sequenceRef.current) return;
          if (!result.report) { setCoverageTarget({company: result.company, state: result.state, owner: userId || ""}); await refreshLibrary(true); return; }
          setReport(result.report);
          setReportOwnerId(userId);
          setReused(result.reused);
          await refreshLibrary(true);
        } else if (target.type === "company") {
          const company = target.company.trim();
          if (!company || company.length > 100 || /[\u0000-\u001f]/.test(company)) throw new Error(t("invalidCompany"));
          const result = await lookupThesis({ company, locale }, controller.signal);
          if (sequence !== sequenceRef.current) return;
          if (!result.report) { setCoverageTarget({company: result.company, state: result.state, owner: userId || ""}); await refreshLibrary(true); return; }
          setReport(result.report); setReportOwnerId(userId); setReused(result.reused);
        } else if (target.type === "job") {
          const result = await awaitJob(target.jobId, controller.signal);
          if (sequence !== sequenceRef.current) return;
          setReport(result.report); setReportOwnerId(userId); setReused(result.reused);
        } else if (target.type === "saved") {
          const result = await openReport(target.reportId, controller.signal);
          if (sequence === sequenceRef.current) { setReport(result.report); setReportOwnerId(userId); setActiveSection("thesis"); setReused(true); }
          await refreshLibrary(true);
        } else {
          await refreshLibrary();
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
  }, [routeReady, target, authorizedFetch, isLoaded, loadLibrary, locale, openReport, readJson, retryCount, t, userId, lookupThesis, awaitJob]);

  useEffect(() => {
    if (!isLoaded) return;
    if (!userId) {
      requestRef.current?.abort();
      sequenceRef.current += 1;
      setReports([]); setReport(null); setReportOwnerId(null); setLibraryOwnerId(null); setError(""); setLoading(false); setCoverageTarget(null);
    }
  }, [isLoaded, userId]);

  const retry = () => {
    if (target.type === "job") {
      window.history.replaceState(null, "", `${window.location.pathname}?company=${encodeURIComponent(target.company)}`);
      setTarget({ type: "company", company: target.company });
    }
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
  const deletePrivateReport = async (item: ReportSummary) => {
    if (item.is_public || deletingId || !userId) return;
    const owner = userId;
    setDeletingId(item.id); setDeleteError(""); setDeleteNotice("");
    try {
      const response = await authorizedFetch(`/api/full-reports/${encodeURIComponent(item.id)}`, { method: "DELETE" }, 30_000);
      if (!response.ok) throw new Error("delete_failed");
      if (accountRef.current !== owner) return;
      setReports(items => items.filter(report => report.id !== item.id));
      setDeleteTarget(null);
      setDeleteNotice(t("deleteSuccess"));
    } catch {
      if (accountRef.current === owner) setDeleteError(t("deleteError"));
    } finally {
      if (accountRef.current === owner) setDeletingId(null);
    }
  };
  const selectedSection = reportOwnerId === userId ? report?.sections.find(section => section.id === activeSection) : undefined;
  const formatDate = (value: string) => formatReportDate(value, locale);
  const selectSavedReport = (id: string) => {
    const published = PUBLISHED_REPORTS.find(item => item.id === id);
    if (published) { window.location.assign(published.url); return; }
    setTarget({ type: "saved", reportId: id });
    setReused(false);
    router.replace(`/${locale}/dashboard/reports?reportId=${encodeURIComponent(id)}`);
  };
  const returnToGallery = () => {
    setTarget({ type: "library" });
    setReport(null); setReportOwnerId(null); setError(""); setReused(false); setQuery(""); setCoverageTarget(null);
    router.replace(`/${locale}/dashboard/reports`);
  };
  const openCompanyInLibrary = (company: string) => {
    const normalized = company.trim();
    if (!normalized) return;
    const published = publishedReportForCompany(normalized);
    if (published) { window.location.assign(published.url); return; }
    setQuery(normalized);
    setSearchOpen(false); setSearchIndex(-1);
    setTarget({ type: "company", company: normalized });
    setError(""); setReport(null); setReportOwnerId(null); setReused(false);
    router.replace(`/${locale}/dashboard/reports?company=${encodeURIComponent(normalized)}`);
  };
  const choosePopularCompany = (company: string) => {
    const normalized = company.trim().toLocaleUpperCase();
    const cached = visibleReports.find(item => item.scope === "company" && item.locale === locale && (item.company.toLocaleUpperCase() === normalized || item.company_name?.toLocaleUpperCase() === normalized));
    if (cached?.is_public) { selectSavedReport(cached.id); return; }
    openCompanyInLibrary(company);
  };
  const submitCompanySearch = (event: FormEvent) => {
    event.preventDefault();
    if (query.trim()) choosePopularCompany(query);
  };
  const searchSuggestions = Array.from(new Map([
    ...POPULAR_COMPANIES.map(item => [item.ticker, item] as const),
    ...visibleReports.filter(item => item.scope === "company").map(item => [item.company, { ticker: item.company, name: item.company_name || item.company }] as const),
  ]).values()).filter(item => query.trim() && `${item.name} ${item.ticker}`.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase())).slice(0, 6);
  const requestCoverage = async (company: string) => {
    const owner = userId;
    setLoading(true); setError("");
    try {
      const response = await authorizedFetch("/api/thesis-library/requests", {method: "POST", body: JSON.stringify({company, locale})}, 30_000);
      const result = await readJson<{state: string; report?: FullReport}>(response);
      if (accountRef.current !== owner) return;
      if (result.report) { setReport(result.report); setReportOwnerId(owner || null); setCoverageTarget(null); }
      else setCoverageTarget({company, state: "requested", owner: owner || ""});
    } catch (cause) {
      if (accountRef.current === owner) setError(cause instanceof Error ? cause.message : t("generationError"));
    } finally { if (accountRef.current === owner) setLoading(false); }
  };
  const reportText = (value: string) => splitBold(stripReportCitations(value, visibleReport?.sources || [])).map((part, index) => part.bold ? <strong key={index} className="font-semibold text-slate-900">{part.text}</strong> : part.text);
  const sourcesFor = (ids: (string | null)[], values: string[] = [], anchors = false) => {
    const all = visibleReport?.sources || [];
    const selected = new Set([...ids, ...values.flatMap(value => reportCitationIds(value, all))]);
    const sources = all.filter(source => selected.has(source.id));
    return <ReportSources sources={sources} label={t("sourceCount", { count: sources.length })} anchors={anchors} />;
  };
  const formatScenarioValue = (value: number | null, currency: string | null) => value === null
    ? t("scenarioUnavailable")
    : `${currency ? `${currency} ` : ""}${new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(value)}`;
  const reportCard = (item: ReportSummary, isPublic: boolean) => <div key={item.id} className="relative h-full"><button onClick={() => selectSavedReport(item.id)} className="group flex h-full w-full flex-col rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:border-sky-200 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-700">
    <div className="flex w-full items-start justify-between gap-3"><div className="flex min-w-0 items-center gap-3"><CompanyLogo symbol={item.symbol || item.company} company={item.company_name || item.company} /><div className="min-w-0"><h3 className="truncate text-lg font-bold text-slate-900">{item.company_name || item.company}</h3><p className="mt-0.5 text-sm text-slate-500">{item.scope === "company" ? item.company : item.period}</p></div></div><span className={`shrink-0 rounded-full px-2.5 py-1 text-[11px] font-bold ${isPublic ? "bg-emerald-50 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>{isPublic ? t("publicBadge") : t("privateBadge")}</span></div>
    <div className="mt-5 flex flex-wrap gap-2 text-xs text-slate-500"><span className="rounded-lg bg-slate-50 px-2.5 py-1.5">{item.scope === "company" ? t("companyOverview") : item.kind === "transcript" ? t("transcript") : t("report")}</span><span className="rounded-lg bg-slate-50 px-2.5 py-1.5">{item.locale === "pt" ? t("localePortuguese") : t("localeEnglish")}</span><span className="rounded-lg bg-slate-50 px-2.5 py-1.5">{formatDate(item.as_of || item.created_at)}</span></div>
    <span className="mt-auto inline-flex items-center gap-1 pr-12 pt-5 text-sm font-semibold text-sky-800">{t("openReport")}<ArrowRight size={15} className="transition-transform group-hover:translate-x-0.5" /></span>
  </button>{!isPublic && <button type="button" onClick={() => { setDeleteError(""); setDeleteTarget(item); }} disabled={deletingId !== null} aria-label={t("deleteReport", { company: item.company_name || item.company })} title={t("deleteReport", { company: item.company_name || item.company })} className="absolute bottom-3 right-3 flex h-11 w-11 items-center justify-center rounded-xl text-slate-400 transition hover:bg-rose-50 hover:text-rose-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-600 disabled:opacity-40">{deletingId === item.id ? <Loader2 size={17} className="animate-spin" /> : <Trash2 size={17} />}</button>}</div>;

  return (
    <div className="min-h-screen bg-[#fafaf9] text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between px-4 py-3 md:px-8">
          <div className="flex items-center gap-3"><button onClick={() => router.push(`/${locale}/dashboard`)} className="rounded-xl p-2 text-slate-600 hover:bg-slate-100" aria-label={t("backDashboard")}><ArrowLeft size={19} /></button><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-700 text-white"><BookOpen size={18} /></div><span className="font-bold tracking-tight">FinAnalyzer</span></div>
          <div className="flex items-center gap-3"><LanguageSwitcher /><UserButton appearance={{ elements: { avatarBox: "h-9 w-9" } }} /></div>
        </div>
      </header>

      {!visibleReport && <section className="px-5 pb-14 pt-14 md:pb-20 md:pt-20">
        <p className="mx-auto mb-5 max-w-xl text-center text-xs leading-5 text-slate-500">{t("libraryReadyDescription")}</p>
        <div className="mx-auto max-w-[900px] text-center"><p className="sr-only">{t("libraryEyebrow")}</p><h1 className="text-[26px] leading-9 tracking-tight text-[#0a0a0a] md:text-[30px]" style={{ fontFamily: '"Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif' }}>{t("companyHeroTitle")}</h1>
          <form onSubmit={submitCompanySearch} role="search" className="relative mx-auto mt-7 flex h-[52px] max-w-[580px] items-center rounded-[14px] border border-[#e5e5e3] bg-white shadow-[0_8px_26px_rgba(0,0,0,0.16),0_2px_5px_rgba(0,0,0,0.06)] focus-within:ring-2 focus-within:ring-sky-200"><label className="flex min-w-0 flex-1 items-center"><span className="sr-only">{t("companySearchLabel")}</span><Search className="ml-5 shrink-0 text-[#a3a3a3]" size={20} /><input ref={searchRef} value={query} role="combobox" aria-expanded={searchOpen && searchSuggestions.length > 0} aria-controls="company-suggestions" aria-autocomplete="list" aria-activedescendant={searchOpen && searchIndex >= 0 ? `company-suggestion-${searchIndex}` : undefined} autoComplete="off" spellCheck={false} onFocus={() => setSearchOpen(true)} onBlur={event => { if (!event.currentTarget.form?.contains(event.relatedTarget as Node)) setSearchOpen(false); }} onChange={event => { setQuery(event.target.value); setSearchOpen(true); setSearchIndex(-1); }} onKeyDown={event => {
                if (event.key === "Escape") { setSearchOpen(false); setSearchIndex(-1); }
                else if (["ArrowDown", "ArrowUp"].includes(event.key) && searchSuggestions.length) { event.preventDefault(); setSearchOpen(true); setSearchIndex(current => current < 0 ? (event.key === "ArrowDown" ? 0 : searchSuggestions.length - 1) : (current + (event.key === "ArrowDown" ? 1 : -1) + searchSuggestions.length) % searchSuggestions.length); }
                else if (event.key === "Enter" && searchOpen && searchIndex >= 0 && searchSuggestions[searchIndex]) { event.preventDefault(); choosePopularCompany(searchSuggestions[searchIndex].ticker); }
              }} placeholder={t("companySearchPlaceholder")} className="h-full w-full min-w-0 bg-transparent py-5 pl-3 pr-2 text-base text-slate-900 outline-none placeholder:text-[#a3a3a3]" /></label>{query.trim() ? <button type="submit" disabled={loading} aria-label={t("companySearchAction")} className="mr-3 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-700 hover:bg-sky-100 disabled:opacity-50"><ArrowRight size={18} /></button> : <kbd aria-hidden="true" className="mr-4 rounded-lg border border-neutral-200 bg-neutral-50 px-2 py-1 text-sm text-neutral-400">/</kbd>}{searchOpen && searchSuggestions.length > 0 && <ul id="company-suggestions" role="listbox" className="absolute left-0 right-0 top-full z-30 mt-2 overflow-hidden rounded-xl border border-[#e7e7e6] bg-white py-1 text-left shadow-[0_8px_30px_rgba(0,0,0,0.1)]">{searchSuggestions.map((company, index) => <li key={company.ticker} id={`company-suggestion-${index}`} role="option" aria-selected={searchIndex === index} onMouseDown={event => event.preventDefault()} onClick={() => { if (!loading) choosePopularCompany(company.ticker); }} className={`flex cursor-pointer items-center gap-3 px-4 py-3 ${searchIndex === index ? "bg-sky-50" : "hover:bg-neutral-50"}`}><CompanyLogo small symbol={company.ticker} company={company.name} /><span className="min-w-0 flex-1 truncate text-sm font-medium">{company.name}</span><span className="rounded-md bg-sky-50 px-2 py-0.5 font-mono text-xs font-semibold text-sky-700">{company.ticker}</span></li>)}</ul>}</form>
          <div className="mx-auto mt-12 max-w-[630px]"><p className="mb-4 text-[11px] font-medium uppercase tracking-[.1em] text-[#a3a3a3]">{t("popularCompanies")}</p><div className="flex flex-wrap justify-center gap-2.5">{POPULAR_COMPANIES.map(company => <button key={company.ticker} type="button" aria-label={`${company.name} (${company.ticker})`} onClick={() => choosePopularCompany(company.ticker)} disabled={loading} className="inline-flex items-center gap-2 rounded-[10px] border border-[#e5e5e3] bg-white px-3 py-2 text-[13px] font-semibold text-[#0a0a0a] transition hover:border-[#635bff] hover:shadow-sm focus-visible:outline-2 focus-visible:outline-sky-700 disabled:opacity-60"><CompanyLogo small symbol={company.ticker} company={company.name} /><span>{company.name}</span></button>)}</div></div>
        </div>
      </section>}

      <div className={`mx-auto grid max-w-[1440px] gap-6 ${visibleReport?.scope === "company" ? "px-0 py-0 sm:px-8 sm:py-9" : "px-4 py-6 md:px-8 lg:py-9"} ${visibleReport && visibleReport.scope !== "company" ? "lg:grid-cols-[290px_minmax(0,1fr)]" : ""}`}>
        {visibleReport && visibleReport.scope !== "company" && <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:sticky lg:top-24">
          <button onClick={returnToGallery} className="mb-4 flex w-full items-center gap-2 rounded-xl bg-sky-50 px-3 py-2.5 text-sm font-semibold text-sky-900 hover:bg-sky-100"><ArrowLeft size={16} />{t("backToGallery")}</button>
          <div className="flex items-center justify-between px-2 pb-3"><div><p className="text-xs font-bold uppercase tracking-[.14em] text-sky-800">{t("libraryEyebrow")}</p><h2 className="mt-1 text-lg font-bold">{t("libraryTitle")}</h2></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">{filteredReports.length}</span></div>
          {loading && <div className="flex items-center gap-2 px-2 py-6 text-sm text-slate-500"><Loader2 className="animate-spin" size={17} />{t("loading")}</div>}
          {!loading && !error && filteredReports.length === 0 && <p className="px-2 py-4 text-sm leading-relaxed text-slate-500">{query ? t("noMatches") : t("emptyLibrary")}</p>}
          <div className="max-h-[58vh] space-y-1 overflow-y-auto">{filteredReports.map(item => <button key={item.id} aria-pressed={visibleReport.id === item.id} onClick={() => selectSavedReport(item.id)} className={`w-full rounded-xl border p-3 text-left transition hover:border-sky-200 hover:bg-sky-50 ${visibleReport.id === item.id ? "border-sky-200 bg-sky-50" : "border-transparent"}`}><span className="flex items-center justify-between gap-2"><span className="truncate text-sm font-bold text-slate-800">{item.company}</span><ChevronRight size={15} className="shrink-0 text-slate-400" /></span><span className="mt-1 block text-xs text-slate-500">{item.period} · {item.scope === "company" ? t("companyOverview") : item.kind === "transcript" ? t("transcript") : t("report")}</span><span className="mt-1 block text-[11px] text-slate-400">{item.is_public ? t("publicBadge") : t("privateBadge")} · {formatDate(item.created_at)}</span></button>)}</div>
        </aside>}

        <main className="min-w-0">
          {!visibleReport && !deleteTarget && deleteError && <p role="alert" className="mb-5 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{deleteError}</p>}
          {!visibleReport && deleteNotice && <p role="status" className="mb-5 text-sm text-slate-600">{deleteNotice}</p>}
          {error && <div role="alert" className="mb-5 flex flex-wrap items-start gap-3 rounded-2xl border border-rose-200 bg-white p-5 text-rose-800 shadow-sm"><AlertCircle className="mt-0.5 shrink-0" size={19} /><div className="min-w-0 flex-1"><p className="font-semibold">{t("errorTitle")}</p><p className="mt-1 text-sm">{error}</p></div><button onClick={retry} className="rounded-lg bg-rose-50 px-3 py-2 text-sm font-semibold hover:bg-rose-100">{t("retry")}</button><button onClick={returnToGallery} className="rounded-lg bg-slate-100 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-200">{t("backToGallery")}</button></div>}
          {loading && !visibleReport && <div role="status" className="flex min-h-[30vh] items-center justify-center gap-3 text-slate-500"><Loader2 className="animate-spin text-sky-700" />{t("loading")}</div>}
          {!loading && coverageTarget && coverageTarget.owner === userId && !visibleReport && <section aria-live="polite" className="mb-8 rounded-2xl border border-sky-100 bg-white p-6 sm:p-8"><div className="flex items-start gap-4"><CompanyLogo symbol={coverageTarget.company} company={coverageTarget.company}/><div><h2 className="text-xl font-bold">{t(coverageTarget.state === "requested" ? "coverageRequestedTitle" : "coverageUnavailableTitle", {company: coverageTarget.company})}</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{t(coverageTarget.state === "requested" ? "coverageRequestedDescription" : "coverageUnavailableDescription")}</p>{coverageTarget.state !== "requested" && <button type="button" onClick={() => void requestCoverage(coverageTarget.company)} className="mt-5 rounded-xl bg-sky-700 px-5 py-3 text-sm font-semibold text-white hover:bg-sky-800">{t("requestCoverage")}</button>}<button type="button" onClick={returnToGallery} className="ml-2 mt-5 rounded-xl px-5 py-3 text-sm font-semibold text-sky-800 hover:bg-sky-50">{t("backToGallery")}</button></div></div></section>}
          {visibleReport && visibleReport.locale !== locale && <p role="status" className="mb-4 rounded-xl bg-sky-50 p-4 text-sm text-sky-900">{t("libraryLanguageFallback", {language: t(visibleReport.locale === "pt" ? "localePortuguese" : "localeEnglish")})}</p>}
          {!loading && !visibleReport && !error && <div className="space-y-10">
            <section><div className="mb-5"><h2 className="text-xl font-bold text-slate-900">{t("companyReports")}</h2><p className="mt-1 text-sm text-slate-500">{t("companyReportsDescription")}</p></div>
              {publicCompanyReports.length > 0 ? <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{publicCompanyReports.map(item => reportCard(item, true))}</div> : <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-sm leading-relaxed text-slate-600">{query ? t("noMatches") : t("publicEmpty")}</div>}
            </section>
            {publicPeriodReports.length > 0 && <section><div className="mb-5"><h2 className="text-xl font-bold text-slate-900">{t("periodReports")}</h2><p className="mt-1 text-sm text-slate-500">{t("periodReportsDescription")}</p></div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{publicPeriodReports.map(item => reportCard(item, true))}</div></section>}
            {privateReports.length > 0 && <section><div className="mb-4"><h2 className="text-xl font-bold text-slate-900">{t("yourPrivateReports")}</h2><p className="mt-1 text-sm text-slate-500">{t("privateDescription")}</p></div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{privateReports.map(item => reportCard(item, false))}</div></section>}
          </div>}
          {visibleReport?.scope === "company" && <CompanyReportReader report={visibleReport} locale={locale} t={t} formatDate={formatDate} onBack={returnToGallery} onRefresh={() => openCompanyInLibrary(visibleReport.company)} onDashboard={() => router.push(`/${locale}/dashboard?company=${encodeURIComponent(visibleReport.company)}`)} />}
          {visibleReport && visibleReport.scope !== "company" && <article className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-6 pt-5 md:px-10"><button onClick={returnToGallery} className="mb-4 inline-flex items-center gap-2 rounded-lg px-2 py-2 text-sm font-semibold text-sky-800 hover:bg-sky-50"><ArrowLeft size={16} />{t("backToGallery")}</button></div>
            <div className="border-b border-slate-100 bg-gradient-to-br from-white via-white to-sky-50/80 p-6 md:p-10">
              <div className="mb-5 flex flex-wrap items-center gap-2"><span className="rounded-full border border-sky-100 bg-sky-50 px-3 py-1 text-xs font-bold uppercase tracking-wide text-sky-800">{visibleReport.kind === "transcript" ? t("transcript") : t("report")}</span>{reused && <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">{t("reused")}</span>}</div>
              <p className="text-xs font-bold uppercase tracking-[.15em] text-sky-800">{t("reportEyebrow")}</p><div className="mt-3 flex items-center gap-3"><CompanyLogo symbol={visibleReport.symbol || visibleReport.company} company={visibleReport.company_name || visibleReport.company} /><h1 className="min-w-0 break-words text-3xl font-bold tracking-tight text-slate-950 md:text-5xl">{visibleReport.company}</h1></div>
              <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-500"><span className="inline-flex items-center gap-2"><Building2 size={15} />{visibleReport.period}</span><span className="inline-flex items-center gap-2"><CalendarDays size={15} />{t("created", { date: formatDate(visibleReport.created_at) })}</span>{visibleReport.score !== null && <span className="font-semibold text-sky-800">{t("score", { score: visibleReport.score })}</span>}</div>
              <div className="mt-7 rounded-2xl border border-sky-100 bg-[#f3f9ff] p-5 md:p-6"><p className="mb-2 text-xs font-bold uppercase tracking-[.14em] text-sky-800">{t("thesisCallout")}</p><p className="text-lg font-medium leading-relaxed text-slate-800">{reportText(visibleReport.sections.find(section => section.id === "thesis")?.summary || visibleReport.sections.find(section => section.id === "thesis")?.paragraphs?.[0] || t("noThesis"))}</p></div>
            </div>
            {visibleReport.metrics.length > 0 && <section className="grid gap-px border-b border-slate-100 bg-slate-100 sm:grid-cols-2 xl:grid-cols-4">{visibleReport.metrics.map((metric, index) => <div key={`${metric.label}-${index}`} className="bg-white p-5 md:p-6"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{metric.label}</p><p className="mt-2 break-words text-2xl font-bold text-slate-900">{reportText(metric.value)}</p></div>)}</section>}
            <div className="grid lg:grid-cols-[220px_minmax(0,1fr)]">
              <nav aria-label={t("sectionsLabel")} className="flex gap-1 overflow-x-auto border-b border-slate-100 p-3 lg:block lg:border-b-0 lg:border-r lg:p-4">{SECTION_IDS.map(id => <button key={id} aria-current={activeSection === id ? "page" : undefined} onClick={() => setActiveSection(id)} className={`whitespace-nowrap rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition lg:mb-1 lg:w-full ${activeSection === id ? "bg-sky-50 text-sky-900" : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"}`}>{t(`sections.${id}`)}</button>)}</nav>
              <section className="min-h-[400px] p-6 md:p-10"><p className="text-xs font-bold uppercase tracking-[.14em] text-sky-800">{t("sectionLabel")}</p><h2 className="mt-2 text-2xl font-bold tracking-tight">{selectedSection?.title || t(`sections.${activeSection}`)}</h2>
                {selectedSection ? <><p className="mt-4 text-lg leading-relaxed text-slate-700">{reportText(selectedSection.summary)}</p><div className="mt-6 space-y-4 text-[15px] leading-7 text-slate-600">{selectedSection.paragraphs.map((paragraph, index) => <p key={index}>{reportText(paragraph)}</p>)}</div>{selectedSection.bullets.length > 0 && <ul className="mt-6 space-y-3">{selectedSection.bullets.map((bullet, index) => <li key={index} className="flex gap-3 text-sm leading-relaxed text-slate-700"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-sky-600" /><span>{reportText(bullet)}</span></li>)}</ul>}{sourcesFor(selectedSection.source_ids, [selectedSection.summary, ...selectedSection.paragraphs, ...selectedSection.bullets])}</> : <p className="mt-4 text-slate-500">{t("sectionUnavailable")}</p>}
              </section>
            </div>
            {(visibleReport.watchpoints.length > 0 || visibleReport.valuation) && <div className="grid gap-6 border-t border-slate-100 bg-slate-50/70 p-6 md:p-8 xl:grid-cols-2">{visibleReport.watchpoints.length > 0 && <section className="rounded-2xl border border-amber-100 bg-white p-5"><h3 className="font-bold text-slate-900">{t("watchpoints")}</h3><ul className="mt-4 space-y-3">{visibleReport.watchpoints.map((point, index) => <li key={index} className="flex gap-3 text-sm leading-relaxed text-slate-600"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" />{reportText(point)}</li>)}</ul></section>}{visibleReport.valuation && <section className="rounded-2xl border border-slate-200 bg-white p-5"><h3 className="font-bold text-slate-900">{t("valuation")}</h3><p className="mt-3 text-sm leading-relaxed text-slate-600">{visibleReport.valuation.available && visibleReport.valuation.base_eps !== null ? t("valuationBasis", { eps: visibleReport.valuation.base_eps, currency: visibleReport.valuation.currency || "" }) : visibleReport.valuation.reason || t("valuationUnavailable")}</p>
              {visibleReport.valuation.available && visibleReport.valuation.base_eps !== null && visibleReport.valuation.base_eps > 0 && <div className="mt-6 border-t border-slate-100 pt-5"><h4 className="font-semibold text-slate-900">{t("scenarioTitle")}</h4><p className="mt-1 text-xs leading-relaxed text-slate-500">{t("scenarioDisclaimer")}</p><div className="mt-4 space-y-4">{SCENARIOS.map(scenario => {
                const inputs = scenarioInputs[scenario.key];
                const value = calculateIllustrativeValue(visibleReport.valuation.base_eps!, inputs);
                const update = (field: keyof ValuationInputs, raw: string) => setScenarioInputs(current => ({ ...current, [scenario.key]: { ...current[scenario.key], [field]: Number(raw) } }));
                return <div key={scenario.key} className="rounded-xl bg-slate-50 p-3"><div className="flex items-center justify-between gap-3"><span className="text-sm font-semibold text-slate-800">{t(`scenarios.${scenario.key}`)}</span><span className="text-sm font-bold text-sky-800">{formatScenarioValue(value, visibleReport.valuation.currency)}</span></div><div className="mt-3 grid grid-cols-3 gap-2"><label className="text-[11px] font-medium text-slate-500">{t("growthInput")}<input aria-label={`${t(`scenarios.${scenario.key}`)} ${t("growthInput")}`} type="number" min="-50" max="100" step="1" value={inputs.growthPercent} onChange={event => update("growthPercent", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-800" /></label><label className="text-[11px] font-medium text-slate-500">{t("peInput")}<input aria-label={`${t(`scenarios.${scenario.key}`)} ${t("peInput")}`} type="number" min="1" max="100" step="1" value={inputs.peMultiple} onChange={event => update("peMultiple", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-800" /></label><label className="text-[11px] font-medium text-slate-500">{t("discountInput")}<input aria-label={`${t(`scenarios.${scenario.key}`)} ${t("discountInput")}`} type="number" min="0" max="50" step="1" value={inputs.discountPercent} onChange={event => update("discountPercent", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-sm text-slate-800" /></label></div></div>;
              })}</div><p className="mt-3 text-xs text-slate-500">{t("scenarioFormula")}</p></div>}
              {sourcesFor([visibleReport.valuation.source_id])}
            </section>}</div>}
            <section className="border-t border-slate-100 p-6 md:p-8">{sourcesFor(visibleReport.sources.map(source => source.id), [], true)}<p className="mt-3 text-sm text-slate-500">{t("coverageDisclaimer", { coverage: visibleReport.coverage })}</p></section>
          </article>}
        </main>
      </div>
      <ConfirmDeleteDialog subject={libraryOwnerId === userId ? deleteSubject : null} kind="report" pending={deletingId !== null} error={deleteError} onCancel={() => { if (!deletingId) { setDeleteTarget(null); setDeleteError(""); } }} onConfirm={() => { if (deleteTarget) void deletePrivateReport(deleteTarget); }} />
    </div>
  );
}
