"use client";
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  BarChart3, UploadCloud, Zap, ArrowRight, 
  FileText, Layout, Database, Check, X 
} from "lucide-react";

export default function LandingPage() {
  const router = useRouter(); 
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  // --- EFEITO DE VERIFICAÇÃO ---
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
            <Link href="/login" className="hidden md:block text-gray-300 hover:text-white font-medium transition-colors">
              Entrar
            </Link>
            <Link href="/register" className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2.5 rounded-lg font-bold transition-all shadow-lg shadow-blue-900/20 hover:scale-105">
              Começar Grátis
            </Link>
          </div>
        </div>
      </nav>

      {/* --- HERO SECTION --- */}
      <section className="relative pt-24 pb-32 overflow-hidden">
        {/* Glow de fundo */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-blue-600/20 blur-[120px] rounded-full -z-10" />

        <div className="max-w-5xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-900/30 border border-blue-500/30 text-blue-400 text-sm font-bold mb-8 animate-in fade-in slide-in-from-bottom-4">
            <Zap size={16} /> Nova IA v2.0 disponível
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold text-white tracking-tight mb-8 leading-tight">
            Analise Ações em <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">Segundos, não Horas.</span>
          </h1>
          
          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed">
            Abandone a leitura manual de PDFs. Nossa IA lê os balanços, interpreta os dados e entrega uma tese de investimento pronta.
          </p>

          <div className="flex flex-col md:flex-row items-center justify-center gap-4">
            <Link href="/register" className="w-full md:w-auto bg-white text-gray-900 px-8 py-4 rounded-xl font-bold text-lg hover:bg-gray-100 transition-all flex items-center justify-center gap-2">
              Criar Conta Grátis <ArrowRight size={20} />
            </Link>
            <Link href="#funcionalidades" className="w-full md:w-auto px-8 py-4 rounded-xl font-bold text-lg text-gray-300 border border-gray-700 hover:border-gray-500 hover:text-white transition-all">
              Ver Funcionalidades
            </Link>
          </div>
        </div>
      </section>

      {/* --- GALERIA BENTO GRID (Estilo Bolha/Fundo) --- */}
      <section id="funcionalidades" className="py-20 bg-[#0d1117] border-y border-gray-800">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Poderoso. Simples. Visual.</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">Tudo o que você precisa em uma única tela.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            
            {/* CARD 1: UPLOAD */}
            <div className="group relative overflow-hidden rounded-[2rem] border border-gray-800 bg-[#161b22] h-[400px] transition-all hover:border-blue-500/50 hover:shadow-2xl hover:shadow-blue-900/10">
              {/* Imagem de Fundo (Bolha) */}
              <div className="absolute inset-0">
                <img 
                  src="/demo-upload.jpg" 
                  alt="Upload" 
                  className="h-full w-full object-cover object-center transition-transform duration-700 group-hover:scale-105 opacity-60 group-hover:opacity-40"
                  onError={(e) => e.currentTarget.style.display = 'none'} 
                />
                {/* Degradê para o texto ficar legível */}
                <div className="absolute inset-0 bg-gradient-to-t from-[#0E1117] via-[#0E1117]/80 to-transparent" />
              </div>
              
              {/* Texto Flutuante */}
              <div className="absolute bottom-0 left-0 p-8 z-10">
                <div className="w-12 h-12 bg-blue-600/20 backdrop-blur-md rounded-2xl flex items-center justify-center mb-4 border border-blue-500/30">
                  <UploadCloud className="text-blue-400 w-6 h-6" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">1. Upload Inteligente</h3>
                <p className="text-gray-400 leading-relaxed">Arraste o PDF. Nossa IA detecta automaticamente a empresa, o trimestre e organiza tudo para você.</p>
              </div>
            </div>

            {/* CARD 2: RESULTADO */}
            <div className="group relative overflow-hidden rounded-[2rem] border border-gray-800 bg-[#161b22] h-[400px] transition-all hover:border-green-500/50 hover:shadow-2xl hover:shadow-green-900/10">
              <div className="absolute inset-0">
                <img 
                  src="/demo-result.jpg" 
                  alt="Resultado" 
                  className="h-full w-full object-cover object-top transition-transform duration-700 group-hover:scale-105 opacity-60 group-hover:opacity-40"
                  onError={(e) => e.currentTarget.style.display = 'none'} 
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0E1117] via-[#0E1117]/80 to-transparent" />
              </div>
              
              <div className="absolute bottom-0 left-0 p-8 z-10">
                <div className="w-12 h-12 bg-green-600/20 backdrop-blur-md rounded-2xl flex items-center justify-center mb-4 border border-green-500/30">
                  <FileText className="text-green-400 w-6 h-6" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">2. Análise Profunda</h3>
                <p className="text-gray-400 leading-relaxed">Score de 0 a 5, indicadores visuais de saúde financeira e uma tese de investimento escrita por IA.</p>
              </div>
            </div>

            {/* CARD 3: TABELA */}
            <div className="group relative overflow-hidden rounded-[2rem] border border-gray-800 bg-[#161b22] h-[400px] transition-all hover:border-purple-500/50 hover:shadow-2xl hover:shadow-purple-900/10">
              <div className="absolute inset-0">
                <img 
                  src="/demo-table.jpg" 
                  alt="Tabela" 
                  className="h-full w-full object-cover object-left-top transition-transform duration-700 group-hover:scale-105 opacity-60 group-hover:opacity-40"
                  onError={(e) => e.currentTarget.style.display = 'none'} 
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0E1117] via-[#0E1117]/80 to-transparent" />
              </div>
              
              <div className="absolute bottom-0 left-0 p-8 z-10">
                <div className="w-12 h-12 bg-purple-600/20 backdrop-blur-md rounded-2xl flex items-center justify-center mb-4 border border-purple-500/30">
                  <Layout className="text-purple-400 w-6 h-6" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">3. Comparador de Ativos</h3>
                <p className="text-gray-400 leading-relaxed">Compare empresas lado a lado. Ordene por Nota, Lucro ou Receita para encontrar as melhores oportunidades.</p>
              </div>
            </div>

            {/* CARD 4: HISTÓRICO */}
            <div className="group relative overflow-hidden rounded-[2rem] border border-gray-800 bg-[#161b22] h-[400px] transition-all hover:border-yellow-500/50 hover:shadow-2xl hover:shadow-yellow-900/10">
              <div className="absolute inset-0">
                <img 
                  src="/demo-history.jpg" 
                  alt="Histórico" 
                  className="h-full w-full object-cover object-top transition-transform duration-700 group-hover:scale-105 opacity-60 group-hover:opacity-40"
                  onError={(e) => e.currentTarget.style.display = 'none'} 
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0E1117] via-[#0E1117]/80 to-transparent" />
              </div>
              
              <div className="absolute bottom-0 left-0 p-8 z-10">
                <div className="w-12 h-12 bg-yellow-600/20 backdrop-blur-md rounded-2xl flex items-center justify-center mb-4 border border-yellow-500/30">
                  <Database className="text-yellow-400 w-6 h-6" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">4. Histórico Completo</h3>
                <p className="text-gray-400 leading-relaxed">Nunca mais perca uma análise. Seus dados ficam salvos na nuvem para você comparar a evolução trimestral.</p>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* --- SEÇÃO DE PLANOS --- */}
      <section id="planos" className="py-24 relative bg-[#0E1117]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
              Um único plano. <br />
              O site mais completo para o investidor.
            </h2>
            
            {/* Toggle Switch */}
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
            {/* Aviso de desconto */}
            <div className={`transition-opacity duration-300 ${billingCycle === 'yearly' ? 'opacity-100' : 'opacity-0'} mt-2`}>
               <span className="bg-orange-500/20 text-orange-400 text-xs font-bold px-3 py-1 rounded-full">2 MESES GRÁTIS</span>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-8 items-start max-w-4xl mx-auto">
            
            {/* CARD GRATUITO */}
            <div className="bg-[#161b22] border border-gray-800 rounded-3xl p-8 hover:border-gray-600 transition-all h-full flex flex-col">
              <h3 className="text-3xl font-bold text-white mb-2">Gratuito</h3>
              <p className="text-gray-400 text-base mb-8">Pra quem se vira com pouquíssimos dados...</p>
              
              <ul className="space-y-4 mb-8 flex-1">
                <Feature text="1 Análise de IA por dia" active />
                <Feature text="Upload limitado (5MB)" active />
                <Feature text="Acesso ao histórico simples" active />
                <Feature text="Suporte por email" active />
                <Feature text="Sem tabela comparativa" disabled />
                <Feature text="Sem prioridade de fila" disabled />
              </ul>

              <Link href="/register" className="block w-full text-center py-4 rounded-xl border border-gray-600 text-white font-bold hover:bg-gray-700 hover:border-gray-500 transition-all mt-auto">
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
                <span className="text-5xl font-bold text-white">{billingCycle === 'monthly' ? 'R$ 49' : 'R$ 490'}</span>
                <span className="text-gray-500 mb-1 text-lg">{billingCycle === 'monthly' ? '/mês' : '/ano'}</span>
              </div>
              <p className="text-gray-400 text-sm mb-8">Para quem quer realmente evoluir como investidor!</p>
              
              <ul className="space-y-4 mb-8 flex-1">
                <Feature text="Análises de IA Ilimitadas" active />
                <Feature text="Upload de arquivos grandes (50MB+)" active />
                <Feature text="Histórico de dados ilimitado" active />
                <Feature text="Tabela Comparativa Customizável" active />
                <Feature text="Prioridade no processamento" active />
                <Feature text="Acesso antecipado a novas features" active />
              </ul>

              <Link href="/pricing" className="block w-full text-center py-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold shadow-lg shadow-blue-900/20 transition-all mt-auto">
                Assinar Agora
              </Link>
              <p className="text-center text-xs text-gray-500 mt-4">Cancele quando quiser.</p>
            </div>

          </div>
        </div>
      </section>

      {/* --- FOOTER --- */}
      <footer className="border-t border-gray-800 py-12 bg-[#0E1117]">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gray-800 rounded-lg flex items-center justify-center">
              <BarChart3 className="text-gray-400 w-5 h-5" />
            </div>
            <span className="text-lg font-bold text-gray-300">FinAnalyzer.AI</span>
          </div>
          <div className="text-gray-500 text-sm">
            © 2026 FinAnalyzer Inc. Todos os direitos reservados.
          </div>
          <div className="flex gap-6">
            <a href="#" className="text-gray-500 hover:text-white transition-colors">Termos</a>
            <a href="#" className="text-gray-500 hover:text-white transition-colors">Privacidade</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Componente auxiliar para a lista de features
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
      <span className={`text-base ${disabled ? 'text-gray-600 line-through' : 'text-gray-300'}`}>{text}</span>
    </li>
  );
}