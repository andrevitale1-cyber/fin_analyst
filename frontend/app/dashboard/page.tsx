"use client";
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useUser, UserButton } from "@clerk/nextjs";
import {
  LayoutDashboard, History, UploadCloud, FileText, Download, ChevronLeft,
  BarChart3, TrendingUp, DollarSign, Percent, Activity, Loader2,
  AlertCircle, Table as TableIcon, Trash2, ArrowUpDown, ArrowUp, ArrowDown,
  GripVertical, Eye, EyeOff, Settings2, X, Zap, Lock, Check, Menu, ExternalLink,
  Sun, Moon, Search
} from "lucide-react";

// --- CONFIGURAÇÃO DO STRIPE E API ---
const STRIPE_CHECKOUT_URL_MONTHLY = "https://buy.stripe.com/bJe3cwgdleEBfiJ9rT67S00";
const STRIPE_CHECKOUT_URL_YEARLY  = "https://buy.stripe.com/3cI6oIgdleEBgmNdI967S01"; 
const API_BASE = "https://api-finanalyzer.onrender.com";

// --- CONFIGURAÇÃO DAS COLUNAS ---
const COLUMN_DEFINITIONS = [
  { key: 'empresa', label: 'Empresa', align: 'center', minWidth: 'min-w-[140px]', color: 'text-gray-900 dark:text-white font-bold' },
  { key: 'nota_final', label: 'Nota Final', align: 'center', color: 'text-purple-600 dark:text-purple-400 font-bold' },
  { key: 'receita_nota', label: 'Receita', align: 'center', color: 'text-blue-600 dark:text-blue-400' },
  { key: 'lucro_nota', label: 'Lucro', align: 'center', color: 'text-green-600 dark:text-green-400' },
  { key: 'divida_nota', label: 'Dívida', align: 'center', color: 'text-red-600 dark:text-red-400' },
  { key: 'rentabilidade_nota', label: 'Rentabilidade', align: 'center', color: 'text-yellow-600 dark:text-yellow-400' },
  { key: 'soma_total', label: 'Soma', align: 'center', bg: 'bg-blue-50 dark:bg-blue-900/10', color: 'text-blue-800 dark:text-blue-300' },
  { key: 'qtde_tri', label: 'Resultados Analisados', align: 'center', bg: 'bg-purple-50 dark:bg-purple-900/10', color: 'text-purple-800 dark:text-purple-300' },
  { key: 'media', label: 'Média', align: 'center', bg: 'bg-green-50 dark:bg-green-900/10', color: 'text-green-800 dark:text-green-300' },
  { key: 'last_analysed_quarter', label: 'Último Tri', align: 'center', color: 'text-gray-600 dark:text-gray-400 font-bold' },
];

function Feature({ text, active = false, disabled = false }: any) {
  return (
    <li className="flex items-center gap-3">
      {disabled ? (
        <div className="p-0.5 rounded-full border border-gray-300 dark:border-gray-700 text-gray-400 dark:text-gray-600"><X size={12} /></div>
      ) : (
        <div className="p-0.5 rounded-full bg-green-100 dark:bg-green-500/10 text-green-600 dark:text-green-500 border border-green-200 dark:border-green-500/20">
          <Check size={12} strokeWidth={3} />
        </div>
      )}
      <span className={`text-sm font-medium ${disabled ? 'text-gray-400 dark:text-gray-600 line-through' : 'text-gray-700 dark:text-gray-300'}`}>{text}</span>
    </li>
  );
}

function UpgradeModal({ onClose, userId, billingCycle: initialBillingCycle = 'monthly' }: { onClose: () => void; userId?: string; billingCycle?: 'monthly' | 'yearly' }) {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>(initialBillingCycle);

  const handleCheckout = () => {
    const baseUrl = billingCycle === "yearly" ? STRIPE_CHECKOUT_URL_YEARLY : STRIPE_CHECKOUT_URL_MONTHLY;
    const url = new URL(baseUrl);
    if (userId) url.searchParams.set("client_reference_id", userId);
    window.open(url.toString(), "_blank");
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-gray-900/60 dark:bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl">
        <button onClick={onClose} className="absolute top-2 right-2 md:-top-8 md:-right-8 text-gray-400 hover:text-white bg-gray-800/80 p-2 rounded-full transition-colors z-50"><X size={24} /></button>

        <div className="flex flex-col items-center gap-1 mb-6">
          <div className="flex items-center justify-center gap-4 bg-white/10 dark:bg-black/40 p-2 rounded-full backdrop-blur-md border border-white/20 dark:border-gray-800">
            <span className={`text-sm font-bold cursor-pointer px-4 py-1.5 rounded-full transition-all ${billingCycle === 'monthly' ? 'bg-white text-gray-900 shadow-md' : 'text-gray-300 hover:text-white'}`} onClick={() => setBillingCycle('monthly')}>Mensal</span>
            <span className={`text-sm font-bold cursor-pointer px-4 py-1.5 rounded-full transition-all ${billingCycle === 'yearly' ? 'bg-white text-gray-900 shadow-md' : 'text-gray-300 hover:text-white'}`} onClick={() => setBillingCycle('yearly')}>Anual</span>
          </div>
          <div className={`transition-opacity duration-300 mt-2 ${billingCycle === 'yearly' ? 'opacity-100' : 'opacity-0'}`}>
            <span className="bg-orange-500/20 text-orange-400 text-xs font-bold px-3 py-1 rounded-full border border-orange-500/30">2 MESES GRÁTIS</span>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-5">
          <div className="bg-white dark:bg-[#11161d] border border-gray-200 dark:border-gray-800/60 rounded-[2rem] p-8 flex flex-col h-full opacity-95 shadow-xl">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1">Gratuito</h3>
            <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">Seu plano atual.</p>
            <ul className="space-y-3 mb-8 flex-1">
              <Feature text="5 Análises por semana" active />
              <Feature text="Relatório Resumido na Tela" active />
              <Feature text="Acesso ao histórico simples" active />
              <Feature text="Suporte por email" active />
              <Feature text="Upload de arquivos ilimitado" disabled />
              <Feature text="Download da Análise Completa" disabled />
              <Feature text="Tabela Comparativa de Ativos" disabled />
            </ul>
            <button onClick={onClose} className="block w-full text-center py-3 rounded-xl border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-white font-bold hover:bg-gray-50 dark:hover:bg-gray-800 transition-all mt-auto">
              Continuar Grátis
            </button>
          </div>

          <div className="bg-gradient-to-b from-blue-50 to-white dark:from-[#0d1627] dark:to-[#11161d] border-2 border-blue-500 rounded-[2rem] p-8 relative shadow-2xl shadow-blue-500/20 dark:shadow-blue-900/20 transform hover:-translate-y-1 transition-all duration-300 h-full flex flex-col">
            <h3 className="text-xl font-bold text-blue-600 dark:text-blue-400 mb-1">Premium</h3>
            <div className="flex items-end gap-1 mb-2">
              <span className="text-4xl font-extrabold text-gray-900 dark:text-white">{billingCycle === 'monthly' ? 'R$ 29' : 'R$ 290'}</span>
              <span className="text-gray-500 mb-1 text-lg font-medium">{billingCycle === 'monthly' ? '/mês' : '/ano'}</span>
            </div>
            <p className="text-gray-600 dark:text-gray-400 text-sm mb-6">Desbloqueie todo o poder da IA.</p>
            <ul className="space-y-3 mb-8 flex-1">
              <Feature text="Análises de IA Ilimitadas" active />
              <Feature text="Relatório Resumido na Tela" active />
              <Feature text="Acesso ao Histórico Ilimitado" active />
              <Feature text="Suporte por Email" active />
              <Feature text="Upload de arquivos ilimitado" active />
              <Feature text="Download da Análise Completa" active />
              <Feature text="Tabela Comparativa de Ativos" active />
              <Feature text="Prioridade máxima na fila" active />
            </ul>
            <button onClick={handleCheckout} className="block w-full text-center py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold shadow-lg shadow-blue-500/30 transition-all mt-auto animate-pulse hover:animate-none">
              Assinar Agora
            </button>
            <p className="text-center text-xs text-gray-500 mt-4 font-medium">Cancele quando quiser.</p>
          </div>
        </div> 
      </div> 
    </div> 
  );
}

function NavItem({ icon, label, active = false, onClick, isLocked = false, collapsed = false }: any) {
  return (
    <button onClick={onClick} title={collapsed ? label : undefined} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative ${collapsed ? 'justify-center px-2' : ''} ${active ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20' : 'text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-white hover:bg-blue-50 dark:hover:bg-white/5 font-medium'}`}>
      {React.cloneElement(icon, { size: 20, className: active ? 'text-white' : 'text-gray-500 dark:text-gray-400 group-hover:text-blue-600 dark:group-hover:text-white transition-colors' })}
      {!collapsed && <span className="text-sm">{label}</span>}
      {!collapsed && isLocked && <Lock size={14} className="ml-auto text-gray-400 dark:text-gray-600 group-hover:text-blue-500 dark:group-hover:text-blue-400" />}
    </button>
  );
}

export default function FinancialDashboard() {
  const router = useRouter();
  const { user, isLoaded } = useUser();

  // CONTROLE REAL DE TEMA CLARO/ESCURO
  const [isDarkMode, setIsDarkMode] = useState(true);

  useEffect(() => {
    // Ao alterar o state, injetamos ou removemos a classe "dark" da tag <html> nativa do navegador
    const root = window.document.documentElement;
    if (isDarkMode) {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
  }, [isDarkMode]);

  const [currentView, setCurrentView] = useState<'dashboard' | 'history' | 'result' | 'table'>('dashboard');
  const [loading, setLoading] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [usageCount, setUsageCount] = useState(0);
  const WEEKLY_LIMIT = 5;
  const [result, setResult] = useState<any>(null);
  const [historyList, setHistoryList] = useState<any[]>([]);
  const [historySearch, setHistorySearch] = useState("");
  const [tableData, setTableData] = useState<any[]>([]);
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [showColumnMenu, setShowColumnMenu] = useState(false);
  const columnMenuRef = useRef<HTMLDivElement>(null);
  const [columnOrder, setColumnOrder] = useState<string[]>(COLUMN_DEFINITIONS.map(c => c.key));
  const [draggedItemIndex, setDraggedItemIndex] = useState<number | null>(null);
  
  // --- CONFIGURAÇÃO DE COLUNAS PADRÃO ---
  const [visibleColumns, setVisibleColumns] = useState<Record<string, boolean>>({
    empresa: true, 
    nota_final: true, 
    receita_nota: true,
    lucro_nota: true, 
    divida_nota: true, 
    rentabilidade_nota: true,
    soma_total: false, 
    qtde_tri: true, 
    media: true, 
    last_analysed_quarter: true 
  });
  
  const [empresa, setEmpresa] = useState("");
  const [ano, setAno] = useState("");
  const [trimestre, setTrimestre] = useState("1T");
  const [file, setFile] = useState<File | null>(null);

  const isPremium = user?.publicMetadata?.plan === 'premium';

  useEffect(() => {
    if (isLoaded && !user) return; 
    if (user && !isPremium) {
      const usageKey = `usage_${user.id}`;
      const dateKey = `usage_date_${user.id}`;
      const savedCount = parseInt(localStorage.getItem(usageKey) || '0');
      const savedDate = localStorage.getItem(dateKey);
      const now = Date.now();
      const oneWeek = 7 * 24 * 60 * 60 * 1000;
      if (!savedDate || (now - parseInt(savedDate)) > oneWeek) {
        localStorage.setItem(usageKey, '0');
        localStorage.setItem(dateKey, now.toString());
        setUsageCount(0);
      } else {
        setUsageCount(savedCount);
      }
    }
  }, [isLoaded, user, isPremium]);

  const formatarData = (dataString: string) => {
    if (!dataString) return "-";
    try {
      const data = new Date(dataString);
      return new Intl.DateTimeFormat('pt-BR', {day: '2-digit', month: '2-digit', year: 'numeric'}).format(data);
    } catch (e) { return dataString; }
  };

  const columnDefsMap = useMemo(() => COLUMN_DEFINITIONS.reduce((acc, col) => { acc[col.key] = col; return acc; }, {} as any), []);
  const visibleCount = useMemo(() => Object.values(visibleColumns).filter(Boolean).length, [visibleColumns]);

  const fetchHistory = async () => {
    if (!user) return;
    try {
      const res = await fetch(`${API_BASE}/api/history?user_id=${user.id}`);
      const data = await res.json();
      setHistoryList(data);
    } catch (error) { console.error("Erro histórico", error); }
  };

  const fetchTableData = async () => {
    if (!user) return;
    try {
      const res = await fetch(`${API_BASE}/api/table-data?user_id=${user.id}`);
      const data = await res.json();
      setTableData(data);
    } catch (error) { console.error("Erro tabela", error); }
  };

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!confirm("Tem certeza que deseja excluir esta análise?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/history/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error("Erro delete");
      fetchHistory();
      fetchTableData();
    } catch (error) { alert("Erro ao excluir."); }
  };

  const handleNavClick = (view: 'dashboard' | 'history' | 'table') => {
    setIsSidebarOpen(false);
    if (view === 'table' && !isPremium) setShowUpgradeModal(true);
    else setCurrentView(view);
  };

  const handleAnalyze = async () => {
    if (!file || !empresa || !ano) { alert("Preencha todos os campos e anexe o PDF!"); return; }
    if (!user) { alert("Aguarde o carregamento do usuário."); return; }
    if (!isPremium && usageCount >= WEEKLY_LIMIT) { setShowUpgradeModal(true); return; }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("empresa", empresa.toUpperCase());
      formData.append("ano", ano);
      formData.append("trimestre", trimestre);
      formData.append("user_id", user.id);

      const response = await fetch(`${API_BASE}/api/analyze`, { method: "POST", body: formData });

      if (response.status === 403) {
        setLoading(false);
        setShowUpgradeModal(true);
        return;
      }
      if (!response.ok) throw new Error("Erro API");
      
      if (!isPremium) {
        const newCount = usageCount + 1;
        setUsageCount(newCount);
        localStorage.setItem(`usage_${user.id}`, newCount.toString());
      }

      const data = await response.json();
      setResult(data);
      setCurrentView('result');
      fetchHistory();
      fetchTableData();
    } catch (error) {
      console.error(error);
      alert("Erro na análise. Verifique se o servidor está online.");
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

  const sortedTableData = useMemo(() => {
    if (!sortConfig) return tableData;
    return [...tableData].sort((a, b) => {
      const valA = a[sortConfig.key];
      const valB = b[sortConfig.key];
      const numA = Number(valA);
      const numB = Number(valB);
      if (!isNaN(numA) && !isNaN(numB)) return sortConfig.direction === 'asc' ? numA - numB : numB - numA;
      if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
      if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [tableData, sortConfig]);

  const filteredHistory = useMemo(() => {
    if (!historySearch.trim()) return historyList;
    const lowerSearch = historySearch.toLowerCase();
    return historyList.filter(item => 
      item.empresa?.toLowerCase().includes(lowerSearch) || 
      item.periodo?.toLowerCase().includes(lowerSearch)
    );
  }, [historyList, historySearch]);

  const handleDownload = () => {
    if (!isPremium) { setShowUpgradeModal(true); return; }
    if (!result) return;

    const meta = result.metadata || {};
    const data = result.data || {};
    const empresa = (meta.empresa || "EMPRESA").toUpperCase();
    const trimestre = meta.trimestre || "";
    const ano = meta.ano || "";
    const periodo = meta.periodo || (trimestre && ano ? `${trimestre}/${ano}` : "");
    const notaFinal = data.nota_geral ?? result.nota_geral ?? data.nota_final ?? result.nota_final ?? "—";
    const analise: string = result.analise_completa || "";
    const today = new Date().toLocaleDateString("pt-BR");
    const year = new Date().getFullYear();

    const scoreColor = (n: number): string => {
      if (n >= 5) return "#06963b";
      if (n >= 4) return "#32f87a";
      if (n >= 3) return "#eab308";
      if (n >= 2) return "#f97316";
      return "#ef4444";
    };

    const notaFinalColor = notaFinal !== "—" ? scoreColor(Number(notaFinal)) : "#9ca3af";

    const sections = [
      { title: "Desempenho de Receita",  label: "RECEITA",       nota: data.receita_nota       ?? null },
      { title: "Rentabilidade e Eficiência", label: "RENTABILIDADE", nota: data.rentabilidade_nota ?? null },
      { title: "Estrutura de Capital",   label: "ESTRUTURA DE CAPITAL",       nota: data.divida_nota        ?? null },
      { title: "Margens e Lucratividade",label: "LUCRO",         nota: data.lucro_nota         ?? null },
    ];

    const cleanText = (raw: string) => raw.replace(/\*\*[^*]+\*\*/g, "").replace(/Nota Seção \d+:[^\n]*/g, "").trim();
    const rawSections = analise.match(/\*\*Seção \d+[^*]*\*\*[\s\S]*?(?=\*\*Seção \d+|\*\*Nota Geral|$)/g) || [];
    const bodies = rawSections.map(cleanText);

    const teseRaw = analise.match(/Seção 5[\s\S]*?(?=\*\*Seção 6|$)/);
    const teseBody = teseRaw ? cleanText(teseRaw[0]) : (data.tese_investimento || "");
    const teseParagraphs = teseBody.split("\n\n").filter(Boolean).map((p: string) => "<p>" + p.replace(/\*\*/g, "") + "</p>").join("");

    const metricCards = sections.map((s) => {
      const n = Number(s.nota ?? 0);
      const c = scoreColor(n);
      const pct = n ? (n / 5 * 100) : 0;
      return (
        '<div class="metric">' +
          '<div class="m-label">' + s.label + '</div>' +
          '<div class="m-score" style="color:' + c + '">' + (s.nota !== null ? s.nota : "—") + '</div>' +
          '<div class="m-bar-bg"><div class="m-bar" style="width:' + pct + '%;background:' + c + '"></div></div>' +
        '</div>'
      );
    }).join("");

    const sectionCards = sections.map((s, i) => {
      const body = bodies[i] || "";
      const notaVal = s.nota !== null ? Number(s.nota) : null;
      const cor = notaVal !== null ? scoreColor(notaVal) : "#9ca3af";
      const badge = notaVal !== null
        ? '<span class="badge" style="background:' + cor + '20;color:' + cor + ';border:1px solid ' + cor + '40">' + notaVal + '/5</span>' : "";
      return (
        '<div class="section">' +
          '<div class="section-header"><h3>' + s.title + '</h3>' + badge + '</div>' +
          '<p>' + (body || "—") + '</p>' +
        '</div>'
      );
    }).join("");

    const css = [
      "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');",
      "*{margin:0;padding:0;box-sizing:border-box}",
      "body{font-family:'Inter',sans-serif;background:#fff;color:#111;padding:48px;max-width:900px;margin:0 auto;font-size:14px;line-height:1.65}",
      ".print-actions{display:flex;justify-content:flex-end;margin-bottom:24px;}",
      ".btn-print{background:#22c55e;color:#fff;border:none;padding:12px 24px;border-radius:10px;font-weight:700;font-size:14px;cursor:pointer;display:flex;align-items:center;gap:8px;font-family:'Inter',sans-serif;box-shadow:0 4px 12px rgba(34,197,94,0.3);transition:transform 0.2s;}",
      ".btn-print:hover{background:#16a34a;transform:scale(1.02);}",
      ".header{display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:32px;border-bottom:2px solid #e5e7eb;margin-bottom:36px}",
      ".brand{display:flex;align-items:center;gap:10px}",
      ".brand-icon{width:36px;height:36px;background:#2563eb;border-radius:10px;display:flex;align-items:center;justify-content:center}",
      ".brand-icon svg{width:20px;height:20px;fill:none;stroke:#fff;stroke-width:2}",
      ".brand-name{font-size:18px;font-weight:800;color:#111}",
      ".brand-name span{color:#2563eb}",
      ".meta{text-align:right}",
      ".meta p{font-size:12px;color:#6b7280}",
      ".meta p strong{color:#374151}",
      ".hero{background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 100%);color:#fff;border-radius:16px;padding:36px 40px;margin-bottom:36px;display:flex;justify-content:space-between;align-items:center}",
      ".hero-left h1{font-size:38px;font-weight:900;letter-spacing:-1px;margin-bottom:4px}",
      ".hero-left p{font-size:16px;color:#93c5fd;font-weight:500}",
      ".hero-left .label{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:#64748b;margin-bottom:8px}",
      ".score-card{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);border-radius:14px;padding:20px 28px;text-align:center}",
      ".score-card .label{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:#94a3b8;margin-bottom:4px}",
      ".score-card .score{font-size:52px;font-weight:900;line-height:1;color:" + notaFinalColor + "}",
      ".score-card .score span{font-size:20px;color:#64748b;font-weight:500}",
      ".score-card .sub{font-size:10px;color:#64748b;margin-top:4px}",
      ".metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:36px}",
      ".metric{border:1px solid #e5e7eb;border-radius:12px;padding:16px;text-align:center}",
      ".metric .m-label{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;margin-bottom:8px;font-weight:600}",
      ".metric .m-score{font-size:28px;font-weight:900}",
      ".metric .m-bar-bg{height:4px;background:#f3f4f6;border-radius:999px;margin-top:8px}",
      ".metric .m-bar{height:4px;border-radius:999px}",
      ".section{border:1px solid #e5e7eb;border-radius:12px;padding:22px 24px;margin-bottom:16px}",
      ".section-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}",
      ".section-header h3{font-size:13px;font-weight:700;color:#111;text-transform:uppercase;letter-spacing:.04em}",
      ".badge{padding:4px 10px;border-radius:999px;font-size:12px;font-weight:700}",
      ".section p{color:#374151;font-size:13.5px;line-height:1.7}",
      ".tese{background:#f8faff;border:1px solid #dbeafe;border-radius:12px;padding:24px;margin-bottom:36px}",
      ".tese h3{font-size:13px;font-weight:700;color:#1d4ed8;text-transform:uppercase;letter-spacing:.06em;margin-bottom:14px}",
      ".tese p{color:#374151;font-size:13.5px;line-height:1.75;margin-bottom:10px}",
      ".footer{border-top:1px solid #e5e7eb;padding-top:20px;font-size:11px;color:#9ca3af;text-align:center}",
      "@media print{ .print-actions { display: none !important; } body{padding:0} @page{margin:20mm} }",
    ].join("\n");

    const html = (
      "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='UTF-8'/>" +
      "<title>Relatório " + empresa + " " + periodo + "</title>" +
      "<style>" + css + "</style></head><body>" +
      "<div class='print-actions'>" +
        "<button class='btn-print' onclick='window.print()'>" +
          "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M6 9V2h12v7'></path><path d='M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2'></path><path d='M6 14h12v8H6z'></path></svg>" +
          "Baixar PDF / Imprimir" +
        "</button>" +
      "</div>" +
      "<div class='header'>" +
        "<div class='brand'>" +
          "<div class='brand-icon'><svg viewBox='0 0 24 24'><polyline points='22 12 18 12 15 21 9 3 6 12 2 12'/></svg></div>" +
          "<div class='brand-name'>FinAnalyzer <span>.AI</span></div>" +
        "</div>" +
        "<div class='meta'><p>Gerado em <strong>" + today + "</strong></p><p>Relatório de análise fundamentalista</p></div>" +
      "</div>" +
      "<div class='hero'>" +
        "<div class='hero-left'>" +
          "<div class='label'>Relatório de Análise</div>" +
          "<h1>" + empresa + "</h1><p>" + periodo + "</p>" +
        "</div>" +
        "<div class='score-card'>" +
          "<div class='label'>Score IA</div>" +
          "<div class='score'>" + notaFinal + "<span>/5</span></div>" +
          "<div class='sub'>Baseado em 4 fundamentos</div>" +
        "</div>" +
      "</div>" +
      "<div class='metrics'>" + metricCards + "</div>" +
      sectionCards +
      "<div class='tese'><h3>Conclusão — Tese e Outlook</h3>" + teseParagraphs + "</div>" +
      "<div class='footer'>" +
        "<p>Este relatório foi gerado automaticamente pelo FinAnalyzer.AI. Não constitui recomendação de investimento.</p>" +
        "<p style='margin-top:6px'>© " + year + " FinAnalyzer Inc. · Todos os direitos reservados</p>" +
      "</div></body></html>"
    );

    const win = window.open("", "_blank");
    if (win) { win.document.write(html); win.document.close(); }
  };

  const renderCellContent = (item: any, key: string, colDef: any) => {
    if (key === 'empresa') return <span className={`${colDef.color || 'text-gray-900 dark:text-white'} font-bold`}>{item[key]?.toString().toUpperCase()}</span>;
    if (key === 'last_analysed_quarter') return <span className="bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 py-1.5 px-3 rounded-md text-xs font-bold border border-blue-200 dark:border-blue-500/30">{item[key]}</span>;
    if (key === 'media') return <span className={`px-2 py-1 rounded font-bold ${item.media >= 4 ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}`}>{item[key]}</span>;
    if (key.includes('nota') || key === 'nota_final') {
      const val = item[key];
      return <span className={`font-bold text-base ${val >= 4 ? 'text-emerald-600 dark:text-emerald-400' : val >= 3 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'}`}>{val}</span>;
    }
    return <span className={`${colDef.color || 'text-gray-700 dark:text-gray-300'}`}>{item[key]}</span>;
  };

  if (!isLoaded) return <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-[#0A0D14]"><Loader2 className="animate-spin text-blue-500 w-10 h-10" /></div>;

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-[#0A0D14] text-gray-900 dark:text-gray-100 font-sans overflow-hidden transition-colors duration-300">
      {showUpgradeModal && <UpgradeModal onClose={() => setShowUpgradeModal(false)} userId={user?.id} />}
      
      {isSidebarOpen && (
        <div className="fixed inset-0 z-40 bg-gray-900/60 dark:bg-black/80 backdrop-blur-sm md:hidden animate-in fade-in" onClick={() => setIsSidebarOpen(false)} />
      )}

      {/* SIDEBAR */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 bg-white dark:bg-[#0B0E14] border-r border-gray-200 dark:border-gray-800/60 flex flex-col p-6 transition-all duration-300 ease-in-out shadow-xl md:shadow-none
        md:relative md:translate-x-0 
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        ${isSidebarCollapsed ? 'md:w-20 md:px-3' : 'w-72'}
      `}>
        <div className="flex items-center justify-between mb-10 px-2">
          <div className={`flex items-center gap-3 ${isSidebarCollapsed ? 'md:justify-center md:w-full' : ''}`}>
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/30 dark:shadow-blue-600/20 flex-shrink-0">
              <BarChart3 className="text-white w-5 h-5" />
            </div>
            {!isSidebarCollapsed && (
              <span className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">FinAnalyzer <span className="text-blue-500">.AI</span></span>
            )}
          </div>
          <button onClick={() => setIsSidebarOpen(false)} className="md:hidden text-gray-400 hover:text-gray-900 dark:hover:text-white"><X size={24} /></button>
          {!isSidebarCollapsed && (
            <button onClick={() => setIsSidebarCollapsed(true)} className="hidden md:flex text-gray-400 hover:text-gray-900 dark:hover:text-white p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 transition-all"><ChevronLeft size={20} /></button>
          )}
        </div>

        <nav className="space-y-2">
          <NavItem icon={<LayoutDashboard />} label="Nova Análise" active={currentView === 'dashboard'} onClick={() => handleNavClick('dashboard')} collapsed={isSidebarCollapsed} />
          <NavItem icon={<TableIcon />} label="Tabela Agregada" active={currentView === 'table'} onClick={() => handleNavClick('table')} isLocked={!isPremium} collapsed={isSidebarCollapsed} />
          <NavItem icon={<History />} label="Histórico" active={currentView === 'history'} onClick={() => handleNavClick('history')} collapsed={isSidebarCollapsed} />
        </nav>

        {!isPremium && (
          <div className="mt-auto mb-6 px-2">
            <div className="bg-gray-50 dark:bg-[#11161d] border border-gray-200 dark:border-gray-800/60 p-4 rounded-xl mb-4 shadow-sm">
              <div className="flex justify-between text-xs mb-2">
                <span className="text-gray-600 dark:text-gray-400 font-medium">Análises Semanais</span>
                <span className={`font-bold ${usageCount >= 5 ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'}`}>{usageCount}/{WEEKLY_LIMIT}</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-800 h-1.5 rounded-full overflow-hidden">
                <div className={`h-full transition-all duration-500 ${usageCount >= 5 ? 'bg-red-500' : 'bg-blue-500'}`} style={{ width: `${Math.min((usageCount / WEEKLY_LIMIT) * 100, 100)}%` }} />
              </div>
            </div>
            <button onClick={() => setShowUpgradeModal(true)} className="w-full bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold py-3.5 rounded-xl transition-all shadow-[0_4px_14px_rgba(37,99,235,0.3)] flex items-center justify-center gap-2">
              <Zap size={14} className="text-yellow-300 fill-yellow-300" /> Seja Premium
            </button>
          </div>
        )}
        
        {isPremium && <div className="mt-auto" />}

        {/* MODO CLARO/ESCURO TOGGLE */}
        {!isSidebarCollapsed && (
          <div className="px-2 mt-4 mb-2">
            <button onClick={() => setIsDarkMode(!isDarkMode)} className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-50 dark:bg-[#11161d] border border-gray-200 dark:border-gray-800/60 rounded-xl text-sm font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all shadow-sm">
              {isDarkMode ? <><Sun size={16} className="text-yellow-500"/> Modo Claro</> : <><Moon size={16} className="text-blue-500 dark:text-blue-400"/> Modo Escuro</>}
            </button>
          </div>
        )}

        {/* USUÁRIO CLERK */}
        <div className="mt-2 px-2 py-3 border-t border-gray-200 dark:border-gray-800/60">
          <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 dark:hover:bg-white/5 transition-all w-full">
              <UserButton 
                showName={!isSidebarCollapsed} 
                appearance={{
                  elements: {
                    userButtonBox: "flex flex-row-reverse w-full justify-start gap-3",
                    userButtonOuterIdentifier: "!text-gray-900 dark:!text-white !font-bold text-sm tracking-wide",
                    avatarBox: "w-9 h-9 ring-2 ring-gray-200 dark:ring-gray-800"
                  }
                }}
              />
          </div>
        </div>
      </aside>
      
      <main className="flex-1 overflow-y-auto p-4 md:p-10 relative">
        {isSidebarCollapsed && (
          <div className="hidden md:flex absolute top-6 left-6 z-10 items-center gap-3">
            <button onClick={() => setIsSidebarCollapsed(false)} className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white bg-white dark:bg-[#11161d] border border-gray-200 dark:border-gray-800 px-3 py-2 rounded-xl text-sm font-medium transition-all hover:border-blue-500 shadow-sm"><Menu size={18} /> Menu</button>
            <button onClick={() => setIsDarkMode(!isDarkMode)} className="p-2 bg-white dark:bg-[#11161d] border border-gray-200 dark:border-gray-800 rounded-xl text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:border-blue-500 shadow-sm transition-all">{isDarkMode ? <Sun size={18} className="text-yellow-500" /> : <Moon size={18} className="text-blue-500" />}</button>
          </div>
        )}
        
        <div className="md:hidden flex items-center justify-between mb-8 pb-4 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <button onClick={() => setIsSidebarOpen(true)} className="p-2.5 bg-white dark:bg-[#11161d] border border-gray-200 dark:border-gray-800 rounded-xl text-gray-900 dark:text-white shadow-sm"><Menu size={20} /></button>
            <span className="font-bold text-lg text-gray-900 dark:text-white tracking-tight">FinAnalyzer <span className="text-blue-500">.AI</span></span>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => setIsDarkMode(!isDarkMode)} className="p-2.5 bg-white dark:bg-[#11161d] border border-gray-200 dark:border-gray-800 rounded-xl shadow-sm">{isDarkMode ? <Sun size={18} className="text-yellow-500" /> : <Moon size={18} className="text-blue-500"/>}</button>
            <UserButton appearance={{ elements: { avatarBox: "w-9 h-9" } }} />
          </div>
        </div>

        {/* NOVA ANÁLISE PREMIUM */}
        {currentView === 'dashboard' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-4xl mx-auto mt-2 md:mt-12 px-0 md:px-0">
            {loading ? (
              <div className="flex flex-col items-center justify-center h-[60vh] animate-in fade-in"><Loader2 className="w-16 h-16 text-blue-600 dark:text-blue-500 animate-spin mb-6" /><h2 className="text-3xl font-bold animate-pulse text-gray-900 dark:text-white mb-3 text-center">Só um momento enquanto organizamos suas informações.</h2><p className="text-gray-500 dark:text-gray-400 text-center px-4 font-medium">Nossa IA está estruturando e analisando seu relatório.</p></div>
            ) : (
              <>
                <div className="text-center mb-10 md:mb-12">
                  <h1 className="text-3xl md:text-[2.75rem] font-extrabold text-gray-900 dark:text-white mb-4 tracking-tight leading-tight">Nova Análise Financeira</h1>
                  <p className="text-gray-500 dark:text-gray-400 text-base md:text-lg font-medium">Carregue o relatório trimestral (PDF) para processamento via IA.</p>
                </div>
                
                <div className="bg-white dark:bg-[#11161d] border border-gray-200 dark:border-gray-800/60 rounded-[2rem] p-6 md:p-12 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-2xl relative overflow-hidden transition-colors duration-500">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5 md:gap-6 mb-8">
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-widest ml-1">Empresa</label>
                      <input type="text" placeholder="Ex: APPLE" className="w-full bg-gray-50 dark:bg-[#0A0D14] border border-gray-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all uppercase placeholder-gray-400 dark:placeholder-gray-600 font-bold" value={empresa} onChange={(e) => setEmpresa(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-widest ml-1">Ano</label>
                      <input type="text" placeholder="2026" className="w-full bg-gray-50 dark:bg-[#0A0D14] border border-gray-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all placeholder-gray-400 dark:placeholder-gray-600 font-bold" value={ano} onChange={(e) => setAno(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-widest ml-1">Trimestre</label>
                      <select className="w-full bg-gray-50 dark:bg-[#0A0D14] border border-gray-200 dark:border-gray-800 rounded-xl px-4 py-3.5 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all appearance-none font-bold" value={trimestre} onChange={(e) => setTrimestre(e.target.value)}>
                        <option value="1T">1º Trimestre</option>
                        <option value="2T">2º Trimestre</option>
                        <option value="3T">3º Trimestre</option>
                        <option value="4T">4º Trimestre</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-[1.5rem] p-10 md:p-14 flex flex-col items-center justify-center bg-gray-50/50 dark:bg-[#0A0D14]/50 hover:bg-gray-50 dark:hover:bg-[#0A0D14] hover:border-blue-400 dark:hover:border-blue-500/50 transition-all duration-300 cursor-pointer relative group">
                    <input type="file" onChange={handleFileChange} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
                    <div className="bg-blue-100 dark:bg-blue-500/10 p-5 rounded-full mb-5 group-hover:scale-110 transition-transform duration-300 shadow-sm relative">
                      <UploadCloud className="text-blue-600 dark:text-blue-400 w-8 h-8 relative z-10" />
                    </div>
                    <p className="text-gray-900 dark:text-white font-extrabold text-xl text-center mb-1">{file ? file.name : "Clique ou arraste o PDF"}</p>
                    <p className="text-gray-500 dark:text-gray-400 text-sm text-center font-medium">Suporta PDF de até 10MB</p>
                  </div>

                  <button onClick={handleAnalyze} className="w-full mt-8 bg-blue-600 hover:bg-blue-500 text-white font-bold text-lg py-4 rounded-xl shadow-[0_4px_20px_rgba(37,99,235,0.25)] dark:shadow-[0_0_20px_rgba(37,99,235,0.3)] transition-all duration-300 flex items-center justify-center gap-3 hover:scale-[1.01]">
                    <Activity size={22} /> Gerar Análise Completa
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* TABELA AGREGADA */}
        {currentView === 'table' && (
          <div className="animate-in fade-in duration-500 max-w-[98%] mx-auto pb-20">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pt-0">
              <div><h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white tracking-tight">Tabela Agregada</h1><p className="text-gray-500 dark:text-gray-400 mt-1 text-sm md:text-base font-medium">Visão consolidada do desempenho das empresas.</p></div>
              <div className="relative" ref={columnMenuRef}>
                <button onClick={() => setShowColumnMenu(!showColumnMenu)} className={`flex items-center gap-2 border px-4 py-2.5 rounded-xl transition-all shadow-sm w-full md:w-auto justify-center font-medium ${showColumnMenu ? 'bg-blue-600 border-blue-500 text-white' : 'bg-white dark:bg-[#11161d] border-gray-300 dark:border-gray-700 hover:border-blue-500 text-gray-700 dark:text-gray-300'}`}>
                  <Settings2 size={18} /><span>Configurar Colunas</span>
                </button>
                {showColumnMenu && (
                  <div className="absolute right-0 mt-3 w-80 bg-white/95 dark:bg-[#11161d]/95 backdrop-blur-md border border-gray-200 dark:border-gray-700 rounded-2xl shadow-2xl z-50 overflow-hidden animate-in fade-in zoom-in-95 origin-top-right">
                    <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-[#0d1117]/50"><span className="text-sm font-bold text-gray-900 dark:text-white">Visualização de Colunas</span><button onClick={() => setShowColumnMenu(false)} className="text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"><X size={16} /></button></div>
                    <div className="p-2 max-h-[400px] overflow-y-auto space-y-1">
                      {columnOrder.map((colKey, index) => {
                        const col = columnDefsMap[colKey];
                        const isVisible = visibleColumns[colKey];
                        return (
                          <div key={colKey} draggable onDragStart={() => onDragStart(index)} onDragEnter={() => onDragEnter(index)} onDragEnd={onDragEnd} onClick={() => toggleColumn(colKey)} className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all border border-transparent ${draggedItemIndex === index ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-500/50 opacity-50' : 'hover:bg-gray-50 dark:hover:bg-white/5 hover:border-gray-200 dark:hover:border-gray-700'}`}>
                            <div className="flex items-center gap-3"><div className="cursor-grab text-gray-400 dark:text-gray-600 hover:text-gray-600 dark:hover:text-gray-300"><GripVertical size={16} /></div><span className={`text-sm font-medium ${isVisible ? 'text-gray-900 dark:text-gray-200' : 'text-gray-400 dark:text-gray-500'}`}>{col.label}</span></div>
                            <div className={`p-1.5 rounded-lg transition-colors ${isVisible ? 'bg-blue-100 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-600'}`}>{isVisible ? <Eye size={14} /> : <EyeOff size={14} />}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </header>
            <div className="bg-white dark:bg-[#11161d] border border-gray-200 dark:border-gray-800/60 rounded-[1.5rem] shadow-sm dark:shadow-xl flex flex-col overflow-hidden transition-colors duration-300">
              <div className="overflow-x-auto w-full">
                <table className={`text-left border-collapse ${visibleCount > 8 ? 'min-w-[1200px]' : 'w-full'}`}>
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-[#0A0D14]/50 text-xs uppercase tracking-wider text-gray-600 dark:text-gray-500">
                      {columnOrder.map((colKey, index) => {
                        const col = columnDefsMap[colKey];
                        if (!visibleColumns[colKey]) return null;
                        const isDragging = draggedItemIndex === index;
                        return (
                          <th key={col.key} draggable onDragStart={() => onDragStart(index)} onDragEnter={() => onDragEnter(index)} onDragEnd={onDragEnd} onDragOver={(e) => e.preventDefault()} onClick={() => handleSort(col.key)} className={`py-4 px-4 font-semibold transition-all relative group select-none cursor-grab active:cursor-grabbing ${col.color || ''} ${col.minWidth || ''} ${isDragging ? 'opacity-30 bg-blue-100 dark:bg-blue-500/10 border-2 border-dashed border-blue-500' : 'hover:bg-gray-100 dark:hover:bg-white/5'}`} style={{ textAlign: col.align as any }}>
                            <div className={`flex items-center gap-2 ${col.align === 'center' ? 'justify-center' : ''}`}><GripVertical size={12} className="text-gray-400 dark:text-gray-700 group-hover:text-gray-600 dark:group-hover:text-gray-400 transition-colors opacity-0 group-hover:opacity-100" />{col.label}{sortConfig?.key === col.key ? (sortConfig?.direction === 'asc' ? <ArrowUp size={12} className="text-blue-500 dark:text-blue-400"/> : <ArrowDown size={12} className="text-blue-500 dark:text-blue-400"/>) : <ArrowUpDown size={12} className="opacity-0 group-hover:opacity-30 transition-opacity"/>}</div>
                          </th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-800 text-sm">
                    {sortedTableData.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-white/[0.02] transition-colors group">
                        {columnOrder.map(colKey => {
                          const col = columnDefsMap[colKey];
                          if (!visibleColumns[colKey]) return null;
                          return <td key={`${item.id}-${col.key}`} className={`py-4 px-4 ${col.align === 'center' ? 'text-center' : ''} ${col.bg || ''}`}>{renderCellContent(item, col.key, col)}</td>;
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {sortedTableData.length === 0 && <div className="p-12 text-center text-gray-500">Nenhuma análise disponível.</div>}
            </div>
          </div>
        )}

        {currentView === 'history' && (
          <div className="animate-in fade-in duration-500 max-w-6xl mx-auto">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pt-0">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">Histórico Detalhado</h1>
                <p className="text-gray-500 dark:text-gray-400 mt-1 font-medium">Gerencie suas análises individuais.</p>
              </div>
              
              {/* BARRA DE BUSCA */}
              <div className="relative w-full md:w-80">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none">
                  <Search size={18} className="text-gray-400 dark:text-gray-500" />
                </div>
                <input
                  type="text"
                  placeholder="Buscar empresa ou período..."
                  className="w-full bg-white dark:bg-[#11161d] border border-gray-200 dark:border-gray-800 rounded-xl pl-10 pr-4 py-3 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-sm placeholder-gray-400 dark:placeholder-gray-600 font-medium"
                  value={historySearch}
                  onChange={(e) => setHistorySearch(e.target.value)}
                />
              </div>
            </header>
            
            <div className="bg-white dark:bg-[#11161d] border border-gray-200 dark:border-gray-800/60 rounded-[1.5rem] shadow-sm dark:shadow-xl overflow-hidden transition-colors duration-300">
             <div className="overflow-x-auto">
              <table className="w-full min-w-[800px] text-left border-collapse">
                <thead><tr className="border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-[#0A0D14]/50 text-xs uppercase tracking-wider text-gray-600 dark:text-gray-500"><th className="py-5 px-6 font-semibold">Empresa</th><th className="py-5 px-6 font-semibold">Período</th><th className="py-5 px-6 font-semibold">Data</th><th className="py-5 px-6 text-center font-semibold">Score</th><th className="py-5 px-6 text-right font-semibold">Ações</th></tr></thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {filteredHistory.map((item: any) => (
                    <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-white/[0.02] transition-colors group cursor-pointer" onClick={() => { setResult(item.conteudo); setEmpresa(item.empresa); setCurrentView('result'); }}>
                      <td className="py-4 px-6"><div className="flex items-center gap-3"><span className="font-bold text-gray-900 dark:text-white">{item.empresa?.toUpperCase()}</span></div></td>
                      <td className="py-4 px-6 text-gray-600 dark:text-gray-400 font-medium">{item.periodo}</td>
                      <td className="py-4 px-6 text-gray-500 dark:text-gray-500 text-sm font-medium">{formatarData(item.data)}</td>
                      <td className="py-4 px-6 text-center"><span className={`inline-flex items-center justify-center w-12 h-8 rounded-lg text-sm font-extrabold ${item.nota >= 4 ? 'bg-emerald-100 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20' : item.nota >= 3 ? 'bg-amber-100 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20' : 'bg-red-100 dark:bg-red-500/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-500/20'}`}>{item.nota}</span></td>
                      <td className="py-4 px-6 text-right"><div className="flex items-center justify-end gap-3"><button onClick={(e) => handleDelete(e, item.id)} className="p-2 text-gray-400 dark:text-gray-500 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors" title="Excluir"><Trash2 size={16} /></button><button className="text-sm font-bold text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300 transition-colors flex items-center gap-1">Detalhes <ChevronLeft className="w-4 h-4 rotate-180" /></button></div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
             </div> 
              {filteredHistory.length === 0 && (
                <div className="p-12 text-center text-gray-500 font-medium">
                  {historyList.length === 0 ? "Histórico vazio." : "Nenhuma análise encontrada para esta busca."}
                </div>
              )}
            </div>
          </div>
        )}

        {/* TELA DE RESULTADOS */}
        {currentView === 'result' && result && (
          <div className="animate-in fade-in zoom-in duration-500 max-w-6xl mx-auto pb-10">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
              <button onClick={() => setCurrentView('history')} className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white flex items-center gap-2 transition-colors group font-medium"><div className="p-2 rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-transparent shadow-sm group-hover:bg-gray-100 dark:group-hover:bg-gray-700 transition-colors"><ChevronLeft size={16} /></div><span>Voltar para Histórico</span></button>
              <button onClick={handleDownload} className={`w-full md:w-auto justify-center px-6 py-2.5 rounded-xl font-bold flex items-center gap-2 shadow-sm transition-all ${isPremium ? 'bg-green-600 hover:bg-green-500 text-white shadow-green-600/20' : 'bg-gray-200 dark:bg-gray-800 text-gray-500 dark:text-gray-400 cursor-not-allowed border border-gray-300 dark:border-gray-700'}`}>
                {isPremium ? <ExternalLink size={18} /> : <Lock size={18} />} Ver Relatório Completo
              </button>
            </div>
            
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-12 border-b border-gray-200 dark:border-gray-800/60 pb-8">
              <div><h2 className="text-gray-500 dark:text-gray-500 uppercase tracking-widest text-xs font-extrabold mb-2">Relatório de Análise</h2><h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 dark:text-white mb-2 tracking-tight">{result.metadata?.empresa?.toUpperCase()}</h1><p className="text-xl text-blue-600 dark:text-blue-400 font-bold">{result.metadata?.periodo || `${result.metadata?.trimestre}/${result.metadata?.ano}`}</p></div>
              <div className="flex items-center gap-6 bg-white dark:bg-[#11161d] p-6 rounded-[1.5rem] border border-gray-200 dark:border-gray-800/60 shadow-sm dark:shadow-none w-full md:w-auto justify-between md:justify-start"><div className="text-right"><p className="text-sm text-gray-500 dark:text-gray-400 font-bold uppercase tracking-wider">Score IA</p><p className="text-xs text-gray-400 dark:text-gray-500 font-medium">Baseado em 4 fundamentos</p></div><div className={`text-5xl font-extrabold tracking-tighter ${(result.data?.nota_geral || 0) >= 4 ? 'text-emerald-500 dark:text-emerald-400' : (result.data?.nota_geral || 0) == 3 ? 'text-amber-500 dark:text-amber-400' : 'text-red-500 dark:text-red-400'}`}>{result.data?.nota_geral}<span className="text-2xl text-gray-400 dark:text-gray-600">/5</span></div></div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
              {[{ label: "Receita", val: result.data?.receita_nota, icon: <DollarSign size={20} className="text-blue-600 dark:text-blue-400" /> }, { label: "Margem", val: result.data?.lucro_nota, icon: <Percent size={20} className="text-purple-600 dark:text-purple-400" /> }, { label: "Dívida", val: result.data?.divida_nota, icon: <AlertCircle size={20} className="text-red-600 dark:text-red-400" /> }, { label: "Rentabilidade", val: result.data?.rentabilidade_nota, icon: <TrendingUp size={20} className="text-emerald-600 dark:text-emerald-400" /> }].map((item, idx) => (
                <div key={idx} className="bg-white dark:bg-[#11161d] border border-gray-200 dark:border-gray-800/60 p-6 rounded-[1.5rem] shadow-sm dark:shadow-none transition-all duration-300">
                  <div className="flex items-center justify-between mb-5"><span className="text-gray-600 dark:text-gray-400 text-sm font-bold">{item.label}</span><div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-transparent p-2.5 rounded-xl">{item.icon}</div></div>
                  <div className="flex items-end gap-1"><span className="text-4xl font-extrabold text-gray-900 dark:text-white tracking-tighter">{item.val}</span><span className="text-gray-400 dark:text-gray-600 text-lg mb-1 font-bold">/5</span></div>
                  <div className="w-full bg-gray-100 dark:bg-gray-800/60 h-1.5 mt-5 rounded-full overflow-hidden"><div className={`h-full ${(item.val || 0) >= 4 ? 'bg-green-500' : (item.val || 0) >= 3 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${((item.val || 0) / 5) * 100}%` }} /></div>
                </div>
              ))}
            </div>
            
            <div className="bg-white dark:bg-[#11161d] border border-gray-200 dark:border-gray-800/60 rounded-[2rem] p-8 md:p-12 shadow-sm dark:shadow-xl transition-colors duration-300">
              <h3 className="text-2xl font-extrabold text-gray-900 dark:text-white mb-8 flex items-center gap-3"><FileText className="text-blue-600 dark:text-blue-500" /> Tese de Investimento</h3>
              <div className="prose dark:prose-invert prose-lg max-w-none text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line font-medium">{result.data?.tese_investimento ? result.data.tese_investimento : "Sem análise textual disponível."}</div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}