"use client";
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  LayoutDashboard, History, UploadCloud, FileText, Download, ChevronLeft,
  BarChart3, TrendingUp, DollarSign, Percent, Activity, LogOut, Loader2,
  AlertCircle, Table as TableIcon, Trash2, ArrowUpDown, ArrowUp, ArrowDown,
  GripVertical, Eye, EyeOff, Settings2, X
} from "lucide-react";

// --- CONFIGURAÇÃO DAS COLUNAS ---
const COLUMN_DEFINITIONS = [
  { key: 'empresa', label: 'Empresa', align: 'center', minWidth: 'min-w-[140px]', color: 'text-white font-bold' },
  { key: 'nota_final', label: 'Nota do Último Resultado', align: 'center', color: 'text-purple-400 font-bold' },
  { key: 'receita_nota', label: 'Receita', align: 'center', color: 'text-blue-400' },
  { key: 'lucro_nota', label: 'Lucro', align: 'center', color: 'text-green-400' },
  { key: 'divida_nota', label: 'Dívida', align: 'center', color: 'text-red-400' },
  { key: 'rentabilidade_nota', label: 'Rentabilidade', align: 'center', color: 'text-yellow-400' },
  { key: 'soma_total', label: 'Soma', align: 'center', bg: 'bg-blue-900/10', color: 'text-blue-200' },
  { key: 'qtde_tri', label: 'Resultados Analisados', align: 'center', bg: 'bg-purple-900/10', color: 'text-purple-200' },
  { key: 'media', label: 'Média', align: 'center', bg: 'bg-green-900/10', color: 'text-green-200' },
  { key: 'last_analysed_quarter', label: 'Último Tri', align: 'center', color: 'text-gray-400 font-bold' },
];

// --- COMPONENTES AUXILIARES ---
function NavItem({ icon, label, active = false, onClick }: any) {
  return (
    <button onClick={onClick} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${active ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}>
      {React.cloneElement(icon, { size: 20 })}<span className="font-medium text-sm">{label}</span>{active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white animate-pulse" />}
    </button>
  );
}

// --- COMPONENTE PRINCIPAL ---
export default function FinancialDashboard() {
  const router = useRouter();

  // --- CONFIGURAÇÃO DA API ---
  const API_BASE = "https://api-finanalyzer.onrender.com"; 

  // ESTADOS GERAIS
  const [currentView, setCurrentView] = useState<'dashboard' | 'history' | 'result' | 'table'>('dashboard');
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<any>(null); // --- NOVO: Estado do Usuário

  // DADOS DA API
  const [result, setResult] = useState<any>(null);
  const [historyList, setHistoryList] = useState<any[]>([]);
  const [tableData, setTableData] = useState<any[]>([]);

  // ESTADOS DE TABELA
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
  
  // FORMULÁRIO
  const [empresa, setEmpresa] = useState("");
  const [ano, setAno] = useState("");
  const [trimestre, setTrimestre] = useState("1T");
  const [file, setFile] = useState<File | null>(null);

  // --- EFEITO 1: RECUPERAR USUÁRIO NO LOAD ---
  useEffect(() => {
    const storedUser = localStorage.getItem('usuario');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    } else {
      router.push('/login'); // Chuta para login se não tiver usuário
    }
  }, [router]);

  const columnDefsMap = useMemo(() => {
    return COLUMN_DEFINITIONS.reduce((acc, col) => {
      acc[col.key] = col;
      return acc;
    }, {} as Record<string, typeof COLUMN_DEFINITIONS[0]>);
  }, []);

  const visibleCount = useMemo(() => Object.values(visibleColumns).filter(Boolean).length, [visibleColumns]);

  const handleLogout = () => {
    localStorage.removeItem('usuario');
    router.push('/login');
  };

  // --- CHAMADAS DE API CORRIGIDAS COM USER_ID ---
  
  const fetchHistory = async () => {
    if (!user) return; // Só busca se tiver usuário
    try {
      // --- CORREÇÃO: Envia user_id na URL ---
      const res = await fetch(`${API_BASE}/api/history?user_id=${user.id}`);
      const data = await res.json();
      setHistoryList(data);
    } catch (error) {
      console.error("Erro ao buscar histórico", error);
    }
  };

  const fetchTableData = async () => {
    if (!user) return; // Só busca se tiver usuário
    try {
      // --- CORREÇÃO: Envia user_id na URL ---
      const res = await fetch(`${API_BASE}/api/table-data?user_id=${user.id}`);
      const data = await res.json();
      setTableData(data);
    } catch (error) {
      console.error("Erro ao buscar dados da tabela", error);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!confirm("Tem certeza que deseja excluir esta análise?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/history/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error("Erro ao deletar");
      fetchHistory();
      fetchTableData();
    } catch (error) {
      alert("Erro ao excluir item.");
    }
  };

  const handleAnalyze = async () => {
    if (!file || !empresa || !ano) {
      alert("Preencha todos os campos!");
      return;
    }
    if (!user) {
        alert("Erro de autenticação. Faça login novamente.");
        return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("empresa", empresa);
      formData.append("ano", ano);
      formData.append("trimestre", trimestre);
      
      // --- CORREÇÃO: Envia o ID do usuário junto com o arquivo ---
      formData.append("user_id", user.id); 

      const response = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        body: formData
      });

      if (!response.ok) throw new Error("Erro na requisição");
      const data = await response.json();
      setResult(data);
      setCurrentView('result');
      fetchHistory();
      fetchTableData();
    } catch (error) {
      console.error(error);
      alert("Erro na análise.");
    } finally {
      setLoading(false);
    }
  };

  // --- EFEITO 2: CARREGAR DADOS AO MUDAR DE TELA ---
  useEffect(() => {
    if (user) { // Só carrega dados se o usuário estiver pronto
        if (currentView === 'history') fetchHistory();
        if (currentView === 'table') fetchTableData();
    }
    
    const handleClickOutside = (event: MouseEvent) => {
      if (columnMenuRef.current && !columnMenuRef.current.contains(event.target as Node)) {
        setShowColumnMenu(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [currentView, user]); // Adicionado 'user' nas dependências

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) setFile(e.target.files[0]);
  };

  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key) {
      direction = sortConfig.direction === 'asc' ? 'desc' : 'asc';
    } else if (['media', 'soma_total', 'qtde_tri', 'nota_final', 'ano'].includes(key)) {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const toggleColumn = (key: string) => setVisibleColumns(prev => ({ ...prev, [key]: !prev[key] }));
  const onDragStart = (index: number) => setDraggedItemIndex(index);
  const onDragEnter = (index: number) => {
    if (draggedItemIndex === null || draggedItemIndex === index) return;
    const newOrder = [...columnOrder];
    const draggedItem = newOrder[draggedItemIndex];
    newOrder.splice(draggedItemIndex, 1);
    newOrder.splice(index, 0, draggedItem);
    setColumnOrder(newOrder);
    setDraggedItemIndex(index);
  };
  const onDragEnd = () => setDraggedItemIndex(null);

  const sortedTableData = useMemo(() => {
    if (!sortConfig) return tableData;
    return [...tableData].sort((a, b) => {
      if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
      if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [tableData, sortConfig]);

  const handleDownload = () => {
    if (!result) return;
    const r = result;
    const data = r.data || {};
    const meta = r.metadata || {};
    const conteudoPrincipal = r.analise_completa ? r.analise_completa : `RESUMO DA TESE:\n${data.tese_investimento || 'Sem dados.'}`;
    const relatorioTexto = `RELATÓRIO DE ANÁLISE FINANCEIRA - IA\nEmpresa: ${meta.empresa}\nPeríodo: ${meta.periodo}\n\n${conteudoPrincipal}`;
    const blob = new Blob([relatorioTexto], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `Relatorio_${meta.empresa}.txt`;
    link.click();
  };

  const renderCellContent = (item: any, key: string, colDef: any) => {
    if (key === 'trimestre') return <span className="bg-blue-900/30 text-blue-300 py-1 px-2 rounded text-xs font-bold border border-blue-500/20">{item[key]}</span>;
    if (key === 'media') return <span className={`px-2 py-1 rounded font-bold ${item.media >= 4 ? 'text-green-400' : 'text-yellow-400'}`}>{item[key]}</span>;
    if (key.includes('nota') || key === 'nota_final') {
      const val = item[key];
      return <span className={`font-bold text-base ${val >= 4 ? 'text-emerald-400' : val >= 3 ? 'text-yellow-400' : 'text-red-400'}`}>{val}</span>;
    }
    return <span className={`${colDef.color || 'text-gray-300'}`}>{item[key]}</span>;
  };

  return (
    <div className="flex h-screen bg-[#0E1117] text-gray-100 font-sans overflow-hidden">
      <aside className="w-72 bg-[#0d1117] border-r border-gray-800 flex flex-col justify-between p-6 z-20">
        <div>
          <div className="flex items-center gap-3 mb-10 px-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-900/20">
              <BarChart3 className="text-white w-5 h-5" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">FinAnalyzer <span className="text-blue-500">.AI</span></span>
          </div>
          <nav className="space-y-2">
            <NavItem icon={<LayoutDashboard />} label="Nova Análise" active={currentView === 'dashboard'} onClick={() => setCurrentView('dashboard')} />
            <NavItem icon={<TableIcon />} label="Tabela Agregada" active={currentView === 'table'} onClick={() => setCurrentView('table')} />
            <NavItem icon={<History />} label="Histórico" active={currentView === 'history'} onClick={() => setCurrentView('history')} />
          </nav>
        </div>
        <button onClick={handleLogout} className="flex items-center gap-3 px-4 py-3 text-gray-500 hover:text-white hover:bg-white/5 rounded-xl transition-all duration-300 group cursor-pointer">
          <LogOut size={20} className="group-hover:text-red-400 transition-colors" />
          <span className="font-medium">Sair</span>
        </button>
      </aside>
      <main className="flex-1 overflow-y-auto p-8 relative">
        {currentView === 'table' && (
          <div className="animate-in fade-in duration-500 max-w-[98%] mx-auto pb-20">
            <header className="flex items-center justify-between mb-8">
              <div><h1 className="text-3xl font-bold text-white tracking-tight">Tabela Agregada</h1><p className="text-gray-400 mt-1">Visão consolidada do desempenho das empresas.</p></div>
              <div className="relative" ref={columnMenuRef}>
                <button onClick={() => setShowColumnMenu(!showColumnMenu)} className={`flex items-center gap-2 border px-4 py-2 rounded-xl transition-all shadow-lg ${showColumnMenu ? 'bg-blue-600 border-blue-500 text-white' : 'bg-[#161b22] border-gray-700 hover:border-blue-500 text-gray-300'}`}>
                  <Settings2 size={18} /><span>Configurar Colunas</span>
                </button>
                {showColumnMenu && (
                  <div className="absolute right-0 mt-3 w-80 bg-[#161b22]/95 backdrop-blur-md border border-gray-700 rounded-2xl shadow-2xl z-50 overflow-hidden animate-in fade-in zoom-in-95 origin-top-right">
                    <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-[#0d1117]/50"><span className="text-sm font-bold text-white">Visualização de Colunas</span><button onClick={() => setShowColumnMenu(false)} className="text-gray-400 hover:text-white"><X size={16} /></button></div>
                    <div className="p-2 max-h-[400px] overflow-y-auto space-y-1">
                      <p className="px-2 py-1 text-xs text-gray-500 font-medium uppercase tracking-wider mb-2">Arraste para reordenar</p>
                      {columnOrder.map((colKey, index) => {
                        const colDef = columnDefsMap[colKey];
                        const isVisible = visibleColumns[colKey];
                        return (
                          <div key={colKey} draggable onDragStart={() => onDragStart(index)} onDragEnter={() => onDragEnter(index)} onDragEnd={onDragEnd} onClick={() => toggleColumn(colKey)} className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all border border-transparent ${draggedItemIndex === index ? 'bg-blue-900/20 border-blue-500/50 opacity-50' : 'hover:bg-white/5 hover:border-gray-700'}`}>
                            <div className="flex items-center gap-3"><div className="cursor-grab text-gray-600 hover:text-gray-300"><GripVertical size={16} /></div><span className={`text-sm font-medium ${isVisible ? 'text-gray-200' : 'text-gray-500'}`}>{colDef.label}</span></div>
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
                            <div className={`flex items-center gap-2 ${col.align === 'center' ? 'justify-center' : ''}`}><GripVertical size={12} className="text-gray-700 group-hover:text-gray-400 transition-colors opacity-0 group-hover:opacity-100" />{col.label}{sortConfig?.key === col.key ? (sortConfig.direction === 'asc' ? <ArrowUp size={12} className="text-blue-400"/> : <ArrowDown size={12} className="text-blue-400"/>) : <ArrowUpDown size={12} className="opacity-0 group-hover:opacity-30 transition-opacity"/>}</div>
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
              {sortedTableData.length === 0 && <div className="p-12 text-center text-gray-500">Nenhuma análise disponível.</div>}
            </div>
          </div>
        )}
        {currentView === 'history' && (
          <div className="animate-in fade-in duration-500 max-w-6xl mx-auto">
            <header className="flex items-center justify-between mb-8"><div><h1 className="text-3xl font-bold text-white tracking-tight">Histórico Detalhado</h1><p className="text-gray-400 mt-1">Gerencie suas análises individuais.</p></div></header>
            <div className="bg-[#161b22] border border-gray-800 rounded-2xl shadow-xl overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead><tr className="border-b border-gray-800 bg-[#0d1117]/50 text-xs uppercase tracking-wider text-gray-500"><th className="py-5 px-6 font-semibold">Empresa</th><th className="py-5 px-6 font-semibold">Período</th><th className="py-5 px-6 font-semibold">Data</th><th className="py-5 px-6 text-center font-semibold">Score</th><th className="py-5 px-6 text-right font-semibold">Ações</th></tr></thead>
                <tbody className="divide-y divide-gray-800">
                  {historyList.map((item: any) => (
                    <tr key={item.id} className="hover:bg-white/[0.02] transition-colors group cursor-pointer" onClick={() => { setResult(item.conteudo); setEmpresa(item.empresa); setCurrentView('result'); }}>
                      <td className="py-4 px-6"><div className="flex items-center gap-3"><span className="font-medium text-gray-200">{item.empresa}</span></div></td>
                      <td className="py-4 px-6 text-gray-400">{item.periodo}</td>
                      <td className="py-4 px-6 text-gray-500 text-sm">{item.data}</td>
                      <td className="py-4 px-6 text-center"><span className={`inline-flex items-center justify-center w-12 h-8 rounded-lg text-sm font-bold ${item.nota >= 4 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : item.nota >= 3 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>{item.nota}</span></td>
                      <td className="py-4 px-6 text-right"><div className="flex items-center justify-end gap-3"><button onClick={(e) => handleDelete(e, item.id)} className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-colors" title="Excluir"><Trash2 size={16} /></button><button className="text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1">Detalhes <ChevronLeft className="w-4 h-4 rotate-180" /></button></div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {historyList.length === 0 && <div className="p-12 text-center text-gray-500">Histórico vazio.</div>}
            </div>
          </div>
        )}
        {currentView === 'dashboard' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-3xl mx-auto mt-10">
            {loading ? (
              <div className="flex flex-col items-center justify-center h-96 animate-in fade-in"><Loader2 className="w-16 h-16 text-blue-500 animate-spin mb-6" /><h2 className="text-3xl font-bold animate-pulse text-white mb-2">Analisando Dados...</h2><p className="text-gray-400">Nossa IA está processando o relatório e calculando os indicadores.</p></div>
            ) : (
              <>
                <div className="text-center mb-12"><h1 className="text-4xl font-bold text-white mb-3 tracking-tight">Nova Análise Financeira</h1><p className="text-gray-400 text-lg">Carregue o relatório trimestral (PDF) para processamento via IA.</p></div>
                <div className="bg-[#161b22] border border-gray-800 rounded-2xl p-8 shadow-2xl relative overflow-hidden group hover:border-gray-700 transition-colors duration-500">
                  <div className="grid grid-cols-3 gap-6 mb-8">
                    <div className="space-y-2"><label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Empresa</label><input type="text" placeholder="Ex: Apple" className="w-full bg-[#0d1117] border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all" value={empresa} onChange={(e) => setEmpresa(e.target.value)} /></div>
                    <div className="space-y-2"><label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Ano</label><input type="text" placeholder="2025" className="w-full bg-[#0d1117] border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all" value={ano} onChange={(e) => setAno(e.target.value)} /></div>
                    <div className="space-y-2"><label className="text-xs font-bold text-gray-500 uppercase tracking-wider">Trimestre</label><select className="w-full bg-[#0d1117] border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none transition-all appearance-none" value={trimestre} onChange={(e) => setTrimestre(e.target.value)}><option value="1T">1º Trimestre</option><option value="2T">2º Trimestre</option><option value="3T">3º Trimestre</option><option value="4T">4º Trimestre</option></select></div>
                  </div>
                  <div className="border-2 border-dashed border-gray-700 rounded-xl p-10 flex flex-col items-center justify-center bg-[#0d1117]/50 hover:bg-[#0d1117] hover:border-blue-500/50 transition-all duration-300 cursor-pointer relative">
                    <input type="file" onChange={handleFileChange} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" /><div className="bg-gray-800 p-4 rounded-full mb-4 group-hover:scale-110 transition-transform duration-300"><UploadCloud className="text-blue-400 w-8 h-8" /></div><p className="text-gray-300 font-medium text-lg">{file ? file.name : "Clique ou arraste o PDF aqui"}</p><p className="text-gray-500 text-sm mt-2">Suporta PDF de até 10MB</p>
                  </div>
                  <button onClick={handleAnalyze} className="w-full mt-8 bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-900/20 transition-all duration-300 flex items-center justify-center gap-2"><Activity size={20} /> Gerar Análise Completa</button>
                </div>
              </>
            )}
          </div>
        )}
        {currentView === 'result' && result && (
          <div className="animate-in fade-in zoom-in duration-500 max-w-6xl mx-auto pb-10">
            <div className="flex justify-between items-center mb-10">
              <button onClick={() => setCurrentView('history')} className="text-gray-400 hover:text-white flex items-center gap-2 transition-colors group"><div className="p-2 rounded-full bg-gray-800 group-hover:bg-gray-700 transition-colors"><ChevronLeft size={16} /></div><span className="font-medium">Voltar para Histórico</span></button>
              <button onClick={handleDownload} className="bg-green-600 hover:bg-green-500 text-white px-6 py-2.5 rounded-lg font-bold flex items-center gap-2 shadow-lg transition-all"><Download size={18} /> Baixar Relatório</button>
            </div>
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-12 border-b border-gray-800 pb-8">
              <div><h2 className="text-gray-500 uppercase tracking-widest text-xs font-bold mb-2">Relatório de Análise</h2><h1 className="text-5xl font-bold text-white mb-2">{result.metadata?.empresa}</h1><p className="text-xl text-blue-400 font-medium">{result.metadata?.periodo}</p></div>
              <div className="flex items-center gap-6 bg-[#161b22] p-6 rounded-2xl border border-gray-800"><div className="text-right"><p className="text-sm text-gray-400 font-medium uppercase">Score IA</p><p className="text-xs text-gray-500">Baseado em 4 fundamentos</p></div><div className={`text-4xl font-bold ${(result.data?.nota_geral || 0) >= 4 ? 'text-emerald-400' : 'text-amber-400'}`}>{result.data?.nota_geral}<span className="text-lg text-gray-600">/5</span></div></div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
              {[{ label: "Receita", val: result.data?.receita_nota, icon: <DollarSign size={20} className="text-blue-400" /> }, { label: "Margem", val: result.data?.lucro_nota, icon: <Percent size={20} className="text-purple-400" /> }, { label: "Dívida", val: result.data?.divida_nota, icon: <AlertCircle size={20} className="text-red-400" /> }, { label: "ROE", val: result.data?.rentabilidade_nota, icon: <TrendingUp size={20} className="text-emerald-400" /> }].map((item, idx) => (
                <div key={idx} className="bg-[#161b22] border border-gray-800 p-6 rounded-2xl hover:border-gray-700 transition-all duration-300">
                  <div className="flex items-center justify-between mb-4"><span className="text-gray-400 text-sm font-medium">{item.label}</span><div className="bg-gray-900 p-2 rounded-lg">{item.icon}</div></div>
                  <div className="flex items-end gap-2"><span className="text-3xl font-bold text-white">{item.val}</span><span className="text-gray-600 text-sm mb-1">/5</span></div>
                  <div className="w-full bg-gray-800 h-1 mt-4 rounded-full overflow-hidden"><div className={`h-full ${(item.val || 0) >= 4 ? 'bg-green-500' : (item.val || 0) >= 3 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${((item.val || 0) / 5) * 100}%` }} /></div>
                </div>
              ))}
            </div>
            <div className="bg-[#161b22] border border-gray-800 rounded-3xl p-10 shadow-2xl"><h3 className="text-2xl font-bold text-white mb-8 flex items-center gap-3"><FileText className="text-blue-500" /> Tese de Investimento</h3><div className="prose prose-invert prose-lg max-w-none text-gray-300 leading-relaxed whitespace-pre-line">{result.data?.tese_investimento ? result.data.tese_investimento : "Sem análise textual disponível."}</div></div>
          </div>
        )}
      </main>
    </div>
  );
}