/**
 * NodeManager - 节点管理模块
 * 负责节点注册、心跳更新、状态查询
 */

const fs = require('fs');
const path = require('path');
const dayjs = require('dayjs');

const CONFIG_DIR = 'D:\\projects\\config';
const HEARTBEATS_FILE = path.join(CONFIG_DIR, 'heartbeats.json');
const SETTINGS_FILE = path.join(CONFIG_DIR, 'settings.json');

class NodeManager {
  constructor() {
    this._ensureConfigFile();
    this._settings = this._loadSettings();
  }

  _ensureConfigFile() {
    if (!fs.existsSync(HEARTBEATS_FILE)) {
      fs.mkdirSync(CONFIG_DIR, { recursive: true });
      fs.writeFileSync(HEARTBEATS_FILE, JSON.stringify({
        nodes: {},
        heartbeatTimeout: 360,
        lastUpdate: null
      }, null, 2));
    }
  }

  _loadSettings() {
    if (fs.existsSync(SETTINGS_FILE)) {
      return JSON.parse(fs.readFileSync(SETTINGS_FILE, 'utf-8'));
    }
    return {
      heartbeatTimeout: 360,
      maxTaskPerNode: 2
    };
  }

  _readHeartbeats() {
    return JSON.parse(fs.readFileSync(HEARTBEATS_FILE, 'utf-8'));
  }

  _writeHeartbeats(data) {
    data.lastUpdate = dayjs().toISOString();
    fs.writeFileSync(HEARTBEATS_FILE, JSON.stringify(data, null, 2), 'utf-8');
  }

  /**
   * 注册或更新节点
   */
  registerNode(nodeId, workspace) {
    const data = this._readHeartbeats();
    
    if (!data.nodes[nodeId]) {
      data.nodes[nodeId] = {
        status: 'online',
        currentTaskCount: 0,
        maxTaskCount: this._settings.maxTaskPerNode || 2,
        capabilities: [],
        lastHeartbeat: dayjs().toISOString(),
        registeredAt: dayjs().toISOString(),
        workspace: workspace
      };
    } else {
      data.nodes[nodeId].workspace = workspace;
      data.nodes[nodeId].lastHeartbeat = dayjs().toISOString();
      data.nodes[nodeId].status = 'online';
    }

    this._writeHeartbeats(data);
    return data.nodes[nodeId];
  }

  /**
   * 更新心跳
   */
  heartbeat(nodeId, status = 'online') {
    const data = this._readHeartbeats();
    
    if (!data.nodes[nodeId]) {
      throw new Error(`节点未注册: ${nodeId}`);
    }

    data.nodes[nodeId].lastHeartbeat = dayjs().toISOString();
    data.nodes[nodeId].status = status;
    
    this._writeHeartbeats(data);
    return data.nodes[nodeId];
  }

  /**
   * 更新节点任务数
   */
  updateTaskCount(nodeId, count) {
    const data = this._readHeartbeats();
    
    if (!data.nodes[nodeId]) {
      throw new Error(`节点未注册: ${nodeId}`);
    }

    data.nodes[nodeId].currentTaskCount = count;
    this._writeHeartbeats(data);
    return data.nodes[nodeId];
  }

  /**
   * 增加节点任务数
   */
  incrementTaskCount(nodeId) {
    const data = this._readHeartbeats();
    
    if (!data.nodes[nodeId]) {
      throw new Error(`节点未注册: ${nodeId}`);
    }

    data.nodes[nodeId].currentTaskCount = (data.nodes[nodeId].currentTaskCount || 0) + 1;
    if (data.nodes[nodeId].currentTaskCount > 0) {
      data.nodes[nodeId].status = 'busy';
    }
    
    this._writeHeartbeats(data);
    return data.nodes[nodeId];
  }

  /**
   * 减少节点任务数
   */
  decrementTaskCount(nodeId) {
    const data = this._readHeartbeats();
    
    if (!data.nodes[nodeId]) {
      throw new Error(`节点未注册: ${nodeId}`);
    }

    data.nodes[nodeId].currentTaskCount = Math.max(0, (data.nodes[nodeId].currentTaskCount || 1) - 1);
    if (data.nodes[nodeId].currentTaskCount === 0) {
      data.nodes[nodeId].status = 'online';
    }
    
    this._writeHeartbeats(data);
    return data.nodes[nodeId];
  }

  /**
   * 获取所有节点
   */
  getNodes() {
    const data = this._readHeartbeats();
    return data.nodes;
  }

  /**
   * 获取单个节点
   */
  getNode(nodeId) {
    const data = this._readHeartbeats();
    return data.nodes[nodeId];
  }

  /**
   * 检查节点是否在线（6 分钟内有心跳）
   */
  isNodeOnline(nodeId) {
    const node = this.getNode(nodeId);
    if (!node) return false;

    const timeout = this._settings.heartbeatTimeout || 360;
    const lastHeartbeat = dayjs(node.lastHeartbeat);
    const diff = dayjs().diff(lastHeartbeat, 'second');
    
    return diff < timeout;
  }

  /**
   * 获取所有在线节点
   */
  getOnlineNodes() {
    const data = this._readHeartbeats();
    const timeout = this._settings.heartbeatTimeout || 360;
    const nodes = {};

    for (const [nodeId, node] of Object.entries(data.nodes)) {
      const diff = dayjs().diff(dayjs(node.lastHeartbeat), 'second');
      if (diff < timeout) {
        nodes[nodeId] = node;
      }
    }

    return nodes;
  }

  /**
   * 获取可用的节点（在线且任务数未满）
   */
  getAvailableNodes() {
    const onlineNodes = this.getOnlineNodes();
    const available = {};

    for (const [nodeId, node] of Object.entries(onlineNodes)) {
      const maxTask = node.maxTaskCount || this._settings.maxTaskPerNode || 2;
      if (node.currentTaskCount < maxTask) {
        available[nodeId] = node;
      }
    }

    return available;
  }

  /**
   * 选择负载最低的节点（平均分配策略）
   */
  selectBestNode() {
    const availableNodes = this.getAvailableNodes();
    
    if (Object.keys(availableNodes).length === 0) {
      return null;
    }

    // 选择任务数最少的节点
    let bestNode = null;
    let minTaskCount = Infinity;

    for (const [nodeId, node] of Object.entries(availableNodes)) {
      if (node.currentTaskCount < minTaskCount) {
        minTaskCount = node.currentTaskCount;
        bestNode = nodeId;
      }
    }

    return bestNode;
  }

  /**
   * 移除节点
   */
  removeNode(nodeId) {
    const data = this._readHeartbeats();
    
    if (!data.nodes[nodeId]) {
      throw new Error(`节点不存在: ${nodeId}`);
    }

    delete data.nodes[nodeId];
    this._writeHeartbeats(data);

    return true;
  }

  /**
   * 获取节点状态摘要
   */
  getStatusSummary() {
    const nodes = this.getNodes();
    const timeout = this._settings.heartbeatTimeout || 360;
    
    let online = 0;
    let busy = 0;
    let offline = 0;
    let totalTasks = 0;

    for (const node of Object.values(nodes)) {
      const diff = dayjs().diff(dayjs(node.lastHeartbeat), 'second');
      if (diff < timeout) {
        online++;
        if (node.status === 'busy') {
          busy++;
        }
        totalTasks += node.currentTaskCount || 0;
      } else {
        offline++;
      }
    }

    return {
      total: Object.keys(nodes).length,
      online,
      busy,
      offline,
      totalTasks
    };
  }
}

module.exports = { NodeManager };
