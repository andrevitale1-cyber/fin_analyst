"use client";
import { useEffect, useRef, useState } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';
import { useLocale } from 'next-intl';
import CompanyLogo from './CompanyLogo';
import AnalysisMarketChart from './AnalysisMarketChart';
import { formatPeriod } from '../lib/analysisText';
import Link from 'next/link';

export default function RecentAnalyses({ onSelect }: { onSelect?: (item: any) => void }) {
  const { user } = useUser();
  const { getToken } = useAuth();
  const tokenRef = useRef(getToken);
  tokenRef.current = getToken;
  const locale = useLocale();
  const [items,setItems] = useState<any[]>([]);
  useEffect(() => {
    const controller = new AbortController(); setItems([]);
    if (!user) return;
    tokenRef.current().then(token => fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api-finanalyzer.onrender.com'}/api/recent-analyses`, {signal:controller.signal,headers:{Authorization:`Bearer ${token}`}}))
      .then(r => { if (!r.ok) throw new Error(); return r.json(); }).then(rows => { if (!controller.signal.aborted) setItems(Array.isArray(rows) ? rows : []); }).catch(() => {});
    return () => controller.abort();
  },[user?.id]);
  return <section className="mt-6 mb-5"><div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-slate-500"><span className="h-px flex-1 bg-white/10"/>{locale === 'en' ? 'Last Analysis' : 'Últimas análises'}<span className="h-px flex-1 bg-white/10"/></div>
    {items.length === 0 ? <p className="mt-4 px-2 text-xs text-slate-500">{locale === 'en' ? 'Your recent analyses appear here.' : 'Suas análises recentes aparecem aqui.'}</p> : items.map(item => <div key={item.id} className="mt-3 rounded-xl p-2 hover:bg-white/5"><Link href={`/${locale}/dashboard?analysis=${item.id}`} onClick={event => { if (onSelect && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) { event.preventDefault(); onSelect(item); } }} className="flex items-center gap-2"><CompanyLogo small symbol={item.symbol} company={item.symbol}/><span className="font-semibold text-sm text-white">{item.symbol}</span><span className="ml-auto text-[10px] text-slate-400">{formatPeriod(item.result?.metadata?.periodo,locale)}</span></Link><div className="ml-6 mt-1 text-slate-300"><AnalysisMarketChart symbol={item.symbol} compact/></div></div>)}
  </section>;
}
