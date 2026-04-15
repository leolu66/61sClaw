const { Database } = require('node-sqlite3-wasm');
const path = require('path');
const fs = require('fs');

const DATA_DIR = path.join(__dirname, 'data');
const DB_FILE = path.join(DATA_DIR, 'embedding_playground.db');
const PRESET_FILE = path.join(__dirname, 'references', 'preset-models.json');

class DatabaseWrapper {
  constructor() {
    this.db = null;
    this.init();
  }

  init() {
    // Ensure data directory exists
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }

    // Open database
    this.db = new Database(DB_FILE);

    // Create tables
    this.createTables();

    // Initialize preset models
    this.initPresetModels();
  }

  createTables() {
    // Models table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        api_url TEXT,
        api_key TEXT,
        model_id TEXT NOT NULL,
        dimension INTEGER,
        price_per_mtokens REAL,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        is_preset INTEGER DEFAULT 0,
        created_at TEXT
      )
    `);

    // Vectors table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS vectors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        model_config_id INTEGER,
        vector_blob TEXT,
        dimension INTEGER,
        created_at TEXT
      )
    `);
  }

  initPresetModels() {
    // Check if presets already exist
    const count = this.db.get('SELECT COUNT(*) as count FROM models WHERE is_preset = 1');
    if (count.count > 0) {
      return; // Presets already initialized
    }

    const presets = JSON.parse(fs.readFileSync(PRESET_FILE, 'utf8'));
    const apiUrl = 'https://lab.iwhalecloud.com/gpt-proxy/v1/embeddings';
    const apiKey = process.env.WHALECLOUD_API_KEY || 'ailab_0MSAtJQa9d/tXaT2eW7wCK1FAfqh8ZVJlhptKupF2F/2ZaU01zwO0SyJtkLIXfo1f5iBemAbJBGR/wA8vkfuw8uUQIgcNB6gvKl2NGsjd0YdVnK0GP31spo=';
    
    presets.models.forEach((preset, index) => {
      const id = index + 1;
      const description = `Context: ${preset.context || '-'}, Params: ${preset.params || '-'}`;
      const createdAt = new Date().toISOString();
      
      this.db.run(
        `INSERT INTO models (id, name, api_url, api_key, model_id, dimension, price_per_mtokens, description, is_active, is_preset, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [id, preset.name, apiUrl, apiKey, preset.model_id, preset.dimension, preset.price_per_mtokens, description, 1, 1, createdAt]
      );
    });
  }

  // Models CRUD
  getAllModels() {
    const rows = this.db.all('SELECT * FROM models ORDER BY id');
    return rows.map(row => ({
      ...row,
      is_active: row.is_active === 1,
      is_preset: row.is_preset === 1
    }));
  }

  getModelById(id) {
    const row = this.db.get('SELECT * FROM models WHERE id = ?', [id]);
    if (!row) return null;
    
    return {
      ...row,
      is_active: row.is_active === 1,
      is_preset: row.is_preset === 1
    };
  }

  getActiveModels() {
    const rows = this.db.all('SELECT * FROM models WHERE is_active = 1 ORDER BY id');
    return rows.map(row => ({
      ...row,
      is_active: row.is_active === 1,
      is_preset: row.is_preset === 1
    }));
  }

  addModel(model) {
    const createdAt = new Date().toISOString();
    
    const result = this.db.run(
      `INSERT INTO models (name, api_url, api_key, model_id, dimension, price_per_mtokens, description, is_active, is_preset, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        model.name,
        model.api_url || '',
        model.api_key || '',
        model.model_id,
        model.dimension || 0,
        model.price_per_mtokens || 0,
        model.description || '',
        model.is_active !== undefined ? (model.is_active ? 1 : 0) : 1,
        0, // is_preset
        createdAt
      ]
    );
    
    return this.getModelById(result.lastInsertRowid);
  }

  updateModel(id, updates) {
    const model = this.getModelById(id);
    if (!model) return null;
    
    // Prevent changing is_preset status and model_id for preset models
    if (model.is_preset) {
      delete updates.is_preset;
      delete updates.model_id;
    }
    
    const fields = [];
    const values = [];
    
    if (updates.name !== undefined) {
      fields.push('name = ?');
      values.push(updates.name);
    }
    if (updates.api_url !== undefined) {
      fields.push('api_url = ?');
      values.push(updates.api_url);
    }
    if (updates.api_key !== undefined) {
      fields.push('api_key = ?');
      values.push(updates.api_key);
    }
    if (updates.model_id !== undefined) {
      fields.push('model_id = ?');
      values.push(updates.model_id);
    }
    if (updates.dimension !== undefined) {
      fields.push('dimension = ?');
      values.push(updates.dimension);
    }
    if (updates.price_per_mtokens !== undefined) {
      fields.push('price_per_mtokens = ?');
      values.push(updates.price_per_mtokens);
    }
    if (updates.description !== undefined) {
      fields.push('description = ?');
      values.push(updates.description);
    }
    if (updates.is_active !== undefined) {
      fields.push('is_active = ?');
      values.push(updates.is_active ? 1 : 0);
    }
    
    if (fields.length === 0) return model;
    
    values.push(id);
    
    this.db.run(`UPDATE models SET ${fields.join(', ')} WHERE id = ?`, values);
    
    return this.getModelById(id);
  }

  deleteModel(id) {
    const model = this.getModelById(id);
    if (!model) return false;
    
    // Preset models can only be disabled, not deleted
    if (model.is_preset) {
      this.updateModel(id, { is_active: false });
      return { disabled: true };
    }
    
    this.db.run('DELETE FROM models WHERE id = ?', [id]);
    return { deleted: true };
  }

  // Vectors CRUD
  getAllVectors(page = 1, pageSize = 50) {
    const offset = (page - 1) * pageSize;
    
    const countResult = this.db.get('SELECT COUNT(*) as total FROM vectors');
    const total = countResult.total;
    
    const rows = this.db.all('SELECT * FROM vectors ORDER BY id DESC LIMIT ? OFFSET ?', [pageSize, offset]);
    
    return {
      vectors: rows,
      total,
      page,
      pageSize
    };
  }

  getVectorById(id) {
    return this.db.get('SELECT * FROM vectors WHERE id = ?', [id]) || null;
  }

  findVectorByTextAndModel(text, modelConfigId) {
    return this.db.get('SELECT * FROM vectors WHERE text = ? AND model_config_id = ?', [text, modelConfigId]) || null;
  }

  addVector(vector) {
    // Check if already exists
    const existing = this.findVectorByTextAndModel(vector.text, vector.model_config_id);
    if (existing) {
      return existing;
    }
    
    const createdAt = new Date().toISOString();
    
    const result = this.db.run(
      `INSERT INTO vectors (text, model_config_id, vector_blob, dimension, created_at)
       VALUES (?, ?, ?, ?, ?)`,
      [
        vector.text,
        vector.model_config_id,
        vector.vector_blob,
        vector.dimension,
        createdAt
      ]
    );
    
    return this.getVectorById(result.lastInsertRowid);
  }

  deleteVector(id) {
    this.db.run('DELETE FROM vectors WHERE id = ?', [id]);
    return true;
  }

  getVectorsByIds(ids) {
    if (!ids || ids.length === 0) return [];
    
    const placeholders = ids.map(() => '?').join(',');
    return this.db.all(`SELECT * FROM vectors WHERE id IN (${placeholders})`, ids);
  }
}

module.exports = new DatabaseWrapper();
