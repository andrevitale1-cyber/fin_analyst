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

    def build_prompt(self, ticker, pdf_text, locale="pt"):
        sector = self.get_sector(ticker)
        
        # Regras específicas por setor (Melhoradas e Anônimas)
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

REGRAS CRÍTICAS:
1. USE APENAS OS DADOS FORNECIDOS ABAIXO. Se os dados forem insuficientes, diga 'Dados insuficientes' em vez de inventar números ou empresas.
2. NUNCA USE 'Empresa Fictícia S.A.' ou dados de exemplo.
3. MANTENHA AS ETIQUETAS 'Seção 1:', 'Seção 2:', 'Seção 3:', 'Seção 4:', 'Seção 5:', 'Seção 6:' e 'Seção 7:' EXATAMENTE ASSIM.

FILTROS DE QUALIDADE:
- Foco em alocação de capital e geração de valor.
- Analise SBC (Stock Based Compensation) e vantagens competitivas.

REGRAS SETORIAIS PARA {sector.upper()}:
{sector_rules}

ESTRUTURA OBRIGATÓRIA (MANTENHA OS NOMES DAS SEÇÕES EM PORTUGUÊS):
[Introdução Analítica]

Seção 1: Evolução Operacional e Top Line
Nota Seção 1: X/5

Seção 2: Rentabilidade e Eficiência de Margens
Nota Seção 2: X/5

Seção 3: Gestão de Capital e Liquidez
Nota Seção 3: X/5

Seção 4: Performance do Lucro Líquido
Nota Seção 4: X/5

Seção 5: Conclusão Estratégica e Rating Final
(Veredito sobre a qualidade).

Seção 6: Nota Final
Nota Geral: X/5

**Seção 7: Dados Estruturados para Gráficos**
Retorne EXATAMENTE um bloco de código JSON para o frontend:
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

DADOS REAIS DO RELATÓRIO PARA ANÁLISE:
{pdf_text[:120000]}
"""
        return prompt
