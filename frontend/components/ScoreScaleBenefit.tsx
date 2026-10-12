"use client";

import { useRef, useState } from "react";
import { useInView, useReducedMotion } from "framer-motion";
import { BarChart3, Pause, Play } from "lucide-react";
import cardStyles from "./SearchBenefit.module.css";
import styles from "./ScoreScaleBenefit.module.css";

export default function ScoreScaleBenefit({ locale }: { locale: string }) {
  const english = locale === "en";
  const card = useRef<HTMLElement>(null);
  const visible = useInView(card, { amount: .3 });
  const reduced = useReducedMotion();
  const [paused, setPaused] = useState(false);
  const running = visible && !reduced && !paused;

  return <article ref={card} className={`${cardStyles.card} ${styles.card}`}>
    <div className={styles.stage} data-running={running} role="img" aria-label={english ? "FinAnalyzer rating scale: whole-number scores from 1 to 5" : "Escala de avaliação do FinAnalyzer: notas inteiras de 1 a 5"}>
      <div className={styles.orbit} aria-hidden="true">
        {[1, 2, 3, 4, 5].map((score, index) => <div key={score} className={styles.arm} style={{ rotate: `${index * 72}deg` }}>
          <div className={styles.carrier}><div style={{ rotate: `${-index * 72}deg` }}><span className={styles.score}>{score}</span></div></div>
        </div>)}
      </div>
      <div className={styles.logo} aria-hidden="true"><BarChart3 /><span>AI</span></div>
    </div>
    <button type="button" className={styles.control} onClick={() => setPaused(value => !value)} aria-label={paused ? (english ? "Play score animation" : "Reproduzir animação das notas") : (english ? "Pause score animation" : "Pausar animação das notas")}>
      {paused ? <Play size={18} /> : <Pause size={18} />}
    </button>
    <div className={cardStyles.copy}>
      <h3>{english ? "Understand the analysis at a glance" : "Entenda a análise de um olhar"}</h3>
      <p>{english ? "A clear scale from 1 to 5 helps you interpret the fundamentals and compare results. Each score is supported by the detailed analysis." : "Uma escala clara de 1 a 5 ajuda a interpretar os fundamentos e comparar resultados. Cada nota é acompanhada da análise detalhada."}</p>
    </div>
  </article>;
}
