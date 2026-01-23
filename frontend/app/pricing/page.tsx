"use client";
import React, { useState, useEffect } from 'react';
import { Check, X, Zap, ArrowRight, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const stored = localStorage.getItem('usuario');
    if (stored) setUser(JSON.parse(stored));
  }, []);

  const handleSubscribe = async () => {
    if (!user) {
      router.push('/login');
      return;
    }
    
    setLoading(true);
    try {
      const res = await fetch('https://api-finanalyzer.onrender.com/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id })
      });
      
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url; // Redireciona para o Stripe
      }
    } catch (error) {
      alert("Erro ao conectar com pagamento.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0E1117] text-white font-sans py-20 px-4">
      <div className="max-w-7xl mx-auto text-center mb-16">
        <h1 className="text-4xl md:text-5xl font-bold mb-6">
          Um único plano. <br />
          <span className="text-blue-500">Tudo o que você precisa.</span>
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          Sem pegadinhas. Escolha evoluir como investidor com a ajuda da IA.
        </p>

        {/* Toggle Mensal/Anual */}
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
        <div className="bg-[#161b22] border border-gray-800 rounded-3xl p-8 flex flex-col">
          <div className="mb-8">
            <h3 className="text-xl font-bold text-white mb-2">Gratuito</h3>
            <p className="text-gray-400 text-sm">Para testar e conhecer a ferramenta.</p>
          </div>
          <div className="text-3xl font-bold mb-8">R$ 0<span className="text-sm text-gray-500 font-normal">/mês</span></div>
          
          <ul className="space-y-4 mb-8 flex-1">
            <FeatureItem text="1 Análise de IA por dia" />
            <FeatureItem text="Acesso ao Histórico Básico" />
            <FeatureItem text="Upload de PDFs até 5MB" />
            <FeatureItem text="Suporte via Email" />
            <FeatureItem text="Sem acesso a Tabela Comparativa" no />
          </ul>

          <button className="w-full py-4 rounded-xl border border-gray-700 text-white font-bold hover:bg-gray-800 transition-all">
            Já estou usando
          </button>
        </div>

        {/* CARD PREMIUM */}
        <div className="bg-gradient-to-b from-blue-900/20 to-[#161b22] border border-blue-500/50 rounded-3xl p-8 flex flex-col relative overflow-hidden">
          <div className="absolute top-0 right-0 bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-bl-xl">MAIS POPULAR</div>
          
          <div className="mb-8">
            <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
              Premium <Zap size={18} className="text-yellow-400 fill-yellow-400" />
            </h3>
            <p className="text-blue-200 text-sm">Para quem quer investir de verdade.</p>
          </div>

          <div className="text-4xl font-bold mb-8 text-white">
            {billingCycle === 'monthly' ? 'R$ 49' : 'R$ 490'}
            <span className="text-sm text-gray-400 font-normal">
              {billingCycle === 'monthly' ? '/mês' : '/ano'}
            </span>
          </div>
          
          <ul className="space-y-4 mb-8 flex-1">
            <FeatureItem text="Análises de IA Ilimitadas" active />
            <FeatureItem text="Upload de PDFs grandes (50MB+)" active />
            <FeatureItem text="Acesso à Tabela Comparativa" active />
            <FeatureItem text="Prioridade no processamento" active />
            <FeatureItem text="Novas features em primeira mão" active />
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