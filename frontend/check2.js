const fs = require('fs');
let code = fs.readFileSync('app/page.tsx', 'utf8');

function count(str) {
  let b = 0, p = 0;
  // very naive string removal
  str = str.replace(/'[^']*'/g, '');
  str = str.replace(/"[^"]*"/g, '');
  str = str.replace(/`[^`]*`/g, '');
  for(let c of str) {
    if(c==='{') b++;
    if(c==='}') b--;
    if(c==='(') p++;
    if(c===')') p--;
  }
  return {b, p};
}

let fns = [
  'function TypewriterEffect',
  'function Feature',
  'function ScoreBadge',
  'function PhoneImage',
  'function ScoreDemo(',
  'function ScoreDemoMobile(',
  'function ComparadorMobile(',
  'function CallAnalysisDemo(',
  'function ReportDemo(',
  'function ReportDemoMobile(',
  'export default function LandingPage'
];

let positions = fns.map(f => ({name: f, idx: code.indexOf(f)})).filter(f => f.idx !== -1);
positions.sort((a,b) => a.idx - b.idx);

for(let i=0; i<positions.length; i++) {
  let start = positions[i].idx;
  let end = (i < positions.length - 1) ? positions[i+1].idx : code.length;
  let block = code.substring(start, end);
  let res = count(block);
  console.log(positions[i].name, res);
}
