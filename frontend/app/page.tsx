"use client";
import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  BarChart3, UploadCloud, Zap, ShieldCheck, ArrowRight, 
  CheckCircle2, TrendingUp, FileText, Search, Layout, Database 
} from "lucide-react";

export default function LandingPage() {
  const router = useRouter(); 

  // --- EFEITO DE VERIFICAÇÃO ---
  useEffect(() => {
    // Verifica se tem usuário salvo no navegador
    const user = localStorage.getItem('usuario');
    if (user) {
      router.push('/dashboard'); // Se tiver logado, manda pro painel
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
            <Link href="/pricing" className="hidden md:block text-gray-300 hover:text-white font-medium transition-colors">
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
      <section className="relative pt-20 pb-20 overflow-hidden">
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
            <Link href="#galeria" className="w-full md:w-auto px-8 py-4 rounded-xl font-bold text-lg text-gray-300 border border-gray-700 hover:border-gray-500 hover:text-white transition-all">
              Ver Funcionalidades
            </Link>
          </div>
        </div>
      </section>

      {/* --- GALERIA DE FUNCIONALIDADES (NOVO) --- */}
      <section id="galeria" className="py-20 bg-[#0d1117] border-y border-gray-800">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Por dentro da Plataforma</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">Interface limpa, rápida e focada na tomada de decisão.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-12">
            
            {/* Feature 1: Upload */}
            <div className="space-y-4 group">
              <div className="rounded-2xl overflow-hidden border border-gray-800 shadow-2xl transition-all duration-500 group-hover:border-blue-500/50 group-hover:shadow-blue-900/20">
                <img src="/demo-upload.jpg" alt="Tela de Upload" className="w-full h-auto transform transition-transform duration-700 group-hover:scale-105" />
              </div>
              <div className="px-2">
                <h3 className="text-2xl font-bold text-white flex items-center gap-2">
                  <UploadCloud className="text-blue-500" /> 1. Upload Simples
                </h3>
                <p className="text-gray-400 mt-2">Basta arrastar o PDF do relatório. O sistema identifica automaticamente a empresa, ano e trimestre.</p>
              </div>
            </div>

            {/* Feature 2: Resultado */}
            <div className="space-y-4 group">
              <div className="rounded-2xl overflow-hidden border border-gray-800 shadow-2xl transition-all duration-500 group-hover:border-blue-500/50 group-hover:shadow-blue-900/20">
                <img src="/demo-result.jpg" alt="Tela de Resultado" className="w-full h-auto transform transition-transform duration-700 group-hover:scale-105" />
              </div>
              <div className="px-2">
                <h3 className="text-2xl font-bold text-white flex items-center gap-2">
                  <FileText className="text-green-500" /> 2. Análise Profunda
                </h3>
                <p className="text-gray-400 mt-2">Receba um Score de 0 a 5, indicadores visuais (Receita, Margem, Dívida) e uma tese escrita pela IA.</p>
              </div>
            </div>

            {/* Feature 3: Tabela */}
            <div className="space-y-4 group">
              <div className="rounded-2xl overflow-hidden border border-gray-800 shadow-2xl transition-all duration-500 group-hover:border-blue-500/50 group-hover:shadow-blue-900/20">
                <img src="/demo-table.jpg" alt="Tabela Agregada" className="w-full h-auto transform transition-transform duration-700 group-hover:scale-105" />
              </div>
              <div className="px-2">
                <h3 className="text-2xl font-bold text-white flex items-center gap-2">
                  <Layout className="text-purple-500" /> 3. Comparação Inteligente
                </h3>
                <p className="text-gray-400 mt-2">Visualize todas as suas empresas em uma única tabela. Ordene por nota, lucro ou receita para encontrar as melhores.</p>
              </div>
            </div>

            {/* Feature 4: Histórico */}
            <div className="space-y-4 group">
              <div className="rounded-2xl overflow-hidden border border-gray-800 shadow-2xl transition-all duration-500 group-hover:border-blue-500/50 group-hover:shadow-blue-900/20">
                <img src="/demo-history.jpg" alt="Histórico Detalhado" className="w-full h-auto transform transition-transform duration-700 group-hover:scale-105" />
              </div>
              <div className="px-2">
                <h3 className="text-2xl font-bold text-white flex items-center gap-2">
                  <Database className="text-yellow-500" /> 4. Histórico Completo
                </h3>
                <p className="text-gray-400 mt-2">Seus dados ficam salvos. Acesse relatórios antigos e compare a evolução das notas ao longo do tempo.</p>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* --- CTA FINAL --- */}
      <section className="py-32 px-6 text-center relative overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-indigo-600/10 blur-[100px] rounded-full -z-10" />
        
        <h2 className="text-4xl md:text-5xl font-bold text-white mb-8">Pronto para investir melhor?</h2>
        <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
          Pare de perder tempo lendo documentos burocráticos. Deixe a tecnologia trabalhar para você.
        </p>
        <Link href="/register" className="inline-block bg-white text-gray-900 px-10 py-5 rounded-2xl font-bold text-xl hover:bg-gray-100 hover:scale-105 transition-all shadow-2xl">
          Criar Conta Gratuita
        </Link>
        <p className="mt-6 text-sm text-gray-500">Não requer cartão de crédito • Cancelamento a qualquer momento</p>
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
            <a href="#" className="text-gray-500 hover:text-white transition-colors">Contato</a>
          </div>
        </div>
      </footer>
    </div>
  );
}