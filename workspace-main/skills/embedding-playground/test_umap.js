const { umapReduce } = require('./visualizer');

// Test with sample vectors
const vectors = [
  [1, 2, 3, 4, 5],
  [1.1, 2.2, 3.1, 4.2, 5.1],
  [10, 20, 30, 40, 50],
  [10.1, 20.2, 30.1, 40.2, 50.1]
];

console.log('Testing UMAP reduce...');
try {
  const result = umapReduce(vectors, 2);
  console.log('UMAP result:', result);
} catch(e) {
  console.error('UMAP error:', e);
  console.error(e.stack);
}

// Test t-SNE
const { tsneReduce } = require('./visualizer');
console.log('\nTesting t-SNE reduce...');
try {
  const result2 = tsneReduce(vectors, 2);
  console.log('t-SNE result:', result2);
} catch(e) {
  console.error('t-SNE error:', e);
  console.error(e.stack);
}
