import assert from 'node:assert/strict';
import { companyLogoSources } from './companyLogos.ts';

assert.equal(companyLogoSources('WEGE3')[0], '/benefits/company-logos/WEGE3.SA.webp');
assert.equal(companyLogoSources('WEGE3.SA')[0], companyLogoSources('WEGE3')[0]);
assert.equal(companyLogoSources(null, 'WEG S.A.')[0], companyLogoSources('WEGE3')[0]);
assert.equal(companyLogoSources('CAVA')[0], 'https://financialmodelingprep.com/image-stock/CAVA.png');
assert.equal(companyLogoSources(null, 'Apple Inc.')[0], companyLogoSources('AAPL')[0]);
assert.equal(companyLogoSources('GOOGL')[0], companyLogoSources('GOOG')[0]);
assert.equal(companyLogoSources('BRK.B')[0], companyLogoSources('BRK-B')[0]);
assert.equal(companyLogoSources('NYSE: DIS')[0], 'https://financialmodelingprep.com/image-stock/DIS.png');
assert.equal(companyLogoSources('RENT3').at(-1), 'https://financialmodelingprep.com/image-stock/RENT3.SA.png');
assert.equal(companyLogoSources(null, 'Adobe Inc. (ADBE)')[0], 'https://financialmodelingprep.com/image-stock/ADBE.png');
assert.deepEqual(companyLogoSources('https://untrusted.example/logo'), []);
assert.deepEqual(companyLogoSources('../secret'), []);
assert.deepEqual(companyLogoSources(null, ''), []);
console.log('Company logo identity and fallback checks passed.');
