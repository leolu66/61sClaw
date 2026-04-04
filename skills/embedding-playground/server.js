const http = require('http');
const fs = require('fs');
const path = require('path');
const db = require('./db');
const { embed, embedMulti } = require('./embedder');
const { similarityMatrix } = require('./calculator');
const { pcaReduce, generate2DChart, generate3DChart } = require('./visualizer');

const PORT = 19876;

function parseJSON(body) {
  try {
    return JSON.parse(body);
  } catch (e) {
    return null;
  }
}

function sendJSON(res, data, status = 200) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(data));
}

function sendError(res, message, status = 400) {
  sendJSON(res, { error: message }, status);
}

const server = http.createServer(async (req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const pathname = url.pathname;
  
  // Parse body for POST/PUT requests
  let body = '';
  if (req.method === 'POST' || req.method === 'PUT') {
    body = await new Promise((resolve) => {
      let data = '';
      req.on('data', chunk => data += chunk);
      req.on('end', () => resolve(data));
    });
  }
  
  // Routes
  try {
    // GET / - Serve index.html
    if (pathname === '/' && req.method === 'GET') {
      const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(html);
      return;
    }
    
    // GET /api/models - List all models
    if (pathname === '/api/models' && req.method === 'GET') {
      sendJSON(res, db.getAllModels());
      return;
    }
    
    // POST /api/models - Add new model
    if (pathname === '/api/models' && req.method === 'POST') {
      const data = parseJSON(body);
      if (!data || !data.name || !data.model_id) {
        sendError(res, 'Missing required fields: name, model_id');
        return;
      }
      const model = db.addModel(data);
      sendJSON(res, model, 201);
      return;
    }
    
    // PUT /api/models/:id - Update model
    if (pathname.startsWith('/api/models/') && req.method === 'PUT') {
      const id = parseInt(pathname.split('/')[3]);
      const data = parseJSON(body);
      if (!data) {
        sendError(res, 'Invalid JSON');
        return;
      }
      const model = db.updateModel(id, data);
      if (!model) {
        sendError(res, 'Model not found', 404);
        return;
      }
      sendJSON(res, model);
      return;
    }
    
    // DELETE /api/models/:id - Delete/disable model
    if (pathname.startsWith('/api/models/') && req.method === 'DELETE') {
      const id = parseInt(pathname.split('/')[3]);
      const result = db.deleteModel(id);
      if (!result) {
        sendError(res, 'Model not found', 404);
        return;
      }
      sendJSON(res, result);
      return;
    }
    
    // POST /api/embed - Embed text
    if (pathname === '/api/embed' && req.method === 'POST') {
      const data = parseJSON(body);
      if (!data || !data.text || !data.modelIds || !Array.isArray(data.modelIds)) {
        sendError(res, 'Missing required fields: text, modelIds');
        return;
      }
      
      const modelConfigs = data.modelIds.map(id => db.getModelById(id)).filter(Boolean);
      if (modelConfigs.length === 0) {
        sendError(res, 'No valid models found');
        return;
      }
      
      const results = await embedMulti(data.text, modelConfigs);
      const response = results.map(r => ({
        modelName: r.model,
        modelId: r.modelId,
        dimension: r.dimension,
        vectorPreview: r.vector ? r.vector.slice(0, 8) : null,
        vector: r.vector,
        duration: r.duration,
        fromCache: r.fromCache,
        error: r.error
      }));
      
      sendJSON(res, { results: response });
      return;
    }
    
    // POST /api/similarity - Similarity matrix
    if (pathname === '/api/similarity' && req.method === 'POST') {
      const data = parseJSON(body);
      if (!data) {
        sendError(res, 'Invalid JSON');
        return;
      }
      
      let vectors = [];
      let labels = [];
      
      if (data.vectorIds && Array.isArray(data.vectorIds)) {
        const savedVectors = db.getVectorsByIds(data.vectorIds);
        vectors = savedVectors.map(v => JSON.parse(v.vector_blob));
        labels = savedVectors.map(v => v.text.substring(0, 50));
      } else if (data.texts && Array.isArray(data.texts) && data.modelId) {
        const modelConfig = db.getModelById(data.modelId);
        if (!modelConfig) {
          sendError(res, 'Model not found', 404);
          return;
        }
        
        for (const text of data.texts) {
          const { embed } = require('./embedder');
          const result = await embed(text, modelConfig);
          vectors.push(result.vector);
          labels.push(text.substring(0, 50));
        }
      } else {
        sendError(res, 'Missing required fields: vectorIds OR (texts + modelId)');
        return;
      }
      
      const matrix = similarityMatrix(vectors);
      
      // Find min/max
      let minVal = 1, maxVal = -1;
      let minPair = null, maxPair = null;
      for (let i = 0; i < matrix.length; i++) {
        for (let j = i + 1; j < matrix.length; j++) {
          if (matrix[i][j] < minVal) {
            minVal = matrix[i][j];
            minPair = [i, j];
          }
          if (matrix[i][j] > maxVal) {
            maxVal = matrix[i][j];
            maxPair = [i, j];
          }
        }
      }
      
      sendJSON(res, {
        matrix,
        labels,
        min: minPair ? { value: minVal, pair: minPair } : null,
        max: maxPair ? { value: maxVal, pair: maxPair } : null
      });
      return;
    }
    
    // POST /api/visualize - Generate visualization
    if (pathname === '/api/visualize' && req.method === 'POST') {
      const data = parseJSON(body);
      if (!data || !data.texts || !Array.isArray(data.texts) || !data.modelIds || !Array.isArray(data.modelIds)) {
        sendError(res, 'Missing required fields: texts, modelIds');
        return;
      }
      
      const dims = data.dims || 2;
      const algorithm = data.algorithm || 'pca';
      const modelConfigs = data.modelIds.map(id => db.getModelById(id)).filter(Boolean);
      
      if (modelConfigs.length === 0) {
        sendError(res, 'No valid models selected');
        return;
      }
      
      // All vectors must have same dimension
      const expectedDim = modelConfigs[0].dimension;
      for (const config of modelConfigs) {
        if (config.dimension !== expectedDim) {
          sendError(res, 'All selected models must have same dimension');
          return;
        }
      }
      
      const allVectors = [];
      const allLabels = [];
      const allModelNames = [];
      
      for (const text of data.texts) {
        for (const config of modelConfigs) {
          const { embed } = require('./embedder');
          const result = await embed(text, config);
          allVectors.push(result.vector);
          allLabels.push(text.substring(0, 50));
          allModelNames.push(config.name);
        }
      }
      
      const { reduceVectors } = require('./visualizer');
      const coordinates = reduceVectors(allVectors, dims, algorithm);
      
      let html;
      if (dims === 3) {
        html = generate3DChart(coordinates, allLabels, allModelNames, algorithm);
      } else {
        html = generate2DChart(coordinates, allLabels, allModelNames, algorithm);
      }
      
      sendJSON(res, { html });
      return;
    }
    
    // GET /api/vectors - List vectors
    if (pathname === '/api/vectors' && req.method === 'GET') {
      const page = parseInt(url.searchParams.get('page')) || 1;
      const pageSize = parseInt(url.searchParams.get('pageSize')) || 50;
      sendJSON(res, db.getAllVectors(page, pageSize));
      return;
    }
    
    // DELETE /api/vectors/:id - Delete vector
    if (pathname.startsWith('/api/vectors/') && req.method === 'DELETE') {
      const id = parseInt(pathname.split('/')[3]);
      const result = db.deleteVector(id);
      if (!result) {
        sendError(res, 'Vector not found', 404);
        return;
      }
      sendJSON(res, { deleted: true });
      return;
    }
    
    // 404
    sendError(res, 'Not found', 404);
    
  } catch (error) {
    console.error('Error handling request:', error);
    sendError(res, 'Internal server error', 500);
  }
});

server.listen(PORT, () => {
  console.log(`Embedding Playground server running at http://localhost:${PORT}`);
});
