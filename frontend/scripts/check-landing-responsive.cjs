// Run against a local preview with Playwright installed (or set PLAYWRIGHT_MODULE).
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.LANDING_URL || 'http://localhost:3012';

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_EXECUTABLE });
  try {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`${base}/en`);
    await page.locator('#landing-title').waitFor();
    await page.evaluate(() => document.fonts.ready);

    for (const [width, height] of [[320, 700], [390, 844], [1024, 768], [1920, 1080], [2560, 1440], [3840, 2160]]) {
      await page.setViewportSize({ width, height });
      await page.waitForTimeout(200);
      const geometry = await page.evaluate(() => {
        const title = document.querySelector('#landing-title');
        const nav = document.querySelector('nav');
        const hero = document.querySelector('section[aria-labelledby="landing-title"]');
        return {
          overflow: document.documentElement.scrollWidth > innerWidth,
          titleTop: title.getBoundingClientRect().top,
          navBottom: nav.getBoundingClientRect().bottom,
          navFits: nav.scrollWidth <= nav.clientWidth + 1,
          heroHeight: hero.getBoundingClientRect().height,
          font: parseFloat(getComputedStyle(title).fontSize),
        };
      });
      assert.equal(geometry.overflow, false, `${width}px: no horizontal overflow`);
      assert.ok(geometry.navFits, `${width}px: navigation fits`);
      assert.ok(geometry.titleTop > geometry.navBottom, `${width}px: header clears title`);
      assert.ok(geometry.heroHeight <= height + 1, `${width}px: marquee fits first screen`);
      if (width >= 2000) assert.ok(Math.abs(geometry.font - width * .032) < 1);
    }

    const marquee = page.getByRole('region', { name: 'What FinAnalyzer helps you do' });
    await marquee.scrollIntoViewIfNeeded();
    const track = marquee.locator('> div');
    const before = await track.evaluate(element => getComputedStyle(element).transform);
    await page.waitForTimeout(250);
    assert.notEqual(await track.evaluate(element => getComputedStyle(element).transform), before);
    assert.equal(await track.evaluate(element => getComputedStyle(element).animationDuration), '24s');
    assert.equal(await marquee.locator('ul:not([aria-hidden]) li').count(), 6);

    await page.setViewportSize({ width: 1920, height: 1080 });
    const story = page.locator('section[aria-label="From reports to understanding"]');
    const top = await story.evaluate(element => element.getBoundingClientRect().top + scrollY);
    await page.evaluate(y => scrollTo(0, y), top + 50);
    await page.waitForTimeout(400);
    await page.mouse.move(900, 500);
    const start = await page.evaluate(() => scrollY);
    await page.mouse.wheel(0, 600);
    await page.waitForTimeout(80);
    const early = await page.evaluate(() => scrollY);
    assert.ok(early > start && early < start + 600, 'wheel eases toward destination');
    await page.waitForTimeout(1200);
    assert.ok(Math.abs(await page.evaluate(() => scrollY) - start - 600) < 3, 'wheel travel stays 1:1');

    await page.goto(`${base}/pt`);
    await page.locator('#landing-title').waitFor();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('button', { name: 'Menu', exact: true }).click();
    await page.getByRole('link', { name: 'Benefícios', exact: true }).waitFor();
    await page.getByRole('button', { name: 'Fechar menu' }).press('Escape');
    assert.equal(await page.locator('#landing-mobile-menu').count(), 0);
    assert.equal(await page.evaluate(() => document.documentElement.classList.contains('lenis')), false);

    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.waitForTimeout(200);
    const staticTrack = page.getByRole('region', { name: 'Como o FinAnalyzer ajuda você' }).locator('> div');
    assert.equal(await staticTrack.evaluate(element => getComputedStyle(element).animationName), 'none');
    assert.equal(await staticTrack.locator('ul[aria-hidden="true"]').isVisible(), false);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    assert.deepEqual(errors, []);
    console.log('Landing checks passed: wide screens, mobile, marquee, wheel easing and reduced motion.');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
