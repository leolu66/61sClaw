const fs = require('fs');
const h = fs.readFileSync('index.html', 'utf8');
const s = h.match(/<script>([\s\S]*?)<\/script>/)[1];

const start = s.indexOf('function renderModelCheckboxes');
const chunk = s.substring(start, start + 1500);
console.log(chunk);
