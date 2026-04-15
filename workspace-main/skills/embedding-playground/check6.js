const vm = require('vm');
const fs = require('fs');
const h = fs.readFileSync('index.html', 'utf8');
const s = h.match(/<script>([\s\S]*?)<\/script>/)[1];

try {
  new vm.Script(s, { filename: 'test.js' });
  console.log('OK');
} catch(e) {
  console.log('Line:', e.lineNumber);
  console.log('Column:', e.column);
  // Extract around the column position
  if (e.column) {
    const pos = e.column - 1;
    console.log('Context:', s.substring(Math.max(0, pos - 100), pos + 100));
    console.log('At pos:', pos);
    console.log('Char at pos:', JSON.stringify(s[pos]));
    console.log('Chars around:', JSON.stringify(s.substring(pos - 5, pos + 5)));
  }
}
