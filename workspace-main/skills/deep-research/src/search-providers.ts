/**
 * 多搜索源支持模块
 * 支持 Firecrawl、Baidu Search、Brave Search
 */

import FirecrawlApp, { SearchResponse as FirecrawlResponse } from '@mendable/firecrawl-js';
import { execSync } from 'child_process';
import * as path from 'path';

export type SearchResult = {
  url: string;
  title: string;
  markdown?: string;
};

export type SearchProvider = 'firecrawl' | 'baidu' | 'brave';

/**
 * 自动检测 Clash 代理是否可用
 * 检测 127.0.0.1:7890 (HTTP) 和 127.0.0.1:7897 (Mixed)
 */
async function detectClashProxy(): Promise<string | undefined> {
  const { ProxyAgent, fetch: undiciFetch } = await import('undici');
  
  // 优先检测的 Clash 端口
  const proxyPorts = [7890, 7897];
  
  for (const port of proxyPorts) {
    const proxyUrl = `http://127.0.0.1:${port}`;
    try {
      // 尝试通过代理访问一个可靠的测试地址
      const dispatcher = new ProxyAgent(proxyUrl);
      const response = await undiciFetch('http://httpbin.org/ip', {
        dispatcher,
        connectTimeout: 3000,
      });
      if (response.ok) {
        console.log(`Detected Clash proxy: ${proxyUrl}`);
        return proxyUrl;
      }
    } catch {
      // 端口不可用，继续检测下一个
    }
  }
  
  // 如果环境变量已设置，也使用它
  const envProxy = process.env.HTTPS_PROXY || process.env.https_proxy || 
                   process.env.HTTP_PROXY || process.env.http_proxy;
  if (envProxy) {
    console.log(`Using proxy from env: ${envProxy}`);
    return envProxy;
  }
  
  return undefined;
}

// Initialize Firecrawl
const firecrawl = new FirecrawlApp({
  apiKey: process.env.FIRECRAWL_API_KEY ?? process.env.FIRECRAWL_KEY ?? '',
  apiUrl: process.env.FIRECRAWL_BASE_URL,
});

/**
 * 使用 Firecrawl 搜索
 */
async function searchWithFirecrawl(query: string, limit: number = 5): Promise<SearchResult[]> {
  const result = await firecrawl.search(query, {
    timeout: 15000,
    limit,
    scrapeOptions: { formats: ['markdown'] },
  });

  return result.data
    .filter(item => item.url && item.title)
    .map(item => ({
      url: item.url!,
      title: item.title!.trim(),
      markdown: item.markdown,
    }));
}

/**
 * 使用百度搜索
 */
async function searchWithBaidu(query: string, limit: number = 5): Promise<SearchResult[]> {
  const baiduScriptPath = path.join(
    __dirname,
    '..',
    '..',
    'baidu-search-1.1.2',
    'scripts',
    'search.py'
  );

  const fs = await import('fs');
  const os = await import('os');
  const requestBody = JSON.stringify({
    query,
    count: limit,
  });

  // 创建临时文件存储 JSON 参数（避免 shell 转义问题）
  const tempFile = path.join(os.tmpdir(), `baidu_search_${Date.now()}.json`);
  
  try {
    fs.writeFileSync(tempFile, requestBody, 'utf-8');

    const output = execSync(
      `python "${baiduScriptPath}" "${tempFile}"`,
      {
        encoding: 'utf-8',
        timeout: 30000,
        env: {
          ...process.env,
          BAIDU_API_KEY: process.env.BAIDU_API_KEY,
        },
      }
    );

    // 解析输出（提取 JSON 数组或对象）
    const jsonMatch = output.match(/\[[\s\S]*\]|\{[\s\S]*\}/);
    if (!jsonMatch) {
      console.log('Baidu search returned no valid JSON');
      return [];
    }

    const results = JSON.parse(jsonMatch[0]);
    
    if (!Array.isArray(results)) {
      console.log('Baidu search returned invalid format');
      return [];
    }

    return results
      .filter((item: any) => item.url && item.title)
      .map((item: any) => ({
        url: item.url,
        title: item.title.trim(),
        markdown: item.content || item.abstract || '',
      }));
  } catch (error) {
    console.error('Baidu search error:', error);
    return [];
  } finally {
    // 清理临时文件
    try {
      fs.unlinkSync(tempFile);
    } catch {
      // ignore cleanup errors
    }
  }
}

/**
 * 使用 Brave Search
 */
async function searchWithBrave(query: string, limit: number = 5): Promise<SearchResult[]> {
  const apiKey = process.env.BRAVE_API_KEY;
  
  if (!apiKey) {
    console.log('Brave API key not found');
    return [];
  }

  try {
    // 自动检测代理（Clash 或环境变量）
    const { ProxyAgent, fetch: undiciFetch } = await import('undici');
    const proxyUrl = await detectClashProxy();
    const dispatcher = proxyUrl ? new ProxyAgent(proxyUrl) : undefined;

    const response = await undiciFetch(
      `https://api.search.brave.com/res/v1/web/search?q=${encodeURIComponent(query)}&count=${limit}`,
      {
        dispatcher,
        headers: {
          'Accept': 'application/json',
          'X-Subscription-Token': apiKey,
        },
      }
    );

    if (!response.ok) {
      console.log(`Brave search failed: ${response.status}`);
      return [];
    }

    const data = await response.json() as any;
    const results = data.web?.results || [];

    return results
      .filter((item: any) => item.url && item.title)
      .map((item: any) => ({
        url: item.url,
        title: item.title.trim(),
        markdown: item.description || '',
      }));
  } catch (error) {
    console.error('Brave search error:', error);
    return [];
  }
}

/**
 * 智能搜索：按优先级尝试多个搜索源
 * 1. Firecrawl (最佳质量，但可能额度不足)
 * 2. Baidu (中文优化，无需 VPN)
 * 3. Brave (备用)
 */
export async function smartSearch(
  query: string,
  limit: number = 5
): Promise<{ results: SearchResult[]; provider: SearchProvider }> {
  // 尝试 Firecrawl
  try {
    console.log(`Trying Firecrawl for: ${query}`);
    const results = await searchWithFirecrawl(query, limit);
    if (results.length > 0) {
      console.log(`Firecrawl returned ${results.length} results`);
      return { results, provider: 'firecrawl' };
    }
  } catch (error: any) {
    // 402 = 额度不足，其他错误也继续尝试
    console.log(`Firecrawl failed: ${error.message || error}`);
  }

  // 尝试百度搜索
  try {
    console.log(`Trying Baidu for: ${query}`);
    const results = await searchWithBaidu(query, limit);
    if (results.length > 0) {
      console.log(`Baidu returned ${results.length} results`);
      return { results, provider: 'baidu' };
    }
  } catch (error: any) {
    console.log(`Baidu failed: ${error.message || error}`);
  }

  // 尝试 Brave Search
  try {
    console.log(`Trying Brave for: ${query}`);
    const results = await searchWithBrave(query, limit);
    if (results.length > 0) {
      console.log(`Brave returned ${results.length} results`);
      return { results, provider: 'brave' };
    }
  } catch (error: any) {
    console.log(`Brave failed: ${error.message || error}`);
  }

  // 全部失败
  console.log('All search providers failed');
  return { results: [], provider: 'firecrawl' };
}

/**
 * 批量搜索多个查询
 */
export async function batchSearch(
  queries: string[],
  limit: number = 5
): Promise<Map<string, SearchResult[]>> {
  const results = new Map<string, SearchResult[]>();

  for (const query of queries) {
    const { results: searchResults } = await smartSearch(query, limit);
    results.set(query, searchResults);
  }

  return results;
}
