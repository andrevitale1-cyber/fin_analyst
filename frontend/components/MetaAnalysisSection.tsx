"use client";

import { Check, CircleAlert, DollarSign, FileText, Percent, TrendingUp, ArrowRight } from "lucide-react";
import { Link } from "@/i18n/routing";
import styles from "./MetaAnalysisSection.module.css";
import ExampleAnalysis from "./ExampleAnalysis";
import { amznQuarter, amznScores } from "@/lib/landingExamples";

export default function MetaAnalysisSection({ locale }: { locale: string }) {
  const english = locale === "en";
  const period = english ? "3Q/2026" : "3T/2026";
  const metrics = [
    { label: english ? "Net Revenue" : "Receita líquida", score: amznScores.revenue, icon: DollarSign, color: "#0075b5" },
    { label: english ? "Net Income" : "Lucro líquido", score: amznScores.income, icon: Percent, color: "#a020ff" },
    { label: english ? "Net Debt" : "Dívida líquida", score: amznScores.debt, icon: CircleAlert, color: "#ff001f" },
    { label: english ? "Profitability" : "Rentabilidade", score: amznScores.profitability, icon: TrendingUp, color: "#008c63" },
  ];
  const features = english ? ["Revenue growth", "Margins and profitability", "Cash flow and debt", "Quality of earnings", "Market reaction", "AI conclusion"] : ["Crescimento da receita", "Margens e rentabilidade", "Caixa e dívida", "Qualidade do lucro", "Reação do mercado", "Conclusão da IA"];

  return <section className={styles.section} aria-labelledby="meta-analysis-heading">
    <div className={styles.layout}>
      <article className={styles.report} aria-label={english ? `FinAnalyser report preview: AMZN, ${period}` : `Prévia do relatório FinAnalyser: AMZN, ${period}`}>
        <header className={styles.reportHeader}>
          <div className={styles.company}><div className={styles.logo}><img src="/benefits/company-logos/AMZN.webp" alt="" width={34} height={34} /></div><div><h3>Amazon <span>AMZN</span></h3><p>{period} · {english ? "Analysis Report" : "Relatório de análise"}</p></div></div>
          <div className={styles.finalScore}><span>AI SCORE</span><strong>{amznScores.overall}<small>/5</small></strong><small>{english ? "Based on 4 fundamentals" : "Com base em 4 fundamentos"}</small></div>
        </header>
        <div className={styles.metrics}>{metrics.map(({label, score, icon: Icon, color}) => <div className={styles.metric} key={label}><div className={styles.icon}><Icon size={19} style={{color}} /></div><div><span>{label}</span><strong style={{color: score <= 3 ? "#ba7800" : "#00875d"}}>{score}<small>/5</small></strong></div></div>)}</div>
        <h4 className={styles.thesisHeading}><FileText size={22} />{english ? "Investment Thesis" : "Tese de investimento"}</h4>
        <ExampleAnalysis className={styles.text} text={english ? amznQuarter.en : amznQuarter.pt}
          label={english ? "Read the full Amazon analysis" : "Leia a análise completa da Amazon"}
          hint={english ? "Swipe to read the full analysis" : "Arraste para ler a análise completa"} />
        <div className={styles.reportFooter}>{english ? "Scroll or swipe inside the card to explore" : "Role ou arraste dentro do card para explorar"} ↓</div>
      </article>
      <div className={styles.copy}>
        <h2 id="meta-analysis-heading">{english ? "AI analysis. " : "Análise por IA. "}<span>{english ? "Clear insights." : "Mais clareza."}</span></h2>
        <p>{english ? "Understand the quarter’s key results, strengths and risks—without reading the entire report." : "Entenda os principais resultados, pontos fortes e riscos do trimestre sem ler o relatório inteiro."}</p>
        <span className={styles.eyebrow}>{english ? "INSIDE THE AI ANALYSIS" : "DENTRO DA ANÁLISE DE IA"}</span>
        <ul>{features.map(feature => <li key={feature}><Check size={15} />{feature}</li>)}</ul>
        <Link className={styles.start} href="/dashboard">{english ? "Explore your next analysis" : "Explore sua próxima análise"}<ArrowRight size={17} /></Link>
        <p className={styles.caption}>{english ? `Example: Amazon · ${period} · FinAnalyser analysis` : `Exemplo: Amazon · ${period} · Análise do FinAnalyser`}</p>
      </div>
    </div>
  </section>;
}
