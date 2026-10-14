import Image from "next/image";
import { ArrowRight, Check } from "lucide-react";
import { Link } from "@/i18n/routing";
import reportStyles from "./MetaAnalysisSection.module.css";
import styles from "./CallAnalysisSection.module.css";

const pages = [
  { width: 1623, height: 904, description: "Microsoft · Earnings Call · 2Q/2026. What explains the results." },
  { width: 1657, height: 862, description: "Guidance, projections, uncertainties and analyst questions." },
  { width: 1627, height: 628, description: "AI conclusion: confident management tone, risks and key moments." },
];

export default function CallAnalysisSection({ locale }: { locale: string }) {
  const english = locale === "en";
  const features = english
    ? ["Results explained", "Guidance & outlook", "Analyst Q&A", "Management tone"]
    : ["O que explica o resultado", "Guidance e perspectivas", "Perguntas dos analistas", "Tom da gestão"];

  return <section className={reportStyles.section} aria-labelledby="call-analysis-heading">
    <div className={`${reportStyles.layout} ${styles.layout}`}>
      <div className={reportStyles.copy}>
        <h2 id="call-analysis-heading">{english ? "What management says. " : "O que a gestão diz. "}<span>{english ? "What matters." : "O que importa."}</span></h2>
        <p>{english ? "AI highlights the explanations, guidance and management tone—without reading the full call transcript." : "A IA destaca as explicações, o guidance e o tom da gestão sem você precisar ler toda a transcrição do call."}</p>
        <span className={reportStyles.eyebrow}>{english ? "INSIDE THE CALL ANALYSIS" : "DENTRO DA ANÁLISE DO CALL"}</span>
        <ul>{features.map(feature => <li key={feature}><Check size={15} aria-hidden="true" />{feature}</li>)}</ul>
        <Link className={reportStyles.start} href="/dashboard">{english ? "Analyze an earnings call" : "Analisar um earnings call"}<ArrowRight size={17} aria-hidden="true" /></Link>
        <p className={reportStyles.caption}>{english ? "Example: Microsoft · 2Q/2026 · FinAnalyzer call analysis" : "Exemplo: Microsoft · 2Q/2026 · Análise de call do FinAnalyzer"}</p>
      </div>
      <article className={reportStyles.report} aria-label={english ? "Microsoft earnings call analysis preview" : "Prévia da análise do earnings call da Microsoft"}>
        <div className={styles.pages} role="region" tabIndex={0} aria-label={english ? "Scroll through the Microsoft call analysis" : "Role para ler a análise do call da Microsoft"}>
          {pages.map((page, index) => <a key={index} href={`/benefits/calls/microsoft-2q2026-${index + 1}.png`} target="_blank" rel="noopener noreferrer" aria-label={english ? `Open report page ${index + 1} at full size` : `Abrir página ${index + 1} do relatório em tamanho original`}>
            <Image src={`/benefits/calls/microsoft-2q2026-${index + 1}.png`} width={page.width} height={page.height} sizes="(max-width: 743px) calc(100vw - 32px), (max-width: 1023px) calc(50vw - 52px), 615px" alt={page.description} />
          </a>)}
        </div>
        <div className={reportStyles.reportFooter}>{english ? "Scroll to read · Select a page to enlarge" : "Role para ler · Selecione uma página para ampliar"}</div>
      </article>
    </div>
  </section>;
}
