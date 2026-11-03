"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowRight, ChevronLeft, ChevronRight, ShieldCheck, FileText, Check, AlertTriangle, Sparkles } from "lucide-react";
import { publishedReportForCompany } from "@/lib/publishedReports";
import apple from "./apple-report-preview.json";
import styles from "./FullReportShowcase.module.css";

const colors = ["#7580ff", "#b390ff", "#54cbbf", "#f0b66c", "#67dfaa"];

export default function FullReportShowcase({ locale }: { locale: string }) {
  const en = locale === "en";
  const rail = useRef<HTMLUListElement>(null);
  const [bounds, setBounds] = useState({ previous: false, next: false });
  const report = publishedReportForCompany("AAPL", locale)!;
  const number = (value: number, digits = 1) => new Intl.NumberFormat(en ? "en-US" : "pt-BR", { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(value);
  const billions = (value: number) => en ? `$${number(value)}B` : `US$ ${number(value)} bi`;
  const text = en ? {
    label: "FULL COMPANY REPORTS", title: "One company. Every perspective.",
    intro: "Go beyond the quarter. Explore the thesis, numbers and risks in our full Apple report.",
    action: "Read the Apple report", date: "Apple report · October 22, 2026", chapters: "Preview the Apple report sections",
    previous: "Previous report section", next: "Next report section", open: "Explore section",
    cards: [
      ["Investment thesis", "Understand what drives the business, what sustains its advantages and what could change the thesis."],
      ["Numbers at a glance", "Revenue, cash generation and margins, with the financial period clearly identified."],
      ["Inside the business", "See how each product and Services contribute to Apple's revenue."],
      ["Quality, with a reason", "A clear scorecard supported by evidence, with strengths and watchpoints."],
      ["The bigger financial picture", "Follow the financial history and distinguish structural progress from a single strong quarter."],
      ["Know what to watch", "Identify the risks, the counterarguments and the developments that could change the investment case."],
    ],
    thesis: "The device opens the door. Services deepen the relationship.",
    thesisBody: "Apple's ecosystem connects premium hardware, recurring usage and high-margin Services.",
    signals: ["Integrated ecosystem", "Recurring Services", "Cash generation"], quality: "Business quality", revenue: "Revenue", fcf: "Free cash flow", margin: "Operating margin",
    ttm: "TTM through Jun 27, 2026", nineMonths: "9M FY2026", mix: "Revenue composition", total: "FY2025 revenue",
    scores: ["Competitive moat", "Capital efficiency", "Growth"], scoreNote: "Quality of the business, independent of the share price.",
    history: "Revenue over six years", unit: "USD billions · FY2020–FY2025", risks: ["Services & regulation", "Product & AI execution", "China & supply chain"],
    riskNote: "What could change the thesis?", riskBody: "Monitor monetization, product relevance and the resilience of demand.",
  } : {
    label: "RELATÓRIOS COMPLETOS", title: "Uma empresa. Todas as perspectivas.",
    intro: "Vá além do trimestre. Explore a tese, os números e os riscos no nosso full report da Apple.",
    action: "Ler o report da Apple", date: "Report Apple · 22 de outubro de 2026", chapters: "Prévia das seções do report da Apple",
    previous: "Seção anterior do report", next: "Próxima seção do report", open: "Explorar seção",
    cards: [
      ["A tese por trás da empresa", "Entenda o que move o negócio, sustenta suas vantagens e pode mudar a tese."],
      ["Números em resumo", "Receita, geração de caixa e margens, com o período financeiro sempre identificado."],
      ["Por dentro do negócio", "Veja como cada produto e os Serviços contribuem para a receita da Apple."],
      ["Qualidade, com justificativa", "Um quadro de notas apoiado em evidências, com pontos fortes e o que acompanhar."],
      ["O histórico em perspectiva", "Acompanhe a evolução financeira e diferencie avanços estruturais de um trimestre forte."],
      ["Saiba o que acompanhar", "Conheça os riscos, os contrapontos e os acontecimentos que podem mudar a tese."],
    ],
    thesis: "O aparelho abre a porta. Os Serviços aprofundam a relação.",
    thesisBody: "O ecossistema da Apple conecta hardware premium, uso recorrente e Serviços de alta margem.",
    signals: ["Ecossistema integrado", "Serviços recorrentes", "Geração de caixa"], quality: "Qualidade do negócio", revenue: "Receita", fcf: "Fluxo de caixa livre", margin: "Margem operacional",
    ttm: "TTM até 27 de jun. de 2026", nineMonths: "9M FY2026", mix: "Composição da receita", total: "Receita FY2025",
    scores: ["Vantagem competitiva", "Eficiência de capital", "Crescimento"], scoreNote: "Qualidade do negócio, independente da cotação da ação.",
    history: "Seis anos de receita", unit: "US$ bilhões · FY2020–FY2025", risks: ["Serviços e regulação", "Produtos e execução em IA", "China e cadeia produtiva"],
    riskNote: "O que pode mudar a tese?", riskBody: "Acompanhe monetização, relevância dos produtos e resiliência da demanda.",
  };
  const anchors = ["investment_thesis", "indicadores_resumo", "business_model", "scorecard", "historico_qualidade_financeira", "risks"];

  useEffect(() => {
    const element = rail.current;
    if (!element) return;
    const update = () => setBounds({ previous: element.scrollLeft > 2, next: element.scrollLeft < element.scrollWidth - element.clientWidth - 2 });
    update();
    element.addEventListener("scroll", update, { passive: true });
    const observer = new ResizeObserver(update);
    observer.observe(element);
    if (element.firstElementChild) observer.observe(element.firstElementChild);
    return () => { element.removeEventListener("scroll", update); observer.disconnect(); };
  }, [locale]);

  function move(direction: number) {
    const element = rail.current;
    if (!element?.firstElementChild) return;
    const step = element.firstElementChild.getBoundingClientRect().width + parseFloat(getComputedStyle(element).columnGap);
    element.scrollBy({ left: step * direction, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }

  const frameHeader = (label: string) => <div className={styles.frameHeader}><img src="/benefits/logos/apple.svg" alt="" width="22" height="24" /><span>Apple <b>AAPL</b></span><small>{label}</small></div>;
  const previews = [
    <div className={styles.panel} key="thesis">{frameHeader(en ? "COMPANY REPORT" : "REPORT COMPLETO")}<div className={styles.thesis}><span className={styles.overline}><Sparkles size={13} /> {en ? "INVESTMENT THESIS" : "TESE DE INVESTIMENTO"}</span><strong>{text.thesis}</strong><p>{text.thesisBody}</p><div className={styles.signals}>{text.signals.map(label => <span key={label}><Check size={12} />{label}</span>)}</div></div></div>,
    <div className={styles.panel} key="numbers">{frameHeader(en ? "FINANCIALS" : "INDICADORES")}<div className={styles.metrics}><div className={styles.mainMetric}><span>{text.revenue}</span><strong>{billions(apple.revenueTTM)}</strong><small>{text.ttm}</small></div><div className={styles.metricPair}><div><span>{text.fcf}</span><strong>{billions(apple.freeCashFlowTTM)}</strong><small>{text.ttm}</small></div><div><span>{text.margin}</span><strong>{number(apple.operatingMargin9M)}%</strong><small>{text.nineMonths}</small></div></div><div className={styles.metricLine}><span /><span /><span /><span /><span /></div></div></div>,
    <div className={styles.panel} key="business">{frameHeader(en ? "BUSINESS" : "NEGÓCIO")}<div className={styles.mixHeader}><span>{text.mix}</span><strong>{billions(416.2)}</strong><small>{text.total}</small></div><div className={styles.mix}><div className={styles.donut} role="img" aria-label={apple.products.map(p => `${p.label}: ${number(p.share)}%`).join(", ")}><span>FY2025</span></div><div className={styles.legend}>{apple.products.map((p, i) => <div key={p.label}><i style={{ background: colors[i] }} /><span>{!en && p.label === "Services" ? "Serviços" : p.label.startsWith("Wearables") ? "Wearables" : p.label}</span><b>{number(p.share)}%</b></div>)}</div></div></div>,
    <div className={styles.panel} key="score">{frameHeader(en ? "SCORECARD" : "NOTAS")}<div className={styles.quality}><ShieldCheck size={22} /><span>{text.quality}</span><strong>{apple.qualityScore}<small>/5</small></strong><div className={styles.dots}>{[1,2,3,4,5].map(n => <i key={n} data-on={n <= apple.qualityScore} />)}</div></div><div className={styles.scoreRows}>{Object.values(apple.scores).map((score, i) => <div key={text.scores[i]}><span>{text.scores[i]}</span><div className={styles.scoreTrack}><i style={{ width: `${score * 20}%` }} /></div><b>{score}<small>/5</small></b></div>)}</div><p className={styles.scoreNote}>{text.scoreNote}</p></div>,
    <div className={styles.panel} key="history">{frameHeader(en ? "FINANCIAL HISTORY" : "HISTÓRICO FINANCEIRO")}<div className={styles.chartTitle}><span>{text.history}</span><strong>{billions(apple.revenue.at(-1)!)}</strong><small>{text.unit}</small></div><div className={styles.bars} role="img" aria-label={apple.years.map((year, i) => `${year}: ${billions(apple.revenue[i])}`).join(", ")}>{apple.revenue.map((value, i) => <div key={apple.years[i]}><span>{number(value, 0)}</span><i style={{ height: `${value / 450 * 100}%` }} /><small>{apple.years[i].replace("FY20", "’")}</small></div>)}</div></div>,
    <div className={styles.panel} key="risks">{frameHeader(en ? "RISKS & WATCHPOINTS" : "RISCOS E ATENÇÃO")}<div className={styles.risks}><span className={styles.overline}><AlertTriangle size={14} /> {en ? "WHAT TO WATCH" : "O QUE ACOMPANHAR"}</span><strong>{text.riskNote}</strong>{text.risks.map((risk, i) => <div key={risk}><span>{i + 1}</span>{risk}<ChevronRight size={14} /></div>)}<p>{text.riskBody}</p></div></div>,
  ];

  return <section id="full-reports" className={styles.section} aria-labelledby="full-report-showcase-title">
    <header className={styles.intro}><p className={styles.eyebrow}><FileText size={15} />{text.label}</p><h2 id="full-report-showcase-title">{text.title}</h2><p className={styles.description}>{text.intro}</p><a className={styles.cta} href={report.url}>{text.action}<ArrowRight size={18} /></a><small>{text.date}</small></header>
    <div className={styles.carousel}>
      <ul id="apple-report-track" ref={rail} className={styles.rail} aria-label={text.chapters} tabIndex={0} onKeyDown={event => { if (event.target === event.currentTarget && ["ArrowLeft","ArrowRight"].includes(event.key)) { event.preventDefault(); move(event.key === "ArrowRight" ? 1 : -1); } }}>
        {text.cards.map(([title, description], index) => <li key={anchors[index]} className={styles.card}><a href={`${report.url}#${anchors[index]}`} aria-label={`${title} · Apple`}><div className={styles.visual}>{previews[index]}</div><div className={styles.copy}><h3>{title}</h3><p>{description}</p><span className={styles.explore}>{text.open}<ArrowRight size={15} /></span></div></a></li>)}
      </ul>
      <button className={`${styles.arrow} ${styles.previous}`} disabled={!bounds.previous} aria-label={text.previous} aria-controls="apple-report-track" onClick={() => move(-1)}><ChevronLeft size={28} /></button>
      <button className={`${styles.arrow} ${styles.next}`} disabled={!bounds.next} aria-label={text.next} aria-controls="apple-report-track" onClick={() => move(1)}><ChevronRight size={28} /></button>
    </div>
  </section>;
}
