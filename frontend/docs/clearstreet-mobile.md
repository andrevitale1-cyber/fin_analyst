# Clear Street mobile reference

Source: https://www.clearstreet.io/ — the Vectors cards and Reasons video section. Inspected through the clone-website workflow in the adjacent design-reference-cloner repository, the source's rendered mobile DOM/CSS/JavaScript, and the supplied iPhone recordings.

Local routes: `/en` and `/pt`. Preview: `http://localhost:3012/en`.

## Implementation ownership

- `components/AnalysisStory.tsx` and its CSS: sticky video grid, three scrolling title panels, video activation, fades and explicit text layering.
- `components/AudienceCards.tsx` and its CSS: native looping Clients video; existing Services Rive animation.
- `components/SearchBenefit.tsx`: first feature-card video.
- `components/useVideoPlayback.ts`: visible-card playback and trusted touch-start retries.
- `public/reference/clearstreet/sources.json`: existing media origin map.

## Reference behavior

The original uses GSAP ScrollTrigger, a sticky grid of 100vh, and 100vh title panels. Enter/enter-back triggers select a video and call play; scroll progress drives the sinusoidal overlay fade. The title has its own scrub trigger and the source CustomEase curve. At 390px width, the measured title width is 263.75px and font size is 28px.

The local section uses the same mechanism and original mobile MP4 assets, with muted inline playback and the first-frame media fragment. Captions are ordinary readable HTML before animation initialization, with an explicit layer above the video grid. Animated WebP replacements and mobile source exclusions have been removed.

The feature-card recording was 200 fps. Its replacement is H.264 Constrained Baseline, 1280×720, 30 fps, no audio and faststart. Duration is 7 seconds (15ms shorter than the former file after frame-rate conversion).

## Validation

Mobile browser checks verify visible captions, changing video pixels, active scene selection, and both card videos restarting at the end. Native video playback requires a physical iPhone check to confirm Safari-specific hardware behavior; desktop Chromium with an iPhone viewport is not that confirmation.
