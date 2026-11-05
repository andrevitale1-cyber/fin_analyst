"use client";

import { useEffect, useState } from 'react';
import { Clock3 } from 'lucide-react';

export default function AnalysisWaitEstimate({kind, locale}: {kind: 'traditional' | 'detailed'; locale: string}) {
  const [delayed, setDelayed] = useState(false);
  const en = locale === 'en';
  const detailed = kind === 'detailed';
  useEffect(() => {
    const timer = setTimeout(() => setDelayed(true), detailed ? 120000 : 180000);
    return () => clearTimeout(timer);
  }, [detailed]);

  return <div className="mt-4 max-w-lg text-sm" role="status">
    <p className="inline-flex items-center gap-2 font-medium text-sky-700"><Clock3 size={16} aria-hidden="true"/>{en ? 'Estimated time: ' : 'Tempo estimado: '}{detailed ? (en ? '40 seconds–2 minutes' : '40 segundos a 2 minutos') : (en ? '1–3 minutes' : '1 a 3 minutos')}</p>
    <p className="mt-1 text-xs leading-5 text-slate-500">{delayed
      ? (en ? 'Taking longer than estimated. Your request is still in progress.' : 'Está levando mais tempo que o estimado. Seu pedido continua em andamento.')
      : (en ? 'Approximate estimate. Document size, source availability and the queue can affect the wait.' : 'Estimativa aproximada. O tamanho do documento, a disponibilidade das fontes e a fila podem alterar a espera.')}</p>
  </div>;
}
