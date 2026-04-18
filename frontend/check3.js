const fs = require('fs');
let code = fs.readFileSync('app/page.tsx', 'utf8');

function count(str) {
  let b = 0, p = 0;
  str = str.replace(/'[^']*'/g, '').replace(/"[^"]*"/g, '').replace(/`[^`]*`/g, '');
  for(let c of str) {
    if(c==='{') b++;
    if(c==='}') b--;
    if(c==='(') p++;
    if(c===')') p--;
  }
  return {b, p};
}

let start = code.indexOf('function ReportDemo(');
let end = code.indexOf('function ReportDemoMobile(');
let rd = code.substring(start, end);

let lines = rd.split('\n');
let totalB = 0;
let totalP = 0;

for(let i=0; i<lines.length; i++) {
  let c = count(lines[i]);
  totalB += c.b;
  totalP += c.p;
  if(totalB < 0 || totalP < 0 || (totalB > 0 && totalB > 20)) {
     // print something interesting
  }
}

// Find the line where the mismatch actually is by looking at the diff between start and end.
// We know it ends with { b: 2, p: 1 }. This means 2 opening braces and 1 opening paren were NEVER closed.
console.log('Unclosed braces:', totalB, 'Unclosed parens:', totalP);

for(let i=0; i<lines.length; i++) {
  let c = count(lines[i]);
  if (c.b !== 0 || c.p !== 0) {
     console.log('Line ' + (i+573) + ': b=' + c.b + ', p=' + c.p + '  | ' + lines[i].trim().substring(0, 50));
  }
}
