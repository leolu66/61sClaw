const fs = require('fs');
const path = process.argv[2];

let content = fs.readFileSync(path, 'utf-8');

// Remove the status line from _getLegend function
content = content.replace(
  /状态[：:]\s*⏳[^`\n]*\n/,
  ''
);

fs.writeFileSync(path, content, 'utf-8');
console.log('Status line removed!');
