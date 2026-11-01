"use client";

import { useState } from "react";
import { CheckCheck, ChevronRight, Sparkles, Zap } from "lucide-react";
import { Link } from "@/i18n/routing";
import styles from "./PricingSection.module.css";

export default function PricingSection({ locale }: { locale: string }) {
  const english = locale === "en";
  const [yearly, setYearly] = useState(false);
  const trialFeatures = english
    ? [
        ["10 analyses with no expiry date", "Shared between quarterly results and earnings calls."],
        ["Aggregated table", "View company indicators in one place."],
        ["Analysis history", "Revisit the analyses you saved at any time."],
        ["Public full reports", "Explore the published company research collection."],
      ]
    : [
        ["10 análises sem prazo de validade", "Compartilhadas entre resultados trimestrais e calls."],
        ["Tabela agregada", "Consulte os indicadores das empresas em um só lugar."],
        ["Histórico de análises", "Volte às análises salvas a qualquer momento."],
        ["Full reports públicos", "Explore a coleção publicada de pesquisas sobre empresas."],
      ];
  const premiumFeatures = english
    ? [
        ["50 analyses per month", "Shared between quarterly results and earnings calls."],
        ["Aggregated table and history", "View indicators and revisit your saved analyses."],
        ["Public full reports", "Read published company research."],
        ["Company comparisons", "Review companies side by side."],
        ["Generate new full reports", "Request company-wide research, saved privately."],
        ["PDF export", "Download your analyses and reports. Exclusive to Premium."],
      ]
    : [
        ["50 análises por mês", "Compartilhadas entre resultados trimestrais e calls."],
        ["Tabela agregada e histórico", "Consulte indicadores e revisite suas análises salvas."],
        ["Full reports públicos", "Leia as pesquisas publicadas sobre empresas."],
        ["Comparação de empresas", "Revise empresas lado a lado."],
        ["Geração de novos full reports", "Solicite pesquisas sobre a empresa como um todo, salvas como privadas."],
        ["Exportação para PDF", "Baixe suas análises e relatórios. Exclusivo do Premium."],
      ];

  return <section id="planos" className={styles.section} aria-labelledby="pricing-heading">
    <div className={styles.container}>
      <header className={styles.intro}>
        <h2 id="pricing-heading">{english ? "Pricing" : "Planos"}</h2>
        <p>{english ? "Spend less time on reports. More time on your decisions." : "Menos tempo nos relatórios. Mais tempo para suas decisões."}</p>
        <div className={styles.billing} role="group" aria-label={english ? "Billing period" : "Período de cobrança"}>
          <button type="button" aria-pressed={!yearly} onClick={() => setYearly(false)}>{english ? "Monthly" : "Mensal"}</button>
          <button type="button" aria-pressed={yearly} onClick={() => setYearly(true)}>{english ? "Yearly" : "Anual"}</button>
        </div>
        <p className={styles.saving}>{yearly ? (english ? "2 months free with yearly billing" : "2 meses grátis no plano anual") : (english ? "Start with 10 free analyses" : "Comece com 10 análises grátis")}</p>
      </header>
      <div className={styles.plans}>
        {[{ name: english ? "Free" : "Grátis", description: english ? "10 analyses to explore the platform, with no time limit." : "10 análises para conhecer a plataforma, sem limite de tempo.", features: trialFeatures, premium: false }, { name: "Premium", description: english ? "Analyze faster. Keep your research within reach." : "Analise com agilidade. Tenha sua pesquisa sempre à mão.", features: premiumFeatures, premium: true }].map(plan => <article key={plan.name} className={`${styles.card} ${plan.premium ? styles.premium : ""}`} aria-label={plan.name}>
          {plan.premium && <span className={styles.badge}>{english ? "Full access" : "Acesso completo"}</span>}
          <div className={styles.heading}>
            <h3>{plan.premium ? <Sparkles size={20} aria-hidden="true" /> : <Zap size={20} aria-hidden="true" />}{plan.name}</h3>
            <p className={styles.description}>{plan.description}</p>
            <p className={styles.price}><strong>{plan.premium ? (yearly ? "R$ 290" : "R$ 29") : "R$ 0"}</strong><span>{plan.premium ? (yearly ? (english ? "/ year" : "/ ano") : (english ? "/ month" : "/ mês")) : (english ? "no time limit" : "sem prazo")}</span></p>
          </div>
          <Link href="/dashboard" className={styles.action}><span>{plan.premium ? (english ? "Choose Premium" : "Escolher Premium") : (english ? "Start for free" : "Começar grátis")}</span><ChevronRight size={16} aria-hidden="true" /></Link>
          <ul className={styles.features}>
            {plan.features.map(([title, detail]) => <li key={title}><span><strong>{title}</strong><small>{detail}</small></span><CheckCheck size={20} aria-label={english ? "Included" : "Incluído"} /></li>)}
          </ul>
          <p className={styles.note}>{plan.premium ? (english ? `Premium: ${yearly ? "R$ 290/year" : "R$ 29/month"}. 50 analyses per month, including yearly subscriptions. Cancel anytime.` : `Premium: ${yearly ? "R$ 290/ano" : "R$ 29/mês"}. 50 análises por mês, inclusive na assinatura anual. Cancele quando quiser.`) : (english ? "10 analyses in total, with no expiry date. PDF export is exclusive to Premium." : "10 análises no total, sem prazo de validade. Exportação para PDF exclusiva do Premium.")}</p>
        </article>)}
      </div>
    </div>
  </section>;
}
