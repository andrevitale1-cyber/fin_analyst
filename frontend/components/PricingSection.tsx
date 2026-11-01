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
        ["10 analyses during your 7-day trial", "Shared between quarterly results and earnings calls."],
        ["Aggregated table", "View company indicators in one place."],
        ["Analysis history", "Revisit the analyses you saved during your trial."],
        ["Public full reports", "Explore the published company research collection."],
      ]
    : [
        ["10 análises durante o teste de 7 dias", "Compartilhadas entre resultados trimestrais e calls."],
        ["Tabela agregada", "Consulte os indicadores das empresas em um só lugar."],
        ["Histórico de análises", "Volte às análises salvas durante o período de teste."],
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
        <p className={styles.saving}>{yearly ? (english ? "2 months free with yearly billing" : "2 meses grátis no plano anual") : (english ? "Try FinAnalyzer free for 7 days" : "Experimente o FinAnalyzer grátis por 7 dias")}</p>
      </header>
      <div className={styles.plans}>
        {[{ name: english ? "Free trial" : "Teste grátis", description: english ? "7 days to explore the platform, with 10 analyses included." : "7 dias para conhecer a plataforma, com 10 análises incluídas.", features: trialFeatures, premium: false }, { name: "Premium", description: english ? "Analyze faster. Keep your research within reach." : "Analise com agilidade. Tenha sua pesquisa sempre à mão.", features: premiumFeatures, premium: true }].map(plan => <article key={plan.name} className={`${styles.card} ${plan.premium ? styles.premium : ""}`} aria-label={plan.name}>
          {plan.premium && <span className={styles.badge}>{english ? "Full access" : "Acesso completo"}</span>}
          <div className={styles.heading}>
            <h3>{plan.premium ? <Sparkles size={20} aria-hidden="true" /> : <Zap size={20} aria-hidden="true" />}{plan.name}</h3>
            <p className={styles.description}>{plan.description}</p>
            <p className={styles.price}><strong>{plan.premium ? (yearly ? "R$ 290" : "R$ 29") : "R$ 0"}</strong><span>{plan.premium ? (yearly ? (english ? "/ year" : "/ ano") : (english ? "/ month" : "/ mês")) : (english ? "/ 7 days" : "/ 7 dias")}</span></p>
          </div>
          <Link href="/dashboard" className={styles.action}><span>{plan.premium ? (english ? "Choose Premium" : "Escolher Premium") : (english ? "Start free trial" : "Começar teste grátis")}</span><ChevronRight size={16} aria-hidden="true" /></Link>
          <ul className={styles.features}>
            {plan.features.map(([title, detail]) => <li key={title}><span><strong>{title}</strong><small>{detail}</small></span><CheckCheck size={20} aria-label={english ? "Included" : "Incluído"} /></li>)}
          </ul>
          <p className={styles.note}>{plan.premium ? (english ? `Premium: ${yearly ? "R$ 290/year" : "R$ 29/month"}. 50 analyses per month, including yearly subscriptions. Cancel anytime.` : `Premium: ${yearly ? "R$ 290/ano" : "R$ 29/mês"}. 50 análises por mês, inclusive na assinatura anual. Cancele quando quiser.`) : (english ? "10 analyses in total over 7 days. PDF export is exclusive to Premium." : "10 análises no total durante 7 dias. Exportação para PDF exclusiva do Premium.")}</p>
        </article>)}
      </div>
    </div>
  </section>;
}
