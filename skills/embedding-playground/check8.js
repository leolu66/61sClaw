const fs = require('fs');
const h = fs.readFileSync('index.html', 'utf8');
const s = h.match(/<script>([\s\S]*?)<\/script>/)[1];

// The split approach doesn't work well. Let me try binary search on position.
function testCode(code) {
  try { new Function(code); return true; } catch(e) { return false; }
}

// First confirm: full code fails
console.log('Full code OK:', testCode(s));

// Find the position where it first breaks
// Try removing functions from the end
const funcStarts = [];
let idx = 0;
while ((idx = s.indexOf('function ', idx + 1)) !== -1) {
  funcStarts.push(idx);
}
console.log('Functions found:', funcStarts.length);

// Test code up to each function start
for (let i = funcStarts.length - 1; i >= 0; i--) {
  const prefix = s.substring(0, funcStarts[i]);
  // Need to close any open braces/parens
  // Add closing chars
  let closers = '';
  let parens = 0, braces = 0;
  for (const c of prefix) {
    if (c === '(') parens++;
    if (c === ')') parens--;
    if (c === '{') braces++;
    if (c === '}') braces--;
  }
  closers += ')'.repeat(Math.max(0, parens));
  closers += '}'.repeat(Math.max(0, braces));
  
  if (testCode(prefix + closers)) {
    console.log('Code OK up to function at pos', funcStarts[i]);
    // Show what function starts there
    console.log('  Function:', s.substring(funcStarts[i], funcStarts[i] + 60));
    
    // Now find the error within this function
    // Find next function start
    const nextStart = funcStarts[i + 1] || s.length;
    const funcCode = s.substring(funcStarts[i], nextStart);
    console.log('  Error is in this function, length:', funcCode.length);
    
    // Test the function alone
    try {
      new Function(funcCode);
      console.log('  Function alone: OK (error is in interaction)');
    } catch(e) {
      console.log('  Function alone ERROR:', e.message);
    }
    break;
  }
}
