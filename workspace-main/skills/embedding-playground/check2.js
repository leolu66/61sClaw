const fs = require('fs');
const h = fs.readFileSync('index.html', 'utf8');
const s = h.match(/<script>([\s\S]*?)<\/script>/)[1];

// Try adding closing brackets until it parses
for (let extra = 0; extra <= 5; extra++) {
  const suffix = ')'.repeat(extra);
  try {
    new Function(s + suffix);
    console.log('Fixed with', extra, 'extra )');
    break;
  } catch(e) {}
}

// Count brackets
let parens = 0, braces = 0, brackets = 0;
for (const c of s) {
  if (c === '(') parens++;
  if (c === ')') parens--;
  if (c === '{') braces++;
  if (c === '}') braces--;
  if (c === '[') brackets++;
  if (c === ']') brackets--;
}
console.log('Paren balance:', parens);
console.log('Brace balance:', braces);
console.log('Bracket balance:', brackets);
