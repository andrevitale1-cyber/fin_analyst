# Full report library

The default Full Reports screen presents a centered company search, company shortcuts, saved company dossiers, older period reports, and the signed-in user's private reports. Opening the library or typing a filter never starts AI generation. Submitting a company search or choosing an uncached shortcut opens a broad company dossier through `POST /api/full-reports/company` with `{company, locale}`. A saved shortcut opens its report with GET.

Public automatic analyses link to `/{locale}/dashboard/reports?company=…`. Uploaded and legacy analyses retain their private/period expansion at `?analysisId=…`; historical reports are never relabelled as company-wide research. The company reader ends with an action to open the normal analysis form with its company prefilled. It does not automatically analyze a quarter.

## Company research and presentation

The company dossier is a continuous report with linked sections: thesis, business, financials, moat, management, market sentiment, outlook, risks, valuation, and verdict. Supported evidence can also populate up to six summary signals and seven quality factors, tracking metrics, segment/geography breakdowns, three to five annual financial periods, dated market figures, and sourced management guidance or analyst consensus. Signals and quality factors may contain a supported subset; repeated category IDs are rejected. Synthesis requires each included quality factor to have a cited integer rating from 1 to 5 and omits factors without enough evidence. It never inserts a default rating. Legacy null ratings remain accepted without being converted into scores.

Research uses one bounded OpenAI web-search request (at most four tool operations, 4,000 output tokens), followed by one structured synthesis (at most 11,000 output tokens). It prioritizes exact financial tables from annual/results releases, dated market figures and sourced guidance, with a remaining search/open operation directed at an original release when a key figure is absent. Public SEC companyfacts data is requested in parallel from fixed trusted endpoints for annual financial history; balance-sheet-only dates cannot displace annual operating periods. Web-search citations become research notes, not claims of verbatim primary-source verification. At least three cited public research sources are required. Model output is validated, and only supplied source IDs can appear in a report.

Missing data stays null/empty. Market prices retain their quoted date and currency and are not represented as real-time prices. Financial history is annual; quarterly EPS is never annualized. The quality score is a whole-number AI assessment calculated from at least three supported quality factors; it is distinct from a quarter's analysis grades.

Company metrics keep their original `value` display string for compatibility and add nullable `numeric_value`, `currency` and `unit`. New synthesis supplies numeric values in full base units, evidenced ISO currency codes for monetary figures, and a unit of `currency`, `currency_per_share`, `percent`, `multiple` or `number`. Percent values use percentage points (`25` means 25%). Typed values must be finite and have their unit; only monetary units carry a currency. If the model omits typed fields for a known annual SEC metric, the server can recover them from the exact structured SEC record for its cited source, matching label and a unique fiscal-year period. It never infers currency from a ticker, converts units from ambiguous display text, or substitutes quarterly/TTM values. Older metrics without a matching record retain their display string. Reader-facing labels follow the requested report language. `coverage` is a complete short editorial sentence about the company and investment question; material evidence gaps belong briefly in their relevant section, rather than the introduction. Text is never truncated by the server to meet content limits.

Valuation uses positive annual/TTM EPS evidenced in a primary source. For SEC evidence the baseline must match the latest disclosed annual EPS. Bear/base/bull growth, P/E and discount rates are explicitly AI assumptions; the server calculates five-year future values, discounted illustrative values, and comparable-currency price changes. These scenarios are separate from sourced management or analyst projections. Valuation is unavailable when its prerequisites are missing. No price target is copied from Clearthesis.

## Reuse, costs and privacy

- Successful company reports are shared across signed-in users, keyed by canonical issuer, language, ISO week, model, and report version.
- Version `company-v2` invalidates earlier research/synthesis cache identities for new company requests. New company reports and library summaries expose `report_version`; previously saved reports remain accessible by their existing ID.
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

## Search and presentation reference

The search and company shortcuts in `/{locale}/dashboard/reports` follow the public [Clearthesis dashboard](https://www.clearthesis.ai/dashboard): centered 580px search, 52px height, 14px corners, search icon, slash shortcut, white surface and shadow; small 18px company logos in bordered 10px-radius shortcuts. The layout wraps at mobile widths. Suggestions use the app's known companies and saved reports, without a paid lookup while typing. They support arrows, Enter and Escape; an explicit ticker search remains available.

Public logo assets for MU, AMD and NOW were observed at Clearthesis `/api/logo/{ticker}` and stored under `frontend/public/report-logos/`; other logos reuse existing local assets. Search and shortcut appearance were compared on desktop and mobile; the surrounding FinAnalyzer header and report gallery are preserved.

Report figures display localized separators, currency and millions/billions/trillions; per-share values stay unscaled. Highlights use readable cards rather than long green pills. Company headers omit operational coverage prose. Cards and shortcuts request the new generation when an older company report is selected; direct links preserve the saved report with an explicit update action. Older content is not assigned guessed scores. Browser checks use mocked reports and do not establish live generation success.
