# Full report library

The dashboard's **Explore full report** button opens `/en/dashboard/reports?analysisId=…` (or `/pt/…`). Opening the library itself never generates a report. Generation happens only after a completed analysis is opened through that button.

## Reuse and privacy

- PostgreSQL retains the source text used by each new analysis (up to the existing 180,000-character limit).
- A full report is keyed by canonical issuer, requested year and quarter, language, document type, exact retained evidence, model, and prompt revision.
- Public releases/transcripts may reuse the same full report across users. Each user receives an independent library link, never another user's history or identity.
- Uploaded documents and older analyses without retained originals are scoped to their owner. They cannot enter the public cache.
- Transaction advisory locks serialize generation for one cache key across processes. A second request waits and reuses the committed result. Failed or invalid generations roll back without saving partial reports.
- The original short analysis still runs normally. This cache saves subsequent **full-report** generations.

## Security and deployment

New endpoints require a Clerk session bearer token, verify its RSA signature and claims, and derive the user ID from its signed subject. The analysis must belong to that subject; report reads require a library link.

Production defaults match the current Clerk instance. Configure these only when using a different instance or local sign-in:

- `CLERK_ISSUER`: default `https://clerk.finanalyser.com.br`
- `CLERK_AUTHORIZED_PARTIES`: exact comma-separated frontend origins; default `https://finanalyser.com.br,https://www.finanalyser.com.br`

For local authenticated previews, explicitly configure the development Clerk issuer and the local origin. No session verification bypass is provided.

`init_db()` adds `analysis_documents`, `full_reports`, and `full_report_access` with `CREATE TABLE IF NOT EXISTS`. Existing history is preserved. The schema is additive; use the service's normal database migration/back-up procedure when deploying. Backend requirements add `PyJWT[crypto]` for RSA verification. No new AI or financial-data subscription is required.

## First-version coverage

Reports have seven sourced sections: thesis, business, financials, moat, management, risks, and valuation. They expand the selected retained document, including comparative figures already present in it. Missing facts must be identified rather than invented. Older analyses can be expanded privately, with an explicit warning that the original source is unavailable.

This version does not automatically acquire multiple years of statements, live prices, analyst estimates, or industry research. Annual/TTM EPS with source evidence can enable an optional scenario calculator; quarterly EPS is never annualized. Growth, multiples, and discount rates are user assumptions. The calculator performs deterministic arithmetic and does not constitute an AI price target.

## Validation

Offline tests cover cache identity, private-source isolation, concurrent requests, failure rollback, ownership checks, signed/expired/forged JWTs, structured output, citations, and unsupported valuation inputs. No paid AI request is needed for regression tests.
