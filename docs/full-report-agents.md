# Full reports: agentes no backend

Os agentes são módulos Python executados pelo serviço atual do Render. Não exigem servidores separados, cadastro de agentes na OpenAI ou outro framework. O frontend continua renderizando HTML React; o modelo nunca fornece HTML executável.

## Fluxo

1. `company_research.py` coleta pesquisa citada, dados financeiros estruturados e tenta localizar o transcript público mais recente. `agents/company_documents.py` busca até um filing e um transcript em hosts verificados. Redirecionamentos são recusados, o download tem limite de tamanho e o conteúdo é tratado como dados.
2. `agents/report_facts.py` extrai um dossiê compacto. Tabelas seguidas por uma linha de fonte são preservadas junto da atribuição. A extração distribui a cobertura entre os temas, sem deixar um transcript longo substituir as outras fontes. Cada fato exige referência e trecho literal encontrado no documento; valores numéricos devem existir no trecho e preservar unidade e período. Dados anuais oficiais são preservados separadamente, sem depender de sua repetição pelo modelo.
3. `agents/report_writer.py` recebe os fatos e instruções específicas para nove seções. Uma requisição estruturada escreve todas as seções, evitando reenviar o contexto nove vezes.
4. `agents/report_valuation.py` trabalha em paralelo com a redação. O modelo identifica EPS comprovado e premissas explícitas bear/base/bull; Python calcula os valores futuros e presentes e escreve a apresentação numérica desses cenários, evitando contradições entre narrativa e tabela. Moeda igual não comprova equivalência entre ADR e ação ordinária, portanto não há upside automático para outra base por ação.
5. `agents/report_verifier.py` aplica checagens de cobertura, períodos, duplicações, participações e aritmética, além de uma revisão independente por LLM dos fatos/trechos e do relatório. Uma rejeição impede salvar o relatório e libera a reserva de cota. A revisão reduz erros; não é garantia absoluta de ausência de alucinações.
6. `ReportFinancialChart.tsx` usa Chart.js nos gráficos financeiros, com tabela acessível equivalente e suporte a movimento reduzido. `ReportSources.tsx` apresenta as fontes em popovers acionados pelos botões ao final das seções.

## Cache, custo e privacidade

- A extração de fatos usa `OPENAI_ANALYSIS_MODEL` (Luna por padrão); redação, valuation e auditoria seguem `OPENAI_FULL_REPORT_MODEL` (Sol por padrão). O cache do dossiê identifica o modelo efetivamente usado.
- Uma geração nova usa quatro chamadas estruturadas: extração, redação, valuation e auditoria, além da coleta limitada. Redação e valuation rodam em paralelo. Não há pesquisa independente por seção. Uma reprovação pode gerar uma única correção apenas dos campos apontados pelo auditor, preservando o restante e recalculando os valores derivados, dentro do prazo total; uma nova reprovação impede a gravação.
- Pesquisa, dossiê e relatório têm cache compartilhado de dados públicos. O dossiê usa a versão da extração, modelo e conteúdo das fontes na chave; pode ser reaproveitado entre idiomas e após falhas posteriores.
- O orçamento da rota é de 315 segundos. Cada chamada tem seu próprio limite; o fluxo não inicia novas etapas quando o orçamento acaba.
- Os relatórios novos permanecem privados. Reaproveitar processamento não expõe a biblioteca privada de outro usuário. Ler um relatório salvo não regenera o conteúdo nem consome cota.
- Relatórios existentes permanecem acessíveis; uma atualização exige ação explícita do usuário.
- A versão nova é `company-v7`, com metadados internos de etapas e verificação. Logs não incluem o conteúdo dos documentos, tokens de sessão ou mensagens sensíveis do provedor.

## Metodologia compartilhada com a análise trimestral

`PromptBuilder.company_field_rules()` reutiliza os blocos ativos de qualidade, instruções de receita/margens/capital/lucro, regras setoriais, padrão editorial e régua qualitativa de notas da análise trimestral. Extração, redação e auditoria dos full reports usam essa mesma base. A adaptação preserva a análise da companhia ao longo de vários períodos, os campos JSON, os fatores atuais da nota da companhia e o agente próprio de valuation; não importa a estrutura numerada nem a fórmula de nota geral do trimestre.

Mudanças de geração podem invalidar o relatório e o dossiê preservando a pesquisa. Correções na coleta usam uma versão própria da pesquisa para não reaproveitar evidências incompletas. Abrir um relatório salvo continua apenas lendo a versão existente.

## Validação

Os testes cobrem os quatro contratos reais, extração sem referência/número válido, rejeição da auditoria antes da gravação, cancelamento da reserva, reuso do dossiê, períodos duplicados, dados futuros, soma de segmentos, aritmética e restrições da coleta de documentos. A interface é verificada em 390 e 1440 pixels com um relatório público real, gráficos e popovers.

Referências técnicas: [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [integração Chart.js](https://www.chartjs.org/docs/latest/getting-started/integration.html) e [acessibilidade Chart.js](https://www.chartjs.org/docs/latest/general/accessibility.html).
