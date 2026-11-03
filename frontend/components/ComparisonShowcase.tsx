import { ArrowUpRight, BarChart3, Swords, Trophy } from "lucide-react";
import styles from "./ComparisonShowcase.module.css";

function CheckMark() {
  return <svg width="25" height="24" viewBox="0 0 25 24" fill="none" aria-hidden="true"><path d="M12.5 21C17.4706 21 21.5 16.9706 21.5 12C21.5 7.02944 17.4706 3 12.5 3C7.52944 3 3.5 7.02944 3.5 12C3.5 16.9706 7.52944 21 12.5 21Z" fill="#2BEB78" /><path d="M8.75 12.75L11 15L16.25 9.75" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>;
}

// Real AMZN × GOOGL duel and fiscal periods supplied by the user; no live generation on the landing page.
export default function ComparisonShowcase({ locale }: { locale: string }) {
  const en = locale === "en";
  const text = en ? {
    title: "Compare results with clarity.",
    intro: "Put companies side by side. Follow their scores over time and understand which quarter was stronger — and why.",
    example: "A real comparison · AMZN × GOOGL · 3Q/2026", company: "Company", period: "Saved quarterly result", fiscal: "Fiscal end: Sep 30, 2026",
    verdict: "QUARTERLY RESULTS VERDICT", winner: "GOOGL delivered the stronger result", confidence: "Confidence: moderate",
    summary: "Alphabet leads on growth, profitability and balance-sheet resources relative to long-term debt.",
    dimensions: ["Growth", "Profitability", "Balance sheet"],
    caveat: "Cash generation and outlook remain insufficient for a comparable verdict.",
    benefits: ["Compare two quarterly results with AI", "Track scores for up to three companies", "Understand the evidence behind the verdict"],
    action: "Compare companies", premium: "A Premium feature. A new duel uses one monthly analysis; reopening a saved duel is free.",
    flow: "Two saved results feed into FinAnalyzer's comparison, which explains the verdict and its limits.",
  } : {
    title: "Compare resultados com clareza.",
    intro: "Coloque empresas lado a lado. Acompanhe as notas ao longo do tempo e entenda qual trimestre foi mais forte — e por quê.",
    example: "Um comparativo real · AMZN × GOOGL · 3T/2026", company: "Empresa", period: "Resultado trimestral salvo", fiscal: "Encerramento fiscal: 30 de set. de 2026",
    verdict: "VEREDITO DOS RESULTADOS TRIMESTRAIS", winner: "GOOGL entregou o resultado mais forte", confidence: "Confiança: moderada",
    summary: "A Alphabet lidera em crescimento, rentabilidade e recursos de balanço em relação à dívida de longo prazo.",
    dimensions: ["Crescimento", "Rentabilidade", "Balanço"],
    caveat: "Geração de caixa e perspectivas têm evidência insuficiente para um veredito comparável.",
    benefits: ["Compare dois resultados trimestrais com IA", "Acompanhe as notas de até três empresas", "Entenda as evidências por trás do veredito"],
    action: "Comparar empresas", premium: "Um recurso Premium. Um novo duelo usa uma análise mensal; reabrir um duelo salvo é gratuito.",
    flow: "Dois resultados salvos entram no comparador do FinAnalyzer, que explica o veredito e seus limites.",
  };

  return <section id="comparar-resultados" className={styles.section} aria-labelledby="comparison-showcase-title">
    <div className={styles.surface}>
      <header className={styles.intro}><h2 id="comparison-showcase-title">{text.title}</h2><p>{text.intro}</p></header>
      <div className={styles.scene} role="group" aria-label={text.flow}>
        <div className={styles.inputs}>
          {[{ symbol: "AMZN", name: "Amazon", logo: "/benefits/company-logos/AMZN.webp" }, { symbol: "GOOGL", name: "Alphabet", logo: "/benefits/company-logos/GOOG.webp" }].map((company, i) => <article key={company.symbol} className={styles.company} aria-label={`${text.company} ${i === 0 ? "A" : "B"}: ${company.name}`}>
            <div className={styles.companyHeader}><img src={company.logo} alt={company.name} width="38" height="38" /><div><strong>{company.symbol}</strong><span>{text.company} {i === 0 ? "A" : "B"} · {company.name}</span></div></div>
            <p className={styles.periodLabel}>{text.period}</p><div className={styles.period}><span>{en ? "3Q/2026" : "3T/2026"}</span><small>{en ? "Nov 2, 2026" : "2 de nov. de 2026"}</small></div><small className={styles.fiscal}>{text.fiscal}</small>
          </article>)}
        </div>
        <div className={styles.connection} aria-hidden="true"><i className={`${styles.flow} ${styles.flowIn}`} /><i className={`${styles.flow} ${styles.flowOut}`} /><div className={styles.brand}><BarChart3 size={38} /></div><span>FinAnalyzer</span><Swords className={styles.swords} size={19} /></div>
        <article className={styles.verdict} aria-label={text.winner}>
          <p className={styles.eyebrow}><Trophy size={17} />{text.verdict}</p><h3>{text.winner}</h3><p className={styles.meta}>AMZN · {en ? "3Q/2026" : "3T/2026"}<span />GOOGL · {en ? "3Q/2026" : "3T/2026"}</p><p className={styles.confidence}>{text.confidence}</p>
          <p className={styles.summary}>{text.summary}</p><div className={styles.dimensions}>{text.dimensions.map(label => <span key={label}><CheckMark />{label}</span>)}</div><p className={styles.caveat}>{text.caveat}</p>
        </article>
      </div>
      <p className={styles.example}>{text.example}</p>
      <ul className={styles.benefits}>{text.benefits.map(benefit => <li key={benefit}><CheckMark /><span>{benefit}</span></li>)}</ul>
      <div className={styles.action}><a href={`/${en ? "en" : "pt"}/dashboard?view=comparison`}>{text.action}<ArrowUpRight size={18} /></a><p>{text.premium}</p></div>
    </div>
  </section>;
}
