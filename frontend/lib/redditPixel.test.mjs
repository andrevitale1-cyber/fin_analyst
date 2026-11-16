import assert from 'node:assert/strict';
import { hashRedditEmail, requestRedditGetStarted, signupConversionId, trackRedditConversion, trackRedditVisit } from './redditPixel.ts';

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
const storage = new Map();
globalThis.localStorage = {getItem:key=>storage.get(key),setItem:(key,value)=>storage.set(key,value)};
window.location.pathname = '/pt';
assert.equal(await signupConversionId('user_old', Date.parse('2026-01-01')),undefined);
assert.equal(await signupConversionId('user_future', Date.now()+100000),undefined);
const signupId = await signupConversionId('user_new',Date.parse('2026-11-16T00:10:00Z'));
assert.equal(signupId.length,64);
const before = window.rdt.callQueue.length;
trackRedditConversion('SignUp',{conversionId:signupId},hash);
trackRedditConversion('SignUp',{conversionId:signupId},hash);
trackRedditConversion('Purchase',{conversionId:'a'.repeat(64),value:29,currency:'BRL'},hash);
trackRedditConversion('Purchase',{conversionId:'a'.repeat(64),value:29,currency:'BRL'},hash);
trackRedditConversion('Purchase',{conversionId:'b'.repeat(64),value:0,currency:'BRL'},hash);
trackRedditConversion('Purchase',{conversionId:'c'.repeat(64),value:29,currency:'USD'},hash);
assert.equal(window.rdt.callQueue.length,before+2);
assert.equal(storage.size,2);
assert.deepEqual(window.rdt.callQueue.at(-1),['track','Purchase',{conversionId:'a'.repeat(64),value:29,currency:'BRL',email:hash}]);
console.log('New-user-only signup, confirmed payment payloads and conversion deduplication passed.');
console.log('Reddit Pixel: hashed email, single initialization, route visits and duplicate protection passed.');

const requests = [];
globalThis.fetch = async (url, options) => {requests.push({url, body:JSON.parse(options.body), keepalive:options.keepalive}); return {ok:true};};
requestRedditGetStarted();
await new Promise(resolve => setTimeout(resolve, 30));
assert.equal(requests.length,1);
assert.equal(requests[0].body.event,'AddToCart');
assert.equal(requests[0].keepalive,true);
const cart = window.rdt.callQueue.at(-1);
assert.equal(cart[1],'AddToCart');
const expectedHash = await crypto.subtle.digest('SHA-256',new TextEncoder().encode('reddit-click:'+requests[0].body.event_id));
assert.equal(cart[2].conversionId,Array.from(new Uint8Array(expectedHash),b=>b.toString(16).padStart(2,'0')).join(''));
