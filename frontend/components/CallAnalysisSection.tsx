import { ArrowRight, Check, FileText } from "lucide-react";
import { Link } from "@/i18n/routing";
import reportStyles from "./MetaAnalysisSection.module.css";
import styles from "./CallAnalysisSection.module.css";
import ExampleAnalysis from "./ExampleAnalysis";
import { spcxCall } from "@/lib/landingExamples";

export default function CallAnalysisSection({ locale }: { locale: string }) {
  const english = locale === "en";
  const period = english ? "3Q/2026" : "3T/2026";
  const features = english
    ? ["Results explained", "Figures from the call", "Capital allocation", "Guidance & outlook", "Risks & evasive points", "Analyst Q&A", "Metrics to follow", "Management tone"]
    : ["O que explica o resultado", "Números citados na call", "Alocação de capital", "Guidance e perspectivas", "Riscos e pontos evasivos", "Perguntas dos analistas", "Métricas para acompanhar", "Tom da gestão"];

  return <section className={reportStyles.section} aria-labelledby="call-analysis-heading">
    <div className={`${reportStyles.layout} ${styles.layout}`}>
      <div className={reportStyles.copy}>
        <h2 id="call-analysis-heading">{english ? "What management says. " : "O que a gestão diz. "}<span>{english ? "What matters." : "O que importa."}</span></h2>
        <p>{english ? "AI highlights the explanations, guidance and management tone—without reading the full call transcript." : "A IA destaca as explicações, o guidance e o tom da gestão sem você precisar ler toda a transcrição do call."}</p>
        <span className={reportStyles.eyebrow}>{english ? "INSIDE THE CALL ANALYSIS" : "DENTRO DA ANÁLISE DO CALL"}</span>
        <ul>{features.map(feature => <li key={feature}><Check size={15} aria-hidden="true" />{feature}</li>)}</ul>
        <Link className={reportStyles.start} href="/dashboard">{english ? "Analyze an earnings call" : "Analisar um earnings call"}<ArrowRight size={17} aria-hidden="true" /></Link>
        <p className={reportStyles.caption}>{english ? `Example: SpaceX · ${period} · FinAnalyser call analysis` : `Exemplo: SpaceX · ${period} · Análise de call do FinAnalyser`}</p>
      </div>
      <article className={reportStyles.report} aria-label={english ? "SpaceX earnings call analysis preview" : "Prévia da análise do earnings call da SpaceX"}>
        <header className={reportStyles.reportHeader}>
          <div className={reportStyles.company}><div className={`${reportStyles.logo} ${styles.monogram}`} aria-hidden="true">SX</div><div><h3>SpaceX <span>SPCX</span></h3><p>{period} · Earnings Call</p></div></div>
        </header>
        <h4 className={reportStyles.thesisHeading}><FileText size={22} />{english ? "Call Analysis" : "Análise do call"}</h4>
        <ExampleAnalysis className={reportStyles.text} text={english ? spcxCall.en : spcxCall.pt}
          label={english ? "Read the full SpaceX call analysis" : "Leia a análise completa do call da SpaceX"}
          hint={english ? "Swipe to read the full analysis" : "Arraste para ler a análise completa"} />
        <div className={reportStyles.reportFooter}>{english ? "Scroll or swipe inside the card to explore" : "Role ou arraste dentro do card para explorar"} ↓</div>
      </article>
    </div>
  </section>;
}
