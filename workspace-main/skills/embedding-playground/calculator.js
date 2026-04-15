function cosineSimilarity(a, b) {
  if (a.length !== b.length) {
    throw new Error('Vectors must have same dimension');
  }
  
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  
  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  
  normA = Math.sqrt(normA);
  normB = Math.sqrt(normB);
  
  if (normA === 0 || normB === 0) {
    return 0;
  }
  
  return dotProduct / (normA * normB);
}

function euclideanDistance(a, b) {
  if (a.length !== b.length) {
    throw new Error('Vectors must have same dimension');
  }
  
  let sum = 0;
  for (let i = 0; i < a.length; i++) {
    const diff = a[i] - b[i];
    sum += diff * diff;
  }
  
  return Math.sqrt(sum);
}

function dotProduct(a, b) {
  if (a.length !== b.length) {
    throw new Error('Vectors must have same dimension');
  }
  
  let sum = 0;
  for (let i = 0; i < a.length; i++) {
    sum += a[i] * b[i];
  }
  
  return sum;
}

function l2Norm(a) {
  let sum = 0;
  for (let i = 0; i < a.length; i++) {
    sum += a[i] * a[i];
  }
  return Math.sqrt(sum);
}

function stats(a) {
  const n = a.length;
  if (n === 0) return { mean: 0, std: 0, min: 0, max: 0 };
  
  let sum = 0;
  let min = a[0];
  let max = a[0];
  
  for (let i = 0; i < n; i++) {
    sum += a[i];
    if (a[i] < min) min = a[i];
    if (a[i] > max) max = a[i];
  }
  
  const mean = sum / n;
  
  let variance = 0;
  for (let i = 0; i < n; i++) {
    variance += (a[i] - mean) * (a[i] - mean);
  }
  
  return {
    mean,
    std: Math.sqrt(variance / n),
    min,
    max
  };
}

function similarityMatrix(vectors) {
  const n = vectors.length;
  const matrix = [];
  
  for (let i = 0; i < n; i++) {
    matrix[i] = [];
    for (let j = 0; j < n; j++) {
      matrix[i][j] = cosineSimilarity(vectors[i], vectors[j]);
    }
  }
  
  return matrix;
}

module.exports = {
  cosineSimilarity,
  euclideanDistance,
  dotProduct,
  l2Norm,
  stats,
  similarityMatrix
};
