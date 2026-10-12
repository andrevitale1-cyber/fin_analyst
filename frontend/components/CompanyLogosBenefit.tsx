"use client";

import { useRef, useState } from "react";
import { useInView, useReducedMotion } from "framer-motion";
import { Pause, Play } from "lucide-react";
import cardStyles from "./SearchBenefit.module.css";
import styles from "./CompanyLogosBenefit.module.css";

const companies = ["Microsoft", "Apple", "NVIDIA", "Google", "Meta", "Tesla"];

export default function CompanyLogosBenefit({ locale }: { locale: string }) {
  const english = locale === "en";
  const card = useRef<HTMLElement>(null);
  const visible = useInView(card, { amount: .3 });
  const reduced = useReducedMotion();
  const [paused, setPaused] = useState(false);

  return <article ref={card} className={`${cardStyles.card} ${styles.card}`}>
    <div className={styles.media} data-running={visible && !reduced && !paused} role="img" aria-label={companies.join(", ")}>
      {[companies, [...companies].reverse()].map((row, index) => <div key={index} className={styles.row} aria-hidden="true">
        <div className={styles.track}>{[0, 1].map(copy => <div className={styles.group} key={copy}>
          {row.map(name => <div className={styles.tile} key={name}><img src={`/benefits/logos/${name.toLowerCase()}.svg`} alt="" width="40" height="40" /><span>{name}</span></div>)}
        </div>)}</div>
      </div>)}
    </div>
    <button type="button" className={styles.control} onClick={() => setPaused(value => !value)} aria-label={paused ? (english ? "Play company logos" : "Reproduzir logos das empresas") : (english ? "Pause company logos" : "Pausar logos das empresas")}>
      {paused ? <Play size={18} /> : <Pause size={18} />}
    </button>
    <div className={cardStyles.copy}>
      <h3>{english ? "Big names. Clearer insights." : "Grandes empresas. Mais clareza."}</h3>
      <p>{english ? "Go beyond familiar logos. Turn company reports into a clear view of revenue, profitability, debt and financial performance." : "Vá além das marcas que você conhece. Transforme os relatórios das empresas em uma visão clara de receita, rentabilidade, dívida e desempenho financeiro."}</p>
    </div>
  </article>;
}
