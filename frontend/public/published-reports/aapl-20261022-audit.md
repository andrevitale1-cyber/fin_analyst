# Auditoria AAPL — FinAnalyser 9 (Revisor e Editor) · revisão inicial
Data: 22/10/2026 (horário de Brasília, UTC-3). Status: **RASCUNHO, não aprovado.** Há 1 bloqueador aberto.

## Contagem
| Severidade | Qtde |
|---|---|
| Bloqueador | 1 |
| Material | 7 |
| Editorial | 7 |

## Verificações feitas
- Li COMMON_RULES.md, COMMON.md, scope.json, status.md e requests/decisions.md (até "Market View final; Thesis liberada").
- Li as 12 seções (`.md` e `.json`) e o valuation (`valuation.md/json`, `model_inputs`, `model_outputs`). Rodei o `test_model.py` numa cópia em /tmp: 17 testes OK.
- Integridade de IDs: todos os `source_ids` das 12 seções existem em `sources.json`. Todos os `fact_ids` existem em `facts.json` ou `calculations.json`. Não sobrou nenhum ID PROV:/mv_proposed_.
- Números-chave recalculados contra facts/calculations/extracts:
  - Receita: TTM US$ 466,8 bi, FY25 US$ 416,2 bi, 9M +16,2% e Q3 +16,4% (109,417/94,036).
  - Margens: 9M bruta 49,1%, operacional 33,6%, Produtos 39,9%, Serviços 76,3%. Q3 50,1% com ~2 p.p. de reembolso tarifário (8-K Q3 e 10-Q).
  - LPA: TTM 8,724; Q3 2,02 − 0,11 = 1,91 (+21,7% contra +28,7%); CAGR FY20–25 de 17,9%; FY21→FY25 +33,0%, com decomposição log de 59/41.
  - FCF: TTM US$ 136,7 bi; 9M US$ 110,2 bi.
  - Recompras: 9M em três conceitos (62,094 DFC / 61,8 Nota 7 / 62,242 DMPL); FY21–25 somando US$ 438,6 bi; disponível US$ 138,0 bi.
  - Base acionária: capa 14,594 bi e diluída usada 14,653 bi.
  - P/L: 39,42x principal e 39,91x secundário. EV/EBIT 32,4x, FCF yield 2,7% e earnings yield 2,5%.
  - WACC: Ke = 4,96% + 1,069×4,20% = 9,45%; WACC 9,37% (Kd líquido de 4,53%, peso de 1,6%).
  - Cenários: margens FY27 de 28,5/32,0/33,5% batem com o modelo. Valor 116,81/158,96/192,60. Preço condicional 126,77/172,90/209,72 e retornos −63,3/−50,0/−39,5% conferidos. DCF reverso 5,81% / 6,88%. "81% acima do teto" conferido.
  - Obrigações de compra: US$ 56,2 bi (27/09/2025) e US$ 57,0 bi (27/06/2026). As duas estão corretas e são datas diferentes.
  - Câmbio na China (renminbi), "publicidade e nuvem" em Serviços, multa DMA de €500 mi e teto de 10%, Suprema Corte no caso Epic (30/06/2026) e alíquota de 17,6% nos 9M: confirmados nos extracts.
- Coerência de período: FY fiscal de set., TTM e 9M estão rotulados na maior parte do texto. As exceções estão abaixo.
- Varredura de frases duplicadas e cortadas nas 12 seções: nenhuma duplicata. Um fragmento de fórmula no Histórico.
- Não usei previous/report_anterior.html como fonte de números.

## Problemas
### B1 · Bloqueador · Tese e Veredito sem entrega registrada
- Local: status.md ("8 Thesis & Final Verdict: em andamento"); decisions.md não registra a entrega nem o aceite de investment_thesis/final_verdict (arquivos de 22:39).
- Impacto: o relatório não pode passar a "pronto para revisão humana" enquanto a seção que dá a conclusão não estiver formalmente entregue.
- Correção: o Thesis confirma a entrega final e o coordenador registra o aceite em decisions.md e status.md. Responsáveis: Thesis & Final Verdict + coordenador.

### M1 · Material · P/L histórico inconsistente e distorcido
- Local: valuation.md, "NOSSA AVALIAÇÃO" ("24,6x–39,1x… no fim de cada exercício entre FY21 e FY26"); investment_thesis.md ("24,6x a 37,5x entre FY21 e FY25"); market_view.md (as duas formas).
- Evidência: o FY26 é proxy (preço de 25/09/2026 ÷ LPA TTM de jun/26) e não é o LPA do exercício. O teto de 37,5x do FY24 usa LPA de US$ 6,08 já reduzido pelo encargo único do State Aid (o Histórico estima lucro de ~US$ 104,0 bi sem ele).
- Impacto: o "histórico" usado para dizer que a ação está acima do próprio padrão tem limites diferentes conforme a seção, e o teto está inflado por item não recorrente.
- Correção: um único intervalo em todas as seções. Excluir ou rotular o proxy de FY26 e apresentar o FY24 também sem o State Aid (ou com nota). Responsáveis: Valuation (origem), Market View e Thesis.

### M2 · Material · Checagem por pares usa a base acionária que foi retirada
- Local: valuation.md (tabela de pares: US$ 194,72 e 255,57); final_verdict.md, "NÍVEL DE CONVICÇÃO".
- Evidência: model_outputs.peer_check = P/L × lucro TTM ÷ 14,594 bi (ações da capa), o que equivale a LPA de US$ 8,83. A decisão de 22/10 tirou o 8,83 do texto. O DCF usa 14,653 bi.
- Impacto: com o LPA oficial de 8,724, os valores ficam em ~US$ 192,3 e ~US$ 252,4. A direção da conclusão não muda.
- Correção: usar o LPA oficial ou as ações diluídas do DCF, ou rotular a métrica. Responsáveis: Valuation e Thesis (texto).

### M3 · Material · Ponte do DCF com timing inconsistente
- Local: valuation.md, "COMO CALCULAMOS", e own_hypotheses.post_balance_distributions.
- Evidência: o FCFF do 4º tri FY26E (US$ 31,8 bi) entra no equity, mas recompras e dividendos depois de 27/06 são tratados como neutros, e as ações ficam fixas em 17/07/2026.
- Impacto: o caixa distribuído no 4º tri é contado como da firma sem reduzir as ações. Minha estimativa é de cerca de −US$ 1 por ação no base, pequeno, mas é inconsistência de método (dupla contagem parcial).
- Correção: deduzir as distribuições estimadas do 4º tri ou não somar o stub, e documentar. Responsável: Valuation.

### M4 · Material · Dois 39,4x com conceitos diferentes
- Local: market_view.md, sumário ("EPS ajustado de US$ 8,83 no FY26 e US$ 9,58 no FY27 (39,4x e 36,3x)"); valuation.md, tabela de múltiplos.
- Evidência: 348,22/8,83 = 39,44x (consenso FY26, prospectivo), que coincide numericamente com o P/L oficial trailing de 39,42x.
- Impacto: o leitor pode confundir o múltiplo principal com o múltiplo sobre o consenso.
- Correção: rotular sempre como "P/L sobre EPS ajustado consensual FY26 (S&P Global)" e, no sumário, explicitar que é prospectivo. Responsáveis: Market View e Valuation.

### M5 · Material · Causalidade sem evidência e fonte sem atribuição
- Local: market_view.md, "VISÃO DO MERCADO".
- Evidência: a frase "muitos alvos foram fixados antes da valorização de 32,5% em 52 semanas e ainda não foram atualizados" não tem fonte com data dos alvos. O 32,5% vem do StockAnalysis (AAPL.mkt.sa.price_change_52w) e aparece sem atribuição.
- Correção: retirar a causalidade ou marcar como hipótese, e atribuir o 32,5% ao provedor. Responsável: Market View.

### M6 · Material · Afirmações sem fonte e período não fechado
- Local: indicadores_resumo.md.
- Evidência: (a) "o maior programa de recompras do mercado" não tem fonte comparativa; (b) "FY2026 é o melhor ano de crescimento desde FY2021" é dito quando o FY26 não foi reportado e só existem os 9M.
- Correção: (a) retirar ou dar fonte; (b) trocar por "9M FY26: maior crescimento desde FY2021". Responsável: Financial Performance.

### M7 · Material · Período errado
- Local: risks.md, "Ressaca do ciclo de iPhone".
- Evidência: "Crescimento de 22% em FY26". O dado é dos 9M FY26 (+22,4%).
- Correção: "+22,4% nos 9M FY26". Responsável: Outlook & Risks.

### Editoriais
- E1. Claims de cálculo sem calc_id/fórmula: final_verdict ("terminal ~74%"), valuation ("terminal 73,8%"), risks ("1 p.p. ≈ US$ 3,5 bi"). Incluir referência a model_outputs. Responsáveis: Thesis, Valuation e Outlook & Risks.
- E2. investment_thesis.md: "liderados por publicidade e nuvem segundo Riscos" cita uma seção no texto do leitor; a fonte é o 10-Q. "Capex consome cerca de 3,1% da receita" vale só para o FY25 (nos 9M FY26 foi 1,9%). Responsável: Thesis.
- E3. business_model.md: "o ciclo de troca do iPhone dita aproximadamente três quartos da receita" é julgamento e não está marcado como tal. Responsável: Business & Moat.
- E4. outlook.md: o caso Epic aparece só "sob recurso"; falta dizer que a Suprema Corte aceitou revisar o padrão de desacato em 30/06/2026, como está em Vantagem Competitiva. Responsável: Outlook & Risks.
- E5. risks.md: "alíquota sobe de ~17% para 19%+": os 17,6% têm fonte, mas o 19%+ é hipótese e precisa do rótulo. Responsável: Outlook & Risks.
- E6. historico_qualidade_financeira.md: a linha "Fórmula: CFO = …" está sem pontuação final e solta abaixo da tabela. Responsável: Financial Performance.
- E7. status.md está desatualizado em relação aos arquivos. Responsável: coordenador.

## Pendências reais (não são erros dos bots)
- 10-K FY26 não publicado: FY26E e o stub do 4º tri são estimativas. A data de 02/11 continua sem confirmação.
- Não há prompt trimestral (scope.json).
- ROIC só como piso; reembolso tarifário em US$ só aproximado; ASRs de maio/2026 pendentes do 10-K.
- Revisão humana obrigatória antes de qualquer publicação. Nada foi publicado.

## Montagem
- review/report.html: 12 seções; Chart.js 4.4.1 via CDN (jsdelivr); sumário clicável; tempo de leitura de ~83 min (16.673 palavras de texto corrido a 200 palavras/min); popover de fontes por seção (botão, Esc fecha); tabelas recolhíveis (`<details>`); seletor de cenários bear/base/bull (radio, teclado); gráficos com aria-label, legenda textual e tabela equivalente. A faixa "RASCUNHO — NÃO PUBLICAR" fica visível.
- Renderização testada no google-chrome headless: review/screenshot_1366.png, screenshot_390.png, screenshot_1366_cenarios.png, screenshot_390_cenarios.png. Na primeira versão havia overflow horizontal em 390px; corrigi com min-width:0 no grid.
- Gerador: review/build_report.py (lê sections/, valuation/ e data/ sem alterar nada).
