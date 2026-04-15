const db = require('./db');

const API_URL = 'https://lab.iwhalecloud.com/gpt-proxy/v1/embeddings';
const DEFAULT_API_KEY = process.env.WHALECLOUD_API_KEY || 'ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo=';

async function fetchWithTimeout(url, options, timeout = 30000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

async function embed(text, modelConfig, retryCount = 1) {
  const startTime = Date.now();
  
  // Check cache first
  const cached = db.findVectorByTextAndModel(text, modelConfig.id);
  if (cached) {
    return {
      vector: JSON.parse(cached.vector_blob),
      dimension: cached.dimension,
      usage: { cached: true },
      duration: 0,
      fromCache: true
    };
  }
  
  const apiKey = modelConfig.api_key || DEFAULT_API_KEY;
  const apiUrl = modelConfig.api_url || API_URL;
  
  let lastError;
  for (let attempt = 0; attempt <= retryCount; attempt++) {
    try {
      const response = await fetchWithTimeout(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          model: modelConfig.model_id,
          input: text
        })
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      const vector = data.data[0].embedding;
      const duration = Date.now() - startTime;
      
      // Save to database
      db.addVector({
        text,
        model_config_id: modelConfig.id,
        vector_blob: JSON.stringify(vector),
        dimension: vector.length
      });
      
      return {
        vector,
        dimension: vector.length,
        usage: data.usage || {},
        duration,
        fromCache: false
      };
    } catch (error) {
      lastError = error;
      if (attempt < retryCount) {
        await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
      }
    }
  }
  
  throw lastError;
}

async function embedBatch(texts, modelConfig) {
  const results = [];
  for (const text of texts) {
    results.push(await embed(text, modelConfig));
  }
  return results;
}

async function embedMulti(text, modelConfigs) {
  const results = [];
  for (const config of modelConfigs) {
    try {
      const result = await embed(text, config);
      results.push({
        model: config.name,
        modelId: config.id,
        ...result
      });
    } catch (error) {
      results.push({
        model: config.name,
        modelId: config.id,
        error: error.message
      });
    }
  }
  return results;
}

module.exports = {
  embed,
  embedBatch,
  embedMulti
};
