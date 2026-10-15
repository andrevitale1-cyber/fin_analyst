# Full report library

The default Full Reports screen presents a centered company search, company shortcuts, saved company dossiers, older period reports, and the signed-in user's private reports. Opening the library or typing a filter never starts AI generation. Submitting a company search or choosing an uncached shortcut opens a broad company dossier through `POST /api/full-reports/company` with `{company, locale}`. A saved shortcut opens its report with GET.

Public automatic analyses link to `/{locale}/dashboard/reports?company=…`. Uploaded and legacy analyses retain their private/period expansion at `?analysisId=…`; historical reports are never relabelled as company-wide research. The company reader ends with an action to open the normal analysis form with its company prefilled. It does not automatically analyze a quarter.

## Company research and presentation

The company dossier is a continuous report with linked sections: thesis, business, financials, moat, management, market sentiment, outlook, risks, valuation, and verdict. Supported evidence can also populate six summary signals, seven quality factors, tracking metrics, segment/geography breakdowns, three to five annual financial periods, dated market figures, and sourced management guidance or analyst consensus.

Research uses one bounded OpenAI web-search request (at most four tool operations, 4,000 output tokens), followed by one structured synthesis (at most 11,000 output tokens). Public SEC companyfacts data is requested in parallel from fixed trusted endpoints for annual financial history. Web-search citations become research notes, not claims of verbatim primary-source verification. At least three cited public research sources are required. Model output is validated, and only supplied source IDs can appear in a report.

Missing data stays null/empty. Market prices retain their quoted date and currency and are not represented as real-time prices. Financial history is annual; quarterly EPS is never annualized. The quality score is a whole-number AI assessment calculated from at least three supported quality factors; it is distinct from a quarter's analysis grades.

Valuation uses positive annual/TTM EPS evidenced in a primary source. For SEC evidence the baseline must match the latest disclosed annual EPS. Bear/base/bull growth, P/E and discount rates are explicitly AI assumptions; the server calculates five-year future values, discounted illustrative values, and comparable-currency price changes. These scenarios are separate from sourced management or analyst projections. Valuation is unavailable when its prerequisites are missing. No price target is copied from Clearthesis.

## Reuse, costs and privacy

- Successful company reports are shared across signed-in users, keyed by canonical issuer, language, ISO week, model, and report version.
- Cited research is committed separately and shared across languages. If synthesis fails, retrying can reuse already collected research.
- Transaction advisory locks serialize matching requests across server processes; two users requesting the same version generate it only once.
- Insufficient/incomplete research has a shared ten-minute cooldown to avoid repeatedly charging for the same failed lookup. Requests are not retried automatically.
- Only explicit company identity and public evidence enter the company research flow; private uploads, user history and account identities are not used as research sources.
- Uploaded documents and older analyses without retained original evidence remain private. Period expansion keeps its source/content-based cache and ownership checks.
- Browsing saved reports does not call the AI. OpenAI web search and synthesis use the existing API account and incur normal API usage when a new version is requested.

## Security and deployment

All report endpoints require a signed Clerk bearer token. Public reports can be read by any signed-in user; private reports require that user's library link. The client and model cannot choose visibility.

Production Clerk defaults are `CLERK_ISSUER=https://clerk.finanalyser.com.br` and `CLERK_AUTHORIZED_PARTIES=https://finanalyser.com.br,https://www.finanalyser.com.br`. Local authenticated previews require explicitly configured development issuer/origin; no authentication bypass is provided.

`init_db()` adds `analysis_documents`, `full_reports`, `full_report_access`, and `company_research_cache` without removing history. Existing reports become public only when retained public evidence matches their cited source. Generation failures emit diagnostic identifiers and validation types without logging credentials, source bodies or generated input values. No partial full report is saved on failure.

## Validation

Offline checks cover strict content schemas, source references, numeric/annual EPS guards, deterministic scenario arithmetic, shared cache identity, concurrency, failed research cooldown, ownership, signed/expired/forged JWTs, and rollback. Browser checks use explicit fixtures and mocked authentication/API responses; they do not prove real provider generation or live data availability.
