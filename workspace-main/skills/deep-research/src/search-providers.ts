/**
 * 多搜索源支持模块
 * 支持 Firecrawl、Volcengine、MultiSearch、Baidu Search、Brave Search
 */

import FirecrawlApp, { SearchResponse as FirecrawlResponse } from '@mendable/firecrawl-js';
import { execSync } from 'child_process';
import * as path from 'path';

import { getCached, setCached } from './search-cache';

export type SearchResult = {
  url: string;
  title: string;
  markdown?: string;
};

export type SearchProvider = 'firecrawl' | 'volc' | 'multi' | 'baidu' | 'brave' | 'cache';

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
        signal: AbortSignal.timeout(3000),
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
 * 使用火山引擎融合搜索
 */
async function searchWithVolc(query: string, limit: number = 5): Promise<SearchResult[]> {
  const volcApiKey = await getVolcApiKey();
  if (!volcApiKey) {
    console.log('Volcengine API key not found');
    return [];
  }

  try {
    const response = await fetch('https://open.feedcoopapi.com/search_api/web_search', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${volcApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        Query: query,
        SearchType: 'web',
        Count: Math.min(limit, 50),
      }),
      signal: AbortSignal.timeout(30000),
    });

    if (!response.ok) {
      console.log(`Volcengine search failed: ${response.status}`);
      return [];
    }

    const data = await response.json() as any;

    // 检查 API 错误
    if (data?.ResponseMetadata?.Error) {
      const err = data.ResponseMetadata.Error;
      console.log(`Volcengine API error: ${err.CodeN || ''} - ${err.Message || 'Unknown'}`);
      return [];
    }

    const webResults = data?.Result?.WebResults || [];
    return webResults
      .filter((item: any) => item.Url && item.Title)
      .map((item: any) => ({
        url: item.Url,
        title: item.Title.trim(),
        markdown: item.Snippet || '',
      }));
  } catch (error) {
    console.error('Volcengine search error:', error);
    return [];
  }
}

/**
 * 从密码箱获取火山引擎 API Key
 */
async function getVolcApiKey(): Promise<string> {
  // 先从环境变量读取
  const envKey = process.env.VOLCSEARCH_API_KEY;
  if (envKey) return envKey;

  // 从密码箱读取
  try {
    const os = await import('os');
    const fs = await import('fs');
    const path = await import('path');
    const credFile = path.join(os.homedir(), '.openclaw', 'vault', 'credentials.json');
    if (fs.existsSync(credFile)) {
      const raw = fs.readFileSync(credFile, 'utf-8');
      const data = JSON.parse(raw);
      const creds = data?.credentials || {};
      const volcCred = creds['volcsearch'] || {};
      for (const field of volcCred.fields || []) {
        if (field.key === 'api_key') return field.value || '';
      }
    }
  } catch (e) {
    console.log('Failed to read volcsearch credentials from vault');
  }

  return '';
}

/**
 * 多搜索引擎 Web 抓取
 * 封装 multi-search-engine-simple-1.0.0，从 Bing CN / 搜狗 / 360 抓取搜索结果
 */
async function searchWithMulti(query: string, limit: number = 5): Promise<SearchResult[]> {
  // 搜索引擎配置（来自 multi-search-engine-simple-1.0.0）
  const engines = [
    {
      name: 'Bing CN',
      url: `https://cn.bing.com/search?q=${encodeURIComponent(query)}&ensearch=0&count=${limit}`,
      // Bing 结果：<li class="b_algo"> 内 <h2><a href="...">title</a></h2> + <p>snippet</p>
      parser: (html: string): SearchResult[] => {
        const results: SearchResult[] = [];
        const algoRegex = /<li class="b_algo">([\s\S]*?)<\/li>/gi;
        let match;
        while ((match = algoRegex.exec(html)) !== null) {
          const block = match[1];
          const urlMatch = block.match(/<a[^>]*href="(https?:\/\/[^"]+)"[^>]*>/i);
          const titleMatch = block.match(/<a[^>]*>([\s\S]*?)<\/a>/i);
          const snippetMatch = block.match(/<p[^>]*>([\s\S]*?)<\/p>/i);
          if (urlMatch && titleMatch) {
            const url = urlMatch[1];
            const title = titleMatch[1].replace(/<[^>]+>/g, '').trim();
            const snippet = snippetMatch ? snippetMatch[1].replace(/<[^>]+>/g, '').trim() : '';
            if (!url.includes('bing.com') && !url.includes('microsoft.com/bing')) {
              results.push({ url, title, markdown: snippet });
            }
          }
        }
        return results.slice(0, limit);
      },
    },
  ];

  for (const engine of engines) {
    try {
      console.log(`Multi-search trying ${engine.name} for: ${query}`);
      const response = await fetch(engine.url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml',
          'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        },
        signal: AbortSignal.timeout(15000),
      });

      if (!response.ok) {
        console.log(`${engine.name} returned ${response.status}`);
        continue;
      }

      const html = await response.text();
      const results = engine.parser(html);
      console.log(`${engine.name} returned ${results.length} results`);
      if (results.length > 0) return results;
    } catch (error) {
      console.log(`${engine.name} failed: ${error}`);
    }
  }

  return [];
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
 * 1. Volcengine (火山引擎，中文优化，5000次免费额度，无需 VPN)
 * 2. Firecrawl (最佳质量，备用搜索源)
 * 3. MultiSearch (Bing CN Web抓取，补充索引覆盖，无需 VPN)
 * 4. Baidu (中文优化，无需 VPN)
 * 5. Brave (国际搜索备用，需 VPN)
 */
export async function smartSearch(
  query: string,
  limit: number = 5
): Promise<{ results: SearchResult[]; provider: SearchProvider }> {
  // 先查缓存
  const cached = await getCached(query);
  if (cached && cached.length > 0) {
    return { results: cached, provider: 'cache' };
  }

  // 尝试火山引擎搜索（优先级最高：有免费额度、中文优化、无需 VPN）
  try {
    console.log(`Trying Volcengine for: ${query}`);
    const results = await searchWithVolc(query, limit);
    if (results.length > 0) {
      console.log(`Volcengine returned ${results.length} results`);
      await setCached(query, 'volc', results);
      return { results, provider: 'volc' };
    }
  } catch (error: any) {
    console.log(`Volcengine failed: ${error.message || error}`);
  }

  // 尝试 Firecrawl（备用，额度有限）
  try {
    console.log(`Trying Firecrawl for: ${query}`);
    const results = await searchWithFirecrawl(query, limit);
    if (results.length > 0) {
      console.log(`Firecrawl returned ${results.length} results`);
      await setCached(query, 'firecrawl', results);
      return { results, provider: 'firecrawl' };
    }
  } catch (error: any) {
    console.log(`Firecrawl failed: ${error.message || error}`);
  }

  // 尝试多搜索引擎 Web 抓取
  try {
    console.log(`Trying MultiSearch for: ${query}`);
    const results = await searchWithMulti(query, limit);
    if (results.length > 0) {
      console.log(`MultiSearch returned ${results.length} results`);
      await setCached(query, 'multi', results);
      return { results, provider: 'multi' };
    }
  } catch (error: any) {
    console.log(`MultiSearch failed: ${error.message || error}`);
  }

  // 尝试百度搜索
  try {
    console.log(`Trying Baidu for: ${query}`);
    const results = await searchWithBaidu(query, limit);
    if (results.length > 0) {
      console.log(`Baidu returned ${results.length} results`);
      await setCached(query, 'baidu', results);
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
      await setCached(query, 'brave', results);
      return { results, provider: 'brave' };
    }
  } catch (error: any) {
    console.log(`Brave failed: ${error.message || error}`);
  }

  // 全部失败
  console.log('All search providers failed');
  return { results: [], provider: 'firecrawl' };
}
