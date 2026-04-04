// Test the function in isolation
const fs = require('fs');
const h = fs.readFileSync('index.html', 'utf8');
const s = h.match(/<script>([\s\S]*?)<\/script>/)[1];

const start = s.indexOf('function renderModelCheckboxes');
const nextFunc = s.indexOf('function openModelModal');
const func = s.substring(start, nextFunc);

console.log('Function length:', func.length);
console.log('---FUNCTION---');
console.log(func);
console.log('---END---');

// Test character by character to find the exact error position
for (let i = func.length; i > 0; i--) {
  const partial = func.substring(0, i);
  try {
    // Add model variable declaration
    new Function('let models=[];', partial);
    console.log('First valid position:', i, 'of', func.length);
    console.log('Next chars:', JSON.stringify(func.substring(i, i+30)));
    break;
  } catch(e) {}
}
