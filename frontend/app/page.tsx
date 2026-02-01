"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import { 
  BarChart3, UploadCloud, ArrowRight, 
  FileText, Layout, Database, Check, X, CheckCircle2, Play, 
  Zap, ShieldCheck, MousePointerClick
} from "lucide-react";

export default function LandingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  return (
    <div className="min-h-screen bg-[#0E1117] text-gray-100 font-sans selection:bg-blue-500/30">
      
      {/* =====================================================================================
          NAVBAR
      ===================================================================================== */}
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

          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-300">
            <a href="#funcionalidades" className="hover:text-white transition-colors">Funcionalidades</a>
            <a href="#pricing" className="hover:text-white transition-colors">Preços</a>
            <a href="#faq" className="hover:text-white transition-colors">FAQ</a>
          </div>

          <div className="flex items-center gap-4">
            <Link href="/login" className="text-sm font-medium text-gray-300 hover:text-white transition-colors hidden sm:block">
              Entrar
            </Link>
            <Link 
              href="/register" 
              className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-all shadow-lg shadow-blue-900/20 flex items-center gap-2 group"
            >
              Começar Agora <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </nav>

      {/* =====================================================================================
          HERO SECTION (CAPA - Inspirado na modernidade)
      ===================================================================================== */}
      <section className="relative pt-20 pb-32 overflow-hidden">
        {/* Efeitos de Fundo (Blobs) */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-blue-600/20 blur-[120px] rounded-full -z-10 pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 flex flex-col items-center text-center">
          
          {/* Badge de Novidade */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-900/20 border border-blue-500/30 text-blue-400 text-sm font-medium mb-8 hover:bg-blue-900/30 transition-colors cursor-default">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
            </span>
            Nova Versão 2.0 com IA Generativa
          </div>

          {/* Título Principal */}
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-8 tracking-tight max-w-5xl leading-[1.1]">
            Análise de Ações profissional <br className="hidden md:block"/> com 
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400 ml-2">
              Inteligência Artificial
            </span>
          </h1>
          
          <p className="text-xl text-gray-400 mb-10 max-w-2xl leading-relaxed">
            Automatize a leitura de relatórios trimestrais (ITR/DFP). Receba teses de investimento, scores fundamentalistas e compare empresas em segundos.
          </p>

          {/* Botões de Ação */}
          <div className="flex flex-col sm:flex-row gap-4 w-full justify-center mb-16">
            <Link href="/register" className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-4 rounded-xl text-lg font-semibold transition-all shadow-xl shadow-blue-900/20 hover:shadow-blue-900/40 hover:-translate-y-1 flex items-center justify-center gap-2">
              Testar Grátis <ArrowRight size={20} />
            </Link>
            <a href="#funcionalidades" className="bg-[#1C2128] hover:bg-[#2D333B] text-white px-8 py-4 rounded-xl text-lg font-semibold transition-all border border-gray-700 hover:border-gray-500 flex items-center justify-center gap-2">
              <Play size={20} className="fill-white" /> Ver Demo
            </a>
          </div>

          {/* Imagem do Dashboard (Principal) */}
          <div className="relative w-full max-w-6xl group perspective-1000">
             {/* Efeito Glow atrás */}
             <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-1000"></div>
             
             {/* Note: Usando uma div placeholder cinza caso a imagem não exista no seu repo ainda, mas a tag img está pronta */}
             <div className="relative rounded-2xl border border-gray-700/50 shadow-2xl bg-[#0E1117] overflow-hidden">
                <img 
                  src="/dashboard-preview.png" 
                  alt="Dashboard Preview" 
                  className="w-full h-auto transform transition-transform duration-500 hover:scale-[1.01]"
                  onError={(e) => {
                    // Fallback visual se a imagem não existir
                    e.currentTarget.style.display = 'none';
                    e.currentTarget.parentElement!.innerHTML += '<div class="h-[600px] w-full flex items-center justify-center text-gray-500">Preview do Dashboard</div>'
                  }}
                />
             </div>
          </div>
        </div>
      </section>

      {/* =====================================================================================
          FUNCIONALIDADES (ESTILO PETSHOP + FUNDAMENTEI)
      ===================================================================================== */}
      <div id="funcionalidades" className="flex flex-col bg-[#0E1117] overflow-hidden">
        
        {/* --- BLOCO 1: UPLOAD INTELIGENTE --- */}
        <section className="py-24 border-b border-gray-800/50 relative">
          <div className="absolute inset-0 bg-blue-900/5 -z-10" /> {/* Fundo sutil azulado */}
          
          <div className="max-w-7xl mx-auto px-6">
            {/* Cabeçalho do Bloco */}
            <div className="flex flex-col items-center text-center max-w-4xl mx-auto mb-16">
              <div className="w-16 h-16 bg-blue-600/10 rounded-2xl flex items-center justify-center mb-6 border border-blue-500/20 shadow-[0_0_30px_-5px_rgba(37,99,235,0.3)]">
                <UploadCloud className="text-blue-500 w-8 h-8" />
              </div>
              
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
                Upload Inteligente
              </h2>
              
              <p className="text-xl text-gray-400 leading-relaxed mb-8 max-w-2xl">
                Esqueça configurações manuais. Basta arrastar o PDF do Release de Resultados (ITR ou DFP). Nossa IA identifica tudo sozinha.
              </p>

              {/* Tags/Badges Estilo Petshop */}
              <div className="flex flex-wrap justify-center gap-4">
                <Badge text="Sem limite de tamanho" color="blue" icon={<Zap size={14}/>} />
                <Badge text="Identificação Automática" color="blue" icon={<MousePointerClick size={14}/>} />
                <Badge text="Processamento Rápido" color="blue" icon={<CheckCircle2 size={14}/>} />
              </div>
            </div>

            {/* Imagem Apresentável (W-FIT + GLOW) */}
            <div className="relative w-fit mx-auto group">
              <div className="absolute -inset-2 bg-blue-500/20 rounded-xl blur-xl opacity-0 group-hover:opacity-100 transition duration-700"></div>
              <img 
                src="/demo-upload.png" 
                alt="Tela de Upload" 
                className="relative block w-auto max-w-full h-auto rounded-xl border border-gray-700/80 shadow-2xl bg-[#0E1117]" 
              />
            </div>
          </div>
        </section>


        {/* --- BLOCO 2: ANÁLISE PROFUNDA --- */}
        <section className="py-24 border-b border-gray-800/50 relative">
          <div className="absolute inset-0 bg-green-900/5 -z-10" /> {/* Fundo sutil esverdeado */}

          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col items-center text-center max-w-4xl mx-auto mb-16">
              <div className="w-16 h-16 bg-green-600/10 rounded-2xl flex items-center justify-center mb-6 border border-green-500/20 shadow-[0_0_30px_-5px_rgba(22,163,74,0.3)]">
                <FileText className="text-green-500 w-8 h-8" />
              </div>
              
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
                Análise Profunda
              </h2>
              
              <p className="text-xl text-gray-400 leading-relaxed mb-8 max-w-2xl">
                Receba um Score Fundamentalista e uma tese de investimento detalhada escrita por Inteligência Artificial.
              </p>

              <div className="flex flex-wrap justify-center gap-4">
                <Badge text="Score (0 a 5)" color="green" icon={<BarChart3 size={14}/>} />
                <Badge text="Indicadores Coloridos" color="green" icon={<CheckCircle2 size={14}/>} />
                <Badge text="Tese Descritiva IA" color="green" icon={<FileText size={14}/>} />
              </div>
            </div>

            <div className="relative w-fit mx-auto group">
              <div className="absolute -inset-2 bg-green-500/20 rounded-xl blur-xl opacity-0 group-hover:opacity-100 transition duration-700"></div>
              <img 
                src="/demo-result.png" 
                alt="Tela de Resultado" 
                className="relative block w-auto max-w-full h-auto rounded-xl border border-gray-700/80 shadow-2xl bg-[#0E1117]" 
              />
            </div>
          </div>
        </section>


        {/* --- BLOCO 3: COMPARADOR DE ATIVOS --- */}
        <section className="py-24 border-b border-gray-800/50 relative">
          <div className="absolute inset-0 bg-purple-900/5 -z-10" />

          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col items-center text-center max-w-4xl mx-auto mb-16">
              <div className="w-16 h-16 bg-purple-600/10 rounded-2xl flex items-center justify-center mb-6 border border-purple-500/20 shadow-[0_0_30px_-5px_rgba(147,51,234,0.3)]">
                <Layout className="text-purple-500 w-8 h-8" />
              </div>
              
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
                Comparador de Ativos
              </h2>
              
              <p className="text-xl text-gray-400 leading-relaxed mb-8 max-w-2xl">
                Visualize e compare todas as empresas analisadas em uma única tabela interativa.
              </p>

              <div className="flex flex-wrap justify-center gap-4">
                <Badge text="Ordenação Inteligente" color="purple" icon={<ArrowRight size={14}/>} />
                <Badge text="Comparação Lado a Lado" color="purple" icon={<Layout size={14}/>} />
              </div>
            </div>

            {/* AQUI ESTÁ A CORREÇÃO CRÍTICA (w-fit) QUE VOCÊ PEDIU */}
            <div className="relative w-fit mx-auto group">
              <div className="absolute -inset-2 bg-purple-500/20 rounded-xl blur-xl opacity-0 group-hover:opacity-100 transition duration-700"></div>
              <img 
                src="/demo-table.png" 
                alt="Tabela Comparativa" 
                className="relative block w-auto max-w-full h-auto rounded-xl border border-gray-700/80 shadow-2xl bg-[#0E1117]" 
              />
            </div>
          </div>
        </section>


        {/* --- BLOCO 4: HISTÓRICO --- */}
        <section className="py-24 border-b border-gray-800/50 relative">
          <div className="absolute inset-0 bg-yellow-900/5 -z-10" />

          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col items-center text-center max-w-4xl mx-auto mb-16">
              <div className="w-16 h-16 bg-yellow-600/10 rounded-2xl flex items-center justify-center mb-6 border border-yellow-500/20 shadow-[0_0_30px_-5px_rgba(234,179,8,0.3)]">
                <Database className="text-yellow-500 w-8 h-8" />
              </div>
              
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
                Histórico Completo
              </h2>
              
              <p className="text-xl text-gray-400 leading-relaxed mb-8 max-w-2xl">
                Seu banco de dados pessoal de investimentos. Acesse análises antigas e acompanhe a evolução.
              </p>

              <div className="flex flex-wrap justify-center gap-4">
                <Badge text="Backup na Nuvem" color="yellow" icon={<Database size={14}/>} />
                <Badge text="Acesso Rápido" color="yellow" icon={<Zap size={14}/>} />
              </div>
            </div>

            <div className="relative w-fit mx-auto group">
              <div className="absolute -inset-2 bg-yellow-500/20 rounded-xl blur-xl opacity-0 group-hover:opacity-100 transition duration-700"></div>
              <img 
                src="/demo-history.png" 
                alt="Histórico" 
                className="relative block w-auto max-w-full h-auto rounded-xl border border-gray-700/80 shadow-2xl bg-[#0E1117]" 
              />
            </div>
          </div>
        </section>

      </div>


      {/* =====================================================================================
          PRICING (PLANOS - ORIGINAL PRESERVADO E INTOCADO)
      ===================================================================================== */}
      <section id="pricing" className="py-32 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">Planos Simples e Transparentes</h2>
            <p className="text-gray-400 text-lg">Comece grátis e faça o upgrade quando precisar.</p>
            
            <div className="flex items-center justify-center gap-4 mt-8">
              <span className={`text-sm font-medium ${billingCycle === 'monthly' ? 'text-white' : 'text-gray-500'}`}>Mensal</span>
              <button 
                onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
                className="w-14 h-8 bg-gray-800 rounded-full relative p-1 transition-colors hover:bg-gray-700"
              >
                <div className={`w-6 h-6 bg-blue-500 rounded-full shadow-md transform transition-transform ${billingCycle === 'yearly' ? 'translate-x-6' : ''}`} />
              </button>
              <span className={`text-sm font-medium ${billingCycle === 'yearly' ? 'text-white' : 'text-gray-500'}`}>
                Anual <span className="text-green-400 text-xs ml-1 font-bold">-20%</span>
              </span>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            
            {/* Free */}
            <div className="bg-[#161B22] border border-gray-800 rounded-2xl p-8 flex flex-col hover:border-gray-600 transition-all">
              <div className="mb-8">
                <h3 className="text-xl font-bold text-white mb-2">Hobby</h3>
                <div className="text-3xl font-bold text-white">R$ 0<span className="text-lg text-gray-500 font-normal">/mês</span></div>
                <p className="text-gray-400 text-sm mt-4">Para quem está começando a investir.</p>
              </div>
              <ul className="space-y-4 mb-8 flex-1">
                <Feature text="3 Análises por mês" />
                <Feature text="Acesso apenas ao ITR (Trimestral)" />
                <Feature text="Score Básico" />
                <Feature text="Histórico de 30 dias" disabled />
              </ul>
              <Link href="/register" className="w-full py-3 rounded-lg border border-gray-700 text-white font-medium hover:bg-gray-800 transition-colors text-center">
                Criar Conta Grátis
              </Link>
            </div>

            {/* Pro */}
            <div className="bg-[#161B22] border border-blue-600/50 rounded-2xl p-8 flex flex-col hover:border-blue-500 transition-all">
              <div className="mb-8">
                <h3 className="text-xl font-bold text-white mb-2">Pro Investor</h3>
                <div className="text-3xl font-bold text-white">
                  {billingCycle === 'monthly' ? 'R$ 29,90' : 'R$ 23,90'}
                  <span className="text-lg text-gray-500 font-normal">/mês</span>
                </div>
                <p className="text-gray-400 text-sm mt-4">Para investidores que levam a sério.</p>
              </div>
              <ul className="space-y-4 mb-8 flex-1">
                <Feature text="50 Análises por mês" />
                <Feature text="ITR e DFP (Anual)" />
                <Feature text="Score Fundamentalista Completo" />
                <Feature text="Teses de Investimento via IA" />
                <Feature text="Comparador de Ativos" />
              </ul>
              <Link href="/register" className="w-full py-3 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-500 transition-colors text-center shadow-lg shadow-blue-900/20">
                Assinar Agora
              </Link>
            </div>

            {/* Whale */}
            <div className="bg-[#161B22] border border-gray-800 rounded-2xl p-8 flex flex-col hover:border-gray-600 transition-all">
              <div className="mb-8">
                <h3 className="text-xl font-bold text-white mb-2">Whale</h3>
                <div className="text-3xl font-bold text-white">
                  {billingCycle === 'monthly' ? 'R$ 89,90' : 'R$ 71,90'}
                  <span className="text-lg text-gray-500 font-normal">/mês</span>
                </div>
                <p className="text-gray-400 text-sm mt-4">Para analistas e gestores.</p>
              </div>
              <ul className="space-y-4 mb-8 flex-1">
                <Feature text="Análises Ilimitadas" />
                <Feature text="Multi-upload (Lote)" />
                <Feature text="Exportação para Excel/CSV" />
                <Feature text="API de Acesso" />
                <Feature text="Gerente de Conta" />
              </ul>
              <Link href="/register" className="w-full py-3 rounded-lg border border-gray-700 text-white font-medium hover:bg-gray-800 transition-colors text-center">
                Falar com Vendas
              </Link>
            </div>

          </div>
        </div>
      </section>

      {/* =====================================================================================
          FOOTER
      ===================================================================================== */}
      <footer className="border-t border-gray-800 bg-[#0D1117] pt-16 pb-8">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-12 mb-16">
            <div className="col-span-2">
              <div className="flex items-center gap-2 mb-6">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <BarChart3 className="text-white w-5 h-5" />
                </div>
                <span className="text-xl font-bold text-white">FinAnalyzer.AI</span>
              </div>
              <p className="text-gray-400 max-w-sm mb-6">
                Transformando relatórios financeiros complexos em decisões simples e inteligentes com o poder da Inteligência Artificial.
              </p>
            </div>
            
            <div>
              <h4 className="font-bold text-white mb-6">Produto</h4>
              <ul className="space-y-4 text-gray-400">
                <li><a href="#funcionalidades" className="hover:text-blue-400 transition-colors">Funcionalidades</a></li>
                <li><a href="#pricing" className="hover:text-blue-400 transition-colors">Preços</a></li>
                <li><Link href="/register" className="hover:text-blue-400 transition-colors">Criar Conta</Link></li>
                <li><Link href="/login" className="hover:text-blue-400 transition-colors">Login</Link></li>
              </ul>
            </div>

            <div>
              <h4 className="font-bold text-white mb-6">Legal</h4>
              <ul className="space-y-4 text-gray-400">
                 <li><Link href="/terms" className="hover:text-blue-400 transition-colors">Termos de Uso</Link></li>
                 <li><Link href="/privacy" className="hover:text-blue-400 transition-colors">Privacidade</Link></li>
                 <li><Link href="/refund" className="hover:text-blue-400 transition-colors">Reembolso</Link></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 pt-8 flex flex-col items-center gap-4">
             <p className="text-xs text-gray-600 text-justify max-w-4xl leading-relaxed">
               <strong>Isenção de Responsabilidade:</strong> O FinAnalyzer.AI é uma ferramenta de análise assistida por inteligência artificial destinada exclusivamente para fins <strong>educacionais, informativos e de suporte</strong>. Ela <strong className="text-gray-300">não substitui a análise humana</strong>, nem constitui recomendação de compra ou venda de ativos. O FinAnalyzer.AI não se responsabiliza pela precisão, integridade ou atualização dos dados, nem por quaisquer decisões de investimento ou prejuízos financeiros decorrentes do uso destas informações. Rentabilidade passada não representa garantia de rentabilidade futura.
             </p>

             <p className="text-center pt-4 text-gray-500">
               © 2026 FinAnalyzer Inc. Todos os direitos reservados.
             </p>
          </div>

        </div>
      </footer>
    </div>
  );
}

// --- COMPONENTES AUXILIARES (Para deixar o código limpo) ---

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

// Novo componente de Badge (Estilo Petshop)
function Badge({ text, color, icon }: { text: string, color: 'blue' | 'green' | 'purple' | 'yellow', icon?: React.ReactNode }) {
    const styles = {
        blue: "bg-blue-500/10 text-blue-400 border-blue-500/20 hover:bg-blue-500/20",
        green: "bg-green-500/10 text-green-400 border-green-500/20 hover:bg-green-500/20",
        purple: "bg-purple-500/10 text-purple-400 border-purple-500/20 hover:bg-purple-500/20",
        yellow: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20 hover:bg-yellow-500/20",
    }
    return (
        <div className={`px-4 py-2 rounded-full border flex items-center gap-2 text-sm font-medium transition-colors cursor-default ${styles[color]}`}>
            {icon}
            {text}
        </div>
    )
}