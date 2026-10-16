import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import * as numbers from './reportNumbers.ts';
const require = createRequire(import.meta.url);
const ts = require('typescript');
const source = readFileSync(new URL('./reportBreakdowns.ts', import.meta.url), 'utf8');
const js = ts.transpileModule(source, {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const module = {exports:{}};
new Function('require', 'module', 'exports', js)(() => numbers, module, module.exports);
const {prepareBreakdowns, breakdownValue, selectSegmentBreakdowns} = module.exports;

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

const segments = [
  {category:'segment',label:'Compute & Networking (FY 2026)',value:'USD 193480000000',share:89.6,source_id:'S1'},
  {category:'segment',label:'Graphics (FY 2026)',value:'USD 22460000000',share:10.4,source_id:'S1'},
  {category:'segment',label:'Data Center (platform, FY 2026)',value:'USD 193700000000',share:89.7,source_id:'S2'},
  {category:'segment',label:'Gaming (platform, FY 2026)',value:'USD 16000000000',share:7.41,source_id:'S2'},
];
assert.deepEqual(selectSegmentBreakdowns(segments).map(row=>row.share),[89.6,10.4], 'never add product-platform revenue to operating segments');
assert.equal(selectSegmentBreakdowns([...segments, {...segments[0],label:' compute and NETWORKING (FY 2026) ',source_id:'S2'}]).length,2,'deduplicate case, whitespace and punctuation variants across sources');
assert.equal(selectSegmentBreakdowns(segments.slice(2)).length,2,'retain a platform breakdown when it is the only perspective');
assert.equal(selectSegmentBreakdowns(geography).length,0);
assert.equal(selectSegmentBreakdowns([{...segments[0], label:'Platform Solutions'}, segments[1]]).length,2,'a segment named Platform Solutions is not an overlapping-platform qualifier');
assert.equal(selectSegmentBreakdowns(segments).reduce((sum,row)=>sum+row.share,0),100);
assert.equal(segments.length,4,'do not mutate cached report data');
console.log('Segment duplicate and overlapping-perspective checks passed.');
