import assert from 'node:assert/strict';
import { formatMetricValue, formatReportMoney } from './reportNumbers.ts';

assert.equal(formatMetricValue({ value: '331839000000', numeric_value: 331839000000, currency: 'USD', unit: 'currency' }, 'pt'), 'US$ 331,84 bi');
assert.equal(formatReportMoney(331839000000, 'USD', 'en'), 'USD 331.84B');
assert.equal(formatMetricValue({ value: '17.95', numeric_value: 17.95, currency: 'USD', unit: 'currency_per_share' }, 'pt'), 'US$ 17,95');
assert.equal(formatMetricValue({ value: '0', numeric_value: 0, unit: 'percent' }, 'pt'), '0%');
assert.equal(formatMetricValue({ value: '21.7', numeric_value: 21.7, unit: 'multiple' }, 'pt'), '21,7×');
assert.equal(formatReportMoney(-1250000000, 'BRL', 'pt'), 'R$ -1,25 bi');
assert.equal(formatMetricValue({ value: '331839000000' }, 'pt'), '331,84 bi');
assert.equal(formatMetricValue({ value: '$331.8 billion, up 17%' }, 'pt'), '$331.8 billion, up 17%');
assert.equal(formatMetricValue({ value: '17,95' }, 'en'), '17,95');
assert.equal(formatReportMoney(null, 'USD', 'pt'), '—');
assert.equal(formatReportMoney(Infinity, 'USD', 'en'), '—');
assert.equal(formatReportMoney(17.95, 'USD', 'pt', false), 'US$ 17,95');
assert.equal(formatReportMoney(0.000051, 'USD', 'pt'), 'US$ 0,000051');
console.log('Report number formatting checks passed.');
