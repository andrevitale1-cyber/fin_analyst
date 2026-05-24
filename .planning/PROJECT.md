# FinAnalyst

## What This Is

Um analisador financeiro inteligente que processa relatórios de resultados (PDFs) e transcrições de teleconferências utilizando IA (Google Gemini). O sistema automatiza a extração de dados quantitativos e qualitativos para fornecer uma visão crítica e rápida sobre o desempenho das empresas.

## Core Value

Democratizar a análise fundamentalista profunda, automatizando a busca e o processamento de dados que antes exigiam horas de leitura manual.

## Requirements

### Validated

- [x] Extração de texto de PDFs financeiros.
- [x] Integração com Google Gemini 1.5 Flash para análise.
- [x] Dashboards de histórico e métricas (Receita, Lucro, Dívida, rentabilidade).
- [x] Autenticação compatível com Clerk.
- [x] Sistema de Trial e Stripe.

### Active

- [ ] **Busca Autônoma Inteligente**: Localizar releases e transcrições via APIs de busca, sem depender de mapeamento manual.
- [ ] **Seleção de Link via LLM**: Usar a IA para identificar o PDF correto entre vários resultados de busca.
- [ ] **Fallback Robusto**: Sistema que tenta múltiplas fontes (Google, Tavily, RI Direto) até encontrar o documento.

### Out of Scope

- [ ] Análise técnica (gráficos de preço/candle).
- [ ] Execução de ordens de compra/venda.

## Context

- O projeto utiliza uma stack Python (FastAPI) no backend e React/Next.js no frontend.
- A dependência principal para inteligência é a API do Google Gemini.
- A coleta de dados é o maior desafio devido à variedade de formatos dos portais de RI.

## Constraints

- **Limites de RAM**: O processamento de PDFs deve ser otimizado para rodar em ambientes com restrição de memória (ex: instâncias gratuitas).
- **Latência**: A análise de IA pode demorar; o sistema deve suportar streaming ou timeouts longos.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Google Gemini 1.5 Flash | Janela de contexto grande e custo-benefício para leitura de documentos. | Active |
| PostgreSQL | Persistência robusta de histórico e usuários. | Active |
| Tavily/Search API | Para resolver a fragilidade de scrapers baseados em URL fixa. | Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

---
*Last updated: 2026-05-11*
