import { smartSearch } from './search-providers';

async function test() {
  console.log('Testing auto proxy detection...');
  const result = await smartSearch('OpenClaw AI framework', 3);
  console.log('\nFinal result:');
  console.log('Provider:', result.provider);
  console.log('Results count:', result.results.length);
  if (result.results.length > 0) {
    console.log('First result:', result.results[0].title);
  }
}

test().catch(console.error);
