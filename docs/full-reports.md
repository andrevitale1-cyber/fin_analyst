# Full report library

The dashboard's **Explore full report** button opens `/en/dashboard/reports?analysisId=…` (or `/pt/…`). Opening the library itself never generates a report. Generation happens only after a completed analysis is opened through that button.

The default library view is a demonstration gallery, with search at the top. To add a demonstration, run an automatic analysis against a public release/transcript and open **Explore full report** once. The completed full report then appears for every signed-in user. Visitors can browse and open saved demonstrations without triggering AI generation. Search filters company and period; private reports appear separately for their owner.

## Reuse and privacy

- PostgreSQL retains the source text used by each new analysis (up to the existing 180,000-character limit).
- A full report is keyed by canonical issuer, requested year and quarter, language, document type, exact retained evidence, model, and prompt revision.
- Full reports from public releases/transcripts are visible to all signed-in users and reuse the same saved content. Neither another user's history nor their identity is exposed.
- Uploaded documents and older analyses without retained originals are scoped to their owner. They cannot enter the public cache.
- Transaction advisory locks serialize generation for one cache key across processes. A second request waits and reuses the committed result. Failed or invalid generations roll back without saving partial reports.
- The original short analysis still runs normally. This cache saves subsequent **full-report** generations.

## Security and deployment

New endpoints require a Clerk session bearer token, verify its RSA signature and claims, and derive the user ID from its signed subject. Generation requires ownership of the selected analysis. Saved report reads require either the database's public flag or the subject's own library link. The client and model cannot choose visibility.

Production defaults match the current Clerk instance. Configure these only when using a different instance or local sign-in:

- `CLERK_ISSUER`: default `https://clerk.finanalyser.com.br`
- `CLERK_AUTHORIZED_PARTIES`: exact comma-separated frontend origins; default `https://finanalyser.com.br,https://www.finanalyser.com.br`

For local authenticated previews, explicitly configure the development Clerk issuer and the local origin. No session verification bypass is provided.

`init_db()` adds `analysis_documents`, `full_reports`, and `full_report_access` with `CREATE TABLE IF NOT EXISTS`, plus an additive `is_public` flag defaulting to false. Existing reports are published only when a retained public source with nonempty text and a matching citation URL proves their provenance; uploads and legacy expansions stay private. Existing history is preserved. Use the service's normal database migration/back-up procedure when deploying. Backend requirements add `PyJWT[crypto]` for RSA verification. No new AI or financial-data subscription is required.

## First-version coverage

Reports have seven sourced sections: thesis, business, financials, moat, management, risks, and valuation. They expand the selected retained document, including comparative figures already present in it. Missing facts must be identified rather than invented. Older analyses can be expanded privately, with an explicit warning that the original source is unavailable.

This version does not automatically acquire multiple years of statements, live prices, analyst estimates, or industry research. Annual/TTM EPS with source evidence can enable an optional scenario calculator; quarterly EPS is never annualized. Growth, multiples, and discount rates are user assumptions. The calculator performs deterministic arithmetic and does not constitute an AI price target.

## Validation

Offline tests cover cache identity, private-source isolation, concurrent requests, failure rollback, ownership checks, signed/expired/forged JWTs, structured output, citations, and unsupported valuation inputs. No paid AI request is needed for regression tests.

The structured-output schema and prompt impose the same text/list limits as the server validator. Valid sections received in a different order are sorted by their IDs without changing their contents; missing/duplicate sections and unknown source IDs remain invalid. Generation failures emit `full_report_failed` with safe provider status/code/parameter/request ID or validation field/type only. Document text, prompts, keys, raw provider messages, and generated input values are never logged. Failed generations are not retried automatically or saved as partial reports.
