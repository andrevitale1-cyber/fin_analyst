"use client";

import { Check, CircleAlert, DollarSign, FileText, Percent, TrendingUp, ArrowRight } from "lucide-react";
import { Link } from "@/i18n/routing";
import styles from "./MetaAnalysisSection.module.css";

// Product analysis transcribed from the screenshots supplied by the user.
const thesis = [
  {
    lead: "Meta’s 1Q26 results reinforce its preeminent role in global digital advertising, leveraging record ad impressions (up 19% YoY) and increasing average ad prices (up 12% YoY) for broad-based revenue acceleration.",
    body: "The Family of Apps ecosystem continues to draw billions of daily users, underpinning Meta’s ongoing monetization engine. While Reality Labs remains an earnings drag, the segment’s controlled losses suggest disciplined investment relative to revenue scale. The company’s deepening commitment to AI, evidenced by the Meta Superintelligence Labs milestone, signals a potential new avenue of competitive advantage, but this is not yet a material factor in financial contribution.",
  },
  {
    lead: "Margins and profitability remain best-in-class, with stable operating margin (41%) and strong operating leverage even alongside surging R&D and infrastructure investments.",
    body: "This capacity to scale costs with revenue is a hallmark of Meta’s model, but the accelerating expense base—especially in R&D and SBC—should be closely monitored. Reality Labs’ persistent losses and the company’s elevated spending guidance imply that, while short-term headline margins are robust, sustained investments are needed to maintain both competitive positioning and future growth.",
  },
  {
    lead: "Meta’s capital discipline is evidenced by world-class free cash flow ($12.39 billion), ample liquidity ($81.18 billion in cash and securities), and prudent capital return via dividends.",
    body: "Ongoing expansion in capex and data centers presents both an opportunity and a risk; investment is necessary to support AI and platform scale, but execution and returns must follow. The balance sheet remains exceptionally strong, giving Meta flexibility to weather litigation, regulatory, or market turbulence.",
  },
  {
    lead: "However, the headline net profit is significantly overstated by a technical $8.03 billion tax benefit, with underlying tax rates set to normalize in subsequent quarters.",
    body: "Operational momentum is unquestioned, but the underlying earnings power—while robust—is not as explosive as the reported bottom line. Future quarters may see net income moderate as the tax environment reverts to normal and investment intensity stays high.",
  },
  {
    lead: "Meta’s guidance implies continued revenue growth and expense discipline, but the company faces material legal and regulatory risks, particularly youth-related scrutiny and data privacy battles in core markets.",
    body: "Management flags the potential for “material loss” as litigation unfolds, which, combined with rising capex, will be critical watch points for the resilience of Meta’s lucrative core business and the durability of its emerging AI bets.",
  },
];
const translatedThesis = [
  {
    lead: "Os resultados da Meta em 1Q26 reforçam seu papel de destaque na publicidade digital global, com impressões de anúncios recordes (+19% em relação ao ano anterior) e aumento do preço médio dos anúncios (+12%), sustentando a aceleração da receita.",
    body: "O ecossistema Family of Apps continua atraindo bilhões de usuários diários e sustentando a monetização da Meta. Embora Reality Labs ainda pressione os resultados, as perdas controladas do segmento sugerem disciplina de investimento em relação à escala da receita. O compromisso crescente com IA, evidenciado pelo marco da Meta Superintelligence Labs, sinaliza uma possível nova vantagem competitiva, mas ainda não contribui de forma material para os resultados financeiros.",
  },
  {
    lead: "Margens e rentabilidade seguem entre as melhores do setor, com margem operacional estável de 41% e forte alavancagem operacional, mesmo com o aumento dos investimentos em P&D e infraestrutura.",
    body: "A capacidade de escalar custos junto com a receita caracteriza o modelo da Meta, mas a aceleração das despesas, especialmente em P&D e remuneração em ações, merece acompanhamento. As perdas persistentes de Reality Labs e a previsão de gastos elevados indicam que investimentos contínuos serão necessários para preservar a posição competitiva e o crescimento futuro.",
  },
  {
    lead: "A disciplina de capital da Meta se reflete no fluxo de caixa livre de US$ 12,39 bilhões, na liquidez de US$ 81,18 bilhões em caixa e títulos e no retorno de capital por meio de dividendos.",
    body: "A expansão dos investimentos e dos centros de dados representa oportunidade e risco: o investimento é necessário para sustentar IA e escala, mas execução e retorno precisam acompanhar. O balanço permanece sólido, oferecendo flexibilidade diante de disputas judiciais, mudanças regulatórias e turbulências de mercado.",
  },
  {
    lead: "Entretanto, o lucro líquido divulgado é significativamente elevado por um benefício fiscal de US$ 8,03 bilhões, com expectativa de normalização das alíquotas nos próximos trimestres.",
    body: "O desempenho operacional é forte, mas a capacidade recorrente de gerar lucro não cresce na mesma proporção do resultado divulgado. O lucro líquido poderá moderar nos próximos trimestres conforme a tributação volte ao normal e a intensidade dos investimentos permaneça elevada.",
  },
  {
    lead: "As projeções da Meta indicam continuidade do crescimento da receita e disciplina de despesas, mas a empresa enfrenta riscos jurídicos e regulatórios relevantes, sobretudo envolvendo jovens e privacidade de dados.",
    body: "A administração sinaliza a possibilidade de perdas materiais com o avanço dos processos. Esses riscos, somados ao aumento dos investimentos, serão pontos de atenção para a resiliência do negócio principal e a sustentabilidade das novas apostas em IA.",
  },
];
const conclusion = "Meta’s first quarter of 2026 exemplifies its ability to combine massive scale, strong user monetization, and operational discipline while investing heavily in future growth vectors. The quarter’s main strength is the recurring ad business, which underpins both cash generation and profit, but the notable jump in net income is artificially inflated by a large, one-off tax reversal that should not recur. Strategic risks are present, notably from regulatory exposure and a sharp increase in capital expenditure, but the company’s liquidity, franchise strength, and execution quality continue to position it among the most resilient global platforms. On balance, the quarter deserves a high rating for operational excellence, with points deducted for the reliance on non-recurring tax benefits and ongoing risk of future legal, regulatory, or investment missteps.";
const translatedConclusion = "O primeiro trimestre de 2026 demonstra a capacidade da Meta de combinar escala, monetização dos usuários e disciplina operacional enquanto investe no crescimento futuro. A principal força do trimestre é o negócio recorrente de publicidade, que sustenta a geração de caixa e o lucro. Contudo, o salto do lucro líquido é elevado por uma reversão fiscal pontual que não deve se repetir. Há riscos estratégicos ligados à regulação e ao aumento dos investimentos, mas a liquidez, a força do negócio e a execução posicionam a empresa entre as plataformas globais mais resilientes. O trimestre merece uma avaliação elevada pela excelência operacional, com ressalvas pela dependência de benefícios fiscais não recorrentes e pelos riscos jurídicos, regulatórios e de investimento.";

export default function MetaAnalysisSection({ locale }: { locale: string }) {
  const english = locale === "en";
  const metrics = [
    { label: english ? "Net Revenue" : "Receita líquida", score: 5, icon: DollarSign, color: "#0075b5" },
    { label: english ? "Net Income" : "Lucro líquido", score: 3, icon: Percent, color: "#a020ff" },
    { label: english ? "Net Debt" : "Dívida líquida", score: 4, icon: CircleAlert, color: "#ff001f" },
    { label: english ? "Profitability" : "Rentabilidade", score: 5, icon: TrendingUp, color: "#008c63" },
  ];
  const features = english ? ["Revenue growth", "Profitability", "Debt & liquidity", "Quality of earnings", "Investment thesis", "Strategic risks"] : ["Crescimento da receita", "Rentabilidade", "Dívida e liquidez", "Qualidade do lucro", "Tese de investimento", "Riscos estratégicos"];

  return <section className={styles.section} aria-labelledby="meta-analysis-heading">
    <div className={styles.layout}>
      <article className={styles.report} aria-label={english ? "FinAnalyzer report preview: META, 1Q/2026" : "Prévia do relatório FinAnalyzer: META, 1Q/2026"}>
        <header className={styles.reportHeader}>
          <div className={styles.company}><div className={styles.logo}><img src="/benefits/company-logos/META.webp" alt="" width={34} height={34} /></div><div><h3>Meta <span>META</span></h3><p>1Q/2026 · {english ? "Analysis Report" : "Relatório de análise"}</p></div></div>
          <div className={styles.finalScore}><span>AI SCORE</span><strong>5<small>/5</small></strong><small>{english ? "Based on 4 fundamentals" : "Com base em 4 fundamentos"}</small></div>
        </header>
        <div className={styles.metrics}>{metrics.map(({label, score, icon: Icon, color}) => <div className={styles.metric} key={label}><div className={styles.icon}><Icon size={19} style={{color}} /></div><div><span>{label}</span><strong style={{color: score === 3 ? "#ba7800" : "#00875d"}}>{score}<small>/5</small></strong></div></div>)}</div>
        <h4 className={styles.thesisHeading}><FileText size={22} />{english ? "Investment Thesis" : "Tese de investimento"}</h4>
        <div className={styles.text} tabIndex={0} role="region" aria-label={english ? "Read the full Meta investment thesis" : "Leia a tese de investimento completa da Meta"}>
          {(english ? thesis : translatedThesis).map(({lead, body}) => <p key={lead}><strong>{lead}</strong><br />{body}</p>)}
          <p><strong>{english ? "AI Conclusion" : "Conclusão da IA"}:</strong> {english ? conclusion : translatedConclusion}</p>
        </div>
        <div className={styles.reportFooter}>{english ? "Scroll to explore the analysis" : "Role para explorar a análise"} ↓</div>
      </article>
      <div className={styles.copy}>
        <h2 id="meta-analysis-heading">{english ? "Understand the business " : "Entenda o negócio "}<span>{english ? "behind the numbers" : "por trás dos números"}</span></h2>
        <p>{english ? "Go beyond the score. FinAnalyzer connects revenue, margins, debt and profitability in a clear investment thesis, highlighting the strengths and risks behind each result." : "Vá além da nota. O FinAnalyzer conecta receita, margens, dívida e rentabilidade em uma tese de investimento clara, destacando as forças e os riscos por trás de cada resultado."}</p>
        <span className={styles.eyebrow}>{english ? "INSIDE THE AI ANALYSIS" : "DENTRO DA ANÁLISE DE IA"}</span>
        <ul>{features.map(feature => <li key={feature}><Check size={15} />{feature}</li>)}</ul>
        <Link className={styles.start} href="/dashboard">{english ? "Explore your next analysis" : "Explore sua próxima análise"}<ArrowRight size={17} /></Link>
        <p className={styles.caption}>{english ? "Example: Meta · 1Q/2026 · FinAnalyzer analysis" : "Exemplo: Meta · 1Q/2026 · Análise do FinAnalyzer"}</p>
      </div>
    </div>
  </section>;
}
