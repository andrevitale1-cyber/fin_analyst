"use client";
import { useEffect, useRef, useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useLocale } from 'next-intl';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

export default function AnalysisMarketChart({ symbol, compact = false }: { symbol: string; compact?: boolean }) {
  const { getToken, userId } = useAuth();
  const tokenRef = useRef(getToken);
  tokenRef.current = getToken;
  const locale = useLocale();
  const [period, setPeriod] = useState('1mo');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!userId || !symbol.trim()) { setData(null); setLoading(false); return; }
    const controller = new AbortController();
    setLoading(true); setData(null);
    tokenRef.current().then(token => fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api-finanalyzer.onrender.com'}/api/market-data?symbol=${encodeURIComponent(symbol)}&range=${compact ? '1d&quote_only=true' : period}`, { signal: controller.signal, headers: { Authorization: `Bearer ${token}` } }))
      .then(response => { if (!response.ok) throw new Error(); return response.json(); })
      .then(value => { if (!controller.signal.aborted) { setData(value); setLoading(false); } })
      .catch(() => { if (!controller.signal.aborted) { setData(null); setLoading(false); } });
    return () => controller.abort();
  }, [symbol, period, compact, userId]);
  const money = (value: number) => new Intl.NumberFormat(locale === 'en' ? 'en-US' : 'pt-BR', data?.currency ? { style: 'currency', currency: data.currency, maximumFractionDigits: 2 } : { maximumFractionDigits: 2 }).format(value);
  const points = data?.points || [];
  const firstPrice = points[0]?.close;
  const lastPrice = points[points.length - 1]?.close;
  const change = compact || period === '1d'
    ? (typeof data?.changePercent === 'number' ? data.changePercent : null)
    : points.length > 1 && firstPrice > 0 ? (lastPrice / firstPrice - 1) * 100 : null;
  const asOf = data?.asOf ? new Date(typeof data.asOf === 'number' ? data.asOf * 1000 : data.asOf).toLocaleString(locale === 'en' ? 'en-US' : 'pt-BR') : '';
  const historyMessage = data?.unavailableReason === 'plan_range'
    ? (locale === 'en' ? 'The data plan does not include this range. Select 1M or 5D.' : 'O plano de dados não inclui este período. Selecione 1M ou 5D.')
    : data?.unavailableReason === 'plan_interval'
      ? (locale === 'en' ? 'Intraday history is not included in the data plan. The latest quote remains available; select 5D or 1M for daily closes.' : 'O plano de dados não inclui histórico intradiário. A cotação continua disponível; selecione 5D ou 1M para ver os fechamentos diários.')
      : (locale === 'en' ? 'Price history temporarily unavailable for this range.' : 'Histórico temporariamente indisponível para este período.');
  const quote = <span title={asOf ? `${data?.source} · ${asOf}` : undefined} className="flex flex-wrap items-baseline gap-x-2 text-sm"><strong>{typeof data?.price === 'number' ? money(data.price) : '—'}</strong>{change !== null && <span className={change >= 0 ? 'text-emerald-500' : 'text-red-500'}>{change > 0 ? '+' : ''}{change.toFixed(2)}%</span>}</span>;
  if (compact && !loading && !data?.available) return <span className="text-[10px] text-slate-500">{locale === 'en' ? 'Quote unavailable' : 'Cotação indisponível'}</span>;
  if (compact) return <span>{quote}{asOf && <span className="block text-[9px] text-slate-500">{asOf}</span>}</span>;
  return <section aria-label={locale === 'en' ? 'Share price' : 'Cotação da ação'} className="my-6 rounded-2xl border border-slate-200 bg-white p-5 text-slate-900">
    <div className="flex flex-wrap items-center justify-between gap-4"><div><h2 className="text-lg font-semibold">{symbol}</h2>{quote}</div><div role="group" aria-label={locale === 'en' ? 'Chart range' : 'Período do gráfico'} className="flex flex-wrap gap-1">{[['1d','1D'],['5d','5D'],['1mo','1M'],['6mo','6M'],['1y','1Y'],['max',locale === 'en' ? 'All time' : 'Máx.']].map(([value,label]) => <button key={value} onClick={() => setPeriod(value)} aria-pressed={period === value} className={`min-h-10 rounded-lg px-3 text-sm ${period === value ? 'bg-sky-100 text-sky-800' : 'text-slate-500 hover:bg-slate-50'}`}>{label}</button>)}</div></div>
    {loading ? <p role="status" className="py-16 text-center text-sm text-slate-500">{locale === 'en' ? 'Loading prices…' : 'Carregando cotações…'}</p> : data?.points?.length > 1 ? <div className="mt-6 h-64 w-full"><ResponsiveContainer width="100%" height="100%"><AreaChart data={data.points}><XAxis dataKey="time" minTickGap={60} tickFormatter={value => String(value).slice(0,10)} tick={{fontSize:11}}/><YAxis domain={['auto','auto']} width={60} tick={{fontSize:11}}/><Tooltip formatter={(value:any) => money(Number(value))}/><Area type="monotone" dataKey="close" name={locale === 'en' ? 'Price' : 'Cotação'} stroke="#0284c7" fill="#e0f2fe" strokeWidth={2} isAnimationActive={false}/></AreaChart></ResponsiveContainer></div> : <p role="status" className="py-16 text-center text-sm text-slate-500">{historyMessage}</p>}
    {data?.points?.length > 1 && data?.interval === '1d' && <p className="mt-3 text-xs text-slate-500">{locale === 'en' ? 'Daily closing prices' : 'Preços de fechamento diário'}</p>}
    {data?.source && <p className="mt-3 text-xs text-slate-500"><a href={data.sourceUrl} target="_blank" rel="noopener noreferrer" className="underline">{data.source}</a>{asOf ? ` · ${asOf}` : ''}{data.points?.length ? ` · ${String(data.points[0].time).slice(0,10)} → ${String(data.points[data.points.length-1].time).slice(0,10)}` : ''} · {locale === 'en' ? 'Coverage and historical depth depend on the data provider.' : 'Cobertura e extensão do histórico dependem do provedor.'}</p>}
  </section>;
}
