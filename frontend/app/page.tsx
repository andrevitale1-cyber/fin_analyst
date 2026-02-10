"use client";
import React, { useState } from 'react';
// import Link from 'next/link'; // <--- Descomente no seu projeto Next.js e use Link
import { 
  BarChart3, UploadCloud, ArrowRight, 
  FileText, Layout, Database, Check, X, CheckCircle2,
  Maximize2, TrendingUp, Search, Filter, MoreHorizontal
} from "lucide-react";

// --- COMPONENTE: MOLDURA DE NAVEGADOR PREMIUM ---
const BrowserMockup = ({ children, className = "" }: { children: React.ReactNode, className?: string }) => {
  return (
    <div className={`relative rounded-2xl border border-gray-800 bg-[#0d1117] shadow-2xl shadow-black/80 overflow-hidden group ${className}`}>
      {/* Header do Navegador */}
      <div className="h-10 bg-[#161b22] border-b border-gray-800 flex items-center px-4 gap-3">
        <div className="flex gap-2">
            <div className="w-3 h-3 rounded-full bg-[#FF5F56] border border-[#E0443E]" />
            <div className="w-3 h-3 rounded-full bg-[#FFBD2E] border border-[#DEA123]" />
            <div className="w-3 h-3 rounded-full bg-[#27C93F] border border-[#1AAB29]" />
        </div>
        {/* Barra de URL Fake */}
        <div className="flex-1 mx-4 h-6 bg-[#0d1117] border border-gray-700/50 rounded-md flex items-center px-3 justify-center opacity-60">
            <div className="w-3 h-3 bg-gray-600 rounded-full mr-2 opacity-50" />
            <div className="w-32 h-2 bg-gray-600 rounded-full opacity-30" />
        </div>
      </div>
      
      {/* Conteúdo */}
      <div className="relative w-full bg-[#0d1117]">
         {children}
      </div>
    </div>
  );
};

// --- COMPONENTE: CARD FLUTUANTE (Para o efeito 3D estilo Fundamentei) ---
const FloatingCard = ({ icon, label, value, color, className }: any) => (
  <div className={`absolute p-4 rounded-xl bg-[#161b22]/90 backdrop-blur-md border border-gray-700 shadow-2xl flex items-center gap-3 animate-in fade-in zoom-in duration-700 ${className}`}>
    <div className={`p-2 rounded-lg ${color} bg-opacity-20`}>
      {icon}
    </div>
    <div>
      <p className="text-xs text-gray-400 font-medium uppercase">{label}</p>
      <p className="text-lg font-bold text-white">{value}</p>
    </div>
  </div>
);

export default function LandingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  return (
    <div className="min-h-screen bg-[#0E1117] text-gray-100 font-sans selection:bg-blue-500/30 overflow-x-hidden">
      
      {/* --- NAVBAR --- */}
      <nav className="border-b border-gray-800 bg-[#0E1117]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/20">
              <BarChart3 className="text-white w-6 h-6" />
            </div>
            <span className="text-2xl font-bold tracking-tight text-white">
              FinAnalyzer <span className="text-blue-500">.AI</span>
            </span>
          </div>

          <div className="flex items-center gap-4">
            <a href="#funcionalidades" className="hidden md:block text-gray-300 hover:text-white font-medium transition-colors">Funcionalidades</a>
            <a href="#planos" className="hidden md:block text-gray-300 hover:text-white font-medium transition-colors">Preços</a>
            <a href="/dashboard" className="hidden md:block text-gray-300 hover:text-white font-medium transition-colors">Entrar</a>
            <a href="/dashboard" className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2.5 rounded-lg font-bold transition-all shadow-lg shadow-blue-900/20 hover:scale-105">
              Começar Grátis
            </a>
          </div>
        </div>
      </nav>

      {/* --- HERO SECTION ESTILO "FUNDAMENTEI" --- */}
      <section className="relative pt-20 pb-40 overflow-visible">
        
        {/* Fundo de Luz (Glow) Atrás da Hero */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[800px] bg-gradient-to-b from-blue-900/10 via-[#0E1117] to-[#0E1117] -z-10 pointer-events-none" />
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-blue-600/10 blur-[120px] rounded-full -z-10" />

        <div className="max-w-7xl mx-auto px-6 text-center">
          
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-900/20 border border-blue-500/30 text-blue-400 text-xs font-bold uppercase tracking-wider mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
             <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" /> Plataforma de Inteligência Artificial
          </div>

          {/* Título Principal */}
          <h1 className="text-5xl md:text-7xl font-extrabold text-white tracking-tight mb-8 leading-[1.1]">
            Análise de Ações e <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-blue-400 animate-gradient">Fundos Imobiliários</span> com IA.
          </h1>
          
          <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto leading-relaxed">
            O site de análise fundamentalista mais rápido do Brasil. 
            Carregue PDFs, visualize dados históricos e tome decisões baseadas em dados estruturados.
          </p>

          {/* Botões CTA */}
          <div className="flex flex-col md:flex-row items-center justify-center gap-4 mb-20">
            <a href="/dashboard" className="w-full md:w-auto bg-blue-600 hover:bg-blue-500 text-white px-8 py-4 rounded-xl font-bold text-lg transition-all shadow-xl shadow-blue-900/20 hover:scale-105 flex items-center justify-center gap-2">
              Analisar Agora <ArrowRight size={20} />
            </a>
            <a href="#funcionalidades" className="w-full md:w-auto px-8 py-4 rounded-xl font-bold text-lg text-gray-300 border border-gray-700 hover:border-gray-500 hover:text-white transition-all bg-[#161b22]/50">
              Ver Demonstração
            </a>
          </div>

          {/* --- A GRANDE IMAGEM "FLUTUANTE" (HERO IMAGE) --- */}
          <div className="relative mx-auto max-w-6xl group perspective-1000">
             
             {/* Efeito de brilho atrás da imagem */}
             <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-1000"></div>

             <BrowserMockup className="transform transition-transform duration-700 hover:scale-[1.01]">
                {/* Imagem Principal da Tabela */}
                <img 
                  src="/image_03af1d.png" 
                  alt="Plataforma FinAnalyzer" 
                  className="w-full h-auto object-cover opacity-90 hover:opacity-100 transition-opacity"
                />
             </BrowserMockup>

             {/* ELEMENTOS FLUTUANTES (DECORAÇÃO 3D) */}
             
             {/* Floating Card 1: Esquerda Superior */}
             <FloatingCard 
               className="-top-12 -left-6 md:-left-12 hidden md:flex delay-100 animate-bounce-slow"
               icon={<TrendingUp className="text-green-400" size={24} />}
               color="text-green-400"
               label="Rentabilidade"
               value="ROE 24%"
             />

             {/* Floating Card 2: Direita Inferior */}
             <FloatingCard 
               className="-bottom-8 -right-4 md:-right-8 hidden md:flex delay-300 animate-bounce-slow"
               icon={<CheckCircle2 className="text-blue-400" size={24} />}
               color="text-blue-400"
               label="Score IA"
               value="4.8 / 5.0"
             />

             {/* Barra de Ferramentas Fake (Centro Inferior) */}
             <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 bg-[#161b22] border border-gray-700 rounded-full py-3 px-6 shadow-2xl hidden md:flex items-center gap-6 animate-in slide-in-from-bottom-8 fade-in duration-1000">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-300 cursor-pointer hover:text-white transition-colors">
                   <Filter size={16} /> Filtros
                </div>
                <div className="w-px h-4 bg-gray-700"></div>
                <div className="flex items-center gap-2 text-sm font-medium text-gray-300 cursor-pointer hover:text-white transition-colors">
                   <Search size={16} /> Comparar
                </div>
                <div className="w-px h-4 bg-gray-700"></div>
                 <div className="flex items-center gap-2 text-sm font-medium text-blue-400 cursor-pointer hover:text-blue-300 transition-colors">
                   <UploadCloud size={16} /> Novo Upload
                </div>
             </div>

          </div>

        </div>
      </section>

      {/* --- FUNCIONALIDADES DETALHADAS --- */}
      <div id="funcionalidades" className="bg-[#0E1117] py-24 relative">
        <div className="max-w-7xl mx-auto px-6">
           <div className="grid md:grid-cols-3 gap-8">
              {/* Card 1 */}
              <div className="bg-[#161b22] border border-gray-800 p-8 rounded-3xl hover:border-blue-500/30 transition-all group">
                 <div className="w-12 h-12 bg-blue-900/30 rounded-xl flex items-center justify-center mb-6 text-blue-400 group-hover:scale-110 transition-transform">
                    <UploadCloud size={24} />
                 </div>
                 <h3 className="text-xl font-bold text-white mb-3">Upload de PDF</h3>
                 <p className="text-gray-400 leading-relaxed">Arraste seus relatórios trimestrais (ITR/DFP). A IA extrai os dados automaticamente em segundos.</p>
              </div>

              {/* Card 2 */}
              <div className="bg-[#161b22] border border-gray-800 p-8 rounded-3xl hover:border-purple-500/30 transition-all group">
                 <div className="w-12 h-12 bg-purple-900/30 rounded-xl flex items-center justify-center mb-6 text-purple-400 group-hover:scale-110 transition-transform">
                    <FileText size={24} />
                 </div>
                 <h3 className="text-xl font-bold text-white mb-3">Análise Qualitativa</h3>
                 <p className="text-gray-400 leading-relaxed">Nossa IA lê o texto do management e gera teses de investimento resumidas e diretas.</p>
              </div>

              {/* Card 3 */}
              <div className="bg-[#161b22] border border-gray-800 p-8 rounded-3xl hover:border-green-500/30 transition-all group">
                 <div className="w-12 h-12 bg-green-900/30 rounded-xl flex items-center justify-center mb-6 text-green-400 group-hover:scale-110 transition-transform">
                    <Layout size={24} />
                 </div>
                 <h3 className="text-xl font-bold text-white mb-3">Tabela Comparativa</h3>
                 <p className="text-gray-400 leading-relaxed">Visualize todos os seus ativos em uma única tabela interativa. Ordene por valuation, dívida e margens.</p>
              </div>
           </div>
        </div>
      </div>

      {/* --- SEÇÃO DE UPLOAD PREVIEW --- */}
      <section className="py-24 border-t border-gray-800 bg-[#0d1117]/50">
          <div className="max-w-7xl mx-auto px-6 grid md:grid-cols-2 gap-16 items-center">
             <div>
                <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">Simples como deve ser.</h2>
                <p className="text-xl text-gray-400 mb-8 leading-relaxed">
                   Esqueça planilhas complexas. A interface do FinAnalyzer foi desenhada para investidores que valorizam seu tempo.
                </p>
                <ul className="space-y-4">
                   <ListItem>Uploads rápidos e seguros</ListItem>
                   <ListItem>Identificação automática de tickers</ListItem>
                   <ListItem>Histórico salvo na nuvem</ListItem>
                </ul>
             </div>
             <BrowserMockup className="transform rotate-2 hover:rotate-0 transition-duration-500 shadow-2xl">
                <img src="/image_456e01.png" className="w-full" alt="Upload Interface" />
             </BrowserMockup>
          </div>
      </section>

      {/* --- SEÇÃO DE PLANOS --- */}
      <section id="planos" className="py-24 relative bg-[#0E1117] border-t border-gray-800">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
              Preço Transparente.
            </h2>
            
            <div className="flex items-center justify-center gap-4 mt-8">
              <span className={`text-base font-bold cursor-pointer transition-colors ${billingCycle === 'monthly' ? 'text-white' : 'text-gray-500'}`} onClick={() => setBillingCycle('monthly')}>Mensal</span>
              <button 
                onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
                className="w-16 h-8 bg-gray-800 rounded-full p-1 relative transition-colors hover:bg-gray-700"
              >
                <div className={`w-6 h-6 bg-blue-500 rounded-full transition-transform duration-300 shadow-md ${billingCycle === 'yearly' ? 'translate-x-8' : 'translate-x-0'}`} />
              </button>
              <span className={`text-base font-bold cursor-pointer transition-colors ${billingCycle === 'yearly' ? 'text-white' : 'text-gray-500'}`} onClick={() => setBillingCycle('yearly')}>Anual</span>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8 items-start max-w-4xl mx-auto">
            {/* CARD GRATUITO */}
            <div className="bg-[#161b22] border border-gray-800 rounded-3xl p-8 hover:border-gray-600 transition-all h-full flex flex-col">
              <h3 className="text-3xl font-bold text-white mb-2">Gratuito</h3>
              <p className="text-gray-400 text-base mb-8">Para começar a analisar sem custo.</p>
              
              <ul className="space-y-4 mb-8 flex-1">
                <Feature text="5 Análises por semana" active />
                <Feature text="Relatório Resumido na Tela" active />
                <Feature text="Acesso ao histórico simples" active />
                <Feature text="Suporte por email" active />
                <Feature text="Upload de arquivos ilimitado" disabled />
                <Feature text="Tabela Comparativa de Ativos" disabled />
              </ul>

              <a href="/dashboard" className="block w-full text-center py-4 rounded-xl border border-gray-600 text-white font-bold hover:bg-gray-700 hover:border-gray-500 transition-all mt-auto">
                Criar conta grátis
              </a>
            </div>

            {/* CARD PREMIUM */}
            <div className="bg-[#0f131a] border border-blue-500 rounded-3xl p-8 relative shadow-2xl shadow-blue-900/10 transform hover:-translate-y-1 transition-all duration-300 h-full flex flex-col">
              {billingCycle === 'yearly' && (
                <div className="absolute top-4 right-4 bg-orange-100 text-orange-800 text-xs font-bold px-3 py-1 rounded-md uppercase tracking-wider">
                  2 Meses Grátis no Anual
                </div>
              )}
              <h3 className="text-2xl font-bold text-blue-400 mb-2">Premium</h3>
              <div className="flex items-end gap-1 mb-2">
                <span className="text-5xl font-bold text-white">{billingCycle === 'monthly' ? 'R$ 29' : 'R$ 290'}</span>
                <span className="text-gray-500 mb-1 text-lg">{billingCycle === 'monthly' ? '/mês' : '/ano'}</span>
              </div>
              <p className="text-gray-400 text-sm mb-8">Desbloqueie todo o poder da IA.</p>
              
              <ul className="space-y-4 mb-8 flex-1">
                <Feature text="Análises de IA Ilimitadas" active />
                <Feature text="Relatório Resumido na Tela" active />
                <Feature text="Acesso ao Histórico Ilimitado" active />
                <Feature text="Suporte Prioritário" active />
                <Feature text="Upload de arquivos ilimitado" active />
                <Feature text="Tabela Comparativa de Ativos" active />
              </ul>

              <a href="/dashboard" className="block w-full text-center py-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold shadow-lg shadow-blue-900/20 transition-all mt-auto">
                Assinar Agora
              </a>
              <p className="text-center text-xs text-gray-500 mt-4">Cancele quando quiser.</p>
            </div>
          </div>
        </div>
      </section>

      {/* --- FOOTER --- */}
      <footer className="border-t border-gray-800 bg-[#0E1117] pt-16 pb-8">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6 mb-12">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gray-800 rounded-lg flex items-center justify-center">
                <BarChart3 className="text-gray-400 w-5 h-5" />
              </div>
              <span className="text-lg font-bold text-gray-300">FinAnalyzer.AI</span>
            </div>
            <div className="flex gap-6">
              <a href="/terms" className="text-gray-500 hover:text-white transition-colors">Termos</a>
              <a href="/privacy" className="text-gray-500 hover:text-white transition-colors">Privacidade</a>
            </div>
          </div>
          <p className="text-center text-xs text-gray-500">© 2026 FinAnalyzer Inc.</p>
        </div>
      </footer>
    </div>
  );
}

// Subcomponentes
function Feature({ text, active = false, disabled = false }: any) {
  return (
    <li className="flex items-center gap-3">
      {disabled ? (
        <div className="p-0.5 rounded-full border border-gray-600 text-gray-500"><X size={12} /></div>
      ) : (
        <div className="p-0.5 rounded-full bg-green-500/10 text-green-500 border border-green-500/30">
          <Check size={12} />
        </div>
      )}
      <span className={`text-base ${disabled ? 'text-gray-500 line-through' : 'text-gray-300'}`}>{text}</span>
    </li>
  );
}

function ListItem({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-center gap-3 text-gray-300">
      <CheckCircle2 size={18} className="text-blue-500" />
      <span>{children}</span>
    </li>
  );
}