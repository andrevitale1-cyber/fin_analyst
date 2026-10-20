# Company research pipeline

The company-v11 report keeps the quarterly methodology but adds company-wide research, a typed operating model and independent validation. Quarterly/call prompts, daily entitlements and default private visibility are unchanged.

## Flow

1. Authenticated request creates or reuses a Postgres job through `/api/report-jobs`. A ready public/owned report returns immediately. A new private report reserves the existing allowance once.
2. Five bounded research topics run in parallel: business/competition, financials, management, outlook and market/risks. The cheaper analysis model gathers evidence; the full-report model writes and reviews. A missing topic can retry without repeating successful topics.
3. SEC companyfacts or CVM DFP provides five annual periods. CVM filters the registered issuer, consolidated statements, submission date, version, full-year duration and share class. EPS retains per-share units even if statements are in thousands. Comparative restatements replace older values. Provenance records the archive, filing date and version for each raw financial cell.
4. The analysis model extracts 32–40 supported facts. Original financial tables remain available to writing and audit.
5. Agent 3 proposes three sets of explicit AI operating assumptions. Python computes the two revenue drivers, margin transitions, EBIT, EBITDA, income, EPS, capex, working-capital investment and FCFF for five fiscal periods. Reported actuals, guidance/consensus and AI estimates remain separate.
6. Supported methods include projected P/E, historical normalized P/E, FCFF DCF, EV/EBITDA and P/B for financial firms. WACC discounts enterprise values; cost of equity discounts P/E scenarios. Discounting respects the research date and fiscal period ends; the remaining part of the current fiscal year uses pro-rata cash flow. Net debt bridges enterprise and equity values. Missing debt is not treated as zero. Historical EPS normalization includes losses.
7. A code verifier rebuilds the complete model from the original primary inputs. An independent model reviews claims, source support, units, periods, conviction, assumptions and narrative consistency. A bounded repair corrects the evidence dossier against original surrounding context before replacing flagged report fields. This prevents an inaccurate extracted denominator or accounting basis from contaminating the repair again. Incomplete/unapproved reports never enter the library.
8. The reader shows synchronized bear/base/bull projections, Chart.js revenue charts, valuations by method, assumptions and source popovers. Values from different methods may disagree; they are not forced into an artificial consensus.

## Reliability and access

- Jobs are owned by the authenticated account. An analysis ID is resolved only from that account's history; private uploaded documents never enter shared company evidence.
- Requests deduplicate per account; generation still deduplicates across accounts using the existing shared report cache and advisory lock. An existing private report grants access only after the requesting account's allowance is checked.
- The existing API service hosts one bounded queue consumer. Jobs live in Postgres, use `FOR UPDATE SKIP LOCKED`, heartbeat every 15 seconds, and can reclaim an interrupted attempt once. Failed model/audit jobs do not retry automatically. Stage checkpoints preserve completed paid work.
- Pending allowance leases are renewed while running. Completed usage is committed with report access; unused/failed reservations are released. No Clerk tokens are stored in the queue.
- The URL retains a job ID for reload/resume. Leaving the page stops polling, not generation.
- `REPORT_JOB_WORKER=0` disables this instance's consumer; another instance can consume the same queue. Shutdown stops new claims, and an interrupted task can be reclaimed after its lease expires.

## Measurement and cost

`report_runs` records company/model, stage, timings, safe error class and provider-reported input/output/cached/reasoning tokens and web-search call counts. It never stores prompts or source text. Checkpoint content is internal public evidence, not a published report.

`REPORT_MODEL_PRICING_JSON` optionally supplies verified USD rates by the exact response model name: `input_per_million`, `cached_input_per_million`, `output_per_million`, `search_per_call`. When absent, monetary cost is unknown, not zero. Configured estimates are estimates, not invoice totals. A confirmed ready-report cache hit performs no generation calls.

Models remain controlled by `OPENAI_ANALYSIS_MODEL` and `OPENAI_FULL_REPORT_MODEL`. No new Redis, paid worker service or dependency is required for this first deployment.

## Explicit assumptions and limits

- Shares and net debt are held constant; margins transition linearly. These assumptions are visible in the reader.
- When the issuer does not provide weighted diluted shares separately, attributable income divided by the exact reported diluted EPS provides an approximate diluted share count. EPS rounding is disclosed.
- Forward inputs are AI scenarios, never fabricated consensus. Company-specific driver labels/rationales explain the generic capacity and productivity factors.
- A model that lacks usable inputs falls back to the existing evidenced EPS workflow. Neither path fabricates a missing input.
- CVM structured identity currently covers issuers recognized in the existing verified company map. Unknown issuers retain the public document/research fallback.

## Validation

Offline checks cover CVM unit/share-class/date/version filtering, calculations, mutation rejection, missing-data behavior, financial-sector method selection, private access, quota reservation/release, job recovery, selective checkpoints and telemetry.

The opt-in `VALIDATE_DEEP_REPORTS_20261020=1` runs one private MU and VIVA3 pilot per version, requiring five years, three scenarios, an additional valuation method and an approved audit. It never publishes the pilots or consumes an end user's allowance. Diagnostics are in `maintenance_tasks` under `deep-report-pilot-v4:*` and `report_runs`.

References:
- https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/
- https://developers.openai.com/api/docs/guides/token-counting

### Live validation status — October 20, 2026

- MU passed the company-v10 live pilot: ten sections, five years, three scenarios, normalized earnings plus a terminal P/E cross-check. The run took 151,008 ms with some upstream research reused, 88,211 input tokens and 10,895 output tokens. Reopening the ready report took 422 ms end-to-end in the server pilot and made zero generation calls. These are observed runs, not promised cold-generation latency.
- VIVA3 passed an earlier company-v8 pilot with five annual periods and three scenarios. A subsequent company-v10 audit rejected a sales-versus-production denominator and the accounting basis of an adjusted-margin comparison. The evidence-repair step and context/denominator tests now address that failure; the last revision still needs a live rerun.
- The company-v11 pilots received provider HTTP 429 / `credit_balance_exhausted` before writing. No company-v11 report was saved. Automatic pilot execution has been disabled (`VALIDATE_DEEP_REPORTS_20261020=0`) to avoid repeated calls. Replenished provider credit is required for the final live validation; no billing settings were changed.
- Local verification: 338 backend tests passed; frontend production build and TypeScript checks passed. Monetary estimates remain unknown because verified model rates were not configured.
