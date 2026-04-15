/**
 * HeartbeatChecker - 心跳检查器
 * 定时检查节点状态，标记离线节点
 */

const { NodeManager } = require('../node/node-manager');

class HeartbeatChecker {
  constructor() {
    this.nodeManager = new NodeManager();
    this.checkInterval = null;
    this.onNodeOffline = null;  // 节点离线回调
    this.onNodeOnline = null;   // 节点恢复在线回调
  }

  /**
   * 启动心跳检查
   * @param {number} intervalMs 检查间隔（毫秒），默认 60 秒
   */
  start(intervalMs = 60000) {
    if (this.checkInterval) {
      this.clearInterval(this.checkInterval);
    }

    console.log(`[HeartbeatChecker] 启动心跳检查，间隔 ${intervalMs}ms`);
    
    this.checkInterval = setInterval(() => {
      this.check();
    }, intervalMs);

    // 立即执行一次检查
    this.check();
  }

  /**
   * 停止心跳检查
   */
  stop() {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
      console.log('[HeartbeatChecker] 已停止心跳检查');
    }
  }

  /**
   * 执行一次检查
   */
  check() {
    const nodes = this.nodeManager.getNodes();
    const now = dayjs();
    let changed = false;

    for (const [nodeId, node] of Object.entries(nodes)) {
      const lastHeartbeat = dayjs(node.lastHeartbeat);
      const diff = now.diff(lastHeartbeat, 'second');
      const timeout = 360; // 6 分钟

      if (diff >= timeout && node.status !== 'offline') {
        // 节点离线
        console.log(`[HeartbeatChecker] 节点 ${nodeId} 已离线（${diff}秒无心跳）`);
        
        // 更新节点状态
        node.status = 'offline';
        changed = true;

        // 触发回调
        if (this.onNodeOffline) {
          this.onNodeOffline(nodeId, node);
        }
      } else if (diff < timeout && node.status === 'offline') {
        // 节点恢复在线
        console.log(`[HeartbeatChecker] 节点 ${nodeId} 恢复在线`);
        
        node.status = node.currentTaskCount > 0 ? 'busy' : 'online';
        changed = true;

        if (this.onNodeOnline) {
          this.onNodeOnline(nodeId, node);
        }
      }
    }

    if (changed) {
      // 保存更新
      const data = JSON.parse(require('fs').readFileSync('D:\\projects\\config\\heartbeats.json', 'utf-8'));
      data.nodes = nodes;
      require('fs').writeFileSync('D:\\projects\\config\\heartbeats.json', JSON.stringify(data, null, 2));
    }

    return changed;
  }

  /**
   * 设置节点离线回调
   */
  setOnNodeOffline(callback) {
    this.onNodeOffline = callback;
  }

  /**
   * 设置节点恢复在线回调
   */
  setOnNodeOnline(callback) {
    this.onNodeOnline = callback;
  }

  /**
   * 手动触发节点离线（用于测试）
   */
  markNodeOffline(nodeId) {
    const node = this.nodeManager.getNode(nodeId);
    if (node) {
      node.status = 'offline';
      
      const data = JSON.parse(require('fs').readFileSync('D:\\projects\\config\\heartbeats.json', 'utf-8'));
      data.nodes[nodeId] = node;
      require('fs').writeFileSync('D:\\projects\\config\\heartbeats.json', JSON.stringify(data, null, 2));
      
      if (this.onNodeOffline) {
        this.onNodeOffline(nodeId, node);
      }
    }
  }

  /**
   * 手动触发节点恢复在线（用于测试）
   */
  markNodeOnline(nodeId) {
    const node = this.nodeManager.getNode(nodeId);
    if (node) {
      node.status = node.currentTaskCount > 0 ? 'busy' : 'online';
      node.lastHeartbeat = require('dayjs')().toISOString();
      
      const data = JSON.parse(require('fs').readFileSync('D:\\projects\\config\\heartbeats.json', 'utf-8'));
      data.nodes[nodeId] = node;
      require('fs').writeFileSync('D:\\projects\\config\\heartbeats.json', JSON.stringify(data, null, 2));
      
      if (this.onNodeOnline) {
        this.onNodeOnline(nodeId, node);
      }
    }
  }
}

// 导出类
const dayjs = require('dayjs');
module.exports = { HeartbeatChecker };
