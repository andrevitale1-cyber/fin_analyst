import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';
import { TIKTOK_BOOTSTRAP, TIKTOK_PIXEL_ID, trackTikTokVisit, trackTikTokConversion } from './tiktokPixel.ts';

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
trackTikTokConversion('InitiateCheckout', 'same-occurrence', {currency:'BRL', value:29});
trackTikTokConversion('InitiateCheckout', 'same-occurrence', {currency:'BRL', value:29});
const tracks = browser.ttq.filter(event => event[0] === 'track');
assert.equal(tracks.length, 1);
assert.equal(tracks[0][3].event_id, 'same-occurrence');
assert.equal(tracks[0][2].value, 29);
const reportPixel = readFileSync(new URL('../public/tiktok-public-report.js', import.meta.url), 'utf8');
const publicBrowser = {};
const calls = [];
vm.runInNewContext(reportPixel, {window: publicBrowser, document, location: {hostname:'finanalyser.com.br'},
  crypto: {randomUUID:()=> 'public-occurrence'}, fetch:(url,options)=>{calls.push(JSON.parse(options.body));return Promise.resolve({ok:true});}});
const reportEvent = publicBrowser.ttq.find(event => event[0] === 'track');
assert.equal(reportEvent[1], 'ViewContent');
assert.equal(reportEvent[3].event_id, calls[0].event_id);
assert.equal(calls[0].content, 'public_report');
for (const name of ['aapl-20261022','aapl-20261022-en','nvda-20261022','nvda-20261022-en']) {
  assert.equal(readFileSync(new URL(`../public/published-reports/${name}.html`, import.meta.url),'utf8').split('/tiktok-public-report.js').length, 2);
}
