const fs = require('fs');
let bak = fs.readFileSync('app/page.bak.tsx', 'utf8');
fs.writeFileSync('app/page.tsx', bak);

function findUnbalanced(str, startLine) {
  let b = 0, p = 0;
  let lines = str.split('\n');
  for(let i=0; i<lines.length; i++) {
     // Naive string removal that won't break on quotes
     let l = lines[i].replace(/'[^']*'/g, '').replace(/"[^"]*"/g, '').replace(/`[^`]*`/g, '');
     for(let c of l) {
       if (c==='{') b++;
       if (c==='}') b--;
       if (c==='(') p++;
       if (c===')') p--;
     }
     if (b < 0) return {line: i + startLine, char: '}'};
     if (p < 0) return {line: i + startLine, char: ')'};
  }
  return { b, p };
}

let reportDemoStart = bak.indexOf('function ReportDemo()');
let reportDemoEnd = bak.indexOf('function ReportDemoMobile()');
let sub1 = bak.substring(reportDemoStart, reportDemoEnd);
let lineStart1 = bak.substring(0, reportDemoStart).split('\n').length;
console.log('ReportDemo:', findUnbalanced(sub1, lineStart1));

let landingPageStart = bak.indexOf('export default function LandingPage');
let sub2 = bak.substring(reportDemoEnd, landingPageStart);
let lineStart2 = bak.substring(0, reportDemoEnd).split('\n').length;
console.log('ReportDemoMobile:', findUnbalanced(sub2, lineStart2));
