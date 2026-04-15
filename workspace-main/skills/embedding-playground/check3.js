const fs = require('fs');
const h = fs.readFileSync('index.html', 'utf8');
const s = h.match(/<script>([\s\S]*?)<\/script>/)[1];

// Find where paren balance becomes negative or track where the extra ( is
let balance = 0;
let maxImbalance = 0;
let maxPos = 0;
for (let i = 0; i < s.length; i++) {
  if (s[i] === '(') balance++;
  if (s[i] === ')') balance--;
  if (balance > maxImbalance) {
    maxImbalance = balance;
    maxPos = i;
  }
}

// Also track balance at each function boundary
let pos = 0;
let lastGoodPos = 0;
balance = 0;
for (let i = 0; i < s.length; i++) {
  if (s[i] === '(') balance++;
  if (s[i] === ')') balance--;
  
  // Check if remaining code after this position has balance 0
  let remaining = balance;
  for (let j = i + 1; j < s.length; j++) {
    if (s[j] === '(') remaining++;
    if (s[j] === ')') remaining--;
  }
  
  if (remaining === -1) {
    // The extra ( is somewhere before position i
    console.log('Extra ( is before pos', i, 'context:', s.substring(Math.max(0,i-80), i+20));
    break;
  }
}

// Try adding ) at various positions
// The missing ) is likely in renderModelsTable or renderModelCheckboxes
// Let's check each function
const funcs = s.split('function ');
for (let i = 1; i < funcs.length; i++) {
  const code = 'function ' + funcs[i];
  // Extract until balanced braces
  let braces = 0;
  let started = false;
  let end = 0;
  for (let j = 0; j < code.length; j++) {
    if (code[j] === '{') { braces++; started = true; }
    if (code[j] === '}') braces--;
    if (started && braces === 0) { end = j; break; }
  }
  const funcBody = code.substring(0, end + 1);
  try {
    new Function(funcBody);
  } catch(e) {
    const name = funcBody.substring(9, funcBody.indexOf('('));
    console.log('Function error:', name, '-', e.message);
    console.log('  First 100 chars:', funcBody.substring(0, 100));
  }
}
