/**
 * ConfigLoader - 配置加载器
 * 支持统一入口配置 + 本地覆盖配置
 */

const fs = require('fs');
const path = require('path');

// 配置目录：优先使用 workspace 根目录的 config，否则使用当前工作目录
const WORKSPACE_ROOT = path.resolve(__dirname, '..', '..', '..', '..');
const CONFIG_DIR = path.join(WORKSPACE_ROOT, 'config');
const DEFAULT_CONFIG_FILE = path.join(CONFIG_DIR, 'coordinator.json');
const LOCAL_CONFIG_FILE = path.join(CONFIG_DIR, 'coordinator.local.json');

class ConfigLoader {
  constructor() {
    this.config = null;
    this.lastLoadTime = 0;
    this.configFile = DEFAULT_CONFIG_FILE;
    this.localConfigFile = LOCAL_CONFIG_FILE;
  }

  /**
   * 加载配置
   * @param {boolean} forceReload 强制重新加载
   * @returns {Object} 合并后的配置
   */
  load(forceReload = false) {
    // 缓存 5 秒，避免频繁读取文件
    const now = Date.now();
    if (!forceReload && this.config && (now - this.lastLoadTime) < 5000) {
      return this.config;
    }

    // 读取主配置
    let config = this._readJsonFile(this.configFile);
    if (!config) {
      throw new Error(`配置文件不存在: ${this.configFile}`);
    }

    // 读取本地覆盖配置（如果存在）
    const localConfig = this._readJsonFile(this.localConfigFile);
    if (localConfig) {
      config = this._mergeConfig(config, localConfig);
    }

    // 验证必要字段
    this._validateConfig(config);

    this.config = config;
    this.lastLoadTime = now;
    return config;
  }

  /**
   * 获取当前节点类型配置
   * @returns {Object} 对应节点类型的配置
   */
  getNodeConfig() {
    const config = this.load();
    const nodeType = config.nodeType;
    
    if (nodeType === 'master') {
      return {
        nodeType: 'master',
        nodeId: config.nodeId || 'main',
        ...config.master
      };
    } else if (nodeType === 'worker') {
      return {
        nodeType: 'worker',
        nodeId: config.nodeId || 'worker',
        ...config.worker
      };
    } else {
      throw new Error(`未知的节点类型: ${nodeType}`);
    }
  }

  /**
   * 读取 JSON 文件
   */
  _readJsonFile(filePath) {
    try {
      if (!fs.existsSync(filePath)) {
        return null;
      }
      const content = fs.readFileSync(filePath, 'utf-8');
      return JSON.parse(content);
    } catch (error) {
      console.error(`读取配置文件失败: ${filePath}`, error.message);
      return null;
    }
  }

  /**
   * 合并配置（深度合并）
   */
  _mergeConfig(base, override) {
    const merged = { ...base };
    
    for (const key in override) {
      if (override.hasOwnProperty(key)) {
        if (typeof override[key] === 'object' && override[key] !== null && !Array.isArray(override[key])) {
          merged[key] = this._mergeConfig(merged[key] || {}, override[key]);
        } else {
          merged[key] = override[key];
        }
      }
    }
    
    return merged;
  }

  /**
   * 验证配置
   */
  _validateConfig(config) {
    if (!config.nodeType) {
      throw new Error('配置缺少 nodeType 字段');
    }
    
    if (config.nodeType === 'worker' && !config.nodeId) {
      throw new Error('子节点配置必须包含 nodeId 字段');
    }

    if (config.nodeType === 'master' && !config.master) {
      throw new Error('主节点配置缺少 master 配置块');
    }

    if (config.nodeType === 'worker' && !config.worker) {
      throw new Error('子节点配置缺少 worker 配置块');
    }
  }

  /**
   * 获取配置目录路径
   */
  getConfigDir() {
    return CONFIG_DIR;
  }

  /**
   * 创建默认配置文件（如果不存在）
   */
  static createDefaultConfig() {
    if (fs.existsSync(DEFAULT_CONFIG_FILE)) {
      return;
    }

    const defaultConfig = {
      _comment: '多智能体协调器配置 - 修改后重启扫描生效',
      nodeType: 'master',
      nodeId: 'main',
      master: {
        resultScanInterval: 30000,
        heartbeatCheckInterval: 300000,
        nodeTimeout: 360,
        notificationEnabled: true,
        maxRetries: 2,
        commandsDir: 'D:\\projects\\commands',
        resultsDir: 'D:\\projects\\results',
        configDir: 'D:\\projects\\config'
      },
      worker: {
        taskScanInterval: 30000,
        heartbeatInterval: 300000,
        maxConcurrentTasks: 2,
        capabilities: ['code', 'analysis', 'doc', 'writing'],
        commandsDir: 'D:\\projects\\commands',
        resultsDir: 'D:\\projects\\results',
        configDir: 'D:\\projects\\config',
        workspaceDir: 'D:\\projects\\workspace'
      }
    };

    if (!fs.existsSync(CONFIG_DIR)) {
      fs.mkdirSync(CONFIG_DIR, { recursive: true });
    }

    fs.writeFileSync(DEFAULT_CONFIG_FILE, JSON.stringify(defaultConfig, null, 2));
    console.log(`已创建默认配置文件: ${DEFAULT_CONFIG_FILE}`);
  }
}

module.exports = { ConfigLoader };
