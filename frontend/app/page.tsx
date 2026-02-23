"use client";
import React, { useState } from 'react';
// import Link from 'next/link'; // <--- Descomente no seu projeto Next.js e use Link no lugar de <a>
import { 
  BarChart3, UploadCloud, ArrowRight, 
  FileText, Layout, Database, Check, X, CheckCircle2,
  Maximize2 
} from "lucide-react";

// --- NOVO COMPONENTE: TELA DE APP (Design Robinhood/Fintech) ---
// Substitui a antiga moldura de navegador por uma apresentação mais limpa, 
// com cantos muito arredondados, bordas subtis e sombras profundas.
const AppScreen = ({ children, className = "", zoom = false, tilt = "none" }: { children: React.ReactNode, className?: string, zoom?: boolean, tilt?: "left" | "right" | "up" | "none" }) => {
  const tiltClasses = {
    left: "-rotate-2 hover:rotate-0 translate-x-2 md:translate-x-4",
    right: "rotate-2 hover:rotate-0 -translate-x-2 md:-translate-x-4",
    up: "hover:-translate-y-3",
    none: "hover:scale-[1.02]"
  };

  return (
    <div className={`relative group transition-all duration-700 ease-out ${tiltClasses[tilt]} ${className}`}>
      {/* Glow de fundo da imagem (brilho difuso) */}
      <div className="absolute -inset-2 bg-gradient-to-tr from-blue-500/10 to-purple-500/10 rounded-[2.5rem] blur-xl opacity-0 group-hover:opacity-100 transition duration-700 pointer-events-none" />
      
      {/* Container Principal */}
      <div className="relative rounded-[1.5rem] md:rounded-[2.5rem] border border-white/5 bg-[#0A0D14] shadow-[0_20px_60px_-15px_rgba(0,0,0,0.6)] overflow-hidden">
        
        {/* Lógica de Zoom para imagens com bordas indesejadas */}
        <div className={`relative w-full ${zoom ? 'scale-[1.35] translate-y-8 md:translate-y-12' : ''} transition-transform duration-700 ease-out origin-top`}>
           {children}
        </div>
        
        {/* Overlay de reflexo subtil (Glass effect) */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/[0.03] to-transparent pointer-events-none z-10" />
      </div>
    </div>
  );
};

export default function LandingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  return (
    <div className="min-h-screen bg-[#0A0D14] text-gray-100 font-sans selection:bg-blue-500/30 overflow-x-hidden">
      
      {/* --- NAVBAR --- */}
      <nav className="border-b border-white/5 bg-[#0A0D14]/80 backdrop-blur-xl sticky top-0 z-50">
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
            <a href="#funcionalidades" className="hidden md:block text-sm text-gray-400 hover:text-white font-medium transition-colors">
              Funcionalidades
            </a>
            <a href="#planos" className="hidden md:block text-sm text-gray-400 hover:text-white font-medium transition-colors">
              Preços
            </a>
            
            <a href="/dashboard" className="hidden md:block text-sm text-gray-400 hover:text-white font-medium transition-colors">
              Entrar
            </a>
            <a href="/dashboard" className="bg-white hover:bg-gray-100 text-black px-6 py-2.5 rounded-full font-bold transition-all shadow-lg shadow-white/10 hover:scale-105 text-sm">
              Começar Grátis
            </a>
          </div>
        </div>
      </nav>

      {/* --- HERO SECTION --- */}
      <section className="relative pt-24 pb-32 overflow-hidden">
        {/* Glow de fundo */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[80vw] h-[500px] bg-blue-600/10 blur-[150px] rounded-full -z-10 opacity-70 pointer-events-none" />

        <div className="max-w-5xl mx-auto px-6 text-center">
          
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-gray-300 text-sm font-medium mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
             <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" /> Nova Versão 2.0
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold text-white tracking-tight mb-8 leading-[1.1]">
            A Nova Era Da <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">Análise de Ativos.</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-400 mb-12 max-w-2xl mx-auto leading-relaxed font-light">
            Acelere a leitura de relatórios trimestrais. Deixe a IA estruturar os dados e gerar insights para apoiar sua decisão de investimento.
          </p>

          <div className="flex flex-col md:flex-row items-center justify-center gap-4">
            <a href="/dashboard" className="w-full md:w-auto bg-white text-gray-900 px-8 py-4 rounded-full font-bold text-lg hover:bg-gray-100 transition-transform hover:scale-105 flex items-center justify-center gap-2 shadow-xl shadow-white/10">
              Criar Conta Grátis <ArrowRight size={20} />
            </a>
            <a href="#funcionalidades" className="w-full md:w-auto px-8 py-4 rounded-full font-bold text-lg text-gray-300 border border-white/10 hover:bg-white/5 hover:text-white transition-all">
              Ver Funcionalidades
            </a>
          </div>
        </div>
      </section>

      {/* --- SEÇÃO: FUNCIONALIDADES --- */}
      <div id="funcionalidades" className="flex flex-col bg-[#0A0D14]">
        
        {/* BLOCO 1: UPLOAD */}
        <section className="py-32 relative border-t border-white/5 overflow-hidden">
          <div className="absolute top-1/2 right-0 w-[400px] h-[400px] bg-blue-600/5 blur-[120px] rounded-full -z-10 pointer-events-none" />
          
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid md:grid-cols-2 gap-16 items-center">
              <div className="order-2 md:order-1">
                <div className="w-14 h-14 bg-blue-600/10 rounded-2xl flex items-center justify-center mb-8 border border-blue-500/20">
                  <UploadCloud className="text-blue-400 w-7 h-7" />
                </div>
                <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">Upload Inteligente</h2>
                <p className="text-lg text-gray-400 leading-relaxed mb-8 font-light">
                  Simplifique sua rotina de análise. Basta arrastar o PDF do Release de Resultados (ITR ou DFP). Nossa IA vai gerar uma análise completa do resultado em segundos.
                </p>
                <ul className="space-y-4">
                  <ListItem>Suporte a PDFs de até 10MB</ListItem>
                  <ListItem>Extração automática de métricas</ListItem>
                  <ListItem>Identificação de trimestre e ano</ListItem>
                </ul>
              </div>
              
              {/* Moldura AppScreen para Imagem */}
              <div className="order-1 md:order-2">
                <AppScreen tilt="right">
                  <img 
                    src="/image_456e01.png" 
                    alt="Tela de Upload" 
                    className="w-full h-auto object-cover opacity-90 hover:opacity-100 transition-opacity"
                  />
                </AppScreen>
              </div>
            </div>
          </div>
        </section>

        {/* BLOCO 2: ANÁLISE PROFUNDA */}
        <section className="py-32 relative border-t border-white/5 bg-[#0D111A]">
          <div className="absolute top-1/2 left-0 w-[400px] h-[400px] bg-green-600/5 blur-[120px] rounded-full -z-10 pointer-events-none" />

          <div className="max-w-7xl mx-auto px-6">
            <div className="grid md:grid-cols-2 gap-16 items-center">
              
              <div className="order-2 md:order-1">
                 <AppScreen tilt="left">
                  <img 
                    src="/demo-result.png" 
                    alt="Tela de Análise" 
                    className="w-full h-auto object-cover opacity-90 hover:opacity-100 transition-opacity"
                  />
                </AppScreen>
              </div>

              <div className="order-1 md:order-2">
                <div className="w-14 h-14 bg-green-600/10 rounded-2xl flex items-center justify-center mb-8 border border-green-500/20">
                  <FileText className="text-green-400 w-7 h-7" />
                </div>
                <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">Score de IA</h2>
                <p className="text-lg text-gray-400 leading-relaxed mb-8 font-light">
                  O FinAnalyzer gera um Score de 0 a 5 para cada métrica fundamentalista, facilitando a identificação imediata de pontos fortes e de atenção na empresa.
                </p>
                <ul className="space-y-4">
                  <ListItem>Score de Receita e Lucro</ListItem>
                  <ListItem>Análise de Endividamento</ListItem>
                  <ListItem>Resumo textual da Tese</ListItem>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* BLOCO 3: COMPARADOR DE ATIVOS (COM ZOOM MANTIDO) */}
        <section className="py-32 relative border-t border-white/5 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-purple-900/5 to-transparent pointer-events-none" />
          
          <div className="max-w-7xl mx-auto px-6 text-center relative z-10">
            <div className="max-w-3xl mx-auto mb-16">
              <div className="w-16 h-16 bg-purple-600/10 rounded-2xl flex items-center justify-center mb-8 border border-purple-500/20 mx-auto">
                <Layout className="text-purple-400 w-8 h-8" />
              </div>
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">Comparador de Ativos</h2>
              <p className="text-xl text-gray-400 leading-relaxed font-light">
                Visualize e compare todos os Resultados que você analisou. Ordene por Nota de Receita, Rentabilidade, Dívida, Lucro e muito mais.
              </p>
            </div>

            <div className="max-w-6xl mx-auto">
               <AppScreen zoom={true} tilt="up" className="border-purple-500/10 shadow-purple-900/10">
                  <img 
                    src="/image_03af1d.png" 
                    alt="Tabela Comparativa" 
                    className="w-full h-auto object-cover"
                  />
               </AppScreen>
               <p className="mt-8 text-sm text-gray-500 flex items-center justify-center gap-2">
                 <Maximize2 size={14} /> Visualização otimizada para foco nos dados
               </p>
            </div>
          </div>
        </section>

        {/* BLOCO 4: HISTÓRICO */}
        <section className="py-32 relative border-t border-white/5 bg-[#0D111A]">
           <div className="max-w-6xl mx-auto px-6 text-center">
              <div className="w-16 h-16 bg-yellow-600/10 rounded-2xl flex items-center justify-center mb-8 border border-yellow-500/20 mx-auto">
                <Database className="text-yellow-400 w-8 h-8" />
              </div>
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">Histórico Completo</h2>
              <p className="text-xl text-gray-400 leading-relaxed max-w-2xl mx-auto mb-16 font-light">
                Todas as suas análises ficam salvas para sempre. Compare a evolução da empresa trimestre a trimestre.
              </p>
              
              <AppScreen tilt="up" className="max-w-4xl mx-auto border-yellow-500/10 shadow-yellow-900/10">
                  <img 
                    src="/demo-history.png" 
                    alt="Histórico" 
                    className="w-full h-auto object-cover opacity-90 hover:opacity-100 transition-opacity"
                  />
               </AppScreen>
           </div>
        </section>

      </div>
      
      {/* --- SEÇÃO DE PLANOS --- */}
      <section id="planos" className="py-32 relative bg-[#0A0D14] border-t border-white/5">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-extrabold text-white mb-6 tracking-tight">
              Um único plano. <br className="hidden md:block"/>
              Invista melhor com o poder da IA.
            </h2>
            
            <div className="flex items-center justify-center gap-4 bg-white/5 inline-flex p-1 rounded-full border border-white/10 mt-8">
              <button 
                onClick={() => setBillingCycle('monthly')}
                className={`px-6 py-2.5 rounded-full text-sm font-bold transition-all ${billingCycle === 'monthly' ? 'bg-white text-black shadow-lg' : 'text-gray-400 hover:text-white'}`}
              >
                Mensal
              </button>
              <button 
                onClick={() => setBillingCycle('yearly')}
                className={`px-6 py-2.5 rounded-full text-sm font-bold transition-all flex items-center gap-2 ${billingCycle === 'yearly' ? 'bg-white text-black shadow-lg' : 'text-gray-400 hover:text-white'}`}
              >
                Anual
              </button>
            </div>
            
            <div className={`transition-opacity duration-300 ${billingCycle === 'yearly' ? 'opacity-100' : 'opacity-0'} mt-4`}>
               <span className="bg-orange-500/20 text-orange-400 text-xs font-bold px-4 py-1.5 rounded-full uppercase tracking-wider">
                 2 MESES GRÁTIS
               </span>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8 items-stretch max-w-4xl mx-auto">
            
            {/* CARD GRATUITO */}
            <div className="bg-[#11141D] border border-white/5 rounded-[2.5rem] p-10 hover:border-white/10 transition-colors flex flex-col">
              <h3 className="text-3xl font-bold text-white mb-2">Gratuito</h3>
              <p className="text-gray-400 text-base mb-10 font-light">Para começar a analisar sem custo.</p>
              
              <ul className="space-y-5 mb-10 flex-1">
                <Feature text="5 Análises por semana" active />
                <Feature text="Relatório Resumido na Tela" active />
                <Feature text="Acesso ao histórico simples" active />
                <Feature text="Suporte por email" active />
                {/* Bloqueios */}
                <Feature text="Upload de arquivos ilimitado" disabled />
                <Feature text="Download da Análise Completa da IA" disabled />
                <Feature text="Tabela Comparativa de Ativos" disabled />
              </ul>

              <a href="/dashboard" className="block w-full text-center py-4 rounded-full border border-white/20 text-white font-bold hover:bg-white/5 transition-all mt-auto">
                Criar conta grátis
              </a>
            </div>

            {/* CARD PREMIUM */}
            <div className="bg-blue-600 rounded-[2.5rem] p-10 relative shadow-[0_0_50px_-12px_rgba(37,99,235,0.4)] flex flex-col transform hover:-translate-y-2 transition-transform duration-300">
              <h3 className="text-3xl font-bold text-white mb-2">Premium</h3>
              <div className="flex items-end gap-1 mb-2">
                <span className="text-6xl font-extrabold text-white">{billingCycle === 'monthly' ? 'R$ 29' : 'R$ 290'}</span>
                <span className="text-blue-200 mb-2 font-medium">{billingCycle === 'monthly' ? '/mês' : '/ano'}</span>
              </div>
              <p className="text-blue-200 text-sm mb-10 font-light">Desbloqueie todo o poder da IA.</p>
              
              <ul className="space-y-5 mb-10 flex-1">
                <Feature text="Análises de IA Ilimitadas" active light />
                <Feature text="Relatório Resumido na Tela" active light />
                <Feature text="Acesso ao Histórico Ilimitado" active light />
                <Feature text="Suporte por Email" active light />
                <Feature text="Upload de arquivos ilimitado" active light />
                <Feature text="Download da Análise Completa da IA" active light />
                <Feature text="Tabela Comparativa de Ativos" active light />
                <Feature text="Prioridade máxima na fila" active light />
              </ul>

              <a href="/dashboard" className="block w-full text-center py-4 rounded-full bg-white text-blue-900 font-extrabold shadow-xl hover:bg-gray-100 transition-all mt-auto">
                Assinar Agora
              </a>
              <p className="text-center text-xs text-blue-200 mt-4 font-medium">Cancele quando quiser.</p>
            </div>
          </div>
        </div>
      </section>

      {/* --- FOOTER & DISCLAIMERS --- */}
      <footer className="border-t border-white/5 bg-[#0A0D14] pt-20 pb-10">
        <div className="max-w-7xl mx-auto px-6">
          
          <div className="flex flex-col md:flex-row justify-between items-center gap-6 mb-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center border border-white/10">
                <BarChart3 className="text-gray-400 w-5 h-5" />
              </div>
              <span className="text-xl font-bold text-gray-300 tracking-tight">FinAnalyzer.AI</span>
            </div>
            
            <div className="flex gap-8">
              <a href="/terms" className="text-sm text-gray-400 hover:text-white transition-colors font-medium">Termos de Uso</a>
              <a href="/privacy" className="text-sm text-gray-400 hover:text-white transition-colors font-medium">Privacidade</a>
              <a href="/refund" className="text-sm text-gray-400 hover:text-white transition-colors font-medium">Reembolso</a>
            </div>
          </div>

          <div className="border-t border-white/5 pt-10 text-xs text-gray-500 space-y-4 text-justify leading-relaxed font-light">
             <p>
               <strong className="text-gray-400 font-semibold">AVISO IMPORTANTE SOBRE IA:</strong> A análise apresentada nesta plataforma é gerada por algoritmos de Inteligência Artificial e serve apenas como uma <strong className="text-gray-400 font-semibold">ferramenta auxiliar de suporte</strong>. Ela <strong className="text-gray-400 font-semibold">não substitui a análise humana</strong>, nem constitui recomendação de compra ou venda de ativos. O FinAnalyzer.AI não se responsabiliza pela precisão, integridade ou atualização dos dados, nem por quaisquer decisões de investimento ou prejuízos financeiros decorrentes do uso destas informações. Rentabilidade passada não representa garantia de rentabilidade futura.
             </p>

             <p className="text-center pt-6 text-gray-600 font-medium">
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
        <div className="p-1 rounded-full border border-gray-700 text-gray-600"><X size={12} /></div>
      ) : (
        <div className={`p-1 rounded-full ${light ? 'bg-white text-blue-600' : 'bg-green-500/20 text-green-400'}`}>
          <Check size={12} strokeWidth={3} />
        </div>
      )}
      <span className={`text-base font-medium ${disabled ? 'text-gray-600 line-through' : light ? 'text-white' : 'text-gray-300'}`}>{text}</span>
    </li>
  );
}

function ListItem({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-center gap-4 text-gray-300 font-medium">
      <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 border border-blue-500/30">
         <Check size={14} className="text-blue-400" strokeWidth={3} />
      </div>
      <span>{children}</span>
    </li>
  );
}