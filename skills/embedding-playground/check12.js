const fs = require('fs');
const h = fs.readFileSync('index.html', 'utf8');
const s = h.match(/<script>([\s\S]*?)<\/script>/)[1];

const start = s.indexOf('function renderModelCheckboxes');
const nextFunc = s.indexOf('function openModelModal');
const func = s.substring(start, nextFunc);

// Track parens, skipping template literals and strings
let depth = 0;
let inSingleQuote = false;
let inDoubleQuote = false;
let inBacktick = false;

for (let i = 0; i < func.length; i++) {
  const c = func[i];
  const prev = i > 0 ? func[i-1] : '';
  
  if (prev === '\\') continue; // skip escaped chars
  
  if (!inBacktick && !inSingleQuote && !inDoubleQuote) {
    if (c === "'") { inSingleQuote = true; continue; }
    if (c === '"') { inDoubleQuote = true; continue; }
    if (c === '`') { inBacktick = true; continue; }
    if (c === '(') { depth++; continue; }
    if (c === ')') { depth--; continue; }
  } else if (inSingleQuote) {
    if (c === "'") { inSingleQuote = false; }
  } else if (inDoubleQuote) {
    if (c === '"') { inDoubleQuote = false; }
  } else if (inBacktick) {
    if (c === '`') { inBacktick = false; }
    // Inside template literal, ${...} contains expressions
    if (c === '$' && func[i+1] === '{') {
      // Track nested braces for template expressions
      let braceDepth = 0;
      let j = i + 2;
      for (; j < func.length; j++) {
        if (func[j] === '{') braceDepth++;
        if (func[j] === '}') {
          if (braceDepth === 0) break;
          braceDepth--;
        }
        // Count parens inside template expressions too
        if (func[j] === '(') depth++;
        if (func[j] === ')') depth--;
        if (depth < 0) {
          console.log('NEGATIVE inside template expr at', j, ':', func.substring(Math.max(0,j-20), j+20));
        }
      }
      i = j; // skip past the }
      continue;
    }
  }
}

console.log('Final paren depth:', depth);
console.log('States - sq:', inSingleQuote, 'dq:', inDoubleQuote, 'bt:', inBacktick);
