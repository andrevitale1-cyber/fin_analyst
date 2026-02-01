"use client";
import React, { useState } from 'react';
import { 
  BarChart3, CloudUpload, ArrowRight, 
  FileText, LayoutTemplate, Database, Check, X, CircleCheck,
  Zap, ShieldCheck, TrendingUp, ChevronRight
} from "lucide-react";

export default function App() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  return (
    <div className="min-h-screen bg-[#0E1117] text-gray-100 font-sans selection:bg-blue-500/30 overflow-x-hidden">
      
      {/* --- NAVBAR --- */}
      <nav className="border-b border-gray-800/50 bg-[#0E1117]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3 group cursor-pointer">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/20 group-hover:scale-110 transition-transform">
              <BarChart3 className="text-white w-6 h-6" />
            </div>
            <span className="text-2xl font-bold tracking-tight text-white">
              FinAnalyzer <span className="text-blue-500">.AI</span>
            </span>
          </div>

          <div className="hidden lg:flex items-center gap-8">
            <a href="#funcionalidades" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Funcionalidades</a>
            <a href="#planos" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Preços</a>
            <a href="/login" className="text-sm font-medium text-gray-400 hover:text-white transition-colors border-l border-gray-800 pl-8">Entrar</a>
            <a href="/register" className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2.5 rounded-lg font-bold text-sm transition-all shadow-lg shadow-blue-900/20 active:scale-95">
              Começar Grátis
            </a>
          </div>
          
          {/* Mobile Menu Icon (Visual only) */}
          <div className="lg:hidden w-8 h-8 flex flex-col justify-center gap-1.5 cursor-pointer">
            <div className="w-full h-0.5 bg-gray-300 rounded-full"></div>
            <div className="w-full h-0.5 bg-gray-300 rounded-full"></div>
            <div className="w-3/4 h-0.5 bg-gray-300 rounded-full"></div>
          </div>
        </div>
      </nav>

      {/* --- HERO SECTION --- */}
      <section className="relative pt-20 pb-32">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[600px] bg-blue-600/10 blur-[120px] rounded-full -z-10" />
        
        <div className="max-w-7xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold tracking-wider uppercase mb-8 animate-fade-in">
            <Zap size={14} className="fill-blue-400/20" />
            A inteligência que faltava no seu Home Broker
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold text-white tracking-tight mb-8 leading-[1.1]">
            Analise Ações em <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-500">
              Segundos, não Horas.
            </span>
          </h1>
          
          <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto leading-relaxed">
            Abandone a leitura manual de PDFs. Nossa IA interpreta balanços, extrai indicadores e entrega uma tese de investimento pronta.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20">
            <a href="/register" className="w-full sm:w-auto bg-white text-gray-900 px-8 py-4 rounded-xl font-bold text-lg hover:bg-gray-100 transition-all flex items-center justify-center gap-2 group">
              Criar Conta Grátis <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </a>
            <a href="#funcionalidades" className="w-full sm:w-auto px-8 py-4 rounded-xl font-bold text-lg text-gray-300 border border-gray-800 hover:border-gray-600 hover:text-white transition-all">
              Ver Como Funciona
            </a>
          </div>

          {/* Interface Preview */}
          <div className="max-w-5xl mx-auto relative group">
             <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur opacity-20 group-hover:opacity-40 transition-opacity"></div>
             <div className="relative bg-[#0d1117] rounded-2xl border border-gray-800 p-2 shadow-2xl shadow-blue-900/10">
                <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-800">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500/50"></div>
                  </div>
                  <div className="h-4 w-1/3 bg-gray-800 rounded-full mx-auto"></div>
                </div>
                <img src="/demo-result.png" alt="Dashboard FinAnalyzer" className="w-full rounded-b-xl opacity-90" />
             </div>
          </div>
        </div>
      </section>

      {/* --- SEÇÃO: FUNCIONALIDADES --- */}
      <section id="funcionalidades" className="py-24 space-y-40">
        
        {/* BLOCO 1: UPLOAD */}
        <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">
          <div className="relative">
            <div className="absolute -inset-10 bg-blue-600/10 blur-[80px] rounded-full -z-10" />
            <img src="/demo-upload.png" alt="Upload Inteligente" className="w-full rounded-2xl shadow-2xl border border-gray-800" />
          </div>
          <div className="space-y-6">
            <div className="w-14 h-14 bg-blue-600/20 rounded-2xl flex items-center justify-center border border-blue-500/30">
              <CloudUpload className="text-blue-400 w-7 h-7" />
            </div>
            <h2 className="text-4xl font-bold text-white leading-tight">Upload Inteligente</h2>
            <p className="text-lg text-gray-400 leading-relaxed">
              Esqueça configurações manuais. Basta arrastar o PDF do Release de Resultados (ITR ou DFP). Nossa IA identifica automaticamente a empresa, o trimestre e o ano.
            </p>
            <ul className="space-y-4">
              <ListItem>Sem limite de tamanho de arquivo</ListItem>
              <ListItem>Identificação automática de tickers</ListItem>
              <ListItem>Processamento em nuvem ultra-rápido</ListItem>
            </ul>
          </div>
        </div>

        {/* BLOCO 2: RESULTADO */}
        <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">
          <div className="space-y-6 lg:order-1 order-2">
            <div className="w-14 h-14 bg-green-600/20 rounded-2xl flex items-center justify-center border border-green-500/30">
              <FileText className="text-green-400 w-7 h-7" />
            </div>
            <h2 className="text-4xl font-bold text-white leading-tight">Análise Profunda</h2>
            <p className="text-lg text-gray-400 leading-relaxed">
              O FinAnalyzer gera um Score de 0 a 5 baseado em fundamentos sólidos e escreve uma tese de investimento completa focada no bottom-line.
            </p>
            <ul className="space-y-4">
              <ListItem>Score Fundamentalista (0 a 5)</ListItem>
              <ListItem>Indicadores visuais coloridos</ListItem>
              <ListItem>Tese descritiva gerada por IA</ListItem>
            </ul>
          </div>
          <div className="relative lg:order-2 order-1">
            <div className="absolute -inset-10 bg-green-600/10 blur-[80px] rounded-full -z-10" />
            <img src="/demo-result.png" alt="Análise de IA" className="w-full rounded-2xl shadow-2xl border border-gray-800" />
          </div>
        </div>

        {/* BLOCO 3: TABELA */}
        <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">
          <div className="relative">
            <div className="absolute -inset-10 bg-purple-600/10 blur-[80px] rounded-full -z-10" />
            <img src="/demo-table.png" alt="Comparador de Ativos" className="w-full rounded-2xl shadow-2xl border border-gray-800" />
          </div>
          <div className="space-y-6">
            <div className="w-14 h-14 bg-purple-600/20 rounded-2xl flex items-center justify-center border border-purple-500/30">
              <LayoutTemplate className="text-purple-400 w-7 h-7" />
            </div>
            <h2 className="text-4xl font-bold text-white leading-tight">Comparador de Ativos</h2>
            <p className="text-lg text-gray-400 leading-relaxed">
              Visualize todas as empresas que você analisou em uma única tabela interativa. Ordene por Nota, Receita ou Lucro.
            </p>
            <ul className="space-y-4">
              <ListItem>Colunas customizáveis</ListItem>
              <ListItem>Ordenação inteligente</ListItem>
              <ListItem>Comparação lado a lado</ListItem>
            </ul>
          </div>
        </div>

        {/* BLOCO 4: HISTÓRICO */}
        <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">
          <div className="space-y-6 lg:order-1 order-2">
            <div className="w-14 h-14 bg-yellow-600/20 rounded-2xl flex items-center justify-center border border-yellow-500/30">
              <Database className="text-yellow-400 w-7 h-7" />
            </div>
            <h2 className="text-4xl font-bold text-white leading-tight">Histórico Completo</h2>
            <p className="text-lg text-gray-400 leading-relaxed">
              Todas as suas análises ficam salvas para sempre. Compare a evolução da nota da empresa trimestre a trimestre.
            </p>
            <ul className="space-y-4">
              <ListItem>Backup automático na nuvem</ListItem>
              <ListItem>Acesso rápido a relatórios antigos</ListItem>
              <ListItem>Exclusão e gerenciamento fácil</ListItem>
            </ul>
          </div>
          <div className="relative lg:order-2 order-1">
            <div className="absolute -inset-10 bg-yellow-600/10 blur-[80px] rounded-full -z-10" />
            <img src="/demo-history.png" alt="Histórico" className="w-full rounded-2xl shadow-2xl border border-gray-800" />
          </div>
        </div>
      </section>

      {/* --- SEÇÃO DE PLANOS --- */}
      <section id="planos" className="py-32 relative bg-[#0A0C10]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-extrabold text-white mb-6">
              O plano certo para <br /> seu perfil de investidor.
            </h2>
            
            <div className="flex items-center justify-center gap-4 mt-10">
              <span className={`text-sm font-bold uppercase tracking-wider transition-colors ${billingCycle === 'monthly' ? 'text-white' : 'text-gray-500'}`}>Mensal</span>
              <button 
                onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
                className="w-14 h-7 bg-gray-800 rounded-full p-1 relative transition-colors hover:bg-gray-700"
              >
                <div className={`w-5 h-5 bg-blue-500 rounded-full transition-all duration-300 shadow-lg ${billingCycle === 'yearly' ? 'translate-x-7' : 'translate-x-0'}`} />
              </button>
              <span className={`text-sm font-bold uppercase tracking-wider transition-colors ${billingCycle === 'yearly' ? 'text-white' : 'text-gray-500'}`}>Anual</span>
            </div>
            
            <div className={`mt-4 h-8 transition-opacity duration-300 ${billingCycle === 'yearly' ? 'opacity-100' : 'opacity-0'}`}>
               <span className="bg-blue-500/20 text-blue-400 text-xs font-black px-4 py-1.5 rounded-full border border-blue-500/30">ECONOMIZE 2 MESES</span>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* CARD GRATUITO */}
            <div className="bg-[#0E1117] border border-gray-800 rounded-3xl p-8 hover:border-gray-700 transition-all flex flex-col group">
              <div className="mb-6">
                <h3 className="text-xl font-bold text-gray-400 mb-2">Plano Gratuito</h3>
                <div className="text-4xl font-extrabold text-white">R$ 0</div>
                <p className="text-gray-500 mt-2 text-sm">Ideal para começar sua jornada.</p>
              </div>
              
              <ul className="space-y-4 mb-10 flex-1">
                <PricingFeature text="5 Análises por semana" active />
                <PricingFeature text="Upload de arquivos ilimitado" active />
                <PricingFeature text="Acesso ao histórico simples" active />
                <PricingFeature text="Suporte por email" active />
                <PricingFeature text="Download do Relatório PDF" disabled />
                <PricingFeature text="Tabela Comparativa de Ativos" disabled />
              </ul>

              <a href="/register" className="w-full py-4 rounded-xl border border-gray-800 text-white font-bold hover:bg-gray-800 transition-all text-center">
                Começar Grátis
              </a>
            </div>

            {/* CARD PREMIUM */}
            <div className="bg-gradient-to-b from-[#161b22] to-[#0E1117] border-2 border-blue-600 rounded-3xl p-8 relative shadow-2xl shadow-blue-900/10 flex flex-col group">
              <div className="absolute -top-4 right-8 bg-blue-600 text-white text-[10px] font-black px-4 py-1.5 rounded-full uppercase tracking-tighter shadow-lg">
                Recomendado
              </div>
              
              <div className="mb-6">
                <h3 className="text-xl font-bold text-blue-400 mb-2">Premium</h3>
                <div className="flex items-end gap-1">
                  <span className="text-5xl font-extrabold text-white">
                    {billingCycle === 'monthly' ? 'R$ 29' : 'R$ 290'}
                  </span>
                  <span className="text-gray-500 mb-1.5 font-medium">{billingCycle === 'monthly' ? '/mês' : '/ano'}</span>
                </div>
                <p className="text-gray-400 mt-2 text-sm">Potencial máximo para suas análises.</p>
              </div>
              
              <ul className="space-y-4 mb-10 flex-1">
                <PricingFeature text="Análises de IA Ilimitadas" active />
                <PricingFeature text="Download do Relatório PDF Completo" active />
                <PricingFeature text="Tabela Comparativa Customizável" active />
                <PricingFeature text="Upload de arquivos ilimitado" active />
                <PricingFeature text="Histórico de dados ilimitado" active />
                <PricingFeature text="Prioridade máxima na fila" active />
              </ul>

              <a href="/register" className="w-full py-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold shadow-lg shadow-blue-900/20 transition-all active:scale-95 text-center">
                Assinar Agora
              </a>
              <p className="text-center text-[10px] text-gray-500 mt-4 uppercase font-bold tracking-widest">Cancele quando quiser</p>
            </div>
          </div>
        </div>
      </section>

      {/* --- FOOTER & DISCLAIMERS --- */}
      <footer className="border-t border-gray-800 bg-[#0E1117] pt-20 pb-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-12 mb-16">
            <div className="col-span-2">
              <div className="flex items-center gap-3 mb-6">
                <BarChart3 className="text-blue-500 w-8 h-8" />
                <span className="text-2xl font-bold text-white">FinAnalyzer.AI</span>
              </div>
              <p className="text-gray-400 max-w-sm leading-relaxed mb-6">
                A ferramenta definitiva para investidores que buscam converter dados em lucro através da Inteligência Artificial.
              </p>
              <div className="flex gap-4">
                <SocialIcon />
                <SocialIcon />
                <SocialIcon />
              </div>
            </div>
            
            <div>
              <h4 className="text-white font-bold mb-6">Produto</h4>
              <ul className="space-y-4 text-sm text-gray-500">
                <li><a href="#" className="hover:text-blue-400 transition-colors">Funcionalidades</a></li>
                <li><a href="#" className="hover:text-blue-400 transition-colors">Preços</a></li>
                <li><a href="#" className="hover:text-blue-400 transition-colors">Changelog</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-white font-bold mb-6">Suporte</h4>
              <ul className="space-y-4 text-sm text-gray-500">
                <li><a href="#" className="hover:text-blue-400 transition-colors">Contato</a></li>
                <li><a href="#" className="hover:text-blue-400 transition-colors">Privacidade</a></li>
                <li><a href="#" className="hover:text-blue-400 transition-colors">Termos</a></li>
              </ul>
            </div>
          </div>

          <div className="pt-10 border-t border-gray-800 text-xs text-gray-500">
            <div className="bg-gray-800/20 p-6 rounded-2xl border border-gray-800/50 mb-8">
              <p className="text-justify leading-relaxed">
                <strong className="text-gray-300">AVISO IMPORTANTE SOBRE IA:</strong> A análise apresentada nesta plataforma é gerada por algoritmos de Inteligência Artificial e serve apenas como uma <strong className="text-gray-300">ferramenta auxiliar de suporte</strong>. Ela <strong className="text-gray-300">não substitui a análise humana</strong>, nem constitui recomendação de compra ou venda de ativos. O FinAnalyzer.AI não se responsabiliza pela precisão, integridade ou atualização dos dados, nem por quaisquer decisões de investimento ou prejuízos financeiros decorrentes do uso destas informações. Rentabilidade passada não representa garantia de rentabilidade futura.
              </p>
            </div>
            <p className="text-center font-medium">© 2026 FinAnalyzer Inc. Todos os direitos reservados.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Subcomponentes
function PricingFeature({ text, active = false, disabled = false }: any) {
  return (
    <li className="flex items-center gap-3">
      {disabled ? (
        <X size={14} className="text-gray-600" />
      ) : (
        <Check size={14} className="text-blue-500" />
      )}
      <span className={`text-sm ${disabled ? 'text-gray-600 line-through' : 'text-gray-300'}`}>{text}</span>
    </li>
  );
}

function ListItem({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-center gap-3 text-gray-300">
      <div className="w-5 h-5 rounded-full bg-blue-500/10 flex items-center justify-center">
        <CircleCheck size={16} className="text-blue-500" />
      </div>
      <span className="text-sm font-medium">{children}</span>
    </li>
  );
}

function SocialIcon() {
  return (
    <div className="w-10 h-10 rounded-full bg-gray-800/50 border border-gray-800 flex items-center justify-center hover:bg-blue-600 hover:border-blue-500 transition-all cursor-pointer">
      <div className="w-4 h-4 bg-gray-400 rounded-sm"></div>
    </div>
  );
}