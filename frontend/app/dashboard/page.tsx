"use client";
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useUser, UserButton } from "@clerk/nextjs"; // <--- NOVO IMPORT
import {
  LayoutDashboard, History, UploadCloud, FileText, Download, ChevronLeft,
  BarChart3, TrendingUp, DollarSign, Percent, Activity, Loader2,
  AlertCircle, Table as TableIcon, Trash2, ArrowUpDown, ArrowUp, ArrowDown,
  GripVertical, Eye, EyeOff, Settings2, X, Zap, Lock, Check
} from "lucide-react";

// --- CONFIGURAÇÃO DO STRIPE ---
// ATENÇÃO: Substitua pelos seus links de pagamento reais da Stripe
const STRIPE_LINKS = {
  monthly: "https://buy.stripe.com/bJe3cwgdleEBfiJ9rT67S00", 
  yearly: "https://buy.stripe.com/3cI6oIgdleEBgmNdI967S01"
};

const API_BASE = "https://api-finanalyzer.onrender.com";

// --- CONFIGURAÇÃO DAS COLUNAS ---
const COLUMN_DEFINITIONS = [
  { key: 'empresa', label: 'Empresa', align: 'center', minWidth: 'min-w-[140px]', color: 'text-white font-bold' },
  { key: 'nota_final', label: 'Nota Final', align: 'center', color: 'text-purple-400 font-bold' },
  { key: 'lucro_nota', label: 'Lucro', align: 'center', color: 'text-green-400' },
  { key: 'margem_nota', label: 'Margem', align: 'center', color: 'text-yellow-400' },
  { key: 'roe_nota', label: 'ROE', align: 'center', color: 'text-orange-400' },
  { key: 'liquidez_nota', label: 'Liquidez', align: 'center', color: 'text-cyan-400' },
  { key: 'divida_nota', label: 'Dívida', align: 'center', color: 'text-red-400' },
];

export default function DashboardPage() {
  const router = useRouter();
  const { user, isLoaded } = useUser();
  
  // --- ESTADOS GERAIS ---
  const [activeTab, setActiveTab] = useState('upload');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  
  // --- ESTADO PARA O CICLO DE FATURAÇÃO (NOVO) ---
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  // --- ESTADOS DA TABELA ---
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [columnVisibility, setColumnVisibility] = useState<Record<string, boolean>>(
    COLUMN_DEFINITIONS.reduce((acc, col) => ({ ...acc, [col.key]: true }), {})
  );
  const [showColumnSelector, setShowColumnSelector] = useState(false);

  // --- EFEITOS ---
  useEffect(() => {
    // Simulação de verificação de auth
    if (isLoaded && !user) {
      router.push('/');
    }
  }, [isLoaded, user]); // Removido router das dependências para evitar loop no mock

  useEffect(() => {
    if (user) {
      fetchHistory();
    }
  }, [user]);

  // --- FUNÇÕES ---
  const fetchHistory = async () => {
    try {
      // Mock data para demonstração se a API falhar
      const mockHistory = [
         { id: 1, empresa: "PETR4", trimestre: "4T24", nota_final: 4.5, receita_nota: 5, lucro_nota: 4, margem_nota: 5, roe_nota: 4, liquidez_nota: 5, divida_nota: 3 },
         { id: 2, empresa: "VALE3", trimestre: "4T24", nota_final: 3.8, receita_nota: 4, lucro_nota: 3, margem_nota: 4, roe_nota: 5, liquidez_nota: 4, divida_nota: 4 }
      ];
      
      try {
        const res = await fetch(`${API_BASE}/historico`);
        if (res.ok) {
          const data = await res.json();
          const cleanData = data.map((item: any) => ({
             ...item,
             nota_final: parseFloat(item.nota_final) || 0
          }));
          setHistory(cleanData);
        } else {
           setHistory(mockHistory); // Fallback para mock
        }
      } catch (e) {
        setHistory(mockHistory); // Fallback para mock
      }

    } catch (err) {
      console.error("Erro ao buscar histórico:", err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!file) {
       // Mock analysis para demo se não houver arquivo real
       setLoading(true);
       setTimeout(() => {
          setAnalysis({
            empresa: "DEMO3",
            trimestre: "1T25",
            nota_final: 4.2,
            receita_nota: 5, lucro_nota: 4, margem_nota: 4, roe_nota: 5, liquidez_nota: 3, divida_nota: 4,
            analise_texto: "A empresa apresentou resultados sólidos no trimestre, com crescimento expressivo de receita (+15% a/a) impulsionado pelo aumento de volume de vendas. O EBITDA ajustado cresceu 12%, embora a margem tenha sofrido leve compressão devido ao aumento de custos logísticos.\n\nPontos Positivos:\n- Forte geração de caixa operacional.\n- Redução da alavancagem financeira.\n\nPontos de Atenção:\n- Exposição cambial elevada.\n- Competição acirrada no setor de varejo."
          });
          setLoading(false);
       }, 2000);
       return;
    }

    setLoading(true);
    setError('');
    setAnalysis(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/analisar`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Erro ao processar o arquivo.");
      }

      const data = await res.json();
      setAnalysis(data);
      fetchHistory(); // Atualiza histórico após análise
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Tem a certeza que deseja eliminar esta análise?")) return;
    try {
      // Tenta deletar na API
      const res = await fetch(`${API_BASE}/historico/${id}`, { method: 'DELETE' });
      // Atualiza estado local independentemente (para funcionar no mock)
      setHistory(history.filter(h => h.id !== id));
    } catch (err) {
      console.error("Erro ao eliminar:", err);
      // Fallback para deletar localmente no mock
      setHistory(history.filter(h => h.id !== id));
    }
  };

  // Lógica de Ordenação
  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'desc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfig({ key, direction });
  };

  const sortedHistory = useMemo(() => {
    if (!sortConfig) return history;
    return [...history].sort((a, b) => {
      // Tratamento especial para valores numéricos e strings
      let valA = a[sortConfig.key];
      let valB = b[sortConfig.key];

      // Tenta converter para número se possível para ordenação correta
      const numA = parseFloat(valA);
      const numB = parseFloat(valB);
      
      if (!isNaN(numA) && !isNaN(numB)) {
         valA = numA;
         valB = numB;
      } else {
         valA = String(valA).toLowerCase();
         valB = String(valB).toLowerCase();
      }

      if (valA < valB) return sortConfig.direction === 'asc' ? -1 : 1;
      if (valA > valB) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [history, sortConfig]);

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-[#0E1117] flex items-center justify-center">
         <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0E1117] text-gray-100 font-sans flex overflow-hidden">
      
      {/* --- SIDEBAR --- */}
      <aside className="w-20 lg:w-64 bg-[#161b22] border-r border-gray-800 flex-col justify-between hidden md:flex transition-all duration-300">
        <div>
          <div className="h-20 flex items-center justify-center lg:justify-start lg:px-6 border-b border-gray-800">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/20 shrink-0">
              <BarChart3 className="text-white w-6 h-6" />
            </div>
            <span className="ml-3 text-xl font-bold tracking-tight text-white hidden lg:block">
              Fin<span className="text-blue-500">Analyzer</span>
            </span>
          </div>

          <nav className="p-4 space-y-2">
            {[
              { id: 'upload', icon: <UploadCloud size={20} />, label: 'Nova Análise' },
              { id: 'history', icon: <TableIcon size={20} />, label: 'Comparador de Ativos' },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                  activeTab === item.id 
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' 
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
              >
                {item.icon}
                <span className="font-medium hidden lg:block">{item.label}</span>
                {activeTab === item.id && (
                  <div className="ml-auto w-1.5 h-1.5 bg-white rounded-full hidden lg:block" />
                )}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-4 border-t border-gray-800">
          <button 
             onClick={() => setShowPaymentModal(true)}
             className="w-full bg-gradient-to-r from-purple-600 to-blue-600 p-4 rounded-xl relative overflow-hidden group mb-4"
          >
             <div className="relative z-10 flex items-center gap-3 justify-center lg:justify-start">
               <Zap className="text-white fill-current" size={20} />
               <div className="text-left hidden lg:block">
                 <p className="text-white font-bold text-sm">Seja Premium</p>
                 <p className="text-blue-100 text-xs">Acesso ilimitado</p>
               </div>
             </div>
             <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
          </button>

          <div className="flex items-center gap-3 px-2 justify-center lg:justify-start">
            <UserButton afterSignOutUrl="/" appearance={{
              elements: { avatarBox: "w-10 h-10 ring-2 ring-gray-700" }
            }} />
            <div className="hidden lg:block overflow-hidden">
               <p className="text-sm font-medium text-white truncate">{user?.fullName}</p>
               <p className="text-xs text-gray-500 truncate">{user?.primaryEmailAddress?.emailAddress}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* --- MOBILE NAV (Simple) --- */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-[#161b22] border-t border-gray-800 z-50 flex justify-around p-3">
         <button onClick={() => setActiveTab('upload')} className={`p-2 rounded-lg ${activeTab === 'upload' ? 'text-blue-500 bg-blue-500/10' : 'text-gray-400'}`}><UploadCloud /></button>
         <button onClick={() => setActiveTab('history')} className={`p-2 rounded-lg ${activeTab === 'history' ? 'text-blue-500 bg-blue-500/10' : 'text-gray-400'}`}><TableIcon /></button>
         <button onClick={() => setShowPaymentModal(true)} className="p-2 rounded-lg text-purple-400"><Zap /></button>
         <div className="p-2"><UserButton /></div>
      </div>

      {/* --- MAIN CONTENT --- */}
      <main className="flex-1 p-6 lg:p-10 overflow-y-auto relative h-screen">
        
        {/* TAB: UPLOAD & ANALYSIS */}
        {activeTab === 'upload' && (
          <div className="max-w-5xl mx-auto space-y-8 pb-20 md:pb-0">
            
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <h1 className="text-3xl font-bold text-white mb-2">Nova Análise</h1>
                <p className="text-gray-400">Carregue o PDF do release de resultados (ITR/DFP) para iniciar.</p>
              </div>
            </div>

            {/* Upload Area */}
            {!analysis && (
              <div 
                className={`relative border-2 border-dashed rounded-3xl p-12 text-center transition-all duration-300 group ${
                  dragActive 
                    ? 'border-blue-500 bg-blue-500/5 scale-[1.01]' 
                    : 'border-gray-700 bg-[#161b22] hover:border-gray-500'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <div className="w-20 h-20 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300 shadow-xl">
                  {loading ? (
                    <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
                  ) : (
                    <UploadCloud className="w-10 h-10 text-blue-400" />
                  )}
                </div>
                
                <h3 className="text-xl font-bold text-white mb-2">
                  {loading ? 'Processando Inteligência Artificial...' : 'Arraste seu arquivo aqui'}
                </h3>
                <p className="text-gray-400 mb-8 max-w-md mx-auto">
                  Suportamos arquivos PDF de até 20MB. Nossa IA identifica automaticamente a empresa e o período.
                </p>

                <div className="relative inline-block">
                  <input 
                    type="file" 
                    id="file-upload" 
                    className="hidden" 
                    accept=".pdf"
                    onChange={handleFileUpload}
                    disabled={loading}
                  />
                  <label 
                    htmlFor="file-upload" 
                    className={`flex items-center gap-2 px-8 py-3 rounded-xl font-bold cursor-pointer transition-all shadow-lg ${
                       loading 
                        ? 'bg-gray-700 text-gray-400 cursor-not-allowed' 
                        : 'bg-blue-600 hover:bg-blue-500 text-white hover:shadow-blue-900/30'
                    }`}
                  >
                    {loading ? 'Analisando...' : 'Selecionar Arquivo'}
                  </label>
                  
                  {/* Botão de demonstração para quando não há arquivo real */}
                  <button 
                    onClick={() => handleAnalyze()}
                    className="block mt-4 text-xs text-gray-500 hover:text-blue-400 underline mx-auto"
                  >
                    (Modo Demo: Simular Análise sem arquivo)
                  </button>
                </div>

                {file && !loading && (
                   <div className="mt-6 flex items-center justify-center gap-2 text-sm text-gray-300 bg-gray-800/50 py-2 px-4 rounded-lg inline-flex">
                      <FileText size={16} />
                      {file.name}
                      <button onClick={(e) => { e.preventDefault(); handleAnalyze(); }} className="ml-4 text-blue-400 hover:text-blue-300 font-bold underline">
                        CONFIRMAR ANÁLISE
                      </button>
                   </div>
                )}

                {error && (
                  <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 flex items-center justify-center gap-2 animate-in fade-in slide-in-from-bottom-2">
                    <AlertCircle size={20} />
                    {error}
                  </div>
                )}
              </div>
            )}

            {/* Analysis Results */}
            {analysis && (
              <div className="animate-in fade-in slide-in-from-bottom-8 duration-500 space-y-8">
                
                {/* Score Card */}
                <div className="bg-gradient-to-br from-[#161b22] to-[#0d1117] border border-gray-800 rounded-3xl p-8 relative overflow-hidden shadow-2xl">
                   <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
                      <Activity size={200} />
                   </div>
                   
                   <div className="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">
                      <div>
                         <div className="flex items-center gap-3 mb-2">
                            <h2 className="text-4xl font-bold text-white">{analysis.empresa}</h2>
                            <span className="px-3 py-1 rounded-full bg-gray-800 border border-gray-700 text-xs font-mono text-gray-300">
                               {analysis.trimestre}
                            </span>
                         </div>
                         <p className="text-gray-400 max-w-xl text-lg">
                           Análise fundamentalista gerada por IA com base nos documentos oficiais.
                         </p>
                      </div>

                      <div className="flex items-center gap-6 bg-gray-900/50 p-4 rounded-2xl border border-gray-800 backdrop-blur-sm">
                         <div className="text-right">
                            <p className="text-gray-400 text-sm font-medium uppercase tracking-wider">Score Final</p>
                            <p className="text-xs text-gray-500">de 0 a 5</p>
                         </div>
                         <div className={`text-6xl font-black tracking-tighter ${
                            analysis.nota_final >= 4 ? 'text-green-500' : 
                            analysis.nota_final >= 3 ? 'text-yellow-500' : 'text-red-500'
                         }`}>
                            {analysis.nota_final}
                         </div>
                      </div>
                   </div>

                   {/* Botões de Ação */}
                   <div className="flex gap-4 mt-8">
                      <button onClick={() => setAnalysis(null)} className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gray-800 hover:bg-gray-700 text-white font-medium transition-colors">
                         <ChevronLeft size={18} /> Nova Análise
                      </button>
                      <button onClick={() => window.print()} className="flex items-center gap-2 px-6 py-3 rounded-xl border border-gray-700 hover:bg-gray-800 text-gray-300 font-medium transition-colors">
                         <Download size={18} /> Salvar PDF
                      </button>
                   </div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  {[
                    { label: 'Receita', val: analysis.receita_nota, icon: <DollarSign size={20} className="text-blue-400" /> },
                    { label: 'Lucro Líq.', val: analysis.lucro_nota, icon: <BarChart3 size={20} className="text-purple-400" /> },
                    { label: 'Margem', val: analysis.margem_nota, icon: <Percent size={20} className="text-yellow-400" /> },
                    { label: 'ROE', val: analysis.roe_nota, icon: <Activity size={20} className="text-orange-400" /> },
                    { label: 'Liquidez', val: analysis.liquidez_nota, icon: <Activity size={20} className="text-cyan-400" /> },
                    { label: 'Dívida', val: analysis.divida_nota, icon: <TrendingUp size={20} className="text-red-400" /> } // Dívida geralmente é melhor se baixa, mas aqui assumo nota de qualidade
                  ].map((item, idx) => (
                    <div key={idx} className="bg-[#161b22] border border-gray-800 p-6 rounded-2xl hover:border-gray-700 transition-all duration-300">
                      <div className="flex items-center justify-between mb-4">
                         <span className="text-gray-400 text-sm font-medium">{item.label}</span>
                         <div className="bg-gray-900 p-2 rounded-lg">{item.icon}</div>
                      </div>
                      <div className="flex items-end gap-2">
                         <span className="text-3xl font-bold text-white">{item.val}</span>
                         <span className="text-gray-600 text-sm mb-1">/5</span>
                      </div>
                      <div className="w-full bg-gray-800 h-1 mt-4 rounded-full overflow-hidden">
                         <div 
                           className={`h-full ${
                             (item.val || 0) >= 4 ? 'bg-green-500' : 
                             (item.val || 0) >= 3 ? 'bg-yellow-500' : 'bg-red-500'
                           }`} 
                           style={{ width: `${((item.val || 0) / 5) * 100}%` }} 
                         />
                      </div>
                    </div>
                  ))}
                </div>

                {/* AI Text Analysis */}
                <div className="bg-[#161b22] border border-gray-800 rounded-3xl p-10 shadow-2xl">
                   <h3 className="text-2xl font-bold text-white mb-8 flex items-center gap-3">
                     <div className="w-1 h-8 bg-blue-500 rounded-full" />
                     Tese de Investimento (IA)
                   </h3>
                   <div className="prose prose-invert prose-lg max-w-none text-gray-300 leading-relaxed whitespace-pre-line">
                      {analysis.analise_texto}
                   </div>
                </div>

              </div>
            )}
          </div>
        )}

        {/* TAB: HISTORY / COMPARISON TABLE */}
        {activeTab === 'history' && (
          <div className="max-w-[1600px] mx-auto pb-20 md:pb-0 h-full flex flex-col">
             <div className="flex items-center justify-between mb-8">
               <div>
                  <h1 className="text-3xl font-bold text-white mb-2">Comparador de Ativos</h1>
                  <p className="text-gray-400">Compare fundamentalmente todas as empresas analisadas.</p>
               </div>
               
               <div className="flex gap-2 relative">
                  <button 
                    onClick={() => setShowColumnSelector(!showColumnSelector)}
                    className="flex items-center gap-2 px-4 py-2 bg-[#161b22] border border-gray-700 text-gray-300 rounded-lg hover:text-white transition-colors"
                  >
                    <Settings2 size={16} /> Colunas
                  </button>
                  
                  {showColumnSelector && (
                    <div className="absolute right-0 top-12 w-64 bg-[#161b22] border border-gray-700 rounded-xl shadow-2xl z-50 p-4">
                      <h4 className="text-white font-bold mb-3 text-sm">Exibir Colunas</h4>
                      <div className="space-y-2 max-h-60 overflow-y-auto">
                        {COLUMN_DEFINITIONS.map(col => (
                          <label key={col.key} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer hover:bg-gray-800 p-2 rounded">
                            <input 
                              type="checkbox" 
                              checked={columnVisibility[col.key]}
                              onChange={() => setColumnVisibility(prev => ({ ...prev, [col.key]: !prev[col.key] }))}
                              className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-offset-gray-900"
                            />
                            {col.label}
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
               </div>
             </div>

             <div className="flex-1 bg-[#161b22] border border-gray-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col">
                <div className="overflow-auto custom-scrollbar flex-1">
                  <table className="w-full border-collapse">
                    <thead className="bg-[#0d1117] sticky top-0 z-20">
                      <tr>
                        {COLUMN_DEFINITIONS.filter(c => columnVisibility[c.key]).map((col) => (
                          <th 
                            key={col.key}
                            className={`p-4 text-xs font-bold text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-800/50 transition-colors border-b border-gray-800 ${col.minWidth || ''}`}
                            onClick={() => handleSort(col.key)}
                          >
                            <div className={`flex items-center gap-2 justify-${col.align === 'center' ? 'center' : 'start'}`}>
                              {col.label}
                              {sortConfig?.key === col.key && (
                                sortConfig.direction === 'asc' ? <ArrowUp size={12} className="text-blue-500" /> : <ArrowDown size={12} className="text-blue-500" />
                              )}
                              {sortConfig?.key !== col.key && <ArrowUpDown size={12} className="text-gray-600 opacity-0 group-hover:opacity-100" />}
                            </div>
                          </th>
                        ))}
                        <th className="p-4 text-xs font-bold text-gray-400 uppercase border-b border-gray-800 w-16">Ações</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800/50">
                      {sortedHistory.map((row) => (
                        <tr key={row.id} className="hover:bg-gray-800/30 transition-colors group">
                           {COLUMN_DEFINITIONS.filter(c => columnVisibility[c.key]).map((col) => (
                             <td key={col.key} className={`p-4 text-sm whitespace-nowrap ${col.color || 'text-gray-300'} text-${col.align || 'left'}`}>
                               {col.key === 'nota_final' ? (
                                  <div className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-gray-800 border border-gray-700">
                                    {row[col.key]}
                                  </div>
                               ) : row[col.key]}
                             </td>
                           ))}
                           <td className="p-4 text-center">
                              <button 
                                onClick={() => handleDelete(row.id)}
                                className="text-gray-600 hover:text-red-400 transition-colors p-2 rounded-lg hover:bg-red-500/10"
                                title="Excluir Análise"
                              >
                                <Trash2 size={16} />
                              </button>
                           </td>
                        </tr>
                      ))}
                      {sortedHistory.length === 0 && (
                        <tr>
                          <td colSpan={COLUMN_DEFINITIONS.length + 1} className="p-12 text-center text-gray-500">
                            Nenhuma análise encontrada. Faça um upload para começar.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
             </div>
          </div>
        )}

      </main>

      {/* --- PAYMENT MODAL (ATUALIZADO) --- */}
      {showPaymentModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-[#161b22] w-full max-w-lg rounded-3xl border border-gray-800 shadow-2xl relative overflow-hidden">
             
             {/* Efeitos de Fundo */}
             <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500" />
             <div className="absolute -top-24 -right-24 w-48 h-48 bg-blue-500/20 blur-[80px] rounded-full pointer-events-none" />

             {/* Botão Fechar */}
             <button 
               onClick={() => setShowPaymentModal(false)}
               className="absolute top-4 right-4 p-2 text-gray-400 hover:text-white bg-gray-800/50 hover:bg-gray-700 rounded-full transition-all"
             >
               <X size={20} />
             </button>

             <div className="p-8 text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl mx-auto flex items-center justify-center shadow-lg shadow-blue-900/40 mb-6">
                   <Zap className="text-white w-8 h-8" fill="currentColor" />
                </div>

                <h3 className="text-2xl font-bold text-white mb-2">Desbloqueie o Poder da IA</h3>
                <p className="text-gray-400 mb-8">
                   Tenha acesso ilimitado a análises, histórico completo e relatórios detalhados.
                </p>

                {/* --- TOGGLE MENSAL / ANUAL --- */}
                <div className="flex justify-center mb-8">
                   <div className="bg-gray-900 p-1.5 rounded-xl flex items-center relative border border-gray-800">
                      <button 
                        onClick={() => setBillingCycle('monthly')}
                        className={`px-6 py-2 rounded-lg text-sm font-bold transition-all duration-300 z-10 ${
                          billingCycle === 'monthly' ? 'text-white shadow-lg' : 'text-gray-400 hover:text-white'
                        }`}
                      >
                        Mensal
                      </button>
                      <button 
                        onClick={() => setBillingCycle('yearly')}
                        className={`px-6 py-2 rounded-lg text-sm font-bold transition-all duration-300 z-10 flex items-center gap-2 ${
                          billingCycle === 'yearly' ? 'text-white shadow-lg' : 'text-gray-400 hover:text-white'
                        }`}
                      >
                        Anual
                        <span className="bg-green-500/20 text-green-400 text-[10px] px-1.5 py-0.5 rounded uppercase tracking-wider">
                          -20%
                        </span>
                      </button>
                      
                      {/* Fundo Animado do Toggle */}
                      <div className={`absolute top-1.5 bottom-1.5 w-[calc(50%-6px)] bg-gray-700 rounded-lg transition-all duration-300 ${
                         billingCycle === 'monthly' ? 'left-1.5' : 'left-[calc(50%+3px)]'
                      }`} />
                   </div>
                </div>

                {/* --- PREÇO DINÂMICO --- */}
                <div className="mb-8">
                   <div className="flex items-end justify-center gap-1">
                      <span className="text-5xl font-black text-white tracking-tight">
                        {billingCycle === 'monthly' ? 'R$ 29' : 'R$ 290'}
                      </span>
                      <span className="text-gray-500 mb-2 font-medium text-lg">
                        /{billingCycle === 'monthly' ? 'mês' : 'ano'}
                      </span>
                   </div>
                   {billingCycle === 'yearly' && (
                      <p className="text-green-400 text-sm mt-2 font-medium">Você economiza 2 meses!</p>
                   )}
                </div>

                {/* --- BOTÃO DE CHECKOUT DINÂMICO --- */}
                <a 
                   href={STRIPE_LINKS[billingCycle]}
                   target="_blank"
                   rel="noopener noreferrer"
                   className="block w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-900/30 hover:scale-[1.02] active:scale-[0.98] transition-all"
                >
                   Assinar Plano {billingCycle === 'monthly' ? 'Mensal' : 'Anual'}
                </a>
                
                <p className="mt-4 text-xs text-gray-500">
                   Pagamento seguro via Stripe. Cancele quando quiser.
                </p>
             </div>
          </div>
        </div>
      )}

    </div>
  );
}