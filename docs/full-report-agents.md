# Full reports: agentes no backend

Os agentes são módulos Python executados pelo serviço atual do Render. Não exigem servidores separados, cadastro de agentes na OpenAI ou outro framework. O frontend continua renderizando HTML React; o modelo nunca fornece HTML executável.

## Fluxo

1. `company_research.py` coleta pesquisa citada, dados financeiros estruturados e tenta localizar o transcript público mais recente. `agents/company_documents.py` busca até um filing e um transcript em hosts verificados. Redirecionamentos são recusados, o download tem limite de tamanho e o conteúdo é tratado como dados.
2. `agents/report_facts.py` extrai um dossiê compacto. Cada fato exige referência e trecho literal encontrado no documento; valores numéricos devem existir no trecho e preservar unidade e período. Dados anuais oficiais são preservados separadamente, sem depender de sua repetição pelo modelo.
3. `agents/report_writer.py` recebe os fatos e instruções específicas para nove seções. Uma requisição estruturada escreve todas as seções, evitando reenviar o contexto nove vezes.
4. `agents/report_valuation.py` trabalha em paralelo com a redação. O modelo identifica EPS comprovado e premissas explícitas bear/base/bull; Python calcula os valores futuros e presentes. Moeda igual não comprova equivalência entre ADR e ação ordinária, portanto não há upside automático para outra base por ação.
5. `agents/report_verifier.py` aplica checagens de cobertura, períodos, duplicações, participações e aritmética, além de uma revisão independente por LLM dos fatos/trechos e do relatório. Uma rejeição impede salvar o relatório e libera a reserva de cota. A revisão reduz erros; não é garantia absoluta de ausência de alucinações.
6. `ReportFinancialChart.tsx` usa Chart.js nos gráficos financeiros, com tabela acessível equivalente e suporte a movimento reduzido. `ReportSources.tsx` apresenta as fontes em popovers acionados pelos botões ao final das seções.

## Cache, custo e privacidade

- O modelo segue `OPENAI_FULL_REPORT_MODEL`, preservando a configuração dinâmica existente.
- Uma geração nova usa quatro chamadas estruturadas: extração, redação, valuation e auditoria, além da coleta limitada. Redação e valuation rodam em paralelo. Não há pesquisa independente por seção nem repetição automática de gerações rejeitadas.
- Pesquisa, dossiê e relatório têm cache compartilhado de dados públicos. O dossiê usa a versão da extração, modelo e conteúdo das fontes na chave; pode ser reaproveitado entre idiomas e após falhas posteriores.
- O orçamento da rota é de 315 segundos. Cada chamada tem seu próprio limite; o fluxo não inicia novas etapas quando o orçamento acaba.
- Os relatórios novos permanecem privados. Reaproveitar processamento não expõe a biblioteca privada de outro usuário. Ler um relatório salvo não regenera o conteúdo nem consome cota.
- Relatórios existentes permanecem acessíveis; uma atualização exige ação explícita do usuário.
- A versão nova é `company-v5`, com metadados internos de etapas e verificação. Logs não incluem o conteúdo dos documentos, tokens de sessão ou mensagens sensíveis do provedor.

## Validação

Os testes cobrem os quatro contratos reais, extração sem referência/número válido, rejeição da auditoria antes da gravação, cancelamento da reserva, reuso do dossiê, períodos duplicados, dados futuros, soma de segmentos, aritmética e restrições da coleta de documentos. A interface é verificada em 390 e 1440 pixels com um relatório público real, gráficos e popovers.

Referências técnicas: [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [integração Chart.js](https://www.chartjs.org/docs/latest/getting-started/integration.html) e [acessibilidade Chart.js](https://www.chartjs.org/docs/latest/general/accessibility.html).
