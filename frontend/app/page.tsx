"use client";

"use client";
import React, { useState, useRef } from 'react';
import { motion, useInView } from "framer-motion";
import { 
  BarChart3, UploadCloud, ArrowRight, 
  FileText, Layout, Database, Check, X
} from "lucide-react";

export default function LandingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  return (
    <div className="min-h-screen bg-[#0A0D14] text-gray-100 font-sans antialiased selection:bg-blue-500/30 overflow-x-hidden">

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
        className="relative min-h-[90vh] lg:min-h-[140vh] w-full flex flex-col items-center justify-start pt-24 lg:pt-32 bg-cover bg-bottom bg-no-repeat"
        style={{ backgroundImage: "url('/hero2.png')" }}
      >
        <div className="max-w-5xl mx-auto px-6 text-center relative z-10 flex flex-col items-center">
          
          {/* Título Gigante com espaçamento apertado e fonte SERIF (Robinhood Style) */}
          <h1 className="text-4xl md:text-4xl lg:text-[6rem] font-serif font-bold text-white tracking-tighter mb-8 leading-none">
            A Nova Era Da <br />
            <span className="text-white tracking-tighter mb-8 leading-none">Análise de Ativos.</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-gray-300 mb-12 max-w-2xl mx-auto leading-relaxed font-medium tracking-tight">
            Acelere a leitura de relatórios trimestrais. Deixe a IA estruturar os dados e gerar insights para apoiar sua decisão de investimento.
          </p>

          <div className="flex flex-col md:flex-row items-center justify-center gap-6 w-full md:w-auto">
            {/* Botão Neon Gringo */}
            <a href="/dashboard" className="w-full md:w-auto bg-[#D2FF00] text-black px-10 py-4 rounded-full font-bold text-lg hover:bg-[#bce600] transition-transform hover:scale-105 flex items-center justify-center gap-2 shadow-[0_0_40px_-10px_rgba(210,255,0,0.5)]">
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
        
        {/* BLOCO 1: UPLOAD (TEXTO NA ESQUERDA) */}
        <section 
          className="py-32 lg:py-56 relative bg-cover bg-center bg-no-repeat overflow-hidden"
          style={{ backgroundImage: "url('/upload.png')" }}
        >
          <div className="max-w-7xl mx-auto px-6 relative z-10">
            <div className="grid lg:grid-cols-12 gap-16 items-center">
              
              {/* Texto ancorado na Esquerda (col-start-1) */}
              <div className="lg:col-span-5 lg:col-start-1">
                <div className="w-16 h-16 bg-blue-500/20 rounded-2xl flex items-center justify-center mb-8 border border-blue-400/30">
                  <UploadCloud className="text-blue-400 w-8 h-8" />
                </div>
                <h2 className="text-5xl md:text-6xl lg:text-[5.5rem] font-serif font-bold text-white mb-8 tracking-tighter leading-[1.05]">
                  Upload <br/>Inteligente
                </h2>
                <p className="text-xl text-gray-300 leading-relaxed mb-10 font-medium tracking-tight">
                  Simplifique sua rotina de análise. Basta arrastar o PDF do Release de Resultados (ITR ou DFP). Nossa IA vai gerar uma análise completa do resultado em segundos.
                </p>
                <ul className="space-y-6">
                  <ListItem>Suporte a PDFs de até 10MB</ListItem>
                  <ListItem>Extração automática de métricas</ListItem>
                  <ListItem>Identificação de trimestre e ano</ListItem>
                </ul>
              </div>

              {/* Imagem do Telemóvel com Animação de Entrada */}
            <div className="lg:col-span-6 lg:col-start-7 relative flex justify-end">
              {/* Glow atrás do telemóvel */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-blue-600/20 blur-[100px] rounded-full pointer-events-none"></div>
          <PhoneImage />
          </div>
            </div>
          </div>
        </section>

        {/* BLOCO 2: SCORE DE IA — texto em cima, vídeo flutuante embaixo, tabela.png como background */}
        <section className="pt-16 lg:pt-20 pb-16 lg:pb-24 relative bg-cover bg-center bg-no-repeat" style={{ backgroundImage: "url('/tabela.png')" }}>
          {/* Overlay escuro para legibilidade */}
          <div className="absolute inset-0 bg-[#0A0D14]/85 pointer-events-none"></div>
          {/* Glow de fundo */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-green-600/10 blur-[120px] rounded-full pointer-events-none"></div>

          <div className="max-w-4xl mx-auto px-6 relative z-10">

            {/* Texto centralizado em cima */}
            <div className="flex flex-col items-center text-center mb-6">
              <div className="w-14 h-14 bg-green-500/20 rounded-2xl flex items-center justify-center mb-4 border border-green-400/30">
                <FileText className="text-green-400 w-7 h-7" />
              </div>
              <h2 className="text-4xl md:text-5xl lg:text-[4rem] font-serif font-bold text-white mb-4 tracking-tighter leading-[1.05]">
                Score de IA
              </h2>
              <p className="text-lg text-gray-300 leading-relaxed mb-6 font-medium tracking-tight max-w-xl">
                O FinAnalyzer gera um Score de 0 a 5 para cada métrica fundamentalista, facilitando a identificação imediata de pontos fortes e de atenção na empresa.
              </p>
              <ul className="flex flex-wrap justify-center gap-6">
                <ListItem>Score de Receita e Lucro</ListItem>
                <ListItem>Análise de Endividamento</ListItem>
                <ListItem>Resumo textual da Tese</ListItem>
              </ul>
            </div>

            {/* Vídeo flutuante */}
            <div className="relative w-full">
              <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 w-3/4 h-24 bg-green-500/20 blur-[60px] rounded-full pointer-events-none"></div>
              <video
                autoPlay
                loop
                muted
                playsInline
                className="w-full rounded-2xl shadow-[0_0_80px_-10px_rgba(0,0,0,0.6)]"
                style={{ display: 'block', border: '1px solid rgba(255,255,255,0.08)' }}
              >
                <source src="/score-demo.mp4" type="video/mp4" />
              </video>
              <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#0A0D14] to-transparent pointer-events-none"></div>
            </div>

          </div>
        </section>

        {/* BLOCO 3: COMPARADOR DE ATIVOS (TEXTO NA ESQUERDA) */}
        <section 
          className="py-32 lg:py-56 relative bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/Design sem nome (2).png')" }}
        >
          <div className="max-w-7xl mx-auto px-6 relative z-10">
             <div className="grid lg:grid-cols-12 gap-0 items-start">
              
               {/* Texto ancorado na Esquerda */}
               <div className="lg:col-span-4 lg:col-start-1">
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

        {/* BLOCO 4: HISTÓRICO (TEXTO NA DIREITA) */}
        <section 
          className="py-32 lg:py-56 relative bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/fundo-historico.jpg')" }}
        >
           <div className="max-w-7xl mx-auto px-6 relative z-10">
              <div className="grid lg:grid-cols-12 gap-0 items-start">
                
                {/* Texto ancorado na Direita (col-start-8) */}
                <div className="lg:col-span-5 lg:col-start-8">
                  <div className="w-16 h-16 bg-yellow-500/20 rounded-2xl flex items-center justify-center mb-8 border border-yellow-400/30">
                    <Database className="text-yellow-400 w-8 h-8" />
                  </div>
                  <h2 className="text-5xl md:text-6xl lg:text-[5.5rem] font-serif font-bold text-white mb-8 tracking-tighter leading-[1.05]">
                    Histórico <br/>Completo
                  </h2>
                  <p className="text-xl text-gray-300 leading-relaxed font-medium tracking-tight">
                    Todas as suas análises ficam salvas para sempre. Compare a evolução da empresa trimestre a trimestre.
                  </p>
                </div>

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
            <h2 className="text-6xl md:text-7xl lg:text-[6.5rem] font-serif font-bold text-white mb-8 tracking-tighter leading-[1.05]">
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
               <span className="bg-[#D2FF00]/90 text-black border border-[#D2FF00] text-sm font-bold px-6 py-2.5 rounded-full uppercase tracking-wider shadow-xl">
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

              <a href="/dashboard" className="block w-full text-center py-6 rounded-full bg-[#D2FF00] text-black text-xl font-extrabold shadow-2xl hover:bg-[#bce600] hover:scale-[1.02] transition-all mt-auto">
                Assinar Agora
              </a>
              <p className="text-center text-sm text-blue-200 mt-8 font-medium">Cancele quando quiser.</p>
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

function PhoneImage() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.img
      ref={ref}
      src="/celular.png"
      alt="App no Telemóvel"
      className="w-full max-w-sm h-auto rounded-[3rem] shadow-[0_30px_60px_-15px_rgba(0,0,0,0.8)]"
      initial={{ opacity: 0, y: 80 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.9, ease: "easeOut", delay: 0.2 }}
    />
  );
}

function Feature({ text, active = false, disabled = false, light = false }: any) {
  return (
    <li className="flex items-center gap-4">
      {disabled ? (
        <div className="p-1.5 rounded-full border border-gray-600 text-gray-500"><X size={14} /></div>
      ) : (
        <div className={`p-1.5 rounded-full ${light ? 'bg-white text-blue-600' : 'bg-blue-600 text-white'}`}>
          <Check size={14} strokeWidth={3} />
        </div>
      )}
      <span className={`text-lg font-medium tracking-tight ${disabled ? 'text-gray-500 line-through' : light ? 'text-white' : 'text-gray-100'}`}>{text}</span>
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