"use client";

import { useRef } from "react";
import { useInView } from "framer-motion";
import cardStyles from "./SearchBenefit.module.css";
import styles from "./CompanyLogosBenefit.module.css";
import companies from "./benefit-companies.json";

const rows = [companies.filter((_, i) => i % 2 === 0), companies.filter((_, i) => i % 2 === 1)];

export default function CompanyLogosBenefit({ locale }: { locale: string }) {
  const english = locale === "en";
  const card = useRef<HTMLElement>(null);
  const visible = useInView(card, { amount: .3 });

  return <article ref={card} className={`${cardStyles.card} ${styles.card}`}>
    <div className={styles.media} data-running={visible} role="img" aria-label={companies.map(company => company.name).join(", ")}>
      {rows.map((row, index) => <div key={index} className={styles.row} aria-hidden="true">
        <div className={styles.track}>{[0, 1].map(copy => <div className={styles.group} key={copy}>
          {row.map(({name, logo}) => <div className={styles.tile} key={name}><img src={logo} alt="" width="40" height="40" /><span>{name}</span></div>)}
        </div>)}</div>
      </div>)}
    </div>
    <div className={cardStyles.copy}>
      <h3>{english ? "Any company. Every result." : "Qualquer empresa. Cada resultado."}</h3>
      <p>{english ? "Analyze results from any company using its official financial reports. Find the document automatically or upload it yourself, and get a clear view of revenue, profitability, debt and financial performance." : "Analise resultados de qualquer empresa a partir de seus relatórios financeiros oficiais. Encontre o documento automaticamente ou envie o arquivo e obtenha uma visão clara de receita, rentabilidade, dívida e desempenho financeiro."}</p>
    </div>
  </article>;
}
