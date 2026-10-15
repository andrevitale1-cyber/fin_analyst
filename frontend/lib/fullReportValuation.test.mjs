import assert from 'node:assert/strict';
import { calculateIllustrativeValue } from './fullReportValuation.ts';

assert.equal(calculateIllustrativeValue(10, { growthPercent: 0, peMultiple: 10, discountPercent: 0 }), 100);
assert.ok(Math.abs(calculateIllustrativeValue(10, { growthPercent: 10, peMultiple: 15, discountPercent: 10 }) - 150) < 1e-10);
assert.equal(calculateIllustrativeValue(10, { growthPercent: -50, peMultiple: 10, discountPercent: 0 }), 3.125);
assert.equal(calculateIllustrativeValue(0, { growthPercent: 10, peMultiple: 15, discountPercent: 10 }), null);
assert.equal(calculateIllustrativeValue(10, { growthPercent: 101, peMultiple: 15, discountPercent: 10 }), null);
assert.equal(calculateIllustrativeValue(10, { growthPercent: 10, peMultiple: 0, discountPercent: 10 }), null);
assert.equal(calculateIllustrativeValue(10, { growthPercent: 10, peMultiple: 15, discountPercent: 51 }), null);
console.log('Illustrative valuation calculation checks passed.');
