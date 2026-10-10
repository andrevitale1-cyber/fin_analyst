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

        language_instruction = "IMPORTANT: Write the analysis text in English, but ALWAYS KEEP the tags 'Seção 1:', 'Seção 2:', 'Nota Seção X: Y/5' and 'Nota Geral: Y/5' EXACTLY in Portuguese so the system can parse them.\n\n" if locale == "en" else ""

        prompt = f"""
{language_instruction}
ATUE COMO UM ANALISTA SÊNIOR DE EQUITY RESEARCH.
Sua missão é realizar uma análise fundamentalista profunda da empresa {ticker.upper()}.
Período solicitado: {periodo or 'identifique no documento'}.

REGRAS CRÍTICAS:
1. USE APENAS OS DADOS FORNECIDOS ABAIXO. Se os dados forem insuficientes, diga 'Dados insuficientes' em vez de inventar números ou empresas.
2. NUNCA USE 'Empresa Fictícia S.A.' ou dados de exemplo.
3. MANTENHA AS ETIQUETAS 'Seção 1:', 'Seção 2:', 'Seção 3:', 'Seção 4:', 'Seção 5:', 'Seção 6:' e 'Seção 7:' EXATAMENTE ASSIM.
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
Avalie a qualidade do trimestre da empresa, não a atratividade da ação nem sua cotação. Compare com períodos equivalentes e considere sazonalidade, mix, rentabilidade, geração de caixa, risco e recorrência:
- 5 (Excelente): desempenho operacional amplamente forte, com crescimento e rentabilidade/caixa sustentáveis e sem deterioração material que altere a tese.
- 4 (Bom): execução positiva e criação de valor, com pressões ou ressalvas pontuais que não dominam o trimestre.
- 3 (Regular): resultado misto; ganhos e fraquezas relevantes se compensam ou a execução permanece sem melhora clara.
- 2 (Ruim): deterioração relevante em indicadores centrais, conversão de caixa, risco de crédito/alavancagem ou execução, sem evidência suficiente de que seja apenas temporária.
- 1 (Muito Ruim): deterioração disseminada, falha operacional grave ou risco material de liquidez/solvência.
A nota final deve refletir o conjunto e não ser automaticamente alta por crescimento de receita. Explique o principal fator que sustenta a nota e o principal limitador.

REGRAS SETORIAIS PARA {sector.upper()}:
{sector_rules}

PADRÃO EDITORIAL E FORMATAÇÃO:
- Use tom profissional, elegante, analítico e jornalístico. Construa uma narrativa fluida e foque em geração de valor.
- Use tabelas Markdown quando houver quebra de receitas por segmento, linhas de crédito ou revisão de guidance. Para segmentos, prefira as colunas segmento, receita, participação na receita, comparação anual e contribuição para o crescimento. Use bullet points para destaques operacionais, despesas e linhas de serviços/seguros quando houver dados.
- Escreva valores por extenso com até duas casas decimais, como "R$ 11,87 bilhões", "aumento de 13,1%" e "expansão de 0,6 p.p.". Não use LaTex.
- Para instituições financeiras, trate de Margem Financeira (NII), ROE, Índice de Eficiência, Custo de Crédito, NPL/inadimplência e Basileia (CET1), se houver dados.
- Para varejo ou indústria, trate de Receita Líquida, EBITDA, Margem Bruta/EBITDA, Dívida Líquida/EBITDA e Vendas Mesmas Lojas (SSS), se houver dados.
- Contextualize aquisições separando crescimento orgânico da consolidação de M&As; não reduza a nota apenas pela existência de M&A.
- Todas as notas são inteiros: 1, 2, 3, 4 ou 5. Não use decimais nas notas.

ESTRUTURA OBRIGATÓRIA (MANTENHA OS NOMES DAS SEÇÕES EM PORTUGUÊS):
[Parágrafo introdutório sem título]
Escreva três a cinco linhas resumindo o trimestre, classificando-o como sólido, fraco ou desafiador e explicando o principal motor do desempenho.

Seção 1: Evolução Operacional e Top Line
Analise Receita Líquida, Carteira de Crédito ou Volume de Vendas. Discuta preço versus volume e desconstrua o crescimento pelo mix de negócios: valor, participação de cada segmento na receita, variação comparável e contribuição para o crescimento total. Inclua tabela Markdown quando os dados permitirem. Não substitua a participação dos segmentos na receita por uma divisão geográfica.
Nota Seção 1: X/5

Seção 2: Rentabilidade e Margens
Analise EBITDA, Margem Financeira, Índice de Eficiência ou Resultado Operacional. Explique alavancagem operacional, diluição ou pressão de custos.
Nota Seção 2: X/5

Seção 3: Estrutura de Capital e Gestão de Risco
Para bancos, analise qualidade do crédito, inadimplência acima de 90 dias, custo do crédito e Basileia. Para empresas não financeiras, analise fluxo de caixa livre, Dívida Líquida/EBITDA, perfil da dívida e despesas financeiras.
Nota Seção 3: X/5

Seção 4: Sumário Executivo do Lucro Líquido
Analise lucro líquido e ROE quando disponível. Identifique efeitos não recorrentes, marcação a mercado ou créditos tributários e conecte o lucro à eficiência descrita anteriormente.
Nota Seção 4: X/5

Seção 5: Conclusão Estratégica e Outlook
Escreva "Conclusão IA:" seguida de um ou dois parágrafos concisos e específicos. Sintetize a nota do trimestre; conecte os principais motores, a conversão em caixa, riscos e sustentabilidade; indique os gatilhos a acompanhar. Não copie as seções anteriores. Diga que superou, atendeu ou frustrou expectativas somente quando o release fornecer uma expectativa explícita. Se houver revisão de guidance, inclua tabela Markdown comparando o anterior e o revisado. Distinga a qualidade operacional do preço da ação e não faça recomendação de compra ou venda sem valuation.

Seção 6: Nota Final
Nota Geral: X/5
Classificação do Trimestre: Excelente, Bom, Regular, Ruim ou Muito Ruim (correspondente à nota de 5, 4, 3, 2 ou 1)

**Seção 7: Dados Estruturados para Gráficos (OBRIGATÓRIO)**
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

DADOS PARA ANÁLISE:
Se houver um documento anexado, use-o como fonte primária. Caso contrário, use o texto abaixo:
{pdf_text[:40000]}
"""
        return prompt
