# Clear Street solution scene → FinAnalyzer

Source: https://www.clearstreet.io/ (global-market video-container).
Destination: /en and /pt, AnalysisStory solution section.
Workflow: local design-reference-cloner/.agents/skills/clone-website/SKILL.md and its motion inspection guide.

## Observed implementation
Two prerendered MP4s, not CSS rectangles or a live 3D renderer. Intro plays once and hands off to a loop. Text is baked into the source clips. The live desktop container measured 1440 × 1440 at a 1440px viewport; videos use the entire square container.

- Intro: https://clearstreet.nyc3.cdn.digitaloceanspaces.com/clearstreet/2024-05-24T09-57-59.487Z-1.mp4
- Loop: https://clearstreet.nyc3.cdn.digitaloceanspaces.com/clearstreet/2024-05-24T09-58-12.854Z-2.mp4
- Local adapted media: frontend/public/benefits/finanalyzer-orbit-{intro,loop}.mp4

## Adaptation and limits
Preserve the motion, normalize pixel aspect ratio to a square, retouch the baked text in the center, and overlay accessible localized HTML copy. These are adapted reference videos, not a newly authored editable 3D scene. The central retouch loses the source detail beneath the original lettering. The public video resolution limits sharpness on large displays.

## Validation
Production webpack build and TypeScript passed. Browser tests at 1440×900 and 390×844 checked intro-to-loop handoff, mobile overflow, reduced-motion pause, and runtime errors. Captures: video-review/solution-desktop.png and solution-mobile.png. The local preview uses existing local authentication configuration; no production authentication change is included.
