"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useLocale } from 'next-intl';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { ArrowRight, ChartNoAxesCombined, CircleAlert, FileText, History, Loader2, Lock, RefreshCw, Scale, Swords, Trophy } from 'lucide-react';
import CompanyLogo from './CompanyLogo';
import { formatPeriod, splitBold } from '../lib/analysisText';

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api-finanalyzer.onrender.com';
const COLORS = ['#0284c7', '#7c3aed', '#059669'];
type Scores = Record<string, number | null>;
type Analysis = { id: number; symbol: string; company: string; year: number; quarter: number; period: string; period_end: string | null; scores: Scores; created_at: string; scoring_version: string; sector: string; duel_eligible: boolean; source: {name: string; url: string | null}; side?: 'A' | 'B' };
type Dimension = {id: string; winner: string; left_assessment: string; right_assessment: string; reason: string; left_quote: string | null; right_quote: string | null; left_supporting_quotes?: string[]; right_supporting_quotes?: string[]};
type Calculated = {side: string; metric: string; basis: string; accounting_basis: string; unit: string; currency: string | null; current: number; previous: number; change: number; growth_pct: number | null};
type Duel = {id: string; state: string; stage: string; error_code?: string; created_at: string; locale: string; participants: Analysis[]; content?: {verdict: string; confidence: string; summary: string; conclusion: string; dimensions: Dimension[]; watchpoints: {side: string; text: string; quote: string; supporting_quotes?: string[]}[]; comparisons: Calculated[]; charged: boolean}};

function Copy({text}: {text: string}) {
  return <>{splitBold(text).map((part, i) => part.bold ? <strong key={i} className="font-semibold text-slate-900">{part.text}</strong> : part.text)}</>;
}

export default function CompanyComparison({ premium, onUpgrade, onOpenAnalysis, onUsageChange }: {
  premium: boolean; onUpgrade: () => void; onOpenAnalysis: (id: number) => void; onUsageChange: () => void;
}) {
  const locale = useLocale(), en = locale === 'en';
  const { getToken } = useAuth();
  const [tab, setTab] = useState<'history' | 'duel'>('history');
  const [records, setRecords] = useState<Analysis[]>([]);
  const [history, setHistory] = useState<Duel[]>([]);
  const [loading, setLoading] = useState(true), [error, setError] = useState('');
  const [retry, setRetry] = useState(0), [locked, setLocked] = useState(false);
  const [selected, setSelected] = useState<string[]>(['', '', '']);
  const [metric, setMetric] = useState('nota_geral');
  const [from, setFrom] = useState(''), [to, setTo] = useState('');
  const [leftSymbol, setLeftSymbol] = useState(''), [rightSymbol, setRightSymbol] = useState('');
  const [leftId, setLeftId] = useState(''), [rightId, setRightId] = useState('');
  const [starting, setStarting] = useState(false), [duelError, setDuelError] = useState('');
  const [jobId, setJobId] = useState(''), [job, setJob] = useState<Duel | null>(null), [pollRevision, setPollRevision] = useState(0);
  const usageCallback = useRef(onUsageChange);
  usageCallback.current = onUsageChange;
  const metrics = en ? {nota_geral:'Overall score', receita_nota:'Revenue', lucro_nota:'Net income', divida_nota:'Net debt', rentabilidade_nota:'Profitability'} : {nota_geral:'Nota geral', receita_nota:'Receita', lucro_nota:'Lucro líquido', divida_nota:'Dívida líquida', rentabilidade_nota:'Rentabilidade'};
  const dimensions: Record<string, string> = en ? {growth:'Growth', profitability:'Profitability', cash:'Cash generation', balance:'Balance sheet', outlook:'Outlook'} : {growth:'Crescimento', profitability:'Rentabilidade', cash:'Geração de caixa', balance:'Balanço', outlook:'Perspectivas'};
  const metricNames: Record<string, string> = en ? {revenue:'Revenue',net_income:'Net income',operating_margin:'Operating margin',gross_margin:'Gross margin',operating_cash_flow:'Operating cash flow',free_cash_flow:'Free cash flow',net_debt:'Net debt',roe:'ROE',credit_loss:'Credit losses',capital_ratio:'Capital ratio',eps:'EPS',same_store_sales:'Same-store sales'} : {revenue:'Receita',net_income:'Lucro líquido',operating_margin:'Margem operacional',gross_margin:'Margem bruta',operating_cash_flow:'Fluxo de caixa operacional',free_cash_flow:'Fluxo de caixa livre',net_debt:'Dívida líquida',roe:'ROE',credit_loss:'Custo de crédito',capital_ratio:'Índice de capital',eps:'LPA',same_store_sales:'Vendas mesmas lojas'};
  const date = (value: string | null) => value && !Number.isNaN(new Date(value).getTime()) ? new Intl.DateTimeFormat(en ? 'en-US' : 'pt-BR', {timeZone:'UTC',dateStyle:'medium'}).format(new Date(value)) : (en ? 'End date not identified' : 'Encerramento não identificado');
  const request = useCallback(async (path: string, init: RequestInit = {}) => {
    const token = await getToken();
    if (!token) throw new Error(en ? 'Please sign in again.' : 'Entre novamente para continuar.');
    const response = await fetch(API + '/api/company-comparison' + path, {cache:'no-store', ...init, headers: {...init.headers, Authorization:`Bearer ${token}`, 'Content-Type':'application/json'}});
    if (response.status === 403) { setLocked(true); throw new Error(en ? 'Premium required.' : 'Recurso exclusivo do Premium.'); }
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(typeof body.detail === 'string' ? body.detail : (en ? 'Could not load comparison. Please try again.' : 'Não foi possível carregar a comparação. Tente novamente.'));
    }
    return response.json();
  }, [getToken, en]);

  useEffect(() => {
    if (!premium) { setLoading(false); return; }
    const controller = new AbortController();
    setLoading(true); setError('');
    Promise.all([request('/analyses', {signal:controller.signal}), request('/duels', {signal:controller.signal})])
      .then(([data, past]) => {
        if (controller.signal.aborted) return;
        setRecords(data.analyses); setHistory(past.duels);
        const symbols = [...new Set<string>(data.analyses.map((r: Analysis) => r.symbol))];
        setSelected(old => old.some(Boolean) ? old : [symbols[0] || '', symbols[1] || '', '']);
        setLeftSymbol(old => old || symbols[0] || ''); setRightSymbol(old => old || symbols[1] || '');
        setLeftId(old => old || String(data.analyses.find((r:Analysis) => r.symbol === symbols[0])?.id || ''));
        setRightId(old => old || String(data.analyses.find((r:Analysis) => r.symbol === symbols[1])?.id || ''));
        const target = new URLSearchParams(window.location.search).get('duel');
        if (target) { setJobId(target); setTab('duel'); }
      }).catch(err => { if (!controller.signal.aborted) setError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [premium, retry, request]);

  useEffect(() => {
    if (!jobId || !premium) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    setDuelError('');
    async function poll() {
      try {
        const next: Duel = await request('/duels/' + encodeURIComponent(jobId), {signal:controller.signal});
        if (controller.signal.aborted) return;
        setJob(next);
        if (['queued','running'].includes(next.state)) timer = setTimeout(poll, 2200);
        else {
          usageCallback.current();
          const saved = await request('/duels', {signal:controller.signal});
          if (!controller.signal.aborted) setHistory(saved.duels);
        }
      } catch (err) {
        if (!controller.signal.aborted) setDuelError(err instanceof Error ? err.message : (en ? 'Could not open this duel.' : 'Não foi possível abrir o duelo.'));
      }
    }
    void poll();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [jobId, pollRevision, premium, request, en]);

  const companies = useMemo(() => [...new Set(records.map(r => r.symbol))].sort(), [records]);
  const years = useMemo(() => [...new Set(records.map(r => r.year))].sort((a,b) => a-b), [records]);
  const latest = useMemo(() => {
    const result = new Map<string, Analysis>();
    for (const record of records) {
      const key = `${record.symbol}:${record.year}:${record.quarter}`;
      if (!result.has(key) || result.get(key)!.id < record.id) result.set(key, record);
    }
    return result;
  }, [records]);
  const series = selected.filter(Boolean);
  const chart = useMemo(() => {
    const inRange = [...latest.values()].filter(r => selected.includes(r.symbol) && (!from || r.year >= Number(from)) && (!to || r.year <= Number(to)));
    if (!inRange.length) return [];
    const ordinals = inRange.map(r => r.year*4+r.quarter-1), rows: Record<string, any>[] = [];
    for (let ordinal=Math.min(...ordinals); ordinal<=Math.max(...ordinals); ordinal++) {
      const year = Math.floor(ordinal/4), quarter = ordinal%4+1;
      const row: Record<string, any> = {period:`${quarter}${en ? 'Q':'T'}/${year}`};
      selected.filter(Boolean).forEach((symbol,i) => { const record = latest.get(`${symbol}:${year}:${quarter}`); row[`s${i}`] = record?.scores[metric] ?? null; row[`a${i}`] = record; });
      rows.push(row);
    }
    return rows;
  }, [latest, selected, from, to, metric, en]);
  const versions = new Set([...latest.values()].filter(r => series.includes(r.symbol)).map(r => r.scoring_version));
  const left = records.find(r => r.id === Number(leftId)), right = records.find(r => r.id === Number(rightId));
  const formatValue = (value: number, unit: string, currency: string | null) => {
    const number = new Intl.NumberFormat(en ? 'en-US' : 'pt-BR', {maximumFractionDigits:2}).format(value);
    const suffix: Record<string,string> = {currency_thousands:en?'K':' mil', currency_millions:en?'M':' mi', currency_billions:en?'B':' bi'};
    return unit === 'percent' ? `${number}%` : unit === 'ratio' ? `${number}x` : `${currency ? currency+' ' : ''}${number}${suffix[unit]||''}`;
  };

  function openJob(id: string) {
    const saved = history.find(item => item.id === id);
    if (saved) {
      const a = saved.participants.find(p => p.side==='A'), b = saved.participants.find(p => p.side==='B');
      if (a && b) { setLeftSymbol(a.symbol); setLeftId(String(a.id)); setRightSymbol(b.symbol); setRightId(String(b.id)); }
    }
    setTab('duel'); setJob(null); setJobId(id); setPollRevision(value => value+1);
    window.history.replaceState(null, '', `/${locale}/dashboard?view=comparison&duel=${encodeURIComponent(id)}`);
  }
  async function start() {
    if (!left || !right || starting) return;
    setStarting(true); setDuelError('');
    try {
      const next = await request('/duels', {method:'POST',body:JSON.stringify({left_id:left.id,right_id:right.id,locale})});
      openJob(next.id); usageCallback.current();
    } catch (err) { setDuelError(err instanceof Error ? err.message : (en ? 'Could not start duel.' : 'Não foi possível iniciar o duelo.')); }
    finally { setStarting(false); }
  }
  const classSelect = 'mt-2 w-full min-w-0 rounded-xl border border-slate-200 bg-white px-3 py-3 text-base text-slate-900 focus:border-sky-500 focus:outline-none';
  const result = job?.content;
  const bySide = (side: string) => job?.participants.find(p => p.side === side);
  const winnerText = (winner: string) => winner === 'tie' ? (en ? 'Tie' : 'Empate') : winner === 'insufficient' ? (en ? 'Insufficient evidence' : 'Evidência insuficiente') : bySide(winner)?.symbol || winner;

  return <section className="mx-auto max-w-6xl pb-12" aria-labelledby="comparison-heading">
    <header className="mb-7"><p className="mb-2 text-xs font-bold uppercase tracking-[.16em] text-sky-700">Premium</p><h1 id="comparison-heading" className="text-3xl font-bold tracking-tight text-slate-900">{en ? 'Compare Companies' : 'Comparar Empresas'}</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">{en ? 'Track fundamentals over time and compare the strength of two quarterly results, using your saved analyses.' : 'Acompanhe os fundamentos ao longo do tempo e compare a qualidade de dois resultados trimestrais usando suas análises salvas.'}</p></header>
    {!premium || locked ? <div className="rounded-3xl border border-sky-100 bg-white p-8"><Lock className="mb-4 text-sky-600"/><h2 className="text-xl font-semibold text-slate-900">{en ? 'A clearer view with Premium' : 'Uma visão mais completa com o Premium'}</h2><p className="mt-3 max-w-xl text-sm leading-6 text-slate-500">{en ? 'Compare up to three score histories and ask AI to judge two quarterly results. Saved duels reopen without using your allowance.' : 'Compare o histórico de até três empresas e peça à IA uma avaliação de dois resultados trimestrais. Duelo salvo pode ser reaberto sem usar sua franquia.'}</p><button onClick={()=>{if(premium){setLocked(false);setRetry(v=>v+1);}else onUpgrade();}} className="mt-6 rounded-xl bg-sky-600 px-5 py-3 text-sm font-bold text-white">{premium?(en?'Refresh access':'Atualizar acesso'):(en ? 'See Premium plans' : 'Ver planos Premium')}</button></div> : <>
      <div role="tablist" aria-label={en ? 'Comparison tools' : 'Ferramentas de comparação'} className="mb-6 flex gap-2 rounded-2xl border border-slate-200 bg-white p-2">{(['history','duel'] as const).map(value => <button key={value} id={`comparison-tab-${value}`} role="tab" aria-selected={tab===value} aria-controls={`comparison-panel-${value}`} onClick={()=>setTab(value)} className={`flex flex-1 items-center justify-center gap-2 rounded-xl px-3 py-3 text-sm font-semibold transition ${tab===value ? 'bg-sky-50 text-sky-700' : 'text-slate-500 hover:bg-slate-50'}`}>{value==='history' ? <ChartNoAxesCombined size={18}/> : <Swords size={18}/>}<span>{value==='history' ? (en ? 'Score history' : 'Evolução das notas') : (en ? 'Results duel' : 'Duelo de resultados')}</span></button>)}</div>
      {loading ? <div role="status" className="flex items-center gap-3 rounded-2xl bg-white p-8 text-slate-500"><Loader2 className="animate-spin" size={20}/>{en ? 'Loading saved analyses…' : 'Carregando análises salvas…'}</div> : error ? <div role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">{error}<button onClick={()=>setRetry(v=>v+1)} className="mt-4 flex items-center gap-2 font-semibold"><RefreshCw size={16}/>{en ? 'Try again' : 'Tentar novamente'}</button></div> : !records.length ? <div className="rounded-2xl border border-slate-200 bg-white p-8 text-slate-600"><h2 className="font-semibold text-slate-900">{en ? 'Start with a quarterly analysis' : 'Comece com uma análise trimestral'}</h2><p className="mt-3 text-sm leading-6">{en ? 'Your quarterly analyses will appear here. Calls have no numerical scores and are not included in these comparisons.' : 'Suas análises trimestrais aparecerão aqui. Calls não recebem notas numéricas e não entram nesta comparação.'}</p></div> : <>
      <div role="tabpanel" id="comparison-panel-history" aria-labelledby="comparison-tab-history" hidden={tab!=='history'}>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 sm:p-7">
          <div className="grid gap-4 sm:grid-cols-3">{selected.map((symbol,index)=><div key={index}><label htmlFor={`compare-company-${index}`} className="text-xs font-semibold uppercase tracking-wide text-slate-500">{en ? 'Company' : 'Empresa'} {index+1}{index===2 ? (en ? ' · optional':' · opcional') : ''}</label><select id={`compare-company-${index}`} className={classSelect} value={symbol} onChange={event=>setSelected(previous=>previous.map((value,i)=>i===index ? event.target.value:value))}><option value="">{en ? 'Select company' : 'Selecionar empresa'}</option>{companies.map(company=><option key={company} disabled={selected.includes(company)&&company!==symbol} value={company}>{company}</option>)}</select></div>)}</div>
          <div className="mt-5 grid gap-4 border-t border-slate-100 pt-5 sm:grid-cols-[2fr_1fr_1fr]"><label className="text-xs font-semibold text-slate-500">{en ? 'Indicator' : 'Indicador'}<select className={classSelect} value={metric} onChange={e=>setMetric(e.target.value)}>{Object.entries(metrics).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label><label className="text-xs font-semibold text-slate-500">{en ? 'From year' : 'Do ano'}<select className={classSelect} value={from} onChange={e=>{setFrom(e.target.value);if(to&&Number(e.target.value)>Number(to))setTo('');}}><option value="">{en ? 'All' : 'Todos'}</option>{years.map(year=><option key={year} value={year}>{year}</option>)}</select></label><label className="text-xs font-semibold text-slate-500">{en ? 'To year' : 'Até o ano'}<select className={classSelect} value={to} onChange={e=>setTo(e.target.value)}><option value="">{en ? 'All' : 'Todos'}</option>{years.filter(year=>!from||year>=Number(from)).map(year=><option key={year} value={year}>{year}</option>)}</select></label></div>
          <div className="mt-6 flex flex-wrap gap-4">{series.map((symbol,index)=><div key={symbol} className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2"><CompanyLogo symbol={symbol} company={symbol} small/><span className="text-sm font-semibold" style={{color:COLORS[index]}}>{symbol}</span></div>)}</div>
          {chart.length && chart.some(row=>series.some((_,i)=>row[`s${i}`]!=null)) ? <div className="mt-5 h-80 min-w-0" role="group" aria-label={en ? 'Company scores by fiscal quarter. The accessible table follows.' : 'Notas por trimestre fiscal. A tabela acessível está abaixo.'}>{tab==='history'&&<ResponsiveContainer width="100%" height="100%" minWidth={0}><LineChart data={chart} margin={{top:16,right:18,left:-20,bottom:8}}><CartesianGrid vertical={false} stroke="#e2e8f0" strokeDasharray="3 5"/><XAxis dataKey="period" tick={{fontSize:11,fill:'#64748b'}} minTickGap={22}/><YAxis domain={[1,5]} ticks={[1,2,3,4,5]} tick={{fontSize:12,fill:'#64748b'}} allowDecimals={false}/><Tooltip formatter={(value,name)=>[`${value}/5`,name]} contentStyle={{borderRadius:12,borderColor:'#e2e8f0'}}/><Legend/>{series.map((symbol,index)=><Line key={symbol} dataKey={`s${index}`} name={symbol} stroke={COLORS[index]} strokeWidth={2.5} connectNulls={false} isAnimationActive={false} dot={(props:any)=>{const record=props.payload?.['a'+index];if(!record||props.value==null)return <g key={props.index}/>;return <g key={props.payload.period} transform={'translate('+props.cx+','+props.cy+')'} role="button" tabIndex={0} aria-label={symbol+' '+props.payload.period+': '+props.value+'/5'} onClick={()=>onOpenAnalysis(record.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onOpenAnalysis(record.id);}}} className="cursor-pointer"><circle r={13} fill="transparent"/><circle r={4} fill="white" stroke={COLORS[index]} strokeWidth={2}/></g>;}} activeDot={false}/>)}</LineChart></ResponsiveContainer>}</div> : <p className="py-12 text-center text-sm text-slate-500">{en ? 'No scores in this selection.' : 'Sem notas nesta seleção.'}</p>}
          <p className="mt-3 text-xs leading-5 text-slate-500">{en ? 'Score tracking does not use your allowance. Fiscal quarters. Gaps mean no saved score; no values are estimated. For duplicate periods, the latest analysis is shown. Select a score in the table to open its analysis.' : 'Este acompanhamento não consome sua franquia. Trimestres fiscais. Lacunas indicam ausência de nota salva; não estimamos valores. Em períodos repetidos, mostramos a análise mais recente. Selecione uma nota na tabela para abrir a análise.'}</p>
          {(versions.has('legacy-unknown')||versions.size>1)&&<p className="mt-4 flex gap-2 rounded-xl bg-amber-50 p-3 text-xs leading-5 text-amber-900"><CircleAlert className="mt-0.5 shrink-0" size={15}/>{en ? 'Methodology note: some historical scores use an older or unidentified rubric. They are preserved as originally published and may not be directly comparable.' : 'Nota metodológica: algumas notas históricas usam critérios antigos ou sem versão identificada. Elas foram preservadas e podem não ser diretamente comparáveis.'}</p>}
          {!!chart.length&&<div className="mt-6 overflow-x-auto"><table className="w-full text-left text-sm"><caption className="mb-3 text-left font-semibold text-slate-900">{en ? 'Scores by quarter' : 'Notas por trimestre'}</caption><thead className="border-b border-slate-200 text-xs text-slate-500"><tr><th className="p-3">{en ? 'Fiscal quarter':'Trimestre fiscal'}</th>{series.map(symbol=><th key={symbol} className="p-3">{symbol}</th>)}</tr></thead><tbody>{chart.map(row=><tr key={row.period} className="border-b border-slate-100"><th className="whitespace-nowrap p-3 font-medium text-slate-600">{row.period}</th>{series.map((symbol,index)=><td key={symbol} className="p-3">{row[`s${index}`]==null ? <span className="text-slate-400">—</span> : <button onClick={()=>onOpenAnalysis(row[`a${index}`].id)} title={date(row[`a${index}`].period_end)} className="rounded-lg px-2 py-1 font-semibold text-sky-700 hover:bg-sky-50 focus-visible:outline-2 focus-visible:outline-sky-600" aria-label={`${symbol} ${row.period}: ${row[`s${index}`]}/5`}>{row[`s${index}`]}/5 <ArrowRight size={12} className="inline"/></button>}</td>)}</tr>)}</tbody></table></div>}
        </div>
      </div>
      <div role="tabpanel" id="comparison-panel-duel" aria-labelledby="comparison-tab-duel" hidden={tab!=='duel'}>
        <div className="rounded-3xl border border-slate-200 bg-white p-5 sm:p-7"><h2 className="flex items-center gap-2 text-xl font-semibold text-slate-900"><Swords size={21} className="text-sky-600"/>{en ? 'Which company delivered the better quarter?' : 'Qual empresa entregou o melhor trimestre?'}</h2><p className="mt-3 text-sm leading-6 text-slate-500">{en ? 'One new duel uses one of your 50 monthly analyses. Reopening a saved duel is free. Failed or inconclusive duels do not use your allowance.' : 'Um duelo novo usa uma das suas 50 análises mensais. Reabrir um duelo salvo é gratuito. Falhas ou duelos inconclusivos não consomem sua franquia.'}</p>
          <div className="mt-6 grid gap-4 md:grid-cols-2">{(['A','B'] as const).map((side,index)=>{
            const symbol=index===0?leftSymbol:rightSymbol, id=index===0?leftId:rightId, other=index===0?rightSymbol:leftSymbol;
            const setSymbol=index===0?setLeftSymbol:setRightSymbol, setId=index===0?setLeftId:setRightId;
            const chosen=index===0?left:right;
            return <div key={side} className="min-w-0 rounded-2xl border border-slate-200 bg-slate-50/70 p-5"><div className="mb-4 flex items-center gap-3"><CompanyLogo symbol={symbol} company={symbol} className="h-10 w-10"/><span className="font-semibold text-slate-900">{symbol || (en ? 'Choose company':'Escolher empresa')}</span></div><label htmlFor={`duel-company-${side}`} className="text-xs font-semibold text-slate-500">{en ? 'Company':'Empresa'} {side}</label><select id={`duel-company-${side}`} value={symbol} className={classSelect} onChange={e=>{setSymbol(e.target.value);setId(String(records.find(r=>r.symbol===e.target.value)?.id||''));}}><option value="">{en?'Select company':'Selecionar empresa'}</option>{companies.map(company=><option key={company} disabled={company===other} value={company}>{company}</option>)}</select><label htmlFor={`duel-period-${side}`} className="mt-4 block text-xs font-semibold text-slate-500">{en?'Saved quarterly result':'Resultado trimestral salvo'}</label><select id={`duel-period-${side}`} value={id} className={classSelect} onChange={e=>setId(e.target.value)}><option value="">{en?'Select period':'Selecionar período'}</option>{records.filter(r=>r.symbol===symbol).map(record=><option key={record.id} value={record.id}>{formatPeriod(record.period,locale)} · {date(record.created_at)}{record.duel_eligible?'':(en?' · source unavailable':' · fonte indisponível')}</option>)}</select><p className="mt-3 text-xs leading-5 text-slate-500">{chosen ? (chosen.period_end ? `${en?'Fiscal end:':'Encerramento fiscal:'} ${date(chosen.period_end)}` : (en?'Fiscal end date not identified':'Encerramento fiscal não identificado')):''}</p>{chosen&&!chosen.duel_eligible&&<p className="mt-2 text-xs leading-5 text-amber-800">{en?'This record has no verified company/period document. Run the quarterly analysis again before using it in a duel.':'Este registro não tem documento verificado da empresa e do período. Refaça a análise trimestral para usá-lo em um duelo.'}</p>}</div>;
          })}</div>
          {left&&right&&(left.year!==right.year||left.quarter!==right.quarter||!left.period_end||!right.period_end||left.period_end!==right.period_end||left.sector!==right.sector||left.sector==='geral')&&<p className="mt-4 flex gap-2 rounded-xl bg-amber-50 p-4 text-xs leading-5 text-amber-900"><Scale size={18} className="shrink-0"/>{en?'Comparability matters: fiscal dates or sectors may differ, or may not be identified. The agent must distinguish these differences and limit its confidence when dates are unknown.':'A comparabilidade importa: datas fiscais ou setores podem ser diferentes ou não estar identificados. O agente deverá contextualizar essas diferenças e limitar sua confiança quando as datas forem desconhecidas.'}</p>}
          <button onClick={()=>void start()} disabled={starting||!left||!right||leftSymbol===rightSymbol||!left.duel_eligible||!right.duel_eligible||['queued','running'].includes(job?.state||'')} className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-sky-600 px-5 py-3.5 font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-50">{starting?<Loader2 size={18} className="animate-spin"/>:<Swords size={18}/>} {en?'Compare results':'Comparar resultados'}</button>
          {duelError&&<div role="alert" className="mt-4 rounded-xl bg-amber-50 p-4 text-sm text-amber-900">{duelError}{jobId&&<button onClick={()=>setPollRevision(v=>v+1)} className="mt-3 block font-semibold">{en?'Check again':'Consultar novamente'}</button>}</div>}
        </div>
        {job&&['queued','running'].includes(job.state)&&<div role="status" aria-live="polite" className="mt-6 flex items-start gap-3 rounded-2xl border border-sky-100 bg-sky-50 p-6"><Loader2 className="mt-0.5 animate-spin text-sky-600" size={21}/><div><p className="font-semibold text-slate-900">{job.stage==='verifying'?(en?'Verifying citations and numerical consistency…':'Verificando as citações e a consistência dos números…'):job.stage==='judging'?(en?'Comparing results and checking the verdict…':'Comparando resultados e verificando o veredito…'):job.stage==='facts'?(en?'Checking facts against the primary documents…':'Conferindo fatos nos documentos de origem…'):(en?'Your duel is queued…':'Seu duelo está na fila…')}</p><p className="mt-2 text-sm leading-6 text-slate-500">{en?'You can leave this tab. The duel will remain in your history.':'Você pode sair desta aba. O duelo ficará no seu histórico.'}</p></div></div>}
        {job&&['failed','stale'].includes(job.state)&&<div role="status" className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm leading-6 text-amber-900">{job.state==='stale'?(en?'The analyses or methodology changed. Start a new comparison to get an updated verdict.':'As análises ou a metodologia mudaram. Inicie uma nova comparação para obter um veredito atualizado.'):(en?'We could not produce a verified comparison. Your allowance was not charged. You can try again.':'Não foi possível produzir uma comparação verificada. Sua franquia não foi consumida. Você pode tentar novamente.')}</div>}
        {result&&job?.state==='completed'&&<article className="mt-6 space-y-5" aria-labelledby="duel-verdict-heading">
          <header className="rounded-3xl bg-[#0f1b2e] p-6 text-white sm:p-8"><p className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-sky-200"><Trophy size={17}/>{en?'Quarterly results verdict':'Veredito dos resultados trimestrais'}</p><h2 id="duel-verdict-heading" className="mt-3 text-2xl font-bold">{['tie','insufficient'].includes(result.verdict)?winnerText(result.verdict):`${winnerText(result.verdict)} ${en?'delivered the stronger result':'entregou o resultado mais forte'}`}</h2><div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-300">{job.participants.map(p=><span key={p.side}>{p.symbol} · {formatPeriod(p.period,locale)}</span>)}<span>{en?'Confidence: ':'Confiança: '}{({high:en?'high':'alta',moderate:en?'moderate':'moderada',low:en?'low':'baixa'} as Record<string,string>)[result.confidence]}</span></div><p className="mt-5 text-sm leading-7 text-slate-100">{result.summary}</p></header>
          <div className="grid gap-4">{result.dimensions.map(d=><section key={d.id} className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-semibold text-slate-900">{dimensions[d.id]}</h3><span className={`rounded-full px-3 py-1 text-xs font-semibold ${d.winner==='insufficient'?'bg-slate-100 text-slate-500':'bg-sky-50 text-sky-700'}`}>{['tie','insufficient'].includes(d.winner)?winnerText(d.winner):`${en?'Advantage: ':'Vantagem: '}${winnerText(d.winner)}`}</span></div><div className="mt-5 grid gap-5 md:grid-cols-2">{(['A','B'] as const).map((side,i)=><div key={side}><p className="mb-2 text-xs font-bold text-slate-900">{bySide(side)?.symbol}</p><p className="text-sm leading-7 text-slate-600"><Copy text={i===0?d.left_assessment:d.right_assessment}/></p></div>)}</div><p className="mt-5 border-t border-slate-100 pt-4 text-sm leading-7 text-slate-700"><Copy text={d.reason}/></p></section>)}</div>
          {!!result.comparisons.length&&<details className="rounded-2xl border border-slate-200 bg-white p-5"><summary className="cursor-pointer font-semibold text-slate-900">{en?'Calculated financial changes':'Variações financeiras calculadas'}</summary><div className="mt-4 overflow-x-auto"><table className="w-full text-left text-xs"><thead><tr>{(en?['Company','Metric','Comparison','Current','Previous','Change']:['Empresa','Indicador','Comparação','Atual','Anterior','Variação']).map(label=><th key={label} className="whitespace-nowrap border-b border-slate-200 p-3 text-slate-500">{label}</th>)}</tr></thead><tbody>{result.comparisons.map((c,i)=><tr key={i} className="border-b border-slate-100"><td className="p-3 font-semibold">{bySide(c.side)?.symbol}</td><td className="p-3">{metricNames[c.metric]||c.metric}{c.accounting_basis==='adjusted'?(en?' · adjusted':' · ajustado'):''}</td><td className="p-3">{c.basis==='prior_year'?(en?'Year over year':'Anual'):(en?'Quarter over quarter':'Trimestral')}</td><td className="whitespace-nowrap p-3">{formatValue(c.current,c.unit,c.currency)}</td><td className="whitespace-nowrap p-3">{formatValue(c.previous,c.unit,c.currency)}</td><td className="whitespace-nowrap p-3">{c.growth_pct!==null?`${c.growth_pct.toLocaleString(en?'en-US':'pt-BR')}%`:c.unit==='percent'?`${c.change.toLocaleString(en?'en-US':'pt-BR')} p.p.`:formatValue(c.change,c.unit,c.currency)}</td></tr>)}</tbody></table></div><p className="mt-3 text-xs leading-5 text-slate-500">{en?'Changes are calculated within each company, with matching units and currencies. Percentage growth is not calculated from a zero or negative base.':'As variações são calculadas dentro de cada empresa, com unidades e moedas iguais. Não calculamos crescimento percentual com base zero ou negativa.'}</p></details>}
          {!!result.watchpoints.length&&<section className="rounded-2xl border border-amber-100 bg-amber-50/60 p-6"><h3 className="font-semibold text-slate-900">{en?'What to watch':'Pontos de atenção'}</h3><div className="mt-4 grid gap-4 sm:grid-cols-2">{result.watchpoints.map((point,i)=><div key={i} className="rounded-xl bg-white p-4"><p className="text-xs font-bold text-slate-900">{bySide(point.side)?.symbol}</p><p className="mt-2 text-sm leading-7 text-slate-600"><Copy text={point.text}/></p></div>)}</div></section>}
          <section className="rounded-2xl border border-slate-200 bg-white p-6"><h3 className="font-semibold text-slate-900">{en?'AI conclusion':'Conclusão da IA'}</h3><p className="mt-4 text-sm leading-7 text-slate-600"><Copy text={result.conclusion}/></p><p className="mt-4 border-t border-slate-100 pt-4 text-xs leading-5 text-slate-500">{en?'This comparison judges the reported quarters. It is not a buy or sell recommendation and does not change the companies’ saved scores.':'A comparação avalia os trimestres reportados. Ela não é uma recomendação de compra ou venda e não altera as notas salvas das empresas.'}{!result.charged&&(en?' No analysis was charged because the evidence was inconclusive.':' Nenhuma análise foi consumida, pois as evidências foram inconclusivas.')}</p>
          <details className="mt-5"><summary className="inline-flex cursor-pointer list-none items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-medium text-slate-600"><FileText size={14}/>2 {en?'sources and evidence':'fontes e evidências'}</summary><div className="mt-4 space-y-5">{job.participants.map((p,index)=><div key={p.side} className="rounded-xl bg-slate-50 p-4"><p className="font-semibold text-slate-900">{p.symbol} · {formatPeriod(p.period,locale)}</p>{p.source.url?<a href={p.source.url} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-xs text-sky-700 underline">{p.source.name}</a>:<p className="mt-2 text-xs text-slate-500">{en?'Uploaded source document':'Documento de origem enviado'}</p>}{result.dimensions.map(d=>{const quote=(index===0?[d.left_quote,...(d.left_supporting_quotes||[])]:[d.right_quote,...(d.right_supporting_quotes||[])]).filter(Boolean).join('\n\n');return quote?<blockquote key={d.id} className="mt-3 border-l-2 border-sky-200 pl-3 text-xs leading-6 text-slate-500"><strong className="font-medium text-slate-700">{dimensions[d.id]}: </strong>{quote}</blockquote>:null;})}{result.watchpoints.filter(w=>w.side===p.side).map((w,i)=><blockquote key={i} className="mt-3 border-l-2 border-amber-200 pl-3 text-xs leading-6 text-slate-500">{[w.quote,...(w.supporting_quotes||[])].join('\n\n')}</blockquote>)}</div>)}</div></details></section>
        </article>}
        <section className="mt-7 rounded-2xl border border-slate-200 bg-white p-5 sm:p-6"><h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900"><History size={19}/>{en?'Saved duels':'Duelos salvos'}</h2><p className="mt-2 text-xs leading-5 text-slate-500">{en?'Your most recent 100 duels. Reopening them does not use your allowance.':'Seus 100 duelos mais recentes. Reabri-los não consome sua franquia.'}</p>{!history.length?<p className="mt-5 text-sm text-slate-500">{en?'Your first duel will appear here.':'Seu primeiro duelo aparecerá aqui.'}</p>:<div className="mt-4 divide-y divide-slate-100">{history.map(saved=><button key={saved.id} onClick={()=>openJob(saved.id)} className="flex w-full flex-wrap items-center justify-between gap-3 rounded-lg px-2 py-4 text-left hover:bg-slate-50"><span className="min-w-0"><strong className="text-sm font-semibold text-slate-900">{saved.participants.map(p=>p.symbol).join(' × ')}</strong><span className="mt-1 block text-xs text-slate-500">{saved.participants.map(p=>`${p.symbol} ${formatPeriod(p.period,locale)}`).join(' · ')} · {saved.locale.toUpperCase()}</span></span><span className="flex items-center gap-2 text-xs font-semibold text-sky-700">{({completed:en?'Open duel':'Abrir duelo',queued:en?'Queued':'Na fila',running:en?'In progress':'Em andamento',failed:en?'Not completed':'Não concluído',stale:en?'Outdated':'Desatualizado'} as Record<string,string>)[saved.state]}<ArrowRight size={15}/></span></button>)}</div>}</section>
      </div>
      </>}
    </>}
  </section>;
}
