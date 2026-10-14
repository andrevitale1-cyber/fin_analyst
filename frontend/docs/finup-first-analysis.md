# First analysis CTA

Source: https://www.finup.io/en — “Get your first card for only $1!” (`.cta-large.is-2`). Destination: `/en` and `/pt`, directly after the three `AnalysisStory` videos and before the benefits section. Owned by `components/AnalysisStory.tsx` and its CSS module.

Inspected source at 1440×1000 and 390×844. Dark background `#0a0a1f`, centered two-line heading (blue gradient first line, white second), Manrope 700 at 56px/58.8px on desktop and approximately 30px/31.5px on mobile. Description width 460px; 24px title gap and 48px button gap. Desktop padding 160px above, 128px below; mobile approximately 96px above, 48px below. Source glow is full content width on desktop and 200% centered width on mobile.

Reused source assets, stored under `public/reference/finup/`:

- `first-analysis-glow.avif`: `https://cdn.prod.website-files.com/6783bb98f24526592fa4e9d4/6784d5ad148e3dba7148e41b_Finup%20-%20Angular%20gradient%20-%20small.avif`
- `manrope-500.woff2`: `https://cdn.prod.website-files.com/6783bb98f24526592fa4e9d4/68917cd4911134dfc16ba1d5_manrope-v19-latin-500.woff2`
- `manrope-600.woff2`: `https://cdn.prod.website-files.com/6783bb98f24526592fa4e9d4/68917cd46c7e13efd87455e0_manrope-v19-latin-600.woff2`
- `manrope-700.woff2`: `https://cdn.prod.website-files.com/6783bb98f24526592fa4e9d4/68917cd4999f186d81890d8b_manrope-v19-latin-700.woff2`

Intentional adaptations: FinAnalyzer copy; one centered link to the locale-aware `/dashboard`; no coupon, price, or copy-code control. Glow overlap adjusted for the removed promo instructions. Text stays visible without a reveal dependency. Existing story video playback and captions are unchanged. AVIF files bypass locale middleware so the glow loads as an image instead of redirecting to an HTML route.

Validation: production Webpack build; source/local desktop and mobile screenshots; 320, 390, 1440 and 1920px browser checks for overflow, CTA destination, asset loading, removed orbit videos, preserved inline/muted/loop attributes. Physical iPhone playback and paid OpenAI calls were not tested for this change.
