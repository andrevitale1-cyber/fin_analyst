> The reader-facing company-report flow now uses the hybrid thesis library. See [thesis-library.md](thesis-library.md). The generation pipeline below is used for explicit editorial preparation, not a reader click.

# Full report library

The default Full Reports screen presents a centered company search, company shortcuts, saved company dossiers, older period reports, and the signed-in user's private reports. Opening the library or typing a filter never starts AI generation. Submitting a company search or choosing an uncached shortcut opens a broad company dossier through `POST /api/full-reports/company` with `{company, locale}`. A saved shortcut opens its report with GET.

Public automatic analyses link to `/{locale}/dashboard/reports?company=…`. Uploaded and legacy analyses retain their private/period expansion at `?analysisId=…`; historical reports are never relabelled as company-wide research. The company reader ends with an action to open the normal analysis form with its company prefilled. It does not automatically analyze a quarter.

## Company research and presentation

The company dossier is a continuous report with linked sections: thesis, business, financials, moat, management, market sentiment, outlook, risks, valuation, and verdict. Supported evidence can also populate up to six summary signals and seven quality factors, tracking metrics, segment/geography breakdowns, three to five annual financial periods, dated market figures, and sourced management guidance or analyst consensus. Signals and quality factors may contain a supported subset; repeated category IDs are rejected. Synthesis requires each included quality factor to have a cited integer rating from 1 to 5 and omits factors without enough evidence. It never inserts a default rating. Legacy null ratings remain accepted without being converted into scores.

Research uses one bounded OpenAI web-search request (at most four tool operations, 4,000 output tokens), optionally one targeted market lookup, then one structured synthesis (at most 11,000 output tokens). When the main evidence lacks numeric dated analyst/market data from an independent provider, the extra lookup searches market providers and financial news for consensus, targets and market reactions; it is limited to two tool operations, 2,000 output tokens and 35 seconds. It runs at most once, with no retry loop. Missing citations, provider errors or a timeout preserve the usable company evidence and leave unavailable market fields empty. Existing dated market evidence skips this request. It prioritizes exact financial tables from annual/results releases, dated market figures and sourced guidance, with a remaining search/open operation directed at an original release when a key figure is absent. Public SEC companyfacts data is requested in parallel from fixed trusted endpoints for annual financial history; balance-sheet-only dates cannot displace annual operating periods. Web-search citations become research notes, not claims of verbatim primary-source verification. At least three cited public research sources are required. Model output is validated, and only supplied source IDs can appear in a report.

Missing data stays null/empty. Market prices retain their quoted date and currency and are not represented as real-time prices. Financial history is annual; quarterly EPS is never annualized. The quality score is a whole-number AI assessment calculated from at least three supported quality factors; it is distinct from a quarter's analysis grades.

Numbers at a glance prioritize the latest scale, profitability and valuation indicators; annual revenue comparisons belong in financial history, rather than repeated metric cards. Summary signals use concise labels, with explanations in their narrative sections.

SEC evidence includes calculated operating, gross and free-cash-flow margins when their inputs share the same currency and exact annual period and revenue is positive. Losses keep their negative sign; nonpositive revenue or missing inputs produce no margin. Evidence text and structured `annual_financials` mark these derived figures as percentages. Revenue CAGR uses comparable currency endpoints with a positive baseline, nonnegative ending revenue and the actual elapsed interval: five annual observations normally span four years, not five. No ROIC is inferred without invested-capital evidence.

Company metrics keep their original `value` display string for compatibility and add nullable `numeric_value`, `currency` and `unit`. New synthesis supplies numeric values in full base units, evidenced ISO currency codes for monetary figures, and a unit of `currency`, `currency_per_share`, `percent`, `multiple` or `number`. Percent values use percentage points (`25` means 25%). Typed values must be finite and have their unit; only monetary units carry a currency. If the model omits typed fields for a known annual SEC metric, the server can recover them from the exact structured SEC record for its cited source, matching label and a unique fiscal-year period. It never infers currency from a ticker, converts units from ambiguous display text, or substitutes quarterly/TTM values. Older metrics without a matching record retain their display string. Reader-facing labels follow the requested report language. `coverage` is a complete short editorial sentence about the company and investment question; material evidence gaps belong briefly in their relevant section, rather than the introduction. Text is never truncated by the server to meet content limits.

Breakdowns preserve `value` and add optional `numeric_value`, `currency`, `period` and `group_complete` (false by default). `share` is always percentage points: `51.5` means 51.5%. The server converts fractional shares only for an explicitly complete category/period/source group of at least two rows whose fractions sum to approximately one. It may calculate shares from complete numeric revenue amounts only when they reconcile to annual revenue for the same period and currency. It preserves isolated small percentages and incomplete groups; it never guesses currency or scale from ambiguous display text.

Optional `analyst_consensus` contains nullable `rating`, `analyst_count`, `target_mean`, `target_low`, `target_high`, `bullish`, `neutral`, `bearish`, `currency`, `as_of` and a `source_ids` list. Populated consensus requires cited sources and an ISO observation date; targets also require a currency, finite positive values and low/mean/high ordering. Missing values stay null. All three rating counts, when supplied with an analyst count, must reconcile to that same provider population. The model must not infer counts from a recommendation or combine providers, dates and sample populations. Empty consensus stays null. Analyst targets remain distinct from the model's valuation scenarios.

Valuation uses positive annual/TTM EPS evidenced in a primary source. For SEC evidence the baseline must match the latest disclosed annual EPS. Bear/base/bull growth, P/E and discount rates are explicitly AI assumptions; the server calculates five-year future values, discounted illustrative values, and comparable-currency price changes. These scenarios are separate from sourced management or analyst projections. Valuation is unavailable when its prerequisites are missing. No price target is copied from Clearthesis.

## Reuse, costs and privacy

- Successful company reports are shared across signed-in users, keyed by canonical issuer, language, ISO week, model, and report version.
- Version `company-v3` invalidates earlier research/synthesis cache identities for new company requests. New company reports and library summaries expose `report_version`; previously saved reports remain accessible by their existing ID.
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

## Microsoft report reference and reading layout

The company reader at `/{locale}/dashboard/reports?company=MSFT` follows the public `https://www.clearthesis.ai/thesis/MSFT` layout: a centered 720px paper, compact navy company header, six supported summary signals, Lora body text with optional highlights, current metrics in three groups, a seven-factor quality card, business breakdowns, financial charts, market consensus, outlook, risks, interactive valuation scenarios and verdict. Body gutters are 40px on desktop and 20px on mobile. Account navigation remains FinAnalyzer's; follow/AI-chat/update-subscription controls from the reference are not simulated.

`CompanyReportReader.tsx` owns this presentation; `FullReports.tsx` keeps the authenticated route, search and gallery. `reportBreakdowns.ts` preserves old records and converts fractional shares only with explicit group completeness or reconciliation to the same annual revenue/currency. Segments use a donut and color-matched legend; geography uses the observed world map projection and percentage bars, not a second donut. Sources remain individually linked. The reading controls change font, size and highlights; scenario selection displays that scenario's assumptions.

The already-published MSFT report was inspected through the signed-in browser session: its 0.515/0.485 shares matched reported annual revenue, and its collected sources contained no analyst-consensus evidence. The new research flow adds a bounded, dated market lookup when necessary, without copying Clearthesis financial opinions or making up missing analyst data. Company reports no longer wait for a redundant library fetch; a secondary library request failure cannot mark an already opened report as failed. New generation and cache use `company-v3`; opening old saved IDs remains possible with an update action.

The reference map topology and Lora font are documented in `frontend/public/report-assets/README.txt`; the font license is included. Offline/browser fixtures verify matching fractions, currencies, dates, reader controls, cache reuse and responsive layouts. They do not establish success of a newly paid research/generation request in production.

## Automatic model routing

New quarterly results and earnings-call analyses (PDF upload and automatic search) use `OPENAI_ANALYSIS_MODEL`, default `gpt-6-luna`. Complete company reports, their public-source research and legacy period-report expansions use `OPENAI_FULL_REPORT_MODEL`, default `gpt-6.1-sol`. The server selects the role; the browser cannot override it.

`OPENAI_MODEL` remains the general client setting for unrelated document-search fallback and X drafts. An existing `OPENAI_MODEL=gpt-4.1` does not override the two task-specific settings. Empty task settings use their defaults. GPT-6 requests explicitly use low reasoning effort with the existing token limits, timeouts, structured-output validation and failure handling. There is no automatic switch to a more expensive model.

Company evidence and generation cache keys use the same resolved full-report model as the actual request. Switching models keeps previous saved reports accessible and separates new generated content by model; cached reports remain shared between authorized users. Existing saved reports are not regenerated merely by opening their saved IDs.

Routing and payload tests use mocked provider responses. They do not establish model availability for the production API project or financial-analysis quality; compare representative real results before drawing conclusions about quality or realized cost.
