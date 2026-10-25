import assert from 'node:assert/strict';
import { publishedReportsForLocale, publishedReportForCompany } from './publishedReports.ts';

for (const locale of ['pt', 'en']) {
  const reports = publishedReportsForLocale(locale);
  assert.deepEqual(reports.map(r => r.company), ['NVDA', 'AAPL']);
  assert.equal(reports[0].locale, locale);
  assert.equal(reports[0].is_public, true);
  assert.equal(reports[0].score, 5);
  assert.equal(reports[1].score, 4);
  assert.equal(reports[1].is_public, true);
  assert.equal(reports[1].locale, locale);
  assert.equal(reports[1].url, `/published-reports/aapl-20261022${locale === 'en' ? '-en' : ''}.html`);
  assert.equal(reports[0].url, `/published-reports/nvda-20261022${locale === 'en' ? '-en' : ''}.html`);
  for (const name of ['NVDA', 'NVIDIA', 'NVIDIA Corporation']) {
    assert.equal(publishedReportForCompany(name, locale)?.id, reports[0].id);
  }
  for (const name of ['AAPL', 'Apple', 'Apple Inc.']) assert.equal(publishedReportForCompany(name, locale)?.id, reports[1].id);
  for (const retired of ['MSFT', 'PETR4', 'NKE']) assert.equal(publishedReportForCompany(retired, locale), undefined);
}
console.log('Apple and NVIDIA are public; both languages, aliases and revised scores resolve.');
