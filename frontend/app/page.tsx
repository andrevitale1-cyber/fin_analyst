"use client";
import React, { useState } from 'react';
// import Link from 'next/link'; // <--- Descomente no seu projeto Next.js e use Link no lugar de <a>
import { 
  BarChart3, UploadCloud, ArrowRight, 
  FileText, Layout, Database, Check, X, CheckCircle2,
  Maximize2 
} from "lucide-react";

export default function LandingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  return (
    <div className="min-h-screen bg-[#0A0D14] text-gray-100 font-sans selection:bg-blue-500/30 overflow-x-hidden">

      {/* --- NAVBAR --- */}
      <nav className="border-b border-white/10 bg-[#0A0D14]/80 backdrop-blur-xl sticky top-0 z-50">
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
        className="relative pt-32 pb-40 lg:pt-40 lg:pb-56 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('/Day and night concept sun moon tree – Royalty-Free Vector _ VectorStock.jfif')" }}
      >
        <div className="absolute inset-0 bg-black/40 z-0" />

        <div className="max-w-7xl mx-auto px-6 text-center relative z-10">
          
          
          <h1 className="text-6xl md:text-8xl lg:text-[6.5rem] font-extrabold text-white tracking-tight mb-8 leading-[1.05] drop-shadow-2xl">
            A Nova Era Da <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 drop-shadow-lg">Análise de Ativos.</span>
          </h1>
          
          <p className="text-xl md:text-3xl text-white mb-16 max-w-4xl mx-auto leading-relaxed font-medium drop-shadow-lg">
            Acelere a leitura de relatórios trimestrais. Deixe a IA estruturar os dados e gerar insights para apoiar sua decisão de investimento.
          </p>

          <div className="flex flex-col md:flex-row items-center justify-center gap-6">
            <a href="/dashboard" className="w-full md:w-auto bg-white text-gray-900 px-10 py-5 rounded-full font-bold text-lg hover:bg-gray-100 transition-transform hover:scale-105 flex items-center justify-center gap-2 shadow-2xl shadow-white/20">
              Criar Conta Grátis <ArrowRight size={20} />
            </a>
            <a href="#funcionalidades" className="w-full md:w-auto px-10 py-5 rounded-full font-bold text-lg text-white border border-white/30 hover:bg-white/10 transition-all backdrop-blur-md bg-black/20">
              Ver Funcionalidades
            </a>
          </div>
        </div>
      </section>

      {/* --- SECÇÃO: FUNCIONALIDADES --- */}
      <div id="funcionalidades" className="flex flex-col">
        
        {/* BLOCO 1: UPLOAD (Aumentado o distanciamento e altura) */}
        <section 
          className="py-32 lg:py-56 relative bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/fundo-upload.jpg')" }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/40 to-transparent z-0" />
          
          <div className="max-w-7xl mx-auto px-6 relative z-10">
            {/* O gap-0 e os cols forçam o distanciamento brutal estilo Robinhood */}
            <div className="grid lg:grid-cols-12 gap-16 lg:gap-0 items-center">
              
              {/* TEXTO: Ocupa apenas 4 colunas (mais estreito) e começa na coluna 2 */}
              <div className="lg:col-span-4 lg:col-start-2 order-2 lg:order-1">
                <div className="w-16 h-16 bg-blue-500/20 rounded-2xl flex items-center justify-center mb-10 border border-blue-400/30 backdrop-blur-sm shadow-xl">
                  <UploadCloud className="text-blue-400 w-8 h-8" />
                </div>
                <h2 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-8 tracking-tight drop-shadow-2xl">Upload Inteligente</h2>
                <p className="text-xl text-gray-100 leading-relaxed mb-10 font-medium drop-shadow-lg">
                  Simplifique sua rotina de análise. Basta arrastar o PDF do Release de Resultados (ITR ou DFP). Nossa IA vai gerar uma análise completa do resultado em segundos.
                </p>
                <ul className="space-y-6">
                  <ListItem>Suporte a PDFs de até 10MB</ListItem>
                  <ListItem>Extração automática de métricas</ListItem>
                  <ListItem>Identificação de trimestre e ano</ListItem>
                </ul>
              </div>
              
              

            </div>
          </div>
        </section>

        {/* BLOCO 2: ANÁLISE PROFUNDA (SCORE) */}
        <section 
          className="py-32 lg:py-56 relative bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/fundo-score.png')" }} 
        >
          <div className="absolute inset-0 bg-gradient-to-l from-black/80 via-black/40 to-transparent z-0" />

          <div className="max-w-7xl mx-auto px-6 relative z-10">
            <div className="grid lg:grid-cols-12 gap-16 lg:gap-0 items-center">
              
          

              {/* TEXTO DESLOCADO BEM PARA A DIREITA (Começa na 8, ocupa 4 colunas) */}
              <div className="lg:col-span-4 lg:col-start-8 order-1 lg:order-2">
                <div className="w-16 h-16 bg-green-500/20 rounded-2xl flex items-center justify-center mb-10 border border-green-400/30 backdrop-blur-sm shadow-xl">
                  <FileText className="text-green-400 w-8 h-8" />
                </div>
                <h2 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-8 tracking-tight drop-shadow-2xl">Score de IA</h2>
                <p className="text-xl text-gray-100 leading-relaxed mb-10 font-medium drop-shadow-lg">
                  O FinAnalyzer gera um Score de 0 a 5 para cada métrica fundamentalista, facilitando a identificação imediata de pontos fortes e de atenção na empresa.
                </p>
                <ul className="space-y-6">
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
          className="py-32 lg:py-56 relative bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/fundo-comparador.jpg')" }}
        >
          <div className="absolute inset-0 bg-black/40 z-0" />
          
          <div className="max-w-7xl mx-auto px-6 text-center relative z-10">
            <div className="max-w-3xl mx-auto mb-20">
              <div className="w-20 h-20 bg-purple-500/20 rounded-3xl flex items-center justify-center mb-10 border border-purple-400/30 mx-auto backdrop-blur-sm shadow-xl">
                <Layout className="text-purple-400 w-10 h-10" />
              </div>
              <h2 className="text-5xl md:text-7xl font-bold text-white mb-8 tracking-tight drop-shadow-2xl">Comparador de Ativos</h2>
              <p className="text-2xl text-gray-100 leading-relaxed font-medium drop-shadow-lg bg-black/20 p-6 rounded-2xl backdrop-blur-sm inline-block">
                Visualize e compare todos os Resultados que você analisou. Ordene por Nota de Receita, Rentabilidade, Dívida, Lucro e muito mais.
              </p>
            </div>

            <div className="max-w-5xl mx-auto relative group">
               <img 
                 src="/comparador.png" 
                 alt="Tabela Comparativa" 
                 className="w-full h-auto object-contain drop-shadow-[0_50px_80px_rgba(0,0,0,0.9)] transition-transform duration-700 hover:scale-[1.02]"
               />
               <p className="mt-10 text-base text-gray-200 font-medium drop-shadow-md bg-black/30 py-3 px-6 rounded-full inline-flex items-center gap-2 backdrop-blur-sm">
                 <Maximize2 size={16} /> Visualização otimizada para foco nos dados
               </p>
            </div>
          </div>
        </section>

        {/* BLOCO 4: HISTÓRICO */}
        <section 
          className="py-32 lg:py-56 relative bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/fundo-historico.jpg')" }}
        >
          <div className="absolute inset-0 bg-black/40 z-0" />

           <div className="max-w-7xl mx-auto px-6 text-center relative z-10">
              <div className="w-20 h-20 bg-yellow-500/20 rounded-3xl flex items-center justify-center mb-10 border border-yellow-400/30 mx-auto backdrop-blur-sm shadow-xl">
                <Database className="text-yellow-400 w-10 h-10" />
              </div>
              <h2 className="text-5xl md:text-7xl font-bold text-white mb-8 tracking-tight drop-shadow-2xl">Histórico Completo</h2>
              <p className="text-2xl text-gray-100 leading-relaxed max-w-3xl mx-auto mb-20 font-medium drop-shadow-lg bg-black/20 p-6 rounded-2xl backdrop-blur-sm inline-block">
                Todas as suas análises ficam salvas para sempre. Compare a evolução da empresa trimestre a trimestre.
              </p>
              
              
           </div>
        </section>

      </div>
      
      {/* --- SECÇÃO DE PLANOS --- */}
      <section 
        id="planos" 
        className="py-32 lg:py-48 relative bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('/fundo-planos.jpg')" }}
      >
        <div className="absolute inset-0 bg-black/70 z-0" />

        <div className="max-w-7xl mx-auto px-6 relative z-10">
          <div className="text-center mb-24">
            <h2 className="text-5xl md:text-7xl font-extrabold text-white mb-6 tracking-tight drop-shadow-2xl">
              Um único plano. <br className="hidden md:block"/>
              Invista melhor com o poder da IA.
            </h2>
            
            <div className="flex items-center justify-center gap-4 bg-black/30 inline-flex p-2 rounded-full border border-white/20 mt-10 backdrop-blur-md">
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
               <span className="bg-orange-500/80 text-white border border-orange-400 text-sm font-bold px-6 py-2.5 rounded-full uppercase tracking-wider shadow-xl drop-shadow-md">
                 2 MESES GRÁTIS
               </span>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-12 items-stretch max-w-5xl mx-auto">
            
            {/* CARD GRATUITO */}
            <div className="bg-[#11141D]/90 backdrop-blur-xl border border-white/10 rounded-[2.5rem] p-14 hover:border-white/30 transition-colors flex flex-col shadow-2xl">
              <h3 className="text-4xl font-bold text-white mb-2 drop-shadow-md">Gratuito</h3>
              <p className="text-gray-300 text-xl mb-12 font-medium">Para começar a analisar sem custo.</p>
              
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
              <h3 className="text-4xl font-bold text-white mb-2 drop-shadow-md">Premium</h3>
              <div className="flex items-end gap-2 mb-2">
                <span className="text-[5.5rem] leading-none font-extrabold text-white drop-shadow-lg">{billingCycle === 'monthly' ? 'R$ 29' : 'R$ 290'}</span>
                <span className="text-blue-100 mb-4 font-medium text-2xl drop-shadow-md">{billingCycle === 'monthly' ? '/mês' : '/ano'}</span>
              </div>
              <p className="text-blue-50 text-xl mb-12 font-medium drop-shadow-md">Desbloqueie todo o poder da IA.</p>
              
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

              <a href="/dashboard" className="block w-full text-center py-6 rounded-full bg-white text-blue-900 text-xl font-extrabold shadow-2xl hover:bg-gray-100 hover:scale-[1.02] transition-all mt-auto">
                Assinar Agora
              </a>
              <p className="text-center text-sm text-blue-200 mt-8 font-medium drop-shadow-md">Cancele quando quiser.</p>
            </div>
          </div>
        </div>
      </section>

      {/* --- FOOTER & DISCLAIMERS --- */}
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

// Subcomponentes
function Feature({ text, active = false, disabled = false, light = false }: any) {
  return (
    <li className="flex items-center gap-4">
      {disabled ? (
        <div className="p-1.5 rounded-full border border-gray-500 text-gray-400"><X size={14} /></div>
      ) : (
        <div className={`p-1.5 rounded-full ${light ? 'bg-white text-blue-600' : 'bg-green-500 text-white'}`}>
          <Check size={14} strokeWidth={3} />
        </div>
      )}
      <span className={`text-lg font-medium drop-shadow-md ${disabled ? 'text-gray-400 line-through' : light ? 'text-white' : 'text-gray-100'}`}>{text}</span>
    </li>
  );
}

function ListItem({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-center gap-4 text-white font-medium text-lg">
      <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0 border border-blue-400 shadow-lg">
         <Check size={16} className="text-white" strokeWidth={3} />
      </div>
      <span className="drop-shadow-lg">{children}</span>
    </li>
  );
}