"use client";
import React, { useState } from 'react';
// import Link from 'next/link'; // <--- Descomente no seu projeto Next.js e use Link no lugar de <a>
import { 
  BarChart3, UploadCloud, ArrowRight, 
  FileText, Layout, Database, Check, X, CheckCircle2,
  Maximize2 
} from "lucide-react";

// --- COMPONENTE: ECRÃ DE APP (Design Robinhood/Glassmorphism) ---
const AppScreen = ({ children, className = "", zoom = false, tilt = "none" }: { children: React.ReactNode, className?: string, zoom?: boolean, tilt?: "left" | "right" | "up" | "none" }) => {
  const tiltClasses = {
    left: "-rotate-2 hover:rotate-0 translate-x-2 md:translate-x-4",
    right: "rotate-2 hover:rotate-0 -translate-x-2 md:-translate-x-4",
    up: "hover:-translate-y-3",
    none: "hover:scale-[1.02]"
  };

  return (
    <div className={`relative group transition-all duration-700 ease-out w-full ${tiltClasses[tilt]} ${className}`}>
      {/* Brilho de fundo da janela */}
      <div className="absolute -inset-2 bg-gradient-to-tr from-blue-500/20 to-purple-500/20 rounded-[2.5rem] blur-xl opacity-0 group-hover:opacity-100 transition duration-700 pointer-events-none" />
      
      {/* Container Principal (Glassmorphism) */}
      <div className="relative rounded-[1.5rem] md:rounded-[2.5rem] border border-white/10 bg-black/40 backdrop-blur-xl shadow-[0_30px_80px_-15px_rgba(0,0,0,0.8)] overflow-hidden">
        
        {/* Lógica de Zoom */}
        <div className={`relative w-full ${zoom ? 'scale-[1.35] translate-y-8 md:translate-y-12' : ''} transition-transform duration-700 ease-out origin-top`}>
           {children}
        </div>
        
        {/* Overlay de reflexo subtil */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/[0.05] to-transparent pointer-events-none z-10" />
      </div>
    </div>
  );
};

export default function LandingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  return (
    <div className="min-h-screen bg-[#0A0D14] text-gray-100 font-sans selection:bg-blue-500/30 overflow-x-hidden">

      {/* --- NAVBAR --- */}
      <nav className="border-b border-white/10 bg-black/60 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-[90rem] mx-auto px-6 h-20 flex items-center justify-between">
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
        className="relative pt-24 pb-32 bg-cover bg-center bg-no-repeat"
        // 👇 AQUI: Caminho para a sua imagem local na pasta public/
        style={{ backgroundImage: "url('/fundo-hero.jpg')" }}
      >
        {/* Overlay escuro para garantir leitura */}
        <div className="absolute inset-0 bg-black/70 backdrop-blur-sm z-0" />

        <div className="max-w-[90rem] mx-auto px-6 text-center relative z-10">
          
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 border border-white/20 text-gray-200 text-sm font-medium mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500 backdrop-blur-md">
             <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" /> Nova Versão 2.0
          </div>

          <h1 className="text-5xl md:text-8xl font-extrabold text-white tracking-tight mb-8 leading-[1.1] drop-shadow-2xl">
            A Nova Era Da <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 drop-shadow-lg">Análise de Ativos.</span>
          </h1>
          
          <p className="text-xl md:text-3xl text-gray-300 mb-12 max-w-4xl mx-auto leading-relaxed font-light drop-shadow-md">
            Acelere a leitura de relatórios trimestrais. Deixe a IA estruturar os dados e gerar insights para apoiar sua decisão de investimento.
          </p>

          <div className="flex flex-col md:flex-row items-center justify-center gap-4">
            <a href="/dashboard" className="w-full md:w-auto bg-white text-gray-900 px-10 py-5 rounded-full font-bold text-lg hover:bg-gray-100 transition-transform hover:scale-105 flex items-center justify-center gap-2 shadow-2xl shadow-white/20">
              Criar Conta Grátis <ArrowRight size={20} />
            </a>
            <a href="#funcionalidades" className="w-full md:w-auto px-10 py-5 rounded-full font-bold text-lg text-white border border-white/30 hover:bg-white/10 transition-all backdrop-blur-sm">
              Ver Funcionalidades
            </a>
          </div>
        </div>
      </section>

      {/* --- SECÇÃO: FUNCIONALIDADES --- */}
      <div id="funcionalidades" className="flex flex-col">
        
        {/* BLOCO 1: UPLOAD */}
        <section 
          className="py-32 relative border-t border-white/10 bg-cover bg-center bg-no-repeat"
          // 👇 AQUI: Imagem local para o bloco Upload
          style={{ backgroundImage: "url('/fundo-upload.jpg')" }}
        >
          <div className="absolute inset-0 bg-black/80 z-0" />
          
          <div className="max-w-[90rem] mx-auto px-6 relative z-10">
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              <div className="order-2 lg:order-1">
                <div className="w-16 h-16 bg-blue-500/20 rounded-2xl flex items-center justify-center mb-8 border border-blue-400/30 backdrop-blur-sm shadow-xl">
                  <UploadCloud className="text-blue-400 w-8 h-8" />
                </div>
                <h2 className="text-5xl md:text-6xl font-bold text-white mb-6 tracking-tight drop-shadow-lg">Upload Inteligente</h2>
                <p className="text-xl text-gray-300 leading-relaxed mb-8 font-light drop-shadow-md">
                  Simplifique sua rotina de análise. Basta arrastar o PDF do Release de Resultados (ITR ou DFP). Nossa IA vai gerar uma análise completa do resultado em segundos.
                </p>
                <ul className="space-y-5">
                  <ListItem>Suporte a PDFs de até 10MB</ListItem>
                  <ListItem>Extração automática de métricas</ListItem>
                  <ListItem>Identificação de trimestre e ano</ListItem>
                </ul>
              </div>
              
              <div className="order-1 lg:order-2">
                <AppScreen tilt="right">
                  <img 
                    src="/image_456e01.png" 
                    alt="Ecrã de Upload" 
                    className="w-full h-auto object-cover opacity-90 hover:opacity-100 transition-opacity duration-700"
                  />
                </AppScreen>
              </div>
            </div>
          </div>
        </section>

        {/* BLOCO 2: ANÁLISE PROFUNDA (SCORE) */}
        <section 
          className="py-32 relative border-t border-white/10 bg-cover bg-center bg-no-repeat"
          // 👇 AQUI: Imagem local para o bloco Score
          style={{ backgroundImage: "url('/fundo-score.png')" }}
        >
          <div className="absolute inset-0 bg-black/80 z-0" />

          <div className="max-w-[90rem] mx-auto px-6 relative z-10">
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              
              <div className="order-2 lg:order-1">
                 <AppScreen tilt="left">
                  <img 
                    src="/Captura de tela 2026-02-22 222027.png" 
                    alt="Ecrã de Análise" 
                    className="w-full h-auto object-cover opacity-90 hover:opacity-100 transition-transform duration-700 scale-[1.2] md:scale-[1.25] origin-top translate-y-2 md:translate-y-4"
                  />
                </AppScreen>
              </div>

              <div className="order-1 lg:order-2">
                <div className="w-16 h-16 bg-green-500/20 rounded-2xl flex items-center justify-center mb-8 border border-green-400/30 backdrop-blur-sm shadow-xl">
                  <FileText className="text-green-400 w-8 h-8" />
                </div>
                <h2 className="text-5xl md:text-6xl font-bold text-white mb-6 tracking-tight drop-shadow-lg">Score de IA</h2>
                <p className="text-xl text-gray-300 leading-relaxed mb-8 font-light drop-shadow-md">
                  O FinAnalyzer gera um Score de 0 a 5 para cada métrica fundamentalista, facilitando a identificação imediata de pontos fortes e de atenção na empresa.
                </p>
                <ul className="space-y-5">
                  <ListItem>Score de Receita e Lucro</ListItem>
                  <ListItem>Análise de Endividamento</ListItem>
                  <ListItem>Resumo textual da Tese</ListItem>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* BLOCO 3: COMPARADOR DE ATIVOS */}
        <section 
          className="py-32 relative border-t border-white/10 bg-cover bg-center bg-no-repeat"
          // 👇 AQUI: Imagem local para o bloco Comparador
          style={{ backgroundImage: "url('/fundo-comparador.jpg')" }}
        >
          <div className="absolute inset-0 bg-black/80 z-0" />
          
          <div className="max-w-[90rem] mx-auto px-6 text-center relative z-10">
            <div className="max-w-4xl mx-auto mb-16">
              <div className="w-20 h-20 bg-purple-500/20 rounded-3xl flex items-center justify-center mb-8 border border-purple-400/30 mx-auto backdrop-blur-sm shadow-xl">
                <Layout className="text-purple-400 w-10 h-10" />
              </div>
              <h2 className="text-5xl md:text-7xl font-bold text-white mb-6 tracking-tight drop-shadow-lg">Comparador de Ativos</h2>
              <p className="text-2xl text-gray-300 leading-relaxed font-light drop-shadow-md">
                Visualize e compare todos os Resultados que você analisou. Ordene por Nota de Receita, Rentabilidade, Dívida, Lucro e muito mais.
              </p>
            </div>

            <div className="max-w-[80rem] mx-auto">
               <AppScreen zoom={true} tilt="up" className="border-purple-500/20 shadow-purple-900/40">
                  <img 
                    src="/image_03af1d.png" 
                    alt="Tabela Comparativa" 
                    className="w-full h-auto object-cover"
                  />
               </AppScreen>
               <p className="mt-8 text-base text-gray-400 flex items-center justify-center gap-2 drop-shadow-md">
                 <Maximize2 size={16} /> Visualização otimizada para foco nos dados
               </p>
            </div>
          </div>
        </section>

        {/* BLOCO 4: HISTÓRICO */}
        <section 
          className="py-32 relative border-t border-white/10 bg-cover bg-center bg-no-repeat"
          // 👇 AQUI: Imagem local para o bloco Histórico
          style={{ backgroundImage: "url('/fundo-historico.jpg')" }}
        >
          <div className="absolute inset-0 bg-black/80 z-0" />

           <div className="max-w-[90rem] mx-auto px-6 text-center relative z-10">
              <div className="w-20 h-20 bg-yellow-500/20 rounded-3xl flex items-center justify-center mb-8 border border-yellow-400/30 mx-auto backdrop-blur-sm shadow-xl">
                <Database className="text-yellow-400 w-10 h-10" />
              </div>
              <h2 className="text-5xl md:text-7xl font-bold text-white mb-6 tracking-tight drop-shadow-lg">Histórico Completo</h2>
              <p className="text-2xl text-gray-300 leading-relaxed max-w-3xl mx-auto mb-16 font-light drop-shadow-md">
                Todas as suas análises ficam salvas para sempre. Compare a evolução da empresa trimestre a trimestre.
              </p>
              
              <AppScreen tilt="up" className="max-w-5xl mx-auto border-yellow-500/20 shadow-yellow-900/30">
                  <img 
                    src="/demo-history.png" 
                    alt="Histórico" 
                    className="w-full h-auto object-cover opacity-90 hover:opacity-100 transition-all duration-700"
                  />
               </AppScreen>
           </div>
        </section>

      </div>
      
      {/* --- SECÇÃO DE PLANOS --- */}
      <section 
        id="planos" 
        className="py-32 relative border-t border-white/10 bg-cover bg-center bg-no-repeat"
        // 👇 AQUI: Imagem local para o bloco Planos
        style={{ backgroundImage: "url('/fundo-planos.jpg')" }}
      >
        <div className="absolute inset-0 bg-black/80 backdrop-blur-sm z-0" />

        <div className="max-w-[90rem] mx-auto px-6 relative z-10">
          <div className="text-center mb-20">
            <h2 className="text-5xl md:text-7xl font-extrabold text-white mb-6 tracking-tight drop-shadow-lg">
              Um único plano. <br className="hidden md:block"/>
              Invista melhor com o poder da IA.
            </h2>
            
            <div className="flex items-center justify-center gap-4 bg-white/10 inline-flex p-1.5 rounded-full border border-white/20 mt-8 backdrop-blur-md">
              <button 
                onClick={() => setBillingCycle('monthly')}
                className={`px-8 py-3 rounded-full text-base font-bold transition-all ${billingCycle === 'monthly' ? 'bg-white text-black shadow-lg' : 'text-gray-300 hover:text-white'}`}
              >
                Mensal
              </button>
              <button 
                onClick={() => setBillingCycle('yearly')}
                className={`px-8 py-3 rounded-full text-base font-bold transition-all flex items-center gap-2 ${billingCycle === 'yearly' ? 'bg-white text-black shadow-lg' : 'text-gray-300 hover:text-white'}`}
              >
                Anual
              </button>
            </div>
            
            <div className={`transition-opacity duration-300 ${billingCycle === 'yearly' ? 'opacity-100' : 'opacity-0'} mt-6`}>
               <span className="bg-orange-500/30 text-orange-300 border border-orange-500/40 text-sm font-bold px-5 py-2 rounded-full uppercase tracking-wider backdrop-blur-sm shadow-xl">
                 2 MESES GRÁTIS
               </span>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-10 items-stretch max-w-5xl mx-auto">
            
            {/* CARD GRATUITO */}
            <div className="bg-black/50 backdrop-blur-xl border border-white/10 rounded-[2.5rem] p-12 hover:border-white/30 transition-colors flex flex-col shadow-2xl">
              <h3 className="text-4xl font-bold text-white mb-2 drop-shadow-md">Gratuito</h3>
              <p className="text-gray-400 text-lg mb-10 font-light">Para começar a analisar sem custo.</p>
              
              <ul className="space-y-6 mb-12 flex-1">
                <Feature text="5 Análises por semana" active />
                <Feature text="Relatório Resumido na Tela" active />
                <Feature text="Acesso ao histórico simples" active />
                <Feature text="Suporte por email" active />
                <Feature text="Upload de arquivos ilimitado" disabled />
                <Feature text="Download da Análise Completa da IA" disabled />
                <Feature text="Tabela Comparativa de Ativos" disabled />
              </ul>

              <a href="/dashboard" className="block w-full text-center py-5 rounded-full border-2 border-white/30 text-white text-lg font-bold hover:bg-white/10 transition-all mt-auto backdrop-blur-md">
                Criar conta grátis
              </a>
            </div>

            {/* CARD PREMIUM */}
            <div className="bg-blue-600/90 backdrop-blur-2xl border border-blue-400/50 rounded-[2.5rem] p-12 relative shadow-[0_0_80px_-10px_rgba(37,99,235,0.6)] flex flex-col transform hover:-translate-y-3 transition-transform duration-300">
              <h3 className="text-4xl font-bold text-white mb-2 drop-shadow-md">Premium</h3>
              <div className="flex items-end gap-2 mb-2">
                <span className="text-7xl font-extrabold text-white drop-shadow-lg">{billingCycle === 'monthly' ? 'R$ 29' : 'R$ 290'}</span>
                <span className="text-blue-200 mb-3 font-medium text-xl">{billingCycle === 'monthly' ? '/mês' : '/ano'}</span>
              </div>
              <p className="text-blue-100 text-lg mb-10 font-light drop-shadow-md">Desbloqueie todo o poder da IA.</p>
              
              <ul className="space-y-6 mb-12 flex-1">
                <Feature text="Análises de IA Ilimitadas" active light />
                <Feature text="Relatório Resumido na Tela" active light />
                <Feature text="Acesso ao Histórico Ilimitado" active light />
                <Feature text="Suporte por Email" active light />
                <Feature text="Upload de arquivos ilimitado" active light />
                <Feature text="Download da Análise Completa da IA" active light />
                <Feature text="Tabela Comparativa de Ativos" active light />
                <Feature text="Prioridade máxima na fila" active light />
              </ul>

              <a href="/dashboard" className="block w-full text-center py-5 rounded-full bg-white text-blue-900 text-lg font-extrabold shadow-2xl hover:bg-gray-100 hover:scale-[1.02] transition-all mt-auto">
                Assinar Agora
              </a>
              <p className="text-center text-sm text-blue-200 mt-6 font-medium drop-shadow-md">Cancele quando quiser.</p>
            </div>
          </div>
        </div>
      </section>

      {/* --- FOOTER & DISCLAIMERS --- */}
      <footer className="border-t border-white/10 bg-black/80 backdrop-blur-2xl pt-20 pb-10">
        <div className="max-w-[90rem] mx-auto px-6">
          
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

          <div className="border-t border-white/10 pt-10 text-sm text-gray-400 space-y-4 text-justify leading-relaxed font-light">
             <p>
               <strong className="text-gray-300 font-semibold">AVISO IMPORTANTE SOBRE IA:</strong> A análise apresentada nesta plataforma é gerada por algoritmos de Inteligência Artificial e serve apenas como uma <strong className="text-gray-300 font-semibold">ferramenta auxiliar de suporte</strong>. Ela <strong className="text-gray-300 font-semibold">não substitui a análise humana</strong>, nem constitui recomendação de compra ou venda de ativos. O FinAnalyzer.AI não se responsabiliza pela precisão, integridade ou atualização dos dados, nem por quaisquer decisões de investimento ou prejuízos financeiros decorrentes do uso destas informações. Rentabilidade passada não representa garantia de rentabilidade futura.
             </p>

             <p className="text-center pt-8 text-gray-500 font-medium">
               © 2026 FinAnalyzer Inc. Todos os direitos reservados.
             </p>
          </div>

        </div>
      </footer>
    </div>
  );
}

// Subcomponentes
function Feature({ text, active = false, disabled = false, light = false }: any) {
  return (
    <li className="flex items-center gap-4">
      {disabled ? (
        <div className="p-1.5 rounded-full border border-gray-600 text-gray-500"><X size={14} /></div>
      ) : (
        <div className={`p-1.5 rounded-full ${light ? 'bg-white text-blue-600' : 'bg-green-500/20 text-green-400'}`}>
          <Check size={14} strokeWidth={3} />
        </div>
      )}
      <span className={`text-lg font-medium ${disabled ? 'text-gray-500 line-through' : light ? 'text-white' : 'text-gray-200'}`}>{text}</span>
    </li>
  );
}

function ListItem({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-center gap-4 text-gray-200 font-medium text-lg">
      <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 border border-blue-500/30">
         <Check size={16} className="text-blue-400" strokeWidth={3} />
      </div>
      <span className="drop-shadow-sm">{children}</span>
    </li>
  );
}