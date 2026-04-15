const fs = require('fs');
const h = fs.readFileSync('index.html', 'utf8');
const s = h.match(/<script>([\s\S]*?)<\/script>/)[1];

// Find template literals that might have issues
let inBacktick = false;
let backtickStart = -1;
let depth = 0;
const issues = [];

for (let i = 0; i < s.length; i++) {
  if (s[i] === '`' && (i === 0 || s[i-1] !== '\\')) {
    if (!inBacktick) {
      inBacktick = true;
      backtickStart = i;
    } else {
      const template = s.substring(backtickStart, i + 1);
      // Check if it contains onclick with nested quotes
      if (template.includes("onclick=") || template.includes('onclick=')) {
        issues.push({ pos: backtickStart, template: template.substring(0, 200) });
      }
      inBacktick = false;
    }
  }
}

console.log('Templates with onclick:', issues.length);
issues.forEach((iss, idx) => {
  console.log(`\n--- Issue ${idx} at pos ${iss.pos} ---`);
  console.log(iss.template);
});

// Also try to find the exact error position by binary search
function testJS(js) {
  try { new Function(js); return true; } catch(e) { return false; }
}

// Binary search for the error
let lo = 0, hi = s.length;
while (hi - lo > 100) {
  let mid = Math.floor((lo + hi) / 2);
  if (testJS(s.substring(0, mid))) {
    lo = mid;
  } else {
    hi = mid;
  }
}
console.log('\nError region:', s.substring(Math.max(0, lo - 50), hi + 50));
