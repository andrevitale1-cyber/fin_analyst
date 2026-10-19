# Clear Street hero symbols and mobile ticker

Reference inspected on 2026-10-19: https://www.clearstreet.io/ → existing local `/en` and `/pt` landing pages.

- The reference uses a duplicated horizontal list, a 24-second linear loop, and Rive canvas symbols rather than SVG icons. It remains a single moving row at 390px.
- `LandingIntro.tsx` / `LandingIntro.module.css` own the ticker; the existing navigation, copy and section order stay in place. `MarqueeSymbol.tsx` renders the actual six Rive assets, using the already installed canvas runtime and matching local WebAssembly.
- Original asset URLs are recorded in `public/reference/clearstreet/sources.json` as `marquee-1.riv` through `marquee-6.riv`. Together the assets occupy about 16KB. No production JavaScript from the reference is included.
- The user explicitly wants the ticker automatic on mobile. Reduced motion slows the loop to 48 seconds and freezes the decorative symbols; it must not turn the ticker into a swipe-only row or a wrapping list.
- Meta and Call previews use `TypingPreview.tsx`. The layout and accessible full text remain present while a decorative copy types at 24ms per character through a 700-character excerpt, then holds the complete analysis for seven seconds before looping. Playback runs only in view. Reading interaction reveals the complete text immediately; reduced motion skips typing.

Nike diagnosis: the request on 2026-10-19 ran from approximately 20:14:00Z to 20:17:04Z and returned HTTP 200. `NIKE` had not resolved to `NKE`, so the SEC source was absent. Previous logs did not record successful stage durations. The fix normalizes the issuer, asks for compact evidence and narrative without removing sections, and records research/cache/synthesis durations without logging source content or user identifiers. No live latency improvement is claimed without a fresh measured generation.
