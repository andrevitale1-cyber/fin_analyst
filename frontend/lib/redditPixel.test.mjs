import assert from 'node:assert/strict';
import { hashRedditEmail, trackRedditVisit } from './redditPixel.ts';

const scripts = [];
globalThis.window = { location: { hostname: 'localhost' } };
globalThis.document = { createElement: () => ({}), head: { appendChild: script => scripts.push(script) } };
trackRedditVisit('/pt');
assert.equal(scripts.length, 0, 'Development and previews must not pollute ad measurements');
window.location.hostname = 'finanalyser.com.br';
const hash = await hashRedditEmail('  TEST@EXAMPLE.COM ');
assert.equal(hash, '973dfe463ec85785f5f95af5ba3906eedb2d931c24e69824a89ea65dba4e813b');
assert.equal(await hashRedditEmail(), undefined);
trackRedditVisit('/pt', hash);
trackRedditVisit('/pt', hash);
trackRedditVisit('/pt/dashboard', hash);
trackRedditVisit('/pt/dashboard', hash);
trackRedditVisit('/en', 'raw@example.com');
assert.equal(scripts.length, 1, 'Vendor script must load once across navigation');
assert.equal(scripts[0].src, 'https://www.redditstatic.com/ads/pixel.js?pixel_id=a2_jzugsawslzp2');
assert.deepEqual(window.rdt.callQueue, [
  ['init', 'a2_jzugsawslzp2'],
  ['track', 'PageVisit', { email: hash }],
  ['track', 'PageVisit', { email: hash }],
  ['track', 'PageVisit', {}],
]);
assert.equal(JSON.stringify(window.rdt.callQueue).includes('example.com'), false);
trackRedditVisit('/pt');
assert.equal(window.rdt.callQueue.length, 5, 'Returning to a previous page is a new visit');
console.log('Reddit Pixel: hashed email, single initialization, route visits and duplicate protection passed.');
