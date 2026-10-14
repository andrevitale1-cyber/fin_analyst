# Earnings-call landing section

Placed immediately after `MetaAnalysisSection`, before Pricing, in both landing locales. Reuses the existing Meta section background, typography, checklist and CTA styles. Desktop layout is reversed: copy on the left, report on the right. Mobile stacks copy above the preview.

The three original Microsoft 2Q/2026 captures supplied by the user are preserved as `public/benefits/calls/microsoft-2q2026-{1,2,3}.png`. No financial figures or report content are regenerated. Next Image serves a responsive preview; each page links to the full-size original. The preview supports vertical scrolling, keyboard focus and visible focus indicators. The English report imagery stays in its original language, with localized surrounding copy.

Checks: production Webpack build; rendered desktop/mobile inspection; 320/390/1440/1920px widths; section order and opposite-side report placement; image loading, keyboard scrolling where content exceeds the frame, dashboard and full-size image links; updated Pricing benefits and monthly/yearly prices. No physical iPhone or paid API generation check.
