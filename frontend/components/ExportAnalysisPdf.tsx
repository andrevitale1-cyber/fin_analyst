"use client";

import { useEffect, useRef, useState } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';
import { Download, Loader2, Lock } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api-finanalyzer.onrender.com';

export default function ExportAnalysisPdf({ analysisId, locale, premium, onUpgrade }: {
  analysisId: number; locale: string; premium: boolean; onUpgrade: () => void;
}) {
  const { getToken } = useAuth();
  const { user } = useUser();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const request = useRef<AbortController | null>(null);
  const en = locale === 'en';
  useEffect(() => { setBusy(false); setError(''); return () => { request.current?.abort(); request.current = null; }; }, [analysisId, user?.id, locale]);

  async function download() {
    if (!premium) { onUpgrade(); return; }
    const controller = new AbortController();
    request.current = controller;
    setBusy(true); setError('');
    const timeout = window.setTimeout(() => controller.abort(), 60000);
    try {
      const token = await getToken();
      if (!token || controller.signal.aborted) throw new Error('Session unavailable');
      const response = await fetch(`${API_BASE}/api/report/${analysisId}/pdf?locale=${locale}`, {
        headers: { Authorization: `Bearer ${token}` }, signal: controller.signal,
      });
      if (response.status === 403) { onUpgrade(); return; }
      if (!response.ok || !response.headers.get('content-type')?.includes('application/pdf')) throw new Error('Export failed');
      const blob = await response.blob();
      if (controller.signal.aborted) return;
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url; link.download = `finanalyser-analysis-${analysisId}.pdf`;
      document.body.appendChild(link); link.click(); link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch {
      if (request.current === controller) setError(en ? 'Could not export the PDF. Please try again.' : 'Não foi possível exportar o PDF. Tente novamente.');
    } finally {
      window.clearTimeout(timeout);
      if (request.current === controller) { setBusy(false); request.current = null; }
    }
  }

  return <div className="flex w-full flex-col gap-2 md:w-auto">
    <button type="button" onClick={() => void download()} disabled={busy || !analysisId}
      className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-5 py-2.5 font-semibold text-slate-700 transition hover:border-sky-300 hover:text-sky-700 disabled:opacity-50">
      {busy ? <Loader2 size={18} className="animate-spin" /> : premium ? <Download size={18} /> : <Lock size={16} />}
      {busy ? (en ? 'Exporting…' : 'Exportando…') : (en ? 'Export PDF' : 'Exportar PDF')}
      {!premium && <span className="text-xs text-sky-700">Premium</span>}
    </button>
    {error && <p role="alert" className="max-w-xs text-sm text-red-600">{error}</p>}
  </div>;
}
