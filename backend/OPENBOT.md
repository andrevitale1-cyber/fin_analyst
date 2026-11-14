# OpenBot document discovery

Optional fallback after direct RI/regulator/API lookup and before broad web search.
Background release prefetch never starts the bot. Existing searches work with this disabled.

Render runtime secrets/settings (never commit their values):

- `OPENBOT_WEBHOOK_URL`: the saved routine's HTTPS endpoint.
- `OPENBOT_WEBHOOK_SECRET`: the full `whsec_...` signing secret, not base64-decoded.
- `OPENBOT_CALLBACK_ORIGIN`: `https://api-finanalyzer.onrender.com`.
- `OPENBOT_DISCOVERY_ENABLED`: `1` only after the external round-trip test passes.

Routine event type: `finanalyser.document.search`. Events contain only the public symbol,
fiscal year/quarter, document type, request ID and a short-lived callback credential.
No user identifiers, private documents or analysis content are transmitted.

The routine must POST JSON to `data.callback_url`, using `Authorization: Bearer <data.callback_token>`.
It must verify that the callback origin is exactly the configured FinAnalyser origin,
and its path is `/api/document-search/openbot/result/<data.request_id>`, without redirects.
Return the original `symbol`, numeric `fiscal_year`, numeric `fiscal_quarter`,
`document_type` (`release` or `transcript`), `status` (`found`, `not_found`,
`temporarily_unavailable`) and `source_url` (direct HTTPS document URL or empty).
Never echo credentials in chat or store them in a command history/file.

Discovery waits at most 70 seconds; callback credentials expire after 90 seconds.
Concurrent requests share an existing discovery for that company/fiscal period/type.
Only known issuer and regulator hosts are downloaded, with redirects checked individually.
The existing independent issuer/fiscal period/financial content validation still applies.
Call transcripts additionally require transcript content and matching speakers/issuer/period.
Third-party copies and unverified CDN URLs are not accepted.

The desktop host must be running, signed in and online on the OpenBot relay.
An offline relay fails fast and normal web search remains available. The routine URL alone
does not prove connectivity; test delivery AND callback before enabling discovery.

Official protocol: https://github.com/nightly-labs/openbot/blob/main/docs/webhooks.md
