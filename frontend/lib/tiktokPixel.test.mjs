import assert from 'node:assert/strict';
import vm from 'node:vm';
import { TIKTOK_BOOTSTRAP, TIKTOK_PIXEL_ID, trackTikTokVisit } from './tiktokPixel.ts';

const scripts = [];
const browser = { location: { hostname: 'localhost' } };
const document = {
  createElement: () => ({}),
  getElementsByTagName: () => [{ parentNode: { insertBefore: script => scripts.push(script) } }],
};
vm.runInNewContext(TIKTOK_BOOTSTRAP, { window: browser, document });
assert.equal(scripts.length, 1);
assert.equal(scripts[0].src, `https://analytics.tiktok.com/i18n/pixel/events.js?sdkid=${TIKTOK_PIXEL_ID}&lib=ttq`);
assert.equal(scripts[0].async, true);
assert.equal(browser.ttq.length, 0, 'Bootstrap must not double-count initial visits');
globalThis.window = browser;
trackTikTokVisit('/pt');
assert.equal(browser.ttq.length, 0, 'Local and preview traffic must not be tracked');
browser.location.hostname = 'finanalyser.com.br';
trackTikTokVisit('/pt');
trackTikTokVisit('/pt');
trackTikTokVisit('/en');
trackTikTokVisit('/en');
trackTikTokVisit('/pt');
assert.deepEqual(Array.from(browser.ttq, event => Array.from(event)), [['page'], ['page'], ['page']]);
assert.equal(scripts.length, 1, 'Navigation must reuse the vendor script');
assert.equal(JSON.stringify(browser.ttq).includes('identify'), false, 'No personal matching data is sent');
console.log('TikTok Pixel: official bootstrap, correct ID, page visits, route deduplication and no identification passed.');
