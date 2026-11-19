"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CONSENT_KEY } from "../lib/consent";
import GoogleAnalytics from "./GoogleAnalytics";
import MetaPixel from "./MetaPixel";
import RedditPixel from "./RedditPixel";
import TikTokPixel from "./TikTokPixel";

type Choice = "granted" | "denied" | null;

export default function CookieConsent({ locale }: { locale: string }) {
  const [choice, setChoice] = useState<Choice | undefined>(undefined);
  const en = locale === "en";

  useEffect(() => {
    try { setChoice(localStorage.getItem(CONSENT_KEY) as Choice); } catch { setChoice(null); }
  }, []);

  const decide = (value: "granted" | "denied") => {
    try { localStorage.setItem(CONSENT_KEY, value); } catch { /* Without storage the choice lasts for this visit only. */ }
    setChoice(value);
  };

  if (choice === "granted") return <><GoogleAnalytics /><RedditPixel /><TikTokPixel /><MetaPixel /></>;
  if (choice !== null) return null;

  return (
    <div role="dialog" aria-live="polite" aria-label={en ? "Cookie preferences" : "Preferências de cookies"}
      className="fixed inset-x-3 bottom-3 z-[100] mx-auto max-w-3xl rounded-2xl border border-white/10 bg-[#111827] p-4 text-sm text-gray-300 shadow-2xl sm:flex sm:items-center sm:gap-4">
      <p className="flex-1">
        {en
          ? "We use cookies for analytics (Google Analytics) and to measure our ads (Meta, TikTok and Reddit). Essential login cookies are always on. "
          : "Usamos cookies para análise de uso (Google Analytics) e para medir nossos anúncios (Meta, TikTok e Reddit). Os cookies essenciais de login ficam sempre ativos. "}
        <Link href={`/${locale}/privacy`} className="text-blue-400 underline">{en ? "Privacy policy" : "Política de privacidade"}</Link>
      </p>
      <div className="mt-3 flex shrink-0 gap-2 sm:mt-0">
        <button onClick={() => decide("denied")} className="rounded-lg border border-white/20 px-4 py-2 font-semibold text-gray-200 hover:bg-white/5">
          {en ? "Decline" : "Recusar"}
        </button>
        <button onClick={() => decide("granted")} className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-500">
          {en ? "Accept" : "Aceitar"}
        </button>
      </div>
    </div>
  );
}

export function ResetCookieChoice({ label }: { label: string }) {
  return (
    <button className="mt-3 text-blue-400 underline"
      onClick={() => { try { localStorage.removeItem(CONSENT_KEY); } catch { /* Nothing stored. */ } window.location.reload(); }}>
      {label}
    </button>
  );
}
