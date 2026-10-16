import { ChevronDown, FileText } from "lucide-react";

type Source = { id: string; title: string; url: string | null };

export default function ReportSources({ sources, label, anchors = false }: { sources: Source[]; label: string; anchors?: boolean }) {
  if (!sources.length) return null;
  return <details className="report-sources group mt-5 text-xs">
    <summary className="inline-flex min-h-10 cursor-pointer list-none items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600 [&::-webkit-details-marker]:hidden">
      <span aria-hidden="true" className="flex -space-x-1.5">{sources.slice(0, 3).map(source => <span key={source.id} className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-slate-200 text-slate-600"><FileText size={12} /></span>)}</span>
      {label}<ChevronDown aria-hidden="true" size={14} className="transition group-open:rotate-180" />
    </summary>
    <ul className="mt-3 space-y-1 rounded-xl border border-slate-200 bg-slate-50/70 p-2">{sources.map(source => <li key={source.id} id={anchors ? `source-${encodeURIComponent(source.id)}` : undefined} className="scroll-mt-28 break-words leading-5">{source.url && /^https?:\/\//i.test(source.url) ? <a href={source.url} target="_blank" rel="noopener noreferrer" className="block rounded-lg px-3 py-2 text-slate-700 hover:bg-white hover:text-sky-800 focus-visible:outline-2 focus-visible:outline-sky-600">{source.title}</a> : <span className="block px-3 py-2 text-slate-600">{source.title}</span>}</li>)}</ul>
  </details>;
}
