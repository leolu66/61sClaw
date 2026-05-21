# -*- coding: utf-8 -*-
"""
C114通信网爬虫
"""
from typing import List
from bs4 import BeautifulSoup

from collector.spiders.base import BaseSpider, AntiSpiderDetected
from common.models import NewsItem, SourceConfig
from collector.request_manager import RequestManager


class C114Spider(BaseSpider):
    """C114通信网爬虫"""
    
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self.request_manager = RequestManager(
            delay_min=1.0,
            delay_max=3.0,
            requests_per_second=0.5
        )
        
    async def fetch(
        self,
        keywords: List[str],
        limit: int = 10,
        **kwargs
    ) -> List[NewsItem]:
        """
        从C114获取新闻
        
        策略: 访问滚动新闻页面，筛选包含关键词的新闻
        """
        items = []
        
        # C114滚动新闻页面
        url = "https://www.c114.com.cn/news/roll.asp"
        
        try:
            # 发送请求
            response = await self.request_manager.request(
                url=url,
                encoding='gbk'  # C114使用GBK编码
            )
            
            # 检查反爬
            if response.status_code == 403:
                raise AntiSpiderDetected("C114返回403，可能触发反爬")
            
            if not response.ok:
                print(f"[C114] 请求失败: {response.status_code}")
                return items
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找新闻列表
            # C114滚动新闻页面结构
            news_list = soup.select('div.news_list li') or soup.select('.news-list li')
            
            if not news_list:
                # 尝试其他选择器
                news_list = soup.select('ul li')
            
            print(f"[C114] 找到 {len(news_list)} 条新闻")
            
            for news_item in news_list[:limit * 2]:  # 多取一些用于筛选
                if len(items) >= limit:
                    break
                
                try:
                    # 提取标题和链接
                    link_elem = news_item.find('a')
                    if not link_elem:
                        continue
                    
                    title = link_elem.get_text(strip=True)
                    href = link_elem.get('href', '')
                    
                    # 过滤无效链接
                    if not href or 'javascript' in href:
                        continue
                    
                    # 处理相对链接
                    if href.startswith('/'):
                        full_url = f"https://www.c114.com.cn{href}"
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    # 提取日期
                    date_elem = news_item.find('span', class_='date') or news_item.find('span', class_='time')
                    date_str = date_elem.get_text(strip=True) if date_elem else ""
                    published_at = self._extract_date(date_str)
                    
                    # 检查是否包含关键词（简化版：暂时不过滤，采集所有新闻）
                    # 实际使用时可以根据需要启用关键词过滤
                    pass
                    
                    # 创建新闻条目
                    item = self.create_news_item(
                        title=title,
                        url=full_url,
                        published_at=published_at
                    )
                    
                    items.append(item)
                    
                except Exception as e:
                    print(f"[C114] 解析单条新闻失败: {e}")
                    continue
            
        except AntiSpiderDetected:
            raise
        except Exception as e:
            print(f"[C114] 获取新闻失败: {e}")
        
        print(f"[C114] 成功获取 {len(items)} 条新闻")
        return items
