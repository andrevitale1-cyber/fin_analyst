# Hybrid research library

Company-wide theses are prepared before readers open them. Quarterly and earnings-call analyses keep their existing prompts, authentication and daily limits. No library lookup, coverage request or click on a quarterly analysis starts a company-report model call.

## Reader flow

- Search opens a published company thesis immediately. Existing private company reports remain readable only by accounts already authorized to read them. A language fallback is clearly identified rather than translated through an unexpected paid call.
- When no report exists, the reader sees an honest unavailable state and can request coverage. The request is deduplicated per account/company/language, does not consume analysis quota and has no promised completion date. Other accounts cannot see that person's requests. A maximum of ten new coverage requests per rolling day bounds abuse.
- Previously saved report URLs continue to work. New public editions do not delete their predecessors or change private reports into public ones. The gallery shows the latest public company edition; a saved older reviewed edition identifies that a newer edition exists.
- Pricing text now describes three Free quarterly/call analyses per day plus the public thesis library. No Stripe subscription, price or payment setting changes.

## Initial collection

The confirmed first collection is Microsoft, NVIDIA, Apple, Google, Amazon, Meta, Petrobras, WEG and Vivara. Migration seeds nine planned Portuguese coverage records. Existing public demonstrations remain readable; seeding does **not** label them as newly researched or reviewed and does **not** call any model.

## Editorial preparation

Run the CLI from `backend/` in the configured operator environment. `DATABASE_URL` is required; preparation also requires funded model access and the existing model key. Never put keys in command arguments or source control.

```text
python -m thesis_library status
python -m thesis_library prepare VIVA3 --locale pt --year 2026 --quarter 2
python -m thesis_library review VIVA3 --locale pt --draft-id <candidate-id>
python -m thesis_library publish VIVA3 --locale pt --draft-id <reviewed-candidate-id>
```

`--year` and `--quarter` identify the latest official fiscal result actually covered by the review; they do not restrict the thesis to that quarter. Operators must confirm this against the original release. Preparation is an explicit paid operation, not a browser request. There is no public prepare/publish API. The CLI connects directly to the database and does not import the application's startup jobs.

The editorial profile uses an independent cache identity so a shallow on-demand report cannot be relabeled as editorial research. Five thematic research tasks can each use four search/open operations and 900–1,200 words; extraction targets 40–48 evidenced facts; writing targets 2,500–3,500 words with bounded field lengths. It has a longer deadline and writing budget. These are research budgets, not a guarantee of quality or a claim to match another product.

The quarterly methodology still governs overlapping fields. Original-document evidence, deterministic financial calculations, explicit AI scenarios and independent audit remain required. A failed stage never publishes a report. Editorial preparation creates a private draft under a service identity, with an explicit review step. It does not consume an end user's allowance. Run metrics and checkpoints remain available for cost and quality review.

Publishing requires the current candidate, the matching company/language, an editorial research profile, approved audit, ten sections, at least three annual periods and an available model with three scenarios. The public edition is a separate copy. An ordinary user's private report cannot be published through this operation. Publication is refused if a newer result is already known or the selected candidate has been replaced.

## Updating after results

When a successful automatic quarterly/call analysis has found an official document, its verified company and fiscal period update coverage metadata in the same database transaction. Private uploads do not feed the shared library or trigger a revision. Older historical results do not replace the latest known period. A newer official result marks a published thesis `needs_update`; readers retain the last approved thesis with a revision-pending notice.

The operator then prepares a new edition, reviews it and publishes it. `status` lists pending revisions and aggregate coverage demand. No unattended paid regeneration, extra Render service or schedule has been enabled. This first version detects results processed by the existing official-document flows; monitoring every issuer's publication calendar independently is a separate scheduling step. A pending revision is never described as an update already completed.

## Migration and verification

The former `/api/report-jobs` POST and `/api/full-reports/company` POST resolve library content instead of creating user generation jobs. Quarterly-history links use the same resolver. The old worker is opt-in (`REPORT_JOB_WORKER=1`) rather than enabled by default; completed legacy job reads remain owner-scoped.

Test without provider calls: library resolution and language preference; public/own-private boundaries; history ownership; request deduplication; official-result ordering; stale-candidate refusal; public-copy publication; absence of public editorial endpoints; existing quarterly and call regression suite. Production build and browser checks cover the reader states. New deep theses still require an explicitly funded editorial preparation and content review; this change alone does not generate the first collection.
