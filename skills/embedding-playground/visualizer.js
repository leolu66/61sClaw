// Common utility functions
function transpose(matrix) {
  const rows = matrix.length;
  const cols = matrix[0].length;
  const result = [];
  
  for (let j = 0; j < cols; j++) {
    result[j] = [];
    for (let i = 0; i < rows; i++) {
      result[j][i] = matrix[i][j];
    }
  }
  
  return result;
}

function matrixMultiply(a, b) {
  const rowsA = a.length;
  const colsA = a[0].length;
  const colsB = b[0].length;
  const result = [];
  
  for (let i = 0; i < rowsA; i++) {
    result[i] = [];
    for (let j = 0; j < colsB; j++) {
      let sum = 0;
      for (let k = 0; k < colsA; k++) {
        sum += a[i][k] * b[k][j];
      }
      result[i][j] = sum;
    }
  }
  
  return result;
}

function centerData(matrix) {
  const rows = matrix.length;
  const cols = matrix[0].length;
  const means = [];
  
  for (let j = 0; j < cols; j++) {
    let sum = 0;
    for (let i = 0; i < rows; i++) {
      sum += matrix[i][j];
    }
    means[j] = sum / rows;
  }
  
  const centered = [];
  for (let i = 0; i < rows; i++) {
    centered[i] = [];
    for (let j = 0; j < cols; j++) {
      centered[i][j] = matrix[i][j] - means[j];
    }
  }
  
  return centered;
}

function euclideanDistance(a, b) {
  let sum = 0;
  for (let i = 0; i < a.length; i++) {
    const diff = a[i] - b[i];
    sum += diff * diff;
  }
  return Math.sqrt(sum);
}

// ==================== PCA ====================
function powerIteration(matrix, numComponents) {
  const n = matrix.length;
  const eigenvalues = [];
  const eigenvectors = [];
  
  let workingMatrix = matrix.map(row => [...row]);
  
  for (let comp = 0; comp < numComponents; comp++) {
    let vec = new Array(n).fill(0).map(() => Math.random() - 0.5);
    let norm = Math.sqrt(vec.reduce((sum, x) => sum + x * x, 0));
    vec = vec.map(x => x / norm);
    
    for (let iter = 0; iter < 100; iter++) {
      let newVec = new Array(n).fill(0);
      for (let i = 0; i < n; i++) {
        for (let j = 0; j < n; j++) {
          newVec[i] += workingMatrix[i][j] * vec[j];
        }
      }
      
      norm = Math.sqrt(newVec.reduce((sum, x) => sum + x * x, 0));
      if (norm > 1e-10) {
        vec = newVec.map(x => x / norm);
      }
    }
    
    let eigenvalue = 0;
    for (let i = 0; i < n; i++) {
      let sum = 0;
      for (let j = 0; j < n; j++) {
        sum += workingMatrix[i][j] * vec[j];
      }
      eigenvalue += vec[i] * sum;
    }
    
    eigenvalues.push(eigenvalue);
    eigenvectors.push([...vec]);
    
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        workingMatrix[i][j] -= eigenvalue * vec[i] * vec[j];
      }
    }
  }
  
  return { eigenvalues, eigenvectors };
}

function pcaReduce(vectors, targetDims = 2) {
  if (vectors.length === 0) return [];
  if (vectors.length === 1) return [[0, 0]];
  
  const centered = centerData(vectors);
  const n = centered.length;
  const dims = centered[0].length;
  const covMatrix = [];
  
  for (let i = 0; i < n; i++) {
    covMatrix[i] = [];
    for (let j = 0; j < n; j++) {
      let sum = 0;
      for (let k = 0; k < dims; k++) {
        sum += centered[i][k] * centered[j][k];
      }
      covMatrix[i][j] = sum / (dims - 1);
    }
  }
  
  const { eigenvectors } = powerIteration(covMatrix, targetDims);
  
  const coordinates = [];
  for (let i = 0; i < n; i++) {
    coordinates[i] = [];
    for (let d = 0; d < targetDims; d++) {
      let sum = 0;
      for (let j = 0; j < n; j++) {
        sum += centered[j][i] * eigenvectors[d][j];
      }
      coordinates[i][d] = sum;
    }
  }
  
  return coordinates;
}

// ==================== t-SNE ====================
function tsneReduce(vectors, targetDims = 2, perplexity = 30, iterations = 500) {
  const n = vectors.length;
  if (n <= 1) return n === 0 ? [] : [[0, 0]];
  
  // Compute pairwise distances
  const distances = new Array(n);
  for (let i = 0; i < n; i++) {
    distances[i] = new Array(n);
    for (let j = 0; j < n; j++) {
      distances[i][j] = euclideanDistance(vectors[i], vectors[j]);
    }
  }
  
  // Compute conditional probabilities P
  const P = new Array(n);
  for (let i = 0; i < n; i++) {
    P[i] = new Array(n);
    let sum = 0;
    for (let j = 0; j < n; j++) {
      if (i !== j) {
        P[i][j] = Math.exp(-distances[i][j] * distances[i][j] / (2 * perplexity * perplexity));
        sum += P[i][j];
      } else {
        P[i][j] = 0;
      }
    }
    // Normalize
    for (let j = 0; j < n; j++) {
      P[i][j] /= sum + 1e-10;
    }
  }
  
  // Symmetrize P
  const P_sym = new Array(n);
  for (let i = 0; i < n; i++) {
    P_sym[i] = new Array(n);
    for (let j = 0; j < n; j++) {
      P_sym[i][j] = (P[i][j] + P[j][i]) / (2 * n);
    }
  }
  
  // Initialize low-dimensional points randomly
  let Y = new Array(n);
  for (let i = 0; i < n; i++) {
    Y[i] = new Array(targetDims);
    for (let d = 0; d < targetDims; d++) {
      Y[i][d] = Math.random() * 0.0001;
    }
  }
  
  // Gradient descent parameters
  const eta = 200;
  const momentum = 0.8;
  let dY = new Array(n).fill(0).map(() => new Array(targetDims).fill(0));
  let dY_prev = new Array(n).fill(0).map(() => new Array(targetDims).fill(0));
  
  // Optimization loop
  for (let iter = 0; iter < iterations; iter++) {
    // Compute low-dimensional similarities Q
    const Q = new Array(n);
    let sum_Q = 0;
    for (let i = 0; i < n; i++) {
      Q[i] = new Array(n);
      for (let j = 0; j < n; j++) {
        if (i !== j) {
          const dist = euclideanDistance(Y[i], Y[j]);
          Q[i][j] = 1 / (1 + dist * dist);
          sum_Q += Q[i][j];
        } else {
          Q[i][j] = 0;
        }
      }
    }
    
    // Normalize Q
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        Q[i][j] /= sum_Q + 1e-10;
      }
    }
    
    // Compute gradients
    for (let i = 0; i < n; i++) {
      for (let d = 0; d < targetDims; d++) {
        dY[i][d] = 0;
        for (let j = 0; j < n; j++) {
          if (i !== j) {
            const diff = Y[i][d] - Y[j][d];
            const pq = P_sym[i][j] - Q[i][j];
            const dist = euclideanDistance(Y[i], Y[j]);
            const factor = pq * diff / (1 + dist * dist);
            dY[i][d] += factor;
          }
        }
        dY[i][d] *= 4;
      }
    }
    
    // Update Y with momentum
    for (let i = 0; i < n; i++) {
      for (let d = 0; d < targetDims; d++) {
        Y[i][d] -= eta * dY[i][d] + momentum * (dY[i][d] - dY_prev[i][d]);
      }
    }
    
    // Save previous gradients
    const temp = dY_prev;
    dY_prev = dY;
    dY = temp;
    
    // Center Y
    const mean = new Array(targetDims).fill(0);
    for (let i = 0; i < n; i++) {
      for (let d = 0; d < targetDims; d++) {
        mean[d] += Y[i][d];
      }
    }
    for (let d = 0; d < targetDims; d++) {
      mean[d] /= n;
    }
    for (let i = 0; i < n; i++) {
      for (let d = 0; d < targetDims; d++) {
        Y[i][d] -= mean[d];
      }
    }
  }
  
  return Y;
}

// ==================== UMAP ====================
function umapReduce(vectors, targetDims = 2, n_neighbors = 15, iterations = 200) {
  const n = vectors.length;
  if (n <= 1) return n === 0 ? [] : [[0, 0]];
  
  // Step 1: Compute k-nearest neighbors
  const distances = new Array(n);
  for (let i = 0; i < n; i++) {
    distances[i] = [];
    for (let j = 0; j < n; j++) {
      if (i !== j) {
        const dist = euclideanDistance(vectors[i], vectors[j]);
        distances[i].push({ dist, idx: j });
      }
    }
    distances[i].sort((a, b) => a.dist - b.dist);
  }
  
  // Step 2: Compute fuzzy simplicial set weights
  const P = new Array(n);
  for (let i = 0; i < n; i++) {
    P[i] = new Array(n).fill(0);
    const rho = distances[i][0].dist;
    const sigma = distances[i][Math.min(n_neighbors, distances[i].length - 1)].dist / Math.sqrt(n_neighbors);
    
    for (let k = 0; k < Math.min(n_neighbors, distances[i].length); k++) {
      const j = distances[i][k].idx;
      const dist = distances[i][k].dist;
      P[i][j] = Math.exp(-Math.max(0, dist - rho) / sigma);
    }
  }
  
  // Symmetrize
  const P_sym = new Array(n);
  for (let i = 0; i < n; i++) {
    P_sym[i] = new Array(n);
    for (let j = 0; j < n; j++) {
      P_sym[i][j] = P[i][j] + P[j][i] - P[i][j] * P[j][i];
    }
  }
  
  // Initialize low-dimensional points
  let Y = pcaReduce(vectors, targetDims); // Use PCA for initialization
  
  // Step 3: Optimization with gradient descent
  const a = 1.576943460309767;
  const b = 0.895060878365303;
  const gamma = 1.0;
  const eta = 1.0;
  
  let dY = new Array(n).fill(0).map(() => new Array(targetDims).fill(0));
  
  for (let iter = 0; iter < iterations; iter++) {
    // Compute Q
    const Q = new Array(n);
    // First initialize all rows
    for (let i = 0; i < n; i++) {
      Q[i] = new Array(n).fill(0);
    }
    // Then fill upper triangle and mirror
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const dist = euclideanDistance(Y[i], Y[j]);
        Q[i][j] = 1 / (1 + a * Math.pow(dist, 2 * b));
        Q[j][i] = Q[i][j];
      }
    }
    
    // Compute gradients
    for (let i = 0; i < n; i++) {
      for (let d = 0; d < targetDims; d++) {
        dY[i][d] = 0;
        for (let j = 0; j < n; j++) {
          if (i !== j) {
            const diff = Y[i][d] - Y[j][d];
            const w_ij = P_sym[i][j];
            const q_ij = Q[i][j];
            const factor = 2 * a * b * Math.pow(euclideanDistance(Y[i], Y[j]), 2 * b - 2) / (1 + a * Math.pow(euclideanDistance(Y[i], Y[j]), 2 * b));
            dY[i][d] += (w_ij - q_ij) * factor * diff * gamma;
          }
        }
      }
    }
    
    // Update
    for (let i = 0; i < n; i++) {
      for (let d = 0; d < targetDims; d++) {
        Y[i][d] -= eta * dY[i][d];
      }
    }
    
    // Center
    const mean = new Array(targetDims).fill(0);
    for (let i = 0; i < n; i++) {
      for (let d = 0; d < targetDims; d++) {
        mean[d] += Y[i][d];
      }
    }
    for (let d = 0; d < targetDims; d++) {
      mean[d] /= n;
    }
    for (let i = 0; i < n; i++) {
      for (let d = 0; d < targetDims; d++) {
        Y[i][d] -= mean[d];
      }
    }
  }
  
  return Y;
}

// Unified reduce function
function reduceVectors(vectors, targetDims = 2, algorithm = 'pca') {
  switch(algorithm.toLowerCase()) {
    case 'tsne':
    case 't-sne':
      return tsneReduce(vectors, targetDims);
    case 'umap':
      return umapReduce(vectors, targetDims);
    case 'pca':
    default:
      return pcaReduce(vectors, targetDims);
  }
}

function generate2DChart(points, labels, modelNames, algorithm = 'pca') {
  const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'];
  
  const traces = [];
  const modelGroups = {};
  
  points.forEach((point, idx) => {
    const modelName = modelNames[idx] || 'Unknown';
    if (!modelGroups[modelName]) {
      modelGroups[modelName] = { x: [], y: [], text: [], name: modelName };
    }
    modelGroups[modelName].x.push(point[0]);
    modelGroups[modelName].y.push(point[1]);
    modelGroups[modelName].text.push(labels[idx] || `Point ${idx}`);
  });
  
  let colorIdx = 0;
  for (const [modelName, group] of Object.entries(modelGroups)) {
    traces.push({
      x: group.x,
      y: group.y,
      mode: 'markers+text',
      type: 'scatter',
      name: modelName,
      text: group.text,
      textposition: 'top center',
      marker: { size: 12, color: colors[colorIdx % colors.length] },
      hovertemplate: '%{text}<br>X: %{x:.4f}<br>Y: %{y:.4f}<extra></extra>'
    });
    colorIdx++;
  }
  
  const algoNames = { 'pca': 'PCA', 'tsne': 't-SNE', 'umap': 'UMAP' };
  const algoName = algoNames[algorithm.toLowerCase()] || algorithm.toUpperCase();
  
  const layout = {
    title: `Embedding Visualization (2D ${algoName})`,
    paper_bgcolor: '#1a1a2e',
    plot_bgcolor: '#16213e',
    font: { color: '#eee' },
    xaxis: { title: 'Dim 1', gridcolor: '#0f3460', zerolinecolor: '#e94560' },
    yaxis: { title: 'Dim 2', gridcolor: '#0f3460', zerolinecolor: '#e94560' },
    legend: { bgcolor: '#1a1a2e', bordercolor: '#0f3460', borderwidth: 1 }
  };
  
  return `<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>body { margin: 0; background: #1a1a2e; }</style>
</head>
<body>
  <div id="chart" style="width:100%;height:100vh;"></div>
  <script>
    const traces = ${JSON.stringify(traces)};
    const layout = ${JSON.stringify(layout)};
    Plotly.newPlot('chart', traces, layout, {responsive: true});
  </script>
</body>
</html>`;
}

function generate3DChart(points, labels, modelNames, algorithm = 'pca') {
  const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'];
  
  const traces = [];
  const modelGroups = {};
  
  points.forEach((point, idx) => {
    const modelName = modelNames[idx] || 'Unknown';
    if (!modelGroups[modelName]) {
      modelGroups[modelName] = { x: [], y: [], z: [], text: [], name: modelName };
    }
    modelGroups[modelName].x.push(point[0]);
    modelGroups[modelName].y.push(point[1]);
    modelGroups[modelName].z.push(point[2] || 0);
    modelGroups[modelName].text.push(labels[idx] || `Point ${idx}`);
  });
  
  let colorIdx = 0;
  for (const [modelName, group] of Object.entries(modelGroups)) {
    traces.push({
      x: group.x,
      y: group.y,
      z: group.z,
      mode: 'markers+text',
      type: 'scatter3d',
      name: modelName,
      text: group.text,
      textposition: 'top center',
      marker: { size: 6, color: colors[colorIdx % colors.length] },
      hovertemplate: '%{text}<br>X: %{x:.4f}<br>Y: %{y:.4f}<br>Z: %{z:.4f}<extra></extra>'
    });
    colorIdx++;
  }
  
  const algoNames = { 'pca': 'PCA', 'tsne': 't-SNE', 'umap': 'UMAP' };
  const algoName = algoNames[algorithm.toLowerCase()] || algorithm.toUpperCase();
  
  const layout = {
    title: `Embedding Visualization (3D ${algoName})`,
    paper_bgcolor: '#1a1a2e',
    scene: {
      bgcolor: '#16213e',
      xaxis: { title: 'Dim 1', gridcolor: '#0f3460' },
      yaxis: { title: 'Dim 2', gridcolor: '#0f3460' },
      zaxis: { title: 'Dim 3', gridcolor: '#0f3460' }
    },
    font: { color: '#eee' },
    legend: { bgcolor: '#1a1a2e', bordercolor: '#0f3460', borderwidth: 1 }
  };
  
  return `<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>body { margin: 0; background: #1a1a2e; }</style>
</head>
<body>
  <div id="chart" style="width:100%;height:100vh;"></div>
  <script>
    const traces = ${JSON.stringify(traces)};
    const layout = ${JSON.stringify(layout)};
    Plotly.newPlot('chart', traces, layout, {responsive: true});
  </script>
</body>
</html>`;
}

module.exports = {
  pcaReduce,
  tsneReduce,
  umapReduce,
  reduceVectors,
  generate2DChart,
  generate3DChart
};
