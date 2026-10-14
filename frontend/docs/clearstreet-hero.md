# Clear Street hero and navigation

Source: https://www.clearstreet.io/ — inspected live through the adjacent `design-reference-cloner/.agents/skills/clone-website` workflow on October 13, 2026.

Destination: the existing FinAnalyzer `/en` and `/pt` homepages. Local preview: http://localhost:3012/en.

## Ownership and references

- `components/LandingIntro.tsx` and its CSS own the floating navigation, desktop dropdowns, mobile menu, hero composition and perspective animation.
- `app/[locale]/page.tsx` replaces the previous navigation/hero with this component. Remaining authored sections are preserved.
- `public/benefits/hero-analysis.png` is the user's supplied FinAnalyzer Meta report screenshot, copied unchanged. CSS separates its visible panels for the animation.
- The existing local Reyhan regular/medium fonts from Clear Street are reused. The page color is `#2e21de`; supporting text is `#9bbcfd`.

## Source behavior and adaptation

The desktop source has a centered 52px-high lavender navigation capsule, a 200vh hero with a sticky viewport, a 3.783-second introductory video, and a scroll-driven image sequence that brings its separated dashboard panels together. Below 1291px, the hero stops pinning; below 1024px navigation becomes a compact menu. The mobile source is 100svh, with 40px/44px title typography and the dashboard above readable text.

The local version recreates the perspective/layer choreography in editable CSS and GSAP using the actual FinAnalyzer screen. It does not embed the Clear Street dashboard video or its production JavaScript bundles. Desktop scroll progress assembles the panels; mobile animation repeats without video autoplay requirements or playback controls. Reduced-motion preferences use a stable composition. Product branding, copy and navigation destinations are adapted to FinAnalyzer.

Desktop Clients/Services controls open real dropdowns. Mobile Menu opens a scrollable navigation sheet; selecting a destination, clicking outside or pressing Escape closes it. Search, sign-in and primary actions lead to the existing dashboard. Section anchors reserve space for the fixed header.

## Verification and remaining differences

Rendered source/local captures are saved in the workspace's `design-audit/clear-hero/` directory. Browser checks cover 320, 390, 1024, 1440 and 1920px widths, English and Portuguese, loaded hero imagery, no horizontal overflow, desktop/mobile menu behavior, Escape dismissal and section navigation. A production Webpack build passes.

The source's pre-rendered dashboard geometry/shading is approximated with native transforms and the FinAnalyzer screenshot. Its Cookiebot, accessibility widget and promotional popup are outside this scope. Mobile checks use a Chromium browser with touch emulation, not a physical iPhone.
