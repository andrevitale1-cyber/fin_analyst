import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import * as numbers from './reportNumbers.ts';
const require = createRequire(import.meta.url);
const ts = require('typescript');
const source = readFileSync(new URL('./reportBreakdowns.ts', import.meta.url), 'utf8');
const js = ts.transpileModule(source, {compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
const module = {exports:{}};
new Function('require', 'module', 'exports', js)(() => numbers, module, module.exports);
const {prepareBreakdowns, breakdownValue} = module.exports;

const geography = [
  { category: 'geography', label: 'Estados Unidos (2026)', value: 'US$ 170.794.000.000', share: 0.515, source_id: 'F1' },
  { category: 'geography', label: 'Outros países (2026)', value: 'US$ 161.045.000.000', share: 0.485, source_id: 'F1' },
];
const history = [{ period: '2026', currency: 'USD', revenue: 331839000000 }];
assert.deepEqual(prepareBreakdowns(geography, history).map(row => row.share), [51.5, 48.5]);
assert.equal(breakdownValue(geography[0], 'pt'), 'US$ 170,79 bi');
assert.equal(prepareBreakdowns([geography[0]], history)[0].share, 0.515);
assert.deepEqual(prepareBreakdowns(geography, [{...history[0],currency:'BRL'}]).map(row=>row.share), [0.515,0.485]);
assert.deepEqual(prepareBreakdowns(geography, [{...history[0],period:'2025'}]).map(row=>row.share), [0.515,0.485]);
assert.deepEqual(prepareBreakdowns(geography).map(row=>row.share), [0.515,0.485]);
assert.deepEqual(prepareBreakdowns(geography.map(row=>({...row,share:row.share*100})), history).map(row=>row.share), [51.5,48.5]);
assert.deepEqual(prepareBreakdowns(geography.map(row=>({...row,group_complete:true,period:'2026'}))).map(row=>row.share), [51.5,48.5]);
assert.equal(breakdownValue({...geography[0],value:'USD 170.79 billion'}, 'pt'), 'USD 170.79 billion');
console.log('Geography fraction, currency, period and display checks passed.');
