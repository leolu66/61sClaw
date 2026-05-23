/**
 * 全局并发控制模块
 * 管理搜索请求的并发数，所有搜索统一经过此 limiter
 */

import pLimit from 'p-limit';

// 默认并发数
const DEFAULT_CONCURRENCY = 3;

// 全局搜索并发限制器
let searchLimiter: ReturnType<typeof pLimit>;

/**
 * 初始化并发控制
 * @param maxConcurrent 最大并发搜索数
 */
export function initConcurrency(maxConcurrent: number = DEFAULT_CONCURRENCY): void {
  const concurrency = Math.max(1, Math.min(maxConcurrent, 10)); // 限制 1-10
  searchLimiter = pLimit(concurrency);
  console.log(`Search concurrency: ${concurrency}`);
}

/**
 * 获取全局搜索 limiter
 * 如果未初始化，使用默认值
 */
export function getSearchLimiter(): ReturnType<typeof pLimit> {
  if (!searchLimiter) {
    searchLimiter = pLimit(DEFAULT_CONCURRENCY);
  }
  return searchLimiter;
}
