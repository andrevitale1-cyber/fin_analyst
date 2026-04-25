"use client";
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useUser, UserButton } from "@clerk/nextjs";
import { useTranslations, useLocale } from "next-intl";
import LanguageSwitcher from "../../../components/LanguageSwitcher";
import {
  LayoutDashboard, History, UploadCloud, FileText, Download, ChevronLeft,
  BarChart3, TrendingUp, DollarSign, Percent, Activity, Loader2,
  AlertCircle, Table as TableIcon, Trash2, ArrowUpDown, ArrowUp, ArrowDown,
  GripVertical, Eye, EyeOff, Settings2, X, Zap, Lock, Check, Menu
} from "lucide-react";

// API_BASE configurada para o seu Render
const API_BASE = "https://api-finanalyzer.onrender.com";
const STRIPE_CHECKOUT_URL_MONTHLY = "https://buy.stripe.com/bJe3cwgdleEBfiJ9rT67S00";
const STRIPE_CHECKOUT_URL_YEARLY  = "https://buy.stripe.com/3cI6oIgdleEBgmNdI967S01"; 

const getColumnDefinitions = (t: any) => [
  { key: 'empresa', label: t('company'), align: 'center', minWidth: 'min-w-[140px]', color: 'text-gray-100 font-medium' },
  { key: 'nota_geral', label: t('finalScore'), align: 'center', color: 'text-blue-400 font-bold' },
  { key: 'receita_nota', label: t('netRevenue'), align: 'center', color: 'text-gray-300' },
  { key: 'lucro_nota', label: t('netIncome'), align: 'center', color: 'text-gray-300' },
  { key: 'divida_nota', label: t('netDebt'), align: 'center', color: 'text-gray-300' },
  { key: 'rentabilidade_nota', label: t('profitability'), align: 'center', color: 'text-gray-300' },
  { key: 'soma_total', label: t('sum'), align: 'center', bg: 'bg-gray-800/30', color: 'text-gray-300' },
  { key: 'qtde_tri', label: t('analyzedResults'), align: 'center', bg: 'bg-gray-800/30', color: 'text-gray-300' },
  { key: 'media', label: t('average'), align: 'center', bg: 'bg-gray-800/30', color: 'text-gray-300' },
  { key: 'last_analysed_quarter', label: t('lastQuarter'), align: 'center', color: 'text-gray-400 font-medium' },
];

function Feature({ text, disabled = false }: any) {
  return (
    <li className="flex items-center gap-3">
      {disabled ? (
        <div className="p-1 rounded-full text-gray-600"><X size={14} /></div>
      ) : (
        <div className="p-1 rounded-full text-blue-500"><Check size={14} /></div>
      )}
      <span className={`text-sm ${disabled ? 'text-gray-500' : 'text-gray-200 font-medium'}`}>{text}</span>
    </li>
  );
}

function UpgradeModal({ onClose, userId, billingCycle: initialBillingCycle = 'monthly', isExpired = false }: { onClose?: () => void; userId?: string; billingCycle?: 'monthly' | 'yearly'; isExpired?: boolean }) {
  const t = useTranslations("Dashboard");
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>(initialBillingCycle);

  const handleCheckout = () => {
    const baseUrl = billingCycle === "yearly" ? STRIPE_CHECKOUT_URL_YEARLY : STRIPE_CHECKOUT_URL_MONTHLY;
    const url = new URL(baseUrl);
    if (userId) url.searchParams.set("client_reference_id", userId);
    window.open(url.toString(), "_blank");
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-[#0E1117] border border-gray-800 shadow-2xl rounded-2xl w-full max-w-4xl overflow-hidden relative flex flex-col md:flex-row">
        {/* Só mostra o botão fechar se o trial ainda está ativo */}
        {!isExpired && onClose && (
          <button onClick={onClose} className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors z-50 bg-[#161b22] p-1.5 rounded-md border border-gray-800">
            <X size={18} />
          </button>
        )}
        {/* Painel esquerdo: info do trial */}
        <div className="w-full md:w-1/2 p-8 border-b md:border-b-0 md:border-r border-gray-800 bg-[#0d1117]/50 flex flex-col">
          <div className="mb-6">
            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold mb-4 ${isExpired ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}`}>
              <span className={`w-2 h-2 rounded-full ${isExpired ? 'bg-red-400' : 'bg-amber-400 animate-pulse'}`} />
              {isExpired ? t("trial.trialExpired") : t("trial.trialActive")}
            </div>
            <h3 className="text-xl font-semibold text-white">{t("upgrade.basicPlan")}</h3>
            <p className="text-sm text-gray-400 mt-2 leading-relaxed">
              {isExpired ? t("trial.trialExpiredDesc") : t("upgrade.basicDesc")}
            </p>
          </div>
          <ul className="space-y-4 mb-8 flex-1">
            <Feature text={t("features.unlimitedAnalysis")} />
            <Feature text={t("features.summaryReport")} />
            <Feature text={t("features.downloadFullReport")} />
            <Feature text={t("features.comparativeTable")} />
            <Feature text={t("features.serverPriority")} />
          </ul>
          {!isExpired && onClose && (
            <button onClick={onClose} className="w-full py-2.5 rounded-lg border border-gray-700 text-sm font-medium text-gray-300 hover:bg-gray-800 transition-colors">
              {t("upgrade.continueBasic")}
            </button>
          )}
        </div>
        {/* Painel direito: plano pro */}
        <div className="w-full md:w-1/2 p-8 bg-[#161b22] relative flex flex-col">
          <div className="absolute top-0 right-0 bg-blue-600 text-white text-[10px] font-bold px-3 py-1 rounded-bl-lg uppercase tracking-wider">{t("upgrade.recommended")}</div>
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-white flex items-center gap-2">FinAnalyzer Pro <Zap size={16} className="text-blue-500 fill-blue-500" /></h3>
            <p className="text-sm text-gray-400 mt-1">{t("upgrade.proDesc")}</p>
          </div>
          <div className="flex items-center gap-2 mb-6 bg-[#0d1117] p-1 rounded-lg w-fit border border-gray-800">
            <button onClick={() => setBillingCycle('monthly')} className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${billingCycle === 'monthly' ? 'bg-gray-800 text-white shadow-sm' : 'text-gray-400 hover:text-white'}`}>{t("upgrade.monthly")}</button>
            <button onClick={() => setBillingCycle('yearly')} className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${billingCycle === 'yearly' ? 'bg-gray-800 text-white shadow-sm' : 'text-gray-400 hover:text-white'}`}>{t("upgrade.yearly")}</button>
          </div>
          <div className="flex items-end gap-1 mb-8">
            <span className="text-4xl font-bold text-white tracking-tight">{billingCycle === 'monthly' ? 'R$ 29' : 'R$ 290'}</span>
            <span className="text-gray-500 text-sm mb-1">{billingCycle === 'monthly' ? '/mês' : '/ano'}</span>
          </div>
          <ul className="space-y-4 mb-8 flex-1">
            <Feature text={t("features.unlimitedAnalysis")} />
            <Feature text={t("features.premiumReports")} />
            <Feature text={t("features.tableUnlocked")} />
            <Feature text={t("features.serverPriority")} />
          </ul>
          <button onClick={handleCheckout} className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition-colors shadow-sm">
            {t("upgrade.subscribePro")}
          </button>
          <p className="text-center text-xs text-gray-500 mt-3">{billingCycle === 'monthly' ? 'Cancele quando quiser.' : 'Cobrança anual. Cancele quando quiser.'}</p>
        </div>
      </div>
    </div>
  );
}

function NavItem({ icon, label, active = false, onClick, isLocked = false, collapsed = false }: any) {
  return (
    <button onClick={onClick} title={collapsed ? label : undefined} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group relative ${collapsed ? 'justify-center px-2' : ''} ${active ? 'bg-gray-800 text-white font-medium' : 'text-gray-400 hover:text-white hover:bg-[#161b22]'}`}>
      {React.cloneElement(icon, { size: 18, className: active ? "text-blue-500" : "text-gray-400 group-hover:text-gray-300" })}
      {!collapsed && <span className="text-sm">{label}</span>}
      {!collapsed && isLocked && <Lock size={14} className="ml-auto text-gray-600" />}
    </button>
  );
}

export default function FinancialDashboard() {
  const router = useRouter();
  const t = useTranslations("Dashboard");
  const locale = useLocale();
  const COLUMN_DEFINITIONS = getColumnDefinitions(t);
  const { user, isLoaded } = useUser();

  const [currentView, setCurrentView] = useState<'dashboard' | 'history' | 'result' | 'table'>('dashboard');
  const [loading, setLoading] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Estado para escolher qual tipo de análise
  const [tipoAnalise, setTipoAnalise] = useState<'pdf' | 'call'>('pdf');

  // --- TRIAL STATE ---
  const [trialDaysLeft, setTrialDaysLeft] = useState<number | null>(null);
  const [isTrialExpired, setIsTrialExpired] = useState(false);
  const [trialChecked, setTrialChecked] = useState(false);

  const [downloadCount, setDownloadCount] = useState(0);
  const WEEKLY_DOWNLOAD_LIMIT = 3;

  const [result, setResult] = useState<any>(null);
  const [historyList, setHistoryList] = useState<any[]>([]);
  const [tableData, setTableData] = useState<any[]>([]);

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

  const isPremium = user?.publicMetadata?.plan === 'premium';

  // --- Verificar acesso ao trial no backend ---
  useEffect(() => {
    if (!isLoaded || !user) return;
    if (isPremium) { setTrialChecked(true); return; }

    // Carrega contagem de downloads
    const downloadKey = `downloads_${user.id}`;
    setDownloadCount(parseInt(localStorage.getItem(downloadKey) || '0'));

    // Verifica o trial no backend
    fetch(`${API_BASE}/api/check-access?user_id=${user.id}&is_premium=false`)
      .then(r => r.json())
      .then(data => {
        setTrialDaysLeft(data.days_left ?? 0);
        setIsTrialExpired(!data.has_access);
        if (!data.has_access) setShowUpgradeModal(true);
        setTrialChecked(true);
      })
      .catch(() => setTrialChecked(true));
  }, [isLoaded, user, isPremium]);

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

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!confirm("Tem certeza que deseja excluir esta análise?")) return;
    try {
      await fetch(`${API_BASE}/api/history/${id}`, { method: 'DELETE' });
      fetchHistory();
      fetchTableData();
    } catch (error) { alert("Erro ao excluir."); }
  };

  const handleNavClick = (view: 'dashboard' | 'history' | 'table') => {
    setIsSidebarOpen(false);
    if (view === 'table' && !isPremium) { setShowUpgradeModal(true); return; }
    setCurrentView(view);
  };

  const handleAnalyze = async () => {
    if (!empresa || !ano || !file) { alert("Preencha todos os campos e anexe o PDF."); return; }
    if (!user) return;

    // Bloqueia se trial expirado e não é premium
    if (!isPremium && isTrialExpired) { setShowUpgradeModal(true); return; }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("ano", ano);
      formData.append("trimestre", trimestre);
      formData.append("user_id", user.id);
      formData.append("empresa", empresa.toUpperCase());
      formData.append("file", file);
      formData.append("locale", locale);

      const urlBackend = tipoAnalise === 'pdf'
        ? `${API_BASE}/api/analyze`
        : `${API_BASE}/api/analyze-call`;

      const response = await fetch(urlBackend, { method: "POST", body: formData });

      if (response.status === 403) { setLoading(false); setShowUpgradeModal(true); return; }
      if (!response.ok) {
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
    } catch (error: any) {
      console.error(error);
      alert("Erro na análise: " + error.message);
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
      item.periodo?.toLowerCase().includes(q)
    );
  }, [historyList, searchQuery]);

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

  const handleDownload = () => {
    const id = result?.id; 
    
    if (!isPremium && downloadCount >= WEEKLY_DOWNLOAD_LIMIT) {
      setShowUpgradeModal(true);
      return;
    }

    if (id) {
      if (!isPremium && user) {
        const newDlCount = downloadCount + 1;
        setDownloadCount(newDlCount);
        localStorage.setItem(`downloads_${user.id}`, newDlCount.toString());
      }
      // Abre o relatório gerado pelo backend numa nova aba
      window.open(`${API_BASE}/api/report/${id}?locale=${locale}`, '_blank');
    } else {
      alert("ID do relatório não encontrado. Tente abrir pelo histórico.");
    }
  };

  const renderCellContent = (item: any, key: string, colDef: any) => {
    if (key === 'empresa') return <span className={`${colDef.color || 'text-white'} font-bold`}>{item[key]?.toString().toUpperCase()}</span>;
    if (key === 'trimestre') return <span className="bg-blue-900/30 text-blue-300 py-1 px-2 rounded text-xs font-bold border border-blue-500/20">{item[key]}</span>;
    if (key === 'media') return <span className={`px-2 py-1 rounded font-bold ${item.media >= 4 ? 'text-green-400' : 'text-yellow-400'}`}>{item[key]}</span>;
    if (key.includes('nota') || key === 'nota_final') {
      const val = item[key];
      return <span className={`font-bold text-base ${val >= 4 ? 'text-emerald-400' : val >= 3 ? 'text-yellow-400' : 'text-red-400'}`}>{val}</span>;
    }
    return <span className={`${colDef.color || 'text-gray-300'}`}>{item[key]}</span>;
  };

  if (!isLoaded || !trialChecked) return <div className="flex h-screen items-center justify-center bg-[#0E1117]"><Loader2 className="animate-spin text-blue-500" /></div>;

  return (
    <div className="flex h-screen bg-[#0E1117] text-gray-100 font-sans overflow-hidden">
      {showUpgradeModal && (
        <UpgradeModal
          onClose={isTrialExpired ? undefined : () => setShowUpgradeModal(false)}
          userId={user?.id}
          isExpired={isTrialExpired}
        />
      )}
      
      {isSidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/80 backdrop-blur-sm md:hidden animate-in fade-in" onClick={() => setIsSidebarOpen(false)} />
      )}

      <aside className={`fixed inset-y-0 left-0 z-50 bg-[#0d1117] border-r border-gray-800 flex flex-col p-6 transition-all duration-300 ease-in-out md:relative md:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} ${isSidebarCollapsed ? 'md:w-20 md:px-3' : 'w-72'}`}>
        <div className="flex items-center justify-between mb-10 px-2">
          <div className={`flex items-center gap-3 ${isSidebarCollapsed ? 'md:justify-center md:w-full' : ''}`}>
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-900/20 flex-shrink-0">
              <BarChart3 className="text-white w-5 h-5" />
            </div>
            {!isSidebarCollapsed && (
              <span className="text-xl font-bold tracking-tight text-white">FinAnalyzer <span className="text-blue-500">.AI</span></span>
            )}
          </div>
          <button onClick={() => setIsSidebarOpen(false)} className="md:hidden text-gray-400 hover:text-white"><X size={24} /></button>
          {!isSidebarCollapsed && (
            <button onClick={() => setIsSidebarCollapsed(true)} className="hidden md:flex text-gray-400 hover:text-white p-1 rounded-lg hover:bg-white/5 transition-all" title="Esconder menu"><ChevronLeft size={20} /></button>
          )}
        </div>

        <nav className="space-y-2">
          <NavItem icon={<LayoutDashboard />} label={t("nav.newAnalysis")} active={currentView === 'dashboard'} onClick={() => handleNavClick('dashboard')} collapsed={isSidebarCollapsed} />
          <NavItem icon={<TableIcon />} label={t("nav.aggregatedTable")} active={currentView === 'table'} onClick={() => handleNavClick('table')} isLocked={!isPremium} collapsed={isSidebarCollapsed} />
          <NavItem icon={<History />} label={t("nav.history")} active={currentView === 'history'} onClick={() => handleNavClick('history')} collapsed={isSidebarCollapsed} />
        </nav>

        {!isPremium && (
          <div className="mt-auto mb-6 px-2">
            {/* Banner de trial */}
            <div className={`border p-4 rounded-xl mb-4 space-y-3 ${
              isTrialExpired
                ? 'bg-red-500/10 border-red-500/30'
                : trialDaysLeft !== null && trialDaysLeft <= 2
                  ? 'bg-amber-500/10 border-amber-500/30'
                  : 'bg-[#161b22] border-gray-800'
            }`}>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                  {isTrialExpired ? t("trial.trialExpired") : t("trial.trialActive")}
                </span>
                {!isTrialExpired && (
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                )}
              </div>
              {!isTrialExpired && trialDaysLeft !== null && (
                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-gray-400">{t("trial.endsIn")}</span>
                    <span className={`font-bold ${trialDaysLeft <= 2 ? 'text-amber-400' : 'text-white'}`}>
                      {trialDaysLeft} {trialDaysLeft === 1 ? t("trial.dayLeft") : t("trial.daysLeft")}
                    </span>
                  </div>
                  <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${trialDaysLeft <= 2 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                      style={{ width: `${Math.min((trialDaysLeft / 7) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              )}
              {isTrialExpired && (
                <p className="text-xs text-red-300">{t("trial.trialExpiredDesc")}</p>
              )}
            </div>
            <button onClick={() => setShowUpgradeModal(true)} className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white text-xs font-bold py-3 rounded-xl transition-all shadow-lg flex items-center justify-center gap-2">
              <Zap size={14} className="text-yellow-300 fill-yellow-300" /> {t("sidebar.goPremium")}
            </button>
          </div>
        )}
        
        {isPremium && <div className="mt-auto" />}

        <div className="mt-4 px-2 py-3 border-t border-gray-800 flex flex-col gap-3">
           <div className="px-2 w-full">
              <LanguageSwitcher />
           </div>
           <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/5 transition-all w-full">
              <UserButton showName={true} appearance={{ elements: { userButtonBox: "flex flex-row-reverse w-full justify-start gap-3", userButtonOuterIdentifier: "!text-white !font-bold text-sm tracking-wide", avatarBox: "w-9 h-9 ring-2 ring-gray-700" } }} />
           </div>
        </div>
      </aside>
      
      <main className="flex-1 overflow-y-auto p-4 md:p-8 relative">
        {isSidebarCollapsed && (
          <button onClick={() => setIsSidebarCollapsed(false)} className="hidden md:flex absolute top-6 left-4 z-10 items-center gap-2 text-gray-400 hover:text-white bg-[#161b22] border border-gray-800 px-3 py-2 rounded-xl text-sm font-medium transition-all hover:border-blue-500"><Menu size={18} /> {t("sidebar.menu")}</button>
        )}
        
        <div className="md:hidden flex items-center justify-between mb-6 pb-4 border-b border-gray-800">
          <div className="flex items-center gap-3"><button onClick={() => setIsSidebarOpen(true)} className="p-2 bg-[#161b22] border border-gray-800 rounded-lg text-white hover:bg-gray-800 active:scale-95 transition-all"><Menu size={24} /></button><span className="font-bold text-lg text-white tracking-tight">FinAnalyzer <span className="text-blue-500">.AI</span></span></div>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <UserButton appearance={{ elements: { avatarBox: "w-8 h-8" } }} />
          </div>
        </div>

        {currentView === 'table' && (
          <div className="animate-in fade-in duration-500 max-w-[98%] mx-auto pb-20">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pt-0">
              <div><h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">{t("table.title")}</h1><p className="text-gray-400 mt-1 text-sm md:text-base">{t("table.desc")}</p></div>
              <div className="relative" ref={columnMenuRef}>
                <button onClick={() => setShowColumnMenu(!showColumnMenu)} className={`flex items-center gap-2 border px-4 py-2 rounded-xl transition-all shadow-lg w-full md:w-auto justify-center ${showColumnMenu ? 'bg-blue-600 border-blue-500 text-white' : 'bg-[#161b22] border-gray-700 hover:border-blue-500 text-gray-300'}`}><Settings2 size={18} /><span>{t("table.configColumns")}</span></button>
                {showColumnMenu && (
                  <div className="absolute right-0 mt-3 w-80 bg-[#161b22]/95 backdrop-blur-md border border-gray-700 rounded-2xl shadow-2xl z-50 overflow-hidden animate-in fade-in zoom-in-95 origin-top-right">
                    <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-[#0d1117]/50"><span className="text-sm font-bold text-white">{t("table.columnView")}</span><button onClick={() => setShowColumnMenu(false)} className="text-gray-400 hover:text-white"><X size={16} /></button></div>
                    <div className="p-2 max-h-[400px] overflow-y-auto space-y-1">
                      <p className="px-2 py-1 text-xs text-gray-500 font-medium uppercase tracking-wider mb-2">{t("table.dragToReorder")}</p>
                      {columnOrder.map((colKey, index) => {
                        const col = columnDefsMap[colKey];
                        const isVisible = visibleColumns[colKey];
                        return (
                          <div key={colKey} draggable onDragStart={() => onDragStart(index)} onDragEnter={() => onDragEnter(index)} onDragEnd={onDragEnd} onClick={() => toggleColumn(colKey)} className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all border border-transparent ${draggedItemIndex === index ? 'bg-blue-900/20 border-blue-500/50 opacity-50' : 'hover:bg-white/5 hover:border-gray-700'}`}>
                            <div className="flex items-center gap-3"><div className="cursor-grab text-gray-600 hover:text-gray-300"><GripVertical size={16} /></div><span className={`text-sm font-medium ${isVisible ? 'text-gray-200' : 'text-gray-500'}`}>{col.label}</span></div>
                            <div className={`p-1.5 rounded-lg transition-colors ${isVisible ? 'bg-blue-500/10 text-blue-400' : 'bg-gray-800 text-gray-600'}`}>{isVisible ? <Eye size={14} /> : <EyeOff size={14} />}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </header>
            <div className="bg-[#161b22] border border-gray-800 rounded-2xl shadow-xl flex flex-col overflow-hidden">
              <div className="overflow-x-auto w-full">
                <table className={`text-left border-collapse ${visibleCount > 8 ? 'min-w-[1200px]' : 'w-full'}`}>
                  <thead>
                    <tr className="border-b border-gray-800 bg-[#0d1117]/50 text-xs uppercase tracking-wider text-gray-500">
                      {columnOrder.map((colKey, index) => {
                        const col = columnDefsMap[colKey];
                        if (!visibleColumns[colKey]) return null;
                        const isDragging = draggedItemIndex === index;
                        return (
                          <th key={col.key} draggable onDragStart={() => onDragStart(index)} onDragEnter={() => onDragEnter(index)} onDragEnd={onDragEnd} onDragOver={(e) => e.preventDefault()} onClick={() => handleSort(col.key)} className={`py-3 px-3 font-semibold transition-all relative group select-none cursor-grab active:cursor-grabbing ${col.color || ''} ${col.minWidth || ''} ${isDragging ? 'opacity-30 bg-blue-500/10 border-2 border-dashed border-blue-500' : 'hover:bg-white/5'}`} style={{ textAlign: col.align as any }}>
                            <div className={`flex items-center gap-2 ${col.align === 'center' ? 'justify-center' : ''}`}><GripVertical size={12} className="text-gray-700 group-hover:text-gray-400 transition-colors opacity-0 group-hover:opacity-100" />{col.label}{sortConfig?.key === col.key ? (sortConfig?.direction === 'asc' ? <ArrowUp size={12} className="text-blue-400"/> : <ArrowDown size={12} className="text-blue-400"/>) : <ArrowUpDown size={12} className="opacity-0 group-hover:opacity-30 transition-opacity"/>}</div>
                          </th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800 text-sm">
                    {sortedTableData.map((item: any) => (
                      <tr key={item.id} className="hover:bg-white/[0.02] transition-colors group">
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
              {sortedTableData.length === 0 && <div className="p-12 text-center text-gray-500">{t("table.empty")}</div>}
            </div>
          </div>
        )}
        
        {currentView === 'history' && (
          <div className="animate-in fade-in duration-500 max-w-6xl mx-auto">
            <header className="flex items-center justify-between mb-8 pt-0">
              <div><h1 className="text-3xl font-bold text-white tracking-tight">{t("historyView.title")}</h1><p className="text-gray-400 mt-1">{t("historyView.desc")}</p></div>
              <div className="relative">
                <input type="text" placeholder={t("historyView.searchPlaceholder")} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="bg-[#161b22] border border-gray-700 rounded-xl px-4 py-2.5 pl-10 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all w-64" />
                <svg className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
                {searchQuery && <button onClick={() => setSearchQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors"><X size={14} /></button>}
              </div>
            </header>
            <div className="bg-[#161b22] border border-gray-800 rounded-2xl shadow-xl overflow-hidden">
             <div className="overflow-x-auto">
              <table className="w-full min-w-[800px] text-left border-collapse">
                <thead><tr className="border-b border-gray-800 bg-[#0d1117]/50 text-xs uppercase tracking-wider text-gray-500"><th className="py-5 px-6 font-semibold">{t("company")}</th><th className="py-5 px-6 font-semibold">{t("historyView.period")}</th><th className="py-5 px-6 font-semibold">{t("historyView.date")}</th><th className="py-5 px-6 text-center font-semibold">{t("historyView.score")}</th><th className="py-5 px-6 text-right font-semibold">{t("historyView.actions")}</th></tr></thead>
                <tbody className="divide-y divide-gray-800">
                  {filteredHistory.map((item: any) => (
                    <tr key={item.id} className="hover:bg-white/[0.02] transition-colors group cursor-pointer" onClick={() => { 
                      setResult({ ...item.conteudo, id: item.id }); 
                      setEmpresa(item.empresa); 
                      setCurrentView('result'); 
                    }}>
                      <td className="py-4 px-6"><div className="flex items-center gap-3"><span className="font-medium text-gray-200">{item.empresa?.toUpperCase()}</span></div></td>
                      <td className="py-4 px-6 text-gray-400">{item.periodo}</td>
                      <td className="py-4 px-6 text-gray-500 text-sm">{formatarData(item.data)}</td>
                      <td className="py-4 px-6 text-center">
                        {item.nota > 0 ? (
                          <span className={`inline-flex items-center justify-center w-12 h-8 rounded-lg text-sm font-bold ${item.nota >= 4 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : item.nota >= 3 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>{item.nota}</span>
                        ) : (
                          <span className="text-purple-400 text-xs bg-purple-500/10 border border-purple-500/20 px-2 py-1 rounded-md font-semibold">CALL</span>
                        )}
                      </td>
                      <td className="py-4 px-6 text-right"><div className="flex items-center justify-end gap-3"><button onClick={(e) => handleDelete(e, item.id)} className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-colors" title="Excluir"><Trash2 size={16} /></button><button className="text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1">{t("historyView.details")} <ChevronLeft className="w-4 h-4 rotate-180" /></button></div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
             </div> 
              {filteredHistory.length === 0 && <div className="p-12 text-center text-gray-500">{searchQuery ? `Nenhum resultado para "${searchQuery}".` : t("historyView.empty")}</div>}
            </div>
          </div>
        )}

        {currentView === 'dashboard' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-3xl mx-auto mt-6 md:mt-10 px-0 md:px-0">
            {loading ? (
              <div className="flex flex-col items-center justify-center h-96 animate-in fade-in"><Loader2 className="w-16 h-16 text-blue-500 animate-spin mb-6" /><h2 className="text-2xl md:text-3xl font-bold animate-pulse text-white mb-2 text-center">{t("newAnalysis.analyzing")}</h2><p className="text-gray-400 text-center px-4">{t("newAnalysis.processing")}</p></div>
            ) : (
              <>
                <div className="text-center mb-6 md:mb-8">
                   <h1 className="text-3xl md:text-4xl font-bold text-white mb-3 tracking-tight">{t("newAnalysis.title")}</h1>
                   <p className="text-gray-400 text-base md:text-lg">{t("newAnalysis.desc")}</p>
                </div>

                {/* BOTÕES DE ALTERNÂNCIA (TOGGLE) */}
                <div className="flex justify-center gap-4 mb-8">
                    <button 
                      type="button" 
                      onClick={() => setTipoAnalise('pdf')} 
                      className={`px-6 py-2.5 rounded-lg font-medium transition-all duration-200 flex items-center gap-2 ${tipoAnalise === 'pdf' ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' : 'bg-[#161b22] border border-gray-800 text-gray-400 hover:text-gray-200 hover:bg-gray-800'}`}
                    >
                      {t("newAnalysis.pdfReport")}
                    </button>
                    <button 
                      type="button"
                      onClick={() => setTipoAnalise('call')} 
                      className={`px-6 py-2.5 rounded-lg font-medium transition-all duration-200 flex items-center gap-2 ${tipoAnalise === 'call' ? 'bg-purple-600 text-white shadow-lg shadow-purple-900/20' : 'bg-[#161b22] border border-gray-800 text-gray-400 hover:text-gray-200 hover:bg-gray-800'}`}
                    >
                      {t("newAnalysis.callTranscript")}
                    </button>
                </div>

                <div className="bg-[#161b22] border border-gray-800 rounded-2xl p-4 md:p-8 shadow-2xl relative overflow-hidden group hover:border-gray-700 transition-colors duration-500">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6 mb-8">
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                        {tipoAnalise === 'pdf' ? t('newAnalysis.companyInput') : t('newAnalysis.tickerInput')}
                      </label>
                      <input 
                        type="text" 
                        placeholder={tipoAnalise === 'pdf' ? t('newAnalysis.companyPlaceholder') : t('newAnalysis.tickerPlaceholder')} 
                        className="w-full bg-[#0d1117] border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all uppercase" 
                        value={empresa} 
                        onChange={(e) => setEmpresa(e.target.value)} 
                      />
                    </div>
                    <div className="space-y-2"><label className="text-xs font-bold text-gray-500 uppercase tracking-wider">{t("newAnalysis.year")}</label><input type="text" placeholder="2025" className="w-full bg-[#0d1117] border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all" value={ano} onChange={(e) => setAno(e.target.value)} /></div>
                    <div className="space-y-2"><label className="text-xs font-bold text-gray-500 uppercase tracking-wider">{t("newAnalysis.quarter")}</label><select className="w-full bg-[#0d1117] border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all appearance-none" value={trimestre} onChange={(e) => setTrimestre(e.target.value)}><option value="1T">{t("newAnalysis.q1")}</option><option value="2T">{t("newAnalysis.q2")}</option><option value="3T">{t("newAnalysis.q3")}</option><option value="4T">{t("newAnalysis.q4")}</option></select></div>
                  </div>
                  
                  {/* A CAIXA DE UPLOAD AGORA APARECE SEMPRE */}
                  <div className="border-2 border-dashed border-gray-700 rounded-xl p-6 md:p-10 flex flex-col items-center justify-center bg-[#0d1117]/50 hover:bg-[#0d1117] hover:border-blue-500/50 transition-all duration-300 cursor-pointer relative">
                    <input type="file" onChange={handleFileChange} accept=".pdf" className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                    <div className="bg-gray-800 p-4 rounded-full mb-4 group-hover:scale-110 transition-transform duration-300"><UploadCloud className="text-blue-400 w-8 h-8" /></div>
                    <p className="text-gray-300 font-medium text-lg text-center">
                      {file ? file.name : (tipoAnalise === 'pdf' ? t("newAnalysis.uploadPdf") : t("newAnalysis.uploadCall"))}
                    </p>
                    <p className="text-gray-500 text-sm mt-2 text-center">{t("newAnalysis.supportPdf")}</p>
                  </div>

                  <button 
                    onClick={handleAnalyze} 
                    className={`w-full mt-8 text-white font-bold py-4 rounded-xl shadow-lg transition-all duration-300 flex items-center justify-center gap-2 ${tipoAnalise === 'pdf' ? 'bg-blue-600 hover:bg-blue-500 shadow-blue-900/20' : 'bg-purple-600 hover:bg-purple-500 shadow-purple-900/20'}`}
                  >
                    <Activity size={20} /> {tipoAnalise === 'pdf' ? t('newAnalysis.generateReport') : t('newAnalysis.generateCall')}
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {currentView === 'result' && result && (
          <div className="animate-in fade-in zoom-in duration-500 max-w-6xl mx-auto pb-10">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
              <button onClick={() => setCurrentView('history')} className="text-gray-400 hover:text-white flex items-center gap-2 transition-colors group"><div className="p-2 rounded-full bg-gray-800 group-hover:bg-gray-700 transition-colors"><ChevronLeft size={16} /></div><span className="font-medium">{t("result.backHistory")}</span></button>
              
              <button onClick={handleDownload} className={`w-full md:w-auto justify-center px-6 py-2.5 rounded-lg font-bold flex items-center gap-2 shadow-lg transition-all ${!isPremium && downloadCount >= WEEKLY_DOWNLOAD_LIMIT ? 'bg-gray-700 text-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-500 text-white'}`}>
                {!isPremium && downloadCount >= WEEKLY_DOWNLOAD_LIMIT ? <Lock size={18} /> : <Download size={18} />}
                {isPremium ? t('result.viewReport') : `\${t('result.viewReport')} (${downloadCount}/${WEEKLY_DOWNLOAD_LIMIT})`}
              </button>
            </div>
            
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-12 border-b border-gray-800 pb-8">
              <div>
                <h2 className="text-gray-500 uppercase tracking-widest text-xs font-bold mb-2">{t("result.analysisReport")}</h2>
                <h1 className="text-4xl md:text-5xl font-bold text-white mb-2">{result.metadata?.empresa?.toUpperCase()}</h1>
                <p className={`text-xl font-medium ${result.metadata?.tipo === "Earnings Call" ? 'text-purple-400' : 'text-blue-400'}`}>
                  {result.metadata?.tipo === "Earnings Call" ? `Earnings Call · ${result.metadata?.periodo}` : result.metadata?.periodo}
                </p>
              </div>
              
              {/* Só mostra a nota geral se não for um Earnings Call */}
              {result.metadata?.tipo !== "Earnings Call" && (
                <div className="flex items-center gap-6 bg-[#161b22] p-6 rounded-2xl border border-gray-800 w-full md:w-auto justify-between md:justify-start">
                  <div className="text-right"><p className="text-sm text-gray-400 font-medium uppercase">{t("result.aiScore")}</p><p className="text-xs text-gray-500">{t("result.basedOn")}</p></div>
                  <div className={`text-4xl font-bold ${Number(result.data?.nota_geral || 0) >= 4 ? 'text-emerald-400' : Number(result.data?.nota_geral || 0) >= 3 ? 'text-amber-400' : 'text-red-400'}`}>
                    {result.data?.nota_geral}<span className="text-lg text-gray-600">/5</span>
                  </div>
                </div>
              )}
            </div>
            
            {/* Oculta as caixinhas de pilares numéricos se for Earnings Call, já que é uma análise textual */}
            {result.metadata?.tipo !== "Earnings Call" && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
                {[{ label: "netRevenue", val: result.data?.receita_nota, icon: <DollarSign size={20} className="text-blue-400" /> }, { label: "netIncome", val: result.data?.lucro_nota, icon: <Percent size={20} className="text-purple-400" /> }, { label: "netDebt", val: result.data?.divida_nota, icon: <AlertCircle size={20} className="text-red-400" /> }, { label: "profitability", val: result.data?.rentabilidade_nota, icon: <TrendingUp size={20} className="text-emerald-400" /> }].map((item, idx) => (
                  <div key={idx} className="bg-[#161b22] border border-gray-800 p-6 rounded-2xl hover:border-gray-700 transition-all duration-300">
                    <div className="flex items-center justify-between mb-4"><span className="text-gray-400 text-sm font-medium">{t(item.label as any)}</span><div className="bg-gray-900 p-2 rounded-lg">{item.icon}</div></div>
                    <div className="flex items-end gap-2"><span className="text-3xl font-bold text-white">{item.val}</span><span className="text-gray-600 text-sm mb-1">/5</span></div>
                    <div className="w-full bg-gray-800 h-1 mt-4 rounded-full overflow-hidden"><div className={`h-full ${Number(item.val || 0) >= 4 ? 'bg-green-500' : Number(item.val || 0) >= 3 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${(Number(item.val || 0) / 5) * 100}%` }} /></div>
                  </div>
                ))}
              </div>
            )}
            
            <div className="bg-[#161b22] border border-gray-800 rounded-3xl p-6 md:p-10 shadow-2xl">
              <h3 className="text-2xl font-bold text-white mb-8 flex items-center gap-3">
                <FileText className={result.metadata?.tipo === "Earnings Call" ? "text-purple-500" : "text-blue-500"} /> 
                {result.metadata?.tipo === "Earnings Call" ? t('result.transcriptAnalysis') : t('result.investmentThesis')}
              </h3>
              <div className="prose prose-invert prose-lg max-w-none text-gray-300 leading-relaxed whitespace-pre-line">
                {result.data?.tese_investimento ? result.data.tese_investimento : (result.analise_completa || "Sem análise textual disponível.")}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}