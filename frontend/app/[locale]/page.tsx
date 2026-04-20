"use client";

import React, { useState, useRef, useEffect } from 'react';
import { motion, useInView } from "framer-motion";
import { useTranslations, useLocale } from "next-intl";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import { Link } from "@/i18n/routing";
import {
  BarChart3, UploadCloud, ArrowRight,
  FileText, Layout, Database, Check, X,
  Trash2, ChevronRight, DollarSign, Percent,
  AlertCircle, TrendingUp, Download, ChevronLeft, Menu, Activity, Mic
} from "lucide-react";

// --- DADOS FAKE (MOCK) ---
const historicoData = [
  { empresa: "ITAÚ", periodo: "4T/2026", data: "05/03/2026", score: 5 },
  { empresa: "PETROBRAS", periodo: "4T/2026", data: "05/03/2026", score: 4 },
  { empresa: "APPLE", periodo: "4T/2026", data: "04/03/2026", score: 3 },
  { empresa: "GOOGLE", periodo: "4T/2025", data: "04/03/2026", score: 5 },
  { empresa: "BROADCOM", periodo: "1T/2026", data: "04/03/2026", score: 5 },
  { empresa: "RAIA DROGASIL", periodo: "4T/2025", data: "04/03/2026", score: 4 },
  { empresa: "TESLA", periodo: "4T/2025", data: "03/03/2026", score: 3 },
  { empresa: "AMAZON", periodo: "4T/2025", data: "27/02/2026", score: 4 },
  { empresa: "COCA COLA", periodo: "4T/2025", data: "26/02/2026", score: 4 },
];

const scoreMetrics = [
  { label: "Receita", icon: DollarSign, color: "text-blue-400", score: 5 },
  { label: "Margem", icon: Percent, color: "text-purple-400", score: 5 },
  { label: "Dívida", icon: AlertCircle, color: "text-red-400", score: 5 },
  { label: "ROE", icon: TrendingUp, color: "text-emerald-400", score: 5 },
];

const reportMetrics = [
  { id: "REV", title: "Receita", score: "5.0", badge: "Excelente", tagClass: "bg-emerald-100 text-emerald-700 border-emerald-200", barColor: "bg-emerald-500" },
  { id: "M&L", title: "Margem & Lucro", score: "5.0", badge: "Excelente", tagClass: "bg-emerald-100 text-emerald-700 border-emerald-200", barColor: "bg-emerald-500" },
  { id: "RISC", title: "Dívida & Risco", score: "5.0", badge: "Excelente", tagClass: "bg-emerald-100 text-emerald-700 border-emerald-200", barColor: "bg-emerald-500" },
  { id: "ROE", title: "Rentabilidade ROE", score: "4.0", badge: "Bom", tagClass: "bg-emerald-50 text-emerald-600 border-emerald-100", barColor: "bg-emerald-400" }
];

const reportBannerStats = [
  { value: "76.44 Bi", label: "RECEITA", var: "18.1%", isPos: true },
  { value: "27.23 Bi", label: "LUCRO", var: "23.6%", isPos: true },
  { value: "68.58%", label: "MG. BRUTA", var: "1.5%", isPos: false },
  { value: "35.63%", label: "MG. LÍQUIDA", var: "4.6%", isPos: true },
  { value: "5.0/5", label: "SCORE IA", var: null, isPos: true },
];

const teseLines = [
  "A Microsoft entregou um resultado excepcional no quarto trimestre fiscal de 2025, validando e fortalecendo a tese de investimento na empresa como uma líder indiscutível na era da nuvem e da inteligência artificial.",
  "Os números superaram as expectativas em todas as linhas principais, demonstrando a capacidade da Microsoft de traduzir a demanda do mercado em crescimento lucrativo e eficiente.",
  "Os principais drivers foram o crescimento robusto e de alta qualidade da receita, impulsionado pelo desempenho estelar do segmento Intelligent Cloud (especialmente Azure) e pela resiliência de Productivity and Business Processes.",
  "A empresa demonstrou uma notável alavancagem operacional, com o lucro operacional crescendo acima da receita e uma expansão significativa das margens.",
  "Além disso, a Microsoft reforçou sua já invejável estrutura de capital, com forte geração de fluxo de caixa livre e redução da dívida bruta.",
  "O outlook da empresa é extremamente positivo, com sua liderança em IA e nuvem assegurando um caminho de crescimento sustentável e de alto valor.",
];

const reportSections = [
  {
    title: "Desempenho de Receita",
    score: 5,
    content: [
      "A Alphabet entregou uma receita consolidada de $113.8 bilhões no 4T/2025, um aumento robusto de 18% em relação ao mesmo período do ano anterior (ou 17% em moeda constante). Este crescimento foi amplamente impulsionado pelas divisões Google Services e Google Cloud.",
      "Aumentou 14% para $95.9 bilhões. Dentro deste segmento, o Google Search & other apresentou um forte crescimento de 17%, e as receitas de assinaturas, plataformas e dispositivos cresceram 17%, indicando uma bem-sucedida diversificação e retenção de usuários. O YouTube Ads cresceu de forma mais moderada em 9%, embora a receita anual total do YouTube (ads e assinaturas) tenha superado $60 bilhões em 2025. O Google Network, por sua vez, registrou uma leve queda de 1.5% para $7.83 bilhões, sendo um ponto de atenção menor no trimestre.",
      "Demonstrou um crescimento excepcional de 48%, atingindo $17.7 bilhões em receita. Este segmento continua a ser um motor de crescimento vital, com forte demanda pela Google Cloud Platform (GCP), especialmente em infraestrutura e soluções de IA empresarial, alcançando uma taxa de execução anual de mais de $70 bilhões.",
      "A receita diminuiu 7.5% para $370 milhões, sublinhando que essas iniciativas ainda estão em estágios iniciais e não contribuem materialmente para a linha superior no curto prazo. O operacional foi um ponto forte, com o Search apresentando mais uso do que nunca e a demanda por produtos de IA impulsionando o crescimento da Cloud, refletindo o sucesso da estratégia de inovação da empresa."
    ]
  },
  {
    title: "Rentabilidade e Eficiência",
    score: 4,
    content: [
      "O lucro operacional consolidado da Alphabet cresceu 16%, atingindo $35.93 bilhões. A margem operacional consolidada foi de 31.6%, uma ligeira redução em comparação aos 32% do 4T/2024.",
      "Apresentou um aumento significativo no lucro operacional, alcançando $40.13 bilhões, indicando que a maior parte do crescimento da receita foi convertida em lucratividade.",
      "Aumentou seu lucro operacional para $5.31 bilhões, mais que dobrando em relação aos $2.09 bilhões do ano anterior. Isso demonstra uma melhora substancial na eficiência operacional e na alavancagem do segmento de nuvem à medida que escala.",
      "O prejuízo operacional se ampliou significativamente para $3.62 bilhões, de $1.17 bilhão no ano anterior, refletindo os contínuos e pesados investimentos em P&D para essas ventures.",
      "As despesas associadas a estas atividades mais que dobraram, chegando a $5.89 bilhões (de $2.78 bilhões), principalmente devido a P&D compartilhado em IA e um encargo de compensação de funcionários de $2.1 bilhões para a Waymo. Este último foi um fator pontual que pressionou a margem operacional consolidada.",
      "Apesar da leve compressão da margem consolidada, os segmentos operacionais core (Google Services e Google Cloud) exibiram forte rentabilidade e ganhos de eficiência, compensando os investimentos em Other Bets e em IA a nível corporativo. A compressão na margem consolidada é vista como um resultado de investimentos estratégicos de longo prazo, ao invés de uma perda de eficiência fundamental."
    ]
  },
  {
    title: "Estrutura de Capital",
    score: 4,
    content: [
      "A Alphabet mantém uma posição de liquidez extremamente robusta, com caixa, equivalentes de caixa e títulos negociáveis totalizando $126.84 bilhões no final de 2025, acima dos $95.66 bilhões em 2024.",
      "A dívida de longo prazo aumentou significativamente para $46.55 bilhões, em comparação com $10.88 bilhões no ano anterior. Este aumento foi impulsionado pela emissão de $24.8 bilhões em notas seniores não garantidas em novembro de 2025, destinadas a fins corporativos gerais. Mesmo com este aumento, a Alphabet permanece em uma confortável posição de caixa líquido.",
      "As despesas com juros aumentaram para $298 milhões (de $53 milhões), refletindo a maior dívida, mas permanecem totalmente gerenciáveis dada a escala da empresa.",
      "Houve uma contribuição positiva substancial, que aumentou para $3.18 bilhões (de $1.27 bilhão), impulsionada principalmente por um ganho de $2.30 bilhões em títulos de capital.",
      "A empresa declarou um dividendo trimestral em dinheiro de $0.21 por ação, sinalizando um novo estágio de maturidade e um compromisso com o retorno direto aos acionistas, complementando seu programa de recompra de ações.",
      "A expectativa de CapEx para 2026, entre $175 bilhões e $185 bilhões, é um ponto crucial. Representa um salto gigantesco em relação aos $91.45 bilhões de 2025, indicando um ciclo de investimento agressivo e estratégico em infraestrutura de IA, que será financiado por sua robusta geração de caixa e o capital levantado via dívida. A estrutura de capital permanece sólida, e o aumento da dívida é uma alocação estratégica de capital para financiar um futuro de intensos investimentos em IA, sem comprometer a saúde financeira da empresa."
    ]
  },
  {
    title: "Lucratividade",
    score: 4,
    content: [
      "O Lucro Líquido da Alphabet para o 4T/2025 atingiu $34.46 bilhões, um crescimento notável de 30% em relação ao ano anterior. O Lucro por Ação (EPS) diluído subiu 31% para $2.82.",
      "O principal motor do crescimento do lucro foi o forte desempenho operacional, liderado pelo crescimento robusto da receita em Search e Google Cloud, combinado com a melhoria da rentabilidade e eficiência nessas divisões. Além disso, o aumento nas Outras Receitas (Despesas), líquidas, impulsionado por ganhos em títulos de capital, contribuiu positivamente para o lucro final.",
      "O ganho de $2.30 bilhões em títulos de capital é um item não operacional e pode ter componentes não-caixa ou voláteis. Este item adicionou aproximadamente $1.8 bilhão ao lucro líquido. Embora impactante, o lucro líquido, mesmo ajustado para este ganho, teria demonstrado um crescimento forte.",
      "O lucro operacional foi impactado negativamente por um encargo de $2.1 bilhões relacionado à compensação de funcionários da Waymo. Este item, de caráter mais pontual, mostra que o desempenho operacional subjacente foi ainda mais forte do que o reportado.",
      "Apesar desses itens específicos, o crescimento do lucro é de alta qualidade e sustentável, fundamentado na força das operações core da Alphabet. Os investimentos agressivos em IA e infraestrutura para 2026, embora afetem o fluxo de caixa livre no curto prazo, são essenciais para manter a liderança tecnológica e impulsionar o crescimento futuro."
    ]
  }
];

const teseContent = [
  "A Alphabet entregou um crescimento de receita impressionante de 18%, impulsionado pelo vigor do Google Search e, mais notavelmente, pela aceleração e crescente lucratividade do Google Cloud, que se consolida como um pilar essencial de crescimento. O lucro líquido cresceu de forma expressiva em 30%, beneficiado por um desempenho operacional robusto e ganhos em títulos de capital.",
  "A tese principal é que a Alphabet está em uma posição privilegiada para capitalizar na era da Inteligência Artificial. Seus resultados demonstram a capacidade de gerar crescimento de receita e lucro em seus segmentos core, enquanto investe agressivamente para garantir relevância e liderança futura."
];

// --- COMPONENTES AUXILIARES ---

function Feature({ text, active = false, disabled = false, light = false }: { text: string; active?: boolean; disabled?: boolean; light?: boolean }) {
  return (
    <li className="flex items-center gap-3">
      {disabled ? (
        <div className="p-1 rounded-full border border-gray-600 text-gray-500 flex-shrink-0"><X size={11} /></div>
      ) : (
        <div className={`p-1 rounded-full flex-shrink-0 ${light ? 'bg-white text-blue-600' : 'bg-blue-600 text-white'}`}>
          <Check size={11} strokeWidth={3} />
        </div>
      )}
      <span className={`text-base font-medium tracking-tight ${disabled ? 'text-gray-500 line-through' : light ? 'text-white' : 'text-gray-100'}`}>{text}</span>
    </li>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 4
      ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
      : score >= 3
        ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/40"
        : "bg-red-500/20 text-red-400 border-red-500/40";

  return (
    <span className={`inline-flex items-center justify-center w-10 h-10 rounded-xl text-sm font-bold border ${color}`}>
      {score}
    </span>
  );
}

function ScoreMetricBar({ score, animate }: { score: number; animate: boolean }) {
  return (
    <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden mt-3">
      <div
        className="h-full bg-emerald-500 rounded-full transition-all duration-1000 ease-out"
        style={{ width: animate ? `${(score / 5) * 100}%` : "0%" }}
      />
    </div>
  );
}

function PhoneImage() {
  const locale = useLocale();
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: false, margin: "-100px" });
  const [isDark, setIsDark] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (isInView) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => {
        setIsDark(prev => !prev);
      }, 2000);
    } else {
      if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
      setIsDark(true);
    }
    return () => { if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; } };
  }, [isInView]);

  const d = isDark;
  const screen = d ? "bg-[#0f1117]" : "bg-[#f2f4f8]";
  const input = d ? "bg-[#1a1d27] border-white/8 text-white" : "bg-white border-gray-200 text-gray-900";
  const label = d ? "text-gray-500" : "text-gray-400";
  const titleC = d ? "text-white" : "text-gray-900";
  const subC = d ? "text-gray-400" : "text-gray-500";
  const zone = d ? "border-blue-500/40 bg-blue-500/5" : "border-blue-400/60 bg-blue-50";
  const zoneFile = d ? "text-white" : "text-gray-800";
  const zoneSub = d ? "text-gray-400" : "text-gray-500";
  const barC = d ? "bg-white/20" : "bg-black/20";
  const statusC = d ? "text-white/50" : "text-black/40";

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 80 }} animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 80 }} transition={{ duration: 0.9, ease: "easeOut", delay: 0.2 }} className="w-full max-w-[320px] mx-auto select-none">
      <div className="relative rounded-[3rem] bg-[#111] shadow-[0_40px_80px_-15px_rgba(0,0,0,0.9)] border border-white/10 overflow-hidden" style={{ padding: "10px" }}>
        <div className="absolute top-3 left-1/2 -translate-x-1/2 w-24 h-6 bg-black rounded-full z-20" />
        <div className={`relative rounded-[2.4rem] overflow-hidden transition-colors duration-700 ${screen}`} style={{ minHeight: "620px" }}>
          <div className={`flex items-center justify-between px-6 pt-10 pb-2 text-[10px] font-semibold transition-colors duration-700 ${statusC}`}>
            <span>9:41</span>
            <div className="flex items-center gap-1"><span>●●● WiFi </span></div>
          </div>
          <div className="px-5 pb-6">
            <div className="text-center mb-5 mt-2">
              <p className={`text-base font-bold leading-tight transition-colors duration-700 ${titleC}`}>{locale === "en" ? "New Financial Analysis" : "Nova Análise Financeira"}</p>
              <p className={`text-xs mt-1 leading-snug transition-colors duration-700 ${subC}`}>{locale === "en" ? "Upload the quarterly report (PDF) for AI processing." : "Carregue o relatório trimestral (PDF) para processamento via IA."}</p>
            </div>
            <div className="space-y-3">
              {[{ label: locale === "en" ? "COMPANY" : "EMPRESA", value: "AMAZON" }, { label: locale === "en" ? "YEAR" : "ANO", value: "2025" }, { label: locale === "en" ? "QUARTER" : "TRIMESTRE", value: locale === "en" ? "1st Quarter" : "1º Trimestre" }].map(f => (
                <div key={f.label}>
                  <p className={`text-[9px] font-semibold uppercase tracking-widest mb-1 transition-colors duration-700 ${label}`}>{f.label}</p>
                  <div className={`rounded-xl border px-3 py-2.5 text-xs font-medium transition-colors duration-700 ${input}`}>{f.value}</div>
                </div>
              ))}
              <div className={`rounded-xl border-2 border-dashed px-4 py-4 text-center mt-1 transition-colors duration-700 ${zone}`}>
                <UploadCloud size={22} className="mx-auto mb-2 text-blue-500" />
                <p className={`text-[10px] font-bold transition-colors duration-700 ${zoneFile}`}>AMZN-Q1-2025-Earnings-Release.pdf</p>
                <p className={`text-[9px] mt-0.5 transition-colors duration-700 ${zoneSub}`}>{locale === "en" ? "Supports PDF up to 10MB" : "Suporta PDF de até 10MB"}</p>
              </div>
              <button className="w-full rounded-xl py-3 text-xs font-bold flex items-center justify-center gap-2 mt-1 bg-blue-600 text-white">
                <span>✦</span> {locale === "en" ? "Generate Analysis" : "Gerar Análise Completa"}
              </button>
            </div>
          </div>
        </div>
        <div className="flex justify-center pt-2 pb-1">
          <div className={`w-24 h-1 rounded-full transition-colors duration-700 ${barC}`} />
        </div>
      </div>
    </motion.div>
  );
}

function ScoreDemo() {
  const locale = useLocale();
  const [barsVisible, setBarsVisible] = React.useState(false);
  useEffect(() => { const t = setTimeout(() => setBarsVisible(true), 500); return () => clearTimeout(t); }, []);

  return (
    <div className="relative w-full select-none">
      <div className="absolute -inset-6 bg-blue-600/10 blur-[60px] rounded-3xl pointer-events-none" />
      <div className="relative rounded-2xl overflow-hidden shadow-[0_40px_100px_-20px_rgba(0,0,0,0.9)] border border-white/10">
        <div className="bg-[#0e1117] border-b border-white/10 px-4 py-3 flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/80" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
          </div>
          <div className="flex-1 bg-white/5 rounded-md px-3 py-1 text-xs text-gray-500 font-mono">
            app.finanalyzer.ai/relatorio/microsoft
          </div>
        </div>

        <div className="bg-white overflow-y-auto scrollbar-thin" style={{ height: "560px" }}>
          <div className="px-6 md:px-8 py-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <Menu size={18} className="text-gray-600" />
                <span className="flex items-center gap-1 text-sm text-gray-600"><ChevronLeft size={16} /> {locale === "en" ? "Back to History" : "Voltar para Histórico"}</span>
              </div>
              <button className="flex items-center gap-2 bg-emerald-500 text-black text-xs font-bold px-3 py-1.5 rounded-lg">
                <Download size={13} /> {locale === "en" ? "Download Full Report" : "Baixar Relatório Completo"}
              </button>
            </div>

            <div className="flex items-start justify-between mb-8">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">{locale === "en" ? "Analysis Report" : "Relatório de Análise"}</p>
                <h1 className="text-4xl font-black text-gray-900 tracking-tight">MICROSOFT</h1>
                <p className="text-blue-400 font-bold text-lg mt-1">4T/2025</p>
              </div>
              <div className="bg-gray-50 border border-gray-200 rounded-xl px-5 py-4 text-right shadow-sm">
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-semibold">{locale === "en" ? "AI Score" : "Score IA"}</p>
                <p className="text-xs text-gray-500 mb-2">{locale === "en" ? "Based on 4 fundamentals" : "Baseado em 4 fundamentos"}</p>
                <div className="flex items-end justify-end gap-1">
                  <span className="text-4xl font-black text-emerald-400">5</span>
                  <span className="text-gray-400 text-lg mb-1">/5</span>
                </div>
              </div>
            </div>
            <div className="border-t border-gray-200 mb-8" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
              {scoreMetrics.map((m) => {
                const Icon = m.icon;
                return (
                  <div key={m.label} className="bg-gray-50 border border-gray-200 rounded-xl p-4 shadow-sm">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm text-gray-600 font-medium">
                        {locale === "en"
                          ? m.label === "Receita" ? "Revenue" : m.label === "Margem" ? "Margin" : m.label === "Dívida" ? "Debt" : m.label
                          : m.label}
                      </span>
                      <Icon size={16} className={m.color} />
                    </div>
                    <div className="flex items-end gap-1">
                      <span className="text-3xl font-black text-gray-900">{m.score}</span>
                      <span className="text-gray-500 text-sm mb-1">/5</span>
                    </div>
                    <ScoreMetricBar score={m.score} animate={barsVisible} />
                  </div>
                );
              })}
            </div>
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 mb-6 shadow-sm">
              <div className="flex items-center gap-3 mb-4">
                <FileText size={18} className="text-blue-500" />
                <h2 className="text-lg font-bold text-gray-900">{locale === "en" ? "Investment Thesis" : "Tese de Investimento"}</h2>
              </div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-4 font-semibold">{locale === "en" ? "Conclusion — Thesis and Outlook" : "Conclusão — Tese e Outlook"}</p>
              <div className="space-y-3">
                {(locale === "en" ? [
                  "Microsoft delivered an exceptional result in the fourth fiscal quarter of 2025, validating and reinforcing the investment thesis for the company as an undisputed leader in the era of cloud and artificial intelligence.",
                  "The numbers exceeded expectations across all major lines, demonstrating Microsoft's ability to translate market demand into profitable and efficient growth.",
                  "The main drivers were the robust, high-quality revenue growth, led by the stellar performance of the Intelligent Cloud segment (especially Azure) and the resilience of Productivity and Business Processes.",
                  "The company demonstrated remarkable operating leverage, with operating income growing above revenue and significant margin expansion.",
                  "Additionally, Microsoft reinforced its already enviable capital structure, with strong free cash flow generation and reduction in gross debt.",
                  "The company's outlook is extremely positive, with its leadership in AI and cloud securing a path of sustainable, high-value growth."
                ] : teseLines).map((line, i) => <p key={i} className="text-sm text-gray-700 leading-relaxed">{line}</p>)}
              </div>
            </div>
            <div className="h-16" />
          </div>
        </div>
      </div>
    </div>
  );
}

function ScoreDemoMobile() {
  const locale = useLocale();
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: false, margin: "-80px" });
  const [barsVisible, setBarsVisible] = useState(false);
  useEffect(() => { if (isInView) { const t = setTimeout(() => setBarsVisible(true), 400); return () => clearTimeout(t); } }, [isInView]);

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 40 }} animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }} transition={{ duration: 0.7, ease: "easeOut" }} className="relative w-full select-none">
      <div className="relative mx-auto rounded-[2.8rem] bg-[#0d0f14] border border-white/10 shadow-[0_30px_80px_-10px_rgba(0,0,0,0.95)] overflow-hidden" style={{ maxWidth: "320px" }}>
        <div className="flex items-center justify-between px-6 pt-8 pb-3 text-[10px] font-semibold text-white/40">
          <span>8:19</span>
          <span>●●● WiFi 🔋</span>
        </div>
        <div className="flex items-center justify-between px-4 pb-3 border-b border-white/8">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#1a1d27] rounded-xl flex items-center justify-center"><Menu size={14} className="text-gray-300" /></div>
            <span className="text-sm font-bold text-white">FinAnalyzer <span className="text-blue-400">.AI</span></span>
          </div>
          <div className="w-8 h-8 rounded-full bg-orange-500 flex items-center justify-center text-white text-xs font-bold">A</div>
        </div>
        <div className="overflow-y-auto" style={{ height: "520px", backgroundColor: "#ffffff" }}>
          <div className="px-4 py-4">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center"><ChevronLeft size={14} className="text-gray-600" /></div>
              <span className="text-sm text-gray-600 font-medium">{locale === "en" ? "Back to History" : "Voltar para Histórico"}</span>
            </div>
            <button className="w-full bg-emerald-500 text-black text-sm font-bold py-3 rounded-xl flex items-center justify-center gap-2 mb-5">
              <Download size={15} /> {locale === "en" ? "Download Full Report" : "Baixar Relatório Completo"}
            </button>
            <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-1">{locale === "en" ? "Analysis Report" : "Relatório de Análise"}</p>
            <h1 className="text-3xl font-black text-gray-900 tracking-tight">MICROSOFT</h1>
            <p className="text-blue-400 font-bold text-lg mt-1 mb-4">2T/2026</p>
            <div className="bg-gray-50 border border-gray-200 shadow-sm rounded-2xl px-5 py-4 flex items-center justify-between mb-5">
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold">{locale === "en" ? "AI Score" : "Score IA"}</p>
                <p className="text-xs text-gray-500 mt-0.5">{locale === "en" ? "Based on 4 fundamentals" : "Baseado em 4 fundamentos"}</p>
              </div>
              <div className="flex items-end gap-0.5">
                <span className="text-4xl font-black text-emerald-400">5</span>
                <span className="text-gray-400 text-base mb-1">/5</span>
              </div>
            </div>
            <div className="border-t border-gray-200 mb-5" />
            <div className="space-y-3 mb-5">
              {scoreMetrics.map((m) => {
                const Icon = m.icon;
                return (
                  <div key={m.label} className="bg-gray-50 border border-gray-200 shadow-sm rounded-2xl px-5 py-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm text-gray-600 font-medium">
                        {locale === "en"
                          ? m.label === "Receita" ? "Revenue" : m.label === "Margem" ? "Margin" : m.label === "Dívida" ? "Debt" : m.label
                          : m.label}
                      </span>
                      <div className="w-8 h-8 rounded-xl bg-white border border-gray-200 shadow-sm flex items-center justify-center"><Icon size={15} className={m.color} /></div>
                    </div>
                    <div className="flex items-end gap-1 mb-2">
                      <span className="text-3xl font-black text-gray-900">{m.score}</span>
                      <span className="text-gray-500 text-sm mb-1">/5</span>
                    </div>
                    <ScoreMetricBar score={m.score} animate={barsVisible} />
                  </div>
                );
              })}
            </div>
            <div className="bg-gray-50 border border-gray-200 shadow-sm rounded-2xl p-5 mb-4">
              <div className="flex items-center gap-2 mb-3">
                <FileText size={16} className="text-blue-500" />
                <h2 className="text-base font-bold text-gray-900">{locale === "en" ? "Investment Thesis" : "Tese de Investimento"}</h2>
              </div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-3 font-semibold">{locale === "en" ? "Conclusion — Thesis and Outlook" : "Conclusão — Tese e Outlook"}</p>
              <div className="space-y-3">
                {(locale === "en" ? [
                  "Microsoft delivered an exceptional result in the fourth fiscal quarter of 2025, validating and reinforcing the investment thesis for the company as an undisputed leader in the era of cloud and artificial intelligence.",
                  "The numbers exceeded expectations across all major lines, demonstrating Microsoft's ability to translate market demand into profitable and efficient growth.",
                  "The main drivers were the robust, high-quality revenue growth, led by the stellar performance of the Intelligent Cloud segment (especially Azure) and the resilience of Productivity and Business Processes.",
                  "The company demonstrated remarkable operating leverage, with operating income growing above revenue and significant margin expansion.",
                  "Additionally, Microsoft reinforced its already enviable capital structure, with strong free cash flow generation and reduction in gross debt.",
                  "The company's outlook is extremely positive, with its leadership in AI and cloud securing a path of sustainable, high-value growth."
                ] : teseLines).map((line, i) => <p key={i} className="text-sm text-gray-700 leading-relaxed">{line}</p>)}
              </div>
            </div>
            <div className="h-8" />
          </div>
        </div>
        <div className="flex justify-center py-2 bg-white"><div className="w-20 h-1 rounded-full bg-gray-300" /></div>
      </div>
    </motion.div>
  );
}

function ComparadorMobile() {
  const locale = useLocale();
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-60px" });

  const comparadorData = [
    { empresa: "AEROVIRONMENT", notaFinal: 2, receita: 4, lucro: 1, divida: 3, rentabilidade: 1, resultados: 2, media: 2.5, ultimoTri: "2T/2026" },
    { empresa: "AMAZON", notaFinal: 4, receita: 5, lucro: 3, divida: 4, rentabilidade: 4, resultados: 1, media: 4, ultimoTri: "4T/2025" },
    { empresa: "AMD", notaFinal: 4, receita: 5, lucro: 4, divida: 5, rentabilidade: 4, resultados: 1, media: 4, ultimoTri: "4T/2025" },
    { empresa: "ARISTA", notaFinal: 5, receita: 5, lucro: 5, divida: 5, rentabilidade: 4, resultados: 1, media: 5, ultimoTri: "4T/2025" },
    { empresa: "AURA", notaFinal: 2, receita: 3, lucro: 2, divida: 1, rentabilidade: 4, resultados: 1, media: 2, ultimoTri: "4T/2025" },
    { empresa: "AXON", notaFinal: 3, receita: 5, lucro: 2, divida: 4, rentabilidade: 4, resultados: 1, media: 3, ultimoTri: "4T/2025" },
    { empresa: "BADGER METERS", notaFinal: 5, receita: 5, lucro: 5, divida: 5, rentabilidade: 5, resultados: 4, media: 4.5, ultimoTri: "4T/2025" },
    { empresa: "BB SEGURIDADE", notaFinal: 3, receita: 3, lucro: 4, divida: 5, rentabilidade: 2, resultados: 1, media: 3, ultimoTri: "4T/2025" },
    { empresa: "BROADCOM", notaFinal: 5, receita: 5, lucro: 5, divida: 4, rentabilidade: 5, resultados: 1, media: 5, ultimoTri: "1T/2026" },
    { empresa: "BR PARTNERS", notaFinal: 3, receita: 3, lucro: 3, divida: 5, rentabilidade: 4, resultados: 1, media: 3, ultimoTri: "4T/2025" },
  ];

  const allCols = [
    { key: "notaFinal", label: "NOTA\nFINAL", colored: true, labelColor: "#a855f7" },
    { key: "receita", label: "RECEITA", colored: true, labelColor: "#3b82f6" },
    { key: "lucro", label: "LUCRO", colored: true, labelColor: "#22c55e" },
    { key: "divida", label: "DÍVIDA", colored: true, labelColor: "#ef4444" },
    { key: "rentabilidade", label: "RENTAB.", colored: true, labelColor: "#eab308" },
  ];

  function scoreColor(s: number) {
    if (s >= 4.5) return "#22c55e";
    if (s >= 4) return "#4ade80";
    if (s >= 3) return "#eab308";
    if (s >= 2) return "#f97316";
    return "#ef4444";
  }

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 40 }} animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }} transition={{ duration: 0.7, ease: "easeOut" }} className="w-full select-none">
      <div className="bg-white/95 backdrop-blur-xl border border-gray-200 rounded-2xl overflow-hidden shadow-2xl">
        <div className="px-5 py-4 border-b border-gray-200">
          <h3 className="text-lg font-bold text-gray-900">{locale === "en" ? "Aggregated Table" : "Tabela Agregada"}</h3>
          <p className="text-sm text-gray-500 mt-0.5">{locale === "en" ? "Consolidated view of performance." : "Visão consolidada do desempenho."}</p>
        </div>
        <div className="overflow-x-auto">
          <table style={{ minWidth: "500px" }} className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider sticky left-0 bg-white z-10">Empresa</th>
                {allCols.map(col => (
                  <th key={col.key} className="text-center px-4 py-3 text-xs font-semibold uppercase tracking-wider whitespace-pre-line leading-tight" style={{ color: col.labelColor }}>{col.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {comparadorData.map((row, i) => (
                <motion.tr key={row.empresa} className="border-b border-gray-100 hover:bg-gray-50 transition-colors" initial={{ opacity: 0, x: 16 }} animate={isInView ? { opacity: 1, x: 0 } : {}} transition={{ duration: 0.35, delay: 0.05 + i * 0.05 }}>
                  <td className="px-5 py-3 text-xs font-bold text-gray-900 sticky left-0 bg-white group-hover:bg-gray-50 z-10 leading-tight">{row.empresa}</td>
                  {allCols.map(col => {
                    const val = row[col.key as keyof typeof row];
                    const numVal = typeof val === "number" ? val : null;
                    return (
                      <td key={col.key} className="px-4 py-3 text-center">
                        <span className="text-sm font-black" style={{ color: col.colored && numVal !== null ? scoreColor(numVal) : "#e5e7eb" }}>{val}</span>
                      </td>
                    );
                  })}
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-5 py-3 border-t border-gray-200 flex items-center justify-end gap-1.5">
          <ChevronRight size={12} className="text-gray-500" />
          <span className="text-xs text-gray-500">{locale === "en" ? "Swipe to see more" : "Deslize para ver mais"}</span>
        </div>
      </div>
    </motion.div>
  );
}

function CallAnalysisDemo() {
  const locale = useLocale();
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, x: -40 }}
      animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -40 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
      className="w-full select-none relative"
    >
      <div className="absolute -inset-4 bg-indigo-500/10 blur-[40px] rounded-3xl pointer-events-none" />
      <div className="relative bg-white/95 backdrop-blur-xl border border-gray-200 rounded-2xl overflow-hidden shadow-2xl">
        <div className="px-5 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-indigo-50 flex items-center justify-center">
              <Mic size={18} className="text-indigo-600" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900">Earnings Call Q4'25</h3>
              <p className="text-xs text-gray-500">{locale === "en" ? "Transcript & Sentiment Analysis" : "Transcrição & Análise de Sentimento"}</p>
            </div>
          </div>
          <div className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 hidden sm:block">
            <span className="text-xs font-bold text-emerald-400">{locale === "en" ? "Tone: Optimistic" : "Tom: Otimista"}</span>
          </div>
        </div>

        <div className="p-5 space-y-4">
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gray-600 flex-shrink-0 flex items-center justify-center text-[10px] font-bold text-white">CEO</div>
            <div className="bg-white rounded-2xl rounded-tl-none p-4 border border-gray-200 text-sm text-gray-700 shadow-sm leading-relaxed">
              {locale === "en" ? '"We are seeing unprecedented demand for our new AI infrastructure, and this is clearly reflected in our margin expansion this quarter."' : '"Vemos uma demanda sem precedentes pela nossa nova infraestrutura de IA, e isso se reflete claramente na nossa expansão de margens neste trimestre."'}
            </div>
          </div>
          <div className="flex gap-3 flex-row-reverse">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex-shrink-0 flex items-center justify-center shadow-lg shadow-blue-500/20"><Activity size={14} className="text-white" /></div>
            <div className="bg-indigo-50 rounded-2xl rounded-tr-none p-4 border border-indigo-100 text-sm text-indigo-800 shadow-inner leading-relaxed">
              <span className="text-[10px] font-bold text-indigo-600 uppercase tracking-wider block mb-1.5">{locale === "en" ? "AI Insight" : "Insight da IA"}</span>
              {locale === "en" ? "The CEO highlights AI-driven margins, confirming the thesis of operational efficiency gains reported in the financial statements." : "O CEO destaca as margens impulsionadas por IA, confirmando a tese de ganho de eficiência operacional reportada no DFP."}
            </div>
          </div>
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gray-600 flex-shrink-0 flex items-center justify-center text-[10px] font-bold text-white">CFO</div>
            <div className="bg-white rounded-2xl rounded-tl-none p-4 border border-gray-200 text-sm text-gray-700 shadow-sm leading-relaxed">
              {locale === "en" ? '"Despite the macroeconomic challenges, we managed to maintain our growth guidance."' : '"Apesar dos desafios macroeconômicos, conseguimos manter nosso guidance de crescimento."'}
            </div>
          </div>
        </div>

        <div className="bg-gray-50 p-5 border-t border-gray-200">
          <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
            <span className="font-medium">{locale === "en" ? "Processing Completed" : "Processamento Concluído"}</span>
            <span className="flex items-center gap-1 font-bold text-emerald-600"><Check size={14} strokeWidth={3} /> {locale === "en" ? "100% Analyzed" : "100% Analisado"}</span>
          </div>
          <div className="h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-indigo-500 rounded-full w-full" />
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// --- EFEITO DE DIGITAÇÃO APRIMORADO ---
function TypewriterEffect({ text, trigger, delay = 0 }: { text: string, trigger: boolean, delay?: number }) {
  const [displayed, setDisplayed] = useState("");
  const [started, setStarted] = useState(false);

  useEffect(() => {
    if (trigger) {
      const t = setTimeout(() => setStarted(true), delay);
      return () => clearTimeout(t);
    }
  }, [trigger, delay]);

  useEffect(() => {
    if (!started) return;
    let i = 0;
    const interval = setInterval(() => {
      i += 1; // Imprime de 2 em 2 letras garantindo máxima suavidade sem travar
      if (i >= text.length) {
        setDisplayed(text);
        clearInterval(interval);
      } else {
        setDisplayed(text.slice(0, i));
      }
    }, 25); // Dispara muito rápido, parecendo 60fps
    return () => clearInterval(interval);
  }, [started, text]);

  return (
    <span>
      {displayed}
      {started && displayed.length < text.length && (
        <span className="inline-block w-1.5 h-3 ml-0.5 bg-blue-500/80 animate-pulse align-middle rounded-sm" />
      )}
    </span>
  );
}

function ReportDemo() {
  const locale = useLocale();
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const [barsVisible, setBarsVisible] = useState(false);
  const [typingTrigger, setTypingTrigger] = useState(false);

  useEffect(() => {
    if (isInView) {
      const t1 = setTimeout(() => setBarsVisible(true), 400);
      const t2 = setTimeout(() => setTypingTrigger(true), 800);
      return () => { clearTimeout(t1); clearTimeout(t2); };
    }
  }, [isInView]);

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 40 }} animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }} transition={{ duration: 0.7, ease: "easeOut" }} className="w-full select-none mt-10">
      <div className="relative mx-auto rounded-[2.8rem] bg-[#0d0f14] border border-white/10 shadow-[0_30px_80px_-10px_rgba(0,0,0,0.95)] overflow-hidden">
        
        {/* Fake Window Header */}
        <div className="bg-[#0e1117] border-b border-white/10 px-4 py-3 flex items-center justify-between">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/80" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
          </div>
          <div className="flex-1 max-w-sm bg-white/5 rounded-md px-3 py-1 text-[11px] text-gray-500 font-mono text-center mx-4">
            app.finanalyzer.ai/export/microsoft
          </div>
          <div className="w-10"></div>
        </div>

        {/* MOCKUP DO RELATÓRIO PDF/HTML REFEITO 1:1 */}
        <div className="bg-white overflow-y-auto scrollbar-thin font-sans" style={{ height: "650px", scrollbarWidth: "thin", scrollbarColor: "rgba(0,0,0,0.1) transparent" }}>
          
          {/* TOPO: Header FinAnalyzer e Botão */}
          <div className="border-b border-gray-200">
            <div className="max-w-[1000px] mx-auto px-10 py-5 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <div className="bg-blue-800 p-1.5 rounded"><Activity size={18} className="text-white" strokeWidth={2.5} /></div>
                <span className="font-bold text-lg text-gray-900 tracking-tight">FinAnalyzer</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs text-gray-400">{locale === "en" ? "Analysis" : "Análise"}</span>
                <span className="text-xs text-gray-400">{locale === "en" ? "Summary" : "Resumo"}</span>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-gray-400">{locale === "en" ? "AI Score" : "Score IA"}</span>
                  <span className="font-bold text-emerald-500">5.0/5</span>
                  <div className="ml-4"><LanguageSwitcher /></div>
                  <button className="bg-blue-800 text-white px-4 py-1.5 rounded flex items-center gap-2 font-bold ml-2">
                    <Download size={14} /> {locale === "en" ? "Save PDF" : "Salvar PDF"}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="max-w-[1000px] mx-auto px-10 pt-12 pb-20">
            
            {/* Título Principal e Score Geral */}
            <div className="flex justify-between items-start mb-8">
              <div>
                <div className="inline-block border border-blue-200 text-blue-600 bg-blue-50 px-3 py-1 rounded-full text-[9px] font-bold tracking-widest uppercase mb-4">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 inline-block mr-1.5 mb-0.5"></span>
                  4T/2025 - {locale === "en" ? "Quarterly Results" : "Resultados Trimestrais"}
                </div>
                <h1 className="text-6xl font-serif font-extrabold text-[#111827] tracking-tight mb-4">Microsoft</h1>
                <p className="text-gray-500 text-sm max-w-sm leading-relaxed">
                  {locale === "en" ? <>Full report generated by <strong className="text-gray-800">AI</strong> based on the official earnings release. Evaluation of revenue, margins, debt, and profitability with a strategic view.</> : <>Relatório completo gerado por <strong className="text-gray-800">IA</strong> com base no release de resultados oficial. Avaliação de receita, margens, endividamento e rentabilidade com visão estratégica.</>}
                </p>
              </div>
              
              <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-6 text-center w-[220px]">
                <p className="text-[9px] text-emerald-700 uppercase tracking-widest mb-4 font-bold">{locale === "en" ? "AI Score — Weighted Average" : "Score IA — Média Ponderada"}</p>
                <div className="w-24 h-24 mx-auto rounded-full border-[6px] border-emerald-500 flex items-center justify-center mb-3">
                  <p className="text-3xl font-black text-emerald-600">5.0<span className="text-sm text-emerald-400">/5</span></p>
                </div>
                <p className="text-sm font-bold text-emerald-700">{locale === "en" ? "Excellent" : "Excelente"}</p>
              </div>
            </div>

            {/* Grid 4 Pilares */}
            <div className="grid grid-cols-4 gap-4 mb-10">
              {reportMetrics.map((m, i) => (
                <div key={i} className="border border-gray-200 rounded-xl p-4 flex flex-col justify-between relative overflow-hidden bg-white shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
                  <div className="flex justify-between items-start mb-6">
                    <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">{m.id}</p>
                    <span className={`px-2 py-0.5 rounded text-[8px] font-bold border ${m.tagClass}`}>{locale === "en" && m.badge === "Excelente" ? "Excellent" : locale === "en" && m.badge === "Bom" ? "Good" : m.badge}</span>
                  </div>
                  <div>
                    <p className="text-3xl font-black text-gray-900 mb-1">{m.score}<span className="text-sm text-gray-400">/5</span></p>
                    <p className="text-[10px] text-gray-500 uppercase">
                      {locale === "en"
                        ? m.title === "Receita" ? "Revenue" : m.title === "Margem & Lucro" ? "Margin & Profit" : m.title === "Dívida & Risco" ? "Debt & Risk" : m.title === "Rentabilidade ROE" ? "Profitability ROE" : m.title
                        : m.title}
                    </p>
                  </div>
                  <div className="absolute bottom-0 left-0 w-full h-1 bg-gray-100">
                    <div className={`h-full transition-all duration-1000 ${m.barColor}`} style={{ width: barsVisible ? `${(parseFloat(m.score)/5)*100}%` : '0%' }}></div>
                  </div>
                </div>
              ))}
            </div>

          </div>

          {/* Banner Escuro */}
          <div className="bg-[#0f172a] text-white w-full py-6">
            <div className="max-w-[1000px] mx-auto px-10 flex justify-between items-center">
              {reportBannerStats.map((stat, i) => (
                <div key={i} className="text-left flex-1 border-r border-white/10 last:border-0 pl-6 first:pl-0">
                  <p className="text-xl font-black mb-1">{stat.value}</p>
                  <p className="text-[9px] text-gray-400 uppercase tracking-widest mb-1">{stat.label}</p>
                  {stat.var && (
                    <p className={`text-[10px] font-bold flex items-center gap-1 ${stat.isPos ? 'text-emerald-400' : 'text-red-400'}`}>
                      {stat.isPos ? '▲' : '▼'} {stat.var}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="max-w-[1000px] mx-auto px-10 pt-16 pb-20">
            {/* Título Seções */}
            <div className="mb-10">
              <p className="text-[10px] text-gray-400 uppercase tracking-widest mb-2 font-bold">{locale === "en" ? "Full AI Analysis" : "Análise Completa por IA"}</p>
              <h2 className="text-3xl font-serif font-extrabold text-[#111827]">{locale === "en" ? "Earnings Read" : "Leitura dos Resultados"}</h2>
            </div>

            {/* SEÇÃO 1: Visão Geral */}
            <div className="border border-gray-200 rounded-2xl p-8 mb-8 shadow-sm">
              <h3 className="text-xl font-serif font-bold text-gray-900 mb-6">{locale === "en" ? "Quarter Overview" : "Visão Geral do Trimestre"}</h3>
              <p className="text-sm text-gray-600 leading-relaxed font-medium mb-8">
                <TypewriterEffect text="A Microsoft encerrou o ano fiscal de 2025 com um desempenho notável no quarto trimestre, impulsionado por um crescimento robusto em suas ofertas de nuvem e inteligência artificial. A empresa superou as expectativas, registrando aumentos expressivos em receita, lucro operacional e lucro líquido, evidenciando a eficácia de sua estratégia focada em inovação e na transformação digital para clientes em diversos setores. Os resultados refletem a forte demanda por suas soluções de nuvem híbrida, serviços de IA e produtos comerciais, consolidando sua posição como líder tecnológico global." trigger={typingTrigger} delay={200} />
              </p>
              
              {/* Mock Gráfico de Barras Duplo */}
              <div className="border border-gray-100 rounded-xl p-5 relative">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h4 className="text-xs font-bold text-gray-900">{locale === "en" ? "Revenue & Income — Overview" : "Receita & Lucro — Visão Geral"}</h4>
                    <p className="text-[10px] text-gray-400">{locale === "en" ? "Evolution in recent quarters" : "Evolução nos últimos trimestres"}</p>
                  </div>
                  <span className="bg-emerald-100 text-emerald-700 text-[9px] font-bold px-2 py-1 rounded">↗ 18.1%</span>
                </div>
                <div className="h-48 flex items-end gap-16 justify-center pb-6 border-b border-gray-100 px-10 relative">
                  {/* Grid lines */}
                  <div className="absolute top-0 left-0 w-full h-full flex flex-col justify-between z-0">
                    <div className="border-b border-gray-100 w-full h-0"></div>
                    <div className="border-b border-gray-100 w-full h-0"></div>
                    <div className="border-b border-gray-100 w-full h-0"></div>
                    <div className="border-b border-gray-100 w-full h-0"></div>
                  </div>
                  
                  {/* 4T24 */}
                  <div className="flex items-end gap-2 relative z-10">
                    <div className="flex flex-col items-center">
                      <span className="text-[8px] text-gray-400 mb-1 font-bold">64.73 Bi</span>
                      <div className="w-8 bg-blue-100 border-2 border-blue-600 rounded-t-sm transition-all duration-1000" style={{ height: barsVisible ? '120px' : '0' }}></div>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-[8px] text-gray-400 mb-1 font-bold">22.04 Bi</span>
                      <div className="w-8 bg-emerald-500 rounded-t-sm transition-all duration-1000" style={{ height: barsVisible ? '40px' : '0' }}></div>
                    </div>
                    <span className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[9px] text-gray-400 font-bold">4T24</span>
                  </div>

                  {/* 4T25 */}
                  <div className="flex items-end gap-2 relative z-10">
                    <div className="flex flex-col items-center">
                      <span className="text-[8px] text-gray-800 mb-1 font-bold">76.44 Bi</span>
                      <div className="w-8 bg-blue-100 border-2 border-blue-600 rounded-t-sm transition-all duration-1000" style={{ height: barsVisible ? '150px' : '0' }}></div>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-[8px] text-gray-800 mb-1 font-bold">27.23 Bi</span>
                      <div className="w-8 bg-emerald-500 rounded-t-sm transition-all duration-1000" style={{ height: barsVisible ? '50px' : '0' }}></div>
                    </div>
                    <span className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[9px] text-gray-800 font-bold">4T25</span>
                  </div>
                </div>
              </div>
            </div>

            {/* SEÇÃO 2: Evolução Operacional */}
            <div className="border-t-4 border-emerald-500 pt-6 mt-12 mb-8 relative">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <p className="text-[9px] text-gray-400 uppercase tracking-widest font-bold mb-1">Seção 1</p>
                  <h3 className="text-xl font-serif font-bold text-gray-900">{locale === "en" ? "Operational Evolution and Top Line" : "Evolução Operacional e Top Line"}</h3>
                </div>
                <div className="bg-emerald-50 border border-emerald-100 rounded-lg py-2 px-4 flex flex-col items-center">
                   <p className="text-[8px] text-emerald-600 uppercase tracking-widest font-bold mb-1">{locale === "en" ? "Section Score" : "Nota da Seção"}</p>
                   <div className="flex items-center gap-2">
                     <span className="text-2xl font-black text-emerald-600">5<span className="text-sm text-emerald-400">/5</span></span>
                     <span className="bg-emerald-500 text-white text-[9px] font-bold px-2 py-0.5 rounded">{locale === "en" ? "Excellent" : "Excelente"}</span>
                   </div>
                </div>
              </div>
              <div className="space-y-4 mb-8">
                <p className="text-sm text-gray-600 leading-relaxed font-medium">
                  <TypewriterEffect text="A Microsoft demonstrou um crescimento impressionante na receita líquida, que atingiu US$ 76,44 bilhões no quarto trimestre fiscal de 2025, um aumento de 18% em relação ao mesmo período do ano anterior. Em moeda constante, o crescimento foi de 17%, indicando uma performance orgânica sólida. A narrativa de crescimento foi fortemente liderada pelas unidades de nuvem e inteligência artificial, que continuam a ser os pilares da estratégia da companhia. A desconstrução da receita por segmento revela os seguintes destaques:" trigger={typingTrigger} delay={2000} />
                </p>
              </div>

              {/* Tabela Mock */}
              <div className="border border-gray-200 rounded-lg overflow-hidden mb-6">
                <table className="w-full text-left">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-wider">Segmento</th>
                      <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-wider text-right">4T24 (Milhões $)</th>
                      <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-wider text-right">4T25 (Milhões $)</th>
                      <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-wider text-right">Variação (Y/Y)</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-gray-100">
                      <td className="px-4 py-3 text-xs font-bold text-gray-700">Productivity and Business Processes</td>
                      <td className="px-4 py-3 text-xs text-gray-500 text-right">28.627</td>
                      <td className="px-4 py-3 text-xs text-gray-900 font-bold text-right">33.112</td>
                      <td className="px-4 py-3 text-xs text-emerald-600 font-bold text-right">+16%</td>
                    </tr>
                    <tr className="border-b border-gray-100">
                      <td className="px-4 py-3 text-xs font-bold text-gray-700">Intelligent Cloud</td>
                      <td className="px-4 py-3 text-xs text-gray-500 text-right">23.785</td>
                      <td className="px-4 py-3 text-xs text-gray-900 font-bold text-right">29.878</td>
                      <td className="px-4 py-3 text-xs text-emerald-600 font-bold text-right">+26%</td>
                    </tr>
                    <tr className="border-b border-gray-100">
                      <td className="px-4 py-3 text-xs font-bold text-gray-700">More Personal Computing</td>
                      <td className="px-4 py-3 text-xs text-gray-500 text-right">12.315</td>
                      <td className="px-4 py-3 text-xs text-gray-900 font-bold text-right">13.451</td>
                      <td className="px-4 py-3 text-xs text-emerald-600 font-bold text-right">+8%</td>
                    </tr>
                    <tr className="bg-gray-50">
                      <td className="px-4 py-3 text-xs font-black text-gray-900">{locale === "en" ? "Total Revenue" : "Total Receita"}</td>
                      <td className="px-4 py-3 text-xs text-gray-500 font-bold text-right">64.727</td>
                      <td className="px-4 py-3 text-xs text-gray-900 font-black text-right">76.441</td>
                      <td className="px-4 py-3 text-xs text-emerald-600 font-black text-right">+18%</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Grid 2 Charts */}
              <div className="grid grid-cols-2 gap-4">
                {/* Evolução Receita */}
                <div className="border border-gray-100 rounded-xl p-5 relative">
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <h4 className="text-xs font-bold text-gray-900">Evolução da Receita</h4>
                      <p className="text-[10px] text-gray-400">Crescimento trimestral absoluto</p>
                    </div>
                    <span className="bg-emerald-100 text-emerald-700 text-[9px] font-bold px-2 py-1 rounded">↗ 18.1%</span>
                  </div>
                  <div className="h-40 flex items-end gap-16 justify-center pb-6 border-b border-gray-100 px-10 relative">
                    <div className="absolute top-0 left-0 w-full h-full flex flex-col justify-between z-0">
                      <div className="border-b border-gray-100 w-full h-0"></div>
                      <div className="border-b border-gray-100 w-full h-0"></div>
                      <div className="border-b border-gray-100 w-full h-0"></div>
                    </div>
                    <div className="flex flex-col items-center relative z-10">
                      <span className="text-[8px] text-gray-400 mb-1 font-bold">64.73 Bi</span>
                      <div className="w-8 bg-blue-100 border-2 border-blue-600 rounded-t-sm transition-all duration-1000" style={{ height: barsVisible ? '120px' : '0' }}></div>
                      <span className="absolute -bottom-5 text-[9px] text-gray-400 font-bold">4T24</span>
                    </div>
                    <div className="flex flex-col items-center relative z-10">
                      <span className="text-[8px] text-gray-800 mb-1 font-bold">76.44 Bi</span>
                      <div className="w-8 bg-blue-100 border-2 border-blue-600 rounded-t-sm transition-all duration-1000" style={{ height: barsVisible ? '150px' : '0' }}></div>
                      <span className="absolute -bottom-5 text-[9px] text-gray-800 font-bold">4T25</span>
                    </div>
                  </div>
                </div>

                {/* Donut Mock */}
                <div className="border border-gray-100 rounded-xl p-5 relative">
                  <div className="mb-6">
                    <h4 className="text-xs font-bold text-gray-900">Composição da Receita</h4>
                    <p className="text-[10px] text-gray-400">Share de Categorias (Último Trimestre)</p>
                  </div>
                  <div className="flex items-center justify-center h-40 gap-6">
                    <div className="w-28 h-28 rounded-full border-[20px] border-[#1e40af] border-t-[#059669] border-r-[#d97706] relative transform rotate-45 transition-all duration-1000" style={{ opacity: barsVisible ? 1 : 0, scale: barsVisible ? 1 : 0.8 }}>
                      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-14 h-14 bg-white rounded-full"></div>
                    </div>
                    <div className="flex flex-col gap-2">
                      <div className="flex items-center gap-2"><span className="w-2 h-2 bg-[#059669] rounded-sm"></span><span className="text-[8px] text-gray-600 font-bold">Intelligent Cloud (39%)</span></div>
                      <div className="flex items-center gap-2"><span className="w-2 h-2 bg-[#1e40af] rounded-sm"></span><span className="text-[8px] text-gray-600 font-bold">Productivity (43%)</span></div>
                      <div className="flex items-center gap-2"><span className="w-2 h-2 bg-[#d97706] rounded-sm"></span><span className="text-[8px] text-gray-600 font-bold">More Personal (18%)</span></div>
                    </div>
                  </div>
                </div>
              </div>

            </div>

            {/* SEÇÃO 3: Rentabilidade */}
            <div className="border-t-4 border-blue-500 pt-6 mt-12 mb-8 relative">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <p className="text-[9px] text-gray-400 uppercase tracking-widest font-bold mb-1">Seção 2</p>
                  <h3 className="text-xl font-serif font-bold text-gray-900">Rentabilidade e Margens</h3>
                </div>
                <div className="bg-blue-50 border border-blue-100 rounded-lg py-2 px-4 flex flex-col items-center">
                   <p className="text-[8px] text-blue-600 uppercase tracking-widest font-bold mb-1">{locale === "en" ? "Section Score" : "Nota da Seção"}</p>
                   <div className="flex items-center gap-2">
                     <span className="text-2xl font-black text-blue-600">4.5<span className="text-sm text-blue-400">/5</span></span>
                     <span className="bg-blue-500 text-white text-[9px] font-bold px-2 py-0.5 rounded">Ótimo</span>
                   </div>
                </div>
              </div>
              <div className="space-y-4 mb-8">
                <p className="text-sm text-gray-600 leading-relaxed font-medium">
                  <TypewriterEffect text="As margens operacionais mostraram forte resiliência, com a Margem Bruta atingindo expressivos 69,5%, impulsionada por economias de escala no segmento de Cloud. O Lucro Líquido saltou para US$ 25,6 bilhões, refletindo uma Margem Líquida robusta de 33,5%." trigger={typingTrigger} delay={2500} />
                </p>
              </div>

              {/* Grid de Cards de Margens */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="border border-gray-100 rounded-xl p-5 bg-white shadow-sm">
                  <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">Margem Bruta</p>
                  <div className="flex items-end gap-2 mb-2">
                    <p className="text-3xl font-black text-gray-900">69.5%</p>
                    <span className="text-[10px] text-emerald-500 font-bold mb-1">▲ 1.2 p.p.</span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 transition-all duration-1000" style={{ width: barsVisible ? '69.5%' : '0%' }}></div>
                  </div>
                </div>
                <div className="border border-gray-100 rounded-xl p-5 bg-white shadow-sm">
                  <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">Margem Operacional</p>
                  <div className="flex items-end gap-2 mb-2">
                    <p className="text-3xl font-black text-gray-900">43.8%</p>
                    <span className="text-[10px] text-emerald-500 font-bold mb-1">▲ 0.5 p.p.</span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-500 transition-all duration-1000" style={{ width: barsVisible ? '43.8%' : '0%' }}></div>
                  </div>
                </div>
                <div className="border border-gray-100 rounded-xl p-5 bg-white shadow-sm">
                  <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">Margem Líquida</p>
                  <div className="flex items-end gap-2 mb-2">
                    <p className="text-3xl font-black text-gray-900">33.5%</p>
                    <span className="text-[10px] text-emerald-500 font-bold mb-1">▲ 0.8 p.p.</span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-purple-500 transition-all duration-1000" style={{ width: barsVisible ? '33.5%' : '0%' }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* SEÇÃO 4: Saúde Financeira e Caixa */}
            <div className="border-t-4 border-purple-500 pt-6 mt-12 mb-8 relative">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <p className="text-[9px] text-gray-400 uppercase tracking-widest font-bold mb-1">Seção 3</p>
                  <h3 className="text-xl font-serif font-bold text-gray-900">Saúde Financeira e Endividamento</h3>
                </div>
                <div className="bg-purple-50 border border-purple-100 rounded-lg py-2 px-4 flex flex-col items-center">
                   <p className="text-[8px] text-purple-600 uppercase tracking-widest font-bold mb-1">{locale === "en" ? "Section Score" : "Nota da Seção"}</p>
                   <div className="flex items-center gap-2">
                     <span className="text-2xl font-black text-purple-600">5<span className="text-sm text-purple-400">/5</span></span>
                     <span className="bg-purple-500 text-white text-[9px] font-bold px-2 py-0.5 rounded">{locale === "en" ? "Excellent" : "Excelente"}</span>
                   </div>
                </div>
              </div>
              <div className="space-y-4 mb-6">
                <p className="text-sm text-gray-600 leading-relaxed font-medium">
                  <TypewriterEffect text="A Microsoft mantém uma posição de caixa formidável, com US$ 102,5 bilhões em caixa e equivalentes, superando de forma confortável sua dívida total de US$ 88 bilhões. O fluxo de caixa operacional permanece altamente gerador, garantindo capacidade de investimento robusta e distribuição consistente aos acionistas." trigger={typingTrigger} delay={3000} />
                </p>
              </div>

              <div className="bg-gray-50 border border-gray-200 rounded-xl p-6">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center border border-emerald-200">
                      <span className="text-lg">💵</span>
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Caixa Líquido</p>
                      <p className="text-2xl font-black text-emerald-700">US$ +14.5 Bi</p>
                    </div>
                  </div>
                  <div className="h-10 w-px bg-gray-200"></div>
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center border border-blue-200">
                      <span className="text-lg">📈</span>
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Alavancagem (Dívida/EBITDA)</p>
                      <p className="text-2xl font-black text-blue-700">0.7x</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* SEÇÃO 5: Conclusão e Tese */}
            <div className="bg-gradient-to-br from-indigo-50 to-blue-50 border border-indigo-100 rounded-2xl p-8 mt-16 mb-8 relative shadow-[0_10px_40px_-15px_rgba(59,130,246,0.15)]">
              <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
                <Activity size={120} />
              </div>
              <h3 className="text-xs font-bold text-indigo-800 uppercase tracking-widest mb-4">Conclusão da Inteligência Artificial</h3>
              <h4 className="text-2xl font-serif font-extrabold text-gray-900 mb-6">{locale === "en" ? "Investment Thesis" : "Tese de Investimento"} & Outlook</h4>
              <div className="space-y-4">
                <p className="text-sm text-gray-700 leading-relaxed font-medium">
                  <TypewriterEffect text="O trimestre consolida a tese de longo prazo da Microsoft como a principal beneficiária institucional da revolução da Inteligência Artificial. A capacidade da empresa de monetizar a IA de forma tangível em todo seu ecossistema corporativo está se traduzindo em uma aceleração sustentável de receita, descolando-se dos ciclos tradicionais de TI." trigger={typingTrigger} delay={4000} />
                </p>
                <p className="text-sm text-gray-700 leading-relaxed font-medium">
                  <TypewriterEffect text="Com fundamentos impecáveis, balanço extremamente saudável e vantagens competitivas em expansão, as perspectivas para os próximos doze meses permanecem francamente positivas. O desafio de valuation premium é justificado pela visibilidade e estabilidade do fluxo de caixa operacional projetado." trigger={typingTrigger} delay={4500} />
                </p>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-6 mt-16 text-center text-[10px] text-gray-400 font-bold uppercase tracking-widest">
              FIM DO RELATÓRIO
            </div>

          </div>
        </div>
      </div>
    </motion.div>
  );
}

function ReportDemoMobile() {
  const locale = useLocale();
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });
  const [barsVisible, setBarsVisible] = useState(false);
  const [typingTrigger, setTypingTrigger] = useState(false);

  useEffect(() => {
    if (isInView) {
      const t1 = setTimeout(() => setBarsVisible(true), 400);
      const t2 = setTimeout(() => setTypingTrigger(true), 800);
      return () => { clearTimeout(t1); clearTimeout(t2); };
    }
  }, [isInView]);

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 40 }} animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }} transition={{ duration: 0.7, ease: "easeOut" }} className="relative w-full select-none mt-8">
      <div className="relative mx-auto rounded-[2.8rem] bg-[#0d0f14] border border-white/10 shadow-[0_30px_80px_-10px_rgba(0,0,0,0.95)] overflow-hidden" style={{ maxWidth: "320px" }}>

        <div className="flex items-center justify-between px-6 pt-8 pb-2 text-[10px] font-semibold text-white/40 bg-[#0e1117]">
          <span>8:19</span>
          <span>●●● WiFi 🔋</span>
        </div>

        <div className="overflow-y-auto bg-white scrollbar-none" style={{ height: "520px", scrollbarWidth: "none" }}>
          <div className="p-5">

            <div className="flex justify-between items-center border-b border-gray-200 pb-4 mb-5">
              <div className="flex items-center gap-1.5">
                <div className="bg-blue-600 p-1.5 rounded-lg"><Activity size={14} className="text-white" strokeWidth={2.5} /></div>
                <span className="font-extrabold text-sm text-gray-900 tracking-tight">FinAnalyzer</span>
              </div>
              <div className="text-right text-[9px] text-gray-500 font-medium">Gerado em<br /> <strong className="text-gray-800">09/03/2026</strong></div>
            </div>

            {/* Título Principal e Score Geral */}
            <div className="mb-6">
              <div className="inline-block border border-blue-200 text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full text-[8px] font-bold tracking-widest uppercase mb-3">
                <span className="w-1 h-1 rounded-full bg-blue-500 inline-block mr-1 mb-0.5"></span>
                4T/2025 - {locale === "en" ? "Quarterly Results" : "Resultados Trimestrais"}
              </div>
              <h1 className="text-4xl font-serif font-extrabold text-[#111827] tracking-tight mb-2">Microsoft</h1>
              <p className="text-gray-500 text-[10px] leading-relaxed mb-6">
                Relatório gerado por <strong className="text-gray-800">IA</strong> com base no release de resultados.
              </p>
              
              <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4 text-center">
                <p className="text-[8px] text-emerald-700 uppercase tracking-widest mb-3 font-bold">{locale === "en" ? "AI Score" : "Score IA"} — Média</p>
                <div className="w-16 h-16 mx-auto rounded-full border-[4px] border-emerald-500 flex items-center justify-center mb-2">
                  <p className="text-xl font-black text-emerald-600">5.0<span className="text-[10px] text-emerald-400">/5</span></p>
                </div>
                <p className="text-[10px] font-bold text-emerald-700">{locale === "en" ? "Excellent" : "Excelente"}</p>
              </div>
            </div>

            {/* Grid 4 Pilares */}
            <div className="grid grid-cols-2 gap-2 mb-6">
              {reportMetrics.map((m, i) => (
                <div key={i} className="border border-gray-200 rounded-lg p-3 flex flex-col justify-between relative overflow-hidden bg-white shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
                  <div className="flex justify-between items-start mb-4">
                    <p className="text-[8px] font-bold text-gray-500 uppercase tracking-widest">{m.id}</p>
                    <span className={`px-1.5 py-0.5 rounded text-[7px] font-bold border ${m.tagClass}`}>{m.badge}</span>
                  </div>
                  <div>
                    <p className="text-xl font-black text-gray-900 mb-0.5">{m.score}<span className="text-[10px] text-gray-400">/5</span></p>
                    <p className="text-[8px] text-gray-500 uppercase">{m.title}</p>
                  </div>
                  <div className="absolute bottom-0 left-0 w-full h-1 bg-gray-100">
                    <div className={`h-full transition-all duration-1000 ${m.barColor}`} style={{ width: barsVisible ? `${(parseFloat(m.score)/5)*100}%` : '0%' }}></div>
                  </div>
                </div>
              ))}
            </div>

            {/* Banner Escuro */}
            <div className="bg-[#0f172a] text-white rounded-xl p-4 mb-8">
              <div className="grid grid-cols-2 gap-4">
                {reportBannerStats.slice(0,4).map((stat, i) => (
                  <div key={i} className="text-left">
                    <p className="text-[10px] text-gray-400 uppercase tracking-widest mb-0.5">{stat.label}</p>
                    <p className="text-lg font-black mb-0.5">{stat.value}</p>
                    {stat.var && (
                      <p className={`text-[8px] font-bold flex items-center gap-1 ${stat.isPos ? 'text-emerald-400' : 'text-red-400'}`}>
                        {stat.isPos ? '▲' : '▼'} {stat.var}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Título Seções */}
            <div className="mb-6">
              <p className="text-[8px] text-gray-400 uppercase tracking-widest mb-1 font-bold">Análise Completa</p>
              <h2 className="text-2xl font-serif font-extrabold text-[#111827]">{locale === "en" ? "Earnings Read" : "Leitura dos Resultados"}</h2>
            </div>

            {/* SEÇÃO 1: Visão Geral */}
            <div className="border border-gray-200 rounded-xl p-4 mb-6 shadow-sm">
              <h3 className="text-lg font-serif font-bold text-gray-900 mb-4">Visão Geral</h3>
              <p className="text-[10px] text-gray-600 leading-relaxed font-medium mb-6">
                <TypewriterEffect text="A Microsoft encerrou o ano fiscal de 2025 com um desempenho notável no quarto trimestre, impulsionado por um crescimento robusto em suas ofertas de nuvem e inteligência artificial." trigger={typingTrigger} delay={200} />
              </p>
              
              {/* Mock Gráfico de Barras Duplo */}
              <div className="border border-gray-100 rounded-lg p-3 relative">
                <div className="mb-4">
                  <h4 className="text-[10px] font-bold text-gray-900">Receita & Lucro</h4>
                </div>
                <div className="h-32 flex items-end gap-6 justify-center pb-4 border-b border-gray-100 relative">
                  <div className="absolute top-0 left-0 w-full h-full flex flex-col justify-between z-0">
                    <div className="border-b border-gray-100 w-full h-0"></div>
                    <div className="border-b border-gray-100 w-full h-0"></div>
                    <div className="border-b border-gray-100 w-full h-0"></div>
                  </div>
                  {/* 4T24 */}
                  <div className="flex items-end gap-1 relative z-10">
                    <div className="w-4 bg-blue-100 border border-blue-600 rounded-t-sm transition-all duration-1000" style={{ height: barsVisible ? '80px' : '0' }}></div>
                    <div className="w-4 bg-emerald-500 rounded-t-sm transition-all duration-1000" style={{ height: barsVisible ? '25px' : '0' }}></div>
                  </div>
                  {/* 4T25 */}
                  <div className="flex items-end gap-1 relative z-10">
                    <div className="w-4 bg-blue-100 border border-blue-600 rounded-t-sm transition-all duration-1000" style={{ height: barsVisible ? '100px' : '0' }}></div>
                    <div className="w-4 bg-emerald-500 rounded-t-sm transition-all duration-1000" style={{ height: barsVisible ? '30px' : '0' }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* SEÇÃO 2: Evolução Operacional */}
            <div className="border-t-2 border-emerald-500 pt-4 mt-8 mb-6 relative">
              <div className="flex flex-col items-start gap-2 mb-4">
                <h3 className="text-lg font-serif font-bold text-gray-900">Evolução Operacional</h3>
                <div className="bg-emerald-50 border border-emerald-100 rounded flex items-center gap-2 py-1 px-2">
                   <span className="text-[9px] text-emerald-600 font-bold uppercase">Nota:</span>
                   <span className="text-sm font-black text-emerald-600">5<span className="text-[10px] text-emerald-400">/5</span></span>
                </div>
              </div>
              <div className="space-y-3 mb-6">
                <p className="text-[10px] text-gray-600 leading-relaxed font-medium">
                  <TypewriterEffect text="Crescimento impressionante na receita líquida, atingindo US$ 76,44 bilhões no 4T25, um aumento de 18% YoY. A narrativa foi fortemente liderada pelas unidades de nuvem." trigger={typingTrigger} delay={2000} />
                </p>
              </div>

              {/* Tabela Mock Mobile */}
              <div className="border border-gray-200 rounded-lg overflow-hidden mb-4">
                <table className="w-full text-left">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-2 py-2 text-[8px] font-bold text-gray-500 uppercase">Seg.</th>
                      <th className="px-2 py-2 text-[8px] font-bold text-gray-500 uppercase text-right">4T25</th>
                      <th className="px-2 py-2 text-[8px] font-bold text-gray-500 uppercase text-right">Y/Y</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-gray-100">
                      <td className="px-2 py-2 text-[9px] font-bold text-gray-700 truncate max-w-[80px]">Cloud</td>
                      <td className="px-2 py-2 text-[9px] text-gray-900 font-bold text-right">29.878</td>
                      <td className="px-2 py-2 text-[9px] text-emerald-600 font-bold text-right">+26%</td>
                    </tr>
                    <tr className="bg-gray-50">
                      <td className="px-2 py-2 text-[9px] font-black text-gray-900 truncate max-w-[80px]">Total</td>
                      <td className="px-2 py-2 text-[9px] text-gray-900 font-black text-right">76.441</td>
                      <td className="px-2 py-2 text-[9px] text-emerald-600 font-black text-right">+18%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* SEÇÃO 3: Rentabilidade */}
            <div className="border-t-2 border-blue-500 pt-4 mt-6 mb-6 relative">
              <div className="flex flex-col items-start gap-2 mb-4">
                <h3 className="text-lg font-serif font-bold text-gray-900">Rentabilidade e Margens</h3>
                <div className="bg-blue-50 border border-blue-100 rounded flex items-center gap-2 py-1 px-2">
                   <span className="text-[9px] text-blue-600 font-bold uppercase">Nota:</span>
                   <span className="text-sm font-black text-blue-600">4.5<span className="text-[10px] text-blue-400">/5</span></span>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="border border-gray-100 rounded-lg p-3 bg-white shadow-sm">
                  <p className="text-[8px] font-bold text-gray-500 uppercase tracking-widest mb-1">Margem Bruta</p>
                  <p className="text-xl font-black text-gray-900 mb-1">69.5%</p>
                  <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 transition-all duration-1000" style={{ width: barsVisible ? '69.5%' : '0%' }}></div>
                  </div>
                </div>
                <div className="border border-gray-100 rounded-lg p-3 bg-white shadow-sm">
                  <p className="text-[8px] font-bold text-gray-500 uppercase tracking-widest mb-1">Margem Líquida</p>
                  <p className="text-xl font-black text-gray-900 mb-1">33.5%</p>
                  <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-purple-500 transition-all duration-1000" style={{ width: barsVisible ? '33.5%' : '0%' }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* SEÇÃO 4: Saúde Financeira */}
            <div className="border-t-2 border-purple-500 pt-4 mt-6 mb-6 relative">
              <div className="flex flex-col items-start gap-2 mb-4">
                <h3 className="text-lg font-serif font-bold text-gray-900">Saúde Financeira</h3>
                <div className="bg-purple-50 border border-purple-100 rounded flex items-center gap-2 py-1 px-2">
                   <span className="text-[9px] text-purple-600 font-bold uppercase">Nota:</span>
                   <span className="text-sm font-black text-purple-600">5<span className="text-[10px] text-purple-400">/5</span></span>
                </div>
              </div>
              
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="flex flex-col gap-3">
                  <div className="flex justify-between items-center border-b border-gray-200 pb-2">
                    <span className="text-[9px] text-gray-500 font-bold uppercase tracking-widest">Caixa Líquido</span>
                    <span className="text-sm font-black text-emerald-700">US$ +14.5 Bi</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[9px] text-gray-500 font-bold uppercase tracking-widest">Alavancagem</span>
                    <span className="text-sm font-black text-blue-700">0.7x</span>
                  </div>
                </div>
              </div>
            </div>

            {/* SEÇÃO 5: Conclusão e Tese */}
            <div className="bg-gradient-to-br from-indigo-50 to-blue-50 border border-indigo-100 rounded-xl p-5 mt-8 mb-6 relative">
              <h3 className="text-[9px] font-bold text-indigo-800 uppercase tracking-widest mb-2">Conclusão da IA</h3>
              <h4 className="text-lg font-serif font-extrabold text-gray-900 mb-3">Tese & Outlook</h4>
              <div className="space-y-3">
                <p className="text-[10px] text-gray-700 leading-relaxed font-medium">
                  <TypewriterEffect text="A Microsoft consolida sua tese de longo prazo como líder na revolução de IA. A capacidade de monetizar tecnologia em todo o ecossistema corporativo está se traduzindo em crescimento sustentável." trigger={typingTrigger} delay={4000} />
                </p>
                <p className="text-[10px] text-gray-700 leading-relaxed font-medium">
                  <TypewriterEffect text="Com fundamentos impecáveis e fluxo de caixa robusto, as perspectivas são positivas. O valuation premium é totalmente justificado pela visibilidade operacional." trigger={typingTrigger} delay={4500} />
                </p>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-4 mt-8 text-center text-[8px] text-gray-400 font-bold uppercase tracking-widest">
              FIM DO RELATÓRIO
            </div>

          </div>
        </div>

        <div className="flex justify-center py-2 bg-[#0e1117] border-t border-white/5">
          <div className="w-20 h-1 rounded-full bg-white/20" />
        </div>
      </div>
    </motion.div>
  );
}

// --- MAIN COMPONENT: LANDING PAGE ---

export default function LandingPage() {
  const locale = useLocale();
  return (
    <LandingPageContent locale={locale} />
  );
}
function LandingPageContent({ locale }: { locale: string }) {
  const [billingCycle, setBillingCycle] = useState('monthly');
  const historicoRef = useRef(null);
  const historicoInView = useInView(historicoRef, { once: true, margin: "-100px" });

  return (
    <div className="min-h-screen bg-[#0A0D14] text-gray-100 font-sans antialiased selection:bg-blue-500/30 overflow-x-hidden">

      {/* --- NAVBAR --- */}
      <nav className="border-b border-white/10 bg-[#0A0D14]/80 backdrop-blur-xl sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-5 h-16 md:h-20 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 md:w-10 md:h-10 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-900/20">
              <BarChart3 className="text-white w-5 h-5 md:w-6 md:h-6" />
            </div>
            <span className="text-xl md:text-2xl font-bold tracking-tight text-white">
              FinAnalyzer <span className="text-blue-500">.AI</span>
            </span>
          </div>

          <div className="hidden md:flex items-center gap-6">
            <a href="#funcionalidades" className="text-sm text-gray-300 hover:text-white font-medium transition-colors">{locale === "en" ? "Features" : "Funcionalidades"}</a>
            <a href="#planos" className="text-sm text-gray-300 hover:text-white font-medium transition-colors">{locale === "en" ? "Pricing" : "Preços"}</a>
            <a href="/dashboard" className="text-sm text-gray-300 hover:text-white font-medium transition-colors">{locale === "en" ? "Sign In" : "Entrar"}</a>
            <a href="/dashboard" className="bg-white hover:bg-gray-100 text-black px-6 py-2.5 rounded-full font-bold transition-all text-sm hover:scale-105">
              {locale === "en" ? "Get Started Free" : "Começar Grátis"}
            </a>
          </div>

          <div className="flex md:hidden items-center gap-2">
            <a href="/dashboard" className="border border-white/30 text-white px-3 py-2 rounded-full font-semibold text-sm hover:bg-white/10 transition-colors">
              {locale === "en" ? "Sign In" : "Entrar"}
            </a>
            <a href="/dashboard" className="bg-white text-black px-3 py-2 rounded-full font-bold text-sm">
              {locale === "en" ? "Sign Up" : "Cadastrar"}
            </a>
            <button className="w-8 h-8 flex flex-col items-center justify-center gap-1.5 ml-1">
              <span className="w-5 h-0.5 bg-white rounded-full" />
              <span className="w-5 h-0.5 bg-white rounded-full" />
            </button>
          </div>
        </div>
      </nav>

      {/* --- HERO SECTION --- */}
      <section
        className="relative min-h-[80vh] lg:min-h-[140vh] w-full flex flex-col items-center justify-start pt-16 lg:pt-32 bg-cover bg-bottom bg-no-repeat"
        style={{ backgroundImage: "url('/hero2.png')" }}
      >
        <div className="max-w-5xl mx-auto px-6 text-center relative z-10 flex flex-col items-center">
          <h1 className="text-[2.6rem] md:text-5xl lg:text-[6rem] font-serif font-bold text-white tracking-tighter mb-6 leading-none">
            {locale === "en" ? <>The New Era of <br /><span className="text-white tracking-tighter mb-8 leading-none">Asset Analysis.</span></> : <>A Nova Era Da <br /><span className="text-white tracking-tighter mb-8 leading-none">Análise de Ativos.</span></>}
          </h1>

          <p className="text-base md:text-2xl text-gray-300 mb-8 md:mb-12 max-w-2xl mx-auto leading-relaxed font-medium tracking-tight">
            {locale === "en" ? "Speed up your quarterly earnings analysis. Let AI structure the data and generate insights to support your investment decisions." : "Acelere a leitura de relatórios trimestrais. Deixe a IA estruturar os dados e gerar insights para apoiar sua decisão de investimento."}
          </p>

          <div className="flex flex-col md:flex-row items-center justify-center gap-6 w-full md:w-auto">
            <a href="/dashboard" className="w-full md:w-auto bg-blue-500 text-white px-10 py-4 rounded-full font-bold text-lg hover:bg-blue-400 transition-transform hover:scale-105 flex items-center justify-center gap-2 shadow-[0_0_40px_-10px_rgba(59,130,246,0.7)]">
              {locale === "en" ? "Create Free Account" : "Criar Conta Grátis"} <ArrowRight size={20} />
            </a>
            <a href="#funcionalidades" className="w-full md:w-auto px-10 py-4 rounded-full font-bold text-lg text-white border border-white/30 hover:bg-white/10 transition-all backdrop-blur-md bg-black/20">
              {locale === "en" ? "See Features" : "Ver Funcionalidades"}
            </a>
          </div>
        </div>
      </section>

      {/* --- SECÇÃO: FUNCIONALIDADES --- */}
      <div id="funcionalidades" className="flex flex-col">

        {/* BLOCO 1: UPLOAD */}
        <section
          className="py-16 lg:py-56 relative bg-cover bg-center bg-no-repeat overflow-hidden"
          style={{ backgroundImage: "url('/upload.png')" }}
        >
          <div className="max-w-7xl mx-auto px-6 relative z-10">
            <div className="flex flex-col lg:grid lg:grid-cols-12 lg:gap-16 lg:items-center">
              <div className="lg:col-span-5 lg:col-start-1 text-center lg:text-left mb-12 lg:mb-0">
                <div className="w-14 h-14 bg-blue-500/20 rounded-2xl flex items-center justify-center mb-6 border border-blue-400/30 mx-auto lg:mx-0">
                  <UploadCloud className="text-blue-400 w-7 h-7" />
                </div>
                <h2 className="text-4xl md:text-5xl lg:text-[3rem] font-serif font-bold text-white mb-4 tracking-tighter leading-[1.05]">
                  {locale === "en" ? <>Smart <br />Upload</> : <>Upload <br />Inteligente</>}
                </h2>
                <p className="text-base text-gray-300 leading-relaxed mb-8 font-medium tracking-tight max-w-md mx-auto lg:mx-0">
                  {locale === "en" ? "Simplify your analysis routine. Just drag the Earnings Release PDF. Our AI will generate a complete report in seconds." : "Simplifique sua rotina de análise. Basta arrastar o PDF do Release de Resultados (ITR ou DFP). Nossa IA vai gerar uma análise completa do resultado em segundos."}
                </p>
              </div>

              <div className="lg:col-span-6 lg:col-start-7 relative flex justify-center lg:justify-end">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-blue-600/20 blur-[100px] rounded-full pointer-events-none" />
                <div className="w-full max-w-[260px] lg:max-w-none">
                  <PhoneImage />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* BLOCO 2: SCORE DE IA */}
        <section
          className="pt-20 lg:pt-28 pb-20 lg:pb-32 relative bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/secao2.png')" }}
        >
          <div className="max-w-6xl mx-auto px-6 relative z-10">
            <div className="flex flex-col items-center text-center mb-10">
              <div className="w-14 h-14 bg-green-500/20 rounded-2xl flex items-center justify-center mb-4 border border-green-400/30">
                <FileText className="text-green-400 w-7 h-7" />
              </div>
              <h2 className="text-4xl md:text-5xl lg:text-[3rem] font-serif font-bold text-white mb-4 tracking-tighter leading-[1.05]">
                {locale === "en" ? "AI Score" : "Score de IA"}
              </h2>
              <p className="text-base text-gray-300 leading-relaxed font-medium tracking-tight max-w-xl">
                {locale === "en" ? "FinAnalyzer generates a Score from 0 to 5 for each fundamental metric, making it easy to immediately identify a company's strengths and areas of concern." : "O FinAnalyzer gera um Score de 0 a 5 para cada métrica fundamentalista, facilitando a identificação imediata de pontos fortes e de atenção na empresa."}
              </p>
            </div>
            <div className="hidden md:block">
              <ScoreDemo />
            </div>
            <div className="md:hidden">
              <ScoreDemoMobile />
            </div>
          </div>
        </section>

        {/* BLOCO 3: COMPARADOR DE ATIVOS */}
        <section className="py-16 lg:py-56 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-black to-sky-400/40 lg:hidden z-0" />

          <div
            className="absolute inset-0 hidden lg:block z-0"
            style={{
              backgroundImage: "url('/secao3_.png')",
              backgroundSize: 'cover',
              backgroundPosition: 'center center',
              backgroundRepeat: 'no-repeat'
            }}
          />

          <div className="max-w-7xl mx-auto px-6 relative z-10">
            <div className="flex flex-col items-center gap-10 lg:hidden">
              <div className="text-center">
                <div className="w-14 h-14 bg-purple-500/20 rounded-2xl flex items-center justify-center mb-6 border border-purple-400/30 mx-auto">
                  <Layout className="text-purple-400 w-7 h-7" />
                </div>
                <h2 className="text-3xl font-serif font-bold text-white mb-4 tracking-tighter leading-[1.05]">
                  {locale === "en" ? <>Asset <br />Comparator</> : <>Comparador <br />de Ativos</>}
                </h2>
                <p className="text-base text-gray-300 leading-relaxed font-medium tracking-tight max-w-sm mx-auto">
                  {locale === "en" ? "Visualize and compare all the results you have analyzed. Sort by Revenue, Profitability, Debt, Net Income, and much more." : "Visualize e compare todos os Resultados que você analisou. Ordene por Nota de Receita, Rentabilidade, Dívida, Lucro e muito mais."}
                </p>
              </div>
              <ComparadorMobile />
            </div>

            <div className="hidden lg:grid lg:grid-cols-12 gap-0 items-start">
              <div className="lg:col-span-4 lg:col-start-9 text-left">
                <div className="w-14 h-14 bg-purple-500/20 rounded-2xl flex items-center justify-center mb-6 border border-purple-400/30">
                  <Layout className="text-purple-400 w-7 h-7" />
                </div>
                <h2 className="text-3xl md:text-4xl lg:text-[3rem] font-serif font-bold text-white mb-5 tracking-tighter leading-[1.05]">
                  {locale === "en" ? <>Asset <br />Comparator</> : <>Comparador <br />de Ativos</>}
                </h2>
                <p className="text-base text-gray-300 leading-relaxed mb-8 font-medium tracking-tight">
                  {locale === "en" ? "Visualize and compare all the results you have analyzed. Sort by Revenue, Profitability, Debt, Net Income, and much more." : "Visualize e compare todos os Resultados que você analisou. Ordene por Nota de Receita, Rentabilidade, Dívida, Lucro e muito mais."}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* BLOCO 4: ANÁLISE DE CALLS */}
        <section
          className="py-16 lg:py-32 relative bg-[#0a0d14] overflow-hidden"
        >
          <div className="absolute top-0 right-0 w-1/2 h-full bg-indigo-600/5 blur-[120px] rounded-full pointer-events-none" />
          <div className="absolute bottom-0 left-0 w-1/2 h-full bg-blue-600/5 blur-[120px] rounded-full pointer-events-none" />

          <div className="max-w-7xl mx-auto px-6 relative z-10">
            <div className="flex flex-col lg:grid lg:grid-cols-12 lg:gap-16 lg:items-center">
              <div className="lg:col-span-5 lg:col-start-8 text-center lg:text-left mb-12 lg:mb-0 order-1 lg:order-2">
                <div className="w-14 h-14 bg-indigo-500/20 rounded-2xl flex items-center justify-center mb-6 border border-indigo-400/30 mx-auto lg:mx-0">
                  <Mic className="text-indigo-400 w-7 h-7" />
                </div>
                <h2 className="text-4xl md:text-5xl lg:text-[3rem] font-serif font-bold text-white mb-4 tracking-tighter leading-[1.05]">
                  {locale === "en" ? <>Earnings <br />Call Analysis</> : <>Análise de <br />Earnings Calls</>}
                </h2>
                <p className="text-base text-gray-300 leading-relaxed mb-8 font-medium tracking-tight max-w-md mx-auto lg:mx-0">
                  {locale === "en" ? "Go beyond the numbers. AI listens, transcribes, and analyzes earnings calls to capture management tone, tough questions, and future outlook in real time." : "Vá além dos números. A IA escuta, transcreve e analisa as teleconferências de resultados para capturar o tom da diretoria, perguntas difíceis e perspectivas futuras em tempo real."}
                </p>
              </div>

              <div className="lg:col-span-6 lg:col-start-1 relative flex justify-center lg:justify-start order-2 lg:order-1">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-indigo-600/20 blur-[100px] rounded-full pointer-events-none" />
                <div className="w-full max-w-[440px] lg:max-w-none">
                  <CallAnalysisDemo />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* BLOCO 5: HISTÓRICO COMPLETO */}
        <section
          className="py-16 lg:py-48 relative bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/secao4.png')" }}
        >
          <div className="absolute inset-0 bg-[#0A0D14]/60 pointer-events-none" />

          <div className="max-w-7xl mx-auto px-6 relative z-10">
            <div className="flex flex-col gap-10 lg:grid lg:grid-cols-12 lg:gap-10 lg:items-center">
              <div className="lg:col-span-3 lg:col-start-1 order-1 text-center lg:text-left">
                <div className="w-14 h-14 bg-yellow-500/20 rounded-2xl flex items-center justify-center mb-6 border border-yellow-400/30 mx-auto lg:mx-0">
                  <Database className="text-yellow-400 w-7 h-7" />
                </div>
                <h2 className="text-3xl lg:text-[2.6rem] font-serif font-bold text-white mb-4 tracking-tighter leading-[1.05]">
                  {locale === "en" ? <>Full <br />History</> : <>Histórico <br />Completo</>}
                </h2>
                <p className="text-sm text-gray-300 leading-relaxed font-medium tracking-tight">
                  {locale === "en" ? "All your analyses are saved forever. Compare a company's evolution quarter by quarter." : "Todas as suas análises ficam salvas para sempre. Compare a evolução da empresa trimestre a trimestre."}
                </p>
              </div>

              <motion.div
                ref={historicoRef}
                className="lg:col-span-8 lg:col-start-5 order-2"
                initial={{ opacity: 0, y: 60 }}
                animate={historicoInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.8, ease: "easeOut" }}
              >
                <div className="bg-white/95 backdrop-blur-xl border border-gray-200 rounded-2xl overflow-hidden shadow-2xl">
                  <div className="px-6 py-5 border-b border-gray-200">
                    <h3 className="text-xl font-bold text-gray-900">{locale === "en" ? "Detailed History" : "Histórico Detalhado"}</h3>
                    <p className="text-sm text-gray-500 mt-1">{locale === "en" ? "Manage your individual analyses." : "Gerencie suas análises individuais."}</p>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="text-left px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">{locale === "en" ? "Company" : "Empresa"}</th>
                          <th className="text-left px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">{locale === "en" ? "Period" : "Período"}</th>
                          <th className="text-left px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider hidden md:table-cell">{locale === "en" ? "Date" : "Data"}</th>
                          <th className="text-center px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Score</th>
                          <th className="text-right px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">{locale === "en" ? "Actions" : "Ações"}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {historicoData.map((item, i) => (
                          <motion.tr
                            key={item.empresa}
                            className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                            initial={{ opacity: 0, x: 20 }}
                            animate={historicoInView ? { opacity: 1, x: 0 } : {}}
                            transition={{ duration: 0.4, delay: 0.1 + i * 0.06 }}
                          >
                            <td className="px-6 py-4 text-sm font-bold text-gray-900">{item.empresa}</td>
                            <td className="px-6 py-4 text-sm text-gray-500">{item.periodo}</td>
                            <td className="px-6 py-4 text-sm text-gray-500 hidden md:table-cell">{item.data}</td>
                            <td className="px-6 py-4 text-center">
                              <ScoreBadge score={item.score} />
                            </td>
                            <td className="px-6 py-4 text-right">
                              <div className="flex items-center justify-end gap-3">
                                <Trash2 size={16} className="text-gray-500 cursor-pointer hover:text-red-400 transition-colors" />
                                <span className="text-blue-400 font-medium text-sm flex items-center gap-1 cursor-pointer hover:text-blue-300 transition-colors">
                                  {locale === "en" ? "Details" : "Detalhes"} <ChevronRight size={14} />
                                </span>
                              </div>
                            </td>
                          </motion.tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </section>

        {/* BLOCO 6: RELATÓRIO COMPLETO */}
        <section className="py-16 lg:py-48 relative overflow-hidden bg-[#05080f]">
          <div className="absolute inset-0 bg-gradient-to-b from-black to-sky-400/40 lg:hidden z-0" />

          <div className="max-w-6xl mx-auto px-6 relative z-10">
            <div className="flex flex-col items-center text-center mb-10">
              <div className="w-14 h-14 bg-blue-500/20 rounded-2xl flex items-center justify-center mb-4 border border-blue-400/30">
                <Download className="text-blue-400 w-7 h-7" />
              </div>
              <h2 className="text-4xl md:text-5xl lg:text-[3rem] font-serif font-bold text-white mb-4 tracking-tighter leading-[1.05]">
                {locale === "en" ? "Full Report" : "Relatório Completo"}
              </h2>
              <p className="text-base text-gray-300 leading-relaxed font-medium tracking-tight max-w-xl">
                {locale === "en" ? "Export your analyses in a clean, professional, and print-ready format. The report details all fundamentals and consolidates the investment thesis." : "Exporte suas análises em um formato limpo, profissional e pronto para impressão. O relatório detalha todos os fundamentos e consolida a tese de investimento."}
              </p>
            </div>

            <div className="hidden md:block">
              <ReportDemo />
            </div>
            <div className="md:hidden">
              <ReportDemoMobile />
            </div>
          </div>
        </section>

      </div>

      {/* --- SECÇÃO DE PLANOS --- */}
      <section
        id="planos"
        className="py-20 lg:py-48 relative bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('/fundo-planos.jpg')" }}
      >
        <div className="max-w-7xl mx-auto px-6 relative z-10">

          <div className="mb-12 md:mb-24 flex flex-col items-center text-center">
            <h2 className="text-3xl md:text-4xl lg:text-[5rem] font-serif font-bold text-white mb-6 tracking-tighter leading-[1.05]">
              {locale === "en" ? <>One single plan. <br className="hidden md:block" /> Invest better.</> : <>Um único plano. <br className="hidden md:block" /> Invista melhor.</>}
            </h2>

            <div className="flex items-center justify-center gap-4 bg-black/30 inline-flex p-2 rounded-full border border-white/20 mt-6 backdrop-blur-md">
              <button
                onClick={() => setBillingCycle('monthly')}
                className={`px-6 md:px-10 py-3 md:py-4 rounded-full text-base md:text-lg font-bold transition-all ${billingCycle === 'monthly' ? 'bg-white text-black shadow-lg' : 'text-gray-300 hover:text-white'}`}
              >
                {locale === "en" ? "Monthly" : "Mensal"}
              </button>
              <button
                onClick={() => setBillingCycle('yearly')}
                className={`px-6 md:px-10 py-3 md:py-4 rounded-full text-base md:text-lg font-bold transition-all flex items-center gap-3 ${billingCycle === 'yearly' ? 'bg-white text-black shadow-lg' : 'text-gray-300 hover:text-white'}`}
              >
                {locale === "en" ? "Yearly" : "Anual"}
              </button>
            </div>

            <div className={`transition-opacity duration-300 ${billingCycle === 'yearly' ? 'opacity-100' : 'opacity-0'} mt-8`}>
              <span className="bg-blue-500/90 text-white border border-blue-400 text-sm font-bold px-6 py-2.5 rounded-full uppercase tracking-wider shadow-xl">
                {locale === "en" ? "2 MONTHS FREE" : "2 MESES GRÁTIS"}
              </span>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-12 items-stretch max-w-5xl mx-auto">

            {/* CARD GRATUITO */}
            <div className="bg-[#11141D]/90 backdrop-blur-xl border border-white/10 rounded-[2.5rem] p-8 md:p-14 hover:border-white/30 transition-colors flex flex-col shadow-2xl">
              <h3 className="text-4xl font-bold text-white mb-2 tracking-tight">{locale === "en" ? "Free" : "Gratuito"}</h3>
              <p className="text-gray-400 text-xl mb-12 font-medium">{locale === "en" ? "To start analyzing at no cost." : "Para começar a analisar sem custo."}</p>

              <ul className="space-y-6 mb-16 flex-1">
                <Feature text={locale === "en" ? "5 Analyses per week" : "5 Análises por semana"} active />
                <Feature text={locale === "en" ? "Summary Report on Screen" : "Relatório Resumido na Tela"} active />
                <Feature text={locale === "en" ? "Simple history access" : "Acesso ao histórico simples"} active />
                <Feature text={locale === "en" ? "Email support" : "Suporte por email"} active />
                <Feature text={locale === "en" ? "Unlimited file upload" : "Upload de arquivos ilimitado"} disabled />
                <Feature text={locale === "en" ? "Download Full AI Report" : "Download da Análise Completa da IA"} disabled />
                <Feature text={locale === "en" ? "Comparative Asset Table" : "Tabela Comparativa de Ativos"} disabled />
                <Feature text={locale === "en" ? "Earnings Call Analysis" : "Análise de Earnings Calls"} disabled />
              </ul>

              <a href="/dashboard" className="block w-full text-center py-6 rounded-full border-2 border-white/30 text-white text-xl font-bold hover:bg-white/10 transition-all mt-auto backdrop-blur-md">
                {locale === "en" ? "Create Free Account" : "Criar conta grátis"}
              </a>
            </div>

            {/* CARD PREMIUM */}
            <div className="bg-blue-600/95 backdrop-blur-2xl border border-blue-400/50 rounded-[2.5rem] p-8 md:p-14 relative shadow-[0_0_80px_-10px_rgba(37,99,235,0.8)] flex flex-col transform hover:-translate-y-4 transition-transform duration-300">
              <h3 className="text-4xl font-bold text-white mb-2 tracking-tight">Premium</h3>
              <div className="flex items-end gap-2 mb-2">
                <span className="text-[3.5rem] md:text-[5.5rem] leading-none font-extrabold text-white tracking-tighter">{billingCycle === 'monthly' ? 'R$ 29' : 'R$ 290'}</span>
                <span className="text-blue-200 mb-4 font-medium text-2xl">{billingCycle === 'monthly' ? '/mês' : '/ano'}</span>
              </div>
              <p className="text-blue-100 text-xl mb-12 font-medium">{locale === "en" ? "Unlock the full power of AI." : "Desbloqueie todo o poder da IA."}</p>

              <ul className="space-y-6 mb-16 flex-1">
                <Feature text={locale === "en" ? "Unlimited AI Analyses" : "Análises de IA Ilimitadas"} active light />
                <Feature text={locale === "en" ? "Summary Report on Screen" : "Relatório Resumido na Tela"} active light />
                <Feature text={locale === "en" ? "Unlimited History Access" : "Acesso ao Histórico Ilimitado"} active light />
                <Feature text={locale === "en" ? "Email Support" : "Suporte por Email"} active light />
                <Feature text={locale === "en" ? "Unlimited file upload" : "Upload de arquivos ilimitado"} active light />
                <Feature text={locale === "en" ? "Download Full AI Report" : "Download da Análise Completa da IA"} active light />
                <Feature text={locale === "en" ? "Comparative Asset Table" : "Tabela Comparativa de Ativos"} active light />
                <Feature text={locale === "en" ? "Earnings Call Analysis" : "Análise de Earnings Calls"} active light />
                <Feature text={locale === "en" ? "Maximum queue priority" : "Prioridade máxima na fila"} active light />
              </ul>

              <a href="/dashboard" className="block w-full text-center py-6 rounded-full bg-white text-blue-700 text-xl font-extrabold shadow-2xl hover:bg-gray-100 hover:scale-[1.02] transition-all mt-auto">
                {locale === "en" ? "Subscribe Now" : "Assinar Agora"}
              </a>
              <p className="text-center text-sm text-blue-200 mt-8 font-medium">{locale === "en" ? "Cancel anytime." : "Cancele quando quiser."}</p>
            </div>
          </div>
        </div>
      </section>

      {/* --- FOOTER --- */}
      <footer className="border-t border-white/10 bg-[#0A0D14] pt-24 pb-12">
        <div className="max-w-7xl mx-auto px-6">

          <div className="flex flex-col md:flex-row justify-between items-center gap-6 mb-16">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center border border-white/20">
                <BarChart3 className="text-white w-6 h-6" />
              </div>
              <span className="text-2xl font-bold text-white tracking-tight">FinAnalyzer.AI</span>
            </div>

            <div className="flex gap-8">
              <a href="/terms" className="text-base text-gray-400 hover:text-white transition-colors font-medium">{locale === "en" ? "Terms of Use" : "Termos de Uso"}</a>
              <a href="/privacy" className="text-base text-gray-400 hover:text-white transition-colors font-medium">{locale === "en" ? "Privacy" : "Privacidade"}</a>
              <a href="/refund" className="text-base text-gray-400 hover:text-white transition-colors font-medium">{locale === "en" ? "Refund" : "Reembolso"}</a>
            </div>
          </div>

          <div className="border-t border-white/10 pt-12 text-sm text-gray-400 space-y-4 text-justify leading-relaxed font-light">
            <p>
              {locale === "en" ? (
                <><strong className="text-gray-300 font-semibold">IMPORTANT DISCLAIMER:</strong> The analysis presented on this platform is generated by Artificial Intelligence algorithms and serves only as an <strong className="text-gray-300 font-semibold">auxiliary support tool</strong>. It <strong className="text-gray-300 font-semibold">does not replace human analysis</strong>, nor does it constitute a recommendation to buy or sell assets. FinAnalyzer.AI is not responsible for the accuracy, completeness, or timeliness of the data, nor for any investment decisions or financial losses resulting from the use of this information. Past performance does not guarantee future results.</>
              ) : (
                <><strong className="text-gray-300 font-semibold">AVISO IMPORTANTE SOBRE IA:</strong> A análise apresentada nesta plataforma é gerada por algoritmos de Inteligência Artificial e serve apenas como uma <strong className="text-gray-300 font-semibold">ferramenta auxiliar de suporte</strong>. Ela <strong className="text-gray-300 font-semibold">não substitui a análise humana</strong>, nem constitui recomendação de compra ou venda de ativos. O FinAnalyzer.AI não se responsabiliza pela precisão, integridade ou atualização dos dados, nem por quaisquer decisões de investimento ou prejuízos financeiros decorrentes do uso destas informações. Rentabilidade passada não representa garantia de rentabilidade futura.</>
              )}
            </p>
            <p className="text-center pt-10 text-gray-500 font-medium">
              {locale === "en" ? "© 2026 FinAnalyzer Inc. All rights reserved." : "© 2026 FinAnalyzer Inc. Todos os direitos reservados."}
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}