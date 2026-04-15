const { embed } = require('./embedder');
const { reduceVectors } = require('./visualizer');

async function test() {
  const texts = ["苹果","梨子","香蕉","手机","国王","王后","父亲","母亲"];
  const modelIds = [1, 5];
  
  console.log('Loading models...');
  const db = require('./db');
  const models = modelIds.map(id => db.getModelById(id)).filter(Boolean);
  console.log('Using models:', models.map(m => m.name));
  
  console.log('Generating embeddings...');
  const allVectors = [];
  for (const text of texts) {
    for (const config of models) {
      console.log('Embedding:', text, 'with', config.name);
      const result = await embed(text, config);
      console.log('Got vector of dim:', result.vector.length);
      allVectors.push(result.vector);
    }
  }
  
  console.log('Total vectors:', allVectors.length);
  console.log('Vector dimensions:', allVectors[0].length);
  
  console.log('Running UMAP...');
  try {
    const coords = reduceVectors(allVectors, 2, 'umap');
    console.log('UMAP result length:', coords.length);
    console.log('Result:', coords);
  } catch(e) {
    console.error('UMAP error:', e);
    console.error(e.stack);
  }
}

test().catch(e => console.error('Error:', e));
