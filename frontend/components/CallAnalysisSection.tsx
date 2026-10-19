import { ArrowRight, Check, FileText } from "lucide-react";
import { Link } from "@/i18n/routing";
import { splitBold } from "@/lib/analysisText";
import reportStyles from "./MetaAnalysisSection.module.css";
import styles from "./CallAnalysisSection.module.css";
import TypingPreview from "./TypingPreview";

// Original English analysis transcribed from the supplied report screenshots.
const analysis = [
  { title: "1. What explains the results", paragraphs: [
    "**Microsoft Cloud revenue surpassed $50 billion** for the first time this quarter, up **26% year-over-year**, powered by accelerating demand and platform strength. AI-driven workloads, infrastructure expansion, and new offerings in both first- and third-party solutions are major contributors. **AI reading:** Cloud is the central growth engine and its success is broad-based across hyperscale infrastructure, agent platforms, and application layers.",
    "**Total company revenue was $81.3 billion, up 17%.** Operating income increased **21%** and EPS was up **24%** (adjusted), pointing to strong operational leverage. Gross margin slightly contracted to **68%** (down y/y) reflecting higher AI infrastructure investment, with continued efficiency gains partially offsetting this. **AI reading:** The top-line growth is robust, efficiency is healthy, but margin pressure from accelerated AI investment is visible.",
    "**Commercial bookings and remaining performance obligation surged** due to multi-year commitments (notably OpenAI and Anthropic) and broad core business growth. Commercial RPO is **up 110% y/y** to **$625B**, with notable durability and diversification. **AI reading:** The scale and breadth of contract wins buttress future revenue visibility.",
  ] },
  { title: "2. Guidance, projections, clues, conditions, and uncertainties", paragraphs: [
    "**Formal Q3 guidance:** Revenue **$80.65–$81.75B (15–17% growth)**, COGS up 22–23%, OPEX up 10–11%, operating margin down slightly y/y. Capex to decrease sequentially but mix of short-lived assets stays high. AI investments and memory pricing are key variables.",
    "**Segment guidance:** Productivity/Business Processes revenue up 14–15%; **M365 commercial cloud 13–14%**; Dynamics 365 high-teens; Intelligent Cloud up 27–29%, Azure up 37–38%. More Personal Computing guidance is weak (revenue down, OEM/Devices down).",
    "**Conditions and clues:** Management stresses ongoing supply constraints (\"demand continues to exceed our supply\"), variability due to memory pricing and capacity additions. OpenAI contract in RPO will cause some quarterly bookings volatility. Guidance for FY26 operating margin is raised to \"up slightly\".",
    "**Key uncertainty:** How quickly capacity can be added to meet AI demand and offset memory price hikes, and the longer-term ROI profile of heavy, multi-use Capex.",
  ] },
  { title: "3. Q&A", paragraphs: [
    "**ROI for Capex and Azure growth:** Investors asked how Capex maps to revenue and ROI. Amy Hood clarified that Capex is distributed across Azure, copilot workloads, and R&D—not just Azure growth—emphasizing a portfolio LTV approach. Useful life risk is mitigated, as much AI hardware is already contracted for full term; efficiency improves over time.",
    "**OpenAI RPO exposure:** On concern over 45% of RPO tied to OpenAI, Hood underscored confidence in the breadth/diversity of the broader RPO (55% non-OpenAI), which is large and growing strongly. The OpenAI relationship is described as robust and strategic. No alarming signals on concentration risk were communicated.",
    "**Other questions** on Fairwater capacity and silicon innovation (Maia 200) were addressed with high-level comments about global infrastructure expansion and flexible, advantaged TCO via both internal and partner silicon. Unanswered issues include precise timing or magnitude of future capacity expansion.",
  ] },
  { title: "4. AI Conclusion", paragraphs: [
    "Predominant tone: **Confident.** Management repeatedly expresses \"very good\" feelings about execution and future positioning, with robust explanations for heavy Capex and high RPO durability (e.g., \"super high confidence\" in diversified backlog; \"excited\" about silicon and supply ramp). Confidence appears clear but is underpinned by commitment to manage supply/demand gaps and ongoing Capex optimization rather than relying on a single bet.",
    "**Main business message:** Microsoft is leading in AI/cloud adoption at scale, with diversified demand, and is willing to trade near-term margin for long-term leadership and customer value.",
    "**Watchpoint:** Track supply chain and memory price risks, as well as the pace of capacity ramp and efficiency impacts on margins.",
  ] },
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
        <header className={reportStyles.reportHeader}>
          <div className={reportStyles.company}><div className={reportStyles.logo}><img src="/benefits/company-logos/MSFT.webp" alt="" width={34} height={34} /></div><div><h3>Microsoft <span>MSFT</span></h3><p>2Q/2026 · Earnings Call</p></div></div>
        </header>
        <h4 className={reportStyles.thesisHeading}><FileText size={22} />{english ? "Call Analysis" : "Análise do call"}</h4>
        <div className={reportStyles.text} data-lenis-prevent role="region" tabIndex={0} aria-label={english ? "Read the full Microsoft call analysis" : "Leia a análise completa do call da Microsoft"}>
          <TypingPreview>{analysis.map(section => <div key={section.title}>
            <h5 className={styles.heading}>{section.title}</h5>
            {section.paragraphs.map(paragraph => <p key={paragraph}>{splitBold(paragraph).map((part, index) => part.bold ? <strong key={index}>{part.text}</strong> : part.text)}</p>)}
          </div>)}</TypingPreview>
        </div>
        <div className={reportStyles.reportFooter}>{english ? "Scroll to explore the analysis" : "Role para explorar a análise"} ↓</div>
      </article>
    </div>
  </section>;
}
