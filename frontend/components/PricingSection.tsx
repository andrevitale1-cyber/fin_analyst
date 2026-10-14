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
        ["Unlimited AI analyses", "Understand key results without reading every page."],
        ["Compare companies", "Review differences to support your decisions."],
        ["Analyze earnings calls", "Bring call insights into your research."],
        ["Download full reports", "Keep a copy of each finished analysis."],
        ["No credit card required", "Explore full access before choosing a plan."],
      ]
    : [
        ["Análises de IA ilimitadas", "Entenda os principais resultados sem ler cada página."],
        ["Compare empresas", "Veja diferenças para apoiar suas decisões."],
        ["Analise earnings calls", "Inclua os insights das calls na sua pesquisa."],
        ["Baixe relatórios completos", "Guarde uma cópia de cada análise concluída."],
        ["Sem cartão de crédito", "Explore o acesso completo antes de escolher um plano."],
      ];
  const premiumFeatures = english
    ? [
        ["Unlimited AI analyses", "Get straight to the drivers, strengths and risks."],
        ["Complete reports", "Read AI insights on screen or download the full report."],
        ["Unlimited analysis history", "Return to saved analyses whenever you need them."],
        ["Company comparisons", "Review companies side by side."],
        ["Documents and earnings calls", "Upload without limits and explore management’s outlook."],
        ["Support and priority", "Get help by email and have analyses prioritized."],
      ]
    : [
        ["Análises de IA ilimitadas", "Vá direto aos fatores, pontos fortes e riscos."],
        ["Relatórios completos", "Leia a análise na tela ou baixe o relatório completo."],
        ["Histórico de análises ilimitado", "Volte às análises salvas quando precisar."],
        ["Comparação de empresas", "Revise empresas lado a lado."],
        ["Documentos e earnings calls", "Envie arquivos sem limite e entenda as perspectivas da gestão."],
        ["Suporte e prioridade", "Receba ajuda por e-mail e tenha análises priorizadas."],
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
        <p className={styles.saving}>{yearly ? (english ? "2 months free with yearly billing" : "2 meses grátis no plano anual") : (english ? "Start with a 7-day free trial" : "Comece com 7 dias grátis")}</p>
      </header>
      <div className={styles.plans}>
        {[{ name: english ? "Free Trial" : "Trial gratuito", description: english ? "Try the full workflow for 7 days, with no credit card." : "Experimente o fluxo completo por 7 dias, sem cartão de crédito.", features: trialFeatures, premium: false }, { name: "Premium", description: english ? "Analyze faster. Keep your research within reach." : "Analise com agilidade. Tenha sua pesquisa sempre à mão.", features: premiumFeatures, premium: true }].map(plan => <article key={plan.name} className={`${styles.card} ${plan.premium ? styles.premium : ""}`} aria-label={plan.name}>
          {plan.premium && <span className={styles.badge}>{english ? "Full access" : "Acesso completo"}</span>}
          <div className={styles.heading}>
            <h3>{plan.premium ? <Sparkles size={20} aria-hidden="true" /> : <Zap size={20} aria-hidden="true" />}{plan.name}</h3>
            <p className={styles.description}>{plan.description}</p>
            <p className={styles.price}><strong>{plan.premium ? (yearly ? "R$ 290" : "R$ 29") : "R$ 0"}</strong><span>{plan.premium ? (yearly ? (english ? "/ year" : "/ ano") : (english ? "/ month" : "/ mês")) : (english ? "/ 7 days" : "/ 7 dias")}</span></p>
          </div>
          <Link href="/dashboard" className={styles.action}><span>{english ? "Start free trial" : "Começar grátis"}</span><ChevronRight size={16} aria-hidden="true" /></Link>
          <ul className={styles.features}>
            {plan.features.map(([title, detail]) => <li key={title}><span><strong>{title}</strong><small>{detail}</small></span><CheckCheck size={20} aria-label={english ? "Included" : "Incluído"} /></li>)}
          </ul>
          <p className={styles.note}>{plan.premium ? (english ? `After the trial: ${yearly ? "R$ 290/year" : "R$ 29/month"}. Cancel anytime.` : `Após o trial: ${yearly ? "R$ 290/ano" : "R$ 29/mês"}. Cancele quando quiser.`) : (english ? "Full access. No credit card required." : "Acesso completo. Sem cartão de crédito.")}</p>
        </article>)}
      </div>
    </div>
  </section>;
}
