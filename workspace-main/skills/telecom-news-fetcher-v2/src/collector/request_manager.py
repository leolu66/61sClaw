# -*- coding: utf-8 -*-
"""
请求管理器 - 反爬策略核心
管理UA轮换、代理、Cookie、请求指纹等
"""
import random
import time
import asyncio
from typing import Optional, Dict, List
import aiohttp


class UserAgentRotator:
    """User-Agent轮换器"""
    
    DEFAULT_UAS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    ]
    
    def __init__(self, user_agents: Optional[List[str]] = None):
        self.user_agents = user_agents or self.DEFAULT_UAS
        
    def get(self) -> str:
        """获取随机UA"""
        return random.choice(self.user_agents)


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, requests_per_second: float = 1.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time: Optional[float] = None
        self._lock = asyncio.Lock()
        
    async def wait(self):
        """等待直到可以发送下一个请求"""
        async with self._lock:
            if self.last_request_time is not None:
                elapsed = time.time() - self.last_request_time
                if elapsed < self.min_interval:
                    await asyncio.sleep(self.min_interval - elapsed)
            self.last_request_time = time.time()


class RequestManager:
    """
    请求管理器
    
    功能:
    - UA轮换
    - 速率限制
    - 随机延迟
    - 请求头管理
    """
    
    def __init__(
        self,
        delay_min: float = 1.0,
        delay_max: float = 3.0,
        requests_per_second: float = 1.0
    ):
        self.ua_rotator = UserAgentRotator()
        self.rate_limiter = RateLimiter(requests_per_second)
        self.delay_min = delay_min
        self.delay_max = delay_max
        
    def get_headers(self, extra_headers: Optional[Dict] = None) -> Dict:
        """获取请求头"""
        headers = {
            'User-Agent': self.ua_rotator.get(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        if extra_headers:
            headers.update(extra_headers)
            
        return headers
    
    async def request(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict] = None,
        timeout: int = 30,
        encoding: Optional[str] = None
    ) -> 'Response':
        """
        发送HTTP请求
        
        Args:
            url: 请求URL
            method: 请求方法
            headers: 额外请求头
            timeout: 超时时间
            encoding: 响应编码
            
        Returns:
            Response: 响应对象
        """
        # 速率限制
        await self.rate_limiter.wait()
        
        # 随机延迟
        await asyncio.sleep(random.uniform(self.delay_min, self.delay_max))
        
        # 构建请求头
        request_headers = self.get_headers(headers)
        
        # 发送请求
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=request_headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                # 读取内容
                content = await response.read()
                
                # 解码
                if encoding:
                    text = content.decode(encoding, errors='ignore')
                else:
                    # 尝试从响应头获取编码
                    charset = response.charset or 'utf-8'
                    text = content.decode(charset, errors='ignore')
                
                return Response(
                    status_code=response.status,
                    text=text,
                    headers=dict(response.headers),
                    url=str(response.url)
                )


class Response:
    """响应对象"""
    
    def __init__(
        self,
        status_code: int,
        text: str,
        headers: Dict,
        url: str
    ):
        self.status_code = status_code
        self.text = text
        self.headers = headers
        self.url = url
        
    @property
    def ok(self) -> bool:
        """请求是否成功"""
        return 200 <= self.status_code < 300
    
    def __repr__(self):
        return f"Response(status={self.status_code}, url={self.url})"
