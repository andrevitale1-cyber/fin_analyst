# Roadmap: Milestone 1 - Smart Autonomous Discovery

## Overview

Este milestone foca em tornar a busca de documentos de RI à prova de falhas, utilizando APIs de busca externa e IA para navegar pela web de forma autônoma.

## Phases

- [ ] **Phase 1: Search Infrastructure** - Integração com APIs de busca.
- [ ] **Phase 2: Intelligent Selection** - Lógica de escolha de links via LLM.
- [ ] **Phase 3: Integration & UX** - Atualização dos endpoints e tratamento de erros.

## Phase Details

### Phase 1: Search Infrastructure
**Goal**: Permitir que o backend realize buscas programáticas.
**Requirements**: SMART-01, SMART-02
**Success Criteria**:
  1. Função `search_results(query)` retorna lista de links e snippets.
  2. Suporte a Tavily ou Google Custom Search API.
**Plans**: 1 plan

### Phase 2: Intelligent Selection
**Goal**: Escolher o PDF certo entre os resultados de busca.
**Requirements**: SMART-03, SMART-04
**Success Criteria**:
  1. Gemini recebe lista de links e retorna o URL correto.
  2. Sistema identifica se o link é um release ou outro documento irrelevante.
**Plans**: 1 plan

### Phase 3: Integration & UX
**Goal**: Unificar a busca inteligente no fluxo principal.
**Requirements**: SMART-05
**Success Criteria**:
  1. `/api/analyze-auto` encontra resultados de empresas fora do `ir_map.json`.
  2. Logs claros sobre o processo de descoberta autônoma.
**Plans**: 1 plan

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Search Infrastructure | 0/1 | Not started | - |
| 2. Intelligent Selection | 0/1 | Not started | - |
| 3. Integration & UX | 0/1 | Not started | - |

---
*Roadmap defined: 2026-05-11*
