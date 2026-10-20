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
        ["3 quarterly or call analyses per day", "Choose automatic search or upload your document."],
        ["1 private full report per day", "Research a company and keep the report in your library."],
        ["Public report gallery", "Read the available public company reports."],
        ["Your saved analyses", "Revisit your own research without using a new daily allowance."],
        ["No credit card required", "Start with the Free plan. Limits renew daily."],
      ]
    : [
        ["3 análises trimestrais ou de calls por dia", "Escolha busca automática ou envie seu documento."],
        ["1 relatório completo privado por dia", "Pesquise uma empresa e guarde o relatório na sua biblioteca."],
        ["Galeria de relatórios públicos", "Leia os relatórios públicos de empresas disponíveis."],
        ["Suas análises salvas", "Consulte sua pesquisa sem consumir uma nova análise diária."],
        ["Sem cartão de crédito", "Comece no Free. Os limites renovam diariamente."],
      ];
  const premiumFeatures = english
    ? [
        ["Unlimited AI analyses", "Get straight to the drivers, strengths and risks."],
        ["Complete reports", "Explore the thesis, fundamentals, risks and sources in one place."],
        ["Unlimited analysis history", "Return to saved analyses whenever you need them."],
        ["Company comparisons", "Review companies side by side."],
        ["Documents and earnings calls", "Upload without limits and explore management’s outlook."],
        ["Support and priority", "Get help by email and have analyses prioritized."],
      ]
    : [
        ["Análises de IA ilimitadas", "Vá direto aos fatores, pontos fortes e riscos."],
        ["Relatórios completos", "Explore a tese, os fundamentos, os riscos e as fontes em um só lugar."],
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
        <p className={styles.saving}>{yearly ? (english ? "2 months free with yearly billing" : "2 meses grátis no plano anual") : (english ? "Start with the Free plan" : "Comece com o plano Free")}</p>
      </header>
      <div className={styles.plans}>
        {[{ name: "Free", description: english ? "Public reports, 3 analyses and 1 private full report per day." : "Relatórios públicos, 3 análises e 1 full report privado por dia.", features: trialFeatures, premium: false }, { name: "Premium", description: english ? "Analyze faster. Keep your research within reach." : "Analise com agilidade. Tenha sua pesquisa sempre à mão.", features: premiumFeatures, premium: true }].map(plan => <article key={plan.name} className={`${styles.card} ${plan.premium ? styles.premium : ""}`} aria-label={plan.name}>
          {plan.premium && <span className={styles.badge}>{english ? "Full access" : "Acesso completo"}</span>}
          <div className={styles.heading}>
            <h3>{plan.premium ? <Sparkles size={20} aria-hidden="true" /> : <Zap size={20} aria-hidden="true" />}{plan.name}</h3>
            <p className={styles.description}>{plan.description}</p>
            <p className={styles.price}><strong>{plan.premium ? (yearly ? "R$ 290" : "R$ 29") : "R$ 0"}</strong><span>{plan.premium ? (yearly ? (english ? "/ year" : "/ ano") : (english ? "/ month" : "/ mês")) : (english ? "/ free" : "/ grátis")}</span></p>
          </div>
          <Link href="/dashboard" className={styles.action}><span>{english ? "Start free" : "Começar grátis"}</span><ChevronRight size={16} aria-hidden="true" /></Link>
          <ul className={styles.features}>
            {plan.features.map(([title, detail]) => <li key={title}><span><strong>{title}</strong><small>{detail}</small></span><CheckCheck size={20} aria-label={english ? "Included" : "Incluído"} /></li>)}
          </ul>
          <p className={styles.note}>{plan.premium ? (english ? `Premium: ${yearly ? "R$ 290/year" : "R$ 29/month"}. Cancel anytime.` : `Premium: ${yearly ? "R$ 290/ano" : "R$ 29/mês"}. Cancele quando quiser.`) : (english ? "Daily limits renew at midnight (São Paulo). No credit card required." : "Limites diários renovam à meia-noite (São Paulo). Sem cartão de crédito.")}</p>
        </article>)}
      </div>
    </div>
  </section>;
}
