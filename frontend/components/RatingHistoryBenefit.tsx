"use client";
import { useEffect, useId, useRef, useState } from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";
import styles from "./SearchBenefit.module.css";
import chartStyles from "./RatingHistoryBenefit.module.css";

const scores = [3.5, 4, 3, 3.6, 3.9, 4.8, 4.2, 4.6, 3.7, 4.4, 4.6];
const points = scores.map((score, index) => ({ x: 22 + index * 36, y: 220 - score * 36 }));
// Smooth midpoints keep the same rounded line treatment as the reference chart.
const line = points.reduce((path, point, index) => {
  if (!index) return `M ${point.x} ${point.y}`;
  const prev = points[index - 1];
  const middle = (prev.x + point.x) / 2;
  return `${path} C ${middle} ${prev.y}, ${middle} ${point.y}, ${point.x} ${point.y}`;
}, "");

export default function RatingHistoryBenefit({ locale }: { locale: string }) {
  const english = locale === "en";
  const ref = useRef<HTMLElement>(null);
  const visible = useInView(ref, { amount: .3 });
  const reduced = useReducedMotion();
  const [active, setActive] = useState(5);
  const [interacting, setInteracting] = useState(false);
  const gradient = useId().replace(/:/g, "");
  useEffect(() => {
    if (!visible || reduced || interacting) return;
    const timer = window.setInterval(() => setActive(index => (index + 1) % scores.length), 1600);
    return () => window.clearInterval(timer);
  }, [visible, reduced, interacting]);
  const selected = points[active];
  const tooltipX = Math.max(30, Math.min(350, selected.x));
  return <motion.article ref={ref} className={styles.card} initial={reduced ? false : { opacity: 0, y: 32 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: .15 }} transition={{ duration: .6 }}>
    <div className={chartStyles.chart}>
      <div className={chartStyles.header}><span>Microsoft</span><span className={chartStyles.filter}>{english ? "Quarterly scores" : "Notas trimestrais"}</span></div>
      <p className={chartStyles.example}>{english ? "Hypothetical example · scores from 0 to 5" : "Exemplo hipotético · notas de 0 a 5"}</p>
      <svg viewBox="0 0 404 260" role="img" aria-label={english ? "Hypothetical Microsoft score history. These are illustrative values, not actual company ratings." : "Histórico hipotético de notas da Microsoft. Valores ilustrativos, não são avaliações reais da empresa."}>
        <defs><linearGradient id={gradient} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#5446ff" stopOpacity=".28" /><stop offset="100%" stopColor="#698eff" stopOpacity="0" /></linearGradient></defs>
        {[40, 76, 112, 148, 184, 220].map(y => <line key={y} x1="22" x2="382" y1={y} y2={y} stroke="#e1e3ec" strokeDasharray="6 6" />)}
        <path d={`${line} L 382 238 L 22 238 Z`} fill={`url(#${gradient})`} />
        <motion.path d={line} fill="none" stroke="#4c40ff" strokeWidth="2.5" strokeLinecap="round" initial={reduced ? false : { pathLength: 0 }} whileInView={{ pathLength: 1 }} viewport={{ once: true }} transition={{ duration: 2 }} />
        <motion.circle r="4" fill="#4c40ff" stroke="white" strokeWidth="2" animate={{ cx: selected.x, cy: selected.y }} transition={{ duration: reduced ? 0 : .5 }} />
        <motion.g animate={{ x: tooltipX - 30, y: Math.max(4, selected.y - 48) }} transition={{ duration: reduced ? 0 : .5 }}>
          <rect width="60" height="30" rx="5" fill="#e6e4ff" /><text x="30" y="20" textAnchor="middle" fill="#4c40ff" fontSize="13" fontWeight="600">{scores[active].toFixed(1)}/5</text>
        </motion.g>
        {points.map((point, index) => <circle key={index} cx={point.x} cy={point.y} r="14" fill="transparent" tabIndex={0} role="button" aria-label={`${english ? "Example" : "Exemplo"} ${index + 1}: ${scores[index]}/5`} onMouseEnter={() => { setInteracting(true); setActive(index); }} onMouseLeave={() => setInteracting(false)} onFocus={() => { setInteracting(true); setActive(index); }} onBlur={() => setInteracting(false)} onClick={() => setActive(index)} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setActive(index); } }} />)}
      </svg>
    </div>
    <div className={styles.copy}>
      <p className={styles.label}>{english ? "SCORE HISTORY" : "HISTÓRICO DE NOTAS"}</p>
      <h3>{english ? "See how the fundamentals evolve" : "Veja a evolução dos fundamentos"}</h3>
      <p>{english ? "Compare scores across quarters and identify changes in a company’s fundamentals. Microsoft history shown as a hypothetical example." : "Compare notas entre trimestres e identifique mudanças nos fundamentos da empresa. Histórico da Microsoft apresentado como exemplo hipotético."}</p>
    </div>
  </motion.article>;
}
