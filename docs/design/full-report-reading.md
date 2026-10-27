# Full report reading surface

Reference: https://www.clearthesis.ai/thesis/AAPL, observed 25 October 2026.

The published Apple and NVIDIA editions in Portuguese and English now share a 720px white paper, 40px desktop / 20px mobile gutters, a compact navy identity header, six summary links, Lora narrative, restrained highlights and a collapsible contents menu. Financial content and source links belong to FinAnalyser; the reference's analysis and valuation judgments are not copied.

## Routes and ownership

| Reference | Local route |
| --- | --- |
| `/thesis/AAPL` | `/published-reports/aapl-20261022.html`, `/published-reports/aapl-20261022-en.html` |
| Shared report design | `/published-reports/nvda-20261022.html`, `/published-reports/nvda-20261022-en.html` |

`frontend/public/report-layout.css` owns the shared presentation. `report-reading.js` owns font, font-size, highlight and contents behavior. Existing per-report scripts continue to own chart data and financial interactions. `CompanyReportReader.tsx` keeps the saved-report reader aligned through compact contents, 15px Lora prose and accessible reading buttons.

The existing Lora font and license in `public/report-assets` are reused. No additional dependency or external font request was introduced.

## Editorial arrangement

Thesis → indicators (including the existing Apple price chart) → quality → business → competitive advantage → financial history → management → outlook → risks → market view → conclusion. IDs and incoming links remain unchanged; contents follow the new order.

Apple's five narrative summary labels are shortened, with complete wording retained in accessible labels/tooltips and the analytical sections. The sixth item quotes its dated, existing P/E metric, not a new fair-value judgment. NVIDIA's summary quotes six existing quality-factor scores, linking to the full seven-factor explanation. No financial score is recalculated.

## Reproduction and checks

Run `python frontend/scripts/refine-report-reading.py` after regenerating the published HTML. It is idempotent and checks that paragraphs, tables, external source links, inline chart scripts and all eleven sections survive the transformation. It does not generate financial research.

Checked locally: production build with `npm run build -- --webpack`, TypeScript, published-report route tests, JavaScript syntax and diff whitespace. Browser coverage: four editions at 390, 768, 1440 and 1920px; no horizontal page overflow or missing images; canvases retain usable dimensions. Manual controls: font and size, highlights, contents navigation/focus, quality explanation, price period and historical series. Captures and geometry results are in the parent workspace's `design-audit/full-report-reading-20261025` directory.

## Deliberate differences

FinAnalyser branding, cutoff dates, sources, research and existing feedback remain. The published collection contains analyst targets but no proprietary fair-value section, so no unavailable valuation module or estimates have been added. NVIDIA has fewer visual datasets than Apple; its existing financial chart and tables remain. Saved reports use the existing React reader, while published editions use static HTML with one shared stylesheet and behavior file.

Publication is separate from the local review preview. Rollback consists of reverting this design change; report data and stored access permissions are unaffected.

## NVIDIA enrichment and embedded feedback

`enrich-published-reports.py` adds concise bilingual editorial context drawn from the supplied NVIDIA standalone draft. The original public 5/5 assessment and the existing decision not to publish a proprietary fair value remain in place: the supplied draft contains different scores and a separate valuation, neither of which is silently substituted. New narrative, dated figures and chart inputs need the normal financial/editorial review before publication.

The public editions now display analyst targets in the Apple-style consensus panel, with 59 buy, two hold and one sell recommendations aggregated from the 62-person StockAnalysis population for NVIDIA. The observed $328.72 mean and $212.21 reference price are distinct from the competing MarketBeat population and are dated in the report. The reusable React consensus widget only displays data provided in the report, doesn't assume a target horizon, and labels a spot price outside the target range rather than placing it on a misleading endpoint.

Company links use known local logo assets and send readers to the library's company resolver. A company without a published report reaches the library's unavailable/coverage-request state; a link does not imply a report already exists. The saved-report component also recognizes named companies in the competitive section using a bounded list of supported tickers and logos.

The NVIDIA edition adds a revenue mix chart for FY2026, operating cash flow versus net income over FY2022–FY2026, and an explicitly qualitative radar: an integrated system and supply scale have stronger supporting evidence; switching costs are only partially supported. The radar is not a numeric valuation or the quality score. Each visualization has a readable data table and source; it remains interpretable if charts do not load.

Published feedback frames begin hidden and appear only after the same-origin feedback component signals that it has loaded. If the route returns an error, a timeout leaves the error document hidden and provides an accessible retry message. Verify both successful and failed route states when deploying; this presentation guard does not repair an unavailable authentication or API service.

Run `python frontend/scripts/enrich-published-reports.py` after the reading-layout script when regenerating editions. Re-running the enrichment is idempotent.
