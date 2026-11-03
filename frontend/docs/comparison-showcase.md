# Comparison showcase

Reference: https://www.finup.io/en, “Quick API integrations” (`section.api`, `.api-content`). Local destinations: `/pt#comparar-resultados` and `/en#comparar-resultados`, after the Apple full-report carousel and before pricing. Owned by `components/ComparisonShowcase.tsx`, its CSS module and the import in `app/[locale]/page.tsx`.

The reference has a rounded `#f2f3f8` surface on a dark background, a centered 56px Manrope heading with a blue gradient, an 18px description, a central integration illustration, three green checkmarks and a white CTA. Its illustration uses separate desktop/mobile looping videos, observed via the DOM. Mobile uses the same vertical hierarchy with smaller padding.

Adaptation: editable HTML/CSS displays two saved quarterly results connected through the FinAnalyzer mark to the verdict. A small CSS pulse suggests the connection; reduced-motion preferences disable it. The Finup payment/API videos were not reused because they describe another product. Static preview cards have no fake dropdown controls. The CTA opens the locale-aware `/dashboard?view=comparison`; it does not submit a duel or consume quota.

Content comes from the two user-supplied screenshots: AMZN versus GOOGL, 3Q/2026, fiscal end September 30, 2026, saved November 2, 2026. GOOGL is the stronger result with moderate confidence, leading on growth, profitability and balance-sheet resources relative to long-term debt. Cash generation and outlook remain insufficient for a comparable verdict. No scores, returns or financial figures were invented. The example is visibly dated and labeled as a real comparison, rather than a live result.

Assets reuse the app’s existing Manrope fonts, AMZN/GOOG WebP logos and FinAnalyzer icon. The green check SVG matches the observed source. Interface copy is available in Portuguese and English, and Premium/quota wording matches the product.

Validation: production Webpack build; browser review at 1440, 1920, 390 and 320 CSS pixels; no page-level horizontal overflow; logo loading; localized CTA destinations; example period, verdict, confidence and limitations checked against the supplied screenshots. Local layout review uses the isolated preview under ignored `smoke-output/`, preserving the application’s authentication. Physical-device touch testing was not performed.
