"use client";

import { useState } from "react";
import { CheckCheck, ChevronRight, Sparkles, Zap } from "lucide-react";
import { Link } from "@/i18n/routing";
import styles from "./PricingSection.module.css";

export default function PricingSection({ locale }: { locale: string }) {
  const english = locale === "en";
  const [yearly, setYearly] = useState(false);
  const trialFeatures = english
    ? ["Full access for 7 days", "Unlimited AI analyses", "Full report download", "Company comparison", "Earnings call analysis", "No credit card required"]
    : ["Acesso completo por 7 dias", "Análises de IA ilimitadas", "Download do relatório completo", "Comparação de empresas", "Análise de earnings calls", "Sem cartão de crédito"];
  const premiumFeatures = english
    ? ["Unlimited AI analyses", "On-screen reports", "Unlimited history access", "Email support", "Unlimited file uploads", "Full report download", "Company comparison", "Earnings call analysis", "Maximum queue priority"]
    : ["Análises de IA ilimitadas", "Relatórios na tela", "Acesso ao histórico ilimitado", "Suporte por e-mail", "Upload de arquivos ilimitado", "Download do relatório completo", "Comparação de empresas", "Análise de earnings calls", "Prioridade máxima na fila"];

  return <section id="planos" className={styles.section} aria-labelledby="pricing-heading">
    <div className={styles.container}>
      <header className={styles.intro}>
        <h2 id="pricing-heading">{english ? "Pricing" : "Planos"}</h2>
        <p>{english ? "Spend less time on reports. More time on your decisions." : "Menos tempo nos relatórios. Mais tempo para suas decisões."}</p>
        <div className={styles.billing} role="group" aria-label={english ? "Billing period" : "Período de cobrança"}>
          <button type="button" aria-pressed={!yearly} onClick={() => setYearly(false)}>{english ? "Monthly" : "Mensal"}</button>
          <button type="button" aria-pressed={yearly} onClick={() => setYearly(true)}>{english ? "Yearly" : "Anual"}</button>
        </div>
        <p className={styles.saving}>{yearly ? (english ? "2 months free with yearly billing" : "2 meses grátis no plano anual") : (english ? "Start with a 7-day free trial" : "Comece com 7 dias grátis")}</p>
      </header>
      <div className={styles.plans}>
        {[{ name: english ? "Free Trial" : "Trial gratuito", features: trialFeatures, premium: false }, { name: "Premium", features: premiumFeatures, premium: true }].map(plan => <article key={plan.name} className={`${styles.card} ${plan.premium ? styles.premium : ""}`} aria-label={plan.name}>
          {plan.premium && <span className={styles.badge}>{english ? "Full access" : "Acesso completo"}</span>}
          <div className={styles.heading}>
            <h3>{plan.premium ? <Sparkles size={20} aria-hidden="true" /> : <Zap size={20} aria-hidden="true" />}{plan.name}</h3>
            <p className={styles.price}><strong>{plan.premium ? (yearly ? "R$ 290" : "R$ 29") : "R$ 0"}</strong><span>{plan.premium ? (yearly ? (english ? "/ year" : "/ ano") : (english ? "/ month" : "/ mês")) : (english ? "/ 7 days" : "/ 7 dias")}</span></p>
          </div>
          <Link href="/dashboard" className={styles.action}><span>{english ? "Start free trial" : "Começar grátis"}</span><ChevronRight size={16} aria-hidden="true" /></Link>
          <ul className={styles.features}>
            {plan.features.map(feature => <li key={feature}><span>{feature}</span><CheckCheck size={20} aria-label={english ? "Included" : "Incluído"} /></li>)}
          </ul>
          <p className={styles.note}>{plan.premium ? (english ? `After the trial: ${yearly ? "R$ 290/year" : "R$ 29/month"}. Cancel anytime.` : `Após o trial: ${yearly ? "R$ 290/ano" : "R$ 29/mês"}. Cancele quando quiser.`) : (english ? "Full access. No credit card required." : "Acesso completo. Sem cartão de crédito.")}</p>
        </article>)}
      </div>
    </div>
  </section>;
}
