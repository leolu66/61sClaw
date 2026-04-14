import * as fs from 'fs/promises';
import * as readline from 'readline';
import { parseArgs } from 'util';
import * as path from 'path';

import { deepResearch, writeFinalReport } from './deep-research';
import { generateFeedback } from './feedback';

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

// Helper function to get user input
function askQuestion(query: string): Promise<string> {
  return new Promise(resolve => {
    rl.question(query, answer => {
      resolve(answer);
    });
  });
}

// run the agent
async function run() {
  // 解析命令行参数
  const { values, positionals } = parseArgs({
    options: {
      breadth: { type: 'string', default: '12' },
      depth: { type: 'string', default: '3' },
      output: { type: 'string', default: 'report.md' },
      'no-interactive': { type: 'boolean', default: false },
    },
    allowPositionals: true,
  });

  let initialQuery = positionals[0];
  let breadth = parseInt(values.breadth as string, 10) || 4;
  let depth = parseInt(values.depth as string, 10) || 2;
  const outputPath = values.output as string;
  const interactive = !values['no-interactive'];

  // 如果没有提供查询参数，提示用户输入
  if (!initialQuery) {
    initialQuery = await askQuestion('What would you like to research? ');
  }

  let combinedQuery = initialQuery;

  // 如果是交互模式，询问参数和后续问题
  if (interactive) {
    // Get breath and depth parameters if not provided
    if (!values.breadth) {
      breadth = parseInt(
        await askQuestion(
          'Enter research breadth (recommended 2-10, default 4): ',
        ),
        10,
      ) || 4;
    }
    if (!values.depth) {
      depth = parseInt(
        await askQuestion('Enter research depth (recommended 1-5, default 2): '),
        10,
      ) || 2;
    }

    console.log(`Creating research plan...`);

    // Generate follow-up questions
    const followUpQuestions = await generateFeedback({
      query: initialQuery,
    });

    console.log(
      '\nTo better understand your research needs, please answer these follow-up questions:',
    );

    // Collect answers to follow-up questions
    const answers: string[] = [];
    for (const question of followUpQuestions) {
      const answer = await askQuestion(`\n${question}\nYour answer: `);
      answers.push(answer);
    }

    // Combine all information for deep research
    combinedQuery = `
Initial Query: ${initialQuery}
Follow-up Questions and Answers:
${followUpQuestions.map((q, i) => `Q: ${q}\nA: ${answers[i]}`).join('\n')}
`;
  } else {
    console.log(`Starting non-interactive research...`);
    console.log(`Query: ${initialQuery}`);
    console.log(`Breadth: ${breadth}, Depth: ${depth}`);
  }

  console.log('\nResearching your topic...');

  const { learnings, visitedSources } = await deepResearch({
    query: combinedQuery,
    breadth,
    depth,
  });

  console.log(`\n\nLearnings:\n\n${learnings.join('\n')}`);
  console.log(
    `\n\nVisited Sources (${visitedSources.length}):\n\n${visitedSources.map(s => `- [${s.title}](${s.url})`).join('\n')}`,
  );
  console.log('Writing final report...');

  const report = await writeFinalReport({
    prompt: combinedQuery,
    learnings,
    visitedSources,
  });

  // 提取报告标题作为文件名
  let finalOutputPath = outputPath;
  if (outputPath === 'report.md') {
    // 从报告中提取第一个#标题
    const titleMatch = report.match(/^#\s+(.+)$/m);
    let filename = 'report.md';
    if (titleMatch) {
      // 处理标题中的特殊字符，替换为安全的字符
      const title = titleMatch[1].trim();
      filename = title.replace(/[<>:"/\\|?*]/g, '_').replace(/\s+/g, '-') + '.md';
    }
    finalOutputPath = path.join(__dirname, '..', 'output', filename);
    // 确保output目录存在
    await fs.mkdir(path.dirname(finalOutputPath), { recursive: true });
  }

  // Save report to file
  await fs.writeFile(finalOutputPath, report, 'utf-8');

  console.log(`\n\nFinal Report:\n\n${report}`);
  console.log(`\nReport has been saved to ${finalOutputPath}`);
  rl.close();
}

run().catch(console.error);
