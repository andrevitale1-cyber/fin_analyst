# Premium detailed quarterly analysis

The quarterly result screen offers an additional saved analysis, without changing its original thesis or scores. Both routes under `/api/detailed-analysis/{analysis_id}` require verified Premium authentication and ownership of the original quarterly analysis. Calls are excluded.

POST with `{ "locale": "pt" | "en" }` reserves one shared monthly `analysis` allowance and queues a durable job. GET retrieves status/content without charging. Concurrent submissions reuse the same owner/source/locale/agent job. Successful content and quota completion commit together; failures release the reservation. Jobs interrupted for ten minutes fail without automatically replaying a paid agent turn. Reopening a completed result costs nothing, even when the monthly allowance is exhausted.

The worker invokes the saved **FinAnalyser — Analista detalhado**, default ID `agent_7685ffaa065e40e9af807b73f00b1fe9a3d76fd716a847ee84`. `OPENAI_DETAILED_AGENT_ID` optionally changes this nonsecret ID. Its saved model, tools and instructions are inherited unchanged. It receives the owner's stored original source document, company, fiscal period and requested language. Older analyses without a stored source must be reanalyzed first; the original AI thesis is never substituted for factual evidence.

The worker checks successful turn completion and a minimum answer length. Provider session/turn IDs are retained for diagnosis; hosted sessions are deleted after use. Generation failures log only safe identifiers and exception types. No private document/content is placed in a public cache. Detailed output is rendered as escaped React text with limited Markdown formatting, never raw HTML.

`DETAILED_ANALYSIS_WORKER=0` disables the in-process background worker for tests. Production starts it through the existing FastAPI lifespan; no additional Render service is required. The job table is created by the existing startup migration. The API key remains server-side.
