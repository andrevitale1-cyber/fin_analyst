"use client";

import { useRef, useState } from "react";
import { useInView, useReducedMotion } from "framer-motion";
import { BarChart3, CircleAlert, DollarSign, Percent, TrendingUp, Pause, Play } from "lucide-react";
import cardStyles from "./SearchBenefit.module.css";
import styles from "./ScoreScaleBenefit.module.css";

export default function ScoreScaleBenefit({ locale }: { locale: string }) {
  const english = locale === "en";
  const card = useRef<HTMLElement>(null);
  const visible = useInView(card, { amount: .3 });
  const reduced = useReducedMotion();
  const [paused, setPaused] = useState(false);
  const running = visible && !reduced && !paused;
  const categories = [
    { label: english ? "Net Revenue" : "Receita líquida", icon: DollarSign, color: "#0075b5" },
    { label: english ? "Net Income" : "Lucro líquido", icon: Percent, color: "#a020ff" },
    { label: english ? "Net Debt" : "Dívida líquida", icon: CircleAlert, color: "#ff001f" },
    { label: english ? "Profitability" : "Rentabilidade", icon: TrendingUp, color: "#008c63" },
  ];

  return <article ref={card} className={`${cardStyles.card} ${styles.card}`}>
    <div className={styles.stage} data-running={running} role="img" aria-label={english ? "Illustrative analysis: net revenue, net income, net debt and profitability combine into an AI score of 5 out of 5" : "Análise ilustrativa: receita líquida, lucro líquido, dívida líquida e rentabilidade se combinam na nota de IA 5 de 5"}>
      <div className={styles.orbit} aria-hidden="true">
        {categories.map(({ label, icon: Icon, color }, index) => <div key={label} className={styles.arm} style={{ rotate: `${index * 90}deg` }}>
          <div className={styles.carrier}><div style={{ rotate: `${-index * 90}deg` }}><span className={styles.score}><Icon style={{ color }} /><span>{label}</span></span></div></div>
        </div>)}
      </div>
      <div className={styles.logo} aria-hidden="true"><div className={styles.logoContent}><BarChart3 /><span>AI</span></div></div>
      <div className={styles.result} aria-hidden="true">
        <div><span>AI SCORE</span><small>{english ? "Based on 4 fundamentals" : "Com base em 4 fundamentos"}</small></div>
        <strong>5<small>/5</small></strong>
      </div>
    </div>
    <button type="button" className={styles.control} onClick={() => setPaused(value => !value)} aria-label={paused ? (english ? "Play score animation" : "Reproduzir animação das notas") : (english ? "Pause score animation" : "Pausar animação das notas")}>
      {paused ? <Play size={18} /> : <Pause size={18} />}
    </button>
    <div className={cardStyles.copy}>
      <h3>{english ? "Understand the analysis at a glance" : "Entenda a análise de um olhar"}</h3>
      <p>{english ? "Revenue, income, debt and profitability come together in one AI score. Explore the detailed analysis behind each assessment." : "Receita, lucro, dívida e rentabilidade se combinam em uma nota de IA. Explore a análise detalhada por trás de cada avaliação."}</p>
    </div>
  </article>;
}
