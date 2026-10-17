# Clear Street hero and navigation

Source: https://www.clearstreet.io/ — inspected live through the adjacent `design-reference-cloner/.agents/skills/clone-website` workflow on October 13, 2026.

Destination: the existing FinAnalyzer `/en` and `/pt` homepages. Local preview: http://localhost:3012/en.

## Ownership and references

- `components/LandingIntro.tsx` and its CSS own the floating navigation, ordered desktop links, mobile menu, static hero and benefits marquee. The component owns and cleans up the landing's wheel smoothing.
- `app/[locale]/page.tsx` replaces the previous navigation/hero with this component. Remaining authored sections are preserved.
- The existing local Reyhan regular/medium fonts from Clear Street are reused. The page color is `#2e21de`; supporting text is `#9bbcfd`.

## Source behavior and adaptation

The desktop source has a centered 52px-high lavender navigation capsule, a 200vh hero with a sticky viewport, a 3.783-second introductory video, and a scroll-driven image sequence that brings its separated dashboard panels together. Below 1291px, the hero stops pinning; below 1024px navigation becomes a compact menu. The mobile source is 100svh, with 40px/44px title typography and the dashboard above readable text.

The Meta report animation, image layers and hero pinning remain excluded at the user's request. Text is centered beneath the floating navigation. The hero now includes a looping benefits strip and fits one viewport without using CSS zoom or scaling the page with transforms.

## Responsive and motion update — October 17, 2026

The Clear Street source was inspected again through the clone command and its motion guide. Above 2000 CSS pixels, it switches to viewport-based typography: the hero and Reasons headings use `3.2vw`. FinAnalyzer now follows that rule for its hero and story titles, and scales supporting text, header spacing, icons and the adjacent solution section proportionally. This covers wide monitors and the expanded CSS viewport produced by reducing browser zoom. Below that boundary the existing desktop/mobile typography remains.

The source's statistics-loop uses two equal content groups with a linear 24-second cycle and a `translateX(-50%)` endpoint. The local marquee uses that geometry with user-approved mixed content: a benefit followed by the corresponding feature. It uses real capabilities rather than invented client numbers or time-saving statistics. Its second group is hidden from assistive technology; reduced-motion users get a static wrapping list. Offscreen animation pauses.

The source's Reasons section retains three 100vh title panels, the sinusoidal overlay fade and its CustomEase title curve. Its global scroller uses Lenis 1.1.13, `lerp: 0.1`, `wheelMultiplier: 1`, `smoothWheel: true`, `syncTouch: false`, synchronized with GSAP. FinAnalyzer uses the same library and wheel parameters on fine-pointer desktop devices. Mobile and reduced-motion scrolling remain native. The two report previews opt out so their own scroll areas still work. Cleanup removes the wheel handler and GSAP callback when leaving the landing or changing device/motion preferences.

The user-requested section order is shared by desktop and mobile: Clients, Benefits, Aggregated table, AI analysis, Calls, Pricing. The separate FinAnalyzer AI dashboard link and the brand's .AI suffix are removed. Mobile Menu opens a scrollable navigation sheet; selecting a destination, clicking outside or pressing Escape closes it. Search, sign-in and primary actions lead to the existing dashboard. Section anchors reserve space for the fixed header.

## Verification and remaining differences

Current captures and measurements are in `smoke-output/clear-responsive/`; earlier captures remain in `design-audit/clear-hero/`. Checks cover 320, 390, 1024, 1440, 1920, 2560 and 3840px CSS viewports, English/Portuguese, no horizontal overflow, marquee movement, mobile menu/Escape, native mobile scrolling and reduced motion. The measured local 600px wheel gesture eases toward its destination and finishes at 600px. Videos were checked during forward/reverse scene changes, and the nested Meta preview scrolls without moving the page.

Repeatable smoke check: `node scripts/check-landing-responsive.cjs` from `frontend`, against a running local preview with Playwright available. Set `LANDING_URL`, `PLAYWRIGHT_MODULE` or `CHROMIUM_EXECUTABLE` if using a different host or bundled browser runtime.

The source dashboard animation is intentionally excluded at the user's request. Its Cookiebot, accessibility widget and promotional popup are outside this scope. Direct wheel timing on the reference remained blocked in the automated browser; matching is based on the inspected public source parameters, not a claimed identical timing trace. Mobile checks use Chromium viewport emulation, not a physical iPhone.
