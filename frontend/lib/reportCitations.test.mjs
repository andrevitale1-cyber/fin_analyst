import assert from 'node:assert/strict';
import { reportCitationIds, stripReportCitations } from './reportCitations.ts';

const sources = [{ id: 'S10' }, { id: 'F1' }, { id: 'company-source' }];
assert.equal(stripReportCitations('**Revenue up 26%**[S10][F1].', sources), '**Revenue up 26%**.');
assert.equal(stripReportCitations('Buy [1, 2]; strong outlook [company-source].', sources), 'Buy; strong outlook.');
assert.deepEqual(reportCitationIds('Growth[S10][S10], cash[F1], price[3]', sources), ['S10', 'F1', 'company-source']);
assert.equal(stripReportCitations('Outlook [2026] [unaudited] and $10 [S999].', sources), 'Outlook [2026] [unaudited] and $10.');
assert.deepEqual(reportCitationIds('No sources [S999]', sources), []);
console.log('Report citation checks passed.');
