const fs = require('fs');
const h = fs.readFileSync('index.html', 'utf8');
const s = h.match(/<script>([\s\S]*?)<\/script>/)[1];

// Format the JS to find the error line
const lines = s.split(/([;{}])/);
let accum = '';
for (let i = 0; i < lines.length; i++) {
  accum += lines[i];
  try {
    new Function(accum);
  } catch(e) {
    if (e.message.includes('missing )')) {
      console.log('Error after chunk', i, ':', lines[i].substring(0, 150));
      console.log('Accum ends with:', accum.substring(accum.length - 200));
      break;
    }
  }
}
