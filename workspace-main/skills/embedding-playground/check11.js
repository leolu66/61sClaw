const fs = require('fs');
const h = fs.readFileSync('index.html', 'utf8');
const s = h.match(/<script>([\s\S]*?)<\/script>/)[1];

const start = s.indexOf('function renderModelCheckboxes');
const nextFunc = s.indexOf('function openModelModal');
const func = s.substring(start, nextFunc);

// Add balanced parens at end
let balance = 0;
for (const c of func) {
  if (c === '(') balance++;
  if (c === ')') balance--;
}
console.log('Paren balance:', balance);
console.log('Brace balance:', (() => { let b = 0; for (const c of func) { if (c === '{') b++; if (c === '}') b--; } return b; })());
console.log('Bracket balance:', (() => { let b = 0; for (const c of func) { if (c === '[') b++; if (c === ']') b--; } return b; })());

// Test with balanced closers
let pBal = 0, bBal = 0, brBal = 0;
for (const c of func) {
  if (c === '(') pBal++;
  if (c === ')') pBal--;
  if (c === '{') bBal++;
  if (c === '}') bBal--;
  if (c === '[') brBal++;
  if (c === ']') brBal--;
}

const closers = '}'.repeat(Math.max(0, bBal)) + ')'.repeat(Math.max(0, pBal));
console.log('Adding closers:', JSON.stringify(closers));

try {
  new Function('let models=[];function escapeHtml(t){return t}', func + closers);
  console.log('WITH CLOSERS: OK!');
} catch(e) {
  console.log('WITH CLOSERS still error:', e.message);
}

// Let me trace paren balance through the function
let depth = 0;
for (let i = 0; i < func.length; i++) {
  if (func[i] === '(') depth++;
  if (func[i] === ')') depth--;
  // Check if depth goes negative
  if (depth < 0) {
    console.log('PAREN GOES NEGATIVE at pos', i);
    console.log('Context:', func.substring(Math.max(0, i-30), i+10));
    break;
  }
}
console.log('Final depth:', depth);
