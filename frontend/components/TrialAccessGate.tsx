"use client";
import { useEffect, useState } from 'react';
import { useAuth, UserButton } from '@clerk/nextjs';
import { useLocale } from 'next-intl';
import Link from 'next/link';

export default function TrialAccessGate({ children }: { children: React.ReactNode }) {
  const { userId, isLoaded, getToken } = useAuth();
  const locale = useLocale();
  const en = locale === 'en';
  const [access, setAccess] = useState<{ owner: string; state: 'active' | 'expired' | 'error' } | null>(null);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!isLoaded || !userId) return;
    const controller = new AbortController();
    let stopped = false;
    const check = async () => {
      const timeout = setTimeout(() => controller.abort(), 20_000);
      try {
        const token = await getToken();
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api-finanalyzer.onrender.com'}/api/check-access?user_id=${encodeURIComponent(userId)}`, {signal:controller.signal,headers:{Authorization:`Bearer ${token}`},cache:'no-store'});
        if (!response.ok) throw new Error();
        const data = await response.json();
        if (typeof data.has_access !== 'boolean') throw new Error();
        if (!controller.signal.aborted) setAccess({owner:userId,state:data.has_access ? 'active' : 'expired'});
      } catch { if (!stopped) setAccess({owner:userId,state:'error'}); }
      finally { clearTimeout(timeout); }
    };
    void check();
    const timer = setInterval(check, 60_000);
    return () => { stopped = true; controller.abort(); clearInterval(timer); };
  }, [userId,isLoaded,getToken,retry]);
  const state = access?.owner === userId ? access?.state : null;
  if (state === 'active') return children;
  return <main className="flex min-h-screen items-center justify-center bg-[#f7f8fc] p-6 text-slate-900"><section className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
    <div className="mb-6 flex items-center justify-between"><Link href={`/${locale}`} className="text-xl font-bold">FinAnalyzer</Link><UserButton/></div>
    {!state ? <p role="status">{en ? 'Checking your access…' : 'Verificando seu acesso…'}</p> : state === 'expired' ? <><h1 className="text-2xl font-semibold">{en ? 'Your 7-day trial has ended' : 'Seu teste de 7 dias terminou'}</h1><p className="mt-3 leading-relaxed text-slate-600">{en ? 'Continue with Premium for R$ 29/month: 50 quarterly or call analyses per month, tables, history and company reports. Your saved analyses are preserved.' : 'Continue com o Premium por R$ 29/mês: 50 análises de resultados ou calls por mês, tabela, histórico e relatórios de empresas. Suas análises salvas estão preservadas.'}</p><a href={`https://buy.stripe.com/bJe3cwgdleEBfiJ9rT67S00?client_reference_id=${encodeURIComponent(userId || "")}`} className="mt-6 block rounded-xl bg-[#1a1aff] px-5 py-3 text-center font-semibold text-white">{en ? 'Subscribe to Premium · R$ 29/month' : 'Assinar Premium · R$ 29/mês'}</a><Link href={`/${locale}#planos`} className="mt-4 block text-center text-sm font-semibold text-sky-700">{en ? 'Compare plans' : 'Comparar planos'}</Link></> : <><p role="alert">{en ? 'We could not verify your access.' : 'Não foi possível verificar seu acesso.'}</p><button onClick={() => setRetry(value => value+1)} className="mt-4 font-semibold text-sky-700">{en ? 'Try again' : 'Tentar novamente'}</button></>}
  </section></main>;
}
