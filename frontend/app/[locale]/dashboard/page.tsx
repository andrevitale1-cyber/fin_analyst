"use client";
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth, useUser, UserButton } from "@clerk/nextjs";
import { useTranslations, useLocale } from "next-intl";
import { formatPeriod, splitBold } from "../../../lib/analysisText";
import DashboardSidebar from "../../../components/DashboardSidebar";
import ReportFeedback from "../../../components/ReportFeedback";
import LanguageSwitcher from "../../../components/LanguageSwitcher";
import CompanyLogo from "../../../components/CompanyLogo";
import ConfirmDeleteDialog from "../../../components/ConfirmDeleteDialog";
import {
  LayoutDashboard, History, UploadCloud, FileText, ChevronLeft,
  BarChart3, TrendingUp, DollarSign, Percent, Loader2,
  AlertCircle, Table as TableIcon, Trash2, ArrowUpDown, ArrowUp, ArrowDown,
  GripVertical, Eye, EyeOff, Settings2, X, Zap, Lock, Check, Menu,
  Search, ArrowRight, Sparkles, ExternalLink, BookOpen
} from "lucide-react";

// API_BASE configurada para o seu Render
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "https://api-finanalyzer.onrender.com";
const STRIPE_CHECKOUT_URL_MONTHLY = "https://buy.stripe.com/bJe3cwgdleEBfiJ9rT67S00";
const STRIPE_CHECKOUT_URL_YEARLY  = "https://buy.stripe.com/3cI6oIgdleEBgmNdI967S01"; 

const getColumnDefinitions = (t: any) => [
  { key: 'empresa', label: t('company'), align: 'center', minWidth: 'min-w-[140px]', color: 'text-slate-900 font-medium' },
  { key: 'nota_geral', label: t('finalScore'), align: 'center', color: 'text-sky-700 font-bold' },
  { key: 'receita_nota', label: t('netRevenue'), align: 'center', color: 'text-slate-600' },
  { key: 'lucro_nota', label: t('netIncome'), align: 'center', color: 'text-slate-600' },
  { key: 'divida_nota', label: t('netDebt'), align: 'center', color: 'text-slate-600' },
  { key: 'rentabilidade_nota', label: t('profitability'), align: 'center', color: 'text-slate-600' },
  { key: 'soma_total', label: t('sum'), align: 'center', bg: 'bg-slate-50/70', color: 'text-slate-600' },
  { key: 'qtde_tri', label: t('analyzedResults'), align: 'center', bg: 'bg-slate-50/70', color: 'text-slate-600' },
  { key: 'media', label: t('average'), align: 'center', bg: 'bg-slate-50/70', color: 'text-slate-600' },
  { key: 'last_analysed_quarter', label: t('lastQuarter'), align: 'center', color: 'text-slate-500 font-medium' },
];

function UpgradeModal({ onClose, userId, billingCycle: initialBillingCycle = 'monthly', isExpired = false }: { onClose?: () => void; userId?: string; billingCycle?: 'monthly' | 'yearly'; isExpired?: boolean }) {
  const locale = useLocale();
  const en = locale === 'en';
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>(initialBillingCycle);
  const handleCheckout = () => {
    const url = new URL(billingCycle === 'yearly' ? STRIPE_CHECKOUT_URL_YEARLY : STRIPE_CHECKOUT_URL_MONTHLY);
    if (userId) url.searchParams.set('client_reference_id', userId);
    window.open(url.toString(), '_blank');
  };
  const plans = [
    { premium: true, name: 'Premium', description: en ? 'More tools for your investment research.' : 'Mais ferramentas para suas pesquisas de investimento.', features: en ? ['Quarterly results and earnings calls', 'Aggregated table and analysis history', 'Public and private company reports', 'Company comparison and PDF export'] : ['Resultados trimestrais e calls', 'Tabela agregada e histórico de análises', 'Relatórios públicos e privados', 'Comparação de empresas e exportação em PDF'] },
    { premium: false, name: en ? 'Free' : 'Grátis', description: en ? 'Start exploring financial research.' : 'Comece a explorar pesquisas financeiras.', features: en ? ['3 quarterly or call analyses per day', '1 company report per day', 'Access to public company reports', 'Analysis history'] : ['3 análises trimestrais ou de calls por dia', '1 relatório de empresa por dia', 'Acesso aos relatórios públicos', 'Histórico de análises'] },
  ];
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-[#050519]/80 p-3 backdrop-blur-sm sm:p-4">
      <div role="dialog" aria-modal="true" aria-labelledby="plans-title" className="relative max-h-[calc(100dvh-1.5rem)] w-full max-w-4xl overflow-y-auto rounded-2xl border border-white/15 bg-[#0a0a1f] p-5 text-white shadow-2xl sm:p-8">
        {!isExpired && onClose && <button onClick={onClose} aria-label={en ? 'Close' : 'Fechar'} className="absolute right-4 top-4 z-10 rounded-lg p-2 text-white/60 hover:bg-white/10 hover:text-white"><X size={20} /></button>}
        <div className="mb-7 pr-8 text-center"><h2 id="plans-title" className="text-2xl font-bold tracking-tight">{en ? 'Choose your plan' : 'Escolha seu plano'}</h2><p className="mt-2 text-sm text-white/65">{en ? 'More clarity for every investment decision.' : 'Mais clareza para cada decisão de investimento.'}</p>
          <div role="group" aria-label={en ? 'Billing period' : 'Período de cobrança'} className="mt-5 inline-flex rounded-md border border-white/20 bg-white/5 p-1">
            {(['monthly', 'yearly'] as const).map(cycle => <button key={cycle} type="button" aria-pressed={billingCycle === cycle} onClick={() => setBillingCycle(cycle)} className={`rounded px-4 py-2 text-sm font-semibold transition ${billingCycle === cycle ? 'bg-[#1a1aff] text-white' : 'text-white/60 hover:text-white'}`}>{cycle === 'monthly' ? (en ? 'Monthly' : 'Mensal') : (en ? 'Yearly' : 'Anual')}</button>)}
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">{plans.map(plan => <article key={plan.name} className={`flex min-w-0 flex-col rounded-xl border p-6 ${plan.premium ? 'border-[#2beb78] bg-[radial-gradient(circle_at_top,_#1a1aff4d,_transparent_70%)]' : 'border-white/20 bg-white/5'}`}>
          <div className="mb-5"><div className="flex items-center justify-between gap-2"><h3 className="flex items-center gap-2 text-xl font-semibold">{plan.premium ? <Sparkles size={19} /> : <Zap size={19} />}{plan.name}</h3>{plan.premium && <span className="rounded-md bg-[#1d423b] px-2 py-1 text-xs font-bold text-[#2beb78]">{en ? 'Full access' : 'Acesso completo'}</span>}</div>
            <p className="mt-2 min-h-[40px] text-sm leading-5 text-white/60">{plan.description}</p>
            <p className="mt-5 flex items-baseline gap-1"><strong className="text-3xl font-bold">{plan.premium ? (billingCycle === 'monthly' ? 'R$ 29' : 'R$ 290') : 'R$ 0'}</strong><span className="text-sm text-white/50">{plan.premium ? (billingCycle === 'monthly' ? (en ? '/ month' : '/ mês') : (en ? '/ year' : '/ ano')) : ''}</span></p></div>
          <ul className="flex-1">{plan.features.map(feature => <li key={feature} className="flex items-start justify-between gap-3 border-t border-white/10 py-3 text-sm leading-5 text-white/85"><span>{feature}</span><Check size={18} className="shrink-0 text-[#2beb78]" aria-hidden="true" /></li>)}</ul>
          {plan.premium ? <button onClick={handleCheckout} className="mt-5 w-full rounded-md bg-[#1a1aff] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#4032ff]">{en ? 'Choose Premium' : 'Escolher Premium'}</button> : !isExpired && onClose ? <button onClick={onClose} className="mt-5 w-full rounded-md border border-white/25 px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/10">{en ? 'Continue with Free' : 'Continuar com Grátis'}</button> : null}
        </article>)}</div>
      </div>
    </div>
  );
}

export default function FinancialDashboard() {
  const router = useRouter();
  const t = useTranslations("Dashboard");
  const locale = useLocale();
  const COLUMN_DEFINITIONS = getColumnDefinitions(t);
  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  const deleteText = useTranslations("DeleteDialog");
  const [pendingDelete, setPendingDelete] = useState<{ id: number; company: string; detail: string; owner: string } | null>(null);
  const [deletingHistory, setDeletingHistory] = useState(false);
  const [deleteHistoryError, setDeleteHistoryError] = useState("");
  const deleteSubject = useMemo(() => pendingDelete ? { company: pendingDelete.company, symbol: pendingDelete.company, detail: pendingDelete.detail } : null, [pendingDelete]);
  const accountRef = useRef(user?.id);
  accountRef.current = user?.id;
  useEffect(() => { setPendingDelete(null); setDeletingHistory(false); setDeleteHistoryError(""); }, [user?.id]);

  const [currentView, setCurrentView] = useState<'dashboard' | 'history' | 'result' | 'table'>('dashboard');
  const [loading, setLoading] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Estado para escolher qual tipo de análise
  const [tipoAnalise, setTipoAnalise] = useState<'pdf' | 'auto'>('auto');
  const [tipoDocumento, setTipoDocumento] = useState<'report' | 'transcript'>('report');
  const [analysisError, setAnalysisError] = useState("");

  // --- TRIAL STATE ---
  const [trialState, setTrialState] = useState<{ userId: string; status: 'pending' | 'active' | 'expired' | 'unavailable'; daysLeft: number | null }>({ userId: '', status: 'pending', daysLeft: null });
  const [dailyRemaining, setDailyRemaining] = useState<{ analysis: number | null; full: number | null }>({ analysis: null, full: null });
  const [accessRetry, setAccessRetry] = useState(0);

  const [result, setResult] = useState<any>(null);
  const [translatedThesis, setTranslatedThesis] = useState<string | null>(null);
  const [translationStatus, setTranslationStatus] = useState<'idle' | 'loading' | 'error'>('idle');
  const translationCache = useRef<Record<string, string>>({});
  const [historyList, setHistoryList] = useState<any[]>([]);
  const [tableData, setTableData] = useState<any[]>([]);

  useEffect(() => {
    setTranslatedThesis(null);
    setTranslationStatus('idle');
    if (currentView !== 'result' || !result?.id || result.metadata?.tipo === 'Earnings Call') return;
    const text = String(result.analise_completa || '');
    const sourceLocale = /\bSection\s+[1-6]\s*:/i.test(text) ? 'en' : /\bSe[cç][aã]o\s+[1-6]\s*:/i.test(text) ? 'pt' : result.metadata?.locale || null;
    if (!sourceLocale || sourceLocale === locale) return;
    const key = `${result.id}:${locale}`;
    if (translationCache.current[key]) { setTranslatedThesis(translationCache.current[key]); return; }
    const controller = new AbortController();
    setTranslationStatus('loading');
    getToken().then(token => {
      if (!token) throw new Error('Authentication unavailable');
      return fetch(`${API_BASE}/api/history/${result.id}/translation`, { method: 'POST', signal: controller.signal, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ locale }) });
    }).then(response => { if (!response.ok) throw new Error('Translation failed'); return response.json(); })
      .then(data => { if (typeof data.text !== 'string' || !data.text.trim()) throw new Error('Empty translation'); translationCache.current[key] = data.text; setTranslatedThesis(data.text); setTranslationStatus('idle'); })
      .catch(() => { if (!controller.signal.aborted) setTranslationStatus('error'); });
    return () => controller.abort();
  }, [currentView, result?.id, locale, getToken]);

  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [showColumnMenu, setShowColumnMenu] = useState(false);
  const columnMenuRef = useRef<HTMLDivElement>(null);
  const [columnOrder, setColumnOrder] = useState<string[]>(COLUMN_DEFINITIONS.map(c => c.key));
  const [draggedItemIndex, setDraggedItemIndex] = useState<number | null>(null);
  const [visibleColumns, setVisibleColumns] = useState<Record<string, boolean>>({
    empresa: true, ano: true, trimestre: true, nota_final: true, soma_total: true,
    qtde_tri: true, media: true, last_analysed_quarter: true, receita_nota: false,
    lucro_nota: true, divida_nota: false, rentabilidade_nota: false
  });
  
  const [empresa, setEmpresa] = useState("");
  const [ano, setAno] = useState("");
  const [trimestre, setTrimestre] = useState("1T");
  const [file, setFile] = useState<File | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const view = params.get("view");
    if (view === "history" || view === "table") setCurrentView(view);
    const company = params.get("company")?.trim() || "";
    if (company && company.length <= 100 && !/[\u0000-\u001f]/.test(company)) setEmpresa(company);
  }, []);

  const isPremium = user?.publicMetadata?.plan === 'premium';
  const accessStatus = isPremium ? 'active' : trialState.userId === user?.id ? trialState.status : 'pending';
  const trialDaysLeft = accessStatus === 'active' ? trialState.daysLeft : null;
  const isTrialExpired = accessStatus === 'expired';

  // --- Verificar acesso ao trial no backend ---
  useEffect(() => {
    if (!isLoaded || !user?.id) return;
    const userId = user.id;
    setShowUpgradeModal(false);

    // Verifica o trial no backend
    const controller = new AbortController();
    let active = true;
    const timeout = setTimeout(() => controller.abort(), 20_000);
    setTrialState({ userId, status: 'pending', daysLeft: null });
    getToken().then(token => {
      if (!token) throw new Error('Authentication unavailable');
      return fetch(`${API_BASE}/api/check-access?user_id=${userId}`, { signal: controller.signal, headers: { Authorization: `Bearer ${token}` } });
    })
      .then(response => {
        if (!response.ok) throw new Error('Access check failed');
        return response.json();
      })
      .then(data => {
        if (!active) return;
        if (typeof data.has_access !== 'boolean') throw new Error('Invalid access response');
        const status = data.has_access ? 'active' : 'expired';
        setTrialState({ userId, status, daysLeft: typeof data.days_left === 'number' ? data.days_left : null });
        setDailyRemaining({ analysis: data.analysis_remaining ?? null, full: data.full_report_remaining ?? null });
      })
      .catch(() => {
        if (active) setTrialState({ userId, status: 'unavailable', daysLeft: null });
      })
      .finally(() => clearTimeout(timeout));
    return () => { active = false; clearTimeout(timeout); controller.abort(); };
  }, [isLoaded, user?.id, isPremium, accessRetry, getToken]);

  const formatarData = (dataString: string) => {
    if (!dataString) return "-";
    try { return new Intl.DateTimeFormat('pt-BR', {day: '2-digit', month: '2-digit', year: 'numeric'}).format(new Date(dataString)); } 
    catch (e) { return dataString; }
  };

  const columnDefsMap = useMemo(() => COLUMN_DEFINITIONS.reduce((acc, col) => { acc[col.key] = col; return acc; }, {} as any), []);
  const visibleCount = useMemo(() => Object.values(visibleColumns).filter(Boolean).length, [visibleColumns]);

  const fetchHistory = async () => {
    if (!user) return;
    try {
      const res = await fetch(`${API_BASE}/api/history?user_id=${user.id}`);
      setHistoryList(await res.json());
    } catch (error) { console.error("Erro histórico", error); }
  };

  const fetchTableData = async () => {
    if (!user) return;
    try {
      const res = await fetch(`${API_BASE}/api/table-data?user_id=${user.id}`);
      setTableData(await res.json());
    } catch (error) { console.error("Erro tabela", error); }
  };

  const handleDelete = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    const item = historyList.find(item => item.id === id);
    if (!item || !user) return;
    setDeleteHistoryError("");
    setPendingDelete({ id, company: item.empresa, detail: formatPeriod(item.periodo, locale), owner: user.id });
  };

  const confirmHistoryDelete = async () => {
    if (!pendingDelete || deletingHistory || pendingDelete.owner !== user?.id) return;
    const target = pendingDelete;
    setDeletingHistory(true); setDeleteHistoryError("");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30_000);
    try {
      const token = await getToken();
      if (!token) throw new Error("missing_token");
      const response = await fetch(`${API_BASE}/api/history/${target.id}`, { method: 'DELETE', signal: controller.signal, headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error("delete_failed");
      if (accountRef.current !== target.owner) return;
      setHistoryList(items => items.filter(item => item.id !== target.id));
      setPendingDelete(null);
      void fetchTableData();
    } catch {
      if (accountRef.current === target.owner) setDeleteHistoryError(deleteText("error"));
    } finally {
      clearTimeout(timeout);
      if (accountRef.current === target.owner) setDeletingHistory(false);
    }
  };

  const handleNavClick = (view: 'dashboard' | 'history' | 'table') => {
    setIsSidebarOpen(false);
    if (view === 'table' && !isPremium) { setShowUpgradeModal(true); return; }
    setCurrentView(view);
  };

  const handleAnalyze = async () => {
    const isAuto = tipoAnalise === 'auto';
    setAnalysisError("");
    if (!empresa.trim() || !/^\d{4}$/.test(ano) || (!isAuto && !file)) {
      setAnalysisError(t("newAnalysis.requiredFields"));
      return;
    }
    if (!user) return;

    // Bloqueia se trial expirado e não é premium
    if (!isPremium && accessStatus !== 'active') {
      if (isTrialExpired) setShowUpgradeModal(true);
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("ano", ano);
      formData.append("trimestre", trimestre);
      formData.append("user_id", user.id);
      formData.append("locale", locale);

      let urlBackend: string;
      const isTranscript = tipoDocumento === 'transcript';
      if (isAuto && isTranscript) {
        urlBackend = `${API_BASE}/api/analyze-call-auto`;
        formData.append("company", empresa.trim());
      } else if (isAuto) {
        urlBackend = `${API_BASE}/api/analyze-auto`;
        formData.append("ticker", empresa.trim());
      } else if (isTranscript) {
        urlBackend = `${API_BASE}/api/analyze-call`;
        formData.append("empresa", empresa.trim());
        formData.append("file", file!);
      } else {
        urlBackend = `${API_BASE}/api/analyze`;
        formData.append("empresa", empresa.trim());
        formData.append("file", file!);
      }

      const token = await getToken();
      if (!token) throw new Error(t("newAnalysis.genericError"));
      const response = await fetch(urlBackend, { method: "POST", body: formData, headers: { Authorization: `Bearer ${token}` } });

      if (response.status === 403) { setLoading(false); setShowUpgradeModal(true); return; }
      if (!response.ok) {
        if (response.status === 503) throw new Error(t("newAnalysis.serviceUnavailable"));
        let errorMsg = "Erro na API do Servidor.";
        try {
          const err = await response.json();
          errorMsg = err.detail || errorMsg;
        } catch (e) {
          errorMsg = `Falha de Conexão (Status ${response.status}). O servidor demorou muito a responder ou reiniciou. Tente novamente com um PDF mais pequeno.`;
        }
        throw new Error(errorMsg);
      }

      const data = await response.json();
      setResult({ ...data, id: data.id });
      setCurrentView('result');
      fetchHistory();
      fetchTableData();
      setAccessRetry(value => value + 1);
    } catch (error: any) {
      console.error(error);
      setAnalysisError(error.message || t("newAnalysis.genericError"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) { 
        if (currentView === 'history') fetchHistory();
        if (currentView === 'table' && isPremium) fetchTableData();
    }
    const handleClickOutside = (e: MouseEvent) => {
      if (columnMenuRef.current && !columnMenuRef.current.contains(e.target as Node)) setShowColumnMenu(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [currentView, user, isPremium]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) setFile(e.target.files[0]);
  };

  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key) direction = sortConfig.direction === 'asc' ? 'desc' : 'asc';
    setSortConfig({ key, direction });
  };

  const toggleColumn = (key: string) => setVisibleColumns(prev => ({ ...prev, [key]: !prev[key] }));
  const onDragStart = (index: number) => setDraggedItemIndex(index);
  const onDragEnter = (index: number) => {
    if (draggedItemIndex === null || draggedItemIndex === index) return;
    const newOrder = [...columnOrder];
    const item = newOrder[draggedItemIndex];
    newOrder.splice(draggedItemIndex, 1);
    newOrder.splice(index, 0, item);
    setColumnOrder(newOrder);
    setDraggedItemIndex(index);
  };
  const onDragEnd = () => setDraggedItemIndex(null);

  const filteredHistory = useMemo(() => {
    if (!searchQuery.trim()) return historyList;
    const q = searchQuery.toLowerCase();
    return historyList.filter((item: any) =>
      item.empresa?.toLowerCase().includes(q) ||
      (item.periodo?.toLowerCase().includes(q) || formatPeriod(item.periodo, locale).toLowerCase().includes(q))
    );
  }, [historyList, searchQuery, locale]);

  const sortedTableData = useMemo(() => {
    if (!sortConfig) return tableData;
    return [...tableData].sort((a, b) => {
      const valA = a[sortConfig.key];
      const valB = b[sortConfig.key];
      const numA = Number(valA);
      const numB = Number(valB);
      if (!isNaN(numA) && !isNaN(numB)) {
        return sortConfig.direction === 'asc' ? numA - numB : numB - numA;
      }
      if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
      if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [tableData, sortConfig]);

  const renderCellContent = (item: any, key: string, colDef: any) => {
    if (key === 'empresa') return <span className={`${colDef.color || 'text-slate-900'} font-bold`}>{item[key]?.toString().toUpperCase()}</span>;
    if (key === 'last_analysed_quarter') return <span className={colDef.color}>{formatPeriod(item[key], locale)}</span>;
    if (key === 'trimestre') return <span className="bg-sky-50 text-sky-700 py-1 px-2 rounded text-xs font-bold border border-blue-500/20">{formatPeriod(item[key], locale)}</span>;
    if (key === 'media') return <span className={`px-2 py-1 rounded font-bold ${item.media >= 4 ? 'text-emerald-700' : 'text-amber-700'}`}>{item[key]}</span>;
    if (key.includes('nota') || key === 'nota_final') {
      const val = item[key];
      return <span className={`font-bold text-base ${val >= 4 ? 'text-emerald-700' : val >= 3 ? 'text-amber-700' : 'text-red-600'}`}>{val}</span>;
    }
    return <span className={`${colDef.color || 'text-slate-600'}`}>{item[key]}</span>;
  };

  if (!isLoaded || !user) return <div className="flex h-screen flex-col items-center justify-center gap-3 bg-[#0E1117] text-sm text-gray-300" role="status"><Loader2 className="animate-spin text-blue-500" />{t("auth.loading")}</div>;

  return (
    <div className="flex h-screen bg-[#08101e] text-gray-100 font-sans overflow-hidden">
      {showUpgradeModal && (
        <UpgradeModal
          onClose={isTrialExpired ? undefined : () => setShowUpgradeModal(false)}
          userId={user?.id}
          isExpired={isTrialExpired}
        />
      )}
      
      <DashboardSidebar active={currentView} open={isSidebarOpen} collapsed={isSidebarCollapsed} onClose={() => setIsSidebarOpen(false)} onCollapse={setIsSidebarCollapsed} onNavigate={view => view === "reports" ? router.push(`/${locale}/dashboard/reports`) : handleNavClick(view)}>
        {!isPremium && !isSidebarCollapsed && accessStatus === 'active' && (
          <div className="mt-auto mb-6 px-2">
            <div className="rounded-xl border border-white/10 bg-white/[0.04] p-4">
              <div className="flex items-center justify-between gap-2"><p className="text-xs font-semibold uppercase tracking-wider text-white/60">{locale === 'en' ? 'Your plan' : 'Seu plano'}</p><span className="rounded-full bg-white/10 px-2 py-1 text-[10px] font-bold text-white">{locale === 'en' ? 'FREE' : 'GRÁTIS'}</span></div>
              <div className="mt-4 flex items-end justify-between gap-2"><div><p className="text-sm font-semibold text-white">{locale === 'en' ? 'Analyses remaining' : 'Análises restantes'}</p><p className="mt-1 text-xs leading-4 text-slate-400">{locale === 'en' ? 'Quarterly results and calls' : 'Resultados trimestrais e calls'}</p></div><span className="whitespace-nowrap text-lg font-bold text-white">{dailyRemaining.analysis ?? '—'}<span className="text-xs font-normal text-slate-400"> / 3</span></span></div>
              <p className="mt-3 border-t border-white/10 pt-3 text-xs leading-4 text-slate-400">{locale === 'en' ? 'Resets daily at midnight (São Paulo).' : 'Renova diariamente à meia-noite (São Paulo).'}</p>
              <button onClick={() => setShowUpgradeModal(true)} className="mt-4 flex w-full items-center justify-center gap-2 rounded-md bg-[#1a1aff] px-3 py-2.5 text-xs font-bold text-white transition hover:bg-[#4032ff]"><Sparkles size={14} />{t("sidebar.goPremium")}</button>
            </div>
          </div>
        )}
        
      </DashboardSidebar>
      <main className="flex-1 min-w-0 overflow-y-auto p-4 md:p-8 relative bg-[#f7f8fc] text-slate-900">
        <div className="md:hidden flex items-center justify-between mb-6 pb-4 border-b border-gray-800">
          <div className="flex items-center gap-3"><button onClick={() => setIsSidebarOpen(true)} aria-label={locale === 'en' ? 'Open menu' : 'Abrir menu'} className="flex h-11 w-11 items-center justify-center rounded-lg text-slate-600 transition hover:bg-slate-100 active:scale-95 focus-visible:outline-2 focus-visible:outline-sky-600"><Menu size={24} /></button><span className="font-bold text-lg tracking-tight text-slate-900">FinAnalyzer <span className="text-blue-500">.AI</span></span></div>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <UserButton appearance={{ elements: { avatarBox: "w-8 h-8" } }} />
          </div>
        </div>

        {currentView === 'table' && (
          <div className="animate-in fade-in duration-500 max-w-6xl mx-auto pb-20">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 rounded-[2rem] border border-slate-200 bg-white/90 p-6 md:p-10 shadow-[0_24px_70px_rgba(38,57,94,0.10)]">
              <div><h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">{t("table.title")}</h1><p className="text-slate-500 mt-1 text-sm md:text-base">{t("table.desc")}</p></div>
              <div className="relative" ref={columnMenuRef}>
                <button onClick={() => setShowColumnMenu(!showColumnMenu)} className={`flex items-center gap-2 border px-4 py-2 rounded-xl transition-all shadow-lg w-full md:w-auto justify-center ${showColumnMenu ? 'bg-blue-600 border-blue-500 text-white' : 'bg-white/90 border-slate-200 hover:border-blue-500 text-slate-600'}`}><Settings2 size={18} /><span>{t("table.configColumns")}</span></button>
                {showColumnMenu && (
                  <div className="absolute right-0 mt-3 w-80 max-w-[calc(100vw-4rem)] bg-white/95 backdrop-blur-md border border-slate-200 rounded-2xl shadow-2xl z-50 overflow-hidden animate-in fade-in zoom-in-95 origin-top-right">
                    <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50"><span className="text-sm font-bold text-slate-900">{t("table.columnView")}</span><button onClick={() => setShowColumnMenu(false)} className="text-slate-500 hover:text-sky-700"><X size={16} /></button></div>
                    <div className="p-2 max-h-[400px] overflow-y-auto space-y-1">
                      <p className="px-2 py-1 text-xs text-slate-500 font-medium uppercase tracking-wider mb-2">{t("table.dragToReorder")}</p>
                      {columnOrder.map((colKey, index) => {
                        const col = columnDefsMap[colKey];
                        const isVisible = visibleColumns[colKey];
                        return (
                          <div key={colKey} draggable onDragStart={() => onDragStart(index)} onDragEnter={() => onDragEnter(index)} onDragEnd={onDragEnd} onClick={() => toggleColumn(colKey)} className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all border border-transparent ${draggedItemIndex === index ? 'bg-sky-100 border-blue-500/50 opacity-50' : 'hover:bg-slate-100 hover:border-slate-200'}`}>
                            <div className="flex items-center gap-3"><div className="cursor-grab text-slate-400 hover:text-slate-600"><GripVertical size={16} /></div><span className={`text-sm font-medium ${isVisible ? 'text-slate-900' : 'text-slate-500'}`}>{col.label}</span></div>
                            <div className={`p-1.5 rounded-lg transition-colors ${isVisible ? 'bg-blue-500/10 text-sky-700' : 'bg-slate-100 text-slate-400'}`}>{isVisible ? <Eye size={14} /> : <EyeOff size={14} />}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </header>
            <div className="bg-white/90 border border-slate-200 rounded-2xl shadow-[0_18px_55px_rgba(38,57,94,0.08)] flex flex-col overflow-hidden">
              <div className="overflow-x-auto w-full">
                <table className={`text-left border-collapse ${visibleCount > 8 ? 'min-w-[1200px]' : 'w-full'}`}>
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
                      {columnOrder.map((colKey, index) => {
                        const col = columnDefsMap[colKey];
                        if (!visibleColumns[colKey]) return null;
                        const isDragging = draggedItemIndex === index;
                        return (
                          <th key={col.key} draggable onDragStart={() => onDragStart(index)} onDragEnter={() => onDragEnter(index)} onDragEnd={onDragEnd} onDragOver={(e) => e.preventDefault()} onClick={() => handleSort(col.key)} className={`py-3 px-3 font-semibold transition-all relative group select-none cursor-grab active:cursor-grabbing ${col.color || ''} ${col.minWidth || ''} ${isDragging ? 'opacity-30 bg-blue-500/10 border-2 border-dashed border-blue-500' : 'hover:bg-slate-100'}`} style={{ textAlign: col.align as any }}>
                            <div className={`flex items-center gap-2 ${col.align === 'center' ? 'justify-center' : ''}`}><GripVertical size={12} className="text-slate-400 group-hover:text-slate-500 transition-colors opacity-0 group-hover:opacity-100" />{col.label}{sortConfig?.key === col.key ? (sortConfig?.direction === 'asc' ? <ArrowUp size={12} className="text-sky-700"/> : <ArrowDown size={12} className="text-sky-700"/>) : <ArrowUpDown size={12} className="opacity-0 group-hover:opacity-30 transition-opacity"/>}</div>
                          </th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {sortedTableData.map((item: any) => (
                      <tr key={item.id} className="hover:bg-sky-50/60 transition-colors group">
                        {columnOrder.map(colKey => {
                          const col = columnDefsMap[colKey];
                          if (!visibleColumns[colKey]) return null;
                          return <td key={`${item.id}-${col.key}`} className={`py-3 px-3 ${col.align === 'center' ? 'text-center' : ''} ${col.bg || ''}`}>{renderCellContent(item, col.key, col)}</td>;
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {sortedTableData.length === 0 && <div className="p-12 text-center text-slate-500">{t("table.empty")}</div>}
            </div>
          </div>
        )}
        
        {currentView === 'history' && (
          <div className="animate-in fade-in duration-500 max-w-6xl mx-auto">
            <header className="flex flex-col gap-4 md:flex-row md:items-center justify-between mb-8 rounded-[2rem] border border-slate-200 bg-white/90 p-6 md:p-10 shadow-[0_24px_70px_rgba(38,57,94,0.10)]">
              <div><h1 className="text-3xl font-bold text-slate-900 tracking-tight">{t("historyView.title")}</h1><p className="text-slate-500 mt-1">{t("historyView.desc")}</p></div>
              <div className="relative">
                <input type="text" placeholder={t("historyView.searchPlaceholder")} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="bg-white/90 border border-slate-200 rounded-xl px-4 py-2.5 pl-10 text-sm text-slate-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all w-full md:w-64" />
                <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
                {searchQuery && <button onClick={() => setSearchQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-sky-700 transition-colors"><X size={14} /></button>}
              </div>
            </header>
            <div className="bg-white/90 border border-slate-200 rounded-2xl shadow-[0_18px_55px_rgba(38,57,94,0.08)] overflow-hidden">
             <div className="overflow-x-auto">
              <table className="w-full min-w-[800px] text-left border-collapse">
                <thead><tr className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wider text-slate-500"><th className="py-5 px-6 font-semibold">{t("company")}</th><th className="py-5 px-6 font-semibold">{t("historyView.period")}</th><th className="py-5 px-6 font-semibold">{t("historyView.date")}</th><th className="py-5 px-6 text-center font-semibold">{t("historyView.score")}</th><th className="py-5 px-6 text-right font-semibold">{t("historyView.actions")}</th></tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredHistory.map((item: any) => (
                    <tr key={item.id} className="hover:bg-sky-50/60 transition-colors group cursor-pointer" onClick={() => {
                      setResult({ ...item.conteudo, id: item.id }); 
                      setEmpresa(item.empresa); 
                      setCurrentView('result'); 
                    }}>
                      <td className="py-4 px-6"><div className="flex items-center gap-3"><span className="font-medium text-slate-900">{item.empresa?.toUpperCase()}</span></div></td>
                      <td className="py-4 px-6 text-slate-500">{formatPeriod(item.periodo, locale)}</td>
                      <td className="py-4 px-6 text-slate-500 text-sm">{formatarData(item.data)}</td>
                      <td className="py-4 px-6 text-center">
                        {item.nota > 0 ? (
                          <span className={`inline-flex items-center justify-center w-12 h-8 rounded-lg text-sm font-bold ${item.nota >= 4 ? 'bg-emerald-500/10 text-emerald-700 border border-emerald-500/20' : item.nota >= 3 ? 'bg-amber-500/10 text-amber-700 border border-amber-500/20' : 'bg-red-500/10 text-red-600 border border-red-500/20'}`}>{item.nota}</span>
                        ) : (
                          <span className="text-purple-600 text-xs bg-purple-500/10 border border-purple-500/20 px-2 py-1 rounded-md font-semibold">CALL</span>
                        )}
                      </td>
                      <td className="py-4 px-6 text-right"><div className="flex items-center justify-end gap-3"><button onClick={(e) => handleDelete(e, item.id)} className="flex h-11 w-11 items-center justify-center text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title={deleteText("confirm")} aria-label={`${deleteText("confirm")}: ${item.empresa}`}><Trash2 size={16} /></button><button className="text-sm font-medium text-sky-700 hover:text-sky-700 transition-colors flex items-center gap-1">{t("historyView.details")} <ChevronLeft className="w-4 h-4 rotate-180" /></button></div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
             </div> 
              {filteredHistory.length === 0 && <div className="p-12 text-center text-slate-500">{searchQuery ? `Nenhum resultado para "${searchQuery}".` : t("historyView.empty")}</div>}
            </div>
          </div>
        )}

        {currentView === 'dashboard' && (
          <section className="relative isolate min-h-full animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-6xl mx-auto pb-12">
            <div aria-hidden="true" className="pointer-events-none absolute -left-32 top-20 -z-10 h-80 w-80 rounded-full bg-cyan-200/60 blur-3xl" />
            <div aria-hidden="true" className="pointer-events-none absolute -right-24 top-[28rem] -z-10 h-96 w-96 rounded-full bg-violet-200/50 blur-3xl" />
            <div aria-hidden="true" className="pointer-events-none absolute right-[18%] top-10 -z-10 h-36 w-36 rotate-12 rounded-[2rem] bg-amber-200/45 blur-2xl" />
            <div className="relative overflow-hidden rounded-[2rem] border border-slate-200 bg-white/90 px-6 py-8 shadow-[0_24px_70px_rgba(38,57,94,0.10)] backdrop-blur md:px-10 md:py-10">
              <div className="pointer-events-none absolute -right-16 -top-24 h-72 w-72 rounded-full border-[36px] border-cyan-100/70" />
              <div className="relative max-w-3xl">
                <h1 className="text-3xl font-semibold leading-tight tracking-tight text-slate-900 md:text-5xl">{t("newAnalysis.title")}</h1>
                <p className="mt-4 text-sm leading-relaxed text-slate-600 md:text-base">{t("newAnalysis.desc")}</p>
              </div>
            </div>

            {loading ? (
              <div className="mt-6 flex min-h-80 flex-col items-center justify-center rounded-3xl border border-slate-200 bg-white/90 px-6 text-center shadow-lg shadow-slate-200/50">
                <Loader2 className="mb-5 h-12 w-12 animate-spin text-sky-500" />
                <h2 className="text-2xl font-semibold text-slate-900">{t("newAnalysis.analyzing")}</h2>
                <p className="mt-2 max-w-lg text-sm text-slate-500">{t("newAnalysis.processing")}</p>
              </div>
            ) : (
              <>
                <div className="mt-7 grid gap-3 md:grid-cols-2">
                  {([
                    { id: 'auto' as const, icon: <Search size={20} />, title: t("newAnalysis.autoSearch"), desc: t("newAnalysis.autoModeDesc") },
                    { id: 'pdf' as const, icon: <UploadCloud size={20} />, title: t("newAnalysis.manualMode"), desc: t("newAnalysis.manualModeDesc") },
                  ]).map(mode => (
                    <button key={mode.id} type="button" aria-pressed={tipoAnalise === mode.id} onClick={() => { setTipoAnalise(mode.id); setAnalysisError(""); }} className={`rounded-2xl border p-5 text-left transition-all duration-200 hover:-translate-y-0.5 ${tipoAnalise === mode.id ? 'border-sky-400 bg-sky-50 shadow-[0_12px_36px_rgba(14,86,150,0.12)]' : 'border-slate-200 bg-white hover:border-slate-300'}`}>
                      <span className={`mb-4 flex h-10 w-10 items-center justify-center rounded-xl ${tipoAnalise === mode.id ? 'bg-sky-100 text-sky-700' : 'bg-slate-100 text-slate-500'}`}>{mode.icon}</span>
                      <span className="block text-sm font-semibold text-slate-900">{mode.title}</span>
                      <span className="mt-1 block text-xs leading-relaxed text-slate-500">{mode.desc}</span>
                    </button>
                  ))}
                </div>

                <div className="mt-5">
                  <div className="rounded-3xl border border-slate-200 bg-white/90 p-5 shadow-[0_18px_55px_rgba(38,57,94,0.08)] md:p-7">
                    <div className="mb-6 flex items-center justify-between gap-3 border-b border-slate-100 pb-5">
                      <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-sky-700">{t("newAnalysis.setupLabel")}</p><h2 className="mt-1 text-xl font-semibold text-slate-900">{tipoAnalise === 'auto' ? t("newAnalysis.autoSearch") : t("newAnalysis.manualMode")}</h2></div>
                      <span className="rounded-lg bg-slate-100 px-2.5 py-1.5 text-xs font-semibold text-slate-600">01 / 02</span>
                    </div>
                    <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_180px_140px_160px]">
                      <label className="block space-y-2 text-xs font-semibold uppercase tracking-wider text-slate-500">{t("newAnalysis.companyInput")}
                        <input type="text" placeholder={t("newAnalysis.companySearchPlaceholder")} className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3.5 text-sm font-medium normal-case text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-sky-500 focus:ring-2 focus:ring-sky-500/15" value={empresa} onChange={(e) => setEmpresa(e.target.value)} />
                      </label>
                      <label className="block space-y-2 text-xs font-semibold uppercase tracking-wider text-slate-500">{t("newAnalysis.documentType")}
                        <select value={tipoDocumento} onChange={(e) => setTipoDocumento(e.target.value as 'report' | 'transcript')} className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3.5 text-sm font-medium text-slate-900 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/15"><option value="report">{t("newAnalysis.reportOption")}</option><option value="transcript">{t("newAnalysis.transcriptOption")}</option></select>
                      </label>
                      <label className="block space-y-2 text-xs font-semibold uppercase tracking-wider text-slate-500">{t("newAnalysis.year")}
                        <input type="text" inputMode="numeric" maxLength={4} placeholder="2025" className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3.5 text-sm font-medium text-slate-900 placeholder:text-slate-400 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/15" value={ano} onChange={(e) => setAno(e.target.value)} />
                      </label>
                      <label className="block space-y-2 text-xs font-semibold uppercase tracking-wider text-slate-500">{t("newAnalysis.quarter")}
                        <select className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3.5 text-sm font-medium text-slate-900 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/15" value={trimestre} onChange={(e) => setTrimestre(e.target.value)}><option value="1T">{t("newAnalysis.q1")}</option><option value="2T">{t("newAnalysis.q2")}</option><option value="3T">{t("newAnalysis.q3")}</option><option value="4T">{t("newAnalysis.q4")}</option></select>
                      </label>
                    </div>

                    {tipoAnalise === 'auto' ? (
                      <div className="mt-6 flex gap-4 rounded-2xl border border-cyan-100 bg-cyan-50/70 p-4 md:p-5">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-100 text-cyan-700"><Search size={20} /></div>
                        <div><p className="text-sm font-semibold text-slate-800">{tipoDocumento === 'transcript' ? t("newAnalysis.autoCallInfo") : t("newAnalysis.autoSearchInfo")}</p><p className="mt-1 text-xs leading-relaxed text-slate-600">{tipoDocumento === 'transcript' ? t("newAnalysis.autoCallDisclaimer") : t("newAnalysis.autoDisclaimer")}</p></div>
                      </div>
                    ) : (
                      <label className="relative mt-6 flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center transition hover:border-sky-400 hover:bg-sky-50">
                        <input type="file" onChange={handleFileChange} accept="application/pdf,.pdf" className="sr-only" />
                        <UploadCloud className="mb-3 h-8 w-8 text-sky-600" />
                        <span className="max-w-full break-all text-sm font-semibold text-slate-900">{file ? file.name : tipoDocumento === 'report' ? t("newAnalysis.uploadPdf") : t("newAnalysis.uploadCall")}</span>
                        <span className="mt-1 text-xs text-slate-500">{t("newAnalysis.supportPdf")}</span>
                      </label>
                    )}

                    {!isPremium && accessStatus !== 'active' && (
                      <div role={accessStatus === 'unavailable' ? 'alert' : 'status'} className="mt-5 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
                        <p>{accessStatus === 'unavailable' ? t("trial.accessUnavailable") : accessStatus === 'expired' ? t("trial.trialExpiredDesc") : t("trial.checkingAccess")}</p>
                        {accessStatus === 'unavailable' && <button type="button" onClick={() => setAccessRetry(value => value + 1)} className="mt-3 font-semibold text-sky-700 hover:text-sky-900">{t("trial.retryAccess")}</button>}
                      </div>
                    )}
                    {analysisError && <div role="alert" className="mt-5 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900"><p>{analysisError}</p>{tipoAnalise === 'auto' && analysisError !== t("newAnalysis.serviceUnavailable") && <button type="button" onClick={() => { setTipoAnalise('pdf'); setAnalysisError(""); }} className="mt-3 inline-flex items-center gap-2 font-semibold text-sky-700 hover:text-sky-900">{t("newAnalysis.tryManual")} <ArrowRight size={15} /></button>}</div>}
                    <button type="button" disabled={loading || (!isPremium && accessStatus !== 'active')} onClick={handleAnalyze} className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-sky-600 px-5 py-4 text-sm font-bold text-white shadow-lg shadow-sky-900/15 transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600"><Sparkles size={18} />{tipoAnalise === 'pdf' ? tipoDocumento === 'report' ? t("newAnalysis.generateReport") : t("newAnalysis.generateCall") : tipoDocumento === 'transcript' ? t("newAnalysis.generateAutoCall") : t("newAnalysis.generateAuto")}<ArrowRight size={18} /></button>
                  </div>

                  <aside className="mt-7 rounded-3xl border border-slate-200 bg-white/80 p-6 shadow-sm">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-sky-700">{t("newAnalysis.howItWorks")}</p>
                    <div className="mt-6 space-y-7">
                      {[t("newAnalysis.stepOne"), t("newAnalysis.stepTwo"), t("newAnalysis.stepThree")].map((step, index) => <div key={index} className="flex gap-3"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-sky-200 bg-sky-50 text-xs font-bold text-sky-700">{index + 1}</span><p className="pt-1 text-sm leading-relaxed text-slate-600">{step}</p></div>)}
                    </div>
                    <div className="mt-8 border-t border-slate-100 pt-5 text-xs leading-relaxed text-slate-500">{t("newAnalysis.manualFallbackNote")}</div>
                  </aside>
                </div>
              </>
            )}
          </section>
        )}

        {currentView === 'result' && result && (
          <div className="animate-in fade-in zoom-in duration-500 max-w-6xl mx-auto pb-10">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
              <button onClick={() => setCurrentView('history')} className="text-slate-500 hover:text-sky-700 flex items-center gap-2 transition-colors group"><div className="p-2 rounded-full bg-slate-100 group-hover:bg-slate-200 transition-colors"><ChevronLeft size={16} /></div><span className="font-medium">{t("result.backHistory")}</span></button>
              
              <button onClick={() => {
                if (!result?.id) return;
                const company = result.metadata?.ticker || result.metadata?.symbol || result.metadata?.empresa || result.metadata?.company || "";
                router.push(company
                  ? `/${locale}/dashboard/reports?company=${encodeURIComponent(String(company))}`
                  : `/${locale}/dashboard/reports?analysisId=${encodeURIComponent(String(result.id))}`);
              }} disabled={!result?.id} className="w-full md:w-auto justify-center px-6 py-2.5 rounded-lg font-bold flex items-center gap-2 shadow-lg transition-all bg-sky-600 hover:bg-sky-700 text-white disabled:opacity-50">
                <BookOpen size={18} /> {t('result.exploreFullReport')}
              </button>
            </div>
            
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-7 rounded-[2rem] border border-slate-200 bg-white/90 p-6 md:p-10 shadow-[0_24px_70px_rgba(38,57,94,0.10)]">
              <div className="min-w-0">
                <div className="mb-3 flex items-center gap-3">
                  <CompanyLogo symbol={result.metadata?.ticker || result.metadata?.symbol || result.metadata?.empresa} company={result.metadata?.empresa || result.metadata?.company || ""} />
                  <div className="min-w-0">
                    <h2 className="text-slate-500 uppercase tracking-widest text-xs font-bold mb-2">{t("result.analysisReport")}</h2>
                    <h1 className="break-words text-3xl md:text-5xl font-bold text-slate-900">{(result.metadata?.empresa || result.metadata?.company)?.toUpperCase()}</h1>
                  </div>
                </div>
                <p className={`text-xl font-medium ${result.metadata?.tipo === "Earnings Call" ? 'text-purple-600' : 'text-sky-700'}`}>
                  {result.metadata?.tipo === "Earnings Call" ? `Earnings Call · ${formatPeriod(result.metadata?.periodo, locale)}` : formatPeriod(result.metadata?.periodo, locale)}
                </p>
                {result.source?.url && /^https?:\/\//.test(result.source.url) && (
                  <a href={result.source.url} target="_blank" rel="noopener noreferrer" className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-sky-400/20 bg-sky-400/10 px-3 py-2 text-sm text-sky-700 transition hover:bg-sky-400/20">
                    <ExternalLink size={15} />{locale === 'en' ? 'View source document' : 'Ver documento de origem'} · {result.source.name}
                  </a>
                )}
              </div>
              
              {/* Só mostra a nota geral se não for um Earnings Call */}
              {result.metadata?.tipo !== "Earnings Call" && (
                <div className="flex items-center gap-6 bg-white/90 p-6 rounded-2xl border border-slate-200 w-full md:w-auto justify-between md:justify-start">
                  <div className="text-right"><p className="text-sm text-slate-500 font-medium uppercase">{t("result.aiScore")}</p><p className="text-xs text-slate-500">{t("result.basedOn")}</p></div>
                  <div className={`text-4xl font-bold ${Number(result.data?.nota_geral || 0) >= 4 ? 'text-emerald-700' : Number(result.data?.nota_geral || 0) >= 3 ? 'text-amber-700' : 'text-red-600'}`}>
                    {result.data?.nota_geral}<span className="text-lg text-slate-400">/5</span>
                  </div>
                </div>
              )}
            </div>
            
            {/* Oculta as caixinhas de pilares numéricos se for Earnings Call, já que é uma análise textual */}
            {result.metadata?.tipo !== "Earnings Call" && (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-7">
                {[{ label: "netRevenue", val: result.data?.receita_nota, icon: <DollarSign size={20} className="text-sky-700" /> }, { label: "netIncome", val: result.data?.lucro_nota, icon: <Percent size={20} className="text-purple-600" /> }, { label: "netDebt", val: result.data?.divida_nota, icon: <AlertCircle size={20} className="text-red-600" /> }, { label: "profitability", val: result.data?.rentabilidade_nota, icon: <TrendingUp size={20} className="text-emerald-700" /> }].map((item, idx) => (
                  <div key={idx} className="bg-white/90 border border-slate-200 p-6 rounded-2xl hover:border-slate-300 transition-all duration-300">
                    <div className="flex items-center justify-between mb-4"><span className="text-slate-500 text-sm font-medium">{t(item.label as any)}</span><div className="bg-slate-100 p-2 rounded-lg">{item.icon}</div></div>
                    <div className="flex items-end gap-2"><span className="text-3xl font-bold text-slate-900">{item.val}</span><span className="text-slate-400 text-sm mb-1">/5</span></div>
                    <div className="w-full bg-slate-100 h-1 mt-4 rounded-full overflow-hidden"><div className={`h-full ${Number(item.val || 0) >= 4 ? 'bg-green-500' : Number(item.val || 0) >= 3 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${(Number(item.val || 0) / 5) * 100}%` }} /></div>
                  </div>
                ))}
              </div>
            )}
            
            <div className="bg-white/90 border border-slate-200 rounded-3xl p-6 md:p-10 shadow-[0_18px_55px_rgba(38,57,94,0.08)]">
              <h3 className="text-2xl font-bold text-slate-900 mb-8 flex items-center gap-3">
                <FileText className={result.metadata?.tipo === "Earnings Call" ? "text-purple-500" : "text-blue-500"} /> 
                {result.metadata?.tipo === "Earnings Call" ? t('result.transcriptAnalysis') : t('result.investmentThesis')}
              </h3>
              <div className="prose prose-lg max-w-none text-slate-600 leading-relaxed whitespace-pre-line">
                {translationStatus === 'loading' ? (locale === 'en' ? 'Translating analysis…' : 'Traduzindo análise…') : splitBold(translatedThesis || result.data?.tese_investimento || result.analise_completa || (locale === 'en' ? 'No analysis text available.' : 'Sem análise textual disponível.')).map((part, index) => part.bold ? <strong key={index} className="font-bold text-slate-900">{part.text}</strong> : <React.Fragment key={index}>{part.text}</React.Fragment>)}
                {translationStatus === 'error' && <span className="mt-3 block text-sm text-amber-700" role="status">{locale === 'en' ? 'Translation unavailable; showing the original analysis.' : 'Tradução indisponível; exibindo a análise original.'}</span>}
              </div>
            </div>
            {result.id && <ReportFeedback key={String(result.id)} reportId={String(result.id)} kind="analysis" locale={locale}/>}
          </div>
        )}
      </main>
      <ConfirmDeleteDialog subject={pendingDelete?.owner === user?.id ? deleteSubject : null} kind="analysis" pending={deletingHistory} error={deleteHistoryError} onCancel={() => { if (!deletingHistory) setPendingDelete(null); }} onConfirm={() => void confirmHistoryDelete()} />
    </div>
  );
}
