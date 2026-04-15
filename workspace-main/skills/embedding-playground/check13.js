const fs = require('fs');
const h = fs.readFileSync('index.html', 'utf8');
const s = h.match(/<script>([\s\S]*?)<\/script>/)[1];

const start = s.indexOf('function renderModelCheckboxes');
const nextFunc = s.indexOf('function openModelModal');
const func = s.substring(start, nextFunc);

// Track depth changes, log each ( and )
let depth = 0;
let inSingleQuote = false;
let inDoubleQuote = false;
let inBacktick = false;
let events = [];

for (let i = 0; i < func.length; i++) {
  const c = func[i];
  const prev = i > 0 ? func[i-1] : '';
  
  if (prev === '\\') continue;
  
  if (!inBacktick && !inSingleQuote && !inDoubleQuote) {
    if (c === "'") { inSingleQuote = true; continue; }
    if (c === '"') { inDoubleQuote = true; continue; }
    if (c === '`') { inBacktick = true; continue; }
    if (c === '(') {
      events.push({ type: 'open', pos: i, depth: ++depth, ctx: func.substring(Math.max(0,i-30), i+5) });
      continue;
    }
    if (c === ')') {
      events.push({ type: 'close', pos: i, depth: --depth, ctx: func.substring(Math.max(0,i-5), i+30) });
      continue;
    }
  } else if (inSingleQuote) {
    if (c === "'") { inSingleQuote = false; }
  } else if (inDoubleQuote) {
    if (c === '"') { inDoubleQuote = false; }
  } else if (inBacktick) {
    if (c === '`') { inBacktick = false; }
    if (c === '$' && func[i+1] === '{') {
      let braceDepth = 0;
      let j = i + 2;
      for (; j < func.length; j++) {
        if (func[j] === '{') braceDepth++;
        if (func[j] === '}') {
          if (braceDepth === 0) break;
          braceDepth--;
        }
        if (func[j] === '(') {
          events.push({ type: 'open(templ)', pos: j, depth: ++depth, ctx: func.substring(Math.max(0,j-20), j+10) });
        }
        if (func[j] === ')') {
          events.push({ type: 'close(templ)', pos: j, depth: --depth, ctx: func.substring(Math.max(0,j-5), j+20) });
        }
      }
      i = j;
      continue;
    }
  }
}

// Show last few events before depth doesn't return to 0
console.log('Total events:', events.length);
events.forEach((e, i) => {
  console.log(`${i}: ${e.type} depth=${e.depth} pos=${e.pos} | ${e.ctx.replace(/\n/g,' ')}`);
});
