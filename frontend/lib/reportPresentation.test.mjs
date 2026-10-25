import assert from 'node:assert/strict';
import { analystTargetsOnly } from './reportPresentation.ts';

const input = {
  sections: [
    { id: 'valuation', summary: 'Our fair value is $100.', paragraphs: [], bullets: [] },
    { id: 'sentiment', summary: 'Analysts target $220.', paragraphs: ['Analysts target $220.', 'The DCF implies $100.'], bullets: ['Source observed 2026-10-22.'] },
    { id: 'financials', summary: 'FCF is $50 billion.', paragraphs: [], bullets: [] },
  ],
  signals: [{ id: 'valuation', value: 'Overvalued' }, { id: 'growth', value: 'Strong' }],
  metrics: [{ label: 'Fair value', value: '$100' }, { label: 'Reported EPS', value: '$5' }],
  watchpoints: ['WACC sensitivity', 'Cash conversion'],
  analyst_consensus: { target_mean: 220, currency: 'USD', as_of: '2026-10-22', source_ids: ['S1'] },
};
const original = structuredClone(input);
const result = analystTargetsOnly(input);
assert.deepEqual(input, original, 'Saved reports must not be mutated');
assert.deepEqual(result.sections.map(s => s.id), ['sentiment', 'financials']);
assert.deepEqual(result.sections[0].paragraphs, ['Analysts target $220.']);
assert.equal(result.sections[1].summary, 'FCF is $50 billion.');
assert.deepEqual(result.analyst_consensus, input.analyst_consensus);
assert.deepEqual(result.metrics.map(m => m.label), ['Reported EPS']);
assert.deepEqual(result.watchpoints, ['Cash conversion']);
assert.deepEqual(result.signals.map(s => s.id), ['growth']);
console.log('Analyst targets retained; proprietary valuation hidden; source data unchanged.');
