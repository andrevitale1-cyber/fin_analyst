# Full report showcase

Reference: https://www.finup.io/en — the six-card feature carousel following “Manage all your payments in one account” (`.swiper.is-team`, `.cart.is-values`). Local destination: `/pt#full-reports` and `/en#full-reports`, after the call analysis section and before pricing.

Owned files: `components/FullReportShowcase.tsx`, its CSS module, `components/apple-report-preview.json`, and the import in `app/[locale]/page.tsx`.

## Observed design and behavior

Dark `#0a0a1f` background; tall cards with a radial blue glow, subtle white borders, rounded corners, centered product visuals and centered title/body copy. The reference uses Manrope, approximately 32px/24px card titles/body at its full desktop scale. Large white arrows overlap the sides. Desktop shows roughly three cards plus a partial next card. Mobile keeps one horizontal row with the next card partly visible; cards do not stack. Navigation is click/swipe driven rather than an automatic marquee.

Reused the Manrope files already stored in `public/reference/finup/` and the existing Apple asset at `public/benefits/logos/apple.svg`. No Finup product screenshots or production bundles were embedded. The visuals are editable HTML/CSS, using the actual published Apple report.

## Content provenance

Source editions: `public/published-reports/aapl-20261022.html` and `aapl-20261022-en.html`, research cutoff October 22, 2026. The visible publication date identifies this as a historical report preview, not a current quote.

- Products, revenue history and fiscal years come from the report's `visual-data` JSON.
- TTM revenue USD 466.8B and FCF USD 136.7B are through June 27, 2026. Operating margin 33.6% is 9M FY2026, explicitly labeled separately.
- Overall quality 4/5, moat 5/5, capital efficiency 5/5 and growth 3/5 match the published scorecard.
- The preview contains six sections: thesis, metrics, revenue composition, quality scorecard, financial history and risks. Links use `publishedReportForCompany` to select the Portuguese/English edition and the real section anchors.

## Intentional adaptations

FinAnalyzer content and Apple data replace Finup payment features. Controls stop at the first/last card; they do not wrap. Mobile has visible 44px navigation buttons below the cards, in addition to native horizontal touch scrolling. Arrow keys work when the rail is focused. Smooth scrolling respects reduced-motion preferences. No new carousel dependency, automatic scrolling, duplicate slides, financial forecast or valuation was added.

Validation: production Webpack build and TypeScript check; browser review at 1440px, 1920px, 390px and 320px; arrow boundaries, keyboard navigation, PT/EN links, matching report anchors, source-data reconciliation and absence of page-level horizontal overflow. Local visual checks used an isolated preview because the application’s private Clerk key is not configured locally; application authentication was preserved. Physical-device touch behavior was not tested.
