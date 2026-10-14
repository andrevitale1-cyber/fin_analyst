import json
import os

class PromptBuilder:
    def __init__(self):
        # Ajustando caminhos para a estrutura do backend
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sector_map_path = os.path.join(base_dir, "data", "sector_map.json")
        self.patterns_path = os.path.join(base_dir, "data", "patterns.json")
        self.sectors = self._load_json(self.sector_map_path)
        self.patterns = self._load_json(self.patterns_path)

    def _load_json(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_sector(self, ticker):
        for sector, tickers in self.sectors.items():
            if ticker.upper() in tickers:
                return sector
        return "geral"

    def build_call_prompt(self, empresa, periodo, locale="pt"):
        if locale == "en":
            return f"""Analyze {empresa}'s {periodo} earnings call as a senior company analyst. Write in English and use only the supplied transcript. Keep the analysis to about 300–450 words, excluding the final timestamp list, and use less when the source is limited. Avoid repetition. Never invent numbers or past-call comparisons. Clearly distinguish reported facts from AI interpretation. Attribute relevant statements to speakers and use short quotes only when useful. Assess tone from management's words and answers only, never from voice, emotion, or body language. An unanswered question means the transcript lacks an answer; do not claim concealment. Compare guidance with prior guidance only when the transcript supports it, and call it raised, maintained, or lowered only with a sourced comparison. Use Markdown **bold** for every section title and selectively for material figures, percentages, guidance, tone labels, and brief key phrases; do not bold whole paragraphs.

Use exactly these five sections, in this order:
**1. What explains the results** — up to three concise bullets. State the key driver, why it matters, and a bounded AI reading. Cover only material revenue, profit, margin, cash, and segment changes.
**2. Guidance, projections, clues, conditions, and uncertainties** — distinguish formal guidance and its assumptions from qualitative clues. Include only material forward demand, orders, capacity, capex, and competition when discussed.
**3. Q&A** — up to two material questions and answers or unresolved issues. Explain what information is missing when management does not answer.
**4. AI Conclusion** — about 60–90 words; begin with “Predominant tone:” and choose optimistic, confident, cautious, defensive, mixed, or inconclusive. Give up to two brief textual examples, describe whether confidence is clear or conditional, and note a prepared-remarks/Q&A difference only if material. End with the main business message and one watchpoint.
**5. Key moments** — only after the conclusion, list up to eight chronological timestamps as “[mm:ss] — Theme: short description; speaker”. Use only timestamps shown in the transcript or verified synchronization. Never estimate from text position or confuse clock time with elapsed recording time. If none are available, write exactly: “The provided transcript contains no timestamps; precise timing could not be identified.”"""
        return f"""Analise a earnings call de {empresa} referente a {periodo} como analista sênior da empresa. Escreva em português e use apenas a transcrição fornecida. Limite a análise a cerca de 300–450 palavras, sem contar a lista final de timestamps; use menos quando a fonte for limitada. Evite repetições. Nunca invente números nem comparações com calls anteriores. Separe claramente fatos reportados de interpretação da IA. Identifique falas relevantes pelo nome do interlocutor e use citações curtas apenas quando forem úteis. Avalie o tom somente pelas palavras e respostas da administração, nunca pela voz, emoção ou linguagem corporal. Uma pergunta sem resposta indica que a transcrição não traz a resposta; não alegue ocultação. Compare o guidance com o anterior somente quando houver suporte na transcrição, e classifique-o como elevado, mantido ou reduzido apenas com comparação citada. Use Markdown **negrito** em todos os títulos de seção e, com moderação, em números, percentuais, guidance, rótulos de tom e frases-chave curtas; não coloque parágrafos inteiros em negrito.

Use exatamente estas cinco seções, nesta ordem:
**1. O que explica os resultados** — até três bullets concisos. Indique o principal fator, por que importa e uma leitura da IA com limites claros. Cubra apenas mudanças materiais em receita, lucro, margem, caixa e segmentos.
**2. Guidance, projeções, sinais, condições e incertezas** — diferencie guidance formal e suas premissas de sinais qualitativos. Inclua apenas informações materiais sobre demanda futura, pedidos, capacidade, capex e concorrência.
**3. Perguntas e respostas** — até duas perguntas e respostas materiais ou questões não resolvidas. Explique qual informação falta quando a administração não responder.
**4. Conclusão da IA** — cerca de 60–90 palavras; comece com “Tom predominante:” e escolha otimista, confiante, cauteloso, defensivo, misto ou inconclusivo. Apresente até duas evidências textuais breves e diga se a confiança da administração é clara ou condicional. Compare falas preparadas e Q&A somente se houver diferença material. Termine com a principal mensagem sobre o negócio e um ponto a acompanhar.
**5. Momentos principais** — somente após a conclusão, liste até oito timestamps em ordem cronológica no formato “[mm:ss] — Tema: descrição curta; interlocutor”. Use apenas timestamps presentes na transcrição ou em sincronização verificada. Nunca estime pela posição do texto nem confunda horário do dia com tempo decorrido da gravação. Se não houver nenhum, escreva exatamente: “A transcrição fornecida não contém timestamps; não foi possível identificar a minutagem com precisão.”"""

    def build_prompt(self, ticker, pdf_text, locale="pt", periodo=None):
        sector = self.get_sector(ticker)
        
        # Regras complementares por setor.
        sector_rules = ""
        if sector == "tecnologia_telecom":
            sector_rules = "- OBRIGATÓRIO: Análise detalhada da Rule of 40 (Crescimento + Margem Operacional).\n- Avaliação de métricas de recorrência e retenção (Churn)."
        elif sector == "industrial_logistica":
            sector_rules = "- OBRIGATÓRIO: Avaliação de Backlog e eficiência do Ciclo Financeiro.\n- Análise da conversão de EBITDA em Fluxo de Caixa Livre."
        elif sector == "financeiro":
            sector_rules = "- OBRIGATÓRIO: Análise de NPL (Inadimplência), Índice de Basileia e Eficiência Bancária."
        elif sector == "utilidades":
            sector_rules = "- OBRIGATÓRIO: Avaliação da relação Dívida Líquida/EBITDA e previsibilidade regulatória."

        english = locale == "en"
        language_instruction = (
            "OUTPUT LANGUAGE: English. Write every part of the analysis in clear, idiomatic English, including the introduction, section headings, score labels, classification, conclusion, and all prose. Keep the machine-readable labels exactly as specified in the English output template below. Do not mix Portuguese into the analysis.\n\n"
            if english else ""
        )
        section_labels = [
            "Section 1: Operating Performance and Top Line",
            "Section 2: Profitability and Margins",
            "Section 3: Capital Structure and Risk Management",
            "Section 4: Net Income Summary",
            "Section 5: Strategic Conclusion and Outlook",
            "Section 6: Final Rating",
        ] if english else [
            "Seção 1: Evolução Operacional e Top Line",
            "Seção 2: Rentabilidade e Margens",
            "Seção 3: Estrutura de Capital e Gestão de Risco",
            "Seção 4: Sumário Executivo do Lucro Líquido",
            "Seção 5: Conclusão Estratégica e Outlook",
            "Seção 6: Nota Final",
        ]
        score_labels = [f"Section Score {i}: X/5" for i in range(1, 5)] if english else [f"Nota Seção {i}: X/5" for i in range(1, 5)]
        overall_label = "Overall Score: X/5" if english else "Nota Geral: X/5"
        classification_label = "Quarter Classification: Excellent, Good, Fair, Poor, or Very Poor" if english else "Classificação do Trimestre: Excelente, Bom, Regular, Ruim ou Muito Ruim"
        section_rule = "Use the exact section and score labels shown in the required structure below." if english else "MANTENHA AS ETIQUETAS 'Seção 1:', 'Seção 2:', 'Seção 3:', 'Seção 4:', 'Seção 5:', 'Seção 6:' e 'Seção 7:' EXATAMENTE ASSIM."
        chart_heading = "Section 7: Structured Data for Charts (MANDATORY)" if english else "Seção 7: Dados Estruturados para Gráficos (OBRIGATÓRIO)"
        data_heading = "DATA FOR ANALYSIS:" if english else "DADOS PARA ANÁLISE:"
        number_style = ('Use the source currency and units as reported, with up to two decimal places (e.g., "$11.87 billion", "a 13.1% increase", "a 0.6 percentage-point expansion"). Do not convert currencies.'
                        if english else 'Escreva valores por extenso com até duas casas decimais, como "R$ 11,87 bilhões", "aumento de 13,1%" e "expansão de 0,6 p.p.". Não use LaTeX.')

        prompt = f"""
{language_instruction}
ATUE COMO UM ANALISTA SÊNIOR DE EQUITY RESEARCH.
Sua missão é realizar uma análise fundamentalista profunda da empresa {ticker.upper()}.
Período solicitado: {periodo or 'identifique no documento'}.

REGRAS CRÍTICAS:
1. USE APENAS OS DADOS FORNECIDOS ABAIXO. Se os dados forem insuficientes, diga 'Dados insuficientes' em vez de inventar números ou empresas.
2. NUNCA USE 'Empresa Fictícia S.A.' ou dados de exemplo.
3. {section_rule} Always return the structured chart data in the required JSON code block.
4. Confirme o período do documento antes de analisar. Se divergir do período solicitado, destaque a divergência; não misture trimestres nem apresente dados de outro período como se fossem do solicitado.
5. Diferencie fatos divulgados, cálculos derivados e interpretação. Para cada número relevante, informe período, unidade e, quando identificável, página ou tabela de origem. Nunca invente uma referência.

FILTROS DE QUALIDADE:
- Foco em alocação de capital e geração de valor.
- Analise SBC (Stock Based Compensation) e vantagens competitivas quando houver evidência no documento.
- Em cada seção 1 a 4, desenvolva a análise em parágrafos: dado atual e comparação com período equivalente do ano anterior ou trimestre anterior quando disponíveis; principais causas da mudança; consequência para qualidade do resultado e risco. Calcule variações apenas com bases comparáveis e mostre a conta ou os valores usados.
- Abra cada bloco analítico com uma frase de destaque em negrito que traga a métrica, o valor do período e a comparação mais útil. Em seguida, explique os fatores que moveram o resultado, a qualidade/recorrência desse movimento e sua implicação. Não repita o mesmo número sem acrescentar interpretação.
- Vá além de adjetivos como 'forte' e 'sólido': explique o que melhorou, o que piorou e se o movimento parece recorrente ou pontual. Considere segmentos, preço/volume, custos, margens, caixa, capital de giro e endividamento apenas quando o documento trouxer dados.
- Se faltar comparativo, fluxo de caixa, guidance ou outra métrica necessária, diga explicitamente o que não é possível concluir. Não transforme ausência de dado em nota máxima.
- Priorize a composição e a contribuição dos segmentos de negócio para a receita e para seu crescimento. Não destaque concentração geográfica por padrão; mencione geografia apenas quando houver exposição comprovada e material a risco regulatório, comercial ou operacional.
- Não trate aquisições, capex estratégico, recompra ou dividendos como positivos/negativos automaticamente. Avalie preço, financiamento, efeitos recorrentes, diluição, obrigações contingentes, retorno esperado e execução apenas com evidências do release. Separe crescimento orgânico de crescimento adquirido.

CRITÉRIOS DAS NOTAS:
Avalie a qualidade e a resiliência de longo prazo do negócio, não a atratividade da ação nem sua cotação. Use sempre a mesma régua entre novas análises da mesma empresa. Para a nota geral, atribua internamente notas de 1 a 5 a quatro dimensões e calcule: 40% capacidade estrutural de crescimento e durabilidade competitiva (tendência de demanda, share, backlog, contratos, parcerias e guidance com evidência), 25% execução operacional realizada no trimestre e no ciclo recente, 20% rentabilidade e conversão em caixa (considerando investimentos de crescimento e itens não recorrentes), e 15% balanço, diluição e riscos de execução/concentração. Arredonde a média ponderada para o inteiro mais próximo e explique os fatores que a puxam para cima ou para baixo; não conte o mesmo fato duas vezes. Leading indicators divulgados pela empresa podem sustentar nota mais alta antes de aparecerem na DRE, desde que sejam concretos, quantificados e plausíveis; identifique-os como prospectivos e não os contabilize como receita ou lucro já realizados. Um lucro líquido pressionado por aquisições, SBC ou custos extraordinários não deve, isoladamente, sobrepor uma trajetória operacional de longo prazo robusta, mas seus efeitos de caixa, diluição, contingências e execução devem reduzir a nota na proporção do risco. Não premie anúncios vagos, pipeline não contratado ou guidance sem base verificável. Compare períodos e considere sazonalidade:
- 5 (Excelente): desempenho operacional amplamente forte, com crescimento e rentabilidade/caixa sustentáveis e sem deterioração material que altere a tese.
- 4 (Bom): execução positiva e criação de valor, com pressões ou ressalvas pontuais que não dominam o trimestre.
- 3 (Regular): resultado misto; ganhos e fraquezas relevantes se compensam ou a execução permanece sem melhora clara.
- 2 (Ruim): deterioração relevante em indicadores centrais, conversão de caixa, risco de crédito/alavancagem ou execução, sem evidência suficiente de que seja apenas temporária.
- 1 (Muito Ruim): deterioração disseminada, falha operacional grave ou risco material de liquidez/solvência.
A nota final deve refletir o conjunto ponderado, não ser automaticamente alta por crescimento de receita nem cair apenas por um trimestre fraco de lucro contábil. Explique em termos concretos o principal fator de longo prazo que sustenta a nota e o principal limitador. Mantenha a mesma nota quando os fatos e o horizonte analisado forem essencialmente os mesmos; não varie a nota por diferenças de redação.

REGRAS SETORIAIS PARA {sector.upper()}:
{sector_rules}

PADRÃO EDITORIAL E FORMATAÇÃO:
- Use tom profissional, elegante, analítico e jornalístico. Construa uma narrativa fluida e foque em geração de valor.
- Use tabelas Markdown quando houver quebra de receitas por segmento, linhas de crédito ou revisão de guidance. Para segmentos, prefira as colunas segmento, receita, participação na receita, comparação anual e contribuição para o crescimento. Use bullet points para destaques operacionais, despesas e linhas de serviços/seguros quando houver dados.
- {number_style}
- Para instituições financeiras, trate de Margem Financeira (NII), ROE, Índice de Eficiência, Custo de Crédito, NPL/inadimplência e Basileia (CET1), se houver dados.
- Para varejo ou indústria, trate de Receita Líquida, EBITDA, Margem Bruta/EBITDA, Dívida Líquida/EBITDA e Vendas Mesmas Lojas (SSS), se houver dados.
- Contextualize aquisições separando crescimento orgânico da consolidação de M&As; não reduza a nota apenas pela existência de M&A.
- Todas as notas são inteiros: 1, 2, 3, 4 ou 5. Não use decimais nas notas.

ESTRUTURA OBRIGATÓRIA (USE OS NOMES DAS SEÇÕES ABAIXO):
[Parágrafo introdutório sem título]
Escreva três a cinco linhas resumindo o trimestre, classificando-o como sólido, fraco ou desafiador e explicando o principal motor do desempenho.

{section_labels[0]}
Analise Receita Líquida, Carteira de Crédito ou Volume de Vendas. Discuta preço versus volume e desconstrua o crescimento pelo mix de negócios: valor, participação de cada segmento na receita, variação comparável e contribuição para o crescimento total. Inclua tabela Markdown quando os dados permitirem. Não substitua a participação dos segmentos na receita por uma divisão geográfica.
{score_labels[0]}

{section_labels[1]}
Analise EBITDA, Margem Financeira, Índice de Eficiência ou Resultado Operacional. Explique alavancagem operacional, diluição ou pressão de custos.
{score_labels[1]}

{section_labels[2]}
Para bancos, analise qualidade do crédito, inadimplência acima de 90 dias, custo do crédito e Basileia. Para empresas não financeiras, analise fluxo de caixa livre, Dívida Líquida/EBITDA, perfil da dívida e despesas financeiras.
{score_labels[2]}

{section_labels[3]}
Analise lucro líquido e ROE quando disponível. Identifique efeitos não recorrentes, marcação a mercado ou créditos tributários e conecte o lucro à eficiência descrita anteriormente.
{score_labels[3]}

{section_labels[4]}
Escreva uma conclusão editorial no padrão de uma nota de resultados fundamentalista: 4 a 6 parágrafos curtos, analíticos e fluidos, sem repetir mecanicamente as seções anteriores. Cada parágrafo deve começar com uma frase de destaque em negrito, específica e apoiada em um dado/indicador do release, seguida da interpretação e implicação. Cubra os principais motores de longo prazo, qualidade do crescimento e participação dos segmentos, margem/lucro versus investimentos de crescimento, caixa e balanço, riscos/contrapontos e o que monitorar. Encerre com um parágrafo iniciado por "Conclusão IA:" / "AI Conclusion:" que dê o veredito equilibrado e explique a nota. Não invente expectativas; só diga que superou ou frustrou expectativas quando o release apresentar uma referência explícita. Quando mencionar guidance, backlog, contratos ou parcerias, separe claramente evidência prospectiva de receita/lucro já reconhecidos. Sem recomendação de compra/venda ou opinião de valuation.

{section_labels[5]}
{overall_label}
{classification_label} (corresponding to the final score)

**{chart_heading}**
Retorne um ÚNICO bloco JSON no final, com a lista abaixo, sem HTML ou Chart.js.
Extraia os últimos quatro trimestres disponíveis, ou o máximo que houver. Inclua apenas períodos presentes no documento; NUNCA invente trimestres.
segmentos deve conter objetos de segmentos de negócio com nome e valor de receita em unidade consistente; despesas_var, nome e var_pct. Use a mesma unidade monetária em todos os trimestres, quando possível. Não use países/regiões como segmentos. composicao_receita, se preenchida, deve repetir apenas a composição por negócios.
Se não houver série histórica, retorne [].
```json
[
  {{
    "name": "3T25",
    "receita": 0,
    "lucro": 0,
    "divida": 0,
    "ebitda": 0,
    "margemBruta": 0,
    "margemLiquida": 0,
    "segmentos": [],
    "composicao_receita": {{}},
    "despesas_var": []
  }}
]
```

{data_heading}
Se houver um documento anexado, use-o como fonte primária. Caso contrário, use o texto abaixo:
{pdf_text[:40000]}
"""
        return prompt
