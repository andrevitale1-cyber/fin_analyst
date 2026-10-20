"use client";

import { useId } from "react";
import { ChevronDown, FileText } from "lucide-react";

type Source = { id: string; title: string; url: string | null };

export default function ReportSources({ sources, label, anchors = false }: { sources: Source[]; label: string; anchors?: boolean }) {
  const id = useId();
  if (!sources.length) return null;
  return <div className="report-sources mt-5 text-xs">
    <button type="button" popoverTarget={id} className="inline-flex min-h-10 cursor-pointer items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600">
      <span aria-hidden="true" className="flex -space-x-1.5">{sources.slice(0, 3).map(source => <span key={source.id} className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-slate-200 text-slate-600"><FileText size={12} /></span>)}</span>
      {label}<ChevronDown aria-hidden="true" size={14} />
    </button>
    <div id={id} popover="auto" aria-label={label} className="report-source-popover fixed inset-0 m-auto max-h-[min(70dvh,32rem)] w-[min(28rem,calc(100vw-2rem))] overflow-y-auto rounded-2xl border border-slate-200 bg-white p-3 text-sm text-slate-700 shadow-2xl backdrop:bg-slate-900/20">
      <div className="mb-2 flex items-center justify-between gap-3 border-b border-slate-100 px-3 pb-2"><strong>{label}</strong><button type="button" popoverTarget={id} popoverTargetAction="hide" aria-label="Close / Fechar" className="flex h-9 w-9 items-center justify-center rounded-lg text-xl hover:bg-slate-100">×</button></div>
      <ul className="space-y-1">{sources.map(source => <li key={source.id} id={anchors ? `source-${encodeURIComponent(source.id)}` : undefined} className="scroll-mt-28 break-words leading-5">{source.url && /^https?:\/\//i.test(source.url) ? <a href={source.url} target="_blank" rel="noopener noreferrer" className="block rounded-lg px-3 py-2 hover:bg-slate-50 hover:text-sky-800 focus-visible:outline-2 focus-visible:outline-sky-600">{source.title}</a> : <span className="block px-3 py-2 text-slate-600">{source.title}</span>}</li>)}</ul>
    </div>
  </div>;
}
