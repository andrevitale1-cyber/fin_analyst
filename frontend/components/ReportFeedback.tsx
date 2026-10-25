"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import { ThumbsDown, ThumbsUp } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "https://api-finanalyzer.onrender.com";

export default function ReportFeedback({ reportId, locale, kind = "full" }: { reportId: string; locale: string; kind?: "full" | "analysis" }) {
  const { getToken, userId, isLoaded } = useAuth();
  const en = locale === "en";
  const [vote, setVote] = useState<number | null>(null);
  const [pending, setPending] = useState(true);
  const [message, setMessage] = useState("");
  const [retry, setRetry] = useState(0);
  const endpoint = `${API}/api/report-feedback/${kind}/${encodeURIComponent(reportId)}`;
  useEffect(() => {
    let active = true;
    setVote(null); setMessage(""); setPending(true);
    if (!isLoaded) return;
    if (!userId) { setPending(false); return; }
    (async () => {
      try {
        const token = await getToken();
        if (!token) throw Error();
        const response = await fetch(endpoint, { headers: { Authorization: `Bearer ${token}` }, signal: AbortSignal.timeout(15000) });
        if (!response.ok) throw Error();
        const result = await response.json();
        if (active) setVote(result.vote);
      } catch { if (active) setMessage(en ? "Could not load your feedback. Try again." : "Não foi possível carregar seu feedback. Tente novamente."); }
      finally { if (active) setPending(false); }
    })();
    return () => { active = false; };
  }, [userId, isLoaded, getToken, endpoint, en, retry]);
  async function submit(nextVote: number) {
    setPending(true); setMessage("");
    try {
      const token = await getToken();
      if (!token) throw Error();
      const response = await fetch(endpoint, { method: "PUT", headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }, body: JSON.stringify({ vote: nextVote }), signal: AbortSignal.timeout(15000) });
      if (!response.ok) throw Error();
      setVote((await response.json()).vote);
      setMessage(en ? "Thank you. Your feedback was saved." : "Obrigado. Seu feedback foi salvo.");
    } catch { setMessage(en ? "Could not save your feedback. Please try again." : "Não foi possível salvar seu feedback. Tente novamente."); }
    finally { setPending(false); }
  }
  return <section aria-label={en ? "Report feedback" : "Feedback do relatório"} className="my-5 rounded-2xl border border-slate-200 bg-white p-5 text-slate-900 sm:p-6">
    <h2 className="text-base font-semibold">{en ? "Was this report helpful?" : "Este relatório foi útil?"}</h2>
    <p className="mt-1 text-xs leading-5 text-slate-500">{en ? "Your feedback helps us improve our research." : "Seu feedback ajuda a melhorar nossas análises."}</p>
    {!userId && isLoaded ? <a target="_top" href={`/${locale}/dashboard/reports?reportId=${encodeURIComponent(reportId)}`} className="mt-3 inline-block text-sm font-medium text-sky-700">{en ? "Sign in to give feedback" : "Entre para avaliar"}</a> : <div className="mt-4 flex flex-wrap gap-2">{([[1, ThumbsUp, en ? "Helpful" : "Gostei"], [-1, ThumbsDown, en ? "Not helpful" : "Não gostei"]] as const).map(([value, Icon, label]) => <button key={value} type="button" aria-pressed={vote === value} disabled={pending} onClick={() => void submit(value)} className={`inline-flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-medium transition disabled:opacity-50 ${vote === value ? "border-sky-600 bg-sky-50 text-sky-800" : "border-slate-200 text-slate-600 hover:bg-slate-50"}`}><Icon size={16}/>{label}</button>)}</div>}
    <p role="status" className="mt-2 text-xs text-slate-600">{message}</p>
    {message.includes("load") || message.includes("carregar") ? <button onClick={() => setRetry(value => value + 1)} className="mt-1 text-xs text-sky-700">{en ? "Try again" : "Tentar novamente"}</button> : null}
  </section>;
}
