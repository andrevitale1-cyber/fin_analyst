"use client";
import React, { useState, useEffect } from 'react';
import { Check, X, Zap, ArrowRight, Loader2, ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';

// 🔴 1. COLE SEU LINK DO STRIPE AQUI 🔴
// Vá no Stripe > Catálogo > Links de Pagamento > Criar > Copie a URL (começa com https://buy.stripe.com/...)
const STRIPE_MONTHLY_URL = "https://buy.stripe.com/test_28E28s5vV5J43eX0H78ww00"; 

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const stored = localStorage.getItem('usuario');
    if (stored) setUser(JSON.parse(stored));
  }, []);

  const handleSubscribe = () => {
    setLoading(true);
    
    // Verifica se o link foi configurado
    if (STRIPE_MONTHLY_URL.includes("https://buy.stripe.com/test_28E28s5vV5J43eX0H78ww00")) {
      alert("Você precisa configurar o Link do Stripe no código (app/pricing/page.tsx)!");
      setLoading(false);
      return;
    }

    // Abre o checkout do Stripe em outra aba
    window.open(STRIPE_MONTHLY_URL, '_blank');
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#0E1117] text-white font-sans py-10 px-4 relative">
      
      {/* Botão de Voltar */}
      <button 
        onClick={() => router.push('/')} 
        className="absolute top-6 left-6 flex items-center gap-2 text-gray-500 hover:text-white transition-colors"
      >
        <ArrowLeft size={20} /> Voltar
      </button>

      <div className="max-w-7xl mx-auto text-center mb-16 mt-10">
        <h1 className="text-4xl md:text-5xl font-bold mb-6">
          Um único plano. <br />
          <span className="text-blue-500">Tudo o que você precisa.</span>
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          Sem pegadinhas. Escolha evoluir como investidor com a ajuda da IA.
        </p>

        {/* Toggle Mensal/Anual (Visual apenas, pois o link é fixo por enquanto) */}
        <div className="flex items-center justify-center gap-4 mt-8">
          <span className={`text-sm font-bold ${billingCycle === 'monthly' ? 'text-white' : 'text-gray-500'}`}>Mensal</span>
          <button 
            onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
            className="w-16 h-8 bg-gray-800 rounded-full p-1 relative transition-colors hover:bg-gray-700"
          >
            <div className={`w-6 h-6 bg-blue-500 rounded-full transition-transform duration-300 ${billingCycle === 'yearly' ? 'translate-x-8' : 'translate-x-0'}`} />
          </button>
          <span className={`text-sm font-bold ${billingCycle === 'yearly' ? 'text-white' : 'text-gray-500'}`}>Anual <span className="text-green-400 text-xs ml-1">(2 meses grátis)</span></span>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
        
        {/* CARD GRATUITO */}
        <div className="bg-[#161b22] border border-gray-800 rounded-3xl p-8 flex flex-col hover:border-gray-700 transition-colors">
          <div className="mb-8">
            <h3 className="text-xl font-bold text-white mb-2">Gratuito</h3>
            <p className="text-gray-400 text-sm">Para testar e conhecer a ferramenta.</p>
          </div>
          <div className="text-3xl font-bold mb-8">R$ 0<span className="text-sm text-gray-500 font-normal">/mês</span></div>
          
          <ul className="space-y-4 mb-8 flex-1">
            {/* Informações Atualizadas */}
            <FeatureItem text="5 Análises de IA por semana" active />
            <FeatureItem text="Upload de Arquivos Ilimitado" active />
            <FeatureItem text="Acesso ao Histórico Simples" active />
            <FeatureItem text="Suporte via Email" active />
            <FeatureItem text="Sem Download de PDF" no />
            <FeatureItem text="Sem Tabela Comparativa" no />
          </ul>

          <button 
            onClick={() => router.push('/dashboard')}
            className="w-full py-4 rounded-xl border border-gray-700 text-white font-bold hover:bg-gray-800 transition-all"
          >
            Continuar no Grátis
          </button>
        </div>

        {/* CARD PREMIUM */}
        <div className="bg-gradient-to-b from-blue-900/20 to-[#161b22] border border-blue-500/50 rounded-3xl p-8 flex flex-col relative overflow-hidden transform hover:-translate-y-1 transition-all duration-300 shadow-2xl shadow-blue-900/10">
          <div className="absolute top-0 right-0 bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-bl-xl">MAIS POPULAR</div>
          
          <div className="mb-8">
            <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
              Premium <Zap size={18} className="text-yellow-400 fill-yellow-400" />
            </h3>
            <p className="text-blue-200 text-sm">Para quem quer investir de verdade.</p>
          </div>

          <div className="text-4xl font-bold mb-8 text-white">
            {billingCycle === 'monthly' ? 'R$ 29' : 'R$ 290'}
            <span className="text-sm text-gray-400 font-normal">
              {billingCycle === 'monthly' ? '/mês' : '/ano'}
            </span>
          </div>
          
          <ul className="space-y-4 mb-8 flex-1">
            <FeatureItem text="Análises de IA Ilimitadas" active />
            <FeatureItem text="Upload Ilimitado" active />
            <FeatureItem text="Download do Relatório em PDF" active />
            <FeatureItem text="Tabela Comparativa Completa" active />
            <FeatureItem text="Prioridade no processamento" active />
            <FeatureItem text="Histórico Vitalício" active />
          </ul>

          <button 
            onClick={handleSubscribe}
            disabled={loading}
            className="w-full py-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold shadow-lg shadow-blue-900/20 transition-all hover:scale-[1.02] flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="animate-spin" /> : <>Assinar Agora <ArrowRight size={18} /></>}
          </button>
          <p className="text-center text-xs text-gray-500 mt-4">Cancelamento a qualquer momento.</p>
        </div>

      </div>
    </div>
  );
}

function FeatureItem({ text, active = false, no = false }: any) {
  return (
    <li className="flex items-center gap-3">
      {no ? (
        <div className="p-1 rounded-full bg-gray-800 text-gray-500"><X size={14} /></div>
      ) : (
        <div className={`p-1 rounded-full ${active ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-800 text-gray-300'}`}>
          <Check size={14} />
        </div>
      )}
      <span className={no ? 'text-gray-600 line-through' : 'text-gray-300'}>{text}</span>
    </li>
  );
}