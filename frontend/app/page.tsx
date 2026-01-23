"use client";
import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  BarChart3, UploadCloud, Zap, ShieldCheck, ArrowRight, 
  CheckCircle2, TrendingUp, FileText, Search 
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

  // ... O resto do código continua igual aqui para baixo ...
  return (
    <div className="min-h-screen bg-[#0E1117] text-gray-100 font-sans selection:bg-blue-500/30">
      
      {/* --- NAVBAR --- */}
      <nav className="border-b border-gray-800 bg-[#0E1117]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          
          {/* --- LADO ESQUERDO: LOGO --- */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/20">
              <BarChart3 className="text-white w-6 h-6" />
            </div>
            <span className="text-2xl font-bold tracking-tight text-white">
              FinAnalyzer <span className="text-blue-500">.AI</span>
            </span>
          </div>

          {/* --- LADO DIREITO: MENUS E BOTÕES --- */}
          <div className="flex items-center gap-4">
            
            {/* Link Preços (NOVO) */}
            <Link href="/pricing" className="hidden md:block text-gray-300 hover:text-white font-medium transition-colors">
              Preços
            </Link>

            {/* Link Entrar */}
            <Link href="/login" className="hidden md:block text-gray-300 hover:text-white font-medium transition-colors">
              Entrar
            </Link>

            {/* Botão Começar */}
            <Link href="/register" className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2.5 rounded-lg font-bold transition-all shadow-lg shadow-blue-900/20 hover:scale-105">
              Começar Grátis
            </Link>
          </div>

        </div>
      </nav>
      {/* --- HERO SECTION --- */}
      <section className="relative pt-20 pb-32 overflow-hidden">
        {/* Efeito de fundo */}
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
            Abandone a leitura manual de PDFs de 50 páginas. Nossa IA lê os balanços trimestrais, interpreta os dados e entrega uma tese de investimento pronta com notas objetivas.
          </p>

          <div className="flex flex-col md:flex-row items-center justify-center gap-4">
            <Link href="/register" className="w-full md:w-auto bg-white text-gray-900 px-8 py-4 rounded-xl font-bold text-lg hover:bg-gray-100 transition-all flex items-center justify-center gap-2">
              Criar Conta Grátis <ArrowRight size={20} />
            </Link>
            <Link href="#como-funciona" className="w-full md:w-auto px-8 py-4 rounded-xl font-bold text-lg text-gray-300 border border-gray-700 hover:border-gray-500 hover:text-white transition-all">
              Ver Exemplo
            </Link>
          </div>

          <div className="mt-12 flex items-center justify-center gap-8 text-gray-500 text-sm font-medium">
            <span className="flex items-center gap-2"><CheckCircle2 size={16} className="text-green-500" /> Sem cartão de crédito</span>
            <span className="flex items-center gap-2"><CheckCircle2 size={16} className="text-green-500" /> Análises ilimitadas (Beta)</span>
          </div>
        </div>
      </section>

      {/* --- PREVIEW DO PRODUTO (MOCKUP) --- */}
      <section className="pb-32 px-6">
        <div className="max-w-6xl mx-auto bg-[#161b22] border border-gray-800 rounded-3xl p-4 md:p-8 shadow-2xl relative">
          <div className="absolute -top-px left-10 right-10 h-px bg-gradient-to-r from-transparent via-blue-500 to-transparent opacity-50" />
          
          {/* Mockup Header */}
          <div className="flex items-center gap-4 mb-8 border-b border-gray-800 pb-6">
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/20" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/20" />
              <div className="w-3 h-3 rounded-full bg-green-500/20" />
            </div>
            <div className="bg-gray-900 px-4 py-1.5 rounded-md text-xs text-gray-500 font-mono flex-1 text-center">finanalyzer.ai/dashboard/analysis/nvda</div>
          </div>

          {/* Mockup Content */}
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div>
                <h3 className="text-blue-400 font-bold text-sm tracking-wider uppercase mb-2">Resultado Processado</h3>
                <h2 className="text-4xl font-bold text-white">NVIDIA Corp.</h2>
                <p className="text-gray-400">1º Trimestre 2025</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
                  <p className="text-gray-500 text-xs uppercase font-bold mb-1">Receita</p>
                  <p className="text-2xl font-bold text-green-400">5/5</p>
                </div>
                <div className="bg-gray-900/50 p-4 rounded-xl border border-gray-800">
                  <p className="text-gray-500 text-xs uppercase font-bold mb-1">Dívida</p>
                  <p className="text-2xl font-bold text-yellow-400">3.5/5</p>
                </div>
              </div>

              <div className="bg-blue-900/10 border border-blue-500/20 p-6 rounded-xl">
                <p className="text-blue-200 italic">
                  "A empresa apresentou um crescimento explosivo em Data Centers, superando as expectativas em 15%. A margem bruta expandiu, demonstrando forte poder de precificação..."
                </p>
              </div>
            </div>

            {/* Ilustração Visual */}
            <div className="relative">
               <div className="absolute inset-0 bg-blue-600/20 blur-3xl rounded-full" />
               <div className="relative bg-[#0d1117] border border-gray-700 rounded-xl p-6 space-y-4">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-red-500/10 rounded-lg text-red-500"><FileText size={24} /></div>
                    <div>
                      <p className="text-white font-bold">Relatorio_Q1_2025.pdf</p>
                      <p className="text-xs text-gray-500">15.4 MB • Processado em 12s</p>
                    </div>
                    <CheckCircle2 className="text-green-500 ml-auto" />
                  </div>
                  <div className="h-px bg-gray-800" />
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm"><span className="text-gray-400">Extração de Texto</span><span className="text-green-400">100%</span></div>
                    <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden"><div className="bg-green-500 w-full h-full" /></div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm"><span className="text-gray-400">Análise de IA</span><span className="text-blue-400">100%</span></div>
                    <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden"><div className="bg-blue-500 w-full h-full" /></div>
                  </div>
               </div>
            </div>
          </div>
        </div>
      </section>

      {/* --- COMO FUNCIONA (FEATURES) --- */}
      <section id="como-funciona" className="py-24 bg-[#0d1117] border-y border-gray-800">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Como o FinAnalyzer funciona?</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">Simples, rápido e direto ao ponto. Você foca na decisão, nós focamos na análise.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<UploadCloud className="text-blue-400" size={32} />}
              title="1. Upload do PDF"
              desc="Baixe o release de resultados do RI da empresa e arraste para a plataforma. Aceitamos arquivos de até 50MB."
            />
            <FeatureCard 
              icon={<Zap className="text-purple-400" size={32} />}
              title="2. IA Analisa Tudo"
              desc="Nossos modelos leem linha por linha, ignorando o marketing e focando nos números reais (Receita, Ebitda, Dívida)."
            />
            <FeatureCard 
              icon={<TrendingUp className="text-green-400" size={32} />}
              title="3. Decisão Clara"
              desc="Receba uma nota de 0 a 5 e uma tese de investimento resumida para saber se vale a pena estudar a empresa a fundo."
            />
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

function FeatureCard({ icon, title, desc }: any) {
  return (
    <div className="bg-[#161b22] p-8 rounded-2xl border border-gray-800 hover:border-blue-500/50 transition-all duration-300 group hover:-translate-y-1">
      <div className="bg-gray-900 w-16 h-16 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <h3 className="text-xl font-bold text-white mb-3">{title}</h3>
      <p className="text-gray-400 leading-relaxed">{desc}</p>
    </div>
  );
}