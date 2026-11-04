# Quarterly release discovery

The dashboard submits the selected ticker and market. The server resolves the issuer independently:
SEC CIK for US companies; B3 CVM code, CNPJ and legal name for Brazilian issuers. An unavailable
catalogue does not authorize a guessed identifier: source identity and fiscal period must still validate.

Sources: verified shared document cache, official RI/SEC catalogues, Equibles, then web search.
Brazilian RI catalogues include MZ; the official B3 registry supplies CVM identifiers. Regulatory
links discovered on the web undergo the same document validation. This does not replace a release
with an annual statement or another quarter. Global coverage depends on accessible official sources.

`release_pipeline` verifies issuer, fiscal year/quarter, usable text and financial content before AI.
SEC supplements are limited to two financial attachments inside the same filing directory and must
identify the requested period. No audio, private uploads or third-party company documents enter this cache.

`official_release_cache` stores verified public text, source links, issuer identifiers, content SHA-256,
lookup status and duration. Positive documents expire after one hour. A refresh replaces the fingerprint;
the existing analysis cache includes content, prompt, model and language, so revised documents are reanalysed.
Failed searches never become permanent negative cache entries. Uploaded documents stay private to their workflow.

The Render worker starts 45 seconds after startup, refreshes up to 12 stale lookups hourly, and uses a
Postgres session lock across instances. Initial warm-up covers the nine selected companies. It explicitly
disables paid web search and never calls an analysis model. Set `RELEASE_PREFETCH_ENABLED=0` to stop it.

Structured logs use `release_pipeline`, `release_identity`, `release_supplements`, `release_prefetch`
and `quarterly_validation`. Statuses distinguish not found, search unavailable, wrong issuer/period,
empty document, missing financial content and invalid scores. Inspect `official_release_cache` for trends.

A category explicitly marked N/A stays null, never zero. At least three valid categories, an overall
score and a thesis are required; a missing or malformed label is not treated as N/A. Invalid results
never reach history or completed usage. Screen and PDF retain the unavailable category.

Regression CI runs without real credentials. A separate real-source check is available:
`python backend/scripts/check_release_sources.py --companies MCD ITUB4 --year 2026 --quarter 3`.
It checks discovery and validation only. No analysis is generated or published by this command.
