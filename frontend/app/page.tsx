"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  BarChart3, UploadCloud, ArrowRight, 
  FileText, Layout, Database, Check, X, CheckCircle2 
} from "lucide-react";

export default function LandingPage() {
  const router = useRouter(); 
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  // Verifica se já existe sessão antiga (opcional, mas mantive sua lógica)
  useEffect(() => {
    const user = localStorage.getItem('usuario');
    if (user) {
      router.push('/dashboard'); 
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-[#0E1117] text-gray-100 font-sans selection:bg-blue-500/30">
      
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
            <Link href="#funcionalidades" className="hidden md:block text-gray-300 hover:text-white font-medium transition-colors">
              Funcionalidades
            </Link>
            <Link href="#planos" className="hidden md:block text-gray-300 hover:text-white font-medium transition-colors">
              Preços
            </Link>
            
            {/* CORREÇÃO AQUI: Mandamos para dashboard, o Middleware cuida do resto */}
            <Link href="/dashboard" className="hidden md:block text-gray-300 hover:text-white font-medium transition-colors">
              Entrar
            </Link>
            <Link href="/dashboard" className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2.5 rounded-lg font-bold transition-all shadow-lg shadow-blue-900/20 hover:scale-105">
              Começar Grátis
            </Link>
          </div>
        </div>
      </nav>

      {/* --- HERO SECTION --- */}
      <section className="relative pt-24 pb-32 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-blue-600/20 blur-[120px] rounded-full -z-10" />

        <div className="max-w-5xl mx-auto px-6 text-center">
          
          <h1 className="text-5xl md:text-7xl font-bold text-white tracking-tight mb-8 leading-tight">
            Analise Ações em <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">Segundos, não Horas.</span>
          </h1>
          
          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed">
            Abandone a leitura manual de PDFs. Nossa IA lê os balanços, interpreta os dados e entrega uma tese de investimento completa.
          </p>

          <div className="flex flex-col md:flex-row items-center justify-center gap-4">
            {/* CORREÇÃO AQUI TAMBÉM */}
            <Link href="/dashboard" className="w-full md:w-auto bg-white text-gray-900 px-8 py-4 rounded-xl font-bold text-lg hover:bg-gray-100 transition-all flex items-center justify-center gap-2">
              Criar Conta Grátis <ArrowRight size={20} />
            </Link>
            <Link href="#funcionalidades" className="w-full md:w-auto px-8 py-4 rounded-xl font-bold text-lg text-gray-300 border border-gray-700 hover:border-gray-500 hover:text-white transition-all">
              Ver Funcionalidades
            </Link>
          </div>
        </div>
      </section>

      {/* --- SEÇÃO: FUNCIONALIDADES --- */}
      <div id="funcionalidades" className="flex flex-col gap-32 pb-32 overflow-hidden">
        
        {/* BLOCO 1: UPLOAD */}
        <section className="relative">
          <div className="max-w-7xl mx-auto px-6 lg:grid lg:grid-cols-[40%_60%] gap-12 items-center">
            <div className="order-2 lg:order-1">
              <div className="w-14 h-14 bg-blue-600/20 rounded-2xl flex items-center justify-center mb-6 border border-blue-500/30">
                <UploadCloud className="text-blue-400 w-7 h-7" />
              </div>
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">Upload Inteligente</h2>
              <p className="text-lg text-gray-400 leading-relaxed mb-6">
                Esqueça configurações manuais. Basta arrastar o PDF do Release de Resultados (ITR ou DFP). Nossa IA identifica automaticamente a empresa, o trimestre e o ano.
              </p>
              <ul className="space-y-3">
                <ListItem>Sem limite de tamanho de arquivo</ListItem>
                <ListItem>Identificação automática de tickers</ListItem>
                <ListItem>Processamento em nuvem ultra-rápido</ListItem>
              </ul>
            </div>
            <div className="order-1 lg:order-2 w-full">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-blue-600/10 blur-[90px] rounded-full -z-10" />
              <img src="/demo-upload.png" alt="Tela de Upload" className="w-full h-auto object-contain drop-shadow-2xl" />
            </div>
          </div>
        </section>

        {/* BLOCO 2: RESULTADO */}
        <section className="relative">
          <div className="max-w-7xl mx-auto px-6 lg:grid lg:grid-cols-[60%_40%] gap-12 items-center">
            <div className="order-1 w-full">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-green-600/10 blur-[90px] rounded-full -z-10" />
              <img src="/demo-result.png" alt="Tela de Resultado" className="w-full h-auto object-contain drop-shadow-2xl" />
            </div>
            <div className="order-2">
              <div className="w-14 h-14 bg-green-600/20 rounded-2xl flex items-center justify-center mb-6 border border-green-500/30">
                <FileText className="text-green-400 w-7 h-7" />
              </div>
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">Análise Profunda</h2>
              <p className="text-lg text-gray-400 leading-relaxed mb-6">
                O FinAnalyzer gera um Score de 0 a 5 baseado em fundamentos sólidos e escreve uma tese de investimento completa.
              </p>
              <ul className="space-y-3">
                <ListItem>Score Fundamentalista (0 a 5)</ListItem>
                <ListItem>Indicadores visuais coloridos</ListItem>
                <ListItem>Tese descritiva gerada por IA</ListItem>
              </ul>
            </div>
          </div>
        </section>

        {/* BLOCO 3: TABELA */}
        <section className="relative">
          <div className="max-w-7xl mx-auto px-6 lg:grid lg:grid-cols-[40%_60%] gap-12 items-center">
            <div className="order-2 lg:order-1">
              <div className="w-14 h-14 bg-purple-600/20 rounded-2xl flex items-center justify-center mb-6 border border-purple-500/30">
                <Layout className="text-purple-400 w-7 h-7" />
              </div>
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">Comparador de Ativos</h2>
              <p className="text-lg text-gray-400 leading-relaxed mb-6">
                Visualize todas as empresas que você analisou em uma única tabela interativa. Ordene por Nota, Receita ou Lucro.
              </p>
              <ul className="space-y-3">
                <ListItem>Colunas customizáveis</ListItem>
                <ListItem>Ordenação inteligente</ListItem>
                <ListItem>Comparação lado a lado</ListItem>
              </ul>
            </div>
            <div className="order-1 lg:order-2 w-full">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-purple-600/10 blur-[90px] rounded-full -z-10" />
              <img src="/demo-table.png" alt="Tabela Agregada" className="w-full h-auto object-contain drop-shadow-2xl" />
            </div>
          </div>
        </section>

        {/* BLOCO 4: HISTÓRICO */}
        <section className="relative">
          <div className="max-w-7xl mx-auto px-6 lg:grid lg:grid-cols-[60%_40%] gap-12 items-center">
            <div className="order-1 w-full">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-yellow-600/10 blur-[90px] rounded-full -z-10" />
              <img src="/demo-history.png" alt="Histórico" className="w-full h-auto object-contain drop-shadow-2xl" />
            </div>
            <div className="order-2">
              <div className="w-14 h-14 bg-yellow-600/20 rounded-2xl flex items-center justify-center mb-6 border border-yellow-500/30">
                <Database className="text-yellow-400 w-7 h-7" />
              </div>
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">Histórico Completo</h2>
              <p className="text-lg text-gray-400 leading-relaxed mb-6">
                Todas as suas análises ficam salvas para sempre. Compare a evolução da nota da empresa trimestre a trimestre.
              </p>
              <ul className="space-y-3">
                <ListItem>Backup automático na nuvem</ListItem>
                <ListItem>Acesso rápido a relatórios antigos</ListItem>
                <ListItem>Exclusão e gerenciamento fácil</ListItem>
              </ul>
            </div>
          </div>
        </section>
      </div>

      {/* --- SEÇÃO DE PLANOS --- */}
      <section id="planos" className="py-24 relative bg-[#0d1117] border-t border-gray-800">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
              Um único plano. <br />
              O site mais completo para o investidor.
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
            <div className={`transition-opacity duration-300 ${billingCycle === 'yearly' ? 'opacity-100' : 'opacity-0'} mt-2`}>
               <span className="bg-orange-500/20 text-orange-400 text-xs font-bold px-3 py-1 rounded-full">2 MESES GRÁTIS</span>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8 items-start max-w-4xl mx-auto">
            {/* CARD GRATUITO */}
            <div className="bg-[#161b22] border border-gray-800 rounded-3xl p-8 hover:border-gray-600 transition-all h-full flex flex-col">
              <h3 className="text-3xl font-bold text-white mb-2">Gratuito</h3>
              <p className="text-gray-400 text-base mb-8">Para começar a analisar sem custo.</p>
              
              <ul className="space-y-4 mb-8 flex-1">
                <Feature text="5 Análises por semana" active />
                <Feature text="Upload de arquivos ilimitado" active />
                <Feature text="Acesso ao histórico simples" active />
                <Feature text="Suporte por email" active />
                {/* Bloqueios */}
                <Feature text="Download do Relatório PDF" disabled />
                <Feature text="Tabela Comparativa de Ativos" disabled />
              </ul>

              {/* CORREÇÃO AQUI */}
              <Link href="/dashboard" className="block w-full text-center py-4 rounded-xl border border-gray-600 text-white font-bold hover:bg-gray-700 hover:border-gray-500 transition-all mt-auto">
                Criar conta grátis
              </Link>
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
              <p className="text-gray-400 text-sm mb-8">Para quem quer realmente evoluir como investidor!</p>
              
              <ul className="space-y-4 mb-8 flex-1">
                <Feature text="Análises de IA Ilimitadas" active />
                <Feature text="Download do Relatório PDF Completo" active />
                <Feature text="Tabela Comparativa Customizável" active />
                <Feature text="Upload de arquivos ilimitado" active />
                <Feature text="Histórico de dados ilimitado" active />
                <Feature text="Prioridade máxima na fila" active />
              </ul>

              {/* CORREÇÃO AQUI */}
              <Link href="/dashboard" className="block w-full text-center py-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold shadow-lg shadow-blue-900/20 transition-all mt-auto">
                Assinar Agora
              </Link>
              <p className="text-center text-xs text-gray-500 mt-4">Cancele quando quiser.</p>
            </div>
          </div>
        </div>
      </section>

      {/* --- FOOTER & DISCLAIMERS --- */}
      <footer className="border-t border-gray-800 bg-[#0E1117] pt-16 pb-8">
        <div className="max-w-7xl mx-auto px-6">
          
          {/* Logo e Links Principais */}
          <div className="flex flex-col md:flex-row justify-between items-center gap-6 mb-12">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gray-800 rounded-lg flex items-center justify-center">
                <BarChart3 className="text-gray-400 w-5 h-5" />
              </div>
              <span className="text-lg font-bold text-gray-300">FinAnalyzer.AI</span>
            </div>
            
            <div className="flex gap-6">
              <a href="#" className="text-gray-500 hover:text-white transition-colors">Termos</a>
              <a href="#" className="text-gray-500 hover:text-white transition-colors">Privacidade</a>
              <a href="#" className="text-gray-500 hover:text-white transition-colors">Contato</a>
            </div>
          </div>

          {/* ÁREA DE DISCLAIMER - TEXTO MAIS CLARO */}
          <div className="border-t border-gray-800 pt-8 text-xs text-gray-400 space-y-4 text-justify leading-relaxed">
             <p>
               <strong className="text-gray-200">AVISO IMPORTANTE SOBRE IA:</strong> A análise apresentada nesta plataforma é gerada por algoritmos de Inteligência Artificial e serve apenas como uma <strong className="text-gray-300">ferramenta auxiliar de suporte</strong>. Ela <strong className="text-gray-300">não substitui a análise humana</strong>, nem constitui recomendação de compra ou venda de ativos. O FinAnalyzer.AI não se responsabiliza pela precisão, integridade ou atualização dos dados, nem por quaisquer decisões de investimento ou prejuízos financeiros decorrentes do uso destas informações. Rentabilidade passada não representa garantia de rentabilidade futura.
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