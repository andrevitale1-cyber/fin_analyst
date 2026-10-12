# Finup account section adapted to the aggregated table

Source: https://www.finup.io/en, section `section.account` / “Manage all your payments in one account”. Destination: FinAnalyzer `/en` and `/pt`, AggregatedTableSection.tsx and its CSS module.

Inspected with the workflow in design-reference-cloner/.agents/skills/clone-website/SKILL.md. Desktop 1440px: section padding 200px, navy body #0a0a1f, title 56px/58.8px, description 400px wide, preview margin 80px, dashboard frame 860px wide, radius 24px, border white at 20% opacity, radial white fill 15% to 5%, screen inset 24px. Frame filter drop-shadow(0 0 80px rgba(26,26,255,.5)); blue rectangle behind screen #1a1aff, max 720x440px. Heading accent gradient 225deg #4b93ff to #9dd0ff.

Mobile 390px: section vertical padding about 92px, title about 30px, preview gap 32px, frame radius 10px, screen inset about 10px. The table scrolls horizontally rather than shrinking its text to an unreadable size.

Adaptations: FinAnalyzer heading and description; live HTML table instead of Finup's account screenshot; controls and saved screenshot values preserved; CTA goes to the local dashboard. Finup's floating payment and bank-card overlays are not included because the requested content is the table frame and background.

Reference captures: video-review/finup-account-section.png and finup-account-mobile.png. Local captures: video-review/table-framed-desktop.png and table-framed-mobile.png. Scratch captures are not published with the app.
