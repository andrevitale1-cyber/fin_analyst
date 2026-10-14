# Clear Street hero and navigation

Source: https://www.clearstreet.io/ — inspected live through the adjacent `design-reference-cloner/.agents/skills/clone-website` workflow on October 13, 2026.

Destination: the existing FinAnalyzer `/en` and `/pt` homepages. Local preview: http://localhost:3012/en.

## Ownership and references

- `components/LandingIntro.tsx` and its CSS own the floating navigation, ordered desktop links, mobile menu and static hero composition.
- `app/[locale]/page.tsx` replaces the previous navigation/hero with this component. Remaining authored sections are preserved.
- The existing local Reyhan regular/medium fonts from Clear Street are reused. The page color is `#2e21de`; supporting text is `#9bbcfd`.

## Source behavior and adaptation

The desktop source has a centered 52px-high lavender navigation capsule, a 200vh hero with a sticky viewport, a 3.783-second introductory video, and a scroll-driven image sequence that brings its separated dashboard panels together. Below 1291px, the hero stops pinning; below 1024px navigation becomes a compact menu. The mobile source is 100svh, with 40px/44px title typography and the dashboard above readable text.

At the user's request, the FinAnalyzer hero displays only its headline, supporting text and scroll link. The Meta report animation, image layers and scroll pinning have been removed. Text is centered within one viewport on desktop and mobile, beneath the floating navigation.

The user-requested section order is shared by desktop and mobile: Clients, Benefits, Aggregated table, AI analysis, Calls, Pricing. The separate FinAnalyzer AI dashboard link and the brand's .AI suffix are removed. Mobile Menu opens a scrollable navigation sheet; selecting a destination, clicking outside or pressing Escape closes it. Search, sign-in and primary actions lead to the existing dashboard. Section anchors reserve space for the fixed header.

## Verification and remaining differences

Rendered source/local captures are saved in the workspace's `design-audit/clear-hero/` directory. Browser checks cover 320, 390, 1024, 1440 and 1920px widths, English and Portuguese, absence of hero media, no horizontal overflow, desktop/mobile menu behavior, Escape dismissal and section navigation. A production Webpack build passes.

The source dashboard animation is intentionally excluded at the user's request. Its Cookiebot, accessibility widget and promotional popup are outside this scope. Mobile checks use a Chromium browser with touch emulation, not a physical iPhone.
