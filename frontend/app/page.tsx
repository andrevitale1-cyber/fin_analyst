"use client";

import React, { useState, useRef, useEffect } from 'react';
import { motion, useInView } from "framer-motion";
import { 
  BarChart3, UploadCloud, ArrowRight, 
  FileText, Layout, Database, Check, X,
  Trash2, ChevronRight, DollarSign, Percent,
  AlertCircle, TrendingUp, Download, ChevronLeft, Menu
} from "lucide-react";

// --- DATA ---
const historicoData = [
  { empresa: "SAMSARA", periodo: "4T/2026", data: "05/03/2026", score: 5 },
  { empresa: "MARVELL", periodo: "4T/2026", data: "05/03/2026", score: 5 },
  { empresa: "VEEVA", periodo: "4T/2026", data: "04/03/2026", score: 5 },
  { empresa: "ENGIE", periodo: "4T/2025", data: "04/03/2026", score: 2 },
  { empresa: "BROADCOM", periodo: "1T/2026", data: "04/03/2026", score: 5 },
  { empresa: "RAIA DROGASIL", periodo: "4T/2025", data: "04/03/2026", score: 4 },
  { empresa: "ON RUNNING", periodo: "4T/2025", data: "03/03/2026", score: 4 },
  { empresa: "AURA", periodo: "4T/2025", data: "27/02/2026", score: 2 },
  { empresa: "CELSIUS", periodo: "4T/2025", data: "26/02/2026", score: 4 },
];

// --- SUBCOMPONENTS ---

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

// --- SCORE DEMO DATA ---
const scoreMetrics = [
  { label: "Receita",  icon: DollarSign,   color: "text-blue-400",    score: 5 },
  { label: "Margem",   icon: Percent,       color: "text-purple-400",  score: 5 },
  { label: "Dívida",   icon: AlertCircle,   color: "text-red-400",     score: 5 },
  { label: "ROE",      icon: TrendingUp,    color: "text-emerald-400", score: 5 },
];

const teseLines = [
  "A Microsoft entregou um resultado excepcional no quarto trimestre fiscal de 2025, validando e fortalecendo a tese de investimento na empresa como uma líder indiscutível na era da nuvem e da inteligência artificial.",
  "Os números superaram as expectativas em todas as linhas principais, demonstrando a capacidade da Microsoft de traduzir a demanda do mercado em crescimento lucrativo e eficiente.",
  "Os principais drivers foram o crescimento robusto e de alta qualidade da receita, impulsionado pelo desempenho estelar do segmento Intelligent Cloud (especialmente Azure) e pela resiliência de Productivity and Business Processes.",
  "A empresa demonstrou uma notável alavancagem operacional, com o lucro operacional crescendo acima da receita e uma expansão significativa das margens.",
  "Além disso, a Microsoft reforçou sua já invejável estrutura de capital, com forte geração de fluxo de caixa livre e redução da dívida bruta.",
  "O outlook da empresa é extremamente positivo, com sua liderança em IA e nuvem assegurando um caminho de crescimento sustentável e de alto valor.",
];

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

function ScoreDemo() {
  const containerRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);
  const [barsVisible, setBarsVisible] = React.useState(false);
  const animFrameRef = useRef<number>(0);
  const scrollPos = useRef(0);

  useEffect(() => {
    const t = setTimeout(() => setBarsVisible(true), 500);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    const inner = innerRef.current;
    if (!container || !inner) return;

    const SPEED = 0.45;
    const PAUSE_MS = 2200;
    let pausing = false;
    let pauseStart = 0;

    const tick = () => {
      if (!containerRef.current || !innerRef.current) return;
      const maxScroll = innerRef.current.scrollHeight - containerRef.current.clientHeight;

      if (pausing) {
        if (Date.now() - pauseStart >= PAUSE_MS) {
          pausing = false;
        }
        animFrameRef.current = requestAnimationFrame(tick);
        return;
      }

      if (scrollPos.current >= maxScroll - 1) {
        scrollPos.current = 0;
        containerRef.current.scrollTop = 0;
        pausing = true;
        pauseStart = Date.now();
        animFrameRef.current = requestAnimationFrame(tick);
        return;
      }

      scrollPos.current = Math.min(scrollPos.current + SPEED, maxScroll);
      containerRef.current.scrollTop = scrollPos.current;
      animFrameRef.current = requestAnimationFrame(tick);
    };

    animFrameRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, []);

  return (
    <div className="relative w-full select-none">
      <div className="absolute -inset-6 bg-blue-600/10 blur-[60px] rounded-3xl pointer-events-none" />
      <div className="relative rounded-2xl overflow-hidden shadow-[0_40px_100px_-20px_rgba(0,0,0,0.9)] border border-white/10">
        {/* Browser chrome */}
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

        {/* Scrollable page content */}
        <div ref={containerRef} className="bg-[#0A0D14] overflow-hidden" style={{ height: "480px" }}>
          <div ref={innerRef} className="px-8 py-6">
            {/* App navbar */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <Menu size={18} className="text-gray-400" />
                <span className="flex items-center gap-1 text-sm text-gray-400">
                  <ChevronLeft size={16} /> Voltar para Histórico
                </span>
              </div>
              <button className="flex items-center gap-2 bg-emerald-500 text-black text-xs font-bold px-3 py-1.5 rounded-lg">
                <Download size={13} /> Baixar Relatório
              </button>
            </div>

            {/* Header */}
            <div className="flex items-start justify-between mb-8">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">Relatório de Análise</p>
                <h1 className="text-4xl font-black text-white tracking-tight">MICROSOFT</h1>
                <p className="text-blue-400 font-bold text-lg mt-1">4T/2025</p>
              </div>
              <div className="bg-[#11141D] border border-white/10 rounded-xl px-5 py-4 text-right">
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Score IA</p>
                <p className="text-xs text-gray-500 mb-2">Baseado em 4 fundamentos</p>
                <div className="flex items-end justify-end gap-1">
                  <span className="text-4xl font-black text-emerald-400">5</span>
                  <span className="text-gray-400 text-lg mb-1">/5</span>
                </div>
              </div>
            </div>

            <div className="border-t border-white/5 mb-8" />

            {/* Metric cards */}
            <div className="grid grid-cols-4 gap-3 mb-8">
              {scoreMetrics.map((m) => {
                const Icon = m.icon;
                return (
                  <div key={m.label} className="bg-[#11141D] border border-white/8 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm text-gray-400">{m.label}</span>
                      <Icon size={16} className={m.color} />
                    </div>
                    <div className="flex items-end gap-1">
                      <span className="text-3xl font-black text-white">{m.score}</span>
                      <span className="text-gray-500 text-sm mb-1">/5</span>
                    </div>
                    <ScoreMetricBar score={m.score} animate={barsVisible} />
                  </div>
                );
              })}
            </div>

            {/* Tese de Investimento */}
            <div className="bg-[#11141D] border border-white/8 rounded-xl p-6 mb-6">
              <div className="flex items-center gap-3 mb-4">
                <FileText size={18} className="text-blue-400" />
                <h2 className="text-lg font-bold text-white">Tese de Investimento</h2>
              </div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-4">Conclusão — Tese e Outlook</p>
              <div className="space-y-3">
                {teseLines.map((line, i) => (
                  <p key={i} className="text-sm text-gray-300 leading-relaxed">{line}</p>
                ))}
              </div>
            </div>
            <div className="h-16" />
          </div>
        </div>

        {/* Bottom fade */}
        <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-[#0A0D14] to-transparent pointer-events-none rounded-b-2xl" />
      </div>
    </div>
  );
}

function PhoneImage() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: false, margin: "-100px" });
  const [isDark, setIsDark] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (isInView) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => {
        setIsDark(prev => !prev);
      }, 3000);
    } else {
      if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
      setIsDark(true);
    }
    return () => { if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; } };
  }, [isInView]);

  const d = isDark;
  const screen   = d ? "bg-[#0f1117]" : "bg-[#f2f4f8]";
  const input    = d ? "bg-[#1a1d27] border-white/8 text-white" : "bg-white border-gray-200 text-gray-900";
  const label    = d ? "text-gray-500" : "text-gray-400";
  const titleC   = d ? "text-white" : "text-gray-900";
  const subC     = d ? "text-gray-400" : "text-gray-500";
  const zone     = d ? "border-blue-500/40 bg-blue-500/5" : "border-blue-400/60 bg-blue-50";
  const zoneFile = d ? "text-white" : "text-gray-800";
  const zoneSub  = d ? "text-gray-400" : "text-gray-500";
  const barC     = d ? "bg-white/20" : "bg-black/20";
  const statusC  = d ? "text-white/50" : "text-black/40";

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 80 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 80 }}
      transition={{ duration: 0.9, ease: "easeOut", delay: 0.2 }}
      className="w-full max-w-[320px] mx-auto select-none"
    >
      {/* Phone frame */}
      <div className="relative rounded-[3rem] bg-[#111] shadow-[0_40px_80px_-15px_rgba(0,0,0,0.9)] border border-white/10 overflow-hidden" style={{ padding: "10px" }}>

        {/* Notch */}
        <div className="absolute top-3 left-1/2 -translate-x-1/2 w-24 h-6 bg-black rounded-full z-20" />

        {/* Screen */}
        <div className={`relative rounded-[2.4rem] overflow-hidden transition-colors duration-700 ${screen}`} style={{ minHeight: "620px" }}>

          {/* Status bar */}
          <div className={`flex items-center justify-between px-6 pt-10 pb-2 text-[10px] font-semibold transition-colors duration-700 ${statusC}`}>
            <span>9:41</span>
            <div className="flex items-center gap-1"><span>●●● WiFi 🔋</span></div>
          </div>

          {/* App content */}
          <div className="px-5 pb-6">
            {/* Header */}
            <div className="text-center mb-5 mt-2">
              <p className={`text-base font-bold leading-tight transition-colors duration-700 ${titleC}`}>Nova Análise Financeira</p>
              <p className={`text-xs mt-1 leading-snug transition-colors duration-700 ${subC}`}>
                Carregue o relatório trimestral (PDF) para processamento via IA.
              </p>
            </div>

            {/* Fields */}
            <div className="space-y-3">
              {[
                { label: "EMPRESA",   value: "AMAZON"        },
                { label: "ANO",       value: "2025"          },
                { label: "TRIMESTRE", value: "1º Trimestre"  },
              ].map(f => (
                <div key={f.label}>
                  <p className={`text-[9px] font-semibold uppercase tracking-widest mb-1 transition-colors duration-700 ${label}`}>{f.label}</p>
                  <div className={`rounded-xl border px-3 py-2.5 text-xs font-medium transition-colors duration-700 ${input}`}>{f.value}</div>
                </div>
              ))}

              {/* Upload zone */}
              <div className={`rounded-xl border-2 border-dashed px-4 py-4 text-center mt-1 transition-colors duration-700 ${zone}`}>
                <UploadCloud size={22} className="mx-auto mb-2 text-blue-500" />
                <p className={`text-[10px] font-bold transition-colors duration-700 ${zoneFile}`}>AMZN-Q1-2025-Earnings-Release.pdf</p>
                <p className={`text-[9px] mt-0.5 transition-colors duration-700 ${zoneSub}`}>Suporta PDF de até 10MB</p>
              </div>

              {/* CTA */}
              <button className="w-full rounded-xl py-3 text-xs font-bold flex items-center justify-center gap-2 mt-1 bg-blue-600 text-white">
                <span>✦</span> Gerar Análise Completa
              </button>
            </div>
          </div>
        </div>

        {/* Home bar */}
        <div className="flex justify-center pt-2 pb-1">
          <div className={`w-24 h-1 rounded-full transition-colors duration-700 ${barC}`} />
        </div>
      </div>
    </motion.div>
  );
}

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

function ListItem({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-center gap-4 text-white font-medium text-lg tracking-tight">
      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 border border-blue-500">
         <Check size={16} className="text-white" strokeWidth={3} />
      </div>
      <span>{children}</span>
    </li>
  );
}

// --- MAIN COMPONENT ---

export default function LandingPage() {
  const [billingCycle, setBillingCycle] = useState('monthly');

  const historicoRef = useRef(null);
  const historicoInView = useInView(historicoRef, { once: true, margin: "-100px" });

  return (
    <div className="min-h-screen bg-[#0A0D14] text-gray-100 font-sans antialiased selection:bg-blue-500/30 overflow-x-hidden">

      {/* --- NAVBAR --- */}
      <nav className="border-b border-white/10 bg-[#0A0D14]/80 backdrop-blur-xl sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-900/20">
              <BarChart3 className="text-white w-6 h-6" />
            </div>
            <span className="text-2xl font-bold tracking-tight text-white">
              FinAnalyzer <span className="text-blue-500">.AI</span>
            </span>
          </div>

          <div className="flex items-center gap-6">
            <a href="#funcionalidades" className="hidden md:block text-sm text-gray-300 hover:text-white font-medium transition-colors">
              Funcionalidades
            </a>
            <a href="#planos" className="hidden md:block text-sm text-gray-300 hover:text-white font-medium transition-colors">
              Preços
            </a>
            <a href="/dashboard" className="hidden md:block text-sm text-gray-300 hover:text-white font-medium transition-colors">
              Entrar
            </a>
            <a href="/dashboard" className="bg-white hover:bg-gray-100 text-black px-6 py-2.5 rounded-full font-bold transition-all shadow-lg shadow-white/10 hover:scale-105 text-sm">
              Começar Grátis
            </a>
          </div>
        </div>
      </nav>

      {/* --- HERO SECTION --- */}
      <section 
        className="relative min-h-[90vh] lg:min-h-[140vh] w-full flex flex-col items-center justify-start pt-24 lg:pt-32 bg-cover bg-bottom bg-no-repeat"
        style={{ backgroundImage: "url('/hero2.png')" }}
      >
        <div className="max-w-5xl mx-auto px-6 text-center relative z-10 flex flex-col items-center">
          <h1 className="text-4xl md:text-4xl lg:text-[6rem] font-serif font-bold text-white tracking-tighter mb-8 leading-none">
            A Nova Era Da <br />
            <span className="text-white tracking-tighter mb-8 leading-none">Análise de Ativos.</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-300 mb-12 max-w-2xl mx-auto leading-relaxed font-medium tracking-tight">
            Acelere a leitura de relatórios trimestrais. Deixe a IA estruturar os dados e gerar insights para apoiar sua decisão de investimento.
          </p>

          <div className="flex flex-col md:flex-row items-center justify-center gap-6 w-full md:w-auto">
            <a href="/dashboard" className="w-full md:w-auto bg-blue-500 text-white px-10 py-4 rounded-full font-bold text-lg hover:bg-blue-400 transition-transform hover:scale-105 flex items-center justify-center gap-2 shadow-[0_0_40px_-10px_rgba(59,130,246,0.7)]">
              Criar Conta Grátis <ArrowRight size={20} />
            </a>
            <a href="#funcionalidades" className="w-full md:w-auto px-10 py-4 rounded-full font-bold text-lg text-white border border-white/30 hover:bg-white/10 transition-all backdrop-blur-md bg-black/20">
              Ver Funcionalidades
            </a>
          </div>
        </div>
      </section>

      {/* --- SECÇÃO: FUNCIONALIDADES --- */}
      <div id="funcionalidades" className="flex flex-col">
        
        {/* BLOCO 1: UPLOAD */}
        <section 
          className="py-20 lg:py-56 relative bg-cover bg-center bg-no-repeat overflow-hidden"
          style={{ backgroundImage: "url('/upload.png')" }}
        >
          <div className="max-w-7xl mx-auto px-6 relative z-10">

            {/* Mobile: text on top centered; Desktop: side by side grid */}
            <div className="flex flex-col lg:grid lg:grid-cols-12 lg:gap-16 lg:items-center">

              {/* Text — centered on mobile, left-aligned on desktop */}
              <div className="lg:col-span-5 lg:col-start-1 text-center lg:text-left mb-12 lg:mb-0">
                <div className="w-14 h-14 bg-blue-500/20 rounded-2xl flex items-center justify-center mb-6 border border-blue-400/30 mx-auto lg:mx-0">
                  <UploadCloud className="text-blue-400 w-7 h-7" />
                </div>
                <h2 className="text-4xl md:text-5xl lg:text-[3rem] font-serif font-bold text-white mb-4 tracking-tighter leading-[1.05]">
                  Upload <br/>Inteligente
                </h2>
                <p className="text-base text-gray-300 leading-relaxed mb-8 font-medium tracking-tight max-w-md mx-auto lg:mx-0">
                  Simplifique sua rotina de análise. Basta arrastar o PDF do Release de Resultados (ITR ou DFP). Nossa IA vai gerar uma análise completa do resultado em segundos.
                </p>
              </div>

              {/* Phone — full width centered on mobile, right column on desktop */}
              <div className="lg:col-span-6 lg:col-start-7 relative flex justify-center lg:justify-end">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-blue-600/20 blur-[100px] rounded-full pointer-events-none" />
                {/* Mobile: constrain width so phone doesn't overflow */}
                <div className="w-full max-w-[260px] lg:max-w-none">
                  <PhoneImage />
                </div>
              </div>

            </div>
          </div>
        </section>

        {/* BLOCO 2: SCORE DE IA */}
<section
  className="pt-16 lg:pt-20 pb-16 lg:pb-24 relative bg-cover bg-center bg-no-repeat"
  style={{ backgroundImage: "url('/secao2.png')" }}
>

  <div className="max-w-4xl mx-auto px-6 relative z-10">
    <div className="flex flex-col items-center text-center mb-6">
      <div className="w-14 h-14 bg-green-500/20 rounded-2xl flex items-center justify-center mb-4 border border-green-400/30">
        <FileText className="text-green-400 w-7 h-7" />
      </div>
      <h2 className="text-4xl md:text-5xl lg:text-[4rem] font-serif font-bold text-white mb-4 tracking-tighter leading-[1.05]">
        Score de IA
      </h2>
      <p className="text-lg text-gray-300 leading-relaxed mb-6 font-medium tracking-tight max-w-xl">
        O FinAnalyzer gera um Score de 0 a 5 para cada métrica fundamentalista,
        facilitando a identificação imediata de pontos fortes e de atenção na empresa.
      </p>
    </div>

    <ScoreDemo />
  </div>
</section>

        {/* BLOCO 3: COMPARADOR DE ATIVOS */}
        <section 
          className="py-32 lg:py-56 relative"
          style={{ 
            backgroundImage: "url('/secao3_.png')",
            backgroundSize: 'cover',
            backgroundPosition: 'center center',
            backgroundRepeat: 'no-repeat'
          }}
        >
          <div className="max-w-7xl mx-auto px-6 relative z-10">
            <div className="grid lg:grid-cols-12 gap-0 items-start">
              <div className="lg:col-span-4 lg:col-start-9">
                <div className="w-14 h-14 bg-purple-500/20 rounded-2xl flex items-center justify-center mb-6 border border-purple-400/30">
                  <Layout className="text-purple-400 w-7 h-7" />
                </div>
                <h2 className="text-3xl md:text-4xl lg:text-[3rem] font-serif font-bold text-white mb-5 tracking-tighter leading-[1.05]">
                  Comparador <br/>de Ativos
                </h2>
                <p className="text-base text-gray-300 leading-relaxed mb-8 font-medium tracking-tight">
                  Visualize e compare todos os Resultados que você analisou. Ordene por Nota de Receita, Rentabilidade, Dívida, Lucro e muito mais.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* BLOCO 4: HISTÓRICO COMPLETO */}
        <section
          className="py-32 lg:py-48 relative bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/fundo-historico.png')" }}
        >
          <div className="absolute inset-0 bg-[#0A0D14]/60 pointer-events-none" />

          <div className="max-w-7xl mx-auto px-6 relative z-10">
            <div className="grid lg:grid-cols-12 gap-12 items-start">

              {/* Texto na esquerda */}
              <div className="lg:col-span-4 lg:col-start-1 order-1">
                <div className="w-16 h-16 bg-yellow-500/20 rounded-2xl flex items-center justify-center mb-8 border border-yellow-400/30">
                  <Database className="text-yellow-400 w-8 h-8" />
                </div>
                <h2 className="text-3xl md:text-4xl lg:text-[3rem] font-serif font-bold text-white mb-5 tracking-tighter leading-[1.05]">
                  Histórico <br />Completo
                </h2>
                <p className="text-base text-gray-300 leading-relaxed mb-8 font-medium tracking-tight">
                  Todas as suas análises ficam salvas para sempre. Compare a evolução da empresa trimestre a trimestre.
                </p>
              </div>

              {/* Tabela na direita */}
              <motion.div
                ref={historicoRef}
                className="lg:col-span-7 lg:col-start-6 order-2"
                initial={{ opacity: 0, y: 60 }}
                animate={historicoInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.8, ease: "easeOut" }}
              >
                <div className="bg-[#11141D]/80 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
                  <div className="px-6 py-5 border-b border-white/10">
                    <h3 className="text-xl font-bold text-white">Histórico Detalhado</h3>
                    <p className="text-sm text-gray-400 mt-1">Gerencie suas análises individuais.</p>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-white/10">
                          <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Empresa</th>
                          <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Período</th>
                          <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider hidden md:table-cell">Data</th>
                          <th className="text-center px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Score</th>
                          <th className="text-right px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Ações</th>
                        </tr>
                      </thead>
                      <tbody>
                        {historicoData.map((item, i) => (
                          <motion.tr
                            key={item.empresa}
                            className="border-b border-white/5 hover:bg-white/5 transition-colors"
                            initial={{ opacity: 0, x: 20 }}
                            animate={historicoInView ? { opacity: 1, x: 0 } : {}}
                            transition={{ duration: 0.4, delay: 0.1 + i * 0.06 }}
                          >
                            <td className="px-6 py-4 text-sm font-bold text-white">{item.empresa}</td>
                            <td className="px-6 py-4 text-sm text-gray-400">{item.periodo}</td>
                            <td className="px-6 py-4 text-sm text-gray-400 hidden md:table-cell">{item.data}</td>
                            <td className="px-6 py-4 text-center">
                              <ScoreBadge score={item.score} />
                            </td>
                            <td className="px-6 py-4 text-right">
                              <div className="flex items-center justify-end gap-3">
                                <Trash2 size={16} className="text-gray-500 cursor-pointer hover:text-red-400 transition-colors" />
                                <span className="text-blue-400 font-medium text-sm flex items-center gap-1 cursor-pointer hover:text-blue-300 transition-colors">
                                  Detalhes <ChevronRight size={14} />
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

      </div>

      {/* --- SECÇÃO DE PLANOS --- */}
      <section 
        id="planos" 
        className="py-32 lg:py-48 relative bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('/fundo-planos.jpg')" }}
      >
        <div className="max-w-7xl mx-auto px-6 relative z-10">
          
          <div className="mb-24 flex flex-col items-center text-center">
            <h2 className="text-3xl md:text-4xl lg:text-[5rem] font-serif font-bold text-white mb-8 tracking-tighter leading-[1.05]">
              Um único plano. <br className="hidden md:block"/>
              Invista melhor.
            </h2>
            
            <div className="flex items-center justify-center gap-4 bg-black/30 inline-flex p-2 rounded-full border border-white/20 mt-6 backdrop-blur-md">
              <button 
                onClick={() => setBillingCycle('monthly')}
                className={`px-10 py-4 rounded-full text-lg font-bold transition-all ${billingCycle === 'monthly' ? 'bg-white text-black shadow-lg' : 'text-gray-300 hover:text-white'}`}
              >
                Mensal
              </button>
              <button 
                onClick={() => setBillingCycle('yearly')}
                className={`px-10 py-4 rounded-full text-lg font-bold transition-all flex items-center gap-3 ${billingCycle === 'yearly' ? 'bg-white text-black shadow-lg' : 'text-gray-300 hover:text-white'}`}
              >
                Anual
              </button>
            </div>
            
            <div className={`transition-opacity duration-300 ${billingCycle === 'yearly' ? 'opacity-100' : 'opacity-0'} mt-8`}>
              <span className="bg-blue-500/90 text-white border border-blue-400 text-sm font-bold px-6 py-2.5 rounded-full uppercase tracking-wider shadow-xl">
                2 MESES GRÁTIS
              </span>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-12 items-stretch max-w-5xl mx-auto">
            
            {/* CARD GRATUITO */}
            <div className="bg-[#11141D]/90 backdrop-blur-xl border border-white/10 rounded-[2.5rem] p-14 hover:border-white/30 transition-colors flex flex-col shadow-2xl">
              <h3 className="text-4xl font-bold text-white mb-2 tracking-tight">Gratuito</h3>
              <p className="text-gray-400 text-xl mb-12 font-medium">Para começar a analisar sem custo.</p>
              
              <ul className="space-y-6 mb-16 flex-1">
                <Feature text="5 Análises por semana" active />
                <Feature text="Relatório Resumido na Tela" active />
                <Feature text="Acesso ao histórico simples" active />
                <Feature text="Suporte por email" active />
                <Feature text="Upload de arquivos ilimitado" disabled />
                <Feature text="Download da Análise Completa da IA" disabled />
                <Feature text="Tabela Comparativa de Ativos" disabled />
              </ul>

              <a href="/dashboard" className="block w-full text-center py-6 rounded-full border-2 border-white/30 text-white text-xl font-bold hover:bg-white/10 transition-all mt-auto backdrop-blur-md">
                Criar conta grátis
              </a>
            </div>

            {/* CARD PREMIUM */}
            <div className="bg-blue-600/95 backdrop-blur-2xl border border-blue-400/50 rounded-[2.5rem] p-14 relative shadow-[0_0_80px_-10px_rgba(37,99,235,0.8)] flex flex-col transform hover:-translate-y-4 transition-transform duration-300">
              <h3 className="text-4xl font-bold text-white mb-2 tracking-tight">Premium</h3>
              <div className="flex items-end gap-2 mb-2">
                <span className="text-[5.5rem] leading-none font-extrabold text-white tracking-tighter">{billingCycle === 'monthly' ? 'R$ 29' : 'R$ 290'}</span>
                <span className="text-blue-200 mb-4 font-medium text-2xl">{billingCycle === 'monthly' ? '/mês' : '/ano'}</span>
              </div>
              <p className="text-blue-100 text-xl mb-12 font-medium">Desbloqueie todo o poder da IA.</p>
              
              <ul className="space-y-6 mb-16 flex-1">
                <Feature text="Análises de IA Ilimitadas" active light />
                <Feature text="Relatório Resumido na Tela" active light />
                <Feature text="Acesso ao Histórico Ilimitado" active light />
                <Feature text="Suporte por Email" active light />
                <Feature text="Upload de arquivos ilimitado" active light />
                <Feature text="Download da Análise Completa da IA" active light />
                <Feature text="Tabela Comparativa de Ativos" active light />
                <Feature text="Prioridade máxima na fila" active light />
              </ul>

              <a href="/dashboard" className="block w-full text-center py-6 rounded-full bg-white text-blue-700 text-xl font-extrabold shadow-2xl hover:bg-gray-100 hover:scale-[1.02] transition-all mt-auto">
                Assinar Agora
              </a>
              <p className="text-center text-sm text-blue-200 mt-8 font-medium">Cancele quando quiser.</p>
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
              <a href="/terms" className="text-base text-gray-400 hover:text-white transition-colors font-medium">Termos de Uso</a>
              <a href="/privacy" className="text-base text-gray-400 hover:text-white transition-colors font-medium">Privacidade</a>
              <a href="/refund" className="text-base text-gray-400 hover:text-white transition-colors font-medium">Reembolso</a>
            </div>
          </div>

          <div className="border-t border-white/10 pt-12 text-sm text-gray-400 space-y-4 text-justify leading-relaxed font-light">
            <p>
              <strong className="text-gray-300 font-semibold">AVISO IMPORTANTE SOBRE IA:</strong> A análise apresentada nesta plataforma é gerada por algoritmos de Inteligência Artificial e serve apenas como uma <strong className="text-gray-300 font-semibold">ferramenta auxiliar de suporte</strong>. Ela <strong className="text-gray-300 font-semibold">não substitui a análise humana</strong>, nem constitui recomendação de compra ou venda de ativos. O FinAnalyzer.AI não se responsabiliza pela precisão, integridade ou atualização dos dados, nem por quaisquer decisões de investimento ou prejuízos financeiros decorrentes do uso destas informações. Rentabilidade passada não representa garantia de rentabilidade futura.
            </p>
            <p className="text-center pt-10 text-gray-500 font-medium">
              © 2026 FinAnalyzer Inc. Todos os direitos reservados.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}