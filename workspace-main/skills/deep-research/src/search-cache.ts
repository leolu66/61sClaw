/**
 * 搜索结果缓存模块
 * 将搜索结果持久化到 cache/ 目录，避免重复搜索
 * 支持 TTL 过期机制
 */

import * as crypto from 'crypto';
import * as fs from 'fs/promises';
import * as path from 'path';

import { SearchResult } from './search-providers';

// 默认缓存目录
const CACHE_DIR = path.join(__dirname, '..', 'cache');

// 默认 TTL: 24 小时 (毫秒)
const DEFAULT_TTL_MS = 24 * 60 * 60 * 1000;

// 是否启用缓存（由 run.ts 初始化时设置）
let cacheEnabled = true;
let cacheTtlMs = DEFAULT_TTL_MS;

// 统计计数器
let cacheHits = 0;
let cacheMisses = 0;
let cacheWrites = 0;

export function getCacheStats() {
  return { hits: cacheHits, misses: cacheMisses, writes: cacheWrites };
}

export function initCache(options: { enabled?: boolean; ttlSeconds?: number } = {}) {
  if (options.enabled !== undefined) {
    cacheEnabled = options.enabled;
  }
  if (options.ttlSeconds !== undefined) {
    cacheTtlMs = options.ttlSeconds * 1000;
  }
  console.log(`Cache: ${cacheEnabled ? 'enabled' : 'disabled'}, TTL: ${Math.round(cacheTtlMs / 1000)}s`);
}

type CacheEntry = {
  query: string;
  provider: string;
  results: SearchResult[];
  timestamp: number;
  ttl: number;
};

/**
 * 生成查询的 hash 作为文件名
 */
function hashQuery(query: string): string {
  return crypto.createHash('md5').update(query.toLowerCase().trim()).digest('hex');
}

/**
 * 获取缓存的搜索结果
 * @returns 缓存命中且未过期时返回结果，否则返回 null
 */
export async function getCached(query: string): Promise<SearchResult[] | null> {
  if (!cacheEnabled) return null;

  const hash = hashQuery(query);
  const cacheFile = path.join(CACHE_DIR, `${hash}.json`);

  try {
    const raw = await fs.readFile(cacheFile, 'utf-8');
    const entry: CacheEntry = JSON.parse(raw);

    // 检查 TTL
    const age = Date.now() - entry.timestamp;
    if (age > entry.ttl) {
      // 过期，删除缓存文件
      await fs.unlink(cacheFile).catch(() => {});
      cacheMisses++;
      return null;
    }

    if (entry.results && entry.results.length > 0) {
      cacheHits++;
      console.log(`  Cache hit: "${query.slice(0, 50)}..." (${entry.results.length} results, provider: ${entry.provider})`);
      return entry.results;
    }
  } catch {
    // 缓存文件不存在或解析失败，返回 null
  }

  cacheMisses++;
  return null;
}

/**
 * 将搜索结果写入缓存
 */
export async function setCached(
  query: string,
  provider: string,
  results: SearchResult[]
): Promise<void> {
  if (!cacheEnabled) return;
  if (!results || results.length === 0) return;

  const hash = hashQuery(query);
  const cacheFile = path.join(CACHE_DIR, `${hash}.json`);

  const entry: CacheEntry = {
    query,
    provider,
    results,
    timestamp: Date.now(),
    ttl: cacheTtlMs,
  };

  try {
    // 确保 cache 目录存在
    await fs.mkdir(CACHE_DIR, { recursive: true });
    await fs.writeFile(cacheFile, JSON.stringify(entry, null, 2), 'utf-8');
    cacheWrites++;
  } catch (error) {
    console.log(`  Cache write failed: ${error}`);
  }
}

/**
 * 清理过期缓存文件
 */
export async function cleanExpiredCache(): Promise<number> {
  let cleaned = 0;

  try {
    const files = await fs.readdir(CACHE_DIR);

    for (const file of files) {
      if (!file.endsWith('.json')) continue;

      const filePath = path.join(CACHE_DIR, file);
      try {
        const raw = await fs.readFile(filePath, 'utf-8');
        const entry: CacheEntry = JSON.parse(raw);
        const age = Date.now() - entry.timestamp;

        if (age > entry.ttl) {
          await fs.unlink(filePath);
          cleaned++;
        }
      } catch {
        // 损坏的缓存文件也删除
        await fs.unlink(filePath).catch(() => {});
        cleaned++;
      }
    }
  } catch {
    // cache 目录不存在
  }

  if (cleaned > 0) {
    console.log(`Cleaned ${cleaned} expired cache entries`);
  }

  return cleaned;
}
