# Equibles: descoberta de releases trimestrais

O backend usa `EQUIBLES_API_KEY`, configurada somente no servidor. A conexão OAuth do plugin no chat não fornece credenciais ao Render.

Fluxo: cache existente → catálogo IR-news do Equibles → coleta RI/SEC/web existente. O catálogo contém links a anúncios da própria companhia; não usamos resumos nem notas produzidas pelo fornecedor como análise. O prompt trimestral, o modelo e as notas permanecem inalterados.

A chamada usa o endpoint documentado `GET https://api.equibles.com/v1/stocks/{ticker}/ir-news`, Bearer no cabeçalho, sem redirecionamentos, resposta limitada a 1 MB e até 50 anúncios recentes. São tentados no máximo dois documentos, com timeout de oito segundos cada. O conteúdo do documento deve confirmar o período e o emissor. Falhas, limites de uso e falta de cobertura voltam à coleta atual.

A consulta recente não garante cobertura de períodos antigos ou de ações da B3. O teste real precisa distinguir disponibilidade da API, presença do anúncio e validação do documento. Nunca substituir um período solicitado pelo resultado mais recente.

A flag temporária `VALIDATE_EQUIBLES_20261020=1` executa uma única verificação de documentos VIVA3/AAPL 2T2026, registrada em `maintenance_tasks`. Não chama modelos nem cria análises ou consome a cota de usuários. Reinícios não repetem a verificação.

Referência: https://equibles.com/docs/api/endpoints/earnings#ir-news
