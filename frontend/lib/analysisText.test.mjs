import assert from 'node:assert/strict';
import { formatPeriod, splitBold } from './analysisText.ts';
assert.equal(formatPeriod('2T/2026', 'en'), '2Q/2026');
assert.equal(formatPeriod('1Q/2025', 'pt'), '1T/2025');
assert.equal(formatPeriod(null, 'en'), '');
assert.equal(formatPeriod('2026', 'en'), '2026');
assert.deepEqual(splitBold('Before **Growth\ncontinued** after **Margins**.'), [
  {text:'Before ',bold:false}, {text:'Growth\ncontinued',bold:true},
  {text:' after ',bold:false}, {text:'Margins',bold:true}, {text:'.',bold:false},
]);
assert.deepEqual(splitBold('**unfinished'), [{text:'**unfinished',bold:false}]);
assert.equal(splitBold('**<script>alert(1)</script>**')[1].text, '<script>alert(1)</script>');
console.log('Period and bold formatting checks passed.');
