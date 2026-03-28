import React, { useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { DollarSign, Percent, AlertCircle, TrendingUp, FileText } from 'lucide-react';

export default function ReportTemplate({ result, onPrintComplete }: { result: any, onPrintComplete: () => void }) {
  
  // Efeito que aciona a impressão logo após os gráficos renderizarem
  useEffect(() => {
    // Dá 800ms para os gráficos calcularem o tamanho e as animações terminarem
    const timer = setTimeout(() => {
      window.print();
    }, 800);

    // Quando o usuário fecha a tela de impressão, volta para o Dashboard
    const handleAfterPrint = () => {
      onPrintComplete();
    };

    window.addEventListener('afterprint', handleAfterPrint);
    
    return () => {
      clearTimeout(timer);
      window.removeEventListener('afterprint', handleAfterPrint);
    };
  }, [onPrintComplete]);

  if (!result) return null;

  const meta = result.metadata || {};
  const data = result.data || {};
  const empresa = (meta.empresa || "EMPRESA").toUpperCase();
  const trimestre = meta.trimestre || "";
  const ano = meta.ano || "";
  const periodo = trimestre ? `${trimestre} de ${ano}` : ano;
  const notaFinal = data.nota_geral ?? result.nota_geral ?? "—";
  const analise: string = result.analise_completa || "";

  const analiseLimpa = analise.trim();

  let chartData: any[] = [];
  try {
    const jsonMatch = analiseLimpa.match(/```json\s*([\s\S]*?)\s*```/);
    if (jsonMatch && jsonMatch[1]) {
      chartData = JSON.parse(jsonMatch[1]);
    }
  } catch (error) {
    console.error("Erro ao extrair dados para o gráfico:", error);
  }

  if (!chartData || chartData.length === 0) {
    chartData = [
      { name: 'Sem Dados', receita: 0, lucro: 0, margemBruta: 0, margemLiquida: 0 }
    ];
  }

  const getScoreColor = (n: any) => {
    const num = Number(n);
    if (isNaN(num)) return "text-slate-500 bg-slate-100 border-slate-200";
    if (num >= 4) return "text-emerald-700 bg-emerald-50 border-emerald-200";
    if (num >= 3) return "text-amber-700 bg-amber-50 border-amber-200";
    return "text-red-700 bg-red-50 border-red-200";
  };

  const sections = [
    { label: "Receita", nota: data.receita_nota ?? "—", icon: <DollarSign size={18} className="text-blue-500"/>, bg: "bg-blue-50 border-blue-100" },
    { label: "Margem", nota: data.lucro_nota ?? "—", icon: <Percent size={18} className="text-emerald-500"/>, bg: "bg-emerald-50 border-emerald-100" },
    { label: "Dívida", nota: data.divida_nota ?? "—", icon: <AlertCircle size={18} className="text-red-500"/>, bg: "bg-red-50 border-red-100" },
    { label: "Rentabilidade", nota: data.rentabilidade_nota ?? "—", icon: <TrendingUp size={18} className="text-amber-500"/>, bg: "bg-amber-50 border-amber-100" },
  ];

  const cleanText = (raw: string) => raw.replace(/\*\*[^*]+\*\*/g, "").replace(/Nota Seção \d+:[^\n]*/g, "").trim();
  const teseRaw = analise.match(/Seção 5[\s\S]*?(?=\*\*Seção 6|$)/);
  const teseBody = teseRaw ? cleanText(teseRaw[0]) : (data.tese_investimento || "Nenhuma tese detalhada disponível.");

  return (
    <div className="w-full min-h-screen bg-white text-slate-900 font-sans p-10">
      
      <div className="border-b border-slate-200 pb-6 mb-8 flex justify-between items-end">
        <div>
          <span className="text-xs font-bold text-blue-600 uppercase tracking-wider bg-blue-50 px-3 py-1 rounded-full border border-blue-100 mb-4 inline-block">
            {periodo}
          </span>
          <h1 className="text-4xl font-extrabold text-slate-950 tracking-tight mt-2">
            Análise de Resultados<br />{empresa}
          </h1>
        </div>
        
        <div className={`px-6 py-4 rounded-xl border ${getScoreColor(notaFinal)} flex items-center gap-6`}>
          <div className="text-right">
            <p className="text-xs font-bold uppercase tracking-wider opacity-80">Score IA</p>
            <p className="text-[10px] opacity-60">Média ponderada</p>
          </div>
          <div className="text-4xl font-black leading-none">{notaFinal}<span className="text-lg opacity-50">/5</span></div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-10">
        {sections.map((s, idx) => (
          <div key={idx} className={`p-5 rounded-xl border ${s.bg}`}>
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm font-semibold text-slate-700">{s.label}</span>
              {s.icon}
            </div>
            <div className="text-3xl font-black text-slate-900">{s.nota}<span className="text-sm text-slate-500 font-medium">/5</span></div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-8 mb-10">
        <div className="border border-slate-200 rounded-xl p-6 bg-white shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-6 border-b border-slate-100 pb-3">Evolução de Receita e Lucro</h3>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
                <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Bar dataKey="receita" fill="#2563eb" radius={[4, 4, 0, 0]} maxBarSize={40} isAnimationActive={false} />
                <Bar dataKey="lucro" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={40} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="border border-slate-200 rounded-xl p-6 bg-white shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-6 border-b border-slate-100 pb-3">Margens Financeiras</h3>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
                <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Line type="monotone" dataKey="margemBruta" stroke="#8b5cf6" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} isAnimationActive={false} />
                <Line type="monotone" dataKey="margemLiquida" stroke="#f59e0b" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-slate-950 text-white rounded-2xl p-8 break-inside-avoid">
        <div className="flex items-center gap-3 mb-6">
          <FileText className="text-blue-500" />
          <h2 className="text-xl font-bold">Conclusão Estratégica</h2>
        </div>
        <div className="space-y-4 text-slate-300 text-sm leading-relaxed">
          {teseBody.split("\n\n").map((paragraph: string, idx: number) => (
            <p key={idx}>{paragraph.replace(/\*\*/g, "")}</p>
          ))}
        </div>
      </div>
      
    </div>
  );
}