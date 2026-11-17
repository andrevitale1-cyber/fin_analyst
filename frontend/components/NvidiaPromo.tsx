"use client";

import { useEffect, useState } from "react";
import { useAuth, useClerk } from "@clerk/nextjs";
import { ArrowRight, X } from "lucide-react";
import styles from "./NvidiaPromo.module.css";

// NVIDIA reported fiscal Q3 2027 on Nov 17, 2026; the invitation runs for 10 days.
const ENDS_AT = Date.parse("2026-11-28T00:00:00-03:00");
const DISMISSED = "nvidia-promo-dismissed";

declare global { interface Window { gtag?: (...args: unknown[]) => void } }
const track = (name: string, extra: Record<string, unknown> = {}) =>
  window.gtag?.("event", name, { promo_id: "nvda_3q_fy2027", transport_type: "beacon", ...extra });

export default function NvidiaPromo({ locale }: { locale: string }) {
  const english = locale === "en";
  const { isLoaded, isSignedIn } = useAuth();
  const clerk = useClerk();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let dismissed = false;
    try { dismissed = sessionStorage.getItem(DISMISSED) === "1"; } catch { /* storage blocked: still show */ }
    if (dismissed || Date.now() >= ENDS_AT) return;
    const timer = window.setTimeout(() => { setOpen(true); track("nvidia_promo_view"); }, 1200);
    return () => clearTimeout(timer);
  }, []);

  const close = () => {
    setOpen(false);
    track("nvidia_promo_dismiss");
    try { sessionStorage.setItem(DISMISSED, "1"); } catch { /* ignore */ }
  };

  const analyze = () => {
    const target = `/${locale}/dashboard?company=NVDA&ano=2027&trimestre=3T`;
    track("nvidia_promo_click", { signed_in: Boolean(isSignedIn) });
    try { sessionStorage.setItem(DISMISSED, "1"); } catch { /* ignore */ }
    if (isSignedIn) window.location.assign(target);
    else void clerk.redirectToSignUp({ signUpForceRedirectUrl: target, signInForceRedirectUrl: target });
  };

  if (!open) return null;
  return <div className={styles.backdrop} onClick={event => { if (event.target === event.currentTarget) close(); }} onKeyDown={event => { if (event.key === "Escape") close(); }}>
    <div className={styles.card} role="dialog" aria-modal="true" aria-labelledby="nvidia-promo-title">
      <button className={styles.close} onClick={close} aria-label={english ? "Close" : "Fechar"}><X size={18} /></button>
      <div className={styles.logo}><img src="/benefits/company-logos/NVDA.webp" alt="" width={44} height={44} /></div>
      <span className={styles.eyebrow}>{english ? "NEW RESULTS" : "RESULTADO NOVO"}</span>
      <h2 id="nvidia-promo-title">{english ? "NVIDIA just reported its fiscal Q3 2027" : "A NVIDIA acabou de divulgar o 3º trimestre fiscal de 2027"}</h2>
      <p>{english
        ? "See in minutes what drove revenue, margins and guidance, how the market reacted, and the AI’s score for the quarter, with links to the official filing."
        : "Veja em minutos o que explica a receita, as margens e o guidance, como o mercado reagiu e a nota da IA para o trimestre, com links para o documento oficial."}</p>
      <button autoFocus className={styles.primary} onClick={analyze} disabled={!isLoaded}>
        {english ? "Analyze NVIDIA’s results" : "Analisar o resultado da NVIDIA"}<ArrowRight size={17} aria-hidden="true" />
      </button>
      {isLoaded && !isSignedIn && <small>{english ? "You’ll create your account first. It takes a few seconds." : "Você cria sua conta antes. Leva poucos segundos."}</small>}
      <button className={styles.later} onClick={close}>{english ? "Not now" : "Agora não"}</button>
    </div>
  </div>;
}
