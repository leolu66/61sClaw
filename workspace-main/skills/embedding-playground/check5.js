const fs = require('fs');
const h = fs.readFileSync('index.html', 'utf8');
const s = h.match(/<script>([\s\S]*?)<\/script>/)[1];

// Write to a .js file and use node --check
fs.writeFileSync('test_syntax.js', s);
console.log('Wrote test_syntax.js');
