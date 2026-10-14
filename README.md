# FinAnalyzer

## Desenvolvimento local

O frontend fica em `frontend/` e o backend em `backend/`. Instale as dependências do frontend com `npm install` dentro de `frontend/` e inicie a interface com `npm run dev`; ela abre em `http://localhost:3000/pt`.

Para testar a API local, crie `backend/.env` a partir de `backend/.env.example`, configure `OPENAI_API_KEY` e instale `backend/requirements.txt` em um ambiente Python. Inicie com `uvicorn main:app --reload --port 8000` dentro de `backend/`. Crie `frontend/.env.local` a partir de `frontend/.env.example` para apontar a interface à API local. Esses arquivos `.env` não devem ser enviados ao GitHub.

## Busca automática

Na área interna, escolha **Busca automática**, informe ticker, ano e trimestre. A API procura um documento público da SEC ou de relações com investidores/B3, confere o período e mostra o link de origem no resultado. Se não encontrar um documento compatível, use **Enviar relatório** para fazer upload manual do PDF. A busca depende da publicação do documento pela empresa e da disponibilidade das fontes. Uma chave OpenAI com créditos de API é necessária para a análise; `TAVILY_API_KEY` é opcional para a busca na web.

Para **Transcrição da call**, informe o ano e trimestre fiscal da empresa. A busca aceita HTML e PDF, prioriza relações com investidores e arquivos públicos de texto, depois Tavily e, somente se nenhum documento válido for encontrado, uma pesquisa web da OpenAI. A empresa, o período principal e a presença de diálogo são conferidos antes da análise. Falhas de acesso/pesquisa são diferenciadas de ausência de documento.

Transcrições verificadas ficam em cache no `REPORT_CACHE_DIR` (por padrão, diretório temporário do servidor). Consultas repetidas evitam nova pesquisa enquanto o cache existir. A análise envia o texto uma única vez, sem anexar novamente o PDF, com limite de 4.000 tokens de saída. O cache pode desaparecer após reinício em hospedagens com armazenamento temporário; arquivos sem texto selecionável e fontes restritas exigem outro documento público ou upload manual de um PDF legível.
