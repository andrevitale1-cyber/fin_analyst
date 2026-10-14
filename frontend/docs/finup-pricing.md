# Pricing adaptation

Source: https://www.finup.io/en, `.pricing`. Local destination: `/en#planos` and `/pt#planos`, after the Meta and earnings-call analysis sections. Files: `components/PricingSection.tsx`, its CSS module and `app/[locale]/page.tsx`.

Inspected at 1440×1000 and 390×844. Source uses Manrope, dark `#0a0a1f` background, centered 56px/58.8px title, 16px card gaps, 8px corners, 24px card padding, translucent white fill and borders. Highlighted card has a green `#2beb78` border and radial blue glow. Desktop CTA is above the feature rows; mobile CTA moves below them. Mobile cards stack, with approximately 16px side gutters and 30px headings.

Reused the locally stored Finup Manrope 500/600/700 fonts. Added regular weight from `https://cdn.prod.website-files.com/6783bb98f24526592fa4e9d4/68917cd4fbf92e334346f39f_manrope-v19-latin-regular.woff2` as `public/reference/finup/manrope-400.woff2`.

Adaptations: two existing FinAnalyzer plans rather than Finup's three; 7-day trial and Premium R$29/month or R$290/year retained, along with existing included features. A monthly/yearly selector changes both the price and the billing footnote. Premium badge says “Full access”, without claiming popularity statistics. CTAs use the established radial button treatment and route to the locale-aware dashboard. Cards fit a centered 848px grid to accommodate two plans. No new checkout or sales-contact workflow.

Removed the old AI Score, Asset Comparator, Earnings Calls, Full History and report-export sections between AI Analysis and Pricing, and their unused private demos and mock data. Kept the benefits, aggregated table, AI Analysis, navigation and footer.

Checks: production Webpack build; source/local desktop and mobile screenshots; 320/390/1440/1920px layout checks; monthly→yearly→monthly price/footnote checks; dashboard links and adjacent section order. Physical iPhone and paid API generation are outside this verification.

Benefit presentation update: five groups for the trial, six for Premium, with a bright bold title and one short explanation per group. Trial emphasizes trying the full workflow; Premium emphasizes ongoing analysis, retrieving saved research, comparisons, document uploads, downloads, call analysis, support and priority. Existing prices and access terms retained.
