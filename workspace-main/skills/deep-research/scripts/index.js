#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

// 处理命令行参数
const args = process.argv.slice(2);
const query = args[0];
const options = args.slice(1);

if (!query) {
  console.error('Usage: deep_research <query> [options]');
  console.error('Options:');
  console.error('  --breadth <number>   研究广度，默认4');
  console.error('  --depth <number>     研究深度，默认2');
  console.error('  --output <path>      报告输出路径，默认./report.md');
  console.error('  --no-interactive     禁用交互模式');
  process.exit(1);
}

// Windows 适配
const isWindows = process.platform === 'win32';
const npxCmd = isWindows ? 'npx.cmd' : 'npx';

// 运行tsx执行src/run.ts
const runPath = path.join(__dirname, '..', 'src', 'run.ts');
const child = spawn(npxCmd, ['tsx', runPath, query, ...options], {
  cwd: path.join(__dirname, '..'),
  stdio: 'inherit',
  shell: isWindows,
  env: {
    ...process.env,
    FIRECRAWL_KEY: process.env.FIRECRAWL_API_KEY
  }
});

child.on('exit', (code) => {
  process.exit(code);
});
