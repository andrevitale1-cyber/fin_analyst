"use client";

import { useEffect, useRef, useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import { ChevronDown, ChevronUp, Loader2, Sparkles } from 'lucide-react';
import { splitBold } from '../lib/analysisText';

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api-finanalyzer.onrender.com';
type Job = {id?: string; state: string; content?: string; error_code?: string};

function Inline({text}: {text: string}) {
  return <>{splitBold(text).map((part, i) => part.bold ? <strong key={i} className="font-semibold text-slate-900">{part.text}</strong> : part.text)}</>;
}

// Render the agent's limited Markdown as React text; HTML and scripts remain inert.
function Content({text}: {text: string}) {
  return <div className="space-y-5 text-base leading-8 text-slate-600">{text.split(/\n\s*\n/).map((block, i) => {
    const lines = block.trim().split('\n');
    if (lines.length > 2 && lines[0].trim().startsWith('|') && /^\s*\|?[\s:|\-]+\|\s*$/.test(lines[1])) {
      const cells = (line: string) => line.trim().replace(/^\||\|$/g, '').split('|');
      return <div key={i} className="overflow-x-auto rounded-xl border border-slate-200"><table className="w-full text-left text-sm"><thead className="bg-slate-50"><tr>{cells(lines[0]).map((cell, j) => <th key={j} className="px-4 py-3 font-semibold"><Inline text={cell}/></th>)}</tr></thead><tbody>{lines.slice(2).map((line, j) => <tr key={j} className="border-t border-slate-100">{cells(line).map((cell, k) => <td key={k} className="px-4 py-3"><Inline text={cell}/></td>)}</tr>)}</tbody></table></div>;
    }
    return <div key={i}>{lines.map((line, j) => /^#{1,6}\s/.test(line) || /^\d+[.)]\s/.test(line) && line.length < 160
      ? <h4 key={j} className="mb-3 text-lg font-semibold text-slate-900"><Inline text={line.replace(/^#{1,6}\s+/, '')}/></h4>
      : <p key={j}><Inline text={line}/></p>)}</div>;
  })}</div>;
}

export default function DetailedQuarterlyAnalysis({analysisId, locale, onUsageChange}: {analysisId: number; locale: string; onUsageChange: () => void}) {
  const {getToken} = useAuth();
  const en = locale === 'en';
  const [job, setJob] = useState<Job>({state: 'loading'});
  const [open, setOpen] = useState(false), [starting, setStarting] = useState(false), [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const [cancelling, setCancelling] = useState(false);
  const usage = useRef(onUsageChange);
  usage.current = onUsageChange;
  const busy = starting || job.state === 'queued' || job.state === 'running';

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    let sawPending = false;
    async function poll() {
      try {
        const token = await getToken();
        const response = await fetch(`${API}/api/detailed-analysis/${analysisId}?locale=${en ? 'en' : 'pt'}`, {signal: controller.signal, headers: {Authorization: `Bearer ${token}`}});
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || (en ? 'Unable to load detailed analysis.' : 'Não foi possível carregar o detalhamento.'));
        if (controller.signal.aborted) return;
        setJob(data);
        if (['queued', 'running'].includes(data.state)) {
          sawPending = true;
          timer = setTimeout(poll, 3000);
        } else if (sawPending || revision > 0) usage.current();
      } catch (e) {
        if (!controller.signal.aborted) {
          setError(e instanceof Error ? e.message : 'Error');
          setJob({state: 'unavailable'});
        }
      }
    }
    void poll();
    return () => {controller.abort(); clearTimeout(timer);};
  }, [analysisId, en, getToken, revision]);

  async function generate() {
    if (busy) return;
    setStarting(true); setError('');
    try {
      const token = await getToken();
      const response = await fetch(`${API}/api/detailed-analysis/${analysisId}`, {method: 'POST', headers: {Authorization: `Bearer ${token}`, 'Content-Type': 'application/json'}, body: JSON.stringify({locale: en ? 'en' : 'pt'})});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || (en ? 'Unable to start detailed analysis.' : 'Não foi possível iniciar o detalhamento.'));
      setJob(data); setOpen(true); setRevision(value => value + 1); usage.current();
    } catch (e) {setError(e instanceof Error ? e.message : 'Error');}
    finally {setStarting(false);}
  }

  async function cancel() {
    if (!job.id || cancelling) return;
    setCancelling(true); setError('');
    try {
      const token = await getToken();
      const response = await fetch(`${API}/api/detailed-analysis/${analysisId}/cancel`, {method: 'POST', headers: {Authorization: `Bearer ${token}`, 'Content-Type': 'application/json'}, body: JSON.stringify({id: job.id})});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || (en ? 'Unable to cancel. Please try again.' : 'Não foi possível cancelar. Tente novamente.'));
      setJob(data); setRevision(value => value + 1); usage.current();
    } catch (e) {setError(e instanceof Error ? e.message : 'Error'); setRevision(value => value + 1);}
    finally {setCancelling(false);}
  }

  const saved = job.state === 'completed';
  return <section className="mt-7 rounded-3xl border border-sky-200 bg-white p-6 md:p-10" aria-label={en ? 'Detailed quarterly analysis' : 'Análise trimestral detalhada'}>
    <div className="flex flex-col justify-between gap-5 md:flex-row md:items-center">
      <div><span className="text-xs font-semibold uppercase tracking-widest text-sky-700">Premium</span><h3 className="mt-2 text-xl font-bold text-slate-900">{en ? 'Go deeper into this quarter' : 'Aprofunde a análise deste trimestre'}</h3><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">{saved ? (en ? 'Saved analysis. Reopen it at no extra cost.' : 'Análise salva. Reabra sem consumir outra análise.') : (en ? 'Understand the numbers, management’s explanations and outlook. Uses 1 monthly analysis only when completed.' : 'Entenda os números, as explicações da gestão e as perspectivas. Consome 1 análise mensal somente ao concluir.')}</p></div>
      <button type="button" disabled={busy || job.state === 'loading'} onClick={() => saved ? setOpen(value => !value) : job.state === 'unavailable' ? (setError(''), setRevision(value => value + 1)) : void generate()} className="inline-flex min-h-12 shrink-0 items-center justify-center gap-2 rounded-xl bg-sky-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:opacity-60">
        {busy ? <Loader2 size={18} className="animate-spin"/> : <Sparkles size={18}/>}{busy ? (en ? 'Preparing detailed analysis…' : 'Preparando análise detalhada…') : saved ? (en ? 'View detailed analysis' : 'Ver análise detalhada') : job.state === 'unavailable' ? (en ? 'Check again' : 'Verificar novamente') : (en ? 'Generate detailed analysis' : 'Gerar análise detalhada')}{saved && (open ? <ChevronUp size={16}/> : <ChevronDown size={16}/>)}</button>
    </div>
    {busy && job.id && <button type="button" onClick={() => void cancel()} disabled={cancelling} className="mt-4 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-red-200 hover:bg-red-50 hover:text-red-700 disabled:opacity-50">{cancelling ? (en ? 'Cancelling…' : 'Cancelando…') : (en ? 'Cancel request' : 'Cancelar pedido')}</button>}
    {job.state === 'cancelled' && <p role="status" className="mt-4 text-sm text-slate-500">{en ? 'Request cancelled. No analysis was charged.' : 'Pedido cancelado. Nenhuma análise foi cobrada.'}</p>}
    {error && <p role="alert" className="mt-4 text-sm text-amber-800">{error}</p>}
    {job.state === 'failed' && <p role="alert" className="mt-4 text-sm text-amber-800">{en ? 'The detailed analysis could not be completed. No analysis was charged. You can try again.' : 'Não foi possível concluir o detalhamento. Nenhuma análise foi cobrada. Você pode tentar novamente.'}</p>}
    {busy && <p role="status" className="mt-5 text-sm text-slate-500">{en ? 'You can leave this page. Your detailed analysis will be saved here.' : 'Você pode sair desta página. A análise detalhada ficará salva aqui.'}</p>}
    {open && saved && job.content && <div className="mt-7 border-t border-slate-100 pt-7"><Content text={job.content}/></div>}
  </section>;
}
