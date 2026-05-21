import { smartSearch } from './search-providers';

async function test() {
  console.log('Testing search with VPN (Brave should work)...');
  const result = await smartSearch('OpenClaw AI agent framework', 3);
  console.log('Provider:', result.provider);
  console.log('Results count:', result.results.length);
  if (result.results.length > 0) {
    console.log('First result:', result.results[0].title);
    console.log('URL:', result.results[0].url);
  }
}

test().catch(console.error);
