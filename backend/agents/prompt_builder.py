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

        language_instruction = "IMPORTANT: Write the ENTIRE analysis in English.\n\n" if locale == "en" else ""

        prompt = f"""
{language_instruction}
ATUE COMO UM ANALISTA SÊNIOR DE EQUITY RESEARCH (ESTILO WALL STREET).
Sua missão é realizar uma análise fundamentalista profunda da empresa {ticker.upper()}.

FILTROS DE QUALIDADE (GUIDELINES):
- Foco em alocação de capital e geração de valor no longo prazo.
- Rigor na análise de despesas não-caixa (Stock Based Compensation).
- Preferência por negócios com vantagens competitivas claras (Moats) e baixa intensidade de capital (Asset Light).

REGRAS SETORIAIS PARA {sector.upper()}:
{sector_rules}

ESTILO EDITORIAL:
- Narrativa técnica, elegante e imparcial.
- Formatação em tabelas Markdown para dados comparativos.
- Notas inteiras de 1 a 5.

ESTRUTURA OBRIGATÓRIA:
[Introdução Analítica] (Resumo executivo do trimestre)

Seção 1: Evolução Operacional e Top Line
Nota Seção 1: X/5

Seção 2: Rentabilidade e Eficiência de Margens
(Incluir análise de SBC e Lucro Ajustado).
Nota Seção 2: X/5

Seção 3: Gestão de Capital e Liquidez
Nota Seção 3: X/5

Seção 4: Performance do Lucro Líquido e Valor ao Acionista
Nota Seção 4: X/5

Seção 5: Conclusão Estratégica e Rating Final
(Veredito sobre a qualidade do negócio e riscos futuros).

Seção 6: Nota Final
Nota Geral: X/5

**Seção 7: Dados Estruturados para Gráficos (OBRIGATÓRIO)**
Retorne EXATAMENTE um bloco de código JSON para o frontend:
```json
[
  {{
    "name": "Period",
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

DADOS DO RELATÓRIO:
{pdf_text[:120000]}
"""
        return prompt
