"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import { 
  BarChart3, UploadCloud, ArrowRight, 
  FileText, Layout, Database, Check, X, CheckCircle2 
} from "lucide-react";

// Este componente segue a estrutura de "use client" e modularidade do modelo Petshop
export default function LandingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

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

          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-400">
            <Link href="#features" className="hover:text-white transition-colors">Funcionalidades</Link>
            <Link href="#how-it-works" className="hover:text-white transition-colors">Como Funciona</Link>
            <Link href="#pricing" className="hover:text-white transition-colors">Preços</Link>
          </div>

          <div className="flex items-center gap-4">
            <Link href="/login" className="px-5 py-2.5 text-sm font-medium hover:text-white transition-colors">
              Entrar
            </Link>
            <Link href="/register" className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-lg shadow-blue-900/20">
              Começar Agora
            </Link>
          </div>
        </div>
      </nav>

      {/* --- HERO SECTION --- */}
      <section className="relative pt-24 pb-32 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] bg-blue-600/10 blur-[120px] rounded-full -z-10" />
        
        <div className="max-w-7xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold tracking-wider uppercase mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
            </span>
            Nova Inteligência Artificial 2.0
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold text-white mb-8 tracking-tight leading-[1.1]">
            Analise Empresas em <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
              Segundos, não Horas.
            </span>
          </h1>
          
          <p className="max-w-2xl mx-auto text-gray-400 text-xl mb-12 leading-relaxed">
            Transforme relatórios complexos em insights acionáveis. Nossa IA processa balanços patrimoniais e DREs instantaneamente para você investir com confiança.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button className="w-full sm:w-auto px-8 py-4 bg-white text-[#0E1117] font-bold rounded-xl hover:bg-gray-200 transition-all flex items-center justify-center gap-2 group">
              Analisar agora gratuitamente
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </button>
            <button className="w-full sm:w-auto px-8 py-4 bg-gray-800/50 text-white font-bold rounded-xl border border-gray-700 hover:bg-gray-800 transition-all">
              Ver demonstração
            </button>
          </div>

          {/* Preview da Interface */}
          <div className="mt-20 relative max-w-5xl mx-auto">
            <div className="absolute inset-0 bg-blue-500/20 blur-[100px] -z-10" />
            <div className="rounded-2xl border border-gray-800 bg-gray-900/50 p-2 backdrop-blur-sm">
               <img 
                src="/demo-result.png" 
                alt="Dashboard Preview" 
                className="rounded-xl border border-gray-800 shadow-2xl"
              />
            </div>
          </div>
        </div>
      </section>

      {/* --- PRICING SECTION --- */}
      <section id="pricing" className="py-32 bg-[#0A0C10]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-20">
            <h2 className="text-4xl font-bold text-white mb-4">Planos que crescem com você</h2>
            <p className="text-gray-400">Escolha a melhor opção para sua jornada de investimento.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Exemplo de Card de Plano (Iniciante) */}
            <div className="p-8 rounded-3xl bg-gray-900/50 border border-gray-800 hover:border-blue-500/50 transition-all">
              <h3 className="text-xl font-bold mb-2">Iniciante</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-bold text-white">R$ 0</span>
                <span className="text-gray-500">/mês</span>
              </div>
              <ul className="space-y-4 mb-8">
                <Feature text="3 análises por mês" />
                <Feature text="Relatórios básicos" />
                <Feature text="Suporte via comunidade" />
                <Feature text="Histórico por 7 dias" disabled />
              </ul>
              <button className="w-full py-3 rounded-xl border border-gray-700 font-bold hover:bg-gray-800 transition-all">
                Começar Grátis
              </button>
            </div>

            {/* Plano Pro (Destaque) */}
            <div className="p-8 rounded-3xl bg-blue-600 border border-blue-400 relative shadow-2xl shadow-blue-900/20 scale-105">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-white text-blue-600 text-xs font-black px-3 py-1 rounded-full uppercase tracking-widest">
                Mais Popular
              </div>
              <h3 className="text-xl font-bold mb-2 text-white">Investidor Pro</h3>
              <div className="flex items-baseline gap-1 mb-6 text-white">
                <span className="text-4xl font-bold">R$ 49</span>
                <span className="opacity-70">/mês</span>
              </div>
              <ul className="space-y-4 mb-8">
                <Feature text="Análises Ilimitadas" active />
                <Feature text="Deep Learning de Balanços" active />
                <Feature text="Exportação em PDF/Excel" active />
                <Feature text="Suporte Prioritário" active />
              </ul>
              <button className="w-full py-3 rounded-xl bg-white text-blue-600 font-bold hover:bg-gray-100 transition-all">
                Assinar Pro
              </button>
            </div>

            {/* Plano Enterprise */}
            <div className="p-8 rounded-3xl bg-gray-900/50 border border-gray-800 transition-all">
              <h3 className="text-xl font-bold mb-2 text-white">Institucional</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-bold text-white">Sob consulta</span>
              </div>
              <ul className="space-y-4 mb-8">
                <Feature text="Acesso via API" />
                <Feature text="Múltiplos usuários" />
                <Feature text="White-label" />
                <Feature text="Consultoria dedicada" />
              </ul>
              <button className="w-full py-3 rounded-xl border border-gray-700 font-bold hover:bg-gray-800 transition-all">
                Falar com Vendas
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* --- FOOTER --- */}
      <footer className="border-t border-gray-800 py-20 bg-[#0E1117]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-12 mb-16">
            <div className="col-span-2">
              <div className="flex items-center gap-3 mb-6">
                <BarChart3 className="text-blue-500 w-8 h-8" />
                <span className="text-2xl font-bold text-white">FinAnalyzer.AI</span>
              </div>
              <p className="text-gray-400 max-w-sm leading-relaxed">
                A ferramenta definitiva para investidores modernos que buscam agilidade e precisão técnica no mercado de capitais.
              </p>
            </div>
            {/* Colunas de links seguindo o padrão modular */}
            <div>
              <h4 className="text-white font-bold mb-6">Produto</h4>
              <ul className="space-y-4 text-gray-400 text-sm">
                <li><Link href="#" className="hover:text-blue-400">Funcionalidades</Link></li>
                <li><Link href="#" className="hover:text-blue-400">Preços</Link></li>
                <li><Link href="#" className="hover:text-blue-400">API</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-6">Legal</h4>
              <ul className="space-y-4 text-gray-400 text-sm">
                <li><Link href="#" className="hover:text-blue-400">Termos de Uso</Link></li>
                <li><Link href="#" className="hover:text-blue-400">Privacidade</Link></li>
              </ul>
            </div>
          </div>
          
          <div className="pt-8 border-t border-gray-800">
             <p className="text-xs text-gray-500 leading-relaxed">
               <strong>Aviso Legal:</strong> As análises geradas são para fins informativos e de suporte. Elas não substituem a análise humana, nem constituem recomendação de compra ou venda de ativos. O FinAnalyzer.AI não se responsabiliza pela precisão dos dados. Rentabilidade passada não representa garantia de rentabilidade futura.
             </p>
             <p className="text-center pt-8 text-gray-600 text-sm">
               © 2026 FinAnalyzer Inc. Todos os direitos reservados.
             </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Subcomponentes auxiliares seguindo o padrão de design limpo
function Feature({ text, active = false, disabled = false }: { text: string; active?: boolean; disabled?: boolean }) {
  return (
    <li className="flex items-center gap-3">
      {disabled ? (
        <div className="p-0.5 rounded-full border border-gray-600 text-gray-500"><X size={12} /></div>
      ) : (
        <div className={`p-0.5 rounded-full border ${active ? 'bg-white/20 border-white/40 text-white' : 'bg-green-500/10 text-green-500 border-green-500/30'}`}>
          <Check size={12} />
        </div>
      )}
      <span className={`text-sm ${disabled ? 'text-gray-600 line-through' : active ? 'text-white' : 'text-gray-400'}`}>{text}</span>
    </li>
  );
}