const fs = require('fs');
const h = fs.readFileSync('index.html', 'utf8');
const s = h.match(/<script>([\s\S]*?)<\/script>/)[1];

const start = s.indexOf('function renderModelCheckboxes');
const nextFunc = s.indexOf('function openModelModal');
const func = s.substring(start, nextFunc);

// Format it - add newlines at key points
const formatted = func
  .replace(/;/g, ';\n')
  .replace(/{/g, '{\n')
  .replace(/}/g, '}\n');
  
console.log(formatted);
